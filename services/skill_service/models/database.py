from datetime import datetime

from sqlalchemy import Column, String, Float, Integer, JSON, DateTime, Index
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class FreshnessHistoryDB(Base):
    """Tuần 11 — append-only history of Freshness Score per (user, role, day).

    Lets the dashboard plot the time-series and lets the alert pipeline diff
    consecutive snapshots to fire skill alerts (per §3.2.5).
    """
    __tablename__ = "skill_freshness_history"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, index=True, nullable=False)
    role = Column(String, nullable=False)
    snapshot_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    score = Column(Float, nullable=False)
    contributions = Column(JSON, default=list)  # serialized SkillContribution[]
    cold_start = Column(Integer, default=0)     # 0/1 bool

    __table_args__ = (
        Index("idx_fresh_user_date", "user_id", "snapshot_date"),
    )


class FreshnessAlertDB(Base):
    """Tuần 11 — fired when score drops materially between snapshots.

    Threshold from §3.2.5: drop > 5 points.
    """
    __tablename__ = "skill_freshness_alerts"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, index=True, nullable=False)
    role = Column(String, nullable=False)
    fired_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    prev_score = Column(Float, nullable=False)
    new_score = Column(Float, nullable=False)
    delta = Column(Float, nullable=False)
    reason = Column(String, default="")  # human-readable summary


class CourseDB(Base):
    """Course Catalog Table"""
    __tablename__ = "skill_courses"
    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    platform = Column(String)
    url = Column(String)
    rating = Column(Float)
    duration_hours = Column(Float)
    price = Column(Float)
    level = Column(String)
    skills = Column(JSON)  # Store skills as JSON array

class BookmarkDB(Base):
    """User Bookmarks Table"""
    __tablename__ = "skill_bookmarks"
    id = Column(Integer, primary_key=True, autoincrement=True)
    course_id = Column(String, index=True)
    user_id = Column(String, index=True)

class ProgressDB(Base):
    """User Course Progress Table"""
    __tablename__ = "skill_course_progress"
    id = Column(Integer, primary_key=True, autoincrement=True)
    course_id = Column(String, index=True)
    user_id = Column(String, index=True)
    completion_rate = Column(Float, default=0.0)
