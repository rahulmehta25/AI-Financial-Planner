"""
Complete User Journey Integration Tests

This module contains comprehensive end-to-end tests that simulate complete user journeys
through the financial planning system, from onboarding to receiving results.

Test Coverage:
- Full onboarding flow (registration → profile setup → goal creation)
- Financial planning process (data input → analysis → recommendations)
- Results generation and delivery (simulation → PDF → notifications)
- Multi-session user interactions
- Mobile app synchronization scenarios
"""
import asyncio
import json
import time
from typing import Dict, List, Any
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from tests.integration.base import UserJourneyTest, integration_test_context
from tests.factories import UserFactory, create_complete_user_scenario
from app.models.user import User
from app.models.financial_profile import FinancialProfile
from app.models.goal import Goal
from app.models.simulation_result import SimulationResult


class TestCompleteUserOnboarding(UserJourneyTest):
    """Test complete user onboarding flow from registration to first plan."""
    
    async def test_full_onboarding_flow(self):
        """Test complete onboarding: registration → verification → profile → goals → first simulation."""
        async with integration_test_context(self) as config:
            
            # Step 1: User Registration
            await self.measure_operation(
                self._test_user_registration,
                "user_registration"
            )
            
            # Step 2: Email Verification (simulated)
            await self.measure_operation(
                self._test_email_verification,
                "email_verification"
            )
            
            # Step 3: Profile Creation
            await self.measure_operation(
                self._test_profile_creation,
                "profile_creation"
            )
            
            # Step 4: Goal Setting
            await self.measure_operation(
                self._test_goal_creation,
                "goal_creation"
            )
            
            # Step 5: Banking Connection (optional)
            await self.measure_operation(
                self._test_banking_connection,
                "banking_connection"
            )
            
            # Step 6: First Financial Plan Generation
            await self.measure_operation(
                self._test_first_plan_generation,
                "first_plan_generation"
            )
            
            # Step 7: Results Review
            await self.measure_operation(
                self._test_results_review,
                "results_review"
            )
            
            # Verify complete user journey
            await self._verify_complete_onboarding()
    
    async def _test_user_registration(self):
        """Test user registration step."""
        user_data = {
            "email": "newuser@example.com",
            "password": "SecurePassword123!",
            "first_name": "John",
            "last_name": "Doe",
            "phone_number": "+1-555-123-4567",
            "date_of_birth": "1985-06-15"
        }
        
        response = await self.client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 201
        
        result = response.json()
        assert result["email"] == user_data["email"]
        assert "id" in result
        
        self.test_user = result
        self.record_journey_step("registration", {"user_id": result["id"]})
        
        return result
    
    async def _test_email_verification(self):
        """Test email verification step."""
        # In real implementation, this would involve email verification
        # For testing, we'll simulate the verification process
        
        verification_data = {
            "email": self.test_user["email"],
            "verification_code": "123456"  # Mock verification code
        }
        
        response = await self.client.post("/api/v1/auth/verify-email", json=verification_data)
        assert response.status_code == 200
        
        self.record_journey_step("email_verification", {"verified": True})
        
        # Now authenticate the user
        login_data = {
            "username": self.test_user["email"],
            "password": "SecurePassword123!"
        }
        
        response = await self.client.post("/api/v1/auth/login", data=login_data)
        assert response.status_code == 200
        
        token_data = response.json()
        self.auth_token = token_data["access_token"]
        
        return {"verified": True, "token": self.auth_token}
    
    async def _test_profile_creation(self):
        """Test financial profile creation."""
        profile_data = {
            "annual_income": 75000.0,
            "monthly_expenses": 4500.0,
            "current_savings": 25000.0,
            "current_debt": 15000.0,
            "investment_experience": "intermediate",
            "risk_tolerance": "moderate",
            "investment_timeline": 25,
            "employment_status": "employed",
            "marital_status": "single",
            "dependents": 0,
            "financial_goals": ["retirement", "house_down_payment", "emergency_fund"]
        }
        
        response = await self.client.post(
            "/api/v1/financial-profiles/",
            json=profile_data,
            headers=self.auth_headers
        )
        assert response.status_code == 201
        
        profile = response.json()
        assert profile["annual_income"] == profile_data["annual_income"]
        assert profile["risk_tolerance"] == profile_data["risk_tolerance"]
        
        self.record_journey_step("profile_creation", {"profile_id": profile["id"]})
        
        return profile
    
    async def _test_goal_creation(self):
        """Test financial goal creation."""
        goals_data = [
            {
                "name": "Retirement Fund",
                "description": "Save for comfortable retirement",
                "goal_type": "retirement",
                "target_amount": 1000000.0,
                "target_date": "2050-01-01",
                "priority": "high",
                "monthly_contribution": 1000.0
            },
            {
                "name": "House Down Payment",
                "description": "Save for house down payment",
                "goal_type": "major_purchase",
                "target_amount": 100000.0,
                "target_date": "2030-01-01",
                "priority": "medium",
                "monthly_contribution": 500.0
            },
            {
                "name": "Emergency Fund",
                "description": "6 months of expenses",
                "goal_type": "emergency",
                "target_amount": 27000.0,
                "target_date": "2026-01-01",
                "priority": "high",
                "monthly_contribution": 300.0
            }
        ]
        
        created_goals = []
        for goal_data in goals_data:
            response = await self.client.post(
                "/api/v1/goals/",
                json=goal_data,
                headers=self.auth_headers
            )
            assert response.status_code == 201
            
            goal = response.json()
            created_goals.append(goal)
        
        self.record_journey_step("goal_creation", {"goals_count": len(created_goals)})
        
        return created_goals
    
    async def _test_banking_connection(self):
        """Test optional banking connection."""
        # Simulate Plaid connection
        banking_data = {
            "institution_id": "ins_109508",
            "public_token": "public-development-token",
            "account_ids": ["account_1", "account_2"]
        }
        
        response = await self.client.post(
            "/api/v1/banking/connect",
            json=banking_data,
            headers=self.auth_headers
        )
        
        # Banking connection might be optional and could fail
        if response.status_code == 201:
            connection = response.json()
            self.record_journey_step("banking_connection", {"connected": True, "accounts": len(connection.get("accounts", []))})
            return connection
        else:
            self.record_journey_step("banking_connection", {"connected": False, "reason": "optional_skip"})
            return {"connected": False}
    
    async def _test_first_plan_generation(self):
        """Test first financial plan generation."""
        simulation_data = {
            "simulation_type": "comprehensive_planning",
            "time_horizon": 25,
            "monte_carlo_runs": 1000,
            "include_goals": True,
            "include_tax_optimization": True,
            "scenario_analysis": True
        }
        
        response = await self.client.post(
            "/api/v1/simulations/run",
            json=simulation_data,
            headers=self.auth_headers
        )
        assert response.status_code == 202  # Async simulation started
        
        simulation_id = response.json()["simulation_id"]
        
        # Poll for completion
        simulation_result = await self._wait_for_simulation_completion(simulation_id)
        
        self.record_journey_step("first_plan_generation", {
            "simulation_id": simulation_id,
            "success_probability": simulation_result.get("success_probability", 0)
        })
        
        return simulation_result
    
    async def _test_results_review(self):
        """Test results review and interaction."""
        # Get user's simulations
        response = await self.client.get(
            "/api/v1/simulations/",
            headers=self.auth_headers
        )
        assert response.status_code == 200
        
        simulations = response.json()
        assert len(simulations) > 0
        
        latest_simulation = simulations[0]
        simulation_id = latest_simulation["id"]
        
        # Get detailed results
        response = await self.client.get(
            f"/api/v1/simulations/{simulation_id}",
            headers=self.auth_headers
        )
        assert response.status_code == 200
        
        detailed_results = response.json()
        
        # Test PDF generation
        response = await self.client.post(
            f"/api/v1/simulations/{simulation_id}/pdf",
            headers=self.auth_headers
        )
        assert response.status_code == 200
        
        self.record_journey_step("results_review", {
            "simulation_id": simulation_id,
            "pdf_generated": True
        })
        
        return detailed_results
    
    async def _wait_for_simulation_completion(self, simulation_id: str, timeout: int = 120) -> Dict[str, Any]:
        """Wait for simulation to complete."""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            response = await self.client.get(
                f"/api/v1/simulations/{simulation_id}",
                headers=self.auth_headers
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("status") == "completed":
                    return result
                elif result.get("status") == "failed":
                    raise Exception(f"Simulation failed: {result.get('error_message')}")
            
            await asyncio.sleep(2)
        
        raise TimeoutError(f"Simulation {simulation_id} did not complete within {timeout} seconds")
    
    async def _verify_complete_onboarding(self):
        """Verify that the complete onboarding process was successful."""
        # Verify journey steps were recorded
        expected_steps = [
            "registration", "email_verification", "profile_creation", 
            "goal_creation", "banking_connection", "first_plan_generation", 
            "results_review"
        ]
        
        recorded_steps = [step["step_name"] for step in self.journey_steps]
        
        for expected_step in expected_steps:
            assert expected_step in recorded_steps, f"Missing journey step: {expected_step}"
        
        # Verify user has complete profile
        response = await self.client.get(
            "/api/v1/financial-profiles/me",
            headers=self.auth_headers
        )
        assert response.status_code == 200
        
        profile = response.json()
        assert profile["annual_income"] > 0
        assert profile["risk_tolerance"] is not None
        
        # Verify user has goals
        response = await self.client.get(
            "/api/v1/goals/",
            headers=self.auth_headers
        )
        assert response.status_code == 200
        
        goals = response.json()
        assert len(goals) >= 3  # Should have at least 3 goals
        
        # Verify user has simulation results
        response = await self.client.get(
            "/api/v1/simulations/",
            headers=self.auth_headers
        )
        assert response.status_code == 200
        
        simulations = response.json()
        assert len(simulations) >= 1  # Should have at least one simulation


class TestReturnUserJourney(UserJourneyTest):
    """Test returning user journeys with existing data."""
    
    async def test_returning_user_plan_update(self):
        """Test returning user updating their financial plan."""
        async with integration_test_context(self) as config:
            
            # Create existing user with complete profile
            await self._create_existing_user()
            
            # Step 1: Login
            await self.measure_operation(
                self._test_user_login,
                "returning_user_login"
            )
            
            # Step 2: Profile Update
            await self.measure_operation(
                self._test_profile_update,
                "profile_update"
            )
            
            # Step 3: Goal Modification
            await self.measure_operation(
                self._test_goal_modification,
                "goal_modification"
            )
            
            # Step 4: New Simulation
            await self.measure_operation(
                self._test_updated_simulation,
                "updated_simulation"
            )
            
            # Step 5: Compare Results
            await self.measure_operation(
                self._test_results_comparison,
                "results_comparison"
            )
    
    async def _create_existing_user(self):
        """Create an existing user with historical data."""
        # Create user with existing profile and goals
        user_data = await self.create_test_user()
        
        # Create historical simulation
        simulation_data = {
            "simulation_type": "retirement_planning",
            "time_horizon": 30,
            "monte_carlo_runs": 500
        }
        
        response = await self.client.post(
            "/api/v1/simulations/run",
            json=simulation_data,
            headers=self.auth_headers
        )
        assert response.status_code == 202
        
        return user_data
    
    async def _test_user_login(self):
        """Test existing user login."""
        # Already handled in create_existing_user
        self.record_journey_step("returning_login", {"existing_user": True})
        return True
    
    async def _test_profile_update(self):
        """Test updating financial profile."""
        update_data = {
            "annual_income": 85000.0,  # Increased income
            "monthly_expenses": 5000.0,  # Increased expenses
            "current_savings": 35000.0,  # Increased savings
            "risk_tolerance": "aggressive"  # Changed risk tolerance
        }
        
        response = await self.client.patch(
            "/api/v1/financial-profiles/me",
            json=update_data,
            headers=self.auth_headers
        )
        assert response.status_code == 200
        
        updated_profile = response.json()
        assert updated_profile["annual_income"] == update_data["annual_income"]
        assert updated_profile["risk_tolerance"] == update_data["risk_tolerance"]
        
        self.record_journey_step("profile_update", {"changes": list(update_data.keys())})
        
        return updated_profile
    
    async def _test_goal_modification(self):
        """Test modifying existing goals."""
        # Get existing goals
        response = await self.client.get(
            "/api/v1/goals/",
            headers=self.auth_headers
        )
        assert response.status_code == 200
        
        goals = response.json()
        if goals:
            # Update first goal
            goal_id = goals[0]["id"]
            update_data = {
                "target_amount": 1200000.0,  # Increased target
                "monthly_contribution": 1200.0  # Increased contribution
            }
            
            response = await self.client.patch(
                f"/api/v1/goals/{goal_id}",
                json=update_data,
                headers=self.auth_headers
            )
            assert response.status_code == 200
        
        # Add new goal
        new_goal_data = {
            "name": "Vacation Fund",
            "description": "Annual vacation savings",
            "goal_type": "other",
            "target_amount": 10000.0,
            "target_date": "2026-12-31",
            "priority": "low",
            "monthly_contribution": 200.0
        }
        
        response = await self.client.post(
            "/api/v1/goals/",
            json=new_goal_data,
            headers=self.auth_headers
        )
        assert response.status_code == 201
        
        self.record_journey_step("goal_modification", {"updated_goals": 1, "new_goals": 1})
        
        return True
    
    async def _test_updated_simulation(self):
        """Test running new simulation with updated data."""
        simulation_data = {
            "simulation_type": "comprehensive_planning",
            "time_horizon": 25,
            "monte_carlo_runs": 1000,
            "include_goals": True,
            "compare_to_previous": True
        }
        
        response = await self.client.post(
            "/api/v1/simulations/run",
            json=simulation_data,
            headers=self.auth_headers
        )
        assert response.status_code == 202
        
        simulation_id = response.json()["simulation_id"]
        simulation_result = await self._wait_for_simulation_completion(simulation_id)
        
        self.record_journey_step("updated_simulation", {
            "simulation_id": simulation_id,
            "comparison_enabled": True
        })
        
        return simulation_result
    
    async def _test_results_comparison(self):
        """Test comparing new results with previous simulation."""
        response = await self.client.get(
            "/api/v1/simulations/",
            headers=self.auth_headers
        )
        assert response.status_code == 200
        
        simulations = response.json()
        assert len(simulations) >= 2  # Should have multiple simulations
        
        # Get comparison data
        latest_simulation_id = simulations[0]["id"]
        previous_simulation_id = simulations[1]["id"]
        
        response = await self.client.get(
            f"/api/v1/simulations/{latest_simulation_id}/compare/{previous_simulation_id}",
            headers=self.auth_headers
        )
        assert response.status_code == 200
        
        comparison = response.json()
        assert "improvement" in comparison
        assert "key_changes" in comparison
        
        self.record_journey_step("results_comparison", {
            "comparison_available": True,
            "improvement_detected": comparison.get("improvement", False)
        })
        
        return comparison


class TestMultiSessionUserJourney(UserJourneyTest):
    """Test user journeys across multiple sessions and devices."""
    
    async def test_cross_device_session_continuity(self):
        """Test user experience across multiple devices/sessions."""
        async with integration_test_context(self) as config:
            
            # Session 1: Desktop - Initial setup
            await self._test_desktop_session()
            
            # Session 2: Mobile - Review and adjust
            await self._test_mobile_session()
            
            # Session 3: Desktop - Final review
            await self._test_return_desktop_session()
            
            # Verify data consistency across sessions
            await self._verify_cross_session_consistency()
    
    async def _test_desktop_session(self):
        """Test desktop session for initial setup."""
        # Create user and initial profile
        await self.create_test_user()
        
        # Simulate desktop-specific features
        await self._test_detailed_profile_creation()
        await self._test_comprehensive_goal_setting()
        
        self.record_journey_step("desktop_session", {"device_type": "desktop"})
    
    async def _test_mobile_session(self):
        """Test mobile session for quick updates."""
        # Simulate mobile login (would typically involve different session handling)
        
        # Mobile-optimized profile updates
        mobile_update = {
            "monthly_expenses": 4800.0,  # Quick expense update
            "current_savings": 28000.0   # Quick savings update
        }
        
        response = await self.client.patch(
            "/api/v1/financial-profiles/me",
            json=mobile_update,
            headers=self.auth_headers
        )
        assert response.status_code == 200
        
        # Quick goal check
        response = await self.client.get(
            "/api/v1/goals/summary",
            headers=self.auth_headers
        )
        assert response.status_code == 200
        
        self.record_journey_step("mobile_session", {"device_type": "mobile"})
    
    async def _test_return_desktop_session(self):
        """Test returning to desktop for detailed review."""
        # Run new simulation with updated data
        simulation_data = {
            "simulation_type": "goal_tracking",
            "monte_carlo_runs": 1000
        }
        
        response = await self.client.post(
            "/api/v1/simulations/run",
            json=simulation_data,
            headers=self.auth_headers
        )
        assert response.status_code == 202
        
        self.record_journey_step("return_desktop_session", {"device_type": "desktop"})
    
    async def _test_detailed_profile_creation(self):
        """Create detailed profile typical of desktop usage."""
        profile_data = {
            "annual_income": 80000.0,
            "monthly_expenses": 4500.0,
            "current_savings": 30000.0,
            "current_debt": 20000.0,
            "investment_experience": "intermediate",
            "risk_tolerance": "moderate",
            "investment_timeline": 30,
            "employment_status": "employed",
            "marital_status": "married",
            "dependents": 2,
            "financial_goals": ["retirement", "education", "house_down_payment"],
            "tax_filing_status": "married_filing_jointly",
            "employer_401k_match": 0.06,
            "current_401k_contribution": 0.10
        }
        
        response = await self.client.post(
            "/api/v1/financial-profiles/",
            json=profile_data,
            headers=self.auth_headers
        )
        assert response.status_code == 201
    
    async def _test_comprehensive_goal_setting(self):
        """Create comprehensive goals typical of desktop usage."""
        goals = [
            {
                "name": "Retirement (401k + IRA)",
                "description": "Combined retirement savings strategy",
                "goal_type": "retirement",
                "target_amount": 1500000.0,
                "target_date": "2055-01-01",
                "priority": "high",
                "monthly_contribution": 1500.0
            },
            {
                "name": "Children's Education Fund",
                "description": "College savings for 2 children",
                "goal_type": "education",
                "target_amount": 400000.0,
                "target_date": "2040-01-01",
                "priority": "high",
                "monthly_contribution": 800.0
            }
        ]
        
        for goal_data in goals:
            response = await self.client.post(
                "/api/v1/goals/",
                json=goal_data,
                headers=self.auth_headers
            )
            assert response.status_code == 201
    
    async def _verify_cross_session_consistency(self):
        """Verify data consistency across different sessions."""
        # Verify profile was updated correctly across sessions
        response = await self.client.get(
            "/api/v1/financial-profiles/me",
            headers=self.auth_headers
        )
        assert response.status_code == 200
        
        profile = response.json()
        
        # Should have mobile updates
        assert profile["monthly_expenses"] == 4800.0
        assert profile["current_savings"] == 28000.0
        
        # Should retain desktop data
        assert profile["dependents"] == 2
        assert profile["marital_status"] == "married"
        
        self.record_journey_step("cross_session_verification", {
            "data_consistent": True,
            "sessions_tested": ["desktop", "mobile", "desktop"]
        })


@pytest.mark.asyncio
@pytest.mark.integration
class TestUserJourneyPerformance:
    """Test performance of complete user journeys."""
    
    async def test_onboarding_performance(self):
        """Test that complete onboarding meets performance requirements."""
        test = TestCompleteUserOnboarding()
        
        async with integration_test_context(test) as config:
            start_time = time.time()
            
            await test.test_full_onboarding_flow()
            
            end_time = time.time()
            total_duration = end_time - start_time
            
            # Assert onboarding completes within reasonable time
            assert total_duration < 300, f"Onboarding took {total_duration:.2f}s, expected < 300s"
            
            # Check individual step performance
            step_durations = {metric.end_time - metric.start_time for metric in test.metrics}
            max_step_duration = max(step_durations) if step_durations else 0
            
            assert max_step_duration < 60, f"Longest step took {max_step_duration:.2f}s, expected < 60s"
    
    async def test_concurrent_user_onboarding(self):
        """Test system performance with multiple concurrent onboarding users."""
        num_concurrent_users = 5
        
        async def single_user_onboarding():
            test = TestCompleteUserOnboarding()
            async with integration_test_context(test) as config:
                await test.test_full_onboarding_flow()
                return test.metrics
        
        # Run concurrent onboarding
        tasks = [single_user_onboarding() for _ in range(num_concurrent_users)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Verify all succeeded
        successful_results = [r for r in results if not isinstance(r, Exception)]
        assert len(successful_results) == num_concurrent_users, "Some concurrent onboarding failed"
        
        # Check performance degradation
        all_metrics = []
        for result in successful_results:
            all_metrics.extend(result)
        
        avg_duration = sum(m.duration for m in all_metrics) / len(all_metrics)
        assert avg_duration < 30, f"Average operation duration {avg_duration:.2f}s too high under load"