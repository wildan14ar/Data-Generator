"""
Application configuration settings
"""

import os
from typing import List, Optional
from functools import lru_cache

from pydantic_settings import BaseSettings
from pydantic import validator


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Project info
    PROJECT_NAME: str = "Datagen API"
    DESCRIPTION: str = "Schema-Aware Data Generator REST API"
    VERSION: str = "1.0.0"
    
    # API settings
    API_STR: str = "/api"
    DEBUG: bool = True
    
    # Security
    SECRET_KEY: str = "your-secret-key-here"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    
    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    RELOAD: bool = True
    
    # CORS settings
    CORS_ORIGINS: List[str] = ["*"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["*"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]
    
    # Security
    ALLOWED_HOSTS: Optional[List[str]] = None
    
    # File settings
    MAX_FILE_SIZE: int = 100 * 1024 * 1024  # 100MB
    TEMP_DIR: str = "temp"
    FILE_CLEANUP_HOURS: int = 1
    
    # Generation limits
    MAX_RECORDS_PER_REQUEST: int = 100000
    MAX_BATCH_SIZE: int = 10000
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    @validator("CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v):
        """Parse CORS origins from string or list."""
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError("Invalid CORS_ORIGINS format")
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()