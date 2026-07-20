"""
Cache Manager

High-level cache management with intelligent caching strategies.
"""

import asyncio
import logging
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta
from collections import defaultdict

from .redis_cache import RedisCache
from ..models import MarketDataPoint, HistoricalData, CompanyInfo, DataProvider
from ..config import config


class CacheManager:
    """High-level cache manager with intelligent caching strategies"""
    
    def __init__(self, redis_cache: RedisCache = None):
        self.redis_cache = redis_cache or RedisCache()
        self.logger = logging.getLogger("market_data.cache_manager")
        
        # Cache performance tracking
        self.hit_counts = defaultdict(int)
        self.miss_counts = defaultdict(int)
        self.error_counts = defaultdict(int)
        
        # Cache warming
        self._warm_cache_symbols: set = set()
        self._warming_task: Optional[asyncio.Task] = None
    
    async def initialize(self):
        """Initialize cache manager"""
        try:
            await self.redis_cache.connect()
            self.logger.info("Cache manager initialized")
            
            # Start cache warming if configured
            if hasattr(config, 'warm_cache_symbols') and config.warm_cache_symbols:
                await self.start_cache_warming(config.warm_cache_symbols)
                
        except Exception as e:
            self.logger.error(f"Failed to initialize cache manager: {e}")
            raise
    
    async def shutdown(self):
        """Shutdown cache manager"""
        if self._warming_task:
            self._warming_task.cancel()
            try:
                await self._warming_task
            except asyncio.CancelledError:
                pass
        
        await self.redis_cache.disconnect()
        self.logger.info("Cache manager shutdown")
    
    async def get_quote_cached(self, symbol: str, provider_callback=None) -> Optional[MarketDataPoint]:
        """Get quote with caching strategy"""
        try:
            # Try cache first
            cached_quote = await self.redis_cache.get_quote(symbol)
            
            if cached_quote:
                # Check if cache is still fresh
                age = datetime.utcnow() - cached_quote.timestamp
                if age.total_seconds() < config.quote_cache_ttl:
                    self.hit_counts['quote'] += 1
                    self.logger.debug(f"Cache hit for quote {symbol}")
                    return cached_quote
            
            # Cache miss or expired - fetch fresh data
            self.miss_counts['quote'] += 1
            self.logger.debug(f"Cache miss for quote {symbol}")
            
            if provider_callback:
                fresh_quote = await provider_callback(symbol)
                if fresh_quote:
                    # Cache the fresh data
                    await self.redis_cache.set_quote(fresh_quote)
                    return fresh_quote
            
            # Return stale data if fresh fetch failed
            return cached_quote
            
        except Exception as e:
            self.error_counts['quote'] += 1
            self.logger.error(f"Error in get_quote_cached for {symbol}: {e}")
            return None
    
    async def get_historical_cached(
        self, 
        symbol: str, 
        start_date: str, 
        end_date: str, 
        interval: str = "1d",
        provider_callback=None
    ) -> Optional[HistoricalData]:
        """Get historical data with caching strategy"""
        try:
            # Try cache first
            cached_data = await self.redis_cache.get_historical_data(symbol, start_date, end_date, interval)
            
            if cached_data:
                self.hit_counts['historical'] += 1
                self.logger.debug(f"Cache hit for historical {symbol} {start_date}-{end_date}")
                return cached_data
            
            # Cache miss - fetch fresh data
            self.miss_counts['historical'] += 1
            self.logger.debug(f"Cache miss for historical {symbol} {start_date}-{end_date}")
            
            if provider_callback:
                fresh_data = await provider_callback(symbol, start_date, end_date, interval)
                if fresh_data:
                    # Cache the fresh data
                    await self.redis_cache.set_historical_data(fresh_data, interval)
                    return fresh_data
            
            return None
            
        except Exception as e:
            self.error_counts['historical'] += 1
            self.logger.error(f"Error in get_historical_cached for {symbol}: {e}")
            return None
    
    async def get_company_info_cached(self, symbol: str, provider_callback=None) -> Optional[CompanyInfo]:
        """Get company info with caching strategy"""
        try:
            # Try cache first
            cached_info = await self.redis_cache.get_company_info(symbol)
            
            if cached_info:
                # Check if cache is still fresh (company info changes rarely)
                age = datetime.utcnow() - cached_info.last_updated
                if age.total_seconds() < config.company_info_cache_ttl:
                    self.hit_counts['company'] += 1
                    self.logger.debug(f"Cache hit for company info {symbol}")
                    return cached_info
            
            # Cache miss or expired - fetch fresh data
            self.miss_counts['company'] += 1
            self.logger.debug(f"Cache miss for company info {symbol}")
            
            if provider_callback:
                fresh_info = await provider_callback(symbol)
                if fresh_info:
                    # Cache the fresh data
                    await self.redis_cache.set_company_info(fresh_info)
                    return fresh_info
            
            # Return stale data if fresh fetch failed
            return cached_info
            
        except Exception as e:
            self.error_counts['company'] += 1
            self.logger.error(f"Error in get_company_info_cached for {symbol}: {e}")
            return None
    
    async def get_multiple_quotes_cached(
        self, 
        symbols: List[str], 
        provider_callback=None
    ) -> Dict[str, MarketDataPoint]:
        """Get multiple quotes with intelligent caching"""
        if not symbols:
            return {}
        
        try:
            # Get cached quotes
            cached_quotes = await self.redis_cache.get_multiple_quotes(symbols)
            fresh_quotes = {}
            missing_symbols = []
            
            # Identify missing or stale quotes
            for symbol in symbols:
                symbol_upper = symbol.upper()
                cached_quote = cached_quotes.get(symbol_upper)
                
                if cached_quote:
                    # Check freshness
                    age = datetime.utcnow() - cached_quote.timestamp
                    if age.total_seconds() < config.quote_cache_ttl:
                        fresh_quotes[symbol_upper] = cached_quote
                        self.hit_counts['quote'] += 1
                        continue
                
                # Need fresh data
                missing_symbols.append(symbol)
                self.miss_counts['quote'] += 1
            
            # Fetch missing quotes
            if missing_symbols and provider_callback:
                try:
                    new_quotes = await provider_callback(missing_symbols)
                    if new_quotes:
                        # Cache new quotes
                        await self.redis_cache.set_multiple_quotes(new_quotes)
                        
                        # Add to results
                        for quote in new_quotes:
                            fresh_quotes[quote.symbol.upper()] = quote
                
                except Exception as e:
                    self.logger.error(f"Error fetching fresh quotes for {missing_symbols}: {e}")
                    
                    # Use stale data for missing symbols
                    for symbol in missing_symbols:
                        symbol_upper = symbol.upper()
                        if symbol_upper in cached_quotes:
                            fresh_quotes[symbol_upper] = cached_quotes[symbol_upper]
            
            return fresh_quotes
            
        except Exception as e:
            self.error_counts['quote'] += 1
            self.logger.error(f"Error in get_multiple_quotes_cached: {e}")
            return {}
    
    async def preload_quotes(self, symbols: List[str], provider_callback=None):
        """Preload quotes into cache"""
        if not symbols or not provider_callback:
            return
        
        try:
            self.logger.info(f"Preloading quotes for {len(symbols)} symbols")
            
            # Fetch fresh quotes
            quotes = await provider_callback(symbols)
            if quotes:
                # Cache all quotes
                await self.redis_cache.set_multiple_quotes(quotes)
                self.logger.info(f"Preloaded {len(quotes)} quotes into cache")
            
        except Exception as e:
            self.logger.error(f"Error preloading quotes: {e}")
    
    async def start_cache_warming(self, symbols: List[str]):
        """Start background cache warming for popular symbols"""
        self._warm_cache_symbols = set(symbol.upper() for symbol in symbols)
        
        if self._warming_task:
            self._warming_task.cancel()
        
        self._warming_task = asyncio.create_task(self._cache_warming_loop())
        self.logger.info(f"Started cache warming for {len(symbols)} symbols")
    
    async def _cache_warming_loop(self):
        """Background loop to keep cache warm"""
        while True:
            try:
                # Warm cache every 30 seconds
                await asyncio.sleep(30)
                
                if not self._warm_cache_symbols:
                    continue
                
                # Check which symbols need refreshing
                symbols_to_refresh = []
                
                for symbol in self._warm_cache_symbols:
                    cached_quote = await self.redis_cache.get_quote(symbol)
                    
                    if not cached_quote:
                        symbols_to_refresh.append(symbol)
                    else:
                        # Check if approaching expiration (refresh when 75% of TTL has passed)
                        age = datetime.utcnow() - cached_quote.timestamp
                        refresh_threshold = config.quote_cache_ttl * 0.75
                        
                        if age.total_seconds() > refresh_threshold:
                            symbols_to_refresh.append(symbol)
                
                if symbols_to_refresh:
                    self.logger.debug(f"Cache warming: refreshing {len(symbols_to_refresh)} symbols")
                    # Note: Would need provider callback here in actual implementation
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in cache warming loop: {e}")
                await asyncio.sleep(60)  # Wait longer on error
    
    async def invalidate_symbol(self, symbol: str):
        """Invalidate cached data for a symbol"""
        try:
            # Delete quote cache
            await self.redis_cache.delete_quote(symbol)
            
            # Delete historical data cache (pattern match)
            pattern = f"historical:{symbol.upper()}:*"
            await self.redis_cache.delete_pattern(pattern)
            
            self.logger.info(f"Invalidated cache for symbol {symbol}")
            
        except Exception as e:
            self.logger.error(f"Error invalidating cache for {symbol}: {e}")
    
    async def clear_all_cache(self):
        """Clear all cached data"""
        try:
            patterns = [
                "quote:*",
                "historical:*", 
                "company:*",
                "news:*"
            ]
            
            total_deleted = 0
            for pattern in patterns:
                deleted = await self.redis_cache.delete_pattern(pattern)
                total_deleted += deleted
            
            self.logger.info(f"Cleared all cache: {total_deleted} keys deleted")
            
        except Exception as e:
            self.logger.error(f"Error clearing all cache: {e}")
    
    def get_cache_statistics(self) -> Dict[str, Any]:
        """Get cache performance statistics"""
        total_hits = sum(self.hit_counts.values())
        total_misses = sum(self.miss_counts.values())
        total_errors = sum(self.error_counts.values())
        total_requests = total_hits + total_misses
        
        hit_rate = total_hits / total_requests if total_requests > 0 else 0
        
        return {
            "performance": {
                "total_hits": total_hits,
                "total_misses": total_misses,
                "total_errors": total_errors,
                "total_requests": total_requests,
                "hit_rate": hit_rate,
                "error_rate": total_errors / total_requests if total_requests > 0 else 0
            },
            "by_type": {
                "quote": {
                    "hits": self.hit_counts['quote'],
                    "misses": self.miss_counts['quote'],
                    "errors": self.error_counts['quote']
                },
                "historical": {
                    "hits": self.hit_counts['historical'],
                    "misses": self.miss_counts['historical'],
                    "errors": self.error_counts['historical']
                },
                "company": {
                    "hits": self.hit_counts['company'],
                    "misses": self.miss_counts['company'],
                    "errors": self.error_counts['company']
                }
            },
            "cache_warming": {
                "enabled": self._warming_task is not None and not self._warming_task.done(),
                "symbols_count": len(self._warm_cache_symbols),
                "symbols": list(self._warm_cache_symbols)
            }
        }
    
    def reset_statistics(self):
        """Reset cache performance statistics"""
        self.hit_counts.clear()
        self.miss_counts.clear()
        self.error_counts.clear()
        self.logger.info("Cache statistics reset")
    
    async def get_detailed_stats(self) -> Dict[str, Any]:
        """Get detailed cache statistics including Redis stats"""
        cache_stats = await self.redis_cache.get_cache_stats()
        manager_stats = self.get_cache_statistics()
        
        return {
            "redis": cache_stats,
            "manager": manager_stats,
            "timestamp": datetime.utcnow().isoformat()
        }