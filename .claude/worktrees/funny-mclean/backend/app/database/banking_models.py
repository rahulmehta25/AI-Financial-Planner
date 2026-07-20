"""
Banking Integration Database Models

This module contains all database models related to banking integration,
including credentials, accounts, transactions, alerts, and analytics.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

from sqlalchemy import (
    Column, String, Integer, DateTime, Boolean, Text, JSON, 
    ForeignKey, Index, CheckConstraint, DECIMAL, BigInteger,
    UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, NUMERIC, TIMESTAMP
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import relationship

from .base import Base


class AuditMixin:
    """Mixin class for audit fields"""
    
    @declared_attr
    def created_at(cls):
        return Column(
            TIMESTAMP(timezone=True), 
            default=lambda: datetime.now(timezone.utc),
            nullable=False,
            index=True
        )
    
    @declared_attr
    def updated_at(cls):
        return Column(
            TIMESTAMP(timezone=True), 
            default=lambda: datetime.now(timezone.utc),
            onupdate=lambda: datetime.now(timezone.utc),
            nullable=False,
            index=True
        )
    
    @declared_attr
    def created_by(cls):
        return Column(UUID(as_uuid=True), nullable=True, index=True)
    
    @declared_attr
    def updated_by(cls):
        return Column(UUID(as_uuid=True), nullable=True, index=True)


class BankingCredential(Base, AuditMixin):
    """Encrypted banking credentials storage"""
    __tablename__ = "banking_credentials"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Credential identification
    credential_id = Column(String(32), unique=True, nullable=False, index=True)  # External reference
    provider = Column(String(50), nullable=False, index=True)  # plaid, yodlee
    institution_id = Column(String(255), nullable=False)
    institution_name = Column(String(255))
    
    # Encrypted credential data
    encrypted_data = Column(Text, nullable=False)  # Encrypted JSON blob
    encryption_version = Column(String(10), default="1.0")
    
    # Status and metadata
    status = Column(String(50), default="active", nullable=False)  # active, expired, error, revoked
    last_sync = Column(TIMESTAMP(timezone=True))
    expires_at = Column(TIMESTAMP(timezone=True))
    
    # Error tracking
    error_count = Column(Integer, default=0)
    last_error = Column(Text)
    last_error_at = Column(TIMESTAMP(timezone=True))
    
    # Relationships
    accounts = relationship("BankAccount", back_populates="credential", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_banking_credential_user', 'user_id'),
        Index('idx_banking_credential_provider', 'provider', 'status'),
        Index('idx_banking_credential_expires', 'expires_at'),
    )
    
    def __repr__(self):
        return f"<BankingCredential(credential_id={self.credential_id}, provider={self.provider})>"


class BankAccount(Base, AuditMixin):
    """Bank account information"""
    __tablename__ = "bank_accounts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    credential_id = Column(UUID(as_uuid=True), ForeignKey("banking_credentials.id"), nullable=False)
    
    # Account identification
    account_id = Column(String(255), nullable=False, index=True)  # Provider account ID
    name = Column(String(255), nullable=False)
    official_name = Column(String(255))
    type = Column(String(50), nullable=False)  # checking, savings, credit, investment
    subtype = Column(String(50))
    
    # Account numbers (encrypted)
    account_number_encrypted = Column(Text)  # Encrypted account number
    routing_number_encrypted = Column(Text)  # Encrypted routing number
    mask = Column(String(10))  # Last 4 digits for display
    
    # Balance information
    current_balance = Column(NUMERIC(15, 2))
    available_balance = Column(NUMERIC(15, 2))
    limit = Column(NUMERIC(15, 2))  # Credit limit for credit accounts
    currency = Column(String(3), default="USD")
    
    # Status and metadata
    status = Column(String(50), default="active", nullable=False)
    is_closed = Column(Boolean, default=False)
    last_balance_update = Column(TIMESTAMP(timezone=True))
    
    # Monitoring settings
    low_balance_threshold = Column(NUMERIC(15, 2))
    enable_alerts = Column(Boolean, default=True)
    
    # Provider-specific data
    provider_data = Column(JSONB)  # Store provider-specific fields
    
    # Relationships
    credential = relationship("BankingCredential", back_populates="accounts")
    transactions = relationship("BankTransaction", back_populates="account", cascade="all, delete-orphan")
    alerts = relationship("BalanceAlert", back_populates="account", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_bank_account_credential', 'credential_id'),
        Index('idx_bank_account_type', 'type', 'status'),
        Index('idx_bank_account_balance_update', 'last_balance_update'),
        UniqueConstraint('credential_id', 'account_id', name='unique_credential_account'),
    )
    
    def __repr__(self):
        return f"<BankAccount(account_id={self.account_id}, name={self.name}, type={self.type})>"


class BankTransaction(Base, AuditMixin):
    """Bank transaction records"""
    __tablename__ = "bank_transactions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(UUID(as_uuid=True), ForeignKey("bank_accounts.id"), nullable=False)
    
    # Transaction identification
    transaction_id = Column(String(255), nullable=False, index=True)  # Provider transaction ID
    
    # Transaction details
    amount = Column(NUMERIC(15, 2), nullable=False)
    date = Column(DateTime(timezone=True), nullable=False, index=True)
    authorized_date = Column(DateTime(timezone=True))
    name = Column(String(500), nullable=False)
    merchant_name = Column(String(255))
    
    # Transaction type and status
    transaction_type = Column(String(50))  # debit, credit, transfer
    pending = Column(Boolean, default=False)
    
    # Location information
    location_address = Column(String(500))
    location_city = Column(String(100))
    location_region = Column(String(100))
    location_country = Column(String(2))
    location_postal_code = Column(String(20))
    location_lat = Column(NUMERIC(10, 7))
    location_lon = Column(NUMERIC(10, 7))
    
    # Categorization
    category = Column(String(100), index=True)
    subcategory = Column(String(100))
    category_confidence = Column(NUMERIC(3, 2))  # 0.0 to 1.0
    manual_category = Column(String(100))  # User-assigned category
    
    # Provider-specific data
    provider_categories = Column(JSONB)  # Original provider categories
    provider_data = Column(JSONB)  # Additional provider fields
    
    # Processing metadata
    processed_at = Column(TIMESTAMP(timezone=True))
    processing_version = Column(String(10))
    
    # Relationships
    account = relationship("BankAccount", back_populates="transactions")
    anomalies = relationship("SpendingAnomaly", back_populates="transaction")
    
    __table_args__ = (
        Index('idx_bank_transaction_account', 'account_id'),
        Index('idx_bank_transaction_date', 'date'),
        Index('idx_bank_transaction_amount', 'amount'),
        Index('idx_bank_transaction_category', 'category', 'subcategory'),
        Index('idx_bank_transaction_pending', 'pending', 'date'),
        UniqueConstraint('account_id', 'transaction_id', name='unique_account_transaction'),
    )
    
    def __repr__(self):
        return f"<BankTransaction(transaction_id={self.transaction_id}, amount={self.amount}, date={self.date})>"


class BalanceAlert(Base, AuditMixin):
    """Balance monitoring alerts"""
    __tablename__ = "balance_alerts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    account_id = Column(UUID(as_uuid=True), ForeignKey("bank_accounts.id"), nullable=False)
    
    # Alert identification
    alert_id = Column(String(100), unique=True, nullable=False, index=True)
    alert_type = Column(String(50), nullable=False, index=True)  # low_balance, negative_balance, etc.
    severity = Column(String(20), default="warning", nullable=False)  # info, warning, critical, urgent
    
    # Alert content
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    
    # Alert context
    current_balance = Column(NUMERIC(15, 2), nullable=False)
    threshold_value = Column(NUMERIC(15, 2))
    triggered_at = Column(TIMESTAMP(timezone=True), nullable=False, index=True)
    
    # Alert status
    acknowledged = Column(Boolean, default=False)
    acknowledged_at = Column(TIMESTAMP(timezone=True))
    acknowledged_by = Column(UUID(as_uuid=True))
    resolved = Column(Boolean, default=False)
    resolved_at = Column(TIMESTAMP(timezone=True))
    
    # Notification tracking
    notifications_sent = Column(JSONB, default=list)  # Track which notifications were sent
    
    # Additional metadata
    metadata = Column(JSONB)
    
    # Relationships
    account = relationship("BankAccount", back_populates="alerts")
    
    __table_args__ = (
        Index('idx_balance_alert_user', 'user_id'),
        Index('idx_balance_alert_account', 'account_id'),
        Index('idx_balance_alert_type', 'alert_type', 'severity'),
        Index('idx_balance_alert_status', 'acknowledged', 'resolved'),
        Index('idx_balance_alert_triggered', 'triggered_at'),
    )
    
    def __repr__(self):
        return f"<BalanceAlert(alert_id={self.alert_id}, alert_type={self.alert_type}, severity={self.severity})>"


class TransactionCategory(Base, AuditMixin):
    """Transaction category definitions and rules"""
    __tablename__ = "transaction_categories"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)  # Null for system categories
    
    # Category definition
    category_id = Column(String(100), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    
    # Hierarchy
    parent_category_id = Column(String(100))
    level = Column(Integer, default=1)  # 1 = top level, 2 = subcategory, etc.
    
    # Category properties
    is_system = Column(Boolean, default=False)  # System vs user-defined
    is_active = Column(Boolean, default=True)
    icon = Column(String(100))  # Icon identifier
    color = Column(String(7))  # Hex color code
    
    # Categorization rules
    keywords = Column(JSONB, default=list)  # Keywords for auto-categorization
    merchant_patterns = Column(JSONB, default=list)  # Merchant name patterns
    amount_ranges = Column(JSONB)  # Amount range rules
    
    # Usage statistics
    usage_count = Column(Integer, default=0)
    last_used = Column(TIMESTAMP(timezone=True))
    
    __table_args__ = (
        Index('idx_transaction_category_user', 'user_id'),
        Index('idx_transaction_category_system', 'is_system', 'is_active'),
        Index('idx_transaction_category_parent', 'parent_category_id'),
        UniqueConstraint('user_id', 'category_id', name='unique_user_category'),
    )
    
    def __repr__(self):
        return f"<TransactionCategory(category_id={self.category_id}, name={self.name})>"


class WebhookEvent(Base, AuditMixin):
    """Banking webhook events for audit and debugging"""
    __tablename__ = "webhook_events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Event identification
    event_id = Column(String(255), unique=True, nullable=False, index=True)
    provider = Column(String(50), nullable=False, index=True)  # plaid, yodlee
    event_type = Column(String(100), nullable=False, index=True)
    
    # Event data
    event_data = Column(JSONB, nullable=False)
    raw_payload = Column(Text)  # Original webhook payload
    
    # Processing information
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    item_id = Column(String(255), index=True)  # Provider item/account ID
    account_id = Column(String(255), index=True)
    
    # Processing status
    processed = Column(Boolean, default=False)
    processed_at = Column(TIMESTAMP(timezone=True))
    processing_time_ms = Column(Integer)
    
    # Error handling
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)
    last_retry_at = Column(TIMESTAMP(timezone=True))
    
    # Request metadata
    source_ip = Column(String(45))
    user_agent = Column(Text)
    request_headers = Column(JSONB)
    
    __table_args__ = (
        Index('idx_webhook_event_provider', 'provider', 'event_type'),
        Index('idx_webhook_event_processed', 'processed', 'created_at'),
        Index('idx_webhook_event_user', 'user_id'),
        Index('idx_webhook_event_item', 'item_id'),
    )
    
    def __repr__(self):
        return f"<WebhookEvent(event_id={self.event_id}, provider={self.provider}, event_type={self.event_type})>"


class SpendingPattern(Base, AuditMixin):
    """Detected spending patterns for analysis"""
    __tablename__ = "spending_patterns"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Pattern identification
    pattern_id = Column(String(255), nullable=False, index=True)
    pattern_type = Column(String(50), nullable=False)  # daily, weekly, monthly, merchant
    category = Column(String(100), nullable=False)
    
    # Pattern characteristics
    frequency = Column(NUMERIC(10, 2))  # Transactions per period
    average_amount = Column(NUMERIC(15, 2))
    typical_merchants = Column(JSONB, default=list)
    typical_times = Column(JSONB, default=list)
    
    # Pattern confidence and validation
    confidence = Column(NUMERIC(3, 2), nullable=False)  # 0.0 to 1.0
    supporting_transactions = Column(Integer, default=0)
    
    # Temporal information
    first_observed = Column(TIMESTAMP(timezone=True), nullable=False)
    last_observed = Column(TIMESTAMP(timezone=True), nullable=False)
    analysis_period_start = Column(TIMESTAMP(timezone=True), nullable=False)
    analysis_period_end = Column(TIMESTAMP(timezone=True), nullable=False)
    
    # Pattern metadata
    description = Column(Text)
    tags = Column(JSONB, default=list)
    is_active = Column(Boolean, default=True)
    
    # Pattern evolution tracking
    previous_pattern_id = Column(UUID(as_uuid=True), ForeignKey("spending_patterns.id"))
    change_reason = Column(String(255))
    
    # Relationships
    anomalies = relationship("SpendingAnomaly", back_populates="pattern")
    
    __table_args__ = (
        Index('idx_spending_pattern_user', 'user_id'),
        Index('idx_spending_pattern_type', 'pattern_type', 'category'),
        Index('idx_spending_pattern_confidence', 'confidence'),
        Index('idx_spending_pattern_period', 'analysis_period_start', 'analysis_period_end'),
        Index('idx_spending_pattern_active', 'is_active', 'last_observed'),
    )
    
    def __repr__(self):
        return f"<SpendingPattern(pattern_id={self.pattern_id}, pattern_type={self.pattern_type}, category={self.category})>"


class SpendingAnomaly(Base, AuditMixin):
    """Detected spending anomalies and fraud alerts"""
    __tablename__ = "spending_anomalies"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    transaction_id = Column(UUID(as_uuid=True), ForeignKey("bank_transactions.id"), nullable=True)
    pattern_id = Column(UUID(as_uuid=True), ForeignKey("spending_patterns.id"), nullable=True)
    
    # Anomaly identification
    anomaly_type = Column(String(50), nullable=False, index=True)  # amount, frequency, merchant, time, location
    severity = Column(String(20), default="low", nullable=False)  # low, medium, high, critical
    
    # Anomaly metrics
    anomaly_score = Column(NUMERIC(5, 2), nullable=False)  # Statistical score
    expected_value = Column(NUMERIC(15, 2))
    actual_value = Column(NUMERIC(15, 2), nullable=False)
    deviation_factor = Column(NUMERIC(5, 2))  # How many standard deviations
    
    # Detection information
    detection_method = Column(String(100))  # statistical, ml, rule_based
    detection_algorithm = Column(String(100))
    model_version = Column(String(50))
    
    # Anomaly description
    reason = Column(Text, nullable=False)
    suggestions = Column(JSONB, default=list)
    
    # Status and resolution
    status = Column(String(50), default="detected")  # detected, investigating, resolved, false_positive
    investigated_by = Column(UUID(as_uuid=True))
    investigated_at = Column(TIMESTAMP(timezone=True))
    resolution_notes = Column(Text)
    
    # User feedback
    user_confirmed = Column(Boolean)  # True = legitimate, False = fraud, None = no feedback
    user_feedback_at = Column(TIMESTAMP(timezone=True))
    user_notes = Column(Text)
    
    # Follow-up actions
    actions_taken = Column(JSONB, default=list)
    requires_followup = Column(Boolean, default=False)
    followup_date = Column(TIMESTAMP(timezone=True))
    
    # Relationships
    transaction = relationship("BankTransaction", back_populates="anomalies")
    pattern = relationship("SpendingPattern", back_populates="anomalies")
    
    __table_args__ = (
        Index('idx_spending_anomaly_user', 'user_id'),
        Index('idx_spending_anomaly_type', 'anomaly_type', 'severity'),
        Index('idx_spending_anomaly_score', 'anomaly_score'),
        Index('idx_spending_anomaly_status', 'status', 'created_at'),
        Index('idx_spending_anomaly_transaction', 'transaction_id'),
        Index('idx_spending_anomaly_followup', 'requires_followup', 'followup_date'),
    )
    
    def __repr__(self):
        return f"<SpendingAnomaly(anomaly_type={self.anomaly_type}, severity={self.severity}, score={self.anomaly_score})>"


class CashFlowAnalysis(Base, AuditMixin):
    """Stored cash flow analysis results"""
    __tablename__ = "cash_flow_analyses"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Analysis metadata
    analysis_period = Column(String(20), nullable=False)  # monthly, quarterly, yearly
    period_start = Column(TIMESTAMP(timezone=True), nullable=False)
    period_end = Column(TIMESTAMP(timezone=True), nullable=False)
    
    # Financial metrics
    total_income = Column(NUMERIC(15, 2), nullable=False)
    total_expenses = Column(NUMERIC(15, 2), nullable=False)
    net_cash_flow = Column(NUMERIC(15, 2), nullable=False)
    savings_rate = Column(NUMERIC(5, 4))  # As percentage
    
    # Income breakdown
    income_by_category = Column(JSONB, default=dict)
    
    # Expense breakdown
    expenses_by_category = Column(JSONB, default=dict)
    
    # Financial health metrics
    financial_health_score = Column(NUMERIC(5, 2))  # 0-100
    income_stability = Column(NUMERIC(5, 2))
    expense_control = Column(NUMERIC(5, 2))
    debt_ratio = Column(NUMERIC(5, 4))
    emergency_fund_months = Column(NUMERIC(5, 2))
    
    # Trend analysis
    trend_direction = Column(String(20))  # increasing, decreasing, stable
    trend_percentage = Column(NUMERIC(5, 2))
    volatility = Column(NUMERIC(5, 2))
    
    # Analysis results
    insights = Column(JSONB, default=list)
    recommendations = Column(JSONB, default=list)
    full_analysis = Column(JSONB)  # Complete analysis data
    
    # Processing metadata
    transactions_analyzed = Column(Integer, default=0)
    accounts_included = Column(Integer, default=0)
    analysis_version = Column(String(10))
    
    __table_args__ = (
        Index('idx_cash_flow_analysis_user', 'user_id'),
        Index('idx_cash_flow_analysis_period', 'period_start', 'period_end'),
        Index('idx_cash_flow_analysis_health_score', 'financial_health_score'),
    )
    
    def __repr__(self):
        return f"<CashFlowAnalysis(user_id={self.user_id}, period={self.analysis_period}, health_score={self.financial_health_score})>"