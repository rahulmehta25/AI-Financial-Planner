"""
Market Data Manager

Central manager that orchestrates all market data operations with failover mechanisms.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, date
from collections import defaultdict

from .providers import AlphaVantageProvider, YahooFinanceProvider, IEXCloudProvider, BaseProvider
from .cache import RedisCache, CacheManager
from .streaming import StreamManager
from .models import (
    MarketDataPoint, HistoricalData, CompanyInfo, DataProvider, 
    MarketDataRequest, MarketDataResponse, MarketDataType
)
from .config import config


class MarketDataManager:
    """Central market data manager with provider failover and caching"""
    
    def __init__(self):
        self.logger = logging.getLogger("market_data.manager")
        
        # Initialize providers
        self.providers: Dict[DataProvider, BaseProvider] = {}
        self._provider_health: Dict[DataProvider, bool] = {}
        self._provider_last_check: Dict[DataProvider, datetime] = {}
        
        # Initialize cache
        self.cache_manager = CacheManager()
        
        # Initialize streaming
        self.stream_manager = None
        
        # Performance tracking
        self.request_counts = defaultdict(int)
        self.error_counts = defaultdict(int)
        self.failover_counts = defaultdict(int)
        
        # Initialization flag
        self._initialized = False
    
    async def initialize(self):
        """Initialize the market data manager"""
        if self._initialized:
            return
        
        self.logger.info("Initializing Market Data Manager")
        
        try:
            # Initialize providers
            await self._initialize_providers()
            
            # Initialize cache
            await self.cache_manager.initialize()
            
            # Initialize streaming
            self.stream_manager = StreamManager(self.providers)
            
            # Start health monitoring
            self._health_check_task = asyncio.create_task(self._health_check_loop())
            
            self._initialized = True
            self.logger.info("Market Data Manager initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Market Data Manager: {e}")
            raise
    
    async def shutdown(self):
        """Shutdown the market data manager"""
        if not self._initialized:
            return
        
        self.logger.info("Shutting down Market Data Manager")
        
        # Cancel health check task
        if hasattr(self, '_health_check_task'):
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
        
        # Shutdown streaming
        if self.stream_manager:
            await self.stream_manager.stop()
        
        # Shutdown cache
        await self.cache_manager.shutdown()
        
        # Cleanup providers
        for provider in self.providers.values():
            try:
                await provider._cleanup_session()
            except Exception as e:
                self.logger.error(f"Error cleaning up provider {provider.name}: {e}")
        
        self._initialized = False
        self.logger.info("Market Data Manager shutdown complete")
    
    async def _initialize_providers(self):
        """Initialize all data providers"""
        # Alpha Vantage
        if config.alpha_vantage_api_key:
            try:
                provider = AlphaVantageProvider()
                await provider._initialize_session()
                self.providers[DataProvider.ALPHA_VANTAGE] = provider
                self._provider_health[DataProvider.ALPHA_VANTAGE] = True
                self.logger.info("Alpha Vantage provider initialized")
            except Exception as e:
                self.logger.error(f"Failed to initialize Alpha Vantage provider: {e}")
        
        # Yahoo Finance (always available)
        try:
            provider = YahooFinanceProvider()
            await provider._initialize_session()
            self.providers[DataProvider.YAHOO_FINANCE] = provider
            self._provider_health[DataProvider.YAHOO_FINANCE] = True
            self.logger.info("Yahoo Finance provider initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize Yahoo Finance provider: {e}")
        
        # IEX Cloud
        if config.iex_cloud_api_key:
            try:
                provider = IEXCloudProvider()
                await provider._initialize_session()
                self.providers[DataProvider.IEX_CLOUD] = provider
                self._provider_health[DataProvider.IEX_CLOUD] = True
                self.logger.info("IEX Cloud provider initialized")
            except Exception as e:
                self.logger.error(f"Failed to initialize IEX Cloud provider: {e}")
        
        if not self.providers:
            raise RuntimeError("No market data providers could be initialized")
    
    async def _health_check_loop(self):
        """Background task to monitor provider health"""
        while True:
            try:
                await asyncio.sleep(300)  # Check every 5 minutes
                
                for provider_type, provider in self.providers.items():
                    try:
                        is_healthy = await provider.health_check()
                        self._provider_health[provider_type] = is_healthy
                        self._provider_last_check[provider_type] = datetime.utcnow()
                        
                        if not is_healthy:
                            self.logger.warning(f"Provider {provider_type} failed health check")
                        
                    except Exception as e:
                        self.logger.error(f"Error checking health of provider {provider_type}: {e}")
                        self._provider_health[provider_type] = False
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in health check loop: {e}")
    
    async def get_quote(self, symbol: str, use_cache: bool = True) -> Optional[MarketDataPoint]:
        """Get current quote for a symbol with provider failover"""
        self.request_counts['quote'] += 1
        
        if use_cache:
            # Try cache first
            cached_quote = await self.cache_manager.get_quote_cached(
                symbol, 
                lambda s: self._get_quote_from_providers(s)
            )
            if cached_quote:
                return cached_quote
        
        # Fetch directly from providers
        return await self._get_quote_from_providers(symbol)
    
    async def _get_quote_from_providers(self, symbol: str) -> Optional[MarketDataPoint]:
        """Get quote from providers with failover"""
        # Try primary provider first
        primary_provider = self.providers.get(config.primary_provider)
        if primary_provider and self._provider_health.get(config.primary_provider, False):
            try:
                quote = await primary_provider.get_quote(symbol)
                if quote:
                    return quote
            except Exception as e:
                self.logger.warning(f"Primary provider {config.primary_provider} failed for {symbol}: {e}")
                self.error_counts[config.primary_provider] += 1
        
        # Try fallback providers
        for provider_type in config.fallback_providers:
            provider = self.providers.get(provider_type)
            if not provider or not self._provider_health.get(provider_type, False):
                continue
            
            try:
                quote = await provider.get_quote(symbol)
                if quote:
                    self.failover_counts[provider_type] += 1
                    self.logger.info(f"Used fallback provider {provider_type} for {symbol}")
                    return quote
                    
            except Exception as e:
                self.logger.warning(f"Fallback provider {provider_type} failed for {symbol}: {e}")
                self.error_counts[provider_type] += 1
        
        self.logger.error(f"All providers failed for symbol {symbol}")
        return None
    
    async def get_multiple_quotes(self, symbols: List[str], use_cache: bool = True) -> List[MarketDataPoint]:
        """Get quotes for multiple symbols efficiently"""
        self.request_counts['multi_quote'] += 1
        
        if not symbols:
            return []
        
        if use_cache:
            # Use cache manager for intelligent caching
            cached_quotes = await self.cache_manager.get_multiple_quotes_cached(
                symbols,
                lambda syms: self._get_multiple_quotes_from_providers(syms)
            )
            return list(cached_quotes.values())
        
        return await self._get_multiple_quotes_from_providers(symbols)
    
    async def _get_multiple_quotes_from_providers(self, symbols: List[str]) -> List[MarketDataPoint]:
        """Get multiple quotes from providers with failover"""
        quotes = []
        
        # Try primary provider first
        primary_provider = self.providers.get(config.primary_provider)
        if primary_provider and self._provider_health.get(config.primary_provider, False):
            try:
                quotes = await primary_provider.get_multiple_quotes(symbols)
                if quotes and len(quotes) >= len(symbols) * 0.8:  # 80% success rate
                    return quotes
            except Exception as e:
                self.logger.warning(f"Primary provider {config.primary_provider} failed for batch: {e}")
                self.error_counts[config.primary_provider] += 1
        
        # Try fallback providers
        for provider_type in config.fallback_providers:
            provider = self.providers.get(provider_type)
            if not provider or not self._provider_health.get(provider_type, False):
                continue
            
            try:
                quotes = await provider.get_multiple_quotes(symbols)
                if quotes:
                    self.failover_counts[provider_type] += 1
                    self.logger.info(f"Used fallback provider {provider_type} for batch")
                    return quotes
                    
            except Exception as e:
                self.logger.warning(f"Fallback provider {provider_type} failed for batch: {e}")
                self.error_counts[provider_type] += 1
        
        # If all batch methods fail, try individual quotes
        self.logger.warning("All batch providers failed, falling back to individual quotes")
        return await self._get_individual_quotes_fallback(symbols)
    
    async def _get_individual_quotes_fallback(self, symbols: List[str]) -> List[MarketDataPoint]:
        """Fallback to individual quote requests"""
        quotes = []
        semaphore = asyncio.Semaphore(config.max_concurrent_requests)
        
        async def fetch_individual_quote(symbol: str):
            async with semaphore:
                quote = await self._get_quote_from_providers(symbol)
                if quote:
                    quotes.append(quote)
        
        tasks = [fetch_individual_quote(symbol) for symbol in symbols]
        await asyncio.gather(*tasks, return_exceptions=True)
        
        return quotes
    
    async def get_historical_data(
        self, 
        symbol: str, 
        start_date: date, 
        end_date: date,
        interval: str = "1d",
        use_cache: bool = True
    ) -> Optional[HistoricalData]:
        """Get historical data with provider failover"""
        self.request_counts['historical'] += 1
        
        start_date_str = start_date.isoformat()
        end_date_str = end_date.isoformat()
        
        if use_cache:
            # Try cache first
            cached_data = await self.cache_manager.get_historical_cached(
                symbol, start_date_str, end_date_str, interval,
                lambda s, sd, ed, i: self._get_historical_from_providers(s, date.fromisoformat(sd), date.fromisoformat(ed), i)
            )
            if cached_data:
                return cached_data
        
        # Fetch directly from providers
        return await self._get_historical_from_providers(symbol, start_date, end_date, interval)
    
    async def _get_historical_from_providers(
        self, 
        symbol: str, 
        start_date: date, 
        end_date: date, 
        interval: str
    ) -> Optional[HistoricalData]:
        """Get historical data from providers with failover"""
        # Try primary provider first
        primary_provider = self.providers.get(config.primary_provider)
        if primary_provider and self._provider_health.get(config.primary_provider, False):
            try:
                data = await primary_provider.get_historical_data(symbol, start_date, end_date, interval)
                if data:
                    return data
            except Exception as e:
                self.logger.warning(f"Primary provider {config.primary_provider} failed for historical {symbol}: {e}")
                self.error_counts[config.primary_provider] += 1
        
        # Try fallback providers
        for provider_type in config.fallback_providers:
            provider = self.providers.get(provider_type)
            if not provider or not self._provider_health.get(provider_type, False):
                continue
            
            try:
                data = await provider.get_historical_data(symbol, start_date, end_date, interval)
                if data:
                    self.failover_counts[provider_type] += 1
                    self.logger.info(f"Used fallback provider {provider_type} for historical {symbol}")
                    return data
                    
            except Exception as e:
                self.logger.warning(f"Fallback provider {provider_type} failed for historical {symbol}: {e}")
                self.error_counts[provider_type] += 1
        
        self.logger.error(f"All providers failed for historical data {symbol}")
        return None
    
    async def get_company_info(self, symbol: str, use_cache: bool = True) -> Optional[CompanyInfo]:
        """Get company information with provider failover"""
        self.request_counts['company'] += 1
        
        if use_cache:
            # Try cache first
            cached_info = await self.cache_manager.get_company_info_cached(
                symbol,
                lambda s: self._get_company_info_from_providers(s)
            )
            if cached_info:
                return cached_info
        
        # Fetch directly from providers
        return await self._get_company_info_from_providers(symbol)
    
    async def _get_company_info_from_providers(self, symbol: str) -> Optional[CompanyInfo]:
        """Get company info from providers with failover"""
        # Try primary provider first
        primary_provider = self.providers.get(config.primary_provider)
        if primary_provider and self._provider_health.get(config.primary_provider, False):
            try:
                info = await primary_provider.get_company_info(symbol)
                if info:
                    return info
            except Exception as e:
                self.logger.warning(f"Primary provider {config.primary_provider} failed for company info {symbol}: {e}")
                self.error_counts[config.primary_provider] += 1
        
        # Try fallback providers
        for provider_type in config.fallback_providers:
            provider = self.providers.get(provider_type)
            if not provider or not self._provider_health.get(provider_type, False):
                continue
            
            try:
                info = await provider.get_company_info(symbol)
                if info:
                    self.failover_counts[provider_type] += 1
                    self.logger.info(f"Used fallback provider {provider_type} for company info {symbol}")
                    return info
                    
            except Exception as e:
                self.logger.warning(f"Fallback provider {provider_type} failed for company info {symbol}: {e}")
                self.error_counts[provider_type] += 1
        
        self.logger.error(f"All providers failed for company info {symbol}")
        return None
    
    async def process_request(self, request: MarketDataRequest) -> MarketDataResponse:
        """Process a market data request"""
        start_time = datetime.utcnow()
        data_points = []
        errors = []
        
        try:
            if MarketDataType.QUOTE in request.data_types:
                # Get quotes
                if len(request.symbols) == 1:
                    quote = await self.get_quote(request.symbols[0])
                    if quote:
                        data_points.append(quote)
                    else:
                        errors.append(f"Failed to get quote for {request.symbols[0]}")
                else:
                    quotes = await self.get_multiple_quotes(request.symbols)
                    data_points.extend(quotes)
                    
                    # Check for missing quotes
                    found_symbols = {quote.symbol for quote in quotes}
                    for symbol in request.symbols:
                        if symbol.upper() not in found_symbols:
                            errors.append(f"Failed to get quote for {symbol}")
            
            if MarketDataType.HISTORICAL in request.data_types:
                # Get historical data
                for symbol in request.symbols:
                    historical = await self.get_historical_data(
                        symbol, 
                        request.start_date or (datetime.utcnow().date() - timedelta(days=30)),
                        request.end_date or datetime.utcnow().date(),
                        request.interval
                    )
                    if historical:
                        data_points.extend(historical.data_points)
                    else:
                        errors.append(f"Failed to get historical data for {symbol}")
            
            # Determine which provider was used (use primary if available)
            provider_used = config.primary_provider
            if not self._provider_health.get(config.primary_provider, False):
                for provider_type in config.fallback_providers:
                    if self._provider_health.get(provider_type, False):
                        provider_used = provider_type
                        break
            
            return MarketDataResponse(
                success=len(data_points) > 0,
                data=data_points,
                errors=errors,
                provider=provider_used,
                timestamp=datetime.utcnow(),
                cached=False  # Would need to track this more precisely
            )
            
        except Exception as e:
            self.logger.error(f"Error processing request: {e}")
            return MarketDataResponse(
                success=False,
                data=[],
                errors=[str(e)],
                provider=config.primary_provider,
                timestamp=datetime.utcnow(),
                cached=False
            )
    
    async def start_streaming(self, host: str = None, port: int = None):
        """Start real-time streaming"""
        if not self.stream_manager:
            raise RuntimeError("Manager not initialized")
        
        await self.stream_manager.start(host, port)
    
    async def stop_streaming(self):
        """Stop real-time streaming"""
        if self.stream_manager:
            await self.stream_manager.stop()
    
    def get_provider_status(self) -> Dict[str, Any]:
        """Get status of all providers"""
        status = {}
        
        for provider_type in DataProvider:
            provider = self.providers.get(provider_type)
            status[provider_type.value] = {
                "available": provider is not None,
                "healthy": self._provider_health.get(provider_type, False),
                "last_health_check": self._provider_last_check.get(provider_type),
                "request_count": self.request_counts.get(provider_type, 0),
                "error_count": self.error_counts.get(provider_type, 0),
                "failover_count": self.failover_counts.get(provider_type, 0)
            }
            
            if provider:
                status[provider_type.value]["error_rate"] = provider.get_error_count()
        
        return status
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get comprehensive system statistics"""
        return {
            "initialized": self._initialized,
            "providers": self.get_provider_status(),
            "cache": self.cache_manager.get_cache_statistics() if self.cache_manager else {},
            "streaming": self.stream_manager.get_streaming_stats() if self.stream_manager else {},
            "requests": dict(self.request_counts),
            "errors": dict(self.error_counts),
            "failovers": dict(self.failover_counts),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Comprehensive health check"""
        health = {
            "overall_status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "components": {}
        }
        
        # Check providers
        healthy_providers = 0
        for provider_type, is_healthy in self._provider_health.items():
            health["components"][f"provider_{provider_type.value}"] = {
                "status": "healthy" if is_healthy else "unhealthy",
                "available": provider_type in self.providers
            }
            if is_healthy:
                healthy_providers += 1
        
        # Check cache
        try:
            cache_healthy = await self.cache_manager.redis_cache.health_check()
            health["components"]["cache"] = {
                "status": "healthy" if cache_healthy else "unhealthy"
            }
        except Exception as e:
            health["components"]["cache"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            cache_healthy = False
        
        # Check streaming
        if self.stream_manager:
            streaming_stats = self.stream_manager.get_streaming_stats()
            health["components"]["streaming"] = {
                "status": "healthy" if streaming_stats.get("streaming", False) else "stopped"
            }
        
        # Overall status
        if healthy_providers == 0:
            health["overall_status"] = "critical"
        elif healthy_providers < len(self.providers) or not cache_healthy:
            health["overall_status"] = "degraded"
        
        return health