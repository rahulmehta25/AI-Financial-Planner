"""
All SQLAlchemy models for the Financial Planner
This file contains all models to ensure proper relationships are established
"""
from typing import Optional, List
from decimal import Decimal
from datetime import date, datetime
from sqlalchemy import (
    Column, String, Boolean, DateTime, JSON, Date, 
    ForeignKey, UniqueConstraint, Index, Enum, DECIMAL, BigInteger
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from app.core.database import Base
from app.models.base import TimestampMixin, TransactionSide, AssetClass, AccountType

# Note: User model is defined in user.py to avoid circular imports

# Account Model
class Account(Base, TimestampMixin):
    """Brokerage account model"""
    
    __tablename__ = "accounts"
    __allow_unmapped__ = True
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    account_type = Column(Enum(AccountType), nullable=False, default=AccountType.TAXABLE)
    broker = Column(String(255))
    account_number = Column(String(255))
    base_currency = Column(String(3), default="USD", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    meta_data = Column("metadata", JSON, default=dict, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="accounts")
    transactions = relationship("Transaction", back_populates="account", cascade="all, delete-orphan")
    positions = relationship("Position", back_populates="account", cascade="all, delete-orphan")
    lots = relationship("Lot", back_populates="account", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("idx_accounts_user_id", "user_id"),
    )


# Instrument Model
class Instrument(Base, TimestampMixin):
    """Financial instrument (stock, ETF, etc.)"""
    
    __tablename__ = "instruments"
    __allow_unmapped__ = True
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    symbol = Column(String(20), nullable=False)
    exchange = Column(String(50))
    name = Column(String(255))
    asset_class = Column(Enum(AssetClass), nullable=False, default=AssetClass.STOCK)
    currency = Column(String(3), default="USD", nullable=False)
    isin = Column(String(12))
    cusip = Column(String(9))
    is_active = Column(Boolean, default=True, nullable=False)
    meta_data = Column("metadata", JSON, default=dict, nullable=False)
    
    # Relationships
    transactions = relationship("Transaction", back_populates="instrument")
    positions = relationship("Position", back_populates="instrument")
    prices = relationship("Price", back_populates="instrument", cascade="all, delete-orphan")
    lots = relationship("Lot", back_populates="instrument")
    
    __table_args__ = (
        UniqueConstraint("symbol", "exchange", name="uq_instruments_symbol_exchange"),
        Index("idx_instruments_symbol", "symbol"),
    )


# Transaction Model
class Transaction(Base, TimestampMixin):
    """Buy/sell transaction record"""
    
    __tablename__ = "transactions"
    __allow_unmapped__ = True
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False)
    instrument_id = Column(UUID(as_uuid=True), ForeignKey("instruments.id"), nullable=False)
    side = Column(Enum(TransactionSide), nullable=False)
    quantity = Column(DECIMAL(20, 8), nullable=False)
    price = Column(DECIMAL(20, 8), nullable=False)
    fee = Column(DECIMAL(20, 8), default=0, nullable=False)
    trade_date = Column(Date, nullable=False)
    settlement_date = Column(Date)
    idempotency_key = Column(String(255), unique=True)
    note = Column(String)
    meta_data = Column("metadata", JSON, default=dict, nullable=False)
    
    # Relationships
    account = relationship("Account", back_populates="transactions")
    instrument = relationship("Instrument", back_populates="transactions")
    lots = relationship("Lot", back_populates="transaction", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("idx_transactions_account_trade", "account_id", "trade_date"),
        Index("idx_transactions_instrument", "instrument_id"),
    )


# Position Model
class Position(Base, TimestampMixin):
    """Current position (cached holdings)"""
    
    __tablename__ = "positions"
    __allow_unmapped__ = True
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False)
    instrument_id = Column(UUID(as_uuid=True), ForeignKey("instruments.id"), nullable=False)
    quantity = Column(DECIMAL(20, 8), nullable=False)
    avg_cost = Column(DECIMAL(20, 8), nullable=False)
    last_price = Column(DECIMAL(20, 8))
    market_value = Column(DECIMAL(20, 8))
    unrealized_pl = Column(DECIMAL(20, 8))
    last_updated = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    # Relationships
    account = relationship("Account", back_populates="positions")
    instrument = relationship("Instrument", back_populates="positions")
    
    __table_args__ = (
        UniqueConstraint("account_id", "instrument_id", name="uq_positions_account_instrument"),
        Index("idx_positions_account", "account_id"),
    )


# Price Model (TimescaleDB hypertable)
class Price(Base):
    """Price data (time-series)"""
    
    __tablename__ = "prices"
    __allow_unmapped__ = True
    
    instrument_id = Column(UUID(as_uuid=True), ForeignKey("instruments.id", ondelete="CASCADE"), nullable=False, primary_key=True)
    ts = Column(DateTime(timezone=True), nullable=False, primary_key=True)
    open = Column(DECIMAL(20, 8))
    high = Column(DECIMAL(20, 8))
    low = Column(DECIMAL(20, 8))
    close = Column(DECIMAL(20, 8), nullable=False)
    adj_close = Column(DECIMAL(20, 8))
    volume = Column(BigInteger)
    source = Column(String(50), default="yfinance")
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    # Relationships
    instrument = relationship("Instrument", back_populates="prices")
    
    __table_args__ = (
        Index("idx_prices_instrument_ts", "instrument_id", "ts"),
    )


# Lot Model
class Lot(Base, TimestampMixin):
    """Tax lot for cost basis tracking"""
    
    __tablename__ = "lots"
    __allow_unmapped__ = True
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transaction_id = Column(UUID(as_uuid=True), ForeignKey("transactions.id", ondelete="CASCADE"), nullable=False)
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False)
    instrument_id = Column(UUID(as_uuid=True), ForeignKey("instruments.id"), nullable=False)
    quantity_open = Column(DECIMAL(20, 8), nullable=False)
    quantity_closed = Column(DECIMAL(20, 8), default=0, nullable=False)
    cost_basis = Column(DECIMAL(20, 8), nullable=False)
    open_date = Column(Date, nullable=False)
    close_date = Column(Date)
    
    # Relationships
    transaction = relationship("Transaction", back_populates="lots")
    account = relationship("Account", back_populates="lots")
    instrument = relationship("Instrument", back_populates="lots")
    
    __table_args__ = (
        Index("idx_lots_account_instrument", "account_id", "instrument_id"),
        Index("idx_lots_open", "instrument_id", "open_date"),
    )