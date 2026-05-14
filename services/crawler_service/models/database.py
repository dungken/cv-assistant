"""SQLAlchemy models for crawler service tables."""
from datetime import datetime

from sqlalchemy import (
    Column, String, Integer, Date, DateTime, Text, UniqueConstraint, Index,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class JDRaw(Base):
    """Raw JD crawled from sources (deduplicated by jd_key)."""
    __tablename__ = "jd_raw"

    jd_key = Column(String(16), primary_key=True)
    source = Column(String(32), nullable=False)
    source_id = Column(String(255))
    title = Column(String(512), nullable=False)
    company = Column(String(255))
    description = Column(Text)
    skills_canonical = Column(JSONB, nullable=False, default=list)
    skills_raw = Column(JSONB, default=list)
    salary_min = Column(Integer)
    salary_max = Column(Integer)
    salary_currency = Column(String(8))
    location = Column(String(128))
    exp_level = Column(String(16))
    role = Column(String(128))         # ITviec slug, e.g. 'data-analyst'; longest is 76 chars
    role_group = Column(String(64))    # ITviec top-level group, e.g. 'data_analytics_and_business_intelligence'
    posted_date = Column(Date, nullable=False)
    first_seen = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_seen = Column(DateTime, nullable=False, default=datetime.utcnow)
    url = Column(Text)

    __table_args__ = (
        Index("idx_jd_posted", "posted_date"),
        Index("idx_jd_role", "role"),
    )


class SkillTrend(Base):
    """Daily aggregated skill demand from JD time-series."""
    __tablename__ = "skill_trends"

    id = Column(Integer, primary_key=True, autoincrement=True)
    skill_canonical = Column(String(255), nullable=False)
    snapshot_date = Column(Date, nullable=False)
    window_days = Column(Integer, nullable=False, default=7)
    role = Column(String(128))
    location = Column(String(64))
    demand_count = Column(Integer, nullable=False, default=0)

    __table_args__ = (
        UniqueConstraint(
            "skill_canonical", "snapshot_date", "window_days", "role", "location",
            name="uq_skill_trend",
        ),
        Index("idx_trends_skill_date", "skill_canonical", "snapshot_date"),
    )


class CrawlerLog(Base):
    """Audit log for each crawl run."""
    __tablename__ = "crawler_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(UUID(as_uuid=True), nullable=False)
    source = Column(String(32), nullable=False)
    started_at = Column(DateTime, nullable=False)
    finished_at = Column(DateTime)
    status = Column(String(16), nullable=False)  # success | failed | partial
    jd_count = Column(Integer, default=0)
    error_message = Column(Text)
