"""SQLAlchemy models for crawler service tables."""
from datetime import datetime

from sqlalchemy import (
    Column, String, Integer, Date, DateTime, Text, UniqueConstraint, Index,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class JDRaw(Base):
    """Raw JD crawled from sources (deduplicated by jd_key).

    Tuần 16 enrichment: in addition to the basic crawler fields, we run each
    JD through `JDParser` (NER service) and store structured signal so the
    matching/learning-path/freshness layers can use real-world constraints —
    not just skill set overlap.
    """
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
    exp_level = Column(String(16))        # raw level slug from crawler (e.g. 'senior')
    role = Column(String(128))            # ITviec slug, e.g. 'data-analyst'
    role_group = Column(String(64))       # ITviec top-level group
    posted_date = Column(Date, nullable=False)
    first_seen = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_seen = Column(DateTime, nullable=False, default=datetime.utcnow)
    url = Column(Text)

    # ── Tuần 16: parsed signals (filled by JDParser after crawl) ────────────
    min_exp = Column(Integer)                          # years
    max_exp = Column(Integer)                          # years
    seniority = Column(String(16))                     # junior | mid | senior | lead
    skills_required = Column(JSONB, default=list)      # blocker skills (must have)
    skills_preferred = Column(JSONB, default=list)     # nice-to-have skills
    degree_required = Column(String(64))               # Bachelor / Master / None
    work_mode = Column(String(16))                     # onsite | hybrid | remote | None
    description_summary = Column(Text)                 # 2-3 sentence summary
    parsed_at = Column(DateTime)                       # when JDParser ran; NULL = not yet
    parse_version = Column(String(16))                 # bump when parser changes

    # ── Cross-source dedup tracking ─────────────────────────────────────────
    # Records sharing the same (company, title) across multiple sources
    # share a job_group_id. Use COUNT(DISTINCT job_group_id) for "unique JOBs"
    # and COUNT(*) for "unique listings".
    job_group_id = Column(String(16))

    __table_args__ = (
        Index("idx_jd_posted", "posted_date"),
        Index("idx_jd_role", "role"),
        Index("idx_jd_seniority", "seniority"),
        Index("idx_jd_parsed", "parsed_at"),
        Index("idx_jd_group", "job_group_id"),
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
