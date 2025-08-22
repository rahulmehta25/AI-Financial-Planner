"""
ML Feature Store Implementation using Feast
Provides feature management, versioning, and online/offline serving for ML models
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import numpy as np
from feast import FeatureStore, Entity, FeatureView, Field, BatchFeatureView
from feast.types import Float32, Float64, Int64, String, Timestamp
from feast.data_source import PostgreSQLSource, FileSource, RedisSource
from feast.infra.offline_stores.contrib.postgres_offline_store.postgres_source import PostgreSQLSource
from feast.value_type import ValueType
from feast.feature_logging import LoggingConfig, LoggingSource

from sqlalchemy import create_engine
import redis
import joblib
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.feature_selection import SelectKBest, f_classif
from sklearn.decomposition import PCA

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FinancialFeatureStore:
    """
    Comprehensive ML Feature Store for Financial Planning Platform
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize Feast Feature Store
        self.feature_store_path = config.get('feature_store_path', './financial_feature_store')
        os.makedirs(self.feature_store_path, exist_ok=True)
        
        # Create Feast configuration
        self.create_feast_config()
        
        # Initialize Feast FeatureStore
        self.store = FeatureStore(repo_path=self.feature_store_path)
        
        # Database connections
        self.postgres_engine = create_engine(config['postgres_connection_string'])
        self.redis_client = redis.Redis(
            host=config.get('redis_host', 'localhost'),
            port=config.get('redis_port', 6379),
            db=config.get('redis_db', 0)
        )
        
        self.logger.info("Financial Feature Store initialized")
    
    def create_feast_config(self):
        """
        Create Feast feature_store.yaml configuration
        """
        feast_config = f"""
project: financial_planning
registry: {self.feature_store_path}/data/registry.db
provider: local
online_store:
  type: redis
  connection_string: "redis://{self.config.get('redis_host', 'localhost')}:{self.config.get('redis_port', 6379)}"
offline_store:
  type: file
entity_key_serialization_version: 2
        """
        
        config_path = os.path.join(self.feature_store_path, 'feature_store.yaml')
        with open(config_path, 'w') as f:
            f.write(feast_config)
        
        self.logger.info(f"Feast configuration created at {config_path}")
    
    def define_entities(self) -> Dict[str, Entity]:
        """
        Define business entities for the feature store
        """
        entities = {
            'user': Entity(
                name="user",
                value_type=ValueType.STRING,
                description="User entity for financial planning"
            ),
            'account': Entity(
                name="account", 
                value_type=ValueType.STRING,
                description="Bank account entity"
            ),
            'security': Entity(
                name="security",
                value_type=ValueType.STRING, 
                description="Financial security/instrument entity"
            ),
            'transaction': Entity(
                name="transaction",
                value_type=ValueType.STRING,
                description="Financial transaction entity"
            ),
            'goal': Entity(
                name="goal",
                value_type=ValueType.STRING,
                description="Financial goal entity"
            )
        }
        
        return entities
    
    def create_user_features(self) -> List[FeatureView]:
        """
        Create user-related feature views
        """
        # Data source for user features
        user_source = PostgreSQLSource(
            name="user_features_source",
            query="""
                SELECT 
                    user_id,
                    age,
                    annual_income,
                    net_worth,
                    risk_tolerance_score,
                    engagement_score,
                    churn_risk_score,
                    financial_health_score,
                    total_accounts,
                    avg_monthly_spending,
                    savings_rate,
                    debt_to_income_ratio,
                    credit_utilization,
                    investment_experience_years,
                    CURRENT_TIMESTAMP as event_timestamp
                FROM marts.customer_360
                WHERE last_updated >= NOW() - INTERVAL '30 days'
            """,
            timestamp_field="event_timestamp"
        )
        
        user_features_fv = FeatureView(
            name="user_features",
            entities=["user"],
            ttl=timedelta(days=30),
            features=[
                Field(name="age", dtype=Int64),
                Field(name="annual_income", dtype=Float64),
                Field(name="net_worth", dtype=Float64),
                Field(name="risk_tolerance_score", dtype=Float32),
                Field(name="engagement_score", dtype=Float32),
                Field(name="churn_risk_score", dtype=Float32),
                Field(name="financial_health_score", dtype=Float32),
                Field(name="total_accounts", dtype=Int64),
                Field(name="avg_monthly_spending", dtype=Float64),
                Field(name="savings_rate", dtype=Float32),
                Field(name="debt_to_income_ratio", dtype=Float32),
                Field(name="credit_utilization", dtype=Float32),
                Field(name="investment_experience_years", dtype=Int64)
            ],
            online=True,
            source=user_source,
            tags={"team": "ml", "category": "user_profile"}
        )
        
        # User behavioral features
        user_behavior_source = PostgreSQLSource(
            name="user_behavior_source",
            query="""
                SELECT 
                    user_id,
                    days_since_last_login,
                    session_count_30d,
                    avg_session_duration,
                    features_used_count,
                    goals_created_count,
                    goals_completed_count,
                    transactions_30d,
                    unique_categories_30d,
                    avg_transaction_amount,
                    spending_volatility,
                    weekend_spending_ratio,
                    night_spending_ratio,
                    CURRENT_TIMESTAMP as event_timestamp
                FROM (
                    SELECT 
                        u.user_id,
                        COALESCE(DATE_PART('day', NOW() - u.last_login_date), 999) as days_since_last_login,
                        COALESCE(ua.session_count_30d, 0) as session_count_30d,
                        COALESCE(ua.avg_session_duration, 0) as avg_session_duration,
                        COALESCE(ua.features_used_count, 0) as features_used_count,
                        COALESCE(g.goals_created, 0) as goals_created_count,
                        COALESCE(g.goals_completed, 0) as goals_completed_count,
                        COALESCE(t.transaction_count, 0) as transactions_30d,
                        COALESCE(t.unique_categories, 0) as unique_categories_30d,
                        COALESCE(t.avg_amount, 0) as avg_transaction_amount,
                        COALESCE(t.amount_stddev, 0) as spending_volatility,
                        COALESCE(t.weekend_ratio, 0) as weekend_spending_ratio,
                        COALESCE(t.night_ratio, 0) as night_spending_ratio
                    FROM dimensions.dim_user u
                    LEFT JOIN (
                        SELECT user_key, 
                               COUNT(*) as session_count_30d,
                               AVG(session_duration_minutes) as avg_session_duration,
                               SUM(features_used) as features_used_count
                        FROM facts.fact_user_activity
                        WHERE date_key >= EXTRACT(EPOCH FROM NOW() - INTERVAL '30 days')::INTEGER / 86400
                        GROUP BY user_key
                    ) ua ON u.user_key = ua.user_key
                    LEFT JOIN (
                        SELECT user_id,
                               COUNT(*) as goals_created,
                               COUNT(*) FILTER (WHERE goal_status = 'completed') as goals_completed
                        FROM dimensions.dim_goal
                        WHERE created_date >= NOW() - INTERVAL '30 days'
                        GROUP BY user_id
                    ) g ON u.user_id = g.user_id
                    LEFT JOIN (
                        SELECT user_key,
                               COUNT(*) as transaction_count,
                               COUNT(DISTINCT category_key) as unique_categories,
                               AVG(amount) as avg_amount,
                               STDDEV(amount) as amount_stddev,
                               AVG(CASE WHEN EXTRACT(dow FROM transaction_datetime) IN (0,6) THEN 1 ELSE 0 END) as weekend_ratio,
                               AVG(CASE WHEN EXTRACT(hour FROM transaction_datetime) BETWEEN 22 AND 6 THEN 1 ELSE 0 END) as night_ratio
                        FROM facts.fact_transaction_enhanced
                        WHERE transaction_datetime >= NOW() - INTERVAL '30 days'
                        GROUP BY user_key
                    ) t ON u.user_key = t.user_key
                    WHERE u.is_current = TRUE
                ) user_stats
            """,
            timestamp_field="event_timestamp"
        )
        
        user_behavior_fv = FeatureView(
            name="user_behavior",
            entities=["user"],
            ttl=timedelta(days=7),
            features=[
                Field(name="days_since_last_login", dtype=Float64),
                Field(name="session_count_30d", dtype=Int64),
                Field(name="avg_session_duration", dtype=Float32),
                Field(name="features_used_count", dtype=Int64),
                Field(name="goals_created_count", dtype=Int64),
                Field(name="goals_completed_count", dtype=Int64),
                Field(name="transactions_30d", dtype=Int64),
                Field(name="unique_categories_30d", dtype=Int64),
                Field(name="avg_transaction_amount", dtype=Float64),
                Field(name="spending_volatility", dtype=Float32),
                Field(name="weekend_spending_ratio", dtype=Float32),
                Field(name="night_spending_ratio", dtype=Float32)
            ],
            online=True,
            source=user_behavior_source,
            tags={"team": "ml", "category": "user_behavior"}
        )
        
        return [user_features_fv, user_behavior_fv]
    
    def create_transaction_features(self) -> List[FeatureView]:
        """
        Create transaction-related feature views
        """
        # Real-time transaction features
        transaction_source = PostgreSQLSource(
            name="transaction_features_source", 
            query="""
                SELECT 
                    transaction_id,
                    user_id,
                    amount,
                    fraud_score,
                    anomaly_score,
                    confidence_score,
                    category_confidence,
                    is_weekend,
                    is_business_hours,
                    is_international,
                    is_online,
                    merchant_risk_score,
                    location_risk_score,
                    velocity_score,
                    amount_zscore,
                    time_since_last_transaction_minutes,
                    transaction_datetime as event_timestamp
                FROM (
                    SELECT 
                        t.transaction_id,
                        u.user_id,
                        t.amount,
                        COALESCE(t.fraud_score, 0) as fraud_score,
                        COALESCE(t.anomaly_score, 0) as anomaly_score,
                        COALESCE(t.confidence_score, 1) as confidence_score,
                        COALESCE(t.category_confidence, 1) as category_confidence,
                        CASE WHEN EXTRACT(dow FROM t.transaction_datetime) IN (0,6) THEN 1 ELSE 0 END as is_weekend,
                        CASE WHEN EXTRACT(hour FROM t.transaction_datetime) BETWEEN 9 AND 17 THEN 1 ELSE 0 END as is_business_hours,
                        COALESCE(t.is_international::int, 0) as is_international,
                        COALESCE(t.is_online::int, 0) as is_online,
                        -- Merchant risk score (simplified)
                        CASE WHEN t.merchant_name IS NOT NULL THEN 
                             COALESCE((SELECT AVG(fraud_score) FROM facts.fact_transaction_enhanced WHERE merchant_name = t.merchant_name), 0)
                             ELSE 0 END as merchant_risk_score,
                        -- Location risk score (simplified)
                        COALESCE(t.anomaly_score * 0.5, 0) as location_risk_score,
                        -- Transaction velocity
                        ROW_NUMBER() OVER (PARTITION BY t.user_key ORDER BY t.transaction_datetime DESC) as velocity_score,
                        -- Amount Z-score (simplified)
                        (t.amount - AVG(t.amount) OVER (PARTITION BY t.user_key)) / 
                        NULLIF(STDDEV(t.amount) OVER (PARTITION BY t.user_key), 0) as amount_zscore,
                        -- Time since last transaction
                        EXTRACT(EPOCH FROM (t.transaction_datetime - 
                                LAG(t.transaction_datetime) OVER (PARTITION BY t.user_key ORDER BY t.transaction_datetime))) / 60 
                        as time_since_last_transaction_minutes,
                        t.transaction_datetime
                    FROM facts.fact_transaction_enhanced t
                    JOIN dimensions.dim_user u ON t.user_key = u.user_key AND u.is_current = TRUE
                    WHERE t.transaction_datetime >= NOW() - INTERVAL '7 days'
                ) tx_features
            """,
            timestamp_field="event_timestamp"
        )
        
        transaction_features_fv = FeatureView(
            name="transaction_features", 
            entities=["transaction"],
            ttl=timedelta(hours=24),
            features=[
                Field(name="user_id", dtype=String),
                Field(name="amount", dtype=Float64),
                Field(name="fraud_score", dtype=Float32),
                Field(name="anomaly_score", dtype=Float32),
                Field(name="confidence_score", dtype=Float32),
                Field(name="category_confidence", dtype=Float32),
                Field(name="is_weekend", dtype=Int64),
                Field(name="is_business_hours", dtype=Int64),
                Field(name="is_international", dtype=Int64),
                Field(name="is_online", dtype=Int64),
                Field(name="merchant_risk_score", dtype=Float32),
                Field(name="location_risk_score", dtype=Float32),
                Field(name="velocity_score", dtype=Int64),
                Field(name="amount_zscore", dtype=Float32),
                Field(name="time_since_last_transaction_minutes", dtype=Float32)
            ],
            online=True,
            source=transaction_source,
            tags={"team": "ml", "category": "transaction_risk"}
        )
        
        return [transaction_features_fv]
    
    def create_portfolio_features(self) -> List[FeatureView]:
        """
        Create portfolio and market-related feature views
        """
        # Portfolio performance features
        portfolio_source = PostgreSQLSource(
            name="portfolio_features_source",
            query="""
                SELECT 
                    user_id,
                    total_portfolio_value,
                    portfolio_return_ytd,
                    portfolio_return_1y,
                    volatility_30d,
                    sharpe_ratio_30d,
                    max_drawdown,
                    beta,
                    alpha,
                    var_95_1d,
                    equity_allocation_pct,
                    fixed_income_allocation_pct,
                    cash_allocation_pct,
                    alternative_allocation_pct,
                    international_allocation_pct,
                    number_of_positions,
                    largest_position_pct,
                    top_10_concentration_pct,
                    esg_score,
                    expense_ratio_weighted,
                    portfolio_age_days,
                    rebalance_frequency_days,
                    CURRENT_TIMESTAMP as event_timestamp
                FROM (
                    SELECT 
                        u.user_id,
                        COALESCE(p.total_market_value, 0) as total_portfolio_value,
                        COALESCE(p.ytd_return, 0) as portfolio_return_ytd,
                        COALESCE(p.annualized_return_1y, 0) as portfolio_return_1y,
                        COALESCE(p.volatility_30d, 0) as volatility_30d,
                        COALESCE(p.sharpe_ratio_30d, 0) as sharpe_ratio_30d,
                        COALESCE(p.max_drawdown, 0) as max_drawdown,
                        COALESCE(p.beta, 1) as beta,
                        COALESCE(p.alpha, 0) as alpha,
                        COALESCE(p.var_95_1d, 0) as var_95_1d,
                        COALESCE(p.equity_allocation_pct, 0) as equity_allocation_pct,
                        COALESCE(p.fixed_income_allocation_pct, 0) as fixed_income_allocation_pct,
                        COALESCE(p.cash_allocation_pct, 0) as cash_allocation_pct,
                        COALESCE(p.alternative_allocation_pct, 0) as alternative_allocation_pct,
                        COALESCE(p.international_allocation_pct, 0) as international_allocation_pct,
                        COALESCE(p.number_of_positions, 0) as number_of_positions,
                        COALESCE(p.largest_position_pct, 0) as largest_position_pct,
                        COALESCE(p.top_10_concentration_pct, 0) as top_10_concentration_pct,
                        COALESCE(p.esg_score, 0) as esg_score,
                        COALESCE(p.expense_ratio_weighted, 0) as expense_ratio_weighted,
                        COALESCE(DATE_PART('day', NOW() - u.registration_date), 0) as portfolio_age_days,
                        30 as rebalance_frequency_days  -- Default rebalance frequency
                    FROM dimensions.dim_user u
                    LEFT JOIN LATERAL (
                        SELECT *
                        FROM facts.fact_portfolio_performance_enhanced pp
                        WHERE pp.user_key = u.user_key
                        ORDER BY pp.date_key DESC
                        LIMIT 1
                    ) p ON true
                    WHERE u.is_current = TRUE
                ) portfolio_stats
            """,
            timestamp_field="event_timestamp"
        )
        
        portfolio_features_fv = FeatureView(
            name="portfolio_features",
            entities=["user"],
            ttl=timedelta(days=1),
            features=[
                Field(name="total_portfolio_value", dtype=Float64),
                Field(name="portfolio_return_ytd", dtype=Float32),
                Field(name="portfolio_return_1y", dtype=Float32),
                Field(name="volatility_30d", dtype=Float32),
                Field(name="sharpe_ratio_30d", dtype=Float32),
                Field(name="max_drawdown", dtype=Float32),
                Field(name="beta", dtype=Float32),
                Field(name="alpha", dtype=Float32),
                Field(name="var_95_1d", dtype=Float64),
                Field(name="equity_allocation_pct", dtype=Float32),
                Field(name="fixed_income_allocation_pct", dtype=Float32),
                Field(name="cash_allocation_pct", dtype=Float32),
                Field(name="alternative_allocation_pct", dtype=Float32),
                Field(name="international_allocation_pct", dtype=Float32),
                Field(name="number_of_positions", dtype=Int64),
                Field(name="largest_position_pct", dtype=Float32),
                Field(name="top_10_concentration_pct", dtype=Float32),
                Field(name="esg_score", dtype=Float32),
                Field(name="expense_ratio_weighted", dtype=Float32),
                Field(name="portfolio_age_days", dtype=Int64),
                Field(name="rebalance_frequency_days", dtype=Int64)
            ],
            online=True,
            source=portfolio_source,
            tags={"team": "ml", "category": "portfolio_performance"}
        )
        
        return [portfolio_features_fv]
    
    def create_goal_features(self) -> List[FeatureView]:
        """
        Create goal-related feature views
        """
        goal_source = PostgreSQLSource(
            name="goal_features_source",
            query="""
                SELECT 
                    goal_id,
                    user_id,
                    goal_type_encoded,
                    target_amount,
                    current_amount,
                    progress_ratio,
                    days_to_target,
                    days_elapsed,
                    monthly_contribution_needed,
                    contribution_frequency_days,
                    goal_priority_rank,
                    success_probability,
                    risk_adjusted_target,
                    goal_complexity_score,
                    similar_goals_success_rate,
                    user_goal_history_score,
                    CURRENT_TIMESTAMP as event_timestamp
                FROM (
                    SELECT 
                        g.goal_id,
                        g.user_id,
                        CASE 
                            WHEN g.goal_type = 'retirement' THEN 1
                            WHEN g.goal_type = 'home_purchase' THEN 2
                            WHEN g.goal_type = 'education' THEN 3
                            WHEN g.goal_type = 'emergency_fund' THEN 4
                            ELSE 0
                        END as goal_type_encoded,
                        g.target_amount,
                        g.current_amount,
                        COALESCE(g.current_amount / NULLIF(g.target_amount, 0), 0) as progress_ratio,
                        COALESCE(DATE_PART('day', g.target_date - CURRENT_DATE), 0) as days_to_target,
                        COALESCE(DATE_PART('day', CURRENT_DATE - g.created_date), 0) as days_elapsed,
                        CASE WHEN g.target_date > CURRENT_DATE THEN
                            (g.target_amount - g.current_amount) / NULLIF(DATE_PART('day', g.target_date - CURRENT_DATE) / 30.0, 0)
                            ELSE 0 END as monthly_contribution_needed,
                        CASE 
                            WHEN g.contribution_frequency = 'weekly' THEN 7
                            WHEN g.contribution_frequency = 'bi_weekly' THEN 14
                            WHEN g.contribution_frequency = 'monthly' THEN 30
                            ELSE 30
                        END as contribution_frequency_days,
                        COALESCE(g.priority_rank, 3) as goal_priority_rank,
                        -- Success probability based on progress and time remaining
                        CASE 
                            WHEN g.target_date < CURRENT_DATE THEN 0
                            WHEN g.current_amount >= g.target_amount THEN 1
                            ELSE GREATEST(0, LEAST(1, 
                                (g.current_amount / g.target_amount) + 
                                (0.5 * (1 - DATE_PART('day', g.target_date - CURRENT_DATE) / 365.0))
                            ))
                        END as success_probability,
                        -- Risk-adjusted target considering market volatility
                        g.target_amount * CASE 
                            WHEN g.risk_tolerance = 'conservative' THEN 1.1
                            WHEN g.risk_tolerance = 'moderate' THEN 1.05
                            ELSE 1.0
                        END as risk_adjusted_target,
                        -- Goal complexity (higher for longer-term, larger goals)
                        LOG(GREATEST(1, g.target_amount / 1000.0)) + 
                        LOG(GREATEST(1, DATE_PART('day', g.target_date - g.created_date) / 365.0)) as goal_complexity_score,
                        -- Success rate of similar goals
                        COALESCE((
                            SELECT AVG(CASE WHEN goal_status = 'completed' THEN 1.0 ELSE 0.0 END)
                            FROM dimensions.dim_goal g2
                            WHERE g2.goal_type = g.goal_type 
                              AND ABS(g2.target_amount - g.target_amount) / g.target_amount < 0.5
                        ), 0.5) as similar_goals_success_rate,
                        -- User's historical goal success rate
                        COALESCE((
                            SELECT AVG(CASE WHEN goal_status = 'completed' THEN 1.0 ELSE 0.0 END)
                            FROM dimensions.dim_goal g3
                            WHERE g3.user_id = g.user_id
                              AND g3.goal_id != g.goal_id
                        ), 0.5) as user_goal_history_score
                    FROM dimensions.dim_goal g
                    WHERE g.goal_status IN ('active', 'paused')
                ) goal_stats
            """,
            timestamp_field="event_timestamp"
        )
        
        goal_features_fv = FeatureView(
            name="goal_features",
            entities=["goal"],
            ttl=timedelta(days=1),
            features=[
                Field(name="user_id", dtype=String),
                Field(name="goal_type_encoded", dtype=Int64),
                Field(name="target_amount", dtype=Float64),
                Field(name="current_amount", dtype=Float64),
                Field(name="progress_ratio", dtype=Float32),
                Field(name="days_to_target", dtype=Int64),
                Field(name="days_elapsed", dtype=Int64),
                Field(name="monthly_contribution_needed", dtype=Float64),
                Field(name="contribution_frequency_days", dtype=Int64),
                Field(name="goal_priority_rank", dtype=Int64),
                Field(name="success_probability", dtype=Float32),
                Field(name="risk_adjusted_target", dtype=Float64),
                Field(name="goal_complexity_score", dtype=Float32),
                Field(name="similar_goals_success_rate", dtype=Float32),
                Field(name="user_goal_history_score", dtype=Float32)
            ],
            online=True,
            source=goal_source,
            tags={"team": "ml", "category": "goal_planning"}
        )
        
        return [goal_features_fv]
    
    def create_market_features(self) -> List[FeatureView]:
        """
        Create market data feature views
        """
        market_source = PostgreSQLSource(
            name="market_features_source",
            query="""
                SELECT 
                    symbol,
                    current_price,
                    volume_normalized,
                    volatility_30d,
                    rsi,
                    macd,
                    moving_avg_ratio_20d,
                    moving_avg_ratio_50d,
                    bollinger_position,
                    volume_spike_ratio,
                    price_momentum_5d,
                    price_momentum_20d,
                    sector_relative_strength,
                    market_correlation,
                    liquidity_score,
                    news_sentiment_score,
                    CURRENT_TIMESTAMP as event_timestamp
                FROM (
                    SELECT 
                        s.symbol,
                        COALESCE(md.close_price, 0) as current_price,
                        -- Normalized volume (0-1 scale)
                        COALESCE(
                            (md.volume - MIN(md.volume) OVER (PARTITION BY md.security_key ORDER BY md.date_key ROWS BETWEEN 29 PRECEDING AND CURRENT ROW)) /
                            NULLIF(MAX(md.volume) OVER (PARTITION BY md.security_key ORDER BY md.date_key ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) - 
                                   MIN(md.volume) OVER (PARTITION BY md.security_key ORDER BY md.date_key ROWS BETWEEN 29 PRECEDING AND CURRENT ROW), 0),
                            0
                        ) as volume_normalized,
                        COALESCE(md.volatility, 0) as volatility_30d,
                        COALESCE(md.rsi, 50) as rsi,
                        COALESCE(md.macd, 0) as macd,
                        -- Moving average ratios
                        COALESCE(md.close_price / NULLIF(md.sma_20, 0), 1) as moving_avg_ratio_20d,
                        COALESCE(md.close_price / NULLIF(md.sma_50, 0), 1) as moving_avg_ratio_50d,
                        -- Bollinger band position (0-1, where 0.5 is middle)
                        CASE 
                            WHEN md.bollinger_upper > md.bollinger_lower THEN
                                (md.close_price - md.bollinger_lower) / (md.bollinger_upper - md.bollinger_lower)
                            ELSE 0.5
                        END as bollinger_position,
                        -- Volume spike ratio
                        COALESCE(
                            md.volume / NULLIF(AVG(md.volume) OVER (
                                PARTITION BY md.security_key 
                                ORDER BY md.date_key 
                                ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
                            ), 0),
                            1
                        ) as volume_spike_ratio,
                        -- Price momentum
                        COALESCE(
                            (md.close_price - LAG(md.close_price, 5) OVER (PARTITION BY md.security_key ORDER BY md.date_key)) /
                            NULLIF(LAG(md.close_price, 5) OVER (PARTITION BY md.security_key ORDER BY md.date_key), 0),
                            0
                        ) as price_momentum_5d,
                        COALESCE(
                            (md.close_price - LAG(md.close_price, 20) OVER (PARTITION BY md.security_key ORDER BY md.date_key)) /
                            NULLIF(LAG(md.close_price, 20) OVER (PARTITION BY md.security_key ORDER BY md.date_key), 0),
                            0
                        ) as price_momentum_20d,
                        -- Sector relative strength (simplified)
                        COALESCE(
                            md.close_price / NULLIF(AVG(md.close_price) OVER (
                                PARTITION BY s.sector 
                                ORDER BY md.date_key 
                                ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
                            ), 0),
                            1
                        ) as sector_relative_strength,
                        -- Market correlation (with SPY - simplified)
                        COALESCE(s.beta, 1) as market_correlation,
                        -- Liquidity score based on volume and bid-ask spread
                        GREATEST(0, 1 - COALESCE(md.bid_ask_spread / NULLIF(md.close_price, 0), 0)) as liquidity_score,
                        -- News sentiment (placeholder - would integrate with news API)
                        0.5 as news_sentiment_score
                    FROM dimensions.dim_security s
                    LEFT JOIN LATERAL (
                        SELECT *
                        FROM facts.fact_market_data_intraday m
                        WHERE m.security_key = s.security_key
                        ORDER BY m.date_key DESC, m.time_key DESC
                        LIMIT 1
                    ) md ON true
                    WHERE s.is_active = TRUE
                      AND s.security_type IN ('stock', 'etf')
                ) market_stats
            """,
            timestamp_field="event_timestamp"
        )
        
        market_features_fv = FeatureView(
            name="market_features",
            entities=["security"],
            ttl=timedelta(hours=1),
            features=[
                Field(name="current_price", dtype=Float64),
                Field(name="volume_normalized", dtype=Float32),
                Field(name="volatility_30d", dtype=Float32),
                Field(name="rsi", dtype=Float32),
                Field(name="macd", dtype=Float32),
                Field(name="moving_avg_ratio_20d", dtype=Float32),
                Field(name="moving_avg_ratio_50d", dtype=Float32),
                Field(name="bollinger_position", dtype=Float32),
                Field(name="volume_spike_ratio", dtype=Float32),
                Field(name="price_momentum_5d", dtype=Float32),
                Field(name="price_momentum_20d", dtype=Float32),
                Field(name="sector_relative_strength", dtype=Float32),
                Field(name="market_correlation", dtype=Float32),
                Field(name="liquidity_score", dtype=Float32),
                Field(name="news_sentiment_score", dtype=Float32)
            ],
            online=True,
            source=market_source,
            tags={"team": "ml", "category": "market_data"}
        )
        
        return [market_features_fv]
    
    def apply_feature_store(self):
        """
        Apply all feature views to the feature store
        """
        try:
            # Define entities
            entities = self.define_entities()
            
            # Create all feature views
            all_feature_views = []
            all_feature_views.extend(self.create_user_features())
            all_feature_views.extend(self.create_transaction_features())
            all_feature_views.extend(self.create_portfolio_features())
            all_feature_views.extend(self.create_goal_features())
            all_feature_views.extend(self.create_market_features())
            
            # Apply entities and feature views
            self.store.apply(list(entities.values()) + all_feature_views)
            
            self.logger.info(f"Applied {len(entities)} entities and {len(all_feature_views)} feature views to the store")
            
        except Exception as e:
            self.logger.error(f"Error applying feature store: {str(e)}")
            raise
    
    def materialize_features(self, start_date: datetime, end_date: datetime):
        """
        Materialize features to the online store
        """
        try:
            self.store.materialize(
                start_date=start_date,
                end_date=end_date
            )
            
            self.logger.info(f"Materialized features from {start_date} to {end_date}")
            
        except Exception as e:
            self.logger.error(f"Error materializing features: {str(e)}")
            raise
    
    def get_online_features(self, entity_ids: Dict[str, List[str]], 
                           feature_refs: List[str]) -> Dict[str, Any]:
        """
        Get features for online serving
        """
        try:
            feature_vector = self.store.get_online_features(
                features=feature_refs,
                entity_rows=[
                    {entity: entity_id for entity, entity_list in entity_ids.items() 
                     for entity_id in entity_list}
                ]
            )
            
            return feature_vector.to_dict()
            
        except Exception as e:
            self.logger.error(f"Error getting online features: {str(e)}")
            raise
    
    def get_historical_features(self, entity_df: pd.DataFrame, 
                              feature_refs: List[str]) -> pd.DataFrame:
        """
        Get historical features for training
        """
        try:
            historical_features = self.store.get_historical_features(
                entity_df=entity_df,
                features=feature_refs
            ).to_df()
            
            return historical_features
            
        except Exception as e:
            self.logger.error(f"Error getting historical features: {str(e)}")
            raise
    
    def create_feature_service(self, name: str, feature_refs: List[str], 
                             description: str = None):
        """
        Create a feature service for model serving
        """
        from feast import FeatureService
        
        feature_service = FeatureService(
            name=name,
            features=feature_refs,
            description=description or f"Feature service for {name}"
        )
        
        self.store.apply([feature_service])
        
        self.logger.info(f"Created feature service: {name}")
        return feature_service
    
    def validate_features(self, feature_refs: List[str]) -> Dict[str, Any]:
        """
        Validate feature quality and consistency
        """
        try:
            validation_results = {
                'feature_count': len(feature_refs),
                'validation_timestamp': datetime.now(),
                'issues': []
            }
            
            # Get sample data for validation
            sample_entities = pd.DataFrame({
                'user_id': ['user_1', 'user_2', 'user_3'],
                'event_timestamp': [datetime.now()] * 3
            })
            
            try:
                sample_features = self.get_historical_features(sample_entities, feature_refs)
                
                # Check for null values
                null_counts = sample_features.isnull().sum()
                high_null_features = null_counts[null_counts > len(sample_features) * 0.5].index.tolist()
                
                if high_null_features:
                    validation_results['issues'].append({
                        'type': 'high_null_values',
                        'features': high_null_features,
                        'message': f"Features with >50% null values: {high_null_features}"
                    })
                
                # Check for constant features
                numeric_features = sample_features.select_dtypes(include=[np.number])
                constant_features = numeric_features.columns[numeric_features.std() == 0].tolist()
                
                if constant_features:
                    validation_results['issues'].append({
                        'type': 'constant_features',
                        'features': constant_features,
                        'message': f"Constant features detected: {constant_features}"
                    })
                
            except Exception as e:
                validation_results['issues'].append({
                    'type': 'retrieval_error',
                    'message': f"Error retrieving features for validation: {str(e)}"
                })
            
            validation_results['is_valid'] = len(validation_results['issues']) == 0
            
            return validation_results
            
        except Exception as e:
            self.logger.error(f"Error validating features: {str(e)}")
            return {
                'is_valid': False,
                'error': str(e),
                'validation_timestamp': datetime.now()
            }
    
    def monitor_feature_drift(self, feature_refs: List[str], 
                            reference_period_days: int = 30) -> Dict[str, Any]:
        """
        Monitor feature drift over time
        """
        try:
            drift_results = {
                'monitoring_timestamp': datetime.now(),
                'reference_period_days': reference_period_days,
                'drift_detected': False,
                'feature_drift_scores': {}
            }
            
            # Get reference period data
            reference_start = datetime.now() - timedelta(days=reference_period_days*2)
            reference_end = datetime.now() - timedelta(days=reference_period_days)
            
            # Get current period data
            current_start = datetime.now() - timedelta(days=reference_period_days)
            current_end = datetime.now()
            
            # Sample entity data for comparison
            sample_entities = pd.DataFrame({
                'user_id': [f'user_{i}' for i in range(1, 101)],  # Sample 100 users
                'event_timestamp': [reference_end] * 100
            })
            
            try:
                # Get reference features
                reference_features = self.get_historical_features(sample_entities, feature_refs)
                
                # Get current features
                sample_entities['event_timestamp'] = current_end
                current_features = self.get_historical_features(sample_entities, feature_refs)
                
                # Calculate drift for numeric features
                numeric_features = reference_features.select_dtypes(include=[np.number]).columns
                
                for feature in numeric_features:
                    if feature in current_features.columns:
                        # Calculate statistical distance (simplified KL divergence)
                        ref_mean = reference_features[feature].mean()
                        curr_mean = current_features[feature].mean()
                        ref_std = reference_features[feature].std()
                        curr_std = current_features[feature].std()
                        
                        # Normalized difference in means
                        mean_drift = abs(curr_mean - ref_mean) / (ref_std + 1e-8)
                        
                        # Ratio of standard deviations
                        std_drift = abs(curr_std - ref_std) / (ref_std + 1e-8)
                        
                        # Combined drift score
                        drift_score = (mean_drift + std_drift) / 2
                        
                        drift_results['feature_drift_scores'][feature] = {
                            'drift_score': drift_score,
                            'drift_level': 'high' if drift_score > 0.5 else 'medium' if drift_score > 0.2 else 'low',
                            'reference_mean': ref_mean,
                            'current_mean': curr_mean,
                            'reference_std': ref_std,
                            'current_std': curr_std
                        }
                        
                        if drift_score > 0.5:
                            drift_results['drift_detected'] = True
                
            except Exception as e:
                drift_results['error'] = f"Error computing drift: {str(e)}"
            
            return drift_results
            
        except Exception as e:
            self.logger.error(f"Error monitoring feature drift: {str(e)}")
            return {
                'drift_detected': False,
                'error': str(e),
                'monitoring_timestamp': datetime.now()
            }
    
    def export_feature_metadata(self) -> Dict[str, Any]:
        """
        Export feature store metadata for documentation and governance
        """
        try:
            registry = self.store.registry
            
            metadata = {
                'export_timestamp': datetime.now().isoformat(),
                'entities': [],
                'feature_views': [],
                'feature_services': []
            }
            
            # Export entities
            for entity in registry.list_entities(project=self.store.project):
                metadata['entities'].append({
                    'name': entity.name,
                    'value_type': entity.value_type.name,
                    'description': entity.description,
                    'tags': entity.tags
                })
            
            # Export feature views
            for fv in registry.list_feature_views(project=self.store.project):
                metadata['feature_views'].append({
                    'name': fv.name,
                    'entities': [e.name for e in fv.entities],
                    'features': [{
                        'name': f.name,
                        'dtype': f.dtype.name
                    } for f in fv.features],
                    'ttl_seconds': fv.ttl.total_seconds(),
                    'online': fv.online,
                    'tags': fv.tags,
                    'source_type': type(fv.source).__name__
                })
            
            # Export feature services
            for fs in registry.list_feature_services(project=self.store.project):
                metadata['feature_services'].append({
                    'name': fs.name,
                    'description': fs.description,
                    'features': [str(f) for f in fs.features]
                })
            
            return metadata
            
        except Exception as e:
            self.logger.error(f"Error exporting metadata: {str(e)}")
            return {
                'error': str(e),
                'export_timestamp': datetime.now().isoformat()
            }


# Example usage and setup
if __name__ == "__main__":
    config = {
        'feature_store_path': './financial_feature_store',
        'postgres_connection_string': 'postgresql://user:password@localhost/financial_planning',
        'redis_host': 'localhost',
        'redis_port': 6379,
        'redis_db': 0
    }
    
    # Initialize feature store
    fs = FinancialFeatureStore(config)
    
    # Apply feature definitions
    fs.apply_feature_store()
    
    # Materialize features
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    fs.materialize_features(start_date, end_date)
    
    # Create feature services for different models
    churn_features = [
        "user_features:age",
        "user_features:engagement_score",
        "user_behavior:days_since_last_login",
        "user_behavior:session_count_30d",
        "portfolio_features:total_portfolio_value"
    ]
    
    fraud_features = [
        "transaction_features:amount",
        "transaction_features:fraud_score",
        "transaction_features:is_international",
        "transaction_features:merchant_risk_score",
        "user_behavior:avg_transaction_amount"
    ]
    
    fs.create_feature_service("churn_prediction_v1", churn_features)
    fs.create_feature_service("fraud_detection_v1", fraud_features)
    
    print("Financial Feature Store setup completed!")
    print("Available feature services: churn_prediction_v1, fraud_detection_v1")
    
    # Example: Get online features for fraud detection
    entity_ids = {'transaction': ['txn_123'], 'user': ['user_456']}
    features = fs.get_online_features(entity_ids, fraud_features)
    print(f"Online features retrieved: {len(features)} features")
    
    # Validate features
    validation_results = fs.validate_features(churn_features)
    print(f"Feature validation: {'PASSED' if validation_results['is_valid'] else 'FAILED'}")
    
    # Monitor drift
    drift_results = fs.monitor_feature_drift(churn_features)
    print(f"Feature drift monitoring: {'DRIFT DETECTED' if drift_results['drift_detected'] else 'NO DRIFT'}")
