"""
Real-Time Alert Engine
Handles alert generation, evaluation, and multi-channel delivery
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, AsyncIterator
from dataclasses import dataclass, field
from enum import Enum
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from twilio.rest import Client
import httpx
from jinja2 import Template

from app.core.config import Config
from app.models.base import Base
from app.services.base.logging_service import LoggingService

logger = LoggingService(__name__)


class AlertPriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertType(Enum):
    PORTFOLIO_DRIFT = "portfolio_drift"
    RISK_BREACH = "risk_breach"
    REBALANCING = "rebalancing"
    TAX_HARVESTING = "tax_harvesting"
    MARKET_EVENT = "market_event"
    GOAL_PROGRESS = "goal_progress"
    DRAWDOWN = "drawdown"
    CUSTOM = "custom"


@dataclass
class Alert:
    id: str
    user_id: str
    type: AlertType
    priority: AlertPriority
    title: str
    message: str
    data: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    requires_action: bool = False
    action_url: Optional[str] = None
    expires_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AlertRule:
    """Base class for alert rules"""
    id: str
    name: str
    type: AlertType
    enabled: bool = True
    priority: AlertPriority = AlertPriority.MEDIUM
    cooldown_minutes: int = 60
    last_triggered: Optional[datetime] = None
    
    async def evaluate(self, context: Dict[str, Any]) -> Optional[Alert]:
        """Evaluate rule and generate alert if conditions are met"""
        raise NotImplementedError


class PortfolioDriftRule(AlertRule):
    """Alert when portfolio drifts from target allocation"""
    
    def __init__(self, threshold: float = 0.05, **kwargs):
        super().__init__(type=AlertType.PORTFOLIO_DRIFT, **kwargs)
        self.threshold = threshold
    
    async def evaluate(self, context: Dict[str, Any]) -> Optional[Alert]:
        portfolio = context.get('portfolio')
        if not portfolio:
            return None
        
        max_drift = 0
        drifted_assets = []
        
        for holding in portfolio.holdings:
            target_weight = portfolio.target_allocation.get(holding.symbol, 0)
            current_weight = holding.value / portfolio.total_value
            drift = abs(current_weight - target_weight)
            
            if drift > self.threshold:
                drifted_assets.append({
                    'symbol': holding.symbol,
                    'current': round(current_weight * 100, 2),
                    'target': round(target_weight * 100, 2),
                    'drift': round(drift * 100, 2)
                })
                max_drift = max(max_drift, drift)
        
        if drifted_assets:
            return Alert(
                id=f"drift_{portfolio.id}_{datetime.utcnow().timestamp()}",
                user_id=context['user_id'],
                type=self.type,
                priority=AlertPriority.HIGH if max_drift > 0.10 else AlertPriority.MEDIUM,
                title="Portfolio Rebalancing Needed",
                message=f"Your portfolio has drifted {round(max_drift * 100, 1)}% from target allocation",
                data={'drifted_assets': drifted_assets},
                requires_action=True,
                action_url="/portfolio/rebalance"
            )
        return None


class RiskThresholdRule(AlertRule):
    """Alert when risk metrics exceed thresholds"""
    
    def __init__(self, max_var: float = 0.10, max_sharpe_decline: float = 0.3, **kwargs):
        super().__init__(type=AlertType.RISK_BREACH, **kwargs)
        self.max_var = max_var
        self.max_sharpe_decline = max_sharpe_decline
    
    async def evaluate(self, context: Dict[str, Any]) -> Optional[Alert]:
        risk_metrics = context.get('risk_metrics')
        if not risk_metrics:
            return None
        
        breaches = []
        
        # Check Value at Risk
        if risk_metrics.var_95 > self.max_var:
            breaches.append({
                'metric': 'Value at Risk (95%)',
                'current': round(risk_metrics.var_95 * 100, 2),
                'threshold': round(self.max_var * 100, 2)
            })
        
        # Check Sharpe ratio decline
        if hasattr(risk_metrics, 'sharpe_change'):
            if risk_metrics.sharpe_change < -self.max_sharpe_decline:
                breaches.append({
                    'metric': 'Sharpe Ratio',
                    'change': round(risk_metrics.sharpe_change * 100, 2),
                    'threshold': round(self.max_sharpe_decline * 100, 2)
                })
        
        if breaches:
            return Alert(
                id=f"risk_{context['user_id']}_{datetime.utcnow().timestamp()}",
                user_id=context['user_id'],
                type=self.type,
                priority=AlertPriority.CRITICAL if len(breaches) > 1 else AlertPriority.HIGH,
                title="Risk Threshold Breach",
                message=f"{len(breaches)} risk metric(s) exceeded thresholds",
                data={'breaches': breaches},
                requires_action=True,
                action_url="/risk/analysis"
            )
        return None


class TaxHarvestingRule(AlertRule):
    """Alert for tax-loss harvesting opportunities"""
    
    def __init__(self, min_loss: float = 1000, min_holding_days: int = 31, **kwargs):
        super().__init__(type=AlertType.TAX_HARVESTING, **kwargs)
        self.min_loss = min_loss
        self.min_holding_days = min_holding_days
    
    async def evaluate(self, context: Dict[str, Any]) -> Optional[Alert]:
        portfolio = context.get('portfolio')
        if not portfolio:
            return None
        
        harvesting_opportunities = []
        total_potential_savings = 0
        
        for holding in portfolio.holdings:
            if holding.unrealized_loss > self.min_loss:
                days_held = (datetime.utcnow() - holding.purchase_date).days
                if days_held >= self.min_holding_days:
                    tax_savings = holding.unrealized_loss * context.get('tax_rate', 0.25)
                    harvesting_opportunities.append({
                        'symbol': holding.symbol,
                        'loss': round(holding.unrealized_loss, 2),
                        'tax_savings': round(tax_savings, 2),
                        'days_held': days_held
                    })
                    total_potential_savings += tax_savings
        
        if harvesting_opportunities:
            return Alert(
                id=f"harvest_{context['user_id']}_{datetime.utcnow().timestamp()}",
                user_id=context['user_id'],
                type=self.type,
                priority=AlertPriority.MEDIUM,
                title="Tax-Loss Harvesting Opportunity",
                message=f"Potential tax savings of ${total_potential_savings:,.0f} available",
                data={
                    'opportunities': harvesting_opportunities,
                    'total_savings': total_potential_savings
                },
                requires_action=True,
                action_url="/tax/harvesting"
            )
        return None


class MarketEventRule(AlertRule):
    """Alert for significant market events"""
    
    def __init__(self, volatility_threshold: float = 0.03, news_sentiment_threshold: float = -0.7, **kwargs):
        super().__init__(type=AlertType.MARKET_EVENT, **kwargs)
        self.volatility_threshold = volatility_threshold
        self.news_sentiment_threshold = news_sentiment_threshold
    
    async def evaluate(self, context: Dict[str, Any]) -> Optional[Alert]:
        market_data = context.get('market_data')
        if not market_data:
            return None
        
        events = []
        
        # Check for high volatility
        if market_data.get('vix', 0) > 30:
            events.append({
                'type': 'volatility',
                'description': f"VIX at {market_data['vix']:.1f} - High market volatility",
                'severity': 'high'
            })
        
        # Check for significant market moves
        indices = market_data.get('indices', {})
        for index, data in indices.items():
            if abs(data.get('daily_change', 0)) > self.volatility_threshold:
                events.append({
                    'type': 'market_move',
                    'description': f"{index} {data['daily_change']:+.2%} today",
                    'severity': 'medium' if abs(data['daily_change']) < 0.05 else 'high'
                })
        
        # Check news sentiment
        if market_data.get('news_sentiment', 0) < self.news_sentiment_threshold:
            events.append({
                'type': 'sentiment',
                'description': "Extremely negative market sentiment detected",
                'severity': 'high'
            })
        
        if events:
            max_severity = max((e['severity'] for e in events), default='medium')
            priority_map = {'low': AlertPriority.LOW, 'medium': AlertPriority.MEDIUM, 'high': AlertPriority.HIGH}
            
            return Alert(
                id=f"market_{datetime.utcnow().timestamp()}",
                user_id=context['user_id'],
                type=self.type,
                priority=priority_map[max_severity],
                title="Significant Market Event",
                message=f"{len(events)} market event(s) detected",
                data={'events': events},
                requires_action=False,
                action_url="/market/overview"
            )
        return None


class AlertEngine:
    """Main alert engine for multi-channel delivery"""
    
    def __init__(self):
        self.rules: Dict[str, List[AlertRule]] = {}
        self.alert_history: Dict[str, List[Alert]] = {}
        self.delivery_channels = self._initialize_channels()
        self.template_engine = AlertTemplateEngine()
        self.user_preferences: Dict[str, Dict[str, Any]] = {}
        self.delivery_stats: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self.failed_deliveries: deque = deque(maxlen=1000)
        logger.info("Alert Engine initialized")
    
    def _initialize_channels(self) -> Dict[str, Any]:
        """Initialize delivery channels"""
        channels = {}
        
        # Email channel
        if Config.SMTP_HOST:
            channels['email'] = aiosmtplib.SMTP(
                hostname=Config.SMTP_HOST,
                port=Config.SMTP_PORT,
                use_tls=True
            )
        
        # SMS channel
        if Config.TWILIO_ACCOUNT_SID:
            channels['sms'] = Client(
                Config.TWILIO_ACCOUNT_SID,
                Config.TWILIO_AUTH_TOKEN
            )
        
        # Push notification channel
        channels['push'] = PushNotificationService()
        
        # Webhook channel
        channels['webhook'] = WebhookService()
        
        return channels
    
    async def register_rules(self, user_id: str, rules: List[AlertRule]):
        """Register alert rules for a user"""
        self.rules[user_id] = rules
        logger.info(f"Registered {len(rules)} rules for user {user_id}")
    
    async def evaluate_rules(self, user_id: str, context: Dict[str, Any]) -> List[Alert]:
        """Evaluate all rules for a user"""
        if user_id not in self.rules:
            return []
        
        alerts = []
        for rule in self.rules[user_id]:
            if not rule.enabled:
                continue
            
            # Check cooldown
            if rule.last_triggered:
                cooldown_end = rule.last_triggered + timedelta(minutes=rule.cooldown_minutes)
                if datetime.utcnow() < cooldown_end:
                    continue
            
            try:
                alert = await rule.evaluate(context)
                if alert:
                    alerts.append(alert)
                    rule.last_triggered = datetime.utcnow()
                    await self._store_alert(alert)
            except Exception as e:
                logger.error(f"Error evaluating rule {rule.id}: {e}")
        
        return alerts
    
    async def send_alert(self, alert: Alert, channels: List[str] = None):
        """Send alert through specified channels"""
        if channels is None:
            channels = await self._get_user_channels(alert.user_id)
        
        # Apply user preferences and priority filtering
        channels = self._filter_channels_by_preferences(alert, channels)
        
        if not channels:
            logger.info(f"No active channels for alert {alert.id}")
            return
        
        tasks = []
        for channel in channels:
            if channel in self.delivery_channels:
                tasks.append(self._send_via_channel(alert, channel))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Log delivery results and update stats
        successful_deliveries = 0
        for channel, result in zip(channels, results):
            if isinstance(result, Exception):
                logger.error(f"Failed to send alert via {channel}: {result}")
                self._record_delivery_failure(alert, channel, str(result))
                self.delivery_stats[alert.user_id][f"{channel}_failed"] += 1
            else:
                logger.info(f"Alert sent via {channel} to user {alert.user_id}")
                successful_deliveries += 1
                self.delivery_stats[alert.user_id][f"{channel}_success"] += 1
        
        # Update overall stats
        self.delivery_stats[alert.user_id]["total_sent"] += successful_deliveries
        self.delivery_stats[alert.user_id]["total_failed"] += len(channels) - successful_deliveries
    
    async def _send_via_channel(self, alert: Alert, channel: str):
        """Send alert through specific channel"""
        if channel == 'email':
            return await self._send_email(alert)
        elif channel == 'sms':
            return await self._send_sms(alert)
        elif channel == 'push':
            return await self._send_push(alert)
        elif channel == 'webhook':
            return await self._send_webhook(alert)
        elif channel == 'in_app':
            return await self._send_in_app(alert)
    
    async def _send_email(self, alert: Alert):
        """Send email alert"""
        if 'email' not in self.delivery_channels:
            return
        
        user = await self._get_user(alert.user_id)
        if not user or not user.email:
            return
        
        subject, body = self.template_engine.generate_email(alert, user)
        
        message = MIMEMultipart('alternative')
        message['Subject'] = subject
        message['From'] = Config.EMAIL_FROM
        message['To'] = user.email
        
        html_part = MIMEText(body['html'], 'html')
        text_part = MIMEText(body['text'], 'plain')
        
        message.attach(text_part)
        message.attach(html_part)
        
        await self.delivery_channels['email'].send_message(message)
    
    async def _send_sms(self, alert: Alert):
        """Send SMS alert"""
        if 'sms' not in self.delivery_channels or alert.priority not in [AlertPriority.HIGH, AlertPriority.CRITICAL]:
            return
        
        user = await self._get_user(alert.user_id)
        if not user or not user.phone_verified:
            return
        
        message = self.template_engine.generate_sms(alert)
        
        self.delivery_channels['sms'].messages.create(
            body=message,
            from_=Config.TWILIO_PHONE_NUMBER,
            to=user.phone
        )
    
    async def _send_push(self, alert: Alert):
        """Send push notification"""
        devices = await self._get_user_devices(alert.user_id)
        
        notification = self.template_engine.generate_push(alert)
        
        for device in devices:
            await self.delivery_channels['push'].send(
                device_token=device.token,
                title=notification['title'],
                body=notification['body'],
                data=notification.get('data', {})
            )
    
    async def _send_webhook(self, alert: Alert):
        """Send webhook notification"""
        webhooks = await self._get_user_webhooks(alert.user_id)
        
        for webhook in webhooks:
            if webhook.alert_types and alert.type not in webhook.alert_types:
                continue
            
            await self.delivery_channels['webhook'].send(
                url=webhook.url,
                data=alert.__dict__,
                secret=webhook.secret
            )
    
    async def _send_in_app(self, alert: Alert):
        """Store in-app notification"""
        # This would typically store in database for frontend to fetch
        if alert.user_id not in self.alert_history:
            self.alert_history[alert.user_id] = []
        
        self.alert_history[alert.user_id].append(alert)
        
        # Trim history to last 100 alerts
        if len(self.alert_history[alert.user_id]) > 100:
            self.alert_history[alert.user_id] = self.alert_history[alert.user_id][-100:]
    
    async def _store_alert(self, alert: Alert):
        """Store alert in database"""
        # Implementation would store in actual database
        pass
    
    async def _get_user(self, user_id: str):
        """Get user details"""
        # Implementation would fetch from database
        return {'email': 'user@example.com', 'phone_verified': True}
    
    async def _get_user_channels(self, user_id: str) -> List[str]:
        """Get user's preferred notification channels"""
        # Implementation would fetch from database
        return ['email', 'in_app', 'push']
    
    async def _get_user_devices(self, user_id: str):
        """Get user's registered devices"""
        # Implementation would fetch from database
        return []
    
    async def _get_user_webhooks(self, user_id: str):
        """Get user's configured webhooks"""
        # Implementation would fetch from database
        return []
    
    def _filter_channels_by_preferences(self, alert: Alert, channels: List[str]) -> List[str]:
        """Filter channels based on user preferences and alert priority"""
        user_prefs = self.user_preferences.get(alert.user_id, {})
        
        # Default preferences
        default_prefs = {
            'email_enabled': True,
            'sms_enabled': True,
            'push_enabled': True,
            'in_app_enabled': True,
            'webhook_enabled': False,
            'quiet_hours_start': 22,  # 10 PM
            'quiet_hours_end': 8,     # 8 AM
            'sms_priority_threshold': AlertPriority.HIGH.value,
            'email_frequency_limit': 20,  # Max emails per day
            'sms_frequency_limit': 5      # Max SMS per day
        }
        
        prefs = {**default_prefs, **user_prefs}
        filtered_channels = []
        
        current_hour = datetime.utcnow().hour
        is_quiet_hours = (
            prefs['quiet_hours_start'] <= current_hour or 
            current_hour <= prefs['quiet_hours_end']
        )
        
        for channel in channels:
            # Check if channel is enabled
            channel_enabled_key = f"{channel}_enabled"
            if not prefs.get(channel_enabled_key, True):
                continue
            
            # Check quiet hours (only affects push and SMS)
            if is_quiet_hours and channel in ['push', 'sms'] and alert.priority not in [AlertPriority.HIGH, AlertPriority.CRITICAL]:
                continue
            
            # Check priority thresholds for SMS
            if channel == 'sms' and alert.priority.value not in ['high', 'critical']:
                priority_threshold = prefs.get('sms_priority_threshold', 'high')
                if not self._meets_priority_threshold(alert.priority, priority_threshold):
                    continue
            
            # Check frequency limits
            if self._exceeds_frequency_limit(alert.user_id, channel, prefs):
                continue
            
            filtered_channels.append(channel)
        
        return filtered_channels
    
    def _meets_priority_threshold(self, alert_priority: AlertPriority, threshold: str) -> bool:
        """Check if alert priority meets threshold"""
        priority_order = ['low', 'medium', 'high', 'critical']
        alert_index = priority_order.index(alert_priority.value)
        threshold_index = priority_order.index(threshold)
        return alert_index >= threshold_index
    
    def _exceeds_frequency_limit(self, user_id: str, channel: str, preferences: Dict[str, Any]) -> bool:
        """Check if channel frequency limit is exceeded"""
        limit_key = f"{channel}_frequency_limit"
        limit = preferences.get(limit_key, 100)  # Default high limit
        
        today_key = datetime.utcnow().strftime("%Y-%m-%d")
        daily_stats = self.delivery_stats.get(user_id, {})
        sent_today = daily_stats.get(f"{channel}_sent_{today_key}", 0)
        
        return sent_today >= limit
    
    def _record_delivery_failure(self, alert: Alert, channel: str, error: str):
        """Record delivery failure for analysis"""
        failure_record = {
            'timestamp': datetime.utcnow().isoformat(),
            'alert_id': alert.id,
            'user_id': alert.user_id,
            'channel': channel,
            'error': error,
            'alert_type': alert.type.value,
            'priority': alert.priority.value
        }
        self.failed_deliveries.append(failure_record)
    
    async def set_user_preferences(self, user_id: str, preferences: Dict[str, Any]):
        """Set user notification preferences"""
        self.user_preferences[user_id] = preferences
        logger.info(f"Updated notification preferences for user {user_id}")
    
    async def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """Get user notification preferences"""
        return self.user_preferences.get(user_id, {})
    
    async def get_delivery_stats(self, user_id: str) -> Dict[str, Any]:
        """Get delivery statistics for a user"""
        stats = self.delivery_stats.get(user_id, {})
        failures = [f for f in self.failed_deliveries if f['user_id'] == user_id]
        
        return {
            'total_sent': stats.get('total_sent', 0),
            'total_failed': stats.get('total_failed', 0),
            'success_rate': stats.get('total_sent', 0) / max(stats.get('total_sent', 0) + stats.get('total_failed', 0), 1),
            'channel_stats': {
                channel: {
                    'success': stats.get(f"{channel}_success", 0),
                    'failed': stats.get(f"{channel}_failed", 0)
                }
                for channel in ['email', 'sms', 'push', 'webhook', 'in_app']
            },
            'recent_failures': failures[-10:],  # Last 10 failures
            'failure_rate_by_type': self._calculate_failure_rates_by_type(failures)
        }
    
    def _calculate_failure_rates_by_type(self, failures: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate failure rates by alert type"""
        if not failures:
            return {}
        
        type_counts = defaultdict(int)
        type_failures = defaultdict(int)
        
        for failure in failures:
            alert_type = failure['alert_type']
            type_failures[alert_type] += 1
            # This is simplified - would need total attempts by type for accurate rate
        
        return {
            alert_type: count / max(count, 1)  # Simplified calculation
            for alert_type, count in type_failures.items()
        }
    
    async def retry_failed_deliveries(self, max_retries: int = 3):
        """Retry failed alert deliveries"""
        retry_count = 0
        
        for failure in list(self.failed_deliveries):
            if retry_count >= max_retries:
                break
            
            # Simple retry logic - in production, would have more sophisticated logic
            if failure.get('retry_count', 0) < 2:  # Max 2 retries per alert
                logger.info(f"Retrying delivery for alert {failure['alert_id']} via {failure['channel']}")
                failure['retry_count'] = failure.get('retry_count', 0) + 1
                retry_count += 1
                # Would implement actual retry logic here
    
    async def get_alert_history(self, user_id: str, limit: int = 50, 
                              alert_type: Optional[AlertType] = None) -> List[Alert]:
        """Get alert history for a user"""
        user_alerts = self.alert_history.get(user_id, [])
        
        if alert_type:
            user_alerts = [alert for alert in user_alerts if alert.type == alert_type]
        
        return sorted(user_alerts, key=lambda x: x.created_at, reverse=True)[:limit]
    
    async def dismiss_alert(self, user_id: str, alert_id: str):
        """Mark alert as dismissed"""
        user_alerts = self.alert_history.get(user_id, [])
        for alert in user_alerts:
            if alert.id == alert_id:
                alert.metadata['dismissed'] = True
                alert.metadata['dismissed_at'] = datetime.utcnow().isoformat()
                logger.info(f"Alert {alert_id} dismissed by user {user_id}")
                break
    
    async def snooze_alert(self, user_id: str, alert_id: str, snooze_until: datetime):
        """Snooze alert until specified time"""
        user_alerts = self.alert_history.get(user_id, [])
        for alert in user_alerts:
            if alert.id == alert_id:
                alert.metadata['snoozed'] = True
                alert.metadata['snooze_until'] = snooze_until.isoformat()
                logger.info(f"Alert {alert_id} snoozed until {snooze_until} by user {user_id}")
                break


class AlertTemplateEngine:
    """Template engine for alert formatting"""
    
    def __init__(self):
        self.templates = self._load_templates()
    
    def _load_templates(self) -> Dict[str, Template]:
        """Load alert templates"""
        templates = {
            # Email templates
            'email_subject_rebalancing': Template("⚖️ Portfolio Rebalancing Needed - {{ alert.data.max_drift }}% Drift"),
            'email_subject_drawdown': Template("📉 Portfolio Drawdown Alert - {{ alert.data.current_drawdown }}%"),
            'email_subject_goal_progress': Template("🎯 Goal Milestone Reached - {{ alert.data.milestone_achieved }}%"),
            'email_subject_tax_harvesting': Template("💰 Tax Harvesting Opportunity - ${{ alert.data.total_potential_savings|int }}"),
            'email_subject_market_regime': Template("📊 Market Regime Change - {{ alert.data.current_regime|title }}"),
            'email_subject_default': Template("📊 {{ alert.title }} - Financial Alert"),
            
            # HTML email templates
            'email_html_rebalancing': Template("""
                <html>
                <head>
                    <style>
                        body { font-family: Arial, sans-serif; margin: 20px; }
                        .header { background-color: #f4f4f4; padding: 20px; border-radius: 10px; }
                        .content { margin: 20px 0; }
                        .action-button { 
                            background-color: #007bff; 
                            color: white; 
                            padding: 12px 24px; 
                            text-decoration: none; 
                            border-radius: 5px; 
                            display: inline-block; 
                            margin: 10px 0;
                        }
                        .drift-table { width: 100%; border-collapse: collapse; margin: 15px 0; }
                        .drift-table th, .drift-table td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                        .drift-table th { background-color: #f2f2f2; }
                        .high-drift { color: #dc3545; font-weight: bold; }
                    </style>
                </head>
                <body>
                    <div class="header">
                        <h2>⚖️ Portfolio Rebalancing Needed</h2>
                        <p>Your portfolio has drifted <strong>{{ alert.data.max_drift }}%</strong> from your target allocation.</p>
                    </div>
                    <div class="content">
                        <p>{{ alert.data.total_assets_drifted }} assets need rebalancing to maintain your investment strategy:</p>
                        
                        <table class="drift-table">
                            <tr>
                                <th>Asset</th>
                                <th>Current %</th>
                                <th>Target %</th>
                                <th>Drift</th>
                                <th>$ Amount</th>
                            </tr>
                            {% for asset in alert.data.drifted_assets %}
                            <tr>
                                <td>{{ asset.symbol }}</td>
                                <td>{{ asset.current_weight }}%</td>
                                <td>{{ asset.target_weight }}%</td>
                                <td class="{% if asset.drift > 7 %}high-drift{% endif %}">{{ asset.drift }}%</td>
                                <td>${{ asset.dollar_drift|int }}</td>
                            </tr>
                            {% endfor %}
                        </table>
                        
                        <p><strong>Total rebalancing value:</strong> ${{ alert.data.rebalance_value|int }}</p>
                        
                        {% if alert.action_url %}
                        <a href="{{ alert.action_url }}" class="action-button">Rebalance Now</a>
                        {% endif %}
                    </div>
                </body>
                </html>
            """),
            
            'email_html_drawdown': Template("""
                <html>
                <head>
                    <style>
                        body { font-family: Arial, sans-serif; margin: 20px; }
                        .header { background-color: #fff3cd; padding: 20px; border-radius: 10px; border-left: 5px solid #ffc107; }
                        .content { margin: 20px 0; }
                        .action-button { 
                            background-color: #ffc107; 
                            color: #212529; 
                            padding: 12px 24px; 
                            text-decoration: none; 
                            border-radius: 5px; 
                            display: inline-block; 
                            margin: 10px 0;
                        }
                        .metric { 
                            background-color: #f8f9fa; 
                            padding: 15px; 
                            margin: 10px 0; 
                            border-radius: 5px; 
                            border-left: 4px solid #ffc107;
                        }
                    </style>
                </head>
                <body>
                    <div class="header">
                        <h2>📉 Portfolio Drawdown Alert</h2>
                        <p>Your portfolio has declined <strong>{{ alert.data.current_drawdown }}%</strong> from its recent high.</p>
                    </div>
                    <div class="content">
                        <div class="metric">
                            <strong>Current Value:</strong> ${{ alert.data.current_value|int }}<br>
                            <strong>Peak Value:</strong> ${{ alert.data.high_water_mark|int }}<br>
                            <strong>Decline Amount:</strong> ${{ alert.data.value_from_peak|int }}
                        </div>
                        
                        {% if alert.data.max_drawdown_in_period > 10 %}
                        <p><strong>Note:</strong> This represents your maximum drawdown of {{ alert.data.max_drawdown_in_period }}% in the recent period.</p>
                        {% endif %}
                        
                        <p>Consider reviewing your risk tolerance and portfolio allocation during this market downturn.</p>
                        
                        {% if alert.action_url %}
                        <a href="{{ alert.action_url }}" class="action-button">Review Risk Settings</a>
                        {% endif %}
                    </div>
                </body>
                </html>
            """),
            
            'email_html_goal_progress': Template("""
                <html>
                <head>
                    <style>
                        body { font-family: Arial, sans-serif; margin: 20px; }
                        .header { background-color: #d4edda; padding: 20px; border-radius: 10px; border-left: 5px solid #28a745; }
                        .content { margin: 20px 0; }
                        .progress-bar { 
                            width: 100%; 
                            height: 25px; 
                            background-color: #e9ecef; 
                            border-radius: 15px; 
                            overflow: hidden;
                            margin: 15px 0;
                        }
                        .progress-fill { 
                            height: 100%; 
                            background-color: #28a745; 
                            width: {{ alert.data.progress_percentage }}%; 
                            transition: width 0.3s ease;
                        }
                        .milestone { 
                            background-color: #f8f9fa; 
                            padding: 15px; 
                            margin: 10px 0; 
                            border-radius: 5px; 
                            border-left: 4px solid #28a745;
                        }
                    </style>
                </head>
                <body>
                    <div class="header">
                        <h2>🎯 Goal Milestone Reached!</h2>
                        <p>Congratulations! You've reached <strong>{{ alert.data.milestone_achieved }}%</strong> of your "{{ alert.data.goal_name }}" goal.</p>
                    </div>
                    <div class="content">
                        <div class="milestone">
                            <strong>Current Progress:</strong> {{ alert.data.progress_percentage }}%<br>
                            <strong>Current Amount:</strong> ${{ alert.data.current_amount|int }}<br>
                            <strong>Target Amount:</strong> ${{ alert.data.target_amount|int }}<br>
                            <strong>Remaining:</strong> ${{ (alert.data.target_amount - alert.data.current_amount)|int }}
                        </div>
                        
                        <div class="progress-bar">
                            <div class="progress-fill"></div>
                        </div>
                        
                        <p>{% if alert.data.on_track %}You're on track to reach your goal!{% else %}Consider increasing contributions to stay on track.{% endif %}</p>
                        
                        {% if alert.data.new_milestones|length > 1 %}
                        <p><strong>New milestones achieved:</strong> {{ alert.data.new_milestones|join(', ') }}%</p>
                        {% endif %}
                    </div>
                </body>
                </html>
            """),
            
            'email_html_tax_harvesting': Template("""
                <html>
                <head>
                    <style>
                        body { font-family: Arial, sans-serif; margin: 20px; }
                        .header { background-color: #d1ecf1; padding: 20px; border-radius: 10px; border-left: 5px solid #17a2b8; }
                        .content { margin: 20px 0; }
                        .action-button { 
                            background-color: #17a2b8; 
                            color: white; 
                            padding: 12px 24px; 
                            text-decoration: none; 
                            border-radius: 5px; 
                            display: inline-block; 
                            margin: 10px 0;
                        }
                        .opportunity-table { width: 100%; border-collapse: collapse; margin: 15px 0; }
                        .opportunity-table th, .opportunity-table td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                        .opportunity-table th { background-color: #f2f2f2; }
                        .warning { background-color: #f8d7da; color: #721c24; padding: 10px; border-radius: 5px; margin: 10px 0; }
                    </style>
                </head>
                <body>
                    <div class="header">
                        <h2>💰 Tax-Loss Harvesting Opportunity</h2>
                        <p>We've identified <strong>{{ alert.data.opportunities_count }}</strong> tax-loss harvesting opportunities with potential savings of <strong>${{ alert.data.total_potential_savings|int }}</strong>.</p>
                    </div>
                    <div class="content">
                        <p>The following positions are eligible for tax-loss harvesting:</p>
                        
                        <table class="opportunity-table">
                            <tr>
                                <th>Asset</th>
                                <th>Loss Amount</th>
                                <th>Tax Savings</th>
                                <th>Holding Period</th>
                            </tr>
                            {% for opp in alert.data.opportunities %}
                            <tr>
                                <td>{{ opp.symbol }}</td>
                                <td>-${{ opp.loss|int }}</td>
                                <td>${{ opp.tax_savings|int }}</td>
                                <td>{{ opp.days_held }} days</td>
                            </tr>
                            {% endfor %}
                        </table>
                        
                        {% if alert.data.wash_sale_warnings %}
                        <div class="warning">
                            <strong>⚠️ Wash Sale Risk:</strong> Some positions may be subject to wash sale rules. Review carefully before proceeding.
                        </div>
                        {% endif %}
                        
                        {% if alert.action_url %}
                        <a href="{{ alert.action_url }}" class="action-button">Review Opportunities</a>
                        {% endif %}
                    </div>
                </body>
                </html>
            """),
            
            'email_html_market_regime': Template("""
                <html>
                <head>
                    <style>
                        body { font-family: Arial, sans-serif; margin: 20px; }
                        .header { background-color: #e2e3e5; padding: 20px; border-radius: 10px; border-left: 5px solid #6c757d; }
                        .content { margin: 20px 0; }
                        .action-button { 
                            background-color: #6c757d; 
                            color: white; 
                            padding: 12px 24px; 
                            text-decoration: none; 
                            border-radius: 5px; 
                            display: inline-block; 
                            margin: 10px 0;
                        }
                        .regime-info { 
                            background-color: #f8f9fa; 
                            padding: 15px; 
                            margin: 10px 0; 
                            border-radius: 5px; 
                            border-left: 4px solid #6c757d;
                        }
                        .implications, .actions { 
                            background-color: #fff3cd; 
                            padding: 15px; 
                            margin: 15px 0; 
                            border-radius: 5px;
                        }
                        .implications h4, .actions h4 { margin-top: 0; }
                    </style>
                </head>
                <body>
                    <div class="header">
                        <h2>📊 Market Regime Change Detected</h2>
                        <p>Market conditions have shifted from <strong>{{ alert.data.previous_regime|title }}</strong> to <strong>{{ alert.data.current_regime|title }}</strong>.</p>
                    </div>
                    <div class="content">
                        <div class="regime-info">
                            <strong>Regime Stability:</strong> {{ alert.data.regime_stability }}%<br>
                            <strong>Volatility Level:</strong> {{ (alert.data.volatility_level * 100)|round(1) }}%<br>
                            <strong>Correlation Level:</strong> {{ (alert.data.correlation_level * 100)|round(1) }}%
                        </div>
                        
                        <div class="implications">
                            <h4>Market Implications:</h4>
                            <ul>
                                {% for implication in alert.data.implications %}
                                <li>{{ implication }}</li>
                                {% endfor %}
                            </ul>
                        </div>
                        
                        <div class="actions">
                            <h4>Recommended Actions:</h4>
                            <ul>
                                {% for action in alert.data.recommended_actions %}
                                <li>{{ action }}</li>
                                {% endfor %}
                            </ul>
                        </div>
                        
                        {% if alert.action_url %}
                        <a href="{{ alert.action_url }}" class="action-button">Review Portfolio Strategy</a>
                        {% endif %}
                    </div>
                </body>
                </html>
            """),
            
            # SMS templates
            'sms_rebalancing': Template("⚖️ Portfolio drift {{ alert.data.max_drift }}%. {{ alert.data.total_assets_drifted }} assets need rebalancing. Total: ${{ alert.data.rebalance_value|int }}"),
            'sms_drawdown': Template("📉 Portfolio down {{ alert.data.current_drawdown }}% from peak. Current: ${{ alert.data.current_value|int }}"),
            'sms_goal_progress': Template("🎯 {{ alert.data.milestone_achieved }}% milestone reached for {{ alert.data.goal_name }}!"),
            'sms_tax_harvesting': Template("💰 {{ alert.data.opportunities_count }} tax harvesting opportunities. Potential savings: ${{ alert.data.total_potential_savings|int }}"),
            'sms_market_regime': Template("📊 Market regime: {{ alert.data.previous_regime }} → {{ alert.data.current_regime }}. Review strategy."),
            'sms_default': Template("{{ alert.title }}: {{ alert.message[:100] }}"),
            
            # Push notification templates
            'push_title_rebalancing': Template("Portfolio Rebalancing Needed"),
            'push_body_rebalancing': Template("{{ alert.data.max_drift }}% drift detected. {{ alert.data.total_assets_drifted }} assets need attention."),
            'push_title_drawdown': Template("Portfolio Drawdown Alert"),
            'push_body_drawdown': Template("Down {{ alert.data.current_drawdown }}% from recent high."),
            'push_title_goal_progress': Template("Goal Milestone Reached! 🎯"),
            'push_body_goal_progress': Template("{{ alert.data.milestone_achieved }}% of {{ alert.data.goal_name }} achieved!"),
            'push_title_tax_harvesting': Template("Tax Harvesting Opportunity"),
            'push_body_tax_harvesting': Template("${{ alert.data.total_potential_savings|int }} potential tax savings available."),
            'push_title_market_regime': Template("Market Regime Change"),
            'push_body_market_regime': Template("Changed to {{ alert.data.current_regime }} regime. Review recommended."),
            'push_title_default': Template("{{ alert.title }}"),
            'push_body_default': Template("{{ alert.message[:150] }}"),
        }
        return templates
    
    def generate_email(self, alert: Alert, user: Dict[str, Any]) -> tuple:
        """Generate email content using sophisticated templates"""
        # Determine template based on alert type
        alert_type_key = alert.type.value.lower()
        
        # Generate subject
        subject_template_key = f'email_subject_{alert_type_key}'
        if subject_template_key in self.templates:
            subject = self.templates[subject_template_key].render(alert=alert, user=user)
        else:
            subject = self.templates['email_subject_default'].render(alert=alert, user=user)
        
        # Generate HTML content
        html_template_key = f'email_html_{alert_type_key}'
        if html_template_key in self.templates:
            html = self.templates[html_template_key].render(alert=alert, user=user)
        else:
            # Fallback to basic template
            html = f"""
                <html>
                <head>
                    <style>
                        body {{ font-family: Arial, sans-serif; margin: 20px; }}
                        .header {{ background-color: #f4f4f4; padding: 20px; border-radius: 10px; }}
                        .content {{ margin: 20px 0; }}
                    </style>
                </head>
                <body>
                    <div class="header">
                        <h2>{alert.title}</h2>
                        <p>{alert.message}</p>
                    </div>
                    <div class="content">
                        <p>Alert Details:</p>
                        <ul>
                            <li><strong>Priority:</strong> {alert.priority.value.title()}</li>
                            <li><strong>Created:</strong> {alert.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}</li>
                        </ul>
                        {f'<p><a href="{alert.action_url}" style="background-color: #007bff; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px;">Take Action</a></p>' if alert.action_url else ''}
                    </div>
                </body>
                </html>
            """
        
        # Generate text content
        text = self._generate_text_content(alert)
        
        return subject, {'html': html, 'text': text}
    
    def _generate_text_content(self, alert: Alert) -> str:
        """Generate plain text email content"""
        text_content = f"{alert.title}\n{'='*len(alert.title)}\n\n{alert.message}\n\n"
        
        if alert.data:
            text_content += "Alert Details:\n"
            for key, value in alert.data.items():
                if isinstance(value, (list, dict)):
                    continue  # Skip complex data in text emails
                text_content += f"• {key.replace('_', ' ').title()}: {value}\n"
            text_content += "\n"
        
        text_content += f"Priority: {alert.priority.value.title()}\n"
        text_content += f"Created: {alert.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
        
        if alert.action_url:
            text_content += f"\nTake action: {alert.action_url}\n"
        
        return text_content
    
    def generate_sms(self, alert: Alert) -> str:
        """Generate SMS content using alert-specific templates"""
        alert_type_key = alert.type.value.lower()
        
        sms_template_key = f'sms_{alert_type_key}'
        if sms_template_key in self.templates:
            message = self.templates[sms_template_key].render(alert=alert)
        else:
            message = self.templates['sms_default'].render(alert=alert)
        
        # Ensure SMS doesn't exceed 160 characters
        return message[:160]
    
    def generate_push(self, alert: Alert) -> Dict[str, Any]:
        """Generate push notification content using alert-specific templates"""
        alert_type_key = alert.type.value.lower()
        
        # Generate title
        title_template_key = f'push_title_{alert_type_key}'
        if title_template_key in self.templates:
            title = self.templates[title_template_key].render(alert=alert)
        else:
            title = self.templates['push_title_default'].render(alert=alert)
        
        # Generate body
        body_template_key = f'push_body_{alert_type_key}'
        if body_template_key in self.templates:
            body = self.templates[body_template_key].render(alert=alert)
        else:
            body = self.templates['push_body_default'].render(alert=alert)
        
        return {
            'title': title,
            'body': body,
            'data': {
                'alert_id': alert.id,
                'type': alert.type.value,
                'priority': alert.priority.value,
                'action_url': alert.action_url,
                'requires_action': alert.requires_action
            },
            'badge': self._get_priority_badge(alert.priority),
            'sound': 'default' if alert.priority in [AlertPriority.HIGH, AlertPriority.CRITICAL] else None
        }
    
    def _get_priority_badge(self, priority: AlertPriority) -> int:
        """Get badge count based on priority"""
        badge_map = {
            AlertPriority.LOW: 1,
            AlertPriority.MEDIUM: 1,
            AlertPriority.HIGH: 2,
            AlertPriority.CRITICAL: 3
        }
        return badge_map.get(priority, 1)


class PushNotificationService:
    """Push notification service"""
    
    async def send(self, device_token: str, title: str, body: str, data: Dict[str, Any] = None):
        """Send push notification"""
        # Implementation would use FCM, APNS, etc.
        logger.info(f"Push notification sent: {title}")


class WebhookService:
    """Webhook delivery service"""
    
    async def send(self, url: str, data: Dict[str, Any], secret: str = None):
        """Send webhook"""
        headers = {'Content-Type': 'application/json'}
        if secret:
            # Add HMAC signature for security
            import hmac
            import hashlib
            signature = hmac.new(
                secret.encode(),
                json.dumps(data).encode(),
                hashlib.sha256
            ).hexdigest()
            headers['X-Signature'] = signature
        
        async with httpx.AsyncClient() as client:
            await client.post(url, json=data, headers=headers)