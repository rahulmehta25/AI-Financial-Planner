"""
Comprehensive Risk Management Engine

This module implements institutional-grade risk management with:
- Value at Risk (VaR) and Conditional VaR (CVaR) calculations
- Comprehensive stress testing scenarios
- Factor risk analysis and decomposition
- Liquidity and concentration risk assessment
- Real-time risk monitoring with alerts
- Position sizing using Kelly Criterion
- R-multiple tracking and expectancy calculations
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
from scipy import stats, optimize
from scipy.stats import norm, t as t_dist
import asyncio
import json
from collections import defaultdict
import warnings
warnings.filterwarnings('ignore')

# Try to import advanced libraries
try:
    from sklearn.decomposition import PCA
    from sklearn.preprocessing import StandardScaler
    from sklearn.ensemble import IsolationForest
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

logger = logging.getLogger(__name__)


class RiskMetricType(Enum):
    """Types of risk metrics"""
    VAR_HISTORICAL = "var_historical"
    VAR_PARAMETRIC = "var_parametric"
    VAR_MONTE_CARLO = "var_monte_carlo"
    CVAR = "cvar"
    MAX_DRAWDOWN = "max_drawdown"
    SHARPE_RATIO = "sharpe_ratio"
    SORTINO_RATIO = "sortino_ratio"
    CALMAR_RATIO = "calmar_ratio"
    INFORMATION_RATIO = "information_ratio"
    TREYNOR_RATIO = "treynor_ratio"
    BETA = "beta"
    CORRELATION = "correlation"
    TRACKING_ERROR = "tracking_error"


class StressScenario(Enum):
    """Pre-defined stress test scenarios"""
    FINANCIAL_CRISIS_2008 = "financial_crisis_2008"
    COVID_PANDEMIC_2020 = "covid_pandemic_2020"
    DOT_COM_CRASH_2000 = "dot_com_crash_2000"
    BLACK_MONDAY_1987 = "black_monday_1987"
    BREXIT_2016 = "brexit_2016"
    FLASH_CRASH_2010 = "flash_crash_2010"
    TAPER_TANTRUM_2013 = "taper_tantrum_2013"
    CHINA_DEVALUATION_2015 = "china_devaluation_2015"
    CUSTOM = "custom"


@dataclass
class PortfolioPosition:
    """Individual portfolio position"""
    symbol: str
    quantity: float
    current_price: float
    cost_basis: float
    asset_class: str  # equity, bond, commodity, crypto, etc.
    sector: str = "Unknown"
    market_cap: str = "Large"  # Large, Mid, Small, Micro
    liquidity_score: float = 1.0  # 0-1, higher is more liquid
    beta: float = 1.0
    volatility: float = 0.15  # Annual volatility
    correlation_matrix_index: Optional[int] = None


@dataclass
class RiskLimits:
    """Risk limits and thresholds"""
    max_var_95: float = 0.05  # 5% VaR limit
    max_var_99: float = 0.10  # 10% VaR limit
    max_position_size: float = 0.10  # 10% max position
    max_sector_exposure: float = 0.25  # 25% max sector
    max_leverage: float = 2.0  # 2:1 leverage
    max_drawdown: float = 0.20  # 20% max drawdown
    min_sharpe_ratio: float = 0.5
    max_correlation: float = 0.8
    min_liquidity_ratio: float = 0.3  # 30% in liquid assets
    stop_loss_percentage: float = 0.08  # 8% stop loss
    risk_per_trade: float = 0.02  # 2% risk per trade (1R)


@dataclass
class RiskMetrics:
    """Comprehensive risk metrics output"""
    var_95_historical: float
    var_99_historical: float
    var_95_parametric: float
    var_99_parametric: float
    var_95_monte_carlo: float
    var_99_monte_carlo: float
    cvar_95: float
    cvar_99: float
    max_drawdown: float
    current_drawdown: float
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    information_ratio: float
    portfolio_beta: float
    portfolio_volatility: float
    tracking_error: float
    concentration_risk: float
    liquidity_risk: float
    factor_exposures: Dict[str, float]
    correlation_risk: float
    tail_risk: float
    stress_test_results: Dict[str, float]
    risk_adjusted_return: float
    kelly_fraction: float
    expectancy: float
    r_multiples: List[float]


@dataclass
class StressTestResult:
    """Stress test scenario result"""
    scenario: StressScenario
    portfolio_impact: float
    var_impact: float
    worst_position: str
    worst_position_impact: float
    recovery_time_estimate: int  # days
    probability_estimate: float
    recommendations: List[str]


@dataclass
class TradeAnalysis:
    """Trade analysis using R-multiples"""
    entry_price: float
    stop_loss: float
    take_profit: Optional[float]
    position_size: float
    risk_amount: float  # 1R in dollar terms
    r_multiple: float  # Result in R terms
    expectancy_contribution: float
    win_rate_impact: float


class RiskManagementEngine:
    """
    Comprehensive risk management engine for portfolio protection
    """
    
    def __init__(self, risk_limits: Optional[RiskLimits] = None):
        """Initialize risk management engine"""
        self.risk_limits = risk_limits or RiskLimits()
        self.positions: List[PortfolioPosition] = []
        self.historical_returns: Optional[pd.DataFrame] = None
        self.correlation_matrix: Optional[np.ndarray] = None
        self.factor_model = None
        self.stress_scenarios = self._initialize_stress_scenarios()
        self.trade_history: List[TradeAnalysis] = []
        self.alerts: List[Dict] = []
        
    def _initialize_stress_scenarios(self) -> Dict[StressScenario, Dict]:
        """Initialize historical stress test scenarios"""
        return {
            StressScenario.FINANCIAL_CRISIS_2008: {
                'equity_shock': -0.55,
                'bond_shock': 0.05,
                'commodity_shock': -0.70,
                'crypto_shock': -0.80,
                'volatility_multiplier': 3.5,
                'correlation_increase': 0.3,
                'duration': 180,
                'probability': 0.02
            },
            StressScenario.COVID_PANDEMIC_2020: {
                'equity_shock': -0.35,
                'bond_shock': 0.08,
                'commodity_shock': -0.50,
                'crypto_shock': -0.50,
                'volatility_multiplier': 4.0,
                'correlation_increase': 0.4,
                'duration': 30,
                'probability': 0.01
            },
            StressScenario.DOT_COM_CRASH_2000: {
                'equity_shock': -0.49,
                'bond_shock': 0.10,
                'commodity_shock': -0.20,
                'crypto_shock': -0.90,
                'volatility_multiplier': 2.5,
                'correlation_increase': 0.2,
                'duration': 365,
                'probability': 0.03
            },
            StressScenario.BLACK_MONDAY_1987: {
                'equity_shock': -0.22,
                'bond_shock': 0.02,
                'commodity_shock': -0.15,
                'crypto_shock': -0.40,
                'volatility_multiplier': 5.0,
                'correlation_increase': 0.5,
                'duration': 1,
                'probability': 0.001
            },
            StressScenario.FLASH_CRASH_2010: {
                'equity_shock': -0.09,
                'bond_shock': 0.01,
                'commodity_shock': -0.05,
                'crypto_shock': -0.15,
                'volatility_multiplier': 8.0,
                'correlation_increase': 0.6,
                'duration': 1,
                'probability': 0.005
            },
            StressScenario.BREXIT_2016: {
                'equity_shock': -0.08,
                'bond_shock': 0.03,
                'commodity_shock': -0.10,
                'crypto_shock': -0.12,
                'volatility_multiplier': 2.0,
                'correlation_increase': 0.15,
                'duration': 5,
                'probability': 0.05
            },
            StressScenario.TAPER_TANTRUM_2013: {
                'equity_shock': -0.06,
                'bond_shock': -0.08,
                'commodity_shock': -0.10,
                'crypto_shock': -0.20,
                'volatility_multiplier': 1.8,
                'correlation_increase': 0.1,
                'duration': 30,
                'probability': 0.10
            },
            StressScenario.CHINA_DEVALUATION_2015: {
                'equity_shock': -0.12,
                'bond_shock': 0.02,
                'commodity_shock': -0.25,
                'crypto_shock': -0.30,
                'volatility_multiplier': 2.2,
                'correlation_increase': 0.25,
                'duration': 10,
                'probability': 0.08
            }
        }
    
    async def calculate_comprehensive_risk_metrics(
        self,
        positions: List[PortfolioPosition],
        historical_returns: pd.DataFrame,
        benchmark_returns: Optional[pd.Series] = None,
        confidence_levels: List[float] = [0.95, 0.99]
    ) -> RiskMetrics:
        """
        Calculate comprehensive risk metrics for portfolio
        
        Args:
            positions: List of portfolio positions
            historical_returns: Historical returns data
            benchmark_returns: Benchmark returns for relative metrics
            confidence_levels: Confidence levels for VaR/CVaR
            
        Returns:
            Comprehensive risk metrics
        """
        self.positions = positions
        self.historical_returns = historical_returns
        
        # Calculate portfolio returns
        portfolio_returns = self._calculate_portfolio_returns(positions, historical_returns)
        
        # Calculate VaR metrics
        var_metrics = await self._calculate_var_metrics(
            portfolio_returns, confidence_levels
        )
        
        # Calculate CVaR metrics
        cvar_metrics = self._calculate_cvar(portfolio_returns, confidence_levels)
        
        # Calculate drawdown metrics
        drawdown_metrics = self._calculate_drawdown_metrics(portfolio_returns)
        
        # Calculate risk-adjusted returns
        risk_adjusted = self._calculate_risk_adjusted_returns(
            portfolio_returns, benchmark_returns
        )
        
        # Calculate factor exposures
        factor_exposures = await self._calculate_factor_exposures(
            positions, historical_returns
        )
        
        # Calculate concentration and liquidity risk
        concentration_risk = self._calculate_concentration_risk(positions)
        liquidity_risk = self._calculate_liquidity_risk(positions)
        
        # Calculate correlation risk
        correlation_risk = self._calculate_correlation_risk(historical_returns)
        
        # Calculate tail risk
        tail_risk = self._calculate_tail_risk(portfolio_returns)
        
        # Run stress tests
        stress_results = await self._run_stress_tests(positions)
        
        # Calculate Kelly fraction for position sizing
        kelly_fraction = self._calculate_kelly_fraction(portfolio_returns)
        
        # Calculate expectancy from trade history
        expectancy = self._calculate_expectancy()
        
        # Get R-multiples from trade history
        r_multiples = [trade.r_multiple for trade in self.trade_history]
        
        return RiskMetrics(
            var_95_historical=var_metrics['historical'][0.95],
            var_99_historical=var_metrics['historical'][0.99],
            var_95_parametric=var_metrics['parametric'][0.95],
            var_99_parametric=var_metrics['parametric'][0.99],
            var_95_monte_carlo=var_metrics['monte_carlo'][0.95],
            var_99_monte_carlo=var_metrics['monte_carlo'][0.99],
            cvar_95=cvar_metrics[0.95],
            cvar_99=cvar_metrics[0.99],
            max_drawdown=drawdown_metrics['max_drawdown'],
            current_drawdown=drawdown_metrics['current_drawdown'],
            sharpe_ratio=risk_adjusted['sharpe_ratio'],
            sortino_ratio=risk_adjusted['sortino_ratio'],
            calmar_ratio=risk_adjusted['calmar_ratio'],
            information_ratio=risk_adjusted['information_ratio'],
            portfolio_beta=risk_adjusted['beta'],
            portfolio_volatility=np.std(portfolio_returns) * np.sqrt(252),
            tracking_error=risk_adjusted['tracking_error'],
            concentration_risk=concentration_risk,
            liquidity_risk=liquidity_risk,
            factor_exposures=factor_exposures,
            correlation_risk=correlation_risk,
            tail_risk=tail_risk,
            stress_test_results=stress_results,
            risk_adjusted_return=risk_adjusted['risk_adjusted_return'],
            kelly_fraction=kelly_fraction,
            expectancy=expectancy,
            r_multiples=r_multiples
        )
    
    def _calculate_portfolio_returns(
        self,
        positions: List[PortfolioPosition],
        historical_returns: pd.DataFrame
    ) -> pd.Series:
        """Calculate portfolio returns from positions"""
        
        # Calculate portfolio weights
        total_value = sum(p.quantity * p.current_price for p in positions)
        weights = {}
        
        for position in positions:
            weight = (position.quantity * position.current_price) / total_value
            weights[position.symbol] = weight
        
        # Calculate weighted returns
        portfolio_returns = pd.Series(index=historical_returns.index, dtype=float)
        portfolio_returns[:] = 0
        
        for symbol, weight in weights.items():
            if symbol in historical_returns.columns:
                portfolio_returns += weight * historical_returns[symbol]
        
        return portfolio_returns
    
    async def _calculate_var_metrics(
        self,
        returns: pd.Series,
        confidence_levels: List[float]
    ) -> Dict[str, Dict[float, float]]:
        """Calculate VaR using multiple methods"""
        
        var_results = {
            'historical': {},
            'parametric': {},
            'monte_carlo': {}
        }
        
        for confidence in confidence_levels:
            # Historical VaR
            var_results['historical'][confidence] = self._calculate_historical_var(
                returns, confidence
            )
            
            # Parametric VaR
            var_results['parametric'][confidence] = self._calculate_parametric_var(
                returns, confidence
            )
            
            # Monte Carlo VaR
            var_results['monte_carlo'][confidence] = await self._calculate_monte_carlo_var(
                returns, confidence
            )
        
        return var_results
    
    def _calculate_historical_var(self, returns: pd.Series, confidence: float) -> float:
        """Calculate historical VaR"""
        return -np.percentile(returns, (1 - confidence) * 100)
    
    def _calculate_parametric_var(self, returns: pd.Series, confidence: float) -> float:
        """Calculate parametric VaR assuming normal distribution"""
        mean = returns.mean()
        std = returns.std()
        
        # Use Cornish-Fisher expansion for non-normal distributions
        skew = returns.skew()
        kurt = returns.kurtosis()
        
        z_score = norm.ppf(confidence)
        
        # Cornish-Fisher adjustment
        cf_z = (z_score + 
                (z_score**2 - 1) * skew / 6 +
                (z_score**3 - 3*z_score) * kurt / 24 -
                (2*z_score**3 - 5*z_score) * skew**2 / 36)
        
        var = -(mean + cf_z * std)
        return var
    
    async def _calculate_monte_carlo_var(
        self,
        returns: pd.Series,
        confidence: float,
        n_simulations: int = 10000
    ) -> float:
        """Calculate Monte Carlo VaR"""
        
        mean = returns.mean()
        std = returns.std()
        
        # Fit t-distribution for heavy tails
        params = t_dist.fit(returns)
        df, loc, scale = params
        
        # Run simulations
        simulated_returns = t_dist.rvs(df, loc=loc, scale=scale, size=n_simulations)
        
        # Calculate VaR
        var = -np.percentile(simulated_returns, (1 - confidence) * 100)
        return var
    
    def _calculate_cvar(
        self,
        returns: pd.Series,
        confidence_levels: List[float]
    ) -> Dict[float, float]:
        """Calculate Conditional VaR (Expected Shortfall)"""
        
        cvar_results = {}
        
        for confidence in confidence_levels:
            var = self._calculate_historical_var(returns, confidence)
            # CVaR is the expected loss beyond VaR
            losses_beyond_var = returns[returns <= -var]
            if len(losses_beyond_var) > 0:
                cvar_results[confidence] = -losses_beyond_var.mean()
            else:
                cvar_results[confidence] = var
        
        return cvar_results
    
    def _calculate_drawdown_metrics(self, returns: pd.Series) -> Dict[str, float]:
        """Calculate drawdown metrics"""
        
        # Calculate cumulative returns
        cum_returns = (1 + returns).cumprod()
        
        # Calculate running maximum
        running_max = cum_returns.expanding().max()
        
        # Calculate drawdown series
        drawdown = (cum_returns - running_max) / running_max
        
        return {
            'max_drawdown': drawdown.min(),
            'current_drawdown': drawdown.iloc[-1],
            'max_drawdown_duration': self._calculate_max_drawdown_duration(drawdown),
            'recovery_time': self._estimate_recovery_time(drawdown)
        }
    
    def _calculate_max_drawdown_duration(self, drawdown: pd.Series) -> int:
        """Calculate maximum drawdown duration in days"""
        
        in_drawdown = drawdown < 0
        drawdown_periods = []
        current_period = 0
        
        for is_dd in in_drawdown:
            if is_dd:
                current_period += 1
            else:
                if current_period > 0:
                    drawdown_periods.append(current_period)
                current_period = 0
        
        if current_period > 0:
            drawdown_periods.append(current_period)
        
        return max(drawdown_periods) if drawdown_periods else 0
    
    def _estimate_recovery_time(self, drawdown: pd.Series) -> int:
        """Estimate recovery time from current drawdown"""
        
        current_dd = drawdown.iloc[-1]
        if current_dd >= 0:
            return 0
        
        # Historical recovery analysis
        historical_recoveries = []
        in_drawdown = False
        dd_start = 0
        
        for i, dd in enumerate(drawdown):
            if dd < 0 and not in_drawdown:
                in_drawdown = True
                dd_start = i
            elif dd >= 0 and in_drawdown:
                in_drawdown = False
                historical_recoveries.append(i - dd_start)
        
        if historical_recoveries:
            # Use median recovery time scaled by current drawdown depth
            median_recovery = np.median(historical_recoveries)
            depth_factor = abs(current_dd) / 0.1  # Normalize to 10% drawdown
            return int(median_recovery * depth_factor)
        
        return 30  # Default estimate
    
    def _calculate_risk_adjusted_returns(
        self,
        returns: pd.Series,
        benchmark_returns: Optional[pd.Series] = None
    ) -> Dict[str, float]:
        """Calculate risk-adjusted return metrics"""
        
        annual_return = returns.mean() * 252
        annual_vol = returns.std() * np.sqrt(252)
        risk_free_rate = 0.02  # Assume 2% risk-free rate
        
        # Sharpe Ratio
        sharpe_ratio = (annual_return - risk_free_rate) / annual_vol if annual_vol > 0 else 0
        
        # Sortino Ratio
        downside_returns = returns[returns < 0]
        downside_vol = downside_returns.std() * np.sqrt(252) if len(downside_returns) > 0 else annual_vol
        sortino_ratio = (annual_return - risk_free_rate) / downside_vol if downside_vol > 0 else 0
        
        # Calmar Ratio
        max_dd = self._calculate_drawdown_metrics(returns)['max_drawdown']
        calmar_ratio = annual_return / abs(max_dd) if max_dd != 0 else 0
        
        # Information Ratio and Beta (if benchmark provided)
        information_ratio = 0
        beta = 1.0
        tracking_error = 0
        
        if benchmark_returns is not None:
            # Align series
            aligned = pd.DataFrame({
                'portfolio': returns,
                'benchmark': benchmark_returns
            }).dropna()
            
            if len(aligned) > 0:
                excess_returns = aligned['portfolio'] - aligned['benchmark']
                tracking_error = excess_returns.std() * np.sqrt(252)
                information_ratio = (excess_returns.mean() * 252) / tracking_error if tracking_error > 0 else 0
                
                # Calculate beta
                covariance = aligned['portfolio'].cov(aligned['benchmark'])
                benchmark_variance = aligned['benchmark'].var()
                beta = covariance / benchmark_variance if benchmark_variance > 0 else 1.0
        
        return {
            'sharpe_ratio': sharpe_ratio,
            'sortino_ratio': sortino_ratio,
            'calmar_ratio': calmar_ratio,
            'information_ratio': information_ratio,
            'beta': beta,
            'tracking_error': tracking_error,
            'risk_adjusted_return': annual_return / beta if beta != 0 else annual_return
        }
    
    async def _calculate_factor_exposures(
        self,
        positions: List[PortfolioPosition],
        historical_returns: pd.DataFrame
    ) -> Dict[str, float]:
        """Calculate factor exposures using PCA or predefined factors"""
        
        exposures = {}
        
        # Asset class exposures
        asset_class_weights = defaultdict(float)
        sector_weights = defaultdict(float)
        market_cap_weights = defaultdict(float)
        
        total_value = sum(p.quantity * p.current_price for p in positions)
        
        for position in positions:
            weight = (position.quantity * position.current_price) / total_value
            asset_class_weights[position.asset_class] += weight
            sector_weights[position.sector] += weight
            market_cap_weights[position.market_cap] += weight
        
        exposures.update({
            f'asset_class_{k}': v for k, v in asset_class_weights.items()
        })
        exposures.update({
            f'sector_{k}': v for k, v in sector_weights.items()
        })
        exposures.update({
            f'market_cap_{k}': v for k, v in market_cap_weights.items()
        })
        
        # Statistical factor analysis if sklearn available
        if SKLEARN_AVAILABLE and len(historical_returns.columns) > 3:
            try:
                # Standardize returns
                scaler = StandardScaler()
                standardized = scaler.fit_transform(historical_returns.dropna())
                
                # PCA for factor extraction
                pca = PCA(n_components=min(5, len(historical_returns.columns)))
                factors = pca.fit_transform(standardized)
                
                # Calculate portfolio exposure to each factor
                portfolio_returns = self._calculate_portfolio_returns(positions, historical_returns)
                portfolio_standardized = scaler.transform(portfolio_returns.values.reshape(-1, 1))
                
                for i, variance_explained in enumerate(pca.explained_variance_ratio_):
                    exposures[f'factor_{i+1}'] = variance_explained
                
            except Exception as e:
                logger.warning(f"Factor analysis failed: {e}")
        
        return exposures
    
    def _calculate_concentration_risk(self, positions: List[PortfolioPosition]) -> float:
        """Calculate concentration risk using Herfindahl-Hirschman Index"""
        
        total_value = sum(p.quantity * p.current_price for p in positions)
        weights = []
        
        for position in positions:
            weight = (position.quantity * position.current_price) / total_value
            weights.append(weight)
        
        # Herfindahl-Hirschman Index
        hhi = sum(w**2 for w in weights)
        
        # Normalize to 0-1 scale (1 = maximum concentration)
        n_positions = len(positions)
        min_hhi = 1 / n_positions if n_positions > 0 else 1
        max_hhi = 1
        
        normalized_hhi = (hhi - min_hhi) / (max_hhi - min_hhi) if max_hhi > min_hhi else 0
        
        return normalized_hhi
    
    def _calculate_liquidity_risk(self, positions: List[PortfolioPosition]) -> float:
        """Calculate portfolio liquidity risk"""
        
        total_value = sum(p.quantity * p.current_price for p in positions)
        weighted_liquidity = 0
        
        for position in positions:
            weight = (position.quantity * position.current_price) / total_value
            # Inverse liquidity score (higher score = higher risk)
            liquidity_risk_contribution = weight * (1 - position.liquidity_score)
            weighted_liquidity += liquidity_risk_contribution
        
        return weighted_liquidity
    
    def _calculate_correlation_risk(self, historical_returns: pd.DataFrame) -> float:
        """Calculate correlation risk in portfolio"""
        
        if len(historical_returns.columns) < 2:
            return 0
        
        # Calculate correlation matrix
        corr_matrix = historical_returns.corr()
        
        # Extract upper triangle (excluding diagonal)
        upper_triangle = np.triu(corr_matrix.values, k=1)
        correlations = upper_triangle[upper_triangle != 0]
        
        if len(correlations) == 0:
            return 0
        
        # Average absolute correlation
        avg_correlation = np.mean(np.abs(correlations))
        
        # High correlation risk if average > 0.6
        correlation_risk = min(avg_correlation / 0.6, 1.0)
        
        return correlation_risk
    
    def _calculate_tail_risk(self, returns: pd.Series) -> float:
        """Calculate tail risk using tail ratio and kurtosis"""
        
        # Calculate percentiles
        percentile_95 = np.percentile(returns, 95)
        percentile_5 = np.percentile(returns, 5)
        
        # Tail ratio (right tail / left tail)
        tail_ratio = abs(percentile_95 / percentile_5) if percentile_5 != 0 else 1
        
        # Excess kurtosis (fat tails)
        excess_kurtosis = returns.kurtosis()
        
        # Combine metrics
        # Higher tail ratio = more asymmetric risk
        # Higher kurtosis = fatter tails
        tail_risk_score = (1 / tail_ratio if tail_ratio > 0 else 1) * (1 + abs(excess_kurtosis) / 3)
        
        return min(tail_risk_score, 1.0)
    
    async def _run_stress_tests(
        self,
        positions: List[PortfolioPosition]
    ) -> Dict[str, float]:
        """Run comprehensive stress tests"""
        
        results = {}
        
        for scenario, params in self.stress_scenarios.items():
            impact = await self._run_single_stress_test(positions, params)
            results[scenario.value] = impact
        
        return results
    
    async def _run_single_stress_test(
        self,
        positions: List[PortfolioPosition],
        scenario_params: Dict
    ) -> float:
        """Run a single stress test scenario"""
        
        total_value = sum(p.quantity * p.current_price for p in positions)
        stressed_value = 0
        
        for position in positions:
            # Get asset class shock
            shock_key = f'{position.asset_class}_shock'
            shock = scenario_params.get(shock_key, -0.10)  # Default 10% shock
            
            # Apply volatility adjustment
            vol_mult = scenario_params.get('volatility_multiplier', 1.0)
            adjusted_shock = shock * (1 + (vol_mult - 1) * position.volatility)
            
            # Calculate stressed position value
            stressed_price = position.current_price * (1 + adjusted_shock)
            stressed_position_value = position.quantity * stressed_price
            stressed_value += stressed_position_value
        
        # Calculate portfolio impact
        portfolio_impact = (stressed_value - total_value) / total_value
        
        return portfolio_impact
    
    def _calculate_kelly_fraction(self, returns: pd.Series) -> float:
        """Calculate Kelly Criterion for optimal position sizing"""
        
        if len(returns) < 30:
            return 0.25  # Default conservative fraction
        
        # Calculate win rate and average win/loss
        winning_returns = returns[returns > 0]
        losing_returns = returns[returns < 0]
        
        if len(winning_returns) == 0 or len(losing_returns) == 0:
            return 0.25
        
        win_rate = len(winning_returns) / len(returns)
        avg_win = winning_returns.mean()
        avg_loss = abs(losing_returns.mean())
        
        # Kelly formula: f = (p*b - q) / b
        # where p = win rate, q = loss rate, b = win/loss ratio
        b = avg_win / avg_loss if avg_loss > 0 else 1
        q = 1 - win_rate
        
        kelly = (win_rate * b - q) / b if b > 0 else 0
        
        # Apply Kelly fraction cap (typically 25% max)
        kelly_capped = min(max(kelly, 0), 0.25)
        
        return kelly_capped
    
    def _calculate_expectancy(self) -> float:
        """Calculate trading expectancy from trade history"""
        
        if not self.trade_history:
            return 0
        
        total_r = sum(trade.r_multiple for trade in self.trade_history)
        n_trades = len(self.trade_history)
        
        # Expectancy = Average R-multiple
        expectancy = total_r / n_trades if n_trades > 0 else 0
        
        return expectancy
    
    def calculate_position_size(
        self,
        account_value: float,
        entry_price: float,
        stop_loss: float,
        risk_per_trade: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Calculate optimal position size using risk management rules
        
        Args:
            account_value: Total account value
            entry_price: Entry price for position
            stop_loss: Stop loss price
            risk_per_trade: Risk per trade (default from risk limits)
            
        Returns:
            Position sizing details
        """
        
        risk_per_trade = risk_per_trade or self.risk_limits.risk_per_trade
        
        # Calculate risk amount (1R)
        risk_amount = account_value * risk_per_trade
        
        # Calculate price risk per share
        price_risk = abs(entry_price - stop_loss)
        
        if price_risk == 0:
            return {
                'position_size': 0,
                'risk_amount': 0,
                'message': 'Invalid stop loss (same as entry price)'
            }
        
        # Calculate position size
        position_size = risk_amount / price_risk
        
        # Apply Kelly Criterion if available
        if self.historical_returns is not None:
            kelly_fraction = self._calculate_kelly_fraction(
                self.historical_returns.iloc[:, 0] if len(self.historical_returns.columns) > 0 
                else pd.Series()
            )
            kelly_adjusted_size = position_size * (kelly_fraction / risk_per_trade)
            position_size = min(position_size, kelly_adjusted_size)
        
        # Calculate position value
        position_value = position_size * entry_price
        
        # Check position limits
        max_position_value = account_value * self.risk_limits.max_position_size
        
        if position_value > max_position_value:
            # Adjust position size to stay within limits
            position_size = max_position_value / entry_price
            actual_risk = position_size * price_risk
            actual_risk_pct = actual_risk / account_value
        else:
            actual_risk = risk_amount
            actual_risk_pct = risk_per_trade
        
        return {
            'position_size': int(position_size),
            'position_value': position_size * entry_price,
            'risk_amount': actual_risk,
            'risk_percentage': actual_risk_pct,
            'price_risk': price_risk,
            'r_multiple_per_share': price_risk,
            'kelly_fraction': kelly_fraction if self.historical_returns is not None else None,
            'max_position_value': max_position_value
        }
    
    def add_trade_result(
        self,
        entry_price: float,
        exit_price: float,
        stop_loss: float,
        position_size: float
    ) -> TradeAnalysis:
        """
        Add trade result for expectancy calculation
        
        Args:
            entry_price: Entry price
            exit_price: Exit price
            stop_loss: Stop loss price
            position_size: Position size
            
        Returns:
            Trade analysis with R-multiple
        """
        
        # Calculate risk (1R)
        price_risk = abs(entry_price - stop_loss)
        risk_amount = position_size * price_risk
        
        # Calculate P&L
        pnl = position_size * (exit_price - entry_price)
        
        # Calculate R-multiple
        r_multiple = pnl / risk_amount if risk_amount > 0 else 0
        
        # Update win rate
        wins = [t for t in self.trade_history if t.r_multiple > 0]
        win_rate = len(wins) / len(self.trade_history) if self.trade_history else 0
        new_win_rate_impact = 1 / (len(self.trade_history) + 1) if r_multiple > 0 else 0
        
        # Calculate expectancy contribution
        expectancy_contribution = r_multiple / (len(self.trade_history) + 1)
        
        trade = TradeAnalysis(
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit=None,
            position_size=position_size,
            risk_amount=risk_amount,
            r_multiple=r_multiple,
            expectancy_contribution=expectancy_contribution,
            win_rate_impact=new_win_rate_impact
        )
        
        self.trade_history.append(trade)
        
        return trade
    
    def generate_risk_report(self, metrics: RiskMetrics) -> Dict[str, Any]:
        """Generate comprehensive risk report"""
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'overall_risk_score': self._calculate_overall_risk_score(metrics),
                'risk_level': self._determine_risk_level(metrics),
                'portfolio_health': self._assess_portfolio_health(metrics)
            },
            'var_metrics': {
                'var_95_historical': f"{metrics.var_95_historical:.2%}",
                'var_99_historical': f"{metrics.var_99_historical:.2%}",
                'var_95_parametric': f"{metrics.var_95_parametric:.2%}",
                'var_99_parametric': f"{metrics.var_99_parametric:.2%}",
                'var_95_monte_carlo': f"{metrics.var_95_monte_carlo:.2%}",
                'var_99_monte_carlo': f"{metrics.var_99_monte_carlo:.2%}",
                'cvar_95': f"{metrics.cvar_95:.2%}",
                'cvar_99': f"{metrics.cvar_99:.2%}"
            },
            'performance_metrics': {
                'sharpe_ratio': f"{metrics.sharpe_ratio:.2f}",
                'sortino_ratio': f"{metrics.sortino_ratio:.2f}",
                'calmar_ratio': f"{metrics.calmar_ratio:.2f}",
                'information_ratio': f"{metrics.information_ratio:.2f}",
                'risk_adjusted_return': f"{metrics.risk_adjusted_return:.2%}"
            },
            'risk_metrics': {
                'portfolio_volatility': f"{metrics.portfolio_volatility:.2%}",
                'portfolio_beta': f"{metrics.portfolio_beta:.2f}",
                'max_drawdown': f"{metrics.max_drawdown:.2%}",
                'current_drawdown': f"{metrics.current_drawdown:.2%}",
                'tracking_error': f"{metrics.tracking_error:.2%}"
            },
            'concentration_metrics': {
                'concentration_risk': f"{metrics.concentration_risk:.2%}",
                'liquidity_risk': f"{metrics.liquidity_risk:.2%}",
                'correlation_risk': f"{metrics.correlation_risk:.2%}",
                'tail_risk': f"{metrics.tail_risk:.2%}"
            },
            'position_sizing': {
                'kelly_fraction': f"{metrics.kelly_fraction:.2%}",
                'expectancy': f"{metrics.expectancy:.2f}R",
                'average_r_multiple': f"{np.mean(metrics.r_multiples):.2f}R" if metrics.r_multiples else "N/A",
                'win_rate': f"{len([r for r in metrics.r_multiples if r > 0])/len(metrics.r_multiples):.2%}" if metrics.r_multiples else "N/A"
            },
            'stress_test_summary': self._summarize_stress_tests(metrics.stress_test_results),
            'factor_exposures': metrics.factor_exposures,
            'recommendations': self._generate_risk_recommendations(metrics),
            'alerts': self._check_risk_alerts(metrics)
        }
        
        return report
    
    def _calculate_overall_risk_score(self, metrics: RiskMetrics) -> float:
        """Calculate overall risk score (0-100, higher is riskier)"""
        
        score = 0
        
        # VaR component (30%)
        var_component = min(metrics.var_95_historical / 0.10, 1.0) * 30
        score += var_component
        
        # Drawdown component (20%)
        dd_component = min(abs(metrics.max_drawdown) / 0.20, 1.0) * 20
        score += dd_component
        
        # Volatility component (15%)
        vol_component = min(metrics.portfolio_volatility / 0.30, 1.0) * 15
        score += vol_component
        
        # Concentration component (15%)
        conc_component = metrics.concentration_risk * 15
        score += conc_component
        
        # Liquidity component (10%)
        liq_component = metrics.liquidity_risk * 10
        score += liq_component
        
        # Tail risk component (10%)
        tail_component = metrics.tail_risk * 10
        score += tail_component
        
        return min(score, 100)
    
    def _determine_risk_level(self, metrics: RiskMetrics) -> str:
        """Determine risk level category"""
        
        risk_score = self._calculate_overall_risk_score(metrics)
        
        if risk_score < 20:
            return "Very Low"
        elif risk_score < 40:
            return "Low"
        elif risk_score < 60:
            return "Moderate"
        elif risk_score < 80:
            return "High"
        else:
            return "Very High"
    
    def _assess_portfolio_health(self, metrics: RiskMetrics) -> str:
        """Assess overall portfolio health"""
        
        issues = []
        
        if metrics.var_95_historical > self.risk_limits.max_var_95:
            issues.append("VaR exceeds limits")
        
        if abs(metrics.max_drawdown) > self.risk_limits.max_drawdown:
            issues.append("Maximum drawdown exceeds limits")
        
        if metrics.sharpe_ratio < self.risk_limits.min_sharpe_ratio:
            issues.append("Poor risk-adjusted returns")
        
        if metrics.concentration_risk > 0.5:
            issues.append("High concentration risk")
        
        if metrics.liquidity_risk > 0.7:
            issues.append("Low liquidity")
        
        if not issues:
            return "Healthy"
        elif len(issues) == 1:
            return f"Minor Issues: {issues[0]}"
        elif len(issues) <= 3:
            return f"Moderate Issues: {', '.join(issues[:2])}"
        else:
            return f"Critical Issues: Multiple risk violations"
    
    def _summarize_stress_tests(self, stress_results: Dict[str, float]) -> Dict[str, str]:
        """Summarize stress test results"""
        
        summary = {}
        
        for scenario, impact in stress_results.items():
            if impact < -0.30:
                severity = "Severe"
            elif impact < -0.15:
                severity = "Moderate"
            elif impact < -0.05:
                severity = "Minor"
            else:
                severity = "Minimal"
            
            summary[scenario] = f"{severity} impact: {impact:.1%}"
        
        # Add worst case
        if stress_results:
            worst_scenario = min(stress_results.items(), key=lambda x: x[1])
            summary['worst_case'] = f"{worst_scenario[0]}: {worst_scenario[1]:.1%}"
        
        return summary
    
    def _generate_risk_recommendations(self, metrics: RiskMetrics) -> List[str]:
        """Generate risk management recommendations"""
        
        recommendations = []
        
        # VaR recommendations
        if metrics.var_95_historical > self.risk_limits.max_var_95:
            recommendations.append("Reduce portfolio risk: Consider decreasing position sizes or adding hedges")
        
        # Drawdown recommendations
        if abs(metrics.current_drawdown) > 0.10:
            recommendations.append("Portfolio in drawdown: Review stop losses and consider defensive positioning")
        
        # Sharpe ratio recommendations
        if metrics.sharpe_ratio < self.risk_limits.min_sharpe_ratio:
            recommendations.append("Improve risk-adjusted returns: Review asset allocation and rebalance")
        
        # Concentration recommendations
        if metrics.concentration_risk > 0.5:
            recommendations.append("Diversify portfolio: Reduce largest positions and add uncorrelated assets")
        
        # Liquidity recommendations
        if metrics.liquidity_risk > 0.5:
            recommendations.append("Improve liquidity: Increase allocation to liquid assets")
        
        # Correlation recommendations
        if metrics.correlation_risk > 0.7:
            recommendations.append("Reduce correlation: Add assets with low correlation to existing holdings")
        
        # Position sizing recommendations
        if metrics.expectancy < 0:
            recommendations.append("Review trading strategy: Negative expectancy indicates losing system")
        
        if metrics.kelly_fraction < 0.10:
            recommendations.append("Conservative position sizing recommended based on Kelly Criterion")
        
        # Stress test recommendations
        worst_stress = min(metrics.stress_test_results.values()) if metrics.stress_test_results else 0
        if worst_stress < -0.30:
            recommendations.append("High stress test risk: Consider tail risk hedging strategies")
        
        return recommendations
    
    def _check_risk_alerts(self, metrics: RiskMetrics) -> List[Dict[str, str]]:
        """Check for risk alerts and violations"""
        
        alerts = []
        
        # Check VaR limits
        if metrics.var_95_historical > self.risk_limits.max_var_95:
            alerts.append({
                'type': 'VaR Breach',
                'severity': 'High',
                'message': f'95% VaR ({metrics.var_95_historical:.2%}) exceeds limit ({self.risk_limits.max_var_95:.2%})',
                'action': 'Reduce risk immediately'
            })
        
        # Check drawdown limits
        if abs(metrics.max_drawdown) > self.risk_limits.max_drawdown:
            alerts.append({
                'type': 'Drawdown Breach',
                'severity': 'High',
                'message': f'Maximum drawdown ({metrics.max_drawdown:.2%}) exceeds limit ({self.risk_limits.max_drawdown:.2%})',
                'action': 'Review position sizing and stops'
            })
        
        # Check Sharpe ratio
        if metrics.sharpe_ratio < 0:
            alerts.append({
                'type': 'Negative Sharpe',
                'severity': 'Medium',
                'message': 'Negative Sharpe ratio indicates returns below risk-free rate',
                'action': 'Review portfolio allocation'
            })
        
        # Check concentration
        if metrics.concentration_risk > 0.7:
            alerts.append({
                'type': 'High Concentration',
                'severity': 'Medium',
                'message': f'Portfolio concentration risk is high ({metrics.concentration_risk:.2%})',
                'action': 'Diversify holdings'
            })
        
        # Check expectancy
        if metrics.expectancy < 0:
            alerts.append({
                'type': 'Negative Expectancy',
                'severity': 'High',
                'message': f'Trading expectancy is negative ({metrics.expectancy:.2f}R)',
                'action': 'Stop trading and review strategy'
            })
        
        self.alerts.extend(alerts)
        return alerts


# Example usage
async def demo_risk_management():
    """Demonstrate risk management engine capabilities"""
    
    # Create sample positions
    positions = [
        PortfolioPosition(
            symbol="AAPL",
            quantity=100,
            current_price=175.50,
            cost_basis=170.00,
            asset_class="equity",
            sector="Technology",
            market_cap="Large",
            liquidity_score=0.95,
            beta=1.2,
            volatility=0.22
        ),
        PortfolioPosition(
            symbol="MSFT",
            quantity=50,
            current_price=380.00,
            cost_basis=370.00,
            asset_class="equity",
            sector="Technology",
            market_cap="Large",
            liquidity_score=0.95,
            beta=1.1,
            volatility=0.20
        ),
        PortfolioPosition(
            symbol="GLD",
            quantity=200,
            current_price=185.00,
            cost_basis=180.00,
            asset_class="commodity",
            sector="Precious Metals",
            market_cap="Large",
            liquidity_score=0.90,
            beta=0.3,
            volatility=0.15
        )
    ]
    
    # Generate sample historical returns
    np.random.seed(42)
    dates = pd.date_range(end=datetime.now(), periods=252, freq='D')
    returns_data = np.random.multivariate_normal(
        [0.0005, 0.0004, 0.0002],  # Daily returns
        [[0.0004, 0.0002, 0.0001],  # Covariance matrix
         [0.0002, 0.0003, 0.0001],
         [0.0001, 0.0001, 0.0002]],
        252
    )
    
    historical_returns = pd.DataFrame(
        returns_data,
        index=dates,
        columns=['AAPL', 'MSFT', 'GLD']
    )
    
    # Create risk management engine
    risk_limits = RiskLimits(
        max_var_95=0.05,
        max_var_99=0.10,
        max_position_size=0.15,
        max_drawdown=0.20,
        risk_per_trade=0.02
    )
    
    engine = RiskManagementEngine(risk_limits)
    
    # Calculate risk metrics
    print("Calculating comprehensive risk metrics...")
    metrics = await engine.calculate_comprehensive_risk_metrics(
        positions,
        historical_returns
    )
    
    # Generate risk report
    report = engine.generate_risk_report(metrics)
    
    # Display report
    print("\n" + "="*60)
    print("RISK MANAGEMENT REPORT")
    print("="*60)
    
    print(f"\nRisk Level: {report['summary']['risk_level']}")
    print(f"Portfolio Health: {report['summary']['portfolio_health']}")
    print(f"Overall Risk Score: {report['summary']['overall_risk_score']:.1f}/100")
    
    print("\n--- VaR Metrics ---")
    for key, value in report['var_metrics'].items():
        print(f"{key}: {value}")
    
    print("\n--- Performance Metrics ---")
    for key, value in report['performance_metrics'].items():
        print(f"{key}: {value}")
    
    print("\n--- Position Sizing (Kelly Criterion) ---")
    for key, value in report['position_sizing'].items():
        print(f"{key}: {value}")
    
    print("\n--- Stress Test Results ---")
    for scenario, result in report['stress_test_summary'].items():
        print(f"{scenario}: {result}")
    
    print("\n--- Recommendations ---")
    for i, rec in enumerate(report['recommendations'], 1):
        print(f"{i}. {rec}")
    
    print("\n--- Risk Alerts ---")
    if report['alerts']:
        for alert in report['alerts']:
            print(f"⚠️ [{alert['severity']}] {alert['type']}: {alert['message']}")
            print(f"   Action: {alert['action']}")
    else:
        print("✓ No risk alerts")
    
    # Example position sizing calculation
    print("\n" + "="*60)
    print("POSITION SIZING EXAMPLE")
    print("="*60)
    
    position_calc = engine.calculate_position_size(
        account_value=100000,
        entry_price=150,
        stop_loss=145
    )
    
    print(f"Account Value: $100,000")
    print(f"Entry Price: $150")
    print(f"Stop Loss: $145")
    print(f"\nRecommended Position Size: {position_calc['position_size']} shares")
    print(f"Position Value: ${position_calc['position_value']:,.2f}")
    print(f"Risk Amount (1R): ${position_calc['risk_amount']:,.2f}")
    print(f"Risk Percentage: {position_calc['risk_percentage']:.2%}")
    print(f"Kelly Fraction: {position_calc['kelly_fraction']:.2%}" if position_calc['kelly_fraction'] else "Kelly Fraction: N/A")
    
    # Example trade tracking
    print("\n" + "="*60)
    print("TRADE TRACKING EXAMPLE")
    print("="*60)
    
    # Add some sample trades
    trades = [
        (150, 155, 145, 100),  # Win: +5R/1R = +1R
        (200, 195, 210, 50),   # Loss: -5R/10R = -0.5R
        (75, 85, 70, 200),     # Win: +10R/5R = +2R
    ]
    
    for entry, exit, stop, size in trades:
        trade = engine.add_trade_result(entry, exit, stop, size)
        result = "WIN" if trade.r_multiple > 0 else "LOSS"
        print(f"{result}: {trade.r_multiple:.2f}R")
    
    expectancy = engine._calculate_expectancy()
    print(f"\nExpectancy: {expectancy:.2f}R per trade")
    print(f"Win Rate: {len([t for t in engine.trade_history if t.r_multiple > 0])/len(engine.trade_history):.1%}")


if __name__ == "__main__":
    asyncio.run(demo_risk_management())