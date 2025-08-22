"""
API endpoints for ML-powered recommendations.
"""

import logging
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.ml.recommendations.recommendation_engine import RecommendationEngine
from app.ml.recommendations.model_monitor import ModelMonitor

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize ML components
recommendation_engine = RecommendationEngine()
model_monitor = ModelMonitor()


@router.get("/recommendations/{user_id}")
async def get_comprehensive_recommendations(
    user_id: str,
    categories: Optional[List[str]] = Query(None, description="Specific recommendation categories to include"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive ML-powered recommendations for a user.
    
    Available categories:
    - goal_optimization: Optimize financial goals
    - portfolio_rebalancing: Balance investment portfolio  
    - risk_assessment: Understand true risk tolerance
    - behavioral_insights: Improve financial habits
    - peer_insights: Learn from similar users
    - savings_strategy: Optimize savings approach
    - life_planning: Prepare for major life events
    """
    try:
        # Verify user access (users can only access their own recommendations)
        if str(current_user.id) != user_id and not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Verify target user exists
        target_user = db.query(User).filter(User.id == user_id).first()
        if not target_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        if not target_user.financial_profile:
            raise HTTPException(
                status_code=400, 
                detail="User must complete financial profile before getting recommendations"
            )
        
        # Generate recommendations
        recommendations = await recommendation_engine.generate_comprehensive_recommendations(
            user_id=user_id,
            categories=categories
        )
        
        if "error" in recommendations:
            raise HTTPException(status_code=500, detail=recommendations["error"])
        
        return recommendations
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get recommendations for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate recommendations")


@router.get("/recommendations/{user_id}/goal-optimization")
async def get_goal_optimization_recommendations(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get goal optimization recommendations using XGBoost."""
    try:
        if str(current_user.id) != user_id and not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="Access denied")
        
        target_user = db.query(User).filter(User.id == user_id).first()
        if not target_user or not target_user.financial_profile:
            raise HTTPException(status_code=404, detail="User or financial profile not found")
        
        recommendations = recommendation_engine.goal_optimizer.optimize_goals(user_id)
        
        if "error" in recommendations:
            raise HTTPException(status_code=500, detail=recommendations["error"])
        
        return recommendations
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get goal optimization for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate goal recommendations")


@router.get("/recommendations/{user_id}/portfolio-rebalancing")
async def get_portfolio_rebalancing_recommendations(
    user_id: str,
    portfolio_value: float = Query(100000, description="Current portfolio value"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get portfolio rebalancing recommendations."""
    try:
        if str(current_user.id) != user_id and not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="Access denied")
        
        target_user = db.query(User).filter(User.id == user_id).first()
        if not target_user or not target_user.financial_profile:
            raise HTTPException(status_code=404, detail="User or financial profile not found")
        
        recommendations = recommendation_engine.portfolio_rebalancer.generate_rebalancing_plan(
            user_id, portfolio_value
        )
        
        if "error" in recommendations:
            raise HTTPException(status_code=500, detail=recommendations["error"])
        
        return recommendations
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get portfolio recommendations for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate portfolio recommendations")


@router.get("/recommendations/{user_id}/risk-assessment")
async def get_risk_assessment(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get risk tolerance prediction and capacity analysis."""
    try:
        if str(current_user.id) != user_id and not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="Access denied")
        
        target_user = db.query(User).filter(User.id == user_id).first()
        if not target_user or not target_user.financial_profile:
            raise HTTPException(status_code=404, detail="User or financial profile not found")
        
        # Get risk tolerance prediction
        risk_prediction = recommendation_engine.risk_predictor.predict_actual_risk_tolerance(user_id)
        
        # Get risk capacity analysis
        capacity_analysis = recommendation_engine.risk_predictor.analyze_risk_capacity_vs_tolerance(user_id)
        
        return {
            "risk_prediction": risk_prediction,
            "capacity_analysis": capacity_analysis
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get risk assessment for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate risk assessment")


@router.get("/recommendations/{user_id}/behavioral-insights")
async def get_behavioral_insights(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get behavioral pattern analysis and spending insights."""
    try:
        if str(current_user.id) != user_id and not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="Access denied")
        
        target_user = db.query(User).filter(User.id == user_id).first()
        if not target_user or not target_user.financial_profile:
            raise HTTPException(status_code=404, detail="User or financial profile not found")
        
        # Get spending pattern analysis
        spending_analysis = recommendation_engine.behavioral_analyzer.analyze_spending_patterns(user_id)
        
        # Get future spending predictions
        spending_predictions = recommendation_engine.behavioral_analyzer.predict_future_spending(
            user_id, months_ahead=6
        )
        
        return {
            "spending_analysis": spending_analysis,
            "spending_predictions": spending_predictions
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get behavioral insights for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate behavioral insights")


@router.get("/recommendations/{user_id}/peer-insights")
async def get_peer_insights(
    user_id: str,
    n_similar: int = Query(10, description="Number of similar users to find"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get peer comparison insights and benchmarks."""
    try:
        if str(current_user.id) != user_id and not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="Access denied")
        
        target_user = db.query(User).filter(User.id == user_id).first()
        if not target_user or not target_user.financial_profile:
            raise HTTPException(status_code=404, detail="User or financial profile not found")
        
        # Find similar users
        similar_users = recommendation_engine.collaborative_filter.find_similar_users(
            user_id, n_similar=n_similar
        )
        
        # Get peer benchmarks
        peer_benchmarks = recommendation_engine.collaborative_filter.get_peer_benchmarks(user_id)
        
        return {
            "similar_users": similar_users,
            "peer_benchmarks": peer_benchmarks
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get peer insights for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate peer insights")


@router.get("/recommendations/{user_id}/savings-strategy")
async def get_savings_strategy(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get personalized savings strategy recommendations."""
    try:
        if str(current_user.id) != user_id and not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="Access denied")
        
        target_user = db.query(User).filter(User.id == user_id).first()
        if not target_user or not target_user.financial_profile:
            raise HTTPException(status_code=404, detail="User or financial profile not found")
        
        savings_strategy = recommendation_engine.savings_strategist.generate_savings_strategy(user_id)
        
        if "error" in savings_strategy:
            raise HTTPException(status_code=500, detail=savings_strategy["error"])
        
        return savings_strategy
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get savings strategy for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate savings strategy")


@router.get("/recommendations/{user_id}/life-planning")
async def get_life_event_predictions(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get life event predictions and financial planning recommendations."""
    try:
        if str(current_user.id) != user_id and not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="Access denied")
        
        target_user = db.query(User).filter(User.id == user_id).first()
        if not target_user or not target_user.financial_profile:
            raise HTTPException(status_code=404, detail="User or financial profile not found")
        
        life_predictions = recommendation_engine.life_event_predictor.predict_life_events(user_id)
        
        if "error" in life_predictions:
            raise HTTPException(status_code=500, detail=life_predictions["error"])
        
        return life_predictions
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get life planning for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate life event predictions")


@router.get("/recommendations/{user_id}/goal-success-probability")
async def get_goal_success_probability(
    user_id: str,
    goal_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get probability of achieving a specific goal."""
    try:
        if str(current_user.id) != user_id and not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="Access denied")
        
        target_user = db.query(User).filter(User.id == user_id).first()
        if not target_user or not target_user.financial_profile:
            raise HTTPException(status_code=404, detail="User or financial profile not found")
        
        probability = recommendation_engine.goal_optimizer.predict_goal_success_probability(
            user_id, goal_id
        )
        
        return {
            "user_id": user_id,
            "goal_id": goal_id,
            "success_probability": probability,
            "confidence_level": "high" if probability > 0.8 else "medium" if probability > 0.5 else "low"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get goal success probability: {e}")
        raise HTTPException(status_code=500, detail="Failed to predict goal success probability")


# Admin endpoints for model management
@router.post("/admin/models/train")
async def train_all_models(
    retrain: bool = Query(False, description="Force retrain existing models"),
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Train all ML models (Admin only)."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        # Run training in background
        background_tasks.add_task(
            _train_models_background,
            retrain=retrain
        )
        
        return {
            "message": "Model training initiated",
            "retrain": retrain,
            "estimated_completion": "2-4 hours"
        }
        
    except Exception as e:
        logger.error(f"Failed to initiate model training: {e}")
        raise HTTPException(status_code=500, detail="Failed to initiate model training")


@router.get("/admin/models/status")
async def get_models_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get status of all ML models (Admin only)."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        status = recommendation_engine.get_recommendation_status()
        return status
        
    except Exception as e:
        logger.error(f"Failed to get models status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get models status")


@router.get("/admin/monitoring/dashboard")
async def get_monitoring_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get ML model monitoring dashboard data (Admin only)."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        dashboard_data = model_monitor.get_monitoring_dashboard_data()
        return dashboard_data
        
    except Exception as e:
        logger.error(f"Failed to get monitoring dashboard: {e}")
        raise HTTPException(status_code=500, detail="Failed to get monitoring dashboard")


@router.get("/admin/monitoring/report")
async def get_monitoring_report(
    model_name: Optional[str] = Query(None, description="Specific model to report on"),
    days: int = Query(30, description="Number of days to include in report"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate comprehensive monitoring report (Admin only)."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        report = model_monitor.generate_monitoring_report(
            model_name=model_name,
            days=days
        )
        return report
        
    except Exception as e:
        logger.error(f"Failed to generate monitoring report: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate monitoring report")


@router.post("/admin/models/{model_name}/retrain")
async def trigger_model_retrain(
    model_name: str,
    reason: str = Query(..., description="Reason for retraining"),
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Trigger retraining for a specific model (Admin only)."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        # Trigger retraining
        result = model_monitor.trigger_model_retraining(
            model_name=model_name,
            reason=reason
        )
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to trigger retraining for {model_name}: {e}")
        raise HTTPException(status_code=500, detail="Failed to trigger model retraining")


@router.get("/feature-importance/{model_name}")
async def get_model_feature_importance(
    model_name: str,
    model_type: str = Query("contribution", description="Type of model (contribution, timeline, priority)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get feature importance for ML models."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        if model_name == "goal_optimizer":
            feature_importance = recommendation_engine.goal_optimizer.get_feature_importance(model_type)
        else:
            raise HTTPException(status_code=400, detail=f"Feature importance not available for {model_name}")
        
        return {
            "model_name": model_name,
            "model_type": model_type,
            "feature_importance": feature_importance
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get feature importance for {model_name}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get feature importance")


async def _train_models_background(retrain: bool = False):
    """Background task for training models."""
    try:
        logger.info("Starting background model training...")
        result = recommendation_engine.train_all_models(retrain=retrain)
        logger.info(f"Background model training completed: {result}")
    except Exception as e:
        logger.error(f"Background model training failed: {e}")


# Utility endpoints
@router.get("/health")
async def health_check():
    """Health check endpoint for the ML recommendations service."""
    try:
        status = recommendation_engine.get_recommendation_status()
        
        return {
            "status": "healthy" if status.get("overall_health") == "healthy" else "degraded",
            "timestamp": status.get("timestamp"),
            "modules_healthy": sum(1 for m in status.get("modules", {}).values() 
                                 if m.get("status") == "healthy"),
            "total_modules": len(status.get("modules", {}))
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }