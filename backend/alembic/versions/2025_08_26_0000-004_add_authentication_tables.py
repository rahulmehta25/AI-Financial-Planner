"""Add authentication tables

Revision ID: 2025_08_26_0000-004
Revises: 2025_08_22_1600-003
Create Date: 2025-08-26 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '2025_08_26_0000-004'
down_revision = '2025_08_22_1600-003'
branch_labels = None
depends_on = None


def upgrade():
    """
    Create authentication-related tables
    """
    
    # Token blacklist table
    op.create_table('token_blacklist',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('jti', sa.String(255), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('token_type', sa.String(50), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('blacklisted_at', sa.DateTime(), nullable=False),
        sa.Column('reason', sa.String(100), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('jti'),
        comment='Blacklisted JWT tokens for secure logout'
    )
    
    # Create indexes for token_blacklist
    op.create_index('idx_token_blacklist_jti_expires', 'token_blacklist', ['jti', 'expires_at'])
    op.create_index('idx_token_blacklist_user_expires', 'token_blacklist', ['user_id', 'expires_at'])
    
    # User sessions table
    op.create_table('user_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('session_id', sa.String(255), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('device_fingerprint', sa.String(255), nullable=True),
        sa.Column('location', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('last_activity', sa.DateTime(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('terminated_at', sa.DateTime(), nullable=True),
        sa.Column('termination_reason', sa.String(100), nullable=True),
        sa.Column('is_suspicious', sa.Boolean(), nullable=False),
        sa.Column('failed_attempts', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('session_id'),
        comment='Active user sessions for authentication tracking'
    )
    
    # Create indexes for user_sessions
    op.create_index('idx_user_sessions_user_active', 'user_sessions', ['user_id', 'is_active'])
    op.create_index('idx_user_sessions_expires_active', 'user_sessions', ['expires_at', 'is_active'])
    op.create_index('idx_user_sessions_session_id', 'user_sessions', ['session_id'])
    
    # Login attempts table
    op.create_table('login_attempts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('success', sa.Boolean(), nullable=False),
        sa.Column('attempted_at', sa.DateTime(), nullable=False),
        sa.Column('failure_reason', sa.String(255), nullable=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('is_suspicious', sa.Boolean(), nullable=False),
        sa.Column('blocked', sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        comment='Login attempts for security monitoring'
    )
    
    # Create indexes for login_attempts
    op.create_index('idx_login_attempts_email_time', 'login_attempts', ['email', 'attempted_at'])
    op.create_index('idx_login_attempts_ip_time', 'login_attempts', ['ip_address', 'attempted_at'])
    op.create_index('idx_login_attempts_success_time', 'login_attempts', ['success', 'attempted_at'])
    
    # Password reset tokens table
    op.create_table('password_reset_tokens',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('token', sa.String(255), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('used_at', sa.DateTime(), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('is_used', sa.Boolean(), nullable=False),
        sa.Column('is_valid', sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token'),
        comment='Password reset tokens'
    )
    
    # Two-factor authentication table
    op.create_table('two_factor_auth',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('secret_key', sa.String(255), nullable=False),
        sa.Column('is_enabled', sa.Boolean(), nullable=False),
        sa.Column('backup_codes', sa.Text(), nullable=True),
        sa.Column('setup_at', sa.DateTime(), nullable=True),
        sa.Column('last_used_at', sa.DateTime(), nullable=True),
        sa.Column('recovery_codes_generated_at', sa.DateTime(), nullable=True),
        sa.Column('recovery_codes_count', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id'),
        comment='Two-factor authentication settings'
    )
    
    # Security events table
    op.create_table('security_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('event_type', sa.String(100), nullable=False),
        sa.Column('event_description', sa.Text(), nullable=True),
        sa.Column('severity', sa.String(20), nullable=False),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('metadata', sa.Text(), nullable=True),
        sa.Column('resolved', sa.Boolean(), nullable=False),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        comment='Security events and audit trail'
    )
    
    # Create indexes for security_events
    op.create_index('idx_security_events_user_time', 'security_events', ['user_id', 'timestamp'])
    op.create_index('idx_security_events_type_time', 'security_events', ['event_type', 'timestamp'])
    op.create_index('idx_security_events_severity', 'security_events', ['severity', 'timestamp'])
    
    # Set default values for existing tables
    op.execute("UPDATE users SET email_verified = false WHERE email_verified IS NULL")


def downgrade():
    """
    Drop authentication-related tables
    """
    
    # Drop indexes first
    op.drop_index('idx_security_events_severity', table_name='security_events')
    op.drop_index('idx_security_events_type_time', table_name='security_events')
    op.drop_index('idx_security_events_user_time', table_name='security_events')
    op.drop_index('idx_login_attempts_success_time', table_name='login_attempts')
    op.drop_index('idx_login_attempts_ip_time', table_name='login_attempts')
    op.drop_index('idx_login_attempts_email_time', table_name='login_attempts')
    op.drop_index('idx_user_sessions_session_id', table_name='user_sessions')
    op.drop_index('idx_user_sessions_expires_active', table_name='user_sessions')
    op.drop_index('idx_user_sessions_user_active', table_name='user_sessions')
    op.drop_index('idx_token_blacklist_user_expires', table_name='token_blacklist')
    op.drop_index('idx_token_blacklist_jti_expires', table_name='token_blacklist')
    
    # Drop tables
    op.drop_table('security_events')
    op.drop_table('two_factor_auth')
    op.drop_table('password_reset_tokens')
    op.drop_table('login_attempts')
    op.drop_table('user_sessions')
    op.drop_table('token_blacklist')