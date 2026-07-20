#!/usr/bin/env python3
"""
Daily Demo Health Check Script

This script runs comprehensive health checks on all demos and generates reports.
It's designed to be run on a schedule (daily) to ensure demo reliability.

Features:
- Automated demo startup and testing
- Health metrics collection
- Error reporting and alerting
- Performance monitoring
- Configuration validation
- Dependency verification
"""

import asyncio
import json
import logging
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import tempfile
import requests
import psutil

# Add project root to Python path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('/tmp/daily_demo_health_check.log')
    ]
)
logger = logging.getLogger(__name__)


class DemoHealthChecker:
    """Comprehensive demo health checking system."""
    
    def __init__(self):
        self.project_root = PROJECT_ROOT
        self.backend_dir = self.project_root / "backend"
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "unknown",
            "checks": {},
            "metrics": {},
            "errors": [],
            "warnings": []
        }
        self.timeout = 120
        
    def run_command(self, command: List[str], cwd: Optional[Path] = None, timeout: int = 60) -> Tuple[int, str, str]:
        """Run a command and return exit code, stdout, stderr."""
        try:
            result = subprocess.run(
                command,
                cwd=cwd or self.backend_dir,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return 124, "", f"Command timed out after {timeout}s"
        except Exception as e:
            return 1, "", str(e)
    
    def check_system_health(self) -> Dict:
        """Check basic system health metrics."""
        logger.info("Checking system health...")
        
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            
            # Disk usage
            disk = psutil.disk_usage('/')
            
            # Check if critical ports are available
            ports_available = []
            for port in [8000, 3000, 5432, 6379]:
                try:
                    import socket
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                        s.settimeout(1)
                        result = s.connect_ex(('localhost', port))
                        ports_available.append({"port": port, "available": result != 0})
                except:
                    ports_available.append({"port": port, "available": False, "error": "check_failed"})
            
            system_health = {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_available_gb": memory.available / (1024**3),
                "disk_percent": disk.percent,
                "disk_free_gb": disk.free / (1024**3),
                "ports": ports_available,
                "status": "healthy"
            }
            
            # Determine if system is healthy
            if cpu_percent > 90:
                system_health["status"] = "warning"
                self.results["warnings"].append(f"High CPU usage: {cpu_percent}%")
            
            if memory.percent > 90:
                system_health["status"] = "critical"
                self.results["errors"].append(f"High memory usage: {memory.percent}%")
            
            if disk.percent > 90:
                system_health["status"] = "critical"
                self.results["errors"].append(f"High disk usage: {disk.percent}%")
            
            return system_health
            
        except Exception as e:
            logger.error(f"System health check failed: {e}")
            return {"status": "error", "error": str(e)}
    
    def check_dependencies(self) -> Dict:
        """Check if all required dependencies are available."""
        logger.info("Checking dependencies...")
        
        dependencies = {
            "python": {"command": ["python3", "--version"], "required": True},
            "pip": {"command": ["pip3", "--version"], "required": True},
            "docker": {"command": ["docker", "--version"], "required": False},
            "docker-compose": {"command": ["docker-compose", "--version"], "required": False},
            "node": {"command": ["node", "--version"], "required": False},
            "npm": {"command": ["npm", "--version"], "required": False}
        }
        
        python_packages = [
            "fastapi", "uvicorn", "numpy", "pydantic", "jose", "passlib",
            "scipy", "matplotlib", "reportlab", "requests", "psutil"
        ]
        
        dep_results = {}
        
        # Check system dependencies
        for name, config in dependencies.items():
            code, stdout, stderr = self.run_command(config["command"], timeout=10)
            dep_results[name] = {
                "available": code == 0,
                "version": stdout.strip() if code == 0 else None,
                "required": config["required"],
                "error": stderr if code != 0 else None
            }
            
            if config["required"] and code != 0:
                self.results["errors"].append(f"Required dependency {name} not available")
        
        # Check Python packages
        package_results = {}
        for package in python_packages:
            code, stdout, stderr = self.run_command(
                ["python3", "-c", f"import {package}; print({package}.__version__ if hasattr({package}, '__version__') else 'installed')"],
                timeout=5
            )
            package_results[package] = {
                "available": code == 0,
                "version": stdout.strip() if code == 0 else None,
                "required": package in ["fastapi", "uvicorn", "numpy", "pydantic"],
                "error": stderr if code != 0 else None
            }
        
        dep_results["python_packages"] = package_results
        
        return dep_results
    
    def check_file_integrity(self) -> Dict:
        """Check integrity of critical demo files."""
        logger.info("Checking file integrity...")
        
        critical_files = [
            "backend/working_demo.py",
            "backend/minimal_working_demo.py",
            "backend/ml_simulation_demo.py",
            "backend/cli_demo.py",
            "backend/start_demo.sh",
            "backend/requirements.txt",
            "docker-compose.yml",
            "demo-smoke-tests.sh"
        ]
        
        file_results = {}
        
        for file_path in critical_files:
            full_path = self.project_root / file_path
            file_results[file_path] = {
                "exists": full_path.exists(),
                "readable": full_path.is_file() and os.access(full_path, os.R_OK) if full_path.exists() else False,
                "size_bytes": full_path.stat().st_size if full_path.exists() else 0,
                "executable": os.access(full_path, os.X_OK) if full_path.suffix == '.sh' and full_path.exists() else None
            }
            
            if not full_path.exists():
                self.results["errors"].append(f"Critical file missing: {file_path}")
            elif not (full_path.is_file() and os.access(full_path, os.R_OK)):
                self.results["errors"].append(f"File not readable: {file_path}")
        
        return file_results
    
    def check_demo_startup(self, demo_name: str, demo_script: str, timeout: int = 60) -> Dict:
        """Test if a demo can start up successfully."""
        logger.info(f"Testing demo startup: {demo_name}")
        
        try:
            # Start demo process
            process = subprocess.Popen(
                ["python3", demo_script],
                cwd=self.backend_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait for startup or timeout
            start_time = time.time()
            api_ready = False
            
            while time.time() - start_time < timeout:
                if process.poll() is not None:
                    # Process ended prematurely
                    stdout, stderr = process.communicate()
                    return {
                        "status": "failed",
                        "error": "Process ended prematurely",
                        "exit_code": process.returncode,
                        "stdout": stdout[-500:],  # Last 500 chars
                        "stderr": stderr[-500:],
                        "startup_time": time.time() - start_time
                    }
                
                # Try to connect to API
                try:
                    response = requests.get("http://localhost:8000/health", timeout=2)
                    if response.status_code == 200:
                        api_ready = True
                        break
                except:
                    pass
                
                time.sleep(2)
            
            # Test API endpoints if ready
            endpoint_results = {}
            if api_ready:
                endpoints = ["/health", "/docs", "/openapi.json"]
                for endpoint in endpoints:
                    try:
                        resp = requests.get(f"http://localhost:8000{endpoint}", timeout=5)
                        endpoint_results[endpoint] = {
                            "status_code": resp.status_code,
                            "response_time": resp.elapsed.total_seconds(),
                            "success": 200 <= resp.status_code < 300
                        }
                    except Exception as e:
                        endpoint_results[endpoint] = {
                            "success": False,
                            "error": str(e)
                        }
            
            # Clean up process
            try:
                process.terminate()
                process.wait(timeout=10)
            except:
                process.kill()
                process.wait(timeout=5)
            
            return {
                "status": "success" if api_ready else "timeout",
                "api_ready": api_ready,
                "startup_time": time.time() - start_time,
                "endpoints": endpoint_results if api_ready else {},
                "process_ended": process.poll() is not None
            }
            
        except Exception as e:
            logger.error(f"Demo startup test failed for {demo_name}: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def check_docker_health(self) -> Dict:
        """Check Docker and docker-compose configuration."""
        logger.info("Checking Docker health...")
        
        docker_results = {}
        
        # Check if Docker is available and running
        code, stdout, stderr = self.run_command(["docker", "info"], timeout=15)
        docker_results["docker_available"] = code == 0
        docker_results["docker_info"] = stdout if code == 0 else stderr
        
        if code == 0:
            # Test docker-compose files
            compose_files = ["docker-compose.yml", "docker-compose.demo.yml"]
            compose_results = {}
            
            for compose_file in compose_files:
                compose_path = self.project_root / compose_file
                if compose_path.exists():
                    code, stdout, stderr = self.run_command(
                        ["docker-compose", "-f", str(compose_path), "config"],
                        cwd=self.project_root,
                        timeout=30
                    )
                    compose_results[compose_file] = {
                        "valid": code == 0,
                        "error": stderr if code != 0 else None
                    }
                else:
                    compose_results[compose_file] = {
                        "valid": False,
                        "error": "File not found"
                    }
            
            docker_results["compose_files"] = compose_results
        
        return docker_results
    
    def run_smoke_tests(self) -> Dict:
        """Run the demo smoke tests."""
        logger.info("Running smoke tests...")
        
        smoke_test_script = self.project_root / "demo-smoke-tests.sh"
        if not smoke_test_script.exists():
            return {
                "status": "skipped",
                "error": "Smoke test script not found"
            }
        
        code, stdout, stderr = self.run_command(
            ["bash", str(smoke_test_script), "--quick", "--verbose"],
            cwd=self.project_root,
            timeout=180
        )
        
        # Parse results from stdout
        passed_tests = stdout.count("[PASS]") if stdout else 0
        failed_tests = stdout.count("[FAIL]") if stdout else 0
        skipped_tests = stdout.count("[SKIP]") if stdout else 0
        
        return {
            "status": "success" if code == 0 else "failed",
            "exit_code": code,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "skipped_tests": skipped_tests,
            "stdout": stdout[-1000:] if stdout else "",  # Last 1000 chars
            "stderr": stderr[-500:] if stderr else ""
        }
    
    def generate_performance_metrics(self) -> Dict:
        """Generate performance metrics for demos."""
        logger.info("Generating performance metrics...")
        
        metrics = {}
        
        # Test ML simulation performance
        try:
            start_time = time.time()
            code, stdout, stderr = self.run_command(
                ["python3", "simple_ml_test.py"],
                timeout=60
            )
            ml_time = time.time() - start_time
            
            metrics["ml_simulation"] = {
                "execution_time": ml_time,
                "success": code == 0,
                "error": stderr if code != 0 else None
            }
        except Exception as e:
            metrics["ml_simulation"] = {"error": str(e)}
        
        # Test API response times
        try:
            # Start minimal demo briefly
            process = subprocess.Popen(
                ["python3", "minimal_working_demo.py"],
                cwd=self.backend_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Wait for startup
            time.sleep(10)
            
            # Test response times
            api_metrics = {}
            endpoints = ["/health", "/docs"]
            
            for endpoint in endpoints:
                try:
                    start_time = time.time()
                    response = requests.get(f"http://localhost:8000{endpoint}", timeout=10)
                    response_time = time.time() - start_time
                    
                    api_metrics[endpoint] = {
                        "response_time": response_time,
                        "status_code": response.status_code,
                        "success": response.status_code == 200
                    }
                except Exception as e:
                    api_metrics[endpoint] = {"error": str(e)}
            
            metrics["api_performance"] = api_metrics
            
            # Clean up
            process.terminate()
            process.wait(timeout=10)
            
        except Exception as e:
            metrics["api_performance"] = {"error": str(e)}
        
        return metrics
    
    def run_all_checks(self) -> Dict:
        """Run all health checks and return comprehensive results."""
        logger.info("Starting comprehensive demo health check...")
        
        start_time = time.time()
        
        try:
            # System health
            self.results["checks"]["system"] = self.check_system_health()
            
            # Dependencies
            self.results["checks"]["dependencies"] = self.check_dependencies()
            
            # File integrity
            self.results["checks"]["files"] = self.check_file_integrity()
            
            # Docker health
            self.results["checks"]["docker"] = self.check_docker_health()
            
            # Smoke tests
            self.results["checks"]["smoke_tests"] = self.run_smoke_tests()
            
            # Demo startup tests (sample a few key demos)
            demo_tests = {}
            key_demos = [
                ("minimal", "minimal_working_demo.py"),
                ("ml_simulation", "ml_simulation_demo.py")
            ]
            
            for demo_name, demo_script in key_demos:
                demo_tests[demo_name] = self.check_demo_startup(demo_name, demo_script, timeout=90)
            
            self.results["checks"]["demo_startup"] = demo_tests
            
            # Performance metrics
            self.results["metrics"] = self.generate_performance_metrics()
            
        except Exception as e:
            logger.error(f"Health check failed with exception: {e}")
            self.results["errors"].append(f"Health check exception: {str(e)}")
        
        # Determine overall status
        total_time = time.time() - start_time
        self.results["execution_time"] = total_time
        
        # Calculate overall status
        if len(self.results["errors"]) == 0:
            if len(self.results["warnings"]) == 0:
                self.results["overall_status"] = "healthy"
            else:
                self.results["overall_status"] = "warning"
        else:
            self.results["overall_status"] = "unhealthy"
        
        logger.info(f"Health check completed in {total_time:.2f}s - Status: {self.results['overall_status']}")
        
        return self.results
    
    def save_report(self, filename: Optional[str] = None) -> str:
        """Save health check report to file."""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"/tmp/demo_health_report_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        logger.info(f"Health report saved to: {filename}")
        return filename
    
    def print_summary(self):
        """Print a summary of health check results."""
        print("\n" + "="*60)
        print(f"DEMO HEALTH CHECK SUMMARY - {self.results['timestamp']}")
        print("="*60)
        
        print(f"Overall Status: {self.results['overall_status'].upper()}")
        print(f"Execution Time: {self.results.get('execution_time', 0):.2f}s")
        print()
        
        if self.results["errors"]:
            print("ERRORS:")
            for error in self.results["errors"]:
                print(f"  ❌ {error}")
            print()
        
        if self.results["warnings"]:
            print("WARNINGS:")
            for warning in self.results["warnings"]:
                print(f"  ⚠️  {warning}")
            print()
        
        # Check summaries
        print("CHECK RESULTS:")
        for check_name, check_result in self.results["checks"].items():
            if isinstance(check_result, dict) and "status" in check_result:
                status = check_result["status"]
                if status == "healthy" or status == "success":
                    print(f"  ✅ {check_name}: {status}")
                elif status == "warning":
                    print(f"  ⚠️  {check_name}: {status}")
                else:
                    print(f"  ❌ {check_name}: {status}")
            else:
                print(f"  ℹ️  {check_name}: completed")
        
        print("\n" + "="*60)


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Daily Demo Health Check")
    parser.add_argument("--save-report", help="Save report to specific file")
    parser.add_argument("--quiet", "-q", action="store_true", help="Quiet mode - minimal output")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")
    
    args = parser.parse_args()
    
    # Configure logging level
    if args.quiet:
        logging.getLogger().setLevel(logging.WARNING)
    
    # Run health check
    checker = DemoHealthChecker()
    results = checker.run_all_checks()
    
    # Save report
    report_file = checker.save_report(args.save_report)
    
    # Output results
    if args.json:
        print(json.dumps(results, indent=2, default=str))
    elif not args.quiet:
        checker.print_summary()
    
    # Exit with appropriate code
    if results["overall_status"] == "healthy":
        sys.exit(0)
    elif results["overall_status"] == "warning":
        sys.exit(1)
    else:
        sys.exit(2)


if __name__ == "__main__":
    main()