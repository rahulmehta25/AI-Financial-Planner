"""
WebSocket Server for Real-time Market Data

WebSocket server that streams real-time market data to connected clients.
"""

import asyncio
import json
import logging
from typing import Set, Dict, List, Optional, Any
from datetime import datetime
import websockets
from websockets.server import WebSocketServerProtocol
from websockets.exceptions import ConnectionClosed

from ..models import MarketDataPoint, WebSocketMessage
from ..config import config


class WebSocketServer:
    """WebSocket server for real-time market data streaming"""
    
    def __init__(self):
        self.clients: Set[WebSocketServerProtocol] = set()
        self.client_subscriptions: Dict[WebSocketServerProtocol, Set[str]] = {}
        self.symbol_subscribers: Dict[str, Set[WebSocketServerProtocol]] = {}
        self.logger = logging.getLogger("market_data.websocket")
        self.server = None
        self._running = False
    
    async def start_server(self, host: str = None, port: int = None):
        """Start the WebSocket server"""
        host = host or config.websocket_host
        port = port or config.websocket_port
        
        self.logger.info(f"Starting WebSocket server on {host}:{port}")
        
        try:
            self.server = await websockets.serve(
                self.handle_client,
                host,
                port,
                ping_interval=20,
                ping_timeout=10,
                close_timeout=10,
                max_size=1024 * 1024,  # 1MB max message size
                max_queue=100
            )
            self._running = True
            self.logger.info(f"WebSocket server started on {host}:{port}")
            
            # Keep the server running
            await self.server.wait_closed()
            
        except Exception as e:
            self.logger.error(f"Failed to start WebSocket server: {e}")
            raise
    
    async def stop_server(self):
        """Stop the WebSocket server"""
        if self.server:
            self.logger.info("Stopping WebSocket server")
            self._running = False
            
            # Close all client connections
            if self.clients:
                await asyncio.gather(
                    *[client.close() for client in self.clients.copy()],
                    return_exceptions=True
                )
            
            self.server.close()
            await self.server.wait_closed()
            self.logger.info("WebSocket server stopped")
    
    async def handle_client(self, websocket: WebSocketServerProtocol, path: str):
        """Handle a new client connection"""
        client_addr = websocket.remote_address
        self.logger.info(f"New client connected: {client_addr}")
        
        # Add client to the set
        self.clients.add(websocket)
        self.client_subscriptions[websocket] = set()
        
        try:
            # Send welcome message
            welcome_msg = WebSocketMessage(
                type="connection_established",
                data={"message": "Connected to market data stream", "server_time": datetime.utcnow().isoformat()}
            )
            await self.send_to_client(websocket, welcome_msg)
            
            # Handle client messages
            async for message in websocket:
                try:
                    await self.handle_message(websocket, message)
                except Exception as e:
                    self.logger.error(f"Error handling message from {client_addr}: {e}")
                    error_msg = WebSocketMessage(
                        type="error",
                        data={"error": "Invalid message format"}
                    )
                    await self.send_to_client(websocket, error_msg)
        
        except ConnectionClosed:
            self.logger.info(f"Client disconnected: {client_addr}")
        except Exception as e:
            self.logger.error(f"Error handling client {client_addr}: {e}")
        finally:
            await self.remove_client(websocket)
    
    async def handle_message(self, websocket: WebSocketServerProtocol, message: str):
        """Handle incoming message from client"""
        try:
            data = json.loads(message)
            msg_type = data.get('type')
            
            if msg_type == 'subscribe':
                symbols = data.get('symbols', [])
                await self.subscribe_client(websocket, symbols)
                
            elif msg_type == 'unsubscribe':
                symbols = data.get('symbols', [])
                await self.unsubscribe_client(websocket, symbols)
                
            elif msg_type == 'get_subscriptions':
                await self.send_subscriptions(websocket)
                
            elif msg_type == 'ping':
                pong_msg = WebSocketMessage(
                    type="pong",
                    data={"timestamp": datetime.utcnow().isoformat()}
                )
                await self.send_to_client(websocket, pong_msg)
                
            else:
                self.logger.warning(f"Unknown message type: {msg_type}")
                error_msg = WebSocketMessage(
                    type="error",
                    data={"error": f"Unknown message type: {msg_type}"}
                )
                await self.send_to_client(websocket, error_msg)
        
        except json.JSONDecodeError:
            self.logger.error("Invalid JSON message received")
            error_msg = WebSocketMessage(
                type="error",
                data={"error": "Invalid JSON format"}
            )
            await self.send_to_client(websocket, error_msg)
    
    async def subscribe_client(self, websocket: WebSocketServerProtocol, symbols: List[str]):
        """Subscribe client to symbols"""
        if not symbols:
            return
        
        # Normalize symbols
        symbols = [symbol.upper().strip() for symbol in symbols]
        
        # Add to client subscriptions
        client_subs = self.client_subscriptions.get(websocket, set())
        new_symbols = []
        
        for symbol in symbols:
            if symbol not in client_subs:
                client_subs.add(symbol)
                new_symbols.append(symbol)
                
                # Add to symbol subscribers
                if symbol not in self.symbol_subscribers:
                    self.symbol_subscribers[symbol] = set()
                self.symbol_subscribers[symbol].add(websocket)
        
        if new_symbols:
            self.logger.info(f"Client {websocket.remote_address} subscribed to: {new_symbols}")
            
            # Send confirmation
            confirmation_msg = WebSocketMessage(
                type="subscription_confirmed",
                data={
                    "symbols": new_symbols,
                    "total_subscriptions": len(client_subs)
                }
            )
            await self.send_to_client(websocket, confirmation_msg)
    
    async def unsubscribe_client(self, websocket: WebSocketServerProtocol, symbols: List[str]):
        """Unsubscribe client from symbols"""
        if not symbols:
            return
        
        # Normalize symbols
        symbols = [symbol.upper().strip() for symbol in symbols]
        
        client_subs = self.client_subscriptions.get(websocket, set())
        removed_symbols = []
        
        for symbol in symbols:
            if symbol in client_subs:
                client_subs.remove(symbol)
                removed_symbols.append(symbol)
                
                # Remove from symbol subscribers
                if symbol in self.symbol_subscribers:
                    self.symbol_subscribers[symbol].discard(websocket)
                    
                    # Clean up empty symbol entries
                    if not self.symbol_subscribers[symbol]:
                        del self.symbol_subscribers[symbol]
        
        if removed_symbols:
            self.logger.info(f"Client {websocket.remote_address} unsubscribed from: {removed_symbols}")
            
            # Send confirmation
            confirmation_msg = WebSocketMessage(
                type="unsubscription_confirmed",
                data={
                    "symbols": removed_symbols,
                    "total_subscriptions": len(client_subs)
                }
            )
            await self.send_to_client(websocket, confirmation_msg)
    
    async def send_subscriptions(self, websocket: WebSocketServerProtocol):
        """Send current subscriptions to client"""
        client_subs = self.client_subscriptions.get(websocket, set())
        
        subscriptions_msg = WebSocketMessage(
            type="current_subscriptions",
            data={
                "symbols": list(client_subs),
                "count": len(client_subs)
            }
        )
        await self.send_to_client(websocket, subscriptions_msg)
    
    async def remove_client(self, websocket: WebSocketServerProtocol):
        """Remove client and clean up subscriptions"""
        if websocket in self.clients:
            self.clients.remove(websocket)
        
        # Remove from all symbol subscriptions
        client_subs = self.client_subscriptions.get(websocket, set())
        for symbol in client_subs:
            if symbol in self.symbol_subscribers:
                self.symbol_subscribers[symbol].discard(websocket)
                if not self.symbol_subscribers[symbol]:
                    del self.symbol_subscribers[symbol]
        
        # Remove client subscription record
        if websocket in self.client_subscriptions:
            del self.client_subscriptions[websocket]
        
        self.logger.info(f"Client {websocket.remote_address} removed and cleaned up")
    
    async def broadcast_market_data(self, market_data: MarketDataPoint):
        """Broadcast market data to subscribed clients"""
        symbol = market_data.symbol
        
        if symbol not in self.symbol_subscribers:
            return
        
        subscribers = self.symbol_subscribers[symbol].copy()
        if not subscribers:
            return
        
        # Create message
        message = WebSocketMessage(
            type="market_data",
            symbol=symbol,
            data=market_data
        )
        
        # Send to all subscribers
        disconnected_clients = []
        
        for client in subscribers:
            try:
                await self.send_to_client(client, message)
            except ConnectionClosed:
                disconnected_clients.append(client)
            except Exception as e:
                self.logger.error(f"Error sending data to client {client.remote_address}: {e}")
                disconnected_clients.append(client)
        
        # Clean up disconnected clients
        for client in disconnected_clients:
            await self.remove_client(client)
    
    async def broadcast_to_all(self, message: WebSocketMessage):
        """Broadcast message to all connected clients"""
        if not self.clients:
            return
        
        disconnected_clients = []
        
        for client in self.clients.copy():
            try:
                await self.send_to_client(client, message)
            except ConnectionClosed:
                disconnected_clients.append(client)
            except Exception as e:
                self.logger.error(f"Error sending broadcast to client {client.remote_address}: {e}")
                disconnected_clients.append(client)
        
        # Clean up disconnected clients
        for client in disconnected_clients:
            await self.remove_client(client)
    
    async def send_to_client(self, websocket: WebSocketServerProtocol, message: WebSocketMessage):
        """Send message to a specific client"""
        try:
            message_json = message.json()
            await websocket.send(message_json)
        except Exception as e:
            self.logger.error(f"Failed to send message to client: {e}")
            raise
    
    def get_stats(self) -> Dict[str, Any]:
        """Get server statistics"""
        return {
            "connected_clients": len(self.clients),
            "total_subscriptions": sum(len(subs) for subs in self.client_subscriptions.values()),
            "unique_symbols": len(self.symbol_subscribers),
            "symbols_with_subscribers": list(self.symbol_subscribers.keys()),
            "running": self._running
        }
    
    def get_client_info(self) -> List[Dict[str, Any]]:
        """Get information about connected clients"""
        client_info = []
        
        for client in self.clients:
            subscriptions = self.client_subscriptions.get(client, set())
            client_info.append({
                "address": str(client.remote_address),
                "subscriptions": list(subscriptions),
                "subscription_count": len(subscriptions)
            })
        
        return client_info