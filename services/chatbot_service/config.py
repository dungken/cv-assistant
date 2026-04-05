import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Chatbot Service Settings"""
    service_name: str = "chatbot-service"
    service_port: int = 5004
    log_level: str = "INFO"
    
    ollama_url: str = os.getenv("CHAT_OLLAMA_URL", "http://localhost:11434")
    model_name: str = os.getenv("CHAT_MODEL_NAME", "qwen2.5:3b")
    chroma_host: str = os.getenv("CHROMA_HOST", "localhost")
    chroma_port: int = int(os.getenv("CHROMA_PORT", 8000))
    
    # Groq Settings
    groq_api_key: str = "" # Provided via .env or user
    groq_model: str = "llama-3.3-70b-versatile"
    use_groq: bool = os.getenv("CHAT_USE_GROQ", "false").lower() in ("1", "true", "yes", "on")
    
    max_history: int = 10
    ner_url: str = "http://localhost:5001"
    skill_service_url: str = "http://localhost:5002"
    career_service_url: str = "http://localhost:5003"
    api_gateway_url: str = "http://localhost:8081"

    # US-27: User memory storage
    memory_dir: str = os.getenv("CHAT_MEMORY_DIR", "data/user_memory")

    
    model_config = SettingsConfigDict(
        env_prefix="CHAT_",
        case_sensitive=False,
        protected_namespaces=()
    )

settings = Settings()
