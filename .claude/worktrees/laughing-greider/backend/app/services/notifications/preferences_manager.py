"""
Notification Preferences Manager

Handles user notification preferences with:
- Channel-specific preferences
- Frequency settings
- Quiet hours
- Unsubscribe management
- GDPR compliance
- Bulk preference management
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, time
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from .config import notification_config, DEFAULT_PREFERENCES
from .models import (
    NotificationPreference,
    NotificationChannel,
    NotificationType,
    UnsubscribeToken,
    PreferenceUpdate
)
from app.database.base import get_db
import secrets
import hashlib


logger = logging.getLogger(__name__)


class PreferencesManager:
    """Manages user notification preferences"""

    def __init__(self):
        pass

    async def get_user_preferences(self, user_id: int) -> Dict[str, Any]:
        """Get all preferences for a user"""
        try:
            db = next(get_db())
            
            preferences = db.query(NotificationPreference).filter(
                NotificationPreference.user_id == user_id
            ).all()
            
            db.close()
            
            # Organize preferences by channel and type
            result = {
                "user_id": user_id,
                "preferences": {},
                "quiet_hours": {},
                "timezone": "UTC"
            }
            
            for channel in NotificationChannel:
                result["preferences"][channel.value] = {}
                
                # Set defaults first
                for notif_type in NotificationType:
                    default_enabled = DEFAULT_PREFERENCES.get(channel.value, {}).get(
                        notif_type.value, True
                    )
                    result["preferences"][channel.value][notif_type.value] = {
                        "enabled": default_enabled,
                        "frequency": "immediate"
                    }
            
            # Override with user's actual preferences
            for pref in preferences:
                channel_prefs = result["preferences"][pref.channel.value]
                channel_prefs[pref.type.value] = {
                    "enabled": pref.enabled,
                    "frequency": pref.frequency
                }
                
                # Set quiet hours and timezone (use first one found)
                if pref.quiet_hours_start and pref.quiet_hours_end:
                    result["quiet_hours"] = {
                        "start": pref.quiet_hours_start,
                        "end": pref.quiet_hours_end
                    }
                
                if pref.timezone:
                    result["timezone"] = pref.timezone
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get user preferences: {e}")
            return {"error": str(e)}

    async def update_preference(
        self,
        user_id: int,
        channel: NotificationChannel,
        notification_type: NotificationType,
        enabled: bool,
        frequency: Optional[str] = None,
        quiet_hours_start: Optional[str] = None,
        quiet_hours_end: Optional[str] = None,
        timezone: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update a specific preference"""
        try:
            db = next(get_db())
            
            # Find existing preference
            existing = db.query(NotificationPreference).filter(
                and_(
                    NotificationPreference.user_id == user_id,
                    NotificationPreference.channel == channel,
                    NotificationPreference.type == notification_type
                )
            ).first()
            
            if existing:
                # Update existing preference
                existing.enabled = enabled
                if frequency:
                    existing.frequency = frequency
                if quiet_hours_start:
                    existing.quiet_hours_start = quiet_hours_start
                if quiet_hours_end:
                    existing.quiet_hours_end = quiet_hours_end
                if timezone:
                    existing.timezone = timezone
                existing.updated_at = datetime.now()
            else:
                # Create new preference
                new_pref = NotificationPreference(
                    user_id=user_id,
                    channel=channel,
                    type=notification_type,
                    enabled=enabled,
                    frequency=frequency or "immediate",
                    quiet_hours_start=quiet_hours_start,
                    quiet_hours_end=quiet_hours_end,
                    timezone=timezone or "UTC"
                )
                db.add(new_pref)
            
            db.commit()
            db.close()
            
            return {
                "status": "success",
                "user_id": user_id,
                "channel": channel.value,
                "type": notification_type.value,
                "enabled": enabled
            }
            
        except Exception as e:
            logger.error(f"Failed to update preference: {e}")
            return {"status": "error", "error": str(e)}

    async def bulk_update_preferences(
        self,
        user_id: int,
        preferences: List[PreferenceUpdate]
    ) -> Dict[str, Any]:
        """Update multiple preferences at once"""
        results = []
        
        for pref_update in preferences:
            result = await self.update_preference(
                user_id=user_id,
                channel=pref_update.channel,
                notification_type=pref_update.type,
                enabled=pref_update.enabled,
                frequency=pref_update.frequency,
                quiet_hours_start=pref_update.quiet_hours_start,
                quiet_hours_end=pref_update.quiet_hours_end,
                timezone=pref_update.timezone
            )
            results.append(result)
        
        successful = sum(1 for r in results if r.get("status") == "success")
        failed = len(results) - successful
        
        return {
            "status": "completed",
            "total": len(preferences),
            "successful": successful,
            "failed": failed,
            "results": results
        }

    async def set_quiet_hours(
        self,
        user_id: int,
        start_time: str,  # "HH:MM" format
        end_time: str,    # "HH:MM" format
        timezone: str = "UTC"
    ) -> Dict[str, Any]:
        """Set quiet hours for all notifications"""
        try:
            # Validate time format
            self._validate_time_format(start_time)
            self._validate_time_format(end_time)
            
            db = next(get_db())
            
            # Update all existing preferences
            preferences = db.query(NotificationPreference).filter(
                NotificationPreference.user_id == user_id
            ).all()
            
            for pref in preferences:
                pref.quiet_hours_start = start_time
                pref.quiet_hours_end = end_time
                pref.timezone = timezone
                pref.updated_at = datetime.now()
            
            # If no preferences exist, create defaults with quiet hours
            if not preferences:
                await self._create_default_preferences(
                    user_id, quiet_hours_start=start_time,
                    quiet_hours_end=end_time, timezone=timezone
                )
            
            db.commit()
            db.close()
            
            return {
                "status": "success",
                "quiet_hours": {
                    "start": start_time,
                    "end": end_time,
                    "timezone": timezone
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to set quiet hours: {e}")
            return {"status": "error", "error": str(e)}

    def _validate_time_format(self, time_str: str):
        """Validate HH:MM time format"""
        try:
            time.fromisoformat(time_str)
        except ValueError:
            raise ValueError(f"Invalid time format: {time_str}. Use HH:MM format.")

    async def _create_default_preferences(
        self,
        user_id: int,
        quiet_hours_start: Optional[str] = None,
        quiet_hours_end: Optional[str] = None,
        timezone: str = "UTC"
    ):
        """Create default preferences for a new user"""
        db = next(get_db())
        
        for channel, types in DEFAULT_PREFERENCES.items():
            for notif_type, enabled in types.items():
                try:
                    pref = NotificationPreference(
                        user_id=user_id,
                        channel=NotificationChannel(channel),
                        type=NotificationType(notif_type),
                        enabled=enabled,
                        frequency="immediate",
                        quiet_hours_start=quiet_hours_start,
                        quiet_hours_end=quiet_hours_end,
                        timezone=timezone
                    )
                    db.add(pref)
                except ValueError:
                    # Skip invalid enum values
                    continue
        
        db.commit()
        db.close()

    async def check_notification_allowed(
        self,
        user_id: int,
        channel: NotificationChannel,
        notification_type: NotificationType,
        current_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Check if notification is allowed based on preferences"""
        try:
            db = next(get_db())
            
            preference = db.query(NotificationPreference).filter(
                and_(
                    NotificationPreference.user_id == user_id,
                    NotificationPreference.channel == channel,
                    NotificationPreference.type == notification_type
                )
            ).first()
            
            db.close()
            
            # If no preference exists, use defaults
            if not preference:
                default_enabled = DEFAULT_PREFERENCES.get(channel.value, {}).get(
                    notification_type.value, True
                )
                return {
                    "allowed": default_enabled,
                    "reason": "default_preference" if default_enabled else "default_disabled"
                }
            
            # Check if notification type is enabled
            if not preference.enabled:
                return {
                    "allowed": False,
                    "reason": "disabled_by_user"
                }
            
            # Check quiet hours
            if preference.quiet_hours_start and preference.quiet_hours_end:
                current_time = current_time or datetime.now()
                
                # Convert to user's timezone
                import pytz
                try:
                    user_tz = pytz.timezone(preference.timezone)
                    user_time = current_time.astimezone(user_tz).time()
                    
                    start_time = time.fromisoformat(preference.quiet_hours_start)
                    end_time = time.fromisoformat(preference.quiet_hours_end)
                    
                    # Handle overnight quiet hours (e.g., 22:00 - 08:00)
                    if start_time > end_time:
                        in_quiet_hours = user_time >= start_time or user_time <= end_time
                    else:
                        in_quiet_hours = start_time <= user_time <= end_time
                    
                    if in_quiet_hours:
                        return {
                            "allowed": False,
                            "reason": "quiet_hours",
                            "quiet_hours": {
                                "start": preference.quiet_hours_start,
                                "end": preference.quiet_hours_end,
                                "timezone": preference.timezone
                            }
                        }
                except Exception as e:
                    logger.warning(f"Error checking quiet hours: {e}")
            
            return {
                "allowed": True,
                "reason": "allowed",
                "frequency": preference.frequency
            }
            
        except Exception as e:
            logger.error(f"Failed to check notification permission: {e}")
            return {
                "allowed": False,
                "reason": "error",
                "error": str(e)
            }

    async def disable_all_notifications(self, user_id: int) -> Dict[str, Any]:
        """Disable all notifications for a user"""
        try:
            db = next(get_db())
            
            # Update all existing preferences
            updated = db.query(NotificationPreference).filter(
                NotificationPreference.user_id == user_id
            ).update({"enabled": False, "updated_at": datetime.now()})
            
            db.commit()
            db.close()
            
            return {
                "status": "success",
                "message": f"Disabled all notifications for user {user_id}",
                "updated_count": updated
            }
            
        except Exception as e:
            logger.error(f"Failed to disable all notifications: {e}")
            return {"status": "error", "error": str(e)}

    async def enable_channel(
        self,
        user_id: int,
        channel: NotificationChannel
    ) -> Dict[str, Any]:
        """Enable all notifications for a specific channel"""
        try:
            db = next(get_db())
            
            updated = db.query(NotificationPreference).filter(
                and_(
                    NotificationPreference.user_id == user_id,
                    NotificationPreference.channel == channel
                )
            ).update({"enabled": True, "updated_at": datetime.now()})
            
            db.commit()
            db.close()
            
            return {
                "status": "success",
                "message": f"Enabled all {channel.value} notifications",
                "updated_count": updated
            }
            
        except Exception as e:
            logger.error(f"Failed to enable channel: {e}")
            return {"status": "error", "error": str(e)}

    async def disable_channel(
        self,
        user_id: int,
        channel: NotificationChannel
    ) -> Dict[str, Any]:
        """Disable all notifications for a specific channel"""
        try:
            db = next(get_db())
            
            updated = db.query(NotificationPreference).filter(
                and_(
                    NotificationPreference.user_id == user_id,
                    NotificationPreference.channel == channel
                )
            ).update({"enabled": False, "updated_at": datetime.now()})
            
            db.commit()
            db.close()
            
            return {
                "status": "success",
                "message": f"Disabled all {channel.value} notifications",
                "updated_count": updated
            }
            
        except Exception as e:
            logger.error(f"Failed to disable channel: {e}")
            return {"status": "error", "error": str(e)}

    async def create_unsubscribe_token(
        self,
        user_id: int,
        channel: NotificationChannel,
        notification_type: NotificationType,
        expires_days: int = 30
    ) -> str:
        """Create unsubscribe token for email links"""
        try:
            db = next(get_db())
            
            # Generate secure token
            token = secrets.token_urlsafe(32)
            
            # Set expiration
            expires_at = datetime.now() + timedelta(days=expires_days)
            
            unsubscribe_token = UnsubscribeToken(
                user_id=user_id,
                token=token,
                channel=channel,
                type=notification_type,
                expires_at=expires_at
            )
            
            db.add(unsubscribe_token)
            db.commit()
            db.close()
            
            return token
            
        except Exception as e:
            logger.error(f"Failed to create unsubscribe token: {e}")
            raise

    async def process_unsubscribe(self, token: str) -> Dict[str, Any]:
        """Process unsubscribe request using token"""
        try:
            db = next(get_db())
            
            # Find and validate token
            unsubscribe = db.query(UnsubscribeToken).filter(
                and_(
                    UnsubscribeToken.token == token,
                    UnsubscribeToken.used == False,
                    UnsubscribeToken.expires_at > datetime.now()
                )
            ).first()
            
            if not unsubscribe:
                return {
                    "status": "error",
                    "error": "Invalid or expired unsubscribe token"
                }
            
            # Update preference
            result = await self.update_preference(
                user_id=unsubscribe.user_id,
                channel=unsubscribe.channel,
                notification_type=unsubscribe.type,
                enabled=False
            )
            
            # Mark token as used
            unsubscribe.used = True
            db.commit()
            db.close()
            
            if result.get("status") == "success":
                return {
                    "status": "success",
                    "message": f"Successfully unsubscribed from {unsubscribe.type.value} {unsubscribe.channel.value} notifications",
                    "user_id": unsubscribe.user_id,
                    "channel": unsubscribe.channel.value,
                    "type": unsubscribe.type.value
                }
            else:
                return result
            
        except Exception as e:
            logger.error(f"Failed to process unsubscribe: {e}")
            return {"status": "error", "error": str(e)}

    async def export_preferences(self, user_id: int) -> Dict[str, Any]:
        """Export user preferences for GDPR compliance"""
        try:
            preferences = await self.get_user_preferences(user_id)
            
            db = next(get_db())
            
            # Get unsubscribe tokens
            tokens = db.query(UnsubscribeToken).filter(
                UnsubscribeToken.user_id == user_id
            ).all()
            
            db.close()
            
            export_data = {
                "user_id": user_id,
                "exported_at": datetime.now().isoformat(),
                "preferences": preferences,
                "unsubscribe_tokens": [
                    {
                        "token": t.token,
                        "channel": t.channel.value,
                        "type": t.type.value,
                        "expires_at": t.expires_at.isoformat(),
                        "used": t.used,
                        "created_at": t.created_at.isoformat()
                    }
                    for t in tokens
                ]
            }
            
            return {
                "status": "success",
                "data": export_data
            }
            
        except Exception as e:
            logger.error(f"Failed to export preferences: {e}")
            return {"status": "error", "error": str(e)}

    async def delete_user_data(self, user_id: int) -> Dict[str, Any]:
        """Delete all user preference data (GDPR right to be forgotten)"""
        try:
            db = next(get_db())
            
            # Delete preferences
            pref_count = db.query(NotificationPreference).filter(
                NotificationPreference.user_id == user_id
            ).delete()
            
            # Delete unsubscribe tokens
            token_count = db.query(UnsubscribeToken).filter(
                UnsubscribeToken.user_id == user_id
            ).delete()
            
            db.commit()
            db.close()
            
            return {
                "status": "success",
                "message": "All user preference data deleted",
                "deleted_preferences": pref_count,
                "deleted_tokens": token_count
            }
            
        except Exception as e:
            logger.error(f"Failed to delete user data: {e}")
            return {"status": "error", "error": str(e)}

    async def get_channel_statistics(self) -> Dict[str, Any]:
        """Get statistics about notification preferences"""
        try:
            db = next(get_db())
            
            stats = {}
            
            for channel in NotificationChannel:
                channel_stats = {
                    "total_users": 0,
                    "enabled_by_type": {},
                    "disabled_by_type": {}
                }
                
                for notif_type in NotificationType:
                    enabled_count = db.query(NotificationPreference).filter(
                        and_(
                            NotificationPreference.channel == channel,
                            NotificationPreference.type == notif_type,
                            NotificationPreference.enabled == True
                        )
                    ).count()
                    
                    disabled_count = db.query(NotificationPreference).filter(
                        and_(
                            NotificationPreference.channel == channel,
                            NotificationPreference.type == notif_type,
                            NotificationPreference.enabled == False
                        )
                    ).count()
                    
                    channel_stats["enabled_by_type"][notif_type.value] = enabled_count
                    channel_stats["disabled_by_type"][notif_type.value] = disabled_count
                
                total_users = db.query(NotificationPreference.user_id).filter(
                    NotificationPreference.channel == channel
                ).distinct().count()
                
                channel_stats["total_users"] = total_users
                stats[channel.value] = channel_stats
            
            db.close()
            
            return {
                "status": "success",
                "statistics": stats,
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get channel statistics: {e}")
            return {"status": "error", "error": str(e)}