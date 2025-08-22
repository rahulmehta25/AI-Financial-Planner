"""
Financial goal model for tracking user objectives
"""

import uuid
from datetime import datetime, date
from sqlalchemy import Column, DateTime, String, Numeric, ForeignKey, Text, Date, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.database.base import Base


class Goal(Base):
    __tablename__ = "goals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Goal Information
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    goal_type = Column(String(50), nullable=False)  # retirement, emergency_fund, home_purchase, education, vacation, debt_payoff
    
    # Financial Details
    target_amount = Column(Numeric(15, 2), nullable=False)
    current_amount = Column(Numeric(15, 2), default=0)
    monthly_contribution = Column(Numeric(15, 2), default=0)
    
    # Timeline
    target_date = Column(Date, nullable=False)
    created_date = Column(Date, default=date.today)
    
    # Status and Priority
    status = Column(String(20), default="active")  # active, completed, paused, cancelled
    priority = Column(Integer, default=5)  # 1 (highest) to 10 (lowest)
    
    # Goal Configuration
    is_flexible_timeline = Column(Boolean, default=False)
    is_flexible_amount = Column(Boolean, default=False)
    automatic_adjustments = Column(Boolean, default=True)
    
    # Progress Tracking
    progress_percentage = Column(Numeric(5, 2), default=0)
    last_contribution_date = Column(Date, nullable=True)
    contribution_frequency = Column(String(20), default="monthly")  # weekly, monthly, quarterly, annually
    
    # Additional Configuration
    risk_level = Column(String(20), nullable=True)  # conservative, moderate, aggressive
    investment_strategy = Column(String(50), nullable=True)
    tax_considerations = Column(JSONB, nullable=True)
    milestones = Column(JSONB, nullable=True)  # Array of milestone objects
    
    # Notes and Tags
    notes = Column(Text, nullable=True)
    tags = Column(JSONB, nullable=True)  # Array of tags for categorization
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="goals")

    @property
    def days_remaining(self) -> int:
        """Calculate days remaining to reach target date"""
        if self.status == "completed":
            return 0
        return (self.target_date - date.today()).days

    @property
    def months_remaining(self) -> int:
        """Calculate months remaining to reach target date"""
        if self.status == "completed":
            return 0
        return max(1, self.days_remaining // 30)

    @property
    def amount_remaining(self) -> float:
        """Calculate amount remaining to reach goal"""
        return max(0, float(self.target_amount) - float(self.current_amount or 0))

    @property
    def required_monthly_contribution(self) -> float:
        """Calculate required monthly contribution to reach goal on time"""
        if self.status == "completed" or self.months_remaining <= 0:
            return 0
        return self.amount_remaining / self.months_remaining

    @property
    def progress_status(self) -> str:
        """Get progress status description"""
        if self.status == "completed":
            return "completed"
        elif self.progress_percentage >= 100:
            return "achieved"
        elif self.progress_percentage >= 75:
            return "on_track"
        elif self.progress_percentage >= 50:
            return "behind"
        elif self.progress_percentage >= 25:
            return "significantly_behind"
        else:
            return "just_started"

    def update_progress(self):
        """Update progress percentage based on current amount"""
        if self.target_amount and self.target_amount > 0:
            self.progress_percentage = min(100, (float(self.current_amount or 0) / float(self.target_amount)) * 100)
        else:
            self.progress_percentage = 0