"""
Portfolio management endpoints
"""
from typing import List, Optional, Dict
from datetime import date
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.api.v1.deps import get_current_user, get_db, get_data_provider
from app.models.user import User
from app.models.all_models import Account, Position, Transaction
from app.schemas.portfolio import (
    PortfolioResponse,
    PositionResponse,
    PerformanceMetrics,
    HoldingDetail
)
# from app.services.portfolio.calculator import PortfolioCalculator  # TODO: implement
from app.services.data_providers.cached_provider import CachedDataProvider

router = APIRouter()


@router.get("/positions", response_model=List[PositionResponse])
async def get_positions(
    account_id: Optional[str] = Query(None, description="Filter by account ID"),
    symbol: Optional[str] = Query(None, description="Filter by symbol"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all positions for the current user"""
    query = select(Position).join(Account).where(
        Account.user_id == current_user.id
    )
    
    if account_id:
        query = query.where(Position.account_id == account_id)
    if symbol:
        query = query.where(Position.symbol == symbol.upper())
    
    result = await db.execute(query)
    positions = result.scalars().all()
    
    return [
        PositionResponse(
            id=str(pos.id),
            account_id=str(pos.account_id),
            symbol=pos.symbol,
            quantity=float(pos.quantity),
            average_cost=float(pos.average_cost),
            current_price=float(pos.current_price) if pos.current_price else None,
            market_value=float(pos.quantity * (pos.current_price or pos.average_cost)),
            unrealized_pnl=float((pos.current_price or pos.average_cost - pos.average_cost) * pos.quantity),
            realized_pnl=float(pos.realized_pnl) if pos.realized_pnl else 0,
            updated_at=pos.updated_at
        )
        for pos in positions
    ]


@router.get("/summary", response_model=PortfolioResponse)
async def get_portfolio_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    data_provider: CachedDataProvider = Depends(get_data_provider)
):
    """Get portfolio summary with current market values"""
    # Get all user positions
    query = select(Position).join(Account).where(
        Account.user_id == current_user.id,
        Position.quantity > 0
    )
    result = await db.execute(query)
    positions = result.scalars().all()
    
    if not positions:
        return PortfolioResponse(
            total_value=0,
            total_cost=0,
            total_pnl=0,
            total_pnl_percentage=0,
            holdings=[],
            performance_metrics=PerformanceMetrics(
                daily_return=0,
                weekly_return=0,
                monthly_return=0,
                yearly_return=0,
                volatility=0,
                sharpe_ratio=0,
                max_drawdown=0
            )
        )
    
    # Get current prices for all symbols
    symbols = list(set(pos.symbol for pos in positions))
    quotes = await data_provider.get_quotes(symbols)
    
    # Calculate portfolio metrics
    holdings = []
    total_value = Decimal(0)
    total_cost = Decimal(0)
    
    for pos in positions:
        quote = quotes.get(pos.symbol)
        current_price = quote.price if quote else pos.current_price or pos.average_cost
        
        market_value = pos.quantity * current_price
        cost_basis = pos.quantity * pos.average_cost
        unrealized_pnl = market_value - cost_basis
        
        holdings.append(HoldingDetail(
            symbol=pos.symbol,
            quantity=float(pos.quantity),
            average_cost=float(pos.average_cost),
            current_price=float(current_price),
            market_value=float(market_value),
            cost_basis=float(cost_basis),
            unrealized_pnl=float(unrealized_pnl),
            unrealized_pnl_percentage=float((unrealized_pnl / cost_basis * 100) if cost_basis > 0 else 0),
            weight=0  # Will calculate after total
        ))
        
        total_value += market_value
        total_cost += cost_basis
    
    # Calculate weights
    for holding in holdings:
        holding.weight = float((Decimal(holding.market_value) / total_value * 100) if total_value > 0 else 0)
    
    # Sort by weight descending
    holdings.sort(key=lambda x: x.weight, reverse=True)
    
    total_pnl = total_value - total_cost
    total_pnl_percentage = float((total_pnl / total_cost * 100) if total_cost > 0 else 0)
    
    # TODO: Calculate real performance metrics from historical data
    performance_metrics = PerformanceMetrics(
        daily_return=0,
        weekly_return=0,
        monthly_return=0,
        yearly_return=0,
        volatility=0,
        sharpe_ratio=0,
        max_drawdown=0
    )
    
    return PortfolioResponse(
        total_value=float(total_value),
        total_cost=float(total_cost),
        total_pnl=float(total_pnl),
        total_pnl_percentage=total_pnl_percentage,
        holdings=holdings,
        performance_metrics=performance_metrics
    )
