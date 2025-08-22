# Demo Validation Test Suite

This directory contains comprehensive automated tests to ensure all demos work correctly and maintain reliability over time.

## Overview

The demo validation test suite provides:

- **Comprehensive Testing**: Tests each demo can start successfully
- **Data Validation**: Validates demo data is present and accessible
- **API Testing**: Checks API endpoints respond correctly
- **Frontend Validation**: Verifies frontend pages load properly
- **Container Testing**: Tests Docker containers start correctly
- **CLI Interaction**: Validates CLI demo interaction
- **Performance Benchmarks**: Checks performance benchmarks run
- **Security Validation**: Ensures security demo completes
- **ML Simulation Testing**: Validates ML simulations execute
- **Mobile App Testing**: Tests mobile app initialization

## Test Structure

### Core Test Files

- `test_all_demos.py` - Main comprehensive test suite
- `conftest.py` - Shared test fixtures and configuration
- `__init__.py` - Package initialization

### Test Categories

#### 1. Basic Demo Startup (`TestBasicDemoStartup`)
- Directory structure validation
- Script executable permissions
- Required file existence checks
- Basic configuration validation

#### 2. API Demo Testing (`TestAPIDemo`) 
- Minimal demo startup testing
- Full-featured demo validation
- Demo data endpoint testing
- User registration and login flows

#### 3. ML Simulation Testing (`TestMLSimulationDemo`)
- ML demo startup validation
- Monte Carlo engine testing
- Output file generation verification
- Performance benchmarking

#### 4. Security Demo Testing (`TestSecurityDemo`)
- Simple security demo validation
- Full security demo testing
- Security configuration checks

#### 5. Performance Testing (`TestPerformanceDemo`)
- Performance demo startup
- Benchmark execution
- Resource usage monitoring

#### 6. CLI Demo Testing (`TestCLIDemo`)
- CLI startup and response testing
- Interactive mode validation
- Help system verification

#### 7. Docker Integration (`TestDockerDemo`)
- Docker compose validation
- Container startup testing
- Service health checks

#### 8. Frontend Testing (`TestFrontendDemo`)
- Frontend build validation
- Page loading tests (with Selenium)
- Component rendering verification

#### 9. Mobile Demo Testing (`TestMobileDemo`)
- Mobile app structure validation
- Demo app configuration checks
- Package dependency verification

#### 10. Data Pipeline Testing (`TestDataPipelineDemo`)
- Simple pipeline execution
- Full pipeline validation
- Data processing verification

## Running the Tests

### Prerequisites

```bash
# Install test dependencies
pip install -r requirements_test.txt

# Or install individual dependencies
pip install pytest requests psutil docker selenium webdriver-manager
```

### Basic Usage

```bash
# Run all demo validation tests
pytest backend/tests/demo-validation/ -v

# Run specific test categories
pytest backend/tests/demo-validation/test_all_demos.py::TestBasicDemoStartup -v
pytest backend/tests/demo-validation/test_all_demos.py::TestAPIDemo -v
pytest backend/tests/demo-validation/test_all_demos.py::TestMLSimulationDemo -v

# Run with specific markers
pytest backend/tests/demo-validation/ -m "demo and smoke" -v
pytest backend/tests/demo-validation/ -m "integration" -v
pytest backend/tests/demo-validation/ -m "not slow" -v
```

### Advanced Options

```bash
# Run with detailed output and timing
pytest backend/tests/demo-validation/ -v --tb=short --durations=10

# Run tests in parallel (requires pytest-xdist)
pytest backend/tests/demo-validation/ -n auto

# Generate coverage report
pytest backend/tests/demo-validation/ --cov=backend --cov-report=html

# Run only failed tests from last run
pytest backend/tests/demo-validation/ --lf

# Run tests with specific timeout
pytest backend/tests/demo-validation/ --timeout=300
```

## Test Configuration

### Environment Variables

The tests respect these environment variables:

```bash
# Test environment configuration
export TESTING=true
export ENVIRONMENT=testing
export DATABASE_URL=postgresql://postgres:@localhost/test_db
export REDIS_URL=redis://localhost:6379/1

# Demo-specific configuration
export DEMO_ENV=test
export AUTO_OPEN_BROWSER=false
export SKIP_CHECKS=false

# CI/CD configuration
export CI=true
export HEADLESS=true
```

### Pytest Markers

Tests are organized using pytest markers:

- `@pytest.mark.demo` - Demo-related tests
- `@pytest.mark.smoke` - Quick smoke tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.slow` - Long-running tests
- `@pytest.mark.selenium` - Tests requiring web browser
- `@pytest.mark.external` - Tests requiring external services

### Test Fixtures

#### `demo_runner` (session-scoped)
Provides a `DemoTestRunner` instance with cleanup capabilities:

```python
def test_example(demo_runner):
    # Access helper methods
    assert demo_runner.wait_for_port(8000)
    assert demo_runner.check_process_running("python")
    
    # Cleanup is handled automatically
    demo_runner.cleanup_tasks.append(lambda: cleanup_function())
```

## Continuous Integration

### GitHub Actions Integration

The tests are integrated with GitHub Actions workflows:

- **Push/PR Triggers**: Run smoke tests on every push/PR
- **Scheduled Runs**: Full validation suite runs daily
- **Manual Triggers**: Can be triggered manually with custom parameters

### Pre-commit Hooks

Demo validation is integrated with pre-commit hooks:

```bash
# Install pre-commit
pip install pre-commit
pre-commit install

# Run manually
pre-commit run demo-smoke-tests --all-files
```

## Smoke Tests

The quick validation script `demo-smoke-tests.sh` provides fast health checks:

```bash
# Run quick validation
./demo-smoke-tests.sh --quick

# Run with verbose output
./demo-smoke-tests.sh --verbose

# Run full validation
./demo-smoke-tests.sh
```

## Daily Health Checks

Automated daily health monitoring is available:

```bash
# Setup daily health checks
backend/scripts/setup_cron_health_checks.sh setup

# Run manual health check
python3 backend/scripts/daily_demo_health_check.py

# Check status
backend/scripts/setup_cron_health_checks.sh status
```

## Test Data Management

### Demo Data Generation

Tests use the `demo_data_generator.py` for creating test data:

```python
from tests.demo_data_generator import DemoDataGenerator

generator = DemoDataGenerator()
user_data = generator.create_user_data()
financial_data = generator.create_financial_profile()
```

### Database Management

Tests handle database setup/teardown automatically:

- Test databases are created in isolation
- Data is cleaned up after each test
- Migrations are run automatically
- Demo data is seeded as needed

## Performance Monitoring

### Benchmarking

Performance tests track key metrics:

- **Startup Time**: How quickly demos start
- **API Response Time**: Endpoint response latencies  
- **Memory Usage**: Peak memory consumption
- **CPU Usage**: Processing requirements
- **Simulation Speed**: ML processing performance

### Reporting

Test results are reported in multiple formats:

- **Console Output**: Real-time test progress
- **JUnit XML**: For CI/CD integration
- **HTML Reports**: Detailed test results
- **JSON Reports**: Machine-readable results
- **Coverage Reports**: Code coverage analysis

## Troubleshooting

### Common Issues

#### Port Conflicts
```bash
# Check for port usage
netstat -an | grep :8000
lsof -i :8000

# Kill processes using ports
kill $(lsof -t -i:8000)
```

#### Permission Issues
```bash
# Fix script permissions
chmod +x demo-smoke-tests.sh
chmod +x backend/start_demo.sh
```

#### Missing Dependencies
```bash
# Install missing Python packages
pip install -r backend/requirements.txt
pip install -r backend/requirements_test.txt

# Install system dependencies (Ubuntu/Debian)
sudo apt-get install postgresql-client redis-tools

# Install browser for Selenium tests
sudo apt-get install chromium-browser
```

#### Docker Issues
```bash
# Check Docker status
docker info
docker-compose config

# Reset Docker environment
docker-compose down -v
docker system prune -f
```

### Debugging Tests

#### Verbose Output
```bash
# Run with maximum verbosity
pytest backend/tests/demo-validation/ -vvv --tb=long

# Show local variables in tracebacks
pytest backend/tests/demo-validation/ --tb=short --showlocals
```

#### Debugging Specific Tests
```python
import pytest

def test_example(demo_runner):
    # Add debugging breakpoint
    pytest.set_trace()
    
    # Your test code here
    result = demo_runner.check_demo_startup("test", "test.py")
    assert result["status"] == "success"
```

#### Log Analysis
```bash
# View test logs
tail -f /tmp/demo-smoke-tests.log

# View health check logs  
ls -la /tmp/demo-health-logs/

# View application logs
docker-compose logs -f api
```

## Contributing

### Adding New Tests

1. Create test methods in the appropriate test class
2. Use descriptive test names: `test_feature_specific_behavior`
3. Add appropriate pytest markers
4. Include docstrings explaining test purpose
5. Handle cleanup in fixtures or teardown

### Test Guidelines

- **Fast by Default**: Keep tests quick unless marked `@pytest.mark.slow`
- **Isolated**: Each test should be independent
- **Descriptive**: Use clear assertion messages
- **Robust**: Handle edge cases and failures gracefully
- **Documented**: Include docstrings and comments

### Example Test Addition

```python
@pytest.mark.demo
@pytest.mark.integration
class TestNewFeature:
    """Test new demo feature functionality."""
    
    def test_new_feature_startup(self, demo_runner):
        """Test that new feature demo can start successfully."""
        # Arrange
        demo_script = "new_feature_demo.py"
        
        # Act
        result = demo_runner.check_demo_startup("new_feature", demo_script)
        
        # Assert
        assert result["status"] == "success", f"Demo startup failed: {result}"
        assert result["api_ready"], "API not ready after startup"
        
    def test_new_feature_api_endpoints(self, demo_runner):
        """Test new feature API endpoints respond correctly."""
        # Implementation here...
        pass
```

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Selenium Documentation](https://selenium-python.readthedocs.io/)
- [Docker Testing Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [CI/CD Testing Strategies](https://docs.github.com/en/actions)

## Support

For issues with the test suite:

1. Check the troubleshooting section above
2. Review logs in `/tmp/demo-health-logs/`
3. Run individual tests with verbose output
4. Check GitHub Actions workflow results
5. Create an issue with detailed error information