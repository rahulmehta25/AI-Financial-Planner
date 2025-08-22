"""
Group savings goals and collaborative planning models
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


class GroupGoalType(PyEnum):
    """Types of group savings goals"""
    FAMILY_VACATION = "family_vacation"
    HOME_DOWN_PAYMENT = "home_down_payment"
    WEDDING = "wedding"
    EMERGENCY_FUND = "emergency_fund"
    BUSINESS_STARTUP = "business_startup"
    EDUCATION_FUND = "education_fund"
    GROUP_INVESTMENT = "group_investment"
    CHARITY_FUNDRAISING = "charity_fundraising"
    EVENT_PLANNING = "event_planning"
    OTHER = "other"


class GroupGoalStatus(PyEnum):
    """Group goal lifecycle status"""
    PLANNING = "planning"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class ParticipantRole(PyEnum):
    """Roles within group goals"""
    CREATOR = "creator"
    ADMIN = "admin"
    PARTICIPANT = "participant"
    VIEWER = "viewer"


class ContributionType(PyEnum):
    """Types of contributions to group goals"""
    MONETARY = "monetary"
    IN_KIND = "in_kind"
    SERVICE = "service"
    MILESTONE = "milestone"


class GroupSavingsGoal(SocialBase):
    """Collaborative savings goals with multiple participants"""
    
    __tablename__ = "group_savings_goals"
    
    # Goal metadata
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    goal_type = Column(Enum(GroupGoalType), nullable=False)
    
    # Creator and ownership
    created_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Financial targets
    target_amount = Column(Float, nullable=False)
    current_amount = Column(Float, default=0.0, nullable=False)
    target_date = Column(DateTime, nullable=False)
    
    # Group settings
    minimum_participants = Column(Integer, default=2, nullable=False)
    maximum_participants = Column(Integer, nullable=True)
    is_invitation_only = Column(Boolean, default=False, nullable=False)
    requires_approval = Column(Boolean, default=True, nullable=False)
    
    # Contribution rules
    minimum_contribution = Column(Float, nullable=True)
    suggested_contribution = Column(Float, nullable=True)
    equal_contributions_required = Column(Boolean, default=False, nullable=False)
    allow_unequal_benefits = Column(Boolean, default=True, nullable=False)
    
    # Privacy and visibility
    is_public = Column(Boolean, default=False, nullable=False)
    is_searchable = Column(Boolean, default=True, nullable=False)
    privacy_level = Column(String(50), default="participants_only", nullable=False)
    
    # Progress tracking
    total_participants = Column(Integer, default=1, nullable=False)  # Creator counts as 1
    active_participants = Column(Integer, default=1, nullable=False)
    progress_percentage = Column(Float, default=0.0, nullable=False)
    
    # Milestones and deadlines
    milestones = Column(JSON, default=list)  # List of milestone definitions
    upcoming_deadlines = Column(JSON, default=list)  # Important dates
    
    # Goal status
    status = Column(Enum(GroupGoalStatus), default=GroupGoalStatus.PLANNING, nullable=False)
    is_featured = Column(Boolean, default=False, nullable=False)
    
    # Success tracking
    completed_at = Column(DateTime, nullable=True)
    actual_completion_amount = Column(Float, nullable=True)
    success_rate = Column(Float, nullable=True)  # For completed goals
    
    # Communication
    allow_comments = Column(Boolean, default=True, nullable=False)
    allow_updates = Column(Boolean, default=True, nullable=False)
    notification_frequency = Column(String(20), default="weekly", nullable=False)
    
    # Tags and categorization
    tags = Column(JSON, default=list)
    category_tags = Column(JSON, default=list)
    
    # Relationships
    creator = relationship("User", backref="created_group_goals")
    participations = relationship("GroupGoalParticipation", back_populates="group_goal")
    
    __table_args__ = (
        CheckConstraint("target_amount > 0", name="check_target_amount_positive"),
        CheckConstraint("current_amount >= 0", name="check_current_amount_non_negative"),
        CheckConstraint("progress_percentage >= 0 AND progress_percentage <= 100", 
                       name="check_progress_percentage_valid"),
        CheckConstraint("maximum_participants IS NULL OR maximum_participants >= minimum_participants", 
                       name="check_max_participants_valid"),
    )
    
    @property
    def progress_percentage_calculated(self) -> float:
        """Calculate current progress percentage"""
        if self.target_amount <= 0:
            return 0.0
        return min(100.0, (self.current_amount / self.target_amount) * 100)
    
    @property
    def days_remaining(self) -> int:
        """Calculate days remaining until target date"""
        if self.target_date:
            delta = self.target_date - datetime.utcnow()
            return max(0, delta.days)
        return 0
    
    @property
    def can_accept_participants(self) -> bool:
        """Check if goal can accept new participants"""
        if self.status != GroupGoalStatus.ACTIVE:
            return False
        
        if self.maximum_participants:
            return self.total_participants < self.maximum_participants
        
        return True
    
    def add_contribution(self, amount: float):
        """Add contribution to goal"""
        self.current_amount += amount
        self.progress_percentage = self.progress_percentage_calculated
        self.updated_at = datetime.utcnow()
        
        # Auto-complete if target reached
        if self.current_amount >= self.target_amount and self.status == GroupGoalStatus.ACTIVE:
            self.complete_goal()
    
    def complete_goal(self):
        """Mark goal as completed"""
        self.status = GroupGoalStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        self.actual_completion_amount = self.current_amount
        self.progress_percentage = 100.0
        self.success_rate = min(100.0, (self.current_amount / self.target_amount) * 100)
        self.updated_at = datetime.utcnow()
    
    def add_participant(self):
        """Increment participant count"""
        self.total_participants += 1
        self.active_participants += 1
        self.updated_at = datetime.utcnow()
    
    def remove_participant(self):
        """Decrement participant count"""
        if self.total_participants > 1:  # Don't go below creator
            self.total_participants -= 1
        if self.active_participants > 1:
            self.active_participants -= 1
        self.updated_at = datetime.utcnow()
    
    def calculate_suggested_individual_contribution(self) -> float:
        """Calculate suggested contribution per participant"""
        if self.total_participants <= 0:
            return self.target_amount
        
        remaining_amount = max(0, self.target_amount - self.current_amount)
        return remaining_amount / self.total_participants


class GroupGoalParticipation(SocialBase):
    """User participation in group savings goals"""
    
    __tablename__ = "group_goal_participations"
    
    # References
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    group_goal_id = Column(UUID(as_uuid=True), ForeignKey("group_savings_goals.id"), nullable=False)
    
    # Participation details
    role = Column(Enum(ParticipantRole), default=ParticipantRole.PARTICIPANT, nullable=False)
    joined_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    invited_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Contribution tracking
    total_contributed = Column(Float, default=0.0, nullable=False)
    contribution_count = Column(Integer, default=0, nullable=False)
    last_contribution_at = Column(DateTime, nullable=True)
    
    # Commitment and targets
    personal_target = Column(Float, nullable=True)  # Individual commitment
    personal_deadline = Column(DateTime, nullable=True)
    contribution_frequency = Column(String(20), nullable=True)  # "weekly", "monthly", etc.
    
    # Participation status
    is_active = Column(Boolean, default=True, nullable=False)
    is_approved = Column(Boolean, default=False, nullable=False)  # For approval-required groups
    approved_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    
    # Communication preferences
    wants_notifications = Column(Boolean, default=True, nullable=False)
    wants_milestone_alerts = Column(Boolean, default=True, nullable=False)
    wants_deadline_reminders = Column(Boolean, default=True, nullable=False)
    
    # Personal notes and motivation
    personal_notes = Column(Text, nullable=True)
    motivation_statement = Column(Text, nullable=True)
    
    # Benefit allocation (for unequal benefit scenarios)
    benefit_percentage = Column(Float, nullable=True)  # % of goal benefit they'll receive
    benefit_description = Column(Text, nullable=True)
    
    # Performance tracking
    contribution_consistency_score = Column(Float, nullable=True)  # 0-100 based on regular contributions
    engagement_score = Column(Float, nullable=True)  # Based on participation in discussions, etc.
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    group_goal = relationship("GroupSavingsGoal", back_populates="participations")
    inviter = relationship("User", foreign_keys=[invited_by_user_id])
    approver = relationship("User", foreign_keys=[approved_by_user_id])
    
    __table_args__ = (
        CheckConstraint("total_contributed >= 0", name="check_total_contributed_non_negative"),
        CheckConstraint("contribution_count >= 0", name="check_contribution_count_non_negative"),
        CheckConstraint("benefit_percentage IS NULL OR (benefit_percentage >= 0 AND benefit_percentage <= 100)",
                       name="check_benefit_percentage_valid"),
    )
    
    @property
    def contribution_progress(self) -> float:
        """Calculate progress toward personal target"""
        if not self.personal_target or self.personal_target <= 0:
            return 0.0
        return min(100.0, (self.total_contributed / self.personal_target) * 100)
    
    @property
    def is_on_track(self) -> bool:
        """Check if participant is on track to meet their commitment"""
        if not self.personal_target or not self.personal_deadline:
            return True  # No specific commitment
        
        days_remaining = (self.personal_deadline - datetime.utcnow()).days
        if days_remaining <= 0:
            return self.total_contributed >= self.personal_target
        
        # Calculate expected progress based on time elapsed
        total_days = (self.personal_deadline - self.joined_at).days
        if total_days <= 0:
            return True
        
        days_elapsed = (datetime.utcnow() - self.joined_at).days
        expected_progress = (days_elapsed / total_days) * 100
        actual_progress = self.contribution_progress
        
        return actual_progress >= (expected_progress * 0.8)  # 80% tolerance
    
    def add_contribution(self, amount: float):
        """Add a contribution from this participant"""
        self.total_contributed += amount
        self.contribution_count += 1
        self.last_contribution_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        
        # Update group goal
        self.group_goal.add_contribution(amount)
    
    def approve_participation(self, approver_id: uuid.UUID):
        """Approve user's participation in the group goal"""
        self.is_approved = True
        self.approved_by_user_id = approver_id
        self.approved_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def leave_group(self):
        """Leave the group goal"""
        self.is_active = False
        self.updated_at = datetime.utcnow()
        self.group_goal.remove_participant()
    
    def update_engagement_score(self, score: float):
        """Update engagement score based on participation activities"""
        self.engagement_score = max(0.0, min(100.0, score))
        self.updated_at = datetime.utcnow()
    
    def calculate_contribution_consistency(self) -> float:
        """Calculate how consistent the user's contributions have been"""
        if self.contribution_count < 2:
            return 100.0 if self.contribution_count > 0 else 0.0
        
        # This would typically involve analyzing contribution patterns over time
        # For now, return a simple calculation based on frequency vs. target
        if not self.contribution_frequency:
            return 50.0  # Default for no frequency set
        
        # Simplified calculation - in reality would analyze actual contribution dates
        days_since_joined = (datetime.utcnow() - self.joined_at).days
        
        if self.contribution_frequency == "weekly":
            expected_contributions = max(1, days_since_joined // 7)
        elif self.contribution_frequency == "monthly":
            expected_contributions = max(1, days_since_joined // 30)
        else:
            expected_contributions = 1
        
        consistency = min(100.0, (self.contribution_count / expected_contributions) * 100)
        self.contribution_consistency_score = consistency
        return consistency