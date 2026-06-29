from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Application
    APP_NAME: str = "Air Quality Monitoring System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8050
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    
    # Database
    DATABASE_PATH: str = "data/air_quality.db"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_CACHE_TTL: int = 3600  # 1 hour
    
    # OpenAQ API
    OPENAQ_API_BASE_URL: str = "https://api.openaq.org/v3"
    OPENAQ_API_KEY: str = Field(default="", description="OpenAQ API key")
    OPENAQ_RATE_LIMIT: int = 10  # requests per second
    OPENAQ_TIMEOUT: int = 30  # seconds
    
    # Dashboard
    DASH_REFRESH_INTERVAL: int = 300  # 5 minutes
    DASH_QUALITY_STALE_HOURS: int = 24
    
    # Authentication
    SECRET_KEY: str = Field(default="your-secret-key-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Data Export
    EXPORT_MAX_ROWS: int = 100000
    EXPORT_TEMP_DIR: str = "temp/exports"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    
    # WebSocket
    WS_HEARTBEAT_INTERVAL: int = 30
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get settings instance."""
    return settings
