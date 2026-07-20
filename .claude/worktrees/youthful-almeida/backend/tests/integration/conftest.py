"""
Integration Test Configuration and Fixtures

This module provides specialized configuration and fixtures for integration tests:
- Extended database fixtures with realistic data
- External service mocking and containers
- Performance monitoring fixtures
- Test environment setup and teardown
- Resource management for complex scenarios
"""
import asyncio
import os
import pytest
import pytest_asyncio
import time
from typing import AsyncGenerator, Generator, Dict, Any
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from httpx import AsyncClient
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer
from testcontainers.kafka import KafkaContainer
from testcontainers.compose import DockerCompose

from app.main import app
from app.database.base import Base
from app.core.config import get_settings
from app.api.deps import get_db, get_current_user
from tests.factories import (
    UserFactory, FinancialProfileFactory, GoalFactory, 
    create_complete_user_scenario, create_retirement_scenario
)
from tests.integration.base import (
    TestEnvironmentManager, integration_test_context
)


# Integration test database configuration
INTEGRATION_DATABASE_URL = "postgresql+asyncpg://integration:integration@localhost:5434/integration_financial_planning"


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the integration test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def integration_postgres_container():
    """Start a PostgreSQL container for integration testing."""
    with PostgresContainer(
        "postgres:15", 
        username="integration", 
        password="integration", 
        dbname="integration_financial_planning",
        port=5434
    ) as postgres:
        yield postgres


@pytest.fixture(scope="session")
def integration_redis_container():
    """Start a Redis container for integration testing."""
    with RedisContainer("redis:7-alpine", port=6380) as redis:
        yield redis


@pytest.fixture(scope="session")
def integration_kafka_container():
    """Start a Kafka container for integration testing."""
    with KafkaContainer("confluentinc/cp-kafka:latest") as kafka:
        yield kafka


@pytest.fixture(scope="session")
async def integration_engine(integration_postgres_container):
    """Create an integration test database engine."""
    database_url = integration_postgres_container.get_connection_url().replace("psycopg2", "asyncpg")
    engine = create_async_engine(database_url, echo=False, pool_size=20, max_overflow=30)
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def integration_db_session(integration_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create an integration database session."""
    async_session = sessionmaker(
        integration_engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def integration_client(integration_db_session) -> AsyncGenerator[AsyncClient, None]:
    """Create an integration test client with database dependency override."""
    
    async def override_get_db():
        yield integration_db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test", timeout=30.0) as client:
        yield client
    
    app.dependency_overrides.clear()


@pytest.fixture
async def complete_user_scenario(integration_db_session: AsyncSession) -> Dict[str, Any]:
    """Create a complete user scenario with profile, goals, and investments."""
    return await create_complete_user_scenario(session=integration_db_session)


@pytest.fixture
async def retirement_scenario(integration_db_session: AsyncSession) -> Dict[str, Any]:
    """Create a retirement planning scenario."""
    return await create_retirement_scenario(session=integration_db_session, age=35)


@pytest.fixture
async def multiple_user_scenarios(integration_db_session: AsyncSession) -> List[Dict[str, Any]]:
    """Create multiple user scenarios for load testing."""
    scenarios = []
    for i in range(5):
        scenario = await create_complete_user_scenario(
            session=integration_db_session,
            risk_tolerance=['conservative', 'moderate', 'aggressive'][i % 3]
        )
        scenarios.append(scenario)
    return scenarios


@pytest.fixture
def test_environment_manager():
    """Provide test environment manager for complex scenarios."""
    return TestEnvironmentManager()


@pytest.fixture
def performance_tracker():
    """Provide performance tracking for integration tests."""
    class PerformanceTracker:
        def __init__(self):
            self.metrics = []
            self.start_times = {}
        
        def start_operation(self, operation_name: str):
            self.start_times[operation_name] = time.time()
        
        def end_operation(self, operation_name: str):
            if operation_name in self.start_times:
                duration = time.time() - self.start_times[operation_name]
                self.metrics.append({
                    'operation': operation_name,
                    'duration': duration,
                    'timestamp': time.time()
                })
                del self.start_times[operation_name]
                return duration
            return None
        
        def get_metrics(self):
            return self.metrics
        
        def get_average_duration(self, operation_name: str):
            operation_metrics = [m for m in self.metrics if m['operation'] == operation_name]
            if operation_metrics:
                return sum(m['duration'] for m in operation_metrics) / len(operation_metrics)
            return None
    
    return PerformanceTracker()


# Mock fixtures for external services
@pytest.fixture
def mock_external_services():
    """Mock all external services for integration testing."""
    mocks = {}
    
    # OpenAI Mock
    mocks['openai'] = AsyncMock()
    mocks['openai'].chat.completions.create.return_value.choices = [
        MagicMock(message=MagicMock(content="Mock AI financial advice"))
    ]
    
    # Anthropic Mock
    mocks['anthropic'] = AsyncMock()
    mocks['anthropic'].messages.create.return_value.content = [
        MagicMock(text="Mock Anthropic financial analysis")
    ]
    
    # Plaid Mock
    mocks['plaid'] = MagicMock()
    mocks['plaid'].accounts_get.return_value = {
        'accounts': [
            {
                'account_id': 'integration_account_123',
                'name': 'Integration Test Checking',
                'type': 'depository',
                'subtype': 'checking',
                'balances': {
                    'available': 10000.00,
                    'current': 10000.00
                }
            }
        ]
    }
    
    mocks['plaid'].transactions_get.return_value = {
        'transactions': [
            {
                'transaction_id': 'integration_txn_001',
                'account_id': 'integration_account_123',
                'amount': 150.00,
                'name': 'Integration Test Transaction',
                'category': ['Food and Drink', 'Restaurants']
            }
        ]
    }
    
    # Email Service Mock
    mocks['email'] = AsyncMock()
    mocks['email'].send.return_value = {
        'message_id': 'integration_email_123',
        'status': 'sent'
    }
    
    # SMS Service Mock
    mocks['sms'] = AsyncMock()
    mocks['sms'].send.return_value = {
        'message_id': 'integration_sms_123',
        'status': 'sent'
    }
    
    # Push Notification Mock
    mocks['push'] = AsyncMock()
    mocks['push'].send.return_value = {
        'message_id': 'integration_push_123',
        'status': 'sent'
    }
    
    return mocks


@pytest.fixture
def mock_market_data_service():
    """Mock market data service for integration testing."""
    mock_service = AsyncMock()
    
    mock_service.get_stock_price.return_value = {
        'symbol': 'AAPL',
        'price': 150.00,
        'change': 2.50,
        'change_percent': 1.69,
        'timestamp': time.time()
    }
    
    mock_service.get_market_data.return_value = {
        'SPY': {'price': 400.00, 'change': 1.25},
        'QQQ': {'price': 350.00, 'change': -0.50},
        'VTI': {'price': 200.00, 'change': 0.75}
    }
    
    return mock_service


@pytest.fixture
def integration_test_data():
    """Provide comprehensive test data for integration scenarios."""
    return {
        'valid_user_data': {
            'email': 'integration@test.com',
            'password': 'IntegrationTest123!',
            'first_name': 'Integration',
            'last_name': 'Tester',
            'phone_number': '+1-555-123-4567',
            'date_of_birth': '1985-01-15'
        },
        'financial_profile_data': {
            'annual_income': 100000.0,
            'monthly_expenses': 6000.0,
            'current_savings': 50000.0,
            'current_debt': 20000.0,
            'investment_experience': 'intermediate',
            'risk_tolerance': 'moderate',
            'investment_timeline': 30,
            'employment_status': 'employed',
            'marital_status': 'married',
            'dependents': 2
        },
        'goal_data': [
            {
                'name': 'Retirement Savings',
                'goal_type': 'retirement',
                'target_amount': 1500000.0,
                'target_date': '2055-01-01',
                'priority': 'high',
                'monthly_contribution': 1200.0
            },
            {
                'name': 'House Down Payment',
                'goal_type': 'major_purchase',
                'target_amount': 120000.0,
                'target_date': '2030-01-01',
                'priority': 'medium',
                'monthly_contribution': 800.0
            },
            {
                'name': 'Emergency Fund',
                'goal_type': 'emergency',
                'target_amount': 36000.0,
                'target_date': '2027-01-01',
                'priority': 'high',
                'monthly_contribution': 500.0
            }
        ],
        'banking_connection_data': {
            'institution_id': 'ins_109508',
            'public_token': 'public-integration-token',
            'account_ids': ['integration_account_123']
        },
        'simulation_data': {
            'simulation_type': 'comprehensive_planning',
            'time_horizon': 30,
            'monte_carlo_runs': 1000,
            'include_goals': True,
            'include_tax_optimization': True,
            'scenario_analysis': True
        }
    }


@pytest.fixture
async def authenticated_integration_client(integration_client: AsyncClient, integration_test_data: Dict[str, Any]):
    """Create authenticated integration client with test user."""
    # Create and authenticate user
    user_data = integration_test_data['valid_user_data']
    
    # Register user
    response = await integration_client.post("/api/v1/auth/register", json=user_data)
    assert response.status_code == 201
    
    user_result = response.json()
    
    # Authenticate
    login_data = {
        "username": user_data["email"],
        "password": user_data["password"]
    }
    
    response = await integration_client.post("/api/v1/auth/login", data=login_data)
    assert response.status_code == 200
    
    token_data = response.json()
    access_token = token_data["access_token"]
    
    # Add auth headers to client
    integration_client.headers.update({"Authorization": f"Bearer {access_token}"})
    
    # Store user info in client for reference
    integration_client.user_data = user_result
    integration_client.auth_token = access_token
    
    yield integration_client


@pytest.fixture
def integration_test_config():
    """Provide integration test configuration."""
    return {
        'test_timeout': 120,  # 2 minutes for complex operations
        'performance_thresholds': {
            'user_registration': 2.0,  # seconds
            'profile_creation': 1.0,
            'goal_creation': 0.5,
            'simulation_execution': 30.0,
            'pdf_generation': 20.0,
            'notification_delivery': 5.0
        },
        'concurrency_limits': {
            'max_concurrent_users': 50,
            'max_concurrent_simulations': 10,
            'max_concurrent_pdfs': 5
        },
        'data_validation': {
            'strict_schema_validation': True,
            'check_data_consistency': True,
            'verify_audit_trails': True
        }
    }


@pytest.fixture(autouse=True)
def setup_integration_environment():
    """Set up integration test environment variables."""
    os.environ.update({
        'TESTING': 'true',
        'INTEGRATION_TESTING': 'true',
        'DATABASE_URL': INTEGRATION_DATABASE_URL,
        'SECRET_KEY': 'integration-test-secret-key-very-long-and-secure',
        'OPENAI_API_KEY': 'integration-test-openai-key',
        'ANTHROPIC_API_KEY': 'integration-test-anthropic-key',
        'PLAID_CLIENT_ID': 'integration-test-plaid-client-id',
        'PLAID_SECRET': 'integration-test-plaid-secret',
        'PLAID_ENV': 'development',
        'SENDGRID_API_KEY': 'integration-test-sendgrid-key',
        'TWILIO_ACCOUNT_SID': 'integration-test-twilio-sid',
        'TWILIO_AUTH_TOKEN': 'integration-test-twilio-token',
        'REDIS_URL': 'redis://localhost:6380',
        'KAFKA_BOOTSTRAP_SERVERS': 'localhost:9092',
        'PDF_STORAGE_PATH': '/tmp/integration_test_pdfs',
        'LOG_LEVEL': 'WARNING'  # Reduce log noise during tests
    })
    
    yield
    
    # Cleanup environment variables
    integration_env_vars = [
        'INTEGRATION_TESTING', 'DATABASE_URL', 'SECRET_KEY',
        'OPENAI_API_KEY', 'ANTHROPIC_API_KEY', 'PLAID_CLIENT_ID',
        'PLAID_SECRET', 'SENDGRID_API_KEY', 'TWILIO_ACCOUNT_SID',
        'TWILIO_AUTH_TOKEN', 'REDIS_URL', 'KAFKA_BOOTSTRAP_SERVERS',
        'PDF_STORAGE_PATH'
    ]
    
    for env_var in integration_env_vars:
        os.environ.pop(env_var, None)


# Resource management fixtures
@pytest.fixture
async def database_cleanup():
    """Provide database cleanup utilities."""
    cleanup_functions = []
    
    def register_cleanup(func):
        cleanup_functions.append(func)
    
    yield register_cleanup
    
    # Run cleanup functions
    for cleanup_func in cleanup_functions:
        try:
            if asyncio.iscoroutinefunction(cleanup_func):
                await cleanup_func()
            else:
                cleanup_func()
        except Exception as e:
            # Log cleanup errors but don't fail the test
            print(f"Cleanup error: {e}")


@pytest.fixture
def file_cleanup():
    """Provide file cleanup utilities."""
    files_to_cleanup = []
    
    def register_file(file_path):
        files_to_cleanup.append(file_path)
    
    yield register_file
    
    # Cleanup files
    import os
    for file_path in files_to_cleanup:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            print(f"File cleanup error: {e}")


# Docker Compose fixture for full integration testing
@pytest.fixture(scope="session")
def docker_compose_services():
    """Start Docker Compose services for full integration testing."""
    compose_path = "/Users/rahulmehta/Desktop/Financial Planning/backend/infrastructure/deployment"
    
    try:
        with DockerCompose(compose_path, compose_file_name="docker-compose.yml") as compose:
            # Wait for services to be ready
            time.sleep(30)  # Allow services to start up
            yield compose
    except Exception as e:
        print(f"Docker Compose services not available: {e}")
        # Yield None so tests can skip if Docker services aren't available
        yield None


# Monitoring and metrics fixtures
@pytest.fixture
def resource_monitor():
    """Provide system resource monitoring for performance tests."""
    import psutil
    
    class ResourceMonitor:
        def __init__(self):
            self.start_cpu = None
            self.start_memory = None
            self.metrics = []
        
        def start_monitoring(self):
            self.start_cpu = psutil.cpu_percent()
            self.start_memory = psutil.virtual_memory().percent
        
        def stop_monitoring(self):
            if self.start_cpu is not None and self.start_memory is not None:
                end_cpu = psutil.cpu_percent()
                end_memory = psutil.virtual_memory().percent
                
                self.metrics.append({
                    'cpu_usage': {
                        'start': self.start_cpu,
                        'end': end_cpu,
                        'delta': end_cpu - self.start_cpu
                    },
                    'memory_usage': {
                        'start': self.start_memory,
                        'end': end_memory,
                        'delta': end_memory - self.start_memory
                    },
                    'timestamp': time.time()
                })
        
        def get_metrics(self):
            return self.metrics
    
    return ResourceMonitor()


# Security testing fixtures
@pytest.fixture
def security_test_tools():
    """Provide security testing utilities."""
    class SecurityTestTools:
        def __init__(self):
            self.security_checks = []
        
        def check_sql_injection(self, client, endpoint, payload):
            """Check for SQL injection vulnerabilities."""
            # This would implement actual SQL injection testing
            pass
        
        def check_xss_vulnerability(self, client, endpoint, payload):
            """Check for XSS vulnerabilities."""
            # This would implement actual XSS testing
            pass
        
        def check_csrf_protection(self, client, endpoint):
            """Check CSRF protection."""
            # This would test CSRF token validation
            pass
        
        def check_rate_limiting(self, client, endpoint, requests_count=100):
            """Check rate limiting implementation."""
            # This would test rate limiting
            pass
    
    return SecurityTestTools()


# Load testing fixtures
@pytest.fixture
def load_test_utils():
    """Provide load testing utilities."""
    class LoadTestUtils:
        def __init__(self):
            self.results = []
        
        async def simulate_concurrent_users(self, client_factory, user_simulation, num_users):
            """Simulate concurrent users."""
            tasks = []
            for i in range(num_users):
                client = await client_factory()
                task = asyncio.create_task(user_simulation(client, user_id=i))
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            return results
        
        def analyze_results(self, results):
            """Analyze load test results."""
            successful = [r for r in results if not isinstance(r, Exception)]
            failed = [r for r in results if isinstance(r, Exception)]
            
            return {
                'total_requests': len(results),
                'successful_requests': len(successful),
                'failed_requests': len(failed),
                'success_rate': len(successful) / len(results) if results else 0
            }
    
    return LoadTestUtils()


# Integration test markers
def pytest_configure(config):
    """Configure pytest markers for integration tests."""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "external_service: mark test as requiring external services"
    )
    config.addinivalue_line(
        "markers", "load_test: mark test as load/performance test"
    )
    config.addinivalue_line(
        "markers", "security_test: mark test as security test"
    )


# Test collection and filtering
def pytest_collection_modifyitems(config, items):
    """Modify test collection for integration tests."""
    for item in items:
        # Add integration marker to all tests in integration directory
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        
        # Add slow marker to tests that might take longer
        if any(keyword in item.name.lower() for keyword in ['load', 'performance', 'stress', 'concurrent']):
            item.add_marker(pytest.mark.slow)
        
        # Add external_service marker to tests requiring external services
        if any(keyword in item.name.lower() for keyword in ['banking', 'notification', 'email', 'sms']):
            item.add_marker(pytest.mark.external_service)