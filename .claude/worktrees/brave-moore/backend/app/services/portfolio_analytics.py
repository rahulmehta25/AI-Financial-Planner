"""
Portfolio Analytics Service - Track and analyze investment performance
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, date, timedelta
from decimal import Decimal
import numpy as np
from dataclasses import dataclass
import logging

from app.services.data_providers.yfinance_provider import YFinanceProvider

logger = logging.getLogger(__name__)


@dataclass
class InvestmentPerformance:
    """Performance metrics for an investment"""
    symbol: str
    name: str
    current_price: Decimal
    total_return: Decimal
    annual_return: Decimal
    volatility: Decimal
    sharpe_ratio: Decimal
    max_drawdown: Decimal
    ytd_return: Decimal
    one_year_return: Optional[Decimal]
    three_year_return: Optional[Decimal]
    five_year_return: Optional[Decimal]
    recommendation: str
    ai_insights: List[str]


@dataclass
class PortfolioAnalysis:
    """Complete portfolio analysis"""
    total_value: Decimal
    total_return: Decimal
    annual_return: Decimal
    best_performer: str
    worst_performer: str
    risk_score: int  # 1-10
    diversification_score: int  # 1-10
    investments: List[InvestmentPerformance]
    recommendations: List[str]
    asset_allocation: Dict[str, Decimal]


class PortfolioAnalytics:
    """Analyze portfolio performance and provide data-backed recommendations"""
    
    def __init__(self, data_provider: YFinanceProvider):
        self.data_provider = data_provider
        
    async def analyze_portfolio(self, holdings: List[Dict[str, Any]]) -> PortfolioAnalysis:
        """
        Analyze portfolio performance and provide recommendations
        
        Args:
            holdings: List of dicts with 'symbol', 'quantity', 'cost_basis'
        """
        investments = []
        total_value = Decimal("0")
        total_cost = Decimal("0")
        
        for holding in holdings:
            symbol = holding['symbol']
            quantity = Decimal(str(holding['quantity']))
            cost_basis = Decimal(str(holding['cost_basis']))
            
            # Get current and historical data
            performance = await self._analyze_investment(symbol, quantity, cost_basis)
            if performance:
                investments.append(performance)
                total_value += quantity * performance.current_price
                total_cost += cost_basis
        
        # Calculate portfolio metrics
        total_return = ((total_value - total_cost) / total_cost * 100) if total_cost > 0 else Decimal("0")
        
        # Sort by performance
        investments.sort(key=lambda x: x.total_return, reverse=True)
        best_performer = investments[0].symbol if investments else None
        worst_performer = investments[-1].symbol if investments else None
        
        # Calculate risk and diversification scores
        risk_score = self._calculate_risk_score(investments)
        diversification_score = self._calculate_diversification_score(investments)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            investments, 
            risk_score, 
            diversification_score
        )
        
        # Calculate asset allocation
        asset_allocation = self._calculate_asset_allocation(investments, total_value)
        
        return PortfolioAnalysis(
            total_value=total_value,
            total_return=total_return,
            annual_return=total_return / 3,  # Simplified - should use actual holding period
            best_performer=best_performer,
            worst_performer=worst_performer,
            risk_score=risk_score,
            diversification_score=diversification_score,
            investments=investments,
            recommendations=recommendations,
            asset_allocation=asset_allocation
        )
    
    async def _analyze_investment(
        self, 
        symbol: str, 
        quantity: Decimal, 
        cost_basis: Decimal
    ) -> Optional[InvestmentPerformance]:
        """Analyze individual investment performance"""
        try:
            # Get current quote
            quote = await self.data_provider.get_quote(symbol)
            if not quote:
                return None
            
            # Get historical data for different periods
            end_date = date.today()
            one_year_ago = end_date - timedelta(days=365)
            three_years_ago = end_date - timedelta(days=365*3)
            five_years_ago = end_date - timedelta(days=365*5)
            ytd_start = date(end_date.year, 1, 1)
            
            # Fetch historical data
            historical_1y = await self.data_provider.get_historical(symbol, one_year_ago, end_date)
            historical_3y = await self.data_provider.get_historical(symbol, three_years_ago, end_date)
            historical_ytd = await self.data_provider.get_historical(symbol, ytd_start, end_date)
            
            # Calculate returns
            current_value = quantity * quote.price
            total_return = ((current_value - cost_basis) / cost_basis * 100) if cost_basis > 0 else Decimal("0")
            
            # Calculate period returns
            ytd_return = self._calculate_period_return(historical_ytd) if historical_ytd else Decimal("0")
            one_year_return = self._calculate_period_return(historical_1y) if historical_1y else None
            three_year_return = self._calculate_annualized_return(historical_3y, 3) if historical_3y else None
            
            # Calculate volatility and Sharpe ratio
            volatility = self._calculate_volatility(historical_1y) if historical_1y else Decimal("0")
            sharpe_ratio = self._calculate_sharpe_ratio(one_year_return, volatility) if one_year_return else Decimal("0")
            
            # Calculate max drawdown
            max_drawdown = self._calculate_max_drawdown(historical_1y) if historical_1y else Decimal("0")
            
            # Generate AI insights
            ai_insights = self._generate_investment_insights(
                symbol=symbol,
                total_return=total_return,
                volatility=volatility,
                sharpe_ratio=sharpe_ratio,
                ytd_return=ytd_return
            )
            
            # Generate recommendation
            recommendation = self._generate_investment_recommendation(
                total_return=total_return,
                volatility=volatility,
                sharpe_ratio=sharpe_ratio
            )
            
            return InvestmentPerformance(
                symbol=symbol,
                name=symbol,  # Would be updated from company info
                current_price=quote.price,
                total_return=total_return,
                annual_return=total_return / 3,  # Simplified
                volatility=volatility,
                sharpe_ratio=sharpe_ratio,
                max_drawdown=max_drawdown,
                ytd_return=ytd_return,
                one_year_return=one_year_return,
                three_year_return=three_year_return,
                five_year_return=None,  # Would need 5 year data
                recommendation=recommendation,
                ai_insights=ai_insights
            )
            
        except Exception as e:
            logger.error(f"Failed to analyze {symbol}: {e}")
            return None
    
    def _calculate_period_return(self, historical_data: List) -> Decimal:
        """Calculate return over a period"""
        if not historical_data or len(historical_data) < 2:
            return Decimal("0")
        
        start_price = historical_data[0].close
        end_price = historical_data[-1].close
        return ((end_price - start_price) / start_price * 100)
    
    def _calculate_annualized_return(self, historical_data: List, years: int) -> Decimal:
        """Calculate annualized return"""
        period_return = self._calculate_period_return(historical_data)
        if period_return == 0:
            return Decimal("0")
        
        # Convert to annualized
        return ((1 + period_return/100) ** (1/years) - 1) * 100
    
    def _calculate_volatility(self, historical_data: List) -> Decimal:
        """Calculate annualized volatility"""
        if not historical_data or len(historical_data) < 2:
            return Decimal("0")
        
        # Calculate daily returns
        prices = [float(bar.close) for bar in historical_data]
        returns = np.diff(prices) / prices[:-1]
        
        # Annualize the volatility (252 trading days)
        daily_vol = np.std(returns)
        annual_vol = daily_vol * np.sqrt(252)
        
        return Decimal(str(annual_vol * 100))
    
    def _calculate_sharpe_ratio(self, annual_return: Decimal, volatility: Decimal) -> Decimal:
        """Calculate Sharpe ratio (using 2% risk-free rate)"""
        if volatility == 0:
            return Decimal("0")
        
        risk_free_rate = Decimal("2")  # 2% risk-free rate
        excess_return = annual_return - risk_free_rate
        return excess_return / volatility
    
    def _calculate_max_drawdown(self, historical_data: List) -> Decimal:
        """Calculate maximum drawdown"""
        if not historical_data:
            return Decimal("0")
        
        prices = [float(bar.close) for bar in historical_data]
        peak = prices[0]
        max_dd = 0
        
        for price in prices:
            if price > peak:
                peak = price
            dd = (peak - price) / peak
            if dd > max_dd:
                max_dd = dd
        
        return Decimal(str(max_dd * 100))
    
    def _calculate_risk_score(self, investments: List[InvestmentPerformance]) -> int:
        """Calculate portfolio risk score (1-10, 10 being highest risk)"""
        if not investments:
            return 5
        
        avg_volatility = sum(inv.volatility for inv in investments) / len(investments)
        
        # Map volatility to risk score
        if avg_volatility < 10:
            return 2
        elif avg_volatility < 15:
            return 3
        elif avg_volatility < 20:
            return 5
        elif avg_volatility < 30:
            return 7
        else:
            return 9
    
    def _calculate_diversification_score(self, investments: List[InvestmentPerformance]) -> int:
        """Calculate diversification score (1-10, 10 being best diversified)"""
        num_holdings = len(investments)
        
        if num_holdings < 3:
            return 2
        elif num_holdings < 5:
            return 4
        elif num_holdings < 10:
            return 6
        elif num_holdings < 20:
            return 8
        else:
            return 10
    
    def _calculate_asset_allocation(
        self, 
        investments: List[InvestmentPerformance],
        total_value: Decimal
    ) -> Dict[str, Decimal]:
        """Calculate asset allocation percentages"""
        allocation = {}
        
        for inv in investments:
            # This is simplified - would need actual position values
            allocation[inv.symbol] = Decimal("10")  # Placeholder
        
        return allocation
    
    def _generate_investment_insights(
        self, 
        symbol: str,
        total_return: Decimal,
        volatility: Decimal,
        sharpe_ratio: Decimal,
        ytd_return: Decimal
    ) -> List[str]:
        """Generate AI-backed insights for an investment"""
        insights = []
        
        # Performance insight
        if total_return > 20:
            insights.append(f"Strong performer with {total_return:.1f}% total return")
        elif total_return < -10:
            insights.append(f"Underperforming with {total_return:.1f}% loss")
        
        # Volatility insight
        if volatility > 30:
            insights.append(f"High volatility ({volatility:.1f}%) suggests higher risk")
        elif volatility < 15:
            insights.append(f"Low volatility ({volatility:.1f}%) indicates stability")
        
        # Sharpe ratio insight
        if sharpe_ratio > 1:
            insights.append("Excellent risk-adjusted returns (Sharpe > 1)")
        elif sharpe_ratio < 0:
            insights.append("Poor risk-adjusted returns (negative Sharpe)")
        
        # YTD insight
        if ytd_return > 10:
            insights.append(f"Strong year-to-date performance: {ytd_return:.1f}%")
        
        return insights
    
    def _generate_investment_recommendation(
        self,
        total_return: Decimal,
        volatility: Decimal,
        sharpe_ratio: Decimal
    ) -> str:
        """Generate recommendation for an investment"""
        if sharpe_ratio > 1 and total_return > 15:
            return "STRONG HOLD - Excellent risk-adjusted returns"
        elif sharpe_ratio > 0.5 and total_return > 0:
            return "HOLD - Positive performance with acceptable risk"
        elif total_return < -20:
            return "REVIEW - Consider tax-loss harvesting"
        elif volatility > 40:
            return "MONITOR - High volatility requires attention"
        else:
            return "HOLD - Performance within normal range"
    
    def _generate_recommendations(
        self,
        investments: List[InvestmentPerformance],
        risk_score: int,
        diversification_score: int
    ) -> List[str]:
        """Generate portfolio-level recommendations"""
        recommendations = []
        
        # Diversification recommendation
        if diversification_score < 5:
            recommendations.append(
                "📊 Low diversification detected. Consider adding holdings in different sectors to reduce risk."
            )
        
        # Risk recommendation
        if risk_score > 7:
            recommendations.append(
                "⚠️ High portfolio risk. Consider adding stable, dividend-paying stocks or bonds."
            )
        elif risk_score < 3:
            recommendations.append(
                "📈 Low risk portfolio. Consider growth stocks for potentially higher returns."
            )
        
        # Performance recommendations
        if investments:
            best = investments[0]
            worst = investments[-1]
            
            if best.total_return > 50:
                recommendations.append(
                    f"🎯 {best.symbol} is significantly outperforming. Consider taking some profits."
                )
            
            if worst.total_return < -30:
                recommendations.append(
                    f"🔍 {worst.symbol} has declined significantly. Review for tax-loss harvesting opportunity."
                )
        
        # Asset allocation
        recommendations.append(
            "💡 Review asset allocation quarterly to maintain target risk profile."
        )
        
        return recommendations