"""Enhanced database schema with comprehensive financial planning models

Revision ID: 007_enhanced_database_schema  
Revises: 2025_08_27_1800-005_add_infrastructure_and_timeseries_tables
Create Date: 2025-08-28 12:00:00.000000

This migration implements the complete database architecture from the Technical Implementation Guide,
including enhanced User, Portfolio, Account, and Transaction models with comprehensive fields for:

- KYC compliance and regulatory tracking
- Multi-factor authentication
- Tax optimization and wash sale detection  
- Plaid integration for bank connectivity
- Portfolio rebalancing and performance analytics
- TimescaleDB optimization for market data
- Comprehensive audit trails

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid


# revision identifiers
revision = '007_enhanced_database_schema'
down_revision = '2025_08_27_1800-005_add_infrastructure_and_timeseries_tables'
branch_labels = None
depends_on = None


def upgrade():
    """Create enhanced database schema"""
    
    # Create enhanced_users table with comprehensive fields
    op.create_table(
        'enhanced_users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('email', sa.String(255), unique=True, nullable=False, index=True),
        sa.Column('password_hash', sa.String(255), nullable=False),
        
        # Multi-Factor Authentication
        sa.Column('mfa_secret', sa.String(32)),
        sa.Column('mfa_enabled', sa.Boolean(), default=False),
        sa.Column('mfa_backup_codes', postgresql.ARRAY(sa.String(10))),
        
        # Basic profile
        sa.Column('first_name', sa.String(100), nullable=False),
        sa.Column('last_name', sa.String(100), nullable=False),
        sa.Column('phone_number', sa.String(20)),
        sa.Column('date_of_birth', sa.DateTime()),
        
        # Enhanced profile (JSONB for flexibility)
        sa.Column('profile', postgresql.JSONB(), default={}),
        
        # Financial risk profiling
        sa.Column('risk_tolerance', sa.Float()),  # 0.0 to 1.0
        sa.Column('investment_horizon', sa.Integer()),  # Years
        sa.Column('tax_bracket', sa.Float()),  # Federal tax bracket
        sa.Column('state_tax_rate', sa.Float()),  # State tax rate
        
        # KYC compliance
        sa.Column('kyc_status', sa.String(20), default='pending'),
        sa.Column('kyc_data', postgresql.JSONB()),
        sa.Column('kyc_verified_at', sa.DateTime(timezone=True)),
        sa.Column('kyc_expires_at', sa.DateTime(timezone=True)),
        
        # Accredited investor status
        sa.Column('accredited_investor', sa.Boolean(), default=False),
        sa.Column('accredited_verified_at', sa.DateTime(timezone=True)),
        sa.Column('accreditation_type', sa.String(50)),
        
        # Account status and security
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('is_verified', sa.Boolean(), default=False),
        sa.Column('is_suspended', sa.Boolean(), default=False),
        sa.Column('suspension_reason', sa.String(255)),
        
        # Security tracking
        sa.Column('last_login', sa.DateTime(timezone=True)),
        sa.Column('failed_login_attempts', sa.Integer(), default=0),
        sa.Column('locked_until', sa.DateTime(timezone=True)),
        sa.Column('password_changed_at', sa.DateTime(timezone=True)),
        
        # Terms and agreements
        sa.Column('terms_accepted_at', sa.DateTime(timezone=True)),
        sa.Column('terms_version', sa.String(10)),
        sa.Column('privacy_policy_accepted_at', sa.DateTime(timezone=True)),
        sa.Column('marketing_consent', sa.Boolean(), default=False),
        
        # Metadata
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    # Enhanced users indexes
    op.create_index('idx_enhanced_user_email_active', 'enhanced_users', ['email', 'is_active'])
    op.create_index('idx_enhanced_user_kyc_status', 'enhanced_users', ['kyc_status'])
    op.create_index('idx_enhanced_user_created_at', 'enhanced_users', ['created_at'])
    op.create_index('idx_enhanced_user_risk_profile', 'enhanced_users', ['risk_tolerance', 'investment_horizon'])
    
    
    # Create enhanced_portfolios table
    op.create_table(
        'enhanced_portfolios',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('enhanced_users.id'), nullable=False),
        
        # Portfolio identification
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.String(500)),
        sa.Column('type', sa.String(20)),  # real, simulated, watchlist, model
        sa.Column('status', sa.String(20), default='active'),
        
        # Financial state
        sa.Column('total_value', postgresql.NUMERIC(15, 2)),
        sa.Column('cash_balance', postgresql.NUMERIC(15, 2), default=0),
        sa.Column('invested_value', postgresql.NUMERIC(15, 2), default=0),
        sa.Column('pending_trades_value', postgresql.NUMERIC(15, 2), default=0),
        
        # Performance metrics
        sa.Column('performance_ytd', postgresql.NUMERIC(8, 4)),
        sa.Column('performance_1year', postgresql.NUMERIC(8, 4)),
        sa.Column('performance_3year', postgresql.NUMERIC(8, 4)),
        sa.Column('performance_inception', postgresql.NUMERIC(8, 4)),
        
        # Risk metrics
        sa.Column('volatility', postgresql.NUMERIC(6, 4)),
        sa.Column('sharpe_ratio', postgresql.NUMERIC(6, 4)),
        sa.Column('max_drawdown', postgresql.NUMERIC(6, 4)),
        sa.Column('beta', postgresql.NUMERIC(6, 4)),
        
        # Cached calculations
        sa.Column('cached_metrics', postgresql.JSONB(), default={}),
        sa.Column('metrics_updated_at', sa.DateTime(timezone=True)),
        sa.Column('metrics_computation_time', sa.Integer()),
        
        # Rebalancing
        sa.Column('target_allocation', postgresql.JSONB()),
        sa.Column('current_allocation', postgresql.JSONB()),
        sa.Column('rebalancing_threshold', postgresql.NUMERIC(4, 2), default=5.0),
        sa.Column('last_rebalanced_at', sa.DateTime(timezone=True)),
        sa.Column('auto_rebalancing_enabled', sa.Boolean(), default=False),
        
        # Version control
        sa.Column('version', sa.Integer(), default=1),
        
        # Tax considerations
        sa.Column('tax_loss_harvesting_enabled', sa.Boolean(), default=False),
        sa.Column('tax_efficiency_score', postgresql.NUMERIC(4, 2)),
        sa.Column('estimated_tax_drag', postgresql.NUMERIC(6, 4)),
        
        # Metadata
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    # Enhanced portfolios indexes
    op.create_index('idx_enhanced_portfolio_user_type', 'enhanced_portfolios', ['user_id', 'type'])
    op.create_index('idx_enhanced_portfolio_status', 'enhanced_portfolios', ['status'])
    op.create_index('idx_enhanced_portfolio_updated_at', 'enhanced_portfolios', ['updated_at'])
    
    
    # Create enhanced_accounts table
    op.create_table(
        'enhanced_accounts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('portfolio_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('enhanced_portfolios.id')),
        
        # Account identification
        sa.Column('account_type', sa.String(20), nullable=False),
        sa.Column('account_name', sa.String(100)),
        sa.Column('institution', sa.String(100)),
        sa.Column('institution_id', sa.String(50)),
        sa.Column('account_number_encrypted', sa.String(255)),
        sa.Column('routing_number_encrypted', sa.String(255)),
        
        # Account status
        sa.Column('status', sa.String(20), default='active'),
        sa.Column('is_primary', sa.Boolean(), default=False),
        sa.Column('custody_type', sa.String(30)),
        
        # Financial balances
        sa.Column('current_balance', postgresql.NUMERIC(15, 2), nullable=False, default=0),
        sa.Column('available_balance', postgresql.NUMERIC(15, 2), default=0),
        sa.Column('pending_balance', postgresql.NUMERIC(15, 2), default=0),
        
        # Retirement account specific
        sa.Column('vested_balance', postgresql.NUMERIC(15, 2)),
        sa.Column('unvested_balance', postgresql.NUMERIC(15, 2)),
        sa.Column('employer_contribution_ytd', postgresql.NUMERIC(12, 2)),
        sa.Column('employee_contribution_ytd', postgresql.NUMERIC(12, 2)),
        
        # Contribution limits
        sa.Column('annual_contribution_limit', postgresql.NUMERIC(12, 2)),
        sa.Column('catch_up_contribution_limit', postgresql.NUMERIC(12, 2)),
        sa.Column('employer_match_percent', postgresql.NUMERIC(5, 2)),
        sa.Column('employer_match_cap', postgresql.NUMERIC(12, 2)),
        sa.Column('vesting_schedule', postgresql.JSONB()),
        
        # Special account info
        sa.Column('beneficiary_info', postgresql.JSONB()),
        sa.Column('state_plan_info', postgresql.JSONB()),
        sa.Column('hsa_qualified_expenses', postgresql.NUMERIC(12, 2)),
        
        # Tax tracking
        sa.Column('cost_basis', postgresql.NUMERIC(15, 2), default=0),
        sa.Column('unrealized_gains', postgresql.NUMERIC(15, 2), default=0),
        sa.Column('realized_gains_ytd', postgresql.NUMERIC(15, 2), default=0),
        sa.Column('realized_losses_ytd', postgresql.NUMERIC(15, 2), default=0),
        sa.Column('dividend_income_ytd', postgresql.NUMERIC(12, 2), default=0),
        sa.Column('interest_income_ytd', postgresql.NUMERIC(12, 2), default=0),
        sa.Column('tax_loss_carryforward', postgresql.NUMERIC(12, 2), default=0),
        sa.Column('wash_sale_adjustments', postgresql.NUMERIC(12, 2), default=0),
        
        # Plaid integration
        sa.Column('plaid_access_token_encrypted', sa.String(500)),
        sa.Column('plaid_item_id', sa.String(100)),
        sa.Column('plaid_institution_id', sa.String(100)),
        sa.Column('plaid_mask', sa.String(10)),
        sa.Column('last_plaid_sync', sa.DateTime(timezone=True)),
        sa.Column('plaid_sync_status', sa.String(20), default='active'),
        sa.Column('plaid_error_code', sa.String(50)),
        
        # Account features
        sa.Column('margin_enabled', sa.Boolean(), default=False),
        sa.Column('options_level', sa.Integer(), default=0),
        sa.Column('day_trading_buying_power', postgresql.NUMERIC(15, 2), default=0),
        sa.Column('minimum_balance_required', postgresql.NUMERIC(12, 2)),
        sa.Column('monthly_maintenance_fee', postgresql.NUMERIC(6, 2)),
        
        # Metadata
        sa.Column('opened_date', sa.DateTime(timezone=True)),
        sa.Column('closed_date', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    # Enhanced accounts indexes
    op.create_index('idx_enhanced_account_portfolio_type', 'enhanced_accounts', ['portfolio_id', 'account_type'])
    op.create_index('idx_enhanced_account_institution', 'enhanced_accounts', ['institution', 'institution_id'])
    op.create_index('idx_enhanced_account_plaid_item', 'enhanced_accounts', ['plaid_item_id'])
    op.create_index('idx_enhanced_account_status', 'enhanced_accounts', ['status'])
    
    
    # Create enhanced_transactions table
    op.create_table(
        'enhanced_transactions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('account_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('enhanced_accounts.id'), nullable=False),
        
        # Transaction basics
        sa.Column('type', sa.String(30), nullable=False),
        sa.Column('subtype', sa.String(30)),
        sa.Column('status', sa.String(20), default='settled'),
        
        # Security information
        sa.Column('symbol', sa.String(20), index=True),
        sa.Column('security_name', sa.String(200)),
        sa.Column('security_type', sa.String(30)),
        sa.Column('cusip', sa.String(9)),
        sa.Column('isin', sa.String(12)),
        
        # Transaction amounts
        sa.Column('quantity', postgresql.NUMERIC(15, 8)),
        sa.Column('price', postgresql.NUMERIC(12, 4)),
        sa.Column('total_amount', postgresql.NUMERIC(15, 2), nullable=False),
        
        # Fees
        sa.Column('commission', postgresql.NUMERIC(8, 2), default=0),
        sa.Column('sec_fee', postgresql.NUMERIC(6, 2), default=0),
        sa.Column('taf_fee', postgresql.NUMERIC(6, 2), default=0),
        sa.Column('other_fees', postgresql.NUMERIC(8, 2), default=0),
        sa.Column('total_fees', postgresql.NUMERIC(8, 2), default=0),
        
        # Tax lot tracking
        sa.Column('tax_lot_id', postgresql.UUID(as_uuid=True)),
        sa.Column('cost_basis', postgresql.NUMERIC(15, 2)),
        sa.Column('realized_gain_loss', postgresql.NUMERIC(12, 2)),
        
        # Wash sale detection
        sa.Column('wash_sale', sa.Boolean(), default=False),
        sa.Column('wash_sale_disallowed_loss', postgresql.NUMERIC(12, 2)),
        sa.Column('wash_sale_adjustment_to_basis', postgresql.NUMERIC(12, 2)),
        sa.Column('related_wash_sale_transactions', postgresql.ARRAY(postgresql.UUID(as_uuid=True))),
        
        # Tax classification
        sa.Column('tax_category', sa.String(30)),
        sa.Column('holding_period_days', sa.Integer()),
        sa.Column('tax_year', sa.Integer()),
        
        # Dividend specific
        sa.Column('dividend_type', sa.String(20)),
        sa.Column('dividend_per_share', postgresql.NUMERIC(8, 4)),
        sa.Column('reinvestment_flag', sa.Boolean(), default=False),
        
        # Corporate actions
        sa.Column('corporate_action_type', sa.String(30)),
        sa.Column('corporate_action_ratio', sa.String(20)),
        sa.Column('original_transaction_id', postgresql.UUID(as_uuid=True)),
        
        # Timing
        sa.Column('trade_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('settlement_date', sa.DateTime(timezone=True)),
        sa.Column('executed_at', sa.DateTime(timezone=True)),
        
        # Order information
        sa.Column('order_id', sa.String(50)),
        sa.Column('order_type', sa.String(20)),
        sa.Column('time_in_force', sa.String(10)),
        
        # Data source
        sa.Column('data_source', sa.String(50)),
        sa.Column('source_transaction_id', sa.String(100)),
        sa.Column('confidence_score', postgresql.NUMERIC(3, 2), default=1.0),
        sa.Column('requires_review', sa.Boolean(), default=False),
        
        # Metadata
        sa.Column('notes', sa.String(500)),
        sa.Column('tags', postgresql.ARRAY(sa.String(50))),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    # Enhanced transactions indexes - critical for performance
    op.create_index('idx_enhanced_transaction_account_date', 'enhanced_transactions', ['account_id', 'trade_date'])
    op.create_index('idx_enhanced_transaction_symbol_date', 'enhanced_transactions', ['symbol', 'trade_date'])
    op.create_index('idx_enhanced_transaction_type_status', 'enhanced_transactions', ['type', 'status'])
    op.create_index('idx_enhanced_transaction_tax_lot', 'enhanced_transactions', ['tax_lot_id'])
    op.create_index('idx_enhanced_transaction_wash_sale', 'enhanced_transactions', ['account_id', 'wash_sale', 'trade_date'])
    op.create_index('idx_enhanced_transaction_settlement_date', 'enhanced_transactions', ['settlement_date'])
    op.create_index('idx_enhanced_transaction_tax_year', 'enhanced_transactions', ['tax_year', 'tax_category'])
    
    
    # Create enhanced_market_data table (TimescaleDB hypertable)
    op.create_table(
        'enhanced_market_data',
        # Composite primary key for time-series
        sa.Column('time', postgresql.TIMESTAMP(timezone=True), primary_key=True),
        sa.Column('symbol', sa.String(20), primary_key=True, index=True),
        
        # Basic OHLCV
        sa.Column('open', postgresql.NUMERIC(12, 4)),
        sa.Column('high', postgresql.NUMERIC(12, 4)),
        sa.Column('low', postgresql.NUMERIC(12, 4)),
        sa.Column('close', postgresql.NUMERIC(12, 4), nullable=False),
        sa.Column('volume', sa.BigInteger()),
        
        # Extended market data
        sa.Column('vwap', postgresql.NUMERIC(12, 4)),
        sa.Column('bid', postgresql.NUMERIC(12, 4)),
        sa.Column('ask', postgresql.NUMERIC(12, 4)),
        sa.Column('spread', postgresql.NUMERIC(8, 4)),
        sa.Column('mid_price', postgresql.NUMERIC(12, 4)),
        
        # Market microstructure
        sa.Column('bid_size', sa.BigInteger()),
        sa.Column('ask_size', sa.BigInteger()),
        sa.Column('trade_count', sa.Integer()),
        sa.Column('block_trades', sa.Integer()),
        
        # Technical indicators
        sa.Column('rsi_14', postgresql.NUMERIC(6, 2)),
        sa.Column('macd', postgresql.NUMERIC(8, 4)),
        sa.Column('macd_signal', postgresql.NUMERIC(8, 4)),
        sa.Column('macd_histogram', postgresql.NUMERIC(8, 4)),
        
        # Moving averages
        sa.Column('sma_20', postgresql.NUMERIC(12, 4)),
        sa.Column('sma_50', postgresql.NUMERIC(12, 4)),
        sa.Column('sma_200', postgresql.NUMERIC(12, 4)),
        sa.Column('ema_12', postgresql.NUMERIC(12, 4)),
        sa.Column('ema_26', postgresql.NUMERIC(12, 4)),
        
        # Bollinger Bands
        sa.Column('bb_upper', postgresql.NUMERIC(12, 4)),
        sa.Column('bb_middle', postgresql.NUMERIC(12, 4)),
        sa.Column('bb_lower', postgresql.NUMERIC(12, 4)),
        sa.Column('bb_width', postgresql.NUMERIC(8, 4)),
        sa.Column('bb_percent', postgresql.NUMERIC(6, 4)),
        
        # Volatility
        sa.Column('historical_volatility', postgresql.NUMERIC(8, 4)),
        sa.Column('garman_klass_volatility', postgresql.NUMERIC(8, 4)),
        sa.Column('parkinson_volatility', postgresql.NUMERIC(8, 4)),
        
        # Market regimes
        sa.Column('volatility_regime', sa.String(20)),
        sa.Column('trend_regime', sa.String(20)),
        sa.Column('momentum_regime', sa.String(20)),
        
        # Data quality
        sa.Column('data_source', sa.String(50), nullable=False),
        sa.Column('data_quality_score', postgresql.NUMERIC(3, 2), default=1.0),
        sa.Column('is_adjusted', sa.Boolean(), default=False),
        sa.Column('adjustment_factor', postgresql.NUMERIC(10, 6), default=1.0),
        
        # Market info
        sa.Column('exchange', sa.String(10)),
        sa.Column('market_cap', sa.BigInteger()),
        sa.Column('shares_outstanding', sa.BigInteger()),
        sa.Column('float_shares', sa.BigInteger()),
        
        # Corporate actions
        sa.Column('has_dividend', sa.Boolean(), default=False),
        sa.Column('has_split', sa.Boolean(), default=False),
        sa.Column('has_earnings', sa.Boolean(), default=False),
        
        # Alternative data
        sa.Column('social_sentiment', postgresql.NUMERIC(5, 2)),
        sa.Column('news_sentiment', postgresql.NUMERIC(5, 2)),
        sa.Column('analyst_rating_avg', postgresql.NUMERIC(3, 1)),
        sa.Column('analyst_price_target_avg', postgresql.NUMERIC(12, 4)),
        
        # Metadata
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )
    
    # Enhanced market data indexes for TimescaleDB
    op.create_index('idx_enhanced_market_data_symbol_time', 'enhanced_market_data', ['symbol', 'time'])
    op.create_index('idx_enhanced_market_data_time', 'enhanced_market_data', ['time'])
    op.create_index('idx_enhanced_market_data_source', 'enhanced_market_data', ['data_source', 'time'])
    op.create_index('idx_enhanced_market_data_volume', 'enhanced_market_data', ['volume', 'time'])
    
    
    # Create user activity log for audit trails
    op.create_table(
        'user_activity_log',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('enhanced_users.id')),
        
        # Activity details
        sa.Column('activity_type', sa.String(50), nullable=False),
        sa.Column('activity_category', sa.String(30)),
        sa.Column('description', sa.String(500)),
        
        # Request details
        sa.Column('ip_address', sa.String(45)),
        sa.Column('user_agent', sa.String(500)),
        sa.Column('request_id', postgresql.UUID(as_uuid=True)),
        sa.Column('session_id', sa.String(100)),
        
        # Data changes
        sa.Column('before_data', postgresql.JSONB()),
        sa.Column('after_data', postgresql.JSONB()),
        sa.Column('affected_entities', postgresql.ARRAY(sa.String(100))),
        
        # Status
        sa.Column('status', sa.String(20)),
        sa.Column('error_code', sa.String(50)),
        sa.Column('error_message', sa.String(500)),
        
        # Timing
        sa.Column('timestamp', postgresql.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('duration_ms', sa.Integer()),
        
        # Compliance
        sa.Column('requires_notification', sa.Boolean(), default=False),
        sa.Column('is_suspicious', sa.Boolean(), default=False),
        sa.Column('compliance_reviewed', sa.Boolean(), default=False),
    )
    
    # User activity log indexes
    op.create_index('idx_user_activity_log_user_timestamp', 'user_activity_log', ['user_id', 'timestamp'])
    op.create_index('idx_user_activity_log_type_timestamp', 'user_activity_log', ['activity_type', 'timestamp'])
    op.create_index('idx_user_activity_log_suspicious', 'user_activity_log', ['is_suspicious', 'timestamp'])
    
    
    # Create regulatory reports table
    op.create_table(
        'regulatory_reports',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        
        # Report identification
        sa.Column('report_type', sa.String(50), nullable=False),
        sa.Column('report_subtype', sa.String(50)),
        sa.Column('regulatory_framework', sa.String(30)),
        
        # Affected entities
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('enhanced_users.id')),
        sa.Column('account_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('enhanced_accounts.id')),
        sa.Column('portfolio_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('enhanced_portfolios.id')),
        
        # Report content
        sa.Column('report_data', postgresql.JSONB(), nullable=False),
        sa.Column('generated_document_url', sa.String(500)),
        sa.Column('document_hash', sa.String(64)),
        
        # Periods and timing
        sa.Column('reporting_period_start', sa.DateTime(timezone=True)),
        sa.Column('reporting_period_end', sa.DateTime(timezone=True)),
        sa.Column('due_date', sa.DateTime(timezone=True)),
        sa.Column('generated_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        
        # Status
        sa.Column('status', sa.String(30), default='draft'),
        sa.Column('submission_method', sa.String(30)),
        sa.Column('submitted_at', sa.DateTime(timezone=True)),
        sa.Column('acknowledged_at', sa.DateTime(timezone=True)),
        
        # Compliance
        sa.Column('compliance_approved', sa.Boolean(), default=False),
        sa.Column('approved_by', sa.String(100)),
        sa.Column('approved_at', sa.DateTime(timezone=True)),
    )
    
    # Regulatory reports indexes
    op.create_index('idx_regulatory_report_user_type', 'regulatory_reports', ['user_id', 'report_type'])
    op.create_index('idx_regulatory_report_period', 'regulatory_reports', ['reporting_period_start', 'reporting_period_end'])
    op.create_index('idx_regulatory_report_status', 'regulatory_reports', ['status', 'due_date'])
    
    
    # Create TimescaleDB hypertable for enhanced_market_data (if TimescaleDB is available)
    # This will be done via a separate SQL script since Alembic doesn't handle TimescaleDB directly
    op.execute("""
        -- Create TimescaleDB hypertable for time-series optimization
        -- This requires TimescaleDB extension to be installed
        DO $$
        BEGIN
            -- Check if TimescaleDB is available
            IF EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'timescaledb') THEN
                -- Convert enhanced_market_data to hypertable
                PERFORM create_hypertable('enhanced_market_data', 'time', 
                    chunk_time_interval => INTERVAL '1 day',
                    if_not_exists => TRUE
                );
                
                -- Create compression policy for older data
                PERFORM add_compression_policy('enhanced_market_data', INTERVAL '7 days');
                
                -- Create retention policy to automatically drop old data after 5 years
                PERFORM add_retention_policy('enhanced_market_data', INTERVAL '5 years');
                
                RAISE NOTICE 'TimescaleDB hypertable created for enhanced_market_data';
            ELSE
                RAISE NOTICE 'TimescaleDB extension not found, skipping hypertable creation';
            END IF;
        EXCEPTION WHEN OTHERS THEN
            RAISE NOTICE 'Could not create TimescaleDB hypertable: %', SQLERRM;
        END;
        $$;
    """)


def downgrade():
    """Drop enhanced database schema"""
    
    # Drop tables in reverse dependency order
    op.drop_table('regulatory_reports')
    op.drop_table('user_activity_log')
    
    # Drop TimescaleDB hypertable first (if exists)
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.tables 
                      WHERE table_name = 'enhanced_market_data') THEN
                DROP TABLE IF EXISTS enhanced_market_data CASCADE;
            END IF;
        END;
        $$;
    """)
    
    op.drop_table('enhanced_transactions')
    op.drop_table('enhanced_accounts')
    op.drop_table('enhanced_portfolios')
    op.drop_table('enhanced_users')