"""
Portfolio schemas for API responses
"""
from typing import List, Optional, Dict
from datetime import datetime
from pydantic import BaseModel, Field


class PositionResponse(BaseModel):
    """Position detail response"""
    id: str
    account_id: str
    symbol: str
    quantity: float
    average_cost: float
    current_price: Optional[float]
    market_value: float
    unrealized_pnl: float
    realized_pnl: float
    updated_at: datetime
    
    class Config:
        from_attributes = True


class HoldingDetail(BaseModel):
    """Individual holding in portfolio"""
    symbol: str
    quantity: float
    average_cost: float
    current_price: float
    market_value: float
    cost_basis: float
    unrealized_pnl: float
    unrealized_pnl_percentage: float
    weight: float = Field(description="Percentage of portfolio")


class PerformanceMetrics(BaseModel):
    """Portfolio performance metrics"""
    daily_return: float
    weekly_return: float
    monthly_return: float
    yearly_return: float
    volatility: float
    sharpe_ratio: float
    max_drawdown: float


class PortfolioResponse(BaseModel):
    """Complete portfolio summary"""
    total_value: float
    total_cost: float
    total_pnl: float
    total_pnl_percentage: float
    holdings: List[HoldingDetail]
    performance_metrics: PerformanceMetrics


class RebalanceRequest(BaseModel):
    """Rebalancing request"""
    target_allocations: Dict[str, float] = Field(
        description="Symbol to target percentage mapping"
    )
    account_id: str


class RebalanceResponse(BaseModel):
    """Rebalancing calculation response"""
    portfolio_value: float
    current_holdings: Dict[str, Dict]
    target_allocations: Dict[str, float]
    required_trades: List[Dict]