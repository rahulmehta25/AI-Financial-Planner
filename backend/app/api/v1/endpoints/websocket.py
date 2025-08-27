"""
WebSocket endpoints for real-time data streaming
"""

import asyncio
import json
import logging
from typing import Dict, Set
from datetime import datetime
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.websockets import WebSocketState

from app.api.deps import get_current_user_from_token
from app.models.user import User

router = APIRouter()
logger = logging.getLogger(__name__)

# Store active WebSocket connections
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_connections: Dict[str, Set[str]] = {}
    
    async def connect(self, websocket: WebSocket, connection_id: str, user_id: str = None):
        await websocket.accept()
        self.active_connections[connection_id] = websocket
        
        if user_id:
            if user_id not in self.user_connections:
                self.user_connections[user_id] = set()
            self.user_connections[user_id].add(connection_id)
            
        logger.info(f"WebSocket connected: {connection_id}")
    
    def disconnect(self, connection_id: str, user_id: str = None):
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
            
        if user_id and user_id in self.user_connections:
            self.user_connections[user_id].discard(connection_id)
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]
                
        logger.info(f"WebSocket disconnected: {connection_id}")
    
    async def send_personal_message(self, message: str, connection_id: str):
        if connection_id in self.active_connections:
            websocket = self.active_connections[connection_id]
            if websocket.client_state == WebSocketState.CONNECTED:
                await websocket.send_text(message)
    
    async def send_user_message(self, message: str, user_id: str):
        if user_id in self.user_connections:
            connections = self.user_connections[user_id].copy()
            for connection_id in connections:
                try:
                    await self.send_personal_message(message, connection_id)
                except Exception as e:
                    logger.error(f"Error sending message to {connection_id}: {e}")
                    self.disconnect(connection_id, user_id)
    
    async def broadcast(self, message: str):
        connections_to_remove = []
        for connection_id, websocket in self.active_connections.items():
            try:
                if websocket.client_state == WebSocketState.CONNECTED:
                    await websocket.send_text(message)
                else:
                    connections_to_remove.append(connection_id)
            except Exception as e:
                logger.error(f"Error broadcasting to {connection_id}: {e}")
                connections_to_remove.append(connection_id)
        
        # Clean up disconnected connections
        for connection_id in connections_to_remove:
            if connection_id in self.active_connections:
                del self.active_connections[connection_id]

manager = ConnectionManager()


@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """Main WebSocket endpoint for real-time data"""
    connection_id = f"{user_id}_{datetime.utcnow().timestamp()}"
    
    try:
        await manager.connect(websocket, connection_id, user_id)
        
        # Send welcome message
        welcome_message = {
            "type": "connection_established",
            "data": {
                "message": f"Connected to Financial Planning System",
                "user_id": user_id,
                "connection_id": connection_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        await websocket.send_text(json.dumps(welcome_message))
        
        # Handle incoming messages
        while True:
            try:
                data = await websocket.receive_text()
                message_data = json.loads(data)
                await handle_websocket_message(websocket, connection_id, user_id, message_data)
            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                error_message = {
                    "type": "error",
                    "data": {"message": "Invalid JSON format"}
                }
                await websocket.send_text(json.dumps(error_message))
            except Exception as e:
                logger.error(f"Error handling WebSocket message: {e}")
                error_message = {
                    "type": "error", 
                    "data": {"message": "Internal server error"}
                }
                await websocket.send_text(json.dumps(error_message))
                
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
    finally:
        manager.disconnect(connection_id, user_id)


async def handle_websocket_message(websocket: WebSocket, connection_id: str, user_id: str, message_data: dict):
    """Handle incoming WebSocket messages"""
    message_type = message_data.get("type", "unknown")
    
    if message_type == "ping":
        response = {
            "type": "pong",
            "data": {"timestamp": datetime.utcnow().isoformat()}
        }
        await websocket.send_text(json.dumps(response))
        
    elif message_type == "subscribe_market_data":
        symbols = message_data.get("symbols", [])
        response = {
            "type": "subscription_confirmed",
            "data": {
                "symbols": symbols,
                "message": f"Subscribed to market data for {len(symbols)} symbols"
            }
        }
        await websocket.send_text(json.dumps(response))
        
        # Start sending mock market data
        asyncio.create_task(send_market_data_updates(connection_id, symbols))
        
    elif message_type == "subscribe_portfolio_updates":
        response = {
            "type": "subscription_confirmed", 
            "data": {
                "message": "Subscribed to portfolio updates",
                "user_id": user_id
            }
        }
        await websocket.send_text(json.dumps(response))
        
        # Start sending mock portfolio updates
        asyncio.create_task(send_portfolio_updates(connection_id, user_id))
        
    elif message_type == "get_status":
        response = {
            "type": "status",
            "data": {
                "connection_id": connection_id,
                "user_id": user_id,
                "connected_at": datetime.utcnow().isoformat(),
                "active_subscriptions": ["portfolio_updates", "market_data"]
            }
        }
        await websocket.send_text(json.dumps(response))
        
    else:
        response = {
            "type": "error",
            "data": {"message": f"Unknown message type: {message_type}"}
        }
        await websocket.send_text(json.dumps(response))


async def send_market_data_updates(connection_id: str, symbols: list):
    """Send periodic market data updates"""
    try:
        while connection_id in manager.active_connections:
            for symbol in symbols:
                # Generate mock market data
                price = 100.0 + (hash(symbol + str(datetime.utcnow().minute)) % 2000) / 100
                change = (hash(symbol + str(datetime.utcnow().second)) % 1000 - 500) / 100
                
                market_update = {
                    "type": "market_data_update",
                    "data": {
                        "symbol": symbol,
                        "price": round(price, 2),
                        "change": round(change, 2),
                        "change_percent": round((change / price) * 100, 2),
                        "timestamp": datetime.utcnow().isoformat()
                    }
                }
                
                await manager.send_personal_message(
                    json.dumps(market_update), 
                    connection_id
                )
            
            await asyncio.sleep(5)  # Update every 5 seconds
            
    except Exception as e:
        logger.error(f"Error sending market data updates: {e}")


async def send_portfolio_updates(connection_id: str, user_id: str):
    """Send periodic portfolio updates"""
    try:
        while connection_id in manager.active_connections:
            # Generate mock portfolio update
            total_value = 125000 + (hash(user_id + str(datetime.utcnow().minute)) % 10000)
            daily_change = (hash(user_id + str(datetime.utcnow().hour)) % 5000 - 2500)
            
            portfolio_update = {
                "type": "portfolio_update",
                "data": {
                    "total_value": total_value,
                    "daily_change": daily_change,
                    "daily_change_percent": round((daily_change / total_value) * 100, 2),
                    "timestamp": datetime.utcnow().isoformat(),
                    "user_id": user_id
                }
            }
            
            await manager.send_personal_message(
                json.dumps(portfolio_update), 
                connection_id
            )
            
            await asyncio.sleep(30)  # Update every 30 seconds
            
    except Exception as e:
        logger.error(f"Error sending portfolio updates: {e}")


# REST endpoints for WebSocket management
@router.get("/ws/status")
async def websocket_status():
    """Get WebSocket server status"""
    return {
        "active_connections": len(manager.active_connections),
        "connected_users": len(manager.user_connections),
        "status": "healthy"
    }


@router.post("/ws/broadcast")
async def broadcast_message(message: dict, current_user: User = Depends(get_current_user)):
    """Broadcast message to all connected clients (admin only)"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    broadcast_data = {
        "type": "broadcast",
        "data": message,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    await manager.broadcast(json.dumps(broadcast_data))
    
    return {
        "message": "Broadcast sent",
        "recipients": len(manager.active_connections)
    }