"""
Schemas for anonymous goal sharing and templates
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator
from uuid import UUID

from .social_base import SocialBaseResponse, EngagementMetrics, AnonymousAuthor, SocialListResponse


class AnonymousGoalShareCreate(BaseModel):
    """Schema for creating anonymous goal share"""
    
    # Option 1: Create from existing goal
    goal_id: Optional[UUID] = None
    
    # Option 2: Create from manual data
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    category: Optional[str] = None
    target_amount: Optional[float] = Field(None, gt=0)
    current_progress: Optional[float] = Field(None, ge=0, le=100)
    target_year: Optional[int] = Field(None, ge=2024, le=2050)
    target_quarter: Optional[int] = Field(None, ge=1, le=4)
    
    # Optional success story elements
    is_completed: bool = False
    completion_date: Optional[datetime] = None
    strategy: Optional[str] = Field(None, max_length=1000)
    tips: Optional[str] = Field(None, max_length=1000)
    challenges: Optional[str] = Field(None, max_length=1000)
    verification_proof: Optional[str] = Field(None, max_length=500)
    
    # Tagging
    tags: Optional[List[str]] = Field(default_factory=list, max_items=10)
    
    # Privacy settings
    allow_demographic_sharing: bool = True
    anonymize_amounts: bool = True
    
    @validator('tags')
    def validate_tags(cls, v):
        if v:
            # Clean and validate tags
            cleaned_tags = []
            for tag in v:
                if isinstance(tag, str) and len(tag.strip()) > 0:
                    cleaned_tags.append(tag.strip().lower()[:50])
            return cleaned_tags[:10]  # Limit to 10 tags
        return []
    
    @validator('goal_id', 'title', 'category', 'target_amount')
    def validate_creation_data(cls, v, values):
        # Either goal_id must be provided, or manual data
        if 'goal_id' in values and values['goal_id']:
            return v
        
        # If no goal_id, then manual data is required
        if not values.get('goal_id'):
            if not values.get('title') or not values.get('category') or not values.get('target_amount'):
                raise ValueError("When not using existing goal, title, category, and target_amount are required")
        
        return v
    
    class Config:
        from_attributes = True


class AnonymousGoalShareResponse(SocialBaseResponse):
    """Response schema for anonymous goal share"""
    
    goal_category: str
    goal_title: str
    goal_description: Optional[str] = None
    target_amount_range: Optional[str] = None
    target_date_year: Optional[int] = None
    target_date_quarter: Optional[int] = None
    current_progress_percentage: float
    is_goal_completed: bool
    completion_date: Optional[datetime] = None
    
    # Success story elements
    strategy_description: Optional[str] = None
    tips_and_lessons: Optional[str] = None
    challenges_faced: Optional[str] = None
    is_verified_completion: bool = False
    
    # Community engagement
    engagement: EngagementMetrics
    inspiration_votes: int = 0
    
    # Tags and categorization
    tags: List[str] = Field(default_factory=list)
    
    # Anonymous author info (privacy-preserving)
    anonymous_author: AnonymousAuthor
    
    class Config:
        from_attributes = True


class GoalInspirationItem(BaseModel):
    """Individual item in goal inspiration feed"""
    
    id: UUID
    type: str = "anonymous_goal_share"
    title: str
    content: Optional[str] = None
    category: str
    progress: float
    is_completed: bool
    tags: List[str] = Field(default_factory=list)
    engagement: EngagementMetrics
    timestamp: datetime
    relevance_score: float
    anonymous_author: AnonymousAuthor
    
    # Success story elements (if completed)
    success_story: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True


class GoalInspirationFeedResponse(SocialListResponse[GoalInspirationItem]):
    """Response schema for goal inspiration feed"""
    
    # Additional feed metadata
    personalization_applied: bool = True
    user_interests: Optional[List[str]] = None
    available_filters: Dict[str, List[str]] = Field(default_factory=dict)
    
    class Config:
        from_attributes = True


class GoalTemplateResponse(BaseModel):
    """Response schema for goal template"""
    
    id: UUID
    title: str
    category: str
    target_amount_range: str
    typical_timeline: Dict[str, Optional[int]]  # year, quarter
    strategy: Optional[str] = None
    tips: Optional[str] = None
    common_challenges: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    success_rate_indicator: float  # 0-5 scale
    
    # Demographic info for template
    demographics: Dict[str, List[str]] = Field(default_factory=dict)
    
    # Usage statistics
    template_usage_count: Optional[int] = None
    average_success_rate: Optional[float] = None
    
    class Config:
        from_attributes = True


class GoalTemplateListResponse(SocialListResponse[GoalTemplateResponse]):
    """Response for goal template listings"""
    
    # Template-specific metadata
    categories: List[str] = Field(default_factory=list)
    popular_tags: List[str] = Field(default_factory=list)
    
    class Config:
        from_attributes = True


class GoalLikeResponse(BaseModel):
    """Response for goal like/inspiration vote actions"""
    
    success: bool = True
    new_count: int
    user_action: str  # "liked", "inspired", "removed_like", etc.
    
    class Config:
        from_attributes = True


class GoalProgressUpdate(BaseModel):
    """Schema for updating goal progress"""
    
    progress_percentage: float = Field(ge=0, le=100)
    is_completed: bool = False
    
    # Completion data (if marking as completed)
    completion_date: Optional[datetime] = None
    tips_learned: Optional[str] = Field(None, max_length=1000)
    challenges_overcome: Optional[str] = Field(None, max_length=1000)
    verification_proof: Optional[str] = Field(None, max_length=500)
    
    class Config:
        from_attributes = True


class CommunityChallenge(BaseModel):
    """Community goal challenge response"""
    
    category: str
    target_range: str
    participant_count: int
    average_progress: float
    challenge_type: str
    description: str
    
    # Challenge timeline (if applicable)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    
    # Participation info
    user_eligible: bool = True
    user_participating: bool = False
    
    class Config:
        from_attributes = True


class CommunityChallengesResponse(BaseModel):
    """Response for community challenges"""
    
    active_challenges: List[CommunityChallenge]
    upcoming_challenges: List[CommunityChallenge]
    user_challenge_history: Optional[List[Dict[str, Any]]] = None
    
    class Config:
        from_attributes = True