"""
AI-Powered Financial Coaching System

Comprehensive coaching system with personalized guidance, habit formation,
crisis management, and interactive learning modules.
"""

from .coaching_engine import PersonalizedCoachingEngine, CoachingType, CoachingTone
from .interactive_coach import InteractiveCoachingManager, ConversationTopic
from .tips_generator import IntelligentTipsGenerator, TipCategory, TipPriority
from .habit_formation import HabitFormationSystem, HabitType, HabitStatus
from .crisis_management import CrisisManagementCoach, CrisisType, CrisisSeverity
from .learning_modules import LearningSystemManager, CourseLevel, LearningPath
from .coaching_analytics import CoachingAnalytics, EngagementMetrics
from .recommendation_engine import SmartRecommendationEngine

__all__ = [
    # Core Engines
    'PersonalizedCoachingEngine',
    'InteractiveCoachingManager',
    'IntelligentTipsGenerator',
    'HabitFormationSystem',
    'CrisisManagementCoach',
    'LearningSystemManager',
    'CoachingAnalytics',
    'SmartRecommendationEngine',
    
    # Enums
    'CoachingType',
    'CoachingTone',
    'ConversationTopic',
    'TipCategory',
    'TipPriority',
    'HabitType',
    'HabitStatus',
    'CrisisType',
    'CrisisSeverity',
    'CourseLevel',
    'LearningPath',
    'EngagementMetrics'
]