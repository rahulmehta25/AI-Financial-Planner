# Financial Planning System - Test Suite

This directory contains a comprehensive test suite for the Financial Planning System, designed to verify all components work together correctly and provide confidence for production deployments.

## 🧪 Test Structure

```
tests/
├── README.md                 # This file
├── conftest.py              # Pytest configuration and fixtures
├── factories.py             # Test data factories using Factory Boy
├── demo_data_generator.py   # Generate realistic demo data
├── unit/                    # Unit tests with mocking
│   ├── test_simulation_service.py
│   ├── test_banking_service.py
│   ├── test_ai_services.py
│   ├── test_monte_carlo_engine.py
│   └── test_ml_models.py
├── integration/             # Integration tests with real services
│   ├── test_auth_endpoints.py
│   ├── test_financial_endpoints.py
│   ├── test_api_integration.py
│   ├── test_database_migrations.py
│   ├── test_user_journey_complete.py
│   └── test_system_integration.py
├── e2e/                     # End-to-end browser tests
│   ├── test_user_journey_e2e.py
│   ├── screenshots/
│   ├── videos/
│   └── downloads/
├── security/                # Security and vulnerability tests
│   └── test_authentication_security.py
├── performance/             # Performance and load tests
│   ├── load_test.py
│   └── locust_tests.py
└── load-testing/           # Advanced load testing scenarios
    ├── scenarios/
    ├── monitoring/
    └── data/
```

## 🚀 Quick Start

### Option 1: Use the Test Runner Script
```bash
# Run all tests
python run_tests.py --suite all

# Run demo test suite
python run_tests.py --suite demo --generate-data

# Quick tests (unit + basic integration)
python run_tests.py --quick --parallel
```

### Option 2: Use Make Commands
```bash
# Quick test suite
make test-quick

# Comprehensive demo
make test-demo

# All tests
make test-all

# System health check
make health-check
```

### Option 3: Direct Pytest Commands
```bash
# Unit tests with coverage
pytest tests/unit/ --cov=app --cov-report=html

# Integration tests
pytest tests/integration/ -v

# Demo test suite
python test_demo.py
```

## 📋 Test Suites

### 1. Demo Test Suite (`test_demo.py`)
**Purpose**: Comprehensive end-to-end testing that simulates a complete user journey.

**Features**:
- User registration and authentication
- Financial profile creation
- Goal setting and management
- Monte Carlo simulations
- ML recommendations
- PDF report generation
- API endpoint validation

**Run**: `python test_demo.py` or `make test-demo`

**Expected Output**:
```
🚀 Starting Comprehensive Financial Planning Demo Test Suite
======================================================================

🏥 Testing system health...
   ✅ Basic health check: AI Financial Planning System API
   ✅ Detailed health check: Database connected

👤 Testing user registration...
   ✅ User registered successfully: demo@example.com

🔐 Testing user authentication...
   ✅ User authenticated successfully

💰 Testing financial profile creation...
   ✅ Financial profile created: uuid-here
   💵 Annual income: $100,000
   🎯 Risk tolerance: moderate

🎯 Testing financial goal creation...
   ✅ Goal created: Retirement Fund - $1,000,000
   ✅ Goal created: Emergency Fund - $50,000
   ✅ Goal created: House Down Payment - $100,000

📊 Testing Monte Carlo simulation...
   ✅ Monte Carlo simulation completed
   🎲 Iterations: 10000
   📈 Success probability: 78.50%
   💰 Expected value: $856,432

🤖 Testing ML recommendations...
   ✅ ML recommendations generated
   📋 Recommendations count: 5

📄 Testing PDF report generation...
   ✅ PDF report generated successfully
   📄 Content length: 245678 bytes

======================================================================
🎉 DEMO TEST SUITE COMPLETED SUCCESSFULLY!
```

### 2. API Test Collection (Postman)
**Purpose**: Validate all API endpoints with realistic requests and responses.

**Files**:
- `api_test_collection.json` - Postman collection
- `api_test_environment.json` - Environment variables

**Import into Postman**:
1. Open Postman
2. Import `api_test_collection.json`
3. Import `api_test_environment.json`
4. Set base_url to your API endpoint
5. Run the collection

**CLI Testing**:
```bash
# Install Newman
npm install -g newman

# Run API tests
newman run api_test_collection.json \
  --environment api_test_environment.json \
  --reporters cli,htmlextra \
  --reporter-htmlextra-export reports/api-test-report.html
```

### 3. End-to-End Browser Tests
**Purpose**: Test the complete user interface and user experience flows.

**Requirements**:
```bash
pip install playwright pytest-playwright
playwright install --with-deps chromium
```

**Run**:
```bash
# Headless mode (CI/CD)
pytest tests/e2e/ --headless

# With browser visible (development)
pytest tests/e2e/ --headed --slowmo=100
```

**Features**:
- Complete user registration and login flow
- Financial profile creation through UI
- Goal setting and management
- Simulation execution and results viewing
- PDF report download
- Responsive design testing
- Performance metrics collection

### 4. Health Check Script
**Purpose**: Verify all system components are running and accessible.

**Run**:
```bash
# Basic health check
python health_check.py

# Detailed check with external services
python health_check.py --detailed

# JSON output for monitoring
python health_check.py --json --save-report health_report.json
```

**Checks**:
- System resources (CPU, memory, disk)
- Database connectivity and performance
- Redis connectivity and performance
- API health endpoints
- External service integrations
- ML service availability
- Banking integration status
- Frontend availability

### 5. Performance Testing
**Purpose**: Ensure the system performs well under load.

**Load Testing with Locust**:
```bash
# Start load test
locust -f tests/performance/locust_tests.py \
  --host=http://localhost:8000 \
  --users=50 \
  --spawn-rate=5 \
  --run-time=120s

# Headless load test
locust -f tests/performance/locust_tests.py \
  --host=http://localhost:8000 \
  --users=100 \
  --spawn-rate=10 \
  --run-time=300s \
  --headless \
  --html=reports/load-test-report.html
```

**Benchmark Testing**:
```bash
pytest tests/performance/ --benchmark-json=benchmark-results.json
```

## 🔧 Test Environment Setup

### Automated Setup
```bash
# Set up everything automatically
make setup-test-env
```

### Manual Setup
```bash
# 1. Start services
docker-compose up -d postgres redis

# 2. Install dependencies
pip install -r requirements.txt
pip install pytest-cov pytest-xdist pytest-html

# 3. Run migrations
alembic upgrade head

# 4. Generate demo data (optional)
python tests/demo_data_generator.py --scenario comprehensive
```

### Environment Variables
Set these in your `.env` file or environment:
```bash
DATABASE_URL=postgresql://financial_planning:financial_planning@localhost:5432/financial_planning
REDIS_URL=redis://localhost:6379
SECRET_KEY=your-secret-key
ENVIRONMENT=testing
TESTING=true
```

## 📊 Test Data Generation

### Demo Data Generator
Generate realistic test data for comprehensive testing:

```bash
# Generate comprehensive dataset
python tests/demo_data_generator.py --scenario comprehensive --users 20

# Generate retirement-focused data
python tests/demo_data_generator.py --scenario retirement

# Generate data for load testing
python tests/demo_data_generator.py --scenario testing --users 100
```

**Generated Data**:
- User personas with realistic financial profiles
- Market scenarios (bull, bear, normal, etc.)
- Goal templates for different life stages
- Investment portfolios with diversification
- Simulation parameters for various scenarios

### Test Factories
Use factories for creating test data in tests:

```python
from tests.factories import UserFactory, FinancialProfileFactory, GoalFactory

# Create a user with profile and goals
scenario = await create_complete_user_scenario(session, risk_tolerance='moderate')

# Create specific test users
conservative_user = await ConservativeProfileFactory.create(session=session)
aggressive_user = await AggressiveProfileFactory.create(session=session)
```

## 🔄 Continuous Integration

### GitHub Actions Workflow
The project includes a comprehensive CI/CD workflow (`.github/workflows/test-suite.yml`) that runs:

1. **Health Check** - System verification
2. **Unit Tests** - Fast isolated tests with coverage
3. **Integration Tests** - Service integration verification
4. **Demo Tests** - End-to-end functionality
5. **E2E Tests** - Browser-based testing
6. **Security Tests** - Vulnerability scanning
7. **Performance Tests** - Load and benchmark testing
8. **API Documentation** - OpenAPI validation

### Local CI Simulation
```bash
# Run the complete CI pipeline locally
make test-ci
```

## 🐛 Troubleshooting

### Common Issues

**Database Connection Errors**:
```bash
# Reset test environment
make clean-test-env
make setup-test-env
```

**Port Conflicts**:
```bash
# Stop all containers
docker-compose down

# Check what's using the ports
lsof -i :5432  # PostgreSQL
lsof -i :6379  # Redis
lsof -i :8000  # API
```

**Test Failures**:
```bash
# Run with verbose output
pytest tests/unit/ -v --tb=long

# Run specific test
pytest tests/unit/test_simulation_service.py::test_monte_carlo_simulation -v

# Run with debugging
pytest tests/unit/ --pdb
```

**Performance Issues**:
```bash
# Run quick subset
make test-quick

# Run with reduced iterations
pytest tests/ -k "not slow"
```

### Getting Help
```bash
# Show available make commands
make help

# Show troubleshooting guide
make troubleshoot

# Check system requirements
python health_check.py --detailed
```

## 📈 Test Coverage

Generate comprehensive coverage reports:

```bash
# HTML coverage report
pytest tests/unit/ tests/integration/ --cov=app --cov-report=html
open htmlcov/index.html

# XML coverage for CI
pytest tests/unit/ tests/integration/ --cov=app --cov-report=xml

# Terminal coverage summary
pytest tests/unit/ tests/integration/ --cov=app --cov-report=term-missing
```

## 🎯 Best Practices

### Writing Tests
- **Test Behavior, Not Implementation**: Focus on what the system should do
- **Use Descriptive Names**: `test_monte_carlo_simulation_with_high_volatility_returns_wider_confidence_intervals`
- **Arrange-Act-Assert**: Structure tests clearly
- **Independent Tests**: Each test should be able to run in isolation
- **Mock External Dependencies**: Use mocks for third-party services

### Test Data
- **Use Factories**: Create consistent, realistic test data
- **Avoid Hard-Coded Values**: Use constants or generators
- **Clean Up**: Ensure tests don't leave behind data
- **Realistic Scenarios**: Test with data that resembles production

### Performance
- **Fast Unit Tests**: Keep unit tests under 1 second each
- **Parallel Execution**: Use pytest-xdist for speed
- **Selective Testing**: Use markers to run subsets
- **Resource Management**: Clean up resources properly

## 📚 Additional Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Factory Boy Documentation](https://factoryboy.readthedocs.io/)
- [Playwright Documentation](https://playwright.dev/python/)
- [Locust Documentation](https://locust.io/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)

## 🤝 Contributing

When adding new features, please:

1. **Add Unit Tests**: Cover new functionality with unit tests
2. **Update Integration Tests**: If you add new endpoints or services
3. **Update Demo Tests**: If new features should be demonstrated
4. **Add to Test Documentation**: Update this README if needed
5. **Run Full Test Suite**: Ensure all tests pass before submitting

```bash
# Before submitting a PR
make test-all
make lint
make format
```