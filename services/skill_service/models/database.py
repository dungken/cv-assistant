from sqlalchemy import Column, String, Float, Integer, JSON
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

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
