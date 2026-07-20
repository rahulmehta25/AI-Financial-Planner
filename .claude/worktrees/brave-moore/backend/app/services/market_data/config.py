"""
Market Data Configuration

Configuration settings for all market data providers and system components.
"""

from typing import Dict, List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings
from enum import Enum
import os


class DataProvider(str, Enum):
    """Supported market data providers"""
    ALPHA_VANTAGE = "alpha_vantage"
    YAHOO_FINANCE = "yahoo_finance"
    IEX_CLOUD = "iex_cloud"


class MarketDataConfig(BaseSettings):
    """Configuration for market data streaming system"""
    
    # API Keys
    alpha_vantage_api_key: Optional[str] = Field(
        default=None,
        env="ALPHA_VANTAGE_API_KEY",
        description="Alpha Vantage API key"
    )
    
    iex_cloud_api_key: Optional[str] = Field(
        default=None,
        env="IEX_CLOUD_API_KEY", 
        description="IEX Cloud API key"
    )
    
    iex_cloud_sandbox: bool = Field(
        default=True,
        env="IEX_CLOUD_SANDBOX",
        description="Use IEX Cloud sandbox environment"
    )
    
    # Rate Limiting (requests per minute)
    alpha_vantage_rate_limit: int = Field(
        default=5,
        description="Alpha Vantage API rate limit per minute"
    )
    
    yahoo_finance_rate_limit: int = Field(
        default=2000,
        description="Yahoo Finance rate limit per minute"
    )
    
    iex_cloud_rate_limit: int = Field(
        default=100,
        description="IEX Cloud rate limit per minute"
    )
    
    # Redis Configuration
    redis_url: str = Field(
        default="redis://localhost:6379",
        env="REDIS_URL",
        description="Redis connection URL"
    )
    
    # Cache TTL (seconds)
    quote_cache_ttl: int = Field(
        default=60,
        description="Real-time quote cache TTL in seconds"
    )
    
    historical_cache_ttl: int = Field(
        default=3600,
        description="Historical data cache TTL in seconds"
    )
    
    company_info_cache_ttl: int = Field(
        default=86400,
        description="Company info cache TTL in seconds"
    )
    
    # WebSocket Configuration
    websocket_host: str = Field(
        default="localhost",
        env="WEBSOCKET_HOST",
        description="WebSocket server host"
    )
    
    websocket_port: int = Field(
        default=8765,
        env="WEBSOCKET_PORT",
        description="WebSocket server port"
    )
    
    # Provider Priority and Failover
    primary_provider: DataProvider = Field(
        default=DataProvider.YAHOO_FINANCE,
        description="Primary data provider"
    )
    
    fallback_providers: List[DataProvider] = Field(
        default=[DataProvider.IEX_CLOUD, DataProvider.ALPHA_VANTAGE],
        description="Fallback providers in order of preference"
    )
    
    # Data Update Intervals (seconds)
    real_time_update_interval: int = Field(
        default=1,
        description="Real-time data update interval in seconds"
    )
    
    batch_update_interval: int = Field(
        default=30,
        description="Batch update interval in seconds"
    )
    
    # Historical Data Configuration
    max_historical_days: int = Field(
        default=365,
        description="Maximum days of historical data to fetch"
    )
    
    # Alert Configuration
    max_alerts_per_user: int = Field(
        default=50,
        description="Maximum alerts per user"
    )
    
    alert_check_interval: int = Field(
        default=5,
        description="Alert check interval in seconds"
    )
    
    # Logging Configuration
    log_level: str = Field(
        default="INFO",
        env="LOG_LEVEL",
        description="Logging level"
    )
    
    log_file: Optional[str] = Field(
        default=None,
        env="MARKET_DATA_LOG_FILE",
        description="Log file path"
    )
    
    # Database Configuration
    database_url: str = Field(
        default="postgresql://user:password@localhost/financial_planning",
        env="DATABASE_URL",
        description="Database connection URL"
    )
    
    # Performance Configuration
    max_concurrent_requests: int = Field(
        default=10,
        description="Maximum concurrent API requests"
    )
    
    request_timeout: int = Field(
        default=30,
        description="API request timeout in seconds"
    )
    
    # Data Validation
    validate_price_changes: bool = Field(
        default=True,
        description="Enable price change validation"
    )
    
    max_price_change_percent: float = Field(
        default=20.0,
        description="Maximum allowed price change percentage"
    )
    
    class Config:
        env_file = ".env"
        env_prefix = "MARKET_DATA_"


# Global configuration instance
config = MarketDataConfig()


def get_provider_config(provider: DataProvider) -> Dict:
    """Get configuration for a specific provider"""
    
    provider_configs = {
        DataProvider.ALPHA_VANTAGE: {
            "api_key": config.alpha_vantage_api_key,
            "rate_limit": config.alpha_vantage_rate_limit,
            "base_url": "https://www.alphavantage.co/query",
        },
        DataProvider.YAHOO_FINANCE: {
            "rate_limit": config.yahoo_finance_rate_limit,
            "base_url": "https://query1.finance.yahoo.com/v8/finance/chart/",
        },
        DataProvider.IEX_CLOUD: {
            "api_key": config.iex_cloud_api_key,
            "rate_limit": config.iex_cloud_rate_limit,
            "base_url": "https://sandbox-api.iexapis.com/stable/" if config.iex_cloud_sandbox 
                       else "https://cloud.iexapis.com/stable/",
        }
    }
    
    return provider_configs.get(provider, {})