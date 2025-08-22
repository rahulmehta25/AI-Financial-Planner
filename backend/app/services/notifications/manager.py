"""
Notification Manager

Main orchestrator for the notification system that coordinates:
- Multiple notification channels
- Template rendering
- Preference checking
- Delivery tracking
- Analytics
"""

import logging
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from sqlalchemy.orm import Session

from .config import notification_config
from .models import (
    NotificationChannel,
    NotificationStatus,
    NotificationPriority,
    NotificationType,
    Notification,
    NotificationLog
)
from .email_service import EmailService
from .push_service import PushNotificationService
from .sms_service import SMSService
from .in_app_service import InAppNotificationService
from .template_manager import NotificationTemplateManager
from .preferences_manager import PreferencesManager
from app.database.base import get_db


logger = logging.getLogger(__name__)


class NotificationManager:
    """Main notification manager orchestrating all services"""

    def __init__(self):
        self.email_service = EmailService()
        self.push_service = PushNotificationService()
        self.sms_service = SMSService()
        self.in_app_service = InAppNotificationService()
        self.template_manager = NotificationTemplateManager()
        self.preferences_manager = PreferencesManager()

    async def send_notification(
        self,
        user_id: int,
        channel: NotificationChannel,
        notification_type: Union[str, NotificationType],
        data: Dict[str, Any],
        recipient: Optional[str] = None,
        template_name: Optional[str] = None,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        scheduled_at: Optional[datetime] = None,
        force_send: bool = False
    ) -> Dict[str, Any]:
        """Send notification through specified channel"""
        try:
            # Convert string to enum if needed
            if isinstance(notification_type, str):
                try:
                    notification_type = NotificationType(notification_type)
                except ValueError:
                    return {"status": "error", "error": f"Invalid notification type: {notification_type}"}

            # Check user preferences (unless forced)
            if not force_send:
                permission_check = await self.preferences_manager.check_notification_allowed(
                    user_id=user_id,
                    channel=channel,
                    notification_type=notification_type
                )
                
                if not permission_check.get("allowed", False):
                    return {
                        "status": "blocked",
                        "reason": permission_check.get("reason"),
                        "details": permission_check
                    }

            # Get user information for template rendering
            user_info = await self._get_user_info(user_id)
            if not user_info:
                return {"status": "error", "error": "User not found"}

            # Prepare template data
            template_data = {
                **data,
                **user_info,
                "notification_type": notification_type.value,
                "channel": channel.value,
                "priority": priority.value
            }

            # Render template
            template_name = template_name or notification_type.value
            rendered_content = await self.template_manager.render_template(
                channel=channel,
                template_name=template_name,
                template_data=template_data,
                notification_type=notification_type
            )

            # Get recipient if not provided
            if not recipient:
                recipient = await self._get_recipient_for_channel(user_id, channel)
                if not recipient:
                    return {"status": "error", "error": f"No recipient configured for {channel.value}"}

            # Create notification record
            db_notification = await self._create_notification_record(
                user_id=user_id,
                channel=channel,
                notification_type=notification_type,
                priority=priority,
                subject=rendered_content.get("subject", ""),
                body=rendered_content.get("body", ""),
                html_body=rendered_content.get("html_body"),
                data=template_data,
                recipient=recipient,
                scheduled_at=scheduled_at
            )

            # Send through appropriate service
            if channel == NotificationChannel.EMAIL:
                result = await self._send_email(
                    recipient, rendered_content, template_data, db_notification.id
                )
            elif channel == NotificationChannel.PUSH:
                result = await self._send_push(
                    recipient, rendered_content, template_data, db_notification.id
                )
            elif channel == NotificationChannel.SMS:
                result = await self._send_sms(
                    recipient, rendered_content, template_data, db_notification.id
                )
            elif channel == NotificationChannel.IN_APP:
                result = await self._send_in_app(
                    recipient, rendered_content, template_data, db_notification.id
                )
            else:
                return {"status": "error", "error": f"Unsupported channel: {channel}"}

            # Update notification record with result
            await self._update_notification_record(db_notification.id, result)

            # Log the event
            await self._log_notification_event(db_notification.id, "sent", result)

            return {
                "status": "success",
                "notification_id": db_notification.id,
                "channel": channel.value,
                "delivery_result": result
            }

        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
            return {"status": "error", "error": str(e)}

    async def send_multi_channel(
        self,
        user_id: int,
        channels: List[NotificationChannel],
        notification_type: Union[str, NotificationType],
        data: Dict[str, Any],
        priority: NotificationPriority = NotificationPriority.NORMAL,
        template_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send notification through multiple channels"""
        results = {}
        
        for channel in channels:
            result = await self.send_notification(
                user_id=user_id,
                channel=channel,
                notification_type=notification_type,
                data=data,
                priority=priority,
                template_name=template_name
            )
            results[channel.value] = result

        successful_channels = [
            channel for channel, result in results.items()
            if result.get("status") == "success"
        ]

        return {
            "status": "completed",
            "successful_channels": successful_channels,
            "failed_channels": len(channels) - len(successful_channels),
            "results": results
        }

    async def send_bulk_notification(
        self,
        user_ids: List[int],
        channel: NotificationChannel,
        notification_type: Union[str, NotificationType],
        data: Dict[str, Any],
        priority: NotificationPriority = NotificationPriority.NORMAL,
        template_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send notification to multiple users"""
        results = []
        
        for user_id in user_ids:
            result = await self.send_notification(
                user_id=user_id,
                channel=channel,
                notification_type=notification_type,
                data=data,
                priority=priority,
                template_name=template_name
            )
            results.append({"user_id": user_id, **result})

        successful = sum(1 for r in results if r.get("status") == "success")
        failed = len(results) - successful

        return {
            "status": "completed",
            "total": len(user_ids),
            "successful": successful,
            "failed": failed,
            "results": results
        }

    async def _send_email(
        self,
        recipient: str,
        content: Dict[str, str],
        data: Dict[str, Any],
        notification_id: int
    ) -> Dict[str, Any]:
        """Send email notification"""
        try:
            return await self.email_service.send_notification(
                recipient=recipient,
                subject=content.get("subject", ""),
                body=content.get("body", ""),
                html_body=content.get("html_body"),
                template_data=data
            )
        except Exception as e:
            logger.error(f"Email send failed for notification {notification_id}: {e}")
            return {"status": "error", "error": str(e)}

    async def _send_push(
        self,
        recipient: str,
        content: Dict[str, str],
        data: Dict[str, Any],
        notification_id: int
    ) -> Dict[str, Any]:
        """Send push notification"""
        try:
            return await self.push_service.send_notification(
                recipient=recipient,
                subject=content.get("subject", ""),
                body=content.get("body", ""),
                data=data.get("push_data", {}),
                priority=data.get("priority", "normal")
            )
        except Exception as e:
            logger.error(f"Push send failed for notification {notification_id}: {e}")
            return {"status": "error", "error": str(e)}

    async def _send_sms(
        self,
        recipient: str,
        content: Dict[str, str],
        data: Dict[str, Any],
        notification_id: int
    ) -> Dict[str, Any]:
        """Send SMS notification"""
        try:
            return await self.sms_service.send_notification(
                recipient=recipient,
                subject=content.get("subject", ""),
                body=content.get("body", ""),
                template_data=data
            )
        except Exception as e:
            logger.error(f"SMS send failed for notification {notification_id}: {e}")
            return {"status": "error", "error": str(e)}

    async def _send_in_app(
        self,
        recipient: str,
        content: Dict[str, str],
        data: Dict[str, Any],
        notification_id: int
    ) -> Dict[str, Any]:
        """Send in-app notification"""
        try:
            return await self.in_app_service.send_notification(
                recipient=recipient,
                subject=content.get("subject", ""),
                body=content.get("body", ""),
                data=data.get("in_app_data", {}),
                priority=data.get("priority", "normal")
            )
        except Exception as e:
            logger.error(f"In-app send failed for notification {notification_id}: {e}")
            return {"status": "error", "error": str(e)}

    async def _get_user_info(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user information for template rendering"""
        try:
            db = next(get_db())
            
            # This would query your user model
            # For now, return placeholder data
            user_info = {
                "user_id": user_id,
                "user_name": f"User {user_id}",
                "user_email": f"user{user_id}@example.com",
                "created_date": datetime.now().strftime("%B %d, %Y"),
                "timezone": "UTC"
            }
            
            db.close()
            return user_info
            
        except Exception as e:
            logger.error(f"Failed to get user info: {e}")
            return None

    async def _get_recipient_for_channel(
        self,
        user_id: int,
        channel: NotificationChannel
    ) -> Optional[str]:
        """Get recipient address for channel"""
        try:
            db = next(get_db())
            
            # This would query user contact information
            # For now, return placeholder data
            recipients = {
                NotificationChannel.EMAIL: f"user{user_id}@example.com",
                NotificationChannel.SMS: f"+1555000{user_id:04d}",
                NotificationChannel.PUSH: f"push_token_{user_id}",
                NotificationChannel.IN_APP: str(user_id)
            }
            
            db.close()
            return recipients.get(channel)
            
        except Exception as e:
            logger.error(f"Failed to get recipient for channel: {e}")
            return None

    async def _create_notification_record(
        self,
        user_id: int,
        channel: NotificationChannel,
        notification_type: NotificationType,
        priority: NotificationPriority,
        subject: str,
        body: str,
        html_body: Optional[str],
        data: Dict[str, Any],
        recipient: str,
        scheduled_at: Optional[datetime]
    ) -> Notification:
        """Create notification record in database"""
        db = next(get_db())
        try:
            notification = Notification(
                user_id=user_id,
                channel=channel,
                type=notification_type,
                priority=priority,
                status=NotificationStatus.PENDING,
                subject=subject,
                body=body,
                html_body=html_body,
                data=data,
                recipient=recipient,
                scheduled_at=scheduled_at
            )
            
            db.add(notification)
            db.commit()
            db.refresh(notification)
            
            return notification
        finally:
            db.close()

    async def _update_notification_record(
        self,
        notification_id: int,
        result: Dict[str, Any]
    ):
        """Update notification record with delivery result"""
        try:
            db = next(get_db())
            
            notification = db.query(Notification).filter(
                Notification.id == notification_id
            ).first()
            
            if notification:
                if result.get("status") == "success":
                    notification.status = NotificationStatus.DELIVERED
                    notification.sent_at = datetime.now()
                    notification.delivered_at = datetime.now()
                    notification.provider = result.get("provider")
                    notification.provider_id = result.get("provider_id")
                    notification.provider_response = result.get("response")
                else:
                    notification.status = NotificationStatus.FAILED
                    notification.error_message = result.get("error", "Unknown error")
                
                db.commit()
            
            db.close()
            
        except Exception as e:
            logger.error(f"Failed to update notification record: {e}")

    async def _log_notification_event(
        self,
        notification_id: int,
        event_type: str,
        event_data: Dict[str, Any]
    ):
        """Log notification event"""
        try:
            db = next(get_db())
            
            log_entry = NotificationLog(
                notification_id=notification_id,
                event_type=event_type,
                event_data=event_data
            )
            
            db.add(log_entry)
            db.commit()
            db.close()
            
        except Exception as e:
            logger.error(f"Failed to log notification event: {e}")

    async def get_notification_status(self, notification_id: int) -> Dict[str, Any]:
        """Get notification delivery status"""
        try:
            db = next(get_db())
            
            notification = db.query(Notification).filter(
                Notification.id == notification_id
            ).first()
            
            if not notification:
                return {"status": "error", "error": "Notification not found"}
            
            # Get logs
            logs = db.query(NotificationLog).filter(
                NotificationLog.notification_id == notification_id
            ).order_by(NotificationLog.timestamp.desc()).all()
            
            db.close()
            
            return {
                "status": "success",
                "notification": {
                    "id": notification.id,
                    "user_id": notification.user_id,
                    "channel": notification.channel.value,
                    "type": notification.type.value,
                    "status": notification.status.value,
                    "subject": notification.subject,
                    "recipient": notification.recipient,
                    "provider": notification.provider,
                    "provider_id": notification.provider_id,
                    "created_at": notification.created_at,
                    "sent_at": notification.sent_at,
                    "delivered_at": notification.delivered_at,
                    "read_at": notification.read_at,
                    "error_message": notification.error_message
                },
                "logs": [
                    {
                        "event_type": log.event_type,
                        "event_data": log.event_data,
                        "timestamp": log.timestamp
                    }
                    for log in logs
                ]
            }
            
        except Exception as e:
            logger.error(f"Failed to get notification status: {e}")
            return {"status": "error", "error": str(e)}

    async def get_user_notifications(
        self,
        user_id: int,
        channel: Optional[NotificationChannel] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Get user's notification history"""
        try:
            db = next(get_db())
            
            query = db.query(Notification).filter(Notification.user_id == user_id)
            
            if channel:
                query = query.filter(Notification.channel == channel)
            
            notifications = query.order_by(
                Notification.created_at.desc()
            ).offset(offset).limit(limit).all()
            
            db.close()
            
            return {
                "status": "success",
                "notifications": [
                    {
                        "id": n.id,
                        "channel": n.channel.value,
                        "type": n.type.value,
                        "status": n.status.value,
                        "subject": n.subject,
                        "created_at": n.created_at,
                        "delivered_at": n.delivered_at,
                        "read_at": n.read_at
                    }
                    for n in notifications
                ]
            }
            
        except Exception as e:
            logger.error(f"Failed to get user notifications: {e}")
            return {"status": "error", "error": str(e)}

    async def handle_webhook(
        self,
        provider: str,
        channel: NotificationChannel,
        payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle delivery webhooks from providers"""
        try:
            if channel == NotificationChannel.EMAIL:
                return await self.email_service.handle_webhook(provider, payload)
            elif channel == NotificationChannel.SMS:
                return await self.sms_service.handle_webhook(payload)
            elif channel == NotificationChannel.PUSH:
                return await self.push_service.handle_webhook(provider, payload)
            else:
                return {"status": "error", "error": f"Webhook not supported for {channel}"}
                
        except Exception as e:
            logger.error(f"Failed to handle webhook: {e}")
            return {"status": "error", "error": str(e)}

    async def get_analytics(
        self,
        start_date: datetime,
        end_date: datetime,
        channel: Optional[NotificationChannel] = None
    ) -> Dict[str, Any]:
        """Get notification analytics"""
        try:
            db = next(get_db())
            
            query = db.query(Notification).filter(
                Notification.created_at.between(start_date, end_date)
            )
            
            if channel:
                query = query.filter(Notification.channel == channel)
            
            notifications = query.all()
            
            # Calculate metrics
            total_sent = len(notifications)
            delivered = sum(1 for n in notifications if n.status == NotificationStatus.DELIVERED)
            failed = sum(1 for n in notifications if n.status == NotificationStatus.FAILED)
            read = sum(1 for n in notifications if n.read_at is not None)
            
            delivery_rate = (delivered / total_sent * 100) if total_sent > 0 else 0
            read_rate = (read / delivered * 100) if delivered > 0 else 0
            
            # Group by channel
            by_channel = {}
            for n in notifications:
                channel_name = n.channel.value
                if channel_name not in by_channel:
                    by_channel[channel_name] = {"sent": 0, "delivered": 0, "failed": 0}
                
                by_channel[channel_name]["sent"] += 1
                if n.status == NotificationStatus.DELIVERED:
                    by_channel[channel_name]["delivered"] += 1
                elif n.status == NotificationStatus.FAILED:
                    by_channel[channel_name]["failed"] += 1
            
            db.close()
            
            return {
                "status": "success",
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },
                "summary": {
                    "total_sent": total_sent,
                    "delivered": delivered,
                    "failed": failed,
                    "read": read,
                    "delivery_rate": round(delivery_rate, 2),
                    "read_rate": round(read_rate, 2)
                },
                "by_channel": by_channel
            }
            
        except Exception as e:
            logger.error(f"Failed to get analytics: {e}")
            return {"status": "error", "error": str(e)}

    async def health_check(self) -> Dict[str, Any]:
        """Check health of all notification services"""
        health_status = {
            "overall": "healthy",
            "services": {}
        }
        
        services = [
            ("email", self.email_service),
            ("push", self.push_service),
            ("sms", self.sms_service),
            ("in_app", self.in_app_service)
        ]
        
        for service_name, service in services:
            try:
                service_health = await service.check_health()
                health_status["services"][service_name] = service_health
                
                if service_health.get("status") != "healthy":
                    health_status["overall"] = "degraded"
                    
            except Exception as e:
                health_status["services"][service_name] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
                health_status["overall"] = "unhealthy"
        
        return health_status