"""
Unit tests for the simulation service.

Tests the Monte Carlo simulation engine, portfolio optimization,
and goal achievement probability calculations.
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from decimal import Decimal
from datetime import datetime, timedelta

from app.services.simulation_service import SimulationService
from app.simulations.engine import MonteCarloEngine
from app.models.goal import Goal
from app.models.financial_profile import FinancialProfile
from tests.factories import UserFactory, FinancialProfileFactory, GoalFactory


class TestSimulationService:
    """Test cases for the simulation service."""
    
    @pytest.fixture
    def simulation_service(self):
        """Create a simulation service instance."""
        return SimulationService()
    
    @pytest.fixture
    def mock_monte_carlo_engine(self):
        """Mock Monte Carlo engine."""
        mock = Mock(spec=MonteCarloEngine)
        mock.run_simulation.return_value = {
            'final_values': [100000, 120000, 95000, 110000, 105000],
            'success_probability': 0.85,
            'percentiles': {
                '10': 95000,
                '50': 105000,
                '90': 120000
            },
            'annual_returns': [0.07, 0.08, 0.06, 0.075, 0.072]
        }
        return mock
    
    @pytest.mark.asyncio
    async def test_run_goal_simulation(self, simulation_service, db_session, mock_monte_carlo_engine):
        """Test running a goal achievement simulation."""
        # Arrange
        user = await UserFactory.create(session=db_session)
        profile = await FinancialProfileFactory.create(session=db_session, user_id=user.id)
        goal = await GoalFactory.create(
            session=db_session,
            user_id=user.id,
            target_amount=Decimal('100000'),
            target_date=datetime.now().date() + timedelta(days=365*10),
            monthly_contribution=Decimal('500')
        )
        
        with patch.object(simulation_service, '_get_monte_carlo_engine', return_value=mock_monte_carlo_engine):
            # Act
            result = await simulation_service.run_goal_simulation(
                profile=profile,
                goal=goal,
                current_amount=Decimal('10000'),
                num_simulations=1000
            )
        
        # Assert
        assert result is not None
        assert 'success_probability' in result
        assert 'final_value_distribution' in result
        assert 'recommended_adjustments' in result
        assert result['success_probability'] == 0.85
        assert len(result['final_value_distribution']) > 0
        mock_monte_carlo_engine.run_simulation.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_run_retirement_simulation(self, simulation_service, db_session, mock_monte_carlo_engine):
        """Test running a retirement planning simulation."""
        # Arrange
        user = await UserFactory.create(session=db_session)
        profile = await FinancialProfileFactory.create(
            session=db_session,
            user_id=user.id,
            annual_income=Decimal('75000'),
            current_savings=Decimal('50000'),
            risk_tolerance='moderate'
        )
        
        retirement_params = {
            'current_age': 35,
            'retirement_age': 65,
            'desired_retirement_income': Decimal('60000'),
            'current_retirement_savings': Decimal('50000'),
            'monthly_contribution': Decimal('1000')
        }
        
        with patch.object(simulation_service, '_get_monte_carlo_engine', return_value=mock_monte_carlo_engine):
            # Act
            result = await simulation_service.run_retirement_simulation(
                profile=profile,
                retirement_params=retirement_params,
                num_simulations=1000
            )
        
        # Assert
        assert result is not None
        assert 'retirement_readiness_score' in result
        assert 'projected_retirement_income' in result
        assert 'shortfall_analysis' in result
        assert 'optimization_suggestions' in result
        mock_monte_carlo_engine.run_simulation.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_optimize_portfolio_allocation(self, simulation_service, db_session):
        """Test portfolio optimization based on risk tolerance."""
        # Arrange
        user = await UserFactory.create(session=db_session)
        profile = await FinancialProfileFactory.create(
            session=db_session,
            user_id=user.id,
            risk_tolerance='moderate',
            investment_timeline=20
        )
        
        current_allocation = {
            'stocks': 0.6,
            'bonds': 0.3,
            'cash': 0.1
        }
        
        with patch('app.services.simulation_service.portfolio_optimizer') as mock_optimizer:
            mock_optimizer.optimize.return_value = {
                'recommended_allocation': {
                    'stocks': 0.7,
                    'bonds': 0.25,
                    'cash': 0.05
                },
                'expected_return': 0.08,
                'expected_volatility': 0.15,
                'sharpe_ratio': 0.53
            }
            
            # Act
            result = await simulation_service.optimize_portfolio_allocation(
                profile=profile,
                current_allocation=current_allocation,
                constraints={'max_stock_allocation': 0.8}
            )
        
        # Assert
        assert result is not None
        assert 'recommended_allocation' in result
        assert 'expected_return' in result
        assert 'rebalancing_suggestions' in result
        assert result['recommended_allocation']['stocks'] == 0.7
        mock_optimizer.optimize.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_calculate_goal_progress(self, simulation_service, db_session):
        """Test calculating progress towards a financial goal."""
        # Arrange
        user = await UserFactory.create(session=db_session)
        goal = await GoalFactory.create(
            session=db_session,
            user_id=user.id,
            target_amount=Decimal('100000'),
            current_amount=Decimal('25000'),
            target_date=datetime.now().date() + timedelta(days=365*5),
            monthly_contribution=Decimal('1000')
        )
        
        # Act
        progress = await simulation_service.calculate_goal_progress(goal)
        
        # Assert
        assert progress is not None
        assert 'completion_percentage' in progress
        assert 'projected_completion_date' in progress
        assert 'on_track' in progress
        assert 'required_monthly_contribution' in progress
        assert progress['completion_percentage'] == 25.0  # 25000/100000 * 100
    
    @pytest.mark.asyncio
    async def test_analyze_risk_metrics(self, simulation_service, db_session):
        """Test risk analysis for a portfolio."""
        # Arrange
        portfolio_data = [
            {'date': '2023-01-01', 'value': 100000},
            {'date': '2023-02-01', 'value': 102000},
            {'date': '2023-03-01', 'value': 98000},
            {'date': '2023-04-01', 'value': 105000},
            {'date': '2023-05-01', 'value': 103000}
        ]
        
        # Act
        risk_metrics = await simulation_service.analyze_risk_metrics(portfolio_data)
        
        # Assert
        assert risk_metrics is not None
        assert 'volatility' in risk_metrics
        assert 'max_drawdown' in risk_metrics
        assert 'var_95' in risk_metrics  # Value at Risk
        assert 'sharpe_ratio' in risk_metrics
        assert 'beta' in risk_metrics
        assert isinstance(risk_metrics['volatility'], float)
        assert risk_metrics['volatility'] >= 0
    
    @pytest.mark.asyncio
    async def test_simulation_with_market_conditions(self, simulation_service, db_session, mock_monte_carlo_engine):
        """Test simulation with different market condition scenarios."""
        # Arrange
        user = await UserFactory.create(session=db_session)
        profile = await FinancialProfileFactory.create(session=db_session, user_id=user.id)
        
        market_scenarios = {
            'bull_market': {'return_multiplier': 1.2, 'volatility_multiplier': 0.8},
            'bear_market': {'return_multiplier': 0.7, 'volatility_multiplier': 1.5},
            'normal_market': {'return_multiplier': 1.0, 'volatility_multiplier': 1.0}
        }
        
        with patch.object(simulation_service, '_get_monte_carlo_engine', return_value=mock_monte_carlo_engine):
            # Act
            results = await simulation_service.run_scenario_analysis(
                profile=profile,
                scenarios=market_scenarios,
                initial_investment=Decimal('50000'),
                time_horizon=10
            )
        
        # Assert
        assert results is not None
        assert len(results) == 3  # Three scenarios
        for scenario_name in market_scenarios.keys():
            assert scenario_name in results
            assert 'success_probability' in results[scenario_name]
            assert 'final_value_distribution' in results[scenario_name]
    
    @pytest.mark.asyncio
    async def test_calculate_withdrawal_strategy(self, simulation_service, db_session):
        """Test retirement withdrawal strategy calculation."""
        # Arrange
        retirement_params = {
            'portfolio_value': Decimal('1000000'),
            'annual_expenses': Decimal('60000'),
            'retirement_duration': 30,
            'inflation_rate': 0.03,
            'market_return_assumption': 0.07
        }
        
        # Act
        strategy = await simulation_service.calculate_withdrawal_strategy(retirement_params)
        
        # Assert
        assert strategy is not None
        assert 'safe_withdrawal_rate' in strategy
        assert 'annual_withdrawal_amount' in strategy
        assert 'portfolio_longevity' in strategy
        assert 'withdrawal_schedule' in strategy
        assert strategy['safe_withdrawal_rate'] <= 0.05  # Should be <= 5% rule of thumb
    
    @pytest.mark.asyncio
    async def test_stress_test_portfolio(self, simulation_service, db_session):
        """Test portfolio stress testing under extreme conditions."""
        # Arrange
        portfolio = {
            'total_value': Decimal('500000'),
            'allocation': {
                'stocks': 0.7,
                'bonds': 0.2,
                'cash': 0.1
            }
        }
        
        stress_scenarios = {
            'market_crash': {'stock_decline': -0.4, 'bond_decline': -0.1},
            'interest_rate_shock': {'bond_decline': -0.2, 'stock_decline': -0.1},
            'inflation_spike': {'real_return_reduction': -0.05}
        }
        
        # Act
        stress_results = await simulation_service.stress_test_portfolio(
            portfolio=portfolio,
            stress_scenarios=stress_scenarios
        )
        
        # Assert
        assert stress_results is not None
        for scenario_name in stress_scenarios.keys():
            assert scenario_name in stress_results
            assert 'portfolio_value_after_stress' in stress_results[scenario_name]
            assert 'percentage_loss' in stress_results[scenario_name]
            assert 'recovery_time_estimate' in stress_results[scenario_name]
    
    def test_monte_carlo_engine_initialization(self, simulation_service):
        """Test Monte Carlo engine initialization with different parameters."""
        # Arrange
        params = {
            'expected_return': 0.07,
            'volatility': 0.15,
            'time_horizon': 10,
            'initial_value': 50000,
            'monthly_contribution': 1000
        }
        
        # Act
        engine = simulation_service._get_monte_carlo_engine(params)
        
        # Assert
        assert engine is not None
        assert hasattr(engine, 'run_simulation')
        assert hasattr(engine, 'expected_return')
        assert hasattr(engine, 'volatility')
    
    @pytest.mark.benchmark
    def test_simulation_performance(self, simulation_service, benchmark, db_session):
        """Benchmark simulation performance."""
        async def run_simulation():
            user = await UserFactory.create(session=db_session)
            profile = await FinancialProfileFactory.create(session=db_session, user_id=user.id)
            goal = await GoalFactory.create(session=db_session, user_id=user.id)
            
            return await simulation_service.run_goal_simulation(
                profile=profile,
                goal=goal,
                current_amount=Decimal('10000'),
                num_simulations=100  # Reduced for benchmark
            )
        
        # Benchmark should complete within reasonable time
        result = benchmark(lambda: asyncio.run(run_simulation()))
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_simulation_input_validation(self, simulation_service, db_session):
        """Test input validation for simulation parameters."""
        # Arrange
        user = await UserFactory.create(session=db_session)
        profile = await FinancialProfileFactory.create(session=db_session, user_id=user.id)
        
        # Test with invalid target amount
        with pytest.raises(ValueError, match="Target amount must be positive"):
            goal = await GoalFactory.create(
                session=db_session,
                user_id=user.id,
                target_amount=Decimal('-1000')  # Negative amount
            )
            await simulation_service.run_goal_simulation(
                profile=profile,
                goal=goal,
                current_amount=Decimal('1000')
            )
        
        # Test with invalid time horizon
        with pytest.raises(ValueError, match="Time horizon must be positive"):
            await simulation_service.run_retirement_simulation(
                profile=profile,
                retirement_params={'current_age': 65, 'retirement_age': 60}  # Invalid age range
            )
    
    @pytest.mark.asyncio
    async def test_simulation_edge_cases(self, simulation_service, db_session):
        """Test simulation behavior with edge cases."""
        # Arrange
        user = await UserFactory.create(session=db_session)
        profile = await FinancialProfileFactory.create(session=db_session, user_id=user.id)
        
        # Test with goal already achieved
        goal = await GoalFactory.create(
            session=db_session,
            user_id=user.id,
            target_amount=Decimal('50000'),
            current_amount=Decimal('60000')  # Already exceeded target
        )
        
        # Act
        result = await simulation_service.run_goal_simulation(
            profile=profile,
            goal=goal,
            current_amount=Decimal('60000')
        )
        
        # Assert
        assert result is not None
        assert result['success_probability'] == 1.0  # Already achieved
        assert 'goal_already_achieved' in result
        assert result['goal_already_achieved'] is True