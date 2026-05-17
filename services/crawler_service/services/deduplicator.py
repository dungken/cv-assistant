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


def compute_job_group_id(company: str | None, title: str) -> str:
    """Group ID for the same job-opening posted across multiple sources.

    Two records share a `job_group_id` only when (company, title) match
    exactly after lowercase + whitespace collapse. Intentionally strict:
    we DON'T strip "Co. Ltd / JSC / Corporation" because real variants
    like "FPT Software" vs "FPT Digital" are distinct legal entities,
    and we DON'T strip "Senior / Junior" because they correspond to
    distinct openings with different pay bands.

    Returns empty string when either field is missing — caller should
    keep the record but exclude it from cross-source dedup analytics.
    """
    if not company or not title:
        return ""
    norm_co = " ".join(company.lower().split())
    norm_title = " ".join(title.lower().split())
    if not norm_co or not norm_title:
        return ""
    payload = f"{norm_co}|{norm_title}"
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()[:16]


def compute_jd_key(jd: RawJD) -> str:
    """Stable jd_key for the same JD across re-crawls.

    Primary signal is the canonical URL on the source platform — every re-crawl
    of the same listing returns the same URL, so the key stays constant even
    when `posted_date` shifts (ITviec sometimes boosts a JD and resets the
    posted-ago label, which used to cause duplicate rows under the old
    week-based key).

    Falls back to (source, normalized_company, normalized_title) when the URL
    is missing — this preserves cross-source dedup (e.g. the same JD scraped
    from both ITviec and TopCV) without depending on the volatile date.
    """
    canonical_url = (jd.url or "").split("?")[0].rstrip("/")
    if canonical_url:
        payload = canonical_url
    else:
        payload = "|".join([
            jd.source,
            normalize_company(jd.company),
            normalize_title(jd.title),
        ])
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()[:16]
