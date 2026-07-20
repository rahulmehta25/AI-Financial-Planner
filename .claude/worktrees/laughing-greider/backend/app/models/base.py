"""
Base model classes and enums
"""
from enum import Enum
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, DateTime, func
from sqlalchemy.ext.declarative import declared_attr
from app.core.database import Base


class TransactionSide(str, Enum):
    """Transaction side enum"""
    BUY = "buy"
    SELL = "sell"


class AssetClass(str, Enum):
    """Asset class enum"""
    STOCK = "stock"
    ETF = "etf"
    BOND = "bond"
    MUTUAL_FUND = "mutual_fund"
    CRYPTO = "crypto"
    CASH = "cash"
    OTHER = "other"


class AccountType(str, Enum):
    """Account type enum"""
    TAXABLE = "taxable"
    IRA = "ira"
    ROTH_IRA = "roth_ira"
    FOUR_ZERO_ONE_K = "401k"
    HSA = "hsa"
    OTHER = "other"


class TimestampMixin:
    """Mixin for adding timestamp columns"""
    
    @declared_attr
    def created_at(cls):
        return Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    @declared_attr
    def updated_at(cls):
        return Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)