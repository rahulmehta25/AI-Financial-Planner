"""
Mentorship matching and session management models
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


class MentorshipType(PyEnum):
    """Types of mentorship relationships"""
    ONE_ON_ONE = "one_on_one"
    GROUP_MENTORING = "group_mentoring"
    PEER_MENTORING = "peer_mentoring"
    REVERSE_MENTORING = "reverse_mentoring"
    MICRO_MENTORING = "micro_mentoring"


class ExpertiseLevel(PyEnum):
    """Levels of expertise in financial areas"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"
    PROFESSIONAL = "professional"


class MentorshipStatus(PyEnum):
    """Status of mentorship relationship"""
    PENDING = "pending"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class SessionStatus(PyEnum):
    """Status of mentorship sessions"""
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"
    RESCHEDULED = "rescheduled"


class CommunicationPreference(PyEnum):
    """Preferred communication methods"""
    VIDEO_CALL = "video_call"
    PHONE_CALL = "phone_call"
    TEXT_CHAT = "text_chat"
    EMAIL = "email"
    IN_PERSON = "in_person"


class MentorProfile(SocialBase):
    """Extended profile for users offering mentorship"""
    
    __tablename__ = "mentor_profiles"
    
    # Link to user social profile
    user_profile_id = Column(UUID(as_uuid=True), ForeignKey("user_social_profiles.id"), nullable=False, unique=True)
    
    # Mentor information
    is_available = Column(Boolean, default=True, nullable=False)
    is_verified_mentor = Column(Boolean, default=False, nullable=False)
    verification_date = Column(DateTime, nullable=True)
    
    # Professional background
    professional_title = Column(String(100), nullable=True)
    company = Column(String(100), nullable=True)
    years_of_experience = Column(Integer, nullable=True)
    certifications = Column(JSON, default=list)  # Financial certifications
    education_background = Column(JSON, default=list)
    
    # Expertise areas and levels
    expertise_areas = Column(JSON, nullable=False)  # List of {"area": "budgeting", "level": "expert"}
    specializations = Column(JSON, default=list)   # Specific specializations
    target_demographics = Column(JSON, default=list)  # Who they prefer to mentor
    
    # Mentorship preferences
    mentorship_types = Column(JSON, default=list)  # Types they offer
    max_mentees = Column(Integer, default=5, nullable=False)
    current_mentees = Column(Integer, default=0, nullable=False)
    session_duration_minutes = Column(Integer, default=60, nullable=False)
    
    # Availability and scheduling
    timezone = Column(String(50), nullable=True)
    available_hours = Column(JSON, default=dict)  # Weekly availability schedule
    communication_preferences = Column(JSON, default=list)  # Preferred methods
    
    # Pricing and commitment
    is_pro_bono = Column(Boolean, default=True, nullable=False)
    hourly_rate = Column(Float, nullable=True)  # If not pro bono
    minimum_commitment_weeks = Column(Integer, default=4, nullable=False)
    maximum_commitment_weeks = Column(Integer, nullable=True)
    
    # Mentor approach and style
    mentoring_philosophy = Column(Text, nullable=True)
    approach_description = Column(Text, nullable=True)
    success_story_examples = Column(JSON, default=list)
    
    # Performance metrics
    total_mentees_helped = Column(Integer, default=0, nullable=False)
    average_session_rating = Column(Float, nullable=True)
    total_sessions_completed = Column(Integer, default=0, nullable=False)
    completion_rate = Column(Float, nullable=True)  # % of mentorships completed successfully
    
    # Community reputation
    mentor_rating = Column(Float, nullable=True)  # Overall mentor rating
    total_reviews = Column(Integer, default=0, nullable=False)
    recommended_by_count = Column(Integer, default=0, nullable=False)
    
    # Response and engagement
    average_response_time_hours = Column(Float, nullable=True)
    last_active_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Featured status
    is_featured_mentor = Column(Boolean, default=False, nullable=False)
    featured_reason = Column(Text, nullable=True)
    
    # Relationships
    user_profile = relationship("UserSocialProfile", back_populates="mentor_profile")
    mentorship_matches = relationship("MentorshipMatch", back_populates="mentor_profile")
    
    __table_args__ = (
        CheckConstraint("max_mentees > 0", name="check_max_mentees_positive"),
        CheckConstraint("current_mentees >= 0", name="check_current_mentees_non_negative"),
        CheckConstraint("current_mentees <= max_mentees", name="check_current_within_max"),
        CheckConstraint("session_duration_minutes > 0", name="check_session_duration_positive"),
        CheckConstraint("average_session_rating IS NULL OR (average_session_rating >= 1 AND average_session_rating <= 5)",
                       name="check_session_rating_valid"),
        CheckConstraint("mentor_rating IS NULL OR (mentor_rating >= 1 AND mentor_rating <= 5)",
                       name="check_mentor_rating_valid"),
    )
    
    @property
    def is_accepting_mentees(self) -> bool:
        """Check if mentor is currently accepting new mentees"""
        return (
            self.is_available and
            self.current_mentees < self.max_mentees and
            self.is_active
        )
    
    @property
    def expertise_level_score(self) -> float:
        """Calculate overall expertise level score"""
        if not self.expertise_areas:
            return 0.0
        
        level_scores = {"beginner": 1, "intermediate": 2, "advanced": 3, "expert": 4, "professional": 5}
        total_score = sum(level_scores.get(area.get("level", "beginner"), 1) for area in self.expertise_areas)
        return total_score / len(self.expertise_areas)
    
    def add_mentee(self):
        """Increment current mentee count"""
        if self.current_mentees < self.max_mentees:
            self.current_mentees += 1
            self.updated_at = datetime.utcnow()
    
    def remove_mentee(self):
        """Decrement current mentee count"""
        if self.current_mentees > 0:
            self.current_mentees -= 1
            self.updated_at = datetime.utcnow()
    
    def update_rating(self, new_rating: float):
        """Update mentor rating with new review"""
        if self.mentor_rating is None:
            self.mentor_rating = new_rating
            self.total_reviews = 1
        else:
            # Calculate weighted average
            total_points = self.mentor_rating * self.total_reviews + new_rating
            self.total_reviews += 1
            self.mentor_rating = total_points / self.total_reviews
        
        self.updated_at = datetime.utcnow()
    
    def can_mentor_in_area(self, area: str, required_level: str = "intermediate") -> bool:
        """Check if mentor has expertise in a specific area"""
        level_hierarchy = ["beginner", "intermediate", "advanced", "expert", "professional"]
        required_index = level_hierarchy.index(required_level)
        
        for expertise in self.expertise_areas:
            if (expertise.get("area") == area and 
                level_hierarchy.index(expertise.get("level", "beginner")) >= required_index):
                return True
        
        return False


class MentorshipMatch(SocialBase):
    """Mentorship relationship between mentor and mentee"""
    
    __tablename__ = "mentorship_matches"
    
    # Participants
    mentor_profile_id = Column(UUID(as_uuid=True), ForeignKey("mentor_profiles.id"), nullable=False)
    mentee_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Relationship details
    mentorship_type = Column(Enum(MentorshipType), default=MentorshipType.ONE_ON_ONE, nullable=False)
    status = Column(Enum(MentorshipStatus), default=MentorshipStatus.PENDING, nullable=False)
    
    # Timeline
    requested_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    started_at = Column(DateTime, nullable=True)
    ended_at = Column(DateTime, nullable=True)
    planned_duration_weeks = Column(Integer, nullable=False)
    
    # Focus areas and goals
    focus_areas = Column(JSON, nullable=False)  # What mentee wants to work on
    mentee_goals = Column(JSON, default=list)   # Specific goals for mentorship
    success_criteria = Column(JSON, default=list)  # How to measure success
    
    # Communication preferences
    preferred_communication = Column(Enum(CommunicationPreference), nullable=False)
    session_frequency = Column(String(20), default="weekly", nullable=False)  # "weekly", "biweekly", etc.
    preferred_session_time = Column(String(50), nullable=True)  # "weekday_evening", "weekend_morning", etc.
    
    # Progress tracking
    sessions_completed = Column(Integer, default=0, nullable=False)
    total_planned_sessions = Column(Integer, nullable=True)
    goals_achieved = Column(Integer, default=0, nullable=False)
    total_goals = Column(Integer, default=0, nullable=False)
    
    # Feedback and ratings
    mentee_satisfaction_rating = Column(Float, nullable=True)  # 1-5 rating from mentee
    mentor_satisfaction_rating = Column(Float, nullable=True)  # 1-5 rating from mentor
    relationship_effectiveness_score = Column(Float, nullable=True)  # System calculated
    
    # Match quality and compatibility
    compatibility_score = Column(Float, nullable=True)  # Algorithm-calculated match quality
    personality_match_score = Column(Float, nullable=True)
    communication_style_match = Column(Float, nullable=True)
    
    # Administrative
    is_paid_mentorship = Column(Boolean, default=False, nullable=False)
    hourly_rate_agreed = Column(Float, nullable=True)
    payment_terms = Column(Text, nullable=True)
    
    # Completion details
    completion_reason = Column(Text, nullable=True)
    mentor_final_notes = Column(Text, nullable=True)
    mentee_final_notes = Column(Text, nullable=True)
    would_mentor_again = Column(Boolean, nullable=True)  # From mentor perspective
    would_mentee_again = Column(Boolean, nullable=True)  # From mentee perspective
    
    # Relationships
    mentor_profile = relationship("MentorProfile", back_populates="mentorship_matches")
    mentee = relationship("User", backref="mentorship_relationships")
    sessions = relationship("MentorshipSession", back_populates="mentorship_match", cascade="all, delete-orphan")
    
    __table_args__ = (
        CheckConstraint("planned_duration_weeks > 0", name="check_duration_positive"),
        CheckConstraint("mentee_satisfaction_rating IS NULL OR (mentee_satisfaction_rating >= 1 AND mentee_satisfaction_rating <= 5)",
                       name="check_mentee_rating_valid"),
        CheckConstraint("mentor_satisfaction_rating IS NULL OR (mentor_satisfaction_rating >= 1 AND mentor_satisfaction_rating <= 5)",
                       name="check_mentor_rating_valid"),
    )
    
    @property
    def is_active(self) -> bool:
        """Check if mentorship is currently active"""
        return self.status == MentorshipStatus.ACTIVE
    
    @property
    def progress_percentage(self) -> float:
        """Calculate overall progress percentage"""
        if not self.total_planned_sessions:
            return 0.0
        return min(100.0, (self.sessions_completed / self.total_planned_sessions) * 100)
    
    @property
    def goal_completion_rate(self) -> float:
        """Calculate goal completion rate"""
        if self.total_goals == 0:
            return 0.0
        return (self.goals_achieved / self.total_goals) * 100
    
    def start_mentorship(self):
        """Start the mentorship relationship"""
        self.status = MentorshipStatus.ACTIVE
        self.started_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        
        # Update mentor's current mentee count
        self.mentor_profile.add_mentee()
    
    def complete_mentorship(self, reason: str = None):
        """Complete the mentorship relationship"""
        self.status = MentorshipStatus.COMPLETED
        self.ended_at = datetime.utcnow()
        if reason:
            self.completion_reason = reason
        self.updated_at = datetime.utcnow()
        
        # Update mentor's current mentee count
        self.mentor_profile.remove_mentee()
    
    def add_session(self):
        """Increment completed sessions count"""
        self.sessions_completed += 1
        self.updated_at = datetime.utcnow()
    
    def achieve_goal(self):
        """Mark a goal as achieved"""
        self.goals_achieved += 1
        self.updated_at = datetime.utcnow()


class MentorshipSession(SocialBase):
    """Individual mentorship sessions"""
    
    __tablename__ = "mentorship_sessions"
    
    # References
    mentorship_match_id = Column(UUID(as_uuid=True), ForeignKey("mentorship_matches.id"), nullable=False)
    
    # Session details
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    session_number = Column(Integer, nullable=False)
    
    # Scheduling
    scheduled_start_time = Column(DateTime, nullable=False)
    scheduled_end_time = Column(DateTime, nullable=False)
    actual_start_time = Column(DateTime, nullable=True)
    actual_end_time = Column(DateTime, nullable=True)
    
    # Session metadata
    communication_method = Column(Enum(CommunicationPreference), nullable=False)
    meeting_link = Column(String(500), nullable=True)  # Video call link
    location = Column(String(200), nullable=True)  # For in-person meetings
    
    # Session content
    agenda = Column(JSON, default=list)  # Planned topics
    topics_covered = Column(JSON, default=list)  # Actual topics discussed
    key_takeaways = Column(JSON, default=list)  # Important points
    action_items = Column(JSON, default=list)  # Follow-up tasks
    
    # Session status
    status = Column(Enum(SessionStatus), default=SessionStatus.SCHEDULED, nullable=False)
    cancellation_reason = Column(Text, nullable=True)
    rescheduled_from_session_id = Column(UUID(as_uuid=True), ForeignKey("mentorship_sessions.id"), nullable=True)
    
    # Feedback and ratings
    mentee_session_rating = Column(Float, nullable=True)  # 1-5 rating
    mentor_session_rating = Column(Float, nullable=True)  # 1-5 rating
    mentee_notes = Column(Text, nullable=True)
    mentor_notes = Column(Text, nullable=True)
    
    # Session preparation
    mentee_preparation_notes = Column(Text, nullable=True)
    mentor_preparation_notes = Column(Text, nullable=True)
    pre_session_questionnaire = Column(JSON, nullable=True)
    
    # Follow-up
    follow_up_required = Column(Boolean, default=False, nullable=False)
    follow_up_completed = Column(Boolean, default=False, nullable=False)
    next_session_focus = Column(Text, nullable=True)
    
    # Relationships
    mentorship_match = relationship("MentorshipMatch", back_populates="sessions")
    rescheduled_from = relationship("MentorshipSession", remote_side="MentorshipSession.id")
    
    __table_args__ = (
        CheckConstraint("scheduled_end_time > scheduled_start_time", name="check_scheduled_times_valid"),
        CheckConstraint("session_number > 0", name="check_session_number_positive"),
        CheckConstraint("mentee_session_rating IS NULL OR (mentee_session_rating >= 1 AND mentee_session_rating <= 5)",
                       name="check_mentee_session_rating_valid"),
        CheckConstraint("mentor_session_rating IS NULL OR (mentor_session_rating >= 1 AND mentor_session_rating <= 5)",
                       name="check_mentor_session_rating_valid"),
    )
    
    @property
    def duration_minutes(self) -> int:
        """Calculate scheduled session duration in minutes"""
        delta = self.scheduled_end_time - self.scheduled_start_time
        return int(delta.total_seconds() / 60)
    
    @property
    def actual_duration_minutes(self) -> int:
        """Calculate actual session duration in minutes"""
        if not (self.actual_start_time and self.actual_end_time):
            return 0
        delta = self.actual_end_time - self.actual_start_time
        return int(delta.total_seconds() / 60)
    
    @property
    def is_upcoming(self) -> bool:
        """Check if session is scheduled for the future"""
        return (
            self.status == SessionStatus.SCHEDULED and
            self.scheduled_start_time > datetime.utcnow()
        )
    
    @property
    def is_overdue(self) -> bool:
        """Check if session is overdue"""
        return (
            self.status == SessionStatus.SCHEDULED and
            self.scheduled_end_time < datetime.utcnow()
        )
    
    def start_session(self):
        """Mark session as started"""
        self.status = SessionStatus.IN_PROGRESS
        self.actual_start_time = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def complete_session(self, mentee_rating: float = None, mentor_rating: float = None):
        """Mark session as completed"""
        self.status = SessionStatus.COMPLETED
        self.actual_end_time = datetime.utcnow()
        
        if mentee_rating:
            self.mentee_session_rating = mentee_rating
        if mentor_rating:
            self.mentor_session_rating = mentor_rating
        
        self.updated_at = datetime.utcnow()
        
        # Update mentorship match session count
        self.mentorship_match.add_session()
    
    def cancel_session(self, reason: str = None):
        """Cancel the session"""
        self.status = SessionStatus.CANCELLED
        if reason:
            self.cancellation_reason = reason
        self.updated_at = datetime.utcnow()
    
    def reschedule_session(self, new_start_time: datetime, new_end_time: datetime):
        """Reschedule the session"""
        self.scheduled_start_time = new_start_time
        self.scheduled_end_time = new_end_time
        self.status = SessionStatus.RESCHEDULED
        self.updated_at = datetime.utcnow()