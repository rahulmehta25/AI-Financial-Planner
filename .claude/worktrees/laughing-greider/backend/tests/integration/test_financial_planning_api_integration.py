"""
Comprehensive integration tests for financial planning API endpoints.

Tests cover:
- Complete user journey from registration to financial planning
- Market data integration and real-time updates
- Portfolio optimization workflows
- Tax optimization strategies
- Retirement planning calculations
- Risk management and compliance
- Performance and scalability
"""

import pytest
import asyncio
from httpx import AsyncClient
from decimal import Decimal
from datetime import datetime, date, timedelta
from typing import Dict, List

from app.main import app
from tests.conftest import test_client, authenticated_client, test_user
from tests.factories import (
    UserFactory, FinancialProfileFactory, GoalFactory, 
    create_complete_user_scenario
)


@pytest.mark.integration
class TestUserOnboardingFlow:
    """Test complete user onboarding and profile creation flow."""
    
    async def test_user_registration_and_profile_setup(self, test_client: AsyncClient):
        """Test complete user registration and profile setup flow."""
        
        # 1. User Registration
        registration_data = {
            "email": "newuser@example.com",
            "password": "SecurePassword123!",
            "first_name": "John",
            "last_name": "Doe",
            "phone_number": "+1-555-123-4567",
            "date_of_birth": "1985-05-15"
        }
        
        response = await test_client.post("/auth/register", json=registration_data)
        assert response.status_code == 201
        user_data = response.json()
        assert user_data["email"] == registration_data["email"]
        user_id = user_data["id"]
        
        # 2. Email Verification (mocked)
        verification_response = await test_client.post(
            f"/auth/verify-email",
            json={"user_id": user_id, "verification_code": "123456"}
        )
        assert verification_response.status_code == 200
        
        # 3. Login
        login_response = await test_client.post(
            "/auth/login",
            json={
                "email": registration_data["email"],
                "password": registration_data["password"]
            }
        )
        assert login_response.status_code == 200
        login_data = login_response.json()
        access_token = login_data["access_token"]
        
        headers = {"Authorization": f"Bearer {access_token}"}
        
        # 4. Create Financial Profile
        profile_data = {
            "annual_income": 85000.0,
            "monthly_expenses": 5500.0,
            "current_savings": 45000.0,
            "current_debt": 25000.0,
            "investment_experience": "intermediate",
            "risk_tolerance": "moderate",
            "investment_timeline": 25,
            "employment_status": "employed",
            "marital_status": "single",
            "dependents": 0
        }
        
        profile_response = await test_client.post(
            "/financial-profiles/",
            json=profile_data,
            headers=headers
        )
        assert profile_response.status_code == 201
        profile = profile_response.json()
        assert profile["annual_income"] == profile_data["annual_income"]
        
        # 5. Set Financial Goals
        goals_data = [
            {
                "name": "Retirement Fund",
                "goal_type": "retirement",
                "target_amount": 1000000.0,
                "target_date": "2049-05-15",
                "priority": "high",
                "monthly_contribution": 800.0
            },
            {
                "name": "Emergency Fund",
                "goal_type": "emergency",
                "target_amount": 30000.0,
                "target_date": "2026-05-15",
                "priority": "high",
                "monthly_contribution": 500.0
            }
        ]
        
        created_goals = []
        for goal_data in goals_data:
            goal_response = await test_client.post(
                "/goals/",
                json=goal_data,
                headers=headers
            )
            assert goal_response.status_code == 201
            created_goals.append(goal_response.json())
        
        assert len(created_goals) == 2
        
        # 6. Get Personalized Recommendations
        recommendations_response = await test_client.get(
            "/recommendations/",
            headers=headers
        )
        assert recommendations_response.status_code == 200
        recommendations = recommendations_response.json()
        
        assert "portfolio_recommendations" in recommendations
        assert "contribution_strategy" in recommendations
        assert "tax_optimization" in recommendations
    
    async def test_risk_assessment_workflow(self, authenticated_client: AsyncClient):
        """Test risk assessment and profile adjustment workflow."""
        
        # 1. Take Risk Assessment
        risk_assessment_data = {
            "questions": [
                {"question_id": "time_horizon", "answer": "20_plus_years"},
                {"question_id": "market_volatility", "answer": "moderate_concern"},
                {"question_id": "investment_experience", "answer": "some_experience"},
                {"question_id": "loss_tolerance", "answer": "moderate_loss_ok"},
                {"question_id": "liquidity_needs", "answer": "emergency_fund_only"}
            ]
        }
        
        assessment_response = await authenticated_client.post(
            "/risk-assessment/",
            json=risk_assessment_data
        )
        assert assessment_response.status_code == 201
        assessment_result = assessment_response.json()
        
        assert "risk_score" in assessment_result
        assert "risk_tolerance" in assessment_result
        assert "recommended_allocation" in assessment_result
        
        # 2. Update Profile Based on Assessment
        risk_tolerance = assessment_result["risk_tolerance"]
        
        profile_update = {
            "risk_tolerance": risk_tolerance,
            "investment_experience": "intermediate"
        }
        
        update_response = await authenticated_client.patch(
            "/financial-profiles/me",
            json=profile_update
        )
        assert update_response.status_code == 200
        
        # 3. Get Updated Recommendations
        updated_recommendations_response = await authenticated_client.get(
            "/recommendations/"
        )
        assert updated_recommendations_response.status_code == 200
        updated_recommendations = updated_recommendations_response.json()
        
        # Recommendations should reflect new risk tolerance
        portfolio_rec = updated_recommendations["portfolio_recommendations"]
        assert "asset_allocation" in portfolio_rec
        
        # Verify allocation matches risk tolerance
        equity_allocation = sum(
            allocation["weight"] 
            for allocation in portfolio_rec["asset_allocation"]
            if "equity" in allocation["asset_class"].lower()
        )
        
        if risk_tolerance == "conservative":
            assert equity_allocation <= 0.6
        elif risk_tolerance == "aggressive":
            assert equity_allocation >= 0.8
        else:  # moderate
            assert 0.6 <= equity_allocation <= 0.8


@pytest.mark.integration
class TestMarketDataIntegration:
    """Test market data integration and real-time functionality."""
    
    async def test_market_data_retrieval_and_caching(self, authenticated_client: AsyncClient):
        """Test market data retrieval, caching, and real-time updates."""
        
        # 1. Get Real-time Quote
        quote_response = await authenticated_client.get("/market-data/quote/AAPL")
        assert quote_response.status_code == 200
        quote_data = quote_response.json()
        
        required_fields = ["symbol", "price", "change", "change_percent", "volume", "timestamp"]
        for field in required_fields:
            assert field in quote_data
        
        assert quote_data["symbol"] == "AAPL"
        assert quote_data["price"] > 0
        
        # 2. Get Historical Data
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=30)
        
        historical_response = await authenticated_client.get(
            f"/market-data/historical/AAPL",
            params={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "interval": "1D"
            }
        )
        assert historical_response.status_code == 200
        historical_data = historical_response.json()
        
        assert "symbol" in historical_data
        assert "data_points" in historical_data
        assert len(historical_data["data_points"]) > 0
        
        # Verify data point structure
        data_point = historical_data["data_points"][0]
        required_ohlcv_fields = ["timestamp", "open_price", "high_price", "low_price", "close_price", "volume"]
        for field in required_ohlcv_fields:
            assert field in data_point
        
        # 3. Test Multiple Symbols
        symbols = ["AAPL", "GOOGL", "MSFT"]
        batch_response = await authenticated_client.post(
            "/market-data/batch-quotes",
            json={"symbols": symbols}
        )
        assert batch_response.status_code == 200
        batch_data = batch_response.json()
        
        assert "quotes" in batch_data
        assert len(batch_data["quotes"]) == len(symbols)
        
        for quote in batch_data["quotes"]:
            assert quote["symbol"] in symbols
            assert quote["price"] > 0
    
    async def test_market_data_validation_and_error_handling(self, authenticated_client: AsyncClient):
        """Test market data validation and error handling."""
        
        # 1. Invalid Symbol
        invalid_response = await authenticated_client.get("/market-data/quote/INVALID")
        assert invalid_response.status_code == 404
        
        # 2. Invalid Date Range
        future_date = (datetime.now() + timedelta(days=30)).date()
        invalid_date_response = await authenticated_client.get(
            f"/market-data/historical/AAPL",
            params={
                "start_date": future_date.isoformat(),
                "end_date": future_date.isoformat()
            }
        )
        assert invalid_date_response.status_code == 400
        
        # 3. Malformed Request
        malformed_response = await authenticated_client.post(
            "/market-data/batch-quotes",
            json={"symbols": "not_a_list"}  # Should be a list
        )
        assert malformed_response.status_code == 422


@pytest.mark.integration
class TestPortfolioOptimizationIntegration:
    """Test portfolio optimization integration workflows."""
    
    async def test_portfolio_optimization_workflow(self, authenticated_client: AsyncClient):
        """Test complete portfolio optimization workflow."""
        
        # 1. Define Investment Universe
        universe_data = {
            "assets": [
                {"symbol": "VTI", "asset_class": "US_EQUITY", "weight": 0.0},
                {"symbol": "VXUS", "asset_class": "INTERNATIONAL_EQUITY", "weight": 0.0},
                {"symbol": "BND", "asset_class": "BONDS", "weight": 0.0},
                {"symbol": "VNQ", "asset_class": "REAL_ESTATE", "weight": 0.0},
                {"symbol": "VTI", "asset_class": "COMMODITIES", "weight": 0.0}
            ]
        }
        
        # 2. Run Mean-Variance Optimization
        optimization_request = {
            "universe": universe_data["assets"],
            "objective": "maximize_sharpe",
            "constraints": {
                "max_weight": 0.6,
                "min_weight": 0.05,
                "max_sector_concentration": 0.8
            },
            "risk_tolerance": 0.15
        }
        
        optimization_response = await authenticated_client.post(
            "/portfolio/optimize",
            json=optimization_request
        )
        assert optimization_response.status_code == 200
        optimization_result = optimization_response.json()
        
        # Verify optimization results
        assert "weights" in optimization_result
        assert "expected_return" in optimization_result
        assert "expected_volatility" in optimization_result
        assert "sharpe_ratio" in optimization_result
        
        weights = optimization_result["weights"]
        total_weight = sum(weights.values())
        assert abs(total_weight - 1.0) < 1e-6
        
        # 3. Run Risk Parity Optimization
        risk_parity_response = await authenticated_client.post(
            "/portfolio/optimize-risk-parity",
            json={"universe": universe_data["assets"]}
        )
        assert risk_parity_response.status_code == 200
        risk_parity_result = risk_parity_response.json()
        
        assert "weights" in risk_parity_result
        assert "risk_contributions" in risk_parity_result
        
        # Risk contributions should be approximately equal
        risk_contributions = list(risk_parity_result["risk_contributions"].values())
        mean_contribution = sum(risk_contributions) / len(risk_contributions)
        
        for contribution in risk_contributions:
            assert abs(contribution - mean_contribution) < 0.1  # 10% tolerance
        
        # 4. Black-Litterman Optimization with Views
        views_data = {
            "universe": universe_data["assets"],
            "views": [
                {"asset": "VTI", "expected_excess_return": 0.02, "confidence": 0.8},
                {"asset": "VXUS", "expected_excess_return": 0.01, "confidence": 0.6}
            ],
            "risk_aversion": 3.0
        }
        
        bl_response = await authenticated_client.post(
            "/portfolio/optimize-black-litterman",
            json=views_data
        )
        assert bl_response.status_code == 200
        bl_result = bl_response.json()
        
        assert "weights" in bl_result
        assert "adjusted_returns" in bl_result
        assert "posterior_covariance" in bl_result
    
    async def test_factor_based_optimization(self, authenticated_client: AsyncClient):
        """Test factor-based portfolio optimization."""
        
        # 1. Factor Exposure Optimization
        factor_request = {
            "universe": [
                {"symbol": "VTI", "asset_class": "US_EQUITY"},
                {"symbol": "VTV", "asset_class": "US_VALUE"},
                {"symbol": "VUG", "asset_class": "US_GROWTH"},
                {"symbol": "VB", "asset_class": "US_SMALL_CAP"}
            ],
            "target_factors": {
                "market_beta": 1.0,
                "size_factor": 0.2,
                "value_factor": 0.1,
                "momentum_factor": 0.0
            },
            "tracking_error_limit": 0.05
        }
        
        factor_response = await authenticated_client.post(
            "/portfolio/optimize-factor-exposure",
            json=factor_request
        )
        assert factor_response.status_code == 200
        factor_result = factor_response.json()
        
        assert "weights" in factor_result
        assert "factor_exposures" in factor_result
        assert "tracking_error" in factor_result
        
        # Verify factor exposures are close to targets
        actual_factors = factor_result["factor_exposures"]
        target_factors = factor_request["target_factors"]
        
        for factor, target in target_factors.items():
            actual = actual_factors[factor]
            assert abs(actual - target) < 0.15, f"Factor {factor}: target {target}, actual {actual}"
        
        # 2. ESG Integration
        esg_request = {
            "universe": factor_request["universe"],
            "esg_criteria": {
                "min_esg_score": 7.0,
                "exclude_sectors": ["tobacco", "weapons"],
                "esg_weight": 0.3
            }
        }
        
        esg_response = await authenticated_client.post(
            "/portfolio/optimize-with-esg",
            json=esg_request
        )
        assert esg_response.status_code == 200
        esg_result = esg_response.json()
        
        assert "weights" in esg_result
        assert "esg_scores" in esg_result
        assert "esg_adjusted_returns" in esg_result
        
        # All included assets should meet ESG criteria
        esg_scores = esg_result["esg_scores"]
        for symbol, score in esg_scores.items():
            assert score >= esg_request["esg_criteria"]["min_esg_score"]


@pytest.mark.integration
class TestRetirementPlanningIntegration:
    """Test retirement planning integration workflows."""
    
    async def test_retirement_planning_analysis(self, authenticated_client: AsyncClient):
        """Test comprehensive retirement planning analysis."""
        
        # 1. Set up retirement scenario
        retirement_data = {
            "current_age": 35,
            "retirement_age": 65,
            "life_expectancy": 90,
            "current_income": 85000.0,
            "target_replacement_ratio": 0.8,
            "expected_inflation": 0.025,
            "expected_return_pre_retirement": 0.07,
            "expected_return_post_retirement": 0.05
        }
        
        # 2. Analyze retirement income needs
        income_analysis_response = await authenticated_client.post(
            "/retirement/analyze-income-needs",
            json=retirement_data
        )
        assert income_analysis_response.status_code == 200
        income_analysis = income_analysis_response.json()
        
        assert "current_income" in income_analysis
        assert "target_retirement_income" in income_analysis
        assert "inflation_adjusted_target" in income_analysis
        assert "total_retirement_need" in income_analysis
        assert "years_to_retirement" in income_analysis
        
        # 3. Account setup and contribution optimization
        accounts_data = {
            "accounts": [
                {
                    "account_type": "traditional_401k",
                    "current_balance": 75000.0,
                    "annual_contribution": 15000.0,
                    "employer_match": 5000.0
                },
                {
                    "account_type": "roth_ira",
                    "current_balance": 25000.0,
                    "annual_contribution": 6000.0
                },
                {
                    "account_type": "hsa",
                    "current_balance": 8000.0,
                    "annual_contribution": 4300.0
                }
            ]
        }
        
        contribution_optimization_response = await authenticated_client.post(
            "/retirement/optimize-contributions",
            json={**retirement_data, **accounts_data}
        )
        assert contribution_optimization_response.status_code == 200
        contribution_optimization = contribution_optimization_response.json()
        
        assert "recommended_strategy" in contribution_optimization
        assert "account_allocations" in contribution_optimization
        assert "employer_match_captured" in contribution_optimization
        assert "tax_savings" in contribution_optimization
        
        # Should capture full employer match
        assert contribution_optimization["employer_match_captured"] == 5000.0
        
        # 4. Roth conversion analysis
        conversion_data = {
            "traditional_balance": 200000.0,
            "current_tax_rate": 0.22,
            "expected_retirement_tax_rate": 0.25,
            "years_to_retirement": 30,
            "conversion_timeline": 10
        }
        
        conversion_response = await authenticated_client.post(
            "/retirement/analyze-roth-conversion",
            json=conversion_data
        )
        assert conversion_response.status_code == 200
        conversion_analysis = conversion_response.json()
        
        assert "optimal_conversion_amount" in conversion_analysis
        assert "conversion_schedule" in conversion_analysis
        assert "tax_cost" in conversion_analysis
        assert "lifetime_benefit" in conversion_analysis
        
        # 5. Monte Carlo retirement simulation
        simulation_data = {
            **retirement_data,
            **accounts_data,
            "num_simulations": 1000,
            "withdrawal_strategy": "dynamic"
        }
        
        simulation_response = await authenticated_client.post(
            "/retirement/monte-carlo-simulation",
            json=simulation_data
        )
        assert simulation_response.status_code == 200
        simulation_results = simulation_response.json()
        
        assert "success_probability" in simulation_results
        assert "percentile_outcomes" in simulation_results
        assert "recommended_adjustments" in simulation_results
        
        # Success probability should be reasonable
        success_probability = simulation_results["success_probability"]
        assert 0.0 <= success_probability <= 1.0
        
        # Should have percentile outcomes
        percentiles = simulation_results["percentile_outcomes"]
        assert "10th" in percentiles
        assert "50th" in percentiles
        assert "90th" in percentiles
    
    async def test_social_security_integration(self, authenticated_client: AsyncClient):
        """Test Social Security benefits integration."""
        
        # 1. Estimate Social Security benefits
        ss_data = {
            "birth_year": 1985,
            "estimated_annual_earnings": [
                {"year": 2020, "earnings": 75000},
                {"year": 2021, "earnings": 78000},
                {"year": 2022, "earnings": 82000},
                {"year": 2023, "earnings": 85000}
            ],
            "claiming_age": 67  # Full retirement age
        }
        
        ss_response = await authenticated_client.post(
            "/retirement/estimate-social-security",
            json=ss_data
        )
        assert ss_response.status_code == 200
        ss_estimate = ss_response.json()
        
        assert "estimated_monthly_benefit" in ss_estimate
        assert "full_retirement_age" in ss_estimate
        assert "early_claiming_reduction" in ss_estimate
        assert "delayed_retirement_credit" in ss_estimate
        
        # 2. Optimize claiming strategy
        claiming_optimization_response = await authenticated_client.post(
            "/retirement/optimize-ss-claiming",
            json={
                **ss_data,
                "life_expectancy": 85,
                "discount_rate": 0.03,
                "other_retirement_income": 50000
            }
        )
        assert claiming_optimization_response.status_code == 200
        claiming_optimization = claiming_optimization_response.json()
        
        assert "optimal_claiming_age" in claiming_optimization
        assert "lifetime_benefit_comparison" in claiming_optimization
        assert "breakeven_analysis" in claiming_optimization


@pytest.mark.integration
class TestTaxOptimizationIntegration:
    """Test tax optimization integration workflows."""
    
    async def test_comprehensive_tax_optimization(self, authenticated_client: AsyncClient):
        """Test comprehensive tax optimization workflow."""
        
        # 1. Set up taxable account with positions
        account_data = {
            "account_type": "taxable",
            "positions": [
                {
                    "symbol": "AAPL",
                    "quantity": 100,
                    "cost_basis": 150.0,
                    "current_price": 180.0,
                    "purchase_date": "2023-01-15"
                },
                {
                    "symbol": "GOOGL", 
                    "quantity": 25,
                    "cost_basis": 2800.0,
                    "current_price": 2600.0,
                    "purchase_date": "2023-06-20"
                },
                {
                    "symbol": "MSFT",
                    "quantity": 50,
                    "cost_basis": 300.0,
                    "current_price": 420.0,
                    "purchase_date": "2022-12-10"
                }
            ]
        }
        
        # 2. Identify tax-loss harvesting opportunities
        harvesting_response = await authenticated_client.post(
            "/tax-optimization/identify-harvesting-opportunities",
            json={
                **account_data,
                "min_loss_threshold": 1000.0,
                "current_date": "2024-11-15"
            }
        )
        assert harvesting_response.status_code == 200
        harvesting_opportunities = harvesting_response.json()
        
        assert "opportunities" in harvesting_opportunities
        assert "total_harvestable_losses" in harvesting_opportunities
        assert "tax_savings_estimate" in harvesting_opportunities
        
        # Should identify GOOGL as a harvesting opportunity
        opportunities = harvesting_opportunities["opportunities"]
        googl_opportunity = next(
            (opp for opp in opportunities if opp["symbol"] == "GOOGL"), None
        )
        assert googl_opportunity is not None
        assert googl_opportunity["unrealized_loss"] > 1000
        
        # 3. Asset location optimization
        asset_location_data = {
            "accounts": {
                "taxable": {"balance": 200000, "tax_rate": 0.15},
                "traditional_401k": {"balance": 300000, "tax_rate": 0.22},
                "roth_ira": {"balance": 100000, "tax_rate": 0.0}
            },
            "assets": [
                {"symbol": "VTI", "dividend_yield": 0.015, "tax_efficiency": 0.9},
                {"symbol": "BND", "dividend_yield": 0.035, "tax_efficiency": 0.3},
                {"symbol": "VNQ", "dividend_yield": 0.040, "tax_efficiency": 0.4}
            ]
        }
        
        asset_location_response = await authenticated_client.post(
            "/tax-optimization/optimize-asset-location",
            json=asset_location_data
        )
        assert asset_location_response.status_code == 200
        asset_location_result = asset_location_response.json()
        
        assert "optimized_allocation" in asset_location_result
        assert "tax_alpha" in asset_location_result
        assert "allocation_rationale" in asset_location_result
        
        # Tax-inefficient assets should go in tax-advantaged accounts
        allocation = asset_location_result["optimized_allocation"]
        traditional_401k_assets = [asset["symbol"] for asset in allocation["traditional_401k"]]
        assert "BND" in traditional_401k_assets  # Bonds should be in 401k
        
        # 4. Withdrawal sequencing optimization
        withdrawal_data = {
            "accounts": {
                "taxable": 150000,
                "traditional_ira": 250000,
                "roth_ira": 100000
            },
            "annual_need": 60000,
            "current_age": 68,
            "tax_rate": 0.18
        }
        
        withdrawal_response = await authenticated_client.post(
            "/tax-optimization/optimize-withdrawal-sequence",
            json=withdrawal_data
        )
        assert withdrawal_response.status_code == 200
        withdrawal_sequence = withdrawal_response.json()
        
        assert "withdrawal_sequence" in withdrawal_sequence
        assert "total_tax_impact" in withdrawal_sequence
        assert "effective_tax_rate" in withdrawal_sequence
        
        # Should prioritize taxable first, Roth last
        sequence = withdrawal_sequence["withdrawal_sequence"]
        assert sequence[0]["account_type"] == "taxable"
        assert sequence[-1]["account_type"] == "roth_ira"
    
    async def test_charitable_giving_optimization(self, authenticated_client: AsyncClient):
        """Test charitable giving optimization strategies."""
        
        charitable_data = {
            "donation_amount": 25000,
            "available_assets": [
                {
                    "symbol": "AAPL",
                    "quantity": 100,
                    "cost_basis": 50.0,
                    "current_price": 200.0,
                    "purchase_date": "2020-01-15",
                    "asset_type": "stock"
                },
                {
                    "symbol": "Cash",
                    "quantity": 25000,
                    "cost_basis": 25000,
                    "current_price": 1.0,
                    "asset_type": "cash"
                }
            ],
            "tax_rate": 0.24,
            "capital_gains_rate": 0.15
        }
        
        charitable_response = await authenticated_client.post(
            "/tax-optimization/optimize-charitable-giving",
            json=charitable_data
        )
        assert charitable_response.status_code == 200
        charitable_optimization = charitable_response.json()
        
        assert "recommended_strategy" in charitable_optimization
        assert "tax_savings" in charitable_optimization
        assert "net_cost" in charitable_optimization
        
        # Should recommend donating appreciated stock
        strategy = charitable_optimization["recommended_strategy"]
        assert strategy["method"] == "appreciated_securities"
        assert strategy["recommended_asset"] == "AAPL"
        
        # Tax savings should exceed deduction-only benefit
        total_tax_savings = charitable_optimization["tax_savings"]["total"]
        deduction_benefit = 25000 * 0.24  # donation * tax rate
        assert total_tax_savings > deduction_benefit


@pytest.mark.integration
class TestRiskManagementIntegration:
    """Test risk management and compliance integration."""
    
    async def test_portfolio_risk_analysis(self, authenticated_client: AsyncClient):
        """Test comprehensive portfolio risk analysis."""
        
        # 1. Portfolio setup
        portfolio_data = {
            "positions": [
                {"symbol": "SPY", "weight": 0.4, "asset_class": "US_EQUITY"},
                {"symbol": "QQQ", "weight": 0.2, "asset_class": "US_GROWTH"},
                {"symbol": "EFA", "weight": 0.2, "asset_class": "INTERNATIONAL"},
                {"symbol": "BND", "weight": 0.15, "asset_class": "BONDS"},
                {"symbol": "VNQ", "weight": 0.05, "asset_class": "REAL_ESTATE"}
            ],
            "portfolio_value": 500000
        }
        
        # 2. Risk metrics calculation
        risk_analysis_response = await authenticated_client.post(
            "/risk-management/analyze-portfolio-risk",
            json=portfolio_data
        )
        assert risk_analysis_response.status_code == 200
        risk_analysis = risk_analysis_response.json()
        
        assert "portfolio_volatility" in risk_analysis
        assert "var_95" in risk_analysis  # Value at Risk
        assert "cvar_95" in risk_analysis  # Conditional Value at Risk
        assert "max_drawdown" in risk_analysis
        assert "sharpe_ratio" in risk_analysis
        assert "correlation_analysis" in risk_analysis
        
        # Risk metrics should be reasonable
        assert 0.05 <= risk_analysis["portfolio_volatility"] <= 0.30
        assert risk_analysis["var_95"] < 0  # VaR is negative (loss)
        assert risk_analysis["cvar_95"] < risk_analysis["var_95"]  # CVaR < VaR
        
        # 3. Stress testing
        stress_scenarios = {
            "scenarios": [
                {"name": "2008_financial_crisis", "equity_shock": -0.37, "bond_shock": 0.05},
                {"name": "covid_march_2020", "equity_shock": -0.34, "bond_shock": 0.08},
                {"name": "tech_bubble_2000", "equity_shock": -0.49, "bond_shock": 0.12},
                {"name": "rising_rates", "equity_shock": -0.15, "bond_shock": -0.10}
            ]
        }
        
        stress_test_response = await authenticated_client.post(
            "/risk-management/stress-test",
            json={**portfolio_data, **stress_scenarios}
        )
        assert stress_test_response.status_code == 200
        stress_results = stress_test_response.json()
        
        assert "scenario_results" in stress_results
        assert "worst_case_loss" in stress_results
        assert "risk_recommendations" in stress_results
        
        # Should have results for all scenarios
        scenario_results = stress_results["scenario_results"]
        assert len(scenario_results) == len(stress_scenarios["scenarios"])
        
        for result in scenario_results:
            assert "scenario_name" in result
            assert "portfolio_loss" in result
            assert "portfolio_value_after" in result
        
        # 4. Dynamic hedging recommendations
        hedging_response = await authenticated_client.post(
            "/risk-management/hedging-recommendations",
            json={
                **portfolio_data,
                "risk_budget": 0.15,  # 15% volatility target
                "hedging_budget": 0.02  # 2% of portfolio for hedging
            }
        )
        assert hedging_response.status_code == 200
        hedging_recommendations = hedging_recommendations.json()
        
        assert "recommended_hedges" in hedging_recommendations
        assert "hedge_ratio" in hedging_recommendations
        assert "expected_portfolio_volatility" in hedging_recommendations
    
    async def test_compliance_monitoring(self, authenticated_client: AsyncClient):
        """Test compliance monitoring and alerts."""
        
        # 1. Set up compliance constraints
        compliance_rules = {
            "max_single_stock_weight": 0.05,
            "max_sector_concentration": 0.25,
            "min_diversification_score": 0.8,
            "max_portfolio_beta": 1.2,
            "required_liquidity_buffer": 0.10,
            "esg_minimum_score": 6.0
        }
        
        # 2. Portfolio that may violate some rules
        test_portfolio = {
            "positions": [
                {"symbol": "AAPL", "weight": 0.08, "sector": "technology", "beta": 1.3},  # Violates single stock limit
                {"symbol": "MSFT", "weight": 0.15, "sector": "technology", "beta": 1.1},
                {"symbol": "GOOGL", "weight": 0.10, "sector": "technology", "beta": 1.2},  # Tech concentration issue
                {"symbol": "JPM", "weight": 0.05, "sector": "financials", "beta": 1.4},
                {"symbol": "BND", "weight": 0.62, "sector": "bonds", "beta": 0.1}
            ]
        }
        
        compliance_check_response = await authenticated_client.post(
            "/risk-management/compliance-check",
            json={"portfolio": test_portfolio, "rules": compliance_rules}
        )
        assert compliance_check_response.status_code == 200
        compliance_result = compliance_check_response.json()
        
        assert "compliance_status" in compliance_result
        assert "violations" in compliance_result
        assert "recommendations" in compliance_result
        
        # Should detect violations
        violations = compliance_result["violations"]
        assert len(violations) > 0
        
        # Should detect single stock weight violation
        single_stock_violation = next(
            (v for v in violations if "single_stock_weight" in v["rule"]), None
        )
        assert single_stock_violation is not None
        assert single_stock_violation["violating_asset"] == "AAPL"
        
        # Should detect sector concentration
        sector_violation = next(
            (v for v in violations if "sector_concentration" in v["rule"]), None
        )
        assert sector_violation is not None
        assert sector_violation["violating_sector"] == "technology"
        
        # 3. Get rebalancing recommendations to fix violations
        rebalancing_response = await authenticated_client.post(
            "/risk-management/rebalancing-recommendations",
            json={"portfolio": test_portfolio, "compliance_rules": compliance_rules}
        )
        assert rebalancing_response.status_code == 200
        rebalancing_recommendations = rebalancing_response.json()
        
        assert "recommended_trades" in rebalancing_recommendations
        assert "expected_compliance_improvement" in rebalancing_recommendations
        
        # Recommendations should reduce violations
        trades = rebalancing_recommendations["recommended_trades"]
        aapl_trade = next((t for t in trades if t["symbol"] == "AAPL"), None)
        if aapl_trade:
            assert aapl_trade["action"] == "sell"  # Should reduce AAPL position


@pytest.mark.integration
@pytest.mark.performance
class TestPerformanceAndScalability:
    """Test API performance and scalability."""
    
    async def test_concurrent_optimization_requests(self, authenticated_client: AsyncClient):
        """Test handling of concurrent optimization requests."""
        
        optimization_request = {
            "universe": [
                {"symbol": "SPY", "asset_class": "US_EQUITY", "weight": 0.0},
                {"symbol": "BND", "asset_class": "BONDS", "weight": 0.0}
            ],
            "objective": "maximize_sharpe",
            "constraints": {"max_weight": 0.8, "min_weight": 0.2}
        }
        
        # Launch multiple concurrent requests
        tasks = []
        for i in range(5):
            task = authenticated_client.post(
                "/portfolio/optimize",
                json=optimization_request
            )
            tasks.append(task)
        
        # Wait for all to complete
        results = await asyncio.gather(*tasks)
        
        # All should succeed
        for response in results:
            assert response.status_code == 200
            result_data = response.json()
            assert "weights" in result_data
            assert "sharpe_ratio" in result_data
    
    async def test_large_portfolio_optimization(self, authenticated_client: AsyncClient):
        """Test optimization with large portfolio universe."""
        
        # Create large universe (50+ assets)
        large_universe = []
        sectors = ["technology", "healthcare", "financials", "energy", "utilities"]
        
        for i in range(50):
            large_universe.append({
                "symbol": f"STOCK_{i:03d}",
                "asset_class": sectors[i % len(sectors)],
                "weight": 0.0
            })
        
        optimization_request = {
            "universe": large_universe,
            "objective": "maximize_sharpe",
            "constraints": {
                "max_weight": 0.1,
                "min_weight": 0.005,
                "max_sector_concentration": 0.3
            }
        }
        
        # Should handle large optimization efficiently
        start_time = datetime.now()
        response = await authenticated_client.post(
            "/portfolio/optimize",
            json=optimization_request
        )
        end_time = datetime.now()
        
        assert response.status_code == 200
        
        # Should complete within reasonable time (< 30 seconds)
        execution_time = (end_time - start_time).total_seconds()
        assert execution_time < 30
        
        result = response.json()
        assert "weights" in result
        assert len(result["weights"]) == len(large_universe)
    
    async def test_api_response_times(self, authenticated_client: AsyncClient):
        """Test API response times for various endpoints."""
        
        endpoints_to_test = [
            ("/market-data/quote/AAPL", "GET", None, 2.0),  # 2 second SLA
            ("/financial-profiles/me", "GET", None, 1.0),   # 1 second SLA
            ("/goals/", "GET", None, 1.0),                   # 1 second SLA
            ("/recommendations/", "GET", None, 5.0),         # 5 second SLA for recommendations
        ]
        
        for endpoint, method, data, sla_seconds in endpoints_to_test:
            start_time = datetime.now()
            
            if method == "GET":
                response = await authenticated_client.get(endpoint)
            elif method == "POST":
                response = await authenticated_client.post(endpoint, json=data)
            
            end_time = datetime.now()
            response_time = (end_time - start_time).total_seconds()
            
            # Should meet SLA
            assert response_time < sla_seconds, \
                f"{endpoint} took {response_time}s, exceeding SLA of {sla_seconds}s"
            
            # Should return valid response
            assert response.status_code in [200, 201]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])
