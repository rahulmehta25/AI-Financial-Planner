"""
SQLAlchemy models for portfolio tracking.
"""
from sqlalchemy import (
    Column, String, DateTime, Decimal, Integer, Boolean, Date, 
    ForeignKey, UniqueConstraint, Index, Enum as SQLEnum, Text, INET
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func
from datetime import datetime
import enum
import uuid

Base = declarative_base()


class TransactionSide(enum.Enum):
    """Transaction side enumeration."""
    BUY = "buy"
    SELL = "sell"


class AssetClass(enum.Enum):
    """Asset class enumeration."""
    EQUITY = "equity"
    ETF = "etf"
    MUTUAL_FUND = "mutual_fund"
    BOND = "bond"
    CASH = "cash"
    CRYPTO = "crypto"
    COMMODITY = "commodity"
    OTHER = "other"


class AccountType(enum.Enum):
    """Account type enumeration."""
    TAXABLE = "taxable"
    TRADITIONAL_IRA = "traditional_ira"
    ROTH_IRA = "roth_ira"
    FOUR_O_ONE_K = "401k"
    HSA = "hsa"
    OTHER = "other"


class User(Base):
    """User model."""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    accounts = relationship("Account", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user")


class Account(Base):
    """Brokerage account model."""
    __tablename__ = "accounts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    account_type = Column(SQLEnum(AccountType), nullable=False)
    broker = Column(String(255))
    account_number = Column(String(255))
    base_currency = Column(String(3), default="USD")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="accounts")
    transactions = relationship("Transaction", back_populates="account", cascade="all, delete-orphan")
    positions = relationship("Position", back_populates="account", cascade="all, delete-orphan")
    lots = relationship("Lot", back_populates="account", cascade="all, delete-orphan")
    snapshots = relationship("PortfolioSnapshot", back_populates="account", cascade="all, delete-orphan")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint("user_id", "name", name="uq_user_account_name"),
        Index("ix_accounts_user_id", "user_id"),
    )


class Instrument(Base):
    """Financial instrument model."""
    __tablename__ = "instruments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    symbol = Column(String(20), nullable=False)
    exchange = Column(String(50))
    name = Column(String(255))
    asset_class = Column(SQLEnum(AssetClass), nullable=False)
    currency = Column(String(3), default="USD")
    isin = Column(String(12))
    cusip = Column(String(9))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    prices = relationship("Price", back_populates="instrument", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="instrument")
    positions = relationship("Position", back_populates="instrument")
    lots = relationship("Lot", back_populates="instrument")
    corporate_actions = relationship("CorporateAction", back_populates="instrument", cascade="all, delete-orphan")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint("symbol", "exchange", name="uq_symbol_exchange"),
        Index("ix_instruments_symbol", "symbol"),
        Index("ix_instruments_asset_class", "asset_class"),
    )


class Price(Base):
    """Price data model (TimescaleDB hypertable)."""
    __tablename__ = "prices"
    
    instrument_id = Column(UUID(as_uuid=True), ForeignKey("instruments.id", ondelete="CASCADE"), primary_key=True)
    ts = Column(DateTime(timezone=True), primary_key=True)
    open = Column(Decimal(20, 8))
    high = Column(Decimal(20, 8))
    low = Column(Decimal(20, 8))
    close = Column(Decimal(20, 8), nullable=False)
    adj_close = Column(Decimal(20, 8))
    volume = Column(Integer)
    source = Column(String(50))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    instrument = relationship("Instrument", back_populates="prices")
    
    # Indexes
    __table_args__ = (
        Index("ix_prices_instrument_ts", "instrument_id", "ts"),
        Index("ix_prices_ts", "ts"),
    )


class Transaction(Base):
    """Transaction model (immutable)."""
    __tablename__ = "transactions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False)
    instrument_id = Column(UUID(as_uuid=True), ForeignKey("instruments.id"), nullable=False)
    side = Column(SQLEnum(TransactionSide), nullable=False)
    quantity = Column(Decimal(20, 8), nullable=False)
    price = Column(Decimal(20, 8), nullable=False)
    fee = Column(Decimal(20, 8), default=0)
    trade_date = Column(Date, nullable=False)
    settlement_date = Column(Date)
    idempotency_key = Column(String(255), unique=True)
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    account = relationship("Account", back_populates="transactions")
    instrument = relationship("Instrument", back_populates="transactions")
    lots = relationship("Lot", back_populates="transaction", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index("ix_transactions_account_trade", "account_id", "trade_date"),
        Index("ix_transactions_account_instrument", "account_id", "instrument_id"),
        Index("ix_transactions_idempotency", "idempotency_key"),
    )


class Lot(Base):
    """Tax lot model."""
    __tablename__ = "lots"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transaction_id = Column(UUID(as_uuid=True), ForeignKey("transactions.id", ondelete="CASCADE"), nullable=False)
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False)
    instrument_id = Column(UUID(as_uuid=True), ForeignKey("instruments.id"), nullable=False)
    quantity_open = Column(Decimal(20, 8), nullable=False)
    quantity_closed = Column(Decimal(20, 8), default=0)
    cost_basis = Column(Decimal(20, 8), nullable=False)
    open_date = Column(Date, nullable=False)
    close_date = Column(Date)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    transaction = relationship("Transaction", back_populates="lots")
    account = relationship("Account", back_populates="lots")
    instrument = relationship("Instrument", back_populates="lots")
    
    # Indexes
    __table_args__ = (
        Index("ix_lots_instrument_open", "instrument_id", "open_date"),
        Index("ix_lots_account_instrument", "account_id", "instrument_id"),
    )


class Position(Base):
    """Current position model (cached)."""
    __tablename__ = "positions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False)
    instrument_id = Column(UUID(as_uuid=True), ForeignKey("instruments.id"), nullable=False)
    quantity = Column(Decimal(20, 8), nullable=False)
    average_cost = Column(Decimal(20, 8))
    market_value = Column(Decimal(20, 8))
    unrealized_gain = Column(Decimal(20, 8))
    last_updated = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    account = relationship("Account", back_populates="positions")
    instrument = relationship("Instrument", back_populates="positions")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint("account_id", "instrument_id", name="uq_account_instrument"),
        Index("ix_positions_account", "account_id"),
        Index("ix_positions_account_instrument", "account_id", "instrument_id"),
    )


class CorporateAction(Base):
    """Corporate action model."""
    __tablename__ = "corporate_actions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    instrument_id = Column(UUID(as_uuid=True), ForeignKey("instruments.id"), nullable=False)
    action_type = Column(String(50), nullable=False)  # 'split', 'dividend', 'spinoff'
    ex_date = Column(Date, nullable=False)
    record_date = Column(Date)
    payment_date = Column(Date)
    ratio = Column(Decimal(20, 8))  # For splits
    cash_amount = Column(Decimal(20, 8))  # For dividends
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    instrument = relationship("Instrument", back_populates="corporate_actions")
    
    # Indexes
    __table_args__ = (
        Index("ix_corporate_actions_instrument", "instrument_id"),
        Index("ix_corporate_actions_ex_date", "ex_date"),
    )


class Benchmark(Base):
    """Benchmark model."""
    __tablename__ = "benchmarks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    symbol = Column(String(20), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class FXRate(Base):
    """Foreign exchange rate model (TimescaleDB hypertable)."""
    __tablename__ = "fx_rates"
    
    base_currency = Column(String(3), primary_key=True)
    quote_currency = Column(String(3), primary_key=True)
    ts = Column(DateTime(timezone=True), primary_key=True)
    rate = Column(Decimal(20, 8), nullable=False)
    source = Column(String(50))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Indexes
    __table_args__ = (
        Index("ix_fx_rates_currencies_ts", "base_currency", "quote_currency", "ts"),
    )


class PortfolioSnapshot(Base):
    """Portfolio snapshot model."""
    __tablename__ = "portfolio_snapshots"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False)
    snapshot_date = Column(Date, nullable=False)
    total_value = Column(Decimal(20, 8), nullable=False)
    cash_value = Column(Decimal(20, 8), default=0)
    positions_value = Column(Decimal(20, 8), default=0)
    daily_return = Column(Decimal(10, 6))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    account = relationship("Account", back_populates="snapshots")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint("account_id", "snapshot_date", name="uq_account_snapshot_date"),
        Index("ix_snapshots_account_date", "account_id", "snapshot_date"),
    )


class AuditLog(Base):
    """Audit log model (immutable, append-only)."""
    __tablename__ = "audit_log"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    action = Column(String(100), nullable=False)
    entity_type = Column(String(50))
    entity_id = Column(UUID(as_uuid=True))
    old_value = Column(JSONB)
    new_value = Column(JSONB)
    ip_address = Column(INET)
    user_agent = Column(Text)
    request_id = Column(String(100))
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")
    
    # Indexes
    __table_args__ = (
        Index("ix_audit_log_user", "user_id", "timestamp"),
        Index("ix_audit_log_entity", "entity_type", "entity_id", "timestamp"),
        Index("ix_audit_log_request", "request_id"),
    )