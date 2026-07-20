"""
Main social platform API router
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from uuid import UUID

from ...api.deps import get_current_user, get_db
from ...models.user import User
from ..schemas.goal_sharing import (
    AnonymousGoalShareCreate, AnonymousGoalShareResponse, 
    GoalInspirationFeedResponse, GoalTemplateListResponse,
    GoalProgressUpdate, CommunityChallengesResponse
)
from ..schemas.peer_comparison import (
    PeerComparisonResponse, DemographicInsightsResponse,
    UserComparisonTrendsResponse, BenchmarkComparisonResponse
)
from ..schemas.social_base import SuccessResponse, ErrorResponse

from ..services import (
    GoalSharingService, PeerComparisonService, ContentModerationService,
    SocialFeedService, AnonymizationService
)

# Create the main social platform router
social_router = APIRouter()

# Create sub-routers for different feature areas
goal_sharing_router = APIRouter(prefix="/goal-sharing", tags=["Anonymous Goal Sharing"])
peer_comparison_router = APIRouter(prefix="/peer-comparison", tags=["Peer Comparison"])
community_router = APIRouter(prefix="/community", tags=["Community Features"])
groups_router = APIRouter(prefix="/groups", tags=["Group Savings Goals"])
mentorship_router = APIRouter(prefix="/mentorship", tags=["Mentorship System"])
feed_router = APIRouter(prefix="/feed", tags=["Social Feed"])
moderation_router = APIRouter(prefix="/moderation", tags=["Content Moderation"])

# Include all sub-routers in the main router
social_router.include_router(goal_sharing_router)
social_router.include_router(peer_comparison_router)
social_router.include_router(community_router)
social_router.include_router(groups_router)
social_router.include_router(mentorship_router)
social_router.include_router(feed_router)
social_router.include_router(moderation_router)


# === ANONYMOUS GOAL SHARING ENDPOINTS ===

@goal_sharing_router.post("/", response_model=AnonymousGoalShareResponse)
async def create_anonymous_goal_share(
    share_data: AnonymousGoalShareCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create an anonymous goal share for community inspiration
    
    - **goal_id**: Share an existing goal (anonymized)
    - **manual data**: Create share from scratch with manual input
    - **privacy controls**: Control what demographic data is shared
    """
    try:
        service = GoalSharingService(db)
        
        if share_data.goal_id:
            share = service.create_anonymous_goal_share(
                user_id=current_user.id,
                goal_id=share_data.goal_id
            )
        else:
            share = service.create_anonymous_goal_share(
                user_id=current_user.id,
                goal_data=share_data.dict(exclude={'goal_id'})
            )
        
        return share
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to create goal share")


@goal_sharing_router.get("/inspiration", response_model=GoalInspirationFeedResponse)
async def get_goal_inspiration_feed(
    category: Optional[str] = Query(None, description="Filter by goal category"),
    age_group: Optional[str] = Query(None, description="Filter by age group"),
    income_range: Optional[str] = Query(None, description="Filter by income range"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get personalized goal inspiration feed with privacy-preserving comparisons
    
    - **Personalized**: Based on user's interests and experience level
    - **Anonymous**: All data is privacy-preserving
    - **Filterable**: By category, demographics, completion status
    """
    try:
        service = GoalSharingService(db)
        
        feed = service.get_goal_inspiration_feed(
            user_id=current_user.id,
            category=category,
            age_group=age_group,
            income_range=income_range,
            page=page,
            per_page=per_page
        )
        
        return feed
        
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to load inspiration feed")


@goal_sharing_router.get("/templates", response_model=GoalTemplateListResponse)
async def get_goal_templates(
    category: Optional[str] = Query(None, description="Filter by goal category"),
    popular_only: bool = Query(True, description="Only show popular templates"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get goal templates based on successful anonymous shares
    
    - **Evidence-based**: Templates from real successful goals
    - **Popular filtering**: Most successful and inspiring templates first
    - **Category specific**: Templates for specific financial goals
    """
    try:
        service = GoalSharingService(db)
        
        templates = service.get_goal_templates(
            category=category,
            popular_only=popular_only
        )
        
        return {"items": templates, "total": len(templates), "page": 1, "per_page": len(templates)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to load goal templates")


@goal_sharing_router.post("/{share_id}/like", response_model=SuccessResponse)
async def like_goal_share(
    share_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add like to anonymous goal share"""
    try:
        service = GoalSharingService(db)
        success = service.add_like(share_id, current_user.id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Goal share not found")
        
        return SuccessResponse(message="Goal share liked successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to like goal share")


@goal_sharing_router.post("/{share_id}/inspire", response_model=SuccessResponse)
async def add_inspiration_vote(
    share_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add inspiration vote to goal share"""
    try:
        service = GoalSharingService(db)
        success = service.add_inspiration_vote(share_id, current_user.id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Goal share not found")
        
        return SuccessResponse(message="Inspiration vote added successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to add inspiration vote")


@goal_sharing_router.get("/challenges", response_model=CommunityChallengesResponse)
async def get_community_challenges(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get community-wide goal challenges based on popular goals"""
    try:
        service = GoalSharingService(db)
        challenges = service.get_community_challenges()
        
        return {
            "active_challenges": challenges,
            "upcoming_challenges": [],  # Would be populated with scheduled challenges
            "user_challenge_history": None  # Could include user's participation history
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to load community challenges")


# === PEER COMPARISON ENDPOINTS ===

@peer_comparison_router.get("/", response_model=PeerComparisonResponse)
async def get_peer_comparison(
    force_refresh: bool = Query(False, description="Force refresh of comparison data"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive peer comparison with privacy protection
    
    - **Anonymous**: All comparisons are privacy-preserving
    - **Demographic matching**: Compared with similar age/income peers
    - **Comprehensive metrics**: Financial health, goals, behavior
    - **Actionable insights**: Personalized recommendations
    """
    try:
        service = PeerComparisonService(db)
        
        comparison = service.generate_peer_comparison(
            user_id=current_user.id,
            force_refresh=force_refresh
        )
        
        if not comparison:
            raise HTTPException(
                status_code=404, 
                detail="Unable to generate comparison - insufficient user data"
            )
        
        return comparison
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to generate peer comparison")


@peer_comparison_router.get("/demographics", response_model=DemographicInsightsResponse)
async def get_demographic_insights(
    age_group: Optional[str] = Query(None),
    income_range: Optional[str] = Query(None),
    region: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get aggregated insights for demographic groups
    
    - **Population insights**: How different demographics perform financially
    - **Anonymous aggregation**: All data is privacy-preserving
    - **Benchmarking**: Compare against broader population groups
    """
    try:
        service = PeerComparisonService(db)
        
        insights = service.get_demographic_insights(
            age_group=age_group,
            income_range=income_range,
            region=region
        )
        
        return insights
        
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to load demographic insights")


@peer_comparison_router.get("/trends", response_model=UserComparisonTrendsResponse)
async def get_user_comparison_trends(
    months: int = Query(12, ge=3, le=60, description="Number of months of history"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get user's comparison trends over time
    
    - **Progress tracking**: See how financial metrics improve over time
    - **Trend analysis**: Identify improving and declining areas
    - **Milestone tracking**: Celebrate achievements and identify next steps
    """
    try:
        service = PeerComparisonService(db)
        
        trends = service.get_user_comparison_trends(
            user_id=current_user.id,
            months=months
        )
        
        return trends
        
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to load comparison trends")


# === SOCIAL FEED ENDPOINTS ===

@feed_router.get("/", response_model=Dict[str, Any])
async def get_personalized_feed(
    feed_type: str = Query("all", regex="^(all|goals|community|groups|mentorship)$"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get personalized social feed with activity from all platform features
    
    - **Personalized**: Based on interests, connections, and activity
    - **Multi-source**: Goals, forums, groups, mentorship activities
    - **Privacy-respecting**: Only shows content user has permission to see
    """
    try:
        service = SocialFeedService(db)
        
        feed = service.get_personalized_feed(
            user_id=current_user.id,
            page=page,
            per_page=per_page,
            feed_type=feed_type
        )
        
        return feed
        
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to load social feed")


@feed_router.get("/trending", response_model=List[Dict[str, Any]])
async def get_trending_content(
    time_period: str = Query("week", regex="^(day|week|month)$"),
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get trending content across the platform
    
    - **Popular content**: Most engaged-with content in specified time period
    - **Cross-platform**: Trending goals, discussions, group activities
    - **Recency balanced**: Mix of recent and highly-engaged content
    """
    try:
        service = SocialFeedService(db)
        
        trending = service.get_trending_content(
            time_period=time_period,
            limit=limit
        )
        
        return trending
        
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to load trending content")


# === CONTENT MODERATION ENDPOINTS ===

@moderation_router.post("/report", response_model=SuccessResponse)
async def report_content(
    content_id: UUID,
    content_type: str = Query(..., regex="^(post|topic|goal_share|group)$"),
    reason: str = Query(..., description="Reason for report"),
    description: Optional[str] = Query(None, max_length=500),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Report content for moderation review
    
    - **Community safety**: Help maintain platform quality and safety
    - **Multiple content types**: Report posts, topics, goal shares, etc.
    - **Detailed reporting**: Provide context for moderation decisions
    """
    try:
        service = ContentModerationService(db)
        
        report = service.report_content(
            content_id=content_id,
            content_type=content_type,
            reported_by_user_id=current_user.id,
            report_reason=reason,
            description=description
        )
        
        return SuccessResponse(message="Content reported successfully - our team will review it")
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to submit report")


# === PLATFORM STATUS AND HEALTH ===

@social_router.get("/status", response_model=Dict[str, Any])
async def get_platform_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get platform status and health metrics
    
    - **Community stats**: Active users, content counts, engagement metrics  
    - **User progress**: Personal activity summary
    - **Platform health**: Content quality, moderation stats
    """
    try:
        # This would aggregate statistics across all social features
        # For now, returning a basic structure
        
        return {
            "platform_health": "healthy",
            "active_users_today": "1000+",  # Would be calculated
            "new_goal_shares_today": "50+",
            "active_discussions": "200+",
            "mentor_sessions_this_week": "150+",
            "user_activity": {
                "goal_shares_created": 0,  # User's activity
                "forum_posts": 0,
                "mentorship_sessions": 0,
                "group_participations": 0
            },
            "community_milestones": [
                "10,000+ anonymous goals shared",
                "5,000+ users helped through mentorship",
                "500+ group goals completed"
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to load platform status")


# Health check endpoint (no auth required)
@social_router.get("/health")
async def health_check():
    """Simple health check for the social platform"""
    return {"status": "healthy", "service": "social_platform"}