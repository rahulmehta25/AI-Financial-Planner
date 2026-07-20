"""
Integration tests for financial planning endpoints.

Tests financial profile management, goal tracking, and simulation endpoints.
"""
import pytest
from httpx import AsyncClient
from decimal import Decimal
from datetime import datetime, timedelta
import json
from unittest.mock import patch

from tests.factories import UserFactory, FinancialProfileFactory, GoalFactory, InvestmentFactory


class TestFinancialProfileEndpoints:
    """Test cases for financial profile management endpoints."""
    
    @pytest.mark.asyncio
    async def test_create_financial_profile(self, authenticated_client: AsyncClient, test_user):
        """Test creating a financial profile."""
        # Arrange
        profile_data = {
            "annual_income": 75000.0,
            "monthly_expenses": 4500.0,
            "current_savings": 25000.0,
            "current_debt": 15000.0,
            "investment_experience": "intermediate",
            "risk_tolerance": "moderate",
            "investment_timeline": 20,
            "financial_goals": ["retirement", "house_down_payment"],
            "employment_status": "employed",
            "marital_status": "single",
            "dependents": 0
        }
        
        # Act
        response = await authenticated_client.post(
            "/api/v1/financial-profiles",
            json=profile_data
        )
        
        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["annual_income"] == profile_data["annual_income"]
        assert data["risk_tolerance"] == profile_data["risk_tolerance"]
        assert data["user_id"] == test_user.id
        assert "id" in data
        assert "created_at" in data
    
    @pytest.mark.asyncio
    async def test_get_financial_profile(self, authenticated_client: AsyncClient, test_financial_profile):
        """Test retrieving financial profile."""
        # Act
        response = await authenticated_client.get(
            f"/api/v1/financial-profiles/{test_financial_profile.id}"
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_financial_profile.id
        assert data["annual_income"] == float(test_financial_profile.annual_income)
        assert data["risk_tolerance"] == test_financial_profile.risk_tolerance
    
    @pytest.mark.asyncio
    async def test_update_financial_profile(self, authenticated_client: AsyncClient, test_financial_profile):
        """Test updating financial profile."""
        # Arrange
        update_data = {
            "annual_income": 85000.0,
            "risk_tolerance": "aggressive",
            "investment_timeline": 25
        }
        
        # Act
        response = await authenticated_client.put(
            f"/api/v1/financial-profiles/{test_financial_profile.id}",
            json=update_data
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["annual_income"] == update_data["annual_income"]
        assert data["risk_tolerance"] == update_data["risk_tolerance"]
        assert data["investment_timeline"] == update_data["investment_timeline"]
    
    @pytest.mark.asyncio
    async def test_delete_financial_profile(self, authenticated_client: AsyncClient, test_financial_profile):
        """Test deleting financial profile."""
        # Act
        response = await authenticated_client.delete(
            f"/api/v1/financial-profiles/{test_financial_profile.id}"
        )
        
        # Assert
        assert response.status_code == 204
        
        # Verify profile is deleted
        get_response = await authenticated_client.get(
            f"/api/v1/financial-profiles/{test_financial_profile.id}"
        )
        assert get_response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_financial_profile_validation(self, authenticated_client: AsyncClient):
        """Test financial profile data validation."""
        invalid_data_cases = [
            # Negative income
            {"annual_income": -1000, "risk_tolerance": "moderate"},
            # Invalid risk tolerance
            {"annual_income": 50000, "risk_tolerance": "invalid"},
            # Expenses > Income
            {"annual_income": 30000, "monthly_expenses": 5000},
            # Negative savings
            {"annual_income": 50000, "current_savings": -1000}
        ]
        
        for invalid_data in invalid_data_cases:
            response = await authenticated_client.post(
                "/api/v1/financial-profiles",
                json=invalid_data
            )
            assert response.status_code == 422


class TestGoalManagementEndpoints:
    """Test cases for financial goal management endpoints."""
    
    @pytest.mark.asyncio
    async def test_create_goal(self, authenticated_client: AsyncClient, test_user):
        """Test creating a financial goal."""
        # Arrange
        goal_data = {
            "name": "Emergency Fund",
            "description": "Build an emergency fund for 6 months of expenses",
            "goal_type": "emergency",
            "target_amount": 30000.0,
            "current_amount": 5000.0,
            "target_date": (datetime.now().date() + timedelta(days=365)).isoformat(),
            "priority": "high",
            "monthly_contribution": 800.0
        }
        
        # Act
        response = await authenticated_client.post("/api/v1/goals", json=goal_data)
        
        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == goal_data["name"]
        assert data["target_amount"] == goal_data["target_amount"]
        assert data["user_id"] == test_user.id
        assert "id" in data
    
    @pytest.mark.asyncio
    async def test_list_goals(self, authenticated_client: AsyncClient, test_user, db_session):
        """Test listing user's goals."""
        # Arrange - create multiple goals
        goals = await GoalFactory.create_batch(session=db_session, size=3, user_id=test_user.id)
        
        # Act
        response = await authenticated_client.get("/api/v1/goals")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 3
        assert all(goal["user_id"] == test_user.id for goal in data)
    
    @pytest.mark.asyncio
    async def test_update_goal_progress(self, authenticated_client: AsyncClient, test_goal):
        """Test updating goal progress."""
        # Arrange
        update_data = {
            "current_amount": 15000.0,
            "monthly_contribution": 1000.0
        }
        
        # Act
        response = await authenticated_client.put(
            f"/api/v1/goals/{test_goal.id}",
            json=update_data
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["current_amount"] == update_data["current_amount"]
        assert data["monthly_contribution"] == update_data["monthly_contribution"]
    
    @pytest.mark.asyncio
    async def test_goal_progress_calculation(self, authenticated_client: AsyncClient, test_goal):
        """Test goal progress calculation endpoint."""
        # Act
        response = await authenticated_client.get(f"/api/v1/goals/{test_goal.id}/progress")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "completion_percentage" in data
        assert "projected_completion_date" in data
        assert "on_track" in data
        assert "required_monthly_contribution" in data
        assert 0 <= data["completion_percentage"] <= 100
    
    @pytest.mark.asyncio
    async def test_goal_recommendations(self, authenticated_client: AsyncClient, test_goal, test_financial_profile):
        """Test goal-specific recommendations."""
        # Act
        response = await authenticated_client.get(f"/api/v1/goals/{test_goal.id}/recommendations")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "recommendations" in data
        assert "priority_adjustments" in data
        assert "optimization_suggestions" in data
        assert isinstance(data["recommendations"], list)


class TestSimulationEndpoints:
    """Test cases for simulation and analysis endpoints."""
    
    @pytest.mark.asyncio
    async def test_monte_carlo_simulation(self, authenticated_client: AsyncClient, test_financial_profile, test_goal):
        """Test Monte Carlo simulation endpoint."""
        # Arrange
        simulation_params = {
            "goal_id": test_goal.id,
            "num_simulations": 1000,
            "market_assumptions": {
                "expected_return": 0.07,
                "volatility": 0.15,
                "inflation_rate": 0.03
            }
        }
        
        with patch('app.services.simulation_service.MonteCarloEngine') as mock_engine:
            mock_engine.return_value.run_simulation.return_value = {
                "success_probability": 0.85,
                "final_value_distribution": {
                    "mean": 125000,
                    "median": 120000,
                    "percentile_10": 95000,
                    "percentile_90": 155000
                }
            }
            
            # Act
            response = await authenticated_client.post(
                "/api/v1/simulations/monte-carlo",
                json=simulation_params
            )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "success_probability" in data
        assert "final_value_distribution" in data
        assert "simulation_id" in data
        assert 0 <= data["success_probability"] <= 1
    
    @pytest.mark.asyncio
    async def test_retirement_planning_simulation(self, authenticated_client: AsyncClient, test_financial_profile):
        """Test retirement planning simulation."""
        # Arrange
        retirement_params = {
            "current_age": 35,
            "retirement_age": 65,
            "desired_retirement_income": 60000.0,
            "current_retirement_savings": 50000.0,
            "monthly_contribution": 1000.0,
            "social_security_estimate": 24000.0
        }
        
        with patch('app.services.simulation_service.SimulationService.run_retirement_simulation') as mock_sim:
            mock_sim.return_value = {
                "retirement_readiness_score": 0.75,
                "projected_retirement_income": 58000,
                "shortfall_analysis": {
                    "annual_shortfall": 2000,
                    "total_shortfall": 60000
                },
                "optimization_suggestions": [
                    "Increase monthly contribution by $200",
                    "Consider delaying retirement by 2 years"
                ]
            }
            
            # Act
            response = await authenticated_client.post(
                "/api/v1/simulations/retirement-planning",
                json=retirement_params
            )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "retirement_readiness_score" in data
        assert "projected_retirement_income" in data
        assert "optimization_suggestions" in data
    
    @pytest.mark.asyncio
    async def test_portfolio_optimization(self, authenticated_client: AsyncClient, test_financial_profile):
        """Test portfolio optimization endpoint."""
        # Arrange
        optimization_params = {
            "current_allocation": {
                "stocks": 0.6,
                "bonds": 0.3,
                "cash": 0.1
            },
            "constraints": {
                "max_stock_allocation": 0.8,
                "min_bond_allocation": 0.1,
                "max_cash_allocation": 0.2
            },
            "optimization_objective": "max_sharpe"
        }
        
        with patch('app.services.simulation_service.SimulationService.optimize_portfolio_allocation') as mock_opt:
            mock_opt.return_value = {
                "recommended_allocation": {
                    "stocks": 0.75,
                    "bonds": 0.2,
                    "cash": 0.05
                },
                "expected_return": 0.085,
                "expected_volatility": 0.16,
                "sharpe_ratio": 0.53,
                "rebalancing_suggestions": [
                    "Increase stock allocation by 15%",
                    "Reduce cash allocation by 5%"
                ]
            }
            
            # Act
            response = await authenticated_client.post(
                "/api/v1/simulations/portfolio-optimization",
                json=optimization_params
            )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "recommended_allocation" in data
        assert "expected_return" in data
        assert "sharpe_ratio" in data
        assert "rebalancing_suggestions" in data
    
    @pytest.mark.asyncio
    async def test_scenario_analysis(self, authenticated_client: AsyncClient, test_financial_profile):
        """Test scenario analysis endpoint."""
        # Arrange
        scenario_params = {
            "base_scenario": {
                "return_rate": 0.07,
                "volatility": 0.15
            },
            "scenarios": {
                "bull_market": {"return_rate": 0.12, "volatility": 0.18},
                "bear_market": {"return_rate": 0.02, "volatility": 0.25},
                "recession": {"return_rate": -0.05, "volatility": 0.35}
            },
            "time_horizon": 10,
            "initial_investment": 50000
        }
        
        # Act
        response = await authenticated_client.post(
            "/api/v1/simulations/scenario-analysis",
            json=scenario_params
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "base_scenario" in data
        assert "scenarios" in data
        assert "bull_market" in data["scenarios"]
        assert "bear_market" in data["scenarios"]
        assert "recession" in data["scenarios"]
    
    @pytest.mark.asyncio
    async def test_get_simulation_history(self, authenticated_client: AsyncClient, test_user):
        """Test retrieving simulation history."""
        # Act
        response = await authenticated_client.get("/api/v1/simulations/history")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # All simulations should belong to the authenticated user
        for simulation in data:
            assert simulation["user_id"] == test_user.id


class TestInvestmentEndpoints:
    """Test cases for investment tracking endpoints."""
    
    @pytest.mark.asyncio
    async def test_add_investment(self, authenticated_client: AsyncClient, test_user):
        """Test adding an investment."""
        # Arrange
        investment_data = {
            "symbol": "AAPL",
            "name": "Apple Inc.",
            "investment_type": "stock",
            "quantity": 10.0,
            "purchase_price": 150.0,
            "purchase_date": "2023-01-15",
            "sector": "technology"
        }
        
        # Act
        response = await authenticated_client.post(
            "/api/v1/investments",
            json=investment_data
        )
        
        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["symbol"] == investment_data["symbol"]
        assert data["quantity"] == investment_data["quantity"]
        assert data["user_id"] == test_user.id
    
    @pytest.mark.asyncio
    async def test_get_portfolio_summary(self, authenticated_client: AsyncClient, test_user, db_session):
        """Test portfolio summary endpoint."""
        # Arrange - create multiple investments
        investments = await InvestmentFactory.create_batch(
            session=db_session,
            size=5,
            user_id=test_user.id
        )
        
        with patch('app.services.market_data.manager.MarketDataManager.get_current_prices') as mock_prices:
            mock_prices.return_value = {
                inv.symbol: float(inv.current_price) for inv in investments
            }
            
            # Act
            response = await authenticated_client.get("/api/v1/investments/portfolio/summary")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "total_value" in data
        assert "total_cost_basis" in data
        assert "total_gain_loss" in data
        assert "total_gain_loss_percentage" in data
        assert "allocation_by_type" in data
        assert "allocation_by_sector" in data
    
    @pytest.mark.asyncio
    async def test_portfolio_performance(self, authenticated_client: AsyncClient, test_user):
        """Test portfolio performance analytics."""
        # Act
        response = await authenticated_client.get(
            "/api/v1/investments/portfolio/performance"
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "time_series" in data
        assert "performance_metrics" in data
        assert "benchmark_comparison" in data
        
        # Check performance metrics
        metrics = data["performance_metrics"]
        assert "total_return" in metrics
        assert "annualized_return" in metrics
        assert "volatility" in metrics
        assert "sharpe_ratio" in metrics
        assert "max_drawdown" in metrics
    
    @pytest.mark.asyncio
    async def test_investment_recommendations(self, authenticated_client: AsyncClient, test_financial_profile):
        """Test investment recommendations endpoint."""
        # Act
        response = await authenticated_client.get("/api/v1/investments/recommendations")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "recommended_investments" in data
        assert "rebalancing_suggestions" in data
        assert "risk_analysis" in data
        
        # Check recommendations structure
        recommendations = data["recommended_investments"]
        assert isinstance(recommendations, list)
        for rec in recommendations:
            assert "symbol" in rec
            assert "reason" in rec
            assert "allocation_percentage" in rec


class TestMarketDataEndpoints:
    """Test cases for market data endpoints."""
    
    @pytest.mark.asyncio
    async def test_get_stock_quote(self, authenticated_client: AsyncClient):
        """Test getting stock quote."""
        with patch('app.services.market_data.providers.yahoo_finance.YahooFinanceProvider.get_quote') as mock_quote:
            mock_quote.return_value = {
                "symbol": "AAPL",
                "price": 150.25,
                "change": 2.15,
                "change_percent": 1.45,
                "volume": 45678123,
                "market_cap": 2500000000000
            }
            
            # Act
            response = await authenticated_client.get("/api/v1/market-data/quote/AAPL")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["symbol"] == "AAPL"
        assert "price" in data
        assert "change" in data
        assert "volume" in data
    
    @pytest.mark.asyncio
    async def test_get_historical_data(self, authenticated_client: AsyncClient):
        """Test getting historical market data."""
        with patch('app.services.market_data.providers.yahoo_finance.YahooFinanceProvider.get_historical_data') as mock_data:
            mock_data.return_value = [
                {
                    "date": "2023-11-01",
                    "open": 145.0,
                    "high": 148.0,
                    "low": 144.0,
                    "close": 147.5,
                    "volume": 34567890
                },
                {
                    "date": "2023-11-02", 
                    "open": 147.5,
                    "high": 151.0,
                    "low": 146.0,
                    "close": 150.25,
                    "volume": 45678123
                }
            ]
            
            # Act
            response = await authenticated_client.get(
                "/api/v1/market-data/historical/AAPL",
                params={"period": "1mo"}
            )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2
        for point in data:
            assert "date" in point
            assert "close" in point
    
    @pytest.mark.asyncio
    async def test_market_indices(self, authenticated_client: AsyncClient):
        """Test getting market indices data."""
        # Act
        response = await authenticated_client.get("/api/v1/market-data/indices")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "SPY" in data or "^GSPC" in data  # S&P 500
        assert "QQQ" in data or "^IXIC" in data  # NASDAQ
    
    @pytest.mark.asyncio
    async def test_sector_performance(self, authenticated_client: AsyncClient):
        """Test sector performance endpoint."""
        # Act
        response = await authenticated_client.get("/api/v1/market-data/sectors")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "technology" in data
        assert "healthcare" in data
        assert "finance" in data
        
        # Check sector data structure
        for sector, performance in data.items():
            assert "return_1d" in performance
            assert "return_1w" in performance
            assert "return_1m" in performance