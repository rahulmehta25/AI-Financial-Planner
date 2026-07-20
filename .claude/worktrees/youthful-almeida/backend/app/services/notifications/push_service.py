"""
Push Notification Service

Supports multiple push notification providers:
- Firebase Cloud Messaging (FCM) for Android and Web
- Apple Push Notification Service (APNS) for iOS
- Web Push for web browsers

Features:
- Rich notifications with actions
- Topic-based messaging
- Device group messaging
- Delivery tracking
- Badge management
"""

import asyncio
import json
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import httpx
import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from pywebpush import webpush, WebPushException

from .config import notification_config, PUSH_PROVIDERS
from .models import NotificationStatus, NotificationChannel
from .base import BaseNotificationService


logger = logging.getLogger(__name__)


class PushNotificationService(BaseNotificationService):
    """Push notification service with multiple provider support"""

    def __init__(self):
        super().__init__(NotificationChannel.PUSH)
        self.fcm_client = None
        self.apns_key = None
        self.vapid_claims = None
        self._initialize_providers()

    def _initialize_providers(self):
        """Initialize push notification providers"""
        # Initialize FCM
        if PUSH_PROVIDERS["fcm"]["enabled"]:
            self._initialize_fcm()

        # Initialize APNS
        if PUSH_PROVIDERS["apns"]["enabled"]:
            self._initialize_apns()

        # Initialize Web Push
        self._initialize_web_push()

    def _initialize_fcm(self):
        """Initialize Firebase Cloud Messaging"""
        try:
            if notification_config.fcm_credentials_file:
                import firebase_admin
                from firebase_admin import credentials, messaging
                
                cred = credentials.Certificate(notification_config.fcm_credentials_file)
                firebase_admin.initialize_app(cred)
                self.fcm_client = messaging
                logger.info("FCM client initialized successfully")
            elif notification_config.fcm_server_key:
                # Legacy server key approach
                self.fcm_server_key = notification_config.fcm_server_key
                logger.info("FCM server key configured")
        except Exception as e:
            logger.error(f"Failed to initialize FCM: {e}")

    def _initialize_apns(self):
        """Initialize Apple Push Notification Service"""
        try:
            if notification_config.apns_key_file:
                with open(notification_config.apns_key_file, 'rb') as key_file:
                    self.apns_key = serialization.load_pem_private_key(
                        key_file.read(), password=None
                    )
                logger.info("APNS key loaded successfully")
        except Exception as e:
            logger.error(f"Failed to initialize APNS: {e}")

    def _initialize_web_push(self):
        """Initialize Web Push VAPID"""
        try:
            if (notification_config.vapid_public_key and 
                notification_config.vapid_private_key):
                self.vapid_claims = {
                    "sub": notification_config.vapid_subject,
                    "exp": int((datetime.now() + timedelta(hours=12)).timestamp())
                }
                logger.info("Web Push VAPID configured")
        except Exception as e:
            logger.error(f"Failed to initialize Web Push: {e}")

    async def send_notification(
        self,
        recipient: str,
        subject: str,
        body: str,
        device_type: str = "android",
        data: Optional[Dict[str, Any]] = None,
        actions: Optional[List[Dict[str, str]]] = None,
        icon: Optional[str] = None,
        image: Optional[str] = None,
        badge: Optional[str] = None,
        sound: Optional[str] = None,
        priority: str = "normal",
        topic: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Send push notification"""
        try:
            if device_type == "ios":
                return await self._send_apns(
                    recipient, subject, body, data, badge, sound, priority
                )
            elif device_type == "android":
                return await self._send_fcm_android(
                    recipient, subject, body, data, icon, image, actions, priority, topic
                )
            elif device_type == "web":
                return await self._send_web_push(
                    recipient, subject, body, data, icon, image, actions, badge
                )
            else:
                # Auto-detect or send to multiple platforms
                return await self._send_multiplatform(
                    recipient, subject, body, data, actions, icon, image, badge, sound, priority
                )

        except Exception as e:
            logger.error(f"Failed to send push notification to {recipient}: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    async def _send_fcm_android(
        self,
        token: str,
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None,
        icon: Optional[str] = None,
        image: Optional[str] = None,
        actions: Optional[List[Dict[str, str]]] = None,
        priority: str = "normal",
        topic: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send FCM notification to Android"""
        if self.fcm_client:
            return await self._send_fcm_with_sdk(
                token, title, body, data, icon, image, actions, priority, topic
            )
        else:
            return await self._send_fcm_with_api(
                token, title, body, data, icon, image, actions, priority, topic
            )

    async def _send_fcm_with_sdk(
        self,
        token: str,
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None,
        icon: Optional[str] = None,
        image: Optional[str] = None,
        actions: Optional[List[Dict[str, str]]] = None,
        priority: str = "normal",
        topic: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send FCM using Firebase Admin SDK"""
        try:
            # Build notification
            notification = self.fcm_client.Notification(
                title=title,
                body=body,
                image=image
            )

            # Build Android config
            android_config = self.fcm_client.AndroidConfig(
                priority=priority,
                notification=self.fcm_client.AndroidNotification(
                    icon=icon or "ic_notification",
                    color="#1E40AF",
                    sound="default",
                    click_action="FLUTTER_NOTIFICATION_CLICK"
                )
            )

            # Build message
            message = self.fcm_client.Message(
                token=token,
                notification=notification,
                data=data or {},
                android=android_config
            )

            # Send message
            response = await asyncio.get_event_loop().run_in_executor(
                None, self.fcm_client.send, message
            )

            return {
                "status": "success",
                "provider": "fcm",
                "provider_id": response,
                "response": {"message_id": response}
            }

        except Exception as e:
            logger.error(f"FCM SDK send failed: {e}")
            raise

    async def _send_fcm_with_api(
        self,
        token: str,
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None,
        icon: Optional[str] = None,
        image: Optional[str] = None,
        actions: Optional[List[Dict[str, str]]] = None,
        priority: str = "normal",
        topic: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send FCM using HTTP API with server key"""
        url = "https://fcm.googleapis.com/fcm/send"
        headers = {
            "Authorization": f"key={self.fcm_server_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "to": token,
            "notification": {
                "title": title,
                "body": body,
                "icon": icon or "ic_notification",
                "image": image,
                "click_action": "FLUTTER_NOTIFICATION_CLICK"
            },
            "data": data or {},
            "priority": "high" if priority == "high" else "normal"
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            return {
                "status": "success",
                "provider": "fcm",
                "provider_id": result.get("results", [{}])[0].get("message_id"),
                "response": result
            }

    async def _send_apns(
        self,
        token: str,
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None,
        badge: Optional[str] = None,
        sound: Optional[str] = None,
        priority: str = "normal"
    ) -> Dict[str, Any]:
        """Send APNS notification to iOS"""
        if not self.apns_key:
            raise Exception("APNS key not configured")

        # Generate JWT token
        now = datetime.utcnow()
        claims = {
            "iss": notification_config.apns_team_id,
            "iat": now,
            "exp": now + timedelta(hours=1)
        }

        jwt_token = jwt.encode(
            claims,
            self.apns_key,
            algorithm="ES256",
            headers={"kid": notification_config.apns_key_id}
        )

        # Build payload
        payload = {
            "aps": {
                "alert": {
                    "title": title,
                    "body": body
                },
                "sound": sound or "default"
            }
        }

        if badge:
            payload["aps"]["badge"] = int(badge)

        if data:
            payload.update(data)

        # Determine environment
        apns_url = "https://api.push.apple.com"  # Production
        # apns_url = "https://api.development.push.apple.com"  # Development

        headers = {
            "authorization": f"bearer {jwt_token}",
            "apns-topic": notification_config.apns_bundle_id,
            "apns-priority": "10" if priority == "high" else "5"
        }

        url = f"{apns_url}/3/device/{token}"

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url, 
                headers=headers, 
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                return {
                    "status": "success",
                    "provider": "apns",
                    "provider_id": response.headers.get("apns-id"),
                    "response": {"status_code": response.status_code}
                }
            else:
                error_response = response.json() if response.content else {}
                raise Exception(f"APNS error: {error_response}")

    async def _send_web_push(
        self,
        endpoint: str,
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None,
        icon: Optional[str] = None,
        image: Optional[str] = None,
        actions: Optional[List[Dict[str, str]]] = None,
        badge: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send Web Push notification"""
        if not self.vapid_claims:
            raise Exception("Web Push VAPID not configured")

        payload = {
            "title": title,
            "body": body,
            "icon": icon or "/static/icon-192x192.png",
            "badge": badge or "/static/badge-72x72.png",
            "data": data or {},
            "requireInteraction": True,
            "actions": actions or []
        }

        if image:
            payload["image"] = image

        try:
            response = webpush(
                subscription_info={"endpoint": endpoint},
                data=json.dumps(payload),
                vapid_private_key=notification_config.vapid_private_key,
                vapid_claims=self.vapid_claims
            )

            return {
                "status": "success",
                "provider": "web_push",
                "response": {"status_code": response.status_code}
            }

        except WebPushException as e:
            logger.error(f"Web Push error: {e}")
            raise

    async def _send_multiplatform(
        self,
        recipient: str,
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None,
        actions: Optional[List[Dict[str, str]]] = None,
        icon: Optional[str] = None,
        image: Optional[str] = None,
        badge: Optional[str] = None,
        sound: Optional[str] = None,
        priority: str = "normal"
    ) -> Dict[str, Any]:
        """Send to multiple platforms based on token format"""
        # Simple heuristic to determine platform
        if recipient.startswith("https://"):
            # Web push endpoint
            return await self._send_web_push(
                recipient, title, body, data, icon, image, actions, badge
            )
        elif ":" in recipient and len(recipient) > 100:
            # Likely FCM token
            return await self._send_fcm_android(
                recipient, title, body, data, icon, image, actions, priority
            )
        elif len(recipient) == 64:
            # Likely APNS token
            return await self._send_apns(
                recipient, title, body, data, badge, sound, priority
            )
        else:
            raise Exception("Unable to determine device type from token")

    async def send_to_topic(
        self,
        topic: str,
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Send notification to a topic"""
        if not self.fcm_client:
            raise Exception("FCM not configured for topic messaging")

        try:
            message = self.fcm_client.Message(
                topic=topic,
                notification=self.fcm_client.Notification(title=title, body=body),
                data=data or {}
            )

            response = await asyncio.get_event_loop().run_in_executor(
                None, self.fcm_client.send, message
            )

            return {
                "status": "success",
                "provider": "fcm",
                "provider_id": response,
                "topic": topic
            }

        except Exception as e:
            logger.error(f"Topic send failed: {e}")
            raise

    async def subscribe_to_topic(self, tokens: List[str], topic: str) -> Dict[str, Any]:
        """Subscribe tokens to a topic"""
        if not self.fcm_client:
            raise Exception("FCM not configured")

        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None, self.fcm_client.subscribe_to_topic, tokens, topic
            )

            return {
                "status": "success",
                "success_count": response.success_count,
                "failure_count": response.failure_count,
                "errors": [error.reason for error in response.errors]
            }

        except Exception as e:
            logger.error(f"Topic subscription failed: {e}")
            raise

    async def unsubscribe_from_topic(self, tokens: List[str], topic: str) -> Dict[str, Any]:
        """Unsubscribe tokens from a topic"""
        if not self.fcm_client:
            raise Exception("FCM not configured")

        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None, self.fcm_client.unsubscribe_from_topic, tokens, topic
            )

            return {
                "status": "success",
                "success_count": response.success_count,
                "failure_count": response.failure_count
            }

        except Exception as e:
            logger.error(f"Topic unsubscription failed: {e}")
            raise

    async def send_rich_notification(
        self,
        recipient: str,
        title: str,
        body: str,
        image_url: Optional[str] = None,
        actions: Optional[List[Dict[str, str]]] = None,
        deep_link: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Send rich notification with images and actions"""
        enriched_data = data or {}
        
        if deep_link:
            enriched_data["deep_link"] = deep_link

        return await self.send_notification(
            recipient=recipient,
            subject=title,
            body=body,
            data=enriched_data,
            actions=actions,
            image=image_url
        )

    async def handle_webhook(self, provider: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle delivery webhooks from push providers"""
        # FCM doesn't provide delivery webhooks in the same way as email
        # This would typically integrate with analytics services
        return {"status": "received", "provider": provider}

    def get_rate_limit(self) -> Dict[str, int]:
        """Get rate limits for push notifications"""
        return {
            "requests_per_minute": 600,
            "requests_per_hour": 10000,
            "requests_per_day": 100000
        }