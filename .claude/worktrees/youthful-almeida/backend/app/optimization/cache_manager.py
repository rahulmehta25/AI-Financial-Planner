"""
Multi-Level Cache Manager for High-Performance Financial Planning System

This module implements a sophisticated caching strategy with multiple tiers:
- L1: In-Memory Cache (microsecond latency)
- L2: Redis Cache (sub-millisecond latency)
- L3: Memcached (millisecond latency)

Features:
- Automatic cache invalidation and TTL management
- Cache warming and preloading
- Distributed cache synchronization
- Cache hit rate monitoring and optimization
"""

import asyncio
import hashlib
import json
import pickle
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

import aiomcache
import numpy as np
from prometheus_client import Counter, Histogram, Gauge
from pydantic import BaseModel
from redis import asyncio as aioredis
from redis.asyncio.lock import Lock as RedisLock


# Metrics
cache_hits = Counter('cache_hits_total', 'Total cache hits', ['cache_level', 'cache_key_type'])
cache_misses = Counter('cache_misses_total', 'Total cache misses', ['cache_level', 'cache_key_type'])
cache_latency = Histogram('cache_operation_latency_seconds', 'Cache operation latency', ['operation', 'cache_level'])
cache_size = Gauge('cache_size_bytes', 'Current cache size in bytes', ['cache_level'])
cache_evictions = Counter('cache_evictions_total', 'Total cache evictions', ['cache_level', 'reason'])


class CacheLevel(Enum):
    """Cache level enumeration"""
    L1_MEMORY = "memory"
    L2_REDIS = "redis"
    L3_MEMCACHED = "memcached"


class CacheStrategy(Enum):
    """Cache invalidation strategies"""
    TTL = "ttl"  # Time-to-live based
    LRU = "lru"  # Least recently used
    LFU = "lfu"  # Least frequently used
    FIFO = "fifo"  # First in, first out
    WRITE_THROUGH = "write_through"  # Write to all levels
    WRITE_BACK = "write_back"  # Write to L1, async to others


@dataclass
class CacheConfig:
    """Cache configuration"""
    # L1 Memory Cache
    memory_max_size: int = 1000  # Maximum number of items
    memory_max_bytes: int = 100 * 1024 * 1024  # 100MB
    memory_ttl: int = 300  # 5 minutes
    
    # L2 Redis
    redis_url: str = "redis://localhost:6379"
    redis_db: int = 0
    redis_ttl: int = 3600  # 1 hour
    redis_max_connections: int = 50
    
    # L3 Memcached
    memcached_hosts: List[str] = field(default_factory=lambda: ["localhost:11211"])
    memcached_ttl: int = 86400  # 24 hours
    memcached_max_pool_size: int = 10
    
    # General settings
    enable_compression: bool = True
    compression_threshold: int = 1024  # Compress if > 1KB
    enable_encryption: bool = False
    cache_key_prefix: str = "finplan"
    enable_metrics: bool = True
    enable_warming: bool = True
    warming_interval: int = 300  # 5 minutes


@dataclass
class CacheEntry:
    """Cache entry with metadata"""
    key: str
    value: Any
    size: int
    created_at: datetime
    accessed_at: datetime
    access_count: int = 0
    ttl: Optional[int] = None
    tags: Set[str] = field(default_factory=set)
    
    def is_expired(self) -> bool:
        """Check if entry is expired"""
        if self.ttl is None:
            return False
        return (datetime.utcnow() - self.created_at).seconds > self.ttl


class LRUCache:
    """Thread-safe LRU cache implementation"""
    
    def __init__(self, max_size: int, max_bytes: int):
        self.max_size = max_size
        self.max_bytes = max_bytes
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.current_bytes = 0
        self.lock = asyncio.Lock()
        
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        async with self.lock:
            if key not in self.cache:
                return None
                
            entry = self.cache[key]
            if entry.is_expired():
                del self.cache[key]
                self.current_bytes -= entry.size
                return None
                
            # Move to end (most recently used)
            self.cache.move_to_end(key)
            entry.accessed_at = datetime.utcnow()
            entry.access_count += 1
            
            return entry.value
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None, tags: Optional[Set[str]] = None) -> None:
        """Set value in cache"""
        async with self.lock:
            # Calculate size
            size = len(pickle.dumps(value))
            
            # Remove old entry if exists
            if key in self.cache:
                old_entry = self.cache[key]
                self.current_bytes -= old_entry.size
                
            # Evict if necessary
            while (len(self.cache) >= self.max_size or 
                   self.current_bytes + size > self.max_bytes) and self.cache:
                evicted_key, evicted_entry = self.cache.popitem(last=False)
                self.current_bytes -= evicted_entry.size
                cache_evictions.labels(cache_level=CacheLevel.L1_MEMORY.value, reason='size').inc()
            
            # Add new entry
            entry = CacheEntry(
                key=key,
                value=value,
                size=size,
                created_at=datetime.utcnow(),
                accessed_at=datetime.utcnow(),
                ttl=ttl,
                tags=tags or set()
            )
            
            self.cache[key] = entry
            self.current_bytes += size
            
    async def delete(self, key: str) -> None:
        """Delete key from cache"""
        async with self.lock:
            if key in self.cache:
                entry = self.cache[key]
                self.current_bytes -= entry.size
                del self.cache[key]
                
    async def clear(self) -> None:
        """Clear all cache entries"""
        async with self.lock:
            self.cache.clear()
            self.current_bytes = 0
            
    async def invalidate_by_tags(self, tags: Set[str]) -> None:
        """Invalidate entries with specific tags"""
        async with self.lock:
            keys_to_delete = []
            for key, entry in self.cache.items():
                if entry.tags & tags:
                    keys_to_delete.append(key)
                    
            for key in keys_to_delete:
                entry = self.cache[key]
                self.current_bytes -= entry.size
                del self.cache[key]


class MultiLevelCacheManager:
    """Multi-level cache manager with automatic tiering"""
    
    def __init__(self, config: Optional[CacheConfig] = None):
        self.config = config or CacheConfig()
        
        # L1: In-memory cache
        self.memory_cache = LRUCache(
            max_size=self.config.memory_max_size,
            max_bytes=self.config.memory_max_bytes
        )
        
        # L2: Redis cache (initialized in setup)
        self.redis_client: Optional[aioredis.Redis] = None
        
        # L3: Memcached (initialized in setup)
        self.memcached_client: Optional[aiomcache.Client] = None
        
        # Cache warming
        self.warming_tasks: List[asyncio.Task] = []
        self.warm_keys: Set[str] = set()
        
        # Statistics
        self.stats = {
            'hits': {'L1': 0, 'L2': 0, 'L3': 0},
            'misses': {'L1': 0, 'L2': 0, 'L3': 0},
            'latency': {'L1': [], 'L2': [], 'L3': []}
        }
        
    async def setup(self) -> None:
        """Initialize cache connections"""
        # Setup Redis
        self.redis_client = await aioredis.from_url(
            self.config.redis_url,
            db=self.config.redis_db,
            max_connections=self.config.redis_max_connections,
            decode_responses=False
        )
        
        # Setup Memcached
        self.memcached_client = aiomcache.Client(
            *self.config.memcached_hosts,
            pool_size=self.config.memcached_max_pool_size
        )
        
        # Start cache warming if enabled
        if self.config.enable_warming:
            warming_task = asyncio.create_task(self._cache_warming_loop())
            self.warming_tasks.append(warming_task)
            
    async def close(self) -> None:
        """Close cache connections"""
        # Cancel warming tasks
        for task in self.warming_tasks:
            task.cancel()
            
        # Close Redis
        if self.redis_client:
            await self.redis_client.close()
            
        # Close Memcached
        if self.memcached_client:
            await self.memcached_client.close()
            
    def _generate_key(self, key: str) -> str:
        """Generate prefixed cache key"""
        return f"{self.config.cache_key_prefix}:{key}"
        
    def _serialize(self, value: Any) -> bytes:
        """Serialize value for storage"""
        data = pickle.dumps(value)
        
        # Compress if enabled and above threshold
        if self.config.enable_compression and len(data) > self.config.compression_threshold:
            import zlib
            data = zlib.compress(data, level=6)
            
        return data
        
    def _deserialize(self, data: bytes) -> Any:
        """Deserialize value from storage"""
        # Decompress if needed
        if self.config.enable_compression:
            try:
                import zlib
                data = zlib.decompress(data)
            except:
                pass  # Not compressed
                
        return pickle.loads(data)
        
    async def get(self, key: str, cache_levels: Optional[List[CacheLevel]] = None) -> Optional[Any]:
        """
        Get value from cache, checking each level in order
        
        Args:
            key: Cache key
            cache_levels: Specific levels to check (default: all)
            
        Returns:
            Cached value or None if not found
        """
        full_key = self._generate_key(key)
        cache_levels = cache_levels or [CacheLevel.L1_MEMORY, CacheLevel.L2_REDIS, CacheLevel.L3_MEMCACHED]
        
        # Check L1: Memory
        if CacheLevel.L1_MEMORY in cache_levels:
            start_time = time.time()
            value = await self.memory_cache.get(full_key)
            latency = time.time() - start_time
            
            if value is not None:
                cache_hits.labels(cache_level='L1', cache_key_type=self._get_key_type(key)).inc()
                self.stats['hits']['L1'] += 1
                cache_latency.labels(operation='get', cache_level='L1').observe(latency)
                return value
            else:
                cache_misses.labels(cache_level='L1', cache_key_type=self._get_key_type(key)).inc()
                self.stats['misses']['L1'] += 1
                
        # Check L2: Redis
        if CacheLevel.L2_REDIS in cache_levels and self.redis_client:
            start_time = time.time()
            try:
                data = await self.redis_client.get(full_key)
                latency = time.time() - start_time
                
                if data:
                    value = self._deserialize(data)
                    cache_hits.labels(cache_level='L2', cache_key_type=self._get_key_type(key)).inc()
                    self.stats['hits']['L2'] += 1
                    cache_latency.labels(operation='get', cache_level='L2').observe(latency)
                    
                    # Promote to L1
                    await self.memory_cache.set(full_key, value, ttl=self.config.memory_ttl)
                    
                    return value
                else:
                    cache_misses.labels(cache_level='L2', cache_key_type=self._get_key_type(key)).inc()
                    self.stats['misses']['L2'] += 1
            except Exception as e:
                print(f"Redis get error: {e}")
                
        # Check L3: Memcached
        if CacheLevel.L3_MEMCACHED in cache_levels and self.memcached_client:
            start_time = time.time()
            try:
                data = await self.memcached_client.get(full_key.encode())
                latency = time.time() - start_time
                
                if data:
                    value = self._deserialize(data)
                    cache_hits.labels(cache_level='L3', cache_key_type=self._get_key_type(key)).inc()
                    self.stats['hits']['L3'] += 1
                    cache_latency.labels(operation='get', cache_level='L3').observe(latency)
                    
                    # Promote to L1 and L2
                    await self.memory_cache.set(full_key, value, ttl=self.config.memory_ttl)
                    if self.redis_client:
                        await self.redis_client.setex(
                            full_key,
                            self.config.redis_ttl,
                            self._serialize(value)
                        )
                    
                    return value
                else:
                    cache_misses.labels(cache_level='L3', cache_key_type=self._get_key_type(key)).inc()
                    self.stats['misses']['L3'] += 1
            except Exception as e:
                print(f"Memcached get error: {e}")
                
        return None
        
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        strategy: CacheStrategy = CacheStrategy.WRITE_THROUGH,
        tags: Optional[Set[str]] = None
    ) -> None:
        """
        Set value in cache
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds
            strategy: Cache write strategy
            tags: Tags for cache invalidation
        """
        full_key = self._generate_key(key)
        
        # Write to L1
        await self.memory_cache.set(
            full_key,
            value,
            ttl=ttl or self.config.memory_ttl,
            tags=tags
        )
        
        if strategy == CacheStrategy.WRITE_THROUGH:
            # Write to all levels immediately
            tasks = []
            
            # Write to L2: Redis
            if self.redis_client:
                tasks.append(
                    self.redis_client.setex(
                        full_key,
                        ttl or self.config.redis_ttl,
                        self._serialize(value)
                    )
                )
                
            # Write to L3: Memcached
            if self.memcached_client:
                tasks.append(
                    self.memcached_client.set(
                        full_key.encode(),
                        self._serialize(value),
                        exptime=ttl or self.config.memcached_ttl
                    )
                )
                
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
                
        elif strategy == CacheStrategy.WRITE_BACK:
            # Write to L1 now, others asynchronously
            asyncio.create_task(self._async_write_back(full_key, value, ttl))
            
    async def _async_write_back(self, key: str, value: Any, ttl: Optional[int]) -> None:
        """Asynchronously write to L2 and L3"""
        tasks = []
        
        # Write to L2: Redis
        if self.redis_client:
            tasks.append(
                self.redis_client.setex(
                    key,
                    ttl or self.config.redis_ttl,
                    self._serialize(value)
                )
            )
            
        # Write to L3: Memcached
        if self.memcached_client:
            tasks.append(
                self.memcached_client.set(
                    key.encode(),
                    self._serialize(value),
                    exptime=ttl or self.config.memcached_ttl
                )
            )
            
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
            
    async def delete(self, key: str) -> None:
        """Delete key from all cache levels"""
        full_key = self._generate_key(key)
        
        tasks = [
            self.memory_cache.delete(full_key)
        ]
        
        if self.redis_client:
            tasks.append(self.redis_client.delete(full_key))
            
        if self.memcached_client:
            tasks.append(self.memcached_client.delete(full_key.encode()))
            
        await asyncio.gather(*tasks, return_exceptions=True)
        
    async def invalidate_pattern(self, pattern: str) -> None:
        """Invalidate all keys matching pattern"""
        # Clear from Redis (supports patterns)
        if self.redis_client:
            cursor = 0
            while True:
                cursor, keys = await self.redis_client.scan(
                    cursor,
                    match=f"{self.config.cache_key_prefix}:{pattern}"
                )
                if keys:
                    await self.redis_client.delete(*keys)
                if cursor == 0:
                    break
                    
        # Clear from memory (simple implementation)
        await self.memory_cache.clear()  # Can't do pattern matching efficiently
        
    async def invalidate_by_tags(self, tags: Set[str]) -> None:
        """Invalidate all entries with specific tags"""
        await self.memory_cache.invalidate_by_tags(tags)
        
        # For Redis and Memcached, we'd need to maintain a tag index
        # This is a simplified implementation
        if tags:
            for tag in tags:
                await self.invalidate_pattern(f"*:tag:{tag}:*")
                
    async def warm_cache(self, keys: List[Tuple[str, Callable]]) -> None:
        """
        Warm cache with specific keys
        
        Args:
            keys: List of (key, value_generator) tuples
        """
        for key, generator in keys:
            value = await generator() if asyncio.iscoroutinefunction(generator) else generator()
            await self.set(key, value, strategy=CacheStrategy.WRITE_THROUGH)
            self.warm_keys.add(key)
            
    async def _cache_warming_loop(self) -> None:
        """Background task for cache warming"""
        while True:
            try:
                await asyncio.sleep(self.config.warming_interval)
                
                # Re-warm keys that are frequently accessed
                for key in list(self.warm_keys):
                    value = await self.get(key)
                    if value is None:
                        self.warm_keys.remove(key)
                        
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Cache warming error: {e}")
                
    def _get_key_type(self, key: str) -> str:
        """Extract key type for metrics"""
        parts = key.split(':')
        return parts[0] if parts else 'unknown'
        
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_hits = sum(self.stats['hits'].values())
        total_misses = sum(self.stats['misses'].values())
        hit_rate = total_hits / (total_hits + total_misses) if (total_hits + total_misses) > 0 else 0
        
        return {
            'hit_rate': hit_rate,
            'hits': self.stats['hits'],
            'misses': self.stats['misses'],
            'memory_size_bytes': self.memory_cache.current_bytes,
            'memory_items': len(self.memory_cache.cache),
            'warm_keys': len(self.warm_keys)
        }


def cached(
    ttl: Optional[int] = None,
    cache_levels: Optional[List[CacheLevel]] = None,
    key_generator: Optional[Callable] = None,
    tags: Optional[Set[str]] = None
):
    """
    Decorator for caching function results
    
    Args:
        ttl: Time-to-live in seconds
        cache_levels: Cache levels to use
        key_generator: Custom key generator function
        tags: Cache tags for invalidation
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            if key_generator:
                cache_key = key_generator(*args, **kwargs)
            else:
                # Default key generation
                key_parts = [func.__name__]
                key_parts.extend(str(arg) for arg in args)
                key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
                cache_key = ":".join(key_parts)
                
            # Get cache manager (assumes it's available in context)
            cache_manager = getattr(wrapper, '_cache_manager', None)
            if not cache_manager:
                # Fallback to executing without cache
                return await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
                
            # Try to get from cache
            value = await cache_manager.get(cache_key, cache_levels=cache_levels)
            if value is not None:
                return value
                
            # Execute function
            value = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
            
            # Store in cache
            await cache_manager.set(
                cache_key,
                value,
                ttl=ttl,
                tags=tags
            )
            
            return value
            
        return wrapper
    return decorator


# Specific cache decorators for different data types
def cache_portfolio(ttl: int = 300):
    """Cache portfolio data (5 minutes default)"""
    return cached(
        ttl=ttl,
        cache_levels=[CacheLevel.L1_MEMORY, CacheLevel.L2_REDIS],
        tags={'portfolio'}
    )


def cache_market_data(ttl: int = 60):
    """Cache market data (1 minute default)"""
    return cached(
        ttl=ttl,
        cache_levels=[CacheLevel.L1_MEMORY],
        tags={'market'}
    )


def cache_user_profile(ttl: int = 3600):
    """Cache user profile (1 hour default)"""
    return cached(
        ttl=ttl,
        cache_levels=[CacheLevel.L1_MEMORY, CacheLevel.L2_REDIS, CacheLevel.L3_MEMCACHED],
        tags={'user'}
    )


def cache_computation(ttl: int = 86400):
    """Cache expensive computations (24 hours default)"""
    return cached(
        ttl=ttl,
        cache_levels=[CacheLevel.L1_MEMORY, CacheLevel.L2_REDIS, CacheLevel.L3_MEMCACHED],
        tags={'computation'}
    )