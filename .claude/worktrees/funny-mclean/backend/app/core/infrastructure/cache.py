"""
Advanced Redis Caching Layer with Multiple Strategies

Provides:
- Multi-tier caching (L1 memory, L2 Redis)
- Cache warming and preloading
- Distributed cache invalidation
- Cache analytics and monitoring
- Pattern-based cache keys
- Compression for large values
- Serialization with multiple formats
"""

import asyncio
import gzip
import hashlib
import json
import logging
import pickle
import time
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Type, Union

import aioredis
from aioredis import Redis

from app.core.config import settings

logger = logging.getLogger(__name__)


class CacheStrategy(Enum):
    """Cache strategies for different use cases"""
    WRITE_THROUGH = "write_through"      # Write to cache and DB simultaneously
    WRITE_BEHIND = "write_behind"        # Write to cache first, DB later
    WRITE_AROUND = "write_around"        # Write only to DB, invalidate cache
    READ_THROUGH = "read_through"        # Read from cache, fallback to DB
    REFRESH_AHEAD = "refresh_ahead"      # Proactively refresh before expiration


class SerializationFormat(Enum):
    """Serialization formats for cached data"""
    JSON = "json"
    PICKLE = "pickle"
    MSGPACK = "msgpack"
    STRING = "string"


@dataclass
class CacheConfig:
    """Cache configuration per key pattern"""
    ttl_seconds: int = 3600
    strategy: CacheStrategy = CacheStrategy.READ_THROUGH
    serialization: SerializationFormat = SerializationFormat.JSON
    compress: bool = False
    compression_threshold: int = 1024  # Compress if data > 1KB
    max_size_bytes: int = 10 * 1024 * 1024  # 10MB max per key
    refresh_threshold: float = 0.8  # Refresh when 80% of TTL elapsed


@dataclass
class CacheStats:
    """Cache statistics for monitoring"""
    hits: int = 0
    misses: int = 0
    sets: int = 0
    deletes: int = 0
    evictions: int = 0
    errors: int = 0
    total_requests: int = 0
    average_response_time_ms: float = 0.0
    memory_usage_bytes: int = 0
    
    @property
    def hit_ratio(self) -> float:
        """Calculate cache hit ratio"""
        if self.total_requests == 0:
            return 0.0
        return self.hits / self.total_requests
    
    @property 
    def miss_ratio(self) -> float:
        """Calculate cache miss ratio"""
        return 1.0 - self.hit_ratio


class CacheKeyBuilder:
    """Utility for building consistent cache keys"""
    
    def __init__(self, prefix: str = "financial_app"):
        self.prefix = prefix
    
    def build_key(self, *parts: Union[str, int, float], namespace: str = None) -> str:
        """Build cache key from parts"""
        key_parts = [self.prefix]
        
        if namespace:
            key_parts.append(namespace)
        
        # Convert all parts to strings and filter out None values
        string_parts = [str(part) for part in parts if part is not None]
        key_parts.extend(string_parts)
        
        return ":".join(key_parts)
    
    def build_pattern(self, pattern: str, namespace: str = None) -> str:
        """Build cache key pattern for bulk operations"""
        if namespace:
            return f"{self.prefix}:{namespace}:{pattern}"
        return f"{self.prefix}:{pattern}"
    
    def hash_key(self, data: Union[str, Dict, List]) -> str:
        """Create hash-based key for complex data"""
        if isinstance(data, (dict, list)):
            data_str = json.dumps(data, sort_keys=True)
        else:
            data_str = str(data)
        
        return hashlib.sha256(data_str.encode()).hexdigest()[:16]


class CacheSerializer:
    """Handles serialization/deserialization with multiple formats"""
    
    @staticmethod
    def serialize(data: Any, format: SerializationFormat, compress: bool = False) -> bytes:
        """Serialize data to bytes"""
        if format == SerializationFormat.JSON:
            serialized = json.dumps(data, default=str).encode('utf-8')
        elif format == SerializationFormat.PICKLE:
            serialized = pickle.dumps(data)
        elif format == SerializationFormat.STRING:
            serialized = str(data).encode('utf-8')
        else:
            raise ValueError(f"Unsupported serialization format: {format}")
        
        if compress:
            serialized = gzip.compress(serialized)
        
        return serialized
    
    @staticmethod
    def deserialize(data: bytes, format: SerializationFormat, compressed: bool = False) -> Any:
        """Deserialize bytes to data"""
        if compressed:
            data = gzip.decompress(data)
        
        if format == SerializationFormat.JSON:
            return json.loads(data.decode('utf-8'))
        elif format == SerializationFormat.PICKLE:
            return pickle.loads(data)
        elif format == SerializationFormat.STRING:
            return data.decode('utf-8')
        else:
            raise ValueError(f"Unsupported serialization format: {format}")


class BaseCache(ABC):
    """Abstract base cache interface"""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        pass
    
    @abstractmethod
    async def set(
        self,
        key: str,
        value: Any,
        expire: Optional[int] = None
    ) -> bool:
        """Set value in cache"""
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        pass
    
    @abstractmethod
    async def clear(self) -> bool:
        """Clear all cache entries"""
        pass


class MemoryCache(BaseCache):
    """In-memory L1 cache for frequently accessed data"""
    
    def __init__(self, max_size: int = 1000, ttl_seconds: int = 300):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._access_order: List[str] = []  # For LRU eviction
        
    async def get(self, key: str) -> Optional[Any]:
        """Get value from memory cache"""
        if key not in self._cache:
            return None
        
        entry = self._cache[key]
        
        # Check expiration
        if time.time() > entry['expires_at']:
            await self.delete(key)
            return None
        
        # Update access order for LRU
        self._access_order.remove(key)
        self._access_order.append(key)
        
        return entry['value']
    
    async def set(
        self,
        key: str,
        value: Any,
        expire: Optional[int] = None
    ) -> bool:
        """Set value in memory cache"""
        try:
            # Evict if at capacity
            if len(self._cache) >= self.max_size and key not in self._cache:
                await self._evict_lru()
            
            expires_at = time.time() + (expire or self.ttl_seconds)
            
            self._cache[key] = {
                'value': value,
                'created_at': time.time(),
                'expires_at': expires_at
            }
            
            # Update access order
            if key in self._access_order:
                self._access_order.remove(key)
            self._access_order.append(key)
            
            return True
            
        except Exception as e:
            logger.error(f"Error setting memory cache key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from memory cache"""
        if key in self._cache:
            del self._cache[key]
            if key in self._access_order:
                self._access_order.remove(key)
            return True
        return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in memory cache"""
        if key not in self._cache:
            return False
        
        entry = self._cache[key]
        if time.time() > entry['expires_at']:
            await self.delete(key)
            return False
        
        return True
    
    async def clear(self) -> bool:
        """Clear all memory cache entries"""
        self._cache.clear()
        self._access_order.clear()
        return True
    
    async def _evict_lru(self) -> None:
        """Evict least recently used entry"""
        if self._access_order:
            lru_key = self._access_order[0]
            await self.delete(lru_key)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get memory cache statistics"""
        current_time = time.time()
        expired_count = sum(
            1 for entry in self._cache.values()
            if current_time > entry['expires_at']
        )
        
        return {
            'size': len(self._cache),
            'max_size': self.max_size,
            'expired_entries': expired_count,
            'utilization_percent': (len(self._cache) / self.max_size) * 100
        }


class RedisCache(BaseCache):
    """Redis-based L2 distributed cache"""
    
    def __init__(
        self,
        redis_url: str = None,
        key_builder: CacheKeyBuilder = None,
        serializer: CacheSerializer = None
    ):
        self.redis_url = redis_url or settings.REDIS_URL
        self.redis: Optional[Redis] = None
        self.key_builder = key_builder or CacheKeyBuilder()
        self.serializer = serializer or CacheSerializer()
        self.is_connected = False
        
        # Cache configurations by pattern
        self.configs: Dict[str, CacheConfig] = {
            "default": CacheConfig(),
            "user:*": CacheConfig(ttl_seconds=1800),  # 30 minutes
            "plan:*": CacheConfig(ttl_seconds=3600),  # 1 hour
            "market_data:*": CacheConfig(ttl_seconds=300, compress=True),  # 5 minutes
            "simulation:*": CacheConfig(ttl_seconds=7200, compress=True, serialization=SerializationFormat.PICKLE)  # 2 hours
        }
        
        self.stats = CacheStats()
    
    async def connect(self) -> None:
        """Connect to Redis"""
        try:
            self.redis = aioredis.from_url(
                self.redis_url,
                decode_responses=False,  # Keep as bytes for serialization
                retry_on_timeout=True,
                socket_keepalive=True,
                socket_keepalive_options={}
            )
            
            # Test connection
            await self.redis.ping()
            self.is_connected = True
            
            logger.info("Connected to Redis cache")
            
        except Exception as e:
            logger.error(f"Failed to connect to Redis cache: {e}")
            raise
    
    async def disconnect(self) -> None:
        """Disconnect from Redis"""
        if self.redis:
            await self.redis.close()
            self.is_connected = False
            logger.info("Disconnected from Redis cache")
    
    def _get_config(self, key: str) -> CacheConfig:
        """Get configuration for cache key"""
        for pattern, config in self.configs.items():
            if pattern == "default":
                continue
            
            # Simple pattern matching (could be enhanced with regex)
            if "*" in pattern:
                prefix = pattern.replace("*", "")
                if key.startswith(prefix):
                    return config
        
        return self.configs["default"]
    
    async def get(self, key: str, config: CacheConfig = None) -> Optional[Any]:
        """Get value from Redis cache"""
        if not self.is_connected:
            await self.connect()
        
        config = config or self._get_config(key)
        start_time = time.time()
        
        try:
            data = await self.redis.get(key)
            
            if data is None:
                self.stats.misses += 1
                self.stats.total_requests += 1
                return None
            
            # Deserialize data
            value = self.serializer.deserialize(
                data,
                config.serialization,
                config.compress
            )
            
            self.stats.hits += 1
            self.stats.total_requests += 1
            
            # Update average response time
            response_time = (time.time() - start_time) * 1000
            self.stats.average_response_time_ms = (
                (self.stats.average_response_time_ms * (self.stats.total_requests - 1) + response_time)
                / self.stats.total_requests
            )
            
            return value
            
        except Exception as e:
            self.stats.errors += 1
            self.stats.total_requests += 1
            logger.error(f"Error getting cache key {key}: {e}")
            return None
    
    async def set(
        self,
        key: str,
        value: Any,
        expire: Optional[int] = None,
        config: CacheConfig = None
    ) -> bool:
        """Set value in Redis cache"""
        if not self.is_connected:
            await self.connect()
        
        config = config or self._get_config(key)
        ttl = expire or config.ttl_seconds
        
        try:
            # Serialize data
            should_compress = config.compress
            if config.compression_threshold > 0:
                # Test serialization size to decide compression
                test_data = self.serializer.serialize(value, config.serialization, False)
                should_compress = len(test_data) > config.compression_threshold
            
            data = self.serializer.serialize(
                value,
                config.serialization,
                should_compress
            )
            
            # Check size limit
            if len(data) > config.max_size_bytes:
                logger.warning(f"Cache key {key} exceeds max size limit ({len(data)} bytes)")
                return False
            
            # Set in Redis with expiration
            await self.redis.setex(key, ttl, data)
            
            self.stats.sets += 1
            return True
            
        except Exception as e:
            self.stats.errors += 1
            logger.error(f"Error setting cache key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from Redis cache"""
        if not self.is_connected:
            await self.connect()
        
        try:
            result = await self.redis.delete(key)
            if result > 0:
                self.stats.deletes += 1
                return True
            return False
            
        except Exception as e:
            self.stats.errors += 1
            logger.error(f"Error deleting cache key {key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in Redis cache"""
        if not self.is_connected:
            await self.connect()
        
        try:
            result = await self.redis.exists(key)
            return result > 0
            
        except Exception as e:
            self.stats.errors += 1
            logger.error(f"Error checking cache key existence {key}: {e}")
            return False
    
    async def clear(self, pattern: str = None) -> bool:
        """Clear cache entries by pattern"""
        if not self.is_connected:
            await self.connect()
        
        try:
            if pattern:
                keys = await self.redis.keys(pattern)
                if keys:
                    deleted = await self.redis.delete(*keys)
                    self.stats.deletes += deleted
                    return True
            else:
                await self.redis.flushdb()
                return True
            
            return False
            
        except Exception as e:
            self.stats.errors += 1
            logger.error(f"Error clearing cache with pattern {pattern}: {e}")
            return False
    
    async def increment(self, key: str, amount: int = 1, expire: Optional[int] = None) -> Optional[int]:
        """Increment counter in cache"""
        if not self.is_connected:
            await self.connect()
        
        try:
            result = await self.redis.incrby(key, amount)
            
            if expire:
                await self.redis.expire(key, expire)
            
            return result
            
        except Exception as e:
            self.stats.errors += 1
            logger.error(f"Error incrementing cache key {key}: {e}")
            return None
    
    async def get_ttl(self, key: str) -> Optional[int]:
        """Get remaining TTL for key"""
        if not self.is_connected:
            await self.connect()
        
        try:
            ttl = await self.redis.ttl(key)
            return ttl if ttl > 0 else None
            
        except Exception as e:
            logger.error(f"Error getting TTL for key {key}: {e}")
            return None
    
    async def bulk_get(self, keys: List[str]) -> Dict[str, Any]:
        """Get multiple keys at once"""
        if not self.is_connected:
            await self.connect()
        
        try:
            if not keys:
                return {}
            
            values = await self.redis.mget(keys)
            result = {}
            
            for i, key in enumerate(keys):
                if values[i] is not None:
                    config = self._get_config(key)
                    try:
                        result[key] = self.serializer.deserialize(
                            values[i],
                            config.serialization,
                            config.compress
                        )
                        self.stats.hits += 1
                    except Exception as e:
                        logger.error(f"Error deserializing bulk key {key}: {e}")
                        self.stats.errors += 1
                else:
                    self.stats.misses += 1
            
            self.stats.total_requests += len(keys)
            return result
            
        except Exception as e:
            self.stats.errors += len(keys)
            self.stats.total_requests += len(keys)
            logger.error(f"Error in bulk get operation: {e}")
            return {}
    
    def get_stats(self) -> CacheStats:
        """Get cache statistics"""
        return self.stats
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform Redis health check"""
        try:
            if not self.is_connected:
                return {
                    'status': 'unhealthy',
                    'error': 'Not connected to Redis'
                }
            
            start_time = time.time()
            pong = await self.redis.ping()
            response_time = (time.time() - start_time) * 1000
            
            if pong:
                info = await self.redis.info()
                return {
                    'status': 'healthy',
                    'response_time_ms': response_time,
                    'memory_usage_mb': info.get('used_memory', 0) / 1024 / 1024,
                    'connected_clients': info.get('connected_clients', 0),
                    'stats': self.stats.__dict__
                }
            else:
                return {
                    'status': 'unhealthy',
                    'error': 'Redis ping failed'
                }
                
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e)
            }


class MultiTierCache:
    """Multi-tier cache with L1 (memory) and L2 (Redis) layers"""
    
    def __init__(
        self,
        l1_cache: MemoryCache = None,
        l2_cache: RedisCache = None,
        write_through: bool = True
    ):
        self.l1_cache = l1_cache or MemoryCache()
        self.l2_cache = l2_cache or RedisCache()
        self.write_through = write_through  # Write to both layers simultaneously
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from multi-tier cache"""
        # Try L1 cache first
        value = await self.l1_cache.get(key)
        if value is not None:
            return value
        
        # Try L2 cache
        value = await self.l2_cache.get(key)
        if value is not None:
            # Warm L1 cache
            await self.l1_cache.set(key, value)
            return value
        
        return None
    
    async def set(
        self,
        key: str,
        value: Any,
        expire: Optional[int] = None
    ) -> bool:
        """Set value in multi-tier cache"""
        if self.write_through:
            # Write to both layers
            l1_success = await self.l1_cache.set(key, value, expire)
            l2_success = await self.l2_cache.set(key, value, expire)
            return l1_success and l2_success
        else:
            # Write to L1 first, then L2
            l1_success = await self.l1_cache.set(key, value, expire)
            if l1_success:
                await self.l2_cache.set(key, value, expire)
            return l1_success
    
    async def delete(self, key: str) -> bool:
        """Delete from both cache layers"""
        l1_success = await self.l1_cache.delete(key)
        l2_success = await self.l2_cache.delete(key)
        return l1_success or l2_success
    
    async def clear(self, pattern: str = None) -> bool:
        """Clear both cache layers"""
        l1_success = await self.l1_cache.clear()
        l2_success = await self.l2_cache.clear(pattern)
        return l1_success and l2_success


class CacheManager:
    """High-level cache manager with decorators and utilities"""
    
    def __init__(self, cache: BaseCache = None):
        self.cache = cache or MultiTierCache()
        self.key_builder = CacheKeyBuilder()
    
    def cached(
        self,
        key_pattern: str = None,
        ttl_seconds: int = 3600,
        namespace: str = None,
        skip_cache: Callable = None
    ):
        """Decorator for caching function results"""
        def decorator(func: Callable):
            async def wrapper(*args, **kwargs):
                # Build cache key
                if key_pattern:
                    # Use provided pattern
                    key_parts = []
                    for i, arg in enumerate(args):
                        key_parts.append(f"arg{i}_{arg}")
                    for k, v in kwargs.items():
                        key_parts.append(f"{k}_{v}")
                    cache_key = self.key_builder.build_key(key_pattern, *key_parts, namespace=namespace)
                else:
                    # Generate key from function name and arguments
                    func_name = func.__name__
                    args_hash = self.key_builder.hash_key({"args": args, "kwargs": kwargs})
                    cache_key = self.key_builder.build_key(func_name, args_hash, namespace=namespace)
                
                # Check if we should skip cache
                if skip_cache and await skip_cache(*args, **kwargs):
                    return await func(*args, **kwargs)
                
                # Try to get from cache
                cached_result = await self.cache.get(cache_key)
                if cached_result is not None:
                    return cached_result
                
                # Execute function and cache result
                result = await func(*args, **kwargs)
                await self.cache.set(cache_key, result, ttl_seconds)
                
                return result
            
            return wrapper
        return decorator
    
    async def get_or_set(
        self,
        key: str,
        factory: Callable,
        ttl_seconds: int = 3600
    ) -> Any:
        """Get from cache or set using factory function"""
        value = await self.cache.get(key)
        if value is not None:
            return value
        
        # Generate value using factory
        if asyncio.iscoroutinefunction(factory):
            value = await factory()
        else:
            value = factory()
        
        # Cache the value
        await self.cache.set(key, value, ttl_seconds)
        return value
    
    async def invalidate_pattern(self, pattern: str, namespace: str = None) -> bool:
        """Invalidate cache keys matching pattern"""
        full_pattern = self.key_builder.build_pattern(pattern, namespace)
        
        if hasattr(self.cache, 'clear'):
            return await self.cache.clear(full_pattern)
        
        return False


# Global cache instances
memory_cache = MemoryCache()
redis_cache = RedisCache()
multi_tier_cache = MultiTierCache(memory_cache, redis_cache)
cache_manager = CacheManager(multi_tier_cache)


@asynccontextmanager
async def cache_context():
    """Context manager for cache connections"""
    try:
        await redis_cache.connect()
        yield cache_manager
    finally:
        await redis_cache.disconnect()