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
        # Sleep tuned for the AJAX `/job-view-detail` endpoint which is not
        # CF-protected — the ~3-6s default was overkill and made enrichment
        # take 10x longer than necessary.
        self.client = PoliteHttpClient(
            extra_headers={
                "X-Crawler-Contact": settings.crawl_user_agent,
                "Accept-Language": "vi-VN,vi;q=0.9,en;q=0.8",
            },
            sleep_min=0.3,
            sleep_max=0.8,
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
        """Legacy entry point — superseded by listing rich + fetch_description.

        TopCV's standalone detail page sits behind Cloudflare Turnstile, so
        the full-page Selenium path is no longer used. The pipeline calls
        crawl_category_rich() for structured fields and fetch_description()
        for the description text via the AJAX `/job-view-detail` endpoint.
        """
        return None

    def fetch_description(self, url: str) -> Optional[str]:
        """Fetch description text via TopCV's AJAX `/job-view-detail` endpoint.

        Discovered via the in-page "quick view" panel: clicking a job card on
        the listing fires `GET /job-view-detail?id=<job_id>`, which returns
        a small JSON envelope with the rendered HTML for the right pane.
        This endpoint is NOT protected by Cloudflare Turnstile (the standalone
        detail page is), so we can crawl descriptions at ~0.3s per JD.
        """
        import json as _json
        job_id = self._extract_job_id(url)
        if not job_id:
            return None
        api_url = f"{self.base_url}/job-view-detail?id={job_id}"
        try:
            body = self._get(api_url, ajax=True)
            payload = _json.loads(body)
        except Exception as e:
            logger.warning("topcv fetch_description failed id=%s: %s", job_id, e)
            return None
        if payload.get("status") != "success":
            return None
        html = (payload.get("data") or {}).get("html_job_detail") or ""
        if not html:
            return None
        soup = BeautifulSoup(html, "html.parser")
        # The body of interest is .box-job-info; it contains 3-4 sections
        # ("Mô tả công việc", "Yêu cầu ứng viên", "Quyền lợi", "Thời gian làm việc")
        # plus the company info card. Concatenate the content-tab blocks plus
        # their headings so downstream NER can use section context.
        parts: list[str] = []
        info = soup.select_one(".box-job-info")
        if info:
            for el in info.find_all(["h3", "div"], recursive=True):
                if el.name == "h3":
                    parts.append(el.get_text(" ", strip=True))
                elif "content-tab" in (el.get("class") or []):
                    parts.append(el.get_text(" ", strip=True))
        text = "\n\n".join(p for p in parts if p)
        return text or None

    @staticmethod
    def _extract_job_id(url: str) -> Optional[str]:
        """Pull the numeric job_id out of a TopCV detail URL.

        Pattern: https://www.topcv.vn/viec-lam/<slug>/<job_id>.html[?...]
        """
        if not url:
            return None
        import re as _re
        m = _re.search(r"/(\d+)\.html", url)
        return m.group(1) if m else None

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

            # Title — prefer the tooltip's `data-original-title` (full text;
            # the visible <span> truncates long titles to "...")
            title_link = card.select_one("h3.title a")
            if not title_link:
                return None
            url = title_link.get("href", "").split("?")[0]
            title_span = title_link.select_one("span[data-original-title]")
            title = (
                title_span.get("data-original-title", "").strip()
                if title_span else title_link.get_text(strip=True)
            )
            if not title:
                return None

            # Company — same tooltip pattern
            company_el = card.select_one("a.company span.company-name")
            company = None
            if company_el:
                company = (
                    company_el.get("data-original-title", "").strip()
                    or company_el.get_text(strip=True)
                )

            # Salary — prefer label.title-salary; strip the leading icon
            salary_el = card.select_one("label.title-salary, label.salary span")
            salary_text = salary_el.get_text(" ", strip=True) if salary_el else None
            salary_min, salary_max, currency = self._parse_salary(salary_text)

            # Location — full location may include multiple cities; the tooltip
            # data-original-title carries the HTML list, so we extract <li> text
            location = self._extract_location(card)

            # Tag overflow `[data-original-title]` holds the comma-separated CSV
            # of all the non-visible tags: category name, benefits, degree,
            # language requirements, age range, etc.  We split it into
            # structured fields below.
            tag_overflow = []
            for el in card.select(".box-icon .tag .remaining-items, .box-icon .tag-quickview .remaining-items"):
                csv = el.get("data-original-title", "")
                if csv:
                    tag_overflow.extend([t.strip() for t in csv.split(",") if t.strip()])
            # Visible tags (.item-tag) — short labels like "3 năm kinh nghiệm",
            # category names, technology badges
            visible_tags = [
                el.get_text(strip=True)
                for el in card.select(".box-icon .tag .item-tag, .box-icon .tag .item-tag a")
                if el.get_text(strip=True) and "..." not in el.get_text()
            ]
            all_tags = list(dict.fromkeys(visible_tags + tag_overflow))

            # Min/max experience — `label.exp span` is the source of truth
            # ("3 năm", "Không yêu cầu", "Không cần kinh nghiệm").
            exp_el = card.select_one("label.exp span")
            min_exp, max_exp = self._parse_exp_years(
                exp_el.get_text(strip=True) if exp_el else None
            )

            # Degree — pulled from the tag overflow ("Đại Học trở lên",
            # "Cao Đẳng trở lên", "Thạc sĩ trở lên")
            degree = self._extract_degree(all_tags)

            # Skills — TopCV doesn't expose real tech skill chips in the
            # listing card. The "tags" are mostly categories + benefits +
            # degree + language requirements, NOT skills. So we leave
            # skills_raw empty and let the downstream pipeline lift them
            # from the title (e.g. "Senior Java Developer" → ["Java"]) via
            # the ontology matcher.
            skills_raw: list[str] = []

            # Posted time — label.label-update text says "1 tuần trước" /
            # "2 ngày trước"; the tooltip data-original-title says "Cập nhật
            # 2 phút trước" (live updated timestamp).
            posted_el = card.select_one("label.label-update")
            posted_text = posted_el.get_text(" ", strip=True) if posted_el else None
            posted_date = self._parse_posted_date(posted_text)

            # role_hint comes from the listing-page category being crawled
            role_slug, _ = CATEGORY_TO_ROLE.get(category, (category, None))

            # Seniority preference: explicit "Không yêu cầu" in exp_el wins,
            # then title heuristic (Senior/Junior/Intern).
            exp_text = exp_el.get_text(strip=True).lower() if exp_el else ""
            if "không" in exp_text:
                exp_level = "fresher"
            else:
                exp_level = self._parse_exp_level(title)

            return RawJD(
                source=self.source_name,
                source_id=job_id,
                title=title,
                company=company,
                description="",  # not fetchable from listing (Cloudflare)
                skills_raw=skills_raw,
                salary_min=salary_min,
                salary_max=salary_max,
                salary_currency=currency,
                location=location,
                exp_level=exp_level,
                posted_date=posted_date,
                url=url,
                role_hint=role_slug,
                min_exp_listing=min_exp,
                max_exp_listing=max_exp,
                degree_listing=degree,
            )
        except Exception as e:
            logger.warning("card parse failed: %s", e)
            return None

    # ── new helpers for the richer listing parse ───────────────────

    @staticmethod
    def _extract_location(card) -> Optional[str]:
        """Pull location text from `label.address`. Prefer the full HTML
        in `data-original-title` (it's a <ul> of cities) over the truncated
        `.city-text` (which says "Hồ Chí Minh (mới) & Hà Nội" but cuts off
        when there are 3+ cities)."""
        addr = card.select_one("label.address[data-original-title]")
        if addr:
            html = addr.get("data-original-title", "")
            if html:
                inner = BeautifulSoup(html, "html.parser")
                lis = [li.get_text(strip=True) for li in inner.select("li")]
                if lis:
                    return " & ".join(lis)
        loc_el = card.select_one("span.city-text, label.address span")
        if loc_el:
            return loc_el.get_text(strip=True)
        return None

    @staticmethod
    def _parse_exp_years(text: Optional[str]) -> tuple[Optional[int], Optional[int]]:
        """Parse `label.exp span` text into (min_exp, max_exp).

        Examples:
          'Không yêu cầu' / 'Không cần kinh nghiệm' → (0, None)
          'Dưới 1 năm' → (0, 1)
          '3 năm' → (3, None)
          '3 - 5 năm' → (3, 5)
          'Trên 5 năm' → (5, None)
        """
        if not text:
            return None, None
        t = text.lower().strip()
        if "không" in t:
            return 0, None
        if "dưới" in t:
            m = re.search(r"(\d+)", t)
            return (0, int(m.group(1))) if m else (0, None)
        if "trên" in t:
            m = re.search(r"(\d+)", t)
            return (int(m.group(1)), None) if m else (None, None)
        nums = [int(n) for n in re.findall(r"\d+", t)]
        if not nums:
            return None, None
        if len(nums) == 1:
            return nums[0], None
        return min(nums[:2]), max(nums[:2])

    @staticmethod
    def _extract_degree(tags: list[str]) -> Optional[str]:
        """Find a degree level inside the TopCV tag list.

        TopCV writes degrees as 'Đại Học trở lên', 'Cao Đẳng trở lên',
        'Thạc sĩ trở lên'. We strip the 'trở lên' suffix and normalize
        the case-mismatched variants to canonical capitalization.
        """
        for tag in tags:
            tl = tag.lower()
            if "thạc sĩ" in tl or "master" in tl:
                return "Thạc sĩ"
            if "tiến sĩ" in tl or "phd" in tl:
                return "Tiến sĩ"
            if "đại học" in tl or "bachelor" in tl:
                return "Đại học"
            if "cao đẳng" in tl or "college" in tl:
                return "Cao đẳng"
            if "trung cấp" in tl:
                return "Trung cấp"
        return None

    # ── utilities ───────────────────────────────────────────────────

    def _get(self, url: str, ajax: bool = False) -> str:
        if ajax:
            # TopCV's job-view-detail XHR endpoint expects the standard AJAX
            # signals; without them it can return the full page wrapper or
            # an HTML error stub instead of JSON.
            return self.client.get(url, headers={
                "Accept": "application/json, text/javascript, */*; q=0.01",
                "X-Requested-With": "XMLHttpRequest",
            })
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
