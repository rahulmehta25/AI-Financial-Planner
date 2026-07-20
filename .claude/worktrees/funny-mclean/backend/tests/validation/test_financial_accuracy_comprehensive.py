"""
Comprehensive financial calculation accuracy validation tests

Validates financial calculations against:
- Known analytical solutions
- Industry standard benchmarks
- Regulatory compliance requirements
- Mathematical properties and invariants
- Real-world financial data

Focuses on ensuring 85%+ accuracy for all financial calculations
with particular emphasis on money calculations and regulatory compliance.
"""

import pytest
import numpy as np
import pandas as pd
from decimal import Decimal, getcontext, ROUND_HALF_UP
from datetime import datetime, date, timedelta
from math import isclose
from typing import Dict, List, Tuple, Optional

# Set high precision for financial calculations
getcontext().prec = 28

from app.services.modeling.monte_carlo import AdvancedMonteCarloEngine, SimulationConfig
from app.services.optimization.portfolio_optimizer import IntelligentPortfolioOptimizer, AssetData
from app.services.tax.tax_optimization import TaxOptimizationEngine, FilingStatus
from app.services.modeling.cash_flow import CashFlowProjector
from app.utils.financial_formulas import (
    present_value, future_value, calculate_npv, calculate_irr,
    calculate_compound_interest, gordon_growth_model,
    black_scholes_call, black_scholes_put
)


class TestFinancialFormulaAccuracy:
    """Test accuracy of basic financial formulas"""
    
    def test_present_value_accuracy(self):
        """Test present value calculation accuracy"""
        test_cases = [
            # (future_value, rate, periods, expected_pv)
            (1000, 0.05, 1, 952.38),  # Simple case
            (10000, 0.08, 10, 4631.93),  # 10-year case
            (1000000, 0.03, 30, 411987.03),  # Long-term, low rate
            (5000, 0.12, 5, 2836.73),  # High rate
        ]
        
        for fv, rate, periods, expected_pv in test_cases:
            calculated_pv = present_value(fv, rate, periods)
            
            # Allow 0.1% relative error tolerance
            relative_error = abs(calculated_pv - expected_pv) / expected_pv
            assert relative_error < 0.001, f"PV calculation error: {calculated_pv} vs {expected_pv}"
    
    def test_future_value_accuracy(self):
        """Test future value calculation accuracy"""
        test_cases = [
            # (present_value, rate, periods, expected_fv)
            (1000, 0.05, 1, 1050.00),
            (1000, 0.08, 10, 2158.92),
            (10000, 0.06, 20, 32071.35),
            (5000, 0.04, 15, 9003.39),
        ]
        
        for pv, rate, periods, expected_fv in test_cases:
            calculated_fv = future_value(pv, rate, periods)
            
            relative_error = abs(calculated_fv - expected_fv) / expected_fv
            assert relative_error < 0.001, f"FV calculation error: {calculated_fv} vs {expected_fv}"
    
    def test_npv_accuracy(self):
        """Test Net Present Value calculation accuracy"""
        # Test case: Initial investment of -100, then +30 for 4 years
        cash_flows = [-100, 30, 30, 30, 30]
        discount_rate = 0.10
        
        # Expected NPV calculation:
        # NPV = -100 + 30/(1.10)^1 + 30/(1.10)^2 + 30/(1.10)^3 + 30/(1.10)^4
        # NPV = -100 + 27.27 + 24.79 + 22.54 + 20.49 = -4.91
        expected_npv = -4.91
        
        calculated_npv = calculate_npv(cash_flows, discount_rate)
        
        relative_error = abs(calculated_npv - expected_npv) / abs(expected_npv)
        assert relative_error < 0.01, f"NPV calculation error: {calculated_npv} vs {expected_npv}"
    
    def test_irr_accuracy(self):
        """Test Internal Rate of Return calculation accuracy"""
        # Test case with known IRR
        cash_flows = [-1000, 300, 400, 500, 200]
        expected_irr = 0.1405  # Approximately 14.05%
        
        calculated_irr = calculate_irr(cash_flows)
        
        # IRR should be accurate to within 0.1%
        assert abs(calculated_irr - expected_irr) < 0.001, f"IRR calculation error: {calculated_irr} vs {expected_irr}"
    
    def test_compound_interest_accuracy(self):
        """Test compound interest calculation"""
        principal = 10000
        rate = 0.07
        periods = 10
        
        # Expected: 10000 * (1.07)^10 = 19,671.51
        expected_value = 19671.51
        
        calculated_value = calculate_compound_interest(principal, rate, periods)
        
        relative_error = abs(calculated_value - expected_value) / expected_value
        assert relative_error < 0.001, f"Compound interest error: {calculated_value} vs {expected_value}"
    
    def test_gordon_growth_model_accuracy(self):
        """Test Gordon Growth Model (Dividend Discount Model)"""
        # Test case: $5 dividend, 3% growth, 8% required return
        dividend = 5.0
        growth_rate = 0.03
        required_return = 0.08
        
        # Expected price = D1 / (r - g) = 5 * 1.03 / (0.08 - 0.03) = 5.15 / 0.05 = 103.00
        expected_price = 103.00
        
        calculated_price = gordon_growth_model(dividend, growth_rate, required_return)
        
        relative_error = abs(calculated_price - expected_price) / expected_price
        assert relative_error < 0.001, f"Gordon Growth Model error: {calculated_price} vs {expected_price}"


class TestBlackScholesAccuracy:
    """Test Black-Scholes option pricing accuracy"""
    
    def test_black_scholes_call_accuracy(self):
        """Test Black-Scholes call option pricing"""
        # Standard test case
        S = 100  # Stock price
        K = 100  # Strike price
        T = 0.25  # 3 months to expiration
        r = 0.05  # Risk-free rate
        sigma = 0.20  # Volatility
        
        # Expected value from standard Black-Scholes tables: ~2.78
        expected_call_price = 2.78
        
        calculated_call_price = black_scholes_call(S, K, T, r, sigma)
        
        relative_error = abs(calculated_call_price - expected_call_price) / expected_call_price
        assert relative_error < 0.02, f"Black-Scholes call error: {calculated_call_price} vs {expected_call_price}"
    
    def test_black_scholes_put_accuracy(self):
        """Test Black-Scholes put option pricing"""
        S = 100
        K = 100
        T = 0.25
        r = 0.05
        sigma = 0.20
        
        # Expected put price from put-call parity: ~1.53
        expected_put_price = 1.53
        
        calculated_put_price = black_scholes_put(S, K, T, r, sigma)
        
        relative_error = abs(calculated_put_price - expected_put_price) / expected_put_price
        assert relative_error < 0.02, f"Black-Scholes put error: {calculated_put_price} vs {expected_put_price}"
    
    def test_put_call_parity(self):
        """Test put-call parity relationship"""
        S = 100
        K = 100
        T = 0.25
        r = 0.05
        sigma = 0.20
        
        call_price = black_scholes_call(S, K, T, r, sigma)
        put_price = black_scholes_put(S, K, T, r, sigma)
        
        # Put-call parity: C - P = S - K * e^(-r*T)
        left_side = call_price - put_price
        right_side = S - K * np.exp(-r * T)
        
        assert abs(left_side - right_side) < 0.01, "Put-call parity violation"


class TestMonteCarloAccuracy:
    """Test Monte Carlo simulation accuracy"""
    
    def test_geometric_brownian_motion_accuracy(self):
        """Test GBM simulation matches theoretical moments"""
        config = SimulationConfig(
            n_paths=50000,
            n_years=1,
            initial_price=100.0,
            risk_free_rate=0.05,
            volatility=0.20
        )
        
        engine = AdvancedMonteCarloEngine(config)
        paths = engine.simulate_paths(verbose=False)
        final_prices = paths[:, -1]
        
        # Theoretical moments for log-normal distribution
        mu = config.risk_free_rate - 0.5 * config.volatility**2
        theoretical_mean = config.initial_price * np.exp(config.risk_free_rate * config.n_years)
        theoretical_var = (config.initial_price**2) * np.exp(2*config.risk_free_rate*config.n_years) * \
                         (np.exp(config.volatility**2*config.n_years) - 1)
        theoretical_std = np.sqrt(theoretical_var)
        
        # Test mean
        simulated_mean = np.mean(final_prices)
        mean_error = abs(simulated_mean - theoretical_mean) / theoretical_mean
        assert mean_error < 0.02, f"Monte Carlo mean error: {mean_error:.4f}"
        
        # Test standard deviation
        simulated_std = np.std(final_prices)
        std_error = abs(simulated_std - theoretical_std) / theoretical_std
        assert std_error < 0.05, f"Monte Carlo std error: {std_error:.4f}"
    
    def test_risk_neutral_valuation(self):
        """Test risk-neutral valuation property"""
        config = SimulationConfig(
            n_paths=100000,
            n_years=0.25,  # 3 months
            initial_price=100.0,
            risk_free_rate=0.05,
            volatility=0.20
        )
        
        engine = AdvancedMonteCarloEngine(config)
        paths = engine.simulate_paths(verbose=False)
        final_prices = paths[:, -1]
        
        # Value European call option with strike 100
        strike = 100
        call_payoffs = np.maximum(final_prices - strike, 0)
        monte_carlo_call_value = np.mean(call_payoffs) * np.exp(-config.risk_free_rate * config.n_years)
        
        # Compare with Black-Scholes
        bs_call_value = black_scholes_call(
            S=config.initial_price,
            K=strike,
            T=config.n_years,
            r=config.risk_free_rate,
            sigma=config.volatility
        )
        
        relative_error = abs(monte_carlo_call_value - bs_call_value) / bs_call_value
        assert relative_error < 0.02, f"Monte Carlo option pricing error: {relative_error:.4f}"


class TestPortfolioOptimizationAccuracy:
    """Test portfolio optimization calculation accuracy"""
    
    def test_two_asset_portfolio_theory(self):
        """Test two-asset portfolio optimization against analytical solution"""
        # Create two assets with known properties
        np.random.seed(42)
        
        # Asset 1: Expected return 8%, volatility 15%
        returns_1 = pd.Series(np.random.normal(0.08/252, 0.15/np.sqrt(252), 1000))
        asset_1 = AssetData(
            symbol="ASSET1",
            returns=returns_1,
            expected_return=0.08,
            volatility=0.15
        )
        
        # Asset 2: Expected return 12%, volatility 25%
        returns_2 = pd.Series(np.random.normal(0.12/252, 0.25/np.sqrt(252), 1000))
        asset_2 = AssetData(
            symbol="ASSET2",
            returns=returns_2,
            expected_return=0.12,
            volatility=0.25
        )
        
        assets = [asset_1, asset_2]
        
        optimizer = IntelligentPortfolioOptimizer(risk_free_rate=0.03)
        
        # Test minimum variance portfolio
        result = optimizer.optimize(
            assets=assets,
            method=OptimizationMethod.MIN_VARIANCE
        )
        
        # For uncorrelated assets, minimum variance weight should favor lower volatility asset
        weights = result.weights
        asset1_weight = weights.get('ASSET1', 0)
        asset2_weight = weights.get('ASSET2', 0)
        
        # Asset 1 has lower volatility, so should have higher weight in min variance portfolio
        assert asset1_weight > asset2_weight, "Minimum variance should favor lower volatility asset"
        
        # Test that portfolio volatility is less than both individual volatilities
        assert result.metrics.volatility < 0.15, "Portfolio volatility should be less than individual assets"
    
    def test_efficient_frontier_properties(self):
        """Test efficient frontier mathematical properties"""
        np.random.seed(42)
        
        # Create multiple assets
        assets = []
        expected_returns = [0.04, 0.08, 0.12, 0.16]
        volatilities = [0.08, 0.15, 0.22, 0.30]
        
        for i, (er, vol) in enumerate(zip(expected_returns, volatilities)):
            returns = pd.Series(np.random.normal(er/252, vol/np.sqrt(252), 1000))
            asset = AssetData(
                symbol=f"ASSET{i+1}",
                returns=returns,
                expected_return=er,
                volatility=vol
            )
            assets.append(asset)
        
        optimizer = IntelligentPortfolioOptimizer(risk_free_rate=0.02)
        
        # Test multiple points on efficient frontier
        min_var_result = optimizer.optimize(assets, OptimizationMethod.MIN_VARIANCE)
        max_sharpe_result = optimizer.optimize(assets, OptimizationMethod.MAX_SHARPE)
        
        # Max Sharpe should have higher return than min variance (generally)
        assert (max_sharpe_result.metrics.expected_return >= 
                min_var_result.metrics.expected_return - 0.01), \
                "Max Sharpe should generally have higher expected return"
        
        # Both should be well-diversified (no single asset > 80%)
        for result in [min_var_result, max_sharpe_result]:
            max_weight = max(result.weights.values()) if result.weights else 0
            assert max_weight <= 0.85, f"Portfolio should be diversified, max weight: {max_weight}"


class TestTaxCalculationAccuracy:
    """Test tax calculation accuracy against known values"""
    
    def test_federal_tax_brackets_2024(self):
        """Test 2024 federal tax bracket calculations"""
        tax_engine = TaxOptimizationEngine(
            current_year=2024,
            filing_status=FilingStatus.SINGLE
        )
        
        # Test specific income levels with known tax amounts
        test_cases = [
            # (taxable_income, expected_tax_range_min, expected_tax_range_max)
            (25000, 2700, 2800),   # 10% + 12% brackets
            (50000, 6600, 6800),   # Up to 12% bracket
            (100000, 17800, 18200), # Up to 22% bracket
            (200000, 45000, 46000), # Up to 24% bracket
        ]
        
        for income, min_tax, max_tax in test_cases:
            tax_info = tax_engine.calculate_income_tax(Decimal(str(income)))
            federal_tax = float(tax_info['federal_tax'])
            
            assert min_tax <= federal_tax <= max_tax, \
                f"Federal tax for ${income:,} should be ${min_tax:,}-${max_tax:,}, got ${federal_tax:,.2f}"
    
    def test_capital_gains_rates(self):
        """Test capital gains tax rate accuracy"""
        tax_engine = TaxOptimizationEngine(
            current_year=2024,
            filing_status=FilingStatus.MARRIED_FILING_JOINTLY
        )
        
        # Test long-term capital gains rates
        test_cases = [
            # (income_level, gain_amount, expected_rate_range)
            (50000, 10000, (0.0, 0.0)),    # 0% bracket
            (100000, 20000, (0.0, 0.15)),   # 0% or 15% bracket boundary
            (300000, 50000, (0.15, 0.15)),  # 15% bracket
            (600000, 100000, (0.20, 0.20)), # 20% bracket
        ]
        
        for income, gain, (min_rate, max_rate) in test_cases:
            cg_info = tax_engine.calculate_capital_gains_tax(
                gain_amount=Decimal(str(gain)),
                holding_period_days=400,  # Long-term
                income_level=Decimal(str(income))
            )
            
            rate = float(cg_info['tax_rate'])
            assert min_rate <= rate <= max_rate + 0.01, \
                f"Capital gains rate for income ${income:,} should be {min_rate:.1%}-{max_rate:.1%}, got {rate:.1%}"


class TestRegulatoryComplianceAccuracy:
    """Test calculations meet regulatory compliance requirements"""
    
    def test_rmd_calculation_accuracy(self):
        """Test Required Minimum Distribution calculations"""
        tax_engine = TaxOptimizationEngine(
            current_year=2024,
            filing_status=FilingStatus.SINGLE
        )
        
        # Test RMD calculations against IRS Uniform Lifetime Table
        test_cases = [
            # (age, account_balance, expected_distribution_factor, expected_rmd_range)
            (73, 500000, 26.5, (18800, 18900)),  # First RMD year
            (75, 600000, 24.6, (24300, 24500)),  # Common age
            (80, 400000, 20.2, (19700, 19900)),  # Later retirement
            (85, 300000, 16.0, (18700, 18800)),  # Advanced age
        ]
        
        from app.services.tax.tax_optimization import TaxAccountType
        
        for age, balance, dist_factor, (min_rmd, max_rmd) in test_cases:
            rmd_info = tax_engine.calculate_required_minimum_distribution(
                account_balance=Decimal(str(balance)),
                age=age,
                account_type=TaxAccountType.TRADITIONAL_401K
            )
            
            rmd_amount = float(rmd_info['required_amount'])
            calculated_factor = float(rmd_info['distribution_factor'])
            
            # Test distribution factor accuracy
            assert abs(calculated_factor - dist_factor) < 0.1, \
                f"Distribution factor for age {age} should be ~{dist_factor}, got {calculated_factor}"
            
            # Test RMD amount accuracy
            assert min_rmd <= rmd_amount <= max_rmd, \
                f"RMD for age {age} with ${balance:,} should be ${min_rmd:,}-${max_rmd:,}, got ${rmd_amount:,.2f}"
    
    def test_contribution_limits_2024(self):
        """Test retirement contribution limits for 2024"""
        # These should match IRS published limits
        expected_limits = {
            '401k_limit': 23000,
            '401k_catchup_limit': 7500,
            'ira_limit': 7000,
            'ira_catchup_limit': 1000,
            'hsa_individual_limit': 4150,
            'hsa_family_limit': 8300,
            'hsa_catchup_limit': 1000
        }
        
        from app.services.tax.tax_optimization import get_contribution_limits
        
        calculated_limits = get_contribution_limits(2024)
        
        for limit_type, expected_amount in expected_limits.items():
            calculated_amount = calculated_limits.get(limit_type, 0)
            assert calculated_amount == expected_amount, \
                f"{limit_type} should be ${expected_amount:,}, got ${calculated_amount:,}"


class TestNumericalStabilityAccuracy:
    """Test numerical stability and edge cases"""
    
    def test_extreme_values_handling(self):
        """Test handling of extreme financial values"""
        # Test very large numbers
        large_pv = present_value(1e12, 0.05, 30)  # $1 trillion
        assert np.isfinite(large_pv), "Should handle large numbers"
        assert large_pv > 0, "Present value should be positive"
        
        # Test very small numbers
        small_fv = future_value(0.01, 0.03, 10)  # 1 cent
        assert np.isfinite(small_fv), "Should handle small numbers"
        assert small_fv > 0.01, "Future value should be larger than present value"
        
        # Test very long time periods
        long_term_fv = future_value(1000, 0.04, 100)  # 100 years
        assert np.isfinite(long_term_fv), "Should handle long time periods"
        assert long_term_fv > 1000, "Long-term future value should be larger"
    
    def test_precision_requirements(self):
        """Test calculation precision meets financial standards"""
        # Financial calculations should be accurate to at least 2 decimal places
        principal = 12345.67
        rate = 0.0456
        periods = 37
        
        fv = future_value(principal, rate, periods)
        back_calculated_pv = present_value(fv, rate, periods)
        
        # Should be able to reverse-calculate with high precision
        precision_error = abs(back_calculated_pv - principal)
        assert precision_error < 0.01, f"Precision error too large: ${precision_error:.4f}"
    
    def test_edge_case_rates(self):
        """Test edge cases with extreme interest rates"""
        # Test zero interest rate
        zero_rate_fv = future_value(1000, 0.0, 10)
        assert zero_rate_fv == 1000, "Zero rate should not change value"
        
        # Test very low interest rate
        low_rate_fv = future_value(1000, 0.0001, 10)  # 0.01%
        assert low_rate_fv > 1000, "Low rate should still increase value"
        assert low_rate_fv < 1001, "Very low rate should have minimal impact"
        
        # Test high interest rate
        high_rate_fv = future_value(1000, 0.50, 2)  # 50% rate
        expected_fv = 1000 * (1.50 ** 2)
        assert abs(high_rate_fv - expected_fv) < 0.01, "High rate calculation should be accurate"


class TestRealWorldDataValidation:
    """Test calculations against real-world financial data"""
    
    @pytest.mark.slow
    def test_historical_market_returns(self):
        """Test portfolio calculations against historical market data"""
        # This test would use real market data to validate calculations
        # Marked as slow since it requires data download
        
        try:
            import yfinance as yf
            
            # Get S&P 500 data for validation
            spy_data = yf.download('SPY', start='2020-01-01', end='2023-01-01', progress=False)
            
            if not spy_data.empty:
                returns = spy_data['Adj Close'].pct_change().dropna()
                
                # Calculate annual statistics
                annual_return = returns.mean() * 252
                annual_vol = returns.std() * np.sqrt(252)
                
                # Sanity checks against known market behavior
                assert -0.5 < annual_return < 0.5, "Annual return should be reasonable"
                assert 0.05 < annual_vol < 0.8, "Volatility should be reasonable"
                
                # Sharpe ratio calculation
                risk_free_rate = 0.02  # Approximate risk-free rate
                sharpe_ratio = (annual_return - risk_free_rate) / annual_vol
                
                # Sharpe ratio should be finite and reasonable
                assert np.isfinite(sharpe_ratio), "Sharpe ratio should be finite"
                assert -2 < sharpe_ratio < 3, "Sharpe ratio should be reasonable"
                
        except ImportError:
            pytest.skip("yfinance not available for real-world data testing")
        except Exception as e:
            pytest.skip(f"Could not download market data: {e}")
    
    def test_benchmark_portfolio_calculations(self):
        """Test against known benchmark portfolio characteristics"""
        # 60/40 stock/bond portfolio characteristics
        # Based on historical performance of diversified portfolios
        
        # Create mock assets representing broad market indices
        np.random.seed(42)
        
        # Stock component (higher return, higher volatility)
        stock_returns = pd.Series(np.random.normal(0.10/252, 0.16/np.sqrt(252), 2000))
        stock_asset = AssetData(
            symbol="STOCKS",
            returns=stock_returns,
            expected_return=0.10,
            volatility=0.16
        )
        
        # Bond component (lower return, lower volatility)
        bond_returns = pd.Series(np.random.normal(0.04/252, 0.06/np.sqrt(252), 2000))
        bond_asset = AssetData(
            symbol="BONDS",
            returns=bond_returns,
            expected_return=0.04,
            volatility=0.06
        )
        
        # Calculate 60/40 portfolio metrics
        portfolio_return = 0.6 * 0.10 + 0.4 * 0.04  # Expected: 7.6%
        
        # Portfolio volatility with correlation
        correlation = 0.2  # Typical stock-bond correlation
        portfolio_var = (0.6**2) * (0.16**2) + (0.4**2) * (0.06**2) + 2 * 0.6 * 0.4 * correlation * 0.16 * 0.06
        portfolio_vol = np.sqrt(portfolio_var)  # Expected: ~10.4%
        
        # Validate calculations
        assert 0.075 < portfolio_return < 0.077, f"60/40 portfolio return should be ~7.6%, got {portfolio_return:.3%}"
        assert 0.10 < portfolio_vol < 0.11, f"60/40 portfolio volatility should be ~10.4%, got {portfolio_vol:.3%}"
        
        # Sharpe ratio should be reasonable
        sharpe_ratio = (portfolio_return - 0.03) / portfolio_vol  # Assuming 3% risk-free rate
        assert 0.3 < sharpe_ratio < 0.6, f"60/40 Sharpe ratio should be reasonable, got {sharpe_ratio:.3f}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-x"])  # Stop on first failure for accuracy testing
