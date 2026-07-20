# 🚀 Financial Planning API Test Suite

A comprehensive, colorful, and informative API testing suite designed for demonstrating the Financial Planning System's capabilities.

## ✨ Features

- **Visual Output**: Colorful console output with Rich library
- **HTML Reports**: Beautiful, interactive HTML reports
- **Performance Testing**: Response time measurements and statistics
- **Load Testing**: Concurrent request testing (100+ requests)
- **Error Handling**: Comprehensive error scenario testing
- **Schema Validation**: Response schema validation with Pydantic
- **Authentication Flow**: Complete auth testing including JWT tokens
- **Realistic Data**: Generates realistic financial planning scenarios
- **Summary Dashboard**: Executive summary with key metrics

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Install test dependencies
pip install -r requirements_test.txt

# Or use the launcher script
./run_api_tests.sh --install-deps
```

### 2. Run Basic Tests

```bash
# Simple test run
python3 test_api_demo.py

# Or use the launcher script
./run_api_tests.sh
```

### 3. Run with Load Testing

```bash
# Include load testing (100 concurrent requests)
python3 test_api_demo.py --load-test

# Or use the launcher script
./run_api_tests.sh --load-test
```

## 📋 Test Categories

### 🏥 Health Endpoints
- `/` - Root endpoint
- `/health` - Comprehensive health check
- `/status` - Service status
- `/docs` - API documentation

### 🔐 Authentication Flow
- User registration
- Login with credentials
- Token validation
- Current user information
- Token refresh

### 💰 Financial Endpoints
- Financial profiles management
- Goals CRUD operations
- Investment tracking
- Market data access
- User management

### 🎯 Simulation Endpoints
- Monte Carlo simulations
- Scenario analysis
- Financial planning calculations
- Real-time simulation status

### 🚨 Error Handling
- Invalid endpoints (404)
- Invalid data (422)
- Unauthorized access (401)
- Server errors (500)

## 📊 Output Examples

### Console Output
```
🚀 Financial Planning API Test Suite

🏥 Testing Health Endpoints
  ✅ GET / - 0.045s
  ✅ GET /health - 0.123s
  ✅ GET /status - 0.034s

🔐 Testing Authentication Flow
  ✅ POST /api/v1/auth/register - 0.234s
  ✅ POST /api/v1/auth/login - 0.189s
  ✅ GET /api/v1/auth/me - 0.067s

📊 TEST SUMMARY DASHBOARD
================================
Total Tests: 25
Successful: 23 (92.0%)
Failed: 2 (8.0%)
Average Response Time: 0.156s
```

### HTML Report
The suite generates a beautiful HTML report with:
- Interactive performance charts
- Detailed test results table
- Color-coded status indicators
- Executive summary dashboard
- Responsive design for mobile/desktop

## 🛠 Command Line Options

```bash
python3 test_api_demo.py [OPTIONS]

OPTIONS:
  --base-url URL    Base URL for API (default: http://localhost:8000)
  --load-test       Include load testing (100 requests)
  --verbose         Enable verbose output
  --help           Show help message

EXAMPLES:
  python3 test_api_demo.py
  python3 test_api_demo.py --base-url http://localhost:3000
  python3 test_api_demo.py --load-test --verbose
```

## 🔧 Launcher Script Options

```bash
./run_api_tests.sh [OPTIONS]

OPTIONS:
  --base-url URL     Set API base URL
  --load-test        Include load testing
  --verbose          Enable verbose output
  --install-deps     Install dependencies
  --help            Show help

FEATURES:
  - Automatic dependency checking
  - Server availability verification
  - Cross-platform browser opening for reports
  - Colored output with status indicators
```

## 📈 Performance Metrics

The test suite tracks and reports:

- **Response Times**: Min, max, average for each endpoint
- **Success Rates**: Percentage of successful requests
- **Throughput**: Requests per second during load testing
- **Error Analysis**: Categorized error types and frequencies
- **Percentile Analysis**: P50, P90, P95 response times

## 🧪 Test Data Generation

The suite includes realistic test data generation:

```python
# Generate realistic financial profiles
generator = TestDataGenerator()
profile = generator.generate_financial_profile(age=35)

# Generate edge cases
edge_cases = generator.generate_edge_case_scenarios()

# Complete test dataset
dataset = generator.get_test_dataset(count=10)
```

## 🎯 Demo Scenarios

### Realistic Financial Profiles
- Young professional (age 22-30)
- Mid-career (age 30-50)
- Pre-retirement (age 50-65)
- High earner scenarios
- High debt scenarios
- Conservative vs aggressive investors

### Load Testing Scenarios
- 100 concurrent health checks
- Authentication under load
- Simulation endpoint stress testing
- Error rate monitoring

## 📁 Generated Files

After running tests, you'll find:

- `api_test_report.html` - Interactive HTML report
- `demo_test_data.json` - Generated test data (if using data generator)
- Console output with colored results
- Performance statistics

## 🔍 Troubleshooting

### Common Issues

1. **Import Errors**
   ```bash
   pip install -r requirements_test.txt
   ```

2. **Server Not Running**
   - Ensure API server is running at specified URL
   - Check server logs for errors
   - Verify port and host configuration

3. **Permission Denied (Linux/Mac)**
   ```bash
   chmod +x run_api_tests.sh
   ```

4. **Rich Library Issues**
   - Fallback text mode available if Rich unavailable
   - Install with: `pip install rich`

### Debug Mode

Enable verbose output for debugging:
```bash
python3 test_api_demo.py --verbose
```

## 🎨 Customization

### Adding New Test Cases

```python
async def test_custom_endpoint(self):
    """Add custom test endpoint"""
    result = await self.make_request(
        "GET", "/api/v1/custom-endpoint",
        expected_status=200
    )
    return result
```

### Custom Test Data

```python
# Modify TestDataGenerator class
def generate_custom_scenario(self):
    return {
        "custom_field": "custom_value",
        # ... more fields
    }
```

## 📖 API Documentation

For complete API documentation, visit:
- `/docs` - Swagger UI
- `/redoc` - ReDoc documentation
- OpenAPI specification available at `/api/v1/openapi.json`

## 🤝 Contributing

To add new tests or improve the suite:

1. Add test methods to `APITestSuite` class
2. Update test data generators as needed
3. Enhance HTML report templates
4. Add new command line options

## 📄 License

This test suite is part of the Financial Planning System project.