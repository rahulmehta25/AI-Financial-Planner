"""
Smart Financial Recommendation Engine

ML-based recommendation system with contextual awareness,
behavioral patterns, and personalized financial guidance.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import json
from dataclasses import dataclass, field
import uuid

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.database.base import SessionLocal
from app.models.user import User
from app.ai.llm_client import LLMClientManager

logger = logging.getLogger(__name__)


class RecommendationType(str, Enum):
    """Types of financial recommendations."""
    SAVING = "saving"
    SPENDING = "spending"
    INVESTING = "investing"
    DEBT = "debt"
    GOAL = "goal"
    HABIT = "habit"
    LEARNING = "learning"
    PRODUCT = "product"
    ACTION = "action"
    OPTIMIZATION = "optimization"


class RecommendationPriority(str, Enum):
    """Priority levels for recommendations."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFORMATIONAL = "informational"


class RecommendationContext(str, Enum):
    """Context for recommendations."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    GOAL_BASED = "goal_based"
    EVENT_TRIGGERED = "event_triggered"
    MILESTONE = "milestone"
    SEASONAL = "seasonal"
    CRISIS = "crisis"


@dataclass
class Recommendation:
    """Financial recommendation."""
    recommendation_id: str
    user_id: str
    type: RecommendationType
    priority: RecommendationPriority
    context: RecommendationContext
    title: str
    description: str
    rationale: str
    action_items: List[str]
    expected_impact: Dict[str, Any]
    confidence_score: float  # 0-1
    relevance_score: float  # 0-1
    personalization_score: float  # 0-1
    expires_at: Optional[datetime]
    related_goals: List[str]
    resources: List[Dict[str, str]]
    tracking_metrics: List[str]
    created_at: datetime
    viewed_at: Optional[datetime] = None
    acted_upon: bool = False
    feedback: Optional[str] = None


@dataclass
class UserPreferences:
    """User preferences for recommendations."""
    user_id: str
    preferred_types: List[RecommendationType]
    excluded_types: List[RecommendationType]
    communication_style: str  # detailed, concise, visual
    risk_tolerance: str  # conservative, moderate, aggressive
    time_availability: str  # limited, moderate, flexible
    notification_frequency: str  # real-time, daily, weekly
    focus_areas: List[str]
    ignored_recommendations: List[str]
    acted_recommendations: List[str]


@dataclass
class RecommendationBatch:
    """Batch of recommendations."""
    batch_id: str
    user_id: str
    context: RecommendationContext
    recommendations: List[Recommendation]
    total_score: float
    diversity_score: float
    created_at: datetime


class SmartRecommendationEngine:
    """AI-powered recommendation engine for personalized financial guidance."""
    
    def __init__(self, llm_manager: LLMClientManager):
        self.llm_manager = llm_manager
        
        # User preference storage
        self.user_preferences: Dict[str, UserPreferences] = {}
        
        # Recommendation history
        self.recommendation_history: List[Recommendation] = []
        
        # Feature vectors for collaborative filtering
        self.user_features: Dict[str, np.ndarray] = {}
        self.item_features: Dict[str, np.ndarray] = {}
        
        # Recommendation templates
        self.templates = self._initialize_templates()
        
        # Scoring weights
        self.scoring_weights = self._initialize_scoring_weights()
        
        # Context rules
        self.context_rules = self._initialize_context_rules()
    
    async def generate_recommendations(
        self,
        user_id: str,
        context: RecommendationContext,
        user_data: Dict[str, Any],
        max_recommendations: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> RecommendationBatch:
        """Generate personalized recommendations for user."""
        
        try:
            # Get user preferences
            preferences = self._get_or_create_preferences(user_id)
            
            # Analyze user context
            user_context = await self._analyze_user_context(user_data)
            
            # Generate candidate recommendations
            candidates = await self._generate_candidates(
                user_id, context, user_context, preferences
            )
            
            # Score and rank recommendations
            scored_candidates = await self._score_recommendations(
                candidates, user_context, preferences
            )
            
            # Apply collaborative filtering
            filtered_candidates = await self._apply_collaborative_filtering(
                user_id, scored_candidates
            )
            
            # Ensure diversity
            diverse_candidates = await self._ensure_diversity(
                filtered_candidates, max_recommendations
            )
            
            # Apply user filters
            if filters:
                diverse_candidates = self._apply_filters(diverse_candidates, filters)
            
            # Select top recommendations
            final_recommendations = diverse_candidates[:max_recommendations]
            
            # Calculate batch metrics
            total_score = sum(r.relevance_score for r in final_recommendations)
            diversity_score = await self._calculate_diversity_score(final_recommendations)
            
            # Create batch
            batch = RecommendationBatch(
                batch_id=str(uuid.uuid4()),
                user_id=user_id,
                context=context,
                recommendations=final_recommendations,
                total_score=total_score,
                diversity_score=diversity_score,
                created_at=datetime.utcnow()
            )
            
            # Store recommendations in history
            self.recommendation_history.extend(final_recommendations)
            
            # Update user features for collaborative filtering
            await self._update_user_features(user_id, final_recommendations)
            
            return batch
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {str(e)}")
            return self._get_fallback_recommendations(user_id, context, max_recommendations)
    
    async def get_contextual_recommendation(
        self,
        user_id: str,
        trigger_event: Dict[str, Any],
        user_data: Dict[str, Any]
    ) -> Optional[Recommendation]:
        """Get single contextual recommendation based on trigger event."""
        
        try:
            # Determine recommendation type from trigger
            rec_type = self._determine_recommendation_type(trigger_event)
            
            # Generate contextual recommendation
            recommendation = await self._generate_contextual_recommendation(
                user_id, rec_type, trigger_event, user_data
            )
            
            # Score for relevance
            recommendation.relevance_score = await self._calculate_relevance(
                recommendation, trigger_event, user_data
            )
            
            # Only return if highly relevant
            if recommendation.relevance_score > 0.7:
                self.recommendation_history.append(recommendation)
                return recommendation
            
            return None
            
        except Exception as e:
            logger.error(f"Error generating contextual recommendation: {str(e)}")
            return None
    
    async def track_recommendation_outcome(
        self,
        recommendation_id: str,
        outcome: Dict[str, Any]
    ) -> None:
        """Track outcome of recommendation for learning."""
        
        try:
            # Find recommendation
            recommendation = next(
                (r for r in self.recommendation_history if r.recommendation_id == recommendation_id),
                None
            )
            
            if not recommendation:
                return
            
            # Update recommendation
            recommendation.acted_upon = outcome.get('acted_upon', False)
            recommendation.feedback = outcome.get('feedback')
            
            # Update user preferences based on outcome
            await self._update_preferences_from_outcome(
                recommendation.user_id, recommendation, outcome
            )
            
            # Update collaborative filtering features
            await self._update_features_from_outcome(
                recommendation, outcome
            )
            
            # Log for analytics
            logger.info(f"Tracked outcome for recommendation {recommendation_id}: {outcome}")
            
        except Exception as e:
            logger.error(f"Error tracking outcome: {str(e)}")
    
    async def get_recommendation_analytics(
        self,
        user_id: Optional[str] = None,
        time_period: int = 30  # days
    ) -> Dict[str, Any]:
        """Get analytics on recommendation performance."""
        
        try:
            cutoff = datetime.utcnow() - timedelta(days=time_period)
            
            # Filter recommendations
            if user_id:
                relevant_recs = [
                    r for r in self.recommendation_history
                    if r.user_id == user_id and r.created_at > cutoff
                ]
            else:
                relevant_recs = [
                    r for r in self.recommendation_history
                    if r.created_at > cutoff
                ]
            
            if not relevant_recs:
                return {'message': 'No recommendations in period'}
            
            # Calculate metrics
            analytics = {
                'total_recommendations': len(relevant_recs),
                'acted_upon_rate': sum(1 for r in relevant_recs if r.acted_upon) / len(relevant_recs),
                'average_relevance_score': np.mean([r.relevance_score for r in relevant_recs]),
                'average_confidence_score': np.mean([r.confidence_score for r in relevant_recs]),
                'average_personalization': np.mean([r.personalization_score for r in relevant_recs]),
                'type_distribution': self._calculate_type_distribution(relevant_recs),
                'priority_distribution': self._calculate_priority_distribution(relevant_recs),
                'top_performing': self._identify_top_performing(relevant_recs),
                'improvement_areas': self._identify_improvement_areas(relevant_recs)
            }
            
            return analytics
            
        except Exception as e:
            logger.error(f"Error getting analytics: {str(e)}")
            return {'error': str(e)}
    
    async def optimize_recommendations(
        self,
        user_id: str,
        optimization_goal: str = 'engagement'
    ) -> Dict[str, Any]:
        """Optimize recommendation strategy for user."""
        
        try:
            # Get user's recommendation history
            user_history = [
                r for r in self.recommendation_history
                if r.user_id == user_id
            ]
            
            if not user_history:
                return {'message': 'Insufficient history for optimization'}
            
            # Analyze performance by type
            type_performance = await self._analyze_type_performance(user_history)
            
            # Analyze timing patterns
            timing_patterns = await self._analyze_timing_patterns(user_history)
            
            # Identify successful patterns
            success_patterns = await self._identify_success_patterns(user_history)
            
            # Generate optimization strategy
            strategy = await self._generate_optimization_strategy(
                type_performance, timing_patterns, success_patterns, optimization_goal
            )
            
            # Update user preferences
            preferences = self.user_preferences.get(user_id)
            if preferences:
                await self._apply_optimization_to_preferences(preferences, strategy)
            
            return {
                'optimization_goal': optimization_goal,
                'type_performance': type_performance,
                'timing_patterns': timing_patterns,
                'success_patterns': success_patterns,
                'strategy': strategy,
                'expected_improvement': strategy.get('expected_improvement', 'Unknown')
            }
            
        except Exception as e:
            logger.error(f"Error optimizing recommendations: {str(e)}")
            return {'error': str(e)}
    
    def _get_or_create_preferences(self, user_id: str) -> UserPreferences:
        """Get or create user preferences."""
        
        if user_id in self.user_preferences:
            return self.user_preferences[user_id]
        
        preferences = UserPreferences(
            user_id=user_id,
            preferred_types=[RecommendationType.SAVING, RecommendationType.GOAL],
            excluded_types=[],
            communication_style='balanced',
            risk_tolerance='moderate',
            time_availability='moderate',
            notification_frequency='daily',
            focus_areas=['savings', 'budgeting'],
            ignored_recommendations=[],
            acted_recommendations=[]
        )
        
        self.user_preferences[user_id] = preferences
        return preferences
    
    async def _analyze_user_context(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze user context from data."""
        
        context = {
            'financial_health': self._assess_financial_health(user_data),
            'current_goals': user_data.get('goals', []),
            'recent_transactions': user_data.get('recent_transactions', []),
            'spending_patterns': user_data.get('spending_patterns', {}),
            'life_stage': user_data.get('life_stage', 'unknown'),
            'stress_level': user_data.get('stress_level', 0.5),
            'engagement_level': user_data.get('engagement_level', 'medium'),
            'time_of_year': self._get_seasonal_context(),
            'recent_achievements': user_data.get('achievements', []),
            'challenges': user_data.get('challenges', [])
        }
        
        return context
    
    async def _generate_candidates(
        self,
        user_id: str,
        context: RecommendationContext,
        user_context: Dict,
        preferences: UserPreferences
    ) -> List[Recommendation]:
        """Generate candidate recommendations."""
        
        candidates = []
        
        # Rule-based candidates
        rule_candidates = await self._generate_rule_based_candidates(
            user_context, context
        )
        candidates.extend(rule_candidates)
        
        # AI-generated candidates
        ai_candidates = await self._generate_ai_candidates(
            user_id, user_context, preferences
        )
        candidates.extend(ai_candidates)
        
        # Goal-based candidates
        if user_context.get('current_goals'):
            goal_candidates = await self._generate_goal_based_candidates(
                user_context['current_goals']
            )
            candidates.extend(goal_candidates)
        
        # Seasonal candidates
        seasonal_candidates = await self._generate_seasonal_candidates(
            user_context['time_of_year']
        )
        candidates.extend(seasonal_candidates)
        
        return candidates
    
    async def _generate_rule_based_candidates(
        self,
        user_context: Dict,
        context: RecommendationContext
    ) -> List[Recommendation]:
        """Generate recommendations based on rules."""
        
        candidates = []
        
        # Emergency fund rule
        if user_context.get('financial_health', {}).get('emergency_fund_months', 0) < 3:
            candidates.append(
                Recommendation(
                    recommendation_id=str(uuid.uuid4()),
                    user_id='',  # Will be filled later
                    type=RecommendationType.SAVING,
                    priority=RecommendationPriority.HIGH,
                    context=context,
                    title="Build Your Emergency Fund",
                    description="You have less than 3 months of expenses saved. Building an emergency fund should be a top priority.",
                    rationale="An emergency fund protects you from unexpected expenses and job loss.",
                    action_items=[
                        "Set up automatic transfer of $500/month to savings",
                        "Open high-yield savings account",
                        "Cut discretionary spending by 20%"
                    ],
                    expected_impact={'monthly_savings': 500, 'peace_of_mind': 'high'},
                    confidence_score=0.9,
                    relevance_score=0,  # Will be calculated
                    personalization_score=0,  # Will be calculated
                    expires_at=None,
                    related_goals=['emergency_fund'],
                    resources=[],
                    tracking_metrics=['savings_balance', 'monthly_contribution'],
                    created_at=datetime.utcnow()
                )
            )
        
        # High spending alert
        spending_ratio = user_context.get('spending_patterns', {}).get('spending_to_income', 0)
        if spending_ratio > 0.9:
            candidates.append(
                Recommendation(
                    recommendation_id=str(uuid.uuid4()),
                    user_id='',
                    type=RecommendationType.SPENDING,
                    priority=RecommendationPriority.HIGH,
                    context=context,
                    title="Reduce Monthly Spending",
                    description="Your spending is over 90% of income, leaving little room for savings.",
                    rationale="High spending ratio limits financial flexibility and goal achievement.",
                    action_items=[
                        "Review and cancel unused subscriptions",
                        "Implement 30% reduction in dining out",
                        "Create strict monthly budget"
                    ],
                    expected_impact={'monthly_savings': 300, 'spending_reduction': 0.15},
                    confidence_score=0.85,
                    relevance_score=0,
                    personalization_score=0,
                    expires_at=None,
                    related_goals=['budgeting'],
                    resources=[],
                    tracking_metrics=['spending_ratio', 'savings_rate'],
                    created_at=datetime.utcnow()
                )
            )
        
        return candidates
    
    async def _generate_ai_candidates(
        self,
        user_id: str,
        user_context: Dict,
        preferences: UserPreferences
    ) -> List[Recommendation]:
        """Generate AI-powered recommendations."""
        
        prompt = f"""
        Generate 3 personalized financial recommendations for a user with:
        
        Context:
        - Financial Health: {user_context.get('financial_health')}
        - Current Goals: {user_context.get('current_goals')}
        - Life Stage: {user_context.get('life_stage')}
        - Stress Level: {user_context.get('stress_level')}
        - Preferences: Risk tolerance: {preferences.risk_tolerance}, Time: {preferences.time_availability}
        
        For each recommendation provide:
        1. Title (concise, action-oriented)
        2. Type (saving/spending/investing/debt/goal)
        3. Priority (critical/high/medium/low)
        4. Description (2-3 sentences)
        5. 3 specific action items
        6. Expected monthly impact in dollars
        
        Focus on practical, achievable recommendations that match the user's situation.
        """
        
        try:
            response = await self.llm_manager.generate(
                prompt=prompt,
                temperature=0.7,
                max_tokens=800
            )
            
            # Parse AI response into recommendations
            recommendations = await self._parse_ai_recommendations(response.content, user_id)
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating AI candidates: {str(e)}")
            return []
    
    async def _parse_ai_recommendations(
        self,
        ai_response: str,
        user_id: str
    ) -> List[Recommendation]:
        """Parse AI response into recommendation objects."""
        
        recommendations = []
        
        # Simple parsing (in production would use structured output)
        # For now, create sample recommendations
        sample_titles = [
            "Optimize Your Investment Portfolio",
            "Automate Your Savings",
            "Reduce High-Interest Debt"
        ]
        
        for i, title in enumerate(sample_titles):
            recommendations.append(
                Recommendation(
                    recommendation_id=str(uuid.uuid4()),
                    user_id=user_id,
                    type=RecommendationType.OPTIMIZATION,
                    priority=RecommendationPriority.MEDIUM,
                    context=RecommendationContext.WEEKLY,
                    title=title,
                    description=f"AI-generated recommendation for {title.lower()}",
                    rationale="Based on your financial profile and goals",
                    action_items=[f"Action {j+1} for {title}" for j in range(3)],
                    expected_impact={'improvement': 'moderate'},
                    confidence_score=0.75,
                    relevance_score=0,
                    personalization_score=0.8,
                    expires_at=datetime.utcnow() + timedelta(days=30),
                    related_goals=[],
                    resources=[],
                    tracking_metrics=['progress'],
                    created_at=datetime.utcnow()
                )
            )
        
        return recommendations
    
    async def _generate_goal_based_candidates(
        self,
        goals: List[str]
    ) -> List[Recommendation]:
        """Generate recommendations based on user goals."""
        
        candidates = []
        
        for goal in goals[:2]:  # Top 2 goals
            if 'retirement' in goal.lower():
                candidates.append(
                    Recommendation(
                        recommendation_id=str(uuid.uuid4()),
                        user_id='',
                        type=RecommendationType.GOAL,
                        priority=RecommendationPriority.HIGH,
                        context=RecommendationContext.GOAL_BASED,
                        title="Boost Retirement Savings",
                        description="Increase your retirement contributions to stay on track for your goal.",
                        rationale="Compound interest makes early contributions extremely valuable.",
                        action_items=[
                            "Increase 401(k) contribution by 2%",
                            "Open and fund IRA account",
                            "Review investment allocation"
                        ],
                        expected_impact={'retirement_balance_30y': 150000},
                        confidence_score=0.85,
                        relevance_score=0,
                        personalization_score=0,
                        expires_at=None,
                        related_goals=['retirement'],
                        resources=[],
                        tracking_metrics=['contribution_rate', 'account_balance'],
                        created_at=datetime.utcnow()
                    )
                )
            elif 'home' in goal.lower():
                candidates.append(
                    Recommendation(
                        recommendation_id=str(uuid.uuid4()),
                        user_id='',
                        type=RecommendationType.GOAL,
                        priority=RecommendationPriority.HIGH,
                        context=RecommendationContext.GOAL_BASED,
                        title="Accelerate Home Down Payment Savings",
                        description="Strategies to reach your down payment goal faster.",
                        rationale="A larger down payment means better mortgage terms and lower monthly payments.",
                        action_items=[
                            "Open dedicated down payment savings account",
                            "Set up automatic weekly transfer of $250",
                            "Research first-time buyer programs"
                        ],
                        expected_impact={'months_to_goal': -6},
                        confidence_score=0.8,
                        relevance_score=0,
                        personalization_score=0,
                        expires_at=None,
                        related_goals=['home_purchase'],
                        resources=[],
                        tracking_metrics=['down_payment_saved', 'months_remaining'],
                        created_at=datetime.utcnow()
                    )
                )
        
        return candidates
    
    async def _generate_seasonal_candidates(
        self,
        time_of_year: str
    ) -> List[Recommendation]:
        """Generate seasonal recommendations."""
        
        candidates = []
        
        if time_of_year == 'tax_season':
            candidates.append(
                Recommendation(
                    recommendation_id=str(uuid.uuid4()),
                    user_id='',
                    type=RecommendationType.OPTIMIZATION,
                    priority=RecommendationPriority.HIGH,
                    context=RecommendationContext.SEASONAL,
                    title="Maximize Tax Deductions",
                    description="Review and maximize your tax deductions before filing.",
                    rationale="Proper tax planning can save thousands of dollars.",
                    action_items=[
                        "Gather all tax documents",
                        "Review eligible deductions",
                        "Consider tax-loss harvesting"
                    ],
                    expected_impact={'tax_savings': 2000},
                    confidence_score=0.7,
                    relevance_score=0,
                    personalization_score=0,
                    expires_at=datetime(datetime.now().year, 4, 15),  # Tax deadline
                    related_goals=['tax_optimization'],
                    resources=[],
                    tracking_metrics=['deductions_claimed', 'tax_saved'],
                    created_at=datetime.utcnow()
                )
            )
        
        return candidates
    
    async def _score_recommendations(
        self,
        candidates: List[Recommendation],
        user_context: Dict,
        preferences: UserPreferences
    ) -> List[Recommendation]:
        """Score and rank recommendations."""
        
        for rec in candidates:
            # Calculate relevance score
            rec.relevance_score = await self._calculate_relevance_score(
                rec, user_context, preferences
            )
            
            # Calculate personalization score
            rec.personalization_score = await self._calculate_personalization_score(
                rec, preferences
            )
            
            # Set user_id
            rec.user_id = preferences.user_id
        
        # Sort by combined score
        candidates.sort(
            key=lambda r: (
                r.relevance_score * self.scoring_weights['relevance'] +
                r.confidence_score * self.scoring_weights['confidence'] +
                r.personalization_score * self.scoring_weights['personalization']
            ),
            reverse=True
        )
        
        return candidates
    
    async def _calculate_relevance_score(
        self,
        rec: Recommendation,
        user_context: Dict,
        preferences: UserPreferences
    ) -> float:
        """Calculate relevance score for recommendation."""
        
        score = 0.5  # Base score
        
        # Type preference
        if rec.type in preferences.preferred_types:
            score += 0.2
        elif rec.type in preferences.excluded_types:
            score -= 0.3
        
        # Goal alignment
        user_goals = user_context.get('current_goals', [])
        if any(goal in rec.related_goals for goal in user_goals):
            score += 0.2
        
        # Priority based on financial health
        financial_health = user_context.get('financial_health', {})
        if rec.priority == RecommendationPriority.CRITICAL and \
           financial_health.get('score', 0.5) < 0.3:
            score += 0.3
        
        # Stress level consideration
        if user_context.get('stress_level', 0.5) > 0.7 and \
           rec.type in [RecommendationType.SAVING, RecommendationType.DEBT]:
            score += 0.1
        
        # Time availability
        if preferences.time_availability == 'limited' and \
           len(rec.action_items) > 3:
            score -= 0.1
        
        return max(0, min(1, score))
    
    async def _calculate_personalization_score(
        self,
        rec: Recommendation,
        preferences: UserPreferences
    ) -> float:
        """Calculate personalization score."""
        
        score = 0.5  # Base score
        
        # Communication style match
        if preferences.communication_style == 'detailed' and len(rec.description) > 100:
            score += 0.1
        elif preferences.communication_style == 'concise' and len(rec.description) < 100:
            score += 0.1
        
        # Risk tolerance alignment
        if preferences.risk_tolerance == 'conservative' and \
           rec.type != RecommendationType.INVESTING:
            score += 0.1
        elif preferences.risk_tolerance == 'aggressive' and \
           rec.type == RecommendationType.INVESTING:
            score += 0.2
        
        # Focus area alignment
        if any(area in rec.title.lower() for area in preferences.focus_areas):
            score += 0.2
        
        # Previous interaction
        if rec.recommendation_id not in preferences.ignored_recommendations:
            score += 0.1
        
        return max(0, min(1, score))
    
    async def _apply_collaborative_filtering(
        self,
        user_id: str,
        recommendations: List[Recommendation]
    ) -> List[Recommendation]:
        """Apply collaborative filtering to refine recommendations."""
        
        # Get user feature vector
        if user_id not in self.user_features:
            # Create default feature vector
            self.user_features[user_id] = np.random.rand(10)
        
        user_vector = self.user_features[user_id]
        
        # Score recommendations based on similarity
        for rec in recommendations:
            # Get or create item feature vector
            if rec.recommendation_id not in self.item_features:
                self.item_features[rec.recommendation_id] = np.random.rand(10)
            
            item_vector = self.item_features[rec.recommendation_id]
            
            # Calculate cosine similarity
            similarity = cosine_similarity(
                user_vector.reshape(1, -1),
                item_vector.reshape(1, -1)
            )[0][0]
            
            # Adjust relevance score based on similarity
            rec.relevance_score = rec.relevance_score * 0.7 + similarity * 0.3
        
        # Re-sort by adjusted scores
        recommendations.sort(key=lambda r: r.relevance_score, reverse=True)
        
        return recommendations
    
    async def _ensure_diversity(
        self,
        recommendations: List[Recommendation],
        max_recommendations: int
    ) -> List[Recommendation]:
        """Ensure diversity in recommendation types."""
        
        diverse_recs = []
        type_counts = {}
        
        for rec in recommendations:
            # Limit same type to 2
            if type_counts.get(rec.type, 0) < 2:
                diverse_recs.append(rec)
                type_counts[rec.type] = type_counts.get(rec.type, 0) + 1
            
            if len(diverse_recs) >= max_recommendations:
                break
        
        # If not enough diverse recommendations, add remaining
        if len(diverse_recs) < max_recommendations:
            for rec in recommendations:
                if rec not in diverse_recs:
                    diverse_recs.append(rec)
                if len(diverse_recs) >= max_recommendations:
                    break
        
        return diverse_recs
    
    def _apply_filters(
        self,
        recommendations: List[Recommendation],
        filters: Dict[str, Any]
    ) -> List[Recommendation]:
        """Apply user-specified filters."""
        
        filtered = recommendations
        
        if 'types' in filters:
            filtered = [r for r in filtered if r.type in filters['types']]
        
        if 'min_confidence' in filters:
            filtered = [r for r in filtered if r.confidence_score >= filters['min_confidence']]
        
        if 'priorities' in filters:
            filtered = [r for r in filtered if r.priority in filters['priorities']]
        
        return filtered
    
    async def _calculate_diversity_score(
        self,
        recommendations: List[Recommendation]
    ) -> float:
        """Calculate diversity score for recommendation batch."""
        
        if not recommendations:
            return 0
        
        # Type diversity
        unique_types = len(set(r.type for r in recommendations))
        type_diversity = unique_types / len(RecommendationType)
        
        # Priority diversity
        unique_priorities = len(set(r.priority for r in recommendations))
        priority_diversity = unique_priorities / len(RecommendationPriority)
        
        # Context diversity
        unique_contexts = len(set(r.context for r in recommendations))
        context_diversity = unique_contexts / len(RecommendationContext)
        
        # Combined diversity score
        diversity = (type_diversity + priority_diversity + context_diversity) / 3
        
        return diversity
    
    async def _update_user_features(
        self,
        user_id: str,
        recommendations: List[Recommendation]
    ) -> None:
        """Update user feature vector based on recommendations."""
        
        if user_id not in self.user_features:
            self.user_features[user_id] = np.zeros(10)
        
        # Simple feature update based on recommendation types
        for rec in recommendations:
            type_index = list(RecommendationType).index(rec.type)
            self.user_features[user_id][type_index] += 0.1
        
        # Normalize
        norm = np.linalg.norm(self.user_features[user_id])
        if norm > 0:
            self.user_features[user_id] /= norm
    
    def _get_fallback_recommendations(
        self,
        user_id: str,
        context: RecommendationContext,
        max_recommendations: int
    ) -> RecommendationBatch:
        """Get fallback recommendations when generation fails."""
        
        fallback_recs = [
            Recommendation(
                recommendation_id=str(uuid.uuid4()),
                user_id=user_id,
                type=RecommendationType.SAVING,
                priority=RecommendationPriority.MEDIUM,
                context=context,
                title="Build Your Savings",
                description="Start building your financial security with regular savings.",
                rationale="Savings provide financial flexibility and peace of mind.",
                action_items=["Save 10% of income", "Open high-yield savings account"],
                expected_impact={'monthly_savings': 200},
                confidence_score=0.7,
                relevance_score=0.5,
                personalization_score=0.3,
                expires_at=None,
                related_goals=['savings'],
                resources=[],
                tracking_metrics=['savings_rate'],
                created_at=datetime.utcnow()
            )
        ]
        
        return RecommendationBatch(
            batch_id=str(uuid.uuid4()),
            user_id=user_id,
            context=context,
            recommendations=fallback_recs[:max_recommendations],
            total_score=0.5,
            diversity_score=0.3,
            created_at=datetime.utcnow()
        )
    
    def _determine_recommendation_type(
        self,
        trigger_event: Dict[str, Any]
    ) -> RecommendationType:
        """Determine recommendation type from trigger event."""
        
        event_type = trigger_event.get('type', '').lower()
        
        type_mapping = {
            'overspending': RecommendationType.SPENDING,
            'goal_progress': RecommendationType.GOAL,
            'market_change': RecommendationType.INVESTING,
            'debt_payment': RecommendationType.DEBT,
            'savings_milestone': RecommendationType.SAVING,
            'learning_complete': RecommendationType.LEARNING
        }
        
        for key, rec_type in type_mapping.items():
            if key in event_type:
                return rec_type
        
        return RecommendationType.ACTION
    
    async def _generate_contextual_recommendation(
        self,
        user_id: str,
        rec_type: RecommendationType,
        trigger_event: Dict,
        user_data: Dict
    ) -> Recommendation:
        """Generate recommendation based on specific trigger."""
        
        # Use AI to generate contextual recommendation
        prompt = f"""
        Generate a specific financial recommendation based on:
        
        Trigger Event: {trigger_event}
        Recommendation Type: {rec_type.value}
        User Data: Income: ${user_data.get('income', 0)}, Savings: ${user_data.get('savings', 0)}
        
        Provide:
        1. Action-oriented title
        2. Clear description (2-3 sentences)
        3. 3 immediate action items
        4. Expected impact
        """
        
        try:
            response = await self.llm_manager.generate(
                prompt=prompt,
                temperature=0.6,
                max_tokens=400
            )
            
            # Parse response (simplified)
            return Recommendation(
                recommendation_id=str(uuid.uuid4()),
                user_id=user_id,
                type=rec_type,
                priority=RecommendationPriority.HIGH,
                context=RecommendationContext.EVENT_TRIGGERED,
                title="Take Action on Recent Event",
                description=response.content[:200] if response.content else "Recommended action based on recent activity",
                rationale="Triggered by recent financial event",
                action_items=["Review the situation", "Take corrective action", "Monitor progress"],
                expected_impact={'improvement': 'significant'},
                confidence_score=0.8,
                relevance_score=0,
                personalization_score=0.7,
                expires_at=datetime.utcnow() + timedelta(days=7),
                related_goals=[],
                resources=[],
                tracking_metrics=['event_response'],
                created_at=datetime.utcnow()
            )
        except:
            # Fallback contextual recommendation
            return Recommendation(
                recommendation_id=str(uuid.uuid4()),
                user_id=user_id,
                type=rec_type,
                priority=RecommendationPriority.MEDIUM,
                context=RecommendationContext.EVENT_TRIGGERED,
                title=f"Address {rec_type.value.title()} Opportunity",
                description=f"Recent activity suggests action needed in {rec_type.value}",
                rationale="Based on recent financial activity",
                action_items=["Review situation", "Plan response", "Take action"],
                expected_impact={'status': 'positive'},
                confidence_score=0.6,
                relevance_score=0,
                personalization_score=0.5,
                expires_at=datetime.utcnow() + timedelta(days=7),
                related_goals=[],
                resources=[],
                tracking_metrics=[],
                created_at=datetime.utcnow()
            )
    
    async def _calculate_relevance(
        self,
        recommendation: Recommendation,
        trigger_event: Dict,
        user_data: Dict
    ) -> float:
        """Calculate relevance of contextual recommendation."""
        
        relevance = 0.5  # Base relevance
        
        # Event recency
        event_time = trigger_event.get('timestamp')
        if event_time and isinstance(event_time, datetime):
            hours_ago = (datetime.utcnow() - event_time).total_seconds() / 3600
            if hours_ago < 1:
                relevance += 0.3
            elif hours_ago < 24:
                relevance += 0.2
            elif hours_ago < 168:  # 1 week
                relevance += 0.1
        
        # Event severity/importance
        if trigger_event.get('severity') == 'high':
            relevance += 0.2
        elif trigger_event.get('severity') == 'critical':
            relevance += 0.3
        
        # User engagement level
        if user_data.get('engagement_level') == 'high':
            relevance += 0.1
        
        return min(1.0, relevance)
    
    async def _update_preferences_from_outcome(
        self,
        user_id: str,
        recommendation: Recommendation,
        outcome: Dict
    ) -> None:
        """Update user preferences based on recommendation outcome."""
        
        preferences = self.user_preferences.get(user_id)
        if not preferences:
            return
        
        if outcome.get('acted_upon'):
            # Add to acted recommendations
            if recommendation.recommendation_id not in preferences.acted_recommendations:
                preferences.acted_recommendations.append(recommendation.recommendation_id)
            
            # Increase preference for this type
            if recommendation.type not in preferences.preferred_types:
                preferences.preferred_types.append(recommendation.type)
        else:
            # Add to ignored if explicitly rejected
            if outcome.get('rejected'):
                if recommendation.recommendation_id not in preferences.ignored_recommendations:
                    preferences.ignored_recommendations.append(recommendation.recommendation_id)
    
    async def _update_features_from_outcome(
        self,
        recommendation: Recommendation,
        outcome: Dict
    ) -> None:
        """Update collaborative filtering features based on outcome."""
        
        # Update item features based on outcome
        if recommendation.recommendation_id in self.item_features:
            if outcome.get('acted_upon'):
                # Increase feature values for successful recommendations
                self.item_features[recommendation.recommendation_id] *= 1.1
            else:
                # Decrease for ignored recommendations
                self.item_features[recommendation.recommendation_id] *= 0.9
            
            # Normalize
            norm = np.linalg.norm(self.item_features[recommendation.recommendation_id])
            if norm > 0:
                self.item_features[recommendation.recommendation_id] /= norm
    
    def _calculate_type_distribution(
        self,
        recommendations: List[Recommendation]
    ) -> Dict[str, float]:
        """Calculate distribution of recommendation types."""
        
        type_counts = {}
        for rec in recommendations:
            type_counts[rec.type.value] = type_counts.get(rec.type.value, 0) + 1
        
        total = len(recommendations)
        return {t: c/total for t, c in type_counts.items()} if total > 0 else {}
    
    def _calculate_priority_distribution(
        self,
        recommendations: List[Recommendation]
    ) -> Dict[str, float]:
        """Calculate distribution of recommendation priorities."""
        
        priority_counts = {}
        for rec in recommendations:
            priority_counts[rec.priority.value] = priority_counts.get(rec.priority.value, 0) + 1
        
        total = len(recommendations)
        return {p: c/total for p, c in priority_counts.items()} if total > 0 else {}
    
    def _identify_top_performing(
        self,
        recommendations: List[Recommendation]
    ) -> List[Dict]:
        """Identify top performing recommendations."""
        
        acted_recs = [r for r in recommendations if r.acted_upon]
        
        # Sort by relevance score
        acted_recs.sort(key=lambda r: r.relevance_score, reverse=True)
        
        return [
            {
                'title': r.title,
                'type': r.type.value,
                'relevance_score': r.relevance_score
            }
            for r in acted_recs[:3]
        ]
    
    def _identify_improvement_areas(
        self,
        recommendations: List[Recommendation]
    ) -> List[str]:
        """Identify areas for improvement in recommendations."""
        
        areas = []
        
        # Low action rate
        action_rate = sum(1 for r in recommendations if r.acted_upon) / len(recommendations) if recommendations else 0
        if action_rate < 0.3:
            areas.append("Increase recommendation relevance")
        
        # Low confidence scores
        avg_confidence = np.mean([r.confidence_score for r in recommendations]) if recommendations else 0
        if avg_confidence < 0.6:
            areas.append("Improve recommendation confidence")
        
        # Low personalization
        avg_personalization = np.mean([r.personalization_score for r in recommendations]) if recommendations else 0
        if avg_personalization < 0.5:
            areas.append("Enhance personalization algorithms")
        
        return areas
    
    async def _analyze_type_performance(
        self,
        history: List[Recommendation]
    ) -> Dict[str, float]:
        """Analyze performance by recommendation type."""
        
        type_performance = {}
        
        for rec_type in RecommendationType:
            type_recs = [r for r in history if r.type == rec_type]
            if type_recs:
                acted = sum(1 for r in type_recs if r.acted_upon)
                type_performance[rec_type.value] = acted / len(type_recs)
        
        return type_performance
    
    async def _analyze_timing_patterns(
        self,
        history: List[Recommendation]
    ) -> Dict[str, Any]:
        """Analyze timing patterns in recommendation success."""
        
        # Group by day of week
        day_performance = {}
        for rec in history:
            day = rec.created_at.strftime('%A')
            if day not in day_performance:
                day_performance[day] = {'total': 0, 'acted': 0}
            day_performance[day]['total'] += 1
            if rec.acted_upon:
                day_performance[day]['acted'] += 1
        
        # Calculate success rates
        for day, stats in day_performance.items():
            stats['success_rate'] = stats['acted'] / stats['total'] if stats['total'] > 0 else 0
        
        return {
            'by_day': day_performance,
            'best_day': max(day_performance.items(), key=lambda x: x[1]['success_rate'])[0] if day_performance else None
        }
    
    async def _identify_success_patterns(
        self,
        history: List[Recommendation]
    ) -> Dict[str, Any]:
        """Identify patterns in successful recommendations."""
        
        successful = [r for r in history if r.acted_upon]
        
        patterns = {}
        
        if successful:
            # Common characteristics
            patterns['avg_action_items'] = np.mean([len(r.action_items) for r in successful])
            patterns['common_priority'] = max(
                set(r.priority for r in successful),
                key=lambda p: sum(1 for r in successful if r.priority == p)
            ).value
            patterns['avg_confidence'] = np.mean([r.confidence_score for r in successful])
        
        return patterns
    
    async def _generate_optimization_strategy(
        self,
        type_performance: Dict,
        timing_patterns: Dict,
        success_patterns: Dict,
        optimization_goal: str
    ) -> Dict[str, Any]:
        """Generate optimization strategy based on analysis."""
        
        strategy = {
            'focus_types': [],
            'optimal_timing': {},
            'content_adjustments': [],
            'expected_improvement': 0
        }
        
        # Identify best performing types
        if type_performance:
            sorted_types = sorted(type_performance.items(), key=lambda x: x[1], reverse=True)
            strategy['focus_types'] = [t for t, p in sorted_types[:3] if p > 0.3]
        
        # Optimal timing
        if timing_patterns.get('best_day'):
            strategy['optimal_timing']['preferred_day'] = timing_patterns['best_day']
        
        # Content adjustments based on success patterns
        if success_patterns:
            if success_patterns.get('avg_action_items', 0) < 4:
                strategy['content_adjustments'].append('Keep action items under 4')
            if success_patterns.get('avg_confidence', 0) > 0.7:
                strategy['content_adjustments'].append('Focus on high-confidence recommendations')
        
        # Expected improvement
        if optimization_goal == 'engagement':
            strategy['expected_improvement'] = '25% increase in action rate'
        elif optimization_goal == 'satisfaction':
            strategy['expected_improvement'] = '15% improvement in user satisfaction'
        
        return strategy
    
    async def _apply_optimization_to_preferences(
        self,
        preferences: UserPreferences,
        strategy: Dict
    ) -> None:
        """Apply optimization strategy to user preferences."""
        
        # Update preferred types based on performance
        if strategy.get('focus_types'):
            for type_str in strategy['focus_types']:
                try:
                    rec_type = RecommendationType(type_str)
                    if rec_type not in preferences.preferred_types:
                        preferences.preferred_types.append(rec_type)
                except:
                    pass
        
        # Update notification timing if available
        if strategy.get('optimal_timing', {}).get('preferred_day'):
            # Store for future use
            pass
    
    def _assess_financial_health(self, user_data: Dict) -> Dict[str, Any]:
        """Assess user's financial health."""
        
        income = user_data.get('income', 0)
        expenses = user_data.get('expenses', 0)
        savings = user_data.get('savings', 0)
        debt = user_data.get('debt', 0)
        
        health = {}
        
        # Emergency fund months
        if expenses > 0:
            health['emergency_fund_months'] = savings / expenses
        else:
            health['emergency_fund_months'] = 0
        
        # Debt to income ratio
        if income > 0:
            health['debt_to_income'] = debt / (income * 12)
        else:
            health['debt_to_income'] = 0
        
        # Savings rate
        if income > 0:
            health['savings_rate'] = (income - expenses) / income
        else:
            health['savings_rate'] = 0
        
        # Overall score
        score = 0
        if health['emergency_fund_months'] >= 6:
            score += 0.3
        elif health['emergency_fund_months'] >= 3:
            score += 0.2
        elif health['emergency_fund_months'] >= 1:
            score += 0.1
        
        if health['debt_to_income'] < 0.3:
            score += 0.3
        elif health['debt_to_income'] < 0.5:
            score += 0.2
        elif health['debt_to_income'] < 0.7:
            score += 0.1
        
        if health['savings_rate'] > 0.2:
            score += 0.4
        elif health['savings_rate'] > 0.1:
            score += 0.3
        elif health['savings_rate'] > 0.05:
            score += 0.2
        elif health['savings_rate'] > 0:
            score += 0.1
        
        health['score'] = score
        
        return health
    
    def _get_seasonal_context(self) -> str:
        """Get current seasonal context."""
        
        month = datetime.now().month
        
        if month in [1, 2, 3]:
            return 'tax_season'
        elif month in [6, 7, 8]:
            return 'summer'
        elif month in [11, 12]:
            return 'holiday_season'
        else:
            return 'regular'
    
    def _initialize_templates(self) -> Dict:
        """Initialize recommendation templates."""
        
        return {
            RecommendationType.SAVING: {
                'templates': [
                    'Build emergency fund',
                    'Increase savings rate',
                    'Automate savings'
                ]
            },
            RecommendationType.SPENDING: {
                'templates': [
                    'Reduce discretionary spending',
                    'Cancel subscriptions',
                    'Optimize monthly bills'
                ]
            },
            RecommendationType.INVESTING: {
                'templates': [
                    'Start investing',
                    'Diversify portfolio',
                    'Increase contributions'
                ]
            }
        }
    
    def _initialize_scoring_weights(self) -> Dict[str, float]:
        """Initialize scoring weights."""
        
        return {
            'relevance': 0.4,
            'confidence': 0.3,
            'personalization': 0.3
        }
    
    def _initialize_context_rules(self) -> Dict:
        """Initialize context-based rules."""
        
        return {
            RecommendationContext.DAILY: {
                'max_recommendations': 3,
                'priority_threshold': RecommendationPriority.MEDIUM
            },
            RecommendationContext.WEEKLY: {
                'max_recommendations': 5,
                'priority_threshold': RecommendationPriority.LOW
            },
            RecommendationContext.CRISIS: {
                'max_recommendations': 3,
                'priority_threshold': RecommendationPriority.HIGH
            }
        }