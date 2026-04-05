from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    """Career Service Settings"""
    service_name: str = "career-service"
    service_port: int = 5003
    log_level: str = "INFO"
    
    chroma_host: str = os.getenv("CHROMA_HOST", "localhost")
    chroma_port: int = int(os.getenv("CHROMA_PORT", 8000))
    onet_path: str = "./knowledge_base/onet/db_28_1_text"
    
    class Config:
        env_prefix = "CAREER_"
        case_sensitive = False

settings = Settings()
