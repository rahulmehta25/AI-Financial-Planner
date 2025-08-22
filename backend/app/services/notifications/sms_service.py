"""
SMS Notification Service

Supports Twilio for SMS messaging with:
- International support
- Delivery tracking
- Template rendering
- Rate limiting
- Phone number validation
- Short links for better UX
"""

import asyncio
import logging
import re
from typing import Optional, Dict, Any, List
from datetime import datetime
import phonenumbers
from phonenumbers import NumberParseException
from twilio.rest import Client
from twilio.base.exceptions import TwilioException
import httpx

from .config import notification_config, SMS_PROVIDERS
from .models import NotificationStatus, NotificationChannel
from .base import BaseNotificationService


logger = logging.getLogger(__name__)


class SMSService(BaseNotificationService):
    """SMS notification service using Twilio"""

    def __init__(self):
        super().__init__(NotificationChannel.SMS)
        self.twilio_client = None
        self.short_link_service = None
        self._initialize_providers()

    def _initialize_providers(self):
        """Initialize SMS providers"""
        if SMS_PROVIDERS["twilio"]["enabled"]:
            try:
                self.twilio_client = Client(
                    notification_config.twilio_account_sid,
                    notification_config.twilio_auth_token
                )
                logger.info("Twilio client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Twilio: {e}")

    async def send_notification(
        self,
        recipient: str,
        subject: str,
        body: str,
        template_name: Optional[str] = None,
        template_data: Optional[Dict[str, Any]] = None,
        media_urls: Optional[List[str]] = None,
        priority: str = "normal",
        shorten_links: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """Send SMS notification"""
        try:
            # Validate and format phone number
            formatted_phone = await self._format_phone_number(recipient)
            if not formatted_phone:
                raise ValueError(f"Invalid phone number: {recipient}")

            # Render template if provided
            if template_name:
                rendered_content = await self._render_template(
                    template_name, template_data or {}
                )
                if rendered_content:
                    body = rendered_content

            # Shorten links if requested
            if shorten_links:
                body = await self._shorten_links_in_text(body)

            # Send SMS
            result = await self._send_twilio_sms(
                to=formatted_phone,
                body=body,
                media_urls=media_urls
            )

            return {
                "status": "success",
                "provider": "twilio",
                "provider_id": result.get("sid"),
                "response": result
            }

        except Exception as e:
            logger.error(f"Failed to send SMS to {recipient}: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    async def _send_twilio_sms(
        self,
        to: str,
        body: str,
        media_urls: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Send SMS via Twilio"""
        if not self.twilio_client:
            raise Exception("Twilio client not initialized")

        try:
            message_params = {
                "to": to,
                "from_": notification_config.twilio_from_number,
                "body": body
            }

            if media_urls:
                message_params["media_url"] = media_urls

            message = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.twilio_client.messages.create(**message_params)
            )

            return {
                "sid": message.sid,
                "status": message.status,
                "direction": message.direction,
                "date_created": message.date_created,
                "price": message.price,
                "price_unit": message.price_unit
            }

        except TwilioException as e:
            logger.error(f"Twilio SMS send failed: {e}")
            raise

    async def _format_phone_number(self, phone: str) -> Optional[str]:
        """Format and validate phone number"""
        try:
            # Remove any non-digit characters except +
            cleaned = re.sub(r'[^\d+]', '', phone)
            
            # Parse the phone number
            parsed = phonenumbers.parse(cleaned, None)
            
            # Validate the number
            if phonenumbers.is_valid_number(parsed):
                return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
            else:
                logger.warning(f"Invalid phone number: {phone}")
                return None

        except NumberParseException as e:
            logger.warning(f"Failed to parse phone number {phone}: {e}")
            return None

    async def _render_template(
        self,
        template_name: str,
        template_data: Dict[str, Any]
    ) -> Optional[str]:
        """Render SMS template"""
        try:
            # SMS templates are simple text files
            template_path = f"app/services/notifications/templates/sms/{template_name}.txt"
            
            with open(template_path, 'r') as f:
                template_content = f.read()

            # Simple variable substitution
            for key, value in template_data.items():
                template_content = template_content.replace(f"{{{key}}}", str(value))

            return template_content

        except Exception as e:
            logger.error(f"Failed to render SMS template {template_name}: {e}")
            return None

    async def _shorten_links_in_text(self, text: str) -> str:
        """Shorten URLs in text to save character count"""
        # Simple URL pattern
        url_pattern = r'https?://[^\s]+'
        urls = re.findall(url_pattern, text)
        
        for url in urls:
            try:
                short_url = await self._shorten_url(url)
                if short_url:
                    text = text.replace(url, short_url)
            except Exception as e:
                logger.warning(f"Failed to shorten URL {url}: {e}")
                # Continue with original URL if shortening fails

        return text

    async def _shorten_url(self, url: str) -> Optional[str]:
        """Shorten a URL using a URL shortening service"""
        # This would integrate with a service like bit.ly, tinyurl, or your own shortener
        # For now, return the original URL
        
        # Example integration with bit.ly (would need API key)
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api-ssl.bitly.com/v4/shorten",
                headers={"Authorization": f"Bearer {BITLY_TOKEN}"},
                json={"long_url": url}
            )
            if response.status_code == 200:
                return response.json()["link"]
        """
        
        return url  # Return original URL for now

    async def send_verification_code(
        self,
        phone_number: str,
        code: str,
        expires_in_minutes: int = 10
    ) -> Dict[str, Any]:
        """Send verification code via SMS"""
        body = f"Your verification code is: {code}. This code expires in {expires_in_minutes} minutes. Do not share this code with anyone."
        
        return await self.send_notification(
            recipient=phone_number,
            subject="Verification Code",
            body=body,
            priority="high"
        )

    async def send_alert(
        self,
        phone_number: str,
        alert_type: str,
        message: str,
        action_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send security or financial alert"""
        body = f"ALERT: {message}"
        
        if action_url:
            body += f" Take action: {action_url}"

        return await self.send_notification(
            recipient=phone_number,
            subject=f"{alert_type} Alert",
            body=body,
            priority="high"
        )

    async def send_reminder(
        self,
        phone_number: str,
        reminder_type: str,
        details: str,
        due_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Send reminder SMS"""
        body = f"Reminder: {details}"
        
        if due_date:
            body += f" Due: {due_date.strftime('%m/%d/%Y')}"

        return await self.send_notification(
            recipient=phone_number,
            subject=f"{reminder_type} Reminder",
            body=body
        )

    async def get_message_status(self, message_sid: str) -> Dict[str, Any]:
        """Get message delivery status from Twilio"""
        if not self.twilio_client:
            raise Exception("Twilio client not initialized")

        try:
            message = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.twilio_client.messages(message_sid).fetch()
            )

            status_mapping = {
                "queued": NotificationStatus.QUEUED,
                "sending": NotificationStatus.SENDING,
                "sent": NotificationStatus.DELIVERED,
                "delivered": NotificationStatus.DELIVERED,
                "undelivered": NotificationStatus.FAILED,
                "failed": NotificationStatus.FAILED
            }

            return {
                "sid": message.sid,
                "status": status_mapping.get(message.status, NotificationStatus.PENDING),
                "twilio_status": message.status,
                "error_code": message.error_code,
                "error_message": message.error_message,
                "price": message.price,
                "price_unit": message.price_unit,
                "date_created": message.date_created,
                "date_sent": message.date_sent,
                "date_updated": message.date_updated
            }

        except TwilioException as e:
            logger.error(f"Failed to get message status: {e}")
            raise

    async def handle_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle Twilio status webhooks"""
        try:
            message_sid = payload.get('MessageSid')
            status = payload.get('MessageStatus')
            
            status_mapping = {
                "delivered": NotificationStatus.DELIVERED,
                "undelivered": NotificationStatus.FAILED,
                "failed": NotificationStatus.FAILED,
                "sent": NotificationStatus.DELIVERED
            }

            event = {
                "provider_id": message_sid,
                "status": status_mapping.get(status, NotificationStatus.PENDING),
                "event_data": payload,
                "timestamp": datetime.now()
            }

            return {"events": [event]}

        except Exception as e:
            logger.error(f"Failed to process Twilio webhook: {e}")
            return {"error": str(e)}

    async def get_account_info(self) -> Dict[str, Any]:
        """Get Twilio account information"""
        if not self.twilio_client:
            raise Exception("Twilio client not initialized")

        try:
            account = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.twilio_client.api.accounts(
                    notification_config.twilio_account_sid
                ).fetch()
            )

            return {
                "account_sid": account.sid,
                "friendly_name": account.friendly_name,
                "status": account.status,
                "type": account.type,
                "date_created": account.date_created,
                "date_updated": account.date_updated
            }

        except TwilioException as e:
            logger.error(f"Failed to get account info: {e}")
            raise

    async def validate_phone_number(self, phone_number: str) -> Dict[str, Any]:
        """Validate phone number using Twilio Lookup API"""
        if not self.twilio_client:
            raise Exception("Twilio client not initialized")

        try:
            phone_number_info = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.twilio_client.lookups.phone_numbers(phone_number).fetch()
            )

            return {
                "phone_number": phone_number_info.phone_number,
                "country_code": phone_number_info.country_code,
                "national_format": phone_number_info.national_format,
                "valid": True
            }

        except TwilioException as e:
            logger.warning(f"Phone number validation failed: {e}")
            return {
                "phone_number": phone_number,
                "valid": False,
                "error": str(e)
            }

    async def get_pricing(self, country_code: str = "US") -> Dict[str, Any]:
        """Get SMS pricing for a country"""
        if not self.twilio_client:
            raise Exception("Twilio client not initialized")

        try:
            pricing = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.twilio_client.pricing.messaging.countries(country_code).fetch()
            )

            return {
                "country": pricing.country,
                "iso_country": pricing.iso_country,
                "outbound_sms_prices": [
                    {
                        "carrier": price.carrier,
                        "mcc": price.mcc,
                        "mnc": price.mnc,
                        "prices": [
                            {
                                "base_price": p.base_price,
                                "current_price": p.current_price,
                                "number_type": p.number_type
                            }
                            for p in price.prices
                        ]
                    }
                    for price in pricing.outbound_sms_prices
                ]
            }

        except TwilioException as e:
            logger.error(f"Failed to get pricing: {e}")
            raise

    def get_rate_limit(self) -> Dict[str, int]:
        """Get rate limits for SMS"""
        return {
            "requests_per_minute": 100,
            "requests_per_hour": 1000,
            "requests_per_day": 10000
        }

    async def check_health(self) -> Dict[str, Any]:
        """Check SMS service health"""
        if not self.twilio_client:
            return {
                "status": "unhealthy",
                "error": "Twilio client not initialized"
            }

        try:
            # Test API connectivity
            await self.get_account_info()
            return {
                "status": "healthy",
                "provider": "twilio",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }