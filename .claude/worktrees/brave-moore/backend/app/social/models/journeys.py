"""
Financial journey sharing and success story models
"""

import uuid
from datetime import datetime
from sqlalchemy import (
    Boolean, Column, DateTime, String, Text, Integer, 
    Float, ForeignKey, JSON, Enum, CheckConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum

from .base import SocialBase


class JourneyStatus(PyEnum):
    """Status of financial journey"""
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    PAUSED = "paused"
    ABANDONED = "abandoned"


class JourneyPhase(PyEnum):
    """Phases of financial journey"""
    PLANNING = "planning"
    IMPLEMENTATION = "implementation"
    OPTIMIZATION = "optimization"
    MAINTENANCE = "maintenance"
    REVIEW = "review"


class MilestoneType(PyEnum):
    """Types of journey milestones"""
    FINANCIAL = "financial"
    BEHAVIORAL = "behavioral"
    EDUCATIONAL = "educational"
    GOAL_ACHIEVEMENT = "goal_achievement"
    HABIT_FORMATION = "habit_formation"
    DEBT_REDUCTION = "debt_reduction"
    SAVINGS_TARGET = "savings_target"
    INVESTMENT_MILESTONE = "investment_milestone"


class StoryCategory(PyEnum):
    """Categories for success stories"""
    DEBT_FREEDOM = "debt_freedom"
    FIRST_HOME = "first_home"
    RETIREMENT = "retirement"
    EMERGENCY_FUND = "emergency_fund"
    CAREER_CHANGE = "career_change"
    SIDE_HUSTLE = "side_hustle"
    INVESTMENT_SUCCESS = "investment_success"
    BUDGET_MASTERY = "budget_mastery"
    FINANCIAL_EDUCATION = "financial_education"
    LIFE_CHANGE = "life_change"


class FinancialJourney(SocialBase):
    """User's financial journey with milestones and sharing options"""
    
    __tablename__ = "financial_journeys"
    
    # Journey metadata
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    
    # Journey timeline
    start_date = Column(DateTime, nullable=False)
    target_completion_date = Column(DateTime, nullable=True)
    actual_completion_date = Column(DateTime, nullable=True)
    
    # Journey categorization
    primary_goal = Column(String(100), nullable=False)
    secondary_goals = Column(JSON, default=list)
    journey_phase = Column(Enum(JourneyPhase), default=JourneyPhase.PLANNING, nullable=False)
    status = Column(Enum(JourneyStatus), default=JourneyStatus.IN_PROGRESS, nullable=False)
    
    # Financial context (anonymized ranges)
    starting_financial_situation = Column(JSON, nullable=True)  # Anonymized data
    current_financial_situation = Column(JSON, nullable=True)
    target_financial_situation = Column(JSON, nullable=True)
    
    # Progress tracking
    overall_progress_percentage = Column(Float, default=0.0, nullable=False)
    milestones_completed = Column(Integer, default=0, nullable=False)
    total_milestones = Column(Integer, default=0, nullable=False)
    
    # Journey strategy and approach
    strategy_description = Column(Text, nullable=True)
    tools_and_resources_used = Column(JSON, default=list)
    key_learning_points = Column(JSON, default=list)
    challenges_faced = Column(JSON, default=list)
    
    # Sharing and privacy
    is_shared_publicly = Column(Boolean, default=False, nullable=False)
    sharing_anonymously = Column(Boolean, default=True, nullable=False)
    allowed_viewer_groups = Column(JSON, default=list)  # ["community", "mentees", etc.]
    
    # Community engagement
    views_count = Column(Integer, default=0, nullable=False)
    likes_count = Column(Integer, default=0, nullable=False)
    comments_count = Column(Integer, default=0, nullable=False)
    inspiration_votes = Column(Integer, default=0, nullable=False)
    
    # Featured content
    is_featured = Column(Boolean, default=False, nullable=False)
    featured_at = Column(DateTime, nullable=True)
    
    # Journey metadata
    tags = Column(JSON, default=list)
    difficulty_rating = Column(Integer, nullable=True)  # Self-assessed 1-5
    time_commitment_hours_per_week = Column(Float, nullable=True)
    
    # Relationships
    user = relationship("User", backref="financial_journeys")
    milestones = relationship("JourneyMilestone", back_populates="journey", cascade="all, delete-orphan")
    success_story = relationship("SuccessStory", back_populates="journey", uselist=False)
    
    __table_args__ = (
        CheckConstraint("overall_progress_percentage >= 0 AND overall_progress_percentage <= 100", 
                       name="check_progress_percentage_valid"),
        CheckConstraint("difficulty_rating IS NULL OR (difficulty_rating >= 1 AND difficulty_rating <= 5)",
                       name="check_difficulty_rating_valid"),
    )
    
    @property
    def duration_days(self) -> int:
        """Calculate journey duration in days"""
        end_date = self.actual_completion_date or datetime.utcnow()
        return (end_date - self.start_date).days
    
    @property
    def is_completed(self) -> bool:
        """Check if journey is completed"""
        return self.status == JourneyStatus.COMPLETED
    
    @property
    def milestone_completion_rate(self) -> float:
        """Calculate milestone completion rate"""
        if self.total_milestones == 0:
            return 0.0
        return (self.milestones_completed / self.total_milestones) * 100
    
    def add_milestone(self, milestone_data: dict):
        """Add a milestone to the journey"""
        self.total_milestones += 1
        self.updated_at = datetime.utcnow()
    
    def complete_milestone(self):
        """Mark a milestone as completed"""
        self.milestones_completed += 1
        self.overall_progress_percentage = self.milestone_completion_rate
        self.updated_at = datetime.utcnow()
        
        # Auto-complete journey if all milestones done
        if self.milestones_completed >= self.total_milestones and self.total_milestones > 0:
            self.complete_journey()
    
    def complete_journey(self):
        """Mark journey as completed"""
        self.status = JourneyStatus.COMPLETED
        self.actual_completion_date = datetime.utcnow()
        self.overall_progress_percentage = 100.0
        self.updated_at = datetime.utcnow()
    
    def add_view(self):
        """Increment view count"""
        self.views_count += 1
        self.updated_at = datetime.utcnow()
    
    def add_like(self):
        """Add like to journey"""
        self.likes_count += 1
        self.updated_at = datetime.utcnow()
    
    def add_inspiration_vote(self):
        """Add inspiration vote"""
        self.inspiration_votes += 1
        self.updated_at = datetime.utcnow()


class JourneyMilestone(SocialBase):
    """Individual milestones within a financial journey"""
    
    __tablename__ = "journey_milestones"
    
    # References
    journey_id = Column(UUID(as_uuid=True), ForeignKey("financial_journeys.id"), nullable=False)
    
    # Milestone details
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    milestone_type = Column(Enum(MilestoneType), nullable=False)
    
    # Milestone targets
    target_date = Column(DateTime, nullable=True)
    target_value = Column(Float, nullable=True)  # For financial milestones
    target_description = Column(Text, nullable=True)
    
    # Completion tracking
    is_completed = Column(Boolean, default=False, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    actual_value = Column(Float, nullable=True)
    completion_proof = Column(Text, nullable=True)
    
    # Milestone details
    difficulty_level = Column(Integer, nullable=True)  # 1-5
    estimated_duration_days = Column(Integer, nullable=True)
    actual_duration_days = Column(Integer, nullable=True)
    
    # Learning and insights
    key_learnings = Column(Text, nullable=True)
    challenges_overcome = Column(Text, nullable=True)
    tips_for_others = Column(Text, nullable=True)
    
    # Milestone ordering
    sequence_order = Column(Integer, nullable=False, default=1)
    
    # Relationships
    journey = relationship("FinancialJourney", back_populates="milestones")
    
    __table_args__ = (
        CheckConstraint("difficulty_level IS NULL OR (difficulty_level >= 1 AND difficulty_level <= 5)",
                       name="check_difficulty_level_valid"),
        CheckConstraint("sequence_order > 0", name="check_sequence_order_positive"),
    )
    
    def complete(self, value: float = None, proof: str = None):
        """Mark milestone as completed"""
        self.is_completed = True
        self.completed_at = datetime.utcnow()
        
        if value is not None:
            self.actual_value = value
        
        if proof:
            self.completion_proof = proof
        
        # Calculate actual duration
        self.actual_duration_days = (datetime.utcnow() - self.journey.start_date).days
        
        self.updated_at = datetime.utcnow()
        
        # Update journey milestone count
        self.journey.complete_milestone()
    
    @property
    def is_overdue(self) -> bool:
        """Check if milestone is overdue"""
        if self.is_completed or not self.target_date:
            return False
        return datetime.utcnow() > self.target_date
    
    @property
    def days_until_due(self) -> int:
        """Calculate days until milestone is due"""
        if not self.target_date:
            return 0
        delta = self.target_date - datetime.utcnow()
        return max(0, delta.days)


class SuccessStory(SocialBase):
    """Success stories shared by users"""
    
    __tablename__ = "success_stories"
    
    # Story metadata
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    journey_id = Column(UUID(as_uuid=True), ForeignKey("financial_journeys.id"), nullable=True)
    
    # Story content
    title = Column(String(200), nullable=False)
    story_content = Column(Text, nullable=False)
    category = Column(Enum(StoryCategory), nullable=False)
    
    # Story timeline
    story_start_date = Column(DateTime, nullable=False)
    story_end_date = Column(DateTime, nullable=False)
    duration_months = Column(Integer, nullable=False)
    
    # Financial impact (anonymized)
    starting_situation_description = Column(Text, nullable=True)
    ending_situation_description = Column(Text, nullable=True)
    key_financial_metrics = Column(JSON, nullable=True)  # Anonymized improvements
    
    # Story elements
    biggest_challenge = Column(Text, nullable=True)
    turning_point = Column(Text, nullable=True)
    key_strategies = Column(JSON, default=list)
    resources_used = Column(JSON, default=list)
    advice_for_others = Column(Text, nullable=True)
    
    # Inspiration and motivation
    motivation_quote = Column(Text, nullable=True)
    biggest_learning = Column(Text, nullable=True)
    what_would_you_do_differently = Column(Text, nullable=True)
    
    # Community engagement
    views_count = Column(Integer, default=0, nullable=False)
    likes_count = Column(Integer, default=0, nullable=False)
    comments_count = Column(Integer, default=0, nullable=False)
    shares_count = Column(Integer, default=0, nullable=False)
    inspiration_votes = Column(Integer, default=0, nullable=False)
    helpful_votes = Column(Integer, default=0, nullable=False)
    
    # Privacy and sharing
    is_anonymous = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    verified_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    verification_date = Column(DateTime, nullable=True)
    
    # Featured content
    is_featured = Column(Boolean, default=False, nullable=False)
    featured_at = Column(DateTime, nullable=True)
    editor_notes = Column(Text, nullable=True)
    
    # Story metadata
    tags = Column(JSON, default=list)
    reading_time_minutes = Column(Integer, nullable=True)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id], backref="success_stories")
    journey = relationship("FinancialJourney", back_populates="success_story")
    verifier = relationship("User", foreign_keys=[verified_by_user_id])
    
    __table_args__ = (
        CheckConstraint("duration_months > 0", name="check_duration_positive"),
        CheckConstraint("story_end_date >= story_start_date", name="check_end_after_start"),
    )
    
    @property
    def is_recent(self) -> bool:
        """Check if story is recent (within last 2 years)"""
        two_years_ago = datetime.utcnow().replace(year=datetime.utcnow().year - 2)
        return self.story_end_date >= two_years_ago
    
    @property
    def engagement_score(self) -> float:
        """Calculate overall engagement score"""
        # Weighted score based on different types of engagement
        weighted_score = (
            self.likes_count * 1.0 +
            self.comments_count * 2.0 +
            self.shares_count * 3.0 +
            self.inspiration_votes * 2.5 +
            self.helpful_votes * 2.0 +
            self.views_count * 0.1
        )
        return weighted_score
    
    def add_view(self):
        """Increment view count"""
        self.views_count += 1
        self.updated_at = datetime.utcnow()
    
    def add_like(self):
        """Add like to story"""
        self.likes_count += 1
        self.updated_at = datetime.utcnow()
    
    def add_inspiration_vote(self):
        """Add inspiration vote"""
        self.inspiration_votes += 1
        self.updated_at = datetime.utcnow()
    
    def add_helpful_vote(self):
        """Add helpful vote"""
        self.helpful_votes += 1
        self.updated_at = datetime.utcnow()
    
    def verify_story(self, verifier_id: uuid.UUID, notes: str = None):
        """Verify the authenticity of the success story"""
        self.is_verified = True
        self.verified_by_user_id = verifier_id
        self.verification_date = datetime.utcnow()
        if notes:
            self.editor_notes = notes
        self.updated_at = datetime.utcnow()
    
    def calculate_reading_time(self):
        """Calculate estimated reading time based on content length"""
        # Assume average reading speed of 200 words per minute
        word_count = len(self.story_content.split())
        self.reading_time_minutes = max(1, round(word_count / 200))
        self.updated_at = datetime.utcnow()