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
        self.client = PoliteHttpClient(
            extra_headers={
                "X-Crawler-Contact": settings.crawl_user_agent,
                "Accept-Language": "en-US,en;q=0.9,vi;q=0.8",
            }
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

    def crawl_detail(self, url: str) -> Optional[RawJD]:
        """Fetch a single JD detail page. Used when description text is needed.

        Most fields are already available from crawl_category_rich; this is a fallback.
        """
        try:
            html = self._get(url)
        except Exception as e:
            logger.warning("detail fetch failed url=%s: %s", url, e)
            return None
        soup = BeautifulSoup(html, "html.parser")
        return self._parse_detail_page(soup, url)

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
        'data-analyst'). This is the slug from the role badge link — the only
        a[href^=/it-jobs/] that has a 'title' attribute and no '?click_source'.

        We store the raw slug rather than mapping to a coarser bucket so the
        analytics layer can group flexibly later (SQL CASE or Python helper).
        """
        for a in card.select('a[href^="/it-jobs/"]'):
            href = a.get("href", "")
            if "?click_source=" in href:
                continue
            if not a.get("title"):
                continue
            slug = href.replace("/it-jobs/", "").split("?")[0]
            return slug or None
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
        """Parse a standalone JD detail page (preview_jd_page variant)."""
        try:
            slug = url.split("/it-jobs/")[-1].split("?")[0]
            title_el = soup.select_one("h1, h3.text-break")
            title = title_el.get_text(strip=True) if title_el else None
            if not title:
                return None

            company_el = soup.select_one('a[href*="/companies/"]')
            company = company_el.get_text(strip=True) if company_el else None

            # JD description: ITviec wraps full description in various containers
            desc_el = soup.select_one(".job-description, .preview-content, .content")
            description = desc_el.get_text("\n", strip=True) if desc_el else ""

            skills_raw = [
                t.get_text(strip=True)
                for t in soup.select("a.itag.itag-light")
                if t.get_text(strip=True)
            ]
            skills_raw = list(dict.fromkeys(skills_raw))

            return RawJD(
                source=self.source_name,
                source_id=slug,
                title=title,
                company=company,
                description=description,
                skills_raw=skills_raw,
                salary_min=None,
                salary_max=None,
                salary_currency=None,
                location=None,
                exp_level=self._parse_exp_level(title),
                posted_date=date.today(),
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
