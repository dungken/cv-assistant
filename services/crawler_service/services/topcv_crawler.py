"""TopCVCrawler — crawl JDs from topcv.vn.

Strategy (based on 2026-05 HTML inspection):
- Listing URL: https://www.topcv.vn/tim-viec-lam-lap-trinh-vien?type_keyword=1&sba=1
- Each JD card: <div class="job-item-search-result" data-job-id="...">
  Contains: title, company, salary (visible!), location.
- Detail pages return 403 with cloudscraper. So we use listing-only data.
- Skill tags: NOT visible in listing → skills_raw is empty here; downstream
  skill_service can run NER on the description (but we can't fetch description
  either). For now we mark TopCV JDs with empty skills_raw — relying on title
  to extract approximate skills.

Categories: TopCV uses search-keyword URLs rather than fixed category paths.
We hardcode a few useful keyword combinations.
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

logger = logging.getLogger(__name__)


# TopCV doesn't have nice category slugs like ITviec. We use keyword search.
CATEGORY_QUERIES = {
    "backend": "lap-trinh-backend",
    "frontend": "lap-trinh-frontend",
    "fullstack": "lap-trinh-fullstack",
    "mobile": "lap-trinh-mobile",
    "devops": "devops",
    "data": "data-engineer",
    "ai": "ai-engineer",
}

# Map TopCV category → (canonical role slug aligned with ITviec, role_group)
# Lets us populate role/role_group columns consistently across sources.
CATEGORY_TO_ROLE = {
    "backend":   ("backend-developer",       "web_application_development"),
    "frontend":  ("frontend-developer",      "web_application_development"),
    "fullstack": ("fullstack-developer",     "web_application_development"),
    "mobile":    ("mobile-application-developer", "mobile_application_development"),
    "devops":    ("devops-engineer",         "devops_and_site_reliability_sre"),
    "data":      ("data-engineer",           "data_engineering"),
    "ai":        ("ai-machine-learning-engineer", "data_science_and_ai_machine_learning"),
}


class TopCVCrawler(IJDCrawler):
    source_name = "topcv"
    base_url = "https://www.topcv.vn"

    def __init__(self, fetch_details: bool = False) -> None:
        # fetch_details=True requires bypassing Cloudflare Turnstile, which
        # as of 2026-05 blocks headless Chrome consistently. See README.md.
        # When False, skills are extracted from title via ontology matching
        # in pipeline.py — recovers ~78% of skills (avg 1.2 skills/JD).
        self.client = PoliteHttpClient(
            extra_headers={
                "X-Crawler-Contact": settings.crawl_user_agent,
                "Accept-Language": "vi-VN,vi;q=0.9,en;q=0.8",
            }
        )
        # When True, use Selenium to fetch each detail page for description text.
        # ~3-5s per JD; required to get skills since listing cards lack them.
        self.fetch_details = fetch_details
        self._selenium = None  # lazy

    # ── public interface ────────────────────────────────────────────

    def list_categories(self) -> list[str]:
        return list(CATEGORY_QUERIES.keys())

    def crawl_listing(self, category: str, max_pages: int = 10) -> list[str]:
        keyword = CATEGORY_QUERIES.get(category)
        if not keyword:
            raise ValueError(f"Unknown category: {category}")

        urls: list[str] = []
        for page in range(1, max_pages + 1):
            page_url = (
                f"{self.base_url}/tim-viec-lam-{keyword}"
                f"?type_keyword=1&sba=1&page={page}"
            )
            try:
                html = self._get(page_url)
            except Exception as e:
                logger.warning("listing fetch failed page=%s: %s", page, e)
                break
            page_urls = self._extract_job_urls(html)
            if not page_urls:
                logger.info("no more cards at page %s, stopping", page)
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
        """Parse RawJD directly from listing cards (detail pages are 403-blocked)."""
        keyword = CATEGORY_QUERIES.get(category)
        if not keyword:
            raise ValueError(f"Unknown category: {category}")

        jds: list[RawJD] = []
        consecutive_failures = 0
        for page in range(1, max_pages + 1):
            page_url = (
                f"{self.base_url}/tim-viec-lam-{keyword}"
                f"?type_keyword=1&sba=1&page={page}"
            )
            try:
                html = self._get(page_url)
                consecutive_failures = 0
            except Exception as e:
                consecutive_failures += 1
                # TopCV throttles aggressively. Back off a long time on 403,
                # but don't give up after the first failure since CF challenges
                # may resolve on their own after a cool-down.
                logger.warning(
                    "topcv listing fetch failed cat=%s page=%s (%d/3): %s",
                    category, page, consecutive_failures, e,
                )
                if consecutive_failures >= 3:
                    logger.error("topcv category=%s aborted after 3 failures", category)
                    break
                # Long cool-down before retrying this page
                import time
                time.sleep(15.0)
                continue

            page_jds = self._parse_listing_cards(html, category)
            if not page_jds:
                logger.info("no more cards at page %s, stopping", page)
                break

            jds.extend(page_jds)
            self._polite_sleep()

        logger.info("category=%s: parsed %d JDs from listing", category, len(jds))

        if self.fetch_details and jds:
            self._enrich_with_descriptions(jds)

        return jds

    def crawl_detail(self, url: str) -> Optional[RawJD]:
        """Fetch a single detail page via Selenium. Returns RawJD with description filled."""
        html = self._fetch_detail_html(url)
        if not html:
            return None
        soup = BeautifulSoup(html, "html.parser")
        title = soup.select_one("h1.job-detail__info--title")
        if not title:
            return None
        desc = self._extract_description(soup)
        # Build a minimal RawJD (caller typically already has more data from listing)
        return RawJD(
            source=self.source_name,
            source_id=url.split("/")[-1].replace(".html", ""),
            title=title.get_text(strip=True),
            company=None,
            description=desc,
            skills_raw=[],
            posted_date=date.today(),
            url=url,
        )

    # ── detail enrichment via Selenium ──────────────────────────────

    def _enrich_with_descriptions(self, jds: list[RawJD]) -> None:
        """For each JD, fetch its detail page and fill in description.

        Selenium is required because TopCV detail pages have a JS challenge
        that cloudscraper does not solve. We keep one driver alive across
        all fetches to amortize ~3-5s startup cost.
        """
        from services.crawler_service.services.selenium_session import SeleniumSession

        logger.info("Enriching %d JDs with detail descriptions (Selenium)…", len(jds))
        enriched = 0
        with SeleniumSession() as sess:
            sess.warmup(f"{self.base_url}/")
            for i, jd in enumerate(jds, start=1):
                html = sess.fetch(jd.url)
                if not html:
                    continue
                soup = BeautifulSoup(html, "html.parser")
                desc = self._extract_description(soup)
                if desc:
                    jd.description = desc
                    enriched += 1
                if i % 10 == 0:
                    logger.info("  enriched %d/%d", i, len(jds))
        logger.info("Enriched %d/%d JDs with descriptions", enriched, len(jds))

    def _fetch_detail_html(self, url: str) -> str:
        from services.crawler_service.services.selenium_session import SeleniumSession

        if self._selenium is None:
            self._selenium = SeleniumSession()
            self._selenium.warmup(f"{self.base_url}/")
        return self._selenium.fetch(url)

    @staticmethod
    def _extract_description(soup: BeautifulSoup) -> str:
        """Concatenate all sections of the job description into one text blob.

        Sections: 'Mô tả công việc', 'Yêu cầu ứng viên', 'Quyền lợi'.
        Skill extraction (downstream) runs ontology matching on this text.
        """
        parts = []
        for item in soup.select(".job-description__item"):
            heading = item.find("h3")
            content = item.select_one(".job-description__item--content")
            if heading and content:
                parts.append(heading.get_text(strip=True))
                parts.append(content.get_text(" ", strip=True))
        return "\n".join(parts)

    def health_check(self) -> bool:
        try:
            jds = self.crawl_category_rich("backend", max_pages=1)
            if not jds:
                logger.error("health_check: parsed 0 JDs")
                return False
            first = jds[0]
            ok = bool(first.title and first.url and first.posted_date)
            logger.info("health_check: %s (sample title=%s)",
                        "OK" if ok else "FAIL", first.title)
            return ok
        except Exception as e:
            logger.exception("health_check raised: %s", e)
            return False

    # ── parsing ─────────────────────────────────────────────────────

    def _extract_job_urls(self, html: str) -> list[str]:
        soup = BeautifulSoup(html, "html.parser")
        urls = []
        for card in soup.select("div.job-item-search-result"):
            link = card.select_one("h3.title a, a.company")  # title link first
            if not link:
                continue
            href = link.get("href", "").split("?")[0]
            if href:
                urls.append(href)
        return urls

    def _parse_listing_cards(self, html: str, category: str) -> list[RawJD]:
        soup = BeautifulSoup(html, "html.parser")
        out: list[RawJD] = []
        for card in soup.select("div.job-item-search-result"):
            jd = self._parse_card(card, category)
            if jd is not None:
                out.append(jd)
        return out

    def _parse_card(self, card, category: str) -> Optional[RawJD]:
        try:
            job_id = card.get("data-job-id")
            if not job_id:
                return None

            title_link = card.select_one("h3.title a")
            if not title_link:
                return None
            url = title_link.get("href", "").split("?")[0]
            title = title_link.get_text(strip=True)
            if not title:
                return None

            company_el = card.select_one("a.company span.company-name")
            company = company_el.get_text(strip=True) if company_el else None

            # Salary — visible on TopCV (unlike ITviec)
            salary_el = card.select_one("label.title-salary, label.salary span")
            salary_text = salary_el.get_text(strip=True) if salary_el else None
            salary_min, salary_max, currency = self._parse_salary(salary_text)

            # Location
            loc_el = card.select_one("span.city-text, label.address span")
            location = loc_el.get_text(strip=True) if loc_el else None

            # Skill tags (TopCV uses .tag-required-skills or similar; check defensively)
            skills_raw = [
                el.get_text(strip=True)
                for el in card.select(".tag-required-skills li, .skill-required-tag, .tag-job-skill")
                if el.get_text(strip=True)
            ]
            skills_raw = list(dict.fromkeys(skills_raw))

            # Posted time — TopCV often has "Cập nhật N giờ trước" or similar
            posted_el = card.select_one(".job-update-at, .created-at, .label-time")
            posted_date = self._parse_posted_date(
                posted_el.get_text(strip=True) if posted_el else None
            )

            # TopCV listings don't expose role badges like ITviec, so we lift
            # the role from the category being crawled. role_hint flows through
            # the pipeline and ends up populating jd_raw.role.
            role_slug, _ = CATEGORY_TO_ROLE.get(category, (category, None))

            return RawJD(
                source=self.source_name,
                source_id=job_id,
                title=title,
                company=company,
                description="",  # not fetchable from listing
                skills_raw=skills_raw,
                salary_min=salary_min,
                salary_max=salary_max,
                salary_currency=currency,
                location=location,
                exp_level=self._parse_exp_level(title),
                posted_date=posted_date,
                url=url,
                role_hint=role_slug,
            )
        except Exception as e:
            logger.warning("card parse failed: %s", e)
            return None

    # ── utilities ───────────────────────────────────────────────────

    def _get(self, url: str) -> str:
        return self.client.get(url)

    def _polite_sleep(self) -> None:
        self.client.polite_sleep()

    @staticmethod
    def _parse_salary(text: Optional[str]) -> tuple[Optional[int], Optional[int], Optional[str]]:
        """Parse Vietnamese salary text.

        Examples handled:
            '30 - 60 triệu'     → 30M, 60M VND
            '1 - 3 triệu'       → 1M, 3M VND
            '25 triệu'          → 25M, 25M VND
            'Tới 1,500 USD'     → None, 1500 USD     (upper bound only)
            'Từ 800 USD'        → 800, None USD      (lower bound only)
            '1,500 - 2,000 USD' → 1500, 2000 USD
            'Thoả thuận'        → all None
        """
        if not text:
            return None, None, None
        t = text.lower().strip()
        if "thoả thuận" in t or "thỏa thuận" in t or "negotiable" in t:
            return None, None, None

        currency = "USD" if "$" in text or "usd" in t else "VND"
        multiplier = 1_000_000 if "triệu" in t else 1

        # Strip thousand-separator commas BEFORE extracting numbers
        # so "1,500" becomes "1500", not "1" and "500".
        normalized = t.replace(",", "").replace(".", "")
        nums = [int(n) for n in re.findall(r"\d+", normalized)]
        if not nums:
            return None, None, currency

        # "Tới X" / "up to X" → only max bound is given
        is_upper_only = bool(re.search(r"\b(tới|đến|up\s*to|max)\b", t))
        # "Từ X" / "from X" → only min bound is given
        is_lower_only = bool(re.search(r"\b(từ|from|min)\b", t)) and not is_upper_only

        if is_upper_only and len(nums) == 1:
            return None, nums[0] * multiplier, currency
        if is_lower_only and len(nums) == 1:
            return nums[0] * multiplier, None, currency
        if len(nums) == 1:
            return nums[0] * multiplier, nums[0] * multiplier, currency
        return min(nums[:2]) * multiplier, max(nums[:2]) * multiplier, currency

    @staticmethod
    def _parse_exp_level(text: Optional[str]) -> Optional[str]:
        if not text:
            return None
        t = text.lower()
        if "senior" in t or "principal" in t or "lead" in t or "trưởng" in t:
            return "senior"
        if "junior" in t or "fresher" in t or "intern" in t or "thực tập" in t:
            return "junior"
        if "middle" in t or " mid " in t:
            return "mid"
        return None

    @staticmethod
    def _parse_posted_date(text: Optional[str]) -> date:
        """TopCV: 'Cập nhật N giờ/ngày/tuần trước' or '3 days ago'. Fallback today."""
        if not text:
            return date.today()
        t = text.lower()
        m = re.search(r"(\d+)\s*(giờ|hour|ngày|day|tuần|week|tháng|month)", t)
        if not m:
            return date.today()
        n = int(m.group(1))
        unit = m.group(2)
        today = date.today()
        if unit in ("giờ", "hour"):
            return today
        if unit in ("ngày", "day"):
            return today - timedelta(days=n)
        if unit in ("tuần", "week"):
            return today - timedelta(days=n * 7)
        if unit in ("tháng", "month"):
            return today - timedelta(days=n * 30)
        return today
