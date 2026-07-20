"""
AI-Powered Recommendation Engine
Provides personalized financial recommendations based on user profile, goals, and market conditions
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import logging
from collections import defaultdict
import asyncio

from sklearn.ensemble import RandomForestRegressor, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import cosine_similarity
from scipy.optimize import minimize
import tensorflow as tf
from tensorflow import keras
import redis

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class RecommendationType(Enum):
    """Types of recommendations"""
    PORTFOLIO_ADJUSTMENT = "portfolio_adjustment"
    REBALANCING = "rebalancing"
    TAX_OPTIMIZATION = "tax_optimization"
    GOAL_PLANNING = "goal_planning"
    RISK_MANAGEMENT = "risk_management"
    INVESTMENT_OPPORTUNITY = "investment_opportunity"
    SAVINGS_OPTIMIZATION = "savings_optimization"
    DEBT_MANAGEMENT = "debt_management"
    INSURANCE_REVIEW = "insurance_review"
    RETIREMENT_PLANNING = "retirement_planning"


class Priority(Enum):
    """Recommendation priority levels"""
    URGENT = "urgent"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFORMATIONAL = "informational"


class ActionType(Enum):
    """Types of recommended actions"""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"
    REBALANCE = "rebalance"
    CONTRIBUTE = "contribute"
    WITHDRAW = "withdraw"
    CONVERT = "convert"
    REVIEW = "review"
    LEARN = "learn"


@dataclass
class Recommendation:
    """Individual recommendation"""
    id: str
    type: RecommendationType
    priority: Priority
    title: str
    description: str
    rationale: str
    action_items: List[Dict[str, Any]]
    expected_impact: Dict[str, Any]
    confidence_score: float  # 0-1
    time_horizon: str  # immediate/short/medium/long
    prerequisites: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)
    alternatives: List[str] = field(default_factory=list)
    supporting_data: Dict[str, Any] = field(default_factory=dict)
    expires_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class PortfolioRecommendation(Recommendation):
    """Portfolio-specific recommendation"""
    target_allocation: Dict[str, float] = field(default_factory=dict)
    current_allocation: Dict[str, float] = field(default_factory=dict)
    trades_required: List[Dict[str, Any]] = field(default_factory=list)
    estimated_cost: float = 0
    estimated_tax_impact: float = 0


@dataclass
class GoalRecommendation(Recommendation):
    """Goal-specific recommendation"""
    goal_id: str = ""
    current_progress: float = 0
    target_progress: float = 0
    monthly_contribution_required: float = 0
    years_to_goal: float = 0
    success_probability: float = 0


class NextBestAction(BaseModel):
    """Next best action for user"""
    action: str = Field(..., description="Recommended action")
    reason: str = Field(..., description="Why this action is recommended")
    urgency: str = Field(..., description="Urgency level")
    impact: str = Field(..., description="Expected impact")
    steps: List[str] = Field(default_factory=list, description="Steps to take")
    deadline: Optional[datetime] = Field(None, description="Action deadline")
    confidence: float = Field(..., ge=0, le=1, description="Confidence score")


class RecommendationEngine:
    """
    Advanced recommendation engine using ML and financial expertise
    to provide personalized, actionable recommendations
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.redis_client = redis.Redis.from_url(
            config.get('redis_url', 'redis://localhost:6379')
        )
        self.models = self._initialize_models()
        self.scaler = StandardScaler()
        self.recommendation_rules = self._load_recommendation_rules()
        self.market_indicators = {}
        
    def _initialize_models(self) -> Dict[str, Any]:
        """Initialize ML models for recommendations"""
        models = {}
        
        # Portfolio optimization model
        models['portfolio_optimizer'] = RandomForestRegressor(
            n_estimators=200,
            max_depth=15,
            random_state=42
        )
        
        # Action prediction model
        models['action_predictor'] = GradientBoostingClassifier(
            n_estimators=100,
            learning_rate=0.1,
            max_depth=5,
            random_state=42
        )
        
        # Goal achievement model
        models['goal_predictor'] = keras.Sequential([
            keras.layers.Dense(128, activation='relu', input_shape=(30,)),
            keras.layers.Dropout(0.3),
            keras.layers.Dense(64, activation='relu'),
            keras.layers.Dense(32, activation='relu'),
            keras.layers.Dense(1, activation='sigmoid')  # Probability of success
        ])
        
        models['goal_predictor'].compile(
            optimizer='adam',
            loss='binary_crossentropy',
            metrics=['accuracy']
        )
        
        # Collaborative filtering for similar users
        models['collaborative_filter'] = None  # To be trained on user data
        
        return models
    
    def _load_recommendation_rules(self) -> Dict[str, Any]:
        """Load rule-based recommendation logic"""
        return {
            'rebalancing': {
                'threshold': 0.05,  # 5% deviation triggers rebalancing
                'min_interval_days': 90,  # Minimum days between rebalancing
                'tax_aware': True
            },
            'tax_loss_harvesting': {
                'min_loss': 1000,  # Minimum loss to harvest
                'wash_sale_period': 30,  # Days to avoid wash sale
                'offset_gains': True
            },
            'emergency_fund': {
                'months_expenses': 6,  # Target months of expenses
                'priority': 'high'
            },
            'retirement': {
                'target_replacement_ratio': 0.8,  # 80% of pre-retirement income
                'safe_withdrawal_rate': 0.04  # 4% rule
            },
            'debt_management': {
                'high_interest_threshold': 0.07,  # 7% APR considered high
                'avalanche_method': True  # Pay highest rate first
            }
        }
    
    async def generate_recommendations(
        self,
        user_profile: Dict[str, Any],
        portfolio: Dict[str, Any],
        goals: List[Dict[str, Any]],
        market_data: Dict[str, Any],
        behavioral_profile: Optional[Dict[str, Any]] = None
    ) -> List[Recommendation]:
        """Generate comprehensive recommendations for user"""
        
        recommendations = []
        
        # Portfolio optimization recommendations
        portfolio_recs = await self._generate_portfolio_recommendations(
            portfolio, user_profile, market_data
        )
        recommendations.extend(portfolio_recs)
        
        # Goal-based recommendations
        goal_recs = await self._generate_goal_recommendations(
            goals, user_profile, portfolio
        )
        recommendations.extend(goal_recs)
        
        # Tax optimization recommendations
        tax_recs = await self._generate_tax_recommendations(
            portfolio, user_profile
        )
        recommendations.extend(tax_recs)
        
        # Risk management recommendations
        risk_recs = await self._generate_risk_recommendations(
            portfolio, user_profile, market_data
        )
        recommendations.extend(risk_recs)
        
        # Behavioral recommendations
        if behavioral_profile:
            behavioral_recs = await self._generate_behavioral_recommendations(
                behavioral_profile, portfolio, user_profile
            )
            recommendations.extend(behavioral_recs)
        
        # Market opportunity recommendations
        market_recs = await self._generate_market_recommendations(
            portfolio, market_data, user_profile
        )
        recommendations.extend(market_recs)
        
        # Prioritize and filter recommendations
        recommendations = self._prioritize_recommendations(
            recommendations, user_profile
        )
        
        # Store recommendations for tracking
        await self._store_recommendations(user_profile['user_id'], recommendations)
        
        return recommendations[:10]  # Return top 10 recommendations
    
    async def _generate_portfolio_recommendations(
        self,
        portfolio: Dict[str, Any],
        user_profile: Dict[str, Any],
        market_data: Dict[str, Any]
    ) -> List[PortfolioRecommendation]:
        """Generate portfolio optimization recommendations"""
        
        recommendations = []
        
        # Check for rebalancing needs
        current_allocation = portfolio.get('allocation', {})
        target_allocation = portfolio.get('target_allocation', {})
        
        if self._needs_rebalancing(current_allocation, target_allocation):
            rebalancing_rec = await self._create_rebalancing_recommendation(
                current_allocation, target_allocation, portfolio, user_profile
            )
            recommendations.append(rebalancing_rec)
        
        # Check for concentration risk
        if self._has_concentration_risk(portfolio):
            diversification_rec = self._create_diversification_recommendation(
                portfolio, market_data
            )
            recommendations.append(diversification_rec)
        
        # Check for underperforming assets
        underperformers = self._identify_underperformers(
            portfolio, market_data
        )
        if underperformers:
            replacement_rec = self._create_replacement_recommendation(
                underperformers, market_data, user_profile
            )
            recommendations.append(replacement_rec)
        
        # Optimize for risk-adjusted returns
        optimization_rec = await self._optimize_portfolio(
            portfolio, user_profile, market_data
        )
        if optimization_rec:
            recommendations.append(optimization_rec)
        
        return recommendations
    
    async def _generate_goal_recommendations(
        self,
        goals: List[Dict[str, Any]],
        user_profile: Dict[str, Any],
        portfolio: Dict[str, Any]
    ) -> List[GoalRecommendation]:
        """Generate goal-specific recommendations"""
        
        recommendations = []
        
        for goal in goals:
            # Assess goal progress
            progress = self._assess_goal_progress(goal, portfolio)
            
            if progress['on_track'] == False:
                # Create catch-up recommendation
                catch_up_rec = self._create_catch_up_recommendation(
                    goal, progress, user_profile
                )
                recommendations.append(catch_up_rec)
            
            # Check if goal needs adjustment
            if self._goal_needs_adjustment(goal, user_profile):
                adjustment_rec = self._create_goal_adjustment_recommendation(
                    goal, user_profile, portfolio
                )
                recommendations.append(adjustment_rec)
            
            # Optimize goal funding strategy
            if goal['type'] == 'retirement':
                retirement_rec = await self._optimize_retirement_strategy(
                    goal, user_profile, portfolio
                )
                if retirement_rec:
                    recommendations.append(retirement_rec)
            elif goal['type'] == 'education':
                education_rec = await self._optimize_education_funding(
                    goal, user_profile
                )
                if education_rec:
                    recommendations.append(education_rec)
        
        return recommendations
    
    async def _generate_tax_recommendations(
        self,
        portfolio: Dict[str, Any],
        user_profile: Dict[str, Any]
    ) -> List[Recommendation]:
        """Generate tax optimization recommendations"""
        
        recommendations = []
        
        # Tax-loss harvesting opportunities
        harvest_opportunities = self._identify_tax_loss_harvesting(
            portfolio, user_profile
        )
        if harvest_opportunities:
            harvest_rec = self._create_harvest_recommendation(
                harvest_opportunities, user_profile
            )
            recommendations.append(harvest_rec)
        
        # Account optimization (401k vs Roth vs taxable)
        account_rec = self._optimize_account_allocation(
            portfolio, user_profile
        )
        if account_rec:
            recommendations.append(account_rec)
        
        # Year-end tax strategies
        if self._is_year_end():
            year_end_rec = self._create_year_end_tax_recommendation(
                portfolio, user_profile
            )
            recommendations.append(year_end_rec)
        
        # Estimated tax payment recommendations
        if self._needs_estimated_tax_adjustment(user_profile):
            tax_payment_rec = self._create_tax_payment_recommendation(
                user_profile
            )
            recommendations.append(tax_payment_rec)
        
        return recommendations
    
    async def _generate_risk_recommendations(
        self,
        portfolio: Dict[str, Any],
        user_profile: Dict[str, Any],
        market_data: Dict[str, Any]
    ) -> List[Recommendation]:
        """Generate risk management recommendations"""
        
        recommendations = []
        
        # Portfolio risk assessment
        risk_metrics = self._calculate_risk_metrics(portfolio, market_data)
        
        if risk_metrics['var_95'] > user_profile.get('risk_tolerance', 0.15):
            risk_reduction_rec = self._create_risk_reduction_recommendation(
                risk_metrics, portfolio, user_profile
            )
            recommendations.append(risk_reduction_rec)
        
        # Hedge recommendations
        if market_data.get('volatility_index', 15) > 25:
            hedge_rec = self._create_hedge_recommendation(
                portfolio, market_data
            )
            recommendations.append(hedge_rec)
        
        # Emergency fund check
        if not self._has_adequate_emergency_fund(user_profile):
            emergency_rec = self._create_emergency_fund_recommendation(
                user_profile
            )
            recommendations.append(emergency_rec)
        
        # Insurance review
        if self._needs_insurance_review(user_profile):
            insurance_rec = self._create_insurance_recommendation(
                user_profile
            )
            recommendations.append(insurance_rec)
        
        return recommendations
    
    async def _generate_behavioral_recommendations(
        self,
        behavioral_profile: Dict[str, Any],
        portfolio: Dict[str, Any],
        user_profile: Dict[str, Any]
    ) -> List[Recommendation]:
        """Generate behaviorally-informed recommendations"""
        
        recommendations = []
        
        # Address behavioral biases
        if behavioral_profile.get('loss_aversion_score', 0.5) > 0.7:
            recommendations.append(
                Recommendation(
                    id=f"behav_{datetime.utcnow().timestamp()}",
                    type=RecommendationType.PORTFOLIO_ADJUSTMENT,
                    priority=Priority.MEDIUM,
                    title="Consider Systematic Investment Approach",
                    description="Your high loss aversion suggests implementing automated investing to reduce emotional decision-making.",
                    rationale="Automated investing helps overcome psychological barriers to investing during market downturns.",
                    action_items=[
                        {
                            "action": "Set up automatic monthly investments",
                            "amount": user_profile.get('monthly_savings', 1000)
                        }
                    ],
                    expected_impact={
                        "emotion_reduction": "High",
                        "return_improvement": "5-10% annually"
                    },
                    confidence_score=0.8,
                    time_horizon="immediate"
                )
            )
        
        # Trading frequency optimization
        if behavioral_profile.get('trading_frequency') == 'high':
            recommendations.append(
                Recommendation(
                    id=f"behav_freq_{datetime.utcnow().timestamp()}",
                    type=RecommendationType.PORTFOLIO_ADJUSTMENT,
                    priority=Priority.HIGH,
                    title="Reduce Trading Frequency",
                    description="Your high trading frequency may be impacting returns through costs and timing errors.",
                    rationale="Studies show that reducing trading frequency by 50% can improve returns by 2-3% annually.",
                    action_items=[
                        {"action": "Implement monthly trading calendar"},
                        {"action": "Set minimum holding period of 30 days"}
                    ],
                    expected_impact={
                        "cost_reduction": "$500-1000 annually",
                        "return_improvement": "2-3%"
                    },
                    confidence_score=0.85,
                    time_horizon="short"
                )
            )
        
        return recommendations
    
    async def _generate_market_recommendations(
        self,
        portfolio: Dict[str, Any],
        market_data: Dict[str, Any],
        user_profile: Dict[str, Any]
    ) -> List[Recommendation]:
        """Generate market opportunity recommendations"""
        
        recommendations = []
        
        # Sector rotation opportunities
        sector_opps = self._identify_sector_opportunities(
            market_data, portfolio
        )
        if sector_opps:
            sector_rec = self._create_sector_recommendation(
                sector_opps, user_profile
            )
            recommendations.append(sector_rec)
        
        # Value opportunities
        value_stocks = self._identify_value_opportunities(market_data)
        if value_stocks and user_profile.get('risk_tolerance', 'moderate') != 'conservative':
            value_rec = self._create_value_recommendation(
                value_stocks, user_profile
            )
            recommendations.append(value_rec)
        
        # Interest rate plays
        if market_data.get('interest_rate_trend') == 'rising':
            rate_rec = self._create_interest_rate_recommendation(
                portfolio, market_data
            )
            recommendations.append(rate_rec)
        
        return recommendations
    
    def _needs_rebalancing(
        self,
        current: Dict[str, float],
        target: Dict[str, float]
    ) -> bool:
        """Check if portfolio needs rebalancing"""
        
        threshold = self.recommendation_rules['rebalancing']['threshold']
        
        for asset, target_weight in target.items():
            current_weight = current.get(asset, 0)
            deviation = abs(current_weight - target_weight)
            if deviation > threshold:
                return True
        
        return False
    
    async def _create_rebalancing_recommendation(
        self,
        current: Dict[str, float],
        target: Dict[str, float],
        portfolio: Dict[str, Any],
        user_profile: Dict[str, Any]
    ) -> PortfolioRecommendation:
        """Create detailed rebalancing recommendation"""
        
        # Calculate required trades
        trades = []
        total_value = portfolio.get('total_value', 100000)
        
        for asset, target_weight in target.items():
            current_weight = current.get(asset, 0)
            diff = target_weight - current_weight
            
            if abs(diff) > 0.01:  # 1% threshold
                trade_value = diff * total_value
                trades.append({
                    'asset': asset,
                    'action': 'buy' if diff > 0 else 'sell',
                    'amount': abs(trade_value),
                    'current_weight': current_weight,
                    'target_weight': target_weight
                })
        
        # Estimate costs and tax impact
        estimated_cost = len(trades) * 5  # $5 per trade estimate
        estimated_tax = sum(
            t['amount'] * 0.15 for t in trades if t['action'] == 'sell'
        ) * 0.2  # Rough tax estimate
        
        return PortfolioRecommendation(
            id=f"rebal_{datetime.utcnow().timestamp()}",
            type=RecommendationType.REBALANCING,
            priority=Priority.HIGH,
            title="Portfolio Rebalancing Required",
            description=f"Your portfolio has drifted from target allocation by more than {self.recommendation_rules['rebalancing']['threshold']*100}%",
            rationale="Regular rebalancing helps maintain desired risk level and can improve returns through systematic buying low and selling high.",
            action_items=trades,
            expected_impact={
                "risk_reduction": "15-20%",
                "return_improvement": "0.5-1% annually"
            },
            confidence_score=0.9,
            time_horizon="immediate",
            target_allocation=target,
            current_allocation=current,
            trades_required=trades,
            estimated_cost=estimated_cost,
            estimated_tax_impact=estimated_tax,
            risks=["Market timing risk", "Transaction costs", "Tax implications"]
        )
    
    def _has_concentration_risk(self, portfolio: Dict[str, Any]) -> bool:
        """Check for concentration risk in portfolio"""
        
        holdings = portfolio.get('holdings', [])
        if not holdings:
            return False
        
        total_value = sum(h.get('value', 0) for h in holdings)
        
        for holding in holdings:
            weight = holding.get('value', 0) / max(total_value, 1)
            if weight > 0.15:  # 15% concentration threshold
                return True
        
        return False
    
    def _create_diversification_recommendation(
        self,
        portfolio: Dict[str, Any],
        market_data: Dict[str, Any]
    ) -> Recommendation:
        """Create diversification recommendation"""
        
        concentrated_holdings = [
            h for h in portfolio.get('holdings', [])
            if h.get('value', 0) / portfolio.get('total_value', 1) > 0.15
        ]
        
        return Recommendation(
            id=f"div_{datetime.utcnow().timestamp()}",
            type=RecommendationType.RISK_MANAGEMENT,
            priority=Priority.HIGH,
            title="Reduce Concentration Risk",
            description=f"You have {len(concentrated_holdings)} position(s) exceeding 15% of portfolio",
            rationale="Concentration risk can lead to significant losses if a single position underperforms.",
            action_items=[
                {
                    "action": "Reduce position",
                    "asset": h['symbol'],
                    "target_weight": 0.10
                }
                for h in concentrated_holdings
            ],
            expected_impact={
                "risk_reduction": "30-40%",
                "volatility_reduction": "20%"
            },
            confidence_score=0.85,
            time_horizon="short",
            alternatives=["Use ETFs for instant diversification", "Implement position limits"]
        )
    
    def _identify_underperformers(
        self,
        portfolio: Dict[str, Any],
        market_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Identify underperforming assets"""
        
        underperformers = []
        benchmark_return = market_data.get('sp500_return', 0.10)
        
        for holding in portfolio.get('holdings', []):
            asset_return = holding.get('total_return', 0)
            if asset_return < benchmark_return - 0.05:  # 5% underperformance
                underperformers.append(holding)
        
        return underperformers
    
    def _create_replacement_recommendation(
        self,
        underperformers: List[Dict[str, Any]],
        market_data: Dict[str, Any],
        user_profile: Dict[str, Any]
    ) -> Recommendation:
        """Create recommendation to replace underperforming assets"""
        
        return Recommendation(
            id=f"replace_{datetime.utcnow().timestamp()}",
            type=RecommendationType.PORTFOLIO_ADJUSTMENT,
            priority=Priority.MEDIUM,
            title="Replace Underperforming Assets",
            description=f"{len(underperformers)} assets are significantly underperforming the benchmark",
            rationale="Replacing chronic underperformers can improve portfolio returns without increasing risk.",
            action_items=[
                {
                    "action": "sell",
                    "asset": u['symbol'],
                    "reason": f"Underperformed by {(market_data.get('sp500_return', 0.10) - u.get('total_return', 0))*100:.1f}%"
                }
                for u in underperformers
            ],
            expected_impact={
                "return_improvement": "2-5% annually"
            },
            confidence_score=0.7,
            time_horizon="medium",
            risks=["May realize losses", "Timing risk"],
            alternatives=["Hold for potential recovery", "Dollar-cost average out"]
        )
    
    async def _optimize_portfolio(
        self,
        portfolio: Dict[str, Any],
        user_profile: Dict[str, Any],
        market_data: Dict[str, Any]
    ) -> Optional[PortfolioRecommendation]:
        """Optimize portfolio using modern portfolio theory"""
        
        # Get expected returns and covariance matrix
        assets = [h['symbol'] for h in portfolio.get('holdings', [])]
        returns = np.array([market_data.get(f"{a}_expected_return", 0.08) for a in assets])
        cov_matrix = self._estimate_covariance_matrix(assets, market_data)
        
        # Define optimization constraints
        constraints = [
            {'type': 'eq', 'fun': lambda x: np.sum(x) - 1}  # Weights sum to 1
        ]
        bounds = [(0, 0.3) for _ in assets]  # Max 30% per asset
        
        # Optimize for maximum Sharpe ratio
        def negative_sharpe(weights):
            portfolio_return = np.dot(weights, returns)
            portfolio_std = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
            return -(portfolio_return - 0.03) / portfolio_std  # Risk-free rate = 3%
        
        # Initial guess (equal weights)
        x0 = np.array([1/len(assets)] * len(assets))
        
        # Optimize
        result = minimize(negative_sharpe, x0, method='SLSQP',
                         bounds=bounds, constraints=constraints)
        
        if not result.success:
            return None
        
        # Create recommendation if optimization improves Sharpe ratio significantly
        optimal_weights = result.x
        current_weights = np.array([h['value']/portfolio['total_value'] 
                                   for h in portfolio['holdings']])
        
        current_sharpe = -negative_sharpe(current_weights)
        optimal_sharpe = -result.fun
        
        if optimal_sharpe > current_sharpe * 1.1:  # 10% improvement threshold
            return PortfolioRecommendation(
                id=f"optimize_{datetime.utcnow().timestamp()}",
                type=RecommendationType.PORTFOLIO_ADJUSTMENT,
                priority=Priority.MEDIUM,
                title="Optimize Portfolio for Risk-Adjusted Returns",
                description=f"Portfolio optimization can improve Sharpe ratio by {(optimal_sharpe/current_sharpe - 1)*100:.1f}%",
                rationale="Mathematical optimization can identify the most efficient portfolio for your risk level.",
                action_items=[
                    {
                        "asset": assets[i],
                        "current_weight": current_weights[i],
                        "optimal_weight": optimal_weights[i],
                        "action": "adjust"
                    }
                    for i in range(len(assets))
                ],
                expected_impact={
                    "sharpe_improvement": f"{(optimal_sharpe/current_sharpe - 1)*100:.1f}%",
                    "risk_adjusted_return": "Improved"
                },
                confidence_score=0.75,
                time_horizon="medium",
                target_allocation={assets[i]: optimal_weights[i] for i in range(len(assets))},
                current_allocation={assets[i]: current_weights[i] for i in range(len(assets))}
            )
        
        return None
    
    def _estimate_covariance_matrix(
        self,
        assets: List[str],
        market_data: Dict[str, Any]
    ) -> np.ndarray:
        """Estimate covariance matrix for assets"""
        
        n = len(assets)
        cov_matrix = np.eye(n) * 0.04  # Default variance
        
        # Add correlations if available
        for i in range(n):
            for j in range(i+1, n):
                correlation = market_data.get(f"corr_{assets[i]}_{assets[j]}", 0.3)
                std_i = market_data.get(f"{assets[i]}_std", 0.2)
                std_j = market_data.get(f"{assets[j]}_std", 0.2)
                cov_matrix[i, j] = correlation * std_i * std_j
                cov_matrix[j, i] = cov_matrix[i, j]
        
        return cov_matrix
    
    def _assess_goal_progress(
        self,
        goal: Dict[str, Any],
        portfolio: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Assess progress toward a financial goal"""
        
        current_value = goal.get('current_value', 0)
        target_value = goal.get('target_value', 100000)
        target_date = goal.get('target_date')
        monthly_contribution = goal.get('monthly_contribution', 0)
        
        if not target_date:
            return {'on_track': False, 'progress_percentage': 0}
        
        # Calculate months remaining
        months_remaining = (target_date - datetime.utcnow()).days / 30
        
        # Project future value with current contribution rate
        assumed_return = 0.07 / 12  # 7% annual return
        future_value = current_value * (1 + assumed_return) ** months_remaining
        future_value += monthly_contribution * (
            ((1 + assumed_return) ** months_remaining - 1) / assumed_return
        )
        
        on_track = future_value >= target_value
        progress_percentage = (current_value / target_value) * 100
        
        return {
            'on_track': on_track,
            'progress_percentage': progress_percentage,
            'projected_value': future_value,
            'shortfall': max(0, target_value - future_value),
            'months_remaining': months_remaining
        }
    
    def _create_catch_up_recommendation(
        self,
        goal: Dict[str, Any],
        progress: Dict[str, Any],
        user_profile: Dict[str, Any]
    ) -> GoalRecommendation:
        """Create recommendation to catch up on goal progress"""
        
        # Calculate required monthly contribution
        shortfall = progress['shortfall']
        months_remaining = progress['months_remaining']
        assumed_return = 0.07 / 12
        
        required_monthly = shortfall * assumed_return / (
            (1 + assumed_return) ** months_remaining - 1
        )
        
        current_monthly = goal.get('monthly_contribution', 0)
        additional_needed = max(0, required_monthly - current_monthly)
        
        return GoalRecommendation(
            id=f"catchup_{goal.get('id', 'goal')}_{datetime.utcnow().timestamp()}",
            type=RecommendationType.GOAL_PLANNING,
            priority=Priority.HIGH if progress['progress_percentage'] < 50 else Priority.MEDIUM,
            title=f"Catch Up on {goal.get('name', 'Financial Goal')}",
            description=f"You're currently at {progress['progress_percentage']:.1f}% of your goal",
            rationale=f"Additional monthly contributions of ${additional_needed:.2f} will help you reach your target",
            action_items=[
                {
                    "action": "increase_contribution",
                    "amount": additional_needed,
                    "frequency": "monthly"
                }
            ],
            expected_impact={
                "goal_achievement": "On track",
                "success_probability": "85%"
            },
            confidence_score=0.8,
            time_horizon="immediate",
            goal_id=goal.get('id'),
            current_progress=progress['progress_percentage'],
            target_progress=100,
            monthly_contribution_required=required_monthly,
            years_to_goal=months_remaining / 12,
            success_probability=0.85,
            alternatives=[
                "Extend goal timeline",
                "Reduce goal amount",
                "Increase investment risk for higher returns"
            ]
        )
    
    def _prioritize_recommendations(
        self,
        recommendations: List[Recommendation],
        user_profile: Dict[str, Any]
    ) -> List[Recommendation]:
        """Prioritize recommendations based on user context"""
        
        # Score each recommendation
        for rec in recommendations:
            score = 0
            
            # Priority scoring
            priority_scores = {
                Priority.URGENT: 100,
                Priority.HIGH: 75,
                Priority.MEDIUM: 50,
                Priority.LOW: 25,
                Priority.INFORMATIONAL: 10
            }
            score += priority_scores.get(rec.priority, 0)
            
            # Confidence scoring
            score += rec.confidence_score * 50
            
            # User preference alignment
            if user_profile.get('preferred_recommendations'):
                if rec.type.value in user_profile['preferred_recommendations']:
                    score += 25
            
            # Time sensitivity
            if rec.expires_at:
                days_until_expiry = (rec.expires_at - datetime.utcnow()).days
                if days_until_expiry < 7:
                    score += 30
                elif days_until_expiry < 30:
                    score += 15
            
            rec.priority_score = score
        
        # Sort by priority score
        recommendations.sort(key=lambda x: x.priority_score, reverse=True)
        
        return recommendations
    
    async def _store_recommendations(
        self,
        user_id: str,
        recommendations: List[Recommendation]
    ):
        """Store recommendations for tracking and analysis"""
        
        for rec in recommendations:
            key = f"recommendation:{user_id}:{rec.id}"
            self.redis_client.setex(
                key,
                86400 * 30,  # 30 days
                json.dumps({
                    'id': rec.id,
                    'type': rec.type.value,
                    'priority': rec.priority.value,
                    'title': rec.title,
                    'created_at': rec.created_at.isoformat(),
                    'confidence_score': rec.confidence_score
                })
            )
    
    async def get_next_best_action(
        self,
        user_id: str,
        recommendations: List[Recommendation]
    ) -> NextBestAction:
        """Determine the single next best action for user"""
        
        if not recommendations:
            return NextBestAction(
                action="Review your financial goals",
                reason="No specific recommendations at this time",
                urgency="low",
                impact="Planning",
                confidence=0.5
            )
        
        # Get highest priority recommendation
        top_rec = recommendations[0]
        
        # Extract primary action
        primary_action = top_rec.action_items[0] if top_rec.action_items else {}
        
        # Create step-by-step guide
        steps = []
        if top_rec.type == RecommendationType.REBALANCING:
            steps = [
                "Review current portfolio allocation",
                "Compare with target allocation",
                "Place sell orders for overweight positions",
                "Place buy orders for underweight positions",
                "Confirm all trades executed"
            ]
        elif top_rec.type == RecommendationType.GOAL_PLANNING:
            steps = [
                "Review goal progress",
                "Calculate required monthly contribution",
                "Set up automatic transfer",
                "Monitor progress monthly"
            ]
        elif top_rec.type == RecommendationType.TAX_OPTIMIZATION:
            steps = [
                "Review current year gains/losses",
                "Identify tax-loss harvesting opportunities",
                "Execute qualifying sales",
                "Track wash sale rules"
            ]
        
        # Determine deadline
        deadline = None
        if top_rec.expires_at:
            deadline = top_rec.expires_at
        elif top_rec.priority == Priority.URGENT:
            deadline = datetime.utcnow() + timedelta(days=7)
        elif top_rec.priority == Priority.HIGH:
            deadline = datetime.utcnow() + timedelta(days=14)
        
        return NextBestAction(
            action=top_rec.title,
            reason=top_rec.rationale,
            urgency=top_rec.priority.value,
            impact=str(top_rec.expected_impact),
            steps=steps,
            deadline=deadline,
            confidence=top_rec.confidence_score
        )
    
    def _identify_tax_loss_harvesting(
        self,
        portfolio: Dict[str, Any],
        user_profile: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Identify tax-loss harvesting opportunities"""
        
        opportunities = []
        min_loss = self.recommendation_rules['tax_loss_harvesting']['min_loss']
        
        for holding in portfolio.get('holdings', []):
            unrealized_loss = holding.get('unrealized_pnl', 0)
            if unrealized_loss < -min_loss:
                # Check wash sale rule
                last_purchase = holding.get('last_purchase_date')
                if last_purchase:
                    days_since = (datetime.utcnow() - last_purchase).days
                    if days_since > self.recommendation_rules['tax_loss_harvesting']['wash_sale_period']:
                        opportunities.append(holding)
        
        return opportunities
    
    def _is_year_end(self) -> bool:
        """Check if it's near year end (Oct-Dec)"""
        return datetime.utcnow().month >= 10
    
    def _needs_estimated_tax_adjustment(self, user_profile: Dict[str, Any]) -> bool:
        """Check if user needs to adjust estimated tax payments"""
        return user_profile.get('self_employed', False) or \
               user_profile.get('investment_income', 0) > 10000
    
    def _calculate_risk_metrics(
        self,
        portfolio: Dict[str, Any],
        market_data: Dict[str, Any]
    ) -> Dict[str, float]:
        """Calculate portfolio risk metrics"""
        
        # Simplified risk calculation
        portfolio_volatility = portfolio.get('volatility', 0.15)
        portfolio_value = portfolio.get('total_value', 100000)
        
        return {
            'var_95': portfolio_value * portfolio_volatility * 1.645,
            'var_99': portfolio_value * portfolio_volatility * 2.326,
            'max_drawdown': portfolio.get('max_drawdown', 0.20),
            'sharpe_ratio': portfolio.get('sharpe_ratio', 1.0),
            'beta': portfolio.get('beta', 1.0)
        }
    
    def _has_adequate_emergency_fund(self, user_profile: Dict[str, Any]) -> bool:
        """Check if user has adequate emergency fund"""
        
        monthly_expenses = user_profile.get('monthly_expenses', 5000)
        emergency_fund = user_profile.get('emergency_fund', 0)
        required_months = self.recommendation_rules['emergency_fund']['months_expenses']
        
        return emergency_fund >= monthly_expenses * required_months
    
    def _needs_insurance_review(self, user_profile: Dict[str, Any]) -> bool:
        """Check if user needs insurance review"""
        
        last_review = user_profile.get('last_insurance_review')
        if not last_review:
            return True
        
        days_since = (datetime.utcnow() - last_review).days
        return days_since > 365  # Annual review
    
    def _identify_sector_opportunities(
        self,
        market_data: Dict[str, Any],
        portfolio: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Identify sector rotation opportunities"""
        
        opportunities = []
        sector_performance = market_data.get('sector_performance', {})
        portfolio_sectors = portfolio.get('sector_allocation', {})
        
        for sector, performance in sector_performance.items():
            if performance > 0.15:  # 15% outperformance
                current_weight = portfolio_sectors.get(sector, 0)
                if current_weight < 0.10:  # Underweight
                    opportunities.append({
                        'sector': sector,
                        'performance': performance,
                        'current_weight': current_weight,
                        'recommended_weight': 0.15
                    })
        
        return opportunities
    
    def _identify_value_opportunities(
        self,
        market_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Identify value investment opportunities"""
        
        # This would normally query a database of stock metrics
        # Simplified version for demonstration
        value_stocks = market_data.get('value_stocks', [])
        
        return [
            stock for stock in value_stocks
            if stock.get('pe_ratio', 20) < 15 and
            stock.get('pb_ratio', 3) < 2
        ]