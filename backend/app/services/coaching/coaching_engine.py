"""
AI-Powered Financial Coaching Engine

This module provides personalized financial coaching through AI-driven insights,
behavioral analysis, and adaptive coaching strategies.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import json
import hashlib
from dataclasses import dataclass

import numpy as np
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.models.user import User
from app.models.financial_profile import FinancialProfile
from app.models.goal import Goal
from app.database.base import SessionLocal
from app.ai.llm_client import LLMClientManager, NarrativeType
from app.ai.config import AIConfig, Language
from app.ai.audit_logger import AuditLogger
from app.ml.recommendations.behavioral_analyzer import BehavioralPatternAnalyzer

logger = logging.getLogger(__name__)


class CoachingType(str, Enum):
    """Types of coaching interventions."""
    GOAL_SETTING = "goal_setting"
    BUDGET_OPTIMIZATION = "budget_optimization"
    SAVINGS_ACCELERATION = "savings_acceleration"
    DEBT_REDUCTION = "debt_reduction"
    INVESTMENT_GUIDANCE = "investment_guidance"
    RETIREMENT_PLANNING = "retirement_planning"
    EMERGENCY_FUND = "emergency_fund"
    TAX_OPTIMIZATION = "tax_optimization"
    BEHAVIORAL_CHANGE = "behavioral_change"
    CRISIS_MANAGEMENT = "crisis_management"
    HABIT_FORMATION = "habit_formation"
    FINANCIAL_LITERACY = "financial_literacy"


class CoachingTone(str, Enum):
    """Coaching communication tones."""
    SUPPORTIVE = "supportive"
    MOTIVATIONAL = "motivational"
    EDUCATIONAL = "educational"
    ANALYTICAL = "analytical"
    EMPATHETIC = "empathetic"
    DIRECT = "direct"
    CELEBRATORY = "celebratory"


class UserContext(BaseModel):
    """User context for personalized coaching."""
    user_id: str
    age: int
    income_level: float
    risk_tolerance: str
    financial_goals: List[str]
    current_savings_rate: float
    debt_to_income_ratio: float
    investment_experience: str
    life_stage: str
    recent_transactions: List[Dict]
    behavioral_patterns: Dict[str, Any]
    stress_indicators: Dict[str, float]
    engagement_level: str
    preferred_communication_style: str
    learning_preference: str


@dataclass
class CoachingSession:
    """Represents a coaching session."""
    session_id: str
    user_id: str
    coaching_type: CoachingType
    tone: CoachingTone
    message: str
    action_items: List[str]
    resources: List[Dict[str, str]]
    follow_up_date: Optional[datetime]
    metrics_to_track: List[str]
    success_criteria: Dict[str, Any]
    timestamp: datetime


class PersonalizedCoachingEngine:
    """AI-powered personalized financial coaching engine."""
    
    def __init__(self, llm_manager: LLMClientManager, config: AIConfig):
        self.llm_manager = llm_manager
        self.config = config
        self.behavioral_analyzer = BehavioralPatternAnalyzer()
        self.audit_logger = AuditLogger()
        
        # Coaching templates for different scenarios
        self.coaching_templates = self._initialize_coaching_templates()
        
        # Coaching strategies based on user profiles
        self.coaching_strategies = self._initialize_coaching_strategies()
        
        # Behavioral nudge library
        self.nudge_library = self._initialize_nudge_library()
    
    async def generate_coaching_session(
        self,
        user_context: UserContext,
        coaching_type: CoachingType,
        trigger_event: Optional[Dict[str, Any]] = None,
        tone: Optional[CoachingTone] = None
    ) -> CoachingSession:
        """Generate a personalized coaching session."""
        
        try:
            # Determine appropriate tone if not specified
            if tone is None:
                tone = await self._determine_optimal_tone(user_context, coaching_type)
            
            # Build coaching prompt
            prompt = await self._build_coaching_prompt(
                user_context, coaching_type, trigger_event, tone
            )
            
            # Generate AI coaching message
            llm_response = await self.llm_manager.generate(
                prompt=prompt,
                narrative_type=NarrativeType.RECOMMENDATION,
                temperature=0.7,  # Higher for more creative coaching
                max_tokens=1500
            )
            
            # Parse and structure coaching response
            coaching_content = await self._parse_coaching_response(
                llm_response.content, user_context, coaching_type
            )
            
            # Generate action items
            action_items = await self._generate_action_items(
                user_context, coaching_type, coaching_content
            )
            
            # Select relevant resources
            resources = await self._select_resources(coaching_type, user_context)
            
            # Determine follow-up schedule
            follow_up_date = await self._calculate_follow_up_date(
                coaching_type, user_context
            )
            
            # Define success metrics
            metrics = await self._define_success_metrics(coaching_type)
            
            # Create coaching session
            session = CoachingSession(
                session_id=self._generate_session_id(),
                user_id=user_context.user_id,
                coaching_type=coaching_type,
                tone=tone,
                message=coaching_content['message'],
                action_items=action_items,
                resources=resources,
                follow_up_date=follow_up_date,
                metrics_to_track=metrics['track'],
                success_criteria=metrics['criteria'],
                timestamp=datetime.utcnow()
            )
            
            # Log coaching session
            await self._log_coaching_session(session)
            
            return session
            
        except Exception as e:
            logger.error(f"Error generating coaching session: {str(e)}")
            # Return fallback coaching
            return await self._generate_fallback_coaching(
                user_context, coaching_type
            )
    
    async def _determine_optimal_tone(
        self,
        user_context: UserContext,
        coaching_type: CoachingType
    ) -> CoachingTone:
        """Determine the optimal coaching tone based on context."""
        
        # Map user characteristics to preferred tones
        tone_mapping = {
            'high_stress': CoachingTone.EMPATHETIC,
            'low_engagement': CoachingTone.MOTIVATIONAL,
            'beginner': CoachingTone.EDUCATIONAL,
            'analytical': CoachingTone.ANALYTICAL,
            'achievement': CoachingTone.CELEBRATORY,
            'crisis': CoachingTone.SUPPORTIVE,
            'experienced': CoachingTone.DIRECT
        }
        
        # Analyze user state
        if user_context.stress_indicators.get('financial_stress', 0) > 0.7:
            return CoachingTone.EMPATHETIC
        
        if user_context.engagement_level == 'low':
            return CoachingTone.MOTIVATIONAL
        
        if user_context.investment_experience == 'beginner':
            return CoachingTone.EDUCATIONAL
        
        if coaching_type == CoachingType.CRISIS_MANAGEMENT:
            return CoachingTone.SUPPORTIVE
        
        # Default to supportive tone
        return CoachingTone.SUPPORTIVE
    
    async def _build_coaching_prompt(
        self,
        user_context: UserContext,
        coaching_type: CoachingType,
        trigger_event: Optional[Dict],
        tone: CoachingTone
    ) -> str:
        """Build a comprehensive coaching prompt for the LLM."""
        
        # Get base template
        template = self.coaching_templates.get(coaching_type, {})
        
        # Build context description
        context_desc = f"""
        User Profile:
        - Age: {user_context.age}
        - Life Stage: {user_context.life_stage}
        - Income Level: ${user_context.income_level:,.0f}
        - Savings Rate: {user_context.current_savings_rate:.1%}
        - Debt-to-Income: {user_context.debt_to_income_ratio:.1%}
        - Risk Tolerance: {user_context.risk_tolerance}
        - Investment Experience: {user_context.investment_experience}
        - Financial Goals: {', '.join(user_context.financial_goals[:3])}
        - Engagement Level: {user_context.engagement_level}
        - Learning Style: {user_context.learning_preference}
        """
        
        # Add trigger event if present
        trigger_desc = ""
        if trigger_event:
            trigger_desc = f"""
            Trigger Event:
            - Type: {trigger_event.get('type', 'unknown')}
            - Description: {trigger_event.get('description', '')}
            - Impact: {trigger_event.get('impact', '')}
            """
        
        # Build behavioral insights
        behavioral_desc = ""
        if user_context.behavioral_patterns:
            patterns = user_context.behavioral_patterns
            behavioral_desc = f"""
            Behavioral Insights:
            - Spending Pattern: {patterns.get('spending_pattern', 'unknown')}
            - Savings Consistency: {patterns.get('savings_consistency', 'unknown')}
            - Goal Adherence: {patterns.get('goal_adherence', 'unknown')}
            """
        
        # Construct the prompt
        prompt = f"""
        You are an expert AI financial coach providing personalized guidance.
        
        Coaching Request: {coaching_type.value}
        Tone: {tone.value}
        
        {context_desc}
        {trigger_desc}
        {behavioral_desc}
        
        Based on this user profile, provide personalized financial coaching that:
        1. Addresses their specific situation and {coaching_type.value} needs
        2. Uses a {tone.value} communication style
        3. Provides actionable, specific guidance
        4. Considers their experience level and learning preference
        5. Acknowledges their current progress and challenges
        6. Offers practical next steps they can take immediately
        
        Structure your response with:
        - Opening: Acknowledge their situation
        - Main Guidance: Core coaching message (2-3 key points)
        - Specific Actions: 3-5 concrete steps they can take
        - Motivation: Encouragement tailored to their profile
        - Next Steps: Clear path forward
        
        Keep the tone {tone.value} and appropriate for someone with {user_context.investment_experience} experience.
        Focus on practical, achievable improvements rather than overwhelming changes.
        """
        
        return prompt
    
    async def _parse_coaching_response(
        self,
        llm_response: str,
        user_context: UserContext,
        coaching_type: CoachingType
    ) -> Dict[str, Any]:
        """Parse and structure the LLM coaching response."""
        
        # For now, return the response as-is
        # In production, this would parse structured sections
        return {
            'message': llm_response,
            'type': coaching_type.value,
            'user_id': user_context.user_id
        }
    
    async def _generate_action_items(
        self,
        user_context: UserContext,
        coaching_type: CoachingType,
        coaching_content: Dict
    ) -> List[str]:
        """Generate specific action items based on coaching type."""
        
        action_items_map = {
            CoachingType.GOAL_SETTING: [
                "Review and prioritize your top 3 financial goals",
                "Set specific, measurable targets for each goal",
                "Create monthly milestones to track progress",
                "Schedule weekly 15-minute financial check-ins",
                "Document your 'why' for each goal"
            ],
            CoachingType.BUDGET_OPTIMIZATION: [
                "Track all expenses for the next 7 days",
                "Identify 3 areas where you can reduce spending by 10%",
                "Set up automatic transfers for savings",
                "Review and cancel unused subscriptions",
                "Create spending categories with limits"
            ],
            CoachingType.SAVINGS_ACCELERATION: [
                f"Increase savings rate by 1% this month",
                "Set up automatic savings transfer on payday",
                "Open a high-yield savings account",
                "Start a 52-week savings challenge",
                "Review and optimize recurring expenses"
            ],
            CoachingType.DEBT_REDUCTION: [
                "List all debts with interest rates and balances",
                "Choose debt avalanche or snowball method",
                "Make an extra payment on highest-priority debt",
                "Negotiate lower interest rates with creditors",
                "Create a debt-free target date"
            ],
            CoachingType.INVESTMENT_GUIDANCE: [
                "Review current asset allocation",
                "Research low-cost index funds",
                "Set up automatic investment contributions",
                "Rebalance portfolio quarterly",
                "Increase 401(k) contribution by 1%"
            ],
            CoachingType.EMERGENCY_FUND: [
                "Calculate 3-6 months of essential expenses",
                "Open dedicated emergency fund account",
                "Set up automatic $50 weekly transfer",
                "Identify items to sell for quick fund boost",
                "Review insurance coverage gaps"
            ],
            CoachingType.HABIT_FORMATION: [
                "Choose one financial habit to focus on",
                "Set daily reminder for habit practice",
                "Track habit streak in calendar",
                "Reward yourself for 7-day streaks",
                "Find accountability partner"
            ]
        }
        
        base_items = action_items_map.get(coaching_type, [])
        
        # Personalize based on user context
        personalized_items = []
        for item in base_items[:3]:  # Take top 3 most relevant
            # Adjust for experience level
            if user_context.investment_experience == 'beginner':
                item = item.replace('quarterly', 'every 6 months')
                item = item.replace('1%', '0.5%')
            
            # Adjust for income level
            if user_context.income_level < 50000:
                item = item.replace('$50', '$25')
                item = item.replace('3-6 months', '1-3 months')
            
            personalized_items.append(item)
        
        return personalized_items
    
    async def _select_resources(
        self,
        coaching_type: CoachingType,
        user_context: UserContext
    ) -> List[Dict[str, str]]:
        """Select relevant educational resources."""
        
        resources = {
            CoachingType.GOAL_SETTING: [
                {"title": "SMART Goals Framework", "type": "article", "url": "/resources/smart-goals"},
                {"title": "Goal Setting Workshop", "type": "video", "url": "/resources/goal-workshop"},
                {"title": "Financial Goals Template", "type": "template", "url": "/resources/goals-template"}
            ],
            CoachingType.BUDGET_OPTIMIZATION: [
                {"title": "50/30/20 Budget Rule", "type": "article", "url": "/resources/budget-rule"},
                {"title": "Expense Tracking Guide", "type": "guide", "url": "/resources/expense-tracking"},
                {"title": "Budget Calculator", "type": "tool", "url": "/tools/budget-calculator"}
            ],
            CoachingType.INVESTMENT_GUIDANCE: [
                {"title": "Investment Basics", "type": "course", "url": "/courses/investing-101"},
                {"title": "Portfolio Diversification", "type": "article", "url": "/resources/diversification"},
                {"title": "Risk Assessment Quiz", "type": "tool", "url": "/tools/risk-assessment"}
            ],
            CoachingType.DEBT_REDUCTION: [
                {"title": "Debt Avalanche vs Snowball", "type": "article", "url": "/resources/debt-strategies"},
                {"title": "Debt Payoff Calculator", "type": "tool", "url": "/tools/debt-calculator"},
                {"title": "Credit Score Guide", "type": "guide", "url": "/resources/credit-score"}
            ]
        }
        
        # Get base resources for coaching type
        base_resources = resources.get(coaching_type, [])
        
        # Filter based on user's learning preference
        if user_context.learning_preference == 'visual':
            return [r for r in base_resources if r['type'] in ['video', 'infographic']][:2]
        elif user_context.learning_preference == 'practical':
            return [r for r in base_resources if r['type'] in ['tool', 'template', 'calculator']][:2]
        else:
            return base_resources[:2]
    
    async def _calculate_follow_up_date(
        self,
        coaching_type: CoachingType,
        user_context: UserContext
    ) -> datetime:
        """Calculate optimal follow-up date based on coaching type."""
        
        # Base follow-up intervals
        follow_up_days = {
            CoachingType.GOAL_SETTING: 7,
            CoachingType.BUDGET_OPTIMIZATION: 14,
            CoachingType.SAVINGS_ACCELERATION: 30,
            CoachingType.DEBT_REDUCTION: 14,
            CoachingType.INVESTMENT_GUIDANCE: 30,
            CoachingType.EMERGENCY_FUND: 7,
            CoachingType.CRISIS_MANAGEMENT: 3,
            CoachingType.HABIT_FORMATION: 7,
            CoachingType.BEHAVIORAL_CHANGE: 14
        }
        
        days = follow_up_days.get(coaching_type, 14)
        
        # Adjust based on engagement level
        if user_context.engagement_level == 'high':
            days = max(3, days - 2)
        elif user_context.engagement_level == 'low':
            days = min(30, days + 7)
        
        return datetime.utcnow() + timedelta(days=days)
    
    async def _define_success_metrics(
        self,
        coaching_type: CoachingType
    ) -> Dict[str, Any]:
        """Define success metrics for the coaching intervention."""
        
        metrics_map = {
            CoachingType.GOAL_SETTING: {
                'track': ['goals_created', 'goals_progress', 'milestone_completion'],
                'criteria': {'goals_created': 3, 'milestone_completion': 0.25}
            },
            CoachingType.BUDGET_OPTIMIZATION: {
                'track': ['expense_tracking_days', 'budget_variance', 'category_adherence'],
                'criteria': {'expense_tracking_days': 7, 'budget_variance': 0.1}
            },
            CoachingType.SAVINGS_ACCELERATION: {
                'track': ['savings_rate_change', 'automatic_saves_setup', 'emergency_fund_growth'],
                'criteria': {'savings_rate_change': 0.01, 'automatic_saves_setup': True}
            },
            CoachingType.DEBT_REDUCTION: {
                'track': ['debt_payments_made', 'total_debt_reduced', 'payment_consistency'],
                'criteria': {'debt_payments_made': 2, 'payment_consistency': 1.0}
            },
            CoachingType.HABIT_FORMATION: {
                'track': ['streak_days', 'habit_completion_rate', 'engagement_score'],
                'criteria': {'streak_days': 7, 'habit_completion_rate': 0.8}
            }
        }
        
        return metrics_map.get(
            coaching_type,
            {'track': ['engagement_score'], 'criteria': {'engagement_score': 0.7}}
        )
    
    def _generate_session_id(self) -> str:
        """Generate unique session ID."""
        timestamp = datetime.utcnow().isoformat()
        return hashlib.sha256(timestamp.encode()).hexdigest()[:16]
    
    async def _log_coaching_session(self, session: CoachingSession):
        """Log coaching session for audit and analytics."""
        await self.audit_logger.log_event(
            event_type="coaching_session",
            user_id=session.user_id,
            details={
                'session_id': session.session_id,
                'coaching_type': session.coaching_type.value,
                'tone': session.tone.value,
                'action_items_count': len(session.action_items),
                'resources_count': len(session.resources),
                'follow_up_scheduled': session.follow_up_date.isoformat() if session.follow_up_date else None
            }
        )
    
    async def _generate_fallback_coaching(
        self,
        user_context: UserContext,
        coaching_type: CoachingType
    ) -> CoachingSession:
        """Generate fallback coaching when AI fails."""
        
        fallback_messages = {
            CoachingType.GOAL_SETTING: "Let's focus on setting clear financial goals. Start by identifying your top three priorities.",
            CoachingType.BUDGET_OPTIMIZATION: "Review your spending patterns and identify areas for improvement. Every small change counts.",
            CoachingType.SAVINGS_ACCELERATION: "Increasing your savings rate by even 1% can make a significant long-term difference.",
            CoachingType.DEBT_REDUCTION: "Focus on paying more than the minimum on your highest-interest debt first.",
            CoachingType.EMERGENCY_FUND: "Building an emergency fund starts with saving even $25 per week."
        }
        
        return CoachingSession(
            session_id=self._generate_session_id(),
            user_id=user_context.user_id,
            coaching_type=coaching_type,
            tone=CoachingTone.SUPPORTIVE,
            message=fallback_messages.get(coaching_type, "Stay focused on your financial goals."),
            action_items=["Review your financial situation", "Set one small goal", "Track progress daily"],
            resources=[],
            follow_up_date=datetime.utcnow() + timedelta(days=7),
            metrics_to_track=['engagement_score'],
            success_criteria={'engagement_score': 0.5},
            timestamp=datetime.utcnow()
        )
    
    def _initialize_coaching_templates(self) -> Dict[CoachingType, Dict]:
        """Initialize coaching templates for different scenarios."""
        return {
            CoachingType.GOAL_SETTING: {
                'focus': 'Creating and prioritizing financial goals',
                'key_elements': ['specificity', 'measurability', 'achievability', 'relevance', 'time-bound']
            },
            CoachingType.BUDGET_OPTIMIZATION: {
                'focus': 'Optimizing spending and budgeting',
                'key_elements': ['expense_tracking', 'category_limits', 'savings_first', 'regular_review']
            },
            # Add more templates as needed
        }
    
    def _initialize_coaching_strategies(self) -> Dict[str, Dict]:
        """Initialize coaching strategies based on user profiles."""
        return {
            'beginner': {
                'approach': 'educational',
                'pace': 'gradual',
                'complexity': 'simple',
                'frequency': 'high'
            },
            'intermediate': {
                'approach': 'balanced',
                'pace': 'moderate',
                'complexity': 'moderate',
                'frequency': 'medium'
            },
            'advanced': {
                'approach': 'analytical',
                'pace': 'accelerated',
                'complexity': 'complex',
                'frequency': 'low'
            }
        }
    
    def _initialize_nudge_library(self) -> Dict[str, List[str]]:
        """Initialize behavioral nudge library."""
        return {
            'savings': [
                "You're just $X away from your monthly savings goal!",
                "Great job! You've saved Y% more than last month.",
                "Small amounts add up. Even $10 more makes a difference."
            ],
            'spending': [
                "You've stayed within budget for Z days straight!",
                "Quick tip: Review subscriptions to find hidden savings.",
                "Your spending is trending down - keep it up!"
            ],
            'goals': [
                "You're N% closer to your goal than last month!",
                "Milestone alert: You've reached X% of your target.",
                "Consistency is key - you're building great habits!"
            ]
        }