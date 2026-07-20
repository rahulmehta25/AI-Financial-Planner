"""
Advanced Risk Models for Portfolio Management

This module implements comprehensive risk assessment models including:
- Value at Risk (VaR) and Conditional VaR (CVaR)
- Stress testing and scenario analysis
- Factor analysis and risk decomposition
- Liquidity risk assessment
- Monte Carlo simulations with fat-tail distributions
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Union, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from scipy import stats
from scipy.optimize import minimize
from scipy.stats import norm, t, skew, kurtosis
import asyncio
import logging
from enum import Enum

logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    """Risk classification levels"""
    MINIMAL = "minimal"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class VaRResult:
    """Value at Risk calculation result"""
    var_95: float
    var_99: float
    cvar_95: float  # Conditional VaR (Expected Shortfall)
    cvar_99: float
    method: str
    confidence_intervals: Dict[float, float] = field(default_factory=dict)
    backtest_results: Optional[Dict] = None


@dataclass
class StressTestResult:
    """Stress test scenario result"""
    scenario_name: str
    portfolio_impact: float
    position_impacts: Dict[str, float]
    risk_metrics: Dict[str, float]
    recovery_time: Optional[int] = None  # Days to recover
    probability: Optional[float] = None


@dataclass
class FactorRisk:
    """Factor risk decomposition"""
    factor_name: str
    exposure: float
    contribution_to_var: float
    marginal_var: float
    component_var: float
    beta: float


@dataclass
class LiquidityRisk:
    """Liquidity risk assessment"""
    liquidation_cost: float
    days_to_liquidate: float
    market_impact: float
    bid_ask_spread: float
    volume_constraint: float
    liquidity_score: float  # 0-100


@dataclass
class RiskReport:
    """Comprehensive risk report"""
    timestamp: datetime
    var_results: Dict[str, VaRResult]
    stress_tests: List[StressTestResult]
    factor_risks: List[FactorRisk]
    liquidity_risk: LiquidityRisk
    correlation_matrix: np.ndarray
    risk_score: float
    risk_level: RiskLevel
    recommendations: List[str]
    r_multiples: Dict[str, float]
    expectancy: float
    max_drawdown: float
    recovery_period: Optional[int]


class RiskModelsEngine:
    """
    Advanced risk modeling engine for comprehensive portfolio risk assessment
    """
    
    def __init__(self, confidence_levels: List[float] = None):
        """
        Initialize risk models engine
        
        Args:
            confidence_levels: List of confidence levels for VaR calculations
        """
        self.confidence_levels = confidence_levels or [0.95, 0.99]
        self.historical_window = 252  # Trading days
        self.monte_carlo_simulations = 10000
        self.stress_scenarios = self._initialize_stress_scenarios()
        self.risk_factors = self._initialize_risk_factors()
        
    def _initialize_stress_scenarios(self) -> Dict[str, Dict]:
        """Initialize historical and hypothetical stress test scenarios"""
        return {
            # Historical scenarios
            '2008_financial_crisis': {
                'name': '2008 Financial Crisis',
                'equity': -0.37,
                'bonds': 0.05,
                'commodities': -0.35,
                'real_estate': -0.40,
                'volatility_multiplier': 3.5,
                'correlation_shock': 0.3,
                'probability': 0.05
            },
            'covid_crash': {
                'name': 'COVID-19 Market Crash',
                'equity': -0.34,
                'bonds': 0.08,
                'commodities': -0.30,
                'real_estate': -0.15,
                'volatility_multiplier': 2.8,
                'correlation_shock': 0.25,
                'probability': 0.07
            },
            'dotcom_bubble': {
                'name': 'Dot-com Bubble Burst',
                'equity': -0.49,
                'bonds': 0.10,
                'commodities': 0.05,
                'real_estate': 0.15,
                'volatility_multiplier': 2.5,
                'correlation_shock': 0.2,
                'probability': 0.03
            },
            'black_monday': {
                'name': 'Black Monday 1987',
                'equity': -0.22,
                'bonds': 0.02,
                'commodities': -0.05,
                'real_estate': -0.10,
                'volatility_multiplier': 4.0,
                'correlation_shock': 0.4,
                'probability': 0.02
            },
            # Hypothetical scenarios
            'inflation_spike': {
                'name': 'Severe Inflation Spike',
                'equity': -0.15,
                'bonds': -0.25,
                'commodities': 0.30,
                'real_estate': 0.10,
                'volatility_multiplier': 2.0,
                'correlation_shock': 0.15,
                'probability': 0.10
            },
            'deflation': {
                'name': 'Deflationary Spiral',
                'equity': -0.20,
                'bonds': 0.15,
                'commodities': -0.40,
                'real_estate': -0.25,
                'volatility_multiplier': 2.2,
                'correlation_shock': 0.2,
                'probability': 0.08
            },
            'geopolitical_crisis': {
                'name': 'Major Geopolitical Crisis',
                'equity': -0.25,
                'bonds': 0.05,
                'commodities': 0.20,
                'real_estate': -0.10,
                'volatility_multiplier': 3.0,
                'correlation_shock': 0.35,
                'probability': 0.06
            },
            'tech_collapse': {
                'name': 'Technology Sector Collapse',
                'equity': -0.40,
                'bonds': 0.12,
                'commodities': -0.05,
                'real_estate': -0.05,
                'volatility_multiplier': 2.5,
                'correlation_shock': 0.25,
                'probability': 0.04
            }
        }
        
    def _initialize_risk_factors(self) -> List[str]:
        """Initialize risk factors for factor analysis"""
        return [
            'market_beta',
            'size_factor',
            'value_factor',
            'momentum_factor',
            'quality_factor',
            'low_volatility_factor',
            'interest_rate_sensitivity',
            'credit_spread_sensitivity',
            'commodity_exposure',
            'currency_exposure'
        ]
    
    async def calculate_var_suite(
        self,
        returns: np.ndarray,
        portfolio_value: float,
        holding_period: int = 1
    ) -> Dict[str, VaRResult]:
        """
        Calculate VaR using multiple methods
        
        Args:
            returns: Historical returns array
            portfolio_value: Current portfolio value
            holding_period: Holding period in days
            
        Returns:
            Dictionary of VaR results by method
        """
        results = {}
        
        # Scale for holding period
        sqrt_hp = np.sqrt(holding_period)
        
        # 1. Historical VaR
        results['historical'] = self._calculate_historical_var(
            returns, portfolio_value, holding_period
        )
        
        # 2. Parametric VaR (variance-covariance)
        results['parametric'] = self._calculate_parametric_var(
            returns, portfolio_value, holding_period
        )
        
        # 3. Monte Carlo VaR
        results['monte_carlo'] = await self._calculate_monte_carlo_var(
            returns, portfolio_value, holding_period
        )
        
        # 4. Cornish-Fisher VaR (accounts for skewness and kurtosis)
        results['cornish_fisher'] = self._calculate_cornish_fisher_var(
            returns, portfolio_value, holding_period
        )
        
        # 5. GARCH VaR (for time-varying volatility)
        results['garch'] = self._calculate_garch_var(
            returns, portfolio_value, holding_period
        )
        
        # Perform backtesting
        for method_name, var_result in results.items():
            var_result.backtest_results = self._backtest_var(
                returns, var_result.var_95, var_result.var_99
            )
        
        return results
    
    def _calculate_historical_var(
        self,
        returns: np.ndarray,
        portfolio_value: float,
        holding_period: int
    ) -> VaRResult:
        """Calculate historical VaR using empirical distribution"""
        
        # Scale returns for holding period
        scaled_returns = returns * np.sqrt(holding_period)
        
        # Calculate VaR at different confidence levels
        var_95 = np.percentile(scaled_returns, 5) * portfolio_value
        var_99 = np.percentile(scaled_returns, 1) * portfolio_value
        
        # Calculate CVaR (Expected Shortfall)
        cvar_95 = scaled_returns[scaled_returns <= np.percentile(scaled_returns, 5)].mean() * portfolio_value
        cvar_99 = scaled_returns[scaled_returns <= np.percentile(scaled_returns, 1)].mean() * portfolio_value
        
        # Bootstrap confidence intervals
        confidence_intervals = self._bootstrap_confidence_intervals(
            scaled_returns, portfolio_value
        )
        
        return VaRResult(
            var_95=abs(var_95),
            var_99=abs(var_99),
            cvar_95=abs(cvar_95),
            cvar_99=abs(cvar_99),
            method='historical',
            confidence_intervals=confidence_intervals
        )
    
    def _calculate_parametric_var(
        self,
        returns: np.ndarray,
        portfolio_value: float,
        holding_period: int
    ) -> VaRResult:
        """Calculate parametric VaR using normal distribution"""
        
        mean_return = returns.mean()
        std_return = returns.std()
        
        # Scale for holding period
        mean_hp = mean_return * holding_period
        std_hp = std_return * np.sqrt(holding_period)
        
        # Calculate VaR using z-scores
        z_95 = norm.ppf(0.05)
        z_99 = norm.ppf(0.01)
        
        var_95 = -(mean_hp + z_95 * std_hp) * portfolio_value
        var_99 = -(mean_hp + z_99 * std_hp) * portfolio_value
        
        # Calculate CVaR analytically for normal distribution
        cvar_95 = -(mean_hp - std_hp * norm.pdf(z_95) / 0.05) * portfolio_value
        cvar_99 = -(mean_hp - std_hp * norm.pdf(z_99) / 0.01) * portfolio_value
        
        return VaRResult(
            var_95=abs(var_95),
            var_99=abs(var_99),
            cvar_95=abs(cvar_95),
            cvar_99=abs(cvar_99),
            method='parametric',
            confidence_intervals={}
        )
    
    async def _calculate_monte_carlo_var(
        self,
        returns: np.ndarray,
        portfolio_value: float,
        holding_period: int
    ) -> VaRResult:
        """Calculate VaR using Monte Carlo simulation with fat-tail distributions"""
        
        mean_return = returns.mean()
        std_return = returns.std()
        
        # Fit Student's t-distribution for fat tails
        params = stats.t.fit(returns)
        df, loc, scale = params
        
        # Generate Monte Carlo simulations
        simulated_returns = stats.t.rvs(
            df=df,
            loc=loc * holding_period,
            scale=scale * np.sqrt(holding_period),
            size=self.monte_carlo_simulations
        )
        
        # Calculate portfolio values
        simulated_values = portfolio_value * (1 + simulated_returns)
        losses = portfolio_value - simulated_values
        
        # Calculate VaR and CVaR
        var_95 = np.percentile(losses, 95)
        var_99 = np.percentile(losses, 99)
        
        cvar_95 = losses[losses >= var_95].mean()
        cvar_99 = losses[losses >= var_99].mean()
        
        return VaRResult(
            var_95=abs(var_95),
            var_99=abs(var_99),
            cvar_95=abs(cvar_95),
            cvar_99=abs(cvar_99),
            method='monte_carlo',
            confidence_intervals={}
        )
    
    def _calculate_cornish_fisher_var(
        self,
        returns: np.ndarray,
        portfolio_value: float,
        holding_period: int
    ) -> VaRResult:
        """Calculate VaR using Cornish-Fisher expansion (accounts for higher moments)"""
        
        mean_return = returns.mean() * holding_period
        std_return = returns.std() * np.sqrt(holding_period)
        skewness = skew(returns)
        excess_kurtosis = kurtosis(returns)
        
        # Cornish-Fisher z-score adjustment
        def cornish_fisher_z(alpha):
            z_alpha = norm.ppf(alpha)
            cf_z = (z_alpha + 
                    (z_alpha**2 - 1) * skewness / 6 +
                    (z_alpha**3 - 3*z_alpha) * excess_kurtosis / 24 -
                    (2*z_alpha**3 - 5*z_alpha) * skewness**2 / 36)
            return cf_z
        
        # Calculate adjusted VaR
        cf_z_95 = cornish_fisher_z(0.05)
        cf_z_99 = cornish_fisher_z(0.01)
        
        var_95 = -(mean_return + cf_z_95 * std_return) * portfolio_value
        var_99 = -(mean_return + cf_z_99 * std_return) * portfolio_value
        
        # Approximate CVaR
        cvar_95 = var_95 * 1.2  # Simple approximation
        cvar_99 = var_99 * 1.25
        
        return VaRResult(
            var_95=abs(var_95),
            var_99=abs(var_99),
            cvar_95=abs(cvar_95),
            cvar_99=abs(cvar_99),
            method='cornish_fisher',
            confidence_intervals={}
        )
    
    def _calculate_garch_var(
        self,
        returns: np.ndarray,
        portfolio_value: float,
        holding_period: int
    ) -> VaRResult:
        """Calculate VaR using GARCH model for time-varying volatility"""
        
        # Simplified GARCH(1,1) implementation
        # In production, use arch library for proper GARCH modeling
        
        # Estimate current volatility using EWMA as proxy
        lambda_param = 0.94
        squared_returns = returns ** 2
        
        volatility = np.sqrt(
            np.average(squared_returns, 
                      weights=lambda_param ** np.arange(len(squared_returns)-1, -1, -1))
        )
        
        # Scale for holding period
        volatility_hp = volatility * np.sqrt(holding_period)
        mean_hp = returns.mean() * holding_period
        
        # Calculate VaR
        z_95 = norm.ppf(0.05)
        z_99 = norm.ppf(0.01)
        
        var_95 = -(mean_hp + z_95 * volatility_hp) * portfolio_value
        var_99 = -(mean_hp + z_99 * volatility_hp) * portfolio_value
        
        # CVaR approximation
        cvar_95 = -(mean_hp - volatility_hp * norm.pdf(z_95) / 0.05) * portfolio_value
        cvar_99 = -(mean_hp - volatility_hp * norm.pdf(z_99) / 0.01) * portfolio_value
        
        return VaRResult(
            var_95=abs(var_95),
            var_99=abs(var_99),
            cvar_95=abs(cvar_95),
            cvar_99=abs(cvar_99),
            method='garch',
            confidence_intervals={}
        )
    
    def _bootstrap_confidence_intervals(
        self,
        returns: np.ndarray,
        portfolio_value: float,
        n_bootstrap: int = 1000
    ) -> Dict[float, float]:
        """Calculate confidence intervals using bootstrap"""
        
        intervals = {}
        for confidence in self.confidence_levels:
            bootstrap_vars = []
            
            for _ in range(n_bootstrap):
                sample = np.random.choice(returns, size=len(returns), replace=True)
                var = np.percentile(sample, (1 - confidence) * 100) * portfolio_value
                bootstrap_vars.append(abs(var))
            
            intervals[confidence] = {
                'lower': np.percentile(bootstrap_vars, 2.5),
                'upper': np.percentile(bootstrap_vars, 97.5)
            }
        
        return intervals
    
    def _backtest_var(
        self,
        returns: np.ndarray,
        var_95: float,
        var_99: float
    ) -> Dict:
        """Backtest VaR model using Kupiec test"""
        
        # Count violations
        violations_95 = np.sum(returns < -var_95 / 100)  # Assuming percentage returns
        violations_99 = np.sum(returns < -var_99 / 100)
        
        n_obs = len(returns)
        
        # Kupiec POF test
        def kupiec_test(violations, confidence, n):
            p = 1 - confidence
            expected = n * p
            if violations == 0:
                violations = 0.5  # Avoid log(0)
            
            likelihood_ratio = 2 * (
                violations * np.log(violations / expected) +
                (n - violations) * np.log((n - violations) / (n - expected))
            )
            p_value = 1 - stats.chi2.cdf(likelihood_ratio, 1)
            return p_value
        
        return {
            'violations_95': violations_95,
            'expected_violations_95': n_obs * 0.05,
            'kupiec_pvalue_95': kupiec_test(violations_95, 0.95, n_obs),
            'violations_99': violations_99,
            'expected_violations_99': n_obs * 0.01,
            'kupiec_pvalue_99': kupiec_test(violations_99, 0.99, n_obs)
        }
    
    async def run_stress_tests(
        self,
        portfolio_positions: Dict[str, float],
        position_sensitivities: Dict[str, Dict[str, float]]
    ) -> List[StressTestResult]:
        """
        Run comprehensive stress tests on portfolio
        
        Args:
            portfolio_positions: Dictionary of position values
            position_sensitivities: Sensitivities to various risk factors
            
        Returns:
            List of stress test results
        """
        results = []
        
        for scenario_id, scenario in self.stress_scenarios.items():
            # Calculate position impacts
            position_impacts = {}
            total_impact = 0
            
            for position, value in portfolio_positions.items():
                # Get asset class for position
                asset_class = self._get_asset_class(position)
                
                # Apply shock based on asset class
                if asset_class in scenario:
                    shock = scenario[asset_class]
                    impact = value * shock
                    position_impacts[position] = impact
                    total_impact += impact
            
            # Calculate additional risk metrics under stress
            stressed_metrics = self._calculate_stressed_metrics(
                portfolio_positions,
                scenario,
                position_sensitivities
            )
            
            # Estimate recovery time
            recovery_time = self._estimate_recovery_time(
                abs(total_impact),
                scenario.get('volatility_multiplier', 1.0)
            )
            
            results.append(StressTestResult(
                scenario_name=scenario['name'],
                portfolio_impact=total_impact,
                position_impacts=position_impacts,
                risk_metrics=stressed_metrics,
                recovery_time=recovery_time,
                probability=scenario.get('probability')
            ))
        
        return results
    
    def _get_asset_class(self, position: str) -> str:
        """Determine asset class for a position"""
        # Simplified mapping - in production, use proper security master
        position_lower = position.lower()
        
        if any(x in position_lower for x in ['spy', 'qqq', 'iwm', 'stock', 'equity']):
            return 'equity'
        elif any(x in position_lower for x in ['tlt', 'ief', 'agg', 'bond', 'treasury']):
            return 'bonds'
        elif any(x in position_lower for x in ['gld', 'slv', 'uso', 'commodity']):
            return 'commodities'
        elif any(x in position_lower for x in ['vnq', 'reit', 'real_estate']):
            return 'real_estate'
        else:
            return 'equity'  # Default to equity
    
    def _calculate_stressed_metrics(
        self,
        portfolio_positions: Dict[str, float],
        scenario: Dict,
        sensitivities: Dict[str, Dict[str, float]]
    ) -> Dict[str, float]:
        """Calculate risk metrics under stress scenario"""
        
        # Apply volatility multiplier
        vol_mult = scenario.get('volatility_multiplier', 1.0)
        corr_shock = scenario.get('correlation_shock', 0.0)
        
        metrics = {
            'stressed_volatility': vol_mult,
            'correlation_increase': corr_shock,
            'margin_requirement': min(1.0, vol_mult * 0.25),  # Simplified
            'liquidity_discount': min(0.5, vol_mult * 0.1)  # Simplified
        }
        
        return metrics
    
    def _estimate_recovery_time(
        self,
        drawdown: float,
        volatility_multiplier: float
    ) -> int:
        """Estimate recovery time in days"""
        # Simplified model: recovery time proportional to drawdown and volatility
        base_recovery = drawdown * 100  # Base days per percent drawdown
        adjusted_recovery = base_recovery * volatility_multiplier
        return int(adjusted_recovery)
    
    async def analyze_factor_risks(
        self,
        portfolio_positions: Dict[str, float],
        factor_exposures: Dict[str, Dict[str, float]],
        factor_covariance: np.ndarray
    ) -> List[FactorRisk]:
        """
        Analyze factor risk contributions
        
        Args:
            portfolio_positions: Portfolio positions
            factor_exposures: Factor exposures for each position
            factor_covariance: Factor covariance matrix
            
        Returns:
            List of factor risk decompositions
        """
        factor_risks = []
        
        # Calculate portfolio factor exposures
        portfolio_exposures = np.zeros(len(self.risk_factors))
        total_value = sum(portfolio_positions.values())
        
        for position, value in portfolio_positions.items():
            weight = value / total_value
            if position in factor_exposures:
                for i, factor in enumerate(self.risk_factors):
                    if factor in factor_exposures[position]:
                        portfolio_exposures[i] += weight * factor_exposures[position][factor]
        
        # Calculate factor contributions to portfolio variance
        portfolio_variance = portfolio_exposures @ factor_covariance @ portfolio_exposures.T
        
        for i, factor in enumerate(self.risk_factors):
            exposure = portfolio_exposures[i]
            
            # Marginal VaR: derivative of VaR with respect to factor exposure
            marginal_var = 2 * exposure * factor_covariance[i, i]
            
            # Component VaR: contribution of factor to total VaR
            component_var = exposure * marginal_var
            
            # Contribution to total variance
            contribution = (exposure ** 2 * factor_covariance[i, i]) / portfolio_variance
            
            factor_risks.append(FactorRisk(
                factor_name=factor,
                exposure=exposure,
                contribution_to_var=contribution,
                marginal_var=marginal_var,
                component_var=component_var,
                beta=exposure  # Simplified - factor exposure as beta
            ))
        
        return factor_risks
    
    def assess_liquidity_risk(
        self,
        portfolio_positions: Dict[str, float],
        market_data: Dict[str, Dict[str, float]]
    ) -> LiquidityRisk:
        """
        Assess portfolio liquidity risk
        
        Args:
            portfolio_positions: Portfolio positions
            market_data: Market data including volume, bid-ask spread
            
        Returns:
            Liquidity risk assessment
        """
        total_liquidation_cost = 0
        weighted_days_to_liquidate = 0
        total_market_impact = 0
        weighted_bid_ask = 0
        total_value = sum(portfolio_positions.values())
        
        for position, value in portfolio_positions.items():
            weight = value / total_value
            
            if position in market_data:
                data = market_data[position]
                
                # Bid-ask spread cost
                bid_ask_spread = data.get('bid_ask_spread', 0.001)  # Default 10 bps
                spread_cost = value * bid_ask_spread
                total_liquidation_cost += spread_cost
                weighted_bid_ask += weight * bid_ask_spread
                
                # Days to liquidate (assuming 20% of daily volume)
                daily_volume = data.get('avg_daily_volume', 1000000)
                volume_value = daily_volume * data.get('price', 100)
                days_to_liquidate = value / (0.2 * volume_value)
                weighted_days_to_liquidate += weight * days_to_liquidate
                
                # Market impact (simplified square-root model)
                market_impact = 0.1 * np.sqrt(value / volume_value)
                total_market_impact += value * market_impact
        
        # Calculate liquidity score (0-100, higher is better)
        liquidity_score = 100 / (1 + weighted_days_to_liquidate + weighted_bid_ask * 100)
        
        # Volume constraint (what % of daily volume can we trade)
        volume_constraint = 0.2  # 20% of daily volume
        
        return LiquidityRisk(
            liquidation_cost=total_liquidation_cost,
            days_to_liquidate=weighted_days_to_liquidate,
            market_impact=total_market_impact / total_value,
            bid_ask_spread=weighted_bid_ask,
            volume_constraint=volume_constraint,
            liquidity_score=liquidity_score
        )
    
    def calculate_r_multiples(
        self,
        trades: List[Dict],
        initial_risk_per_trade: float
    ) -> Dict[str, float]:
        """
        Calculate R-multiples for risk assessment
        
        Args:
            trades: List of trade dictionaries with entry, exit, stop_loss
            initial_risk_per_trade: Initial risk amount per trade (1R)
            
        Returns:
            R-multiple statistics
        """
        r_multiples = []
        
        for trade in trades:
            entry = trade['entry_price']
            exit = trade['exit_price']
            stop = trade['stop_loss']
            position_size = trade.get('position_size', 1)
            
            # Calculate risk (1R)
            risk = abs(entry - stop) * position_size
            
            # Calculate profit/loss
            pnl = (exit - entry) * position_size
            
            # Calculate R-multiple
            r_multiple = pnl / risk if risk > 0 else 0
            r_multiples.append(r_multiple)
        
        if not r_multiples:
            return {
                'average_r': 0,
                'win_rate': 0,
                'expectancy': 0,
                'max_r': 0,
                'min_r': 0,
                'std_r': 0
            }
        
        r_array = np.array(r_multiples)
        wins = r_array[r_array > 0]
        losses = r_array[r_array <= 0]
        
        win_rate = len(wins) / len(r_multiples)
        avg_win = wins.mean() if len(wins) > 0 else 0
        avg_loss = losses.mean() if len(losses) > 0 else 0
        
        # Calculate expectancy
        expectancy = (win_rate * avg_win) + ((1 - win_rate) * avg_loss)
        
        return {
            'average_r': r_array.mean(),
            'win_rate': win_rate,
            'expectancy': expectancy,
            'max_r': r_array.max(),
            'min_r': r_array.min(),
            'std_r': r_array.std(),
            'sharpe_r': expectancy / r_array.std() if r_array.std() > 0 else 0
        }
    
    def calculate_max_drawdown(
        self,
        equity_curve: np.ndarray
    ) -> Tuple[float, Optional[int]]:
        """
        Calculate maximum drawdown and recovery period
        
        Args:
            equity_curve: Array of portfolio values over time
            
        Returns:
            Tuple of (max_drawdown, recovery_period_days)
        """
        if len(equity_curve) < 2:
            return 0.0, None
        
        # Calculate running maximum
        running_max = np.maximum.accumulate(equity_curve)
        
        # Calculate drawdowns
        drawdowns = (equity_curve - running_max) / running_max
        
        # Find maximum drawdown
        max_dd = drawdowns.min()
        max_dd_idx = drawdowns.argmin()
        
        # Calculate recovery period
        recovery_period = None
        if max_dd_idx < len(equity_curve) - 1:
            recovery_value = running_max[max_dd_idx]
            future_values = equity_curve[max_dd_idx + 1:]
            
            # Find where equity recovers to previous high
            recovery_indices = np.where(future_values >= recovery_value)[0]
            if len(recovery_indices) > 0:
                recovery_period = recovery_indices[0] + 1
        
        return abs(max_dd), recovery_period
    
    def position_sizing_kelly(
        self,
        win_probability: float,
        win_loss_ratio: float,
        kelly_fraction: float = 0.25
    ) -> float:
        """
        Calculate position size using Kelly Criterion
        
        Args:
            win_probability: Probability of winning
            win_loss_ratio: Average win / average loss
            kelly_fraction: Fraction of Kelly to use (for safety)
            
        Returns:
            Recommended position size as fraction of capital
        """
        if win_loss_ratio <= 0:
            return 0.0
        
        # Kelly formula: f = (p * b - q) / b
        # where p = win probability, q = loss probability, b = win/loss ratio
        q = 1 - win_probability
        kelly = (win_probability * win_loss_ratio - q) / win_loss_ratio
        
        # Apply Kelly fraction for safety
        safe_kelly = kelly * kelly_fraction
        
        # Cap at maximum position size
        return min(max(safe_kelly, 0), 0.25)  # Max 25% of capital
    
    def calculate_risk_adjusted_metrics(
        self,
        returns: np.ndarray,
        risk_free_rate: float = 0.03
    ) -> Dict[str, float]:
        """
        Calculate risk-adjusted performance metrics
        
        Args:
            returns: Array of returns
            risk_free_rate: Annual risk-free rate
            
        Returns:
            Dictionary of risk-adjusted metrics
        """
        if len(returns) < 2:
            return {
                'sharpe_ratio': 0,
                'sortino_ratio': 0,
                'calmar_ratio': 0,
                'omega_ratio': 0,
                'tail_ratio': 0
            }
        
        # Annualization factor (assuming daily returns)
        annual_factor = np.sqrt(252)
        
        # Sharpe Ratio
        excess_returns = returns - risk_free_rate / 252
        sharpe = excess_returns.mean() / returns.std() * annual_factor
        
        # Sortino Ratio (downside deviation)
        downside_returns = returns[returns < 0]
        downside_std = downside_returns.std() if len(downside_returns) > 0 else returns.std()
        sortino = excess_returns.mean() / downside_std * annual_factor
        
        # Calmar Ratio (return / max drawdown)
        cumulative_returns = (1 + returns).cumprod()
        max_dd, _ = self.calculate_max_drawdown(cumulative_returns)
        annual_return = (cumulative_returns[-1] ** (252 / len(returns))) - 1
        calmar = annual_return / abs(max_dd) if max_dd != 0 else 0
        
        # Omega Ratio (probability weighted ratio of gains vs losses)
        threshold = risk_free_rate / 252
        gains = returns[returns > threshold] - threshold
        losses = threshold - returns[returns <= threshold]
        
        omega = gains.sum() / losses.sum() if losses.sum() > 0 else float('inf')
        
        # Tail Ratio (95th percentile gain / 5th percentile loss)
        tail_ratio = abs(np.percentile(returns, 95) / np.percentile(returns, 5))
        
        return {
            'sharpe_ratio': sharpe,
            'sortino_ratio': sortino,
            'calmar_ratio': calmar,
            'omega_ratio': omega,
            'tail_ratio': tail_ratio
        }
    
    async def generate_risk_report(
        self,
        portfolio_positions: Dict[str, float],
        market_data: Dict,
        historical_returns: np.ndarray,
        trades: List[Dict] = None
    ) -> RiskReport:
        """
        Generate comprehensive risk report
        
        Args:
            portfolio_positions: Current portfolio positions
            market_data: Market data for positions
            historical_returns: Historical returns data
            trades: Historical trades for R-multiple analysis
            
        Returns:
            Comprehensive risk report
        """
        portfolio_value = sum(portfolio_positions.values())
        
        # Calculate VaR suite
        var_results = await self.calculate_var_suite(
            historical_returns,
            portfolio_value,
            holding_period=1
        )
        
        # Run stress tests
        stress_tests = await self.run_stress_tests(
            portfolio_positions,
            {}  # Position sensitivities would come from market data
        )
        
        # Analyze factor risks (simplified)
        factor_risks = []  # Would require factor model data
        
        # Assess liquidity risk
        liquidity_risk = self.assess_liquidity_risk(
            portfolio_positions,
            market_data
        )
        
        # Calculate correlation matrix (simplified)
        correlation_matrix = np.corrcoef(historical_returns.reshape(-1, 1).T)
        
        # Calculate R-multiples if trades provided
        r_multiples = {}
        expectancy = 0
        if trades:
            r_multiples = self.calculate_r_multiples(trades, portfolio_value * 0.01)
            expectancy = r_multiples.get('expectancy', 0)
        
        # Calculate max drawdown
        equity_curve = np.cumprod(1 + historical_returns) * portfolio_value
        max_drawdown, recovery_period = self.calculate_max_drawdown(equity_curve)
        
        # Calculate overall risk score
        risk_score = self._calculate_overall_risk_score(
            var_results,
            stress_tests,
            liquidity_risk,
            max_drawdown
        )
        
        # Determine risk level
        risk_level = self._determine_risk_level(risk_score)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            risk_score,
            var_results,
            stress_tests,
            liquidity_risk
        )
        
        return RiskReport(
            timestamp=datetime.now(),
            var_results=var_results,
            stress_tests=stress_tests,
            factor_risks=factor_risks,
            liquidity_risk=liquidity_risk,
            correlation_matrix=correlation_matrix,
            risk_score=risk_score,
            risk_level=risk_level,
            recommendations=recommendations,
            r_multiples=r_multiples,
            expectancy=expectancy,
            max_drawdown=max_drawdown,
            recovery_period=recovery_period
        )
    
    def _calculate_overall_risk_score(
        self,
        var_results: Dict[str, VaRResult],
        stress_tests: List[StressTestResult],
        liquidity_risk: LiquidityRisk,
        max_drawdown: float
    ) -> float:
        """Calculate overall risk score (0-100, higher is riskier)"""
        
        # VaR component (average across methods)
        var_scores = []
        for method, result in var_results.items():
            # Normalize VaR as percentage of portfolio
            var_score = min(100, result.var_99 * 100)  # Assuming VaR as percentage
            var_scores.append(var_score)
        
        var_component = np.mean(var_scores) * 0.3
        
        # Stress test component
        stress_impacts = [abs(st.portfolio_impact) for st in stress_tests]
        stress_component = min(100, np.mean(stress_impacts) * 100) * 0.3
        
        # Liquidity component (inverse of liquidity score)
        liquidity_component = (100 - liquidity_risk.liquidity_score) * 0.2
        
        # Drawdown component
        drawdown_component = min(100, abs(max_drawdown) * 100) * 0.2
        
        # Calculate total score
        total_score = (
            var_component +
            stress_component +
            liquidity_component +
            drawdown_component
        )
        
        return min(100, total_score)
    
    def _determine_risk_level(self, risk_score: float) -> RiskLevel:
        """Determine risk level based on score"""
        if risk_score < 20:
            return RiskLevel.MINIMAL
        elif risk_score < 40:
            return RiskLevel.LOW
        elif risk_score < 60:
            return RiskLevel.MODERATE
        elif risk_score < 80:
            return RiskLevel.HIGH
        else:
            return RiskLevel.CRITICAL
    
    def _generate_recommendations(
        self,
        risk_score: float,
        var_results: Dict[str, VaRResult],
        stress_tests: List[StressTestResult],
        liquidity_risk: LiquidityRisk
    ) -> List[str]:
        """Generate risk management recommendations"""
        recommendations = []
        
        # Based on risk score
        if risk_score > 70:
            recommendations.append("URGENT: Portfolio risk is critically high. Consider immediate risk reduction.")
            recommendations.append("Reduce position sizes by 30-50% to lower overall exposure.")
        elif risk_score > 50:
            recommendations.append("Portfolio risk is elevated. Review and adjust positions.")
            recommendations.append("Consider hedging strategies to protect against downside.")
        
        # Based on VaR
        avg_var = np.mean([r.var_95 for r in var_results.values()])
        if avg_var > 0.05:  # More than 5% VaR
            recommendations.append(f"Value at Risk exceeds 5%. Consider diversification.")
            recommendations.append("Add defensive assets or protective puts.")
        
        # Based on stress tests
        worst_stress = min(stress_tests, key=lambda x: x.portfolio_impact)
        if abs(worst_stress.portfolio_impact) > 0.25:
            recommendations.append(f"Portfolio vulnerable to {worst_stress.scenario_name}.")
            recommendations.append("Implement tail risk hedging strategies.")
        
        # Based on liquidity
        if liquidity_risk.liquidity_score < 50:
            recommendations.append("Liquidity risk is high. Increase allocation to liquid assets.")
            recommendations.append(f"Current liquidation would take {liquidity_risk.days_to_liquidate:.1f} days.")
        
        # Position sizing recommendations
        recommendations.append("Use position sizing rules: Risk no more than 2% per trade.")
        recommendations.append("Apply Kelly Criterion with safety factor of 0.25.")
        
        # Correlation recommendations
        recommendations.append("Monitor correlation changes during market stress.")
        recommendations.append("Maintain uncorrelated asset classes for true diversification.")
        
        return recommendations


if __name__ == "__main__":
    # Example usage and testing
    async def test_risk_models():
        # Initialize engine
        risk_engine = RiskModelsEngine()
        
        # Generate sample data
        np.random.seed(42)
        returns = np.random.normal(0.001, 0.02, 252)  # Daily returns
        
        portfolio = {
            'SPY': 100000,
            'AGG': 50000,
            'GLD': 25000,
            'VNQ': 25000
        }
        
        market_data = {
            'SPY': {'bid_ask_spread': 0.0001, 'avg_daily_volume': 50000000, 'price': 450},
            'AGG': {'bid_ask_spread': 0.0002, 'avg_daily_volume': 10000000, 'price': 110},
            'GLD': {'bid_ask_spread': 0.0003, 'avg_daily_volume': 5000000, 'price': 180},
            'VNQ': {'bid_ask_spread': 0.0004, 'avg_daily_volume': 3000000, 'price': 90}
        }
        
        # Generate risk report
        report = await risk_engine.generate_risk_report(
            portfolio,
            market_data,
            returns
        )
        
        print(f"Risk Score: {report.risk_score:.2f}")
        print(f"Risk Level: {report.risk_level.value}")
        print(f"Max Drawdown: {report.max_drawdown:.2%}")
        print("\nRecommendations:")
        for rec in report.recommendations:
            print(f"- {rec}")
    
    # Run test
    # asyncio.run(test_risk_models())