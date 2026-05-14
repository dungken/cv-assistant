"""Run one full crawl cycle and exit.

Use case: manual daily crawl, or invoked by Linux cron / Windows Task Scheduler
without needing the long-running FastAPI service.

    cd /home/.../cv_assistant
    .venv/bin/python -m services.crawler_service.scripts.run_once_crawl

Crawls ITviec (~850 JDs) + TopCV (top categories), aggregates skill_trends.
"""
import argparse
import logging
import os
import sys
import time
from datetime import date
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from services.crawler_service.services.aggregator import aggregate_skill_trends
from services.crawler_service.services.itviec_crawler import ItviecCrawler
from services.crawler_service.services.pipeline import CrawlPipeline
from services.crawler_service.services.topcv_crawler import TopCVCrawler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--fetch-details",
        action="store_true",
        default=os.environ.get("CRAWL_FETCH_DETAILS", "").lower() in {"1", "true", "yes"},
        help=(
            "Follow every listing URL into its detail page. Adds ~1 HTTP per "
            "JD (~30-60 min for full crawl) but captures the `description` "
            "field needed by JDEnricher → NER. Without this flag the crawler "
            "stays in fast listing-only mode."
        ),
    )
    ap.add_argument("--max-jds-itviec", type=int, default=1000)
    ap.add_argument("--max-jds-topcv", type=int, default=500)
    ap.add_argument(
        "--enrich-inline",
        action="store_true",
        help=(
            "Call NER inline as each JD is processed. Off by default — prefer "
            "running `scripts/backfill_jd_enrichment.py` after the crawl so "
            "the crawler stays decoupled from NER uptime."
        ),
    )
    ap.add_argument(
        "--use-llm",
        action="store_true",
        default=os.environ.get("CRAWL_USE_LLM", "").lower() in {"1", "true", "yes"},
        help=(
            "Call Groq LLM inline to enrich semantic fields (seniority, "
            "min/max_exp, degree, required vs preferred skills, fallback salary). "
            "Requires CHAT_GROQ_API_KEY in env."
        ),
    )
    args = ap.parse_args()

    if args.fetch_details:
        logger.info("Running in detail-fetch mode — captures `description` for enrichment.")
    if args.enrich_inline:
        logger.info("Inline NER enrichment ENABLED — make sure NER service is reachable.")
    if args.use_llm:
        logger.info("Groq LLM enrichment ENABLED — ensure CHAT_GROQ_API_KEY is set.")

    start = time.time()
    total_jds = 0

    # ── ITviec ──
    try:
        result = CrawlPipeline(
            crawler=ItviecCrawler(),
            fetch_details=args.fetch_details,
            enrich_inline=args.enrich_inline,
            use_llm=args.use_llm,
        ).run(
            categories=["all"], max_pages=50, max_jds=args.max_jds_itviec,
        )
        logger.info("ITviec: status=%s jds=%d", result["status"], result["jd_count"])
        total_jds += result["jd_count"]
    except Exception as e:
        logger.exception("ITviec crawl crashed: %s", e)

    # ── TopCV ──
    try:
        result = CrawlPipeline(
            crawler=TopCVCrawler(),
            fetch_details=args.fetch_details,
            enrich_inline=args.enrich_inline,
            use_llm=args.use_llm,
        ).run(
            categories=["backend", "frontend", "fullstack", "mobile", "data", "ai", "devops"],
            max_pages=3, max_jds=args.max_jds_topcv,
        )
        logger.info("TopCV: status=%s jds=%d", result["status"], result["jd_count"])
        total_jds += result["jd_count"]
    except Exception as e:
        logger.exception("TopCV crawl crashed: %s", e)

    # ── Aggregate ──
    try:
        rows = aggregate_skill_trends(snapshot_date=date.today(), window_days=7)
        logger.info("Aggregated skill_trends: %d rows", rows)
    except Exception as e:
        logger.exception("Aggregate failed: %s", e)

    logger.info("DONE: total %d JDs in %.1fs", total_jds, time.time() - start)


if __name__ == "__main__":
    main()
