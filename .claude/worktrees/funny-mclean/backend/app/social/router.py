"""
Main router for social platform - integrates all social features
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..api.deps import get_db, get_current_user
from ..models.user import User
from .api.social_router import social_router
from .services import (
    GoalSharingService, PeerComparisonService, ContentModerationService,
    SocialFeedService, AnonymizationService
)

# Create the main social platform router
router = APIRouter(
    prefix="/social",
    tags=["Social Platform"],
    dependencies=[Depends(get_current_user)]  # Require authentication for all social endpoints
)

# Include the main social router
router.include_router(social_router, prefix="")

# Add some additional utility endpoints at the social platform level

@router.get("/")
async def get_social_platform_info():
    """
    Get information about the social platform features
    """
    return {
        "platform": "Financial Planning Social Platform",
        "version": "1.0.0",
        "features": [
            "Anonymous Goal Sharing - Share and discover financial goals while maintaining privacy",
            "Peer Comparison - Compare your financial progress with anonymous demographic peers", 
            "Community Forums - Discuss financial topics with moderated community",
            "Group Savings Goals - Collaborate on shared financial objectives",
            "Mentorship System - Connect with financial mentors and mentees",
            "Social Feed - Personalized activity feed across all platform features",
            "Content Moderation - AI-powered and human content safety systems"
        ],
        "privacy_features": [
            "Anonymous goal sharing with demographic anonymization",
            "Privacy-preserving peer comparisons using differential privacy",
            "Granular privacy controls for all shared data",
            "Minimum group size enforcement for statistical anonymity",
            "Content sanitization to remove personally identifying information"
        ],
        "safety_features": [
            "Automated content moderation with AI detection",
            "Human moderator review system",
            "Community reporting tools",
            "Financial misinformation detection",
            "Harassment and spam protection"
        ],
        "endpoints": {
            "goal_sharing": "/social/goal-sharing/",
            "peer_comparison": "/social/peer-comparison/",
            "community_forums": "/social/community/",
            "group_goals": "/social/groups/",
            "mentorship": "/social/mentorship/",
            "social_feed": "/social/feed/",
            "content_moderation": "/social/moderation/"
        }
    }


@router.post("/initialize-profile")
async def initialize_social_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Initialize user's social profile with default settings
    """
    from .models.user_social import UserSocialProfile, UserPrivacySettings
    
    # Check if profile already exists
    existing_profile = db.query(UserSocialProfile).filter(
        UserSocialProfile.user_id == current_user.id
    ).first()
    
    if existing_profile:
        return {"message": "Social profile already exists", "profile_id": str(existing_profile.id)}
    
    try:
        # Create social profile with privacy-first defaults
        social_profile = UserSocialProfile(
            user_id=current_user.id,
            display_name=None,  # User can set later
            bio=None,
            experience_level="beginner",  # Default
            expertise_areas=[],
            interest_areas=[],
            achievement_badges=[]
        )
        
        db.add(social_profile)
        db.flush()  # Get the ID
        
        # Create privacy settings with conservative defaults
        privacy_settings = UserPrivacySettings(
            user_profile_id=social_profile.id,
            profile_visibility="community_only",
            goal_sharing_level="community_only",
            share_goal_amounts=False,  # Conservative default
            share_goal_progress=True,
            share_goal_achievements=True,
            share_age_range=True,
            share_income_range=False,  # Conservative default
            share_net_worth_range=False,  # Conservative default
            share_investment_types=True,
            anonymize_in_comparisons=True,
            anonymize_success_stories=True,
            allow_mentorship_requests=True,
            allow_direct_messages=True,
            allow_challenge_invites=True,
            allow_group_goal_invites=True
        )
        
        db.add(privacy_settings)
        db.commit()
        
        return {
            "message": "Social profile initialized successfully",
            "profile_id": str(social_profile.id),
            "privacy_settings_applied": "Conservative defaults - you can adjust in settings"
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to initialize social profile")


@router.get("/privacy-guide")
async def get_privacy_guide():
    """
    Get comprehensive privacy guide for the social platform
    """
    return {
        "privacy_philosophy": "Privacy-first design with granular user control",
        "data_protection_measures": {
            "anonymization": {
                "goal_sharing": "Goal titles and descriptions are sanitized to remove personal identifiers",
                "demographic_data": "Age, income, and location are converted to ranges/groups",
                "peer_comparisons": "All comparisons use statistical methods that preserve individual privacy"
            },
            "minimum_group_sizes": {
                "peer_comparisons": "Minimum 10 users required for any comparison group",
                "demographic_insights": "Minimum 5 users required for demographic statistics",
                "k_anonymity": "Dataset satisfies k-anonymity requirements where k >= 5"
            },
            "differential_privacy": {
                "numerical_data": "Statistical noise added to numerical comparisons",
                "aggregation": "All aggregate statistics include privacy-preserving noise"
            }
        },
        "user_controls": {
            "visibility_levels": [
                "private - Only you can see",
                "mentors_only - Only your mentors can see", 
                "friends_only - Only your connections can see",
                "community_only - All platform members can see",
                "public - Visible to anyone"
            ],
            "data_sharing_options": [
                "Share goal progress but not amounts",
                "Share demographic ranges but not specifics",
                "Anonymize all success stories",
                "Control who can contact you"
            ],
            "opt_out_options": [
                "Disable peer comparisons completely",
                "Opt out of demographic data sharing",
                "Disable social feed appearances",
                "Block specific users or content types"
            ]
        },
        "content_safety": {
            "automated_moderation": "AI systems scan content for spam, harassment, and misinformation",
            "human_review": "Flagged content is reviewed by trained moderators",
            "community_reporting": "Users can report inappropriate content",
            "appeal_process": "Users can appeal moderation decisions"
        },
        "data_retention": {
            "anonymous_shares": "Anonymized goal shares are retained to help future users",
            "personal_data": "Personal identifiers are deleted when shares are anonymized",
            "comparison_data": "Comparison data is refreshed regularly and old data is purged",
            "account_deletion": "All user data is permanently deleted upon account closure"
        }
    }


# Export the router for integration with the main app
__all__ = ["router"]