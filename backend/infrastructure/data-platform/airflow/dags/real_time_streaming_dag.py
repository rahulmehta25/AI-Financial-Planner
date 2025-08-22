"""
Real-time Data Streaming DAG
Manages Kafka streams and real-time data processing
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.sensors.filesystem import FileSensor
from airflow.utils.dates import days_ago
from airflow.utils.task_group import TaskGroup

import logging
from kafka import KafkaProducer, KafkaConsumer
import json
import pandas as pd
from typing import Dict, List, Any


default_args = {
    'owner': 'data-engineering',
    'depends_on_past': False,
    'start_date': days_ago(1),
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=2),
    'catchup': False
}

dag = DAG(
    'real_time_streaming_pipeline',
    default_args=default_args,
    description='Real-time data streaming with Kafka',
    schedule_interval='@continuous',
    catchup=False,
    tags=['streaming', 'kafka', 'real-time']
)


def start_kafka_streams(**context):
    """
    Initialize and start Kafka streams for real-time processing
    """
    try:
        # Kafka configuration
        kafka_config = {
            'bootstrap_servers': ['localhost:9092'],
            'auto_offset_reset': 'earliest',
            'enable_auto_commit': True,
            'group_id': 'financial_streaming_group'
        }
        
        # Initialize producer for outbound streams
        producer = KafkaProducer(
            bootstrap_servers=kafka_config['bootstrap_servers'],
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            key_serializer=lambda k: k.encode('utf-8') if k else None
        )
        
        # Topics to monitor
        topics = [
            'market_data_real_time',
            'transaction_stream',
            'user_activity_stream',
            'risk_alerts'
        ]
        
        logging.info(f"Kafka streams started for topics: {topics}")
        
        context['task_instance'].xcom_push(key='kafka_topics', value=topics)
        return topics
        
    except Exception as e:
        logging.error(f"Failed to start Kafka streams: {str(e)}")
        raise


def process_market_data_stream(**context):
    """
    Process real-time market data stream
    """
    try:
        # Consumer for market data
        consumer = KafkaConsumer(
            'market_data_real_time',
            bootstrap_servers=['localhost:9092'],
            auto_offset_reset='latest',
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            consumer_timeout_ms=10000  # 10 second timeout for this DAG run
        )
        
        processed_messages = []
        
        for message in consumer:
            try:
                market_data = message.value
                
                # Real-time processing logic
                processed_data = {
                    'symbol': market_data.get('symbol'),
                    'price': float(market_data.get('price', 0)),
                    'volume': int(market_data.get('volume', 0)),
                    'timestamp': market_data.get('timestamp'),
                    'change_percent': calculate_price_change(market_data),
                    'volatility_indicator': calculate_volatility(market_data),
                    'processed_at': datetime.utcnow().isoformat()
                }
                
                processed_messages.append(processed_data)
                
                # Trigger alerts if necessary
                if abs(processed_data['change_percent']) > 5.0:
                    send_price_alert(processed_data)
                
            except Exception as e:
                logging.error(f"Error processing market data message: {str(e)}")
                continue
        
        consumer.close()
        
        logging.info(f"Processed {len(processed_messages)} market data messages")
        
        context['task_instance'].xcom_push(key='processed_market_data', value=processed_messages)
        return processed_messages
        
    except Exception as e:
        logging.error(f"Market data stream processing failed: {str(e)}")
        raise


def process_transaction_stream(**context):
    """
    Process real-time transaction stream
    """
    try:
        consumer = KafkaConsumer(
            'transaction_stream',
            bootstrap_servers=['localhost:9092'],
            auto_offset_reset='latest',
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            consumer_timeout_ms=10000
        )
        
        processed_transactions = []
        
        for message in consumer:
            try:
                transaction = message.value
                
                # Real-time transaction processing
                processed_transaction = {
                    'transaction_id': transaction.get('id'),
                    'user_id': transaction.get('user_id'),
                    'amount': float(transaction.get('amount', 0)),
                    'category': categorize_transaction(transaction),
                    'fraud_score': calculate_fraud_score(transaction),
                    'spending_pattern': analyze_spending_pattern(transaction),
                    'processed_at': datetime.utcnow().isoformat()
                }
                
                processed_transactions.append(processed_transaction)
                
                # Fraud detection
                if processed_transaction['fraud_score'] > 0.8:
                    send_fraud_alert(processed_transaction)
                
                # Budget alerts
                if check_budget_exceeded(processed_transaction):
                    send_budget_alert(processed_transaction)
                
            except Exception as e:
                logging.error(f"Error processing transaction: {str(e)}")
                continue
        
        consumer.close()
        
        logging.info(f"Processed {len(processed_transactions)} transactions")
        
        context['task_instance'].xcom_push(key='processed_transactions', value=processed_transactions)
        return processed_transactions
        
    except Exception as e:
        logging.error(f"Transaction stream processing failed: {str(e)}")
        raise


def real_time_analytics(**context):
    """
    Perform real-time analytics on streaming data
    """
    try:
        # Get processed data from previous tasks
        market_data = context['task_instance'].xcom_pull(
            task_ids='process_market_data_stream',
            key='processed_market_data'
        ) or []
        
        transactions = context['task_instance'].xcom_pull(
            task_ids='process_transaction_stream',
            key='processed_transactions'
        ) or []
        
        # Real-time analytics calculations
        analytics = {
            'market_analytics': {
                'total_symbols_processed': len(set(d['symbol'] for d in market_data)),
                'avg_price_change': calculate_average_change(market_data),
                'high_volatility_stocks': get_high_volatility_stocks(market_data),
                'market_sentiment': calculate_market_sentiment(market_data)
            },
            'transaction_analytics': {
                'total_transactions': len(transactions),
                'total_volume': sum(t['amount'] for t in transactions),
                'fraud_alerts': len([t for t in transactions if t['fraud_score'] > 0.8]),
                'top_categories': get_top_spending_categories(transactions)
            },
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Store analytics for dashboards
        store_real_time_analytics(analytics)
        
        logging.info(f"Real-time analytics completed: {analytics}")
        
        context['task_instance'].xcom_push(key='real_time_analytics', value=analytics)
        return analytics
        
    except Exception as e:
        logging.error(f"Real-time analytics failed: {str(e)}")
        raise


def stream_to_warehouse(**context):
    """
    Stream processed data to data warehouse
    """
    try:
        # Get all processed data
        market_data = context['task_instance'].xcom_pull(
            task_ids='process_market_data_stream',
            key='processed_market_data'
        ) or []
        
        transactions = context['task_instance'].xcom_pull(
            task_ids='process_transaction_stream',
            key='processed_transactions'
        ) or []
        
        # Stream to warehouse tables
        if market_data:
            stream_to_table('real_time_market_data', market_data)
            
        if transactions:
            stream_to_table('real_time_transactions', transactions)
        
        logging.info("Data streaming to warehouse completed")
        return True
        
    except Exception as e:
        logging.error(f"Streaming to warehouse failed: {str(e)}")
        raise


# Helper functions
def calculate_price_change(market_data: Dict) -> float:
    """Calculate price change percentage"""
    try:
        current_price = float(market_data.get('price', 0))
        previous_price = float(market_data.get('previous_price', current_price))
        
        if previous_price == 0:
            return 0.0
            
        return ((current_price - previous_price) / previous_price) * 100
    except:
        return 0.0


def calculate_volatility(market_data: Dict) -> str:
    """Calculate volatility indicator"""
    try:
        price_change = abs(calculate_price_change(market_data))
        
        if price_change > 10:
            return 'HIGH'
        elif price_change > 5:
            return 'MEDIUM'
        else:
            return 'LOW'
    except:
        return 'UNKNOWN'


def categorize_transaction(transaction: Dict) -> str:
    """Categorize transaction based on merchant/description"""
    # Simplified categorization logic
    description = transaction.get('description', '').lower()
    
    if any(word in description for word in ['grocery', 'supermarket', 'food']):
        return 'Food & Dining'
    elif any(word in description for word in ['gas', 'fuel', 'exxon', 'shell']):
        return 'Transportation'
    elif any(word in description for word in ['amazon', 'walmart', 'target']):
        return 'Shopping'
    else:
        return 'Other'


def calculate_fraud_score(transaction: Dict) -> float:
    """Calculate fraud probability score"""
    score = 0.0
    
    # Amount-based scoring
    amount = float(transaction.get('amount', 0))
    if amount > 1000:
        score += 0.3
    elif amount > 5000:
        score += 0.5
    
    # Time-based scoring (unusual hours)
    # Add time-based logic here
    
    # Location-based scoring
    # Add location-based logic here
    
    return min(score, 1.0)


def analyze_spending_pattern(transaction: Dict) -> str:
    """Analyze spending pattern"""
    # Simplified pattern analysis
    amount = float(transaction.get('amount', 0))
    
    if amount > 1000:
        return 'HIGH_SPENDING'
    elif amount < 10:
        return 'MICRO_TRANSACTION'
    else:
        return 'NORMAL'


def send_price_alert(data: Dict):
    """Send price change alert"""
    logging.info(f"PRICE ALERT: {data['symbol']} changed by {data['change_percent']}%")


def send_fraud_alert(transaction: Dict):
    """Send fraud alert"""
    logging.warning(f"FRAUD ALERT: Transaction {transaction['transaction_id']} has fraud score {transaction['fraud_score']}")


def send_budget_alert(transaction: Dict):
    """Send budget exceeded alert"""
    logging.info(f"BUDGET ALERT: User {transaction['user_id']} may have exceeded budget")


def check_budget_exceeded(transaction: Dict) -> bool:
    """Check if transaction exceeds budget"""
    # Simplified budget check
    return float(transaction.get('amount', 0)) > 500


def calculate_average_change(market_data: List[Dict]) -> float:
    """Calculate average price change"""
    if not market_data:
        return 0.0
    
    changes = [d['change_percent'] for d in market_data]
    return sum(changes) / len(changes)


def get_high_volatility_stocks(market_data: List[Dict]) -> List[str]:
    """Get list of high volatility stocks"""
    return [d['symbol'] for d in market_data if d['volatility_indicator'] == 'HIGH']


def calculate_market_sentiment(market_data: List[Dict]) -> str:
    """Calculate overall market sentiment"""
    if not market_data:
        return 'NEUTRAL'
    
    positive_changes = sum(1 for d in market_data if d['change_percent'] > 0)
    total_changes = len(market_data)
    
    if positive_changes / total_changes > 0.6:
        return 'POSITIVE'
    elif positive_changes / total_changes < 0.4:
        return 'NEGATIVE'
    else:
        return 'NEUTRAL'


def get_top_spending_categories(transactions: List[Dict]) -> List[Dict]:
    """Get top spending categories"""
    category_totals = {}
    
    for transaction in transactions:
        category = transaction['category']
        amount = transaction['amount']
        
        if category in category_totals:
            category_totals[category] += amount
        else:
            category_totals[category] = amount
    
    sorted_categories = sorted(category_totals.items(), key=lambda x: x[1], reverse=True)
    return [{'category': cat, 'amount': amount} for cat, amount in sorted_categories[:5]]


def store_real_time_analytics(analytics: Dict):
    """Store analytics in cache/database"""
    # In production, this would store in Redis or database
    logging.info(f"Storing real-time analytics: {analytics}")


def stream_to_table(table_name: str, data: List[Dict]):
    """Stream data to warehouse table"""
    # In production, this would use proper streaming insert
    logging.info(f"Streaming {len(data)} records to {table_name}")


# Task Definitions
start_streams_task = PythonOperator(
    task_id='start_kafka_streams',
    python_callable=start_kafka_streams,
    dag=dag
)

with TaskGroup("stream_processing", dag=dag) as processing_group:
    process_market_task = PythonOperator(
        task_id='process_market_data_stream',
        python_callable=process_market_data_stream
    )
    
    process_transaction_task = PythonOperator(
        task_id='process_transaction_stream',
        python_callable=process_transaction_stream
    )

analytics_task = PythonOperator(
    task_id='real_time_analytics',
    python_callable=real_time_analytics,
    dag=dag
)

stream_warehouse_task = PythonOperator(
    task_id='stream_to_warehouse',
    python_callable=stream_to_warehouse,
    dag=dag
)

# Task Dependencies
start_streams_task >> processing_group >> analytics_task >> stream_warehouse_task