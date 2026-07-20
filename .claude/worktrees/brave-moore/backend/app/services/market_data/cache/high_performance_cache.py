"""
High-Performance Market Data Cache - Optimized for Millions of Updates/Second

Enterprise-grade caching system featuring:
- Redis Streams for real-time data ingestion
- Connection pooling and pipelining for maximum throughput
- LUA scripts for atomic operations
- Memory-efficient data structures
- Pub/Sub for real-time notifications
- Compression and serialization optimization
- Circuit breaker protection for cache operations
"""

import asyncio
import logging
import json
import pickle
import zlib
import msgpack
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, AsyncIterator, Callable
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
from enum import Enum
import statistics

import aioredis
from aioredis import Redis, ConnectionPool
import numpy as np

logger = logging.getLogger(__name__)


class SerializationFormat(Enum):
    """Serialization format options"""
    PICKLE = "pickle"
    MSGPACK = "msgpack"
    JSON = "json"
    JSON_COMPRESSED = "json_compressed"


class CacheStrategy(Enum):
    """Cache update strategies"""
    WRITE_THROUGH = "write_through"
    WRITE_BEHIND = "write_behind"
    REFRESH_AHEAD = "refresh_ahead"


@dataclass
class CacheConfig:
    """High-performance cache configuration"""
    redis_url: str = "redis://localhost:6379"
    max_connections: int = 50
    min_connections: int = 10
    connection_timeout: int = 10
    socket_keepalive: bool = True
    socket_keepalive_options: Dict[int, int] = None
    
    # Performance settings
    pipeline_size: int = 1000
    batch_size: int = 100
    compression_threshold: int = 1024  # Compress data larger than 1KB
    serialization_format: SerializationFormat = SerializationFormat.MSGPACK
    
    # Cache TTL settings (seconds)
    quote_ttl: int = 60
    trade_ttl: int = 300
    aggregate_ttl: int = 3600
    fundamental_ttl: int = 86400
    
    # Stream settings
    stream_max_len: int = 100000
    consumer_group: str = "market_data_processors"
    consumer_name: str = "processor_1"
    
    # Circuit breaker
    max_failures: int = 5
    failure_timeout: int = 30


@dataclass
class StreamMessage:
    """Market data stream message"""
    id: str
    timestamp: datetime
    symbol: str
    data_type: str
    data: Dict[str, Any]
    metadata: Dict[str, Any] = None


class HighPerformanceMarketDataCache:
    """
    High-performance Redis-based cache optimized for millions of market data updates per second
    """
    
    def __init__(self, config: CacheConfig = None):
        self.config = config or CacheConfig()
        
        # Connection management
        self.connection_pool: Optional[ConnectionPool] = None
        self.redis: Optional[Redis] = None
        self.pub_redis: Optional[Redis] = None  # Dedicated connection for pub/sub
        
        # Performance tracking
        self.metrics = {
            'operations_per_second': deque(maxlen=60),
            'cache_hits': 0,
            'cache_misses': 0,
            'pipeline_operations': 0,
            'stream_messages': 0,
            'compression_ratio': deque(maxlen=100),
            'avg_latency': deque(maxlen=1000)
        }
        
        # Stream management
        self.stream_processors = {}
        self.stream_subscriptions = defaultdict(list)
        
        # LUA scripts for atomic operations
        self.lua_scripts = {}
        
        # Circuit breaker for cache operations
        self.failure_count = 0
        self.last_failure_time = None
        self.circuit_open = False
        
        # Background tasks
        self.background_tasks = set()
        
        # Data structures optimization
        self._init_lua_scripts()
        
    async def initialize(self):
        """Initialize the high-performance cache system"""
        try:
            # Create connection pool with optimizations
            socket_keepalive_options = self.config.socket_keepalive_options or {
                1: 1,  # TCP_KEEPIDLE
                2: 3,  # TCP_KEEPINTVL  
                3: 5,  # TCP_KEEPCNT
            }
            
            self.connection_pool = ConnectionPool.from_url(
                self.config.redis_url,
                max_connections=self.config.max_connections,
                retry_on_timeout=True,
                socket_keepalive=self.config.socket_keepalive,
                socket_keepalive_options=socket_keepalive_options,
                socket_connect_timeout=self.config.connection_timeout,
                health_check_interval=30
            )
            
            # Main Redis connection
            self.redis = Redis(connection_pool=self.connection_pool)
            
            # Dedicated pub/sub connection
            self.pub_redis = Redis.from_url(self.config.redis_url)
            
            # Test connections
            await self.redis.ping()
            await self.pub_redis.ping()
            
            # Load LUA scripts
            await self._load_lua_scripts()
            
            # Initialize stream processing
            await self._initialize_streams()
            
            # Start background tasks
            self._start_background_tasks()
            
            logger.info("High-performance market data cache initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize high-performance cache: {e}")
            raise
    
    def _init_lua_scripts(self):
        """Initialize LUA scripts for atomic operations"""
        
        # Atomic quote update with timestamp check
        self.lua_scripts['update_quote_atomic'] = """
        local key = KEYS[1]
        local new_data = ARGV[1]
        local new_timestamp = tonumber(ARGV[2])
        local ttl = tonumber(ARGV[3])
        
        local current = redis.call('GET', key)
        if current then
            local current_data = cjson.decode(current)
            local current_timestamp = tonumber(current_data.timestamp or 0)
            
            if new_timestamp <= current_timestamp then
                return 0  -- Skip update, data is older
            end
        end
        
        redis.call('SETEX', key, ttl, new_data)
        return 1  -- Updated
        """
        
        # Batch pipeline with collision detection
        self.lua_scripts['batch_update_quotes'] = """
        local updated_count = 0
        
        for i = 1, #KEYS do
            local key = KEYS[i]
            local new_data = ARGV[i * 3 - 2]
            local new_timestamp = tonumber(ARGV[i * 3 - 1])
            local ttl = tonumber(ARGV[i * 3])
            
            local current = redis.call('GET', key)
            local should_update = true
            
            if current then
                local current_data = cjson.decode(current)
                local current_timestamp = tonumber(current_data.timestamp or 0)
                
                if new_timestamp <= current_timestamp then
                    should_update = false
                end
            end
            
            if should_update then
                redis.call('SETEX', key, ttl, new_data)
                updated_count = updated_count + 1
            end
        end
        
        return updated_count
        """
        
        # Stream processing with deduplication
        self.lua_scripts['process_stream_batch'] = """
        local stream_key = KEYS[1]
        local processed_set = KEYS[2]
        local max_len = tonumber(ARGV[1])
        
        local messages = redis.call('XREAD', 'COUNT', '100', 'STREAMS', stream_key, '$')
        local processed_count = 0
        
        if messages and messages[1] and messages[1][2] then
            for i, message in ipairs(messages[1][2]) do
                local message_id = message[1]
                
                -- Check if already processed
                if redis.call('SISMEMBER', processed_set, message_id) == 0 then
                    redis.call('SADD', processed_set, message_id)
                    processed_count = processed_count + 1
                end
            end
        end
        
        -- Trim stream to max length
        redis.call('XTRIM', stream_key, 'MAXLEN', '~', max_len)
        
        return processed_count
        """
    
    async def _load_lua_scripts(self):
        """Load LUA scripts into Redis"""
        try:
            for script_name, script_content in self.lua_scripts.items():
                script_hash = await self.redis.script_load(script_content)
                self.lua_scripts[script_name + '_hash'] = script_hash
                logger.debug(f"Loaded LUA script '{script_name}' with hash {script_hash}")
                
        except Exception as e:
            logger.error(f"Failed to load LUA scripts: {e}")
            raise
    
    async def _initialize_streams(self):
        """Initialize Redis streams for real-time data"""
        try:
            # Create streams with consumer groups
            streams = ['market_quotes', 'market_trades', 'market_aggregates']
            
            for stream_name in streams:
                try:
                    # Try to create consumer group
                    await self.redis.xgroup_create(
                        stream_name,
                        self.config.consumer_group,
                        id='0',
                        mkstream=True
                    )
                    logger.info(f"Created consumer group for stream '{stream_name}'")
                except Exception as e:
                    if "BUSYGROUP" not in str(e):
                        logger.warning(f"Failed to create consumer group for '{stream_name}': {e}")
                        
        except Exception as e:
            logger.error(f"Failed to initialize streams: {e}")
            raise
    
    def _start_background_tasks(self):
        """Start background processing tasks"""
        tasks = [
            self._metrics_collector(),
            self._stream_processor(),
            self._cache_maintenance(),
            self._circuit_breaker_monitor()
        ]
        
        for task in tasks:
            background_task = asyncio.create_task(task)
            self.background_tasks.add(background_task)
            background_task.add_done_callback(self.background_tasks.discard)
    
    def _serialize_data(self, data: Any) -> bytes:
        """Serialize data with optimal format and compression"""
        try:
            if self.config.serialization_format == SerializationFormat.MSGPACK:
                serialized = msgpack.packb(data, use_bin_type=True)
            elif self.config.serialization_format == SerializationFormat.PICKLE:
                serialized = pickle.dumps(data, protocol=pickle.HIGHEST_PROTOCOL)
            elif self.config.serialization_format == SerializationFormat.JSON:
                serialized = json.dumps(data, separators=(',', ':')).encode('utf-8')
            elif self.config.serialization_format == SerializationFormat.JSON_COMPRESSED:
                json_data = json.dumps(data, separators=(',', ':')).encode('utf-8')
                serialized = zlib.compress(json_data, level=6)
            else:
                serialized = pickle.dumps(data)
            
            # Apply compression for large data
            if len(serialized) > self.config.compression_threshold:
                original_size = len(serialized)
                compressed = zlib.compress(serialized, level=6)
                
                if len(compressed) < original_size * 0.8:  # Only use if 20%+ reduction
                    compression_ratio = original_size / len(compressed)
                    self.metrics['compression_ratio'].append(compression_ratio)
                    return b'COMPRESSED:' + compressed
                    
            return serialized
            
        except Exception as e:
            logger.error(f"Serialization error: {e}")
            return pickle.dumps(data)  # Fallback to pickle
    
    def _deserialize_data(self, data: bytes) -> Any:
        """Deserialize data with decompression if needed"""
        try:
            if data.startswith(b'COMPRESSED:'):
                data = zlib.decompress(data[11:])  # Remove 'COMPRESSED:' prefix
            
            if self.config.serialization_format == SerializationFormat.MSGPACK:
                return msgpack.unpackb(data, raw=False, strict_map_key=False)
            elif self.config.serialization_format == SerializationFormat.PICKLE:
                return pickle.loads(data)
            elif self.config.serialization_format == SerializationFormat.JSON:
                return json.loads(data.decode('utf-8'))
            elif self.config.serialization_format == SerializationFormat.JSON_COMPRESSED:
                return json.loads(data.decode('utf-8'))
            else:
                return pickle.loads(data)
                
        except Exception as e:
            logger.error(f"Deserialization error: {e}")
            try:
                return pickle.loads(data)  # Fallback to pickle
            except:
                return None
    
    async def set_quote_atomic(
        self,
        symbol: str,
        quote_data: Dict[str, Any],
        ttl: int = None
    ) -> bool:
        """Set quote data atomically with timestamp checking"""
        if self.circuit_open:
            return False
            
        ttl = ttl or self.config.quote_ttl
        key = f"quote:{symbol.upper()}"
        
        try:
            start_time = time.time()
            
            # Add timestamp for ordering
            quote_data['timestamp'] = time.time()
            serialized_data = self._serialize_data(quote_data)
            
            # Execute atomic update
            script_hash = self.lua_scripts['update_quote_atomic_hash']
            result = await self.redis.evalsha(
                script_hash,
                1,  # Number of keys
                key,
                serialized_data,
                quote_data['timestamp'],
                ttl
            )
            
            # Update metrics
            latency = time.time() - start_time
            self.metrics['avg_latency'].append(latency)
            
            return bool(result)
            
        except Exception as e:
            await self._handle_cache_error(e)
            return False
    
    async def batch_set_quotes(
        self,
        quotes: List[Dict[str, Any]],
        ttl: int = None
    ) -> int:
        """Batch set multiple quotes with high throughput"""
        if self.circuit_open or not quotes:
            return 0
        
        ttl = ttl or self.config.quote_ttl
        updated_count = 0
        
        try:
            # Process in chunks for optimal pipeline size
            chunk_size = self.config.pipeline_size
            
            for i in range(0, len(quotes), chunk_size):
                chunk = quotes[i:i + chunk_size]
                keys = []
                args = []
                
                for quote in chunk:
                    symbol = quote.get('symbol', '').upper()
                    if not symbol:
                        continue
                    
                    key = f"quote:{symbol}"
                    keys.append(key)
                    
                    # Add timestamp
                    quote['timestamp'] = time.time()
                    serialized_data = self._serialize_data(quote)
                    
                    args.extend([serialized_data, quote['timestamp'], ttl])
                
                if keys:
                    # Execute batch update
                    script_hash = self.lua_scripts['batch_update_quotes_hash']
                    result = await self.redis.evalsha(script_hash, len(keys), *keys, *args)
                    updated_count += result
            
            self.metrics['pipeline_operations'] += 1
            return updated_count
            
        except Exception as e:
            await self._handle_cache_error(e)
            return 0
    
    async def get_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get quote data with high performance"""
        if self.circuit_open:
            return None
        
        key = f"quote:{symbol.upper()}"
        
        try:
            start_time = time.time()
            
            data = await self.redis.get(key)
            
            latency = time.time() - start_time
            self.metrics['avg_latency'].append(latency)
            
            if data:
                self.metrics['cache_hits'] += 1
                return self._deserialize_data(data)
            else:
                self.metrics['cache_misses'] += 1
                return None
                
        except Exception as e:
            await self._handle_cache_error(e)
            self.metrics['cache_misses'] += 1
            return None
    
    async def get_quotes_batch(self, symbols: List[str]) -> Dict[str, Dict[str, Any]]:
        """Get multiple quotes with pipelining"""
        if self.circuit_open or not symbols:
            return {}
        
        try:
            keys = [f"quote:{symbol.upper()}" for symbol in symbols]
            
            # Use pipeline for batch retrieval
            pipe = self.redis.pipeline()
            for key in keys:
                pipe.get(key)
            
            results = await pipe.execute()
            
            quotes = {}
            for symbol, data in zip(symbols, results):
                if data:
                    deserialized = self._deserialize_data(data)
                    if deserialized:
                        quotes[symbol.upper()] = deserialized
                        self.metrics['cache_hits'] += 1
                    else:
                        self.metrics['cache_misses'] += 1
                else:
                    self.metrics['cache_misses'] += 1
            
            return quotes
            
        except Exception as e:
            await self._handle_cache_error(e)
            return {}
    
    async def stream_add(
        self,
        stream_name: str,
        data: Dict[str, Any],
        max_len: int = None
    ) -> str:
        """Add data to Redis stream for real-time processing"""
        if self.circuit_open:
            return ""
        
        max_len = max_len or self.config.stream_max_len
        
        try:
            # Add to stream with automatic trimming
            message_id = await self.redis.xadd(
                stream_name,
                data,
                maxlen=max_len,
                approximate=True  # Allow approximate trimming for performance
            )
            
            self.metrics['stream_messages'] += 1
            return message_id
            
        except Exception as e:
            await self._handle_cache_error(e)
            return ""
    
    async def stream_read(
        self,
        stream_name: str,
        consumer_group: str = None,
        consumer_name: str = None,
        count: int = 100,
        block: int = 1000
    ) -> List[StreamMessage]:
        """Read from Redis stream with consumer group"""
        if self.circuit_open:
            return []
        
        consumer_group = consumer_group or self.config.consumer_group
        consumer_name = consumer_name or self.config.consumer_name
        
        try:
            # Read from consumer group
            messages = await self.redis.xreadgroup(
                consumer_group,
                consumer_name,
                {stream_name: '>'},
                count=count,
                block=block
            )
            
            stream_messages = []
            
            if messages:
                for stream, msgs in messages:
                    for msg_id, fields in msgs:
                        stream_msg = StreamMessage(
                            id=msg_id.decode() if isinstance(msg_id, bytes) else msg_id,
                            timestamp=datetime.utcnow(),  # Could extract from message
                            symbol=fields.get(b'symbol', b'').decode() if b'symbol' in fields else '',
                            data_type=fields.get(b'data_type', b'').decode() if b'data_type' in fields else '',
                            data=fields,
                            metadata={}
                        )
                        stream_messages.append(stream_msg)
            
            return stream_messages
            
        except Exception as e:
            await self._handle_cache_error(e)
            return []
    
    async def publish_real_time(self, channel: str, data: Dict[str, Any]) -> int:
        """Publish real-time data to Redis pub/sub"""
        if self.circuit_open:
            return 0
        
        try:
            serialized_data = self._serialize_data(data)
            subscribers = await self.pub_redis.publish(channel, serialized_data)
            return subscribers
            
        except Exception as e:
            await self._handle_cache_error(e)
            return 0
    
    async def subscribe_real_time(
        self,
        channel: str,
        callback: Callable[[Dict[str, Any]], None]
    ) -> asyncio.Task:
        """Subscribe to real-time data updates"""
        async def subscription_handler():
            try:
                pubsub = self.pub_redis.pubsub()
                await pubsub.subscribe(channel)
                
                async for message in pubsub.listen():
                    if message['type'] == 'message':
                        try:
                            data = self._deserialize_data(message['data'])
                            await callback(data)
                        except Exception as e:
                            logger.error(f"Error in subscription callback: {e}")
                            
            except Exception as e:
                logger.error(f"Subscription error for channel '{channel}': {e}")
        
        task = asyncio.create_task(subscription_handler())
        return task
    
    async def _handle_cache_error(self, error: Exception):
        """Handle cache operation errors with circuit breaker"""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()
        
        logger.error(f"Cache error: {error}")
        
        # Circuit breaker logic
        if self.failure_count >= self.config.max_failures:
            self.circuit_open = True
            logger.warning(f"Cache circuit breaker opened after {self.failure_count} failures")
    
    async def _circuit_breaker_monitor(self):
        """Monitor and potentially close circuit breaker"""
        while True:
            try:
                if self.circuit_open and self.last_failure_time:
                    time_since_failure = (datetime.utcnow() - self.last_failure_time).total_seconds()
                    
                    if time_since_failure >= self.config.failure_timeout:
                        # Test if cache is working
                        try:
                            await self.redis.ping()
                            self.circuit_open = False
                            self.failure_count = 0
                            logger.info("Cache circuit breaker closed - service recovered")
                        except:
                            pass  # Keep circuit open
                
                await asyncio.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                logger.error(f"Circuit breaker monitor error: {e}")
                await asyncio.sleep(30)
    
    async def _metrics_collector(self):
        """Collect performance metrics"""
        while True:
            try:
                current_time = time.time()
                
                # Calculate operations per second
                if hasattr(self, '_last_metric_time'):
                    time_diff = current_time - self._last_metric_time
                    if time_diff > 0:
                        ops_count = (
                            self.metrics['cache_hits'] + 
                            self.metrics['cache_misses'] + 
                            self.metrics['stream_messages']
                        )
                        
                        if hasattr(self, '_last_ops_count'):
                            ops_per_second = (ops_count - self._last_ops_count) / time_diff
                            self.metrics['operations_per_second'].append(ops_per_second)
                        
                        self._last_ops_count = ops_count
                
                self._last_metric_time = current_time
                
                await asyncio.sleep(1)  # Collect every second
                
            except Exception as e:
                logger.error(f"Metrics collector error: {e}")
                await asyncio.sleep(5)
    
    async def _stream_processor(self):
        """Background stream processing"""
        while True:
            try:
                # Process each active stream
                streams = ['market_quotes', 'market_trades', 'market_aggregates']
                
                for stream_name in streams:
                    messages = await self.stream_read(stream_name, count=50, block=100)
                    
                    if messages:
                        # Process messages in batch
                        await self._process_stream_messages(stream_name, messages)
                        
                        # Acknowledge processed messages
                        message_ids = [msg.id for msg in messages]
                        if message_ids:
                            await self.redis.xack(
                                stream_name,
                                self.config.consumer_group,
                                *message_ids
                            )
                
                await asyncio.sleep(0.01)  # 10ms processing loop
                
            except Exception as e:
                logger.error(f"Stream processor error: {e}")
                await asyncio.sleep(1)
    
    async def _process_stream_messages(self, stream_name: str, messages: List[StreamMessage]):
        """Process stream messages (override in subclasses)"""
        # This would be implemented based on specific business logic
        logger.debug(f"Processing {len(messages)} messages from stream '{stream_name}'")
    
    async def _cache_maintenance(self):
        """Perform periodic cache maintenance"""
        while True:
            try:
                # Clean up expired keys periodically
                await self.redis.execute_command("MEMORY", "PURGE")
                
                # Log cache statistics
                stats = await self.get_performance_stats()
                logger.debug(f"Cache stats: {stats}")
                
                await asyncio.sleep(300)  # Every 5 minutes
                
            except Exception as e:
                logger.error(f"Cache maintenance error: {e}")
                await asyncio.sleep(600)  # Wait longer on error
    
    async def get_performance_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics"""
        try:
            redis_info = await self.redis.info()
            
            # Calculate averages
            avg_ops_per_second = (
                statistics.mean(self.metrics['operations_per_second'])
                if self.metrics['operations_per_second'] else 0
            )
            
            avg_latency = (
                statistics.mean(self.metrics['avg_latency'])
                if self.metrics['avg_latency'] else 0
            )
            
            avg_compression_ratio = (
                statistics.mean(self.metrics['compression_ratio'])
                if self.metrics['compression_ratio'] else 1.0
            )
            
            hit_ratio = 0
            total_requests = self.metrics['cache_hits'] + self.metrics['cache_misses']
            if total_requests > 0:
                hit_ratio = self.metrics['cache_hits'] / total_requests
            
            return {
                'performance': {
                    'operations_per_second': avg_ops_per_second,
                    'average_latency_ms': avg_latency * 1000,
                    'cache_hit_ratio': hit_ratio,
                    'compression_ratio': avg_compression_ratio
                },
                'counters': {
                    'cache_hits': self.metrics['cache_hits'],
                    'cache_misses': self.metrics['cache_misses'],
                    'pipeline_operations': self.metrics['pipeline_operations'],
                    'stream_messages': self.metrics['stream_messages']
                },
                'redis_info': {
                    'used_memory_human': redis_info.get('used_memory_human'),
                    'connected_clients': redis_info.get('connected_clients'),
                    'total_commands_processed': redis_info.get('total_commands_processed'),
                    'instantaneous_ops_per_sec': redis_info.get('instantaneous_ops_per_sec')
                },
                'circuit_breaker': {
                    'open': self.circuit_open,
                    'failure_count': self.failure_count,
                    'last_failure': self.last_failure_time.isoformat() if self.last_failure_time else None
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting performance stats: {e}")
            return {}
    
    async def shutdown(self):
        """Shutdown the cache system gracefully"""
        logger.info("Shutting down high-performance cache...")
        
        # Cancel background tasks
        for task in self.background_tasks:
            task.cancel()
        
        # Wait for tasks to complete
        if self.background_tasks:
            await asyncio.gather(*self.background_tasks, return_exceptions=True)
        
        # Close Redis connections
        if self.redis:
            await self.redis.close()
        
        if self.pub_redis:
            await self.pub_redis.close()
        
        if self.connection_pool:
            await self.connection_pool.disconnect()
        
        logger.info("High-performance cache shutdown complete")


# Global high-performance cache instance
high_performance_cache = HighPerformanceMarketDataCache()