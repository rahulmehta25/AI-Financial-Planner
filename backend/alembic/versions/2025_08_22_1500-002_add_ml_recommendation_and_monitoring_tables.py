"""Add ML recommendation and monitoring tables

Revision ID: 002_ml_recommendations
Revises: 001_initial_financial_planning_schema_with_audit_logging
Create Date: 2025-08-22 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '002_ml_recommendations'
down_revision: Union[str, None] = '001_initial_financial_planning_schema_with_audit_logging'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enum types
    op.execute("CREATE TYPE recommendationtype AS ENUM ('goal_optimization', 'portfolio_rebalancing', 'risk_assessment', 'behavioral_insights', 'peer_insights', 'savings_strategy', 'life_planning')")
    op.execute("CREATE TYPE recommendationpriority AS ENUM ('low', 'medium', 'high', 'critical')")
    op.execute("CREATE TYPE recommendationstatus AS ENUM ('active', 'viewed', 'acted_upon', 'dismissed', 'expired')")

    # Create ml_recommendations table
    op.create_table(
        'ml_recommendations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('recommendation_type', sa.Enum('goal_optimization', 'portfolio_rebalancing', 'risk_assessment', 'behavioral_insights', 'peer_insights', 'savings_strategy', 'life_planning', name='recommendationtype'), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('priority', sa.Enum('low', 'medium', 'high', 'critical', name='recommendationpriority'), nullable=True),
        sa.Column('status', sa.Enum('active', 'viewed', 'acted_upon', 'dismissed', 'expired', name='recommendationstatus'), nullable=True),
        sa.Column('model_name', sa.String(length=100), nullable=False),
        sa.Column('model_version', sa.String(length=50), nullable=True),
        sa.Column('confidence_score', sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column('recommendation_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('actionable_items', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('expected_impact', sa.String(length=50), nullable=True),
        sa.Column('effort_level', sa.String(length=50), nullable=True),
        sa.Column('valid_until', sa.DateTime(), nullable=True),
        sa.Column('viewed_at', sa.DateTime(), nullable=True),
        sa.Column('acted_upon_at', sa.DateTime(), nullable=True),
        sa.Column('dismissed_at', sa.DateTime(), nullable=True),
        sa.Column('user_rating', sa.Integer(), nullable=True),
        sa.Column('user_feedback', sa.Text(), nullable=True),
        sa.Column('effectiveness_score', sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ml_recommendations_user_id'), 'ml_recommendations', ['user_id'], unique=False)
    op.create_index(op.f('ix_ml_recommendations_recommendation_type'), 'ml_recommendations', ['recommendation_type'], unique=False)
    op.create_index(op.f('ix_ml_recommendations_status'), 'ml_recommendations', ['status'], unique=False)
    op.create_index(op.f('ix_ml_recommendations_created_at'), 'ml_recommendations', ['created_at'], unique=False)

    # Create ml_model_performance table
    op.create_table(
        'ml_model_performance',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('model_name', sa.String(length=100), nullable=False),
        sa.Column('model_version', sa.String(length=50), nullable=True),
        sa.Column('metric_name', sa.String(length=100), nullable=False),
        sa.Column('metric_value', sa.Numeric(precision=15, scale=8), nullable=False),
        sa.Column('baseline_value', sa.Numeric(precision=15, scale=8), nullable=True),
        sa.Column('threshold_value', sa.Numeric(precision=15, scale=8), nullable=True),
        sa.Column('data_points', sa.Integer(), nullable=True),
        sa.Column('evaluation_period_start', sa.DateTime(), nullable=True),
        sa.Column('evaluation_period_end', sa.DateTime(), nullable=True),
        sa.Column('evaluation_context', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('is_degraded', sa.Boolean(), nullable=True),
        sa.Column('degradation_severity', sa.String(length=20), nullable=True),
        sa.Column('recorded_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ml_model_performance_model_name'), 'ml_model_performance', ['model_name'], unique=False)
    op.create_index(op.f('ix_ml_model_performance_recorded_at'), 'ml_model_performance', ['recorded_at'], unique=False)

    # Create ml_data_drift_alerts table
    op.create_table(
        'ml_data_drift_alerts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('model_name', sa.String(length=100), nullable=False),
        sa.Column('feature_name', sa.String(length=100), nullable=True),
        sa.Column('drift_score', sa.Numeric(precision=10, scale=6), nullable=False),
        sa.Column('drift_threshold', sa.Numeric(precision=10, scale=6), nullable=False),
        sa.Column('drift_severity', sa.String(length=20), nullable=False),
        sa.Column('reference_period_start', sa.DateTime(), nullable=True),
        sa.Column('reference_period_end', sa.DateTime(), nullable=True),
        sa.Column('current_period_start', sa.DateTime(), nullable=True),
        sa.Column('current_period_end', sa.DateTime(), nullable=True),
        sa.Column('is_acknowledged', sa.Boolean(), nullable=True),
        sa.Column('acknowledged_by', sa.String(length=100), nullable=True),
        sa.Column('acknowledged_at', sa.DateTime(), nullable=True),
        sa.Column('resolution_notes', sa.Text(), nullable=True),
        sa.Column('drift_details', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('detected_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ml_data_drift_alerts_model_name'), 'ml_data_drift_alerts', ['model_name'], unique=False)
    op.create_index(op.f('ix_ml_data_drift_alerts_detected_at'), 'ml_data_drift_alerts', ['detected_at'], unique=False)

    # Create ml_retraining_jobs table
    op.create_table(
        'ml_retraining_jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('job_id', sa.String(length=50), nullable=False),
        sa.Column('model_name', sa.String(length=100), nullable=False),
        sa.Column('trigger_reason', sa.String(length=200), nullable=False),
        sa.Column('trigger_type', sa.String(length=50), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('progress_percentage', sa.Integer(), nullable=True),
        sa.Column('training_config', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('data_version', sa.String(length=50), nullable=True),
        sa.Column('old_model_version', sa.String(length=50), nullable=True),
        sa.Column('new_model_version', sa.String(length=50), nullable=True),
        sa.Column('performance_improvement', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('training_metrics', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('estimated_completion', sa.DateTime(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('job_id')
    )
    op.create_index(op.f('ix_ml_retraining_jobs_model_name'), 'ml_retraining_jobs', ['model_name'], unique=False)
    op.create_index(op.f('ix_ml_retraining_jobs_status'), 'ml_retraining_jobs', ['status'], unique=False)

    # Create ml_user_interactions table
    op.create_table(
        'ml_user_interactions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('recommendation_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('interaction_type', sa.String(length=50), nullable=False),
        sa.Column('interaction_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('session_id', sa.String(length=100), nullable=True),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['recommendation_id'], ['ml_recommendations.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ml_user_interactions_user_id'), 'ml_user_interactions', ['user_id'], unique=False)
    op.create_index(op.f('ix_ml_user_interactions_timestamp'), 'ml_user_interactions', ['timestamp'], unique=False)

    # Create ml_model_versions table
    op.create_table(
        'ml_model_versions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('model_name', sa.String(length=100), nullable=False),
        sa.Column('version', sa.String(length=50), nullable=False),
        sa.Column('model_type', sa.String(length=50), nullable=True),
        sa.Column('algorithm', sa.String(length=100), nullable=True),
        sa.Column('hyperparameters', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('features', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('training_data_size', sa.Integer(), nullable=True),
        sa.Column('training_data_hash', sa.String(length=64), nullable=True),
        sa.Column('training_duration_seconds', sa.Integer(), nullable=True),
        sa.Column('validation_metrics', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('test_metrics', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('is_production', sa.Boolean(), nullable=True),
        sa.Column('model_file_path', sa.String(length=500), nullable=True),
        sa.Column('artifact_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('trained_at', sa.DateTime(), nullable=False),
        sa.Column('deployed_at', sa.DateTime(), nullable=True),
        sa.Column('retired_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ml_model_versions_model_name'), 'ml_model_versions', ['model_name'], unique=False)
    op.create_index(op.f('ix_ml_model_versions_version'), 'ml_model_versions', ['version'], unique=False)
    op.create_index(op.f('ix_ml_model_versions_is_active'), 'ml_model_versions', ['is_active'], unique=False)

    # Create ml_experiments table
    op.create_table(
        'ml_experiments',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('experiment_name', sa.String(length=200), nullable=False),
        sa.Column('experiment_type', sa.String(length=50), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('control_model_version', sa.String(length=50), nullable=True),
        sa.Column('treatment_model_version', sa.String(length=50), nullable=True),
        sa.Column('traffic_split', sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column('target_metric', sa.String(length=100), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('control_metrics', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('treatment_metrics', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('statistical_significance', sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column('winner', sa.String(length=50), nullable=True),
        sa.Column('planned_start', sa.DateTime(), nullable=True),
        sa.Column('planned_end', sa.DateTime(), nullable=True),
        sa.Column('actual_start', sa.DateTime(), nullable=True),
        sa.Column('actual_end', sa.DateTime(), nullable=True),
        sa.Column('created_by', sa.String(length=100), nullable=True),
        sa.Column('experiment_config', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ml_experiments_experiment_name'), 'ml_experiments', ['experiment_name'], unique=False)
    op.create_index(op.f('ix_ml_experiments_status'), 'ml_experiments', ['status'], unique=False)


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_index(op.f('ix_ml_experiments_status'), table_name='ml_experiments')
    op.drop_index(op.f('ix_ml_experiments_experiment_name'), table_name='ml_experiments')
    op.drop_table('ml_experiments')
    
    op.drop_index(op.f('ix_ml_model_versions_is_active'), table_name='ml_model_versions')
    op.drop_index(op.f('ix_ml_model_versions_version'), table_name='ml_model_versions')
    op.drop_index(op.f('ix_ml_model_versions_model_name'), table_name='ml_model_versions')
    op.drop_table('ml_model_versions')
    
    op.drop_index(op.f('ix_ml_user_interactions_timestamp'), table_name='ml_user_interactions')
    op.drop_index(op.f('ix_ml_user_interactions_user_id'), table_name='ml_user_interactions')
    op.drop_table('ml_user_interactions')
    
    op.drop_index(op.f('ix_ml_retraining_jobs_status'), table_name='ml_retraining_jobs')
    op.drop_index(op.f('ix_ml_retraining_jobs_model_name'), table_name='ml_retraining_jobs')
    op.drop_table('ml_retraining_jobs')
    
    op.drop_index(op.f('ix_ml_data_drift_alerts_detected_at'), table_name='ml_data_drift_alerts')
    op.drop_index(op.f('ix_ml_data_drift_alerts_model_name'), table_name='ml_data_drift_alerts')
    op.drop_table('ml_data_drift_alerts')
    
    op.drop_index(op.f('ix_ml_model_performance_recorded_at'), table_name='ml_model_performance')
    op.drop_index(op.f('ix_ml_model_performance_model_name'), table_name='ml_model_performance')
    op.drop_table('ml_model_performance')
    
    op.drop_index(op.f('ix_ml_recommendations_created_at'), table_name='ml_recommendations')
    op.drop_index(op.f('ix_ml_recommendations_status'), table_name='ml_recommendations')
    op.drop_index(op.f('ix_ml_recommendations_recommendation_type'), table_name='ml_recommendations')
    op.drop_index(op.f('ix_ml_recommendations_user_id'), table_name='ml_recommendations')
    op.drop_table('ml_recommendations')
    
    # Drop enum types
    op.execute("DROP TYPE recommendationstatus")
    op.execute("DROP TYPE recommendationpriority")
    op.execute("DROP TYPE recommendationtype")