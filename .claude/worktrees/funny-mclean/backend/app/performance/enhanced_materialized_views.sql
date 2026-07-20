-- Enhanced Materialized Views with Advanced Optimizations
-- Includes partitioning, compression, and parallel processing hints

-- ============================================================================
-- Enable Required Extensions
-- ============================================================================
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
CREATE EXTENSION IF NOT EXISTS pg_cron;
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

-- ============================================================================
-- Configuration for Performance
-- ============================================================================
ALTER SYSTEM SET max_parallel_workers_per_gather = 4;
ALTER SYSTEM SET max_parallel_workers = 8;
ALTER SYSTEM SET max_parallel_maintenance_workers = 4;
ALTER SYSTEM SET effective_cache_size = '8GB';
ALTER SYSTEM SET maintenance_work_mem = '1GB';
ALTER SYSTEM SET work_mem = '256MB';
ALTER SYSTEM SET random_page_cost = 1.1; -- For SSD storage
ALTER SYSTEM SET effective_io_concurrency = 200; -- For SSD storage
ALTER SYSTEM SET jit = on;

-- Reload configuration
SELECT pg_reload_conf();

-- ============================================================================
-- Hypertable for Time-Series Market Data (TimescaleDB)
-- ============================================================================
CREATE TABLE IF NOT EXISTS market_data_timeseries (
    time TIMESTAMPTZ NOT NULL,
    symbol TEXT NOT NULL,
    price DECIMAL(18, 4),
    volume BIGINT,
    bid DECIMAL(18, 4),
    ask DECIMAL(18, 4),
    high DECIMAL(18, 4),
    low DECIMAL(18, 4),
    vwap DECIMAL(18, 4), -- Volume Weighted Average Price
    trades_count INT,
    metadata JSONB
) PARTITION BY RANGE (time);

-- Convert to hypertable with compression
SELECT create_hypertable('market_data_timeseries', 'time', 
    chunk_time_interval => interval '1 day',
    if_not_exists => TRUE);

-- Enable compression
ALTER TABLE market_data_timeseries SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'symbol',
    timescaledb.compress_orderby = 'time DESC'
);

-- Add compression policy (compress chunks older than 7 days)
SELECT add_compression_policy('market_data_timeseries', INTERVAL '7 days');

-- Create continuous aggregate for real-time OHLCV
CREATE MATERIALIZED VIEW market_data_1min
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 minute', time) AS bucket,
    symbol,
    FIRST(price, time) AS open,
    MAX(price) AS high,
    MIN(price) AS low,
    LAST(price, time) AS close,
    SUM(volume) AS volume,
    AVG(vwap) AS vwap,
    COUNT(*) AS trade_count
FROM market_data_timeseries
GROUP BY bucket, symbol
WITH NO DATA;

-- Add refresh policy
SELECT add_continuous_aggregate_policy('market_data_1min',
    start_offset => INTERVAL '1 hour',
    end_offset => INTERVAL '1 minute',
    schedule_interval => INTERVAL '1 minute');

-- ============================================================================
-- Partitioned Portfolio History Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS portfolio_history (
    id BIGSERIAL,
    user_id UUID NOT NULL,
    portfolio_id UUID NOT NULL,
    snapshot_date DATE NOT NULL,
    total_value DECIMAL(18, 2),
    total_invested DECIMAL(18, 2),
    total_return DECIMAL(18, 2),
    return_percentage DECIMAL(8, 4),
    asset_allocation JSONB,
    risk_metrics JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (id, snapshot_date)
) PARTITION BY RANGE (snapshot_date);

-- Create monthly partitions
CREATE TABLE portfolio_history_2024_01 PARTITION OF portfolio_history
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
    
CREATE TABLE portfolio_history_2024_02 PARTITION OF portfolio_history
    FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');

-- Auto-partition creation function
CREATE OR REPLACE FUNCTION create_monthly_partition()
RETURNS void AS $$
DECLARE
    start_date date;
    end_date date;
    partition_name text;
BEGIN
    start_date := date_trunc('month', CURRENT_DATE);
    end_date := start_date + interval '1 month';
    partition_name := 'portfolio_history_' || to_char(start_date, 'YYYY_MM');
    
    EXECUTE format('CREATE TABLE IF NOT EXISTS %I PARTITION OF portfolio_history 
                   FOR VALUES FROM (%L) TO (%L)',
                   partition_name, start_date, end_date);
END;
$$ LANGUAGE plpgsql;

-- Schedule monthly partition creation
-- SELECT cron.schedule('create-monthly-partition', '0 0 1 * *', 
--     $$SELECT create_monthly_partition();$$);

-- ============================================================================
-- Advanced Portfolio Performance Materialized View with Window Functions
-- ============================================================================
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_portfolio_performance_advanced AS
WITH RECURSIVE date_series AS (
    SELECT generate_series(
        CURRENT_DATE - INTERVAL '365 days',
        CURRENT_DATE,
        '1 day'::interval
    )::date AS date
),
portfolio_daily AS (
    SELECT 
        ph.user_id,
        ph.portfolio_id,
        ds.date,
        COALESCE(ph.total_value, LAG(ph.total_value) OVER (
            PARTITION BY ph.portfolio_id 
            ORDER BY ds.date
        )) AS total_value,
        ph.total_invested,
        ph.return_percentage
    FROM date_series ds
    LEFT JOIN portfolio_history ph ON ds.date = ph.snapshot_date
),
rolling_metrics AS (
    SELECT 
        user_id,
        portfolio_id,
        date,
        total_value,
        -- Rolling returns
        (total_value - LAG(total_value, 1) OVER w) / NULLIF(LAG(total_value, 1) OVER w, 0) * 100 AS daily_return,
        (total_value - LAG(total_value, 7) OVER w) / NULLIF(LAG(total_value, 7) OVER w, 0) * 100 AS weekly_return,
        (total_value - LAG(total_value, 30) OVER w) / NULLIF(LAG(total_value, 30) OVER w, 0) * 100 AS monthly_return,
        (total_value - LAG(total_value, 365) OVER w) / NULLIF(LAG(total_value, 365) OVER w, 0) * 100 AS yearly_return,
        -- Moving averages
        AVG(total_value) OVER (PARTITION BY portfolio_id ORDER BY date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) AS ma_30,
        AVG(total_value) OVER (PARTITION BY portfolio_id ORDER BY date ROWS BETWEEN 89 PRECEDING AND CURRENT ROW) AS ma_90,
        -- Volatility
        STDDEV(total_value) OVER (PARTITION BY portfolio_id ORDER BY date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) AS volatility_30d,
        -- Maximum drawdown
        (total_value - MAX(total_value) OVER (PARTITION BY portfolio_id ORDER BY date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)) 
            / NULLIF(MAX(total_value) OVER (PARTITION BY portfolio_id ORDER BY date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 0) * 100 AS current_drawdown
    FROM portfolio_daily
    WINDOW w AS (PARTITION BY portfolio_id ORDER BY date)
),
sharpe_calculations AS (
    SELECT 
        portfolio_id,
        AVG(daily_return) * 252 AS annualized_return, -- 252 trading days
        STDDEV(daily_return) * SQRT(252) AS annualized_volatility,
        CASE 
            WHEN STDDEV(daily_return) > 0 
            THEN (AVG(daily_return) * 252 - 2.0) / (STDDEV(daily_return) * SQRT(252)) -- Risk-free rate = 2%
            ELSE 0 
        END AS sharpe_ratio
    FROM rolling_metrics
    WHERE date >= CURRENT_DATE - INTERVAL '1 year'
    GROUP BY portfolio_id
)
SELECT 
    rm.user_id,
    rm.portfolio_id,
    rm.date,
    rm.total_value,
    rm.daily_return,
    rm.weekly_return,
    rm.monthly_return,
    rm.yearly_return,
    rm.ma_30,
    rm.ma_90,
    rm.volatility_30d,
    rm.current_drawdown,
    sc.sharpe_ratio,
    sc.annualized_return,
    sc.annualized_volatility,
    NOW() AS materialized_at
FROM rolling_metrics rm
LEFT JOIN sharpe_calculations sc ON rm.portfolio_id = sc.portfolio_id
WHERE rm.date = CURRENT_DATE;

-- Indexes for performance
CREATE UNIQUE INDEX idx_mv_portfolio_perf_adv_portfolio_date 
ON mv_portfolio_performance_advanced(portfolio_id, date);

CREATE INDEX idx_mv_portfolio_perf_adv_user 
ON mv_portfolio_performance_advanced(user_id);

CREATE INDEX idx_mv_portfolio_perf_adv_sharpe 
ON mv_portfolio_performance_advanced(sharpe_ratio DESC NULLS LAST);

-- ============================================================================
-- Real-time Goal Tracking with Predictive Analytics
-- ============================================================================
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_goal_analytics AS
WITH goal_history AS (
    SELECT 
        g.id AS goal_id,
        g.profile_id,
        g.target_amount,
        g.target_date,
        g.created_at AS goal_created,
        gt.transaction_date,
        gt.amount,
        SUM(gt.amount) OVER (PARTITION BY g.id ORDER BY gt.transaction_date) AS cumulative_amount
    FROM goals g
    LEFT JOIN goal_transactions gt ON g.id = gt.goal_id
    WHERE g.is_active = true
),
contribution_patterns AS (
    SELECT 
        goal_id,
        AVG(amount) AS avg_contribution,
        STDDEV(amount) AS contribution_stddev,
        COUNT(*) AS num_contributions,
        MAX(transaction_date) AS last_contribution,
        EXTRACT(EPOCH FROM AVG(transaction_date - LAG(transaction_date) OVER (PARTITION BY goal_id ORDER BY transaction_date))) / 86400 AS avg_days_between_contributions
    FROM goal_history
    WHERE amount IS NOT NULL
    GROUP BY goal_id
),
predictions AS (
    SELECT 
        gh.goal_id,
        gh.profile_id,
        gh.target_amount,
        gh.target_date,
        MAX(gh.cumulative_amount) AS current_amount,
        cp.avg_contribution,
        cp.avg_days_between_contributions,
        CASE 
            WHEN cp.avg_days_between_contributions > 0 AND cp.avg_contribution > 0
            THEN gh.target_date - INTERVAL '1 day' * CEIL((gh.target_amount - MAX(gh.cumulative_amount)) / cp.avg_contribution * cp.avg_days_between_contributions)
            ELSE NULL
        END AS predicted_completion_date,
        CASE 
            WHEN EXTRACT(DAYS FROM (gh.target_date - CURRENT_DATE)) > 0
            THEN (gh.target_amount - MAX(gh.cumulative_amount)) / NULLIF(EXTRACT(DAYS FROM (gh.target_date - CURRENT_DATE)), 0)
            ELSE 0
        END AS required_daily_amount,
        MAX(gh.cumulative_amount) / NULLIF(gh.target_amount, 0) * 100 AS completion_percentage
    FROM goal_history gh
    LEFT JOIN contribution_patterns cp ON gh.goal_id = cp.goal_id
    GROUP BY gh.goal_id, gh.profile_id, gh.target_amount, gh.target_date, cp.avg_contribution, cp.avg_days_between_contributions
)
SELECT 
    p.*,
    CASE 
        WHEN p.completion_percentage >= 100 THEN 'COMPLETED'
        WHEN p.predicted_completion_date <= p.target_date THEN 'ON_TRACK'
        WHEN p.target_date < CURRENT_DATE THEN 'OVERDUE'
        ELSE 'AT_RISK'
    END AS goal_status,
    NOW() AS materialized_at
FROM predictions p;

CREATE UNIQUE INDEX idx_mv_goal_analytics_goal 
ON mv_goal_analytics(goal_id);

CREATE INDEX idx_mv_goal_analytics_status 
ON mv_goal_analytics(goal_status);

-- ============================================================================
-- Aggregated ML Model Performance with Statistical Significance
-- ============================================================================
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_ml_model_performance AS
WITH model_predictions AS (
    SELECT 
        mr.model_type,
        mr.model_version,
        mr.recommendation_type,
        mr.confidence_score,
        mr.created_at AS prediction_time,
        mrf.rating,
        mrf.action_taken,
        mrf.created_at AS feedback_time,
        EXTRACT(EPOCH FROM (mrf.created_at - mr.created_at)) / 3600 AS hours_to_feedback
    FROM ml_recommendations mr
    LEFT JOIN ml_recommendation_feedback mrf ON mr.id = mrf.recommendation_id
    WHERE mr.created_at >= CURRENT_DATE - INTERVAL '90 days'
),
performance_metrics AS (
    SELECT 
        model_type,
        model_version,
        recommendation_type,
        COUNT(*) AS total_predictions,
        COUNT(rating) AS predictions_with_feedback,
        AVG(confidence_score) AS avg_confidence,
        STDDEV(confidence_score) AS confidence_stddev,
        AVG(rating) AS avg_rating,
        STDDEV(rating) AS rating_stddev,
        SUM(CASE WHEN action_taken THEN 1 ELSE 0 END)::FLOAT / NULLIF(COUNT(action_taken), 0) AS action_rate,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY hours_to_feedback) AS median_feedback_time,
        -- Statistical significance (z-score for action rate vs baseline 50%)
        (SUM(CASE WHEN action_taken THEN 1 ELSE 0 END)::FLOAT / NULLIF(COUNT(action_taken), 0) - 0.5) 
            / NULLIF(SQRT(0.5 * 0.5 / NULLIF(COUNT(action_taken), 0)), 0) AS action_rate_zscore
    FROM model_predictions
    GROUP BY model_type, model_version, recommendation_type
),
model_comparison AS (
    SELECT 
        model_type,
        model_version,
        AVG(avg_rating) AS overall_avg_rating,
        AVG(action_rate) AS overall_action_rate,
        ROW_NUMBER() OVER (PARTITION BY model_type ORDER BY AVG(avg_rating) DESC, AVG(action_rate) DESC) AS model_rank
    FROM performance_metrics
    GROUP BY model_type, model_version
)
SELECT 
    pm.*,
    mc.model_rank,
    mc.overall_avg_rating,
    mc.overall_action_rate,
    CASE 
        WHEN ABS(pm.action_rate_zscore) > 2.576 THEN 'HIGHLY_SIGNIFICANT' -- 99% confidence
        WHEN ABS(pm.action_rate_zscore) > 1.96 THEN 'SIGNIFICANT' -- 95% confidence
        WHEN ABS(pm.action_rate_zscore) > 1.645 THEN 'MARGINALLY_SIGNIFICANT' -- 90% confidence
        ELSE 'NOT_SIGNIFICANT'
    END AS statistical_significance,
    NOW() AS materialized_at
FROM performance_metrics pm
LEFT JOIN model_comparison mc ON pm.model_type = mc.model_type AND pm.model_version = mc.model_version;

CREATE INDEX idx_mv_ml_model_perf_type_version 
ON mv_ml_model_performance(model_type, model_version);

CREATE INDEX idx_mv_ml_model_perf_significance 
ON mv_ml_model_performance(statistical_significance);

-- ============================================================================
-- User Cohort Analysis View
-- ============================================================================
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_user_cohort_analysis AS
WITH user_cohorts AS (
    SELECT 
        u.id AS user_id,
        DATE_TRUNC('month', u.created_at) AS cohort_month,
        u.created_at AS user_created_at,
        fp.net_worth,
        fp.risk_tolerance,
        COUNT(DISTINCT g.id) AS num_goals,
        COUNT(DISTINCT i.id) AS num_investments
    FROM users u
    LEFT JOIN financial_profiles fp ON u.id = fp.user_id
    LEFT JOIN goals g ON fp.id = g.profile_id
    LEFT JOIN investments i ON fp.id = i.profile_id
    GROUP BY u.id, u.created_at, fp.net_worth, fp.risk_tolerance
),
retention_analysis AS (
    SELECT 
        uc.cohort_month,
        COUNT(DISTINCT uc.user_id) AS cohort_size,
        COUNT(DISTINCT CASE WHEN al.timestamp >= uc.user_created_at + INTERVAL '7 days' 
                           AND al.timestamp < uc.user_created_at + INTERVAL '14 days' 
                      THEN uc.user_id END) AS week_2_retained,
        COUNT(DISTINCT CASE WHEN al.timestamp >= uc.user_created_at + INTERVAL '30 days' 
                           AND al.timestamp < uc.user_created_at + INTERVAL '60 days' 
                      THEN uc.user_id END) AS month_2_retained,
        COUNT(DISTINCT CASE WHEN al.timestamp >= uc.user_created_at + INTERVAL '90 days' 
                           AND al.timestamp < uc.user_created_at + INTERVAL '180 days' 
                      THEN uc.user_id END) AS quarter_2_retained
    FROM user_cohorts uc
    LEFT JOIN audit_logs al ON uc.user_id = al.user_id
    GROUP BY uc.cohort_month
),
cohort_value AS (
    SELECT 
        uc.cohort_month,
        AVG(uc.net_worth) AS avg_net_worth,
        AVG(uc.num_goals) AS avg_goals_per_user,
        AVG(uc.num_investments) AS avg_investments_per_user,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY uc.net_worth) AS median_net_worth
    FROM user_cohorts uc
    GROUP BY uc.cohort_month
)
SELECT 
    ra.cohort_month,
    ra.cohort_size,
    ra.week_2_retained::FLOAT / NULLIF(ra.cohort_size, 0) * 100 AS week_2_retention_rate,
    ra.month_2_retained::FLOAT / NULLIF(ra.cohort_size, 0) * 100 AS month_2_retention_rate,
    ra.quarter_2_retained::FLOAT / NULLIF(ra.cohort_size, 0) * 100 AS quarter_2_retention_rate,
    cv.avg_net_worth,
    cv.median_net_worth,
    cv.avg_goals_per_user,
    cv.avg_investments_per_user,
    NOW() AS materialized_at
FROM retention_analysis ra
LEFT JOIN cohort_value cv ON ra.cohort_month = cv.cohort_month
ORDER BY ra.cohort_month DESC;

CREATE INDEX idx_mv_cohort_analysis_month 
ON mv_user_cohort_analysis(cohort_month DESC);

-- ============================================================================
-- Query Performance Tracking View
-- ============================================================================
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_query_performance AS
SELECT 
    queryid,
    query,
    calls,
    total_exec_time,
    mean_exec_time,
    stddev_exec_time,
    min_exec_time,
    max_exec_time,
    rows,
    100.0 * shared_blks_hit / NULLIF(shared_blks_hit + shared_blks_read, 0) AS cache_hit_ratio,
    blk_read_time + blk_write_time AS total_io_time,
    temp_blks_written,
    NOW() AS materialized_at
FROM pg_stat_statements
WHERE query NOT LIKE '%pg_stat_statements%'
    AND mean_exec_time > 10 -- Only queries taking more than 10ms
ORDER BY total_exec_time DESC
LIMIT 100;

CREATE INDEX idx_mv_query_perf_total_time 
ON mv_query_performance(total_exec_time DESC);

-- ============================================================================
-- Automatic Refresh Scheduling
-- ============================================================================

-- High-frequency refresh (every 5 minutes) for real-time data
-- SELECT cron.schedule('refresh-market-data-5min', '*/5 * * * *', 
--     $$REFRESH MATERIALIZED VIEW CONCURRENTLY market_data_1min;$$);

-- Hourly refresh for portfolio performance
-- SELECT cron.schedule('refresh-portfolio-hourly', '0 * * * *', 
--     $$REFRESH MATERIALIZED VIEW CONCURRENTLY mv_portfolio_performance_advanced;$$);

-- Daily refresh for analytics views
-- SELECT cron.schedule('refresh-analytics-daily', '0 2 * * *', 
--     $$
--     REFRESH MATERIALIZED VIEW CONCURRENTLY mv_goal_analytics;
--     REFRESH MATERIALIZED VIEW CONCURRENTLY mv_ml_model_performance;
--     REFRESH MATERIALIZED VIEW CONCURRENTLY mv_user_cohort_analysis;
--     $$);

-- Weekly refresh for query performance
-- SELECT cron.schedule('refresh-query-perf-weekly', '0 3 * * 0', 
--     $$REFRESH MATERIALIZED VIEW CONCURRENTLY mv_query_performance;$$);

-- ============================================================================
-- Performance Monitoring Functions
-- ============================================================================

CREATE OR REPLACE FUNCTION get_materialized_view_stats()
RETURNS TABLE(
    view_name text,
    size_mb numeric,
    row_count bigint,
    last_refresh timestamp,
    refresh_duration_ms numeric
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        mv.matviewname::text,
        ROUND(pg_relation_size(mv.matviewname::regclass) / 1024.0 / 1024.0, 2) AS size_mb,
        (SELECT COUNT(*) FROM pg_class WHERE relname = mv.matviewname) AS row_count,
        COALESCE(
            (SELECT MAX(refresh_end) FROM materialized_view_refresh_log WHERE view_name = mv.matviewname),
            NOW() - INTERVAL '1 year'
        ) AS last_refresh,
        COALESCE(
            (SELECT AVG(duration_ms) FROM materialized_view_refresh_log WHERE view_name = mv.matviewname AND status = 'SUCCESS'),
            0
        ) AS refresh_duration_ms
    FROM pg_matviews mv
    ORDER BY size_mb DESC;
END;
$$ LANGUAGE plpgsql;

-- Function to analyze index usage
CREATE OR REPLACE FUNCTION analyze_index_usage()
RETURNS TABLE(
    schemaname name,
    tablename name,
    indexname name,
    index_size text,
    index_scans bigint,
    index_efficiency numeric
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        s.schemaname,
        s.tablename,
        s.indexname,
        pg_size_pretty(pg_relation_size(s.indexrelid)) AS index_size,
        s.idx_scan AS index_scans,
        CASE 
            WHEN s.idx_scan > 0 
            THEN ROUND(100.0 * s.idx_tup_read / s.idx_scan, 2)
            ELSE 0
        END AS index_efficiency
    FROM pg_stat_user_indexes s
    ORDER BY s.idx_scan DESC;
END;
$$ LANGUAGE plpgsql;