"""
Portfolio management and analysis endpoints
"""

from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta

from app.api.deps import get_current_active_user, get_db
from app.models.user import User

router = APIRouter()


@router.get("/overview")
async def get_portfolio_overview(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Get portfolio overview and summary"""
    return {
        "portfolio_summary": {
            "total_value": 125000.75,
            "today_change": 2340.50,
            "today_change_percent": 1.87,
            "total_gain_loss": 18750.25,
            "total_gain_loss_percent": 17.65,
            "cost_basis": 106250.50,
            "last_updated": datetime.utcnow().isoformat()
        },
        "performance_metrics": {
            "ytd_return": 12.3,
            "one_year_return": 18.7,
            "three_year_return": 9.2,
            "five_year_return": 11.8,
            "sharpe_ratio": 1.42,
            "beta": 0.95,
            "alpha": 2.1,
            "volatility": 14.5
        },
        "quick_stats": {
            "number_of_holdings": 12,
            "sectors_represented": 8,
            "dividend_yield": 2.8,
            "expense_ratio": 0.12
        }
    }


@router.get("/holdings")
async def get_portfolio_holdings(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Get detailed portfolio holdings"""
    return {
        "holdings": [
            {
                "symbol": "VTI",
                "name": "Vanguard Total Stock Market ETF",
                "asset_class": "equity",
                "shares": 150.0,
                "current_price": 245.67,
                "market_value": 36850.50,
                "cost_basis": 32500.00,
                "gain_loss": 4350.50,
                "gain_loss_percent": 13.39,
                "weight_percent": 29.5,
                "sector": "diversified"
            },
            {
                "symbol": "BND", 
                "name": "Vanguard Total Bond Market ETF",
                "asset_class": "fixed_income",
                "shares": 400.0,
                "current_price": 78.25,
                "market_value": 31300.00,
                "cost_basis": 32000.00,
                "gain_loss": -700.00,
                "gain_loss_percent": -2.19,
                "weight_percent": 25.0,
                "sector": "bonds"
            },
            {
                "symbol": "VEA",
                "name": "Vanguard FTSE Developed Markets ETF", 
                "asset_class": "equity",
                "shares": 300.0,
                "current_price": 48.92,
                "market_value": 14676.00,
                "cost_basis": 13500.00,
                "gain_loss": 1176.00,
                "gain_loss_percent": 8.71,
                "weight_percent": 11.7,
                "sector": "international"
            },
            {
                "symbol": "VWO",
                "name": "Vanguard Emerging Markets ETF",
                "asset_class": "equity", 
                "shares": 200.0,
                "current_price": 42.15,
                "market_value": 8430.00,
                "cost_basis": 8800.00,
                "gain_loss": -370.00,
                "gain_loss_percent": -4.20,
                "weight_percent": 6.7,
                "sector": "emerging_markets"
            },
            {
                "symbol": "VNQ",
                "name": "Vanguard Real Estate ETF",
                "asset_class": "real_estate",
                "shares": 100.0,
                "current_price": 89.50,
                "market_value": 8950.00,
                "cost_basis": 9200.00,
                "gain_loss": -250.00,
                "gain_loss_percent": -2.72,
                "weight_percent": 7.2,
                "sector": "real_estate"
            }
        ],
        "summary": {
            "total_holdings": 5,
            "total_market_value": 125000.75,
            "total_cost_basis": 106250.50,
            "total_gain_loss": 18750.25,
            "total_gain_loss_percent": 17.65
        },
        "asset_allocation": {
            "equity": 60.2,
            "fixed_income": 25.0,
            "real_estate": 7.2,
            "cash": 7.6
        }
    }


@router.get("/performance")
async def get_portfolio_performance(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    period: str = "1Y"
) -> Any:
    """Get portfolio performance data and charts"""
    # Generate sample performance data
    end_date = datetime.now()
    days = 365 if period == "1Y" else 30 if period == "1M" else 7
    start_date = end_date - timedelta(days=days)
    
    performance_data = []
    base_value = 108000.0
    
    for i in range(days):
        date = start_date + timedelta(days=i)
        # Simple mock data with some volatility
        value = base_value + (i * 45) + (i % 7 * 200) - (i % 11 * 150)
        performance_data.append({
            "date": date.strftime("%Y-%m-%d"),
            "portfolio_value": round(value, 2),
            "daily_return": round((value / (base_value + ((i-1) * 45)) - 1) * 100, 2) if i > 0 else 0.0
        })
    
    return {
        "performance_data": performance_data,
        "period": period,
        "benchmarks": {
            "sp500": {
                "return": 11.8,
                "label": "S&P 500"
            },
            "total_bond": {
                "return": -2.1,
                "label": "Total Bond Market"  
            },
            "balanced_portfolio": {
                "return": 8.4,
                "label": "60/40 Portfolio"
            }
        },
        "portfolio_metrics": {
            "total_return": 17.65,
            "annualized_return": 12.3,
            "volatility": 14.5,
            "max_drawdown": -8.2,
            "best_day": 3.4,
            "worst_day": -4.1,
            "up_days": 65.2,
            "down_days": 34.8
        }
    }


@router.get("/allocation")
async def get_portfolio_allocation(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Get detailed portfolio allocation breakdown"""
    return {
        "target_allocation": {
            "equity": 60.0,
            "fixed_income": 25.0,
            "real_estate": 10.0,
            "cash": 5.0
        },
        "current_allocation": {
            "equity": 60.2,
            "fixed_income": 25.0,
            "real_estate": 7.2,
            "cash": 7.6
        },
        "allocation_drift": {
            "equity": 0.2,
            "fixed_income": 0.0,
            "real_estate": -2.8,
            "cash": 2.6
        },
        "rebalancing_needed": True,
        "rebalancing_suggestions": [
            {
                "action": "sell",
                "asset": "cash",
                "amount": 2500.00,
                "reason": "Overweight position"
            },
            {
                "action": "buy",
                "asset": "real_estate",
                "amount": 2500.00,
                "reason": "Underweight position"
            }
        ],
        "sector_allocation": {
            "technology": 18.5,
            "healthcare": 12.3,
            "financials": 10.8,
            "consumer_discretionary": 8.7,
            "industrials": 7.2,
            "bonds": 25.0,
            "real_estate": 7.2,
            "international": 11.7,
            "emerging_markets": 6.7,
            "cash": 7.6
        },
        "geographic_allocation": {
            "us_domestic": 70.5,
            "international_developed": 11.7,
            "emerging_markets": 6.7,
            "bonds": 25.0,
            "cash": 7.6
        },
        "risk_metrics": {
            "portfolio_beta": 0.95,
            "expected_annual_return": 7.8,
            "expected_volatility": 14.5,
            "sharpe_ratio": 1.42,
            "risk_adjusted_return": "Excellent"
        }
    }