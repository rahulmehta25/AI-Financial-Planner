"""
API endpoints for advanced investment strategies with risk warnings
"""

from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from pydantic import BaseModel, Field, validator
from datetime import datetime

from app.services.advanced_strategies import (
    AdvancedStrategiesService, 
    StrategyType, 
    RiskLevel
)
from app.api.deps import get_current_active_user
from app.database.models import User


router = APIRouter(prefix="/advanced-strategies", tags=["advanced-strategies"])


# Pydantic models for request/response
class RiskAcknowledgmentRequest(BaseModel):
    """Request model for risk acknowledgment"""
    strategy_type: str = Field(..., description="Strategy type to acknowledge")
    quiz_score: float = Field(0.0, ge=0.0, le=1.0, description="Quiz score (0-1)")
    confirmation_text: str = Field(..., description="Confirmation text from user")
    
    @validator('confirmation_text')
    def validate_confirmation(cls, v):
        required_text = "I understand the risks and can afford to lose this investment"
        if required_text.lower() not in v.lower():
            raise ValueError("Must include risk acknowledgment confirmation text")
        return v


class StrategyAnalysisRequest(BaseModel):
    """Request model for strategy analysis"""
    strategy_type: str = Field(..., description="Type of strategy to analyze")
    market_data: Optional[Dict[str, Any]] = Field(None, description="Market data for analysis")
    portfolio_value: Optional[float] = Field(None, ge=1000, description="Portfolio value")


class PortfolioStressTestRequest(BaseModel):
    """Request model for portfolio stress testing"""
    positions: List[Dict[str, Any]] = Field(..., description="Portfolio positions")
    scenario: str = Field("financial_crisis_2008", description="Stress test scenario")
    
    @validator('positions')
    def validate_positions(cls, v):
        if not v:
            raise ValueError("At least one position is required")
        
        for pos in v:
            if 'value' not in pos or 'symbol' not in pos:
                raise ValueError("Each position must have 'value' and 'symbol'")
                
        return v


class PositionSizingRequest(BaseModel):
    """Request model for position sizing calculation"""
    strategy_type: str = Field(..., description="Strategy type")
    portfolio_value: float = Field(..., ge=1000, description="Total portfolio value")
    historical_performance: Dict[str, float] = Field(
        ..., 
        description="Historical performance data"
    )
    
    @validator('historical_performance')
    def validate_performance_data(cls, v):
        required_keys = ['win_rate', 'avg_win', 'avg_loss']
        for key in required_keys:
            if key not in v:
                raise ValueError(f"Missing required key: {key}")
        return v


class GrowthStockScreenRequest(BaseModel):
    """Request model for growth stock screening"""
    revenue_growth_3y: Optional[float] = Field(0.20, description="Minimum 3-year revenue growth")
    earnings_growth_3y: Optional[float] = Field(0.25, description="Minimum 3-year earnings growth")
    roe_min: Optional[float] = Field(0.15, description="Minimum ROE")
    debt_to_equity_max: Optional[float] = Field(0.5, description="Maximum debt to equity ratio")
    peg_ratio_max: Optional[float] = Field(2.0, description="Maximum PEG ratio")
    market_cap_min: Optional[float] = Field(1000000000, description="Minimum market cap")


class OptionsAnalysisRequest(BaseModel):
    """Request model for options strategy analysis"""
    strategy: str = Field(..., description="Options strategy type (covered_call, protective_put)")
    stock_price: float = Field(..., gt=0, description="Current stock price")
    strike_price: Optional[float] = Field(None, gt=0, description="Strike price")
    premium: Optional[float] = Field(None, gt=0, description="Option premium")
    days_to_expiration: Optional[int] = Field(None, gt=0, description="Days to expiration")


# Initialize service
strategies_service = AdvancedStrategiesService()


@router.get("/risk-disclosure", response_model=Dict[str, Any])
async def get_risk_disclosure():
    """
    Get comprehensive risk disclosure for advanced strategies.
    
    **WARNING:** These are high-risk investment strategies that can result in significant losses.
    Users must acknowledge risks before accessing any strategy features.
    """
    return strategies_service.get_risk_disclosure()


@router.post("/acknowledge-risks", response_model=Dict[str, Any])
async def acknowledge_risks(
    request: RiskAcknowledgmentRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Acknowledge risks for a specific strategy.
    
    Requires user to:
    1. Pass educational quiz with minimum score
    2. Provide explicit risk acknowledgment text
    3. Confirm they understand potential for total loss
    """
    try:
        strategy_type = StrategyType(request.strategy_type)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid strategy type: {request.strategy_type}"
        )
    
    result = strategies_service.acknowledge_risks(
        user_id=str(current_user.id),
        strategy_type=strategy_type,
        quiz_score=request.quiz_score
    )
    
    if not result["acknowledged"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["reason"]
        )
    
    return {
        "message": "Risk acknowledgment recorded successfully",
        "details": result,
        "warning": "Remember: Only invest money you can afford to lose completely"
    }


@router.get("/strategies/{strategy_type}", response_model=Dict[str, Any])
async def get_strategy_analysis(
    strategy_type: str,
    current_user: User = Depends(get_current_active_user),
    include_metrics: bool = Query(True, description="Include performance metrics"),
    include_education: bool = Query(True, description="Include educational content")
):
    """
    Get comprehensive analysis for a specific strategy.
    
    **Requires risk acknowledgment** - Users must acknowledge risks before accessing strategy details.
    """
    try:
        strategy_enum = StrategyType(strategy_type)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid strategy type: {strategy_type}"
        )
    
    # Check if user has acknowledged risks
    if not strategies_service.require_risk_acknowledgment(str(current_user.id), strategy_enum):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Risk acknowledgment required. Please acknowledge risks first."
        )
    
    analysis = strategies_service.get_strategy_analysis(strategy_enum)
    
    # Filter response based on query parameters
    if not include_metrics:
        analysis.pop('metrics', None)
    if not include_education:
        analysis.pop('educational_content', None)
    
    return {
        **analysis,
        "access_warning": "HIGH RISK: This strategy can result in significant losses",
        "user_acknowledged_risks": True
    }


@router.post("/portfolio/stress-test", response_model=Dict[str, Any])
async def portfolio_stress_test(
    request: PortfolioStressTestRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Perform stress test on portfolio using historical crisis scenarios.
    
    Simulates portfolio performance during major market downturns to assess risk.
    """
    result = strategies_service.portfolio_stress_test(
        portfolio_positions=request.positions,
        scenario=request.scenario
    )
    
    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )
    
    return {
        **result,
        "disclaimer": "Stress test results are simulations based on historical data and may not predict future performance",
        "recommendation": "Consider adjusting portfolio allocation based on stress test results"
    }


@router.post("/position-sizing", response_model=Dict[str, Any])
async def calculate_position_sizing(
    request: PositionSizingRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Calculate optimal position sizing using Kelly Criterion and risk management principles.
    
    **Important:** Position sizing recommendations include safety factors for high-risk strategies.
    """
    try:
        strategy_enum = StrategyType(request.strategy_type)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid strategy type: {request.strategy_type}"
        )
    
    # Check risk acknowledgment for high-risk strategies
    if strategy_enum in [StrategyType.OPTIONS_TRADING, StrategyType.LEVERAGED_ETF, StrategyType.CRYPTOCURRENCY]:
        if not strategies_service.require_risk_acknowledgment(str(current_user.id), strategy_enum):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Risk acknowledgment required for this high-risk strategy"
            )
    
    result = strategies_service.calculate_optimal_position_size(
        strategy_type=strategy_enum,
        portfolio_value=request.portfolio_value,
        historical_performance=request.historical_performance
    )
    
    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )
    
    return {
        **result,
        "warning": "Position sizing is a recommendation only. Consider your personal risk tolerance and financial situation",
        "safety_note": "Recommendations include safety factors to limit potential losses"
    }


@router.get("/thematic-opportunities", response_model=Dict[str, Any])
async def get_thematic_opportunities(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current thematic investment opportunities (AI, clean energy, biotech, etc.).
    
    High-growth themes with significant risk and reward potential.
    """
    opportunities = strategies_service.get_thematic_investment_opportunities()
    
    return {
        **opportunities,
        "risk_warning": "Thematic investments are concentrated bets on specific trends and carry high risk",
        "allocation_limit": "Limit thematic investments to 5-10% of total portfolio"
    }


@router.post("/growth-stocks/screen", response_model=Dict[str, Any])
async def screen_growth_stocks(
    request: GrowthStockScreenRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Screen for growth stocks based on fundamental criteria.
    
    **Note:** This is a screening tool only. Conduct thorough research before investing.
    """
    # Check if user has acknowledged growth stock risks
    strategy_enum = StrategyType.GROWTH_STOCKS
    if not strategies_service.require_risk_acknowledgment(str(current_user.id), strategy_enum):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please acknowledge growth stock risks before using screening tool"
        )
    
    growth_strategy = strategies_service.strategies[StrategyType.GROWTH_STOCKS]
    criteria = request.dict(exclude_none=True)
    
    results = growth_strategy.growth_stock_screener(criteria)
    
    return {
        **results,
        "disclaimer": "Screening results are for educational purposes only. Not investment advice.",
        "next_steps": [
            "Research each company thoroughly",
            "Analyze competitive position", 
            "Review recent earnings and guidance",
            "Consider valuation relative to growth prospects",
            "Diversify across multiple growth stocks"
        ]
    }


@router.post("/options/analyze", response_model=Dict[str, Any])
async def analyze_options_strategy(
    request: OptionsAnalysisRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Analyze options trading strategies (covered calls, protective puts).
    
    **EXTREME RISK WARNING:** Options trading can result in total loss of premium or unlimited losses.
    """
    # Check options trading risk acknowledgment
    strategy_enum = StrategyType.OPTIONS_TRADING
    if not strategies_service.require_risk_acknowledgment(str(current_user.id), strategy_enum):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Options trading requires explicit risk acknowledgment. This strategy involves extreme risk."
        )
    
    options_strategy = strategies_service.strategies[StrategyType.OPTIONS_TRADING]
    
    if request.strategy == "covered_call":
        if not all([request.strike_price, request.premium, request.days_to_expiration]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Covered call analysis requires strike_price, premium, and days_to_expiration"
            )
        
        analysis = options_strategy.covered_call_analysis(
            stock_price=request.stock_price,
            strike_price=request.strike_price,
            premium=request.premium,
            days_to_expiration=request.days_to_expiration
        )
        
    elif request.strategy == "protective_put":
        if not all([request.strike_price, request.premium]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Protective put analysis requires strike_price and premium"
            )
        
        analysis = options_strategy.protective_put_analysis(
            stock_price=request.stock_price,
            put_strike=request.strike_price,
            put_premium=request.premium
        )
        
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Supported strategies: covered_call, protective_put"
        )
    
    return {
        **analysis,
        "RISK_WARNING": "Options trading involves extreme risk. You can lose 100% of premium paid or face unlimited losses.",
        "education_required": "Ensure you understand Greeks, time decay, and assignment risks before trading options",
        "position_sizing": "Never risk more than 1-2% of portfolio on any single options trade"
    }


@router.get("/leveraged-etf/decay-analysis", response_model=Dict[str, Any])
async def leveraged_etf_decay_analysis(
    daily_returns: List[float] = Body(..., description="List of daily returns"),
    leverage: float = Body(2.0, description="Leverage multiplier"),
    current_user: User = Depends(get_current_active_user)
):
    """
    Analyze volatility decay for leveraged ETF strategies.
    
    **WARNING:** Leveraged ETFs can lose 80-100% even if underlying index rises due to volatility decay.
    """
    # Check leveraged ETF risk acknowledgment
    strategy_enum = StrategyType.LEVERAGED_ETF
    if not strategies_service.require_risk_acknowledgment(str(current_user.id), strategy_enum):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Leveraged ETF analysis requires risk acknowledgment. These instruments have extreme volatility decay risk."
        )
    
    if not daily_returns or len(daily_returns) < 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Minimum 5 daily returns required for decay analysis"
        )
    
    leveraged_strategy = strategies_service.strategies[StrategyType.LEVERAGED_ETF]
    analysis = leveraged_strategy.volatility_decay_analysis(daily_returns, leverage)
    
    return {
        **analysis,
        "EXTREME_RISK_WARNING": "Leveraged ETFs are SHORT-TERM instruments only. Holding periods longer than days to weeks can result in severe losses even if underlying performs well.",
        "key_insight": f"Volatility decay of {analysis.get('decay_percentage', 0):.1f}% shows the cost of daily rebalancing",
        "trading_recommendation": "Use only for short-term directional bets with strict stop-losses"
    }


@router.get("/risk-management/scenarios", response_model=Dict[str, Any])
async def get_stress_test_scenarios():
    """
    Get available historical stress test scenarios for portfolio analysis.
    
    These scenarios help assess how portfolios might perform during major market crises.
    """
    scenarios = strategies_service.risk_management.stress_test_scenarios()
    
    return {
        "available_scenarios": scenarios,
        "usage_note": "Use these scenarios to stress test your portfolio and adjust risk accordingly",
        "recommendation": "Test your portfolio against multiple scenarios, especially the most recent ones"
    }


@router.get("/strategies", response_model=Dict[str, Any])
async def list_available_strategies(
    risk_level: Optional[str] = Query(None, description="Filter by risk level"),
    current_user: User = Depends(get_current_active_user)
):
    """
    List all available advanced investment strategies with risk levels.
    
    **Note:** Access to individual strategies requires separate risk acknowledgment.
    """
    strategies = []
    
    for strategy_type, strategy_obj in strategies_service.strategies.items():
        strategy_info = {
            "type": strategy_type.value,
            "name": strategy_obj.name,
            "risk_level": strategy_obj.risk_level.value,
            "description": f"Advanced {strategy_obj.name.lower()} strategy",
            "risk_acknowledged": strategies_service.require_risk_acknowledgment(
                str(current_user.id), strategy_type
            )
        }
        
        # Filter by risk level if specified
        if risk_level and strategy_obj.risk_level.value != risk_level:
            continue
            
        strategies.append(strategy_info)
    
    return {
        "strategies": strategies,
        "risk_levels": [level.value for level in RiskLevel],
        "warning": "All advanced strategies involve significant risk of loss",
        "requirement": "Risk acknowledgment required before accessing strategy details"
    }


@router.post("/paper-trading/enable", response_model=Dict[str, Any])
async def enable_paper_trading(
    strategy_type: str = Body(..., description="Strategy to enable paper trading for"),
    current_user: User = Depends(get_current_active_user)
):
    """
    Enable paper trading mode for a strategy (simulation only, no real money).
    
    **Recommended:** Practice with paper trading before risking real capital.
    """
    try:
        strategy_enum = StrategyType(strategy_type)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid strategy type: {strategy_type}"
        )
    
    # Paper trading doesn't require full risk acknowledgment but user should see warnings
    return {
        "paper_trading_enabled": True,
        "strategy": strategy_type,
        "benefits": [
            "Practice strategy without financial risk",
            "Learn mechanics and timing",
            "Build confidence before real trading",
            "Test different position sizes"
        ],
        "next_step": "Start with small simulated positions and track performance",
        "transition_note": "Only move to live trading after consistent paper trading success"
    }