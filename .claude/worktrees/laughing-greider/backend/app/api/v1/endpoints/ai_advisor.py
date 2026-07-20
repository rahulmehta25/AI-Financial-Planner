"""
AI Financial Advisor API Endpoints
Provides REST API for AI-driven financial advice and conversation management
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
import json
import asyncio

from fastapi import APIRouter, HTTPException, Depends, Query, Body, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field, validator

from app.database.base import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.services.ai.financial_advisor_ai import (
    PersonalizedFinancialAdvisor,
    UserContext,
    MarketContext,
    PersonalizedAdvice,
    TaskType
)
from app.services.ai.conversation_manager import (
    ConversationManager,
    ConversationSession,
    ConversationState
)
from app.services.ai.templates.financial_advice_prompts import (
    FinancialAdvicePrompts,
    AdviceCategory
)
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai-advisor", tags=["AI Financial Advisor"])

# Initialize services
advisor_config = {
    'anthropic_api_key': settings.ANTHROPIC_API_KEY,
    'openai_api_key': settings.OPENAI_API_KEY,
    'redis_url': settings.REDIS_URL,
    'compliance_level': settings.COMPLIANCE_LEVEL,
    'max_requests_per_minute': 60,
    'cache_ttl': 3600,
    'use_cache': True,
    'vector_store_path': './data/vector_store'
}

financial_advisor = PersonalizedFinancialAdvisor(config=advisor_config)
conversation_manager = ConversationManager(config=advisor_config)
prompt_manager = FinancialAdvicePrompts()

# Request/Response Models
class AdviceRequest(BaseModel):
    """Request model for financial advice"""
    query: str = Field(..., min_length=10, max_length=2000, description="User's question or request")
    category: Optional[str] = Field(None, description="Category of advice needed")
    include_visualizations: bool = Field(True, description="Include charts and graphs")
    risk_tolerance: Optional[str] = Field(None, description="Override user's default risk tolerance")
    time_horizon: Optional[int] = Field(None, description="Investment time horizon in years")
    additional_context: Optional[Dict[str, Any]] = Field(None, description="Additional context")

class ConversationMessage(BaseModel):
    """Message in a conversation"""
    message: str = Field(..., min_length=1, max_length=2000)
    session_id: Optional[str] = Field(None, description="Existing session ID or None for new session")
    
class ConversationEndRequest(BaseModel):
    """Request to end a conversation"""
    session_id: str = Field(..., description="Session ID to end")
    satisfaction_score: Optional[float] = Field(None, ge=0, le=5, description="Satisfaction rating")
    feedback: Optional[str] = Field(None, max_length=500, description="User feedback")

class AdviceResponse(BaseModel):
    """Response containing personalized financial advice"""
    advice: str
    key_points: List[str]
    action_items: List[Dict[str, Any]]
    confidence_score: float
    disclaimers: List[str]
    visualizations: Optional[List[Dict[str, Any]]] = None
    sources: List[str]
    session_id: Optional[str] = None
    
class ConversationResponse(BaseModel):
    """Response from conversation endpoint"""
    session_id: str
    response: str
    state: str
    suggestions: List[str]
    action_items: List[Dict[str, Any]]
    turn_number: int
    max_turns: int
    confidence: float

# API Endpoints
@router.post("/advice", response_model=AdviceResponse)
async def get_financial_advice(
    request: AdviceRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> AdviceResponse:
    """
    Generate personalized financial advice based on user query and context
    """
    try:
        logger.info(f"Generating advice for user {current_user.id}: {request.query[:50]}...")
        
        # Build user context
        user_context = await _build_user_context(current_user, db, request)
        
        # Get market context
        market_context = await _get_market_context()
        
        # Generate personalized advice
        advice = await financial_advisor.generate_personalized_advice(
            user_query=request.query,
            user_context=user_context,
            market_context=market_context
        )
        
        # Format visualizations if requested
        visualizations = None
        if request.include_visualizations:
            visualizations = await _generate_visualizations(advice, user_context)
        
        # Format response
        response = AdviceResponse(
            advice=advice.narrative,
            key_points=advice.key_points,
            action_items=[
                {
                    'title': item.title,
                    'description': item.description,
                    'priority': item.priority,
                    'impact': item.impact,
                    'timeline': item.timeline
                }
                for item in advice.action_plan.items
            ],
            confidence_score=advice.confidence_score,
            disclaimers=advice.disclaimers,
            visualizations=visualizations,
            sources=advice.sources
        )
        
        # Log successful generation
        await _log_advice_generation(current_user.id, request.query, advice)
        
        return response
    
    except Exception as e:
        logger.error(f"Error generating advice: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate financial advice")

@router.post("/conversation/start", response_model=ConversationResponse)
async def start_conversation(
    message: Optional[str] = Body(None, description="Optional initial message"),
    current_user: User = Depends(get_current_user)
) -> ConversationResponse:
    """
    Start a new financial advisory conversation session
    """
    try:
        # Start new session
        session = await conversation_manager.start_session(
            user_id=str(current_user.id),
            initial_message=message
        )
        
        # If initial message provided, process it
        if message:
            result = await conversation_manager.process_message(
                session_id=session.session_id,
                message=message
            )
            
            return ConversationResponse(
                session_id=session.session_id,
                response=result['response'],
                state=result['state'],
                suggestions=result.get('suggestions', []),
                action_items=result.get('action_items', []),
                turn_number=result['turn_number'],
                max_turns=result['max_turns'],
                confidence=result.get('confidence', 0.8)
            )
        else:
            # Return greeting
            return ConversationResponse(
                session_id=session.session_id,
                response="Hello! I'm your AI financial advisor. How can I help you today?",
                state=ConversationState.GREETING.value,
                suggestions=[
                    "Review my portfolio",
                    "Help with retirement planning",
                    "Tax optimization strategies",
                    "Investment recommendations"
                ],
                action_items=[],
                turn_number=0,
                max_turns=conversation_manager.max_turns,
                confidence=1.0
            )
    
    except Exception as e:
        logger.error(f"Error starting conversation: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to start conversation")

@router.post("/conversation/message", response_model=ConversationResponse)
async def send_message(
    request: ConversationMessage,
    current_user: User = Depends(get_current_user)
) -> ConversationResponse:
    """
    Send a message in an existing conversation or start a new one
    """
    try:
        # If no session ID, start new session
        if not request.session_id:
            session = await conversation_manager.start_session(
                user_id=str(current_user.id)
            )
            session_id = session.session_id
        else:
            session_id = request.session_id
        
        # Process message
        result = await conversation_manager.process_message(
            session_id=session_id,
            message=request.message
        )
        
        # Check for errors
        if 'error' in result:
            raise HTTPException(status_code=400, detail=result['error'])
        
        return ConversationResponse(
            session_id=session_id,
            response=result['response'],
            state=result['state'],
            suggestions=result.get('suggestions', []),
            action_items=result.get('action_items', []),
            turn_number=result['turn_number'],
            max_turns=result['max_turns'],
            confidence=result.get('confidence', 0.8)
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process message")

@router.post("/conversation/end")
async def end_conversation(
    request: ConversationEndRequest,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    End a conversation session and get summary
    """
    try:
        result = await conversation_manager.end_session(
            session_id=request.session_id,
            satisfaction_score=request.satisfaction_score
        )
        
        # Store feedback if provided
        if request.feedback:
            await _store_feedback(
                user_id=current_user.id,
                session_id=request.session_id,
                feedback=request.feedback,
                satisfaction_score=request.satisfaction_score
            )
        
        return result
    
    except Exception as e:
        logger.error(f"Error ending conversation: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to end conversation")

@router.get("/conversation/history")
async def get_conversation_history(
    days: int = Query(30, ge=1, le=365, description="Number of days of history"),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get user's conversation history and analytics
    """
    try:
        analytics = await conversation_manager.get_conversation_analytics(
            user_id=str(current_user.id),
            days=days
        )
        
        return analytics
    
    except Exception as e:
        logger.error(f"Error getting conversation history: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve conversation history")

@router.get("/templates/{category}")
async def get_advice_template(
    category: str,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get available advice templates for a category
    """
    try:
        # Convert string to category enum
        try:
            advice_category = AdviceCategory(category)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid category: {category}")
        
        # Get template
        template = prompt_manager.templates.get(advice_category)
        if not template:
            raise HTTPException(status_code=404, detail=f"No template found for category: {category}")
        
        return {
            'category': category,
            'name': template.name,
            'required_context': template.required_context,
            'compliance_level': template.compliance_level,
            'disclaimers': template.disclaimers,
            'examples': template.examples
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting template: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve template")

@router.get("/templates")
async def list_advice_templates(
    current_user: User = Depends(get_current_user)
) -> List[Dict[str, str]]:
    """
    List all available advice template categories
    """
    try:
        categories = [
            {
                'value': cat.value,
                'name': cat.name.replace('_', ' ').title(),
                'description': f"Templates for {cat.value.replace('_', ' ')}"
            }
            for cat in AdviceCategory
        ]
        
        return categories
    
    except Exception as e:
        logger.error(f"Error listing templates: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to list templates")

@router.post("/feedback")
async def submit_feedback(
    session_id: str = Body(..., description="Session ID"),
    rating: float = Body(..., ge=1, le=5, description="Rating 1-5"),
    feedback: Optional[str] = Body(None, description="Text feedback"),
    current_user: User = Depends(get_current_user)
) -> Dict[str, str]:
    """
    Submit feedback for an AI interaction
    """
    try:
        await _store_feedback(
            user_id=current_user.id,
            session_id=session_id,
            feedback=feedback,
            satisfaction_score=rating
        )
        
        return {"status": "Feedback received successfully"}
    
    except Exception as e:
        logger.error(f"Error storing feedback: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to store feedback")

# Helper Functions
async def _build_user_context(
    user: User,
    db: AsyncSession,
    request: AdviceRequest
) -> UserContext:
    """Build comprehensive user context for advice generation"""
    
    # Get user profile data
    profile = {
        'user_id': str(user.id),
        'age': user.profile.get('age', 35) if hasattr(user, 'profile') else 35,
        'risk_tolerance': request.risk_tolerance or user.profile.get('risk_tolerance', 'moderate'),
        'state': user.profile.get('state', 'CA'),
        'tax_bracket': user.profile.get('tax_bracket', 0.24),
        'employment_status': user.profile.get('employment_status', 'employed'),
        'financial_literacy': user.profile.get('financial_literacy', 'intermediate')
    }
    
    # Get portfolio analysis (simplified for demo)
    portfolio_analysis = {
        'total_value': 250000,
        'allocation': {
            'stocks': 0.60,
            'bonds': 0.30,
            'cash': 0.10
        },
        'ytd_return': 0.08,
        'risk_score': 65
    }
    
    # Get goal progress (simplified for demo)
    goal_progress = [
        {
            'name': 'Retirement',
            'target_amount': 2000000,
            'current_amount': 250000,
            'target_date': '2055-01-01',
            'progress': 0.125
        }
    ]
    
    # Add any additional context from request
    if request.additional_context:
        profile.update(request.additional_context)
    
    return UserContext(
        user_id=str(user.id),
        profile=profile,
        portfolio_analysis=portfolio_analysis,
        goal_progress=goal_progress
    )

async def _get_market_context() -> MarketContext:
    """Get current market context"""
    
    # In production, this would fetch real market data
    return MarketContext(
        current_market_conditions="moderate_growth",
        volatility_regime="normal",
        economic_outlook="cautiously_optimistic"
    )

async def _generate_visualizations(
    advice: PersonalizedAdvice,
    context: UserContext
) -> List[Dict[str, Any]]:
    """Generate visualization data for the advice"""
    
    visualizations = []
    
    # Portfolio allocation chart
    if context.portfolio_analysis:
        visualizations.append({
            'type': 'pie_chart',
            'title': 'Current Portfolio Allocation',
            'data': context.portfolio_analysis.get('allocation', {})
        })
    
    # Goal progress chart
    if context.goal_progress:
        visualizations.append({
            'type': 'progress_bar',
            'title': 'Financial Goals Progress',
            'data': [
                {
                    'name': goal['name'],
                    'progress': goal['progress'] * 100,
                    'target': goal['target_amount']
                }
                for goal in context.goal_progress
            ]
        })
    
    # Action items priority matrix
    if advice.action_plan.items:
        visualizations.append({
            'type': 'priority_matrix',
            'title': 'Action Items by Impact and Priority',
            'data': [
                {
                    'title': item.title,
                    'impact': item.impact,
                    'priority': item.priority
                }
                for item in advice.action_plan.items
            ]
        })
    
    return visualizations

async def _log_advice_generation(
    user_id: int,
    query: str,
    advice: PersonalizedAdvice
):
    """Log advice generation for analytics and compliance"""
    
    try:
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'user_id': str(user_id),
            'query': query[:200],  # Truncate for privacy
            'confidence_score': advice.confidence_score,
            'action_items_count': len(advice.action_plan.items),
            'disclaimers_included': len(advice.disclaimers) > 0
        }
        
        # In production, this would be stored in a proper logging system
        logger.info(f"Advice generated: {json.dumps(log_entry)}")
    
    except Exception as e:
        logger.error(f"Failed to log advice generation: {e}")

async def _store_feedback(
    user_id: int,
    session_id: str,
    feedback: Optional[str],
    satisfaction_score: Optional[float]
):
    """Store user feedback for continuous improvement"""
    
    try:
        feedback_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'user_id': str(user_id),
            'session_id': session_id,
            'satisfaction_score': satisfaction_score,
            'feedback': feedback
        }
        
        # In production, this would be stored in database
        logger.info(f"Feedback stored: {json.dumps(feedback_entry)}")
    
    except Exception as e:
        logger.error(f"Failed to store feedback: {e}")