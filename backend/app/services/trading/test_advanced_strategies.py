"""
Test Suite for Advanced Trading Strategies

Comprehensive tests for options strategies, pair trading, and volatility modeling.
"""

import pytest
import numpy as np
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List

from advanced_strategies import (
    AdvancedTradingStrategies,
    MarketView,
    OptionType,
    StrategyType,
    BlackScholesModel,
    CointegrationAnalyzer,
    GARCHModel
)


class TestBlackScholesModel:
    """Test Black-Scholes option pricing model"""
    
    def test_call_price_at_expiry(self):
        """Test call option pricing at expiration"""
        bs = BlackScholesModel()
        
        # At expiration (T=0), call value = max(S-K, 0)
        S, K, r, sigma = 100, 95, 0.05, 0.2
        price = bs.call_price(S, K, r, sigma, 0)
        assert price == 5.0
        
        # OTM call at expiry
        price = bs.call_price(90, 95, r, sigma, 0)
        assert price == 0.0
    
    def test_put_price_at_expiry(self):
        """Test put option pricing at expiration"""
        bs = BlackScholesModel()
        
        # At expiration (T=0), put value = max(K-S, 0)
        S, K, r, sigma = 90, 95, 0.05, 0.2
        price = bs.put_price(S, K, r, sigma, 0)
        assert price == 5.0
        
        # OTM put at expiry
        price = bs.put_price(100, 95, r, sigma, 0)
        assert price == 0.0
    
    def test_put_call_parity(self):
        """Test put-call parity relationship"""
        bs = BlackScholesModel()
        
        S, K, r, sigma, T = 100, 100, 0.05, 0.2, 0.25
        
        call_price = bs.call_price(S, K, r, sigma, T)
        put_price = bs.put_price(S, K, r, sigma, T)
        
        # Put-Call Parity: C - P = S - K*exp(-r*T)
        lhs = call_price - put_price
        rhs = S - K * np.exp(-r * T)
        
        assert abs(lhs - rhs) < 0.01  # Small tolerance for numerical errors
    
    def test_greeks_calculation(self):
        """Test Greeks calculation"""
        bs = BlackScholesModel()
        
        S, K, r, sigma, T = 100, 100, 0.05, 0.2, 0.25
        
        call_greeks = bs.calculate_greeks(S, K, r, sigma, T, OptionType.CALL)
        
        # Delta should be between 0 and 1 for calls
        assert 0 <= call_greeks['delta'] <= 1
        
        # Gamma should be positive
        assert call_greeks['gamma'] >= 0
        
        # Theta should typically be negative (time decay)
        assert call_greeks['theta'] < 0
        
        # Vega should be positive
        assert call_greeks['vega'] > 0
    
    def test_implied_volatility(self):
        """Test implied volatility calculation"""
        bs = BlackScholesModel()
        
        S, K, r, T = 100, 100, 0.05, 0.25
        true_sigma = 0.3
        
        # Calculate option price with known volatility
        option_price = bs.call_price(S, K, r, true_sigma, T)
        
        # Back out implied volatility
        iv = bs.implied_volatility(option_price, S, K, r, T, OptionType.CALL)
        
        # Should recover the original volatility
        assert abs(iv - true_sigma) < 0.01


class TestCointegrationAnalyzer:
    """Test cointegration analysis for pair trading"""
    
    def test_cointegration_detection(self):
        """Test detection of cointegrated pairs"""
        analyzer = CointegrationAnalyzer()
        
        # Create synthetic cointegrated pair
        np.random.seed(42)
        n = 100
        
        # Generate cointegrated series
        x = np.cumsum(np.random.randn(n))
        y = x + np.random.randn(n) * 0.5  # y follows x with noise
        
        result = analyzer.test_cointegration(y, x)
        
        # Should detect cointegration
        assert result['cointegrated'] == True
        assert result['pvalue'] < 0.05
        assert result['hedge_ratio'] > 0  # Should be close to 1
    
    def test_z_score_calculation(self):
        """Test z-score calculation for spread"""
        analyzer = CointegrationAnalyzer()
        
        # Create spread with known properties
        spread = np.array([0, 1, -1, 2, -2, 0, 1, -1, 3, -3])
        
        z_score = analyzer.calculate_z_score(spread, lookback=5)
        
        # Z-score should be calculated correctly
        recent_mean = np.mean(spread[-5:])
        recent_std = np.std(spread[-5:])
        expected_z = (spread[-1] - recent_mean) / recent_std
        
        assert abs(z_score - expected_z) < 0.01
    
    def test_half_life_calculation(self):
        """Test half-life of mean reversion calculation"""
        analyzer = CointegrationAnalyzer()
        
        # Create mean-reverting series
        np.random.seed(42)
        n = 200
        prices1 = np.cumsum(np.random.randn(n))
        prices2 = prices1 + np.sin(np.linspace(0, 4*np.pi, n)) * 2
        
        result = analyzer.test_cointegration(prices1, prices2)
        
        # Should have finite half-life
        assert 0 < result['half_life'] < np.inf


class TestGARCHModel:
    """Test GARCH volatility modeling"""
    
    def test_garch_initialization(self):
        """Test GARCH model initialization"""
        garch = GARCHModel(omega=0.00001, alpha=0.1, beta=0.85)
        
        # Check stationarity condition
        assert garch.alpha + garch.beta < 1
    
    def test_garch_fitting(self):
        """Test GARCH model fitting"""
        np.random.seed(42)
        
        # Generate returns with volatility clustering
        n = 500
        returns = np.random.randn(n) * 0.01
        
        # Add volatility clustering
        for i in range(100, 150):
            returns[i] *= 3  # High volatility period
        
        garch = GARCHModel()
        garch.fit(returns)
        
        # Parameters should be updated
        assert garch.omega > 0
        assert 0 < garch.alpha < 1
        assert 0 < garch.beta < 1
    
    def test_volatility_forecast(self):
        """Test volatility forecasting"""
        np.random.seed(42)
        returns = np.random.randn(252) * 0.01
        
        garch = GARCHModel()
        forecast = garch.forecast(returns, horizon=20)
        
        # Check forecast structure
        assert forecast.current_volatility > 0
        assert forecast.forecast_1d > 0
        assert forecast.forecast_5d > 0
        assert forecast.forecast_20d > 0
        assert len(forecast.volatility_term_structure) == 20
        
        # Confidence intervals should be reasonable
        assert forecast.confidence_intervals['95%'][0] < forecast.current_volatility
        assert forecast.confidence_intervals['95%'][1] > forecast.current_volatility


class TestAdvancedTradingStrategies:
    """Test main trading strategies class"""
    
    @pytest.mark.asyncio
    async def test_covered_call_creation(self):
        """Test covered call strategy creation"""
        strategies = AdvancedTradingStrategies()
        
        strategy = await strategies.create_options_strategy(
            underlying_price=100,
            market_view=MarketView.NEUTRAL,
            volatility=0.20,
            days_to_expiry=30,
            capital=10000
        )
        
        assert strategy.strategy_type == StrategyType.COVERED_CALL
        assert len(strategy.legs) >= 2  # Stock + short call
        assert strategy.max_profit > 0
        assert strategy.max_loss > 0
        assert len(strategy.breakeven_points) > 0
    
    @pytest.mark.asyncio
    async def test_bull_call_spread(self):
        """Test bull call spread creation"""
        strategies = AdvancedTradingStrategies()
        
        strategy = await strategies.create_options_strategy(
            underlying_price=100,
            market_view=MarketView.BULLISH,
            volatility=0.25,
            days_to_expiry=30,
            capital=5000
        )
        
        assert strategy.strategy_type == StrategyType.BULL_CALL_SPREAD
        assert len(strategy.legs) == 2  # Long call + short call
        assert strategy.max_profit > strategy.max_loss  # Limited risk/reward
    
    @pytest.mark.asyncio
    async def test_iron_condor(self):
        """Test iron condor strategy for neutral market"""
        strategies = AdvancedTradingStrategies()
        
        strategy = await strategies.create_options_strategy(
            underlying_price=100,
            market_view=MarketView.NEUTRAL,
            volatility=0.15,
            days_to_expiry=45,
            capital=10000
        )
        
        # Could be iron condor or covered call for neutral view
        assert strategy.strategy_type in [StrategyType.IRON_CONDOR, StrategyType.COVERED_CALL]
        
        if strategy.strategy_type == StrategyType.IRON_CONDOR:
            assert len(strategy.legs) == 4  # 4 options legs
            assert len(strategy.breakeven_points) == 2  # Upper and lower breakeven
            assert strategy.probability_profit is not None
    
    @pytest.mark.asyncio
    async def test_long_straddle(self):
        """Test long straddle for high volatility"""
        strategies = AdvancedTradingStrategies()
        
        strategy = await strategies.create_options_strategy(
            underlying_price=100,
            market_view=MarketView.VOLATILE,
            volatility=0.40,
            days_to_expiry=30,
            capital=8000
        )
        
        assert strategy.strategy_type == StrategyType.LONG_STRADDLE
        assert len(strategy.legs) == 2  # Long call + long put
        assert strategy.max_profit == float('inf')  # Unlimited upside
        assert len(strategy.breakeven_points) == 2  # Upper and lower breakeven
    
    @pytest.mark.asyncio
    async def test_pair_trading_identification(self):
        """Test pair trading opportunity identification"""
        strategies = AdvancedTradingStrategies()
        
        # Create synthetic cointegrated pairs
        np.random.seed(42)
        n = 100
        
        # Cointegrated pair
        price1 = 100 + np.cumsum(np.random.randn(n) * 0.5)
        price2 = 95 + 0.95 * price1 + np.random.randn(n) * 2
        
        # Add spread deviation
        price2[-10:] += 5  # Create trading opportunity
        
        price_data = {
            'STOCK_A': price1,
            'STOCK_B': price2,
            'STOCK_C': 100 + np.cumsum(np.random.randn(n) * 0.7)  # Unrelated stock
        }
        
        signals = await strategies.identify_pair_trading_opportunities(
            price_data,
            lookback_period=60,
            z_score_threshold=2.0
        )
        
        # Should identify the cointegrated pair
        assert len(signals) > 0
        
        # Check signal properties
        for signal in signals:
            assert signal.z_score != 0
            assert signal.hedge_ratio > 0
            assert signal.signal in ["long_spread", "short_spread", "neutral"]
            assert 0 <= signal.confidence <= 1
    
    @pytest.mark.asyncio
    async def test_volatility_forecast(self):
        """Test GARCH volatility forecasting"""
        strategies = AdvancedTradingStrategies()
        
        # Generate sample returns
        np.random.seed(42)
        returns = np.random.randn(252) * 0.01
        
        forecast = await strategies.calculate_volatility_forecast(
            symbol='TEST',
            returns=returns,
            horizon=20
        )
        
        # Check forecast validity
        assert forecast.current_volatility > 0
        assert forecast.forecast_1d > 0
        assert len(forecast.volatility_term_structure) == 20
        assert all(v > 0 for v in forecast.volatility_term_structure)
    
    @pytest.mark.asyncio
    async def test_statistical_arbitrage_scan(self):
        """Test statistical arbitrage opportunity scanning"""
        strategies = AdvancedTradingStrategies()
        
        # Create price data with opportunities
        np.random.seed(42)
        n = 50
        
        price_data = {}
        volume_data = {}
        
        # Mean reverting stock
        prices = [100]
        for _ in range(n-1):
            change = np.random.randn() * 2
            if prices[-1] > 105:
                change -= 1  # Mean revert down
            elif prices[-1] < 95:
                change += 1  # Mean revert up
            prices.append(prices[-1] + change)
        
        price_data['MEAN_REVERT'] = np.array(prices)
        volume_data['MEAN_REVERT'] = np.random.uniform(1e6, 2e6, n)
        
        # Trending stock
        trend = 100 * (1.001 ** np.arange(n)) + np.random.randn(n) * 0.5
        price_data['TREND'] = trend
        volume_data['TREND'] = np.random.uniform(1e6, 2e6, n)
        
        opportunities = await strategies.statistical_arbitrage_scan(
            price_data,
            volume_data,
            lookback=20
        )
        
        # Should find opportunities
        assert len(opportunities) > 0
        
        # Check opportunity structure
        for opp in opportunities:
            assert opp['symbol'] in price_data
            assert opp['strategy'] in ['mean_reversion', 'momentum']
            assert opp['signal'] in ['buy', 'sell']
            assert 0 <= opp['confidence'] <= 1
    
    @pytest.mark.asyncio
    async def test_option_implied_move(self):
        """Test calculation of implied move from option IVs"""
        strategies = AdvancedTradingStrategies()
        
        # Test with known IVs
        atm_call_iv = 0.20  # 20% IV
        atm_put_iv = 0.22   # 22% IV
        days_to_expiry = 7
        
        implied_move = strategies.calculate_option_implied_move(
            atm_call_iv,
            atm_put_iv,
            days_to_expiry
        )
        
        # Check calculations
        avg_iv = (atm_call_iv + atm_put_iv) / 2
        time_factor = np.sqrt(days_to_expiry / 365)
        expected_1sd = avg_iv * time_factor
        
        assert abs(implied_move['expected_move_1sd'] - expected_1sd) < 0.001
        assert implied_move['expected_move_2sd'] == expected_1sd * 2
        assert implied_move['probability_within_1sd'] == 0.68
        assert implied_move['probability_within_2sd'] == 0.95
    
    @pytest.mark.asyncio
    async def test_strategy_backtesting(self):
        """Test options strategy backtesting"""
        strategies = AdvancedTradingStrategies()
        
        # Create a simple strategy
        strategy = await strategies.create_options_strategy(
            underlying_price=100,
            market_view=MarketView.BULLISH,
            volatility=0.20,
            days_to_expiry=30,
            capital=5000
        )
        
        # Generate price path
        np.random.seed(42)
        price_path = [100]
        for _ in range(30):
            price_path.append(price_path[-1] * (1 + np.random.randn() * 0.01))
        
        volatility_path = [0.20] * 31
        
        backtest = strategies.backtest_options_strategy(
            strategy,
            np.array(price_path),
            np.array(volatility_path)
        )
        
        # Check backtest results
        assert 'final_pnl' in backtest
        assert 'max_pnl' in backtest
        assert 'min_pnl' in backtest
        assert 'return_pct' in backtest
        assert 'win_rate' in backtest
        assert len(backtest['daily_results']) == 31


class TestIntegration:
    """Integration tests for complete workflows"""
    
    @pytest.mark.asyncio
    async def test_market_neutral_portfolio(self):
        """Test creation of market neutral portfolio with pairs"""
        strategies = AdvancedTradingStrategies()
        
        # Create price data with multiple cointegrated pairs
        np.random.seed(42)
        n = 100
        
        # Technology pair
        tech1 = 100 + np.cumsum(np.random.randn(n) * 0.8)
        tech2 = 95 + 0.98 * tech1 + np.random.randn(n) * 1.5
        
        # Finance pair
        fin1 = 80 + np.cumsum(np.random.randn(n) * 0.6)
        fin2 = 82 + 1.02 * fin1 + np.random.randn(n) * 1.2
        
        price_data = {
            'TECH_A': tech1,
            'TECH_B': tech2,
            'FIN_A': fin1,
            'FIN_B': fin2
        }
        
        # Find pair trading opportunities
        signals = await strategies.identify_pair_trading_opportunities(
            price_data,
            lookback_period=60,
            z_score_threshold=1.5
        )
        
        # Should find opportunities
        assert len(signals) > 0
        
        # Verify hedge ratios for market neutrality
        for signal in signals:
            # Position sizes should be balanced by hedge ratio
            if signal.signal == "long_spread":
                # Long pair[0], short pair[1] with hedge ratio
                assert signal.hedge_ratio > 0
    
    @pytest.mark.asyncio
    async def test_volatility_arbitrage_workflow(self):
        """Test complete volatility arbitrage workflow"""
        strategies = AdvancedTradingStrategies()
        
        # Historical returns for volatility modeling
        np.random.seed(42)
        returns = np.random.randn(252) * 0.01
        
        # Add volatility regime change
        returns[100:120] *= 3  # High vol period
        
        # Forecast volatility
        forecast = await strategies.calculate_volatility_forecast(
            symbol='VOL_ARB',
            returns=returns,
            horizon=20
        )
        
        # Current implied volatility from options
        implied_vol = 0.25
        
        # If forecast < implied, sell volatility (sell straddle)
        # If forecast > implied, buy volatility (buy straddle)
        if forecast.forecast_5d < implied_vol:
            strategy = await strategies.create_options_strategy(
                underlying_price=100,
                market_view=MarketView.RANGE_BOUND,  # Sell volatility
                volatility=implied_vol,
                days_to_expiry=5,
                capital=10000
            )
        else:
            strategy = await strategies.create_options_strategy(
                underlying_price=100,
                market_view=MarketView.VOLATILE,  # Buy volatility
                volatility=implied_vol,
                days_to_expiry=5,
                capital=10000
            )
        
        assert strategy is not None
        assert strategy.strategy_type in [
            StrategyType.IRON_CONDOR,
            StrategyType.BUTTERFLY_SPREAD,
            StrategyType.LONG_STRADDLE,
            StrategyType.COVERED_CALL
        ]


@pytest.mark.asyncio
async def test_performance_benchmark():
    """Benchmark performance of strategy calculations"""
    import time
    
    strategies = AdvancedTradingStrategies()
    
    # Generate large dataset
    n_symbols = 50
    n_days = 252
    
    price_data = {}
    for i in range(n_symbols):
        prices = 100 + np.cumsum(np.random.randn(n_days) * 0.5)
        price_data[f'STOCK_{i}'] = prices
    
    # Benchmark pair trading analysis
    start = time.time()
    
    signals = await strategies.identify_pair_trading_opportunities(
        price_data,
        lookback_period=60,
        z_score_threshold=2.0
    )
    
    elapsed = time.time() - start
    
    print(f"\nPair trading analysis for {n_symbols} symbols: {elapsed:.2f} seconds")
    print(f"Found {len(signals)} opportunities")
    
    # Should complete in reasonable time
    assert elapsed < 10  # 10 seconds for 50 symbols
    
    # Test options strategy creation speed
    start = time.time()
    
    strategies_created = []
    for view in MarketView:
        strategy = await strategies.create_options_strategy(
            underlying_price=100,
            market_view=view,
            volatility=0.25,
            days_to_expiry=30,
            capital=10000
        )
        strategies_created.append(strategy)
    
    elapsed = time.time() - start
    
    print(f"Options strategy creation for {len(MarketView)} views: {elapsed:.2f} seconds")
    
    assert elapsed < 1  # Should be very fast


if __name__ == "__main__":
    # Run integration test
    asyncio.run(test_performance_benchmark())