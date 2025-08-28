"""
Enhanced Market Data API Router

FastAPI router providing comprehensive market data endpoints with:
- Real-time quotes and trades with WebSocket streaming
- Historical data with advanced analytics
- Multi-source consensus and validation
- High-performance caching and failover
- Performance monitoring and health checks
"""

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, Query, Depends
from fastapi.responses import StreamingResponse
from typing import List, Optional, Dict, Any, Union
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
import asyncio
import json
import logging

from .unified_market_data_system import (
    UnifiedMarketDataSystem,
    MarketDataRequest,
    MarketDataResponse,
    DataSourceType,
    UpdateFrequency,
    unified_market_data_system
)
from .aggregator_enhanced import ConsensusMethod, DataQuality
from .failover_manager import ServiceLevel

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/market-data", tags=["Market Data"])


# Pydantic models for API
class QuoteRequest(BaseModel):
    symbols: List[str] = Field(..., description="List of stock symbols", example=["AAPL", "GOOGL", "MSFT"])
    consensus_method: ConsensusMethod = Field(ConsensusMethod.WEIGHTED_AVERAGE, description="Consensus building method")
    max_sources: int = Field(5, ge=1, le=10, description="Maximum number of data sources to use")
    include_validation: bool = Field(True, description="Include data validation")
    service_level: ServiceLevel = Field(ServiceLevel.MEDIUM, description="Required service level")


class HistoricalDataRequest(BaseModel):
    symbols: List[str] = Field(..., description="List of stock symbols")
    start_date: datetime = Field(..., description="Start date for historical data")
    end_date: datetime = Field(default_factory=datetime.utcnow, description="End date for historical data")
    interval: str = Field("1d", description="Data interval (1m, 5m, 15m, 1h, 1d)", regex="^(1m|5m|15m|1h|1d|1w|1M)$")
    include_fundamentals: bool = Field(False, description="Include fundamental ratios")
    include_technical: bool = Field(True, description="Include technical indicators")


class StreamSubscriptionRequest(BaseModel):
    symbols: List[str] = Field(..., description="Symbols to subscribe to")
    data_types: List[DataSourceType] = Field([DataSourceType.REAL_TIME], description="Types of data to stream")
    update_frequency: UpdateFrequency = Field(UpdateFrequency.MEDIUM, description="Update frequency")


class SystemStatusResponse(BaseModel):
    system: Dict[str, Any]
    performance: Dict[str, Any]
    components: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class QuoteResponse(BaseModel):
    symbol: str
    bid: Optional[float] = None
    ask: Optional[float] = None
    last: Optional[float] = None
    volume: Optional[int] = None
    spread: Optional[float] = None
    timestamp: datetime
    quality: DataQuality
    confidence: float
    sources: List[str]
    validation_results: Optional[Dict[str, Any]] = None


# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.subscriptions: Dict[WebSocket, Dict[str, Any]] = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if websocket in self.subscriptions:
            del self.subscriptions[websocket]

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        try:
            await websocket.send_text(json.dumps(message, default=str))
        except Exception as e:
            logger.error(f"Error sending WebSocket message: {e}")

    async def broadcast(self, message: dict, symbol_filter: str = None):
        for connection in self.active_connections.copy():
            try:
                # Filter by symbol if specified
                if symbol_filter:
                    sub_info = self.subscriptions.get(connection, {})
                    if symbol_filter not in sub_info.get('symbols', []):
                        continue
                
                await connection.send_text(json.dumps(message, default=str))
            except Exception as e:
                logger.error(f"Error broadcasting WebSocket message: {e}")
                self.disconnect(connection)


# Global connection manager
manager = ConnectionManager()


# Dependency to get market data system
async def get_market_data_system() -> UnifiedMarketDataSystem:
    if not unified_market_data_system.is_initialized:
        await unified_market_data_system.initialize()
    return unified_market_data_system


@router.on_event("startup")
async def startup_event():
    """Initialize the market data system on startup"""
    try:
        await unified_market_data_system.initialize()
        logger.info("Market data system initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize market data system: {e}")
        raise


@router.on_event("shutdown")
async def shutdown_event():
    """Shutdown the market data system"""
    try:
        await unified_market_data_system.shutdown()
        logger.info("Market data system shutdown complete")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


@router.get("/quotes", response_model=List[QuoteResponse])
async def get_quotes(
    request: QuoteRequest,
    system: UnifiedMarketDataSystem = Depends(get_market_data_system)
):
    """
    Get real-time quotes with multi-source consensus validation
    
    Returns validated quotes from multiple data providers with quality metrics.
    """
    try:
        market_request = MarketDataRequest(
            symbols=request.symbols,
            data_types=[DataSourceType.REAL_TIME],
            consensus_method=request.consensus_method,
            include_validation=request.include_validation,
            service_level=request.service_level,
            enable_caching=True,
            max_age_seconds=60
        )
        
        responses = await system.get_market_data(market_request)
        
        # Convert to API response format
        quote_responses = []
        for response in responses:
            if response.data_type == DataSourceType.REAL_TIME:
                data = response.data
                quote_responses.append(QuoteResponse(
                    symbol=response.symbol,
                    bid=data.get('bid'),
                    ask=data.get('ask'),
                    last=data.get('last') or data.get('price'),
                    volume=data.get('volume'),
                    spread=data.get('spread'),
                    timestamp=response.timestamp,
                    quality=response.quality,
                    confidence=response.confidence,
                    sources=response.sources,
                    validation_results=response.validation_results
                ))
        
        return quote_responses
        
    except Exception as e:
        logger.error(f"Error getting quotes: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/quotes/batch")
async def get_quotes_batch(
    symbols: List[str],
    consensus_method: ConsensusMethod = ConsensusMethod.WEIGHTED_AVERAGE,
    service_level: ServiceLevel = ServiceLevel.MEDIUM,
    system: UnifiedMarketDataSystem = Depends(get_market_data_system)
):
    """Get quotes for multiple symbols efficiently using batch processing"""
    try:
        if len(symbols) > 100:
            raise HTTPException(status_code=400, detail="Maximum 100 symbols per batch request")
        
        market_request = MarketDataRequest(
            symbols=symbols,
            data_types=[DataSourceType.REAL_TIME],
            consensus_method=consensus_method,
            service_level=service_level,
            enable_caching=True,
            max_age_seconds=30
        )
        
        responses = await system.get_market_data(market_request)
        
        # Group by symbol
        quotes_by_symbol = {}
        for response in responses:
            if response.data_type == DataSourceType.REAL_TIME:
                quotes_by_symbol[response.symbol] = {
                    'data': response.data,
                    'quality': response.quality.value,
                    'confidence': response.confidence,
                    'sources': response.sources,
                    'timestamp': response.timestamp,
                    'latency_ms': response.latency_ms
                }
        
        return {
            'quotes': quotes_by_symbol,
            'processed_count': len(quotes_by_symbol),
            'requested_count': len(symbols),
            'timestamp': datetime.utcnow()
        }
        
    except Exception as e:
        logger.error(f"Error in batch quotes: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/historical")
async def get_historical_data(
    request: HistoricalDataRequest,
    system: UnifiedMarketDataSystem = Depends(get_market_data_system)
):
    """Get historical market data with enhanced analytics and technical indicators"""
    try:
        if len(request.symbols) > 50:
            raise HTTPException(status_code=400, detail="Maximum 50 symbols per historical request")
        
        # Validate date range
        if request.start_date >= request.end_date:
            raise HTTPException(status_code=400, detail="Start date must be before end date")
        
        date_diff = request.end_date - request.start_date
        if date_diff.days > 365:
            raise HTTPException(status_code=400, detail="Maximum date range is 365 days")
        
        market_request = MarketDataRequest(
            symbols=request.symbols,
            data_types=[DataSourceType.HISTORICAL],
            service_level=ServiceLevel.HIGH,
            enable_caching=True,
            max_age_seconds=3600  # 1 hour cache for historical data
        )
        
        responses = await system.get_market_data(market_request)
        
        # Format historical data responses
        historical_data = {}
        for response in responses:
            if response.data_type == DataSourceType.HISTORICAL:
                historical_data[response.symbol] = {
                    'data': response.data,
                    'quality': response.quality.value,
                    'confidence': response.confidence,
                    'sources': response.sources,
                    'from_cache': response.from_cache,
                    'validation': response.validation_results
                }
        
        return {
            'historical_data': historical_data,
            'request_params': {
                'start_date': request.start_date,
                'end_date': request.end_date,
                'interval': request.interval,
                'include_fundamentals': request.include_fundamentals,
                'include_technical': request.include_technical
            },
            'processed_count': len(historical_data),
            'timestamp': datetime.utcnow()
        }
        
    except Exception as e:
        logger.error(f"Error getting historical data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/fundamental/{symbol}")
async def get_fundamental_data(
    symbol: str,
    system: UnifiedMarketDataSystem = Depends(get_market_data_system)
):
    """Get fundamental data and financial ratios for a symbol"""
    try:
        market_request = MarketDataRequest(
            symbols=[symbol.upper()],
            data_types=[DataSourceType.FUNDAMENTAL],
            service_level=ServiceLevel.MEDIUM,
            enable_caching=True,
            max_age_seconds=86400  # 24 hour cache for fundamental data
        )
        
        responses = await system.get_market_data(market_request)
        
        if not responses:
            raise HTTPException(status_code=404, detail=f"Fundamental data not found for {symbol}")
        
        response = responses[0]
        
        return {
            'symbol': symbol.upper(),
            'fundamental_data': response.data,
            'quality': response.quality.value,
            'confidence': response.confidence,
            'sources': response.sources,
            'timestamp': response.timestamp,
            'from_cache': response.from_cache
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting fundamental data for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sentiment/{symbol}")
async def get_market_sentiment(
    symbol: str,
    timeframe: str = "1d",
    system: UnifiedMarketDataSystem = Depends(get_market_data_system)
):
    """Get market sentiment analysis for a symbol"""
    try:
        # This would use the sentiment analysis from the aggregator
        sentiment_data = await system.aggregator.get_market_sentiment_analysis([symbol.upper()], timeframe)
        
        if symbol.upper() not in sentiment_data:
            raise HTTPException(status_code=404, detail=f"Sentiment data not found for {symbol}")
        
        return {
            'symbol': symbol.upper(),
            'sentiment': sentiment_data[symbol.upper()],
            'timeframe': timeframe,
            'timestamp': datetime.utcnow()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting sentiment for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.websocket("/stream")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time market data streaming"""
    await manager.connect(websocket)
    
    try:
        while True:
            # Wait for subscription message
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get('type') == 'subscribe':
                # Handle subscription
                symbols = message.get('symbols', [])
                data_types = [DataSourceType(dt) for dt in message.get('data_types', ['real_time'])]
                
                # Store subscription info
                manager.subscriptions[websocket] = {
                    'symbols': symbols,
                    'data_types': data_types,
                    'subscribed_at': datetime.utcnow()
                }
                
                # Set up real-time callback
                async def websocket_callback(response: MarketDataResponse):
                    if response.symbol in symbols:
                        await manager.send_personal_message({
                            'type': 'market_data',
                            'symbol': response.symbol,
                            'data_type': response.data_type.value,
                            'data': response.data,
                            'quality': response.quality.value,
                            'timestamp': response.timestamp.isoformat()
                        }, websocket)
                
                # Subscribe to real-time updates
                system = await get_market_data_system()
                subscription_id = await system.subscribe_real_time(
                    symbols=symbols,
                    data_types=data_types,
                    callback=websocket_callback,
                    update_frequency=UpdateFrequency.HIGH
                )
                
                # Send confirmation
                await manager.send_personal_message({
                    'type': 'subscription_confirmed',
                    'subscription_id': subscription_id,
                    'symbols': symbols,
                    'data_types': [dt.value for dt in data_types]
                }, websocket)
                
            elif message.get('type') == 'unsubscribe':
                # Handle unsubscription
                subscription_id = message.get('subscription_id')
                if subscription_id:
                    system = await get_market_data_system()
                    await system.unsubscribe_real_time(subscription_id)
                
                await manager.send_personal_message({
                    'type': 'unsubscribed',
                    'subscription_id': subscription_id
                }, websocket)
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await manager.send_personal_message({
            'type': 'error',
            'message': str(e)
        }, websocket)


@router.get("/status", response_model=SystemStatusResponse)
async def get_system_status(
    system: UnifiedMarketDataSystem = Depends(get_market_data_system)
):
    """Get comprehensive system status and performance metrics"""
    try:
        status = await system.get_system_status()
        
        return SystemStatusResponse(
            system=status.get('system', {}),
            performance=status.get('performance', {}),
            components=status.get('components', {})
        )
        
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """Simple health check endpoint"""
    try:
        # Basic health checks
        checks = {
            'market_data_system': unified_market_data_system.is_initialized,
            'timestamp': datetime.utcnow(),
            'status': 'healthy' if unified_market_data_system.is_initialized else 'initializing'
        }
        
        # Additional component checks if system is initialized
        if unified_market_data_system.is_initialized:
            try:
                # Quick cache check
                if unified_market_data_system.cache and unified_market_data_system.cache.redis:
                    await unified_market_data_system.cache.redis.ping()
                    checks['cache'] = 'healthy'
                else:
                    checks['cache'] = 'unavailable'
            except:
                checks['cache'] = 'unhealthy'
        
        return checks
        
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return {
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow()
        }


@router.get("/performance/metrics")
async def get_performance_metrics(
    system: UnifiedMarketDataSystem = Depends(get_market_data_system)
):
    """Get detailed performance metrics"""
    try:
        metrics = {}
        
        # System performance
        if hasattr(system.monitor, 'get_summary'):
            metrics['system'] = system.monitor.get_summary()
        
        # Cache performance
        if hasattr(system.cache, 'get_performance_stats'):
            metrics['cache'] = await system.cache.get_performance_stats()
        
        # Failover manager metrics
        if hasattr(system.failover_manager, 'get_status'):
            metrics['failover'] = await system.failover_manager.get_status()
        
        # Real-time manager metrics
        if hasattr(system.realtime_manager, 'get_connection_status'):
            metrics['realtime'] = await system.realtime_manager.get_connection_status()
        
        return {
            'metrics': metrics,
            'timestamp': datetime.utcnow()
        }
        
    except Exception as e:
        logger.error(f"Error getting performance metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/admin/reset-circuit-breaker/{provider}")
async def reset_circuit_breaker(
    provider: str,
    system: UnifiedMarketDataSystem = Depends(get_market_data_system)
):
    """Reset circuit breaker for a specific provider (admin endpoint)"""
    try:
        await system.failover_manager.reset_provider(provider)
        
        return {
            'message': f'Circuit breaker reset for provider {provider}',
            'provider': provider,
            'timestamp': datetime.utcnow()
        }
        
    except Exception as e:
        logger.error(f"Error resetting circuit breaker for {provider}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/providers/status")
async def get_providers_status(
    system: UnifiedMarketDataSystem = Depends(get_market_data_system)
):
    """Get status of all data providers"""
    try:
        status = await system.failover_manager.get_status()
        
        return {
            'providers': status.get('providers', {}),
            'overall_health': status.get('overall_health', False),
            'timestamp': status.get('timestamp'),
            'summary': {
                'total_providers': len(status.get('providers', {})),
                'healthy_providers': sum(1 for p in status.get('providers', {}).values() 
                                       if p.get('health', {}).get('status', False)),
                'total_requests': status.get('total_requests', 0),
                'success_rate': (status.get('successful_requests', 0) / 
                               max(status.get('total_requests', 1), 1))
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting provider status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Streaming response for large datasets
@router.get("/stream/historical/{symbol}")
async def stream_historical_data(
    symbol: str,
    start_date: datetime = Query(...),
    end_date: datetime = Query(...),
    interval: str = "1d",
    system: UnifiedMarketDataSystem = Depends(get_market_data_system)
):
    """Stream historical data for large datasets"""
    
    async def generate_data():
        try:
            # This would stream large historical datasets in chunks
            market_request = MarketDataRequest(
                symbols=[symbol.upper()],
                data_types=[DataSourceType.HISTORICAL],
                service_level=ServiceLevel.MEDIUM
            )
            
            responses = await system.get_market_data(market_request)
            
            for response in responses:
                yield f"data: {json.dumps(response.data, default=str)}\n\n"
                
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(
        generate_data(),
        media_type="text/plain",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
    )