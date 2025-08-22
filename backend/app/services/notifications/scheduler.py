"""
Notification Scheduler and Queue Manager

Handles:
- Notification scheduling
- Queue management
- Retry logic
- Rate limiting
- Batch processing
- Failed notification handling
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import redis.asyncio as redis
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc

from .config import notification_config
from .models import (
    Notification,
    NotificationStatus,
    NotificationChannel,
    NotificationPriority,
    NotificationLog
)
from .manager import NotificationManager
from app.database.base import get_db


logger = logging.getLogger(__name__)


class QueuePriority(Enum):
    """Queue priority levels"""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


@dataclass
class QueuedNotification:
    """Queued notification data structure"""
    id: str
    user_id: int
    channel: str
    type: str
    priority: str
    data: Dict[str, Any]
    scheduled_at: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3
    created_at: Optional[datetime] = None


class NotificationScheduler:
    """Notification scheduler and queue manager"""

    def __init__(self):
        self.redis_client = None
        self.notification_manager = None
        self.running = False
        self.worker_tasks = []
        self._initialize_redis()
        self._initialize_queues()

    def _initialize_redis(self):
        """Initialize Redis connection"""
        try:
            self.redis_client = redis.from_url(
                notification_config.redis_url,
                db=notification_config.redis_db,
                decode_responses=True
            )
            logger.info("Redis client initialized for notification scheduler")
        except Exception as e:
            logger.error(f"Failed to initialize Redis: {e}")
            raise

    def _initialize_queues(self):
        """Initialize queue names"""
        self.queues = {
            NotificationChannel.EMAIL: notification_config.email_queue_name,
            NotificationChannel.PUSH: notification_config.push_queue_name,
            NotificationChannel.SMS: notification_config.sms_queue_name,
            NotificationChannel.IN_APP: "in_app_notifications"
        }

    async def start(self):
        """Start the scheduler workers"""
        if self.running:
            return

        self.running = True
        self.notification_manager = NotificationManager()
        
        # Start worker tasks for each channel
        for channel in NotificationChannel:
            task = asyncio.create_task(self._queue_worker(channel))
            self.worker_tasks.append(task)
        
        # Start scheduled notification processor
        scheduled_task = asyncio.create_task(self._scheduled_processor())
        self.worker_tasks.append(scheduled_task)
        
        # Start retry processor
        retry_task = asyncio.create_task(self._retry_processor())
        self.worker_tasks.append(retry_task)
        
        logger.info("Notification scheduler started with workers")

    async def stop(self):
        """Stop the scheduler workers"""
        self.running = False
        
        # Cancel all worker tasks
        for task in self.worker_tasks:
            task.cancel()
        
        # Wait for tasks to complete
        await asyncio.gather(*self.worker_tasks, return_exceptions=True)
        
        self.worker_tasks.clear()
        logger.info("Notification scheduler stopped")

    async def schedule_notification(
        self,
        user_id: int,
        channel: NotificationChannel,
        notification_type: str,
        data: Dict[str, Any],
        scheduled_at: Optional[datetime] = None,
        priority: NotificationPriority = NotificationPriority.NORMAL
    ) -> str:
        """Schedule a notification for delivery"""
        try:
            # Generate unique ID
            import uuid
            notification_id = str(uuid.uuid4())
            
            queued_notification = QueuedNotification(
                id=notification_id,
                user_id=user_id,
                channel=channel.value,
                type=notification_type,
                priority=priority.value,
                data=data,
                scheduled_at=scheduled_at,
                created_at=datetime.now()
            )
            
            if scheduled_at and scheduled_at > datetime.now():
                # Schedule for later
                await self._add_to_scheduled_queue(queued_notification)
            else:
                # Add to immediate processing queue
                await self._add_to_processing_queue(queued_notification)
            
            logger.info(f"Scheduled notification {notification_id} for user {user_id}")
            return notification_id
            
        except Exception as e:
            logger.error(f"Failed to schedule notification: {e}")
            raise

    async def _add_to_scheduled_queue(self, notification: QueuedNotification):
        """Add notification to scheduled queue"""
        scheduled_time = notification.scheduled_at.timestamp()
        notification_data = json.dumps({
            "id": notification.id,
            "user_id": notification.user_id,
            "channel": notification.channel,
            "type": notification.type,
            "priority": notification.priority,
            "data": notification.data,
            "retry_count": notification.retry_count,
            "max_retries": notification.max_retries,
            "created_at": notification.created_at.isoformat()
        })
        
        await self.redis_client.zadd(
            "scheduled_notifications",
            {notification_data: scheduled_time}
        )

    async def _add_to_processing_queue(self, notification: QueuedNotification):
        """Add notification to processing queue"""
        queue_name = self.queues[NotificationChannel(notification.channel)]
        
        notification_data = json.dumps({
            "id": notification.id,
            "user_id": notification.user_id,
            "channel": notification.channel,
            "type": notification.type,
            "priority": notification.priority,
            "data": notification.data,
            "retry_count": notification.retry_count,
            "max_retries": notification.max_retries,
            "created_at": notification.created_at.isoformat()
        })
        
        # Use priority scoring for queue ordering
        priority_scores = {
            "low": 1,
            "normal": 2,
            "high": 3,
            "critical": 4
        }
        
        score = priority_scores.get(notification.priority, 2)
        current_time = datetime.now().timestamp()
        
        # Combine priority and timestamp for scoring
        final_score = score * 1000000 + current_time
        
        await self.redis_client.zadd(queue_name, {notification_data: final_score})

    async def _queue_worker(self, channel: NotificationChannel):
        """Worker for processing notifications from queue"""
        queue_name = self.queues[channel]
        
        while self.running:
            try:
                # Get highest priority notification
                items = await self.redis_client.zrevrange(
                    queue_name, 0, 0, withscores=True
                )
                
                if not items:
                    await asyncio.sleep(1)
                    continue
                
                notification_data, score = items[0]
                notification_dict = json.loads(notification_data)
                
                # Remove from queue
                await self.redis_client.zrem(queue_name, notification_data)
                
                # Process notification
                await self._process_notification(notification_dict)
                
            except Exception as e:
                logger.error(f"Error in queue worker for {channel}: {e}")
                await asyncio.sleep(5)

    async def _process_notification(self, notification_dict: Dict[str, Any]):
        """Process a single notification"""
        try:
            channel = NotificationChannel(notification_dict["channel"])
            
            # Check rate limits
            if not await self._check_rate_limit(
                notification_dict["user_id"], channel
            ):
                # Re-queue with delay
                await self._requeue_with_delay(notification_dict, delay_seconds=300)
                return
            
            # Send notification
            result = await self.notification_manager.send_notification(
                user_id=notification_dict["user_id"],
                channel=channel,
                notification_type=notification_dict["type"],
                data=notification_dict["data"]
            )
            
            if result.get("status") == "success":
                await self._log_notification_event(
                    notification_dict["id"], "processed", result
                )
            else:
                # Handle failure
                await self._handle_failed_notification(notification_dict, result)
            
        except Exception as e:
            logger.error(f"Failed to process notification: {e}")
            await self._handle_failed_notification(
                notification_dict, {"error": str(e)}
            )

    async def _handle_failed_notification(
        self,
        notification_dict: Dict[str, Any],
        error_result: Dict[str, Any]
    ):
        """Handle failed notification with retry logic"""
        retry_count = notification_dict.get("retry_count", 0)
        max_retries = notification_dict.get("max_retries", notification_config.max_retries)
        
        if retry_count < max_retries:
            # Calculate exponential backoff delay
            delay_seconds = notification_config.retry_delay * (2 ** retry_count)
            
            # Update retry count
            notification_dict["retry_count"] = retry_count + 1
            
            # Re-queue with delay
            await self._requeue_with_delay(notification_dict, delay_seconds)
            
            await self._log_notification_event(
                notification_dict["id"], "retry_scheduled", 
                {"retry_count": retry_count + 1, "delay_seconds": delay_seconds}
            )
        else:
            # Max retries exceeded
            await self._log_notification_event(
                notification_dict["id"], "failed_permanently", error_result
            )
            
            # Move to dead letter queue
            await self._add_to_dead_letter_queue(notification_dict, error_result)

    async def _requeue_with_delay(
        self,
        notification_dict: Dict[str, Any],
        delay_seconds: int
    ):
        """Re-queue notification with delay"""
        retry_time = datetime.now() + timedelta(seconds=delay_seconds)
        
        await self.redis_client.zadd(
            "retry_notifications",
            {json.dumps(notification_dict): retry_time.timestamp()}
        )

    async def _add_to_dead_letter_queue(
        self,
        notification_dict: Dict[str, Any],
        error_result: Dict[str, Any]
    ):
        """Add failed notification to dead letter queue"""
        dead_letter_data = {
            **notification_dict,
            "failed_at": datetime.now().isoformat(),
            "error": error_result
        }
        
        await self.redis_client.lpush(
            "dead_letter_notifications",
            json.dumps(dead_letter_data)
        )

    async def _scheduled_processor(self):
        """Process scheduled notifications"""
        while self.running:
            try:
                current_time = datetime.now().timestamp()
                
                # Get notifications ready for processing
                items = await self.redis_client.zrangebyscore(
                    "scheduled_notifications", 0, current_time, withscores=True
                )
                
                for notification_data, scheduled_time in items:
                    notification_dict = json.loads(notification_data)
                    
                    # Remove from scheduled queue
                    await self.redis_client.zrem("scheduled_notifications", notification_data)
                    
                    # Add to processing queue
                    queued_notification = QueuedNotification(
                        id=notification_dict["id"],
                        user_id=notification_dict["user_id"],
                        channel=notification_dict["channel"],
                        type=notification_dict["type"],
                        priority=notification_dict["priority"],
                        data=notification_dict["data"],
                        retry_count=notification_dict.get("retry_count", 0),
                        max_retries=notification_dict.get("max_retries", 3)
                    )
                    
                    await self._add_to_processing_queue(queued_notification)
                
                await asyncio.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                logger.error(f"Error in scheduled processor: {e}")
                await asyncio.sleep(30)

    async def _retry_processor(self):
        """Process retry notifications"""
        while self.running:
            try:
                current_time = datetime.now().timestamp()
                
                # Get notifications ready for retry
                items = await self.redis_client.zrangebyscore(
                    "retry_notifications", 0, current_time, withscores=True
                )
                
                for notification_data, retry_time in items:
                    notification_dict = json.loads(notification_data)
                    
                    # Remove from retry queue
                    await self.redis_client.zrem("retry_notifications", notification_data)
                    
                    # Add back to processing queue
                    queued_notification = QueuedNotification(
                        id=notification_dict["id"],
                        user_id=notification_dict["user_id"],
                        channel=notification_dict["channel"],
                        type=notification_dict["type"],
                        priority=notification_dict["priority"],
                        data=notification_dict["data"],
                        retry_count=notification_dict.get("retry_count", 0),
                        max_retries=notification_dict.get("max_retries", 3)
                    )
                    
                    await self._add_to_processing_queue(queued_notification)
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Error in retry processor: {e}")
                await asyncio.sleep(60)

    async def _check_rate_limit(
        self,
        user_id: int,
        channel: NotificationChannel
    ) -> bool:
        """Check if user is within rate limits"""
        try:
            current_hour = datetime.now().strftime("%Y-%m-%d-%H")
            rate_key = f"rate_limit:{channel.value}:{user_id}:{current_hour}"
            
            current_count = await self.redis_client.get(rate_key)
            current_count = int(current_count) if current_count else 0
            
            # Get rate limits by channel
            rate_limits = {
                NotificationChannel.EMAIL: notification_config.email_rate_limit,
                NotificationChannel.SMS: notification_config.sms_rate_limit,
                NotificationChannel.PUSH: notification_config.push_rate_limit,
                NotificationChannel.IN_APP: 1000  # High limit for in-app
            }
            
            limit = rate_limits.get(channel, 100)
            
            if current_count >= limit:
                logger.warning(f"Rate limit exceeded for user {user_id} on {channel}")
                return False
            
            # Increment counter
            await self.redis_client.incr(rate_key)
            await self.redis_client.expire(rate_key, 3600)  # 1 hour
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking rate limit: {e}")
            return True  # Allow on error

    async def _log_notification_event(
        self,
        notification_id: str,
        event_type: str,
        event_data: Dict[str, Any]
    ):
        """Log notification events"""
        try:
            log_data = {
                "notification_id": notification_id,
                "event_type": event_type,
                "event_data": event_data,
                "timestamp": datetime.now().isoformat()
            }
            
            await self.redis_client.lpush(
                "notification_events",
                json.dumps(log_data)
            )
            
            # Keep only recent events
            await self.redis_client.ltrim("notification_events", 0, 9999)
            
        except Exception as e:
            logger.error(f"Failed to log notification event: {e}")

    async def get_queue_stats(self) -> Dict[str, Any]:
        """Get queue statistics"""
        try:
            stats = {}
            
            for channel, queue_name in self.queues.items():
                queue_size = await self.redis_client.zcard(queue_name)
                stats[channel.value] = {
                    "queue_size": queue_size,
                    "queue_name": queue_name
                }
            
            # Scheduled and retry queues
            scheduled_count = await self.redis_client.zcard("scheduled_notifications")
            retry_count = await self.redis_client.zcard("retry_notifications")
            dead_letter_count = await self.redis_client.llen("dead_letter_notifications")
            
            stats["scheduled"] = scheduled_count
            stats["retry"] = retry_count
            stats["dead_letter"] = dead_letter_count
            stats["running"] = self.running
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get queue stats: {e}")
            return {"error": str(e)}

    async def clear_dead_letter_queue(self) -> int:
        """Clear dead letter queue and return count of cleared items"""
        try:
            count = await self.redis_client.llen("dead_letter_notifications")
            await self.redis_client.delete("dead_letter_notifications")
            return count
        except Exception as e:
            logger.error(f"Failed to clear dead letter queue: {e}")
            return 0

    async def reprocess_dead_letters(self, limit: int = 100) -> Dict[str, Any]:
        """Reprocess notifications from dead letter queue"""
        try:
            reprocessed = 0
            
            for _ in range(limit):
                dead_letter_data = await self.redis_client.rpop("dead_letter_notifications")
                if not dead_letter_data:
                    break
                
                notification_dict = json.loads(dead_letter_data)
                
                # Reset retry count and requeue
                notification_dict["retry_count"] = 0
                
                queued_notification = QueuedNotification(
                    id=notification_dict["id"],
                    user_id=notification_dict["user_id"],
                    channel=notification_dict["channel"],
                    type=notification_dict["type"],
                    priority=notification_dict["priority"],
                    data=notification_dict["data"],
                    retry_count=0
                )
                
                await self._add_to_processing_queue(queued_notification)
                reprocessed += 1
            
            return {
                "status": "success",
                "reprocessed_count": reprocessed
            }
            
        except Exception as e:
            logger.error(f"Failed to reprocess dead letters: {e}")
            return {"status": "error", "error": str(e)}

    async def pause_queue(self, channel: NotificationChannel):
        """Pause processing for a specific channel"""
        # This would be implemented by adding a pause flag in Redis
        await self.redis_client.set(f"queue_paused:{channel.value}", "true")

    async def resume_queue(self, channel: NotificationChannel):
        """Resume processing for a specific channel"""
        await self.redis_client.delete(f"queue_paused:{channel.value}")

    async def is_queue_paused(self, channel: NotificationChannel) -> bool:
        """Check if queue is paused"""
        paused = await self.redis_client.get(f"queue_paused:{channel.value}")
        return paused == "true"