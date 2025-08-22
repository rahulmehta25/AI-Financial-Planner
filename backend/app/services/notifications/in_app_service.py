"""
In-App Notification Service

Handles real-time in-app notifications with:
- WebSocket connections for real-time delivery
- Read/unread tracking
- Priority levels
- Notification center
- Badge counts
- Action handling
"""

import asyncio
import json
import logging
from typing import Optional, Dict, Any, List, Set
from datetime import datetime, timedelta
from collections import defaultdict
import redis.asyncio as redis
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc

from .config import notification_config
from .models import (
    NotificationStatus, 
    NotificationChannel, 
    NotificationPriority,
    Notification,
    NotificationLog
)
from .base import BaseNotificationService
from app.database.base import get_db


logger = logging.getLogger(__name__)


class InAppNotificationService(BaseNotificationService):
    """In-app notification service with real-time delivery"""

    def __init__(self):
        super().__init__(NotificationChannel.IN_APP)
        self.redis_client = None
        self.connected_users: Dict[int, Set[str]] = defaultdict(set)  # user_id -> set of connection_ids
        self.user_connections: Dict[str, int] = {}  # connection_id -> user_id
        self._initialize_redis()

    def _initialize_redis(self):
        """Initialize Redis connection for real-time features"""
        try:
            self.redis_client = redis.from_url(
                notification_config.redis_url,
                db=notification_config.redis_db,
                decode_responses=True
            )
            logger.info("Redis client initialized for in-app notifications")
        except Exception as e:
            logger.error(f"Failed to initialize Redis: {e}")

    async def send_notification(
        self,
        recipient: str,  # user_id as string
        subject: str,
        body: str,
        priority: str = "normal",
        data: Optional[Dict[str, Any]] = None,
        action_url: Optional[str] = None,
        action_text: Optional[str] = None,
        expires_at: Optional[datetime] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Send in-app notification"""
        try:
            user_id = int(recipient)
            
            # Create notification data
            notification_data = {
                "id": None,  # Will be set after DB insert
                "user_id": user_id,
                "subject": subject,
                "body": body,
                "priority": priority,
                "data": data or {},
                "action_url": action_url,
                "action_text": action_text,
                "created_at": datetime.now().isoformat(),
                "expires_at": expires_at.isoformat() if expires_at else None,
                "read": False,
                "status": NotificationStatus.PENDING.value
            }

            # Store in database
            db_notification = await self._store_notification(notification_data)
            notification_data["id"] = db_notification.id

            # Send real-time notification
            await self._send_realtime(user_id, notification_data)

            # Update badge count
            await self._update_badge_count(user_id)

            return {
                "status": "success",
                "notification_id": db_notification.id,
                "delivered_realtime": user_id in self.connected_users
            }

        except Exception as e:
            logger.error(f"Failed to send in-app notification to {recipient}: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    async def _store_notification(self, notification_data: Dict[str, Any]) -> Notification:
        """Store notification in database"""
        db = next(get_db())
        try:
            db_notification = Notification(
                user_id=notification_data["user_id"],
                channel=NotificationChannel.IN_APP,
                priority=NotificationPriority(notification_data["priority"]),
                status=NotificationStatus.DELIVERED,  # In-app is immediately delivered
                subject=notification_data["subject"],
                body=notification_data["body"],
                data=notification_data["data"],
                delivered_at=datetime.now()
            )
            
            db.add(db_notification)
            db.commit()
            db.refresh(db_notification)
            
            return db_notification
        finally:
            db.close()

    async def _send_realtime(self, user_id: int, notification_data: Dict[str, Any]):
        """Send notification via WebSocket to connected clients"""
        if user_id in self.connected_users:
            # Send to all connections for this user
            for connection_id in self.connected_users[user_id]:
                await self._send_to_connection(connection_id, notification_data)
            
            # Update status to delivered
            notification_data["status"] = NotificationStatus.DELIVERED.value

        # Cache in Redis for when user reconnects
        await self._cache_notification(user_id, notification_data)

    async def _send_to_connection(self, connection_id: str, notification_data: Dict[str, Any]):
        """Send notification to a specific WebSocket connection"""
        # This would integrate with your WebSocket manager
        # For now, we'll cache it for retrieval
        try:
            if self.redis_client:
                await self.redis_client.lpush(
                    f"notifications:connection:{connection_id}",
                    json.dumps(notification_data)
                )
                await self.redis_client.expire(
                    f"notifications:connection:{connection_id}",
                    3600  # 1 hour
                )
        except Exception as e:
            logger.error(f"Failed to send to connection {connection_id}: {e}")

    async def _cache_notification(self, user_id: int, notification_data: Dict[str, Any]):
        """Cache notification in Redis"""
        try:
            if self.redis_client:
                await self.redis_client.lpush(
                    f"notifications:user:{user_id}",
                    json.dumps(notification_data)
                )
                # Keep last 100 notifications
                await self.redis_client.ltrim(f"notifications:user:{user_id}", 0, 99)
        except Exception as e:
            logger.error(f"Failed to cache notification: {e}")

    async def _update_badge_count(self, user_id: int):
        """Update unread notification count"""
        try:
            count = await self.get_unread_count(user_id)
            
            if self.redis_client:
                await self.redis_client.set(
                    f"badge:user:{user_id}",
                    count,
                    ex=3600  # 1 hour expiry
                )

            # Send badge update to connected clients
            if user_id in self.connected_users:
                badge_data = {
                    "type": "badge_update",
                    "count": count,
                    "timestamp": datetime.now().isoformat()
                }
                
                for connection_id in self.connected_users[user_id]:
                    await self._send_to_connection(connection_id, badge_data)

        except Exception as e:
            logger.error(f"Failed to update badge count: {e}")

    async def connect_user(self, user_id: int, connection_id: str):
        """Register user WebSocket connection"""
        self.connected_users[user_id].add(connection_id)
        self.user_connections[connection_id] = user_id
        
        logger.info(f"User {user_id} connected with connection {connection_id}")
        
        # Send cached notifications
        await self._send_cached_notifications(user_id, connection_id)
        
        # Send current badge count
        badge_count = await self.get_unread_count(user_id)
        await self._send_to_connection(connection_id, {
            "type": "badge_update",
            "count": badge_count
        })

    async def disconnect_user(self, connection_id: str):
        """Unregister user WebSocket connection"""
        if connection_id in self.user_connections:
            user_id = self.user_connections[connection_id]
            self.connected_users[user_id].discard(connection_id)
            
            if not self.connected_users[user_id]:
                del self.connected_users[user_id]
            
            del self.user_connections[connection_id]
            logger.info(f"Connection {connection_id} disconnected")

    async def _send_cached_notifications(self, user_id: int, connection_id: str):
        """Send cached notifications to newly connected user"""
        try:
            if self.redis_client:
                notifications = await self.redis_client.lrange(
                    f"notifications:user:{user_id}", 0, 9  # Last 10 notifications
                )
                
                for notification_json in reversed(notifications):
                    notification_data = json.loads(notification_json)
                    await self._send_to_connection(connection_id, notification_data)

        except Exception as e:
            logger.error(f"Failed to send cached notifications: {e}")

    async def mark_as_read(self, user_id: int, notification_id: int) -> Dict[str, Any]:
        """Mark notification as read"""
        try:
            db = next(get_db())
            
            notification = db.query(Notification).filter(
                and_(
                    Notification.id == notification_id,
                    Notification.user_id == user_id,
                    Notification.channel == NotificationChannel.IN_APP
                )
            ).first()
            
            if not notification:
                return {"status": "error", "error": "Notification not found"}
            
            if not notification.read_at:
                notification.read_at = datetime.now()
                db.commit()
                
                # Log the read event
                log_entry = NotificationLog(
                    notification_id=notification_id,
                    event_type="read",
                    event_data={"user_id": user_id}
                )
                db.add(log_entry)
                db.commit()
                
                # Update badge count
                await self._update_badge_count(user_id)
            
            db.close()
            
            return {"status": "success", "notification_id": notification_id}
            
        except Exception as e:
            logger.error(f"Failed to mark notification as read: {e}")
            return {"status": "error", "error": str(e)}

    async def mark_all_as_read(self, user_id: int) -> Dict[str, Any]:
        """Mark all notifications as read for a user"""
        try:
            db = next(get_db())
            
            unread_notifications = db.query(Notification).filter(
                and_(
                    Notification.user_id == user_id,
                    Notification.channel == NotificationChannel.IN_APP,
                    Notification.read_at.is_(None)
                )
            ).all()
            
            count = 0
            for notification in unread_notifications:
                notification.read_at = datetime.now()
                count += 1
            
            if count > 0:
                db.commit()
                
                # Update badge count
                await self._update_badge_count(user_id)
            
            db.close()
            
            return {"status": "success", "marked_count": count}
            
        except Exception as e:
            logger.error(f"Failed to mark all notifications as read: {e}")
            return {"status": "error", "error": str(e)}

    async def get_notifications(
        self,
        user_id: int,
        limit: int = 20,
        offset: int = 0,
        unread_only: bool = False
    ) -> Dict[str, Any]:
        """Get user's notifications"""
        try:
            db = next(get_db())
            
            query = db.query(Notification).filter(
                and_(
                    Notification.user_id == user_id,
                    Notification.channel == NotificationChannel.IN_APP
                )
            )
            
            if unread_only:
                query = query.filter(Notification.read_at.is_(None))
            
            notifications = query.order_by(desc(Notification.created_at)).offset(offset).limit(limit).all()
            
            result = []
            for notification in notifications:
                result.append({
                    "id": notification.id,
                    "subject": notification.subject,
                    "body": notification.body,
                    "priority": notification.priority.value,
                    "data": notification.data,
                    "created_at": notification.created_at.isoformat(),
                    "read_at": notification.read_at.isoformat() if notification.read_at else None,
                    "is_read": notification.read_at is not None
                })
            
            db.close()
            
            return {
                "status": "success",
                "notifications": result,
                "count": len(result)
            }
            
        except Exception as e:
            logger.error(f"Failed to get notifications: {e}")
            return {"status": "error", "error": str(e)}

    async def get_unread_count(self, user_id: int) -> int:
        """Get unread notification count"""
        try:
            db = next(get_db())
            
            count = db.query(Notification).filter(
                and_(
                    Notification.user_id == user_id,
                    Notification.channel == NotificationChannel.IN_APP,
                    Notification.read_at.is_(None)
                )
            ).count()
            
            db.close()
            return count
            
        except Exception as e:
            logger.error(f"Failed to get unread count: {e}")
            return 0

    async def delete_notification(self, user_id: int, notification_id: int) -> Dict[str, Any]:
        """Delete a notification"""
        try:
            db = next(get_db())
            
            notification = db.query(Notification).filter(
                and_(
                    Notification.id == notification_id,
                    Notification.user_id == user_id,
                    Notification.channel == NotificationChannel.IN_APP
                )
            ).first()
            
            if not notification:
                return {"status": "error", "error": "Notification not found"}
            
            db.delete(notification)
            db.commit()
            db.close()
            
            # Update badge count
            await self._update_badge_count(user_id)
            
            return {"status": "success", "notification_id": notification_id}
            
        except Exception as e:
            logger.error(f"Failed to delete notification: {e}")
            return {"status": "error", "error": str(e)}

    async def cleanup_old_notifications(self, days: int = 30):
        """Clean up notifications older than specified days"""
        try:
            db = next(get_db())
            
            cutoff_date = datetime.now() - timedelta(days=days)
            
            deleted_count = db.query(Notification).filter(
                and_(
                    Notification.channel == NotificationChannel.IN_APP,
                    Notification.created_at < cutoff_date
                )
            ).delete()
            
            db.commit()
            db.close()
            
            logger.info(f"Cleaned up {deleted_count} old in-app notifications")
            return {"status": "success", "deleted_count": deleted_count}
            
        except Exception as e:
            logger.error(f"Failed to cleanup old notifications: {e}")
            return {"status": "error", "error": str(e)}

    async def send_broadcast(
        self,
        user_ids: List[int],
        subject: str,
        body: str,
        priority: str = "normal",
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Send notification to multiple users"""
        results = []
        
        for user_id in user_ids:
            try:
                result = await self.send_notification(
                    recipient=str(user_id),
                    subject=subject,
                    body=body,
                    priority=priority,
                    data=data
                )
                results.append({"user_id": user_id, **result})
            except Exception as e:
                results.append({
                    "user_id": user_id,
                    "status": "error",
                    "error": str(e)
                })

        successful = sum(1 for r in results if r["status"] == "success")
        failed = len(results) - successful

        return {
            "status": "completed",
            "total": len(user_ids),
            "successful": successful,
            "failed": failed,
            "results": results
        }

    async def get_connected_users(self) -> List[int]:
        """Get list of currently connected users"""
        return list(self.connected_users.keys())

    async def is_user_online(self, user_id: int) -> bool:
        """Check if user is currently connected"""
        return user_id in self.connected_users

    def get_rate_limit(self) -> Dict[str, int]:
        """Get rate limits for in-app notifications"""
        return {
            "requests_per_minute": 1000,
            "requests_per_hour": 10000,
            "requests_per_day": 100000
        }