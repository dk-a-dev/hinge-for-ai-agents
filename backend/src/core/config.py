from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    # API Settings
    PROJECT_NAME: str = "Agentic Hinge API"
    VERSION: str = "0.1.0"
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/agentic_hinge"
    
    # Redis for Celery
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Pinecone
    PINECONE_API_KEY: Optional[str] = None
    PINECONE_ENV: str = "us-east-1"
    PINECONE_INDEX_NAME: str = "agentic-hinge-index-768"
    
    # LLM Providers
    GROQ_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
