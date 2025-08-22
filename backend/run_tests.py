#!/usr/bin/env python3
"""
Comprehensive Test Runner for Financial Planning System

This script provides a unified interface for running all types of tests:
- Unit tests
- Integration tests
- End-to-end tests
- Security tests
- Performance tests
- Demo test suite

Usage:
python run_tests.py --suite all
python run_tests.py --suite demo --generate-data
python run_tests.py --suite unit --coverage
python run_tests.py --quick --parallel
"""

import argparse
import asyncio
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import shutil

# ANSI color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class TestRunner:
    """Comprehensive test runner for the Financial Planning System"""
    
    def __init__(self, args):
        self.args = args
        self.start_time = time.time()
        self.results = {}
        self.reports_dir = Path("reports")
        self.reports_dir.mkdir(exist_ok=True)
        
        # Test suite configurations
        self.test_suites = {
            "unit": {
                "path": "tests/unit/",
                "description": "Unit tests with mocking",
                "timeout": 300,
                "parallel": True
            },
            "integration": {
                "path": "tests/integration/",
                "description": "Integration tests with real services",
                "timeout": 600,
                "parallel": False
            },
            "e2e": {
                "path": "tests/e2e/",
                "description": "End-to-end browser tests",
                "timeout": 1200,
                "parallel": False
            },
            "demo": {
                "path": "test_demo.py",
                "description": "Comprehensive demo test suite",
                "timeout": 900,
                "parallel": False
            },
            "security": {
                "path": "tests/security/",
                "description": "Security and vulnerability tests",
                "timeout": 300,
                "parallel": True
            },
            "performance": {
                "path": "tests/performance/",
                "description": "Performance and load tests",
                "timeout": 600,
                "parallel": False
            }
        }
    
    def print_header(self, message: str):
        """Print a formatted header"""
        print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}{message.center(60)}{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}\n")
    
    def print_success(self, message: str):
        """Print success message"""
        print(f"{Colors.OKGREEN}✅ {message}{Colors.ENDC}")
    
    def print_warning(self, message: str):
        """Print warning message"""
        print(f"{Colors.WARNING}⚠️  {message}{Colors.ENDC}")
    
    def print_error(self, message: str):
        """Print error message"""
        print(f"{Colors.FAIL}❌ {message}{Colors.ENDC}")
    
    def print_info(self, message: str):
        """Print info message"""
        print(f"{Colors.OKBLUE}ℹ️  {message}{Colors.ENDC}")
    
    def check_dependencies(self) -> bool:
        """Check if all required dependencies are available"""
        self.print_info("Checking dependencies...")
        
        required_tools = {
            "python": "Python interpreter",
            "pytest": "Pytest testing framework",
            "docker-compose": "Docker Compose for services",
        }
        
        missing_tools = []
        
        for tool, description in required_tools.items():
            if not shutil.which(tool):
                missing_tools.append(f"{tool} ({description})")
        
        if missing_tools:
            self.print_error("Missing required tools:")
            for tool in missing_tools:
                print(f"  - {tool}")
            print("\nInstall missing tools and try again.")
            return False
        
        self.print_success("All dependencies available")
        return True
    
    def setup_environment(self) -> bool:
        """Set up the test environment"""
        self.print_info("Setting up test environment...")
        
        # Check if services are running
        try:
            # Check if Docker services are running
            result = subprocess.run(
                ["docker-compose", "ps", "--services", "--filter", "status=running"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            running_services = result.stdout.strip().split('\n') if result.stdout.strip() else []
            required_services = ["postgres", "redis"]
            
            missing_services = [svc for svc in required_services if svc not in running_services]
            
            if missing_services:
                self.print_warning(f"Starting required services: {', '.join(missing_services)}")
                subprocess.run(
                    ["docker-compose", "up", "-d"] + missing_services,
                    check=True,
                    timeout=60
                )
                
                # Wait for services to be ready
                self.print_info("Waiting for services to be ready...")
                time.sleep(10)
            
            # Run database migrations
            self.print_info("Running database migrations...")
            env = os.environ.copy()
            env.update({
                "DATABASE_URL": "postgresql://financial_planning:financial_planning@localhost:5432/financial_planning",
                "ENVIRONMENT": "testing"
            })
            
            subprocess.run(
                ["alembic", "upgrade", "head"],
                check=True,
                env=env,
                timeout=30
            )
            
            self.print_success("Test environment ready")
            return True
            
        except subprocess.CalledProcessError as e:
            self.print_error(f"Failed to set up environment: {e}")
            return False
        except subprocess.TimeoutExpired:
            self.print_error("Timeout setting up environment")
            return False
    
    def generate_demo_data(self) -> bool:
        """Generate demo data for testing"""
        if not self.args.generate_data:
            return True
            
        self.print_info("Generating demo data...")
        
        try:
            cmd = [
                "python", "tests/demo_data_generator.py",
                "--scenario", "comprehensive",
                "--users", str(self.args.demo_users or 10),
                "--output", "tests/demo_data.json"
            ]
            
            result = subprocess.run(cmd, check=True, timeout=120)
            self.print_success("Demo data generated successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            self.print_error(f"Failed to generate demo data: {e}")
            return False
        except subprocess.TimeoutExpired:
            self.print_error("Timeout generating demo data")
            return False
    
    def run_health_check(self) -> bool:
        """Run system health check"""
        self.print_info("Running health check...")
        
        try:
            cmd = ["python", "health_check.py"]
            if self.args.verbose:
                cmd.append("--detailed")
            
            result = subprocess.run(
                cmd,
                check=True,
                timeout=60,
                env={**os.environ, "TESTING": "true"}
            )
            
            self.print_success("Health check passed")
            return True
            
        except subprocess.CalledProcessError as e:
            self.print_error(f"Health check failed: {e}")
            return False
        except subprocess.TimeoutExpired:
            self.print_error("Health check timeout")
            return False
    
    def run_test_suite(self, suite_name: str) -> Tuple[bool, Dict]:
        """Run a specific test suite"""
        suite_config = self.test_suites[suite_name]
        
        self.print_info(f"Running {suite_name} tests: {suite_config['description']}")
        
        # Build pytest command
        cmd = ["pytest", suite_config["path"], "-v"]
        
        # Add common options
        cmd.extend([
            "--tb=short",
            f"--junit-xml=reports/{suite_name}-results.xml",
            f"--html=reports/{suite_name}-tests.html",
            "--self-contained-html"
        ])
        
        # Suite-specific options
        if suite_name == "unit" and self.args.coverage:
            cmd.extend([
                "--cov=app",
                "--cov-report=html",
                "--cov-report=xml",
                "--cov-report=term-missing"
            ])
        
        if suite_name == "e2e":
            if self.args.headless:
                cmd.append("--headless")
        
        if suite_name == "performance":
            cmd.extend([
                "--benchmark-json=reports/benchmark-results.json"
            ])
        
        # Parallel execution
        if suite_config["parallel"] and self.args.parallel:
            cmd.extend(["-n", "auto"])
        
        # Timeout
        timeout = suite_config["timeout"]
        if self.args.quick and suite_name in ["unit", "integration"]:
            timeout = min(timeout, 180)  # Limit to 3 minutes for quick tests
        
        # Environment variables
        env = os.environ.copy()
        env.update({
            "DATABASE_URL": "postgresql://financial_planning:financial_planning@localhost:5432/financial_planning",
            "REDIS_URL": "redis://localhost:6379",
            "SECRET_KEY": "test-secret-key-change-in-production",
            "ENVIRONMENT": "testing",
            "TESTING": "true",
            "LOG_LEVEL": "DEBUG" if self.args.verbose else "INFO"
        })
        
        # Run the tests
        start_time = time.time()
        try:
            result = subprocess.run(
                cmd,
                timeout=timeout,
                env=env,
                capture_output=not self.args.verbose,
                text=True
            )
            
            duration = time.time() - start_time
            success = result.returncode == 0
            
            suite_result = {
                "success": success,
                "duration": round(duration, 2),
                "return_code": result.returncode,
                "command": " ".join(cmd)
            }
            
            if success:
                self.print_success(f"{suite_name} tests passed ({duration:.1f}s)")
            else:
                self.print_error(f"{suite_name} tests failed ({duration:.1f}s)")
                if not self.args.verbose and result.stdout:
                    print(f"STDOUT:\n{result.stdout[-1000:]}")  # Last 1000 chars
                if not self.args.verbose and result.stderr:
                    print(f"STDERR:\n{result.stderr[-1000:]}")  # Last 1000 chars
            
            return success, suite_result
            
        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            self.print_error(f"{suite_name} tests timed out after {duration:.1f}s")
            return False, {
                "success": False,
                "duration": round(duration, 2),
                "return_code": -1,
                "error": "timeout"
            }
        except Exception as e:
            duration = time.time() - start_time
            self.print_error(f"{suite_name} tests failed with error: {e}")
            return False, {
                "success": False,
                "duration": round(duration, 2),
                "return_code": -1,
                "error": str(e)
            }
    
    def run_security_checks(self) -> Tuple[bool, Dict]:
        """Run security checks"""
        self.print_info("Running security checks...")
        
        results = {"bandit": None, "safety": None, "tests": None}
        overall_success = True
        
        # Bandit static analysis
        try:
            cmd = ["bandit", "-r", "app/", "-f", "json", "-o", "reports/bandit-report.json"]
            result = subprocess.run(cmd, timeout=60, capture_output=True)
            results["bandit"] = {"success": result.returncode == 0, "return_code": result.returncode}
            if result.returncode != 0:
                self.print_warning("Bandit found security issues")
            else:
                self.print_success("Bandit security check passed")
        except Exception as e:
            results["bandit"] = {"success": False, "error": str(e)}
            self.print_warning(f"Bandit check failed: {e}")
        
        # Safety dependency check
        try:
            cmd = ["safety", "check", "--json", "--output", "reports/safety-report.json"]
            result = subprocess.run(cmd, timeout=60, capture_output=True)
            results["safety"] = {"success": result.returncode == 0, "return_code": result.returncode}
            if result.returncode != 0:
                self.print_warning("Safety found vulnerable dependencies")
            else:
                self.print_success("Safety dependency check passed")
        except Exception as e:
            results["safety"] = {"success": False, "error": str(e)}
            self.print_warning(f"Safety check failed: {e}")
        
        # Security tests
        if Path("tests/security").exists():
            success, test_results = self.run_test_suite("security")
            results["tests"] = test_results
            if not success:
                overall_success = False
        
        return overall_success, results
    
    def generate_report(self) -> Dict:
        """Generate comprehensive test report"""
        total_duration = time.time() - self.start_time
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "duration_seconds": round(total_duration, 2),
            "configuration": {
                "suite": self.args.suite,
                "quick": self.args.quick,
                "parallel": self.args.parallel,
                "coverage": self.args.coverage,
                "headless": self.args.headless,
                "verbose": self.args.verbose
            },
            "results": self.results,
            "summary": {
                "total_suites": len(self.results),
                "passed_suites": sum(1 for r in self.results.values() if r.get("success", False)),
                "failed_suites": sum(1 for r in self.results.values() if not r.get("success", False))
            }
        }
        
        # Save report
        report_file = self.reports_dir / "comprehensive-test-report.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        return report
    
    def print_summary(self, report: Dict):
        """Print test run summary"""
        self.print_header("TEST RUN SUMMARY")
        
        print(f"🕐 Total Duration: {report['duration_seconds']:.1f} seconds")
        print(f"📊 Test Suites Run: {report['summary']['total_suites']}")
        print(f"✅ Passed: {report['summary']['passed_suites']}")
        print(f"❌ Failed: {report['summary']['failed_suites']}")
        
        print(f"\n📋 Suite Results:")
        for suite_name, result in self.results.items():
            status = "✅ PASS" if result.get("success", False) else "❌ FAIL"
            duration = result.get("duration", 0)
            print(f"  {status} {suite_name:12} ({duration:.1f}s)")
        
        print(f"\n📄 Reports generated in: {self.reports_dir}")
        
        if report['summary']['failed_suites'] == 0:
            self.print_success("All tests passed! 🎉")
        else:
            self.print_error(f"{report['summary']['failed_suites']} test suite(s) failed")
    
    def run(self) -> int:
        """Main test runner entry point"""
        try:
            self.print_header("FINANCIAL PLANNING SYSTEM - TEST RUNNER")
            
            # Dependency check
            if not self.check_dependencies():
                return 1
            
            # Environment setup
            if not self.setup_environment():
                return 1
            
            # Generate demo data if requested
            if not self.generate_demo_data():
                return 1
            
            # Health check
            if not self.run_health_check():
                self.print_warning("Health check failed, but continuing with tests...")
            
            # Determine which suites to run
            if self.args.suite == "all":
                suites_to_run = list(self.test_suites.keys())
            elif self.args.suite == "quick":
                suites_to_run = ["unit", "integration"]
            else:
                suites_to_run = [self.args.suite]
            
            self.print_info(f"Running test suites: {', '.join(suites_to_run)}")
            
            # Run test suites
            overall_success = True
            for suite_name in suites_to_run:
                if suite_name == "security":
                    success, result = self.run_security_checks()
                else:
                    success, result = self.run_test_suite(suite_name)
                
                self.results[suite_name] = result
                if not success:
                    overall_success = False
                    
                    if self.args.fail_fast:
                        self.print_error("Stopping due to --fail-fast")
                        break
            
            # Generate and display report
            report = self.generate_report()
            self.print_summary(report)
            
            return 0 if overall_success else 1
            
        except KeyboardInterrupt:
            self.print_warning("Test run interrupted by user")
            return 130
        except Exception as e:
            self.print_error(f"Unexpected error: {e}")
            return 1


def main():
    parser = argparse.ArgumentParser(
        description="Comprehensive test runner for Financial Planning System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_tests.py --suite all                    # Run all test suites
  python run_tests.py --suite demo --generate-data   # Run demo with data generation
  python run_tests.py --suite unit --coverage        # Unit tests with coverage
  python run_tests.py --quick --parallel             # Quick tests in parallel
  python run_tests.py --suite e2e --headless         # Headless browser tests
        """
    )
    
    parser.add_argument(
        "--suite",
        choices=["all", "quick", "unit", "integration", "e2e", "demo", "security", "performance"],
        default="quick",
        help="Test suite to run (default: quick)"
    )
    
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Generate coverage reports for unit tests"
    )
    
    parser.add_argument(
        "--parallel",
        action="store_true",
        help="Run tests in parallel where possible"
    )
    
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run browser tests in headless mode"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Verbose output"
    )
    
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Quick mode with reduced timeouts"
    )
    
    parser.add_argument(
        "--fail-fast",
        action="store_true",
        help="Stop on first test suite failure"
    )
    
    parser.add_argument(
        "--generate-data",
        action="store_true",
        help="Generate demo data before running tests"
    )
    
    parser.add_argument(
        "--demo-users",
        type=int,
        default=10,
        help="Number of demo users to generate (default: 10)"
    )
    
    args = parser.parse_args()
    
    # Override suite for quick mode
    if args.quick and args.suite == "quick":
        args.suite = "quick"
    
    runner = TestRunner(args)
    exit_code = runner.run()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()