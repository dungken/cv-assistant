"""Normalize gold labels theo convention của rule extractor.

Gold do labeler tạo ra có một số convention khác với rule extractor:
- Seniority: gold dùng compound 'mid-senior', 'manager', 'director' → rule enum {junior, mid, senior, lead}
- Work mode: gold dùng compound 'onsite/hybrid', 'remote/hybrid' → rule enum {onsite, hybrid, remote}
- min_exp: gold đôi khi chọn middle of range, rule luôn chọn min

Script này normalize gold để eval consistent với rule.

Run từ repo root:
    .venv/bin/python -m services.crawler_service.scripts.eval.normalize_gold \\
        --input services/crawler_service/data/eval/gold_labels_remapped.jsonl \\
        --output services/crawler_service/data/eval/gold_labels_normalized.jsonl
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


# Seniority mapping: gold → rule enum
SENIORITY_MAP = {
    "mid-senior": "senior",
    "manager": "lead",
    "director": "lead",
    "leader": "lead",
}

# Work mode mapping: compound → single
WORK_MODE_MAP = {
    "onsite/hybrid": "hybrid",   # presence of hybrid wins
    "remote/hybrid": "remote",   # remote stronger
    "hybrid/onsite": "hybrid",
    "hybrid/remote": "remote",
}


def normalize_seniority(value):
    if value is None:
        return None
    return SENIORITY_MAP.get(value, value)


def normalize_work_mode(value):
    if value is None:
        return None
    return WORK_MODE_MAP.get(value, value)


def normalize_record(record: dict) -> dict:
    gold = record.get("gold_labels", {})
    gold["seniority"] = normalize_seniority(gold.get("seniority"))
    gold["work_mode"] = normalize_work_mode(gold.get("work_mode"))
    record["gold_labels"] = gold
    return record


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    in_path = Path(args.input)
    out_path = Path(args.output)

    n_changed = 0
    out_lines = []
    with in_path.open() as f:
        for line in f:
            record = json.loads(line)
            orig = json.dumps(record.get("gold_labels", {}), sort_keys=True)
            record = normalize_record(record)
            new = json.dumps(record.get("gold_labels", {}), sort_keys=True)
            if orig != new:
                n_changed += 1
            out_lines.append(json.dumps(record, ensure_ascii=False))

    out_path.write_text("\n".join(out_lines) + "\n", encoding="utf-8")
    print(f"Normalized {n_changed}/{len(out_lines)} records → {out_path}")


if __name__ == "__main__":
    main()
