"""
Portfolio Analytics API endpoints - Track and analyze investments
"""
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
import logging

from app.api.v1.deps import get_db, get_current_user, get_data_provider
from app.models.user import User
from app.models.all_models import Position, Account
from app.services.portfolio_analytics import PortfolioAnalytics
from app.services.data_providers.cached_provider import CachedDataProvider

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/portfolio/analysis")
async def get_portfolio_analysis(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    data_provider: CachedDataProvider = Depends(get_data_provider)
):
    """
    Get comprehensive portfolio analysis with performance metrics and AI recommendations
    """
    # Get user's positions
    query = select(Position).join(Account).where(
        and_(
            Account.user_id == current_user.id,
            Position.quantity > 0
        )
    )
    result = await db.execute(query)
    positions = result.scalars().all()
    
    if not positions:
        return {
            "message": "No holdings found. Import your transactions to see analysis.",
            "total_value": 0,
            "recommendations": [
                "📥 Import your transaction history from your broker",
                "📊 Track multiple investment accounts in one place",
                "🤖 Get AI-powered investment insights"
            ]
        }
    
    # Convert positions to holdings format
    holdings = []
    for position in positions:
        if position.instrument:
            holdings.append({
                "symbol": position.instrument.symbol,
                "quantity": position.quantity,
                "cost_basis": position.cost_basis
            })
    
    # Analyze portfolio
    analytics = PortfolioAnalytics(data_provider.provider)
    analysis = await analytics.analyze_portfolio(holdings)
    
    return {
        "portfolio_summary": {
            "total_value": float(analysis.total_value),
            "total_return": float(analysis.total_return),
            "annual_return": float(analysis.annual_return),
            "best_performer": analysis.best_performer,
            "worst_performer": analysis.worst_performer,
            "risk_score": analysis.risk_score,
            "diversification_score": analysis.diversification_score
        },
        "investments": [
            {
                "symbol": inv.symbol,
                "name": inv.name,
                "current_price": float(inv.current_price),
                "total_return": float(inv.total_return),
                "annual_return": float(inv.annual_return),
                "volatility": float(inv.volatility),
                "sharpe_ratio": float(inv.sharpe_ratio),
                "ytd_return": float(inv.ytd_return),
                "recommendation": inv.recommendation,
                "insights": inv.ai_insights
            }
            for inv in analysis.investments
        ],
        "recommendations": analysis.recommendations,
        "asset_allocation": {
            k: float(v) for k, v in analysis.asset_allocation.items()
        }
    }


@router.get("/investments/compare")
async def compare_investments(
    symbols: str,  # Comma-separated symbols
    period: str = "1y",  # 1y, 3y, 5y, ytd
    current_user: User = Depends(get_current_user),
    data_provider: CachedDataProvider = Depends(get_data_provider)
):
    """
    Compare performance of multiple investments
    """
    symbol_list = [s.strip().upper() for s in symbols.split(",")]
    
    if len(symbol_list) > 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 10 symbols for comparison"
        )
    
    comparisons = []
    for symbol in symbol_list:
        # Get current quote
        quote = await data_provider.get_quote(symbol)
        if not quote:
            continue
        
        # Get historical performance
        from datetime import date, timedelta
        end_date = date.today()
        
        if period == "ytd":
            start_date = date(end_date.year, 1, 1)
        elif period == "1y":
            start_date = end_date - timedelta(days=365)
        elif period == "3y":
            start_date = end_date - timedelta(days=365*3)
        elif period == "5y":
            start_date = end_date - timedelta(days=365*5)
        else:
            start_date = end_date - timedelta(days=365)
        
        historical = await data_provider.get_historical(symbol, start_date, end_date)
        
        if historical and len(historical) > 1:
            period_return = ((historical[-1].close - historical[0].close) / historical[0].close * 100)
            
            comparisons.append({
                "symbol": symbol,
                "current_price": float(quote.price),
                "period_return": float(period_return),
                "start_price": float(historical[0].close),
                "end_price": float(historical[-1].close),
                "period": period
            })
    
    # Sort by performance
    comparisons.sort(key=lambda x: x['period_return'], reverse=True)
    
    # Add rankings and insights
    for i, comp in enumerate(comparisons):
        comp['rank'] = i + 1
        
        if comp['period_return'] > 20:
            comp['insight'] = f"Strong performer - Up {comp['period_return']:.1f}% in {period}"
        elif comp['period_return'] < -10:
            comp['insight'] = f"Underperformer - Down {abs(comp['period_return']):.1f}% in {period}"
        else:
            comp['insight'] = f"Moderate performance - {comp['period_return']:.1f}% return in {period}"
    
    return {
        "period": period,
        "comparisons": comparisons,
        "best_performer": comparisons[0] if comparisons else None,
        "worst_performer": comparisons[-1] if comparisons else None,
        "recommendation": _generate_comparison_recommendation(comparisons)
    }


@router.get("/investments/recommendations/{symbol}")
async def get_investment_recommendations(
    symbol: str,
    current_user: User = Depends(get_current_user),
    data_provider: CachedDataProvider = Depends(get_data_provider)
):
    """
    Get AI-powered recommendations for a specific investment
    """
    symbol = symbol.upper()
    
    # Get current and historical data
    quote = await data_provider.get_quote(symbol)
    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Symbol {symbol} not found"
        )
    
    # Get historical data
    from datetime import date, timedelta
    end_date = date.today()
    one_year_ago = end_date - timedelta(days=365)
    
    historical = await data_provider.get_historical(symbol, one_year_ago, end_date)
    
    # Calculate metrics
    recommendations = []
    
    if historical and len(historical) > 1:
        # Calculate returns
        one_year_return = ((historical[-1].close - historical[0].close) / historical[0].close * 100)
        
        # Find 52-week high/low
        prices = [bar.close for bar in historical]
        week_52_high = max(prices)
        week_52_low = min(prices)
        
        # Distance from 52-week high
        distance_from_high = ((week_52_high - quote.price) / week_52_high * 100)
        
        # Generate recommendations based on data
        if one_year_return > 30:
            recommendations.append({
                "type": "performance",
                "message": f"Strong momentum with {one_year_return:.1f}% gain over past year",
                "action": "Consider taking partial profits if overweight in portfolio"
            })
        
        if distance_from_high > 20:
            recommendations.append({
                "type": "value",
                "message": f"Trading {distance_from_high:.1f}% below 52-week high",
                "action": "Potential buying opportunity if fundamentals remain strong"
            })
        
        if quote.price < week_52_low * 1.1:
            recommendations.append({
                "type": "caution",
                "message": "Near 52-week low",
                "action": "Review for potential value play or tax-loss harvesting"
            })
        
        # Volatility analysis
        import numpy as np
        returns = np.diff(prices) / prices[:-1]
        volatility = np.std(returns) * np.sqrt(252) * 100
        
        if volatility > 40:
            recommendations.append({
                "type": "risk",
                "message": f"High volatility at {volatility:.1f}% annualized",
                "action": "Size position appropriately for risk tolerance"
            })
    
    # Add general recommendations
    recommendations.append({
        "type": "diversification",
        "message": "Ensure proper portfolio diversification",
        "action": "No single holding should exceed 10% of portfolio"
    })
    
    return {
        "symbol": symbol,
        "current_price": float(quote.price),
        "analysis": {
            "52_week_high": float(week_52_high) if historical else None,
            "52_week_low": float(week_52_low) if historical else None,
            "one_year_return": float(one_year_return) if historical else None,
            "volatility": float(volatility) if historical else None
        },
        "recommendations": recommendations,
        "data_disclaimer": "Based on 15-minute delayed market data"
    }


def _generate_comparison_recommendation(comparisons: List[Dict]) -> str:
    """Generate recommendation based on comparison results"""
    if not comparisons:
        return "Add symbols to compare investment performance"
    
    best = comparisons[0]
    worst = comparisons[-1]
    
    if best['period_return'] > 50:
        return f"🚀 {best['symbol']} shows exceptional performance. Consider diversifying gains."
    elif worst['period_return'] < -30:
        return f"⚠️ {worst['symbol']} has significant losses. Review for tax-loss harvesting."
    else:
        avg_return = sum(c['period_return'] for c in comparisons) / len(comparisons)
        if avg_return > 15:
            return f"✅ Portfolio showing strong performance with {avg_return:.1f}% average return"
        else:
            return f"📊 Mixed performance. Focus on long-term investment strategy"