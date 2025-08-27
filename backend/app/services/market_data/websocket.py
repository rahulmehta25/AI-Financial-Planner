"""
WebSocket Manager for Real-Time Market Data

Manages real-time WebSocket connections from multiple providers with
intelligent routing, connection pooling, and data distribution.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Callable, Union
from collections import defaultdict, deque
from enum import Enum
import weakref

from .providers.polygon_io import PolygonIOProvider
from .providers.databento import DatabentoProvider
from .models import DataProvider
from .config import config


class WebSocketEventType(Enum):
    """WebSocket event types"""
    TRADE = "trade"
    QUOTE = "quote"
    AGGREGATE = "aggregate"
    ORDER_BOOK = "order_book"
    STATUS = "status"
    ERROR = "error"


class SubscriptionStatus(Enum):
    """Subscription status"""
    PENDING = "pending"
    ACTIVE = "active"
    FAILED = "failed"
    CANCELLED = "cancelled"


class WebSocketConnection:
    """Represents a WebSocket connection to a provider"""
    
    def __init__(self, provider: DataProvider, provider_instance):
        self.provider = provider
        self.provider_instance = provider_instance
        self.connected = False
        self.authenticated = False
        self.subscriptions = set()
        self.last_heartbeat = None
        self.connection_time = None
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 10
        
        # Performance metrics
        self.messages_received = 0
        self.bytes_received = 0
        self.last_message_time = None
        self.latency_samples = deque(maxlen=100)


class WebSocketSubscription:
    """Represents a subscription to real-time data"""
    
    def __init__(self, symbols: List[str], event_types: List[WebSocketEventType], handler: Callable):
        self.id = f"sub_{hash((tuple(symbols), tuple(event_types), id(handler)))}"
        self.symbols = set(symbols)
        self.event_types = set(event_types)
        self.handler = handler
        self.created_at = datetime.utcnow()
        self.status = SubscriptionStatus.PENDING
        self.providers = set()  # Which providers are handling this subscription
        
        # Performance tracking
        self.messages_received = 0
        self.last_message_time = None
        self.errors = []


class WebSocketManager:
    """Comprehensive WebSocket manager with multi-provider support"""
    
    def __init__(self, aggregator):
        self.aggregator = aggregator
        self.logger = logging.getLogger("market_data.websocket")
        
        # WebSocket connections
        self.connections: Dict[DataProvider, WebSocketConnection] = {}
        
        # Active subscriptions
        self.subscriptions: Dict[str, WebSocketSubscription] = {}
        
        # Symbol to subscription mapping
        self.symbol_subscriptions: Dict[str, Set[str]] = defaultdict(set)
        
        # Event handlers
        self.global_handlers: Dict[WebSocketEventType, List[Callable]] = defaultdict(list)
        
        # Connection health monitoring
        self.health_check_interval = 30  # seconds
        self.heartbeat_timeout = 60     # seconds
        
        # Rate limiting for subscriptions
        self.subscription_rate_limiter = defaultdict(lambda: deque(maxlen=100))
        self.max_subscriptions_per_minute = 60
        
        # Data quality monitoring
        self.data_quality_metrics = defaultdict(lambda: {
            'messages_per_second': deque(maxlen=60),
            'error_rate': deque(maxlen=100),
            'latency': deque(maxlen=100)
        })
        
        # Background tasks
        self._health_monitor_task = None
        self._cleanup_task = None
        self._metrics_task = None
        
        self._initialized = False
    
    async def initialize(self):
        """Initialize the WebSocket manager"""
        if self._initialized:
            return
        
        self.logger.info("Initializing WebSocket Manager")
        
        try:
            # Initialize connections to available providers
            await self._initialize_connections()
            
            # Start background tasks
            self._health_monitor_task = asyncio.create_task(self._health_monitor_loop())
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
            self._metrics_task = asyncio.create_task(self._metrics_loop())
            
            self._initialized = True
            self.logger.info("WebSocket Manager initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize WebSocket Manager: {e}")
            raise
    
    async def _initialize_connections(self):
        """Initialize WebSocket connections to available providers"""
        # Priority order for WebSocket providers
        websocket_providers = [
            DataProvider.POLYGON_IO,
            DataProvider.DATABENTO,
        ]
        
        for provider_type in websocket_providers:
            if provider_type in self.aggregator.providers:
                try:
                    provider_instance = self.aggregator.providers[provider_type]
                    
                    # Check if provider supports WebSocket
                    if hasattr(provider_instance, 'connect_websocket'):
                        connection = WebSocketConnection(provider_type, provider_instance)
                        
                        # Attempt connection
                        if await provider_instance.connect_websocket():
                            connection.connected = True
                            connection.connection_time = datetime.utcnow()
                            self.connections[provider_type] = connection
                            
                            self.logger.info(f"WebSocket connected to {provider_type}")
                        else:
                            self.logger.warning(f"Failed to connect WebSocket to {provider_type}")
                    
                except Exception as e:
                    self.logger.error(f"Error initializing WebSocket for {provider_type}: {e}")
    
    async def subscribe(
        self,
        symbols: Union[str, List[str]],
        event_types: Union[WebSocketEventType, List[WebSocketEventType]] = None,
        handler: Callable = None
    ) -> str:
        """Subscribe to real-time data for symbols"""
        # Normalize inputs
        if isinstance(symbols, str):
            symbols = [symbols]
        
        if event_types is None:
            event_types = [WebSocketEventType.TRADE, WebSocketEventType.QUOTE]
        elif isinstance(event_types, WebSocketEventType):
            event_types = [event_types]
        
        # Rate limiting check
        if not await self._check_subscription_rate_limit():
            raise RuntimeError("Subscription rate limit exceeded")
        
        # Create subscription
        subscription = WebSocketSubscription(symbols, event_types, handler)
        self.subscriptions[subscription.id] = subscription
        
        # Map symbols to subscription
        for symbol in symbols:
            self.symbol_subscriptions[symbol].add(subscription.id)
        
        # Subscribe to available providers
        await self._execute_subscription(subscription)
        
        self.logger.info(f"Created subscription {subscription.id} for {len(symbols)} symbols")
        return subscription.id
    
    async def _execute_subscription(self, subscription: WebSocketSubscription):
        """Execute subscription on available providers"""
        successful_providers = 0
        
        for provider_type, connection in self.connections.items():
            if not connection.connected:
                continue
            
            try:
                provider = connection.provider_instance
                
                # Subscribe based on event types
                if WebSocketEventType.TRADE in subscription.event_types:
                    if hasattr(provider, 'subscribe_to_trades'):
                        await provider.subscribe_to_trades(list(subscription.symbols))
                        successful_providers += 1
                
                if WebSocketEventType.QUOTE in subscription.event_types:
                    if hasattr(provider, 'subscribe_to_quotes'):
                        await provider.subscribe_to_quotes(list(subscription.symbols))
                        successful_providers += 1
                
                # Register handler
                if subscription.handler:
                    for symbol in subscription.symbols:
                        provider.register_handler(symbol, self._create_handler_wrapper(subscription))
                
                subscription.providers.add(provider_type)
                connection.subscriptions.update(subscription.symbols)
                
            except Exception as e:
                self.logger.error(f"Failed to subscribe to {provider_type}: {e}")
                subscription.errors.append(f"{provider_type}: {str(e)}")
        
        if successful_providers > 0:
            subscription.status = SubscriptionStatus.ACTIVE
        else:
            subscription.status = SubscriptionStatus.FAILED
            self.logger.error(f"Subscription {subscription.id} failed on all providers")
    
    def _create_handler_wrapper(self, subscription: WebSocketSubscription) -> Callable:
        """Create a handler wrapper that tracks metrics and calls user handler"""
        async def handler_wrapper(data: Dict[str, Any]):
            try:
                # Track metrics
                subscription.messages_received += 1
                subscription.last_message_time = datetime.utcnow()
                
                # Update provider metrics
                provider_type = data.get('provider')
                if provider_type:
                    metrics = self.data_quality_metrics[provider_type]
                    metrics['messages_per_second'].append(datetime.utcnow())
                
                # Call user handler if provided
                if subscription.handler:
                    await subscription.handler(data)
                
                # Call global handlers
                event_type = WebSocketEventType(data.get('type', 'unknown'))
                for handler in self.global_handlers[event_type]:
                    try:
                        await handler(data)
                    except Exception as e:
                        self.logger.error(f"Global handler error: {e}")
                
            except Exception as e:
                self.logger.error(f"Handler wrapper error: {e}")
                subscription.errors.append(str(e))
        
        return handler_wrapper
    
    async def unsubscribe(self, subscription_id: str) -> bool:
        """Unsubscribe from real-time data"""
        if subscription_id not in self.subscriptions:
            return False
        
        subscription = self.subscriptions[subscription_id]
        subscription.status = SubscriptionStatus.CANCELLED
        
        # Remove from symbol mappings
        for symbol in subscription.symbols:
            self.symbol_subscriptions[symbol].discard(subscription_id)
            if not self.symbol_subscriptions[symbol]:
                del self.symbol_subscriptions[symbol]
        
        # Unsubscribe from providers if no other subscriptions exist for these symbols
        for provider_type in subscription.providers:
            if provider_type in self.connections:
                connection = self.connections[provider_type]
                
                # Check if any other subscriptions need these symbols
                symbols_to_unsubscribe = set()
                for symbol in subscription.symbols:
                    if symbol not in self.symbol_subscriptions:
                        symbols_to_unsubscribe.add(symbol)
                
                if symbols_to_unsubscribe:
                    # TODO: Implement provider-specific unsubscribe logic
                    connection.subscriptions -= symbols_to_unsubscribe
        
        # Remove subscription
        del self.subscriptions[subscription_id]
        
        self.logger.info(f"Unsubscribed {subscription_id}")
        return True
    
    def add_global_handler(self, event_type: WebSocketEventType, handler: Callable):
        """Add a global handler for all events of a specific type"""
        self.global_handlers[event_type].append(handler)
        self.logger.info(f"Added global handler for {event_type}")
    
    def remove_global_handler(self, event_type: WebSocketEventType, handler: Callable):
        """Remove a global handler"""
        if handler in self.global_handlers[event_type]:
            self.global_handlers[event_type].remove(handler)
    
    async def _check_subscription_rate_limit(self) -> bool:
        """Check if subscription rate limit is exceeded"""
        now = datetime.utcnow()
        minute_ago = now - timedelta(minutes=1)
        
        # Clean old timestamps
        current_requests = self.subscription_rate_limiter[now.minute]
        current_requests = deque([ts for ts in current_requests if ts > minute_ago], maxlen=100)
        self.subscription_rate_limiter[now.minute] = current_requests
        
        if len(current_requests) >= self.max_subscriptions_per_minute:
            return False
        
        current_requests.append(now)
        return True
    
    # Background monitoring tasks
    async def _health_monitor_loop(self):
        """Monitor WebSocket connection health"""
        while True:
            try:
                await asyncio.sleep(self.health_check_interval)
                
                for provider_type, connection in self.connections.items():
                    try:
                        # Check connection health
                        if connection.connected:
                            # Check for recent activity
                            if (connection.last_heartbeat and 
                                (datetime.utcnow() - connection.last_heartbeat).total_seconds() > self.heartbeat_timeout):
                                
                                self.logger.warning(f"{provider_type} WebSocket appears stale")
                                await self._reconnect_provider(provider_type)
                        else:
                            # Attempt reconnection
                            await self._reconnect_provider(provider_type)
                    
                    except Exception as e:
                        self.logger.error(f"Health check error for {provider_type}: {e}")
            
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Health monitor loop error: {e}")
    
    async def _reconnect_provider(self, provider_type: DataProvider):
        """Reconnect to a specific provider"""
        if provider_type not in self.connections:
            return
        
        connection = self.connections[provider_type]
        
        if connection.reconnect_attempts >= connection.max_reconnect_attempts:
            self.logger.error(f"Max reconnection attempts reached for {provider_type}")
            return
        
        connection.reconnect_attempts += 1
        
        try:
            self.logger.info(f"Attempting to reconnect to {provider_type}")
            
            # Disconnect existing connection
            if hasattr(connection.provider_instance, 'disconnect_websocket'):
                await connection.provider_instance.disconnect_websocket()
            
            # Attempt new connection
            if await connection.provider_instance.connect_websocket():
                connection.connected = True
                connection.connection_time = datetime.utcnow()
                connection.reconnect_attempts = 0
                
                # Resubscribe to active subscriptions
                await self._resubscribe_after_reconnect(provider_type)
                
                self.logger.info(f"Successfully reconnected to {provider_type}")
            else:
                connection.connected = False
                self.logger.warning(f"Failed to reconnect to {provider_type}")
        
        except Exception as e:
            self.logger.error(f"Reconnection error for {provider_type}: {e}")
            connection.connected = False
    
    async def _resubscribe_after_reconnect(self, provider_type: DataProvider):
        """Resubscribe to all active subscriptions after reconnection"""
        connection = self.connections[provider_type]
        
        for subscription_id, subscription in self.subscriptions.items():
            if (subscription.status == SubscriptionStatus.ACTIVE and 
                provider_type in subscription.providers):
                
                try:
                    # Re-execute subscription
                    provider = connection.provider_instance
                    
                    if WebSocketEventType.TRADE in subscription.event_types:
                        if hasattr(provider, 'subscribe_to_trades'):
                            await provider.subscribe_to_trades(list(subscription.symbols))
                    
                    if WebSocketEventType.QUOTE in subscription.event_types:
                        if hasattr(provider, 'subscribe_to_quotes'):
                            await provider.subscribe_to_quotes(list(subscription.symbols))
                    
                    # Re-register handlers
                    if subscription.handler:
                        for symbol in subscription.symbols:
                            provider.register_handler(symbol, self._create_handler_wrapper(subscription))
                    
                except Exception as e:
                    self.logger.error(f"Failed to resubscribe {subscription_id} to {provider_type}: {e}")
    
    async def _cleanup_loop(self):
        """Clean up stale subscriptions and connections"""
        while True:
            try:
                await asyncio.sleep(300)  # Run every 5 minutes
                
                # Clean up failed subscriptions
                failed_subscriptions = [
                    sub_id for sub_id, sub in self.subscriptions.items()
                    if sub.status == SubscriptionStatus.FAILED
                ]
                
                for sub_id in failed_subscriptions:
                    await self.unsubscribe(sub_id)
                
                # Clean up empty symbol mappings
                empty_symbols = [
                    symbol for symbol, subs in self.symbol_subscriptions.items()
                    if not subs
                ]
                
                for symbol in empty_symbols:
                    del self.symbol_subscriptions[symbol]
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Cleanup loop error: {e}")
    
    async def _metrics_loop(self):
        """Collect and log performance metrics"""
        while True:
            try:
                await asyncio.sleep(60)  # Run every minute
                
                # Calculate metrics for each provider
                for provider_type, metrics in self.data_quality_metrics.items():
                    messages_per_second = len([
                        ts for ts in metrics['messages_per_second']
                        if (datetime.utcnow() - ts).total_seconds() <= 60
                    ])
                    
                    avg_latency = (
                        sum(metrics['latency']) / len(metrics['latency'])
                        if metrics['latency'] else 0
                    )
                    
                    error_rate = (
                        sum(metrics['error_rate']) / len(metrics['error_rate'])
                        if metrics['error_rate'] else 0
                    )
                    
                    self.logger.debug(
                        f"{provider_type} WebSocket metrics: "
                        f"msgs/sec={messages_per_second}, "
                        f"latency={avg_latency:.2f}ms, "
                        f"error_rate={error_rate:.2%}"
                    )
            
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Metrics loop error: {e}")
    
    def get_subscription_info(self, subscription_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a subscription"""
        if subscription_id not in self.subscriptions:
            return None
        
        subscription = self.subscriptions[subscription_id]
        
        return {
            "id": subscription.id,
            "symbols": list(subscription.symbols),
            "event_types": [et.value for et in subscription.event_types],
            "status": subscription.status.value,
            "providers": [p.value for p in subscription.providers],
            "created_at": subscription.created_at.isoformat(),
            "messages_received": subscription.messages_received,
            "last_message_time": subscription.last_message_time.isoformat() if subscription.last_message_time else None,
            "errors": subscription.errors
        }
    
    def get_connection_status(self) -> Dict[str, Any]:
        """Get status of all WebSocket connections"""
        status = {}
        
        for provider_type, connection in self.connections.items():
            status[provider_type.value] = {
                "connected": connection.connected,
                "authenticated": connection.authenticated,
                "connection_time": connection.connection_time.isoformat() if connection.connection_time else None,
                "subscriptions_count": len(connection.subscriptions),
                "messages_received": connection.messages_received,
                "bytes_received": connection.bytes_received,
                "last_message_time": connection.last_message_time.isoformat() if connection.last_message_time else None,
                "reconnect_attempts": connection.reconnect_attempts,
                "avg_latency": (
                    sum(connection.latency_samples) / len(connection.latency_samples)
                    if connection.latency_samples else 0
                )
            }
        
        return status
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get comprehensive system statistics"""
        return {
            "initialized": self._initialized,
            "connections": self.get_connection_status(),
            "subscriptions": {
                "total": len(self.subscriptions),
                "active": sum(1 for s in self.subscriptions.values() if s.status == SubscriptionStatus.ACTIVE),
                "pending": sum(1 for s in self.subscriptions.values() if s.status == SubscriptionStatus.PENDING),
                "failed": sum(1 for s in self.subscriptions.values() if s.status == SubscriptionStatus.FAILED)
            },
            "symbols_tracked": len(self.symbol_subscriptions),
            "global_handlers": {et.value: len(handlers) for et, handlers in self.global_handlers.items()},
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def shutdown(self):
        """Shutdown the WebSocket manager"""
        self.logger.info("Shutting down WebSocket Manager")
        
        # Cancel background tasks
        tasks = [self._health_monitor_task, self._cleanup_task, self._metrics_task]
        for task in tasks:
            if task:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
        # Close all connections
        for provider_type, connection in self.connections.items():
            try:
                if hasattr(connection.provider_instance, 'disconnect_websocket'):
                    await connection.provider_instance.disconnect_websocket()
            except Exception as e:
                self.logger.error(f"Error closing WebSocket for {provider_type}: {e}")
        
        # Clear all subscriptions
        self.subscriptions.clear()
        self.symbol_subscriptions.clear()
        self.connections.clear()
        
        self._initialized = False
        self.logger.info("WebSocket Manager shutdown complete")