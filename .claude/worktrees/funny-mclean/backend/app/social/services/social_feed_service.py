"""
Social feed service for activity tracking and personalized feeds
"""

import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func

from ..models.user_social import UserSocialProfile, UserPrivacySettings
from ..models.goal_sharing import AnonymousGoalShare
from ..models.forums import ForumTopic, ForumPost
from ..models.group_goals import GroupSavingsGoal, GroupGoalParticipation
from ..models.mentorship import MentorshipMatch, MentorshipSession
from .anonymization_service import AnonymizationService


class SocialFeedService:
    """Service for generating personalized social feeds and activity tracking"""
    
    def __init__(self, db: Session):
        self.db = db
        self.anonymization_service = AnonymizationService(db)
    
    def get_personalized_feed(self, user_id: uuid.UUID, page: int = 1, 
                            per_page: int = 20, feed_type: str = "all") -> Dict[str, Any]:
        """
        Generate personalized social feed for user
        """
        user_profile = self.db.query(UserSocialProfile).filter(
            UserSocialProfile.user_id == user_id
        ).first()
        
        if not user_profile:
            return {"items": [], "total": 0, "page": page, "per_page": per_page}
        
        feed_items = []
        
        # Get user's interests and experience level for personalization
        interests = user_profile.interest_areas or []
        expertise_areas = user_profile.expertise_areas or []
        experience_level = user_profile.experience_level
        
        offset = (page - 1) * per_page
        
        if feed_type in ["all", "goals"]:
            # Anonymous goal shares matching user interests
            goal_items = self._get_goal_feed_items(user_id, interests, experience_level, per_page // 4)
            feed_items.extend(goal_items)
        
        if feed_type in ["all", "community"]:
            # Forum discussions
            forum_items = self._get_forum_feed_items(user_id, interests, expertise_areas, per_page // 4)
            feed_items.extend(forum_items)
        
        if feed_type in ["all", "groups"]:
            # Group goal activities
            group_items = self._get_group_feed_items(user_id, interests, per_page // 4)
            feed_items.extend(group_items)
        
        if feed_type in ["all", "mentorship"]:
            # Mentorship activities
            mentorship_items = self._get_mentorship_feed_items(user_id, per_page // 4)
            feed_items.extend(mentorship_items)
        
        # Sort by relevance score and recency
        feed_items.sort(key=lambda x: (x.get("relevance_score", 0), x.get("timestamp")), reverse=True)
        
        # Apply pagination
        total_items = len(feed_items)
        paginated_items = feed_items[offset:offset + per_page]
        
        return {
            "items": paginated_items,
            "total": total_items,
            "page": page,
            "per_page": per_page,
            "has_next": (offset + per_page) < total_items,
            "has_prev": page > 1
        }
    
    def _get_goal_feed_items(self, user_id: uuid.UUID, interests: List[str], 
                           experience_level: str, limit: int) -> List[Dict[str, Any]]:
        """Get goal sharing feed items"""
        
        # Get recent anonymous goal shares
        goal_shares = self.db.query(AnonymousGoalShare).filter(
            and_(
                AnonymousGoalShare.is_public == True,
                AnonymousGoalShare.is_flagged == False,
                AnonymousGoalShare.user_id != user_id,  # Don't show user's own shares
                AnonymousGoalShare.created_at > datetime.utcnow() - timedelta(days=30)
            )
        ).order_by(desc(AnonymousGoalShare.created_at)).limit(limit * 2).all()
        
        feed_items = []
        for share in goal_shares:
            # Calculate relevance score
            relevance_score = 0.0
            
            # Interest matching
            if any(interest in share.tags for interest in interests):
                relevance_score += 30
            
            # Category interest
            if share.goal_category.value in [interest.lower().replace(" ", "_") for interest in interests]:
                relevance_score += 25
            
            # Experience level matching
            if share.user_age_group and experience_level:
                if experience_level in ["beginner", "intermediate"] and share.is_goal_completed:
                    relevance_score += 20  # Beginners benefit from seeing completed goals
            
            # Engagement indicators
            relevance_score += min(share.likes_count * 2, 20)
            relevance_score += min(share.inspiration_votes * 3, 15)
            
            # Recency boost
            days_old = (datetime.utcnow() - share.created_at).days
            if days_old < 3:
                relevance_score += 15
            elif days_old < 7:
                relevance_score += 10
            elif days_old < 14:
                relevance_score += 5
            
            feed_item = {
                "id": str(share.id),
                "type": "anonymous_goal_share",
                "title": share.goal_title,
                "content": share.goal_description or "",
                "category": share.goal_category.value,
                "progress": share.current_progress_percentage,
                "is_completed": share.is_goal_completed,
                "tags": share.tags,
                "engagement": {
                    "likes": share.likes_count,
                    "comments": share.comments_count,
                    "inspiration_votes": share.inspiration_votes
                },
                "timestamp": share.created_at,
                "relevance_score": relevance_score,
                "anonymous_author": {
                    "age_group": share.user_age_group.value if share.user_age_group else None,
                    "income_range": share.user_income_range.value if share.user_income_range else None,
                    "region": share.user_location_region
                }
            }
            
            # Add success story elements if completed
            if share.is_goal_completed and share.tips_and_lessons:
                feed_item["success_story"] = {
                    "tips": share.tips_and_lessons,
                    "challenges": share.challenges_faced,
                    "strategy": share.strategy_description
                }
            
            feed_items.append(feed_item)
        
        # Sort by relevance and return top items
        feed_items.sort(key=lambda x: x["relevance_score"], reverse=True)
        return feed_items[:limit]
    
    def _get_forum_feed_items(self, user_id: uuid.UUID, interests: List[str],
                             expertise_areas: List[str], limit: int) -> List[Dict[str, Any]]:
        """Get forum discussion feed items"""
        
        # Get recent active topics
        topics = self.db.query(ForumTopic).filter(
            and_(
                ForumTopic.is_public == True,
                ForumTopic.is_flagged == False,
                ForumTopic.status.in_(["open", "pinned"]),
                ForumTopic.created_at > datetime.utcnow() - timedelta(days=14)
            )
        ).order_by(desc(ForumTopic.last_post_at)).limit(limit * 2).all()
        
        feed_items = []
        for topic in topics:
            # Calculate relevance
            relevance_score = 0.0
            
            # Interest/expertise matching
            topic_tags = topic.tags or []
            if any(tag in interests + expertise_areas for tag in topic_tags):
                relevance_score += 25
            
            # Category matching
            category_type = topic.category.forum_type.value if topic.category else ""
            if any(interest.lower().replace(" ", "_") in category_type for interest in interests):
                relevance_score += 20
            
            # Engagement metrics
            relevance_score += min(topic.views_count * 0.1, 15)
            relevance_score += min(topic.posts_count * 2, 25)
            relevance_score += min(topic.likes_count * 1.5, 15)
            
            # Question priority for helpful users
            if topic.post_type.value == "question" and not topic.is_solved:
                if any(area in expertise_areas for area in topic.tags or []):
                    relevance_score += 30  # Experts see relevant unanswered questions
            
            # Recent activity boost
            if topic.last_post_at:
                hours_since_activity = (datetime.utcnow() - topic.last_post_at).total_seconds() / 3600
                if hours_since_activity < 2:
                    relevance_score += 20
                elif hours_since_activity < 12:
                    relevance_score += 10
                elif hours_since_activity < 24:
                    relevance_score += 5
            
            feed_item = {
                "id": str(topic.id),
                "type": "forum_topic",
                "title": topic.title,
                "content": topic.description or "",
                "category": topic.category.name if topic.category else "",
                "post_type": topic.post_type.value,
                "is_solved": topic.is_solved,
                "tags": topic.tags,
                "engagement": {
                    "views": topic.views_count,
                    "posts": topic.posts_count,
                    "participants": topic.participants_count,
                    "likes": topic.likes_count
                },
                "timestamp": topic.last_post_at or topic.created_at,
                "relevance_score": relevance_score,
                "author": {
                    "display_name": topic.created_by.social_profile.display_name if topic.created_by and topic.created_by.social_profile else "Anonymous",
                    "experience_level": topic.created_by.social_profile.experience_level if topic.created_by and topic.created_by.social_profile else None
                }
            }
            
            feed_items.append(feed_item)
        
        feed_items.sort(key=lambda x: x["relevance_score"], reverse=True)
        return feed_items[:limit]
    
    def _get_group_feed_items(self, user_id: uuid.UUID, interests: List[str], 
                            limit: int) -> List[Dict[str, Any]]:
        """Get group goal feed items"""
        
        # Get user's group participations
        user_groups = self.db.query(GroupGoalParticipation).filter(
            and_(
                GroupGoalParticipation.user_id == user_id,
                GroupGoalParticipation.is_active == True
            )
        ).all()
        
        user_group_ids = [p.group_goal_id for p in user_groups]
        
        # Get recent group activities
        groups = self.db.query(GroupSavingsGoal).filter(
            or_(
                GroupSavingsGoal.id.in_(user_group_ids),  # User's groups
                and_(
                    GroupSavingsGoal.is_public == True,
                    GroupSavingsGoal.is_searchable == True,
                    GroupSavingsGoal.status == "active"
                )
            )
        ).order_by(desc(GroupSavingsGoal.updated_at)).limit(limit * 2).all()
        
        feed_items = []
        for group in groups:
            relevance_score = 0.0
            
            # Higher score for user's own groups
            if group.id in user_group_ids:
                relevance_score += 50
            
            # Interest matching
            group_tags = group.tags or []
            if any(tag in interests for tag in group_tags):
                relevance_score += 20
            
            # Goal type matching
            if group.goal_type.value.replace("_", " ") in [interest.lower() for interest in interests]:
                relevance_score += 25
            
            # Progress and activity
            relevance_score += min(group.progress_percentage * 0.1, 10)
            relevance_score += min(group.total_participants * 2, 15)
            
            # Recent activity
            days_since_update = (datetime.utcnow() - group.updated_at).days
            if days_since_update < 1:
                relevance_score += 15
            elif days_since_update < 3:
                relevance_score += 10
            elif days_since_update < 7:
                relevance_score += 5
            
            feed_item = {
                "id": str(group.id),
                "type": "group_goal",
                "title": group.title,
                "content": group.description,
                "goal_type": group.goal_type.value,
                "progress": {
                    "current_amount": group.current_amount,
                    "target_amount": group.target_amount,
                    "percentage": group.progress_percentage,
                    "participants": group.total_participants
                },
                "target_date": group.target_date.isoformat() if group.target_date else None,
                "tags": group.tags,
                "timestamp": group.updated_at,
                "relevance_score": relevance_score,
                "is_participant": group.id in user_group_ids,
                "can_join": group.can_accept_participants and group.id not in user_group_ids
            }
            
            feed_items.append(feed_item)
        
        feed_items.sort(key=lambda x: x["relevance_score"], reverse=True)
        return feed_items[:limit]
    
    def _get_mentorship_feed_items(self, user_id: uuid.UUID, limit: int) -> List[Dict[str, Any]]:
        """Get mentorship-related feed items"""
        
        # Get user's mentorship activities
        mentorships = self.db.query(MentorshipMatch).filter(
            or_(
                MentorshipMatch.mentee_user_id == user_id,
                MentorshipMatch.mentor_profile.has(
                    MentorshipMatch.mentor_profile.property.mapper.class_.user_profile.has(
                        UserSocialProfile.user_id == user_id
                    )
                )
            )
        ).filter(MentorshipMatch.status == "active").all()
        
        feed_items = []
        for mentorship in mentorships:
            # Get recent sessions
            recent_sessions = self.db.query(MentorshipSession).filter(
                and_(
                    MentorshipSession.mentorship_match_id == mentorship.id,
                    MentorshipSession.updated_at > datetime.utcnow() - timedelta(days=7)
                )
            ).order_by(desc(MentorshipSession.updated_at)).limit(2).all()
            
            for session in recent_sessions:
                relevance_score = 75  # High relevance for user's own mentorship activities
                
                # Boost for completed sessions
                if session.status.value == "completed":
                    relevance_score += 15
                
                # Recent activity boost
                hours_since_update = (datetime.utcnow() - session.updated_at).total_seconds() / 3600
                if hours_since_update < 24:
                    relevance_score += 20
                elif hours_since_update < 72:
                    relevance_score += 10
                
                is_mentor = (mentorship.mentor_profile.user_profile.user_id == user_id)
                other_participant = mentorship.mentor_profile.user_profile if not is_mentor else mentorship.mentee
                
                feed_item = {
                    "id": str(session.id),
                    "type": "mentorship_session",
                    "title": session.title,
                    "content": f"Mentorship session {session.session_number}",
                    "session_status": session.status.value,
                    "focus_areas": mentorship.focus_areas,
                    "communication_method": session.communication_method.value,
                    "scheduled_time": session.scheduled_start_time.isoformat() if session.scheduled_start_time else None,
                    "timestamp": session.updated_at,
                    "relevance_score": relevance_score,
                    "role": "mentor" if is_mentor else "mentee",
                    "other_participant": {
                        "display_name": other_participant.social_profile.display_name if hasattr(other_participant, 'social_profile') and other_participant.social_profile else "Anonymous"
                    }
                }
                
                # Add session outcomes for completed sessions
                if session.status.value == "completed" and session.key_takeaways:
                    feed_item["outcomes"] = {
                        "takeaways": session.key_takeaways[:3],  # Limit for feed display
                        "action_items": len(session.action_items or [])
                    }
                
                feed_items.append(feed_item)
        
        return feed_items[:limit]
    
    def track_user_activity(self, user_id: uuid.UUID, activity_type: str, 
                          activity_data: Dict[str, Any]) -> None:
        """
        Track user activity for feed generation and analytics
        This would typically store in a separate activity log table
        """
        # Update user's last active timestamp
        user_profile = self.db.query(UserSocialProfile).filter(
            UserSocialProfile.user_id == user_id
        ).first()
        
        if user_profile:
            user_profile.update_last_active()
            
            # Update relevant counters based on activity type
            if activity_type == "forum_post":
                user_profile.posts_count += 1
            elif activity_type == "forum_comment":
                user_profile.comments_count += 1
            elif activity_type == "goal_achievement":
                user_profile.add_achievement(activity_data.get("badge_name", "goal_achieved"))
            
            self.db.commit()
    
    def get_trending_content(self, time_period: str = "week", limit: int = 10) -> List[Dict[str, Any]]:
        """Get trending content across the platform"""
        
        if time_period == "day":
            cutoff = datetime.utcnow() - timedelta(days=1)
        elif time_period == "week":
            cutoff = datetime.utcnow() - timedelta(days=7)
        elif time_period == "month":
            cutoff = datetime.utcnow() - timedelta(days=30)
        else:
            cutoff = datetime.utcnow() - timedelta(days=7)
        
        trending_items = []
        
        # Trending anonymous goal shares
        trending_goals = self.db.query(AnonymousGoalShare).filter(
            and_(
                AnonymousGoalShare.created_at > cutoff,
                AnonymousGoalShare.is_public == True,
                AnonymousGoalShare.is_flagged == False
            )
        ).order_by(
            desc(AnonymousGoalShare.likes_count + AnonymousGoalShare.inspiration_votes * 2)
        ).limit(limit // 2).all()
        
        for goal in trending_goals:
            trending_items.append({
                "id": str(goal.id),
                "type": "anonymous_goal_share",
                "title": goal.goal_title,
                "engagement_score": goal.likes_count + goal.inspiration_votes * 2,
                "category": goal.goal_category.value,
                "is_completed": goal.is_goal_completed,
                "timestamp": goal.created_at
            })
        
        # Trending forum topics
        trending_topics = self.db.query(ForumTopic).filter(
            and_(
                ForumTopic.last_post_at > cutoff,
                ForumTopic.is_public == True,
                ForumTopic.is_flagged == False
            )
        ).order_by(
            desc(ForumTopic.posts_count * 2 + ForumTopic.views_count * 0.1 + ForumTopic.likes_count)
        ).limit(limit // 2).all()
        
        for topic in trending_topics:
            engagement_score = topic.posts_count * 2 + topic.views_count * 0.1 + topic.likes_count
            trending_items.append({
                "id": str(topic.id),
                "type": "forum_topic",
                "title": topic.title,
                "engagement_score": engagement_score,
                "category": topic.category.name if topic.category else "",
                "post_type": topic.post_type.value,
                "timestamp": topic.last_post_at or topic.created_at
            })
        
        # Sort by engagement score
        trending_items.sort(key=lambda x: x["engagement_score"], reverse=True)
        return trending_items[:limit]