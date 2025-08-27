"""
Enhanced Yahoo Finance Provider

Robust fallback provider using yfinance library with improved error handling,
caching, rate limiting, and data validation.
"""

import asyncio
import logging
import yfinance as yf
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
import time
from decimal import Decimal

from .base import BaseProvider
from ..models import MarketDataPoint, HistoricalData, CompanyInfo, DataProvider
from ..config import config


class YFinanceEnhancedProvider(BaseProvider):
    """Enhanced Yahoo Finance provider with robust fallback capabilities"""
    
    def __init__(self):
        super().__init__()
        self.name = "Yahoo Finance Enhanced"
        
        # Thread pool for blocking yfinance operations
        self.executor = ThreadPoolExecutor(max_workers=10, thread_name_prefix="yfinance")
        
        # Rate limiting (Yahoo Finance is free but has limits)
        self.requests_per_minute = 60
        self.request_timestamps = []
        
        # Circuit breaker with higher tolerance for free service
        self.failure_count = 0
        self.failure_threshold = 10
        self.reset_timeout = 600  # 10 minutes
        self.last_failure_time = None
        
        # Cache for ticker objects to avoid recreation
        self.ticker_cache = {}
        self.ticker_cache_ttl = 3600  # 1 hour
        self.ticker_cache_timestamps = {}
        
        # Retry configuration
        self.max_retries = 3
        self.retry_delay = 1
        
    async def _rate_limit_check(self):
        """Check and enforce rate limiting"""
        now = datetime.utcnow()
        minute_ago = now - timedelta(minutes=1)
        
        # Remove old timestamps
        self.request_timestamps = [
            ts for ts in self.request_timestamps if ts > minute_ago
        ]
        
        if len(self.request_timestamps) >= self.requests_per_minute:
            sleep_time = 60 - (now - min(self.request_timestamps)).total_seconds()
            if sleep_time > 0:
                self.logger.info(f"Rate limit reached, sleeping for {sleep_time:.2f}s")
                await asyncio.sleep(sleep_time)
        
        self.request_timestamps.append(now)
    
    def _get_ticker(self, symbol: str) -> yf.Ticker:
        """Get or create ticker object with caching"""
        symbol = symbol.upper()
        now = time.time()
        
        # Check if ticker is cached and still valid
        if (symbol in self.ticker_cache and 
            symbol in self.ticker_cache_timestamps and
            now - self.ticker_cache_timestamps[symbol] < self.ticker_cache_ttl):
            return self.ticker_cache[symbol]
        
        # Create new ticker
        ticker = yf.Ticker(symbol)
        self.ticker_cache[symbol] = ticker
        self.ticker_cache_timestamps[symbol] = now
        
        return ticker
    
    def _is_circuit_open(self) -> bool:
        """Check if circuit breaker is open"""
        if self.failure_count >= self.failure_threshold:
            if self.last_failure_time:
                time_since_failure = (datetime.utcnow() - self.last_failure_time).total_seconds()
                if time_since_failure < self.reset_timeout:
                    return True
                else:
                    self._reset_circuit_breaker()
        return False
    
    def _record_failure(self):
        """Record a failure for circuit breaker"""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()
        self.logger.warning(f"Failure recorded. Count: {self.failure_count}/{self.failure_threshold}")
    
    def _reset_circuit_breaker(self):
        """Reset circuit breaker after successful request"""
        if self.failure_count > 0:
            self.logger.info("Circuit breaker reset after successful request")
        self.failure_count = 0
        self.last_failure_time = None
    
    async def _execute_with_retry(self, func, *args, **kwargs):
        """Execute function with retry logic"""
        if self._is_circuit_open():
            self.logger.warning("Circuit breaker is open, skipping request")
            return None
        
        await self._rate_limit_check()
        
        for attempt in range(self.max_retries):
            try:
                # Execute in thread pool to avoid blocking
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(self.executor, func, *args, **kwargs)
                
                if result is not None:
                    self._reset_circuit_breaker()
                    return result
                else:
                    self.logger.warning(f"No data returned on attempt {attempt + 1}")
                    
            except Exception as e:
                self.logger.error(f"Attempt {attempt + 1} failed: {e}")
                
                if attempt < self.max_retries - 1:
                    wait_time = self.retry_delay * (2 ** attempt)  # Exponential backoff
                    await asyncio.sleep(wait_time)
        
        self._record_failure()
        return None
    
    def _get_quote_sync(self, symbol: str) -> Optional[Dict]:
        """Get quote synchronously (for thread pool execution)"""
        try:
            ticker = self._get_ticker(symbol)
            
            # Get current data - try multiple methods
            info = None
            fast_info = None
            
            try:
                fast_info = ticker.fast_info
            except Exception as e:
                self.logger.debug(f"fast_info failed for {symbol}: {e}")
            
            try:
                info = ticker.info
            except Exception as e:
                self.logger.debug(f"info failed for {symbol}: {e}")
            
            # Get recent history as fallback
            hist = None
            try:
                hist = ticker.history(period="2d")
                if hist.empty:
                    hist = None
            except Exception as e:
                self.logger.debug(f"history failed for {symbol}: {e}")
            
            # Build quote data from available sources
            quote_data = {}
            
            if fast_info:
                quote_data.update({
                    'price': fast_info.get('lastPrice'),
                    'open': fast_info.get('open'),
                    'high': fast_info.get('dayHigh'),
                    'low': fast_info.get('dayLow'),
                    'previous_close': fast_info.get('previousClose'),
                    'volume': fast_info.get('lastVolume')
                })
            
            if info:
                quote_data.update({
                    'price': quote_data.get('price') or info.get('currentPrice') or info.get('regularMarketPrice'),
                    'bid': info.get('bid'),
                    'ask': info.get('ask'),
                    'volume': quote_data.get('volume') or info.get('volume'),
                    'market_cap': info.get('marketCap'),
                    'previous_close': quote_data.get('previous_close') or info.get('previousClose')
                })
            
            if hist is not None and not hist.empty:
                last_row = hist.iloc[-1]
                quote_data.update({
                    'price': quote_data.get('price') or last_row['Close'],
                    'open': quote_data.get('open') or last_row['Open'],
                    'high': quote_data.get('high') or last_row['High'],
                    'low': quote_data.get('low') or last_row['Low'],
                    'volume': quote_data.get('volume') or last_row['Volume']
                })
            
            if quote_data.get('price'):
                return quote_data
            else:
                self.logger.warning(f"No valid price data found for {symbol}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error getting quote for {symbol}: {e}")
            return None
    
    def _get_historical_sync(self, symbol: str, start_date: date, end_date: date, interval: str) -> Optional[pd.DataFrame]:
        """Get historical data synchronously"""
        try:
            ticker = self._get_ticker(symbol)
            
            # Map interval to yfinance format
            interval_map = {
                "1m": "1m",
                "5m": "5m",
                "15m": "15m",
                "1h": "1h",
                "1d": "1d",
                "1w": "1wk",
                "1M": "1mo"
            }
            
            yf_interval = interval_map.get(interval, "1d")
            
            # For very recent data, use period instead of start/end
            days_diff = (end_date - start_date).days
            if days_diff <= 5 and yf_interval in ["1m", "5m", "15m"]:
                hist = ticker.history(period="5d", interval=yf_interval)
            else:
                hist = ticker.history(
                    start=start_date.isoformat(),
                    end=(end_date + timedelta(days=1)).isoformat(),  # Include end date
                    interval=yf_interval
                )
            
            if hist.empty:
                self.logger.warning(f"No historical data found for {symbol}")
                return None
            
            return hist
            
        except Exception as e:
            self.logger.error(f"Error getting historical data for {symbol}: {e}")
            return None
    
    def _get_company_info_sync(self, symbol: str) -> Optional[Dict]:
        """Get company info synchronously"""
        try:
            ticker = self._get_ticker(symbol)
            info = ticker.info
            
            if not info:
                return None
            
            return info
            
        except Exception as e:
            self.logger.error(f"Error getting company info for {symbol}: {e}")
            return None
    
    async def get_quote(self, symbol: str) -> Optional[MarketDataPoint]:
        """Get current quote for symbol"""
        quote_data = await self._execute_with_retry(self._get_quote_sync, symbol)
        
        if not quote_data:
            return None
        
        # Calculate change if we have current and previous close
        change = None
        change_percent = None
        if quote_data.get('price') and quote_data.get('previous_close'):
            try:
                change = float(quote_data['price']) - float(quote_data['previous_close'])
                change_percent = (change / float(quote_data['previous_close'])) * 100
            except (ValueError, TypeError, ZeroDivisionError):
                pass
        
        return MarketDataPoint(
            symbol=symbol.upper(),
            price=float(quote_data.get('price', 0)),
            volume=int(quote_data.get('volume', 0)) if quote_data.get('volume') else None,
            timestamp=datetime.utcnow(),  # Yahoo doesn't provide exact timestamp
            bid=float(quote_data.get('bid', 0)) if quote_data.get('bid') else None,
            ask=float(quote_data.get('ask', 0)) if quote_data.get('ask') else None,
            open_price=float(quote_data.get('open', 0)) if quote_data.get('open') else None,
            high_price=float(quote_data.get('high', 0)) if quote_data.get('high') else None,
            low_price=float(quote_data.get('low', 0)) if quote_data.get('low') else None,
            previous_close=float(quote_data.get('previous_close', 0)) if quote_data.get('previous_close') else None,
            change=change,
            change_percent=change_percent,
            provider=DataProvider.YAHOO_FINANCE
        )
    
    async def get_multiple_quotes(self, symbols: List[str]) -> List[MarketDataPoint]:
        """Get quotes for multiple symbols"""
        quotes = []
        
        # Use semaphore to limit concurrent requests
        semaphore = asyncio.Semaphore(5)
        
        async def fetch_quote(symbol: str):
            async with semaphore:
                quote = await self.get_quote(symbol)
                if quote:
                    quotes.append(quote)
        
        tasks = [fetch_quote(symbol) for symbol in symbols]
        await asyncio.gather(*tasks, return_exceptions=True)
        
        return quotes
    
    async def get_historical_data(
        self, 
        symbol: str, 
        start_date: date, 
        end_date: date, 
        interval: str = "1d"
    ) -> Optional[HistoricalData]:
        """Get historical data"""
        hist_df = await self._execute_with_retry(
            self._get_historical_sync, symbol, start_date, end_date, interval
        )
        
        if hist_df is None or hist_df.empty:
            return None
        
        data_points = []
        for index, row in hist_df.iterrows():
            # Handle timezone-aware datetime
            timestamp = index
            if hasattr(timestamp, 'tz_localize'):
                timestamp = timestamp.tz_localize(None) if timestamp.tz is None else timestamp.tz_convert(None)
            
            data_point = MarketDataPoint(
                symbol=symbol.upper(),
                price=float(row['Close']),
                volume=int(row['Volume']) if pd.notna(row['Volume']) else None,
                timestamp=timestamp.to_pydatetime() if hasattr(timestamp, 'to_pydatetime') else timestamp,
                open_price=float(row['Open']),
                high_price=float(row['High']),
                low_price=float(row['Low']),
                previous_close=None,  # Would need to calculate from previous row
                change=None,
                change_percent=None,
                bid=None,
                ask=None,
                provider=DataProvider.YAHOO_FINANCE
            )
            data_points.append(data_point)
        
        return HistoricalData(
            symbol=symbol.upper(),
            data_points=data_points,
            start_date=start_date,
            end_date=end_date,
            interval=interval,
            provider=DataProvider.YAHOO_FINANCE
        )
    
    async def get_company_info(self, symbol: str) -> Optional[CompanyInfo]:
        """Get company information"""
        info_data = await self._execute_with_retry(self._get_company_info_sync, symbol)
        
        if not info_data:
            return None
        
        # Calculate P/E ratio if possible
        pe_ratio = None
        try:
            if info_data.get('currentPrice') and info_data.get('earningsPerShare'):
                pe_ratio = float(info_data['currentPrice']) / float(info_data['earningsPerShare'])
        except (ValueError, TypeError, ZeroDivisionError):
            pe_ratio = info_data.get('trailingPE') or info_data.get('forwardPE')
        
        return CompanyInfo(
            symbol=symbol.upper(),
            name=info_data.get('longName') or info_data.get('shortName', ''),
            description=info_data.get('longBusinessSummary', ''),
            sector=info_data.get('sector', ''),
            industry=info_data.get('industry', ''),
            market_cap=info_data.get('marketCap'),
            shares_outstanding=info_data.get('sharesOutstanding'),
            exchange=info_data.get('exchange', ''),
            currency=info_data.get('currency', 'USD'),
            country=info_data.get('country', ''),
            website=info_data.get('website', ''),
            employees=info_data.get('fullTimeEmployees'),
            pe_ratio=pe_ratio,
            dividend_yield=info_data.get('dividendYield'),
            provider=DataProvider.YAHOO_FINANCE
        )
    
    async def health_check(self) -> bool:
        """Check if provider is healthy"""
        try:
            # Simple test with a well-known symbol
            quote = await self.get_quote("AAPL")
            return quote is not None and quote.price > 0
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return False
    
    async def _cleanup_session(self):
        """Cleanup resources"""
        if self.executor:
            self.executor.shutdown(wait=True)
        self.ticker_cache.clear()
        self.ticker_cache_timestamps.clear()
        await super()._cleanup_session()
    
    def get_error_count(self) -> int:
        """Get current error count for monitoring"""
        return self.failure_count
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            'ticker_cache_size': len(self.ticker_cache),
            'oldest_cached_ticker': min(self.ticker_cache_timestamps.values()) if self.ticker_cache_timestamps else None,
            'newest_cached_ticker': max(self.ticker_cache_timestamps.values()) if self.ticker_cache_timestamps else None
        }