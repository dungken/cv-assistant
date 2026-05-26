"""Tuần 14 + Tuần 16 — per-user CV state persisted in Postgres.

Source of truth for `/health-score`, `/skill-alerts`, `/opportunity-window`,
and `/learning-path/me`. Decoupled from auth: callers pass `user_id`. When
auth lands we resolve `user_id` from the JWT before calling here.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from services.skill_service.models.database import UserCVDB


@dataclass
class CVRecord:
    user_id: str
    target_role: str
    skills_with_recency: list[dict]  # [{"name": str, "last_used_year": int|None}, ...]
    updated_at: datetime
    years_experience: Optional[float] = None
    preferred_location: Optional[str] = None
    preferred_work_modes: list[str] = field(default_factory=list)
    profile_extras: dict = field(default_factory=dict)


def get_cv(db: Session, user_id: str) -> Optional[CVRecord]:
    row = db.query(UserCVDB).filter(UserCVDB.user_id == user_id).one_or_none()
    if row is None:
        return None
    return CVRecord(
        user_id=row.user_id,
        target_role=row.target_role,
        skills_with_recency=list(row.skills_with_recency or []),
        updated_at=row.updated_at,
        years_experience=row.years_experience,
        preferred_location=row.preferred_location,
        preferred_work_modes=list(row.preferred_work_modes or []),
        profile_extras=dict(row.profile_extras or {}),
    )


def upsert_cv(
    db: Session,
    user_id: str,
    target_role: str,
    skills: list[dict],
    years_experience: Optional[float] = None,
    preferred_location: Optional[str] = None,
    preferred_work_modes: Optional[list[str]] = None,
    profile_extras: Optional[dict] = None,
) -> CVRecord:
    """Insert-or-update the CV row. Caller is responsible for triggering the
    BackgroundTask that recomputes Freshness (see main.py).

    `profile_extras` carries the 6 dimensions of Multi-criteria Freshness that
    don't fit the scalar columns above: seniority, past_job_titles, num_projects,
    project_skill_counts, degree, major, achievement_text, language_text, and
    the has_* section flags. Stored as JSON for flexibility (schema may evolve
    as we add dimensions).
    """
    row = db.query(UserCVDB).filter(UserCVDB.user_id == user_id).one_or_none()
    now = datetime.utcnow()
    modes = list(preferred_work_modes or [])
    extras = dict(profile_extras or {})
    if row is None:
        row = UserCVDB(
            user_id=user_id, target_role=target_role,
            skills_with_recency=skills, updated_at=now,
            years_experience=years_experience,
            preferred_location=preferred_location,
            preferred_work_modes=modes,
            profile_extras=extras,
        )
        db.add(row)
    else:
        row.target_role = target_role
        row.skills_with_recency = skills
        row.updated_at = now
        if years_experience is not None:
            row.years_experience = years_experience
        if preferred_location is not None:
            row.preferred_location = preferred_location
        if preferred_work_modes is not None:
            row.preferred_work_modes = modes
        if profile_extras is not None:
            # Shallow-merge so partial updates keep previously-set keys.
            merged = dict(row.profile_extras or {})
            merged.update(profile_extras)
            row.profile_extras = merged
    db.commit()
    return CVRecord(
        user_id=user_id, target_role=target_role,
        skills_with_recency=skills, updated_at=now,
        years_experience=row.years_experience,
        preferred_location=row.preferred_location,
        preferred_work_modes=list(row.preferred_work_modes or []),
        profile_extras=dict(row.profile_extras or {}),
    )
