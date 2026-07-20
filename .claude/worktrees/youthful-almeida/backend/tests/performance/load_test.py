"""
Comprehensive Load Testing Suite

Features:
- Locust-based load testing
- k6 script generation
- JMeter test plan creation
- Performance regression detection
- Automated performance reports
"""

import time
import json
import statistics
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass, field
import asyncio
import random

from locust import HttpUser, task, between, events
from locust.env import Environment
from locust.stats import stats_printer, stats_history
from locust.log import setup_logging
import gevent

# For k6 script generation
K6_SCRIPT_TEMPLATE = """
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('errors');
const apiLatency = new Trend('api_latency');

// Test configuration
export const options = {
  stages: [
    { duration: '2m', target: {ramp_users} },   // Ramp up
    { duration: '5m', target: {steady_users} },  // Steady state
    { duration: '2m', target: {peak_users} },    // Peak load
    { duration: '5m', target: {peak_users} },    // Sustain peak
    { duration: '2m', target: 0 },               // Ramp down
  ],
  thresholds: {
    'http_req_duration': ['p(95)<{p95_threshold}'],
    'http_req_duration': ['p(99)<{p99_threshold}'],
    'errors': ['rate<{error_threshold}'],
  },
};

const BASE_URL = '{base_url}';

// Test data
const users = JSON.parse(open('./test_users.json'));

export default function() {
  const user = users[Math.floor(Math.random() * users.length)];
  
  // Login
  const loginRes = http.post(`${BASE_URL}/auth/login`, JSON.stringify({
    email: user.email,
    password: user.password
  }), {
    headers: { 'Content-Type': 'application/json' }
  });
  
  check(loginRes, {
    'login successful': (r) => r.status === 200,
  });
  
  if (loginRes.status !== 200) {
    errorRate.add(1);
    return;
  }
  
  const token = loginRes.json('access_token');
  const headers = {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  };
  
  // Test scenarios
  {test_scenarios}
  
  sleep(1);
}
"""


@dataclass
class LoadTestConfig:
    """Load test configuration"""
    base_url: str = "http://localhost:8000"
    num_users: int = 100
    spawn_rate: int = 10
    test_duration: int = 300  # seconds
    
    # Performance thresholds
    p95_threshold_ms: int = 500
    p99_threshold_ms: int = 1000
    error_rate_threshold: float = 0.01
    
    # Test scenarios weights
    scenario_weights: Dict[str, int] = field(default_factory=lambda: {
        'portfolio_view': 30,
        'simulation_run': 20,
        'goal_management': 20,
        'market_data': 15,
        'investment_update': 10,
        'report_generation': 5
    })


@dataclass
class LoadTestResult:
    """Load test results"""
    start_time: datetime
    end_time: datetime
    total_requests: int
    successful_requests: int
    failed_requests: int
    
    # Response times (ms)
    min_response_time: float
    max_response_time: float
    mean_response_time: float
    median_response_time: float
    p95_response_time: float
    p99_response_time: float
    
    # Throughput
    requests_per_second: float
    bytes_per_second: float
    
    # Errors
    error_rate: float
    error_types: Dict[str, int]
    
    # Resource usage
    peak_cpu: float
    peak_memory: float
    peak_connections: int


class FinancialPlanningUser(HttpUser):
    """
    Simulated user for load testing the financial planning application
    """
    wait_time = between(1, 3)
    
    def on_start(self):
        """Login and setup user session"""
        # Login with test credentials
        response = self.client.post("/api/v1/auth/login", json={
            "email": f"test_user_{random.randint(1, 100)}@example.com",
            "password": "TestPassword123!"
        })
        
        if response.status_code == 200:
            self.token = response.json()["access_token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
            self.user_id = response.json()["user_id"]
        else:
            self.token = None
            self.headers = {}
            self.user_id = None
    
    @task(30)
    def view_portfolio(self):
        """View portfolio summary"""
        if self.token:
            with self.client.get(
                f"/api/v1/portfolio/{self.user_id}",
                headers=self.headers,
                catch_response=True
            ) as response:
                if response.status_code != 200:
                    response.failure(f"Got status code {response.status_code}")
    
    @task(20)
    def run_simulation(self):
        """Run Monte Carlo simulation"""
        if self.token:
            simulation_data = {
                "initial_investment": 10000,
                "monthly_contribution": 500,
                "years": 20,
                "risk_tolerance": "moderate",
                "num_simulations": 1000
            }
            
            with self.client.post(
                "/api/v1/simulations/monte-carlo",
                json=simulation_data,
                headers=self.headers,
                catch_response=True
            ) as response:
                if response.status_code != 200:
                    response.failure(f"Simulation failed: {response.status_code}")
                elif response.elapsed.total_seconds() > 5:
                    response.failure("Simulation took too long")
    
    @task(20)
    def manage_goals(self):
        """Create and update financial goals"""
        if self.token:
            # Create a goal
            goal_data = {
                "name": f"Goal_{random.randint(1, 1000)}",
                "target_amount": random.randint(5000, 50000),
                "target_date": "2030-01-01",
                "category": random.choice(["retirement", "education", "house", "vacation"]),
                "priority": random.choice(["high", "medium", "low"])
            }
            
            response = self.client.post(
                "/api/v1/goals",
                json=goal_data,
                headers=self.headers
            )
            
            if response.status_code == 201:
                goal_id = response.json()["id"]
                
                # Update the goal
                self.client.patch(
                    f"/api/v1/goals/{goal_id}",
                    json={"monthly_contribution": random.randint(100, 1000)},
                    headers=self.headers
                )
    
    @task(15)
    def fetch_market_data(self):
        """Fetch market data for multiple symbols"""
        symbols = random.sample(
            ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA", "META", "NVDA", "JPM"],
            k=random.randint(1, 5)
        )
        
        self.client.get(
            f"/api/v1/market-data?symbols={','.join(symbols)}",
            headers=self.headers if self.token else {}
        )
    
    @task(10)
    def update_investment(self):
        """Update investment allocations"""
        if self.token:
            allocation_data = {
                "stocks": random.randint(30, 70),
                "bonds": random.randint(10, 40),
                "real_estate": random.randint(5, 20),
                "commodities": random.randint(0, 10),
                "cash": random.randint(5, 15)
            }
            
            # Normalize to 100%
            total = sum(allocation_data.values())
            allocation_data = {k: v/total*100 for k, v in allocation_data.items()}
            
            self.client.put(
                f"/api/v1/investments/allocation",
                json=allocation_data,
                headers=self.headers
            )
    
    @task(5)
    def generate_report(self):
        """Generate PDF report"""
        if self.token:
            with self.client.post(
                "/api/v1/reports/generate",
                json={"report_type": "comprehensive", "format": "pdf"},
                headers=self.headers,
                catch_response=True
            ) as response:
                if response.status_code != 200:
                    response.failure(f"Report generation failed: {response.status_code}")
                elif response.elapsed.total_seconds() > 10:
                    response.failure("Report generation took too long")
    
    @task(2)
    def complex_query(self):
        """Execute complex analytical query"""
        if self.token:
            # GraphQL query for complex data fetching
            query = """
            query GetPortfolioAnalysis($userId: ID!) {
                portfolio(userId: $userId) {
                    totalValue
                    investments {
                        symbol
                        currentValue
                        performance {
                            daily
                            weekly
                            monthly
                            yearly
                        }
                    }
                    riskMetrics {
                        volatility
                        sharpeRatio
                        beta
                    }
                }
            }
            """
            
            self.client.post(
                "/graphql",
                json={"query": query, "variables": {"userId": self.user_id}},
                headers=self.headers
            )


class LoadTestRunner:
    """
    Orchestrate and run load tests
    """
    
    def __init__(self, config: LoadTestConfig):
        """
        Initialize load test runner
        
        Args:
            config: Load test configuration
        """
        self.config = config
        self.results: List[LoadTestResult] = []
    
    def run_locust_test(self) -> LoadTestResult:
        """
        Run Locust load test
        
        Returns:
            Load test results
        """
        # Setup Locust environment
        env = Environment(user_classes=[FinancialPlanningUser])
        env.create_local_runner()
        
        # Setup logging
        setup_logging("INFO")
        
        # Start test
        env.runner.start(self.config.num_users, spawn_rate=self.config.spawn_rate)
        
        # Run for specified duration
        start_time = datetime.now()
        gevent.spawn_later(self.config.test_duration, lambda: env.runner.quit())
        
        # Start stats collection
        gevent.spawn(stats_printer(env.stats))
        gevent.spawn(stats_history, env.runner)
        
        # Wait for test to complete
        env.runner.greenlet.join()
        
        end_time = datetime.now()
        
        # Collect results
        stats = env.stats
        
        # Calculate response time percentiles
        response_times = []
        for stat in stats.entries.values():
            if stat.response_times:
                response_times.extend(stat.response_times)
        
        if response_times:
            response_times.sort()
            p95_index = int(len(response_times) * 0.95)
            p99_index = int(len(response_times) * 0.99)
            
            result = LoadTestResult(
                start_time=start_time,
                end_time=end_time,
                total_requests=stats.total.num_requests,
                successful_requests=stats.total.num_requests - stats.total.num_failures,
                failed_requests=stats.total.num_failures,
                min_response_time=stats.total.min_response_time,
                max_response_time=stats.total.max_response_time,
                mean_response_time=stats.total.avg_response_time,
                median_response_time=stats.total.median_response_time,
                p95_response_time=response_times[p95_index] if p95_index < len(response_times) else 0,
                p99_response_time=response_times[p99_index] if p99_index < len(response_times) else 0,
                requests_per_second=stats.total.current_rps,
                bytes_per_second=stats.total.total_content_length / self.config.test_duration,
                error_rate=stats.total.fail_ratio,
                error_types=self._categorize_errors(stats),
                peak_cpu=0,  # Would be collected from monitoring
                peak_memory=0,  # Would be collected from monitoring
                peak_connections=0  # Would be collected from monitoring
            )
        else:
            result = LoadTestResult(
                start_time=start_time,
                end_time=end_time,
                total_requests=0,
                successful_requests=0,
                failed_requests=0,
                min_response_time=0,
                max_response_time=0,
                mean_response_time=0,
                median_response_time=0,
                p95_response_time=0,
                p99_response_time=0,
                requests_per_second=0,
                bytes_per_second=0,
                error_rate=0,
                error_types={},
                peak_cpu=0,
                peak_memory=0,
                peak_connections=0
            )
        
        self.results.append(result)
        return result
    
    def _categorize_errors(self, stats) -> Dict[str, int]:
        """Categorize errors by type"""
        error_types = {}
        
        for stat in stats.entries.values():
            if stat.num_failures > 0:
                # Categorize by status code or error type
                error_type = f"HTTP_{stat.name}"
                error_types[error_type] = stat.num_failures
        
        return error_types
    
    def generate_k6_script(self, output_file: str = "load_test.js"):
        """
        Generate k6 load test script
        
        Args:
            output_file: Output file path
        """
        # Generate test scenarios
        scenarios = []
        
        if 'portfolio_view' in self.config.scenario_weights:
            scenarios.append("""
  // Portfolio view scenario
  const portfolioRes = http.get(`${BASE_URL}/api/v1/portfolio/${user.id}`, { headers });
  check(portfolioRes, { 'portfolio loaded': (r) => r.status === 200 });
  apiLatency.add(portfolioRes.timings.duration);
            """)
        
        if 'simulation_run' in self.config.scenario_weights:
            scenarios.append("""
  // Simulation scenario
  const simRes = http.post(`${BASE_URL}/api/v1/simulations/monte-carlo`,
    JSON.stringify({
      initial_investment: 10000,
      monthly_contribution: 500,
      years: 20,
      num_simulations: 1000
    }), { headers });
  check(simRes, { 'simulation completed': (r) => r.status === 200 });
  apiLatency.add(simRes.timings.duration);
            """)
        
        # Generate script
        script = K6_SCRIPT_TEMPLATE.format(
            base_url=self.config.base_url,
            ramp_users=self.config.num_users // 2,
            steady_users=self.config.num_users,
            peak_users=self.config.num_users * 2,
            p95_threshold=self.config.p95_threshold_ms,
            p99_threshold=self.config.p99_threshold_ms,
            error_threshold=self.config.error_rate_threshold,
            test_scenarios='\n'.join(scenarios)
        )
        
        with open(output_file, 'w') as f:
            f.write(script)
        
        print(f"k6 script generated: {output_file}")
        print(f"Run with: k6 run {output_file}")
    
    def generate_jmeter_plan(self, output_file: str = "load_test.jmx"):
        """
        Generate JMeter test plan
        
        Args:
            output_file: Output file path
        """
        # JMeter test plan XML structure
        jmeter_plan = f"""<?xml version="1.0" encoding="UTF-8"?>
<jmeterTestPlan version="1.2" properties="5.0" jmeter="5.4.1">
  <hashTree>
    <TestPlan guiclass="TestPlanGui" testclass="TestPlan" testname="Financial Planning Load Test">
      <elementProp name="TestPlan.user_defined_variables" elementType="Arguments">
        <collectionProp name="Arguments.arguments">
          <elementProp name="BASE_URL" elementType="Argument">
            <stringProp name="Argument.name">BASE_URL</stringProp>
            <stringProp name="Argument.value">{self.config.base_url}</stringProp>
          </elementProp>
        </collectionProp>
      </elementProp>
    </TestPlan>
    <hashTree>
      <ThreadGroup guiclass="ThreadGroupGui" testclass="ThreadGroup" testname="User Load">
        <intProp name="ThreadGroup.num_threads">{self.config.num_users}</intProp>
        <intProp name="ThreadGroup.ramp_time">{self.config.num_users // self.config.spawn_rate}</intProp>
        <longProp name="ThreadGroup.duration">{self.config.test_duration}</longProp>
      </ThreadGroup>
      <hashTree>
        <!-- Add HTTP samplers for each scenario -->
        <HTTPSamplerProxy guiclass="HttpTestSampleGui" testclass="HTTPSamplerProxy" testname="Login">
          <elementProp name="HTTPsampler.Arguments" elementType="Arguments">
            <collectionProp name="Arguments.arguments">
              <elementProp name="email" elementType="HTTPArgument">
                <stringProp name="Argument.value">test@example.com</stringProp>
              </elementProp>
            </collectionProp>
          </elementProp>
          <stringProp name="HTTPSampler.path">/api/v1/auth/login</stringProp>
          <stringProp name="HTTPSampler.method">POST</stringProp>
        </HTTPSamplerProxy>
      </hashTree>
    </hashTree>
  </hashTree>
</jmeterTestPlan>
        """
        
        with open(output_file, 'w') as f:
            f.write(jmeter_plan)
        
        print(f"JMeter test plan generated: {output_file}")
        print(f"Run with: jmeter -n -t {output_file} -l results.jtl")
    
    def check_performance_regression(
        self,
        current_result: LoadTestResult,
        baseline_result: LoadTestResult,
        threshold_percent: float = 10.0
    ) -> Dict[str, Any]:
        """
        Check for performance regression
        
        Args:
            current_result: Current test results
            baseline_result: Baseline results to compare against
            threshold_percent: Regression threshold percentage
            
        Returns:
            Regression analysis results
        """
        regressions = []
        
        # Check response time regression
        metrics_to_check = [
            ('mean_response_time', 'Mean Response Time'),
            ('p95_response_time', 'P95 Response Time'),
            ('p99_response_time', 'P99 Response Time'),
            ('error_rate', 'Error Rate')
        ]
        
        for metric_name, display_name in metrics_to_check:
            current_value = getattr(current_result, metric_name)
            baseline_value = getattr(baseline_result, metric_name)
            
            if baseline_value > 0:
                change_percent = ((current_value - baseline_value) / baseline_value) * 100
                
                if change_percent > threshold_percent:
                    regressions.append({
                        'metric': display_name,
                        'baseline': baseline_value,
                        'current': current_value,
                        'change_percent': change_percent,
                        'regression': True
                    })
        
        # Check throughput regression
        if baseline_result.requests_per_second > 0:
            throughput_change = (
                (current_result.requests_per_second - baseline_result.requests_per_second) /
                baseline_result.requests_per_second
            ) * 100
            
            if throughput_change < -threshold_percent:
                regressions.append({
                    'metric': 'Throughput',
                    'baseline': baseline_result.requests_per_second,
                    'current': current_result.requests_per_second,
                    'change_percent': throughput_change,
                    'regression': True
                })
        
        return {
            'has_regression': len(regressions) > 0,
            'regressions': regressions,
            'summary': f"Found {len(regressions)} performance regressions"
        }
    
    def generate_report(self, result: LoadTestResult, output_file: str = "load_test_report.html"):
        """
        Generate HTML performance report
        
        Args:
            result: Load test results
            output_file: Output file path
        """
        html_report = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Load Test Report - {result.start_time.strftime('%Y-%m-%d %H:%M')}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .summary {{ background: #f0f0f0; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
        .metric {{ display: inline-block; margin: 10px 20px; }}
        .metric-value {{ font-size: 24px; font-weight: bold; color: #333; }}
        .metric-label {{ color: #666; }}
        .pass {{ color: green; }}
        .fail {{ color: red; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background: #f0f0f0; }}
    </style>
</head>
<body>
    <h1>Load Test Performance Report</h1>
    
    <div class="summary">
        <h2>Test Summary</h2>
        <div class="metric">
            <div class="metric-label">Duration</div>
            <div class="metric-value">{(result.end_time - result.start_time).total_seconds():.1f}s</div>
        </div>
        <div class="metric">
            <div class="metric-label">Total Requests</div>
            <div class="metric-value">{result.total_requests:,}</div>
        </div>
        <div class="metric">
            <div class="metric-label">Success Rate</div>
            <div class="metric-value {'pass' if result.error_rate < 0.01 else 'fail'}">
                {(1 - result.error_rate) * 100:.1f}%
            </div>
        </div>
        <div class="metric">
            <div class="metric-label">Throughput</div>
            <div class="metric-value">{result.requests_per_second:.1f} req/s</div>
        </div>
    </div>
    
    <h2>Response Time Distribution</h2>
    <table>
        <tr>
            <th>Metric</th>
            <th>Value (ms)</th>
            <th>Status</th>
        </tr>
        <tr>
            <td>Minimum</td>
            <td>{result.min_response_time:.1f}</td>
            <td class="pass">✓</td>
        </tr>
        <tr>
            <td>Mean</td>
            <td>{result.mean_response_time:.1f}</td>
            <td class="{'pass' if result.mean_response_time < 200 else 'fail'}">
                {'✓' if result.mean_response_time < 200 else '✗'}
            </td>
        </tr>
        <tr>
            <td>Median</td>
            <td>{result.median_response_time:.1f}</td>
            <td class="{'pass' if result.median_response_time < 200 else 'fail'}">
                {'✓' if result.median_response_time < 200 else '✗'}
            </td>
        </tr>
        <tr>
            <td>95th Percentile</td>
            <td>{result.p95_response_time:.1f}</td>
            <td class="{'pass' if result.p95_response_time < 500 else 'fail'}">
                {'✓' if result.p95_response_time < 500 else '✗'}
            </td>
        </tr>
        <tr>
            <td>99th Percentile</td>
            <td>{result.p99_response_time:.1f}</td>
            <td class="{'pass' if result.p99_response_time < 1000 else 'fail'}">
                {'✓' if result.p99_response_time < 1000 else '✗'}
            </td>
        </tr>
        <tr>
            <td>Maximum</td>
            <td>{result.max_response_time:.1f}</td>
            <td>-</td>
        </tr>
    </table>
    
    <h2>Error Analysis</h2>
    <table>
        <tr>
            <th>Error Type</th>
            <th>Count</th>
            <th>Percentage</th>
        </tr>
        {''.join([f'<tr><td>{error_type}</td><td>{count}</td><td>{count/result.total_requests*100:.2f}%</td></tr>' 
                  for error_type, count in result.error_types.items()])}
    </table>
    
    <h2>Test Configuration</h2>
    <ul>
        <li>Target URL: {self.config.base_url}</li>
        <li>Virtual Users: {self.config.num_users}</li>
        <li>Spawn Rate: {self.config.spawn_rate} users/sec</li>
        <li>Test Duration: {self.config.test_duration} seconds</li>
    </ul>
    
    <h2>Performance Thresholds</h2>
    <table>
        <tr>
            <th>Metric</th>
            <th>Threshold</th>
            <th>Actual</th>
            <th>Status</th>
        </tr>
        <tr>
            <td>P95 Response Time</td>
            <td>&lt; {self.config.p95_threshold_ms}ms</td>
            <td>{result.p95_response_time:.1f}ms</td>
            <td class="{'pass' if result.p95_response_time < self.config.p95_threshold_ms else 'fail'}">
                {'PASS' if result.p95_response_time < self.config.p95_threshold_ms else 'FAIL'}
            </td>
        </tr>
        <tr>
            <td>P99 Response Time</td>
            <td>&lt; {self.config.p99_threshold_ms}ms</td>
            <td>{result.p99_response_time:.1f}ms</td>
            <td class="{'pass' if result.p99_response_time < self.config.p99_threshold_ms else 'fail'}">
                {'PASS' if result.p99_response_time < self.config.p99_threshold_ms else 'FAIL'}
            </td>
        </tr>
        <tr>
            <td>Error Rate</td>
            <td>&lt; {self.config.error_rate_threshold * 100:.1f}%</td>
            <td>{result.error_rate * 100:.2f}%</td>
            <td class="{'pass' if result.error_rate < self.config.error_rate_threshold else 'fail'}">
                {'PASS' if result.error_rate < self.config.error_rate_threshold else 'FAIL'}
            </td>
        </tr>
    </table>
    
    <p><small>Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</small></p>
</body>
</html>
        """
        
        with open(output_file, 'w') as f:
            f.write(html_report)
        
        print(f"Performance report generated: {output_file}")
        
        # Return summary for CI/CD integration
        return {
            'passed': all([
                result.p95_response_time < self.config.p95_threshold_ms,
                result.p99_response_time < self.config.p99_threshold_ms,
                result.error_rate < self.config.error_rate_threshold
            ]),
            'metrics': {
                'p95_response_time': result.p95_response_time,
                'p99_response_time': result.p99_response_time,
                'error_rate': result.error_rate,
                'throughput': result.requests_per_second
            }
        }


# CLI interface for running tests
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run load tests")
    parser.add_argument("--users", type=int, default=100, help="Number of concurrent users")
    parser.add_argument("--duration", type=int, default=300, help="Test duration in seconds")
    parser.add_argument("--spawn-rate", type=int, default=10, help="User spawn rate")
    parser.add_argument("--url", default="http://localhost:8000", help="Base URL")
    parser.add_argument("--generate-k6", action="store_true", help="Generate k6 script")
    parser.add_argument("--generate-jmeter", action="store_true", help="Generate JMeter plan")
    
    args = parser.parse_args()
    
    config = LoadTestConfig(
        base_url=args.url,
        num_users=args.users,
        spawn_rate=args.spawn_rate,
        test_duration=args.duration
    )
    
    runner = LoadTestRunner(config)
    
    if args.generate_k6:
        runner.generate_k6_script()
    elif args.generate_jmeter:
        runner.generate_jmeter_plan()
    else:
        print("Starting load test...")
        result = runner.run_locust_test()
        report = runner.generate_report(result)
        
        print(f"\nTest {'PASSED' if report['passed'] else 'FAILED'}")
        print(f"P95: {report['metrics']['p95_response_time']:.1f}ms")
        print(f"P99: {report['metrics']['p99_response_time']:.1f}ms")
        print(f"Error Rate: {report['metrics']['error_rate']*100:.2f}%")
        print(f"Throughput: {report['metrics']['throughput']:.1f} req/s")