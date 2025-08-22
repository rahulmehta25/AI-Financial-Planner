"""
Financial Analytics Engine using Apache Spark
Comprehensive analytics for financial planning data
"""

import os
import sys
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
import pandas as pd

from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import (
    col, when, sum as spark_sum, avg, max as spark_max, min as spark_min,
    count, countDistinct, stddev, variance, corr, lag, lead, 
    datediff, date_add, date_sub, year, month, dayofweek,
    window, desc, asc, rank, dense_rank, row_number,
    percentile_approx, collect_list, explode, split,
    regexp_replace, trim, upper, lower, coalesce,
    unix_timestamp, from_unixtime, to_date, to_timestamp
)
from pyspark.sql.window import Window
from pyspark.sql.types import *
from pyspark.ml.feature import VectorAssembler, StandardScaler
from pyspark.ml.clustering import KMeans
from pyspark.ml.regression import LinearRegression
from pyspark.ml.evaluation import RegressionEvaluator

# Import our custom Spark configuration
sys.path.append('/opt/spark/config')
from spark_config import create_analytics_session, DATA_SOURCE_CONFIG


class FinancialAnalyticsEngine:
    """
    Comprehensive financial analytics engine for processing large-scale financial data
    """
    
    def __init__(self, environment: str = 'development'):
        self.environment = environment
        self.spark = create_analytics_session(environment)
        self.logger = logging.getLogger(__name__)
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        self.logger.info(f"Financial Analytics Engine initialized for {environment}")
    
    def load_data(self, source: str, table_name: str, **kwargs) -> DataFrame:
        """
        Load data from various sources (PostgreSQL, S3, Delta Lake, etc.)
        """
        try:
            if source == 'postgres':
                config = DATA_SOURCE_CONFIG['postgres']
                df = self.spark.read \
                    .format("jdbc") \
                    .option("url", config['url']) \
                    .option("dbtable", table_name) \
                    .option("user", config['user']) \
                    .option("password", config['password']) \
                    .option("driver", config['driver']) \
                    .load()
                    
            elif source == 'delta':
                table_path = f"{DATA_SOURCE_CONFIG['delta']['table_path']}/{table_name}"
                df = self.spark.read.format("delta").load(table_path)
                
            elif source == 's3':
                s3_path = f"s3a://{DATA_SOURCE_CONFIG['s3']['bucket']}/{table_name}"
                df = self.spark.read.parquet(s3_path)
                
            elif source == 'csv':
                file_path = kwargs.get('file_path')
                df = self.spark.read \
                    .option("header", "true") \
                    .option("inferSchema", "true") \
                    .csv(file_path)
            else:
                raise ValueError(f"Unsupported data source: {source}")
            
            self.logger.info(f"Loaded {df.count()} records from {source}.{table_name}")
            return df
            
        except Exception as e:
            self.logger.error(f"Error loading data from {source}.{table_name}: {str(e)}")
            raise
    
    def portfolio_performance_analysis(self, portfolio_df: DataFrame, 
                                     market_data_df: DataFrame) -> DataFrame:
        """
        Comprehensive portfolio performance analysis with risk metrics
        """
        try:
            # Join portfolio with market data
            portfolio_with_market = portfolio_df.alias("p").join(
                market_data_df.alias("m"),
                (col("p.security_key") == col("m.security_key")) & 
                (col("p.date_key") == col("m.date_key")),
                "inner"
            )
            
            # Define window specifications
            user_window = Window.partitionBy("user_key").orderBy("date_key")
            security_window = Window.partitionBy("user_key", "security_key").orderBy("date_key")
            
            # Calculate daily returns
            daily_returns = portfolio_with_market.withColumn(
                "daily_return",
                (col("m.close_price") - lag("m.close_price").over(security_window)) / 
                lag("m.close_price").over(security_window)
            ).withColumn(
                "portfolio_daily_return",
                col("daily_return") * col("p.weight")
            )
            
            # Aggregate portfolio-level metrics
            portfolio_metrics = daily_returns.groupBy("user_key", "date_key").agg(
                spark_sum("portfolio_daily_return").alias("total_daily_return"),
                spark_sum("p.market_value").alias("total_portfolio_value"),
                countDistinct("p.security_key").alias("num_holdings"),
                spark_max("p.weight").alias("max_position_weight"),
                stddev("daily_return").alias("portfolio_volatility")
            )
            
            # Calculate rolling metrics (30-day windows)
            rolling_window = Window.partitionBy("user_key") \
                .orderBy("date_key") \
                .rowsBetween(-29, 0)
            
            portfolio_with_rolling = portfolio_metrics.withColumn(
                "rolling_30d_return",
                avg("total_daily_return").over(rolling_window)
            ).withColumn(
                "rolling_30d_volatility",
                stddev("total_daily_return").over(rolling_window)
            ).withColumn(
                "rolling_sharpe_ratio",
                col("rolling_30d_return") / col("rolling_30d_volatility")
            )
            
            # Calculate maximum drawdown
            cumulative_window = Window.partitionBy("user_key") \
                .orderBy("date_key") \
                .rowsBetween(Window.unboundedPreceding, 0)
            
            portfolio_with_drawdown = portfolio_with_rolling.withColumn(
                "cumulative_return",
                spark_sum("total_daily_return").over(cumulative_window)
            ).withColumn(
                "running_max",
                spark_max("cumulative_return").over(cumulative_window)
            ).withColumn(
                "drawdown",
                col("cumulative_return") - col("running_max")
            )
            
            # Add risk categorization
            risk_categorized = portfolio_with_drawdown.withColumn(
                "risk_category",
                when(col("rolling_30d_volatility") > 0.02, "High Risk")
                .when(col("rolling_30d_volatility") > 0.01, "Medium Risk")
                .otherwise("Low Risk")
            ).withColumn(
                "diversification_score",
                when(col("num_holdings") >= 20, "Well Diversified")
                .when(col("num_holdings") >= 10, "Moderately Diversified")
                .otherwise("Under Diversified")
            )
            
            self.logger.info("Portfolio performance analysis completed")
            return risk_categorized
            
        except Exception as e:
            self.logger.error(f"Error in portfolio performance analysis: {str(e)}")
            raise
    
    def transaction_analytics(self, transaction_df: DataFrame) -> Dict[str, DataFrame]:
        """
        Comprehensive transaction analytics including spending patterns and anomaly detection
        """
        try:
            results = {}
            
            # 1. Spending Pattern Analysis
            spending_patterns = transaction_df.groupBy("user_key", "category_key") \
                .agg(
                    spark_sum("amount").alias("total_spent"),
                    avg("amount").alias("avg_transaction"),
                    count("*").alias("transaction_count"),
                    stddev("amount").alias("amount_volatility")
                ) \
                .withColumn(
                    "spending_consistency",
                    when(col("amount_volatility") / col("avg_transaction") < 0.5, "Consistent")
                    .when(col("amount_volatility") / col("avg_transaction") < 1.0, "Moderate")
                    .otherwise("Volatile")
                )
            
            results['spending_patterns'] = spending_patterns
            
            # 2. Time-based Analysis
            time_analysis = transaction_df \
                .withColumn("hour", (col("time_key") / 3600).cast("int")) \
                .withColumn("day_of_week", dayofweek(to_date(col("date_key").cast("string"), "yyyyMMdd"))) \
                .groupBy("user_key", "hour", "day_of_week") \
                .agg(
                    count("*").alias("transaction_count"),
                    avg("amount").alias("avg_amount")
                ) \
                .withColumn(
                    "peak_spending_time",
                    when((col("hour").between(9, 17)) & (col("day_of_week").between(2, 6)), "Business Hours")
                    .when(col("hour").between(18, 22), "Evening")
                    .when(col("day_of_week").isin(1, 7), "Weekend")
                    .otherwise("Off Hours")
                )
            
            results['time_analysis'] = time_analysis
            
            # 3. Anomaly Detection using statistical methods
            user_window = Window.partitionBy("user_key", "category_key")
            
            anomaly_detection = transaction_df \
                .withColumn("category_avg", avg("amount").over(user_window)) \
                .withColumn("category_stddev", stddev("amount").over(user_window)) \
                .withColumn(
                    "z_score",
                    (col("amount") - col("category_avg")) / col("category_stddev")
                ) \
                .withColumn(
                    "is_anomaly",
                    when(abs(col("z_score")) > 3, True).otherwise(False)
                ) \
                .withColumn(
                    "anomaly_severity",
                    when(abs(col("z_score")) > 4, "Severe")
                    .when(abs(col("z_score")) > 3, "Moderate")
                    .otherwise("Normal")
                )
            
            results['anomaly_detection'] = anomaly_detection.filter(col("is_anomaly") == True)
            
            # 4. Monthly Trend Analysis
            monthly_trends = transaction_df \
                .withColumn("year_month", 
                    concat(year(to_date(col("date_key").cast("string"), "yyyyMMdd")),
                           month(to_date(col("date_key").cast("string"), "yyyyMMdd")))) \
                .groupBy("user_key", "category_key", "year_month") \
                .agg(
                    spark_sum("amount").alias("monthly_total"),
                    count("*").alias("monthly_count")
                )
            
            # Calculate month-over-month growth
            monthly_window = Window.partitionBy("user_key", "category_key").orderBy("year_month")
            monthly_growth = monthly_trends \
                .withColumn("prev_month_total", lag("monthly_total").over(monthly_window)) \
                .withColumn(
                    "mom_growth",
                    (col("monthly_total") - col("prev_month_total")) / col("prev_month_total") * 100
                )
            
            results['monthly_trends'] = monthly_growth
            
            # 5. Cash Flow Analysis
            cash_flow = transaction_df \
                .withColumn("cash_flow_type",
                    when(col("is_credit") == True, "Inflow")
                    .otherwise("Outflow")
                ) \
                .groupBy("user_key", "date_key", "cash_flow_type") \
                .agg(spark_sum("amount").alias("daily_amount")) \
                .groupBy("user_key", "date_key") \
                .pivot("cash_flow_type") \
                .sum("daily_amount") \
                .fillna(0) \
                .withColumn("net_cash_flow", col("Inflow") - col("Outflow"))
            
            # Calculate rolling cash flow metrics
            cash_flow_window = Window.partitionBy("user_key").orderBy("date_key").rowsBetween(-6, 0)
            cash_flow_with_metrics = cash_flow \
                .withColumn("rolling_7d_net", avg("net_cash_flow").over(cash_flow_window)) \
                .withColumn("cash_flow_trend",
                    when(col("rolling_7d_net") > 100, "Positive")
                    .when(col("rolling_7d_net") < -100, "Negative")
                    .otherwise("Neutral")
                )
            
            results['cash_flow'] = cash_flow_with_metrics
            
            self.logger.info("Transaction analytics completed")
            return results
            
        except Exception as e:
            self.logger.error(f"Error in transaction analytics: {str(e)}")
            raise
    
    def cohort_analysis(self, user_df: DataFrame, transaction_df: DataFrame) -> DataFrame:
        """
        Customer cohort analysis based on registration date and spending behavior
        """
        try:
            # Define cohorts based on registration month
            user_cohorts = user_df \
                .withColumn("registration_month", 
                    concat(year(col("registration_date")), 
                           lpad(month(col("registration_date")), 2, "0"))) \
                .select("user_key", "user_id", "registration_date", "registration_month")
            
            # Join with transactions to get spending behavior
            cohort_transactions = transaction_df.alias("t") \
                .join(user_cohorts.alias("u"), "user_key") \
                .withColumn("transaction_month",
                    concat(year(to_date(col("date_key").cast("string"), "yyyyMMdd")),
                           lpad(month(to_date(col("date_key").cast("string"), "yyyyMMdd")), 2, "0")))
            
            # Calculate periods since registration
            cohort_transactions = cohort_transactions \
                .withColumn("period_number",
                    months_between(
                        to_date(col("transaction_month"), "yyyyMM"),
                        to_date(col("registration_month"), "yyyyMM")
                    ).cast("int")
                )
            
            # Cohort metrics by period
            cohort_metrics = cohort_transactions \
                .groupBy("registration_month", "period_number") \
                .agg(
                    countDistinct("user_key").alias("active_users"),
                    spark_sum("amount").alias("total_spending"),
                    avg("amount").alias("avg_transaction_value"),
                    count("*").alias("total_transactions")
                )
            
            # Calculate retention rates
            cohort_sizes = user_cohorts.groupBy("registration_month") \
                .agg(countDistinct("user_key").alias("cohort_size"))
            
            cohort_retention = cohort_metrics.alias("cm") \
                .join(cohort_sizes.alias("cs"), "registration_month") \
                .withColumn("retention_rate", 
                    col("active_users") / col("cohort_size") * 100) \
                .withColumn("avg_spending_per_user",
                    col("total_spending") / col("active_users"))
            
            # Add cohort performance indicators
            cohort_final = cohort_retention \
                .withColumn("cohort_health",
                    when(col("retention_rate") > 80, "Excellent")
                    .when(col("retention_rate") > 60, "Good")
                    .when(col("retention_rate") > 40, "Average")
                    .otherwise("Poor")
                ) \
                .withColumn("revenue_trend",
                    when(col("avg_spending_per_user") > 1000, "High Value")
                    .when(col("avg_spending_per_user") > 500, "Medium Value")
                    .otherwise("Low Value")
                )
            
            self.logger.info("Cohort analysis completed")
            return cohort_final
            
        except Exception as e:
            self.logger.error(f"Error in cohort analysis: {str(e)}")
            raise
    
    def time_series_analysis(self, df: DataFrame, date_col: str, 
                           value_col: str, group_cols: List[str] = None) -> DataFrame:
        """
        Advanced time series analysis with trend detection and forecasting
        """
        try:
            if group_cols is None:
                group_cols = []
            
            # Convert date column to proper format
            ts_df = df.withColumn("date", to_date(col(date_col).cast("string"), "yyyyMMdd"))
            
            # Define window for time series calculations
            if group_cols:
                ts_window = Window.partitionBy(*group_cols).orderBy("date")
            else:
                ts_window = Window.orderBy("date")
            
            # Calculate time series features
            ts_features = ts_df \
                .withColumn("prev_value", lag(value_col, 1).over(ts_window)) \
                .withColumn("prev_7d_value", lag(value_col, 7).over(ts_window)) \
                .withColumn("prev_30d_value", lag(value_col, 30).over(ts_window)) \
                .withColumn(
                    "daily_change",
                    col(value_col) - col("prev_value")
                ) \
                .withColumn(
                    "daily_change_pct",
                    (col(value_col) - col("prev_value")) / col("prev_value") * 100
                ) \
                .withColumn(
                    "weekly_change_pct",
                    (col(value_col) - col("prev_7d_value")) / col("prev_7d_value") * 100
                ) \
                .withColumn(
                    "monthly_change_pct",
                    (col(value_col) - col("prev_30d_value")) / col("prev_30d_value") * 100
                )
            
            # Calculate moving averages
            ma_window_7 = ts_window.rowsBetween(-6, 0)
            ma_window_30 = ts_window.rowsBetween(-29, 0)
            
            ts_with_ma = ts_features \
                .withColumn("ma_7d", avg(value_col).over(ma_window_7)) \
                .withColumn("ma_30d", avg(value_col).over(ma_window_30)) \
                .withColumn("volatility_7d", stddev(value_col).over(ma_window_7)) \
                .withColumn("volatility_30d", stddev(value_col).over(ma_window_30))
            
            # Trend detection
            ts_with_trend = ts_with_ma \
                .withColumn(
                    "trend_direction",
                    when(col(value_col) > col("ma_7d"), "Upward")
                    .when(col(value_col) < col("ma_7d"), "Downward")
                    .otherwise("Sideways")
                ) \
                .withColumn(
                    "volatility_level",
                    when(col("volatility_7d") > col("volatility_30d") * 1.5, "High")
                    .when(col("volatility_7d") < col("volatility_30d") * 0.5, "Low")
                    .otherwise("Normal")
                )
            
            # Seasonality detection (day of week, month patterns)
            ts_with_seasonality = ts_with_trend \
                .withColumn("day_of_week", dayofweek("date")) \
                .withColumn("month", month("date")) \
                .withColumn("quarter", quarter("date"))
            
            # Calculate seasonal averages
            if group_cols:
                seasonal_window = Window.partitionBy(*(group_cols + ["day_of_week"]))
                monthly_window = Window.partitionBy(*(group_cols + ["month"]))
            else:
                seasonal_window = Window.partitionBy("day_of_week")
                monthly_window = Window.partitionBy("month")
            
            ts_final = ts_with_seasonality \
                .withColumn("seasonal_avg_dow", avg(value_col).over(seasonal_window)) \
                .withColumn("seasonal_avg_month", avg(value_col).over(monthly_window)) \
                .withColumn(
                    "seasonal_deviation",
                    (col(value_col) - col("seasonal_avg_dow")) / col("seasonal_avg_dow") * 100
                )
            
            self.logger.info("Time series analysis completed")
            return ts_final
            
        except Exception as e:
            self.logger.error(f"Error in time series analysis: {str(e)}")
            raise
    
    def customer_segmentation(self, user_df: DataFrame, 
                            transaction_df: DataFrame) -> DataFrame:
        """
        Advanced customer segmentation using RFM analysis and machine learning
        """
        try:
            # Calculate RFM metrics
            current_date = datetime.now().date()
            
            # Recency: Days since last transaction
            recency_df = transaction_df \
                .withColumn("transaction_date", to_date(col("date_key").cast("string"), "yyyyMMdd")) \
                .groupBy("user_key") \
                .agg(spark_max("transaction_date").alias("last_transaction_date")) \
                .withColumn("recency", 
                    datediff(lit(current_date), col("last_transaction_date")))
            
            # Frequency: Number of transactions
            frequency_df = transaction_df \
                .groupBy("user_key") \
                .agg(count("*").alias("frequency"))
            
            # Monetary: Total spending amount
            monetary_df = transaction_df \
                .filter(col("amount") > 0) \
                .groupBy("user_key") \
                .agg(spark_sum("amount").alias("monetary"))
            
            # Combine RFM metrics
            rfm_df = recency_df \
                .join(frequency_df, "user_key") \
                .join(monetary_df, "user_key") \
                .join(user_df.select("user_key", "user_id", "age_group", "risk_tolerance"), "user_key")
            
            # Create RFM scores using quintiles
            rfm_with_scores = rfm_df \
                .withColumn("recency_score",
                    when(col("recency") <= 30, 5)
                    .when(col("recency") <= 60, 4)
                    .when(col("recency") <= 90, 3)
                    .when(col("recency") <= 180, 2)
                    .otherwise(1)
                ) \
                .withColumn("frequency_score",
                    when(col("frequency") >= 50, 5)
                    .when(col("frequency") >= 25, 4)
                    .when(col("frequency") >= 10, 3)
                    .when(col("frequency") >= 5, 2)
                    .otherwise(1)
                ) \
                .withColumn("monetary_score",
                    when(col("monetary") >= 10000, 5)
                    .when(col("monetary") >= 5000, 4)
                    .when(col("monetary") >= 1000, 3)
                    .when(col("monetary") >= 500, 2)
                    .otherwise(1)
                )
            
            # Create customer segments based on RFM scores
            customer_segments = rfm_with_scores \
                .withColumn("rfm_segment",
                    when((col("recency_score") >= 4) & (col("frequency_score") >= 4) & (col("monetary_score") >= 4), "Champions")
                    .when((col("recency_score") >= 3) & (col("frequency_score") >= 3) & (col("monetary_score") >= 3), "Loyal Customers")
                    .when((col("recency_score") >= 4) & (col("frequency_score") <= 2), "New Customers")
                    .when((col("recency_score") <= 2) & (col("frequency_score") >= 3) & (col("monetary_score") >= 3), "At Risk")
                    .when((col("recency_score") <= 2) & (col("frequency_score") <= 2), "Lost Customers")
                    .when((col("monetary_score") >= 4), "Big Spenders")
                    .otherwise("Regular Customers")
                ) \
                .withColumn("customer_value",
                    col("recency_score") + col("frequency_score") + col("monetary_score")
                ) \
                .withColumn("value_tier",
                    when(col("customer_value") >= 12, "High Value")
                    .when(col("customer_value") >= 8, "Medium Value")
                    .otherwise("Low Value")
                )
            
            # ML-based clustering for additional insights
            feature_cols = ["recency", "frequency", "monetary"]
            
            # Prepare features for ML
            assembler = VectorAssembler(inputCols=feature_cols, outputCol="features")
            feature_df = assembler.transform(customer_segments)
            
            # Scale features
            scaler = StandardScaler(inputCol="features", outputCol="scaled_features")
            scaler_model = scaler.fit(feature_df)
            scaled_df = scaler_model.transform(feature_df)
            
            # Apply K-means clustering
            kmeans = KMeans(featuresCol="scaled_features", predictionCol="ml_cluster", k=5)
            kmeans_model = kmeans.fit(scaled_df)
            clustered_df = kmeans_model.transform(scaled_df)
            
            # Add cluster interpretation
            final_segments = clustered_df \
                .withColumn("ml_segment_description",
                    when(col("ml_cluster") == 0, "Segment A")
                    .when(col("ml_cluster") == 1, "Segment B")
                    .when(col("ml_cluster") == 2, "Segment C")
                    .when(col("ml_cluster") == 3, "Segment D")
                    .otherwise("Segment E")
                ) \
                .select("user_key", "user_id", "recency", "frequency", "monetary",
                       "recency_score", "frequency_score", "monetary_score",
                       "rfm_segment", "value_tier", "ml_cluster", "ml_segment_description")
            
            self.logger.info("Customer segmentation completed")
            return final_segments
            
        except Exception as e:
            self.logger.error(f"Error in customer segmentation: {str(e)}")
            raise
    
    def risk_analysis(self, portfolio_df: DataFrame, market_data_df: DataFrame) -> DataFrame:
        """
        Comprehensive risk analysis including VaR, CVaR, and stress testing
        """
        try:
            # Join portfolio with market data
            portfolio_market = portfolio_df.alias("p").join(
                market_data_df.alias("m"),
                (col("p.security_key") == col("m.security_key")) & 
                (col("p.date_key") == col("m.date_key")),
                "inner"
            )
            
            # Calculate daily returns for each security
            security_window = Window.partitionBy("user_key", "security_key").orderBy("date_key")
            
            returns_df = portfolio_market \
                .withColumn("prev_price", lag("m.close_price").over(security_window)) \
                .withColumn("daily_return", 
                    (col("m.close_price") - col("prev_price")) / col("prev_price")) \
                .withColumn("weighted_return", 
                    col("daily_return") * col("p.weight"))
            
            # Portfolio-level daily returns
            portfolio_returns = returns_df \
                .groupBy("user_key", "date_key") \
                .agg(spark_sum("weighted_return").alias("portfolio_return"))
            
            # Calculate risk metrics
            user_window = Window.partitionBy("user_key")
            rolling_window = Window.partitionBy("user_key").orderBy("date_key").rowsBetween(-29, 0)
            
            risk_metrics = portfolio_returns \
                .withColumn("portfolio_volatility", stddev("portfolio_return").over(user_window)) \
                .withColumn("rolling_volatility", stddev("portfolio_return").over(rolling_window)) \
                .withColumn("var_95", percentile_approx("portfolio_return", 0.05).over(user_window)) \
                .withColumn("var_99", percentile_approx("portfolio_return", 0.01).over(user_window))
            
            # Calculate Conditional VaR (Expected Shortfall)
            cvar_df = risk_metrics \
                .filter(col("portfolio_return") <= col("var_95")) \
                .groupBy("user_key") \
                .agg(avg("portfolio_return").alias("cvar_95"))
            
            # Join back with main dataset
            risk_final = risk_metrics.alias("rm").join(cvar_df.alias("cv"), "user_key", "left") \
                .withColumn("risk_level",
                    when(col("portfolio_volatility") > 0.03, "High Risk")
                    .when(col("portfolio_volatility") > 0.015, "Medium Risk")
                    .otherwise("Low Risk")
                ) \
                .withColumn("sharpe_ratio",
                    avg("portfolio_return").over(user_window) / col("portfolio_volatility")
                )
            
            # Stress testing scenarios
            stress_scenarios = risk_final \
                .withColumn("stress_scenario_1", col("portfolio_return") * 2)  # 2x volatility
                .withColumn("stress_scenario_2", col("portfolio_return") - 0.05)  # 5% market drop
                .withColumn("stress_scenario_3", 
                    when(col("portfolio_return") > 0, col("portfolio_return") * 0.5)
                    .otherwise(col("portfolio_return") * 1.5)  # Reduced gains, amplified losses
                )
            
            self.logger.info("Risk analysis completed")
            return stress_scenarios
            
        except Exception as e:
            self.logger.error(f"Error in risk analysis: {str(e)}")
            raise
    
    def save_results(self, df: DataFrame, output_path: str, 
                    format: str = 'delta', mode: str = 'overwrite'):
        """
        Save analysis results to various formats
        """
        try:
            writer = df.coalesce(10).write.mode(mode)
            
            if format == 'delta':
                writer.format("delta").save(output_path)
            elif format == 'parquet':
                writer.parquet(output_path)
            elif format == 'postgres':
                config = DATA_SOURCE_CONFIG['postgres']
                writer.format("jdbc") \
                    .option("url", config['url']) \
                    .option("dbtable", output_path) \
                    .option("user", config['user']) \
                    .option("password", config['password']) \
                    .option("driver", config['driver']) \
                    .save()
            else:
                raise ValueError(f"Unsupported output format: {format}")
            
            self.logger.info(f"Results saved to {output_path} in {format} format")
            
        except Exception as e:
            self.logger.error(f"Error saving results: {str(e)}")
            raise
    
    def cleanup(self):
        """Clean up Spark session"""
        self.spark.stop()
        self.logger.info("Spark session stopped")


# Example usage and job orchestration
def run_daily_analytics_job():
    """
    Daily analytics job that runs all core analytics
    """
    engine = FinancialAnalyticsEngine(environment='production')
    
    try:
        # Load data
        users_df = engine.load_data('postgres', 'dimensions.dim_user')
        transactions_df = engine.load_data('postgres', 'facts.fact_transaction')
        portfolio_df = engine.load_data('postgres', 'facts.fact_portfolio_performance')
        market_data_df = engine.load_data('postgres', 'facts.fact_market_data_intraday')
        
        # Run analytics
        portfolio_analysis = engine.portfolio_performance_analysis(portfolio_df, market_data_df)
        transaction_analytics = engine.transaction_analytics(transactions_df)
        cohort_analysis = engine.cohort_analysis(users_df, transactions_df)
        customer_segments = engine.customer_segmentation(users_df, transactions_df)
        risk_analysis = engine.risk_analysis(portfolio_df, market_data_df)
        
        # Save results
        engine.save_results(portfolio_analysis, 'analytics.portfolio_performance', 'delta')
        engine.save_results(transaction_analytics['spending_patterns'], 'analytics.spending_patterns', 'delta')
        engine.save_results(cohort_analysis, 'analytics.cohort_analysis', 'delta')
        engine.save_results(customer_segments, 'analytics.customer_segments', 'delta')
        engine.save_results(risk_analysis, 'analytics.risk_analysis', 'delta')
        
        logging.info("Daily analytics job completed successfully")
        
    except Exception as e:
        logging.error(f"Daily analytics job failed: {str(e)}")
        raise
    finally:
        engine.cleanup()


if __name__ == "__main__":
    run_daily_analytics_job()