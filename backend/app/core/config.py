"""
Core Configuration for the AI Financial Planning System

Configuration management using Pydantic settings with environment variable support.
"""

import os
from typing import List, Optional, Union
from pydantic import BaseSettings, Field, validator
from pydantic.types import SecretStr


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Project Information
    PROJECT_NAME: str = "AI Financial Planning System"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    DESCRIPTION: str = "AI-driven financial planning and simulation system"
    
    # Server Configuration
    HOST: str = Field("0.0.0.0", env="HOST")
    PORT: int = Field(8000, env="PORT")
    RELOAD: bool = Field(False, env="RELOAD")
    WORKERS: int = Field(1, env="WORKERS")
    
    # CORS Configuration
    BACKEND_CORS_ORIGINS: List[str] = Field(
        [
            "http://localhost:3000", 
            "http://localhost:3001", 
            "http://127.0.0.1:3000", 
            "http://127.0.0.1:3001",
            "http://localhost:5173",  # Vite dev server
            "http://127.0.0.1:5173",
            "http://localhost:4173",  # Vite preview
            "http://127.0.0.1:4173",
            "https://ai-financial-planner-zeta.vercel.app",  # Production frontend
            "https://ai-financial-planner-*.vercel.app",  # Preview deployments
            "*"  # Allow all origins for development (remove in strict production)
        ],
        env="BACKEND_CORS_ORIGINS"
    )
    
    # Allowed Hosts
    ALLOWED_HOSTS: List[str] = Field(
        ["localhost", "127.0.0.1", "0.0.0.0"],
        env="ALLOWED_HOSTS"
    )
    
    # Database Configuration
    DATABASE_URL: str = Field(
        "sqlite+aiosqlite:///./financial_planning.db",
        env="DATABASE_URL"
    )
    DATABASE_POOL_SIZE: int = Field(20, env="DATABASE_POOL_SIZE")
    DATABASE_MAX_OVERFLOW: int = Field(30, env="DATABASE_MAX_OVERFLOW")
    DATABASE_POOL_TIMEOUT: int = Field(30, env="DATABASE_POOL_TIMEOUT")
    
    # Redis Configuration
    REDIS_URL: str = Field("redis://localhost:6379", env="REDIS_URL")
    REDIS_PASSWORD: Optional[SecretStr] = Field(None, env="REDIS_PASSWORD")
    REDIS_DB: int = Field(0, env="REDIS_DB")
    
    # Security Configuration
    SECRET_KEY: SecretStr = Field(..., env="SECRET_KEY")
    ALGORITHM: str = Field("HS256", env="ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(7, env="REFRESH_TOKEN_EXPIRE_DAYS")
    
    # Password Security
    MIN_PASSWORD_LENGTH: int = Field(8, env="MIN_PASSWORD_LENGTH")
    PASSWORD_HASH_ROUNDS: int = Field(12, env="PASSWORD_HASH_ROUNDS")
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = Field(60, env="RATE_LIMIT_PER_MINUTE")
    RATE_LIMIT_PER_HOUR: int = Field(1000, env="RATE_LIMIT_PER_HOUR")
    
    # Simulation Configuration
    DEFAULT_MONTE_CARLO_ITERATIONS: int = Field(50_000, env="DEFAULT_MONTE_CARLO_ITERATIONS")
    MAX_MONTE_CARLO_ITERATIONS: int = Field(100_000, env="MAX_MONTE_CARLO_ITERATIONS")
    SIMULATION_TIMEOUT_SECONDS: int = Field(300, env="SIMULATION_TIMEOUT_SECONDS")  # 5 minutes
    MAX_CONCURRENT_SIMULATIONS: int = Field(10, env="MAX_CONCURRENT_SIMULATIONS")
    
    # AI/LLM Configuration
    OPENAI_API_KEY: Optional[SecretStr] = Field(None, env="OPENAI_API_KEY")
    ANTHROPIC_API_KEY: Optional[SecretStr] = Field(None, env="ANTHROPIC_API_KEY")
    DEFAULT_LLM_PROVIDER: str = Field("openai", env="DEFAULT_LLM_PROVIDER")
    LLM_MODEL: str = Field("gpt-4", env="LLM_MODEL")
    LLM_MAX_TOKENS: int = Field(2000, env="LLM_MAX_TOKENS")
    LLM_TEMPERATURE: float = Field(0.7, env="LLM_TEMPERATURE")
    
    # Capital Market Assumptions
    DEFAULT_CMA_VERSION: str = Field("2024.1", env="DEFAULT_CMA_VERSION")
    CMA_UPDATE_FREQUENCY_DAYS: int = Field(90, env="CMA_UPDATE_FREQUENCY_DAYS")
    
    # Audit and Compliance
    AUDIT_LOG_RETENTION_DAYS: int = Field(2555, env="AUDIT_LOG_RETENTION_DAYS")  # 7 years
    COMPLIANCE_DISCLAIMER: str = Field(
        "Simulations are estimates, not guarantees.",
        env="COMPLIANCE_DISCLAIMER"
    )
    REQUIRED_DISCLAIMERS: List[str] = Field(
        ["Simulations are estimates, not guarantees."],
        env="REQUIRED_DISCLAIMERS"
    )
    
    # PDF Export Configuration
    PDF_TEMPLATE_DIR: str = Field("templates/pdf", env="PDF_TEMPLATE_DIR")
    PDF_OUTPUT_DIR: str = Field("exports/pdf", env="PDF_OUTPUT_DIR")
    MAX_PDF_SIZE_MB: int = Field(10, env="MAX_PDF_SIZE_MB")
    
    # Monitoring and Logging
    LOG_LEVEL: str = Field("INFO", env="LOG_LEVEL")
    LOG_FORMAT: str = Field(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        env="LOG_FORMAT"
    )
    SENTRY_DSN: Optional[str] = Field(None, env="SENTRY_DSN")
    ENABLE_METRICS: bool = Field(True, env="ENABLE_METRICS")
    
    # Email Configuration
    SMTP_HOST: Optional[str] = Field(None, env="SMTP_HOST")
    SMTP_PORT: int = Field(587, env="SMTP_PORT")
    SMTP_USERNAME: Optional[str] = Field(None, env="SMTP_USERNAME")
    SMTP_PASSWORD: Optional[SecretStr] = Field(None, env="SMTP_PASSWORD")
    SMTP_TLS: bool = Field(True, env="SMTP_TLS")
    FROM_EMAIL: str = Field("noreply@financialplanner.com", env="FROM_EMAIL")
    
    # Background Tasks
    ENABLE_BACKGROUND_TASKS: bool = Field(True, env="ENABLE_BACKGROUND_TASKS")
    CELERY_BROKER_URL: str = Field("redis://localhost:6379/0", env="CELERY_BROKER_URL")
    CELERY_RESULT_BACKEND: str = Field("redis://localhost:6379/0", env="CELERY_RESULT_BACKEND")
    
    # Banking Integration Configuration
    PLAID_CLIENT_ID: Optional[SecretStr] = Field(None, env="PLAID_CLIENT_ID")
    PLAID_SECRET: Optional[SecretStr] = Field(None, env="PLAID_SECRET")
    PLAID_PUBLIC_KEY: Optional[SecretStr] = Field(None, env="PLAID_PUBLIC_KEY")
    PLAID_ENVIRONMENT: str = Field("sandbox", env="PLAID_ENVIRONMENT")  # sandbox, development, production
    PLAID_WEBHOOK_URL: Optional[str] = Field(None, env="PLAID_WEBHOOK_URL")
    
    # Yodlee Configuration
    YODLEE_BASE_URL: str = Field("https://sandbox.api.yodlee.com/ysl", env="YODLEE_BASE_URL")
    YODLEE_CLIENT_ID: Optional[SecretStr] = Field(None, env="YODLEE_CLIENT_ID")
    YODLEE_SECRET: Optional[SecretStr] = Field(None, env="YODLEE_SECRET")
    YODLEE_ADMIN_LOGIN_NAME: Optional[str] = Field(None, env="YODLEE_ADMIN_LOGIN_NAME")
    
    # Banking Security
    BANKING_ENCRYPTION_KEY: Optional[SecretStr] = Field(None, env="BANKING_ENCRYPTION_KEY")
    BANKING_CREDENTIAL_VAULT_TTL: int = Field(86400, env="BANKING_CREDENTIAL_VAULT_TTL")  # 24 hours
    BANKING_MAX_RETRY_ATTEMPTS: int = Field(3, env="BANKING_MAX_RETRY_ATTEMPTS")
    BANKING_RETRY_DELAY_SECONDS: int = Field(5, env="BANKING_RETRY_DELAY_SECONDS")
    
    # Transaction Processing
    TRANSACTION_SYNC_DAYS: int = Field(30, env="TRANSACTION_SYNC_DAYS")
    TRANSACTION_CATEGORIZATION_CONFIDENCE_THRESHOLD: float = Field(0.8, env="TRANSACTION_CATEGORIZATION_CONFIDENCE_THRESHOLD")
    ENABLE_REAL_TIME_TRANSACTION_SYNC: bool = Field(True, env="ENABLE_REAL_TIME_TRANSACTION_SYNC")
    
    # Cash Flow Analysis
    CASH_FLOW_ANALYSIS_LOOKBACK_MONTHS: int = Field(12, env="CASH_FLOW_ANALYSIS_LOOKBACK_MONTHS")
    SPENDING_PATTERN_ANOMALY_THRESHOLD: float = Field(2.0, env="SPENDING_PATTERN_ANOMALY_THRESHOLD")  # Standard deviations
    
    # Balance Monitoring
    LOW_BALANCE_THRESHOLD_PERCENTAGE: float = Field(0.1, env="LOW_BALANCE_THRESHOLD_PERCENTAGE")  # 10%
    BALANCE_CHECK_FREQUENCY_HOURS: int = Field(6, env="BALANCE_CHECK_FREQUENCY_HOURS")
    
    # Development and Testing
    DEBUG: bool = Field(False, env="DEBUG")
    TESTING: bool = Field(False, env="TESTING")
    ENVIRONMENT: str = Field("production", env="ENVIRONMENT")
    
    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    @validator("ALLOWED_HOSTS", pre=True)
    def assemble_allowed_hosts(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    @validator("REQUIRED_DISCLAIMERS", pre=True)
    def assemble_disclaimers(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Global settings instance
settings = Settings()

# Environment-specific overrides
if settings.ENVIRONMENT == "development":
    settings.DEBUG = True
    settings.RELOAD = True
    settings.LOG_LEVEL = "DEBUG"

if settings.ENVIRONMENT == "testing":
    settings.TESTING = True
    settings.DEBUG = True
    settings.LOG_LEVEL = "DEBUG"