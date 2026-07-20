"""
Notification Service

Service for sending various types of notifications for market alerts.
"""

import asyncio
import logging
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import aiohttp
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart

from ..models import AlertConfig, PriceAlert
from ..config import config


class NotificationService:
    """Service for sending alert notifications"""
    
    def __init__(self):
        self.logger = logging.getLogger("market_data.notification_service")
        self._session: Optional[aiohttp.ClientSession] = None
        
        # Email configuration
        self.smtp_server = getattr(config, 'smtp_server', 'smtp.gmail.com')
        self.smtp_port = getattr(config, 'smtp_port', 587)
        self.smtp_username = getattr(config, 'smtp_username', None)
        self.smtp_password = getattr(config, 'smtp_password', None)
        self.from_email = getattr(config, 'from_email', None)
        
        # Push notification configuration
        self.push_service_url = getattr(config, 'push_service_url', None)
        self.push_api_key = getattr(config, 'push_api_key', None)
        
        # Statistics
        self.emails_sent = 0
        self.push_notifications_sent = 0
        self.webhooks_sent = 0
        self.notification_errors = 0
    
    async def initialize(self):
        """Initialize the notification service"""
        try:
            # Initialize HTTP session for webhooks and push notifications
            timeout = aiohttp.ClientTimeout(total=30)
            self._session = aiohttp.ClientSession(timeout=timeout)
            
            self.logger.info("Notification service initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize notification service: {e}")
            raise
    
    async def shutdown(self):
        """Shutdown the notification service"""
        if self._session:
            await self._session.close()
        
        self.logger.info("Notification service shutdown")
    
    async def send_email_alert(self, alert_config: AlertConfig, alert_instance: PriceAlert) -> bool:
        """Send email notification for alert"""
        try:
            if not self._is_email_configured():
                self.logger.warning("Email not configured, skipping email notification")
                return False
            
            # Get user email (would typically come from user service)
            user_email = await self._get_user_email(alert_config.user_id)
            if not user_email:
                self.logger.error(f"No email found for user {alert_config.user_id}")
                return False
            
            # Create email content
            subject = self._create_email_subject(alert_config, alert_instance)
            body = self._create_email_body(alert_config, alert_instance)
            
            # Send email in background to avoid blocking
            asyncio.create_task(self._send_email_async(user_email, subject, body))
            
            self.emails_sent += 1
            return True
            
        except Exception as e:
            self.notification_errors += 1
            self.logger.error(f"Error sending email alert: {e}")
            return False
    
    async def send_push_alert(self, alert_config: AlertConfig, alert_instance: PriceAlert) -> bool:
        """Send push notification for alert"""
        try:
            if not self._is_push_configured():
                self.logger.warning("Push notifications not configured")
                return False
            
            # Get user push tokens (would typically come from user service)
            push_tokens = await self._get_user_push_tokens(alert_config.user_id)
            if not push_tokens:
                self.logger.warning(f"No push tokens found for user {alert_config.user_id}")
                return False
            
            # Create push notification payload
            payload = self._create_push_payload(alert_config, alert_instance)
            
            # Send to all user's devices
            success_count = 0
            for token in push_tokens:
                success = await self._send_push_notification(token, payload)
                if success:
                    success_count += 1
            
            if success_count > 0:
                self.push_notifications_sent += success_count
                return True
            
            return False
            
        except Exception as e:
            self.notification_errors += 1
            self.logger.error(f"Error sending push alert: {e}")
            return False
    
    async def send_webhook_alert(self, alert_config: AlertConfig, alert_instance: PriceAlert) -> bool:
        """Send webhook notification for alert"""
        try:
            if not alert_config.webhook_url:
                return False
            
            # Create webhook payload
            payload = self._create_webhook_payload(alert_config, alert_instance)
            
            # Send webhook
            success = await self._send_webhook(alert_config.webhook_url, payload)
            
            if success:
                self.webhooks_sent += 1
                return True
            
            return False
            
        except Exception as e:
            self.notification_errors += 1
            self.logger.error(f"Error sending webhook alert: {e}")
            return False
    
    def _is_email_configured(self) -> bool:
        """Check if email is properly configured"""
        return all([
            self.smtp_server,
            self.smtp_username,
            self.smtp_password,
            self.from_email
        ])
    
    def _is_push_configured(self) -> bool:
        """Check if push notifications are properly configured"""
        return all([
            self.push_service_url,
            self.push_api_key
        ])
    
    async def _get_user_email(self, user_id: str) -> Optional[str]:
        """Get user email address"""
        # This would typically integrate with your user service
        # For now, return a placeholder
        self.logger.debug(f"Getting email for user {user_id}")
        
        # In a real implementation, you would:
        # 1. Query your user database
        # 2. Or call a user service API
        # 3. Return the user's email address
        
        return f"user_{user_id}@example.com"  # Placeholder
    
    async def _get_user_push_tokens(self, user_id: str) -> List[str]:
        """Get user push notification tokens"""
        # This would typically integrate with your user service
        # For now, return a placeholder
        self.logger.debug(f"Getting push tokens for user {user_id}")
        
        # In a real implementation, you would:
        # 1. Query your user database for device tokens
        # 2. Return a list of valid push tokens
        
        return []  # Placeholder
    
    def _create_email_subject(self, alert_config: AlertConfig, alert_instance: PriceAlert) -> str:
        """Create email subject line"""
        return f"Market Alert: {alert_instance.symbol} - {alert_config.alert_type.value.replace('_', ' ').title()}"
    
    def _create_email_body(self, alert_config: AlertConfig, alert_instance: PriceAlert) -> str:
        """Create email body content"""
        timestamp = alert_instance.trigger_timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")
        
        body = f"""
Market Alert Triggered

Symbol: {alert_instance.symbol}
Alert Type: {alert_config.alert_type.value.replace('_', ' ').title()}
Trigger Price: ${alert_instance.trigger_price}
Triggered At: {timestamp}

Message: {alert_instance.message}

Alert Details:
- Alert ID: {alert_config.id}
- Created: {alert_config.created_at.strftime("%Y-%m-%d %H:%M:%S UTC")}
"""
        
        if alert_config.alert_type.value in ['price_above', 'price_below']:
            body += f"- Threshold: ${alert_config.threshold_value}\n"
        elif alert_config.alert_type.value == 'price_change_percent':
            body += f"- Percentage Threshold: {alert_config.percentage_threshold}%\n"
            body += f"- Actual Change: {alert_instance.trigger_value}%\n"
        
        body += f"""
This is an automated message from your Financial Planning Market Data System.
If you wish to modify or disable this alert, please log into your account.
"""
        
        return body
    
    def _create_push_payload(self, alert_config: AlertConfig, alert_instance: PriceAlert) -> Dict[str, Any]:
        """Create push notification payload"""
        return {
            "title": f"{alert_instance.symbol} Alert",
            "body": alert_instance.message,
            "data": {
                "alert_id": alert_config.id,
                "symbol": alert_instance.symbol,
                "price": str(alert_instance.trigger_price),
                "alert_type": alert_config.alert_type.value,
                "timestamp": alert_instance.trigger_timestamp.isoformat()
            },
            "badge": 1,
            "sound": "default"
        }
    
    def _create_webhook_payload(self, alert_config: AlertConfig, alert_instance: PriceAlert) -> Dict[str, Any]:
        """Create webhook payload"""
        return {
            "event": "market_alert_triggered",
            "timestamp": alert_instance.trigger_timestamp.isoformat(),
            "alert": {
                "id": alert_config.id,
                "user_id": alert_config.user_id,
                "symbol": alert_instance.symbol,
                "alert_type": alert_config.alert_type.value,
                "threshold_value": str(alert_config.threshold_value) if alert_config.threshold_value else None,
                "percentage_threshold": str(alert_config.percentage_threshold) if alert_config.percentage_threshold else None
            },
            "trigger": {
                "price": str(alert_instance.trigger_price),
                "value": str(alert_instance.trigger_value) if alert_instance.trigger_value else None,
                "message": alert_instance.message
            }
        }
    
    async def _send_email_async(self, to_email: str, subject: str, body: str):
        """Send email asynchronously"""
        try:
            # Create message
            msg = MimeMultipart()
            msg['From'] = self.from_email
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Add body
            msg.attach(MimeText(body, 'plain'))
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            self.logger.info(f"Email sent successfully to {to_email}")
            
        except Exception as e:
            self.notification_errors += 1
            self.logger.error(f"Error sending email to {to_email}: {e}")
    
    async def _send_push_notification(self, push_token: str, payload: Dict[str, Any]) -> bool:
        """Send push notification to a device"""
        try:
            if not self._session:
                return False
            
            headers = {
                'Authorization': f'Bearer {self.push_api_key}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'to': push_token,
                **payload
            }
            
            async with self._session.post(
                self.push_service_url,
                headers=headers,
                json=data
            ) as response:
                if response.status == 200:
                    self.logger.debug(f"Push notification sent to {push_token[:10]}...")
                    return True
                else:
                    error_text = await response.text()
                    self.logger.error(f"Push notification failed: {response.status} - {error_text}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"Error sending push notification: {e}")
            return False
    
    async def _send_webhook(self, webhook_url: str, payload: Dict[str, Any]) -> bool:
        """Send webhook notification"""
        try:
            if not self._session:
                return False
            
            headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'Financial-Planning-Market-Data/1.0'
            }
            
            async with self._session.post(
                webhook_url,
                headers=headers,
                json=payload
            ) as response:
                if 200 <= response.status < 300:
                    self.logger.debug(f"Webhook sent successfully to {webhook_url}")
                    return True
                else:
                    error_text = await response.text()
                    self.logger.error(f"Webhook failed: {response.status} - {error_text}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"Error sending webhook to {webhook_url}: {e}")
            return False
    
    async def send_test_notifications(self, user_id: str, notification_types: List[str] = None) -> Dict[str, bool]:
        """Send test notifications to verify configuration"""
        if notification_types is None:
            notification_types = ['email', 'push', 'webhook']
        
        results = {}
        
        # Create test alert data
        test_alert_config = AlertConfig(
            user_id=user_id,
            symbol="TEST",
            alert_type="price_above",
            threshold_value=100.0,
            webhook_url="https://httpbin.org/post" if 'webhook' in notification_types else None
        )
        
        test_alert_instance = PriceAlert(
            alert_config_id=test_alert_config.id,
            user_id=user_id,
            symbol="TEST",
            alert_type="price_above",
            trigger_price=105.0,
            message="This is a test alert notification"
        )
        
        # Send test notifications
        if 'email' in notification_types:
            results['email'] = await self.send_email_alert(test_alert_config, test_alert_instance)
        
        if 'push' in notification_types:
            results['push'] = await self.send_push_alert(test_alert_config, test_alert_instance)
        
        if 'webhook' in notification_types:
            results['webhook'] = await self.send_webhook_alert(test_alert_config, test_alert_instance)
        
        return results
    
    def get_notification_stats(self) -> Dict[str, Any]:
        """Get notification service statistics"""
        return {
            "emails_sent": self.emails_sent,
            "push_notifications_sent": self.push_notifications_sent,
            "webhooks_sent": self.webhooks_sent,
            "notification_errors": self.notification_errors,
            "total_notifications": self.emails_sent + self.push_notifications_sent + self.webhooks_sent,
            "configuration": {
                "email_configured": self._is_email_configured(),
                "push_configured": self._is_push_configured(),
                "smtp_server": self.smtp_server,
                "smtp_port": self.smtp_port,
                "from_email": self.from_email
            }
        }
    
    def reset_stats(self):
        """Reset notification statistics"""
        self.emails_sent = 0
        self.push_notifications_sent = 0
        self.webhooks_sent = 0
        self.notification_errors = 0
        self.logger.info("Notification statistics reset")