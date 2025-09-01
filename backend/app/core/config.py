"""
Application configuration using Pydantic Settings
"""
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator
import os


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    model_config = SettingsConfigDict(
        env_file=".env.development" if os.getenv("ENV", "development") == "development" else ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )
    
    # Application
    app_name: str = "Financial Portfolio Tracker"
    app_version: str = "1.0.0"
    debug: bool = Field(default=False)
    environment: str = Field(default="development", alias="ENV")
    
    # Database
    database_url: str = Field(
        default="sqlite+aiosqlite:///./test_portfolio.db",
        alias="DATABASE_URL"
    )
    db_echo: bool = Field(default=False)
    db_pool_size: int = Field(default=10)
    db_max_overflow: int = Field(default=20)
    db_pool_timeout: int = Field(default=30)
    
    # Redis
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        alias="REDIS_URL"
    )
    redis_max_connections: int = Field(default=50)
    
    # Security
    secret_key: str = Field(
        default="development_secret_key_change_in_production",
        alias="SECRET_KEY"
    )
    jwt_secret_key: str = Field(
        default="development_jwt_secret_change_in_production",
        alias="JWT_SECRET_KEY"
    )
    jwt_algorithm: str = Field(default="HS256")
    jwt_expiration_hours: int = Field(default=24)
    refresh_token_expiration_days: int = Field(default=30)
    
    # CORS
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173"]
    )
    cors_allow_credentials: bool = Field(default=True)
    cors_allow_methods: List[str] = Field(default=["*"])
    cors_allow_headers: List[str] = Field(default=["*"])
    
    # Security
    allowed_hosts: List[str] = Field(default=["*"])
    
    # API
    api_v1_prefix: str = Field(default="/api/v1")
    rate_limit_per_minute: int = Field(default=100)
    
    # Market Data
    yfinance_cache_ttl_seconds: int = Field(default=60)
    yfinance_max_retries: int = Field(default=3)
    yfinance_retry_delay_seconds: int = Field(default=1)
    yfinance_cache_dir: str = Field(default="/tmp/yfinance_cache")
    
    # Circuit Breaker
    circuit_breaker_failure_threshold: int = Field(default=3)
    circuit_breaker_recovery_timeout: int = Field(default=60)
    circuit_breaker_expected_exception: Optional[str] = Field(default=None)
    
    # Background Jobs
    job_queue_high: str = Field(default="high")
    job_queue_default: str = Field(default="default")
    job_queue_low: str = Field(default="low")
    job_max_retries: int = Field(default=3)
    job_retry_delay_seconds: int = Field(default=60)
    
    # Logging
    log_level: str = Field(default="INFO")
    log_format: str = Field(default="json")
    
    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Ensure database URL is properly formatted"""
        if not v.startswith(("postgresql://", "postgresql+asyncpg://", "sqlite", "sqlite+aiosqlite://")):
            raise ValueError("Database URL must be a PostgreSQL or SQLite connection string")
        return v
    
    @field_validator("redis_url")
    @classmethod
    def validate_redis_url(cls, v: str) -> str:
        """Ensure Redis URL is properly formatted"""
        if not v.startswith("redis://"):
            raise ValueError("Redis URL must start with redis://")
        return v
    
    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Validate environment name"""
        allowed = ["development", "staging", "production", "testing"]
        if v not in allowed:
            raise ValueError(f"Environment must be one of: {allowed}")
        return v
    
    @property
    def is_development(self) -> bool:
        """Check if running in development mode"""
        return self.environment == "development"
    
    @property
    def is_production(self) -> bool:
        """Check if running in production mode"""
        return self.environment == "production"
    
    @property
    def is_testing(self) -> bool:
        """Check if running in test mode"""
        return self.environment == "testing"


# Create global settings instance
settings = Settings()