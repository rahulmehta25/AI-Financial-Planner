"""
Real-Time Streaming Data Pipeline with Kafka Integration
Handles real-time market data, transaction processing, and event-driven analytics
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import json
import logging
from dataclasses import dataclass

from airflow import DAG
from airflow.operators.python import PythonOperator, BranchPythonOperator
from airflow.operators.bash import BashOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.providers.kafka.operators.kafka import KafkaProduceOperator, KafkaConsumeOperator
from airflow.providers.http.sensors.http import HttpSensor
from airflow.models import Variable
from airflow.utils.dates import days_ago
from airflow.utils.task_group import TaskGroup
from airflow.utils.trigger_rule import TriggerRule
from airflow.sensors.sql import SqlSensor

from kafka import KafkaProducer, KafkaConsumer
from kafka.errors import KafkaError
import pandas as pd
import numpy as np
import requests
from sqlalchemy import create_engine
import redis
from confluent_kafka.avro import AvroProducer, AvroConsumer
from confluent_kafka.schema_registry import SchemaRegistryClient

# Configuration
default_args = {
    'owner': 'streaming-team',
    'depends_on_past': False,
    'start_date': days_ago(1),
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=2),
    'catchup': False,
    'max_active_runs': 2,  # Allow multiple concurrent runs for streaming
    'email': ['streaming-alerts@financialplanning.com']
}

# DAG Definition
dag = DAG(
    'real_time_streaming_enhanced',
    default_args=default_args,
    description='Real-time streaming pipeline with Kafka integration',
    schedule_interval=timedelta(minutes=1),  # High frequency for real-time processing
    catchup=False,
    tags=['streaming', 'kafka', 'real-time', 'market-data'],
    doc_md=__doc__
)

# Streaming Configuration
STREAMING_CONFIG = {
    'kafka': {
        'bootstrap_servers': Variable.get('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092'),
        'schema_registry_url': Variable.get('KAFKA_SCHEMA_REGISTRY_URL', 'http://localhost:8081'),
        'security_protocol': Variable.get('KAFKA_SECURITY_PROTOCOL', 'PLAINTEXT'),
        'sasl_mechanism': Variable.get('KAFKA_SASL_MECHANISM', 'PLAIN'),
        'sasl_username': Variable.get('KAFKA_SASL_USERNAME', ''),
        'sasl_password': Variable.get('KAFKA_SASL_PASSWORD', '')
    },
    'redis': {
        'host': Variable.get('REDIS_HOST', 'localhost'),
        'port': int(Variable.get('REDIS_PORT', '6379')),
        'db': int(Variable.get('REDIS_DB', '0')),
        'password': Variable.get('REDIS_PASSWORD', None)
    },
    'topics': {
        'market_data_raw': 'market-data-raw',
        'market_data_processed': 'market-data-processed',
        'transactions_raw': 'transactions-raw',
        'transactions_processed': 'transactions-processed',
        'alerts': 'financial-alerts',
        'user_events': 'user-events',
        'portfolio_updates': 'portfolio-updates'
    }
}

@dataclass
class MarketDataEvent:
    symbol: str
    price: float
    volume: int
    timestamp: datetime
    exchange: str
    bid: float = None
    ask: float = None
    change_pct: float = None
    source: str = 'unknown'
    
    def to_dict(self) -> Dict:
        return {
            'symbol': self.symbol,
            'price': self.price,
            'volume': self.volume,
            'timestamp': self.timestamp.isoformat(),
            'exchange': self.exchange,
            'bid': self.bid,
            'ask': self.ask,
            'change_pct': self.change_pct,
            'source': self.source
        }

@dataclass
class TransactionEvent:
    user_id: str
    transaction_id: str
    amount: float
    category: str
    merchant: str
    timestamp: datetime
    account_id: str
    is_debit: bool
    description: str = None
    
    def to_dict(self) -> Dict:
        return {
            'user_id': self.user_id,
            'transaction_id': self.transaction_id,
            'amount': self.amount,
            'category': self.category,
            'merchant': self.merchant,
            'timestamp': self.timestamp.isoformat(),
            'account_id': self.account_id,
            'is_debit': self.is_debit,
            'description': self.description
        }

class StreamingProcessor:
    """Real-time streaming data processor"""
    
    def __init__(self):
        self.kafka_config = STREAMING_CONFIG['kafka']
        self.redis_config = STREAMING_CONFIG['redis']
        self.logger = logging.getLogger(__name__)
        
        # Initialize connections
        self.redis_client = redis.Redis(
            host=self.redis_config['host'],
            port=self.redis_config['port'],
            db=self.redis_config['db'],
            password=self.redis_config['password'],
            decode_responses=True
        )
        
        # Schema Registry for Avro
        self.schema_registry_client = SchemaRegistryClient({
            'url': self.kafka_config['schema_registry_url']
        })
        
        # PostgreSQL connection
        self.postgres_hook = PostgresHook(postgres_conn_id='warehouse_postgres')
    
    def create_kafka_producer(self) -> AvroProducer:
        """Create Kafka Avro producer"""
        producer_config = {
            'bootstrap.servers': self.kafka_config['bootstrap_servers'],
            'schema.registry.url': self.kafka_config['schema_registry_url'],
            'acks': 'all',
            'retries': 3,
            'max.in.flight.requests.per.connection': 1,
            'enable.idempotence': True,
            'compression.type': 'snappy'
        }
        
        # Add security config if needed
        if self.kafka_config['security_protocol'] != 'PLAINTEXT':
            producer_config.update({
                'security.protocol': self.kafka_config['security_protocol'],
                'sasl.mechanism': self.kafka_config['sasl_mechanism'],
                'sasl.username': self.kafka_config['sasl_username'],
                'sasl.password': self.kafka_config['sasl_password']
            })
        
        return AvroProducer(producer_config)
    
    def create_kafka_consumer(self, topics: List[str], group_id: str) -> AvroConsumer:
        """Create Kafka Avro consumer"""
        consumer_config = {
            'bootstrap.servers': self.kafka_config['bootstrap_servers'],
            'schema.registry.url': self.kafka_config['schema_registry_url'],
            'group.id': group_id,
            'auto.offset.reset': 'earliest',
            'enable.auto.commit': True,
            'auto.commit.interval.ms': 1000,
            'session.timeout.ms': 30000,
            'max.poll.interval.ms': 300000
        }
        
        # Add security config if needed
        if self.kafka_config['security_protocol'] != 'PLAINTEXT':
            consumer_config.update({
                'security.protocol': self.kafka_config['security_protocol'],
                'sasl.mechanism': self.kafka_config['sasl_mechanism'],
                'sasl.username': self.kafka_config['sasl_username'],
                'sasl.password': self.kafka_config['sasl_password']
            })
        
        consumer = AvroConsumer(consumer_config)
        consumer.subscribe(topics)
        return consumer
    
    def cache_market_data(self, data: MarketDataEvent) -> bool:
        """Cache market data in Redis for fast access"""
        try:
            # Store latest price
            price_key = f"price:{data.symbol}"
            self.redis_client.set(price_key, data.price, ex=3600)  # Expire in 1 hour
            
            # Store in time series for charts
            ts_key = f"prices:{data.symbol}:1m"
            timestamp = int(data.timestamp.timestamp())
            self.redis_client.zadd(ts_key, {f"{data.price}:{data.volume}": timestamp})
            
            # Keep only last 24 hours of data
            cutoff_time = timestamp - (24 * 3600)
            self.redis_client.zremrangebyscore(ts_key, 0, cutoff_time)
            
            # Store market stats
            stats_key = f"stats:{data.symbol}"
            stats = {
                'last_price': data.price,
                'last_volume': data.volume,
                'last_update': data.timestamp.isoformat(),
                'bid': data.bid or 0,
                'ask': data.ask or 0,
                'change_pct': data.change_pct or 0
            }
            self.redis_client.hmset(stats_key, stats)
            self.redis_client.expire(stats_key, 3600)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to cache market data for {data.symbol}: {str(e)}")
            return False
    
    def detect_price_alerts(self, data: MarketDataEvent) -> List[Dict]:
        """Detect price-based alerts and notifications"""
        alerts = []
        
        try:
            # Get previous price for comparison
            prev_price_key = f"prev_price:{data.symbol}"
            prev_price = self.redis_client.get(prev_price_key)
            
            if prev_price:
                prev_price = float(prev_price)
                price_change_pct = ((data.price - prev_price) / prev_price) * 100
                
                # Significant price movement alert (>5% change)
                if abs(price_change_pct) >= 5.0:
                    alerts.append({
                        'type': 'significant_price_movement',
                        'symbol': data.symbol,
                        'current_price': data.price,
                        'previous_price': prev_price,
                        'change_percent': price_change_pct,
                        'timestamp': data.timestamp.isoformat(),
                        'severity': 'high' if abs(price_change_pct) >= 10 else 'medium'
                    })
                
                # Volume spike alert (>200% of average)
                avg_volume_key = f"avg_volume:{data.symbol}"
                avg_volume = self.redis_client.get(avg_volume_key)
                if avg_volume and data.volume > (float(avg_volume) * 2):
                    alerts.append({
                        'type': 'volume_spike',
                        'symbol': data.symbol,
                        'current_volume': data.volume,
                        'average_volume': float(avg_volume),
                        'spike_ratio': data.volume / float(avg_volume),
                        'timestamp': data.timestamp.isoformat(),
                        'severity': 'medium'
                    })
            
            # Update previous price for next comparison
            self.redis_client.set(prev_price_key, data.price, ex=300)  # 5 minute expiry
            
            # Check user-defined price alerts from database
            user_alerts = self.check_user_price_alerts(data)
            alerts.extend(user_alerts)
            
            return alerts
            
        except Exception as e:
            self.logger.error(f"Failed to detect price alerts for {data.symbol}: {str(e)}")
            return []
    
    def check_user_price_alerts(self, data: MarketDataEvent) -> List[Dict]:
        """Check user-defined price alerts"""
        try:
            # Query user alerts from database
            query = """
                SELECT ua.user_id, ua.alert_type, ua.target_price, ua.condition_type, u.email
                FROM user_alerts ua
                JOIN users u ON ua.user_id = u.id
                WHERE ua.symbol = %s 
                AND ua.is_active = true
                AND (
                    (ua.condition_type = 'above' AND %s >= ua.target_price) OR
                    (ua.condition_type = 'below' AND %s <= ua.target_price)
                )
            """
            
            df = pd.read_sql(query, self.postgres_hook.get_sqlalchemy_engine(), 
                           params=[data.symbol, data.price, data.price])
            
            alerts = []
            for _, row in df.iterrows():
                alerts.append({
                    'type': 'user_price_alert',
                    'user_id': row['user_id'],
                    'user_email': row['email'],
                    'symbol': data.symbol,
                    'current_price': data.price,
                    'target_price': row['target_price'],
                    'condition': row['condition_type'],
                    'timestamp': data.timestamp.isoformat(),
                    'severity': 'high'
                })
            
            return alerts
            
        except Exception as e:
            self.logger.error(f"Failed to check user price alerts: {str(e)}")
            return []
    
    def process_transaction_stream(self, transaction: TransactionEvent) -> Dict:
        """Process real-time transaction data"""
        try:
            # Fraud detection
            fraud_score = self.calculate_fraud_score(transaction)
            
            # Spending pattern analysis
            spending_analysis = self.analyze_spending_pattern(transaction)
            
            # Budget impact calculation
            budget_impact = self.calculate_budget_impact(transaction)
            
            # Cache user's latest transaction info
            user_tx_key = f"user_tx:{transaction.user_id}"
            tx_data = {
                'last_transaction_id': transaction.transaction_id,
                'last_amount': transaction.amount,
                'last_merchant': transaction.merchant,
                'last_timestamp': transaction.timestamp.isoformat(),
                'daily_spending': self.get_daily_spending(transaction.user_id) + transaction.amount
            }
            self.redis_client.hmset(user_tx_key, tx_data)
            self.redis_client.expire(user_tx_key, 86400)  # 24 hours
            
            return {
                'transaction_id': transaction.transaction_id,
                'user_id': transaction.user_id,
                'processing_timestamp': datetime.now().isoformat(),
                'fraud_score': fraud_score,
                'spending_analysis': spending_analysis,
                'budget_impact': budget_impact,
                'processed_successfully': True
            }
            
        except Exception as e:
            self.logger.error(f"Failed to process transaction {transaction.transaction_id}: {str(e)}")
            return {
                'transaction_id': transaction.transaction_id,
                'user_id': transaction.user_id,
                'processing_timestamp': datetime.now().isoformat(),
                'error': str(e),
                'processed_successfully': False
            }
    
    def calculate_fraud_score(self, transaction: TransactionEvent) -> float:
        """Calculate fraud risk score for transaction"""
        try:
            score = 0.0
            
            # Check for unusual amount
            user_avg_key = f"user_avg:{transaction.user_id}"
            avg_amount = self.redis_client.get(user_avg_key)
            if avg_amount and transaction.amount > (float(avg_amount) * 5):
                score += 0.3
            
            # Check for rapid transactions
            last_tx_key = f"last_tx_time:{transaction.user_id}"
            last_tx_time = self.redis_client.get(last_tx_key)
            if last_tx_time:
                time_diff = (transaction.timestamp - datetime.fromisoformat(last_tx_time)).total_seconds()
                if time_diff < 60:  # Less than 1 minute
                    score += 0.4
            
            # Update last transaction time
            self.redis_client.set(last_tx_key, transaction.timestamp.isoformat(), ex=3600)
            
            # Check for unusual merchant/location
            user_merchants_key = f"user_merchants:{transaction.user_id}"
            known_merchants = self.redis_client.smembers(user_merchants_key)
            if transaction.merchant not in known_merchants:
                score += 0.2
                # Add to known merchants
                self.redis_client.sadd(user_merchants_key, transaction.merchant)
                self.redis_client.expire(user_merchants_key, 2592000)  # 30 days
            
            # Cap the score at 1.0
            return min(score, 1.0)
            
        except Exception as e:
            self.logger.error(f"Failed to calculate fraud score: {str(e)}")
            return 0.0
    
    def analyze_spending_pattern(self, transaction: TransactionEvent) -> Dict:
        """Analyze spending patterns and trends"""
        try:
            # Get daily spending so far
            daily_spending = self.get_daily_spending(transaction.user_id)
            
            # Get weekly spending
            weekly_spending = self.get_weekly_spending(transaction.user_id)
            
            # Get category spending
            category_spending = self.get_category_spending(transaction.user_id, transaction.category)
            
            # Calculate trends
            daily_trend = 'increasing' if daily_spending > 100 else 'normal'  # Simple threshold
            category_trend = 'high' if category_spending > 500 else 'normal'
            
            return {
                'daily_spending_total': daily_spending,
                'weekly_spending_total': weekly_spending,
                'category_spending_total': category_spending,
                'daily_trend': daily_trend,
                'category_trend': category_trend,
                'is_weekend': transaction.timestamp.weekday() >= 5,
                'is_business_hours': 9 <= transaction.timestamp.hour <= 17
            }
            
        except Exception as e:
            self.logger.error(f"Failed to analyze spending pattern: {str(e)}")
            return {}
    
    def calculate_budget_impact(self, transaction: TransactionEvent) -> Dict:
        """Calculate impact on user budgets"""
        try:
            # Get user's budget for this category
            budget_query = """
                SELECT monthly_limit, spent_amount 
                FROM user_budgets 
                WHERE user_id = %s AND category = %s 
                AND EXTRACT(YEAR FROM created_date) = %s 
                AND EXTRACT(MONTH FROM created_date) = %s
            """
            
            df = pd.read_sql(
                budget_query, 
                self.postgres_hook.get_sqlalchemy_engine(),
                params=[
                    transaction.user_id, 
                    transaction.category,
                    transaction.timestamp.year,
                    transaction.timestamp.month
                ]
            )
            
            if not df.empty:
                budget = df.iloc[0]
                new_spent = budget['spent_amount'] + transaction.amount
                remaining = budget['monthly_limit'] - new_spent
                utilization_pct = (new_spent / budget['monthly_limit']) * 100
                
                return {
                    'has_budget': True,
                    'monthly_limit': budget['monthly_limit'],
                    'spent_before': budget['spent_amount'],
                    'spent_after': new_spent,
                    'remaining': remaining,
                    'utilization_percent': utilization_pct,
                    'over_budget': new_spent > budget['monthly_limit'],
                    'warning_threshold': utilization_pct > 80
                }
            else:
                return {
                    'has_budget': False,
                    'message': 'No budget set for this category'
                }
                
        except Exception as e:
            self.logger.error(f"Failed to calculate budget impact: {str(e)}")
            return {'has_budget': False, 'error': str(e)}
    
    def get_daily_spending(self, user_id: str) -> float:
        """Get user's daily spending total"""
        try:
            daily_key = f"daily_spending:{user_id}:{datetime.now().date()}"
            spending = self.redis_client.get(daily_key)
            return float(spending) if spending else 0.0
        except:
            return 0.0
    
    def get_weekly_spending(self, user_id: str) -> float:
        """Get user's weekly spending total"""
        try:
            week_start = datetime.now().date() - timedelta(days=datetime.now().weekday())
            weekly_key = f"weekly_spending:{user_id}:{week_start}"
            spending = self.redis_client.get(weekly_key)
            return float(spending) if spending else 0.0
        except:
            return 0.0
    
    def get_category_spending(self, user_id: str, category: str) -> float:
        """Get user's monthly category spending"""
        try:
            month_key = f"category_spending:{user_id}:{category}:{datetime.now().strftime('%Y-%m')}"
            spending = self.redis_client.get(month_key)
            return float(spending) if spending else 0.0
        except:
            return 0.0


# Task Functions
def stream_market_data(**context):
    """
    Stream and process real-time market data
    """
    try:
        processor = StreamingProcessor()
        producer = processor.create_kafka_producer()
        
        # Fetch real-time market data from APIs
        api_sources = [
            {'name': 'alpha_vantage', 'url': Variable.get('ALPHA_VANTAGE_REALTIME_URL')},
            {'name': 'polygon', 'url': Variable.get('POLYGON_REALTIME_URL')}
        ]
        
        processed_count = 0
        alerts_generated = 0
        
        for source in api_sources:
            try:
                # Simulate real-time data fetching
                # In production, this would connect to WebSocket streams
                market_data = {
                    'symbols': ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'SPY'],
                    'data': [
                        {
                            'symbol': 'AAPL',
                            'price': 150.25,
                            'volume': 1000000,
                            'bid': 150.24,
                            'ask': 150.26,
                            'change_pct': 1.2
                        }
                        # More data would be here
                    ]
                }
                
                for data_point in market_data['data']:
                    # Create market data event
                    event = MarketDataEvent(
                        symbol=data_point['symbol'],
                        price=data_point['price'],
                        volume=data_point['volume'],
                        timestamp=datetime.now(),
                        exchange='NASDAQ',
                        bid=data_point.get('bid'),
                        ask=data_point.get('ask'),
                        change_pct=data_point.get('change_pct'),
                        source=source['name']
                    )
                    
                    # Cache in Redis
                    processor.cache_market_data(event)
                    
                    # Detect alerts
                    alerts = processor.detect_price_alerts(event)
                    alerts_generated += len(alerts)
                    
                    # Publish to Kafka
                    producer.produce(
                        topic=STREAMING_CONFIG['topics']['market_data_processed'],
                        value=event.to_dict(),
                        key=event.symbol
                    )
                    
                    # Publish alerts if any
                    for alert in alerts:
                        producer.produce(
                            topic=STREAMING_CONFIG['topics']['alerts'],
                            value=alert,
                            key=f"alert_{event.symbol}"
                        )
                    
                    processed_count += 1
                
            except Exception as e:
                logging.error(f"Failed to process data from {source['name']}: {str(e)}")
                continue
        
        producer.flush()
        
        # Store metrics
        context['task_instance'].xcom_push(
            key='streaming_metrics',
            value={
                'processed_count': processed_count,
                'alerts_generated': alerts_generated,
                'execution_time': datetime.now().isoformat()
            }
        )
        
        logging.info(f"Processed {processed_count} market data points, generated {alerts_generated} alerts")
        
    except Exception as e:
        logging.error(f"Market data streaming failed: {str(e)}")
        raise


def stream_transaction_data(**context):
    """
    Stream and process real-time transaction data
    """
    try:
        processor = StreamingProcessor()
        
        # Consume transactions from Kafka (simulated)
        consumer = processor.create_kafka_consumer(
            [STREAMING_CONFIG['topics']['transactions_raw']],
            'transaction-processor-group'
        )
        
        processed_transactions = []
        high_risk_transactions = []
        
        # Process messages (with timeout for batch processing)
        start_time = datetime.now()
        timeout_seconds = 30  # Process for 30 seconds max
        
        while (datetime.now() - start_time).total_seconds() < timeout_seconds:
            msg = consumer.poll(timeout=1.0)
            if msg is None:
                continue
            
            if msg.error():
                logging.error(f"Consumer error: {msg.error()}")
                continue
            
            try:
                # Parse transaction data
                tx_data = msg.value()
                transaction = TransactionEvent(
                    user_id=tx_data['user_id'],
                    transaction_id=tx_data['transaction_id'],
                    amount=tx_data['amount'],
                    category=tx_data['category'],
                    merchant=tx_data['merchant'],
                    timestamp=datetime.fromisoformat(tx_data['timestamp']),
                    account_id=tx_data['account_id'],
                    is_debit=tx_data['is_debit'],
                    description=tx_data.get('description')
                )
                
                # Process transaction
                result = processor.process_transaction_stream(transaction)
                processed_transactions.append(result)
                
                # Check for high-risk transactions
                if result.get('fraud_score', 0) > 0.7:
                    high_risk_transactions.append(result)
                
                # Publish processed transaction
                producer = processor.create_kafka_producer()
                producer.produce(
                    topic=STREAMING_CONFIG['topics']['transactions_processed'],
                    value=result,
                    key=transaction.transaction_id
                )
                
            except Exception as e:
                logging.error(f"Failed to process transaction message: {str(e)}")
                continue
        
        consumer.close()
        
        # Store results
        context['task_instance'].xcom_push(
            key='transaction_metrics',
            value={
                'processed_count': len(processed_transactions),
                'high_risk_count': len(high_risk_transactions),
                'processing_time_seconds': timeout_seconds
            }
        )
        
        logging.info(f"Processed {len(processed_transactions)} transactions, {len(high_risk_transactions)} high-risk")
        
    except Exception as e:
        logging.error(f"Transaction streaming failed: {str(e)}")
        raise


def monitor_stream_health(**context):
    """
    Monitor streaming pipeline health and performance
    """
    try:
        processor = StreamingProcessor()
        
        # Check Kafka cluster health
        producer = processor.create_kafka_producer()
        
        # Test message production
        test_message = {
            'type': 'health_check',
            'timestamp': datetime.now().isoformat(),
            'source': 'airflow_monitor'
        }
        
        producer.produce(
            topic='health-check',
            value=test_message,
            key='health_check'
        )
        producer.flush()
        
        # Check Redis health
        redis_health = processor.redis_client.ping()
        
        # Check topic lag (simplified)
        topics_health = {
            topic: {'status': 'healthy', 'lag': 0} 
            for topic in STREAMING_CONFIG['topics'].values()
        }
        
        # Get streaming metrics from previous tasks
        streaming_metrics = context['task_instance'].xcom_pull(
            task_ids='stream_market_data',
            key='streaming_metrics'
        ) or {}
        
        transaction_metrics = context['task_instance'].xcom_pull(
            task_ids='stream_transaction_data', 
            key='transaction_metrics'
        ) or {}
        
        health_status = {
            'overall_status': 'healthy',
            'kafka_healthy': True,
            'redis_healthy': redis_health,
            'topics_status': topics_health,
            'streaming_metrics': streaming_metrics,
            'transaction_metrics': transaction_metrics,
            'check_timestamp': datetime.now().isoformat()
        }
        
        # Store health status
        context['task_instance'].xcom_push(key='stream_health', value=health_status)
        
        logging.info(f"Stream health check completed: {health_status['overall_status']}")
        
    except Exception as e:
        logging.error(f"Stream health monitoring failed: {str(e)}")
        # Don't raise - we want the pipeline to continue even if monitoring fails
        context['task_instance'].xcom_push(
            key='stream_health',
            value={'overall_status': 'unhealthy', 'error': str(e)}
        )


# Task Groups
with TaskGroup("stream_processing", dag=dag) as stream_processing_group:
    stream_market_task = PythonOperator(
        task_id='stream_market_data',
        python_callable=stream_market_data,
        doc_md="Stream and process real-time market data"
    )
    
    stream_transaction_task = PythonOperator(
        task_id='stream_transaction_data',
        python_callable=stream_transaction_data,
        doc_md="Stream and process real-time transaction data"
    )

# Individual tasks
health_monitor_task = PythonOperator(
    task_id='monitor_stream_health',
    python_callable=monitor_stream_health,
    doc_md="Monitor streaming pipeline health and performance",
    trigger_rule=TriggerRule.ALL_DONE
)

# Store metrics in database
store_metrics_task = PostgresOperator(
    task_id='store_streaming_metrics',
    postgres_conn_id='warehouse_postgres',
    sql="""
        INSERT INTO audit.streaming_metrics (
            execution_date, market_data_processed, transactions_processed,
            alerts_generated, high_risk_transactions, overall_status
        ) VALUES (
            CURRENT_TIMESTAMP,
            {{ ti.xcom_pull(task_ids='stream_processing.stream_market_data', key='streaming_metrics')['processed_count'] | default(0) }},
            {{ ti.xcom_pull(task_ids='stream_processing.stream_transaction_data', key='transaction_metrics')['processed_count'] | default(0) }},
            {{ ti.xcom_pull(task_ids='stream_processing.stream_market_data', key='streaming_metrics')['alerts_generated'] | default(0) }},
            {{ ti.xcom_pull(task_ids='stream_processing.stream_transaction_data', key='transaction_metrics')['high_risk_count'] | default(0) }},
            '{{ ti.xcom_pull(task_ids='monitor_stream_health', key='stream_health')['overall_status'] | default('unknown') }}'
        )
    """,
    doc_md="Store streaming metrics in audit database"
)

# Task Dependencies
stream_processing_group >> health_monitor_task >> store_metrics_task