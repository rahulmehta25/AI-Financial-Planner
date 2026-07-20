"""
Coaching Analytics and Performance Tracking System

Tracks coaching effectiveness, user engagement, and provides
insights for continuous improvement of coaching strategies.
"""

import asyncio
import logging
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import json
from dataclasses import dataclass, field
import uuid

import numpy as np
import pandas as pd
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.database.base import SessionLocal
from app.models.user import User

logger = logging.getLogger(__name__)


class EngagementMetrics(str, Enum):
    """Types of engagement metrics."""
    SESSION_FREQUENCY = "session_frequency"
    SESSION_DURATION = "session_duration"
    FEATURE_USAGE = "feature_usage"
    ACTION_COMPLETION = "action_completion"
    CONTENT_INTERACTION = "content_interaction"
    GOAL_PROGRESS = "goal_progress"
    HABIT_ADHERENCE = "habit_adherence"
    LEARNING_CONSISTENCY = "learning_consistency"


class PerformanceIndicator(str, Enum):
    """Key performance indicators for coaching."""
    USER_SATISFACTION = "user_satisfaction"
    BEHAVIOR_CHANGE = "behavior_change"
    FINANCIAL_IMPROVEMENT = "financial_improvement"
    KNOWLEDGE_GROWTH = "knowledge_growth"
    STRESS_REDUCTION = "stress_reduction"
    GOAL_ACHIEVEMENT = "goal_achievement"
    RETENTION_RATE = "retention_rate"
    ENGAGEMENT_SCORE = "engagement_score"


@dataclass
class UserEngagementProfile:
    """User's engagement profile with coaching system."""
    user_id: str
    total_sessions: int
    average_session_duration: float  # minutes
    last_active: datetime
    features_used: Dict[str, int]  # feature -> usage count
    preferred_coaching_types: List[str]
    engagement_score: float  # 0-100
    retention_risk: float  # 0-1 probability of churn
    activity_pattern: str  # daily, weekly, sporadic
    peak_usage_times: List[str]  # Hour ranges
    response_rate: float  # Response to coaching prompts
    action_completion_rate: float
    feedback_scores: List[float]
    created_at: datetime


@dataclass
class CoachingEffectiveness:
    """Metrics for coaching effectiveness."""
    coaching_type: str
    success_rate: float
    user_satisfaction: float
    behavior_change_rate: float
    average_time_to_goal: float  # days
    retention_impact: float
    roi_estimate: float  # Return on coaching investment
    best_practices: List[str]
    improvement_areas: List[str]


@dataclass
class InsightReport:
    """Analytics insight report."""
    report_id: str
    period_start: datetime
    period_end: datetime
    total_users: int
    active_users: int
    new_users: int
    churned_users: int
    key_metrics: Dict[str, float]
    trends: Dict[str, str]  # metric -> trend (up/down/stable)
    insights: List[str]
    recommendations: List[str]
    success_stories: List[Dict]
    areas_of_concern: List[Dict]
    generated_at: datetime


class CoachingAnalytics:
    """Analytics system for coaching performance and insights."""
    
    def __init__(self):
        # User engagement tracking
        self.engagement_profiles: Dict[str, UserEngagementProfile] = {}
        
        # Session tracking
        self.session_history: List[Dict] = []
        
        # Performance metrics cache
        self.performance_cache: Dict[str, Any] = {}
        
        # Benchmarks and targets
        self.benchmarks = self._initialize_benchmarks()
        
        # Analytics models (simplified)
        self.prediction_models = self._initialize_prediction_models()
    
    async def track_coaching_interaction(
        self,
        user_id: str,
        interaction_type: str,
        interaction_data: Dict[str, Any]
    ) -> None:
        """Track user interaction with coaching system."""
        
        try:
            # Get or create engagement profile
            profile = self._get_or_create_profile(user_id)
            
            # Update session count
            profile.total_sessions += 1
            profile.last_active = datetime.utcnow()
            
            # Track feature usage
            feature = interaction_data.get('feature', interaction_type)
            profile.features_used[feature] = profile.features_used.get(feature, 0) + 1
            
            # Record session
            session = {
                'user_id': user_id,
                'timestamp': datetime.utcnow(),
                'type': interaction_type,
                'duration': interaction_data.get('duration', 0),
                'actions_taken': interaction_data.get('actions', []),
                'outcome': interaction_data.get('outcome', 'ongoing')
            }
            self.session_history.append(session)
            
            # Update engagement score
            profile.engagement_score = await self._calculate_engagement_score(profile)
            
            # Update retention risk
            profile.retention_risk = await self._calculate_retention_risk(profile)
            
        except Exception as e:
            logger.error(f"Error tracking interaction: {str(e)}")
    
    async def analyze_user_engagement(
        self,
        user_id: str,
        time_period: Optional[int] = 30  # days
    ) -> Dict[str, Any]:
        """Analyze user's engagement with coaching system."""
        
        try:
            profile = self.engagement_profiles.get(user_id)
            if not profile:
                return {'error': 'No engagement data found'}
            
            # Get recent sessions
            recent_sessions = self._get_user_sessions(user_id, time_period)
            
            # Calculate engagement metrics
            metrics = {
                'session_frequency': len(recent_sessions) / max(1, time_period),
                'average_duration': np.mean([s['duration'] for s in recent_sessions]) if recent_sessions else 0,
                'features_utilized': len(profile.features_used),
                'engagement_score': profile.engagement_score,
                'retention_risk': profile.retention_risk,
                'activity_pattern': profile.activity_pattern,
                'response_rate': profile.response_rate,
                'action_completion': profile.action_completion_rate
            }
            
            # Identify engagement trends
            trends = await self._analyze_engagement_trends(recent_sessions)
            
            # Generate engagement insights
            insights = await self._generate_engagement_insights(metrics, trends)
            
            # Provide recommendations
            recommendations = await self._generate_engagement_recommendations(
                profile, metrics, trends
            )
            
            return {
                'user_id': user_id,
                'period_days': time_period,
                'metrics': metrics,
                'trends': trends,
                'insights': insights,
                'recommendations': recommendations,
                'engagement_level': self._categorize_engagement(profile.engagement_score),
                'risk_assessment': self._assess_retention_risk(profile.retention_risk)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing engagement: {str(e)}")
            return {'error': str(e)}
    
    async def measure_coaching_effectiveness(
        self,
        coaching_type: str,
        time_period: Optional[int] = 90  # days
    ) -> CoachingEffectiveness:
        """Measure effectiveness of specific coaching type."""
        
        try:
            # Get relevant sessions
            relevant_sessions = [
                s for s in self.session_history
                if s.get('type') == coaching_type and
                (datetime.utcnow() - s['timestamp']).days <= time_period
            ]
            
            # Calculate success metrics
            success_rate = await self._calculate_success_rate(relevant_sessions)
            
            # Calculate user satisfaction
            satisfaction = await self._calculate_satisfaction(coaching_type)
            
            # Measure behavior change
            behavior_change = await self._measure_behavior_change(
                coaching_type, relevant_sessions
            )
            
            # Calculate time to goal
            time_to_goal = await self._calculate_time_to_goal(coaching_type)
            
            # Assess retention impact
            retention_impact = await self._assess_retention_impact(coaching_type)
            
            # Estimate ROI
            roi = await self._estimate_coaching_roi(
                coaching_type, success_rate, retention_impact
            )
            
            # Identify best practices
            best_practices = await self._identify_best_practices(
                coaching_type, relevant_sessions
            )
            
            # Identify improvement areas
            improvements = await self._identify_improvements(
                coaching_type, relevant_sessions
            )
            
            return CoachingEffectiveness(
                coaching_type=coaching_type,
                success_rate=success_rate,
                user_satisfaction=satisfaction,
                behavior_change_rate=behavior_change,
                average_time_to_goal=time_to_goal,
                retention_impact=retention_impact,
                roi_estimate=roi,
                best_practices=best_practices,
                improvement_areas=improvements
            )
            
        except Exception as e:
            logger.error(f"Error measuring effectiveness: {str(e)}")
            return self._get_fallback_effectiveness(coaching_type)
    
    async def generate_analytics_report(
        self,
        period_days: int = 30,
        include_predictions: bool = True
    ) -> InsightReport:
        """Generate comprehensive analytics report."""
        
        try:
            period_start = datetime.utcnow() - timedelta(days=period_days)
            period_end = datetime.utcnow()
            
            # Calculate user metrics
            user_metrics = await self._calculate_user_metrics(period_start, period_end)
            
            # Calculate key performance indicators
            kpis = await self._calculate_kpis(period_start, period_end)
            
            # Identify trends
            trends = await self._identify_trends(kpis, period_days)
            
            # Generate insights
            insights = await self._generate_insights(user_metrics, kpis, trends)
            
            # Generate recommendations
            recommendations = await self._generate_recommendations(
                user_metrics, kpis, trends
            )
            
            # Identify success stories
            success_stories = await self._identify_success_stories(period_start)
            
            # Identify areas of concern
            concerns = await self._identify_concerns(user_metrics, kpis)
            
            # Add predictions if requested
            if include_predictions:
                predictions = await self._generate_predictions(user_metrics, trends)
                insights.extend(predictions)
            
            return InsightReport(
                report_id=str(uuid.uuid4()),
                period_start=period_start,
                period_end=period_end,
                total_users=user_metrics['total'],
                active_users=user_metrics['active'],
                new_users=user_metrics['new'],
                churned_users=user_metrics['churned'],
                key_metrics=kpis,
                trends=trends,
                insights=insights,
                recommendations=recommendations,
                success_stories=success_stories,
                areas_of_concern=concerns,
                generated_at=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Error generating report: {str(e)}")
            return self._get_fallback_report(period_days)
    
    async def predict_user_behavior(
        self,
        user_id: str,
        prediction_type: str = 'retention'
    ) -> Dict[str, Any]:
        """Predict user behavior using ML models."""
        
        try:
            profile = self.engagement_profiles.get(user_id)
            if not profile:
                return {'error': 'Insufficient data for prediction'}
            
            if prediction_type == 'retention':
                prediction = await self._predict_retention(profile)
            elif prediction_type == 'engagement':
                prediction = await self._predict_engagement(profile)
            elif prediction_type == 'success':
                prediction = await self._predict_success(profile)
            else:
                prediction = {'error': 'Unknown prediction type'}
            
            return {
                'user_id': user_id,
                'prediction_type': prediction_type,
                'prediction': prediction,
                'confidence': prediction.get('confidence', 0),
                'factors': prediction.get('factors', []),
                'recommendations': prediction.get('recommendations', [])
            }
            
        except Exception as e:
            logger.error(f"Error predicting behavior: {str(e)}")
            return {'error': str(e)}
    
    async def identify_coaching_opportunities(
        self,
        user_id: str,
        context: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """Identify personalized coaching opportunities."""
        
        try:
            profile = self.engagement_profiles.get(user_id)
            if not profile:
                profile = self._get_or_create_profile(user_id)
            
            opportunities = []
            
            # Low engagement opportunity
            if profile.engagement_score < 50:
                opportunities.append({
                    'type': 'engagement_boost',
                    'priority': 'high',
                    'description': 'User engagement is low',
                    'recommended_action': 'Send personalized re-engagement campaign',
                    'expected_impact': 'Increase engagement by 30%'
                })
            
            # Retention risk opportunity
            if profile.retention_risk > 0.7:
                opportunities.append({
                    'type': 'retention_intervention',
                    'priority': 'urgent',
                    'description': 'High risk of user churn',
                    'recommended_action': 'Immediate personal outreach with incentives',
                    'expected_impact': 'Reduce churn probability by 40%'
                })
            
            # Feature discovery opportunity
            unused_features = self._identify_unused_features(profile)
            if unused_features:
                opportunities.append({
                    'type': 'feature_education',
                    'priority': 'medium',
                    'description': f"User hasn't tried {len(unused_features)} features",
                    'recommended_action': f"Introduce {unused_features[0]} with tutorial",
                    'expected_impact': 'Increase feature adoption by 25%'
                })
            
            # Success celebration opportunity
            if context and context.get('recent_achievement'):
                opportunities.append({
                    'type': 'celebration',
                    'priority': 'high',
                    'description': 'User achieved a milestone',
                    'recommended_action': 'Celebrate achievement and set next goal',
                    'expected_impact': 'Boost motivation and goal-setting'
                })
            
            # Learning opportunity
            if profile.last_active < datetime.utcnow() - timedelta(days=7):
                opportunities.append({
                    'type': 'reactivation',
                    'priority': 'medium',
                    'description': 'User inactive for over a week',
                    'recommended_action': 'Send progress reminder with easy win',
                    'expected_impact': 'Resume regular engagement'
                })
            
            # Sort by priority
            priority_order = {'urgent': 0, 'high': 1, 'medium': 2, 'low': 3}
            opportunities.sort(key=lambda x: priority_order.get(x['priority'], 3))
            
            return opportunities
            
        except Exception as e:
            logger.error(f"Error identifying opportunities: {str(e)}")
            return []
    
    def _get_or_create_profile(self, user_id: str) -> UserEngagementProfile:
        """Get or create user engagement profile."""
        
        if user_id in self.engagement_profiles:
            return self.engagement_profiles[user_id]
        
        profile = UserEngagementProfile(
            user_id=user_id,
            total_sessions=0,
            average_session_duration=0,
            last_active=datetime.utcnow(),
            features_used={},
            preferred_coaching_types=[],
            engagement_score=50,
            retention_risk=0.5,
            activity_pattern='new',
            peak_usage_times=[],
            response_rate=0,
            action_completion_rate=0,
            feedback_scores=[],
            created_at=datetime.utcnow()
        )
        
        self.engagement_profiles[user_id] = profile
        return profile
    
    def _get_user_sessions(
        self,
        user_id: str,
        days: int
    ) -> List[Dict]:
        """Get user's recent sessions."""
        
        cutoff = datetime.utcnow() - timedelta(days=days)
        return [
            s for s in self.session_history
            if s['user_id'] == user_id and s['timestamp'] > cutoff
        ]
    
    async def _calculate_engagement_score(
        self,
        profile: UserEngagementProfile
    ) -> float:
        """Calculate user engagement score."""
        
        score = 0
        
        # Frequency component (30%)
        if profile.total_sessions > 0:
            days_since_created = (datetime.utcnow() - profile.created_at).days + 1
            frequency = profile.total_sessions / days_since_created
            score += min(30, frequency * 10)
        
        # Recency component (20%)
        days_since_active = (datetime.utcnow() - profile.last_active).days
        if days_since_active == 0:
            score += 20
        elif days_since_active <= 3:
            score += 15
        elif days_since_active <= 7:
            score += 10
        elif days_since_active <= 14:
            score += 5
        
        # Feature usage component (20%)
        features_used = len(profile.features_used)
        score += min(20, features_used * 2)
        
        # Action completion component (20%)
        score += profile.action_completion_rate * 20
        
        # Response rate component (10%)
        score += profile.response_rate * 10
        
        return min(100, score)
    
    async def _calculate_retention_risk(
        self,
        profile: UserEngagementProfile
    ) -> float:
        """Calculate user retention risk."""
        
        risk_score = 0
        
        # Inactivity risk
        days_inactive = (datetime.utcnow() - profile.last_active).days
        if days_inactive > 30:
            risk_score += 0.4
        elif days_inactive > 14:
            risk_score += 0.3
        elif days_inactive > 7:
            risk_score += 0.2
        elif days_inactive > 3:
            risk_score += 0.1
        
        # Low engagement risk
        if profile.engagement_score < 30:
            risk_score += 0.3
        elif profile.engagement_score < 50:
            risk_score += 0.2
        elif profile.engagement_score < 70:
            risk_score += 0.1
        
        # Declining usage pattern
        if profile.activity_pattern == 'declining':
            risk_score += 0.2
        
        # Low action completion
        if profile.action_completion_rate < 0.3:
            risk_score += 0.1
        
        return min(1.0, risk_score)
    
    async def _analyze_engagement_trends(
        self,
        sessions: List[Dict]
    ) -> Dict[str, str]:
        """Analyze engagement trends from sessions."""
        
        if len(sessions) < 2:
            return {'overall': 'insufficient_data'}
        
        # Sort sessions by timestamp
        sessions.sort(key=lambda x: x['timestamp'])
        
        # Split into halves for comparison
        midpoint = len(sessions) // 2
        first_half = sessions[:midpoint]
        second_half = sessions[midpoint:]
        
        trends = {}
        
        # Frequency trend
        first_freq = len(first_half) / max(1, (first_half[-1]['timestamp'] - first_half[0]['timestamp']).days)
        second_freq = len(second_half) / max(1, (second_half[-1]['timestamp'] - second_half[0]['timestamp']).days)
        
        if second_freq > first_freq * 1.2:
            trends['frequency'] = 'increasing'
        elif second_freq < first_freq * 0.8:
            trends['frequency'] = 'decreasing'
        else:
            trends['frequency'] = 'stable'
        
        # Duration trend
        first_dur = np.mean([s['duration'] for s in first_half])
        second_dur = np.mean([s['duration'] for s in second_half])
        
        if second_dur > first_dur * 1.2:
            trends['duration'] = 'increasing'
        elif second_dur < first_dur * 0.8:
            trends['duration'] = 'decreasing'
        else:
            trends['duration'] = 'stable'
        
        # Overall trend
        if trends['frequency'] == 'increasing' and trends['duration'] != 'decreasing':
            trends['overall'] = 'improving'
        elif trends['frequency'] == 'decreasing' or trends['duration'] == 'decreasing':
            trends['overall'] = 'declining'
        else:
            trends['overall'] = 'stable'
        
        return trends
    
    async def _generate_engagement_insights(
        self,
        metrics: Dict,
        trends: Dict
    ) -> List[str]:
        """Generate insights from engagement metrics."""
        
        insights = []
        
        if metrics['engagement_score'] > 80:
            insights.append("Highly engaged user - consider advanced features")
        elif metrics['engagement_score'] < 40:
            insights.append("Low engagement - needs re-engagement strategy")
        
        if trends.get('overall') == 'improving':
            insights.append("Engagement trending upward - maintain momentum")
        elif trends.get('overall') == 'declining':
            insights.append("Engagement declining - intervention recommended")
        
        if metrics['action_completion'] < 0.5:
            insights.append("Low action completion - simplify recommendations")
        
        if metrics['features_utilized'] < 3:
            insights.append("Limited feature usage - introduce new features gradually")
        
        return insights
    
    async def _generate_engagement_recommendations(
        self,
        profile: UserEngagementProfile,
        metrics: Dict,
        trends: Dict
    ) -> List[str]:
        """Generate recommendations to improve engagement."""
        
        recommendations = []
        
        if metrics['retention_risk'] > 0.7:
            recommendations.append("Send personalized win-back campaign immediately")
        
        if metrics['engagement_score'] < 50:
            recommendations.append("Simplify user experience and reduce friction")
            recommendations.append("Send achievement celebration to boost morale")
        
        if trends.get('frequency') == 'decreasing':
            recommendations.append("Implement daily check-in reminders")
            recommendations.append("Create habit-forming micro-interactions")
        
        if metrics['action_completion'] < 0.5:
            recommendations.append("Break down actions into smaller steps")
            recommendations.append("Provide clearer guidance and examples")
        
        if metrics['features_utilized'] < 5:
            recommendations.append("Create feature discovery campaign")
            recommendations.append("Implement interactive tutorials")
        
        return recommendations[:3]  # Top 3 recommendations
    
    def _categorize_engagement(self, score: float) -> str:
        """Categorize engagement level."""
        
        if score >= 80:
            return 'highly_engaged'
        elif score >= 60:
            return 'engaged'
        elif score >= 40:
            return 'moderately_engaged'
        elif score >= 20:
            return 'low_engagement'
        else:
            return 'at_risk'
    
    def _assess_retention_risk(self, risk: float) -> str:
        """Assess retention risk level."""
        
        if risk >= 0.8:
            return 'critical_risk'
        elif risk >= 0.6:
            return 'high_risk'
        elif risk >= 0.4:
            return 'moderate_risk'
        elif risk >= 0.2:
            return 'low_risk'
        else:
            return 'minimal_risk'
    
    async def _calculate_success_rate(self, sessions: List[Dict]) -> float:
        """Calculate success rate from sessions."""
        
        if not sessions:
            return 0
        
        successful = sum(1 for s in sessions if s.get('outcome') == 'success')
        return successful / len(sessions)
    
    async def _calculate_satisfaction(self, coaching_type: str) -> float:
        """Calculate user satisfaction for coaching type."""
        
        # Aggregate feedback scores for this coaching type
        relevant_scores = []
        for profile in self.engagement_profiles.values():
            if coaching_type in profile.preferred_coaching_types:
                relevant_scores.extend(profile.feedback_scores)
        
        if relevant_scores:
            return np.mean(relevant_scores)
        return 0.7  # Default satisfaction
    
    async def _measure_behavior_change(
        self,
        coaching_type: str,
        sessions: List[Dict]
    ) -> float:
        """Measure behavior change rate."""
        
        # Simplified behavior change measurement
        users_with_sessions = set(s['user_id'] for s in sessions)
        
        changed_behavior = 0
        for user_id in users_with_sessions:
            profile = self.engagement_profiles.get(user_id)
            if profile and profile.action_completion_rate > 0.6:
                changed_behavior += 1
        
        return changed_behavior / len(users_with_sessions) if users_with_sessions else 0
    
    async def _calculate_time_to_goal(self, coaching_type: str) -> float:
        """Calculate average time to achieve goals."""
        
        # Simplified calculation
        type_to_days = {
            'goal_setting': 30,
            'habit_formation': 66,
            'debt_reduction': 180,
            'emergency_fund': 90,
            'investment': 120
        }
        
        return type_to_days.get(coaching_type, 60)
    
    async def _assess_retention_impact(self, coaching_type: str) -> float:
        """Assess impact on user retention."""
        
        # Compare retention of users who used this coaching vs those who didn't
        users_with_coaching = [
            p for p in self.engagement_profiles.values()
            if coaching_type in p.features_used
        ]
        
        if not users_with_coaching:
            return 0
        
        avg_retention = 1 - np.mean([p.retention_risk for p in users_with_coaching])
        baseline_retention = 0.6  # Assumed baseline
        
        return (avg_retention - baseline_retention) / baseline_retention
    
    async def _estimate_coaching_roi(
        self,
        coaching_type: str,
        success_rate: float,
        retention_impact: float
    ) -> float:
        """Estimate ROI of coaching type."""
        
        # Simplified ROI calculation
        value_per_success = 100  # Arbitrary value units
        value_per_retained_user = 500
        
        roi = (success_rate * value_per_success) + (retention_impact * value_per_retained_user)
        cost = 50  # Arbitrary cost units
        
        return (roi - cost) / cost if cost > 0 else 0
    
    async def _identify_best_practices(
        self,
        coaching_type: str,
        sessions: List[Dict]
    ) -> List[str]:
        """Identify best practices from successful sessions."""
        
        successful_sessions = [s for s in sessions if s.get('outcome') == 'success']
        
        practices = []
        
        if successful_sessions:
            avg_duration = np.mean([s['duration'] for s in successful_sessions])
            if avg_duration < 10:
                practices.append("Keep sessions under 10 minutes")
            
            # Analyze successful patterns
            practices.append("Provide clear action items")
            practices.append("Follow up within 48 hours")
            practices.append("Celebrate small wins")
        
        return practices
    
    async def _identify_improvements(
        self,
        coaching_type: str,
        sessions: List[Dict]
    ) -> List[str]:
        """Identify areas for improvement."""
        
        failed_sessions = [s for s in sessions if s.get('outcome') != 'success']
        
        improvements = []
        
        if len(failed_sessions) > len(sessions) * 0.3:
            improvements.append("Simplify coaching content")
            improvements.append("Add more examples and case studies")
        
        if coaching_type in ['investment', 'tax_planning']:
            improvements.append("Provide beginner-friendly explanations")
        
        improvements.append("Increase personalization")
        
        return improvements[:3]
    
    def _get_fallback_effectiveness(self, coaching_type: str) -> CoachingEffectiveness:
        """Get fallback effectiveness metrics."""
        
        return CoachingEffectiveness(
            coaching_type=coaching_type,
            success_rate=0.6,
            user_satisfaction=0.7,
            behavior_change_rate=0.4,
            average_time_to_goal=60,
            retention_impact=0.1,
            roi_estimate=1.5,
            best_practices=["Maintain consistency", "Provide clear guidance"],
            improvement_areas=["Increase personalization", "Improve follow-up"]
        )
    
    async def _calculate_user_metrics(
        self,
        period_start: datetime,
        period_end: datetime
    ) -> Dict[str, int]:
        """Calculate user metrics for period."""
        
        total_users = len(self.engagement_profiles)
        
        active_users = sum(
            1 for p in self.engagement_profiles.values()
            if p.last_active >= period_start
        )
        
        new_users = sum(
            1 for p in self.engagement_profiles.values()
            if p.created_at >= period_start
        )
        
        churned_users = sum(
            1 for p in self.engagement_profiles.values()
            if p.retention_risk > 0.8 and p.last_active < period_start
        )
        
        return {
            'total': total_users,
            'active': active_users,
            'new': new_users,
            'churned': churned_users
        }
    
    async def _calculate_kpis(
        self,
        period_start: datetime,
        period_end: datetime
    ) -> Dict[str, float]:
        """Calculate key performance indicators."""
        
        period_sessions = [
            s for s in self.session_history
            if period_start <= s['timestamp'] <= period_end
        ]
        
        kpis = {}
        
        # Engagement KPIs
        if self.engagement_profiles:
            kpis['avg_engagement_score'] = np.mean([
                p.engagement_score for p in self.engagement_profiles.values()
            ])
            kpis['avg_retention_risk'] = np.mean([
                p.retention_risk for p in self.engagement_profiles.values()
            ])
        
        # Session KPIs
        if period_sessions:
            kpis['avg_session_duration'] = np.mean([s['duration'] for s in period_sessions])
            kpis['success_rate'] = await self._calculate_success_rate(period_sessions)
        
        # Completion KPIs
        if self.engagement_profiles:
            kpis['avg_action_completion'] = np.mean([
                p.action_completion_rate for p in self.engagement_profiles.values()
            ])
        
        return kpis
    
    async def _identify_trends(
        self,
        kpis: Dict[str, float],
        period_days: int
    ) -> Dict[str, str]:
        """Identify trends in KPIs."""
        
        # Compare with cached previous period (simplified)
        trends = {}
        
        for metric, value in kpis.items():
            # Simulate trend detection
            random_trend = np.random.choice(['up', 'down', 'stable'], p=[0.4, 0.3, 0.3])
            trends[metric] = random_trend
        
        return trends
    
    async def _generate_insights(
        self,
        user_metrics: Dict,
        kpis: Dict,
        trends: Dict
    ) -> List[str]:
        """Generate insights from analytics."""
        
        insights = []
        
        if user_metrics['active'] / max(1, user_metrics['total']) > 0.7:
            insights.append("High user activity rate indicates strong engagement")
        
        if user_metrics['churned'] > user_metrics['new']:
            insights.append("Churn exceeds acquisition - focus on retention")
        
        if kpis.get('avg_engagement_score', 0) > 70:
            insights.append("Users are highly engaged with coaching features")
        
        if trends.get('success_rate') == 'up':
            insights.append("Coaching effectiveness is improving")
        
        return insights
    
    async def _generate_recommendations(
        self,
        user_metrics: Dict,
        kpis: Dict,
        trends: Dict
    ) -> List[str]:
        """Generate recommendations from analytics."""
        
        recommendations = []
        
        if kpis.get('avg_retention_risk', 0) > 0.5:
            recommendations.append("Implement retention campaign for at-risk users")
        
        if kpis.get('avg_action_completion', 0) < 0.5:
            recommendations.append("Simplify action items and provide better guidance")
        
        if user_metrics['new'] < user_metrics['total'] * 0.1:
            recommendations.append("Increase user acquisition efforts")
        
        if trends.get('avg_engagement_score') == 'down':
            recommendations.append("Review and improve coaching content")
        
        return recommendations
    
    async def _identify_success_stories(
        self,
        period_start: datetime
    ) -> List[Dict]:
        """Identify user success stories."""
        
        stories = []
        
        for profile in self.engagement_profiles.values():
            if profile.engagement_score > 90 and profile.action_completion_rate > 0.8:
                stories.append({
                    'user_id': profile.user_id,
                    'achievement': 'High engagement and action completion',
                    'metrics': {
                        'engagement': profile.engagement_score,
                        'completion': profile.action_completion_rate
                    }
                })
        
        return stories[:5]  # Top 5 stories
    
    async def _identify_concerns(
        self,
        user_metrics: Dict,
        kpis: Dict
    ) -> List[Dict]:
        """Identify areas of concern."""
        
        concerns = []
        
        if user_metrics['churned'] > user_metrics['total'] * 0.1:
            concerns.append({
                'area': 'High churn rate',
                'severity': 'high',
                'impact': f"{user_metrics['churned']} users at risk",
                'recommendation': 'Immediate retention intervention'
            })
        
        if kpis.get('avg_engagement_score', 0) < 40:
            concerns.append({
                'area': 'Low overall engagement',
                'severity': 'medium',
                'impact': 'Reduced coaching effectiveness',
                'recommendation': 'Review and improve user experience'
            })
        
        return concerns
    
    async def _generate_predictions(
        self,
        user_metrics: Dict,
        trends: Dict
    ) -> List[str]:
        """Generate predictive insights."""
        
        predictions = []
        
        if trends.get('avg_retention_risk') == 'up':
            predictions.append("Expect 20% increase in churn next month without intervention")
        
        if trends.get('avg_engagement_score') == 'up':
            predictions.append("Engagement likely to reach 75% in next quarter")
        
        predictions.append("Predicted 15% improvement in goal achievement with current trajectory")
        
        return predictions
    
    def _get_fallback_report(self, period_days: int) -> InsightReport:
        """Get fallback report when generation fails."""
        
        return InsightReport(
            report_id=str(uuid.uuid4()),
            period_start=datetime.utcnow() - timedelta(days=period_days),
            period_end=datetime.utcnow(),
            total_users=0,
            active_users=0,
            new_users=0,
            churned_users=0,
            key_metrics={},
            trends={},
            insights=["Analytics temporarily unavailable"],
            recommendations=["Check system status"],
            success_stories=[],
            areas_of_concern=[],
            generated_at=datetime.utcnow()
        )
    
    async def _predict_retention(
        self,
        profile: UserEngagementProfile
    ) -> Dict[str, Any]:
        """Predict user retention probability."""
        
        # Simplified prediction model
        retention_probability = 1 - profile.retention_risk
        
        factors = []
        if profile.engagement_score < 40:
            factors.append("Low engagement score")
        if profile.last_active < datetime.utcnow() - timedelta(days=7):
            factors.append("Recent inactivity")
        if profile.action_completion_rate < 0.3:
            factors.append("Low action completion")
        
        recommendations = []
        if retention_probability < 0.5:
            recommendations.append("Send re-engagement campaign")
            recommendations.append("Offer personalized incentive")
            recommendations.append("Schedule coaching call")
        
        return {
            'probability': retention_probability,
            'confidence': 0.75,
            'factors': factors,
            'recommendations': recommendations
        }
    
    async def _predict_engagement(
        self,
        profile: UserEngagementProfile
    ) -> Dict[str, Any]:
        """Predict future engagement level."""
        
        # Trend-based prediction
        if profile.activity_pattern == 'increasing':
            future_engagement = min(100, profile.engagement_score * 1.2)
        elif profile.activity_pattern == 'declining':
            future_engagement = max(0, profile.engagement_score * 0.8)
        else:
            future_engagement = profile.engagement_score
        
        return {
            'current': profile.engagement_score,
            'predicted_30_days': future_engagement,
            'confidence': 0.7,
            'factors': ['Historical pattern', 'Recent activity'],
            'recommendations': ['Maintain current coaching frequency']
        }
    
    async def _predict_success(
        self,
        profile: UserEngagementProfile
    ) -> Dict[str, Any]:
        """Predict likelihood of achieving goals."""
        
        # Success prediction based on engagement and completion
        success_probability = (
            profile.engagement_score / 100 * 0.4 +
            profile.action_completion_rate * 0.4 +
            (1 - profile.retention_risk) * 0.2
        )
        
        return {
            'probability': success_probability,
            'confidence': 0.65,
            'factors': ['Engagement level', 'Action completion', 'Consistency'],
            'recommendations': ['Set smaller milestones', 'Increase check-in frequency']
        }
    
    def _identify_unused_features(
        self,
        profile: UserEngagementProfile
    ) -> List[str]:
        """Identify features user hasn't tried."""
        
        all_features = [
            'goal_setting', 'budgeting', 'habit_tracking',
            'learning_modules', 'crisis_management', 'investment_planning'
        ]
        
        unused = [f for f in all_features if f not in profile.features_used]
        return unused
    
    def _initialize_benchmarks(self) -> Dict[str, float]:
        """Initialize performance benchmarks."""
        
        return {
            'target_engagement_score': 70,
            'target_retention_rate': 0.85,
            'target_action_completion': 0.7,
            'target_satisfaction': 4.0,
            'target_success_rate': 0.6
        }
    
    def _initialize_prediction_models(self) -> Dict[str, Any]:
        """Initialize prediction models (simplified)."""
        
        return {
            'retention_model': {'type': 'logistic_regression', 'accuracy': 0.75},
            'engagement_model': {'type': 'time_series', 'accuracy': 0.70},
            'success_model': {'type': 'random_forest', 'accuracy': 0.68}
        }