# Financial Planning App - Notification System

A comprehensive notification system supporting multiple channels, templates, and delivery tracking.

## Features

### 📧 Email Notifications
- **Providers**: SendGrid (primary), AWS SES (fallback)
- **Features**: HTML templates, attachments, bounce handling, unsubscribe links
- **Templates**: Welcome, goal achievements, market alerts, security alerts, summaries

### 📱 Push Notifications
- **Providers**: Firebase Cloud Messaging, Apple Push Notification Service, Web Push
- **Features**: Rich notifications, topic messaging, device targeting, badge management
- **Platforms**: iOS, Android, Web browsers

### 💬 SMS Notifications
- **Provider**: Twilio
- **Features**: International support, delivery tracking, phone validation, short links
- **Use Cases**: Security alerts, verification codes, critical market updates

### 🔔 In-App Notifications
- **Features**: Real-time delivery, read/unread tracking, notification center, badge counts
- **Technology**: WebSocket connections, Redis caching

## Architecture

```
NotificationManager
├── EmailService (SendGrid/AWS SES)
├── PushNotificationService (FCM/APNS/WebPush)
├── SMSService (Twilio)
├── InAppNotificationService (WebSocket/Redis)
├── TemplateManager (Jinja2 templates)
├── PreferencesManager (User preferences)
└── NotificationScheduler (Queue management)
```

## Database Models

### Core Tables
- `notification_templates` - Template definitions
- `notification_preferences` - User preferences by channel/type
- `notifications` - Notification records and delivery status
- `notification_logs` - Event tracking and analytics
- `unsubscribe_tokens` - GDPR-compliant unsubscribe management

## API Endpoints

### Sending Notifications
```http
POST /api/v1/notifications/send
POST /api/v1/notifications/send-multi-channel
POST /api/v1/notifications/send-bulk
```

### Preferences Management
```http
GET /api/v1/notifications/preferences
PUT /api/v1/notifications/preferences
PUT /api/v1/notifications/preferences/bulk
PUT /api/v1/notifications/preferences/quiet-hours
POST /api/v1/notifications/preferences/disable-all
```

### Template Management (Admin)
```http
POST /api/v1/notifications/templates
GET /api/v1/notifications/templates
PUT /api/v1/notifications/templates/{id}
DELETE /api/v1/notifications/templates/{id}
```

### Analytics & Monitoring
```http
GET /api/v1/notifications/analytics
GET /api/v1/notifications/queue/stats
GET /api/v1/notifications/health
```

## Configuration

### Environment Variables

```bash
# Email Configuration
NOTIFICATION_SENDGRID_API_KEY=sg_xxx
NOTIFICATION_SENDGRID_FROM_EMAIL=noreply@yourapp.com
NOTIFICATION_AWS_ACCESS_KEY_ID=xxx
NOTIFICATION_AWS_SECRET_ACCESS_KEY=xxx
NOTIFICATION_AWS_SES_FROM_EMAIL=noreply@yourapp.com

# Push Notifications
NOTIFICATION_FCM_SERVER_KEY=xxx
NOTIFICATION_FCM_CREDENTIALS_FILE=/path/to/firebase-credentials.json
NOTIFICATION_APNS_KEY_FILE=/path/to/apns-key.p8
NOTIFICATION_APNS_KEY_ID=xxx
NOTIFICATION_APNS_TEAM_ID=xxx
NOTIFICATION_VAPID_PUBLIC_KEY=xxx
NOTIFICATION_VAPID_PRIVATE_KEY=xxx

# SMS Configuration
NOTIFICATION_TWILIO_ACCOUNT_SID=xxx
NOTIFICATION_TWILIO_AUTH_TOKEN=xxx
NOTIFICATION_TWILIO_FROM_NUMBER=+1234567890

# Redis Configuration
NOTIFICATION_REDIS_URL=redis://localhost:6379
NOTIFICATION_REDIS_DB=1

# Rate Limiting
NOTIFICATION_EMAIL_RATE_LIMIT=100
NOTIFICATION_SMS_RATE_LIMIT=50
NOTIFICATION_PUSH_RATE_LIMIT=1000
```

## Usage Examples

### Send Welcome Email
```python
from app.services.notifications import NotificationManager

manager = NotificationManager()

result = await manager.send_notification(
    user_id=123,
    channel=NotificationChannel.EMAIL,
    notification_type="welcome",
    data={
        "user_name": "John Doe",
        "user_email": "john@example.com",
        "created_date": "January 15, 2024"
    }
)
```

### Send Goal Achievement Push Notification
```python
result = await manager.send_notification(
    user_id=123,
    channel=NotificationChannel.PUSH,
    notification_type="goal_achievement",
    data={
        "goal_name": "Emergency Fund",
        "target_amount": "10000",
        "achievement_date": "2024-01-15"
    },
    priority=NotificationPriority.HIGH
)
```

### Send Security Alert SMS
```python
result = await manager.send_notification(
    user_id=123,
    channel=NotificationChannel.SMS,
    notification_type="security_alert",
    data={
        "alert_type": "Suspicious login",
        "activity_time": "2024-01-15 10:30 AM",
        "location": "New York, NY"
    },
    priority=NotificationPriority.CRITICAL
)
```

### Update User Preferences
```python
from app.services.notifications import PreferencesManager

prefs = PreferencesManager()

await prefs.update_preference(
    user_id=123,
    channel=NotificationChannel.EMAIL,
    notification_type=NotificationType.MARKET_ALERT,
    enabled=True,
    frequency="daily"
)
```

## Template System

### Template Types
- **Email**: Subject + Text + HTML templates
- **SMS**: Text only (160 character limit)
- **Push**: Title + Body
- **In-App**: Title + Body + Actions

### Template Variables
Common variables available in all templates:
- `user_name`, `user_email`, `user_id`
- `app_name`, `app_url`, `support_email`
- `current_date`, `current_year`
- `logo_url`, `brand_color`, `unsubscribe_url`

### Custom Filters
- `currency`: Format monetary values
- `date`: Format dates
- `percentage`: Format percentages

Example template:
```html
<h1>Congratulations {{user_name}}!</h1>
<p>You've achieved your "{{goal_name}}" goal of {{target_amount|currency}}!</p>
<p>Achievement date: {{achievement_date|date}}</p>
```

## Queue Management

### Queue Types
- **Processing Queues**: Immediate delivery by channel
- **Scheduled Queue**: Future delivery
- **Retry Queue**: Failed notifications with exponential backoff
- **Dead Letter Queue**: Permanently failed notifications

### Rate Limiting
- Email: 100/hour per user
- SMS: 50/hour per user  
- Push: 1000/hour per user
- In-App: Unlimited

### Monitoring
- Real-time queue statistics
- Delivery analytics
- Health checks for all services
- Dead letter queue management

## Security & Compliance

### GDPR Compliance
- User data export
- Right to be forgotten
- Unsubscribe tokens
- Preference audit trails

### Security Features
- Webhook signature validation
- Rate limiting protection
- Input sanitization
- Encrypted data storage

## Scaling Considerations

### Horizontal Scaling
- Stateless service design
- Redis-based queue distribution
- Multiple worker processes
- Provider failover support

### Performance Optimization
- Template caching
- Connection pooling
- Batch processing
- Async/await throughout

## Error Handling

### Retry Logic
- Exponential backoff
- Maximum retry limits
- Dead letter queuing
- Error categorization

### Monitoring & Alerting
- Failed notification tracking
- Provider health monitoring
- Queue depth alerts
- Performance metrics

## Development Setup

1. Install dependencies:
```bash
pip install -r app/services/notifications/requirements.txt
```

2. Set environment variables (see Configuration section)

3. Run database migrations:
```bash
alembic upgrade head
```

4. Start the notification scheduler:
```python
from app.services.notifications import NotificationScheduler

scheduler = NotificationScheduler()
await scheduler.start()
```

## Testing

### Unit Tests
```bash
pytest app/services/notifications/tests/
```

### Integration Tests
```bash
pytest app/services/notifications/tests/integration/
```

### Load Testing
```bash
pytest app/services/notifications/tests/load/
```

## Contributing

1. Follow the existing code structure
2. Add tests for new features
3. Update documentation
4. Follow GDPR compliance guidelines
5. Test with multiple providers