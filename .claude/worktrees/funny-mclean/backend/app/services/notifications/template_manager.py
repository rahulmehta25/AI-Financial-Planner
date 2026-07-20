"""
Notification Template Manager

Handles template loading, rendering, and management for all notification types
"""

import os
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from jinja2 import Environment, FileSystemLoader, Template, TemplateNotFound
import redis.asyncio as redis
from sqlalchemy.orm import Session

from .config import notification_config, TEMPLATE_CONFIG
from .models import NotificationTemplate, NotificationChannel, NotificationType
from app.database.base import get_db


logger = logging.getLogger(__name__)


class NotificationTemplateManager:
    """Manages notification templates across all channels"""

    def __init__(self):
        self.template_path = "app/services/notifications/templates"
        self.redis_client = None
        self.cache_prefix = "template_cache"
        self._initialize_redis()
        self._setup_jinja()

    def _initialize_redis(self):
        """Initialize Redis for template caching"""
        try:
            self.redis_client = redis.from_url(
                notification_config.redis_url,
                db=notification_config.redis_db,
                decode_responses=True
            )
        except Exception as e:
            logger.warning(f"Redis not available for template caching: {e}")

    def _setup_jinja(self):
        """Setup Jinja2 environment"""
        self.jinja_env = Environment(
            loader=FileSystemLoader(self.template_path),
            autoescape=True,
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Add custom filters
        self.jinja_env.filters['currency'] = self._currency_filter
        self.jinja_env.filters['date'] = self._date_filter
        self.jinja_env.filters['percentage'] = self._percentage_filter

    def _currency_filter(self, value: float, currency: str = "USD") -> str:
        """Format currency values"""
        if currency == "USD":
            return f"${value:,.2f}"
        return f"{value:,.2f} {currency}"

    def _date_filter(self, value: datetime, format: str = "%B %d, %Y") -> str:
        """Format date values"""
        if isinstance(value, str):
            try:
                value = datetime.fromisoformat(value.replace('Z', '+00:00'))
            except:
                return value
        return value.strftime(format)

    def _percentage_filter(self, value: float) -> str:
        """Format percentage values"""
        return f"{value:+.2f}%"

    async def render_template(
        self,
        channel: NotificationChannel,
        template_name: str,
        template_data: Dict[str, Any],
        notification_type: Optional[NotificationType] = None
    ) -> Dict[str, str]:
        """Render template for specific channel"""
        try:
            # Check cache first
            cached_result = await self._get_cached_template(
                channel, template_name, template_data
            )
            if cached_result:
                return cached_result

            # Add global template variables
            enriched_data = self._enrich_template_data(template_data)

            if channel == NotificationChannel.EMAIL:
                result = await self._render_email_template(template_name, enriched_data)
            elif channel == NotificationChannel.SMS:
                result = await self._render_sms_template(template_name, enriched_data)
            elif channel == NotificationChannel.PUSH:
                result = await self._render_push_template(template_name, enriched_data)
            elif channel == NotificationChannel.IN_APP:
                result = await self._render_in_app_template(template_name, enriched_data)
            else:
                raise ValueError(f"Unsupported channel: {channel}")

            # Cache the result
            await self._cache_template_result(channel, template_name, template_data, result)

            return result

        except Exception as e:
            logger.error(f"Failed to render template {template_name} for {channel}: {e}")
            raise

    def _enrich_template_data(self, template_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add global template variables"""
        enriched = template_data.copy()
        
        # Add global configuration
        enriched.update(TEMPLATE_CONFIG)
        
        # Add current date/time
        enriched['current_date'] = datetime.now()
        enriched['current_year'] = datetime.now().year
        
        # Add app-specific variables
        enriched.setdefault('app_name', 'Financial Planning App')
        enriched.setdefault('support_email', 'support@financialplanning.com')
        
        return enriched

    async def _render_email_template(
        self,
        template_name: str,
        template_data: Dict[str, Any]
    ) -> Dict[str, str]:
        """Render email template (subject, text, and HTML)"""
        result = {}
        
        # Render subject
        try:
            subject_template = self.jinja_env.get_template(f"email/{template_name}_subject.txt")
            result['subject'] = subject_template.render(**template_data).strip()
        except TemplateNotFound:
            result['subject'] = template_data.get('default_subject', 'Notification')

        # Render text body
        try:
            text_template = self.jinja_env.get_template(f"email/{template_name}.txt")
            result['body'] = text_template.render(**template_data)
        except TemplateNotFound:
            result['body'] = template_data.get('default_body', '')

        # Render HTML body
        try:
            html_template = self.jinja_env.get_template(f"email/{template_name}.html")
            result['html_body'] = html_template.render(**template_data)
        except TemplateNotFound:
            result['html_body'] = None

        return result

    async def _render_sms_template(
        self,
        template_name: str,
        template_data: Dict[str, Any]
    ) -> Dict[str, str]:
        """Render SMS template"""
        try:
            template = self.jinja_env.get_template(f"sms/{template_name}.txt")
            body = template.render(**template_data)
            
            # Ensure SMS length limits
            if len(body) > 160:
                logger.warning(f"SMS template {template_name} exceeds 160 characters")
            
            return {
                'subject': '',  # SMS doesn't have subjects
                'body': body
            }
        except TemplateNotFound:
            return {
                'subject': '',
                'body': template_data.get('default_body', 'Notification')
            }

    async def _render_push_template(
        self,
        template_name: str,
        template_data: Dict[str, Any]
    ) -> Dict[str, str]:
        """Render push notification template"""
        try:
            # Push notifications typically have title and body
            title_template = self.jinja_env.get_template(f"push/{template_name}_title.txt")
            body_template = self.jinja_env.get_template(f"push/{template_name}.txt")
            
            return {
                'subject': title_template.render(**template_data).strip(),
                'body': body_template.render(**template_data)
            }
        except TemplateNotFound:
            return {
                'subject': template_data.get('default_subject', 'Notification'),
                'body': template_data.get('default_body', '')
            }

    async def _render_in_app_template(
        self,
        template_name: str,
        template_data: Dict[str, Any]
    ) -> Dict[str, str]:
        """Render in-app notification template"""
        try:
            title_template = self.jinja_env.get_template(f"in_app/{template_name}_title.txt")
            body_template = self.jinja_env.get_template(f"in_app/{template_name}.txt")
            
            return {
                'subject': title_template.render(**template_data).strip(),
                'body': body_template.render(**template_data)
            }
        except TemplateNotFound:
            return {
                'subject': template_data.get('default_subject', 'Notification'),
                'body': template_data.get('default_body', '')
            }

    async def _get_cached_template(
        self,
        channel: NotificationChannel,
        template_name: str,
        template_data: Dict[str, Any]
    ) -> Optional[Dict[str, str]]:
        """Get template from cache"""
        if not self.redis_client:
            return None

        try:
            # Create cache key based on template and data hash
            import hashlib
            data_hash = hashlib.md5(str(sorted(template_data.items())).encode()).hexdigest()
            cache_key = f"{self.cache_prefix}:{channel.value}:{template_name}:{data_hash}"
            
            cached = await self.redis_client.get(cache_key)
            if cached:
                import json
                return json.loads(cached)
        except Exception as e:
            logger.warning(f"Failed to get cached template: {e}")
        
        return None

    async def _cache_template_result(
        self,
        channel: NotificationChannel,
        template_name: str,
        template_data: Dict[str, Any],
        result: Dict[str, str]
    ):
        """Cache template result"""
        if not self.redis_client:
            return

        try:
            import hashlib
            import json
            
            data_hash = hashlib.md5(str(sorted(template_data.items())).encode()).hexdigest()
            cache_key = f"{self.cache_prefix}:{channel.value}:{template_name}:{data_hash}"
            
            await self.redis_client.setex(
                cache_key,
                notification_config.template_cache_ttl,
                json.dumps(result)
            )
        except Exception as e:
            logger.warning(f"Failed to cache template result: {e}")

    async def create_template(
        self,
        name: str,
        channel: NotificationChannel,
        notification_type: NotificationType,
        subject_template: Optional[str] = None,
        body_template: str = "",
        html_template: Optional[str] = None,
        variables: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Create a new template in the database"""
        try:
            db = next(get_db())
            
            template = NotificationTemplate(
                name=name,
                channel=channel,
                type=notification_type,
                subject_template=subject_template,
                body_template=body_template,
                html_template=html_template,
                variables=variables or []
            )
            
            db.add(template)
            db.commit()
            db.refresh(template)
            db.close()
            
            return {
                "status": "success",
                "template_id": template.id,
                "name": template.name
            }
            
        except Exception as e:
            logger.error(f"Failed to create template: {e}")
            return {"status": "error", "error": str(e)}

    async def update_template(
        self,
        template_id: int,
        **updates
    ) -> Dict[str, Any]:
        """Update an existing template"""
        try:
            db = next(get_db())
            
            template = db.query(NotificationTemplate).filter(
                NotificationTemplate.id == template_id
            ).first()
            
            if not template:
                return {"status": "error", "error": "Template not found"}
            
            for key, value in updates.items():
                if hasattr(template, key):
                    setattr(template, key, value)
            
            template.updated_at = datetime.now()
            db.commit()
            db.close()
            
            # Clear cache for this template
            await self._clear_template_cache(template.name)
            
            return {"status": "success", "template_id": template_id}
            
        except Exception as e:
            logger.error(f"Failed to update template: {e}")
            return {"status": "error", "error": str(e)}

    async def get_template(self, template_id: int) -> Optional[Dict[str, Any]]:
        """Get template by ID"""
        try:
            db = next(get_db())
            
            template = db.query(NotificationTemplate).filter(
                NotificationTemplate.id == template_id
            ).first()
            
            db.close()
            
            if template:
                return {
                    "id": template.id,
                    "name": template.name,
                    "channel": template.channel.value,
                    "type": template.type.value,
                    "subject_template": template.subject_template,
                    "body_template": template.body_template,
                    "html_template": template.html_template,
                    "variables": template.variables,
                    "is_active": template.is_active,
                    "created_at": template.created_at,
                    "updated_at": template.updated_at
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get template: {e}")
            return None

    async def list_templates(
        self,
        channel: Optional[NotificationChannel] = None,
        notification_type: Optional[NotificationType] = None,
        active_only: bool = True
    ) -> List[Dict[str, Any]]:
        """List templates with filters"""
        try:
            db = next(get_db())
            
            query = db.query(NotificationTemplate)
            
            if channel:
                query = query.filter(NotificationTemplate.channel == channel)
            
            if notification_type:
                query = query.filter(NotificationTemplate.type == notification_type)
            
            if active_only:
                query = query.filter(NotificationTemplate.is_active == True)
            
            templates = query.all()
            db.close()
            
            return [
                {
                    "id": t.id,
                    "name": t.name,
                    "channel": t.channel.value,
                    "type": t.type.value,
                    "is_active": t.is_active,
                    "created_at": t.created_at,
                    "updated_at": t.updated_at
                }
                for t in templates
            ]
            
        except Exception as e:
            logger.error(f"Failed to list templates: {e}")
            return []

    async def delete_template(self, template_id: int) -> Dict[str, Any]:
        """Delete a template"""
        try:
            db = next(get_db())
            
            template = db.query(NotificationTemplate).filter(
                NotificationTemplate.id == template_id
            ).first()
            
            if not template:
                return {"status": "error", "error": "Template not found"}
            
            template_name = template.name
            db.delete(template)
            db.commit()
            db.close()
            
            # Clear cache
            await self._clear_template_cache(template_name)
            
            return {"status": "success", "template_id": template_id}
            
        except Exception as e:
            logger.error(f"Failed to delete template: {e}")
            return {"status": "error", "error": str(e)}

    async def _clear_template_cache(self, template_name: str):
        """Clear cache for a specific template"""
        if not self.redis_client:
            return

        try:
            # Clear all cached versions of this template
            pattern = f"{self.cache_prefix}:*:{template_name}:*"
            keys = await self.redis_client.keys(pattern)
            if keys:
                await self.redis_client.delete(*keys)
        except Exception as e:
            logger.warning(f"Failed to clear template cache: {e}")

    async def validate_template(
        self,
        template_content: str,
        template_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate template syntax and rendering"""
        try:
            template = Template(template_content)
            rendered = template.render(**template_data)
            
            return {
                "valid": True,
                "rendered_preview": rendered[:200] + "..." if len(rendered) > 200 else rendered
            }
            
        except Exception as e:
            return {
                "valid": False,
                "error": str(e)
            }

    def get_available_variables(self) -> Dict[str, List[str]]:
        """Get list of available template variables by context"""
        return {
            "user": [
                "user_id", "user_name", "user_email", "user_phone",
                "created_date", "last_login", "timezone"
            ],
            "goal": [
                "goal_id", "goal_name", "target_amount", "current_amount",
                "progress_percentage", "target_date", "achievement_date"
            ],
            "market": [
                "security_name", "symbol", "current_price", "price_change",
                "percentage_change", "alert_type", "alert_time"
            ],
            "security": [
                "alert_type", "activity_time", "location", "ip_address",
                "device_info", "security_url"
            ],
            "system": [
                "app_name", "app_url", "support_email", "current_date",
                "logo_url", "brand_color", "unsubscribe_url"
            ]
        }