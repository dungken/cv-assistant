"""Tuần 14 + Tuần 16 — Opportunity Window service.

Returns recent JDs that match the user's CV using a multi-dimensional fit
score, not just skill overlap:

  - skill_required_coverage  = |required ∩ owned| / |required|     (blocker)
  - skill_preferred_coverage = |preferred ∩ owned| / |preferred|   (nice-to-have)
  - exp_fit                  = how close cv_years is to JD's required range
  - location_match           = 1 if user location matches JD location, else 0
  - work_mode_match          = 1 if user accepts JD's work_mode, else 0

`match_score` is a weighted blend that emphasizes blockers (required + exp)
over nice-to-haves. Cards on the dashboard expose each dimension so the user
can see *why* the score is what it is — much more useful than a single number.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Optional

from sqlalchemy import text
from sqlalchemy.orm import Session


# ─── Weights (sum = 1.0 for the composite score) ──────────────────────────────

W_REQUIRED = 0.55
W_PREFERRED = 0.15
W_EXP = 0.20
W_LOCATION = 0.05
W_WORK_MODE = 0.05


@dataclass
class OpportunityJD:
    jd_key: str
    title: str
    company: str
    role: Optional[str]
    location: Optional[str]
    posted_date: str
    url: Optional[str]
    salary_min: Optional[int]
    salary_max: Optional[int]
    salary_currency: Optional[str]
    # Enriched fields
    seniority: Optional[str]
    min_exp: Optional[int]
    max_exp: Optional[int]
    work_mode: Optional[str]
    description_summary: Optional[str]
    # Match breakdown
    match_score: float          # 0..1 composite
    skill_required_coverage: float
    skill_preferred_coverage: float
    exp_fit: float
    location_match: bool
    work_mode_match: bool
    matched_skills: list[str] = field(default_factory=list)
    missing_required: list[str] = field(default_factory=list)
    missing_preferred: list[str] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)  # human-readable reasons user can't apply


def find_opportunities(
    db: Session,
    cv_skills: list[str],
    target_role: Optional[str] = None,
    cv_years: Optional[float] = None,
    cv_location: Optional[str] = None,
    cv_work_modes: Optional[list[str]] = None,  # e.g. ["remote", "hybrid"]
    days: int = 7,
    limit: int = 10,
    min_match: float = 0.4,
) -> list[OpportunityJD]:
    """Return top-N JDs posted in the last `days` days, ranked by composite match.

    Unlike v1, we use `skills_required` (NER-parsed) as the blocker set when
    available, falling back to `skills_canonical` for unparsed rows. JDs whose
    composite `match_score < min_match` are excluded.
    """
    cv_set = {s.lower() for s in cv_skills}
    cv_work_set = {m.lower() for m in (cv_work_modes or [])}
    start = date.today() - timedelta(days=days)

    sql = """
        SELECT jd_key, title, company, role, location,
               posted_date, url, salary_min, salary_max, salary_currency,
               skills_canonical, skills_required, skills_preferred,
               seniority, min_exp, max_exp, work_mode, description_summary
        FROM jd_raw
        WHERE posted_date >= :start
        ORDER BY posted_date DESC
        LIMIT 300
    """
    rows = db.execute(text(sql), {"start": start}).fetchall()

    results: list[OpportunityJD] = []
    for r in rows:
        required_raw = r[11] or []     # skills_required (parsed); may be empty
        preferred_raw = r[12] or []    # skills_preferred (parsed)
        canonical = r[10] or []        # skills_canonical (basic crawler list)

        # Use parsed `required` if present; otherwise treat all canonical as required.
        if required_raw:
            required = [s for s in required_raw if isinstance(s, str) and s.strip()]
        else:
            required = [s for s in canonical if isinstance(s, str) and s.strip()]
        if not required:
            continue
        preferred = [s for s in (preferred_raw or []) if isinstance(s, str) and s.strip()]

        req_lower = {s.lower(): s for s in required}
        pref_lower = {s.lower(): s for s in preferred if s.lower() not in req_lower}

        matched = [orig for low, orig in req_lower.items() if low in cv_set]
        missing_req = [orig for low, orig in req_lower.items() if low not in cv_set]
        matched_pref = [orig for low, orig in pref_lower.items() if low in cv_set]
        missing_pref = [orig for low, orig in pref_lower.items() if low not in cv_set]

        required_coverage = len(matched) / max(len(required), 1)
        preferred_coverage = (
            len(matched_pref) / len(preferred) if preferred else 1.0
        )

        seniority = r[13]
        min_exp = r[14]
        max_exp = r[15]
        exp_fit = _exp_fit(cv_years, min_exp, max_exp)

        loc = r[4]
        location_match = _location_match(cv_location, loc)

        work_mode = r[16]
        work_mode_match = _work_mode_match(cv_work_set, work_mode)

        if target_role and r[3] and target_role.lower() not in r[3].lower():
            continue

        score = (
            W_REQUIRED * required_coverage
            + W_PREFERRED * preferred_coverage
            + W_EXP * exp_fit
            + W_LOCATION * (1.0 if location_match else 0.0)
            + W_WORK_MODE * (1.0 if work_mode_match else 0.0)
        )

        if score < min_match:
            continue

        blockers = _build_blockers(
            missing_req=missing_req, cv_years=cv_years, min_exp=min_exp,
            cv_location=cv_location, jd_location=loc, location_match=location_match,
        )

        results.append(OpportunityJD(
            jd_key=r[0], title=r[1], company=r[2] or "",
            role=r[3], location=loc,
            posted_date=r[5].isoformat() if r[5] else "",
            url=r[6], salary_min=r[7], salary_max=r[8], salary_currency=r[9],
            seniority=seniority, min_exp=min_exp, max_exp=max_exp,
            work_mode=work_mode, description_summary=r[17],
            match_score=round(score, 3),
            skill_required_coverage=round(required_coverage, 3),
            skill_preferred_coverage=round(preferred_coverage, 3),
            exp_fit=round(exp_fit, 3),
            location_match=location_match,
            work_mode_match=work_mode_match,
            matched_skills=matched,
            missing_required=missing_req,
            missing_preferred=missing_pref,
            blockers=blockers,
        ))

    results.sort(key=lambda o: (o.match_score, o.posted_date), reverse=True)
    return results[:limit]


# ─── Per-dimension fit functions ─────────────────────────────────────────────


def _exp_fit(cv_years: Optional[float], min_exp: Optional[int], max_exp: Optional[int]) -> float:
    """1.0 when CV experience is inside the JD's range, falling off linearly
    outside it. When JD doesn't state a range we return 1.0 (no signal)."""
    if cv_years is None or (min_exp is None and max_exp is None):
        return 1.0
    cv = float(cv_years)
    lo = float(min_exp) if min_exp is not None else 0.0
    hi = float(max_exp) if max_exp is not None else max(lo + 4, lo)
    if lo <= cv <= hi:
        return 1.0
    if cv < lo:
        gap = lo - cv
        # Tolerate up to 2-year gap — degrades linearly to 0 across that window.
        return max(0.0, 1.0 - gap / 2.0)
    # Over-qualified: less harsh penalty; still ranks above blockers.
    over = cv - hi
    return max(0.3, 1.0 - over / 5.0)


_LOCATION_ALIASES = {
    "hcm": "ho chi minh",
    "tphcm": "ho chi minh",
    "tp hcm": "ho chi minh",
    "tp.hcm": "ho chi minh",
    "tp. hcm": "ho chi minh",
    "saigon": "ho chi minh",
    "sài gòn": "ho chi minh",
    "hn": "ha noi",
    "hà nội": "ha noi",
    "hanoi": "ha noi",
    "dn": "da nang",
    "đà nẵng": "da nang",
    "danang": "da nang",
}


def _canonical_location(loc: str) -> str:
    norm = loc.strip().lower()
    return _LOCATION_ALIASES.get(norm, norm)


def _location_match(cv_location: Optional[str], jd_location: Optional[str]) -> bool:
    if not cv_location:
        return True  # user hasn't specified — don't penalize
    if not jd_location:
        return False
    cv_norm = _canonical_location(cv_location)
    jd_norm = _canonical_location(jd_location)
    if not cv_norm or not jd_norm:
        return False
    return cv_norm in jd_norm or jd_norm in cv_norm


def _work_mode_match(cv_modes: set[str], jd_mode: Optional[str]) -> bool:
    if not cv_modes:
        return True
    if not jd_mode:
        return False
    return jd_mode.lower() in cv_modes


def _build_blockers(*, missing_req, cv_years, min_exp, cv_location, jd_location, location_match) -> list[str]:
    out: list[str] = []
    if missing_req:
        head = ", ".join(missing_req[:3])
        rest = len(missing_req) - 3
        out.append(
            f"Thiếu {len(missing_req)} skill yêu cầu: {head}"
            + (f" · +{rest}" if rest > 0 else "")
        )
    if cv_years is not None and min_exp is not None and float(cv_years) + 0.5 < float(min_exp):
        out.append(f"Cần {min_exp}+ năm exp, bạn có {cv_years:g}")
    if not location_match and cv_location and jd_location:
        out.append(f"Khác địa điểm: bạn ở {cv_location}, JD ở {jd_location}")
    return out
