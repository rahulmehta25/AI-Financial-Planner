"""
Base Notification Service

Abstract base class for all notification services
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

from .models import NotificationChannel, NotificationStatus


logger = logging.getLogger(__name__)


class BaseNotificationService(ABC):
    """Abstract base class for notification services"""

    def __init__(self, channel: NotificationChannel):
        self.channel = channel
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    @abstractmethod
    async def send_notification(
        self,
        recipient: str,
        subject: str,
        body: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Send a notification"""
        pass

    async def validate_recipient(self, recipient: str) -> bool:
        """Validate recipient format"""
        return bool(recipient and recipient.strip())

    async def get_delivery_status(self, provider_id: str) -> Optional[NotificationStatus]:
        """Get delivery status from provider"""
        return None

    async def handle_webhook(self, provider: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle delivery webhooks from providers"""
        return {"status": "not_implemented"}

    async def retry_failed_notification(
        self,
        notification_id: int,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """Retry a failed notification"""
        return {"status": "not_implemented"}

    def get_rate_limit(self) -> Dict[str, int]:
        """Get rate limits for this service"""
        return {
            "requests_per_minute": 60,
            "requests_per_hour": 1000,
            "requests_per_day": 10000
        }

    async def check_health(self) -> Dict[str, Any]:
        """Check service health"""
        return {
            "status": "healthy",
            "channel": self.channel.value,
            "timestamp": datetime.now().isoformat()
        }