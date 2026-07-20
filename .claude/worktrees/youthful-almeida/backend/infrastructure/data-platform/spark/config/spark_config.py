"""
Apache Spark Configuration for Financial Analytics Platform
Optimized for big data processing and analytics workloads
"""

import os
from pyspark.sql import SparkSession
from pyspark.conf import SparkConf
from typing import Dict, Any, Optional
import logging


class SparkConfigManager:
    """
    Manages Spark configuration for different environments and workloads
    """
    
    def __init__(self, environment: str = 'development'):
        self.environment = environment
        self.logger = logging.getLogger(__name__)
        
    def get_spark_config(self, workload_type: str = 'analytics') -> SparkConf:
        """
        Get optimized Spark configuration based on workload type
        
        Args:
            workload_type: Type of workload (analytics, streaming, ml, etl)
        """
        base_config = self._get_base_config()
        workload_config = self._get_workload_config(workload_type)
        
        # Merge configurations
        final_config = {**base_config, **workload_config}
        
        # Create SparkConf object
        conf = SparkConf()
        for key, value in final_config.items():
            conf.set(key, value)
            
        return conf
    
    def _get_base_config(self) -> Dict[str, Any]:
        """Base Spark configuration for all workloads"""
        
        # Environment-specific settings
        if self.environment == 'production':
            executor_instances = "10"
            executor_cores = "5"
            executor_memory = "8g"
            driver_memory = "4g"
            max_result_size = "2g"
        elif self.environment == 'staging':
            executor_instances = "5"
            executor_cores = "3"
            executor_memory = "4g"
            driver_memory = "2g"
            max_result_size = "1g"
        else:  # development
            executor_instances = "2"
            executor_cores = "2"
            executor_memory = "2g"
            driver_memory = "1g"
            max_result_size = "512m"
        
        base_config = {
            # Application settings
            "spark.app.name": "FinancialAnalyticsPlatform",
            "spark.submit.deployMode": "client",
            
            # Resource allocation
            "spark.executor.instances": executor_instances,
            "spark.executor.cores": executor_cores,
            "spark.executor.memory": executor_memory,
            "spark.driver.memory": driver_memory,
            "spark.driver.maxResultSize": max_result_size,
            
            # Memory management
            "spark.executor.memoryFraction": "0.8",
            "spark.executor.memoryStorageLevel": "MEMORY_AND_DISK_SER",
            "spark.sql.adaptive.enabled": "true",
            "spark.sql.adaptive.coalescePartitions.enabled": "true",
            "spark.sql.adaptive.advisoryPartitionSizeInBytes": "128MB",
            
            # Performance optimization
            "spark.sql.adaptive.skewJoin.enabled": "true",
            "spark.sql.adaptive.localShuffleReader.enabled": "true",
            "spark.sql.cbo.enabled": "true",  # Cost-based optimizer
            "spark.sql.cbo.joinReorder.enabled": "true",
            
            # Shuffle optimization
            "spark.shuffle.service.enabled": "true",
            "spark.dynamicAllocation.enabled": "true",
            "spark.dynamicAllocation.minExecutors": "1",
            "spark.dynamicAllocation.maxExecutors": "20",
            "spark.dynamicAllocation.initialExecutors": "3",
            
            # Serialization
            "spark.serializer": "org.apache.spark.serializer.KryoSerializer",
            "spark.kryo.registrationRequired": "false",
            "spark.kryo.unsafe": "true",
            
            # Networking
            "spark.network.timeout": "300s",
            "spark.executor.heartbeatInterval": "20s",
            
            # Checkpointing
            "spark.sql.streaming.checkpointLocation": "/opt/spark/checkpoints",
            
            # SQL and DataFrame optimization
            "spark.sql.execution.arrow.pyspark.enabled": "true",
            "spark.sql.execution.arrow.maxRecordsPerBatch": "10000",
            "spark.sql.parquet.enableVectorizedReader": "true",
            "spark.sql.parquet.columnarReaderBatchSize": "4096",
            
            # Garbage collection
            "spark.executor.extraJavaOptions": 
                "-XX:+UseG1GC -XX:+PrintGCDetails -XX:+PrintGCTimeStamps",
            "spark.driver.extraJavaOptions": 
                "-XX:+UseG1GC -XX:+PrintGCDetails -XX:+PrintGCTimeStamps",
                
            # Monitoring and logging
            "spark.eventLog.enabled": "true",
            "spark.eventLog.dir": "/opt/spark/event-logs",
            "spark.history.fs.logDirectory": "/opt/spark/event-logs",
            
            # Security (for production)
            "spark.authenticate": "true" if self.environment == 'production' else "false",
            "spark.network.crypto.enabled": "true" if self.environment == 'production' else "false",
            
            # Delta Lake configuration
            "spark.sql.extensions": "io.delta.sql.DeltaSparkSessionExtension",
            "spark.sql.catalog.spark_catalog": "org.apache.spark.sql.delta.catalog.DeltaCatalog",
            
            # Hive support
            "spark.sql.catalogImplementation": "hive",
            "spark.sql.warehouse.dir": "/opt/spark/warehouse",
        }
        
        return base_config
    
    def _get_workload_config(self, workload_type: str) -> Dict[str, Any]:
        """Get workload-specific configuration"""
        
        configs = {
            'analytics': {
                # Optimized for complex analytical queries
                "spark.sql.adaptive.coalescePartitions.minPartitionNum": "1",
                "spark.sql.adaptive.advisoryPartitionSizeInBytes": "256MB",
                "spark.sql.broadcastTimeout": "300",
                "spark.sql.files.maxPartitionBytes": "268435456",  # 256MB
                "spark.default.parallelism": "200",
                "spark.sql.shuffle.partitions": "200",
            },
            
            'streaming': {
                # Optimized for real-time streaming
                "spark.streaming.backpressure.enabled": "true",
                "spark.streaming.kafka.consumer.cache.enabled": "true",
                "spark.streaming.kafka.maxRatePerPartition": "1000",
                "spark.streaming.receiver.maxRate": "10000",
                "spark.streaming.blockInterval": "200ms",
                "spark.streaming.batchDuration": "5s",
                "spark.sql.streaming.metricsEnabled": "true",
                "spark.sql.streaming.ui.enabled": "true",
            },
            
            'ml': {
                # Optimized for machine learning workloads
                "spark.ml.cache.enabled": "true",
                "spark.mllib.local.threshold": "1e6",
                "spark.executor.instances": "20",
                "spark.executor.cores": "4",
                "spark.executor.memory": "12g",
                "spark.driver.memory": "8g",
                "spark.default.parallelism": "400",
                "spark.sql.shuffle.partitions": "400",
            },
            
            'etl': {
                # Optimized for ETL batch processing
                "spark.sql.adaptive.advisoryPartitionSizeInBytes": "512MB",
                "spark.sql.files.maxPartitionBytes": "536870912",  # 512MB
                "spark.default.parallelism": "100",
                "spark.sql.shuffle.partitions": "100",
                "spark.executor.memoryFraction": "0.9",
                "spark.sql.adaptive.coalescePartitions.parallelismFirst": "false",
            }
        }
        
        return configs.get(workload_type, {})
    
    def create_spark_session(self, workload_type: str = 'analytics', 
                           app_name: Optional[str] = None) -> SparkSession:
        """
        Create optimized Spark session
        """
        conf = self.get_spark_config(workload_type)
        
        if app_name:
            conf.set("spark.app.name", app_name)
        
        # Create Spark session
        spark = SparkSession.builder \
            .config(conf=conf) \
            .enableHiveSupport() \
            .getOrCreate()
            
        # Set log level
        if self.environment == 'development':
            spark.sparkContext.setLogLevel("INFO")
        else:
            spark.sparkContext.setLogLevel("WARN")
            
        # Register UDFs and functions
        self._register_udfs(spark)
        
        return spark
    
    def _register_udfs(self, spark: SparkSession):
        """Register custom UDFs for financial calculations"""
        from pyspark.sql.functions import udf
        from pyspark.sql.types import DoubleType, StringType, BooleanType
        import numpy as np
        from datetime import datetime, timedelta
        
        # Financial calculation UDFs
        @udf(returnType=DoubleType())
        def calculate_compound_return(initial_value, final_value, years):
            """Calculate compound annual growth rate"""
            if initial_value <= 0 or final_value <= 0 or years <= 0:
                return 0.0
            return (pow(final_value / initial_value, 1.0 / years) - 1.0) * 100
        
        @udf(returnType=DoubleType())
        def calculate_sharpe_ratio(returns, risk_free_rate=0.02):
            """Calculate Sharpe ratio"""
            if not returns or len(returns) < 2:
                return 0.0
            
            excess_returns = [r - risk_free_rate for r in returns]
            mean_excess = np.mean(excess_returns)
            std_excess = np.std(excess_returns)
            
            return mean_excess / std_excess if std_excess > 0 else 0.0
        
        @udf(returnType=DoubleType())
        def calculate_volatility(returns):
            """Calculate annualized volatility"""
            if not returns or len(returns) < 2:
                return 0.0
            return np.std(returns) * np.sqrt(252)  # Annualized
        
        @udf(returnType=BooleanType())
        def is_business_day(date_str):
            """Check if date is a business day"""
            try:
                date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                return date_obj.weekday() < 5  # Monday = 0, Sunday = 6
            except:
                return False
        
        @udf(returnType=StringType())
        def categorize_transaction_amount(amount):
            """Categorize transaction by amount"""
            abs_amount = abs(float(amount))
            if abs_amount >= 10000:
                return 'VERY_HIGH'
            elif abs_amount >= 1000:
                return 'HIGH'
            elif abs_amount >= 100:
                return 'MEDIUM'
            elif abs_amount >= 10:
                return 'LOW'
            else:
                return 'MICRO'
        
        @udf(returnType=DoubleType())
        def calculate_portfolio_beta(stock_returns, market_returns):
            """Calculate portfolio beta"""
            if not stock_returns or not market_returns or len(stock_returns) != len(market_returns):
                return 1.0
            
            covariance = np.cov(stock_returns, market_returns)[0][1]
            market_variance = np.var(market_returns)
            
            return covariance / market_variance if market_variance > 0 else 1.0
        
        # Register UDFs
        spark.udf.register("calculate_compound_return", calculate_compound_return)
        spark.udf.register("calculate_sharpe_ratio", calculate_sharpe_ratio)
        spark.udf.register("calculate_volatility", calculate_volatility)
        spark.udf.register("is_business_day", is_business_day)
        spark.udf.register("categorize_transaction_amount", categorize_transaction_amount)
        spark.udf.register("calculate_portfolio_beta", calculate_portfolio_beta)
        
        self.logger.info("Registered custom UDFs for financial calculations")


# Convenience functions for different workload types
def create_analytics_session(environment: str = 'development') -> SparkSession:
    """Create Spark session optimized for analytics"""
    config_manager = SparkConfigManager(environment)
    return config_manager.create_spark_session('analytics', 'FinancialAnalytics')

def create_streaming_session(environment: str = 'development') -> SparkSession:
    """Create Spark session optimized for streaming"""
    config_manager = SparkConfigManager(environment)
    return config_manager.create_spark_session('streaming', 'FinancialStreaming')

def create_ml_session(environment: str = 'development') -> SparkSession:
    """Create Spark session optimized for machine learning"""
    config_manager = SparkConfigManager(environment)
    return config_manager.create_spark_session('ml', 'FinancialML')

def create_etl_session(environment: str = 'development') -> SparkSession:
    """Create Spark session optimized for ETL"""
    config_manager = SparkConfigManager(environment)
    return config_manager.create_spark_session('etl', 'FinancialETL')


# Environment configuration
SPARK_ENVIRONMENTS = {
    'development': {
        'master': 'local[*]',
        'executor_memory': '2g',
        'driver_memory': '1g',
        'max_executors': 4
    },
    'staging': {
        'master': 'spark://staging-master:7077',
        'executor_memory': '4g',
        'driver_memory': '2g',
        'max_executors': 10
    },
    'production': {
        'master': 'spark://prod-master:7077',
        'executor_memory': '8g',
        'driver_memory': '4g',
        'max_executors': 50
    }
}

# Data source configurations
DATA_SOURCE_CONFIG = {
    'postgres': {
        'url': 'jdbc:postgresql://localhost:5432/financial_dw',
        'driver': 'org.postgresql.Driver',
        'user': os.getenv('POSTGRES_USER', 'postgres'),
        'password': os.getenv('POSTGRES_PASSWORD', 'password'),
        'properties': {
            'fetchsize': '10000',
            'batchsize': '10000'
        }
    },
    'kafka': {
        'bootstrap_servers': 'localhost:9092',
        'security_protocol': 'PLAINTEXT',
        'group_id': 'spark_financial_analytics',
        'auto_offset_reset': 'earliest',
        'enable_auto_commit': 'true'
    },
    's3': {
        'endpoint': 's3.amazonaws.com',
        'access_key': os.getenv('AWS_ACCESS_KEY_ID'),
        'secret_key': os.getenv('AWS_SECRET_ACCESS_KEY'),
        'bucket': 'financial-platform-data'
    },
    'delta': {
        'table_path': '/opt/spark/delta-tables',
        'checkpoint_location': '/opt/spark/checkpoints'
    }
}

# Performance tuning presets
PERFORMANCE_PRESETS = {
    'memory_optimized': {
        'spark.executor.memoryFraction': '0.9',
        'spark.sql.adaptive.enabled': 'true',
        'spark.sql.adaptive.coalescePartitions.enabled': 'true',
        'spark.sql.adaptive.skewJoin.enabled': 'true'
    },
    'compute_optimized': {
        'spark.executor.cores': '8',
        'spark.default.parallelism': '400',
        'spark.sql.shuffle.partitions': '400',
        'spark.sql.adaptive.advisoryPartitionSizeInBytes': '128MB'
    },
    'io_optimized': {
        'spark.sql.files.maxPartitionBytes': '1073741824',  # 1GB
        'spark.sql.parquet.columnarReaderBatchSize': '8192',
        'spark.hadoop.parquet.enable.dictionary': 'true',
        'spark.hadoop.parquet.compression': 'snappy'
    }
}