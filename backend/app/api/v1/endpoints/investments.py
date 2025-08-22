"""
Investment portfolio management endpoints
"""

from typing import Any, List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.core.exceptions import NotFoundError
from app.models.user import User
from app.schemas.investment import InvestmentCreate, InvestmentResponse, InvestmentUpdate
from app.services.investment_service import InvestmentService

router = APIRouter()


@router.post("", response_model=InvestmentResponse, status_code=status.HTTP_201_CREATED)
async def create_investment(
    investment_data: InvestmentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Add a new investment to portfolio
    """
    investment_service = InvestmentService(db)
    investment = await investment_service.create_investment(current_user.id, investment_data)
    return investment


@router.get("", response_model=List[InvestmentResponse])
async def get_user_investments(
    skip: int = 0,
    limit: int = 100,
    investment_type: Optional[str] = Query(None, description="Filter by investment type"),
    account_type: Optional[str] = Query(None, description="Filter by account type"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get all investments for current user with optional filters
    """
    investment_service = InvestmentService(db)
    investments = await investment_service.get_user_investments(
        current_user.id,
        skip=skip,
        limit=limit,
        investment_type=investment_type,
        account_type=account_type
    )
    return investments


@router.get("/{investment_id}", response_model=InvestmentResponse)
async def get_investment(
    investment_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get specific investment by ID
    """
    investment_service = InvestmentService(db)
    investment = await investment_service.get_investment(investment_id, current_user.id)
    
    if not investment:
        raise NotFoundError("Investment not found")
    
    return investment


@router.put("/{investment_id}", response_model=InvestmentResponse)
async def update_investment(
    investment_id: UUID,
    investment_update: InvestmentUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Update existing investment
    """
    investment_service = InvestmentService(db)
    investment = await investment_service.update_investment(
        investment_id, current_user.id, investment_update
    )
    
    if not investment:
        raise NotFoundError("Investment not found")
    
    return investment


@router.delete("/{investment_id}")
async def delete_investment(
    investment_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Delete investment (mark as sold)
    """
    investment_service = InvestmentService(db)
    success = await investment_service.delete_investment(investment_id, current_user.id)
    
    if not success:
        raise NotFoundError("Investment not found")
    
    return {"message": "Investment deleted successfully"}


@router.get("/portfolio/summary")
async def get_portfolio_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get portfolio summary with total value, allocation, and performance
    """
    investment_service = InvestmentService(db)
    summary = await investment_service.get_portfolio_summary(current_user.id)
    return summary


@router.get("/portfolio/allocation")
async def get_portfolio_allocation(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get portfolio asset allocation breakdown
    """
    investment_service = InvestmentService(db)
    allocation = await investment_service.get_portfolio_allocation(current_user.id)
    return allocation


@router.get("/portfolio/performance")
async def get_portfolio_performance(
    days: int = Query(30, description="Number of days for performance calculation"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get portfolio performance metrics over specified period
    """
    investment_service = InvestmentService(db)
    performance = await investment_service.get_portfolio_performance(current_user.id, days)
    return performance


@router.post("/portfolio/rebalance")
async def rebalance_portfolio(
    target_allocation: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Generate rebalancing recommendations based on target allocation
    """
    investment_service = InvestmentService(db)
    recommendations = await investment_service.generate_rebalancing_plan(
        current_user.id, target_allocation
    )
    return recommendations


@router.post("/sync-prices")
async def sync_investment_prices(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Sync current prices for all user investments
    """
    investment_service = InvestmentService(db)
    result = await investment_service.sync_investment_prices(current_user.id)
    return result