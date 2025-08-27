"""
Authentication Models

Models for token blacklisting, user sessions, and security tracking.
"""

import uuid
from datetime import datetime, timedelta
from sqlalchemy import Boolean, Column, DateTime, String, Text, Integer, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.base import Base


class TokenBlacklist(Base):
    """
    Model for blacklisted JWT tokens to handle secure logout
    """
    __tablename__ = "token_blacklist"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    jti = Column(String(255), unique=True, index=True, nullable=False, comment="JWT ID")
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    token_type = Column(String(50), nullable=False, comment="access or refresh")
    expires_at = Column(DateTime, nullable=False, index=True)
    blacklisted_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    reason = Column(String(100), nullable=True, comment="Reason for blacklisting")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_token_blacklist_jti_expires', 'jti', 'expires_at'),
        Index('idx_token_blacklist_user_expires', 'user_id', 'expires_at'),
    )

    def __repr__(self):
        return f"<TokenBlacklist(jti={self.jti}, user_id={self.user_id})>"


class UserSession(Base):
    """
    Model for tracking active user sessions
    """
    __tablename__ = "user_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(String(255), unique=True, index=True, nullable=False)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Session metadata
    ip_address = Column(String(45), nullable=True, comment="IPv4 or IPv6 address")
    user_agent = Column(Text, nullable=True)
    device_fingerprint = Column(String(255), nullable=True)
    location = Column(String(255), nullable=True, comment="Approximate location")
    
    # Session timing
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_activity = Column(DateTime, default=datetime.utcnow, nullable=False, onupdate=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    
    # Session status
    is_active = Column(Boolean, default=True, nullable=False)
    terminated_at = Column(DateTime, nullable=True)
    termination_reason = Column(String(100), nullable=True)
    
    # Security flags
    is_suspicious = Column(Boolean, default=False, nullable=False)
    failed_attempts = Column(Integer, default=0, nullable=False)
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_user_sessions_user_active', 'user_id', 'is_active'),
        Index('idx_user_sessions_expires_active', 'expires_at', 'is_active'),
        Index('idx_user_sessions_session_id', 'session_id'),
    )

    def __repr__(self):
        return f"<UserSession(session_id={self.session_id}, user_id={self.user_id})>"

    @property
    def is_expired(self) -> bool:
        """Check if session is expired"""
        return datetime.utcnow() > self.expires_at

    @property
    def time_until_expiry(self) -> timedelta:
        """Time until session expires"""
        return self.expires_at - datetime.utcnow()

    def refresh_activity(self) -> None:
        """Update last activity timestamp"""
        self.last_activity = datetime.utcnow()

    def terminate(self, reason: str = None) -> None:
        """Terminate the session"""
        self.is_active = False
        self.terminated_at = datetime.utcnow()
        self.termination_reason = reason


class LoginAttempt(Base):
    """
    Model for tracking login attempts for security monitoring
    """
    __tablename__ = "login_attempts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Attempt metadata
    email = Column(String(255), nullable=False, index=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    
    # Attempt details
    success = Column(Boolean, nullable=False, index=True)
    attempted_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    failure_reason = Column(String(255), nullable=True)
    
    # Associated user if successful
    user_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    
    # Security metadata
    is_suspicious = Column(Boolean, default=False, nullable=False)
    blocked = Column(Boolean, default=False, nullable=False)
    
    # Indexes for performance and security queries
    __table_args__ = (
        Index('idx_login_attempts_email_time', 'email', 'attempted_at'),
        Index('idx_login_attempts_ip_time', 'ip_address', 'attempted_at'),
        Index('idx_login_attempts_success_time', 'success', 'attempted_at'),
    )

    def __repr__(self):
        return f"<LoginAttempt(email={self.email}, success={self.success})>"


class PasswordResetToken(Base):
    """
    Model for password reset tokens
    """
    __tablename__ = "password_reset_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    token = Column(String(255), unique=True, index=True, nullable=False)
    
    # Token metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    used_at = Column(DateTime, nullable=True)
    
    # Security
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    
    # Status
    is_used = Column(Boolean, default=False, nullable=False)
    is_valid = Column(Boolean, default=True, nullable=False)
    
    def __repr__(self):
        return f"<PasswordResetToken(user_id={self.user_id}, used={self.is_used})>"

    @property
    def is_expired(self) -> bool:
        """Check if token is expired"""
        return datetime.utcnow() > self.expires_at

    def mark_used(self) -> None:
        """Mark token as used"""
        self.is_used = True
        self.used_at = datetime.utcnow()

    def invalidate(self) -> None:
        """Invalidate the token"""
        self.is_valid = False


class TwoFactorAuth(Base):
    """
    Model for Two-Factor Authentication settings
    """
    __tablename__ = "two_factor_auth"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), unique=True, nullable=False, index=True)
    
    # TOTP settings
    secret_key = Column(String(255), nullable=False)  # Encrypted
    is_enabled = Column(Boolean, default=False, nullable=False)
    backup_codes = Column(Text, nullable=True)  # JSON array of encrypted codes
    
    # Setup and usage tracking
    setup_at = Column(DateTime, nullable=True)
    last_used_at = Column(DateTime, nullable=True)
    
    # Recovery
    recovery_codes_generated_at = Column(DateTime, nullable=True)
    recovery_codes_count = Column(Integer, default=0, nullable=False)

    def __repr__(self):
        return f"<TwoFactorAuth(user_id={self.user_id}, enabled={self.is_enabled})>"


class SecurityEvent(Base):
    """
    Model for tracking security-related events
    """
    __tablename__ = "security_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    session_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    
    # Event details
    event_type = Column(String(100), nullable=False, index=True)
    event_description = Column(Text, nullable=True)
    severity = Column(String(20), nullable=False, index=True)  # low, medium, high, critical
    
    # Context
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Metadata
    metadata = Column(Text, nullable=True)  # JSON data
    resolved = Column(Boolean, default=False, nullable=False)
    resolved_at = Column(DateTime, nullable=True)

    # Indexes for security queries
    __table_args__ = (
        Index('idx_security_events_user_time', 'user_id', 'timestamp'),
        Index('idx_security_events_type_time', 'event_type', 'timestamp'),
        Index('idx_security_events_severity', 'severity', 'timestamp'),
    )

    def __repr__(self):
        return f"<SecurityEvent(type={self.event_type}, severity={self.severity})>"