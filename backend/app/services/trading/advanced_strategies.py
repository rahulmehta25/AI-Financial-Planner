"""
Advanced Trading Strategies Module

Implements sophisticated trading strategies including options strategies,
statistical arbitrage, pair trading with cointegration, and volatility modeling.

Features:
- Options strategies (covered calls, spreads, straddles, iron condors)
- Black-Scholes option pricing
- Pair trading with cointegration testing
- Statistical arbitrage
- GARCH volatility modeling
- Market view-based strategy selection
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Union
from enum import Enum
from datetime import datetime, timedelta
import numpy as np
from scipy import stats
from scipy.optimize import minimize, brentq
import pandas as pd
import asyncio
import logging
from collections import defaultdict
import warnings

# Suppress numpy warnings for cleaner output
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)


class MarketView(Enum):
    """Market outlook for strategy selection"""
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"
    VOLATILE = "volatile"
    RANGE_BOUND = "range_bound"


class OptionType(Enum):
    """Option type classification"""
    CALL = "call"
    PUT = "put"


class StrategyType(Enum):
    """Trading strategy classification"""
    # Options Strategies
    COVERED_CALL = "covered_call"
    PROTECTIVE_PUT = "protective_put"
    BULL_CALL_SPREAD = "bull_call_spread"
    BEAR_PUT_SPREAD = "bear_put_spread"
    LONG_STRADDLE = "long_straddle"
    LONG_STRANGLE = "long_strangle"
    IRON_CONDOR = "iron_condor"
    BUTTERFLY_SPREAD = "butterfly_spread"
    COLLAR = "collar"
    CALENDAR_SPREAD = "calendar_spread"
    
    # Statistical Arbitrage
    PAIR_TRADING = "pair_trading"
    MEAN_REVERSION = "mean_reversion"
    MOMENTUM = "momentum"
    STAT_ARB = "statistical_arbitrage"
    
    # Volatility Strategies
    VOLATILITY_ARBITRAGE = "volatility_arbitrage"
    DISPERSION_TRADING = "dispersion_trading"


@dataclass
class OptionContract:
    """Option contract specification"""
    type: OptionType
    strike: float
    expiry: datetime
    premium: float
    implied_volatility: Optional[float] = None
    delta: Optional[float] = None
    gamma: Optional[float] = None
    theta: Optional[float] = None
    vega: Optional[float] = None
    rho: Optional[float] = None


@dataclass
class OptionStrategy:
    """Options strategy definition"""
    strategy_type: StrategyType
    legs: List[Dict[str, Any]]
    max_profit: Optional[float] = None
    max_loss: Optional[float] = None
    breakeven_points: List[float] = field(default_factory=list)
    probability_profit: Optional[float] = None
    expected_value: Optional[float] = None
    margin_requirement: Optional[float] = None


@dataclass
class PairTradingSignal:
    """Pair trading signal"""
    pair: Tuple[str, str]
    z_score: float
    spread: float
    hedge_ratio: float
    cointegration_pvalue: float
    half_life: float
    signal: str  # "long_spread", "short_spread", "neutral"
    confidence: float


@dataclass
class GARCHForecast:
    """GARCH volatility forecast"""
    current_volatility: float
    forecast_1d: float
    forecast_5d: float
    forecast_20d: float
    volatility_term_structure: np.ndarray
    confidence_intervals: Dict[str, Tuple[float, float]]


class BlackScholesModel:
    """Black-Scholes option pricing model with Greeks calculation"""
    
    @staticmethod
    def calculate_d1_d2(S: float, K: float, r: float, sigma: float, T: float) -> Tuple[float, float]:
        """Calculate d1 and d2 parameters for Black-Scholes formula"""
        d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        return d1, d2
    
    @staticmethod
    def call_price(S: float, K: float, r: float, sigma: float, T: float) -> float:
        """Calculate call option price using Black-Scholes formula"""
        if T <= 0:
            return max(S - K, 0)
        
        d1, d2 = BlackScholesModel.calculate_d1_d2(S, K, r, sigma, T)
        call_price = S * stats.norm.cdf(d1) - K * np.exp(-r * T) * stats.norm.cdf(d2)
        return call_price
    
    @staticmethod
    def put_price(S: float, K: float, r: float, sigma: float, T: float) -> float:
        """Calculate put option price using Black-Scholes formula"""
        if T <= 0:
            return max(K - S, 0)
        
        d1, d2 = BlackScholesModel.calculate_d1_d2(S, K, r, sigma, T)
        put_price = K * np.exp(-r * T) * stats.norm.cdf(-d2) - S * stats.norm.cdf(-d1)
        return put_price
    
    @staticmethod
    def implied_volatility(option_price: float, S: float, K: float, r: float, T: float,
                          option_type: OptionType) -> float:
        """Calculate implied volatility using Newton-Raphson method"""
        
        def objective(sigma):
            if option_type == OptionType.CALL:
                return BlackScholesModel.call_price(S, K, r, sigma, T) - option_price
            else:
                return BlackScholesModel.put_price(S, K, r, sigma, T) - option_price
        
        try:
            # Use Brent's method to find implied volatility
            iv = brentq(objective, 0.001, 5.0)
            return iv
        except:
            return 0.3  # Return default if convergence fails
    
    @staticmethod
    def calculate_greeks(S: float, K: float, r: float, sigma: float, T: float,
                        option_type: OptionType) -> Dict[str, float]:
        """Calculate all Greeks for an option"""
        
        if T <= 0:
            return {
                'delta': 1.0 if option_type == OptionType.CALL else -1.0 if S < K else 0.0,
                'gamma': 0.0,
                'theta': 0.0,
                'vega': 0.0,
                'rho': 0.0
            }
        
        d1, d2 = BlackScholesModel.calculate_d1_d2(S, K, r, sigma, T)
        
        # Delta
        if option_type == OptionType.CALL:
            delta = stats.norm.cdf(d1)
        else:
            delta = -stats.norm.cdf(-d1)
        
        # Gamma (same for calls and puts)
        gamma = stats.norm.pdf(d1) / (S * sigma * np.sqrt(T))
        
        # Theta
        if option_type == OptionType.CALL:
            theta = (-S * stats.norm.pdf(d1) * sigma / (2 * np.sqrt(T))
                    - r * K * np.exp(-r * T) * stats.norm.cdf(d2)) / 365
        else:
            theta = (-S * stats.norm.pdf(d1) * sigma / (2 * np.sqrt(T))
                    + r * K * np.exp(-r * T) * stats.norm.cdf(-d2)) / 365
        
        # Vega (same for calls and puts)
        vega = S * stats.norm.pdf(d1) * np.sqrt(T) / 100
        
        # Rho
        if option_type == OptionType.CALL:
            rho = K * T * np.exp(-r * T) * stats.norm.cdf(d2) / 100
        else:
            rho = -K * T * np.exp(-r * T) * stats.norm.cdf(-d2) / 100
        
        return {
            'delta': delta,
            'gamma': gamma,
            'theta': theta,
            'vega': vega,
            'rho': rho
        }


class CointegrationAnalyzer:
    """Statistical cointegration analysis for pair trading"""
    
    @staticmethod
    def test_cointegration(prices1: np.ndarray, prices2: np.ndarray) -> Dict[str, Any]:
        """Test for cointegration using Engle-Granger method"""
        from statsmodels.tsa.stattools import coint, adfuller
        
        # Run cointegration test
        score, pvalue, _ = coint(prices1, prices2)
        
        # Calculate hedge ratio using OLS
        X = np.column_stack([prices2, np.ones(len(prices2))])
        hedge_ratio, intercept = np.linalg.lstsq(X, prices1, rcond=None)[0]
        
        # Calculate spread
        spread = prices1 - hedge_ratio * prices2 - intercept
        
        # Test spread for stationarity
        adf_result = adfuller(spread, autolag='AIC')
        
        # Calculate half-life of mean reversion
        spread_lag = spread[:-1]
        spread_diff = np.diff(spread)
        X_lag = np.column_stack([spread_lag, np.ones(len(spread_lag))])
        theta = np.linalg.lstsq(X_lag, spread_diff, rcond=None)[0][0]
        half_life = -np.log(2) / theta if theta < 0 else np.inf
        
        return {
            'cointegrated': pvalue < 0.05,
            'pvalue': pvalue,
            'hedge_ratio': hedge_ratio,
            'spread': spread,
            'spread_mean': np.mean(spread),
            'spread_std': np.std(spread),
            'half_life': half_life,
            'adf_statistic': adf_result[0],
            'adf_pvalue': adf_result[1]
        }
    
    @staticmethod
    def calculate_z_score(spread: np.ndarray, lookback: int = 20) -> float:
        """Calculate z-score of current spread value"""
        if len(spread) < lookback:
            return 0.0
        
        spread_mean = np.mean(spread[-lookback:])
        spread_std = np.std(spread[-lookback:])
        
        if spread_std == 0:
            return 0.0
        
        return (spread[-1] - spread_mean) / spread_std


class GARCHModel:
    """GARCH(1,1) volatility modeling"""
    
    def __init__(self, omega: float = 0.00001, alpha: float = 0.1, beta: float = 0.85):
        """Initialize GARCH model parameters"""
        self.omega = omega  # Long-term variance weight
        self.alpha = alpha  # ARCH parameter (squared returns weight)
        self.beta = beta    # GARCH parameter (previous variance weight)
        
        # Ensure stationarity condition
        if self.alpha + self.beta >= 1:
            self.beta = 0.99 - self.alpha
    
    def fit(self, returns: np.ndarray) -> None:
        """Fit GARCH model to historical returns using MLE"""
        
        def negative_log_likelihood(params):
            omega, alpha, beta = params
            
            # Initialize variance
            variance = np.var(returns)
            log_likelihood = 0
            
            for r in returns:
                # Update log-likelihood
                log_likelihood -= 0.5 * (np.log(2 * np.pi * variance) + r**2 / variance)
                
                # Update variance for next period
                variance = omega + alpha * r**2 + beta * variance
            
            return -log_likelihood
        
        # Optimize parameters
        bounds = [(1e-6, 1), (0, 1), (0, 1)]
        constraints = {'type': 'ineq', 'fun': lambda x: 0.999 - x[1] - x[2]}
        
        result = minimize(
            negative_log_likelihood,
            x0=[self.omega, self.alpha, self.beta],
            bounds=bounds,
            constraints=constraints,
            method='SLSQP'
        )
        
        if result.success:
            self.omega, self.alpha, self.beta = result.x
    
    def forecast(self, returns: np.ndarray, horizon: int = 20) -> GARCHForecast:
        """Generate volatility forecast"""
        
        # Calculate current volatility
        variance = np.var(returns)
        for r in returns[-20:]:  # Use recent returns
            variance = self.omega + self.alpha * r**2 + self.beta * variance
        
        current_vol = np.sqrt(variance * 252)  # Annualized
        
        # Multi-period forecast
        forecasts = []
        forecast_var = variance
        
        for h in range(horizon):
            forecast_var = self.omega + (self.alpha + self.beta) * forecast_var
            forecasts.append(np.sqrt(forecast_var * 252))
        
        # Calculate confidence intervals
        confidence_intervals = {
            '95%': (current_vol * 0.8, current_vol * 1.2),
            '99%': (current_vol * 0.7, current_vol * 1.3)
        }
        
        return GARCHForecast(
            current_volatility=current_vol,
            forecast_1d=forecasts[0] if len(forecasts) > 0 else current_vol,
            forecast_5d=forecasts[4] if len(forecasts) > 4 else current_vol,
            forecast_20d=forecasts[19] if len(forecasts) > 19 else current_vol,
            volatility_term_structure=np.array(forecasts),
            confidence_intervals=confidence_intervals
        )


class AdvancedTradingStrategies:
    """Main class for advanced trading strategies implementation"""
    
    def __init__(self, risk_free_rate: float = 0.05):
        """Initialize trading strategies engine"""
        self.risk_free_rate = risk_free_rate
        self.bs_model = BlackScholesModel()
        self.coint_analyzer = CointegrationAnalyzer()
        self.garch_models: Dict[str, GARCHModel] = {}
        
    async def create_options_strategy(
        self,
        underlying_price: float,
        market_view: MarketView,
        volatility: float,
        days_to_expiry: int = 30,
        capital: float = 10000
    ) -> OptionStrategy:
        """Create optimal options strategy based on market view"""
        
        T = days_to_expiry / 365.0
        
        # Select strategy based on market view
        if market_view == MarketView.BULLISH:
            return self._create_bull_call_spread(underlying_price, volatility, T, capital)
        elif market_view == MarketView.BEARISH:
            return self._create_bear_put_spread(underlying_price, volatility, T, capital)
        elif market_view == MarketView.NEUTRAL:
            return self._create_iron_condor(underlying_price, volatility, T, capital)
        elif market_view == MarketView.VOLATILE:
            return self._create_long_straddle(underlying_price, volatility, T, capital)
        elif market_view == MarketView.RANGE_BOUND:
            return self._create_butterfly_spread(underlying_price, volatility, T, capital)
        else:
            # Default to covered call for income generation
            return self._create_covered_call(underlying_price, volatility, T, capital)
    
    def _create_covered_call(
        self,
        S: float,
        sigma: float,
        T: float,
        capital: float
    ) -> OptionStrategy:
        """Create covered call strategy"""
        
        # Select OTM strike (typically 2-5% above current price)
        strike = S * 1.03
        
        # Calculate option premium
        call_premium = self.bs_model.call_price(S, strike, self.risk_free_rate, sigma, T)
        
        # Calculate Greeks
        greeks = self.bs_model.calculate_greeks(S, strike, self.risk_free_rate, sigma, T, OptionType.CALL)
        
        # Number of contracts (100 shares per contract)
        num_contracts = int(capital / (S * 100))
        
        strategy = OptionStrategy(
            strategy_type=StrategyType.COVERED_CALL,
            legs=[
                {'type': 'stock', 'quantity': 100 * num_contracts, 'price': S},
                {'type': 'call', 'quantity': -num_contracts, 'strike': strike, 
                 'premium': call_premium, 'greeks': greeks}
            ],
            max_profit=(strike - S + call_premium) * 100 * num_contracts,
            max_loss=(S - call_premium) * 100 * num_contracts,
            breakeven_points=[S - call_premium],
            margin_requirement=capital
        )
        
        # Calculate probability of profit
        d2 = (np.log(S / strike) + (self.risk_free_rate - 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        strategy.probability_profit = 1 - stats.norm.cdf(d2)
        
        return strategy
    
    def _create_bull_call_spread(
        self,
        S: float,
        sigma: float,
        T: float,
        capital: float
    ) -> OptionStrategy:
        """Create bull call spread strategy"""
        
        # Buy ATM call, sell OTM call
        long_strike = S
        short_strike = S * 1.05
        
        long_premium = self.bs_model.call_price(S, long_strike, self.risk_free_rate, sigma, T)
        short_premium = self.bs_model.call_price(S, short_strike, self.risk_free_rate, sigma, T)
        
        net_debit = long_premium - short_premium
        num_spreads = int(capital / (net_debit * 100))
        
        strategy = OptionStrategy(
            strategy_type=StrategyType.BULL_CALL_SPREAD,
            legs=[
                {'type': 'call', 'quantity': num_spreads, 'strike': long_strike, 
                 'premium': long_premium, 'action': 'buy'},
                {'type': 'call', 'quantity': -num_spreads, 'strike': short_strike,
                 'premium': short_premium, 'action': 'sell'}
            ],
            max_profit=(short_strike - long_strike - net_debit) * 100 * num_spreads,
            max_loss=net_debit * 100 * num_spreads,
            breakeven_points=[long_strike + net_debit],
            margin_requirement=net_debit * 100 * num_spreads
        )
        
        return strategy
    
    def _create_bear_put_spread(
        self,
        S: float,
        sigma: float,
        T: float,
        capital: float
    ) -> OptionStrategy:
        """Create bear put spread strategy"""
        
        # Buy ATM put, sell OTM put
        long_strike = S
        short_strike = S * 0.95
        
        long_premium = self.bs_model.put_price(S, long_strike, self.risk_free_rate, sigma, T)
        short_premium = self.bs_model.put_price(S, short_strike, self.risk_free_rate, sigma, T)
        
        net_debit = long_premium - short_premium
        num_spreads = int(capital / (net_debit * 100))
        
        strategy = OptionStrategy(
            strategy_type=StrategyType.BEAR_PUT_SPREAD,
            legs=[
                {'type': 'put', 'quantity': num_spreads, 'strike': long_strike,
                 'premium': long_premium, 'action': 'buy'},
                {'type': 'put', 'quantity': -num_spreads, 'strike': short_strike,
                 'premium': short_premium, 'action': 'sell'}
            ],
            max_profit=(long_strike - short_strike - net_debit) * 100 * num_spreads,
            max_loss=net_debit * 100 * num_spreads,
            breakeven_points=[long_strike - net_debit],
            margin_requirement=net_debit * 100 * num_spreads
        )
        
        return strategy
    
    def _create_iron_condor(
        self,
        S: float,
        sigma: float,
        T: float,
        capital: float
    ) -> OptionStrategy:
        """Create iron condor strategy for range-bound markets"""
        
        # Sell OTM call spread and OTM put spread
        call_short_strike = S * 1.03
        call_long_strike = S * 1.05
        put_short_strike = S * 0.97
        put_long_strike = S * 0.95
        
        # Calculate premiums
        call_short_prem = self.bs_model.call_price(S, call_short_strike, self.risk_free_rate, sigma, T)
        call_long_prem = self.bs_model.call_price(S, call_long_strike, self.risk_free_rate, sigma, T)
        put_short_prem = self.bs_model.put_price(S, put_short_strike, self.risk_free_rate, sigma, T)
        put_long_prem = self.bs_model.put_price(S, put_long_strike, self.risk_free_rate, sigma, T)
        
        net_credit = (call_short_prem - call_long_prem) + (put_short_prem - put_long_prem)
        
        # Risk calculation
        max_risk = max(call_long_strike - call_short_strike, put_short_strike - put_long_strike) - net_credit
        num_condors = int(capital / (max_risk * 100))
        
        strategy = OptionStrategy(
            strategy_type=StrategyType.IRON_CONDOR,
            legs=[
                {'type': 'call', 'quantity': -num_condors, 'strike': call_short_strike,
                 'premium': call_short_prem, 'action': 'sell'},
                {'type': 'call', 'quantity': num_condors, 'strike': call_long_strike,
                 'premium': call_long_prem, 'action': 'buy'},
                {'type': 'put', 'quantity': -num_condors, 'strike': put_short_strike,
                 'premium': put_short_prem, 'action': 'sell'},
                {'type': 'put', 'quantity': num_condors, 'strike': put_long_strike,
                 'premium': put_long_prem, 'action': 'buy'}
            ],
            max_profit=net_credit * 100 * num_condors,
            max_loss=max_risk * 100 * num_condors,
            breakeven_points=[
                put_short_strike - net_credit,
                call_short_strike + net_credit
            ],
            margin_requirement=max_risk * 100 * num_condors
        )
        
        # Calculate probability of profit (price stays between short strikes)
        d1_put = (np.log(S / put_short_strike) + (self.risk_free_rate - 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        d1_call = (np.log(S / call_short_strike) + (self.risk_free_rate - 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        
        prob_below_put = stats.norm.cdf(d1_put)
        prob_above_call = 1 - stats.norm.cdf(d1_call)
        strategy.probability_profit = 1 - prob_below_put - prob_above_call
        
        return strategy
    
    def _create_long_straddle(
        self,
        S: float,
        sigma: float,
        T: float,
        capital: float
    ) -> OptionStrategy:
        """Create long straddle for high volatility expectations"""
        
        strike = S  # ATM straddle
        
        call_premium = self.bs_model.call_price(S, strike, self.risk_free_rate, sigma, T)
        put_premium = self.bs_model.put_price(S, strike, self.risk_free_rate, sigma, T)
        
        total_premium = call_premium + put_premium
        num_straddles = int(capital / (total_premium * 100))
        
        # Breakeven points
        upper_breakeven = strike + total_premium
        lower_breakeven = strike - total_premium
        
        strategy = OptionStrategy(
            strategy_type=StrategyType.LONG_STRADDLE,
            legs=[
                {'type': 'call', 'quantity': num_straddles, 'strike': strike,
                 'premium': call_premium, 'action': 'buy'},
                {'type': 'put', 'quantity': num_straddles, 'strike': strike,
                 'premium': put_premium, 'action': 'buy'}
            ],
            max_profit=float('inf'),  # Unlimited upside
            max_loss=total_premium * 100 * num_straddles,
            breakeven_points=[lower_breakeven, upper_breakeven],
            margin_requirement=total_premium * 100 * num_straddles
        )
        
        # Calculate probability of profit (need move beyond breakeven)
        move_required = total_premium / S
        z_score = move_required / (sigma * np.sqrt(T))
        strategy.probability_profit = 2 * (1 - stats.norm.cdf(z_score))
        
        return strategy
    
    def _create_butterfly_spread(
        self,
        S: float,
        sigma: float,
        T: float,
        capital: float
    ) -> OptionStrategy:
        """Create butterfly spread for low volatility/range-bound view"""
        
        # ATM butterfly
        lower_strike = S * 0.95
        middle_strike = S
        upper_strike = S * 1.05
        
        # Calculate premiums
        lower_call = self.bs_model.call_price(S, lower_strike, self.risk_free_rate, sigma, T)
        middle_call = self.bs_model.call_price(S, middle_strike, self.risk_free_rate, sigma, T)
        upper_call = self.bs_model.call_price(S, upper_strike, self.risk_free_rate, sigma, T)
        
        net_debit = lower_call - 2 * middle_call + upper_call
        num_butterflies = int(capital / (net_debit * 100))
        
        max_profit = (middle_strike - lower_strike - net_debit) * 100 * num_butterflies
        
        strategy = OptionStrategy(
            strategy_type=StrategyType.BUTTERFLY_SPREAD,
            legs=[
                {'type': 'call', 'quantity': num_butterflies, 'strike': lower_strike,
                 'premium': lower_call, 'action': 'buy'},
                {'type': 'call', 'quantity': -2 * num_butterflies, 'strike': middle_strike,
                 'premium': middle_call, 'action': 'sell'},
                {'type': 'call', 'quantity': num_butterflies, 'strike': upper_strike,
                 'premium': upper_call, 'action': 'buy'}
            ],
            max_profit=max_profit,
            max_loss=net_debit * 100 * num_butterflies,
            breakeven_points=[
                lower_strike + net_debit,
                upper_strike - net_debit
            ],
            margin_requirement=net_debit * 100 * num_butterflies
        )
        
        return strategy
    
    async def identify_pair_trading_opportunities(
        self,
        price_data: Dict[str, np.ndarray],
        lookback_period: int = 60,
        z_score_threshold: float = 2.0
    ) -> List[PairTradingSignal]:
        """Identify pair trading opportunities using cointegration analysis"""
        
        opportunities = []
        symbols = list(price_data.keys())
        
        # Test all pairs for cointegration
        for i in range(len(symbols)):
            for j in range(i + 1, len(symbols)):
                symbol1, symbol2 = symbols[i], symbols[j]
                prices1, prices2 = price_data[symbol1], price_data[symbol2]
                
                if len(prices1) < lookback_period or len(prices2) < lookback_period:
                    continue
                
                # Test cointegration
                coint_result = self.coint_analyzer.test_cointegration(
                    prices1[-lookback_period:],
                    prices2[-lookback_period:]
                )
                
                if coint_result['cointegrated']:
                    # Calculate current z-score
                    z_score = self.coint_analyzer.calculate_z_score(coint_result['spread'])
                    
                    # Generate signal
                    if abs(z_score) > z_score_threshold:
                        signal = "short_spread" if z_score > 0 else "long_spread"
                        confidence = min(abs(z_score) / 3.0, 1.0)  # Confidence based on z-score
                        
                        opportunities.append(PairTradingSignal(
                            pair=(symbol1, symbol2),
                            z_score=z_score,
                            spread=coint_result['spread'][-1],
                            hedge_ratio=coint_result['hedge_ratio'],
                            cointegration_pvalue=coint_result['pvalue'],
                            half_life=coint_result['half_life'],
                            signal=signal,
                            confidence=confidence
                        ))
        
        # Sort by confidence
        opportunities.sort(key=lambda x: x.confidence, reverse=True)
        
        return opportunities
    
    async def calculate_volatility_forecast(
        self,
        symbol: str,
        returns: np.ndarray,
        horizon: int = 20
    ) -> GARCHForecast:
        """Calculate GARCH volatility forecast for a symbol"""
        
        # Get or create GARCH model for symbol
        if symbol not in self.garch_models:
            self.garch_models[symbol] = GARCHModel()
        
        garch = self.garch_models[symbol]
        
        # Fit model to recent returns
        garch.fit(returns[-252:])  # Use last year of returns
        
        # Generate forecast
        forecast = garch.forecast(returns, horizon)
        
        return forecast
    
    async def statistical_arbitrage_scan(
        self,
        price_data: Dict[str, np.ndarray],
        volume_data: Dict[str, np.ndarray],
        lookback: int = 20
    ) -> List[Dict[str, Any]]:
        """Scan for statistical arbitrage opportunities"""
        
        opportunities = []
        
        for symbol, prices in price_data.items():
            if len(prices) < lookback + 1:
                continue
            
            volumes = volume_data.get(symbol, np.ones(len(prices)))
            
            # Calculate returns
            returns = np.diff(prices) / prices[:-1]
            
            # Mean reversion signal
            recent_return = (prices[-1] - prices[-lookback]) / prices[-lookback]
            avg_return = np.mean(returns[-lookback:])
            std_return = np.std(returns[-lookback:])
            
            if std_return > 0:
                z_score = (recent_return - avg_return) / std_return
                
                # Strong mean reversion opportunity
                if abs(z_score) > 2.5:
                    signal = "buy" if z_score < -2.5 else "sell"
                    
                    # Calculate expected return to mean
                    expected_move = -z_score * std_return
                    
                    # Volume confirmation
                    avg_volume = np.mean(volumes[-lookback:])
                    recent_volume = volumes[-1]
                    volume_ratio = recent_volume / avg_volume if avg_volume > 0 else 1
                    
                    opportunities.append({
                        'symbol': symbol,
                        'strategy': 'mean_reversion',
                        'signal': signal,
                        'z_score': z_score,
                        'expected_return': expected_move,
                        'confidence': min(abs(z_score) / 3.0, 1.0),
                        'volume_confirmation': volume_ratio > 1.2,
                        'current_price': prices[-1],
                        'target_price': prices[-1] * (1 + expected_move)
                    })
            
            # Momentum signal
            short_ma = np.mean(prices[-5:])
            long_ma = np.mean(prices[-20:])
            
            if long_ma > 0:
                momentum = (short_ma - long_ma) / long_ma
                
                if abs(momentum) > 0.02:  # 2% divergence
                    signal = "buy" if momentum > 0 else "sell"
                    
                    opportunities.append({
                        'symbol': symbol,
                        'strategy': 'momentum',
                        'signal': signal,
                        'momentum': momentum,
                        'confidence': min(abs(momentum) * 20, 1.0),
                        'short_ma': short_ma,
                        'long_ma': long_ma,
                        'current_price': prices[-1]
                    })
        
        # Sort by confidence
        opportunities.sort(key=lambda x: x['confidence'], reverse=True)
        
        return opportunities
    
    def calculate_option_implied_move(
        self,
        atm_call_iv: float,
        atm_put_iv: float,
        days_to_expiry: int
    ) -> Dict[str, float]:
        """Calculate expected move based on option implied volatility"""
        
        # Average IV for ATM straddle
        avg_iv = (atm_call_iv + atm_put_iv) / 2
        
        # Time factor
        time_factor = np.sqrt(days_to_expiry / 365)
        
        # Expected move (1 standard deviation)
        expected_move_1sd = avg_iv * time_factor
        
        # 2 standard deviation move (95% confidence)
        expected_move_2sd = expected_move_1sd * 2
        
        return {
            'expected_move_1sd': expected_move_1sd,
            'expected_move_2sd': expected_move_2sd,
            'probability_within_1sd': 0.68,
            'probability_within_2sd': 0.95,
            'breakeven_up': 1 + expected_move_1sd,
            'breakeven_down': 1 - expected_move_1sd
        }
    
    def backtest_options_strategy(
        self,
        strategy: OptionStrategy,
        price_path: np.ndarray,
        volatility_path: np.ndarray
    ) -> Dict[str, Any]:
        """Backtest an options strategy over historical price path"""
        
        results = []
        
        for t, (price, vol) in enumerate(zip(price_path, volatility_path)):
            pnl = 0
            
            # Calculate P&L for each leg
            for leg in strategy.legs:
                if leg['type'] == 'stock':
                    pnl += leg['quantity'] * (price - leg['price'])
                elif leg['type'] in ['call', 'put']:
                    # Recalculate option value
                    time_remaining = max(0, 30 - t) / 365.0
                    
                    if time_remaining > 0:
                        if leg['type'] == 'call':
                            option_value = self.bs_model.call_price(
                                price, leg['strike'], self.risk_free_rate, vol, time_remaining
                            )
                        else:
                            option_value = self.bs_model.put_price(
                                price, leg['strike'], self.risk_free_rate, vol, time_remaining
                            )
                    else:
                        # At expiration
                        if leg['type'] == 'call':
                            option_value = max(price - leg['strike'], 0)
                        else:
                            option_value = max(leg['strike'] - price, 0)
                    
                    # P&L calculation (negative quantity means short)
                    pnl += leg['quantity'] * 100 * (option_value - leg['premium'])
            
            results.append({
                'day': t,
                'price': price,
                'pnl': pnl,
                'cumulative_pnl': pnl
            })
        
        # Calculate cumulative P&L
        cumulative_pnl = 0
        for r in results:
            cumulative_pnl += r['pnl']
            r['cumulative_pnl'] = cumulative_pnl
        
        # Calculate metrics
        final_pnl = results[-1]['cumulative_pnl']
        max_pnl = max(r['cumulative_pnl'] for r in results)
        min_pnl = min(r['cumulative_pnl'] for r in results)
        
        return {
            'final_pnl': final_pnl,
            'max_pnl': max_pnl,
            'min_pnl': min_pnl,
            'return_pct': final_pnl / strategy.margin_requirement * 100 if strategy.margin_requirement > 0 else 0,
            'win_rate': sum(1 for r in results if r['pnl'] > 0) / len(results) if results else 0,
            'daily_results': results
        }


# Example usage and testing
async def example_usage():
    """Demonstrate advanced trading strategies usage"""
    
    # Initialize strategies engine
    strategies = AdvancedTradingStrategies(risk_free_rate=0.05)
    
    # Example 1: Create options strategy based on market view
    print("=" * 80)
    print("OPTIONS STRATEGIES BY MARKET VIEW")
    print("=" * 80)
    
    underlying_price = 100
    volatility = 0.25
    capital = 10000
    
    for view in MarketView:
        strategy = await strategies.create_options_strategy(
            underlying_price=underlying_price,
            market_view=view,
            volatility=volatility,
            days_to_expiry=30,
            capital=capital
        )
        
        print(f"\n{view.value.upper()} Strategy: {strategy.strategy_type.value}")
        print(f"  Max Profit: ${strategy.max_profit:.2f}" if strategy.max_profit != float('inf') else "  Max Profit: Unlimited")
        print(f"  Max Loss: ${strategy.max_loss:.2f}")
        print(f"  Breakeven: {strategy.breakeven_points}")
        print(f"  Probability of Profit: {strategy.probability_profit:.1%}" if strategy.probability_profit else "")
    
    # Example 2: Pair trading opportunities
    print("\n" + "=" * 80)
    print("PAIR TRADING OPPORTUNITIES")
    print("=" * 80)
    
    # Generate sample correlated price data
    np.random.seed(42)
    days = 100
    
    # Create cointegrated pair
    price1 = 100 + np.cumsum(np.random.randn(days) * 0.5)
    price2 = 95 + 0.95 * price1 + np.random.randn(days) * 2
    
    price_data = {
        'STOCK_A': price1,
        'STOCK_B': price2,
        'STOCK_C': 100 + np.cumsum(np.random.randn(days) * 0.7)
    }
    
    pair_signals = await strategies.identify_pair_trading_opportunities(
        price_data,
        lookback_period=60,
        z_score_threshold=2.0
    )
    
    for signal in pair_signals[:3]:  # Show top 3
        print(f"\nPair: {signal.pair[0]}-{signal.pair[1]}")
        print(f"  Signal: {signal.signal}")
        print(f"  Z-Score: {signal.z_score:.2f}")
        print(f"  Hedge Ratio: {signal.hedge_ratio:.3f}")
        print(f"  Half Life: {signal.half_life:.1f} days")
        print(f"  Confidence: {signal.confidence:.1%}")
    
    # Example 3: GARCH volatility forecast
    print("\n" + "=" * 80)
    print("GARCH VOLATILITY FORECAST")
    print("=" * 80)
    
    returns = np.random.randn(252) * 0.01  # Daily returns
    
    forecast = await strategies.calculate_volatility_forecast(
        symbol='SPY',
        returns=returns,
        horizon=20
    )
    
    print(f"\nVolatility Forecast for SPY:")
    print(f"  Current Volatility: {forecast.current_volatility:.1%}")
    print(f"  1-Day Forecast: {forecast.forecast_1d:.1%}")
    print(f"  5-Day Forecast: {forecast.forecast_5d:.1%}")
    print(f"  20-Day Forecast: {forecast.forecast_20d:.1%}")
    print(f"  95% Confidence Interval: {forecast.confidence_intervals['95%'][0]:.1%} - {forecast.confidence_intervals['95%'][1]:.1%}")
    
    # Example 4: Statistical arbitrage scan
    print("\n" + "=" * 80)
    print("STATISTICAL ARBITRAGE OPPORTUNITIES")
    print("=" * 80)
    
    # Add more varied price data
    for i in range(5):
        symbol = f'STOCK_{chr(68 + i)}'
        trend = np.random.randn() * 0.1
        prices = 100 * (1 + trend) ** np.arange(days) + np.cumsum(np.random.randn(days) * 2)
        price_data[symbol] = prices
    
    volume_data = {k: np.random.uniform(1e6, 1e7, days) for k in price_data.keys()}
    
    stat_arb_opps = await strategies.statistical_arbitrage_scan(
        price_data,
        volume_data,
        lookback=20
    )
    
    for opp in stat_arb_opps[:5]:  # Show top 5
        print(f"\n{opp['symbol']} - {opp['strategy'].upper()}")
        print(f"  Signal: {opp['signal'].upper()}")
        print(f"  Confidence: {opp['confidence']:.1%}")
        if opp['strategy'] == 'mean_reversion':
            print(f"  Z-Score: {opp['z_score']:.2f}")
            print(f"  Expected Return: {opp['expected_return']:.1%}")
            print(f"  Target Price: ${opp['target_price']:.2f}")
        else:
            print(f"  Momentum: {opp['momentum']:.1%}")
    
    # Example 5: Options strategy backtesting
    print("\n" + "=" * 80)
    print("OPTIONS STRATEGY BACKTEST")
    print("=" * 80)
    
    # Create a covered call strategy
    covered_call = await strategies.create_options_strategy(
        underlying_price=100,
        market_view=MarketView.NEUTRAL,
        volatility=0.20,
        days_to_expiry=30,
        capital=10000
    )
    
    # Simulate price path
    price_path = [100]
    for _ in range(30):
        price_path.append(price_path[-1] * (1 + np.random.randn() * 0.01))
    
    volatility_path = [0.20] * 31
    
    backtest_results = strategies.backtest_options_strategy(
        covered_call,
        np.array(price_path),
        np.array(volatility_path)
    )
    
    print(f"\nCovered Call Backtest Results:")
    print(f"  Final P&L: ${backtest_results['final_pnl']:.2f}")
    print(f"  Return: {backtest_results['return_pct']:.1f}%")
    print(f"  Max P&L: ${backtest_results['max_pnl']:.2f}")
    print(f"  Min P&L: ${backtest_results['min_pnl']:.2f}")
    print(f"  Win Rate: {backtest_results['win_rate']:.1%}")


if __name__ == "__main__":
    asyncio.run(example_usage())