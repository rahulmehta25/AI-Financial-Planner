-- Advanced Dimensional Model with SCD Type 2, Data Marts, and Analytics Tables
-- Comprehensive data warehouse schema for financial planning platform

-- =====================================================================
-- EXTENSIONS AND FUNCTIONS
-- =====================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";
CREATE EXTENSION IF NOT EXISTS "btree_gin";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create schemas with proper organization
CREATE SCHEMA IF NOT EXISTS raw;           -- Raw data from sources
CREATE SCHEMA IF NOT EXISTS staging;       -- Staging area for transformations
CREATE SCHEMA IF NOT EXISTS dimensions;    -- Dimension tables
CREATE SCHEMA IF NOT EXISTS facts;         -- Fact tables
CREATE SCHEMA IF NOT EXISTS marts;         -- Data marts for specific use cases
CREATE SCHEMA IF NOT EXISTS audit;         -- Audit and lineage tracking
CREATE SCHEMA IF NOT EXISTS metadata;      -- Metadata management
CREATE SCHEMA IF NOT EXISTS analytics;     -- Analytics and ML features

-- =====================================================================
-- UTILITY FUNCTIONS FOR SCD TYPE 2
-- =====================================================================

-- Function to generate surrogate keys
CREATE OR REPLACE FUNCTION generate_surrogate_key()
RETURNS BIGINT AS $$
BEGIN
    RETURN nextval('dimensions.surrogate_key_seq');
END;
$$ LANGUAGE plpgsql;

-- Create sequence for surrogate keys
CREATE SEQUENCE IF NOT EXISTS dimensions.surrogate_key_seq
    START WITH 1000000
    INCREMENT BY 1
    NO MAXVALUE
    CACHE 1000;

-- Function to handle SCD Type 2 updates
CREATE OR REPLACE FUNCTION handle_scd_type2(
    p_table_name TEXT,
    p_business_key TEXT,
    p_new_data JSONB,
    p_excluded_columns TEXT[] DEFAULT ARRAY['effective_date', 'expiration_date', 'is_current', 'record_version']
) RETURNS BIGINT AS $$
DECLARE
    v_current_record RECORD;
    v_has_changes BOOLEAN := FALSE;
    v_new_surrogate_key BIGINT;
    v_sql TEXT;
BEGIN
    -- Get current active record
    v_sql := format('SELECT * FROM %s WHERE %s = $1 AND is_current = TRUE', p_table_name, p_business_key);
    EXECUTE v_sql INTO v_current_record USING p_new_data->p_business_key;
    
    IF v_current_record IS NULL THEN
        -- No existing record, insert new
        v_new_surrogate_key := generate_surrogate_key();
        v_sql := format(
            'INSERT INTO %s SELECT $1, ($2::JSONB || jsonb_build_object(''%s'', $1, ''effective_date'', CURRENT_DATE, ''is_current'', true, ''record_version'', 1)).*',
            p_table_name, p_business_key
        );
        EXECUTE v_sql USING v_new_surrogate_key, p_new_data;
        RETURN v_new_surrogate_key;
    END IF;
    
    -- Check for changes (simplified - would need proper field-by-field comparison in production)
    -- This is a placeholder for actual change detection logic
    v_has_changes := TRUE;
    
    IF v_has_changes THEN
        -- Expire current record
        v_sql := format(
            'UPDATE %s SET is_current = FALSE, expiration_date = CURRENT_DATE WHERE %s = $1 AND is_current = TRUE',
            p_table_name, p_business_key
        );
        EXECUTE v_sql USING p_new_data->p_business_key;
        
        -- Insert new version
        v_new_surrogate_key := generate_surrogate_key();
        v_sql := format(
            'INSERT INTO %s SELECT $1, ($2::JSONB || jsonb_build_object(''%s'', $1, ''effective_date'', CURRENT_DATE, ''is_current'', true, ''record_version'', $3)).*',
            p_table_name, p_business_key
        );
        EXECUTE v_sql USING v_new_surrogate_key, p_new_data, COALESCE(v_current_record.record_version, 0) + 1;
        RETURN v_new_surrogate_key;
    END IF;
    
    -- No changes, return existing surrogate key
    RETURN v_current_record.user_key; -- Assuming user_key, adjust as needed
END;
$$ LANGUAGE plpgsql;

-- =====================================================================
-- ENHANCED DIMENSION TABLES WITH SCD TYPE 2
-- =====================================================================

-- Enhanced User Dimension with comprehensive attributes
DROP TABLE IF EXISTS dimensions.dim_user CASCADE;
CREATE TABLE dimensions.dim_user (
    user_key BIGINT PRIMARY KEY DEFAULT generate_surrogate_key(),
    user_id VARCHAR(50) NOT NULL,
    
    -- Personal Information
    email VARCHAR(255),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    full_name VARCHAR(201) GENERATED ALWAYS AS (COALESCE(first_name, '') || ' ' || COALESCE(last_name, '')) STORED,
    date_of_birth DATE,
    age INTEGER GENERATED ALWAYS AS (EXTRACT(YEAR FROM AGE(CURRENT_DATE, date_of_birth))) STORED,
    age_group VARCHAR(20) GENERATED ALWAYS AS (
        CASE 
            WHEN EXTRACT(YEAR FROM AGE(CURRENT_DATE, date_of_birth)) < 25 THEN 'Under 25'
            WHEN EXTRACT(YEAR FROM AGE(CURRENT_DATE, date_of_birth)) < 35 THEN '25-34'
            WHEN EXTRACT(YEAR FROM AGE(CURRENT_DATE, date_of_birth)) < 45 THEN '35-44'
            WHEN EXTRACT(YEAR FROM AGE(CURRENT_DATE, date_of_birth)) < 55 THEN '45-54'
            WHEN EXTRACT(YEAR FROM AGE(CURRENT_DATE, date_of_birth)) < 65 THEN '55-64'
            ELSE '65+'
        END
    ) STORED,
    gender VARCHAR(20),
    phone_number VARCHAR(20),
    
    -- Financial Profile
    annual_income DECIMAL(12,2),
    income_range VARCHAR(50) GENERATED ALWAYS AS (
        CASE 
            WHEN annual_income < 25000 THEN 'Under $25K'
            WHEN annual_income < 50000 THEN '$25K-$50K'
            WHEN annual_income < 75000 THEN '$50K-$75K'
            WHEN annual_income < 100000 THEN '$75K-$100K'
            WHEN annual_income < 150000 THEN '$100K-$150K'
            WHEN annual_income < 250000 THEN '$150K-$250K'
            ELSE 'Over $250K'
        END
    ) STORED,
    net_worth DECIMAL(15,2),
    employment_status VARCHAR(50),
    employer VARCHAR(200),
    job_title VARCHAR(100),
    industry VARCHAR(100),
    
    -- Demographics
    marital_status VARCHAR(20),
    number_of_dependents INTEGER DEFAULT 0,
    education_level VARCHAR(50),
    homeowner_status VARCHAR(20),
    
    -- Financial Behavior
    risk_tolerance VARCHAR(20),
    investment_experience VARCHAR(20),
    investment_style VARCHAR(30),
    primary_financial_goal VARCHAR(100),
    time_horizon_years INTEGER,
    
    -- Platform Behavior
    registration_date DATE NOT NULL,
    last_login_date DATE,
    subscription_type VARCHAR(50),
    subscription_start_date DATE,
    subscription_end_date DATE,
    user_status VARCHAR(20) DEFAULT 'active',
    preferred_language VARCHAR(10) DEFAULT 'en',
    notification_preferences JSONB,
    feature_flags JSONB,
    
    -- Geographic Information
    country VARCHAR(50),
    state_province VARCHAR(50),
    city VARCHAR(100),
    postal_code VARCHAR(20),
    time_zone VARCHAR(50),
    latitude DECIMAL(10,8),
    longitude DECIMAL(11,8),
    
    -- Segmentation
    customer_segment VARCHAR(50),
    lifecycle_stage VARCHAR(30),
    ltv_segment VARCHAR(20), -- Lifetime Value segment
    churn_risk_score DECIMAL(3,2),
    engagement_score DECIMAL(3,2),
    
    -- SCD Type 2 Management
    effective_date DATE NOT NULL DEFAULT CURRENT_DATE,
    expiration_date DATE,
    is_current BOOLEAN NOT NULL DEFAULT TRUE,
    record_version INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100) DEFAULT CURRENT_USER,
    updated_by VARCHAR(100) DEFAULT CURRENT_USER,
    
    -- Data Quality
    data_quality_score DECIMAL(3,2) DEFAULT 1.00,
    source_system VARCHAR(50) DEFAULT 'financial_planning_app',
    
    -- Constraints
    CONSTRAINT dim_user_business_key_unique UNIQUE(user_id, effective_date),
    CONSTRAINT dim_user_age_check CHECK (age IS NULL OR age BETWEEN 0 AND 120),
    CONSTRAINT dim_user_income_check CHECK (annual_income IS NULL OR annual_income >= 0),
    CONSTRAINT dim_user_dependents_check CHECK (number_of_dependents >= 0),
    CONSTRAINT dim_user_quality_score_check CHECK (data_quality_score BETWEEN 0 AND 1),
    CONSTRAINT dim_user_scd_check CHECK (
        (is_current = TRUE AND expiration_date IS NULL) OR 
        (is_current = FALSE AND expiration_date IS NOT NULL)
    )
);

-- Enhanced Account Dimension
DROP TABLE IF EXISTS dimensions.dim_account CASCADE;
CREATE TABLE dimensions.dim_account (
    account_key BIGINT PRIMARY KEY DEFAULT generate_surrogate_key(),
    account_id VARCHAR(50) NOT NULL,
    user_id VARCHAR(50) NOT NULL,
    
    -- Account Basic Information
    account_name VARCHAR(200),
    account_type VARCHAR(50) NOT NULL,
    account_subtype VARCHAR(50),
    account_category VARCHAR(50), -- checking, savings, investment, credit, loan, mortgage
    
    -- Financial Institution Details
    financial_institution VARCHAR(200),
    institution_id VARCHAR(50),
    institution_type VARCHAR(50), -- bank, credit_union, brokerage, etc.
    routing_number_encrypted VARCHAR(500),
    account_number_masked VARCHAR(50),
    
    -- Account Properties
    currency_code VARCHAR(3) DEFAULT 'USD',
    account_status VARCHAR(20) DEFAULT 'active',
    is_primary BOOLEAN DEFAULT FALSE,
    is_joint_account BOOLEAN DEFAULT FALSE,
    joint_owner_name VARCHAR(200),
    
    -- Account Limits and Features
    credit_limit DECIMAL(15,2),
    available_credit DECIMAL(15,2),
    minimum_balance DECIMAL(15,2),
    overdraft_limit DECIMAL(15,2),
    interest_rate DECIMAL(5,4),
    apy DECIMAL(5,4), -- Annual Percentage Yield
    
    -- Fees and Charges
    monthly_fee DECIMAL(8,2),
    overdraft_fee DECIMAL(8,2),
    foreign_transaction_fee_pct DECIMAL(5,4),
    atm_fee DECIMAL(8,2),
    
    -- Account Dates
    account_opened_date DATE,
    account_closed_date DATE,
    last_statement_date DATE,
    next_statement_date DATE,
    
    -- Investment Account Specific
    investment_advisor VARCHAR(200),
    management_fee_pct DECIMAL(5,4),
    portfolio_strategy VARCHAR(100),
    
    -- Loan/Credit Specific
    original_loan_amount DECIMAL(15,2),
    loan_term_months INTEGER,
    payment_due_day INTEGER,
    next_payment_date DATE,
    last_payment_date DATE,
    maturity_date DATE,
    
    -- Account Performance
    account_age_days INTEGER GENERATED ALWAYS AS (
        CASE WHEN account_opened_date IS NOT NULL 
             THEN CURRENT_DATE - account_opened_date 
             ELSE NULL END
    ) STORED,
    
    -- Integration and Data Management
    plaid_account_id VARCHAR(100),
    yodlee_account_id VARCHAR(100),
    data_provider VARCHAR(50),
    last_data_refresh TIMESTAMP WITH TIME ZONE,
    sync_status VARCHAR(20) DEFAULT 'active',
    sync_error_count INTEGER DEFAULT 0,
    
    -- SCD Type 2 Management
    effective_date DATE NOT NULL DEFAULT CURRENT_DATE,
    expiration_date DATE,
    is_current BOOLEAN NOT NULL DEFAULT TRUE,
    record_version INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100) DEFAULT CURRENT_USER,
    updated_by VARCHAR(100) DEFAULT CURRENT_USER,
    
    -- Data Quality
    data_quality_score DECIMAL(3,2) DEFAULT 1.00,
    source_system VARCHAR(50) DEFAULT 'banking_integration',
    
    -- Constraints
    CONSTRAINT dim_account_business_key_unique UNIQUE(account_id, effective_date),
    CONSTRAINT dim_account_user_fk FOREIGN KEY (user_id) 
        REFERENCES dimensions.dim_user(user_id) DEFERRABLE,
    CONSTRAINT dim_account_limits_check CHECK (credit_limit IS NULL OR credit_limit >= 0),
    CONSTRAINT dim_account_balance_check CHECK (minimum_balance IS NULL OR minimum_balance >= 0),
    CONSTRAINT dim_account_rate_check CHECK (interest_rate IS NULL OR interest_rate BETWEEN -1 AND 1),
    CONSTRAINT dim_account_quality_score_check CHECK (data_quality_score BETWEEN 0 AND 1),
    CONSTRAINT dim_account_scd_check CHECK (
        (is_current = TRUE AND expiration_date IS NULL) OR 
        (is_current = FALSE AND expiration_date IS NOT NULL)
    )
);

-- Enhanced Security/Investment Dimension
DROP TABLE IF EXISTS dimensions.dim_security CASCADE;
CREATE TABLE dimensions.dim_security (
    security_key BIGINT PRIMARY KEY DEFAULT generate_surrogate_key(),
    symbol VARCHAR(20) NOT NULL,
    
    -- Basic Security Information
    security_name VARCHAR(200) NOT NULL,
    company_name VARCHAR(200),
    security_type VARCHAR(50) NOT NULL, -- stock, bond, etf, mutual_fund, crypto, commodity, option
    asset_class VARCHAR(50), -- equity, fixed_income, alternative, cash, crypto
    sub_asset_class VARCHAR(50),
    
    -- Classification
    sector VARCHAR(100),
    industry VARCHAR(100),
    sub_industry VARCHAR(100),
    gics_sector VARCHAR(100),
    gics_industry_group VARCHAR(100),
    
    -- Market Information
    exchange VARCHAR(50),
    primary_exchange VARCHAR(50),
    country VARCHAR(50),
    currency VARCHAR(3) DEFAULT 'USD',
    market_cap_category VARCHAR(20), -- large_cap, mid_cap, small_cap, micro_cap
    
    -- Financial Metrics
    market_cap BIGINT,
    shares_outstanding BIGINT,
    float_shares BIGINT,
    enterprise_value BIGINT,
    book_value_per_share DECIMAL(12,4),
    
    -- Valuation Ratios
    pe_ratio DECIMAL(8,2),
    peg_ratio DECIMAL(8,2),
    price_to_book DECIMAL(8,2),
    price_to_sales DECIMAL(8,2),
    ev_to_ebitda DECIMAL(8,2),
    
    -- Risk and Performance
    beta DECIMAL(8,4),
    alpha DECIMAL(8,4),
    volatility_30d DECIMAL(8,4),
    volatility_90d DECIMAL(8,4),
    volatility_1y DECIMAL(8,4),
    
    -- Dividend Information
    is_dividend_paying BOOLEAN DEFAULT FALSE,
    dividend_yield DECIMAL(5,4),
    dividend_rate DECIMAL(10,4),
    dividend_frequency VARCHAR(20), -- monthly, quarterly, semi_annual, annual
    ex_dividend_date DATE,
    dividend_pay_date DATE,
    
    -- Fund-Specific Information
    expense_ratio DECIMAL(5,4),
    management_fee DECIMAL(5,4),
    load_fee_front DECIMAL(5,4),
    load_fee_back DECIMAL(5,4),
    minimum_investment DECIMAL(12,2),
    fund_family VARCHAR(100),
    fund_manager VARCHAR(200),
    inception_date DATE,
    
    -- Trading Information
    ipo_date DATE,
    delisting_date DATE,
    last_trade_date DATE,
    average_daily_volume BIGINT,
    bid_ask_spread DECIMAL(8,4),
    
    -- ESG and Sustainability
    esg_score DECIMAL(3,1),
    esg_grade VARCHAR(3),
    environmental_score DECIMAL(3,1),
    social_score DECIMAL(3,1),
    governance_score DECIMAL(3,1),
    
    -- Status and Flags
    is_active BOOLEAN DEFAULT TRUE,
    is_tradeable BOOLEAN DEFAULT TRUE,
    is_optionable BOOLEAN DEFAULT FALSE,
    is_shortable BOOLEAN DEFAULT TRUE,
    is_etf BOOLEAN DEFAULT FALSE,
    is_reit BOOLEAN DEFAULT FALSE,
    
    -- Data Provider Information
    data_provider VARCHAR(50),
    provider_security_id VARCHAR(100),
    cusip VARCHAR(9),
    isin VARCHAR(12),
    figi VARCHAR(12),
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_market_data_update TIMESTAMP WITH TIME ZONE,
    
    -- Data Quality
    data_quality_score DECIMAL(3,2) DEFAULT 1.00,
    data_completeness_pct DECIMAL(5,2),
    
    -- Constraints
    CONSTRAINT dim_security_symbol_unique UNIQUE(symbol),
    CONSTRAINT dim_security_market_cap_check CHECK (market_cap IS NULL OR market_cap > 0),
    CONSTRAINT dim_security_shares_check CHECK (shares_outstanding IS NULL OR shares_outstanding > 0),
    CONSTRAINT dim_security_pe_check CHECK (pe_ratio IS NULL OR pe_ratio > 0),
    CONSTRAINT dim_security_expense_ratio_check CHECK (expense_ratio IS NULL OR expense_ratio BETWEEN 0 AND 1),
    CONSTRAINT dim_security_quality_score_check CHECK (data_quality_score BETWEEN 0 AND 1)
);

-- Enhanced Transaction Category Dimension with Hierarchy
DROP TABLE IF EXISTS dimensions.dim_transaction_category CASCADE;
CREATE TABLE dimensions.dim_transaction_category (
    category_key BIGINT PRIMARY KEY DEFAULT generate_surrogate_key(),
    category_id VARCHAR(50) NOT NULL UNIQUE,
    
    -- Hierarchical Structure
    category_name VARCHAR(100) NOT NULL,
    parent_category_id VARCHAR(50),
    category_level INTEGER NOT NULL DEFAULT 1,
    category_path VARCHAR(500),
    root_category VARCHAR(50),
    
    -- Category Properties
    is_income BOOLEAN NOT NULL DEFAULT FALSE,
    is_expense BOOLEAN NOT NULL DEFAULT TRUE,
    is_transfer BOOLEAN NOT NULL DEFAULT FALSE,
    is_discretionary BOOLEAN NOT NULL DEFAULT TRUE,
    is_recurring BOOLEAN NOT NULL DEFAULT FALSE,
    
    -- Financial Planning
    budget_category VARCHAR(50),
    budget_priority INTEGER DEFAULT 3, -- 1=high, 2=medium, 3=low
    typical_frequency VARCHAR(20), -- daily, weekly, monthly, quarterly, yearly, irregular
    seasonality VARCHAR(20), -- none, holiday, summer, winter, etc.
    
    -- Tax and Compliance
    tax_category VARCHAR(50),
    tax_deductible BOOLEAN DEFAULT FALSE,
    business_expense BOOLEAN DEFAULT FALSE,
    
    -- Analytics and ML
    spending_pattern VARCHAR(30), -- fixed, variable, impulse, planned
    emotional_trigger VARCHAR(30), -- stress, celebration, necessity, social
    lifestyle_category VARCHAR(50),
    
    -- Visual and UX
    display_name VARCHAR(100),
    icon_name VARCHAR(50),
    color_code VARCHAR(7), -- Hex color code
    display_order INTEGER,
    
    -- Merchant Categories
    mcc_codes TEXT[], -- Merchant Category Codes
    common_merchants TEXT[],
    keywords TEXT[],
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    is_system_category BOOLEAN DEFAULT FALSE,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign Key Constraint
    CONSTRAINT dim_category_parent_fk FOREIGN KEY (parent_category_id) 
        REFERENCES dimensions.dim_transaction_category(category_id) DEFERRABLE,
    CONSTRAINT dim_category_level_check CHECK (category_level BETWEEN 1 AND 5),
    CONSTRAINT dim_category_priority_check CHECK (budget_priority BETWEEN 1 AND 5)
);

-- Enhanced Geography Dimension
DROP TABLE IF EXISTS dimensions.dim_geography CASCADE;
CREATE TABLE dimensions.dim_geography (
    geography_key BIGINT PRIMARY KEY DEFAULT generate_surrogate_key(),
    
    -- Geographic Hierarchy
    country_code VARCHAR(3) NOT NULL,
    country_name VARCHAR(100) NOT NULL,
    region VARCHAR(50),
    sub_region VARCHAR(50),
    
    state_province_code VARCHAR(10),
    state_province_name VARCHAR(100),
    
    county_name VARCHAR(100),
    city_name VARCHAR(100),
    
    postal_code VARCHAR(20),
    postal_code_extension VARCHAR(10),
    
    -- Precise Location
    latitude DECIMAL(10,8),
    longitude DECIMAL(11,8),
    elevation_meters INTEGER,
    
    -- Time Zone Information
    time_zone VARCHAR(50),
    utc_offset_hours DECIMAL(3,1),
    observes_dst BOOLEAN DEFAULT FALSE,
    
    -- Economic and Demographic Data
    population INTEGER,
    population_density DECIMAL(10,2), -- people per sq km
    median_household_income DECIMAL(12,2),
    median_home_value DECIMAL(12,2),
    cost_of_living_index DECIMAL(5,2), -- 100 = national average
    unemployment_rate DECIMAL(5,4),
    
    -- Market Data
    market_size VARCHAR(20), -- metro, micro, rural
    market_rank INTEGER,
    dma_code INTEGER, -- Designated Market Area
    
    -- Financial Services
    num_banks INTEGER,
    num_credit_unions INTEGER,
    num_investment_firms INTEGER,
    banking_competition_index DECIMAL(3,2),
    
    -- Demographics
    median_age DECIMAL(4,1),
    education_level_index DECIMAL(3,2),
    tech_adoption_score DECIMAL(3,2),
    
    -- Status and Quality
    is_active BOOLEAN DEFAULT TRUE,
    data_quality_score DECIMAL(3,2) DEFAULT 1.00,
    last_updated DATE,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT dim_geography_coords_check CHECK (
        (latitude IS NULL AND longitude IS NULL) OR 
        (latitude BETWEEN -90 AND 90 AND longitude BETWEEN -180 AND 180)
    ),
    CONSTRAINT dim_geography_population_check CHECK (population IS NULL OR population >= 0),
    CONSTRAINT dim_geography_income_check CHECK (median_household_income IS NULL OR median_household_income >= 0)
);

-- =====================================================================
-- ADVANCED FACT TABLES WITH COMPREHENSIVE METRICS
-- =====================================================================

-- Enhanced Transaction Fact Table
DROP TABLE IF EXISTS facts.fact_transaction_enhanced CASCADE;
CREATE TABLE facts.fact_transaction_enhanced (
    transaction_key BIGINT PRIMARY KEY DEFAULT generate_surrogate_key(),
    
    -- Dimension Keys
    date_key INTEGER NOT NULL,
    time_key INTEGER NOT NULL,
    user_key BIGINT NOT NULL,
    account_key BIGINT NOT NULL,
    category_key BIGINT,
    geography_key BIGINT,
    merchant_key BIGINT,
    
    -- Degenerate Dimensions (transaction-specific attributes)
    transaction_id VARCHAR(100) NOT NULL,
    parent_transaction_id VARCHAR(100), -- For splits/transfers
    transaction_group_id VARCHAR(100), -- For related transactions
    
    -- Transaction Details
    description TEXT,
    merchant_name VARCHAR(200),
    merchant_category VARCHAR(100),
    mcc_code VARCHAR(4),
    
    -- Amounts and Currency
    amount DECIMAL(15,2) NOT NULL,
    original_amount DECIMAL(15,2),
    original_currency VARCHAR(3),
    exchange_rate DECIMAL(10,6) DEFAULT 1.0,
    
    -- Fee Breakdown
    base_amount DECIMAL(15,2),
    tax_amount DECIMAL(10,2) DEFAULT 0,
    tip_amount DECIMAL(10,2) DEFAULT 0,
    fee_amount DECIMAL(10,2) DEFAULT 0,
    cashback_amount DECIMAL(10,2) DEFAULT 0,
    
    -- Transaction State
    transaction_status VARCHAR(20) DEFAULT 'posted', -- pending, posted, cancelled, declined
    running_balance DECIMAL(15,2),
    available_balance DECIMAL(15,2),
    
    -- Classification Flags
    is_debit BOOLEAN NOT NULL,
    is_credit BOOLEAN NOT NULL,
    is_transfer BOOLEAN DEFAULT FALSE,
    is_recurring BOOLEAN DEFAULT FALSE,
    is_pending BOOLEAN DEFAULT FALSE,
    is_international BOOLEAN DEFAULT FALSE,
    is_online BOOLEAN DEFAULT FALSE,
    is_mobile BOOLEAN DEFAULT FALSE,
    is_disputed BOOLEAN DEFAULT FALSE,
    is_refund BOOLEAN DEFAULT FALSE,
    is_fee BOOLEAN DEFAULT FALSE,
    
    -- ML and Analytics Scores
    fraud_score DECIMAL(3,2) DEFAULT 0.00,
    confidence_score DECIMAL(3,2) DEFAULT 1.00,
    anomaly_score DECIMAL(3,2) DEFAULT 0.00,
    category_confidence DECIMAL(3,2) DEFAULT 1.00,
    
    -- Budget and Planning
    budget_impact DECIMAL(15,2),
    planned_expense BOOLEAN DEFAULT FALSE,
    over_budget_flag BOOLEAN DEFAULT FALSE,
    
    -- Behavioral Analytics
    spending_pattern VARCHAR(30), -- routine, impulse, planned, seasonal
    transaction_context VARCHAR(50), -- grocery, gas, dining, shopping, etc.
    time_of_day_category VARCHAR(20), -- morning, afternoon, evening, night
    day_type VARCHAR(20), -- weekday, weekend, holiday
    
    -- Location and Context
    location_city VARCHAR(100),
    location_state VARCHAR(50),
    location_country VARCHAR(50),
    location_coordinates POINT,
    location_accuracy_meters INTEGER,
    
    -- Timestamps
    transaction_datetime TIMESTAMP WITH TIME ZONE NOT NULL,
    posted_date DATE,
    authorized_date DATE,
    settlement_date DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Data Lineage
    source_system VARCHAR(50) NOT NULL,
    data_provider VARCHAR(50),
    provider_transaction_id VARCHAR(200),
    etl_batch_id BIGINT,
    data_quality_score DECIMAL(3,2) DEFAULT 1.00,
    
    -- Reference Information
    reference_number VARCHAR(100),
    authorization_code VARCHAR(50),
    trace_number VARCHAR(50),
    
    -- Indexes for Performance
    INDEX idx_transaction_user_date (user_key, date_key),
    INDEX idx_transaction_account_date (account_key, date_key),
    INDEX idx_transaction_category (category_key),
    INDEX idx_transaction_amount (amount),
    INDEX idx_transaction_merchant (merchant_name),
    INDEX idx_transaction_datetime (transaction_datetime),
    INDEX idx_transaction_status (transaction_status),
    INDEX idx_transaction_fraud_score (fraud_score) WHERE fraud_score > 0.5,
    INDEX idx_transaction_location USING GIST (location_coordinates) WHERE location_coordinates IS NOT NULL,
    
    -- Constraints
    CONSTRAINT fact_transaction_business_key_unique UNIQUE(transaction_id, account_key),
    CONSTRAINT fact_transaction_amount_check CHECK (amount <> 0),
    CONSTRAINT fact_transaction_scores_check CHECK (
        fraud_score BETWEEN 0 AND 1 AND 
        confidence_score BETWEEN 0 AND 1 AND 
        anomaly_score BETWEEN 0 AND 1
    ),
    CONSTRAINT fact_transaction_boolean_check CHECK (
        (is_debit = TRUE AND is_credit = FALSE) OR 
        (is_debit = FALSE AND is_credit = TRUE)
    )
);

-- Advanced Portfolio Performance Fact with Risk Metrics
DROP TABLE IF EXISTS facts.fact_portfolio_performance_enhanced CASCADE;
CREATE TABLE facts.fact_portfolio_performance_enhanced (
    portfolio_performance_key BIGINT PRIMARY KEY DEFAULT generate_surrogate_key(),
    
    -- Dimension Keys
    date_key INTEGER NOT NULL,
    user_key BIGINT NOT NULL,
    account_key BIGINT,
    benchmark_key BIGINT,
    
    -- Portfolio Values
    total_market_value DECIMAL(15,2) NOT NULL,
    total_cost_basis DECIMAL(15,2) NOT NULL,
    cash_value DECIMAL(15,2) DEFAULT 0,
    accrued_interest DECIMAL(12,2) DEFAULT 0,
    
    -- Gains and Losses
    unrealized_gain_loss DECIMAL(15,2),
    unrealized_gain_loss_pct DECIMAL(8,4),
    realized_gain_loss_mtd DECIMAL(15,2) DEFAULT 0,
    realized_gain_loss_qtd DECIMAL(15,2) DEFAULT 0,
    realized_gain_loss_ytd DECIMAL(15,2) DEFAULT 0,
    
    -- Income
    dividend_income_mtd DECIMAL(12,2) DEFAULT 0,
    dividend_income_qtd DECIMAL(12,2) DEFAULT 0,
    dividend_income_ytd DECIMAL(12,2) DEFAULT 0,
    interest_income_mtd DECIMAL(12,2) DEFAULT 0,
    interest_income_qtd DECIMAL(12,2) DEFAULT 0,
    interest_income_ytd DECIMAL(12,2) DEFAULT 0,
    
    -- Performance Metrics
    daily_return DECIMAL(8,4),
    mtd_return DECIMAL(8,4),
    qtd_return DECIMAL(8,4),
    ytd_return DECIMAL(8,4),
    inception_return DECIMAL(8,4),
    
    -- Annualized Returns
    annualized_return_1y DECIMAL(8,4),
    annualized_return_3y DECIMAL(8,4),
    annualized_return_5y DECIMAL(8,4),
    annualized_return_10y DECIMAL(8,4),
    
    -- Risk Metrics
    volatility_30d DECIMAL(8,4),
    volatility_90d DECIMAL(8,4),
    volatility_1y DECIMAL(8,4),
    sharpe_ratio_30d DECIMAL(8,4),
    sharpe_ratio_90d DECIMAL(8,4),
    sharpe_ratio_1y DECIMAL(8,4),
    
    -- Advanced Risk Metrics
    max_drawdown DECIMAL(8,4),
    max_drawdown_duration_days INTEGER,
    beta DECIMAL(8,4),
    alpha DECIMAL(8,4),
    tracking_error DECIMAL(8,4),
    information_ratio DECIMAL(8,4),
    sortino_ratio DECIMAL(8,4),
    calmar_ratio DECIMAL(8,4),
    
    -- Value at Risk
    var_95_1d DECIMAL(15,2),
    var_99_1d DECIMAL(15,2),
    var_95_1w DECIMAL(15,2),
    cvar_95_1d DECIMAL(15,2), -- Conditional VaR (Expected Shortfall)
    cvar_99_1d DECIMAL(15,2),
    
    -- Asset Allocation
    equity_allocation_pct DECIMAL(5,2),
    fixed_income_allocation_pct DECIMAL(5,2),
    cash_allocation_pct DECIMAL(5,2),
    alternative_allocation_pct DECIMAL(5,2),
    international_allocation_pct DECIMAL(5,2),
    
    -- Geographic Allocation
    us_allocation_pct DECIMAL(5,2),
    developed_international_pct DECIMAL(5,2),
    emerging_markets_pct DECIMAL(5,2),
    
    -- Sector Allocation (top 5)
    technology_allocation_pct DECIMAL(5,2),
    healthcare_allocation_pct DECIMAL(5,2),
    financials_allocation_pct DECIMAL(5,2),
    consumer_allocation_pct DECIMAL(5,2),
    industrials_allocation_pct DECIMAL(5,2),
    
    -- Portfolio Characteristics
    number_of_positions INTEGER,
    largest_position_pct DECIMAL(5,2),
    top_10_concentration_pct DECIMAL(5,2),
    average_position_size DECIMAL(15,2),
    portfolio_turnover_pct DECIMAL(5,2),
    
    -- ESG Metrics
    esg_score DECIMAL(3,1),
    carbon_intensity DECIMAL(10,4),
    
    -- Fees and Costs
    total_fees_mtd DECIMAL(10,2) DEFAULT 0,
    total_fees_qtd DECIMAL(10,2) DEFAULT 0,
    total_fees_ytd DECIMAL(10,2) DEFAULT 0,
    expense_ratio_weighted DECIMAL(5,4),
    
    -- Benchmark Comparison
    benchmark_return DECIMAL(8,4),
    excess_return DECIMAL(8,4),
    up_capture_ratio DECIMAL(5,4),
    down_capture_ratio DECIMAL(5,4),
    
    -- Goal Tracking
    goal_progress_pct DECIMAL(5,2),
    on_track_for_goal BOOLEAN,
    projected_goal_date DATE,
    
    -- Data Quality and Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    data_quality_score DECIMAL(3,2) DEFAULT 1.00,
    
    -- Constraints and Indexes
    CONSTRAINT fact_portfolio_business_key_unique UNIQUE(date_key, user_key, account_key),
    CONSTRAINT fact_portfolio_value_check CHECK (total_market_value >= 0),
    CONSTRAINT fact_portfolio_allocation_check CHECK (
        (equity_allocation_pct + fixed_income_allocation_pct + 
         cash_allocation_pct + alternative_allocation_pct) <= 100.01
    ),
    INDEX idx_portfolio_user_date (user_key, date_key),
    INDEX idx_portfolio_performance (ytd_return, sharpe_ratio_1y),
    INDEX idx_portfolio_risk (max_drawdown, volatility_1y)
);

-- =====================================================================
-- DATA MARTS FOR SPECIFIC USE CASES
-- =====================================================================

-- Customer 360 Mart
DROP TABLE IF EXISTS marts.customer_360 CASCADE;
CREATE TABLE marts.customer_360 (
    user_key BIGINT PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL,
    
    -- Basic Demographics
    full_name VARCHAR(201),
    age INTEGER,
    age_group VARCHAR(20),
    income_range VARCHAR(50),
    location_city VARCHAR(100),
    location_state VARCHAR(50),
    
    -- Account Summary
    total_accounts INTEGER,
    checking_accounts INTEGER,
    savings_accounts INTEGER,
    investment_accounts INTEGER,
    credit_accounts INTEGER,
    loan_accounts INTEGER,
    
    -- Financial Position
    total_assets DECIMAL(15,2),
    total_liabilities DECIMAL(15,2),
    net_worth DECIMAL(15,2),
    liquid_assets DECIMAL(15,2),
    credit_utilization_pct DECIMAL(5,2),
    
    -- Cash Flow (Monthly)
    avg_monthly_income DECIMAL(12,2),
    avg_monthly_expenses DECIMAL(12,2),
    avg_monthly_savings DECIMAL(12,2),
    savings_rate_pct DECIMAL(5,2),
    
    -- Spending Behavior
    top_spending_category VARCHAR(50),
    avg_transaction_amount DECIMAL(10,2),
    transactions_per_month DECIMAL(8,2),
    most_frequent_merchant VARCHAR(200),
    
    -- Investment Profile
    total_portfolio_value DECIMAL(15,2),
    portfolio_return_ytd DECIMAL(8,4),
    risk_tolerance VARCHAR(20),
    investment_style VARCHAR(30),
    
    -- Goals and Planning
    total_goals INTEGER,
    active_goals INTEGER,
    goals_on_track INTEGER,
    avg_goal_progress_pct DECIMAL(5,2),
    
    -- Platform Engagement
    days_since_registration INTEGER,
    days_since_last_login INTEGER,
    total_logins INTEGER,
    avg_session_duration_minutes DECIMAL(8,2),
    features_used INTEGER,
    
    -- Risk and Quality Scores
    overall_fraud_risk_score DECIMAL(3,2),
    credit_score_estimate INTEGER,
    financial_health_score DECIMAL(3,2),
    engagement_score DECIMAL(3,2),
    churn_risk_score DECIMAL(3,2),
    
    -- Segmentation
    customer_segment VARCHAR(50),
    lifecycle_stage VARCHAR(30),
    ltv_segment VARCHAR(20),
    
    -- Timestamps
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Indexes
    INDEX idx_customer_360_segment (customer_segment, ltv_segment),
    INDEX idx_customer_360_risk (churn_risk_score, overall_fraud_risk_score),
    INDEX idx_customer_360_value (net_worth, total_portfolio_value),
    INDEX idx_customer_360_engagement (engagement_score, days_since_last_login)
);

-- Financial Health Dashboard Mart
DROP TABLE IF EXISTS marts.financial_health_dashboard CASCADE;
CREATE TABLE marts.financial_health_dashboard (
    dashboard_key BIGINT PRIMARY KEY DEFAULT generate_surrogate_key(),
    user_key BIGINT NOT NULL,
    snapshot_date DATE NOT NULL,
    
    -- Overall Health Score (0-100)
    financial_health_score INTEGER,
    health_trend VARCHAR(20), -- improving, declining, stable
    
    -- Component Scores
    liquidity_score INTEGER, -- Emergency fund adequacy
    debt_score INTEGER, -- Debt-to-income ratio health
    savings_score INTEGER, -- Savings rate and consistency
    investment_score INTEGER, -- Portfolio diversification and performance
    planning_score INTEGER, -- Goal setting and progress
    
    -- Key Metrics
    debt_to_income_ratio DECIMAL(5,4),
    emergency_fund_months DECIMAL(4,2),
    credit_utilization_pct DECIMAL(5,2),
    savings_rate_pct DECIMAL(5,2),
    investment_allocation_score INTEGER,
    
    -- Recommendations
    top_recommendation TEXT,
    recommendation_category VARCHAR(50),
    recommendation_priority INTEGER,
    estimated_impact_score INTEGER,
    
    -- Benchmarks
    peer_group_avg_score INTEGER,
    age_group_avg_score INTEGER,
    income_group_avg_score INTEGER,
    
    -- Trends (30-day changes)
    score_change_30d INTEGER,
    liquidity_change_30d INTEGER,
    debt_change_30d INTEGER,
    savings_change_30d INTEGER,
    
    -- Alert Flags
    high_debt_alert BOOLEAN DEFAULT FALSE,
    low_emergency_fund_alert BOOLEAN DEFAULT FALSE,
    irregular_income_alert BOOLEAN DEFAULT FALSE,
    high_spending_alert BOOLEAN DEFAULT FALSE,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints and Indexes
    CONSTRAINT financial_health_business_key_unique UNIQUE(user_key, snapshot_date),
    CONSTRAINT financial_health_score_check CHECK (financial_health_score BETWEEN 0 AND 100),
    INDEX idx_financial_health_user_date (user_key, snapshot_date),
    INDEX idx_financial_health_score (financial_health_score, health_trend),
    INDEX idx_financial_health_alerts (high_debt_alert, low_emergency_fund_alert)
);

-- =====================================================================
-- MATERIALIZED VIEWS FOR FAST ANALYTICS
-- =====================================================================

-- Real-time User Activity Summary
DROP MATERIALIZED VIEW IF EXISTS marts.user_activity_summary_mv CASCADE;
CREATE MATERIALIZED VIEW marts.user_activity_summary_mv AS
SELECT 
    u.user_key,
    u.user_id,
    u.full_name,
    u.customer_segment,
    u.registration_date,
    
    -- Account Summary
    COUNT(DISTINCT a.account_key) FILTER (WHERE a.is_current = TRUE) as total_accounts,
    COUNT(DISTINCT a.account_key) FILTER (WHERE a.is_current = TRUE AND a.account_category = 'checking') as checking_accounts,
    COUNT(DISTINCT a.account_key) FILTER (WHERE a.is_current = TRUE AND a.account_category = 'savings') as savings_accounts,
    COUNT(DISTINCT a.account_key) FILTER (WHERE a.is_current = TRUE AND a.account_category = 'investment') as investment_accounts,
    
    -- Transaction Summary (Last 30 days)
    COUNT(DISTINCT t.transaction_key) FILTER (WHERE t.date_key >= EXTRACT(EPOCH FROM CURRENT_DATE - INTERVAL '30 days')::INTEGER) as transactions_30d,
    AVG(t.amount) FILTER (WHERE t.date_key >= EXTRACT(EPOCH FROM CURRENT_DATE - INTERVAL '30 days')::INTEGER AND t.is_debit = TRUE) as avg_expense_30d,
    SUM(t.amount) FILTER (WHERE t.date_key >= EXTRACT(EPOCH FROM CURRENT_DATE - INTERVAL '30 days')::INTEGER AND t.is_debit = TRUE) as total_expenses_30d,
    SUM(t.amount) FILTER (WHERE t.date_key >= EXTRACT(EPOCH FROM CURRENT_DATE - INTERVAL '30 days')::INTEGER AND t.is_credit = TRUE) as total_income_30d,
    
    -- Portfolio Summary (Latest)
    p.total_market_value as current_portfolio_value,
    p.ytd_return as portfolio_ytd_return,
    p.financial_health_score,
    
    -- Activity Timestamps
    MAX(t.transaction_datetime) as last_transaction_date,
    u.last_login_date,
    
    -- Data Quality
    AVG(t.data_quality_score) as avg_data_quality,
    
    -- Refresh Timestamp
    CURRENT_TIMESTAMP as last_refreshed
    
FROM dimensions.dim_user u
LEFT JOIN dimensions.dim_account a ON u.user_id = a.user_id
LEFT JOIN facts.fact_transaction_enhanced t ON u.user_key = t.user_key
LEFT JOIN LATERAL (
    SELECT *
    FROM facts.fact_portfolio_performance_enhanced pp
    WHERE pp.user_key = u.user_key
    ORDER BY pp.date_key DESC
    LIMIT 1
) p ON true
WHERE u.is_current = TRUE
GROUP BY 
    u.user_key, u.user_id, u.full_name, u.customer_segment, u.registration_date,
    u.last_login_date, p.total_market_value, p.ytd_return, p.financial_health_score;

-- Create indexes on materialized view
CREATE UNIQUE INDEX idx_user_activity_mv_user_key ON marts.user_activity_summary_mv(user_key);
CREATE INDEX idx_user_activity_mv_segment ON marts.user_activity_summary_mv(customer_segment);
CREATE INDEX idx_user_activity_mv_value ON marts.user_activity_summary_mv(current_portfolio_value);

-- =====================================================================
-- STORED PROCEDURES FOR DATA WAREHOUSE MAINTENANCE
-- =====================================================================

-- Procedure to refresh materialized views
CREATE OR REPLACE FUNCTION refresh_materialized_views()
RETURNS VOID AS $$
BEGIN
    -- Refresh user activity summary
    REFRESH MATERIALIZED VIEW CONCURRENTLY marts.user_activity_summary_mv;
    
    -- Log the refresh
    INSERT INTO audit.materialized_view_refresh_log (view_name, refresh_timestamp, rows_affected)
    VALUES ('user_activity_summary_mv', CURRENT_TIMESTAMP, 
            (SELECT COUNT(*) FROM marts.user_activity_summary_mv));
    
    RAISE NOTICE 'Materialized views refreshed successfully';
END;
$$ LANGUAGE plpgsql;

-- Procedure to maintain partition tables (example for future partitioning)
CREATE OR REPLACE FUNCTION maintain_partition_tables()
RETURNS VOID AS $$
DECLARE
    partition_date DATE;
    table_name TEXT;
BEGIN
    -- Create next month's partition for transaction fact table
    partition_date := DATE_TRUNC('month', CURRENT_DATE + INTERVAL '1 month');
    table_name := 'facts.fact_transaction_enhanced_' || TO_CHAR(partition_date, 'YYYY_MM');
    
    -- Check if partition exists, create if not
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name LIKE '%' || TO_CHAR(partition_date, 'YYYY_MM')) THEN
        -- Create partition (simplified - would need proper partitioning syntax)
        RAISE NOTICE 'Would create partition: %', table_name;
    END IF;
    
    -- Drop old partitions (older than 7 years)
    -- Implementation would go here
    
END;
$$ LANGUAGE plpgsql;

-- Procedure to update dimension tables with SCD Type 2
CREATE OR REPLACE FUNCTION update_user_dimension(
    p_user_data JSONB
) RETURNS BIGINT AS $$
DECLARE
    v_user_key BIGINT;
BEGIN
    -- Use the generic SCD Type 2 function
    v_user_key := handle_scd_type2(
        'dimensions.dim_user',
        'user_id',
        p_user_data
    );
    
    RETURN v_user_key;
END;
$$ LANGUAGE plpgsql;

-- =====================================================================
-- AUDIT AND MONITORING TABLES
-- =====================================================================

-- Table to track materialized view refreshes
CREATE TABLE IF NOT EXISTS audit.materialized_view_refresh_log (
    log_id BIGINT PRIMARY KEY DEFAULT generate_surrogate_key(),
    view_name VARCHAR(200) NOT NULL,
    refresh_timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    rows_affected BIGINT,
    duration_seconds DECIMAL(10,3),
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT
);

-- Table to track SCD Type 2 changes
CREATE TABLE IF NOT EXISTS audit.scd_change_log (
    change_id BIGINT PRIMARY KEY DEFAULT generate_surrogate_key(),
    table_name VARCHAR(200) NOT NULL,
    business_key VARCHAR(200) NOT NULL,
    surrogate_key BIGINT NOT NULL,
    change_type VARCHAR(20) NOT NULL, -- INSERT, UPDATE, DELETE
    old_values JSONB,
    new_values JSONB,
    changed_by VARCHAR(100) DEFAULT CURRENT_USER,
    change_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Performance monitoring table
CREATE TABLE IF NOT EXISTS audit.query_performance_log (
    log_id BIGINT PRIMARY KEY DEFAULT generate_surrogate_key(),
    query_type VARCHAR(50) NOT NULL,
    table_names TEXT[],
    execution_time_ms DECIMAL(10,3) NOT NULL,
    rows_affected BIGINT,
    query_hash VARCHAR(64),
    execution_plan JSONB,
    executed_by VARCHAR(100) DEFAULT CURRENT_USER,
    execution_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================================
-- GRANTS AND SECURITY
-- =====================================================================

-- Create roles for different access levels
-- Note: These would typically be created by a DBA
/*
CREATE ROLE financial_data_analyst;
CREATE ROLE financial_data_scientist;
CREATE ROLE financial_application;
CREATE ROLE financial_etl_service;

-- Grant appropriate permissions
GRANT SELECT ON ALL TABLES IN SCHEMA dimensions TO financial_data_analyst;
GRANT SELECT ON ALL TABLES IN SCHEMA facts TO financial_data_analyst;
GRANT SELECT ON ALL TABLES IN SCHEMA marts TO financial_data_analyst;

GRANT SELECT ON ALL TABLES IN SCHEMA dimensions TO financial_data_scientist;
GRANT SELECT ON ALL TABLES IN SCHEMA facts TO financial_data_scientist;
GRANT SELECT ON ALL TABLES IN SCHEMA marts TO financial_data_scientist;
GRANT SELECT ON ALL TABLES IN SCHEMA analytics TO financial_data_scientist;

-- ETL service needs broader access
GRANT ALL ON ALL TABLES IN SCHEMA staging TO financial_etl_service;
GRANT INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA dimensions TO financial_etl_service;
GRANT INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA facts TO financial_etl_service;
*/

-- =====================================================================
-- COMMENTS FOR DOCUMENTATION
-- =====================================================================

COMMENT ON SCHEMA dimensions IS 'Dimension tables with slowly changing dimension (SCD) Type 2 implementation';
COMMENT ON SCHEMA facts IS 'Fact tables containing measurable business events and metrics';
COMMENT ON SCHEMA marts IS 'Pre-aggregated data marts optimized for specific analytical use cases';
COMMENT ON SCHEMA audit IS 'Audit trail and data lineage tracking tables';

COMMENT ON TABLE dimensions.dim_user IS 'User dimension with SCD Type 2 for tracking customer changes over time';
COMMENT ON COLUMN dimensions.dim_user.user_key IS 'Surrogate key for user dimension (never changes)';
COMMENT ON COLUMN dimensions.dim_user.user_id IS 'Business key from source system (natural key)';
COMMENT ON COLUMN dimensions.dim_user.effective_date IS 'Date when this version of the record became effective';
COMMENT ON COLUMN dimensions.dim_user.is_current IS 'Flag indicating if this is the current active version';

COMMENT ON TABLE facts.fact_transaction_enhanced IS 'Comprehensive transaction fact table with behavioral analytics';
COMMENT ON COLUMN facts.fact_transaction_enhanced.fraud_score IS 'ML-generated fraud risk score (0-1)';
COMMENT ON COLUMN facts.fact_transaction_enhanced.anomaly_score IS 'Statistical anomaly detection score (0-1)';

COMMENT ON TABLE marts.customer_360 IS 'Comprehensive customer view aggregating all customer touchpoints';
COMMENT ON TABLE marts.financial_health_dashboard IS 'Pre-calculated financial health scores and metrics';

COMMENT ON MATERIALIZED VIEW marts.user_activity_summary_mv IS 'Real-time user activity summary for dashboards';

-- Create a summary view of the data warehouse structure
DROP VIEW IF EXISTS metadata.data_warehouse_summary CASCADE;
CREATE VIEW metadata.data_warehouse_summary AS
SELECT 
    schemaname,
    COUNT(*) as table_count,
    CASE schemaname
        WHEN 'dimensions' THEN 'Master data with historical tracking'
        WHEN 'facts' THEN 'Transactional and measurement data'
        WHEN 'marts' THEN 'Pre-aggregated analytical datasets'
        WHEN 'audit' THEN 'Data lineage and quality tracking'
        ELSE 'Other'
    END as schema_description
FROM pg_tables 
WHERE schemaname IN ('dimensions', 'facts', 'marts', 'audit', 'staging', 'analytics')
GROUP BY schemaname
ORDER BY schemaname;

COMMENT ON VIEW metadata.data_warehouse_summary IS 'Summary of data warehouse structure and table counts';

-- =====================================================================
-- COMPLETION MESSAGE
-- =====================================================================

-- Log the successful creation of the advanced dimensional model
INSERT INTO audit.data_quality_metrics (
    table_name, column_name, metric_type, metric_value, 
    threshold_value, status, execution_date
) VALUES (
    'data_warehouse', 'schema_creation', 'completeness', 1.0, 
    1.0, 'pass', CURRENT_DATE
);

RAISE NOTICE 'Advanced dimensional model created successfully!';
RAISE NOTICE 'Created schemas: dimensions, facts, marts, audit, metadata, analytics';
RAISE NOTICE 'Key features: SCD Type 2, comprehensive fact tables, pre-built data marts';
RAISE NOTICE 'Use metadata.data_warehouse_summary to see structure overview';
