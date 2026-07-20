"""
Advanced Financial Stream Processor using Kafka Streams
Real-time processing of financial data with complex event processing
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from decimal import Decimal
import asyncio
import numpy as np
import pandas as pd
from statistics import mean, stdev

from kafka import KafkaProducer, KafkaConsumer
from kafka.errors import KafkaError
from confluent_kafka.avro import AvroProducer, AvroConsumer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka import avro
import redis
from sqlalchemy import create_engine
import psycopg2
from psycopg2.extras import RealDictCursor

# Avro Schemas
MARKET_DATA_SCHEMA = """
{
  "type": "record",
  "name": "MarketData",
  "fields": [
    {"name": "symbol", "type": "string"},
    {"name": "price", "type": "double"},
    {"name": "volume", "type": "long"},
    {"name": "timestamp", "type": "long"},
    {"name": "exchange", "type": "string"},
    {"name": "bid", "type": ["null", "double"], "default": null},
    {"name": "ask", "type": ["null", "double"], "default": null},
    {"name": "change_pct", "type": ["null", "double"], "default": null},
    {"name": "source", "type": "string"}
  ]
}
"""

TRANSACTION_SCHEMA = """
{
  "type": "record",
  "name": "Transaction",
  "fields": [
    {"name": "transaction_id", "type": "string"},
    {"name": "user_id", "type": "string"},
    {"name": "account_id", "type": "string"},
    {"name": "amount", "type": "double"},
    {"name": "category", "type": "string"},
    {"name": "merchant", "type": "string"},
    {"name": "timestamp", "type": "long"},
    {"name": "is_debit", "type": "boolean"},
    {"name": "description", "type": ["null", "string"], "default": null},
    {"name": "location", "type": ["null", "string"], "default": null}
  ]
}
"""

ALERT_SCHEMA = """
{
  "type": "record",
  "name": "FinancialAlert",
  "fields": [
    {"name": "alert_id", "type": "string"},
    {"name": "alert_type", "type": "string"},
    {"name": "user_id", "type": ["null", "string"], "default": null},
    {"name": "symbol", "type": ["null", "string"], "default": null},
    {"name": "severity", "type": {"type": "enum", "name": "Severity", "symbols": ["LOW", "MEDIUM", "HIGH", "CRITICAL"]}},
    {"name": "message", "type": "string"},
    {"name": "timestamp", "type": "long"},
    {"name": "metadata", "type": {"type": "map", "values": "string"}}
  ]
}
"""

@dataclass
class ProcessingMetrics:
    processed_count: int = 0
    error_count: int = 0
    latency_ms: List[float] = None
    throughput_per_second: float = 0.0
    last_processed_timestamp: Optional[datetime] = None
    
    def __post_init__(self):
        if self.latency_ms is None:
            self.latency_ms = []

class AdvancedStreamProcessor:
    """
    Advanced stream processor for financial data with complex event processing
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize connections
        self.setup_kafka_clients()
        self.setup_redis_client()
        self.setup_database_connection()
        
        # Processing state
        self.metrics = ProcessingMetrics()
        self.running = False
        
        # Event detection windows
        self.price_windows = {}  # symbol -> list of (timestamp, price)
        self.transaction_windows = {}  # user_id -> list of transactions
        
        # Pattern detection
        self.pattern_detectors = {
            'price_anomaly': self.detect_price_anomaly,
            'volume_spike': self.detect_volume_spike,
            'rapid_trading': self.detect_rapid_trading,
            'spending_pattern': self.detect_spending_pattern,
            'fraud_pattern': self.detect_fraud_pattern
        }
    
    def setup_kafka_clients(self):
        """Initialize Kafka producers and consumers with Avro support"""
        # Schema Registry
        self.schema_registry = SchemaRegistryClient({
            'url': self.config['schema_registry_url']
        })
        
        # Parse Avro schemas
        self.market_data_schema = avro.loads(MARKET_DATA_SCHEMA)
        self.transaction_schema = avro.loads(TRANSACTION_SCHEMA)
        self.alert_schema = avro.loads(ALERT_SCHEMA)
        
        # Producer for processed events and alerts
        producer_config = {
            'bootstrap.servers': self.config['bootstrap_servers'],
            'schema.registry.url': self.config['schema_registry_url'],
            'acks': 'all',
            'retries': 3,
            'enable.idempotence': True,
            'compression.type': 'snappy',
            'linger.ms': 5,  # Batch messages for better throughput
            'batch.size': 16384
        }
        
        self.producer = AvroProducer(producer_config)
        
        # Consumers for input streams
        consumer_config = {
            'bootstrap.servers': self.config['bootstrap_servers'],
            'schema.registry.url': self.config['schema_registry_url'],
            'group.id': self.config.get('consumer_group', 'financial-stream-processor'),
            'auto.offset.reset': 'earliest',
            'enable.auto.commit': True,
            'max.poll.interval.ms': 300000,
            'session.timeout.ms': 30000
        }
        
        self.market_consumer = AvroConsumer(consumer_config)
        self.transaction_consumer = AvroConsumer(consumer_config)
        
        # Subscribe to topics
        self.market_consumer.subscribe([self.config['topics']['market_data']])
        self.transaction_consumer.subscribe([self.config['topics']['transactions']])
    
    def setup_redis_client(self):
        """Initialize Redis client for caching and windowing"""
        self.redis_client = redis.Redis(
            host=self.config['redis']['host'],
            port=self.config['redis']['port'],
            db=self.config['redis']['db'],
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5
        )
    
    def setup_database_connection(self):
        """Initialize database connection for lookups"""
        self.db_config = self.config['database']
        self.engine = create_engine(
            f"postgresql://{self.db_config['user']}:{self.db_config['password']}"
            f"@{self.db_config['host']}:{self.db_config['port']}/{self.db_config['database']}"
        )
    
    async def start_processing(self):
        """Start the stream processing pipeline"""
        self.running = True
        self.logger.info("Starting advanced financial stream processor...")
        
        # Start multiple processing tasks concurrently
        tasks = [
            asyncio.create_task(self.process_market_data_stream()),
            asyncio.create_task(self.process_transaction_stream()),
            asyncio.create_task(self.pattern_detection_loop()),
            asyncio.create_task(self.metrics_reporter_loop())
        ]
        
        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            self.logger.error(f"Stream processing error: {str(e)}")
        finally:
            self.running = False
            self.cleanup()
    
    async def process_market_data_stream(self):
        """Process market data stream with real-time analytics"""
        self.logger.info("Starting market data stream processing...")
        
        while self.running:
            try:
                # Poll for messages with timeout
                msg = self.market_consumer.poll(timeout=1.0)
                
                if msg is None:
                    continue
                    
                if msg.error():
                    self.logger.error(f"Consumer error: {msg.error()}")
                    continue
                
                start_time = datetime.now()
                
                # Parse message
                market_data = msg.value()
                symbol = market_data['symbol']
                price = market_data['price']
                volume = market_data['volume']
                timestamp = datetime.fromtimestamp(market_data['timestamp'] / 1000)
                
                # Update price windows for pattern detection
                self.update_price_window(symbol, timestamp, price, volume)
                
                # Real-time calculations
                analytics = await self.calculate_market_analytics(market_data)
                
                # Detect patterns and anomalies
                alerts = await self.detect_market_patterns(market_data, analytics)
                
                # Update cache with latest data
                await self.cache_market_data(market_data, analytics)
                
                # Publish processed data
                processed_data = {
                    **market_data,
                    'analytics': analytics,
                    'processing_timestamp': int(datetime.now().timestamp() * 1000)
                }
                
                self.producer.produce(
                    topic=self.config['topics']['market_data_processed'],
                    key=symbol,
                    value=processed_data
                )
                
                # Publish alerts
                for alert in alerts:
                    await self.publish_alert(alert)
                
                # Update metrics
                processing_time = (datetime.now() - start_time).total_seconds() * 1000
                self.update_processing_metrics(processing_time)
                
            except Exception as e:
                self.logger.error(f"Error processing market data: {str(e)}")
                self.metrics.error_count += 1
                await asyncio.sleep(0.1)
    
    async def process_transaction_stream(self):
        """Process transaction stream with fraud detection and analytics"""
        self.logger.info("Starting transaction stream processing...")
        
        while self.running:
            try:
                msg = self.transaction_consumer.poll(timeout=1.0)
                
                if msg is None:
                    continue
                    
                if msg.error():
                    self.logger.error(f"Consumer error: {msg.error()}")
                    continue
                
                start_time = datetime.now()
                
                # Parse transaction
                transaction = msg.value()
                user_id = transaction['user_id']
                
                # Update transaction windows
                self.update_transaction_window(user_id, transaction)
                
                # Real-time fraud detection
                fraud_score = await self.calculate_fraud_score(transaction)
                
                # Spending pattern analysis
                spending_analysis = await self.analyze_spending_patterns(transaction)
                
                # Budget impact calculation
                budget_impact = await self.calculate_budget_impact(transaction)
                
                # User behavior scoring
                behavior_score = await self.calculate_behavior_score(user_id, transaction)
                
                # Detect transaction patterns
                alerts = await self.detect_transaction_patterns(transaction, {
                    'fraud_score': fraud_score,
                    'spending_analysis': spending_analysis,
                    'budget_impact': budget_impact,
                    'behavior_score': behavior_score
                })
                
                # Update user state in cache
                await self.update_user_state(user_id, transaction, {
                    'fraud_score': fraud_score,
                    'behavior_score': behavior_score
                })
                
                # Publish processed transaction
                processed_transaction = {
                    **transaction,
                    'fraud_score': fraud_score,
                    'spending_analysis': spending_analysis,
                    'budget_impact': budget_impact,
                    'behavior_score': behavior_score,
                    'processing_timestamp': int(datetime.now().timestamp() * 1000)
                }
                
                self.producer.produce(
                    topic=self.config['topics']['transactions_processed'],
                    key=transaction['transaction_id'],
                    value=processed_transaction
                )
                
                # Publish alerts
                for alert in alerts:
                    await self.publish_alert(alert)
                
                # Update metrics
                processing_time = (datetime.now() - start_time).total_seconds() * 1000
                self.update_processing_metrics(processing_time)
                
            except Exception as e:
                self.logger.error(f"Error processing transaction: {str(e)}")
                self.metrics.error_count += 1
                await asyncio.sleep(0.1)
    
    def update_price_window(self, symbol: str, timestamp: datetime, price: float, volume: int):
        """Update sliding window for price data"""
        if symbol not in self.price_windows:
            self.price_windows[symbol] = []
        
        self.price_windows[symbol].append((timestamp, price, volume))
        
        # Keep only last 100 data points (or 5 minutes of data)
        cutoff_time = timestamp - timedelta(minutes=5)
        self.price_windows[symbol] = [
            (ts, p, v) for ts, p, v in self.price_windows[symbol]
            if ts >= cutoff_time
        ][-100:]  # Also limit by count
    
    def update_transaction_window(self, user_id: str, transaction: Dict):
        """Update sliding window for user transactions"""
        if user_id not in self.transaction_windows:
            self.transaction_windows[user_id] = []
        
        transaction_time = datetime.fromtimestamp(transaction['timestamp'] / 1000)
        self.transaction_windows[user_id].append((transaction_time, transaction))
        
        # Keep only last hour of transactions
        cutoff_time = transaction_time - timedelta(hours=1)
        self.transaction_windows[user_id] = [
            (ts, tx) for ts, tx in self.transaction_windows[user_id]
            if ts >= cutoff_time
        ]
    
    async def calculate_market_analytics(self, market_data: Dict) -> Dict[str, Any]:
        """Calculate real-time market analytics"""
        symbol = market_data['symbol']
        current_price = market_data['price']
        current_volume = market_data['volume']
        
        analytics = {
            'current_price': current_price,
            'current_volume': current_volume,
        }
        
        # Get historical data from window
        if symbol in self.price_windows and len(self.price_windows[symbol]) > 1:
            window_data = self.price_windows[symbol]
            prices = [p for _, p, _ in window_data]
            volumes = [v for _, _, v in window_data]
            
            # Price analytics
            analytics.update({
                'price_change': current_price - prices[-2] if len(prices) > 1 else 0,
                'price_change_pct': ((current_price - prices[-2]) / prices[-2] * 100) if len(prices) > 1 and prices[-2] > 0 else 0,
                'moving_avg_5': mean(prices[-5:]) if len(prices) >= 5 else current_price,
                'moving_avg_20': mean(prices[-20:]) if len(prices) >= 20 else current_price,
                'price_volatility': stdev(prices) if len(prices) > 1 else 0,
                'volume_avg': mean(volumes) if volumes else current_volume,
                'volume_spike_ratio': current_volume / mean(volumes) if volumes and mean(volumes) > 0 else 1.0
            })
            
            # Technical indicators
            if len(prices) >= 20:
                # RSI calculation (simplified)
                price_changes = [prices[i] - prices[i-1] for i in range(1, len(prices))]
                gains = [change for change in price_changes if change > 0]
                losses = [-change for change in price_changes if change < 0]
                
                avg_gain = mean(gains[-14:]) if len(gains) >= 14 else 0
                avg_loss = mean(losses[-14:]) if len(losses) >= 14 else 0.01  # Avoid division by zero
                
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))
                analytics['rsi'] = rsi
                
                # Bollinger Bands
                ma_20 = analytics['moving_avg_20']
                std_20 = stdev(prices[-20:])
                analytics.update({
                    'bollinger_upper': ma_20 + (2 * std_20),
                    'bollinger_lower': ma_20 - (2 * std_20)
                })
        
        # Get additional analytics from cache
        cached_analytics = self.redis_client.hgetall(f"analytics:{symbol}")
        if cached_analytics:
            analytics.update({
                'daily_high': float(cached_analytics.get('daily_high', current_price)),
                'daily_low': float(cached_analytics.get('daily_low', current_price)),
                'daily_volume': int(cached_analytics.get('daily_volume', current_volume))
            })
        
        return analytics
    
    async def detect_market_patterns(self, market_data: Dict, analytics: Dict) -> List[Dict]:
        """Detect market patterns and generate alerts"""
        alerts = []
        symbol = market_data['symbol']
        
        # Price anomaly detection
        if analytics.get('price_volatility', 0) > 0:
            volatility_threshold = 3 * analytics['price_volatility']
            price_change = abs(analytics.get('price_change', 0))
            
            if price_change > volatility_threshold:
                alerts.append({
                    'alert_type': 'price_anomaly',
                    'symbol': symbol,
                    'severity': 'HIGH' if price_change > 5 * analytics['price_volatility'] else 'MEDIUM',
                    'message': f'{symbol} price anomaly detected: {price_change:.2f} change (volatility: {analytics["price_volatility"]:.2f})',
                    'metadata': {
                        'price_change': str(price_change),
                        'volatility': str(analytics['price_volatility']),
                        'current_price': str(market_data['price'])
                    }
                })
        
        # Volume spike detection
        volume_spike_ratio = analytics.get('volume_spike_ratio', 1.0)
        if volume_spike_ratio > 3.0:  # 300% of average volume
            alerts.append({
                'alert_type': 'volume_spike',
                'symbol': symbol,
                'severity': 'HIGH' if volume_spike_ratio > 5.0 else 'MEDIUM',
                'message': f'{symbol} volume spike: {volume_spike_ratio:.2f}x average volume',
                'metadata': {
                    'volume_spike_ratio': str(volume_spike_ratio),
                    'current_volume': str(market_data['volume']),
                    'average_volume': str(analytics.get('volume_avg', 0))
                }
            })
        
        # RSI overbought/oversold
        rsi = analytics.get('rsi')
        if rsi is not None:
            if rsi > 80:
                alerts.append({
                    'alert_type': 'rsi_overbought',
                    'symbol': symbol,
                    'severity': 'MEDIUM',
                    'message': f'{symbol} RSI indicates overbought condition: {rsi:.2f}',
                    'metadata': {'rsi': str(rsi)}
                })
            elif rsi < 20:
                alerts.append({
                    'alert_type': 'rsi_oversold',
                    'symbol': symbol,
                    'severity': 'MEDIUM',
                    'message': f'{symbol} RSI indicates oversold condition: {rsi:.2f}',
                    'metadata': {'rsi': str(rsi)}
                })
        
        # Bollinger Band breakout
        current_price = market_data['price']
        if 'bollinger_upper' in analytics and 'bollinger_lower' in analytics:
            if current_price > analytics['bollinger_upper']:
                alerts.append({
                    'alert_type': 'bollinger_breakout_up',
                    'symbol': symbol,
                    'severity': 'MEDIUM',
                    'message': f'{symbol} broke above upper Bollinger Band',
                    'metadata': {
                        'current_price': str(current_price),
                        'bollinger_upper': str(analytics['bollinger_upper'])
                    }
                })
            elif current_price < analytics['bollinger_lower']:
                alerts.append({
                    'alert_type': 'bollinger_breakout_down',
                    'symbol': symbol,
                    'severity': 'MEDIUM',
                    'message': f'{symbol} broke below lower Bollinger Band',
                    'metadata': {
                        'current_price': str(current_price),
                        'bollinger_lower': str(analytics['bollinger_lower'])
                    }
                })
        
        return alerts
    
    async def calculate_fraud_score(self, transaction: Dict) -> float:
        """Calculate fraud risk score for transaction"""
        user_id = transaction['user_id']
        amount = transaction['amount']
        timestamp = datetime.fromtimestamp(transaction['timestamp'] / 1000)
        
        fraud_score = 0.0
        
        # Amount-based scoring
        user_avg_key = f"user_avg_amount:{user_id}"
        avg_amount = self.redis_client.get(user_avg_key)
        if avg_amount:
            avg_amount = float(avg_amount)
            if amount > avg_amount * 10:  # 10x average
                fraud_score += 0.4
            elif amount > avg_amount * 5:  # 5x average
                fraud_score += 0.2
        
        # Frequency-based scoring
        if user_id in self.transaction_windows:
            recent_transactions = [
                tx for ts, tx in self.transaction_windows[user_id]
                if (timestamp - ts).total_seconds() < 300  # Last 5 minutes
            ]
            
            if len(recent_transactions) > 5:
                fraud_score += 0.3
            elif len(recent_transactions) > 3:
                fraud_score += 0.15
        
        # Time-based scoring (unusual hours)
        if timestamp.hour < 6 or timestamp.hour > 22:
            fraud_score += 0.1
        
        # Merchant-based scoring
        merchant = transaction.get('merchant', '')
        user_merchants_key = f"user_merchants:{user_id}"
        known_merchants = self.redis_client.smembers(user_merchants_key)
        if merchant and merchant not in known_merchants:
            fraud_score += 0.15
            # Add to known merchants for future reference
            self.redis_client.sadd(user_merchants_key, merchant)
            self.redis_client.expire(user_merchants_key, 30 * 24 * 3600)  # 30 days
        
        # Location-based scoring (if available)
        location = transaction.get('location')
        if location:
            user_locations_key = f"user_locations:{user_id}"
            known_locations = self.redis_client.smembers(user_locations_key)
            if location not in known_locations:
                fraud_score += 0.1
                self.redis_client.sadd(user_locations_key, location)
                self.redis_client.expire(user_locations_key, 30 * 24 * 3600)
        
        return min(fraud_score, 1.0)  # Cap at 1.0
    
    async def analyze_spending_patterns(self, transaction: Dict) -> Dict[str, Any]:
        """Analyze spending patterns for insights"""
        user_id = transaction['user_id']
        amount = transaction['amount']
        category = transaction['category']
        timestamp = datetime.fromtimestamp(transaction['timestamp'] / 1000)
        
        # Get daily spending
        daily_key = f"daily_spending:{user_id}:{timestamp.date()}"
        daily_spending = float(self.redis_client.get(daily_key) or 0) + amount
        self.redis_client.setex(daily_key, 86400, daily_spending)  # 24 hours
        
        # Get weekly spending
        week_start = timestamp.date() - timedelta(days=timestamp.weekday())
        weekly_key = f"weekly_spending:{user_id}:{week_start}"
        weekly_spending = float(self.redis_client.get(weekly_key) or 0) + amount
        self.redis_client.setex(weekly_key, 7 * 86400, weekly_spending)
        
        # Get monthly category spending
        month_key = f"category_spending:{user_id}:{category}:{timestamp.strftime('%Y-%m')}"
        category_spending = float(self.redis_client.get(month_key) or 0) + amount
        self.redis_client.setex(month_key, 31 * 86400, category_spending)
        
        return {
            'daily_spending': daily_spending,
            'weekly_spending': weekly_spending,
            'category_spending': category_spending,
            'is_weekend': timestamp.weekday() >= 5,
            'is_business_hours': 9 <= timestamp.hour <= 17,
            'spending_velocity': len(self.transaction_windows.get(user_id, [])),
            'category_trend': 'high' if category_spending > 1000 else 'normal'
        }
    
    async def calculate_budget_impact(self, transaction: Dict) -> Dict[str, Any]:
        """Calculate transaction impact on user budgets"""
        user_id = transaction['user_id']
        category = transaction['category']
        amount = transaction['amount']
        timestamp = datetime.fromtimestamp(transaction['timestamp'] / 1000)
        
        try:
            # Query user budget from database
            query = """
                SELECT monthly_limit, spent_amount 
                FROM user_budgets 
                WHERE user_id = %s AND category = %s 
                AND EXTRACT(YEAR FROM created_date) = %s 
                AND EXTRACT(MONTH FROM created_date) = %s
            """
            
            with self.engine.connect() as conn:
                result = conn.execute(query, (
                    user_id, category, timestamp.year, timestamp.month
                )).fetchone()
            
            if result:
                monthly_limit = result[0]
                current_spent = result[1] + amount
                remaining = monthly_limit - current_spent
                utilization = (current_spent / monthly_limit) * 100
                
                return {
                    'has_budget': True,
                    'monthly_limit': monthly_limit,
                    'current_spent': current_spent,
                    'remaining': remaining,
                    'utilization_percent': utilization,
                    'over_budget': current_spent > monthly_limit,
                    'approaching_limit': utilization > 80
                }
            else:
                return {'has_budget': False}
                
        except Exception as e:
            self.logger.error(f"Error calculating budget impact: {str(e)}")
            return {'has_budget': False, 'error': str(e)}
    
    async def calculate_behavior_score(self, user_id: str, transaction: Dict) -> float:
        """Calculate user behavior score based on transaction patterns"""
        score = 0.5  # Start with neutral score
        
        # Consistency scoring
        if user_id in self.transaction_windows:
            transactions = [tx for _, tx in self.transaction_windows[user_id]]
            if len(transactions) > 5:
                amounts = [tx['amount'] for tx in transactions]
                avg_amount = mean(amounts)
                amount_std = stdev(amounts) if len(amounts) > 1 else 0
                
                # Consistent spending patterns get higher scores
                if amount_std < avg_amount * 0.5:  # Low variability
                    score += 0.2
                
                # Regular spending intervals
                timestamps = [datetime.fromtimestamp(tx['timestamp'] / 1000) for tx in transactions]
                if len(timestamps) > 2:
                    intervals = [(timestamps[i] - timestamps[i-1]).total_seconds() for i in range(1, len(timestamps))]
                    avg_interval = mean(intervals)
                    interval_std = stdev(intervals) if len(intervals) > 1 else 0
                    
                    if interval_std < avg_interval * 0.3:  # Regular intervals
                        score += 0.15
        
        # Category diversity (healthy financial behavior)
        user_categories_key = f"user_categories:{user_id}"
        category_count = self.redis_client.scard(user_categories_key)
        if category_count > 5:
            score += 0.1
        
        return min(score, 1.0)
    
    async def detect_transaction_patterns(self, transaction: Dict, analytics: Dict) -> List[Dict]:
        """Detect patterns in transaction data"""
        alerts = []
        user_id = transaction['user_id']
        
        # High fraud score alert
        fraud_score = analytics.get('fraud_score', 0)
        if fraud_score > 0.7:
            alerts.append({
                'alert_type': 'high_fraud_risk',
                'user_id': user_id,
                'severity': 'CRITICAL' if fraud_score > 0.9 else 'HIGH',
                'message': f'High fraud risk transaction detected (score: {fraud_score:.2f})',
                'metadata': {
                    'fraud_score': str(fraud_score),
                    'transaction_id': transaction['transaction_id'],
                    'amount': str(transaction['amount'])
                }
            })
        
        # Budget exceeded alert
        budget_impact = analytics.get('budget_impact', {})
        if budget_impact.get('over_budget'):
            alerts.append({
                'alert_type': 'budget_exceeded',
                'user_id': user_id,
                'severity': 'HIGH',
                'message': f'Budget exceeded for category {transaction["category"]}',
                'metadata': {
                    'category': transaction['category'],
                    'monthly_limit': str(budget_impact.get('monthly_limit', 0)),
                    'current_spent': str(budget_impact.get('current_spent', 0))
                }
            })
        elif budget_impact.get('approaching_limit'):
            alerts.append({
                'alert_type': 'budget_warning',
                'user_id': user_id,
                'severity': 'MEDIUM',
                'message': f'Approaching budget limit for category {transaction["category"]}',
                'metadata': {
                    'category': transaction['category'],
                    'utilization_percent': str(budget_impact.get('utilization_percent', 0))
                }
            })
        
        # Rapid spending alert
        spending_analysis = analytics.get('spending_analysis', {})
        if spending_analysis.get('spending_velocity', 0) > 10:  # More than 10 transactions in last hour
            alerts.append({
                'alert_type': 'rapid_spending',
                'user_id': user_id,
                'severity': 'MEDIUM',
                'message': 'Rapid spending pattern detected',
                'metadata': {
                    'transaction_count': str(spending_analysis['spending_velocity']),
                    'time_window': '1 hour'
                }
            })
        
        return alerts
    
    async def cache_market_data(self, market_data: Dict, analytics: Dict):
        """Cache market data and analytics in Redis"""
        symbol = market_data['symbol']
        timestamp = datetime.fromtimestamp(market_data['timestamp'] / 1000)
        
        # Cache latest price and analytics
        market_key = f"market:{symbol}"
        self.redis_client.hmset(market_key, {
            'price': market_data['price'],
            'volume': market_data['volume'],
            'timestamp': market_data['timestamp'],
            'change_pct': analytics.get('price_change_pct', 0),
            'volatility': analytics.get('price_volatility', 0),
            'rsi': analytics.get('rsi', 50)
        })
        self.redis_client.expire(market_key, 3600)  # 1 hour
        
        # Update daily high/low
        daily_key = f"daily_stats:{symbol}:{timestamp.date()}"
        current_high = self.redis_client.hget(daily_key, 'high')
        current_low = self.redis_client.hget(daily_key, 'low')
        
        price = market_data['price']
        if not current_high or price > float(current_high):
            self.redis_client.hset(daily_key, 'high', price)
        if not current_low or price < float(current_low):
            self.redis_client.hset(daily_key, 'low', price)
        
        self.redis_client.expire(daily_key, 86400)  # 24 hours
    
    async def update_user_state(self, user_id: str, transaction: Dict, analytics: Dict):
        """Update user state in cache"""
        user_key = f"user_state:{user_id}"
        
        # Update user transaction stats
        self.redis_client.hmset(user_key, {
            'last_transaction_id': transaction['transaction_id'],
            'last_amount': transaction['amount'],
            'last_timestamp': transaction['timestamp'],
            'fraud_score': analytics.get('fraud_score', 0),
            'behavior_score': analytics.get('behavior_score', 0.5),
            'last_merchant': transaction.get('merchant', '')
        })
        self.redis_client.expire(user_key, 86400)  # 24 hours
        
        # Update running averages
        avg_key = f"user_avg_amount:{user_id}"
        current_avg = self.redis_client.get(avg_key)
        if current_avg:
            # Simple exponential moving average
            new_avg = 0.9 * float(current_avg) + 0.1 * transaction['amount']
        else:
            new_avg = transaction['amount']
        
        self.redis_client.setex(avg_key, 7 * 86400, new_avg)  # 7 days
    
    async def publish_alert(self, alert_data: Dict):
        """Publish alert to Kafka topic"""
        alert = {
            'alert_id': f"alert_{datetime.now().timestamp()}",
            'alert_type': alert_data['alert_type'],
            'user_id': alert_data.get('user_id'),
            'symbol': alert_data.get('symbol'),
            'severity': alert_data['severity'],
            'message': alert_data['message'],
            'timestamp': int(datetime.now().timestamp() * 1000),
            'metadata': alert_data.get('metadata', {})
        }
        
        self.producer.produce(
            topic=self.config['topics']['alerts'],
            key=alert['alert_id'],
            value=alert
        )
    
    async def pattern_detection_loop(self):
        """Continuous pattern detection on cached data"""
        while self.running:
            try:
                # Run pattern detection on accumulated data
                await self.detect_cross_stream_patterns()
                await asyncio.sleep(10)  # Run every 10 seconds
                
            except Exception as e:
                self.logger.error(f"Pattern detection error: {str(e)}")
                await asyncio.sleep(5)
    
    async def detect_cross_stream_patterns(self):
        """Detect patterns across different data streams"""
        # Market correlation with user behavior
        # Portfolio rebalancing triggers
        # Mass market events affecting user spending
        # This would contain sophisticated cross-stream analysis
        pass
    
    async def metrics_reporter_loop(self):
        """Report processing metrics"""
        while self.running:
            try:
                # Calculate throughput
                if self.metrics.latency_ms:
                    avg_latency = mean(self.metrics.latency_ms)
                    p95_latency = np.percentile(self.metrics.latency_ms, 95)
                    
                    self.logger.info(
                        f"Processing metrics - "
                        f"Processed: {self.metrics.processed_count}, "
                        f"Errors: {self.metrics.error_count}, "
                        f"Avg Latency: {avg_latency:.2f}ms, "
                        f"P95 Latency: {p95_latency:.2f}ms, "
                        f"Throughput: {self.metrics.throughput_per_second:.2f}/sec"
                    )
                
                # Reset latency window to prevent memory growth
                self.metrics.latency_ms = self.metrics.latency_ms[-1000:]  # Keep last 1000 measurements
                
                await asyncio.sleep(60)  # Report every minute
                
            except Exception as e:
                self.logger.error(f"Metrics reporting error: {str(e)}")
                await asyncio.sleep(30)
    
    def update_processing_metrics(self, processing_time_ms: float):
        """Update processing metrics"""
        self.metrics.processed_count += 1
        self.metrics.latency_ms.append(processing_time_ms)
        self.metrics.last_processed_timestamp = datetime.now()
        
        # Calculate throughput (messages per second over last minute)
        now = datetime.now()
        if self.metrics.last_processed_timestamp:
            time_diff = (now - self.metrics.last_processed_timestamp).total_seconds()
            if time_diff > 0:
                self.metrics.throughput_per_second = 1.0 / time_diff
    
    def cleanup(self):
        """Clean up resources"""
        try:
            self.producer.flush()
            self.market_consumer.close()
            self.transaction_consumer.close()
            self.redis_client.close()
            self.logger.info("Stream processor cleanup completed")
        except Exception as e:
            self.logger.error(f"Cleanup error: {str(e)}")


# Example usage and configuration
if __name__ == "__main__":
    import asyncio
    
    config = {
        'bootstrap_servers': 'localhost:9092',
        'schema_registry_url': 'http://localhost:8081',
        'consumer_group': 'financial-stream-processor',
        'topics': {
            'market_data': 'market-data-raw',
            'transactions': 'transactions-raw',
            'market_data_processed': 'market-data-processed',
            'transactions_processed': 'transactions-processed',
            'alerts': 'financial-alerts'
        },
        'redis': {
            'host': 'localhost',
            'port': 6379,
            'db': 0
        },
        'database': {
            'host': 'localhost',
            'port': 5432,
            'database': 'financial_planning',
            'user': 'postgres',
            'password': 'password'
        }
    }
    
    processor = AdvancedStreamProcessor(config)
    asyncio.run(processor.start_processing())