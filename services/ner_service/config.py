from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """NER Service Settings"""
    service_name: str = "ner-service"
    service_port: int = 5001
    log_level: str = "INFO"
    
    model_path: str = "./models/ner/checkpoint"
    
    class Config:
        env_prefix = "NER_"
        case_sensitive = False

settings = Settings()
