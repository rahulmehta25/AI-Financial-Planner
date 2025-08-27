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
        
        tasks = []
        for channel in channels:
            if channel in self.delivery_channels:
                tasks.append(self._send_via_channel(alert, channel))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Log delivery results
        for channel, result in zip(channels, results):
            if isinstance(result, Exception):
                logger.error(f"Failed to send alert via {channel}: {result}")
            else:
                logger.info(f"Alert sent via {channel} to user {alert.user_id}")
    
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


class AlertTemplateEngine:
    """Template engine for alert formatting"""
    
    def __init__(self):
        self.templates = self._load_templates()
    
    def _load_templates(self) -> Dict[str, Template]:
        """Load alert templates"""
        templates = {
            'email_subject': Template("{{ alert.title }} - Financial Planner Alert"),
            'email_html': Template("""
                <html>
                <body>
                    <h2>{{ alert.title }}</h2>
                    <p>{{ alert.message }}</p>
                    {% if alert.data %}
                    <ul>
                    {% for key, value in alert.data.items() %}
                        <li><strong>{{ key }}:</strong> {{ value }}</li>
                    {% endfor %}
                    </ul>
                    {% endif %}
                    {% if alert.action_url %}
                    <a href="{{ alert.action_url }}">Take Action</a>
                    {% endif %}
                </body>
                </html>
            """),
            'sms': Template("{{ alert.title }}: {{ alert.message[:100] }}{% if alert.requires_action %} - Action required{% endif %}"),
            'push_title': Template("{{ alert.title }}"),
            'push_body': Template("{{ alert.message[:150] }}")
        }
        return templates
    
    def generate_email(self, alert: Alert, user: Dict[str, Any]) -> tuple:
        """Generate email content"""
        subject = self.templates['email_subject'].render(alert=alert, user=user)
        html = self.templates['email_html'].render(alert=alert, user=user)
        text = f"{alert.title}\n\n{alert.message}"
        
        return subject, {'html': html, 'text': text}
    
    def generate_sms(self, alert: Alert) -> str:
        """Generate SMS content (160 char limit)"""
        return self.templates['sms'].render(alert=alert)[:160]
    
    def generate_push(self, alert: Alert) -> Dict[str, Any]:
        """Generate push notification content"""
        return {
            'title': self.templates['push_title'].render(alert=alert),
            'body': self.templates['push_body'].render(alert=alert),
            'data': {
                'alert_id': alert.id,
                'type': alert.type.value,
                'priority': alert.priority.value
            }
        }


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