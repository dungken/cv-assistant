"""Data Quality Audit for jd_raw — Layers 1 + 2.

Layer 1 (Completeness): coverage % per field.
Layer 2 (Validity): rule-based sanity checks — values within expected ranges.

Run:
    PYTHONPATH=. .venv/bin/python -m services.crawler_service.scripts.eval.data_quality \
        --out services/crawler_service/data/eval/data_quality_report.md

Writes a markdown report (and prints to stdout). No external dependencies beyond
what the crawler service already uses.
"""
from __future__ import annotations

import argparse
import os
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

from sqlalchemy import create_engine, text


DB_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://skill_user:skill_password@localhost:5434/skill_data",
)


# ── Layer 1: Completeness ────────────────────────────────────────

COMPLETENESS_FIELDS = [
    # (field, sql_filter_for_non_empty, required_target_pct)
    ("title",              "title IS NOT NULL AND title <> ''",                95),
    ("company",            "company IS NOT NULL AND company <> ''",            90),
    ("url",                "url IS NOT NULL AND url <> ''",                    98),
    ("description",        "description IS NOT NULL AND length(description) > 100", 60),
    ("posted_date",        "posted_date IS NOT NULL",                          98),
    ("location",           "location IS NOT NULL AND location <> ''",          85),
    ("salary_min",         "salary_min IS NOT NULL",                           20),
    ("salary_max",         "salary_max IS NOT NULL",                           20),
    ("salary_currency",    "salary_currency IS NOT NULL",                      20),
    ("skills_canonical",   "jsonb_array_length(skills_canonical) > 0",         70),
    ("role",               "role IS NOT NULL AND role <> ''",                  50),
    ("role_group",         "role_group IS NOT NULL AND role_group <> ''",      50),
    # Enrichment fields (lower targets — fill in by parser, not crawler)
    ("seniority",          "seniority IS NOT NULL",                            30),
    ("min_exp",            "min_exp IS NOT NULL",                              25),
    ("max_exp",            "max_exp IS NOT NULL",                              15),
    ("work_mode",          "work_mode IS NOT NULL",                            25),
    ("degree_required",    "degree_required IS NOT NULL",                      10),
    ("skills_required",    "jsonb_array_length(skills_required) > 0",          25),
    ("skills_preferred",   "jsonb_array_length(skills_preferred) > 0",         10),
    ("description_summary", "description_summary IS NOT NULL AND description_summary <> ''", 25),
]


def completeness_table(db, source_filter: str = "") -> list[dict]:
    where = f"WHERE {source_filter}" if source_filter else ""
    total = db.execute(text(f"SELECT COUNT(*) FROM jd_raw {where}")).scalar() or 0
    rows = []
    for field, filt, target in COMPLETENESS_FIELDS:
        sql = f"SELECT COUNT(*) FROM jd_raw {where}{'  AND' if where else 'WHERE'} {filt}"
        cnt = db.execute(text(sql)).scalar() or 0
        pct = (cnt / total * 100) if total else 0
        verdict = "✅" if pct >= target else ("⚠️" if pct >= target * 0.7 else "❌")
        rows.append({
            "field": field, "cnt": cnt, "total": total,
            "pct": round(pct, 1), "target": target, "verdict": verdict,
        })
    return rows


# ── Layer 2: Validity (sanity checks) ────────────────────────────

VALIDITY_CHECKS = [
    ("salary_min ≤ salary_max",
     "SELECT COUNT(*) FROM jd_raw WHERE salary_min IS NOT NULL AND salary_max IS NOT NULL AND salary_min > salary_max",
     "rows where salary_min > salary_max (logical error)"),
    ("min_exp in [0, 20]",
     "SELECT COUNT(*) FROM jd_raw WHERE min_exp IS NOT NULL AND (min_exp < 0 OR min_exp > 20)",
     "rows with min_exp outside reasonable range"),
    ("max_exp in [0, 30]",
     "SELECT COUNT(*) FROM jd_raw WHERE max_exp IS NOT NULL AND (max_exp < 0 OR max_exp > 30)",
     "rows with max_exp outside reasonable range"),
    ("min_exp ≤ max_exp",
     "SELECT COUNT(*) FROM jd_raw WHERE min_exp IS NOT NULL AND max_exp IS NOT NULL AND min_exp > max_exp",
     "rows where min_exp > max_exp (logical error)"),
    ("posted_date not in future",
     "SELECT COUNT(*) FROM jd_raw WHERE posted_date > CURRENT_DATE",
     "rows posted in the future (clock bug or scrape error)"),
    ("posted_date not too old (>2y)",
     "SELECT COUNT(*) FROM jd_raw WHERE posted_date < CURRENT_DATE - INTERVAL '2 years'",
     "rows older than 2 years (stale platform listing)"),
    ("seniority in enum",
     """SELECT COUNT(*) FROM jd_raw
        WHERE seniority IS NOT NULL AND seniority NOT IN
        ('intern','junior','mid','mid-senior','senior','lead','manager','principal')""",
     "rows with unrecognized seniority value"),
    ("work_mode in enum",
     "SELECT COUNT(*) FROM jd_raw WHERE work_mode IS NOT NULL AND work_mode NOT IN ('onsite','hybrid','remote')",
     "rows with unrecognized work_mode value"),
    ("salary_currency in enum",
     "SELECT COUNT(*) FROM jd_raw WHERE salary_currency IS NOT NULL AND salary_currency NOT IN ('USD','VND','EUR','SGD','JPY')",
     "rows with unrecognized salary currency"),
    ("description length reasonable",
     "SELECT COUNT(*) FROM jd_raw WHERE description IS NOT NULL AND length(description) > 50000",
     "rows with abnormally long description (>50KB)"),
    ("URL well-formed",
     "SELECT COUNT(*) FROM jd_raw WHERE url IS NOT NULL AND url <> '' AND url NOT LIKE 'http%'",
     "rows with malformed URL"),
    ("no duplicate jd_key",
     "SELECT COALESCE(SUM(c - 1), 0) FROM (SELECT COUNT(*) c FROM jd_raw GROUP BY jd_key) g",
     "extra rows beyond the first per jd_key (should be 0 with PK)"),
    ("no duplicate (source, url) pair",
     """SELECT COALESCE(SUM(c - 1), 0) FROM (
            SELECT COUNT(*) c FROM jd_raw
            WHERE url IS NOT NULL AND url <> ''
            GROUP BY source, split_part(url, '?', 1)
        ) g""",
     "extra rows for the same source + canonical URL (duplicate detection)"),
]


def validity_table(db) -> list[dict]:
    rows = []
    for name, sql, desc in VALIDITY_CHECKS:
        violations = db.execute(text(sql)).scalar() or 0
        verdict = "✅" if violations == 0 else ("⚠️" if violations <= 5 else "❌")
        rows.append({"check": name, "violations": violations, "desc": desc, "verdict": verdict})
    return rows


# ── Report builder ───────────────────────────────────────────────

def build_md(completeness_all: list[dict], completeness_by_source: dict,
             validity: list[dict], total_rows: int) -> str:
    lines: list[str] = []
    lines.append("# Data Quality Audit — `jd_raw`")
    lines.append("")
    lines.append(f"_Generated: {date.today().isoformat()} · Total rows: **{total_rows:,}**_")
    lines.append("")

    # Layer 1 overall
    lines.append("## Layer 1 — Completeness (overall)")
    lines.append("")
    lines.append("| Field | Coverage | Target | Status |")
    lines.append("|---|---|---|---|")
    for r in completeness_all:
        lines.append(f"| `{r['field']}` | {r['cnt']:,}/{r['total']:,} ({r['pct']}%) | ≥{r['target']}% | {r['verdict']} |")
    lines.append("")

    # Layer 1 per source
    lines.append("## Layer 1 — Completeness (per source)")
    lines.append("")
    sources = list(completeness_by_source.keys())
    if sources:
        # Wide table: rows = field, cols = source
        header = "| Field |" + "".join(f" {s} |" for s in sources)
        sep    = "|---|" + "".join("---|" for _ in sources)
        lines.append(header)
        lines.append(sep)
        # Use first source as reference for field order
        field_names = [r["field"] for r in completeness_by_source[sources[0]]]
        for fname in field_names:
            cells = []
            for s in sources:
                r = next((x for x in completeness_by_source[s] if x["field"] == fname), None)
                cells.append(f" {r['pct']}% {r['verdict']}" if r else " — ")
            lines.append(f"| `{fname}` |" + "|".join(cells) + "|")
        lines.append("")

    # Layer 2
    lines.append("## Layer 2 — Validity (sanity checks)")
    lines.append("")
    lines.append("| Check | Violations | Status | Description |")
    lines.append("|---|---|---|---|")
    for r in validity:
        lines.append(f"| {r['check']} | {r['violations']:,} | {r['verdict']} | {r['desc']} |")
    lines.append("")

    # Summary
    pass_l1 = sum(1 for r in completeness_all if r["verdict"] == "✅")
    pass_l2 = sum(1 for r in validity if r["verdict"] == "✅")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- **Layer 1 (Completeness):** {pass_l1}/{len(completeness_all)} fields meet target")
    lines.append(f"- **Layer 2 (Validity):** {pass_l2}/{len(validity)} checks pass with zero violations")
    lines.append("")
    overall = "✅ Good" if pass_l1 + pass_l2 >= (len(completeness_all) + len(validity)) * 0.8 else "⚠️ Needs review"
    lines.append(f"**Overall verdict:** {overall}")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "services/crawler_service/data/eval/data_quality_report.md"))
    args = ap.parse_args()

    engine = create_engine(DB_URL, future=True)
    with engine.connect() as db:
        total = db.execute(text("SELECT COUNT(*) FROM jd_raw")).scalar() or 0
        if total == 0:
            print("⚠️  jd_raw is empty — nothing to audit.")
            return 1

        sources = [r[0] for r in db.execute(text("SELECT DISTINCT source FROM jd_raw ORDER BY source")).all()]

        completeness_all = completeness_table(db)
        completeness_by_source = {
            s: completeness_table(db, source_filter=f"source = '{s}'") for s in sources
        }
        validity = validity_table(db)

    report = build_md(completeness_all, completeness_by_source, validity, total)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(report, encoding="utf-8")
    print(report)
    print(f"\n→ Saved: {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
