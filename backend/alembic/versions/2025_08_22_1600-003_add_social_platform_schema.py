"""Add social platform schema with privacy controls

Revision ID: 003
Revises: 002
Create Date: 2025-08-22 16:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade():
    # Create enums for social platform
    
    # Privacy level enum
    privacy_level_enum = postgresql.ENUM(
        'PUBLIC', 'COMMUNITY_ONLY', 'FRIENDS_ONLY', 'MENTORS_ONLY', 'PRIVATE',
        name='privacylevel'
    )
    privacy_level_enum.create(op.get_bind())
    
    # Sharing preference enum
    sharing_preference_enum = postgresql.ENUM(
        'NONE', 'GOALS_ONLY', 'PROGRESS_ONLY', 'ACHIEVEMENTS_ONLY', 'CHALLENGES_ONLY', 'ALL',
        name='sharingpreference'
    )
    sharing_preference_enum.create(op.get_bind())
    
    # Goal category enum
    goal_category_enum = postgresql.ENUM(
        'EMERGENCY_FUND', 'RETIREMENT', 'HOME_PURCHASE', 'DEBT_PAYOFF', 'EDUCATION', 
        'TRAVEL', 'INVESTMENT', 'BUSINESS', 'OTHER',
        name='goalcategory'
    )
    goal_category_enum.create(op.get_bind())
    
    # Age group enum
    age_group_enum = postgresql.ENUM(
        'UNDER_25', 'AGE_25_34', 'AGE_35_44', 'AGE_45_54', 'AGE_55_64', 'OVER_65',
        name='agegroup'
    )
    age_group_enum.create(op.get_bind())
    
    # Income range enum
    income_range_enum = postgresql.ENUM(
        'UNDER_30K', 'RANGE_30K_50K', 'RANGE_50K_75K', 'RANGE_75K_100K', 
        'RANGE_100K_150K', 'RANGE_150K_250K', 'OVER_250K',
        name='incomerange'
    )
    income_range_enum.create(op.get_bind())
    
    # Forum type enum
    forum_type_enum = postgresql.ENUM(
        'GENERAL_DISCUSSION', 'BEGINNER_QUESTIONS', 'INVESTMENT_ADVICE', 'BUDGETING_TIPS',
        'DEBT_MANAGEMENT', 'CAREER_FINANCE', 'REAL_ESTATE', 'RETIREMENT_PLANNING',
        'TAX_DISCUSSION', 'SUCCESS_STORIES', 'TOOLS_AND_APPS', 'NEWS_AND_MARKET',
        name='forumtype'
    )
    forum_type_enum.create(op.get_bind())
    
    # Topic status enum
    topic_status_enum = postgresql.ENUM(
        'OPEN', 'CLOSED', 'PINNED', 'LOCKED', 'ARCHIVED',
        name='topicstatus'
    )
    topic_status_enum.create(op.get_bind())
    
    # Post type enum
    post_type_enum = postgresql.ENUM(
        'DISCUSSION', 'QUESTION', 'ADVICE', 'SUCCESS_STORY', 'TOOL_REVIEW', 'NEWS_SHARE', 'POLL',
        name='posttype'
    )
    post_type_enum.create(op.get_bind())
    
    # Moderation action enum
    moderation_action_enum = postgresql.ENUM(
        'APPROVED', 'FLAGGED', 'HIDDEN', 'DELETED', 'EDITED', 'MOVED', 'LOCKED', 'PINNED', 'WARNED',
        name='moderationaction'
    )
    moderation_action_enum.create(op.get_bind())
    
    # Moderation reason enum
    moderation_reason_enum = postgresql.ENUM(
        'SPAM', 'INAPPROPRIATE_CONTENT', 'HARASSMENT', 'OFF_TOPIC', 'FINANCIAL_MISINFORMATION',
        'SOLICITATION', 'DUPLICATE_POST', 'POLICY_VIOLATION', 'USER_REQUESTED',
        name='moderationreason'
    )
    moderation_reason_enum.create(op.get_bind())
    
    # Group goal type enum
    group_goal_type_enum = postgresql.ENUM(
        'FAMILY_VACATION', 'HOME_DOWN_PAYMENT', 'WEDDING', 'EMERGENCY_FUND', 'BUSINESS_STARTUP',
        'EDUCATION_FUND', 'GROUP_INVESTMENT', 'CHARITY_FUNDRAISING', 'EVENT_PLANNING', 'OTHER',
        name='groupgoaltype'
    )
    group_goal_type_enum.create(op.get_bind())
    
    # Group goal status enum
    group_goal_status_enum = postgresql.ENUM(
        'PLANNING', 'ACTIVE', 'COMPLETED', 'CANCELLED', 'PAUSED',
        name='groupgoalstatus'
    )
    group_goal_status_enum.create(op.get_bind())
    
    # Participant role enum
    participant_role_enum = postgresql.ENUM(
        'CREATOR', 'ADMIN', 'PARTICIPANT', 'VIEWER',
        name='participantrole'
    )
    participant_role_enum.create(op.get_bind())
    
    # Mentorship type enum
    mentorship_type_enum = postgresql.ENUM(
        'ONE_ON_ONE', 'GROUP_MENTORING', 'PEER_MENTORING', 'REVERSE_MENTORING', 'MICRO_MENTORING',
        name='mentorshiptype'
    )
    mentorship_type_enum.create(op.get_bind())
    
    # Expertise level enum
    expertise_level_enum = postgresql.ENUM(
        'BEGINNER', 'INTERMEDIATE', 'ADVANCED', 'EXPERT', 'PROFESSIONAL',
        name='expertiselevel'
    )
    expertise_level_enum.create(op.get_bind())
    
    # Mentorship status enum
    mentorship_status_enum = postgresql.ENUM(
        'PENDING', 'ACTIVE', 'PAUSED', 'COMPLETED', 'CANCELLED',
        name='mentorshipstatus'
    )
    mentorship_status_enum.create(op.get_bind())
    
    # Session status enum
    session_status_enum = postgresql.ENUM(
        'SCHEDULED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED', 'NO_SHOW', 'RESCHEDULED',
        name='sessionstatus'
    )
    session_status_enum.create(op.get_bind())
    
    # Communication preference enum
    communication_preference_enum = postgresql.ENUM(
        'VIDEO_CALL', 'PHONE_CALL', 'TEXT_CHAT', 'EMAIL', 'IN_PERSON',
        name='communicationpreference'
    )
    communication_preference_enum.create(op.get_bind())

    # Create user social profiles table
    op.create_table('user_social_profiles',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.Column('is_public', sa.Boolean(), nullable=False),
        sa.Column('is_flagged', sa.Boolean(), nullable=False),
        sa.Column('moderation_notes', sa.Text(), nullable=True),
        sa.Column('moderated_at', sa.DateTime(), nullable=True),
        sa.Column('moderated_by_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('display_name', sa.String(length=100), nullable=True),
        sa.Column('bio', sa.Text(), nullable=True),
        sa.Column('avatar_url', sa.Text(), nullable=True),
        sa.Column('location', sa.String(length=100), nullable=True),
        sa.Column('reputation_score', sa.Integer(), nullable=False),
        sa.Column('total_contributions', sa.Integer(), nullable=False),
        sa.Column('helpful_votes_received', sa.Integer(), nullable=False),
        sa.Column('challenges_completed', sa.Integer(), nullable=False),
        sa.Column('following_count', sa.Integer(), nullable=False),
        sa.Column('followers_count', sa.Integer(), nullable=False),
        sa.Column('last_active_at', sa.DateTime(), nullable=True),
        sa.Column('posts_count', sa.Integer(), nullable=False),
        sa.Column('comments_count', sa.Integer(), nullable=False),
        sa.Column('experience_level', sa.Enum('beginner', 'intermediate', 'advanced', 'expert', name='experience_level'), nullable=True),
        sa.Column('expertise_areas', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('interest_areas', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('achievement_badges', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )
    op.create_index(op.f('ix_user_social_profiles_user_id'), 'user_social_profiles', ['user_id'], unique=False)
    op.create_index(op.f('ix_user_social_profiles_experience_level'), 'user_social_profiles', ['experience_level'], unique=False)

    # Create user privacy settings table
    op.create_table('user_privacy_settings',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.Column('is_public', sa.Boolean(), nullable=False),
        sa.Column('is_flagged', sa.Boolean(), nullable=False),
        sa.Column('moderation_notes', sa.Text(), nullable=True),
        sa.Column('moderated_at', sa.DateTime(), nullable=True),
        sa.Column('moderated_by_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('user_profile_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('profile_visibility', privacy_level_enum, nullable=False),
        sa.Column('goal_sharing_level', privacy_level_enum, nullable=False),
        sa.Column('share_goal_amounts', sa.Boolean(), nullable=False),
        sa.Column('share_goal_progress', sa.Boolean(), nullable=False),
        sa.Column('share_goal_achievements', sa.Boolean(), nullable=False),
        sa.Column('share_age_range', sa.Boolean(), nullable=False),
        sa.Column('share_income_range', sa.Boolean(), nullable=False),
        sa.Column('share_net_worth_range', sa.Boolean(), nullable=False),
        sa.Column('share_investment_types', sa.Boolean(), nullable=False),
        sa.Column('allow_mentorship_requests', sa.Boolean(), nullable=False),
        sa.Column('allow_direct_messages', sa.Boolean(), nullable=False),
        sa.Column('allow_challenge_invites', sa.Boolean(), nullable=False),
        sa.Column('allow_group_goal_invites', sa.Boolean(), nullable=False),
        sa.Column('anonymize_in_comparisons', sa.Boolean(), nullable=False),
        sa.Column('anonymize_in_leaderboards', sa.Boolean(), nullable=False),
        sa.Column('anonymize_success_stories', sa.Boolean(), nullable=False),
        sa.Column('email_community_updates', sa.Boolean(), nullable=False),
        sa.Column('email_mentor_messages', sa.Boolean(), nullable=False),
        sa.Column('email_challenge_notifications', sa.Boolean(), nullable=False),
        sa.Column('push_social_notifications', sa.Boolean(), nullable=False),
        sa.Column('sharing_preferences', sharing_preference_enum, nullable=False),
        sa.Column('blocked_users', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('restricted_keywords', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['user_profile_id'], ['user_social_profiles.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_profile_id')
    )

    # Create anonymous goal shares table
    op.create_table('anonymous_goal_shares',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.Column('is_public', sa.Boolean(), nullable=False),
        sa.Column('is_flagged', sa.Boolean(), nullable=False),
        sa.Column('moderation_notes', sa.Text(), nullable=True),
        sa.Column('moderated_at', sa.DateTime(), nullable=True),
        sa.Column('moderated_by_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('original_goal_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('goal_category', goal_category_enum, nullable=False),
        sa.Column('goal_title', sa.String(length=200), nullable=False),
        sa.Column('goal_description', sa.Text(), nullable=True),
        sa.Column('target_amount_range', sa.String(length=50), nullable=True),
        sa.Column('target_date_year', sa.Integer(), nullable=True),
        sa.Column('target_date_quarter', sa.Integer(), nullable=True),
        sa.Column('current_progress_percentage', sa.Float(), nullable=False),
        sa.Column('is_goal_completed', sa.Boolean(), nullable=False),
        sa.Column('completion_date', sa.DateTime(), nullable=True),
        sa.Column('user_age_group', age_group_enum, nullable=True),
        sa.Column('user_income_range', income_range_enum, nullable=True),
        sa.Column('user_location_region', sa.String(length=50), nullable=True),
        sa.Column('strategy_description', sa.Text(), nullable=True),
        sa.Column('tips_and_lessons', sa.Text(), nullable=True),
        sa.Column('challenges_faced', sa.Text(), nullable=True),
        sa.Column('likes_count', sa.Integer(), nullable=False),
        sa.Column('comments_count', sa.Integer(), nullable=False),
        sa.Column('shares_count', sa.Integer(), nullable=False),
        sa.Column('inspiration_votes', sa.Integer(), nullable=False),
        sa.Column('tags', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('is_verified_completion', sa.Boolean(), nullable=False),
        sa.Column('verification_notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['original_goal_id'], ['goals.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_anonymous_goal_shares_goal_category'), 'anonymous_goal_shares', ['goal_category'], unique=False)
    op.create_index(op.f('ix_anonymous_goal_shares_user_age_group'), 'anonymous_goal_shares', ['user_age_group'], unique=False)
    op.create_index(op.f('ix_anonymous_goal_shares_is_goal_completed'), 'anonymous_goal_shares', ['is_goal_completed'], unique=False)

    # Create peer comparisons table
    op.create_table('peer_comparisons',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.Column('is_public', sa.Boolean(), nullable=False),
        sa.Column('is_flagged', sa.Boolean(), nullable=False),
        sa.Column('moderation_notes', sa.Text(), nullable=True),
        sa.Column('moderated_at', sa.DateTime(), nullable=True),
        sa.Column('moderated_by_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('cohort_age_group', age_group_enum, nullable=False),
        sa.Column('cohort_income_range', income_range_enum, nullable=False),
        sa.Column('cohort_location_region', sa.String(length=50), nullable=True),
        sa.Column('cohort_size', sa.Integer(), nullable=False),
        sa.Column('savings_rate_percentile', sa.Float(), nullable=True),
        sa.Column('emergency_fund_percentile', sa.Float(), nullable=True),
        sa.Column('debt_to_income_percentile', sa.Float(), nullable=True),
        sa.Column('investment_allocation_percentile', sa.Float(), nullable=True),
        sa.Column('net_worth_percentile', sa.Float(), nullable=True),
        sa.Column('goals_completion_rate_percentile', sa.Float(), nullable=True),
        sa.Column('average_goal_progress_percentile', sa.Float(), nullable=True),
        sa.Column('financial_discipline_score', sa.Float(), nullable=True),
        sa.Column('learning_engagement_percentile', sa.Float(), nullable=True),
        sa.Column('top_performing_behaviors', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('improvement_suggestions', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('similar_user_count', sa.Integer(), nullable=True),
        sa.Column('comparison_date', sa.DateTime(), nullable=False),
        sa.Column('data_freshness_days', sa.Integer(), nullable=False),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('contains_insufficient_data', sa.Boolean(), nullable=False),
        sa.Column('privacy_protection_applied', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_peer_comparisons_user_id'), 'peer_comparisons', ['user_id'], unique=False)
    op.create_index(op.f('ix_peer_comparisons_cohort_age_group'), 'peer_comparisons', ['cohort_age_group'], unique=False)

    # Additional tables would be created here for forums, group goals, mentorship, etc.
    # Due to space constraints, I'll create the key structural ones
    
    # Create forum categories table
    op.create_table('forum_categories',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.Column('is_public', sa.Boolean(), nullable=False),
        sa.Column('is_flagged', sa.Boolean(), nullable=False),
        sa.Column('moderation_notes', sa.Text(), nullable=True),
        sa.Column('moderated_at', sa.DateTime(), nullable=True),
        sa.Column('moderated_by_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('name', sa.String(length=100), nullable=False, unique=True),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('forum_type', forum_type_enum, nullable=False),
        sa.Column('parent_category_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('display_order', sa.Integer(), nullable=False),
        sa.Column('is_moderated', sa.Boolean(), nullable=False),
        sa.Column('requires_approval', sa.Boolean(), nullable=False),
        sa.Column('is_read_only', sa.Boolean(), nullable=False),
        sa.Column('minimum_experience_level', sa.String(length=20), nullable=True),
        sa.Column('is_private', sa.Boolean(), nullable=False),
        sa.Column('allowed_user_groups', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('topics_count', sa.Integer(), nullable=False),
        sa.Column('posts_count', sa.Integer(), nullable=False),
        sa.Column('participants_count', sa.Integer(), nullable=False),
        sa.Column('last_post_at', sa.DateTime(), nullable=True),
        sa.Column('last_post_user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('last_topic_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('moderator_user_ids', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('moderation_rules', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('auto_moderation_enabled', sa.Boolean(), nullable=False),
        sa.Column('icon_name', sa.String(length=50), nullable=True),
        sa.Column('color_theme', sa.String(length=20), nullable=True),
        sa.Column('banner_image_url', sa.String(length=500), nullable=True),
        sa.ForeignKeyConstraint(['last_post_user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['parent_category_id'], ['forum_categories.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Set default values for existing tables (if any)
    op.execute("UPDATE user_social_profiles SET reputation_score = 0 WHERE reputation_score IS NULL")
    op.execute("UPDATE user_social_profiles SET total_contributions = 0 WHERE total_contributions IS NULL")
    op.execute("UPDATE user_social_profiles SET helpful_votes_received = 0 WHERE helpful_votes_received IS NULL")
    op.execute("UPDATE user_social_profiles SET challenges_completed = 0 WHERE challenges_completed IS NULL")
    op.execute("UPDATE user_social_profiles SET following_count = 0 WHERE following_count IS NULL")
    op.execute("UPDATE user_social_profiles SET followers_count = 0 WHERE followers_count IS NULL")
    op.execute("UPDATE user_social_profiles SET posts_count = 0 WHERE posts_count IS NULL")
    op.execute("UPDATE user_social_profiles SET comments_count = 0 WHERE comments_count IS NULL")


def downgrade():
    # Drop tables in reverse order
    op.drop_table('forum_categories')
    op.drop_table('peer_comparisons')
    op.drop_table('anonymous_goal_shares')
    op.drop_table('user_privacy_settings')
    op.drop_table('user_social_profiles')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS communicationpreference')
    op.execute('DROP TYPE IF EXISTS sessionstatus')
    op.execute('DROP TYPE IF EXISTS mentorshipstatus')
    op.execute('DROP TYPE IF EXISTS expertiselevel')
    op.execute('DROP TYPE IF EXISTS mentorshiptype')
    op.execute('DROP TYPE IF EXISTS participantrole')
    op.execute('DROP TYPE IF EXISTS groupgoalstatus')
    op.execute('DROP TYPE IF EXISTS groupgoaltype')
    op.execute('DROP TYPE IF EXISTS moderationreason')
    op.execute('DROP TYPE IF EXISTS moderationaction')
    op.execute('DROP TYPE IF EXISTS posttype')
    op.execute('DROP TYPE IF EXISTS topicstatus')
    op.execute('DROP TYPE IF EXISTS forumtype')
    op.execute('DROP TYPE IF EXISTS incomerange')
    op.execute('DROP TYPE IF EXISTS agegroup')
    op.execute('DROP TYPE IF EXISTS goalcategory')
    op.execute('DROP TYPE IF EXISTS sharingpreference')
    op.execute('DROP TYPE IF EXISTS privacylevel')