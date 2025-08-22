"""
Pydantic schemas for the AI Financial Planning System
"""

from .financial_planning import (
    PlanInputModel,
    PlanCreationResponse,
    PlanStatusResponse,
    PlanResultsResponse,
    TradeOffAnalysis,
    PortfolioRecommendation
)

from .simulation import (
    SimulationCreate,
    SimulationResponse,
    SimulationUpdate,
    MonteCarloRequest,
    ScenarioAnalysisRequest
)

from .user import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserLogin,
    UserProfile
)

__all__ = [
    # Financial Planning
    "PlanInputModel",
    "PlanCreationResponse", 
    "PlanStatusResponse",
    "PlanResultsResponse",
    "TradeOffAnalysis",
    "PortfolioRecommendation",
    
    # Simulation
    "SimulationCreate",
    "SimulationResponse", 
    "SimulationUpdate",
    "MonteCarloRequest",
    "ScenarioAnalysisRequest",
    
    # User
    "UserCreate",
    "UserUpdate",
    "UserResponse", 
    "UserLogin",
    "UserProfile"
]