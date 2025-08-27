"""add infrastructure and timeseries tables

Revision ID: 005
Revises: 004
Create Date: 2025-08-27 18:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade():
    # Create TimescaleDB extension if not exists
    op.execute("CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;")
    
    # Market data time-series table
    op.create_table('market_data',
        sa.Column('time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('symbol', sa.String(length=20), nullable=False),
        sa.Column('open', sa.Float(), nullable=True),
        sa.Column('high', sa.Float(), nullable=True),
        sa.Column('low', sa.Float(), nullable=True),
        sa.Column('close', sa.Float(), nullable=True),
        sa.Column('volume', sa.BigInteger(), nullable=True),
        sa.Column('vwap', sa.Float(), nullable=True),
        sa.Column('bid', sa.Float(), nullable=True),
        sa.Column('ask', sa.Float(), nullable=True),
        sa.Column('spread', sa.Float(), nullable=True),
        sa.Column('data_source', sa.String(length=50), nullable=True),
        sa.Column('quality_score', sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint('time', 'symbol')
    )
    
    # Convert to TimescaleDB hypertable
    op.execute("""
        SELECT create_hypertable('market_data', 'time',
            chunk_time_interval => INTERVAL '1 day',
            if_not_exists => TRUE);
    """)
    
    # Create index for efficient queries
    op.create_index('idx_market_data_symbol_time', 'market_data', ['symbol', 'time'])
    
    # Portfolio performance time-series
    op.create_table('portfolio_performance',
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('portfolio_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('total_value', sa.Float(), nullable=False),
        sa.Column('daily_return', sa.Float(), nullable=True),
        sa.Column('cumulative_return', sa.Float(), nullable=True),
        sa.Column('volatility', sa.Float(), nullable=True),
        sa.Column('sharpe_ratio', sa.Float(), nullable=True),
        sa.Column('max_drawdown', sa.Float(), nullable=True),
        sa.Column('beta', sa.Float(), nullable=True),
        sa.Column('alpha', sa.Float(), nullable=True),
        sa.Column('tracking_error', sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint('timestamp', 'portfolio_id')
    )
    
    # Convert to hypertable
    op.execute("""
        SELECT create_hypertable('portfolio_performance', 'timestamp',
            chunk_time_interval => INTERVAL '1 day',
            if_not_exists => TRUE);
    """)
    
    op.create_index('idx_portfolio_performance_portfolio_time', 'portfolio_performance', ['portfolio_id', 'timestamp'])
    
    # Simulation results time-series
    op.create_table('simulation_results',
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('simulation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('portfolio_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('scenario_name', sa.String(length=100), nullable=True),
        sa.Column('time_horizon', sa.Integer(), nullable=True),
        sa.Column('num_simulations', sa.Integer(), nullable=True),
        sa.Column('confidence_level', sa.Float(), nullable=True),
        sa.Column('expected_return', sa.Float(), nullable=True),
        sa.Column('expected_volatility', sa.Float(), nullable=True),
        sa.Column('var_95', sa.Float(), nullable=True),
        sa.Column('cvar_95', sa.Float(), nullable=True),
        sa.Column('best_case', sa.Float(), nullable=True),
        sa.Column('worst_case', sa.Float(), nullable=True),
        sa.Column('median_outcome', sa.Float(), nullable=True),
        sa.Column('simulation_paths', postgresql.JSONB(), nullable=True),
        sa.Column('parameters', postgresql.JSONB(), nullable=True),
        sa.PrimaryKeyConstraint('created_at', 'simulation_id')
    )
    
    # Convert to hypertable
    op.execute("""
        SELECT create_hypertable('simulation_results', 'created_at',
            chunk_time_interval => INTERVAL '7 days',
            if_not_exists => TRUE);
    """)
    
    op.create_index('idx_simulation_results_portfolio', 'simulation_results', ['portfolio_id'])
    
    # Task execution tracking
    op.create_table('task_executions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('task_name', sa.String(length=255), nullable=False),
        sa.Column('task_id', sa.String(length=255), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('priority', sa.Integer(), nullable=True),
        sa.Column('queue_name', sa.String(length=100), nullable=True),
        sa.Column('arguments', postgresql.JSONB(), nullable=True),
        sa.Column('result', postgresql.JSONB(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('traceback', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), default=0),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('duration_seconds', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_index('idx_task_executions_task_id', 'task_executions', ['task_id'])
    op.create_index('idx_task_executions_status', 'task_executions', ['status'])
    op.create_index('idx_task_executions_created_at', 'task_executions', ['created_at'])
    
    # Service registry for service mesh
    op.create_table('service_registry',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('service_name', sa.String(length=100), nullable=False),
        sa.Column('instance_id', sa.String(length=255), nullable=False),
        sa.Column('host', sa.String(length=255), nullable=False),
        sa.Column('port', sa.Integer(), nullable=False),
        sa.Column('health_check_url', sa.String(length=255), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('weight', sa.Integer(), default=1),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('last_health_check', sa.DateTime(timezone=True), nullable=True),
        sa.Column('registered_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('service_name', 'host', 'port', name='uq_service_instance')
    )
    
    op.create_index('idx_service_registry_name_status', 'service_registry', ['service_name', 'status'])
    
    # API rate limiting
    op.create_table('api_rate_limits',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('client_identifier', sa.String(length=255), nullable=False),
        sa.Column('endpoint', sa.String(length=255), nullable=True),
        sa.Column('request_count', sa.Integer(), default=0),
        sa.Column('window_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('window_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('limit_exceeded_count', sa.Integer(), default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_index('idx_api_rate_limits_client_window', 'api_rate_limits', 
                    ['client_identifier', 'window_start', 'window_end'])
    
    # Cache metadata for tracking
    op.create_table('cache_metadata',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('cache_key', sa.String(length=500), nullable=False),
        sa.Column('cache_type', sa.String(length=50), nullable=True),
        sa.Column('ttl_seconds', sa.Integer(), nullable=True),
        sa.Column('hit_count', sa.BigInteger(), default=0),
        sa.Column('miss_count', sa.BigInteger(), default=0),
        sa.Column('size_bytes', sa.Integer(), nullable=True),
        sa.Column('last_accessed', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('cache_key', name='uq_cache_key')
    )
    
    op.create_index('idx_cache_metadata_key', 'cache_metadata', ['cache_key'])
    op.create_index('idx_cache_metadata_expires', 'cache_metadata', ['expires_at'])
    
    # Message queue tracking
    op.create_table('message_queue_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('message_id', sa.String(length=255), nullable=False),
        sa.Column('queue_name', sa.String(length=100), nullable=False),
        sa.Column('exchange', sa.String(length=100), nullable=True),
        sa.Column('routing_key', sa.String(length=255), nullable=True),
        sa.Column('message_type', sa.String(length=100), nullable=True),
        sa.Column('payload', postgresql.JSONB(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('retry_count', sa.Integer(), default=0),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('consumed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('acknowledged_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_index('idx_message_queue_logs_message_id', 'message_queue_logs', ['message_id'])
    op.create_index('idx_message_queue_logs_queue_status', 'message_queue_logs', ['queue_name', 'status'])
    
    # Create continuous aggregates for TimescaleDB
    op.execute("""
        CREATE MATERIALIZED VIEW IF NOT EXISTS market_data_hourly
        WITH (timescaledb.continuous) AS
        SELECT 
            time_bucket('1 hour', time) AS hour,
            symbol,
            FIRST(open, time) AS open,
            MAX(high) AS high,
            MIN(low) AS low,
            LAST(close, time) AS close,
            SUM(volume) AS volume,
            AVG(vwap) AS avg_vwap
        FROM market_data
        GROUP BY hour, symbol
        WITH NO DATA;
    """)
    
    op.execute("""
        CREATE MATERIALIZED VIEW IF NOT EXISTS portfolio_performance_daily
        WITH (timescaledb.continuous) AS
        SELECT 
            time_bucket('1 day', timestamp) AS day,
            portfolio_id,
            LAST(total_value, timestamp) AS closing_value,
            AVG(daily_return) AS avg_daily_return,
            AVG(volatility) AS avg_volatility,
            AVG(sharpe_ratio) AS avg_sharpe_ratio
        FROM portfolio_performance
        GROUP BY day, portfolio_id
        WITH NO DATA;
    """)
    
    # Add compression policies for older data
    op.execute("""
        SELECT add_compression_policy('market_data', INTERVAL '7 days');
    """)
    
    op.execute("""
        SELECT add_compression_policy('portfolio_performance', INTERVAL '30 days');
    """)
    
    op.execute("""
        SELECT add_compression_policy('simulation_results', INTERVAL '90 days');
    """)
    
    # Add retention policies
    op.execute("""
        SELECT add_retention_policy('market_data', INTERVAL '5 years');
    """)
    
    op.execute("""
        SELECT add_retention_policy('portfolio_performance', INTERVAL '10 years');
    """)


def downgrade():
    # Drop continuous aggregates first
    op.execute("DROP MATERIALIZED VIEW IF EXISTS portfolio_performance_daily;")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS market_data_hourly;")
    
    # Drop tables
    op.drop_table('message_queue_logs')
    op.drop_table('cache_metadata')
    op.drop_table('api_rate_limits')
    op.drop_table('service_registry')
    op.drop_table('task_executions')
    op.drop_table('simulation_results')
    op.drop_table('portfolio_performance')
    op.drop_table('market_data')
    
    # Note: We don't drop the TimescaleDB extension as other tables might use it