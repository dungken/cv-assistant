from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Chatbot Service Settings"""
    service_name: str = "chatbot-service"
    service_port: int = 5004
    log_level: str = "INFO"
    
    ollama_url: str = "http://localhost:11434"
    model_name: str = "llama3.2:1b"
    chroma_path: str = "./knowledge_base/chroma_db"
    
    max_history: int = 10
    ner_url: str = "http://localhost:5001"
    skill_service_url: str = "http://localhost:5002"
    career_service_url: str = "http://localhost:5003"

    
    class Config:
        env_prefix = "CHAT_"
        case_sensitive = False

settings = Settings()
