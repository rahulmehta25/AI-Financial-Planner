"""
Simulation Pydantic Schemas

Schemas for simulation creation, updates, and responses.
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, validator
from datetime import datetime


class SimulationCreate(BaseModel):
    """Request model for creating a new simulation"""
    
    name: str = Field(..., description="Name of the simulation")
    description: Optional[str] = Field(None, description="Description of the simulation")
    simulation_type: str = Field(..., description="Type of simulation (monte_carlo, scenario_analysis, etc.)")
    parameters: Dict[str, Any] = Field(..., description="Simulation parameters")
    user_id: Optional[str] = Field(None, description="User ID (will be set automatically)")
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Retirement Planning 2024",
                "description": "Monte Carlo simulation for retirement planning",
                "simulation_type": "monte_carlo",
                "parameters": {
                    "n_simulations": 50000,
                    "years_to_retirement": 25,
                    "initial_portfolio_value": 100000
                }
            }
        }


class SimulationUpdate(BaseModel):
    """Request model for updating a simulation"""
    
    name: Optional[str] = Field(None, description="New name for the simulation")
    description: Optional[str] = Field(None, description="New description for the simulation")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Updated simulation parameters")
    status: Optional[str] = Field(None, description="New status for the simulation")


class SimulationResponse(BaseModel):
    """Response model for simulation data"""
    
    id: str = Field(..., description="Unique identifier for the simulation")
    name: str = Field(..., description="Name of the simulation")
    description: Optional[str] = Field(None, description="Description of the simulation")
    simulation_type: str = Field(..., description="Type of simulation")
    status: str = Field(..., description="Current status of the simulation")
    parameters: Dict[str, Any] = Field(..., description="Simulation parameters")
    results: Optional[Dict[str, Any]] = Field(None, description="Simulation results")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    user_id: Optional[str] = Field(None, description="User ID who created the simulation")
    
    class Config:
        schema_extra = {
            "example": {
                "id": "sim_12345",
                "name": "Retirement Planning 2024",
                "description": "Monte Carlo simulation for retirement planning",
                "simulation_type": "monte_carlo",
                "status": "completed",
                "parameters": {"n_simulations": 50000, "years_to_retirement": 25},
                "results": {"success_probability": 75.5, "median_balance": 1250000},
                "created_at": "2024-01-27T10:00:00Z",
                "updated_at": "2024-01-27T10:05:00Z",
                "completed_at": "2024-01-27T10:05:00Z",
                "user_id": "user_123"
            }
        }


class MonteCarloRequest(BaseModel):
    """Request model for Monte Carlo simulation"""
    
    # Basic information
    simulation_name: Optional[str] = Field(None, description="Optional name for the simulation")
    
    # Demographics
    current_age: int = Field(..., ge=18, le=100, description="Current age")
    retirement_age: int = Field(..., ge=50, le=100, description="Planned retirement age")
    life_expectancy: int = Field(85, ge=65, le=120, description="Expected life expectancy")
    
    # Financial parameters
    current_portfolio_value: float = Field(..., ge=0, description="Current portfolio value")
    annual_contribution: float = Field(..., ge=0, description="Annual contribution amount")
    contribution_growth_rate: float = Field(0.03, ge=-0.10, le=0.20, description="Annual growth rate of contributions")
    target_replacement_ratio: float = Field(0.80, ge=0.20, le=2.0, description="Target income replacement ratio")
    current_annual_income: float = Field(..., gt=0, description="Current annual income")
    
    # Risk preferences
    risk_tolerance: str = Field("moderate", description="Risk tolerance level")
    custom_portfolio_allocation: Optional[Dict[str, float]] = Field(None, description="Custom portfolio allocation")
    
    # Simulation settings
    n_simulations: int = Field(50_000, ge=1_000, le=100_000, description="Number of Monte Carlo simulations")
    random_seed: Optional[int] = Field(None, description="Random seed for reproducibility")
    include_trade_off_analysis: bool = Field(True, description="Include trade-off analysis")
    include_stress_testing: bool = Field(True, description="Include stress testing")
    
    # Advanced settings
    rebalancing_frequency: int = Field(12, ge=1, le=12, description="Rebalancing frequency per year")
    market_regime: str = Field("normal", description="Market regime assumption")
    
    @validator('retirement_age')
    def retirement_age_must_be_after_current(cls, v, values):
        if 'current_age' in values and v <= values['current_age']:
            raise ValueError('Retirement age must be greater than current age')
        return v
    
    @validator('life_expectancy')
    def life_expectancy_must_be_after_retirement(cls, v, values):
        if 'retirement_age' in values and v <= values['retirement_age']:
            raise ValueError('Life expectancy must be greater than retirement age')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "simulation_name": "My Retirement Plan",
                "current_age": 35,
                "retirement_age": 65,
                "life_expectancy": 85,
                "current_portfolio_value": 100000,
                "annual_contribution": 15000,
                "contribution_growth_rate": 0.03,
                "target_replacement_ratio": 0.80,
                "current_annual_income": 75000,
                "risk_tolerance": "moderate",
                "n_simulations": 50000,
                "include_trade_off_analysis": True,
                "include_stress_testing": True
            }
        }


class ScenarioAnalysisRequest(BaseModel):
    """Request model for scenario analysis"""
    
    simulation_name: Optional[str] = Field(None, description="Optional name for the scenario analysis")
    base_simulation_id: Optional[str] = Field(None, description="ID of base simulation to compare against")
    
    # Scenario parameters
    scenarios: List[str] = Field(..., description="List of scenarios to analyze")
    scenario_parameters: Dict[str, Dict[str, Any]] = Field(..., description="Parameters for each scenario")
    
    # Analysis settings
    include_sensitivity_analysis: bool = Field(True, description="Include sensitivity analysis")
    confidence_levels: List[float] = Field([0.90, 0.95, 0.99], description="Confidence levels for analysis")
    
    class Config:
        schema_extra = {
            "example": {
                "simulation_name": "Market Scenario Analysis",
                "scenarios": ["bull_market", "bear_market", "crisis"],
                "scenario_parameters": {
                    "bull_market": {"return_multiplier": 1.2, "volatility_multiplier": 0.8},
                    "bear_market": {"return_multiplier": 0.8, "volatility_multiplier": 1.2},
                    "crisis": {"return_multiplier": 0.6, "volatility_multiplier": 1.5}
                },
                "include_sensitivity_analysis": True,
                "confidence_levels": [0.90, 0.95, 0.99]
            }
        }
