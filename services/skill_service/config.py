import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Skill Service Settings"""
    service_name: str = "skill-service"
    service_port: int = 5002
    log_level: str = "INFO"
    
    chroma_host: str = os.getenv("CHROMA_HOST", "localhost")
    chroma_port: int = int(os.getenv("CHROMA_PORT", 8000))
    ner_service_url: str = os.getenv("NER_SERVICE_URL", "http://localhost:5001/extract")
    database_url: str = os.getenv("DATABASE_URL", "postgresql://skill_user:skill_password@localhost:5434/skill_data")
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

    
    class Config:
        env_prefix = "SKILL_"
        case_sensitive = False

settings = Settings()
