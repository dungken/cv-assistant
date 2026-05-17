"""Crawler pipeline orchestrator: listing → detail → dedup → extract → save → log."""
import logging
import uuid
from datetime import datetime
from typing import Iterable

from services.crawler_service.config import settings
from services.crawler_service.models.database import CrawlerLog
from services.crawler_service.models.schemas import ProcessedJD, RawJD
from services.crawler_service.services.base_crawler import IJDCrawler
from services.crawler_service.services.db_session import get_session
from services.crawler_service.services.deduplicator import compute_jd_key, compute_job_group_id
from services.crawler_service.services.enricher import JDEnricher
from services.crawler_service.services.llm_extractor import LLMJDExtractor
from services.crawler_service.services.structured_extractor import extract as rule_extract
from services.crawler_service.services.skill_extractor import SkillExtractor
from services.crawler_service.services.storage import JDStorage

logger = logging.getLogger(__name__)


class CrawlPipeline:
    def __init__(
        self,
        crawler: IJDCrawler,
        extractor: SkillExtractor | None = None,
        storage: JDStorage | None = None,
        enricher: JDEnricher | None = None,
        fetch_details: bool = False,
        enrich_inline: bool = False,
        use_llm: bool = False,
        llm: LLMJDExtractor | None = None,
    ) -> None:
        self.crawler = crawler
        self.extractor = extractor or SkillExtractor()
        self.storage = storage or JDStorage()
        # NER enricher: optional legacy backend, kept for backfill workflow.
        self.enricher = enricher if enrich_inline else None
        if enrich_inline and self.enricher is None:
            self.enricher = JDEnricher(ner_url=settings.ner_service_url)
        # Groq-backed LLM extractor: the smart-overlay backend for semantic
        # fields (seniority, min/max_exp, degree, required vs preferred).
        # Layered on top of regex extractor; HTML/JSON-LD wins for direct
        # fields (location, salary numeric, posted_date).
        self.llm = llm
        if use_llm and self.llm is None:
            try:
                self.llm = LLMJDExtractor()
            except ValueError as e:
                logger.warning("use_llm=True but LLM init failed: %s — falling back to regex", e)
                self.llm = None
        # When True, every listing URL is followed into its detail page so we
        # capture the full `description`.
        self.fetch_details = fetch_details

    def run(
        self,
        categories: list[str] | None = None,
        max_pages: int = None,
        max_jds: int = None,
    ) -> dict:
        """Run a single crawl pass. Returns run summary."""
        run_id = str(uuid.uuid4())
        started_at = datetime.utcnow()
        categories = categories or self.crawler.list_categories()
        max_pages = max_pages or settings.crawl_max_pages_per_category
        max_jds = max_jds or settings.crawl_max_jds_per_run

        status = "success"
        error_msg = None
        processed: list[ProcessedJD] = []

        try:
            tagged_jds = self._collect_jds(categories, max_pages, max_jds)
            logger.info("run=%s collected %d JDs", run_id, len(tagged_jds))

            processed = self._process(tagged_jds)
            logger.info("run=%s after dedup+normalize: %d unique", run_id, len(processed))

            self.storage.save_batch(processed)
            logger.info("run=%s saved to storage", run_id)
        except Exception as e:
            status = "failed"
            error_msg = str(e)
            logger.exception("run=%s failed: %s", run_id, e)

        finished_at = datetime.utcnow()
        self._write_log(run_id, started_at, finished_at, status, len(processed), error_msg)
        return {
            "run_id": run_id,
            "source": self.crawler.source_name,
            "status": status,
            "jd_count": len(processed),
            "started_at": started_at.isoformat(),
            "finished_at": finished_at.isoformat(),
            "error_message": error_msg,
        }

    # ── stages ──────────────────────────────────────────────────────

    def _collect_jds(
        self, categories: list[str], max_pages: int, cap: int
    ) -> list[tuple[RawJD, str]]:
        """Return (RawJD, category) pairs so we can persist role later."""
        seen_urls: set[str] = set()
        out: list[tuple[RawJD, str]] = []
        rich = getattr(self.crawler, "crawl_category_rich", None)

        # Prefer the AJAX `fetch_description` enrichment path when the crawler
        # supports it (ITviec): listing cards give us salary + skills + location,
        # then the /content endpoint gives us the description text. This sidesteps
        # the Cloudflare 403 wall on the full detail page.
        fetch_desc = getattr(self.crawler, "fetch_description", None)
        for cat in categories:
            if len(out) >= cap:
                break
            try:
                cat_jds: list[RawJD]
                if callable(rich):
                    cat_jds = rich(cat, max_pages=max_pages)
                    if self.fetch_details and callable(fetch_desc):
                        for jd in cat_jds:
                            if len(out) + sum(1 for j in cat_jds if j is jd or jd.description) >= cap:
                                break
                            if jd.description:
                                continue  # already populated
                            desc = fetch_desc(jd.url)
                            if desc:
                                jd.description = desc
                            self.crawler.client.polite_sleep() if hasattr(self.crawler, "client") else None
                elif self.fetch_details:
                    urls = self.crawler.crawl_listing(cat, max_pages=max_pages)
                    cat_jds = []
                    for u in urls:
                        if len(out) + len(cat_jds) >= cap:
                            break
                        if u in seen_urls:
                            continue
                        d = self.crawler.crawl_detail(u)
                        if d:
                            cat_jds.append(d)
                else:
                    cat_jds = []
            except Exception as e:
                logger.warning("category failed cat=%s: %s", cat, e)
                continue

            for jd in cat_jds:
                if jd.url in seen_urls:
                    continue
                seen_urls.add(jd.url)
                out.append((jd, cat))
                if len(out) >= cap:
                    break
        return out

    def _process(self, tagged: Iterable[tuple[RawJD, str]]) -> list[ProcessedJD]:
        now = datetime.utcnow()
        by_key: dict[str, ProcessedJD] = {}
        for raw, fallback_role in tagged:
            # Prefer role inferred from the listing card (works when crawling
            # the unfiltered /it-jobs endpoint where category is generic).
            role = raw.role_hint or fallback_role
            key = compute_jd_key(raw)
            if key in by_key:
                if len(raw.description) > len(by_key[key].raw.description):
                    by_key[key] = self._build_processed(key, raw, role, now)
                continue
            by_key[key] = self._build_processed(key, raw, role, now)
        return list(by_key.values())

    def _build_processed(self, key: str, raw: RawJD, role: str, now: datetime) -> ProcessedJD:
        canonical = self.extractor.extract_from_jd(
            description=raw.description,
            fallback_skills=raw.skills_raw,
            title=raw.title,
        )
        # Resolve role_group via the ITviec expertise mapping (auto-generated).
        role_group = None
        try:
            from services.crawler_service.services.role_groups import ROLE_GROUPS
            if role and role in ROLE_GROUPS:
                role_group = ROLE_GROUPS[role]["group"]
        except ImportError:
            pass

        # Layered extraction:
        #   1) Rule-based regex always runs (cheap, deterministic)
        #   2) LLM overlay (Groq) when enabled — wins on semantic fields
        #   3) HTML/JSON-LD already filled raw.salary_*, raw.location — HTML wins
        structured = None
        if raw.description and len(raw.description) >= 50:
            structured = rule_extract(
                title=raw.title,
                description=raw.description,
                all_skills=canonical,
            )

        # LLM overlay (Groq) — extracts richer semantic fields.
        parse_version = "rule-v1"
        if self.llm is not None and structured is not None:
            llm_out = self.llm.extract(
                title=raw.title,
                description=raw.description,
                candidate_skills=canonical,
            )
            if llm_out is not None:
                # Semantic fields: LLM wins when present.
                if llm_out.seniority is not None:
                    structured.seniority = llm_out.seniority
                if llm_out.min_exp is not None:
                    structured.min_exp = llm_out.min_exp
                if llm_out.max_exp is not None:
                    structured.max_exp = llm_out.max_exp
                if llm_out.degree_required is not None:
                    structured.degree_required = llm_out.degree_required
                if llm_out.skills_required:
                    structured.skills_required = llm_out.skills_required
                if llm_out.skills_preferred:
                    structured.skills_preferred = llm_out.skills_preferred
                # Cross-validation fields: LLM only fills GAPS in HTML/regex.
                if structured.work_mode is None and llm_out.work_mode is not None:
                    structured.work_mode = llm_out.work_mode
                # Salary: HTML/JSON-LD wins when numeric. Use LLM only if HTML
                # had no signal (e.g. ITviec hid salary behind sign-in).
                if raw.salary_min is None and llm_out.salary_min is not None:
                    raw.salary_min = llm_out.salary_min
                if raw.salary_max is None and llm_out.salary_max is not None:
                    raw.salary_max = llm_out.salary_max
                if not raw.salary_currency and llm_out.salary_currency:
                    raw.salary_currency = llm_out.salary_currency
                parse_version = "rule+llm-v1"

        # Optional NER enrichment overlay — only when explicitly enabled.
        if self.enricher is not None and raw.description and len(raw.description) >= 50:
            enriched = self.enricher.enrich(
                title=raw.title, company=raw.company or "", description=raw.description,
            )
            if enriched is not None and structured is not None:
                structured.min_exp = enriched.min_exp or structured.min_exp
                structured.max_exp = enriched.max_exp or structured.max_exp
                structured.seniority = enriched.seniority or structured.seniority
                structured.degree_required = enriched.degree_required or structured.degree_required
                if enriched.skills_required:
                    structured.skills_required = enriched.skills_required
                if enriched.skills_preferred:
                    structured.skills_preferred = enriched.skills_preferred
                structured.work_mode = enriched.work_mode or structured.work_mode
                parse_version = "rule+ner-v1"

        return ProcessedJD(
            jd_key=key,
            raw=raw,
            skills_canonical=canonical,
            role=role,
            role_group=role_group,
            first_seen=now,
            last_seen=now,
            min_exp=structured.min_exp if structured else None,
            max_exp=structured.max_exp if structured else None,
            seniority=structured.seniority if structured else None,
            skills_required=structured.skills_required if structured else [],
            skills_preferred=structured.skills_preferred if structured else [],
            degree_required=structured.degree_required if structured else None,
            work_mode=structured.work_mode if structured else None,
            description_summary=structured.description_summary if structured else None,
            parsed_at=now if structured else None,
            parse_version=parse_version if structured else None,
            job_group_id=compute_job_group_id(raw.company, raw.title) or None,
        )

    def _write_log(self, run_id, started, finished, status, count, error) -> None:
        with get_session() as session:
            session.add(CrawlerLog(
                run_id=run_id,
                source=self.crawler.source_name,
                started_at=started,
                finished_at=finished,
                status=status,
                jd_count=count,
                error_message=error,
            ))
