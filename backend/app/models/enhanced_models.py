"""
Enhanced database models with comprehensive fields for enterprise-level financial planning system

These models implement the complete database architecture specified in the Technical Implementation Guide,
including KYC compliance, tax optimization, portfolio management, and TimescaleDB integration.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from sqlalchemy import (
    Column, String, Integer, Float, DateTime, JSON, ForeignKey, Index,
    Boolean, BigInteger, text
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY, NUMERIC, TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.base import Base
from app.core.config import settings


class User(Base):
    """
    Enhanced User model with KYC compliance, risk profiling, and MFA support
    """
    __tablename__ = 'enhanced_users'
    
    # Primary identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    
    # Multi-Factor Authentication
    mfa_secret = Column(String(32))  # Base32 encoded TOTP secret
    mfa_enabled = Column(Boolean, default=False)
    mfa_backup_codes = Column(ARRAY(String(10)))  # Array of backup codes
    
    # Basic profile information
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    phone_number = Column(String(20))
    date_of_birth = Column(DateTime(timezone=False))
    
    # Enhanced profile stored as JSONB for flexibility
    profile = Column(JSONB, default={})  # Contains: address, employment, income, etc.
    
    # Financial risk profiling
    risk_tolerance = Column(Float)  # 0.0 to 1.0 scale (conservative to aggressive)
    investment_horizon = Column(Integer)  # Investment horizon in years
    tax_bracket = Column(Float)  # Federal tax bracket percentage
    state_tax_rate = Column(Float)  # State tax rate if applicable
    
    # Regulatory compliance and KYC
    kyc_status = Column(String(20), default='pending')  # pending, in_progress, approved, rejected
    kyc_data = Column(JSONB)  # Stores KYC documents, verification data, etc.
    kyc_verified_at = Column(DateTime(timezone=True))
    kyc_expires_at = Column(DateTime(timezone=True))
    
    # Accredited investor status
    accredited_investor = Column(Boolean, default=False)
    accredited_verified_at = Column(DateTime(timezone=True))
    accreditation_type = Column(String(50))  # income, net_worth, professional, entity
    
    # Account status and security
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    is_suspended = Column(Boolean, default=False)
    suspension_reason = Column(String(255))
    
    # Login and security tracking
    last_login = Column(DateTime(timezone=True))
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime(timezone=True))
    password_changed_at = Column(DateTime(timezone=True))
    
    # Terms and agreements
    terms_accepted_at = Column(DateTime(timezone=True))
    terms_version = Column(String(10))
    privacy_policy_accepted_at = Column(DateTime(timezone=True))
    marketing_consent = Column(Boolean, default=False)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
    
    # Relationships
    portfolios = relationship("Portfolio", back_populates="user", cascade="all, delete-orphan")
    
    # Performance indexes
    __table_args__ = (
        Index('idx_enhanced_user_email_active', 'email', 'is_active'),
        Index('idx_enhanced_user_kyc_status', 'kyc_status'),
        Index('idx_enhanced_user_created_at', 'created_at'),
        Index('idx_enhanced_user_risk_profile', 'risk_tolerance', 'investment_horizon'),
    )
    
    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"
    
    @property
    def needs_kyc_renewal(self) -> bool:
        """Check if KYC verification needs renewal"""
        if not self.kyc_expires_at:
            return False
        return datetime.now(timezone.utc) > self.kyc_expires_at
    
    @property
    def is_locked(self) -> bool:
        """Check if account is currently locked"""
        if not self.locked_until:
            return False
        return datetime.now(timezone.utc) < self.locked_until


class Portfolio(Base):
    """
    Enhanced Portfolio model with version control, cached metrics, and rebalancing logic
    """
    __tablename__ = 'enhanced_portfolios'
    
    # Primary identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('enhanced_users.id'), nullable=False)
    
    # Portfolio identification
    name = Column(String(100), nullable=False)
    description = Column(String(500))
    type = Column(String(20))  # 'real', 'simulated', 'watchlist', 'model'
    status = Column(String(20), default='active')  # active, inactive, closed
    
    # Current financial state
    total_value = Column(NUMERIC(15, 2))  # Total portfolio value
    cash_balance = Column(NUMERIC(15, 2), default=0)  # Available cash
    invested_value = Column(NUMERIC(15, 2), default=0)  # Value of investments
    pending_trades_value = Column(NUMERIC(15, 2), default=0)  # Pending trade amounts
    
    # Performance metrics
    performance_ytd = Column(NUMERIC(8, 4))  # Year-to-date performance percentage
    performance_1year = Column(NUMERIC(8, 4))  # 1-year performance
    performance_3year = Column(NUMERIC(8, 4))  # 3-year annualized performance
    performance_inception = Column(NUMERIC(8, 4))  # Since-inception performance
    
    # Risk metrics
    volatility = Column(NUMERIC(6, 4))  # Annualized volatility
    sharpe_ratio = Column(NUMERIC(6, 4))  # Risk-adjusted return
    max_drawdown = Column(NUMERIC(6, 4))  # Maximum drawdown percentage
    beta = Column(NUMERIC(6, 4))  # Beta vs market benchmark
    
    # Cached calculations for performance
    cached_metrics = Column(JSONB, default={})  # Stores complex calculations
    metrics_updated_at = Column(DateTime(timezone=True))
    metrics_computation_time = Column(Integer)  # Time taken to compute metrics (ms)
    
    # Target allocation and rebalancing
    target_allocation = Column(JSONB)  # Target asset class allocation
    current_allocation = Column(JSONB)  # Current asset class allocation
    rebalancing_threshold = Column(NUMERIC(4, 2), default=5.0)  # Percentage drift threshold
    last_rebalanced_at = Column(DateTime(timezone=True))
    auto_rebalancing_enabled = Column(Boolean, default=False)
    
    # Version control for optimistic locking
    version = Column(Integer, default=1)
    
    # Tax considerations
    tax_loss_harvesting_enabled = Column(Boolean, default=False)
    tax_efficiency_score = Column(NUMERIC(4, 2))  # 0-100 tax efficiency score
    estimated_tax_drag = Column(NUMERIC(6, 4))  # Estimated annual tax drag
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="portfolios")
    accounts = relationship("Account", back_populates="portfolio", cascade="all, delete-orphan")
    
    # Performance indexes
    __table_args__ = (
        Index('idx_enhanced_portfolio_user_type', 'user_id', 'type'),
        Index('idx_enhanced_portfolio_status', 'status'),
        Index('idx_enhanced_portfolio_updated_at', 'updated_at'),
    )
    
    @hybrid_property
    def needs_rebalancing(self):
        """Check if portfolio needs rebalancing based on drift from target allocation"""
        if not self.cached_metrics or not self.target_allocation:
            return False
        
        current_allocation = self.cached_metrics.get('current_allocation', {})
        
        for asset_class, target_weight in self.target_allocation.items():
            current_weight = current_allocation.get(asset_class, 0)
            drift = abs(current_weight - target_weight)
            if drift > self.rebalancing_threshold:
                return True
        return False
    
    @property
    def allocation_drift(self) -> Dict[str, float]:
        """Calculate drift between current and target allocation"""
        if not self.target_allocation or not self.cached_metrics:
            return {}
        
        current_allocation = self.cached_metrics.get('current_allocation', {})
        drift = {}
        
        for asset_class, target_weight in self.target_allocation.items():
            current_weight = current_allocation.get(asset_class, 0)
            drift[asset_class] = current_weight - target_weight
        
        return drift


class Account(Base):
    """
    Enhanced Account model with encrypted fields, Plaid integration, and comprehensive tax tracking
    """
    __tablename__ = 'enhanced_accounts'
    
    # Primary identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    portfolio_id = Column(UUID(as_uuid=True), ForeignKey('enhanced_portfolios.id'))
    
    # Account identification
    account_type = Column(String(20), nullable=False)  # '401k', 'roth_ira', '529', 'taxable', 'hsa', 'sep_ira'
    account_name = Column(String(100))
    institution = Column(String(100))
    institution_id = Column(String(50))  # Institution identifier
    account_number_encrypted = Column(String(255))  # Encrypted account number
    routing_number_encrypted = Column(String(255))  # Encrypted routing number (if applicable)
    
    # Account status
    status = Column(String(20), default='active')  # active, inactive, closed, frozen
    is_primary = Column(Boolean, default=False)
    custody_type = Column(String(30))  # self_directed, managed, robo_advisor
    
    # Financial balances
    current_balance = Column(NUMERIC(15, 2), nullable=False, default=0)
    available_balance = Column(NUMERIC(15, 2), default=0)  # Available for trading
    pending_balance = Column(NUMERIC(15, 2), default=0)  # Pending transactions
    
    # Retirement account specific fields
    vested_balance = Column(NUMERIC(15, 2))  # Vested portion for 401k
    unvested_balance = Column(NUMERIC(15, 2))  # Unvested portion
    employer_contribution_ytd = Column(NUMERIC(12, 2))  # YTD employer contributions
    employee_contribution_ytd = Column(NUMERIC(12, 2))  # YTD employee contributions
    
    # Contribution limits and matching
    annual_contribution_limit = Column(NUMERIC(12, 2))  # IRS annual limit
    catch_up_contribution_limit = Column(NUMERIC(12, 2))  # Additional for 50+
    employer_match_percent = Column(NUMERIC(5, 2))  # Employer match percentage
    employer_match_cap = Column(NUMERIC(12, 2))  # Maximum employer match
    vesting_schedule = Column(JSONB)  # Vesting schedule details
    
    # Beneficiary and special purpose info
    beneficiary_info = Column(JSONB)  # Beneficiary information for retirement/529 accounts
    state_plan_info = Column(JSONB)  # For 529 plans - state-specific information
    hsa_qualified_expenses = Column(NUMERIC(12, 2))  # For HSA - qualified expenses YTD
    
    # Tax tracking and cost basis
    cost_basis = Column(NUMERIC(15, 2), default=0)  # Total cost basis
    unrealized_gains = Column(NUMERIC(15, 2), default=0)  # Unrealized gains/losses
    realized_gains_ytd = Column(NUMERIC(15, 2), default=0)  # YTD realized gains
    realized_losses_ytd = Column(NUMERIC(15, 2), default=0)  # YTD realized losses
    dividend_income_ytd = Column(NUMERIC(12, 2), default=0)  # YTD dividend income
    interest_income_ytd = Column(NUMERIC(12, 2), default=0)  # YTD interest income
    
    # Tax loss harvesting
    tax_loss_carryforward = Column(NUMERIC(12, 2), default=0)  # Available tax loss carryforward
    wash_sale_adjustments = Column(NUMERIC(12, 2), default=0)  # Wash sale disallowed losses
    
    # Plaid integration for bank/brokerage connectivity
    plaid_access_token_encrypted = Column(String(500))  # Encrypted Plaid access token
    plaid_item_id = Column(String(100))  # Plaid item ID
    plaid_institution_id = Column(String(100))  # Plaid institution ID
    plaid_mask = Column(String(10))  # Last 4 digits for display
    last_plaid_sync = Column(DateTime(timezone=True))  # Last successful sync
    plaid_sync_status = Column(String(20), default='active')  # active, error, requires_auth
    plaid_error_code = Column(String(50))  # Last error code if any
    
    # Account features and restrictions
    margin_enabled = Column(Boolean, default=False)
    options_level = Column(Integer, default=0)  # Options trading level (0-4)
    day_trading_buying_power = Column(NUMERIC(15, 2), default=0)
    minimum_balance_required = Column(NUMERIC(12, 2))
    monthly_maintenance_fee = Column(NUMERIC(6, 2))
    
    # Metadata
    opened_date = Column(DateTime(timezone=True))
    closed_date = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
    
    # Relationships
    portfolio = relationship("Portfolio", back_populates="accounts")
    transactions = relationship("Transaction", back_populates="account", cascade="all, delete-orphan")
    
    # Performance indexes
    __table_args__ = (
        Index('idx_enhanced_account_portfolio_type', 'portfolio_id', 'account_type'),
        Index('idx_enhanced_account_institution', 'institution', 'institution_id'),
        Index('idx_enhanced_account_plaid_item', 'plaid_item_id'),
        Index('idx_enhanced_account_status', 'status'),
    )
    
    @property
    def total_contributions_ytd(self) -> float:
        """Calculate total YTD contributions"""
        employer = self.employer_contribution_ytd or 0
        employee = self.employee_contribution_ytd or 0
        return float(employer + employee)
    
    @property
    def available_contribution_room(self) -> float:
        """Calculate remaining contribution room for the year"""
        if not self.annual_contribution_limit:
            return 0
        
        used = self.employee_contribution_ytd or 0
        limit = self.annual_contribution_limit
        return float(max(0, limit - used))
    
    @property
    def is_retirement_account(self) -> bool:
        """Check if this is a retirement account"""
        retirement_types = {'401k', 'roth_ira', 'traditional_ira', 'sep_ira', 'simple_ira', '403b', '457'}
        return self.account_type in retirement_types


class Transaction(Base):
    """
    Enhanced Transaction model with tax lot tracking, wash sale detection, and comprehensive metadata
    """
    __tablename__ = 'enhanced_transactions'
    
    # Primary identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(UUID(as_uuid=True), ForeignKey('enhanced_accounts.id'), nullable=False)
    
    # Transaction basics
    type = Column(String(30), nullable=False)  # buy, sell, dividend, interest, contribution, withdrawal, transfer, split, merger
    subtype = Column(String(30))  # market, limit, stop, stop_limit for orders; qualified, non_qualified for dividends
    status = Column(String(20), default='settled')  # pending, executed, settled, cancelled, rejected
    
    # Security information
    symbol = Column(String(20), index=True)  # Stock symbol or identifier
    security_name = Column(String(200))  # Full security name
    security_type = Column(String(30))  # stock, bond, etf, mutual_fund, option, crypto, cash
    cusip = Column(String(9))  # CUSIP identifier
    isin = Column(String(12))  # ISIN identifier
    
    # Transaction amounts and quantities
    quantity = Column(NUMERIC(15, 8))  # Shares or units (high precision for crypto)
    price = Column(NUMERIC(12, 4))  # Price per share/unit
    total_amount = Column(NUMERIC(15, 2), nullable=False)  # Total transaction amount
    
    # Fees and costs
    commission = Column(NUMERIC(8, 2), default=0)  # Brokerage commission
    sec_fee = Column(NUMERIC(6, 2), default=0)  # SEC fee
    taf_fee = Column(NUMERIC(6, 2), default=0)  # TAF fee  
    other_fees = Column(NUMERIC(8, 2), default=0)  # Other fees
    total_fees = Column(NUMERIC(8, 2), default=0)  # Total fees
    
    # Tax lot tracking for cost basis
    tax_lot_id = Column(UUID(as_uuid=True))  # Links related buy/sell transactions
    cost_basis = Column(NUMERIC(15, 2))  # Cost basis for this transaction
    realized_gain_loss = Column(NUMERIC(12, 2))  # Realized gain/loss (for sells)
    
    # Wash sale detection and tracking
    wash_sale = Column(Boolean, default=False)  # Is this a wash sale?
    wash_sale_disallowed_loss = Column(NUMERIC(12, 2))  # Disallowed loss amount
    wash_sale_adjustment_to_basis = Column(NUMERIC(12, 2))  # Basis adjustment from wash sale
    related_wash_sale_transactions = Column(ARRAY(UUID(as_uuid=True)))  # Related transactions
    
    # Tax classification
    tax_category = Column(String(30))  # short_term, long_term, tax_free, tax_deferred
    holding_period_days = Column(Integer)  # Days held for tax purposes
    tax_year = Column(Integer)  # Tax year this transaction affects
    
    # Dividend and income specific
    dividend_type = Column(String(20))  # qualified, ordinary, return_of_capital, capital_gain
    dividend_per_share = Column(NUMERIC(8, 4))  # Dividend per share
    reinvestment_flag = Column(Boolean, default=False)  # Was dividend reinvested?
    
    # Corporate actions
    corporate_action_type = Column(String(30))  # split, merger, spinoff, dividend
    corporate_action_ratio = Column(String(20))  # e.g., "2:1" for stock split
    original_transaction_id = Column(UUID(as_uuid=True))  # For corporate action adjustments
    
    # Timing information
    trade_date = Column(DateTime(timezone=True), nullable=False)  # When trade was made
    settlement_date = Column(DateTime(timezone=True))  # When trade settles
    executed_at = Column(DateTime(timezone=True))  # Exact execution time
    
    # Order information
    order_id = Column(String(50))  # Broker order ID
    order_type = Column(String(20))  # market, limit, stop, stop_limit
    time_in_force = Column(String(10))  # day, gtc, ioc, fok
    
    # Data source and quality
    data_source = Column(String(50))  # plaid, manual, broker_api, import
    source_transaction_id = Column(String(100))  # Original transaction ID from source
    confidence_score = Column(NUMERIC(3, 2), default=1.0)  # Data quality confidence (0-1)
    requires_review = Column(Boolean, default=False)  # Flagged for manual review
    
    # Metadata
    notes = Column(String(500))  # User notes
    tags = Column(ARRAY(String(50)))  # User-defined tags
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
    
    # Relationships
    account = relationship("Account", back_populates="transactions")
    
    # Performance indexes for high-volume transaction queries
    __table_args__ = (
        Index('idx_enhanced_transaction_account_date', 'account_id', 'trade_date'),
        Index('idx_enhanced_transaction_symbol_date', 'symbol', 'trade_date'),
        Index('idx_enhanced_transaction_type_status', 'type', 'status'),
        Index('idx_enhanced_transaction_tax_lot', 'tax_lot_id'),
        Index('idx_enhanced_transaction_wash_sale', 'account_id', 'wash_sale', 'trade_date'),
        Index('idx_enhanced_transaction_settlement_date', 'settlement_date'),
        Index('idx_enhanced_transaction_tax_year', 'tax_year', 'tax_category'),
    )
    
    @property
    def net_amount(self) -> float:
        """Calculate net amount after fees"""
        return float(self.total_amount - (self.total_fees or 0))
    
    @property
    def is_long_term(self) -> bool:
        """Check if this is a long-term capital gain/loss (>365 days)"""
        return (self.holding_period_days or 0) > 365
    
    @property
    def effective_rate(self) -> float:
        """Calculate effective rate including fees"""
        if not self.price or not self.quantity:
            return 0
        return float((self.total_amount + (self.total_fees or 0)) / self.quantity)


class EnhancedMarketData(Base):
    """
    Enhanced MarketData model optimized for TimescaleDB with comprehensive market metrics
    """
    __tablename__ = 'enhanced_market_data'
    
    # Composite primary key for time-series data (TimescaleDB hypertable)
    time = Column(TIMESTAMP(timezone=True), primary_key=True)
    symbol = Column(String(20), primary_key=True, index=True)
    
    # Basic OHLCV data
    open = Column(NUMERIC(12, 4))
    high = Column(NUMERIC(12, 4))
    low = Column(NUMERIC(12, 4))
    close = Column(NUMERIC(12, 4), nullable=False)
    volume = Column(BigInteger)
    
    # Extended market data
    vwap = Column(NUMERIC(12, 4))  # Volume Weighted Average Price
    bid = Column(NUMERIC(12, 4))  # Current bid price
    ask = Column(NUMERIC(12, 4))  # Current ask price
    spread = Column(NUMERIC(8, 4))  # Bid-ask spread
    mid_price = Column(NUMERIC(12, 4))  # Mid-point price
    
    # Market microstructure
    bid_size = Column(BigInteger)  # Shares at bid
    ask_size = Column(BigInteger)  # Shares at ask
    trade_count = Column(Integer)  # Number of trades
    block_trades = Column(Integer)  # Number of block trades (>10K shares)
    
    # Technical indicators (pre-calculated for performance)
    rsi_14 = Column(NUMERIC(6, 2))  # 14-period RSI
    macd = Column(NUMERIC(8, 4))  # MACD line
    macd_signal = Column(NUMERIC(8, 4))  # MACD signal line
    macd_histogram = Column(NUMERIC(8, 4))  # MACD histogram
    
    # Moving averages
    sma_20 = Column(NUMERIC(12, 4))  # 20-day Simple Moving Average
    sma_50 = Column(NUMERIC(12, 4))  # 50-day Simple Moving Average
    sma_200 = Column(NUMERIC(12, 4))  # 200-day Simple Moving Average
    ema_12 = Column(NUMERIC(12, 4))  # 12-day Exponential Moving Average
    ema_26 = Column(NUMERIC(12, 4))  # 26-day Exponential Moving Average
    
    # Bollinger Bands
    bb_upper = Column(NUMERIC(12, 4))  # Upper Bollinger Band
    bb_middle = Column(NUMERIC(12, 4))  # Middle Bollinger Band (20-day SMA)
    bb_lower = Column(NUMERIC(12, 4))  # Lower Bollinger Band
    bb_width = Column(NUMERIC(8, 4))  # Bollinger Band Width
    bb_percent = Column(NUMERIC(6, 4))  # %B indicator
    
    # Volatility measures
    historical_volatility = Column(NUMERIC(8, 4))  # 20-day historical volatility
    garman_klass_volatility = Column(NUMERIC(8, 4))  # Garman-Klass volatility estimator
    parkinson_volatility = Column(NUMERIC(8, 4))  # Parkinson volatility estimator
    
    # Market regime indicators
    volatility_regime = Column(String(20))  # low, medium, high
    trend_regime = Column(String(20))  # uptrend, downtrend, sideways
    momentum_regime = Column(String(20))  # strong_positive, weak_positive, neutral, weak_negative, strong_negative
    
    # Data quality and sources
    data_source = Column(String(50), nullable=False)  # polygon, databento, alpha_vantage, etc.
    data_quality_score = Column(NUMERIC(3, 2), default=1.0)  # 0.0 to 1.0
    is_adjusted = Column(Boolean, default=False)  # Price adjusted for splits/dividends
    adjustment_factor = Column(NUMERIC(10, 6), default=1.0)  # Adjustment factor applied
    
    # Exchange and market info
    exchange = Column(String(10))  # NYSE, NASDAQ, etc.
    market_cap = Column(BigInteger)  # Market capitalization
    shares_outstanding = Column(BigInteger)  # Shares outstanding
    float_shares = Column(BigInteger)  # Float shares
    
    # Corporate actions flags
    has_dividend = Column(Boolean, default=False)  # Dividend payment on this date
    has_split = Column(Boolean, default=False)  # Stock split on this date
    has_earnings = Column(Boolean, default=False)  # Earnings announcement
    
    # Alternative data
    social_sentiment = Column(NUMERIC(5, 2))  # Social media sentiment score (-100 to 100)
    news_sentiment = Column(NUMERIC(5, 2))  # News sentiment score
    analyst_rating_avg = Column(NUMERIC(3, 1))  # Average analyst rating (1-5)
    analyst_price_target_avg = Column(NUMERIC(12, 4))  # Average price target
    
    # Metadata
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    
    # TimescaleDB optimized indexes
    __table_args__ = (
        Index('idx_enhanced_market_data_symbol_time', 'symbol', 'time'),
        Index('idx_enhanced_market_data_time', 'time'),
        Index('idx_enhanced_market_data_source', 'data_source', 'time'),
        Index('idx_enhanced_market_data_volume', 'volume', 'time'),
        # TimescaleDB hypertable will be configured in migration
        {'timescaledb_hypertable': {
            'time_column_name': 'time',
            'chunk_time_interval': '1 day'
        }}
    )
    
    @hybrid_property
    def price_change(self):
        """Calculate price change from open to close"""
        if self.open and self.close:
            return self.close - self.open
        return None
    
    @hybrid_property
    def price_change_percent(self):
        """Calculate percentage price change"""
        if self.open and self.close and self.open != 0:
            return ((self.close - self.open) / self.open) * 100
        return None
    
    @property
    def is_volatile_day(self) -> bool:
        """Determine if this was a volatile trading day"""
        if not self.high or not self.low or not self.close:
            return False
        daily_range = (self.high - self.low) / self.close
        return daily_range > 0.03  # More than 3% daily range
    
    def __repr__(self):
        return f"<EnhancedMarketData(symbol={self.symbol}, time={self.time}, close={self.close})>"


# Additional models for regulatory compliance and audit trails
class UserActivityLog(Base):
    """
    Comprehensive audit log for user activities and system interactions
    """
    __tablename__ = 'user_activity_log'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('enhanced_users.id'))
    
    # Activity details
    activity_type = Column(String(50), nullable=False)  # login, trade, portfolio_view, etc.
    activity_category = Column(String(30))  # authentication, trading, reporting, etc.
    description = Column(String(500))
    
    # Request details
    ip_address = Column(String(45))  # IPv4 or IPv6
    user_agent = Column(String(500))
    request_id = Column(UUID(as_uuid=True))
    session_id = Column(String(100))
    
    # Data changes (for audit)
    before_data = Column(JSONB)  # State before change
    after_data = Column(JSONB)  # State after change
    affected_entities = Column(ARRAY(String(100)))  # Entity IDs affected
    
    # Result and status
    status = Column(String(20))  # success, failure, partial
    error_code = Column(String(50))
    error_message = Column(String(500))
    
    # Timing
    timestamp = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    duration_ms = Column(Integer)  # Activity duration in milliseconds
    
    # Compliance flags
    requires_notification = Column(Boolean, default=False)  # Regulatory notification required
    is_suspicious = Column(Boolean, default=False)  # Flagged as suspicious activity
    compliance_reviewed = Column(Boolean, default=False)  # Reviewed by compliance
    
    __table_args__ = (
        Index('idx_user_activity_log_user_timestamp', 'user_id', 'timestamp'),
        Index('idx_user_activity_log_type_timestamp', 'activity_type', 'timestamp'),
        Index('idx_user_activity_log_suspicious', 'is_suspicious', 'timestamp'),
    )


class RegulatoryReport(Base):
    """
    Storage for regulatory reports and compliance documentation
    """
    __tablename__ = 'regulatory_reports'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Report identification
    report_type = Column(String(50), nullable=False)  # trade_confirmation, 1099_div, account_statement
    report_subtype = Column(String(50))
    regulatory_framework = Column(String(30))  # finra, sec, irs, cftc
    
    # Affected entities
    user_id = Column(UUID(as_uuid=True), ForeignKey('enhanced_users.id'))
    account_id = Column(UUID(as_uuid=True), ForeignKey('enhanced_accounts.id'))
    portfolio_id = Column(UUID(as_uuid=True), ForeignKey('enhanced_portfolios.id'))
    
    # Report content
    report_data = Column(JSONB, nullable=False)  # Structured report data
    generated_document_url = Column(String(500))  # Link to PDF/document
    document_hash = Column(String(64))  # SHA-256 hash for integrity
    
    # Periods and timing
    reporting_period_start = Column(DateTime(timezone=True))
    reporting_period_end = Column(DateTime(timezone=True))
    due_date = Column(DateTime(timezone=True))
    generated_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    
    # Status tracking
    status = Column(String(30), default='draft')  # draft, finalized, submitted, acknowledged
    submission_method = Column(String(30))  # electronic, mail, portal
    submitted_at = Column(DateTime(timezone=True))
    acknowledged_at = Column(DateTime(timezone=True))
    
    # Compliance verification
    compliance_approved = Column(Boolean, default=False)
    approved_by = Column(String(100))
    approved_at = Column(DateTime(timezone=True))
    
    __table_args__ = (
        Index('idx_regulatory_report_user_type', 'user_id', 'report_type'),
        Index('idx_regulatory_report_period', 'reporting_period_start', 'reporting_period_end'),
        Index('idx_regulatory_report_status', 'status', 'due_date'),
    )