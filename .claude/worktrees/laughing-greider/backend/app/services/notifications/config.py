"""
Notification System Configuration
"""

from pydantic_settings import BaseSettings
from typing import Optional, Dict, Any
import os


class NotificationConfig(BaseSettings):
    """Configuration for notification services"""
    
    # Email Configuration (SendGrid)
    sendgrid_api_key: Optional[str] = None
    sendgrid_from_email: str = "noreply@financialplanning.com"
    sendgrid_from_name: str = "Financial Planning App"
    
    # AWS SES Configuration
    aws_ses_region: str = "us-east-1"
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_ses_from_email: Optional[str] = None
    
    # Firebase Cloud Messaging
    fcm_server_key: Optional[str] = None
    fcm_project_id: Optional[str] = None
    fcm_credentials_file: Optional[str] = None
    
    # Twilio SMS Configuration
    twilio_account_sid: Optional[str] = None
    twilio_auth_token: Optional[str] = None
    twilio_from_number: Optional[str] = None
    
    # Push Notification Configuration
    apns_key_id: Optional[str] = None
    apns_key_file: Optional[str] = None
    apns_team_id: Optional[str] = None
    apns_bundle_id: str = "com.financialplanning.app"
    
    # Web Push Configuration
    vapid_public_key: Optional[str] = None
    vapid_private_key: Optional[str] = None
    vapid_subject: str = "mailto:support@financialplanning.com"
    
    # Redis Configuration for queues
    redis_url: str = "redis://localhost:6379"
    redis_db: int = 1
    
    # Queue Configuration
    notification_queue_name: str = "notifications"
    email_queue_name: str = "email_notifications"
    push_queue_name: str = "push_notifications"
    sms_queue_name: str = "sms_notifications"
    
    # Rate Limiting
    email_rate_limit: int = 100  # per hour
    sms_rate_limit: int = 50     # per hour
    push_rate_limit: int = 1000  # per hour
    
    # Retry Configuration
    max_retries: int = 3
    retry_delay: int = 300  # 5 minutes
    
    # Template Configuration
    template_cache_ttl: int = 3600  # 1 hour
    
    # Monitoring
    enable_delivery_tracking: bool = True
    enable_analytics: bool = True
    
    # Security
    webhook_secret: Optional[str] = None
    
    class Config:
        env_file = ".env"
        env_prefix = "NOTIFICATION_"


# Global configuration instance
notification_config = NotificationConfig()


# Provider Configuration
EMAIL_PROVIDERS = {
    "sendgrid": {
        "enabled": bool(notification_config.sendgrid_api_key),
        "priority": 1,
    },
    "aws_ses": {
        "enabled": bool(notification_config.aws_access_key_id),
        "priority": 2,
    }
}

SMS_PROVIDERS = {
    "twilio": {
        "enabled": bool(notification_config.twilio_account_sid),
        "priority": 1,
    }
}

PUSH_PROVIDERS = {
    "fcm": {
        "enabled": bool(notification_config.fcm_server_key or notification_config.fcm_credentials_file),
        "priority": 1,
    },
    "apns": {
        "enabled": bool(notification_config.apns_key_file),
        "priority": 2,
    }
}


# Default notification preferences
DEFAULT_PREFERENCES = {
    "email": {
        "welcome": True,
        "goal_achievement": True,
        "market_alerts": True,
        "weekly_summary": True,
        "monthly_summary": True,
        "security_alerts": True,
        "marketing": False,
    },
    "push": {
        "goal_achievement": True,
        "market_alerts": True,
        "security_alerts": True,
        "daily_tips": False,
        "marketing": False,
    },
    "sms": {
        "security_alerts": True,
        "critical_market_alerts": False,
        "goal_achievement": False,
        "marketing": False,
    },
    "in_app": {
        "all": True,
    }
}


# Notification Templates Configuration
TEMPLATE_CONFIG = {
    "base_url": "https://api.financialplanning.com",
    "logo_url": "https://api.financialplanning.com/static/logo.png",
    "brand_color": "#1E40AF",
    "footer_text": "Financial Planning App - Your path to financial freedom",
    "unsubscribe_url": "https://app.financialplanning.com/preferences/unsubscribe",
    "privacy_url": "https://app.financialplanning.com/privacy",
    "terms_url": "https://app.financialplanning.com/terms",
}