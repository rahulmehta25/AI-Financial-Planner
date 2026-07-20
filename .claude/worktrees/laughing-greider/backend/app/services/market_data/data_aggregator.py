from typing import List, Dict, Any, Optional
import asyncio
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)

class MarketDataAggregator:
    def __init__(self):
        # Primary data sources
        self.polygon_client = None  # PolygonClient(Config.POLYGON_API_KEY)
        self.databento_client = None  # DatabentClient(Config.DATABENTO_API_KEY)
        
        # Fallback sources
        self.fallback_sources = [
            YFinanceAdapter(),
            AlphaVantageAdapter(),
            TwelveDataAdapter()
        ]
        
        # Caching layer
        self.cache = MarketDataCache()
        
        # WebSocket manager for real-time data
        self.ws_manager = WebSocketManager()
        
        # Circuit breaker for each source
        self.circuit_breakers = {
            'polygon': CircuitBreaker(failure_threshold=5),
            'databento': CircuitBreaker(failure_threshold=3),
            'yfinance': CircuitBreaker(failure_threshold=10)
        }
        
        # Data quality validator
        self.validator = MarketDataValidator()
    
    async def get_historical_data(
        self,
        symbols: List[str],
        start_date: datetime,
        end_date: datetime,
        interval: str = '1d',
        data_type: str = 'bars'
    ) -> pd.DataFrame:
        """Fetch historical data with intelligent source selection and fallback"""
        
        # Check cache first
        cached_data = await self.cache.get_historical(
            symbols, start_date, end_date, interval
        )
        
        if cached_data is not None and self._is_cache_fresh(cached_data):
            return cached_data
        
        # Determine best source based on requirements
        source = self._select_optimal_source(
            symbols, start_date, end_date, interval, data_type
        )
        
        # Try primary source with circuit breaker
        try:
            data = await self.circuit_breakers[source].call(
                self._fetch_from_source,
                source, symbols, start_date, end_date, interval
            )
            
            # Validate data quality
            if not await self.validator.validate(data):
                raise DataQualityException("Data failed quality checks")
            
            # Cache the validated data
            await self.cache.store_historical(
                symbols, data, interval, ttl=self._calculate_ttl(interval)
            )
            
            return data
            
        except (CircuitOpenException, DataQualityException) as e:
            # Fallback to secondary sources
            return await self._fetch_with_fallback(
                symbols, start_date, end_date, interval
            )
    
    async def get_real_time_data(
        self,
        symbols: List[str],
        data_types: List[str] = ['trades', 'quotes']
    ):
        """Stream real-time market data"""
        
        # Subscribe to WebSocket feeds
        streams = []
        
        if 'trades' in data_types:
            streams.append(
                self.ws_manager.subscribe_trades(symbols)
            )
        
        if 'quotes' in data_types:
            streams.append(
                self.ws_manager.subscribe_quotes(symbols)
            )
        
        # Merge multiple streams
        async for data in self._merge_streams(streams):
            # Validate real-time data
            if await self.validator.validate_realtime(data):
                # Update cache with latest data
                await self.cache.update_realtime(data)
                
                yield self._normalize_realtime_data(data)
    
    async def get_fundamental_data(
        self,
        symbols: List[str],
        metrics: List[str] = None
    ) -> Dict[str, Any]:
        """Fetch fundamental data including financials, ratios, etc."""
        
        fundamental_data = {}
        
        for symbol in symbols:
            # Try to get from cache
            cached = await self.cache.get_fundamental(symbol)
            
            if cached and self._is_fundamental_fresh(cached):
                fundamental_data[symbol] = cached
                continue
            
            # Fetch fresh data
            try:
                data = await self._fetch_fundamental_data(symbol)
                ratios = self._calculate_financial_ratios(data)
                
                fundamental_data[symbol] = {
                    'company': data,
                    'ratios': ratios,
                    'updated_at': datetime.utcnow()
                }
                
                # Cache the data
                await self.cache.store_fundamental(
                    symbol,
                    fundamental_data[symbol],
                    ttl=86400  # 24 hours
                )
                
            except Exception as e:
                logger.error(f"Failed to fetch fundamental data for {symbol}: {e}")
                # Try fallback source
                fundamental_data[symbol] = await self._fetch_fundamental_fallback(symbol)
        
        return fundamental_data
    
    def _calculate_financial_ratios(self, financials: Dict) -> Dict[str, float]:
        """Calculate key financial ratios"""
        ratios = {}
        
        try:
            # Profitability ratios
            if financials.get('net_income') and financials.get('shareholders_equity'):
                ratios['roe'] = financials['net_income'] / financials['shareholders_equity']
            
            if financials.get('net_income') and financials.get('total_assets'):
                ratios['roa'] = financials['net_income'] / financials['total_assets']
            
            if financials.get('net_income') and financials.get('revenue'):
                ratios['profit_margin'] = financials['net_income'] / financials['revenue']
            
            # Liquidity ratios
            if financials.get('current_assets') and financials.get('current_liabilities'):
                ratios['current_ratio'] = financials['current_assets'] / financials['current_liabilities']
            
            if (financials.get('current_assets') and financials.get('current_liabilities') and 
                financials.get('inventory')):
                ratios['quick_ratio'] = (
                    financials['current_assets'] - financials['inventory']
                ) / financials['current_liabilities']
            
            # Leverage ratios
            if financials.get('total_debt') and financials.get('shareholders_equity'):
                ratios['debt_to_equity'] = financials['total_debt'] / financials['shareholders_equity']
            
            if financials.get('ebit') and financials.get('interest_expense'):
                ratios['interest_coverage'] = financials['ebit'] / financials['interest_expense']
            
        except (KeyError, ZeroDivisionError) as e:
            logger.warning(f"Could not calculate some ratios: {e}")
        
        return ratios
    
    async def _fetch_from_source(
        self,
        source: str,
        symbols: List[str],
        start_date: datetime,
        end_date: datetime,
        interval: str
    ) -> pd.DataFrame:
        """Fetch data from specific source"""
        
        if source == 'polygon':
            # Placeholder for Polygon implementation
            return pd.DataFrame()
            
        elif source == 'databento':
            # Placeholder for Databento implementation
            return pd.DataFrame()
            
        else:
            raise ValueError(f"Unknown source: {source}")
    
    def _select_optimal_source(
        self,
        symbols: List[str],
        start_date: datetime,
        end_date: datetime,
        interval: str,
        data_type: str
    ) -> str:
        """Select the best data source based on requirements"""
        
        # Simple source selection logic
        if len(symbols) > 100:
            return 'databento'  # Better for bulk data
        elif interval == '1m' or interval == '5m':
            return 'polygon'  # Better for intraday
        else:
            return 'polygon'  # Default to Polygon
    
    def _is_cache_fresh(self, data: pd.DataFrame) -> bool:
        """Check if cached data is fresh enough"""
        if data.empty:
            return False
        
        # Check if data is less than 1 hour old
        latest_time = data.index.max()
        if isinstance(latest_time, pd.Timestamp):
            return (datetime.now() - latest_time.to_pydatetime()) < timedelta(hours=1)
        
        return False
    
    def _is_fundamental_fresh(self, data: Dict) -> bool:
        """Check if fundamental data is fresh enough"""
        if 'updated_at' not in data:
            return False
        
        updated_at = data['updated_at']
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at)
        
        return (datetime.now() - updated_at) < timedelta(days=1)
    
    def _calculate_ttl(self, interval: str) -> int:
        """Calculate cache TTL based on data interval"""
        ttl_map = {
            '1m': 300,    # 5 minutes
            '5m': 900,    # 15 minutes
            '15m': 1800,  # 30 minutes
            '1h': 3600,   # 1 hour
            '1d': 86400,  # 1 day
        }
        return ttl_map.get(interval, 3600)
    
    async def _fetch_with_fallback(
        self,
        symbols: List[str],
        start_date: datetime,
        end_date: datetime,
        interval: str
    ) -> pd.DataFrame:
        """Fetch data using fallback sources"""
        
        for source in self.fallback_sources:
            try:
                data = await source.get_historical_data(
                    symbols, start_date, end_date, interval
                )
                if not data.empty:
                    return data
            except Exception as e:
                logger.warning(f"Fallback source {source.__class__.__name__} failed: {e}")
                continue
        
        raise Exception("All data sources failed")
    
    async def _fetch_fundamental_data(self, symbol: str) -> Dict:
        """Fetch fundamental data from primary source"""
        # Placeholder implementation
        return {
            'net_income': 1000000,
            'revenue': 10000000,
            'total_assets': 50000000,
            'shareholders_equity': 30000000,
            'current_assets': 20000000,
            'current_liabilities': 10000000,
            'inventory': 5000000,
            'total_debt': 15000000,
            'ebit': 1500000,
            'interest_expense': 200000
        }
    
    async def _fetch_fundamental_fallback(self, symbol: str) -> Dict:
        """Fetch fundamental data from fallback source"""
        # Placeholder implementation
        return {
            'company': {'name': symbol, 'sector': 'Unknown'},
            'ratios': {},
            'updated_at': datetime.utcnow()
        }
    
    async def _merge_streams(self, streams):
        """Merge multiple data streams"""
        # Placeholder implementation
        yield {}
    
    def _normalize_realtime_data(self, data: Dict) -> Dict:
        """Normalize real-time data to standard format"""
        # Placeholder implementation
        return data

# Placeholder classes
class YFinanceAdapter:
    async def get_historical_data(self, symbols, start_date, end_date, interval):
        return pd.DataFrame()

class AlphaVantageAdapter:
    async def get_historical_data(self, symbols, start_date, end_date, interval):
        return pd.DataFrame()

class TwelveDataAdapter:
    async def get_historical_data(self, symbols, start_date, end_date, interval):
        return pd.DataFrame()

class MarketDataCache:
    async def get_historical(self, symbols, start_date, end_date, interval):
        return None
    
    async def store_historical(self, symbols, data, interval, ttl):
        pass
    
    async def get_fundamental(self, symbol):
        return None
    
    async def store_fundamental(self, symbol, data, ttl):
        pass
    
    async def update_realtime(self, data):
        pass

class WebSocketManager:
    def subscribe_trades(self, symbols):
        return []
    
    def subscribe_quotes(self, symbols):
        return []

class CircuitBreaker:
    def __init__(self, failure_threshold):
        self.failure_threshold = failure_threshold
        self.failure_count = 0
        self.state = 'closed'
    
    async def call(self, func, *args, **kwargs):
        if self.state == 'open':
            raise CircuitOpenException("Circuit breaker is open")
        
        try:
            result = await func(*args, **kwargs)
            self.failure_count = 0
            return result
        except Exception as e:
            self.failure_count += 1
            if self.failure_count >= self.failure_threshold:
                self.state = 'open'
            raise e

class MarketDataValidator:
    async def validate(self, data):
        return True
    
    async def validate_realtime(self, data):
        return True

class DataQualityException(Exception):
    pass

class CircuitOpenException(Exception):
    pass
