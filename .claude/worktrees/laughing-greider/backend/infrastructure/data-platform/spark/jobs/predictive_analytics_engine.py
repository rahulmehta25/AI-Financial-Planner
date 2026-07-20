"""
Predictive Analytics Engine for Financial Planning
Advanced machine learning and time series forecasting using Apache Spark
"""

import os
import sys
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
import pandas as pd
from decimal import Decimal

# Spark imports
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import (
    col, when, sum as spark_sum, avg, max as spark_max, min as spark_min,
    count, countDistinct, stddev, variance, lag, lead, 
    datediff, date_add, date_sub, year, month, dayofweek, quarter,
    window, desc, asc, rank, dense_rank, row_number,
    percentile_approx, collect_list, explode, split, coalesce,
    unix_timestamp, from_unixtime, to_date, to_timestamp,
    regexp_replace, trim, upper, lower, abs as spark_abs,
    sqrt, pow as spark_pow, exp, log, sin, cos, rand, randn
)
from pyspark.sql.window import Window
from pyspark.sql.types import *

# ML imports
from pyspark.ml.feature import (
    VectorAssembler, StandardScaler, MinMaxScaler, PCA,
    StringIndexer, OneHotEncoder, Bucketizer, QuantileDiscretizer,
    Word2Vec, CountVectorizer, TfidfVectorizer, HashingTF,
    ChiSqSelector, UnivariateFeatureSelector
)
from pyspark.ml.regression import (
    LinearRegression, DecisionTreeRegressor, RandomForestRegressor,
    GBTRegressor, GeneralizedLinearRegression, AFTSurvivalRegression
)
from pyspark.ml.classification import (
    LogisticRegression, DecisionTreeClassifier, RandomForestClassifier,
    GBTClassifier, NaiveBayes, MultilayerPerceptronClassifier
)
from pyspark.ml.clustering import KMeans, GaussianMixture, BisectingKMeans
from pyspark.ml.recommendation import ALS
from pyspark.ml.evaluation import (
    RegressionEvaluator, BinaryClassificationEvaluator, 
    MulticlassClassificationEvaluator
)
from pyspark.ml.tuning import CrossValidator, ParamGridBuilder, TrainValidationSplit
from pyspark.ml.pipeline import Pipeline, PipelineModel
from pyspark.ml import Pipeline
from pyspark.ml.stat import Correlation, ChiSquareTest

# Time series and advanced analytics
from pyspark.sql.functions import (
    collect_list, sort_array, array, struct, to_json, from_json,
    slice as spark_slice, size, array_contains, array_distinct
)

# Import custom Spark configuration
sys.path.append('/opt/spark/config')
from spark_config import create_analytics_session, DATA_SOURCE_CONFIG

class PredictiveAnalyticsEngine:
    """
    Advanced predictive analytics engine for financial data
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
        
        # Model storage paths
        self.model_path = f"s3a://ml-models/financial-planning/{environment}/"
        self.feature_store_path = f"s3a://feature-store/financial-planning/{environment}/"
        
        self.logger.info(f"Predictive Analytics Engine initialized for {environment}")
    
    def load_data(self, table_name: str, date_range: Optional[Tuple[str, str]] = None) -> DataFrame:
        """
        Load data with optional date filtering
        """
        try:
            # Load from data warehouse
            config = DATA_SOURCE_CONFIG['postgres']
            df = self.spark.read \
                .format("jdbc") \
                .option("url", config['url']) \
                .option("dbtable", table_name) \
                .option("user", config['user']) \
                .option("password", config['password']) \
                .option("driver", config['driver']) \
                .load()
            
            # Apply date filtering if provided
            if date_range and 'date' in df.columns:
                start_date, end_date = date_range
                df = df.filter(
                    (col('date') >= start_date) & 
                    (col('date') <= end_date)
                )
            
            self.logger.info(f"Loaded {df.count()} records from {table_name}")
            return df
            
        except Exception as e:
            self.logger.error(f"Error loading data from {table_name}: {str(e)}")
            raise
    
    def create_time_series_features(self, df: DataFrame, 
                                  value_col: str, 
                                  time_col: str = 'date',
                                  group_cols: List[str] = None) -> DataFrame:
        """
        Create comprehensive time series features
        """
        try:
            if group_cols is None:
                group_cols = []
            
            # Define window specifications
            if group_cols:
                window_spec = Window.partitionBy(*group_cols).orderBy(time_col)
            else:
                window_spec = Window.orderBy(time_col)
            
            # Create lag features
            df_features = df
            for lag_period in [1, 7, 14, 30, 90, 365]:  # Various lag periods
                df_features = df_features.withColumn(
                    f"{value_col}_lag_{lag_period}",
                    lag(value_col, lag_period).over(window_spec)
                )
            
            # Create lead features (for forecasting validation)
            for lead_period in [1, 7, 30]:
                df_features = df_features.withColumn(
                    f"{value_col}_lead_{lead_period}",
                    lead(value_col, lead_period).over(window_spec)
                )
            
            # Rolling statistics
            for window_size in [7, 30, 90, 365]:
                rolling_window = window_spec.rowsBetween(-window_size + 1, 0)
                
                df_features = df_features \
                    .withColumn(
                        f"{value_col}_rolling_mean_{window_size}",
                        avg(value_col).over(rolling_window)
                    ) \
                    .withColumn(
                        f"{value_col}_rolling_std_{window_size}",
                        stddev(value_col).over(rolling_window)
                    ) \
                    .withColumn(
                        f"{value_col}_rolling_min_{window_size}",
                        spark_min(value_col).over(rolling_window)
                    ) \
                    .withColumn(
                        f"{value_col}_rolling_max_{window_size}",
                        spark_max(value_col).over(rolling_window)
                    )
            
            # Rate of change features
            df_features = df_features \
                .withColumn(
                    f"{value_col}_pct_change_1d",
                    (col(value_col) - col(f"{value_col}_lag_1")) / col(f"{value_col}_lag_1") * 100
                ) \
                .withColumn(
                    f"{value_col}_pct_change_7d",
                    (col(value_col) - col(f"{value_col}_lag_7")) / col(f"{value_col}_lag_7") * 100
                ) \
                .withColumn(
                    f"{value_col}_pct_change_30d",
                    (col(value_col) - col(f"{value_col}_lag_30")) / col(f"{value_col}_lag_30") * 100
                )
            
            # Momentum indicators
            df_features = df_features \
                .withColumn(
                    f"{value_col}_momentum_7d",
                    col(value_col) - col(f"{value_col}_rolling_mean_7")
                ) \
                .withColumn(
                    f"{value_col}_momentum_30d",
                    col(value_col) - col(f"{value_col}_rolling_mean_30")
                )
            
            # Volatility features
            df_features = df_features \
                .withColumn(
                    f"{value_col}_volatility_ratio_7d",
                    col(f"{value_col}_rolling_std_7") / col(f"{value_col}_rolling_mean_7")
                ) \
                .withColumn(
                    f"{value_col}_volatility_ratio_30d",
                    col(f"{value_col}_rolling_std_30") / col(f"{value_col}_rolling_mean_30")
                )
            
            # Seasonal features
            df_features = df_features \
                .withColumn("day_of_week", dayofweek(col(time_col))) \
                .withColumn("month", month(col(time_col))) \
                .withColumn("quarter", quarter(col(time_col))) \
                .withColumn("year", year(col(time_col)))
            
            # Cyclical encoding for seasonal features
            df_features = df_features \
                .withColumn("day_of_week_sin", sin(2 * np.pi * col("day_of_week") / 7)) \
                .withColumn("day_of_week_cos", cos(2 * np.pi * col("day_of_week") / 7)) \
                .withColumn("month_sin", sin(2 * np.pi * col("month") / 12)) \
                .withColumn("month_cos", cos(2 * np.pi * col("month") / 12))
            
            # Trend features
            df_features = df_features \
                .withColumn(
                    "days_from_start",
                    datediff(col(time_col), spark_min(col(time_col)).over(Window.partitionBy()))
                ) \
                .withColumn(
                    "linear_trend",
                    col("days_from_start") / 365.0  # Years from start
                )
            
            self.logger.info(f"Created time series features for {value_col}")
            return df_features
            
        except Exception as e:
            self.logger.error(f"Error creating time series features: {str(e)}")
            raise
    
    def build_customer_ltv_model(self, transaction_df: DataFrame, 
                                user_df: DataFrame) -> PipelineModel:
        """
        Build Customer Lifetime Value (LTV) prediction model
        """
        try:
            self.logger.info("Building Customer LTV model...")
            
            # Prepare customer features
            customer_features = user_df.join(
                transaction_df.groupBy("user_key")
                .agg(
                    spark_sum("amount").alias("total_spend"),
                    count("*").alias("transaction_count"),
                    avg("amount").alias("avg_transaction_amount"),
                    countDistinct("category_key").alias("category_diversity"),
                    datediff(spark_max("transaction_datetime"), spark_min("transaction_datetime")).alias("customer_tenure_days"),
                    stddev("amount").alias("spending_volatility")
                ),
                "user_key",
                "left"
            )
            
            # Calculate LTV target (simplified as total spend extrapolated)
            customer_features = customer_features.withColumn(
                "ltv_target",
                when(col("customer_tenure_days") > 0,
                     col("total_spend") * (365.0 / col("customer_tenure_days")) * 3  # 3-year LTV
                ).otherwise(col("total_spend"))
            )
            
            # Feature engineering
            feature_columns = [
                "age", "annual_income", "transaction_count", "avg_transaction_amount",
                "category_diversity", "customer_tenure_days", "spending_volatility"
            ]
            
            # Handle categorical variables
            string_indexer_risk = StringIndexer(
                inputCol="risk_tolerance", outputCol="risk_tolerance_indexed"
            )
            onehot_risk = OneHotEncoder(
                inputCol="risk_tolerance_indexed", outputCol="risk_tolerance_vec"
            )
            
            string_indexer_segment = StringIndexer(
                inputCol="customer_segment", outputCol="customer_segment_indexed"
            )
            onehot_segment = OneHotEncoder(
                inputCol="customer_segment_indexed", outputCol="customer_segment_vec"
            )
            
            # Assemble features
            feature_cols = feature_columns + ["risk_tolerance_vec", "customer_segment_vec"]
            assembler = VectorAssembler(inputCols=feature_cols, outputCol="features")
            
            # Scale features
            scaler = StandardScaler(inputCol="features", outputCol="scaled_features")
            
            # Define models to try
            rf_model = RandomForestRegressor(
                featuresCol="scaled_features",
                labelCol="ltv_target",
                predictionCol="ltv_prediction",
                numTrees=100,
                maxDepth=10,
                seed=42
            )
            
            gbt_model = GBTRegressor(
                featuresCol="scaled_features",
                labelCol="ltv_target",
                predictionCol="ltv_prediction",
                maxIter=100,
                maxDepth=6,
                stepSize=0.1,
                seed=42
            )
            
            # Create pipeline
            pipeline = Pipeline(stages=[
                string_indexer_risk, onehot_risk,
                string_indexer_segment, onehot_segment,
                assembler, scaler, rf_model
            ])
            
            # Split data
            train_df, test_df = customer_features.filter(
                col("ltv_target").isNotNull()
            ).randomSplit([0.8, 0.2], seed=42)
            
            # Train model
            model = pipeline.fit(train_df)
            
            # Evaluate model
            predictions = model.transform(test_df)
            evaluator = RegressionEvaluator(
                labelCol="ltv_target",
                predictionCol="ltv_prediction",
                metricName="rmse"
            )
            
            rmse = evaluator.evaluate(predictions)
            self.logger.info(f"LTV Model RMSE: {rmse}")
            
            # Save model
            model_save_path = f"{self.model_path}customer_ltv_model"
            model.write().overwrite().save(model_save_path)
            
            self.logger.info(f"Customer LTV model saved to {model_save_path}")
            return model
            
        except Exception as e:
            self.logger.error(f"Error building Customer LTV model: {str(e)}")
            raise
    
    def build_churn_prediction_model(self, user_activity_df: DataFrame) -> PipelineModel:
        """
        Build customer churn prediction model
        """
        try:
            self.logger.info("Building churn prediction model...")
            
            # Define churn (simplified - no activity in last 30 days)
            current_date = datetime.now()
            churn_cutoff_date = current_date - timedelta(days=30)
            
            user_activity_df = user_activity_df.withColumn(
                "is_churned",
                when(
                    col("last_activity_date") < churn_cutoff_date.strftime('%Y-%m-%d'),
                    1.0
                ).otherwise(0.0)
            )
            
            # Feature engineering for churn
            churn_features = user_activity_df \
                .withColumn(
                    "days_since_last_activity",
                    datediff(lit(current_date.strftime('%Y-%m-%d')), col("last_activity_date"))
                ) \
                .withColumn(
                    "avg_session_duration_minutes",
                    coalesce(col("avg_session_duration_minutes"), lit(0))
                ) \
                .withColumn(
                    "transaction_frequency",
                    col("total_transactions") / 
                    (col("days_since_registration") / 30.0)  # transactions per month
                ) \
                .withColumn(
                    "engagement_trend",
                    col("recent_logins_30d") / col("total_logins")
                )
            
            # Feature columns
            feature_columns = [
                "days_since_last_activity", "days_since_registration",
                "total_transactions", "avg_transaction_amount", "total_spend",
                "avg_session_duration_minutes", "total_logins", "recent_logins_30d",
                "transaction_frequency", "engagement_trend",
                "number_of_goals", "goals_completed_ratio"
            ]
            
            # Handle categorical features
            string_indexers = []
            onehot_encoders = []
            categorical_cols = ["risk_tolerance", "customer_segment", "age_group"]
            
            for cat_col in categorical_cols:
                indexer = StringIndexer(
                    inputCol=cat_col, 
                    outputCol=f"{cat_col}_indexed"
                )
                encoder = OneHotEncoder(
                    inputCol=f"{cat_col}_indexed", 
                    outputCol=f"{cat_col}_vec"
                )
                string_indexers.append(indexer)
                onehot_encoders.append(encoder)
                feature_columns.append(f"{cat_col}_vec")
            
            # Assemble features
            assembler = VectorAssembler(
                inputCols=feature_columns, 
                outputCol="features"
            )
            
            # Scale features
            scaler = StandardScaler(
                inputCol="features", 
                outputCol="scaled_features"
            )
            
            # Logistic regression for churn prediction
            lr = LogisticRegression(
                featuresCol="scaled_features",
                labelCol="is_churned",
                predictionCol="churn_prediction",
                probabilityCol="churn_probability",
                maxIter=100,
                regParam=0.01,
                elasticNetParam=0.1
            )
            
            # Create pipeline
            pipeline_stages = string_indexers + onehot_encoders + [assembler, scaler, lr]
            pipeline = Pipeline(stages=pipeline_stages)
            
            # Split data
            train_df, test_df = churn_features.filter(
                col("is_churned").isNotNull()
            ).randomSplit([0.8, 0.2], seed=42)
            
            # Train model
            model = pipeline.fit(train_df)
            
            # Evaluate model
            predictions = model.transform(test_df)
            evaluator = BinaryClassificationEvaluator(
                labelCol="is_churned",
                rawPredictionCol="rawPrediction",
                metricName="areaUnderROC"
            )
            
            auc = evaluator.evaluate(predictions)
            self.logger.info(f"Churn Model AUC: {auc}")
            
            # Feature importance (for Random Forest)
            rf_model = RandomForestClassifier(
                featuresCol="scaled_features",
                labelCol="is_churned",
                predictionCol="churn_prediction",
                numTrees=100,
                maxDepth=10
            )
            
            # Save model
            model_save_path = f"{self.model_path}churn_prediction_model"
            model.write().overwrite().save(model_save_path)
            
            self.logger.info(f"Churn prediction model saved to {model_save_path}")
            return model
            
        except Exception as e:
            self.logger.error(f"Error building churn prediction model: {str(e)}")
            raise
    
    def build_spending_forecasting_model(self, transaction_df: DataFrame) -> PipelineModel:
        """
        Build spending forecasting model using time series features
        """
        try:
            self.logger.info("Building spending forecasting model...")
            
            # Aggregate daily spending by user
            daily_spending = transaction_df.filter(col("is_debit") == True) \
                .groupBy("user_key", to_date(col("transaction_datetime")).alias("date")) \
                .agg(
                    spark_sum("amount").alias("daily_spending"),
                    count("*").alias("daily_transaction_count")
                ) \
                .orderBy("user_key", "date")
            
            # Create time series features
            spending_with_features = self.create_time_series_features(
                daily_spending,
                value_col="daily_spending",
                time_col="date",
                group_cols=["user_key"]
            )
            
            # Filter out rows with null lag features (first few days)
            spending_with_features = spending_with_features.filter(
                col("daily_spending_lag_30").isNotNull()
            )
            
            # Feature selection for forecasting
            feature_columns = [
                "daily_spending_lag_1", "daily_spending_lag_7", "daily_spending_lag_30",
                "daily_spending_rolling_mean_7", "daily_spending_rolling_mean_30",
                "daily_spending_rolling_std_7", "daily_spending_rolling_std_30",
                "daily_spending_pct_change_7d", "daily_spending_momentum_7d",
                "day_of_week_sin", "day_of_week_cos", "month_sin", "month_cos",
                "linear_trend", "daily_transaction_count"
            ]
            
            # Assemble features
            assembler = VectorAssembler(
                inputCols=feature_columns,
                outputCol="features"
            )
            
            # Scale features
            scaler = StandardScaler(
                inputCol="features",
                outputCol="scaled_features"
            )
            
            # Gradient Boosted Trees for forecasting
            gbt = GBTRegressor(
                featuresCol="scaled_features",
                labelCol="daily_spending",
                predictionCol="spending_forecast",
                maxIter=100,
                maxDepth=8,
                stepSize=0.1,
                subsamplingRate=0.8
            )
            
            # Create pipeline
            pipeline = Pipeline(stages=[assembler, scaler, gbt])
            
            # Split data (time-based split)
            total_days = spending_with_features.select("date").distinct().count()
            train_days = int(total_days * 0.8)
            
            train_end_date = spending_with_features.select("date") \
                .distinct().orderBy("date") \
                .limit(train_days) \
                .select(spark_max("date")).collect()[0][0]
            
            train_df = spending_with_features.filter(col("date") <= train_end_date)
            test_df = spending_with_features.filter(col("date") > train_end_date)
            
            # Train model
            model = pipeline.fit(train_df)
            
            # Evaluate model
            predictions = model.transform(test_df)
            evaluator = RegressionEvaluator(
                labelCol="daily_spending",
                predictionCol="spending_forecast",
                metricName="rmse"
            )
            
            rmse = evaluator.evaluate(predictions)
            mae_evaluator = RegressionEvaluator(
                labelCol="daily_spending",
                predictionCol="spending_forecast",
                metricName="mae"
            )
            mae = mae_evaluator.evaluate(predictions)
            
            self.logger.info(f"Spending Forecast Model - RMSE: {rmse}, MAE: {mae}")
            
            # Save model
            model_save_path = f"{self.model_path}spending_forecasting_model"
            model.write().overwrite().save(model_save_path)
            
            self.logger.info(f"Spending forecasting model saved to {model_save_path}")
            return model
            
        except Exception as e:
            self.logger.error(f"Error building spending forecasting model: {str(e)}")
            raise
    
    def build_portfolio_optimization_model(self, portfolio_df: DataFrame, 
                                         market_data_df: DataFrame) -> Dict[str, Any]:
        """
        Build portfolio optimization recommendations using modern portfolio theory
        """
        try:
            self.logger.info("Building portfolio optimization model...")
            
            # Calculate returns for each security
            returns_df = market_data_df \
                .withColumn("prev_close", lag("close_price").over(
                    Window.partitionBy("security_key").orderBy("date_key")
                )) \
                .withColumn(
                    "daily_return",
                    (col("close_price") - col("prev_close")) / col("prev_close")
                ) \
                .filter(col("daily_return").isNotNull())
            
            # Calculate correlation matrix
            securities_returns = returns_df.groupBy("security_key") \
                .pivot("date_key") \
                .agg(avg("daily_return")) \
                .fillna(0)
            
            # Feature engineering for portfolio optimization
            security_metrics = returns_df.groupBy("security_key") \
                .agg(
                    avg("daily_return").alias("expected_return"),
                    stddev("daily_return").alias("volatility"),
                    count("*").alias("trading_days"),
                    spark_max("daily_return").alias("max_daily_return"),
                    spark_min("daily_return").alias("min_daily_return")
                ) \
                .withColumn(
                    "sharpe_ratio",
                    col("expected_return") / col("volatility")
                ) \
                .withColumn(
                    "annualized_return",
                    col("expected_return") * 252  # Assuming 252 trading days
                ) \
                .withColumn(
                    "annualized_volatility",
                    col("volatility") * sqrt(lit(252))
                )
            
            # Risk-Return clustering for portfolio construction
            feature_columns = ["expected_return", "volatility", "sharpe_ratio"]
            assembler = VectorAssembler(
                inputCols=feature_columns,
                outputCol="features"
            )
            
            scaler = StandardScaler(
                inputCol="features",
                outputCol="scaled_features"
            )
            
            kmeans = KMeans(
                featuresCol="scaled_features",
                predictionCol="risk_cluster",
                k=5,  # 5 risk categories
                seed=42
            )
            
            pipeline = Pipeline(stages=[assembler, scaler, kmeans])
            model = pipeline.fit(security_metrics)
            clustered_securities = model.transform(security_metrics)
            
            # Generate portfolio recommendations
            portfolio_recommendations = clustered_securities \
                .withColumn(
                    "portfolio_weight_suggestion",
                    when(col("risk_cluster") == 0, 0.05)  # Low risk, low allocation
                    .when(col("risk_cluster") == 1, 0.15)  # Conservative
                    .when(col("risk_cluster") == 2, 0.25)  # Moderate
                    .when(col("risk_cluster") == 3, 0.30)  # Growth
                    .otherwise(0.25)  # High risk/high return
                ) \
                .withColumn(
                    "recommendation_reason",
                    when(col("sharpe_ratio") > 1.0, "High risk-adjusted return")
                    .when(col("volatility") < 0.15, "Low volatility")
                    .when(col("expected_return") > 0.10, "High expected return")
                    .otherwise("Diversification")
                )
            
            # Save recommendations
            recommendations_path = f"{self.feature_store_path}portfolio_recommendations"
            portfolio_recommendations.write.mode("overwrite").parquet(recommendations_path)
            
            # Calculate portfolio-level metrics
            portfolio_metrics = {
                'total_securities_analyzed': security_metrics.count(),
                'avg_expected_return': security_metrics.agg(avg("expected_return")).collect()[0][0],
                'avg_volatility': security_metrics.agg(avg("volatility")).collect()[0][0],
                'model_path': recommendations_path
            }
            
            self.logger.info(f"Portfolio optimization completed: {portfolio_metrics}")
            return portfolio_metrics
            
        except Exception as e:
            self.logger.error(f"Error building portfolio optimization model: {str(e)}")
            raise
    
    def build_fraud_detection_model(self, transaction_df: DataFrame) -> PipelineModel:
        """
        Build advanced fraud detection model
        """
        try:
            self.logger.info("Building fraud detection model...")
            
            # Feature engineering for fraud detection
            user_window = Window.partitionBy("user_key").orderBy("transaction_datetime")
            
            fraud_features = transaction_df \
                .withColumn(
                    "amount_zscore",
                    (col("amount") - avg("amount").over(user_window)) / 
                    stddev("amount").over(user_window)
                ) \
                .withColumn(
                    "time_since_last_transaction",
                    unix_timestamp(col("transaction_datetime")) - 
                    lag(unix_timestamp(col("transaction_datetime"))).over(user_window)
                ) \
                .withColumn(
                    "transaction_frequency_1h",
                    count("*").over(
                        user_window.rowsBetween(-6, 0)  # Assuming 10-min intervals
                    )
                ) \
                .withColumn(
                    "is_unusual_hour",
                    when(
                        (hour(col("transaction_datetime")) < 6) | 
                        (hour(col("transaction_datetime")) > 22),
                        1.0
                    ).otherwise(0.0)
                ) \
                .withColumn(
                    "is_weekend",
                    when(dayofweek(col("transaction_datetime")).isin([1, 7]), 1.0)
                    .otherwise(0.0)
                ) \
                .withColumn(
                    "amount_deviation_from_avg",
                    spark_abs(col("amount") - avg("amount").over(user_window))
                )
            
            # Create synthetic fraud labels (for demonstration - in reality, use known fraud cases)
            fraud_features = fraud_features.withColumn(
                "is_fraud",
                when(
                    (spark_abs(col("amount_zscore")) > 3) |
                    (col("transaction_frequency_1h") > 10) |
                    ((col("is_unusual_hour") == 1) & (col("amount") > 1000)),
                    1.0
                ).otherwise(0.0)
            )
            
            # Feature columns
            feature_columns = [
                "amount", "amount_zscore", "time_since_last_transaction",
                "transaction_frequency_1h", "is_unusual_hour", "is_weekend",
                "amount_deviation_from_avg", "is_international", "is_online"
            ]
            
            # Handle categorical features
            category_indexer = StringIndexer(
                inputCol="category", 
                outputCol="category_indexed"
            )
            category_encoder = OneHotEncoder(
                inputCol="category_indexed", 
                outputCol="category_vec"
            )
            
            # Assemble features
            assembler = VectorAssembler(
                inputCols=feature_columns + ["category_vec"],
                outputCol="features"
            )
            
            # Scale features
            scaler = StandardScaler(
                inputCol="features",
                outputCol="scaled_features"
            )
            
            # Random Forest for fraud detection (handles imbalanced data well)
            rf = RandomForestClassifier(
                featuresCol="scaled_features",
                labelCol="is_fraud",
                predictionCol="fraud_prediction",
                probabilityCol="fraud_probability",
                numTrees=200,
                maxDepth=10,
                subsamplingRate=0.8,
                featureSubsetStrategy="sqrt"
            )
            
            # Create pipeline
            pipeline = Pipeline(stages=[
                category_indexer, category_encoder, assembler, scaler, rf
            ])
            
            # Handle class imbalance by stratified sampling
            fraud_cases = fraud_features.filter(col("is_fraud") == 1.0)
            normal_cases = fraud_features.filter(col("is_fraud") == 0.0)
            
            # Sample to create balanced dataset
            fraud_count = fraud_cases.count()
            normal_sample_ratio = min(1.0, fraud_count * 5 / normal_cases.count())
            
            balanced_data = fraud_cases.union(
                normal_cases.sample(withReplacement=False, fraction=normal_sample_ratio)
            )
            
            # Split data
            train_df, test_df = balanced_data.randomSplit([0.8, 0.2], seed=42)
            
            # Train model
            model = pipeline.fit(train_df)
            
            # Evaluate model
            predictions = model.transform(test_df)
            evaluator = BinaryClassificationEvaluator(
                labelCol="is_fraud",
                rawPredictionCol="rawPrediction",
                metricName="areaUnderROC"
            )
            
            auc = evaluator.evaluate(predictions)
            self.logger.info(f"Fraud Detection Model AUC: {auc}")
            
            # Calculate precision and recall
            precision_evaluator = MulticlassClassificationEvaluator(
                labelCol="is_fraud",
                predictionCol="fraud_prediction",
                metricName="weightedPrecision"
            )
            recall_evaluator = MulticlassClassificationEvaluator(
                labelCol="is_fraud",
                predictionCol="fraud_prediction",
                metricName="weightedRecall"
            )
            
            precision = precision_evaluator.evaluate(predictions)
            recall = recall_evaluator.evaluate(predictions)
            
            self.logger.info(f"Fraud Detection Model - Precision: {precision}, Recall: {recall}")
            
            # Save model
            model_save_path = f"{self.model_path}fraud_detection_model"
            model.write().overwrite().save(model_save_path)
            
            self.logger.info(f"Fraud detection model saved to {model_save_path}")
            return model
            
        except Exception as e:
            self.logger.error(f"Error building fraud detection model: {str(e)}")
            raise
    
    def build_goal_success_predictor(self, goals_df: DataFrame, 
                                   user_df: DataFrame, 
                                   transaction_df: DataFrame) -> PipelineModel:
        """
        Build model to predict goal achievement success
        """
        try:
            self.logger.info("Building goal success prediction model...")
            
            # Calculate goal progress features
            goal_progress = goals_df \
                .withColumn(
                    "progress_ratio",
                    col("current_amount") / col("target_amount")
                ) \
                .withColumn(
                    "days_to_target",
                    datediff(col("target_date"), col("created_date"))
                ) \
                .withColumn(
                    "days_elapsed",
                    datediff(lit(datetime.now().strftime('%Y-%m-%d')), col("created_date"))
                ) \
                .withColumn(
                    "expected_progress_ratio",
                    col("days_elapsed") / col("days_to_target")
                ) \
                .withColumn(
                    "progress_vs_expected",
                    col("progress_ratio") - col("expected_progress_ratio")
                ) \
                .withColumn(
                    "monthly_contribution_needed",
                    (col("target_amount") - col("current_amount")) / 
                    (col("days_to_target") / 30.0)
                )
            
            # Define success (simplified - goals that are 80%+ complete or completed)
            goal_progress = goal_progress.withColumn(
                "will_succeed",
                when(
                    (col("progress_ratio") >= 0.8) | 
                    (col("progress_vs_expected") > 0.2),
                    1.0
                ).otherwise(0.0)
            )
            
            # Join with user characteristics
            goal_features = goal_progress.join(user_df, "user_id", "left")
            
            # Add spending behavior features
            user_spending = transaction_df.groupBy("user_key") \
                .agg(
                    avg("amount").alias("avg_spending"),
                    stddev("amount").alias("spending_volatility"),
                    count("*").alias("total_transactions"),
                    spark_sum("amount").alias("total_spending")
                )
            
            goal_features = goal_features.join(user_spending, "user_key", "left")
            
            # Feature engineering
            goal_features = goal_features \
                .withColumn(
                    "contribution_affordability",
                    col("monthly_contribution_needed") / col("avg_spending")
                ) \
                .withColumn(
                    "goal_ambition_score",
                    col("target_amount") / col("annual_income")
                ) \
                .withColumn(
                    "savings_discipline_score",
                    col("current_amount") / col("days_elapsed")
                )
            
            # Feature columns
            feature_columns = [
                "progress_ratio", "days_to_target", "progress_vs_expected",
                "monthly_contribution_needed", "age", "annual_income",
                "contribution_affordability", "goal_ambition_score",
                "savings_discipline_score", "avg_spending", "spending_volatility"
            ]
            
            # Handle categorical features
            goal_type_indexer = StringIndexer(
                inputCol="goal_type", 
                outputCol="goal_type_indexed"
            )
            goal_type_encoder = OneHotEncoder(
                inputCol="goal_type_indexed", 
                outputCol="goal_type_vec"
            )
            
            risk_indexer = StringIndexer(
                inputCol="risk_tolerance", 
                outputCol="risk_indexed"
            )
            risk_encoder = OneHotEncoder(
                inputCol="risk_indexed", 
                outputCol="risk_vec"
            )
            
            # Assemble features
            assembler = VectorAssembler(
                inputCols=feature_columns + ["goal_type_vec", "risk_vec"],
                outputCol="features"
            )
            
            # Scale features
            scaler = StandardScaler(
                inputCol="features",
                outputCol="scaled_features"
            )
            
            # Gradient Boosted Trees for goal success prediction
            gbt = GBTClassifier(
                featuresCol="scaled_features",
                labelCol="will_succeed",
                predictionCol="success_prediction",
                probabilityCol="success_probability",
                maxIter=100,
                maxDepth=6,
                stepSize=0.1
            )
            
            # Create pipeline
            pipeline = Pipeline(stages=[
                goal_type_indexer, goal_type_encoder,
                risk_indexer, risk_encoder,
                assembler, scaler, gbt
            ])
            
            # Split data
            train_df, test_df = goal_features.filter(
                col("will_succeed").isNotNull()
            ).randomSplit([0.8, 0.2], seed=42)
            
            # Train model
            model = pipeline.fit(train_df)
            
            # Evaluate model
            predictions = model.transform(test_df)
            evaluator = BinaryClassificationEvaluator(
                labelCol="will_succeed",
                rawPredictionCol="rawPrediction",
                metricName="areaUnderROC"
            )
            
            auc = evaluator.evaluate(predictions)
            self.logger.info(f"Goal Success Prediction Model AUC: {auc}")
            
            # Save model
            model_save_path = f"{self.model_path}goal_success_predictor"
            model.write().overwrite().save(model_save_path)
            
            self.logger.info(f"Goal success prediction model saved to {model_save_path}")
            return model
            
        except Exception as e:
            self.logger.error(f"Error building goal success prediction model: {str(e)}")
            raise
    
    def generate_personalized_recommendations(self, user_id: str) -> Dict[str, Any]:
        """
        Generate personalized financial recommendations using trained models
        """
        try:
            self.logger.info(f"Generating recommendations for user {user_id}")
            
            # Load user data
            user_data = self.load_data(
                "dimensions.dim_user"
            ).filter(col("user_id") == user_id)
            
            if user_data.count() == 0:
                return {"error": f"User {user_id} not found"}
            
            # Load models (simplified - in production, use proper model loading)
            recommendations = {
                "user_id": user_id,
                "generated_at": datetime.now().isoformat(),
                "recommendations": []
            }
            
            # LTV-based recommendations
            user_info = user_data.collect()[0]
            if user_info.annual_income and user_info.annual_income > 50000:
                recommendations["recommendations"].append({
                    "type": "investment",
                    "priority": "high",
                    "title": "Increase Investment Allocation",
                    "description": "Based on your income level, consider increasing your investment allocation to 20-25% of income.",
                    "estimated_impact": "High",
                    "category": "wealth_building"
                })
            
            # Goal-based recommendations
            if user_info.age and user_info.age < 35:
                recommendations["recommendations"].append({
                    "type": "savings",
                    "priority": "high",
                    "title": "Emergency Fund Priority",
                    "description": "Build an emergency fund covering 6 months of expenses. Start with automated savings.",
                    "estimated_impact": "High",
                    "category": "financial_security"
                })
            
            # Risk-based recommendations
            if user_info.risk_tolerance == "conservative":
                recommendations["recommendations"].append({
                    "type": "portfolio",
                    "priority": "medium",
                    "title": "Balanced Portfolio Allocation",
                    "description": "Consider a 60/40 stocks/bonds allocation to balance growth with stability.",
                    "estimated_impact": "Medium",
                    "category": "investment_strategy"
                })
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Error generating recommendations for {user_id}: {str(e)}")
            return {"error": str(e)}
    
    def cleanup(self):
        """Clean up Spark session"""
        self.spark.stop()
        self.logger.info("Predictive Analytics Engine cleanup completed")


# Example usage and orchestration
def run_predictive_analytics_pipeline():
    """
    Run the complete predictive analytics pipeline
    """
    engine = PredictiveAnalyticsEngine(environment='production')
    
    try:
        # Load data
        users_df = engine.load_data('dimensions.dim_user')
        transactions_df = engine.load_data('facts.fact_transaction_enhanced')
        goals_df = engine.load_data('dimensions.dim_goal')
        portfolio_df = engine.load_data('facts.fact_portfolio_performance_enhanced')
        market_data_df = engine.load_data('facts.fact_market_data_intraday')
        
        # Build models
        logging.info("Building predictive models...")
        
        # Customer Lifetime Value
        ltv_model = engine.build_customer_ltv_model(transactions_df, users_df)
        
        # Churn Prediction
        user_activity_df = users_df  # Simplified - would join with activity data
        churn_model = engine.build_churn_prediction_model(user_activity_df)
        
        # Spending Forecasting
        spending_model = engine.build_spending_forecasting_model(transactions_df)
        
        # Portfolio Optimization
        portfolio_optimization = engine.build_portfolio_optimization_model(
            portfolio_df, market_data_df
        )
        
        # Fraud Detection
        fraud_model = engine.build_fraud_detection_model(transactions_df)
        
        # Goal Success Prediction
        goal_model = engine.build_goal_success_predictor(
            goals_df, users_df, transactions_df
        )
        
        logging.info("All predictive models built successfully")
        
        # Generate sample recommendations
        sample_user_id = "user_123"  # Replace with actual user ID
        recommendations = engine.generate_personalized_recommendations(sample_user_id)
        logging.info(f"Sample recommendations: {recommendations}")
        
    except Exception as e:
        logging.error(f"Predictive analytics pipeline failed: {str(e)}")
        raise
    finally:
        engine.cleanup()


if __name__ == "__main__":
    run_predictive_analytics_pipeline()