"""
Performance Testing and Validation Script

This script validates that the optimization system meets the SLA targets:
- p50 < 100ms
- p95 < 300ms
- p99 < 500ms
"""

import asyncio
import random
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional

import aiohttp
import numpy as np
from locust import HttpUser, task, between
import asyncpg


@dataclass
class PerformanceResult:
    """Performance test result"""
    endpoint: str
    response_times: List[float]
    error_count: int
    success_count: int
    
    @property
    def p50(self) -> float:
        return np.percentile(self.response_times, 50) if self.response_times else 0
        
    @property
    def p95(self) -> float:
        return np.percentile(self.response_times, 95) if self.response_times else 0
        
    @property
    def p99(self) -> float:
        return np.percentile(self.response_times, 99) if self.response_times else 0
        
    @property
    def mean(self) -> float:
        return np.mean(self.response_times) if self.response_times else 0
        
    @property
    def throughput(self) -> float:
        total_time = sum(self.response_times) / 1000  # Convert to seconds
        return self.success_count / total_time if total_time > 0 else 0
        
    def meets_sla(self, p50_target: float = 100, p95_target: float = 300, p99_target: float = 500) -> bool:
        """Check if results meet SLA targets"""
        return (
            self.p50 <= p50_target and
            self.p95 <= p95_target and
            self.p99 <= p99_target
        )
        
    def print_summary(self):
        """Print performance summary"""
        print(f"\nEndpoint: {self.endpoint}")
        print(f"  Requests: {self.success_count} successful, {self.error_count} failed")
        print(f"  Response Times (ms):")
        print(f"    p50: {self.p50:.2f}")
        print(f"    p95: {self.p95:.2f}")
        print(f"    p99: {self.p99:.2f}")
        print(f"    Mean: {self.mean:.2f}")
        print(f"  Throughput: {self.throughput:.2f} req/s")
        print(f"  SLA Status: {'✓ PASS' if self.meets_sla() else '✗ FAIL'}")


class OptimizationTester:
    """Test the optimization system performance"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def setup(self):
        """Setup test client"""
        self.session = aiohttp.ClientSession()
        
    async def teardown(self):
        """Cleanup test client"""
        if self.session:
            await self.session.close()
            
    async def test_endpoint(
        self,
        endpoint: str,
        method: str = "GET",
        payload: Optional[dict] = None,
        num_requests: int = 1000,
        concurrent: int = 10
    ) -> PerformanceResult:
        """
        Test a single endpoint
        
        Args:
            endpoint: API endpoint path
            method: HTTP method
            payload: Request payload for POST/PUT
            num_requests: Total number of requests
            concurrent: Number of concurrent requests
            
        Returns:
            Performance test results
        """
        url = f"{self.base_url}{endpoint}"
        response_times = []
        errors = 0
        
        semaphore = asyncio.Semaphore(concurrent)
        
        async def make_request():
            async with semaphore:
                try:
                    start = time.time()
                    
                    if method == "GET":
                        async with self.session.get(url) as response:
                            await response.text()
                    elif method == "POST":
                        async with self.session.post(url, json=payload) as response:
                            await response.text()
                            
                    elapsed = (time.time() - start) * 1000  # Convert to ms
                    response_times.append(elapsed)
                    
                except Exception as e:
                    nonlocal errors
                    errors += 1
                    
        # Run requests
        tasks = [make_request() for _ in range(num_requests)]
        await asyncio.gather(*tasks, return_exceptions=True)
        
        return PerformanceResult(
            endpoint=endpoint,
            response_times=response_times,
            error_count=errors,
            success_count=len(response_times)
        )
        
    async def test_cache_performance(self) -> Dict[str, PerformanceResult]:
        """Test cache performance with different scenarios"""
        results = {}
        
        # Test cold cache (first requests)
        print("\n=== Testing Cold Cache Performance ===")
        cold_result = await self.test_endpoint(
            "/api/v1/portfolios/recommended",
            num_requests=100,
            concurrent=10
        )
        results["cold_cache"] = cold_result
        cold_result.print_summary()
        
        # Test warm cache (subsequent requests)
        print("\n=== Testing Warm Cache Performance ===")
        warm_result = await self.test_endpoint(
            "/api/v1/portfolios/recommended",
            num_requests=1000,
            concurrent=20
        )
        results["warm_cache"] = warm_result
        warm_result.print_summary()
        
        # Cache hit ratio should be high for warm cache
        improvement = ((cold_result.p50 - warm_result.p50) / cold_result.p50) * 100
        print(f"\nCache Performance Improvement: {improvement:.1f}%")
        
        return results
        
    async def test_query_optimization(self) -> Dict[str, PerformanceResult]:
        """Test query optimization with complex queries"""
        results = {}
        
        print("\n=== Testing Query Optimization ===")
        
        # Test simple query
        print("\n--- Simple Query (Point Lookup) ---")
        simple_result = await self.test_endpoint(
            "/api/v1/users/123",
            num_requests=500,
            concurrent=10
        )
        results["simple_query"] = simple_result
        simple_result.print_summary()
        
        # Test complex query with joins
        print("\n--- Complex Query (Joins + Aggregation) ---")
        complex_result = await self.test_endpoint(
            "/api/v1/portfolios/123/performance?start_date=2024-01-01&end_date=2024-12-31",
            num_requests=200,
            concurrent=5
        )
        results["complex_query"] = complex_result
        complex_result.print_summary()
        
        # Test bulk operation
        print("\n--- Bulk Operation ---")
        bulk_result = await self.test_endpoint(
            "/api/v1/portfolios/bulk",
            method="POST",
            payload={"user_ids": list(range(1, 101))},
            num_requests=50,
            concurrent=2
        )
        results["bulk_operation"] = bulk_result
        bulk_result.print_summary()
        
        return results
        
    async def test_response_optimization(self) -> Dict[str, PerformanceResult]:
        """Test response optimization features"""
        results = {}
        
        print("\n=== Testing Response Optimization ===")
        
        # Test small response
        print("\n--- Small Response (<1KB) ---")
        small_result = await self.test_endpoint(
            "/api/v1/market/quote/AAPL",
            num_requests=1000,
            concurrent=20
        )
        results["small_response"] = small_result
        small_result.print_summary()
        
        # Test medium response with compression
        print("\n--- Medium Response with Compression (10KB) ---")
        medium_result = await self.test_endpoint(
            "/api/v1/portfolios/123/transactions?limit=100",
            num_requests=500,
            concurrent=10
        )
        results["medium_response"] = medium_result
        medium_result.print_summary()
        
        # Test large response with streaming
        print("\n--- Large Response with Streaming (1MB+) ---")
        large_result = await self.test_endpoint(
            "/api/v1/reports/annual/2024",
            num_requests=50,
            concurrent=2
        )
        results["large_response"] = large_result
        large_result.print_summary()
        
        # Test partial response
        print("\n--- Partial Response (Field Filtering) ---")
        partial_result = await self.test_endpoint(
            "/api/v1/portfolios/123?fields=id,name,total_value",
            num_requests=1000,
            concurrent=20
        )
        results["partial_response"] = partial_result
        partial_result.print_summary()
        
        return results
        
    async def test_concurrent_load(self) -> PerformanceResult:
        """Test system under high concurrent load"""
        print("\n=== Testing High Concurrent Load ===")
        
        # Mix of different endpoints to simulate real usage
        endpoints = [
            ("/api/v1/portfolios/recommended", "GET", None),
            ("/api/v1/users/123", "GET", None),
            ("/api/v1/market/quote/SPY", "GET", None),
            ("/api/v1/portfolios/123/rebalance", "POST", {"target_allocation": {"stocks": 60, "bonds": 40}}),
        ]
        
        response_times = []
        errors = 0
        
        async def make_mixed_request():
            endpoint, method, payload = random.choice(endpoints)
            url = f"{self.base_url}{endpoint}"
            
            try:
                start = time.time()
                
                if method == "GET":
                    async with self.session.get(url) as response:
                        await response.text()
                else:
                    async with self.session.post(url, json=payload) as response:
                        await response.text()
                        
                elapsed = (time.time() - start) * 1000
                response_times.append(elapsed)
                
            except Exception:
                nonlocal errors
                errors += 1
                
        # Simulate 100 concurrent users making 10 requests each
        tasks = []
        for _ in range(100):  # 100 users
            for _ in range(10):  # 10 requests per user
                tasks.append(make_mixed_request())
                await asyncio.sleep(0.01)  # Small delay between requests
                
        await asyncio.gather(*tasks, return_exceptions=True)
        
        result = PerformanceResult(
            endpoint="mixed_load",
            response_times=response_times,
            error_count=errors,
            success_count=len(response_times)
        )
        
        result.print_summary()
        return result
        
    async def run_full_test(self) -> Dict[str, any]:
        """Run complete performance test suite"""
        print("=" * 80)
        print(" PERFORMANCE OPTIMIZATION TEST SUITE")
        print("=" * 80)
        print(f"\nTarget SLA: p50 < 100ms, p95 < 300ms, p99 < 500ms")
        print(f"Test started at: {datetime.now().isoformat()}")
        
        await self.setup()
        
        all_results = {}
        
        try:
            # Run all test categories
            all_results["cache"] = await self.test_cache_performance()
            all_results["query"] = await self.test_query_optimization()
            all_results["response"] = await self.test_response_optimization()
            all_results["load"] = await self.test_concurrent_load()
            
            # Generate summary
            print("\n" + "=" * 80)
            print(" PERFORMANCE TEST SUMMARY")
            print("=" * 80)
            
            total_tests = 0
            passed_tests = 0
            
            for category, results in all_results.items():
                if isinstance(results, dict):
                    for name, result in results.items():
                        total_tests += 1
                        if result.meets_sla():
                            passed_tests += 1
                            status = "✓ PASS"
                        else:
                            status = "✗ FAIL"
                        print(f"{category}/{name}: {status} (p50={result.p50:.1f}ms, p99={result.p99:.1f}ms)")
                else:
                    total_tests += 1
                    if results.meets_sla():
                        passed_tests += 1
                        status = "✓ PASS"
                    else:
                        status = "✗ FAIL"
                    print(f"{category}: {status} (p50={results.p50:.1f}ms, p99={results.p99:.1f}ms)")
                    
            print(f"\n Overall: {passed_tests}/{total_tests} tests passed")
            print(f"SLA Compliance: {'✓ ACHIEVED' if passed_tests == total_tests else '✗ NOT ACHIEVED'}")
            
        finally:
            await self.teardown()
            
        return all_results


# Locust load testing configuration
class FinancialPlannerUser(HttpUser):
    """Locust user for load testing"""
    
    wait_time = between(1, 3)
    
    def on_start(self):
        """Login and setup user session"""
        # Simulate user login
        self.client.post("/api/v1/auth/login", json={
            "username": "test_user",
            "password": "test_password"
        })
        
    @task(3)
    def view_portfolio(self):
        """View portfolio (high frequency)"""
        self.client.get("/api/v1/portfolios/123")
        
    @task(2)
    def get_market_data(self):
        """Get market quotes (medium frequency)"""
        symbols = ["AAPL", "GOOGL", "MSFT", "SPY", "QQQ"]
        symbol = random.choice(symbols)
        self.client.get(f"/api/v1/market/quote/{symbol}")
        
    @task(1)
    def run_simulation(self):
        """Run Monte Carlo simulation (low frequency)"""
        self.client.post("/api/v1/simulations/monte-carlo", json={
            "portfolio_id": 123,
            "years": 10,
            "simulations": 1000
        })
        
    @task(2)
    def get_recommendations(self):
        """Get AI recommendations"""
        self.client.get("/api/v1/recommendations/portfolio")


async def main():
    """Main entry point for performance testing"""
    tester = OptimizationTester()
    results = await tester.run_full_test()
    
    # Save results to file
    import json
    with open("performance_test_results.json", "w") as f:
        # Convert results to serializable format
        serializable_results = {}
        for category, category_results in results.items():
            if isinstance(category_results, dict):
                serializable_results[category] = {
                    name: {
                        "p50": result.p50,
                        "p95": result.p95,
                        "p99": result.p99,
                        "mean": result.mean,
                        "throughput": result.throughput,
                        "meets_sla": result.meets_sla()
                    }
                    for name, result in category_results.items()
                }
            else:
                serializable_results[category] = {
                    "p50": category_results.p50,
                    "p95": category_results.p95,
                    "p99": category_results.p99,
                    "mean": category_results.mean,
                    "throughput": category_results.throughput,
                    "meets_sla": category_results.meets_sla()
                }
                
        json.dump(serializable_results, f, indent=2)
        
    print(f"\nResults saved to performance_test_results.json")


if __name__ == "__main__":
    # Run performance tests
    asyncio.run(main())
    
    # To run Locust load testing:
    # locust -f performance_test.py --host=http://localhost:8000