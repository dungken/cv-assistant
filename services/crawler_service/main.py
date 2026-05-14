"""Crawler Service FastAPI entrypoint."""
import logging
import sys
from contextlib import asynccontextmanager
from datetime import datetime, date
from pathlib import Path

import uvicorn
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import FastAPI, HTTPException, Query

# Add project root for `services.crawler_service...` imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from services.crawler_service.config import settings
from services.crawler_service.services.aggregator import aggregate_skill_trends
from services.crawler_service.services.db_session import init_db
from services.crawler_service.services.itviec_crawler import ItviecCrawler
from services.crawler_service.services.topcv_crawler import TopCVCrawler
from services.crawler_service.services.pipeline import CrawlPipeline

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("crawler_service")

scheduler = BackgroundScheduler(timezone="Asia/Ho_Chi_Minh")


# ── pipelines registry — easy to add more sources later ───────────

def _build_pipelines() -> dict[str, CrawlPipeline]:
    return {
        "itviec": CrawlPipeline(crawler=ItviecCrawler()),
        "topcv": CrawlPipeline(crawler=TopCVCrawler()),
    }


def _run_daily_crawl() -> None:
    logger.info("daily crawl tick at %s", datetime.utcnow())
    for name, pipeline in _build_pipelines().items():
        try:
            result = pipeline.run()
            logger.info("source=%s done: %s", name, result)
        except Exception as e:
            logger.exception("source=%s crashed: %s", name, e)
    # Aggregate after all sources crawled
    try:
        aggregate_skill_trends(snapshot_date=date.today(), window_days=7)
    except Exception as e:
        logger.exception("aggregate failed: %s", e)


# ── lifecycle ─────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    if settings.enable_scheduler:
        scheduler.add_job(
            _run_daily_crawl,
            trigger=CronTrigger(hour=settings.cron_hour, minute=settings.cron_minute),
            id="daily_crawl",
            replace_existing=True,
        )
        scheduler.start()
        logger.info("Scheduler started; next run at %02d:%02d Asia/Ho_Chi_Minh",
                    settings.cron_hour, settings.cron_minute)
    yield
    if scheduler.running:
        scheduler.shutdown()


app = FastAPI(title="Crawler Service", version="0.1.0", lifespan=lifespan)


# ── endpoints ─────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "scheduler_running": scheduler.running}


@app.get("/crawler/health-check")
def crawler_health_check(source: str = Query("itviec")):
    """Quick self-test of a source — does its HTML still parse?"""
    pipelines = _build_pipelines()
    pipeline = pipelines.get(source)
    if not pipeline:
        raise HTTPException(404, f"Unknown source: {source}")
    ok = pipeline.crawler.health_check()
    return {"source": source, "healthy": ok}


@app.post("/crawler/trigger")
def trigger_crawl(
    source: str = Query("itviec"),
    categories: str | None = Query(None, description="Comma-separated category keys"),
    max_pages: int = Query(None, ge=1, le=20),
    max_jds: int = Query(None, ge=1, le=1000),
):
    """Manually trigger a crawl (for testing or ad-hoc runs)."""
    pipelines = _build_pipelines()
    pipeline = pipelines.get(source)
    if not pipeline:
        raise HTTPException(404, f"Unknown source: {source}")

    cats = [c.strip() for c in categories.split(",")] if categories else None
    result = pipeline.run(categories=cats, max_pages=max_pages, max_jds=max_jds)
    return result


@app.post("/crawler/aggregate")
def trigger_aggregate(
    snapshot_date: str | None = Query(None, description="YYYY-MM-DD, default today"),
    window_days: int = Query(7, ge=1, le=30),
):
    """Manually trigger skill_trends aggregation."""
    snap = date.fromisoformat(snapshot_date) if snapshot_date else date.today()
    rows = aggregate_skill_trends(snapshot_date=snap, window_days=window_days)
    return {"snapshot_date": snap.isoformat(), "window_days": window_days, "rows_upserted": rows}


if __name__ == "__main__":
    uvicorn.run(
        "services.crawler_service.main:app",
        host="0.0.0.0",
        port=settings.service_port,
        reload=False,
    )
