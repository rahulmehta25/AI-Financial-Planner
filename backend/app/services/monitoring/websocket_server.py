"""
WebSocket Server for Real-Time Updates
Manages client connections and broadcasts real-time data
"""

import asyncio
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, Set, List, Optional, Any
from dataclasses import dataclass, field
import websockets
from websockets.server import WebSocketServerProtocol
import jwt
from collections import defaultdict

from app.core.config import Config
from app.services.base.logging_service import LoggingService
from app.services.market_data.aggregator import MarketDataAggregator

logger = LoggingService(__name__)


@dataclass
class ClientConnection:
    """Represents a connected client"""
    id: str
    user_id: str
    websocket: WebSocketServerProtocol
    subscriptions: Set[str] = field(default_factory=set)
    connected_at: datetime = field(default_factory=datetime.utcnow)
    last_ping: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BroadcastMessage:
    """Message to broadcast to clients"""
    type: str
    channel: str
    data: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.utcnow)
    target_users: Optional[List[str]] = None


class WebSocketServer:
    """Main WebSocket server for real-time updates"""
    
    def __init__(self, host: str = "0.0.0.0", port: int = 8765):
        self.host = host
        self.port = port
        self.connections: Dict[str, ClientConnection] = {}
        self.user_connections: Dict[str, Set[str]] = defaultdict(set)
        self.channel_subscribers: Dict[str, Set[str]] = defaultdict(set)
        self.rate_limiter = RateLimiter()
        self.market_data = MarketDataAggregator()
        self.broadcast_queue: asyncio.Queue = asyncio.Queue()
        self.running = False
        logger.info(f"WebSocket server initialized on {host}:{port}")
    
    async def start(self):
        """Start the WebSocket server"""
        self.running = True
        
        # Start background tasks
        asyncio.create_task(self._broadcast_worker())
        asyncio.create_task(self._heartbeat_worker())
        asyncio.create_task(self._market_data_worker())
        
        # Start WebSocket server
        async with websockets.serve(
            self.handle_client,
            self.host,
            self.port,
            ping_interval=20,
            ping_timeout=10
        ):
            logger.info(f"WebSocket server started on ws://{self.host}:{self.port}")
            await asyncio.Future()  # run forever
    
    async def handle_client(self, websocket: WebSocketServerProtocol, path: str):
        """Handle new client connection"""
        connection_id = str(uuid.uuid4())
        client = None
        
        try:
            # Authenticate client
            auth_msg = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            auth_data = json.loads(auth_msg)
            
            user_id = await self._authenticate(auth_data.get('token'))
            if not user_id:
                await websocket.send(json.dumps({
                    'type': 'error',
                    'message': 'Authentication failed'
                }))
                return
            
            # Create client connection
            client = ClientConnection(
                id=connection_id,
                user_id=user_id,
                websocket=websocket
            )
            
            # Register connection
            self.connections[connection_id] = client
            self.user_connections[user_id].add(connection_id)
            
            # Send welcome message
            await websocket.send(json.dumps({
                'type': 'connected',
                'connection_id': connection_id,
                'timestamp': datetime.utcnow().isoformat()
            }))
            
            logger.info(f"Client {connection_id} (user: {user_id}) connected")
            
            # Handle messages
            await self._handle_messages(client)
            
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Client {connection_id} disconnected")
        except asyncio.TimeoutError:
            logger.warning(f"Client {connection_id} authentication timeout")
        except Exception as e:
            logger.error(f"Error handling client {connection_id}: {e}")
        finally:
            # Clean up connection
            if client:
                await self._disconnect_client(client)
    
    async def _handle_messages(self, client: ClientConnection):
        """Handle messages from a connected client"""
        async for message in client.websocket:
            try:
                # Rate limiting
                if not await self.rate_limiter.check(client.user_id):
                    await client.websocket.send(json.dumps({
                        'type': 'error',
                        'message': 'Rate limit exceeded'
                    }))
                    continue
                
                data = json.loads(message)
                message_type = data.get('type')
                
                if message_type == 'subscribe':
                    await self._handle_subscribe(client, data)
                elif message_type == 'unsubscribe':
                    await self._handle_unsubscribe(client, data)
                elif message_type == 'ping':
                    await self._handle_ping(client)
                elif message_type == 'request':
                    await self._handle_request(client, data)
                else:
                    await client.websocket.send(json.dumps({
                        'type': 'error',
                        'message': f'Unknown message type: {message_type}'
                    }))
                
            except json.JSONDecodeError:
                await client.websocket.send(json.dumps({
                    'type': 'error',
                    'message': 'Invalid JSON'
                }))
            except Exception as e:
                logger.error(f"Error handling message from {client.id}: {e}")
                await client.websocket.send(json.dumps({
                    'type': 'error',
                    'message': 'Internal server error'
                }))
    
    async def _handle_subscribe(self, client: ClientConnection, data: Dict[str, Any]):
        """Handle subscription request"""
        channels = data.get('channels', [])
        
        for channel in channels:
            if self._validate_channel(channel, client.user_id):
                client.subscriptions.add(channel)
                self.channel_subscribers[channel].add(client.id)
                
                # Send initial data for channel
                initial_data = await self._get_initial_data(channel, client.user_id)
                if initial_data:
                    await client.websocket.send(json.dumps({
                        'type': 'data',
                        'channel': channel,
                        'data': initial_data,
                        'timestamp': datetime.utcnow().isoformat()
                    }))
        
        await client.websocket.send(json.dumps({
            'type': 'subscribed',
            'channels': list(client.subscriptions),
            'timestamp': datetime.utcnow().isoformat()
        }))
    
    async def _handle_unsubscribe(self, client: ClientConnection, data: Dict[str, Any]):
        """Handle unsubscribe request"""
        channels = data.get('channels', [])
        
        for channel in channels:
            if channel in client.subscriptions:
                client.subscriptions.remove(channel)
                self.channel_subscribers[channel].discard(client.id)
        
        await client.websocket.send(json.dumps({
            'type': 'unsubscribed',
            'channels': channels,
            'timestamp': datetime.utcnow().isoformat()
        }))
    
    async def _handle_ping(self, client: ClientConnection):
        """Handle ping message"""
        client.last_ping = datetime.utcnow()
        await client.websocket.send(json.dumps({
            'type': 'pong',
            'timestamp': datetime.utcnow().isoformat()
        }))
    
    async def _handle_request(self, client: ClientConnection, data: Dict[str, Any]):
        """Handle data request"""
        request_type = data.get('request')
        
        if request_type == 'portfolio':
            await self._send_portfolio_update(client)
        elif request_type == 'alerts':
            await self._send_recent_alerts(client)
        elif request_type == 'market':
            await self._send_market_snapshot(client)
        else:
            await client.websocket.send(json.dumps({
                'type': 'error',
                'message': f'Unknown request type: {request_type}'
            }))
    
    async def _authenticate(self, token: str) -> Optional[str]:
        """Authenticate client token"""
        try:
            payload = jwt.decode(
                token,
                Config.JWT_SECRET_KEY,
                algorithms=['HS256']
            )
            return payload.get('user_id')
        except jwt.InvalidTokenError:
            return None
    
    def _validate_channel(self, channel: str, user_id: str) -> bool:
        """Validate if user can subscribe to channel"""
        # Channel format: type:resource
        # e.g., portfolio:123, market:SPY, alerts:all
        
        parts = channel.split(':')
        if len(parts) != 2:
            return False
        
        channel_type, resource = parts
        
        # Validate based on channel type
        if channel_type == 'portfolio':
            # Check if user owns the portfolio
            return True  # Simplified - would check ownership
        elif channel_type == 'market':
            # Market data is available to all
            return True
        elif channel_type == 'alerts':
            # User can only subscribe to their own alerts
            return resource == 'all' or resource == user_id
        elif channel_type == 'news':
            # News is available to all
            return True
        
        return False
    
    async def _get_initial_data(self, channel: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get initial data for a channel"""
        parts = channel.split(':')
        if len(parts) != 2:
            return None
        
        channel_type, resource = parts
        
        if channel_type == 'portfolio':
            # Return current portfolio state
            return {
                'total_value': 100000,  # Would fetch actual data
                'daily_change': 1250,
                'daily_change_pct': 1.25
            }
        elif channel_type == 'market':
            # Return current market data
            return await self.market_data.get_quote(resource)
        
        return None
    
    async def _disconnect_client(self, client: ClientConnection):
        """Disconnect and clean up client"""
        if client.id in self.connections:
            del self.connections[client.id]
        
        self.user_connections[client.user_id].discard(client.id)
        if not self.user_connections[client.user_id]:
            del self.user_connections[client.user_id]
        
        for channel in client.subscriptions:
            self.channel_subscribers[channel].discard(client.id)
        
        logger.info(f"Client {client.id} cleaned up")
    
    async def broadcast(self, message: BroadcastMessage):
        """Queue message for broadcast"""
        await self.broadcast_queue.put(message)
    
    async def _broadcast_worker(self):
        """Worker to process broadcast queue"""
        while self.running:
            try:
                message = await self.broadcast_queue.get()
                await self._process_broadcast(message)
            except Exception as e:
                logger.error(f"Broadcast error: {e}")
    
    async def _process_broadcast(self, message: BroadcastMessage):
        """Process and send broadcast message"""
        # Determine target connections
        target_connections = set()
        
        if message.target_users:
            # Send to specific users
            for user_id in message.target_users:
                target_connections.update(self.user_connections.get(user_id, set()))
        else:
            # Send to channel subscribers
            target_connections = self.channel_subscribers.get(message.channel, set())
        
        # Send to all target connections
        data = json.dumps({
            'type': message.type,
            'channel': message.channel,
            'data': message.data,
            'timestamp': message.timestamp.isoformat()
        })
        
        disconnected = []
        for conn_id in target_connections:
            if conn_id in self.connections:
                try:
                    await self.connections[conn_id].websocket.send(data)
                except websockets.exceptions.ConnectionClosed:
                    disconnected.append(conn_id)
        
        # Clean up disconnected clients
        for conn_id in disconnected:
            if conn_id in self.connections:
                await self._disconnect_client(self.connections[conn_id])
    
    async def _heartbeat_worker(self):
        """Send periodic heartbeats and clean up stale connections"""
        while self.running:
            await asyncio.sleep(30)
            
            now = datetime.utcnow()
            disconnected = []
            
            for conn_id, client in list(self.connections.items()):
                # Check for stale connections
                if now - client.last_ping > timedelta(minutes=2):
                    disconnected.append(client)
                else:
                    # Send heartbeat
                    try:
                        await client.websocket.send(json.dumps({
                            'type': 'heartbeat',
                            'timestamp': now.isoformat()
                        }))
                    except websockets.exceptions.ConnectionClosed:
                        disconnected.append(client)
            
            # Clean up disconnected clients
            for client in disconnected:
                await self._disconnect_client(client)
    
    async def _market_data_worker(self):
        """Stream market data to subscribers"""
        while self.running:
            try:
                # Get market data updates
                market_updates = await self.market_data.get_realtime_updates()
                
                for symbol, data in market_updates.items():
                    channel = f"market:{symbol}"
                    if self.channel_subscribers[channel]:
                        await self.broadcast(BroadcastMessage(
                            type='market_update',
                            channel=channel,
                            data=data
                        ))
                
                await asyncio.sleep(1)  # Update frequency
                
            except Exception as e:
                logger.error(f"Market data worker error: {e}")
                await asyncio.sleep(5)
    
    async def send_portfolio_update(self, user_id: str, portfolio_data: Dict[str, Any]):
        """Send portfolio update to user"""
        await self.broadcast(BroadcastMessage(
            type='portfolio_update',
            channel=f"portfolio:{user_id}",
            data=portfolio_data,
            target_users=[user_id]
        ))
    
    async def send_alert(self, user_id: str, alert_data: Dict[str, Any]):
        """Send alert to user"""
        await self.broadcast(BroadcastMessage(
            type='alert',
            channel=f"alerts:{user_id}",
            data=alert_data,
            target_users=[user_id]
        ))
    
    async def send_market_event(self, event_data: Dict[str, Any]):
        """Send market event to all subscribers"""
        await self.broadcast(BroadcastMessage(
            type='market_event',
            channel='market:events',
            data=event_data
        ))
    
    async def _send_portfolio_update(self, client: ClientConnection):
        """Send current portfolio state to client"""
        # Would fetch actual portfolio data
        portfolio_data = {
            'total_value': 125000,
            'daily_change': 2500,
            'daily_change_pct': 2.0,
            'positions': [
                {'symbol': 'AAPL', 'value': 25000, 'change': 500},
                {'symbol': 'GOOGL', 'value': 20000, 'change': 300}
            ]
        }
        
        await client.websocket.send(json.dumps({
            'type': 'portfolio',
            'data': portfolio_data,
            'timestamp': datetime.utcnow().isoformat()
        }))
    
    async def _send_recent_alerts(self, client: ClientConnection):
        """Send recent alerts to client"""
        # Would fetch actual alerts
        alerts = [
            {
                'id': 'alert_1',
                'type': 'rebalancing',
                'title': 'Portfolio Rebalancing Needed',
                'message': 'Your portfolio has drifted 5% from target',
                'timestamp': datetime.utcnow().isoformat()
            }
        ]
        
        await client.websocket.send(json.dumps({
            'type': 'alerts',
            'data': alerts,
            'timestamp': datetime.utcnow().isoformat()
        }))
    
    async def _send_market_snapshot(self, client: ClientConnection):
        """Send market snapshot to client"""
        snapshot = await self.market_data.get_market_snapshot()
        
        await client.websocket.send(json.dumps({
            'type': 'market_snapshot',
            'data': snapshot,
            'timestamp': datetime.utcnow().isoformat()
        }))


class RateLimiter:
    """Rate limiter for WebSocket connections"""
    
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, List[datetime]] = defaultdict(list)
    
    async def check(self, user_id: str) -> bool:
        """Check if user is within rate limits"""
        now = datetime.utcnow()
        window_start = now - timedelta(seconds=self.window_seconds)
        
        # Clean old requests
        self.requests[user_id] = [
            req_time for req_time in self.requests[user_id]
            if req_time > window_start
        ]
        
        # Check limit
        if len(self.requests[user_id]) >= self.max_requests:
            return False
        
        # Add request
        self.requests[user_id].append(now)
        return True


class WebSocketManager:
    """Manager for WebSocket server lifecycle"""
    
    def __init__(self):
        self.server: Optional[WebSocketServer] = None
        self.server_task: Optional[asyncio.Task] = None
    
    async def start_server(self, host: str = "0.0.0.0", port: int = 8765):
        """Start the WebSocket server"""
        self.server = WebSocketServer(host, port)
        self.server_task = asyncio.create_task(self.server.start())
        logger.info("WebSocket server started")
    
    async def stop_server(self):
        """Stop the WebSocket server"""
        if self.server:
            self.server.running = False
            if self.server_task:
                self.server_task.cancel()
                try:
                    await self.server_task
                except asyncio.CancelledError:
                    pass
        logger.info("WebSocket server stopped")
    
    async def broadcast_update(self, message: BroadcastMessage):
        """Broadcast update to clients"""
        if self.server:
            await self.server.broadcast(message)