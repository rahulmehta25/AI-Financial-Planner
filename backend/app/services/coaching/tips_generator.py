"""
Intelligent Financial Tips Generation System

Generates personalized, timely, and actionable financial tips based on user behavior,
market conditions, and financial patterns.
"""

import asyncio
import logging
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import json
from dataclasses import dataclass

import numpy as np
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database.base import SessionLocal
from app.models.user import User
from app.ai.llm_client import LLMClientManager
from app.services.banking.spending_pattern_detector import SpendingPatternDetector

logger = logging.getLogger(__name__)


class TipCategory(str, Enum):
    """Categories of financial tips."""
    SAVINGS = "savings"
    BUDGETING = "budgeting"
    INVESTING = "investing"
    DEBT_MANAGEMENT = "debt_management"
    TAX_PLANNING = "tax_planning"
    RETIREMENT = "retirement"
    INSURANCE = "insurance"
    CREDIT_SCORE = "credit_score"
    EMERGENCY_FUND = "emergency_fund"
    SPENDING_HABITS = "spending_habits"
    FINANCIAL_LITERACY = "financial_literacy"
    MARKET_INSIGHTS = "market_insights"
    SEASONAL = "seasonal"
    LIFESTYLE = "lifestyle"


class TipPriority(str, Enum):
    """Priority levels for tips."""
    URGENT = "urgent"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    EDUCATIONAL = "educational"


class TipTiming(str, Enum):
    """Timing for tip delivery."""
    IMMEDIATE = "immediate"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    SEASONAL = "seasonal"
    EVENT_BASED = "event_based"


@dataclass
class FinancialTip:
    """Represents a financial tip."""
    tip_id: str
    user_id: str
    category: TipCategory
    priority: TipPriority
    title: str
    content: str
    action_items: List[str]
    potential_savings: Optional[float]
    time_to_implement: str  # e.g., "5 minutes", "1 hour", "ongoing"
    difficulty_level: str  # easy, medium, hard
    personalization_score: float  # 0-1, how relevant to user
    expiry_date: Optional[datetime]
    related_resources: List[Dict[str, str]]
    success_metrics: Dict[str, Any]
    created_at: datetime
    delivered_at: Optional[datetime]
    acted_upon: bool = False
    feedback_score: Optional[float] = None


class TipGenerationContext(BaseModel):
    """Context for tip generation."""
    user_id: str
    spending_patterns: Dict[str, Any]
    recent_transactions: List[Dict]
    financial_goals: List[str]
    current_month_progress: Dict[str, float]
    market_conditions: Dict[str, Any]
    seasonal_factors: List[str]
    user_preferences: Dict[str, Any]
    engagement_history: Dict[str, Any]
    stress_indicators: Dict[str, float]


class IntelligentTipsGenerator:
    """Generates intelligent, personalized financial tips."""
    
    def __init__(self, llm_manager: LLMClientManager):
        self.llm_manager = llm_manager
        self.spending_detector = SpendingPatternDetector()
        
        # Initialize tip templates
        self.tip_templates = self._initialize_tip_templates()
        
        # Seasonal tip calendar
        self.seasonal_calendar = self._initialize_seasonal_calendar()
        
        # Behavioral trigger rules
        self.behavioral_triggers = self._initialize_behavioral_triggers()
        
        # Tip effectiveness tracking
        self.effectiveness_cache = {}
    
    async def generate_daily_tips(
        self,
        user_id: str,
        max_tips: int = 3,
        categories: Optional[List[TipCategory]] = None
    ) -> List[FinancialTip]:
        """Generate daily personalized tips for a user."""
        
        try:
            # Build generation context
            context = await self._build_generation_context(user_id)
            
            # Identify relevant tip categories
            if categories is None:
                categories = await self._identify_relevant_categories(context)
            
            # Generate tips for each category
            all_tips = []
            for category in categories[:max_tips]:
                tip = await self._generate_category_tip(context, category)
                if tip:
                    all_tips.append(tip)
            
            # Rank and filter tips
            ranked_tips = await self._rank_tips(all_tips, context)
            
            # Select top tips
            selected_tips = ranked_tips[:max_tips]
            
            # Log tip generation
            await self._log_tip_generation(user_id, selected_tips)
            
            return selected_tips
            
        except Exception as e:
            logger.error(f"Error generating daily tips: {str(e)}")
            return await self._get_fallback_tips(user_id, max_tips)
    
    async def generate_contextual_tip(
        self,
        user_id: str,
        trigger_event: Dict[str, Any]
    ) -> Optional[FinancialTip]:
        """Generate a tip based on a specific trigger event."""
        
        try:
            context = await self._build_generation_context(user_id)
            
            # Determine tip category from trigger
            category = self._map_trigger_to_category(trigger_event)
            
            # Generate AI-powered contextual tip
            prompt = self._build_contextual_prompt(context, trigger_event, category)
            
            llm_response = await self.llm_manager.generate(
                prompt=prompt,
                temperature=0.6,
                max_tokens=500
            )
            
            # Parse and structure tip
            tip = await self._parse_llm_tip(
                llm_response.content,
                user_id,
                category,
                trigger_event
            )
            
            return tip
            
        except Exception as e:
            logger.error(f"Error generating contextual tip: {str(e)}")
            return None
    
    async def generate_weekly_insights(
        self,
        user_id: str
    ) -> Dict[str, Any]:
        """Generate weekly financial insights and tips."""
        
        context = await self._build_generation_context(user_id)
        
        # Analyze week's patterns
        weekly_analysis = await self._analyze_weekly_patterns(context)
        
        # Generate insight categories
        insights = {
            'spending_summary': await self._generate_spending_insights(weekly_analysis),
            'savings_progress': await self._generate_savings_insights(weekly_analysis),
            'goal_updates': await self._generate_goal_insights(weekly_analysis),
            'optimization_opportunities': await self._identify_optimizations(weekly_analysis),
            'upcoming_actions': await self._generate_upcoming_actions(context),
            'achievement_highlights': await self._identify_achievements(weekly_analysis)
        }
        
        # Generate personalized weekly tips
        weekly_tips = await self.generate_daily_tips(
            user_id,
            max_tips=5,
            categories=[
                TipCategory.SAVINGS,
                TipCategory.BUDGETING,
                TipCategory.INVESTING
            ]
        )
        
        insights['weekly_tips'] = [self._tip_to_dict(tip) for tip in weekly_tips]
        
        return insights
    
    async def _build_generation_context(self, user_id: str) -> TipGenerationContext:
        """Build context for tip generation."""
        
        with SessionLocal() as db:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError(f"User {user_id} not found")
            
            # Get user's financial profile and patterns
            # This would integrate with existing services
            spending_patterns = {}  # Would call spending pattern detector
            recent_transactions = []  # Would fetch from banking service
            financial_goals = []  # Would fetch from goals service
            
            return TipGenerationContext(
                user_id=user_id,
                spending_patterns=spending_patterns,
                recent_transactions=recent_transactions,
                financial_goals=financial_goals,
                current_month_progress={
                    'savings_rate': 0.15,
                    'budget_adherence': 0.85,
                    'goal_progress': 0.60
                },
                market_conditions={
                    'interest_rates': 'rising',
                    'inflation': 'moderate',
                    'market_sentiment': 'cautious'
                },
                seasonal_factors=self._get_current_seasonal_factors(),
                user_preferences={
                    'communication_style': 'concise',
                    'tip_frequency': 'daily',
                    'focus_areas': ['savings', 'investing']
                },
                engagement_history={
                    'tips_acted_upon': 0.65,
                    'average_feedback': 4.2,
                    'preferred_categories': ['savings', 'budgeting']
                },
                stress_indicators={
                    'financial_stress': 0.3,
                    'time_stress': 0.5
                }
            )
    
    async def _identify_relevant_categories(
        self,
        context: TipGenerationContext
    ) -> List[TipCategory]:
        """Identify most relevant tip categories for user."""
        
        relevance_scores = {}
        
        # Score based on user's current situation
        if context.current_month_progress['savings_rate'] < 0.10:
            relevance_scores[TipCategory.SAVINGS] = 0.9
        
        if context.current_month_progress['budget_adherence'] < 0.8:
            relevance_scores[TipCategory.BUDGETING] = 0.85
        
        if 'retirement' in context.financial_goals:
            relevance_scores[TipCategory.RETIREMENT] = 0.8
        
        if context.stress_indicators['financial_stress'] > 0.6:
            relevance_scores[TipCategory.EMERGENCY_FUND] = 0.95
            relevance_scores[TipCategory.DEBT_MANAGEMENT] = 0.9
        
        # Add seasonal relevance
        current_month = datetime.now().month
        if current_month in [1, 2, 3]:  # Tax season
            relevance_scores[TipCategory.TAX_PLANNING] = 0.85
        elif current_month in [11, 12]:  # Holiday season
            relevance_scores[TipCategory.SPENDING_HABITS] = 0.9
        
        # Sort by relevance
        sorted_categories = sorted(
            relevance_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return [cat for cat, _ in sorted_categories]
    
    async def _generate_category_tip(
        self,
        context: TipGenerationContext,
        category: TipCategory
    ) -> Optional[FinancialTip]:
        """Generate a tip for a specific category."""
        
        # Build category-specific prompt
        prompt = f"""
        Generate a personalized financial tip for the {category.value} category.
        
        User Context:
        - Current savings rate: {context.current_month_progress['savings_rate']:.1%}
        - Budget adherence: {context.current_month_progress['budget_adherence']:.1%}
        - Financial goals: {', '.join(context.financial_goals[:3])}
        - Stress level: {context.stress_indicators['financial_stress']:.1f}/1.0
        
        Market Context:
        - Interest rates: {context.market_conditions['interest_rates']}
        - Inflation: {context.market_conditions['inflation']}
        
        Create a tip that is:
        1. Specific and actionable
        2. Achievable within the user's constraints
        3. Relevant to current market conditions
        4. Time-bound with clear next steps
        
        Format as:
        Title: [Concise, engaging title]
        Content: [Main tip explanation, 2-3 sentences]
        Actions: [3 specific action items]
        Potential Savings: [Estimated monthly savings if applicable]
        Time to Implement: [Realistic time estimate]
        """
        
        try:
            llm_response = await self.llm_manager.generate(
                prompt=prompt,
                temperature=0.7,
                max_tokens=400
            )
            
            return await self._parse_llm_tip(
                llm_response.content,
                context.user_id,
                category,
                None
            )
        except Exception as e:
            logger.error(f"Error generating category tip: {str(e)}")
            return self._get_template_tip(category, context)
    
    async def _parse_llm_tip(
        self,
        llm_content: str,
        user_id: str,
        category: TipCategory,
        trigger_event: Optional[Dict]
    ) -> FinancialTip:
        """Parse LLM response into structured tip."""
        
        # Simple parsing - in production would use structured output
        lines = llm_content.strip().split('\n')
        
        title = "Financial Tip"
        content = llm_content
        actions = []
        potential_savings = None
        time_to_implement = "15 minutes"
        
        for line in lines:
            if line.startswith("Title:"):
                title = line.replace("Title:", "").strip()
            elif line.startswith("Content:"):
                content = line.replace("Content:", "").strip()
            elif line.startswith("Actions:"):
                actions_text = line.replace("Actions:", "").strip()
                actions = [a.strip() for a in actions_text.split(',')][:3]
            elif line.startswith("Potential Savings:"):
                try:
                    savings_text = line.replace("Potential Savings:", "").strip()
                    potential_savings = float(''.join(filter(str.isdigit, savings_text)))
                except:
                    potential_savings = None
            elif line.startswith("Time to Implement:"):
                time_to_implement = line.replace("Time to Implement:", "").strip()
        
        return FinancialTip(
            tip_id=self._generate_tip_id(),
            user_id=user_id,
            category=category,
            priority=self._determine_priority(category, trigger_event),
            title=title,
            content=content,
            action_items=actions if actions else ["Review your finances", "Set a goal", "Track progress"],
            potential_savings=potential_savings,
            time_to_implement=time_to_implement,
            difficulty_level=self._assess_difficulty(actions),
            personalization_score=0.85,
            expiry_date=datetime.utcnow() + timedelta(days=7),
            related_resources=[],
            success_metrics={'actions_completed': 0, 'savings_achieved': 0},
            created_at=datetime.utcnow(),
            delivered_at=None
        )
    
    def _get_template_tip(
        self,
        category: TipCategory,
        context: TipGenerationContext
    ) -> FinancialTip:
        """Get a template-based tip as fallback."""
        
        templates = self.tip_templates.get(category, [])
        if not templates:
            templates = self.tip_templates[TipCategory.SAVINGS]
        
        template = random.choice(templates)
        
        # Personalize template with context
        title = template['title']
        content = template['content'].format(
            savings_rate=context.current_month_progress['savings_rate'],
            budget_adherence=context.current_month_progress['budget_adherence']
        )
        
        return FinancialTip(
            tip_id=self._generate_tip_id(),
            user_id=context.user_id,
            category=category,
            priority=TipPriority.MEDIUM,
            title=title,
            content=content,
            action_items=template.get('actions', []),
            potential_savings=template.get('potential_savings'),
            time_to_implement=template.get('time_to_implement', '30 minutes'),
            difficulty_level=template.get('difficulty', 'medium'),
            personalization_score=0.6,
            expiry_date=datetime.utcnow() + timedelta(days=7),
            related_resources=template.get('resources', []),
            success_metrics={'tip_viewed': False, 'actions_started': 0},
            created_at=datetime.utcnow(),
            delivered_at=None
        )
    
    async def _rank_tips(
        self,
        tips: List[FinancialTip],
        context: TipGenerationContext
    ) -> List[FinancialTip]:
        """Rank tips by relevance and impact."""
        
        for tip in tips:
            # Calculate ranking score
            score = 0.0
            
            # Personalization weight
            score += tip.personalization_score * 0.3
            
            # Priority weight
            priority_weights = {
                TipPriority.URGENT: 1.0,
                TipPriority.HIGH: 0.8,
                TipPriority.MEDIUM: 0.5,
                TipPriority.LOW: 0.3,
                TipPriority.EDUCATIONAL: 0.4
            }
            score += priority_weights.get(tip.priority, 0.5) * 0.3
            
            # Potential savings weight
            if tip.potential_savings:
                savings_impact = min(tip.potential_savings / 500, 1.0)  # Normalize to 0-1
                score += savings_impact * 0.2
            
            # User preference alignment
            if tip.category in context.user_preferences.get('focus_areas', []):
                score += 0.2
            
            # Store score for sorting
            tip.ranking_score = score
        
        # Sort by ranking score
        return sorted(tips, key=lambda t: getattr(t, 'ranking_score', 0), reverse=True)
    
    def _map_trigger_to_category(self, trigger_event: Dict) -> TipCategory:
        """Map trigger event to appropriate tip category."""
        
        trigger_type = trigger_event.get('type', '').lower()
        
        mapping = {
            'overspending': TipCategory.BUDGETING,
            'low_balance': TipCategory.EMERGENCY_FUND,
            'large_purchase': TipCategory.SPENDING_HABITS,
            'salary_deposit': TipCategory.SAVINGS,
            'market_drop': TipCategory.INVESTING,
            'debt_payment': TipCategory.DEBT_MANAGEMENT,
            'tax_document': TipCategory.TAX_PLANNING,
            'subscription_charge': TipCategory.BUDGETING,
            'milestone_reached': TipCategory.SAVINGS
        }
        
        return mapping.get(trigger_type, TipCategory.FINANCIAL_LITERACY)
    
    def _build_contextual_prompt(
        self,
        context: TipGenerationContext,
        trigger_event: Dict,
        category: TipCategory
    ) -> str:
        """Build prompt for contextual tip generation."""
        
        return f"""
        Generate a timely financial tip based on this trigger event:
        
        Event: {trigger_event.get('type')}
        Description: {trigger_event.get('description', '')}
        Amount: ${trigger_event.get('amount', 0):,.2f}
        Category: {category.value}
        
        User is currently:
        - Saving {context.current_month_progress['savings_rate']:.1%} of income
        - {context.current_month_progress['budget_adherence']:.0%} within budget
        - Stress level: {context.stress_indicators['financial_stress']:.1f}/1.0
        
        Provide an immediately actionable tip that addresses this specific situation.
        Keep it concise, supportive, and focused on the next best action.
        """
    
    def _determine_priority(
        self,
        category: TipCategory,
        trigger_event: Optional[Dict]
    ) -> TipPriority:
        """Determine tip priority based on category and trigger."""
        
        if trigger_event:
            urgency = trigger_event.get('urgency', 'medium')
            if urgency == 'high':
                return TipPriority.URGENT
            elif urgency == 'medium':
                return TipPriority.HIGH
        
        # Category-based defaults
        priority_map = {
            TipCategory.EMERGENCY_FUND: TipPriority.HIGH,
            TipCategory.DEBT_MANAGEMENT: TipPriority.HIGH,
            TipCategory.TAX_PLANNING: TipPriority.MEDIUM,
            TipCategory.SAVINGS: TipPriority.MEDIUM,
            TipCategory.INVESTING: TipPriority.MEDIUM,
            TipCategory.FINANCIAL_LITERACY: TipPriority.LOW
        }
        
        return priority_map.get(category, TipPriority.MEDIUM)
    
    def _assess_difficulty(self, actions: List[str]) -> str:
        """Assess implementation difficulty."""
        
        if not actions:
            return "easy"
        
        # Simple heuristic based on action complexity
        complex_keywords = ['research', 'analyze', 'calculate', 'negotiate', 'restructure']
        simple_keywords = ['check', 'review', 'set', 'enable', 'track']
        
        action_text = ' '.join(actions).lower()
        
        if any(keyword in action_text for keyword in complex_keywords):
            return "hard"
        elif any(keyword in action_text for keyword in simple_keywords):
            return "easy"
        else:
            return "medium"
    
    def _generate_tip_id(self) -> str:
        """Generate unique tip ID."""
        import hashlib
        timestamp = datetime.utcnow().isoformat()
        random_component = str(random.randint(1000, 9999))
        return hashlib.sha256(f"{timestamp}:{random_component}".encode()).hexdigest()[:12]
    
    def _get_current_seasonal_factors(self) -> List[str]:
        """Get current seasonal factors."""
        
        month = datetime.now().month
        factors = []
        
        if month in [1, 2, 3]:
            factors.extend(['tax_season', 'new_year_goals'])
        elif month in [6, 7, 8]:
            factors.extend(['summer_vacation', 'back_to_school'])
        elif month in [11, 12]:
            factors.extend(['holiday_shopping', 'year_end_planning'])
        
        return factors
    
    async def _get_fallback_tips(
        self,
        user_id: str,
        max_tips: int
    ) -> List[FinancialTip]:
        """Get fallback tips when generation fails."""
        
        fallback_tips = [
            FinancialTip(
                tip_id=self._generate_tip_id(),
                user_id=user_id,
                category=TipCategory.SAVINGS,
                priority=TipPriority.MEDIUM,
                title="Automate Your Savings",
                content="Set up automatic transfers to savings right after payday.",
                action_items=["Choose amount to save", "Set up auto-transfer", "Track for one month"],
                potential_savings=200.0,
                time_to_implement="10 minutes",
                difficulty_level="easy",
                personalization_score=0.5,
                expiry_date=datetime.utcnow() + timedelta(days=30),
                related_resources=[],
                success_metrics={},
                created_at=datetime.utcnow(),
                delivered_at=None
            ),
            FinancialTip(
                tip_id=self._generate_tip_id(),
                user_id=user_id,
                category=TipCategory.BUDGETING,
                priority=TipPriority.MEDIUM,
                title="Review Subscriptions",
                content="Cancel unused subscriptions to free up monthly cash flow.",
                action_items=["List all subscriptions", "Identify unused ones", "Cancel and save"],
                potential_savings=50.0,
                time_to_implement="30 minutes",
                difficulty_level="easy",
                personalization_score=0.5,
                expiry_date=datetime.utcnow() + timedelta(days=7),
                related_resources=[],
                success_metrics={},
                created_at=datetime.utcnow(),
                delivered_at=None
            )
        ]
        
        return fallback_tips[:max_tips]
    
    def _tip_to_dict(self, tip: FinancialTip) -> Dict[str, Any]:
        """Convert tip to dictionary."""
        return {
            'id': tip.tip_id,
            'category': tip.category.value,
            'priority': tip.priority.value,
            'title': tip.title,
            'content': tip.content,
            'actions': tip.action_items,
            'potential_savings': tip.potential_savings,
            'time_to_implement': tip.time_to_implement,
            'difficulty': tip.difficulty_level
        }
    
    async def _log_tip_generation(self, user_id: str, tips: List[FinancialTip]):
        """Log tip generation for analytics."""
        logger.info(f"Generated {len(tips)} tips for user {user_id}")
    
    def _initialize_tip_templates(self) -> Dict[TipCategory, List[Dict]]:
        """Initialize tip templates."""
        return {
            TipCategory.SAVINGS: [
                {
                    'title': 'Boost Your Savings Rate',
                    'content': 'Your current savings rate is {savings_rate:.1%}. Try increasing it by 1% this month.',
                    'actions': ['Review budget', 'Identify 1% to cut', 'Set up auto-save'],
                    'potential_savings': 100,
                    'time_to_implement': '15 minutes',
                    'difficulty': 'easy'
                }
            ],
            TipCategory.BUDGETING: [
                {
                    'title': 'Track Your Spending',
                    'content': 'You are {budget_adherence:.0%} within budget. Focus on your top spending category.',
                    'actions': ['Review last week expenses', 'Set category limit', 'Use cash for this category'],
                    'potential_savings': 150,
                    'time_to_implement': '20 minutes',
                    'difficulty': 'medium'
                }
            ]
        }
    
    def _initialize_seasonal_calendar(self) -> Dict[int, List[str]]:
        """Initialize seasonal tip calendar."""
        return {
            1: ['tax_prep', 'new_year_goals', 'gym_membership_review'],
            4: ['tax_filing', 'spring_cleaning_finances'],
            7: ['mid_year_review', 'vacation_budgeting'],
            10: ['year_end_planning', 'benefits_enrollment'],
            12: ['holiday_budgeting', 'charitable_giving', 'tax_loss_harvesting']
        }
    
    def _initialize_behavioral_triggers(self) -> Dict[str, Dict]:
        """Initialize behavioral trigger rules."""
        return {
            'overspending': {
                'threshold': 1.2,  # 20% over budget
                'category': TipCategory.BUDGETING,
                'priority': TipPriority.HIGH
            },
            'savings_milestone': {
                'threshold': 1000,  # Every $1000 saved
                'category': TipCategory.SAVINGS,
                'priority': TipPriority.MEDIUM
            }
        }
    
    async def _analyze_weekly_patterns(self, context: TipGenerationContext) -> Dict:
        """Analyze weekly financial patterns."""
        return {
            'total_spent': 850.00,
            'vs_budget': -50.00,
            'top_categories': ['groceries', 'dining', 'transport'],
            'unusual_charges': [],
            'savings_added': 200.00
        }
    
    async def _generate_spending_insights(self, analysis: Dict) -> Dict:
        """Generate spending insights."""
        return {
            'total': analysis['total_spent'],
            'vs_budget': analysis['vs_budget'],
            'top_category': analysis['top_categories'][0] if analysis['top_categories'] else 'general',
            'recommendation': 'Consider meal planning to reduce dining expenses'
        }
    
    async def _generate_savings_insights(self, analysis: Dict) -> Dict:
        """Generate savings insights."""
        return {
            'amount_saved': analysis['savings_added'],
            'on_track': analysis['savings_added'] >= 150,
            'recommendation': 'Great job! You saved more than your target this week'
        }
    
    async def _generate_goal_insights(self, analysis: Dict) -> Dict:
        """Generate goal progress insights."""
        return {
            'goals_on_track': 2,
            'goals_behind': 1,
            'next_milestone': 'Emergency fund reaches $1000 (80% complete)'
        }
    
    async def _identify_optimizations(self, analysis: Dict) -> List[Dict]:
        """Identify optimization opportunities."""
        return [
            {'area': 'subscriptions', 'potential_savings': 30, 'effort': 'low'},
            {'area': 'insurance', 'potential_savings': 50, 'effort': 'medium'}
        ]
    
    async def _generate_upcoming_actions(self, context: TipGenerationContext) -> List[str]:
        """Generate upcoming action items."""
        return [
            "Review and pay credit card bill (due in 5 days)",
            "Check investment portfolio rebalancing",
            "Schedule annual insurance review"
        ]
    
    async def _identify_achievements(self, analysis: Dict) -> List[str]:
        """Identify user achievements."""
        achievements = []
        
        if analysis.get('vs_budget', 0) < 0:
            achievements.append("Stayed under budget this week!")
        
        if analysis.get('savings_added', 0) > 0:
            achievements.append(f"Added ${analysis['savings_added']:.0f} to savings")
        
        return achievements