"""
Automated Cash Flow Analysis Service

This module provides comprehensive cash flow analysis including income tracking,
expense categorization, trend analysis, and financial health scoring.
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
from collections import defaultdict
import statistics

import numpy as np
import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import ValidationError
from .plaid_service import Transaction, BankAccount
from .transaction_categorizer import CategoryPrediction, transaction_categorizer

logger = logging.getLogger(__name__)


@dataclass
class CashFlowPeriod:
    """Cash flow data for a specific period"""
    period_start: datetime
    period_end: datetime
    total_income: float
    total_expenses: float
    net_cash_flow: float
    income_by_category: Dict[str, float]
    expenses_by_category: Dict[str, float]
    transaction_count: int
    average_transaction_size: float


@dataclass
class CashFlowTrend:
    """Cash flow trend analysis"""
    period: str  # 'monthly', 'quarterly', 'yearly'
    trend_direction: str  # 'increasing', 'decreasing', 'stable'
    trend_percentage: float
    volatility: float
    seasonal_patterns: Dict[str, float]
    growth_rate: float


@dataclass
class FinancialHealthScore:
    """Financial health assessment"""
    overall_score: float  # 0-100
    income_stability: float
    expense_control: float
    savings_rate: float
    debt_ratio: float
    emergency_fund_months: float
    recommendations: List[str]


@dataclass
class BudgetVariance:
    """Budget vs actual spending variance"""
    category: str
    budgeted_amount: float
    actual_amount: float
    variance_amount: float
    variance_percentage: float
    status: str  # 'over_budget', 'under_budget', 'on_track'


class CashFlowAnalyzer:
    """
    Automated cash flow analysis service.
    
    Features:
    - Income and expense tracking
    - Trend analysis and forecasting
    - Financial health scoring
    - Budget variance analysis
    - Savings rate calculation
    - Cash flow projections
    - Anomaly detection
    """
    
    def __init__(self):
        self.lookback_months = settings.CASH_FLOW_ANALYSIS_LOOKBACK_MONTHS
    
    async def analyze_cash_flow(
        self,
        transactions: List[Transaction],
        accounts: List[BankAccount],
        categorized_transactions: Optional[List[CategoryPrediction]] = None,
        user_id: Optional[str] = None,
        analysis_period: Optional[str] = 'monthly'
    ) -> Dict[str, Any]:
        """
        Comprehensive cash flow analysis
        
        Args:
            transactions: List of transactions to analyze
            accounts: List of bank accounts
            categorized_transactions: Pre-categorized transactions
            user_id: User identifier
            analysis_period: Analysis period ('monthly', 'quarterly', 'yearly')
            
        Returns:
            Complete cash flow analysis report
        """
        try:
            # Categorize transactions if not provided
            if not categorized_transactions:
                categorized_transactions = await transaction_categorizer.categorize_transactions_batch(
                    transactions, user_id
                )
            
            # Create DataFrame for analysis
            df = self._create_transaction_dataframe(transactions, categorized_transactions)
            
            # Perform various analyses
            period_analysis = self._analyze_by_period(df, analysis_period)
            trend_analysis = self._analyze_trends(df, analysis_period)
            health_score = self._calculate_financial_health(df, accounts)
            savings_analysis = self._analyze_savings_patterns(df)
            forecasting = self._forecast_cash_flow(df, months_ahead=6)
            
            # Generate insights and recommendations
            insights = self._generate_insights(
                period_analysis, trend_analysis, health_score, savings_analysis
            )
            
            analysis_result = {
                'user_id': user_id,
                'analysis_timestamp': datetime.utcnow().isoformat(),
                'analysis_period': analysis_period,
                'data_period': {
                    'start_date': min(t.date for t in transactions).isoformat(),
                    'end_date': max(t.date for t in transactions).isoformat(),
                    'total_transactions': len(transactions)
                },
                'period_analysis': [period.__dict__ for period in period_analysis],
                'trend_analysis': trend_analysis.__dict__,
                'financial_health': health_score.__dict__,
                'savings_analysis': savings_analysis,
                'cash_flow_forecast': forecasting,
                'insights': insights,
                'recommendations': self._generate_recommendations(health_score, trend_analysis)
            }
            
            logger.info(f"Completed cash flow analysis for user {user_id}")
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error in cash flow analysis: {str(e)}")
            raise ValidationError("Failed to analyze cash flow")
    
    def _create_transaction_dataframe(
        self,
        transactions: List[Transaction],
        categorized_transactions: List[CategoryPrediction]
    ) -> pd.DataFrame:
        """Create pandas DataFrame from transactions for analysis"""
        try:
            data = []
            
            for i, transaction in enumerate(transactions):
                category_prediction = categorized_transactions[i] if i < len(categorized_transactions) else None
                
                data.append({
                    'transaction_id': transaction.transaction_id,
                    'date': transaction.date,
                    'amount': transaction.amount,
                    'abs_amount': abs(transaction.amount),
                    'description': transaction.name,
                    'merchant_name': transaction.merchant_name,
                    'category': category_prediction.category if category_prediction else 'other',
                    'subcategory': category_prediction.subcategory if category_prediction else 'uncategorized',
                    'is_income': transaction.amount < 0,  # Negative amounts are income
                    'is_expense': transaction.amount > 0,
                    'pending': transaction.pending,
                    'currency': transaction.currency,
                    'month': transaction.date.strftime('%Y-%m'),
                    'quarter': f"{transaction.date.year}-Q{(transaction.date.month-1)//3 + 1}",
                    'year': transaction.date.year,
                    'day_of_week': transaction.date.weekday(),
                    'day_of_month': transaction.date.day
                })
            
            df = pd.DataFrame(data)
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')
            
            return df
            
        except Exception as e:
            logger.error(f"Error creating transaction DataFrame: {str(e)}")
            raise ValidationError("Failed to process transaction data")
    
    def _analyze_by_period(self, df: pd.DataFrame, period: str) -> List[CashFlowPeriod]:
        """Analyze cash flow by time periods"""
        try:
            periods = []
            
            if period == 'monthly':
                groupby_column = 'month'
                date_format = '%Y-%m'
            elif period == 'quarterly':
                groupby_column = 'quarter'
                date_format = '%Y-Q%q'
            else:  # yearly
                groupby_column = 'year'
                date_format = '%Y'
            
            grouped = df.groupby(groupby_column)
            
            for period_key, period_df in grouped:
                # Calculate income and expenses
                income_df = period_df[period_df['is_income']]
                expense_df = period_df[period_df['is_expense']]
                
                total_income = abs(income_df['amount'].sum()) if not income_df.empty else 0.0
                total_expenses = expense_df['amount'].sum() if not expense_df.empty else 0.0
                
                # Income by category
                income_by_category = {}
                if not income_df.empty:
                    income_categories = income_df.groupby('category')['amount'].sum().abs()
                    income_by_category = income_categories.to_dict()
                
                # Expenses by category
                expenses_by_category = {}
                if not expense_df.empty:
                    expense_categories = expense_df.groupby('category')['amount'].sum()
                    expenses_by_category = expense_categories.to_dict()
                
                # Period dates
                period_start = period_df['date'].min()
                period_end = period_df['date'].max()
                
                cash_flow_period = CashFlowPeriod(
                    period_start=period_start,
                    period_end=period_end,
                    total_income=total_income,
                    total_expenses=total_expenses,
                    net_cash_flow=total_income - total_expenses,
                    income_by_category=income_by_category,
                    expenses_by_category=expenses_by_category,
                    transaction_count=len(period_df),
                    average_transaction_size=period_df['abs_amount'].mean()
                )
                
                periods.append(cash_flow_period)
            
            return sorted(periods, key=lambda x: x.period_start)
            
        except Exception as e:
            logger.error(f"Error analyzing by period: {str(e)}")
            return []
    
    def _analyze_trends(self, df: pd.DataFrame, period: str) -> CashFlowTrend:
        """Analyze cash flow trends over time"""
        try:
            if period == 'monthly':
                groupby_column = 'month'
            elif period == 'quarterly':
                groupby_column = 'quarter'
            else:
                groupby_column = 'year'
            
            # Calculate net cash flow by period
            period_cash_flow = []
            grouped = df.groupby(groupby_column)
            
            for period_key, period_df in grouped:
                income = abs(period_df[period_df['is_income']]['amount'].sum())
                expenses = period_df[period_df['is_expense']]['amount'].sum()
                net_flow = income - expenses
                period_cash_flow.append(net_flow)
            
            if len(period_cash_flow) < 2:
                return CashFlowTrend(
                    period=period,
                    trend_direction='insufficient_data',
                    trend_percentage=0.0,
                    volatility=0.0,
                    seasonal_patterns={},
                    growth_rate=0.0
                )
            
            # Calculate trend direction and percentage
            first_half = period_cash_flow[:len(period_cash_flow)//2]
            second_half = period_cash_flow[len(period_cash_flow)//2:]
            
            avg_first = statistics.mean(first_half)
            avg_second = statistics.mean(second_half)
            
            if avg_first == 0:
                trend_percentage = 0.0
            else:
                trend_percentage = ((avg_second - avg_first) / abs(avg_first)) * 100
            
            if trend_percentage > 5:
                trend_direction = 'increasing'
            elif trend_percentage < -5:
                trend_direction = 'decreasing'
            else:
                trend_direction = 'stable'
            
            # Calculate volatility (coefficient of variation)
            volatility = (statistics.stdev(period_cash_flow) / abs(statistics.mean(period_cash_flow))) * 100 if statistics.mean(period_cash_flow) != 0 else 0
            
            # Seasonal patterns (simplified)
            seasonal_patterns = {}
            if 'month' in df.columns:
                monthly_spending = df[df['is_expense']].groupby(df['date'].dt.month)['amount'].sum()
                avg_monthly = monthly_spending.mean()
                for month, spending in monthly_spending.items():
                    seasonal_patterns[f'month_{month}'] = (spending / avg_monthly - 1) * 100 if avg_monthly != 0 else 0
            
            # Growth rate (annualized)
            if len(period_cash_flow) > 1:
                periods_per_year = {'monthly': 12, 'quarterly': 4, 'yearly': 1}[period]
                n_periods = len(period_cash_flow)
                years = n_periods / periods_per_year
                if years > 0 and period_cash_flow[0] != 0:
                    growth_rate = ((period_cash_flow[-1] / period_cash_flow[0]) ** (1/years) - 1) * 100
                else:
                    growth_rate = 0.0
            else:
                growth_rate = 0.0
            
            return CashFlowTrend(
                period=period,
                trend_direction=trend_direction,
                trend_percentage=trend_percentage,
                volatility=volatility,
                seasonal_patterns=seasonal_patterns,
                growth_rate=growth_rate
            )
            
        except Exception as e:
            logger.error(f"Error analyzing trends: {str(e)}")
            return CashFlowTrend(
                period=period,
                trend_direction='error',
                trend_percentage=0.0,
                volatility=0.0,
                seasonal_patterns={},
                growth_rate=0.0
            )
    
    def _calculate_financial_health(self, df: pd.DataFrame, accounts: List[BankAccount]) -> FinancialHealthScore:
        """Calculate comprehensive financial health score"""
        try:
            # Get recent 3 months for health calculation
            recent_date = df['date'].max()
            three_months_ago = recent_date - timedelta(days=90)
            recent_df = df[df['date'] >= three_months_ago]
            
            # Income stability (coefficient of variation)
            monthly_income = recent_df[recent_df['is_income']].groupby(recent_df['date'].dt.to_period('M'))['amount'].sum().abs()
            if len(monthly_income) > 1:
                income_stability = max(0, 100 - (statistics.stdev(monthly_income) / statistics.mean(monthly_income)) * 100)
            else:
                income_stability = 50.0  # Neutral score for insufficient data
            
            # Expense control (spending consistency)
            monthly_expenses = recent_df[recent_df['is_expense']].groupby(recent_df['date'].dt.to_period('M'))['amount'].sum()
            if len(monthly_expenses) > 1:
                expense_control = max(0, 100 - (statistics.stdev(monthly_expenses) / statistics.mean(monthly_expenses)) * 100)
            else:
                expense_control = 50.0
            
            # Savings rate
            total_income = abs(recent_df[recent_df['is_income']]['amount'].sum())
            total_expenses = recent_df[recent_df['is_expense']]['amount'].sum()
            
            if total_income > 0:
                savings_rate = ((total_income - total_expenses) / total_income) * 100
            else:
                savings_rate = 0.0
            
            # Debt ratio (simplified - based on credit/loan categories)
            debt_payments = recent_df[recent_df['category'].isin(['financial', 'bills_utilities'])]['amount'].sum()
            debt_ratio = (debt_payments / total_income) * 100 if total_income > 0 else 0.0
            
            # Emergency fund months (based on current account balances)
            total_liquid_balance = sum(
                acc.balance_current or 0 for acc in accounts 
                if acc.type in ['depository', 'checking', 'savings']
            )
            monthly_expenses = total_expenses / 3  # Average monthly expenses
            emergency_fund_months = total_liquid_balance / monthly_expenses if monthly_expenses > 0 else 0.0
            
            # Calculate overall score (weighted average)
            weights = {
                'income_stability': 0.25,
                'expense_control': 0.20,
                'savings_rate': 0.25,
                'debt_ratio': 0.15,
                'emergency_fund': 0.15
            }
            
            # Normalize scores
            normalized_savings_rate = min(100, max(0, savings_rate * 2))  # 50% savings = 100 score
            normalized_debt_ratio = max(0, 100 - debt_ratio * 2)  # Lower debt = higher score
            normalized_emergency_fund = min(100, emergency_fund_months * 16.67)  # 6 months = 100 score
            
            overall_score = (
                weights['income_stability'] * income_stability +
                weights['expense_control'] * expense_control +
                weights['savings_rate'] * normalized_savings_rate +
                weights['debt_ratio'] * normalized_debt_ratio +
                weights['emergency_fund'] * normalized_emergency_fund
            )
            
            # Generate recommendations
            recommendations = []
            if income_stability < 70:
                recommendations.append("Work on stabilizing income sources")
            if expense_control < 70:
                recommendations.append("Focus on consistent spending habits")
            if savings_rate < 10:
                recommendations.append("Increase savings rate to at least 10%")
            if debt_ratio > 30:
                recommendations.append("Consider reducing debt payments")
            if emergency_fund_months < 3:
                recommendations.append("Build emergency fund to 3-6 months of expenses")
            
            return FinancialHealthScore(
                overall_score=overall_score,
                income_stability=income_stability,
                expense_control=expense_control,
                savings_rate=savings_rate,
                debt_ratio=debt_ratio,
                emergency_fund_months=emergency_fund_months,
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.error(f"Error calculating financial health: {str(e)}")
            return FinancialHealthScore(
                overall_score=0.0,
                income_stability=0.0,
                expense_control=0.0,
                savings_rate=0.0,
                debt_ratio=0.0,
                emergency_fund_months=0.0,
                recommendations=["Unable to calculate financial health score"]
            )
    
    def _analyze_savings_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze savings patterns and opportunities"""
        try:
            # Monthly savings calculation
            monthly_data = df.groupby('month').agg({
                'amount': lambda x: x[x < 0].sum() + x[x > 0].sum()  # Net cash flow
            }).reset_index()
            
            monthly_data['savings'] = -monthly_data['amount']  # Positive savings
            
            # Savings statistics
            avg_monthly_savings = monthly_data['savings'].mean()
            savings_volatility = monthly_data['savings'].std()
            
            # Identify savings opportunities (categories with high spending)
            expense_categories = df[df['is_expense']].groupby('category')['amount'].sum().sort_values(ascending=False)
            
            savings_opportunities = []
            for category, amount in expense_categories.head(5).items():
                monthly_avg = amount / len(df['month'].unique())
                potential_reduction = monthly_avg * 0.1  # 10% reduction opportunity
                savings_opportunities.append({
                    'category': category,
                    'monthly_average': monthly_avg,
                    'potential_monthly_savings': potential_reduction,
                    'annual_potential': potential_reduction * 12
                })
            
            return {
                'average_monthly_savings': avg_monthly_savings,
                'savings_volatility': savings_volatility,
                'savings_trend': 'increasing' if monthly_data['savings'].iloc[-1] > monthly_data['savings'].iloc[0] else 'decreasing',
                'savings_opportunities': savings_opportunities,
                'total_potential_annual_savings': sum(opp['annual_potential'] for opp in savings_opportunities)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing savings patterns: {str(e)}")
            return {}
    
    def _forecast_cash_flow(self, df: pd.DataFrame, months_ahead: int = 6) -> Dict[str, Any]:
        """Simple cash flow forecasting"""
        try:
            # Calculate monthly averages
            monthly_stats = df.groupby('month').agg({
                'amount': lambda x: (x[x < 0].sum(), x[x > 0].sum())  # Income, Expenses
            })
            
            # Simple trend-based forecasting
            recent_months = monthly_stats.tail(6)  # Last 6 months
            
            if len(recent_months) == 0:
                return {'error': 'Insufficient data for forecasting'}
            
            # Average monthly income and expenses
            avg_monthly_income = abs(np.mean([month[0] for month in recent_months['amount']]))
            avg_monthly_expenses = np.mean([month[1] for month in recent_months['amount']])
            
            # Generate forecast
            forecast = []
            base_date = df['date'].max()
            
            for i in range(1, months_ahead + 1):
                forecast_date = base_date + timedelta(days=30 * i)
                
                # Simple trend adjustment (could be more sophisticated)
                trend_factor = 1.0 + (i * 0.01)  # 1% monthly growth assumption
                
                forecast.append({
                    'month': forecast_date.strftime('%Y-%m'),
                    'predicted_income': avg_monthly_income * trend_factor,
                    'predicted_expenses': avg_monthly_expenses * trend_factor,
                    'predicted_net_flow': (avg_monthly_income - avg_monthly_expenses) * trend_factor,
                    'confidence': max(0.5, 1.0 - (i * 0.1))  # Decreasing confidence
                })
            
            return {
                'forecast_months': months_ahead,
                'forecasting_method': 'trend_based',
                'forecast': forecast,
                'assumptions': {
                    'base_monthly_income': avg_monthly_income,
                    'base_monthly_expenses': avg_monthly_expenses,
                    'trend_factor': '1% monthly growth'
                }
            }
            
        except Exception as e:
            logger.error(f"Error forecasting cash flow: {str(e)}")
            return {'error': str(e)}
    
    def _generate_insights(
        self,
        period_analysis: List[CashFlowPeriod],
        trend_analysis: CashFlowTrend,
        health_score: FinancialHealthScore,
        savings_analysis: Dict[str, Any]
    ) -> List[str]:
        """Generate actionable insights from analysis"""
        insights = []
        
        try:
            # Income insights
            if trend_analysis.trend_direction == 'increasing':
                insights.append(f"Your income has been trending upward by {trend_analysis.trend_percentage:.1f}%")
            elif trend_analysis.trend_direction == 'decreasing':
                insights.append(f"Your income has decreased by {trend_analysis.trend_percentage:.1f}% - consider diversifying income sources")
            
            # Spending insights
            if period_analysis:
                latest_period = period_analysis[-1]
                if latest_period.total_expenses > latest_period.total_income:
                    insights.append("Your expenses exceeded income this period - review spending categories")
                
                # Category insights
                top_expense_category = max(latest_period.expenses_by_category.items(), key=lambda x: x[1], default=('none', 0))
                if top_expense_category[1] > 0:
                    insights.append(f"Your highest spending category is {top_expense_category[0]} at ${top_expense_category[1]:.2f}")
            
            # Health score insights
            if health_score.overall_score >= 80:
                insights.append("Excellent financial health! Keep up the good work")
            elif health_score.overall_score >= 60:
                insights.append("Good financial health with room for improvement")
            else:
                insights.append("Consider focusing on improving your financial fundamentals")
            
            # Savings insights
            if savings_analysis.get('average_monthly_savings', 0) > 0:
                insights.append(f"Great job saving an average of ${savings_analysis['average_monthly_savings']:.2f} per month")
            else:
                insights.append("Consider setting up automatic savings to build wealth")
            
            # Volatility insights
            if trend_analysis.volatility > 50:
                insights.append("Your cash flow is quite volatile - focus on stabilizing income and expenses")
            
            return insights
            
        except Exception as e:
            logger.error(f"Error generating insights: {str(e)}")
            return ["Unable to generate insights from current data"]
    
    def _generate_recommendations(
        self,
        health_score: FinancialHealthScore,
        trend_analysis: CashFlowTrend
    ) -> List[str]:
        """Generate specific recommendations based on analysis"""
        recommendations = []
        
        try:
            # Income recommendations
            if health_score.income_stability < 70:
                recommendations.append("Consider building multiple income streams for stability")
            
            # Expense recommendations
            if health_score.expense_control < 70:
                recommendations.append("Create a detailed budget to better control expenses")
            
            # Savings recommendations
            if health_score.savings_rate < 10:
                recommendations.append("Aim to save at least 10% of your income")
            elif health_score.savings_rate < 20:
                recommendations.append("Consider increasing your savings rate to 20% for faster wealth building")
            
            # Emergency fund recommendations
            if health_score.emergency_fund_months < 3:
                recommendations.append("Build an emergency fund covering 3-6 months of expenses")
            
            # Debt recommendations
            if health_score.debt_ratio > 30:
                recommendations.append("Consider debt consolidation or payment strategies to reduce debt burden")
            
            # Trend-based recommendations
            if trend_analysis.trend_direction == 'decreasing':
                recommendations.append("Focus on increasing income or reducing expenses to reverse negative trend")
            
            if trend_analysis.volatility > 50:
                recommendations.append("Work on stabilizing your cash flow through budgeting and planning")
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {str(e)}")
            return ["Unable to generate recommendations"]
    
    async def compare_budget_vs_actual(
        self,
        transactions: List[Transaction],
        budget: Dict[str, float],
        categorized_transactions: Optional[List[CategoryPrediction]] = None,
        period_start: Optional[datetime] = None,
        period_end: Optional[datetime] = None
    ) -> List[BudgetVariance]:
        """
        Compare actual spending vs budget
        
        Args:
            transactions: List of transactions
            budget: Budget amounts by category
            categorized_transactions: Pre-categorized transactions
            period_start: Analysis period start
            period_end: Analysis period end
            
        Returns:
            Budget variance analysis
        """
        try:
            # Filter transactions by period if specified
            if period_start and period_end:
                transactions = [t for t in transactions if period_start <= t.date <= period_end]
            
            # Categorize transactions if needed
            if not categorized_transactions:
                categorized_transactions = await transaction_categorizer.categorize_transactions_batch(transactions)
            
            # Calculate actual spending by category
            actual_spending = defaultdict(float)
            for i, transaction in enumerate(transactions):
                if transaction.amount > 0:  # Expenses only
                    category = categorized_transactions[i].category if i < len(categorized_transactions) else 'other'
                    actual_spending[category] += transaction.amount
            
            # Calculate variances
            variances = []
            all_categories = set(budget.keys()) | set(actual_spending.keys())
            
            for category in all_categories:
                budgeted = budget.get(category, 0.0)
                actual = actual_spending.get(category, 0.0)
                variance_amount = actual - budgeted
                
                if budgeted > 0:
                    variance_percentage = (variance_amount / budgeted) * 100
                else:
                    variance_percentage = 100.0 if actual > 0 else 0.0
                
                # Determine status
                if abs(variance_percentage) <= 10:
                    status = 'on_track'
                elif variance_percentage > 10:
                    status = 'over_budget'
                else:
                    status = 'under_budget'
                
                variances.append(BudgetVariance(
                    category=category,
                    budgeted_amount=budgeted,
                    actual_amount=actual,
                    variance_amount=variance_amount,
                    variance_percentage=variance_percentage,
                    status=status
                ))
            
            return sorted(variances, key=lambda x: abs(x.variance_amount), reverse=True)
            
        except Exception as e:
            logger.error(f"Error comparing budget vs actual: {str(e)}")
            return []


# Singleton instance
cash_flow_analyzer = CashFlowAnalyzer()