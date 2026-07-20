"""
Notification Service for Multi-Channel Alert Delivery
Handles email, SMS, push notifications, and webhooks
"""

import asyncio
import json
import hmac
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from enum import Enum
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from twilio.rest import Client as TwilioClient
import httpx
from jinja2 import Environment, FileSystemLoader, Template
import firebase_admin
from firebase_admin import credentials, messaging
from apns2.client import APNsClient
from apns2.payload import Payload

from app.core.config import Config
from app.services.base.logging_service import LoggingService
from app.services.monitoring.alert_engine import Alert, AlertPriority

logger = LoggingService(__name__)


class NotificationChannel(Enum):
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    WEBHOOK = "webhook"
    IN_APP = "in_app"
    SLACK = "slack"
    TELEGRAM = "telegram"


@dataclass
class NotificationPreferences:
    """User notification preferences"""
    user_id: str
    email_enabled: bool = True
    sms_enabled: bool = False
    push_enabled: bool = True
    webhook_enabled: bool = False
    in_app_enabled: bool = True
    quiet_hours: Optional[tuple] = None  # (start_hour, end_hour) in UTC
    priority_threshold: AlertPriority = AlertPriority.MEDIUM
    channels_by_type: Dict[str, List[NotificationChannel]] = field(default_factory=dict)
    email_frequency: str = "immediate"  # immediate, hourly, daily
    sms_for_critical_only: bool = True


@dataclass
class NotificationResult:
    """Result of notification delivery"""
    channel: NotificationChannel
    success: bool
    timestamp: datetime = field(default_factory=datetime.utcnow)
    error: Optional[str] = None
    delivery_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class NotificationBatch:
    """Batch of notifications for digest delivery"""
    user_id: str
    alerts: List[Alert] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    scheduled_for: Optional[datetime] = None


class NotificationService:
    """Main notification service for multi-channel delivery"""
    
    def __init__(self):
        self.email_client = self._setup_email_client()
        self.sms_client = self._setup_sms_client()
        self.push_clients = self._setup_push_clients()
        self.template_env = self._setup_templates()
        self.notification_queue: asyncio.Queue = asyncio.Queue()
        self.batch_queues: Dict[str, NotificationBatch] = {}
        self.delivery_history: Dict[str, List[NotificationResult]] = {}
        self.rate_limiters: Dict[str, RateLimiter] = {}
        self.running = False
        logger.info("Notification Service initialized")
    
    def _setup_email_client(self) -> Optional[aiosmtplib.SMTP]:
        """Setup email client"""
        if Config.SMTP_HOST:
            return aiosmtplib.SMTP(
                hostname=Config.SMTP_HOST,
                port=Config.SMTP_PORT,
                username=Config.SMTP_USERNAME,
                password=Config.SMTP_PASSWORD,
                use_tls=True
            )
        return None
    
    def _setup_sms_client(self) -> Optional[TwilioClient]:
        """Setup SMS client"""
        if Config.TWILIO_ACCOUNT_SID and Config.TWILIO_AUTH_TOKEN:
            return TwilioClient(Config.TWILIO_ACCOUNT_SID, Config.TWILIO_AUTH_TOKEN)
        return None
    
    def _setup_push_clients(self) -> Dict[str, Any]:
        """Setup push notification clients"""
        clients = {}
        
        # Firebase Cloud Messaging for Android
        if Config.FIREBASE_CREDENTIALS:
            cred = credentials.Certificate(Config.FIREBASE_CREDENTIALS)
            firebase_admin.initialize_app(cred)
            clients['fcm'] = messaging
        
        # Apple Push Notification Service for iOS
        if Config.APNS_KEY_PATH:
            clients['apns'] = APNsClient(
                Config.APNS_KEY_PATH,
                use_sandbox=Config.APNS_USE_SANDBOX,
                topic=Config.APNS_TOPIC
            )
        
        return clients
    
    def _setup_templates(self) -> Environment:
        """Setup Jinja2 template environment"""
        return Environment(
            loader=FileSystemLoader('templates/notifications'),
            autoescape=True
        )
    
    async def start(self):
        """Start notification service"""
        self.running = True
        asyncio.create_task(self._process_queue())
        asyncio.create_task(self._process_batches())
        logger.info("Notification service started")
    
    async def stop(self):
        """Stop notification service"""
        self.running = False
        logger.info("Notification service stopped")
    
    async def send_notification(
        self,
        alert: Alert,
        user_preferences: NotificationPreferences,
        channels: Optional[List[NotificationChannel]] = None
    ) -> List[NotificationResult]:
        """Send notification through specified channels"""
        
        # Check quiet hours
        if self._in_quiet_hours(user_preferences):
            if alert.priority != AlertPriority.CRITICAL:
                return await self._queue_for_later(alert, user_preferences)
        
        # Check priority threshold
        if alert.priority.value < user_preferences.priority_threshold.value:
            return []
        
        # Determine channels
        if channels is None:
            channels = self._determine_channels(alert, user_preferences)
        
        # Check rate limits
        channels = await self._apply_rate_limits(user_preferences.user_id, channels)
        
        # Send through each channel
        results = []
        for channel in channels:
            try:
                result = await self._send_via_channel(alert, user_preferences, channel)
                results.append(result)
                
                # Store in history
                if user_preferences.user_id not in self.delivery_history:
                    self.delivery_history[user_preferences.user_id] = []
                self.delivery_history[user_preferences.user_id].append(result)
                
            except Exception as e:
                logger.error(f"Failed to send via {channel}: {e}")
                results.append(NotificationResult(
                    channel=channel,
                    success=False,
                    error=str(e)
                ))
        
        return results
    
    async def _send_via_channel(
        self,
        alert: Alert,
        preferences: NotificationPreferences,
        channel: NotificationChannel
    ) -> NotificationResult:
        """Send notification through specific channel"""
        
        if channel == NotificationChannel.EMAIL:
            return await self._send_email(alert, preferences)
        elif channel == NotificationChannel.SMS:
            return await self._send_sms(alert, preferences)
        elif channel == NotificationChannel.PUSH:
            return await self._send_push(alert, preferences)
        elif channel == NotificationChannel.WEBHOOK:
            return await self._send_webhook(alert, preferences)
        elif channel == NotificationChannel.IN_APP:
            return await self._send_in_app(alert, preferences)
        elif channel == NotificationChannel.SLACK:
            return await self._send_slack(alert, preferences)
        elif channel == NotificationChannel.TELEGRAM:
            return await self._send_telegram(alert, preferences)
        else:
            raise ValueError(f"Unknown channel: {channel}")
    
    async def _send_email(self, alert: Alert, preferences: NotificationPreferences) -> NotificationResult:
        """Send email notification"""
        if not self.email_client:
            return NotificationResult(
                channel=NotificationChannel.EMAIL,
                success=False,
                error="Email client not configured"
            )
        
        try:
            # Get user email
            user_email = await self._get_user_email(preferences.user_id)
            if not user_email:
                return NotificationResult(
                    channel=NotificationChannel.EMAIL,
                    success=False,
                    error="No email address found"
                )
            
            # Render template
            template = self.template_env.get_template('email_alert.html')
            html_content = template.render(alert=alert, user_id=preferences.user_id)
            
            # Create message
            message = MIMEMultipart('alternative')
            message['Subject'] = f"[{alert.priority.value.upper()}] {alert.title}"
            message['From'] = Config.EMAIL_FROM
            message['To'] = user_email
            message['Reply-To'] = Config.EMAIL_REPLY_TO
            
            # Add text and HTML parts
            text_part = MIMEText(alert.message, 'plain')
            html_part = MIMEText(html_content, 'html')
            
            message.attach(text_part)
            message.attach(html_part)
            
            # Add logo if available
            if Config.EMAIL_LOGO_PATH:
                with open(Config.EMAIL_LOGO_PATH, 'rb') as f:
                    logo = MIMEImage(f.read())
                    logo.add_header('Content-ID', '<logo>')
                    message.attach(logo)
            
            # Send email
            await self.email_client.send_message(message)
            
            return NotificationResult(
                channel=NotificationChannel.EMAIL,
                success=True,
                delivery_id=message['Message-ID']
            )
            
        except Exception as e:
            logger.error(f"Email delivery failed: {e}")
            return NotificationResult(
                channel=NotificationChannel.EMAIL,
                success=False,
                error=str(e)
            )
    
    async def _send_sms(self, alert: Alert, preferences: NotificationPreferences) -> NotificationResult:
        """Send SMS notification"""
        if not self.sms_client:
            return NotificationResult(
                channel=NotificationChannel.SMS,
                success=False,
                error="SMS client not configured"
            )
        
        # Check if SMS should be sent
        if preferences.sms_for_critical_only and alert.priority != AlertPriority.CRITICAL:
            return NotificationResult(
                channel=NotificationChannel.SMS,
                success=False,
                error="SMS only for critical alerts"
            )
        
        try:
            # Get user phone
            user_phone = await self._get_user_phone(preferences.user_id)
            if not user_phone:
                return NotificationResult(
                    channel=NotificationChannel.SMS,
                    success=False,
                    error="No phone number found"
                )
            
            # Create SMS message (160 char limit)
            message_text = f"{alert.title}: {alert.message}"[:160]
            
            # Send SMS
            message = self.sms_client.messages.create(
                body=message_text,
                from_=Config.TWILIO_PHONE_NUMBER,
                to=user_phone
            )
            
            return NotificationResult(
                channel=NotificationChannel.SMS,
                success=True,
                delivery_id=message.sid
            )
            
        except Exception as e:
            logger.error(f"SMS delivery failed: {e}")
            return NotificationResult(
                channel=NotificationChannel.SMS,
                success=False,
                error=str(e)
            )
    
    async def _send_push(self, alert: Alert, preferences: NotificationPreferences) -> NotificationResult:
        """Send push notification"""
        try:
            # Get user devices
            devices = await self._get_user_devices(preferences.user_id)
            if not devices:
                return NotificationResult(
                    channel=NotificationChannel.PUSH,
                    success=False,
                    error="No devices registered"
                )
            
            results = []
            
            for device in devices:
                if device['platform'] == 'android' and 'fcm' in self.push_clients:
                    # Send via FCM
                    message = messaging.Message(
                        notification=messaging.Notification(
                            title=alert.title,
                            body=alert.message[:200]
                        ),
                        data={
                            'alert_id': alert.id,
                            'type': alert.type.value,
                            'priority': alert.priority.value
                        },
                        token=device['token']
                    )
                    response = messaging.send(message)
                    results.append(response)
                    
                elif device['platform'] == 'ios' and 'apns' in self.push_clients:
                    # Send via APNS
                    payload = Payload(
                        alert=alert.message[:200],
                        badge=1,
                        sound="default",
                        custom={
                            'alert_id': alert.id,
                            'type': alert.type.value
                        }
                    )
                    self.push_clients['apns'].send_notification(
                        device['token'],
                        payload,
                        topic=Config.APNS_TOPIC
                    )
                    results.append(device['token'])
            
            return NotificationResult(
                channel=NotificationChannel.PUSH,
                success=True,
                metadata={'devices': len(devices)}
            )
            
        except Exception as e:
            logger.error(f"Push delivery failed: {e}")
            return NotificationResult(
                channel=NotificationChannel.PUSH,
                success=False,
                error=str(e)
            )
    
    async def _send_webhook(self, alert: Alert, preferences: NotificationPreferences) -> NotificationResult:
        """Send webhook notification"""
        try:
            # Get user webhooks
            webhooks = await self._get_user_webhooks(preferences.user_id)
            if not webhooks:
                return NotificationResult(
                    channel=NotificationChannel.WEBHOOK,
                    success=False,
                    error="No webhooks configured"
                )
            
            results = []
            
            async with httpx.AsyncClient() as client:
                for webhook in webhooks:
                    # Prepare payload
                    payload = {
                        'alert': alert.__dict__,
                        'timestamp': datetime.utcnow().isoformat(),
                        'user_id': preferences.user_id
                    }
                    
                    # Add signature for security
                    headers = {'Content-Type': 'application/json'}
                    if webhook.get('secret'):
                        signature = hmac.new(
                            webhook['secret'].encode(),
                            json.dumps(payload).encode(),
                            hashlib.sha256
                        ).hexdigest()
                        headers['X-Webhook-Signature'] = signature
                    
                    # Send webhook
                    response = await client.post(
                        webhook['url'],
                        json=payload,
                        headers=headers,
                        timeout=10.0
                    )
                    results.append(response.status_code == 200)
            
            return NotificationResult(
                channel=NotificationChannel.WEBHOOK,
                success=all(results),
                metadata={'webhooks_sent': len(results)}
            )
            
        except Exception as e:
            logger.error(f"Webhook delivery failed: {e}")
            return NotificationResult(
                channel=NotificationChannel.WEBHOOK,
                success=False,
                error=str(e)
            )
    
    async def _send_in_app(self, alert: Alert, preferences: NotificationPreferences) -> NotificationResult:
        """Store in-app notification"""
        try:
            # Store notification in database for frontend to fetch
            await self._store_in_app_notification(preferences.user_id, alert)
            
            # Send real-time update if user is connected
            await self._send_realtime_notification(preferences.user_id, alert)
            
            return NotificationResult(
                channel=NotificationChannel.IN_APP,
                success=True
            )
            
        except Exception as e:
            logger.error(f"In-app delivery failed: {e}")
            return NotificationResult(
                channel=NotificationChannel.IN_APP,
                success=False,
                error=str(e)
            )
    
    async def _send_slack(self, alert: Alert, preferences: NotificationPreferences) -> NotificationResult:
        """Send Slack notification"""
        try:
            # Get Slack webhook URL
            slack_config = await self._get_slack_config(preferences.user_id)
            if not slack_config:
                return NotificationResult(
                    channel=NotificationChannel.SLACK,
                    success=False,
                    error="Slack not configured"
                )
            
            # Create Slack message
            slack_message = {
                'text': alert.title,
                'attachments': [{
                    'color': self._get_slack_color(alert.priority),
                    'fields': [
                        {'title': 'Message', 'value': alert.message, 'short': False},
                        {'title': 'Priority', 'value': alert.priority.value, 'short': True},
                        {'title': 'Type', 'value': alert.type.value, 'short': True}
                    ],
                    'footer': 'Financial Planner',
                    'ts': int(datetime.utcnow().timestamp())
                }]
            }
            
            # Send to Slack
            async with httpx.AsyncClient() as client:
                response = await client.post(slack_config['webhook_url'], json=slack_message)
                
                return NotificationResult(
                    channel=NotificationChannel.SLACK,
                    success=response.status_code == 200
                )
                
        except Exception as e:
            logger.error(f"Slack delivery failed: {e}")
            return NotificationResult(
                channel=NotificationChannel.SLACK,
                success=False,
                error=str(e)
            )
    
    async def _send_telegram(self, alert: Alert, preferences: NotificationPreferences) -> NotificationResult:
        """Send Telegram notification"""
        try:
            # Get Telegram config
            telegram_config = await self._get_telegram_config(preferences.user_id)
            if not telegram_config:
                return NotificationResult(
                    channel=NotificationChannel.TELEGRAM,
                    success=False,
                    error="Telegram not configured"
                )
            
            # Create Telegram message
            message_text = f"*{alert.title}*\n\n{alert.message}\n\nPriority: {alert.priority.value}"
            
            # Send to Telegram
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"https://api.telegram.org/bot{Config.TELEGRAM_BOT_TOKEN}/sendMessage",
                    json={
                        'chat_id': telegram_config['chat_id'],
                        'text': message_text,
                        'parse_mode': 'Markdown'
                    }
                )
                
                return NotificationResult(
                    channel=NotificationChannel.TELEGRAM,
                    success=response.status_code == 200
                )
                
        except Exception as e:
            logger.error(f"Telegram delivery failed: {e}")
            return NotificationResult(
                channel=NotificationChannel.TELEGRAM,
                success=False,
                error=str(e)
            )
    
    def _in_quiet_hours(self, preferences: NotificationPreferences) -> bool:
        """Check if current time is in quiet hours"""
        if not preferences.quiet_hours:
            return False
        
        current_hour = datetime.utcnow().hour
        start_hour, end_hour = preferences.quiet_hours
        
        if start_hour <= end_hour:
            return start_hour <= current_hour < end_hour
        else:
            return current_hour >= start_hour or current_hour < end_hour
    
    def _determine_channels(
        self,
        alert: Alert,
        preferences: NotificationPreferences
    ) -> List[NotificationChannel]:
        """Determine which channels to use based on alert and preferences"""
        channels = []
        
        # Check type-specific channels
        if alert.type.value in preferences.channels_by_type:
            channels.extend(preferences.channels_by_type[alert.type.value])
        else:
            # Use default channels based on preferences
            if preferences.email_enabled:
                channels.append(NotificationChannel.EMAIL)
            if preferences.sms_enabled:
                channels.append(NotificationChannel.SMS)
            if preferences.push_enabled:
                channels.append(NotificationChannel.PUSH)
            if preferences.in_app_enabled:
                channels.append(NotificationChannel.IN_APP)
        
        # Override for critical alerts
        if alert.priority == AlertPriority.CRITICAL:
            if preferences.sms_enabled:
                channels.append(NotificationChannel.SMS)
            channels.append(NotificationChannel.PUSH)
        
        return list(set(channels))  # Remove duplicates
    
    async def _apply_rate_limits(
        self,
        user_id: str,
        channels: List[NotificationChannel]
    ) -> List[NotificationChannel]:
        """Apply rate limiting to channels"""
        if user_id not in self.rate_limiters:
            self.rate_limiters[user_id] = RateLimiter(user_id)
        
        allowed_channels = []
        for channel in channels:
            if await self.rate_limiters[user_id].check(channel):
                allowed_channels.append(channel)
        
        return allowed_channels
    
    async def _queue_for_later(
        self,
        alert: Alert,
        preferences: NotificationPreferences
    ) -> List[NotificationResult]:
        """Queue notification for later delivery"""
        user_id = preferences.user_id
        
        if user_id not in self.batch_queues:
            self.batch_queues[user_id] = NotificationBatch(user_id=user_id)
        
        self.batch_queues[user_id].alerts.append(alert)
        
        return [NotificationResult(
            channel=NotificationChannel.IN_APP,
            success=True,
            metadata={'queued': True}
        )]
    
    async def _process_queue(self):
        """Process notification queue"""
        while self.running:
            try:
                # Process immediate notifications
                await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"Queue processing error: {e}")
    
    async def _process_batches(self):
        """Process batched notifications"""
        while self.running:
            try:
                # Check for scheduled batch sends
                now = datetime.utcnow()
                
                for user_id, batch in list(self.batch_queues.items()):
                    if batch.scheduled_for and batch.scheduled_for <= now:
                        await self._send_batch(batch)
                        del self.batch_queues[user_id]
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Batch processing error: {e}")
    
    async def _send_batch(self, batch: NotificationBatch):
        """Send batched notifications"""
        # Implementation would send digest email
        pass
    
    def _get_slack_color(self, priority: AlertPriority) -> str:
        """Get Slack color for priority"""
        colors = {
            AlertPriority.LOW: '#36a64f',
            AlertPriority.MEDIUM: '#ff9900',
            AlertPriority.HIGH: '#ff6600',
            AlertPriority.CRITICAL: '#ff0000'
        }
        return colors.get(priority, '#808080')
    
    # Database access methods (would be implemented with actual database)
    async def _get_user_email(self, user_id: str) -> Optional[str]:
        return f"user_{user_id}@example.com"
    
    async def _get_user_phone(self, user_id: str) -> Optional[str]:
        return None  # Would fetch from database
    
    async def _get_user_devices(self, user_id: str) -> List[Dict[str, str]]:
        return []  # Would fetch from database
    
    async def _get_user_webhooks(self, user_id: str) -> List[Dict[str, Any]]:
        return []  # Would fetch from database
    
    async def _get_slack_config(self, user_id: str) -> Optional[Dict[str, str]]:
        return None  # Would fetch from database
    
    async def _get_telegram_config(self, user_id: str) -> Optional[Dict[str, str]]:
        return None  # Would fetch from database
    
    async def _store_in_app_notification(self, user_id: str, alert: Alert):
        # Would store in database
        pass
    
    async def _send_realtime_notification(self, user_id: str, alert: Alert):
        # Would send via WebSocket
        pass


class RateLimiter:
    """Rate limiter for notifications"""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.limits = {
            NotificationChannel.EMAIL: (10, 3600),  # 10 per hour
            NotificationChannel.SMS: (5, 3600),     # 5 per hour
            NotificationChannel.PUSH: (20, 3600),   # 20 per hour
            NotificationChannel.WEBHOOK: (50, 3600), # 50 per hour
            NotificationChannel.IN_APP: (100, 3600)  # 100 per hour
        }
        self.requests: Dict[NotificationChannel, List[datetime]] = {}
    
    async def check(self, channel: NotificationChannel) -> bool:
        """Check if request is within rate limits"""
        if channel not in self.limits:
            return True
        
        limit, window = self.limits[channel]
        now = datetime.utcnow()
        window_start = now - timedelta(seconds=window)
        
        # Initialize if needed
        if channel not in self.requests:
            self.requests[channel] = []
        
        # Clean old requests
        self.requests[channel] = [
            req_time for req_time in self.requests[channel]
            if req_time > window_start
        ]
        
        # Check limit
        if len(self.requests[channel]) >= limit:
            return False
        
        # Add request
        self.requests[channel].append(now)
        return True