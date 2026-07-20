"""
Market Data API Router

FastAPI router for market data endpoints.
"""

from typing import List, Optional, Dict, Any
from datetime import date, datetime
from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from fastapi.responses import StreamingResponse
import json

from .manager import MarketDataManager
from .monitoring import MarketDataMonitor
from .models import (
    MarketDataRequest, MarketDataResponse, AlertConfig, PriceAlert,
    MarketDataPoint, HistoricalData, CompanyInfo, DataProvider, AlertType
)
from .config import config


# Global instances (in a real app, these would be dependency injected)
market_data_manager = MarketDataManager()
monitor = MarketDataMonitor()

# Create router
router = APIRouter(prefix="/api/v1/market-data", tags=["Market Data"])


async def get_market_data_manager() -> MarketDataManager:
    """Dependency to get market data manager"""
    if not market_data_manager._initialized:
        await market_data_manager.initialize()
    return market_data_manager


async def get_monitor() -> MarketDataMonitor:
    """Dependency to get monitoring system"""
    return monitor


@router.get("/quotes/{symbol}", response_model=MarketDataPoint)
async def get_quote(
    symbol: str,
    use_cache: bool = Query(True, description="Use cached data if available"),
    manager: MarketDataManager = Depends(get_market_data_manager),
    monitor: MarketDataMonitor = Depends(get_monitor)
):
    """Get current quote for a symbol"""
    try:
        start_time = datetime.utcnow()
        
        quote = await manager.get_quote(symbol, use_cache=use_cache)
        
        duration = (datetime.utcnow() - start_time).total_seconds()
        monitor.record_api_request(
            provider=config.primary_provider,
            symbol=symbol,
            success=quote is not None,
            duration=duration
        )
        
        if not quote:
            raise HTTPException(status_code=404, detail=f"Quote not found for symbol {symbol}")
        
        return quote
        
    except Exception as e:
        monitor.record_api_request(
            provider=config.primary_provider,
            symbol=symbol,
            success=False,
            duration=0
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/quotes", response_model=List[MarketDataPoint])
async def get_multiple_quotes(
    symbols: List[str],
    use_cache: bool = Query(True, description="Use cached data if available"),
    manager: MarketDataManager = Depends(get_market_data_manager),
    monitor: MarketDataMonitor = Depends(get_monitor)
):
    """Get quotes for multiple symbols"""
    try:
        start_time = datetime.utcnow()
        
        if len(symbols) > 50:
            raise HTTPException(status_code=400, detail="Maximum 50 symbols allowed per request")
        
        quotes = await manager.get_multiple_quotes(symbols, use_cache=use_cache)
        
        duration = (datetime.utcnow() - start_time).total_seconds()
        monitor.record_api_request(
            provider=config.primary_provider,
            symbol="batch",
            success=len(quotes) > 0,
            duration=duration
        )
        
        return quotes
        
    except Exception as e:
        monitor.record_api_request(
            provider=config.primary_provider,
            symbol="batch",
            success=False,
            duration=0
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/historical/{symbol}", response_model=HistoricalData)
async def get_historical_data(
    symbol: str,
    start_date: date = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: date = Query(..., description="End date (YYYY-MM-DD)"),
    interval: str = Query("1d", description="Data interval (1d, 1wk, 1mo)"),
    use_cache: bool = Query(True, description="Use cached data if available"),
    manager: MarketDataManager = Depends(get_market_data_manager),
    monitor: MarketDataMonitor = Depends(get_monitor)
):
    """Get historical data for a symbol"""
    try:
        if start_date > end_date:
            raise HTTPException(status_code=400, detail="Start date must be before end date")
        
        if (end_date - start_date).days > config.max_historical_days:
            raise HTTPException(
                status_code=400, 
                detail=f"Date range too large. Maximum {config.max_historical_days} days allowed"
            )
        
        start_time = datetime.utcnow()
        
        historical = await manager.get_historical_data(
            symbol, start_date, end_date, interval, use_cache=use_cache
        )
        
        duration = (datetime.utcnow() - start_time).total_seconds()
        monitor.record_api_request(
            provider=config.primary_provider,
            symbol=symbol,
            success=historical is not None,
            duration=duration
        )
        
        if not historical:
            raise HTTPException(status_code=404, detail=f"Historical data not found for symbol {symbol}")
        
        return historical
        
    except Exception as e:
        monitor.record_api_request(
            provider=config.primary_provider,
            symbol=symbol,
            success=False,
            duration=0
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/company/{symbol}", response_model=CompanyInfo)
async def get_company_info(
    symbol: str,
    use_cache: bool = Query(True, description="Use cached data if available"),
    manager: MarketDataManager = Depends(get_market_data_manager),
    monitor: MarketDataMonitor = Depends(get_monitor)
):
    """Get company information for a symbol"""
    try:
        start_time = datetime.utcnow()
        
        company_info = await manager.get_company_info(symbol, use_cache=use_cache)
        
        duration = (datetime.utcnow() - start_time).total_seconds()
        monitor.record_api_request(
            provider=config.primary_provider,
            symbol=symbol,
            success=company_info is not None,
            duration=duration
        )
        
        if not company_info:
            raise HTTPException(status_code=404, detail=f"Company info not found for symbol {symbol}")
        
        return company_info
        
    except Exception as e:
        monitor.record_api_request(
            provider=config.primary_provider,
            symbol=symbol,
            success=False,
            duration=0
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/request", response_model=MarketDataResponse)
async def process_market_data_request(
    request: MarketDataRequest,
    manager: MarketDataManager = Depends(get_market_data_manager),
    monitor: MarketDataMonitor = Depends(get_monitor)
):
    """Process a comprehensive market data request"""
    try:
        start_time = datetime.utcnow()
        
        response = await manager.process_request(request)
        
        duration = (datetime.utcnow() - start_time).total_seconds()
        monitor.record_api_request(
            provider=response.provider,
            symbol="request",
            success=response.success,
            duration=duration
        )
        
        return response
        
    except Exception as e:
        monitor.record_api_request(
            provider=config.primary_provider,
            symbol="request",
            success=False,
            duration=0
        )
        raise HTTPException(status_code=500, detail=str(e))


# Alert Management Endpoints

@router.post("/alerts", response_model=Dict[str, str])
async def create_alert(
    alert: AlertConfig,
    manager: MarketDataManager = Depends(get_market_data_manager)
):
    """Create a new price alert"""
    try:
        if not manager.stream_manager:
            raise HTTPException(status_code=503, detail="Streaming service not available")
        
        # Add alert to the alert engine
        success = await manager.stream_manager.alert_engine.add_alert(alert)
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to create alert")
        
        return {"alert_id": alert.id, "status": "created"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/alerts/{user_id}", response_model=List[AlertConfig])
async def get_user_alerts(
    user_id: str,
    manager: MarketDataManager = Depends(get_market_data_manager)
):
    """Get all alerts for a user"""
    try:
        if not manager.stream_manager:
            raise HTTPException(status_code=503, detail="Streaming service not available")
        
        alerts = manager.stream_manager.alert_engine.get_user_alerts(user_id)
        return alerts
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/alerts/{alert_id}")
async def delete_alert(
    alert_id: str,
    manager: MarketDataManager = Depends(get_market_data_manager)
):
    """Delete an alert"""
    try:
        if not manager.stream_manager:
            raise HTTPException(status_code=503, detail="Streaming service not available")
        
        success = await manager.stream_manager.alert_engine.remove_alert(alert_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Alert not found")
        
        return {"status": "deleted"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Streaming Endpoints

@router.post("/streaming/start")
async def start_streaming(
    background_tasks: BackgroundTasks,
    host: Optional[str] = Query(None),
    port: Optional[int] = Query(None),
    manager: MarketDataManager = Depends(get_market_data_manager)
):
    """Start real-time data streaming"""
    try:
        background_tasks.add_task(manager.start_streaming, host, port)
        return {"status": "starting", "message": "Real-time streaming is starting"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/streaming/stop")
async def stop_streaming(
    manager: MarketDataManager = Depends(get_market_data_manager)
):
    """Stop real-time data streaming"""
    try:
        await manager.stop_streaming()
        return {"status": "stopped", "message": "Real-time streaming stopped"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/streaming/stats")
async def get_streaming_stats(
    manager: MarketDataManager = Depends(get_market_data_manager)
):
    """Get streaming statistics"""
    try:
        if not manager.stream_manager:
            return {"streaming": False, "message": "Streaming not active"}
        
        stats = manager.stream_manager.get_streaming_stats()
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# System Status and Monitoring Endpoints

@router.get("/status")
async def get_system_status(
    manager: MarketDataManager = Depends(get_market_data_manager)
):
    """Get system status"""
    try:
        health = await manager.health_check()
        stats = manager.get_system_stats()
        
        return {
            "health": health,
            "stats": stats,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/providers")
async def get_provider_status(
    manager: MarketDataManager = Depends(get_market_data_manager)
):
    """Get status of all data providers"""
    try:
        status = manager.get_provider_status()
        return status
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/monitoring/dashboard")
async def get_monitoring_dashboard(
    monitor: MarketDataMonitor = Depends(get_monitor)
):
    """Get comprehensive monitoring dashboard"""
    try:
        dashboard = monitor.get_monitoring_dashboard()
        return dashboard
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/monitoring/performance")
async def get_performance_report(
    hours: int = Query(24, description="Number of hours to analyze"),
    monitor: MarketDataMonitor = Depends(get_monitor)
):
    """Get performance report"""
    try:
        if hours < 1 or hours > 168:  # Max 1 week
            raise HTTPException(status_code=400, detail="Hours must be between 1 and 168")
        
        report = monitor.get_performance_report(hours)
        return report
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Cache Management Endpoints

@router.post("/cache/clear")
async def clear_cache(
    manager: MarketDataManager = Depends(get_market_data_manager),
    monitor: MarketDataMonitor = Depends(get_monitor)
):
    """Clear all cached data"""
    try:
        await manager.cache_manager.clear_all_cache()
        
        monitor.record_cache_operation("clear_all", False, 0)
        
        return {"status": "success", "message": "Cache cleared"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/cache/{symbol}")
async def invalidate_symbol_cache(
    symbol: str,
    manager: MarketDataManager = Depends(get_market_data_manager),
    monitor: MarketDataMonitor = Depends(get_monitor)
):
    """Invalidate cached data for a specific symbol"""
    try:
        await manager.cache_manager.invalidate_symbol(symbol)
        
        monitor.record_cache_operation("invalidate", False, 0)
        
        return {"status": "success", "message": f"Cache invalidated for {symbol}"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cache/stats")
async def get_cache_stats(
    manager: MarketDataManager = Depends(get_market_data_manager)
):
    """Get cache statistics"""
    try:
        stats = await manager.cache_manager.get_detailed_stats()
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Development and Testing Endpoints

@router.post("/test/notifications/{user_id}")
async def test_notifications(
    user_id: str,
    notification_types: List[str] = Query(["email"], description="Types of notifications to test"),
    manager: MarketDataManager = Depends(get_market_data_manager)
):
    """Test notification system"""
    try:
        if not manager.stream_manager:
            raise HTTPException(status_code=503, detail="Streaming service not available")
        
        notification_service = manager.stream_manager.alert_engine.notification_service
        results = await notification_service.send_test_notifications(user_id, notification_types)
        
        return {
            "user_id": user_id,
            "test_results": results,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config")
async def get_configuration():
    """Get current configuration (non-sensitive)"""
    try:
        return {
            "providers": {
                "primary": config.primary_provider.value,
                "fallback": [p.value for p in config.fallback_providers]
            },
            "cache": {
                "quote_ttl": config.quote_cache_ttl,
                "historical_ttl": config.historical_cache_ttl,
                "company_ttl": config.company_info_cache_ttl
            },
            "websocket": {
                "host": config.websocket_host,
                "port": config.websocket_port
            },
            "limits": {
                "max_alerts_per_user": config.max_alerts_per_user,
                "max_historical_days": config.max_historical_days,
                "max_concurrent_requests": config.max_concurrent_requests
            },
            "intervals": {
                "real_time_update": config.real_time_update_interval,
                "batch_update": config.batch_update_interval,
                "alert_check": config.alert_check_interval
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))