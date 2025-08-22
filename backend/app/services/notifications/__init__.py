"""
Notification System Package

Comprehensive notification system supporting:
- Email notifications (SendGrid/AWS SES)
- Push notifications (Firebase Cloud Messaging)
- SMS notifications (Twilio)
- In-app notifications
- Template management
- Preference management
- Scheduling and queuing
"""

from .manager import NotificationManager
from .email_service import EmailService
from .push_service import PushNotificationService
from .sms_service import SMSService
from .in_app_service import InAppNotificationService
from .template_manager import NotificationTemplateManager
from .preferences_manager import PreferencesManager
from .scheduler import NotificationScheduler
from .models import (
    NotificationChannel,
    NotificationStatus,
    NotificationPriority,
    NotificationPreference,
)

__all__ = [
    "NotificationManager",
    "EmailService", 
    "PushNotificationService",
    "SMSService",
    "InAppNotificationService",
    "NotificationTemplateManager",
    "PreferencesManager",
    "NotificationScheduler",
    "NotificationChannel",
    "NotificationStatus", 
    "NotificationPriority",
    "NotificationPreference",
]