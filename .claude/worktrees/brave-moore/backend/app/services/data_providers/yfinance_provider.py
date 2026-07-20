"""
yfinance data provider with circuit breaker and retry logic
"""
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, date, timedelta
from decimal import Decimal
import logging
import yfinance as yf
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_log
)

from app.services.data_providers.base import (
    DataProvider,
    Quote,
    HistoricalBar,
    DividendInfo,
    SplitInfo,
    DataProviderStatus
)
from app.services.data_providers.circuit_breaker import CircuitBreaker, CircuitOpenError
from app.core.config import settings

logger = logging.getLogger(__name__)


class YFinanceProvider(DataProvider):
    """
    Market data provider using yfinance library
    
    Features:
    - Circuit breaker for fault tolerance
    - Exponential backoff retry
    - Bulk quote fetching
    - 15-minute delayed data disclaimer
    """
    
    def __init__(self):
        super().__init__("yfinance")
        
        # Initialize circuit breaker
        self.circuit_breaker = CircuitBreaker(
            name="yfinance",
            failure_threshold=settings.circuit_breaker_failure_threshold,
            recovery_timeout=settings.circuit_breaker_recovery_timeout,
            expected_exception=Exception
        )
        
        # Cache for tickers to avoid recreating
        self._ticker_cache: Dict[str, yf.Ticker] = {}
        
    def _get_ticker(self, symbol: str) -> yf.Ticker:
        """Get or create ticker object"""
        if symbol not in self._ticker_cache:
            self._ticker_cache[symbol] = yf.Ticker(symbol)
        return self._ticker_cache[symbol]
    
    def _decimal_safe(self, value: Any) -> Optional[Decimal]:
        """Convert value to Decimal safely"""
        if value is None or (isinstance(value, float) and not value == value):  # NaN check
            return None
        try:
            return Decimal(str(value))
        except:
            return None
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        retry=retry_if_exception_type((ConnectionError, TimeoutError)),
        before=before_log(logger, logging.DEBUG)
    )
    async def _fetch_quote_with_retry(self, symbol: str) -> Optional[Quote]:
        """Fetch quote with retry logic"""
        try:
            # Run yfinance in thread pool since it's synchronous
            loop = asyncio.get_event_loop()
            ticker = self._get_ticker(symbol)
            
            # Get ticker info
            info = await loop.run_in_executor(None, lambda: ticker.info)
            
            # Extract price data
            current_price = self._decimal_safe(
                info.get('currentPrice') or 
                info.get('regularMarketPrice') or
                info.get('previousClose')
            )
            
            if current_price is None:
                logger.warning(f"No price data available for {symbol}")
                return None
            
            quote = Quote(
                symbol=symbol,
                price=current_price,
                open=self._decimal_safe(info.get('regularMarketOpen') or info.get('open')),
                high=self._decimal_safe(info.get('regularMarketDayHigh') or info.get('dayHigh')),
                low=self._decimal_safe(info.get('regularMarketDayLow') or info.get('dayLow')),
                close=self._decimal_safe(info.get('previousClose')),
                volume=info.get('regularMarketVolume') or info.get('volume'),
                timestamp=datetime.utcnow(),
                source="yfinance",
                is_delayed=True,
                delay_minutes=15
            )
            
            self._set_healthy()
            return quote
            
        except Exception as e:
            logger.error(f"Failed to fetch quote for {symbol}: {e}")
            self._set_error(str(e))
            raise
    
    async def get_quote(self, symbol: str) -> Optional[Quote]:
        """Get current quote for a symbol"""
        try:
            return await self.circuit_breaker.call(
                self._fetch_quote_with_retry,
                symbol
            )
        except CircuitOpenError:
            logger.warning(f"Circuit open for yfinance, cannot fetch quote for {symbol}")
            self._status = DataProviderStatus.UNAVAILABLE
            return None
        except Exception as e:
            logger.error(f"Error fetching quote for {symbol}: {e}")
            return None
    
    async def get_quotes(self, symbols: List[str]) -> Dict[str, Optional[Quote]]:
        """Get quotes for multiple symbols"""
        results = {}
        
        # Use asyncio.gather for parallel fetching
        tasks = [self.get_quote(symbol) for symbol in symbols]
        quotes = await asyncio.gather(*tasks, return_exceptions=True)
        
        for symbol, quote_or_error in zip(symbols, quotes):
            if isinstance(quote_or_error, Exception):
                logger.error(f"Error fetching quote for {symbol}: {quote_or_error}")
                results[symbol] = None
            else:
                results[symbol] = quote_or_error
        
        return results
    
    async def get_historical(
        self,
        symbol: str,
        start_date: date,
        end_date: date,
        interval: str = "1d"
    ) -> List[HistoricalBar]:
        """Get historical price data"""
        try:
            async def _fetch():
                loop = asyncio.get_event_loop()
                ticker = self._get_ticker(symbol)
                
                # Fetch historical data
                hist = await loop.run_in_executor(
                    None,
                    lambda: ticker.history(
                        start=start_date,
                        end=end_date,
                        interval=interval,
                        auto_adjust=False
                    )
                )
                
                bars = []
                for index, row in hist.iterrows():
                    bar = HistoricalBar(
                        date=index.date(),
                        open=self._decimal_safe(row['Open']) or Decimal(0),
                        high=self._decimal_safe(row['High']) or Decimal(0),
                        low=self._decimal_safe(row['Low']) or Decimal(0),
                        close=self._decimal_safe(row['Close']) or Decimal(0),
                        adj_close=self._decimal_safe(row.get('Adj Close')),
                        volume=int(row['Volume']) if row['Volume'] else 0
                    )
                    bars.append(bar)
                
                return bars
            
            result = await self.circuit_breaker.call(_fetch)
            self._set_healthy()
            return result
            
        except CircuitOpenError:
            logger.warning(f"Circuit open for yfinance, cannot fetch historical for {symbol}")
            self._status = DataProviderStatus.UNAVAILABLE
            return []
        except Exception as e:
            logger.error(f"Error fetching historical for {symbol}: {e}")
            self._set_error(str(e))
            return []
    
    async def get_dividends(
        self,
        symbol: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[DividendInfo]:
        """Get dividend history"""
        try:
            async def _fetch():
                loop = asyncio.get_event_loop()
                ticker = self._get_ticker(symbol)
                
                # Get all dividends
                divs = await loop.run_in_executor(None, lambda: ticker.dividends)
                
                dividends = []
                for div_date, amount in divs.items():
                    div_date = div_date.date()
                    
                    # Filter by date range if provided
                    if start_date and div_date < start_date:
                        continue
                    if end_date and div_date > end_date:
                        continue
                    
                    dividends.append(DividendInfo(
                        ex_date=div_date,
                        amount=self._decimal_safe(amount) or Decimal(0)
                    ))
                
                return dividends
            
            result = await self.circuit_breaker.call(_fetch)
            self._set_healthy()
            return result
            
        except CircuitOpenError:
            logger.warning(f"Circuit open for yfinance, cannot fetch dividends for {symbol}")
            return []
        except Exception as e:
            logger.error(f"Error fetching dividends for {symbol}: {e}")
            return []
    
    async def get_splits(
        self,
        symbol: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[SplitInfo]:
        """Get stock split history"""
        try:
            async def _fetch():
                loop = asyncio.get_event_loop()
                ticker = self._get_ticker(symbol)
                
                # Get all splits
                splits = await loop.run_in_executor(None, lambda: ticker.splits)
                
                split_list = []
                for split_date, ratio in splits.items():
                    split_date = split_date.date()
                    
                    # Filter by date range if provided
                    if start_date and split_date < start_date:
                        continue
                    if end_date and split_date > end_date:
                        continue
                    
                    split_list.append(SplitInfo(
                        date=split_date,
                        ratio=self._decimal_safe(ratio) or Decimal(1)
                    ))
                
                return split_list
            
            result = await self.circuit_breaker.call(_fetch)
            self._set_healthy()
            return result
            
        except CircuitOpenError:
            logger.warning(f"Circuit open for yfinance, cannot fetch splits for {symbol}")
            return []
        except Exception as e:
            logger.error(f"Error fetching splits for {symbol}: {e}")
            return []
    
    async def health_check(self) -> bool:
        """Check if provider is healthy by fetching SPY quote"""
        try:
            # Try to fetch SPY as a health check
            quote = await self.get_quote("SPY")
            return quote is not None
        except:
            return False
    
    def get_status_info(self) -> dict:
        """Get provider status information"""
        return {
            "provider": self.name,
            "status": self._status.value,
            "circuit_breaker": self.circuit_breaker.get_status(),
            "last_success": self._last_success.isoformat() if self._last_success else None,
            "last_error": self._last_error,
            "disclaimer": "Data is delayed by approximately 15 minutes"
        }