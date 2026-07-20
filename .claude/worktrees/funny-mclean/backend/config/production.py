"""
Production Configuration for Financial Planning System

This configuration is optimized for production deployment with:
- Security hardening
- Performance optimization
- Monitoring integration
- High availability settings
- Comprehensive logging
"""

import os
import secrets
from typing import Optional, List
from urllib.parse import quote_plus
from pydantic import BaseSettings, validator
from functools import lru_cache


class ProductionSettings(BaseSettings):
    """Production configuration settings with security and performance optimizations."""
    
    # Environment
    ENV: str = "production"
    DEBUG: bool = False
    TESTING: bool = False
    
    # Application
    APP_NAME: str = "Financial Planner API"
    APP_VERSION: str = "2.0.0"
    API_PREFIX: str = "/api/v1"
    
    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 4
    WORKER_CLASS: str = "uvicorn.workers.UvicornWorker"
    WORKER_CONNECTIONS: int = 1000
    MAX_REQUESTS: int = 1000
    MAX_REQUESTS_JITTER: int = 100
    PRELOAD_APP: bool = True
    TIMEOUT: int = 120
    KEEPALIVE: int = 5
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", secrets.token_urlsafe(32))
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    PASSWORD_MIN_LENGTH: int = 12
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "https://financialplanner.com",
        "https://www.financialplanner.com",
        "https://app.financialplanner.com"
    ]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"]
    CORS_ALLOW_HEADERS: List[str] = [
        "Authorization", "Content-Type", "Accept", "Origin", "User-Agent",
        "Cache-Control", "X-Requested-With", "X-Request-ID"
    ]
    
    # Database Configuration - PostgreSQL
    DB_HOST: str = os.getenv("DB_HOST", "postgresql-service")
    DB_PORT: int = int(os.getenv("DB_PORT", "5432"))
    DB_NAME: str = os.getenv("DB_NAME", "financial_planner")
    DB_USER: str = os.getenv("DB_USER", "financial_planner_user")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 30
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 3600
    DB_POOL_PRE_PING: bool = True
    DB_ECHO: bool = False
    DB_SSL_MODE: str = "require"
    
    # Redis Configuration
    REDIS_HOST: str = os.getenv("REDIS_HOST", "redis-service")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))
    REDIS_PASSWORD: Optional[str] = os.getenv("REDIS_PASSWORD")
    REDIS_SSL: bool = True
    REDIS_MAX_CONNECTIONS: int = 50
    REDIS_RETRY_ON_TIMEOUT: bool = True
    REDIS_SOCKET_CONNECT_TIMEOUT: int = 5
    REDIS_SOCKET_TIMEOUT: int = 5
    
    # Cache Configuration
    CACHE_TTL: int = 3600  # 1 hour default
    CACHE_TTL_SHORT: int = 300  # 5 minutes
    CACHE_TTL_LONG: int = 86400  # 24 hours
    CACHE_PREFIX: str = "fp:prod:"
    ENABLE_CACHE: bool = True
    
    # Celery Configuration
    CELERY_BROKER_URL: str = ""
    CELERY_RESULT_BACKEND: str = ""
    CELERY_TASK_SERIALIZER: str = "json"
    CELERY_RESULT_SERIALIZER: str = "json"
    CELERY_ACCEPT_CONTENT: List[str] = ["json"]
    CELERY_TIMEZONE: str = "UTC"
    CELERY_ENABLE_UTC: bool = True
    CELERY_TASK_ROUTES: dict = {
        "app.tasks.monte_carlo.*": {"queue": "compute"},
        "app.tasks.ml.*": {"queue": "ml"},
        "app.tasks.notifications.*": {"queue": "notifications"},
        "app.tasks.reports.*": {"queue": "reports"}
    }
    CELERY_TASK_TIME_LIMIT: int = 3600  # 1 hour
    CELERY_TASK_SOFT_TIME_LIMIT: int = 3300  # 55 minutes
    
    # Market Data APIs
    POLYGON_API_KEY: Optional[str] = os.getenv("POLYGON_API_KEY")
    DATABENTO_API_KEY: Optional[str] = os.getenv("DATABENTO_API_KEY")
    ALPHA_VANTAGE_API_KEY: Optional[str] = os.getenv("ALPHA_VANTAGE_API_KEY")
    ENABLE_REAL_TIME_DATA: bool = True
    MARKET_DATA_REFRESH_INTERVAL: int = 60  # seconds
    MARKET_DATA_CACHE_DURATION: int = 300  # 5 minutes
    
    # AI/ML Configuration
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY")
    LLM_MODEL: str = "gpt-4-turbo-preview"
    LLM_MAX_TOKENS: int = 4000
    LLM_TEMPERATURE: float = 0.7
    LLM_TIMEOUT: int = 30
    ENABLE_AI_FEATURES: bool = True
    
    # Monte Carlo Configuration
    DEFAULT_SIMULATIONS: int = 10000
    MAX_SIMULATIONS: int = 100000
    MIN_SIMULATIONS: int = 1000
    SIMULATION_BATCH_SIZE: int = 1000
    ENABLE_GPU_ACCELERATION: bool = True
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 60  # seconds
    RATE_LIMIT_BURST: int = 20
    
    # Monitoring and Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    LOG_FILE: Optional[str] = "/app/logs/app.log"
    LOG_ROTATION: str = "1 day"
    LOG_RETENTION: str = "30 days"
    ENABLE_STRUCTURED_LOGGING: bool = True
    
    # Metrics and Health Checks
    ENABLE_METRICS: bool = True
    METRICS_PORT: int = 9090
    METRICS_PATH: str = "/metrics"
    HEALTH_CHECK_INTERVAL: int = 30
    ENABLE_PROFILING: bool = False
    
    # Sentry Configuration
    SENTRY_DSN: Optional[str] = os.getenv("SENTRY_DSN")
    SENTRY_TRACES_SAMPLE_RATE: float = 0.1
    SENTRY_ENVIRONMENT: str = "production"
    
    # AWS Configuration
    AWS_REGION: str = os.getenv("AWS_REGION", "us-east-1")
    AWS_ACCESS_KEY_ID: Optional[str] = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY: Optional[str] = os.getenv("AWS_SECRET_ACCESS_KEY")
    
    # S3 Configuration
    S3_BUCKET_DOCUMENTS: str = os.getenv("S3_BUCKET_DOCUMENTS", "financial-planner-documents-prod")
    S3_BUCKET_BACKUPS: str = os.getenv("S3_BUCKET_BACKUPS", "financial-planner-backups-prod")
    S3_BUCKET_ML_MODELS: str = os.getenv("S3_BUCKET_ML_MODELS", "financial-planner-ml-models")
    
    # Email Configuration (SES)
    EMAIL_BACKEND: str = "ses"
    EMAIL_FROM: str = "noreply@financialplanner.com"
    EMAIL_FROM_NAME: str = "Financial Planner"
    SES_REGION: str = "us-east-1"
    
    # Feature Flags
    ENABLE_BETA_FEATURES: bool = False
    ENABLE_ADVANCED_ANALYTICS: bool = True
    ENABLE_PDF_EXPORT: bool = True
    ENABLE_WEBSOCKET: bool = True
    ENABLE_BACKUP: bool = True
    ENABLE_ALERTING: bool = True
    
    # Performance Configuration
    MAX_CONNECTIONS: int = 100
    CONNECTION_TIMEOUT: int = 30
    REQUEST_TIMEOUT: int = 60
    RESPONSE_TIMEOUT: int = 60
    
    # Backup Configuration
    BACKUP_ENABLED: bool = True
    BACKUP_INTERVAL_HOURS: int = 6
    BACKUP_RETENTION_DAYS: int = 30
    
    # Security Headers
    SECURITY_HEADERS: dict = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:; connect-src 'self' https:; frame-ancestors 'none';"
    }
    
    # WebSocket Configuration
    WEBSOCKET_ENABLED: bool = True
    WEBSOCKET_MAX_CONNECTIONS: int = 1000
    WEBSOCKET_HEARTBEAT_INTERVAL: int = 30
    
    # Third-party Integrations
    PLAID_CLIENT_ID: Optional[str] = os.getenv("PLAID_CLIENT_ID")
    PLAID_SECRET: Optional[str] = os.getenv("PLAID_SECRET")
    PLAID_ENVIRONMENT: str = "production"
    
    @validator("CELERY_BROKER_URL", pre=True, always=True)
    def build_celery_broker_url(cls, v, values):
        if v:
            return v
        return cls._build_redis_url(values, db=1)
    
    @validator("CELERY_RESULT_BACKEND", pre=True, always=True)
    def build_celery_result_backend(cls, v, values):
        if v:
            return v
        return cls._build_redis_url(values, db=2)
    
    @staticmethod
    def _build_redis_url(values: dict, db: int = 0) -> str:
        """Build Redis connection URL."""
        host = values.get("REDIS_HOST", "redis-service")
        port = values.get("REDIS_PORT", 6379)
        password = values.get("REDIS_PASSWORD")
        ssl_param = "?ssl=true&ssl_cert_reqs=required" if values.get("REDIS_SSL", True) else ""
        
        if password:
            return f"redis://:{quote_plus(password)}@{host}:{port}/{db}{ssl_param}"
        else:
            return f"redis://{host}:{port}/{db}{ssl_param}"
    
    @property
    def database_url(self) -> str:
        """Build database connection URL."""
        password_encoded = quote_plus(self.DB_PASSWORD) if self.DB_PASSWORD else ""
        return (
            f"postgresql://{self.DB_USER}:{password_encoded}@"
            f"{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
            f"?sslmode={self.DB_SSL_MODE}"
        )
    
    @property
    def redis_url(self) -> str:
        """Build Redis connection URL."""
        return self._build_redis_url(self.__dict__, self.REDIS_DB)
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.ENV.lower() == "production"
    
    @property
    def database_config(self) -> dict:
        """Database configuration for SQLAlchemy."""
        return {
            "url": self.database_url,
            "pool_size": self.DB_POOL_SIZE,
            "max_overflow": self.DB_MAX_OVERFLOW,
            "pool_timeout": self.DB_POOL_TIMEOUT,
            "pool_recycle": self.DB_POOL_RECYCLE,
            "pool_pre_ping": self.DB_POOL_PRE_PING,
            "echo": self.DB_ECHO
        }
    
    @property
    def redis_config(self) -> dict:
        """Redis configuration for connection pool."""
        return {
            "host": self.REDIS_HOST,
            "port": self.REDIS_PORT,
            "db": self.REDIS_DB,
            "password": self.REDIS_PASSWORD,
            "ssl": self.REDIS_SSL,
            "max_connections": self.REDIS_MAX_CONNECTIONS,
            "retry_on_timeout": self.REDIS_RETRY_ON_TIMEOUT,
            "socket_connect_timeout": self.REDIS_SOCKET_CONNECT_TIMEOUT,
            "socket_timeout": self.REDIS_SOCKET_TIMEOUT
        }
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_production_settings() -> ProductionSettings:
    """Get cached production settings instance."""
    return ProductionSettings()


# Export settings instance
settings = get_production_settings()

# Logging configuration
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        },
        "json": {
            "format": "%(asctime)s %(name)s %(levelname)s %(message)s",
            "class": "pythonjsonlogger.jsonlogger.JsonFormatter"
        },
    },
    "handlers": {
        "default": {
            "formatter": "json" if settings.LOG_FORMAT == "json" else "default",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
        },
        "file": {
            "formatter": "json" if settings.LOG_FORMAT == "json" else "default",
            "class": "logging.handlers.TimedRotatingFileHandler",
            "filename": settings.LOG_FILE,
            "when": "midnight",
            "interval": 1,
            "backupCount": 30,
            "encoding": "utf8",
        } if settings.LOG_FILE else {
            "formatter": "json" if settings.LOG_FORMAT == "json" else "default",
            "class": "logging.NullHandler",
        },
    },
    "loggers": {
        "": {
            "handlers": ["default", "file"],
            "level": settings.LOG_LEVEL,
        },
        "uvicorn": {
            "handlers": ["default"],
            "level": "INFO",
            "propagate": False,
        },
        "uvicorn.error": {
            "handlers": ["default"],
            "level": "INFO",
            "propagate": False,
        },
        "uvicorn.access": {
            "handlers": ["default"],
            "level": "INFO",
            "propagate": False,
        },
        "sqlalchemy.engine": {
            "handlers": ["default", "file"],
            "level": "WARNING",
            "propagate": False,
        },
        "celery": {
            "handlers": ["default", "file"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

# Celery configuration
CELERY_CONFIG = {
    "broker_url": settings.CELERY_BROKER_URL,
    "result_backend": settings.CELERY_RESULT_BACKEND,
    "task_serializer": settings.CELERY_TASK_SERIALIZER,
    "result_serializer": settings.CELERY_RESULT_SERIALIZER,
    "accept_content": settings.CELERY_ACCEPT_CONTENT,
    "timezone": settings.CELERY_TIMEZONE,
    "enable_utc": settings.CELERY_ENABLE_UTC,
    "task_routes": settings.CELERY_TASK_ROUTES,
    "task_time_limit": settings.CELERY_TASK_TIME_LIMIT,
    "task_soft_time_limit": settings.CELERY_TASK_SOFT_TIME_LIMIT,
    "worker_prefetch_multiplier": 1,
    "worker_max_tasks_per_child": 1000,
    "task_acks_late": True,
    "worker_disable_rate_limits": False,
    "task_compression": "gzip",
    "result_compression": "gzip",
    "task_track_started": True,
    "result_expires": 3600,
}