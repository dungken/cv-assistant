"""Tuần 14 — Opportunity Window service.

Returns recent JDs (posted in the last N days) that match the user's CV well.
"Match score" is a coverage ratio: |required ∩ owned_skills| / |required|.
We use this lightweight proxy instead of the full ATS engine to keep the
endpoint sub-second; the dashboard component (§3.5) only needs ranking, not
full ATS breakdown.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Optional

from sqlalchemy import text
from sqlalchemy.orm import Session


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
    match_score: float       # 0..1
    matched_skills: list[str]
    missing_skills: list[str]


def find_opportunities(
    db: Session,
    cv_skills: list[str],
    target_role: Optional[str] = None,
    days: int = 7,
    limit: int = 10,
    min_match: float = 0.5,
) -> list[OpportunityJD]:
    """Return top-N JDs posted in the last `days` days with match_score ≥ min_match.

    Note: we read directly from `jd_raw` written by the crawler (§3.4). The
    `role` filter is best-effort — many JDs have unknown role.
    """
    cv_set = {s.lower() for s in cv_skills}
    start = date.today() - timedelta(days=days)

    sql = """
        SELECT jd_key, title, company, role, location,
               posted_date, url, salary_min, salary_max, skills_canonical
        FROM jd_raw
        WHERE posted_date >= :start
        ORDER BY posted_date DESC
        LIMIT 200
    """
    rows = db.execute(text(sql), {"start": start}).fetchall()

    results: list[OpportunityJD] = []
    for r in rows:
        required = [s for s in (r[9] or []) if s]
        if not required:
            continue
        req_lower = {s.lower(): s for s in required}
        matched = [original for low, original in req_lower.items() if low in cv_set]
        missing = [original for low, original in req_lower.items() if low not in cv_set]
        score = len(matched) / len(required)
        if score < min_match:
            continue
        if target_role and r[3] and target_role.lower() not in r[3].lower():
            # Soft role filter — skip mismatched roles when we have a role hint.
            continue
        results.append(OpportunityJD(
            jd_key=r[0], title=r[1], company=r[2] or "",
            role=r[3], location=r[4],
            posted_date=r[5].isoformat() if r[5] else "",
            url=r[6], salary_min=r[7], salary_max=r[8],
            match_score=round(score, 3),
            matched_skills=matched, missing_skills=missing,
        ))

    # Rank: higher match first, then more recent.
    results.sort(key=lambda o: (-o.match_score, o.posted_date), reverse=False)
    results.sort(key=lambda o: (-o.match_score, o.posted_date))
    # Simpler: descending match, then descending date (string ISO is lex-sortable).
    results.sort(key=lambda o: (o.match_score, o.posted_date), reverse=True)
    return results[:limit]
