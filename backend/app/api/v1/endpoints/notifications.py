"""
Notification API Endpoints

RESTful API for managing notifications, preferences, and templates
"""

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.security import HTTPBearer
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from pydantic import BaseModel

from app.services.notifications import (
    NotificationManager,
    NotificationScheduler,
    PreferencesManager,
    NotificationTemplateManager,
    NotificationChannel,
    NotificationPriority,
    NotificationType,
    BulkNotificationRequest,
    PreferenceUpdate,
    NotificationResponse
)
from app.api.deps import get_current_user
from app.models.user import User


router = APIRouter()
security = HTTPBearer()

# Initialize services
notification_manager = NotificationManager()
scheduler = NotificationScheduler()
preferences_manager = PreferencesManager()
template_manager = NotificationTemplateManager()


# Request/Response Models
class SendNotificationRequest(BaseModel):
    channel: NotificationChannel
    notification_type: str
    data: Dict[str, Any]
    recipient: Optional[str] = None
    template_name: Optional[str] = None
    priority: NotificationPriority = NotificationPriority.NORMAL
    scheduled_at: Optional[datetime] = None


class MultiChannelNotificationRequest(BaseModel):
    channels: List[NotificationChannel]
    notification_type: str
    data: Dict[str, Any]
    priority: NotificationPriority = NotificationPriority.NORMAL
    template_name: Optional[str] = None


class WebhookPayload(BaseModel):
    provider: str
    channel: NotificationChannel
    payload: Dict[str, Any]


class TemplateCreateRequest(BaseModel):
    name: str
    channel: NotificationChannel
    notification_type: NotificationType
    subject_template: Optional[str] = None
    body_template: str
    html_template: Optional[str] = None
    variables: Optional[List[str]] = None


# Notification Endpoints
@router.post("/send", response_model=Dict[str, Any])
async def send_notification(
    request: SendNotificationRequest,
    current_user: User = Depends(get_current_user)
):
    """Send a single notification"""
    try:
        result = await notification_manager.send_notification(
            user_id=current_user.id,
            channel=request.channel,
            notification_type=request.notification_type,
            data=request.data,
            recipient=request.recipient,
            template_name=request.template_name,
            priority=request.priority,
            scheduled_at=request.scheduled_at
        )
        
        if result.get("status") == "error":
            raise HTTPException(status_code=400, detail=result.get("error"))
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/send-multi-channel", response_model=Dict[str, Any])
async def send_multi_channel_notification(
    request: MultiChannelNotificationRequest,
    current_user: User = Depends(get_current_user)
):
    """Send notification through multiple channels"""
    try:
        result = await notification_manager.send_multi_channel(
            user_id=current_user.id,
            channels=request.channels,
            notification_type=request.notification_type,
            data=request.data,
            priority=request.priority,
            template_name=request.template_name
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/send-bulk", response_model=Dict[str, Any])
async def send_bulk_notification(
    request: BulkNotificationRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """Send notification to multiple users (admin only)"""
    # Add admin check here
    if not getattr(current_user, 'is_admin', False):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        # Process in background for large lists
        if len(request.user_ids) > 100:
            background_tasks.add_task(
                _process_bulk_notification,
                request.user_ids,
                request.channel,
                request.type,
                request.template_data,
                request.priority,
                request.scheduled_at
            )
            return {
                "status": "accepted",
                "message": "Bulk notification queued for processing",
                "user_count": len(request.user_ids)
            }
        else:
            result = await notification_manager.send_bulk_notification(
                user_ids=request.user_ids,
                channel=request.channel,
                notification_type=request.type,
                data=request.template_data,
                priority=request.priority
            )
            return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def _process_bulk_notification(
    user_ids: List[int],
    channel: NotificationChannel,
    notification_type: str,
    data: Dict[str, Any],
    priority: NotificationPriority,
    scheduled_at: Optional[datetime]
):
    """Background task for processing bulk notifications"""
    try:
        await notification_manager.send_bulk_notification(
            user_ids=user_ids,
            channel=channel,
            notification_type=notification_type,
            data=data,
            priority=priority
        )
    except Exception as e:
        logger.error(f"Bulk notification processing failed: {e}")


@router.get("/status/{notification_id}", response_model=Dict[str, Any])
async def get_notification_status(
    notification_id: int,
    current_user: User = Depends(get_current_user)
):
    """Get notification delivery status"""
    try:
        result = await notification_manager.get_notification_status(notification_id)
        
        # Check if user owns this notification or is admin
        if result.get("status") == "success":
            notification = result.get("notification", {})
            if (notification.get("user_id") != current_user.id and 
                not getattr(current_user, 'is_admin', False)):
                raise HTTPException(status_code=403, detail="Access denied")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history", response_model=Dict[str, Any])
async def get_notification_history(
    channel: Optional[NotificationChannel] = None,
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user)
):
    """Get user's notification history"""
    try:
        result = await notification_manager.get_user_notifications(
            user_id=current_user.id,
            channel=channel,
            limit=limit,
            offset=offset
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Preference Endpoints
@router.get("/preferences", response_model=Dict[str, Any])
async def get_user_preferences(
    current_user: User = Depends(get_current_user)
):
    """Get user's notification preferences"""
    try:
        result = await preferences_manager.get_user_preferences(current_user.id)
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/preferences", response_model=Dict[str, Any])
async def update_preference(
    channel: NotificationChannel,
    notification_type: NotificationType,
    enabled: bool,
    frequency: Optional[str] = "immediate",
    current_user: User = Depends(get_current_user)
):
    """Update a notification preference"""
    try:
        result = await preferences_manager.update_preference(
            user_id=current_user.id,
            channel=channel,
            notification_type=notification_type,
            enabled=enabled,
            frequency=frequency
        )
        
        if result.get("status") == "error":
            raise HTTPException(status_code=400, detail=result.get("error"))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/preferences/bulk", response_model=Dict[str, Any])
async def bulk_update_preferences(
    preferences: List[PreferenceUpdate],
    current_user: User = Depends(get_current_user)
):
    """Update multiple preferences at once"""
    try:
        result = await preferences_manager.bulk_update_preferences(
            user_id=current_user.id,
            preferences=preferences
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/preferences/quiet-hours", response_model=Dict[str, Any])
async def set_quiet_hours(
    start_time: str,
    end_time: str,
    timezone: str = "UTC",
    current_user: User = Depends(get_current_user)
):
    """Set quiet hours for notifications"""
    try:
        result = await preferences_manager.set_quiet_hours(
            user_id=current_user.id,
            start_time=start_time,
            end_time=end_time,
            timezone=timezone
        )
        
        if result.get("status") == "error":
            raise HTTPException(status_code=400, detail=result.get("error"))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/preferences/disable-all", response_model=Dict[str, Any])
async def disable_all_notifications(
    current_user: User = Depends(get_current_user)
):
    """Disable all notifications for user"""
    try:
        result = await preferences_manager.disable_all_notifications(current_user.id)
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/preferences/enable-channel", response_model=Dict[str, Any])
async def enable_channel(
    channel: NotificationChannel,
    current_user: User = Depends(get_current_user)
):
    """Enable all notifications for a channel"""
    try:
        result = await preferences_manager.enable_channel(
            user_id=current_user.id,
            channel=channel
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/preferences/disable-channel", response_model=Dict[str, Any])
async def disable_channel(
    channel: NotificationChannel,
    current_user: User = Depends(get_current_user)
):
    """Disable all notifications for a channel"""
    try:
        result = await preferences_manager.disable_channel(
            user_id=current_user.id,
            channel=channel
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/unsubscribe/{token}", response_model=Dict[str, Any])
async def unsubscribe(token: str):
    """Process unsubscribe request via token"""
    try:
        result = await preferences_manager.process_unsubscribe(token)
        
        if result.get("status") == "error":
            raise HTTPException(status_code=400, detail=result.get("error"))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Template Endpoints (Admin only)
@router.post("/templates", response_model=Dict[str, Any])
async def create_template(
    request: TemplateCreateRequest,
    current_user: User = Depends(get_current_user)
):
    """Create notification template (admin only)"""
    if not getattr(current_user, 'is_admin', False):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        result = await template_manager.create_template(
            name=request.name,
            channel=request.channel,
            notification_type=request.notification_type,
            subject_template=request.subject_template,
            body_template=request.body_template,
            html_template=request.html_template,
            variables=request.variables
        )
        
        if result.get("status") == "error":
            raise HTTPException(status_code=400, detail=result.get("error"))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/templates", response_model=List[Dict[str, Any]])
async def list_templates(
    channel: Optional[NotificationChannel] = None,
    notification_type: Optional[NotificationType] = None,
    current_user: User = Depends(get_current_user)
):
    """List notification templates"""
    if not getattr(current_user, 'is_admin', False):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        templates = await template_manager.list_templates(
            channel=channel,
            notification_type=notification_type
        )
        
        return templates
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/templates/{template_id}", response_model=Dict[str, Any])
async def get_template(
    template_id: int,
    current_user: User = Depends(get_current_user)
):
    """Get template by ID"""
    if not getattr(current_user, 'is_admin', False):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        template = await template_manager.get_template(template_id)
        
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        
        return template
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/templates/{template_id}", response_model=Dict[str, Any])
async def update_template(
    template_id: int,
    updates: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """Update template"""
    if not getattr(current_user, 'is_admin', False):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        result = await template_manager.update_template(template_id, **updates)
        
        if result.get("status") == "error":
            raise HTTPException(status_code=400, detail=result.get("error"))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/templates/{template_id}", response_model=Dict[str, Any])
async def delete_template(
    template_id: int,
    current_user: User = Depends(get_current_user)
):
    """Delete template"""
    if not getattr(current_user, 'is_admin', False):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        result = await template_manager.delete_template(template_id)
        
        if result.get("status") == "error":
            raise HTTPException(status_code=400, detail=result.get("error"))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Webhook Endpoints
@router.post("/webhooks/{provider}", response_model=Dict[str, Any])
async def handle_webhook(
    provider: str,
    request: WebhookPayload
):
    """Handle delivery webhooks from notification providers"""
    try:
        result = await notification_manager.handle_webhook(
            provider=provider,
            channel=request.channel,
            payload=request.payload
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Analytics and Admin Endpoints
@router.get("/analytics", response_model=Dict[str, Any])
async def get_analytics(
    start_date: datetime,
    end_date: datetime,
    channel: Optional[NotificationChannel] = None,
    current_user: User = Depends(get_current_user)
):
    """Get notification analytics (admin only)"""
    if not getattr(current_user, 'is_admin', False):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        result = await notification_manager.get_analytics(
            start_date=start_date,
            end_date=end_date,
            channel=channel
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/queue/stats", response_model=Dict[str, Any])
async def get_queue_stats(
    current_user: User = Depends(get_current_user)
):
    """Get queue statistics (admin only)"""
    if not getattr(current_user, 'is_admin', False):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        stats = await scheduler.get_queue_stats()
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/queue/clear-dead-letters", response_model=Dict[str, Any])
async def clear_dead_letter_queue(
    current_user: User = Depends(get_current_user)
):
    """Clear dead letter queue (admin only)"""
    if not getattr(current_user, 'is_admin', False):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        count = await scheduler.clear_dead_letter_queue()
        return {"status": "success", "cleared_count": count}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/queue/reprocess-dead-letters", response_model=Dict[str, Any])
async def reprocess_dead_letters(
    limit: int = Query(100, le=1000),
    current_user: User = Depends(get_current_user)
):
    """Reprocess notifications from dead letter queue (admin only)"""
    if not getattr(current_user, 'is_admin', False):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        result = await scheduler.reprocess_dead_letters(limit)
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health", response_model=Dict[str, Any])
async def health_check():
    """Check notification system health"""
    try:
        health = await notification_manager.health_check()
        
        if health.get("overall") == "unhealthy":
            raise HTTPException(status_code=503, detail="Notification system unhealthy")
        
        return health
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/preferences/statistics", response_model=Dict[str, Any])
async def get_preference_statistics(
    current_user: User = Depends(get_current_user)
):
    """Get notification preference statistics (admin only)"""
    if not getattr(current_user, 'is_admin', False):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        stats = await preferences_manager.get_channel_statistics()
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))