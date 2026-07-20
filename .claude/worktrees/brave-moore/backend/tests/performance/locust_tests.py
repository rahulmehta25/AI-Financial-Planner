"""
Comprehensive Load Testing with Locust

Implements various load testing scenarios:
- User journey simulations
- API endpoint stress testing
- WebSocket connection testing
- Database query load testing
- Concurrent user scenarios
- Performance regression testing
"""

import json
import random
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any
import gevent
from locust import HttpUser, TaskSet, task, between, events, User
from locust.contrib.fasthttp import FastHttpUser
from locust.exception import RescheduleTask
import websocket
import threading

# Performance thresholds for assertions
PERFORMANCE_THRESHOLDS = {
    'login': 500,  # ms
    'portfolio_view': 1000,
    'simulation_run': 5000,
    'goal_creation': 800,
    'market_data': 300,
    'report_generation': 3000
}


class FinancialPlanningUser(FastHttpUser):
    """
    Simulates realistic user behavior on the financial planning platform
    """
    
    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks
    
    def on_start(self):
        """Initialize user session"""
        self.user_id = None
        self.token = None
        self.portfolio_id = None
        self.goals = []
        self.login()
    
    def login(self):
        """Authenticate user"""
        response = self.client.post(
            "/api/v1/auth/login",
            json={
                "email": f"user{random.randint(1, 10000)}@test.com",
                "password": "TestPassword123!"
            },
            catch_response=True
        )
        
        if response.status_code == 200:
            data = response.json()
            self.token = data.get("access_token")
            self.user_id = data.get("user_id")
            self.client.headers.update({"Authorization": f"Bearer {self.token}"})
            response.success()
        else:
            response.failure(f"Login failed: {response.status_code}")
    
    @task(10)
    def view_portfolio(self):
        """View portfolio - most common action"""
        with self.client.get(
            f"/api/v1/portfolio/{self.user_id}",
            catch_response=True,
            name="/api/v1/portfolio/[user_id]"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                self.portfolio_id = data.get("portfolio_id")
                
                # Check performance
                if response.elapsed.total_seconds() * 1000 > PERFORMANCE_THRESHOLDS['portfolio_view']:
                    response.failure(f"Portfolio view too slow: {response.elapsed.total_seconds()*1000:.0f}ms")
                else:
                    response.success()
            else:
                response.failure(f"Portfolio view failed: {response.status_code}")
    
    @task(5)
    def run_simulation(self):
        """Run Monte Carlo simulation"""
        if not self.portfolio_id:
            raise RescheduleTask()
        
        simulation_params = {
            "portfolio_id": self.portfolio_id,
            "years": random.randint(10, 30),
            "simulations": random.choice([1000, 5000, 10000]),
            "monthly_contribution": random.randint(500, 5000),
            "risk_tolerance": random.choice(["conservative", "moderate", "aggressive"])
        }
        
        with self.client.post(
            "/api/v1/simulations/monte-carlo",
            json=simulation_params,
            catch_response=True,
            timeout=10
        ) as response:
            if response.status_code == 200:
                # Check performance
                if response.elapsed.total_seconds() * 1000 > PERFORMANCE_THRESHOLDS['simulation_run']:
                    response.failure(f"Simulation too slow: {response.elapsed.total_seconds()*1000:.0f}ms")
                else:
                    response.success()
            else:
                response.failure(f"Simulation failed: {response.status_code}")
    
    @task(3)
    def create_goal(self):
        """Create a financial goal"""
        goal_data = {
            "name": f"Goal {random.randint(1, 100)}",
            "target_amount": random.randint(10000, 100000),
            "target_date": (datetime.now() + timedelta(days=random.randint(365, 3650))).isoformat(),
            "category": random.choice(["retirement", "education", "house", "vacation", "emergency"]),
            "priority": random.randint(1, 5)
        }
        
        with self.client.post(
            "/api/v1/goals",
            json=goal_data,
            catch_response=True
        ) as response:
            if response.status_code == 201:
                goal = response.json()
                self.goals.append(goal.get("id"))
                
                # Check performance
                if response.elapsed.total_seconds() * 1000 > PERFORMANCE_THRESHOLDS['goal_creation']:
                    response.failure(f"Goal creation too slow: {response.elapsed.total_seconds()*1000:.0f}ms")
                else:
                    response.success()
            else:
                response.failure(f"Goal creation failed: {response.status_code}")
    
    @task(8)
    def get_market_data(self):
        """Fetch market data"""
        symbols = ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA", "SPY", "QQQ", "VTI"]
        symbol = random.choice(symbols)
        
        with self.client.get(
            f"/api/v1/market-data/{symbol}",
            catch_response=True,
            name="/api/v1/market-data/[symbol]"
        ) as response:
            if response.status_code == 200:
                # Check performance
                if response.elapsed.total_seconds() * 1000 > PERFORMANCE_THRESHOLDS['market_data']:
                    response.failure(f"Market data fetch too slow: {response.elapsed.total_seconds()*1000:.0f}ms")
                else:
                    response.success()
            else:
                response.failure(f"Market data fetch failed: {response.status_code}")
    
    @task(2)
    def generate_report(self):
        """Generate PDF report"""
        if not self.portfolio_id:
            raise RescheduleTask()
        
        with self.client.post(
            "/api/v1/reports/generate",
            json={
                "portfolio_id": self.portfolio_id,
                "report_type": random.choice(["summary", "detailed", "tax"]),
                "period": random.choice(["monthly", "quarterly", "annual"])
            },
            catch_response=True,
            timeout=10
        ) as response:
            if response.status_code == 200:
                # Check performance
                if response.elapsed.total_seconds() * 1000 > PERFORMANCE_THRESHOLDS['report_generation']:
                    response.failure(f"Report generation too slow: {response.elapsed.total_seconds()*1000:.0f}ms")
                else:
                    response.success()
            else:
                response.failure(f"Report generation failed: {response.status_code}")
    
    @task(1)
    def update_profile(self):
        """Update user profile"""
        profile_data = {
            "annual_income": random.randint(50000, 500000),
            "net_worth": random.randint(100000, 5000000),
            "risk_tolerance": random.choice(["conservative", "moderate", "aggressive"]),
            "investment_horizon": random.randint(5, 30)
        }
        
        with self.client.put(
            f"/api/v1/profile/{self.user_id}",
            json=profile_data,
            catch_response=True,
            name="/api/v1/profile/[user_id]"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Profile update failed: {response.status_code}")


class WebSocketUser(User):
    """
    Tests WebSocket connections for real-time features
    """
    
    wait_time = between(1, 2)
    
    def on_start(self):
        """Initialize WebSocket connection"""
        self.ws = None
        self.connect_websocket()
    
    def connect_websocket(self):
        """Establish WebSocket connection"""
        try:
            self.ws = websocket.WebSocketApp(
                "ws://localhost:8000/ws",
                on_open=self.on_open,
                on_message=self.on_message,
                on_error=self.on_error,
                on_close=self.on_close
            )
            
            # Run WebSocket in separate thread
            self.ws_thread = threading.Thread(target=self.ws.run_forever)
            self.ws_thread.daemon = True
            self.ws_thread.start()
            
            events.request_success.fire(
                request_type="WebSocket",
                name="connect",
                response_time=100,
                response_length=0
            )
        except Exception as e:
            events.request_failure.fire(
                request_type="WebSocket",
                name="connect",
                response_time=0,
                response_length=0,
                exception=e
            )
    
    def on_open(self, ws):
        """WebSocket opened"""
        # Subscribe to market data
        ws.send(json.dumps({
            "action": "subscribe",
            "channels": ["market_data", "portfolio_updates"]
        }))
    
    def on_message(self, ws, message):
        """Handle WebSocket message"""
        try:
            data = json.loads(message)
            events.request_success.fire(
                request_type="WebSocket",
                name=f"message_{data.get('type', 'unknown')}",
                response_time=10,
                response_length=len(message)
            )
        except Exception as e:
            events.request_failure.fire(
                request_type="WebSocket",
                name="message_parse",
                response_time=0,
                response_length=0,
                exception=e
            )
    
    def on_error(self, ws, error):
        """Handle WebSocket error"""
        events.request_failure.fire(
            request_type="WebSocket",
            name="error",
            response_time=0,
            response_length=0,
            exception=error
        )
    
    def on_close(self, ws):
        """WebSocket closed"""
        pass
    
    @task
    def send_message(self):
        """Send message through WebSocket"""
        if self.ws and self.ws.sock and self.ws.sock.connected:
            message = json.dumps({
                "action": "ping",
                "timestamp": time.time()
            })
            
            start_time = time.time()
            try:
                self.ws.send(message)
                response_time = (time.time() - start_time) * 1000
                
                events.request_success.fire(
                    request_type="WebSocket",
                    name="send_message",
                    response_time=response_time,
                    response_length=len(message)
                )
            except Exception as e:
                events.request_failure.fire(
                    request_type="WebSocket",
                    name="send_message",
                    response_time=0,
                    response_length=0,
                    exception=e
                )
    
    def on_stop(self):
        """Clean up WebSocket connection"""
        if self.ws:
            self.ws.close()


class DatabaseStressTest(FastHttpUser):
    """
    Stress test database-heavy operations
    """
    
    wait_time = between(0.5, 1.5)
    
    @task(10)
    def complex_aggregation(self):
        """Test complex database aggregation"""
        with self.client.get(
            "/api/v1/analytics/portfolio-performance",
            params={
                "start_date": "2020-01-01",
                "end_date": "2024-12-31",
                "grouping": "monthly",
                "metrics": "all"
            },
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Aggregation failed: {response.status_code}")
    
    @task(5)
    def bulk_insert(self):
        """Test bulk data insertion"""
        transactions = [
            {
                "date": (datetime.now() - timedelta(days=random.randint(1, 365))).isoformat(),
                "amount": random.uniform(100, 10000),
                "category": random.choice(["income", "expense", "investment"]),
                "description": f"Transaction {i}"
            }
            for i in range(100)
        ]
        
        with self.client.post(
            "/api/v1/transactions/bulk",
            json={"transactions": transactions},
            catch_response=True,
            timeout=5
        ) as response:
            if response.status_code == 201:
                response.success()
            else:
                response.failure(f"Bulk insert failed: {response.status_code}")
    
    @task(8)
    def search_operations(self):
        """Test search functionality"""
        search_terms = ["retirement", "investment", "savings", "goal", "portfolio"]
        
        with self.client.get(
            "/api/v1/search",
            params={
                "q": random.choice(search_terms),
                "limit": 50,
                "offset": 0
            },
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Search failed: {response.status_code}")


class SpikeTestUser(FastHttpUser):
    """
    Simulates sudden spike in traffic
    """
    
    wait_time = between(0.1, 0.5)  # Very aggressive
    
    @task
    def hammer_endpoint(self):
        """Hit endpoint aggressively"""
        endpoints = [
            "/api/v1/health",
            "/api/v1/market-data/SPY",
            "/api/v1/portfolio/summary",
            "/api/v1/goals/active"
        ]
        
        endpoint = random.choice(endpoints)
        
        with self.client.get(
            endpoint,
            catch_response=True,
            timeout=2
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 429:  # Rate limited
                response.failure("Rate limited")
            else:
                response.failure(f"Request failed: {response.status_code}")


# Custom event handlers for reporting
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Initialize test metrics"""
    print(f"Load test starting with {environment.parsed_options.num_users} users")
    print(f"Spawn rate: {environment.parsed_options.spawn_rate} users/second")
    print(f"Host: {environment.parsed_options.host}")


@events.request_success.add_listener
def on_request_success(request_type, name, response_time, response_length, **kwargs):
    """Track successful requests"""
    # Check against thresholds
    for endpoint, threshold in PERFORMANCE_THRESHOLDS.items():
        if endpoint in name and response_time > threshold:
            print(f"⚠️  Performance degradation: {name} took {response_time:.0f}ms (threshold: {threshold}ms)")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Generate test report"""
    print("\n" + "="*50)
    print("LOAD TEST SUMMARY")
    print("="*50)
    
    stats = environment.stats
    
    print(f"\nTotal Requests: {stats.total.num_requests}")
    print(f"Total Failures: {stats.total.num_failures}")
    print(f"Failure Rate: {stats.total.fail_ratio*100:.2f}%")
    print(f"Average Response Time: {stats.total.avg_response_time:.0f}ms")
    print(f"Median Response Time: {stats.total.median_response_time:.0f}ms")
    print(f"95th Percentile: {stats.total.get_response_time_percentile(0.95):.0f}ms")
    print(f"99th Percentile: {stats.total.get_response_time_percentile(0.99):.0f}ms")
    
    # Performance assertions
    print("\n" + "-"*50)
    print("PERFORMANCE ASSERTIONS")
    print("-"*50)
    
    assertions_passed = True
    
    for endpoint, threshold in PERFORMANCE_THRESHOLDS.items():
        endpoint_stats = None
        for stat in stats.entries.values():
            if endpoint in stat.name:
                endpoint_stats = stat
                break
        
        if endpoint_stats:
            avg_time = endpoint_stats.avg_response_time
            passed = avg_time <= threshold
            status = "✓" if passed else "✗"
            print(f"{status} {endpoint}: {avg_time:.0f}ms (threshold: {threshold}ms)")
            
            if not passed:
                assertions_passed = False
    
    # Overall verdict
    print("\n" + "="*50)
    if assertions_passed and stats.total.fail_ratio < 0.01:  # < 1% failure rate
        print("✓ LOAD TEST PASSED")
    else:
        print("✗ LOAD TEST FAILED")
    print("="*50)


# Locust configuration for different test scenarios
class StressTestScenario(FastHttpUser):
    """Combined stress test scenario"""
    tasks = [FinancialPlanningUser, DatabaseStressTest]
    wait_time = between(1, 2)


class EnduranceTestScenario(FastHttpUser):
    """Long-running endurance test"""
    tasks = [FinancialPlanningUser]
    wait_time = between(2, 5)


# Custom CLI commands for specific test scenarios
if __name__ == "__main__":
    import sys
    from locust import main
    
    # Default configuration
    sys.argv.extend([
        "--host", "http://localhost:8000",
        "--users", "100",
        "--spawn-rate", "10",
        "--time", "5m",
        "--html", "load_test_report.html",
        "--csv", "load_test_metrics"
    ])
    
    main.main()