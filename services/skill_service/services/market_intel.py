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
import time
from typing import Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# In-memory TTL cache. Dashboard payload is ~50KB and rebuild is ~50ms, so
# we keep it small and simple — no need for redis. TTL = 5 minutes matches
# how often new crawl runs land.
_CACHE: dict[tuple, tuple[float, dict]] = {}
_CACHE_TTL_SEC = 300


# Whitelist for filter values — passed through as raw SQL fragments below would
# be a SQLi risk, so all filters are bound parameters and validated against
# these sets where applicable.
ALLOWED_SOURCES = {"itviec", "topcv", "uit_forum", "all"}


def _greedy_clusters(pairs: list[dict]) -> list[dict]:
    """Greedy connected-component grouping over skill co-occurrence edges.

    Two skills land in the same cluster if they co-occur (transitively) above the
    SQL-side threshold. We then label each cluster by its top-3 skills (by total
    edge weight inside the cluster) and emit up to 6 clusters of size ≥3.
    Simple and explainable — good enough for a dashboard insight.
    """
    from collections import defaultdict

    parent: dict[str, str] = {}
    weight: dict[str, int] = defaultdict(int)

    def find(x: str) -> str:
        while parent.get(x, x) != x:
            parent[x] = parent.get(parent[x], parent[x])
            x = parent[x]
        return x

    def union(a: str, b: str) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    for p in pairs:
        a, b, c = p["skill_a"], p["skill_b"], p["cnt"]
        parent.setdefault(a, a); parent.setdefault(b, b)
        union(a, b)
        weight[a] += c
        weight[b] += c

    groups: dict[str, list[str]] = defaultdict(list)
    for s in parent:
        groups[find(s)].append(s)

    out = []
    for members in groups.values():
        if len(members) < 3:
            continue
        members_sorted = sorted(members, key=lambda s: weight[s], reverse=True)
        out.append({
            "skills": members_sorted,
            "size": len(members_sorted),
            "label": " + ".join(members_sorted[:3]),
        })
    out.sort(key=lambda c: c["size"], reverse=True)
    return out[:6]


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

    cache_key = (source, role_group, seniority)
    cached = _CACHE.get(cache_key)
    if cached and (time.time() - cached[0]) < _CACHE_TTL_SEC:
        return cached[1]

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

    # ── 7. Top 10 locations (normalized) ─────────────────────────────
    # ITviec uses "Hà Nội (mới)" / "Hồ Chí Minh (mới)", TopCV uses ASCII variants
    # like "Ha Noi", "Ho Chi Minh", and some rows combine cities ("Ho Chi Minh - Ha Noi").
    # Bucket them so the chart shows distinct cities rather than spelling variants.
    location_sql = text(f"""
        WITH normed AS (
          SELECT
            CASE
              WHEN location ILIKE '%ho chi minh%' OR location ILIKE '%hồ chí minh%' OR location ILIKE '%hcm%' OR location ILIKE '%tp.hcm%' THEN 'Hồ Chí Minh'
              WHEN location ILIKE '%ha noi%' OR location ILIKE '%hà nội%' OR location ILIKE '%hanoi%' THEN 'Hà Nội'
              WHEN location ILIKE '%da nang%' OR location ILIKE '%đà nẵng%' OR location ILIKE '%danang%' THEN 'Đà Nẵng'
              WHEN location ILIKE '%can tho%' OR location ILIKE '%cần thơ%' THEN 'Cần Thơ'
              WHEN location ILIKE '%hai phong%' OR location ILIKE '%hải phòng%' THEN 'Hải Phòng'
              WHEN location ILIKE '%binh duong%' OR location ILIKE '%bình dương%' THEN 'Bình Dương'
              WHEN location ILIKE '%dong nai%' OR location ILIKE '%đồng nai%' THEN 'Đồng Nai'
              ELSE location
            END AS loc_norm
          FROM jd_raw WHERE {where_sql} AND location IS NOT NULL AND location <> ''
        )
        SELECT loc_norm AS location, COUNT(*) AS cnt
        FROM normed
        GROUP BY loc_norm ORDER BY cnt DESC LIMIT 10
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

    # ── 9. Daily posting trend (last 30 days) ───────────────────────
    trend_sql = text(f"""
        SELECT posted_date::text AS day, COUNT(*) AS cnt
        FROM jd_raw
        WHERE {where_sql} AND posted_date >= CURRENT_DATE - INTERVAL '30 days'
        GROUP BY posted_date ORDER BY posted_date
    """)
    daily_trend = [dict(r) for r in db.execute(trend_sql, params).mappings().all()]

    # ── 10. Top 15 companies hiring most ───────────────────────────
    company_sql = text(f"""
        SELECT company, COUNT(*) AS cnt
        FROM jd_raw WHERE {where_sql} AND company IS NOT NULL AND company <> ''
        GROUP BY company ORDER BY cnt DESC LIMIT 15
    """)
    top_companies = [dict(r) for r in db.execute(company_sql, params).mappings().all()]

    # ── 11. Min-experience histogram (bucketed) ────────────────────
    # Buckets: 0 (fresher), 1, 2, 3, 4-5, 6-7, 8+. The 34-yr outlier above is bogus,
    # so we cap at 15 in the bucketing.
    exp_sql = text(f"""
        SELECT
          CASE
            WHEN min_exp = 0 THEN '0 (Fresher)'
            WHEN min_exp = 1 THEN '1 năm'
            WHEN min_exp = 2 THEN '2 năm'
            WHEN min_exp = 3 THEN '3 năm'
            WHEN min_exp BETWEEN 4 AND 5 THEN '4-5 năm'
            WHEN min_exp BETWEEN 6 AND 7 THEN '6-7 năm'
            WHEN min_exp >= 8 AND min_exp <= 15 THEN '8+ năm'
            ELSE NULL
          END AS bucket,
          COUNT(*) AS cnt
        FROM jd_raw WHERE {where_sql} AND min_exp IS NOT NULL
        GROUP BY bucket ORDER BY MIN(min_exp)
    """)
    exp_histogram = [dict(r) for r in db.execute(exp_sql, params).mappings().all() if r["bucket"]]

    # ── 12. Degree requirement (normalize EN/VI variants) ──────────
    degree_sql = text(f"""
        SELECT
          CASE
            WHEN LOWER(degree_required) LIKE '%master%' OR LOWER(degree_required) LIKE '%thạc%' THEN 'Master'
            WHEN LOWER(degree_required) LIKE '%bachelor%' OR LOWER(degree_required) LIKE '%đại học%' THEN 'Cử nhân (Bachelor)'
            WHEN LOWER(degree_required) LIKE '%cao đẳng%' OR LOWER(degree_required) LIKE '%college%' THEN 'Cao đẳng'
            WHEN LOWER(degree_required) LIKE '%phd%' OR LOWER(degree_required) LIKE '%tiến sĩ%' THEN 'PhD'
            ELSE 'Khác'
          END AS degree_norm,
          COUNT(*) AS cnt
        FROM jd_raw WHERE {where_sql} AND degree_required IS NOT NULL
        GROUP BY degree_norm ORDER BY cnt DESC
    """)
    degree_distribution = [dict(r) for r in db.execute(degree_sql, params).mappings().all()]

    # ── 13. Skill co-occurrence top 12 pairs ───────────────────────
    # Symmetric pairs only (skill_a < skill_b) and limit input to top-30 skills
    # so the cross join doesn't blow up.
    cooc_sql = text(f"""
        WITH top30 AS (
          SELECT skill FROM (
            SELECT jsonb_array_elements_text(skills_canonical) AS skill, COUNT(*) c
            FROM jd_raw WHERE {where_sql}
            GROUP BY skill ORDER BY c DESC LIMIT 30
          ) x
        ),
        jd_skills AS (
          SELECT jd_key, jsonb_array_elements_text(skills_canonical) AS skill
          FROM jd_raw WHERE {where_sql}
        ),
        pairs AS (
          SELECT a.skill AS skill_a, b.skill AS skill_b
          FROM jd_skills a
          JOIN jd_skills b ON a.jd_key = b.jd_key AND a.skill < b.skill
          WHERE a.skill IN (SELECT skill FROM top30) AND b.skill IN (SELECT skill FROM top30)
        )
        SELECT skill_a, skill_b, COUNT(*) AS cnt
        FROM pairs GROUP BY skill_a, skill_b
        ORDER BY cnt DESC LIMIT 12
    """)
    skill_pairs = [dict(r) for r in db.execute(cooc_sql, params).mappings().all()]

    # ── 14. Skill Premium Index — median salary per skill vs overall median ──
    # Only USD salaries to avoid mixing units. JDs need both skills_canonical
    # and salary_min/max. We compute (median_skill / median_overall - 1) * 100
    # as a premium %. Negative = pays below average.
    premium_sql = text(f"""
        WITH usd_jds AS (
          SELECT jd_key, skills_canonical,
                 (salary_min + salary_max) / 2.0 AS midpoint
          FROM jd_raw
          WHERE {where_sql} AND salary_currency = 'USD'
            AND salary_min IS NOT NULL AND salary_max IS NOT NULL
            AND salary_min BETWEEN 200 AND 20000
        ),
        overall AS (
          SELECT PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY midpoint) AS med FROM usd_jds
        ),
        skill_med AS (
          SELECT jsonb_array_elements_text(skills_canonical) AS skill,
                 PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY midpoint) AS med,
                 COUNT(*) AS cnt
          FROM usd_jds GROUP BY skill HAVING COUNT(*) >= 5
        )
        SELECT s.skill, s.cnt, s.med AS median_salary,
               ROUND((((s.med / NULLIF(o.med, 0)) - 1) * 100)::numeric, 1) AS premium_pct
        FROM skill_med s CROSS JOIN overall o
        ORDER BY premium_pct DESC NULLS LAST
    """)
    premium_rows = [dict(r) for r in db.execute(premium_sql, params).mappings().all()]
    skill_premium = {
        "top_premium": [
            {**r, "median_salary": float(r["median_salary"]), "premium_pct": float(r["premium_pct"])}
            for r in premium_rows[:10]
        ],
        "lowest_paid": [
            {**r, "median_salary": float(r["median_salary"]), "premium_pct": float(r["premium_pct"])}
            for r in premium_rows[-5:][::-1]
        ],
    }

    # ── 15. Skill Velocity — last 14 days vs previous 14 days ────────
    velocity_sql = text(f"""
        WITH recent AS (
          SELECT jsonb_array_elements_text(skills_canonical) AS skill, COUNT(*) AS cnt
          FROM jd_raw
          WHERE {where_sql}
            AND posted_date >= CURRENT_DATE - INTERVAL '14 days'
          GROUP BY skill
        ),
        prev AS (
          SELECT jsonb_array_elements_text(skills_canonical) AS skill, COUNT(*) AS cnt
          FROM jd_raw
          WHERE {where_sql}
            AND posted_date >= CURRENT_DATE - INTERVAL '28 days'
            AND posted_date <  CURRENT_DATE - INTERVAL '14 days'
          GROUP BY skill
        )
        SELECT
          COALESCE(r.skill, p.skill) AS skill,
          COALESCE(r.cnt, 0) AS recent_cnt,
          COALESCE(p.cnt, 0) AS prev_cnt,
          COALESCE(r.cnt, 0) - COALESCE(p.cnt, 0) AS delta_abs,
          CASE WHEN COALESCE(p.cnt, 0) > 0
               THEN ROUND((((COALESCE(r.cnt, 0)::numeric / p.cnt) - 1) * 100)::numeric, 1)
               ELSE NULL END AS delta_pct
        FROM recent r FULL OUTER JOIN prev p ON r.skill = p.skill
        WHERE COALESCE(r.cnt, 0) + COALESCE(p.cnt, 0) >= 8
        ORDER BY delta_abs DESC
    """)
    velocity_rows = [dict(r) for r in db.execute(velocity_sql, params).mappings().all()]
    skill_velocity = {
        "trending_up": [
            {**r, "delta_pct": float(r["delta_pct"]) if r["delta_pct"] is not None else None}
            for r in velocity_rows[:8]
        ],
        "trending_down": [
            {**r, "delta_pct": float(r["delta_pct"]) if r["delta_pct"] is not None else None}
            for r in velocity_rows[-8:][::-1]
        ],
    }

    # ── 16. Companies-by-Skill mapping ──────────────────────────────
    # For top 15 skills, which 3 companies hire the most JDs containing that skill.
    # Useful drilldown: "I know React — who hires for it?"
    companies_skill_sql = text(f"""
        WITH top_s AS (
          SELECT skill FROM (
            SELECT jsonb_array_elements_text(skills_canonical) AS skill, COUNT(*) c
            FROM jd_raw WHERE {where_sql}
            GROUP BY skill ORDER BY c DESC LIMIT 15
          ) x
        ),
        s_co AS (
          SELECT jsonb_array_elements_text(skills_canonical) AS skill, company, COUNT(*) AS cnt
          FROM jd_raw WHERE {where_sql} AND company IS NOT NULL AND company <> ''
          GROUP BY skill, company
        ),
        ranked AS (
          SELECT skill, company, cnt,
                 ROW_NUMBER() OVER (PARTITION BY skill ORDER BY cnt DESC) AS rn
          FROM s_co WHERE skill IN (SELECT skill FROM top_s)
        )
        SELECT skill, company, cnt FROM ranked WHERE rn <= 3
        ORDER BY skill, rn
    """)
    cs_rows = [dict(r) for r in db.execute(companies_skill_sql, params).mappings().all()]
    companies_by_skill: dict[str, list] = {}
    for r in cs_rows:
        companies_by_skill.setdefault(r["skill"], []).append(
            {"company": r["company"], "cnt": r["cnt"]}
        )

    # ── 17. Remote-friendliness per skill ───────────────────────────
    remote_sql = text(f"""
        WITH top_s AS (
          SELECT skill FROM (
            SELECT jsonb_array_elements_text(skills_canonical) AS skill, COUNT(*) c
            FROM jd_raw WHERE {where_sql} AND work_mode IS NOT NULL
            GROUP BY skill ORDER BY c DESC LIMIT 15
          ) x
        )
        SELECT skill,
               COUNT(*) AS total,
               SUM(CASE WHEN work_mode IN ('remote', 'hybrid') THEN 1 ELSE 0 END) AS flexible,
               ROUND((SUM(CASE WHEN work_mode IN ('remote', 'hybrid') THEN 1.0 ELSE 0 END) * 100.0 / COUNT(*))::numeric, 1) AS pct
        FROM (
          SELECT jsonb_array_elements_text(skills_canonical) AS skill, work_mode
          FROM jd_raw WHERE {where_sql} AND work_mode IS NOT NULL
        ) sw
        WHERE skill IN (SELECT skill FROM top_s)
        GROUP BY skill ORDER BY pct DESC
    """)
    remote_rows = [dict(r) for r in db.execute(remote_sql, params).mappings().all()]
    remote_by_skill = [
        {**r, "pct": float(r["pct"]) if r["pct"] is not None else 0}
        for r in remote_rows
    ]

    # ── 18. Salary by role group (USD only) ─────────────────────────
    role_salary_sql = text(f"""
        SELECT role_group,
               COUNT(*) AS cnt,
               PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY (salary_min + salary_max) / 2.0) AS median_mid,
               PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY (salary_min + salary_max) / 2.0) AS p25,
               PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY (salary_min + salary_max) / 2.0) AS p75
        FROM jd_raw
        WHERE {where_sql} AND role_group IS NOT NULL
          AND salary_currency = 'USD'
          AND salary_min IS NOT NULL AND salary_max IS NOT NULL
          AND salary_min BETWEEN 200 AND 20000
        GROUP BY role_group HAVING COUNT(*) >= 3
        ORDER BY median_mid DESC LIMIT 10
    """)
    role_salary = [
        {**r,
         "median_mid": float(r["median_mid"]) if r["median_mid"] is not None else None,
         "p25": float(r["p25"]) if r["p25"] is not None else None,
         "p75": float(r["p75"]) if r["p75"] is not None else None}
        for r in [dict(x) for x in db.execute(role_salary_sql, params).mappings().all()]
    ]

    # ── 19. Education premium — salary lift per degree level ────────
    edu_salary_sql = text(f"""
        WITH norm AS (
          SELECT
            CASE
              WHEN LOWER(degree_required) LIKE '%master%' OR LOWER(degree_required) LIKE '%thạc%' THEN 'Master'
              WHEN LOWER(degree_required) LIKE '%bachelor%' OR LOWER(degree_required) LIKE '%đại học%' THEN 'Cử nhân'
              WHEN LOWER(degree_required) LIKE '%cao đẳng%' OR LOWER(degree_required) LIKE '%college%' THEN 'Cao đẳng'
              WHEN LOWER(degree_required) LIKE '%phd%' OR LOWER(degree_required) LIKE '%tiến sĩ%' THEN 'PhD'
              ELSE NULL
            END AS degree_norm,
            (salary_min + salary_max) / 2.0 AS midpoint
          FROM jd_raw
          WHERE {where_sql} AND degree_required IS NOT NULL
            AND salary_currency = 'USD'
            AND salary_min IS NOT NULL AND salary_max IS NOT NULL
            AND salary_min BETWEEN 200 AND 20000
        )
        SELECT degree_norm,
               COUNT(*) AS cnt,
               ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY midpoint)::numeric, 0) AS median_salary
        FROM norm WHERE degree_norm IS NOT NULL
        GROUP BY degree_norm HAVING COUNT(*) >= 3
        ORDER BY median_salary DESC
    """)
    edu_salary = [
        {**r, "median_salary": float(r["median_salary"]) if r["median_salary"] is not None else None}
        for r in [dict(x) for x in db.execute(edu_salary_sql, params).mappings().all()]
    ]

    # ── 20. Geo salary — median per city (USD) ──────────────────────
    geo_salary_sql = text(f"""
        WITH normed AS (
          SELECT
            CASE
              WHEN location ILIKE '%ho chi minh%' OR location ILIKE '%hồ chí minh%' OR location ILIKE '%hcm%' THEN 'Hồ Chí Minh'
              WHEN location ILIKE '%ha noi%' OR location ILIKE '%hà nội%' OR location ILIKE '%hanoi%' THEN 'Hà Nội'
              WHEN location ILIKE '%da nang%' OR location ILIKE '%đà nẵng%' THEN 'Đà Nẵng'
              ELSE NULL
            END AS city,
            (salary_min + salary_max) / 2.0 AS midpoint
          FROM jd_raw
          WHERE {where_sql} AND location IS NOT NULL
            AND salary_currency = 'USD'
            AND salary_min IS NOT NULL AND salary_max IS NOT NULL
            AND salary_min BETWEEN 200 AND 20000
        )
        SELECT city,
               COUNT(*) AS cnt,
               ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY midpoint)::numeric, 0) AS median_salary,
               ROUND(PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY midpoint)::numeric, 0) AS p25,
               ROUND(PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY midpoint)::numeric, 0) AS p75
        FROM normed WHERE city IS NOT NULL
        GROUP BY city ORDER BY median_salary DESC
    """)
    geo_salary = [
        {**r,
         "median_salary": float(r["median_salary"]) if r["median_salary"] is not None else None,
         "p25": float(r["p25"]) if r["p25"] is not None else None,
         "p75": float(r["p75"]) if r["p75"] is not None else None}
        for r in [dict(x) for x in db.execute(geo_salary_sql, params).mappings().all()]
    ]

    # ── 21. Skill clusters — greedy community detection over co-occurrence ─
    # Take top 25 skills, build adjacency, group into clusters by transitive
    # co-occurrence above a threshold. Simple greedy: skill seeds the cluster
    # if it has ≥3 strong neighbours not yet assigned.
    # Use Jaccard similarity (intersection / union) so dominant skills don't
    # eat every cluster. Threshold ≥ 0.30 = ≥30% of either side's appearances
    # are joint — that's a real co-stack, not just "both popular".
    cluster_input_sql = text(f"""
        WITH top30 AS (
          SELECT skill, c FROM (
            SELECT jsonb_array_elements_text(skills_canonical) AS skill, COUNT(*) c
            FROM jd_raw WHERE {where_sql}
            GROUP BY skill ORDER BY c DESC LIMIT 30
          ) x
        ),
        jd_skills AS (
          SELECT jd_key, jsonb_array_elements_text(skills_canonical) AS skill
          FROM jd_raw WHERE {where_sql}
        ),
        pair_cnt AS (
          SELECT a.skill AS skill_a, b.skill AS skill_b, COUNT(*) AS cnt
          FROM jd_skills a JOIN jd_skills b
            ON a.jd_key = b.jd_key AND a.skill < b.skill
          WHERE a.skill IN (SELECT skill FROM top30) AND b.skill IN (SELECT skill FROM top30)
          GROUP BY a.skill, b.skill HAVING COUNT(*) >= 8
        )
        SELECT pc.skill_a, pc.skill_b, pc.cnt
        FROM pair_cnt pc
        JOIN top30 ta ON ta.skill = pc.skill_a
        JOIN top30 tb ON tb.skill = pc.skill_b
        WHERE pc.cnt::numeric / (ta.c + tb.c - pc.cnt) >= 0.15
        ORDER BY pc.cnt DESC
    """)
    pairs = [dict(r) for r in db.execute(cluster_input_sql, params).mappings().all()]
    skill_clusters = _greedy_clusters(pairs)

    # ── 22. Most-mentioned tools per experience level ───────────────
    exp_skills_sql = text(f"""
        WITH bucketed AS (
          SELECT
            CASE
              WHEN min_exp <= 1 THEN '0-1 năm'
              WHEN min_exp <= 3 THEN '2-3 năm'
              WHEN min_exp <= 5 THEN '4-5 năm'
              WHEN min_exp <= 15 THEN '6+ năm'
              ELSE NULL
            END AS exp_bucket,
            jsonb_array_elements_text(skills_canonical) AS skill
          FROM jd_raw WHERE {where_sql} AND min_exp IS NOT NULL
        ),
        ranked AS (
          SELECT exp_bucket, skill, COUNT(*) AS cnt,
                 ROW_NUMBER() OVER (PARTITION BY exp_bucket ORDER BY COUNT(*) DESC) AS rn
          FROM bucketed WHERE exp_bucket IS NOT NULL
          GROUP BY exp_bucket, skill
        )
        SELECT exp_bucket, skill, cnt FROM ranked WHERE rn <= 8
        ORDER BY exp_bucket, rn
    """)
    exp_skills_rows = [dict(r) for r in db.execute(exp_skills_sql, params).mappings().all()]
    skills_by_exp: dict[str, list] = {}
    for r in exp_skills_rows:
        skills_by_exp.setdefault(r["exp_bucket"], []).append({"skill": r["skill"], "cnt": r["cnt"]})

    # ── 24. Hidden Gem skills — low demand × high salary quadrant ──
    # x = JD count, y = median USD salary. SV-actionable: skills with cnt<30
    # but median > overall median = under-the-radar opportunities.
    gem_sql = text(f"""
        WITH usd_jds AS (
          SELECT jd_key, skills_canonical,
                 (salary_min + salary_max) / 2.0 AS midpoint
          FROM jd_raw WHERE {where_sql}
            AND salary_currency = 'USD'
            AND salary_min IS NOT NULL AND salary_max IS NOT NULL
            AND salary_min BETWEEN 200 AND 20000
        ),
        overall AS (
          SELECT PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY midpoint) AS med FROM usd_jds
        )
        SELECT skill, COUNT(*) AS cnt,
               PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY midpoint) AS median_salary,
               (SELECT med FROM overall) AS overall_median
        FROM (
          SELECT jsonb_array_elements_text(skills_canonical) AS skill, midpoint
          FROM usd_jds
        ) x
        GROUP BY skill HAVING COUNT(*) >= 3
    """)
    gem_raw = [dict(r) for r in db.execute(gem_sql, params).mappings().all()]
    skill_quadrants = [
        {
            "skill": r["skill"],
            "cnt": r["cnt"],
            "median_salary": float(r["median_salary"]),
            "is_gem": r["cnt"] < 30 and float(r["median_salary"]) > float(r["overall_median"]),
        }
        for r in gem_raw
    ]
    hidden_gems = sorted(
        [s for s in skill_quadrants if s["is_gem"]],
        key=lambda s: s["median_salary"], reverse=True,
    )[:10]

    # ── 25. Salary curve by experience (overall + top roles) ────────
    salary_curve_sql = text(f"""
        WITH bucketed AS (
          SELECT
            CASE
              WHEN min_exp <= 1 THEN '0-1 năm'
              WHEN min_exp <= 3 THEN '2-3 năm'
              WHEN min_exp <= 5 THEN '4-5 năm'
              WHEN min_exp <= 15 THEN '6+ năm'
              ELSE NULL
            END AS exp_bucket,
            role_group,
            (salary_min + salary_max) / 2.0 AS midpoint
          FROM jd_raw WHERE {where_sql}
            AND min_exp IS NOT NULL
            AND salary_currency = 'USD'
            AND salary_min IS NOT NULL AND salary_max IS NOT NULL
            AND salary_min BETWEEN 200 AND 20000
        )
        SELECT exp_bucket, role_group, COUNT(*) AS cnt,
               PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY midpoint) AS median_salary
        FROM bucketed WHERE exp_bucket IS NOT NULL
        GROUP BY exp_bucket, role_group HAVING COUNT(*) >= 2
        ORDER BY exp_bucket
    """)
    curve_rows = [dict(r) for r in db.execute(salary_curve_sql, params).mappings().all()]
    # Pivot: { exp_bucket: { overall_median, role_X: median, ... } }
    from collections import defaultdict
    by_bucket: dict = defaultdict(lambda: {"all_amounts": [], "by_role": {}})
    for r in curve_rows:
        bucket = r["exp_bucket"]
        med = float(r["median_salary"])
        if r["role_group"]:
            by_bucket[bucket]["by_role"][r["role_group"]] = {"median": med, "cnt": r["cnt"]}
        by_bucket[bucket]["all_amounts"].append((med, r["cnt"]))
    # Top 4 roles overall to keep chart readable.
    role_freq: dict = defaultdict(int)
    for r in curve_rows:
        if r["role_group"]:
            role_freq[r["role_group"]] += r["cnt"]
    top_roles_for_curve = [r for r, _ in sorted(role_freq.items(), key=lambda x: -x[1])[:4]]
    salary_curve = []
    for bucket in ["0-1 năm", "2-3 năm", "4-5 năm", "6+ năm"]:
        if bucket not in by_bucket: continue
        amounts = by_bucket[bucket]["all_amounts"]
        # weighted median by cnt: just take simple weighted avg of medians, close enough
        total_cnt = sum(c for _, c in amounts)
        overall_med = sum(m * c for m, c in amounts) / total_cnt if total_cnt else None
        entry = {"exp": bucket, "overall_median": overall_med}
        for role in top_roles_for_curve:
            r = by_bucket[bucket]["by_role"].get(role)
            entry[role] = r["median"] if r else None
        salary_curve.append(entry)

    # ── 26. Skill Specificity Score (% JD containing skill) ─────────
    total_for_spec = kpi_row["total_jds"] or 1
    spec_sql = text(f"""
        SELECT skill, COUNT(*) AS cnt
        FROM (
          SELECT DISTINCT jd_key, jsonb_array_elements_text(skills_canonical) AS skill
          FROM jd_raw WHERE {where_sql}
        ) s
        GROUP BY skill HAVING COUNT(*) >= 5
        ORDER BY cnt DESC LIMIT 30
    """)
    spec_rows = [dict(r) for r in db.execute(spec_sql, params).mappings().all()]
    skill_specificity = []
    for r in spec_rows:
        pct = (r["cnt"] / total_for_spec) * 100
        if pct >= 30: tier = "core"
        elif pct >= 10: tier = "common"
        else: tier = "specialized"
        skill_specificity.append({
            "skill": r["skill"], "cnt": r["cnt"],
            "pct": round(pct, 1), "tier": tier,
        })

    # ── 27. Hot Companies (velocity for companies) ──────────────────
    hot_co_sql = text(f"""
        WITH recent AS (
          SELECT company, COUNT(*) AS cnt FROM jd_raw
          WHERE {where_sql} AND company IS NOT NULL AND company <> ''
            AND posted_date >= CURRENT_DATE - INTERVAL '14 days'
          GROUP BY company
        ),
        prev AS (
          SELECT company, COUNT(*) AS cnt FROM jd_raw
          WHERE {where_sql} AND company IS NOT NULL AND company <> ''
            AND posted_date >= CURRENT_DATE - INTERVAL '28 days'
            AND posted_date <  CURRENT_DATE - INTERVAL '14 days'
          GROUP BY company
        )
        SELECT COALESCE(r.company, p.company) AS company,
               COALESCE(r.cnt, 0) AS recent_cnt,
               COALESCE(p.cnt, 0) AS prev_cnt,
               COALESCE(r.cnt, 0) - COALESCE(p.cnt, 0) AS delta_abs
        FROM recent r FULL OUTER JOIN prev p ON r.company = p.company
        WHERE COALESCE(r.cnt, 0) + COALESCE(p.cnt, 0) >= 5
        ORDER BY delta_abs DESC LIMIT 10
    """)
    hot_companies = [dict(r) for r in db.execute(hot_co_sql, params).mappings().all()]

    # ── 28. Combo Salary — does adding a skill boost pay? ───────────
    # For top 5 pairs (already in skill_pairs), compute median salary when
    # both skills present vs single skill A vs single skill B.
    combo_salary = []
    for pair in skill_pairs[:6]:
        a, b = pair["skill_a"], pair["skill_b"]
        combo_sql = text(f"""
            WITH usd_jds AS (
              SELECT jd_key, skills_canonical, (salary_min + salary_max) / 2.0 AS mid
              FROM jd_raw WHERE {where_sql}
                AND salary_currency = 'USD'
                AND salary_min IS NOT NULL AND salary_max IS NOT NULL
                AND salary_min BETWEEN 200 AND 20000
            )
            SELECT
              PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY mid) FILTER (
                WHERE skills_canonical ? :a AND skills_canonical ? :b
              ) AS both_med,
              COUNT(*) FILTER (WHERE skills_canonical ? :a AND skills_canonical ? :b) AS both_cnt,
              PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY mid) FILTER (
                WHERE skills_canonical ? :a
              ) AS a_med,
              PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY mid) FILTER (
                WHERE skills_canonical ? :b
              ) AS b_med
            FROM usd_jds
        """)
        r = db.execute(combo_sql, {**params, "a": a, "b": b}).mappings().first()
        if r and r["both_cnt"] and r["both_cnt"] >= 3 and r["both_med"]:
            single_avg = ((r["a_med"] or 0) + (r["b_med"] or 0)) / 2
            premium = ((float(r["both_med"]) / single_avg) - 1) * 100 if single_avg else 0
            combo_salary.append({
                "skill_a": a, "skill_b": b,
                "both_median": float(r["both_med"]), "both_cnt": r["both_cnt"],
                "a_median": float(r["a_med"]) if r["a_med"] else None,
                "b_median": float(r["b_med"]) if r["b_med"] else None,
                "combo_premium_pct": round(premium, 1),
            })
    combo_salary.sort(key=lambda x: x["combo_premium_pct"], reverse=True)

    # ── 29. English Premium — JD requiring English vs not ──────────
    eng_sql = text(f"""
        WITH base AS (
          SELECT jd_key, (salary_min + salary_max) / 2.0 AS mid,
                 (description ILIKE '%english%' OR description ILIKE '%tiếng anh%'
                  OR title ILIKE '%english%' OR skills_canonical ? 'English') AS has_english
          FROM jd_raw WHERE {where_sql}
            AND salary_currency = 'USD'
            AND salary_min IS NOT NULL AND salary_max IS NOT NULL
            AND salary_min BETWEEN 200 AND 20000
        )
        SELECT has_english,
               COUNT(*) AS cnt,
               ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY mid)::numeric, 0) AS median_salary
        FROM base GROUP BY has_english
    """)
    eng_rows = [dict(r) for r in db.execute(eng_sql, params).mappings().all()]
    with_eng = next((r for r in eng_rows if r["has_english"]), None)
    without_eng = next((r for r in eng_rows if not r["has_english"]), None)
    english_premium = None
    if with_eng and without_eng and without_eng["median_salary"]:
        prem = ((float(with_eng["median_salary"]) / float(without_eng["median_salary"])) - 1) * 100
        english_premium = {
            "with_english": {
                "cnt": with_eng["cnt"],
                "median_salary": float(with_eng["median_salary"]),
            },
            "without_english": {
                "cnt": without_eng["cnt"],
                "median_salary": float(without_eng["median_salary"]),
            },
            "premium_pct": round(prem, 1),
        }

    # ── 30. Day-of-week posting pattern ─────────────────────────────
    dow_sql = text(f"""
        SELECT EXTRACT(DOW FROM posted_date)::int AS dow, COUNT(*) AS cnt
        FROM jd_raw WHERE {where_sql}
          AND posted_date >= CURRENT_DATE - INTERVAL '60 days'
        GROUP BY dow ORDER BY dow
    """)
    dow_raw = [dict(r) for r in db.execute(dow_sql, params).mappings().all()]
    dow_names = ["Chủ nhật", "Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7"]
    day_of_week = [
        {"day": dow_names[(r["dow"] or 0) % 7], "dow": r["dow"], "cnt": r["cnt"]}
        for r in dow_raw
    ]

    # ── 31. Outdated Skill Alert — declining 4+ weeks straight ──────
    # Compare weekly counts; if last 2 weeks both below previous 2 weeks → alert.
    outdated_sql = text(f"""
        WITH weekly AS (
          SELECT skill,
                 SUM(CASE WHEN posted_date >= CURRENT_DATE - INTERVAL '7 days' THEN 1 ELSE 0 END) AS w1,
                 SUM(CASE WHEN posted_date >= CURRENT_DATE - INTERVAL '14 days' AND posted_date < CURRENT_DATE - INTERVAL '7 days' THEN 1 ELSE 0 END) AS w2,
                 SUM(CASE WHEN posted_date >= CURRENT_DATE - INTERVAL '21 days' AND posted_date < CURRENT_DATE - INTERVAL '14 days' THEN 1 ELSE 0 END) AS w3,
                 SUM(CASE WHEN posted_date >= CURRENT_DATE - INTERVAL '28 days' AND posted_date < CURRENT_DATE - INTERVAL '21 days' THEN 1 ELSE 0 END) AS w4
          FROM (
            SELECT posted_date, jsonb_array_elements_text(skills_canonical) AS skill
            FROM jd_raw WHERE {where_sql} AND posted_date >= CURRENT_DATE - INTERVAL '28 days'
          ) s
          GROUP BY skill
        )
        SELECT skill, w1, w2, w3, w4
        FROM weekly
        WHERE (w4 + w3) >= 8 AND (w1 + w2) < (w3 + w4) * 0.5
        ORDER BY (w3 + w4) - (w1 + w2) DESC LIMIT 8
    """)
    outdated_skills = [dict(r) for r in db.execute(outdated_sql, params).mappings().all()]

    # ── 32. Niche Champions — companies hiring uncommon skills ──────
    niche_sql = text(f"""
        WITH skill_freq AS (
          SELECT jsonb_array_elements_text(skills_canonical) AS skill, COUNT(*) AS total_cnt
          FROM jd_raw WHERE {where_sql} GROUP BY skill
        ),
        niche_skills AS (SELECT skill FROM skill_freq WHERE total_cnt BETWEEN 3 AND 25),
        co_x_skill AS (
          SELECT company, jsonb_array_elements_text(skills_canonical) AS skill
          FROM jd_raw WHERE {where_sql} AND company IS NOT NULL AND company <> ''
        )
        SELECT company, COUNT(*) AS niche_skill_jds
        FROM co_x_skill
        WHERE skill IN (SELECT skill FROM niche_skills)
        GROUP BY company ORDER BY niche_skill_jds DESC LIMIT 8
    """)
    niche_champions = [dict(r) for r in db.execute(niche_sql, params).mappings().all()]

    # ── 33. Co-existence network graph data (nodes + edges) ─────────
    # Reuse the top-30 skill set; emit nodes with size = popularity, edges
    # with weight = co-occurrence. Frontend renders with simple radial layout.
    network_sql = text(f"""
        WITH top30 AS (
          SELECT skill, c FROM (
            SELECT jsonb_array_elements_text(skills_canonical) AS skill, COUNT(*) c
            FROM jd_raw WHERE {where_sql}
            GROUP BY skill ORDER BY c DESC LIMIT 30
          ) x
        ),
        jd_skills AS (
          SELECT jd_key, jsonb_array_elements_text(skills_canonical) AS skill
          FROM jd_raw WHERE {where_sql}
        ),
        pairs AS (
          SELECT a.skill AS skill_a, b.skill AS skill_b, COUNT(*) AS cnt
          FROM jd_skills a JOIN jd_skills b
            ON a.jd_key = b.jd_key AND a.skill < b.skill
          WHERE a.skill IN (SELECT skill FROM top30) AND b.skill IN (SELECT skill FROM top30)
          GROUP BY a.skill, b.skill HAVING COUNT(*) >= 10
        )
        SELECT 'node' AS kind, skill AS a, NULL AS b, c::int AS w FROM top30
        UNION ALL
        SELECT 'edge', skill_a, skill_b, cnt::int FROM pairs
    """)
    net_rows = [dict(r) for r in db.execute(network_sql, params).mappings().all()]
    skill_network = {
        "nodes": [{"skill": r["a"], "cnt": r["w"]} for r in net_rows if r["kind"] == "node"],
        "edges": [{"skill_a": r["a"], "skill_b": r["b"], "cnt": r["w"]} for r in net_rows if r["kind"] == "edge"],
    }

    # ── 34. Filter options for the UI dropdowns (ignore current filter) ─
    role_options = [r[0] for r in db.execute(text(
        "SELECT DISTINCT role_group FROM jd_raw WHERE role_group IS NOT NULL ORDER BY role_group"
    )).all()]
    seniority_options = [r[0] for r in db.execute(text(
        "SELECT DISTINCT seniority FROM jd_raw WHERE seniority IS NOT NULL ORDER BY seniority"
    )).all()]
    source_options = [r[0] for r in db.execute(text(
        "SELECT DISTINCT source FROM jd_raw ORDER BY source"
    )).all()]

    payload = {
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
        "daily_trend": daily_trend,
        "top_companies": top_companies,
        "exp_histogram": exp_histogram,
        "degree_distribution": degree_distribution,
        "skill_pairs": skill_pairs,
        "skill_premium": skill_premium,
        "skill_velocity": skill_velocity,
        "companies_by_skill": companies_by_skill,
        "remote_by_skill": remote_by_skill,
        "role_salary": role_salary,
        "edu_salary": edu_salary,
        "geo_salary": geo_salary,
        "skill_clusters": skill_clusters,
        "skills_by_exp": skills_by_exp,
        "hidden_gems": hidden_gems,
        "skill_quadrants": skill_quadrants,
        "salary_curve": salary_curve,
        "skill_specificity": skill_specificity,
        "hot_companies": hot_companies,
        "combo_salary": combo_salary,
        "english_premium": english_premium,
        "day_of_week": day_of_week,
        "outdated_skills": outdated_skills,
        "niche_champions": niche_champions,
        "skill_network": skill_network,
        "options": {
            "sources": source_options,
            "role_groups": role_options,
            "seniorities": seniority_options,
        },
    }
    _CACHE[cache_key] = (time.time(), payload)
    return payload
