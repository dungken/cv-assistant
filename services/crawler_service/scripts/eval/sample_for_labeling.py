"""Build a stratified labeling sample from jd_raw.

Pulls JDs with non-empty descriptions, runs the rule-based extractor to
pre-fill labels, stratifies by language (EN / VI / Mixed) × role group,
and writes a JSONL file ready to be loaded into the labeling UI.

Output schema (one line per JD):
    {
      "jd_key": "...",
      "title": "...",
      "company": "...",
      "url": "...",
      "description": "...",        # full text for the UI to display
      "stratum": "vi-backend",     # stratification label
      "pre_labels": {              # rule-based extractor output (suggested defaults)
         "seniority": null,
         "min_exp": 5,
         "max_exp": null,
         "degree_required": null,
         "work_mode": "onsite",
         "skills_required": [...],
         "skills_preferred": [],
         "salary_min": 1000,
         "salary_max": 1800,
         "salary_currency": "USD"
      },
      "gold_labels": null          # filled by the UI
    }

Run from repo root:
    PYTHONPATH=. .venv/bin/python -m services.crawler_service.scripts.eval.sample_for_labeling \\
        --n 100 --out services/crawler_service/data/eval/label_pool.jsonl
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import random
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from services.crawler_service.services.structured_extractor import extract as rule_extract


logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("sample-for-labeling")

DB_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://skill_user:skill_password@localhost:5434/skill_data",
)

# Language detection heuristics — cheap regex on description.
_VI_DIACRITICS = re.compile(
    r"[àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ]"
)
_EN_STOPWORDS = re.compile(r"\b(the|a|an|with|for|and|to|of|in|on)\b", re.I)


def detect_lang(text_in: str) -> str:
    if not text_in:
        return "empty"
    has_vi = bool(_VI_DIACRITICS.search(text_in))
    en_hits = len(_EN_STOPWORDS.findall(text_in))
    if has_vi and en_hits >= 5:
        return "mixed"
    if has_vi:
        return "vi"
    return "en"


# Role groups for stratification. Map crawler role slug → coarse bucket.
_ROLE_BUCKETS = {
    "backend": ["backend", "java", "php", "python", "node", "go", "dotnet"],
    "frontend": ["frontend", "react", "vue", "angular"],
    "fullstack": ["fullstack", "full-stack"],
    "mobile": ["mobile", "ios", "android", "flutter", "react-native"],
    "data_ai": ["data", "ai", "machine", "ml", "analyst", "scientist", "bi"],
    "devops": ["devops", "sre", "infra", "cloud", "platform"],
    "other": ["pm", "designer", "qa", "test", "security", "auditor", "manager"],
}


def role_bucket(role: str | None, role_group: str | None, title: str | None) -> str:
    """Coarse-grained bucket so we can stratify even when role is missing."""
    hay = " ".join(filter(None, [role, role_group, title or ""])).lower()
    for bucket, keywords in _ROLE_BUCKETS.items():
        if any(k in hay for k in keywords):
            return bucket
    return "other"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=100, help="number of JDs to sample")
    ap.add_argument(
        "--out",
        default=str(ROOT / "services/crawler_service/data/eval/label_pool.jsonl"),
        help="output JSONL path",
    )
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    random.seed(args.seed)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    engine = create_engine(DB_URL, future=True)
    SessionLocal = sessionmaker(bind=engine, future=True)

    sql = """
        SELECT jd_key, title, COALESCE(company, '') AS company, url,
               COALESCE(description, '') AS description,
               COALESCE(role, '') AS role, COALESCE(role_group, '') AS role_group,
               skills_canonical
        FROM jd_raw
        WHERE description IS NOT NULL AND length(description) >= 200
        ORDER BY posted_date DESC
        LIMIT 2000
    """
    db = SessionLocal()
    try:
        rows = db.execute(text(sql)).fetchall()
    finally:
        db.close()

    if not rows:
        logger.error("No eligible JDs in jd_raw. Run the crawler first.")
        return 1

    logger.info("Loaded %d candidate JDs from DB", len(rows))

    # Group by (lang, role_bucket) for stratified sampling.
    buckets: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        jd_key, title, company, url, description, role, role_group, skills_canonical = r
        lang = detect_lang(description)
        rb = role_bucket(role, role_group, title)
        stratum = f"{lang}-{rb}"
        buckets[stratum].append({
            "jd_key": jd_key,
            "title": title,
            "company": company,
            "url": url,
            "description": description,
            "role": role,
            "role_group": role_group,
            "skills_canonical": list(skills_canonical or []),
            "stratum": stratum,
        })

    logger.info("Distribution across strata:")
    for s in sorted(buckets):
        logger.info("  %-25s %d", s, len(buckets[s]))

    # Proportional allocation by stratum size, with min 1 per non-empty bucket
    # to ensure coverage of rare strata (e.g. Vietnamese-only DevOps).
    total = sum(len(v) for v in buckets.values())
    allocations: dict[str, int] = {}
    remaining = args.n
    for stratum, members in buckets.items():
        share = max(1, round(args.n * len(members) / total))
        allocations[stratum] = min(share, len(members))
        remaining -= allocations[stratum]
    # Adjust to hit exactly args.n
    while remaining != 0:
        # Sort strata by current alloc / population ratio
        sorted_strata = sorted(
            buckets.keys(),
            key=lambda s: allocations[s] / max(len(buckets[s]), 1),
            reverse=(remaining < 0),
        )
        for s in sorted_strata:
            if remaining > 0 and allocations[s] < len(buckets[s]):
                allocations[s] += 1
                remaining -= 1
            elif remaining < 0 and allocations[s] > 1:
                allocations[s] -= 1
                remaining += 1
            if remaining == 0:
                break

    # Sample within each stratum.
    selected: list[dict] = []
    for stratum, n in allocations.items():
        if n <= 0:
            continue
        selected.extend(random.sample(buckets[stratum], n))

    logger.info("\nFinal allocation:")
    for s in sorted(allocations):
        logger.info("  %-25s %d", s, allocations[s])
    logger.info("Total sampled: %d", len(selected))

    # Pre-fill labels with the rule-based extractor.
    with out_path.open("w", encoding="utf-8") as fh:
        for jd in selected:
            pre = rule_extract(
                title=jd["title"],
                description=jd["description"],
                all_skills=jd["skills_canonical"],
            )
            jd["pre_labels"] = {
                "seniority": pre.seniority,
                "min_exp": pre.min_exp,
                "max_exp": pre.max_exp,
                "degree_required": pre.degree_required,
                "work_mode": pre.work_mode,
                "skills_required": pre.skills_required,
                "skills_preferred": pre.skills_preferred,
                # Salary defaults come from the crawler (JSON-LD); we don't
                # have them in this row but the UI can read jd_raw if needed.
            }
            jd["gold_labels"] = None
            fh.write(json.dumps(jd, ensure_ascii=False) + "\n")

    logger.info("Wrote %d JDs to %s", len(selected), out_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
