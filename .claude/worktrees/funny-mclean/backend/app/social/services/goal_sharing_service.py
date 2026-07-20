"""
Anonymous goal sharing service with privacy preservation
"""

import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func

from ..models.goal_sharing import AnonymousGoalShare, GoalCategory, AgeGroup, IncomeRange
from ..models.user_social import UserSocialProfile
from ...models.goal import Goal
from .anonymization_service import AnonymizationService


class GoalSharingService:
    """Service for anonymous goal sharing and inspiration"""
    
    def __init__(self, db: Session):
        self.db = db
        self.anonymization_service = AnonymizationService(db)
    
    def create_anonymous_goal_share(self, user_id: uuid.UUID, goal_id: Optional[uuid.UUID] = None,
                                  goal_data: Dict[str, Any] = None) -> AnonymousGoalShare:
        """
        Create an anonymous goal share from either existing goal or manual data
        """
        if goal_id:
            # Create from existing goal
            goal = self.db.query(Goal).filter(
                and_(Goal.id == goal_id, Goal.user_id == user_id)
            ).first()
            
            if not goal:
                raise ValueError("Goal not found or access denied")
            
            return self._create_share_from_goal(user_id, goal)
        
        elif goal_data:
            # Create from manual input
            return self._create_share_from_data(user_id, goal_data)
        
        else:
            raise ValueError("Either goal_id or goal_data must be provided")
    
    def _create_share_from_goal(self, user_id: uuid.UUID, goal: Goal) -> AnonymousGoalShare:
        """Create anonymous share from existing goal"""
        
        # Get user's demographic info for anonymization
        anonymous_profile = self.anonymization_service.create_anonymous_profile_snapshot(
            user_id, "goal_sharing"
        )
        
        # Anonymize the goal amount
        amount_range = self.anonymization_service.anonymize_amount_to_range(goal.target_amount)
        
        # Calculate progress
        progress = (goal.current_amount / goal.target_amount * 100) if goal.target_amount > 0 else 0
        
        # Sanitize title and description
        sanitized_title = self.anonymization_service.sanitize_goal_title(goal.title)
        sanitized_description = self.anonymization_service.sanitize_goal_title(goal.description or "")
        
        share = AnonymousGoalShare(
            original_goal_id=goal.id,
            user_id=user_id,
            goal_category=self._map_goal_to_category(goal.category),
            goal_title=sanitized_title,
            goal_description=sanitized_description if sanitized_description else None,
            target_amount_range=amount_range,
            target_date_year=goal.target_date.year if goal.target_date else None,
            target_date_quarter=((goal.target_date.month - 1) // 3) + 1 if goal.target_date else None,
            current_progress_percentage=progress,
            is_goal_completed=goal.is_achieved,
            completion_date=goal.achieved_date,
            user_age_group=anonymous_profile.get("age_group"),
            user_income_range=anonymous_profile.get("income_range"),
            user_location_region=anonymous_profile.get("region"),
            tags=self._generate_goal_tags(goal)
        )
        
        self.db.add(share)
        self.db.commit()
        return share
    
    def _create_share_from_data(self, user_id: uuid.UUID, goal_data: Dict[str, Any]) -> AnonymousGoalShare:
        """Create anonymous share from manual data"""
        
        anonymous_profile = self.anonymization_service.create_anonymous_profile_snapshot(
            user_id, "goal_sharing"
        )
        
        # Validate required fields
        required_fields = ["title", "category", "target_amount", "current_progress"]
        for field in required_fields:
            if field not in goal_data:
                raise ValueError(f"Required field '{field}' missing")
        
        # Anonymize amount
        amount_range = self.anonymization_service.anonymize_amount_to_range(goal_data["target_amount"])
        
        # Sanitize inputs
        sanitized_title = self.anonymization_service.sanitize_goal_title(goal_data["title"])
        sanitized_description = self.anonymization_service.sanitize_goal_title(
            goal_data.get("description", "")
        )
        
        share = AnonymousGoalShare(
            user_id=user_id,
            goal_category=GoalCategory(goal_data["category"]),
            goal_title=sanitized_title,
            goal_description=sanitized_description if sanitized_description else None,
            target_amount_range=amount_range,
            target_date_year=goal_data.get("target_year"),
            target_date_quarter=goal_data.get("target_quarter"),
            current_progress_percentage=goal_data["current_progress"],
            is_goal_completed=goal_data.get("is_completed", False),
            completion_date=datetime.fromisoformat(goal_data["completion_date"]) if goal_data.get("completion_date") else None,
            user_age_group=anonymous_profile.get("age_group"),
            user_income_range=anonymous_profile.get("income_range"),
            user_location_region=anonymous_profile.get("region"),
            strategy_description=goal_data.get("strategy"),
            tips_and_lessons=goal_data.get("tips"),
            challenges_faced=goal_data.get("challenges"),
            tags=goal_data.get("tags", [])
        )
        
        self.db.add(share)
        self.db.commit()
        return share
    
    def get_goal_inspiration_feed(self, user_id: uuid.UUID, category: Optional[str] = None,
                                age_group: Optional[str] = None, income_range: Optional[str] = None,
                                page: int = 1, per_page: int = 20) -> Dict[str, Any]:
        """
        Get personalized goal inspiration feed
        """
        query = self.db.query(AnonymousGoalShare).filter(
            and_(
                AnonymousGoalShare.is_public == True,
                AnonymousGoalShare.is_flagged == False,
                AnonymousGoalShare.user_id != user_id  # Don't show user's own shares
            )
        )
        
        # Apply filters
        if category:
            query = query.filter(AnonymousGoalShare.goal_category == GoalCategory(category))
        
        if age_group:
            query = query.filter(AnonymousGoalShare.user_age_group == AgeGroup(age_group))
        
        if income_range:
            query = query.filter(AnonymousGoalShare.user_income_range == IncomeRange(income_range))
        
        # Get user's profile for personalization
        user_profile = self.db.query(UserSocialProfile).filter(
            UserSocialProfile.user_id == user_id
        ).first()
        
        # Prioritize content based on user's interests and experience level
        if user_profile:
            # For beginners, prioritize completed goals
            if user_profile.experience_level in ["beginner", "intermediate"]:
                query = query.order_by(
                    desc(AnonymousGoalShare.is_goal_completed),
                    desc(AnonymousGoalShare.inspiration_votes),
                    desc(AnonymousGoalShare.likes_count),
                    desc(AnonymousGoalShare.created_at)
                )
            else:
                # For advanced users, prioritize recent and highly engaged content
                query = query.order_by(
                    desc(AnonymousGoalShare.inspiration_votes + AnonymousGoalShare.likes_count),
                    desc(AnonymousGoalShare.created_at)
                )
        else:
            # Default ordering
            query = query.order_by(
                desc(AnonymousGoalShare.inspiration_votes),
                desc(AnonymousGoalShare.created_at)
            )
        
        # Apply pagination
        total = query.count()
        offset = (page - 1) * per_page
        shares = query.offset(offset).limit(per_page).all()
        
        # Format response
        items = []
        for share in shares:
            item = {
                "id": str(share.id),
                "title": share.goal_title,
                "description": share.goal_description,
                "category": share.goal_category.value,
                "target_amount_range": share.target_amount_range,
                "progress_percentage": share.current_progress_percentage,
                "is_completed": share.is_goal_completed,
                "tags": share.tags,
                "engagement": {
                    "likes": share.likes_count,
                    "comments": share.comments_count,
                    "inspiration_votes": share.inspiration_votes
                },
                "created_at": share.created_at.isoformat(),
                "anonymous_author": {
                    "age_group": share.user_age_group.value if share.user_age_group else None,
                    "income_range": share.user_income_range.value if share.user_income_range else None,
                    "region": share.user_location_region
                }
            }
            
            # Add success story elements if completed
            if share.is_goal_completed:
                item["success_story"] = {
                    "strategy": share.strategy_description,
                    "tips": share.tips_and_lessons,
                    "challenges": share.challenges_faced,
                    "completion_date": share.completion_date.isoformat() if share.completion_date else None,
                    "is_verified": share.is_verified_completion
                }
            
            items.append(item)
        
        return {
            "items": items,
            "total": total,
            "page": page,
            "per_page": per_page,
            "has_next": (offset + per_page) < total,
            "has_prev": page > 1
        }
    
    def get_goal_templates(self, category: Optional[str] = None, 
                          popular_only: bool = True) -> List[Dict[str, Any]]:
        """
        Generate goal templates from successful anonymous shares
        """
        query = self.db.query(AnonymousGoalShare).filter(
            and_(
                AnonymousGoalShare.is_goal_completed == True,
                AnonymousGoalShare.is_public == True,
                AnonymousGoalShare.is_flagged == False
            )
        )
        
        if category:
            query = query.filter(AnonymousGoalShare.goal_category == GoalCategory(category))
        
        if popular_only:
            # Only include shares with significant engagement
            query = query.filter(
                AnonymousGoalShare.inspiration_votes + AnonymousGoalShare.likes_count >= 5
            )
        
        shares = query.order_by(
            desc(AnonymousGoalShare.inspiration_votes),
            desc(AnonymousGoalShare.likes_count)
        ).limit(20).all()
        
        templates = []
        for share in shares:
            template = {
                "id": str(share.id),
                "title": share.goal_title,
                "category": share.goal_category.value,
                "target_amount_range": share.target_amount_range,
                "typical_timeline": {
                    "year": share.target_date_year,
                    "quarter": share.target_date_quarter
                },
                "strategy": share.strategy_description,
                "tips": share.tips_and_lessons,
                "common_challenges": share.challenges_faced,
                "tags": share.tags,
                "success_rate_indicator": min(share.inspiration_votes / 10, 5),  # Simplified metric
                "demographics": {
                    "age_groups": [share.user_age_group.value] if share.user_age_group else [],
                    "income_ranges": [share.user_income_range.value] if share.user_income_range else []
                }
            }
            templates.append(template)
        
        return templates
    
    def add_like(self, share_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """Add like to anonymous goal share"""
        share = self.db.query(AnonymousGoalShare).filter(
            AnonymousGoalShare.id == share_id
        ).first()
        
        if not share:
            return False
        
        # TODO: Track user likes in separate table to prevent duplicate likes
        # For now, just increment
        share.add_like()
        self.db.commit()
        return True
    
    def add_inspiration_vote(self, share_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """Add inspiration vote to goal share"""
        share = self.db.query(AnonymousGoalShare).filter(
            AnonymousGoalShare.id == share_id
        ).first()
        
        if not share:
            return False
        
        share.add_inspiration_vote()
        self.db.commit()
        return True
    
    def update_goal_progress(self, share_id: uuid.UUID, user_id: uuid.UUID,
                           new_progress: float, completion_data: Optional[Dict[str, Any]] = None) -> bool:
        """Update progress on anonymous goal share"""
        share = self.db.query(AnonymousGoalShare).filter(
            and_(
                AnonymousGoalShare.id == share_id,
                AnonymousGoalShare.user_id == user_id
            )
        ).first()
        
        if not share:
            return False
        
        share.current_progress_percentage = min(100.0, max(0.0, new_progress))
        
        if new_progress >= 100.0 and completion_data:
            share.mark_completed(completion_data.get("verification_proof"))
            if completion_data.get("tips"):
                share.tips_and_lessons = completion_data["tips"]
            if completion_data.get("challenges"):
                share.challenges_faced = completion_data["challenges"]
        
        self.db.commit()
        return True
    
    def _map_goal_to_category(self, goal_category: str) -> GoalCategory:
        """Map goal category to anonymous sharing category"""
        category_mapping = {
            "emergency": GoalCategory.EMERGENCY_FUND,
            "retirement": GoalCategory.RETIREMENT,
            "house": GoalCategory.HOME_PURCHASE,
            "home": GoalCategory.HOME_PURCHASE,
            "debt": GoalCategory.DEBT_PAYOFF,
            "education": GoalCategory.EDUCATION,
            "travel": GoalCategory.TRAVEL,
            "investment": GoalCategory.INVESTMENT,
            "business": GoalCategory.BUSINESS,
        }
        
        return category_mapping.get(goal_category.lower(), GoalCategory.OTHER)
    
    def _generate_goal_tags(self, goal: Goal) -> List[str]:
        """Generate tags for goal based on its characteristics"""
        tags = []
        
        # Amount-based tags
        if goal.target_amount < 1000:
            tags.append("small_goal")
        elif goal.target_amount < 10000:
            tags.append("medium_goal")
        else:
            tags.append("large_goal")
        
        # Timeline-based tags
        if goal.target_date:
            months_to_target = (goal.target_date - datetime.now()).days // 30
            if months_to_target < 6:
                tags.append("short_term")
            elif months_to_target < 24:
                tags.append("medium_term")
            else:
                tags.append("long_term")
        
        # Progress-based tags
        progress = (goal.current_amount / goal.target_amount * 100) if goal.target_amount > 0 else 0
        if progress > 75:
            tags.append("almost_there")
        elif progress > 50:
            tags.append("halfway_there")
        elif progress < 10:
            tags.append("getting_started")
        
        # Goal-specific tags based on category
        category_tags = {
            "emergency": ["emergency_fund", "financial_security"],
            "retirement": ["retirement_planning", "long_term_investing"],
            "house": ["homeownership", "real_estate", "down_payment"],
            "debt": ["debt_free", "financial_freedom"],
            "travel": ["travel_goals", "experiences"],
            "education": ["education_investment", "skill_building"],
        }
        
        if goal.category and goal.category.lower() in category_tags:
            tags.extend(category_tags[goal.category.lower()])
        
        return tags
    
    def get_community_challenges(self) -> List[Dict[str, Any]]:
        """Get community-wide goal challenges based on popular goals"""
        
        # Find popular goal categories and amounts
        popular_goals = self.db.query(
            AnonymousGoalShare.goal_category,
            AnonymousGoalShare.target_amount_range,
            func.count(AnonymousGoalShare.id).label('count'),
            func.avg(AnonymousGoalShare.current_progress_percentage).label('avg_progress')
        ).filter(
            and_(
                AnonymousGoalShare.created_at > datetime.utcnow() - timedelta(days=90),
                AnonymousGoalShare.is_public == True
            )
        ).group_by(
            AnonymousGoalShare.goal_category,
            AnonymousGoalShare.target_amount_range
        ).having(func.count(AnonymousGoalShare.id) >= 5).all()
        
        challenges = []
        for goal_data in popular_goals:
            challenge = {
                "category": goal_data.goal_category.value,
                "target_range": goal_data.target_amount_range,
                "participant_count": goal_data.count,
                "average_progress": round(goal_data.avg_progress, 1),
                "challenge_type": "community_goal",
                "description": f"Join {goal_data.count} others working on {goal_data.goal_category.value.replace('_', ' ')} goals"
            }
            challenges.append(challenge)
        
        return challenges