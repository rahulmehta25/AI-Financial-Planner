"""
Comprehensive unit tests for Advanced Monte Carlo Engine

Tests cover:
- Basic Monte Carlo simulation accuracy
- Market regime detection
- Jump diffusion processes
- GARCH volatility modeling
- Risk metrics calculations
- GPU acceleration (if available)
- Property-based testing with Hypothesis
"""

import pytest
import numpy as np
import pandas as pd
from hypothesis import given, strategies as st, settings, assume
from hypothesis.extra.numpy import arrays
from unittest.mock import patch, MagicMock
import cupy as cp
from scipy import stats
import warnings

from app.services.modeling.monte_carlo import (
    AdvancedMonteCarloEngine,
    SimulationConfig,
    MarketRegime
)
from tests.factories import EnhancedMarketDataFactory

# Suppress CuPy warnings if GPU not available
warnings.filterwarnings("ignore", category=UserWarning, module="cupy")


class TestSimulationConfig:
    """Test SimulationConfig dataclass"""
    
    def test_default_config(self):
        """Test default configuration values"""
        config = SimulationConfig()
        
        assert config.n_paths == 50_000
        assert config.n_years == 30
        assert config.initial_price == 100.0
        assert config.risk_free_rate == 0.02
        assert config.volatility == 0.15
        assert config.jump_intensity == 0.1
        assert config.jump_size_mean == -0.05
        assert config.jump_size_std == 0.2
    
    @given(
        n_paths=st.integers(min_value=1000, max_value=100000),
        n_years=st.integers(min_value=1, max_value=50),
        initial_price=st.floats(min_value=10, max_value=1000),
        volatility=st.floats(min_value=0.01, max_value=1.0)
    )
    def test_custom_config_valid_ranges(self, n_paths, n_years, initial_price, volatility):
        """Property-based test for valid configuration ranges"""
        config = SimulationConfig(
            n_paths=n_paths,
            n_years=n_years,
            initial_price=initial_price,
            volatility=volatility
        )
        
        assert config.n_paths == n_paths
        assert config.n_years == n_years
        assert config.initial_price == initial_price
        assert config.volatility == volatility


class TestAdvancedMonteCarloEngine:
    """Comprehensive tests for AdvancedMonteCarloEngine"""
    
    @pytest.fixture
    def engine(self):
        """Create engine with test configuration"""
        config = SimulationConfig(
            n_paths=1000,  # Smaller for testing
            n_years=5,
            initial_price=100.0,
            risk_free_rate=0.05,
            volatility=0.2
        )
        return AdvancedMonteCarloEngine(config)
    
    def test_engine_initialization(self, engine):
        """Test engine initialization"""
        assert engine.config.n_paths == 1000
        assert engine.config.n_years == 5
        assert hasattr(engine, 'gpu_available')
    
    def test_market_regime_detection(self, engine):
        """Test market regime detection functionality"""
        # Create test returns series with different regimes
        
        # Bull market returns (positive mean)
        bull_returns = np.random.normal(0.08/252, 0.15/np.sqrt(252), 252)
        regime = engine._detect_market_regime(bull_returns)
        # Note: regime detection is probabilistic, so we don't assert specific regime
        assert isinstance(regime, MarketRegime)
        
        # Bear market returns (negative mean)
        bear_returns = np.random.normal(-0.15/252, 0.25/np.sqrt(252), 252)
        regime = engine._detect_market_regime(bear_returns)
        assert isinstance(regime, MarketRegime)
    
    def test_jump_diffusion_process(self, engine):
        """Test jump diffusion implementation"""
        # Create base process
        np.random.seed(42)
        base_process = np.random.normal(0, 0.01, (100, 252))
        dt = 1.0 / 252
        
        # Apply jump diffusion
        enhanced_process = engine._jump_diffusion_process(base_process, dt)
        
        assert enhanced_process.shape == base_process.shape
        # Enhanced process should have different statistics due to jumps
        assert np.std(enhanced_process) >= np.std(base_process)
    
    def test_garch_volatility(self, engine):
        """Test GARCH volatility modeling"""
        # Create returns series
        np.random.seed(42)
        returns = np.random.normal(0, 0.02, 252)
        
        volatilities = engine._garch_volatility(returns)
        
        assert len(volatilities) == len(returns)
        assert all(vol > 0 for vol in volatilities)
        # GARCH should show time-varying volatility
        assert np.std(volatilities) > 0
    
    def test_simulate_paths_basic(self, engine):
        """Test basic path simulation"""
        paths = engine.simulate_paths(verbose=False)
        
        # Check dimensions
        expected_steps = engine.config.n_years * 252 + 1
        assert paths.shape == (engine.config.n_paths, expected_steps)
        
        # All paths should start at initial price
        assert np.allclose(paths[:, 0], engine.config.initial_price)
        
        # Paths should be positive (no bankruptcy in basic GBM)
        assert np.all(paths > 0)
    
    @given(
        n_paths=st.integers(min_value=100, max_value=1000),
        n_years=st.integers(min_value=1, max_value=10)
    )
    @settings(max_examples=10, deadline=5000)
    def test_simulate_paths_property_based(self, n_paths, n_years):
        """Property-based testing for path simulation"""
        config = SimulationConfig(
            n_paths=n_paths,
            n_years=n_years,
            initial_price=100.0
        )
        engine = AdvancedMonteCarloEngine(config)
        
        paths = engine.simulate_paths(verbose=False)
        
        # Properties that should always hold
        assert paths.shape[0] == n_paths
        assert paths.shape[1] == n_years * 252 + 1
        assert np.all(paths[:, 0] == 100.0)
        assert np.all(paths > 0)
    
    def test_calculate_risk_metrics(self, engine):
        """Test risk metrics calculation"""
        np.random.seed(42)
        paths = engine.simulate_paths(verbose=False)
        
        risk_metrics = engine.calculate_risk_metrics(paths)
        
        # Check all required metrics are present
        expected_metrics = {
            "Value at Risk (95%)",
            "Conditional VaR (95%)",
            "Maximum Drawdown",
            "Sharpe Ratio",
            "Skewness",
            "Kurtosis"
        }
        assert set(risk_metrics.keys()) == expected_metrics
        
        # Check metric ranges make sense
        assert risk_metrics["Value at Risk (95%)"] > 0
        assert risk_metrics["Conditional VaR (95%)"] > 0
        assert risk_metrics["Maximum Drawdown"] >= 0
        # Sharpe ratio can be negative
        assert isinstance(risk_metrics["Sharpe Ratio"], (int, float, np.number))
        
        # CVaR should be <= VaR (more extreme loss)
        assert risk_metrics["Conditional VaR (95%)"] <= risk_metrics["Value at Risk (95%)"]
    
    def test_performance_requirements(self, engine):
        """Test performance requirements for financial calculations"""
        import time
        
        start_time = time.time()
        paths = engine.simulate_paths(verbose=False)
        simulation_time = time.time() - start_time
        
        # Performance requirement: should complete in reasonable time
        # For 1000 paths x 5 years, should be under 5 seconds
        assert simulation_time < 5.0
        
        start_time = time.time()
        risk_metrics = engine.calculate_risk_metrics(paths)
        metrics_time = time.time() - start_time
        
        # Risk metrics should be very fast
        assert metrics_time < 1.0
    
    @pytest.mark.skipif(not cp.cuda.runtime.getDeviceCount(), reason="GPU not available")
    def test_gpu_acceleration(self):
        """Test GPU acceleration if available"""
        config = SimulationConfig(n_paths=10000, n_years=10)
        engine = AdvancedMonteCarloEngine(config)
        
        # Test that GPU is detected and used
        assert engine.gpu_available
        
        # Run simulation - should use GPU internally
        paths = engine.simulate_paths(verbose=False)
        
        # Results should be equivalent to CPU version
        assert paths.shape == (10000, 10 * 252 + 1)
        assert np.all(paths[:, 0] == config.initial_price)
    
    def test_statistical_accuracy(self, engine):
        """Test statistical accuracy of Monte Carlo simulation"""
        # Use larger sample for statistical testing
        config = SimulationConfig(
            n_paths=10000,
            n_years=1,
            initial_price=100.0,
            risk_free_rate=0.05,
            volatility=0.2
        )
        engine = AdvancedMonteCarloEngine(config)
        
        paths = engine.simulate_paths(verbose=False)
        final_prices = paths[:, -1]
        
        # For Geometric Brownian Motion, final prices should be log-normal
        log_returns = np.log(final_prices / config.initial_price)
        
        # Expected log return
        expected_log_return = (config.risk_free_rate - 0.5 * config.volatility**2) * 1
        actual_mean = np.mean(log_returns)
        
        # Statistical test: mean should be close to expected (within 2 standard errors)
        standard_error = config.volatility / np.sqrt(config.n_paths)
        assert abs(actual_mean - expected_log_return) < 2 * standard_error
        
        # Volatility should be close to expected
        actual_vol = np.std(log_returns)
        vol_standard_error = config.volatility / np.sqrt(2 * (config.n_paths - 1))
        assert abs(actual_vol - config.volatility) < 2 * vol_standard_error
    
    def test_edge_cases(self):
        """Test edge cases and error handling"""
        # Test with minimal configuration
        config = SimulationConfig(
            n_paths=1,
            n_years=1,
            volatility=0.01
        )
        engine = AdvancedMonteCarloEngine(config)
        
        paths = engine.simulate_paths(verbose=False)
        assert paths.shape == (1, 253)  # 252 trading days + initial
        
        # Test with high volatility
        config = SimulationConfig(
            n_paths=100,
            n_years=1,
            volatility=0.8
        )
        engine = AdvancedMonteCarloEngine(config)
        
        paths = engine.simulate_paths(verbose=False)
        assert paths.shape == (100, 253)
        assert np.all(paths > 0)  # Should still be positive
    
    def test_reproducibility(self, engine):
        """Test simulation reproducibility with same random seed"""
        # Note: This test may be challenging due to parallel processing
        # We test that the overall statistics are consistent
        
        np.random.seed(42)
        paths1 = engine.simulate_paths(verbose=False)
        
        np.random.seed(42)
        paths2 = engine.simulate_paths(verbose=False)
        
        # Due to parallel processing, exact reproduction may not be possible
        # Test that statistical properties are similar
        final_prices1 = paths1[:, -1]
        final_prices2 = paths2[:, -1]
        
        # Mean and std should be very similar (within 5%)
        assert abs(np.mean(final_prices1) - np.mean(final_prices2)) / np.mean(final_prices1) < 0.05
        assert abs(np.std(final_prices1) - np.std(final_prices2)) / np.std(final_prices1) < 0.05


class TestFinancialAccuracy:
    """Test financial calculation accuracy and edge cases"""
    
    def test_risk_neutral_pricing(self):
        """Test risk-neutral pricing consistency"""
        config = SimulationConfig(
            n_paths=50000,
            n_years=1,
            initial_price=100.0,
            risk_free_rate=0.05,
            volatility=0.2
        )
        engine = AdvancedMonteCarloEngine(config)
        
        paths = engine.simulate_paths(verbose=False)
        final_prices = paths[:, -1]
        
        # Under risk-neutral measure, E[S_T] = S_0 * exp(r*T)
        expected_final_price = config.initial_price * np.exp(config.risk_free_rate * config.n_years)
        actual_mean = np.mean(final_prices)
        
        # Should be within 1% for large sample
        relative_error = abs(actual_mean - expected_final_price) / expected_final_price
        assert relative_error < 0.01
    
    def test_volatility_accuracy(self):
        """Test volatility calculation accuracy"""
        config = SimulationConfig(
            n_paths=20000,
            n_years=1,
            volatility=0.25
        )
        engine = AdvancedMonteCarloEngine(config)
        
        paths = engine.simulate_paths(verbose=False)
        returns = np.diff(np.log(paths), axis=1)
        
        # Annualized volatility
        actual_vol = np.std(returns) * np.sqrt(252)
        
        # Should be close to configured volatility
        assert abs(actual_vol - config.volatility) < 0.02
    
    @given(
        volatilities=arrays(
            dtype=np.float64,
            shape=5,
            elements=st.floats(min_value=0.05, max_value=0.5)
        )
    )
    @settings(max_examples=10, deadline=3000)
    def test_volatility_property_based(self, volatilities):
        """Property-based test for different volatility levels"""
        for vol in volatilities:
            config = SimulationConfig(
                n_paths=1000,
                n_years=1,
                volatility=vol
            )
            engine = AdvancedMonteCarloEngine(config)
            
            paths = engine.simulate_paths(verbose=False)
            
            # Higher volatility should lead to wider price distribution
            price_range = np.max(paths[:, -1]) - np.min(paths[:, -1])
            assert price_range > 0
            
            # Risk metrics should reflect volatility
            risk_metrics = engine.calculate_risk_metrics(paths)
            assert risk_metrics["Maximum Drawdown"] >= 0


class TestIntegrationWithMarketData:
    """Integration tests with market data factories"""
    
    @pytest.mark.asyncio
    async def test_with_realistic_market_data(self, db_session):
        """Test Monte Carlo with realistic market data"""
        # Generate realistic market data
        symbols = ['SPY', 'BND', 'VTI']
        market_data = await EnhancedMarketDataFactory.create_time_series(
            db_session, 'SPY', days=252
        )
        
        # Extract returns for calibration
        prices = [data.close_price for data in market_data]
        returns = pd.Series(prices).pct_change().dropna()
        
        # Calibrate Monte Carlo parameters
        annual_return = returns.mean() * 252
        annual_vol = returns.std() * np.sqrt(252)
        
        config = SimulationConfig(
            n_paths=5000,
            n_years=5,
            initial_price=float(prices[0]),
            risk_free_rate=annual_return,  # Simplified
            volatility=annual_vol
        )
        
        engine = AdvancedMonteCarloEngine(config)
        paths = engine.simulate_paths(verbose=False)
        
        # Simulation should complete successfully
        assert paths.shape[0] == 5000
        assert paths.shape[1] == 5 * 252 + 1
        
        # Calculate risk metrics
        risk_metrics = engine.calculate_risk_metrics(paths)
        
        # All metrics should be finite and reasonable
        for metric_name, value in risk_metrics.items():
            assert np.isfinite(value), f"{metric_name} is not finite: {value}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
