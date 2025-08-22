# Market Data Streaming System

A comprehensive real-time market data streaming system that integrates multiple data providers with WebSocket streaming, Redis caching, alert mechanisms, and comprehensive monitoring.

## Architecture Overview

The system consists of several integrated components:

- **Data Providers**: Alpha Vantage, Yahoo Finance, and IEX Cloud integrations
- **Caching Layer**: Redis-based caching with intelligent TTL management
- **Streaming Engine**: WebSocket server for real-time data distribution
- **Alert System**: Customizable price alerts with multiple notification channels
- **Storage Layer**: Historical data storage with validation and quality checks
- **Monitoring**: Comprehensive monitoring and logging system

## Features

### 🔌 Multiple Data Providers
- **Alpha Vantage**: Professional-grade financial data
- **Yahoo Finance**: Free, reliable market data
- **IEX Cloud**: High-quality financial data with extensive coverage

### 🚀 Real-time Streaming
- WebSocket server for live price updates
- Client subscription management
- Automatic failover between providers
- Rate limiting and request optimization

### 💾 Intelligent Caching
- Redis-based caching with configurable TTLs
- Cache warming for popular symbols
- Hit/miss ratio tracking
- Automatic cache invalidation

### 🔔 Alert System
- Multiple alert types (price thresholds, volume spikes, moving averages)
- Email, push, and webhook notifications
- User-specific alert limits
- Alert history and acknowledgment

### 📊 Data Storage & Validation
- Historical data storage with PostgreSQL
- Data quality validation and anomaly detection
- Provider comparison and consistency checks
- Automated data cleanup policies

### 📈 Monitoring & Analytics
- Comprehensive system health monitoring
- Performance metrics and alerting
- Structured logging with configurable levels
- Real-time dashboard with system statistics

## Quick Start

### Environment Setup

1. **Install Dependencies**
```bash
pip install -r requirements.txt
```

2. **Set Environment Variables**
```bash
# API Keys (optional but recommended)
export ALPHA_VANTAGE_API_KEY="your_alpha_vantage_key"
export IEX_CLOUD_API_KEY="your_iex_cloud_key"
export IEX_CLOUD_SANDBOX=true  # Use sandbox for testing

# Redis Configuration
export REDIS_URL="redis://localhost:6379"

# Database Configuration
export DATABASE_URL="postgresql://user:password@localhost/financial_planning"

# Logging
export LOG_LEVEL="INFO"
export MARKET_DATA_LOG_FILE="/var/log/market_data.log"
```

3. **Initialize the System**
```python
from app.services.market_data import MarketDataManager

# Initialize the manager
manager = MarketDataManager()
await manager.initialize()

# Start real-time streaming (optional)
await manager.start_streaming()
```

## API Usage

### Basic Quote Retrieval
```python
# Get a single quote
quote = await manager.get_quote("AAPL")
print(f"AAPL: ${quote.current_price}")

# Get multiple quotes
quotes = await manager.get_multiple_quotes(["AAPL", "GOOGL", "MSFT"])
for quote in quotes:
    print(f"{quote.symbol}: ${quote.current_price}")
```

### Historical Data
```python
from datetime import date, timedelta

# Get historical data
start_date = date.today() - timedelta(days=30)
end_date = date.today()

historical = await manager.get_historical_data(
    symbol="AAPL",
    start_date=start_date,
    end_date=end_date,
    interval="1d"
)

print(f"Retrieved {len(historical.data_points)} data points")
```

### WebSocket Streaming

#### Client-side JavaScript Example
```javascript
const ws = new WebSocket('ws://localhost:8765');

// Subscribe to symbols
ws.onopen = function() {
    ws.send(JSON.stringify({
        type: 'subscribe',
        symbols: ['AAPL', 'GOOGL', 'MSFT']
    }));
};

// Handle market data
ws.onmessage = function(event) {
    const message = JSON.parse(event.data);
    
    if (message.type === 'market_data') {
        console.log(`${message.symbol}: $${message.data.current_price}`);
    }
};
```

#### Python Client Example
```python
import asyncio
import websockets
import json

async def market_data_client():
    uri = "ws://localhost:8765"
    
    async with websockets.connect(uri) as websocket:
        # Subscribe to symbols
        await websocket.send(json.dumps({
            "type": "subscribe",
            "symbols": ["AAPL", "GOOGL", "MSFT"]
        }))
        
        # Listen for updates
        while True:
            message = await websocket.recv()
            data = json.loads(message)
            
            if data["type"] == "market_data":
                print(f"{data['symbol']}: ${data['data']['current_price']}")

# Run the client
asyncio.run(market_data_client())
```

### Price Alerts
```python
from app.services.market_data.models import AlertConfig, AlertType

# Create a price alert
alert = AlertConfig(
    user_id="user_123",
    symbol="AAPL",
    alert_type=AlertType.PRICE_ABOVE,
    threshold_value=150.00,
    email_notification=True,
    webhook_url="https://your-webhook.com/alerts"
)

# Add the alert
success = await manager.stream_manager.alert_engine.add_alert(alert)
print(f"Alert created: {success}")
```

## Configuration

### Provider Configuration
```python
from app.services.market_data.config import config

# Set primary provider
config.primary_provider = DataProvider.YAHOO_FINANCE

# Set fallback providers
config.fallback_providers = [DataProvider.IEX_CLOUD, DataProvider.ALPHA_VANTAGE]

# Configure rate limits
config.yahoo_finance_rate_limit = 2000  # requests per minute
config.alpha_vantage_rate_limit = 5     # requests per minute
config.iex_cloud_rate_limit = 100       # requests per minute
```

### Cache Configuration
```python
# Cache TTL settings (seconds)
config.quote_cache_ttl = 60          # 1 minute for quotes
config.historical_cache_ttl = 3600   # 1 hour for historical data
config.company_info_cache_ttl = 86400 # 24 hours for company info
```

### WebSocket Configuration
```python
# WebSocket server settings
config.websocket_host = "localhost"
config.websocket_port = 8765

# Update intervals
config.real_time_update_interval = 1  # seconds
config.batch_update_interval = 30     # seconds
```

## API Endpoints

The system provides comprehensive REST API endpoints:

### Market Data Endpoints
- `GET /api/v1/market-data/quotes/{symbol}` - Get current quote
- `POST /api/v1/market-data/quotes` - Get multiple quotes
- `GET /api/v1/market-data/historical/{symbol}` - Get historical data
- `GET /api/v1/market-data/company/{symbol}` - Get company information

### Alert Management
- `POST /api/v1/market-data/alerts` - Create alert
- `GET /api/v1/market-data/alerts/{user_id}` - Get user alerts
- `DELETE /api/v1/market-data/alerts/{alert_id}` - Delete alert

### Streaming Control
- `POST /api/v1/market-data/streaming/start` - Start streaming
- `POST /api/v1/market-data/streaming/stop` - Stop streaming
- `GET /api/v1/market-data/streaming/stats` - Get streaming statistics

### System Monitoring
- `GET /api/v1/market-data/status` - System health status
- `GET /api/v1/market-data/providers` - Provider status
- `GET /api/v1/market-data/monitoring/dashboard` - Monitoring dashboard
- `GET /api/v1/market-data/cache/stats` - Cache statistics

## Database Schema

### Market Data Storage
```sql
CREATE TABLE market_data (
    id UUID PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    open_price NUMERIC(15,4),
    high_price NUMERIC(15,4),
    low_price NUMERIC(15,4),
    close_price NUMERIC(15,4),
    current_price NUMERIC(15,4),
    volume BIGINT,
    market_cap NUMERIC(20,2),
    price_change NUMERIC(15,4),
    price_change_percent NUMERIC(8,4),
    data_type VARCHAR(50) NOT NULL,
    provider VARCHAR(50) NOT NULL,
    is_real_time BOOLEAN DEFAULT FALSE,
    additional_data JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Alert Configuration
```sql
CREATE TABLE market_alerts (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id),
    symbol VARCHAR(20) NOT NULL,
    alert_type VARCHAR(50) NOT NULL,
    threshold_value NUMERIC(15,4),
    percentage_threshold NUMERIC(8,4),
    is_active BOOLEAN DEFAULT TRUE,
    expires_at TIMESTAMPTZ,
    email_notification BOOLEAN DEFAULT TRUE,
    push_notification BOOLEAN DEFAULT FALSE,
    webhook_url VARCHAR(500),
    custom_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

## Performance Considerations

### Caching Strategy
- **Quotes**: 60-second TTL for balance between freshness and performance
- **Historical Data**: 1-hour TTL as historical data doesn't change frequently
- **Company Info**: 24-hour TTL as fundamental data changes rarely

### Rate Limiting
- Implements intelligent rate limiting per provider
- Automatic backoff and retry mechanisms
- Request queuing during high-traffic periods

### Database Optimization
- Indexed by symbol, timestamp, and provider
- Partitioning by date for large datasets
- Automated cleanup of old data

### WebSocket Performance
- Connection pooling and client management
- Efficient subscription tracking
- Automatic cleanup of disconnected clients

## Monitoring and Alerting

### Health Checks
```python
# Check system health
health = await manager.health_check()
print(f"Overall status: {health['overall_status']}")

# Check individual components
for component, status in health['components'].items():
    print(f"{component}: {status['status']}")
```

### Performance Metrics
```python
# Get system statistics
stats = manager.get_system_stats()

print(f"Requests: {stats['requests']}")
print(f"Errors: {stats['errors']}")
print(f"Cache hit rate: {stats['cache']['hit_rate']:.2%}")
```

### Custom Alerts
The system supports threshold-based alerting for:
- High error rates
- Poor cache performance
- WebSocket connection issues
- Provider availability

## Testing

### Unit Tests
```bash
# Run all tests
pytest app/services/market_data/tests/

# Run specific test categories
pytest app/services/market_data/tests/test_providers.py
pytest app/services/market_data/tests/test_caching.py
pytest app/services/market_data/tests/test_alerts.py
```

### Integration Tests
```bash
# Test with live providers (requires API keys)
pytest app/services/market_data/tests/integration/

# Test WebSocket streaming
pytest app/services/market_data/tests/test_streaming.py
```

### Performance Tests
```bash
# Load testing
pytest app/services/market_data/tests/performance/
```

## Deployment

### Docker Deployment
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app/ ./app/
EXPOSE 8000 8765

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose
```yaml
version: '3.8'
services:
  market-data:
    build: .
    ports:
      - "8000:8000"
      - "8765:8765"
    environment:
      - REDIS_URL=redis://redis:6379
      - DATABASE_URL=postgresql://user:password@postgres:5432/financial_planning
    depends_on:
      - redis
      - postgres
  
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
  
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: financial_planning
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
    ports:
      - "5432:5432"
```

### Kubernetes Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: market-data-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: market-data-service
  template:
    metadata:
      labels:
        app: market-data-service
    spec:
      containers:
      - name: market-data
        image: financial-planning/market-data:latest
        ports:
        - containerPort: 8000
        - containerPort: 8765
        env:
        - name: REDIS_URL
          value: "redis://redis-service:6379"
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: database-url
```

## Security Considerations

### API Security
- Rate limiting per IP and user
- API key validation for external providers
- Input validation and sanitization
- CORS configuration for WebSocket connections

### Data Security
- Encryption of sensitive configuration
- Secure credential storage
- Audit logging of all operations
- Regular security updates

### Network Security
- TLS/SSL for all external communications
- WebSocket connection authentication
- Firewall rules for database access
- VPN requirements for production access

## Troubleshooting

### Common Issues

#### Provider API Errors
```python
# Check provider status
status = manager.get_provider_status()
for provider, info in status.items():
    if not info['healthy']:
        print(f"Provider {provider} is unhealthy: {info}")
```

#### Cache Issues
```python
# Check cache connectivity
cache_healthy = await manager.cache_manager.redis_cache.health_check()
if not cache_healthy:
    print("Redis cache is not accessible")

# Get cache statistics
cache_stats = await manager.cache_manager.get_detailed_stats()
print(f"Cache hit rate: {cache_stats['manager']['performance']['hit_rate']:.2%}")
```

#### WebSocket Connection Issues
```python
# Check WebSocket server status
streaming_stats = manager.stream_manager.get_streaming_stats()
print(f"Active connections: {streaming_stats['websocket_stats']['connected_clients']}")
print(f"Streaming status: {streaming_stats['streaming']}")
```

### Debug Mode
```python
import logging
logging.getLogger("market_data").setLevel(logging.DEBUG)

# Enable detailed logging
config.log_level = "DEBUG"
```

### Performance Debugging
```python
# Get detailed performance metrics
perf_report = monitor.get_performance_report(hours=1)
print(f"Average response time: {perf_report['avg_response_time']:.2f}s")
print(f"Error rate: {perf_report['error_rate']:.2%}")
```

## Contributing

### Development Setup
1. Clone the repository
2. Create a virtual environment
3. Install development dependencies
4. Set up pre-commit hooks
5. Run tests to ensure everything works

### Code Standards
- Follow PEP 8 style guidelines
- Use type hints throughout
- Write comprehensive docstrings
- Achieve >90% test coverage
- Add appropriate logging

### Pull Request Process
1. Create feature branch
2. Implement changes with tests
3. Update documentation
4. Run full test suite
5. Submit pull request with detailed description

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Create an issue on GitHub
- Check the troubleshooting section
- Review the API documentation
- Consult the monitoring dashboard for system status