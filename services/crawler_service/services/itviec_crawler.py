"""ItviecCrawler — crawl JDs from itviec.com.

Strategy (based on 2026-05 HTML inspection):
- Listing page (?lab_feature=preview_jd_page) embeds ALL relevant fields inside
  each <div class="job-card ..."> element: title, company, skills (itag), location,
  posted-ago, slug. We parse these directly — no need to fetch detail pages.
- Salary is gated behind login on ITviec — we leave it null.
- Description: optionally fetch via JD content endpoint
  /it-jobs/<slug>/content?job_index=N&locale=en for full text (deferred to v2).

Pagination: append ?page=N to listing URL.

Resilience: ITviec markup changes occasionally. Each field has try/except so
one bad JD doesn't kill the batch. health_check() should be run daily.
"""
import logging
import re
from datetime import date, datetime, timedelta
from typing import Optional

from bs4 import BeautifulSoup

from services.crawler_service.config import settings
from services.crawler_service.models.schemas import RawJD
from services.crawler_service.services.base_crawler import IJDCrawler
from services.crawler_service.services.http_client import PoliteHttpClient

try:
    # Auto-generated mapping (see scripts/build_role_mapping.py).
    from services.crawler_service.services.role_groups import ROLE_GROUPS
except ImportError:
    ROLE_GROUPS = {}

logger = logging.getLogger(__name__)


CATEGORY_PATHS = {
    # 'all' uses the unfiltered /it-jobs endpoint — paginates through ALL JDs
    # on the platform (~850-900 as of 2026-05). Preferred for bulk ingestion.
    "all": "/it-jobs",
    # Specific categories — useful when only certain roles are wanted.
    # Each category caps at ~5-7 pages; total via 'all' is much higher.
    "backend": "/it-jobs/backend-developer",
    "frontend": "/it-jobs/frontend-developer",
    "fullstack": "/it-jobs/fullstack",
    "mobile": "/it-jobs/mobile-developer",
    "devops": "/it-jobs/devops-engineer",
    "data": "/it-jobs/data-scientist",
    "ai": "/it-jobs/ai-machine-learning",
    "qa": "/it-jobs/tester-qa-qc",
    "pm": "/it-jobs/project-manager",
    "designer": "/it-jobs/ux-ui-designer",
}


class ItviecCrawler(IJDCrawler):
    source_name = "itviec"
    base_url = "https://itviec.com"

    def __init__(self) -> None:
        # cloudscraper handles ITviec's CF challenge; PoliteHttpClient adds
        # retries with exponential backoff and a configurable jitter sleep.
        # Sleep tuned per endpoint usage:
        #   - listing pages (~50 cards each): 1-2s — low-cost, indexable
        #   - AJAX /content (per-JD enrichment): 0.3-0.8s — not rate-limited
        #   - full detail with JSON-LD salary: callers should sleep more
        #     (CF gates after ~20 bursts); we leave that to the caller.
        self.client = PoliteHttpClient(
            extra_headers={
                "X-Crawler-Contact": settings.crawl_user_agent,
                "Accept-Language": "en-US,en;q=0.9,vi;q=0.8",
            },
            sleep_min=0.3,
            sleep_max=0.8,
        )

    # ── public interface ────────────────────────────────────────────

    def list_categories(self) -> list[str]:
        # Default to 'all' only — paginating /it-jobs covers every JD on the platform
        # in one pass, avoiding duplicate fetches across category-specific endpoints.
        # Callers wanting per-role data can still request specific keys explicitly.
        return ["all"]

    def crawl_listing(self, category: str, max_pages: int = 10) -> list[str]:
        """Return list of detail-page URLs for a category."""
        path = CATEGORY_PATHS.get(category)
        if not path:
            raise ValueError(f"Unknown category: {category}")

        urls: list[str] = []
        for page in range(1, max_pages + 1):
            page_url = f"{self.base_url}{path}?page={page}"
            try:
                html = self._get(page_url)
            except Exception as e:
                logger.warning("listing fetch failed page=%s: %s", page, e)
                break

            page_urls = self._extract_job_urls(html)
            if not page_urls:
                logger.info("no more JD cards at page %s, stopping", page)
                break

            urls.extend(page_urls)
            self._polite_sleep()

        seen, unique = set(), []
        for u in urls:
            if u not in seen:
                seen.add(u)
                unique.append(u)
        logger.info("category=%s: %d unique JD URLs", category, len(unique))
        return unique

    def crawl_category_rich(self, category: str, max_pages: int = 10) -> list[RawJD]:
        """Skip detail pages — parse RawJD directly from listing cards.

        Faster (1 fetch per ~25 JDs) and avoids triggering rate limits on detail pages.
        """
        path = CATEGORY_PATHS.get(category)
        if not path:
            raise ValueError(f"Unknown category: {category}")

        jds: list[RawJD] = []
        for page in range(1, max_pages + 1):
            page_url = f"{self.base_url}{path}?page={page}"
            try:
                html = self._get(page_url)
            except Exception as e:
                logger.warning("listing fetch failed page=%s: %s", page, e)
                break

            page_jds = self._parse_listing_cards(html, category)
            if not page_jds:
                logger.info("no more cards at page %s, stopping", page)
                break

            jds.extend(page_jds)
            self._polite_sleep()

        logger.info("category=%s: parsed %d JDs from listing", category, len(jds))
        return jds

    def fetch_description(self, url: str) -> Optional[str]:
        """Backwards-compat wrapper — returns just description text.

        For new code, prefer fetch_content_details() (richer) or
        fetch_full_jd_signal() (richest, also fetches JSON-LD salary).
        """
        details = self.fetch_content_details(url)
        return details.get("description") if details else None

    def fetch_full_jd_signal(self, url: str) -> Optional[dict]:
        """Combined fetch: AJAX content + full-detail JSON-LD for salary.

        ITviec splits the JD content across two endpoints:
          - `/it-jobs/<slug>/content?...` (AJAX) → description + work_mode
            + location_text. NOT Cloudflare-blocked.
          - `/it-jobs/<slug>?lab_feature=preview_jd_page` (full page) →
            JSON-LD JobPosting block with baseSalary. Cloudflare gates this
            after ~20 requests, so we fail soft on 403 and just return None
            for salary fields rather than blowing up the crawl.

        Returns:
          {
            "description": str | None,
            "salary_min": int | None,
            "salary_max": int | None,
            "salary_currency": str | None,
            "work_mode": str | None,
            "location_text": str | None,
          }
        """
        details = self.fetch_content_details(url) or {}
        smin, smax, scur = self._fetch_jsonld_salary(url)
        if smin is not None: details["salary_min"] = smin
        if smax is not None: details["salary_max"] = smax
        if scur: details["salary_currency"] = scur
        return details

    def _fetch_jsonld_salary(self, url: str) -> tuple[Optional[int], Optional[int], Optional[str]]:
        """Fetch the full detail page and pull `baseSalary` from its JSON-LD
        JobPosting block. Returns (min, max, currency) or all-None on failure.

        Cloudflare gates this endpoint aggressively (typically 403 after ~10
        bursts). We add an extra 2-4s jitter sleep BEFORE each fetch — beyond
        the AJAX sleep — to keep CF happy across long crawls. Failure is
        treated as "salary not available" rather than retried.
        """
        import json as _json
        import random as _random
        import time as _time
        _time.sleep(_random.uniform(2.0, 4.0))
        try:
            html = self._get(url)
        except Exception:
            return None, None, None
        soup = BeautifulSoup(html, "html.parser")
        for sc in soup.select('script[type="application/ld+json"]'):
            try:
                data = _json.loads(sc.string or "")
            except Exception:
                continue
            if isinstance(data, dict) and data.get("@type") == "JobPosting":
                base = data.get("baseSalary")
                if not isinstance(base, dict):
                    return None, None, None
                cur = base.get("currency")
                sv = base.get("value") or {}
                if not isinstance(sv, dict):
                    return None, None, cur
                smin = sv.get("minValue")
                smax = sv.get("maxValue")
                return (
                    int(smin) if isinstance(smin, (int, float)) and smin > 0 else None,
                    int(smax) if isinstance(smax, (int, float)) and smax > 0 else None,
                    cur,
                )
        return None, None, None

    def fetch_content_details(self, url: str) -> Optional[dict]:
        """Fetch full content pane via `/it-jobs/<slug>/content` AJAX endpoint.

        Returns a dict with all structured fields the pane exposes:
          description   — concatenated text of job-description + job-experiences
          salary_min    — int (if numeric salary shown; None when 'You'll love it')
          salary_max    — int
          salary_currency — 'USD' / 'VND'
          work_mode     — onsite / hybrid / remote (parsed from preview-job-overview)
          location_text — full location string ('Tower 2 (T26) Times City, ...')

        The AJAX endpoint is NOT Cloudflare-blocked (the full /it-jobs/<slug>
        page is), so we can crawl this at ~0.4s per JD even on cold IPs.
        Some employers gate salary behind sign-in — those JDs show 'You'll
        love it' instead of numbers; we return None for salary_* in that case.
        """
        slug = self._extract_slug(url)
        if not slug:
            return None
        content_url = f"{self.base_url}/it-jobs/{slug}/content?job_index=0&locale=en"
        try:
            html = self._get(content_url)
        except Exception as e:
            logger.warning("content fetch failed slug=%s: %s", slug, e)
            return None
        soup = BeautifulSoup(html, "html.parser")

        # ── description: 3 sections + heading labels ───────────────────
        parts: list[str] = []
        for sec_class, label in (
            ("job-description", "Job description"),
            ("job-experiences", "Your skills and experience"),
            ("job-why-love-working", "Why you'll love working here"),
        ):
            sec = soup.select_one(f"section.{sec_class}")
            if not sec:
                continue
            body = sec.select_one(".paragraph") or sec
            text = body.get_text(" ", strip=True)
            if text:
                parts.append(f"{label}\n\n{text}")
        if not parts:
            legacy = soup.select_one("section.job-content, .job-content, .preview-content")
            if legacy:
                txt = legacy.get_text(" ", strip=True)
                if txt:
                    parts.append(txt)
        description = "\n\n".join(parts) or None

        # ── salary: `.salary.text-success-color span` of preview header ─
        # When the employer chose to hide it, the span reads "You'll love it"
        # (or sometimes "Sign in to view salary"). Those are not numeric →
        # parse_salary returns (None, None, None) and we leave the fields None.
        salary_min = salary_max = salary_currency = None
        sal_el = soup.select_one(".preview-job-header .salary span, .salary.text-success-color span")
        if sal_el:
            sal_text = sal_el.get_text(strip=True)
            salary_min, salary_max, salary_currency = self._parse_salary_text(sal_text)

        # ── work_mode: preview-job-overview has the "At office" / "Hybrid"
        # / "Remote" badge. Map to canonical enum.
        work_mode = None
        for badge in soup.select(".preview-job-overview .preview-header-item span"):
            t = badge.get_text(strip=True).lower()
            if t in {"at office", "onsite", "on-site", "on site", "làm việc tại văn phòng"}:
                work_mode = "onsite"
                break
            if t in {"hybrid"}:
                work_mode = "hybrid"
                break
            if t in {"remote", "fully remote"}:
                work_mode = "remote"
                break

        # ── location_text: first map-pin span in overview ───────────────
        location_text = None
        loc_el = soup.select_one(".preview-job-overview .small-text.text-rich-grey")
        if loc_el:
            location_text = loc_el.get_text(strip=True)

        return {
            "description": description,
            "salary_min": salary_min,
            "salary_max": salary_max,
            "salary_currency": salary_currency,
            "work_mode": work_mode,
            "location_text": location_text,
        }

    def crawl_detail(self, url: str) -> Optional[RawJD]:
        """Legacy detail-page entry point — now delegates to the listing parser.

        The pipeline calls this when `fetch_details=True`. Because the full
        detail page is Cloudflare-blocked, we instead rely on the listing
        cards (already parsed in crawl_category_rich) and just enrich them
        with description via fetch_description(). The pipeline's standard
        path uses crawl_category_rich() and then merges descriptions.

        Kept for interface compatibility; new code should call
        crawl_category_rich() + fetch_description() directly.
        """
        return None

    @staticmethod
    def _extract_slug(url: str) -> Optional[str]:
        """Pull the slug out of `https://itviec.com/it-jobs/<slug>?...` URLs."""
        if not url:
            return None
        marker = "/it-jobs/"
        if marker not in url:
            return None
        tail = url.split(marker, 1)[1]
        slug = tail.split("?")[0].split("/")[0].strip("/")
        return slug or None

    def health_check(self) -> bool:
        """Verify listing page still parses correctly."""
        try:
            jds = self.crawl_category_rich("backend", max_pages=1)
            if not jds:
                logger.error("health_check: parsed 0 JDs from backend listing")
                return False
            first = jds[0]
            ok = bool(first.title and first.posted_date and first.skills_raw)
            logger.info("health_check: %s (sample title=%s, %d skills)",
                        "OK" if ok else "FAIL", first.title, len(first.skills_raw))
            return ok
        except Exception as e:
            logger.exception("health_check raised: %s", e)
            return False

    # ── parsing ─────────────────────────────────────────────────────

    def _extract_job_urls(self, html: str) -> list[str]:
        """Extract canonical JD detail URLs from a listing page."""
        soup = BeautifulSoup(html, "html.parser")
        urls = []
        for card in soup.select("div.job-card"):
            slug = card.get("data-search--job-selection-job-slug-value")
            if not slug:
                continue
            urls.append(f"{self.base_url}/it-jobs/{slug}?lab_feature=preview_jd_page")
        return urls

    def _parse_listing_cards(self, html: str, category: str) -> list[RawJD]:
        soup = BeautifulSoup(html, "html.parser")
        out: list[RawJD] = []
        for card in soup.select("div.job-card"):
            jd = self._parse_card(card, category)
            if jd is not None:
                out.append(jd)
        return out

    @staticmethod
    def _infer_role_from_card(card) -> Optional[str]:
        """Return the ITviec role slug shown on the card (e.g. 'backend-developer',
        'data-analyst').

        Heuristic: the role badge link points to a short slug like
        `/it-jobs/backend-developer` (with a `title` attribute), while the JD
        permalink has a long slug ending in a numeric id like
        `/it-jobs/senior-backend-engineer-...-company-3014?lab_feature=...`.
        We pick the link whose path-only portion is short (≤ 3 dash segments)
        and does NOT end in a numeric suffix — that's the role taxonomy entry.
        """
        import re as _re
        for a in card.select('a[href^="/it-jobs/"]'):
            href = a.get("href", "")
            path = href.replace("/it-jobs/", "").split("?")[0].strip("/")
            if not path:
                continue
            # Skip the JD permalink itself (ends with numeric id like "-3014")
            if _re.search(r"-\d{3,}$", path):
                continue
            # Role slugs are short (1-3 dash segments): "backend-developer",
            # "ux-ui-designer", "data-analyst"
            if path.count("-") > 3:
                continue
            return path
        return None

    def _parse_card(self, card, category: str) -> Optional[RawJD]:
        try:
            slug = card.get("data-search--job-selection-job-slug-value")
            if not slug:
                return None

            url = f"{self.base_url}/it-jobs/{slug}?lab_feature=preview_jd_page"

            title_el = card.select_one("h3.text-break")
            title = title_el.get_text(strip=True) if title_el else None
            if not title:
                return None

            # Company: <a href="/companies/<slug>"> text
            company = None
            company_el = card.select_one('a.text-rich-grey[href*="/companies/"]')
            if company_el:
                company = company_el.get_text(strip=True)

            # Skill tags
            skills_raw = []
            for tag in card.select("a.itag.itag-light"):
                txt = tag.get_text(strip=True)
                if txt:
                    skills_raw.append(txt)
            # +N more tag (e.g. "+2") may have data-bs-original-title="Microservices, AWS"
            more_tag = card.select_one('div.itag[data-bs-original-title]')
            if more_tag:
                more_text = more_tag.get("data-bs-original-title", "")
                for extra in more_text.split(","):
                    extra = extra.strip()
                    if extra:
                        skills_raw.append(extra)
            skills_raw = list(dict.fromkeys(skills_raw))

            # Location: div with title attribute, next to map-pin icon
            location = None
            loc_el = card.select_one("div.text-rich-grey.text-truncate.text-nowrap[title]")
            if loc_el:
                location = loc_el.get("title") or loc_el.get_text(strip=True)

            # Posted: <span class="small-text text-dark-grey">Posted 1 day ago</span>
            posted_text = None
            for span in card.select("span.small-text.text-dark-grey"):
                t = span.get_text(" ", strip=True)
                if "posted" in t.lower() or "ago" in t.lower():
                    posted_text = t
                    break
            posted_date = self._parse_posted_date(posted_text)

            # Experience level from title (Senior / Junior / etc.)
            exp_level = self._parse_exp_level(title)

            return RawJD(
                source=self.source_name,
                source_id=slug,
                title=title,
                company=company,
                description="",  # listing card has bullet-point teasers only; fetch detail if needed
                skills_raw=skills_raw,
                salary_min=None,
                salary_max=None,
                salary_currency=None,
                location=location,
                exp_level=exp_level,
                posted_date=posted_date,
                url=url,
                role_hint=self._infer_role_from_card(card),
            )
        except Exception as e:
            logger.warning("card parse failed: %s", e)
            return None

    def _parse_detail_page(self, soup: BeautifulSoup, url: str) -> Optional[RawJD]:
        """Parse a standalone JD detail page.

        ITviec embeds a schema.org JobPosting JSON-LD block on every detail
        page — we use it as the source of truth for structured fields (dates,
        location, salary, industry, monthsOfExperience). Falls back to HTML
        selectors when JSON-LD is missing.
        """
        import json as _json

        try:
            slug = url.split("/it-jobs/")[-1].split("?")[0]
            title_el = soup.select_one("h1, h3.text-break")
            title = title_el.get_text(strip=True) if title_el else None
            if not title:
                return None

            # ── JSON-LD JobPosting ─────────────────────────────────────────
            ld: dict = {}
            for sc in soup.select('script[type="application/ld+json"]'):
                try:
                    data = _json.loads(sc.string or "")
                except Exception:
                    continue
                if isinstance(data, dict) and data.get("@type") == "JobPosting":
                    ld = data
                    break

            # ── Company ────────────────────────────────────────────────────
            company = (
                (ld.get("hiringOrganization") or {}).get("name")
                if isinstance(ld.get("hiringOrganization"), dict) else None
            )
            if not company:
                company_el = soup.select_one('a[href*="/companies/"]')
                company = company_el.get_text(strip=True) if company_el else None

            # ── Description (decoded from JSON-LD when available) ──────────
            description = ""
            ld_desc = ld.get("description") or ""
            if ld_desc:
                # description is HTML-escaped; strip tags to plain text
                description = BeautifulSoup(ld_desc, "html.parser").get_text("\n", strip=True)
            if not description:
                desc_el = (
                    soup.select_one("section.job-content")
                    or soup.select_one(".job-description")
                    or soup.select_one(".preview-content")
                )
                description = desc_el.get_text("\n", strip=True) if desc_el else ""

            # ── Skill tags (scoped to main job, NOT "More jobs for you") ───
            # ITviec re-uses .itag.itag-light for similar-job cards at the
            # bottom of the page. We restrict to the main job container and
            # also drop any anchor whose href has ?lab_feature=similar_job.
            main = (
                soup.select_one("section.preview-job-overview")
                or soup.select_one("section.job-content")
                or soup.select_one(".preview-job-wrapper")
                or soup
            )
            skills_raw = []
            for t in main.select("a.itag.itag-light"):
                href = t.get("href", "") or ""
                if "lab_feature=similar_job" in href:
                    continue
                txt = t.get_text(strip=True)
                if txt:
                    skills_raw.append(txt)
            skills_raw = list(dict.fromkeys(skills_raw))
            # Fallback: comma-separated string in JSON-LD
            if not skills_raw and ld.get("skills"):
                skills_raw = [s.strip() for s in str(ld["skills"]).split(",") if s.strip()]

            # ── Location (JSON-LD addressRegion or HTML title attr) ────────
            location = None
            ld_locs = ld.get("jobLocation") or []
            if isinstance(ld_locs, dict):
                ld_locs = [ld_locs]
            for loc in ld_locs:
                addr = loc.get("address", {}) if isinstance(loc, dict) else {}
                region = (addr.get("addressRegion") or "").strip()
                city = (addr.get("addressLocality") or "").strip()
                if region and region.lower() not in {"not available", "n/a", ""}:
                    location = region
                    break
                if city and city.lower() not in {"not available", "n/a", ""}:
                    location = city
                    break
            if not location:
                loc_el = soup.select_one("div.text-rich-grey.text-truncate.text-nowrap[title]")
                if loc_el:
                    location = loc_el.get("title") or loc_el.get_text(strip=True)

            # ── Salary (JSON-LD baseSalary) ────────────────────────────────
            salary_min = salary_max = None
            salary_currency = None
            base_sal = ld.get("baseSalary") if isinstance(ld.get("baseSalary"), dict) else None
            if base_sal:
                sv = base_sal.get("value") or {}
                if isinstance(sv, dict):
                    smin = sv.get("minValue")
                    smax = sv.get("maxValue")
                    if isinstance(smin, (int, float)) and smin > 0:
                        salary_min = int(smin)
                    if isinstance(smax, (int, float)) and smax > 0:
                        salary_max = int(smax)
                # Only set currency when we actually extracted salary value.
                # Without a value, currency is meaningless and pollutes Market Intel.
                if salary_min is not None or salary_max is not None:
                    salary_currency = base_sal.get("currency")
            # Fallback: parse salary text from HTML card ("1,000 - 1,800 USD")
            if salary_min is None and salary_max is None:
                sal_el = soup.select_one(".salary .ips-2.fw-500, span.salary")
                if sal_el:
                    parsed = self._parse_salary_text(sal_el.get_text(" ", strip=True))
                    if parsed:
                        salary_min, salary_max, salary_currency = parsed

            # ── Posted date (JSON-LD datePosted) ───────────────────────────
            posted_date_val = date.today()
            if ld.get("datePosted"):
                try:
                    posted_date_val = date.fromisoformat(ld["datePosted"][:10])
                except Exception:
                    pass

            # ── Work mode badge ("At office" / "Hybrid" / "Remote") ────────
            # Lives in the preview header, not in description. We surface it
            # into `description` so the downstream extractor picks it up.
            for txt in soup.find_all(string=re.compile(r"^(At office|Hybrid|Remote|Onsite|On-site)$", re.I)):
                description = f"{description}\nWork mode: {txt.strip()}"
                break

            return RawJD(
                source=self.source_name,
                source_id=slug,
                title=title,
                company=company,
                description=description,
                skills_raw=skills_raw,
                salary_min=salary_min,
                salary_max=salary_max,
                salary_currency=salary_currency,
                location=location,
                exp_level=self._parse_exp_level(title),
                posted_date=posted_date_val,
                url=url,
            )
        except Exception as e:
            logger.exception("detail parse failed url=%s: %s", url, e)
            return None

    # ── utilities ───────────────────────────────────────────────────

    def _get(self, url: str) -> str:
        return self.client.get(url)

    def _polite_sleep(self) -> None:
        self.client.polite_sleep()

    @staticmethod
    def _parse_exp_level(text: Optional[str]) -> Optional[str]:
        if not text:
            return None
        t = text.lower()
        if "senior" in t or "principal" in t or "lead" in t:
            return "senior"
        if "junior" in t or "fresher" in t or "fresh" in t or "intern" in t:
            return "junior"
        if "middle" in t or " mid " in t or "mid-" in t:
            return "mid"
        return None

    @staticmethod
    def _parse_salary_text(text: str) -> Optional[tuple[int, int, str]]:
        """Parse ITviec salary spans like '1,000 - 1,800 USD' or '20.000.000 – 30.000.000'.
        Returns (min, max, currency) or None when not parseable.
        """
        if not text:
            return None
        # USD-style with comma separator
        m = re.search(r"([\d,]+)\s*[-–]\s*([\d,]+)\s*(USD|VND)?", text, re.I)
        if m:
            lo = int(m.group(1).replace(",", ""))
            hi = int(m.group(2).replace(",", ""))
            cur = (m.group(3) or "USD").upper()
            if lo > 0 and hi > 0:
                return lo, hi, cur
        # VND-style with dot separator (e.g. 20.000.000)
        m = re.search(r"(\d{1,3}(?:\.\d{3})+)\s*[-–]\s*(\d{1,3}(?:\.\d{3})+)", text)
        if m:
            lo = int(m.group(1).replace(".", ""))
            hi = int(m.group(2).replace(".", ""))
            if lo > 0 and hi > 0:
                return lo, hi, "VND"
        return None

    @staticmethod
    def _parse_posted_date(text: Optional[str]) -> date:
        """ITviec shows 'Posted N day(s)/hour(s)/week(s)/month(s) ago'."""
        if not text:
            return date.today()
        t = text.lower()
        m = re.search(r"(\d+)\s*(hour|day|week|month)", t)
        if not m:
            return date.today()
        n = int(m.group(1))
        unit = m.group(2)
        today = date.today()
        if unit == "hour":
            return today
        if unit == "day":
            return today - timedelta(days=n)
        if unit == "week":
            return today - timedelta(days=n * 7)
        if unit == "month":
            return today - timedelta(days=n * 30)
        return today
