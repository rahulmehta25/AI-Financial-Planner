"""
Load testing scenarios for the financial planning API.

Tests cover:
- User registration and authentication load
- Portfolio optimization under load
- Market data streaming load
- Concurrent financial calculations
- Database connection pooling
- Cache performance under load
- Memory and CPU usage monitoring
"""

import asyncio
import aiohttp
import time
import json
from typing import List, Dict, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import statistics
import logging
from concurrent.futures import ThreadPoolExecutor
import psutil
import numpy as np


@dataclass
class LoadTestResult:
    """Results from a load test scenario."""
    scenario_name: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    average_response_time: float
    p95_response_time: float
    p99_response_time: float
    requests_per_second: float
    errors: List[str]
    start_time: datetime
    end_time: datetime
    peak_memory_mb: float
    peak_cpu_percent: float


class FinancialPlannerLoadTester:
    """Load tester for financial planning API."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = None
        self.logger = logging.getLogger(__name__)
        
        # Performance monitoring
        self.process = psutil.Process()
        self.memory_samples = []
        self.cpu_samples = []
    
    async def __aenter__(self):
        """Async context manager entry."""
        connector = aiohttp.TCPConnector(
            limit=1000,  # Total connection limit
            limit_per_host=100,  # Per-host connection limit
            ttl_dns_cache=300,  # DNS cache TTL
            use_dns_cache=True
        )
        
        timeout = aiohttp.ClientTimeout(total=30, connect=10)
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={"Content-Type": "application/json"}
        )
        
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def authenticate_user(self, user_id: int) -> str:
        """Authenticate a test user and return access token."""
        auth_data = {
            "email": f"loadtest_user_{user_id}@example.com",
            "password": "LoadTest123!"
        }
        
        async with self.session.post(
            f"{self.base_url}/auth/login",
            json=auth_data
        ) as response:
            if response.status == 200:
                data = await response.json()
                return data["access_token"]
            else:
                raise Exception(f"Authentication failed: {response.status}")
    
    def monitor_system_resources(self):
        """Monitor system resources during load test."""
        while True:
            try:
                # Memory usage in MB
                memory_mb = self.process.memory_info().rss / 1024 / 1024
                self.memory_samples.append(memory_mb)
                
                # CPU usage percentage
                cpu_percent = self.process.cpu_percent()
                self.cpu_samples.append(cpu_percent)
                
                time.sleep(1)  # Sample every second
                
            except psutil.NoSuchProcess:
                break
            except Exception as e:
                self.logger.error(f"Resource monitoring error: {e}")
                break
    
    async def run_load_test_scenario(
        self,
        scenario_name: str,
        test_function,
        concurrent_users: int,
        duration_seconds: int,
        **kwargs
    ) -> LoadTestResult:
        """Run a load test scenario with specified parameters."""
        
        self.logger.info(
            f"Starting load test: {scenario_name} with {concurrent_users} users for {duration_seconds}s"
        )
        
        # Start resource monitoring
        monitor_task = asyncio.create_task(
            asyncio.to_thread(self.monitor_system_resources)
        )
        
        start_time = datetime.now()
        end_time = start_time + timedelta(seconds=duration_seconds)
        
        # Track results
        response_times = []
        successful_requests = 0
        failed_requests = 0
        errors = []
        
        # Create semaphore to limit concurrent requests
        semaphore = asyncio.Semaphore(concurrent_users)
        
        async def user_session(user_id: int):
            """Simulate a single user session."""
            nonlocal successful_requests, failed_requests
            
            try:
                # Authenticate user
                token = await self.authenticate_user(user_id)
                headers = {"Authorization": f"Bearer {token}"}
                
                while datetime.now() < end_time:
                    async with semaphore:
                        request_start = time.time()
                        
                        try:
                            await test_function(user_id, headers, **kwargs)
                            
                            request_time = time.time() - request_start
                            response_times.append(request_time)
                            successful_requests += 1
                            
                        except Exception as e:
                            failed_requests += 1
                            errors.append(str(e))
                            self.logger.error(f"Request failed: {e}")
                        
                        # Small delay between requests
                        await asyncio.sleep(0.1)
                        
            except Exception as e:
                self.logger.error(f"User session {user_id} failed: {e}")
                errors.append(f"User {user_id}: {str(e)}")
        
        # Start user sessions
        user_tasks = [
            asyncio.create_task(user_session(i))
            for i in range(concurrent_users)
        ]
        
        # Wait for test completion
        await asyncio.gather(*user_tasks, return_exceptions=True)
        
        # Stop resource monitoring
        monitor_task.cancel()
        
        actual_end_time = datetime.now()
        total_duration = (actual_end_time - start_time).total_seconds()
        
        # Calculate metrics
        total_requests = successful_requests + failed_requests
        requests_per_second = total_requests / total_duration if total_duration > 0 else 0
        
        avg_response_time = statistics.mean(response_times) if response_times else 0
        p95_response_time = np.percentile(response_times, 95) if response_times else 0
        p99_response_time = np.percentile(response_times, 99) if response_times else 0
        
        peak_memory_mb = max(self.memory_samples) if self.memory_samples else 0
        peak_cpu_percent = max(self.cpu_samples) if self.cpu_samples else 0
        
        result = LoadTestResult(
            scenario_name=scenario_name,
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            average_response_time=avg_response_time,
            p95_response_time=p95_response_time,
            p99_response_time=p99_response_time,
            requests_per_second=requests_per_second,
            errors=errors[:10],  # Keep only first 10 errors
            start_time=start_time,
            end_time=actual_end_time,
            peak_memory_mb=peak_memory_mb,
            peak_cpu_percent=peak_cpu_percent
        )
        
        self.logger.info(f"Load test completed: {result}")
        return result


class LoadTestScenarios:
    """Collection of load test scenarios for financial planning API."""
    
    def __init__(self, load_tester: FinancialPlannerLoadTester):
        self.load_tester = load_tester
        self.session = load_tester.session
        self.base_url = load_tester.base_url
    
    async def user_registration_load(self, user_id: int, headers: Dict, **kwargs):
        """Test user registration under load."""
        
        registration_data = {
            "email": f"loadtest_new_{user_id}_{int(time.time())}@example.com",
            "password": "LoadTest123!",
            "first_name": f"LoadTest{user_id}",
            "last_name": "User",
            "phone_number": f"+1-555-{user_id:04d}-{int(time.time()) % 10000:04d}",
            "date_of_birth": "1990-01-01"
        }
        
        async with self.session.post(
            f"{self.base_url}/auth/register",
            json=registration_data
        ) as response:
            if response.status not in [201, 409]:  # 409 = already exists
                raise Exception(f"Registration failed: {response.status}")
    
    async def portfolio_optimization_load(self, user_id: int, headers: Dict, **kwargs):
        """Test portfolio optimization under load."""
        
        optimization_request = {
            "universe": [
                {"symbol": "SPY", "asset_class": "US_EQUITY", "weight": 0.0},
                {"symbol": "BND", "asset_class": "BONDS", "weight": 0.0},
                {"symbol": "VNQ", "asset_class": "REAL_ESTATE", "weight": 0.0},
                {"symbol": "VXUS", "asset_class": "INTERNATIONAL", "weight": 0.0}
            ],
            "objective": "maximize_sharpe",
            "constraints": {
                "max_weight": 0.6,
                "min_weight": 0.1
            }
        }
        
        async with self.session.post(
            f"{self.base_url}/portfolio/optimize",
            json=optimization_request,
            headers=headers
        ) as response:
            if response.status != 200:
                raise Exception(f"Optimization failed: {response.status}")
            
            result = await response.json()
            if "weights" not in result:
                raise Exception("Invalid optimization response")
    
    async def market_data_load(self, user_id: int, headers: Dict, **kwargs):
        """Test market data retrieval under load."""
        
        symbols = ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA"]
        symbol = symbols[user_id % len(symbols)]
        
        # Test both individual and batch quotes
        if user_id % 2 == 0:
            # Individual quote
            async with self.session.get(
                f"{self.base_url}/market-data/quote/{symbol}",
                headers=headers
            ) as response:
                if response.status != 200:
                    raise Exception(f"Quote retrieval failed: {response.status}")
        else:
            # Batch quotes
            async with self.session.post(
                f"{self.base_url}/market-data/batch-quotes",
                json={"symbols": symbols[:3]},
                headers=headers
            ) as response:
                if response.status != 200:
                    raise Exception(f"Batch quotes failed: {response.status}")
    
    async def monte_carlo_simulation_load(self, user_id: int, headers: Dict, **kwargs):
        """Test Monte Carlo simulations under load."""
        
        simulation_request = {
            "portfolio": {
                "assets": [
                    {"symbol": "SPY", "weight": 0.6},
                    {"symbol": "BND", "weight": 0.4}
                ]
            },
            "num_simulations": 1000,  # Lighter load for stress test
            "time_horizon": 30,
            "confidence_levels": [0.05, 0.5, 0.95]
        }
        
        async with self.session.post(
            f"{self.base_url}/simulations/monte-carlo",
            json=simulation_request,
            headers=headers
        ) as response:
            if response.status != 200:
                raise Exception(f"Simulation failed: {response.status}")
            
            result = await response.json()
            if "success_probability" not in result:
                raise Exception("Invalid simulation response")
    
    async def retirement_planning_load(self, user_id: int, headers: Dict, **kwargs):
        """Test retirement planning calculations under load."""
        
        retirement_request = {
            "current_age": 30 + (user_id % 30),
            "retirement_age": 65,
            "current_income": 50000 + (user_id * 1000),
            "current_savings": 10000 + (user_id * 500),
            "monthly_contribution": 500 + (user_id * 10),
            "expected_return": 0.07,
            "inflation_rate": 0.025
        }
        
        async with self.session.post(
            f"{self.base_url}/retirement/calculate-needs",
            json=retirement_request,
            headers=headers
        ) as response:
            if response.status != 200:
                raise Exception(f"Retirement calculation failed: {response.status}")
    
    async def tax_optimization_load(self, user_id: int, headers: Dict, **kwargs):
        """Test tax optimization under load."""
        
        tax_request = {
            "accounts": [
                {
                    "account_type": "taxable",
                    "balance": 50000 + (user_id * 1000),
                    "positions": [
                        {"symbol": "AAPL", "quantity": 100, "cost_basis": 150.0},
                        {"symbol": "MSFT", "quantity": 50, "cost_basis": 300.0}
                    ]
                }
            ],
            "tax_rate": 0.22,
            "min_loss_threshold": 1000
        }
        
        async with self.session.post(
            f"{self.base_url}/tax-optimization/analyze",
            json=tax_request,
            headers=headers
        ) as response:
            if response.status != 200:
                raise Exception(f"Tax optimization failed: {response.status}")
    
    async def mixed_workload(self, user_id: int, headers: Dict, **kwargs):
        """Test mixed workload simulating real user behavior."""
        
        # Simulate different user actions with realistic probabilities
        actions = [
            (self.market_data_load, 0.4),           # 40% - Check market data
            (self.portfolio_optimization_load, 0.2), # 20% - Run optimization
            (self.retirement_planning_load, 0.2),    # 20% - Retirement planning
            (self.tax_optimization_load, 0.1),       # 10% - Tax optimization
            (self.monte_carlo_simulation_load, 0.1)  # 10% - Monte Carlo
        ]
        
        # Select action based on probabilities
        rand = np.random.random()
        cumulative_prob = 0
        
        for action_func, probability in actions:
            cumulative_prob += probability
            if rand <= cumulative_prob:
                await action_func(user_id, headers, **kwargs)
                break


async def run_comprehensive_load_tests():
    """Run comprehensive load tests for the financial planning API."""
    
    results = []
    
    async with FinancialPlannerLoadTester() as load_tester:
        scenarios = LoadTestScenarios(load_tester)
        
        # Test scenarios with increasing load
        test_cases = [
            # Light load tests
            ("User Registration - Light", scenarios.user_registration_load, 5, 30),
            ("Portfolio Optimization - Light", scenarios.portfolio_optimization_load, 3, 30),
            ("Market Data - Light", scenarios.market_data_load, 10, 30),
            
            # Medium load tests
            ("Monte Carlo - Medium", scenarios.monte_carlo_simulation_load, 5, 60),
            ("Retirement Planning - Medium", scenarios.retirement_planning_load, 8, 60),
            ("Tax Optimization - Medium", scenarios.tax_optimization_load, 6, 60),
            
            # High load tests
            ("Mixed Workload - High", scenarios.mixed_workload, 20, 120),
            ("Market Data - High", scenarios.market_data_load, 50, 60),
            
            # Stress tests
            ("Portfolio Optimization - Stress", scenarios.portfolio_optimization_load, 15, 180),
            ("Mixed Workload - Stress", scenarios.mixed_workload, 100, 300)
        ]
        
        for name, test_func, users, duration in test_cases:
            try:
                result = await load_tester.run_load_test_scenario(
                    scenario_name=name,
                    test_function=test_func,
                    concurrent_users=users,
                    duration_seconds=duration
                )
                results.append(result)
                
                # Brief pause between tests
                await asyncio.sleep(10)
                
            except Exception as e:
                logging.error(f"Load test {name} failed: {e}")
                continue
    
    # Generate load test report
    generate_load_test_report(results)
    
    return results


def generate_load_test_report(results: List[LoadTestResult]):
    """Generate a comprehensive load test report."""
    
    report = ["\n=== FINANCIAL PLANNER LOAD TEST REPORT ==="]
    report.append(f"Report generated: {datetime.now()}\n")
    
    # Summary table
    report.append("SUMMARY TABLE:")
    report.append("-" * 120)
    report.append(
        f"{'Scenario':<40} {'Users':<6} {'Duration':<8} {'Total Req':<10} {'Success Rate':<12} "
        f"{'Avg RT (ms)':<12} {'P95 RT (ms)':<12} {'RPS':<8} {'Peak Memory (MB)':<16}"
    )
    report.append("-" * 120)
    
    for result in results:
        success_rate = (result.successful_requests / result.total_requests * 100) if result.total_requests > 0 else 0
        
        report.append(
            f"{result.scenario_name:<40} {result.total_requests // (result.end_time - result.start_time).total_seconds() * 60:<6.0f} "
            f"{(result.end_time - result.start_time).total_seconds():<8.0f} {result.total_requests:<10} "
            f"{success_rate:<12.1f}% {result.average_response_time * 1000:<12.1f} "
            f"{result.p95_response_time * 1000:<12.1f} {result.requests_per_second:<8.1f} {result.peak_memory_mb:<16.1f}"
        )
    
    report.append("-" * 120)
    
    # Performance analysis
    report.append("\nPERFORMANCE ANALYSIS:")
    report.append("=" * 50)
    
    # Identify best and worst performing scenarios
    if results:
        best_rps = max(results, key=lambda r: r.requests_per_second)
        worst_success_rate = min(results, key=lambda r: r.successful_requests / r.total_requests if r.total_requests > 0 else 0)
        highest_memory = max(results, key=lambda r: r.peak_memory_mb)
        
        report.append(f"🚀 Best Throughput: {best_rps.scenario_name} ({best_rps.requests_per_second:.1f} RPS)")
        report.append(f"⚠️  Lowest Success Rate: {worst_success_rate.scenario_name} ({worst_success_rate.successful_requests / worst_success_rate.total_requests * 100:.1f}%)")
        report.append(f"📊 Highest Memory Usage: {highest_memory.scenario_name} ({highest_memory.peak_memory_mb:.1f} MB)")
    
    # Recommendations
    report.append("\nRECOMMENDATIONS:")
    report.append("=" * 50)
    
    for result in results:
        if result.failed_requests > result.successful_requests * 0.05:  # >5% failure rate
            report.append(f"🔥 {result.scenario_name}: High failure rate ({result.failed_requests / result.total_requests * 100:.1f}%). Consider optimization.")
        
        if result.average_response_time > 2.0:  # >2 second average
            report.append(f"🐌 {result.scenario_name}: Slow response time ({result.average_response_time:.2f}s avg). Consider caching or optimization.")
        
        if result.peak_memory_mb > 1000:  # >1GB peak memory
            report.append(f"💾 {result.scenario_name}: High memory usage ({result.peak_memory_mb:.1f}MB). Check for memory leaks.")
    
    # Error summary
    report.append("\nERROR SUMMARY:")
    report.append("=" * 50)
    
    for result in results:
        if result.errors:
            report.append(f"\n{result.scenario_name} errors:")
            for error in result.errors:
                report.append(f"  - {error}")
    
    # Write report to file
    report_content = "\n".join(report)
    
    with open(f"load_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt", "w") as f:
        f.write(report_content)
    
    print(report_content)


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Run load tests
    asyncio.run(run_comprehensive_load_tests())
