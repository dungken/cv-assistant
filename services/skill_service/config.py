import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Skill Service Settings"""
    service_name: str = "skill-service"
    service_port: int = 5002
    log_level: str = "INFO"
    
    chroma_path: str = "./knowledge_base/chroma_db"
    embedding_model: str = "all-MiniLM-L6-v2"
    similarity_threshold: float = 0.5
    
    class Config:
        env_prefix = "SKILL_"
        case_sensitive = False

settings = Settings()
