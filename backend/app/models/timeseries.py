"""
Time-series database models with TimescaleDB optimization

These models are designed to work with TimescaleDB for efficient time-series data storage
and querying, particularly for market data and portfolio performance tracking.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    Column, String, Integer, DateTime, Boolean, DECIMAL, 
    BigInteger, ForeignKey, Index, text
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, NUMERIC, TIMESTAMP
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property

from app.database.base import Base


class MarketData(Base):
    """
    Time-series market data optimized for TimescaleDB
    This table will be converted to a hypertable for efficient time-series operations
    """
    __tablename__ = 'market_data_legacy'  # Legacy table, use enhanced_market_data for new implementations
    
    # Composite primary key for time-series data
    time = Column(TIMESTAMP(timezone=True), primary_key=True)
    symbol = Column(String(20), primary_key=True, index=True)
    
    # OHLCV data
    open = Column(NUMERIC(12, 4))
    high = Column(NUMERIC(12, 4))
    low = Column(NUMERIC(12, 4))
    close = Column(NUMERIC(12, 4), nullable=False)
    volume = Column(BigInteger)
    
    # Additional market metrics
    vwap = Column(NUMERIC(12, 4))  # Volume Weighted Average Price
    bid = Column(NUMERIC(12, 4))
    ask = Column(NUMERIC(12, 4))
    spread = Column(NUMERIC(8, 4))
    
    # Market indicators
    rsi = Column(NUMERIC(6, 2))  # Relative Strength Index
    macd = Column(NUMERIC(8, 4))  # MACD
    bollinger_upper = Column(NUMERIC(12, 4))
    bollinger_lower = Column(NUMERIC(12, 4))
    
    # Data quality and source
    data_source = Column(String(50))  # polygon, alpha_vantage, etc.
    data_quality_score = Column(NUMERIC(3, 2))  # 0.0 to 1.0
    is_adjusted = Column(Boolean, default=False)
    
    # Metadata
    created_at = Column(TIMESTAMP(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    __table_args__ = (
        Index('idx_market_data_symbol_time', 'symbol', 'time'),
        Index('idx_market_data_time', 'time'),
        Index('idx_market_data_created_at', 'created_at'),
        # TimescaleDB hypertable configuration will be handled in database setup
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
    
    def __repr__(self):
        return f"<MarketData(symbol={self.symbol}, time={self.time}, close={self.close})>"


class PortfolioPerformanceTimeseries(Base):
    """
    Time-series portfolio performance tracking
    Hypertable optimized for portfolio value and performance metrics over time
    """
    __tablename__ = 'portfolio_performance_timeseries'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timestamp = Column(TIMESTAMP(timezone=True), nullable=False, index=True)
    portfolio_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Portfolio values
    total_value = Column(NUMERIC(15, 2), nullable=False)
    cash_balance = Column(NUMERIC(15, 2), default=0)
    invested_value = Column(NUMERIC(15, 2), default=0)
    
    # Performance metrics
    daily_return = Column(NUMERIC(8, 4))
    cumulative_return = Column(NUMERIC(8, 4))
    ytd_return = Column(NUMERIC(8, 4))
    
    # Risk metrics
    volatility = Column(NUMERIC(6, 4))  # Annualized volatility
    sharpe_ratio = Column(NUMERIC(6, 4))
    max_drawdown = Column(NUMERIC(6, 4))
    beta = Column(NUMERIC(6, 4))
    
    # Asset allocation breakdown (stored as JSONB)
    allocation = Column(JSONB)  # {"stocks": 60.5, "bonds": 30.0, "cash": 9.5}
    
    # Benchmark comparison
    benchmark_return = Column(NUMERIC(8, 4))
    alpha = Column(NUMERIC(6, 4))  # Portfolio alpha vs benchmark
    tracking_error = Column(NUMERIC(6, 4))
    
    # Data source and quality
    calculation_method = Column(String(50), default='time_weighted')
    confidence_score = Column(NUMERIC(3, 2))  # Data confidence
    
    # Metadata
    created_at = Column(TIMESTAMP(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    __table_args__ = (
        Index('idx_portfolio_perf_portfolio_time', 'portfolio_id', 'timestamp'),
        Index('idx_portfolio_perf_timestamp', 'timestamp'),
        Index('idx_portfolio_perf_created_at', 'created_at'),
    )
    
    def __repr__(self):
        return f"<PortfolioPerformance(portfolio_id={self.portfolio_id}, timestamp={self.timestamp}, value=${self.total_value})>"


class SimulationResultTimeseries(Base):
    """
    Time-series storage for Monte Carlo simulation results
    Optimized for storing large volumes of simulation data
    """
    __tablename__ = 'simulation_results_timeseries'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(TIMESTAMP(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    
    # Simulation identification
    plan_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    simulation_batch_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    simulation_run = Column(Integer, nullable=False)  # Which run in the batch (1 to N)
    
    # Time horizon data
    year = Column(Integer, nullable=False)  # Year in simulation (1 to planning_horizon)
    quarter = Column(Integer)  # Quarter within the year (1-4)
    
    # Portfolio values at this time point
    portfolio_value = Column(NUMERIC(15, 2), nullable=False)
    cash_flow = Column(NUMERIC(15, 2), default=0)
    withdrawal = Column(NUMERIC(15, 2), default=0)
    contribution = Column(NUMERIC(15, 2), default=0)
    
    # Asset class breakdown
    asset_values = Column(JSONB)  # {"stocks": 500000, "bonds": 200000, ...}
    
    # Returns and performance for this period
    period_return = Column(NUMERIC(8, 4))
    cumulative_return = Column(NUMERIC(8, 4))
    
    # Scenario conditions
    market_scenario = Column(String(50))  # "bull", "bear", "normal", "recession"
    inflation_rate = Column(NUMERIC(6, 4))
    interest_rate = Column(NUMERIC(6, 4))
    
    # Goal tracking
    goal_progress = Column(JSONB)  # Progress toward various goals
    probability_of_success = Column(NUMERIC(5, 4))  # At this point in time
    
    # Simulation metadata
    random_seed = Column(BigInteger)  # For reproducibility
    algorithm_version = Column(String(20))
    computation_time_ms = Column(Integer)
    
    __table_args__ = (
        Index('idx_simulation_plan_batch', 'plan_id', 'simulation_batch_id'),
        Index('idx_simulation_batch_run', 'simulation_batch_id', 'simulation_run'),
        Index('idx_simulation_year', 'plan_id', 'year'),
        Index('idx_simulation_created_at', 'created_at'),
    )
    
    def __repr__(self):
        return f"<SimulationResult(plan_id={self.plan_id}, year={self.year}, value=${self.portfolio_value})>"


class EconomicIndicatorTimeseries(Base):
    """
    Time-series economic indicators and market conditions
    Used for scenario generation and market regime detection
    """
    __tablename__ = 'economic_indicators_timeseries'
    
    time = Column(TIMESTAMP(timezone=True), primary_key=True)
    indicator_name = Column(String(100), primary_key=True)
    
    # Indicator values
    value = Column(NUMERIC(12, 6), nullable=False)
    previous_value = Column(NUMERIC(12, 6))
    
    # Change metrics
    period_change = Column(NUMERIC(8, 4))
    period_change_percent = Column(NUMERIC(8, 4))
    
    # Statistical measures
    z_score = Column(NUMERIC(8, 4))  # How many standard deviations from mean
    percentile = Column(NUMERIC(5, 2))  # Historical percentile
    
    # Data source and quality
    data_source = Column(String(50))
    data_frequency = Column(String(20))  # daily, weekly, monthly, quarterly
    revision_number = Column(Integer, default=0)  # For revised economic data
    is_preliminary = Column(Boolean, default=False)
    
    # Metadata
    unit = Column(String(50))  # "percent", "billions_usd", etc.
    seasonal_adjustment = Column(String(20))  # "seasonally_adjusted", "not_adjusted"
    created_at = Column(TIMESTAMP(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    __table_args__ = (
        Index('idx_economic_indicator_name_time', 'indicator_name', 'time'),
        Index('idx_economic_indicator_time', 'time'),
    )
    
    def __repr__(self):
        return f"<EconomicIndicator(name={self.indicator_name}, time={self.time}, value={self.value})>"


class MarketRegimeTimeseries(Base):
    """
    Market regime classification over time
    Used for regime-aware modeling and analysis
    """
    __tablename__ = 'market_regimes_timeseries'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    start_date = Column(TIMESTAMP(timezone=True), nullable=False, index=True)
    end_date = Column(TIMESTAMP(timezone=True), index=True)  # NULL for current regime
    
    # Regime classification
    regime_type = Column(String(50), nullable=False)  # "bull_market", "bear_market", "recession", etc.
    confidence = Column(NUMERIC(5, 4), nullable=False)  # Model confidence in classification
    
    # Regime characteristics
    avg_volatility = Column(NUMERIC(6, 4))
    avg_return = Column(NUMERIC(8, 4))
    max_drawdown = Column(NUMERIC(6, 4))
    
    # Economic context
    primary_drivers = Column(JSONB)  # ["inflation", "interest_rates", "geopolitical"]
    economic_indicators = Column(JSONB)  # Key economic indicators during this regime
    
    # Model information
    detection_algorithm = Column(String(100))  # Algorithm used to detect regime
    model_version = Column(String(20))
    detected_at = Column(TIMESTAMP(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # Validation
    is_confirmed = Column(Boolean, default=False)  # Whether regime is confirmed or preliminary
    confirmed_at = Column(TIMESTAMP(timezone=True))
    
    __table_args__ = (
        Index('idx_market_regime_dates', 'start_date', 'end_date'),
        Index('idx_market_regime_type', 'regime_type'),
    )
    
    def __repr__(self):
        return f"<MarketRegime(type={self.regime_type}, start={self.start_date}, confidence={self.confidence})>"


# Continuous aggregate views for TimescaleDB (created via SQL)
class HourlyMarketSummaryView(Base):
    """
    Materialized view for hourly market data aggregates
    This will be created as a TimescaleDB continuous aggregate
    """
    __tablename__ = 'hourly_market_summary_view'
    
    bucket = Column(TIMESTAMP(timezone=True), primary_key=True)
    symbol = Column(String(20), primary_key=True)
    
    # OHLCV aggregates
    open_price = Column(NUMERIC(12, 4))
    high_price = Column(NUMERIC(12, 4))
    low_price = Column(NUMERIC(12, 4))
    close_price = Column(NUMERIC(12, 4))
    total_volume = Column(BigInteger)
    avg_price = Column(NUMERIC(12, 4))
    
    # Additional metrics
    price_volatility = Column(NUMERIC(8, 4))
    trade_count = Column(Integer)
    
    __table_args__ = (
        Index('idx_hourly_summary_symbol_bucket', 'symbol', 'bucket'),
    )


class DailyPortfolioSummaryView(Base):
    """
    Materialized view for daily portfolio performance aggregates
    """
    __tablename__ = 'daily_portfolio_summary_view'
    
    bucket = Column(TIMESTAMP(timezone=True), primary_key=True)
    portfolio_id = Column(UUID(as_uuid=True), primary_key=True)
    
    # Daily aggregates
    start_value = Column(NUMERIC(15, 2))
    end_value = Column(NUMERIC(15, 2))
    min_value = Column(NUMERIC(15, 2))
    max_value = Column(NUMERIC(15, 2))
    avg_value = Column(NUMERIC(15, 2))
    
    # Performance metrics
    daily_return = Column(NUMERIC(8, 4))
    volatility = Column(NUMERIC(6, 4))
    
    __table_args__ = (
        Index('idx_daily_portfolio_summary_portfolio_bucket', 'portfolio_id', 'bucket'),
    )