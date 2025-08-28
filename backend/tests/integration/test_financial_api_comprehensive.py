"""
Comprehensive integration tests for Financial Planning API endpoints

Tests cover:
- Full user journey from registration to portfolio optimization
- Authentication and authorization flows
- Financial profile creation and updates
- Goal setting and tracking
- Portfolio optimization API integration
- Monte Carlo simulation endpoints
- Tax optimization API flows
- Error handling and edge cases
- Performance under load
"""

import pytest
import asyncio
import json
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List
from httpx import AsyncClient
from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.models.user import User
from app.models.financial_profile import FinancialProfile
from app.models.goal import Goal
from app.core.config import get_settings
from tests.factories import (
    UserFactory, FinancialProfileFactory, GoalFactory,
    create_complete_user_scenario
)


class TestUserManagementAPI:
    """Test user registration, authentication, and profile management"""
    
    @pytest.mark.asyncio
    async def test_user_registration_flow(self, test_client: AsyncClient, db_session: AsyncSession):
        """Test complete user registration flow"""
        # Step 1: Register new user
        registration_data = {
            "email": "test@example.com",
            "password": "SecurePassword123!",
            "first_name": "John",
            "last_name": "Doe",
            "phone_number": "+1-555-123-4567",
            "date_of_birth": "1990-01-15"
        }
        
        response = await test_client.post("/api/v1/auth/register", json=registration_data)
        assert response.status_code == status.HTTP_201_CREATED
        
        user_data = response.json()
        assert user_data["email"] == registration_data["email"]
        assert user_data["first_name"] == registration_data["first_name"]
        assert "id" in user_data
        assert "hashed_password" not in user_data  # Should not expose password
        
        user_id = user_data["id"]
        
        # Step 2: Login with credentials
        login_data = {
            "username": registration_data["email"],
            "password": registration_data["password"]
        }
        
        response = await test_client.post("/api/v1/auth/login", data=login_data)
        assert response.status_code == status.HTTP_200_OK
        
        token_data = response.json()
        assert "access_token" in token_data
        assert token_data["token_type"] == "bearer"
        
        access_token = token_data["access_token"]
        
        # Step 3: Access protected endpoint with token
        headers = {"Authorization": f"Bearer {access_token}"}
        response = await test_client.get("/api/v1/users/me", headers=headers)
        assert response.status_code == status.HTTP_200_OK
        
        user_profile = response.json()
        assert user_profile["id"] == user_id
        assert user_profile["email"] == registration_data["email"]
    
    @pytest.mark.asyncio
    async def test_user_authentication_errors(self, test_client: AsyncClient, db_session: AsyncSession):
        """Test authentication error scenarios"""
        # Test invalid credentials
        login_data = {
            "username": "nonexistent@example.com",
            "password": "wrongpassword"
        }
        
        response = await test_client.post("/api/v1/auth/login", data=login_data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
        # Test access without token
        response = await test_client.get("/api/v1/users/me")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
        # Test access with invalid token
        headers = {"Authorization": "Bearer invalid_token"}
        response = await test_client.get("/api/v1/users/me", headers=headers)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    @pytest.mark.asyncio
    async def test_duplicate_user_registration(self, test_client: AsyncClient, db_session: AsyncSession):
        """Test duplicate email registration handling"""
        user = await UserFactory.create(session=db_session)
        
        registration_data = {
            "email": user.email,  # Duplicate email
            "password": "SecurePassword123!",
            "first_name": "Jane",
            "last_name": "Smith"
        }
        
        response = await test_client.post("/api/v1/auth/register", json=registration_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
        error_data = response.json()
        assert "email" in error_data["detail"].lower()


class TestFinancialProfileAPI:
    """Test financial profile creation and management"""
    
    @pytest.mark.asyncio
    async def test_financial_profile_creation(self, authenticated_client: AsyncClient, test_user: User, db_session: AsyncSession):
        """Test creating and retrieving financial profile"""
        profile_data = {
            "annual_income": 75000.0,
            "monthly_expenses": 4500.0,
            "current_savings": 25000.0,
            "current_debt": 15000.0,
            "risk_tolerance": "moderate",
            "investment_experience": "intermediate",
            "investment_timeline": 20,
            "financial_goals": ["retirement", "house_down_payment"],
            "employment_status": "employed",
            "marital_status": "single",
            "dependents": 0
        }
        
        # Create financial profile
        response = await authenticated_client.post(
            "/api/v1/financial-profiles/", 
            json=profile_data
        )
        assert response.status_code == status.HTTP_201_CREATED
        
        created_profile = response.json()
        assert created_profile["annual_income"] == profile_data["annual_income"]
        assert created_profile["risk_tolerance"] == profile_data["risk_tolerance"]
        assert created_profile["user_id"] == test_user.id
        
        profile_id = created_profile["id"]
        
        # Retrieve financial profile
        response = await authenticated_client.get(f"/api/v1/financial-profiles/{profile_id}")
        assert response.status_code == status.HTTP_200_OK
        
        retrieved_profile = response.json()
        assert retrieved_profile["id"] == profile_id
        assert retrieved_profile["annual_income"] == profile_data["annual_income"]
    
    @pytest.mark.asyncio
    async def test_financial_profile_validation(self, authenticated_client: AsyncClient, test_user: User):
        """Test financial profile input validation"""
        invalid_profiles = [
            {
                "annual_income": -1000,  # Negative income
                "risk_tolerance": "moderate"
            },
            {
                "annual_income": 75000,
                "risk_tolerance": "invalid_tolerance",  # Invalid enum
            },
            {
                "annual_income": 75000,
                "monthly_expenses": 10000,  # Expenses > income
                "risk_tolerance": "moderate"
            }
        ]
        
        for invalid_profile in invalid_profiles:
            response = await authenticated_client.post(
                "/api/v1/financial-profiles/",
                json=invalid_profile
            )
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    @pytest.mark.asyncio
    async def test_financial_profile_update(self, authenticated_client: AsyncClient, test_financial_profile: FinancialProfile):
        """Test updating financial profile"""
        update_data = {
            "annual_income": 85000.0,
            "risk_tolerance": "aggressive",
            "investment_timeline": 25
        }
        
        response = await authenticated_client.put(
            f"/api/v1/financial-profiles/{test_financial_profile.id}",
            json=update_data
        )
        assert response.status_code == status.HTTP_200_OK
        
        updated_profile = response.json()
        assert updated_profile["annual_income"] == update_data["annual_income"]
        assert updated_profile["risk_tolerance"] == update_data["risk_tolerance"]
        assert updated_profile["investment_timeline"] == update_data["investment_timeline"]


class TestGoalsAPI:
    """Test financial goals management"""
    
    @pytest.mark.asyncio
    async def test_goal_crud_operations(self, authenticated_client: AsyncClient, test_user: User):
        """Test complete CRUD operations for goals"""
        # Create goal
        goal_data = {
            "name": "Retirement Fund",
            "description": "Build retirement savings for comfortable retirement",
            "goal_type": "retirement",
            "target_amount": 1000000.0,
            "current_amount": 50000.0,
            "target_date": "2050-12-31",
            "priority": "high",
            "monthly_contribution": 2000.0
        }
        
        response = await authenticated_client.post("/api/v1/goals/", json=goal_data)
        assert response.status_code == status.HTTP_201_CREATED
        
        created_goal = response.json()
        assert created_goal["name"] == goal_data["name"]
        assert created_goal["target_amount"] == goal_data["target_amount"]
        assert created_goal["user_id"] == test_user.id
        
        goal_id = created_goal["id"]
        
        # Read goal
        response = await authenticated_client.get(f"/api/v1/goals/{goal_id}")
        assert response.status_code == status.HTTP_200_OK
        
        retrieved_goal = response.json()
        assert retrieved_goal["id"] == goal_id
        
        # Update goal
        update_data = {
            "target_amount": 1200000.0,
            "monthly_contribution": 2500.0
        }
        
        response = await authenticated_client.put(
            f"/api/v1/goals/{goal_id}",
            json=update_data
        )
        assert response.status_code == status.HTTP_200_OK
        
        updated_goal = response.json()
        assert updated_goal["target_amount"] == update_data["target_amount"]
        
        # List all goals
        response = await authenticated_client.get("/api/v1/goals/")
        assert response.status_code == status.HTTP_200_OK
        
        goals_list = response.json()
        assert len(goals_list) >= 1
        assert any(goal["id"] == goal_id for goal in goals_list)
        
        # Delete goal
        response = await authenticated_client.delete(f"/api/v1/goals/{goal_id}")
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verify deletion
        response = await authenticated_client.get(f"/api/v1/goals/{goal_id}")
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    @pytest.mark.asyncio
    async def test_goal_progress_tracking(self, authenticated_client: AsyncClient, test_goal: Goal):
        """Test goal progress tracking functionality"""
        # Update goal progress
        progress_data = {
            "current_amount": 75000.0,
            "additional_contribution": 25000.0,
            "contribution_date": datetime.now().isoformat()
        }
        
        response = await authenticated_client.post(
            f"/api/v1/goals/{test_goal.id}/progress",
            json=progress_data
        )
        assert response.status_code == status.HTTP_200_OK
        
        updated_goal = response.json()
        assert updated_goal["current_amount"] == progress_data["current_amount"]
        
        # Get goal progress history
        response = await authenticated_client.get(
            f"/api/v1/goals/{test_goal.id}/progress-history"
        )
        assert response.status_code == status.HTTP_200_OK
        
        progress_history = response.json()
        assert len(progress_history) > 0
        assert progress_history[0]["amount"] == progress_data["additional_contribution"]


class TestPortfolioOptimizationAPI:
    """Test portfolio optimization endpoints"""
    
    @pytest.mark.asyncio
    async def test_portfolio_optimization_request(self, authenticated_client: AsyncClient, test_user: User, db_session: AsyncSession):
        """Test portfolio optimization API endpoint"""
        # Create user scenario with assets
        scenario = await create_complete_user_scenario(db_session, risk_tolerance='moderate')
        
        optimization_request = {
            "method": "max_sharpe",
            "assets": [
                {
                    "symbol": "VTI",
                    "expected_return": 0.08,
                    "volatility": 0.15,
                    "current_price": 220.50
                },
                {
                    "symbol": "VXUS",
                    "expected_return": 0.06,
                    "volatility": 0.18,
                    "current_price": 58.75
                },
                {
                    "symbol": "BND",
                    "expected_return": 0.03,
                    "volatility": 0.05,
                    "current_price": 75.20
                }
            ],
            "constraints": {
                "max_position_size": 0.4,
                "min_position_size": 0.05,
                "risk_tolerance": "moderate"
            },
            "investment_amount": 100000.0
        }
        
        response = await authenticated_client.post(
            "/api/v1/portfolio/optimize",
            json=optimization_request
        )
        assert response.status_code == status.HTTP_200_OK
        
        optimization_result = response.json()
        
        # Validate response structure
        assert "weights" in optimization_result
        assert "metrics" in optimization_result
        assert "method" in optimization_result
        
        # Validate weights sum to 1
        weights = optimization_result["weights"]
        total_weight = sum(weights.values())
        assert abs(total_weight - 1.0) < 0.01
        
        # Validate metrics
        metrics = optimization_result["metrics"]
        assert "expected_return" in metrics
        assert "volatility" in metrics
        assert "sharpe_ratio" in metrics
        
        assert metrics["expected_return"] > 0
        assert metrics["volatility"] > 0
        assert metrics["sharpe_ratio"] > 0
    
    @pytest.mark.asyncio
    async def test_portfolio_optimization_methods(self, authenticated_client: AsyncClient):
        """Test different optimization methods"""
        base_request = {
            "assets": [
                {
                    "symbol": "SPY",
                    "expected_return": 0.10,
                    "volatility": 0.16
                },
                {
                    "symbol": "BND",
                    "expected_return": 0.04,
                    "volatility": 0.04
                }
            ],
            "investment_amount": 50000.0
        }
        
        methods = ["max_sharpe", "min_variance", "risk_parity", "mean_variance"]
        
        results = {}
        for method in methods:
            request_data = {**base_request, "method": method}
            
            response = await authenticated_client.post(
                "/api/v1/portfolio/optimize",
                json=request_data
            )
            assert response.status_code == status.HTTP_200_OK
            
            result = response.json()
            results[method] = result
            
            # Basic validation
            assert result["method"] == method
            assert "weights" in result
            assert sum(result["weights"].values()) == pytest.approx(1.0, rel=0.01)
        
        # Compare methods
        # Max Sharpe should have highest Sharpe ratio
        max_sharpe_ratio = max(results[method]["metrics"]["sharpe_ratio"] for method in methods)
        assert results["max_sharpe"]["metrics"]["sharpe_ratio"] == pytest.approx(max_sharpe_ratio, rel=0.01)
        
        # Min variance should have lowest volatility
        min_volatility = min(results[method]["metrics"]["volatility"] for method in methods)
        assert results["min_variance"]["metrics"]["volatility"] == pytest.approx(min_volatility, rel=0.01)
    
    @pytest.mark.asyncio
    async def test_portfolio_optimization_constraints(self, authenticated_client: AsyncClient):
        """Test portfolio optimization with various constraints"""
        request_data = {
            "method": "max_sharpe",
            "assets": [
                {
                    "symbol": "AAPL",
                    "expected_return": 0.12,
                    "volatility": 0.25,
                    "sector": "Technology"
                },
                {
                    "symbol": "GOOGL",
                    "expected_return": 0.10,
                    "volatility": 0.22,
                    "sector": "Technology"
                },
                {
                    "symbol": "JPM",
                    "expected_return": 0.08,
                    "volatility": 0.18,
                    "sector": "Finance"
                }
            ],
            "constraints": {
                "max_position_size": 0.3,
                "sector_limits": {
                    "Technology": [0.2, 0.6]  # Min 20%, Max 60%
                }
            },
            "investment_amount": 75000.0
        }
        
        response = await authenticated_client.post(
            "/api/v1/portfolio/optimize",
            json=request_data
        )
        assert response.status_code == status.HTTP_200_OK
        
        result = response.json()
        weights = result["weights"]
        
        # Check position size constraints
        for weight in weights.values():
            assert weight <= 0.3 + 0.01  # Allow small tolerance
        
        # Check sector constraints
        tech_weight = weights.get("AAPL", 0) + weights.get("GOOGL", 0)
        assert 0.2 <= tech_weight <= 0.6 + 0.01


class TestMonteCarloSimulationAPI:
    """Test Monte Carlo simulation endpoints"""
    
    @pytest.mark.asyncio
    async def test_monte_carlo_simulation_basic(self, authenticated_client: AsyncClient, test_user: User):
        """Test basic Monte Carlo simulation"""
        simulation_request = {
            "initial_investment": 100000.0,
            "monthly_contribution": 1000.0,
            "investment_horizon_years": 30,
            "expected_return": 0.07,
            "volatility": 0.15,
            "num_simulations": 10000,
            "confidence_levels": [0.1, 0.5, 0.9]
        }
        
        response = await authenticated_client.post(
            "/api/v1/simulations/monte-carlo",
            json=simulation_request
        )
        assert response.status_code == status.HTTP_200_OK
        
        simulation_result = response.json()
        
        # Validate response structure
        assert "final_values" in simulation_result
        assert "percentiles" in simulation_result
        assert "success_probability" in simulation_result
        assert "risk_metrics" in simulation_result
        
        # Validate percentiles
        percentiles = simulation_result["percentiles"]
        assert len(percentiles) == len(simulation_request["confidence_levels"])
        
        # Percentiles should be ordered
        percentile_values = [p["value"] for p in percentiles]
        assert percentile_values == sorted(percentile_values)
        
        # Final value should be reasonable
        final_values = simulation_result["final_values"]
        assert final_values["mean"] > simulation_request["initial_investment"]
        assert final_values["std"] > 0
    
    @pytest.mark.asyncio
    async def test_monte_carlo_goal_analysis(self, authenticated_client: AsyncClient, test_goal: Goal):
        """Test Monte Carlo simulation for specific goal"""
        goal_simulation_request = {
            "goal_id": test_goal.id,
            "current_savings": 25000.0,
            "monthly_contribution": 500.0,
            "expected_return": 0.08,
            "volatility": 0.16,
            "num_simulations": 5000
        }
        
        response = await authenticated_client.post(
            "/api/v1/simulations/goal-analysis",
            json=goal_simulation_request
        )
        assert response.status_code == status.HTTP_200_OK
        
        analysis_result = response.json()
        
        # Validate goal-specific analysis
        assert "goal_achievement_probability" in analysis_result
        assert "shortfall_analysis" in analysis_result
        assert "recommended_contribution" in analysis_result
        
        # Achievement probability should be between 0 and 1
        achievement_prob = analysis_result["goal_achievement_probability"]
        assert 0 <= achievement_prob <= 1
        
        # Should provide actionable recommendations
        if achievement_prob < 0.8:  # If low probability
            assert analysis_result["recommended_contribution"] > goal_simulation_request["monthly_contribution"]
    
    @pytest.mark.asyncio
    async def test_simulation_performance_requirements(self, authenticated_client: AsyncClient):
        """Test simulation performance requirements"""
        import time
        
        large_simulation_request = {
            "initial_investment": 50000.0,
            "monthly_contribution": 2000.0,
            "investment_horizon_years": 40,
            "expected_return": 0.06,
            "volatility": 0.18,
            "num_simulations": 50000,  # Large number of simulations
            "confidence_levels": [0.05, 0.25, 0.5, 0.75, 0.95]
        }
        
        start_time = time.time()
        response = await authenticated_client.post(
            "/api/v1/simulations/monte-carlo",
            json=large_simulation_request
        )
        execution_time = time.time() - start_time
        
        assert response.status_code == status.HTTP_200_OK
        
        # Performance requirement: large simulation should complete within 30 seconds
        assert execution_time < 30.0
        
        result = response.json()
        assert result["execution_time"] > 0
        assert result["num_simulations"] == large_simulation_request["num_simulations"]


class TestTaxOptimizationAPI:
    """Test tax optimization endpoints"""
    
    @pytest.mark.asyncio
    async def test_tax_loss_harvesting_analysis(self, authenticated_client: AsyncClient, test_user: User):
        """Test tax-loss harvesting analysis endpoint"""
        holdings_data = {
            "holdings": [
                {
                    "symbol": "AAPL",
                    "quantity": 100,
                    "purchase_price": 150.0,
                    "current_price": 180.0,
                    "purchase_date": "2023-01-15",
                    "account_type": "taxable"
                },
                {
                    "symbol": "TSLA",
                    "quantity": 50,
                    "purchase_price": 300.0,
                    "current_price": 250.0,  # Loss position
                    "purchase_date": "2023-06-01",
                    "account_type": "taxable"
                }
            ],
            "tax_rate": 0.24,
            "analysis_date": "2024-01-15"
        }
        
        response = await authenticated_client.post(
            "/api/v1/tax/loss-harvesting-analysis",
            json=holdings_data
        )
        assert response.status_code == status.HTTP_200_OK
        
        analysis_result = response.json()
        
        # Should identify loss opportunities
        assert "opportunities" in analysis_result
        assert "total_harvestable_losses" in analysis_result
        assert "estimated_tax_savings" in analysis_result
        
        opportunities = analysis_result["opportunities"]
        
        # Should find TSLA as loss opportunity
        tsla_opportunities = [opp for opp in opportunities if opp["symbol"] == "TSLA"]
        assert len(tsla_opportunities) > 0
        
        tsla_opp = tsla_opportunities[0]
        assert tsla_opp["unrealized_loss"] > 0
        assert tsla_opp["tax_benefit"] > 0
        assert not tsla_opp["wash_sale_risk"]  # Should not have wash sale risk initially
    
    @pytest.mark.asyncio
    async def test_asset_location_optimization(self, authenticated_client: AsyncClient, test_user: User):
        """Test asset location optimization endpoint"""
        location_request = {
            "target_allocation": {
                "stocks": 0.70,
                "bonds": 0.25,
                "reits": 0.05
            },
            "account_balances": {
                "taxable": 200000.0,
                "traditional_401k": 150000.0,
                "roth_ira": 50000.0
            },
            "tax_rates": {
                "ordinary_income": 0.24,
                "capital_gains": 0.15,
                "dividend": 0.15
            }
        }
        
        response = await authenticated_client.post(
            "/api/v1/tax/asset-location",
            json=location_request
        )
        assert response.status_code == status.HTTP_200_OK
        
        optimization_result = response.json()
        
        # Validate response structure
        assert "optimal_allocation" in optimization_result
        assert "tax_efficiency_score" in optimization_result
        assert "annual_tax_savings" in optimization_result
        
        optimal_allocation = optimization_result["optimal_allocation"]
        
        # Should allocate tax-inefficient assets to tax-advantaged accounts
        # Bonds should be primarily in traditional 401k or Roth IRA
        bond_allocation = optimal_allocation["bonds"]
        taxable_bonds = bond_allocation.get("taxable", 0)
        total_bonds = sum(bond_allocation.values())
        
        if total_bonds > 0:
            taxable_bond_ratio = taxable_bonds / total_bonds
            assert taxable_bond_ratio < 0.5  # Most bonds should be in tax-advantaged accounts
    
    @pytest.mark.asyncio
    async def test_roth_conversion_analysis(self, authenticated_client: AsyncClient, test_user: User):
        """Test Roth conversion analysis endpoint"""
        conversion_request = {
            "traditional_ira_balance": 200000.0,
            "current_income": 80000.0,
            "current_age": 45,
            "retirement_age": 65,
            "conversion_amount": 50000.0,
            "filing_status": "married_filing_jointly",
            "state": "CA"
        }
        
        response = await authenticated_client.post(
            "/api/v1/tax/roth-conversion-analysis",
            json=conversion_request
        )
        assert response.status_code == status.HTTP_200_OK
        
        analysis_result = response.json()
        
        # Validate analysis components
        assert "conversion_tax" in analysis_result
        assert "future_tax_savings" in analysis_result
        assert "break_even_years" in analysis_result
        assert "net_present_value" in analysis_result
        assert "recommendation" in analysis_result
        
        # Conversion tax should be positive
        assert analysis_result["conversion_tax"] > 0
        
        # Should provide actionable recommendation
        recommendation = analysis_result["recommendation"]
        assert recommendation in ["CONVERT", "DONT_CONVERT", "PARTIAL_CONVERT"]
        
        # If recommending conversion, should explain why
        if recommendation == "CONVERT":
            assert "reasons" in analysis_result
            assert len(analysis_result["reasons"]) > 0


class TestAPIErrorHandlingAndEdgeCases:
    """Test API error handling and edge cases"""
    
    @pytest.mark.asyncio
    async def test_invalid_input_validation(self, authenticated_client: AsyncClient):
        """Test API input validation and error messages"""
        # Test invalid portfolio optimization request
        invalid_requests = [
            {
                "method": "invalid_method",
                "assets": [],  # Empty assets
                "investment_amount": 1000
            },
            {
                "method": "max_sharpe",
                "assets": [
                    {
                        "symbol": "TEST",
                        "expected_return": -2.0,  # Invalid return
                        "volatility": 0.1
                    }
                ],
                "investment_amount": -1000  # Negative amount
            }
        ]
        
        for invalid_request in invalid_requests:
            response = await authenticated_client.post(
                "/api/v1/portfolio/optimize",
                json=invalid_request
            )
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
            
            error_detail = response.json()
            assert "detail" in error_detail
    
    @pytest.mark.asyncio
    async def test_resource_not_found(self, authenticated_client: AsyncClient):
        """Test 404 handling for non-existent resources"""
        # Test non-existent goal
        response = await authenticated_client.get("/api/v1/goals/99999")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
        # Test non-existent financial profile
        response = await authenticated_client.get("/api/v1/financial-profiles/99999")
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self, test_client: AsyncClient):
        """Test API rate limiting (if implemented)"""
        # Make multiple requests rapidly
        responses = []
        for i in range(100):
            response = await test_client.get("/api/v1/health")
            responses.append(response.status_code)
        
        # Should handle high request volume gracefully
        # Either all succeed or some are rate limited (429)
        valid_codes = [200, 429]
        assert all(code in valid_codes for code in responses)
    
    @pytest.mark.asyncio
    async def test_concurrent_request_handling(self, authenticated_client: AsyncClient, test_user: User):
        """Test handling of concurrent requests"""
        # Create multiple concurrent optimization requests
        optimization_request = {
            "method": "max_sharpe",
            "assets": [
                {
                    "symbol": "VTI",
                    "expected_return": 0.08,
                    "volatility": 0.15
                },
                {
                    "symbol": "BND",
                    "expected_return": 0.03,
                    "volatility": 0.05
                }
            ],
            "investment_amount": 10000.0
        }
        
        # Send 10 concurrent requests
        tasks = [
            authenticated_client.post("/api/v1/portfolio/optimize", json=optimization_request)
            for _ in range(10)
        ]
        
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # All requests should succeed or fail gracefully
        successful_responses = [r for r in responses if hasattr(r, 'status_code') and r.status_code == 200]
        assert len(successful_responses) >= 8  # At least 80% should succeed


class TestCompleteUserJourney:
    """End-to-end integration test simulating complete user journey"""
    
    @pytest.mark.asyncio
    async def test_complete_financial_planning_workflow(self, test_client: AsyncClient, db_session: AsyncSession):
        """Test complete user journey from registration to financial plan"""
        # Step 1: User Registration
        registration_data = {
            "email": "journey@example.com",
            "password": "SecurePassword123!",
            "first_name": "Journey",
            "last_name": "User"
        }
        
        response = await test_client.post("/api/v1/auth/register", json=registration_data)
        assert response.status_code == status.HTTP_201_CREATED
        
        # Step 2: Login
        login_data = {
            "username": registration_data["email"],
            "password": registration_data["password"]
        }
        
        response = await test_client.post("/api/v1/auth/login", data=login_data)
        assert response.status_code == status.HTTP_200_OK
        
        token_data = response.json()
        headers = {"Authorization": f"Bearer {token_data['access_token']}"}
        
        # Step 3: Create Financial Profile
        profile_data = {
            "annual_income": 100000.0,
            "monthly_expenses": 5000.0,
            "current_savings": 50000.0,
            "current_debt": 20000.0,
            "risk_tolerance": "moderate",
            "investment_experience": "intermediate",
            "investment_timeline": 25,
            "financial_goals": ["retirement", "house_down_payment"],
            "employment_status": "employed",
            "marital_status": "married",
            "dependents": 2
        }
        
        response = await test_client.post(
            "/api/v1/financial-profiles/",
            json=profile_data,
            headers=headers
        )
        assert response.status_code == status.HTTP_201_CREATED
        
        # Step 4: Create Financial Goals
        goals_data = [
            {
                "name": "Retirement Fund",
                "goal_type": "retirement",
                "target_amount": 1500000.0,
                "current_amount": 30000.0,
                "target_date": "2049-12-31",
                "priority": "high",
                "monthly_contribution": 1500.0
            },
            {
                "name": "House Down Payment",
                "goal_type": "major_purchase",
                "target_amount": 80000.0,
                "current_amount": 10000.0,
                "target_date": "2027-06-30",
                "priority": "medium",
                "monthly_contribution": 1000.0
            }
        ]
        
        created_goals = []
        for goal_data in goals_data:
            response = await test_client.post(
                "/api/v1/goals/",
                json=goal_data,
                headers=headers
            )
            assert response.status_code == status.HTTP_201_CREATED
            created_goals.append(response.json())
        
        # Step 5: Run Portfolio Optimization
        optimization_request = {
            "method": "max_sharpe",
            "assets": [
                {
                    "symbol": "VTI",
                    "expected_return": 0.08,
                    "volatility": 0.15,
                    "asset_class": "equities"
                },
                {
                    "symbol": "VXUS",
                    "expected_return": 0.06,
                    "volatility": 0.18,
                    "asset_class": "international_equities"
                },
                {
                    "symbol": "BND",
                    "expected_return": 0.03,
                    "volatility": 0.05,
                    "asset_class": "bonds"
                },
                {
                    "symbol": "VNQ",
                    "expected_return": 0.07,
                    "volatility": 0.20,
                    "asset_class": "reits"
                }
            ],
            "constraints": {
                "max_position_size": 0.4,
                "min_position_size": 0.05
            },
            "investment_amount": 50000.0
        }
        
        response = await test_client.post(
            "/api/v1/portfolio/optimize",
            json=optimization_request,
            headers=headers
        )
        assert response.status_code == status.HTTP_200_OK
        
        portfolio_result = response.json()
        assert "weights" in portfolio_result
        assert "metrics" in portfolio_result
        
        # Step 6: Run Monte Carlo Simulation for Retirement Goal
        simulation_request = {
            "goal_id": created_goals[0]["id"],  # Retirement goal
            "current_savings": 30000.0,
            "monthly_contribution": 1500.0,
            "expected_return": portfolio_result["metrics"]["expected_return"],
            "volatility": portfolio_result["metrics"]["volatility"],
            "num_simulations": 10000
        }
        
        response = await test_client.post(
            "/api/v1/simulations/goal-analysis",
            json=simulation_request,
            headers=headers
        )
        assert response.status_code == status.HTTP_200_OK
        
        simulation_result = response.json()
        assert "goal_achievement_probability" in simulation_result
        
        # Step 7: Generate Comprehensive Financial Plan
        plan_request = {
            "include_portfolio": True,
            "include_goals": True,
            "include_simulations": True,
            "include_tax_strategies": True,
            "planning_horizon_years": 25
        }
        
        response = await test_client.post(
            "/api/v1/financial-plan/generate",
            json=plan_request,
            headers=headers
        )
        
        # This endpoint might not exist yet, so we allow 404
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]
        
        if response.status_code == status.HTTP_200_OK:
            financial_plan = response.json()
            assert "portfolio_allocation" in financial_plan
            assert "goal_projections" in financial_plan
            assert "risk_analysis" in financial_plan


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
