"""
Community challenges and rewards system models
"""

import uuid
from datetime import datetime, timedelta
from sqlalchemy import (
    Boolean, Column, DateTime, String, Text, Integer, 
    Float, ForeignKey, JSON, Enum, CheckConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum

from .base import SocialBase


class ChallengeType(PyEnum):
    """Types of financial challenges"""
    SAVINGS = "savings"
    DEBT_REDUCTION = "debt_reduction"
    INVESTMENT = "investment"
    BUDGETING = "budgeting"
    LEARNING = "learning"
    HABIT_BUILDING = "habit_building"
    SPENDING_REDUCTION = "spending_reduction"
    INCOME_INCREASE = "income_increase"


class ChallengeFrequency(PyEnum):
    """How often challenge repeats"""
    ONE_TIME = "one_time"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"


class ChallengeDifficulty(PyEnum):
    """Challenge difficulty levels"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class ChallengeStatus(PyEnum):
    """Challenge lifecycle status"""
    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class ParticipationStatus(PyEnum):
    """User participation status in challenges"""
    JOINED = "joined"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    WITHDRAWN = "withdrawn"


class CommunityChallenge(SocialBase):
    """Community challenges for collaborative financial goals"""
    
    __tablename__ = "community_challenges"
    
    # Challenge metadata
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    challenge_type = Column(Enum(ChallengeType), nullable=False)
    difficulty_level = Column(Enum(ChallengeDifficulty), nullable=False)
    
    # Challenge creator (optional - can be system-generated)
    created_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Timing
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    registration_deadline = Column(DateTime, nullable=True)
    frequency = Column(Enum(ChallengeFrequency), default=ChallengeFrequency.ONE_TIME, nullable=False)
    
    # Challenge rules and criteria
    success_criteria = Column(JSON, nullable=False)  # Flexible criteria definition
    rules_and_guidelines = Column(Text, nullable=False)
    minimum_participants = Column(Integer, default=1, nullable=False)
    maximum_participants = Column(Integer, nullable=True)
    
    # Target demographic (optional filtering)
    target_age_groups = Column(JSON, default=list)  # List of AgeGroup enums
    target_income_ranges = Column(JSON, default=list)  # List of IncomeRange enums
    target_experience_levels = Column(JSON, default=list)  # List of experience levels
    
    # Progress tracking
    total_participants = Column(Integer, default=0, nullable=False)
    active_participants = Column(Integer, default=0, nullable=False)
    completed_participants = Column(Integer, default=0, nullable=False)
    
    # Rewards and incentives
    has_rewards = Column(Boolean, default=False, nullable=False)
    reward_type = Column(String(50), nullable=True)  # "badges", "points", "prizes", "recognition"
    reward_description = Column(Text, nullable=True)
    total_reward_pool = Column(Float, nullable=True)  # For monetary prizes
    
    # Community engagement
    likes_count = Column(Integer, default=0, nullable=False)
    comments_count = Column(Integer, default=0, nullable=False)
    shares_count = Column(Integer, default=0, nullable=False)
    
    # Challenge status
    status = Column(Enum(ChallengeStatus), default=ChallengeStatus.DRAFT, nullable=False)
    is_featured = Column(Boolean, default=False, nullable=False)
    is_recurring = Column(Boolean, default=False, nullable=False)
    
    # Moderation
    requires_verification = Column(Boolean, default=False, nullable=False)
    auto_approve_completion = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    creator = relationship("User", backref="created_challenges")
    participations = relationship("ChallengeParticipation", back_populates="challenge")
    rewards = relationship("ChallengeReward", back_populates="challenge")
    
    __table_args__ = (
        CheckConstraint("end_date > start_date", name="check_end_after_start"),
        CheckConstraint("maximum_participants IS NULL OR maximum_participants >= minimum_participants", 
                       name="check_max_participants_valid"),
    )
    
    @property
    def is_active(self) -> bool:
        """Check if challenge is currently active"""
        now = datetime.utcnow()
        return (
            self.status == ChallengeStatus.ACTIVE and
            self.start_date <= now <= self.end_date
        )
    
    @property
    def can_register(self) -> bool:
        """Check if users can still register for the challenge"""
        now = datetime.utcnow()
        registration_open = True
        
        if self.registration_deadline:
            registration_open = now <= self.registration_deadline
        
        capacity_available = True
        if self.maximum_participants:
            capacity_available = self.total_participants < self.maximum_participants
        
        return (
            self.status == ChallengeStatus.ACTIVE and
            now < self.end_date and
            registration_open and
            capacity_available
        )
    
    @property
    def completion_rate(self) -> float:
        """Calculate challenge completion rate"""
        if self.total_participants == 0:
            return 0.0
        return (self.completed_participants / self.total_participants) * 100
    
    def add_participant(self):
        """Increment participant count"""
        self.total_participants += 1
        self.active_participants += 1
        self.updated_at = datetime.utcnow()
    
    def complete_participant(self):
        """Move participant from active to completed"""
        if self.active_participants > 0:
            self.active_participants -= 1
        self.completed_participants += 1
        self.updated_at = datetime.utcnow()
    
    def remove_participant(self):
        """Remove participant from challenge"""
        if self.total_participants > 0:
            self.total_participants -= 1
        if self.active_participants > 0:
            self.active_participants -= 1
        self.updated_at = datetime.utcnow()


class ChallengeParticipation(SocialBase):
    """User participation in community challenges"""
    
    __tablename__ = "challenge_participations"
    
    # References
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    challenge_id = Column(UUID(as_uuid=True), ForeignKey("community_challenges.id"), nullable=False)
    
    # Participation details
    joined_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    status = Column(Enum(ParticipationStatus), default=ParticipationStatus.JOINED, nullable=False)
    
    # Progress tracking
    progress_percentage = Column(Float, default=0.0, nullable=False)
    progress_data = Column(JSON, default=dict)  # Flexible progress tracking
    last_update_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Completion details
    completed_at = Column(DateTime, nullable=True)
    completion_proof = Column(Text, nullable=True)  # Evidence of completion
    is_verified = Column(Boolean, default=False, nullable=False)
    verified_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    verified_at = Column(DateTime, nullable=True)
    
    # User experience
    notes = Column(Text, nullable=True)  # User's personal notes
    difficulty_rating = Column(Integer, nullable=True)  # 1-5 rating
    satisfaction_rating = Column(Integer, nullable=True)  # 1-5 rating
    would_recommend = Column(Boolean, nullable=True)
    
    # Social sharing
    is_shared_publicly = Column(Boolean, default=False, nullable=False)
    success_story = Column(Text, nullable=True)  # User's success story
    
    # Rewards earned
    points_earned = Column(Integer, default=0, nullable=False)
    badges_earned = Column(JSON, default=list)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    challenge = relationship("CommunityChallenge", back_populates="participations")
    verifier = relationship("User", foreign_keys=[verified_by_user_id])
    
    __table_args__ = (
        CheckConstraint("progress_percentage >= 0 AND progress_percentage <= 100", 
                       name="check_progress_percentage_valid"),
        CheckConstraint("difficulty_rating IS NULL OR (difficulty_rating >= 1 AND difficulty_rating <= 5)",
                       name="check_difficulty_rating_valid"),
        CheckConstraint("satisfaction_rating IS NULL OR (satisfaction_rating >= 1 AND satisfaction_rating <= 5)",
                       name="check_satisfaction_rating_valid"),
    )
    
    def update_progress(self, percentage: float, data: dict = None):
        """Update participation progress"""
        self.progress_percentage = min(100.0, max(0.0, percentage))
        
        if data:
            self.progress_data.update(data)
        
        self.last_update_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        
        # Auto-complete if 100%
        if self.progress_percentage >= 100.0 and self.status == ParticipationStatus.IN_PROGRESS:
            self.complete()
    
    def complete(self, proof: str = None):
        """Mark participation as completed"""
        self.status = ParticipationStatus.COMPLETED
        self.progress_percentage = 100.0
        self.completed_at = datetime.utcnow()
        
        if proof:
            self.completion_proof = proof
        
        self.updated_at = datetime.utcnow()
    
    def verify_completion(self, verifier_id: uuid.UUID):
        """Verify user's completion of challenge"""
        self.is_verified = True
        self.verified_by_user_id = verifier_id
        self.verified_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def withdraw(self):
        """Withdraw from challenge"""
        self.status = ParticipationStatus.WITHDRAWN
        self.updated_at = datetime.utcnow()


class ChallengeReward(SocialBase):
    """Rewards for challenge completion"""
    
    __tablename__ = "challenge_rewards"
    
    # References
    challenge_id = Column(UUID(as_uuid=True), ForeignKey("community_challenges.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    participation_id = Column(UUID(as_uuid=True), ForeignKey("challenge_participations.id"), nullable=False)
    
    # Reward details
    reward_type = Column(String(50), nullable=False)  # "badge", "points", "certificate", "prize"
    reward_name = Column(String(100), nullable=False)
    reward_description = Column(Text, nullable=True)
    reward_value = Column(Float, nullable=True)  # Point value or monetary value
    
    # Reward metadata
    earned_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    is_claimed = Column(Boolean, default=False, nullable=False)
    claimed_at = Column(DateTime, nullable=True)
    
    # Badge/Certificate details
    badge_image_url = Column(String(500), nullable=True)
    certificate_url = Column(String(500), nullable=True)
    
    # Special rewards
    is_leaderboard_reward = Column(Boolean, default=False, nullable=False)
    leaderboard_position = Column(Integer, nullable=True)
    
    # Relationships
    challenge = relationship("CommunityChallenge", back_populates="rewards")
    user = relationship("User", backref="challenge_rewards")
    participation = relationship("ChallengeParticipation", backref="rewards")
    
    def claim_reward(self):
        """Mark reward as claimed"""
        self.is_claimed = True
        self.claimed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()