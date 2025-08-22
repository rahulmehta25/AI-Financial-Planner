"""
Advanced Redis Caching Strategy with Multi-Layer Caching

Implements sophisticated caching patterns including:
- Multi-tier caching (L1: in-memory, L2: Redis, L3: database)
- Cache warming and preloading
- Intelligent cache invalidation
- TTL management with refresh strategies
- Cache stampede prevention
"""

import asyncio
import hashlib
import json
import pickle
import time
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union
from enum import Enum
import logging

import redis.asyncio as redis
from redis.asyncio import ConnectionPool
import msgpack
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class CacheLevel(Enum):
    """Cache levels for multi-tier caching"""
    L1_MEMORY = "memory"
    L2_REDIS = "redis"
    L3_DATABASE = "database"


class CacheTTL:
    """Predefined TTL values for different data types"""
    REALTIME = 5  # 5 seconds for real-time data
    SHORT = 60  # 1 minute for frequently changing data
    MEDIUM = 300  # 5 minutes for moderate data
    LONG = 3600  # 1 hour for stable data
    DAILY = 86400  # 1 day for daily reports
    WEEKLY = 604800  # 1 week for historical data
    
    # Dynamic TTL based on data volatility
    @staticmethod
    def calculate_dynamic_ttl(
        data_type: str,
        last_update: datetime,
        access_frequency: int
    ) -> int:
        """Calculate dynamic TTL based on data characteristics"""
        base_ttl = {
            'market_data': CacheTTL.SHORT,
            'portfolio': CacheTTL.MEDIUM,
            'simulation': CacheTTL.LONG,
            'user_profile': CacheTTL.DAILY,
            'historical': CacheTTL.WEEKLY
        }.get(data_type, CacheTTL.MEDIUM)
        
        # Adjust based on access frequency
        if access_frequency > 100:
            base_ttl = max(base_ttl // 2, CacheTTL.REALTIME)
        elif access_frequency < 10:
            base_ttl = min(base_ttl * 2, CacheTTL.WEEKLY)
        
        return base_ttl


class AdvancedRedisCache:
    """
    Advanced Redis cache implementation with sophisticated features
    """
    
    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        max_memory_cache_size: int = 1000,
        enable_compression: bool = True,
        enable_metrics: bool = True
    ):
        self.redis_url = redis_url
        self.redis_client: Optional[redis.Redis] = None
        self.connection_pool: Optional[ConnectionPool] = None
        
        # L1 in-memory cache
        self.memory_cache: Dict[str, Tuple[Any, float]] = {}
        self.memory_cache_order: List[str] = []
        self.max_memory_cache_size = max_memory_cache_size
        
        # Cache configuration
        self.enable_compression = enable_compression
        self.enable_metrics = enable_metrics
        
        # Metrics tracking
        self.metrics = {
            'hits': {'L1': 0, 'L2': 0},
            'misses': 0,
            'evictions': 0,
            'errors': 0
        }
        
        # Lock manager for preventing cache stampedes
        self.locks: Dict[str, asyncio.Lock] = {}
        
        # Invalidation tracking
        self.invalidation_patterns: Dict[str, Set[str]] = {}
    
    async def initialize(self):
        """Initialize Redis connection pool"""
        self.connection_pool = ConnectionPool.from_url(
            self.redis_url,
            max_connections=50,
            decode_responses=False
        )
        self.redis_client = redis.Redis(connection_pool=self.connection_pool)
        
        # Test connection
        await self.redis_client.ping()
        logger.info("Advanced Redis cache initialized successfully")
    
    async def close(self):
        """Close Redis connections"""
        if self.redis_client:
            await self.redis_client.close()
        if self.connection_pool:
            await self.connection_pool.disconnect()
    
    def _generate_cache_key(
        self,
        prefix: str,
        params: Dict[str, Any],
        version: str = "v1"
    ) -> str:
        """Generate a consistent cache key from parameters"""
        # Sort params for consistency
        sorted_params = json.dumps(params, sort_keys=True)
        param_hash = hashlib.md5(sorted_params.encode()).hexdigest()
        return f"{prefix}:{version}:{param_hash}"
    
    def _serialize(self, data: Any) -> bytes:
        """Serialize data for storage"""
        if self.enable_compression:
            return msgpack.packb(data, use_bin_type=True)
        return pickle.dumps(data)
    
    def _deserialize(self, data: bytes) -> Any:
        """Deserialize data from storage"""
        if self.enable_compression:
            return msgpack.unpackb(data, raw=False)
        return pickle.loads(data)
    
    async def get(
        self,
        key: str,
        default: Any = None,
        skip_l1: bool = False
    ) -> Optional[Any]:
        """
        Get value from cache with multi-tier lookup
        
        Args:
            key: Cache key
            default: Default value if not found
            skip_l1: Skip L1 memory cache
            
        Returns:
            Cached value or default
        """
        # L1: Check memory cache
        if not skip_l1 and key in self.memory_cache:
            value, expiry = self.memory_cache[key]
            if expiry > time.time():
                self.metrics['hits']['L1'] += 1
                # Move to end for LRU
                self.memory_cache_order.remove(key)
                self.memory_cache_order.append(key)
                return value
            else:
                # Expired, remove from memory
                del self.memory_cache[key]
                self.memory_cache_order.remove(key)
        
        # L2: Check Redis
        try:
            data = await self.redis_client.get(key)
            if data:
                value = self._deserialize(data)
                self.metrics['hits']['L2'] += 1
                
                # Populate L1 cache
                if not skip_l1:
                    ttl = await self.redis_client.ttl(key)
                    self._set_memory_cache(key, value, ttl)
                
                return value
        except Exception as e:
            logger.error(f"Redis get error: {e}")
            self.metrics['errors'] += 1
        
        self.metrics['misses'] += 1
        return default
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: int = CacheTTL.MEDIUM,
        skip_l1: bool = False,
        tags: List[str] = None
    ) -> bool:
        """
        Set value in cache with multi-tier storage
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
            skip_l1: Skip L1 memory cache
            tags: Tags for grouped invalidation
            
        Returns:
            Success status
        """
        # L1: Set in memory cache
        if not skip_l1:
            self._set_memory_cache(key, value, ttl)
        
        # L2: Set in Redis
        try:
            serialized = self._serialize(value)
            await self.redis_client.setex(key, ttl, serialized)
            
            # Track tags for invalidation
            if tags:
                for tag in tags:
                    await self.redis_client.sadd(f"tag:{tag}", key)
                    await self.redis_client.expire(f"tag:{tag}", ttl)
            
            return True
        except Exception as e:
            logger.error(f"Redis set error: {e}")
            self.metrics['errors'] += 1
            return False
    
    def _set_memory_cache(self, key: str, value: Any, ttl: int):
        """Set value in L1 memory cache with LRU eviction"""
        expiry = time.time() + ttl
        
        # Evict if at capacity
        if len(self.memory_cache) >= self.max_memory_cache_size:
            if self.memory_cache_order:
                oldest = self.memory_cache_order.pop(0)
                del self.memory_cache[oldest]
                self.metrics['evictions'] += 1
        
        self.memory_cache[key] = (value, expiry)
        if key in self.memory_cache_order:
            self.memory_cache_order.remove(key)
        self.memory_cache_order.append(key)
    
    async def delete(self, key: str) -> bool:
        """Delete from all cache tiers"""
        # L1: Remove from memory
        if key in self.memory_cache:
            del self.memory_cache[key]
            self.memory_cache_order.remove(key)
        
        # L2: Remove from Redis
        try:
            await self.redis_client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Redis delete error: {e}")
            return False
    
    async def invalidate_pattern(self, pattern: str):
        """Invalidate all keys matching a pattern"""
        # Clear from memory cache
        keys_to_delete = [k for k in self.memory_cache if pattern in k]
        for key in keys_to_delete:
            del self.memory_cache[key]
            self.memory_cache_order.remove(key)
        
        # Clear from Redis
        try:
            cursor = 0
            while True:
                cursor, keys = await self.redis_client.scan(
                    cursor, match=pattern, count=100
                )
                if keys:
                    await self.redis_client.delete(*keys)
                if cursor == 0:
                    break
        except Exception as e:
            logger.error(f"Pattern invalidation error: {e}")
    
    async def invalidate_tags(self, tags: List[str]):
        """Invalidate all keys associated with tags"""
        for tag in tags:
            try:
                keys = await self.redis_client.smembers(f"tag:{tag}")
                if keys:
                    # Clear from memory
                    for key in keys:
                        key_str = key.decode() if isinstance(key, bytes) else key
                        if key_str in self.memory_cache:
                            del self.memory_cache[key_str]
                            self.memory_cache_order.remove(key_str)
                    
                    # Clear from Redis
                    await self.redis_client.delete(*keys)
                    await self.redis_client.delete(f"tag:{tag}")
            except Exception as e:
                logger.error(f"Tag invalidation error: {e}")
    
    async def get_or_set(
        self,
        key: str,
        factory: Callable,
        ttl: int = CacheTTL.MEDIUM,
        lock_timeout: float = 10.0
    ) -> Any:
        """
        Get from cache or compute and set with lock to prevent stampedes
        
        Args:
            key: Cache key
            factory: Async function to compute value if not cached
            ttl: Time to live
            lock_timeout: Lock timeout for stampede prevention
            
        Returns:
            Cached or computed value
        """
        # Try to get from cache
        value = await self.get(key)
        if value is not None:
            return value
        
        # Acquire lock to prevent stampede
        if key not in self.locks:
            self.locks[key] = asyncio.Lock()
        
        try:
            async with asyncio.wait_for(
                self.locks[key].acquire(),
                timeout=lock_timeout
            ):
                # Double-check after acquiring lock
                value = await self.get(key)
                if value is not None:
                    return value
                
                # Compute value
                value = await factory() if asyncio.iscoroutinefunction(factory) else factory()
                
                # Cache the result
                await self.set(key, value, ttl)
                return value
        except asyncio.TimeoutError:
            logger.warning(f"Lock timeout for key: {key}")
            # Compute without caching to avoid blocking
            return await factory() if asyncio.iscoroutinefunction(factory) else factory()
        finally:
            if key in self.locks and self.locks[key].locked():
                self.locks[key].release()
    
    async def warm_cache(
        self,
        keys_factories: Dict[str, Tuple[Callable, int]]
    ):
        """
        Pre-warm cache with multiple keys
        
        Args:
            keys_factories: Dict of key -> (factory_function, ttl)
        """
        tasks = []
        for key, (factory, ttl) in keys_factories.items():
            tasks.append(self.get_or_set(key, factory, ttl))
        
        await asyncio.gather(*tasks, return_exceptions=True)
        logger.info(f"Cache warmed with {len(keys_factories)} keys")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get cache performance metrics"""
        total_hits = self.metrics['hits']['L1'] + self.metrics['hits']['L2']
        total_requests = total_hits + self.metrics['misses']
        hit_rate = (total_hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'l1_hits': self.metrics['hits']['L1'],
            'l2_hits': self.metrics['hits']['L2'],
            'misses': self.metrics['misses'],
            'hit_rate': f"{hit_rate:.2f}%",
            'evictions': self.metrics['evictions'],
            'errors': self.metrics['errors'],
            'memory_cache_size': len(self.memory_cache)
        }


def cache_decorator(
    ttl: int = CacheTTL.MEDIUM,
    key_prefix: str = None,
    tags: List[str] = None
):
    """
    Decorator for caching function results
    
    Args:
        ttl: Time to live in seconds
        key_prefix: Custom key prefix
        tags: Tags for grouped invalidation
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            prefix = key_prefix or f"{func.__module__}.{func.__name__}"
            cache_key = f"{prefix}:{str(args)}:{str(kwargs)}"
            
            # Get cache instance (assumes it's available in context)
            cache = kwargs.pop('_cache', None)
            if not cache:
                # Execute without caching if no cache available
                return await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
            
            # Try to get from cache
            result = await cache.get(cache_key)
            if result is not None:
                return result
            
            # Execute function
            result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
            
            # Cache result
            await cache.set(cache_key, result, ttl, tags=tags)
            
            return result
        
        return wrapper
    return decorator