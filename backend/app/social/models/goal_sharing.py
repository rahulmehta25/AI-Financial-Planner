"""
Anonymous goal sharing and peer comparison models
"""

import uuid
from datetime import datetime
from sqlalchemy import (
    Boolean, Column, DateTime, String, Text, Integer, 
    Float, ForeignKey, JSON, Enum
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum

from .base import SocialBase


class GoalCategory(PyEnum):
    """Categories for goals to enable peer comparisons"""
    EMERGENCY_FUND = "emergency_fund"
    RETIREMENT = "retirement"
    HOME_PURCHASE = "home_purchase"
    DEBT_PAYOFF = "debt_payoff"
    EDUCATION = "education"
    TRAVEL = "travel"
    INVESTMENT = "investment"
    BUSINESS = "business"
    OTHER = "other"


class AgeGroup(PyEnum):
    """Age groups for anonymous comparisons"""
    UNDER_25 = "under_25"
    AGE_25_34 = "25_34"
    AGE_35_44 = "35_44"
    AGE_45_54 = "45_54"
    AGE_55_64 = "55_64"
    OVER_65 = "over_65"


class IncomeRange(PyEnum):
    """Income ranges for anonymous comparisons"""
    UNDER_30K = "under_30k"
    RANGE_30K_50K = "30k_50k"
    RANGE_50K_75K = "50k_75k"
    RANGE_75K_100K = "75k_100k"
    RANGE_100K_150K = "100k_150k"
    RANGE_150K_250K = "150k_250k"
    OVER_250K = "over_250k"


class AnonymousGoalShare(SocialBase):
    """Anonymous goal sharing for community inspiration and comparison"""
    
    __tablename__ = "anonymous_goal_shares"
    
    # Original goal reference (optional for privacy)
    original_goal_id = Column(UUID(as_uuid=True), ForeignKey("goals.id"), nullable=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Anonymized goal information
    goal_category = Column(Enum(GoalCategory), nullable=False)
    goal_title = Column(String(200), nullable=False)  # Sanitized title
    goal_description = Column(Text, nullable=True)    # Optional description
    
    # Target information (anonymized amounts)
    target_amount_range = Column(String(50), nullable=True)  # "10k-25k", "25k-50k", etc.
    target_date_year = Column(Integer, nullable=True)        # Just year for privacy
    target_date_quarter = Column(Integer, nullable=True)     # Q1, Q2, Q3, Q4
    
    # Progress information
    current_progress_percentage = Column(Float, nullable=False, default=0.0)
    is_goal_completed = Column(Boolean, default=False, nullable=False)
    completion_date = Column(DateTime, nullable=True)
    
    # Anonymous demographic context
    user_age_group = Column(Enum(AgeGroup), nullable=True)
    user_income_range = Column(Enum(IncomeRange), nullable=True)
    user_location_region = Column(String(50), nullable=True)  # "Northeast", "West Coast", etc.
    
    # Goal strategy and tips (user-provided)
    strategy_description = Column(Text, nullable=True)
    tips_and_lessons = Column(Text, nullable=True)
    challenges_faced = Column(Text, nullable=True)
    
    # Community engagement
    likes_count = Column(Integer, default=0, nullable=False)
    comments_count = Column(Integer, default=0, nullable=False)
    shares_count = Column(Integer, default=0, nullable=False)
    inspiration_votes = Column(Integer, default=0, nullable=False)
    
    # Tags for discovery
    tags = Column(JSON, default=list)  # ["first_time_buyer", "aggressive_saving", etc.]
    
    # Verification (goals with proof of completion get special status)
    is_verified_completion = Column(Boolean, default=False, nullable=False)
    verification_notes = Column(Text, nullable=True)
    
    # Relationships
    original_goal = relationship("Goal", backref="anonymous_shares")
    user = relationship("User", backref="anonymous_goal_shares")
    
    def add_like(self):
        """Increment like counter"""
        self.likes_count += 1
        self.updated_at = datetime.utcnow()
    
    def remove_like(self):
        """Decrement like counter"""
        self.likes_count = max(0, self.likes_count - 1)
        self.updated_at = datetime.utcnow()
    
    def add_inspiration_vote(self):
        """Add inspiration vote"""
        self.inspiration_votes += 1
        self.updated_at = datetime.utcnow()
    
    def mark_completed(self, verification_proof: str = None):
        """Mark goal as completed"""
        self.is_goal_completed = True
        self.completion_date = datetime.utcnow()
        self.current_progress_percentage = 100.0
        
        if verification_proof:
            self.is_verified_completion = True
            self.verification_notes = verification_proof
        
        self.updated_at = datetime.utcnow()


class PeerComparison(SocialBase):
    """Peer comparison data for users to see how they stack up anonymously"""
    
    __tablename__ = "peer_comparisons"
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Comparison cohort definition
    cohort_age_group = Column(Enum(AgeGroup), nullable=False)
    cohort_income_range = Column(Enum(IncomeRange), nullable=False)
    cohort_location_region = Column(String(50), nullable=True)
    cohort_size = Column(Integer, nullable=False)  # Number of users in comparison
    
    # Financial metrics (percentiles within cohort)
    savings_rate_percentile = Column(Float, nullable=True)       # 0-100
    emergency_fund_percentile = Column(Float, nullable=True)     # 0-100
    debt_to_income_percentile = Column(Float, nullable=True)     # 0-100 (lower is better)
    investment_allocation_percentile = Column(Float, nullable=True)  # 0-100
    net_worth_percentile = Column(Float, nullable=True)          # 0-100
    
    # Goal progress comparisons
    goals_completion_rate_percentile = Column(Float, nullable=True)  # 0-100
    average_goal_progress_percentile = Column(Float, nullable=True)  # 0-100
    
    # Behavioral comparisons
    financial_discipline_score = Column(Float, nullable=True)    # 0-100 composite score
    learning_engagement_percentile = Column(Float, nullable=True)  # Community participation
    
    # Anonymized insights
    top_performing_behaviors = Column(JSON, default=list)  # What top performers do differently
    improvement_suggestions = Column(JSON, default=list)   # Personalized suggestions
    similar_user_count = Column(Integer, nullable=True)    # Users with similar profiles
    
    # Comparison metadata
    comparison_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    data_freshness_days = Column(Integer, nullable=False)  # How old is the underlying data
    confidence_score = Column(Float, nullable=True)        # Statistical confidence in comparison
    
    # Privacy protection
    contains_insufficient_data = Column(Boolean, default=False, nullable=False)
    privacy_protection_applied = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    user = relationship("User", backref="peer_comparisons")
    
    def is_comparison_reliable(self) -> bool:
        """Check if comparison has sufficient data to be meaningful"""
        return (
            self.cohort_size >= 10 and  # Minimum cohort size
            not self.contains_insufficient_data and
            (self.confidence_score or 0.0) >= 0.7
        )
    
    def get_relative_performance(self, metric: str) -> str:
        """Get user's relative performance description for a metric"""
        percentile = getattr(self, f"{metric}_percentile", None)
        
        if percentile is None:
            return "Insufficient data"
        
        if percentile >= 90:
            return "Top performer"
        elif percentile >= 75:
            return "Above average"
        elif percentile >= 50:
            return "Average"
        elif percentile >= 25:
            return "Below average"
        else:
            return "Needs improvement"
    
    def generate_insights(self) -> dict:
        """Generate personalized insights based on comparison data"""
        insights = {
            "strengths": [],
            "opportunities": [],
            "recommendations": []
        }
        
        # Identify strengths (top 25% performance)
        metrics = [
            ("savings_rate", "savings rate"),
            ("emergency_fund", "emergency fund"),
            ("investment_allocation", "investment allocation"),
            ("goals_completion_rate", "goal completion"),
        ]
        
        for metric_key, metric_name in metrics:
            percentile = getattr(self, f"{metric_key}_percentile", None)
            if percentile and percentile >= 75:
                insights["strengths"].append(f"Strong {metric_name}")
        
        # Identify opportunities (bottom 50% performance)
        for metric_key, metric_name in metrics:
            percentile = getattr(self, f"{metric_key}_percentile", None)
            if percentile and percentile < 50:
                insights["opportunities"].append(f"Improve {metric_name}")
        
        # Add behavioral recommendations
        if self.top_performing_behaviors:
            insights["recommendations"].extend(self.improvement_suggestions[:3])
        
        return insights