"""Tuần 16 — for JD rows that were crawled from listing pages and therefore
have an empty `description`, re-fetch the detail page to capture the full
description, then run JDEnricher to populate the parsed signal columns.

This is the bridge between "old data crawled by listing-only mode" and the
new enrichment pipeline. Once this runs over the existing 1.4k JDs, the
dashboard finally has structured signal (min_exp, seniority, work_mode,
required vs preferred) to surface.

Run:
    PYTHONPATH=. python3 services/crawler_service/scripts/enrich_existing_jds.py \\
        [--limit 50] [--ner-url http://localhost:5005] [--source itviec]
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

from services.crawler_service.services.enricher import JDEnricher
from services.crawler_service.services.itviec_crawler import ItviecCrawler


logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("enrich-existing")


DB_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://skill_user:skill_password@localhost:5434/skill_data",
)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ner-url", default=os.environ.get("NER_SERVICE_URL", "http://localhost:5005"))
    ap.add_argument("--limit", type=int, default=50)
    ap.add_argument("--source", default="itviec", choices=["itviec"],
                    help="only itviec is supported for now (topcv detail pages need separate parser)")
    ap.add_argument("--skip-fetch", action="store_true",
                    help="skip detail-page fetch and only run enricher on rows that already have description")
    args = ap.parse_args()

    engine = create_engine(DB_URL, future=True)
    SessionLocal = sessionmaker(bind=engine, future=True)
    enricher = JDEnricher(ner_url=args.ner_url)

    # Pick rows that have URL + empty description (only itviec for now since
    # we have a working detail-page parser for it).
    sql = """
        SELECT jd_key, url, title, COALESCE(company, '') AS company,
               COALESCE(description, '') AS description
        FROM jd_raw
        WHERE source = :source
          AND url IS NOT NULL
          AND (parsed_at IS NULL OR length(COALESCE(description, '')) < 50)
        ORDER BY posted_date DESC
        LIMIT :lim
    """
    db = SessionLocal()
    try:
        rows = db.execute(text(sql), {"source": args.source, "lim": args.limit}).fetchall()
    finally:
        db.close()

    logger.info("Found %d JD rows to enrich (limit=%d, source=%s)", len(rows), args.limit, args.source)
    if not rows:
        return 0

    # Build the crawler once if we'll fetch.
    crawler = None
    if not args.skip_fetch:
        crawler = ItviecCrawler()

    enriched_ok = 0
    enriched_fail = 0
    fetched_ok = 0
    fetched_fail = 0
    started = time.time()

    db = SessionLocal()
    try:
        for r in rows:
            jd_key, url, title, company, description = r[0], r[1], r[2], r[3], r[4]
            need_fetch = len(description or "") < 50

            if need_fetch and crawler:
                try:
                    detail = crawler.crawl_detail(url)
                except Exception as e:
                    logger.warning("fetch failed %s: %s", jd_key, e)
                    fetched_fail += 1
                    continue
                if not detail or not detail.description:
                    fetched_fail += 1
                    continue
                description = detail.description
                # Save the freshly-fetched description before enriching so the
                # work isn't lost if NER fails next.
                db.execute(text(
                    "UPDATE jd_raw SET description = :d WHERE jd_key = :k"
                ), {"d": description, "k": jd_key})
                db.commit()
                fetched_ok += 1
            elif need_fetch and not crawler:
                # --skip-fetch mode: nothing to do.
                continue

            enriched = enricher.enrich(title=title, company=company, description=description)
            if enriched is None:
                enriched_fail += 1
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
            enriched_ok += 1
            if enriched_ok % 10 == 0:
                db.commit()
                logger.info("  progress: fetched %d/%d, enriched %d/%d (elapsed %.1fs)",
                            fetched_ok, fetched_ok + fetched_fail,
                            enriched_ok, enriched_ok + enriched_fail,
                            time.time() - started)
        db.commit()
    finally:
        db.close()

    elapsed = time.time() - started
    logger.info("Done in %.1fs. fetched ok=%d fail=%d · enriched ok=%d fail=%d",
                elapsed, fetched_ok, fetched_fail, enriched_ok, enriched_fail)
    return 0 if enriched_ok else 1


def _json(obj) -> str:
    import json
    return json.dumps(obj)


if __name__ == "__main__":
    sys.exit(main())
