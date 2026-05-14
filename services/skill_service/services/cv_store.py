"""Tuần 14 — per-user CV state persisted in Postgres.

Source of truth for `/health-score`, `/skill-alerts`, `/opportunity-window`,
and `/learning-path/me`. Decoupled from auth: callers pass `user_id`. When
auth lands in Tuần 14+ we resolve `user_id` from the JWT before calling here.
"""
from __future__ import annotations

from dataclasses import dataclass
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


def get_cv(db: Session, user_id: str) -> Optional[CVRecord]:
    row = db.query(UserCVDB).filter(UserCVDB.user_id == user_id).one_or_none()
    if row is None:
        return None
    return CVRecord(
        user_id=row.user_id,
        target_role=row.target_role,
        skills_with_recency=list(row.skills_with_recency or []),
        updated_at=row.updated_at,
    )


def upsert_cv(
    db: Session, user_id: str, target_role: str, skills: list[dict],
) -> CVRecord:
    """Insert-or-update the CV row. Caller is responsible for triggering the
    BackgroundTask that recomputes Freshness (see main.py)."""
    row = db.query(UserCVDB).filter(UserCVDB.user_id == user_id).one_or_none()
    now = datetime.utcnow()
    if row is None:
        row = UserCVDB(
            user_id=user_id, target_role=target_role,
            skills_with_recency=skills, updated_at=now,
        )
        db.add(row)
    else:
        row.target_role = target_role
        row.skills_with_recency = skills
        row.updated_at = now
    db.commit()
    return CVRecord(
        user_id=user_id, target_role=target_role,
        skills_with_recency=skills, updated_at=now,
    )
