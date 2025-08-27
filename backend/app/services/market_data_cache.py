"""
Market Data Caching Service
Provides efficient caching for market data with TTL and intelligent cache management
"""

import asyncio
import json
import logging
import hashlib
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from decimal import Decimal
import redis.asyncio as redis
from redis.asyncio import Redis

from app.core.config import settings


class MarketDataCache:
    """Advanced caching service for market data"""
    
    def __init__(self):
        self.logger = logging.getLogger("market_data_cache")
        self.redis_client: Optional[Redis] = None
        
        # Cache TTL settings (in seconds)
        self.cache_ttl = {
            "quote": 60,           # 1 minute for live quotes
            "historical_1d": 3600, # 1 hour for daily historical data
            "historical_intraday": 300,  # 5 minutes for intraday data
            "technical_analysis": 300,   # 5 minutes for technical indicators
            "sp500_data": 1800,    # 30 minutes for S&P 500 data
            "sector_performance": 900,   # 15 minutes for sector data
            "market_indices": 300, # 5 minutes for market indices
            "news": 600,          # 10 minutes for news
            "search": 86400,      # 24 hours for symbol search results
            "company_info": 86400 # 24 hours for company information
        }
        
        # Cache key prefixes
        self.key_prefix = "financial_planning:market_data:"
        
    async def initialize(self):
        """Initialize Redis connection"""
        try:
            redis_url = getattr(settings, 'REDIS_URL', 'redis://localhost:6379')
            self.redis_client = redis.from_url(
                redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                max_connections=20
            )
            
            # Test connection
            await self.redis_client.ping()
            self.logger.info("Redis connection initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Redis connection: {e}")
            self.redis_client = None
    
    async def shutdown(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()
            self.logger.info("Redis connection closed")
    
    def _generate_cache_key(self, key_type: str, *args) -> str:
        """Generate a cache key from type and arguments"""
        # Create a unique key from arguments
        key_data = "_".join(str(arg) for arg in args if arg is not None)
        key_hash = hashlib.md5(key_data.encode()).hexdigest()[:8]
        return f"{self.key_prefix}{key_type}:{key_hash}:{key_data}"
    
    def _serialize_data(self, data: Any) -> str:
        """Serialize data for caching"""
        def json_serializer(obj):
            """Custom JSON serializer for special types"""
            if isinstance(obj, Decimal):
                return float(obj)
            elif isinstance(obj, datetime):
                return obj.isoformat()
            elif hasattr(obj, 'dict'):
                return obj.dict()
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
        
        return json.dumps(data, default=json_serializer, ensure_ascii=False)
    
    def _deserialize_data(self, data: str) -> Any:
        """Deserialize cached data"""
        try:
            return json.loads(data)
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to deserialize cached data: {e}")
            return None
    
    async def get(self, key_type: str, *args) -> Optional[Any]:
        """Get data from cache"""
        if not self.redis_client:
            return None
        
        try:
            cache_key = self._generate_cache_key(key_type, *args)
            cached_data = await self.redis_client.get(cache_key)
            
            if cached_data:
                self.logger.debug(f"Cache hit for key: {key_type}")
                return self._deserialize_data(cached_data)
            
            self.logger.debug(f"Cache miss for key: {key_type}")
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting from cache: {e}")
            return None
    
    async def set(self, key_type: str, data: Any, *args, ttl: Optional[int] = None) -> bool:
        """Set data in cache"""
        if not self.redis_client:
            return False
        
        try:
            cache_key = self._generate_cache_key(key_type, *args)
            serialized_data = self._serialize_data(data)
            
            # Use default TTL if not specified
            if ttl is None:
                ttl = self.cache_ttl.get(key_type, 300)
            
            await self.redis_client.setex(cache_key, ttl, serialized_data)
            self.logger.debug(f"Cached data for key: {key_type}, TTL: {ttl}s")
            return True
            
        except Exception as e:
            self.logger.error(f"Error setting cache: {e}")
            return False
    
    async def delete(self, key_type: str, *args) -> bool:
        """Delete data from cache"""
        if not self.redis_client:
            return False
        
        try:
            cache_key = self._generate_cache_key(key_type, *args)
            result = await self.redis_client.delete(cache_key)
            return result > 0
            
        except Exception as e:
            self.logger.error(f"Error deleting from cache: {e}")
            return False
    
    async def get_or_fetch(
        self, 
        key_type: str, 
        fetch_func: Callable, 
        *args,
        ttl: Optional[int] = None,
        force_refresh: bool = False
    ) -> Optional[Any]:
        """Get data from cache or fetch if not available"""
        
        # Check cache first unless force refresh
        if not force_refresh:
            cached_data = await self.get(key_type, *args)
            if cached_data is not None:
                return cached_data
        
        # Fetch new data
        try:
            self.logger.debug(f"Fetching fresh data for key: {key_type}")
            fresh_data = await fetch_func(*args)
            
            if fresh_data is not None:
                # Cache the fresh data
                await self.set(key_type, fresh_data, *args, ttl=ttl)
            
            return fresh_data
            
        except Exception as e:
            self.logger.error(f"Error fetching data for {key_type}: {e}")
            return None
    
    async def get_multiple_quotes_cached(
        self, 
        symbols: List[str], 
        fetch_func: Callable
    ) -> Dict[str, Any]:
        """Get multiple quotes with intelligent caching"""
        results = {}
        uncached_symbols = []
        
        # Check cache for each symbol
        for symbol in symbols:
            cached_quote = await self.get("quote", symbol)
            if cached_quote:
                results[symbol] = cached_quote
            else:
                uncached_symbols.append(symbol)
        
        # Fetch uncached symbols
        if uncached_symbols:
            try:
                fresh_quotes = await fetch_func(uncached_symbols)
                
                # Cache and add fresh quotes
                for quote in fresh_quotes:
                    symbol = quote.get("symbol")
                    if symbol:
                        await self.set("quote", quote, symbol)
                        results[symbol] = quote
                        
            except Exception as e:
                self.logger.error(f"Error fetching multiple quotes: {e}")
        
        return results
    
    async def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate all cache keys matching a pattern"""
        if not self.redis_client:
            return 0
        
        try:
            full_pattern = f"{self.key_prefix}{pattern}*"
            keys = await self.redis_client.keys(full_pattern)
            
            if keys:
                deleted = await self.redis_client.delete(*keys)
                self.logger.info(f"Invalidated {deleted} cache entries matching pattern: {pattern}")
                return deleted
            
            return 0
            
        except Exception as e:
            self.logger.error(f"Error invalidating cache pattern {pattern}: {e}")
            return 0
    
    async def get_cache_statistics(self) -> Dict[str, Any]:
        """Get cache statistics"""
        if not self.redis_client:
            return {"status": "disconnected"}
        
        try:
            info = await self.redis_client.info()
            
            # Count keys by type
            key_counts = {}
            for key_type in self.cache_ttl.keys():
                pattern = f"{self.key_prefix}{key_type}:*"
                keys = await self.redis_client.keys(pattern)
                key_counts[key_type] = len(keys)
            
            return {
                "status": "connected",
                "memory_usage": info.get("used_memory_human", "unknown"),
                "connected_clients": info.get("connected_clients", 0),
                "total_keys": await self.redis_client.dbsize(),
                "key_counts_by_type": key_counts,
                "cache_ttl_settings": self.cache_ttl.copy()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting cache statistics: {e}")
            return {"status": "error", "error": str(e)}
    
    async def health_check(self) -> bool:
        """Check Redis health"""
        if not self.redis_client:
            return False
        
        try:
            await self.redis_client.ping()
            return True
        except Exception as e:
            self.logger.error(f"Redis health check failed: {e}")
            return False
    
    async def cleanup_expired_keys(self) -> int:
        """Manually cleanup expired keys (Redis handles this automatically, but this is for monitoring)"""
        if not self.redis_client:
            return 0
        
        try:
            # Get all our keys
            pattern = f"{self.key_prefix}*"
            keys = await self.redis_client.keys(pattern)
            
            expired_count = 0
            for key in keys:
                ttl = await self.redis_client.ttl(key)
                if ttl == -2:  # Key doesn't exist (expired)
                    expired_count += 1
            
            self.logger.info(f"Found {expired_count} expired keys during cleanup")
            return expired_count
            
        except Exception as e:
            self.logger.error(f"Error during cache cleanup: {e}")
            return 0
    
    # Specialized cache methods for different data types
    
    async def cache_quote(self, symbol: str, quote_data: Dict[str, Any]) -> bool:
        """Cache a stock quote"""
        return await self.set("quote", quote_data, symbol)
    
    async def get_cached_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get cached stock quote"""
        return await self.get("quote", symbol)
    
    async def cache_historical_data(
        self, 
        symbol: str, 
        start_date: str, 
        end_date: str, 
        interval: str, 
        data: Dict[str, Any]
    ) -> bool:
        """Cache historical data"""
        key_type = "historical_intraday" if interval in ["1m", "5m", "15m", "30m", "1h"] else "historical_1d"
        return await self.set(key_type, data, symbol, start_date, end_date, interval)
    
    async def get_cached_historical_data(
        self, 
        symbol: str, 
        start_date: str, 
        end_date: str, 
        interval: str
    ) -> Optional[Dict[str, Any]]:
        """Get cached historical data"""
        key_type = "historical_intraday" if interval in ["1m", "5m", "15m", "30m", "1h"] else "historical_1d"
        return await self.get(key_type, symbol, start_date, end_date, interval)
    
    async def cache_technical_analysis(
        self, 
        symbol: str, 
        period: str, 
        interval: str, 
        analysis: Dict[str, Any]
    ) -> bool:
        """Cache technical analysis"""
        return await self.set("technical_analysis", analysis, symbol, period, interval)
    
    async def get_cached_technical_analysis(
        self, 
        symbol: str, 
        period: str, 
        interval: str
    ) -> Optional[Dict[str, Any]]:
        """Get cached technical analysis"""
        return await self.get("technical_analysis", symbol, period, interval)
    
    async def cache_sp500_data(self, period: str, data: Dict[str, Any]) -> bool:
        """Cache S&P 500 data"""
        return await self.set("sp500_data", data, period)
    
    async def get_cached_sp500_data(self, period: str) -> Optional[Dict[str, Any]]:
        """Get cached S&P 500 data"""
        return await self.get("sp500_data", period)