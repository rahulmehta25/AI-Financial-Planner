"""
Comprehensive Load Testing Scenarios

Realistic user behavior patterns for the financial planning system
"""

import random
import time
import json
import websocket
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from locust import HttpUser, task, between, events, TaskSet
from locust.exception import RescheduleTask
import gevent
from gevent.pool import Pool


class UserBehaviorMixin:
    """Common user behavior patterns"""
    
    def login(self) -> bool:
        """Authenticate user and store token"""
        with self.client.post(
            "/api/v1/auth/login",
            json={
                "email": self.test_email,
                "password": self.test_password
            },
            catch_response=True,
            name="AUTH: Login"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                self.user_id = data.get("user_id")
                self.headers = {"Authorization": f"Bearer {self.token}"}
                response.success()
                return True
            else:
                response.failure(f"Login failed: {response.status_code}")
                return False
    
    def check_response_time(self, response, threshold_ms: int, name: str):
        """Check if response time meets SLA"""
        response_time_ms = response.elapsed.total_seconds() * 1000
        if response_time_ms > threshold_ms:
            response.failure(f"{name} exceeded SLA: {response_time_ms:.0f}ms > {threshold_ms}ms")
        else:
            response.success()
    
    def simulate_think_time(self, min_seconds: float = 0.5, max_seconds: float = 2.0):
        """Simulate user think time between actions"""
        time.sleep(random.uniform(min_seconds, max_seconds))


class OnboardingScenario(TaskSet, UserBehaviorMixin):
    """New user onboarding flow"""
    
    def on_start(self):
        """Initialize onboarding scenario"""
        self.email = f"newuser_{random.randint(100000, 999999)}@test.com"
        self.user_data = None
    
    @task(1)
    def register_user(self):
        """Step 1: User registration"""
        with self.client.post(
            "/api/v1/auth/register",
            json={
                "email": self.email,
                "password": "Test@Password123",
                "first_name": "Test",
                "last_name": "User",
                "date_of_birth": "1990-01-01"
            },
            catch_response=True,
            name="ONBOARDING: Register"
        ) as response:
            if response.status_code in [200, 201]:
                self.user_data = response.json()
                self.check_response_time(response, 1000, "Registration")
            else:
                response.failure(f"Registration failed: {response.status_code}")
                raise RescheduleTask()
    
    @task(2)
    def complete_profile(self):
        """Step 2: Complete financial profile"""
        if not self.user_data:
            raise RescheduleTask()
        
        with self.client.post(
            "/api/v1/profile/financial",
            json={
                "annual_income": random.randint(50000, 200000),
                "net_worth": random.randint(10000, 500000),
                "risk_tolerance": random.choice(["conservative", "moderate", "aggressive"]),
                "investment_experience": random.choice(["beginner", "intermediate", "advanced"]),
                "retirement_age": random.randint(60, 70),
                "monthly_expenses": random.randint(3000, 10000)
            },
            headers={"Authorization": f"Bearer {self.user_data.get('access_token')}"},
            catch_response=True,
            name="ONBOARDING: Complete Profile"
        ) as response:
            self.check_response_time(response, 2000, "Profile completion")
    
    @task(3)
    def set_initial_goals(self):
        """Step 3: Set initial financial goals"""
        if not self.user_data:
            raise RescheduleTask()
        
        goals = [
            {
                "name": "Emergency Fund",
                "target_amount": random.randint(10000, 30000),
                "target_date": (datetime.now() + timedelta(days=365)).isoformat(),
                "category": "emergency_fund",
                "priority": "high"
            },
            {
                "name": "Retirement",
                "target_amount": random.randint(500000, 2000000),
                "target_date": (datetime.now() + timedelta(days=365*30)).isoformat(),
                "category": "retirement",
                "priority": "high"
            }
        ]
        
        for goal in goals:
            with self.client.post(
                "/api/v1/goals",
                json=goal,
                headers={"Authorization": f"Bearer {self.user_data.get('access_token')}"},
                catch_response=True,
                name="ONBOARDING: Create Goal"
            ) as response:
                self.check_response_time(response, 1000, "Goal creation")
            
            self.simulate_think_time(0.5, 1.5)
    
    @task(1)
    def connect_bank_account(self):
        """Step 4: Connect bank account (simulated)"""
        if not self.user_data:
            raise RescheduleTask()
        
        with self.client.post(
            "/api/v1/banking/connect",
            json={
                "provider": "plaid",
                "public_token": "test_public_token_" + str(random.randint(1000, 9999))
            },
            headers={"Authorization": f"Bearer {self.user_data.get('access_token')}"},
            catch_response=True,
            name="ONBOARDING: Connect Bank"
        ) as response:
            self.check_response_time(response, 5000, "Bank connection")
    
    @task(1)
    def initial_portfolio_setup(self):
        """Step 5: Initial portfolio allocation"""
        if not self.user_data:
            raise RescheduleTask()
        
        with self.client.post(
            "/api/v1/portfolio/initialize",
            json={
                "initial_investment": random.randint(1000, 50000),
                "monthly_contribution": random.randint(100, 2000),
                "allocation": {
                    "stocks": random.randint(30, 70),
                    "bonds": random.randint(20, 50),
                    "cash": random.randint(5, 20)
                }
            },
            headers={"Authorization": f"Bearer {self.user_data.get('access_token')}"},
            catch_response=True,
            name="ONBOARDING: Portfolio Setup"
        ) as response:
            self.check_response_time(response, 3000, "Portfolio setup")
    
    @task(1)
    def stop(self):
        """Complete onboarding and switch to regular user behavior"""
        self.interrupt()


class MonteCarloSimulationScenario(TaskSet, UserBehaviorMixin):
    """Monte Carlo simulation stress testing"""
    
    @task(3)
    def run_basic_simulation(self):
        """Run basic Monte Carlo simulation"""
        with self.client.post(
            "/api/v1/simulations/monte-carlo",
            json={
                "initial_investment": random.randint(10000, 100000),
                "monthly_contribution": random.randint(500, 5000),
                "years": random.randint(10, 30),
                "num_simulations": 1000,
                "risk_profile": random.choice(["conservative", "moderate", "aggressive"]),
                "inflation_rate": random.uniform(0.02, 0.04)
            },
            headers=self.parent.headers,
            catch_response=True,
            timeout=60,
            name="SIMULATION: Basic Monte Carlo"
        ) as response:
            self.check_response_time(response, 30000, "Basic simulation")
    
    @task(2)
    def run_complex_simulation(self):
        """Run complex Monte Carlo simulation with multiple goals"""
        with self.client.post(
            "/api/v1/simulations/monte-carlo/complex",
            json={
                "scenarios": [
                    {
                        "name": "Base Case",
                        "initial_investment": random.randint(50000, 200000),
                        "monthly_contribution": random.randint(1000, 10000),
                        "years": 30,
                        "num_simulations": 5000
                    },
                    {
                        "name": "Aggressive",
                        "initial_investment": random.randint(50000, 200000),
                        "monthly_contribution": random.randint(2000, 15000),
                        "years": 25,
                        "num_simulations": 5000
                    }
                ],
                "goals": [
                    {"name": "Retirement", "amount": 2000000, "year": 30},
                    {"name": "College", "amount": 200000, "year": 18}
                ],
                "market_scenarios": ["bull", "bear", "normal"],
                "confidence_levels": [0.50, 0.75, 0.90, 0.95]
            },
            headers=self.parent.headers,
            catch_response=True,
            timeout=120,
            name="SIMULATION: Complex Monte Carlo"
        ) as response:
            self.check_response_time(response, 60000, "Complex simulation")
    
    @task(1)
    def run_stress_test_simulation(self):
        """Run stress test with maximum parameters"""
        with self.client.post(
            "/api/v1/simulations/monte-carlo/stress",
            json={
                "initial_investment": 1000000,
                "monthly_contribution": 20000,
                "years": 50,
                "num_simulations": 10000,  # Maximum simulations
                "include_taxes": True,
                "include_social_security": True,
                "include_inflation": True,
                "detailed_output": True
            },
            headers=self.parent.headers,
            catch_response=True,
            timeout=180,
            name="SIMULATION: Stress Test"
        ) as response:
            self.check_response_time(response, 120000, "Stress test simulation")
    
    @task(1)
    def get_simulation_results(self):
        """Retrieve previous simulation results"""
        with self.client.get(
            f"/api/v1/simulations/results/latest",
            headers=self.parent.headers,
            catch_response=True,
            name="SIMULATION: Get Results"
        ) as response:
            self.check_response_time(response, 500, "Get simulation results")


class PortfolioManagementScenario(TaskSet, UserBehaviorMixin):
    """Portfolio viewing and management tasks"""
    
    @task(5)
    def view_portfolio_summary(self):
        """View portfolio summary dashboard"""
        with self.client.get(
            f"/api/v1/portfolio/summary",
            headers=self.parent.headers,
            catch_response=True,
            name="PORTFOLIO: View Summary"
        ) as response:
            self.check_response_time(response, 500, "Portfolio summary")
    
    @task(3)
    def view_portfolio_details(self):
        """View detailed portfolio holdings"""
        with self.client.get(
            f"/api/v1/portfolio/holdings",
            headers=self.parent.headers,
            catch_response=True,
            name="PORTFOLIO: View Holdings"
        ) as response:
            self.check_response_time(response, 1000, "Portfolio holdings")
    
    @task(2)
    def calculate_performance(self):
        """Calculate portfolio performance metrics"""
        with self.client.get(
            f"/api/v1/portfolio/performance?period=1Y",
            headers=self.parent.headers,
            catch_response=True,
            name="PORTFOLIO: Calculate Performance"
        ) as response:
            self.check_response_time(response, 2000, "Performance calculation")
    
    @task(2)
    def rebalance_portfolio(self):
        """Rebalance portfolio allocation"""
        with self.client.post(
            "/api/v1/portfolio/rebalance",
            json={
                "target_allocation": {
                    "stocks": random.randint(40, 70),
                    "bonds": random.randint(20, 40),
                    "real_estate": random.randint(5, 15),
                    "cash": random.randint(5, 10)
                },
                "rebalance_threshold": 5  # 5% threshold
            },
            headers=self.parent.headers,
            catch_response=True,
            name="PORTFOLIO: Rebalance"
        ) as response:
            self.check_response_time(response, 3000, "Portfolio rebalance")
    
    @task(1)
    def analyze_risk(self):
        """Analyze portfolio risk metrics"""
        with self.client.get(
            "/api/v1/portfolio/risk-analysis",
            headers=self.parent.headers,
            catch_response=True,
            name="PORTFOLIO: Risk Analysis"
        ) as response:
            self.check_response_time(response, 5000, "Risk analysis")


class MarketDataStreamingScenario(TaskSet, UserBehaviorMixin):
    """Market data and WebSocket streaming"""
    
    def on_start(self):
        """Initialize WebSocket connection"""
        self.ws = None
        self.ws_connected = False
        self.symbols = random.sample(
            ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA", "META", "NVDA", "JPM"],
            k=random.randint(3, 6)
        )
    
    @task(3)
    def fetch_market_data(self):
        """Fetch current market data"""
        with self.client.get(
            f"/api/v1/market-data?symbols={','.join(self.symbols)}",
            headers=self.parent.headers,
            catch_response=True,
            name="MARKET: Fetch Data"
        ) as response:
            self.check_response_time(response, 300, "Market data fetch")
    
    @task(2)
    def fetch_historical_data(self):
        """Fetch historical market data"""
        symbol = random.choice(self.symbols)
        with self.client.get(
            f"/api/v1/market-data/historical/{symbol}?period=1Y",
            headers=self.parent.headers,
            catch_response=True,
            name="MARKET: Historical Data"
        ) as response:
            self.check_response_time(response, 1000, "Historical data")
    
    @task(1)
    def connect_websocket(self):
        """Connect to market data WebSocket stream"""
        if not self.ws_connected:
            try:
                # Simulate WebSocket connection
                ws_url = self.parent.host.replace("http", "ws") + "/ws/market-data"
                
                # Note: This is a simulation. Real WebSocket testing would require
                # a different approach with actual WebSocket client
                with self.client.get(
                    "/api/v1/market-data/stream/init",
                    headers=self.parent.headers,
                    catch_response=True,
                    name="MARKET: WebSocket Init"
                ) as response:
                    if response.status_code == 200:
                        self.ws_connected = True
                        response.success()
                        
                        # Simulate subscribing to symbols
                        self.client.post(
                            "/api/v1/market-data/stream/subscribe",
                            json={"symbols": self.symbols},
                            headers=self.parent.headers,
                            name="MARKET: Subscribe Symbols"
                        )
            except Exception as e:
                print(f"WebSocket connection failed: {e}")
    
    @task(2)
    def stream_market_updates(self):
        """Simulate receiving market updates"""
        if self.ws_connected:
            # Simulate polling for updates
            with self.client.get(
                "/api/v1/market-data/stream/updates",
                headers=self.parent.headers,
                catch_response=True,
                name="MARKET: Stream Updates"
            ) as response:
                self.check_response_time(response, 100, "Market updates")
    
    def on_stop(self):
        """Close WebSocket connection"""
        if self.ws_connected:
            self.client.post(
                "/api/v1/market-data/stream/disconnect",
                headers=self.parent.headers,
                name="MARKET: Disconnect"
            )
            self.ws_connected = False


class ReportGenerationScenario(TaskSet, UserBehaviorMixin):
    """PDF report generation scenarios"""
    
    @task(3)
    def generate_basic_report(self):
        """Generate basic financial report"""
        with self.client.post(
            "/api/v1/reports/generate",
            json={
                "report_type": "summary",
                "format": "pdf",
                "period": "YTD"
            },
            headers=self.parent.headers,
            catch_response=True,
            timeout=120,
            name="REPORT: Basic PDF"
        ) as response:
            self.check_response_time(response, 30000, "Basic report")
    
    @task(2)
    def generate_comprehensive_report(self):
        """Generate comprehensive financial plan"""
        with self.client.post(
            "/api/v1/reports/generate",
            json={
                "report_type": "comprehensive",
                "format": "pdf",
                "include_sections": [
                    "executive_summary",
                    "portfolio_analysis",
                    "goal_progress",
                    "risk_assessment",
                    "tax_analysis",
                    "recommendations",
                    "monte_carlo_results",
                    "transaction_history"
                ],
                "period": "ALL"
            },
            headers=self.parent.headers,
            catch_response=True,
            timeout=180,
            name="REPORT: Comprehensive PDF"
        ) as response:
            self.check_response_time(response, 60000, "Comprehensive report")
    
    @task(1)
    def generate_tax_report(self):
        """Generate tax report"""
        with self.client.post(
            "/api/v1/reports/generate",
            json={
                "report_type": "tax",
                "format": "pdf",
                "tax_year": datetime.now().year - 1
            },
            headers=self.parent.headers,
            catch_response=True,
            timeout=90,
            name="REPORT: Tax Report"
        ) as response:
            self.check_response_time(response, 45000, "Tax report")
    
    @task(2)
    def check_report_status(self):
        """Check async report generation status"""
        with self.client.get(
            "/api/v1/reports/status/latest",
            headers=self.parent.headers,
            catch_response=True,
            name="REPORT: Check Status"
        ) as response:
            self.check_response_time(response, 200, "Report status")
    
    @task(1)
    def download_report(self):
        """Download generated report"""
        with self.client.get(
            "/api/v1/reports/download/latest",
            headers=self.parent.headers,
            catch_response=True,
            name="REPORT: Download"
        ) as response:
            self.check_response_time(response, 5000, "Report download")


class BankingSyncScenario(TaskSet, UserBehaviorMixin):
    """Banking integration and transaction sync"""
    
    @task(3)
    def sync_accounts(self):
        """Sync bank accounts"""
        with self.client.post(
            "/api/v1/banking/sync",
            json={"full_sync": False},
            headers=self.parent.headers,
            catch_response=True,
            timeout=30,
            name="BANKING: Sync Accounts"
        ) as response:
            self.check_response_time(response, 15000, "Account sync")
    
    @task(4)
    def fetch_transactions(self):
        """Fetch recent transactions"""
        with self.client.get(
            "/api/v1/banking/transactions?limit=50",
            headers=self.parent.headers,
            catch_response=True,
            name="BANKING: Fetch Transactions"
        ) as response:
            self.check_response_time(response, 2000, "Transaction fetch")
    
    @task(2)
    def categorize_transactions(self):
        """Auto-categorize transactions"""
        with self.client.post(
            "/api/v1/banking/transactions/categorize",
            json={
                "transaction_ids": [f"txn_{i}" for i in range(10)],
                "auto_categorize": True
            },
            headers=self.parent.headers,
            catch_response=True,
            name="BANKING: Categorize"
        ) as response:
            self.check_response_time(response, 3000, "Transaction categorization")
    
    @task(2)
    def analyze_spending(self):
        """Analyze spending patterns"""
        with self.client.get(
            "/api/v1/banking/analytics/spending?period=3M",
            headers=self.parent.headers,
            catch_response=True,
            name="BANKING: Spending Analysis"
        ) as response:
            self.check_response_time(response, 5000, "Spending analysis")
    
    @task(1)
    def detect_anomalies(self):
        """Detect transaction anomalies"""
        with self.client.post(
            "/api/v1/banking/analytics/anomalies",
            json={"sensitivity": "medium"},
            headers=self.parent.headers,
            catch_response=True,
            name="BANKING: Anomaly Detection"
        ) as response:
            self.check_response_time(response, 10000, "Anomaly detection")


class GoalManagementScenario(TaskSet, UserBehaviorMixin):
    """Financial goal management"""
    
    @task(4)
    def view_goals(self):
        """View all financial goals"""
        with self.client.get(
            "/api/v1/goals",
            headers=self.parent.headers,
            catch_response=True,
            name="GOALS: View All"
        ) as response:
            self.check_response_time(response, 500, "View goals")
    
    @task(2)
    def create_goal(self):
        """Create new financial goal"""
        goal_types = ["retirement", "house", "education", "vacation", "emergency"]
        with self.client.post(
            "/api/v1/goals",
            json={
                "name": f"Goal_{random.randint(1000, 9999)}",
                "category": random.choice(goal_types),
                "target_amount": random.randint(10000, 100000),
                "target_date": (datetime.now() + timedelta(days=random.randint(365, 3650))).isoformat(),
                "monthly_contribution": random.randint(100, 2000),
                "priority": random.choice(["low", "medium", "high"])
            },
            headers=self.parent.headers,
            catch_response=True,
            name="GOALS: Create"
        ) as response:
            self.check_response_time(response, 1000, "Create goal")
    
    @task(3)
    def track_progress(self):
        """Track goal progress"""
        with self.client.get(
            "/api/v1/goals/progress",
            headers=self.parent.headers,
            catch_response=True,
            name="GOALS: Track Progress"
        ) as response:
            self.check_response_time(response, 1500, "Goal progress")
    
    @task(2)
    def optimize_goals(self):
        """Optimize goal allocation"""
        with self.client.post(
            "/api/v1/goals/optimize",
            json={
                "optimization_strategy": "maximize_probability",
                "constraints": {
                    "min_emergency_fund": 10000,
                    "max_risk": 0.7
                }
            },
            headers=self.parent.headers,
            catch_response=True,
            name="GOALS: Optimize"
        ) as response:
            self.check_response_time(response, 5000, "Goal optimization")
    
    @task(1)
    def simulate_goal_scenarios(self):
        """Simulate different goal scenarios"""
        with self.client.post(
            "/api/v1/goals/simulate",
            json={
                "scenarios": [
                    {"monthly_contribution": 500, "return_rate": 0.07},
                    {"monthly_contribution": 1000, "return_rate": 0.08},
                    {"monthly_contribution": 1500, "return_rate": 0.06}
                ],
                "years": 10
            },
            headers=self.parent.headers,
            catch_response=True,
            name="GOALS: Simulate Scenarios"
        ) as response:
            self.check_response_time(response, 10000, "Goal simulation")


class FinancialPlanningUser(HttpUser):
    """Main user class that combines all scenarios"""
    
    wait_time = between(1, 3)
    tasks = {
        PortfolioManagementScenario: 30,
        MonteCarloSimulationScenario: 20,
        GoalManagementScenario: 20,
        MarketDataStreamingScenario: 15,
        BankingSyncScenario: 10,
        ReportGenerationScenario: 5
    }
    
    def on_start(self):
        """Initialize user session"""
        # Load test credentials
        try:
            with open("./test_data/test_credentials.json", "r") as f:
                credentials = json.load(f)
                cred = random.choice(credentials)
                self.test_email = cred["email"]
                self.test_password = cred["password"]
        except:
            # Fallback to generated credentials
            self.test_email = f"test_user_{random.randint(1, 1000)}@example.com"
            self.test_password = "Test@Password123"
        
        # Login
        self.login()
    
    def login(self):
        """Authenticate user"""
        with self.client.post(
            "/api/v1/auth/login",
            json={
                "email": self.test_email,
                "password": self.test_password
            },
            catch_response=True,
            name="AUTH: Login"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                self.user_id = data.get("user_id")
                self.headers = {"Authorization": f"Bearer {self.token}"}
                response.success()
            else:
                response.failure(f"Login failed: {response.status_code}")
                self.token = None
                self.headers = {}
    
    def on_stop(self):
        """Cleanup on user stop"""
        if hasattr(self, 'token') and self.token:
            self.client.post(
                "/api/v1/auth/logout",
                headers=self.headers,
                name="AUTH: Logout"
            )


class NewUserFlow(HttpUser):
    """Simulates new user onboarding flow"""
    
    wait_time = between(2, 5)
    tasks = [OnboardingScenario]
    
    def on_start(self):
        """Start onboarding flow"""
        pass


# Event handlers for monitoring
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Initialize test monitoring"""
    print("Load test started")
    print(f"Target host: {environment.host}")
    print(f"Users: {environment.parsed_options.num_users}")
    print(f"Spawn rate: {environment.parsed_options.spawn_rate}")


@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, **kwargs):
    """Monitor individual requests"""
    if exception:
        print(f"Request failed: {name} - {exception}")
    elif response_time > 5000:  # Log slow requests
        print(f"Slow request: {name} - {response_time}ms")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Generate test summary"""
    print("\nLoad test completed")
    print("Generating performance report...")
    
    # Calculate statistics
    stats = environment.stats
    
    if stats.total.num_requests > 0:
        print(f"\nResults Summary:")
        print(f"  Total Requests: {stats.total.num_requests}")
        print(f"  Failed Requests: {stats.total.num_failures}")
        print(f"  Success Rate: {(1 - stats.total.fail_ratio) * 100:.2f}%")
        print(f"  Average Response Time: {stats.total.avg_response_time:.0f}ms")
        print(f"  Median Response Time: {stats.total.median_response_time:.0f}ms")
        print(f"  Min Response Time: {stats.total.min_response_time:.0f}ms")
        print(f"  Max Response Time: {stats.total.max_response_time:.0f}ms")
        print(f"  RPS: {stats.total.current_rps:.2f}")
        
        # Check SLAs
        print(f"\nSLA Validation:")
        p95_pass = stats.total.get_response_time_percentile(0.95) < 500
        p99_pass = stats.total.get_response_time_percentile(0.99) < 1000
        error_pass = stats.total.fail_ratio < 0.01
        
        print(f"  P95 < 500ms: {'PASS' if p95_pass else 'FAIL'} ({stats.total.get_response_time_percentile(0.95):.0f}ms)")
        print(f"  P99 < 1000ms: {'PASS' if p99_pass else 'FAIL'} ({stats.total.get_response_time_percentile(0.99):.0f}ms)")
        print(f"  Error Rate < 1%: {'PASS' if error_pass else 'FAIL'} ({stats.total.fail_ratio * 100:.2f}%)")
        
        overall_pass = p95_pass and p99_pass and error_pass
        print(f"\nOverall Result: {'PASS' if overall_pass else 'FAIL'}")