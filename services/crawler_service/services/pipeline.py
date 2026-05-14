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
from services.crawler_service.services.deduplicator import compute_jd_key
from services.crawler_service.services.skill_extractor import SkillExtractor
from services.crawler_service.services.storage import JDStorage

logger = logging.getLogger(__name__)


class CrawlPipeline:
    def __init__(
        self,
        crawler: IJDCrawler,
        extractor: SkillExtractor | None = None,
        storage: JDStorage | None = None,
    ) -> None:
        self.crawler = crawler
        self.extractor = extractor or SkillExtractor()
        self.storage = storage or JDStorage()

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

        for cat in categories:
            if len(out) >= cap:
                break
            try:
                if callable(rich):
                    cat_jds = rich(cat, max_pages=max_pages)
                else:
                    urls = self.crawler.crawl_listing(cat, max_pages=max_pages)
                    cat_jds = [d for d in (self.crawler.crawl_detail(u) for u in urls) if d]
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
        return ProcessedJD(
            jd_key=key,
            raw=raw,
            skills_canonical=canonical,
            role=role,
            role_group=role_group,
            first_seen=now,
            last_seen=now,
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
