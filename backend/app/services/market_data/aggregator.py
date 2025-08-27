"""
Market Data Aggregator

Intelligent failover system that orchestrates multiple market data providers
with sophisticated routing, caching, and data quality validation.
"""

import asyncio
import logging
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union, Callable
from collections import defaultdict, deque
from enum import Enum
import json
import pandas as pd

from .providers.polygon_io import PolygonIOProvider
from .providers.databento import DatabentoProvider
from .providers.yfinance_enhanced import YFinanceEnhancedProvider
from .providers.alpha_vantage import AlphaVantageProvider
from .providers.iex_cloud import IEXCloudProvider
from .models import MarketDataPoint, HistoricalData, CompanyInfo, DataProvider
from .cache import CacheManager
from .config import config


class ProviderPriority(Enum):
    """Provider priority levels"""
    PRIMARY = 1
    SECONDARY = 2
    FALLBACK = 3
    EMERGENCY = 4


class DataQuality(Enum):
    """Data quality levels"""
    EXCELLENT = 5
    GOOD = 4
    ACCEPTABLE = 3
    POOR = 2
    UNUSABLE = 1


class MarketDataAggregator:
    """Intelligent market data aggregator with multi-provider failover"""
    
    def __init__(self):
        self.logger = logging.getLogger("market_data.aggregator")
        
        # Provider hierarchy with priorities
        self.provider_hierarchy = {
            ProviderPriority.PRIMARY: [],
            ProviderPriority.SECONDARY: [],
            ProviderPriority.FALLBACK: [],
            ProviderPriority.EMERGENCY: []
        }
        
        # Provider instances
        self.providers = {}
        
        # Provider health and performance tracking
        self.provider_health = defaultdict(bool)
        self.provider_latency = defaultdict(lambda: deque(maxlen=100))
        self.provider_success_rate = defaultdict(lambda: deque(maxlen=1000))
        self.provider_last_check = defaultdict(datetime.utcnow)
        
        # Data quality tracking
        self.data_quality_scores = defaultdict(lambda: deque(maxlen=100))
        
        # Cache manager
        self.cache_manager = CacheManager()
        
        # Circuit breakers per provider
        self.circuit_breakers = {}
        
        # Rate limiting
        self.global_rate_limiter = AsyncRateLimiter(requests_per_minute=300)
        
        # Data normalization rules
        self.normalization_rules = {
            'price_precision': 4,
            'volume_precision': 0,
            'timestamp_format': 'utc',
            'currency_normalization': True
        }
        
        self._initialized = False
    
    async def initialize(self):
        """Initialize the aggregator with all available providers"""
        if self._initialized:
            return
        
        self.logger.info("Initializing Market Data Aggregator")
        
        try:
            await self._initialize_providers()
            await self._setup_provider_hierarchy()
            await self.cache_manager.initialize()
            
            # Start background tasks
            asyncio.create_task(self._health_monitor_loop())
            asyncio.create_task(self._performance_monitor_loop())
            asyncio.create_task(self._data_quality_monitor_loop())
            
            self._initialized = True
            self.logger.info("Market Data Aggregator initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize aggregator: {e}")
            raise
    
    async def _initialize_providers(self):
        """Initialize all available providers"""
        provider_configs = [
            (DataProvider.POLYGON_IO, PolygonIOProvider, config.polygon_api_key),
            (DataProvider.DATABENTO, DatabentoProvider, config.databento_api_key),
            (DataProvider.ALPHA_VANTAGE, AlphaVantageProvider, config.alpha_vantage_api_key),
            (DataProvider.IEX_CLOUD, IEXCloudProvider, config.iex_cloud_api_key),
            (DataProvider.YAHOO_FINANCE, YFinanceEnhancedProvider, None)  # No API key needed
        ]
        
        for provider_type, provider_class, api_key in provider_configs:
            try:
                if provider_type == DataProvider.YAHOO_FINANCE:
                    provider = provider_class()
                else:
                    if not api_key:
                        self.logger.info(f"No API key for {provider_type}, skipping")
                        continue
                    provider = provider_class(api_key)
                
                await provider._initialize_session()
                self.providers[provider_type] = provider
                
                # Initialize circuit breaker
                self.circuit_breakers[provider_type] = CircuitBreaker(
                    failure_threshold=config.circuit_breaker_thresholds.get(provider_type, 5),
                    reset_timeout=config.circuit_breaker_timeouts.get(provider_type, 300)
                )
                
                self.logger.info(f"Initialized provider: {provider_type}")
                
            except Exception as e:
                self.logger.error(f"Failed to initialize {provider_type}: {e}")
    
    async def _setup_provider_hierarchy(self):
        """Setup provider hierarchy based on capabilities and costs"""
        # Primary providers (professional, real-time)
        if DataProvider.POLYGON_IO in self.providers:
            self.provider_hierarchy[ProviderPriority.PRIMARY].append(DataProvider.POLYGON_IO)
        if DataProvider.DATABENTO in self.providers:
            self.provider_hierarchy[ProviderPriority.PRIMARY].append(DataProvider.DATABENTO)
        
        # Secondary providers (good quality, some limitations)
        if DataProvider.IEX_CLOUD in self.providers:
            self.provider_hierarchy[ProviderPriority.SECONDARY].append(DataProvider.IEX_CLOUD)
        if DataProvider.ALPHA_VANTAGE in self.providers:
            self.provider_hierarchy[ProviderPriority.SECONDARY].append(DataProvider.ALPHA_VANTAGE)
        
        # Fallback providers (free, reliable)
        if DataProvider.YAHOO_FINANCE in self.providers:
            self.provider_hierarchy[ProviderPriority.FALLBACK].append(DataProvider.YAHOO_FINANCE)
        
        # Log the hierarchy
        for priority, providers in self.provider_hierarchy.items():
            if providers:
                self.logger.info(f"{priority.name}: {[p.value for p in providers]}")
    
    async def get_quote(self, symbol: str, use_cache: bool = True) -> Optional[MarketDataPoint]:
        """Get current quote with intelligent provider selection"""
        start_time = datetime.utcnow()
        
        # Check cache first
        if use_cache:
            cached_quote = await self.cache_manager.get_quote_cached(symbol)
            if cached_quote and self._is_cache_fresh(cached_quote, max_age_seconds=30):
                return cached_quote
        
        # Select optimal provider
        selected_provider = await self._select_provider_for_quotes([symbol])
        if not selected_provider:
            self.logger.error("No healthy providers available for quotes")
            return None
        
        # Attempt to get quote with fallback
        quote = await self._fetch_with_fallback(
            self._get_quote_from_provider,
            symbol,
            selected_provider
        )
        
        if quote:
            # Normalize and validate data
            quote = self._normalize_quote_data(quote)
            quality_score = self._assess_data_quality(quote)
            
            if quality_score >= DataQuality.ACCEPTABLE:
                # Cache the result
                if use_cache:
                    await self.cache_manager.store_quote(symbol, quote, ttl=60)
                
                # Track performance
                latency = (datetime.utcnow() - start_time).total_seconds()
                self._record_provider_performance(quote.provider, True, latency)
                
                return quote
            else:
                self.logger.warning(f"Quote quality too low: {quality_score}")
        
        self._record_provider_performance(selected_provider, False, 0)
        return None
    
    async def get_multiple_quotes(self, symbols: List[str], use_cache: bool = True) -> List[MarketDataPoint]:
        """Get quotes for multiple symbols efficiently"""
        if not symbols:
            return []
        
        start_time = datetime.utcnow()
        quotes = []
        uncached_symbols = []
        
        # Check cache for each symbol
        if use_cache:
            for symbol in symbols:
                cached_quote = await self.cache_manager.get_quote_cached(symbol)
                if cached_quote and self._is_cache_fresh(cached_quote, max_age_seconds=30):
                    quotes.append(cached_quote)
                else:
                    uncached_symbols.append(symbol)
        else:
            uncached_symbols = symbols
        
        if not uncached_symbols:
            return quotes
        
        # Select optimal provider
        selected_provider = await self._select_provider_for_quotes(uncached_symbols)
        if not selected_provider:
            self.logger.error("No healthy providers available for batch quotes")
            return quotes
        
        # Batch fetch with intelligent chunking
        batch_quotes = await self._fetch_quotes_in_batches(uncached_symbols, selected_provider)
        
        # Process and validate results
        for quote in batch_quotes:
            if quote:
                quote = self._normalize_quote_data(quote)
                quality_score = self._assess_data_quality(quote)
                
                if quality_score >= DataQuality.ACCEPTABLE:
                    quotes.append(quote)
                    
                    # Cache individual quote
                    if use_cache:
                        await self.cache_manager.store_quote(quote.symbol, quote, ttl=60)
        
        # Track performance
        latency = (datetime.utcnow() - start_time).total_seconds()
        success = len(batch_quotes) > 0
        self._record_provider_performance(selected_provider, success, latency)
        
        return quotes
    
    async def get_historical_data(
        self, 
        symbol: str, 
        start_date: date, 
        end_date: date, 
        interval: str = "1d",
        use_cache: bool = True
    ) -> Optional[HistoricalData]:
        """Get historical data with intelligent provider selection"""
        start_time = datetime.utcnow()
        
        # Check cache first
        if use_cache:
            cached_data = await self.cache_manager.get_historical_cached(
                symbol, start_date, end_date, interval
            )
            if cached_data and self._is_historical_cache_fresh(cached_data, interval):
                return cached_data
        
        # Select optimal provider for historical data
        selected_provider = await self._select_provider_for_historical(symbol, start_date, end_date, interval)
        if not selected_provider:
            self.logger.error("No healthy providers available for historical data")
            return None
        
        # Fetch with fallback
        historical_data = await self._fetch_with_fallback(
            self._get_historical_from_provider,
            symbol, start_date, end_date, interval, selected_provider
        )
        
        if historical_data:
            # Normalize and validate data
            historical_data = self._normalize_historical_data(historical_data)
            quality_score = self._assess_historical_quality(historical_data)
            
            if quality_score >= DataQuality.ACCEPTABLE:
                # Cache the result
                if use_cache:
                    cache_ttl = self._calculate_historical_cache_ttl(interval)
                    await self.cache_manager.store_historical(
                        symbol, historical_data, cache_ttl
                    )
                
                # Track performance
                latency = (datetime.utcnow() - start_time).total_seconds()
                self._record_provider_performance(historical_data.provider, True, latency)
                
                return historical_data
            else:
                self.logger.warning(f"Historical data quality too low: {quality_score}")
        
        self._record_provider_performance(selected_provider, False, 0)
        return None
    
    async def get_company_info(self, symbol: str, use_cache: bool = True) -> Optional[CompanyInfo]:
        """Get company information with caching"""
        # Check cache first (company info changes rarely)
        if use_cache:
            cached_info = await self.cache_manager.get_company_info_cached(symbol)
            if cached_info and self._is_cache_fresh(cached_info, max_age_seconds=86400):  # 24 hours
                return cached_info
        
        # Select provider that's good for company info
        selected_provider = await self._select_provider_for_company_info(symbol)
        if not selected_provider:
            return None
        
        # Fetch with fallback
        company_info = await self._fetch_with_fallback(
            self._get_company_info_from_provider,
            symbol, selected_provider
        )
        
        if company_info:
            # Normalize and cache
            company_info = self._normalize_company_info(company_info)
            if use_cache:
                await self.cache_manager.store_company_info(symbol, company_info, ttl=86400)
        
        return company_info
    
    async def _select_provider_for_quotes(self, symbols: List[str]) -> Optional[DataProvider]:
        """Select optimal provider for quote requests"""
        # Score providers based on health, latency, and capabilities
        provider_scores = {}
        
        for priority in [ProviderPriority.PRIMARY, ProviderPriority.SECONDARY, ProviderPriority.FALLBACK]:
            for provider_type in self.provider_hierarchy[priority]:
                if provider_type not in self.providers:
                    continue
                
                # Check health
                if not self.provider_health[provider_type]:
                    continue
                
                # Check circuit breaker
                if self.circuit_breakers[provider_type].is_open():
                    continue
                
                # Calculate score
                score = self._calculate_provider_score(provider_type, 'quotes')
                provider_scores[provider_type] = score
        
        if not provider_scores:
            return None
        
        # Select provider with highest score
        best_provider = max(provider_scores.items(), key=lambda x: x[1])[0]
        return best_provider
    
    async def _select_provider_for_historical(
        self, 
        symbol: str, 
        start_date: date, 
        end_date: date, 
        interval: str
    ) -> Optional[DataProvider]:
        """Select optimal provider for historical data"""
        provider_scores = {}
        
        for priority in [ProviderPriority.PRIMARY, ProviderPriority.SECONDARY, ProviderPriority.FALLBACK]:
            for provider_type in self.provider_hierarchy[priority]:
                if provider_type not in self.providers:
                    continue
                
                if not self.provider_health[provider_type]:
                    continue
                
                if self.circuit_breakers[provider_type].is_open():
                    continue
                
                # Check if provider supports the requested interval
                if not self._provider_supports_interval(provider_type, interval):
                    continue
                
                # Check if provider supports the date range
                if not self._provider_supports_date_range(provider_type, start_date, end_date):
                    continue
                
                score = self._calculate_provider_score(provider_type, 'historical')
                provider_scores[provider_type] = score
        
        if not provider_scores:
            return None
        
        return max(provider_scores.items(), key=lambda x: x[1])[0]
    
    async def _select_provider_for_company_info(self, symbol: str) -> Optional[DataProvider]:
        """Select optimal provider for company information"""
        # Company info providers in order of preference
        preferred_providers = [
            DataProvider.POLYGON_IO,
            DataProvider.ALPHA_VANTAGE,
            DataProvider.IEX_CLOUD,
            DataProvider.YAHOO_FINANCE
        ]
        
        for provider_type in preferred_providers:
            if (provider_type in self.providers and 
                self.provider_health[provider_type] and
                not self.circuit_breakers[provider_type].is_open()):
                return provider_type
        
        return None
    
    def _calculate_provider_score(self, provider_type: DataProvider, request_type: str) -> float:
        """Calculate provider score based on performance metrics"""
        score = 100.0  # Base score
        
        # Health factor
        if not self.provider_health[provider_type]:
            return 0.0
        
        # Success rate factor
        success_rates = self.provider_success_rate[provider_type]
        if success_rates:
            success_rate = sum(success_rates) / len(success_rates)
            score *= success_rate
        
        # Latency factor (lower is better)
        latencies = self.provider_latency[provider_type]
        if latencies:
            avg_latency = sum(latencies) / len(latencies)
            latency_factor = max(0.1, 1.0 - (avg_latency / 10.0))  # Normalize to 0-1
            score *= latency_factor
        
        # Data quality factor
        quality_scores = self.data_quality_scores[provider_type]
        if quality_scores:
            avg_quality = sum(q.value for q in quality_scores) / len(quality_scores)
            quality_factor = avg_quality / 5.0  # Normalize to 0-1
            score *= quality_factor
        
        # Provider-specific bonuses
        provider_bonuses = {
            DataProvider.POLYGON_IO: 1.2,  # Premium data
            DataProvider.DATABENTO: 1.2,   # Premium data
            DataProvider.IEX_CLOUD: 1.1,   # Good reliability
            DataProvider.ALPHA_VANTAGE: 1.0,
            DataProvider.YAHOO_FINANCE: 0.8  # Free but limited
        }
        
        score *= provider_bonuses.get(provider_type, 1.0)
        
        return score
    
    async def _fetch_with_fallback(self, fetch_func: Callable, *args) -> Any:
        """Execute fetch function with automatic fallback"""
        primary_provider = args[-1] if args else None
        
        # Try primary provider first
        if primary_provider:
            try:
                result = await fetch_func(*args)
                if result:
                    return result
            except Exception as e:
                self.logger.warning(f"Primary provider {primary_provider} failed: {e}")
        
        # Try fallback providers
        for priority in [ProviderPriority.SECONDARY, ProviderPriority.FALLBACK, ProviderPriority.EMERGENCY]:
            for provider_type in self.provider_hierarchy[priority]:
                if provider_type == primary_provider:
                    continue
                
                if not self.provider_health[provider_type]:
                    continue
                
                if self.circuit_breakers[provider_type].is_open():
                    continue
                
                try:
                    # Replace the provider in args
                    new_args = list(args[:-1]) + [provider_type]
                    result = await fetch_func(*new_args)
                    if result:
                        self.logger.info(f"Successfully used fallback provider: {provider_type}")
                        return result
                except Exception as e:
                    self.logger.warning(f"Fallback provider {provider_type} failed: {e}")
        
        return None
    
    async def _get_quote_from_provider(self, symbol: str, provider_type: DataProvider) -> Optional[MarketDataPoint]:
        """Get quote from specific provider"""
        provider = self.providers[provider_type]
        return await provider.get_quote(symbol)
    
    async def _get_historical_from_provider(
        self, 
        symbol: str, 
        start_date: date, 
        end_date: date, 
        interval: str, 
        provider_type: DataProvider
    ) -> Optional[HistoricalData]:
        """Get historical data from specific provider"""
        provider = self.providers[provider_type]
        return await provider.get_historical_data(symbol, start_date, end_date, interval)
    
    async def _get_company_info_from_provider(self, symbol: str, provider_type: DataProvider) -> Optional[CompanyInfo]:
        """Get company info from specific provider"""
        provider = self.providers[provider_type]
        return await provider.get_company_info(symbol)
    
    async def _fetch_quotes_in_batches(self, symbols: List[str], provider_type: DataProvider) -> List[MarketDataPoint]:
        """Fetch quotes in optimal batch sizes"""
        provider = self.providers[provider_type]
        
        # Determine optimal batch size for provider
        batch_sizes = {
            DataProvider.POLYGON_IO: 10,
            DataProvider.DATABENTO: 50,
            DataProvider.IEX_CLOUD: 100,
            DataProvider.ALPHA_VANTAGE: 1,  # No bulk API
            DataProvider.YAHOO_FINANCE: 5
        }
        
        batch_size = batch_sizes.get(provider_type, 10)
        quotes = []
        
        # Process in batches
        for i in range(0, len(symbols), batch_size):
            batch_symbols = symbols[i:i + batch_size]
            
            try:
                if hasattr(provider, 'get_multiple_quotes') and len(batch_symbols) > 1:
                    batch_quotes = await provider.get_multiple_quotes(batch_symbols)
                    quotes.extend(batch_quotes)
                else:
                    # Fall back to individual requests
                    semaphore = asyncio.Semaphore(5)
                    
                    async def fetch_single(symbol):
                        async with semaphore:
                            return await provider.get_quote(symbol)
                    
                    tasks = [fetch_single(symbol) for symbol in batch_symbols]
                    batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    for result in batch_results:
                        if isinstance(result, MarketDataPoint):
                            quotes.append(result)
                            
            except Exception as e:
                self.logger.error(f"Batch quote fetch failed for {provider_type}: {e}")
        
        return quotes
    
    # Data normalization methods
    def _normalize_quote_data(self, quote: MarketDataPoint) -> MarketDataPoint:
        """Normalize quote data across providers"""
        # Round prices to consistent precision
        if quote.price:
            quote.price = round(float(quote.price), self.normalization_rules['price_precision'])
        
        # Ensure volume is integer
        if quote.volume:
            quote.volume = int(quote.volume)
        
        # Normalize timestamp to UTC
        if quote.timestamp and quote.timestamp.tzinfo is None:
            quote.timestamp = quote.timestamp.replace(tzinfo=None)
        
        return quote
    
    def _normalize_historical_data(self, historical: HistoricalData) -> HistoricalData:
        """Normalize historical data"""
        for data_point in historical.data_points:
            self._normalize_quote_data(data_point)
        
        return historical
    
    def _normalize_company_info(self, company: CompanyInfo) -> CompanyInfo:
        """Normalize company information"""
        # Standardize market cap format
        if company.market_cap and isinstance(company.market_cap, str):
            try:
                company.market_cap = float(company.market_cap.replace(',', '').replace('$', ''))
            except ValueError:
                company.market_cap = None
        
        return company
    
    # Data quality assessment
    def _assess_data_quality(self, quote: MarketDataPoint) -> DataQuality:
        """Assess quote data quality"""
        score = 5
        
        if not quote.price or quote.price <= 0:
            return DataQuality.UNUSABLE
        
        if not quote.timestamp:
            score -= 1
        
        if not quote.volume:
            score -= 0.5
        
        if not quote.bid or not quote.ask:
            score -= 0.5
        
        # Check for stale data
        if quote.timestamp:
            age_minutes = (datetime.utcnow() - quote.timestamp).total_seconds() / 60
            if age_minutes > 60:
                score -= 1
        
        return DataQuality(max(1, int(score)))
    
    def _assess_historical_quality(self, historical: HistoricalData) -> DataQuality:
        """Assess historical data quality"""
        if not historical.data_points:
            return DataQuality.UNUSABLE
        
        score = 5
        
        # Check for gaps in data
        timestamps = [dp.timestamp for dp in historical.data_points if dp.timestamp]
        if len(timestamps) < len(historical.data_points) * 0.9:
            score -= 1
        
        # Check for reasonable price ranges
        prices = [dp.price for dp in historical.data_points if dp.price and dp.price > 0]
        if not prices:
            return DataQuality.UNUSABLE
        
        price_ratio = max(prices) / min(prices) if prices else 0
        if price_ratio > 100:  # Suspicious price swings
            score -= 1
        
        return DataQuality(max(1, int(score)))
    
    # Helper methods
    def _is_cache_fresh(self, data, max_age_seconds: int) -> bool:
        """Check if cached data is still fresh"""
        if not hasattr(data, 'timestamp') or not data.timestamp:
            return False
        
        age = (datetime.utcnow() - data.timestamp).total_seconds()
        return age <= max_age_seconds
    
    def _is_historical_cache_fresh(self, historical: HistoricalData, interval: str) -> bool:
        """Check if historical data cache is fresh"""
        # Different intervals have different freshness requirements
        freshness_map = {
            "1m": 60,      # 1 minute
            "5m": 300,     # 5 minutes
            "15m": 900,    # 15 minutes
            "1h": 3600,    # 1 hour
            "1d": 86400,   # 1 day
            "1w": 604800,  # 1 week
            "1M": 2592000  # 1 month
        }
        
        max_age = freshness_map.get(interval, 3600)
        return self._is_cache_fresh(historical, max_age)
    
    def _calculate_historical_cache_ttl(self, interval: str) -> int:
        """Calculate appropriate cache TTL for historical data"""
        ttl_map = {
            "1m": 300,     # 5 minutes
            "5m": 600,     # 10 minutes
            "15m": 1800,   # 30 minutes
            "1h": 3600,    # 1 hour
            "1d": 86400,   # 1 day
            "1w": 604800,  # 1 week
            "1M": 2592000  # 1 month
        }
        
        return ttl_map.get(interval, 3600)
    
    def _provider_supports_interval(self, provider_type: DataProvider, interval: str) -> bool:
        """Check if provider supports the requested interval"""
        provider_intervals = {
            DataProvider.POLYGON_IO: ["1m", "5m", "15m", "1h", "1d", "1w", "1M"],
            DataProvider.DATABENTO: ["1m", "5m", "15m", "1h", "1d", "1w", "1M"],
            DataProvider.ALPHA_VANTAGE: ["1m", "5m", "15m", "1h", "1d", "1w", "1M"],
            DataProvider.IEX_CLOUD: ["1d", "1w", "1M"],
            DataProvider.YAHOO_FINANCE: ["1m", "5m", "15m", "1h", "1d", "1w", "1M"]
        }
        
        supported = provider_intervals.get(provider_type, [])
        return interval in supported
    
    def _provider_supports_date_range(self, provider_type: DataProvider, start_date: date, end_date: date) -> bool:
        """Check if provider supports the requested date range"""
        days_back = (date.today() - start_date).days
        
        # Provider limitations
        limitations = {
            DataProvider.POLYGON_IO: 365 * 10,  # 10 years
            DataProvider.DATABENTO: 365 * 20,   # 20 years
            DataProvider.ALPHA_VANTAGE: 365 * 20, # 20 years
            DataProvider.IEX_CLOUD: 365 * 5,    # 5 years
            DataProvider.YAHOO_FINANCE: 365 * 50 # 50+ years
        }
        
        max_days = limitations.get(provider_type, 365)
        return days_back <= max_days
    
    def _record_provider_performance(self, provider_type: DataProvider, success: bool, latency: float):
        """Record provider performance metrics"""
        self.provider_success_rate[provider_type].append(1.0 if success else 0.0)
        
        if success:
            self.provider_latency[provider_type].append(latency)
    
    # Background monitoring tasks
    async def _health_monitor_loop(self):
        """Background task to monitor provider health"""
        while True:
            try:
                await asyncio.sleep(300)  # Check every 5 minutes
                
                for provider_type, provider in self.providers.items():
                    try:
                        is_healthy = await provider.health_check()
                        self.provider_health[provider_type] = is_healthy
                        self.provider_last_check[provider_type] = datetime.utcnow()
                        
                        if not is_healthy:
                            self.logger.warning(f"Provider {provider_type} health check failed")
                        
                    except Exception as e:
                        self.logger.error(f"Health check error for {provider_type}: {e}")
                        self.provider_health[provider_type] = False
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Health monitor loop error: {e}")
    
    async def _performance_monitor_loop(self):
        """Background task to monitor performance metrics"""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute
                
                # Log performance summary
                for provider_type in self.providers:
                    success_rates = self.provider_success_rate[provider_type]
                    latencies = self.provider_latency[provider_type]
                    
                    if success_rates:
                        avg_success = sum(success_rates) / len(success_rates)
                        avg_latency = sum(latencies) / len(latencies) if latencies else 0
                        
                        self.logger.debug(
                            f"{provider_type}: Success={avg_success:.2%}, Latency={avg_latency:.2f}s"
                        )
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Performance monitor loop error: {e}")
    
    async def _data_quality_monitor_loop(self):
        """Background task to monitor data quality"""
        while True:
            try:
                await asyncio.sleep(300)  # Check every 5 minutes
                
                # Sample some quotes to assess quality
                test_symbols = ["AAPL", "GOOGL", "MSFT", "TSLA", "AMZN"]
                
                for provider_type in self.providers:
                    if not self.provider_health[provider_type]:
                        continue
                    
                    try:
                        # Get a sample quote
                        provider = self.providers[provider_type]
                        quote = await provider.get_quote(test_symbols[0])
                        
                        if quote:
                            quality = self._assess_data_quality(quote)
                            self.data_quality_scores[provider_type].append(quality)
                        
                    except Exception as e:
                        self.logger.debug(f"Quality check failed for {provider_type}: {e}")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Data quality monitor loop error: {e}")
    
    async def shutdown(self):
        """Shutdown the aggregator and cleanup resources"""
        self.logger.info("Shutting down Market Data Aggregator")
        
        # Shutdown providers
        for provider in self.providers.values():
            try:
                await provider._cleanup_session()
            except Exception as e:
                self.logger.error(f"Error shutting down provider: {e}")
        
        # Shutdown cache
        await self.cache_manager.shutdown()
        
        self._initialized = False
        self.logger.info("Market Data Aggregator shutdown complete")
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        provider_status = {}
        
        for provider_type in self.providers:
            success_rates = self.provider_success_rate[provider_type]
            latencies = self.provider_latency[provider_type]
            quality_scores = self.data_quality_scores[provider_type]
            
            provider_status[provider_type.value] = {
                "healthy": self.provider_health[provider_type],
                "circuit_breaker_open": self.circuit_breakers[provider_type].is_open(),
                "success_rate": sum(success_rates) / len(success_rates) if success_rates else 0,
                "avg_latency": sum(latencies) / len(latencies) if latencies else 0,
                "avg_quality": sum(q.value for q in quality_scores) / len(quality_scores) if quality_scores else 0,
                "last_check": self.provider_last_check[provider_type].isoformat()
            }
        
        return {
            "initialized": self._initialized,
            "providers": provider_status,
            "cache_stats": self.cache_manager.get_cache_stats() if self.cache_manager else {},
            "timestamp": datetime.utcnow().isoformat()
        }


class CircuitBreaker:
    """Simple circuit breaker implementation"""
    
    def __init__(self, failure_threshold: int = 5, reset_timeout: int = 300):
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    def is_open(self) -> bool:
        if self.state == "OPEN":
            if (self.last_failure_time and 
                (datetime.utcnow() - self.last_failure_time).total_seconds() > self.reset_timeout):
                self.state = "HALF_OPEN"
                return False
            return True
        return False
    
    def record_success(self):
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"
    
    def record_failure(self):
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"


class AsyncRateLimiter:
    """Async rate limiter"""
    
    def __init__(self, requests_per_minute: int):
        self.requests_per_minute = requests_per_minute
        self.request_timestamps = deque()
    
    async def acquire(self):
        now = datetime.utcnow()
        minute_ago = now - timedelta(minutes=1)
        
        # Remove old timestamps
        while self.request_timestamps and self.request_timestamps[0] <= minute_ago:
            self.request_timestamps.popleft()
        
        if len(self.request_timestamps) >= self.requests_per_minute:
            sleep_time = 60 - (now - self.request_timestamps[0]).total_seconds()
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)
        
        self.request_timestamps.append(now)