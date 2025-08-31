"""
Base classes and interfaces for market data providers
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from datetime import datetime, date
from decimal import Decimal
from dataclasses import dataclass
from enum import Enum


class DataProviderStatus(Enum):
    """Status of a data provider"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"


@dataclass
class Quote:
    """Market quote data"""
    symbol: str
    price: Decimal
    open: Optional[Decimal] = None
    high: Optional[Decimal] = None
    low: Optional[Decimal] = None
    close: Optional[Decimal] = None
    volume: Optional[int] = None
    timestamp: Optional[datetime] = None
    source: str = "unknown"
    is_delayed: bool = True
    delay_minutes: int = 15


@dataclass
class HistoricalBar:
    """Historical price bar"""
    date: date
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    adj_close: Optional[Decimal] = None
    volume: int = 0


@dataclass
class DividendInfo:
    """Dividend information"""
    ex_date: date
    amount: Decimal
    payment_date: Optional[date] = None
    record_date: Optional[date] = None


@dataclass
class SplitInfo:
    """Stock split information"""
    date: date
    ratio: Decimal  # e.g., 2.0 for 2:1 split


class DataProvider(ABC):
    """Abstract base class for market data providers"""
    
    def __init__(self, name: str):
        self.name = name
        self._status = DataProviderStatus.HEALTHY
        self._last_error: Optional[str] = None
        self._last_success: Optional[datetime] = None
    
    @abstractmethod
    async def get_quote(self, symbol: str) -> Optional[Quote]:
        """Get current quote for a symbol"""
        pass
    
    @abstractmethod
    async def get_quotes(self, symbols: List[str]) -> Dict[str, Optional[Quote]]:
        """Get quotes for multiple symbols"""
        pass
    
    @abstractmethod
    async def get_historical(
        self,
        symbol: str,
        start_date: date,
        end_date: date,
        interval: str = "1d"
    ) -> List[HistoricalBar]:
        """Get historical price data"""
        pass
    
    @abstractmethod
    async def get_dividends(
        self,
        symbol: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[DividendInfo]:
        """Get dividend history"""
        pass
    
    @abstractmethod
    async def get_splits(
        self,
        symbol: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[SplitInfo]:
        """Get stock split history"""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if provider is healthy"""
        pass
    
    @property
    def status(self) -> DataProviderStatus:
        """Get current provider status"""
        return self._status
    
    @property
    def last_error(self) -> Optional[str]:
        """Get last error message"""
        return self._last_error
    
    @property
    def last_success(self) -> Optional[datetime]:
        """Get timestamp of last successful request"""
        return self._last_success
    
    def _set_healthy(self):
        """Mark provider as healthy"""
        self._status = DataProviderStatus.HEALTHY
        self._last_success = datetime.utcnow()
        self._last_error = None
    
    def _set_error(self, error: str):
        """Record an error"""
        self._last_error = error
        # Don't immediately mark as unavailable - let circuit breaker decide