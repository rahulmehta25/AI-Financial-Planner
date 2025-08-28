"""
Monte Carlo Simulation API Endpoints

New endpoints for the comprehensive Monte Carlo simulation engine with
advanced features including trade-off analysis and stress testing.
"""

from typing import Any, Dict, List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from pydantic import BaseModel, Field, validator
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.core.exceptions import NotFoundError, ValidationError
from app.models.user import User
from app.simulations.orchestrator import SimulationOrchestrator, SimulationRequest
from app.simulations.portfolio_mapping import RiskTolerance

router = APIRouter()

# Initialize simulation orchestrator
simulation_orchestrator = SimulationOrchestrator()


class MonteCarloSimulationRequest(BaseModel):
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
    
    @validator('risk_tolerance')
    def validate_risk_tolerance(cls, v):
        valid_values = [rt.value for rt in RiskTolerance]
        if v.lower() not in valid_values:
            raise ValueError(f'Risk tolerance must be one of: {", ".join(valid_values)}')
        return v.lower()


class QuickAnalysisRequest(BaseModel):
    """Request model for quick analysis"""
    
    current_age: int = Field(..., ge=18, le=100)
    retirement_age: int = Field(..., ge=50, le=100)
    current_portfolio_value: float = Field(..., ge=0)
    annual_contribution: float = Field(..., ge=0)
    current_annual_income: float = Field(..., gt=0)
    risk_tolerance: str = Field("moderate")
    
    @validator('retirement_age')
    def retirement_age_validation(cls, v, values):
        if 'current_age' in values and v <= values['current_age']:
            raise ValueError('Retirement age must be greater than current age')
        return v


class SimulationResponse(BaseModel):
    """Response model for simulation results"""
    
    request_id: str
    simulation_name: Optional[str]
    timestamp: str
    
    # Core results
    success_probability: float
    median_retirement_balance: float
    percentile_10_balance: float
    percentile_90_balance: float
    
    # Portfolio information
    portfolio_allocation: Dict[str, float]
    etf_recommendations: List[Dict[str, Any]]
    
    # Analysis results
    comprehensive_results: Dict[str, Any]
    trade_off_analysis: Optional[Dict[str, Any]]
    stress_test_results: Optional[Dict[str, Any]]
    
    # Performance metrics
    simulation_time_seconds: float
    performance_metrics: Dict[str, Any]
    
    # Recommendations
    recommendations: Dict[str, Any]
    summary_report: str


class QuickAnalysisResponse(BaseModel):
    """Response model for quick analysis"""
    
    success_probability: float
    median_balance: float
    assessment: str
    key_recommendations: List[str]


@router.post("/run-simulation", response_model=SimulationResponse)
async def run_monte_carlo_simulation(
    request: MonteCarloSimulationRequest,
    current_user: User = Depends(get_current_user),
    background_tasks: BackgroundTasks = None
) -> Any:
    """
    Run comprehensive Monte Carlo simulation for retirement planning
    
    This endpoint runs a full Monte Carlo simulation with:
    - 50,000 simulation paths by default
    - Comprehensive statistical analysis
    - Trade-off analysis for different strategies
    - Stress testing under various market conditions
    - ETF recommendations
    - Actionable recommendations
    
    The simulation typically takes 10-30 seconds depending on parameters.
    """
    try:
        # Convert request to internal format
        simulation_request = SimulationRequest(
            user_id=str(current_user.id),
            simulation_name=request.simulation_name,
            current_age=request.current_age,
            retirement_age=request.retirement_age,
            life_expectancy=request.life_expectancy,
            current_portfolio_value=request.current_portfolio_value,
            annual_contribution=request.annual_contribution,
            contribution_growth_rate=request.contribution_growth_rate,
            target_replacement_ratio=request.target_replacement_ratio,
            current_annual_income=request.current_annual_income,
            risk_tolerance=request.risk_tolerance,
            custom_portfolio_allocation=request.custom_portfolio_allocation,
            n_simulations=request.n_simulations,
            random_seed=request.random_seed,
            include_trade_off_analysis=request.include_trade_off_analysis,
            include_stress_testing=request.include_stress_testing,
            rebalancing_frequency=request.rebalancing_frequency,
            market_regime=request.market_regime
        )
        
        # Run simulation
        results = await simulation_orchestrator.run_comprehensive_simulation(simulation_request)
        
        # Convert results to response format
        return SimulationResponse(
            request_id=results.request_id,
            simulation_name=results.simulation_name,
            timestamp=results.timestamp.isoformat(),
            success_probability=results.success_probability,
            median_retirement_balance=results.median_retirement_balance,
            percentile_10_balance=results.percentile_10_balance,
            percentile_90_balance=results.percentile_90_balance,
            portfolio_allocation=results.portfolio_allocation,
            etf_recommendations=results.etf_recommendations,
            comprehensive_results=results.comprehensive_results,
            trade_off_analysis=results.trade_off_analysis,
            stress_test_results=results.stress_test_results,
            simulation_time_seconds=results.simulation_time_seconds,
            performance_metrics=results.performance_metrics,
            recommendations=results.recommendations,
            summary_report=results.summary_report
        )
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Validation error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Simulation failed: {str(e)}"
        )


@router.post("/quick-analysis", response_model=QuickAnalysisResponse)
async def quick_retirement_analysis(
    request: QuickAnalysisRequest,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Run quick retirement analysis for immediate feedback
    
    This endpoint provides fast analysis (typically 1-3 seconds) with:
    - 5,000 simulation paths
    - Basic success probability
    - Key recommendations
    - Overall assessment
    
    Ideal for initial consultation or parameter exploration.
    """
    try:
        # Create simulation request with quick settings
        simulation_request = SimulationRequest(
            user_id=str(current_user.id),
            current_age=request.current_age,
            retirement_age=request.retirement_age,
            current_portfolio_value=request.current_portfolio_value,
            annual_contribution=request.annual_contribution,
            current_annual_income=request.current_annual_income,
            risk_tolerance=request.risk_tolerance,
            n_simulations=5_000,  # Reduced for speed
            include_trade_off_analysis=False,
            include_stress_testing=False
        )
        
        # Run quick analysis
        results = await simulation_orchestrator.run_quick_analysis(simulation_request)
        
        return QuickAnalysisResponse(**results)
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Validation error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Quick analysis failed: {str(e)}"
        )


@router.get("/portfolio-options")
async def get_portfolio_options() -> Dict[str, Any]:
    """
    Get available portfolio options and risk tolerance levels
    
    Returns information about:
    - Risk tolerance levels
    - Model portfolios for each risk level
    - Available asset classes
    - Example ETF mappings
    """
    try:
        portfolio_mapper = simulation_orchestrator.portfolio_mapper
        
        # Get risk tolerance options
        risk_levels = portfolio_mapper.get_risk_tolerance_options()
        
        # Get model portfolios
        model_portfolios = {}
        for risk_level in risk_levels:
            try:
                model_portfolio = portfolio_mapper.get_model_portfolio(risk_level)
                model_portfolios[risk_level] = {
                    "name": model_portfolio.name,
                    "description": model_portfolio.description,
                    "allocations": model_portfolio.allocations,
                    "expected_return": model_portfolio.expected_return,
                    "expected_volatility": model_portfolio.expected_volatility,
                    "target_age_range": model_portfolio.target_age_range
                }
            except Exception:
                continue
        
        # Get available asset classes
        asset_classes = portfolio_mapper.get_available_asset_classes()
        
        return {
            "risk_tolerance_levels": risk_levels,
            "model_portfolios": model_portfolios,
            "available_asset_classes": asset_classes,
            "asset_class_descriptions": {
                "US_LARGE_CAP": "US Large Cap Equities (S&P 500)",
                "US_SMALL_CAP": "US Small Cap Equities (Russell 2000)",
                "INTERNATIONAL_DEVELOPED": "International Developed Market Equities",
                "EMERGING_MARKETS": "Emerging Market Equities",
                "US_TREASURY_INTERMEDIATE": "US Intermediate Treasury Bonds",
                "CORPORATE_BONDS": "US Investment Grade Corporate Bonds",
                "HIGH_YIELD_BONDS": "US High Yield Corporate Bonds",
                "REITS": "Real Estate Investment Trusts",
                "CASH": "Cash and Money Market Instruments"
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get portfolio options: {str(e)}"
        )


@router.post("/validate-portfolio")
async def validate_portfolio_allocation(
    allocation: Dict[str, float]
) -> Dict[str, Any]:
    """
    Validate a custom portfolio allocation
    
    Returns validation results and calculated metrics for the portfolio.
    """
    try:
        portfolio_mapper = simulation_orchestrator.portfolio_mapper
        
        # Validate allocation
        is_valid, errors = portfolio_mapper.validate_allocation(allocation)
        
        result = {
            "is_valid": is_valid,
            "errors": errors
        }
        
        if is_valid:
            # Calculate portfolio metrics
            from app.simulations.engine import PortfolioAllocation
            portfolio = PortfolioAllocation(allocation)
            metrics = portfolio_mapper.calculate_portfolio_metrics(portfolio)
            result["metrics"] = metrics
            
            # Get ETF recommendations
            etf_recs = portfolio_mapper.get_etf_recommendations(portfolio)
            result["etf_recommendations"] = [
                {
                    "symbol": etf.symbol,
                    "name": etf.name,
                    "asset_class": etf.asset_class,
                    "expense_ratio": etf.expense_ratio,
                    "description": etf.description
                }
                for etf in etf_recs
            ]
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Portfolio validation failed: {str(e)}"
        )


@router.get("/market-assumptions")
async def get_current_market_assumptions() -> Dict[str, Any]:
    """
    Get current market assumptions used in simulations
    
    Returns forward-looking expected returns, volatilities, and correlations
    for all asset classes.
    """
    try:
        market_assumptions = simulation_orchestrator.market_assumptions
        summary = market_assumptions.get_summary_statistics()
        
        # Get individual asset class assumptions
        asset_details = {}
        for asset_name, asset_class in market_assumptions.asset_classes.items():
            asset_details[asset_name] = {
                "name": asset_class.name,
                "expected_return": asset_class.expected_return,
                "volatility": asset_class.volatility,
                "sharpe_ratio": asset_class.sharpe_ratio,
                "description": asset_class.description
            }
        
        return {
            "summary_statistics": summary,
            "asset_class_assumptions": asset_details,
            "inflation_assumptions": market_assumptions.inflation_assumptions,
            "last_updated": summary["last_updated"]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get market assumptions: {str(e)}"
        )


@router.get("/performance-metrics")
async def get_engine_performance() -> Dict[str, Any]:
    """
    Get performance metrics for the simulation engine
    
    Returns performance statistics including execution times and throughput.
    """
    try:
        performance_metrics = simulation_orchestrator.monte_carlo_engine.get_performance_metrics()
        
        return {
            "engine_performance": performance_metrics,
            "component_status": {
                "market_assumptions": "active",
                "portfolio_mapper": "active", 
                "monte_carlo_engine": "active",
                "results_calculator": "active",
                "trade_off_analyzer": "active"
            },
            "capabilities": {
                "max_simulations": 100_000,
                "target_execution_time": "< 30 seconds for 50,000 simulations",
                "supported_asset_classes": len(simulation_orchestrator.portfolio_mapper.get_available_asset_classes()),
                "numba_compilation": "enabled",
                "parallel_processing": "enabled"
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get performance metrics: {str(e)}"
        )