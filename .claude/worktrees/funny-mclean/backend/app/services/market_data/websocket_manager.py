"""
WebSocket Manager - Real-Time Market Data Integration

Comprehensive WebSocket connection management for real-time market data:
- Multi-provider WebSocket connections (Polygon.io, Alpaca, Databento)
- Event-driven architecture with handlers for trades, quotes, aggregates
- Automatic reconnection with exponential backoff
- Data buffering and stream processing
- Connection health monitoring and failover
"""

import asyncio
import json
import logging
import websocket
import ssl
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable, AsyncIterator
from collections import defaultdict, deque
from dataclasses import dataclass, asdict
from enum import Enum
import aiohttp
import backoff
import pandas as pd

from app.core.config import Config
from app.services.market_data.cache.cache_manager import CacheManager

logger = logging.getLogger(__name__)


class ConnectionState(Enum):
    """WebSocket connection states"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"  
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    FAILED = "failed"


class MessageType(Enum):
    """Market data message types"""
    TRADE = "trade"
    QUOTE = "quote" 
    AGGREGATE = "aggregate"
    STATUS = "status"
    ERROR = "error"
    HEARTBEAT = "heartbeat"


@dataclass
class TradeData:
    """Normalized trade data structure"""
    symbol: str
    price: float
    size: int
    timestamp: datetime
    exchange: str
    conditions: List[str]
    provider: str
    tape: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class QuoteData:
    """Normalized quote data structure"""
    symbol: str
    bid: float
    ask: float
    bid_size: int
    ask_size: int
    timestamp: datetime
    exchange: str
    provider: str
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass 
class AggregateData:
    """Normalized aggregate/bar data structure"""
    symbol: str
    open: float
    high: float
    low: float
    close: float
    volume: int
    vwap: float
    timestamp: datetime
    provider: str
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class AsyncBuffer:
    """Asynchronous data buffer with size limits"""
    
    def __init__(self, max_size: int = 100000):
        self.max_size = max_size
        self.buffer = deque()
        self.lock = asyncio.Lock()
    
    async def put(self, item: Any):
        """Add item to buffer"""
        async with self.lock:
            self.buffer.append(item)
            if len(self.buffer) > self.max_size:
                self.buffer.popleft()
    
    async def get_batch(self, size: int = 100) -> List[Any]:
        """Get batch of items from buffer"""
        async with self.lock:
            batch = []
            for _ in range(min(size, len(self.buffer))):
                if self.buffer:
                    batch.append(self.buffer.popleft())
            return batch
    
    async def size(self) -> int:
        """Get current buffer size"""
        async with self.lock:
            return len(self.buffer)


class ExponentialBackoff:
    """Exponential backoff strategy for reconnections"""
    
    def __init__(
        self,
        initial_delay: float = 1.0,
        max_delay: float = 300.0,
        multiplier: float = 2.0,
        jitter: bool = True
    ):
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.multiplier = multiplier
        self.jitter = jitter
        self.current_delay = initial_delay
        
    def get_delay(self) -> float:
        """Get next delay value"""
        delay = self.current_delay
        self.current_delay = min(self.current_delay * self.multiplier, self.max_delay)
        
        if self.jitter:
            # Add random jitter to prevent thundering herd
            import random
            delay *= (0.5 + random.random() * 0.5)
        
        return delay
    
    def reset(self):
        """Reset backoff to initial delay"""
        self.current_delay = self.initial_delay


class PolygonWebSocketClient:
    """Polygon.io WebSocket client implementation"""
    
    def __init__(self, api_key: str, feed: str = 'sip', market: str = 'stocks'):
        self.api_key = api_key
        self.feed = feed  # 'sip' or 'delayed'
        self.market = market
        self.url = f"wss://socket.polygon.io/{market}"
        self.websocket = None
        self.subscriptions = set()
        self.event_handlers = defaultdict(list)
        self.state = ConnectionState.DISCONNECTED
        self.backoff = ExponentialBackoff()
        
    def on(self, event: str, handler: Callable):
        """Register event handler"""
        self.event_handlers[event].append(handler)
    
    async def connect(self):
        """Connect to Polygon WebSocket"""
        try:
            self.state = ConnectionState.CONNECTING
            logger.info("Connecting to Polygon.io WebSocket...")
            
            # Create SSL context
            ssl_context = ssl.create_default_context()
            
            # Connect to WebSocket
            async with aiohttp.ClientSession() as session:
                self.websocket = await session.ws_connect(
                    self.url,
                    ssl=ssl_context,
                    heartbeat=30
                )
                
                # Authenticate
                auth_message = {
                    "action": "auth",
                    "params": self.api_key
                }
                await self.websocket.send_str(json.dumps(auth_message))
                
                # Wait for auth response
                auth_response = await self.websocket.receive()
                auth_data = json.loads(auth_response.data)
                
                if auth_data.get("status") != "auth_success":
                    raise Exception(f"Authentication failed: {auth_data}")
                
                self.state = ConnectionState.CONNECTED
                logger.info("Successfully connected to Polygon.io WebSocket")
                
                # Restore subscriptions if any
                await self._restore_subscriptions()
                
                # Start message processing
                asyncio.create_task(self._process_messages())
                
                self.backoff.reset()
                
        except Exception as e:
            self.state = ConnectionState.FAILED
            logger.error(f"Failed to connect to Polygon WebSocket: {e}")
            raise
    
    async def _restore_subscriptions(self):
        """Restore subscriptions after reconnection"""
        if self.subscriptions:
            subscribe_message = {
                "action": "subscribe",
                "params": ",".join(self.subscriptions)
            }
            await self.websocket.send_str(json.dumps(subscribe_message))
            logger.info(f"Restored {len(self.subscriptions)} subscriptions")
    
    async def _process_messages(self):
        """Process incoming WebSocket messages"""
        try:
            async for msg in self.websocket:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    try:
                        data = json.loads(msg.data)
                        await self._handle_message(data)
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to decode message: {e}")
                        
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    logger.error(f"WebSocket error: {msg.data}")
                    break
                    
        except Exception as e:
            logger.error(f"Error processing messages: {e}")
        finally:
            self.state = ConnectionState.DISCONNECTED
    
    async def _handle_message(self, data: List[Dict[str, Any]]):
        """Handle incoming message data"""
        for message in data:
            msg_type = message.get('ev')  # Event type
            
            if msg_type == 'T':  # Trade
                trade_data = TradeData(
                    symbol=message.get('sym'),
                    price=message.get('p'),
                    size=message.get('s'),
                    timestamp=datetime.fromtimestamp(message.get('t') / 1000),
                    exchange=message.get('x', ''),
                    conditions=message.get('c', []),
                    provider='polygon',
                    tape=message.get('z')
                )
                
                # Trigger event handlers
                for handler in self.event_handlers['trade']:
                    try:
                        await handler(trade_data)
                    except Exception as e:
                        logger.error(f"Error in trade handler: {e}")
            
            elif msg_type == 'Q':  # Quote
                quote_data = QuoteData(
                    symbol=message.get('sym'),
                    bid=message.get('bp'),
                    ask=message.get('ap'),
                    bid_size=message.get('bs'),
                    ask_size=message.get('as'),
                    timestamp=datetime.fromtimestamp(message.get('t') / 1000),
                    exchange=message.get('x', ''),
                    provider='polygon'
                )
                
                # Trigger event handlers  
                for handler in self.event_handlers['quote']:
                    try:
                        await handler(quote_data)
                    except Exception as e:
                        logger.error(f"Error in quote handler: {e}")
            
            elif msg_type == 'A':  # Aggregate
                agg_data = AggregateData(
                    symbol=message.get('sym'),
                    open=message.get('o'),
                    high=message.get('h'),
                    low=message.get('l'),
                    close=message.get('c'),
                    volume=message.get('v'),
                    vwap=message.get('vw'),
                    timestamp=datetime.fromtimestamp(message.get('e') / 1000),
                    provider='polygon'
                )
                
                # Trigger event handlers
                for handler in self.event_handlers['aggregate']:
                    try:
                        await handler(agg_data)
                    except Exception as e:
                        logger.error(f"Error in aggregate handler: {e}")
            
            elif msg_type == 'status':
                # Handle status messages
                for handler in self.event_handlers['status']:
                    try:
                        await handler(message)
                    except Exception as e:
                        logger.error(f"Error in status handler: {e}")
    
    async def subscribe_trades(self, symbols: List[str]):
        """Subscribe to trade data for symbols"""
        trades_params = [f"T.{symbol}" for symbol in symbols]
        self.subscriptions.update(trades_params)
        
        if self.state == ConnectionState.CONNECTED:
            subscribe_message = {
                "action": "subscribe", 
                "params": ",".join(trades_params)
            }
            await self.websocket.send_str(json.dumps(subscribe_message))
            logger.info(f"Subscribed to trades for {len(symbols)} symbols")
    
    async def subscribe_quotes(self, symbols: List[str]):
        """Subscribe to quote data for symbols"""
        quote_params = [f"Q.{symbol}" for symbol in symbols]
        self.subscriptions.update(quote_params)
        
        if self.state == ConnectionState.CONNECTED:
            subscribe_message = {
                "action": "subscribe",
                "params": ",".join(quote_params)
            }
            await self.websocket.send_str(json.dumps(subscribe_message))
            logger.info(f"Subscribed to quotes for {len(symbols)} symbols")
    
    async def subscribe_aggregates(self, symbols: List[str]):
        """Subscribe to aggregate data for symbols"""
        agg_params = [f"A.{symbol}" for symbol in symbols]
        self.subscriptions.update(agg_params)
        
        if self.state == ConnectionState.CONNECTED:
            subscribe_message = {
                "action": "subscribe",
                "params": ",".join(agg_params)
            }
            await self.websocket.send_str(json.dumps(subscribe_message))
            logger.info(f"Subscribed to aggregates for {len(symbols)} symbols")


class RealTimeDataManager:
    """
    Comprehensive real-time market data management system
    
    Manages WebSocket connections to multiple providers,
    processes real-time data streams, and provides unified access.
    """
    
    def __init__(self):
        self.connections = {}
        self.subscriptions = defaultdict(set)
        self.data_buffer = AsyncBuffer(max_size=100000)
        self.cache_manager = CacheManager()
        
        # Event callbacks
        self.trade_callbacks = []
        self.quote_callbacks = []
        self.aggregate_callbacks = []
        
        # Connection monitoring
        self.connection_health = {}
        self.last_heartbeat = {}
        
        # Processing stats
        self.message_count = defaultdict(int)
        self.last_message_time = {}
        
    async def initialize(self):
        """Initialize all WebSocket connections"""
        await self.establish_connections()
        
        # Start monitoring tasks
        asyncio.create_task(self._monitor_connections())
        asyncio.create_task(self._process_data_buffer())
        asyncio.create_task(self._connection_health_check())
        
        logger.info("RealTimeDataManager initialized successfully")
    
    async def establish_connections(self):
        """Establish WebSocket connections to all providers"""
        
        # Polygon.io WebSocket
        if Config.POLYGON_API_KEY:
            await self._connect_polygon()
        
        # Add other providers as needed
        # await self._connect_alpaca()
        # await self._connect_databento()
        
    async def _connect_polygon(self):
        """Connect to Polygon.io real-time WebSocket"""
        try:
            polygon_client = PolygonWebSocketClient(
                api_key=Config.POLYGON_API_KEY,
                feed='sip',  # SIP feed for consolidated data
                market='stocks'
            )
            
            # Set up event handlers
            polygon_client.on('trade', self._handle_polygon_trade)
            polygon_client.on('quote', self._handle_polygon_quote)
            polygon_client.on('aggregate', self._handle_polygon_aggregate)
            polygon_client.on('status', self._handle_status_update)
            
            # Connect with retry logic
            await self._connect_with_retry(polygon_client)
            
            self.connections['polygon'] = polygon_client
            self.connection_health['polygon'] = True
            self.last_heartbeat['polygon'] = datetime.utcnow()
            
            logger.info("Polygon.io WebSocket connection established")
            
        except Exception as e:
            logger.error(f"Failed to connect to Polygon.io: {e}")
            self.connection_health['polygon'] = False
    
    @backoff.on_exception(
        backoff.expo,
        Exception,
        max_tries=5,
        max_time=300
    )
    async def _connect_with_retry(self, client):
        """Connect to WebSocket with exponential backoff retry"""
        await client.connect()
    
    async def _handle_polygon_trade(self, trade_data: TradeData):
        """Process real-time trade from Polygon"""
        try:
            # Update message statistics
            self.message_count['polygon_trades'] += 1
            self.last_message_time['polygon'] = datetime.utcnow()
            
            # Update in-memory cache
            await self._update_trade_cache(trade_data)
            
            # Add to processing buffer
            await self.data_buffer.put({
                'type': 'trade',
                'data': trade_data.to_dict(),
                'timestamp': datetime.utcnow()
            })
            
            # Trigger registered callbacks
            for callback in self.trade_callbacks:
                try:
                    await callback(trade_data)
                except Exception as e:
                    logger.error(f"Error in trade callback: {e}")
            
            # Check for price alerts
            await self._check_price_alerts(trade_data)
            
        except Exception as e:
            logger.error(f"Error handling Polygon trade: {e}")
    
    async def _handle_polygon_quote(self, quote_data: QuoteData):
        """Process real-time quote from Polygon"""
        try:
            # Update message statistics
            self.message_count['polygon_quotes'] += 1
            self.last_message_time['polygon'] = datetime.utcnow()
            
            # Update in-memory cache
            await self._update_quote_cache(quote_data)
            
            # Add to processing buffer
            await self.data_buffer.put({
                'type': 'quote',
                'data': quote_data.to_dict(),
                'timestamp': datetime.utcnow()
            })
            
            # Trigger registered callbacks
            for callback in self.quote_callbacks:
                try:
                    await callback(quote_data)
                except Exception as e:
                    logger.error(f"Error in quote callback: {e}")
            
        except Exception as e:
            logger.error(f"Error handling Polygon quote: {e}")
    
    async def _handle_polygon_aggregate(self, agg_data: AggregateData):
        """Process real-time aggregate from Polygon"""
        try:
            # Update message statistics  
            self.message_count['polygon_aggregates'] += 1
            self.last_message_time['polygon'] = datetime.utcnow()
            
            # Update in-memory cache
            await self._update_aggregate_cache(agg_data)
            
            # Add to processing buffer
            await self.data_buffer.put({
                'type': 'aggregate',
                'data': agg_data.to_dict(),
                'timestamp': datetime.utcnow()
            })
            
            # Trigger registered callbacks
            for callback in self.aggregate_callbacks:
                try:
                    await callback(agg_data)
                except Exception as e:
                    logger.error(f"Error in aggregate callback: {e}")
            
        except Exception as e:
            logger.error(f"Error handling Polygon aggregate: {e}")
    
    async def _handle_status_update(self, status_data: Dict[str, Any]):
        """Handle WebSocket status updates"""
        logger.info(f"WebSocket status update: {status_data}")
        
        # Update connection health based on status
        if status_data.get('status') == 'connected':
            self.connection_health['polygon'] = True
        elif status_data.get('status') == 'disconnected':
            self.connection_health['polygon'] = False
            # Trigger reconnection
            asyncio.create_task(self._reconnect_polygon())
    
    async def _update_trade_cache(self, trade_data: TradeData):
        """Update cache with latest trade data"""
        cache_key = f"latest_trade_{trade_data.symbol}"
        await self.cache_manager.set(
            cache_key,
            trade_data.to_dict(),
            ttl=300  # 5 minutes
        )
    
    async def _update_quote_cache(self, quote_data: QuoteData):
        """Update cache with latest quote data"""
        cache_key = f"latest_quote_{quote_data.symbol}"
        await self.cache_manager.set(
            cache_key,
            quote_data.to_dict(),
            ttl=60  # 1 minute
        )
    
    async def _update_aggregate_cache(self, agg_data: AggregateData):
        """Update cache with latest aggregate data"""
        cache_key = f"latest_agg_{agg_data.symbol}"
        await self.cache_manager.set(
            cache_key,
            agg_data.to_dict(),
            ttl=300  # 5 minutes
        )
    
    async def _check_price_alerts(self, trade_data: TradeData):
        """Check if trade triggers any price alerts"""
        # This would integrate with an alerts system
        # For now, just log significant price movements
        
        # Get previous price from cache
        cache_key = f"prev_price_{trade_data.symbol}"
        prev_price = await self.cache_manager.get(cache_key)
        
        if prev_price:
            price_change = abs(trade_data.price - prev_price) / prev_price
            if price_change > 0.05:  # 5% change
                logger.warning(
                    f"Significant price movement in {trade_data.symbol}: "
                    f"{prev_price} -> {trade_data.price} ({price_change:.2%})"
                )
        
        # Update previous price
        await self.cache_manager.set(cache_key, trade_data.price, ttl=3600)
    
    async def _process_data_buffer(self):
        """Process buffered data in batches"""
        while True:
            try:
                batch = await self.data_buffer.get_batch(100)
                
                if batch:
                    # Process batch (store to database, etc.)
                    await self._store_batch_to_database(batch)
                    logger.debug(f"Processed batch of {len(batch)} messages")
                
                # Wait before next batch
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Error processing data buffer: {e}")
                await asyncio.sleep(5)
    
    async def _store_batch_to_database(self, batch: List[Dict[str, Any]]):
        """Store batch of data to time-series database"""
        # This would integrate with TimescaleDB or similar
        # For now, just count the messages
        
        trades = [item for item in batch if item['type'] == 'trade']
        quotes = [item for item in batch if item['type'] == 'quote'] 
        aggregates = [item for item in batch if item['type'] == 'aggregate']
        
        if trades:
            logger.debug(f"Would store {len(trades)} trades to database")
        if quotes:
            logger.debug(f"Would store {len(quotes)} quotes to database")
        if aggregates:
            logger.debug(f"Would store {len(aggregates)} aggregates to database")
    
    async def _monitor_connections(self):
        """Monitor WebSocket connection health"""
        while True:
            try:
                for provider, client in self.connections.items():
                    if hasattr(client, 'state'):
                        if client.state == ConnectionState.DISCONNECTED:
                            logger.warning(f"{provider} connection lost, attempting reconnection")
                            await self._reconnect_provider(provider)
                
                await asyncio.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                logger.error(f"Error monitoring connections: {e}")
                await asyncio.sleep(30)
    
    async def _connection_health_check(self):
        """Periodic health check for connections"""
        while True:
            try:
                for provider in self.connections:
                    last_message = self.last_message_time.get(provider)
                    
                    if last_message:
                        time_since_last = (datetime.utcnow() - last_message).total_seconds()
                        
                        # If no message for 5 minutes, consider unhealthy
                        if time_since_last > 300:
                            logger.warning(
                                f"{provider} hasn't sent messages for {time_since_last}s"
                            )
                            self.connection_health[provider] = False
                        else:
                            self.connection_health[provider] = True
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Error in health check: {e}")
                await asyncio.sleep(60)
    
    async def _reconnect_provider(self, provider: str):
        """Reconnect to a specific provider"""
        if provider == 'polygon':
            await self._reconnect_polygon()
        # Add other providers as needed
    
    async def _reconnect_polygon(self):
        """Reconnect to Polygon.io WebSocket"""
        try:
            if 'polygon' in self.connections:
                # Close existing connection
                client = self.connections['polygon']
                if hasattr(client, 'websocket') and client.websocket:
                    await client.websocket.close()
            
            # Re-establish connection
            await self._connect_polygon()
            
        except Exception as e:
            logger.error(f"Failed to reconnect to Polygon: {e}")
    
    # Public API methods
    
    async def subscribe_to_trades(self, symbols: List[str], provider: str = 'polygon'):
        """Subscribe to trade data for symbols"""
        if provider in self.connections:
            client = self.connections[provider]
            if hasattr(client, 'subscribe_trades'):
                await client.subscribe_trades(symbols)
                self.subscriptions[provider].update(symbols)
                logger.info(f"Subscribed to trades for {symbols} on {provider}")
    
    async def subscribe_to_quotes(self, symbols: List[str], provider: str = 'polygon'):
        """Subscribe to quote data for symbols"""
        if provider in self.connections:
            client = self.connections[provider]
            if hasattr(client, 'subscribe_quotes'):
                await client.subscribe_quotes(symbols)
                self.subscriptions[provider].update(symbols)
                logger.info(f"Subscribed to quotes for {symbols} on {provider}")
    
    async def subscribe_to_aggregates(self, symbols: List[str], provider: str = 'polygon'):
        """Subscribe to aggregate data for symbols"""
        if provider in self.connections:
            client = self.connections[provider]
            if hasattr(client, 'subscribe_aggregates'):
                await client.subscribe_aggregates(symbols)
                self.subscriptions[provider].update(symbols)
                logger.info(f"Subscribed to aggregates for {symbols} on {provider}")
    
    def register_trade_callback(self, callback: Callable[[TradeData], None]):
        """Register callback for trade data"""
        self.trade_callbacks.append(callback)
    
    def register_quote_callback(self, callback: Callable[[QuoteData], None]):
        """Register callback for quote data"""
        self.quote_callbacks.append(callback)
    
    def register_aggregate_callback(self, callback: Callable[[AggregateData], None]):
        """Register callback for aggregate data"""
        self.aggregate_callbacks.append(callback)
    
    async def get_connection_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all WebSocket connections"""
        status = {}
        
        for provider, client in self.connections.items():
            status[provider] = {
                'state': client.state.value if hasattr(client, 'state') else 'unknown',
                'healthy': self.connection_health.get(provider, False),
                'subscriptions': list(self.subscriptions[provider]),
                'message_count': self.message_count.get(f'{provider}_trades', 0) +
                                self.message_count.get(f'{provider}_quotes', 0) +
                                self.message_count.get(f'{provider}_aggregates', 0),
                'last_message': self.last_message_time.get(provider)
            }
        
        return status
    
    async def get_realtime_data_stream(
        self,
        symbols: List[str],
        data_types: List[str] = ['trades', 'quotes']
    ) -> AsyncIterator[Dict[str, Any]]:
        """Get real-time data stream for symbols"""
        
        # Subscribe to requested data types
        for data_type in data_types:
            if data_type == 'trades':
                await self.subscribe_to_trades(symbols)
            elif data_type == 'quotes':
                await self.subscribe_to_quotes(symbols)
            elif data_type == 'aggregates':
                await self.subscribe_to_aggregates(symbols)
        
        # Stream data from buffer
        last_processed = datetime.utcnow()
        
        while True:
            try:
                batch = await self.data_buffer.get_batch(50)
                
                for item in batch:
                    if item['timestamp'] > last_processed:
                        data = item['data']
                        if data.get('symbol') in symbols:
                            yield {
                                'type': item['type'],
                                'data': data,
                                'timestamp': item['timestamp']
                            }
                
                if batch:
                    last_processed = max(item['timestamp'] for item in batch)
                
                await asyncio.sleep(0.1)  # 100ms delay
                
            except Exception as e:
                logger.error(f"Error in data stream: {e}")
                await asyncio.sleep(1)


# Global instance for use throughout the application
realtime_data_manager = RealTimeDataManager()