"""
Redis Cache Implementation

Redis-based caching for market data with TTL management and serialization.
"""

import json
import pickle
import logging
from typing import Optional, Any, Dict, List, Union
from datetime import datetime, timedelta
from redis import asyncio as aioredis
from redis.asyncio import Redis

from ..models import MarketDataPoint, HistoricalData, CompanyInfo
from ..config import config


class RedisCache:
    """Redis cache for market data"""
    
    def __init__(self, redis_url: str = None):
        self.redis_url = redis_url or config.redis_url
        self.redis: Optional[Redis] = None
        self.logger = logging.getLogger("market_data.redis_cache")
        
        # Cache key prefixes
        self.QUOTE_PREFIX = "quote:"
        self.HISTORICAL_PREFIX = "historical:"
        self.COMPANY_PREFIX = "company:"
        self.NEWS_PREFIX = "news:"
        self.BATCH_PREFIX = "batch:"
        
        # Cache TTLs (seconds)
        self.quote_ttl = config.quote_cache_ttl
        self.historical_ttl = config.historical_cache_ttl
        self.company_ttl = config.company_info_cache_ttl
    
    async def connect(self):
        """Connect to Redis"""
        try:
            self.redis = await aioredis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=False,  # We'll handle encoding ourselves
                max_connections=20,
                retry_on_timeout=True
            )
            
            # Test connection
            await self.redis.ping()
            self.logger.info("Connected to Redis")
            
        except Exception as e:
            self.logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    async def disconnect(self):
        """Disconnect from Redis"""
        if self.redis:
            await self.redis.close()
            self.logger.info("Disconnected from Redis")
    
    async def get_quote(self, symbol: str) -> Optional[MarketDataPoint]:
        """Get cached quote for a symbol"""
        if not self.redis:
            return None
        
        key = f"{self.QUOTE_PREFIX}{symbol.upper()}"
        
        try:
            data = await self.redis.get(key)
            if data:
                quote_dict = pickle.loads(data)
                return MarketDataPoint(**quote_dict)
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting cached quote for {symbol}: {e}")
            return None
    
    async def set_quote(self, quote: MarketDataPoint, ttl: int = None) -> bool:
        """Cache a quote with TTL"""
        if not self.redis:
            return False
        
        key = f"{self.QUOTE_PREFIX}{quote.symbol.upper()}"
        ttl = ttl or self.quote_ttl
        
        try:
            # Convert to dict and serialize
            quote_dict = quote.dict()
            data = pickle.dumps(quote_dict)
            
            await self.redis.setex(key, ttl, data)
            self.logger.debug(f"Cached quote for {quote.symbol} (TTL: {ttl}s)")
            return True
            
        except Exception as e:
            self.logger.error(f"Error caching quote for {quote.symbol}: {e}")
            return False
    
    async def get_historical_data(self, symbol: str, start_date: str, end_date: str, interval: str = "1d") -> Optional[HistoricalData]:
        """Get cached historical data"""
        if not self.redis:
            return None
        
        key = f"{self.HISTORICAL_PREFIX}{symbol.upper()}:{start_date}:{end_date}:{interval}"
        
        try:
            data = await self.redis.get(key)
            if data:
                historical_dict = pickle.loads(data)
                return HistoricalData(**historical_dict)
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting cached historical data for {symbol}: {e}")
            return None
    
    async def set_historical_data(self, historical: HistoricalData, interval: str = "1d", ttl: int = None) -> bool:
        """Cache historical data with TTL"""
        if not self.redis:
            return False
        
        start_date = historical.start_date.isoformat()
        end_date = historical.end_date.isoformat()
        key = f"{self.HISTORICAL_PREFIX}{historical.symbol.upper()}:{start_date}:{end_date}:{interval}"
        ttl = ttl or self.historical_ttl
        
        try:
            # Convert to dict and serialize
            historical_dict = historical.dict()
            data = pickle.dumps(historical_dict)
            
            await self.redis.setex(key, ttl, data)
            self.logger.debug(f"Cached historical data for {historical.symbol} (TTL: {ttl}s)")
            return True
            
        except Exception as e:
            self.logger.error(f"Error caching historical data for {historical.symbol}: {e}")
            return False
    
    async def get_company_info(self, symbol: str) -> Optional[CompanyInfo]:
        """Get cached company information"""
        if not self.redis:
            return None
        
        key = f"{self.COMPANY_PREFIX}{symbol.upper()}"
        
        try:
            data = await self.redis.get(key)
            if data:
                company_dict = pickle.loads(data)
                return CompanyInfo(**company_dict)
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting cached company info for {symbol}: {e}")
            return None
    
    async def set_company_info(self, company: CompanyInfo, ttl: int = None) -> bool:
        """Cache company information with TTL"""
        if not self.redis:
            return False
        
        key = f"{self.COMPANY_PREFIX}{company.symbol.upper()}"
        ttl = ttl or self.company_ttl
        
        try:
            # Convert to dict and serialize
            company_dict = company.dict()
            data = pickle.dumps(company_dict)
            
            await self.redis.setex(key, ttl, data)
            self.logger.debug(f"Cached company info for {company.symbol} (TTL: {ttl}s)")
            return True
            
        except Exception as e:
            self.logger.error(f"Error caching company info for {company.symbol}: {e}")
            return False
    
    async def get_multiple_quotes(self, symbols: List[str]) -> Dict[str, MarketDataPoint]:
        """Get multiple cached quotes efficiently"""
        if not self.redis or not symbols:
            return {}
        
        # Prepare keys
        keys = [f"{self.QUOTE_PREFIX}{symbol.upper()}" for symbol in symbols]
        quotes = {}
        
        try:
            # Use pipeline for efficiency
            pipe = self.redis.pipeline()
            for key in keys:
                pipe.get(key)
            
            results = await pipe.execute()
            
            for i, (symbol, data) in enumerate(zip(symbols, results)):
                if data:
                    try:
                        quote_dict = pickle.loads(data)
                        quotes[symbol.upper()] = MarketDataPoint(**quote_dict)
                    except Exception as e:
                        self.logger.error(f"Error deserializing quote for {symbol}: {e}")
            
            return quotes
            
        except Exception as e:
            self.logger.error(f"Error getting multiple cached quotes: {e}")
            return {}
    
    async def set_multiple_quotes(self, quotes: List[MarketDataPoint], ttl: int = None) -> int:
        """Cache multiple quotes efficiently"""
        if not self.redis or not quotes:
            return 0
        
        ttl = ttl or self.quote_ttl
        cached_count = 0
        
        try:
            # Use pipeline for efficiency
            pipe = self.redis.pipeline()
            
            for quote in quotes:
                key = f"{self.QUOTE_PREFIX}{quote.symbol.upper()}"
                quote_dict = quote.dict()
                data = pickle.dumps(quote_dict)
                pipe.setex(key, ttl, data)
            
            await pipe.execute()
            cached_count = len(quotes)
            
            self.logger.debug(f"Cached {cached_count} quotes (TTL: {ttl}s)")
            
        except Exception as e:
            self.logger.error(f"Error caching multiple quotes: {e}")
        
        return cached_count
    
    async def delete_quote(self, symbol: str) -> bool:
        """Delete cached quote for a symbol"""
        if not self.redis:
            return False
        
        key = f"{self.QUOTE_PREFIX}{symbol.upper()}"
        
        try:
            result = await self.redis.delete(key)
            return result > 0
            
        except Exception as e:
            self.logger.error(f"Error deleting cached quote for {symbol}: {e}")
            return False
    
    async def delete_pattern(self, pattern: str) -> int:
        """Delete keys matching a pattern"""
        if not self.redis:
            return 0
        
        try:
            keys = []
            async for key in self.redis.scan_iter(match=pattern):
                keys.append(key.decode() if isinstance(key, bytes) else key)
            
            if keys:
                return await self.redis.delete(*keys)
            return 0
            
        except Exception as e:
            self.logger.error(f"Error deleting pattern {pattern}: {e}")
            return 0
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        if not self.redis:
            return {}
        
        try:
            info = await self.redis.info()
            
            # Count keys by prefix
            quote_count = 0
            historical_count = 0
            company_count = 0
            
            async for key in self.redis.scan_iter(match=f"{self.QUOTE_PREFIX}*"):
                quote_count += 1
            
            async for key in self.redis.scan_iter(match=f"{self.HISTORICAL_PREFIX}*"):
                historical_count += 1
            
            async for key in self.redis.scan_iter(match=f"{self.COMPANY_PREFIX}*"):
                company_count += 1
            
            return {
                "redis_info": {
                    "used_memory": info.get("used_memory_human"),
                    "connected_clients": info.get("connected_clients"),
                    "total_commands_processed": info.get("total_commands_processed"),
                    "keyspace_hits": info.get("keyspace_hits"),
                    "keyspace_misses": info.get("keyspace_misses"),
                },
                "cache_counts": {
                    "quotes": quote_count,
                    "historical": historical_count,
                    "company_info": company_count,
                    "total": quote_count + historical_count + company_count
                },
                "hit_ratio": self._calculate_hit_ratio(info)
            }
            
        except Exception as e:
            self.logger.error(f"Error getting cache stats: {e}")
            return {}
    
    def _calculate_hit_ratio(self, info: Dict[str, Any]) -> float:
        """Calculate cache hit ratio"""
        hits = info.get("keyspace_hits", 0)
        misses = info.get("keyspace_misses", 0)
        total = hits + misses
        
        if total == 0:
            return 0.0
        
        return hits / total
    
    async def clear_expired_keys(self):
        """Manually clear expired keys (Redis usually handles this automatically)"""
        if not self.redis:
            return
        
        try:
            # Redis handles expiration automatically, but we can force cleanup
            await self.redis.execute_command("MEMORY", "PURGE")
            self.logger.info("Triggered Redis memory purge")
            
        except Exception as e:
            self.logger.error(f"Error clearing expired keys: {e}")
    
    async def set_json(self, key: str, data: Dict[str, Any], ttl: int = 3600) -> bool:
        """Set JSON data with TTL"""
        if not self.redis:
            return False
        
        try:
            json_data = json.dumps(data, default=str)
            await self.redis.setex(key, ttl, json_data)
            return True
            
        except Exception as e:
            self.logger.error(f"Error setting JSON data for key {key}: {e}")
            return False
    
    async def get_json(self, key: str) -> Optional[Dict[str, Any]]:
        """Get JSON data"""
        if not self.redis:
            return None
        
        try:
            data = await self.redis.get(key)
            if data:
                if isinstance(data, bytes):
                    data = data.decode()
                return json.loads(data)
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting JSON data for key {key}: {e}")
            return None
    
    async def health_check(self) -> bool:
        """Check Redis connection health"""
        try:
            if self.redis:
                await self.redis.ping()
                return True
            return False
            
        except Exception as e:
            self.logger.error(f"Redis health check failed: {e}")
            return False