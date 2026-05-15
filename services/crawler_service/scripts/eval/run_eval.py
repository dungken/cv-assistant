"""Evaluate the JD extraction pipeline against gold labels.

Reads `gold_labels.jsonl` (produced by label_ui.py) and runs the same
JDs through the extraction pipeline. Reports per-field accuracy +
confidence intervals + a confusion matrix for skills_required vs preferred.

Run from repo root:
    PYTHONPATH=. .venv/bin/python -m services.crawler_service.scripts.eval.run_eval \\
        --gold services/crawler_service/data/eval/gold_labels.jsonl \\
        --report services/crawler_service/data/eval/report.md \\
        [--use-llm]   # to evaluate the rule+LLM stack instead of rule-only
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
logger = logging.getLogger("eval")

DB_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://skill_user:skill_password@localhost:5434/skill_data",
)


# ─── Field comparators ───────────────────────────────────────────────────────


def equal_scalar(a, b) -> bool:
    """None == None counts as match. Strings compared case-insensitive."""
    if a is None and b is None:
        return True
    if a is None or b is None:
        return False
    if isinstance(a, str) and isinstance(b, str):
        return a.strip().lower() == b.strip().lower()
    return a == b


def equal_int(a, b) -> bool:
    if a is None and b is None:
        return True
    if a is None or b is None:
        return False
    return int(a) == int(b)


def jaccard(set_a: set[str], set_b: set[str]) -> float:
    """Jaccard similarity for skill lists. Both empty → 1.0 (perfect)."""
    a = {s.lower() for s in (set_a or [])}
    b = {s.lower() for s in (set_b or [])}
    if not a and not b:
        return 1.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union else 0.0


def bucket_accuracy(
    pred_req: list[str], pred_pref: list[str],
    gold_req: list[str], gold_pref: list[str],
) -> dict:
    """For every gold skill, did we put it in the right bucket?
    Returns {hits, total, by_bucket}."""
    pred_req_l = {s.lower() for s in (pred_req or [])}
    pred_pref_l = {s.lower() for s in (pred_pref or [])}

    hits = 0
    total = 0
    bucket_hits = {"required": 0, "preferred": 0}
    bucket_totals = {"required": 0, "preferred": 0}

    for s in (gold_req or []):
        sl = s.lower()
        total += 1
        bucket_totals["required"] += 1
        if sl in pred_req_l:
            hits += 1
            bucket_hits["required"] += 1
    for s in (gold_pref or []):
        sl = s.lower()
        total += 1
        bucket_totals["preferred"] += 1
        if sl in pred_pref_l:
            hits += 1
            bucket_hits["preferred"] += 1

    return {
        "hits": hits, "total": total,
        "by_bucket": {
            b: (bucket_hits[b], bucket_totals[b]) for b in bucket_hits
        },
    }


# ─── Wilson confidence interval ──────────────────────────────────────────────


def wilson_ci(hits: int, total: int, z: float = 1.96) -> tuple[float, float]:
    """95% Wilson score interval for a binomial proportion.
    More robust than normal approximation when p is near 0 or 1."""
    if total == 0:
        return (0.0, 0.0)
    p = hits / total
    n = total
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    margin = (z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / denom
    return (max(0.0, centre - margin), min(1.0, centre + margin))


# ─── Pipeline runner ─────────────────────────────────────────────────────────


@dataclass
class FieldResult:
    correct: int = 0
    total: int = 0
    samples_wrong: list[dict] = field(default_factory=list)  # for error analysis


def run_pipeline_on_jd(
    jd_key: str,
    db,
    use_llm: bool,
    llm=None,
) -> dict:
    """Re-run the rule-based + optional LLM extractor on a single JD."""
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
        # Salary comes from JSON-LD upstream — we read it from jd_raw.
    }
    sal = db.execute(text("""
        SELECT salary_min, salary_max, salary_currency FROM jd_raw WHERE jd_key = :k
    """), {"k": jd_key}).first()
    if sal:
        out["salary_min"], out["salary_max"], out["salary_currency"] = sal

    if use_llm and llm is not None and description and len(description) >= 80:
        llm_out = llm.extract(
            title=title, description=description, candidate_skills=skills_canonical,
        )
        if llm_out is not None:
            # Same merge logic as pipeline._build_processed
            if llm_out.seniority is not None:
                out["seniority"] = llm_out.seniority
            if llm_out.min_exp is not None:
                out["min_exp"] = llm_out.min_exp
            if llm_out.max_exp is not None:
                out["max_exp"] = llm_out.max_exp
            if llm_out.degree_required is not None:
                out["degree_required"] = llm_out.degree_required
            if llm_out.skills_required:
                out["skills_required"] = llm_out.skills_required
            if llm_out.skills_preferred:
                out["skills_preferred"] = llm_out.skills_preferred
            if out.get("work_mode") is None and llm_out.work_mode is not None:
                out["work_mode"] = llm_out.work_mode
            if out.get("salary_min") is None and llm_out.salary_min is not None:
                out["salary_min"] = llm_out.salary_min
            if out.get("salary_max") is None and llm_out.salary_max is not None:
                out["salary_max"] = llm_out.salary_max
            if not out.get("salary_currency") and llm_out.salary_currency:
                out["salary_currency"] = llm_out.salary_currency
    return out


# ─── Main ────────────────────────────────────────────────────────────────────


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--gold", required=True, help="path to gold_labels.jsonl")
    ap.add_argument("--report", default=None, help="path to write markdown report")
    ap.add_argument("--use-llm", action="store_true", help="add LLM overlay")
    args = ap.parse_args()

    gold_path = Path(args.gold)
    if not gold_path.exists():
        logger.error("Gold file not found: %s", gold_path)
        return 1

    # Load gold
    gold_records: list[dict] = []
    with gold_path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                gold_records.append(json.loads(line))
    logger.info("Loaded %d gold records", len(gold_records))

    if not gold_records:
        logger.error("Gold file is empty")
        return 1

    # Optional LLM
    llm = None
    if args.use_llm:
        from services.crawler_service.services.llm_extractor import LLMJDExtractor
        try:
            llm = LLMJDExtractor()
            logger.info("Using LLM overlay: %s", llm.model)
        except ValueError as e:
            logger.error("LLM init failed: %s", e)
            return 1

    engine = create_engine(DB_URL, future=True)
    SessionLocal = sessionmaker(bind=engine, future=True)
    db = SessionLocal()

    # Per-field results
    SCALAR_FIELDS = ["seniority", "degree_required", "work_mode", "salary_currency"]
    INT_FIELDS = ["min_exp", "max_exp", "salary_min", "salary_max"]
    results: dict[str, FieldResult] = defaultdict(FieldResult)
    skills_jaccard_required: list[float] = []
    skills_jaccard_preferred: list[float] = []
    bucket_total = {"hits": 0, "total": 0,
                    "required_hits": 0, "required_total": 0,
                    "preferred_hits": 0, "preferred_total": 0}

    try:
        for rec in gold_records:
            jd_key = rec["jd_key"]
            gold = rec["gold_labels"]
            pred = run_pipeline_on_jd(jd_key, db, args.use_llm, llm)
            if not pred:
                logger.warning("JD %s not in DB, skipping", jd_key)
                continue

            for f in SCALAR_FIELDS:
                results[f].total += 1
                ok = equal_scalar(pred.get(f), gold.get(f))
                if ok:
                    results[f].correct += 1
                else:
                    results[f].samples_wrong.append({
                        "jd_key": jd_key, "gold": gold.get(f), "pred": pred.get(f),
                    })

            for f in INT_FIELDS:
                results[f].total += 1
                ok = equal_int(pred.get(f), gold.get(f))
                if ok:
                    results[f].correct += 1
                else:
                    results[f].samples_wrong.append({
                        "jd_key": jd_key, "gold": gold.get(f), "pred": pred.get(f),
                    })

            # Skills: Jaccard + bucket-accuracy
            jr = jaccard(pred.get("skills_required") or [], gold.get("skills_required") or [])
            jp = jaccard(pred.get("skills_preferred") or [], gold.get("skills_preferred") or [])
            skills_jaccard_required.append(jr)
            skills_jaccard_preferred.append(jp)

            ba = bucket_accuracy(
                pred.get("skills_required") or [], pred.get("skills_preferred") or [],
                gold.get("skills_required") or [], gold.get("skills_preferred") or [],
            )
            bucket_total["hits"] += ba["hits"]
            bucket_total["total"] += ba["total"]
            bucket_total["required_hits"] += ba["by_bucket"]["required"][0]
            bucket_total["required_total"] += ba["by_bucket"]["required"][1]
            bucket_total["preferred_hits"] += ba["by_bucket"]["preferred"][0]
            bucket_total["preferred_total"] += ba["by_bucket"]["preferred"][1]
    finally:
        db.close()

    # ── Report ──
    lines: list[str] = []
    backend = "rule + LLM" if args.use_llm else "rule-only"
    lines.append(f"# JD Extraction Eval — {backend}")
    lines.append(f"\nGold labels: `{args.gold}`  ·  N = {len(gold_records)}\n")

    lines.append("## Per-field accuracy (95% Wilson CI)\n")
    lines.append("| Field | Correct/Total | Accuracy | 95% CI |")
    lines.append("|---|---|---|---|")
    for f in SCALAR_FIELDS + INT_FIELDS:
        r = results[f]
        if r.total == 0:
            continue
        acc = r.correct / r.total
        lo, hi = wilson_ci(r.correct, r.total)
        lines.append(f"| `{f}` | {r.correct}/{r.total} | {acc*100:.1f}% | [{lo*100:.1f}%, {hi*100:.1f}%] |")

    # Skills
    n = len(skills_jaccard_required) or 1
    avg_jr = sum(skills_jaccard_required) / n
    avg_jp = sum(skills_jaccard_preferred) / n
    lines.append("")
    lines.append("## Skill extraction (per-JD averages)")
    lines.append("")
    lines.append(f"- **Jaccard(skills_required, gold)**: {avg_jr*100:.1f}%")
    lines.append(f"- **Jaccard(skills_preferred, gold)**: {avg_jp*100:.1f}%")
    lines.append("")
    lines.append("## Skill bucket accuracy (across all gold skills)\n")
    if bucket_total["total"]:
        bt_acc = bucket_total["hits"] / bucket_total["total"]
        bt_lo, bt_hi = wilson_ci(bucket_total["hits"], bucket_total["total"])
        lines.append(f"- Overall: **{bt_acc*100:.1f}%** ({bucket_total['hits']}/{bucket_total['total']}, "
                     f"95% CI [{bt_lo*100:.1f}%, {bt_hi*100:.1f}%])")
    if bucket_total["required_total"]:
        rh, rt = bucket_total["required_hits"], bucket_total["required_total"]
        rlo, rhi = wilson_ci(rh, rt)
        lines.append(f"- Required-skill recall: **{rh/rt*100:.1f}%** ({rh}/{rt}, [{rlo*100:.1f}%, {rhi*100:.1f}%])")
    if bucket_total["preferred_total"]:
        ph, pt = bucket_total["preferred_hits"], bucket_total["preferred_total"]
        plo, phi = wilson_ci(ph, pt)
        lines.append(f"- Preferred-skill recall: **{ph/pt*100:.1f}%** ({ph}/{pt}, [{plo*100:.1f}%, {phi*100:.1f}%])")
    lines.append("")

    # ── Error samples (first 3 per field) ──
    lines.append("## Error samples (first 3 per field)\n")
    for f in SCALAR_FIELDS + INT_FIELDS:
        r = results[f]
        if not r.samples_wrong:
            continue
        lines.append(f"\n### `{f}`")
        for s in r.samples_wrong[:3]:
            lines.append(f"- jd_key=`{s['jd_key']}`  gold=`{s['gold']}`  pred=`{s['pred']}`")

    report = "\n".join(lines)
    print(report)

    if args.report:
        Path(args.report).parent.mkdir(parents=True, exist_ok=True)
        Path(args.report).write_text(report, encoding="utf-8")
        logger.info("Wrote report to %s", args.report)

    return 0


if __name__ == "__main__":
    sys.exit(main())
