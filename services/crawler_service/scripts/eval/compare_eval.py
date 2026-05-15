"""Side-by-side comparison: rule-only vs rule+LLM eval on the same gold set.

Runs the eval pipeline twice (once per backend) and produces a single
markdown report with both columns + delta. Useful for the "ship/no-ship"
decision and for the thesis report's Chương 4.

Run from repo root (after gold_labels.jsonl exists):
    PYTHONPATH=. .venv/bin/python -m services.crawler_service.scripts.eval.compare_eval \\
        --gold services/crawler_service/data/eval/gold_labels.jsonl \\
        --report services/crawler_service/data/eval/compare_report.md
"""
from __future__ import annotations

import argparse
import json
import logging
import math
import os
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from services.crawler_service.services.structured_extractor import extract as rule_extract


logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("compare-eval")

DB_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://skill_user:skill_password@localhost:5434/skill_data",
)

SCALAR_FIELDS = ["seniority", "degree_required", "work_mode", "salary_currency"]
INT_FIELDS = ["min_exp", "max_exp", "salary_min", "salary_max"]


# ─── Helpers (mirror run_eval.py) ─────────────────────────────────────────────


def equal_scalar(a, b) -> bool:
    if a is None and b is None: return True
    if a is None or b is None: return False
    if isinstance(a, str) and isinstance(b, str):
        return a.strip().lower() == b.strip().lower()
    return a == b


def equal_int(a, b) -> bool:
    if a is None and b is None: return True
    if a is None or b is None: return False
    return int(a) == int(b)


def jaccard(set_a, set_b) -> float:
    a = {s.lower() for s in (set_a or [])}
    b = {s.lower() for s in (set_b or [])}
    if not a and not b: return 1.0
    union = len(a | b)
    return len(a & b) / union if union else 0.0


def bucket_accuracy(pred_req, pred_pref, gold_req, gold_pref) -> dict:
    pr = {s.lower() for s in (pred_req or [])}
    pp = {s.lower() for s in (pred_pref or [])}
    hits = total = 0
    rh = rt = ph = pt = 0
    for s in (gold_req or []):
        total += 1; rt += 1
        if s.lower() in pr:
            hits += 1; rh += 1
    for s in (gold_pref or []):
        total += 1; pt += 1
        if s.lower() in pp:
            hits += 1; ph += 1
    return {"hits": hits, "total": total, "rh": rh, "rt": rt, "ph": ph, "pt": pt}


def wilson_ci(hits: int, total: int, z: float = 1.96) -> tuple[float, float]:
    if total == 0: return (0.0, 0.0)
    p = hits / total
    n = total
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    margin = (z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / denom
    return (max(0.0, centre - margin), min(1.0, centre + margin))


# ─── Pipeline runner ─────────────────────────────────────────────────────────


def run_pipeline(jd_key: str, db, llm) -> dict:
    """Returns prediction. If `llm` is not None, applies LLM overlay."""
    row = db.execute(text("""
        SELECT title, description, skills_canonical
        FROM jd_raw WHERE jd_key = :k
    """), {"k": jd_key}).first()
    if row is None:
        return {}
    title, description, skills_canonical = row
    skills_canonical = list(skills_canonical or [])
    pred = rule_extract(title=title, description=description, all_skills=skills_canonical)
    out = {
        "seniority": pred.seniority,
        "min_exp": pred.min_exp,
        "max_exp": pred.max_exp,
        "degree_required": pred.degree_required,
        "work_mode": pred.work_mode,
        "skills_required": pred.skills_required,
        "skills_preferred": pred.skills_preferred,
    }
    sal = db.execute(text("""
        SELECT salary_min, salary_max, salary_currency FROM jd_raw WHERE jd_key = :k
    """), {"k": jd_key}).first()
    if sal:
        out["salary_min"], out["salary_max"], out["salary_currency"] = sal

    if llm is not None and description and len(description) >= 80:
        llm_out = llm.extract(
            title=title, description=description, candidate_skills=skills_canonical,
        )
        if llm_out is not None:
            if llm_out.seniority is not None: out["seniority"] = llm_out.seniority
            if llm_out.min_exp is not None: out["min_exp"] = llm_out.min_exp
            if llm_out.max_exp is not None: out["max_exp"] = llm_out.max_exp
            if llm_out.degree_required is not None: out["degree_required"] = llm_out.degree_required
            if llm_out.skills_required: out["skills_required"] = llm_out.skills_required
            if llm_out.skills_preferred: out["skills_preferred"] = llm_out.skills_preferred
            if out.get("work_mode") is None and llm_out.work_mode is not None:
                out["work_mode"] = llm_out.work_mode
            if out.get("salary_min") is None and llm_out.salary_min is not None:
                out["salary_min"] = llm_out.salary_min
            if out.get("salary_max") is None and llm_out.salary_max is not None:
                out["salary_max"] = llm_out.salary_max
            if not out.get("salary_currency") and llm_out.salary_currency:
                out["salary_currency"] = llm_out.salary_currency
    return out


@dataclass
class BackendStats:
    name: str
    field_correct: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    field_total: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    jaccard_required: list[float] = field(default_factory=list)
    jaccard_preferred: list[float] = field(default_factory=list)
    bucket_hits: int = 0
    bucket_total: int = 0
    req_hits: int = 0
    req_total: int = 0
    pref_hits: int = 0
    pref_total: int = 0


def run_backend(name: str, gold_records: list[dict], db, llm) -> BackendStats:
    stats = BackendStats(name=name)
    for rec in gold_records:
        gold = rec["gold_labels"]
        pred = run_pipeline(rec["jd_key"], db, llm)
        if not pred:
            continue
        for f in SCALAR_FIELDS:
            stats.field_total[f] += 1
            if equal_scalar(pred.get(f), gold.get(f)):
                stats.field_correct[f] += 1
        for f in INT_FIELDS:
            stats.field_total[f] += 1
            if equal_int(pred.get(f), gold.get(f)):
                stats.field_correct[f] += 1
        stats.jaccard_required.append(jaccard(pred.get("skills_required"), gold.get("skills_required")))
        stats.jaccard_preferred.append(jaccard(pred.get("skills_preferred"), gold.get("skills_preferred")))
        ba = bucket_accuracy(
            pred.get("skills_required"), pred.get("skills_preferred"),
            gold.get("skills_required"), gold.get("skills_preferred"),
        )
        stats.bucket_hits += ba["hits"]; stats.bucket_total += ba["total"]
        stats.req_hits += ba["rh"]; stats.req_total += ba["rt"]
        stats.pref_hits += ba["ph"]; stats.pref_total += ba["pt"]
    return stats


# ─── Report formatting ───────────────────────────────────────────────────────


def fmt_pct(hits: int, total: int) -> str:
    if total == 0: return "—"
    p = hits / total
    lo, hi = wilson_ci(hits, total)
    return f"{p*100:.1f}% [{lo*100:.1f}-{hi*100:.1f}]"


def fmt_avg(vals: list[float]) -> str:
    if not vals: return "—"
    return f"{sum(vals)/len(vals)*100:.1f}%"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--gold", required=True)
    ap.add_argument("--report", default=None)
    args = ap.parse_args()

    gold_path = Path(args.gold)
    if not gold_path.exists():
        logger.error("Gold file not found: %s", gold_path)
        return 1

    gold_records = []
    with gold_path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                gold_records.append(json.loads(line))
    logger.info("Loaded %d gold records", len(gold_records))
    if not gold_records:
        return 1

    # LLM (best-effort; if unavailable, second column is skipped)
    llm = None
    try:
        from services.crawler_service.services.llm_extractor import LLMJDExtractor
        llm = LLMJDExtractor()
        logger.info("LLM backend: %s", llm.model)
    except Exception as e:
        logger.warning("LLM unavailable (%s) — comparing rule-only vs (none).", e)

    engine = create_engine(DB_URL, future=True)
    SessionLocal = sessionmaker(bind=engine, future=True)
    db = SessionLocal()
    try:
        rule_stats = run_backend("rule-only", gold_records, db, llm=None)
        llm_stats = run_backend("rule + LLM", gold_records, db, llm=llm) if llm else None
    finally:
        db.close()

    # ── Build report ──
    lines: list[str] = []
    lines.append("# JD Extraction — Backend Comparison")
    lines.append(f"\nGold set: `{args.gold}`  ·  N = {len(gold_records)}\n")

    lines.append("## Per-field accuracy (95% Wilson CI)\n")
    if llm_stats:
        lines.append("| Field | Rule-only | Rule + LLM | Δ |")
        lines.append("|---|---|---|---|")
        for f in SCALAR_FIELDS + INT_FIELDS:
            r_acc = rule_stats.field_correct[f] / max(rule_stats.field_total[f], 1)
            l_acc = llm_stats.field_correct[f] / max(llm_stats.field_total[f], 1)
            delta = (l_acc - r_acc) * 100
            arrow = "🟢" if delta > 1 else ("🔴" if delta < -1 else "⚪")
            lines.append(
                f"| `{f}` | {fmt_pct(rule_stats.field_correct[f], rule_stats.field_total[f])} "
                f"| {fmt_pct(llm_stats.field_correct[f], llm_stats.field_total[f])} "
                f"| {arrow} {delta:+.1f}pp |"
            )
    else:
        lines.append("| Field | Rule-only |")
        lines.append("|---|---|")
        for f in SCALAR_FIELDS + INT_FIELDS:
            lines.append(f"| `{f}` | {fmt_pct(rule_stats.field_correct[f], rule_stats.field_total[f])} |")

    lines.append("\n## Skill extraction\n")
    if llm_stats:
        lines.append("| Metric | Rule-only | Rule + LLM | Δ |")
        lines.append("|---|---|---|---|")
        r_jr = sum(rule_stats.jaccard_required) / len(rule_stats.jaccard_required) if rule_stats.jaccard_required else 0
        l_jr = sum(llm_stats.jaccard_required) / len(llm_stats.jaccard_required) if llm_stats.jaccard_required else 0
        r_jp = sum(rule_stats.jaccard_preferred) / len(rule_stats.jaccard_preferred) if rule_stats.jaccard_preferred else 0
        l_jp = sum(llm_stats.jaccard_preferred) / len(llm_stats.jaccard_preferred) if llm_stats.jaccard_preferred else 0
        lines.append(f"| Jaccard(required) | {r_jr*100:.1f}% | {l_jr*100:.1f}% | {(l_jr-r_jr)*100:+.1f}pp |")
        lines.append(f"| Jaccard(preferred) | {r_jp*100:.1f}% | {l_jp*100:.1f}% | {(l_jp-r_jp)*100:+.1f}pp |")
        lines.append(f"| Bucket overall | {fmt_pct(rule_stats.bucket_hits, rule_stats.bucket_total)} "
                     f"| {fmt_pct(llm_stats.bucket_hits, llm_stats.bucket_total)} "
                     f"| — |")
        lines.append(f"| Required recall | {fmt_pct(rule_stats.req_hits, rule_stats.req_total)} "
                     f"| {fmt_pct(llm_stats.req_hits, llm_stats.req_total)} "
                     f"| — |")
        lines.append(f"| Preferred recall | {fmt_pct(rule_stats.pref_hits, rule_stats.pref_total)} "
                     f"| {fmt_pct(llm_stats.pref_hits, llm_stats.pref_total)} "
                     f"| — |")
    else:
        lines.append("| Metric | Rule-only |")
        lines.append("|---|---|")
        lines.append(f"| Jaccard(required) | {fmt_avg(rule_stats.jaccard_required)} |")
        lines.append(f"| Jaccard(preferred) | {fmt_avg(rule_stats.jaccard_preferred)} |")
        lines.append(f"| Bucket overall | {fmt_pct(rule_stats.bucket_hits, rule_stats.bucket_total)} |")

    lines.append("")
    lines.append("## Aggregate summary\n")

    def _macro_acc(stats: BackendStats) -> float:
        accs = [
            stats.field_correct[f] / stats.field_total[f]
            for f in SCALAR_FIELDS + INT_FIELDS
            if stats.field_total[f] > 0
        ]
        return sum(accs) / len(accs) if accs else 0

    r_macro = _macro_acc(rule_stats)
    lines.append(f"- **Rule-only** macro-avg accuracy across 8 fields: **{r_macro*100:.1f}%**")
    if llm_stats:
        l_macro = _macro_acc(llm_stats)
        lines.append(f"- **Rule + LLM** macro-avg accuracy across 8 fields: **{l_macro*100:.1f}%**")
        lines.append(f"- **Δ overall**: {(l_macro-r_macro)*100:+.1f}pp")
    lines.append("")

    # ── Decision matrix ──
    lines.append("## Decision matrix\n")
    lines.append("| Macro-avg | Action |")
    lines.append("|---|---|")
    lines.append("| ≥ 85% | Ship pipeline cho dashboard. Document trong báo cáo. |")
    lines.append("| 75–85% | Ship rule-only. Mark LLM as future improvement. |")
    lines.append("| < 75% | Cần fine-tune (Path 2). Build dataset 500 JD lên. |")
    lines.append("")

    report = "\n".join(lines)
    print(report)

    if args.report:
        Path(args.report).parent.mkdir(parents=True, exist_ok=True)
        Path(args.report).write_text(report, encoding="utf-8")
        logger.info("Report written to %s", args.report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
