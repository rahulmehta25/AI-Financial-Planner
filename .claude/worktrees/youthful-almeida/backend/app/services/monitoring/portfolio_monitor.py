"""
Real-Time Portfolio Monitoring Service
Provides comprehensive real-time monitoring with WebSocket support, configurable alerts,
tax loss harvesting detection, and market regime change monitoring.
"""

import asyncio
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
from decimal import Decimal
import logging
from collections import defaultdict, deque
import websockets
import json

from app.services.monitoring.alert_engine import AlertEngine, Alert, AlertType, AlertPriority
from app.services.monitoring.websocket_server import WebSocketManager, BroadcastMessage
from app.services.market_data.aggregator import MarketDataAggregator
from app.services.tax.tax_loss_harvesting import TaxLossHarvestingService
from app.services.modeling.risk_models import RiskModelingService
from app.core.config import Config

logger = logging.getLogger(__name__)


class MonitoringEventType(Enum):
    PORTFOLIO_UPDATE = "portfolio_update"
    REBALANCING_SIGNAL = "rebalancing_signal"
    DRAWDOWN_ALERT = "drawdown_alert"
    GOAL_PROGRESS = "goal_progress"
    TAX_HARVESTING = "tax_harvesting"
    MARKET_REGIME_CHANGE = "market_regime_change"
    RISK_THRESHOLD_BREACH = "risk_threshold_breach"
    CORRELATION_BREAKDOWN = "correlation_breakdown"


@dataclass
class PortfolioSnapshot:
    """Portfolio state at a point in time"""
    timestamp: datetime
    user_id: str
    portfolio_id: str
    total_value: Decimal
    daily_change: Decimal
    daily_change_pct: float
    positions: Dict[str, Dict[str, Any]]
    allocations: Dict[str, float]
    target_allocations: Dict[str, float]
    risk_metrics: Dict[str, float]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MonitoringRule:
    """Base class for monitoring rules"""
    id: str
    name: str
    event_type: MonitoringEventType
    enabled: bool = True
    check_interval_seconds: int = 60
    user_id: str = None
    portfolio_id: str = None
    last_check: Optional[datetime] = None
    last_triggered: Optional[datetime] = None
    cooldown_minutes: int = 15
    
    async def evaluate(self, snapshot: PortfolioSnapshot, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Evaluate rule and return event data if triggered"""
        raise NotImplementedError


class RebalancingRule(MonitoringRule):
    """Monitor portfolio drift and trigger rebalancing alerts"""
    
    def __init__(self, drift_threshold: float = 0.05, **kwargs):
        super().__init__(event_type=MonitoringEventType.REBALANCING_SIGNAL, **kwargs)
        self.drift_threshold = drift_threshold
    
    async def evaluate(self, snapshot: PortfolioSnapshot, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        max_drift = 0
        drifted_assets = []
        
        for symbol, current_weight in snapshot.allocations.items():
            target_weight = snapshot.target_allocations.get(symbol, 0)
            drift = abs(current_weight - target_weight)
            
            if drift > self.drift_threshold:
                drifted_assets.append({
                    'symbol': symbol,
                    'current_weight': round(current_weight * 100, 2),
                    'target_weight': round(target_weight * 100, 2),
                    'drift': round(drift * 100, 2),
                    'dollar_drift': float(snapshot.total_value * Decimal(drift))
                })
                max_drift = max(max_drift, drift)
        
        if drifted_assets:
            return {
                'max_drift': round(max_drift * 100, 2),
                'total_assets_drifted': len(drifted_assets),
                'drifted_assets': drifted_assets,
                'rebalance_value': sum(asset['dollar_drift'] for asset in drifted_assets),
                'priority': 'high' if max_drift > 0.10 else 'medium'
            }
        return None


class DrawdownRule(MonitoringRule):
    """Monitor portfolio drawdown levels"""
    
    def __init__(self, max_drawdown: float = 0.10, trailing_days: int = 30, **kwargs):
        super().__init__(event_type=MonitoringEventType.DRAWDOWN_ALERT, **kwargs)
        self.max_drawdown = max_drawdown
        self.trailing_days = trailing_days
        self.high_water_mark = None
    
    async def evaluate(self, snapshot: PortfolioSnapshot, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        current_value = float(snapshot.total_value)
        
        # Update high water mark
        if self.high_water_mark is None or current_value > self.high_water_mark:
            self.high_water_mark = current_value
        
        # Calculate current drawdown
        current_drawdown = (self.high_water_mark - current_value) / self.high_water_mark
        
        if current_drawdown > self.max_drawdown:
            # Get historical data for context
            historical_values = context.get('historical_values', [current_value])
            
            # Calculate maximum drawdown in period
            max_dd_in_period = 0
            peak = max(historical_values)
            for value in historical_values:
                dd = (peak - value) / peak
                max_dd_in_period = max(max_dd_in_period, dd)
                if value > peak:
                    peak = value
            
            return {
                'current_drawdown': round(current_drawdown * 100, 2),
                'max_drawdown_threshold': round(self.max_drawdown * 100, 2),
                'max_drawdown_in_period': round(max_dd_in_period * 100, 2),
                'high_water_mark': self.high_water_mark,
                'current_value': current_value,
                'value_from_peak': current_value - self.high_water_mark,
                'priority': 'critical' if current_drawdown > 0.15 else 'high'
            }
        return None


class GoalProgressRule(MonitoringRule):
    """Monitor progress toward financial goals"""
    
    def __init__(self, goal_id: str, milestone_intervals: List[float] = None, **kwargs):
        super().__init__(event_type=MonitoringEventType.GOAL_PROGRESS, **kwargs)
        self.goal_id = goal_id
        self.milestone_intervals = milestone_intervals or [0.25, 0.50, 0.75, 0.90, 1.0]
        self.achieved_milestones = set()
    
    async def evaluate(self, snapshot: PortfolioSnapshot, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        goal = context.get('goals', {}).get(self.goal_id)
        if not goal:
            return None
        
        target_amount = goal.get('target_amount', 0)
        current_progress = float(snapshot.total_value) / target_amount if target_amount > 0 else 0
        
        # Check for new milestone achievements
        new_milestones = []
        for milestone in self.milestone_intervals:
            if current_progress >= milestone and milestone not in self.achieved_milestones:
                new_milestones.append(milestone)
                self.achieved_milestones.add(milestone)
        
        if new_milestones:
            highest_milestone = max(new_milestones)
            return {
                'goal_id': self.goal_id,
                'goal_name': goal.get('name', 'Unnamed Goal'),
                'current_amount': float(snapshot.total_value),
                'target_amount': target_amount,
                'progress_percentage': round(current_progress * 100, 2),
                'milestone_achieved': round(highest_milestone * 100, 1),
                'new_milestones': [round(m * 100, 1) for m in new_milestones],
                'on_track': current_progress >= goal.get('expected_progress', 0),
                'priority': 'medium'
            }
        return None


class TaxHarvestingMonitorRule(MonitoringRule):
    """Monitor tax loss harvesting opportunities"""
    
    def __init__(self, min_loss_amount: float = 1000, min_holding_days: int = 31, **kwargs):
        super().__init__(event_type=MonitoringEventType.TAX_HARVESTING, **kwargs)
        self.min_loss_amount = min_loss_amount
        self.min_holding_days = min_holding_days
        self.tax_service = TaxLossHarvestingService()
    
    async def evaluate(self, snapshot: PortfolioSnapshot, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        opportunities = await self.tax_service.identify_harvesting_opportunities(
            snapshot.user_id,
            min_loss=self.min_loss_amount,
            min_holding_days=self.min_holding_days
        )
        
        if opportunities:
            total_potential_savings = sum(opp.get('tax_savings', 0) for opp in opportunities)
            
            return {
                'opportunities_count': len(opportunities),
                'total_potential_savings': round(total_potential_savings, 2),
                'opportunities': opportunities[:5],  # Top 5 opportunities
                'wash_sale_warnings': [
                    opp for opp in opportunities 
                    if opp.get('wash_sale_risk', False)
                ],
                'priority': 'medium' if total_potential_savings > 5000 else 'low'
            }
        return None


class MarketRegimeRule(MonitoringRule):
    """Monitor market regime changes"""
    
    def __init__(self, volatility_threshold: float = 0.25, correlation_threshold: float = 0.7, **kwargs):
        super().__init__(event_type=MonitoringEventType.MARKET_REGIME_CHANGE, **kwargs)
        self.volatility_threshold = volatility_threshold
        self.correlation_threshold = correlation_threshold
        self.risk_service = RiskModelingService()
        self.regime_history = deque(maxlen=30)  # Last 30 regime observations
    
    async def evaluate(self, snapshot: PortfolioSnapshot, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        market_data = context.get('market_data', {})
        if not market_data:
            return None
        
        # Analyze current market regime
        regime_analysis = await self._analyze_market_regime(market_data, snapshot)
        current_regime = regime_analysis.get('regime')
        
        # Store regime history
        self.regime_history.append({
            'timestamp': snapshot.timestamp,
            'regime': current_regime,
            'volatility': regime_analysis.get('volatility', 0),
            'correlation': regime_analysis.get('avg_correlation', 0)
        })
        
        # Detect regime changes
        if len(self.regime_history) >= 2:
            prev_regime = self.regime_history[-2]['regime']
            if current_regime != prev_regime:
                # Calculate regime stability
                recent_regimes = [r['regime'] for r in list(self.regime_history)[-7:]]  # Last week
                stability = recent_regimes.count(current_regime) / len(recent_regimes)
                
                return {
                    'previous_regime': prev_regime,
                    'current_regime': current_regime,
                    'regime_stability': round(stability * 100, 1),
                    'volatility_level': regime_analysis.get('volatility', 0),
                    'correlation_level': regime_analysis.get('avg_correlation', 0),
                    'implications': self._get_regime_implications(current_regime),
                    'recommended_actions': self._get_regime_actions(current_regime),
                    'priority': 'high' if stability < 0.5 else 'medium'
                }
        return None
    
    async def _analyze_market_regime(self, market_data: Dict[str, Any], snapshot: PortfolioSnapshot) -> Dict[str, Any]:
        """Analyze current market regime"""
        try:
            # Get market indicators
            vix = market_data.get('vix', 20)
            sp500_returns = market_data.get('sp500_returns', [])
            correlations = market_data.get('asset_correlations', {})
            
            # Calculate regime indicators
            volatility = vix / 100
            avg_correlation = np.mean(list(correlations.values())) if correlations else 0.5
            
            # Determine regime
            if volatility > self.volatility_threshold and avg_correlation > self.correlation_threshold:
                regime = 'crisis'
            elif volatility > self.volatility_threshold:
                regime = 'volatile'
            elif avg_correlation > self.correlation_threshold:
                regime = 'risk_off'
            else:
                regime = 'normal'
            
            return {
                'regime': regime,
                'volatility': round(volatility, 3),
                'avg_correlation': round(avg_correlation, 3),
                'vix_level': vix,
                'correlation_range': [min(correlations.values()), max(correlations.values())] if correlations else [0, 0]
            }
        except Exception as e:
            logger.error(f"Error analyzing market regime: {e}")
            return {'regime': 'unknown', 'volatility': 0, 'avg_correlation': 0}
    
    def _get_regime_implications(self, regime: str) -> List[str]:
        """Get implications for each regime"""
        implications = {
            'crisis': [
                'High correlation between assets reduces diversification benefits',
                'Flight to quality assets (bonds, gold) may outperform',
                'Value stocks may underperform growth stocks',
                'Increased volatility across all asset classes'
            ],
            'volatile': [
                'Higher than normal market volatility',
                'Increased opportunity for rebalancing gains',
                'Options strategies may become more valuable',
                'Risk parity strategies may underperform'
            ],
            'risk_off': [
                'Investors rotating from risky to safe assets',
                'Defensive sectors may outperform cyclical sectors',
                'Currency hedging becomes more important',
                'Credit spreads likely widening'
            ],
            'normal': [
                'Normal market conditions with typical correlations',
                'Standard asset allocation models should perform well',
                'Good environment for diversified portfolios',
                'Systematic strategies should work as expected'
            ]
        }
        return implications.get(regime, ['Unknown regime implications'])
    
    def _get_regime_actions(self, regime: str) -> List[str]:
        """Get recommended actions for each regime"""
        actions = {
            'crisis': [
                'Consider increasing cash allocation',
                'Review and possibly reduce equity exposure',
                'Increase allocation to safe haven assets',
                'Avoid leveraged strategies'
            ],
            'volatile': [
                'Consider reducing position sizes',
                'Implement options strategies for downside protection',
                'Increase rebalancing frequency',
                'Monitor drawdown levels closely'
            ],
            'risk_off': [
                'Tilt toward defensive sectors',
                'Consider increasing bond duration',
                'Review currency hedging policies',
                'Monitor credit exposure'
            ],
            'normal': [
                'Maintain target asset allocation',
                'Regular rebalancing schedule',
                'Continue systematic investment plans',
                'Monitor for regime changes'
            ]
        }
        return actions.get(regime, ['No specific actions recommended'])


class PortfolioMonitoringService:
    """Comprehensive real-time portfolio monitoring service"""
    
    def __init__(self):
        self.websocket_manager = WebSocketManager()
        self.alert_engine = AlertEngine()
        self.market_data = MarketDataAggregator()
        self.monitoring_rules: Dict[str, List[MonitoringRule]] = defaultdict(list)
        self.portfolio_snapshots: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.active_monitors: Set[str] = set()
        self.check_intervals: Dict[str, int] = {}
        self.running = False
        
        logger.info("Portfolio Monitoring Service initialized")
    
    async def start_monitoring(self):
        """Start the monitoring service"""
        self.running = True
        
        # Start WebSocket server
        await self.websocket_manager.start_server(
            host=Config.WEBSOCKET_HOST or "0.0.0.0",
            port=Config.WEBSOCKET_PORT or 8765
        )
        
        # Start monitoring loops
        asyncio.create_task(self._monitoring_loop())
        asyncio.create_task(self._health_check_loop())
        asyncio.create_task(self._cleanup_loop())
        
        logger.info("Portfolio monitoring service started")
    
    async def stop_monitoring(self):
        """Stop the monitoring service"""
        self.running = False
        await self.websocket_manager.stop_server()
        logger.info("Portfolio monitoring service stopped")
    
    async def register_portfolio(self, user_id: str, portfolio_id: str, rules: List[MonitoringRule]):
        """Register a portfolio for monitoring"""
        monitor_key = f"{user_id}:{portfolio_id}"
        self.monitoring_rules[monitor_key] = rules
        self.active_monitors.add(monitor_key)
        
        # Set minimum check interval
        min_interval = min((rule.check_interval_seconds for rule in rules), default=60)
        self.check_intervals[monitor_key] = min_interval
        
        logger.info(f"Registered monitoring for portfolio {portfolio_id} (user: {user_id}) with {len(rules)} rules")
    
    async def unregister_portfolio(self, user_id: str, portfolio_id: str):
        """Unregister a portfolio from monitoring"""
        monitor_key = f"{user_id}:{portfolio_id}"
        self.monitoring_rules.pop(monitor_key, None)
        self.active_monitors.discard(monitor_key)
        self.check_intervals.pop(monitor_key, None)
        
        logger.info(f"Unregistered monitoring for portfolio {portfolio_id} (user: {user_id})")
    
    async def update_portfolio(self, snapshot: PortfolioSnapshot):
        """Update portfolio state and trigger monitoring checks"""
        monitor_key = f"{snapshot.user_id}:{snapshot.portfolio_id}"
        
        # Store snapshot
        self.portfolio_snapshots[monitor_key].append(snapshot)
        
        # Broadcast real-time update
        await self._broadcast_portfolio_update(snapshot)
        
        # Check monitoring rules
        if monitor_key in self.monitoring_rules:
            await self._check_portfolio_rules(monitor_key, snapshot)
        
        logger.debug(f"Updated portfolio {snapshot.portfolio_id} for user {snapshot.user_id}")
    
    async def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.running:
            try:
                current_time = datetime.utcnow()
                
                for monitor_key in list(self.active_monitors):
                    try:
                        # Check if it's time to evaluate this portfolio
                        interval = self.check_intervals.get(monitor_key, 60)
                        if self._should_check_portfolio(monitor_key, current_time, interval):
                            await self._perform_portfolio_check(monitor_key)
                    except Exception as e:
                        logger.error(f"Error checking portfolio {monitor_key}: {e}")
                
                await asyncio.sleep(5)  # Check every 5 seconds
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(10)
    
    async def _perform_portfolio_check(self, monitor_key: str):
        """Perform comprehensive check for a portfolio"""
        rules = self.monitoring_rules.get(monitor_key, [])
        if not rules:
            return
        
        # Get latest snapshot
        snapshots = self.portfolio_snapshots.get(monitor_key, deque())
        if not snapshots:
            return
        
        latest_snapshot = snapshots[-1]
        
        # Build context for rule evaluation
        context = await self._build_monitoring_context(monitor_key, latest_snapshot)
        
        # Evaluate all rules
        for rule in rules:
            if not rule.enabled:
                continue
            
            try:
                # Check cooldown
                if rule.last_triggered:
                    cooldown_end = rule.last_triggered + timedelta(minutes=rule.cooldown_minutes)
                    if datetime.utcnow() < cooldown_end:
                        continue
                
                # Evaluate rule
                event_data = await rule.evaluate(latest_snapshot, context)
                if event_data:
                    rule.last_triggered = datetime.utcnow()
                    await self._handle_monitoring_event(rule, event_data, latest_snapshot)
                
                rule.last_check = datetime.utcnow()
                
            except Exception as e:
                logger.error(f"Error evaluating rule {rule.id}: {e}")
    
    async def _build_monitoring_context(self, monitor_key: str, snapshot: PortfolioSnapshot) -> Dict[str, Any]:
        """Build context data for rule evaluation"""
        user_id = snapshot.user_id
        
        # Get historical portfolio values
        snapshots = self.portfolio_snapshots[monitor_key]
        historical_values = [float(s.total_value) for s in snapshots]
        
        # Get market data
        market_data = await self.market_data.get_market_overview()
        
        # Get user goals (would typically fetch from database)
        goals = await self._get_user_goals(user_id)
        
        # Calculate additional metrics
        returns = self._calculate_returns(historical_values) if len(historical_values) > 1 else []
        
        return {
            'historical_values': historical_values,
            'returns': returns,
            'market_data': market_data,
            'goals': goals,
            'volatility': np.std(returns) * np.sqrt(252) if returns else 0,  # Annualized
            'sharpe_ratio': self._calculate_sharpe_ratio(returns),
            'max_drawdown': self._calculate_max_drawdown(historical_values),
            'correlation_matrix': await self._get_asset_correlations(snapshot.positions.keys())
        }
    
    def _calculate_returns(self, values: List[float]) -> List[float]:
        """Calculate returns from values"""
        if len(values) < 2:
            return []
        return [(values[i] - values[i-1]) / values[i-1] for i in range(1, len(values))]
    
    def _calculate_sharpe_ratio(self, returns: List[float], risk_free_rate: float = 0.02) -> float:
        """Calculate Sharpe ratio"""
        if not returns:
            return 0
        
        mean_return = np.mean(returns) * 252  # Annualized
        volatility = np.std(returns) * np.sqrt(252)  # Annualized
        
        return (mean_return - risk_free_rate) / volatility if volatility > 0 else 0
    
    def _calculate_max_drawdown(self, values: List[float]) -> float:
        """Calculate maximum drawdown"""
        if len(values) < 2:
            return 0
        
        peak = values[0]
        max_dd = 0
        
        for value in values[1:]:
            if value > peak:
                peak = value
            dd = (peak - value) / peak
            max_dd = max(max_dd, dd)
        
        return max_dd
    
    async def _get_asset_correlations(self, symbols: Set[str]) -> Dict[str, float]:
        """Get correlations between assets"""
        try:
            # This would typically fetch real correlation data
            # For now, return mock correlations
            correlations = {}
            symbol_list = list(symbols)
            for i, symbol1 in enumerate(symbol_list):
                for symbol2 in symbol_list[i+1:]:
                    correlations[f"{symbol1}_{symbol2}"] = np.random.uniform(0.1, 0.8)
            return correlations
        except Exception as e:
            logger.error(f"Error getting asset correlations: {e}")
            return {}
    
    async def _handle_monitoring_event(self, rule: MonitoringRule, event_data: Dict[str, Any], 
                                     snapshot: PortfolioSnapshot):
        """Handle monitoring event"""
        # Create alert
        alert = Alert(
            id=f"{rule.event_type.value}_{snapshot.portfolio_id}_{datetime.utcnow().timestamp()}",
            user_id=snapshot.user_id,
            type=self._map_event_to_alert_type(rule.event_type),
            priority=self._map_priority(event_data.get('priority', 'medium')),
            title=self._generate_alert_title(rule.event_type, event_data),
            message=self._generate_alert_message(rule.event_type, event_data),
            data=event_data,
            requires_action=self._requires_action(rule.event_type),
            action_url=self._get_action_url(rule.event_type)
        )
        
        # Send alert through alert engine
        await self.alert_engine.send_alert(alert)
        
        # Broadcast WebSocket event
        await self._broadcast_monitoring_event(rule.event_type, event_data, snapshot)
        
        logger.info(f"Handled monitoring event: {rule.event_type.value} for portfolio {snapshot.portfolio_id}")
    
    def _map_event_to_alert_type(self, event_type: MonitoringEventType) -> AlertType:
        """Map monitoring event to alert type"""
        mapping = {
            MonitoringEventType.REBALANCING_SIGNAL: AlertType.REBALANCING,
            MonitoringEventType.DRAWDOWN_ALERT: AlertType.DRAWDOWN,
            MonitoringEventType.GOAL_PROGRESS: AlertType.GOAL_PROGRESS,
            MonitoringEventType.TAX_HARVESTING: AlertType.TAX_HARVESTING,
            MonitoringEventType.MARKET_REGIME_CHANGE: AlertType.MARKET_EVENT,
            MonitoringEventType.RISK_THRESHOLD_BREACH: AlertType.RISK_BREACH
        }
        return mapping.get(event_type, AlertType.CUSTOM)
    
    def _map_priority(self, priority_str: str) -> AlertPriority:
        """Map priority string to AlertPriority enum"""
        mapping = {
            'low': AlertPriority.LOW,
            'medium': AlertPriority.MEDIUM,
            'high': AlertPriority.HIGH,
            'critical': AlertPriority.CRITICAL
        }
        return mapping.get(priority_str.lower(), AlertPriority.MEDIUM)
    
    def _generate_alert_title(self, event_type: MonitoringEventType, data: Dict[str, Any]) -> str:
        """Generate alert title based on event type"""
        titles = {
            MonitoringEventType.REBALANCING_SIGNAL: f"Rebalancing Needed - {data.get('max_drift', 0):.1f}% Drift",
            MonitoringEventType.DRAWDOWN_ALERT: f"Portfolio Drawdown Alert - {data.get('current_drawdown', 0):.1f}%",
            MonitoringEventType.GOAL_PROGRESS: f"Goal Milestone Reached - {data.get('milestone_achieved', 0)}%",
            MonitoringEventType.TAX_HARVESTING: f"Tax Harvesting Opportunity - ${data.get('total_potential_savings', 0):,.0f}",
            MonitoringEventType.MARKET_REGIME_CHANGE: f"Market Regime Change - {data.get('current_regime', 'Unknown').title()}",
            MonitoringEventType.RISK_THRESHOLD_BREACH: "Risk Threshold Breach Detected"
        }
        return titles.get(event_type, f"Portfolio Alert - {event_type.value}")
    
    def _generate_alert_message(self, event_type: MonitoringEventType, data: Dict[str, Any]) -> str:
        """Generate alert message based on event type"""
        if event_type == MonitoringEventType.REBALANCING_SIGNAL:
            return f"Your portfolio has drifted {data.get('max_drift', 0):.1f}% from target allocation. {data.get('total_assets_drifted', 0)} assets need rebalancing."
        
        elif event_type == MonitoringEventType.DRAWDOWN_ALERT:
            return f"Portfolio is down {data.get('current_drawdown', 0):.1f}% from recent high. Current value: ${data.get('current_value', 0):,.0f}"
        
        elif event_type == MonitoringEventType.GOAL_PROGRESS:
            return f"Congratulations! You've reached {data.get('milestone_achieved', 0)}% of your '{data.get('goal_name', 'goal')}'."
        
        elif event_type == MonitoringEventType.TAX_HARVESTING:
            return f"Found {data.get('opportunities_count', 0)} tax-loss harvesting opportunities worth ${data.get('total_potential_savings', 0):,.0f} in potential savings."
        
        elif event_type == MonitoringEventType.MARKET_REGIME_CHANGE:
            return f"Market regime changed from {data.get('previous_regime', 'unknown')} to {data.get('current_regime', 'unknown')}. Review recommended actions."
        
        return f"Portfolio monitoring event: {event_type.value}"
    
    def _requires_action(self, event_type: MonitoringEventType) -> bool:
        """Determine if event requires user action"""
        action_required = {
            MonitoringEventType.REBALANCING_SIGNAL: True,
            MonitoringEventType.DRAWDOWN_ALERT: True,
            MonitoringEventType.TAX_HARVESTING: True,
            MonitoringEventType.MARKET_REGIME_CHANGE: True,
            MonitoringEventType.GOAL_PROGRESS: False,
            MonitoringEventType.RISK_THRESHOLD_BREACH: True
        }
        return action_required.get(event_type, False)
    
    def _get_action_url(self, event_type: MonitoringEventType) -> Optional[str]:
        """Get action URL for event type"""
        urls = {
            MonitoringEventType.REBALANCING_SIGNAL: "/portfolio/rebalance",
            MonitoringEventType.DRAWDOWN_ALERT: "/portfolio/risk-analysis",
            MonitoringEventType.TAX_HARVESTING: "/tax/harvesting",
            MonitoringEventType.MARKET_REGIME_CHANGE: "/portfolio/strategy-review",
            MonitoringEventType.RISK_THRESHOLD_BREACH: "/portfolio/risk-settings"
        }
        return urls.get(event_type)
    
    async def _broadcast_portfolio_update(self, snapshot: PortfolioSnapshot):
        """Broadcast real-time portfolio update"""
        update_data = {
            'portfolio_id': snapshot.portfolio_id,
            'total_value': float(snapshot.total_value),
            'daily_change': float(snapshot.daily_change),
            'daily_change_pct': snapshot.daily_change_pct,
            'timestamp': snapshot.timestamp.isoformat(),
            'positions': {
                symbol: {
                    'value': pos.get('value', 0),
                    'change': pos.get('change', 0),
                    'weight': pos.get('weight', 0)
                }
                for symbol, pos in snapshot.positions.items()
            }
        }
        
        await self.websocket_manager.broadcast_update(BroadcastMessage(
            type='portfolio_update',
            channel=f"portfolio:{snapshot.user_id}",
            data=update_data,
            target_users=[snapshot.user_id]
        ))
    
    async def _broadcast_monitoring_event(self, event_type: MonitoringEventType, 
                                        event_data: Dict[str, Any], snapshot: PortfolioSnapshot):
        """Broadcast monitoring event"""
        event_message = {
            'event_type': event_type.value,
            'portfolio_id': snapshot.portfolio_id,
            'data': event_data,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        await self.websocket_manager.broadcast_update(BroadcastMessage(
            type='monitoring_event',
            channel=f"monitoring:{snapshot.user_id}",
            data=event_message,
            target_users=[snapshot.user_id]
        ))
    
    def _should_check_portfolio(self, monitor_key: str, current_time: datetime, interval: int) -> bool:
        """Determine if portfolio should be checked"""
        rules = self.monitoring_rules.get(monitor_key, [])
        if not rules:
            return False
        
        # Check if any rule needs to be evaluated
        for rule in rules:
            if not rule.enabled:
                continue
            
            if not rule.last_check:
                return True
            
            time_since_check = (current_time - rule.last_check).total_seconds()
            if time_since_check >= rule.check_interval_seconds:
                return True
        
        return False
    
    async def _get_user_goals(self, user_id: str) -> Dict[str, Any]:
        """Get user financial goals"""
        # This would typically fetch from database
        # Return mock goals for now
        return {
            'retirement': {
                'name': 'Retirement',
                'target_amount': 1000000,
                'target_date': '2045-01-01',
                'expected_progress': 0.3
            },
            'house': {
                'name': 'House Down Payment',
                'target_amount': 100000,
                'target_date': '2025-06-01',
                'expected_progress': 0.7
            }
        }
    
    async def _health_check_loop(self):
        """Health check loop to ensure monitoring is working"""
        while self.running:
            try:
                await asyncio.sleep(300)  # Check every 5 minutes
                
                # Check WebSocket server health
                if self.websocket_manager.server:
                    active_connections = len(self.websocket_manager.server.connections)
                    logger.debug(f"Health check: {active_connections} active WebSocket connections")
                
                # Check monitoring rules health
                total_rules = sum(len(rules) for rules in self.monitoring_rules.values())
                logger.debug(f"Health check: Monitoring {len(self.active_monitors)} portfolios with {total_rules} rules")
                
            except Exception as e:
                logger.error(f"Error in health check: {e}")
    
    async def _cleanup_loop(self):
        """Cleanup old data periodically"""
        while self.running:
            try:
                await asyncio.sleep(3600)  # Clean up every hour
                
                cutoff_time = datetime.utcnow() - timedelta(hours=24)
                
                # Clean up old snapshots (keep last 24 hours)
                for monitor_key, snapshots in self.portfolio_snapshots.items():
                    while snapshots and snapshots[0].timestamp < cutoff_time:
                        snapshots.popleft()
                
                logger.debug("Completed monitoring data cleanup")
                
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")
    
    async def get_monitoring_status(self, user_id: str, portfolio_id: str) -> Dict[str, Any]:
        """Get current monitoring status for a portfolio"""
        monitor_key = f"{user_id}:{portfolio_id}"
        
        if monitor_key not in self.monitoring_rules:
            return {'status': 'not_monitored'}
        
        rules = self.monitoring_rules[monitor_key]
        snapshots = self.portfolio_snapshots[monitor_key]
        
        return {
            'status': 'active',
            'rules_count': len(rules),
            'enabled_rules': len([r for r in rules if r.enabled]),
            'last_update': snapshots[-1].timestamp.isoformat() if snapshots else None,
            'snapshot_count': len(snapshots),
            'check_interval': self.check_intervals.get(monitor_key, 60),
            'rule_details': [
                {
                    'id': rule.id,
                    'name': rule.name,
                    'type': rule.event_type.value,
                    'enabled': rule.enabled,
                    'last_check': rule.last_check.isoformat() if rule.last_check else None,
                    'last_triggered': rule.last_triggered.isoformat() if rule.last_triggered else None
                }
                for rule in rules
            ]
        }


# Factory functions for creating common monitoring rules
def create_standard_monitoring_rules(user_id: str, portfolio_id: str, 
                                    risk_tolerance: str = 'moderate') -> List[MonitoringRule]:
    """Create standard set of monitoring rules based on risk tolerance"""
    rules = []
    
    # Risk tolerance mappings
    risk_params = {
        'conservative': {
            'drift_threshold': 0.03,
            'max_drawdown': 0.05,
            'min_tax_loss': 500,
            'volatility_threshold': 0.20
        },
        'moderate': {
            'drift_threshold': 0.05,
            'max_drawdown': 0.10,
            'min_tax_loss': 1000,
            'volatility_threshold': 0.25
        },
        'aggressive': {
            'drift_threshold': 0.08,
            'max_drawdown': 0.15,
            'min_tax_loss': 2000,
            'volatility_threshold': 0.30
        }
    }
    
    params = risk_params.get(risk_tolerance, risk_params['moderate'])
    
    # Rebalancing rule
    rules.append(RebalancingRule(
        id=f"rebalance_{portfolio_id}",
        name="Portfolio Rebalancing Monitor",
        user_id=user_id,
        portfolio_id=portfolio_id,
        drift_threshold=params['drift_threshold'],
        check_interval_seconds=300  # 5 minutes
    ))
    
    # Drawdown rule
    rules.append(DrawdownRule(
        id=f"drawdown_{portfolio_id}",
        name="Drawdown Monitor",
        user_id=user_id,
        portfolio_id=portfolio_id,
        max_drawdown=params['max_drawdown'],
        check_interval_seconds=60,  # 1 minute
        cooldown_minutes=60
    ))
    
    # Tax harvesting rule
    rules.append(TaxHarvestingMonitorRule(
        id=f"tax_{portfolio_id}",
        name="Tax Loss Harvesting Monitor",
        user_id=user_id,
        portfolio_id=portfolio_id,
        min_loss_amount=params['min_tax_loss'],
        check_interval_seconds=3600,  # 1 hour
        cooldown_minutes=240  # 4 hours
    ))
    
    # Market regime rule
    rules.append(MarketRegimeRule(
        id=f"regime_{portfolio_id}",
        name="Market Regime Monitor",
        user_id=user_id,
        portfolio_id=portfolio_id,
        volatility_threshold=params['volatility_threshold'],
        check_interval_seconds=900,  # 15 minutes
        cooldown_minutes=120  # 2 hours
    ))
    
    return rules