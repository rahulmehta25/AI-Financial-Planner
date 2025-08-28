"""
Comprehensive Locust performance testing suite for Financial Planning API

Load test scenarios:
- User registration and authentication flow
- Financial profile creation and updates
- Portfolio optimization under load
- Monte Carlo simulations at scale
- Concurrent goal management
- API endpoint stress testing
- Database performance under load

Usage:
    # Basic load test
    locust -f locust_financial_planning.py --host=http://localhost:8000
    
    # Headless load test
    locust -f locust_financial_planning.py --host=http://localhost:8000 \
           --users=50 --spawn-rate=5 --run-time=300s --headless
    
    # Stress test
    locust -f locust_financial_planning.py --host=http://localhost:8000 \
           --users=200 --spawn-rate=10 --run-time=600s --headless
"""

import json
import random
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from locust import HttpUser, task, between, events
from locust.contrib.fasthttp import FastHttpUser
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FinancialPlanningUser(FastHttpUser):
    """
    Base user class for financial planning API testing
    Simulates realistic user behavior patterns
    """
    
    # User behavior: think time between requests
    wait_time = between(1, 3)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_data = {}
        self.access_token = None
        self.financial_profile_id = None
        self.goal_ids = []
        self.portfolio_weights = None
    
    def on_start(self):
        """Called when user starts - register and login"""
        self.register_user()
        self.login_user()
        
    def on_stop(self):
        """Called when user stops"""
        if self.access_token:
            self.logout_user()
    
    def register_user(self):
        """Register a new user"""
        user_id = random.randint(10000, 99999)
        self.user_data = {
            "email": f"loadtest{user_id}@example.com",
            "password": "LoadTestPassword123!",
            "first_name": f"LoadTest",
            "last_name": f"User{user_id}",
            "phone_number": f"+1-555-{random.randint(100, 999)}-{random.randint(1000, 9999)}",
            "date_of_birth": "1985-06-15"
        }
        
        with self.client.post(
            "/api/v1/auth/register",
            json=self.user_data,
            catch_response=True,
            name="register_user"
        ) as response:
            if response.status_code == 201:
                response.success()
            elif response.status_code == 400:  # User already exists
                response.success()  # Treat as success for load testing
            else:
                response.failure(f"Registration failed: {response.status_code}")
    
    def login_user(self):
        """Login user and get access token"""
        login_data = {
            "username": self.user_data["email"],
            "password": self.user_data["password"]
        }
        
        with self.client.post(
            "/api/v1/auth/login",
            data=login_data,
            catch_response=True,
            name="login_user"
        ) as response:
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data["access_token"]
                response.success()
            else:
                response.failure(f"Login failed: {response.status_code}")
    
    def logout_user(self):
        """Logout user"""
        if self.access_token:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            with self.client.post(
                "/api/v1/auth/logout",
                headers=headers,
                catch_response=True,
                name="logout_user"
            ) as response:
                if response.status_code in [200, 401]:  # 401 is ok if token expired
                    response.success()
                else:
                    response.failure(f"Logout failed: {response.status_code}")
    
    def get_auth_headers(self) -> Dict[str, str]:
        """Get authorization headers"""
        if self.access_token:
            return {"Authorization": f"Bearer {self.access_token}"}
        return {}
    
    @task(10)
    def create_financial_profile(self):
        """Create or update financial profile"""
        if not self.access_token:
            return
        
        profile_data = {
            "annual_income": random.uniform(40000, 200000),
            "monthly_expenses": random.uniform(2000, 8000),
            "current_savings": random.uniform(5000, 100000),
            "current_debt": random.uniform(0, 50000),
            "risk_tolerance": random.choice(["conservative", "moderate", "aggressive"]),
            "investment_experience": random.choice(["beginner", "intermediate", "advanced"]),
            "investment_timeline": random.randint(5, 40),
            "financial_goals": random.sample(
                ["retirement", "house_down_payment", "emergency_fund", "education", "travel"],
                k=random.randint(1, 3)
            ),
            "employment_status": random.choice(["employed", "self_employed", "retired"]),
            "marital_status": random.choice(["single", "married", "divorced"]),
            "dependents": random.randint(0, 4)
        }
        
        with self.client.post(
            "/api/v1/financial-profiles/",
            json=profile_data,
            headers=self.get_auth_headers(),
            catch_response=True,
            name="create_financial_profile"
        ) as response:
            if response.status_code == 201:
                profile = response.json()
                self.financial_profile_id = profile["id"]
                response.success()
            else:
                response.failure(f"Profile creation failed: {response.status_code}")
    
    @task(8)
    def create_financial_goal(self):
        """Create financial goals"""
        if not self.access_token or len(self.goal_ids) >= 3:
            return
        
        goal_types = {
            "retirement": {
                "target_range": (500000, 2000000),
                "years_range": (20, 40)
            },
            "major_purchase": {
                "target_range": (20000, 150000),
                "years_range": (2, 10)
            },
            "emergency": {
                "target_range": (10000, 50000),
                "years_range": (1, 3)
            },
            "education": {
                "target_range": (50000, 200000),
                "years_range": (5, 18)
            }
        }
        
        goal_type = random.choice(list(goal_types.keys()))
        goal_config = goal_types[goal_type]
        
        target_amount = random.uniform(*goal_config["target_range"])
        years_to_goal = random.randint(*goal_config["years_range"])
        
        goal_data = {
            "name": f"{goal_type.replace('_', ' ').title()} Goal",
            "description": f"Load test {goal_type} goal",
            "goal_type": goal_type,
            "target_amount": target_amount,
            "current_amount": random.uniform(0, target_amount * 0.3),
            "target_date": (datetime.now() + timedelta(days=years_to_goal * 365)).isoformat(),
            "priority": random.choice(["low", "medium", "high"]),
            "monthly_contribution": random.uniform(100, 2000)
        }
        
        with self.client.post(
            "/api/v1/goals/",
            json=goal_data,
            headers=self.get_auth_headers(),
            catch_response=True,
            name="create_goal"
        ) as response:
            if response.status_code == 201:
                goal = response.json()
                self.goal_ids.append(goal["id"])
                response.success()
            else:
                response.failure(f"Goal creation failed: {response.status_code}")
    
    @task(5)
    def get_user_goals(self):
        """Retrieve user goals"""
        if not self.access_token:
            return
        
        with self.client.get(
            "/api/v1/goals/",
            headers=self.get_auth_headers(),
            catch_response=True,
            name="get_goals"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Get goals failed: {response.status_code}")
    
    @task(15)
    def optimize_portfolio(self):
        """Run portfolio optimization"""
        if not self.access_token:
            return
        
        # Generate realistic asset data
        assets = [
            {
                "symbol": "VTI",
                "expected_return": random.uniform(0.06, 0.10),
                "volatility": random.uniform(0.12, 0.18),
                "asset_class": "equities"
            },
            {
                "symbol": "VXUS",
                "expected_return": random.uniform(0.05, 0.09),
                "volatility": random.uniform(0.15, 0.22),
                "asset_class": "international_equities"
            },
            {
                "symbol": "BND",
                "expected_return": random.uniform(0.02, 0.05),
                "volatility": random.uniform(0.03, 0.07),
                "asset_class": "bonds"
            },
            {
                "symbol": "VNQ",
                "expected_return": random.uniform(0.05, 0.08),
                "volatility": random.uniform(0.16, 0.25),
                "asset_class": "reits"
            },
            {
                "symbol": "VTI",
                "expected_return": random.uniform(0.04, 0.07),
                "volatility": random.uniform(0.10, 0.15),
                "asset_class": "commodities"
            }
        ]
        
        # Randomly select 3-4 assets
        selected_assets = random.sample(assets, k=random.randint(3, 4))
        
        optimization_request = {
            "method": random.choice(["max_sharpe", "min_variance", "risk_parity"]),
            "assets": selected_assets,
            "constraints": {
                "max_position_size": random.uniform(0.3, 0.6),
                "min_position_size": random.uniform(0.01, 0.05)
            },
            "investment_amount": random.uniform(10000, 500000)
        }
        
        with self.client.post(
            "/api/v1/portfolio/optimize",
            json=optimization_request,
            headers=self.get_auth_headers(),
            catch_response=True,
            name="portfolio_optimization"
        ) as response:
            if response.status_code == 200:
                result = response.json()
                self.portfolio_weights = result.get("weights")
                response.success()
            else:
                response.failure(f"Portfolio optimization failed: {response.status_code}")
    
    @task(8)
    def run_monte_carlo_simulation(self):
        """Run Monte Carlo simulation"""
        if not self.access_token:
            return
        
        simulation_request = {
            "initial_investment": random.uniform(10000, 200000),
            "monthly_contribution": random.uniform(500, 3000),
            "investment_horizon_years": random.randint(10, 40),
            "expected_return": random.uniform(0.05, 0.12),
            "volatility": random.uniform(0.10, 0.25),
            "num_simulations": random.choice([1000, 5000, 10000]),
            "confidence_levels": [0.1, 0.5, 0.9]
        }
        
        with self.client.post(
            "/api/v1/simulations/monte-carlo",
            json=simulation_request,
            headers=self.get_auth_headers(),
            catch_response=True,
            name="monte_carlo_simulation"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Monte Carlo simulation failed: {response.status_code}")
    
    @task(3)
    def goal_progress_simulation(self):
        """Run goal-specific simulation"""
        if not self.access_token or not self.goal_ids:
            return
        
        goal_id = random.choice(self.goal_ids)
        
        simulation_request = {
            "goal_id": goal_id,
            "current_savings": random.uniform(5000, 50000),
            "monthly_contribution": random.uniform(200, 1500),
            "expected_return": random.uniform(0.06, 0.10),
            "volatility": random.uniform(0.12, 0.20),
            "num_simulations": 5000
        }
        
        with self.client.post(
            "/api/v1/simulations/goal-analysis",
            json=simulation_request,
            headers=self.get_auth_headers(),
            catch_response=True,
            name="goal_simulation"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Goal simulation failed: {response.status_code}")
    
    @task(2)
    def tax_loss_harvesting_analysis(self):
        """Analyze tax loss harvesting opportunities"""
        if not self.access_token:
            return
        
        # Generate realistic holdings data
        holdings = []
        for _ in range(random.randint(5, 15)):
            symbol = random.choice(["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA", "SPY", "QQQ", "VTI", "BND"])
            purchase_price = random.uniform(50, 500)
            current_price = purchase_price * random.uniform(0.7, 1.4)  # Some gains, some losses
            
            holding = {
                "symbol": symbol,
                "quantity": random.randint(10, 500),
                "purchase_price": purchase_price,
                "current_price": current_price,
                "purchase_date": (datetime.now() - timedelta(days=random.randint(30, 730))).isoformat(),
                "account_type": random.choice(["taxable", "traditional_401k", "roth_ira"])
            }
            holdings.append(holding)
        
        request_data = {
            "holdings": holdings,
            "tax_rate": random.uniform(0.22, 0.32),
            "analysis_date": datetime.now().isoformat()
        }
        
        with self.client.post(
            "/api/v1/tax/loss-harvesting-analysis",
            json=request_data,
            headers=self.get_auth_headers(),
            catch_response=True,
            name="tax_loss_harvesting"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Tax analysis failed: {response.status_code}")
    
    @task(1)
    def health_check(self):
        """Simple health check"""
        with self.client.get("/api/v1/health", name="health_check") as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Health check failed: {response.status_code}")


class HeavyComputationUser(FinancialPlanningUser):
    """
    User focused on computationally intensive operations
    Simulates users who run large simulations and complex optimizations
    """
    
    weight = 3  # This user type has lower probability of being chosen
    
    @task(20)
    def large_portfolio_optimization(self):
        """Optimize portfolio with many assets"""
        if not self.access_token:
            return
        
        # Generate many assets for large portfolio
        symbols = [
            "VTI", "VXUS", "VEA", "VWO", "BND", "VTEB", "VGIT", "VNQ", "VNQI", "VDE",
            "VGT", "VHT", "VFH", "VAW", "VIS", "VCR", "VDC", "VPU", "VGK", "VPL"
        ]
        
        assets = []
        for symbol in random.sample(symbols, k=random.randint(8, 15)):
            asset = {
                "symbol": symbol,
                "expected_return": random.uniform(0.03, 0.15),
                "volatility": random.uniform(0.08, 0.30),
                "asset_class": random.choice(["equities", "bonds", "reits", "commodities"])
            }
            assets.append(asset)
        
        optimization_request = {
            "method": "max_sharpe",
            "assets": assets,
            "constraints": {
                "max_position_size": 0.15,
                "min_position_size": 0.01,
                "sector_limits": {
                    "technology": [0.05, 0.25],
                    "healthcare": [0.05, 0.20]
                }
            },
            "investment_amount": random.uniform(100000, 1000000)
        }
        
        with self.client.post(
            "/api/v1/portfolio/optimize",
            json=optimization_request,
            headers=self.get_auth_headers(),
            catch_response=True,
            name="large_portfolio_optimization"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Large portfolio optimization failed: {response.status_code}")
    
    @task(15)
    def high_precision_monte_carlo(self):
        """Run high-precision Monte Carlo simulation"""
        if not self.access_token:
            return
        
        simulation_request = {
            "initial_investment": random.uniform(50000, 500000),
            "monthly_contribution": random.uniform(1000, 5000),
            "investment_horizon_years": random.randint(20, 40),
            "expected_return": random.uniform(0.06, 0.12),
            "volatility": random.uniform(0.12, 0.25),
            "num_simulations": 50000,  # High precision
            "confidence_levels": [0.01, 0.05, 0.1, 0.25, 0.5, 0.75, 0.9, 0.95, 0.99]
        }
        
        with self.client.post(
            "/api/v1/simulations/monte-carlo",
            json=simulation_request,
            headers=self.get_auth_headers(),
            catch_response=True,
            name="high_precision_simulation"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"High precision simulation failed: {response.status_code}")


class BurstTrafficUser(FinancialPlanningUser):
    """
    User that simulates burst traffic patterns
    Makes multiple rapid requests then pauses
    """
    
    wait_time = between(0.1, 0.5)  # Very short wait times
    weight = 2
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.burst_mode = False
        self.burst_count = 0
    
    @task(5)
    def burst_portfolio_requests(self):
        """Make burst of portfolio optimization requests"""
        if not self.access_token:
            return
        
        # Enter burst mode
        if not self.burst_mode:
            self.burst_mode = True
            self.burst_count = 0
        
        # Make rapid requests
        for _ in range(5):
            self.optimize_portfolio()
            time.sleep(0.1)
            
            self.burst_count += 1
            if self.burst_count >= 20:  # Exit burst mode
                self.burst_mode = False
                time.sleep(random.uniform(5, 10))  # Long pause
                break


# Custom event handlers for performance monitoring
@events.request.add_listener
def on_request(request_type, name, response_time, response_length, response, context, exception, **kwargs):
    """
    Custom request handler to log slow requests
    """
    if response_time > 5000:  # Log requests over 5 seconds
        logger.warning(f"Slow request: {name} took {response_time}ms")
    
    if exception:
        logger.error(f"Request failed: {name} - {exception}")


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """
    Called when test starts
    """
    logger.info("Financial Planning load test started")
    logger.info(f"Target host: {environment.host}")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """
    Called when test stops
    """
    logger.info("Financial Planning load test completed")
    
    # Log summary statistics
    stats = environment.stats
    logger.info(f"Total requests: {stats.total.num_requests}")
    logger.info(f"Total failures: {stats.total.num_failures}")
    logger.info(f"Average response time: {stats.total.avg_response_time}ms")
    logger.info(f"Max response time: {stats.total.max_response_time}ms")


# Performance test scenarios
class QuickLoadTest(FinancialPlanningUser):
    """Quick load test scenario - 5 minutes"""
    wait_time = between(1, 2)
    weight = 10


class SustainedLoadTest(FinancialPlanningUser):
    """Sustained load test scenario - 30+ minutes"""
    wait_time = between(2, 5)
    weight = 8


class StressTest(FinancialPlanningUser):
    """Stress test scenario - high load, minimal wait times"""
    wait_time = between(0.5, 1)
    weight = 6


if __name__ == "__main__":
    # Command line usage information
    print("""
    Financial Planning API Load Testing Suite
    
    Usage examples:
    
    # Quick test (5 users, 2 per second for 60 seconds)
    locust -f locust_financial_planning.py --host=http://localhost:8000 \
           --users=5 --spawn-rate=2 --run-time=60s --headless
    
    # Standard load test (25 users, 5 per second for 300 seconds)
    locust -f locust_financial_planning.py --host=http://localhost:8000 \
           --users=25 --spawn-rate=5 --run-time=300s --headless
    
    # Stress test (100 users, 10 per second for 600 seconds)
    locust -f locust_financial_planning.py --host=http://localhost:8000 \
           --users=100 --spawn-rate=10 --run-time=600s --headless
    
    # Extreme stress test (500 users, 20 per second)
    locust -f locust_financial_planning.py --host=http://localhost:8000 \
           --users=500 --spawn-rate=20 --run-time=1200s --headless
    
    Results will be saved to HTML report automatically.
    """)
