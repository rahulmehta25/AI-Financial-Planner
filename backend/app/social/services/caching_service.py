"""
Caching and performance optimization service for social platform
"""

import json
import uuid
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from functools import wraps
from hashlib import md5

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

from sqlalchemy.orm import Session


class SocialCacheService:
    """
    Caching service for social platform with Redis backend
    Falls back to in-memory caching if Redis is not available
    """
    
    def __init__(self, redis_url: Optional[str] = None):
        self.redis_client = None
        self.memory_cache = {}  # Fallback in-memory cache
        self.cache_stats = {"hits": 0, "misses": 0, "errors": 0}
        
        if REDIS_AVAILABLE and redis_url:
            try:
                self.redis_client = redis.from_url(redis_url, decode_responses=True)
                self.redis_client.ping()  # Test connection
            except Exception as e:
                print(f"Redis connection failed, falling back to memory cache: {e}")
                self.redis_client = None
    
    def _get_cache_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate cache key from prefix and arguments"""
        key_data = f"{prefix}:{':'.join(str(arg) for arg in args)}"
        if kwargs:
            key_data += f":{':'.join(f'{k}={v}' for k, v in sorted(kwargs.items()))}"
        
        # Hash long keys to avoid Redis key length limits
        if len(key_data) > 200:
            key_hash = md5(key_data.encode()).hexdigest()
            return f"{prefix}:hash:{key_hash}"
        
        return key_data
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            if self.redis_client:
                value = self.redis_client.get(key)
                if value:
                    self.cache_stats["hits"] += 1
                    return json.loads(value)
                else:
                    self.cache_stats["misses"] += 1
                    return None
            else:
                # Memory cache fallback
                cache_entry = self.memory_cache.get(key)
                if cache_entry:
                    if cache_entry["expires"] and datetime.utcnow() > cache_entry["expires"]:
                        del self.memory_cache[key]
                        self.cache_stats["misses"] += 1
                        return None
                    self.cache_stats["hits"] += 1
                    return cache_entry["value"]
                else:
                    self.cache_stats["misses"] += 1
                    return None
                    
        except Exception as e:
            self.cache_stats["errors"] += 1
            return None
    
    def set(self, key: str, value: Any, ttl_seconds: int = 3600) -> bool:
        """Set value in cache with TTL"""
        try:
            if self.redis_client:
                serialized_value = json.dumps(value, default=str)
                return self.redis_client.setex(key, ttl_seconds, serialized_value)
            else:
                # Memory cache fallback
                expires = datetime.utcnow() + timedelta(seconds=ttl_seconds)
                self.memory_cache[key] = {
                    "value": value,
                    "expires": expires
                }
                
                # Simple memory cache cleanup (remove 10% of oldest entries if cache gets large)
                if len(self.memory_cache) > 1000:
                    oldest_keys = sorted(
                        self.memory_cache.keys(),
                        key=lambda k: self.memory_cache[k]["expires"]
                    )[:100]
                    for old_key in oldest_keys:
                        del self.memory_cache[old_key]
                
                return True
                
        except Exception as e:
            self.cache_stats["errors"] += 1
            return False
    
    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        try:
            if self.redis_client:
                return bool(self.redis_client.delete(key))
            else:
                return bool(self.memory_cache.pop(key, None))
        except Exception as e:
            self.cache_stats["errors"] += 1
            return False
    
    def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching pattern"""
        try:
            if self.redis_client:
                keys = self.redis_client.keys(pattern)
                if keys:
                    return self.redis_client.delete(*keys)
                return 0
            else:
                # Memory cache pattern matching (simplified)
                matching_keys = [k for k in self.memory_cache.keys() if pattern.replace("*", "") in k]
                for key in matching_keys:
                    del self.memory_cache[key]
                return len(matching_keys)
        except Exception as e:
            self.cache_stats["errors"] += 1
            return 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics"""
        total_requests = self.cache_stats["hits"] + self.cache_stats["misses"]
        hit_rate = (self.cache_stats["hits"] / total_requests * 100) if total_requests > 0 else 0
        
        stats = {
            "hits": self.cache_stats["hits"],
            "misses": self.cache_stats["misses"],
            "errors": self.cache_stats["errors"],
            "hit_rate": round(hit_rate, 2),
            "backend": "redis" if self.redis_client else "memory"
        }
        
        if not self.redis_client:
            stats["memory_cache_size"] = len(self.memory_cache)
        
        return stats


# Global cache instance
cache_service = SocialCacheService()


def cached(prefix: str, ttl_seconds: int = 3600, cache_on_user: bool = True):
    """
    Decorator for caching function results
    
    Args:
        prefix: Cache key prefix
        ttl_seconds: Time to live in seconds
        cache_on_user: Whether to include user_id in cache key
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Extract user_id if caching on user
            cache_key_parts = []
            if cache_on_user and len(args) > 0:
                # Assume first argument is user_id or has user_id attribute
                first_arg = args[0]
                if isinstance(first_arg, uuid.UUID):
                    cache_key_parts.append(str(first_arg))
                elif hasattr(first_arg, 'id'):
                    cache_key_parts.append(str(first_arg.id))
            
            # Create cache key
            cache_key = cache_service._get_cache_key(
                prefix, 
                *cache_key_parts,
                *args[1:] if cache_on_user else args,
                **kwargs
            )
            
            # Try to get from cache
            cached_result = cache_service.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache_service.set(cache_key, result, ttl_seconds)
            
            return result
        
        return wrapper
    return decorator


class PerformanceOptimizer:
    """Performance optimization utilities for social platform"""
    
    @staticmethod
    def optimize_query_for_pagination(query, page: int, per_page: int):
        """Optimize database queries for pagination"""
        offset = (page - 1) * per_page
        
        # Add limit/offset
        query = query.offset(offset).limit(per_page)
        
        return query
    
    @staticmethod
    def batch_load_related_data(db: Session, items: List[Any], 
                               relationship_attr: str, foreign_key: str):
        """Batch load related data to avoid N+1 queries"""
        if not items:
            return {}
        
        # Extract foreign keys
        foreign_keys = [getattr(item, foreign_key) for item in items if getattr(item, foreign_key)]
        if not foreign_keys:
            return {}
        
        # This would typically use SQLAlchemy's relationship loading
        # Implementation depends on specific models
        return {}
    
    @staticmethod
    def compress_response_data(data: Dict[str, Any], 
                             remove_null_values: bool = True,
                             compress_arrays: bool = True) -> Dict[str, Any]:
        """Compress response data by removing unnecessary fields"""
        
        def clean_dict(d):
            if not isinstance(d, dict):
                return d
            
            cleaned = {}
            for k, v in d.items():
                if remove_null_values and v is None:
                    continue
                
                if isinstance(v, dict):
                    cleaned[k] = clean_dict(v)
                elif isinstance(v, list) and compress_arrays:
                    # Compress arrays by removing null/empty elements
                    cleaned[k] = [clean_dict(item) for item in v if item is not None]
                else:
                    cleaned[k] = v
            
            return cleaned
        
        return clean_dict(data)


# Cache configuration for different data types
CACHE_CONFIGS = {
    "peer_comparison": {
        "ttl": 3600 * 24,  # 24 hours
        "prefix": "peer_comp"
    },
    "goal_inspiration": {
        "ttl": 3600 * 2,   # 2 hours  
        "prefix": "goal_insp"
    },
    "social_feed": {
        "ttl": 3600,       # 1 hour
        "prefix": "feed"
    },
    "demographic_insights": {
        "ttl": 3600 * 12,  # 12 hours
        "prefix": "demo_insights"
    },
    "community_stats": {
        "ttl": 3600 * 6,   # 6 hours
        "prefix": "comm_stats"
    },
    "user_profile": {
        "ttl": 3600 * 4,   # 4 hours
        "prefix": "user_profile"
    }
}


def get_cache_config(data_type: str) -> Dict[str, Any]:
    """Get cache configuration for specific data type"""
    return CACHE_CONFIGS.get(data_type, {"ttl": 3600, "prefix": "default"})


def invalidate_user_cache(user_id: uuid.UUID):
    """Invalidate all cache entries for a specific user"""
    patterns_to_clear = [
        f"peer_comp:*{user_id}*",
        f"goal_insp:*{user_id}*", 
        f"feed:*{user_id}*",
        f"user_profile:*{user_id}*"
    ]
    
    cleared_count = 0
    for pattern in patterns_to_clear:
        cleared_count += cache_service.clear_pattern(pattern)
    
    return cleared_count


def warm_cache_for_user(user_id: uuid.UUID, db: Session):
    """Pre-warm cache with commonly accessed data for a user"""
    # This would typically pre-load:
    # - User's peer comparison data
    # - Recent social feed items
    # - User's social profile
    # Implementation would depend on specific service methods
    pass


class CacheMetrics:
    """Track cache performance metrics"""
    
    @staticmethod
    def get_performance_report() -> Dict[str, Any]:
        """Get comprehensive cache performance report"""
        stats = cache_service.get_stats()
        
        return {
            "cache_performance": stats,
            "recommendations": CacheMetrics._get_recommendations(stats),
            "health_status": CacheMetrics._assess_health(stats)
        }
    
    @staticmethod
    def _get_recommendations(stats: Dict[str, Any]) -> List[str]:
        """Get performance recommendations based on cache stats"""
        recommendations = []
        
        if stats["hit_rate"] < 50:
            recommendations.append("Cache hit rate is low - consider increasing TTL for stable data")
        
        if stats["errors"] > stats["hits"] * 0.1:
            recommendations.append("High cache error rate - check Redis connection and memory")
        
        if stats.get("memory_cache_size", 0) > 500:
            recommendations.append("In-memory cache is large - consider Redis for better performance")
        
        return recommendations
    
    @staticmethod
    def _assess_health(stats: Dict[str, Any]) -> str:
        """Assess cache health status"""
        if stats["hit_rate"] >= 70 and stats["errors"] == 0:
            return "excellent"
        elif stats["hit_rate"] >= 50 and stats["errors"] < stats["hits"] * 0.05:
            return "good"
        elif stats["hit_rate"] >= 30:
            return "fair"
        else:
            return "needs_improvement"