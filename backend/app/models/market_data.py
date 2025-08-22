"""
Market data model for storing historical and real-time market information
"""

import uuid
from datetime import datetime, date
from sqlalchemy import Column, DateTime, String, Numeric, Date, Boolean, Integer, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.database.base import Base


class MarketData(Base):
    __tablename__ = "market_data"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Security Identification
    symbol = Column(String(20), nullable=False, index=True)
    exchange = Column(String(20), nullable=True)
    security_type = Column(String(20), nullable=False)  # stock, bond, etf, mutual_fund, crypto, commodity
    
    # Date and Time
    date = Column(Date, nullable=False, index=True)
    timestamp = Column(DateTime, nullable=True)  # For intraday data
    
    # Price Data
    open_price = Column(Numeric(15, 4), nullable=True)
    high_price = Column(Numeric(15, 4), nullable=True)
    low_price = Column(Numeric(15, 4), nullable=True)
    close_price = Column(Numeric(15, 4), nullable=False)
    adjusted_close = Column(Numeric(15, 4), nullable=True)  # Adjusted for splits/dividends
    
    # Volume and Market Data
    volume = Column(Numeric(20, 0), nullable=True)
    market_cap = Column(Numeric(20, 2), nullable=True)
    shares_outstanding = Column(Numeric(20, 0), nullable=True)
    
    # Financial Ratios and Metrics
    pe_ratio = Column(Numeric(8, 2), nullable=True)
    pb_ratio = Column(Numeric(8, 2), nullable=True)
    dividend_yield = Column(Numeric(6, 4), nullable=True)
    dividend_amount = Column(Numeric(10, 4), nullable=True)
    eps = Column(Numeric(10, 4), nullable=True)  # Earnings per share
    
    # Technical Indicators
    sma_20 = Column(Numeric(15, 4), nullable=True)  # 20-day simple moving average
    sma_50 = Column(Numeric(15, 4), nullable=True)  # 50-day simple moving average
    sma_200 = Column(Numeric(15, 4), nullable=True)  # 200-day simple moving average
    rsi = Column(Numeric(6, 2), nullable=True)  # Relative Strength Index
    beta = Column(Numeric(6, 4), nullable=True)  # Beta coefficient
    
    # Volatility Metrics
    daily_return = Column(Numeric(8, 6), nullable=True)  # Daily return percentage
    volatility_30d = Column(Numeric(6, 4), nullable=True)  # 30-day volatility
    volatility_90d = Column(Numeric(6, 4), nullable=True)  # 90-day volatility
    volatility_1y = Column(Numeric(6, 4), nullable=True)  # 1-year volatility
    
    # Economic Indicators (for market indices)
    inflation_rate = Column(Numeric(6, 4), nullable=True)
    interest_rate = Column(Numeric(6, 4), nullable=True)  # Risk-free rate
    gdp_growth = Column(Numeric(6, 4), nullable=True)
    unemployment_rate = Column(Numeric(6, 4), nullable=True)
    
    # Fund-Specific Data
    expense_ratio = Column(Numeric(6, 4), nullable=True)  # For ETFs/Mutual Funds
    aum = Column(Numeric(20, 2), nullable=True)  # Assets under management
    nav = Column(Numeric(15, 4), nullable=True)  # Net asset value
    
    # Additional Metadata
    currency = Column(String(3), default="USD")
    data_source = Column(String(50), nullable=False)  # yahoo, alpha_vantage, iex, etc.
    data_quality = Column(String(20), default="good")  # good, fair, poor, estimated
    is_adjusted = Column(Boolean, default=False)  # Is data adjusted for corporate actions
    
    # Corporate Actions
    split_ratio = Column(Numeric(10, 6), nullable=True)  # Stock split ratio
    dividend_ex_date = Column(Date, nullable=True)
    
    # Sector and Industry Classification
    sector = Column(String(50), nullable=True)
    industry = Column(String(100), nullable=True)
    gics_sector = Column(String(50), nullable=True)
    gics_industry = Column(String(100), nullable=True)
    
    # Additional Data
    extended_data = Column(JSONB, nullable=True)  # Store additional metrics
    news_sentiment = Column(Numeric(3, 2), nullable=True)  # Sentiment score -1 to 1
    analyst_rating = Column(String(20), nullable=True)  # buy, hold, sell
    price_target = Column(Numeric(15, 4), nullable=True)  # Analyst price target
    
    # Data Status
    is_active = Column(Boolean, default=True)
    is_delisted = Column(Boolean, default=False)
    last_updated = Column(DateTime, default=datetime.utcnow)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Create composite indexes for efficient querying
    __table_args__ = (
        Index('idx_symbol_date', 'symbol', 'date'),
        Index('idx_date_symbol', 'date', 'symbol'),
        Index('idx_symbol_type', 'symbol', 'security_type'),
    )

    @property
    def price_change(self) -> float:
        """Calculate price change from open to close"""
        if self.open_price and self.close_price:
            return float(self.close_price) - float(self.open_price)
        return 0.0

    @property
    def price_change_percentage(self) -> float:
        """Calculate percentage price change"""
        if self.open_price and self.open_price != 0:
            return (self.price_change / float(self.open_price)) * 100
        return 0.0

    @property
    def trading_range(self) -> float:
        """Calculate trading range (high - low)"""
        if self.high_price and self.low_price:
            return float(self.high_price) - float(self.low_price)
        return 0.0

    @property
    def is_recent_data(self) -> bool:
        """Check if data is from recent trading session"""
        days_old = (date.today() - self.date).days
        return days_old <= 7  # Consider data recent if within a week

    def calculate_volatility(self, price_history: list) -> float:
        """Calculate volatility from price history"""
        if len(price_history) < 2:
            return 0.0
        
        import numpy as np
        returns = []
        for i in range(1, len(price_history)):
            if price_history[i-1] != 0:
                returns.append((price_history[i] - price_history[i-1]) / price_history[i-1])
        
        if returns:
            return float(np.std(returns) * np.sqrt(252))  # Annualized volatility
        return 0.0