"""
Kafka Streams processor for financial data
Handles real-time stream processing with stateful operations
"""

import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from collections import defaultdict, deque

from kafka import KafkaProducer, KafkaConsumer
from kafka.errors import KafkaError
import pandas as pd
import numpy as np


@dataclass
class StreamConfig:
    """Configuration for stream processing"""
    bootstrap_servers: List[str]
    consumer_group: str
    auto_offset_reset: str = 'earliest'
    enable_auto_commit: bool = True
    session_timeout_ms: int = 30000
    heartbeat_interval_ms: int = 3000
    max_poll_records: int = 500
    fetch_min_bytes: int = 1024
    fetch_max_wait_ms: int = 500


class FinancialStreamProcessor:
    """
    Real-time financial data stream processor with advanced analytics
    """
    
    def __init__(self, config: StreamConfig):
        self.config = config
        self.producer = None
        self.consumers = {}
        self.state_stores = {}
        self.running = False
        
        # Initialize state stores
        self._initialize_state_stores()
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def _initialize_state_stores(self):
        """Initialize in-memory state stores for stateful processing"""
        self.state_stores = {
            'user_sessions': defaultdict(dict),
            'price_history': defaultdict(lambda: deque(maxlen=100)),
            'transaction_patterns': defaultdict(list),
            'fraud_scores': defaultdict(float),
            'budget_tracking': defaultdict(dict),
            'portfolio_positions': defaultdict(dict),
            'market_volatility': defaultdict(lambda: deque(maxlen=50)),
            'correlation_matrix': defaultdict(dict)
        }
    
    def start(self):
        """Start the stream processing"""
        try:
            # Initialize producer
            self.producer = KafkaProducer(
                bootstrap_servers=self.config.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v, default=str).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None,
                acks='all',
                retries=3,
                batch_size=16384,
                linger_ms=5,
                buffer_memory=33554432
            )
            
            # Initialize consumers for different topics
            self._setup_consumers()
            
            self.running = True
            self.logger.info("Financial stream processor started")
            
            # Start processing loops
            self._process_streams()
            
        except Exception as e:
            self.logger.error(f"Failed to start stream processor: {str(e)}")
            raise
    
    def _setup_consumers(self):
        """Setup consumers for different topics"""
        topics = [
            'market_data_real_time',
            'transaction_stream',
            'user_activity_stream',
            'portfolio_updates'
        ]
        
        for topic in topics:
            consumer = KafkaConsumer(
                topic,
                bootstrap_servers=self.config.bootstrap_servers,
                group_id=f"{self.config.consumer_group}_{topic}",
                auto_offset_reset=self.config.auto_offset_reset,
                enable_auto_commit=self.config.enable_auto_commit,
                session_timeout_ms=self.config.session_timeout_ms,
                heartbeat_interval_ms=self.config.heartbeat_interval_ms,
                max_poll_records=self.config.max_poll_records,
                fetch_min_bytes=self.config.fetch_min_bytes,
                fetch_max_wait_ms=self.config.fetch_max_wait_ms,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                key_deserializer=lambda k: k.decode('utf-8') if k else None
            )
            
            self.consumers[topic] = consumer
    
    def _process_streams(self):
        """Main processing loop for all streams"""
        while self.running:
            try:
                # Process each topic
                for topic, consumer in self.consumers.items():
                    messages = consumer.poll(timeout_ms=1000)
                    
                    for topic_partition, records in messages.items():
                        for record in records:
                            self._route_message(topic, record)
                
            except Exception as e:
                self.logger.error(f"Error in stream processing: {str(e)}")
                continue
    
    def _route_message(self, topic: str, record):
        """Route messages to appropriate processors"""
        try:
            if topic == 'market_data_real_time':
                self._process_market_data(record)
            elif topic == 'transaction_stream':
                self._process_transaction(record)
            elif topic == 'user_activity_stream':
                self._process_user_activity(record)
            elif topic == 'portfolio_updates':
                self._process_portfolio_update(record)
                
        except Exception as e:
            self.logger.error(f"Error processing message from {topic}: {str(e)}")
    
    def _process_market_data(self, record):
        """Process real-time market data with technical analysis"""
        try:
            data = record.value
            symbol = data.get('symbol')
            price = float(data.get('price', 0))
            volume = int(data.get('volume', 0))
            timestamp = data.get('timestamp')
            
            # Update price history
            price_history = self.state_stores['price_history'][symbol]
            price_history.append({
                'price': price,
                'volume': volume,
                'timestamp': timestamp
            })
            
            # Calculate technical indicators
            technical_analysis = self._calculate_technical_indicators(symbol, price_history)
            
            # Update volatility tracking
            volatility_history = self.state_stores['market_volatility'][symbol]
            if len(price_history) > 1:
                price_change = (price - price_history[-2]['price']) / price_history[-2]['price']
                volatility_history.append(abs(price_change))
            
            # Generate enriched market data
            enriched_data = {
                'symbol': symbol,
                'price': price,
                'volume': volume,
                'timestamp': timestamp,
                'technical_indicators': technical_analysis,
                'volatility_score': self._calculate_volatility_score(volatility_history),
                'trend_direction': self._determine_trend(price_history),
                'support_resistance': self._calculate_support_resistance(price_history),
                'processed_at': datetime.utcnow().isoformat()
            }
            
            # Send to analytics topic
            self._send_to_topic('market_analytics', enriched_data, key=symbol)
            
            # Check for alerts
            self._check_market_alerts(enriched_data)
            
        except Exception as e:
            self.logger.error(f"Error processing market data: {str(e)}")
    
    def _process_transaction(self, record):
        """Process transaction with fraud detection and budget tracking"""
        try:
            transaction = record.value
            user_id = transaction.get('user_id')
            amount = float(transaction.get('amount', 0))
            category = transaction.get('category')
            timestamp = transaction.get('timestamp')
            
            # Update transaction patterns
            user_patterns = self.state_stores['transaction_patterns'][user_id]
            user_patterns.append({
                'amount': amount,
                'category': category,
                'timestamp': timestamp
            })
            
            # Keep only recent transactions (last 30 days)
            cutoff_time = datetime.utcnow() - timedelta(days=30)
            user_patterns[:] = [
                t for t in user_patterns 
                if datetime.fromisoformat(t['timestamp'].replace('Z', '+00:00')) > cutoff_time
            ]
            
            # Fraud detection
            fraud_score = self._calculate_fraud_score(user_id, transaction, user_patterns)
            
            # Budget tracking
            budget_impact = self._update_budget_tracking(user_id, category, amount)
            
            # Spending pattern analysis
            spending_pattern = self._analyze_spending_pattern(user_patterns)
            
            # Generate enriched transaction
            enriched_transaction = {
                **transaction,
                'fraud_score': fraud_score,
                'budget_impact': budget_impact,
                'spending_pattern': spending_pattern,
                'anomaly_indicators': self._detect_transaction_anomalies(user_id, transaction),
                'processed_at': datetime.utcnow().isoformat()
            }
            
            # Send to analytics topic
            self._send_to_topic('transaction_analytics', enriched_transaction, key=user_id)
            
            # Check for alerts
            self._check_transaction_alerts(enriched_transaction)
            
        except Exception as e:
            self.logger.error(f"Error processing transaction: {str(e)}")
    
    def _process_user_activity(self, record):
        """Process user activity for behavioral analysis"""
        try:
            activity = record.value
            user_id = activity.get('user_id')
            activity_type = activity.get('activity_type')
            timestamp = activity.get('timestamp')
            
            # Update user session
            session = self.state_stores['user_sessions'][user_id]
            session['last_activity'] = timestamp
            session['activity_count'] = session.get('activity_count', 0) + 1
            
            # Behavioral analysis
            behavior_analysis = self._analyze_user_behavior(user_id, activity)
            
            # Generate insights
            insights = {
                'user_id': user_id,
                'activity_type': activity_type,
                'timestamp': timestamp,
                'behavior_analysis': behavior_analysis,
                'engagement_score': self._calculate_engagement_score(session),
                'processed_at': datetime.utcnow().isoformat()
            }
            
            # Send to analytics topic
            self._send_to_topic('user_analytics', insights, key=user_id)
            
        except Exception as e:
            self.logger.error(f"Error processing user activity: {str(e)}")
    
    def _process_portfolio_update(self, record):
        """Process portfolio updates for performance tracking"""
        try:
            update = record.value
            user_id = update.get('user_id')
            portfolio_id = update.get('portfolio_id')
            positions = update.get('positions', [])
            
            # Update portfolio positions
            portfolio_key = f"{user_id}_{portfolio_id}"
            self.state_stores['portfolio_positions'][portfolio_key] = positions
            
            # Calculate portfolio metrics
            portfolio_metrics = self._calculate_portfolio_metrics(positions)
            
            # Risk analysis
            risk_analysis = self._calculate_portfolio_risk(positions)
            
            # Performance attribution
            performance_attribution = self._calculate_performance_attribution(positions)
            
            # Generate portfolio analytics
            analytics = {
                'user_id': user_id,
                'portfolio_id': portfolio_id,
                'metrics': portfolio_metrics,
                'risk_analysis': risk_analysis,
                'performance_attribution': performance_attribution,
                'rebalancing_suggestions': self._generate_rebalancing_suggestions(positions),
                'processed_at': datetime.utcnow().isoformat()
            }
            
            # Send to analytics topic
            self._send_to_topic('portfolio_analytics', analytics, key=portfolio_key)
            
        except Exception as e:
            self.logger.error(f"Error processing portfolio update: {str(e)}")
    
    def _calculate_technical_indicators(self, symbol: str, price_history: deque) -> Dict:
        """Calculate technical indicators for a symbol"""
        if len(price_history) < 2:
            return {}
        
        prices = [item['price'] for item in price_history]
        volumes = [item['volume'] for item in price_history]
        
        indicators = {}
        
        # Simple Moving Averages
        if len(prices) >= 5:
            indicators['sma_5'] = sum(prices[-5:]) / 5
        if len(prices) >= 20:
            indicators['sma_20'] = sum(prices[-20:]) / 20
        if len(prices) >= 50:
            indicators['sma_50'] = sum(prices[-50:]) / 50
        
        # RSI (Relative Strength Index)
        if len(prices) >= 14:
            indicators['rsi'] = self._calculate_rsi(prices[-14:])
        
        # MACD
        if len(prices) >= 26:
            indicators['macd'] = self._calculate_macd(prices)
        
        # Bollinger Bands
        if len(prices) >= 20:
            indicators['bollinger_bands'] = self._calculate_bollinger_bands(prices[-20:])
        
        # Volume indicators
        if len(volumes) >= 10:
            indicators['volume_sma'] = sum(volumes[-10:]) / 10
            indicators['volume_ratio'] = volumes[-1] / indicators['volume_sma'] if indicators['volume_sma'] > 0 else 1
        
        return indicators
    
    def _calculate_rsi(self, prices: List[float]) -> float:
        """Calculate RSI (Relative Strength Index)"""
        if len(prices) < 2:
            return 50.0
        
        gains = []
        losses = []
        
        for i in range(1, len(prices)):
            change = prices[i] - prices[i-1]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))
        
        avg_gain = sum(gains) / len(gains) if gains else 0
        avg_loss = sum(losses) / len(losses) if losses else 0
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def _calculate_macd(self, prices: List[float]) -> Dict:
        """Calculate MACD (Moving Average Convergence Divergence)"""
        if len(prices) < 26:
            return {}
        
        # Calculate EMAs
        ema_12 = self._calculate_ema(prices, 12)
        ema_26 = self._calculate_ema(prices, 26)
        
        macd_line = ema_12 - ema_26
        
        return {
            'macd_line': macd_line,
            'ema_12': ema_12,
            'ema_26': ema_26
        }
    
    def _calculate_ema(self, prices: List[float], period: int) -> float:
        """Calculate Exponential Moving Average"""
        if len(prices) < period:
            return sum(prices) / len(prices)
        
        multiplier = 2 / (period + 1)
        ema = prices[0]
        
        for price in prices[1:]:
            ema = (price * multiplier) + (ema * (1 - multiplier))
        
        return ema
    
    def _calculate_bollinger_bands(self, prices: List[float]) -> Dict:
        """Calculate Bollinger Bands"""
        if len(prices) < 20:
            return {}
        
        sma = sum(prices) / len(prices)
        variance = sum((price - sma) ** 2 for price in prices) / len(prices)
        std_dev = variance ** 0.5
        
        return {
            'upper_band': sma + (2 * std_dev),
            'middle_band': sma,
            'lower_band': sma - (2 * std_dev)
        }
    
    def _calculate_volatility_score(self, volatility_history: deque) -> float:
        """Calculate volatility score based on recent price movements"""
        if not volatility_history:
            return 0.0
        
        recent_volatility = list(volatility_history)
        avg_volatility = sum(recent_volatility) / len(recent_volatility)
        
        # Normalize to 0-100 scale
        volatility_score = min(avg_volatility * 1000, 100)
        return volatility_score
    
    def _determine_trend(self, price_history: deque) -> str:
        """Determine price trend direction"""
        if len(price_history) < 5:
            return 'NEUTRAL'
        
        recent_prices = [item['price'] for item in list(price_history)[-5:]]
        
        # Calculate trend using linear regression slope
        x = list(range(len(recent_prices)))
        n = len(recent_prices)
        
        sum_x = sum(x)
        sum_y = sum(recent_prices)
        sum_xy = sum(x[i] * recent_prices[i] for i in range(n))
        sum_x2 = sum(x[i] ** 2 for i in range(n))
        
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)
        
        if slope > 0.01:
            return 'UPTREND'
        elif slope < -0.01:
            return 'DOWNTREND'
        else:
            return 'NEUTRAL'
    
    def _calculate_support_resistance(self, price_history: deque) -> Dict:
        """Calculate support and resistance levels"""
        if len(price_history) < 10:
            return {}
        
        prices = [item['price'] for item in price_history]
        
        # Simple approach: use recent highs and lows
        recent_prices = prices[-20:] if len(prices) >= 20 else prices
        
        resistance = max(recent_prices)
        support = min(recent_prices)
        
        return {
            'resistance': resistance,
            'support': support,
            'range_percentage': ((resistance - support) / support) * 100 if support > 0 else 0
        }
    
    def _calculate_fraud_score(self, user_id: str, transaction: Dict, user_patterns: List[Dict]) -> float:
        """Calculate fraud probability score for a transaction"""
        score = 0.0
        
        amount = float(transaction.get('amount', 0))
        timestamp = transaction.get('timestamp')
        location = transaction.get('location', {})
        
        # Amount-based scoring
        if user_patterns:
            avg_amount = sum(t['amount'] for t in user_patterns) / len(user_patterns)
            if amount > avg_amount * 5:  # 5x normal amount
                score += 0.3
            elif amount > avg_amount * 3:  # 3x normal amount
                score += 0.2
        
        # Time-based scoring (unusual hours)
        try:
            hour = datetime.fromisoformat(timestamp.replace('Z', '+00:00')).hour
            if hour < 6 or hour > 22:  # Outside normal hours
                score += 0.1
        except:
            pass
        
        # Frequency-based scoring
        recent_transactions = [
            t for t in user_patterns 
            if (datetime.utcnow() - datetime.fromisoformat(t['timestamp'].replace('Z', '+00:00'))).total_seconds() < 3600
        ]
        
        if len(recent_transactions) > 5:  # More than 5 transactions in an hour
            score += 0.2
        
        # Location-based scoring (if available)
        # This would require historical location data
        
        return min(score, 1.0)
    
    def _update_budget_tracking(self, user_id: str, category: str, amount: float) -> Dict:
        """Update budget tracking for a user"""
        budget_data = self.state_stores['budget_tracking'][user_id]
        
        # Initialize if not exists
        if category not in budget_data:
            budget_data[category] = {
                'budget_limit': 1000,  # Default budget
                'spent_amount': 0,
                'transaction_count': 0
            }
        
        # Update spending
        budget_data[category]['spent_amount'] += amount
        budget_data[category]['transaction_count'] += 1
        
        # Calculate metrics
        spent = budget_data[category]['spent_amount']
        limit = budget_data[category]['budget_limit']
        
        return {
            'category': category,
            'spent_amount': spent,
            'budget_limit': limit,
            'remaining_budget': limit - spent,
            'percentage_used': (spent / limit) * 100 if limit > 0 else 0,
            'is_over_budget': spent > limit
        }
    
    def _analyze_spending_pattern(self, user_patterns: List[Dict]) -> Dict:
        """Analyze user spending patterns"""
        if not user_patterns:
            return {}
        
        # Category analysis
        category_spending = defaultdict(float)
        for transaction in user_patterns:
            category_spending[transaction['category']] += transaction['amount']
        
        total_spending = sum(category_spending.values())
        
        # Time analysis
        hourly_spending = defaultdict(float)
        for transaction in user_patterns:
            try:
                hour = datetime.fromisoformat(transaction['timestamp'].replace('Z', '+00:00')).hour
                hourly_spending[hour] += transaction['amount']
            except:
                continue
        
        return {
            'total_spending': total_spending,
            'avg_transaction': total_spending / len(user_patterns),
            'top_categories': dict(sorted(category_spending.items(), key=lambda x: x[1], reverse=True)[:5]),
            'peak_spending_hour': max(hourly_spending.items(), key=lambda x: x[1])[0] if hourly_spending else None,
            'transaction_frequency': len(user_patterns) / 30  # per day over 30 days
        }
    
    def _detect_transaction_anomalies(self, user_id: str, transaction: Dict) -> List[str]:
        """Detect anomalies in transaction patterns"""
        anomalies = []
        
        amount = float(transaction.get('amount', 0))
        category = transaction.get('category')
        
        # Get user patterns
        user_patterns = self.state_stores['transaction_patterns'][user_id]
        
        if user_patterns:
            # Amount anomaly
            amounts = [t['amount'] for t in user_patterns if t['category'] == category]
            if amounts:
                avg_amount = sum(amounts) / len(amounts)
                if amount > avg_amount * 3:
                    anomalies.append('UNUSUAL_AMOUNT')
        
        # Add more anomaly detection logic here
        
        return anomalies
    
    def _analyze_user_behavior(self, user_id: str, activity: Dict) -> Dict:
        """Analyze user behavior patterns"""
        session = self.state_stores['user_sessions'][user_id]
        
        # Basic behavioral metrics
        behavior = {
            'session_duration': self._calculate_session_duration(session),
            'activity_frequency': session.get('activity_count', 0),
            'engagement_level': self._determine_engagement_level(session),
            'feature_usage': self._analyze_feature_usage(user_id, activity)
        }
        
        return behavior
    
    def _calculate_engagement_score(self, session: Dict) -> float:
        """Calculate user engagement score"""
        activity_count = session.get('activity_count', 0)
        
        # Simple engagement scoring
        if activity_count > 50:
            return 1.0
        elif activity_count > 20:
            return 0.8
        elif activity_count > 10:
            return 0.6
        elif activity_count > 5:
            return 0.4
        else:
            return 0.2
    
    def _calculate_portfolio_metrics(self, positions: List[Dict]) -> Dict:
        """Calculate portfolio performance metrics"""
        if not positions:
            return {}
        
        total_value = sum(float(pos.get('market_value', 0)) for pos in positions)
        total_cost = sum(float(pos.get('cost_basis', 0)) for pos in positions)
        
        metrics = {
            'total_value': total_value,
            'total_cost': total_cost,
            'total_return': total_value - total_cost,
            'total_return_percentage': ((total_value - total_cost) / total_cost) * 100 if total_cost > 0 else 0,
            'position_count': len(positions),
            'diversification_score': self._calculate_diversification_score(positions)
        }
        
        return metrics
    
    def _calculate_portfolio_risk(self, positions: List[Dict]) -> Dict:
        """Calculate portfolio risk metrics"""
        if not positions:
            return {}
        
        # Simple risk calculation based on position concentration
        total_value = sum(float(pos.get('market_value', 0)) for pos in positions)
        
        if total_value == 0:
            return {}
        
        # Concentration risk
        max_position = max(float(pos.get('market_value', 0)) for pos in positions)
        concentration_risk = (max_position / total_value) * 100
        
        # Sector concentration (if sector data available)
        sector_allocation = defaultdict(float)
        for pos in positions:
            sector = pos.get('sector', 'Unknown')
            sector_allocation[sector] += float(pos.get('market_value', 0))
        
        max_sector = max(sector_allocation.values()) if sector_allocation else 0
        sector_concentration = (max_sector / total_value) * 100 if total_value > 0 else 0
        
        return {
            'concentration_risk': concentration_risk,
            'sector_concentration': sector_concentration,
            'risk_level': self._determine_risk_level(concentration_risk, sector_concentration)
        }
    
    def _calculate_performance_attribution(self, positions: List[Dict]) -> Dict:
        """Calculate performance attribution by asset/sector"""
        attribution = defaultdict(float)
        
        for pos in positions:
            symbol = pos.get('symbol', 'Unknown')
            market_value = float(pos.get('market_value', 0))
            cost_basis = float(pos.get('cost_basis', 0))
            
            if cost_basis > 0:
                return_contribution = ((market_value - cost_basis) / cost_basis) * 100
                attribution[symbol] = return_contribution
        
        return dict(attribution)
    
    def _generate_rebalancing_suggestions(self, positions: List[Dict]) -> List[Dict]:
        """Generate portfolio rebalancing suggestions"""
        suggestions = []
        
        # Simple rebalancing logic
        total_value = sum(float(pos.get('market_value', 0)) for pos in positions)
        
        if total_value == 0:
            return suggestions
        
        for pos in positions:
            symbol = pos.get('symbol')
            market_value = float(pos.get('market_value', 0))
            allocation = (market_value / total_value) * 100
            
            # Flag positions with high concentration
            if allocation > 20:  # More than 20% in single position
                suggestions.append({
                    'type': 'REDUCE_CONCENTRATION',
                    'symbol': symbol,
                    'current_allocation': allocation,
                    'suggested_allocation': 15,
                    'action': 'SELL',
                    'amount': market_value * 0.25  # Sell 25%
                })
        
        return suggestions
    
    def _send_to_topic(self, topic: str, data: Dict, key: str = None):
        """Send data to Kafka topic"""
        try:
            future = self.producer.send(topic, value=data, key=key)
            future.get(timeout=10)  # Wait for send to complete
        except KafkaError as e:
            self.logger.error(f"Failed to send to topic {topic}: {str(e)}")
    
    def _check_market_alerts(self, market_data: Dict):
        """Check for market-based alerts"""
        symbol = market_data['symbol']
        volatility = market_data.get('volatility_score', 0)
        
        # High volatility alert
        if volatility > 80:
            alert = {
                'type': 'HIGH_VOLATILITY',
                'symbol': symbol,
                'volatility_score': volatility,
                'timestamp': datetime.utcnow().isoformat(),
                'severity': 'HIGH'
            }
            self._send_to_topic('alerts', alert, key=symbol)
    
    def _check_transaction_alerts(self, transaction: Dict):
        """Check for transaction-based alerts"""
        user_id = transaction['user_id']
        fraud_score = transaction.get('fraud_score', 0)
        budget_impact = transaction.get('budget_impact', {})
        
        # Fraud alert
        if fraud_score > 0.8:
            alert = {
                'type': 'POTENTIAL_FRAUD',
                'user_id': user_id,
                'transaction_id': transaction['transaction_id'],
                'fraud_score': fraud_score,
                'timestamp': datetime.utcnow().isoformat(),
                'severity': 'CRITICAL'
            }
            self._send_to_topic('alerts', alert, key=user_id)
        
        # Budget alert
        if budget_impact.get('is_over_budget'):
            alert = {
                'type': 'BUDGET_EXCEEDED',
                'user_id': user_id,
                'category': budget_impact['category'],
                'amount_over': budget_impact['spent_amount'] - budget_impact['budget_limit'],
                'timestamp': datetime.utcnow().isoformat(),
                'severity': 'MEDIUM'
            }
            self._send_to_topic('alerts', alert, key=user_id)
    
    def stop(self):
        """Stop the stream processor"""
        self.running = False
        
        if self.producer:
            self.producer.close()
        
        for consumer in self.consumers.values():
            consumer.close()
        
        self.logger.info("Financial stream processor stopped")
    
    # Helper methods for calculations
    def _calculate_session_duration(self, session: Dict) -> float:
        """Calculate session duration in minutes"""
        # Implement session duration logic
        return 30.0  # Placeholder
    
    def _determine_engagement_level(self, session: Dict) -> str:
        """Determine user engagement level"""
        activity_count = session.get('activity_count', 0)
        if activity_count > 50:
            return 'HIGH'
        elif activity_count > 20:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def _analyze_feature_usage(self, user_id: str, activity: Dict) -> Dict:
        """Analyze feature usage patterns"""
        return {
            'most_used_feature': 'dashboard',  # Placeholder
            'feature_diversity': 0.8
        }
    
    def _calculate_diversification_score(self, positions: List[Dict]) -> float:
        """Calculate portfolio diversification score"""
        if len(positions) <= 1:
            return 0.0
        
        # Simple diversification based on number of positions
        # In practice, this would consider correlations, sectors, etc.
        position_count = len(positions)
        if position_count >= 20:
            return 1.0
        elif position_count >= 10:
            return 0.8
        elif position_count >= 5:
            return 0.6
        else:
            return 0.3
    
    def _determine_risk_level(self, concentration_risk: float, sector_concentration: float) -> str:
        """Determine overall risk level"""
        if concentration_risk > 30 or sector_concentration > 40:
            return 'HIGH'
        elif concentration_risk > 20 or sector_concentration > 30:
            return 'MEDIUM'
        else:
            return 'LOW'


# Configuration and startup
if __name__ == "__main__":
    config = StreamConfig(
        bootstrap_servers=['localhost:9092'],
        consumer_group='financial_stream_processor',
        auto_offset_reset='earliest'
    )
    
    processor = FinancialStreamProcessor(config)
    
    try:
        processor.start()
    except KeyboardInterrupt:
        processor.stop()