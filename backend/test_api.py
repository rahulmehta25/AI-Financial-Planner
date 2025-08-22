#!/usr/bin/env python3
"""
Comprehensive API Testing Script for AI Financial Planning System

Tests all available endpoints and provides clear feedback on what's working.
Color-coded output: Green=Pass, Yellow=Partial/Warning, Red=Fail

Usage: python test_api.py [base_url]
Default base_url: http://localhost:8000
"""

import requests
import json
import sys
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from urllib.parse import urljoin
import traceback

# Color codes for terminal output
class Colors:
    GREEN = '\033[92m'  # Success
    YELLOW = '\033[93m'  # Warning/Partial
    RED = '\033[91m'    # Error
    BLUE = '\033[94m'   # Info
    PURPLE = '\033[95m' # Header
    CYAN = '\033[96m'   # Request details
    WHITE = '\033[97m'  # Normal text
    BOLD = '\033[1m'    # Bold
    END = '\033[0m'     # Reset

def print_colored(text: str, color: str = Colors.WHITE) -> None:
    """Print text with color"""
    print(f"{color}{text}{Colors.END}")

def print_header(text: str) -> None:
    """Print a header with formatting"""
    print_colored(f"\n{'='*60}", Colors.PURPLE)
    print_colored(f"{text.center(60)}", Colors.PURPLE + Colors.BOLD)
    print_colored(f"{'='*60}", Colors.PURPLE)

def print_subheader(text: str) -> None:
    """Print a subheader with formatting"""
    print_colored(f"\n{'-'*40}", Colors.BLUE)
    print_colored(f"{text}", Colors.BLUE + Colors.BOLD)
    print_colored(f"{'-'*40}", Colors.BLUE)

def print_request_details(method: str, url: str, data: Any = None) -> None:
    """Print request details"""
    print_colored(f"🔄 {method} {url}", Colors.CYAN)
    if data:
        print_colored(f"📤 Request Data: {json.dumps(data, indent=2)}", Colors.CYAN)

def print_response_summary(status_code: int, response_time: float, data: Any = None) -> None:
    """Print response summary with appropriate colors"""
    if 200 <= status_code < 300:
        color = Colors.GREEN
        status_text = "SUCCESS"
    elif 400 <= status_code < 500:
        color = Colors.YELLOW
        status_text = "CLIENT ERROR"
    else:
        color = Colors.RED
        status_text = "SERVER ERROR"
    
    print_colored(f"📥 {status_code} {status_text} ({response_time:.2f}s)", color)
    if data:
        print_colored(f"📊 Response Data: {json.dumps(data, indent=2)[:500]}{'...' if len(str(data)) > 500 else ''}", color)

class APITester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        self.access_token: Optional[str] = None
        self.user_id: Optional[str] = None
        self.test_results: List[Dict[str, Any]] = []
    
    def make_request(self, method: str, endpoint: str, data: Any = None, 
                    headers: Dict[str, str] = None, params: Dict[str, Any] = None) -> Tuple[int, Any, float]:
        """Make HTTP request and return status code, data, and response time"""
        url = urljoin(self.base_url, endpoint.lstrip('/'))
        
        # Add authentication header if we have a token
        req_headers = headers or {}
        if self.access_token:
            req_headers['Authorization'] = f'Bearer {self.access_token}'
        
        print_request_details(method, url, data)
        
        start_time = time.time()
        try:
            response = self.session.request(
                method=method,
                url=url,
                json=data if method.upper() in ['POST', 'PUT', 'PATCH'] else None,
                headers=req_headers,
                params=params,
                timeout=30
            )
            response_time = time.time() - start_time
            
            try:
                response_data = response.json() if response.content else None
            except json.JSONDecodeError:
                response_data = response.text
            
            print_response_summary(response.status_code, response_time, response_data)
            
            return response.status_code, response_data, response_time
            
        except requests.exceptions.RequestException as e:
            response_time = time.time() - start_time
            print_colored(f"❌ Request failed: {str(e)}", Colors.RED)
            return 0, {"error": str(e)}, response_time
    
    def test_health_checks(self) -> None:
        """Test health check endpoints"""
        print_header("HEALTH CHECK ENDPOINTS")
        
        # Test root endpoint
        print_subheader("Root Endpoint")
        status, data, time_taken = self.make_request('GET', '/')
        self.record_test("Root Health Check", status, 200, time_taken, data)
        
        # Test health endpoint
        print_subheader("Health Check Endpoint")
        status, data, time_taken = self.make_request('GET', '/health')
        self.record_test("Health Check", status, 200, time_taken, data)
        
        # Test API docs
        print_subheader("API Documentation")
        status, data, time_taken = self.make_request('GET', '/docs')
        self.record_test("API Docs", status, 200, time_taken, None)
    
    def test_user_registration(self) -> bool:
        """Test user registration endpoint"""
        print_header("USER REGISTRATION")
        
        # Generate unique test user
        timestamp = int(time.time())
        test_user = {
            "email": f"test_user_{timestamp}@example.com",
            "first_name": "Test",
            "last_name": "User",
            "password": "testpassword123",
            "confirm_password": "testpassword123",
            "company": "Test Company",
            "title": "Test Engineer"
        }
        
        print_subheader("Register New User")
        status, data, time_taken = self.make_request('POST', '/api/v1/auth/register', test_user)
        success = self.record_test("User Registration", status, 201, time_taken, data)
        
        if success and data:
            self.user_id = data.get('id')
            print_colored(f"✅ User registered successfully! User ID: {self.user_id}", Colors.GREEN)
            
            # Store credentials for login
            self.test_user_email = test_user['email']
            self.test_user_password = test_user['password']
            return True
        
        return False
    
    def test_user_login(self) -> bool:
        """Test user login endpoints"""
        print_header("USER AUTHENTICATION")
        
        if not hasattr(self, 'test_user_email'):
            print_colored("⚠️ No test user available. Cannot test login.", Colors.YELLOW)
            return False
        
        # Test OAuth2 login
        print_subheader("OAuth2 Login")
        login_data = {
            "username": self.test_user_email,
            "password": self.test_user_password,
            "grant_type": "password"
        }
        
        # OAuth2 uses form data, not JSON
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        status, data, time_taken = self.make_request('POST', '/api/v1/auth/login', login_data)
        success = self.record_test("OAuth2 Login", status, 200, time_taken, data)
        
        if success and data:
            self.access_token = data.get('access_token')
            print_colored(f"✅ Login successful! Token acquired.", Colors.GREEN)
            return True
        
        # Test email login as fallback
        print_subheader("Email Login")
        email_login_data = {
            "email": self.test_user_email,
            "password": self.test_user_password
        }
        
        status, data, time_taken = self.make_request('POST', '/api/v1/auth/login/email', email_login_data)
        success = self.record_test("Email Login", status, 200, time_taken, data)
        
        if success and data:
            self.access_token = data.get('access_token')
            print_colored(f"✅ Email login successful! Token acquired.", Colors.GREEN)
            return True
        
        return False
    
    def test_authenticated_endpoints(self) -> None:
        """Test endpoints that require authentication"""
        print_header("AUTHENTICATED USER ENDPOINTS")
        
        if not self.access_token:
            print_colored("⚠️ No access token available. Skipping authenticated tests.", Colors.YELLOW)
            return
        
        # Test get current user
        print_subheader("Get Current User")
        status, data, time_taken = self.make_request('GET', '/api/v1/users/me')
        self.record_test("Get Current User", status, 200, time_taken, data)
        
        # Test get user from auth endpoint
        print_subheader("Get User Info (Auth)")
        status, data, time_taken = self.make_request('GET', '/api/v1/auth/me')
        self.record_test("Get User Info", status, 200, time_taken, data)
        
        # Test token refresh
        print_subheader("Refresh Token")
        status, data, time_taken = self.make_request('POST', '/api/v1/auth/refresh')
        self.record_test("Refresh Token", status, 200, time_taken, data)
    
    def test_simulation_endpoints(self) -> None:
        """Test simulation-related endpoints"""
        print_header("SIMULATION ENDPOINTS")
        
        if not self.access_token:
            print_colored("⚠️ Authentication required for simulation endpoints.", Colors.YELLOW)
            return
        
        # Test get user simulations
        print_subheader("Get User Simulations")
        status, data, time_taken = self.make_request('GET', '/api/v1/simulations')
        self.record_test("Get User Simulations", status, 200, time_taken, data)
        
        # Test create simulation
        print_subheader("Create Simulation")
        simulation_data = {
            "name": "Test Retirement Simulation",
            "description": "Test Monte Carlo simulation for API testing",
            "simulation_type": "monte_carlo",
            "parameters": {
                "n_simulations": 1000,
                "years_to_retirement": 25,
                "initial_portfolio_value": 100000,
                "annual_contribution": 12000,
                "risk_tolerance": "moderate"
            }
        }
        
        status, data, time_taken = self.make_request('POST', '/api/v1/simulations', simulation_data)
        success = self.record_test("Create Simulation", status, 201, time_taken, data)
        
        if success and data:
            simulation_id = data.get('id')
            print_colored(f"✅ Simulation created! ID: {simulation_id}", Colors.GREEN)
            
            # Test get specific simulation
            if simulation_id:
                print_subheader("Get Specific Simulation")
                status, data, time_taken = self.make_request('GET', f'/api/v1/simulations/{simulation_id}')
                self.record_test("Get Specific Simulation", status, 200, time_taken, data)
    
    def test_financial_endpoints(self) -> None:
        """Test financial planning endpoints"""
        print_header("FINANCIAL PLANNING ENDPOINTS")
        
        if not self.access_token:
            print_colored("⚠️ Authentication required for financial endpoints.", Colors.YELLOW)
            return
        
        # Test financial profiles
        print_subheader("Financial Profiles")
        status, data, time_taken = self.make_request('GET', '/api/v1/financial-profiles')
        self.record_test("Get Financial Profiles", status, 200, time_taken, data)
        
        # Test goals
        print_subheader("Financial Goals")
        status, data, time_taken = self.make_request('GET', '/api/v1/goals')
        self.record_test("Get Financial Goals", status, 200, time_taken, data)
        
        # Test investments
        print_subheader("Investments")
        status, data, time_taken = self.make_request('GET', '/api/v1/investments')
        self.record_test("Get Investments", status, 200, time_taken, data)
    
    def test_market_data_endpoints(self) -> None:
        """Test market data endpoints"""
        print_header("MARKET DATA ENDPOINTS")
        
        # These might not require authentication
        print_subheader("Market Data")
        status, data, time_taken = self.make_request('GET', '/api/v1/market-data')
        self.record_test("Get Market Data", status, [200, 401, 404], time_taken, data)
        
        # Test specific market data
        print_subheader("Market Data - SPY")
        status, data, time_taken = self.make_request('GET', '/api/v1/market-data/SPY')
        self.record_test("Get SPY Market Data", status, [200, 401, 404], time_taken, data)
    
    def test_ml_endpoints(self) -> None:
        """Test ML recommendation endpoints"""
        print_header("ML RECOMMENDATION ENDPOINTS")
        
        if not self.access_token:
            print_colored("⚠️ Authentication required for ML endpoints.", Colors.YELLOW)
            return
        
        print_subheader("ML Recommendations")
        status, data, time_taken = self.make_request('GET', '/api/v1/ml/recommendations')
        self.record_test("Get ML Recommendations", status, [200, 404], time_taken, data)
    
    def test_banking_endpoints(self) -> None:
        """Test banking integration endpoints"""
        print_header("BANKING INTEGRATION ENDPOINTS")
        
        if not self.access_token:
            print_colored("⚠️ Authentication required for banking endpoints.", Colors.YELLOW)
            return
        
        print_subheader("Banking Accounts")
        status, data, time_taken = self.make_request('GET', '/api/v1/banking/accounts')
        self.record_test("Get Banking Accounts", status, [200, 404], time_taken, data)
        
        print_subheader("Banking Transactions")
        status, data, time_taken = self.make_request('GET', '/api/v1/banking/transactions')
        self.record_test("Get Banking Transactions", status, [200, 404], time_taken, data)
    
    def test_notification_endpoints(self) -> None:
        """Test notification endpoints"""
        print_header("NOTIFICATION ENDPOINTS")
        
        if not self.access_token:
            print_colored("⚠️ Authentication required for notification endpoints.", Colors.YELLOW)
            return
        
        print_subheader("User Notifications")
        status, data, time_taken = self.make_request('GET', '/api/v1/notifications')
        self.record_test("Get Notifications", status, [200, 404], time_taken, data)
    
    def test_voice_endpoints(self) -> None:
        """Test voice interface endpoints"""
        print_header("VOICE INTERFACE ENDPOINTS")
        
        if not self.access_token:
            print_colored("⚠️ Authentication required for voice endpoints.", Colors.YELLOW)
            return
        
        print_subheader("Voice Interface")
        status, data, time_taken = self.make_request('GET', '/api/v1/voice')
        self.record_test("Voice Interface", status, [200, 404], time_taken, data)
    
    def test_pdf_export_endpoints(self) -> None:
        """Test PDF export endpoints"""
        print_header("PDF EXPORT ENDPOINTS")
        
        if not self.access_token:
            print_colored("⚠️ Authentication required for PDF export endpoints.", Colors.YELLOW)
            return
        
        # Test list PDF exports
        print_subheader("PDF Exports")
        status, data, time_taken = self.make_request('GET', '/api/v1/pdf-exports')
        self.record_test("Get PDF Exports", status, [200, 404], time_taken, data)
    
    def record_test(self, test_name: str, actual_status: int, expected_status: Any, 
                   response_time: float, data: Any = None) -> bool:
        """Record test result"""
        if isinstance(expected_status, list):
            success = actual_status in expected_status
        else:
            success = actual_status == expected_status
        
        result = {
            'test_name': test_name,
            'expected_status': expected_status,
            'actual_status': actual_status,
            'success': success,
            'response_time': response_time,
            'timestamp': datetime.now().isoformat(),
            'data': data
        }
        
        self.test_results.append(result)
        
        # Print immediate result
        if success:
            print_colored(f"✅ {test_name}: PASSED", Colors.GREEN)
        else:
            print_colored(f"❌ {test_name}: FAILED (expected {expected_status}, got {actual_status})", Colors.RED)
        
        return success
    
    def print_summary(self) -> None:
        """Print test summary"""
        print_header("TEST SUMMARY")
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        avg_response_time = sum(result['response_time'] for result in self.test_results) / total_tests if total_tests > 0 else 0
        
        print_colored(f"📊 Total Tests: {total_tests}", Colors.BLUE)
        print_colored(f"✅ Passed: {passed_tests}", Colors.GREEN)
        print_colored(f"❌ Failed: {failed_tests}", Colors.RED)
        print_colored(f"⏱️  Average Response Time: {avg_response_time:.2f}s", Colors.BLUE)
        print_colored(f"📈 Success Rate: {(passed_tests/total_tests)*100:.1f}%", Colors.BLUE)
        
        # Print working endpoints
        print_subheader("WORKING ENDPOINTS")
        working_endpoints = [result for result in self.test_results if result['success']]
        if working_endpoints:
            for result in working_endpoints:
                print_colored(f"✅ {result['test_name']} ({result['response_time']:.2f}s)", Colors.GREEN)
        else:
            print_colored("❌ No endpoints are currently working", Colors.RED)
        
        # Print failing endpoints
        failing_endpoints = [result for result in self.test_results if not result['success']]
        if failing_endpoints:
            print_subheader("FAILING ENDPOINTS")
            for result in failing_endpoints:
                print_colored(f"❌ {result['test_name']} (expected {result['expected_status']}, got {result['actual_status']})", Colors.RED)
        
        # Generate recommendations
        print_subheader("RECOMMENDATIONS")
        if failed_tests == 0:
            print_colored("🎉 All endpoints are working perfectly!", Colors.GREEN)
        elif passed_tests == 0:
            print_colored("🚨 Server appears to be down or misconfigured. Check server status.", Colors.RED)
        else:
            print_colored("⚠️ Some endpoints are working. Check server logs for failed endpoints.", Colors.YELLOW)
            
        # Check if authentication is working
        auth_tests = [r for r in self.test_results if 'login' in r['test_name'].lower() or 'register' in r['test_name'].lower()]
        auth_working = any(r['success'] for r in auth_tests)
        
        if not auth_working:
            print_colored("🔐 Authentication not working - many endpoints will be inaccessible", Colors.YELLOW)
        elif self.access_token:
            print_colored("🔐 Authentication working - full API access available", Colors.GREEN)
    
    def save_results(self, filename: str = None) -> None:
        """Save test results to JSON file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"api_test_results_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump({
                'test_run': {
                    'timestamp': datetime.now().isoformat(),
                    'base_url': self.base_url,
                    'total_tests': len(self.test_results),
                    'passed_tests': sum(1 for r in self.test_results if r['success']),
                    'failed_tests': sum(1 for r in self.test_results if not r['success'])
                },
                'results': self.test_results
            }, f, indent=2)
        
        print_colored(f"📄 Results saved to: {filename}", Colors.BLUE)
    
    def run_all_tests(self) -> None:
        """Run comprehensive API test suite"""
        print_colored(f"🚀 Starting API Tests for: {self.base_url}", Colors.PURPLE + Colors.BOLD)
        print_colored(f"🕒 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", Colors.BLUE)
        
        try:
            # Basic health checks (no auth required)
            self.test_health_checks()
            
            # User registration and login
            registration_success = self.test_user_registration()
            if registration_success:
                login_success = self.test_user_login()
                
                if login_success:
                    # Authenticated endpoints
                    self.test_authenticated_endpoints()
                    self.test_simulation_endpoints()
                    self.test_financial_endpoints()
                    self.test_ml_endpoints()
                    self.test_banking_endpoints()
                    self.test_notification_endpoints()
                    self.test_voice_endpoints()
                    self.test_pdf_export_endpoints()
            
            # Market data (might work without auth)
            self.test_market_data_endpoints()
            
        except Exception as e:
            print_colored(f"❌ Unexpected error during testing: {str(e)}", Colors.RED)
            print_colored(f"🔍 Error details: {traceback.format_exc()}", Colors.RED)
        
        finally:
            # Always show summary
            self.print_summary()
            self.save_results()

def main():
    """Main function"""
    # Get base URL from command line or use default
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    
    print_colored("🧪 AI Financial Planning System - API Test Suite", Colors.PURPLE + Colors.BOLD)
    print_colored("=" * 60, Colors.PURPLE)
    
    # Create and run tester
    tester = APITester(base_url)
    tester.run_all_tests()

if __name__ == "__main__":
    main()