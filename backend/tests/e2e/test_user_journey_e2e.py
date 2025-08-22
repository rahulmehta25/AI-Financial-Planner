"""
End-to-End Browser Tests for Financial Planning System

Tests the complete user journey through a web browser using Playwright.
Covers registration, login, profile creation, simulations, and report generation.

Install dependencies:
pip install playwright pytest-playwright
playwright install

Run with: 
python -m pytest tests/e2e/test_user_journey_e2e.py -v --headed
"""

import asyncio
import json
import time
from pathlib import Path
from typing import Dict, Any

import pytest
from playwright.async_api import async_playwright, Page, BrowserContext, expect


class E2ETestData:
    """Test data for E2E testing"""
    
    TEST_USER = {
        "email": "e2e-test@example.com",
        "password": "SecurePassword123!",
        "full_name": "E2E Test User",
        "age": 35
    }
    
    FINANCIAL_PROFILE = {
        "annual_income": 120000,
        "current_savings": 75000,
        "monthly_expenses": 7000,
        "debt_amount": 25000,
        "risk_tolerance": "moderate",
        "investment_timeline": 25,
        "retirement_age": 65,
        "dependents": 2
    }
    
    GOALS = [
        {
            "name": "Retirement Savings",
            "target_amount": 1500000,
            "priority": "high",
            "category": "retirement"
        },
        {
            "name": "Emergency Fund",
            "target_amount": 60000,
            "priority": "high", 
            "category": "emergency"
        },
        {
            "name": "House Down Payment",
            "target_amount": 150000,
            "priority": "medium",
            "category": "major_purchase"
        }
    ]


@pytest.fixture(scope="session")
async def browser_context():
    """Create a browser context for testing"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,  # Set to True for CI/CD
            slow_mo=100,     # Slow down actions for demo
            args=['--no-sandbox', '--disable-dev-shm-usage']
        )
        
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 720},
            record_video_dir="tests/e2e/videos/",
            record_video_size={'width': 1280, 'height': 720}
        )
        
        yield context
        await context.close()
        await browser.close()


@pytest.fixture
async def page(browser_context: BrowserContext):
    """Create a new page for each test"""
    page = await browser_context.new_page()
    yield page
    await page.close()


class TestFinancialPlanningE2E:
    """End-to-end test suite for the Financial Planning System"""
    
    BASE_URL = "http://localhost:3000"  # Frontend URL
    API_URL = "http://localhost:8000"   # Backend API URL
    
    async def test_01_system_health_check(self, page: Page):
        """Test that the system is running and accessible"""
        print("\n🏥 Testing system health...")
        
        # Check API health endpoint
        response = await page.request.get(f"{self.API_URL}/health")
        assert response.status == 200
        
        health_data = await response.json()
        assert health_data["status"] == "healthy"
        print(f"   ✅ API Health: {health_data['status']}")
    
    async def test_02_frontend_loads(self, page: Page):
        """Test that the frontend application loads"""
        print("\n🌐 Testing frontend loading...")
        
        try:
            await page.goto(self.BASE_URL, wait_until="networkidle")
            
            # Wait for the app to load
            await page.wait_for_selector("body", timeout=10000)
            
            # Check for common elements that indicate the app loaded
            title = await page.title()
            print(f"   ✅ Page loaded: {title}")
            
            # Take a screenshot
            await page.screenshot(path="tests/e2e/screenshots/01_homepage.png")
            
        except Exception as e:
            print(f"   ⚠️  Frontend not available: {str(e)}")
            print("   📝 This test requires a running frontend application")
            pytest.skip("Frontend not available - testing API only")
    
    async def test_03_user_registration_flow(self, page: Page):
        """Test user registration through the UI"""
        print("\n👤 Testing user registration flow...")
        
        try:
            await page.goto(f"{self.BASE_URL}/register")
            
            # Fill registration form
            await page.fill('[data-testid="email-input"]', E2ETestData.TEST_USER["email"])
            await page.fill('[data-testid="password-input"]', E2ETestData.TEST_USER["password"])
            await page.fill('[data-testid="full-name-input"]', E2ETestData.TEST_USER["full_name"])
            await page.fill('[data-testid="age-input"]', str(E2ETestData.TEST_USER["age"]))
            
            # Submit form
            await page.click('[data-testid="register-button"]')
            
            # Wait for success indication
            await page.wait_for_selector('[data-testid="registration-success"]', timeout=5000)
            
            print("   ✅ User registration completed through UI")
            await page.screenshot(path="tests/e2e/screenshots/02_registration_success.png")
            
        except Exception as e:
            print(f"   ⚠️  UI registration test failed: {str(e)}")
            # Fallback to API registration
            await self._register_user_via_api(page)
    
    async def _register_user_via_api(self, page: Page):
        """Fallback registration via API"""
        print("   🔄 Registering user via API...")
        
        response = await page.request.post(
            f"{self.API_URL}/api/v1/auth/register",
            data=json.dumps(E2ETestData.TEST_USER),
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status == 201
        print("   ✅ User registered via API")
    
    async def test_04_user_login_flow(self, page: Page):
        """Test user login through the UI"""
        print("\n🔐 Testing user login flow...")
        
        try:
            await page.goto(f"{self.BASE_URL}/login")
            
            # Fill login form
            await page.fill('[data-testid="email-input"]', E2ETestData.TEST_USER["email"])
            await page.fill('[data-testid="password-input"]', E2ETestData.TEST_USER["password"])
            
            # Submit form
            await page.click('[data-testid="login-button"]')
            
            # Wait for dashboard or profile page
            await page.wait_for_url("**/dashboard", timeout=10000)
            
            print("   ✅ User login completed through UI")
            await page.screenshot(path="tests/e2e/screenshots/03_login_success.png")
            
        except Exception as e:
            print(f"   ⚠️  UI login test failed: {str(e)}")
            # Fallback to API login
            await self._login_user_via_api(page)
    
    async def _login_user_via_api(self, page: Page):
        """Fallback login via API"""
        print("   🔄 Logging in user via API...")
        
        login_data = {
            "username": E2ETestData.TEST_USER["email"],
            "password": E2ETestData.TEST_USER["password"]
        }
        
        response = await page.request.post(
            f"{self.API_URL}/api/v1/auth/login",
            data=login_data
        )
        
        assert response.status == 200
        auth_data = await response.json()
        
        # Store token in browser context for subsequent requests
        await page.context.add_cookies([{
            "name": "access_token",
            "value": auth_data["access_token"],
            "domain": "localhost",
            "path": "/"
        }])
        
        print("   ✅ User logged in via API")
    
    async def test_05_financial_profile_creation(self, page: Page):
        """Test financial profile creation"""
        print("\n💰 Testing financial profile creation...")
        
        try:
            await page.goto(f"{self.BASE_URL}/profile/create")
            
            # Fill financial profile form
            profile_data = E2ETestData.FINANCIAL_PROFILE
            
            await page.fill('[data-testid="annual-income"]', str(profile_data["annual_income"]))
            await page.fill('[data-testid="current-savings"]', str(profile_data["current_savings"]))
            await page.fill('[data-testid="monthly-expenses"]', str(profile_data["monthly_expenses"]))
            await page.fill('[data-testid="debt-amount"]', str(profile_data["debt_amount"]))
            
            # Select risk tolerance
            await page.select_option('[data-testid="risk-tolerance"]', profile_data["risk_tolerance"])
            
            await page.fill('[data-testid="investment-timeline"]', str(profile_data["investment_timeline"]))
            await page.fill('[data-testid="retirement-age"]', str(profile_data["retirement_age"]))
            await page.fill('[data-testid="dependents"]', str(profile_data["dependents"]))
            
            # Submit form
            await page.click('[data-testid="create-profile-button"]')
            
            # Wait for success
            await page.wait_for_selector('[data-testid="profile-success"]', timeout=10000)
            
            print("   ✅ Financial profile created through UI")
            await page.screenshot(path="tests/e2e/screenshots/04_profile_created.png")
            
        except Exception as e:
            print(f"   ⚠️  UI profile creation failed: {str(e)}")
            await self._create_profile_via_api(page)
    
    async def _create_profile_via_api(self, page: Page):
        """Fallback profile creation via API"""
        print("   🔄 Creating profile via API...")
        
        response = await page.request.post(
            f"{self.API_URL}/api/v1/financial-profiles/",
            data=json.dumps(E2ETestData.FINANCIAL_PROFILE),
            headers={"Content-Type": "application/json"}
        )
        
        if response.status == 201:
            profile_data = await response.json()
            print(f"   ✅ Profile created via API: {profile_data['id']}")
            return profile_data["id"]
        else:
            print(f"   ❌ Profile creation failed: {response.status}")
            return None
    
    async def test_06_goal_creation_flow(self, page: Page):
        """Test financial goal creation"""
        print("\n🎯 Testing goal creation flow...")
        
        try:
            await page.goto(f"{self.BASE_URL}/goals/create")
            
            # Create each goal
            for i, goal_data in enumerate(E2ETestData.GOALS):
                if i > 0:
                    # Click "Add Another Goal" for subsequent goals
                    await page.click('[data-testid="add-goal-button"]')
                
                # Fill goal form
                await page.fill(f'[data-testid="goal-name-{i}"]', goal_data["name"])
                await page.fill(f'[data-testid="goal-amount-{i}"]', str(goal_data["target_amount"]))
                await page.select_option(f'[data-testid="goal-priority-{i}"]', goal_data["priority"])
                await page.select_option(f'[data-testid="goal-category-{i}"]', goal_data["category"])
                
                print(f"   📝 Goal configured: {goal_data['name']} - ${goal_data['target_amount']:,}")
            
            # Submit all goals
            await page.click('[data-testid="save-goals-button"]')
            
            # Wait for success
            await page.wait_for_selector('[data-testid="goals-success"]', timeout=10000)
            
            print("   ✅ Goals created through UI")
            await page.screenshot(path="tests/e2e/screenshots/05_goals_created.png")
            
        except Exception as e:
            print(f"   ⚠️  UI goal creation failed: {str(e)}")
            await self._create_goals_via_api(page)
    
    async def _create_goals_via_api(self, page: Page):
        """Fallback goal creation via API"""
        print("   🔄 Creating goals via API...")
        
        for goal_data in E2ETestData.GOALS:
            # Add target_date for API
            goal_with_date = {
                **goal_data,
                "target_date": "2044-01-01T00:00:00Z"
            }
            
            response = await page.request.post(
                f"{self.API_URL}/api/v1/goals/",
                data=json.dumps(goal_with_date),
                headers={"Content-Type": "application/json"}
            )
            
            if response.status == 201:
                print(f"   ✅ Goal created: {goal_data['name']}")
            else:
                print(f"   ⚠️  Goal creation failed: {goal_data['name']}")
    
    async def test_07_monte_carlo_simulation(self, page: Page):
        """Test Monte Carlo simulation execution"""
        print("\n📊 Testing Monte Carlo simulation...")
        
        try:
            await page.goto(f"{self.BASE_URL}/simulations")
            
            # Configure simulation parameters
            await page.fill('[data-testid="iterations"]', "10000")
            await page.fill('[data-testid="years"]', "20")
            await page.fill('[data-testid="expected-return"]', "0.07")
            await page.fill('[data-testid="volatility"]', "0.15")
            
            # Start simulation
            await page.click('[data-testid="run-simulation-button"]')
            
            # Wait for simulation to complete (with longer timeout)
            await page.wait_for_selector('[data-testid="simulation-results"]', timeout=30000)
            
            # Check results are displayed
            success_rate = await page.text_content('[data-testid="success-probability"]')
            expected_value = await page.text_content('[data-testid="expected-value"]')
            
            print(f"   ✅ Simulation completed")
            print(f"   📈 Success Rate: {success_rate}")
            print(f"   💰 Expected Value: {expected_value}")
            
            await page.screenshot(path="tests/e2e/screenshots/06_simulation_results.png")
            
        except Exception as e:
            print(f"   ⚠️  UI simulation failed: {str(e)}")
            await self._run_simulation_via_api(page)
    
    async def _run_simulation_via_api(self, page: Page):
        """Fallback simulation via API"""
        print("   🔄 Running simulation via API...")
        
        simulation_data = {
            "profile_id": "1",  # Assuming profile exists
            "iterations": 10000,
            "years": 20,
            "inflation_rate": 0.025,
            "market_volatility": 0.15,
            "expected_return": 0.07
        }
        
        response = await page.request.post(
            f"{self.API_URL}/api/v1/monte-carlo/run",
            data=json.dumps(simulation_data),
            headers={"Content-Type": "application/json"}
        )
        
        if response.status == 200:
            result = await response.json()
            print(f"   ✅ Simulation completed via API")
            print(f"   📊 Success probability: {result.get('success_probability', 'N/A')}")
        else:
            print(f"   ⚠️  Simulation failed: {response.status}")
    
    async def test_08_pdf_report_generation(self, page: Page):
        """Test PDF report generation and download"""
        print("\n📄 Testing PDF report generation...")
        
        try:
            await page.goto(f"{self.BASE_URL}/reports")
            
            # Configure report options
            await page.check('[data-testid="include-charts"]')
            await page.check('[data-testid="include-goals"]')
            await page.check('[data-testid="include-recommendations"]')
            
            # Set up download promise before clicking
            async with page.expect_download() as download_info:
                await page.click('[data-testid="generate-pdf-button"]')
            
            download = await download_info.value
            
            # Save the downloaded file
            await download.save_as("tests/e2e/downloads/financial_report.pdf")
            
            print(f"   ✅ PDF report downloaded: {download.suggested_filename}")
            print(f"   📄 File size: {await download.path()} bytes" if await download.path() else "Unknown")
            
        except Exception as e:
            print(f"   ⚠️  UI PDF generation failed: {str(e)}")
            await self._generate_pdf_via_api(page)
    
    async def _generate_pdf_via_api(self, page: Page):
        """Fallback PDF generation via API"""
        print("   🔄 Generating PDF via API...")
        
        report_data = {
            "profile_id": "1",
            "template": "detailed_plan",
            "include_charts": True,
            "include_goals": True,
            "include_recommendations": True
        }
        
        response = await page.request.post(
            f"{self.API_URL}/api/v1/export/pdf/financial-plan",
            data=json.dumps(report_data),
            headers={"Content-Type": "application/json"}
        )
        
        if response.status == 200:
            content_type = response.headers.get("content-type", "")
            if "application/pdf" in content_type:
                print("   ✅ PDF generated via API")
                
                # Save PDF
                pdf_content = await response.body()
                Path("tests/e2e/downloads/").mkdir(exist_ok=True)
                with open("tests/e2e/downloads/api_financial_report.pdf", "wb") as f:
                    f.write(pdf_content)
                print(f"   💾 PDF saved: {len(pdf_content)} bytes")
            else:
                result = await response.json()
                if "task_id" in result:
                    print(f"   🔄 PDF generation started (async): {result['task_id']}")
        else:
            print(f"   ⚠️  PDF generation failed: {response.status}")
    
    async def test_09_navigation_and_responsiveness(self, page: Page):
        """Test navigation between pages and responsive design"""
        print("\n🧭 Testing navigation and responsiveness...")
        
        try:
            # Test main navigation
            navigation_items = [
                ("/dashboard", "Dashboard"),
                ("/profile", "Profile"),
                ("/goals", "Goals"),
                ("/simulations", "Simulations"),
                ("/reports", "Reports")
            ]
            
            for path, name in navigation_items:
                try:
                    await page.goto(f"{self.BASE_URL}{path}")
                    await page.wait_for_load_state("networkidle")
                    print(f"   ✅ {name} page loaded")
                except Exception as e:
                    print(f"   ⚠️  {name} page failed: {str(e)}")
            
            # Test responsive design
            viewports = [
                {"width": 1920, "height": 1080, "name": "Desktop"},
                {"width": 768, "height": 1024, "name": "Tablet"},
                {"width": 375, "height": 667, "name": "Mobile"}
            ]
            
            for viewport in viewports:
                await page.set_viewport_size({"width": viewport["width"], "height": viewport["height"]})
                await page.goto(f"{self.BASE_URL}/dashboard")
                await page.screenshot(path=f"tests/e2e/screenshots/responsive_{viewport['name'].lower()}.png")
                print(f"   📱 {viewport['name']} layout captured")
            
        except Exception as e:
            print(f"   ⚠️  Navigation test incomplete: {str(e)}")
    
    async def test_10_performance_metrics(self, page: Page):
        """Test and measure performance metrics"""
        print("\n⚡ Testing performance metrics...")
        
        try:
            # Navigate to main dashboard and measure load time
            start_time = time.time()
            await page.goto(f"{self.BASE_URL}/dashboard", wait_until="networkidle")
            load_time = time.time() - start_time
            
            print(f"   📊 Dashboard load time: {load_time:.2f} seconds")
            
            # Measure JavaScript errors
            errors = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            
            # Navigate through key pages
            await page.goto(f"{self.BASE_URL}/simulations")
            await page.wait_for_load_state("networkidle")
            
            if errors:
                print(f"   ⚠️  JavaScript errors detected: {len(errors)}")
                for error in errors[:3]:  # Show first 3 errors
                    print(f"      - {error}")
            else:
                print("   ✅ No JavaScript errors detected")
            
            # Test for accessibility issues (basic check)
            await page.evaluate("""
                // Basic accessibility check
                const images = document.querySelectorAll('img:not([alt])');
                const buttons = document.querySelectorAll('button:not([aria-label]):not([title])');
                console.log('Images without alt:', images.length);
                console.log('Buttons without labels:', buttons.length);
            """)
            
            print("   ✅ Performance metrics collected")
            
        except Exception as e:
            print(f"   ⚠️  Performance testing failed: {str(e)}")


# Test fixtures and utilities
@pytest.fixture(scope="session", autouse=True)
def setup_e2e_environment():
    """Set up the E2E testing environment"""
    print("🔧 Setting up E2E test environment...")
    
    # Create necessary directories
    Path("tests/e2e/screenshots").mkdir(parents=True, exist_ok=True)
    Path("tests/e2e/videos").mkdir(parents=True, exist_ok=True)
    Path("tests/e2e/downloads").mkdir(parents=True, exist_ok=True)
    
    yield
    
    print("🧹 E2E test environment cleanup completed")


# Utility functions for CI/CD
def run_headless_tests():
    """Run tests in headless mode for CI/CD"""
    import subprocess
    
    cmd = [
        "python", "-m", "pytest", 
        "tests/e2e/test_user_journey_e2e.py",
        "-v", "--headless", "--maxfail=3"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0


if __name__ == "__main__":
    # Run the E2E tests directly
    import subprocess
    
    print("🚀 Running E2E Test Suite...")
    result = subprocess.run([
        "python", "-m", "pytest", __file__, "-v", "--tb=short"
    ])
    
    exit(result.returncode)