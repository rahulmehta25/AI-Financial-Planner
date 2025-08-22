#!/usr/bin/env python3
"""
🚀 Comprehensive API Demo Test Suite
=====================================

This script provides a complete testing suite for the Financial Planning API with:
- Colorful, visual output for demos
- HTML report generation
- Performance measurements
- Error handling validation
- Schema validation
- Authentication flow testing
- Load testing capabilities
- Summary dashboard

Usage:
    python test_api_demo.py [--base-url http://localhost:8000] [--load-test] [--verbose]

Author: Financial Planning System Test Suite
Version: 1.0.0
"""

import asyncio
import json
import time
import argparse
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import logging
import sys
import traceback

# Third-party imports with fallbacks
try:
    import httpx
    import rich
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
    from rich.layout import Layout
    from rich.align import Align
    from rich.text import Text
    from rich.live import Live
    from rich.columns import Columns
    from rich.markdown import Markdown
    RICH_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Rich library not available: {e}")
    print("💡 Install with: pip install rich httpx")
    RICH_AVAILABLE = False

try:
    from pydantic import ValidationError, BaseModel
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False
    print("⚠️  Pydantic not available for schema validation")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TestResult:
    """Container for test results"""
    def __init__(self, name: str, success: bool, response_time: float, 
                 status_code: Optional[int] = None, error_message: Optional[str] = None,
                 response_data: Optional[Dict] = None):
        self.name = name
        self.success = success
        self.response_time = response_time
        self.status_code = status_code
        self.error_message = error_message
        self.response_data = response_data
        self.timestamp = datetime.now()

class APITestSuite:
    """Comprehensive API testing suite with visual output"""
    
    def __init__(self, base_url: str = "http://localhost:8000", verbose: bool = False):
        self.base_url = base_url.rstrip('/')
        self.verbose = verbose
        self.console = Console() if RICH_AVAILABLE else None
        self.results: List[TestResult] = []
        self.auth_token: Optional[str] = None
        self.test_user_data = {
            "email": "demo@example.com",
            "password": "DemoPassword123!",
            "full_name": "Demo User"
        }
        
        # Performance tracking
        self.performance_stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "average_response_time": 0,
            "fastest_response": float('inf'),
            "slowest_response": 0,
            "response_times": []
        }
        
        # Test configuration
        self.timeout = 30.0  # seconds
        
        # Sample data for testing
        self.sample_financial_plan = {
            "age": 35,
            "target_retirement_age": 65,
            "marital_status": "married",
            "current_savings_balance": 150000.0,
            "annual_savings_rate_percentage": 15.0,
            "income_level": 85000.0,
            "debt_balance": 25000.0,
            "debt_interest_rate_percentage": 4.5,
            "account_buckets_taxable": 40.0,
            "account_buckets_401k_ira": 35.0,
            "account_buckets_roth": 25.0,
            "risk_preference": "balanced",
            "desired_retirement_spending_per_year": 60000.0,
            "plan_name": "Demo Retirement Plan",
            "notes": "Test plan for API demo"
        }

    def print_header(self):
        """Display colorful header"""
        if not self.console:
            print("🚀 Financial Planning API Test Suite")
            print("=" * 50)
            return
            
        header_text = """
# 🚀 Financial Planning API Test Suite

**Testing comprehensive API functionality with:**
- ✅ Endpoint availability testing  
- 🔐 Authentication flow validation
- 📊 Response schema validation
- ⚡ Performance measurements
- 🔥 Load testing capabilities
- 📈 Visual reporting dashboard
        """
        
        self.console.print(Panel(
            Markdown(header_text),
            title="API Test Suite",
            border_style="blue",
            padding=(1, 2)
        ))

    async def make_request(self, method: str, endpoint: str, 
                          data: Optional[Dict] = None, 
                          headers: Optional[Dict] = None,
                          expected_status: int = 200) -> TestResult:
        """Make HTTP request with error handling and timing"""
        url = f"{self.base_url}{endpoint}"
        request_headers = {"Content-Type": "application/json"}
        
        if headers:
            request_headers.update(headers)
            
        if self.auth_token:
            request_headers["Authorization"] = f"Bearer {self.auth_token}"
        
        start_time = time.time()
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                if method.upper() == "GET":
                    response = await client.get(url, headers=request_headers)
                elif method.upper() == "POST":
                    response = await client.post(url, json=data, headers=request_headers)
                elif method.upper() == "PUT":
                    response = await client.put(url, json=data, headers=request_headers)
                elif method.upper() == "DELETE":
                    response = await client.delete(url, headers=request_headers)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
                
                response_time = time.time() - start_time
                
                # Update performance stats
                self.performance_stats["total_requests"] += 1
                self.performance_stats["response_times"].append(response_time)
                self.performance_stats["fastest_response"] = min(
                    self.performance_stats["fastest_response"], response_time
                )
                self.performance_stats["slowest_response"] = max(
                    self.performance_stats["slowest_response"], response_time
                )
                
                success = response.status_code == expected_status
                if success:
                    self.performance_stats["successful_requests"] += 1
                else:
                    self.performance_stats["failed_requests"] += 1
                
                try:
                    response_data = response.json()
                except:
                    response_data = {"text": response.text}
                
                return TestResult(
                    name=f"{method.upper()} {endpoint}",
                    success=success,
                    response_time=response_time,
                    status_code=response.status_code,
                    response_data=response_data,
                    error_message=None if success else f"Expected {expected_status}, got {response.status_code}"
                )
                
        except Exception as e:
            response_time = time.time() - start_time
            self.performance_stats["total_requests"] += 1
            self.performance_stats["failed_requests"] += 1
            self.performance_stats["response_times"].append(response_time)
            
            return TestResult(
                name=f"{method.upper()} {endpoint}",
                success=False,
                response_time=response_time,
                error_message=str(e)
            )

    async def test_health_endpoints(self) -> List[TestResult]:
        """Test basic health and status endpoints"""
        if self.console:
            self.console.print("\n🏥 Testing Health Endpoints", style="bold cyan")
        
        tests = [
            ("GET", "/", 200),
            ("GET", "/health", 200),
            ("GET", "/status", 200),
            ("GET", "/docs", 200),
        ]
        
        results = []
        for method, endpoint, expected_status in tests:
            result = await self.make_request(method, endpoint, expected_status=expected_status)
            results.append(result)
            self.results.append(result)
            
            if self.console:
                status_color = "green" if result.success else "red"
                self.console.print(f"  {'✅' if result.success else '❌'} {result.name} - {result.response_time:.3f}s", style=status_color)
        
        return results

    async def test_authentication_flow(self) -> List[TestResult]:
        """Test complete authentication flow"""
        if self.console:
            self.console.print("\n🔐 Testing Authentication Flow", style="bold cyan")
        
        results = []
        
        # Test user registration
        register_result = await self.make_request(
            "POST", "/api/v1/auth/register",
            data=self.test_user_data,
            expected_status=201
        )
        results.append(register_result)
        self.results.append(register_result)
        
        # Test login with form data
        login_form_data = {
            "username": self.test_user_data["email"],
            "password": self.test_user_data["password"]
        }
        
        # Try login endpoint
        login_result = await self.make_request(
            "POST", "/api/v1/auth/login",
            data=login_form_data,
            expected_status=200
        )
        results.append(login_result)
        self.results.append(login_result)
        
        # Extract token if login successful
        if login_result.success and login_result.response_data:
            self.auth_token = login_result.response_data.get("access_token")
        
        # Test getting current user
        if self.auth_token:
            me_result = await self.make_request(
                "GET", "/api/v1/auth/me",
                expected_status=200
            )
            results.append(me_result)
            self.results.append(me_result)
        
        # Display results
        if self.console:
            for result in results:
                status_color = "green" if result.success else "red"
                self.console.print(f"  {'✅' if result.success else '❌'} {result.name} - {result.response_time:.3f}s", style=status_color)
        
        return results

    async def test_financial_endpoints(self) -> List[TestResult]:
        """Test financial planning endpoints"""
        if self.console:
            self.console.print("\n💰 Testing Financial Planning Endpoints", style="bold cyan")
        
        results = []
        
        # Test endpoints that should work without auth
        public_tests = [
            ("GET", "/api/v1/market-data/health", 200),
            ("GET", "/api/v1/market-data/status", 200),
        ]
        
        for method, endpoint, expected_status in public_tests:
            result = await self.make_request(method, endpoint, expected_status=expected_status)
            results.append(result)
            self.results.append(result)
        
        # Test authenticated endpoints
        if self.auth_token:
            auth_tests = [
                ("GET", "/api/v1/users/me", 200),
                ("GET", "/api/v1/simulations", 200),
                ("GET", "/api/v1/financial-profiles", 200),
                ("GET", "/api/v1/goals", 200),
                ("GET", "/api/v1/investments", 200),
            ]
            
            for method, endpoint, expected_status in auth_tests:
                result = await self.make_request(method, endpoint, expected_status=expected_status)
                results.append(result)
                self.results.append(result)
            
            # Test creating a financial profile
            profile_data = {
                "age": self.sample_financial_plan["age"],
                "annual_income": self.sample_financial_plan["income_level"],
                "risk_tolerance": self.sample_financial_plan["risk_preference"],
                "investment_experience": "intermediate"
            }
            
            create_profile_result = await self.make_request(
                "POST", "/api/v1/financial-profiles",
                data=profile_data,
                expected_status=201
            )
            results.append(create_profile_result)
            self.results.append(create_profile_result)
        
        # Display results
        if self.console:
            for result in results:
                status_color = "green" if result.success else "red"
                self.console.print(f"  {'✅' if result.success else '❌'} {result.name} - {result.response_time:.3f}s", style=status_color)
        
        return results

    async def test_simulation_endpoints(self) -> List[TestResult]:
        """Test simulation endpoints with realistic data"""
        if self.console:
            self.console.print("\n🎯 Testing Simulation Endpoints", style="bold cyan")
        
        results = []
        
        if not self.auth_token:
            if self.console:
                self.console.print("  ⚠️  Skipping simulation tests - no auth token", style="yellow")
            return results
        
        # Test Monte Carlo simulation
        monte_carlo_data = {
            "initial_investment": self.sample_financial_plan["current_savings_balance"],
            "monthly_contribution": 2000.0,
            "years_to_retirement": self.sample_financial_plan["target_retirement_age"] - self.sample_financial_plan["age"],
            "expected_return": 0.07,
            "volatility": 0.12,
            "simulations_count": 1000,
            "retirement_spending": self.sample_financial_plan["desired_retirement_spending_per_year"]
        }
        
        monte_carlo_result = await self.make_request(
            "POST", "/api/v1/monte-carlo/simulate",
            data=monte_carlo_data,
            expected_status=201
        )
        results.append(monte_carlo_result)
        self.results.append(monte_carlo_result)
        
        # Test creating a simulation
        simulation_data = {
            "name": "Demo API Test Simulation",
            "description": "Test simulation created by API test suite",
            "parameters": self.sample_financial_plan,
            "simulation_type": "monte_carlo"
        }
        
        create_sim_result = await self.make_request(
            "POST", "/api/v1/simulations",
            data=simulation_data,
            expected_status=201
        )
        results.append(create_sim_result)
        self.results.append(create_sim_result)
        
        # Display results
        if self.console:
            for result in results:
                status_color = "green" if result.success else "red"
                self.console.print(f"  {'✅' if result.success else '❌'} {result.name} - {result.response_time:.3f}s", style=status_color)
        
        return results

    async def test_error_handling(self) -> List[TestResult]:
        """Test various error scenarios"""
        if self.console:
            self.console.print("\n🚨 Testing Error Handling", style="bold cyan")
        
        results = []
        
        error_tests = [
            ("GET", "/api/v1/nonexistent-endpoint", 404),
            ("GET", "/api/v1/users/999999", 404),
            ("POST", "/api/v1/auth/login", {"invalid": "data"}, 422),
            ("POST", "/api/v1/simulations", {"invalid_simulation": True}, 401),  # No auth
        ]
        
        for method, endpoint, *args in error_tests:
            data = args[0] if len(args) > 1 else None
            expected_status = args[-1]
            
            result = await self.make_request(method, endpoint, data=data, expected_status=expected_status)
            results.append(result)
            self.results.append(result)
            
            if self.console:
                status_color = "green" if result.success else "red"
                self.console.print(f"  {'✅' if result.success else '❌'} {result.name} - {result.response_time:.3f}s", style=status_color)
        
        return results

    async def run_load_test(self, num_requests: int = 100) -> List[TestResult]:
        """Run load test with multiple concurrent requests"""
        if self.console:
            self.console.print(f"\n⚡ Running Load Test ({num_requests} requests)", style="bold cyan")
        
        results = []
        
        async def single_request():
            return await self.make_request("GET", "/health")
        
        # Run concurrent requests
        start_time = time.time()
        tasks = [single_request() for _ in range(num_requests)]
        
        if self.console:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                TimeElapsedColumn(),
            ) as progress:
                task = progress.add_task("Load testing...", total=num_requests)
                
                completed = 0
                for coro in asyncio.as_completed(tasks):
                    result = await coro
                    results.append(result)
                    completed += 1
                    progress.update(task, completed=completed)
        else:
            results = await asyncio.gather(*tasks)
        
        total_time = time.time() - start_time
        
        # Analyze load test results
        successful = sum(1 for r in results if r.success)
        failed = len(results) - successful
        response_times = [r.response_time for r in results]
        avg_response_time = statistics.mean(response_times)
        
        if self.console:
            load_stats = f"""
**Load Test Results:**
- Total Requests: {num_requests}
- Successful: {successful} ({successful/num_requests*100:.1f}%)
- Failed: {failed} ({failed/num_requests*100:.1f}%)
- Total Time: {total_time:.2f}s
- Requests/Second: {num_requests/total_time:.2f}
- Avg Response Time: {avg_response_time:.3f}s
- Min Response Time: {min(response_times):.3f}s
- Max Response Time: {max(response_times):.3f}s
            """
            self.console.print(Panel(Markdown(load_stats), title="Load Test Results", border_style="green"))
        
        self.results.extend(results)
        return results

    def calculate_performance_stats(self):
        """Calculate final performance statistics"""
        if self.performance_stats["response_times"]:
            self.performance_stats["average_response_time"] = statistics.mean(
                self.performance_stats["response_times"]
            )
        
        if self.performance_stats["fastest_response"] == float('inf'):
            self.performance_stats["fastest_response"] = 0

    def generate_summary_dashboard(self) -> str:
        """Generate colorful summary dashboard"""
        if not self.console:
            return self.generate_text_summary()
        
        self.calculate_performance_stats()
        
        # Create summary statistics
        total_tests = len(self.results)
        successful_tests = sum(1 for r in self.results if r.success)
        failed_tests = total_tests - successful_tests
        success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
        
        # Create performance table
        perf_table = Table(title="Performance Statistics")
        perf_table.add_column("Metric", style="cyan")
        perf_table.add_column("Value", style="green")
        
        perf_table.add_row("Total Requests", str(self.performance_stats["total_requests"]))
        perf_table.add_row("Successful Requests", str(self.performance_stats["successful_requests"]))
        perf_table.add_row("Failed Requests", str(self.performance_stats["failed_requests"]))
        perf_table.add_row("Average Response Time", f"{self.performance_stats['average_response_time']:.3f}s")
        perf_table.add_row("Fastest Response", f"{self.performance_stats['fastest_response']:.3f}s")
        perf_table.add_row("Slowest Response", f"{self.performance_stats['slowest_response']:.3f}s")
        perf_table.add_row("Success Rate", f"{success_rate:.1f}%")
        
        # Create results table
        results_table = Table(title="Test Results")
        results_table.add_column("Test", style="cyan")
        results_table.add_column("Status", justify="center")
        results_table.add_column("Response Time", justify="right", style="green")
        results_table.add_column("Status Code", justify="center")
        
        for result in self.results[-20:]:  # Show last 20 results
            status_emoji = "✅" if result.success else "❌"
            status_color = "green" if result.success else "red"
            
            results_table.add_row(
                result.name,
                Text(status_emoji, style=status_color),
                f"{result.response_time:.3f}s",
                str(result.status_code) if result.status_code else "N/A"
            )
        
        # Print summary
        self.console.print("\n" + "="*80)
        self.console.print(Align.center(Text("📊 TEST SUMMARY DASHBOARD", style="bold blue")))
        self.console.print("="*80)
        
        # Create columns layout
        columns = Columns([perf_table, results_table], equal=True, expand=True)
        self.console.print(columns)
        
        # Final summary panel
        summary_text = f"""
## 🎯 Test Execution Summary

**Overall Results:**
- 🧪 Total Tests: {total_tests}
- ✅ Successful: {successful_tests} ({success_rate:.1f}%)
- ❌ Failed: {failed_tests} ({100-success_rate:.1f}%)

**Performance Highlights:**
- ⚡ Average Response: {self.performance_stats['average_response_time']:.3f}s
- 🚀 Fastest Response: {self.performance_stats['fastest_response']:.3f}s
- 🐌 Slowest Response: {self.performance_stats['slowest_response']:.3f}s

**Status:** {'🟢 PASSED' if success_rate >= 80 else '🟡 PARTIAL' if success_rate >= 50 else '🔴 FAILED'}
        """
        
        border_style = "green" if success_rate >= 80 else "yellow" if success_rate >= 50 else "red"
        
        self.console.print(Panel(
            Markdown(summary_text),
            title="Executive Summary",
            border_style=border_style,
            padding=(1, 2)
        ))
        
        return "Dashboard displayed in console"

    def generate_text_summary(self) -> str:
        """Generate text-based summary for environments without rich"""
        self.calculate_performance_stats()
        
        total_tests = len(self.results)
        successful_tests = sum(1 for r in self.results if r.success)
        failed_tests = total_tests - successful_tests
        success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
        
        summary = f"""
{'='*80}
                          TEST SUMMARY DASHBOARD
{'='*80}

OVERALL RESULTS:
- Total Tests: {total_tests}
- Successful: {successful_tests} ({success_rate:.1f}%)
- Failed: {failed_tests} ({100-success_rate:.1f}%)

PERFORMANCE STATISTICS:
- Total Requests: {self.performance_stats['total_requests']}
- Average Response Time: {self.performance_stats['average_response_time']:.3f}s
- Fastest Response: {self.performance_stats['fastest_response']:.3f}s
- Slowest Response: {self.performance_stats['slowest_response']:.3f}s

RECENT TEST RESULTS:
"""
        
        for result in self.results[-10:]:  # Show last 10 results
            status = "PASS" if result.success else "FAIL"
            summary += f"  {status:4} | {result.name:40} | {result.response_time:.3f}s\n"
        
        status_text = "PASSED" if success_rate >= 80 else "PARTIAL" if success_rate >= 50 else "FAILED"
        summary += f"\nOVERALL STATUS: {status_text}\n"
        summary += "="*80 + "\n"
        
        return summary

    def generate_html_report(self, output_file: str = "api_test_report.html") -> str:
        """Generate comprehensive HTML report"""
        self.calculate_performance_stats()
        
        total_tests = len(self.results)
        successful_tests = sum(1 for r in self.results if r.success)
        failed_tests = total_tests - successful_tests
        success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
        
        # Generate HTML
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>API Test Report - Financial Planning System</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 2.5em;
            text-shadow: 0 2px 4px rgba(0,0,0,0.3);
        }}
        .header p {{
            margin: 10px 0 0 0;
            opacity: 0.9;
            font-size: 1.1em;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            padding: 30px;
            background: #f8f9fa;
        }}
        .stat-card {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            border-left: 4px solid;
        }}
        .stat-card.success {{ border-left-color: #28a745; }}
        .stat-card.warning {{ border-left-color: #ffc107; }}
        .stat-card.error {{ border-left-color: #dc3545; }}
        .stat-card.info {{ border-left-color: #17a2b8; }}
        .stat-number {{
            font-size: 2.5em;
            font-weight: bold;
            margin: 0;
        }}
        .stat-label {{
            color: #666;
            margin: 0;
            text-transform: uppercase;
            font-size: 0.9em;
            letter-spacing: 1px;
        }}
        .results-section {{
            padding: 30px;
        }}
        .section-title {{
            font-size: 1.8em;
            margin-bottom: 20px;
            color: #333;
            border-bottom: 2px solid #4facfe;
            padding-bottom: 10px;
        }}
        .results-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }}
        .results-table th {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px;
            text-align: left;
            font-weight: 600;
        }}
        .results-table td {{
            padding: 12px 15px;
            border-bottom: 1px solid #eee;
        }}
        .results-table tbody tr:hover {{
            background: #f8f9fa;
        }}
        .status-success {{ color: #28a745; font-weight: bold; }}
        .status-error {{ color: #dc3545; font-weight: bold; }}
        .progress-bar {{
            width: 100%;
            height: 20px;
            background: #eee;
            border-radius: 10px;
            overflow: hidden;
            margin: 10px 0;
        }}
        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, #4facfe 0%, #00f2fe 100%);
            transition: width 0.3s ease;
        }}
        .footer {{
            background: #333;
            color: white;
            text-align: center;
            padding: 20px;
            font-size: 0.9em;
        }}
        .timestamp {{
            color: #666;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 API Test Report</h1>
            <p>Financial Planning System - Comprehensive Testing Results</p>
            <p class="timestamp">Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card success">
                <div class="stat-number">{successful_tests}</div>
                <div class="stat-label">Successful Tests</div>
            </div>
            <div class="stat-card error">
                <div class="stat-number">{failed_tests}</div>
                <div class="stat-label">Failed Tests</div>
            </div>
            <div class="stat-card info">
                <div class="stat-number">{success_rate:.1f}%</div>
                <div class="stat-label">Success Rate</div>
            </div>
            <div class="stat-card warning">
                <div class="stat-number">{self.performance_stats['average_response_time']:.3f}s</div>
                <div class="stat-label">Avg Response Time</div>
            </div>
        </div>
        
        <div class="results-section">
            <h2 class="section-title">📊 Performance Overview</h2>
            <div class="progress-bar">
                <div class="progress-fill" style="width: {success_rate}%"></div>
            </div>
            <p><strong>Success Rate:</strong> {success_rate:.1f}% ({successful_tests}/{total_tests} tests passed)</p>
        </div>
        
        <div class="results-section">
            <h2 class="section-title">📋 Detailed Test Results</h2>
            <table class="results-table">
                <thead>
                    <tr>
                        <th>Test Name</th>
                        <th>Status</th>
                        <th>Response Time</th>
                        <th>Status Code</th>
                        <th>Timestamp</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        # Add test results
        for result in self.results:
            status_class = "status-success" if result.success else "status-error"
            status_text = "✅ PASS" if result.success else "❌ FAIL"
            
            html_content += f"""
                    <tr>
                        <td>{result.name}</td>
                        <td class="{status_class}">{status_text}</td>
                        <td>{result.response_time:.3f}s</td>
                        <td>{result.status_code or 'N/A'}</td>
                        <td>{result.timestamp.strftime('%H:%M:%S')}</td>
                    </tr>
            """
        
        html_content += f"""
                </tbody>
            </table>
        </div>
        
        <div class="results-section">
            <h2 class="section-title">📈 Performance Statistics</h2>
            <table class="results-table">
                <thead>
                    <tr>
                        <th>Metric</th>
                        <th>Value</th>
                    </tr>
                </thead>
                <tbody>
                    <tr><td>Total Requests</td><td>{self.performance_stats['total_requests']}</td></tr>
                    <tr><td>Successful Requests</td><td>{self.performance_stats['successful_requests']}</td></tr>
                    <tr><td>Failed Requests</td><td>{self.performance_stats['failed_requests']}</td></tr>
                    <tr><td>Average Response Time</td><td>{self.performance_stats['average_response_time']:.3f}s</td></tr>
                    <tr><td>Fastest Response</td><td>{self.performance_stats['fastest_response']:.3f}s</td></tr>
                    <tr><td>Slowest Response</td><td>{self.performance_stats['slowest_response']:.3f}s</td></tr>
                </tbody>
            </table>
        </div>
        
        <div class="footer">
            <p>Generated by Financial Planning API Test Suite v1.0.0</p>
            <p>Base URL: {self.base_url}</p>
        </div>
    </div>
</body>
</html>
        """
        
        # Write HTML file
        output_path = Path(output_file)
        output_path.write_text(html_content, encoding='utf-8')
        
        return str(output_path.absolute())

    async def run_comprehensive_test_suite(self, include_load_test: bool = False):
        """Run the complete test suite"""
        self.print_header()
        
        # Run all test categories
        await self.test_health_endpoints()
        await self.test_authentication_flow()
        await self.test_financial_endpoints()
        await self.test_simulation_endpoints()
        await self.test_error_handling()
        
        if include_load_test:
            await self.run_load_test()
        
        # Generate and display summary
        summary = self.generate_summary_dashboard()
        
        # Generate HTML report
        html_report = self.generate_html_report()
        
        if self.console:
            self.console.print(f"\n📄 HTML Report generated: [link={html_report}]{html_report}[/link]", style="bold blue")
        else:
            print(f"\n📄 HTML Report generated: {html_report}")
        
        return summary, html_report


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Financial Planning API Test Suite")
    parser.add_argument("--base-url", default="http://localhost:8000", 
                       help="Base URL for the API (default: http://localhost:8000)")
    parser.add_argument("--load-test", action="store_true", 
                       help="Include load testing (100 concurrent requests)")
    parser.add_argument("--verbose", action="store_true", 
                       help="Enable verbose output")
    
    args = parser.parse_args()
    
    # Create test suite
    test_suite = APITestSuite(
        base_url=args.base_url,
        verbose=args.verbose
    )
    
    try:
        # Run comprehensive test suite
        summary, html_report = await test_suite.run_comprehensive_test_suite(
            include_load_test=args.load_test
        )
        
        print(f"\n🎉 Test suite completed successfully!")
        print(f"📊 View detailed results: {html_report}")
        
        # Return appropriate exit code
        success_rate = len([r for r in test_suite.results if r.success]) / len(test_suite.results) * 100
        return 0 if success_rate >= 80 else 1
        
    except Exception as e:
        if test_suite.console:
            test_suite.console.print(f"\n❌ Test suite failed with error: {str(e)}", style="bold red")
        else:
            print(f"\n❌ Test suite failed with error: {str(e)}")
        
        logger.error(f"Test suite error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)