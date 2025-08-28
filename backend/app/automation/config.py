"""
Daily Operations Configuration

Configuration settings and constants for daily operations automation.
"""

from datetime import time
from typing import Dict, Any, List
from enum import Enum
import pytz

# Market timezone
MARKET_TIMEZONE = pytz.timezone('US/Eastern')

# Market hours configuration
MARKET_HOURS = {
    "pre_market_start": time(4, 0),      # 4:00 AM ET
    "market_open": time(9, 30),          # 9:30 AM ET
    "market_close": time(16, 0),         # 4:00 PM ET
    "after_hours_end": time(20, 0)       # 8:00 PM ET
}

# Operation schedules
OPERATION_SCHEDULES = {
    "pre_market": {
        "hour": 4,
        "minute": 0,
        "timezone": MARKET_TIMEZONE
    },
    "market_open": {
        "hour": 9,
        "minute": 30,
        "timezone": MARKET_TIMEZONE
    },
    "mid_day": {
        "hour": 12,
        "minute": 0,
        "timezone": MARKET_TIMEZONE
    },
    "market_close": {
        "hour": 16,
        "minute": 0,
        "timezone": MARKET_TIMEZONE
    },
    "post_market": {
        "hour": 18,
        "minute": 0,
        "timezone": MARKET_TIMEZONE
    }
}

# Task configuration
TASK_CONFIG = {
    "max_concurrent_tasks": 10,
    "task_timeout": 300,  # 5 minutes
    "max_retries": 3,
    "retry_delay": 30,    # 30 seconds
    "health_check_interval": 60,  # 1 minute
    "system_monitor_interval": 30,  # 30 seconds
}

# Alert thresholds
ALERT_THRESHOLDS = {
    "task_failure_rate": 0.15,      # 15% failure rate
    "system_memory_usage": 0.85,    # 85% memory usage
    "system_cpu_usage": 0.80,       # 80% CPU usage
    "database_connection_pool": 0.90, # 90% connection pool usage
    "api_response_time": 2.0,       # 2 second response time
    "disk_usage": 0.85,             # 85% disk usage
    "portfolio_drift": 0.05,        # 5% drift from target allocation
    "var_breach": 1.5,              # 1.5x normal VaR
    "drawdown_limit": 0.10          # 10% drawdown limit
}

# Risk monitoring configuration
RISK_CONFIG = {
    "var_confidence_levels": [0.95, 0.99],
    "var_time_horizons": [1, 5, 22],  # 1 day, 1 week, 1 month
    "stress_test_scenarios": [
        "market_crash_2008",
        "covid_march_2020",
        "flash_crash_2010",
        "interest_rate_shock",
        "currency_crisis"
    ],
    "position_limit_checks": [
        "single_position_limit",
        "sector_concentration",
        "country_exposure",
        "currency_exposure",
        "liquidity_requirements"
    ]
}

# Performance tracking
PERFORMANCE_CONFIG = {
    "benchmark_symbols": ["SPY", "AGG", "VTI", "VXUS"],
    "performance_periods": [1, 7, 30, 90, 365],  # days
    "attribution_factors": [
        "asset_allocation",
        "security_selection",
        "timing",
        "currency",
        "fees"
    ],
    "metrics_to_calculate": [
        "total_return",
        "sharpe_ratio",
        "sortino_ratio",
        "max_drawdown",
        "calmar_ratio",
        "information_ratio",
        "treynor_ratio",
        "alpha",
        "beta",
        "tracking_error"
    ]
}

# Tax optimization settings
TAX_CONFIG = {
    "harvest_minimum_loss": 100,      # Minimum $100 loss to harvest
    "harvest_minimum_days": 31,       # Avoid wash sale rule
    "short_term_rate": 0.37,          # 37% short-term capital gains
    "long_term_rate": 0.20,           # 20% long-term capital gains
    "rebalancing_tax_budget": 0.005,  # 0.5% of portfolio value for tax impact
    "asset_location_preferences": {
        "tax_deferred": ["bonds", "reits", "high_dividend_stocks"],
        "tax_free": ["growth_stocks", "international_stocks"],
        "taxable": ["tax_managed_funds", "municipal_bonds", "index_funds"]
    }
}

# Data quality thresholds
DATA_QUALITY_CONFIG = {
    "price_change_threshold": 0.20,    # 20% price change flag
    "volume_anomaly_threshold": 3.0,   # 3x average volume
    "missing_data_threshold": 0.05,    # 5% missing data tolerance
    "stale_data_threshold": 3600,      # 1 hour stale data limit (seconds)
    "data_sources_required": 2,        # Minimum data sources for validation
    "confidence_score_threshold": 0.8  # 80% confidence score minimum
}

# Notification settings
NOTIFICATION_CONFIG = {
    "critical_alerts": {
        "channels": ["email", "sms", "push"],
        "recipients": ["admin", "operations"],
        "escalation_timeout": 300  # 5 minutes
    },
    "high_priority": {
        "channels": ["email", "push"],
        "recipients": ["admin"],
        "escalation_timeout": 900  # 15 minutes
    },
    "medium_priority": {
        "channels": ["email"],
        "recipients": ["admin"],
        "escalation_timeout": 1800  # 30 minutes
    },
    "low_priority": {
        "channels": ["in_app"],
        "recipients": ["admin"],
        "escalation_timeout": 3600  # 1 hour
    }
}

# Backup and archival settings
BACKUP_CONFIG = {
    "daily_backup_time": time(2, 0),   # 2:00 AM
    "retention_periods": {
        "daily": 7,    # 7 days
        "weekly": 4,   # 4 weeks  
        "monthly": 12, # 12 months
        "yearly": 7    # 7 years
    },
    "backup_types": [
        "database_full",
        "database_incremental", 
        "config_files",
        "log_files",
        "user_data"
    ],
    "compression_enabled": True,
    "encryption_enabled": True
}

# API rate limiting
API_RATE_LIMITS = {
    "market_data": {
        "requests_per_minute": 60,
        "requests_per_hour": 1000,
        "requests_per_day": 10000
    },
    "banking": {
        "requests_per_minute": 30,
        "requests_per_hour": 500,
        "requests_per_day": 2000
    },
    "notifications": {
        "requests_per_minute": 100,
        "requests_per_hour": 2000,
        "requests_per_day": 20000
    }
}

# Market calendar settings
MARKET_CALENDAR = {
    "trading_days": [0, 1, 2, 3, 4],  # Monday to Friday
    "holidays": [
        "New Year's Day",
        "Martin Luther King Jr. Day", 
        "Presidents Day",
        "Good Friday",
        "Memorial Day",
        "Juneteenth",
        "Independence Day",
        "Labor Day",
        "Thanksgiving Day",
        "Christmas Day"
    ],
    "early_close_days": [
        "Black Friday",
        "Christmas Eve",
        "New Year's Eve"
    ]
}

# System health monitoring
HEALTH_MONITORING = {
    "check_intervals": {
        "critical_services": 30,    # 30 seconds
        "database": 60,             # 1 minute  
        "external_apis": 120,       # 2 minutes
        "system_resources": 60,     # 1 minute
        "disk_space": 300           # 5 minutes
    },
    "service_dependencies": {
        "market_data": ["database", "redis", "external_api"],
        "portfolio": ["database", "market_data", "risk_engine"],
        "notifications": ["database", "smtp", "push_service"],
        "risk_engine": ["database", "market_data", "ml_models"],
        "tax_service": ["database", "portfolio", "market_data"]
    },
    "recovery_procedures": {
        "database_connection_lost": "restart_connection_pool",
        "external_api_timeout": "switch_to_backup_provider",
        "high_memory_usage": "restart_background_tasks",
        "disk_space_low": "cleanup_old_files"
    }
}

# Environment-specific configurations
ENVIRONMENT_CONFIGS = {
    "development": {
        "task_timeout": 30,
        "max_retries": 1,
        "health_check_interval": 300,
        "log_level": "DEBUG"
    },
    "staging": {
        "task_timeout": 120,
        "max_retries": 2,
        "health_check_interval": 120,
        "log_level": "INFO"
    },
    "production": {
        "task_timeout": 300,
        "max_retries": 3,
        "health_check_interval": 60,
        "log_level": "WARNING"
    }
}

def get_config_for_environment(env: str = "production") -> Dict[str, Any]:
    """Get configuration for specific environment"""
    base_config = {
        "task_config": TASK_CONFIG,
        "alert_thresholds": ALERT_THRESHOLDS,
        "risk_config": RISK_CONFIG,
        "performance_config": PERFORMANCE_CONFIG,
        "tax_config": TAX_CONFIG,
        "data_quality_config": DATA_QUALITY_CONFIG,
        "notification_config": NOTIFICATION_CONFIG,
        "backup_config": BACKUP_CONFIG,
        "api_rate_limits": API_RATE_LIMITS,
        "market_calendar": MARKET_CALENDAR,
        "health_monitoring": HEALTH_MONITORING
    }
    
    # Override with environment-specific settings
    if env in ENVIRONMENT_CONFIGS:
        env_config = ENVIRONMENT_CONFIGS[env]
        base_config["task_config"].update({
            k: v for k, v in env_config.items() 
            if k in base_config["task_config"]
        })
    
    return base_config