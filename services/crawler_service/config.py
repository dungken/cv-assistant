"""Crawler Service Configuration."""
import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    service_port: int = int(os.getenv("SERVICE_PORT", "5006"))

    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql://skill_user:skill_password@localhost:5434/skill_data",
    )

    chroma_host: str | None = os.getenv("CHROMA_HOST")
    chroma_port: int = int(os.getenv("CHROMA_PORT", "8000"))
    chroma_collection: str = os.getenv("CHROMA_COLLECTION", "real_jds")

    ner_service_url: str = os.getenv("NER_SERVICE_URL", "http://localhost:5005")
    skill_service_url: str = os.getenv("SKILL_SERVICE_URL", "http://localhost:5002")

    crawl_user_agent: str = (
        "Mozilla/5.0 (compatible; CVAssistantBot/1.0; academic research; "
        "+mailto:research@utc2.edu.vn)"
    )
    crawl_sleep_min_seconds: float = 3.0
    crawl_sleep_max_seconds: float = 6.0
    crawl_max_pages_per_category: int = 50  # enough to cover all ~880 ITviec JDs (~44 pages × 20)
    crawl_max_jds_per_run: int = 1000

    cron_hour: int = 2
    cron_minute: int = 0

    enable_scheduler: bool = os.getenv("ENABLE_SCHEDULER", "true").lower() == "true"

    model_config = {
        "env_file": ".env",
        "extra": "ignore",
    }


settings = Settings()
