"""
Notification System Models and Enums
"""

from enum import Enum
from typing import Dict, Any, Optional, List
from datetime import datetime
from pydantic import BaseModel, Field
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.base import Base


class NotificationChannel(str, Enum):
    """Notification delivery channels"""
    EMAIL = "email"
    PUSH = "push"
    SMS = "sms"
    IN_APP = "in_app"


class NotificationStatus(str, Enum):
    """Notification delivery status"""
    PENDING = "pending"
    QUEUED = "queued"
    SENDING = "sending"
    DELIVERED = "delivered"
    FAILED = "failed"
    BOUNCED = "bounced"
    REJECTED = "rejected"
    READ = "read"
    CLICKED = "clicked"
    UNSUBSCRIBED = "unsubscribed"


class NotificationPriority(str, Enum):
    """Notification priority levels"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class NotificationType(str, Enum):
    """Types of notifications"""
    WELCOME = "welcome"
    GOAL_ACHIEVEMENT = "goal_achievement"
    GOAL_REMINDER = "goal_reminder"
    MARKET_ALERT = "market_alert"
    PORTFOLIO_REBALANCE = "portfolio_rebalance"
    WEEKLY_SUMMARY = "weekly_summary"
    MONTHLY_SUMMARY = "monthly_summary"
    SECURITY_ALERT = "security_alert"
    PASSWORD_RESET = "password_reset"
    ACCOUNT_VERIFICATION = "account_verification"
    DEPOSIT_CONFIRMATION = "deposit_confirmation"
    WITHDRAWAL_CONFIRMATION = "withdrawal_confirmation"
    BUDGET_ALERT = "budget_alert"
    BILL_REMINDER = "bill_reminder"
    INVESTMENT_OPPORTUNITY = "investment_opportunity"
    MARKET_NEWS = "market_news"
    EDUCATIONAL_CONTENT = "educational_content"
    SYSTEM_MAINTENANCE = "system_maintenance"


# SQLAlchemy Models
class NotificationTemplate(Base):
    """Notification template model"""
    __tablename__ = "notification_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True)
    channel = Column(SQLEnum(NotificationChannel))
    type = Column(SQLEnum(NotificationType))
    subject_template = Column(String(200))
    body_template = Column(Text)
    html_template = Column(Text)
    variables = Column(JSON)  # Required template variables
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    notifications = relationship("Notification", back_populates="template")


class NotificationPreference(Base):
    """User notification preferences"""
    __tablename__ = "notification_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    channel = Column(SQLEnum(NotificationChannel))
    type = Column(SQLEnum(NotificationType))
    enabled = Column(Boolean, default=True)
    frequency = Column(String(50), default="immediate")  # immediate, daily, weekly, monthly
    quiet_hours_start = Column(String(5))  # HH:MM format
    quiet_hours_end = Column(String(5))    # HH:MM format
    timezone = Column(String(50), default="UTC")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="notification_preferences")


class Notification(Base):
    """Notification record"""
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    template_id = Column(Integer, ForeignKey("notification_templates.id"))
    channel = Column(SQLEnum(NotificationChannel))
    type = Column(SQLEnum(NotificationType))
    priority = Column(SQLEnum(NotificationPriority), default=NotificationPriority.NORMAL)
    status = Column(SQLEnum(NotificationStatus), default=NotificationStatus.PENDING)
    
    # Content
    subject = Column(String(200))
    body = Column(Text)
    html_body = Column(Text)
    data = Column(JSON)  # Additional data for the notification
    
    # Delivery details
    recipient = Column(String(200))  # email, phone number, or device token
    provider = Column(String(50))    # sendgrid, twilio, fcm, etc.
    provider_id = Column(String(100)) # External provider's message ID
    provider_response = Column(JSON)
    
    # Scheduling
    scheduled_at = Column(DateTime(timezone=True))
    sent_at = Column(DateTime(timezone=True))
    delivered_at = Column(DateTime(timezone=True))
    read_at = Column(DateTime(timezone=True))
    clicked_at = Column(DateTime(timezone=True))
    
    # Tracking
    open_count = Column(Integer, default=0)
    click_count = Column(Integer, default=0)
    bounce_reason = Column(String(200))
    error_message = Column(Text)
    
    # Retry logic
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    next_retry_at = Column(DateTime(timezone=True))
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="notifications")
    template = relationship("NotificationTemplate", back_populates="notifications")


class NotificationLog(Base):
    """Notification delivery log"""
    __tablename__ = "notification_logs"

    id = Column(Integer, primary_key=True, index=True)
    notification_id = Column(Integer, ForeignKey("notifications.id"))
    event_type = Column(String(50))  # sent, delivered, opened, clicked, bounced, etc.
    event_data = Column(JSON)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    notification = relationship("Notification")


class UnsubscribeToken(Base):
    """Unsubscribe tokens for email notifications"""
    __tablename__ = "unsubscribe_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    token = Column(String(64), unique=True, index=True)
    channel = Column(SQLEnum(NotificationChannel))
    type = Column(SQLEnum(NotificationType))
    expires_at = Column(DateTime(timezone=True))
    used = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User")


# Pydantic Models
class NotificationBase(BaseModel):
    """Base notification model"""
    channel: NotificationChannel
    type: NotificationType
    priority: NotificationPriority = NotificationPriority.NORMAL
    subject: Optional[str] = None
    body: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    scheduled_at: Optional[datetime] = None


class NotificationCreate(NotificationBase):
    """Create notification model"""
    user_id: int
    recipient: Optional[str] = None


class NotificationUpdate(BaseModel):
    """Update notification model"""
    status: Optional[NotificationStatus] = None
    provider_id: Optional[str] = None
    provider_response: Optional[Dict[str, Any]] = None
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    clicked_at: Optional[datetime] = None
    error_message: Optional[str] = None
    bounce_reason: Optional[str] = None


class NotificationResponse(NotificationBase):
    """Notification response model"""
    id: int
    user_id: int
    status: NotificationStatus
    recipient: Optional[str] = None
    provider: Optional[str] = None
    provider_id: Optional[str] = None
    retry_count: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PreferenceUpdate(BaseModel):
    """Update user preferences model"""
    channel: NotificationChannel
    type: NotificationType
    enabled: bool
    frequency: Optional[str] = "immediate"
    quiet_hours_start: Optional[str] = None
    quiet_hours_end: Optional[str] = None
    timezone: Optional[str] = "UTC"


class BulkNotificationRequest(BaseModel):
    """Bulk notification request"""
    user_ids: List[int]
    channel: NotificationChannel
    type: NotificationType
    priority: NotificationPriority = NotificationPriority.NORMAL
    template_data: Dict[str, Any]
    scheduled_at: Optional[datetime] = None


class NotificationStats(BaseModel):
    """Notification statistics"""
    total_sent: int
    total_delivered: int
    total_opened: int
    total_clicked: int
    total_failed: int
    delivery_rate: float
    open_rate: float
    click_rate: float
    bounce_rate: float