from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """NER Service Settings"""
    service_name: str = "ner-service"
    service_port: int = 5001
    log_level: str = "INFO"
    
    model_path: str = "../../models/ner/final"
    jd_model_path: str = "../../models/ner/jd_final"
    
    # LLM Refinement (Elite Phase)
    ollama_url: str = "http://localhost:11434/api/generate"
    enable_llm_refinement: bool = True
    
    model_config = SettingsConfigDict(
        env_prefix="NER_",
        case_sensitive=False,
        protected_namespaces=()
    )

settings = Settings()
