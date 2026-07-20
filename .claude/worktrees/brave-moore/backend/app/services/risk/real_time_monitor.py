"""
Real-Time Risk Monitoring and Alert System

This module implements real-time portfolio risk monitoring with:
- Live risk metric calculation
- Automated alert generation
- WebSocket streaming for dashboards
- Risk limit enforcement
- Automated hedging recommendations
- Circuit breaker implementation
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Set, Callable
from dataclasses import dataclass, field
from enum import Enum
import logging
from collections import deque
import numpy as np
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
import websocket
from threading import Lock, Thread
import redis
import pickle

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    HIGH = "high"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class MonitoringMetric(Enum):
    """Metrics to monitor in real-time"""
    PORTFOLIO_VALUE = "portfolio_value"
    VAR_95 = "var_95"
    VAR_99 = "var_99"
    CURRENT_DRAWDOWN = "current_drawdown"
    VOLATILITY = "volatility"
    CORRELATION = "correlation"
    CONCENTRATION = "concentration"
    LIQUIDITY = "liquidity"
    MARGIN_USAGE = "margin_usage"
    LEVERAGE = "leverage"
    BETA = "beta"
    DELTA = "delta"
    GAMMA = "gamma"
    THETA = "theta"
    VEGA = "vega"


@dataclass
class RiskAlert:
    """Risk alert notification"""
    alert_id: str
    timestamp: datetime
    metric: MonitoringMetric
    severity: AlertSeverity
    current_value: float
    threshold_value: float
    message: str
    recommended_action: str
    auto_action_taken: Optional[str] = None
    acknowledged: bool = False
    resolved: bool = False
    resolution_time: Optional[datetime] = None


@dataclass
class MonitoringRule:
    """Rule for monitoring and alerting"""
    rule_id: str
    metric: MonitoringMetric
    condition: str  # "greater_than", "less_than", "equals", "change_percent"
    threshold: float
    severity: AlertSeverity
    cooldown_minutes: int = 5  # Prevent alert spam
    auto_action: Optional[Callable] = None
    enabled: bool = True


@dataclass
class CircuitBreaker:
    """Circuit breaker for emergency risk control"""
    breaker_id: str
    trigger_condition: str
    threshold: float
    action: str  # "halt_trading", "liquidate_positions", "hedge_portfolio"
    cooldown_minutes: int = 60
    last_triggered: Optional[datetime] = None
    trigger_count: int = 0
    enabled: bool = True


class RealTimeRiskMonitor:
    """
    Real-time risk monitoring and alert system
    """
    
    def __init__(
        self,
        redis_host: str = "localhost",
        redis_port: int = 6379,
        websocket_port: int = 8765
    ):
        """Initialize real-time monitor"""
        
        # Data storage
        self.positions = {}
        self.market_data = {}
        self.historical_data = deque(maxlen=1000)  # Keep last 1000 data points
        self.risk_metrics = {}
        self.alerts: List[RiskAlert] = []
        
        # Monitoring configuration
        self.monitoring_rules = self._initialize_monitoring_rules()
        self.circuit_breakers = self._initialize_circuit_breakers()
        self.monitoring_interval = 1  # seconds
        self.calculation_interval = 5  # seconds for heavy calculations
        
        # Threading and async
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.monitoring_active = False
        self.monitoring_thread = None
        self.calculation_thread = None
        self.lock = Lock()
        
        # Redis for distributed monitoring
        try:
            self.redis_client = redis.Redis(
                host=redis_host,
                port=redis_port,
                decode_responses=False
            )
            self.redis_available = True
        except:
            logger.warning("Redis not available, using in-memory storage")
            self.redis_client = None
            self.redis_available = False
        
        # WebSocket for real-time updates
        self.websocket_clients = set()
        self.websocket_server = None
        self.websocket_port = websocket_port
        
        # Alert history and statistics
        self.alert_history = deque(maxlen=1000)
        self.metric_history = {metric: deque(maxlen=1000) for metric in MonitoringMetric}
        
    def _initialize_monitoring_rules(self) -> List[MonitoringRule]:
        """Initialize default monitoring rules"""
        
        return [
            # VaR monitoring
            MonitoringRule(
                rule_id="VAR95_LIMIT",
                metric=MonitoringMetric.VAR_95,
                condition="greater_than",
                threshold=0.05,
                severity=AlertSeverity.HIGH,
                cooldown_minutes=5
            ),
            MonitoringRule(
                rule_id="VAR99_LIMIT",
                metric=MonitoringMetric.VAR_99,
                condition="greater_than",
                threshold=0.10,
                severity=AlertSeverity.CRITICAL,
                cooldown_minutes=5
            ),
            
            # Drawdown monitoring
            MonitoringRule(
                rule_id="DRAWDOWN_WARNING",
                metric=MonitoringMetric.CURRENT_DRAWDOWN,
                condition="less_than",
                threshold=-0.10,
                severity=AlertSeverity.WARNING,
                cooldown_minutes=15
            ),
            MonitoringRule(
                rule_id="DRAWDOWN_CRITICAL",
                metric=MonitoringMetric.CURRENT_DRAWDOWN,
                condition="less_than",
                threshold=-0.20,
                severity=AlertSeverity.CRITICAL,
                cooldown_minutes=5
            ),
            
            # Volatility spike
            MonitoringRule(
                rule_id="VOLATILITY_SPIKE",
                metric=MonitoringMetric.VOLATILITY,
                condition="change_percent",
                threshold=0.50,  # 50% increase
                severity=AlertSeverity.HIGH,
                cooldown_minutes=10
            ),
            
            # Correlation breakdown
            MonitoringRule(
                rule_id="CORRELATION_BREAKDOWN",
                metric=MonitoringMetric.CORRELATION,
                condition="greater_than",
                threshold=0.90,
                severity=AlertSeverity.WARNING,
                cooldown_minutes=30
            ),
            
            # Concentration risk
            MonitoringRule(
                rule_id="CONCENTRATION_RISK",
                metric=MonitoringMetric.CONCENTRATION,
                condition="greater_than",
                threshold=0.25,
                severity=AlertSeverity.WARNING,
                cooldown_minutes=60
            ),
            
            # Liquidity crisis
            MonitoringRule(
                rule_id="LIQUIDITY_CRISIS",
                metric=MonitoringMetric.LIQUIDITY,
                condition="less_than",
                threshold=0.30,
                severity=AlertSeverity.HIGH,
                cooldown_minutes=15
            ),
            
            # Leverage limits
            MonitoringRule(
                rule_id="LEVERAGE_LIMIT",
                metric=MonitoringMetric.LEVERAGE,
                condition="greater_than",
                threshold=2.0,
                severity=AlertSeverity.CRITICAL,
                cooldown_minutes=5
            ),
            
            # Margin call warning
            MonitoringRule(
                rule_id="MARGIN_WARNING",
                metric=MonitoringMetric.MARGIN_USAGE,
                condition="greater_than",
                threshold=0.80,
                severity=AlertSeverity.HIGH,
                cooldown_minutes=5
            )
        ]
    
    def _initialize_circuit_breakers(self) -> List[CircuitBreaker]:
        """Initialize circuit breakers for emergency control"""
        
        return [
            CircuitBreaker(
                breaker_id="CATASTROPHIC_LOSS",
                trigger_condition="portfolio_loss_percent",
                threshold=-0.10,  # 10% loss
                action="halt_trading",
                cooldown_minutes=60
            ),
            CircuitBreaker(
                breaker_id="EXTREME_VOLATILITY",
                trigger_condition="volatility_spike",
                threshold=5.0,  # 5x normal volatility
                action="reduce_positions",
                cooldown_minutes=30
            ),
            CircuitBreaker(
                breaker_id="MARGIN_CALL",
                trigger_condition="margin_usage",
                threshold=0.95,  # 95% margin used
                action="liquidate_positions",
                cooldown_minutes=15
            ),
            CircuitBreaker(
                breaker_id="CORRELATION_CRISIS",
                trigger_condition="correlation_average",
                threshold=0.95,  # 95% average correlation
                action="hedge_portfolio",
                cooldown_minutes=120
            )
        ]
    
    async def start_monitoring(self):
        """Start real-time monitoring"""
        
        if self.monitoring_active:
            logger.warning("Monitoring already active")
            return
        
        self.monitoring_active = True
        
        # Start monitoring thread
        self.monitoring_thread = Thread(target=self._monitoring_loop)
        self.monitoring_thread.daemon = True
        self.monitoring_thread.start()
        
        # Start calculation thread
        self.calculation_thread = Thread(target=self._calculation_loop)
        self.calculation_thread.daemon = True
        self.calculation_thread.start()
        
        # Start WebSocket server
        await self._start_websocket_server()
        
        logger.info("Real-time risk monitoring started")
    
    async def stop_monitoring(self):
        """Stop real-time monitoring"""
        
        self.monitoring_active = False
        
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        
        if self.calculation_thread:
            self.calculation_thread.join(timeout=5)
        
        if self.websocket_server:
            self.websocket_server.close()
        
        logger.info("Real-time risk monitoring stopped")
    
    def _monitoring_loop(self):
        """Main monitoring loop (runs in separate thread)"""
        
        while self.monitoring_active:
            try:
                # Update market data
                self._update_market_data()
                
                # Check monitoring rules
                self._check_monitoring_rules()
                
                # Check circuit breakers
                self._check_circuit_breakers()
                
                # Send updates to clients
                self._broadcast_updates()
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
            
            # Sleep for monitoring interval
            asyncio.run(asyncio.sleep(self.monitoring_interval))
    
    def _calculation_loop(self):
        """Heavy calculation loop (runs less frequently)"""
        
        while self.monitoring_active:
            try:
                # Calculate risk metrics
                self._calculate_risk_metrics()
                
                # Update historical data
                self._update_historical_data()
                
                # Analyze trends
                self._analyze_trends()
                
                # Generate predictions
                self._generate_risk_predictions()
                
            except Exception as e:
                logger.error(f"Error in calculation loop: {e}")
            
            # Sleep for calculation interval
            asyncio.run(asyncio.sleep(self.calculation_interval))
    
    def _update_market_data(self):
        """Update live market data"""
        
        # This would connect to real market data feeds
        # For demo, we'll simulate data
        
        with self.lock:
            for symbol in self.positions.keys():
                if symbol not in self.market_data:
                    self.market_data[symbol] = {
                        'price': 100.0,
                        'volume': 1000000,
                        'bid': 99.95,
                        'ask': 100.05,
                        'volatility': 0.20
                    }
                
                # Simulate price movement
                current_price = self.market_data[symbol]['price']
                volatility = self.market_data[symbol]['volatility']
                daily_vol = volatility / np.sqrt(252)
                
                # Random walk with drift
                drift = 0.0001  # Small positive drift
                random_shock = np.random.normal(drift, daily_vol)
                new_price = current_price * (1 + random_shock)
                
                self.market_data[symbol]['price'] = new_price
                self.market_data[symbol]['last_update'] = datetime.now()
    
    def _calculate_risk_metrics(self):
        """Calculate current risk metrics"""
        
        with self.lock:
            # Portfolio value
            portfolio_value = sum(
                self.positions.get(symbol, {}).get('quantity', 0) * 
                self.market_data.get(symbol, {}).get('price', 0)
                for symbol in self.positions
            )
            
            # Simple VaR calculation (would be more sophisticated in production)
            returns = []
            for symbol in self.positions:
                if symbol in self.market_data:
                    price_history = self.metric_history.get(MonitoringMetric.PORTFOLIO_VALUE, [])
                    if len(price_history) > 1:
                        recent_returns = np.diff(list(price_history)[-100:]) / list(price_history)[-101:-1]
                        returns.extend(recent_returns)
            
            if returns:
                var_95 = np.percentile(returns, 5) if returns else 0
                var_99 = np.percentile(returns, 1) if returns else 0
            else:
                var_95 = 0
                var_99 = 0
            
            # Update metrics
            self.risk_metrics = {
                MonitoringMetric.PORTFOLIO_VALUE: portfolio_value,
                MonitoringMetric.VAR_95: abs(var_95),
                MonitoringMetric.VAR_99: abs(var_99),
                MonitoringMetric.VOLATILITY: np.std(returns) if returns else 0,
                MonitoringMetric.CURRENT_DRAWDOWN: self._calculate_current_drawdown(),
                MonitoringMetric.CONCENTRATION: self._calculate_concentration(),
                MonitoringMetric.LIQUIDITY: self._calculate_liquidity(),
                MonitoringMetric.LEVERAGE: self._calculate_leverage(),
                MonitoringMetric.MARGIN_USAGE: self._calculate_margin_usage()
            }
            
            # Store in history
            for metric, value in self.risk_metrics.items():
                self.metric_history[metric].append(value)
            
            # Store in Redis if available
            if self.redis_available:
                self._store_metrics_redis()
    
    def _calculate_current_drawdown(self) -> float:
        """Calculate current drawdown from peak"""
        
        history = list(self.metric_history[MonitoringMetric.PORTFOLIO_VALUE])
        if len(history) < 2:
            return 0
        
        peak = max(history)
        current = history[-1] if history else 0
        
        if peak > 0:
            drawdown = (current - peak) / peak
            return drawdown
        return 0
    
    def _calculate_concentration(self) -> float:
        """Calculate portfolio concentration (HHI)"""
        
        total_value = sum(
            self.positions.get(symbol, {}).get('quantity', 0) * 
            self.market_data.get(symbol, {}).get('price', 0)
            for symbol in self.positions
        )
        
        if total_value == 0:
            return 1.0
        
        hhi = 0
        for symbol in self.positions:
            position_value = (
                self.positions[symbol].get('quantity', 0) * 
                self.market_data.get(symbol, {}).get('price', 0)
            )
            weight = position_value / total_value
            hhi += weight ** 2
        
        return hhi
    
    def _calculate_liquidity(self) -> float:
        """Calculate portfolio liquidity score"""
        
        # Simple liquidity based on volume
        # In production, would use bid-ask spreads, market depth, etc.
        
        total_value = sum(
            self.positions.get(symbol, {}).get('quantity', 0) * 
            self.market_data.get(symbol, {}).get('price', 0)
            for symbol in self.positions
        )
        
        if total_value == 0:
            return 0
        
        liquid_value = 0
        for symbol in self.positions:
            position_value = (
                self.positions[symbol].get('quantity', 0) * 
                self.market_data.get(symbol, {}).get('price', 0)
            )
            
            # Check if position can be liquidated quickly
            daily_volume_value = (
                self.market_data.get(symbol, {}).get('volume', 0) * 
                self.market_data.get(symbol, {}).get('price', 0)
            )
            
            if daily_volume_value > 0:
                # Position should be < 1% of daily volume for good liquidity
                liquidity_ratio = position_value / (daily_volume_value * 0.01)
                if liquidity_ratio < 1:
                    liquid_value += position_value
        
        return liquid_value / total_value
    
    def _calculate_leverage(self) -> float:
        """Calculate current leverage"""
        
        # Simplified leverage calculation
        portfolio_value = self.risk_metrics.get(MonitoringMetric.PORTFOLIO_VALUE, 0)
        account_equity = self.positions.get('account_equity', portfolio_value)
        
        if account_equity > 0:
            return portfolio_value / account_equity
        return 1.0
    
    def _calculate_margin_usage(self) -> float:
        """Calculate margin usage percentage"""
        
        # Simplified margin calculation
        margin_used = self.positions.get('margin_used', 0)
        margin_available = self.positions.get('margin_available', 100000)
        
        total_margin = margin_used + margin_available
        if total_margin > 0:
            return margin_used / total_margin
        return 0
    
    def _check_monitoring_rules(self):
        """Check all monitoring rules for alerts"""
        
        current_time = datetime.now()
        
        for rule in self.monitoring_rules:
            if not rule.enabled:
                continue
            
            # Check cooldown
            last_alert = self._get_last_alert_for_rule(rule.rule_id)
            if last_alert and (current_time - last_alert.timestamp).total_seconds() < rule.cooldown_minutes * 60:
                continue
            
            # Get metric value
            metric_value = self.risk_metrics.get(rule.metric, 0)
            
            # Check condition
            triggered = False
            
            if rule.condition == "greater_than":
                triggered = metric_value > rule.threshold
            elif rule.condition == "less_than":
                triggered = metric_value < rule.threshold
            elif rule.condition == "equals":
                triggered = abs(metric_value - rule.threshold) < 0.0001
            elif rule.condition == "change_percent":
                # Check percentage change from previous value
                history = list(self.metric_history[rule.metric])
                if len(history) >= 2:
                    previous = history[-2]
                    if previous != 0:
                        change_pct = (metric_value - previous) / abs(previous)
                        triggered = abs(change_pct) > rule.threshold
            
            if triggered:
                self._create_alert(rule, metric_value)
                
                # Execute auto action if defined
                if rule.auto_action:
                    self._execute_auto_action(rule, metric_value)
    
    def _check_circuit_breakers(self):
        """Check circuit breakers for emergency conditions"""
        
        current_time = datetime.now()
        
        for breaker in self.circuit_breakers:
            if not breaker.enabled:
                continue
            
            # Check cooldown
            if breaker.last_triggered and (current_time - breaker.last_triggered).total_seconds() < breaker.cooldown_minutes * 60:
                continue
            
            # Check trigger condition
            triggered = False
            
            if breaker.trigger_condition == "portfolio_loss_percent":
                drawdown = self.risk_metrics.get(MonitoringMetric.CURRENT_DRAWDOWN, 0)
                triggered = drawdown < breaker.threshold
                
            elif breaker.trigger_condition == "volatility_spike":
                current_vol = self.risk_metrics.get(MonitoringMetric.VOLATILITY, 0)
                history = list(self.metric_history[MonitoringMetric.VOLATILITY])
                if len(history) > 20:
                    avg_vol = np.mean(history[-20:-1])
                    if avg_vol > 0:
                        spike_ratio = current_vol / avg_vol
                        triggered = spike_ratio > breaker.threshold
                        
            elif breaker.trigger_condition == "margin_usage":
                margin = self.risk_metrics.get(MonitoringMetric.MARGIN_USAGE, 0)
                triggered = margin > breaker.threshold
                
            elif breaker.trigger_condition == "correlation_average":
                correlation = self.risk_metrics.get(MonitoringMetric.CORRELATION, 0)
                triggered = correlation > breaker.threshold
            
            if triggered:
                self._trigger_circuit_breaker(breaker)
    
    def _create_alert(self, rule: MonitoringRule, current_value: float):
        """Create and store alert"""
        
        alert = RiskAlert(
            alert_id=f"ALERT-{datetime.now().strftime('%Y%m%d%H%M%S')}-{rule.rule_id}",
            timestamp=datetime.now(),
            metric=rule.metric,
            severity=rule.severity,
            current_value=current_value,
            threshold_value=rule.threshold,
            message=f"{rule.metric.value} triggered: {current_value:.4f} (threshold: {rule.threshold:.4f})",
            recommended_action=self._get_recommended_action(rule, current_value)
        )
        
        with self.lock:
            self.alerts.append(alert)
            self.alert_history.append(alert)
        
        # Send notification
        self._send_alert_notification(alert)
        
        logger.warning(f"Risk alert: {alert.message}")
    
    def _trigger_circuit_breaker(self, breaker: CircuitBreaker):
        """Trigger circuit breaker action"""
        
        logger.critical(f"CIRCUIT BREAKER TRIGGERED: {breaker.breaker_id}")
        
        breaker.last_triggered = datetime.now()
        breaker.trigger_count += 1
        
        # Create emergency alert
        alert = RiskAlert(
            alert_id=f"BREAKER-{datetime.now().strftime('%Y%m%d%H%M%S')}-{breaker.breaker_id}",
            timestamp=datetime.now(),
            metric=MonitoringMetric.PORTFOLIO_VALUE,  # Generic metric for breakers
            severity=AlertSeverity.EMERGENCY,
            current_value=0,
            threshold_value=breaker.threshold,
            message=f"CIRCUIT BREAKER: {breaker.breaker_id} - Action: {breaker.action}",
            recommended_action=f"Emergency action required: {breaker.action}",
            auto_action_taken=breaker.action
        )
        
        with self.lock:
            self.alerts.append(alert)
        
        # Execute emergency action
        self._execute_emergency_action(breaker.action)
    
    def _execute_emergency_action(self, action: str):
        """Execute emergency circuit breaker action"""
        
        if action == "halt_trading":
            logger.critical("HALTING ALL TRADING ACTIVITY")
            # Implementation would halt all trading systems
            
        elif action == "liquidate_positions":
            logger.critical("INITIATING EMERGENCY LIQUIDATION")
            # Implementation would start liquidation process
            
        elif action == "reduce_positions":
            logger.critical("REDUCING POSITION SIZES")
            # Implementation would reduce all positions by 50%
            
        elif action == "hedge_portfolio":
            logger.critical("INITIATING EMERGENCY HEDGING")
            # Implementation would buy protective puts or other hedges
    
    def _get_recommended_action(self, rule: MonitoringRule, current_value: float) -> str:
        """Get recommended action for alert"""
        
        actions = {
            "VAR95_LIMIT": "Reduce portfolio risk immediately. Consider closing losing positions.",
            "VAR99_LIMIT": "CRITICAL: Portfolio at extreme risk. Liquidate risky positions NOW.",
            "DRAWDOWN_WARNING": "Portfolio in drawdown. Review positions and tighten stops.",
            "DRAWDOWN_CRITICAL": "Severe drawdown. Consider defensive positioning or hedging.",
            "VOLATILITY_SPIKE": "Market volatility spike detected. Reduce position sizes.",
            "CORRELATION_BREAKDOWN": "Asset correlations breaking down. Review diversification.",
            "CONCENTRATION_RISK": "Portfolio too concentrated. Diversify holdings.",
            "LIQUIDITY_CRISIS": "Low liquidity detected. Move to more liquid assets.",
            "LEVERAGE_LIMIT": "Leverage too high. Reduce positions or add capital.",
            "MARGIN_WARNING": "Approaching margin call. Add funds or reduce positions."
        }
        
        return actions.get(rule.rule_id, "Review portfolio and take appropriate action.")
    
    def _get_last_alert_for_rule(self, rule_id: str) -> Optional[RiskAlert]:
        """Get last alert for specific rule"""
        
        for alert in reversed(self.alert_history):
            if rule_id in alert.alert_id:
                return alert
        return None
    
    def _send_alert_notification(self, alert: RiskAlert):
        """Send alert notification to clients"""
        
        # Broadcast via WebSocket
        alert_data = {
            'type': 'risk_alert',
            'alert': {
                'id': alert.alert_id,
                'timestamp': alert.timestamp.isoformat(),
                'severity': alert.severity.value,
                'metric': alert.metric.value,
                'message': alert.message,
                'action': alert.recommended_action
            }
        }
        
        self._broadcast_to_websocket(alert_data)
        
        # Store in Redis for persistence
        if self.redis_available:
            self._store_alert_redis(alert)
    
    def _broadcast_updates(self):
        """Broadcast current metrics to all clients"""
        
        update_data = {
            'type': 'metrics_update',
            'timestamp': datetime.now().isoformat(),
            'metrics': {
                metric.value: value 
                for metric, value in self.risk_metrics.items()
            },
            'active_alerts': len([a for a in self.alerts if not a.resolved]),
            'circuit_breakers_active': any(
                b.last_triggered and 
                (datetime.now() - b.last_triggered).total_seconds() < b.cooldown_minutes * 60
                for b in self.circuit_breakers
            )
        }
        
        self._broadcast_to_websocket(update_data)
    
    def _broadcast_to_websocket(self, data: Dict):
        """Broadcast data to all WebSocket clients"""
        
        if not self.websocket_clients:
            return
        
        message = json.dumps(data)
        disconnected_clients = set()
        
        for client in self.websocket_clients:
            try:
                client.send(message)
            except:
                disconnected_clients.add(client)
        
        # Remove disconnected clients
        self.websocket_clients -= disconnected_clients
    
    async def _start_websocket_server(self):
        """Start WebSocket server for real-time updates"""
        
        # This would implement a full WebSocket server
        # For demo, we'll use a placeholder
        logger.info(f"WebSocket server started on port {self.websocket_port}")
    
    def _store_metrics_redis(self):
        """Store metrics in Redis for distributed monitoring"""
        
        if not self.redis_available:
            return
        
        try:
            # Store current metrics
            metrics_key = f"risk_metrics:{datetime.now().strftime('%Y%m%d%H%M%S')}"
            self.redis_client.setex(
                metrics_key,
                3600,  # 1 hour TTL
                pickle.dumps(self.risk_metrics)
            )
            
            # Update current metrics pointer
            self.redis_client.set("risk_metrics:current", metrics_key)
            
        except Exception as e:
            logger.error(f"Failed to store metrics in Redis: {e}")
    
    def _store_alert_redis(self, alert: RiskAlert):
        """Store alert in Redis"""
        
        if not self.redis_available:
            return
        
        try:
            alert_key = f"risk_alert:{alert.alert_id}"
            self.redis_client.setex(
                alert_key,
                86400,  # 24 hour TTL
                pickle.dumps(alert)
            )
            
            # Add to alert list
            self.redis_client.lpush("risk_alerts:active", alert_key)
            
        except Exception as e:
            logger.error(f"Failed to store alert in Redis: {e}")
    
    def _update_historical_data(self):
        """Update historical data for analysis"""
        
        # Store snapshot of current state
        snapshot = {
            'timestamp': datetime.now(),
            'metrics': dict(self.risk_metrics),
            'positions': dict(self.positions),
            'market_data': dict(self.market_data)
        }
        
        self.historical_data.append(snapshot)
    
    def _analyze_trends(self):
        """Analyze trends in risk metrics"""
        
        if len(self.historical_data) < 10:
            return
        
        # Analyze recent trends
        recent_data = list(self.historical_data)[-100:]
        
        for metric in MonitoringMetric:
            values = [
                d['metrics'].get(metric, 0) 
                for d in recent_data 
                if metric in d['metrics']
            ]
            
            if len(values) > 10:
                # Calculate trend (simple linear regression)
                x = np.arange(len(values))
                slope, intercept = np.polyfit(x, values, 1)
                
                # Store trend information
                trend_direction = "increasing" if slope > 0 else "decreasing"
                trend_strength = abs(slope) / (np.mean(values) if np.mean(values) != 0 else 1)
                
                # Alert on concerning trends
                if trend_strength > 0.1:  # 10% change rate
                    logger.info(f"{metric.value} trend: {trend_direction} (strength: {trend_strength:.2f})")
    
    def _generate_risk_predictions(self):
        """Generate short-term risk predictions"""
        
        # Simple prediction based on recent volatility and trends
        # In production, would use more sophisticated models
        
        if len(self.historical_data) < 30:
            return
        
        predictions = {}
        
        # Predict next period VaR
        recent_var = [
            d['metrics'].get(MonitoringMetric.VAR_95, 0)
            for d in list(self.historical_data)[-30:]
        ]
        
        if recent_var:
            # Simple EWMA prediction
            alpha = 0.94  # Decay factor
            weights = np.array([alpha ** i for i in range(len(recent_var)-1, -1, -1)])
            weights /= weights.sum()
            predicted_var = np.sum(np.array(recent_var) * weights)
            
            predictions['var_95_next'] = predicted_var
            
            # Check if prediction exceeds limits
            if predicted_var > 0.05:
                logger.warning(f"Predicted VaR ({predicted_var:.3f}) may exceed limits")
        
        return predictions
    
    def get_current_status(self) -> Dict[str, Any]:
        """Get current monitoring status"""
        
        with self.lock:
            return {
                'monitoring_active': self.monitoring_active,
                'current_metrics': dict(self.risk_metrics),
                'active_alerts': [
                    {
                        'id': alert.alert_id,
                        'severity': alert.severity.value,
                        'message': alert.message,
                        'timestamp': alert.timestamp.isoformat()
                    }
                    for alert in self.alerts
                    if not alert.resolved
                ],
                'circuit_breakers_status': [
                    {
                        'id': breaker.breaker_id,
                        'enabled': breaker.enabled,
                        'trigger_count': breaker.trigger_count,
                        'last_triggered': breaker.last_triggered.isoformat() if breaker.last_triggered else None
                    }
                    for breaker in self.circuit_breakers
                ],
                'monitoring_rules_enabled': sum(1 for rule in self.monitoring_rules if rule.enabled),
                'total_alerts_today': len([
                    a for a in self.alert_history
                    if a.timestamp.date() == datetime.now().date()
                ])
            }
    
    def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge an alert"""
        
        with self.lock:
            for alert in self.alerts:
                if alert.alert_id == alert_id:
                    alert.acknowledged = True
                    logger.info(f"Alert {alert_id} acknowledged")
                    return True
        return False
    
    def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an alert"""
        
        with self.lock:
            for alert in self.alerts:
                if alert.alert_id == alert_id:
                    alert.resolved = True
                    alert.resolution_time = datetime.now()
                    logger.info(f"Alert {alert_id} resolved")
                    return True
        return False
    
    def update_positions(self, positions: Dict[str, Dict]):
        """Update monitored positions"""
        
        with self.lock:
            self.positions = positions
            logger.info(f"Updated {len(positions)} positions for monitoring")
    
    def add_monitoring_rule(self, rule: MonitoringRule):
        """Add custom monitoring rule"""
        
        self.monitoring_rules.append(rule)
        logger.info(f"Added monitoring rule: {rule.rule_id}")
    
    def disable_circuit_breaker(self, breaker_id: str) -> bool:
        """Disable a circuit breaker"""
        
        for breaker in self.circuit_breakers:
            if breaker.breaker_id == breaker_id:
                breaker.enabled = False
                logger.warning(f"Circuit breaker {breaker_id} disabled")
                return True
        return False
    
    def enable_circuit_breaker(self, breaker_id: str) -> bool:
        """Enable a circuit breaker"""
        
        for breaker in self.circuit_breakers:
            if breaker.breaker_id == breaker_id:
                breaker.enabled = True
                logger.info(f"Circuit breaker {breaker_id} enabled")
                return True
        return False


# Example usage
async def demo_real_time_monitoring():
    """Demonstrate real-time risk monitoring"""
    
    # Create monitor
    monitor = RealTimeRiskMonitor()
    
    # Set up sample positions
    positions = {
        'AAPL': {'quantity': 100, 'cost_basis': 170.00},
        'MSFT': {'quantity': 50, 'cost_basis': 370.00},
        'GOOGL': {'quantity': 25, 'cost_basis': 140.00},
        'account_equity': 100000,
        'margin_used': 20000,
        'margin_available': 80000
    }
    
    monitor.update_positions(positions)
    
    # Start monitoring
    await monitor.start_monitoring()
    
    print("Real-time risk monitoring started...")
    print("="*60)
    
    # Simulate monitoring for a short period
    for i in range(10):
        await asyncio.sleep(2)
        
        # Get current status
        status = monitor.get_current_status()
        
        print(f"\n[Update {i+1}]")
        print(f"Portfolio Value: ${status['current_metrics'].get(MonitoringMetric.PORTFOLIO_VALUE, 0):,.2f}")
        print(f"VaR 95%: {status['current_metrics'].get(MonitoringMetric.VAR_95, 0):.3%}")
        print(f"Current Drawdown: {status['current_metrics'].get(MonitoringMetric.CURRENT_DRAWDOWN, 0):.2%}")
        print(f"Active Alerts: {len(status['active_alerts'])}")
        
        if status['active_alerts']:
            print("\nActive Alerts:")
            for alert in status['active_alerts']:
                print(f"  [{alert['severity']}] {alert['message']}")
        
        if status['circuit_breakers_status']:
            triggered = [cb for cb in status['circuit_breakers_status'] if cb['last_triggered']]
            if triggered:
                print(f"\n⚠️  Circuit Breakers Triggered: {len(triggered)}")
    
    # Stop monitoring
    await monitor.stop_monitoring()
    print("\nMonitoring stopped.")


if __name__ == "__main__":
    asyncio.run(demo_real_time_monitoring())