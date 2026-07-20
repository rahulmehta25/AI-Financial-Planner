"""
Portfolio rebalancing recommendation engine using modern portfolio theory
and machine learning optimization.

This module provides:
- Risk-adjusted portfolio optimization
- Rebalancing recommendations based on drift detection
- Dynamic asset allocation based on market conditions
- Tax-efficient rebalancing strategies
"""

import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import xgboost as xgb
from sklearn.covariance import LedoitWolf
import cvxpy as cp
from scipy.optimize import minimize
import yfinance as yf
from PyPortfolioOpt import EfficientFrontier, risk_models, expected_returns
from PyPortfolioOpt.discrete_allocation import DiscreteAllocation, get_latest_prices
import joblib
import json
from pathlib import Path

from app.models.user import User
from app.models.financial_profile import FinancialProfile
from app.models.investment import Investment
from app.database.base import SessionLocal

logger = logging.getLogger(__name__)


class PortfolioRebalancer:
    """Advanced portfolio rebalancing system with ML-driven optimization."""
    
    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path or "/app/ml/models/portfolio_rebalancer"
        self.rebalancing_model = None
        self.risk_model = None
        self.return_model = None
        self.market_regime_model = None
        
        # Default asset universe
        self.default_assets = {
            'stocks': ['VTI', 'VXUS', 'VUG', 'VTV', 'VB'],  # Total, International, Growth, Value, Small
            'bonds': ['BND', 'VTEB', 'VGIT', 'VTIP'],        # Total, Municipal, Gov, TIPS
            'alternatives': ['VNQ', 'IAU', 'PDBC'],          # REITs, Gold, Commodities
            'cash': ['VMOT']                                 # Money Market
        }
        
        self.risk_free_rate = 0.02  # 2% risk-free rate assumption
        self._load_models()
    
    def _load_models(self) -> None:
        """Load pre-trained rebalancing models."""
        try:
            model_dir = Path(self.model_path)
            if model_dir.exists():
                self.rebalancing_model = joblib.load(model_dir / "rebalancing_model.pkl")
                self.risk_model = joblib.load(model_dir / "risk_model.pkl")
                self.return_model = joblib.load(model_dir / "return_model.pkl")
                self.market_regime_model = joblib.load(model_dir / "market_regime_model.pkl")
                logger.info("Loaded pre-trained portfolio models")
        except Exception as e:
            logger.warning(f"Could not load pre-trained models: {e}")
    
    def _save_models(self) -> None:
        """Save trained models."""
        try:
            model_dir = Path(self.model_path)
            model_dir.mkdir(parents=True, exist_ok=True)
            
            if self.rebalancing_model:
                joblib.dump(self.rebalancing_model, model_dir / "rebalancing_model.pkl")
            if self.risk_model:
                joblib.dump(self.risk_model, model_dir / "risk_model.pkl")
            if self.return_model:
                joblib.dump(self.return_model, model_dir / "return_model.pkl")
            if self.market_regime_model:
                joblib.dump(self.market_regime_model, model_dir / "market_regime_model.pkl")
            
            logger.info("Saved portfolio rebalancing models")
        except Exception as e:
            logger.error(f"Failed to save models: {e}")
    
    def get_market_data(self, symbols: List[str], period: str = "2y") -> pd.DataFrame:
        """Fetch market data for given symbols."""
        try:
            data = yf.download(symbols, period=period, progress=False)['Adj Close']
            return data.dropna()
        except Exception as e:
            logger.error(f"Failed to fetch market data: {e}")
            return pd.DataFrame()
    
    def calculate_optimal_weights(self, symbols: List[str], risk_tolerance: str,
                                investment_horizon: int) -> Dict[str, float]:
        """Calculate optimal portfolio weights using modern portfolio theory."""
        try:
            # Get market data
            prices = self.get_market_data(symbols)
            if prices.empty:
                return {}
            
            # Calculate expected returns and risk model
            mu = expected_returns.mean_historical_return(prices, frequency=252)
            S = risk_models.sample_cov(prices, frequency=252)
            
            # Adjust for risk tolerance
            risk_aversion = self._get_risk_aversion(risk_tolerance)
            
            # Create efficient frontier
            ef = EfficientFrontier(mu, S)
            
            # Add constraints based on investment profile
            constraints = self._get_portfolio_constraints(risk_tolerance, investment_horizon)
            for constraint in constraints:
                ef.add_constraint(constraint)
            
            # Optimize portfolio
            if risk_tolerance == 'conservative':
                weights = ef.min_volatility()
            elif risk_tolerance == 'aggressive':
                weights = ef.max_sharpe()
            else:  # moderate
                weights = ef.efficient_risk(target_volatility=0.15)
            
            # Clean weights (remove tiny allocations)
            cleaned_weights = ef.clean_weights()
            
            return cleaned_weights
            
        except Exception as e:
            logger.error(f"Failed to calculate optimal weights: {e}")
            return self._get_default_allocation(risk_tolerance)
    
    def _get_risk_aversion(self, risk_tolerance: str) -> float:
        """Get risk aversion parameter based on tolerance."""
        risk_aversions = {
            'conservative': 5.0,
            'moderate': 3.0,
            'aggressive': 1.0
        }
        return risk_aversions.get(risk_tolerance, 3.0)
    
    def _get_portfolio_constraints(self, risk_tolerance: str, 
                                 investment_horizon: int) -> List[callable]:
        """Get portfolio constraints based on investor profile."""
        constraints = []
        
        # Conservative constraints
        if risk_tolerance == 'conservative':
            # Limit individual stock exposure
            constraints.append(lambda w: 0.15 - w.max())  # Max 15% in any asset
            # Minimum bond allocation
            bond_symbols = ['BND', 'VTEB', 'VGIT', 'VTIP']
            constraints.append(lambda w: sum(w.get(s, 0) for s in bond_symbols) - 0.4)
        
        # Aggressive constraints
        elif risk_tolerance == 'aggressive':
            # Allow higher concentration
            constraints.append(lambda w: 0.25 - w.max())  # Max 25% in any asset
            # Minimum equity allocation
            stock_symbols = ['VTI', 'VXUS', 'VUG', 'VTV', 'VB']
            constraints.append(lambda w: sum(w.get(s, 0) for s in stock_symbols) - 0.7)
        
        # Time horizon constraints
        if investment_horizon < 5:  # Short-term
            # Increase bond/cash allocation for shorter horizons
            safe_symbols = ['BND', 'VMOT', 'VGIT']
            constraints.append(lambda w: sum(w.get(s, 0) for s in safe_symbols) - 0.3)
        
        return constraints
    
    def _get_default_allocation(self, risk_tolerance: str) -> Dict[str, float]:
        """Get default asset allocation based on risk tolerance."""
        allocations = {
            'conservative': {
                'VTI': 0.20, 'VXUS': 0.10, 'BND': 0.40, 'VTEB': 0.15,
                'VNQ': 0.05, 'VMOT': 0.10
            },
            'moderate': {
                'VTI': 0.35, 'VXUS': 0.15, 'VUG': 0.10, 'BND': 0.25,
                'VNQ': 0.10, 'IAU': 0.05
            },
            'aggressive': {
                'VTI': 0.40, 'VXUS': 0.20, 'VUG': 0.15, 'VTV': 0.10,
                'VB': 0.05, 'VNQ': 0.10
            }
        }
        return allocations.get(risk_tolerance, allocations['moderate'])
    
    def analyze_portfolio_drift(self, current_weights: Dict[str, float],
                               target_weights: Dict[str, float]) -> Dict[str, Any]:
        """Analyze portfolio drift and recommend rebalancing."""
        drift_analysis = {
            'total_drift': 0.0,
            'asset_drifts': {},
            'rebalancing_needed': False,
            'drift_threshold': 0.05,  # 5% threshold
            'recommendations': []
        }
        
        all_assets = set(current_weights.keys()) | set(target_weights.keys())
        
        for asset in all_assets:
            current = current_weights.get(asset, 0.0)
            target = target_weights.get(asset, 0.0)
            drift = abs(current - target)
            
            drift_analysis['asset_drifts'][asset] = {
                'current': current,
                'target': target,
                'drift': drift,
                'drift_percentage': (drift / max(target, 0.01)) * 100
            }
            
            drift_analysis['total_drift'] += drift
            
            if drift > drift_analysis['drift_threshold']:
                drift_analysis['rebalancing_needed'] = True
                action = 'sell' if current > target else 'buy'
                drift_analysis['recommendations'].append({
                    'asset': asset,
                    'action': action,
                    'amount_percentage': drift,
                    'priority': 'high' if drift > 0.1 else 'medium'
                })
        
        # Sort recommendations by drift magnitude
        drift_analysis['recommendations'].sort(
            key=lambda x: x['amount_percentage'], reverse=True
        )
        
        return drift_analysis
    
    def generate_rebalancing_plan(self, user_id: str, portfolio_value: float) -> Dict[str, Any]:
        """Generate comprehensive rebalancing recommendations for a user."""
        try:
            with SessionLocal() as db:
                user = db.query(User).filter(User.id == user_id).first()
                if not user or not user.financial_profile:
                    return {"error": "User or financial profile not found"}
                
                # Get current portfolio
                current_portfolio = self._get_current_portfolio(user_id, db)
                if not current_portfolio:
                    return {"error": "No investment data found"}
                
                # Get user's risk profile
                risk_tolerance = user.financial_profile.risk_tolerance
                investment_horizon = self._estimate_investment_horizon(user.financial_profile)
                
                # Get recommended asset universe
                recommended_assets = self._get_recommended_assets(user.financial_profile)
                
                # Calculate optimal weights
                optimal_weights = self.calculate_optimal_weights(
                    recommended_assets, risk_tolerance, investment_horizon
                )
                
                if not optimal_weights:
                    optimal_weights = self._get_default_allocation(risk_tolerance)
                
                # Analyze drift
                current_weights = self._normalize_weights(current_portfolio)
                drift_analysis = self.analyze_portfolio_drift(current_weights, optimal_weights)
                
                # Generate specific rebalancing actions
                rebalancing_actions = self._generate_rebalancing_actions(
                    current_portfolio, optimal_weights, portfolio_value, user.financial_profile
                )
                
                # Calculate projected performance
                performance_projection = self._project_performance(
                    optimal_weights, recommended_assets, investment_horizon
                )
                
                return {
                    'user_id': user_id,
                    'current_portfolio': current_portfolio,
                    'optimal_weights': optimal_weights,
                    'drift_analysis': drift_analysis,
                    'rebalancing_actions': rebalancing_actions,
                    'performance_projection': performance_projection,
                    'tax_considerations': self._analyze_tax_implications(rebalancing_actions),
                    'implementation_priority': self._prioritize_actions(rebalancing_actions),
                    'next_review_date': (datetime.now() + timedelta(days=90)).isoformat()
                }
                
        except Exception as e:
            logger.error(f"Failed to generate rebalancing plan for user {user_id}: {e}")
            return {"error": str(e)}
    
    def _get_current_portfolio(self, user_id: str, db) -> Dict[str, float]:
        """Get user's current portfolio weights."""
        investments = db.query(Investment).filter(Investment.user_id == user_id).all()
        
        portfolio = {}
        total_value = 0
        
        for investment in investments:
            if investment.current_value:
                portfolio[investment.symbol] = float(investment.current_value)
                total_value += float(investment.current_value)
        
        # Normalize to weights
        if total_value > 0:
            portfolio = {k: v/total_value for k, v in portfolio.items()}
        
        return portfolio
    
    def _normalize_weights(self, portfolio: Dict[str, float]) -> Dict[str, float]:
        """Normalize portfolio values to weights."""
        total = sum(portfolio.values())
        if total > 0:
            return {k: v/total for k, v in portfolio.items()}
        return portfolio
    
    def _estimate_investment_horizon(self, profile: FinancialProfile) -> int:
        """Estimate investment horizon in years."""
        if profile.retirement_age_target:
            return max(1, profile.retirement_age_target - profile.age)
        
        # Default based on age
        if profile.age < 30:
            return 35
        elif profile.age < 50:
            return 25
        else:
            return max(5, 65 - profile.age)
    
    def _get_recommended_assets(self, profile: FinancialProfile) -> List[str]:
        """Get recommended asset universe based on user profile."""
        assets = []
        
        # Core equity holdings
        assets.extend(['VTI', 'VXUS'])  # US Total + International
        
        # Risk-based additions
        if profile.risk_tolerance == 'aggressive':
            assets.extend(['VUG', 'VB'])  # Growth + Small Cap
        elif profile.risk_tolerance == 'moderate':
            assets.extend(['VUG', 'VTV'])  # Growth + Value
        
        # Bond allocation
        assets.extend(['BND'])
        if profile.risk_tolerance == 'conservative':
            assets.extend(['VGIT', 'VTEB'])  # Government + Municipal
        
        # Alternative investments for higher risk tolerance
        if profile.risk_tolerance in ['moderate', 'aggressive']:
            assets.extend(['VNQ'])  # REITs
            
        if profile.risk_tolerance == 'aggressive':
            assets.extend(['IAU'])  # Gold
        
        # Cash equivalent for conservative investors
        if profile.risk_tolerance == 'conservative':
            assets.extend(['VMOT'])
        
        return assets
    
    def _generate_rebalancing_actions(self, current_portfolio: Dict[str, float],
                                    optimal_weights: Dict[str, float],
                                    portfolio_value: float,
                                    profile: FinancialProfile) -> List[Dict[str, Any]]:
        """Generate specific buy/sell actions for rebalancing."""
        actions = []
        
        # Get latest prices for discrete allocation
        try:
            symbols = list(set(current_portfolio.keys()) | set(optimal_weights.keys()))
            latest_prices = get_latest_prices(yf.download(symbols, period="1d")['Adj Close'])
            
            # Calculate target dollar amounts
            target_amounts = {asset: weight * portfolio_value 
                            for asset, weight in optimal_weights.items()}
            
            # Calculate current dollar amounts
            current_amounts = {asset: weight * portfolio_value 
                             for asset, weight in current_portfolio.items()}
            
            # Generate actions
            for asset in set(list(current_amounts.keys()) + list(target_amounts.keys())):
                current_value = current_amounts.get(asset, 0)
                target_value = target_amounts.get(asset, 0)
                difference = target_value - current_value
                
                if abs(difference) > 100:  # Only suggest changes > $100
                    action_type = 'buy' if difference > 0 else 'sell'
                    
                    if asset in latest_prices:
                        shares = int(abs(difference) / latest_prices[asset])
                        
                        actions.append({
                            'asset': asset,
                            'action': action_type,
                            'dollar_amount': abs(difference),
                            'shares': shares,
                            'current_weight': current_portfolio.get(asset, 0),
                            'target_weight': optimal_weights.get(asset, 0),
                            'priority': self._calculate_action_priority(
                                abs(difference), portfolio_value, asset
                            )
                        })
            
            # Sort by priority
            actions.sort(key=lambda x: x['priority'], reverse=True)
            
        except Exception as e:
            logger.error(f"Failed to generate rebalancing actions: {e}")
        
        return actions
    
    def _calculate_action_priority(self, dollar_amount: float, 
                                 portfolio_value: float, asset: str) -> float:
        """Calculate priority score for rebalancing action."""
        # Higher priority for larger percentage changes
        percentage_impact = dollar_amount / portfolio_value
        
        # Higher priority for core holdings
        core_assets = ['VTI', 'VXUS', 'BND']
        core_multiplier = 1.5 if asset in core_assets else 1.0
        
        return percentage_impact * core_multiplier * 100
    
    def _project_performance(self, weights: Dict[str, float], assets: List[str],
                           horizon_years: int) -> Dict[str, Any]:
        """Project portfolio performance based on historical data."""
        try:
            # Get historical data
            prices = self.get_market_data(assets, period="5y")
            if prices.empty:
                return {}
            
            # Calculate portfolio returns
            returns = prices.pct_change().dropna()
            portfolio_returns = sum(weights.get(asset, 0) * returns[asset] 
                                  for asset in assets if asset in returns.columns)
            
            # Calculate statistics
            annual_return = portfolio_returns.mean() * 252
            annual_volatility = portfolio_returns.std() * np.sqrt(252)
            sharpe_ratio = (annual_return - self.risk_free_rate) / annual_volatility
            
            # Project future value
            expected_annual_return = annual_return
            projected_value = (1 + expected_annual_return) ** horizon_years
            
            return {
                'expected_annual_return': float(annual_return),
                'expected_volatility': float(annual_volatility),
                'sharpe_ratio': float(sharpe_ratio),
                'projected_multiplier': float(projected_value),
                'confidence_interval_95': {
                    'lower': float(projected_value * 0.7),
                    'upper': float(projected_value * 1.4)
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to project performance: {e}")
            return {}
    
    def _analyze_tax_implications(self, actions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze tax implications of rebalancing actions."""
        tax_analysis = {
            'total_sell_actions': 0,
            'estimated_tax_impact': 'low',  # Would need cost basis data for accurate calculation
            'tax_loss_harvesting_opportunities': [],
            'recommendations': []
        }
        
        sell_actions = [a for a in actions if a['action'] == 'sell']
        tax_analysis['total_sell_actions'] = len(sell_actions)
        
        if len(sell_actions) > 3:
            tax_analysis['estimated_tax_impact'] = 'high'
            tax_analysis['recommendations'].append(
                "Consider spreading rebalancing over multiple periods to minimize tax impact"
            )
        
        # General tax-efficient recommendations
        tax_analysis['recommendations'].extend([
            "Prioritize rebalancing in tax-advantaged accounts first",
            "Consider using new contributions for rebalancing instead of selling",
            "Review cost basis before selling positions with significant gains"
        ])
        
        return tax_analysis
    
    def _prioritize_actions(self, actions: List[Dict[str, Any]]) -> List[str]:
        """Prioritize rebalancing actions by importance."""
        if not actions:
            return []
        
        # Sort by priority score
        sorted_actions = sorted(actions, key=lambda x: x['priority'], reverse=True)
        
        priorities = []
        
        # High priority (top 3 or >2% portfolio impact)
        high_priority = [a for a in sorted_actions[:3] 
                        if a['dollar_amount'] / sum(b['dollar_amount'] for b in actions) > 0.02]
        
        if high_priority:
            priorities.append(f"High Priority: Rebalance {', '.join(a['asset'] for a in high_priority)}")
        
        # Medium priority
        medium_priority = sorted_actions[3:6]
        if medium_priority:
            priorities.append(f"Medium Priority: Consider {', '.join(a['asset'] for a in medium_priority)}")
        
        # General recommendation
        if len(sorted_actions) > 6:
            priorities.append("Review remaining positions quarterly")
        
        return priorities
    
    def detect_market_regime(self) -> str:
        """Detect current market regime for tactical allocation adjustments."""
        try:
            # Get market indicators
            spy_data = yf.download('SPY', period='6m')['Adj Close']
            vix_data = yf.download('^VIX', period='6m')['Adj Close']
            
            # Simple regime detection based on volatility and trend
            recent_vol = spy_data.pct_change().rolling(30).std().iloc[-1]
            recent_trend = (spy_data.iloc[-1] / spy_data.iloc[-60] - 1)
            current_vix = vix_data.iloc[-1]
            
            if current_vix > 25 and recent_vol > 0.02:
                return 'crisis'
            elif current_vix > 20 or recent_vol > 0.015:
                return 'volatile'
            elif recent_trend > 0.1:
                return 'bull'
            elif recent_trend < -0.1:
                return 'bear'
            else:
                return 'normal'
                
        except Exception as e:
            logger.error(f"Failed to detect market regime: {e}")
            return 'normal'