"""CV Freshness Engine — Tuần 10.

Implements the formula from chuong3/3.2:

    Freshness(CV, r, t) = 100 * sum_{s in S}  w_r(s) * trend(s, t) * recency(s)
                                / sum_{s in S_r_ideal}  w_r(s)

Components:
- importance w_r(s) = α1·1[PART_OF(s, r)] + α2·indegree_REQUIRES(s) + α3·freq_r(s)
- trend(s, t)       = clip(d_t / MA_4(s, t-1), 0.5, 1.5)
- recency(s)        = step function on years since last use {1.0, 0.7, 0.4, 0.1}
- S_r_ideal         = top-15 skills in JD role r over the last 4 weeks

Reads `skill_trends` written by the crawler aggregator (per-week buckets via
`window_days=7`). Falls back gracefully when there's not enough history
(cold-start: first 4 weeks of crawling).
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from services.skill_service.services.ontology import (
    PART_OF,
    REQUIRES,
    SkillOntology,
)

logger = logging.getLogger(__name__)


# ─── Tunables (defaults match chuong3/3.2) ────────────────────────────────────

ALPHA_PART_OF = 0.3
ALPHA_REQUIRES_INDEGREE = 0.2
ALPHA_FREQUENCY = 0.5

TREND_CLIP_LOW = 0.5
TREND_CLIP_HIGH = 1.5

IDEAL_TOP_K = 15
TREND_WINDOW_DAYS = 7
TREND_LOOKBACK_WEEKS = 4

DEFAULT_RECENCY = 0.7  # used when CV experience date info is missing

ALERT_DROP_THRESHOLD = 5.0  # §3.2.5 — fire alert when score drops more than this


# ─── CV input + output dataclasses ────────────────────────────────────────────

@dataclass
class CVSkillInput:
    """One CV skill, optionally with the most-recent year of use from NER."""
    name: str
    last_used_year: Optional[int] = None  # e.g. 2025

    def recency(self, today_year: int) -> float:
        if self.last_used_year is None:
            return 0.7  # average — see chuong3/3.2.6 (NER fallback)
        years = today_year - self.last_used_year
        if years <= 1:
            return 1.0
        if years <= 2:
            return 0.7
        if years <= 5:
            return 0.4
        return 0.1


@dataclass
class SkillContribution:
    skill: str
    importance: float
    trend: float
    recency: float
    contribution: float  # 100 * w·trend·recency / denominator


@dataclass
class FreshnessResult:
    score: float
    role: str
    snapshot_date: date
    contributions: list[SkillContribution] = field(default_factory=list)
    ideal_skills: list[str] = field(default_factory=list)
    missing_ideal: list[str] = field(default_factory=list)  # ideal skills not in CV
    cold_start: bool = False  # True if trend data is too thin


# ─── Engine ───────────────────────────────────────────────────────────────────


class CVFreshnessEngine:
    """Compute Freshness Score from skill_trends + ontology."""

    def __init__(self, ontology: SkillOntology):
        self.ontology = ontology
        self._requires_indegree_max = self._compute_requires_indegree_max()

    # ── importance components ──

    def _compute_requires_indegree_max(self) -> int:
        """Max in-degree of REQUIRES across the graph — used to normalize to [0,1]."""
        max_deg = 1
        for skill_lower, by_rel in self.ontology.graph_in.items():
            deg = len(by_rel.get(REQUIRES, []))
            if deg > max_deg:
                max_deg = deg
        return max_deg

    def _is_part_of_role(self, skill: str, role: str) -> bool:
        """True if skill PART_OF a domain that maps to this role."""
        skill_lower = skill.lower()
        # Map our role name to ontology domains.
        role_domains = _ROLE_TO_DOMAINS.get(role.lower(), set())
        targets = self.ontology.graph_out.get(skill_lower, {}).get(PART_OF, [])
        for tgt in targets:
            if tgt in role_domains:
                return True
        # Fallback: skill's category matches one of the role's preferred categories.
        cat = self.ontology.skill_to_category.get(skill_lower)
        return cat in role_domains

    def _requires_indegree(self, skill: str) -> float:
        deg = len(self.ontology.graph_in.get(skill.lower(), {}).get(REQUIRES, []))
        return deg / self._requires_indegree_max

    def _importance(self, skill: str, role: str, freq_norm: float) -> float:
        """w_r(s) ∈ [0, 1]."""
        return (
            ALPHA_PART_OF * (1.0 if self._is_part_of_role(skill, role) else 0.0)
            + ALPHA_REQUIRES_INDEGREE * self._requires_indegree(skill)
            + ALPHA_FREQUENCY * freq_norm
        )

    # ── trend & frequency from skill_trends ──

    def _load_trend_data(
        self, db: Session, role: str, snapshot_date: date
    ) -> tuple[dict[str, int], dict[str, float], bool]:
        """Returns (current_demand_by_skill, freq_norm_by_skill, cold_start)."""
        # Current week demand (latest snapshot ≤ snapshot_date with window_days=7)
        sql_current = text(
            """
            SELECT skill_canonical, demand_count
            FROM skill_trends
            WHERE window_days = :window
              AND snapshot_date = (
                  SELECT MAX(snapshot_date) FROM skill_trends
                  WHERE window_days = :window
                    AND snapshot_date <= :snap
                    AND (role = :role OR (:role IS NULL AND role IS NULL))
              )
              AND (role = :role OR (:role IS NULL AND role IS NULL))
            """
        )
        role_arg = role if role else None
        rows = db.execute(
            sql_current, {"window": TREND_WINDOW_DAYS, "snap": snapshot_date, "role": role_arg}
        ).fetchall()
        current: dict[str, int] = {r[0]: int(r[1]) for r in rows}

        if not current:
            logger.warning("freshness: no skill_trends for role=%s snap=%s", role, snapshot_date)
            return {}, {}, True

        # Normalize freq to [0, 1] using max demand in the snapshot.
        max_demand = max(current.values()) or 1
        freq_norm = {sk: cnt / max_demand for sk, cnt in current.items()}

        # Cold-start detection: < 4 distinct snapshots historically.
        sql_history_count = text(
            """
            SELECT COUNT(DISTINCT snapshot_date) FROM skill_trends
            WHERE window_days = :window
              AND (role = :role OR (:role IS NULL AND role IS NULL))
              AND snapshot_date <= :snap
            """
        )
        n_snaps = db.execute(
            sql_history_count,
            {"window": TREND_WINDOW_DAYS, "snap": snapshot_date, "role": role_arg},
        ).scalar() or 0
        cold_start = n_snaps < TREND_LOOKBACK_WEEKS

        return current, freq_norm, cold_start

    def _trend_for_skill(
        self, db: Session, skill: str, role: str, snapshot_date: date, current: dict[str, int]
    ) -> float:
        """trend(s, t) = clip(d_t / MA_4_prev, 0.5, 1.5)."""
        d_t = current.get(skill, 0)
        if d_t == 0:
            return TREND_CLIP_LOW

        # MA over the 4 previous weekly snapshots strictly before snapshot_date.
        sql = text(
            """
            SELECT AVG(demand_count) FROM (
                SELECT demand_count FROM skill_trends
                WHERE skill_canonical = :sk
                  AND window_days = :window
                  AND (role = :role OR (:role IS NULL AND role IS NULL))
                  AND snapshot_date < :snap
                ORDER BY snapshot_date DESC
                LIMIT :k
            ) sub
            """
        )
        ma = db.execute(
            sql,
            {
                "sk": skill,
                "window": TREND_WINDOW_DAYS,
                "role": role if role else None,
                "snap": snapshot_date,
                "k": TREND_LOOKBACK_WEEKS,
            },
        ).scalar()
        if ma is None or ma == 0:
            return 1.0  # no history → neutral
        ratio = d_t / float(ma)
        return max(TREND_CLIP_LOW, min(TREND_CLIP_HIGH, ratio))

    # ── ideal skill set ──

    def _ideal_skills(self, current: dict[str, int]) -> list[str]:
        """Top-K most-demanded canonical skills in the current snapshot."""
        return [
            sk for sk, _ in sorted(current.items(), key=lambda kv: -kv[1])[:IDEAL_TOP_K]
        ]

    # ── public ──

    def compute(
        self,
        db: Session,
        cv_skills: list[CVSkillInput],
        role: str,
        snapshot_date: Optional[date] = None,
        today_year: Optional[int] = None,
    ) -> FreshnessResult:
        snapshot_date = snapshot_date or date.today()
        today_year = today_year or snapshot_date.year

        current, freq_norm, cold_start = self._load_trend_data(db, role, snapshot_date)
        if not current:
            return FreshnessResult(
                score=0.0,
                role=role,
                snapshot_date=snapshot_date,
                cold_start=True,
            )

        ideal = self._ideal_skills(current)
        # Denominator = sum of importance over ideal set.
        denom = 0.0
        for sk in ideal:
            denom += self._importance(sk, role, freq_norm.get(sk, 0.0))
        if denom <= 0:
            denom = 1e-6

        # Canonicalize CV skill names against the ontology.
        contributions: list[SkillContribution] = []
        numerator = 0.0
        cv_skill_set: set[str] = set()
        for cv in cv_skills:
            canon = self.ontology.canonical.get(cv.name.lower(), cv.name)
            cv_skill_set.add(canon)
            w = self._importance(canon, role, freq_norm.get(canon, 0.0))
            tr = self._trend_for_skill(db, canon, role, snapshot_date, current)
            rec = cv.recency(today_year)
            term = w * tr * rec
            numerator += term
            contributions.append(
                SkillContribution(
                    skill=canon,
                    importance=round(w, 4),
                    trend=round(tr, 4),
                    recency=round(rec, 4),
                    contribution=round(100.0 * term / denom, 3),
                )
            )

        score = 100.0 * numerator / denom
        # The formula is unbounded above only if a CV piles up many high-trend skills
        # outside the ideal set. Cap at 100 for UX (per A1 in §3.2.1).
        score = max(0.0, min(100.0, score))

        missing_ideal = [s for s in ideal if s not in cv_skill_set]
        contributions.sort(key=lambda c: -c.contribution)

        return FreshnessResult(
            score=round(score, 2),
            role=role,
            snapshot_date=snapshot_date,
            contributions=contributions,
            ideal_skills=ideal,
            missing_ideal=missing_ideal,
            cold_start=cold_start,
        )


# ─── Persistence helpers (Tuần 11) ────────────────────────────────────────────


def record_history_and_alert(
    db: Session,
    user_id: str,
    result: FreshnessResult,
) -> Optional[dict]:
    """Append result to skill_freshness_history and fire an alert if score
    dropped more than ALERT_DROP_THRESHOLD from the previous snapshot.

    Returns the alert dict if fired, else None. Imports are local so the
    pure-formula `compute()` path stays import-light for unit tests.
    """
    from services.skill_service.models.database import (
        FreshnessHistoryDB, FreshnessAlertDB,
    )

    # Find the most recent prior score for (user, role).
    prev = (
        db.query(FreshnessHistoryDB)
        .filter(
            FreshnessHistoryDB.user_id == user_id,
            FreshnessHistoryDB.role == result.role,
        )
        .order_by(FreshnessHistoryDB.snapshot_date.desc())
        .first()
    )

    db.add(
        FreshnessHistoryDB(
            user_id=user_id,
            role=result.role,
            score=result.score,
            contributions=[c.__dict__ for c in result.contributions],
            cold_start=1 if result.cold_start else 0,
        )
    )

    alert_payload = None
    if prev is not None:
        delta = prev.score - result.score
        if delta > ALERT_DROP_THRESHOLD:
            reason = _summarize_alert_reason(result, prev_score=prev.score)
            alert = FreshnessAlertDB(
                user_id=user_id,
                role=result.role,
                prev_score=prev.score,
                new_score=result.score,
                delta=delta,
                reason=reason,
            )
            db.add(alert)
            alert_payload = {
                "user_id": user_id,
                "role": result.role,
                "prev_score": prev.score,
                "new_score": result.score,
                "delta": delta,
                "reason": reason,
            }
            logger.info(
                "Freshness alert fired user=%s role=%s drop=%.2f -> %.2f",
                user_id, result.role, delta, result.score,
            )
    db.commit()
    return alert_payload


def _summarize_alert_reason(result: FreshnessResult, prev_score: float) -> str:
    """Pick the largest-trend-drop skill in the contribution list as the headline."""
    if not result.contributions:
        return f"Freshness dropped from {prev_score:.1f} to {result.score:.1f}."
    worst = min(result.contributions, key=lambda c: c.trend)
    return (
        f"Freshness dropped from {prev_score:.1f} to {result.score:.1f}. "
        f"Likely cause: '{worst.skill}' trend={worst.trend:.2f} (cooling)."
    )


# ─── Role → ontology PART_OF domain mapping ───────────────────────────────────
# Maps the 5 study roles (Backend, Frontend, Data, DevOps, AI Engineer) to the
# domain names used by PART_OF edges and to category names from SKILL_ONTOLOGY.

_ROLE_TO_DOMAINS: dict[str, set[str]] = {
    "backend": {"Backend Development", "Web Development", "Database"},
    "frontend": {"Frontend Development", "Web Development"},
    "data": {"Data Science", "Data Engineering", "Database"},
    "data_engineer": {"Data Engineering", "Database"},
    "data_scientist": {"Data Science", "ML/AI"},
    "devops": {"DevOps & Infrastructure", "Cloud Platforms"},
    "ai_engineer": {"ML/AI", "Data Science"},
    "ml_engineer": {"ML/AI", "Data Engineering"},
    "fullstack": {"Frontend Development", "Backend Development", "Web Development"},
    "mobile": {"Mobile"},
}
