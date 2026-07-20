"""API endpoints for AI narrative generation."""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from datetime import datetime

from .narrative_generator import NarrativeGenerator
from .template_manager import TemplateType
from .config import Language, LLMProvider
from ..api.deps import get_current_user
from ..models.user import User


# Initialize router
router = APIRouter(prefix="/ai", tags=["AI Narratives"])

# Initialize narrative generator (singleton)
narrative_generator = NarrativeGenerator()


# Request/Response models
class NarrativeRequest(BaseModel):
    """Request model for narrative generation."""
    template_type: TemplateType = Field(..., description="Type of narrative template")
    data: Dict[str, Any] = Field(..., description="Data for template variables")
    language: Language = Field(Language.ENGLISH, description="Target language")
    provider: Optional[LLMProvider] = Field(None, description="Specific LLM provider")


class BatchNarrativeRequest(BaseModel):
    """Request model for batch narrative generation."""
    requests: List[NarrativeRequest] = Field(..., description="List of narrative requests")


class NarrativeResponse(BaseModel):
    """Response model for generated narrative."""
    narrative: str = Field(..., description="Generated narrative text")
    template_type: str = Field(..., description="Template type used")
    language: str = Field(..., description="Language of narrative")
    provider: str = Field(..., description="LLM provider used")
    tokens_used: int = Field(..., description="Number of tokens consumed")
    generation_time_ms: float = Field(..., description="Generation time in milliseconds")
    timestamp: str = Field(..., description="Generation timestamp")
    fallback: bool = Field(False, description="Whether fallback was used")


class SimulationNarrativeRequest(BaseModel):
    """Request for comprehensive simulation narratives."""
    simulation_id: str = Field(..., description="Simulation ID")
    include_baseline: bool = Field(True, description="Include baseline summary")
    include_scenarios: bool = Field(True, description="Include scenario comparisons")
    include_risks: bool = Field(True, description="Include risk assessment")
    include_recommendations: bool = Field(True, description="Include action recommendations")
    language: Language = Field(Language.ENGLISH, description="Target language")


# API Endpoints
@router.post("/generate", response_model=NarrativeResponse)
async def generate_narrative(
    request: NarrativeRequest,
    current_user: User = Depends(get_current_user)
) -> NarrativeResponse:
    """Generate a single AI narrative.
    
    Args:
        request: Narrative generation request
        current_user: Authenticated user
        
    Returns:
        Generated narrative response
    """
    try:
        result = await narrative_generator.generate_narrative(
            template_type=request.template_type,
            data=request.data,
            user_id=str(current_user.id),
            language=request.language,
            provider=request.provider
        )
        
        return NarrativeResponse(**result)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to generate narrative")


@router.post("/generate-batch", response_model=List[NarrativeResponse])
async def generate_batch_narratives(
    request: BatchNarrativeRequest,
    current_user: User = Depends(get_current_user)
) -> List[NarrativeResponse]:
    """Generate multiple narratives in batch.
    
    Args:
        request: Batch narrative request
        current_user: Authenticated user
        
    Returns:
        List of generated narratives
    """
    try:
        # Convert requests to dict format
        batch_requests = [
            {
                "template_type": req.template_type.value,
                "data": req.data,
                "language": req.language.value,
                "provider": req.provider.value if req.provider else None
            }
            for req in request.requests
        ]
        
        results = await narrative_generator.generate_batch_narratives(
            batch_requests,
            user_id=str(current_user.id)
        )
        
        return [NarrativeResponse(**result) for result in results]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to generate batch narratives")


@router.post("/simulation-narratives")
async def generate_simulation_narratives(
    request: SimulationNarrativeRequest,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Generate comprehensive narratives for a simulation.
    
    Args:
        request: Simulation narrative request
        current_user: Authenticated user
        
    Returns:
        Dictionary of generated narratives
    """
    # This would integrate with the simulation engine to get data
    # For now, returning a structured response
    narratives = {}
    
    # Mock simulation data (would be retrieved from database)
    simulation_data = {
        "initial_portfolio": 100000,
        "current_age": 35,
        "final_portfolio": 850000,
        "retirement_age": 65,
        "avg_return": 7.2,
        "success_rate": 85,
        "monthly_savings": 1500,
        "years_to_retirement": 30,
        "risk_level": "Moderate",
        "inflation_rate": 2.5,
        "num_goals": 3,
        "stock_allocation": 60,
        "bond_allocation": 30,
        "cash_allocation": 10
    }
    
    try:
        # Generate baseline summary
        if request.include_baseline:
            baseline_result = await narrative_generator.generate_narrative(
                template_type=TemplateType.BASELINE_SUMMARY,
                data=simulation_data,
                user_id=str(current_user.id),
                language=request.language
            )
            narratives["baseline"] = baseline_result
        
        # Generate scenario comparison
        if request.include_scenarios:
            scenario_data = {
                **simulation_data,
                "scenario_a_name": "Conservative Growth",
                "scenario_a_final": 750000,
                "scenario_a_success": 90,
                "scenario_a_monthly": 1200,
                "scenario_a_risk": "Low",
                "scenario_b_name": "Aggressive Growth",
                "scenario_b_final": 950000,
                "scenario_b_success": 75,
                "scenario_b_monthly": 1800,
                "scenario_b_risk": "High",
                "portfolio_difference": 200000,
                "portfolio_diff_pct": 26.7,
                "success_diff": -15,
                "monthly_diff": 600,
                "recommendation_text": "Consider your risk tolerance carefully"
            }
            
            scenario_result = await narrative_generator.generate_narrative(
                template_type=TemplateType.SCENARIO_COMPARISON,
                data=scenario_data,
                user_id=str(current_user.id),
                language=request.language
            )
            narratives["scenarios"] = scenario_result
        
        # Generate risk assessment
        if request.include_risks:
            risk_data = {
                "risk_profile": "Moderate",
                "volatility": 12.5,
                "max_drawdown": 25.0,
                "var_95": 125000,
                "crash_value": 70000,
                "recession_impact": 15.0,
                "recovery_months": 18,
                "strategy_1": "Diversify across asset classes",
                "strategy_2": "Maintain emergency fund",
                "strategy_3": "Rebalance quarterly",
                "risk_alignment": "well-aligned"
            }
            
            risk_result = await narrative_generator.generate_narrative(
                template_type=TemplateType.RISK_ASSESSMENT,
                data=risk_data,
                user_id=str(current_user.id),
                language=request.language
            )
            narratives["risk_assessment"] = risk_result
        
        # Generate recommendations
        if request.include_recommendations:
            recommendation_data = {
                "action_1_title": "Increase Monthly Contributions",
                "action_1_impact": "High",
                "action_1_timeline": "Immediate",
                "action_1_benefit": 50000,
                "action_2_title": "Optimize Tax-Advantaged Accounts",
                "action_2_impact": "Medium",
                "action_2_timeline": "Next quarter",
                "action_2_benefit": 30000,
                "action_3_title": "Review Asset Allocation",
                "action_3_impact": "Medium",
                "action_3_timeline": "Annual",
                "action_3_benefit": 20000,
                "next_step_1": "Schedule consultation with advisor",
                "next_step_2": "Set up automatic investment increases",
                "review_timeline": "3 months",
                "total_improvement": 10
            }
            
            recommendation_result = await narrative_generator.generate_narrative(
                template_type=TemplateType.ACTION_RECOMMENDATION,
                data=recommendation_data,
                user_id=str(current_user.id),
                language=request.language
            )
            narratives["recommendations"] = recommendation_result
        
        return {
            "simulation_id": request.simulation_id,
            "narratives": narratives,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to generate simulation narratives")


@router.get("/templates")
async def list_templates(
    current_user: User = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """List available narrative templates.
    
    Args:
        current_user: Authenticated user
        
    Returns:
        List of template information
    """
    return narrative_generator.template_manager.list_available_templates()


@router.get("/statistics")
async def get_statistics(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get AI system statistics.
    
    Args:
        current_user: Authenticated user (must be admin)
        
    Returns:
        System statistics
    """
    # Check if user is admin (implement proper check)
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    stats = narrative_generator.audit_logger.get_statistics()
    
    # Add A/B test results if enabled
    if narrative_generator.config.enable_ab_testing:
        ab_results = await narrative_generator.get_ab_test_results()
        stats["ab_testing"] = ab_results
    
    return stats


@router.get("/audit-logs")
async def search_audit_logs(
    start_date: datetime,
    end_date: datetime,
    event_type: Optional[str] = None,
    user_id: Optional[str] = None,
    current_user: User = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """Search audit logs.
    
    Args:
        start_date: Start of search period
        end_date: End of search period
        event_type: Filter by event type
        user_id: Filter by user
        current_user: Authenticated user (must be admin)
        
    Returns:
        List of audit events
    """
    # Check if user is admin
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    logs = await narrative_generator.audit_logger.search_logs(
        start_date=start_date,
        end_date=end_date,
        event_type=event_type,
        user_id=user_id
    )
    
    return logs


@router.post("/validate-prompt")
async def validate_prompt(
    prompt: str,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Validate a prompt for safety.
    
    Args:
        prompt: Prompt to validate
        current_user: Authenticated user
        
    Returns:
        Validation result
    """
    is_valid, error = narrative_generator.safety_controller.validate_prompt(prompt)
    
    return {
        "is_valid": is_valid,
        "error": error,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/safety-report")
async def get_safety_report(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get safety violation report.
    
    Args:
        start_date: Start of reporting period
        end_date: End of reporting period
        current_user: Authenticated user (must be admin)
        
    Returns:
        Safety violation report
    """
    # Check if user is admin
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    report = narrative_generator.safety_controller.get_violation_report(
        start_date=start_date,
        end_date=end_date
    )
    
    return report