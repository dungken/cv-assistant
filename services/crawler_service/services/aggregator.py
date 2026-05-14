"""Aggregate per-day skill demand from jd_raw into skill_trends.

Runs after each crawl. For a given snapshot_date and window of N days:
    skill_trends.demand_count = count of distinct jd_key in jd_raw where
        posted_date in [snapshot_date - window + 1, snapshot_date]
        AND skill appears in skills_canonical.

Computes both:
  - overall (role=NULL, location=NULL) — used by Freshness when no role specified
  - per-role rollups — used by role-aware Freshness Score
"""
import logging
from datetime import date, timedelta

from sqlalchemy import text
from sqlalchemy.dialects.postgresql import insert as pg_insert

from services.crawler_service.models.database import SkillTrend
from services.crawler_service.services.db_session import get_session

logger = logging.getLogger(__name__)


def aggregate_skill_trends(snapshot_date: date | None = None, window_days: int = 7) -> int:
    """Recompute skill_trends for the given snapshot_date. Returns rows upserted."""
    snapshot_date = snapshot_date or date.today()
    start = snapshot_date - timedelta(days=window_days - 1)
    rows_upserted = 0

    with get_session() as session:
        # Overall — no role/location filter
        rows_upserted += _aggregate_one(session, snapshot_date, window_days, start, group_by_role=False)
        # Per role
        rows_upserted += _aggregate_one(session, snapshot_date, window_days, start, group_by_role=True)

    logger.info(
        "skill_trends aggregated for %s window=%dd, rows=%d",
        snapshot_date, window_days, rows_upserted,
    )
    return rows_upserted


def _aggregate_one(session, snapshot_date, window_days, start, group_by_role: bool) -> int:
    role_select = "role" if group_by_role else "NULL::varchar AS role"
    role_group = ", role" if group_by_role else ""

    sql = text(f"""
        SELECT skill, {role_select}, COUNT(DISTINCT jd_key) AS cnt
        FROM (
            SELECT jd_key, role,
                   jsonb_array_elements_text(skills_canonical) AS skill
            FROM jd_raw
            WHERE posted_date BETWEEN :start AND :end
        ) s
        GROUP BY skill{role_group}
    """)
    rows = session.execute(sql, {"start": start, "end": snapshot_date}).fetchall()

    count = 0
    for row in rows:
        skill_canonical = row[0]
        role = row[1]
        demand_count = row[2]
        if not skill_canonical:
            continue
        stmt = pg_insert(SkillTrend).values(
            skill_canonical=skill_canonical,
            snapshot_date=snapshot_date,
            window_days=window_days,
            role=role,
            location=None,
            demand_count=demand_count,
        ).on_conflict_do_update(
            constraint="uq_skill_trend",
            set_={"demand_count": demand_count},
        )
        session.execute(stmt)
        count += 1
    return count
