"""
Financial Planning Pydantic Schemas

Based on the AI Financial Planner Implementation Guide, these schemas define
the data models for creating, managing, and retrieving financial plans.
"""

from typing import Literal, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime


class PlanInputModel(BaseModel):
    """Input model for creating a new financial plan"""
    
    # Demographics
    age: int = Field(..., ge=18, le=100, description="Current age of the user")
    target_retirement_age: int = Field(..., ge=50, le=100, description="Target age for retirement")
    marital_status: Literal["single", "married"] = Field(..., description="Marital status of the user")
    
    # Financial snapshot
    current_savings_balance: float = Field(..., ge=0, description="Current total savings balance")
    annual_savings_rate_percentage: float = Field(..., ge=0, le=100, description="Percentage of income saved annually")
    income_level: float = Field(..., ge=0, description="Current annual income level")
    debt_balance: float = Field(..., ge=0, description="Total outstanding debt balance")
    debt_interest_rate_percentage: float = Field(..., ge=0, le=100, description="Annual interest rate on debt")
    
    # Account buckets (must sum to 100%)
    account_buckets_taxable: float = Field(..., ge=0, le=100, description="Percentage of savings in taxable accounts")
    account_buckets_401k_ira: float = Field(..., ge=0, le=100, description="Percentage of savings in 401k/IRA accounts")
    account_buckets_roth: float = Field(..., ge=0, le=100, description="Percentage of savings in Roth accounts")
    
    # Risk and goals
    risk_preference: Literal["conservative", "balanced", "aggressive"] = Field(..., description="User's risk preference")
    desired_retirement_spending_per_year: float = Field(..., ge=0, description="Desired annual spending in retirement")
    
    # Optional fields
    plan_name: Optional[str] = Field(None, description="Optional name for the financial plan")
    notes: Optional[str] = Field(None, description="Additional notes or context")
    
    @validator('target_retirement_age')
    def retirement_age_must_be_after_current(cls, v, values):
        if 'age' in values and v <= values['age']:
            raise ValueError('Retirement age must be greater than current age')
        return v
    
    @validator('account_buckets_taxable', 'account_buckets_401k_ira', 'account_buckets_roth')
    def account_buckets_must_sum_to_100(cls, v, values):
        # This validator will be called for each field, so we need to check the sum
        # We'll do the full validation in a separate validator
        return v
    
    @validator('*', pre=True)
    def validate_account_buckets_sum(cls, v, field):
        if field.name in ['account_buckets_taxable', 'account_buckets_401k_ira', 'account_buckets_roth']:
            # Get all values to validate sum
            values = getattr(cls, '__dict__', {})
            if all(f in values for f in ['account_buckets_taxable', 'account_buckets_401k_ira', 'account_buckets_roth']):
                total = (values.get('account_buckets_taxable', 0) + 
                        values.get('account_buckets_401k_ira', 0) + 
                        values.get('account_buckets_roth', 0))
                if not abs(total - 100.0) < 0.01:  # Allow small floating point differences
                    raise ValueError(f'Account buckets must sum to 100%, got {total:.1f}%')
        return v


class PlanCreationResponse(BaseModel):
    """Response model for successful plan creation"""
    
    plan_id: str = Field(..., description="Unique identifier for the created financial plan")
    status: str = Field("processing", description="Current status of the plan simulation")
    message: str = Field("Plan created successfully", description="Status message")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Plan creation timestamp")
    estimated_completion_time: Optional[int] = Field(None, description="Estimated completion time in seconds")


class PlanStatusResponse(BaseModel):
    """Response model for checking plan simulation status"""
    
    plan_id: str = Field(..., description="Unique identifier for the financial plan")
    status: Literal["processing", "completed", "failed"] = Field(..., description="Current status of the plan simulation")
    progress: float = Field(..., ge=0, le=100, description="Simulation progress in percentage")
    message: Optional[str] = Field(None, description="Additional status message")
    current_step: Optional[str] = Field(None, description="Current simulation step")
    estimated_time_remaining: Optional[int] = Field(None, description="Estimated time remaining in seconds")
    last_updated: datetime = Field(default_factory=datetime.utcnow, description="Last status update timestamp")


class TradeOffAnalysis(BaseModel):
    """Trade-off scenario analysis results"""
    
    scenario_name: str = Field(..., description="Name of the trade-off scenario")
    description: str = Field(..., description="Description of the scenario")
    probability_of_success: float = Field(..., ge=0, le=100, description="Probability of success under this scenario")
    median_balance: float = Field(..., description="Median balance at retirement under this scenario")
    impact_on_success_rate: float = Field(..., description="Change in success rate compared to baseline")
    recommended_action: str = Field(..., description="Recommended action based on this scenario")
    trade_off_details: Dict[str, Any] = Field(..., description="Detailed trade-off information")


class PortfolioRecommendation(BaseModel):
    """Portfolio allocation recommendation"""
    
    risk_level: str = Field(..., description="Risk level of the recommended portfolio")
    asset_allocation: Dict[str, float] = Field(..., description="Asset allocation percentages")
    expected_return: float = Field(..., description="Expected annual return")
    expected_volatility: float = Field(..., description="Expected annual volatility")
    sharpe_ratio: float = Field(..., description="Expected Sharpe ratio")
    rebalancing_frequency: str = Field(..., description="Recommended rebalancing frequency")
    etf_recommendations: Dict[str, str] = Field(..., description="Specific ETF recommendations by asset class")
    rationale: str = Field(..., description="Explanation of the recommendation")


class PlanResultsResponse(BaseModel):
    """Complete simulation results for a financial plan"""
    
    plan_id: str = Field(..., description="Unique identifier for the financial plan")
    
    # Baseline results
    baseline_probability_of_success: float = Field(..., ge=0, le=100, description="Probability of funding retirement goal at current path")
    median_balance: float = Field(..., description="Median balance at retirement")
    tenth_percentile_balance: float = Field(..., description="10th percentile balance at retirement")
    
    # Trade-off scenarios
    trade_off_scenarios: list[TradeOffAnalysis] = Field(..., description="Analysis of different trade-off scenarios")
    
    # Portfolio recommendation
    portfolio_recommendation: PortfolioRecommendation = Field(..., description="Recommended portfolio allocation")
    
    # AI-generated narrative
    client_friendly_narrative: str = Field(..., description="Generative AI-powered narrative explanation")
    
    # Compliance and audit
    disclaimer: str = Field("Simulations are estimates, not guarantees.", description="Compliance disclaimer")
    cma_version: str = Field(..., description="Version of Capital Market Assumptions used")
    simulation_metadata: Dict[str, Any] = Field(..., description="Simulation configuration and metadata")
    
    # Timestamps
    created_at: datetime = Field(..., description="Plan creation timestamp")
    completed_at: datetime = Field(..., description="Simulation completion timestamp")
    
    class Config:
        schema_extra = {
            "example": {
                "plan_id": "plan_12345",
                "baseline_probability_of_success": 75.5,
                "median_balance": 1250000.0,
                "tenth_percentile_balance": 850000.0,
                "trade_off_scenarios": [
                    {
                        "scenario_name": "Save More",
                        "description": "Increase annual savings by 3%",
                        "probability_of_success": 82.3,
                        "median_balance": 1350000.0,
                        "impact_on_success_rate": 6.8,
                        "recommended_action": "Consider increasing savings rate",
                        "trade_off_details": {"savings_increase": "3%", "lifestyle_impact": "moderate"}
                    }
                ],
                "portfolio_recommendation": {
                    "risk_level": "balanced",
                    "asset_allocation": {"stocks": 60, "bonds": 30, "cash": 10},
                    "expected_return": 0.065,
                    "expected_volatility": 0.12,
                    "sharpe_ratio": 0.54,
                    "rebalancing_frequency": "quarterly",
                    "etf_recommendations": {"stocks": "VTI", "bonds": "BND", "cash": "VMFXX"},
                    "rationale": "Balanced approach suitable for moderate risk tolerance"
                },
                "client_friendly_narrative": "Based on your current plan, you have a 75.5% chance of funding your retirement...",
                "disclaimer": "Simulations are estimates, not guarantees.",
                "cma_version": "2024.1",
                "simulation_metadata": {"n_simulations": 50000, "random_seed": 12345},
                "created_at": "2024-01-27T10:00:00Z",
                "completed_at": "2024-01-27T10:00:05Z"
            }
        }
