"""
User social profiles and privacy settings models
"""

import uuid
from datetime import datetime
from sqlalchemy import (
    Boolean, Column, DateTime, String, Text, Integer, 
    Enum, ForeignKey, JSON, Float
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum

from .base import SocialBase


class PrivacyLevel(PyEnum):
    """Privacy levels for user data sharing"""
    PUBLIC = "public"
    COMMUNITY_ONLY = "community_only" 
    FRIENDS_ONLY = "friends_only"
    MENTORS_ONLY = "mentors_only"
    PRIVATE = "private"


class SharingPreference(PyEnum):
    """What data users are willing to share"""
    NONE = "none"
    GOALS_ONLY = "goals_only"
    PROGRESS_ONLY = "progress_only"
    ACHIEVEMENTS_ONLY = "achievements_only"
    CHALLENGES_ONLY = "challenges_only"
    ALL = "all"


class UserSocialProfile(SocialBase):
    """Extended social profile for users with community features"""
    
    __tablename__ = "user_social_profiles"
    
    # Link to main user
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, unique=True)
    
    # Social profile information
    display_name = Column(String(100), nullable=True)  # Optional pseudonym
    bio = Column(Text, nullable=True)
    avatar_url = Column(Text, nullable=True)
    location = Column(String(100), nullable=True)  # General location (city/state)
    
    # Community stats
    reputation_score = Column(Integer, default=0, nullable=False)
    total_contributions = Column(Integer, default=0, nullable=False)
    helpful_votes_received = Column(Integer, default=0, nullable=False)
    challenges_completed = Column(Integer, default=0, nullable=False)
    
    # Social connections
    following_count = Column(Integer, default=0, nullable=False)
    followers_count = Column(Integer, default=0, nullable=False)
    
    # Engagement metrics
    last_active_at = Column(DateTime, default=datetime.utcnow)
    posts_count = Column(Integer, default=0, nullable=False)
    comments_count = Column(Integer, default=0, nullable=False)
    
    # Financial experience level
    experience_level = Column(Enum(
        "beginner", "intermediate", "advanced", "expert",
        name="experience_level"
    ), default="beginner")
    
    # Areas of expertise/interest (for mentorship)
    expertise_areas = Column(JSON, default=list)  # ["budgeting", "investing", "retirement"]
    interest_areas = Column(JSON, default=list)   # Areas they want to learn about
    
    # Achievement badges
    achievement_badges = Column(JSON, default=list)  # ["first_goal", "consistent_saver", etc.]
    
    # Relationships
    user = relationship("User", back_populates="social_profile")
    privacy_settings = relationship("UserPrivacySettings", back_populates="user_profile", uselist=False)
    mentor_profile = relationship("MentorProfile", back_populates="user_profile", uselist=False)
    
    def update_reputation(self, points: int):
        """Update reputation score"""
        self.reputation_score = max(0, self.reputation_score + points)
        self.updated_at = datetime.utcnow()
    
    def add_achievement(self, badge_name: str):
        """Add achievement badge if not already earned"""
        if badge_name not in self.achievement_badges:
            self.achievement_badges.append(badge_name)
            self.updated_at = datetime.utcnow()
    
    def update_last_active(self):
        """Update last active timestamp"""
        self.last_active_at = datetime.utcnow()


class UserPrivacySettings(SocialBase):
    """Privacy settings for user social features"""
    
    __tablename__ = "user_privacy_settings"
    
    # Link to user profile
    user_profile_id = Column(UUID(as_uuid=True), ForeignKey("user_social_profiles.id"), nullable=False, unique=True)
    
    # Profile visibility
    profile_visibility = Column(Enum(PrivacyLevel), default=PrivacyLevel.COMMUNITY_ONLY, nullable=False)
    
    # Goal sharing preferences
    goal_sharing_level = Column(Enum(PrivacyLevel), default=PrivacyLevel.COMMUNITY_ONLY, nullable=False)
    share_goal_amounts = Column(Boolean, default=False, nullable=False)
    share_goal_progress = Column(Boolean, default=True, nullable=False)
    share_goal_achievements = Column(Boolean, default=True, nullable=False)
    
    # Financial data sharing
    share_age_range = Column(Boolean, default=True, nullable=False)
    share_income_range = Column(Boolean, default=False, nullable=False)
    share_net_worth_range = Column(Boolean, default=False, nullable=False)
    share_investment_types = Column(Boolean, default=True, nullable=False)
    
    # Community participation
    allow_mentorship_requests = Column(Boolean, default=True, nullable=False)
    allow_direct_messages = Column(Boolean, default=True, nullable=False)
    allow_challenge_invites = Column(Boolean, default=True, nullable=False)
    allow_group_goal_invites = Column(Boolean, default=True, nullable=False)
    
    # Data anonymization preferences
    anonymize_in_comparisons = Column(Boolean, default=True, nullable=False)
    anonymize_in_leaderboards = Column(Boolean, default=False, nullable=False)
    anonymize_success_stories = Column(Boolean, default=True, nullable=False)
    
    # Communication preferences
    email_community_updates = Column(Boolean, default=True, nullable=False)
    email_mentor_messages = Column(Boolean, default=True, nullable=False)
    email_challenge_notifications = Column(Boolean, default=True, nullable=False)
    push_social_notifications = Column(Boolean, default=True, nullable=False)
    
    # Data sharing restrictions
    sharing_preferences = Column(Enum(SharingPreference), default=SharingPreference.GOALS_ONLY, nullable=False)
    blocked_users = Column(JSON, default=list)  # List of user IDs
    restricted_keywords = Column(JSON, default=list)  # Keywords to filter from sharing
    
    # Relationships
    user_profile = relationship("UserSocialProfile", back_populates="privacy_settings")
    
    def can_share_with_user(self, target_user_id: uuid.UUID, relationship_type: str = "community") -> bool:
        """Check if user can share data with target user"""
        if str(target_user_id) in self.blocked_users:
            return False
            
        if self.sharing_preferences == SharingPreference.NONE:
            return False
            
        # Check privacy level requirements
        if self.profile_visibility == PrivacyLevel.PRIVATE:
            return False
        elif self.profile_visibility == PrivacyLevel.FRIENDS_ONLY:
            return relationship_type in ["friend", "mentor"]
        elif self.profile_visibility == PrivacyLevel.MENTORS_ONLY:
            return relationship_type == "mentor"
        elif self.profile_visibility == PrivacyLevel.COMMUNITY_ONLY:
            return relationship_type in ["community", "friend", "mentor"]
        
        return True  # PUBLIC
    
    def block_user(self, user_id: uuid.UUID):
        """Block a user from seeing shared content"""
        user_id_str = str(user_id)
        if user_id_str not in self.blocked_users:
            self.blocked_users.append(user_id_str)
            self.updated_at = datetime.utcnow()
    
    def unblock_user(self, user_id: uuid.UUID):
        """Unblock a user"""
        user_id_str = str(user_id)
        if user_id_str in self.blocked_users:
            self.blocked_users.remove(user_id_str)
            self.updated_at = datetime.utcnow()