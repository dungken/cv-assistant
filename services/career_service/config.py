from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Career Service Settings"""
    service_name: str = "career-service"
    service_port: int = 5003
    log_level: str = "INFO"
    
    chroma_path: str = "./knowledge_base/chroma_db"
    onet_path: str = "./knowledge_base/onet/db_28_1_text"
    
    class Config:
        env_prefix = "CAREER_"
        case_sensitive = False

settings = Settings()
