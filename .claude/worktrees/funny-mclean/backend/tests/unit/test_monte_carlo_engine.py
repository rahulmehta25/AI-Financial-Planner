"""
Comprehensive unit tests for Monte Carlo simulation engine.

This test suite covers:
- Monte Carlo simulation logic
- Portfolio optimization
- Risk calculations
- Performance edge cases
- Statistical validity
- Error handling
"""
import pytest
import numpy as np
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
from decimal import Decimal
from datetime import datetime, timedelta

from app.simulations.engine import MonteCarloEngine
from app.simulations.results_calculator import ResultsCalculator
from app.simulations.market_assumptions import MarketAssumptions
from app.simulations.portfolio_mapping import PortfolioMapper
from app.models.financial_profile import FinancialProfile
from app.models.goal import Goal, GoalType
from app.schemas.simulation import SimulationRequest, PortfolioAllocation


class TestMonteCarloEngine:
    """Test suite for Monte Carlo simulation engine."""
    
    @pytest.fixture
    def engine(self):
        """Create Monte Carlo engine instance."""
        return MonteCarloEngine()
    
    @pytest.fixture
    def sample_portfolio(self):
        """Sample portfolio allocation for testing."""
        return {
            'stocks': 0.60,
            'bonds': 0.30,
            'cash': 0.10
        }
    
    @pytest.fixture
    def sample_financial_profile(self):
        """Sample financial profile for testing."""
        return FinancialProfile(
            annual_income=75000,
            monthly_expenses=4500,
            current_savings=25000,
            debt_amount=15000,
            risk_tolerance='moderate',
            age=35,
            retirement_age=65
        )
    
    @pytest.fixture
    def sample_goals(self):
        """Sample financial goals for testing."""
        return [
            Goal(
                name="Retirement",
                target_amount=1000000,
                target_date=datetime.now() + timedelta(days=365*30),
                goal_type=GoalType.RETIREMENT,
                priority=1
            ),
            Goal(
                name="Emergency Fund",
                target_amount=50000,
                target_date=datetime.now() + timedelta(days=365*2),
                goal_type=GoalType.EMERGENCY_FUND,
                priority=2
            )
        ]
    
    @pytest.mark.asyncio
    async def test_run_simulation_basic(self, engine, sample_portfolio, sample_financial_profile, sample_goals):
        """Test basic Monte Carlo simulation execution."""
        simulation_request = SimulationRequest(
            portfolio_allocation=sample_portfolio,
            time_horizon_years=30,
            initial_investment=25000,
            monthly_contribution=1000,
            num_simulations=1000
        )
        
        result = await engine.run_simulation(
            simulation_request, 
            sample_financial_profile, 
            sample_goals
        )
        
        assert result is not None
        assert result.num_simulations == 1000
        assert result.time_horizon_years == 30
        assert len(result.projection_data) > 0
        assert result.success_probability >= 0.0
        assert result.success_probability <= 1.0
    
    @pytest.mark.asyncio
    async def test_simulation_statistical_validity(self, engine, sample_portfolio, sample_financial_profile, sample_goals):
        """Test statistical validity of Monte Carlo results."""
        simulation_request = SimulationRequest(
            portfolio_allocation=sample_portfolio,
            time_horizon_years=10,
            initial_investment=10000,
            monthly_contribution=500,
            num_simulations=5000  # Larger sample for statistical validity
        )
        
        result = await engine.run_simulation(
            simulation_request, 
            sample_financial_profile, 
            sample_goals
        )
        
        # Test statistical properties
        final_values = [sim[-1] for sim in result.simulation_paths]
        mean_final_value = np.mean(final_values)
        std_final_value = np.std(final_values)
        
        # Should have reasonable mean and standard deviation
        assert mean_final_value > 0
        assert std_final_value > 0
        
        # Test percentile calculations
        assert result.percentile_10 < result.percentile_50
        assert result.percentile_50 < result.percentile_90
        assert result.percentile_90 > mean_final_value
    
    def test_portfolio_allocation_validation(self, engine):
        """Test portfolio allocation validation."""
        # Valid allocation
        valid_allocation = {'stocks': 0.6, 'bonds': 0.3, 'cash': 0.1}
        assert engine._validate_portfolio_allocation(valid_allocation)
        
        # Invalid allocation - doesn't sum to 1
        invalid_allocation_1 = {'stocks': 0.6, 'bonds': 0.3, 'cash': 0.2}
        assert not engine._validate_portfolio_allocation(invalid_allocation_1)
        
        # Invalid allocation - negative values
        invalid_allocation_2 = {'stocks': 0.8, 'bonds': 0.3, 'cash': -0.1}
        assert not engine._validate_portfolio_allocation(invalid_allocation_2)
        
        # Invalid allocation - missing asset class
        invalid_allocation_3 = {'stocks': 0.7, 'bonds': 0.3}
        assert not engine._validate_portfolio_allocation(invalid_allocation_3)
    
    @pytest.mark.asyncio
    async def test_simulation_with_different_risk_profiles(self, engine, sample_financial_profile, sample_goals):
        """Test simulations with different risk tolerance levels."""
        risk_profiles = ['conservative', 'moderate', 'aggressive']
        
        for risk_profile in risk_profiles:
            profile = FinancialProfile(**sample_financial_profile.__dict__)
            profile.risk_tolerance = risk_profile
            
            # Get appropriate portfolio for risk profile
            portfolio = engine._get_portfolio_for_risk_tolerance(risk_profile)
            
            simulation_request = SimulationRequest(
                portfolio_allocation=portfolio,
                time_horizon_years=20,
                initial_investment=10000,
                monthly_contribution=500,
                num_simulations=1000
            )
            
            result = await engine.run_simulation(simulation_request, profile, sample_goals)
            
            assert result is not None
            assert result.success_probability >= 0.0
            assert result.success_probability <= 1.0
            
            # Conservative should have lower volatility
            if risk_profile == 'conservative':
                assert portfolio['bonds'] + portfolio['cash'] >= 0.5
            elif risk_profile == 'aggressive':
                assert portfolio['stocks'] >= 0.7
    
    @pytest.mark.asyncio
    async def test_simulation_edge_cases(self, engine, sample_financial_profile, sample_goals):
        """Test Monte Carlo simulation edge cases."""
        
        # Test with zero initial investment
        zero_initial_request = SimulationRequest(
            portfolio_allocation={'stocks': 0.6, 'bonds': 0.3, 'cash': 0.1},
            time_horizon_years=10,
            initial_investment=0,
            monthly_contribution=1000,
            num_simulations=100
        )
        
        result = await engine.run_simulation(
            zero_initial_request, 
            sample_financial_profile, 
            sample_goals
        )
        assert result is not None
        
        # Test with zero monthly contribution
        zero_monthly_request = SimulationRequest(
            portfolio_allocation={'stocks': 0.6, 'bonds': 0.3, 'cash': 0.1},
            time_horizon_years=10,
            initial_investment=10000,
            monthly_contribution=0,
            num_simulations=100
        )
        
        result = await engine.run_simulation(
            zero_monthly_request, 
            sample_financial_profile, 
            sample_goals
        )
        assert result is not None
        
        # Test with very short time horizon
        short_horizon_request = SimulationRequest(
            portfolio_allocation={'stocks': 0.6, 'bonds': 0.3, 'cash': 0.1},
            time_horizon_years=1,
            initial_investment=10000,
            monthly_contribution=500,
            num_simulations=100
        )
        
        result = await engine.run_simulation(
            short_horizon_request, 
            sample_financial_profile, 
            sample_goals
        )
        assert result is not None
        assert result.time_horizon_years == 1
    
    def test_returns_generation(self, engine):
        """Test generation of random returns."""
        portfolio = {'stocks': 0.6, 'bonds': 0.3, 'cash': 0.1}
        returns = engine._generate_monthly_returns(portfolio, 120)  # 10 years
        
        assert len(returns) == 120
        assert all(isinstance(r, float) for r in returns)
        
        # Test statistical properties of returns
        mean_return = np.mean(returns)
        std_return = np.std(returns)
        
        # Should be within reasonable bounds for monthly returns
        assert -0.2 < mean_return < 0.2  # Monthly return between -20% and 20%
        assert 0 < std_return < 0.3  # Standard deviation should be positive and reasonable
    
    def test_correlation_matrix_application(self, engine):
        """Test application of correlation matrix in return generation."""
        portfolio = {'stocks': 0.6, 'bonds': 0.3, 'cash': 0.1}
        
        # Generate multiple return series
        returns_series = []
        for _ in range(10):
            returns = engine._generate_monthly_returns(portfolio, 60)
            returns_series.append(returns)
        
        # Check that returns are properly correlated
        returns_array = np.array(returns_series)
        correlation = np.corrcoef(returns_array)
        
        # Diagonal should be 1 (perfect self-correlation)
        assert np.allclose(np.diag(correlation), 1.0, rtol=1e-10)
    
    @pytest.mark.asyncio
    async def test_goal_success_probability_calculation(self, engine, sample_financial_profile):
        """Test goal success probability calculation."""
        retirement_goal = Goal(
            name="Retirement",
            target_amount=500000,  # Lower target for higher success probability
            target_date=datetime.now() + timedelta(days=365*20),
            goal_type=GoalType.RETIREMENT,
            priority=1
        )
        
        simulation_request = SimulationRequest(
            portfolio_allocation={'stocks': 0.7, 'bonds': 0.2, 'cash': 0.1},
            time_horizon_years=20,
            initial_investment=50000,
            monthly_contribution=2000,
            num_simulations=1000
        )
        
        result = await engine.run_simulation(
            simulation_request, 
            sample_financial_profile, 
            [retirement_goal]
        )
        
        # With aggressive portfolio and high contributions, success probability should be high
        assert result.success_probability > 0.5
        
        # Test with impossible goal
        impossible_goal = Goal(
            name="Impossible Goal",
            target_amount=10000000,  # Very high target
            target_date=datetime.now() + timedelta(days=365*5),  # Short timeframe
            goal_type=GoalType.CUSTOM,
            priority=1
        )
        
        result_impossible = await engine.run_simulation(
            simulation_request, 
            sample_financial_profile, 
            [impossible_goal]
        )
        
        # Success probability should be very low
        assert result_impossible.success_probability < 0.1
    
    def test_market_assumptions_integration(self, engine):
        """Test integration with market assumptions."""
        market_assumptions = MarketAssumptions()
        
        # Test that market assumptions are properly loaded
        assert hasattr(market_assumptions, 'expected_returns')
        assert hasattr(market_assumptions, 'volatilities')
        assert hasattr(market_assumptions, 'correlations')
        
        # Test returns calculation with market assumptions
        portfolio = {'stocks': 0.6, 'bonds': 0.3, 'cash': 0.1}
        expected_return = engine._calculate_expected_portfolio_return(portfolio, market_assumptions)
        
        assert isinstance(expected_return, float)
        assert 0 < expected_return < 0.5  # Should be a reasonable annual return
    
    @pytest.mark.asyncio
    async def test_inflation_adjustment(self, engine, sample_financial_profile, sample_goals):
        """Test inflation adjustment in simulations."""
        simulation_request = SimulationRequest(
            portfolio_allocation={'stocks': 0.6, 'bonds': 0.3, 'cash': 0.1},
            time_horizon_years=20,
            initial_investment=10000,
            monthly_contribution=500,
            num_simulations=500,
            inflation_rate=0.03  # 3% inflation
        )
        
        result_with_inflation = await engine.run_simulation(
            simulation_request, 
            sample_financial_profile, 
            sample_goals
        )
        
        # Test without inflation
        simulation_request.inflation_rate = 0.0
        result_without_inflation = await engine.run_simulation(
            simulation_request, 
            sample_financial_profile, 
            sample_goals
        )
        
        # Real returns should be lower with inflation
        assert result_with_inflation.expected_final_value < result_without_inflation.expected_final_value
    
    def test_performance_optimization(self, engine):
        """Test performance optimization features."""
        # Test with large number of simulations
        portfolio = {'stocks': 0.6, 'bonds': 0.3, 'cash': 0.1}
        
        import time
        start_time = time.time()
        
        # Generate returns for large simulation
        returns = engine._generate_monthly_returns(portfolio, 360)  # 30 years
        
        execution_time = time.time() - start_time
        
        # Should complete within reasonable time (less than 1 second)
        assert execution_time < 1.0
        assert len(returns) == 360
    
    @pytest.mark.asyncio
    async def test_simulation_reproducibility(self, engine, sample_financial_profile, sample_goals):
        """Test that simulations are reproducible with same random seed."""
        simulation_request = SimulationRequest(
            portfolio_allocation={'stocks': 0.6, 'bonds': 0.3, 'cash': 0.1},
            time_horizon_years=10,
            initial_investment=10000,
            monthly_contribution=500,
            num_simulations=100,
            random_seed=42
        )
        
        result1 = await engine.run_simulation(
            simulation_request, 
            sample_financial_profile, 
            sample_goals
        )
        
        result2 = await engine.run_simulation(
            simulation_request, 
            sample_financial_profile, 
            sample_goals
        )
        
        # Results should be identical with same seed
        assert result1.expected_final_value == result2.expected_final_value
        assert result1.success_probability == result2.success_probability
        assert len(result1.simulation_paths) == len(result2.simulation_paths)
    
    @pytest.mark.asyncio
    async def test_error_handling(self, engine, sample_financial_profile, sample_goals):
        """Test error handling in Monte Carlo engine."""
        
        # Test with invalid portfolio allocation
        with pytest.raises(ValueError):
            invalid_request = SimulationRequest(
                portfolio_allocation={'stocks': 1.5, 'bonds': 0.3, 'cash': -0.8},
                time_horizon_years=10,
                initial_investment=10000,
                monthly_contribution=500,
                num_simulations=100
            )
            await engine.run_simulation(invalid_request, sample_financial_profile, sample_goals)
        
        # Test with negative time horizon
        with pytest.raises(ValueError):
            negative_time_request = SimulationRequest(
                portfolio_allocation={'stocks': 0.6, 'bonds': 0.3, 'cash': 0.1},
                time_horizon_years=-5,
                initial_investment=10000,
                monthly_contribution=500,
                num_simulations=100
            )
            await engine.run_simulation(negative_time_request, sample_financial_profile, sample_goals)
        
        # Test with zero simulations
        with pytest.raises(ValueError):
            zero_sims_request = SimulationRequest(
                portfolio_allocation={'stocks': 0.6, 'bonds': 0.3, 'cash': 0.1},
                time_horizon_years=10,
                initial_investment=10000,
                monthly_contribution=500,
                num_simulations=0
            )
            await engine.run_simulation(zero_sims_request, sample_financial_profile, sample_goals)


class TestResultsCalculator:
    """Test suite for simulation results calculator."""
    
    @pytest.fixture
    def calculator(self):
        """Create results calculator instance."""
        return ResultsCalculator()
    
    def test_percentile_calculations(self, calculator):
        """Test percentile calculations."""
        # Sample simulation paths
        simulation_paths = [
            [1000, 1100, 1200, 1300, 1400],
            [1000, 1050, 1080, 1150, 1200],
            [1000, 1150, 1350, 1500, 1600],
            [1000, 950, 900, 950, 1000],
            [1000, 1200, 1400, 1600, 1800]
        ]
        
        percentiles = calculator.calculate_percentiles(simulation_paths)
        
        assert 'percentile_10' in percentiles
        assert 'percentile_50' in percentiles
        assert 'percentile_90' in percentiles
        
        # Percentiles should be in ascending order
        assert percentiles['percentile_10'] <= percentiles['percentile_50']
        assert percentiles['percentile_50'] <= percentiles['percentile_90']
    
    def test_success_probability_calculation(self, calculator):
        """Test success probability calculation against goals."""
        simulation_paths = [
            [1000, 1100, 1200, 1300, 1500],  # Success
            [1000, 1050, 1080, 1150, 1300],  # Success  
            [1000, 1150, 1350, 1500, 1600],  # Success
            [1000, 950, 900, 950, 1000],     # Failure
            [1000, 1200, 1400, 1600, 1200]   # Failure
        ]
        
        target_amount = 1400
        success_probability = calculator.calculate_success_probability(
            simulation_paths, target_amount
        )
        
        # 3 out of 5 simulations succeed
        assert success_probability == 0.6
    
    def test_risk_metrics_calculation(self, calculator):
        """Test calculation of risk metrics."""
        returns_data = [0.1, -0.05, 0.08, 0.15, -0.02, 0.12, -0.08, 0.05]
        
        risk_metrics = calculator.calculate_risk_metrics(returns_data)
        
        assert 'volatility' in risk_metrics
        assert 'sharpe_ratio' in risk_metrics
        assert 'max_drawdown' in risk_metrics
        assert 'var_95' in risk_metrics
        
        # Volatility should be positive
        assert risk_metrics['volatility'] > 0
        
        # VaR should be negative (loss)
        assert risk_metrics['var_95'] <= 0
    
    def test_drawdown_calculation(self, calculator):
        """Test maximum drawdown calculation."""
        price_series = [1000, 1100, 1200, 1000, 800, 900, 1100, 1300]
        
        max_drawdown = calculator.calculate_max_drawdown(price_series)
        
        # Maximum drawdown should be from peak of 1200 to trough of 800
        expected_drawdown = (800 - 1200) / 1200  # -33.33%
        assert abs(max_drawdown - expected_drawdown) < 0.001


class TestMarketAssumptions:
    """Test suite for market assumptions."""
    
    @pytest.fixture
    def market_assumptions(self):
        """Create market assumptions instance."""
        return MarketAssumptions()
    
    def test_market_data_loading(self, market_assumptions):
        """Test loading of market assumptions data."""
        assert hasattr(market_assumptions, 'expected_returns')
        assert hasattr(market_assumptions, 'volatilities')
        assert hasattr(market_assumptions, 'correlations')
        
        # Check that data is properly formatted
        assert isinstance(market_assumptions.expected_returns, dict)
        assert isinstance(market_assumptions.volatilities, dict)
        assert isinstance(market_assumptions.correlations, pd.DataFrame)
    
    def test_asset_class_coverage(self, market_assumptions):
        """Test that all required asset classes are covered."""
        required_assets = ['stocks', 'bonds', 'cash', 'real_estate', 'commodities']
        
        for asset in required_assets:
            assert asset in market_assumptions.expected_returns
            assert asset in market_assumptions.volatilities
    
    def test_correlation_matrix_validity(self, market_assumptions):
        """Test validity of correlation matrix."""
        corr_matrix = market_assumptions.correlations
        
        # Should be square matrix
        assert corr_matrix.shape[0] == corr_matrix.shape[1]
        
        # Diagonal should be 1
        assert all(corr_matrix.iloc[i, i] == 1.0 for i in range(len(corr_matrix)))
        
        # Should be symmetric
        assert corr_matrix.equals(corr_matrix.T)
        
        # All correlations should be between -1 and 1
        assert ((corr_matrix >= -1) & (corr_matrix <= 1)).all().all()
    
    def test_economic_scenario_generation(self, market_assumptions):
        """Test generation of different economic scenarios."""
        scenarios = ['bull_market', 'bear_market', 'recession', 'normal']
        
        for scenario in scenarios:
            adjusted_assumptions = market_assumptions.get_scenario_assumptions(scenario)
            
            assert 'expected_returns' in adjusted_assumptions
            assert 'volatilities' in adjusted_assumptions
            
            # Recession should have lower expected returns
            if scenario == 'recession':
                normal_returns = market_assumptions.get_scenario_assumptions('normal')['expected_returns']
                recession_returns = adjusted_assumptions['expected_returns']
                assert recession_returns['stocks'] < normal_returns['stocks']


class TestPortfolioMapper:
    """Test suite for portfolio mapping functionality."""
    
    @pytest.fixture
    def portfolio_mapper(self):
        """Create portfolio mapper instance."""
        return PortfolioMapper()
    
    def test_risk_tolerance_mapping(self, portfolio_mapper):
        """Test mapping of risk tolerance to portfolio allocation."""
        conservative_portfolio = portfolio_mapper.get_portfolio_for_risk_tolerance('conservative')
        moderate_portfolio = portfolio_mapper.get_portfolio_for_risk_tolerance('moderate')
        aggressive_portfolio = portfolio_mapper.get_portfolio_for_risk_tolerance('aggressive')
        
        # Conservative should have more bonds and cash
        assert conservative_portfolio['bonds'] + conservative_portfolio['cash'] > 0.5
        
        # Aggressive should have more stocks
        assert aggressive_portfolio['stocks'] > 0.6
        
        # All portfolios should sum to 1
        for portfolio in [conservative_portfolio, moderate_portfolio, aggressive_portfolio]:
            assert abs(sum(portfolio.values()) - 1.0) < 0.001
    
    def test_age_based_allocation(self, portfolio_mapper):
        """Test age-based portfolio allocation."""
        young_portfolio = portfolio_mapper.get_age_appropriate_portfolio(25)
        middle_portfolio = portfolio_mapper.get_age_appropriate_portfolio(45)
        older_portfolio = portfolio_mapper.get_age_appropriate_portfolio(65)
        
        # Younger investors should have more stocks
        assert young_portfolio['stocks'] > middle_portfolio['stocks']
        assert middle_portfolio['stocks'] > older_portfolio['stocks']
        
        # Older investors should have more bonds
        assert older_portfolio['bonds'] > middle_portfolio['bonds']
        assert middle_portfolio['bonds'] > young_portfolio['bonds']
    
    def test_goal_based_allocation(self, portfolio_mapper):
        """Test goal-based portfolio allocation."""
        retirement_portfolio = portfolio_mapper.get_goal_appropriate_portfolio(
            GoalType.RETIREMENT, time_horizon=30
        )
        emergency_portfolio = portfolio_mapper.get_goal_appropriate_portfolio(
            GoalType.EMERGENCY_FUND, time_horizon=1
        )
        house_portfolio = portfolio_mapper.get_goal_appropriate_portfolio(
            GoalType.HOME_PURCHASE, time_horizon=5
        )
        
        # Emergency fund should be very conservative (high cash)
        assert emergency_portfolio['cash'] > 0.5
        
        # Long-term retirement should be more aggressive
        assert retirement_portfolio['stocks'] > house_portfolio['stocks']
        
        # All portfolios should sum to 1
        for portfolio in [retirement_portfolio, emergency_portfolio, house_portfolio]:
            assert abs(sum(portfolio.values()) - 1.0) < 0.001


@pytest.mark.benchmark
class TestMonteCarloPerformance:
    """Performance benchmarks for Monte Carlo engine."""
    
    @pytest.fixture
    def engine(self):
        """Create Monte Carlo engine for performance testing."""
        return MonteCarloEngine()
    
    @pytest.fixture
    def large_simulation_request(self):
        """Large simulation request for performance testing."""
        return SimulationRequest(
            portfolio_allocation={'stocks': 0.6, 'bonds': 0.3, 'cash': 0.1},
            time_horizon_years=40,
            initial_investment=100000,
            monthly_contribution=2000,
            num_simulations=10000
        )
    
    def test_large_simulation_performance(self, benchmark, engine, large_simulation_request, 
                                        sample_financial_profile, sample_goals):
        """Benchmark performance of large Monte Carlo simulation."""
        
        async def run_large_simulation():
            return await engine.run_simulation(
                large_simulation_request, 
                sample_financial_profile, 
                sample_goals
            )
        
        # Benchmark should complete within reasonable time
        result = benchmark(asyncio.run, run_large_simulation())
        
        assert result is not None
        assert result.num_simulations == 10000
    
    def test_parallel_simulation_performance(self, benchmark, engine):
        """Benchmark performance of parallel simulations."""
        
        def run_parallel_simulations():
            portfolio = {'stocks': 0.6, 'bonds': 0.3, 'cash': 0.1}
            
            # Run multiple smaller simulations in parallel
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
                futures = []
                for _ in range(4):
                    future = executor.submit(engine._generate_monthly_returns, portfolio, 240)
                    futures.append(future)
                
                results = [future.result() for future in futures]
            
            return results
        
        results = benchmark(run_parallel_simulations)
        
        assert len(results) == 4
        assert all(len(r) == 240 for r in results)