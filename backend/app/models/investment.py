"""
Investment model for tracking user portfolios and holdings
"""

import uuid
from datetime import datetime, date
from sqlalchemy import Column, DateTime, String, Numeric, ForeignKey, Text, Date, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.database.base import Base


class Investment(Base):
    __tablename__ = "investments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Investment Identification
    symbol = Column(String(20), nullable=False)  # Stock ticker, fund symbol, etc.
    name = Column(String(200), nullable=False)
    investment_type = Column(String(50), nullable=False)  # stock, bond, etf, mutual_fund, crypto, real_estate, commodity
    
    # Account Information
    account_type = Column(String(50), nullable=False)  # taxable, ira, 401k, roth_ira, etc.
    account_name = Column(String(100), nullable=True)
    broker = Column(String(100), nullable=True)
    
    # Position Details
    shares_owned = Column(Numeric(15, 6), default=0)
    average_cost_basis = Column(Numeric(15, 4), default=0)
    current_price = Column(Numeric(15, 4), default=0)
    current_value = Column(Numeric(15, 2), default=0)
    
    # Purchase Information
    purchase_date = Column(Date, nullable=False)
    purchase_price = Column(Numeric(15, 4), nullable=False)
    purchase_amount = Column(Numeric(15, 2), nullable=False)
    
    # Performance Tracking
    unrealized_gain_loss = Column(Numeric(15, 2), default=0)
    unrealized_gain_loss_percentage = Column(Numeric(8, 4), default=0)
    dividend_yield = Column(Numeric(6, 4), default=0)
    total_dividends_received = Column(Numeric(15, 2), default=0)
    
    # Investment Strategy
    investment_goal = Column(String(50), nullable=True)  # growth, income, balanced, speculation
    risk_level = Column(String(20), nullable=True)  # low, medium, high
    sector = Column(String(50), nullable=True)
    geographic_focus = Column(String(50), nullable=True)  # domestic, international, global
    
    # Tax Information
    tax_lot_method = Column(String(20), default="fifo")  # fifo, lifo, specific_identification, average_cost
    is_tax_advantaged = Column(Boolean, default=False)
    cost_basis_adjusted = Column(Boolean, default=False)
    
    # Monitoring and Alerts
    target_allocation_percentage = Column(Numeric(5, 2), nullable=True)
    rebalance_threshold = Column(Numeric(5, 2), default=5.0)  # Percentage deviation before rebalancing
    stop_loss_percentage = Column(Numeric(5, 2), nullable=True)
    take_profit_percentage = Column(Numeric(5, 2), nullable=True)
    
    # Status and Flags
    status = Column(String(20), default="active")  # active, sold, transferred, closed
    is_core_holding = Column(Boolean, default=False)
    is_monitored = Column(Boolean, default=True)
    auto_reinvest_dividends = Column(Boolean, default=True)
    
    # Additional Data
    expense_ratio = Column(Numeric(6, 4), nullable=True)  # For funds
    beta = Column(Numeric(6, 4), nullable=True)  # Market beta
    pe_ratio = Column(Numeric(8, 2), nullable=True)  # Price-to-earnings ratio
    market_cap = Column(Numeric(20, 2), nullable=True)
    
    # Historical Data
    price_history = Column(JSONB, nullable=True)  # Store recent price history
    performance_metrics = Column(JSONB, nullable=True)  # Store calculated metrics
    
    # Notes and Research
    notes = Column(Text, nullable=True)
    research_notes = Column(Text, nullable=True)
    tags = Column(JSONB, nullable=True)  # Array of tags for categorization
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_price_update = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="investments")

    @property
    def total_cost_basis(self) -> float:
        """Calculate total cost basis"""
        return float(self.shares_owned or 0) * float(self.average_cost_basis or 0)

    @property
    def market_value(self) -> float:
        """Calculate current market value"""
        return float(self.shares_owned or 0) * float(self.current_price or 0)

    @property
    def gain_loss_amount(self) -> float:
        """Calculate gain/loss amount"""
        return self.market_value - self.total_cost_basis

    @property
    def gain_loss_percentage(self) -> float:
        """Calculate gain/loss percentage"""
        if self.total_cost_basis == 0:
            return 0.0
        return (self.gain_loss_amount / self.total_cost_basis) * 100

    @property
    def days_held(self) -> int:
        """Calculate number of days held"""
        return (date.today() - self.purchase_date).days

    @property
    def is_long_term_holding(self) -> bool:
        """Check if holding qualifies for long-term capital gains (365+ days)"""
        return self.days_held >= 365

    def update_current_value(self):
        """Update current value and performance metrics"""
        self.current_value = self.market_value
        self.unrealized_gain_loss = self.gain_loss_amount
        self.unrealized_gain_loss_percentage = self.gain_loss_percentage
        self.last_price_update = datetime.utcnow()