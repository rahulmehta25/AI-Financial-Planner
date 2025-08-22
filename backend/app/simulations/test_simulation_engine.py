"""
Comprehensive Unit Tests for Monte Carlo Simulation Engine

Tests all components of the simulation engine including:
- Market assumptions
- Portfolio mapping
- Monte Carlo engine
- Results calculator
- Trade-off analyzer
- Performance and accuracy validation
"""

import pytest
import numpy as np
import pandas as pd
from typing import Dict, Any
from unittest.mock import Mock, patch
import warnings

# Filter NumPy warnings that occur during testing
warnings.filterwarnings("ignore", category=RuntimeWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

from .market_assumptions import CapitalMarketAssumptions, AssetClassAssumptions
from .engine import (
    MonteCarloEngine, PortfolioAllocation, SimulationParameters,
    simulate_portfolio_paths_numba, simulate_retirement_withdrawals_numba
)
from .portfolio_mapping import (
    PortfolioMapper, RiskTolerance, ModelPortfolio, ETFMapping
)
from .results_calculator import ResultsCalculator, OutcomeMetrics
from .trade_off_analyzer import TradeOffAnalyzer, TradeOffScenario
from .logging_config import ValidationError, CalculationError


class TestCapitalMarketAssumptions:
    """Test Capital Market Assumptions functionality"""
    
    def test_initialization(self):
        """Test CMA initialization"""
        cma = CapitalMarketAssumptions()
        
        assert len(cma.asset_classes) > 0
        assert cma.correlation_matrix.shape[0] == len(cma.asset_names)
        assert np.allclose(np.diag(cma.correlation_matrix), 1.0)
        
    def test_asset_assumptions(self):
        """Test individual asset class assumptions"""
        cma = CapitalMarketAssumptions()
        
        # Test US Large Cap
        us_large_cap = cma.get_asset_assumptions("US_LARGE_CAP")
        assert isinstance(us_large_cap, AssetClassAssumptions)
        assert 0 < us_large_cap.expected_return < 0.20  # Reasonable return range
        assert 0 < us_large_cap.volatility < 0.50       # Reasonable volatility range
        
        # Test unknown asset class
        with pytest.raises(ValueError):
            cma.get_asset_assumptions("UNKNOWN_ASSET")
    
    def test_correlation_matrix(self):
        """Test correlation matrix properties"""
        cma = CapitalMarketAssumptions()
        
        # Test symmetry
        assert np.allclose(cma.correlation_matrix, cma.correlation_matrix.T)
        
        # Test diagonal elements are 1.0
        assert np.allclose(np.diag(cma.correlation_matrix), 1.0)
        
        # Test positive definite
        eigenvals = np.linalg.eigvals(cma.correlation_matrix)
        assert np.all(eigenvals > -1e-8)  # Allow for small numerical errors
        
        # Test correlation bounds
        off_diag = cma.correlation_matrix[~np.eye(len(cma.asset_names), dtype=bool)]
        assert np.all(off_diag >= -1.0)
        assert np.all(off_diag <= 1.0)
    
    def test_covariance_matrix(self):
        """Test covariance matrix calculation"""
        cma = CapitalMarketAssumptions()
        cov_matrix, asset_names = cma.get_covariance_matrix()
        
        assert cov_matrix.shape[0] == len(asset_names)
        assert cov_matrix.shape[1] == len(asset_names)
        
        # Test symmetry
        assert np.allclose(cov_matrix, cov_matrix.T)
        
        # Test positive definite
        eigenvals = np.linalg.eigvals(cov_matrix)
        assert np.all(eigenvals > -1e-8)
    
    def test_inflation_simulation(self):
        """Test inflation path simulation"""
        cma = CapitalMarketAssumptions()
        
        years = 10
        n_sims = 1000
        inflation_paths = cma.simulate_inflation_path(years, n_sims)
        
        assert inflation_paths.shape == (n_sims, years * 12)
        assert np.all(inflation_paths > 0)  # Inflation should be positive
        assert np.all(inflation_paths < 0.20)  # Reasonable upper bound
    
    def test_market_regime_updates(self):
        """Test market regime adjustments"""
        cma = CapitalMarketAssumptions()
        
        # Store original values
        orig_returns = [asset.expected_return for asset in cma.asset_classes.values()]
        orig_vols = [asset.volatility for asset in cma.asset_classes.values()]
        
        # Test bear market adjustment
        cma.update_assumptions("bear")
        bear_returns = [asset.expected_return for asset in cma.asset_classes.values()]
        bear_vols = [asset.volatility for asset in cma.asset_classes.values()]
        
        # Returns should be lower in bear market
        assert np.mean(bear_returns) < np.mean(orig_returns)
        # Volatility should be higher in bear market
        assert np.mean(bear_vols) > np.mean(orig_vols)
    
    def test_summary_statistics(self):
        """Test summary statistics generation"""
        cma = CapitalMarketAssumptions()
        stats = cma.get_summary_statistics()
        
        assert "asset_classes" in stats
        assert "expected_returns" in stats
        assert "volatilities" in stats
        assert "correlations" in stats
        assert "last_updated" in stats
        
        assert stats["asset_classes"] > 0


class TestPortfolioAllocation:
    """Test Portfolio Allocation functionality"""
    
    def test_valid_allocation(self):
        """Test valid portfolio allocation"""
        allocation = {"US_LARGE_CAP": 0.6, "CORPORATE_BONDS": 0.4}
        portfolio = PortfolioAllocation(allocation)
        
        assert portfolio.allocations == allocation
    
    def test_invalid_allocation_sum(self):
        """Test invalid allocation that doesn't sum to 1.0"""
        allocation = {"US_LARGE_CAP": 0.6, "CORPORATE_BONDS": 0.3}  # Sums to 0.9
        
        with pytest.raises(ValueError, match="must sum to 1.0"):
            PortfolioAllocation(allocation)
    
    def test_allocation_tolerance(self):
        """Test allocation tolerance for small numerical errors"""
        allocation = {"US_LARGE_CAP": 0.60001, "CORPORATE_BONDS": 0.39999}
        portfolio = PortfolioAllocation(allocation)  # Should not raise error
        
        assert portfolio.allocations == allocation


class TestPortfolioMapper:
    """Test Portfolio Mapping functionality"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.mapper = PortfolioMapper()
    
    def test_initialization(self):
        """Test portfolio mapper initialization"""
        assert len(self.mapper.model_portfolios) > 0
        assert len(self.mapper.etf_universe) > 0
        
        # Test all risk tolerance levels have portfolios
        for risk_level in RiskTolerance:
            assert risk_level in self.mapper.model_portfolios
    
    def test_model_portfolio_retrieval(self):
        """Test model portfolio retrieval"""
        # Test with RiskTolerance enum
        portfolio = self.mapper.get_model_portfolio(RiskTolerance.MODERATE)
        assert isinstance(portfolio, ModelPortfolio)
        assert portfolio.risk_level == RiskTolerance.MODERATE
        
        # Test with string
        portfolio = self.mapper.get_model_portfolio("conservative")
        assert portfolio.risk_level == RiskTolerance.CONSERVATIVE
        
        # Test invalid risk tolerance
        with pytest.raises(ValueError):
            self.mapper.get_model_portfolio("invalid")
    
    def test_age_adjusted_portfolio(self):
        """Test age-adjusted portfolio allocation"""
        # Young investor should have more equity
        young_portfolio = self.mapper.get_age_adjusted_portfolio(RiskTolerance.MODERATE, 25)
        
        # Older investor should have more bonds
        older_portfolio = self.mapper.get_age_adjusted_portfolio(RiskTolerance.MODERATE, 65)
        
        # Calculate equity allocations
        equity_assets = ["US_LARGE_CAP", "US_SMALL_CAP", "INTERNATIONAL_DEVELOPED", "EMERGING_MARKETS"]
        
        young_equity = sum(young_portfolio.allocations.get(asset, 0) for asset in equity_assets)
        older_equity = sum(older_portfolio.allocations.get(asset, 0) for asset in equity_assets)
        
        assert young_equity > older_equity
    
    def test_lifecycle_portfolio(self):
        """Test lifecycle-based portfolio allocation"""
        early_career = self.mapper.get_lifecycle_portfolio(30)
        pre_retirement = self.mapper.get_lifecycle_portfolio(60)
        
        equity_assets = ["US_LARGE_CAP", "US_SMALL_CAP", "INTERNATIONAL_DEVELOPED", "EMERGING_MARKETS"]
        
        early_equity = sum(early_career.allocations.get(asset, 0) for asset in equity_assets)
        pre_equity = sum(pre_retirement.allocations.get(asset, 0) for asset in equity_assets)
        
        assert early_equity > pre_equity
    
    def test_etf_recommendations(self):
        """Test ETF recommendation generation"""
        allocation = PortfolioAllocation({"US_LARGE_CAP": 0.7, "CORPORATE_BONDS": 0.3})
        
        recommendations = self.mapper.get_etf_recommendations(allocation)
        
        assert len(recommendations) == 2  # Should have 2 ETFs for 2 asset classes
        assert all(isinstance(etf, ETFMapping) for etf in recommendations)
    
    def test_portfolio_metrics_calculation(self):
        """Test portfolio metrics calculation"""
        allocation = PortfolioAllocation({"US_LARGE_CAP": 0.6, "CORPORATE_BONDS": 0.4})
        
        metrics = self.mapper.calculate_portfolio_metrics(allocation)
        
        assert "expected_annual_return" in metrics
        assert "expected_annual_volatility" in metrics
        assert "expected_sharpe_ratio" in metrics
        assert "equity_allocation" in metrics
        assert "bond_allocation" in metrics
        
        # Test reasonable ranges
        assert 0 < metrics["expected_annual_return"] < 0.20
        assert 0 < metrics["expected_annual_volatility"] < 0.50
    
    def test_allocation_validation(self):
        """Test portfolio allocation validation"""
        # Valid allocation
        valid_allocation = {"US_LARGE_CAP": 0.6, "CORPORATE_BONDS": 0.4}
        is_valid, errors = self.mapper.validate_allocation(valid_allocation)
        assert is_valid
        assert len(errors) == 0
        
        # Invalid allocation (doesn't sum to 1.0)
        invalid_allocation = {"US_LARGE_CAP": 0.5, "CORPORATE_BONDS": 0.4}
        is_valid, errors = self.mapper.validate_allocation(invalid_allocation)
        assert not is_valid
        assert len(errors) > 0
        
        # Negative allocation
        negative_allocation = {"US_LARGE_CAP": 0.6, "CORPORATE_BONDS": -0.1, "CASH": 0.5}
        is_valid, errors = self.mapper.validate_allocation(negative_allocation)
        assert not is_valid


class TestMonteCarloEngine:
    """Test Monte Carlo Engine functionality"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.engine = MonteCarloEngine()
        self.portfolio = PortfolioAllocation({"US_LARGE_CAP": 0.7, "CORPORATE_BONDS": 0.3})
        self.parameters = SimulationParameters(
            n_simulations=1000,  # Smaller for faster tests
            years_to_retirement=10,
            retirement_years=15,
            initial_portfolio_value=50000,
            annual_contribution=5000
        )
    
    def test_initialization(self):
        """Test engine initialization"""
        assert self.engine.market_assumptions is not None
        assert self.engine.last_simulation_time is None
        assert self.engine.last_simulation_results is None
    
    def test_input_validation(self):
        """Test input validation"""
        # Valid inputs should not raise error
        self.engine._validate_simulation_inputs(self.portfolio, self.parameters)
        
        # Invalid parameters
        invalid_params = SimulationParameters(n_simulations=-100)
        with pytest.raises(ValidationError):
            self.engine._validate_simulation_inputs(self.portfolio, invalid_params)
        
        # Invalid portfolio
        invalid_portfolio = PortfolioAllocation({"US_LARGE_CAP": 0.5})  # Doesn't sum to 1.0
        with pytest.raises(ValidationError):
            self.engine._validate_simulation_inputs(invalid_portfolio, self.parameters)
    
    def test_simulation_execution(self):
        """Test full simulation execution"""
        results = self.engine.run_simulation(self.portfolio, self.parameters)
        
        # Test result structure
        assert "success_probability" in results
        assert "simulation_metadata" in results
        assert "raw_results" in results
        
        # Test metadata
        metadata = results["simulation_metadata"]
        assert metadata["n_simulations"] == self.parameters.n_simulations
        assert metadata["years_to_retirement"] == self.parameters.years_to_retirement
        
        # Test raw results
        raw_results = results["raw_results"]
        assert "retirement_balances" in raw_results
        assert "final_balances" in raw_results
        
        # Test result dimensions
        assert len(raw_results["retirement_balances"]) == self.parameters.n_simulations
        assert len(raw_results["final_balances"]) == self.parameters.n_simulations
        
        # Test result reasonableness
        retirement_balances = np.array(raw_results["retirement_balances"])
        assert np.all(retirement_balances >= 0)  # Balances should be non-negative
        assert np.mean(retirement_balances) > self.parameters.initial_portfolio_value  # Should grow
    
    def test_reproducibility(self):
        """Test simulation reproducibility with random seed"""
        params1 = SimulationParameters(n_simulations=100, random_seed=42)
        params2 = SimulationParameters(n_simulations=100, random_seed=42)
        
        results1 = self.engine.run_simulation(self.portfolio, params1)
        results2 = self.engine.run_simulation(self.portfolio, params2)
        
        # Results should be identical with same seed
        assert np.allclose(
            results1["raw_results"]["retirement_balances"],
            results2["raw_results"]["retirement_balances"]
        )
    
    def test_performance_metrics(self):
        """Test performance metrics tracking"""
        self.engine.run_simulation(self.portfolio, self.parameters)
        
        metrics = self.engine.get_performance_metrics()
        
        assert "last_simulation_time_seconds" in metrics
        assert "simulations_per_second" in metrics
        assert "performance_target_met" in metrics
        
        # Performance should be reasonable
        assert metrics["last_simulation_time_seconds"] > 0
        assert metrics["simulations_per_second"] > 0
    
    def test_stress_testing(self):
        """Test stress testing functionality"""
        stress_results = self.engine.run_stress_test(
            self.portfolio, 
            self.parameters,
            stress_scenarios=["bear"]
        )
        
        assert "baseline" in stress_results
        assert "bear" in stress_results
        
        # Bear market should generally have lower success rates
        baseline_success = stress_results["baseline"]["success_probability"]
        bear_success = stress_results["bear"]["success_probability"]
        
        # Allow some flexibility as results can vary with small sample sizes
        assert bear_success <= baseline_success + 0.1


class TestNumbaFunctions:
    """Test Numba-compiled functions directly"""
    
    def test_portfolio_paths_simulation(self):
        """Test Numba portfolio paths simulation"""
        # Setup test data
        expected_returns = np.array([0.08, 0.04])
        covariance_matrix = np.array([[0.02, 0.005], [0.005, 0.01]])
        portfolio_weights = np.array([0.7, 0.3])
        n_simulations = 100
        n_years = 5
        initial_value = 10000.0
        monthly_contributions = np.full(60, 500.0)  # 60 months of $500
        
        # Run simulation
        paths = simulate_portfolio_paths_numba(
            expected_returns=expected_returns,
            covariance_matrix=covariance_matrix,
            portfolio_weights=portfolio_weights,
            n_simulations=n_simulations,
            n_years=n_years,
            initial_value=initial_value,
            monthly_contributions=monthly_contributions,
            rebalance_frequency=12
        )
        
        # Test output dimensions
        assert paths.shape == (n_simulations, n_years * 12)
        
        # Test initial values
        assert np.allclose(paths[:, 0], initial_value)
        
        # Test that values generally increase (due to contributions and returns)
        assert np.mean(paths[:, -1]) > initial_value
    
    def test_retirement_withdrawals_simulation(self):
        """Test Numba retirement withdrawals simulation"""
        # Create simple portfolio paths
        n_sims = 50
        n_months = 120  # 10 years
        portfolio_paths = np.zeros((n_sims, n_months))
        
        # Fill with declining values (simplified retirement simulation)
        for i in range(n_sims):
            portfolio_paths[i, :] = 100000 * np.exp(-0.03 * np.arange(n_months) / 12)
        
        retirement_start_month = 60  # Start retirement at month 60
        initial_withdrawal_rate = 0.04
        inflation_paths = np.full((n_sims, 60), 0.025)  # 2.5% inflation
        
        final_balances, withdrawals = simulate_retirement_withdrawals_numba(
            portfolio_paths=portfolio_paths,
            retirement_start_month=retirement_start_month,
            initial_withdrawal_rate=initial_withdrawal_rate,
            inflation_paths=inflation_paths
        )
        
        # Test output dimensions
        assert len(final_balances) == n_sims
        assert withdrawals.shape[0] == n_sims
        
        # Test that withdrawals are positive
        assert np.all(withdrawals >= 0)
        
        # Test that final balances are non-negative
        assert np.all(final_balances >= 0)


class TestResultsCalculator:
    """Test Results Calculator functionality"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.calculator = ResultsCalculator()
        
        # Create mock simulation results
        self.mock_results = {
            "simulation_metadata": {
                "n_simulations": 1000,
                "years_to_retirement": 30,
                "retirement_years": 25
            },
            "raw_results": {
                "retirement_balances": np.random.lognormal(13, 0.5, 1000).tolist(),  # Log-normal distribution
                "final_balances": np.random.lognormal(12, 0.8, 1000).tolist()
            },
            "success_probability": 0.85
        }
    
    def test_comprehensive_results_calculation(self):
        """Test comprehensive results calculation"""
        results = self.calculator.calculate_comprehensive_results(self.mock_results)
        
        # Test main sections
        assert "outcome_metrics" in results
        assert "risk_metrics" in results
        assert "return_metrics" in results
        assert "withdrawal_analysis" in results
        assert "scenario_analysis" in results
        assert "goal_probabilities" in results
        assert "metadata" in results
        
        # Test outcome metrics
        outcome = results["outcome_metrics"]
        assert "success_probability" in outcome
        assert "percentiles" in outcome
        assert "expected_shortfall" in outcome
        
        # Test that percentiles are ordered correctly
        percentiles = outcome["percentiles"]
        p10 = percentiles["percentile_10"]
        p50 = percentiles["percentile_50"]
        p90 = percentiles["percentile_90"]
        
        assert p10 <= p50 <= p90
    
    def test_risk_metrics_calculation(self):
        """Test risk metrics calculation"""
        results = self.calculator.calculate_comprehensive_results(self.mock_results)
        risk_metrics = results["risk_metrics"]
        
        assert "value_at_risk_5" in risk_metrics
        assert "conditional_var_5" in risk_metrics
        assert "volatility" in risk_metrics
        assert "downside_deviation" in risk_metrics
        assert "sortino_ratio" in risk_metrics
        
        # Test that VaR is less than conditional VaR
        assert risk_metrics["value_at_risk_5"] >= risk_metrics["conditional_var_5"]
    
    def test_scenario_comparison(self):
        """Test scenario comparison functionality"""
        # Create alternative results
        alternative_results = self.mock_results.copy()
        alternative_results["raw_results"]["retirement_balances"] = (
            np.array(self.mock_results["raw_results"]["retirement_balances"]) * 1.1
        ).tolist()
        
        comparison = self.calculator.compare_scenarios(
            self.mock_results, alternative_results, "Alternative"
        )
        
        assert "scenario_name" in comparison
        assert "statistical_significance" in comparison
        assert "improvement_metrics" in comparison
        assert "relative_performance" in comparison
        
        # Test that improvement is positive (alternative has higher balances)
        assert comparison["improvement_metrics"]["median_balance_improvement_pct"] > 0
    
    def test_summary_report_generation(self):
        """Test summary report generation"""
        comprehensive_results = self.calculator.calculate_comprehensive_results(self.mock_results)
        report = self.calculator.generate_summary_report(comprehensive_results)
        
        assert isinstance(report, str)
        assert len(report) > 100  # Should be a substantial report
        assert "SUCCESS PROBABILITY" in report
        assert "EXPECTED OUTCOMES" in report
        assert "RISK ANALYSIS" in report


class TestTradeOffAnalyzer:
    """Test Trade-Off Analyzer functionality"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.analyzer = TradeOffAnalyzer()
        self.portfolio = PortfolioAllocation({"US_LARGE_CAP": 0.7, "CORPORATE_BONDS": 0.3})
        self.parameters = SimulationParameters(
            n_simulations=500,  # Smaller for faster tests
            years_to_retirement=20,
            annual_contribution=10000
        )
    
    def test_initialization(self):
        """Test trade-off analyzer initialization"""
        assert self.analyzer.engine is not None
        assert self.analyzer.results_calc is not None
        assert len(self.analyzer.scenario_templates) > 0
    
    def test_scenario_templates(self):
        """Test scenario templates"""
        templates = self.analyzer.scenario_templates
        
        # Test that key scenarios exist
        assert "increase_savings_3pct" in templates
        assert "delay_retirement_2yr" in templates
        assert "reduce_spending_10pct" in templates
        
        # Test template structure
        for scenario in templates.values():
            assert hasattr(scenario, 'name')
            assert hasattr(scenario, 'description')
            assert hasattr(scenario, 'parameter_changes')
            assert hasattr(scenario, 'expected_impact')
    
    def test_specific_tradeoff_analysis(self):
        """Test analysis of specific trade-off scenario"""
        custom_scenario = TradeOffScenario(
            name="Test Increase Savings",
            description="Increase savings by 20%",
            parameter_changes={"contribution_multiplier": 1.2},
            expected_impact="positive"
        )
        
        results = self.analyzer.analyze_specific_tradeoff(
            self.portfolio, self.parameters, custom_scenario
        )
        
        assert "scenario_details" in results
        assert "baseline_results" in results
        assert "scenario_results" in results
        assert "comparison" in results
        assert "trade_off_metrics" in results
        assert "recommendation" in results
        
        # Test that increased savings generally improves outcomes
        comparison = results["comparison"]
        # Allow for some variability in small sample tests
        assert comparison["improvement_metrics"]["success_rate_improvement"] >= -0.1
    
    @pytest.mark.slow
    def test_comprehensive_tradeoff_analysis(self):
        """Test comprehensive trade-off analysis (marked as slow)"""
        # Use even smaller parameters for this comprehensive test
        fast_parameters = SimulationParameters(
            n_simulations=100,
            years_to_retirement=10,
            annual_contribution=5000
        )
        
        results = self.analyzer.run_comprehensive_tradeoff_analysis(
            self.portfolio,
            fast_parameters,
            scenarios_to_analyze=["increase_savings_3pct"]
        )
        
        assert "baseline_results" in results
        assert "scenario_results" in results
        assert "trade_off_comparisons" in results
        assert "trade_off_summary" in results
        assert "recommendations" in results
        
        # Test that at least one scenario was analyzed
        assert len(results["scenario_results"]) >= 1
    
    def test_portfolio_adjustments(self):
        """Test portfolio adjustment functionality"""
        # Test making portfolio more aggressive
        conservative_portfolio = PortfolioAllocation({
            "US_LARGE_CAP": 0.3,
            "CORPORATE_BONDS": 0.7
        })
        
        aggressive_portfolio = self.analyzer._make_portfolio_more_aggressive(conservative_portfolio)
        
        # Should have more equity, less bonds
        equity_assets = ["US_LARGE_CAP", "US_SMALL_CAP", "INTERNATIONAL_DEVELOPED", "EMERGING_MARKETS"]
        bond_assets = ["US_TREASURY_LONG", "US_TREASURY_INTERMEDIATE", "CORPORATE_BONDS", "HIGH_YIELD_BONDS"]
        
        orig_equity = sum(conservative_portfolio.allocations.get(asset, 0) for asset in equity_assets)
        new_equity = sum(aggressive_portfolio.allocations.get(asset, 0) for asset in equity_assets)
        
        assert new_equity >= orig_equity
        
        # Test making portfolio more conservative
        aggressive_input = PortfolioAllocation({"US_LARGE_CAP": 0.8, "CORPORATE_BONDS": 0.2})
        conservative_output = self.analyzer._make_portfolio_more_conservative(aggressive_input)
        
        orig_equity = sum(aggressive_input.allocations.get(asset, 0) for asset in equity_assets)
        new_equity = sum(conservative_output.allocations.get(asset, 0) for asset in equity_assets)
        
        assert new_equity <= orig_equity


class TestIntegration:
    """Integration tests for the complete simulation system"""
    
    def test_end_to_end_simulation(self):
        """Test complete end-to-end simulation workflow"""
        # Setup components
        mapper = PortfolioMapper()
        engine = MonteCarloEngine()
        calculator = ResultsCalculator()
        
        # Get a model portfolio
        portfolio_allocation = mapper.get_age_adjusted_portfolio(RiskTolerance.MODERATE, 35)
        
        # Setup parameters
        parameters = SimulationParameters(
            n_simulations=500,  # Reasonable size for integration test
            years_to_retirement=25,
            initial_portfolio_value=25000,
            annual_contribution=8000
        )
        
        # Run simulation
        sim_results = engine.run_simulation(portfolio_allocation, parameters)
        
        # Calculate comprehensive results
        comprehensive_results = calculator.calculate_comprehensive_results(sim_results)
        
        # Test that all components worked together
        assert sim_results["success_probability"] > 0
        assert comprehensive_results["outcome_metrics"]["success_probability"] > 0
        assert len(comprehensive_results["goal_probabilities"]) > 0
        
        # Test performance
        performance = engine.get_performance_metrics()
        assert performance["last_simulation_time_seconds"] < 30  # Should meet performance target
    
    def test_realistic_retirement_scenario(self):
        """Test realistic retirement planning scenario"""
        mapper = PortfolioMapper()
        engine = MonteCarloEngine()
        
        # 35-year-old professional saving for retirement
        portfolio = mapper.get_age_adjusted_portfolio(RiskTolerance.MODERATELY_AGGRESSIVE, 35)
        
        parameters = SimulationParameters(
            n_simulations=1000,
            years_to_retirement=30,
            retirement_years=25,
            initial_portfolio_value=75000,      # Some existing savings
            annual_contribution=15000,          # $15k/year contributions
            contribution_growth_rate=0.03,      # 3% annual increases
            withdrawal_rate=0.04                # 4% withdrawal rule
        )
        
        results = engine.run_simulation(portfolio, parameters)
        
        # Test reasonable outcomes for this scenario
        assert results["success_probability"] > 0.50  # Should have decent success rate
        
        retirement_balances = np.array(results["raw_results"]["retirement_balances"])
        median_balance = np.median(retirement_balances)
        
        # Should accumulate substantial wealth over 30 years
        assert median_balance > parameters.initial_portfolio_value * 3
        
        # Test that most outcomes are positive
        assert np.mean(retirement_balances > 0) > 0.95


# Performance benchmarks
class TestPerformance:
    """Performance tests to ensure the engine meets speed requirements"""
    
    @pytest.mark.slow
    def test_50k_simulation_performance(self):
        """Test that 50,000 simulations complete within 30 seconds"""
        engine = MonteCarloEngine()
        portfolio = PortfolioAllocation({"US_LARGE_CAP": 0.6, "CORPORATE_BONDS": 0.4})
        parameters = SimulationParameters(n_simulations=50_000)
        
        import time
        start_time = time.time()
        results = engine.run_simulation(portfolio, parameters)
        end_time = time.time()
        
        simulation_time = end_time - start_time
        
        # Should meet the 30-second target
        assert simulation_time < 30.0, f"Simulation took {simulation_time:.2f} seconds, target is 30s"
        
        # Should have high success rate for reasonable scenario
        assert results["success_probability"] > 0.50
    
    def test_memory_efficiency(self):
        """Test memory efficiency of large simulations"""
        engine = MonteCarloEngine()
        portfolio = PortfolioAllocation({"US_LARGE_CAP": 0.8, "CASH": 0.2})
        parameters = SimulationParameters(n_simulations=10_000)
        
        # This test mainly ensures no memory errors occur
        results = engine.run_simulation(portfolio, parameters)
        
        assert len(results["raw_results"]["retirement_balances"]) == 10_000
        assert len(results["raw_results"]["final_balances"]) == 10_000


# Fixtures and utilities for tests
@pytest.fixture
def sample_portfolio():
    """Sample portfolio allocation for testing"""
    return PortfolioAllocation({
        "US_LARGE_CAP": 0.5,
        "INTERNATIONAL_DEVELOPED": 0.2,
        "CORPORATE_BONDS": 0.3
    })


@pytest.fixture
def sample_parameters():
    """Sample simulation parameters for testing"""
    return SimulationParameters(
        n_simulations=100,  # Small for fast tests
        years_to_retirement=15,
        retirement_years=20,
        annual_contribution=6000
    )


# Custom pytest markers
def pytest_configure(config):
    """Configure custom pytest markers"""
    config.addinivalue_line("markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')")


if __name__ == "__main__":
    # Run specific test classes for development
    pytest.main([
        __file__ + "::TestCapitalMarketAssumptions",
        "-v"
    ])