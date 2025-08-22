"""
Social platform API schemas
"""

from .social_base import SocialBaseResponse, SocialCreateResponse, SocialListResponse
from .user_social import UserSocialProfileResponse, UserPrivacySettingsUpdate, UserSocialProfileUpdate
from .goal_sharing import (
    AnonymousGoalShareCreate, AnonymousGoalShareResponse, 
    GoalInspirationFeedResponse, GoalTemplateResponse
)
from .peer_comparison import PeerComparisonResponse, DemographicInsightsResponse
from .community_forums import (
    ForumCategoryResponse, ForumTopicCreate, ForumTopicResponse,
    ForumPostCreate, ForumPostResponse, ModerationReportCreate
)
from .group_goals import (
    GroupGoalCreate, GroupGoalResponse, GroupGoalParticipationCreate,
    GroupGoalParticipationResponse
)
from .mentorship import (
    MentorProfileCreate, MentorProfileResponse, MentorshipMatchCreate,
    MentorshipMatchResponse, MentorshipSessionCreate, MentorshipSessionResponse
)
from .social_feed import SocialFeedResponse, ActivityTrackingCreate

__all__ = [
    # Base schemas
    "SocialBaseResponse", "SocialCreateResponse", "SocialListResponse",
    
    # User social schemas
    "UserSocialProfileResponse", "UserPrivacySettingsUpdate", "UserSocialProfileUpdate",
    
    # Goal sharing schemas
    "AnonymousGoalShareCreate", "AnonymousGoalShareResponse", 
    "GoalInspirationFeedResponse", "GoalTemplateResponse",
    
    # Peer comparison schemas
    "PeerComparisonResponse", "DemographicInsightsResponse",
    
    # Community forum schemas
    "ForumCategoryResponse", "ForumTopicCreate", "ForumTopicResponse",
    "ForumPostCreate", "ForumPostResponse", "ModerationReportCreate",
    
    # Group goals schemas
    "GroupGoalCreate", "GroupGoalResponse", "GroupGoalParticipationCreate",
    "GroupGoalParticipationResponse",
    
    # Mentorship schemas
    "MentorProfileCreate", "MentorProfileResponse", "MentorshipMatchCreate",
    "MentorshipMatchResponse", "MentorshipSessionCreate", "MentorshipSessionResponse",
    
    # Social feed schemas
    "SocialFeedResponse", "ActivityTrackingCreate"
]