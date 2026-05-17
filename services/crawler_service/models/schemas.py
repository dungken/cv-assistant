"""Pydantic schemas for crawler service."""
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field


class RawJD(BaseModel):
    """JD as crawled from a source — before deduplication and normalization."""

    source: str
    source_id: str
    title: str
    company: Optional[str] = None
    description: str = ""
    skills_raw: list[str] = Field(default_factory=list)
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    salary_currency: Optional[str] = None
    location: Optional[str] = None
    exp_level: Optional[str] = None
    posted_date: date
    url: str
    role_hint: Optional[str] = None  # role inferred from listing badge (preferred over category)


class ProcessedJD(BaseModel):
    """JD after dedup + skill normalization, ready to persist."""

    jd_key: str
    raw: RawJD
    skills_canonical: list[str]
    role: Optional[str] = None         # ITviec slug, e.g. 'data-analyst'
    role_group: Optional[str] = None   # Top-level group
    first_seen: datetime
    last_seen: datetime

    # Tuần 16 — enriched signal from JDParser (None until /parse-jd-text succeeds)
    min_exp: Optional[int] = None
    max_exp: Optional[int] = None
    seniority: Optional[str] = None
    skills_required: list[str] = Field(default_factory=list)
    skills_preferred: list[str] = Field(default_factory=list)
    degree_required: Optional[str] = None
    work_mode: Optional[str] = None
    description_summary: Optional[str] = None
    parsed_at: Optional[datetime] = None
    parse_version: Optional[str] = None

    # Cross-source dedup tracking — shared by records of the same JOB across
    # multiple sources (e.g. same opening on ITviec + TopCV).
    job_group_id: Optional[str] = None


class CrawlerRunResult(BaseModel):
    run_id: str
    source: str
    started_at: datetime
    finished_at: Optional[datetime] = None
    status: str
    jd_count: int = 0
    error_message: Optional[str] = None
