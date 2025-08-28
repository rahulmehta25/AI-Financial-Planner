"""
Core Configuration for the AI Financial Planning System

Configuration management using Pydantic settings with environment variable support.
"""

import os
from typing import List, Optional, Union, Dict, Any
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )
    # Application
    APP_NAME: str = "AI Financial Planner"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 4
    
    # Database
    DATABASE_URL: str = "postgresql://user:pass@localhost/financial_planner"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 30
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    REDIS_POOL_SIZE: int = 10
    
    # JWT
    JWT_SECRET: str = "your-secret-key"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    
    # Market Data APIs
    POLYGON_API_KEY: str = ""
    DATABENTO_API_KEY: str = ""
    ALPHA_VANTAGE_API_KEY: str = ""
    TWELVE_DATA_API_KEY: str = ""
    
    # AI/ML APIs
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    
    # External Services
    PLAID_CLIENT_ID: str = ""
    PLAID_SECRET: str = ""
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    
    # Security
    SECRET_KEY: str = "your-secret-key-here"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Monitoring
    SENTRY_DSN: Optional[str] = None
    DATADOG_API_KEY: Optional[str] = None
    
    # AWS (if using)
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_REGION: str = "us-east-1"
    AWS_S3_BUCKET: Optional[str] = None


# Global settings instance
settings = Settings()

# Feature flags
FEATURE_FLAGS = {
    "advanced_monte_carlo": True,
    "ai_recommendations": True,
    "real_time_monitoring": True,
    "tax_optimization": True,
    "alternative_investments": False,
    "options_trading": False,
    "cryptocurrency": False,
}


def get_settings() -> Settings:
    return settings