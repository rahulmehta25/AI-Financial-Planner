"""
Base schemas for social platform API responses
"""

from typing import Optional, List, Generic, TypeVar, Any, Dict
from datetime import datetime
from pydantic import BaseModel, Field
from uuid import UUID

T = TypeVar('T')


class SocialBaseResponse(BaseModel):
    """Base response schema for social platform entities"""
    id: UUID
    created_at: datetime
    updated_at: datetime
    is_active: bool = True
    is_public: bool = True
    is_flagged: bool = False
    
    class Config:
        from_attributes = True


class SocialCreateResponse(BaseModel):
    """Response schema for create operations"""
    id: UUID
    success: bool = True
    message: str = "Created successfully"
    
    class Config:
        from_attributes = True


class SocialListResponse(BaseModel, Generic[T]):
    """Generic paginated list response"""
    items: List[T]
    total: int
    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=20, ge=1, le=100)
    has_next: bool = False
    has_prev: bool = False
    
    class Config:
        from_attributes = True


class EngagementMetrics(BaseModel):
    """Common engagement metrics"""
    likes: int = 0
    comments: int = 0
    views: int = 0
    shares: int = 0
    
    class Config:
        from_attributes = True


class PrivacySettings(BaseModel):
    """Privacy settings for various content types"""
    is_public: bool = True
    share_with_community: bool = True
    share_with_mentors_only: bool = False
    anonymize_data: bool = True
    
    class Config:
        from_attributes = True


class ContentModerationInfo(BaseModel):
    """Content moderation information"""
    is_flagged: bool = False
    is_approved: bool = True
    moderation_notes: Optional[str] = None
    moderated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class AnonymousAuthor(BaseModel):
    """Anonymous author information for privacy-preserving content"""
    anonymous_id: str
    experience_level: Optional[str] = None
    age_group: Optional[str] = None
    income_range: Optional[str] = None
    region: Optional[str] = None
    reputation_score: Optional[int] = None
    
    class Config:
        from_attributes = True


class ErrorResponse(BaseModel):
    """Standard error response"""
    error: bool = True
    message: str
    details: Optional[Dict[str, Any]] = None
    error_code: Optional[str] = None
    
    class Config:
        from_attributes = True


class SuccessResponse(BaseModel):
    """Standard success response"""
    success: bool = True
    message: str
    data: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True


class FilterOptions(BaseModel):
    """Common filter options for list endpoints"""
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    is_public: Optional[bool] = None
    sort_by: str = "created_at"
    sort_order: str = Field(default="desc", regex="^(asc|desc)$")
    
    class Config:
        from_attributes = True