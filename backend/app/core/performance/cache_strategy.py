"""
Multi-layer Caching Strategy for Financial Planning System
Implements L1 (in-memory), L2 (Redis), L3 (CDN) caching with smart invalidation
"""

import time
import json
import hashlib
import pickle
from typing import Any, Optional, Dict, List, Callable, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from functools import wraps
from collections import OrderedDict
import asyncio
from enum import Enum

import redis
from redis.asyncio import Redis as AsyncRedis
from redis.sentinel import Sentinel
import aioredis
import msgpack
import lz4.frame

from app.core.config import settings

import logging
logger = logging.getLogger(__name__)


class CacheLevel(Enum):
    """Cache hierarchy levels"""
    L1_MEMORY = "memory"
    L2_REDIS = "redis"
    L3_CDN = "cdn"
    L4_DISK = "disk"


@dataclass
class CacheEntry:
    """Cache entry with metadata"""
    key: str
    value: Any
    ttl: int
    created_at: datetime = field(default_factory=datetime.now)
    access_count: int = 0
    last_accessed: datetime = field(default_factory=datetime.now)
    size_bytes: int = 0
    compression_ratio: float = 1.0
    
    def is_expired(self) -> bool:
        """Check if cache entry has expired"""
        return datetime.now() > self.created_at + timedelta(seconds=self.ttl)
    
    def update_access(self):
        """Update access statistics"""
        self.access_count += 1
        self.last_accessed = datetime.now()


class LRUCache:
    """
    Thread-safe LRU cache implementation for L1 memory caching
    """
    
    def __init__(self, max_size: int = 10000, max_memory_mb: int = 512):
        self.max_size = max_size
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.current_memory_bytes = 0
        self.lock = asyncio.Lock()
        
        # Statistics
        self.hits = 0
        self.misses = 0
        self.evictions = 0
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        async with self.lock:
            if key in self.cache:
                entry = self.cache[key]
                
                if entry.is_expired():
                    del self.cache[key]
                    self.current_memory_bytes -= entry.size_bytes
                    self.misses += 1
                    return None
                
                # Move to end (most recently used)
                self.cache.move_to_end(key)
                entry.update_access()
                self.hits += 1
                return entry.value
            
            self.misses += 1
            return None
    
    async def set(self, key: str, value: Any, ttl: int = 300):
        """Set value in cache"""
        async with self.lock:
            # Calculate size
            size_bytes = len(pickle.dumps(value))
            
            # Check if we need to evict
            while (len(self.cache) >= self.max_size or 
                   self.current_memory_bytes + size_bytes > self.max_memory_bytes):
                if not self.cache:
                    break
                
                # Evict least recently used
                evicted_key, evicted_entry = self.cache.popitem(last=False)
                self.current_memory_bytes -= evicted_entry.size_bytes
                self.evictions += 1
            
            # Add new entry
            entry = CacheEntry(
                key=key,
                value=value,
                ttl=ttl,
                size_bytes=size_bytes
            )
            
            self.cache[key] = entry
            self.current_memory_bytes += size_bytes
    
    async def invalidate(self, pattern: str = None):
        """Invalidate cache entries matching pattern"""
        async with self.lock:
            if pattern:
                keys_to_delete = [
                    k for k in self.cache.keys() 
                    if pattern in k or k.startswith(pattern)
                ]
                for key in keys_to_delete:
                    entry = self.cache.pop(key)
                    self.current_memory_bytes -= entry.size_bytes
            else:
                self.cache.clear()
                self.current_memory_bytes = 0
    
    def get_stats(self) -> Dict:
        """Get cache statistics"""
        hit_rate = self.hits / (self.hits + self.misses) if (self.hits + self.misses) > 0 else 0
        return {
            'size': len(self.cache),
            'memory_mb': self.current_memory_bytes / (1024 * 1024),
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': hit_rate,
            'evictions': self.evictions
        }


class RedisCache:
    """
    Distributed Redis cache with compression and clustering support
    """
    
    def __init__(self):
        # Redis connection pools
        self.redis_pool = None
        self.async_redis = None
        
        # Configuration
        self.compression_threshold = 1024  # Compress values larger than 1KB
        self.default_ttl = 3600  # 1 hour
        
        # Statistics
        self.stats = {
            'hits': 0,
            'misses': 0,
            'compressions': 0,
            'decompressions': 0
        }
    
    async def connect(self):
        """Initialize Redis connections"""
        try:
            # Setup Redis Sentinel for HA (if configured)
            if hasattr(settings, 'REDIS_SENTINELS'):
                sentinel = Sentinel(settings.REDIS_SENTINELS)
                self.redis_pool = sentinel.master_for(
                    settings.REDIS_MASTER_NAME,
                    socket_keepalive=True,
                    socket_keepalive_options={
                        1: 1,  # TCP_KEEPIDLE
                        2: 1,  # TCP_KEEPINTVL
                        3: 5,  # TCP_KEEPCNT
                    }
                )
            else:
                # Standard Redis connection
                self.async_redis = await aioredis.create_redis_pool(
                    f'redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}',
                    minsize=5,
                    maxsize=20,
                    encoding='utf-8'
                )
                
                self.redis_pool = redis.ConnectionPool(
                    host=settings.REDIS_HOST,
                    port=settings.REDIS_PORT,
                    db=settings.REDIS_DB,
                    max_connections=50,
                    socket_keepalive=True
                )
            
            logger.info("Redis cache connected successfully")
            
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    def _serialize(self, value: Any) -> bytes:
        """Serialize and optionally compress value"""
        # Use msgpack for efficient serialization
        serialized = msgpack.packb(value, use_bin_type=True)
        
        # Compress if above threshold
        if len(serialized) > self.compression_threshold:
            compressed = lz4.frame.compress(serialized)
            self.stats['compressions'] += 1
            return b'LZ4:' + compressed
        
        return serialized
    
    def _deserialize(self, data: bytes) -> Any:
        """Deserialize and optionally decompress value"""
        if data.startswith(b'LZ4:'):
            decompressed = lz4.frame.decompress(data[4:])
            self.stats['decompressions'] += 1
            return msgpack.unpackb(decompressed, raw=False)
        
        return msgpack.unpackb(data, raw=False)
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from Redis"""
        try:
            if self.async_redis:
                data = await self.async_redis.get(key)
            else:
                with redis.Redis(connection_pool=self.redis_pool) as r:
                    data = r.get(key)
            
            if data:
                self.stats['hits'] += 1
                return self._deserialize(data)
            
            self.stats['misses'] += 1
            return None
            
        except Exception as e:
            logger.warning(f"Redis get failed for key {key}: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set value in Redis"""
        try:
            ttl = ttl or self.default_ttl
            data = self._serialize(value)
            
            if self.async_redis:
                await self.async_redis.setex(key, ttl, data)
            else:
                with redis.Redis(connection_pool=self.redis_pool) as r:
                    r.setex(key, ttl, data)
                    
        except Exception as e:
            logger.warning(f"Redis set failed for key {key}: {e}")
    
    async def delete(self, keys: Union[str, List[str]]):
        """Delete keys from Redis"""
        try:
            if isinstance(keys, str):
                keys = [keys]
            
            if self.async_redis:
                await self.async_redis.delete(*keys)
            else:
                with redis.Redis(connection_pool=self.redis_pool) as r:
                    r.delete(*keys)
                    
        except Exception as e:
            logger.warning(f"Redis delete failed: {e}")
    
    async def invalidate_pattern(self, pattern: str):
        """Invalidate all keys matching pattern"""
        try:
            if self.async_redis:
                cursor = '0'
                while cursor != 0:
                    cursor, keys = await self.async_redis.scan(
                        cursor, match=pattern, count=100
                    )
                    if keys:
                        await self.async_redis.delete(*keys)
            else:
                with redis.Redis(connection_pool=self.redis_pool) as r:
                    for key in r.scan_iter(match=pattern, count=100):
                        r.delete(key)
                        
        except Exception as e:
            logger.warning(f"Redis pattern invalidation failed: {e}")


class CDNCache:
    """
    CDN and edge caching integration
    """
    
    def __init__(self):
        self.cdn_endpoints = getattr(settings, 'CDN_ENDPOINTS', [])
        self.edge_locations = getattr(settings, 'EDGE_LOCATIONS', [])
        
    async def push_to_cdn(self, key: str, value: Any, content_type: str = 'application/json'):
        """Push content to CDN edge locations"""
        # This would integrate with actual CDN API (CloudFlare, Fastly, etc.)
        pass
    
    async def invalidate_cdn(self, pattern: str):
        """Invalidate CDN cache"""
        # This would call CDN purge API
        pass
    
    asyncবয় warm_cdn_cache(self, popular_keys: List[str]):
        """Pre-warm CDN cache with popular content"""
        # This would push frequently accessed content to edge locations
        pass


class CacheStrategy:
    """
    Comprehensive multi-layer caching strategy with intelligent routing
    """
    
    def __init__(self):
        # Initialize cache layers
        self.l1_cache = LRUCache(max_size=10000, max_memory_mb=512)
        self.l2_cache = RedisCache()
        self.l3_cache = CDNCache()
        
        # Cache configuration
        self.ttl_config = {
            # Real-time data (short TTL)
            'quote': 1,
            'market_data': 5,
            'portfolio_value': 10,
            
            # User data (medium TTL)
            'user_profile': 300,
            'portfolio_holdings': 60,
            'transactions': 120,
            
            # Static data (long TTL)
            'security_info': 3600,
            'historical_data': 1800,
            'analytics': 600,
            
            # Computed results
            'monte_carlo': 1800,
            'optimization': 900,
            'recommendations': 600
        }
        
        # Cache routing rules
        self.routing_rules = {
            'hot_data': [CacheLevel.L1_MEMORY, CacheLevel.L2_REDIS],
            'warm_data': [CacheLevel.L2_REDIS],
            'cold_data': [CacheLevel.L3_CDN],
            'static_assets': [CacheLevel.L1_MEMORY, CacheLevel.L3_CDN]
        }
        
        # Statistics
        self.request_count = 0
        self.cache_hits = {'L1': 0, 'L2': 0, 'L3': 0}
        self.cache_misses = 0
    
    async def initialize(self):
        """Initialize all cache layers"""
        await self.l2_cache.connect()
        logger.info("Cache strategy initialized")
    
    def get_cache_key(self, prefix: str, params: Dict = None) -> str:
        """Generate consistent cache key"""
        if params:
            # Sort params for consistent key generation
            sorted_params = sorted(params.items())
            param_str = '_'.join([f"{k}:{v}" for k, v in sorted_params])
            return f"{prefix}:{param_str}"
        return prefix
    
    def get_ttl(self, data_type: str) -> int:
        """Get TTL for data type"""
        return self.ttl_config.get(data_type, 300)
    
    async def get(
        self,
        key: str,
        compute_func: Optional[Callable] = None,
        data_type: str = 'default',
        cache_levels: Optional[List[CacheLevel]] = None
    ) -> Optional[Any]:
        """
        Get value from cache hierarchy with automatic fallback
        """
        self.request_count += 1
        
        # Determine cache levels to check
        if not cache_levels:
            cache_levels = self._determine_cache_levels(data_type)
        
        # Check L1 (Memory)
        if CacheLevel.L1_MEMORY in cache_levels:
            value = await self.l1_cache.get(key)
            if value is not None:
                self.cache_hits['L1'] += 1
                return value
        
        # Check L2 (Redis)
        if CacheLevel.L2_REDIS in cache_levels:
            value = await self.l2_cache.get(key)
            if value is not None:
                self.cache_hits['L2'] += 1
                
                # Promote to L1 if hot data
                if CacheLevel.L1_MEMORY in cache_levels:
                    await self.l1_cache.set(key, value, self.get_ttl(data_type))
                
                return value
        
        # Check L3 (CDN) - typically for static content
        if CacheLevel.L3_CDN in cache_levels:
            # CDN lookup would go here
            pass
        
        # Cache miss - compute if function provided
        if compute_func:
            self.cache_misses += 1
            value = await compute_func()
            
            # Store in appropriate cache levels
            await self.set(key, value, data_type, cache_levels)
            
            return value
        
        self.cache_misses += 1
        return None
    
    async def set(
        self,
        key: str,
        value: Any,
        data_type: str = 'default',
        cache_levels: Optional[List[CacheLevel]] = None
    ):
        """
        Set value in cache hierarchy
        """
        ttl = self.get_ttl(data_type)
        
        # Determine cache levels to populate
        if not cache_levels:
            cache_levels = self._determine_cache_levels(data_type)
        
        # Store in cache levels
        tasks = []
        
        if CacheLevel.L1_MEMORY in cache_levels:
            tasks.append(self.l1_cache.set(key, value, ttl))
        
        if CacheLevel.L2_REDIS in cache_levels:
            tasks.append(self.l2_cache.set(key, value, ttl))
        
        if CacheLevel.L3_CDN in cache_levels:
            tasks.append(self.l3_cache.push_to_cdn(key, value))
        
        await asyncio.gather(*tasks)
    
    async def invalidate(
        self,
        pattern: str,
        cache_levels: Optional[List[CacheLevel]] = None
    ):
        """
        Invalidate cache entries matching pattern
        """
        if not cache_levels:
            cache_levels = [CacheLevel.L1_MEMORY, CacheLevel.L2_REDIS, CacheLevel.L3_CDN]
        
        tasks = []
        
        if CacheLevel.L1_MEMORY in cache_levels:
            tasks.append(self.l1_cache.invalidate(pattern))
        
        if CacheLevel.L2_REDIS in cache_levels:
            tasks.append(self.l2_cache.invalidate_pattern(f"{pattern}*"))
        
        if CacheLevel.L3_CDN in cache_levels:
            tasks.append(self.l3_cache.invalidate_cdn(pattern))
        
        await asyncio.gather(*tasks)
    
    def _determine_cache_levels(self, data_type: str) -> List[CacheLevel]:
        """
        Determine appropriate cache levels based on data type
        """
        # Hot data: frequently accessed, small TTL
        if data_type in ['quote', 'market_data', 'portfolio_value']:
            return [CacheLevel.L1_MEMORY, CacheLevel.L2_REDIS]
        
        # Warm data: moderate access, medium TTL
        elif data_type in ['user_profile', 'portfolio_holdings', 'transactions']:
            return [CacheLevel.L2_REDIS]
        
        # Cold data: infrequent access, long TTL
        elif data_type in ['historical_data', 'security_info']:
            return [CacheLevel.L2_REDIS, CacheLevel.L3_CDN]
        
        # Computed results: expensive to generate
        elif data_type in ['monte_carlo', 'optimization', 'recommendations']:
            return [CacheLevel.L1_MEMORY, CacheLevel.L2_REDIS]
        
        # Default
        return [CacheLevel.L2_REDIS]
    
    def cache_decorator(
        self,
        data_type: str = 'default',
        ttl: Optional[int] = None,
        key_prefix: Optional[str] = None
    ):
        """
        Decorator for automatic caching of function results
        """
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Generate cache key
                if key_prefix:
                    cache_key = self.get_cache_key(key_prefix, kwargs)
                else:
                    cache_key = self.get_cache_key(func.__name__, kwargs)
                
                # Try to get from cache
                result = await self.get(cache_key, data_type=data_type)
                
                if result is not None:
                    return result
                
                # Compute and cache
                result = await func(*args, **kwargs)
                await self.set(cache_key, result, data_type)
                
                return result
            
            return wrapper
        return decorator
    
    async def preload_cache(self, preload_keys: Dict[str, Callable]):
        """
        Preload cache with essential data
        """
        tasks = []
        for key, compute_func in preload_keys.items():
            tasks.append(self.get(key, compute_func=compute_func))
        
        await asyncio.gather(*tasks)
        logger.info(f"Preloaded {len(preload_keys)} cache entries")
    
    def get_stats(self) -> Dict:
        """
        Get comprehensive cache statistics
        """
        total_hits = sum(self.cache_hits.values())
        hit_rate = total_hits / self.request_count if self.request_count > 0 else 0
        
        return {
            'request_count': self.request_count,
            'total_hits': total_hits,
            'total_misses': self.cache_misses,
            'hit_rate': hit_rate,
            'layer_hits': self.cache_hits,
            'l1_stats': self.l1_cache.get_stats(),
            'l2_stats': self.l2_cache.stats,
            'recommendations': self._generate_cache_recommendations()
        }
    
    def _generate_cache_recommendations(self) -> List[str]:
        """
        Generate cache optimization recommendations
        """
        recommendations = []
        
        # Check hit rates
        if self.request_count > 1000:
            hit_rate = sum(self.cache_hits.values()) / self.request_count
            
            if hit_rate < 0.7:
                recommendations.append("Low cache hit rate - consider increasing TTLs")
            
            if self.cache_hits['L1'] < self.cache_hits['L2']:
                recommendations.append("Consider promoting hot data to L1 cache")
        
        # Check memory usage
        l1_stats = self.l1_cache.get_stats()
        if l1_stats['evictions'] > 1000:
            recommendations.append("High L1 eviction rate - consider increasing memory limit")
        
        return recommendations


# Singleton instance
cache_strategy = CacheStrategy()