# Financial Planning System - Load Testing Suite

Comprehensive load testing suite for performance validation, benchmarking, and scalability testing of the financial planning system.

## Features

### 1. Test Scenarios
- **User Onboarding**: New user registration and profile setup
- **Monte Carlo Simulations**: Stress testing complex calculations
- **Portfolio Management**: Concurrent portfolio operations
- **Market Data Streaming**: WebSocket connection stress testing
- **Banking Sync**: Transaction synchronization load testing
- **Report Generation**: PDF generation performance testing
- **Goal Management**: Financial goal CRUD operations

### 2. Performance Benchmarks
- **Response Time SLAs**:
  - API endpoints: P95 < 500ms, P99 < 1000ms
  - Monte Carlo simulations: P95 < 30 seconds
  - PDF generation: P95 < 60 seconds
  - Market data: P95 < 300ms
  - WebSocket latency: P95 < 100ms

- **Throughput Requirements**:
  - Minimum 100 requests/second
  - Support 500+ concurrent users
  - 1000+ WebSocket connections

- **Error Rate Targets**:
  - < 1% error rate
  - < 0.5% timeout rate

### 3. Test Data Generation
- Realistic user profiles (young professionals, families, retirees, HNW)
- Financial goals and investment portfolios
- Transaction histories (6-12 months)
- Market data simulation
- 1000+ test accounts with credentials

### 4. Monitoring Integration
- **Prometheus** metrics collection
- **Grafana** dashboard visualization
- **Real-time** performance tracking
- **Resource usage** monitoring (CPU, memory, I/O)
- **Database** performance metrics
- **Alert** notifications (Slack, PagerDuty)

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Generate test data
python data/test_data_generator.py

# Optional: Setup monitoring stack
docker-compose -f ../../infrastructure/monitoring/docker-compose.monitoring.yml up -d
```

## Usage

### Quick Start

```bash
# Run basic load test (100 users, 5 minutes)
python orchestrator.py --users 100 --duration 300

# Run stress test
python orchestrator.py --profile stress --users 500 --duration 600

# Run with monitoring
python orchestrator.py --prometheus localhost:9091 --grafana localhost:3000
```

### Test Profiles

#### Smoke Test
Quick validation test with minimal load:
```bash
python orchestrator.py --profile smoke --users 5 --duration 120
```

#### Load Test
Standard load test with gradual ramp-up:
```bash
python orchestrator.py --profile load --users 200 --duration 900
```

#### Stress Test
Push system to its limits:
```bash
python orchestrator.py --profile stress --users 1000 --duration 1200
```

#### Spike Test
Test response to sudden traffic spikes:
```bash
python orchestrator.py --profile spike --users 500 --duration 600
```

#### Soak Test
Extended duration test for memory leaks:
```bash
python orchestrator.py --profile soak --users 200 --duration 14400
```

### Advanced Options

```bash
# Generate new test data
python orchestrator.py --generate-data --test-accounts 5000

# Enable Slack notifications
python orchestrator.py --slack-webhook https://hooks.slack.com/...

# Custom target host
python orchestrator.py --host https://staging.example.com

# Distributed testing
locust -f scenarios/comprehensive_scenarios.py --master --expect-workers 4
locust -f scenarios/comprehensive_scenarios.py --worker --master-host localhost
```

## Test Scenarios Details

### 1. User Onboarding Flow
```python
- User registration
- Financial profile completion
- Goal setting (2-3 goals)
- Bank account connection
- Initial portfolio setup
```

### 2. Monte Carlo Simulation
```python
- Basic simulation (1000 iterations)
- Complex simulation (5000 iterations, multiple scenarios)
- Stress test (10000 iterations, maximum parameters)
```

### 3. Portfolio Management
```python
- View portfolio summary (30% weight)
- View detailed holdings (20% weight)
- Calculate performance metrics (20% weight)
- Rebalance portfolio (20% weight)
- Risk analysis (10% weight)
```

### 4. Market Data Streaming
```python
- Fetch current prices
- Historical data retrieval
- WebSocket connection
- Real-time updates subscription
```

### 5. Banking Integration
```python
- Account synchronization
- Transaction fetching
- Auto-categorization
- Spending analysis
- Anomaly detection
```

## Performance Metrics

### Key Metrics Tracked
- **Response Times**: Min, Max, Mean, Median, P50, P75, P90, P95, P99
- **Throughput**: Requests per second, Peak RPS
- **Errors**: Error rate, Error types breakdown
- **Resources**: CPU usage, Memory usage, Database connections
- **Business Metrics**: Active users, WebSocket connections, Cache hit rate

### SLA Validation
The suite automatically validates against defined SLAs:
```python
- API Response P95 < 500ms
- API Response P99 < 1000ms
- Monte Carlo P95 < 30 seconds
- PDF Generation P95 < 60 seconds
- Error Rate < 1%
- Minimum RPS > 100
```

## Reports

### HTML Report
Comprehensive HTML report with:
- Executive summary
- Response time distribution
- SLA compliance status
- Resource usage graphs
- Performance recommendations
- Slowest endpoints analysis

### JSON Report
Machine-readable report for CI/CD integration:
```json
{
  "test_id": "20240121_143022",
  "sla_passed": true,
  "total_requests": 45234,
  "error_rate": 0.008,
  "p95_response_time": 487,
  "recommendations": [...]
}
```

### Grafana Dashboard
Real-time dashboard showing:
- Requests per second
- Response time percentiles
- Error rate trends
- System resource usage
- Database performance
- Active user count

## CI/CD Integration

### GitHub Actions
```yaml
- name: Run Load Test
  run: |
    python tests/load-testing/orchestrator.py \
      --profile load \
      --users 100 \
      --duration 300 \
      --json-report
    
- name: Check Performance
  run: |
    python -c "
    import json
    with open('reports/*/report_*.json') as f:
        report = json.load(f)
    if not report['sla_passed']:
        exit(1)
    "
```

### Jenkins Pipeline
```groovy
stage('Load Testing') {
    steps {
        sh '''
            python tests/load-testing/orchestrator.py \
              --profile ${LOAD_PROFILE} \
              --users ${USER_COUNT} \
              --duration ${TEST_DURATION}
        '''
    }
    post {
        always {
            publishHTML([
                reportDir: 'reports',
                reportFiles: '*/report_*.html',
                reportName: 'Load Test Report'
            ])
        }
    }
}
```

## Performance Regression Detection

The suite includes automatic regression detection:
```python
# Compares against baseline metrics
- Response time regression > 10%
- Throughput regression > 10%
- Error rate increase > 50%
- Resource usage increase > 20%
```

## Troubleshooting

### Common Issues

1. **High Error Rate**
   - Check application logs
   - Verify database connection pool
   - Monitor rate limiting

2. **Slow Response Times**
   - Profile slow queries
   - Check cache configuration
   - Monitor CPU/memory usage

3. **Connection Errors**
   - Verify network configuration
   - Check firewall rules
   - Monitor connection limits

### Debug Mode
```bash
# Enable debug logging
LOCUST_LOGLEVEL=DEBUG python orchestrator.py

# Save detailed logs
python orchestrator.py 2>&1 | tee load_test.log
```

## Best Practices

1. **Warm-up Period**: Allow 1-2 minutes for system warm-up
2. **Gradual Ramp-up**: Increase load gradually to identify breaking points
3. **Baseline Testing**: Establish performance baselines for comparison
4. **Regular Testing**: Run tests after each major deployment
5. **Monitor Everything**: Track all metrics during tests
6. **Document Results**: Keep historical records for trend analysis

## Contributing

To add new test scenarios:

1. Create scenario class in `scenarios/`
2. Define user behaviors with `@task` decorators
3. Set appropriate weights for task distribution
4. Update configuration in `config.py`
5. Document SLAs and benchmarks

## License

MIT License - See LICENSE file for details