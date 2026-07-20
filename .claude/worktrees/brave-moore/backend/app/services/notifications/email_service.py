"""
Email Notification Service

Supports multiple email providers:
- SendGrid
- AWS SES

Features:
- Template rendering
- Bounce and complaint handling
- Delivery tracking
- Unsubscribe handling
- Rich HTML emails
"""

import asyncio
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
import aiofiles
import sendgrid
from sendgrid.helpers.mail import Mail, Email, To, Content
import boto3
from botocore.exceptions import ClientError
import jinja2
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

from .config import notification_config, EMAIL_PROVIDERS
from .models import NotificationStatus, NotificationChannel, NotificationType
from .base import BaseNotificationService


logger = logging.getLogger(__name__)


class EmailService(BaseNotificationService):
    """Email notification service with multiple provider support"""

    def __init__(self):
        super().__init__(NotificationChannel.EMAIL)
        self.sendgrid_client = None
        self.ses_client = None
        self.template_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader('app/services/notifications/templates/email')
        )
        self._initialize_providers()

    def _initialize_providers(self):
        """Initialize email providers"""
        # Initialize SendGrid
        if EMAIL_PROVIDERS["sendgrid"]["enabled"]:
            try:
                self.sendgrid_client = sendgrid.SendGridAPIClient(
                    api_key=notification_config.sendgrid_api_key
                )
                logger.info("SendGrid client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize SendGrid: {e}")

        # Initialize AWS SES
        if EMAIL_PROVIDERS["aws_ses"]["enabled"]:
            try:
                self.ses_client = boto3.client(
                    'ses',
                    region_name=notification_config.aws_ses_region,
                    aws_access_key_id=notification_config.aws_access_key_id,
                    aws_secret_access_key=notification_config.aws_secret_access_key
                )
                logger.info("AWS SES client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize AWS SES: {e}")

    async def send_notification(
        self,
        recipient: str,
        subject: str,
        body: str,
        html_body: Optional[str] = None,
        template_name: Optional[str] = None,
        template_data: Optional[Dict[str, Any]] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
        priority: str = "normal"
    ) -> Dict[str, Any]:
        """Send email notification"""
        try:
            # Render template if provided
            if template_name:
                rendered_content = await self._render_template(
                    template_name, template_data or {}
                )
                if rendered_content:
                    subject = rendered_content.get('subject', subject)
                    body = rendered_content.get('body', body)
                    html_body = rendered_content.get('html_body', html_body)

            # Choose provider based on priority and availability
            provider_result = await self._send_with_provider(
                recipient=recipient,
                subject=subject,
                body=body,
                html_body=html_body,
                attachments=attachments,
                priority=priority
            )

            return {
                "status": "success",
                "provider": provider_result.get("provider"),
                "provider_id": provider_result.get("provider_id"),
                "response": provider_result.get("response")
            }

        except Exception as e:
            logger.error(f"Failed to send email to {recipient}: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    async def _send_with_provider(
        self,
        recipient: str,
        subject: str,
        body: str,
        html_body: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
        priority: str = "normal"
    ) -> Dict[str, Any]:
        """Send email using available providers in order of priority"""
        
        # Try SendGrid first (higher priority)
        if self.sendgrid_client and EMAIL_PROVIDERS["sendgrid"]["enabled"]:
            try:
                result = await self._send_sendgrid(
                    recipient, subject, body, html_body, attachments
                )
                return {"provider": "sendgrid", **result}
            except Exception as e:
                logger.warning(f"SendGrid failed, trying next provider: {e}")

        # Fallback to AWS SES
        if self.ses_client and EMAIL_PROVIDERS["aws_ses"]["enabled"]:
            try:
                result = await self._send_ses(
                    recipient, subject, body, html_body, attachments
                )
                return {"provider": "aws_ses", **result}
            except Exception as e:
                logger.error(f"AWS SES also failed: {e}")
                raise

        raise Exception("No email providers available")

    async def _send_sendgrid(
        self,
        recipient: str,
        subject: str,
        body: str,
        html_body: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Send email via SendGrid"""
        from_email = Email(
            notification_config.sendgrid_from_email,
            notification_config.sendgrid_from_name
        )
        to_email = To(recipient)

        # Create content
        content = Content("text/plain", body)
        mail = Mail(from_email, to_email, subject, content)

        # Add HTML content if provided
        if html_body:
            mail.add_content(Content("text/html", html_body))

        # Add attachments if provided
        if attachments:
            for attachment in attachments:
                await self._add_sendgrid_attachment(mail, attachment)

        # Add tracking
        mail.tracking_settings = {
            "click_tracking": {"enable": True},
            "open_tracking": {"enable": True},
            "subscription_tracking": {"enable": True}
        }

        # Send email
        response = await asyncio.get_event_loop().run_in_executor(
            None, self.sendgrid_client.send, mail
        )

        return {
            "provider_id": response.headers.get('X-Message-Id'),
            "response": {
                "status_code": response.status_code,
                "headers": dict(response.headers)
            }
        }

    async def _send_ses(
        self,
        recipient: str,
        subject: str,
        body: str,
        html_body: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Send email via AWS SES"""
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = notification_config.aws_ses_from_email or notification_config.sendgrid_from_email
        msg['To'] = recipient

        # Add text part
        text_part = MIMEText(body, 'plain', 'utf-8')
        msg.attach(text_part)

        # Add HTML part if provided
        if html_body:
            html_part = MIMEText(html_body, 'html', 'utf-8')
            msg.attach(html_part)

        # Add attachments if provided
        if attachments:
            for attachment in attachments:
                await self._add_ses_attachment(msg, attachment)

        # Send email
        response = await asyncio.get_event_loop().run_in_executor(
            None,
            self.ses_client.send_raw_email,
            {
                'Source': msg['From'],
                'Destinations': [recipient],
                'RawMessage': {'Data': msg.as_string()}
            }
        )

        return {
            "provider_id": response['MessageId'],
            "response": response
        }

    async def _add_sendgrid_attachment(self, mail, attachment: Dict[str, Any]):
        """Add attachment to SendGrid email"""
        from sendgrid.helpers.mail import Attachment
        import base64

        if 'file_path' in attachment:
            async with aiofiles.open(attachment['file_path'], 'rb') as f:
                file_data = await f.read()
                encoded_data = base64.b64encode(file_data).decode()
        else:
            encoded_data = attachment['data']

        attachment_obj = Attachment(
            file_content=encoded_data,
            file_name=attachment['filename'],
            file_type=attachment.get('content_type', 'application/octet-stream'),
            disposition=attachment.get('disposition', 'attachment')
        )
        mail.add_attachment(attachment_obj)

    async def _add_ses_attachment(self, msg, attachment: Dict[str, Any]):
        """Add attachment to SES email"""
        if 'file_path' in attachment:
            async with aiofiles.open(attachment['file_path'], 'rb') as f:
                file_data = await f.read()
        else:
            file_data = attachment['data']

        part = MIMEBase('application', 'octet-stream')
        part.set_payload(file_data)
        encoders.encode_base64(part)
        part.add_header(
            'Content-Disposition',
            f'attachment; filename= {attachment["filename"]}'
        )
        msg.attach(part)

    async def _render_template(
        self,
        template_name: str,
        template_data: Dict[str, Any]
    ) -> Optional[Dict[str, str]]:
        """Render email template"""
        try:
            # Load template files
            subject_template = self.template_env.get_template(f"{template_name}_subject.txt")
            text_template = self.template_env.get_template(f"{template_name}.txt")
            
            # Try to load HTML template
            html_template = None
            try:
                html_template = self.template_env.get_template(f"{template_name}.html")
            except jinja2.TemplateNotFound:
                pass

            # Render templates
            subject = subject_template.render(**template_data)
            body = text_template.render(**template_data)
            html_body = html_template.render(**template_data) if html_template else None

            return {
                "subject": subject.strip(),
                "body": body,
                "html_body": html_body
            }

        except Exception as e:
            logger.error(f"Failed to render template {template_name}: {e}")
            return None

    async def handle_webhook(self, provider: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle delivery webhooks from email providers"""
        if provider == "sendgrid":
            return await self._handle_sendgrid_webhook(payload)
        elif provider == "aws_ses":
            return await self._handle_ses_webhook(payload)
        else:
            raise ValueError(f"Unknown provider: {provider}")

    async def _handle_sendgrid_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle SendGrid webhook events"""
        events = []
        
        for event in payload:
            event_type = event.get('event')
            message_id = event.get('sg_message_id')
            
            status_mapping = {
                'delivered': NotificationStatus.DELIVERED,
                'open': NotificationStatus.READ,
                'click': NotificationStatus.CLICKED,
                'bounce': NotificationStatus.BOUNCED,
                'dropped': NotificationStatus.FAILED,
                'unsubscribe': NotificationStatus.UNSUBSCRIBED
            }
            
            status = status_mapping.get(event_type)
            if status:
                events.append({
                    'provider_id': message_id,
                    'status': status,
                    'event_data': event,
                    'timestamp': datetime.fromtimestamp(event.get('timestamp', 0))
                })

        return {'events': events}

    async def _handle_ses_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle AWS SES webhook events (SNS notifications)"""
        events = []
        
        message = payload.get('Message', {})
        if isinstance(message, str):
            import json
            message = json.loads(message)
        
        event_type = message.get('eventType')
        message_id = message.get('mail', {}).get('messageId')
        
        status_mapping = {
            'delivery': NotificationStatus.DELIVERED,
            'bounce': NotificationStatus.BOUNCED,
            'complaint': NotificationStatus.REJECTED,
            'reject': NotificationStatus.FAILED
        }
        
        status = status_mapping.get(event_type)
        if status:
            events.append({
                'provider_id': message_id,
                'status': status,
                'event_data': message,
                'timestamp': datetime.now()
            })

        return {'events': events}

    async def create_unsubscribe_link(self, user_id: int, notification_type: str) -> str:
        """Create unsubscribe link for email"""
        # This would typically generate a secure token and store it in the database
        # For now, return a placeholder
        return f"{notification_config.template_config['unsubscribe_url']}?token=placeholder&type={notification_type}"

    async def verify_domain(self, domain: str) -> Dict[str, Any]:
        """Verify email domain for sending"""
        if self.ses_client:
            try:
                response = await asyncio.get_event_loop().run_in_executor(
                    None,
                    self.ses_client.put_identity_verification_attributes,
                    {'Identity': domain}
                )
                return {"status": "success", "response": response}
            except ClientError as e:
                return {"status": "error", "error": str(e)}
        
        return {"status": "error", "error": "No SES client available"}

    async def get_sending_quota(self) -> Dict[str, Any]:
        """Get current sending quota and rate"""
        if self.ses_client:
            try:
                response = await asyncio.get_event_loop().run_in_executor(
                    None, self.ses_client.get_send_quota
                )
                return {
                    "max_24_hour": response.get('Max24HourSend'),
                    "max_send_rate": response.get('MaxSendRate'),
                    "sent_last_24_hours": response.get('SentLast24Hours')
                }
            except ClientError as e:
                logger.error(f"Failed to get sending quota: {e}")
        
        return {"error": "Unable to retrieve quota"}

    async def get_reputation(self) -> Dict[str, Any]:
        """Get sending reputation metrics"""
        if self.ses_client:
            try:
                response = await asyncio.get_event_loop().run_in_executor(
                    None, self.ses_client.get_reputation
                )
                return response
            except ClientError as e:
                logger.error(f"Failed to get reputation: {e}")
        
        return {"error": "Unable to retrieve reputation"}