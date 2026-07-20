"""
Real-time Risk Monitoring System

This module implements comprehensive real-time risk monitoring including:
- Continuous portfolio risk assessment
- Real-time alert generation
- Risk dashboard and metrics
- Automated risk mitigation
- Performance tracking
- Anomaly detection
"""

import asyncio
import numpy as np
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import deque
import logging
from enum import Enum
import json

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    HIGH = "high"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class MonitoringStatus(Enum):
    """Monitoring system status"""
    ACTIVE = "active"
    PAUSED = "paused"
    ERROR = "error"
    MAINTENANCE = "maintenance"


class RiskMetricType(Enum):
    """Types of risk metrics to monitor"""
    VAR = "value_at_risk"
    VOLATILITY = "volatility"
    CORRELATION = "correlation"
    DRAWDOWN = "drawdown"
    LEVERAGE = "leverage"
    CONCENTRATION = "concentration"
    LIQUIDITY = "liquidity"
    MARGIN = "margin"
    PNL = "profit_loss"
    EXPOSURE = "exposure"


@dataclass
class RiskAlert:
    """Risk alert notification"""
    alert_id: str
    timestamp: datetime
    severity: AlertSeverity
    metric_type: RiskMetricType
    current_value: float
    threshold: float
    message: str
    position_id: Optional[str] = None
    recommended_action: Optional[str] = None
    auto_action_taken: Optional[str] = None
    metadata: Dict = field(default_factory=dict)


@dataclass
class RiskMetric:
    """Individual risk metric"""
    metric_type: RiskMetricType
    value: float
    timestamp: datetime
    threshold_warning: float
    threshold_critical: float
    trend: str  # increasing, decreasing, stable
    rate_of_change: float
    historical_values: deque = field(default_factory=lambda: deque(maxlen=100))


@dataclass
class MonitoringConfig:
    """Configuration for risk monitoring"""
    update_frequency: int = 5  # seconds
    alert_cooldown: int = 300  # seconds between same alerts
    historical_window: int = 1440  # minutes (24 hours)
    enable_auto_mitigation: bool = True
    enable_notifications: bool = True
    metrics_to_monitor: List[RiskMetricType] = field(default_factory=list)
    thresholds: Dict[str, Dict[str, float]] = field(default_factory=dict)


@dataclass
class RiskDashboard:
    """Real-time risk dashboard data"""
    timestamp: datetime
    status: MonitoringStatus
    overall_risk_score: float
    risk_level: str
    metrics: Dict[RiskMetricType, RiskMetric]
    active_alerts: List[RiskAlert]
    recent_actions: List[Dict]
    portfolio_stats: Dict[str, float]
    market_conditions: Dict[str, Any]


class RealTimeRiskMonitor:
    """
    Real-time risk monitoring and alerting system
    """
    
    def __init__(
        self,
        config: Optional[MonitoringConfig] = None,
        alert_callback: Optional[Callable] = None
    ):
        """
        Initialize real-time risk monitor
        
        Args:
            config: Monitoring configuration
            alert_callback: Callback function for alerts
        """
        self.config = config or self._default_config()
        self.alert_callback = alert_callback
        self.status = MonitoringStatus.ACTIVE
        
        # Initialize monitoring components
        self.metrics = self._initialize_metrics()
        self.alert_history = deque(maxlen=1000)
        self.active_alerts = []
        self.alert_cooldowns = {}
        
        # Performance tracking
        self.performance_tracker = PerformanceTracker()
        self.anomaly_detector = AnomalyDetector()
        
        # Monitoring tasks
        self.monitoring_task = None
        self.is_running = False
        
    def _default_config(self) -> MonitoringConfig:
        """Default monitoring configuration"""
        return MonitoringConfig(
            update_frequency=5,
            alert_cooldown=300,
            historical_window=1440,
            enable_auto_mitigation=True,
            enable_notifications=True,
            metrics_to_monitor=[
                RiskMetricType.VAR,
                RiskMetricType.VOLATILITY,
                RiskMetricType.DRAWDOWN,
                RiskMetricType.LEVERAGE,
                RiskMetricType.CONCENTRATION,
                RiskMetricType.PNL
            ],
            thresholds={
                'var_95': {'warning': 0.05, 'critical': 0.10},
                'volatility': {'warning': 0.30, 'critical': 0.50},
                'drawdown': {'warning': 0.10, 'critical': 0.20},
                'leverage': {'warning': 1.5, 'critical': 2.0},
                'concentration': {'warning': 0.25, 'critical': 0.40},
                'daily_loss': {'warning': 0.03, 'critical': 0.05},
                'correlation': {'warning': 0.80, 'critical': 0.95}
            }
        )
    
    def _initialize_metrics(self) -> Dict[RiskMetricType, RiskMetric]:
        """Initialize risk metrics"""
        metrics = {}
        
        for metric_type in self.config.metrics_to_monitor:
            # Map metric type to threshold key
            threshold_key = self._get_threshold_key(metric_type)
            thresholds = self.config.thresholds.get(
                threshold_key,
                {'warning': 0.5, 'critical': 1.0}
            )
            
            metrics[metric_type] = RiskMetric(
                metric_type=metric_type,
                value=0.0,
                timestamp=datetime.now(),
                threshold_warning=thresholds['warning'],
                threshold_critical=thresholds['critical'],
                trend='stable',
                rate_of_change=0.0
            )
        
        return metrics
    
    def _get_threshold_key(self, metric_type: RiskMetricType) -> str:
        """Map metric type to threshold configuration key"""
        mapping = {
            RiskMetricType.VAR: 'var_95',
            RiskMetricType.VOLATILITY: 'volatility',
            RiskMetricType.DRAWDOWN: 'drawdown',
            RiskMetricType.LEVERAGE: 'leverage',
            RiskMetricType.CONCENTRATION: 'concentration',
            RiskMetricType.PNL: 'daily_loss',
            RiskMetricType.CORRELATION: 'correlation',
            RiskMetricType.LIQUIDITY: 'liquidity',
            RiskMetricType.MARGIN: 'margin',
            RiskMetricType.EXPOSURE: 'exposure'
        }
        return mapping.get(metric_type, 'default')
    
    async def start_monitoring(
        self,
        portfolio_manager,
        market_data_provider,
        risk_engine
    ):
        """
        Start real-time monitoring
        
        Args:
            portfolio_manager: Portfolio management interface
            market_data_provider: Market data provider
            risk_engine: Risk calculation engine
        """
        if self.is_running:
            logger.warning("Monitoring already running")
            return
        
        self.is_running = True
        self.status = MonitoringStatus.ACTIVE
        
        logger.info("Starting real-time risk monitoring")
        
        # Start monitoring loop
        self.monitoring_task = asyncio.create_task(
            self._monitoring_loop(
                portfolio_manager,
                market_data_provider,
                risk_engine
            )
        )
    
    async def stop_monitoring(self):
        """Stop real-time monitoring"""
        if not self.is_running:
            return
        
        self.is_running = False
        self.status = MonitoringStatus.PAUSED
        
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Stopped real-time risk monitoring")
    
    async def _monitoring_loop(
        self,
        portfolio_manager,
        market_data_provider,
        risk_engine
    ):
        """Main monitoring loop"""
        while self.is_running:
            try:
                # Update portfolio and market data
                portfolio = await portfolio_manager.get_portfolio()
                market_data = await market_data_provider.get_latest_data()
                
                # Calculate risk metrics
                await self._update_metrics(portfolio, market_data, risk_engine)
                
                # Check for alerts
                alerts = self._check_alerts()
                
                # Process alerts
                for alert in alerts:
                    await self._process_alert(alert, portfolio_manager)
                
                # Check for anomalies
                anomalies = self.anomaly_detector.detect(self.metrics)
                for anomaly in anomalies:
                    await self._process_anomaly(anomaly)
                
                # Update performance metrics
                self.performance_tracker.update(portfolio, self.metrics)
                
                # Wait for next update
                await asyncio.sleep(self.config.update_frequency)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                self.status = MonitoringStatus.ERROR
                await asyncio.sleep(self.config.update_frequency * 2)
                self.status = MonitoringStatus.ACTIVE
    
    async def _update_metrics(
        self,
        portfolio: Dict,
        market_data: Dict,
        risk_engine
    ):
        """Update all risk metrics"""
        current_time = datetime.now()
        
        # Calculate VaR
        if RiskMetricType.VAR in self.metrics:
            var_result = await risk_engine.calculate_var(
                portfolio, market_data
            )
            self._update_metric(
                RiskMetricType.VAR,
                var_result['var_95'],
                current_time
            )
        
        # Calculate volatility
        if RiskMetricType.VOLATILITY in self.metrics:
            volatility = self._calculate_portfolio_volatility(
                portfolio, market_data
            )
            self._update_metric(
                RiskMetricType.VOLATILITY,
                volatility,
                current_time
            )
        
        # Calculate drawdown
        if RiskMetricType.DRAWDOWN in self.metrics:
            drawdown = self._calculate_drawdown(portfolio)
            self._update_metric(
                RiskMetricType.DRAWDOWN,
                abs(drawdown),
                current_time
            )
        
        # Calculate leverage
        if RiskMetricType.LEVERAGE in self.metrics:
            leverage = self._calculate_leverage(portfolio)
            self._update_metric(
                RiskMetricType.LEVERAGE,
                leverage,
                current_time
            )
        
        # Calculate concentration
        if RiskMetricType.CONCENTRATION in self.metrics:
            concentration = self._calculate_concentration(portfolio)
            self._update_metric(
                RiskMetricType.CONCENTRATION,
                concentration,
                current_time
            )
        
        # Calculate P&L
        if RiskMetricType.PNL in self.metrics:
            daily_pnl = self._calculate_daily_pnl(portfolio)
            self._update_metric(
                RiskMetricType.PNL,
                daily_pnl,
                current_time
            )
    
    def _update_metric(
        self,
        metric_type: RiskMetricType,
        value: float,
        timestamp: datetime
    ):
        """Update a single metric"""
        metric = self.metrics[metric_type]
        
        # Store historical value
        metric.historical_values.append((timestamp, value))
        
        # Calculate trend and rate of change
        if len(metric.historical_values) > 1:
            prev_value = metric.historical_values[-2][1]
            prev_time = metric.historical_values[-2][0]
            
            # Rate of change (per minute)
            time_diff = (timestamp - prev_time).total_seconds() / 60
            if time_diff > 0:
                metric.rate_of_change = (value - prev_value) / time_diff
            
            # Trend
            if value > prev_value * 1.05:
                metric.trend = 'increasing'
            elif value < prev_value * 0.95:
                metric.trend = 'decreasing'
            else:
                metric.trend = 'stable'
        
        # Update current value
        metric.value = value
        metric.timestamp = timestamp
    
    def _check_alerts(self) -> List[RiskAlert]:
        """Check for alert conditions"""
        alerts = []
        current_time = datetime.now()
        
        for metric_type, metric in self.metrics.items():
            # Check if in cooldown
            cooldown_key = f"{metric_type.value}"
            if cooldown_key in self.alert_cooldowns:
                if (current_time - self.alert_cooldowns[cooldown_key]).total_seconds() < self.config.alert_cooldown:
                    continue
            
            # Check thresholds
            alert = None
            
            if metric.value >= metric.threshold_critical:
                alert = self._create_alert(
                    metric_type,
                    metric.value,
                    metric.threshold_critical,
                    AlertSeverity.CRITICAL
                )
            elif metric.value >= metric.threshold_warning:
                alert = self._create_alert(
                    metric_type,
                    metric.value,
                    metric.threshold_warning,
                    AlertSeverity.WARNING
                )
            
            # Check rapid changes
            if metric.rate_of_change > 0.1:  # 10% per minute
                alert = self._create_alert(
                    metric_type,
                    metric.value,
                    metric.rate_of_change,
                    AlertSeverity.HIGH,
                    f"Rapid increase in {metric_type.value}"
                )
            
            if alert:
                alerts.append(alert)
                self.alert_cooldowns[cooldown_key] = current_time
        
        return alerts
    
    def _create_alert(
        self,
        metric_type: RiskMetricType,
        current_value: float,
        threshold: float,
        severity: AlertSeverity,
        custom_message: Optional[str] = None
    ) -> RiskAlert:
        """Create a risk alert"""
        
        # Generate message
        if custom_message:
            message = custom_message
        else:
            message = f"{metric_type.value} at {current_value:.2f} exceeds threshold {threshold:.2f}"
        
        # Generate recommended action
        recommended_action = self._get_recommended_action(metric_type, severity)
        
        alert = RiskAlert(
            alert_id=f"ALERT-{datetime.now().timestamp()}",
            timestamp=datetime.now(),
            severity=severity,
            metric_type=metric_type,
            current_value=current_value,
            threshold=threshold,
            message=message,
            recommended_action=recommended_action
        )
        
        return alert
    
    def _get_recommended_action(
        self,
        metric_type: RiskMetricType,
        severity: AlertSeverity
    ) -> str:
        """Get recommended action for alert"""
        
        actions = {
            (RiskMetricType.VAR, AlertSeverity.CRITICAL): "Immediately reduce position sizes or add hedges",
            (RiskMetricType.VAR, AlertSeverity.WARNING): "Review portfolio risk and consider reducing exposure",
            (RiskMetricType.VOLATILITY, AlertSeverity.CRITICAL): "Reduce leverage and implement protective strategies",
            (RiskMetricType.DRAWDOWN, AlertSeverity.CRITICAL): "Activate defensive strategies and preserve capital",
            (RiskMetricType.LEVERAGE, AlertSeverity.CRITICAL): "Reduce leverage immediately to avoid margin calls",
            (RiskMetricType.CONCENTRATION, AlertSeverity.WARNING): "Diversify portfolio to reduce concentration risk",
            (RiskMetricType.PNL, AlertSeverity.CRITICAL): "Stop trading and review risk management"
        }
        
        return actions.get(
            (metric_type, severity),
            "Review portfolio and take appropriate action"
        )
    
    async def _process_alert(
        self,
        alert: RiskAlert,
        portfolio_manager
    ):
        """Process and distribute alert"""
        
        # Add to alert history
        self.alert_history.append(alert)
        self.active_alerts.append(alert)
        
        # Log alert
        log_level = {
            AlertSeverity.INFO: logger.info,
            AlertSeverity.WARNING: logger.warning,
            AlertSeverity.HIGH: logger.error,
            AlertSeverity.CRITICAL: logger.critical,
            AlertSeverity.EMERGENCY: logger.critical
        }
        
        log_level[alert.severity](
            f"Risk Alert: {alert.message} | Action: {alert.recommended_action}"
        )
        
        # Send notification if enabled
        if self.config.enable_notifications and self.alert_callback:
            await self.alert_callback(alert)
        
        # Auto-mitigation if enabled and critical
        if (self.config.enable_auto_mitigation and 
            alert.severity in [AlertSeverity.CRITICAL, AlertSeverity.EMERGENCY]):
            
            action_taken = await self._auto_mitigate(
                alert, portfolio_manager
            )
            alert.auto_action_taken = action_taken
    
    async def _auto_mitigate(
        self,
        alert: RiskAlert,
        portfolio_manager
    ) -> str:
        """Automatically mitigate critical risks"""
        
        action_taken = "No action taken"
        
        try:
            if alert.metric_type == RiskMetricType.LEVERAGE:
                # Reduce leverage
                await portfolio_manager.reduce_leverage(target=1.5)
                action_taken = "Reduced leverage to 1.5x"
                
            elif alert.metric_type == RiskMetricType.DRAWDOWN:
                # Activate stop-losses
                await portfolio_manager.activate_all_stops()
                action_taken = "Activated all stop-loss orders"
                
            elif alert.metric_type == RiskMetricType.VAR:
                # Reduce positions proportionally
                await portfolio_manager.reduce_positions(factor=0.7)
                action_taken = "Reduced all positions by 30%"
                
            elif alert.metric_type == RiskMetricType.PNL:
                # Halt trading
                await portfolio_manager.halt_trading()
                action_taken = "Halted all trading activity"
                
        except Exception as e:
            logger.error(f"Auto-mitigation failed: {e}")
            action_taken = f"Auto-mitigation failed: {str(e)}"
        
        return action_taken
    
    async def _process_anomaly(self, anomaly: Dict):
        """Process detected anomaly"""
        
        # Create alert for anomaly
        alert = RiskAlert(
            alert_id=f"ANOMALY-{datetime.now().timestamp()}",
            timestamp=datetime.now(),
            severity=AlertSeverity.HIGH,
            metric_type=anomaly['metric_type'],
            current_value=anomaly['value'],
            threshold=anomaly['expected_value'],
            message=f"Anomaly detected in {anomaly['metric_type'].value}",
            recommended_action="Investigate unusual market behavior",
            metadata={'anomaly_score': anomaly['score']}
        )
        
        await self._process_alert(alert, None)
    
    def _calculate_portfolio_volatility(
        self,
        portfolio: Dict,
        market_data: Dict
    ) -> float:
        """Calculate portfolio volatility"""
        
        # Get position weights and volatilities
        weights = []
        volatilities = []
        
        total_value = portfolio['total_value']
        for position_id, position in portfolio['positions'].items():
            weight = position['value'] / total_value
            vol = market_data.get(position_id, {}).get('volatility', 0.20)
            
            weights.append(weight)
            volatilities.append(vol)
        
        if not weights:
            return 0.0
        
        # Simple portfolio volatility (ignoring correlations)
        weights = np.array(weights)
        volatilities = np.array(volatilities)
        
        # Weighted average volatility (simplified)
        portfolio_vol = np.sqrt(np.sum((weights * volatilities) ** 2))
        
        return portfolio_vol
    
    def _calculate_drawdown(self, portfolio: Dict) -> float:
        """Calculate current drawdown"""
        
        current_value = portfolio['total_value']
        peak_value = portfolio.get('peak_value', current_value)
        
        if peak_value > 0:
            drawdown = (current_value - peak_value) / peak_value
        else:
            drawdown = 0.0
        
        return drawdown
    
    def _calculate_leverage(self, portfolio: Dict) -> float:
        """Calculate portfolio leverage"""
        
        total_positions = sum(
            p['value'] for p in portfolio['positions'].values()
        )
        equity = portfolio.get('equity', portfolio['total_value'])
        
        if equity > 0:
            leverage = total_positions / equity
        else:
            leverage = 0.0
        
        return leverage
    
    def _calculate_concentration(self, portfolio: Dict) -> float:
        """Calculate portfolio concentration (HHI)"""
        
        if not portfolio['positions']:
            return 0.0
        
        total_value = portfolio['total_value']
        weights = [
            (p['value'] / total_value) ** 2 
            for p in portfolio['positions'].values()
        ]
        
        # Herfindahl-Hirschman Index
        hhi = sum(weights)
        
        return hhi
    
    def _calculate_daily_pnl(self, portfolio: Dict) -> float:
        """Calculate daily P&L percentage"""
        
        current_value = portfolio['total_value']
        previous_close = portfolio.get('previous_close', current_value)
        
        if previous_close > 0:
            daily_pnl = (current_value - previous_close) / previous_close
        else:
            daily_pnl = 0.0
        
        return daily_pnl
    
    def get_dashboard(self) -> RiskDashboard:
        """Get current risk dashboard"""
        
        # Calculate overall risk score
        risk_score = self._calculate_overall_risk_score()
        
        # Determine risk level
        if risk_score < 25:
            risk_level = "Low"
        elif risk_score < 50:
            risk_level = "Moderate"
        elif risk_score < 75:
            risk_level = "High"
        else:
            risk_level = "Critical"
        
        # Get portfolio statistics
        portfolio_stats = self.performance_tracker.get_statistics()
        
        # Get market conditions
        market_conditions = self.anomaly_detector.get_market_conditions()
        
        # Get recent actions
        recent_actions = [
            {
                'timestamp': alert.timestamp.isoformat(),
                'action': alert.auto_action_taken,
                'trigger': alert.message
            }
            for alert in self.alert_history
            if alert.auto_action_taken and 
            (datetime.now() - alert.timestamp).total_seconds() < 3600
        ]
        
        return RiskDashboard(
            timestamp=datetime.now(),
            status=self.status,
            overall_risk_score=risk_score,
            risk_level=risk_level,
            metrics=self.metrics,
            active_alerts=self.active_alerts[-10:],  # Last 10 alerts
            recent_actions=recent_actions,
            portfolio_stats=portfolio_stats,
            market_conditions=market_conditions
        )
    
    def _calculate_overall_risk_score(self) -> float:
        """Calculate overall risk score (0-100)"""
        
        if not self.metrics:
            return 0.0
        
        scores = []
        weights = {
            RiskMetricType.VAR: 0.25,
            RiskMetricType.VOLATILITY: 0.15,
            RiskMetricType.DRAWDOWN: 0.20,
            RiskMetricType.LEVERAGE: 0.15,
            RiskMetricType.CONCENTRATION: 0.10,
            RiskMetricType.PNL: 0.15
        }
        
        for metric_type, metric in self.metrics.items():
            # Normalize metric value to 0-100
            if metric.threshold_critical > 0:
                normalized = min(100, (metric.value / metric.threshold_critical) * 100)
            else:
                normalized = 0
            
            weight = weights.get(metric_type, 0.1)
            scores.append(normalized * weight)
        
        return sum(scores) / sum(weights.values())
    
    def export_metrics(self, format: str = 'json') -> str:
        """Export metrics for external systems"""
        
        data = {
            'timestamp': datetime.now().isoformat(),
            'status': self.status.value,
            'metrics': {
                mt.value: {
                    'value': m.value,
                    'trend': m.trend,
                    'rate_of_change': m.rate_of_change
                }
                for mt, m in self.metrics.items()
            },
            'alerts': [
                {
                    'timestamp': a.timestamp.isoformat(),
                    'severity': a.severity.value,
                    'message': a.message
                }
                for a in self.active_alerts[-10:]
            ]
        }
        
        if format == 'json':
            return json.dumps(data, indent=2)
        else:
            # Could add other formats (CSV, XML, etc.)
            return str(data)


class PerformanceTracker:
    """Track portfolio performance metrics"""
    
    def __init__(self):
        self.metrics_history = deque(maxlen=10000)
        self.statistics = {}
        
    def update(self, portfolio: Dict, metrics: Dict[RiskMetricType, RiskMetric]):
        """Update performance metrics"""
        
        entry = {
            'timestamp': datetime.now(),
            'portfolio_value': portfolio['total_value'],
            'metrics': {mt.value: m.value for mt, m in metrics.items()}
        }
        
        self.metrics_history.append(entry)
        self._calculate_statistics()
    
    def _calculate_statistics(self):
        """Calculate performance statistics"""
        
        if len(self.metrics_history) < 2:
            return
        
        values = [e['portfolio_value'] for e in self.metrics_history]
        returns = np.diff(values) / values[:-1]
        
        self.statistics = {
            'total_return': (values[-1] - values[0]) / values[0] if values[0] > 0 else 0,
            'volatility': np.std(returns) * np.sqrt(252) if len(returns) > 1 else 0,
            'sharpe_ratio': np.mean(returns) / np.std(returns) * np.sqrt(252) if np.std(returns) > 0 else 0,
            'max_value': max(values),
            'min_value': min(values),
            'current_value': values[-1]
        }
    
    def get_statistics(self) -> Dict[str, float]:
        """Get performance statistics"""
        return self.statistics.copy()


class AnomalyDetector:
    """Detect anomalies in risk metrics"""
    
    def __init__(self, sensitivity: float = 2.0):
        self.sensitivity = sensitivity  # Standard deviations for anomaly
        self.baseline_stats = {}
        self.market_conditions = {}
        
    def detect(self, metrics: Dict[RiskMetricType, RiskMetric]) -> List[Dict]:
        """Detect anomalies in metrics"""
        
        anomalies = []
        
        for metric_type, metric in metrics.items():
            if len(metric.historical_values) < 20:
                continue
            
            # Calculate baseline statistics
            values = [v[1] for v in metric.historical_values]
            mean = np.mean(values)
            std = np.std(values)
            
            # Check for anomaly
            z_score = (metric.value - mean) / std if std > 0 else 0
            
            if abs(z_score) > self.sensitivity:
                anomalies.append({
                    'metric_type': metric_type,
                    'value': metric.value,
                    'expected_value': mean,
                    'z_score': z_score,
                    'score': abs(z_score) / self.sensitivity
                })
        
        # Update market conditions
        self._update_market_conditions(metrics)
        
        return anomalies
    
    def _update_market_conditions(self, metrics: Dict[RiskMetricType, RiskMetric]):
        """Update market condition assessment"""
        
        # Simple market regime detection
        volatility = metrics.get(RiskMetricType.VOLATILITY, None)
        
        if volatility:
            if volatility.value < 0.15:
                regime = "Low Volatility"
            elif volatility.value < 0.25:
                regime = "Normal"
            elif volatility.value < 0.40:
                regime = "High Volatility"
            else:
                regime = "Crisis"
        else:
            regime = "Unknown"
        
        self.market_conditions = {
            'regime': regime,
            'timestamp': datetime.now().isoformat()
        }
    
    def get_market_conditions(self) -> Dict:
        """Get current market conditions"""
        return self.market_conditions.copy()


if __name__ == "__main__":
    # Example usage
    async def test_monitoring():
        # Create monitor
        monitor = RealTimeRiskMonitor()
        
        # Simulate portfolio and market data
        class MockPortfolioManager:
            async def get_portfolio(self):
                return {
                    'total_value': 1000000,
                    'equity': 900000,
                    'positions': {
                        'AAPL': {'value': 200000},
                        'GOOGL': {'value': 150000},
                        'MSFT': {'value': 100000}
                    },
                    'previous_close': 980000,
                    'peak_value': 1050000
                }
            
            async def reduce_positions(self, factor):
                print(f"Reducing positions by {1-factor:.0%}")
        
        class MockMarketDataProvider:
            async def get_latest_data(self):
                return {
                    'AAPL': {'volatility': 0.25},
                    'GOOGL': {'volatility': 0.30},
                    'MSFT': {'volatility': 0.22}
                }
        
        class MockRiskEngine:
            async def calculate_var(self, portfolio, market_data):
                return {'var_95': 0.08}
        
        # Start monitoring
        await monitor.start_monitoring(
            MockPortfolioManager(),
            MockMarketDataProvider(),
            MockRiskEngine()
        )
        
        # Run for a bit
        await asyncio.sleep(15)
        
        # Get dashboard
        dashboard = monitor.get_dashboard()
        print(f"Risk Score: {dashboard.overall_risk_score:.1f}")
        print(f"Risk Level: {dashboard.risk_level}")
        print(f"Active Alerts: {len(dashboard.active_alerts)}")
        
        # Stop monitoring
        await monitor.stop_monitoring()
    
    # Run test
    # asyncio.run(test_monitoring())