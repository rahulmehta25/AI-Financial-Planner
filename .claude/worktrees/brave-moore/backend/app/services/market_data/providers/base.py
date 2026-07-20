"""
Base Provider Class

Abstract base class for all market data providers.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any
from datetime import datetime, date
import asyncio
import time
from collections import defaultdict
import logging

from ..models import MarketDataPoint, MarketDataType, DataProvider, HistoricalData, CompanyInfo
from ..config import config


class RateLimiter:
    """Rate limiter for API requests"""
    
    def __init__(self, requests_per_minute: int):
        self.requests_per_minute = requests_per_minute
        self.requests = []
        self.lock = asyncio.Lock()
    
    async def wait_if_needed(self):
        """Wait if rate limit would be exceeded"""
        async with self.lock:
            now = time.time()
            # Remove requests older than 1 minute
            self.requests = [req_time for req_time in self.requests if now - req_time < 60]
            
            if len(self.requests) >= self.requests_per_minute:
                # Calculate wait time until oldest request is older than 1 minute
                wait_time = 60 - (now - self.requests[0])
                if wait_time > 0:
                    await asyncio.sleep(wait_time)
                    # Clean up again after waiting
                    now = time.time()
                    self.requests = [req_time for req_time in self.requests if now - req_time < 60]
            
            self.requests.append(now)


class BaseProvider(ABC):
    """Abstract base class for market data providers"""
    
    def __init__(self, provider: DataProvider, rate_limit: int = 60):
        self.provider = provider
        self.rate_limiter = RateLimiter(rate_limit)
        self.logger = logging.getLogger(f"market_data.{provider.value}")
        self._session = None
        self._error_count = defaultdict(int)
        self._last_error_reset = time.time()
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self._initialize_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self._cleanup_session()
    
    @abstractmethod
    async def _initialize_session(self):
        """Initialize HTTP session"""
        pass
    
    @abstractmethod
    async def _cleanup_session(self):
        """Cleanup HTTP session"""
        pass
    
    @abstractmethod
    async def get_quote(self, symbol: str) -> Optional[MarketDataPoint]:
        """Get current quote for a symbol"""
        pass
    
    @abstractmethod
    async def get_historical_data(
        self, 
        symbol: str, 
        start_date: date, 
        end_date: date,
        interval: str = "1d"
    ) -> Optional[HistoricalData]:
        """Get historical data for a symbol"""
        pass
    
    @abstractmethod
    async def get_company_info(self, symbol: str) -> Optional[CompanyInfo]:
        """Get company information for a symbol"""
        pass
    
    async def get_multiple_quotes(self, symbols: List[str]) -> List[MarketDataPoint]:
        """Get quotes for multiple symbols"""
        quotes = []
        
        # Use semaphore to limit concurrent requests
        semaphore = asyncio.Semaphore(config.max_concurrent_requests)
        
        async def fetch_quote(symbol: str):
            async with semaphore:
                try:
                    quote = await self.get_quote(symbol)
                    if quote:
                        quotes.append(quote)
                except Exception as e:
                    self.logger.error(f"Error fetching quote for {symbol}: {e}")
                    self._record_error(symbol)
        
        # Execute requests concurrently
        tasks = [fetch_quote(symbol) for symbol in symbols]
        await asyncio.gather(*tasks, return_exceptions=True)
        
        return quotes
    
    def _record_error(self, symbol: str):
        """Record error for monitoring"""
        now = time.time()
        
        # Reset error counts every hour
        if now - self._last_error_reset > 3600:
            self._error_count.clear()
            self._last_error_reset = now
        
        self._error_count[symbol] += 1
        
        if self._error_count[symbol] > 5:
            self.logger.warning(f"High error rate for {symbol}: {self._error_count[symbol]} errors")
    
    def get_error_count(self, symbol: str = None) -> int:
        """Get error count for symbol or total"""
        if symbol:
            return self._error_count.get(symbol, 0)
        return sum(self._error_count.values())
    
    async def health_check(self) -> bool:
        """Check if provider is healthy"""
        try:
            # Try to fetch a quote for a common symbol
            test_quote = await self.get_quote("AAPL")
            return test_quote is not None
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return False
    
    def _validate_price_data(self, data: Dict[str, Any]) -> bool:
        """Validate price data for anomalies"""
        if not config.validate_price_changes:
            return True
        
        try:
            current = float(data.get('current_price', 0))
            previous = float(data.get('previous_close', 0))
            
            if previous > 0:
                change_percent = abs((current - previous) / previous * 100)
                if change_percent > config.max_price_change_percent:
                    self.logger.warning(
                        f"Suspicious price change: {change_percent:.2f}% for {data.get('symbol')}"
                    )
                    return False
            
            return True
        except (ValueError, TypeError, ZeroDivisionError):
            return False
    
    @property
    def name(self) -> str:
        """Provider name"""
        return self.provider.value