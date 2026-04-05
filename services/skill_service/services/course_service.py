import json
import os
from typing import List, Dict, Optional
from pathlib import Path
import logging
from sqlalchemy.orm import Session

from services.skill_service.models.schemas import Course, LearningPhase, LearningRoadmap
from services.skill_service.models.database import CourseDB, BookmarkDB, ProgressDB
from services.skill_service.services.db_session import SessionLocal, init_db

logger = logging.getLogger(__name__)

# --- Service Implementation ---

class CourseService:
    def __init__(self, courses_data_path: str = None):
        if not courses_data_path:
            courses_data_path = str(Path(__file__).parent.parent / "data" / "courses.json")
        
        self.courses_data_path = courses_data_path
        
        # Initialize DB tables
        init_db()
        
        # Auto-seed if empty
        self._seed_courses()

    def _seed_courses(self):
        """Seed the database from JSON if the course table is empty."""
        db = SessionLocal()
        try:
            if db.query(CourseDB).count() == 0:
                logger.info("Course table empty, seeding from JSON...")
                if os.path.exists(self.courses_data_path):
                    with open(self.courses_data_path, 'r') as f:
                        data = json.load(f)
                        courses_data = data.get("courses", [])
                        for c in courses_data:
                            new_course = CourseDB(
                                id=c["id"],
                                title=c["title"],
                                platform=c["platform"],
                                url=c["url"],
                                rating=c["rating"],
                                duration_hours=c["duration_hours"],
                                price=c["price"],
                                level=c["level"],
                                skills=c["skills"]
                            )
                            db.add(new_course)
                        db.commit()
                        logger.info(f"Seeded {len(courses_data)} courses into Postgres.")
                else:
                    logger.warning(f"Seed file not found at {self.courses_data_path}")
        except Exception as e:
            logger.error(f"Error seeding courses: {e}")
            db.rollback()
        finally:
            db.close()

    def get_recommendations(self, missing_skills: List[str], user_id: str = "default_user") -> List[Course]:
        """Perform recommendation matching directly from PostgreSQL."""
        db = SessionLocal()
        try:
            # 1. Fetch user state
            bookmarks = [b.course_id for b in db.query(BookmarkDB).filter_by(user_id=user_id).all()]
            progress_rows = db.query(ProgressDB).filter_by(user_id=user_id).all()
            progress_map = {p.course_id: p.completion_rate for p in progress_rows}

            # 2. Fetch ALL courses from DB
            all_courses = db.query(CourseDB).all()
            
            missing_lower = [s.lower() for s in missing_skills]
            scored_courses = []
            
            for c_db in all_courses:
                course_skills = [s.lower() for s in (c_db.skills or [])]
                overlap = [s for s in course_skills if s in missing_lower]
                
                if overlap:
                    # Convert DB model to Schema
                    course_obj = Course(
                        id=c_db.id,
                        title=c_db.title,
                        platform=c_db.platform,
                        url=c_db.url,
                        rating=c_db.rating,
                        duration_hours=c_db.duration_hours,
                        price=c_db.price,
                        level=c_db.level,
                        skills=c_db.skills,
                        is_bookmarked=c_db.id in bookmarks,
                        progress=progress_map.get(c_db.id, 0.0)
                    )
                    scored_courses.append((len(overlap), course_obj))
            
            # Sort by overlap count and then rating
            scored_courses.sort(key=lambda x: (-x[0], -x[1].rating))
            return [c for score, c in scored_courses[:8]]
        except Exception as e:
            logger.error(f"Error getting recommendations: {e}")
            return []
        finally:
            db.close()

    def generate_roadmap(self, missing_skills: List[Dict], user_id: str = "default_user") -> LearningRoadmap:
        priority_map = {"high": 0, "medium": 1, "low": 2}
        sorted_skills = sorted(missing_skills, key=lambda x: priority_map.get(x.get("priority", "low"), 2))
        
        phases = []
        current_week = 1
        
        for i in range(0, len(sorted_skills), 2):
            skill_batch = sorted_skills[i:i+2]
            skill_names = [s["skill"] for s in skill_batch]
            relevant_courses = self.get_recommendations(skill_names, user_id=user_id)
            
            phase_courses = relevant_courses[:1]
            est_hours = sum(c.duration_hours for c in phase_courses)
            
            phases.append(LearningPhase(
                phase=f"Phase {len(phases) + 1}",
                weeks=f"{current_week}-{current_week+1}",
                skills=skill_names,
                courses=phase_courses,
                estimated_hours=est_hours
            ))
            current_week += 2
            
        return LearningRoadmap(
            total_weeks=max(0, current_week - 1),
            phases=phases,
            current_progress=0.0
        )

    def toggle_bookmark(self, course_id: str, user_id: str = "default_user") -> bool:
        db = SessionLocal()
        try:
            existing = db.query(BookmarkDB).filter_by(course_id=course_id, user_id=user_id).first()
            if existing:
                db.delete(existing)
                bookmarked = False
            else:
                new_bookmark = BookmarkDB(course_id=course_id, user_id=user_id)
                db.add(new_bookmark)
                bookmarked = True
            db.commit()
            return bookmarked
        finally:
            db.close()

    def update_progress(self, course_id: str, progress: float, user_id: str = "default_user"):
        db = SessionLocal()
        try:
            existing = db.query(ProgressDB).filter_by(course_id=course_id, user_id=user_id).first()
            if existing:
                existing.completion_rate = progress
            else:
                new_progress = ProgressDB(course_id=course_id, user_id=user_id, completion_rate=progress)
                db.add(new_progress)
            db.commit()
            return True
        finally:
            db.close()
