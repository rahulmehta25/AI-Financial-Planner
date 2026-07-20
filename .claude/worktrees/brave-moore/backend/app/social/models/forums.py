"""
Community forums and moderation models
"""

import uuid
from datetime import datetime
from sqlalchemy import (
    Boolean, Column, DateTime, String, Text, Integer, 
    Float, ForeignKey, JSON, Enum, CheckConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum

from .base import SocialBase


class ForumType(PyEnum):
    """Types of forum categories"""
    GENERAL_DISCUSSION = "general_discussion"
    BEGINNER_QUESTIONS = "beginner_questions"
    INVESTMENT_ADVICE = "investment_advice"
    BUDGETING_TIPS = "budgeting_tips"
    DEBT_MANAGEMENT = "debt_management"
    CAREER_FINANCE = "career_finance"
    REAL_ESTATE = "real_estate"
    RETIREMENT_PLANNING = "retirement_planning"
    TAX_DISCUSSION = "tax_discussion"
    SUCCESS_STORIES = "success_stories"
    TOOLS_AND_APPS = "tools_and_apps"
    NEWS_AND_MARKET = "news_and_market"


class TopicStatus(PyEnum):
    """Status of forum topics"""
    OPEN = "open"
    CLOSED = "closed"
    PINNED = "pinned"
    LOCKED = "locked"
    ARCHIVED = "archived"


class PostType(PyEnum):
    """Types of forum posts"""
    DISCUSSION = "discussion"
    QUESTION = "question"
    ADVICE = "advice"
    SUCCESS_STORY = "success_story"
    TOOL_REVIEW = "tool_review"
    NEWS_SHARE = "news_share"
    POLL = "poll"


class ModerationAction(PyEnum):
    """Types of moderation actions"""
    APPROVED = "approved"
    FLAGGED = "flagged"
    HIDDEN = "hidden"
    DELETED = "deleted"
    EDITED = "edited"
    MOVED = "moved"
    LOCKED = "locked"
    PINNED = "pinned"
    WARNED = "warned"


class ModerationReason(PyEnum):
    """Reasons for moderation actions"""
    SPAM = "spam"
    INAPPROPRIATE_CONTENT = "inappropriate_content"
    HARASSMENT = "harassment"
    OFF_TOPIC = "off_topic"
    FINANCIAL_MISINFORMATION = "financial_misinformation"
    SOLICITATION = "solicitation"
    DUPLICATE_POST = "duplicate_post"
    POLICY_VIOLATION = "policy_violation"
    USER_REQUESTED = "user_requested"


class ForumCategory(SocialBase):
    """Forum categories for organizing discussions"""
    
    __tablename__ = "forum_categories"
    
    # Category details
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=False)
    forum_type = Column(Enum(ForumType), nullable=False)
    
    # Category organization
    parent_category_id = Column(UUID(as_uuid=True), ForeignKey("forum_categories.id"), nullable=True)
    display_order = Column(Integer, default=0, nullable=False)
    
    # Category settings
    is_moderated = Column(Boolean, default=True, nullable=False)
    requires_approval = Column(Boolean, default=False, nullable=False)
    is_read_only = Column(Boolean, default=False, nullable=False)
    minimum_experience_level = Column(String(20), nullable=True)  # "beginner", "intermediate", etc.
    
    # Access control
    is_private = Column(Boolean, default=False, nullable=False)
    allowed_user_groups = Column(JSON, default=list)  # User groups that can access
    
    # Category statistics
    topics_count = Column(Integer, default=0, nullable=False)
    posts_count = Column(Integer, default=0, nullable=False)
    participants_count = Column(Integer, default=0, nullable=False)
    
    # Last activity
    last_post_at = Column(DateTime, nullable=True)
    last_post_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    last_topic_id = Column(UUID(as_uuid=True), nullable=True)
    
    # Moderation
    moderator_user_ids = Column(JSON, default=list)  # List of moderator user IDs
    moderation_rules = Column(JSON, default=list)  # Category-specific rules
    auto_moderation_enabled = Column(Boolean, default=True, nullable=False)
    
    # Display customization
    icon_name = Column(String(50), nullable=True)
    color_theme = Column(String(20), nullable=True)
    banner_image_url = Column(String(500), nullable=True)
    
    # Relationships
    parent_category = relationship("ForumCategory", remote_side="ForumCategory.id")
    subcategories = relationship("ForumCategory", back_populates="parent_category")
    topics = relationship("ForumTopic", back_populates="category")
    last_post_user = relationship("User", foreign_keys=[last_post_user_id])
    
    def add_topic(self):
        """Increment topic count"""
        self.topics_count += 1
        self.updated_at = datetime.utcnow()
    
    def add_post(self, user_id: uuid.UUID, topic_id: uuid.UUID):
        """Increment post count and update last activity"""
        self.posts_count += 1
        self.last_post_at = datetime.utcnow()
        self.last_post_user_id = user_id
        self.last_topic_id = topic_id
        self.updated_at = datetime.utcnow()
    
    def is_user_moderator(self, user_id: uuid.UUID) -> bool:
        """Check if user is a moderator for this category"""
        return str(user_id) in self.moderator_user_ids
    
    def add_moderator(self, user_id: uuid.UUID):
        """Add user as moderator"""
        user_id_str = str(user_id)
        if user_id_str not in self.moderator_user_ids:
            self.moderator_user_ids.append(user_id_str)
            self.updated_at = datetime.utcnow()


class ForumTopic(SocialBase):
    """Forum topics (threads) within categories"""
    
    __tablename__ = "forum_topics"
    
    # Topic details
    category_id = Column(UUID(as_uuid=True), ForeignKey("forum_categories.id"), nullable=False)
    created_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Topic content
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    post_type = Column(Enum(PostType), default=PostType.DISCUSSION, nullable=False)
    
    # Topic status
    status = Column(Enum(TopicStatus), default=TopicStatus.OPEN, nullable=False)
    is_featured = Column(Boolean, default=False, nullable=False)
    is_sticky = Column(Boolean, default=False, nullable=False)
    
    # Engagement metrics
    views_count = Column(Integer, default=0, nullable=False)
    posts_count = Column(Integer, default=0, nullable=False)
    participants_count = Column(Integer, default=0, nullable=False)
    likes_count = Column(Integer, default=0, nullable=False)
    
    # Last activity
    last_post_at = Column(DateTime, nullable=True)
    last_post_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    last_post_id = Column(UUID(as_uuid=True), nullable=True)
    
    # Topic metadata
    tags = Column(JSON, default=list)
    difficulty_level = Column(String(20), nullable=True)  # For questions/advice
    is_solved = Column(Boolean, default=False, nullable=False)  # For questions
    best_answer_post_id = Column(UUID(as_uuid=True), nullable=True)
    
    # Poll data (if post_type is poll)
    poll_question = Column(Text, nullable=True)
    poll_options = Column(JSON, nullable=True)
    poll_votes = Column(JSON, default=dict)  # {option_id: vote_count}
    poll_expires_at = Column(DateTime, nullable=True)
    allow_multiple_votes = Column(Boolean, default=False, nullable=False)
    
    # Content warnings
    has_content_warning = Column(Boolean, default=False, nullable=False)
    content_warnings = Column(JSON, default=list)  # ["financial_loss", "debt_stress", etc.]
    
    # Relationships
    category = relationship("ForumCategory", back_populates="topics")
    created_by = relationship("User", foreign_keys=[created_by_user_id], backref="forum_topics_created")
    last_post_user = relationship("User", foreign_keys=[last_post_user_id])
    posts = relationship("ForumPost", back_populates="topic", cascade="all, delete-orphan")
    
    __table_args__ = (
        CheckConstraint("posts_count >= 0", name="check_posts_count_non_negative"),
        CheckConstraint("views_count >= 0", name="check_views_count_non_negative"),
    )
    
    @property
    def is_active(self) -> bool:
        """Check if topic is open for new posts"""
        return self.status in [TopicStatus.OPEN, TopicStatus.PINNED]
    
    @property
    def engagement_score(self) -> float:
        """Calculate engagement score based on activity"""
        # Weighted score considering views, posts, participants, and likes
        score = (
            self.views_count * 0.1 +
            self.posts_count * 2.0 +
            self.participants_count * 1.5 +
            self.likes_count * 1.0
        )
        return score
    
    def add_view(self):
        """Increment view count"""
        self.views_count += 1
        self.updated_at = datetime.utcnow()
    
    def add_post(self, user_id: uuid.UUID, post_id: uuid.UUID):
        """Add post to topic"""
        self.posts_count += 1
        self.last_post_at = datetime.utcnow()
        self.last_post_user_id = user_id
        self.last_post_id = post_id
        self.updated_at = datetime.utcnow()
        
        # Update category stats
        self.category.add_post(user_id, self.id)
    
    def mark_solved(self, best_answer_post_id: uuid.UUID = None):
        """Mark topic as solved (for questions)"""
        self.is_solved = True
        if best_answer_post_id:
            self.best_answer_post_id = best_answer_post_id
        self.updated_at = datetime.utcnow()
    
    def close_topic(self):
        """Close topic for new posts"""
        self.status = TopicStatus.CLOSED
        self.updated_at = datetime.utcnow()
    
    def pin_topic(self):
        """Pin topic to top of category"""
        self.status = TopicStatus.PINNED
        self.is_sticky = True
        self.updated_at = datetime.utcnow()


class ForumPost(SocialBase):
    """Individual posts within forum topics"""
    
    __tablename__ = "forum_posts"
    
    # Post references
    topic_id = Column(UUID(as_uuid=True), ForeignKey("forum_topics.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    parent_post_id = Column(UUID(as_uuid=True), ForeignKey("forum_posts.id"), nullable=True)  # For replies
    
    # Post content
    content = Column(Text, nullable=False)
    content_format = Column(String(20), default="markdown", nullable=False)  # "markdown", "html", "plain"
    
    # Post metadata
    post_number = Column(Integer, nullable=False)  # Sequential number within topic
    is_original_post = Column(Boolean, default=False, nullable=False)  # First post in topic
    
    # Editing history
    is_edited = Column(Boolean, default=False, nullable=False)
    edited_at = Column(DateTime, nullable=True)
    edit_count = Column(Integer, default=0, nullable=False)
    edit_reason = Column(Text, nullable=True)
    
    # Engagement
    likes_count = Column(Integer, default=0, nullable=False)
    dislikes_count = Column(Integer, default=0, nullable=False)
    helpful_votes = Column(Integer, default=0, nullable=False)
    is_best_answer = Column(Boolean, default=False, nullable=False)
    
    # Post quality indicators
    quality_score = Column(Float, nullable=True)  # Auto-calculated based on engagement
    is_expert_answer = Column(Boolean, default=False, nullable=False)  # From verified experts
    word_count = Column(Integer, nullable=True)
    
    # Content analysis
    sentiment_score = Column(Float, nullable=True)  # Sentiment analysis (-1 to 1)
    contains_financial_advice = Column(Boolean, default=False, nullable=False)
    advice_disclaimer_included = Column(Boolean, default=False, nullable=False)
    
    # Attachments and media
    has_attachments = Column(Boolean, default=False, nullable=False)
    attachment_urls = Column(JSON, default=list)
    embedded_links = Column(JSON, default=list)
    
    # Reply tracking
    replies_count = Column(Integer, default=0, nullable=False)
    
    # Relationships
    topic = relationship("ForumTopic", back_populates="posts")
    user = relationship("User", backref="forum_posts")
    parent_post = relationship("ForumPost", remote_side="ForumPost.id", backref="replies")
    moderations = relationship("ForumModeration", back_populates="post")
    
    __table_args__ = (
        CheckConstraint("post_number > 0", name="check_post_number_positive"),
        CheckConstraint("likes_count >= 0", name="check_likes_count_non_negative"),
        CheckConstraint("dislikes_count >= 0", name="check_dislikes_count_non_negative"),
    )
    
    @property
    def net_votes(self) -> int:
        """Calculate net voting score"""
        return self.likes_count - self.dislikes_count + self.helpful_votes
    
    @property
    def is_highly_rated(self) -> bool:
        """Check if post is highly rated by community"""
        return self.net_votes >= 10 or self.helpful_votes >= 5
    
    def add_like(self):
        """Add like to post"""
        self.likes_count += 1
        self.updated_at = datetime.utcnow()
    
    def add_dislike(self):
        """Add dislike to post"""
        self.dislikes_count += 1
        self.updated_at = datetime.utcnow()
    
    def add_helpful_vote(self):
        """Add helpful vote"""
        self.helpful_votes += 1
        self.updated_at = datetime.utcnow()
    
    def mark_as_best_answer(self):
        """Mark post as best answer for topic"""
        self.is_best_answer = True
        self.updated_at = datetime.utcnow()
        
        # Update topic
        self.topic.mark_solved(self.id)
    
    def edit_post(self, new_content: str, reason: str = None):
        """Edit post content"""
        self.content = new_content
        self.is_edited = True
        self.edited_at = datetime.utcnow()
        self.edit_count += 1
        if reason:
            self.edit_reason = reason
        self.updated_at = datetime.utcnow()
    
    def calculate_word_count(self):
        """Calculate and store word count"""
        self.word_count = len(self.content.split())
        self.updated_at = datetime.utcnow()


class ForumModeration(SocialBase):
    """Moderation actions and reports for forum content"""
    
    __tablename__ = "forum_moderations"
    
    # Moderation target
    post_id = Column(UUID(as_uuid=True), ForeignKey("forum_posts.id"), nullable=True)
    topic_id = Column(UUID(as_uuid=True), ForeignKey("forum_topics.id"), nullable=True)
    reported_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Moderation details
    action_taken = Column(Enum(ModerationAction), nullable=False)
    reason = Column(Enum(ModerationReason), nullable=False)
    moderator_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Report information
    reported_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    report_description = Column(Text, nullable=True)
    report_category = Column(String(50), nullable=True)
    
    # Moderation action details
    moderator_notes = Column(Text, nullable=True)
    action_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    duration_hours = Column(Integer, nullable=True)  # For temporary actions
    expires_at = Column(DateTime, nullable=True)
    
    # Appeal process
    can_appeal = Column(Boolean, default=True, nullable=False)
    appeal_submitted = Column(Boolean, default=False, nullable=False)
    appeal_text = Column(Text, nullable=True)
    appeal_date = Column(DateTime, nullable=True)
    appeal_resolved = Column(Boolean, default=False, nullable=False)
    appeal_resolution = Column(Text, nullable=True)
    
    # Automated moderation
    is_automated_action = Column(Boolean, default=False, nullable=False)
    confidence_score = Column(Float, nullable=True)  # For AI moderation
    auto_moderation_triggers = Column(JSON, default=list)
    
    # Status tracking
    is_resolved = Column(Boolean, default=False, nullable=False)
    resolved_at = Column(DateTime, nullable=True)
    resolution_notes = Column(Text, nullable=True)
    
    # Relationships
    post = relationship("ForumPost", back_populates="moderations")
    topic = relationship("ForumTopic", backref="moderations")
    reported_user = relationship("User", foreign_keys=[reported_user_id], backref="moderation_reports_received")
    moderator = relationship("User", foreign_keys=[moderator_user_id], backref="moderation_actions_taken")
    reporter = relationship("User", foreign_keys=[reported_by_user_id], backref="moderation_reports_submitted")
    
    __table_args__ = (
        CheckConstraint("(post_id IS NOT NULL) OR (topic_id IS NOT NULL)", 
                       name="check_moderation_target_exists"),
    )
    
    def resolve_report(self, resolution_notes: str = None):
        """Mark moderation report as resolved"""
        self.is_resolved = True
        self.resolved_at = datetime.utcnow()
        if resolution_notes:
            self.resolution_notes = resolution_notes
        self.updated_at = datetime.utcnow()
    
    def submit_appeal(self, appeal_text: str):
        """Submit appeal for moderation action"""
        self.appeal_submitted = True
        self.appeal_text = appeal_text
        self.appeal_date = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def resolve_appeal(self, resolution: str):
        """Resolve appeal with outcome"""
        self.appeal_resolved = True
        self.appeal_resolution = resolution
        self.updated_at = datetime.utcnow()
    
    @property
    def is_active(self) -> bool:
        """Check if moderation action is currently active"""
        if not self.expires_at:
            return not self.is_resolved
        return datetime.utcnow() < self.expires_at and not self.is_resolved