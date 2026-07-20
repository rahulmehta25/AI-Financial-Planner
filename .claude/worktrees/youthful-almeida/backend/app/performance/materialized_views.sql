-- Materialized Views for Performance Optimization
-- These views pre-compute complex queries and aggregations for instant access

-- ============================================================================
-- Portfolio Performance Summary View
-- Pre-calculates portfolio metrics for each user
-- ============================================================================
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_portfolio_performance AS
WITH portfolio_values AS (
    SELECT 
        u.id as user_id,
        u.email,
        fp.id as profile_id,
        SUM(i.current_value) as total_portfolio_value,
        SUM(i.initial_investment) as total_invested,
        SUM(i.current_value) - SUM(i.initial_investment) as total_gains,
        (SUM(i.current_value) - SUM(i.initial_investment)) / NULLIF(SUM(i.initial_investment), 0) * 100 as total_return_pct,
        COUNT(DISTINCT i.asset_class) as asset_class_diversity,
        MAX(i.updated_at) as last_update
    FROM users u
    LEFT JOIN financial_profiles fp ON u.id = fp.user_id
    LEFT JOIN investments i ON fp.id = i.profile_id
    GROUP BY u.id, u.email, fp.id
),
risk_metrics AS (
    SELECT 
        profile_id,
        AVG(volatility) as avg_volatility,
        AVG(sharpe_ratio) as avg_sharpe_ratio,
        MAX(max_drawdown) as worst_drawdown
    FROM investment_performance_metrics
    WHERE created_at >= CURRENT_DATE - INTERVAL '1 year'
    GROUP BY profile_id
)
SELECT 
    pv.*,
    rm.avg_volatility,
    rm.avg_sharpe_ratio,
    rm.worst_drawdown,
    NOW() as materialized_at
FROM portfolio_values pv
LEFT JOIN risk_metrics rm ON pv.profile_id = rm.profile_id;

CREATE UNIQUE INDEX idx_mv_portfolio_performance_user 
ON mv_portfolio_performance(user_id);

CREATE INDEX idx_mv_portfolio_performance_update 
ON mv_portfolio_performance(last_update);

-- ============================================================================
-- Goal Progress Tracking View
-- Pre-calculates goal completion percentages and projections
-- ============================================================================
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_goal_progress AS
WITH goal_contributions AS (
    SELECT 
        g.id as goal_id,
        g.profile_id,
        g.name as goal_name,
        g.target_amount,
        g.target_date,
        g.priority,
        g.category,
        COALESCE(SUM(gt.amount), 0) as total_contributed,
        COUNT(gt.id) as num_transactions,
        MAX(gt.transaction_date) as last_contribution_date
    FROM goals g
    LEFT JOIN goal_transactions gt ON g.id = gt.goal_id
    WHERE g.is_active = true
    GROUP BY g.id, g.profile_id, g.name, g.target_amount, g.target_date, g.priority, g.category
),
projections AS (
    SELECT 
        gc.*,
        gc.total_contributed / NULLIF(gc.target_amount, 0) * 100 as completion_percentage,
        CASE 
            WHEN gc.target_date <= CURRENT_DATE THEN 'OVERDUE'
            WHEN gc.total_contributed >= gc.target_amount THEN 'COMPLETED'
            WHEN EXTRACT(DAYS FROM (gc.target_date - CURRENT_DATE)) <= 30 THEN 'AT_RISK'
            ELSE 'ON_TRACK'
        END as status,
        EXTRACT(DAYS FROM (gc.target_date - CURRENT_DATE)) as days_remaining,
        CASE 
            WHEN EXTRACT(DAYS FROM (gc.target_date - CURRENT_DATE)) > 0 
            THEN (gc.target_amount - gc.total_contributed) / NULLIF(EXTRACT(DAYS FROM (gc.target_date - CURRENT_DATE)), 0)
            ELSE 0
        END as required_daily_contribution
    FROM goal_contributions gc
)
SELECT 
    p.*,
    fp.user_id,
    NOW() as materialized_at
FROM projections p
JOIN financial_profiles fp ON p.profile_id = fp.id;

CREATE INDEX idx_mv_goal_progress_profile 
ON mv_goal_progress(profile_id);

CREATE INDEX idx_mv_goal_progress_status 
ON mv_goal_progress(status);

CREATE INDEX idx_mv_goal_progress_user 
ON mv_goal_progress(user_id);

-- ============================================================================
-- Market Data Aggregates View
-- Pre-calculates market statistics and trends
-- ============================================================================
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_market_data_aggregates AS
WITH daily_stats AS (
    SELECT 
        symbol,
        asset_type,
        DATE(timestamp) as trading_date,
        FIRST_VALUE(price) OVER (PARTITION BY symbol, DATE(timestamp) ORDER BY timestamp) as open_price,
        MAX(price) OVER (PARTITION BY symbol, DATE(timestamp)) as high_price,
        MIN(price) OVER (PARTITION BY symbol, DATE(timestamp)) as low_price,
        LAST_VALUE(price) OVER (PARTITION BY symbol, DATE(timestamp) ORDER BY timestamp 
                                RANGE BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) as close_price,
        SUM(volume) OVER (PARTITION BY symbol, DATE(timestamp)) as daily_volume,
        COUNT(*) OVER (PARTITION BY symbol, DATE(timestamp)) as tick_count
    FROM market_data
    WHERE timestamp >= CURRENT_DATE - INTERVAL '90 days'
),
moving_averages AS (
    SELECT 
        symbol,
        trading_date,
        close_price,
        AVG(close_price) OVER (PARTITION BY symbol ORDER BY trading_date ROWS BETWEEN 4 PRECEDING AND CURRENT ROW) as ma_5,
        AVG(close_price) OVER (PARTITION BY symbol ORDER BY trading_date ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) as ma_20,
        AVG(close_price) OVER (PARTITION BY symbol ORDER BY trading_date ROWS BETWEEN 49 PRECEDING AND CURRENT ROW) as ma_50,
        AVG(close_price) OVER (PARTITION BY symbol ORDER BY trading_date ROWS BETWEEN 199 PRECEDING AND CURRENT ROW) as ma_200
    FROM (
        SELECT DISTINCT symbol, trading_date, close_price 
        FROM daily_stats
    ) ds
),
volatility_metrics AS (
    SELECT 
        symbol,
        trading_date,
        close_price,
        STDDEV(close_price) OVER (PARTITION BY symbol ORDER BY trading_date ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) as volatility_20d,
        (close_price - LAG(close_price, 1) OVER (PARTITION BY symbol ORDER BY trading_date)) / 
            NULLIF(LAG(close_price, 1) OVER (PARTITION BY symbol ORDER BY trading_date), 0) * 100 as daily_return_pct
    FROM (
        SELECT DISTINCT symbol, trading_date, close_price 
        FROM daily_stats
    ) ds
)
SELECT 
    ds.symbol,
    ds.asset_type,
    ds.trading_date,
    ds.open_price,
    ds.high_price,
    ds.low_price,
    ds.close_price,
    ds.daily_volume,
    ds.tick_count,
    ma.ma_5,
    ma.ma_20,
    ma.ma_50,
    ma.ma_200,
    vm.volatility_20d,
    vm.daily_return_pct,
    NOW() as materialized_at
FROM daily_stats ds
LEFT JOIN moving_averages ma ON ds.symbol = ma.symbol AND ds.trading_date = ma.trading_date
LEFT JOIN volatility_metrics vm ON ds.symbol = vm.symbol AND ds.trading_date = vm.trading_date;

CREATE INDEX idx_mv_market_data_symbol_date 
ON mv_market_data_aggregates(symbol, trading_date DESC);

CREATE INDEX idx_mv_market_data_date 
ON mv_market_data_aggregates(trading_date DESC);

-- ============================================================================
-- ML Recommendation Performance View
-- Tracks ML model performance and recommendation success rates
-- ============================================================================
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_ml_recommendation_performance AS
WITH recommendation_outcomes AS (
    SELECT 
        r.model_type,
        r.recommendation_type,
        DATE(r.created_at) as recommendation_date,
        COUNT(*) as total_recommendations,
        SUM(CASE WHEN rf.rating >= 4 THEN 1 ELSE 0 END) as positive_feedback,
        SUM(CASE WHEN rf.rating <= 2 THEN 1 ELSE 0 END) as negative_feedback,
        AVG(rf.rating) as avg_rating,
        SUM(CASE WHEN rf.action_taken = true THEN 1 ELSE 0 END) as actions_taken
    FROM ml_recommendations r
    LEFT JOIN ml_recommendation_feedback rf ON r.id = rf.recommendation_id
    WHERE r.created_at >= CURRENT_DATE - INTERVAL '30 days'
    GROUP BY r.model_type, r.recommendation_type, DATE(r.created_at)
),
model_accuracy AS (
    SELECT 
        model_type,
        recommendation_type,
        COUNT(*) as total_predictions,
        AVG(CASE WHEN actions_taken > 0 THEN 1.0 ELSE 0.0 END) * 100 as action_rate,
        AVG(avg_rating) as overall_avg_rating,
        SUM(positive_feedback) / NULLIF(SUM(total_recommendations), 0) * 100 as satisfaction_rate
    FROM recommendation_outcomes
    GROUP BY model_type, recommendation_type
)
SELECT 
    ma.*,
    NOW() as materialized_at
FROM model_accuracy ma;

CREATE INDEX idx_mv_ml_performance_model 
ON mv_ml_recommendation_performance(model_type, recommendation_type);

-- ============================================================================
-- User Activity Summary View
-- Aggregates user engagement and activity metrics
-- ============================================================================
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_user_activity_summary AS
WITH activity_metrics AS (
    SELECT 
        u.id as user_id,
        u.email,
        u.created_at as user_created_at,
        COUNT(DISTINCT DATE(al.timestamp)) as active_days_30d,
        COUNT(DISTINCT al.action) as unique_actions_30d,
        MAX(al.timestamp) as last_activity,
        COUNT(CASE WHEN al.action LIKE 'simulation%' THEN 1 END) as simulation_count,
        COUNT(CASE WHEN al.action LIKE 'goal%' THEN 1 END) as goal_interactions,
        COUNT(CASE WHEN al.action LIKE 'investment%' THEN 1 END) as investment_actions
    FROM users u
    LEFT JOIN audit_logs al ON u.id = al.user_id 
        AND al.timestamp >= CURRENT_DATE - INTERVAL '30 days'
    GROUP BY u.id, u.email, u.created_at
),
engagement_score AS (
    SELECT 
        user_id,
        email,
        user_created_at,
        active_days_30d,
        unique_actions_30d,
        last_activity,
        simulation_count,
        goal_interactions,
        investment_actions,
        (
            (active_days_30d * 3.0) +
            (unique_actions_30d * 2.0) +
            (simulation_count * 1.5) +
            (goal_interactions * 1.0) +
            (investment_actions * 2.5)
        ) / 10.0 as engagement_score,
        CASE 
            WHEN last_activity >= CURRENT_DATE - INTERVAL '7 days' THEN 'ACTIVE'
            WHEN last_activity >= CURRENT_DATE - INTERVAL '30 days' THEN 'MODERATE'
            WHEN last_activity >= CURRENT_DATE - INTERVAL '90 days' THEN 'DORMANT'
            ELSE 'INACTIVE'
        END as activity_status
    FROM activity_metrics
)
SELECT 
    es.*,
    NOW() as materialized_at
FROM engagement_score es;

CREATE UNIQUE INDEX idx_mv_user_activity_user 
ON mv_user_activity_summary(user_id);

CREATE INDEX idx_mv_user_activity_status 
ON mv_user_activity_summary(activity_status);

CREATE INDEX idx_mv_user_activity_engagement 
ON mv_user_activity_summary(engagement_score DESC);

-- ============================================================================
-- Refresh Functions for Materialized Views
-- ============================================================================

-- Function to refresh all materialized views
CREATE OR REPLACE FUNCTION refresh_all_materialized_views()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_portfolio_performance;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_goal_progress;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_market_data_aggregates;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_ml_recommendation_performance;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_user_activity_summary;
END;
$$ LANGUAGE plpgsql;

-- Function to refresh specific materialized view with logging
CREATE OR REPLACE FUNCTION refresh_materialized_view_with_log(view_name text)
RETURNS void AS $$
DECLARE
    start_time timestamp;
    end_time timestamp;
    row_count bigint;
BEGIN
    start_time := clock_timestamp();
    
    EXECUTE format('REFRESH MATERIALIZED VIEW CONCURRENTLY %I', view_name);
    
    end_time := clock_timestamp();
    
    -- Get row count
    EXECUTE format('SELECT COUNT(*) FROM %I', view_name) INTO row_count;
    
    -- Log the refresh
    INSERT INTO materialized_view_refresh_log (
        view_name,
        refresh_start,
        refresh_end,
        duration_ms,
        row_count,
        status
    ) VALUES (
        view_name,
        start_time,
        end_time,
        EXTRACT(MILLISECONDS FROM (end_time - start_time)),
        row_count,
        'SUCCESS'
    );
    
EXCEPTION WHEN OTHERS THEN
    -- Log the error
    INSERT INTO materialized_view_refresh_log (
        view_name,
        refresh_start,
        refresh_end,
        duration_ms,
        status,
        error_message
    ) VALUES (
        view_name,
        start_time,
        clock_timestamp(),
        EXTRACT(MILLISECONDS FROM (clock_timestamp() - start_time)),
        'ERROR',
        SQLERRM
    );
    RAISE;
END;
$$ LANGUAGE plpgsql;

-- Create log table for materialized view refreshes
CREATE TABLE IF NOT EXISTS materialized_view_refresh_log (
    id SERIAL PRIMARY KEY,
    view_name TEXT NOT NULL,
    refresh_start TIMESTAMP NOT NULL,
    refresh_end TIMESTAMP NOT NULL,
    duration_ms BIGINT,
    row_count BIGINT,
    status VARCHAR(20) NOT NULL,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_mv_refresh_log_view 
ON materialized_view_refresh_log(view_name, refresh_start DESC);

-- ============================================================================
-- Scheduled Refresh Jobs (using pg_cron extension)
-- ============================================================================

-- Note: Requires pg_cron extension to be installed
-- CREATE EXTENSION IF NOT EXISTS pg_cron;

-- Schedule hourly refresh for frequently changing data
-- SELECT cron.schedule('refresh-market-data-hourly', '0 * * * *', 
--     $$SELECT refresh_materialized_view_with_log('mv_market_data_aggregates');$$);

-- Schedule daily refresh for portfolio and goal data
-- SELECT cron.schedule('refresh-portfolio-daily', '0 2 * * *', 
--     $$SELECT refresh_materialized_view_with_log('mv_portfolio_performance');$$);

-- SELECT cron.schedule('refresh-goals-daily', '15 2 * * *', 
--     $$SELECT refresh_materialized_view_with_log('mv_goal_progress');$$);

-- Schedule weekly refresh for ML performance metrics
-- SELECT cron.schedule('refresh-ml-weekly', '0 3 * * 0', 
--     $$SELECT refresh_materialized_view_with_log('mv_ml_recommendation_performance');$$);

-- Schedule twice-daily refresh for user activity
-- SELECT cron.schedule('refresh-activity-twice-daily', '0 6,18 * * *', 
--     $$SELECT refresh_materialized_view_with_log('mv_user_activity_summary');$$);