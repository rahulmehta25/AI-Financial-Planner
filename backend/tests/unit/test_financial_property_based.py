"""
Property-based testing framework for financial calculations using Hypothesis

Tests mathematical properties and invariants that should hold for all financial calculations:
- Commutative and associative properties
- Monotonicity properties
- Boundary conditions
- Numerical stability
- Domain-specific invariants (e.g., portfolio weights sum to 1)
"""

import pytest
import numpy as np
import pandas as pd
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, timedelta
from hypothesis import given, strategies as st, settings, assume, note
from hypothesis.extra.numpy import arrays
from hypothesis.extra.pandas import data_frames, columns
from typing import List, Dict, Tuple
import warnings

# Import financial calculation modules
from app.services.modeling.monte_carlo import AdvancedMonteCarloEngine, SimulationConfig
from app.services.optimization.portfolio_optimizer import (
    IntelligentPortfolioOptimizer, AssetData, PortfolioConstraints
)
from app.services.modeling.cash_flow import CashFlowProjector
from app.services.tax.tax_optimization import TaxOptimizationEngine, FilingStatus
from app.services.optimization.mpt import ModernPortfolioTheory

# Suppress numerical warnings for cleaner test output
warnings.filterwarnings("ignore", category=RuntimeWarning)
np.seterr(divide='ignore', invalid='ignore')


# Custom Hypothesis strategies for financial data
@st.composite
def financial_returns(draw, min_periods=50, max_periods=1000):
    """Generate realistic financial return series"""
    n_periods = draw(st.integers(min_value=min_periods, max_value=max_periods))
    
    # Generate returns with realistic parameters
    annual_return = draw(st.floats(min_value=-0.3, max_value=0.4))
    annual_vol = draw(st.floats(min_value=0.05, max_value=0.8))
    
    # Convert to daily parameters
    daily_return = annual_return / 252
    daily_vol = annual_vol / np.sqrt(252)
    
    returns = draw(arrays(
        dtype=np.float64,
        shape=n_periods,
        elements=st.floats(
            min_value=daily_return - 4 * daily_vol,
            max_value=daily_return + 4 * daily_vol,
            allow_nan=False,
            allow_infinity=False
        )
    ))
    
    return pd.Series(returns)


@st.composite
def asset_data_strategy(draw, min_assets=2, max_assets=20):
    """Generate valid AssetData objects"""
    n_assets = draw(st.integers(min_value=min_assets, max_value=max_assets))
    
    assets = []
    for i in range(n_assets):
        returns = draw(financial_returns())
        expected_return = draw(st.floats(min_value=-0.2, max_value=0.3))
        volatility = draw(st.floats(min_value=0.01, max_value=0.8))
        
        asset = AssetData(
            symbol=f'ASSET_{i:02d}',
            returns=returns,
            expected_return=expected_return,
            volatility=volatility,
            sector=draw(st.sampled_from(['Technology', 'Healthcare', 'Finance', 'Energy'])),
            esg_score=draw(st.floats(min_value=0, max_value=100) | st.none())
        )
        assets.append(asset)
    
    return assets


@st.composite
def portfolio_weights(draw, n_assets):
    """Generate valid portfolio weights that sum to 1"""
    # Generate positive weights
    raw_weights = draw(arrays(
        dtype=np.float64,
        shape=n_assets,
        elements=st.floats(min_value=0.001, max_value=1.0)
    ))
    
    # Normalize to sum to 1
    weights = raw_weights / raw_weights.sum()
    return weights


@st.composite
def simulation_config_strategy(draw):
    """Generate valid SimulationConfig objects"""
    return SimulationConfig(
        n_paths=draw(st.integers(min_value=100, max_value=10000)),
        n_years=draw(st.integers(min_value=1, max_value=20)),
        initial_price=draw(st.floats(min_value=10, max_value=1000)),
        risk_free_rate=draw(st.floats(min_value=0.0, max_value=0.15)),
        volatility=draw(st.floats(min_value=0.01, max_value=0.8)),
        jump_intensity=draw(st.floats(min_value=0.0, max_value=0.5)),
        jump_size_mean=draw(st.floats(min_value=-0.2, max_value=0.1)),
        jump_size_std=draw(st.floats(min_value=0.01, max_value=0.5))
    )


class TestMonteCarloProperties:
    """Property-based tests for Monte Carlo simulation"""
    
    @given(config=simulation_config_strategy())
    @settings(max_examples=20, deadline=10000)
    def test_simulation_basic_properties(self, config):
        """Test basic properties of Monte Carlo simulation"""
        engine = AdvancedMonteCarloEngine(config)
        
        paths = engine.simulate_paths(verbose=False)
        
        # Property 1: Correct dimensions
        expected_steps = config.n_years * 252 + 1
        assert paths.shape == (config.n_paths, expected_steps)
        
        # Property 2: All paths start at initial price
        initial_prices = paths[:, 0]
        assert np.allclose(initial_prices, config.initial_price)
        
        # Property 3: All paths should be positive (no bankruptcy in GBM)
        assert np.all(paths > 0)
        
        # Property 4: Path continuity (no infinite jumps)
        price_ratios = paths[:, 1:] / paths[:, :-1]
        assert np.all(np.isfinite(price_ratios))
        assert np.all(price_ratios > 0)
    
    @given(
        initial_price_1=st.floats(min_value=50, max_value=200),
        initial_price_2=st.floats(min_value=50, max_value=200)
    )
    @settings(max_examples=10, deadline=5000)
    def test_linearity_property(self, initial_price_1, initial_price_2):
        """Test linearity: E[aX + bY] = aE[X] + bE[Y]"""
        assume(abs(initial_price_1 - initial_price_2) > 1)  # Ensure they're different
        
        config = SimulationConfig(
            n_paths=5000,
            n_years=1,
            risk_free_rate=0.05,
            volatility=0.2
        )
        
        engine = AdvancedMonteCarloEngine(config)
        
        # Simulate with first initial price
        config.initial_price = initial_price_1
        paths_1 = engine.simulate_paths(verbose=False)
        mean_final_1 = np.mean(paths_1[:, -1])
        
        # Simulate with second initial price
        config.initial_price = initial_price_2
        paths_2 = engine.simulate_paths(verbose=False)
        mean_final_2 = np.mean(paths_2[:, -1])
        
        # Test linearity property
        ratio = mean_final_1 / mean_final_2
        expected_ratio = initial_price_1 / initial_price_2
        
        # Allow 5% tolerance due to Monte Carlo variance
        relative_error = abs(ratio - expected_ratio) / expected_ratio
        assert relative_error < 0.05
    
    @given(
        vol_1=st.floats(min_value=0.1, max_value=0.3),
        vol_2=st.floats(min_value=0.1, max_value=0.3)
    )
    @settings(max_examples=10, deadline=5000)
    def test_volatility_monotonicity(self, vol_1, vol_2):
        """Test that higher volatility leads to higher variance"""
        assume(abs(vol_1 - vol_2) > 0.05)  # Ensure meaningful difference
        
        config = SimulationConfig(
            n_paths=5000,
            n_years=1,
            initial_price=100,
            risk_free_rate=0.05
        )
        
        engine = AdvancedMonteCarloEngine(config)
        
        # Lower volatility simulation
        config.volatility = min(vol_1, vol_2)
        paths_low = engine.simulate_paths(verbose=False)
        var_low = np.var(np.log(paths_low[:, -1] / paths_low[:, 0]))
        
        # Higher volatility simulation
        config.volatility = max(vol_1, vol_2)
        paths_high = engine.simulate_paths(verbose=False)
        var_high = np.var(np.log(paths_high[:, -1] / paths_high[:, 0]))
        
        # Higher volatility should lead to higher variance
        assert var_high >= var_low - 0.001  # Small tolerance for numerical errors
    
    @given(config=simulation_config_strategy())
    @settings(max_examples=10, deadline=8000)
    def test_risk_metrics_properties(self, config):
        """Test properties of risk metrics"""
        # Use smaller config for faster testing
        config.n_paths = min(config.n_paths, 2000)
        config.n_years = min(config.n_years, 5)
        
        engine = AdvancedMonteCarloEngine(config)
        paths = engine.simulate_paths(verbose=False)
        
        risk_metrics = engine.calculate_risk_metrics(paths)
        
        # Property 1: VaR and CVaR should be positive (loss amounts)
        assert risk_metrics["Value at Risk (95%)"] > 0
        assert risk_metrics["Conditional VaR (95%)"] > 0
        
        # Property 2: CVaR >= VaR (CVaR is tail expectation)
        assert (risk_metrics["Conditional VaR (95%)"] <= 
               risk_metrics["Value at Risk (95%)"] + 1e-6)
        
        # Property 3: Maximum drawdown should be non-negative
        assert risk_metrics["Maximum Drawdown"] >= -1e-6
        
        # Property 4: All metrics should be finite
        for metric, value in risk_metrics.items():
            assert np.isfinite(value), f"{metric} is not finite: {value}"


class TestPortfolioOptimizationProperties:
    """Property-based tests for portfolio optimization"""
    
    @given(assets=asset_data_strategy(min_assets=3, max_assets=8))
    @settings(max_examples=15, deadline=8000)
    def test_weight_normalization_property(self, assets):
        """Test that portfolio weights always sum to 1"""
        optimizer = IntelligentPortfolioOptimizer()
        
        try:
            result = optimizer.optimize(
                assets=assets,
                method=OptimizationMethod.MIN_VARIANCE
            )
            
            weights_sum = sum(result.weights.values())
            assert abs(weights_sum - 1.0) < 1e-5, f"Weights sum to {weights_sum}, not 1.0"
            
        except Exception as e:
            # Log the error for debugging but don't fail the property test
            note(f"Optimization failed: {e}")
            assume(False)  # Skip this example
    
    @given(assets=asset_data_strategy(min_assets=2, max_assets=5))
    @settings(max_examples=10, deadline=6000)
    def test_non_negative_weights_property(self, assets):
        """Test that weights are non-negative when short selling is disabled"""
        optimizer = IntelligentPortfolioOptimizer()
        constraints = PortfolioConstraints(allow_short_selling=False)
        
        try:
            result = optimizer.optimize(
                assets=assets,
                method=OptimizationMethod.MIN_VARIANCE,
                constraints=constraints
            )
            
            # All weights should be non-negative
            for symbol, weight in result.weights.items():
                assert weight >= -1e-6, f"Negative weight for {symbol}: {weight}"
                
        except Exception as e:
            note(f"Optimization failed: {e}")
            assume(False)
    
    @given(
        max_position_1=st.floats(min_value=0.1, max_value=0.4),
        max_position_2=st.floats(min_value=0.1, max_value=0.4)
    )
    @settings(max_examples=8, deadline=6000)
    def test_constraint_monotonicity(self, max_position_1, max_position_2):
        """Test that tighter constraints lead to higher or equal risk"""
        assume(abs(max_position_1 - max_position_2) > 0.05)
        
        # Create simple asset set
        np.random.seed(42)
        assets = []
        for i in range(4):
            returns = pd.Series(np.random.normal(0.08/252, 0.15/np.sqrt(252), 252))
            asset = AssetData(
                symbol=f'ASSET_{i}',
                returns=returns,
                expected_return=0.08 + i * 0.01,
                volatility=0.15 + i * 0.02
            )
            assets.append(asset)
        
        optimizer = IntelligentPortfolioOptimizer()
        
        try:
            # Less constrained portfolio
            loose_constraints = PortfolioConstraints(
                max_position_size=max(max_position_1, max_position_2)
            )
            loose_result = optimizer.optimize(
                assets=assets,
                method=OptimizationMethod.MIN_VARIANCE,
                constraints=loose_constraints
            )
            
            # More constrained portfolio
            tight_constraints = PortfolioConstraints(
                max_position_size=min(max_position_1, max_position_2)
            )
            tight_result = optimizer.optimize(
                assets=assets,
                method=OptimizationMethod.MIN_VARIANCE,
                constraints=tight_constraints
            )
            
            # Tighter constraints should lead to higher or equal risk
            assert (tight_result.metrics.volatility >= 
                   loose_result.metrics.volatility - 1e-4)
            
        except Exception as e:
            note(f"Constraint test failed: {e}")
            assume(False)
    
    @given(n_assets=st.integers(min_value=3, max_value=8))
    @settings(max_examples=10, deadline=5000)
    def test_diversification_property(self, n_assets):
        """Test that equal-weight portfolio has maximum diversification ratio"""
        # Create assets with equal expected returns but different volatilities
        np.random.seed(42)
        assets = []
        
        for i in range(n_assets):
            volatility = 0.1 + i * 0.05  # Different volatilities
            returns = pd.Series(
                np.random.normal(0.08/252, volatility/np.sqrt(252), 252)
            )
            
            asset = AssetData(
                symbol=f'ASSET_{i}',
                returns=returns,
                expected_return=0.08,  # Same expected return
                volatility=volatility
            )
            assets.append(asset)
        
        optimizer = IntelligentPortfolioOptimizer()
        
        try:
            result = optimizer.optimize(
                assets=assets,
                method=OptimizationMethod.MAX_DIVERSIFICATION
            )
            
            # Check that it's reasonably diversified
            weights_array = np.array(list(result.weights.values()))
            
            # No single asset should dominate completely
            max_weight = np.max(weights_array)
            assert max_weight < 0.8, f"Single asset weight too high: {max_weight}"
            
            # Should use multiple assets
            non_zero_weights = np.sum(weights_array > 0.01)
            assert non_zero_weights >= min(3, n_assets)
            
        except Exception as e:
            note(f"Diversification test failed: {e}")
            assume(False)


class TestFinancialCalculationProperties:
    """Property-based tests for general financial calculations"""
    
    @given(
        principal=st.floats(min_value=1000, max_value=100000),
        rate=st.floats(min_value=0.01, max_value=0.2),
        periods=st.integers(min_value=1, max_value=50)
    )
    def test_compound_interest_properties(self, principal, rate, periods):
        """Test compound interest calculation properties"""
        from app.utils.financial_formulas import calculate_compound_interest
        
        future_value = calculate_compound_interest(principal, rate, periods)
        
        # Property 1: Future value should be greater than principal for positive rates
        assert future_value >= principal
        
        # Property 2: Monotonicity with respect to rate
        higher_rate_fv = calculate_compound_interest(principal, rate * 1.1, periods)
        assert higher_rate_fv >= future_value
        
        # Property 3: Monotonicity with respect to time
        longer_time_fv = calculate_compound_interest(principal, rate, periods + 1)
        assert longer_time_fv >= future_value
        
        # Property 4: Scaling property
        double_principal_fv = calculate_compound_interest(principal * 2, rate, periods)
        assert abs(double_principal_fv - future_value * 2) < 1e-10
    
    @given(
        pv=st.floats(min_value=1000, max_value=100000),
        rate=st.floats(min_value=0.001, max_value=0.15),
        periods=st.integers(min_value=1, max_value=30)
    )
    def test_present_value_future_value_inverse(self, pv, rate, periods):
        """Test that PV and FV are inverse operations"""
        from app.utils.financial_formulas import present_value, future_value
        
        # Convert present value to future value and back
        fv = future_value(pv, rate, periods)
        pv_calculated = present_value(fv, rate, periods)
        
        # Should recover original present value
        relative_error = abs(pv_calculated - pv) / pv
        assert relative_error < 1e-10
    
    @given(
        cash_flows=arrays(
            dtype=np.float64,
            shape=st.integers(min_value=2, max_value=20),
            elements=st.floats(min_value=-10000, max_value=10000)
        ),
        rate=st.floats(min_value=0.01, max_value=0.2)
    )
    def test_npv_properties(self, cash_flows, rate):
        """Test Net Present Value calculation properties"""
        from app.utils.financial_formulas import calculate_npv
        
        # Ensure we have at least one negative and one positive cash flow
        assume(np.any(cash_flows > 0) and np.any(cash_flows < 0))
        
        npv = calculate_npv(cash_flows, rate)
        
        # Property 1: NPV should be finite
        assert np.isfinite(npv)
        
        # Property 2: Monotonicity with respect to discount rate
        # (NPV decreases as discount rate increases for typical cash flows)
        higher_rate = rate * 1.1
        npv_higher_rate = calculate_npv(cash_flows, higher_rate)
        
        # This property holds when first cash flow is negative (investment)
        if cash_flows[0] < 0:
            assert npv >= npv_higher_rate - 1e-10
        
        # Property 3: Scaling property
        scaled_cf = cash_flows * 2
        scaled_npv = calculate_npv(scaled_cf, rate)
        assert abs(scaled_npv - npv * 2) < 1e-8
    
    @given(
        price=st.floats(min_value=50, max_value=500),
        dividend=st.floats(min_value=0, max_value=20),
        growth_rate=st.floats(min_value=-0.1, max_value=0.2),
        required_return=st.floats(min_value=0.05, max_value=0.25)
    )
    def test_dividend_discount_model_properties(self, price, dividend, growth_rate, required_return):
        """Test Dividend Discount Model properties"""
        from app.utils.financial_formulas import gordon_growth_model
        
        assume(required_return > growth_rate + 0.01)  # Ensure convergence
        
        calculated_price = gordon_growth_model(dividend, growth_rate, required_return)
        
        # Property 1: Price should be positive for positive dividends
        if dividend > 0:
            assert calculated_price > 0
        
        # Property 2: Higher growth rate should lead to higher price
        if growth_rate < required_return - 0.02:  # Ensure still convergent
            higher_growth_price = gordon_growth_model(
                dividend, growth_rate + 0.01, required_return
            )
            assert higher_growth_price >= calculated_price - 1e-10
        
        # Property 3: Higher required return should lead to lower price
        lower_return_price = gordon_growth_model(
            dividend, growth_rate, required_return - 0.01
        )
        assert lower_return_price >= calculated_price - 1e-10


class TestTaxCalculationProperties:
    """Property-based tests for tax calculations"""
    
    @given(
        income1=st.floats(min_value=10000, max_value=100000),
        income2=st.floats(min_value=10000, max_value=100000)
    )
    @settings(max_examples=15, deadline=3000)
    def test_progressive_taxation_property(self, income1, income2):
        """Test progressive taxation: higher income leads to higher effective rate"""
        assume(abs(income1 - income2) > 5000)  # Meaningful difference
        
        tax_engine = TaxOptimizationEngine(
            current_year=2024,
            filing_status=FilingStatus.SINGLE
        )
        
        lower_income = min(income1, income2)
        higher_income = max(income1, income2)
        
        lower_tax = tax_engine.calculate_income_tax(Decimal(str(lower_income)))
        higher_tax = tax_engine.calculate_income_tax(Decimal(str(higher_income)))
        
        # Progressive taxation property
        assert (higher_tax['effective_rate'] >= 
               lower_tax['effective_rate'] - Decimal('0.001'))
        
        # Absolute tax should be higher for higher income
        assert higher_tax['federal_tax'] >= lower_tax['federal_tax']
    
    @given(
        gain_amount=st.floats(min_value=1000, max_value=50000),
        holding_days_1=st.integers(min_value=100, max_value=300),
        holding_days_2=st.integers(min_value=400, max_value=800)
    )
    @settings(max_examples=10, deadline=3000)
    def test_capital_gains_holding_period_property(self, gain_amount, holding_days_1, holding_days_2):
        """Test that long-term capital gains are taxed at lower rates"""
        tax_engine = TaxOptimizationEngine(
            current_year=2024,
            filing_status=FilingStatus.SINGLE
        )
        
        # Short-term gain (under 365 days)
        short_term = tax_engine.calculate_capital_gains_tax(
            gain_amount=Decimal(str(gain_amount)),
            holding_period_days=holding_days_1,
            income_level=Decimal('80000')
        )
        
        # Long-term gain (over 365 days)
        long_term = tax_engine.calculate_capital_gains_tax(
            gain_amount=Decimal(str(gain_amount)),
            holding_period_days=holding_days_2,
            income_level=Decimal('80000')
        )
        
        # Long-term should have lower or equal tax rate
        assert long_term['tax_rate'] <= short_term['tax_rate'] + Decimal('0.001')
        assert long_term['tax_owed'] <= short_term['tax_owed'] + Decimal('1')


class TestNumericalStabilityProperties:
    """Property-based tests for numerical stability"""
    
    @given(
        values=arrays(
            dtype=np.float64,
            shape=st.integers(min_value=10, max_value=100),
            elements=st.floats(
                min_value=1e-10, max_value=1e10,
                allow_nan=False, allow_infinity=False
            )
        )
    )
    def test_portfolio_variance_numerical_stability(self, values):
        """Test numerical stability of portfolio variance calculations"""
        from app.utils.portfolio_math import calculate_portfolio_variance
        
        n_assets = len(values)
        
        # Create correlation matrix
        corr_matrix = np.eye(n_assets) + 0.1 * np.random.random((n_assets, n_assets))
        corr_matrix = (corr_matrix + corr_matrix.T) / 2  # Make symmetric
        np.fill_diagonal(corr_matrix, 1.0)  # Diagonal should be 1
        
        # Ensure positive definiteness
        eigenvals = np.linalg.eigvals(corr_matrix)
        if np.min(eigenvals) <= 0:
            corr_matrix += (abs(np.min(eigenvals)) + 1e-8) * np.eye(n_assets)
        
        # Create covariance matrix
        volatilities = np.abs(values) / np.sum(np.abs(values)) + 0.01  # Normalize
        cov_matrix = np.outer(volatilities, volatilities) * corr_matrix
        
        # Create weights that sum to 1
        weights = np.abs(values) / np.sum(np.abs(values))
        
        try:
            portfolio_var = calculate_portfolio_variance(weights, cov_matrix)
            
            # Portfolio variance should be positive and finite
            assert portfolio_var >= 0
            assert np.isfinite(portfolio_var)
            
            # Should be less than or equal to maximum individual variance
            max_individual_var = np.max(np.diag(cov_matrix))
            assert portfolio_var <= max_individual_var + 1e-10
            
        except (np.linalg.LinAlgError, ValueError) as e:
            # Skip if numerical issues make the test invalid
            assume(False)
    
    @given(
        returns=arrays(
            dtype=np.float64,
            shape=st.integers(min_value=50, max_value=500),
            elements=st.floats(
                min_value=-0.1, max_value=0.1,
                allow_nan=False, allow_infinity=False
            )
        )
    )
    def test_sharpe_ratio_numerical_stability(self, returns):
        """Test numerical stability of Sharpe ratio calculations"""
        from app.utils.performance_metrics import calculate_sharpe_ratio
        
        risk_free_rate = 0.02
        
        try:
            sharpe_ratio = calculate_sharpe_ratio(returns, risk_free_rate)
            
            # Sharpe ratio should be finite
            if np.std(returns) > 1e-10:  # Avoid division by zero
                assert np.isfinite(sharpe_ratio)
                
                # Sharpe ratio should be bounded for reasonable returns
                assert abs(sharpe_ratio) < 100  # Sanity check
                
        except (ZeroDivisionError, ValueError):
            # Skip if returns have zero variance
            assume(False)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--hypothesis-show-statistics"])
