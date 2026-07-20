"""
Cached data provider wrapper using Redis
"""
import json
import pickle
from typing import Dict, List, Optional, Any
from datetime import datetime, date, timedelta
from decimal import Decimal
import logging
import redis.asyncio as redis
from redis.exceptions import RedisError

from app.services.data_providers.base import (
    DataProvider,
    Quote,
    HistoricalBar,
    DividendInfo,
    SplitInfo
)
from app.core.config import settings

logger = logging.getLogger(__name__)


class CachedDataProvider(DataProvider):
    """
    Wrapper that adds Redis caching to any data provider
    
    Features:
    - Configurable TTL for different data types
    - Automatic cache invalidation
    - Fallback to underlying provider on cache miss
    - Serialization of complex types
    """
    
    def __init__(self, provider: DataProvider, redis_client: Optional[redis.Redis] = None):
        super().__init__(f"cached_{provider.name}")
        self.provider = provider
        
        # Initialize Redis client
        if redis_client:
            self.redis = redis_client
        else:
            self.redis = redis.from_url(
                settings.redis_url,
                decode_responses=False,  # We'll handle encoding/decoding
                max_connections=settings.redis_max_connections
            )
        
        # Cache TTL configuration (in seconds)
        self.quote_ttl = settings.yfinance_cache_ttl_seconds
        self.historical_ttl = 3600  # 1 hour for historical data
        self.dividend_ttl = 86400    # 24 hours for dividends
        self.split_ttl = 86400       # 24 hours for splits
    
    def _make_key(self, prefix: str, *args) -> str:
        """Create Redis key"""
        parts = [prefix] + [str(arg) for arg in args]
        return ":".join(parts)
    
    def _serialize_quote(self, quote: Quote) -> str:
        """Serialize Quote to JSON"""
        return json.dumps({
            "symbol": quote.symbol,
            "price": str(quote.price),
            "open": str(quote.open) if quote.open else None,
            "high": str(quote.high) if quote.high else None,
            "low": str(quote.low) if quote.low else None,
            "close": str(quote.close) if quote.close else None,
            "volume": quote.volume,
            "timestamp": quote.timestamp.isoformat() if quote.timestamp else None,
            "source": quote.source,
            "is_delayed": quote.is_delayed,
            "delay_minutes": quote.delay_minutes
        })
    
    def _deserialize_quote(self, data: str) -> Quote:
        """Deserialize Quote from JSON"""
        obj = json.loads(data)
        return Quote(
            symbol=obj["symbol"],
            price=Decimal(obj["price"]),
            open=Decimal(obj["open"]) if obj["open"] else None,
            high=Decimal(obj["high"]) if obj["high"] else None,
            low=Decimal(obj["low"]) if obj["low"] else None,
            close=Decimal(obj["close"]) if obj["close"] else None,
            volume=obj["volume"],
            timestamp=datetime.fromisoformat(obj["timestamp"]) if obj["timestamp"] else None,
            source=obj["source"],
            is_delayed=obj["is_delayed"],
            delay_minutes=obj["delay_minutes"]
        )
    
    async def get_quote(self, symbol: str) -> Optional[Quote]:
        """Get quote with caching"""
        key = self._make_key("quote", symbol)
        
        try:
            # Try to get from cache
            cached = await self.redis.get(key)
            if cached:
                logger.debug(f"Cache hit for quote: {symbol}")
                return self._deserialize_quote(cached)
        except RedisError as e:
            logger.warning(f"Redis error getting quote cache: {e}")
        
        # Cache miss - fetch from provider
        logger.debug(f"Cache miss for quote: {symbol}")
        quote = await self.provider.get_quote(symbol)
        
        if quote:
            # Store in cache
            try:
                await self.redis.setex(
                    key,
                    self.quote_ttl,
                    self._serialize_quote(quote)
                )
            except RedisError as e:
                logger.warning(f"Redis error setting quote cache: {e}")
        
        return quote
    
    async def get_quotes(self, symbols: List[str]) -> Dict[str, Optional[Quote]]:
        """Get multiple quotes with caching"""
        results = {}
        uncached_symbols = []
        
        # Check cache for each symbol
        for symbol in symbols:
            key = self._make_key("quote", symbol)
            try:
                cached = await self.redis.get(key)
                if cached:
                    logger.debug(f"Cache hit for quote: {symbol}")
                    results[symbol] = self._deserialize_quote(cached)
                else:
                    uncached_symbols.append(symbol)
            except RedisError:
                uncached_symbols.append(symbol)
        
        # Fetch uncached symbols
        if uncached_symbols:
            logger.debug(f"Fetching {len(uncached_symbols)} uncached quotes")
            fresh_quotes = await self.provider.get_quotes(uncached_symbols)
            
            # Cache the fresh quotes
            for symbol, quote in fresh_quotes.items():
                results[symbol] = quote
                if quote:
                    key = self._make_key("quote", symbol)
                    try:
                        await self.redis.setex(
                            key,
                            self.quote_ttl,
                            self._serialize_quote(quote)
                        )
                    except RedisError:
                        pass
        
        return results
    
    async def get_historical(
        self,
        symbol: str,
        start_date: date,
        end_date: date,
        interval: str = "1d"
    ) -> List[HistoricalBar]:
        """Get historical data with caching"""
        key = self._make_key("historical", symbol, start_date.isoformat(), end_date.isoformat(), interval)
        
        try:
            # Try to get from cache
            cached = await self.redis.get(key)
            if cached:
                logger.debug(f"Cache hit for historical: {symbol}")
                # Use pickle for complex objects
                return pickle.loads(cached)
        except RedisError as e:
            logger.warning(f"Redis error getting historical cache: {e}")
        
        # Cache miss - fetch from provider
        logger.debug(f"Cache miss for historical: {symbol}")
        bars = await self.provider.get_historical(symbol, start_date, end_date, interval)
        
        if bars:
            # Store in cache
            try:
                await self.redis.setex(
                    key,
                    self.historical_ttl,
                    pickle.dumps(bars)
                )
            except RedisError as e:
                logger.warning(f"Redis error setting historical cache: {e}")
        
        return bars
    
    async def get_dividends(
        self,
        symbol: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[DividendInfo]:
        """Get dividends with caching"""
        key = self._make_key(
            "dividends",
            symbol,
            start_date.isoformat() if start_date else "all",
            end_date.isoformat() if end_date else "all"
        )
        
        try:
            cached = await self.redis.get(key)
            if cached:
                logger.debug(f"Cache hit for dividends: {symbol}")
                return pickle.loads(cached)
        except RedisError:
            pass
        
        # Cache miss
        logger.debug(f"Cache miss for dividends: {symbol}")
        dividends = await self.provider.get_dividends(symbol, start_date, end_date)
        
        if dividends:
            try:
                await self.redis.setex(
                    key,
                    self.dividend_ttl,
                    pickle.dumps(dividends)
                )
            except RedisError:
                pass
        
        return dividends
    
    async def get_splits(
        self,
        symbol: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[SplitInfo]:
        """Get splits with caching"""
        key = self._make_key(
            "splits",
            symbol,
            start_date.isoformat() if start_date else "all",
            end_date.isoformat() if end_date else "all"
        )
        
        try:
            cached = await self.redis.get(key)
            if cached:
                logger.debug(f"Cache hit for splits: {symbol}")
                return pickle.loads(cached)
        except RedisError:
            pass
        
        # Cache miss
        logger.debug(f"Cache miss for splits: {symbol}")
        splits = await self.provider.get_splits(symbol, start_date, end_date)
        
        if splits:
            try:
                await self.redis.setex(
                    key,
                    self.split_ttl,
                    pickle.dumps(splits)
                )
            except RedisError:
                pass
        
        return splits
    
    async def health_check(self) -> bool:
        """Check health of both cache and provider"""
        # Check Redis
        try:
            await self.redis.ping()
        except:
            logger.warning("Redis health check failed")
        
        # Check underlying provider
        return await self.provider.health_check()
    
    async def invalidate_quote(self, symbol: str):
        """Invalidate cached quote for a symbol"""
        key = self._make_key("quote", symbol)
        try:
            await self.redis.delete(key)
            logger.debug(f"Invalidated quote cache for {symbol}")
        except RedisError:
            pass
    
    async def invalidate_all_quotes(self):
        """Invalidate all cached quotes"""
        pattern = self._make_key("quote", "*")
        try:
            cursor = 0
            while True:
                cursor, keys = await self.redis.scan(cursor, match=pattern, count=100)
                if keys:
                    await self.redis.delete(*keys)
                if cursor == 0:
                    break
            logger.info("Invalidated all quote caches")
        except RedisError as e:
            logger.error(f"Error invalidating quote caches: {e}")
    
    async def close(self):
        """Close Redis connection"""
        await self.redis.close()