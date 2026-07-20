"""
Main FastAPI application for Portfolio Tracker MVP.
Focused on real portfolio tracking, not simulations.
"""
from fastapi import FastAPI, HTTPException, Depends, File, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager
from typing import List, Optional, Dict
import logging
import json
from datetime import datetime, date

from app.core.config import settings
from app.database.session import get_db, engine
from app.models.portfolio import Base
from app.services.portfolio.transaction_processor import TransactionProcessor
from app.services.market_data.providers.yfinance_enhanced import YFinanceProvider
from app.api.v1 import auth, portfolio, transactions, market_data

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Portfolio Tracker...")
    
    # Create database tables
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created/verified")
    
    # Initialize data providers
    app.state.market_data_provider = YFinanceProvider()
    logger.info("Market data providers initialized")
    
    # Initialize WebSocket manager
    app.state.websocket_manager = WebSocketManager()
    logger.info("WebSocket manager initialized")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Portfolio Tracker...")
    await app.state.websocket_manager.disconnect_all()


# Create FastAPI app
app = FastAPI(
    title="Portfolio Tracker",
    description="Real portfolio tracking with accurate calculations and tax optimization",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class WebSocketManager:
    """Manage WebSocket connections for real-time updates."""
    
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
        self.user_connection_count: Dict[str, int] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str):
        """Connect a new WebSocket client."""
        # Check connection limit
        if self.user_connection_count.get(user_id, 0) >= settings.WS_MAX_CONNECTIONS_PER_USER:
            await websocket.close(code=1008, reason="Connection limit exceeded")
            return False
        
        await websocket.accept()
        
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        
        self.active_connections[user_id].append(websocket)
        self.user_connection_count[user_id] = self.user_connection_count.get(user_id, 0) + 1
        
        logger.info(f"WebSocket connected for user {user_id}")
        return True
    
    def disconnect(self, websocket: WebSocket, user_id: str):
        """Disconnect a WebSocket client."""
        if user_id in self.active_connections:
            self.active_connections[user_id].remove(websocket)
            self.user_connection_count[user_id] -= 1
            
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
                del self.user_connection_count[user_id]
        
        logger.info(f"WebSocket disconnected for user {user_id}")
    
    async def send_to_user(self, user_id: str, message: dict):
        """Send message to all connections for a user."""
        if user_id in self.active_connections:
            disconnected = []
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except:
                    disconnected.append(connection)
            
            # Clean up disconnected clients
            for conn in disconnected:
                self.disconnect(conn, user_id)
    
    async def broadcast_quote(self, symbol: str, quote: dict):
        """Broadcast quote update to all subscribed users."""
        message = {
            "type": "quote_update",
            "symbol": symbol,
            "data": quote,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # In production, we'd check which users are subscribed to this symbol
        for user_id in self.active_connections:
            await self.send_to_user(user_id, message)
    
    async def disconnect_all(self):
        """Disconnect all WebSocket clients."""
        for user_id in list(self.active_connections.keys()):
            for conn in self.active_connections[user_id]:
                await conn.close()


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with system status."""
    return {
        "app": "Portfolio Tracker",
        "version": "1.0.0",
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "data_disclaimer": "Market data is delayed by 15 minutes",
        "timestamp": datetime.utcnow().isoformat()
    }


# Health check endpoint
@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint."""
    checks = {
        "database": False,
        "market_data": False,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Check database
    try:
        db.execute("SELECT 1")
        checks["database"] = True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
    
    # Check market data provider
    try:
        provider_status = await app.state.market_data_provider.check_health()
        checks["market_data"] = provider_status.value == "healthy"
    except Exception as e:
        logger.error(f"Market data health check failed: {e}")
    
    status_code = 200 if all([checks["database"], checks["market_data"]]) else 503
    
    return JSONResponse(
        status_code=status_code,
        content={
            "status": "healthy" if status_code == 200 else "unhealthy",
            "checks": checks
        }
    )


# Portfolio endpoints
@app.get("/api/v1/portfolio/{account_id}")
async def get_portfolio(
    account_id: str,
    db: Session = Depends(get_db)
):
    """Get portfolio overview for an account."""
    # TODO: Add authentication and verify user owns this account
    
    from app.models.portfolio import Position, Instrument
    
    positions = db.query(Position).join(Instrument).filter(
        Position.account_id == account_id
    ).all()
    
    total_value = sum(p.market_value or 0 for p in positions)
    total_cost = sum(p.quantity * p.average_cost for p in positions if p.average_cost)
    total_gain = total_value - total_cost if total_cost else 0
    
    return {
        "account_id": account_id,
        "total_value": float(total_value),
        "total_cost": float(total_cost),
        "total_gain": float(total_gain),
        "total_gain_percent": float((total_gain / total_cost * 100) if total_cost else 0),
        "position_count": len(positions),
        "last_updated": datetime.utcnow().isoformat()
    }


@app.get("/api/v1/positions/{account_id}")
async def get_positions(
    account_id: str,
    db: Session = Depends(get_db)
):
    """Get all positions for an account."""
    from app.models.portfolio import Position, Instrument
    
    positions = db.query(Position, Instrument).join(Instrument).filter(
        Position.account_id == account_id
    ).all()
    
    result = []
    for position, instrument in positions:
        result.append({
            "symbol": instrument.symbol,
            "name": instrument.name,
            "quantity": float(position.quantity),
            "average_cost": float(position.average_cost) if position.average_cost else None,
            "market_value": float(position.market_value) if position.market_value else None,
            "unrealized_gain": float(position.unrealized_gain) if position.unrealized_gain else None,
            "last_updated": position.last_updated.isoformat()
        })
    
    return result


@app.post("/api/v1/import")
async def import_csv(
    account_id: str,
    file: UploadFile = File(...),
    broker: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Import transactions from CSV file."""
    # TODO: Add authentication
    
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV")
    
    content = await file.read()
    csv_content = content.decode('utf-8')
    
    processor = TransactionProcessor(db)
    imported_count, errors = processor.import_csv(csv_content, account_id, broker)
    
    if errors and imported_count == 0:
        raise HTTPException(status_code=400, detail={"message": "Import failed", "errors": errors})
    
    return {
        "imported": imported_count,
        "errors": errors,
        "message": f"Successfully imported {imported_count} transactions"
    }


@app.get("/api/v1/quotes/{symbols}")
async def get_quotes(symbols: str):
    """Get quotes for multiple symbols."""
    symbol_list = symbols.split(',')
    
    if len(symbol_list) > 50:
        raise HTTPException(status_code=400, detail="Maximum 50 symbols per request")
    
    quotes = await app.state.market_data_provider.get_quotes_bulk(symbol_list)
    
    result = {}
    for symbol, quote in quotes.items():
        if quote:
            result[symbol] = {
                "last": float(quote.last),
                "bid": float(quote.bid) if quote.bid else None,
                "ask": float(quote.ask) if quote.ask else None,
                "volume": quote.volume,
                "timestamp": quote.timestamp.isoformat(),
                "is_delayed": quote.is_delayed,
                "delay_minutes": quote.delay_minutes
            }
    
    return result


@app.websocket("/ws/market_data")
async def websocket_market_data(
    websocket: WebSocket,
    # user_id would come from JWT token in production
    user_id: str = "demo_user"
):
    """WebSocket endpoint for real-time market data."""
    manager = app.state.websocket_manager
    
    if not await manager.connect(websocket, user_id):
        return
    
    try:
        # Send initial connection message
        await websocket.send_json({
            "type": "connected",
            "message": "WebSocket connected successfully",
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Handle incoming messages
        while True:
            data = await websocket.receive_json()
            
            if data.get("action") == "subscribe":
                symbols = data.get("symbols", [])
                # TODO: Track user subscriptions
                await websocket.send_json({
                    "type": "subscribed",
                    "symbols": symbols,
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            elif data.get("action") == "unsubscribe":
                symbols = data.get("symbols", [])
                await websocket.send_json({
                    "type": "unsubscribed",
                    "symbols": symbols,
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            elif data.get("action") == "ping":
                await websocket.send_json({
                    "type": "pong",
                    "timestamp": datetime.utcnow().isoformat()
                })
    
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket, user_id)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main_portfolio:app",
        host="0.0.0.0",
        port=8000,
        reload=True if settings.ENVIRONMENT == "development" else False
    )