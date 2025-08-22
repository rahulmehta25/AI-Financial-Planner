"""
Pytest configuration and shared fixtures for the test suite.

This file contains:
- Database fixtures for testing
- Authentication fixtures
- Test client fixtures
- Data factory fixtures
- Mock fixtures for external services
"""
import asyncio
import os
import pytest
import pytest_asyncio
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from httpx import AsyncClient
from testcontainers.postgres import PostgresContainer

from app.main import app
from app.database.base import Base
from app.database.models import User, FinancialProfile, Goal, Investment
from app.core.config import get_settings
from app.api.deps import get_db, get_current_user
from tests.factories import UserFactory, FinancialProfileFactory, GoalFactory


# Test database configuration
TEST_DATABASE_URL = "postgresql+asyncpg://test:test@localhost:5433/test_financial_planning"


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def postgres_container():
    """Start a PostgreSQL container for testing."""
    with PostgresContainer("postgres:15", 
                          username="test", 
                          password="test", 
                          dbname="test_financial_planning",
                          port=5433) as postgres:
        yield postgres


@pytest.fixture(scope="session")
async def test_engine(postgres_container):
    """Create a test database engine."""
    database_url = postgres_container.get_connection_url().replace("psycopg2", "asyncpg")
    engine = create_async_engine(database_url, echo=False)
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a database session for testing."""
    async_session = sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def test_client(db_session) -> AsyncGenerator[AsyncClient, None]:
    """Create a test client with database dependency override."""
    
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
    
    app.dependency_overrides.clear()


@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user."""
    user = await UserFactory.create(session=db_session)
    return user


@pytest.fixture
async def authenticated_client(test_client: AsyncClient, test_user: User) -> AsyncClient:
    """Create an authenticated test client."""
    
    def override_get_current_user():
        return test_user
    
    app.dependency_overrides[get_current_user] = override_get_current_user
    
    yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
async def test_financial_profile(db_session: AsyncSession, test_user: User) -> FinancialProfile:
    """Create a test financial profile."""
    profile = await FinancialProfileFactory.create(session=db_session, user_id=test_user.id)
    return profile


@pytest.fixture
async def test_goal(db_session: AsyncSession, test_user: User) -> Goal:
    """Create a test financial goal."""
    goal = await GoalFactory.create(session=db_session, user_id=test_user.id)
    return goal


# Mock fixtures for external services
@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for AI service tests."""
    mock = AsyncMock()
    mock.chat.completions.create.return_value.choices = [
        MagicMock(message=MagicMock(content="Mock AI response"))
    ]
    return mock


@pytest.fixture
def mock_anthropic_client():
    """Mock Anthropic client for AI service tests."""
    mock = AsyncMock()
    mock.messages.create.return_value.content = [
        MagicMock(text="Mock Anthropic response")
    ]
    return mock


@pytest.fixture
def mock_plaid_client():
    """Mock Plaid client for banking service tests."""
    mock = MagicMock()
    mock.accounts_get.return_value = {
        'accounts': [
            {
                'account_id': 'test_account_id',
                'name': 'Test Checking Account',
                'type': 'depository',
                'subtype': 'checking',
                'balances': {
                    'available': 1000.00,
                    'current': 1000.00
                }
            }
        ]
    }
    return mock


@pytest.fixture
def mock_yfinance():
    """Mock yfinance for market data tests."""
    mock = MagicMock()
    mock.download.return_value = MagicMock()
    mock.Ticker.return_value.info = {
        'symbol': 'AAPL',
        'regularMarketPrice': 150.00,
        'marketCap': 2500000000000
    }
    return mock


@pytest.fixture
def mock_redis():
    """Mock Redis client for caching tests."""
    mock = AsyncMock()
    mock.get.return_value = None
    mock.set.return_value = True
    mock.delete.return_value = 1
    return mock


# Performance testing fixtures
@pytest.fixture
def benchmark_settings():
    """Configuration for benchmark tests."""
    return {
        'min_rounds': 5,
        'max_time': 1.0,
        'calibration_precision': 4
    }


# Security testing fixtures
@pytest.fixture
def security_headers():
    """Expected security headers for testing.""" 
    return {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'Content-Security-Policy': "default-src 'self'"
    }


# Data validation fixtures
@pytest.fixture
def valid_financial_data():
    """Valid financial data for testing."""
    return {
        'annual_income': 75000.0,
        'monthly_expenses': 4500.0,
        'current_savings': 25000.0,
        'debt_amount': 15000.0,
        'risk_tolerance': 'moderate',
        'age': 35,
        'retirement_age': 65
    }


@pytest.fixture
def invalid_financial_data():
    """Invalid financial data for testing validation."""
    return {
        'annual_income': -1000.0,  # Negative income
        'monthly_expenses': 15000.0,  # Expenses > income
        'current_savings': -5000.0,  # Negative savings
        'debt_amount': -1000.0,  # Negative debt
        'risk_tolerance': 'invalid',  # Invalid risk tolerance
        'age': 150,  # Invalid age
        'retirement_age': 30  # Retirement age < current age
    }


# Compliance testing fixtures
@pytest.fixture
def compliance_test_data():
    """Test data for compliance verification."""
    return {
        'pii_data': {
            'ssn': '123-45-6789',
            'email': 'test@example.com',
            'phone': '+1-555-123-4567'
        },
        'financial_data': {
            'account_numbers': ['1234567890', '0987654321'],
            'routing_numbers': ['123456789', '987654321']
        }
    }


# Environment setup
@pytest.fixture(autouse=True)
def setup_test_environment():
    """Set up test environment variables."""
    os.environ['TESTING'] = 'true'
    os.environ['DATABASE_URL'] = TEST_DATABASE_URL
    os.environ['SECRET_KEY'] = 'test-secret-key'
    os.environ['OPENAI_API_KEY'] = 'test-openai-key'
    os.environ['ANTHROPIC_API_KEY'] = 'test-anthropic-key'
    os.environ['PLAID_CLIENT_ID'] = 'test-plaid-client-id'
    os.environ['PLAID_SECRET'] = 'test-plaid-secret'
    yield
    # Cleanup environment variables
    for key in ['TESTING', 'DATABASE_URL', 'SECRET_KEY', 'OPENAI_API_KEY', 
                'ANTHROPIC_API_KEY', 'PLAID_CLIENT_ID', 'PLAID_SECRET']:
        os.environ.pop(key, None)