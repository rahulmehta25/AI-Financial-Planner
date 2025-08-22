"""
Market Data Models

Data models for market data streaming system.
"""

from typing import Dict, List, Optional, Any, Union
from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from pydantic import BaseModel, Field, validator
import uuid


class MarketDataType(str, Enum):
    """Types of market data"""
    QUOTE = "quote"
    HISTORICAL = "historical"
    INTRADAY = "intraday"
    NEWS = "news"
    FUNDAMENTALS = "fundamentals"


class DataProvider(str, Enum):
    """Market data providers"""
    ALPHA_VANTAGE = "alpha_vantage"
    YAHOO_FINANCE = "yahoo_finance"
    IEX_CLOUD = "iex_cloud"


class AlertType(str, Enum):
    """Types of price alerts"""
    PRICE_ABOVE = "price_above"
    PRICE_BELOW = "price_below"
    PRICE_CHANGE_PERCENT = "price_change_percent"
    VOLUME_SPIKE = "volume_spike"
    MOVING_AVERAGE_CROSS = "moving_average_cross"


class AlertStatus(str, Enum):
    """Alert status"""
    ACTIVE = "active"
    TRIGGERED = "triggered"
    DISABLED = "disabled"
    EXPIRED = "expired"


class MarketDataPoint(BaseModel):
    """Single market data point"""
    
    symbol: str = Field(..., description="Stock symbol")
    timestamp: datetime = Field(..., description="Data timestamp")
    
    # Price data
    open_price: Optional[Decimal] = Field(None, description="Opening price")
    high_price: Optional[Decimal] = Field(None, description="High price")
    low_price: Optional[Decimal] = Field(None, description="Low price")
    close_price: Optional[Decimal] = Field(None, description="Closing price")
    current_price: Optional[Decimal] = Field(None, description="Current price")
    
    # Volume and market data
    volume: Optional[int] = Field(None, description="Trading volume")
    market_cap: Optional[Decimal] = Field(None, description="Market capitalization")
    
    # Calculated fields
    price_change: Optional[Decimal] = Field(None, description="Price change from previous close")
    price_change_percent: Optional[Decimal] = Field(None, description="Price change percentage")
    
    # Metadata
    data_type: MarketDataType = Field(..., description="Type of market data")
    provider: DataProvider = Field(..., description="Data provider")
    is_real_time: bool = Field(False, description="Is real-time data")
    
    # Additional data (provider-specific)
    additional_data: Dict[str, Any] = Field(default_factory=dict, description="Additional provider data")
    
    class Config:
        json_encoders = {
            Decimal: str,
            datetime: lambda v: v.isoformat(),
        }
    
    @validator('symbol')
    def validate_symbol(cls, v):
        """Validate stock symbol format"""
        if not v or len(v.strip()) == 0:
            raise ValueError("Symbol cannot be empty")
        return v.upper().strip()
    
    @validator('current_price', 'open_price', 'high_price', 'low_price', 'close_price')
    def validate_prices(cls, v):
        """Validate price values"""
        if v is not None and v < 0:
            raise ValueError("Price cannot be negative")
        return v
    
    @validator('volume')
    def validate_volume(cls, v):
        """Validate volume"""
        if v is not None and v < 0:
            raise ValueError("Volume cannot be negative")
        return v


class HistoricalData(BaseModel):
    """Historical market data"""
    
    symbol: str = Field(..., description="Stock symbol")
    start_date: date = Field(..., description="Start date")
    end_date: date = Field(..., description="End date")
    data_points: List[MarketDataPoint] = Field(..., description="Historical data points")
    provider: DataProvider = Field(..., description="Data provider")
    
    class Config:
        json_encoders = {
            date: lambda v: v.isoformat(),
        }


class CompanyInfo(BaseModel):
    """Company information"""
    
    symbol: str = Field(..., description="Stock symbol")
    name: str = Field(..., description="Company name")
    sector: Optional[str] = Field(None, description="Company sector")
    industry: Optional[str] = Field(None, description="Company industry")
    description: Optional[str] = Field(None, description="Company description")
    website: Optional[str] = Field(None, description="Company website")
    market_cap: Optional[Decimal] = Field(None, description="Market capitalization")
    employees: Optional[int] = Field(None, description="Number of employees")
    exchange: Optional[str] = Field(None, description="Stock exchange")
    country: Optional[str] = Field(None, description="Company country")
    provider: DataProvider = Field(..., description="Data provider")
    last_updated: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")


class AlertConfig(BaseModel):
    """Alert configuration"""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Alert ID")
    user_id: str = Field(..., description="User ID")
    symbol: str = Field(..., description="Stock symbol")
    alert_type: AlertType = Field(..., description="Type of alert")
    
    # Alert parameters
    threshold_value: Optional[Decimal] = Field(None, description="Threshold value for alert")
    percentage_threshold: Optional[Decimal] = Field(None, description="Percentage threshold")
    
    # Alert settings
    is_active: bool = Field(True, description="Is alert active")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    expires_at: Optional[datetime] = Field(None, description="Expiration timestamp")
    
    # Notification settings
    email_notification: bool = Field(True, description="Send email notification")
    push_notification: bool = Field(False, description="Send push notification")
    webhook_url: Optional[str] = Field(None, description="Webhook URL for notification")
    
    # Alert message
    custom_message: Optional[str] = Field(None, description="Custom alert message")
    
    @validator('symbol')
    def validate_symbol(cls, v):
        """Validate stock symbol format"""
        return v.upper().strip()
    
    @validator('threshold_value', 'percentage_threshold')
    def validate_thresholds(cls, v):
        """Validate threshold values"""
        if v is not None and v < 0:
            raise ValueError("Threshold values cannot be negative")
        return v


class PriceAlert(BaseModel):
    """Triggered price alert"""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Alert instance ID")
    alert_config_id: str = Field(..., description="Alert configuration ID")
    user_id: str = Field(..., description="User ID")
    symbol: str = Field(..., description="Stock symbol")
    alert_type: AlertType = Field(..., description="Type of alert")
    
    # Trigger data
    trigger_price: Decimal = Field(..., description="Price that triggered alert")
    trigger_value: Optional[Decimal] = Field(None, description="Value that triggered alert")
    trigger_timestamp: datetime = Field(default_factory=datetime.utcnow, description="Trigger timestamp")
    
    # Alert status
    status: AlertStatus = Field(AlertStatus.TRIGGERED, description="Alert status")
    
    # Notification status
    email_sent: bool = Field(False, description="Email notification sent")
    push_sent: bool = Field(False, description="Push notification sent")
    webhook_sent: bool = Field(False, description="Webhook notification sent")
    
    # Message
    message: str = Field(..., description="Alert message")
    
    class Config:
        json_encoders = {
            Decimal: str,
            datetime: lambda v: v.isoformat(),
        }


class MarketDataRequest(BaseModel):
    """Market data request"""
    
    symbols: List[str] = Field(..., description="List of stock symbols")
    data_types: List[MarketDataType] = Field(default=[MarketDataType.QUOTE], description="Types of data to fetch")
    start_date: Optional[date] = Field(None, description="Start date for historical data")
    end_date: Optional[date] = Field(None, description="End date for historical data")
    interval: Optional[str] = Field("1d", description="Data interval (1m, 5m, 1h, 1d, etc.)")
    real_time: bool = Field(False, description="Request real-time data")
    
    @validator('symbols')
    def validate_symbols(cls, v):
        """Validate and normalize symbols"""
        if not v:
            raise ValueError("At least one symbol is required")
        return [symbol.upper().strip() for symbol in v]


class MarketDataResponse(BaseModel):
    """Market data response"""
    
    success: bool = Field(..., description="Request success status")
    data: List[MarketDataPoint] = Field(default_factory=list, description="Market data points")
    errors: List[str] = Field(default_factory=list, description="Error messages")
    provider: DataProvider = Field(..., description="Data provider used")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
    cached: bool = Field(False, description="Data served from cache")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


class WebSocketMessage(BaseModel):
    """WebSocket message format"""
    
    type: str = Field(..., description="Message type")
    symbol: Optional[str] = Field(None, description="Stock symbol")
    data: Optional[Union[MarketDataPoint, List[MarketDataPoint], Dict[str, Any]]] = Field(None, description="Message data")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Message timestamp")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }