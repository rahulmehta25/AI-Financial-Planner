# Integration Tests

This directory contains comprehensive end-to-end integration tests for the Financial Planning System. These tests verify the complete system functionality across all services, ensuring proper integration between components.

## Test Structure

```
tests/integration/
├── conftest.py                         # Integration test fixtures and configuration
├── pytest.ini                         # Pytest configuration for integration tests
├── base.py                            # Base classes and utilities for integration tests
├── test_user_journey_complete.py      # Complete user journey tests
├── test_notification_delivery.py      # Multi-channel notification delivery tests  
├── test_banking_integration.py        # Banking integration and transaction sync tests
├── test_pdf_generation.py            # PDF generation and download tests
├── test_system_integration.py        # Microservice communication tests
└── README.md                          # This file
```

## Test Categories

### 1. Full User Journey Tests (`test_user_journey_complete.py`)
- **Complete Onboarding Flow**: Registration → Profile → Goals → First Simulation
- **Returning User Journey**: Login → Profile Update → New Simulation → Results Comparison
- **Multi-Session Continuity**: Cross-device session management and data consistency
- **Performance Requirements**: Sub-5 minute complete onboarding

### 2. Multi-Channel Notification Delivery (`test_notification_delivery.py`)
- **Welcome Campaign**: Email, SMS, In-App notifications for new users
- **Goal Achievement**: Multi-channel celebration notifications
- **Market Alerts**: Preference-based alert delivery and throttling
- **Delivery Reliability**: Retry mechanisms, fallback channels, status tracking
- **Webhook Integration**: External system notification delivery

### 3. Banking Integration (`test_banking_integration.py`)
- **Account Connection**: Plaid/Yodlee integration from link creation to data sync
- **Transaction Sync**: Real-time transaction updates via webhooks
- **Multi-Bank Aggregation**: Consolidated view across banking providers
- **Security & Compliance**: Encryption, PCI compliance, audit logging
- **Error Recovery**: Connection failures, re-authentication flows

### 4. PDF Generation & Download (`test_pdf_generation.py`)
- **Complete Generation Flow**: Simulation → Template → PDF → Download
- **Template Customization**: Branding, multi-language, dynamic content
- **Queue Processing**: High-volume PDF generation with prioritization
- **Security Features**: Password protection, watermarking, access control
- **Multi-Format Export**: Excel, CSV, PowerPoint, Interactive HTML

### 5. System Integration (`test_system_integration.py`)
- **Microservice Communication**: Inter-service API calls and data flow
- **API Gateway Integration**: Routing, authentication, rate limiting, load balancing
- **Service Discovery**: Registration, health checks, failover scenarios
- **Distributed Transactions**: Saga patterns, two-phase commit, compensation
- **Event-Driven Architecture**: Pub/Sub, event sourcing, CQRS patterns

## Test Execution

### Prerequisites

1. **Docker Environment**: Required for test containers
```bash
docker --version  # Ensure Docker is installed
docker-compose --version  # Ensure Docker Compose is available
```

2. **Python Dependencies**:
```bash
pip install -r requirements.txt
pip install pytest pytest-asyncio pytest-cov pytest-timeout testcontainers
```

3. **Environment Setup**:
```bash
# Copy and configure test environment
cp env.template .env.test
# Edit .env.test with test-specific configurations
```

### Running Integration Tests

#### Run All Integration Tests
```bash
# From project root
pytest tests/integration/ -v

# With coverage
pytest tests/integration/ --cov=app --cov-report=html

# With detailed output
pytest tests/integration/ -v -s --tb=long
```

#### Run Specific Test Categories
```bash
# User journey tests only
pytest tests/integration/test_user_journey_complete.py -v

# Banking integration tests
pytest tests/integration/test_banking_integration.py -v

# PDF generation tests
pytest tests/integration/test_pdf_generation.py -v

# System integration tests
pytest tests/integration/test_system_integration.py -v

# Notification delivery tests
pytest tests/integration/test_notification_delivery.py -v
```

#### Run Tests by Markers
```bash
# Run only slow tests
pytest tests/integration/ -m "slow" -v

# Run tests requiring external services
pytest tests/integration/ -m "external_service" -v

# Run load/performance tests
pytest tests/integration/ -m "load_test" -v

# Run security tests
pytest tests/integration/ -m "security_test" -v

# Exclude slow tests
pytest tests/integration/ -m "not slow" -v
```

#### Parallel Execution
```bash
# Install pytest-xdist for parallel execution
pip install pytest-xdist

# Run tests in parallel
pytest tests/integration/ -n auto -v
```

### Test Configuration

#### Performance Thresholds
Tests include performance assertions with the following thresholds:
- **User Registration**: < 2 seconds
- **Profile Creation**: < 1 second
- **Goal Creation**: < 0.5 seconds
- **Simulation Execution**: < 30 seconds
- **PDF Generation**: < 20 seconds
- **Notification Delivery**: < 5 seconds

#### Concurrency Limits
- **Max Concurrent Users**: 50
- **Max Concurrent Simulations**: 10
- **Max Concurrent PDFs**: 5

#### Timeout Settings
- **Default Test Timeout**: 300 seconds (5 minutes)
- **Complex Operation Timeout**: 120 seconds (2 minutes)
- **HTTP Request Timeout**: 30 seconds

## Test Data & Fixtures

### User Scenarios
- **Complete User Scenario**: User with profile, goals, and investments
- **Retirement Scenario**: Focused on retirement planning (age 35)
- **Multiple User Scenarios**: 5 users with different risk tolerances

### Mock Services
- **External APIs**: OpenAI, Anthropic, Plaid, Yodlee
- **Notification Services**: Email (SendGrid), SMS (Twilio), Push (FCM)
- **Market Data**: Yahoo Finance, Alpha Vantage, IEX Cloud

### Test Containers
- **PostgreSQL**: Isolated database for integration tests
- **Redis**: Cache and session storage testing
- **Kafka**: Event streaming integration testing

## Debugging Integration Tests

### Logging Configuration
```bash
# Enable debug logging
pytest tests/integration/ --log-cli-level=DEBUG -s

# Save logs to file
pytest tests/integration/ --log-file=integration_tests.log
```

### Database State Inspection
```python
# Access database session in tests
async def test_debug_database_state(integration_db_session):
    from sqlalchemy import text
    result = await integration_db_session.execute(text("SELECT COUNT(*) FROM users"))
    user_count = result.scalar()
    print(f"Users in database: {user_count}")
```

### Service Health Checking
```bash
# Check service health before running tests
curl http://localhost:8000/health
curl http://localhost:8001/health  # User service
curl http://localhost:8002/health  # Banking service
```

## Continuous Integration

### GitHub Actions Integration
```yaml
# .github/workflows/integration-tests.yml
name: Integration Tests
on: [push, pull_request]
jobs:
  integration-tests:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-asyncio pytest-cov testcontainers
      - name: Run integration tests
        run: pytest tests/integration/ --cov=app --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

### Test Environment Variables
Required environment variables for CI/CD:
```bash
TESTING=true
INTEGRATION_TESTING=true
DATABASE_URL=postgresql+asyncpg://test:test@localhost:5432/test_db
SECRET_KEY=test-secret-key
OPENAI_API_KEY=test-openai-key
ANTHROPIC_API_KEY=test-anthropic-key
PLAID_CLIENT_ID=test-plaid-client
PLAID_SECRET=test-plaid-secret
SENDGRID_API_KEY=test-sendgrid-key
TWILIO_ACCOUNT_SID=test-twilio-sid
TWILIO_AUTH_TOKEN=test-twilio-token
```

## Performance Monitoring

### Metrics Collected
- **Operation Duration**: Time taken for each test operation
- **Resource Usage**: CPU and memory consumption during tests
- **Throughput**: Requests per second for load tests
- **Error Rates**: Success/failure ratios for reliability testing

### Performance Reports
```bash
# Generate performance report
pytest tests/integration/ --durations=0 --benchmark-only

# Profile slow tests
pytest tests/integration/ --profile-svg
```

## Troubleshooting

### Common Issues

1. **Docker Container Startup Failures**
   ```bash
   # Check Docker daemon
   docker info
   
   # Check available ports
   netstat -tulpn | grep :5432
   
   # Clean up containers
   docker container prune
   ```

2. **Database Connection Issues**
   ```bash
   # Test database connectivity
   psql -h localhost -p 5434 -U integration -d integration_financial_planning
   
   # Check container logs
   docker logs <container_id>
   ```

3. **Test Timeout Issues**
   ```bash
   # Increase timeout for specific tests
   pytest tests/integration/ --timeout=600
   
   # Run tests sequentially (no parallel)
   pytest tests/integration/ -n 1
   ```

4. **External Service Mock Failures**
   ```python
   # Check mock configuration
   def test_mock_verification(mock_external_services):
       assert mock_external_services['plaid'] is not None
       assert mock_external_services['openai'] is not None
   ```

### Getting Help

1. **Check test logs**: Look at `integration_tests.log` for detailed error information
2. **Review test output**: Use `-v` and `-s` flags for verbose output
3. **Inspect database state**: Use database debugging fixtures
4. **Monitor resource usage**: Check system resources during test execution

## Contributing

### Adding New Integration Tests

1. **Follow naming convention**: `test_<feature>_integration.py`
2. **Use appropriate markers**: Mark tests with relevant pytest markers
3. **Include performance assertions**: Set reasonable performance thresholds
4. **Add cleanup logic**: Ensure tests clean up resources
5. **Document test purpose**: Add comprehensive docstrings

### Test Development Guidelines

1. **Isolation**: Tests should be independent and not rely on other tests
2. **Reproducibility**: Tests should produce consistent results
3. **Coverage**: Aim for comprehensive feature coverage
4. **Performance**: Consider test execution time and resource usage
5. **Maintenance**: Keep tests maintainable and well-documented

## Architecture Integration Verification

These integration tests verify the following architectural components:

### Service Architecture
- ✅ Microservice communication patterns
- ✅ API gateway integration
- ✅ Service discovery and health checks
- ✅ Load balancing and failover

### Data Architecture  
- ✅ Database consistency across services
- ✅ Cache synchronization
- ✅ Event streaming and message queues
- ✅ Data encryption and security

### Business Logic
- ✅ Complete user workflows
- ✅ Financial calculation accuracy
- ✅ Goal tracking and achievement
- ✅ Notification delivery reliability

### External Integrations
- ✅ Banking provider APIs (Plaid, Yodlee)
- ✅ AI/ML service integration
- ✅ Notification service providers
- ✅ Document generation and storage

This comprehensive integration test suite ensures that all system components work together correctly and meet performance, security, and reliability requirements.