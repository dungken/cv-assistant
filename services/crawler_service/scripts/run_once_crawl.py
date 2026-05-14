"""Run one full crawl cycle and exit.

Use case: manual daily crawl, or invoked by Linux cron / Windows Task Scheduler
without needing the long-running FastAPI service.

    cd /home/.../cv_assistant
    .venv/bin/python -m services.crawler_service.scripts.run_once_crawl

Crawls ITviec (~850 JDs) + TopCV (top categories), aggregates skill_trends.
"""
import logging
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
    start = time.time()
    total_jds = 0

    # ── ITviec ──
    try:
        result = CrawlPipeline(crawler=ItviecCrawler()).run(
            categories=["all"], max_pages=50, max_jds=1000,
        )
        logger.info("ITviec: status=%s jds=%d", result["status"], result["jd_count"])
        total_jds += result["jd_count"]
    except Exception as e:
        logger.exception("ITviec crawl crashed: %s", e)

    # ── TopCV ──
    try:
        result = CrawlPipeline(crawler=TopCVCrawler()).run(
            categories=["backend", "frontend", "fullstack", "mobile", "data", "ai", "devops"],
            max_pages=3, max_jds=500,
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
