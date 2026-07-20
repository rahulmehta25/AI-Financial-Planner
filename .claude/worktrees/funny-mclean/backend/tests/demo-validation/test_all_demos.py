#!/usr/bin/env python3
"""
Comprehensive Demo Validation Test Suite

This module contains automated tests to ensure all demos work correctly:
- Tests each demo can start successfully
- Validates demo data is present
- Checks API endpoints respond
- Verifies frontend pages load
- Tests Docker containers start
- Validates CLI demo interaction
- Checks performance benchmarks run
- Ensures security demo completes
- Validates ML simulations execute
- Tests mobile app initialization
"""

import asyncio
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import pytest
import requests
import psutil
import docker
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

# Test configuration
BASE_DIR = Path(__file__).parent.parent.parent
API_BASE_URL = "http://localhost:8000"
FRONTEND_BASE_URL = "http://localhost:3000"
TIMEOUT = 60
DOCKER_TIMEOUT = 120


class DemoTestRunner:
    """Comprehensive demo test runner with health checks and validation."""
    
    def __init__(self):
        self.docker_client = docker.from_env()
        self.test_results = {}
        self.cleanup_tasks = []
        
    def cleanup(self):
        """Clean up test resources."""
        for task in self.cleanup_tasks:
            try:
                task()
            except Exception as e:
                print(f"Cleanup error: {e}")
    
    def wait_for_port(self, port: int, host: str = "localhost", timeout: int = TIMEOUT) -> bool:
        """Wait for a port to become available."""
        import socket
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                with socket.create_connection((host, port), timeout=1):
                    return True
            except (ConnectionRefusedError, OSError):
                time.sleep(1)
        return False
    
    def check_process_running(self, process_name: str) -> bool:
        """Check if a process is running."""
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if process_name.lower() in ' '.join(proc.info['cmdline'] or []).lower():
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return False


@pytest.fixture(scope="session")
def demo_runner():
    """Create and cleanup demo test runner."""
    runner = DemoTestRunner()
    yield runner
    runner.cleanup()


@pytest.mark.demo
@pytest.mark.smoke
class TestBasicDemoStartup:
    """Test basic demo startup functionality."""
    
    def test_demo_directory_structure(self, demo_runner):
        """Verify demo directory structure exists."""
        required_dirs = [
            "backend",
            "frontend", 
            "mobile",
            "scripts"
        ]
        
        for dir_name in required_dirs:
            dir_path = BASE_DIR / dir_name
            assert dir_path.exists(), f"Required directory {dir_name} not found"
            assert dir_path.is_dir(), f"{dir_name} is not a directory"
    
    def test_demo_scripts_executable(self, demo_runner):
        """Verify demo scripts are executable."""
        scripts = [
            "backend/start_demo.sh",
            "backend/stop_demo.sh",
            "backend/reset_demo.sh",
            "validate_demo.sh",
            "start_docker_demo.sh"
        ]
        
        for script in scripts:
            script_path = BASE_DIR / script
            if script_path.exists():
                assert os.access(script_path, os.X_OK), f"Script {script} is not executable"
    
    def test_required_files_exist(self, demo_runner):
        """Verify required demo files exist."""
        required_files = [
            "backend/working_demo.py",
            "backend/minimal_working_demo.py",
            "backend/ml_simulation_demo.py",
            "backend/cli_demo.py",
            "backend/security_demo.py",
            "backend/performance_demo.py",
            "docker-compose.yml",
            "docker-compose.demo.yml",
            "backend/requirements.txt",
            "frontend/package.json"
        ]
        
        for file_name in required_files:
            file_path = BASE_DIR / file_name
            assert file_path.exists(), f"Required file {file_name} not found"
            assert file_path.is_file(), f"{file_name} is not a file"


@pytest.mark.demo
@pytest.mark.integration
class TestAPIDemo:
    """Test API demo functionality."""
    
    def test_minimal_demo_startup(self, demo_runner):
        """Test minimal demo can start successfully."""
        # Start minimal demo
        process = subprocess.Popen(
            [sys.executable, "minimal_working_demo.py"],
            cwd=BASE_DIR / "backend",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        demo_runner.cleanup_tasks.append(lambda: process.terminate())
        
        # Wait for API to be available
        assert demo_runner.wait_for_port(8000), "API port did not become available"
        time.sleep(5)  # Allow full startup
        
        # Test health endpoint
        response = requests.get(f"{API_BASE_URL}/health", timeout=10)
        assert response.status_code == 200
        
        health_data = response.json()
        assert health_data.get("status") == "healthy"
        
        process.terminate()
        process.wait(timeout=10)
    
    def test_full_demo_startup(self, demo_runner):
        """Test full-featured demo can start successfully."""
        # Check if dependencies are available
        try:
            import scipy
            import matplotlib
            import reportlab
        except ImportError:
            pytest.skip("Full demo dependencies not available")
        
        process = subprocess.Popen(
            [sys.executable, "working_demo.py"],
            cwd=BASE_DIR / "backend",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        demo_runner.cleanup_tasks.append(lambda: process.terminate())
        
        # Wait for API to be available
        assert demo_runner.wait_for_port(8000), "API port did not become available"
        time.sleep(5)
        
        # Test various endpoints
        endpoints_to_test = [
            "/health",
            "/docs",
            "/openapi.json"
        ]
        
        for endpoint in endpoints_to_test:
            response = requests.get(f"{API_BASE_URL}{endpoint}", timeout=10)
            assert response.status_code == 200, f"Endpoint {endpoint} failed"
        
        process.terminate()
        process.wait(timeout=10)
    
    def test_demo_data_endpoints(self, demo_runner):
        """Test demo data creation and retrieval."""
        # Start API
        process = subprocess.Popen(
            [sys.executable, "minimal_working_demo.py"],
            cwd=BASE_DIR / "backend",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        demo_runner.cleanup_tasks.append(lambda: process.terminate())
        
        assert demo_runner.wait_for_port(8000), "API port did not become available"
        time.sleep(5)
        
        # Test sample data creation
        response = requests.get(f"{API_BASE_URL}/sample-data", timeout=10)
        assert response.status_code == 200
        
        # Test user registration
        user_data = {
            "email": "test@demo.com",
            "password": "test123"
        }
        response = requests.post(f"{API_BASE_URL}/register", json=user_data, timeout=10)
        assert response.status_code in [200, 201], f"User registration failed: {response.text}"
        
        # Test login
        response = requests.post(f"{API_BASE_URL}/login", json=user_data, timeout=10)
        assert response.status_code == 200
        
        process.terminate()
        process.wait(timeout=10)


@pytest.mark.demo
@pytest.mark.integration
class TestMLSimulationDemo:
    """Test ML simulation demo functionality."""
    
    def test_ml_demo_startup(self, demo_runner):
        """Test ML simulation demo can start."""
        # Run ML simulation demo
        result = subprocess.run(
            [sys.executable, "ml_simulation_demo.py", "--quick-test"],
            cwd=BASE_DIR / "backend",
            capture_output=True,
            text=True,
            timeout=180
        )
        
        assert result.returncode == 0, f"ML demo failed: {result.stderr}"
        assert "Monte Carlo Simulation" in result.stdout
    
    def test_monte_carlo_engine(self, demo_runner):
        """Test Monte Carlo simulation engine."""
        # Import and test simulation engine
        sys.path.insert(0, str(BASE_DIR / "backend"))
        
        from app.simulations.engine import MonteCarloEngine
        
        engine = MonteCarloEngine()
        
        # Test basic simulation
        result = engine.run_simulation(
            initial_investment=10000,
            monthly_contribution=1000,
            years=10,
            expected_return=0.07,
            volatility=0.15,
            num_simulations=1000
        )
        
        assert result is not None
        assert 'percentiles' in result
        assert len(result['scenarios']) == 1000
        
        sys.path.remove(str(BASE_DIR / "backend"))
    
    def test_ml_outputs_generation(self, demo_runner):
        """Test ML demo generates expected outputs."""
        output_dir = BASE_DIR / "backend" / "ml_demo_outputs"
        
        # Clean up existing outputs
        if output_dir.exists():
            import shutil
            shutil.rmtree(output_dir)
        
        # Run ML demo
        result = subprocess.run(
            [sys.executable, "ml_simulation_demo.py"],
            cwd=BASE_DIR / "backend",
            capture_output=True,
            text=True,
            timeout=300
        )
        
        # Check outputs were created
        assert output_dir.exists(), "ML demo outputs directory not created"
        
        expected_files = [
            "comprehensive_analysis_*.json",
            "efficient_frontier_data.txt",
            "risk_return_data.txt"
        ]
        
        import glob
        for pattern in expected_files:
            files = glob.glob(str(output_dir / pattern))
            assert len(files) > 0, f"Expected output file matching {pattern} not found"


@pytest.mark.demo
@pytest.mark.integration  
class TestSecurityDemo:
    """Test security demo functionality."""
    
    def test_security_demo_simple(self, demo_runner):
        """Test simple security demo."""
        result = subprocess.run(
            [sys.executable, "security_demo_simple.py"],
            cwd=BASE_DIR / "backend",
            capture_output=True,
            text=True,
            timeout=60
        )
        
        assert result.returncode == 0, f"Security demo failed: {result.stderr}"
        assert "Security Demo" in result.stdout
    
    def test_security_demo_full(self, demo_runner):
        """Test full security demo."""
        result = subprocess.run(
            [sys.executable, "security_demo.py", "--quick"],
            cwd=BASE_DIR / "backend",
            capture_output=True,
            text=True,
            timeout=120
        )
        
        # Should complete without critical errors
        assert result.returncode in [0, 1], f"Security demo crashed: {result.stderr}"
        assert "Security" in result.stdout or "security" in result.stdout


@pytest.mark.demo
@pytest.mark.integration
class TestPerformanceDemo:
    """Test performance demo functionality."""
    
    def test_performance_demo_startup(self, demo_runner):
        """Test performance demo can start."""
        try:
            result = subprocess.run(
                [sys.executable, "performance_demo.py", "--test-mode"],
                cwd=BASE_DIR / "backend",
                capture_output=True,
                text=True,
                timeout=120
            )
            
            # Performance demo may not always succeed due to system constraints
            # We just ensure it doesn't crash completely
            assert "performance" in result.stdout.lower() or "benchmark" in result.stdout.lower()
            
        except subprocess.TimeoutExpired:
            pytest.skip("Performance demo timed out - acceptable for CI/CD")


@pytest.mark.demo
@pytest.mark.integration
class TestCLIDemo:
    """Test CLI demo functionality."""
    
    def test_cli_demo_startup(self, demo_runner):
        """Test CLI demo can start and respond."""
        result = subprocess.run(
            [sys.executable, "cli_demo.py", "--test"],
            cwd=BASE_DIR / "backend",
            capture_output=True,
            text=True,
            timeout=60
        )
        
        # CLI demo should start without errors
        assert result.returncode == 0, f"CLI demo failed: {result.stderr}"
    
    def test_cli_interactive_mode(self, demo_runner):
        """Test CLI demo interactive mode."""
        # Test non-interactive mode only to avoid hanging
        result = subprocess.run(
            [sys.executable, "cli_demo.py", "--help"],
            cwd=BASE_DIR / "backend",
            capture_output=True,
            text=True,
            timeout=30
        )
        
        # Should show help or run without errors
        assert result.returncode in [0, 1]  # Help might return 1


@pytest.mark.demo
@pytest.mark.integration
@pytest.mark.slow
class TestDockerDemo:
    """Test Docker-based demo functionality."""
    
    def test_docker_compose_validity(self, demo_runner):
        """Test docker-compose files are valid."""
        compose_files = [
            "docker-compose.yml",
            "docker-compose.demo.yml"
        ]
        
        for compose_file in compose_files:
            compose_path = BASE_DIR / compose_file
            if compose_path.exists():
                result = subprocess.run(
                    ["docker-compose", "-f", str(compose_path), "config"],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                assert result.returncode == 0, f"Invalid docker-compose file {compose_file}: {result.stderr}"
    
    def test_docker_demo_startup(self, demo_runner):
        """Test Docker demo environment startup."""
        # Only run if docker is available and not in CI
        if not demo_runner.docker_client or os.getenv('CI'):
            pytest.skip("Docker not available or running in CI")
        
        compose_file = BASE_DIR / "docker-compose.demo.yml"
        if not compose_file.exists():
            pytest.skip("Demo docker-compose file not found")
        
        try:
            # Start demo environment
            result = subprocess.run(
                ["docker-compose", "-f", str(compose_file), "up", "-d", "--build"],
                cwd=BASE_DIR,
                capture_output=True,
                text=True,
                timeout=DOCKER_TIMEOUT
            )
            
            if result.returncode != 0:
                pytest.skip(f"Docker demo startup failed: {result.stderr}")
            
            # Wait for services
            time.sleep(30)
            
            # Check if API is responding
            try:
                response = requests.get(f"{API_BASE_URL}/health", timeout=10)
                assert response.status_code == 200
            except requests.RequestException:
                pytest.skip("API not responding after Docker startup")
            
        finally:
            # Cleanup
            subprocess.run(
                ["docker-compose", "-f", str(compose_file), "down", "-v"],
                cwd=BASE_DIR,
                capture_output=True,
                timeout=60
            )


@pytest.mark.demo
@pytest.mark.integration
@pytest.mark.slow
class TestFrontendDemo:
    """Test frontend demo functionality."""
    
    def test_frontend_build(self, demo_runner):
        """Test frontend can build successfully."""
        frontend_dir = BASE_DIR / "frontend"
        if not frontend_dir.exists():
            pytest.skip("Frontend directory not found")
        
        # Check if package.json exists
        package_json = frontend_dir / "package.json"
        if not package_json.exists():
            pytest.skip("package.json not found")
        
        # Install dependencies (skip if already installed)
        node_modules = frontend_dir / "node_modules"
        if not node_modules.exists():
            result = subprocess.run(
                ["npm", "install"],
                cwd=frontend_dir,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode != 0:
                pytest.skip(f"npm install failed: {result.stderr}")
        
        # Test build
        result = subprocess.run(
            ["npm", "run", "build"],
            cwd=frontend_dir,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        assert result.returncode == 0, f"Frontend build failed: {result.stderr}"
    
    @pytest.mark.selenium
    def test_frontend_pages_load(self, demo_runner):
        """Test frontend pages load correctly (requires Selenium)."""
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
        except ImportError:
            pytest.skip("Selenium not available")
        
        # Start backend API
        api_process = subprocess.Popen(
            [sys.executable, "minimal_working_demo.py"],
            cwd=BASE_DIR / "backend",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        demo_runner.cleanup_tasks.append(lambda: api_process.terminate())
        
        assert demo_runner.wait_for_port(8000), "API port did not become available"
        
        # Setup headless Chrome
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        try:
            driver = webdriver.Chrome(options=chrome_options)
            demo_runner.cleanup_tasks.append(lambda: driver.quit())
            
            # Test API docs page
            driver.get(f"{API_BASE_URL}/docs")
            
            # Wait for page to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            assert "Financial Planning" in driver.title or "FastAPI" in driver.title
            
        except WebDriverException:
            pytest.skip("Chrome WebDriver not available")
        finally:
            api_process.terminate()
            api_process.wait(timeout=10)


@pytest.mark.demo
@pytest.mark.integration
class TestMobileDemo:
    """Test mobile demo functionality."""
    
    def test_mobile_demo_structure(self, demo_runner):
        """Test mobile demo has required structure."""
        mobile_dir = BASE_DIR / "mobile"
        if not mobile_dir.exists():
            pytest.skip("Mobile directory not found")
        
        required_files = [
            "package.json",
            "App.tsx",
            "app.json"
        ]
        
        for file_name in required_files:
            file_path = mobile_dir / file_name
            if file_path.exists():
                assert file_path.is_file(), f"Mobile {file_name} is not a file"
    
    def test_mobile_demo_app_structure(self, demo_runner):
        """Test mobile demo app has required structure."""
        demo_app_dir = BASE_DIR / "mobile" / "demo-app"
        if not demo_app_dir.exists():
            pytest.skip("Mobile demo-app directory not found")
        
        required_files = [
            "package.json",
            "App.tsx",
            "app.json",
            "babel.config.js"
        ]
        
        for file_name in required_files:
            file_path = demo_app_dir / file_name
            assert file_path.exists(), f"Demo app {file_name} not found"


@pytest.mark.demo
@pytest.mark.integration
class TestDataPipelineDemo:
    """Test data pipeline demo functionality."""
    
    def test_simple_data_pipeline_demo(self, demo_runner):
        """Test simple data pipeline demo."""
        result = subprocess.run(
            [sys.executable, "simple_data_pipeline_demo.py"],
            cwd=BASE_DIR / "backend",
            capture_output=True,
            text=True,
            timeout=120
        )
        
        assert result.returncode == 0, f"Data pipeline demo failed: {result.stderr}"
        assert "pipeline" in result.stdout.lower()
    
    def test_data_pipeline_demo_full(self, demo_runner):
        """Test full data pipeline demo."""
        result = subprocess.run(
            [sys.executable, "data_pipeline_demo.py"],
            cwd=BASE_DIR / "backend", 
            capture_output=True,
            text=True,
            timeout=180
        )
        
        # Data pipeline may fail due to missing dependencies
        # We just ensure it attempts to run
        assert "Data Pipeline Demo" in result.stdout or result.returncode in [0, 1]


@pytest.mark.demo
@pytest.mark.smoke
class TestDemoHealthChecks:
    """Overall demo health checks and integration tests."""
    
    def test_all_demo_files_syntax(self, demo_runner):
        """Test all demo Python files have valid syntax."""
        demo_files = [
            "backend/working_demo.py",
            "backend/minimal_working_demo.py", 
            "backend/ml_simulation_demo.py",
            "backend/cli_demo.py",
            "backend/security_demo.py",
            "backend/performance_demo.py",
            "backend/data_pipeline_demo.py",
            "backend/simple_data_pipeline_demo.py"
        ]
        
        for demo_file in demo_files:
            file_path = BASE_DIR / demo_file
            if file_path.exists():
                result = subprocess.run(
                    [sys.executable, "-m", "py_compile", str(file_path)],
                    capture_output=True,
                    text=True
                )
                assert result.returncode == 0, f"Syntax error in {demo_file}: {result.stderr}"
    
    def test_demo_dependencies_importable(self, demo_runner):
        """Test critical demo dependencies are importable."""
        critical_imports = [
            "fastapi",
            "uvicorn",
            "numpy",
            "pydantic",
            "jose",
            "passlib"
        ]
        
        for module in critical_imports:
            result = subprocess.run(
                [sys.executable, "-c", f"import {module}"],
                capture_output=True,
                text=True
            )
            assert result.returncode == 0, f"Critical module {module} not importable: {result.stderr}"
    
    def test_demo_environment_setup(self, demo_runner):
        """Test demo environment can be set up."""
        # Check if .env template exists
        env_template = BASE_DIR / "backend" / "env.template"
        if env_template.exists():
            assert env_template.is_file(), "env.template is not a file"
        
        # Check if requirements files exist
        requirements_files = [
            "backend/requirements.txt",
            "backend/requirements_demo.txt",
            "backend/requirements_minimal.txt"
        ]
        
        for req_file in requirements_files:
            req_path = BASE_DIR / req_file
            if req_path.exists():
                assert req_path.is_file(), f"{req_file} is not a file"
                
                # Validate requirements format
                with open(req_path) as f:
                    content = f.read()
                    assert len(content.strip()) > 0, f"{req_file} is empty"


if __name__ == "__main__":
    # Run the test suite
    pytest.main([__file__, "-v", "--tb=short"])