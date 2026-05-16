"""UITForumCrawler — crawl JDs from forum.uit.edu.vn (Discourse).

Strategy:
- Discourse exposes a JSON API for every topic list and post.
- Listing: GET /tag/<tag>.json?page=N → topic_list.topics[]
- Detail: GET /t/<slug>/<id>.json → post_stream.posts[0].cooked (HTML body)
- We strip HTML to plain text for the description field.

Tags used (from forum.uit.edu.vn):
- thực-tập (internship)
- việc-làm (jobs)
- tuyển-dụng (recruitment)
- internship

JDs are SV-targeted (intern/fresher), highly relevant for the thesis target
audience. ~hundreds of topics across these tags, posted by HR or alumni.

Salary, location, deadline are sometimes embedded in the body but not as
structured fields — relies on downstream LLM extractor to pull them out.
"""
from __future__ import annotations

import json
import logging
import re
from datetime import date, datetime
from typing import Optional
from urllib.parse import quote

from bs4 import BeautifulSoup

from services.crawler_service.config import settings
from services.crawler_service.models.schemas import RawJD
from services.crawler_service.services.base_crawler import IJDCrawler
from services.crawler_service.services.http_client import PoliteHttpClient

logger = logging.getLogger(__name__)


# Tag → URL slug (Discourse URL-encodes Vietnamese diacritics).
TAG_PATHS = {
    "internship": "internship",
    "thuc-tap": "thực-tập",
    "viec-lam": "việc-làm",
    "tuyen-dung": "tuyển-dụng",
}

# Heuristic: extract company name from title patterns like
# "[Company] Job Title", "Company - Job Title", "Company tuyển ..."
_COMPANY_PATTERNS = [
    re.compile(r"^\[([^\]]+)\]"),                       # [Company] ...
    re.compile(r"^([A-Z][\w&. -]+?)\s+(?:tuyển|recruit)", re.I),
    re.compile(r"^([A-Z][\w&. -]+?)\s*[-–—]\s"),         # Company - ...
]


class UITForumCrawler(IJDCrawler):
    source_name = "uit_forum"
    base_url = "https://forum.uit.edu.vn"

    def __init__(self) -> None:
        self.client = PoliteHttpClient(
            extra_headers={
                "X-Crawler-Contact": settings.crawl_user_agent,
                "Accept": "application/json",
                "Accept-Language": "vi,en;q=0.9",
            },
            sleep_min=1.5,
            sleep_max=3.0,
        )

    # ── public interface ────────────────────────────────────────────

    def list_categories(self) -> list[str]:
        return list(TAG_PATHS.keys())

    def crawl_listing(self, category: str, max_pages: int = 10) -> list[str]:
        """Return list of detail-page URLs (canonical /t/<slug>/<id>) for a tag."""
        tag = TAG_PATHS.get(category)
        if not tag:
            raise ValueError(f"Unknown UIT tag: {category}")

        urls: list[str] = []
        seen_ids: set[int] = set()
        # Discourse /tag/<tag>.json paginates with ?page=0,1,2,...
        for page in range(0, max_pages):
            page_url = f"{self.base_url}/tag/{quote(tag)}.json?page={page}"
            try:
                body = self._get(page_url)
                payload = json.loads(body)
            except Exception as e:
                logger.warning("UIT listing fetch failed tag=%s page=%d: %s", tag, page, e)
                break

            topics = (payload.get("topic_list") or {}).get("topics") or []
            if not topics:
                logger.info("UIT no more topics tag=%s at page=%d", tag, page)
                break

            new_in_page = 0
            for t in topics:
                tid = t.get("id")
                slug = t.get("slug")
                if not tid or not slug or tid in seen_ids:
                    continue
                seen_ids.add(tid)
                urls.append(f"{self.base_url}/t/{slug}/{tid}")
                new_in_page += 1

            if new_in_page == 0:
                # Discourse sometimes returns the same page again at the end.
                break
            self._polite_sleep()

        logger.info("UIT tag=%s collected %d topic URLs", tag, len(urls))
        return urls

    def crawl_detail(self, url: str) -> Optional[RawJD]:
        """Fetch a single topic via JSON API and project to RawJD."""
        # /t/<slug>/<id> → /t/<slug>/<id>.json
        json_url = url.rstrip("/") + ".json"
        try:
            body = self._get(json_url)
            payload = json.loads(body)
        except Exception as e:
            logger.warning("UIT detail fetch failed url=%s: %s", url, e)
            return None

        try:
            return self._payload_to_jd(payload, url)
        except Exception as e:
            logger.warning("UIT parse failed url=%s: %s", url, e)
            return None

    def health_check(self) -> bool:
        try:
            urls = self.crawl_listing("internship", max_pages=1)
            if not urls:
                return False
            jd = self.crawl_detail(urls[0])
            return jd is not None and bool(jd.title and jd.description)
        except Exception:
            return False

    # ── helpers ─────────────────────────────────────────────────────

    def _payload_to_jd(self, payload: dict, url: str) -> Optional[RawJD]:
        topic_id = payload.get("id")
        title = (payload.get("title") or "").strip()
        slug = payload.get("slug") or ""
        created_at = payload.get("created_at")
        tags = payload.get("tags") or []

        posts = (payload.get("post_stream") or {}).get("posts") or []
        if not posts:
            return None
        first = posts[0]
        cooked_html = first.get("cooked") or ""
        description = self._html_to_text(cooked_html)
        if not description or len(description) < 80:
            return None  # skip near-empty topics (usually link-only posts)

        # Posted date from Discourse ISO8601.
        posted = self._parse_iso_date(created_at) or date.today()

        # Company extracted from title heuristics; fallback empty.
        company = self._extract_company(title)

        return RawJD(
            source=self.source_name,
            source_id=str(topic_id),
            title=title,
            company=company,
            description=description,
            skills_raw=[],            # tags are workflow tags, not tech skills
            salary_min=None,
            salary_max=None,
            salary_currency=None,
            location=None,            # body-mentioned, LLM will extract
            exp_level="intern",       # forum is intern/fresher-dominant
            posted_date=posted,
            url=url,
            role_hint=None,
        )

    def _html_to_text(self, html: str) -> str:
        if not html:
            return ""
        soup = BeautifulSoup(html, "html.parser")
        # Drop <aside class="quote"> blockquotes (they repeat prior posts).
        for q in soup.select("aside.quote, blockquote"):
            q.decompose()
        # Convert <br> and block tags to newlines for readable text.
        for br in soup.find_all("br"):
            br.replace_with("\n")
        text = soup.get_text("\n", strip=True)
        # Collapse 3+ blank lines to 2.
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    def _extract_company(self, title: str) -> Optional[str]:
        for pat in _COMPANY_PATTERNS:
            m = pat.search(title)
            if m:
                cand = m.group(1).strip(" -–—")
                # Reject too-short or obviously-not-company captures.
                if 2 <= len(cand) <= 60 and not cand.lower().startswith("intern"):
                    return cand
        return None

    def _parse_iso_date(self, iso: Optional[str]) -> Optional[date]:
        if not iso:
            return None
        try:
            return datetime.fromisoformat(iso.replace("Z", "+00:00")).date()
        except ValueError:
            return None

    def _get(self, url: str) -> str:
        return self.client.get(url)

    def _polite_sleep(self) -> None:
        self.client.polite_sleep()
