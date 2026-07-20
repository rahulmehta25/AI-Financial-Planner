"""
ML-powered recommendation system for financial planning.

This module provides:
- Goal optimization recommendations using XGBoost
- Portfolio rebalancing suggestions  
- Risk tolerance prediction
- Behavioral pattern analysis
- Collaborative filtering for peer insights
- Personalized savings strategies
- Life event predictions
- Model monitoring and retraining
"""

from .goal_optimizer import GoalOptimizer
from .portfolio_rebalancer import PortfolioRebalancer
from .risk_predictor import RiskTolerancePredictor
from .behavioral_analyzer import BehavioralPatternAnalyzer
from .collaborative_filter import CollaborativeFilter
from .savings_strategist import SavingsStrategist
from .life_event_predictor import LifeEventPredictor
from .model_monitor import ModelMonitor
from .recommendation_engine import RecommendationEngine

__all__ = [
    "GoalOptimizer",
    "PortfolioRebalancer", 
    "RiskTolerancePredictor",
    "BehavioralPatternAnalyzer",
    "CollaborativeFilter",
    "SavingsStrategist",
    "LifeEventPredictor",
    "ModelMonitor",
    "RecommendationEngine"
]