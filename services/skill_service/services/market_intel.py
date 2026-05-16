"""Market Intelligence — analytics over jd_raw for the /market-intel dashboard.

Differs from MarketAnalyzer (which scans Chroma metadata): this queries Postgres
directly so we can use real fields (seniority, work_mode, min_exp, ...) populated
by the JD enrichment pipeline. SQL-side aggregation also avoids loading thousands
of rows into Python.

All counts are derived from the same WHERE clause built from filters, so the
overview KPIs and the chart slices stay consistent.
"""
from __future__ import annotations

import logging
from typing import Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


# Whitelist for filter values — passed through as raw SQL fragments below would
# be a SQLi risk, so all filters are bound parameters and validated against
# these sets where applicable.
ALLOWED_SOURCES = {"itviec", "topcv", "uit_forum", "all"}


def _build_filters(source: str, role_group: Optional[str], seniority: Optional[str]) -> tuple[str, dict]:
    """Return (where_clause, params). Always starts with WHERE 1=1 for easy concat."""
    where = ["1=1"]
    params: dict = {}
    if source and source != "all":
        where.append("source = :source")
        params["source"] = source
    if role_group:
        where.append("role_group = :role_group")
        params["role_group"] = role_group
    if seniority:
        where.append("seniority = :seniority")
        params["seniority"] = seniority
    return " AND ".join(where), params


def get_dashboard(
    db: Session,
    source: str = "all",
    role_group: Optional[str] = None,
    seniority: Optional[str] = None,
) -> dict:
    """Return one big payload for the Market Intel dashboard.

    Single endpoint by design — the frontend renders 8 widgets off this and we
    avoid 8 round-trips. ~50ms even on 1.5K JDs because every aggregation runs
    in Postgres.
    """
    if source not in ALLOWED_SOURCES:
        source = "all"

    where_sql, params = _build_filters(source, role_group, seniority)

    # ── 1. Overview KPIs ────────────────────────────────────────────
    kpi_sql = text(f"""
        SELECT
          COUNT(*) AS total_jds,
          COUNT(DISTINCT company) FILTER (WHERE company IS NOT NULL AND company <> '') AS total_companies,
          COUNT(DISTINCT source) AS total_sources,
          MIN(posted_date) AS earliest_post,
          MAX(posted_date) AS latest_post
        FROM jd_raw WHERE {where_sql}
    """)
    kpi_row = db.execute(kpi_sql, params).mappings().one()

    source_breakdown_sql = text(f"""
        SELECT source, COUNT(*) AS cnt
        FROM jd_raw WHERE {where_sql}
        GROUP BY source ORDER BY cnt DESC
    """)
    source_breakdown = [dict(r) for r in db.execute(source_breakdown_sql, params).mappings().all()]

    # Distinct skill count needs an unnest, so it's its own query.
    skill_count_sql = text(f"""
        SELECT COUNT(DISTINCT skill) AS unique_skills
        FROM (
          SELECT jsonb_array_elements_text(skills_canonical) AS skill
          FROM jd_raw WHERE {where_sql}
        ) s
    """)
    unique_skills = db.execute(skill_count_sql, params).scalar() or 0

    # ── 2. Top 20 hot skills ────────────────────────────────────────
    top_skills_sql = text(f"""
        SELECT skill, COUNT(*) AS cnt
        FROM (
          SELECT jsonb_array_elements_text(skills_canonical) AS skill
          FROM jd_raw WHERE {where_sql}
        ) s
        WHERE skill <> ''
        GROUP BY skill ORDER BY cnt DESC LIMIT 20
    """)
    top_skills = [dict(r) for r in db.execute(top_skills_sql, params).mappings().all()]

    # ── 3. Role group distribution ──────────────────────────────────
    role_sql = text(f"""
        SELECT role_group, COUNT(*) AS cnt
        FROM jd_raw WHERE {where_sql} AND role_group IS NOT NULL
        GROUP BY role_group ORDER BY cnt DESC LIMIT 12
    """)
    role_distribution = [dict(r) for r in db.execute(role_sql, params).mappings().all()]

    # ── 4. Seniority breakdown ──────────────────────────────────────
    seniority_sql = text(f"""
        SELECT seniority, COUNT(*) AS cnt
        FROM jd_raw WHERE {where_sql} AND seniority IS NOT NULL
        GROUP BY seniority ORDER BY cnt DESC
    """)
    seniority_distribution = [dict(r) for r in db.execute(seniority_sql, params).mappings().all()]

    # ── 5. Work mode breakdown ──────────────────────────────────────
    work_mode_sql = text(f"""
        SELECT work_mode, COUNT(*) AS cnt
        FROM jd_raw WHERE {where_sql} AND work_mode IS NOT NULL
        GROUP BY work_mode ORDER BY cnt DESC
    """)
    work_mode_distribution = [dict(r) for r in db.execute(work_mode_sql, params).mappings().all()]

    # ── 6. Salary by seniority (median min, median max in USD-ish) ──
    # We don't normalize currency here — most ITviec values are USD, TopCV are VND.
    # Frontend caveat shown next to the chart.
    salary_sql = text(f"""
        SELECT
          COALESCE(seniority, 'unknown') AS seniority,
          salary_currency AS currency,
          COUNT(*) AS cnt,
          PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY salary_min) AS median_min,
          PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY salary_max) AS median_max
        FROM jd_raw
        WHERE {where_sql} AND salary_min IS NOT NULL AND salary_max IS NOT NULL
        GROUP BY seniority, salary_currency
        HAVING COUNT(*) >= 3
        ORDER BY seniority
    """)
    salary_by_seniority = [dict(r) for r in db.execute(salary_sql, params).mappings().all()]

    # ── 7. Top 10 locations ─────────────────────────────────────────
    location_sql = text(f"""
        SELECT location, COUNT(*) AS cnt
        FROM jd_raw WHERE {where_sql} AND location IS NOT NULL AND location <> ''
        GROUP BY location ORDER BY cnt DESC LIMIT 10
    """)
    top_locations = [dict(r) for r in db.execute(location_sql, params).mappings().all()]

    # ── 8. Skill × role-group heatmap (top 10 skills × top 6 roles) ─
    heatmap_sql = text(f"""
        WITH top_s AS (
          SELECT skill FROM (
            SELECT jsonb_array_elements_text(skills_canonical) AS skill, COUNT(*) c
            FROM jd_raw WHERE {where_sql}
            GROUP BY skill ORDER BY c DESC LIMIT 10
          ) x
        ),
        top_r AS (
          SELECT role_group FROM jd_raw
          WHERE {where_sql} AND role_group IS NOT NULL
          GROUP BY role_group ORDER BY COUNT(*) DESC LIMIT 6
        )
        SELECT skill, role_group, COUNT(*) AS cnt
        FROM (
          SELECT role_group, jsonb_array_elements_text(skills_canonical) AS skill
          FROM jd_raw WHERE {where_sql} AND role_group IS NOT NULL
        ) sr
        WHERE skill IN (SELECT skill FROM top_s) AND role_group IN (SELECT role_group FROM top_r)
        GROUP BY skill, role_group
    """)
    heatmap_rows = [dict(r) for r in db.execute(heatmap_sql, params).mappings().all()]

    # ── 9. Filter options for the UI dropdowns (ignore current filter) ─
    role_options = [r[0] for r in db.execute(text(
        "SELECT DISTINCT role_group FROM jd_raw WHERE role_group IS NOT NULL ORDER BY role_group"
    )).all()]
    seniority_options = [r[0] for r in db.execute(text(
        "SELECT DISTINCT seniority FROM jd_raw WHERE seniority IS NOT NULL ORDER BY seniority"
    )).all()]
    source_options = [r[0] for r in db.execute(text(
        "SELECT DISTINCT source FROM jd_raw ORDER BY source"
    )).all()]

    return {
        "filters_applied": {
            "source": source,
            "role_group": role_group,
            "seniority": seniority,
        },
        "kpis": {
            "total_jds": kpi_row["total_jds"] or 0,
            "total_companies": kpi_row["total_companies"] or 0,
            "total_sources": kpi_row["total_sources"] or 0,
            "unique_skills": unique_skills,
            "earliest_post": kpi_row["earliest_post"].isoformat() if kpi_row["earliest_post"] else None,
            "latest_post": kpi_row["latest_post"].isoformat() if kpi_row["latest_post"] else None,
        },
        "source_breakdown": source_breakdown,
        "top_skills": top_skills,
        "role_distribution": role_distribution,
        "seniority_distribution": seniority_distribution,
        "work_mode_distribution": work_mode_distribution,
        "salary_by_seniority": [
            {**r, "median_min": float(r["median_min"]) if r["median_min"] is not None else None,
                  "median_max": float(r["median_max"]) if r["median_max"] is not None else None}
            for r in salary_by_seniority
        ],
        "top_locations": top_locations,
        "heatmap": heatmap_rows,
        "options": {
            "sources": source_options,
            "role_groups": role_options,
            "seniorities": seniority_options,
        },
    }
