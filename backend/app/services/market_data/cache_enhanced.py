"""
Enhanced Market Data Caching System

Advanced caching with rate limiting, quota management, intelligent expiration,
and multi-tier storage for optimal performance and cost control.
"""

import asyncio
import json
import logging
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union, Callable
from collections import defaultdict, deque
from enum import Enum
import pickle
import gzip
import redis.asyncio as redis
from contextlib import asynccontextmanager

from ..models import MarketDataPoint, HistoricalData, CompanyInfo, DataProvider
from ..config import config


class CacheLevel(Enum):
    """Cache storage levels"""
    L1_MEMORY = "l1_memory"      # Fastest, smallest
    L2_REDIS = "l2_redis"        # Fast, medium size
    L3_POSTGRES = "l3_postgres"  # Slower, unlimited size


class CacheStrategy(Enum):
    """Cache strategies"""
    WRITE_THROUGH = "write_through"    # Write to cache and storage simultaneously
    WRITE_BEHIND = "write_behind"      # Write to cache immediately, storage async
    WRITE_AROUND = "write_around"      # Write only to storage, skip cache


class DataType(Enum):
    """Data types for quota management"""
    QUOTE = "quote"
    HISTORICAL = "historical"
    COMPANY_INFO = "company_info"
    REAL_TIME = "real_time"


class QuotaManager:
    """Manages API quotas and rate limits across providers"""
    
    def __init__(self):
        self.logger = logging.getLogger("market_data.quota")
        
        # Provider quotas (requests per time period)
        self.provider_quotas = {
            DataProvider.POLYGON_IO: {
                'requests_per_minute': 5,  # Free tier
                'requests_per_day': 1000,
                'cost_per_request': 0.004
            },
            DataProvider.DATABENTO: {
                'requests_per_minute': 100,
                'requests_per_day': 10000,
                'cost_per_request': 0.002
            },
            DataProvider.ALPHA_VANTAGE: {
                'requests_per_minute': 5,
                'requests_per_day': 500,
                'cost_per_request': 0.0
            },
            DataProvider.IEX_CLOUD: {
                'requests_per_minute': 60,
                'requests_per_day': 50000,
                'cost_per_request': 0.0001
            },
            DataProvider.YAHOO_FINANCE: {
                'requests_per_minute': 60,
                'requests_per_day': 2000,
                'cost_per_request': 0.0
            }
        }
        
        # Usage tracking
        self.usage_counters = defaultdict(lambda: {
            'minute': deque(maxlen=60),
            'day': deque(maxlen=1440),  # 24 hours in minutes
            'costs': deque(maxlen=10000)
        })
        
        # Budget management
        self.daily_budget = config.daily_market_data_budget or 10.0  # $10 default
        self.cost_alerts = [0.5, 0.8, 0.95]  # Alert at 50%, 80%, 95%
        self.cost_alert_sent = set()
    
    async def can_make_request(self, provider: DataProvider, data_type: DataType) -> Tuple[bool, str]:
        """Check if a request can be made without exceeding quotas"""
        if provider not in self.provider_quotas:
            return True, "No quota limits"
        
        quotas = self.provider_quotas[provider]
        now = datetime.utcnow()
        
        # Check minute limit
        minute_requests = self._count_recent_requests(provider, 'minute', now, timedelta(minutes=1))
        if minute_requests >= quotas['requests_per_minute']:
            return False, f"Minute limit exceeded: {minute_requests}/{quotas['requests_per_minute']}"
        
        # Check daily limit
        daily_requests = self._count_recent_requests(provider, 'day', now, timedelta(days=1))
        if daily_requests >= quotas['requests_per_day']:
            return False, f"Daily limit exceeded: {daily_requests}/{quotas['requests_per_day']}"
        
        # Check budget
        daily_cost = self._calculate_daily_cost(provider)
        request_cost = quotas['cost_per_request']
        
        if daily_cost + request_cost > self.daily_budget:
            return False, f"Budget exceeded: ${daily_cost + request_cost:.2f} > ${self.daily_budget:.2f}"
        
        return True, "OK"
    
    def record_request(self, provider: DataProvider, data_type: DataType):
        """Record a request for quota tracking"""
        now = datetime.utcnow()
        usage = self.usage_counters[provider]
        
        usage['minute'].append(now)
        usage['day'].append(now)
        
        # Record cost
        if provider in self.provider_quotas:
            cost = self.provider_quotas[provider]['cost_per_request']
            usage['costs'].append((now, cost))
        
        # Check for cost alerts
        self._check_cost_alerts()
    
    def _count_recent_requests(self, provider: DataProvider, period: str, now: datetime, window: timedelta) -> int:
        """Count requests in a time window"""
        usage = self.usage_counters[provider]
        cutoff = now - window
        
        # Clean old entries
        while usage[period] and usage[period][0] < cutoff:
            usage[period].popleft()
        
        return len(usage[period])
    
    def _calculate_daily_cost(self, provider: DataProvider) -> float:
        """Calculate daily cost for a provider"""
        usage = self.usage_counters[provider]
        now = datetime.utcnow()
        day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        daily_cost = 0.0
        for timestamp, cost in usage['costs']:
            if timestamp >= day_start:
                daily_cost += cost
        
        return daily_cost
    
    def _check_cost_alerts(self):
        """Check if cost alerts should be sent"""
        total_daily_cost = sum(self._calculate_daily_cost(p) for p in DataProvider)
        cost_ratio = total_daily_cost / self.daily_budget
        
        for alert_threshold in self.cost_alerts:
            if cost_ratio >= alert_threshold and alert_threshold not in self.cost_alert_sent:
                self.logger.warning(
                    f"Daily budget alert: ${total_daily_cost:.2f} ({cost_ratio:.1%} of budget)"
                )
                self.cost_alert_sent.add(alert_threshold)
        
        # Reset alerts at midnight
        now = datetime.utcnow()
        if now.hour == 0 and now.minute == 0:
            self.cost_alert_sent.clear()
    
    def get_quota_status(self) -> Dict[str, Any]:
        """Get current quota status for all providers"""
        status = {}
        now = datetime.utcnow()
        
        for provider in DataProvider:
            if provider not in self.provider_quotas:
                continue
            
            quotas = self.provider_quotas[provider]
            
            minute_usage = self._count_recent_requests(provider, 'minute', now, timedelta(minutes=1))
            daily_usage = self._count_recent_requests(provider, 'day', now, timedelta(days=1))
            daily_cost = self._calculate_daily_cost(provider)
            
            status[provider.value] = {
                'minute_usage': f"{minute_usage}/{quotas['requests_per_minute']}",
                'daily_usage': f"{daily_usage}/{quotas['requests_per_day']}",
                'daily_cost': f"${daily_cost:.2f}",
                'cost_per_request': f"${quotas['cost_per_request']:.4f}"
            }
        
        total_cost = sum(self._calculate_daily_cost(p) for p in DataProvider)
        status['total'] = {
            'daily_cost': f"${total_cost:.2f}",
            'budget': f"${self.daily_budget:.2f}",
            'budget_used': f"{total_cost / self.daily_budget:.1%}"
        }
        
        return status


class EnhancedCacheManager:
    """Multi-tier cache manager with intelligent expiration and quota management"""
    
    def __init__(self):
        self.logger = logging.getLogger("market_data.cache")
        
        # Cache levels
        self.l1_cache = {}  # In-memory cache
        self.l2_redis = None  # Redis cache
        # L3 PostgreSQL handled by database models
        
        # Cache configuration
        self.l1_max_size = 10000
        self.l1_ttl_default = 300  # 5 minutes
        
        # Cache statistics
        self.stats = defaultdict(int)
        self.hit_rates = defaultdict(lambda: deque(maxlen=1000))
        
        # Cache strategies per data type
        self.cache_strategies = {
            DataType.QUOTE: CacheStrategy.WRITE_THROUGH,
            DataType.HISTORICAL: CacheStrategy.WRITE_BEHIND,
            DataType.COMPANY_INFO: CacheStrategy.WRITE_THROUGH,
            DataType.REAL_TIME: CacheStrategy.WRITE_AROUND
        }
        
        # TTL settings per data type
        self.ttl_settings = {
            DataType.QUOTE: 60,        # 1 minute
            DataType.HISTORICAL: 3600, # 1 hour
            DataType.COMPANY_INFO: 86400, # 24 hours
            DataType.REAL_TIME: 10     # 10 seconds
        }
        
        # Compression settings
        self.compression_enabled = True
        self.compression_threshold = 1024  # Compress if > 1KB
        
        # Quota manager
        self.quota_manager = QuotaManager()
        
        # Background tasks
        self._cleanup_task = None
        self._stats_task = None
        
        self._initialized = False
    
    async def initialize(self):
        """Initialize the cache manager"""
        if self._initialized:
            return
        
        self.logger.info("Initializing Enhanced Cache Manager")
        
        try:
            # Initialize Redis connection
            if config.redis_url:
                self.l2_redis = redis.from_url(
                    config.redis_url,
                    decode_responses=False,  # We handle encoding/decoding
                    max_connections=20
                )
                
                # Test connection
                await self.l2_redis.ping()
                self.logger.info("Redis cache connected")
            else:
                self.logger.warning("No Redis URL configured, using memory cache only")
            
            # Start background tasks
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
            self._stats_task = asyncio.create_task(self._stats_loop())
            
            self._initialized = True
            self.logger.info("Enhanced Cache Manager initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize cache manager: {e}")
            raise
    
    @asynccontextmanager
    async def quota_check(self, provider: DataProvider, data_type: DataType):
        """Context manager for quota checking"""
        can_proceed, reason = await self.quota_manager.can_make_request(provider, data_type)
        
        if not can_proceed:
            raise QuotaExceededException(f"Quota exceeded for {provider}: {reason}")
        
        try:
            yield
            # Record successful request
            self.quota_manager.record_request(provider, data_type)
        except Exception:
            # Don't record failed requests
            raise
    
    async def get_quote(self, symbol: str, provider_fallback: Callable = None) -> Optional[MarketDataPoint]:
        """Get quote with multi-tier caching"""
        cache_key = f"quote:{symbol.upper()}"
        
        # Try L1 cache first
        l1_result = await self._get_from_l1(cache_key)
        if l1_result:
            self.stats['l1_hits'] += 1
            self.hit_rates['quote'].append(True)
            return l1_result
        
        # Try L2 cache (Redis)
        l2_result = await self._get_from_l2(cache_key)
        if l2_result:
            self.stats['l2_hits'] += 1
            self.hit_rates['quote'].append(True)
            
            # Promote to L1
            await self._set_to_l1(cache_key, l2_result, self.ttl_settings[DataType.QUOTE])
            return l2_result
        
        # Cache miss - use provider fallback
        self.stats['misses'] += 1
        self.hit_rates['quote'].append(False)
        
        if provider_fallback:
            try:
                quote = await provider_fallback()
                if quote:
                    await self.store_quote(symbol, quote)
                return quote
            except Exception as e:
                self.logger.error(f"Provider fallback failed: {e}")
        
        return None
    
    async def store_quote(self, symbol: str, quote: MarketDataPoint, ttl: int = None):
        """Store quote in appropriate cache levels"""
        cache_key = f"quote:{symbol.upper()}"
        ttl = ttl or self.ttl_settings[DataType.QUOTE]
        strategy = self.cache_strategies[DataType.QUOTE]
        
        if strategy == CacheStrategy.WRITE_THROUGH:
            # Write to all levels
            await self._set_to_l1(cache_key, quote, ttl)
            await self._set_to_l2(cache_key, quote, ttl)
        elif strategy == CacheStrategy.WRITE_BEHIND:
            # Write to L1 immediately, L2 async
            await self._set_to_l1(cache_key, quote, ttl)
            asyncio.create_task(self._set_to_l2(cache_key, quote, ttl))
        elif strategy == CacheStrategy.WRITE_AROUND:
            # Skip cache, go directly to persistent storage
            pass
        
        self.stats['stores'] += 1
    
    async def get_historical(
        self, 
        symbol: str, 
        start_date: str, 
        end_date: str, 
        interval: str,
        provider_fallback: Callable = None
    ) -> Optional[HistoricalData]:
        """Get historical data with intelligent caching"""
        cache_key = f"hist:{symbol.upper()}:{start_date}:{end_date}:{interval}"
        
        # Try L2 cache first (historical data is larger)
        l2_result = await self._get_from_l2(cache_key)
        if l2_result:
            self.stats['l2_hits'] += 1
            self.hit_rates['historical'].append(True)
            return l2_result
        
        # Try L3 cache (PostgreSQL) - would query database
        # This would be implemented with database queries
        
        # Cache miss
        self.stats['misses'] += 1
        self.hit_rates['historical'].append(False)
        
        if provider_fallback:
            try:
                historical = await provider_fallback()
                if historical:
                    await self.store_historical(symbol, historical)
                return historical
            except Exception as e:
                self.logger.error(f"Historical provider fallback failed: {e}")
        
        return None
    
    async def store_historical(self, symbol: str, historical: HistoricalData, ttl: int = None):
        """Store historical data efficiently"""
        cache_key = f"hist:{symbol.upper()}:{historical.start_date}:{historical.end_date}:{historical.interval}"
        ttl = ttl or self.ttl_settings[DataType.HISTORICAL]
        
        # Historical data goes to L2 cache (too large for L1)
        await self._set_to_l2(cache_key, historical, ttl)
        
        # Also store in database for L3 cache
        # This would involve database operations
        
        self.stats['stores'] += 1
    
    async def get_company_info(self, symbol: str, provider_fallback: Callable = None) -> Optional[CompanyInfo]:
        """Get company info with long-term caching"""
        cache_key = f"company:{symbol.upper()}"
        
        # Try L1 first
        l1_result = await self._get_from_l1(cache_key)
        if l1_result:
            self.stats['l1_hits'] += 1
            return l1_result
        
        # Try L2
        l2_result = await self._get_from_l2(cache_key)
        if l2_result:
            self.stats['l2_hits'] += 1
            await self._set_to_l1(cache_key, l2_result, self.ttl_settings[DataType.COMPANY_INFO])
            return l2_result
        
        # Cache miss
        self.stats['misses'] += 1
        
        if provider_fallback:
            try:
                info = await provider_fallback()
                if info:
                    await self.store_company_info(symbol, info)
                return info
            except Exception as e:
                self.logger.error(f"Company info provider fallback failed: {e}")
        
        return None
    
    async def store_company_info(self, symbol: str, info: CompanyInfo, ttl: int = None):
        """Store company info with long TTL"""
        cache_key = f"company:{symbol.upper()}"
        ttl = ttl or self.ttl_settings[DataType.COMPANY_INFO]
        
        await self._set_to_l1(cache_key, info, ttl)
        await self._set_to_l2(cache_key, info, ttl)
        
        self.stats['stores'] += 1
    
    # L1 Cache Operations (In-Memory)
    async def _get_from_l1(self, key: str) -> Any:
        """Get from L1 (memory) cache"""
        if key in self.l1_cache:
            data, expiry = self.l1_cache[key]
            
            if expiry and datetime.utcnow() > expiry:
                del self.l1_cache[key]
                return None
            
            return data
        
        return None
    
    async def _set_to_l1(self, key: str, value: Any, ttl: int):
        """Set to L1 (memory) cache with LRU eviction"""
        # Check size limit
        if len(self.l1_cache) >= self.l1_max_size:
            await self._evict_l1_lru()
        
        expiry = datetime.utcnow() + timedelta(seconds=ttl) if ttl else None
        self.l1_cache[key] = (value, expiry)
    
    async def _evict_l1_lru(self):
        """Evict least recently used items from L1 cache"""
        # Simple eviction - remove 10% of items
        evict_count = max(1, len(self.l1_cache) // 10)
        
        # Remove items with earliest expiry
        expired_items = []
        for k, (_, expiry) in self.l1_cache.items():
            if expiry:
                expired_items.append((k, expiry))
        
        expired_items.sort(key=lambda x: x[1])
        
        for key, _ in expired_items[:evict_count]:
            del self.l1_cache[key]
    
    # L2 Cache Operations (Redis)
    async def _get_from_l2(self, key: str) -> Any:
        """Get from L2 (Redis) cache"""
        if not self.l2_redis:
            return None
        
        try:
            data = await self.l2_redis.get(key)
            if data:
                # Decompress if needed
                if data.startswith(b'gzip:'):
                    data = gzip.decompress(data[5:])
                
                # Deserialize
                return pickle.loads(data)
        except Exception as e:
            self.logger.error(f"Redis get error: {e}")
        
        return None
    
    async def _set_to_l2(self, key: str, value: Any, ttl: int):
        """Set to L2 (Redis) cache with compression"""
        if not self.l2_redis:
            return
        
        try:
            # Serialize
            data = pickle.dumps(value)
            
            # Compress if large
            if self.compression_enabled and len(data) > self.compression_threshold:
                data = b'gzip:' + gzip.compress(data)
            
            # Store with TTL
            await self.l2_redis.setex(key, ttl, data)
        except Exception as e:
            self.logger.error(f"Redis set error: {e}")
    
    async def invalidate_symbol(self, symbol: str):
        """Invalidate all cache entries for a symbol"""
        symbol = symbol.upper()
        patterns = [
            f"quote:{symbol}",
            f"hist:{symbol}:*",
            f"company:{symbol}"
        ]
        
        # L1 cache
        keys_to_remove = []
        for key in self.l1_cache:
            for pattern in patterns:
                if key.startswith(pattern.replace('*', '')):
                    keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self.l1_cache[key]
        
        # L2 cache (Redis)
        if self.l2_redis:
            for pattern in patterns:
                try:
                    if '*' in pattern:
                        keys = await self.l2_redis.keys(pattern)
                        if keys:
                            await self.l2_redis.delete(*keys)
                    else:
                        await self.l2_redis.delete(pattern)
                except Exception as e:
                    self.logger.error(f"Redis invalidation error: {e}")
        
        self.logger.info(f"Invalidated cache for symbol: {symbol}")
    
    async def _cleanup_loop(self):
        """Background cleanup task"""
        while True:
            try:
                await asyncio.sleep(300)  # Run every 5 minutes
                
                # Clean expired L1 entries
                expired_keys = []
                now = datetime.utcnow()
                
                for key, (_, expiry) in self.l1_cache.items():
                    if expiry and now > expiry:
                        expired_keys.append(key)
                
                for key in expired_keys:
                    del self.l1_cache[key]
                
                if expired_keys:
                    self.logger.debug(f"Cleaned up {len(expired_keys)} expired L1 entries")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Cleanup loop error: {e}")
    
    async def _stats_loop(self):
        """Background statistics collection"""
        while True:
            try:
                await asyncio.sleep(60)  # Run every minute
                
                # Calculate hit rates
                for data_type in ['quote', 'historical']:
                    hits = self.hit_rates[data_type]
                    if hits:
                        hit_rate = sum(hits) / len(hits)
                        self.logger.debug(f"{data_type} hit rate: {hit_rate:.2%}")
                
                # Log cache sizes
                l1_size = len(self.l1_cache)
                self.logger.debug(f"L1 cache size: {l1_size}/{self.l1_max_size}")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Stats loop error: {e}")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics"""
        l1_size = len(self.l1_cache)
        
        # Calculate hit rates
        hit_rates = {}
        for data_type in ['quote', 'historical']:
            hits = self.hit_rates[data_type]
            if hits:
                hit_rates[data_type] = sum(hits) / len(hits)
            else:
                hit_rates[data_type] = 0.0
        
        stats = {
            'l1_cache': {
                'size': l1_size,
                'max_size': self.l1_max_size,
                'usage_percent': (l1_size / self.l1_max_size) * 100
            },
            'l2_cache': {
                'connected': self.l2_redis is not None
            },
            'hit_rates': hit_rates,
            'operations': dict(self.stats),
            'quota_status': self.quota_manager.get_quota_status()
        }
        
        return stats
    
    async def shutdown(self):
        """Shutdown the cache manager"""
        self.logger.info("Shutting down Enhanced Cache Manager")
        
        # Cancel background tasks
        if self._cleanup_task:
            self._cleanup_task.cancel()
        if self._stats_task:
            self._stats_task.cancel()
        
        # Close Redis connection
        if self.l2_redis:
            await self.l2_redis.close()
        
        # Clear L1 cache
        self.l1_cache.clear()
        
        self._initialized = False
        self.logger.info("Enhanced Cache Manager shutdown complete")


class QuotaExceededException(Exception):
    """Raised when API quota is exceeded"""
    pass