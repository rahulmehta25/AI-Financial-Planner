"""
Market Data API Endpoints

Comprehensive REST API endpoints for market data with advanced features:
- Multi-provider failover
- Real-time WebSocket subscriptions
- Intelligent caching
- Rate limiting and quota management
- Comprehensive error handling
"""

import asyncio
import logging
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any, Union
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi import BackgroundTasks, status
from pydantic import BaseModel, Field, validator
from pydantic.types import conint, confloat

from ....core.deps import get_current_user
from ....services.market_data.aggregator import MarketDataAggregator
from ....services.market_data.websocket import WebSocketManager, WebSocketEventType
from ....services.market_data.cache_enhanced import EnhancedCacheManager, QuotaExceededException
from ....services.market_data.models import DataProvider


# Response Models
class MarketDataPointResponse(BaseModel):
    """Market data point response"""
    symbol: str
    price: Optional[float] = None
    volume: Optional[int] = None
    timestamp: Optional[datetime] = None
    bid: Optional[float] = None
    ask: Optional[float] = None
    open_price: Optional[float] = None
    high_price: Optional[float] = None
    low_price: Optional[float] = None
    previous_close: Optional[float] = None
    change: Optional[float] = None
    change_percent: Optional[float] = None
    provider: Optional[str] = None


class HistoricalDataResponse(BaseModel):
    """Historical data response"""
    symbol: str
    data_points: List[MarketDataPointResponse]
    start_date: date
    end_date: date
    interval: str
    provider: Optional[str] = None
    total_points: int = Field(..., description="Total number of data points")


class CompanyInfoResponse(BaseModel):
    """Company information response"""
    symbol: str
    name: str = ""
    description: str = ""
    sector: str = ""
    industry: str = ""
    market_cap: Optional[float] = None
    shares_outstanding: Optional[int] = None
    exchange: str = ""
    currency: str = "USD"
    country: str = ""
    website: str = ""
    employees: Optional[int] = None
    pe_ratio: Optional[float] = None
    dividend_yield: Optional[float] = None
    provider: Optional[str] = None


class QuoteRequest(BaseModel):
    """Quote request model"""
    symbols: List[str] = Field(..., min_items=1, max_items=100, description="List of symbols")
    use_cache: bool = Field(True, description="Whether to use cache")
    
    @validator('symbols')
    def validate_symbols(cls, v):
        """Validate symbol format"""
        for symbol in v:
            if not isinstance(symbol, str) or not symbol.strip():
                raise ValueError("Invalid symbol format")
        return [s.upper().strip() for s in v]


class HistoricalRequest(BaseModel):
    """Historical data request model"""
    symbol: str = Field(..., description="Stock symbol")
    start_date: date = Field(..., description="Start date")
    end_date: date = Field(..., description="End date")
    interval: str = Field("1d", regex="^(1m|5m|15m|1h|1d|1w|1M)$", description="Data interval")
    use_cache: bool = Field(True, description="Whether to use cache")
    
    @validator('symbol')
    def validate_symbol(cls, v):
        return v.upper().strip()
    
    @validator('end_date')
    def validate_date_range(cls, v, values):
        if 'start_date' in values and v < values['start_date']:
            raise ValueError("End date must be after start date")
        if v > date.today():
            raise ValueError("End date cannot be in the future")
        return v


class WebSocketSubscriptionRequest(BaseModel):
    """WebSocket subscription request"""
    symbols: List[str] = Field(..., min_items=1, max_items=50)
    event_types: List[str] = Field(["trade", "quote"], description="Event types to subscribe to")
    
    @validator('symbols')
    def validate_symbols(cls, v):
        return [s.upper().strip() for s in v]
    
    @validator('event_types')
    def validate_event_types(cls, v):
        valid_types = {"trade", "quote", "aggregate"}
        for event_type in v:
            if event_type not in valid_types:
                raise ValueError(f"Invalid event type: {event_type}")
        return v


class APIResponse(BaseModel):
    """Standard API response wrapper"""
    success: bool
    data: Optional[Any] = None
    message: str = ""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    cached: bool = False
    provider: Optional[str] = None
    quota_remaining: Optional[Dict[str, Any]] = None


# Router setup
router = APIRouter(prefix="/market-data", tags=["market_data"])
logger = logging.getLogger("market_data.api")

# Global instances (would be injected in production)
aggregator = None
websocket_manager = None
cache_manager = None


async def get_aggregator():
    """Dependency to get market data aggregator"""
    global aggregator
    if not aggregator:
        from ....services.market_data.aggregator import MarketDataAggregator
        aggregator = MarketDataAggregator()
        await aggregator.initialize()
    return aggregator


async def get_websocket_manager():
    """Dependency to get WebSocket manager"""
    global websocket_manager
    if not websocket_manager:
        agg = await get_aggregator()
        from ....services.market_data.websocket import WebSocketManager
        websocket_manager = WebSocketManager(agg)
        await websocket_manager.initialize()
    return websocket_manager


async def get_cache_manager():
    """Dependency to get cache manager"""
    global cache_manager
    if not cache_manager:
        from ....services.market_data.cache_enhanced import EnhancedCacheManager
        cache_manager = EnhancedCacheManager()
        await cache_manager.initialize()
    return cache_manager


# Quote Endpoints
@router.post("/quotes", response_model=APIResponse)
async def get_quotes(
    request: QuoteRequest,
    background_tasks: BackgroundTasks,
    current_user=Depends(get_current_user),
    aggregator=Depends(get_aggregator),
    cache_mgr=Depends(get_cache_manager)
):
    """
    Get current quotes for multiple symbols with intelligent provider failover.
    
    Features:
    - Multi-provider failover
    - Intelligent caching
    - Rate limiting
    - Data quality validation
    """
    try:
        start_time = datetime.utcnow()
        
        # Get quotes through aggregator
        quotes = await aggregator.get_multiple_quotes(request.symbols, request.use_cache)
        
        # Convert to response format
        quote_responses = []
        provider_used = None
        
        for quote in quotes:
            if quote:
                quote_response = MarketDataPointResponse(
                    symbol=quote.symbol,
                    price=quote.price,
                    volume=quote.volume,
                    timestamp=quote.timestamp,
                    bid=quote.bid,
                    ask=quote.ask,
                    open_price=quote.open_price,
                    high_price=quote.high_price,
                    low_price=quote.low_price,
                    previous_close=quote.previous_close,
                    change=quote.change,
                    change_percent=quote.change_percent,
                    provider=quote.provider.value if quote.provider else None
                )
                quote_responses.append(quote_response)
                
                if not provider_used and quote.provider:
                    provider_used = quote.provider.value
        
        # Get quota information
        quota_info = cache_mgr.quota_manager.get_quota_status()
        
        # Calculate processing time
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        # Log metrics in background
        background_tasks.add_task(
            log_api_metrics,
            "quotes",
            len(request.symbols),
            len(quote_responses),
            processing_time,
            provider_used
        )
        
        return APIResponse(
            success=True,
            data=quote_responses,
            message=f"Retrieved {len(quote_responses)}/{len(request.symbols)} quotes",
            cached=request.use_cache,
            provider=provider_used,
            quota_remaining=quota_info
        )
        
    except QuotaExceededException as e:
        logger.warning(f"Quota exceeded for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting quotes: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve quotes"
        )


@router.get("/quote/{symbol}", response_model=APIResponse)
async def get_single_quote(
    symbol: str,
    use_cache: bool = Query(True, description="Use cache if available"),
    current_user=Depends(get_current_user),
    aggregator=Depends(get_aggregator)
):
    """Get current quote for a single symbol"""
    try:
        quote = await aggregator.get_quote(symbol, use_cache)
        
        if not quote:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Quote not found for symbol: {symbol}"
            )
        
        quote_response = MarketDataPointResponse(
            symbol=quote.symbol,
            price=quote.price,
            volume=quote.volume,
            timestamp=quote.timestamp,
            bid=quote.bid,
            ask=quote.ask,
            open_price=quote.open_price,
            high_price=quote.high_price,
            low_price=quote.low_price,
            previous_close=quote.previous_close,
            change=quote.change,
            change_percent=quote.change_percent,
            provider=quote.provider.value if quote.provider else None
        )
        
        return APIResponse(
            success=True,
            data=quote_response,
            message="Quote retrieved successfully",
            cached=use_cache,
            provider=quote.provider.value if quote.provider else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting quote for {symbol}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve quote"
        )


# Historical Data Endpoints
@router.post("/historical", response_model=APIResponse)
async def get_historical_data(
    request: HistoricalRequest,
    background_tasks: BackgroundTasks,
    current_user=Depends(get_current_user),
    aggregator=Depends(get_aggregator)
):
    """
    Get historical market data with intelligent provider selection and caching.
    
    Features:
    - Intelligent provider selection based on data requirements
    - Comprehensive caching strategy
    - Data quality validation
    - Automatic gap filling
    """
    try:
        start_time = datetime.utcnow()
        
        # Validate date range
        if (request.end_date - request.start_date).days > 365 * 5:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Date range too large (maximum 5 years)"
            )
        
        # Get historical data through aggregator
        historical = await aggregator.get_historical_data(
            request.symbol,
            request.start_date,
            request.end_date,
            request.interval,
            request.use_cache
        )
        
        if not historical:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Historical data not found for symbol: {request.symbol}"
            )
        
        # Convert to response format
        data_points = []
        for point in historical.data_points:
            data_point = MarketDataPointResponse(
                symbol=point.symbol,
                price=point.price,
                volume=point.volume,
                timestamp=point.timestamp,
                open_price=point.open_price,
                high_price=point.high_price,
                low_price=point.low_price,
                provider=point.provider.value if point.provider else None
            )
            data_points.append(data_point)
        
        historical_response = HistoricalDataResponse(
            symbol=historical.symbol,
            data_points=data_points,
            start_date=historical.start_date,
            end_date=historical.end_date,
            interval=historical.interval,
            provider=historical.provider.value if historical.provider else None,
            total_points=len(data_points)
        )
        
        # Log metrics
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        background_tasks.add_task(
            log_api_metrics,
            "historical",
            1,
            len(data_points),
            processing_time,
            historical.provider.value if historical.provider else None
        )
        
        return APIResponse(
            success=True,
            data=historical_response,
            message=f"Retrieved {len(data_points)} historical data points",
            cached=request.use_cache,
            provider=historical.provider.value if historical.provider else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting historical data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve historical data"
        )


# Company Information Endpoints
@router.get("/company/{symbol}", response_model=APIResponse)
async def get_company_info(
    symbol: str,
    use_cache: bool = Query(True, description="Use cache if available"),
    current_user=Depends(get_current_user),
    aggregator=Depends(get_aggregator)
):
    """Get comprehensive company information"""
    try:
        company_info = await aggregator.get_company_info(symbol, use_cache)
        
        if not company_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Company information not found for symbol: {symbol}"
            )
        
        company_response = CompanyInfoResponse(
            symbol=company_info.symbol,
            name=company_info.name,
            description=company_info.description,
            sector=company_info.sector,
            industry=company_info.industry,
            market_cap=company_info.market_cap,
            shares_outstanding=company_info.shares_outstanding,
            exchange=company_info.exchange,
            currency=company_info.currency,
            country=company_info.country,
            website=company_info.website,
            employees=company_info.employees,
            pe_ratio=company_info.pe_ratio,
            dividend_yield=company_info.dividend_yield,
            provider=company_info.provider.value if company_info.provider else None
        )
        
        return APIResponse(
            success=True,
            data=company_response,
            message="Company information retrieved successfully",
            cached=use_cache,
            provider=company_info.provider.value if company_info.provider else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting company info for {symbol}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve company information"
        )


# WebSocket Endpoints
@router.websocket("/ws/realtime")
async def websocket_realtime_endpoint(
    websocket: WebSocket,
    ws_manager=Depends(get_websocket_manager)
):
    """
    WebSocket endpoint for real-time market data streaming.
    
    Supports:
    - Real-time trade data
    - Real-time quote data
    - Multiple symbol subscriptions
    - Automatic reconnection
    """
    await websocket.accept()
    logger.info(f"WebSocket connected: {websocket.client}")
    
    user_subscriptions = set()
    
    try:
        while True:
            # Wait for subscription message
            data = await websocket.receive_json()
            
            if data.get("action") == "subscribe":
                # Validate subscription request
                try:
                    sub_request = WebSocketSubscriptionRequest(**data)
                    
                    # Create handler for this WebSocket connection
                    async def websocket_handler(market_data: Dict[str, Any]):
                        try:
                            await websocket.send_json(market_data)
                        except Exception as e:
                            logger.error(f"Error sending WebSocket data: {e}")
                    
                    # Convert event types
                    event_types = [
                        WebSocketEventType(et) for et in sub_request.event_types
                    ]
                    
                    # Subscribe through WebSocket manager
                    subscription_id = await ws_manager.subscribe(
                        sub_request.symbols,
                        event_types,
                        websocket_handler
                    )
                    
                    user_subscriptions.add(subscription_id)
                    
                    # Send confirmation
                    await websocket.send_json({
                        "type": "subscription_confirmed",
                        "subscription_id": subscription_id,
                        "symbols": sub_request.symbols,
                        "event_types": sub_request.event_types
                    })
                    
                    logger.info(f"WebSocket subscribed to {len(sub_request.symbols)} symbols")
                    
                except Exception as e:
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Subscription failed: {str(e)}"
                    })
            
            elif data.get("action") == "unsubscribe":
                subscription_id = data.get("subscription_id")
                if subscription_id in user_subscriptions:
                    await ws_manager.unsubscribe(subscription_id)
                    user_subscriptions.remove(subscription_id)
                    
                    await websocket.send_json({
                        "type": "unsubscription_confirmed",
                        "subscription_id": subscription_id
                    })
            
            elif data.get("action") == "ping":
                await websocket.send_json({"type": "pong"})
            
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {websocket.client}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        # Clean up subscriptions
        for subscription_id in user_subscriptions:
            try:
                await ws_manager.unsubscribe(subscription_id)
            except Exception as e:
                logger.error(f"Error cleaning up subscription {subscription_id}: {e}")


# System Status Endpoints
@router.get("/status", response_model=APIResponse)
async def get_system_status(
    current_user=Depends(get_current_user),
    aggregator=Depends(get_aggregator),
    cache_mgr=Depends(get_cache_manager)
):
    """Get comprehensive system status including providers, cache, and quotas"""
    try:
        status_data = {
            "aggregator": aggregator.get_system_status(),
            "cache": cache_mgr.get_cache_stats(),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return APIResponse(
            success=True,
            data=status_data,
            message="System status retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve system status"
        )


@router.get("/providers", response_model=APIResponse)
async def get_provider_status(
    current_user=Depends(get_current_user),
    aggregator=Depends(get_aggregator)
):
    """Get status of all market data providers"""
    try:
        provider_status = {}
        
        for provider_type in DataProvider:
            if provider_type in aggregator.providers:
                provider = aggregator.providers[provider_type]
                health = await provider.health_check()
                
                provider_status[provider_type.value] = {
                    "available": True,
                    "healthy": health,
                    "name": provider.name if hasattr(provider, 'name') else provider_type.value
                }
            else:
                provider_status[provider_type.value] = {
                    "available": False,
                    "healthy": False,
                    "name": provider_type.value
                }
        
        return APIResponse(
            success=True,
            data=provider_status,
            message="Provider status retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Error getting provider status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve provider status"
        )


# Cache Management Endpoints
@router.delete("/cache/{symbol}")
async def invalidate_symbol_cache(
    symbol: str,
    current_user=Depends(get_current_user),
    cache_mgr=Depends(get_cache_manager)
):
    """Invalidate cache for a specific symbol"""
    try:
        await cache_mgr.invalidate_symbol(symbol)
        
        return APIResponse(
            success=True,
            message=f"Cache invalidated for symbol: {symbol}"
        )
        
    except Exception as e:
        logger.error(f"Error invalidating cache for {symbol}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to invalidate cache"
        )


# Background Tasks
async def log_api_metrics(
    endpoint: str,
    symbols_requested: int,
    symbols_returned: int,
    processing_time: float,
    provider: Optional[str]
):
    """Log API metrics for monitoring and optimization"""
    try:
        logger.info(
            f"API Metrics - Endpoint: {endpoint}, "
            f"Requested: {symbols_requested}, "
            f"Returned: {symbols_returned}, "
            f"Time: {processing_time:.3f}s, "
            f"Provider: {provider}"
        )
        
        # Here you could also send metrics to monitoring systems like Prometheus, DataDog, etc.
        
    except Exception as e:
        logger.error(f"Error logging API metrics: {e}")


# Error Handlers
@router.exception_handler(QuotaExceededException)
async def quota_exceeded_handler(request, exc):
    """Handle quota exceeded exceptions"""
    return APIResponse(
        success=False,
        message=str(exc),
        timestamp=datetime.utcnow()
    )


# Health Check
@router.get("/health")
async def health_check():
    """Simple health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow()}