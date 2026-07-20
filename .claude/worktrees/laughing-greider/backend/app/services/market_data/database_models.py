"""
Market Data Database Models

SQLAlchemy models for market data storage.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Integer, Boolean, Text, BigInteger,
    ForeignKey, Index, CheckConstraint, UniqueConstraint, event
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, NUMERIC, TIMESTAMP
from sqlalchemy.orm import relationship

from ...database.base import Base
from ...database.models import AuditMixin


class MarketDataModel(Base, AuditMixin):
    """Market data storage for quotes, historical data, and real-time feeds"""
    __tablename__ = "market_data"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Symbol and identification
    symbol = Column(String(20), nullable=False, index=True)
    timestamp = Column(TIMESTAMP(timezone=True), nullable=False, index=True)
    
    # Price data
    open_price = Column(NUMERIC(15, 4))
    high_price = Column(NUMERIC(15, 4))
    low_price = Column(NUMERIC(15, 4))
    close_price = Column(NUMERIC(15, 4))
    current_price = Column(NUMERIC(15, 4))
    
    # Volume and market data
    volume = Column(BigInteger)
    market_cap = Column(NUMERIC(20, 2))
    
    # Calculated fields
    price_change = Column(NUMERIC(15, 4))
    price_change_percent = Column(NUMERIC(8, 4))
    
    # Metadata
    data_type = Column(String(50), nullable=False, index=True)  # quote, historical, intraday
    provider = Column(String(50), nullable=False, index=True)  # alpha_vantage, yahoo_finance, iex_cloud
    is_real_time = Column(Boolean, default=False, nullable=False)
    
    # Additional provider-specific data
    additional_data = Column(JSONB, default=dict)
    
    # Data quality and validation
    data_quality_score = Column(NUMERIC(3, 2))  # 0.0 to 1.0
    validation_flags = Column(JSONB)
    anomaly_flags = Column(JSONB)
    
    __table_args__ = (
        UniqueConstraint('symbol', 'timestamp', 'provider', name='unique_symbol_timestamp_provider'),
        Index('idx_market_data_symbol_date', 'symbol', 'timestamp'),
        Index('idx_market_data_provider_type', 'provider', 'data_type'),
        Index('idx_market_data_current_price', 'current_price'),
        Index('idx_market_data_real_time', 'is_real_time', 'timestamp'),
        CheckConstraint('open_price >= 0', name='check_open_price_positive'),
        CheckConstraint('high_price >= 0', name='check_high_price_positive'),
        CheckConstraint('low_price >= 0', name='check_low_price_positive'),
        CheckConstraint('close_price >= 0', name='check_close_price_positive'),
        CheckConstraint('current_price >= 0', name='check_current_price_positive'),
        CheckConstraint('volume >= 0', name='check_volume_positive'),
        # Partitioning by date will be handled in migration
    )
    
    def __repr__(self):
        return f"<MarketDataModel(symbol={self.symbol}, timestamp={self.timestamp}, provider={self.provider})>"


class AlertModel(Base, AuditMixin):
    """Market data alerts and notifications"""
    __tablename__ = "market_alerts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Alert configuration
    symbol = Column(String(20), nullable=False, index=True)
    alert_type = Column(String(50), nullable=False, index=True)  # price_above, price_below, etc.
    
    # Alert parameters
    threshold_value = Column(NUMERIC(15, 4))
    percentage_threshold = Column(NUMERIC(8, 4))
    
    # Alert settings
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    expires_at = Column(TIMESTAMP(timezone=True))
    
    # Notification settings
    email_notification = Column(Boolean, default=True, nullable=False)
    push_notification = Column(Boolean, default=False, nullable=False)
    webhook_url = Column(String(500))
    
    # Custom message
    custom_message = Column(Text)
    
    # Alert metadata
    last_triggered = Column(TIMESTAMP(timezone=True))
    trigger_count = Column(Integer, default=0, nullable=False)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    triggered_alerts = relationship("TriggeredAlertModel", back_populates="alert_config")
    
    __table_args__ = (
        Index('idx_alert_user_symbol', 'user_id', 'symbol'),
        Index('idx_alert_active_expires', 'is_active', 'expires_at'),
        Index('idx_alert_type_threshold', 'alert_type', 'threshold_value'),
    )
    
    def __repr__(self):
        return f"<AlertModel(id={self.id}, user_id={self.user_id}, symbol={self.symbol})>"


class TriggeredAlertModel(Base, AuditMixin):
    """Record of triggered alerts"""
    __tablename__ = "triggered_alerts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    alert_config_id = Column(UUID(as_uuid=True), ForeignKey("market_alerts.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Trigger data
    symbol = Column(String(20), nullable=False, index=True)
    alert_type = Column(String(50), nullable=False)
    trigger_price = Column(NUMERIC(15, 4), nullable=False)
    trigger_value = Column(NUMERIC(15, 4))
    trigger_timestamp = Column(TIMESTAMP(timezone=True), nullable=False, index=True)
    
    # Alert status
    status = Column(String(50), default="triggered", nullable=False)  # triggered, acknowledged, dismissed
    
    # Notification status
    email_sent = Column(Boolean, default=False, nullable=False)
    push_sent = Column(Boolean, default=False, nullable=False)
    webhook_sent = Column(Boolean, default=False, nullable=False)
    
    # Message and metadata
    message = Column(Text, nullable=False)
    additional_data = Column(JSONB)
    
    # Acknowledgment
    acknowledged_at = Column(TIMESTAMP(timezone=True))
    acknowledged_by = Column(UUID(as_uuid=True))
    
    # Relationships
    alert_config = relationship("AlertModel", back_populates="triggered_alerts")
    user = relationship("User", foreign_keys=[user_id])
    
    __table_args__ = (
        Index('idx_triggered_alert_user_timestamp', 'user_id', 'trigger_timestamp'),
        Index('idx_triggered_alert_symbol_timestamp', 'symbol', 'trigger_timestamp'),
        Index('idx_triggered_alert_status', 'status', 'trigger_timestamp'),
    )
    
    def __repr__(self):
        return f"<TriggeredAlertModel(id={self.id}, symbol={self.symbol}, trigger_timestamp={self.trigger_timestamp})>"


class CompanyInfoModel(Base, AuditMixin):
    """Company information cache"""
    __tablename__ = "company_info"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Company identification
    symbol = Column(String(20), nullable=False, unique=True, index=True)
    name = Column(String(500), nullable=False)
    
    # Company details
    sector = Column(String(200))
    industry = Column(String(200))
    description = Column(Text)
    website = Column(String(500))
    
    # Financial metrics
    market_cap = Column(NUMERIC(20, 2))
    employees = Column(Integer)
    
    # Location
    exchange = Column(String(50))
    country = Column(String(100))
    
    # Data source and quality
    provider = Column(String(50), nullable=False)
    last_updated = Column(TIMESTAMP(timezone=True), nullable=False)
    data_quality_score = Column(NUMERIC(3, 2))
    
    # Additional provider-specific data
    additional_data = Column(JSONB, default=dict)
    
    __table_args__ = (
        Index('idx_company_name', 'name'),
        Index('idx_company_sector_industry', 'sector', 'industry'),
        Index('idx_company_last_updated', 'last_updated'),
        Index('idx_company_market_cap', 'market_cap'),
    )
    
    def __repr__(self):
        return f"<CompanyInfoModel(symbol={self.symbol}, name={self.name})>"


# Event listeners for audit logging
@event.listens_for(MarketDataModel, 'after_insert')
@event.listens_for(MarketDataModel, 'after_update')
def create_market_data_audit_log(mapper, connection, target):
    """Create audit log entries for market data changes"""
    # This will be implemented in the audit service
    pass


@event.listens_for(AlertModel, 'after_insert')
@event.listens_for(AlertModel, 'after_update')
@event.listens_for(AlertModel, 'after_delete')
def create_alert_audit_log(mapper, connection, target):
    """Create audit log entries for alert changes"""
    # This will be implemented in the audit service
    pass