"""
Market Data Schemas
API response models for market data endpoints
"""

from typing import List, Optional, Dict, Any, Union
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel, Field, validator
from enum import Enum


class TimePeriod(str, Enum):
    """Time periods for historical data"""
    ONE_DAY = "1D"
    ONE_WEEK = "1W"
    ONE_MONTH = "1M"
    THREE_MONTHS = "3M"
    ONE_YEAR = "1Y"
    FIVE_YEARS = "5Y"
    MAX = "MAX"


class IntervalType(str, Enum):
    """Data interval types"""
    ONE_MINUTE = "1m"
    FIVE_MINUTES = "5m"
    FIFTEEN_MINUTES = "15m"
    THIRTY_MINUTES = "30m"
    ONE_HOUR = "1h"
    ONE_DAY = "1d"
    ONE_WEEK = "1wk"
    ONE_MONTH = "1mo"


class MarketDataCreate(BaseModel):
    """Market data creation model"""
    symbol: str = Field(..., description="Stock symbol")
    
    @validator('symbol')
    def validate_symbol(cls, v):
        return v.upper().strip()


class PriceData(BaseModel):
    """Individual price data point"""
    date: str = Field(..., description="Date of the data point")
    timestamp: str = Field(..., description="Full timestamp")
    open: Optional[float] = Field(None, description="Opening price")
    high: Optional[float] = Field(None, description="High price")
    low: Optional[float] = Field(None, description="Low price")
    close: Optional[float] = Field(None, description="Closing price")
    volume: Optional[int] = Field(None, description="Trading volume")


class ComparisonData(BaseModel):
    """S&P 500 comparison data point"""
    date: str = Field(..., description="Date")
    stock_pct_change: float = Field(..., description="Stock percentage change from baseline")
    sp500_pct_change: Optional[float] = Field(None, description="S&P 500 percentage change from baseline")


class SP500ComparisonData(BaseModel):
    """S&P 500 comparison analysis"""
    comparison_data: List[ComparisonData] = Field(..., description="Comparison data points")
    correlation: Optional[float] = Field(None, description="Correlation coefficient with S&P 500")


class HistoricalDataResponse(BaseModel):
    """Historical data response"""
    symbol: str = Field(..., description="Stock symbol")
    start_date: Optional[str] = Field(None, description="Start date")
    end_date: Optional[str] = Field(None, description="End date")
    interval: str = Field(..., description="Data interval")
    data_points: List[PriceData] = Field(..., description="Historical price data")
    provider: str = Field(..., description="Data provider")
    sp500_comparison: Optional[SP500ComparisonData] = Field(None, description="S&P 500 comparison data")


class MovingAverages(BaseModel):
    """Moving averages data"""
    sma_20: Optional[float] = Field(None, description="20-period Simple Moving Average")
    sma_50: Optional[float] = Field(None, description="50-period Simple Moving Average")
    sma_200: Optional[float] = Field(None, description="200-period Simple Moving Average")
    ema_12: Optional[float] = Field(None, description="12-period Exponential Moving Average")
    ema_26: Optional[float] = Field(None, description="26-period Exponential Moving Average")


class MACDData(BaseModel):
    """MACD indicator data"""
    macd: List[Optional[float]] = Field(..., description="MACD line values")
    signal: List[Optional[float]] = Field(..., description="Signal line values")
    histogram: List[Optional[float]] = Field(..., description="MACD histogram values")


class BollingerBandsData(BaseModel):
    """Bollinger Bands data"""
    upper: List[Optional[float]] = Field(..., description="Upper Bollinger Band")
    middle: List[Optional[float]] = Field(..., description="Middle Bollinger Band (SMA)")
    lower: List[Optional[float]] = Field(..., description="Lower Bollinger Band")


class MomentumIndicators(BaseModel):
    """Momentum indicators"""
    rsi: Optional[float] = Field(None, description="Relative Strength Index (current)")
    macd: Optional[MACDData] = Field(None, description="MACD indicator data")


class VolatilityIndicators(BaseModel):
    """Volatility indicators"""
    bollinger_bands: Optional[BollingerBandsData] = Field(None, description="Bollinger Bands data")


class VolumeAnalysis(BaseModel):
    """Volume analysis data"""
    current_volume: Optional[int] = Field(None, description="Current trading volume")
    avg_volume_20: Optional[float] = Field(None, description="20-period average volume")
    volume_ratio: Optional[float] = Field(None, description="Current volume to average ratio")


class TrendAnalysis(BaseModel):
    """Trend analysis results"""
    trend: str = Field(..., description="Overall trend direction")
    strength: int = Field(..., description="Trend strength score")
    signals: List[str] = Field(..., description="Technical analysis signals")


class DetailedIndicators(BaseModel):
    """Detailed indicator series for charting"""
    sma_20_series: List[Optional[float]] = Field(..., description="20-period SMA series")
    sma_50_series: List[Optional[float]] = Field(..., description="50-period SMA series")
    ema_12_series: List[Optional[float]] = Field(..., description="12-period EMA series")
    ema_26_series: List[Optional[float]] = Field(..., description="26-period EMA series")
    rsi_series: List[Optional[float]] = Field(..., description="RSI series")
    macd_series: MACDData = Field(..., description="MACD series")
    bollinger_series: BollingerBandsData = Field(..., description="Bollinger Bands series")
    volume_sma_series: Optional[List[Optional[float]]] = Field(None, description="Volume SMA series")


class PriceDataSummary(BaseModel):
    """Current price data summary"""
    current_price: Optional[float] = Field(None, description="Current price")
    price_change: Optional[float] = Field(None, description="Price change from previous close")
    price_change_percent: Optional[float] = Field(None, description="Price change percentage")


class TechnicalAnalysisResponse(BaseModel):
    """Complete technical analysis response"""
    symbol: str = Field(..., description="Stock symbol")
    period: str = Field(..., description="Analysis period")
    last_updated: str = Field(..., description="Last update timestamp")
    price_data: PriceDataSummary = Field(..., description="Current price information")
    moving_averages: MovingAverages = Field(..., description="Moving averages")
    momentum_indicators: MomentumIndicators = Field(..., description="Momentum indicators")
    volatility_indicators: VolatilityIndicators = Field(..., description="Volatility indicators")
    volume_analysis: VolumeAnalysis = Field(..., description="Volume analysis")
    trend_analysis: TrendAnalysis = Field(..., description="Trend analysis")
    detailed_indicators: DetailedIndicators = Field(..., description="Detailed indicator series")


class MarketDataResponse(BaseModel):
    """Current market data response"""
    symbol: str = Field(..., description="Stock symbol")
    current_price: Optional[float] = Field(None, description="Current price")
    open_price: Optional[float] = Field(None, description="Opening price")
    high_price: Optional[float] = Field(None, description="High price")
    low_price: Optional[float] = Field(None, description="Low price")
    close_price: Optional[float] = Field(None, description="Closing price")
    volume: Optional[int] = Field(None, description="Trading volume")
    price_change: Optional[float] = Field(None, description="Price change")
    price_change_percent: Optional[float] = Field(None, description="Price change percentage")
    timestamp: str = Field(..., description="Data timestamp")
    provider: str = Field(..., description="Data provider")


class SearchResult(BaseModel):
    """Symbol search result"""
    symbol: str = Field(..., description="Stock symbol")
    name: str = Field(..., description="Company name")
    type: Optional[str] = Field(None, description="Security type")
    exchange: Optional[str] = Field(None, description="Exchange")


class SectorPerformance(BaseModel):
    """Sector performance data"""
    sector: str = Field(..., description="Sector name")
    symbol: str = Field(..., description="Sector ETF symbol")
    price: Optional[float] = Field(None, description="Current price")
    change: Optional[float] = Field(None, description="Price change")
    change_percent: Optional[float] = Field(None, description="Price change percentage")


class MarketIndex(BaseModel):
    """Market index data"""
    name: str = Field(..., description="Index name")
    symbol: str = Field(..., description="Index symbol")
    value: Optional[float] = Field(None, description="Current value")
    change: Optional[float] = Field(None, description="Change from previous close")
    change_percent: Optional[float] = Field(None, description="Percentage change")
    timestamp: str = Field(..., description="Last update timestamp")


class EconomicIndicator(BaseModel):
    """Economic indicator data"""
    name: str = Field(..., description="Indicator name")
    symbol: str = Field(..., description="Symbol/ticker")
    value: Optional[float] = Field(None, description="Current value")
    change: Optional[float] = Field(None, description="Change from previous")
    description: str = Field(..., description="Indicator description")


class EconomicIndicatorsResponse(BaseModel):
    """Economic indicators response"""
    last_updated: str = Field(..., description="Last update timestamp")
    indicators: List[EconomicIndicator] = Field(..., description="Economic indicators")


class NewsArticle(BaseModel):
    """News article data"""
    title: str = Field(..., description="Article title")
    summary: Optional[str] = Field(None, description="Article summary")
    url: str = Field(..., description="Article URL")
    publisher: Optional[str] = Field(None, description="Publisher name")
    published_at: Optional[str] = Field(None, description="Publication timestamp")
    type: str = Field(default="news", description="Article type")


class WatchlistResponse(BaseModel):
    """Watchlist response"""
    message: str = Field(..., description="Response message")
    symbols: List[str] = Field(..., description="Symbols in watchlist")
    user_id: int = Field(..., description="User ID")


class ChartRequest(BaseModel):
    """Chart data request"""
    symbol: str = Field(..., description="Stock symbol")
    period: TimePeriod = Field(TimePeriod.ONE_YEAR, description="Time period")
    interval: IntervalType = Field(IntervalType.ONE_DAY, description="Data interval")
    include_sp500: bool = Field(False, description="Include S&P 500 comparison")
    include_technical_indicators: bool = Field(False, description="Include technical indicators")
    
    @validator('symbol')
    def validate_symbol(cls, v):
        return v.upper().strip()


class ChartResponse(BaseModel):
    """Chart data response"""
    symbol: str = Field(..., description="Stock symbol")
    period: str = Field(..., description="Time period")
    interval: str = Field(..., description="Data interval")
    price_data: List[PriceData] = Field(..., description="Price data points")
    sp500_comparison: Optional[SP500ComparisonData] = Field(None, description="S&P 500 comparison")
    technical_indicators: Optional[TechnicalAnalysisResponse] = Field(None, description="Technical indicators")
    last_updated: str = Field(..., description="Last update timestamp")