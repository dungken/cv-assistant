"""Compute deterministic jd_key for deduplication across sources and runs."""
import hashlib
import re

from services.crawler_service.models.schemas import RawJD


_COMPANY_SUFFIXES = re.compile(
    r"\b(co\.?\,?\s*ltd|ltd|jsc|inc|corporation|corp|company|công\s*ty|cty)\b\.?",
    re.IGNORECASE,
)
_WS = re.compile(r"\s+")
_LEVEL_SUFFIX = re.compile(
    r"\b(senior|junior|middle|mid|fresher|fresh|intern|lead|principal|"
    r"sr\.?|jr\.?|ii|iii|iv|level\s*\d+)\b",
    re.IGNORECASE,
)


def normalize_company(name: str | None) -> str:
    if not name:
        return ""
    cleaned = _COMPANY_SUFFIXES.sub("", name)
    return _WS.sub(" ", cleaned).strip().lower()


def normalize_title(title: str) -> str:
    cleaned = _LEVEL_SUFFIX.sub("", title)
    return _WS.sub(" ", cleaned).strip().lower()


def compute_jd_key(jd: RawJD) -> str:
    """Same (company, normalized_title, ISO week) → same jd_key.

    Rationale: a JD reposted on consecutive days within a week is one job opening.
    Different titles by same company in same week treated as different keys.
    """
    year, week, _ = jd.posted_date.isocalendar()
    payload = "|".join([
        normalize_company(jd.company),
        normalize_title(jd.title),
        f"{year}-W{week:02d}",
    ])
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()[:16]
