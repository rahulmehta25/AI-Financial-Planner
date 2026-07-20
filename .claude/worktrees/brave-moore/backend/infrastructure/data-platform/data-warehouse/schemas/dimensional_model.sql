-- Data Warehouse Dimensional Model for Financial Planning Platform
-- Star schema design with slowly changing dimensions

-- Create schemas
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS dimensions;
CREATE SCHEMA IF NOT EXISTS facts;
CREATE SCHEMA IF NOT EXISTS marts;
CREATE SCHEMA IF NOT EXISTS audit;

-- =====================================================================
-- DIMENSION TABLES
-- =====================================================================

-- Date Dimension
CREATE TABLE dimensions.dim_date (
    date_key INTEGER PRIMARY KEY,
    date_actual DATE NOT NULL,
    day_of_week INTEGER NOT NULL,
    day_name VARCHAR(10) NOT NULL,
    day_of_month INTEGER NOT NULL,
    day_of_year INTEGER NOT NULL,
    week_of_year INTEGER NOT NULL,
    month_number INTEGER NOT NULL,
    month_name VARCHAR(10) NOT NULL,
    quarter_number INTEGER NOT NULL,
    quarter_name VARCHAR(2) NOT NULL,
    year_number INTEGER NOT NULL,
    is_weekend BOOLEAN NOT NULL,
    is_holiday BOOLEAN NOT NULL DEFAULT FALSE,
    holiday_name VARCHAR(50),
    fiscal_year INTEGER,
    fiscal_quarter INTEGER,
    fiscal_month INTEGER,
    is_business_day BOOLEAN NOT NULL,
    days_from_today INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Time Dimension
CREATE TABLE dimensions.dim_time (
    time_key INTEGER PRIMARY KEY,
    hour_24 INTEGER NOT NULL,
    hour_12 INTEGER NOT NULL,
    minute INTEGER NOT NULL,
    second INTEGER NOT NULL,
    am_pm VARCHAR(2) NOT NULL,
    time_display VARCHAR(8) NOT NULL,
    business_hours_flag BOOLEAN NOT NULL,
    peak_hours_flag BOOLEAN NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User Dimension (SCD Type 2)
CREATE TABLE dimensions.dim_user (
    user_key BIGSERIAL PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL,
    email VARCHAR(255),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    date_of_birth DATE,
    age_group VARCHAR(20),
    income_range VARCHAR(50),
    employment_status VARCHAR(50),
    marital_status VARCHAR(20),
    number_of_dependents INTEGER,
    education_level VARCHAR(50),
    risk_tolerance VARCHAR(20),
    investment_experience VARCHAR(20),
    primary_goal VARCHAR(100),
    registration_date DATE,
    country VARCHAR(50),
    state_province VARCHAR(50),
    city VARCHAR(100),
    postal_code VARCHAR(20),
    time_zone VARCHAR(50),
    preferred_language VARCHAR(10),
    subscription_type VARCHAR(50),
    user_status VARCHAR(20),
    -- SCD Type 2 columns
    effective_date DATE NOT NULL,
    expiration_date DATE,
    is_current BOOLEAN NOT NULL DEFAULT TRUE,
    record_version INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Indexes
    UNIQUE(user_id, effective_date)
);

-- Account Dimension (SCD Type 2)
CREATE TABLE dimensions.dim_account (
    account_key BIGSERIAL PRIMARY KEY,
    account_id VARCHAR(50) NOT NULL,
    user_id VARCHAR(50) NOT NULL,
    account_type VARCHAR(50) NOT NULL,
    account_subtype VARCHAR(50),
    account_name VARCHAR(200),
    financial_institution VARCHAR(200),
    institution_id VARCHAR(50),
    account_number_masked VARCHAR(50),
    routing_number_encrypted VARCHAR(500),
    currency_code VARCHAR(3) DEFAULT 'USD',
    account_status VARCHAR(20),
    is_primary BOOLEAN DEFAULT FALSE,
    account_category VARCHAR(50), -- checking, savings, investment, credit, loan
    interest_rate DECIMAL(5,4),
    credit_limit DECIMAL(15,2),
    minimum_balance DECIMAL(15,2),
    -- SCD Type 2 columns
    effective_date DATE NOT NULL,
    expiration_date DATE,
    is_current BOOLEAN NOT NULL DEFAULT TRUE,
    record_version INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(account_id, effective_date)
);

-- Security/Investment Dimension
CREATE TABLE dimensions.dim_security (
    security_key BIGSERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL UNIQUE,
    security_name VARCHAR(200) NOT NULL,
    security_type VARCHAR(50) NOT NULL, -- stock, bond, etf, mutual_fund, crypto, etc.
    sector VARCHAR(100),
    industry VARCHAR(100),
    market_cap_category VARCHAR(20), -- large_cap, mid_cap, small_cap, micro_cap
    exchange VARCHAR(50),
    country VARCHAR(50),
    currency VARCHAR(3) DEFAULT 'USD',
    is_dividend_paying BOOLEAN DEFAULT FALSE,
    dividend_frequency VARCHAR(20),
    expense_ratio DECIMAL(5,4),
    beta DECIMAL(8,4),
    pe_ratio DECIMAL(8,2),
    market_cap BIGINT,
    shares_outstanding BIGINT,
    ipo_date DATE,
    is_active BOOLEAN DEFAULT TRUE,
    data_provider VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Transaction Category Dimension
CREATE TABLE dimensions.dim_transaction_category (
    category_key BIGSERIAL PRIMARY KEY,
    category_id VARCHAR(50) NOT NULL UNIQUE,
    category_name VARCHAR(100) NOT NULL,
    parent_category_id VARCHAR(50),
    category_level INTEGER NOT NULL DEFAULT 1,
    category_path VARCHAR(500),
    is_income BOOLEAN NOT NULL DEFAULT FALSE,
    is_discretionary BOOLEAN NOT NULL DEFAULT TRUE,
    budget_category VARCHAR(50),
    tax_category VARCHAR(50),
    priority_level INTEGER DEFAULT 3, -- 1=high, 2=medium, 3=low
    typical_frequency VARCHAR(20), -- daily, weekly, monthly, yearly, irregular
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Geography Dimension
CREATE TABLE dimensions.dim_geography (
    geography_key BIGSERIAL PRIMARY KEY,
    country_code VARCHAR(3) NOT NULL,
    country_name VARCHAR(100) NOT NULL,
    state_province_code VARCHAR(10),
    state_province_name VARCHAR(100),
    city_name VARCHAR(100),
    postal_code VARCHAR(20),
    latitude DECIMAL(10,8),
    longitude DECIMAL(11,8),
    time_zone VARCHAR(50),
    region VARCHAR(50),
    population INTEGER,
    median_income DECIMAL(12,2),
    cost_of_living_index DECIMAL(5,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Goal Dimension
CREATE TABLE dimensions.dim_goal (
    goal_key BIGSERIAL PRIMARY KEY,
    goal_id VARCHAR(50) NOT NULL UNIQUE,
    user_id VARCHAR(50) NOT NULL,
    goal_type VARCHAR(50) NOT NULL, -- retirement, home_purchase, education, emergency_fund, etc.
    goal_name VARCHAR(200) NOT NULL,
    goal_description TEXT,
    target_amount DECIMAL(15,2) NOT NULL,
    current_amount DECIMAL(15,2) DEFAULT 0,
    target_date DATE,
    priority_rank INTEGER,
    risk_tolerance VARCHAR(20),
    goal_status VARCHAR(20), -- active, paused, completed, cancelled
    created_date DATE NOT NULL,
    completed_date DATE,
    auto_contribute BOOLEAN DEFAULT FALSE,
    contribution_frequency VARCHAR(20),
    monthly_contribution DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Market Data Provider Dimension
CREATE TABLE dimensions.dim_data_provider (
    provider_key BIGSERIAL PRIMARY KEY,
    provider_id VARCHAR(50) NOT NULL UNIQUE,
    provider_name VARCHAR(100) NOT NULL,
    provider_type VARCHAR(50), -- market_data, banking, news, alternative
    data_quality_score DECIMAL(3,2) DEFAULT 1.00,
    latency_ms INTEGER,
    coverage_percentage DECIMAL(5,2),
    cost_per_request DECIMAL(8,4),
    is_real_time BOOLEAN DEFAULT FALSE,
    rate_limit INTEGER,
    api_version VARCHAR(20),
    contact_info JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================================
-- FACT TABLES
-- =====================================================================

-- Daily Account Balance Fact
CREATE TABLE facts.fact_account_balance_daily (
    balance_key BIGSERIAL PRIMARY KEY,
    date_key INTEGER NOT NULL REFERENCES dimensions.dim_date(date_key),
    user_key BIGINT NOT NULL REFERENCES dimensions.dim_user(user_key),
    account_key BIGINT NOT NULL REFERENCES dimensions.dim_account(account_key),
    
    -- Measures
    opening_balance DECIMAL(15,2) NOT NULL,
    closing_balance DECIMAL(15,2) NOT NULL,
    daily_change DECIMAL(15,2) NOT NULL,
    daily_change_percent DECIMAL(8,4),
    inflow_amount DECIMAL(15,2) DEFAULT 0,
    outflow_amount DECIMAL(15,2) DEFAULT 0,
    interest_earned DECIMAL(10,2) DEFAULT 0,
    fees_charged DECIMAL(10,2) DEFAULT 0,
    
    -- Derived measures
    available_balance DECIMAL(15,2),
    pending_balance DECIMAL(15,2),
    overdraft_amount DECIMAL(15,2) DEFAULT 0,
    
    -- Metadata
    data_quality_score DECIMAL(3,2) DEFAULT 1.00,
    provider_key INTEGER REFERENCES dimensions.dim_data_provider(provider_key),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    UNIQUE(date_key, user_key, account_key)
);

-- Transaction Fact
CREATE TABLE facts.fact_transaction (
    transaction_key BIGSERIAL PRIMARY KEY,
    date_key INTEGER NOT NULL REFERENCES dimensions.dim_date(date_key),
    time_key INTEGER NOT NULL REFERENCES dimensions.dim_time(time_key),
    user_key BIGINT NOT NULL REFERENCES dimensions.dim_user(user_key),
    account_key BIGINT NOT NULL REFERENCES dimensions.dim_account(account_key),
    category_key BIGINT REFERENCES dimensions.dim_transaction_category(category_key),
    geography_key BIGINT REFERENCES dimensions.dim_geography(geography_key),
    
    -- Degenerate dimensions
    transaction_id VARCHAR(100) NOT NULL,
    merchant_name VARCHAR(200),
    description TEXT,
    reference_number VARCHAR(100),
    
    -- Measures
    amount DECIMAL(15,2) NOT NULL,
    original_amount DECIMAL(15,2),
    original_currency VARCHAR(3),
    exchange_rate DECIMAL(10,6) DEFAULT 1.0,
    
    -- Derived measures
    running_balance DECIMAL(15,2),
    budget_impact DECIMAL(15,2),
    
    -- Flags and indicators
    is_debit BOOLEAN NOT NULL,
    is_credit BOOLEAN NOT NULL,
    is_transfer BOOLEAN DEFAULT FALSE,
    is_recurring BOOLEAN DEFAULT FALSE,
    is_pending BOOLEAN DEFAULT FALSE,
    is_disputed BOOLEAN DEFAULT FALSE,
    
    -- Risk and quality scores
    fraud_score DECIMAL(3,2) DEFAULT 0.00,
    confidence_score DECIMAL(3,2) DEFAULT 1.00,
    anomaly_score DECIMAL(3,2) DEFAULT 0.00,
    
    -- Timestamps
    posted_date DATE,
    authorized_date DATE,
    settlement_date DATE,
    
    -- Metadata
    data_source VARCHAR(50),
    provider_key INTEGER REFERENCES dimensions.dim_data_provider(provider_key),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Indexes for performance
    INDEX idx_transaction_user_date (user_key, date_key),
    INDEX idx_transaction_account_date (account_key, date_key),
    INDEX idx_transaction_category (category_key),
    INDEX idx_transaction_amount (amount),
    UNIQUE(transaction_id, account_key)
);

-- Market Data Fact (Intraday)
CREATE TABLE facts.fact_market_data_intraday (
    market_data_key BIGSERIAL PRIMARY KEY,
    date_key INTEGER NOT NULL REFERENCES dimensions.dim_date(date_key),
    time_key INTEGER NOT NULL REFERENCES dimensions.dim_time(time_key),
    security_key BIGINT NOT NULL REFERENCES dimensions.dim_security(security_key),
    provider_key INTEGER NOT NULL REFERENCES dimensions.dim_data_provider(provider_key),
    
    -- Price measures
    open_price DECIMAL(12,4),
    high_price DECIMAL(12,4),
    low_price DECIMAL(12,4),
    close_price DECIMAL(12,4) NOT NULL,
    volume BIGINT,
    
    -- Derived measures
    price_change DECIMAL(12,4),
    price_change_percent DECIMAL(8,4),
    volatility DECIMAL(8,4),
    
    -- Technical indicators
    sma_5 DECIMAL(12,4),
    sma_20 DECIMAL(12,4),
    sma_50 DECIMAL(12,4),
    rsi DECIMAL(5,2),
    macd DECIMAL(8,4),
    bollinger_upper DECIMAL(12,4),
    bollinger_lower DECIMAL(12,4),
    
    -- Market metrics
    market_cap BIGINT,
    pe_ratio DECIMAL(8,2),
    dividend_yield DECIMAL(5,4),
    
    -- Quality metrics
    data_quality_score DECIMAL(3,2) DEFAULT 1.00,
    bid_ask_spread DECIMAL(8,4),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Indexes
    INDEX idx_market_data_security_date (security_key, date_key, time_key),
    INDEX idx_market_data_date (date_key),
    UNIQUE(security_key, date_key, time_key, provider_key)
);

-- Portfolio Performance Fact
CREATE TABLE facts.fact_portfolio_performance (
    portfolio_key BIGSERIAL PRIMARY KEY,
    date_key INTEGER NOT NULL REFERENCES dimensions.dim_date(date_key),
    user_key BIGINT NOT NULL REFERENCES dimensions.dim_user(user_key),
    
    -- Portfolio measures
    total_value DECIMAL(15,2) NOT NULL,
    total_cost_basis DECIMAL(15,2) NOT NULL,
    unrealized_gain_loss DECIMAL(15,2),
    realized_gain_loss DECIMAL(15,2),
    dividend_income DECIMAL(12,2) DEFAULT 0,
    
    -- Performance metrics
    daily_return DECIMAL(8,4),
    cumulative_return DECIMAL(8,4),
    annualized_return DECIMAL(8,4),
    sharpe_ratio DECIMAL(8,4),
    max_drawdown DECIMAL(8,4),
    volatility DECIMAL(8,4),
    beta DECIMAL(8,4),
    alpha DECIMAL(8,4),
    
    -- Risk metrics
    value_at_risk DECIMAL(15,2),
    expected_shortfall DECIMAL(15,2),
    
    -- Allocation metrics
    equity_allocation DECIMAL(5,2),
    bond_allocation DECIMAL(5,2),
    cash_allocation DECIMAL(5,2),
    alternative_allocation DECIMAL(5,2),
    international_allocation DECIMAL(5,2),
    
    -- Benchmark comparison
    benchmark_return DECIMAL(8,4),
    excess_return DECIMAL(8,4),
    tracking_error DECIMAL(8,4),
    information_ratio DECIMAL(8,4),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(date_key, user_key)
);

-- Goal Progress Fact
CREATE TABLE facts.fact_goal_progress (
    progress_key BIGSERIAL PRIMARY KEY,
    date_key INTEGER NOT NULL REFERENCES dimensions.dim_date(date_key),
    user_key BIGINT NOT NULL REFERENCES dimensions.dim_user(user_key),
    goal_key BIGINT NOT NULL REFERENCES dimensions.dim_goal(goal_key),
    
    -- Progress measures
    current_amount DECIMAL(15,2) NOT NULL,
    target_amount DECIMAL(15,2) NOT NULL,
    contribution_amount DECIMAL(12,2) DEFAULT 0,
    withdrawal_amount DECIMAL(12,2) DEFAULT 0,
    
    -- Calculated measures
    progress_percentage DECIMAL(5,2),
    amount_needed DECIMAL(15,2),
    days_to_goal INTEGER,
    projected_completion_date DATE,
    monthly_savings_needed DECIMAL(12,2),
    
    -- Confidence metrics
    probability_of_success DECIMAL(5,2),
    risk_adjusted_return DECIMAL(8,4),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(date_key, user_key, goal_key)
);

-- User Activity Fact
CREATE TABLE facts.fact_user_activity (
    activity_key BIGSERIAL PRIMARY KEY,
    date_key INTEGER NOT NULL REFERENCES dimensions.dim_date(date_key),
    time_key INTEGER NOT NULL REFERENCES dimensions.dim_time(time_key),
    user_key BIGINT NOT NULL REFERENCES dimensions.dim_user(user_key),
    
    -- Activity measures
    session_duration_minutes INTEGER,
    page_views INTEGER DEFAULT 0,
    features_used INTEGER DEFAULT 0,
    transactions_viewed INTEGER DEFAULT 0,
    goals_updated INTEGER DEFAULT 0,
    reports_generated INTEGER DEFAULT 0,
    
    -- Engagement measures
    engagement_score DECIMAL(5,2),
    feature_adoption_score DECIMAL(5,2),
    
    -- Device and channel
    device_type VARCHAR(50),
    operating_system VARCHAR(50),
    browser VARCHAR(50),
    channel VARCHAR(50), -- web, mobile_app, api
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================================
-- DATA MARTS (Star Schema Aggregations)
-- =====================================================================

-- Monthly Financial Summary Mart
CREATE TABLE marts.monthly_financial_summary (
    summary_key BIGSERIAL PRIMARY KEY,
    user_key BIGINT NOT NULL,
    year_month VARCHAR(7) NOT NULL, -- YYYY-MM format
    
    -- Balance metrics
    avg_total_balance DECIMAL(15,2),
    min_total_balance DECIMAL(15,2),
    max_total_balance DECIMAL(15,2),
    end_of_month_balance DECIMAL(15,2),
    
    -- Transaction metrics
    total_income DECIMAL(15,2),
    total_expenses DECIMAL(15,2),
    net_cash_flow DECIMAL(15,2),
    transaction_count INTEGER,
    avg_transaction_amount DECIMAL(12,2),
    
    -- Category breakdowns
    essential_expenses DECIMAL(15,2),
    discretionary_expenses DECIMAL(15,2),
    savings_amount DECIMAL(15,2),
    investment_amount DECIMAL(15,2),
    
    -- Goal metrics
    total_goal_contributions DECIMAL(15,2),
    goals_on_track INTEGER,
    total_goals INTEGER,
    
    -- Portfolio metrics
    portfolio_value DECIMAL(15,2),
    portfolio_return DECIMAL(8,4),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(user_key, year_month)
);

-- =====================================================================
-- INDEXES FOR PERFORMANCE
-- =====================================================================

-- Date dimension indexes
CREATE INDEX idx_dim_date_actual ON dimensions.dim_date(date_actual);
CREATE INDEX idx_dim_date_year_month ON dimensions.dim_date(year_number, month_number);

-- User dimension indexes
CREATE INDEX idx_dim_user_id ON dimensions.dim_user(user_id);
CREATE INDEX idx_dim_user_current ON dimensions.dim_user(user_id) WHERE is_current = TRUE;

-- Account dimension indexes
CREATE INDEX idx_dim_account_id ON dimensions.dim_account(account_id);
CREATE INDEX idx_dim_account_user ON dimensions.dim_account(user_id);
CREATE INDEX idx_dim_account_current ON dimensions.dim_account(account_id) WHERE is_current = TRUE;

-- Security dimension indexes
CREATE INDEX idx_dim_security_symbol ON dimensions.dim_security(symbol);
CREATE INDEX idx_dim_security_type ON dimensions.dim_security(security_type);
CREATE INDEX idx_dim_security_sector ON dimensions.dim_security(sector);

-- Fact table indexes for performance
CREATE INDEX idx_fact_balance_user_date ON facts.fact_account_balance_daily(user_key, date_key);
CREATE INDEX idx_fact_transaction_user_date ON facts.fact_transaction(user_key, date_key);
CREATE INDEX idx_fact_market_security_date ON facts.fact_market_data_intraday(security_key, date_key);
CREATE INDEX idx_fact_portfolio_user_date ON facts.fact_portfolio_performance(user_key, date_key);

-- =====================================================================
-- MATERIALIZED VIEWS FOR FAST QUERIES
-- =====================================================================

-- User summary view
CREATE MATERIALIZED VIEW marts.user_summary_mv AS
SELECT 
    u.user_key,
    u.user_id,
    u.first_name,
    u.last_name,
    u.age_group,
    u.risk_tolerance,
    COUNT(DISTINCT a.account_key) AS account_count,
    COUNT(DISTINCT g.goal_key) AS goal_count,
    SUM(CASE WHEN ab.closing_balance IS NOT NULL THEN ab.closing_balance ELSE 0 END) AS total_balance,
    AVG(pp.total_return) AS avg_portfolio_return,
    MAX(ab.date_key) AS last_balance_date
FROM dimensions.dim_user u
LEFT JOIN dimensions.dim_account a ON u.user_id = a.user_id AND a.is_current = TRUE
LEFT JOIN dimensions.dim_goal g ON u.user_id = g.user_id
LEFT JOIN facts.fact_account_balance_daily ab ON u.user_key = ab.user_key 
    AND ab.date_key = (SELECT MAX(date_key) FROM facts.fact_account_balance_daily WHERE user_key = u.user_key)
LEFT JOIN facts.fact_portfolio_performance pp ON u.user_key = pp.user_key
    AND pp.date_key = (SELECT MAX(date_key) FROM facts.fact_portfolio_performance WHERE user_key = u.user_key)
WHERE u.is_current = TRUE
GROUP BY u.user_key, u.user_id, u.first_name, u.last_name, u.age_group, u.risk_tolerance;

-- Create refresh schedule for materialized views
CREATE INDEX ON marts.user_summary_mv(user_key);
CREATE INDEX ON marts.user_summary_mv(total_balance);

-- =====================================================================
-- AUDIT AND METADATA TABLES
-- =====================================================================

-- Data lineage tracking
CREATE TABLE audit.data_lineage (
    lineage_key BIGSERIAL PRIMARY KEY,
    source_table VARCHAR(100) NOT NULL,
    target_table VARCHAR(100) NOT NULL,
    transformation_type VARCHAR(50) NOT NULL,
    execution_date DATE NOT NULL,
    records_processed BIGINT,
    execution_time_seconds INTEGER,
    data_quality_score DECIMAL(3,2),
    created_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Data quality monitoring
CREATE TABLE audit.data_quality_metrics (
    metric_key BIGSERIAL PRIMARY KEY,
    table_name VARCHAR(100) NOT NULL,
    column_name VARCHAR(100),
    metric_type VARCHAR(50) NOT NULL, -- completeness, accuracy, consistency, timeliness
    metric_value DECIMAL(5,2) NOT NULL,
    threshold_value DECIMAL(5,2),
    status VARCHAR(20) NOT NULL, -- pass, warning, fail
    execution_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ETL job monitoring
CREATE TABLE audit.etl_job_log (
    job_log_key BIGSERIAL PRIMARY KEY,
    job_name VARCHAR(100) NOT NULL,
    job_type VARCHAR(50) NOT NULL, -- extract, transform, load, validation
    status VARCHAR(20) NOT NULL, -- running, completed, failed
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    records_processed BIGINT,
    records_failed BIGINT,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================================
-- SLOWLY CHANGING DIMENSION PROCEDURES
-- =====================================================================

-- Function to handle SCD Type 2 for users
CREATE OR REPLACE FUNCTION update_user_scd2(
    p_user_id VARCHAR(50),
    p_email VARCHAR(255),
    p_first_name VARCHAR(100),
    p_last_name VARCHAR(100),
    p_date_of_birth DATE,
    p_income_range VARCHAR(50),
    p_risk_tolerance VARCHAR(20)
) RETURNS VOID AS $$
BEGIN
    -- Check if record has changed
    IF EXISTS (
        SELECT 1 FROM dimensions.dim_user 
        WHERE user_id = p_user_id 
        AND is_current = TRUE
        AND (email != p_email OR first_name != p_first_name OR last_name != p_last_name 
             OR date_of_birth != p_date_of_birth OR income_range != p_income_range 
             OR risk_tolerance != p_risk_tolerance)
    ) THEN
        -- Expire current record
        UPDATE dimensions.dim_user 
        SET is_current = FALSE, 
            expiration_date = CURRENT_DATE,
            updated_at = CURRENT_TIMESTAMP
        WHERE user_id = p_user_id AND is_current = TRUE;
        
        -- Insert new record
        INSERT INTO dimensions.dim_user (
            user_id, email, first_name, last_name, date_of_birth, 
            income_range, risk_tolerance, effective_date, 
            is_current, record_version
        ) 
        SELECT 
            p_user_id, p_email, p_first_name, p_last_name, p_date_of_birth,
            p_income_range, p_risk_tolerance, CURRENT_DATE,
            TRUE, COALESCE(MAX(record_version), 0) + 1
        FROM dimensions.dim_user 
        WHERE user_id = p_user_id;
    END IF;
END;
$$ LANGUAGE plpgsql;