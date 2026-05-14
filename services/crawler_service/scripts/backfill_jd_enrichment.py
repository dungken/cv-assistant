"""Tuần 16 — re-parse description for jd_raw rows that haven't been
enriched yet (parsed_at IS NULL or parse_version != current).

Run:
    PYTHONPATH=. python3 services/crawler_service/scripts/backfill_jd_enrichment.py
        [--limit N] [--ner-url http://localhost:5005] [--dry-run]
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from services.crawler_service.services.enricher import JDEnricher, PARSE_VERSION


logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("backfill")


DB_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://skill_user:skill_password@localhost:5434/skill_data",
)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ner-url", default=os.environ.get("NER_SERVICE_URL", "http://localhost:5005"))
    ap.add_argument("--limit", type=int, default=200, help="max rows per run")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--reparse-all", action="store_true",
                    help="re-parse even rows already at the current parse_version")
    args = ap.parse_args()

    engine = create_engine(DB_URL, future=True)
    SessionLocal = sessionmaker(bind=engine, future=True)
    enricher = JDEnricher(ner_url=args.ner_url)

    where = "parsed_at IS NULL OR parse_version IS NULL OR parse_version <> :v" \
        if not args.reparse_all else "TRUE"
    sql = f"""
        SELECT jd_key, title, COALESCE(company, '') AS company, description
        FROM jd_raw
        WHERE description IS NOT NULL AND length(description) >= 50
          AND ({where})
        ORDER BY posted_date DESC
        LIMIT :lim
    """

    db = SessionLocal()
    try:
        rows = db.execute(text(sql), {"v": PARSE_VERSION, "lim": args.limit}).fetchall()
    finally:
        db.close()

    logger.info("Found %d JD rows to backfill (limit=%d)", len(rows), args.limit)
    if args.dry_run:
        for r in rows[:5]:
            logger.info("  would parse %s: %s", r[0], r[1][:60])
        return 0

    ok = 0
    fail = 0
    started = time.time()
    db = SessionLocal()
    try:
        for r in rows:
            jd_key, title, company, description = r[0], r[1], r[2], r[3]
            enriched = enricher.enrich(title=title, company=company, description=description)
            if enriched is None:
                fail += 1
                continue
            db.execute(text("""
                UPDATE jd_raw SET
                    min_exp = :min_exp,
                    max_exp = :max_exp,
                    seniority = :seniority,
                    skills_required = CAST(:skills_required AS JSONB),
                    skills_preferred = CAST(:skills_preferred AS JSONB),
                    degree_required = :degree_required,
                    work_mode = :work_mode,
                    description_summary = :description_summary,
                    parsed_at = :parsed_at,
                    parse_version = :parse_version
                WHERE jd_key = :jd_key
            """), {
                "min_exp": enriched.min_exp,
                "max_exp": enriched.max_exp,
                "seniority": enriched.seniority,
                "skills_required": _json(enriched.skills_required),
                "skills_preferred": _json(enriched.skills_preferred),
                "degree_required": enriched.degree_required,
                "work_mode": enriched.work_mode,
                "description_summary": enriched.description_summary,
                "parsed_at": datetime.utcnow(),
                "parse_version": enriched.parse_version,
                "jd_key": jd_key,
            })
            ok += 1
            if ok % 20 == 0:
                db.commit()
                logger.info("  progress: %d ok / %d fail (elapsed %.1fs)", ok, fail, time.time() - started)
        db.commit()
    finally:
        db.close()

    elapsed = time.time() - started
    logger.info("Done: %d enriched, %d failed in %.1fs (%.2f s/jd)",
                ok, fail, elapsed, elapsed / max(ok + fail, 1))
    return 0 if ok else 1


def _json(obj) -> str:
    import json
    return json.dumps(obj)


if __name__ == "__main__":
    sys.exit(main())
