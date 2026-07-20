"""
Comprehensive integration tests for API endpoints.

This test suite covers:
- Authentication and authorization
- Financial profile management
- Goal management
- Investment tracking
- Monte Carlo simulations
- AI-powered recommendations
- Banking integration
- PDF export
- Real-time updates
- Error handling
"""
import pytest
import json
import asyncio
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import patch, Mock, AsyncMock
from httpx import AsyncClient
from fastapi import status

from app.main import app
from app.models.user import User
from app.models.financial_profile import FinancialProfile
from app.models.goal import Goal, GoalType
from app.models.investment import Investment
from app.models.simulation_result import SimulationResult
from app.core.security import create_access_token
from tests.factories import UserFactory, FinancialProfileFactory, GoalFactory


class TestAuthenticationEndpoints:
    """Test authentication and authorization endpoints."""
    
    @pytest.mark.asyncio
    async def test_user_registration(self, test_client: AsyncClient):
        """Test user registration endpoint."""
        
        registration_data = {
            "email": "testuser@example.com",
            "password": "SecurePassword123!",
            "first_name": "Test",
            "last_name": "User",
            "date_of_birth": "1990-01-01",
            "phone_number": "+1-555-123-4567"
        }
        
        response = await test_client.post("/api/v1/auth/register", json=registration_data)
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["email"] == registration_data["email"]
        assert "password" not in data["user"]  # Password should not be returned
    
    @pytest.mark.asyncio
    async def test_user_login(self, test_client: AsyncClient, test_user: User):
        """Test user login endpoint."""
        
        login_data = {
            "email": test_user.email,
            "password": "testpassword123"
        }
        
        response = await test_client.post("/api/v1/auth/login", json=login_data)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
        assert "user" in data
        assert data["user"]["id"] == str(test_user.id)
    
    @pytest.mark.asyncio
    async def test_invalid_login(self, test_client: AsyncClient):
        """Test login with invalid credentials."""
        
        login_data = {
            "email": "nonexistent@example.com",
            "password": "wrongpassword"
        }
        
        response = await test_client.post("/api/v1/auth/login", json=login_data)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        data = response.json()
        assert "detail" in data
    
    @pytest.mark.asyncio
    async def test_token_refresh(self, test_client: AsyncClient, test_user: User):
        """Test token refresh endpoint."""
        
        # First login to get refresh token
        login_response = await test_client.post("/api/v1/auth/login", json={
            "email": test_user.email,
            "password": "testpassword123"
        })
        
        refresh_token = login_response.json()["refresh_token"]
        
        # Use refresh token to get new access token
        refresh_response = await test_client.post("/api/v1/auth/refresh", json={
            "refresh_token": refresh_token
        })
        
        assert refresh_response.status_code == status.HTTP_200_OK
        data = refresh_response.json()
        assert "access_token" in data
    
    @pytest.mark.asyncio
    async def test_protected_endpoint_without_auth(self, test_client: AsyncClient):
        """Test accessing protected endpoint without authentication."""
        
        response = await test_client.get("/api/v1/users/me")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    @pytest.mark.asyncio
    async def test_protected_endpoint_with_invalid_token(self, test_client: AsyncClient):
        """Test accessing protected endpoint with invalid token."""
        
        headers = {"Authorization": "Bearer invalid_token"}
        response = await test_client.get("/api/v1/users/me", headers=headers)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    @pytest.mark.asyncio
    async def test_get_current_user(self, authenticated_client: AsyncClient, test_user: User):
        """Test getting current user information."""
        
        response = await authenticated_client.get("/api/v1/users/me")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["id"] == str(test_user.id)
        assert data["email"] == test_user.email
        assert "password" not in data


class TestFinancialProfileEndpoints:
    """Test financial profile management endpoints."""
    
    @pytest.mark.asyncio
    async def test_create_financial_profile(self, authenticated_client: AsyncClient):
        """Test creating a financial profile."""
        
        profile_data = {
            "annual_income": 75000.00,
            "monthly_expenses": 4500.00,
            "current_savings": 25000.00,
            "debt_amount": 15000.00,
            "risk_tolerance": "moderate",
            "investment_experience": "intermediate",
            "age": 35,
            "retirement_age": 65,
            "dependents": 1
        }
        
        response = await authenticated_client.post(
            "/api/v1/financial-profiles", 
            json=profile_data
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        
        assert data["annual_income"] == profile_data["annual_income"]
        assert data["risk_tolerance"] == profile_data["risk_tolerance"]
        assert "id" in data
    
    @pytest.mark.asyncio
    async def test_get_financial_profile(self, authenticated_client: AsyncClient, 
                                       test_financial_profile: FinancialProfile):
        """Test retrieving financial profile."""
        
        response = await authenticated_client.get(
            f"/api/v1/financial-profiles/{test_financial_profile.id}"
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["id"] == str(test_financial_profile.id)
        assert data["annual_income"] == float(test_financial_profile.annual_income)
    
    @pytest.mark.asyncio
    async def test_update_financial_profile(self, authenticated_client: AsyncClient,
                                          test_financial_profile: FinancialProfile):
        """Test updating financial profile."""
        
        update_data = {
            "annual_income": 85000.00,
            "monthly_expenses": 5000.00,
            "risk_tolerance": "aggressive"
        }
        
        response = await authenticated_client.patch(
            f"/api/v1/financial-profiles/{test_financial_profile.id}",
            json=update_data
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["annual_income"] == update_data["annual_income"]
        assert data["risk_tolerance"] == update_data["risk_tolerance"]
    
    @pytest.mark.asyncio
    async def test_financial_profile_validation(self, authenticated_client: AsyncClient):
        """Test financial profile data validation."""
        
        invalid_profile_data = {
            "annual_income": -1000.00,  # Negative income
            "monthly_expenses": 15000.00,  # Expenses > income (monthly)
            "risk_tolerance": "invalid_risk",  # Invalid risk tolerance
            "age": 150  # Invalid age
        }
        
        response = await authenticated_client.post(
            "/api/v1/financial-profiles",
            json=invalid_profile_data
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        data = response.json()
        assert "detail" in data
    
    @pytest.mark.asyncio
    async def test_calculate_financial_metrics(self, authenticated_client: AsyncClient,
                                             test_financial_profile: FinancialProfile):
        """Test calculation of financial metrics."""
        
        response = await authenticated_client.get(
            f"/api/v1/financial-profiles/{test_financial_profile.id}/metrics"
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert "net_worth" in data
        assert "savings_rate" in data
        assert "debt_to_income_ratio" in data
        assert "financial_health_score" in data
        
        # Verify calculations
        expected_net_worth = (test_financial_profile.current_savings - 
                            test_financial_profile.debt_amount)
        assert abs(data["net_worth"] - expected_net_worth) < 0.01


class TestGoalManagementEndpoints:
    """Test goal management endpoints."""
    
    @pytest.mark.asyncio
    async def test_create_goal(self, authenticated_client: AsyncClient):
        """Test creating a financial goal."""
        
        goal_data = {
            "name": "Emergency Fund",
            "description": "Build emergency fund for 6 months expenses",
            "target_amount": 50000.00,
            "target_date": (datetime.now() + timedelta(days=365*2)).isoformat(),
            "goal_type": "emergency_fund",
            "priority": 1
        }
        
        response = await authenticated_client.post("/api/v1/goals", json=goal_data)
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        
        assert data["name"] == goal_data["name"]
        assert data["target_amount"] == goal_data["target_amount"]
        assert data["goal_type"] == goal_data["goal_type"]
    
    @pytest.mark.asyncio
    async def test_get_goals(self, authenticated_client: AsyncClient, test_goal: Goal):
        """Test retrieving user goals."""
        
        response = await authenticated_client.get("/api/v1/goals")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert isinstance(data, list)
        assert len(data) >= 1
        
        # Find our test goal
        test_goal_data = next((g for g in data if g["id"] == str(test_goal.id)), None)
        assert test_goal_data is not None
        assert test_goal_data["name"] == test_goal.name
    
    @pytest.mark.asyncio
    async def test_update_goal(self, authenticated_client: AsyncClient, test_goal: Goal):
        """Test updating a financial goal."""
        
        update_data = {
            "name": "Updated Goal Name",
            "target_amount": 60000.00,
            "priority": 2
        }
        
        response = await authenticated_client.patch(
            f"/api/v1/goals/{test_goal.id}",
            json=update_data
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["name"] == update_data["name"]
        assert data["target_amount"] == update_data["target_amount"]
        assert data["priority"] == update_data["priority"]
    
    @pytest.mark.asyncio
    async def test_delete_goal(self, authenticated_client: AsyncClient, test_goal: Goal):
        """Test deleting a financial goal."""
        
        response = await authenticated_client.delete(f"/api/v1/goals/{test_goal.id}")
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verify goal is deleted
        get_response = await authenticated_client.get(f"/api/v1/goals/{test_goal.id}")
        assert get_response.status_code == status.HTTP_404_NOT_FOUND
    
    @pytest.mark.asyncio
    async def test_goal_progress_tracking(self, authenticated_client: AsyncClient, test_goal: Goal):
        """Test goal progress tracking."""
        
        progress_data = {
            "current_amount": 15000.00,
            "notes": "Monthly contribution of $500"
        }
        
        response = await authenticated_client.post(
            f"/api/v1/goals/{test_goal.id}/progress",
            json=progress_data
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        
        assert data["current_amount"] == progress_data["current_amount"]
        assert data["notes"] == progress_data["notes"]
        
        # Calculate progress percentage
        expected_progress = progress_data["current_amount"] / test_goal.target_amount
        assert abs(data["progress_percentage"] - expected_progress) < 0.01
    
    @pytest.mark.asyncio
    async def test_goal_recommendations(self, authenticated_client: AsyncClient, test_goal: Goal):
        """Test getting goal-specific recommendations."""
        
        with patch('app.ai.recommendation_engine.RecommendationEngine') as mock_engine:
            mock_engine_instance = AsyncMock()
            mock_engine_instance.generate_goal_recommendations.return_value = {
                "recommendations": [
                    {
                        "type": "increase_contribution",
                        "description": "Increase monthly contribution by $100",
                        "impact": "Reach goal 6 months earlier"
                    }
                ]
            }
            mock_engine.return_value = mock_engine_instance
            
            response = await authenticated_client.get(
                f"/api/v1/goals/{test_goal.id}/recommendations"
            )
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            
            assert "recommendations" in data
            assert len(data["recommendations"]) >= 1
            
            rec = data["recommendations"][0]
            assert "type" in rec
            assert "description" in rec
            assert "impact" in rec


class TestMonteCarloSimulationEndpoints:
    """Test Monte Carlo simulation endpoints."""
    
    @pytest.mark.asyncio
    async def test_run_simulation(self, authenticated_client: AsyncClient, 
                                test_financial_profile: FinancialProfile,
                                test_goal: Goal):
        """Test running Monte Carlo simulation."""
        
        simulation_request = {
            "portfolio_allocation": {
                "stocks": 0.60,
                "bonds": 0.30,
                "cash": 0.10
            },
            "time_horizon_years": 30,
            "initial_investment": 25000.00,
            "monthly_contribution": 1000.00,
            "num_simulations": 1000,
            "inflation_rate": 0.03
        }
        
        with patch('app.simulations.engine.MonteCarloEngine') as mock_engine:
            mock_engine_instance = AsyncMock()
            mock_engine_instance.run_simulation.return_value = Mock(
                success_probability=0.75,
                expected_final_value=1200000,
                percentile_10=800000,
                percentile_50=1200000,
                percentile_90=1600000,
                num_simulations=1000,
                time_horizon_years=30
            )
            mock_engine.return_value = mock_engine_instance
            
            response = await authenticated_client.post(
                "/api/v1/simulations/monte-carlo",
                json=simulation_request
            )
            
            assert response.status_code == status.HTTP_201_CREATED
            data = response.json()
            
            assert "id" in data
            assert data["success_probability"] == 0.75
            assert data["expected_final_value"] == 1200000
            assert data["num_simulations"] == 1000
    
    @pytest.mark.asyncio
    async def test_get_simulation_results(self, authenticated_client: AsyncClient):
        """Test retrieving simulation results."""
        
        # First create a simulation
        simulation_request = {
            "portfolio_allocation": {"stocks": 0.6, "bonds": 0.3, "cash": 0.1},
            "time_horizon_years": 20,
            "initial_investment": 50000,
            "monthly_contribution": 2000,
            "num_simulations": 500
        }
        
        with patch('app.simulations.engine.MonteCarloEngine') as mock_engine:
            mock_result = Mock(
                id="sim_123",
                success_probability=0.8,
                expected_final_value=1500000,
                percentile_10=1000000,
                percentile_50=1500000,
                percentile_90=2000000
            )
            mock_engine_instance = AsyncMock()
            mock_engine_instance.run_simulation.return_value = mock_result
            mock_engine.return_value = mock_engine_instance
            
            create_response = await authenticated_client.post(
                "/api/v1/simulations/monte-carlo",
                json=simulation_request
            )
            simulation_id = create_response.json()["id"]
            
            # Now retrieve the results
            get_response = await authenticated_client.get(
                f"/api/v1/simulations/{simulation_id}"
            )
            
            assert get_response.status_code == status.HTTP_200_OK
            data = get_response.json()
            
            assert data["id"] == simulation_id
            assert data["success_probability"] == 0.8
    
    @pytest.mark.asyncio
    async def test_simulation_comparison(self, authenticated_client: AsyncClient):
        """Test comparing multiple simulations."""
        
        simulation_ids = ["sim_1", "sim_2", "sim_3"]
        
        with patch('app.services.simulation_service.SimulationService') as mock_service:
            mock_service_instance = AsyncMock()
            mock_service_instance.compare_simulations.return_value = {
                "comparison_results": {
                    "sim_1": {"success_probability": 0.75, "expected_value": 1200000},
                    "sim_2": {"success_probability": 0.80, "expected_value": 1350000},
                    "sim_3": {"success_probability": 0.70, "expected_value": 1100000}
                },
                "best_simulation": "sim_2",
                "key_insights": [
                    "Simulation 2 shows highest success probability",
                    "Increased stock allocation improves long-term outcomes"
                ]
            }
            mock_service.return_value = mock_service_instance
            
            response = await authenticated_client.post(
                "/api/v1/simulations/compare",
                json={"simulation_ids": simulation_ids}
            )
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            
            assert "comparison_results" in data
            assert "best_simulation" in data
            assert data["best_simulation"] == "sim_2"
            assert "key_insights" in data
    
    @pytest.mark.asyncio
    async def test_simulation_scenario_analysis(self, authenticated_client: AsyncClient):
        """Test scenario analysis for simulations."""
        
        scenario_request = {
            "base_simulation_id": "sim_123",
            "scenarios": [
                {
                    "name": "market_crash",
                    "adjustments": {
                        "stock_return_reduction": 0.15,
                        "volatility_increase": 0.10
                    }
                },
                {
                    "name": "high_inflation",
                    "adjustments": {
                        "inflation_rate": 0.06,
                        "interest_rate_increase": 0.02
                    }
                }
            ]
        }
        
        with patch('app.simulations.engine.MonteCarloEngine') as mock_engine:
            mock_engine_instance = AsyncMock()
            mock_engine_instance.run_scenario_analysis.return_value = {
                "base_scenario": {"success_probability": 0.75},
                "scenario_results": {
                    "market_crash": {"success_probability": 0.60, "impact": -0.15},
                    "high_inflation": {"success_probability": 0.65, "impact": -0.10}
                },
                "recommendations": [
                    "Consider increasing bond allocation during market volatility",
                    "Maintain higher cash reserves during inflationary periods"
                ]
            }
            mock_engine.return_value = mock_engine_instance
            
            response = await authenticated_client.post(
                "/api/v1/simulations/scenario-analysis",
                json=scenario_request
            )
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            
            assert "base_scenario" in data
            assert "scenario_results" in data
            assert "recommendations" in data
            assert len(data["scenario_results"]) == 2


class TestInvestmentEndpoints:
    """Test investment tracking endpoints."""
    
    @pytest.mark.asyncio
    async def test_add_investment(self, authenticated_client: AsyncClient):
        """Test adding an investment."""
        
        investment_data = {
            "symbol": "AAPL",
            "quantity": 10.0,
            "purchase_price": 150.00,
            "purchase_date": "2024-01-15",
            "investment_type": "stock",
            "account_type": "taxable"
        }
        
        response = await authenticated_client.post(
            "/api/v1/investments",
            json=investment_data
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        
        assert data["symbol"] == investment_data["symbol"]
        assert data["quantity"] == investment_data["quantity"]
        assert data["purchase_price"] == investment_data["purchase_price"]
    
    @pytest.mark.asyncio
    async def test_get_portfolio_summary(self, authenticated_client: AsyncClient):
        """Test getting portfolio summary."""
        
        with patch('app.services.investment_service.InvestmentService') as mock_service:
            mock_service_instance = AsyncMock()
            mock_service_instance.get_portfolio_summary.return_value = {
                "total_value": 125000.00,
                "total_cost_basis": 100000.00,
                "unrealized_gain_loss": 25000.00,
                "allocation": {
                    "stocks": 0.70,
                    "bonds": 0.20,
                    "cash": 0.10
                },
                "top_holdings": [
                    {"symbol": "AAPL", "value": 15000, "percentage": 0.12},
                    {"symbol": "GOOGL", "value": 12000, "percentage": 0.096}
                ]
            }
            mock_service.return_value = mock_service_instance
            
            response = await authenticated_client.get("/api/v1/investments/portfolio/summary")
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            
            assert data["total_value"] == 125000.00
            assert data["unrealized_gain_loss"] == 25000.00
            assert "allocation" in data
            assert "top_holdings" in data
    
    @pytest.mark.asyncio
    async def test_portfolio_performance_analysis(self, authenticated_client: AsyncClient):
        """Test portfolio performance analysis."""
        
        with patch('app.services.investment_service.InvestmentService') as mock_service:
            mock_service_instance = AsyncMock()
            mock_service_instance.analyze_portfolio_performance.return_value = {
                "returns": {
                    "1_month": 0.025,
                    "3_months": 0.078,
                    "1_year": 0.124,
                    "ytd": 0.089
                },
                "risk_metrics": {
                    "volatility": 0.145,
                    "sharpe_ratio": 1.23,
                    "max_drawdown": -0.089
                },
                "benchmark_comparison": {
                    "sp500_outperformance": 0.015,
                    "risk_adjusted_performance": "outperforming"
                }
            }
            mock_service.return_value = mock_service_instance
            
            response = await authenticated_client.get(
                "/api/v1/investments/portfolio/performance"
            )
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            
            assert "returns" in data
            assert "risk_metrics" in data
            assert "benchmark_comparison" in data
            assert data["risk_metrics"]["sharpe_ratio"] == 1.23


class TestBankingIntegrationEndpoints:
    """Test banking integration endpoints."""
    
    @pytest.mark.asyncio
    async def test_plaid_link_token_creation(self, authenticated_client: AsyncClient):
        """Test creating Plaid Link token."""
        
        with patch('app.services.banking.plaid_service.PlaidService') as mock_plaid:
            mock_plaid_instance = AsyncMock()
            mock_plaid_instance.create_link_token.return_value = {
                "link_token": "link-sandbox-12345",
                "expiration": "2024-01-01T12:00:00Z"
            }
            mock_plaid.return_value = mock_plaid_instance
            
            response = await authenticated_client.post("/api/v1/banking/plaid/link-token")
            
            assert response.status_code == status.HTTP_201_CREATED
            data = response.json()
            
            assert "link_token" in data
            assert "expiration" in data
    
    @pytest.mark.asyncio
    async def test_plaid_public_token_exchange(self, authenticated_client: AsyncClient):
        """Test exchanging Plaid public token for access token."""
        
        exchange_request = {
            "public_token": "public-sandbox-token-123"
        }
        
        with patch('app.services.banking.plaid_service.PlaidService') as mock_plaid:
            mock_plaid_instance = AsyncMock()
            mock_plaid_instance.exchange_public_token.return_value = {
                "access_token": "access-sandbox-12345",
                "item_id": "item_456"
            }
            mock_plaid.return_value = mock_plaid_instance
            
            response = await authenticated_client.post(
                "/api/v1/banking/plaid/token-exchange",
                json=exchange_request
            )
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            
            assert "access_token" in data
            assert "item_id" in data
    
    @pytest.mark.asyncio
    async def test_get_bank_accounts(self, authenticated_client: AsyncClient):
        """Test retrieving bank accounts."""
        
        with patch('app.services.banking.bank_aggregator.BankAggregator') as mock_aggregator:
            mock_aggregator_instance = AsyncMock()
            mock_aggregator_instance.get_all_accounts.return_value = [
                {
                    "id": "account_1",
                    "name": "Checking Account",
                    "type": "checking",
                    "balance": 2500.75,
                    "currency": "USD",
                    "provider": "plaid"
                },
                {
                    "id": "account_2",
                    "name": "Savings Account",
                    "type": "savings",
                    "balance": 15000.00,
                    "currency": "USD",
                    "provider": "plaid"
                }
            ]
            mock_aggregator.return_value = mock_aggregator_instance
            
            response = await authenticated_client.get("/api/v1/banking/accounts")
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            
            assert isinstance(data, list)
            assert len(data) == 2
            assert data[0]["type"] == "checking"
            assert data[1]["type"] == "savings"
    
    @pytest.mark.asyncio
    async def test_get_transactions(self, authenticated_client: AsyncClient):
        """Test retrieving bank transactions."""
        
        query_params = {
            "start_date": "2024-01-01",
            "end_date": "2024-01-31",
            "account_id": "account_1"
        }
        
        with patch('app.services.banking.bank_aggregator.BankAggregator') as mock_aggregator:
            mock_aggregator_instance = AsyncMock()
            mock_aggregator_instance.get_transactions.return_value = [
                {
                    "id": "txn_1",
                    "date": "2024-01-15",
                    "description": "Netflix Subscription",
                    "amount": 15.99,
                    "category": "Entertainment",
                    "account_id": "account_1"
                },
                {
                    "id": "txn_2",
                    "date": "2024-01-10",
                    "description": "Grocery Store",
                    "amount": 87.45,
                    "category": "Food & Dining",
                    "account_id": "account_1"
                }
            ]
            mock_aggregator.return_value = mock_aggregator_instance
            
            response = await authenticated_client.get(
                "/api/v1/banking/transactions",
                params=query_params
            )
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            
            assert isinstance(data, list)
            assert len(data) == 2
            assert data[0]["description"] == "Netflix Subscription"
    
    @pytest.mark.asyncio
    async def test_spending_analysis(self, authenticated_client: AsyncClient):
        """Test spending pattern analysis."""
        
        with patch('app.services.banking.spending_pattern_detector.SpendingPatternDetector') as mock_detector:
            mock_detector_instance = AsyncMock()
            mock_detector_instance.analyze_spending_patterns.return_value = {
                "monthly_spending_by_category": {
                    "Food & Dining": 450.00,
                    "Transportation": 280.00,
                    "Entertainment": 150.00,
                    "Shopping": 320.00
                },
                "spending_trends": {
                    "overall_trend": "increasing",
                    "trend_percentage": 0.08
                },
                "recurring_transactions": [
                    {
                        "merchant": "Netflix",
                        "amount": 15.99,
                        "frequency": "monthly",
                        "category": "Entertainment"
                    }
                ]
            }
            mock_detector.return_value = mock_detector_instance
            
            response = await authenticated_client.get("/api/v1/banking/spending-analysis")
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            
            assert "monthly_spending_by_category" in data
            assert "spending_trends" in data
            assert "recurring_transactions" in data
            assert data["spending_trends"]["overall_trend"] == "increasing"


class TestAIRecommendationsEndpoints:
    """Test AI-powered recommendations endpoints."""
    
    @pytest.mark.asyncio
    async def test_get_personalized_recommendations(self, authenticated_client: AsyncClient,
                                                  test_financial_profile: FinancialProfile):
        """Test getting personalized AI recommendations."""
        
        with patch('app.ai.recommendation_engine.RecommendationEngine') as mock_engine:
            mock_engine_instance = AsyncMock()
            mock_engine_instance.generate_comprehensive_recommendations.return_value = {
                "investment_recommendations": [
                    {
                        "type": "portfolio_rebalancing",
                        "description": "Consider rebalancing your portfolio to 65% stocks, 25% bonds, 10% cash",
                        "priority": "high",
                        "expected_impact": "Improve risk-adjusted returns by 0.8% annually"
                    }
                ],
                "risk_management": [
                    {
                        "type": "emergency_fund",
                        "description": "Increase emergency fund to cover 6 months of expenses",
                        "priority": "high",
                        "target_amount": 27000
                    }
                ],
                "behavioral_insights": [
                    {
                        "insight": "You tend to check your portfolio frequently during market volatility",
                        "recommendation": "Consider reducing portfolio check frequency to monthly"
                    }
                ]
            }
            mock_engine.return_value = mock_engine_instance
            
            response = await authenticated_client.get("/api/v1/ai/recommendations")
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            
            assert "investment_recommendations" in data
            assert "risk_management" in data
            assert "behavioral_insights" in data
            assert len(data["investment_recommendations"]) >= 1
    
    @pytest.mark.asyncio
    async def test_generate_financial_narrative(self, authenticated_client: AsyncClient,
                                              test_financial_profile: FinancialProfile):
        """Test generating financial narrative."""
        
        with patch('app.ai.narrative_generator.NarrativeGenerator') as mock_generator:
            mock_generator_instance = AsyncMock()
            mock_generator_instance.generate_comprehensive_narrative.return_value = {
                "executive_summary": "Your financial position shows strong fundamentals with room for optimization in investment allocation.",
                "detailed_analysis": {
                    "strengths": [
                        "Healthy savings rate of 20%",
                        "Diversified income sources",
                        "Conservative debt management"
                    ],
                    "areas_for_improvement": [
                        "Portfolio could benefit from increased stock allocation",
                        "Consider maximizing 401k contributions"
                    ]
                },
                "action_plan": [
                    "Increase stock allocation to 70% over next 6 months",
                    "Set up automatic monthly contributions",
                    "Review and optimize tax-advantaged accounts"
                ]
            }
            mock_generator.return_value = mock_generator_instance
            
            response = await authenticated_client.get("/api/v1/ai/financial-narrative")
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            
            assert "executive_summary" in data
            assert "detailed_analysis" in data
            assert "action_plan" in data
            assert len(data["action_plan"]) >= 1
    
    @pytest.mark.asyncio
    async def test_ai_chat_interaction(self, authenticated_client: AsyncClient):
        """Test AI chat interaction endpoint."""
        
        chat_request = {
            "message": "How can I improve my retirement savings?",
            "context": {
                "current_savings": 50000,
                "age": 35,
                "retirement_age": 65
            }
        }
        
        with patch('app.ai.llm_client.LLMClient') as mock_llm:
            mock_llm_instance = AsyncMock()
            mock_llm_instance.generate_completion.return_value = Mock(
                content="Based on your current savings and age, I recommend increasing your retirement contributions by 15% if possible. Consider maximizing your 401k match and opening a Roth IRA for tax diversification."
            )
            mock_llm.return_value = mock_llm_instance
            
            response = await authenticated_client.post(
                "/api/v1/ai/chat",
                json=chat_request
            )
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            
            assert "response" in data
            assert "retirement" in data["response"].lower()
            assert "conversation_id" in data
    
    @pytest.mark.asyncio
    async def test_ml_risk_assessment(self, authenticated_client: AsyncClient,
                                    test_financial_profile: FinancialProfile):
        """Test ML-based risk assessment."""
        
        with patch('app.ml.recommendations.risk_predictor.RiskPredictor') as mock_predictor:
            mock_predictor_instance = AsyncMock()
            mock_predictor_instance.assess_comprehensive_risk.return_value = {
                "overall_risk_score": 65,
                "risk_factors": {
                    "market_risk": 70,
                    "inflation_risk": 55,
                    "longevity_risk": 60,
                    "liquidity_risk": 30
                },
                "risk_tolerance_match": {
                    "stated_tolerance": "moderate",
                    "behavioral_tolerance": "conservative",
                    "recommended_tolerance": "moderate_conservative"
                },
                "recommendations": [
                    "Consider increasing bond allocation by 5%",
                    "Build larger emergency fund for liquidity buffer"
                ]
            }
            mock_predictor.return_value = mock_predictor_instance
            
            response = await authenticated_client.get("/api/v1/ai/risk-assessment")
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            
            assert "overall_risk_score" in data
            assert "risk_factors" in data
            assert "risk_tolerance_match" in data
            assert data["overall_risk_score"] == 65


class TestPDFExportEndpoints:
    """Test PDF export endpoints."""
    
    @pytest.mark.asyncio
    async def test_generate_financial_plan_pdf(self, authenticated_client: AsyncClient,
                                             test_financial_profile: FinancialProfile,
                                             test_goal: Goal):
        """Test generating financial plan PDF."""
        
        pdf_request = {
            "template_type": "comprehensive_plan",
            "include_charts": True,
            "include_projections": True,
            "custom_branding": {
                "company_name": "AI Financial Planner",
                "logo_url": "https://example.com/logo.png"
            }
        }
        
        with patch('app.services.pdf_generator.PDFGenerator') as mock_generator:
            mock_generator_instance = AsyncMock()
            mock_generator_instance.generate_financial_plan_pdf.return_value = {
                "pdf_id": "pdf_123",
                "download_url": "https://example.com/pdfs/plan_123.pdf",
                "expires_at": "2024-01-08T00:00:00Z"
            }
            mock_generator.return_value = mock_generator_instance
            
            response = await authenticated_client.post(
                "/api/v1/pdf/financial-plan",
                json=pdf_request
            )
            
            assert response.status_code == status.HTTP_201_CREATED
            data = response.json()
            
            assert "pdf_id" in data
            assert "download_url" in data
            assert "expires_at" in data
    
    @pytest.mark.asyncio
    async def test_download_pdf(self, authenticated_client: AsyncClient):
        """Test downloading generated PDF."""
        
        pdf_id = "pdf_123"
        
        with patch('app.services.pdf_generator.PDFGenerator') as mock_generator:
            mock_pdf_content = b"Mock PDF content"
            mock_generator_instance = AsyncMock()
            mock_generator_instance.get_pdf_content.return_value = mock_pdf_content
            mock_generator.return_value = mock_generator_instance
            
            response = await authenticated_client.get(f"/api/v1/pdf/download/{pdf_id}")
            
            assert response.status_code == status.HTTP_200_OK
            assert response.headers["content-type"] == "application/pdf"
            assert response.content == mock_pdf_content


class TestRealTimeUpdatesEndpoints:
    """Test real-time updates via WebSocket."""
    
    @pytest.mark.asyncio
    async def test_websocket_connection(self, authenticated_client: AsyncClient):
        """Test WebSocket connection for real-time updates."""
        
        with patch('app.services.websocket_manager.WebSocketManager') as mock_manager:
            mock_manager_instance = Mock()
            mock_manager_instance.connect_user.return_value = True
            mock_manager.return_value = mock_manager_instance
            
            # Test WebSocket connection endpoint
            response = await authenticated_client.get("/api/v1/ws/connect")
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            
            assert "connection_id" in data
            assert "websocket_url" in data
    
    @pytest.mark.asyncio
    async def test_portfolio_updates_subscription(self, authenticated_client: AsyncClient):
        """Test subscribing to portfolio updates."""
        
        subscription_request = {
            "subscription_type": "portfolio_updates",
            "update_frequency": "real_time",
            "symbols": ["AAPL", "GOOGL", "MSFT"]
        }
        
        response = await authenticated_client.post(
            "/api/v1/ws/subscribe",
            json=subscription_request
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert "subscription_id" in data
        assert "status" in data
        assert data["status"] == "active"


class TestErrorHandlingAndValidation:
    """Test error handling and input validation."""
    
    @pytest.mark.asyncio
    async def test_404_error_handling(self, authenticated_client: AsyncClient):
        """Test 404 error handling."""
        
        response = await authenticated_client.get("/api/v1/nonexistent-endpoint")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert "detail" in data
    
    @pytest.mark.asyncio
    async def test_422_validation_error(self, authenticated_client: AsyncClient):
        """Test input validation errors."""
        
        invalid_goal_data = {
            "name": "",  # Empty name
            "target_amount": -1000,  # Negative amount
            "target_date": "invalid-date",  # Invalid date format
            "goal_type": "invalid_type"  # Invalid goal type
        }
        
        response = await authenticated_client.post(
            "/api/v1/goals",
            json=invalid_goal_data
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        data = response.json()
        
        assert "detail" in data
        assert isinstance(data["detail"], list)
        assert len(data["detail"]) >= 4  # Multiple validation errors
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self, authenticated_client: AsyncClient):
        """Test API rate limiting."""
        
        # Make multiple rapid requests
        responses = []
        for _ in range(100):  # Exceed rate limit
            response = await authenticated_client.get("/api/v1/users/me")
            responses.append(response)
        
        # Should eventually get rate limited
        rate_limited_responses = [r for r in responses 
                                if r.status_code == status.HTTP_429_TOO_MANY_REQUESTS]
        
        assert len(rate_limited_responses) > 0
    
    @pytest.mark.asyncio
    async def test_server_error_handling(self, authenticated_client: AsyncClient):
        """Test server error handling."""
        
        # Mock a service that raises an exception
        with patch('app.services.financial_profile_service.FinancialProfileService') as mock_service:
            mock_service_instance = AsyncMock()
            mock_service_instance.get_profile.side_effect = Exception("Database connection failed")
            mock_service.return_value = mock_service_instance
            
            response = await authenticated_client.get("/api/v1/financial-profiles/123")
            
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            data = response.json()
            
            assert "detail" in data
            # Should not expose internal error details in production
            assert "Database connection failed" not in data["detail"]
    
    @pytest.mark.asyncio
    async def test_cors_handling(self, test_client: AsyncClient):
        """Test CORS handling for cross-origin requests."""
        
        headers = {
            "Origin": "https://example.com",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type,Authorization"
        }
        
        # Preflight request
        response = await test_client.options("/api/v1/auth/login", headers=headers)
        
        assert response.status_code == status.HTTP_200_OK
        assert "Access-Control-Allow-Origin" in response.headers
        assert "Access-Control-Allow-Methods" in response.headers
        assert "Access-Control-Allow-Headers" in response.headers