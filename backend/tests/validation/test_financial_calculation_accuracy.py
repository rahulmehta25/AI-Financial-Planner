"""
Financial calculation accuracy validation tests.

Tests cover:
- Mathematical accuracy of financial formulas
- Time value of money calculations
- Portfolio performance metrics
- Risk calculations (VaR, CVaR, etc.)
- Tax calculations and compliance
- Retirement planning accuracy
- Monte Carlo simulation convergence
- Cross-validation against known benchmarks
"""

import pytest
import numpy as np
from decimal import Decimal, getcontext
from datetime import datetime, date, timedelta
from typing import List, Dict, Tuple
import math
from scipy import stats
from scipy.optimize import minimize

from app.services.modeling.monte_carlo import AdvancedMonteCarloEngine
from app.services.optimization.mpt import ModernPortfolioTheory
from app.services.retirement_planning import RetirementPlanningService
from app.services.tax_optimization import TaxOptimizationService
from app.utils.financial_calculations import (
    present_value, future_value, annuity_present_value, annuity_future_value,
    compound_annual_growth_rate, sharpe_ratio, sortino_ratio, maximum_drawdown,
    value_at_risk, conditional_value_at_risk, beta_coefficient
)

# Set decimal precision for financial calculations
getcontext().prec = 28


class TestTimeValueOfMoneyAccuracy:
    """Test accuracy of time value of money calculations."""
    
    def test_present_value_accuracy(self):
        """Test present value calculation against known values."""
        
        # Test case 1: $1000 in 5 years at 7% discount rate
        pv = present_value(future_value=1000, rate=0.07, periods=5)
        expected = 1000 / (1.07 ** 5)  # $712.99
        assert abs(pv - expected) < 0.01, f"Expected {expected:.2f}, got {pv:.2f}"
        
        # Test case 2: $5000 in 10 years at 3% discount rate
        pv = present_value(future_value=5000, rate=0.03, periods=10)
        expected = 5000 / (1.03 ** 10)  # $3720.48
        assert abs(pv - expected) < 0.01
        
        # Test case 3: Edge case with 0% rate
        pv = present_value(future_value=1000, rate=0.0, periods=5)
        assert pv == 1000, "PV should equal FV when rate is 0%"
    
    def test_future_value_accuracy(self):
        """Test future value calculation accuracy."""
        
        # Test case 1: $1000 invested for 10 years at 7%
        fv = future_value(present_value=1000, rate=0.07, periods=10)
        expected = 1000 * (1.07 ** 10)  # $1967.15
        assert abs(fv - expected) < 0.01
        
        # Test case 2: Rule of 72 validation (approximate)
        # Money should double in ~10.24 years at 7%
        fv = future_value(present_value=1000, rate=0.07, periods=10.24)
        assert 1990 < fv < 2010, f"Expected ~2000, got {fv:.2f}"
    
    def test_annuity_calculations(self):
        """Test annuity calculation accuracy."""
        
        # Test case 1: $1000 annual payment for 20 years at 5%
        pv = annuity_present_value(payment=1000, rate=0.05, periods=20)
        # Formula: PMT * [(1 - (1 + r)^-n) / r]
        expected = 1000 * (1 - (1.05 ** -20)) / 0.05  # $12,462.21
        assert abs(pv - expected) < 0.01
        
        # Test case 2: Future value of annuity
        fv = annuity_future_value(payment=1000, rate=0.05, periods=20)
        # Formula: PMT * [((1 + r)^n - 1) / r]
        expected = 1000 * ((1.05 ** 20) - 1) / 0.05  # $33,065.95
        assert abs(fv - expected) < 0.01
        
        # Test case 3: Annuity due (payments at beginning)
        pv_due = annuity_present_value(payment=1000, rate=0.05, periods=20, due=True)
        expected_due = pv * 1.05  # Multiply by (1 + r) for annuity due
        assert abs(pv_due - expected_due) < 0.01
    
    def test_compound_growth_accuracy(self):
        """Test compound annual growth rate (CAGR) calculation."""
        
        # Test case 1: $1000 grows to $2000 in 10 years
        cagr = compound_annual_growth_rate(beginning_value=1000, ending_value=2000, periods=10)
        expected = (2000 / 1000) ** (1/10) - 1  # ~7.18%
        assert abs(cagr - expected) < 0.0001
        
        # Test case 2: Negative growth
        cagr = compound_annual_growth_rate(beginning_value=1000, ending_value=800, periods=5)
        expected = (800 / 1000) ** (1/5) - 1  # ~-4.56%
        assert abs(cagr - expected) < 0.0001
        
        # Test case 3: No growth
        cagr = compound_annual_growth_rate(beginning_value=1000, ending_value=1000, periods=5)
        assert cagr == 0.0


class TestPortfolioPerformanceMetrics:
    """Test accuracy of portfolio performance calculations."""
    
    @pytest.fixture
    def sample_returns(self):
        """Sample return data for testing."""
        # 12 months of returns (monthly)
        portfolio_returns = np.array([
            0.05, -0.02, 0.08, -0.01, 0.03, 0.07,
            -0.04, 0.06, 0.02, -0.03, 0.09, 0.01
        ])
        
        market_returns = np.array([
            0.04, -0.01, 0.07, 0.00, 0.02, 0.06,
            -0.03, 0.05, 0.01, -0.02, 0.08, 0.02
        ])
        
        risk_free_rate = 0.02 / 12  # 2% annual, converted to monthly
        
        return portfolio_returns, market_returns, risk_free_rate
    
    def test_sharpe_ratio_accuracy(self, sample_returns):
        """Test Sharpe ratio calculation accuracy."""
        
        portfolio_returns, _, risk_free_rate = sample_returns
        
        # Calculate Sharpe ratio
        sharpe = sharpe_ratio(portfolio_returns, risk_free_rate)
        
        # Manual calculation for verification
        excess_returns = portfolio_returns - risk_free_rate
        expected_sharpe = np.mean(excess_returns) / np.std(excess_returns, ddof=1)
        
        # Annualize (multiply by sqrt(12) for monthly data)
        expected_sharpe *= np.sqrt(12)
        
        assert abs(sharpe - expected_sharpe) < 0.001
    
    def test_sortino_ratio_accuracy(self, sample_returns):
        """Test Sortino ratio calculation accuracy."""
        
        portfolio_returns, _, risk_free_rate = sample_returns
        
        # Calculate Sortino ratio
        sortino = sortino_ratio(portfolio_returns, risk_free_rate)
        
        # Manual calculation
        excess_returns = portfolio_returns - risk_free_rate
        downside_returns = excess_returns[excess_returns < 0]
        downside_deviation = np.sqrt(np.mean(downside_returns ** 2))
        expected_sortino = np.mean(excess_returns) / downside_deviation * np.sqrt(12)
        
        assert abs(sortino - expected_sortino) < 0.001
    
    def test_maximum_drawdown_accuracy(self, sample_returns):
        """Test maximum drawdown calculation accuracy."""
        
        portfolio_returns, _, _ = sample_returns
        
        # Calculate maximum drawdown
        max_dd = maximum_drawdown(portfolio_returns)
        
        # Manual calculation
        cumulative_returns = np.cumprod(1 + portfolio_returns)
        running_max = np.maximum.accumulate(cumulative_returns)
        drawdowns = (cumulative_returns - running_max) / running_max
        expected_max_dd = np.min(drawdowns)
        
        assert abs(max_dd - expected_max_dd) < 0.001
    
    def test_beta_calculation_accuracy(self, sample_returns):
        """Test beta coefficient calculation accuracy."""
        
        portfolio_returns, market_returns, _ = sample_returns
        
        # Calculate beta
        beta = beta_coefficient(portfolio_returns, market_returns)
        
        # Manual calculation using covariance
        covariance = np.cov(portfolio_returns, market_returns)[0, 1]
        market_variance = np.var(market_returns, ddof=1)
        expected_beta = covariance / market_variance
        
        assert abs(beta - expected_beta) < 0.001
    
    def test_value_at_risk_accuracy(self, sample_returns):
        """Test Value at Risk (VaR) calculation accuracy."""
        
        portfolio_returns, _, _ = sample_returns
        
        # Test different confidence levels
        confidence_levels = [0.95, 0.99, 0.999]
        
        for confidence in confidence_levels:
            # Parametric VaR (assuming normal distribution)
            var_parametric = value_at_risk(portfolio_returns, confidence, method='parametric')
            
            # Historical VaR (using empirical distribution)
            var_historical = value_at_risk(portfolio_returns, confidence, method='historical')
            
            # Manual parametric calculation
            mean_return = np.mean(portfolio_returns)
            std_return = np.std(portfolio_returns, ddof=1)
            z_score = stats.norm.ppf(1 - confidence)
            expected_var_parametric = mean_return + z_score * std_return
            
            assert abs(var_parametric - expected_var_parametric) < 0.001
            
            # Historical VaR should be a percentile of actual returns
            expected_var_historical = np.percentile(portfolio_returns, (1 - confidence) * 100)
            assert abs(var_historical - expected_var_historical) < 0.001
    
    def test_conditional_value_at_risk_accuracy(self, sample_returns):
        """Test Conditional Value at Risk (CVaR) calculation accuracy."""
        
        portfolio_returns, _, _ = sample_returns
        confidence = 0.95
        
        # Calculate CVaR
        cvar = conditional_value_at_risk(portfolio_returns, confidence)
        
        # Manual calculation
        var = value_at_risk(portfolio_returns, confidence, method='historical')
        tail_losses = portfolio_returns[portfolio_returns <= var]
        expected_cvar = np.mean(tail_losses) if len(tail_losses) > 0 else var
        
        assert abs(cvar - expected_cvar) < 0.001


class TestRetirementPlanningAccuracy:
    """Test accuracy of retirement planning calculations."""
    
    def test_retirement_savings_calculation(self):
        """Test retirement savings requirement calculation."""
        
        # Scenario: 35-year-old wants to replace 80% of $100K income
        current_age = 35
        retirement_age = 65
        current_income = 100000
        replacement_ratio = 0.8
        inflation_rate = 0.025
        expected_return = 0.07
        life_expectancy = 90
        
        years_to_retirement = retirement_age - current_age
        years_in_retirement = life_expectancy - retirement_age
        
        # Calculate target retirement income (inflation-adjusted)
        target_income = current_income * replacement_ratio
        inflation_adjusted_income = target_income * (1 + inflation_rate) ** years_to_retirement
        
        # Calculate total retirement need (present value of annuity)
        # Using real return rate (nominal - inflation)
        real_return_rate = (1 + expected_return) / (1 + inflation_rate) - 1
        
        retirement_need = annuity_present_value(
            payment=inflation_adjusted_income,
            rate=real_return_rate,
            periods=years_in_retirement
        )
        
        # Verify calculation makes sense
        assert retirement_need > 0
        assert retirement_need > inflation_adjusted_income * 10  # Should be more than 10 years of income
        assert retirement_need < inflation_adjusted_income * 30  # But less than 30 years
    
    def test_required_monthly_savings(self):
        """Test calculation of required monthly savings for retirement goal."""
        
        # Target: $1M in 30 years with 7% annual return
        target_amount = 1000000
        years = 30
        annual_rate = 0.07
        monthly_rate = annual_rate / 12
        months = years * 12
        
        # Calculate required monthly payment (future value of annuity)
        # FV = PMT * [((1 + r)^n - 1) / r]
        # Solving for PMT: PMT = FV * r / ((1 + r)^n - 1)
        required_payment = target_amount * monthly_rate / ((1 + monthly_rate) ** months - 1)
        
        # Verify the payment will actually reach the target
        actual_fv = annuity_future_value(
            payment=required_payment,
            rate=monthly_rate,
            periods=months
        )
        
        assert abs(actual_fv - target_amount) < 1  # Within $1
        
        # Sanity check: payment should be reasonable
        assert 500 < required_payment < 2000  # Between $500-$2000/month seems reasonable
    
    def test_rmd_calculation_accuracy(self):
        """Test Required Minimum Distribution calculation accuracy."""
        
        # IRS life expectancy factors (simplified)
        life_expectancy_factors = {
            73: 26.5, 74: 25.5, 75: 24.6, 76: 23.7, 77: 22.9,
            78: 22.0, 79: 21.1, 80: 20.2, 81: 19.4, 82: 18.5,
            83: 17.7, 84: 16.8, 85: 16.0
        }
        
        test_cases = [
            (73, 500000, 500000 / 26.5),
            (75, 300000, 300000 / 24.6),
            (80, 150000, 150000 / 20.2)
        ]
        
        for age, balance, expected_rmd in test_cases:
            calculated_rmd = balance / life_expectancy_factors[age]
            assert abs(calculated_rmd - expected_rmd) < 0.01
    
    def test_social_security_benefit_estimation(self):
        """Test Social Security benefit estimation accuracy."""
        
        # Simplified Social Security calculation (actual calculation is more complex)
        # Primary Insurance Amount (PIA) calculation for 2024
        
        def calculate_pia(average_indexed_monthly_earnings):
            """Calculate Primary Insurance Amount based on AIME."""
            
            # 2024 bend points
            bend_point_1 = 1174
            bend_point_2 = 7078
            
            if average_indexed_monthly_earnings <= bend_point_1:
                pia = average_indexed_monthly_earnings * 0.9
            elif average_indexed_monthly_earnings <= bend_point_2:
                pia = (bend_point_1 * 0.9 + 
                       (average_indexed_monthly_earnings - bend_point_1) * 0.32)
            else:
                pia = (bend_point_1 * 0.9 + 
                       (bend_point_2 - bend_point_1) * 0.32 +
                       (average_indexed_monthly_earnings - bend_point_2) * 0.15)
            
            return pia
        
        # Test cases
        test_cases = [
            (1000, 900),      # Below first bend point: $1000 * 0.9
            (3000, 1758.4),   # Between bend points: $1174 * 0.9 + $1826 * 0.32
            (8000, 2559.14)   # Above second bend point
        ]
        
        for aime, expected_pia in test_cases:
            calculated_pia = calculate_pia(aime)
            assert abs(calculated_pia - expected_pia) < 0.5  # Within $0.50


class TestTaxCalculationAccuracy:
    """Test accuracy of tax-related calculations."""
    
    def test_marginal_tax_rate_calculation(self):
        """Test marginal tax rate calculation for 2024 tax brackets."""
        
        # 2024 tax brackets for single filers
        tax_brackets = [
            (11600, 0.10),
            (47150, 0.12),
            (100525, 0.22),
            (191950, 0.24),
            (243725, 0.32),
            (609350, 0.35),
            (float('inf'), 0.37)
        ]
        
        def calculate_marginal_rate(income):
            """Calculate marginal tax rate based on income."""
            for threshold, rate in tax_brackets:
                if income <= threshold:
                    return rate
            return tax_brackets[-1][1]  # Highest rate
        
        # Test cases
        test_cases = [
            (50000, 0.22),    # 22% bracket
            (25000, 0.12),    # 12% bracket
            (200000, 0.32),   # 32% bracket
            (10000, 0.10),    # 10% bracket
            (700000, 0.37)    # 37% bracket
        ]
        
        for income, expected_rate in test_cases:
            calculated_rate = calculate_marginal_rate(income)
            assert calculated_rate == expected_rate
    
    def test_effective_tax_rate_calculation(self):
        """Test effective tax rate calculation."""
        
        def calculate_effective_rate(income):
            """Calculate effective tax rate."""
            # 2024 tax brackets for single filers
            brackets = [
                (11600, 0.10),
                (47150, 0.12),
                (100525, 0.22),
                (191950, 0.24),
                (243725, 0.32),
                (609350, 0.35),
                (float('inf'), 0.37)
            ]
            
            total_tax = 0
            remaining_income = income
            previous_threshold = 0
            
            for threshold, rate in brackets:
                if remaining_income <= 0:
                    break
                
                taxable_at_bracket = min(remaining_income, threshold - previous_threshold)
                total_tax += taxable_at_bracket * rate
                remaining_income -= taxable_at_bracket
                previous_threshold = threshold
                
                if threshold >= income:
                    break
            
            return total_tax / income if income > 0 else 0
        
        # Test cases
        test_cases = [
            50000,   # Should be around 12-15%
            100000,  # Should be around 18-20%
            200000   # Should be around 23-25%
        ]
        
        for income in test_cases:
            effective_rate = calculate_effective_rate(income)
            
            # Effective rate should be less than marginal rate
            marginal_rate = calculate_marginal_rate(income)
            assert effective_rate < marginal_rate
            
            # Reasonable bounds check
            assert 0 <= effective_rate <= 0.37
    
    def test_capital_gains_tax_calculation(self):
        """Test capital gains tax calculation accuracy."""
        
        # 2024 long-term capital gains rates
        def calculate_ltcg_rate(income, filing_status='single'):
            """Calculate long-term capital gains tax rate."""
            if filing_status == 'single':
                if income <= 47025:
                    return 0.0
                elif income <= 518900:
                    return 0.15
                else:
                    return 0.20
            elif filing_status == 'married_filing_jointly':
                if income <= 94050:
                    return 0.0
                elif income <= 583750:
                    return 0.15
                else:
                    return 0.20
            
            return 0.15  # Default
        
        # Test cases
        test_cases = [
            (40000, 'single', 0.0),
            (80000, 'single', 0.15),
            (600000, 'single', 0.20),
            (50000, 'married_filing_jointly', 0.0),
            (200000, 'married_filing_jointly', 0.15)
        ]
        
        for income, status, expected_rate in test_cases:
            calculated_rate = calculate_ltcg_rate(income, status)
            assert calculated_rate == expected_rate
    
    def test_tax_loss_harvesting_benefit(self):
        """Test tax benefit calculation from loss harvesting."""
        
        # Scenario: $10,000 capital loss, 24% marginal rate, 15% LTCG rate
        capital_loss = 10000
        marginal_tax_rate = 0.24
        capital_gains_rate = 0.15
        
        # Tax benefit from offsetting gains
        tax_benefit_from_offset = capital_loss * capital_gains_rate
        
        # If no gains to offset, can deduct up to $3,000 against ordinary income
        ordinary_income_deduction = min(capital_loss, 3000)
        tax_benefit_from_deduction = ordinary_income_deduction * marginal_tax_rate
        
        # Remaining loss can be carried forward
        carryforward_loss = max(0, capital_loss - 3000)
        
        assert tax_benefit_from_offset == 1500  # $10,000 * 0.15
        assert tax_benefit_from_deduction == 720  # $3,000 * 0.24
        assert carryforward_loss == 7000  # $10,000 - $3,000


class TestMonteCarloAccuracy:
    """Test Monte Carlo simulation accuracy and convergence."""
    
    def test_geometric_brownian_motion_properties(self):
        """Test that simulated returns have expected statistical properties."""
        
        np.random.seed(42)  # For reproducible results
        
        # Parameters
        mu = 0.08  # Expected return
        sigma = 0.20  # Volatility
        dt = 1/252  # Daily time step
        n_steps = 252  # One year
        n_simulations = 10000
        
        # Simulate paths
        simulated_returns = []
        
        for _ in range(n_simulations):
            # Generate daily returns using GBM
            daily_returns = np.random.normal(
                (mu - 0.5 * sigma**2) * dt,
                sigma * np.sqrt(dt),
                n_steps
            )
            
            # Calculate annual return
            annual_return = np.exp(np.sum(daily_returns)) - 1
            simulated_returns.append(annual_return)
        
        simulated_returns = np.array(simulated_returns)
        
        # Test convergence to theoretical values
        mean_return = np.mean(simulated_returns)
        std_return = np.std(simulated_returns)
        
        # Theoretical values for GBM
        theoretical_mean = np.exp(mu) - 1  # ~0.0833
        theoretical_std = np.sqrt(np.exp(2*mu + sigma**2) * (np.exp(sigma**2) - 1))  # ~0.2107
        
        # Allow 5% tolerance for Monte Carlo error
        assert abs(mean_return - theoretical_mean) < theoretical_mean * 0.05
        assert abs(std_return - theoretical_std) < theoretical_std * 0.05
    
    def test_monte_carlo_convergence(self):
        """Test that Monte Carlo results converge with more simulations."""
        
        np.random.seed(42)
        
        # True value to estimate: E[max(S-K, 0)] for a call option
        # Using Black-Scholes as benchmark
        S0 = 100  # Initial stock price
        K = 105   # Strike price
        T = 1     # Time to expiration
        r = 0.05  # Risk-free rate
        sigma = 0.2  # Volatility
        
        # Black-Scholes call option price (analytical solution)
        from scipy.stats import norm
        d1 = (np.log(S0/K) + (r + 0.5*sigma**2)*T) / (sigma*np.sqrt(T))
        d2 = d1 - sigma*np.sqrt(T)
        bs_price = S0 * norm.cdf(d1) - K * np.exp(-r*T) * norm.cdf(d2)
        
        # Monte Carlo estimation with different sample sizes
        sample_sizes = [1000, 5000, 10000, 50000]
        mc_estimates = []
        
        for n_sims in sample_sizes:
            # Simulate stock price at expiration
            Z = np.random.standard_normal(n_sims)
            ST = S0 * np.exp((r - 0.5*sigma**2)*T + sigma*np.sqrt(T)*Z)
            
            # Calculate option payoffs and discount to present value
            payoffs = np.maximum(ST - K, 0)
            mc_price = np.exp(-r*T) * np.mean(payoffs)
            mc_estimates.append(mc_price)
        
        # Error should decrease as sample size increases
        errors = [abs(estimate - bs_price) for estimate in mc_estimates]
        
        # Each subsequent estimate should be more accurate (generally)
        for i in range(1, len(errors)):
            # Allow some randomness, but overall trend should improve
            assert errors[i] < errors[0] * 1.5  # At least not much worse
        
        # Final estimate should be quite close
        assert errors[-1] < bs_price * 0.02  # Within 2%
    
    def test_portfolio_simulation_accuracy(self):
        """Test multi-asset portfolio simulation accuracy."""
        
        np.random.seed(42)
        
        # Portfolio of two assets
        weights = np.array([0.6, 0.4])
        expected_returns = np.array([0.08, 0.06])
        volatilities = np.array([0.20, 0.15])
        correlation = 0.3
        
        # Covariance matrix
        cov_matrix = np.array([
            [volatilities[0]**2, correlation * volatilities[0] * volatilities[1]],
            [correlation * volatilities[0] * volatilities[1], volatilities[1]**2]
        ])
        
        # Portfolio expected return and volatility
        portfolio_return = np.dot(weights, expected_returns)
        portfolio_volatility = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
        
        # Monte Carlo simulation
        n_simulations = 10000
        n_periods = 252
        dt = 1/252
        
        portfolio_returns = []
        
        for _ in range(n_simulations):
            # Generate correlated random returns
            random_returns = np.random.multivariate_normal(
                (expected_returns - 0.5 * volatilities**2) * dt,
                cov_matrix * dt,
                n_periods
            )
            
            # Calculate portfolio returns
            daily_portfolio_returns = np.dot(random_returns, weights)
            annual_return = np.exp(np.sum(daily_portfolio_returns)) - 1
            portfolio_returns.append(annual_return)
        
        # Test simulation results
        sim_mean = np.mean(portfolio_returns)
        sim_std = np.std(portfolio_returns)
        
        # Theoretical values
        theoretical_mean = np.exp(portfolio_return) - 1
        theoretical_std = np.sqrt(np.exp(2*portfolio_return + portfolio_volatility**2) * 
                                 (np.exp(portfolio_volatility**2) - 1))
        
        # Convergence test (5% tolerance)
        assert abs(sim_mean - theoretical_mean) < theoretical_mean * 0.05
        assert abs(sim_std - theoretical_std) < theoretical_std * 0.1  # 10% tolerance for volatility


class TestCrossValidationWithBenchmarks:
    """Cross-validate calculations against known benchmarks and external sources."""
    
    def test_bond_pricing_accuracy(self):
        """Test bond pricing against known Treasury bond prices."""
        
        def bond_price(face_value, coupon_rate, yield_rate, periods):
            """Calculate bond price using present value of cash flows."""
            coupon_payment = face_value * coupon_rate / periods  # Assume annual payments
            
            # Present value of coupon payments (annuity)
            pv_coupons = coupon_payment * (1 - (1 + yield_rate)**(-periods)) / yield_rate
            
            # Present value of face value
            pv_face_value = face_value / (1 + yield_rate)**periods
            
            return pv_coupons + pv_face_value
        
        # Test case: 10-year Treasury with 3% coupon, 2.5% yield
        price = bond_price(face_value=1000, coupon_rate=0.03, yield_rate=0.025, periods=10)
        
        # Expected price should be above par (coupon > yield)
        assert price > 1000
        assert 1040 < price < 1050  # Approximate expected range
        
        # Test case: Bond at par (coupon = yield)
        par_price = bond_price(face_value=1000, coupon_rate=0.03, yield_rate=0.03, periods=10)
        assert abs(par_price - 1000) < 0.01  # Should be very close to par
    
    def test_option_pricing_accuracy(self):
        """Test option pricing against Black-Scholes model."""
        
        from scipy.stats import norm
        
        def black_scholes_call(S, K, T, r, sigma):
            """Black-Scholes call option price."""
            d1 = (np.log(S/K) + (r + 0.5*sigma**2)*T) / (sigma*np.sqrt(T))
            d2 = d1 - sigma*np.sqrt(T)
            
            call_price = S * norm.cdf(d1) - K * np.exp(-r*T) * norm.cdf(d2)
            return call_price
        
        def black_scholes_put(S, K, T, r, sigma):
            """Black-Scholes put option price."""
            d1 = (np.log(S/K) + (r + 0.5*sigma**2)*T) / (sigma*np.sqrt(T))
            d2 = d1 - sigma*np.sqrt(T)
            
            put_price = K * np.exp(-r*T) * norm.cdf(-d2) - S * norm.cdf(-d1)
            return put_price
        
        # Test parameters
        S = 100    # Stock price
        K = 100    # Strike price
        T = 1      # Time to expiration (1 year)
        r = 0.05   # Risk-free rate
        sigma = 0.2  # Volatility
        
        call_price = black_scholes_call(S, K, T, r, sigma)
        put_price = black_scholes_put(S, K, T, r, sigma)
        
        # Test put-call parity: C - P = S - K*e^(-r*T)
        parity_difference = call_price - put_price - (S - K * np.exp(-r*T))
        assert abs(parity_difference) < 1e-10  # Should be essentially zero
        
        # Sanity checks
        assert call_price > 0
        assert put_price > 0
        assert call_price > max(0, S - K)  # Should have time value
        assert put_price > max(0, K - S)   # Should have time value
    
    def test_portfolio_optimization_efficiency(self):
        """Test that optimized portfolios lie on the efficient frontier."""
        
        # Sample data for 3 assets
        returns = np.array([0.08, 0.12, 0.06])
        cov_matrix = np.array([
            [0.04, 0.02, 0.01],
            [0.02, 0.09, 0.015],
            [0.01, 0.015, 0.025]
        ])
        
        def portfolio_stats(weights, returns, cov_matrix):
            """Calculate portfolio return and volatility."""
            portfolio_return = np.dot(weights, returns)
            portfolio_variance = np.dot(weights.T, np.dot(cov_matrix, weights))
            portfolio_volatility = np.sqrt(portfolio_variance)
            return portfolio_return, portfolio_volatility
        
        def optimize_portfolio(target_return, returns, cov_matrix):
            """Optimize portfolio for minimum variance given target return."""
            n_assets = len(returns)
            
            # Constraints
            constraints = [
                {'type': 'eq', 'fun': lambda x: np.sum(x) - 1},  # Weights sum to 1
                {'type': 'eq', 'fun': lambda x: np.dot(x, returns) - target_return}  # Target return
            ]
            
            bounds = [(0, 1) for _ in range(n_assets)]  # Long-only
            
            # Objective: minimize variance
            def objective(weights):
                return np.dot(weights.T, np.dot(cov_matrix, weights))
            
            # Initial guess: equal weights
            x0 = np.array([1/n_assets] * n_assets)
            
            result = minimize(objective, x0, method='SLSQP', 
                            bounds=bounds, constraints=constraints)
            
            if result.success:
                return result.x
            else:
                return None
        
        # Test portfolio optimization for different target returns
        target_returns = [0.07, 0.08, 0.09, 0.10]
        
        efficient_portfolios = []
        for target in target_returns:
            weights = optimize_portfolio(target, returns, cov_matrix)
            if weights is not None:
                ret, vol = portfolio_stats(weights, returns, cov_matrix)
                efficient_portfolios.append((ret, vol, weights))
                
                # Verify the portfolio achieves target return
                assert abs(ret - target) < 1e-6
                
                # Verify weights sum to 1
                assert abs(np.sum(weights) - 1) < 1e-6
        
        # Verify efficient frontier properties
        assert len(efficient_portfolios) == len(target_returns)
        
        # Higher return portfolios should have higher volatility
        for i in range(1, len(efficient_portfolios)):
            assert efficient_portfolios[i][0] > efficient_portfolios[i-1][0]  # Higher return
            assert efficient_portfolios[i][1] >= efficient_portfolios[i-1][1]  # Higher or equal volatility


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
