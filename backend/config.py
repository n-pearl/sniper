from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/sniper"
    POSTGRES_DB: str = "sniper"
    POSTGRES_USER: str = "user"
    POSTGRES_PASSWORD: str = "password"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    
    # API Keys
    ALPHA_VANTAGE_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    
    # Redis (for caching and Celery)
    REDIS_URL: str = "redis://localhost:6379"
    
    # App Settings
    APP_NAME: str = "Sniper News Intelligence"
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"
    
    # Sentiment Analysis
    SENTIMENT_BATCH_SIZE: int = 10
    FINBERT_MODEL_NAME: str = "ProsusAI/finbert"
    
    # News Processing
    NEWS_UPDATE_INTERVAL: int = 300  # 5 minutes
    MAX_ARTICLES_PER_REQUEST: int = 100
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
