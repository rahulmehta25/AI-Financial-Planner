"""
Market data endpoints for retrieving financial market information
"""

from typing import Any, List, Optional
from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.core.exceptions import NotFoundError, DataProviderError
from app.models.user import User
from app.schemas.market_data import MarketDataResponse, MarketDataCreate
from app.services.market_data_service import MarketDataService

router = APIRouter()


@router.get("/quote/{symbol}", response_model=MarketDataResponse)
async def get_quote(
    symbol: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get current quote for a symbol
    """
    market_service = MarketDataService(db)
    quote = await market_service.get_current_quote(symbol.upper())
    
    if not quote:
        raise NotFoundError(f"Quote not found for symbol: {symbol}")
    
    return quote


@router.get("/historical/{symbol}")
async def get_historical_data(
    symbol: str,
    start_date: Optional[date] = Query(None, description="Start date for historical data"),
    end_date: Optional[date] = Query(None, description="End date for historical data"),
    period: Optional[str] = Query("1y", description="Period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get historical price data for a symbol
    """
    market_service = MarketDataService(db)
    
    try:
        historical_data = await market_service.get_historical_data(
            symbol.upper(),
            start_date=start_date,
            end_date=end_date,
            period=period
        )
        return historical_data
    except Exception as e:
        raise DataProviderError(f"Failed to retrieve historical data: {str(e)}")


@router.get("/search")
async def search_symbols(
    query: str = Query(..., description="Search query for symbols"),
    limit: int = Query(10, description="Maximum number of results"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Search for symbols by name or ticker
    """
    market_service = MarketDataService(db)
    results = await market_service.search_symbols(query, limit)
    return results


@router.get("/sectors")
async def get_sector_performance(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get sector performance data
    """
    market_service = MarketDataService(db)
    sector_data = await market_service.get_sector_performance()
    return sector_data


@router.get("/indices")
async def get_market_indices(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get major market indices data
    """
    market_service = MarketDataService(db)
    indices = await market_service.get_market_indices()
    return indices


@router.get("/economic-indicators")
async def get_economic_indicators(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get key economic indicators
    """
    market_service = MarketDataService(db)
    indicators = await market_service.get_economic_indicators()
    return indicators


@router.post("/watchlist")
async def add_to_watchlist(
    symbols: List[str],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Add symbols to user watchlist
    """
    market_service = MarketDataService(db)
    result = await market_service.add_to_watchlist(current_user.id, symbols)
    return result


@router.get("/watchlist")
async def get_watchlist(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get user's watchlist with current quotes
    """
    market_service = MarketDataService(db)
    watchlist = await market_service.get_watchlist(current_user.id)
    return watchlist


@router.delete("/watchlist/{symbol}")
async def remove_from_watchlist(
    symbol: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Remove symbol from user watchlist
    """
    market_service = MarketDataService(db)
    success = await market_service.remove_from_watchlist(current_user.id, symbol.upper())
    
    if not success:
        raise NotFoundError("Symbol not found in watchlist")
    
    return {"message": f"Removed {symbol} from watchlist"}


@router.get("/news/{symbol}")
async def get_symbol_news(
    symbol: str,
    limit: int = Query(10, description="Maximum number of news articles"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get recent news for a symbol
    """
    market_service = MarketDataService(db)
    news = await market_service.get_symbol_news(symbol.upper(), limit)
    return news


@router.get("/analysis/{symbol}")
async def get_technical_analysis(
    symbol: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get technical analysis indicators for a symbol
    """
    market_service = MarketDataService(db)
    analysis = await market_service.get_technical_analysis(symbol.upper())
    return analysis