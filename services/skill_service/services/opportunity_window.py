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

from collections import Counter
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

# Role aliases reused from freshness_engine — JD `role` column often
# uses 'backend-developer' instead of short 'backend'.
from services.skill_service.services.freshness_engine import (
    ROLE_ALIASES_FOR_TRENDS, _role_alias_list,
)
from services.skill_service.services.ontology import SkillOntology


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


def _canon(skill: str, ontology: Optional[SkillOntology]) -> str:
    """Lowercase + ontology canonical form (e.g. '.NET Core' -> '.net core' -> 'dotnet')."""
    low = skill.lower().strip()
    if ontology is None:
        return low
    return (ontology.canonical.get(low) or low).lower()


def find_opportunities(
    db: Session,
    cv_skills: list[str],
    target_role: Optional[str] = None,
    cv_years: Optional[float] = None,
    cv_location: Optional[str] = None,
    cv_work_modes: Optional[list[str]] = None,
    days: int = 30,                                # nới mặc định 7 → 30 (VN thưa)
    limit: int = 10,
    min_match: float = 0.4,
    ontology: Optional[SkillOntology] = None,      # cho phép pass ontology để canonicalize
) -> tuple[list[OpportunityJD], dict]:
    """Return (top-N JDs, aggregate_insights).

    Improvements vs v2:
    - Canonicalize cả CV và JD skills qua ontology trước khi match (handle '.NET Core' = '.NET').
    - Role filter dùng alias list thay vì strict substring (backend → backend-developer/...).
    - Trả thêm aggregate dict: top missing skills across JDs, total scanned, count passed.
    """
    cv_set = {_canon(s, ontology) for s in cv_skills}
    cv_work_set = {m.lower() for m in (cv_work_modes or [])}
    start = date.today() - timedelta(days=days)

    # Pull broader candidate pool — sort theo posted_date DESC nhưng tăng cap để
    # không miss JD match cao bị đẩy sau LIMIT.
    # Chỉ lấy data từ source thật (itviec/topcv) — loại 'test' seed của unit tests
    # và bất kỳ source không xác định nào.
    sql = """
        SELECT jd_key, title, company, role, location,
               posted_date, url, salary_min, salary_max, salary_currency,
               skills_canonical, skills_required, skills_preferred,
               seniority, min_exp, max_exp, work_mode, description_summary
        FROM jd_raw
        WHERE posted_date >= :start
          AND source IN ('itviec', 'topcv')
        ORDER BY posted_date DESC
        LIMIT 800
    """
    rows = db.execute(text(sql), {"start": start}).fetchall()

    # Role alias matching — JD role có thể là 'backend-developer' khi user chọn 'backend'
    role_aliases = set(_role_alias_list(target_role)) if target_role else set()

    results: list[OpportunityJD] = []
    total_scanned = 0
    missing_skill_counter: Counter[str] = Counter()  # đếm missing skill xuất hiện qua bao nhiêu JD

    for r in rows:
        total_scanned += 1
        required_raw = r[11] or []
        preferred_raw = r[12] or []
        canonical = r[10] or []

        if required_raw:
            required = [s for s in required_raw if isinstance(s, str) and s.strip()]
        else:
            required = [s for s in canonical if isinstance(s, str) and s.strip()]
        if not required:
            continue
        preferred = [s for s in (preferred_raw or []) if isinstance(s, str) and s.strip()]

        # Canonicalize maps: canon_form -> original (giữ original để hiển thị)
        req_canon = {_canon(s, ontology): s for s in required}
        pref_canon = {_canon(s, ontology): s for s in preferred if _canon(s, ontology) not in req_canon}

        matched = [orig for c, orig in req_canon.items() if c in cv_set]
        missing_req = [orig for c, orig in req_canon.items() if c not in cv_set]
        matched_pref = [orig for c, orig in pref_canon.items() if c in cv_set]
        missing_pref = [orig for c, orig in pref_canon.items() if c not in cv_set]

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

        # Role filter: nếu user chọn role → JD.role phải match 1 trong các alias
        # Nếu JD.role NULL → giữ lại (don't penalize crawler missing role)
        if role_aliases and r[3]:
            jd_role_low = r[3].lower()
            # match nếu JD role chứa hoặc bằng bất kỳ alias nào
            if not any(a in jd_role_low for a in role_aliases):
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

        # Track missing skills across passing JDs để aggregate insight
        for skill in missing_req:
            missing_skill_counter[skill] += 1

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

    # Build aggregate insights (trên FULL results, không chỉ top-N)
    top_missing = [
        {"skill": skill, "count": cnt, "pct": round(cnt / max(len(results), 1) * 100, 1)}
        for skill, cnt in missing_skill_counter.most_common(8)
    ]
    aggregate = {
        "total_scanned": total_scanned,
        "total_passed": len(results),
        "top_missing_skills": top_missing,
    }
    return results[:limit], aggregate


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
