import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from services.skill_service.config import settings
from services.skill_service.models.database import Base

logger = logging.getLogger(__name__)

# Create Engine
engine = create_engine(settings.database_url)

# Session Factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Initialize Postgres tables."""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Skill Service Database initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")

def get_db():
    """FastAPI Dependency for database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
