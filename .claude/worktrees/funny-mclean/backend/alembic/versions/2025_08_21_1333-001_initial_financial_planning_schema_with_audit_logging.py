"""Initial financial planning schema with audit logging

Revision ID: 001_initial_schema
Revises: 
Create Date: 2025-08-21 13:33:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic
revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create the initial financial planning database schema with comprehensive audit logging"""
    
    # Create UUID extension
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    
    # Create users table
    op.create_table('users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('first_name', sa.String(length=100), nullable=False),
        sa.Column('last_name', sa.String(length=100), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('is_superuser', sa.Boolean(), nullable=False, default=False),
        sa.Column('is_verified', sa.Boolean(), nullable=False, default=False),
        sa.Column('timezone', sa.String(length=50), default='UTC'),
        sa.Column('locale', sa.String(length=10), default='en_US'),
        sa.Column('preferences', postgresql.JSONB(), default={}),
        sa.Column('company', sa.String(length=255)),
        sa.Column('title', sa.String(length=255)),
        sa.Column('license_number', sa.String(length=100)),
        sa.Column('last_login', postgresql.TIMESTAMP(timezone=True)),
        sa.Column('failed_login_attempts', sa.Integer(), default=0),
        sa.Column('locked_until', postgresql.TIMESTAMP(timezone=True)),
        sa.Column('password_changed_at', postgresql.TIMESTAMP(timezone=True)),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True)),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True)),
    )
    
    # Create indexes for users table
    op.create_index('idx_users_email', 'users', ['email'], unique=True)
    op.create_index('idx_users_created_at', 'users', ['created_at'])
    op.create_index('idx_users_updated_at', 'users', ['updated_at'])
    op.create_index('idx_users_created_by', 'users', ['created_by'])
    op.create_index('idx_users_updated_by', 'users', ['updated_by'])
    
    # Create capital market assumptions table
    op.create_table('capital_market_assumptions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('version', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('effective_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('assumptions', postgresql.JSONB(), nullable=False),
        sa.Column('source', sa.String(length=255)),
        sa.Column('methodology', sa.Text()),
        sa.Column('review_date', sa.DateTime(timezone=True)),
        sa.Column('approved_by', postgresql.UUID(as_uuid=True)),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True)),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True)),
    )
    
    # Create indexes and constraints for CMA table
    op.create_index('idx_cma_version', 'capital_market_assumptions', ['version'], unique=True)
    op.create_index('idx_cma_effective_date', 'capital_market_assumptions', ['effective_date'])
    op.create_index('idx_cma_active', 'capital_market_assumptions', ['is_active'])
    
    # Create portfolio models table
    op.create_table('portfolio_models',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('risk_level', sa.Integer(), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('asset_allocation', postgresql.JSONB(), nullable=False),
        sa.Column('expected_return', sa.NUMERIC(5, 4)),
        sa.Column('volatility', sa.NUMERIC(5, 4)),
        sa.Column('sharpe_ratio', sa.NUMERIC(5, 4)),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True)),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True)),
        sa.CheckConstraint('risk_level >= 1 AND risk_level <= 10', name='check_risk_level'),
    )
    
    # Create indexes for portfolio models
    op.create_index('idx_portfolio_risk_level', 'portfolio_models', ['risk_level'])
    op.create_index('idx_portfolio_active', 'portfolio_models', ['is_active'])
    
    # Create plans table
    op.create_table('plans',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('status', sa.String(length=50), nullable=False, default='draft'),
        sa.Column('version', sa.Integer(), nullable=False, default=1),
        sa.Column('parent_plan_id', postgresql.UUID(as_uuid=True)),
        sa.Column('cma_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('portfolio_model_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('monte_carlo_iterations', sa.Integer(), default=10000),
        sa.Column('random_seed', sa.BigInteger(), nullable=False),
        sa.Column('planning_horizon_years', sa.Integer(), nullable=False),
        sa.Column('confidence_level', sa.NUMERIC(3, 2), default=0.95),
        sa.Column('last_run_at', postgresql.TIMESTAMP(timezone=True)),
        sa.Column('completed_at', postgresql.TIMESTAMP(timezone=True)),
        sa.Column('tags', postgresql.JSONB(), default=[]),
        sa.Column('category', sa.String(length=100)),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True)),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True)),
        sa.CheckConstraint('planning_horizon_years > 0', name='check_planning_horizon'),
        sa.CheckConstraint('monte_carlo_iterations > 0', name='check_monte_carlo_iterations'),
        sa.CheckConstraint('confidence_level > 0 AND confidence_level < 1', name='check_confidence_level'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['parent_plan_id'], ['plans.id'], ),
        sa.ForeignKeyConstraint(['cma_id'], ['capital_market_assumptions.id'], ),
        sa.ForeignKeyConstraint(['portfolio_model_id'], ['portfolio_models.id'], ),
    )
    
    # Create indexes for plans table
    op.create_index('idx_plan_user_status', 'plans', ['user_id', 'status'])
    op.create_index('idx_plan_last_run', 'plans', ['last_run_at'])
    op.create_index('idx_plan_random_seed', 'plans', ['random_seed'])
    
    # Create plan inputs table
    op.create_table('plan_inputs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('plan_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('input_type', sa.String(length=100), nullable=False),
        sa.Column('input_name', sa.String(length=255), nullable=False),
        sa.Column('input_value', postgresql.JSONB(), nullable=False),
        sa.Column('validation_rules', postgresql.JSONB()),
        sa.Column('is_valid', sa.Boolean(), default=True),
        sa.Column('validation_errors', postgresql.JSONB()),
        sa.Column('data_source', sa.String(length=100)),
        sa.Column('confidence_score', sa.NUMERIC(3, 2)),
        sa.Column('version', sa.Integer(), default=1),
        sa.Column('superseded_by', postgresql.UUID(as_uuid=True)),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True)),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True)),
        sa.ForeignKeyConstraint(['plan_id'], ['plans.id'], ),
        sa.ForeignKeyConstraint(['superseded_by'], ['plan_inputs.id'], ),
    )
    
    # Create indexes for plan inputs
    op.create_index('idx_plan_input_type', 'plan_inputs', ['plan_id', 'input_type'])
    op.create_index('idx_plan_input_name', 'plan_inputs', ['plan_id', 'input_name'])
    op.create_index('idx_plan_input_version', 'plan_inputs', ['plan_id', 'version'])
    
    # Create plan outputs table
    op.create_table('plan_outputs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('plan_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('output_type', sa.String(length=100), nullable=False),
        sa.Column('output_name', sa.String(length=255), nullable=False),
        sa.Column('output_value', postgresql.JSONB(), nullable=False),
        sa.Column('computation_time_ms', sa.Integer()),
        sa.Column('algorithm_version', sa.String(length=50)),
        sa.Column('confidence_interval_lower', sa.NUMERIC(15, 2)),
        sa.Column('confidence_interval_upper', sa.NUMERIC(15, 2)),
        sa.Column('standard_deviation', sa.NUMERIC(15, 2)),
        sa.Column('version', sa.Integer(), default=1),
        sa.Column('depends_on_inputs', postgresql.JSONB()),
        sa.Column('depends_on_outputs', postgresql.JSONB()),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True)),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True)),
        sa.ForeignKeyConstraint(['plan_id'], ['plans.id'], ),
    )
    
    # Create indexes for plan outputs
    op.create_index('idx_plan_output_type', 'plan_outputs', ['plan_id', 'output_type'])
    op.create_index('idx_plan_output_name', 'plan_outputs', ['plan_id', 'output_name'])
    op.create_index('idx_plan_output_version', 'plan_outputs', ['plan_id', 'version'])
    
    # Create audit logs table with partitioning support
    op.create_table('audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('timestamp', postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True)),
        sa.Column('session_id', sa.String(length=255)),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('resource_type', sa.String(length=100), nullable=False),
        sa.Column('resource_id', postgresql.UUID(as_uuid=True)),
        sa.Column('ip_address', sa.String(length=45)),
        sa.Column('user_agent', sa.Text()),
        sa.Column('request_id', postgresql.UUID(as_uuid=True)),
        sa.Column('old_values', postgresql.JSONB()),
        sa.Column('new_values', postgresql.JSONB()),
        sa.Column('changed_fields', postgresql.JSONB()),
        sa.Column('metadata', postgresql.JSONB()),
        sa.Column('severity', sa.String(length=20), default='info'),
        sa.Column('compliance_category', sa.String(length=100)),
        sa.Column('retention_until', postgresql.TIMESTAMP(timezone=True)),
        sa.Column('execution_time_ms', sa.Integer()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    )
    
    # Create indexes for audit logs
    op.create_index('idx_audit_timestamp', 'audit_logs', ['timestamp'])
    op.create_index('idx_audit_user_action', 'audit_logs', ['user_id', 'action'])
    op.create_index('idx_audit_resource', 'audit_logs', ['resource_type', 'resource_id'])
    op.create_index('idx_audit_session', 'audit_logs', ['session_id', 'timestamp'])
    op.create_index('idx_audit_request', 'audit_logs', ['request_id'])
    op.create_index('idx_audit_severity', 'audit_logs', ['severity', 'timestamp'])
    
    # Create system events table
    op.create_table('system_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('timestamp', postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('event_type', sa.String(length=100), nullable=False),
        sa.Column('event_category', sa.String(length=100), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('severity', sa.String(length=20), nullable=False, default='info'),
        sa.Column('component', sa.String(length=100)),
        sa.Column('environment', sa.String(length=50)),
        sa.Column('version', sa.String(length=50)),
        sa.Column('error_code', sa.String(length=50)),
        sa.Column('stack_trace', sa.Text()),
        sa.Column('additional_data', postgresql.JSONB()),
        sa.Column('duration_ms', sa.Integer()),
        sa.Column('memory_usage_mb', sa.Integer()),
        sa.Column('cpu_usage_percent', sa.NUMERIC(5, 2)),
        sa.Column('resolved', sa.Boolean(), default=False),
        sa.Column('resolved_at', postgresql.TIMESTAMP(timezone=True)),
        sa.Column('resolved_by', postgresql.UUID(as_uuid=True)),
        sa.Column('resolution_notes', sa.Text()),
    )
    
    # Create indexes for system events
    op.create_index('idx_system_event_timestamp', 'system_events', ['timestamp'])
    op.create_index('idx_system_event_type', 'system_events', ['event_type', 'severity'])
    op.create_index('idx_system_event_category', 'system_events', ['event_category', 'timestamp'])
    op.create_index('idx_system_event_resolved', 'system_events', ['resolved', 'timestamp'])
    
    # Create data retention policies table
    op.create_table('data_retention_policies',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('table_name', sa.String(length=100), nullable=False),
        sa.Column('conditions', postgresql.JSONB()),
        sa.Column('retention_period_days', sa.Integer(), nullable=False),
        sa.Column('action', sa.String(length=50), nullable=False, default='delete'),
        sa.Column('schedule_cron', sa.String(length=100)),
        sa.Column('last_executed', postgresql.TIMESTAMP(timezone=True)),
        sa.Column('next_execution', postgresql.TIMESTAMP(timezone=True)),
        sa.Column('records_processed', sa.BigInteger(), default=0),
        sa.Column('last_execution_duration_ms', sa.Integer()),
        sa.Column('last_execution_status', sa.String(length=50)),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True)),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True)),
        sa.CheckConstraint('retention_period_days > 0', name='check_retention_period'),
    )
    
    # Create indexes for data retention policies
    op.create_index('idx_retention_policy_name', 'data_retention_policies', ['name'], unique=True)
    op.create_index('idx_retention_policy_active', 'data_retention_policies', ['is_active'])
    op.create_index('idx_retention_policy_next_execution', 'data_retention_policies', ['next_execution'])
    
    # Create audit trigger function for comprehensive logging
    op.execute("""
        CREATE OR REPLACE FUNCTION audit_trigger_function()
        RETURNS TRIGGER AS $$
        DECLARE
            audit_row audit_logs%ROWTYPE;
            include_values BOOLEAN = TRUE;
            log_diffs BOOLEAN = TRUE;
            h_old jsonb;
            h_new jsonb;
        BEGIN
            -- Initialize the audit record
            audit_row.id = uuid_generate_v4();
            audit_row.timestamp = current_timestamp;
            audit_row.resource_type = TG_TABLE_NAME::text;
            audit_row.severity = 'info';
            
            -- Set action based on TG_OP
            IF TG_OP = 'DELETE' THEN
                audit_row.action = 'DELETE';
                audit_row.resource_id = OLD.id;
                IF include_values THEN
                    audit_row.old_values = to_jsonb(OLD);
                END IF;
            ELSIF TG_OP = 'INSERT' THEN
                audit_row.action = 'CREATE';
                audit_row.resource_id = NEW.id;
                IF include_values THEN
                    audit_row.new_values = to_jsonb(NEW);
                END IF;
            ELSIF TG_OP = 'UPDATE' THEN
                audit_row.action = 'UPDATE';
                audit_row.resource_id = NEW.id;
                IF include_values THEN
                    audit_row.old_values = to_jsonb(OLD);
                    audit_row.new_values = to_jsonb(NEW);
                    
                    -- Calculate changed fields
                    IF log_diffs THEN
                        WITH old_record AS (SELECT to_jsonb(OLD) as j),
                             new_record AS (SELECT to_jsonb(NEW) as j),
                             changes AS (
                                SELECT array_agg(key) as changed_fields
                                FROM (
                                    SELECT key
                                    FROM jsonb_each(old_record.j)
                                    WHERE key NOT IN ('updated_at', 'version')
                                    AND jsonb_extract_path(old_record.j, key) IS DISTINCT FROM jsonb_extract_path(new_record.j, key)
                                    UNION
                                    SELECT key
                                    FROM jsonb_each(new_record.j)
                                    WHERE key NOT IN ('updated_at', 'version')
                                    AND jsonb_extract_path(old_record.j, key) IS DISTINCT FROM jsonb_extract_path(new_record.j, key)
                                ) t
                             )
                        SELECT to_jsonb(changed_fields) INTO audit_row.changed_fields FROM changes;
                    END IF;
                END IF;
            END IF;
            
            -- Insert the audit record
            INSERT INTO audit_logs VALUES (audit_row.*);
            
            -- Return appropriate record
            IF TG_OP = 'DELETE' THEN
                RETURN OLD;
            ELSE
                RETURN NEW;
            END IF;
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    # Create audit triggers for key tables
    audit_tables = ['users', 'plans', 'plan_inputs', 'plan_outputs', 'capital_market_assumptions', 'portfolio_models']
    for table in audit_tables:
        op.execute(f"""
            CREATE TRIGGER {table}_audit_trigger
            AFTER INSERT OR UPDATE OR DELETE ON {table}
            FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();
        """)
    
    # Create function for automatic timestamp updates
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = current_timestamp;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    # Create update triggers for timestamp management
    timestamp_tables = ['users', 'plans', 'plan_inputs', 'plan_outputs', 'capital_market_assumptions', 
                       'portfolio_models', 'data_retention_policies']
    for table in timestamp_tables:
        op.execute(f"""
            CREATE TRIGGER {table}_update_timestamp
            BEFORE UPDATE ON {table}
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
        """)
    
    # Create partitioned table for audit_logs (monthly partitions)
    op.execute("""
        -- Create partitioned audit_logs table for better performance
        DROP TABLE IF EXISTS audit_logs_partitioned;
        CREATE TABLE audit_logs_partitioned (
            LIKE audit_logs INCLUDING ALL
        ) PARTITION BY RANGE (timestamp);
        
        -- Create initial partitions for the next 12 months
        CREATE TABLE audit_logs_2025_08 PARTITION OF audit_logs_partitioned
            FOR VALUES FROM ('2025-08-01') TO ('2025-09-01');
        CREATE TABLE audit_logs_2025_09 PARTITION OF audit_logs_partitioned
            FOR VALUES FROM ('2025-09-01') TO ('2025-10-01');
        CREATE TABLE audit_logs_2025_10 PARTITION OF audit_logs_partitioned
            FOR VALUES FROM ('2025-10-01') TO ('2025-11-01');
        CREATE TABLE audit_logs_2025_11 PARTITION OF audit_logs_partitioned
            FOR VALUES FROM ('2025-11-01') TO ('2025-12-01');
        CREATE TABLE audit_logs_2025_12 PARTITION OF audit_logs_partitioned
            FOR VALUES FROM ('2025-12-01') TO ('2026-01-01');
        CREATE TABLE audit_logs_2026_01 PARTITION OF audit_logs_partitioned
            FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');
        CREATE TABLE audit_logs_2026_02 PARTITION OF audit_logs_partitioned
            FOR VALUES FROM ('2026-02-01') TO ('2026-03-01');
        CREATE TABLE audit_logs_2026_03 PARTITION OF audit_logs_partitioned
            FOR VALUES FROM ('2026-03-01') TO ('2026-04-01');
        CREATE TABLE audit_logs_2026_04 PARTITION OF audit_logs_partitioned
            FOR VALUES FROM ('2026-04-01') TO ('2026-05-01');
        CREATE TABLE audit_logs_2026_05 PARTITION OF audit_logs_partitioned
            FOR VALUES FROM ('2026-05-01') TO ('2026-06-01');
        CREATE TABLE audit_logs_2026_06 PARTITION OF audit_logs_partitioned
            FOR VALUES FROM ('2026-06-01') TO ('2026-07-01');
        CREATE TABLE audit_logs_2026_07 PARTITION OF audit_logs_partitioned
            FOR VALUES FROM ('2026-07-01') TO ('2026-08-01');
    """)


def downgrade() -> None:
    """Drop all tables and extensions"""
    
    # Drop all audit triggers first
    audit_tables = ['users', 'plans', 'plan_inputs', 'plan_outputs', 'capital_market_assumptions', 'portfolio_models']
    for table in audit_tables:
        op.execute(f"DROP TRIGGER IF EXISTS {table}_audit_trigger ON {table}")
    
    # Drop update triggers
    timestamp_tables = ['users', 'plans', 'plan_inputs', 'plan_outputs', 'capital_market_assumptions', 
                       'portfolio_models', 'data_retention_policies']
    for table in timestamp_tables:
        op.execute(f"DROP TRIGGER IF EXISTS {table}_update_timestamp ON {table}")
    
    # Drop functions
    op.execute("DROP FUNCTION IF EXISTS audit_trigger_function() CASCADE")
    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column() CASCADE")
    
    # Drop partitioned audit logs
    op.execute("DROP TABLE IF EXISTS audit_logs_partitioned CASCADE")
    
    # Drop all tables in reverse dependency order
    op.drop_table('data_retention_policies')
    op.drop_table('system_events')
    op.drop_table('audit_logs')
    op.drop_table('plan_outputs')
    op.drop_table('plan_inputs')
    op.drop_table('plans')
    op.drop_table('portfolio_models')
    op.drop_table('capital_market_assumptions')
    op.drop_table('users')
    
    # Drop UUID extension
    op.execute('DROP EXTENSION IF EXISTS "uuid-ossp"')