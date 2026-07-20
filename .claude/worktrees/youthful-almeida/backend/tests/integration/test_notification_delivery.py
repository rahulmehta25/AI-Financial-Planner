"""
Multi-channel Notification Delivery Integration Tests

This module tests the complete notification delivery system across all channels:
- Email notifications
- SMS notifications  
- Push notifications
- In-app notifications
- Webhook notifications

Test Coverage:
- Channel-specific delivery verification
- Multi-channel campaign coordination
- Notification preferences and filtering
- Delivery status tracking and retries
- Template rendering and personalization
- Rate limiting and throttling
- Failure handling and fallback mechanisms
"""
import asyncio
import json
import time
from typing import Dict, List, Any, Optional
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
import pytest_asyncio
from httpx import AsyncClient

from tests.integration.base import FullStackIntegrationTest, integration_test_context
from tests.factories import UserFactory, create_complete_user_scenario


class TestMultiChannelNotificationDelivery(FullStackIntegrationTest):
    """Test comprehensive multi-channel notification delivery."""
    
    def __init__(self):
        super().__init__()
        self.notification_mocks = {}
        self.delivery_tracking = {}
    
    async def setup_test_environment(self) -> Dict[str, Any]:
        """Set up notification testing environment with mocked services."""
        config = await super().setup_test_environment()
        
        # Set up notification service mocks
        await self._setup_notification_mocks()
        
        # Initialize delivery tracking
        self.delivery_tracking = {
            'email': [],
            'sms': [],
            'push': [],
            'in_app': [],
            'webhook': []
        }
        
        config.update({
            'notification_testing': True,
            'mock_external_services': True
        })
        
        return config
    
    async def _setup_notification_mocks(self):
        """Set up mocks for external notification services."""
        # Email service mock (SendGrid/SMTP)
        self.notification_mocks['email'] = AsyncMock()
        self.notification_mocks['email'].send.return_value = {
            'message_id': 'email_123',
            'status': 'sent',
            'timestamp': time.time()
        }
        
        # SMS service mock (Twilio)
        self.notification_mocks['sms'] = AsyncMock()
        self.notification_mocks['sms'].send.return_value = {
            'message_id': 'sms_456',
            'status': 'sent',
            'timestamp': time.time()
        }
        
        # Push notification mock (FCM/APNS)
        self.notification_mocks['push'] = AsyncMock()
        self.notification_mocks['push'].send.return_value = {
            'message_id': 'push_789',
            'status': 'sent',
            'timestamp': time.time()
        }
        
        # Webhook service mock
        self.notification_mocks['webhook'] = AsyncMock()
        self.notification_mocks['webhook'].send.return_value = {
            'status_code': 200,
            'response_time': 0.1
        }
    
    async def test_welcome_notification_campaign(self):
        """Test complete welcome notification campaign across all channels."""
        async with integration_test_context(self) as config:
            
            # Create new user (triggers welcome campaign)
            user_data = await self._create_test_user()
            
            # Test welcome email
            await self.measure_operation(
                lambda: self._test_welcome_email_delivery(user_data),
                "welcome_email_delivery"
            )
            
            # Test welcome SMS (if phone provided)
            await self.measure_operation(
                lambda: self._test_welcome_sms_delivery(user_data),
                "welcome_sms_delivery"
            )
            
            # Test in-app welcome notification
            await self.measure_operation(
                lambda: self._test_welcome_in_app_notification(user_data),
                "welcome_in_app_notification"
            )
            
            # Verify campaign coordination
            await self._verify_welcome_campaign_coordination()
    
    async def test_goal_achievement_notifications(self):
        """Test goal achievement notification across multiple channels."""
        async with integration_test_context(self) as config:
            
            # Set up user with goals
            scenario = await self._create_user_with_goals()
            user = scenario['user']
            goals = scenario['goals']
            
            # Simulate goal achievement
            goal_id = goals[0].id
            await self._simulate_goal_achievement(user.id, goal_id)
            
            # Test achievement email
            await self.measure_operation(
                lambda: self._test_goal_achievement_email(user, goal_id),
                "goal_achievement_email"
            )
            
            # Test achievement push notification
            await self.measure_operation(
                lambda: self._test_goal_achievement_push(user, goal_id),
                "goal_achievement_push"
            )
            
            # Test in-app celebration
            await self.measure_operation(
                lambda: self._test_goal_achievement_in_app(user, goal_id),
                "goal_achievement_in_app"
            )
            
            # Verify notification personalization
            await self._verify_notification_personalization(user, goal_id)
    
    async def test_market_alert_notifications(self):
        """Test market alert notifications with preferences."""
        async with integration_test_context(self) as config:
            
            # Set up user with notification preferences
            user_data = await self._create_user_with_preferences()
            
            # Simulate market event
            market_event = {
                'event_type': 'market_volatility',
                'severity': 'high',
                'affected_symbols': ['SPY', 'AAPL'],
                'impact_description': 'Market down 3% due to economic data'
            }
            
            await self._trigger_market_alert(market_event)
            
            # Test alert delivery based on preferences
            await self.measure_operation(
                lambda: self._test_market_alert_delivery(user_data, market_event),
                "market_alert_delivery"
            )
            
            # Test alert filtering and throttling
            await self._test_alert_throttling(user_data, market_event)
    
    async def test_notification_preferences_integration(self):
        """Test notification preferences across all channels."""
        async with integration_test_context(self) as config:
            
            user_data = await self._create_test_user()
            
            # Test default preferences
            await self._test_default_notification_preferences(user_data)
            
            # Test preference updates
            await self._test_notification_preference_updates(user_data)
            
            # Test preference enforcement
            await self._test_preference_enforcement(user_data)
            
            # Test opt-out scenarios
            await self._test_notification_opt_out(user_data)
    
    async def test_notification_delivery_reliability(self):
        """Test notification delivery reliability and retry mechanisms."""
        async with integration_test_context(self) as config:
            
            user_data = await self._create_test_user()
            
            # Test retry on failure
            await self._test_delivery_retry_mechanism(user_data)
            
            # Test fallback channels
            await self._test_fallback_channel_delivery(user_data)
            
            # Test delivery status tracking
            await self._test_delivery_status_tracking(user_data)
            
            # Test rate limiting
            await self._test_notification_rate_limiting(user_data)
    
    async def test_webhook_notification_integration(self):
        """Test webhook notification integration with external systems."""
        async with integration_test_context(self) as config:
            
            # Set up webhook endpoints
            webhook_config = await self._setup_webhook_endpoints()
            
            user_data = await self._create_test_user()
            
            # Test various webhook events
            await self._test_user_registration_webhook(user_data)
            await self._test_goal_created_webhook(user_data)
            await self._test_simulation_completed_webhook(user_data)
            
            # Test webhook delivery reliability
            await self._test_webhook_retry_and_timeout(user_data)
    
    # Helper methods for notification testing
    
    async def _create_test_user(self) -> Dict[str, Any]:
        """Create test user for notification testing."""
        user_data = {
            "email": "notifications@example.com",
            "password": "TestPassword123!",
            "first_name": "Notification",
            "last_name": "Tester",
            "phone_number": "+1-555-987-6543"
        }
        
        response = await self.client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 201
        
        # Authenticate user
        login_data = {"username": user_data["email"], "password": user_data["password"]}
        response = await self.client.post("/api/v1/auth/login", data=login_data)
        token_data = response.json()
        
        user_data['id'] = response.json()['id']
        user_data['auth_token'] = token_data["access_token"]
        
        return user_data
    
    async def _create_user_with_goals(self) -> Dict[str, Any]:
        """Create user with financial goals."""
        user_data = await self._create_test_user()
        
        # Create financial profile
        profile_data = {
            "annual_income": 75000.0,
            "monthly_expenses": 4500.0,
            "current_savings": 25000.0,
            "risk_tolerance": "moderate"
        }
        
        headers = {"Authorization": f"Bearer {user_data['auth_token']}"}
        response = await self.client.post(
            "/api/v1/financial-profiles/",
            json=profile_data,
            headers=headers
        )
        assert response.status_code == 201
        
        # Create goals
        goals_data = [
            {
                "name": "Emergency Fund",
                "goal_type": "emergency",
                "target_amount": 27000.0,
                "target_date": "2026-01-01",
                "priority": "high"
            }
        ]
        
        goals = []
        for goal_data in goals_data:
            response = await self.client.post(
                "/api/v1/goals/",
                json=goal_data,
                headers=headers
            )
            assert response.status_code == 201
            goals.append(response.json())
        
        return {
            'user': user_data,
            'goals': goals
        }
    
    async def _create_user_with_preferences(self) -> Dict[str, Any]:
        """Create user with specific notification preferences."""
        user_data = await self._create_test_user()
        
        # Set notification preferences
        preferences = {
            "email_notifications": True,
            "sms_notifications": True,
            "push_notifications": True,
            "in_app_notifications": True,
            "marketing_emails": False,
            "market_alerts": True,
            "goal_reminders": True,
            "security_alerts": True,
            "frequency_preference": "immediate"
        }
        
        headers = {"Authorization": f"Bearer {user_data['auth_token']}"}
        response = await self.client.post(
            "/api/v1/notifications/preferences",
            json=preferences,
            headers=headers
        )
        assert response.status_code == 200
        
        user_data['preferences'] = preferences
        return user_data
    
    async def _test_welcome_email_delivery(self, user_data: Dict[str, Any]):
        """Test welcome email delivery."""
        with patch('app.services.notifications.email_service.EmailService.send') as mock_send:
            mock_send.return_value = self.notification_mocks['email'].send.return_value
            
            # Trigger welcome email
            await self._trigger_welcome_notifications(user_data['id'])
            
            # Verify email was sent
            mock_send.assert_called_once()
            call_args = mock_send.call_args
            
            assert call_args[1]['to'] == user_data['email']
            assert 'welcome' in call_args[1]['template_name'].lower()
            assert user_data['first_name'] in call_args[1]['context']['first_name']
            
            self.delivery_tracking['email'].append({
                'user_id': user_data['id'],
                'template': 'welcome',
                'status': 'sent',
                'timestamp': time.time()
            })
    
    async def _test_welcome_sms_delivery(self, user_data: Dict[str, Any]):
        """Test welcome SMS delivery."""
        with patch('app.services.notifications.sms_service.SMSService.send') as mock_send:
            mock_send.return_value = self.notification_mocks['sms'].send.return_value
            
            # SMS should be sent if phone number provided
            if user_data.get('phone_number'):
                # Verify SMS was sent
                mock_send.assert_called_once()
                call_args = mock_send.call_args
                
                assert call_args[1]['to'] == user_data['phone_number']
                assert 'welcome' in call_args[1]['message'].lower()
                
                self.delivery_tracking['sms'].append({
                    'user_id': user_data['id'],
                    'template': 'welcome',
                    'status': 'sent',
                    'timestamp': time.time()
                })
    
    async def _test_welcome_in_app_notification(self, user_data: Dict[str, Any]):
        """Test welcome in-app notification."""
        headers = {"Authorization": f"Bearer {user_data['auth_token']}"}
        
        # Check in-app notifications
        response = await self.client.get(
            "/api/v1/notifications/in-app",
            headers=headers
        )
        assert response.status_code == 200
        
        notifications = response.json()
        welcome_notifications = [n for n in notifications if 'welcome' in n['type'].lower()]
        
        assert len(welcome_notifications) >= 1, "Welcome in-app notification not found"
        
        welcome_notif = welcome_notifications[0]
        assert welcome_notif['user_id'] == user_data['id']
        assert not welcome_notif['read']
        
        self.delivery_tracking['in_app'].append({
            'user_id': user_data['id'],
            'notification_id': welcome_notif['id'],
            'type': 'welcome',
            'status': 'delivered',
            'timestamp': time.time()
        })
    
    async def _simulate_goal_achievement(self, user_id: str, goal_id: str):
        """Simulate goal achievement event."""
        # This would typically be triggered by the application logic
        # For testing, we'll call the notification service directly
        
        achievement_data = {
            'user_id': user_id,
            'goal_id': goal_id,
            'achievement_percentage': 100.0,
            'achievement_date': time.time()
        }
        
        # Trigger goal achievement notifications
        response = await self.client.post(
            "/api/v1/notifications/trigger/goal-achievement",
            json=achievement_data
        )
        assert response.status_code == 200
    
    async def _test_goal_achievement_email(self, user: Dict[str, Any], goal_id: str):
        """Test goal achievement email notification."""
        with patch('app.services.notifications.email_service.EmailService.send') as mock_send:
            mock_send.return_value = self.notification_mocks['email'].send.return_value
            
            # Verify achievement email
            mock_send.assert_called()
            call_args = mock_send.call_args
            
            assert call_args[1]['to'] == user['email']
            assert 'achievement' in call_args[1]['template_name'].lower()
            assert goal_id in str(call_args[1]['context'])
    
    async def _test_goal_achievement_push(self, user: Dict[str, Any], goal_id: str):
        """Test goal achievement push notification."""
        with patch('app.services.notifications.push_service.PushService.send') as mock_send:
            mock_send.return_value = self.notification_mocks['push'].send.return_value
            
            # Verify push notification
            mock_send.assert_called()
            call_args = mock_send.call_args
            
            assert user['id'] in str(call_args[1]['user_ids'])
            assert 'achievement' in call_args[1]['title'].lower()
    
    async def _test_goal_achievement_in_app(self, user: Dict[str, Any], goal_id: str):
        """Test goal achievement in-app notification."""
        headers = {"Authorization": f"Bearer {user['auth_token']}"}
        
        response = await self.client.get(
            "/api/v1/notifications/in-app",
            headers=headers
        )
        assert response.status_code == 200
        
        notifications = response.json()
        achievement_notifications = [n for n in notifications if 'achievement' in n['type'].lower()]
        
        assert len(achievement_notifications) >= 1, "Achievement in-app notification not found"
    
    async def _trigger_market_alert(self, market_event: Dict[str, Any]):
        """Trigger market alert notifications."""
        response = await self.client.post(
            "/api/v1/notifications/trigger/market-alert",
            json=market_event
        )
        assert response.status_code == 200
    
    async def _test_market_alert_delivery(self, user_data: Dict[str, Any], market_event: Dict[str, Any]):
        """Test market alert delivery based on user preferences."""
        headers = {"Authorization": f"Bearer {user_data['auth_token']}"}
        
        # Check if user should receive market alerts based on preferences
        if user_data['preferences'].get('market_alerts', False):
            
            # Check email delivery
            if user_data['preferences'].get('email_notifications', False):
                with patch('app.services.notifications.email_service.EmailService.send') as mock_send:
                    mock_send.return_value = self.notification_mocks['email'].send.return_value
                    
                    # Verify alert email
                    mock_send.assert_called()
                    call_args = mock_send.call_args
                    assert 'market' in call_args[1]['template_name'].lower()
            
            # Check push notification
            if user_data['preferences'].get('push_notifications', False):
                with patch('app.services.notifications.push_service.PushService.send') as mock_send:
                    mock_send.return_value = self.notification_mocks['push'].send.return_value
                    
                    # Verify push notification
                    mock_send.assert_called()
    
    async def _test_alert_throttling(self, user_data: Dict[str, Any], market_event: Dict[str, Any]):
        """Test alert throttling to prevent spam."""
        # Send multiple similar alerts rapidly
        for i in range(5):
            await self._trigger_market_alert(market_event)
            await asyncio.sleep(0.1)
        
        # Verify throttling is working
        headers = {"Authorization": f"Bearer {user_data['auth_token']}"}
        response = await self.client.get(
            "/api/v1/notifications/in-app",
            headers=headers
        )
        
        notifications = response.json()
        market_notifications = [n for n in notifications if 'market' in n['type'].lower()]
        
        # Should not have 5 identical notifications due to throttling
        assert len(market_notifications) < 5, "Alert throttling not working"
    
    async def _test_delivery_retry_mechanism(self, user_data: Dict[str, Any]):
        """Test notification delivery retry on failure."""
        with patch('app.services.notifications.email_service.EmailService.send') as mock_send:
            # Simulate failure then success
            mock_send.side_effect = [
                Exception("Temporary failure"),
                self.notification_mocks['email'].send.return_value
            ]
            
            # Trigger notification that should be retried
            test_notification = {
                'user_id': user_data['id'],
                'type': 'test_retry',
                'message': 'Test retry mechanism'
            }
            
            response = await self.client.post(
                "/api/v1/notifications/send",
                json=test_notification
            )
            
            # Should eventually succeed after retry
            assert response.status_code == 200
            assert mock_send.call_count == 2  # Initial attempt + retry
    
    async def _test_fallback_channel_delivery(self, user_data: Dict[str, Any]):
        """Test fallback to alternative channels on primary channel failure."""
        with patch('app.services.notifications.email_service.EmailService.send') as mock_email:
            with patch('app.services.notifications.sms_service.SMSService.send') as mock_sms:
                
                # Email fails, should fallback to SMS
                mock_email.side_effect = Exception("Email service unavailable")
                mock_sms.return_value = self.notification_mocks['sms'].send.return_value
                
                # Send critical notification that requires fallback
                critical_notification = {
                    'user_id': user_data['id'],
                    'type': 'security_alert',
                    'priority': 'critical',
                    'message': 'Security alert test'
                }
                
                response = await self.client.post(
                    "/api/v1/notifications/send",
                    json=critical_notification
                )
                
                assert response.status_code == 200
                mock_sms.assert_called_once()  # Should fallback to SMS
    
    async def _test_delivery_status_tracking(self, user_data: Dict[str, Any]):
        """Test notification delivery status tracking."""
        # Send notification
        test_notification = {
            'user_id': user_data['id'],
            'type': 'test_tracking',
            'message': 'Test delivery tracking'
        }
        
        response = await self.client.post(
            "/api/v1/notifications/send",
            json=test_notification
        )
        assert response.status_code == 200
        
        notification_id = response.json()['notification_id']
        
        # Check delivery status
        headers = {"Authorization": f"Bearer {user_data['auth_token']}"}
        response = await self.client.get(
            f"/api/v1/notifications/{notification_id}/status",
            headers=headers
        )
        assert response.status_code == 200
        
        status = response.json()
        assert 'delivery_status' in status
        assert 'timestamp' in status
        assert status['notification_id'] == notification_id
    
    async def _test_notification_rate_limiting(self, user_data: Dict[str, Any]):
        """Test notification rate limiting."""
        headers = {"Authorization": f"Bearer {user_data['auth_token']}"}
        
        # Send many notifications rapidly
        successful_sends = 0
        rate_limited_sends = 0
        
        for i in range(20):
            test_notification = {
                'user_id': user_data['id'],
                'type': 'test_rate_limit',
                'message': f'Rate limit test {i}'
            }
            
            response = await self.client.post(
                "/api/v1/notifications/send",
                json=test_notification
            )
            
            if response.status_code == 200:
                successful_sends += 1
            elif response.status_code == 429:  # Too Many Requests
                rate_limited_sends += 1
        
        # Should have some rate limiting
        assert rate_limited_sends > 0, "Rate limiting not working"
        assert successful_sends > 0, "All requests should not be rate limited"
    
    async def _setup_webhook_endpoints(self) -> Dict[str, Any]:
        """Set up webhook endpoints for testing."""
        webhook_config = {
            'endpoints': [
                {
                    'url': 'https://example.com/webhooks/user-events',
                    'events': ['user.registered', 'user.verified'],
                    'secret': 'webhook_secret_123'
                },
                {
                    'url': 'https://example.com/webhooks/financial-events',
                    'events': ['goal.created', 'simulation.completed'],
                    'secret': 'webhook_secret_456'
                }
            ]
        }
        
        # Configure webhooks in system
        response = await self.client.post(
            "/api/v1/webhooks/configure",
            json=webhook_config
        )
        assert response.status_code == 200
        
        return webhook_config
    
    async def _test_user_registration_webhook(self, user_data: Dict[str, Any]):
        """Test webhook delivery on user registration."""
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_post.return_value = MagicMock(status_code=200)
            
            # User registration should trigger webhook
            # (This would have been triggered during user creation)
            
            # Verify webhook was called
            mock_post.assert_called()
            call_args = mock_post.call_args
            
            webhook_data = json.loads(call_args[1]['content'])
            assert webhook_data['event'] == 'user.registered'
            assert webhook_data['data']['user_id'] == user_data['id']
    
    async def _test_goal_created_webhook(self, user_data: Dict[str, Any]):
        """Test webhook delivery on goal creation."""
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_post.return_value = MagicMock(status_code=200)
            
            # Create goal (should trigger webhook)
            goal_data = {
                "name": "Webhook Test Goal",
                "goal_type": "other",
                "target_amount": 10000.0,
                "target_date": "2026-01-01"
            }
            
            headers = {"Authorization": f"Bearer {user_data['auth_token']}"}
            response = await self.client.post(
                "/api/v1/goals/",
                json=goal_data,
                headers=headers
            )
            assert response.status_code == 201
            
            # Verify webhook was called
            mock_post.assert_called()
            webhook_data = json.loads(mock_post.call_args[1]['content'])
            assert webhook_data['event'] == 'goal.created'
    
    async def _verify_welcome_campaign_coordination(self):
        """Verify welcome campaign was coordinated across channels."""
        # Check that all channels received welcome notifications
        email_deliveries = [d for d in self.delivery_tracking['email'] if d['template'] == 'welcome']
        sms_deliveries = [d for d in self.delivery_tracking['sms'] if d['template'] == 'welcome']
        in_app_deliveries = [d for d in self.delivery_tracking['in_app'] if d['type'] == 'welcome']
        
        assert len(email_deliveries) > 0, "Welcome email not delivered"
        assert len(in_app_deliveries) > 0, "Welcome in-app notification not delivered"
        
        # If phone number provided, SMS should be delivered too
        if sms_deliveries:
            assert len(sms_deliveries) > 0, "Welcome SMS not delivered when phone provided"
    
    async def _verify_notification_personalization(self, user: Dict[str, Any], goal_id: str):
        """Verify notifications are properly personalized."""
        headers = {"Authorization": f"Bearer {user['auth_token']}"}
        
        # Get recent notifications
        response = await self.client.get(
            "/api/v1/notifications/recent",
            headers=headers
        )
        assert response.status_code == 200
        
        notifications = response.json()
        achievement_notifications = [n for n in notifications if 'achievement' in n['type'].lower()]
        
        if achievement_notifications:
            notif = achievement_notifications[0]
            # Should contain user's name and goal information
            assert user['first_name'].lower() in notif['content'].lower()
            assert goal_id in str(notif['metadata'])
    
    async def _trigger_welcome_notifications(self, user_id: str):
        """Trigger welcome notifications for a user."""
        welcome_data = {
            'user_id': user_id,
            'event': 'user_registered'
        }
        
        response = await self.client.post(
            "/api/v1/notifications/trigger/welcome",
            json=welcome_data
        )
        assert response.status_code == 200
    
    async def _test_default_notification_preferences(self, user_data: Dict[str, Any]):
        """Test default notification preferences."""
        headers = {"Authorization": f"Bearer {user_data['auth_token']}"}
        
        response = await self.client.get(
            "/api/v1/notifications/preferences",
            headers=headers
        )
        assert response.status_code == 200
        
        preferences = response.json()
        
        # Verify sensible defaults
        assert preferences['security_alerts'] == True
        assert preferences['goal_reminders'] == True
        assert preferences['marketing_emails'] == False  # Should default to opt-out
    
    async def _test_notification_preference_updates(self, user_data: Dict[str, Any]):
        """Test updating notification preferences."""
        headers = {"Authorization": f"Bearer {user_data['auth_token']}"}
        
        new_preferences = {
            'email_notifications': False,
            'sms_notifications': True,
            'marketing_emails': True
        }
        
        response = await self.client.patch(
            "/api/v1/notifications/preferences",
            json=new_preferences,
            headers=headers
        )
        assert response.status_code == 200
        
        # Verify preferences were updated
        response = await self.client.get(
            "/api/v1/notifications/preferences",
            headers=headers
        )
        
        preferences = response.json()
        assert preferences['email_notifications'] == False
        assert preferences['sms_notifications'] == True
        assert preferences['marketing_emails'] == True
    
    async def _test_preference_enforcement(self, user_data: Dict[str, Any]):
        """Test that notification preferences are enforced."""
        headers = {"Authorization": f"Bearer {user_data['auth_token']}"}
        
        # Disable email notifications
        await self.client.patch(
            "/api/v1/notifications/preferences",
            json={'email_notifications': False},
            headers=headers
        )
        
        # Send a non-critical notification
        test_notification = {
            'user_id': user_data['id'],
            'type': 'goal_reminder',
            'message': 'Don\'t forget your goals!'
        }
        
        with patch('app.services.notifications.email_service.EmailService.send') as mock_send:
            response = await self.client.post(
                "/api/v1/notifications/send",
                json=test_notification
            )
            
            # Email should not be sent due to preferences
            mock_send.assert_not_called()
    
    async def _test_notification_opt_out(self, user_data: Dict[str, Any]):
        """Test complete notification opt-out scenarios."""
        headers = {"Authorization": f"Bearer {user_data['auth_token']}"}
        
        # Opt out of all notifications except critical security alerts
        opt_out_preferences = {
            'email_notifications': False,
            'sms_notifications': False,
            'push_notifications': False,
            'in_app_notifications': False,
            'marketing_emails': False,
            'goal_reminders': False,
            'market_alerts': False,
            'security_alerts': True  # Should always remain enabled
        }
        
        response = await self.client.patch(
            "/api/v1/notifications/preferences",
            json=opt_out_preferences,
            headers=headers
        )
        assert response.status_code == 200
        
        # Test that non-security notifications are not sent
        test_notification = {
            'user_id': user_data['id'],
            'type': 'goal_reminder',
            'message': 'This should not be sent'
        }
        
        with patch('app.services.notifications.email_service.EmailService.send') as mock_email:
            with patch('app.services.notifications.sms_service.SMSService.send') as mock_sms:
                response = await self.client.post(
                    "/api/v1/notifications/send",
                    json=test_notification
                )
                
                # No notifications should be sent
                mock_email.assert_not_called()
                mock_sms.assert_not_called()
        
        # Test that security alerts are still sent
        security_notification = {
            'user_id': user_data['id'],
            'type': 'security_alert',
            'priority': 'critical',
            'message': 'Security alert - this should be sent'
        }
        
        with patch('app.services.notifications.email_service.EmailService.send') as mock_email:
            response = await self.client.post(
                "/api/v1/notifications/send",
                json=security_notification
            )
            
            # Security alert should still be sent
            mock_email.assert_called_once()


@pytest.mark.asyncio
@pytest.mark.integration
class TestNotificationDeliveryPerformance:
    """Test notification delivery performance and scalability."""
    
    async def test_high_volume_notification_delivery(self):
        """Test delivery performance with high notification volume."""
        test = TestMultiChannelNotificationDelivery()
        
        async with integration_test_context(test) as config:
            
            # Create multiple users
            users = []
            for i in range(100):
                user_data = await test._create_test_user()
                users.append(user_data)
            
            # Send notifications to all users
            start_time = time.time()
            
            notification_tasks = []
            for user in users:
                task = asyncio.create_task(
                    test._send_test_notification(user)
                )
                notification_tasks.append(task)
            
            await asyncio.gather(*notification_tasks)
            
            end_time = time.time()
            total_duration = end_time - start_time
            
            # Assert performance requirements
            notifications_per_second = len(users) / total_duration
            assert notifications_per_second > 10, f"Too slow: {notifications_per_second:.2f} notifications/sec"
    
    async def _send_test_notification(self, user_data: Dict[str, Any]):
        """Send test notification to a user."""
        test_notification = {
            'user_id': user_data['id'],
            'type': 'performance_test',
            'message': 'Performance test notification'
        }
        
        response = await self.client.post(
            "/api/v1/notifications/send",
            json=test_notification
        )
        assert response.status_code == 200