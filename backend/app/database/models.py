"""
Comprehensive database models for the Financial Planning System with audit logging
"""

import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from decimal import Decimal

from sqlalchemy import (
    Column, String, Integer, DateTime, Boolean, Text, JSON, 
    ForeignKey, Index, CheckConstraint, DECIMAL, BigInteger,
    text, event, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, NUMERIC, TIMESTAMP
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import relationship, validates
from sqlalchemy.ext.hybrid import hybrid_property

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


class User(Base, AuditMixin):
    """User accounts and authentication"""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    
    # User preferences and settings
    timezone = Column(String(50), default="UTC")
    locale = Column(String(10), default="en_US")
    preferences = Column(JSONB, default=dict)
    
    # Professional information
    company = Column(String(255))
    title = Column(String(255))
    license_number = Column(String(100))
    
    # Security fields
    last_login = Column(TIMESTAMP(timezone=True))
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(TIMESTAMP(timezone=True))
    password_changed_at = Column(TIMESTAMP(timezone=True))
    
    # Relationships
    plans = relationship("Plan", back_populates="user")
    audit_logs = relationship("AuditLog", back_populates="user")
    
    @hybrid_property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email})>"


class CapitalMarketAssumptions(Base, AuditMixin):
    """Versioned capital market assumptions for reproducibility"""
    __tablename__ = "capital_market_assumptions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    version = Column(String(50), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True, nullable=False)
    effective_date = Column(DateTime(timezone=True), nullable=False)
    
    # CMA data stored as JSONB for flexibility
    assumptions = Column(JSONB, nullable=False)
    
    # Metadata
    source = Column(String(255))
    methodology = Column(Text)
    review_date = Column(DateTime(timezone=True))
    approved_by = Column(UUID(as_uuid=True))
    
    # Relationships
    plans = relationship("Plan", back_populates="cma")
    
    __table_args__ = (
        UniqueConstraint('version', name='unique_cma_version'),
        Index('idx_cma_effective_date', 'effective_date'),
        Index('idx_cma_active', 'is_active'),
    )
    
    def __repr__(self):
        return f"<CapitalMarketAssumptions(version={self.version}, name={self.name})>"


class PortfolioModel(Base, AuditMixin):
    """Risk-based portfolio templates"""
    __tablename__ = "portfolio_models"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    risk_level = Column(Integer, nullable=False)  # 1-10 scale
    description = Column(Text)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Portfolio composition stored as JSONB
    asset_allocation = Column(JSONB, nullable=False)
    
    # Expected returns and risk metrics
    expected_return = Column(NUMERIC(5, 4))  # Annual expected return
    volatility = Column(NUMERIC(5, 4))  # Annual volatility
    sharpe_ratio = Column(NUMERIC(5, 4))
    
    # Relationships
    plans = relationship("Plan", back_populates="portfolio_model")
    
    __table_args__ = (
        CheckConstraint('risk_level >= 1 AND risk_level <= 10', name='check_risk_level'),
        Index('idx_portfolio_risk_level', 'risk_level'),
        Index('idx_portfolio_active', 'is_active'),
    )
    
    def __repr__(self):
        return f"<PortfolioModel(name={self.name}, risk_level={self.risk_level})>"


class Plan(Base, AuditMixin):
    """Metadata for each financial plan"""
    __tablename__ = "plans"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Plan identification
    name = Column(String(255), nullable=False)
    description = Column(Text)
    status = Column(String(50), default="draft", nullable=False)  # draft, active, archived
    
    # Versioning for reproducibility
    version = Column(Integer, default=1, nullable=False)
    parent_plan_id = Column(UUID(as_uuid=True), ForeignKey("plans.id"))
    
    # Key references for reproducibility
    cma_id = Column(UUID(as_uuid=True), ForeignKey("capital_market_assumptions.id"), nullable=False)
    portfolio_model_id = Column(UUID(as_uuid=True), ForeignKey("portfolio_models.id"), nullable=False)
    
    # Monte Carlo configuration
    monte_carlo_iterations = Column(Integer, default=10000)
    random_seed = Column(BigInteger, nullable=False)  # For complete reproducibility
    
    # Plan metadata
    planning_horizon_years = Column(Integer, nullable=False)
    confidence_level = Column(NUMERIC(3, 2), default=0.95)  # 95% confidence
    
    # Timestamps for plan lifecycle
    last_run_at = Column(TIMESTAMP(timezone=True))
    completed_at = Column(TIMESTAMP(timezone=True))
    
    # Tags and categorization
    tags = Column(JSONB, default=list)
    category = Column(String(100))
    
    # Relationships
    user = relationship("User", back_populates="plans")
    cma = relationship("CapitalMarketAssumptions", back_populates="plans")
    portfolio_model = relationship("PortfolioModel", back_populates="plans")
    inputs = relationship("PlanInput", back_populates="plan")
    outputs = relationship("PlanOutput", back_populates="plan")
    child_plans = relationship("Plan", remote_side=[id])
    
    __table_args__ = (
        CheckConstraint('planning_horizon_years > 0', name='check_planning_horizon'),
        CheckConstraint('monte_carlo_iterations > 0', name='check_monte_carlo_iterations'),
        CheckConstraint('confidence_level > 0 AND confidence_level < 1', name='check_confidence_level'),
        Index('idx_plan_user_status', 'user_id', 'status'),
        Index('idx_plan_last_run', 'last_run_at'),
        Index('idx_plan_random_seed', 'random_seed'),
    )
    
    def __repr__(self):
        return f"<Plan(id={self.id}, name={self.name}, status={self.status})>"


class PlanInput(Base, AuditMixin):
    """All user-provided inputs for complete reproducibility"""
    __tablename__ = "plan_inputs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plan_id = Column(UUID(as_uuid=True), ForeignKey("plans.id"), nullable=False)
    
    # Input categorization
    input_type = Column(String(100), nullable=False, index=True)  # demographics, goals, assets, etc.
    input_name = Column(String(255), nullable=False)
    
    # Flexible input storage
    input_value = Column(JSONB, nullable=False)
    
    # Validation and constraints
    validation_rules = Column(JSONB)
    is_valid = Column(Boolean, default=True)
    validation_errors = Column(JSONB)
    
    # Data source and confidence
    data_source = Column(String(100))  # user_input, imported, calculated
    confidence_score = Column(NUMERIC(3, 2))  # 0.0 to 1.0
    
    # Versioning
    version = Column(Integer, default=1)
    superseded_by = Column(UUID(as_uuid=True), ForeignKey("plan_inputs.id"))
    
    # Relationships
    plan = relationship("Plan", back_populates="inputs")
    
    __table_args__ = (
        Index('idx_plan_input_type', 'plan_id', 'input_type'),
        Index('idx_plan_input_name', 'plan_id', 'input_name'),
        Index('idx_plan_input_version', 'plan_id', 'version'),
    )
    
    def __repr__(self):
        return f"<PlanInput(plan_id={self.plan_id}, input_name={self.input_name})>"


class PlanOutput(Base, AuditMixin):
    """Simulation results and outcomes"""
    __tablename__ = "plan_outputs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plan_id = Column(UUID(as_uuid=True), ForeignKey("plans.id"), nullable=False)
    
    # Output categorization
    output_type = Column(String(100), nullable=False, index=True)  # simulation, analysis, recommendation
    output_name = Column(String(255), nullable=False)
    
    # Results storage
    output_value = Column(JSONB, nullable=False)
    
    # Computation metadata
    computation_time_ms = Column(Integer)
    algorithm_version = Column(String(50))
    
    # Statistical metrics
    confidence_interval_lower = Column(NUMERIC(15, 2))
    confidence_interval_upper = Column(NUMERIC(15, 2))
    standard_deviation = Column(NUMERIC(15, 2))
    
    # Versioning and dependencies
    version = Column(Integer, default=1)
    depends_on_inputs = Column(JSONB)  # List of input IDs this output depends on
    depends_on_outputs = Column(JSONB)  # List of output IDs this output depends on
    
    # Relationships
    plan = relationship("Plan", back_populates="outputs")
    
    __table_args__ = (
        Index('idx_plan_output_type', 'plan_id', 'output_type'),
        Index('idx_plan_output_name', 'plan_id', 'output_name'),
        Index('idx_plan_output_version', 'plan_id', 'version'),
    )
    
    def __repr__(self):
        return f"<PlanOutput(plan_id={self.plan_id}, output_name={self.output_name})>"


class AuditLog(Base):
    """Comprehensive audit trail for compliance"""
    __tablename__ = "audit_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Core audit fields
    timestamp = Column(TIMESTAMP(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    session_id = Column(String(255), index=True)
    
    # Action details
    action = Column(String(100), nullable=False, index=True)  # CREATE, READ, UPDATE, DELETE, EXECUTE
    resource_type = Column(String(100), nullable=False, index=True)  # plan, user, simulation, etc.
    resource_id = Column(UUID(as_uuid=True), index=True)
    
    # Request context
    ip_address = Column(String(45))  # IPv6 compatible
    user_agent = Column(Text)
    request_id = Column(UUID(as_uuid=True), index=True)
    
    # Change tracking
    old_values = Column(JSONB)
    new_values = Column(JSONB)
    changed_fields = Column(JSONB)
    
    # Additional context
    metadata = Column(JSONB)
    severity = Column(String(20), default="info")  # debug, info, warning, error, critical
    
    # Compliance fields
    compliance_category = Column(String(100))  # GDPR, SOX, etc.
    retention_until = Column(TIMESTAMP(timezone=True))
    
    # Performance tracking
    execution_time_ms = Column(Integer)
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")
    
    __table_args__ = (
        Index('idx_audit_timestamp', 'timestamp'),
        Index('idx_audit_user_action', 'user_id', 'action'),
        Index('idx_audit_resource', 'resource_type', 'resource_id'),
        Index('idx_audit_session', 'session_id', 'timestamp'),
        Index('idx_audit_request', 'request_id'),
        Index('idx_audit_severity', 'severity', 'timestamp'),
        # Partitioning will be handled in the migration
    )
    
    def __repr__(self):
        return f"<AuditLog(action={self.action}, resource_type={self.resource_type}, timestamp={self.timestamp})>"


class SystemEvent(Base):
    """System events and operational metrics"""
    __tablename__ = "system_events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timestamp = Column(TIMESTAMP(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Event classification
    event_type = Column(String(100), nullable=False, index=True)  # startup, shutdown, error, performance
    event_category = Column(String(100), nullable=False, index=True)  # system, database, api, simulation
    
    # Event details
    message = Column(Text, nullable=False)
    severity = Column(String(20), default="info", nullable=False)
    
    # Context and metadata
    component = Column(String(100))  # Which system component generated the event
    environment = Column(String(50))  # development, staging, production
    version = Column(String(50))  # Application version
    
    # Technical details
    error_code = Column(String(50))
    stack_trace = Column(Text)
    additional_data = Column(JSONB)
    
    # Performance metrics
    duration_ms = Column(Integer)
    memory_usage_mb = Column(Integer)
    cpu_usage_percent = Column(NUMERIC(5, 2))
    
    # Resolution tracking
    resolved = Column(Boolean, default=False)
    resolved_at = Column(TIMESTAMP(timezone=True))
    resolved_by = Column(UUID(as_uuid=True))
    resolution_notes = Column(Text)
    
    __table_args__ = (
        Index('idx_system_event_timestamp', 'timestamp'),
        Index('idx_system_event_type', 'event_type', 'severity'),
        Index('idx_system_event_category', 'event_category', 'timestamp'),
        Index('idx_system_event_resolved', 'resolved', 'timestamp'),
    )
    
    def __repr__(self):
        return f"<SystemEvent(event_type={self.event_type}, severity={self.severity})>"


class DataRetentionPolicy(Base, AuditMixin):
    """Data retention and cleanup policies"""
    __tablename__ = "data_retention_policies"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Policy identification
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Target data
    table_name = Column(String(100), nullable=False)
    conditions = Column(JSONB)  # SQL conditions for data selection
    
    # Retention rules
    retention_period_days = Column(Integer, nullable=False)
    action = Column(String(50), default="delete", nullable=False)  # delete, archive, anonymize
    
    # Schedule configuration
    schedule_cron = Column(String(100))  # Cron expression for automated cleanup
    last_executed = Column(TIMESTAMP(timezone=True))
    next_execution = Column(TIMESTAMP(timezone=True))
    
    # Execution tracking
    records_processed = Column(BigInteger, default=0)
    last_execution_duration_ms = Column(Integer)
    last_execution_status = Column(String(50))  # success, failed, partial
    
    __table_args__ = (
        CheckConstraint('retention_period_days > 0', name='check_retention_period'),
        Index('idx_retention_policy_active', 'is_active'),
        Index('idx_retention_policy_next_execution', 'next_execution'),
    )
    
    def __repr__(self):
        return f"<DataRetentionPolicy(name={self.name}, table_name={self.table_name})>"


# Event listeners for audit logging
@event.listens_for(User, 'after_insert')
@event.listens_for(User, 'after_update')
@event.listens_for(User, 'after_delete')
def create_user_audit_log(mapper, connection, target):
    """Create audit log entries for user changes"""
    # This will be implemented in the audit service
    pass


@event.listens_for(Plan, 'after_insert')
@event.listens_for(Plan, 'after_update')
@event.listens_for(Plan, 'after_delete')
def create_plan_audit_log(mapper, connection, target):
    """Create audit log entries for plan changes"""
    # This will be implemented in the audit service
    pass