from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    app_name: str = "FastAPI Application"
    debug: bool = False
    database_url: Optional[str] = None
    
    # Knowunity API settings
    knowunity_api_key: str
    knowunity_api_base: str = "https://knowunity-agent-olympics-2026-api.vercel.app"
    
    # OpenAI settings
    openai_api_key: str
    openai_model: str = "gpt-4o-mini"
    
    # Application settings
    log_dir: str = "logs"
    max_conversation_turns: int = 10
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
