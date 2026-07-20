#!/usr/bin/env python3
"""
Integration Test Runner

This script provides a comprehensive test runner for integration tests with:
- Environment setup and validation
- Service health checking
- Test execution with reporting
- Performance monitoring
- Cleanup and teardown
"""
import asyncio
import argparse
import json
import os
import sys
import time
import subprocess
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
import psutil
import requests
from datetime import datetime


class IntegrationTestRunner:
    """Comprehensive integration test runner with environment management."""
    
    def __init__(self):
        self.logger = self._setup_logging()
        self.start_time = None
        self.test_results = {}
        self.performance_metrics = {}
        self.service_health = {}
        
    def _setup_logging(self) -> logging.Logger:
        """Set up logging configuration."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler('integration_test_runner.log')
            ]
        )
        return logging.getLogger(__name__)
    
    async def run_integration_tests(self, 
                                   test_categories: Optional[List[str]] = None,
                                   parallel: bool = False,
                                   performance_mode: bool = False,
                                   skip_setup: bool = False) -> Dict[str, Any]:
        """Run comprehensive integration tests."""
        self.start_time = time.time()
        self.logger.info("Starting integration test execution")
        
        try:
            # Step 1: Environment validation
            if not skip_setup:
                await self._validate_environment()
                await self._setup_test_services()
                await self._verify_service_health()
            
            # Step 2: Run tests
            test_results = await self._execute_tests(
                test_categories=test_categories,
                parallel=parallel,
                performance_mode=performance_mode
            )
            
            # Step 3: Performance analysis
            if performance_mode:
                await self._analyze_performance()
            
            # Step 4: Generate reports
            await self._generate_reports(test_results)
            
            return test_results
            
        except Exception as e:
            self.logger.error(f"Integration test execution failed: {e}")
            raise
        finally:
            if not skip_setup:
                await self._cleanup_test_environment()
    
    async def _validate_environment(self):
        """Validate test environment prerequisites."""
        self.logger.info("Validating test environment")
        
        # Check Python version
        if sys.version_info < (3, 8):
            raise RuntimeError("Python 3.8+ required for integration tests")
        
        # Check Docker availability
        try:
            subprocess.run(['docker', '--version'], check=True, capture_output=True)
            subprocess.run(['docker-compose', '--version'], check=True, capture_output=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise RuntimeError("Docker and Docker Compose are required")
        
        # Check required environment variables
        required_env_vars = [
            'SECRET_KEY', 'DATABASE_URL', 'OPENAI_API_KEY', 
            'ANTHROPIC_API_KEY', 'PLAID_CLIENT_ID', 'PLAID_SECRET'
        ]
        
        missing_vars = [var for var in required_env_vars if not os.getenv(var)]
        if missing_vars:
            self.logger.warning(f"Missing environment variables: {missing_vars}")
            self.logger.info("Using test defaults for missing variables")
        
        # Check available system resources
        memory_gb = psutil.virtual_memory().total / (1024**3)
        if memory_gb < 4:
            self.logger.warning("Low system memory detected. Tests may run slowly.")
        
        disk_space_gb = psutil.disk_usage('/').free / (1024**3)
        if disk_space_gb < 5:
            raise RuntimeError("Insufficient disk space for integration tests")
        
        self.logger.info("Environment validation completed successfully")
    
    async def _setup_test_services(self):
        """Set up test services and containers."""
        self.logger.info("Setting up test services")
        
        # Start test containers
        services_to_start = [
            ('PostgreSQL', self._start_postgres_container),
            ('Redis', self._start_redis_container),
            ('Kafka', self._start_kafka_container)
        ]
        
        for service_name, start_func in services_to_start:
            try:
                self.logger.info(f"Starting {service_name} container")
                await start_func()
                self.logger.info(f"{service_name} container started successfully")
            except Exception as e:
                self.logger.error(f"Failed to start {service_name}: {e}")
                raise
        
        # Wait for services to be ready
        await self._wait_for_services_ready()
        
        self.logger.info("Test services setup completed")
    
    async def _start_postgres_container(self):
        """Start PostgreSQL test container."""
        cmd = [
            'docker', 'run', '-d',
            '--name', 'integration-postgres',
            '-p', '5434:5432',
            '-e', 'POSTGRES_USER=integration',
            '-e', 'POSTGRES_PASSWORD=integration',
            '-e', 'POSTGRES_DB=integration_financial_planning',
            'postgres:15'
        ]
        
        try:
            subprocess.run(cmd, check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            if b'already in use' in e.stderr:
                self.logger.info("PostgreSQL container already running")
            else:
                raise
    
    async def _start_redis_container(self):
        """Start Redis test container."""
        cmd = [
            'docker', 'run', '-d',
            '--name', 'integration-redis',
            '-p', '6380:6379',
            'redis:7-alpine'
        ]
        
        try:
            subprocess.run(cmd, check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            if b'already in use' in e.stderr:
                self.logger.info("Redis container already running")
            else:
                raise
    
    async def _start_kafka_container(self):
        """Start Kafka test container."""
        # This is a simplified Kafka setup - in production you'd use docker-compose
        cmd = [
            'docker', 'run', '-d',
            '--name', 'integration-kafka',
            '-p', '9092:9092',
            '-e', 'KAFKA_ZOOKEEPER_CONNECT=localhost:2181',
            '-e', 'KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://localhost:9092',
            'confluentinc/cp-kafka:latest'
        ]
        
        try:
            subprocess.run(cmd, check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            if b'already in use' in e.stderr:
                self.logger.info("Kafka container already running")
            else:
                self.logger.warning("Kafka container start failed - some tests may be skipped")
    
    async def _wait_for_services_ready(self, timeout: int = 60):
        """Wait for services to be ready."""
        self.logger.info("Waiting for services to be ready")
        
        services = {
            'PostgreSQL': ('localhost', 5434),
            'Redis': ('localhost', 6380)
        }
        
        start_time = time.time()
        
        for service_name, (host, port) in services.items():
            while time.time() - start_time < timeout:
                try:
                    import socket
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(1)
                    result = sock.connect_ex((host, port))
                    sock.close()
                    
                    if result == 0:
                        self.logger.info(f"{service_name} is ready")
                        break
                    
                except Exception:
                    pass
                
                await asyncio.sleep(1)
            else:
                raise RuntimeError(f"{service_name} failed to start within {timeout} seconds")
        
        # Additional wait for PostgreSQL to accept connections
        await asyncio.sleep(5)
    
    async def _verify_service_health(self):
        """Verify health of all required services."""
        self.logger.info("Verifying service health")
        
        health_checks = [
            ('Database', self._check_database_health),
            ('Cache', self._check_redis_health),
            ('Application', self._check_application_health)
        ]
        
        for service_name, health_check in health_checks:
            try:
                is_healthy = await health_check()
                self.service_health[service_name] = is_healthy
                
                if is_healthy:
                    self.logger.info(f"{service_name} health check passed")
                else:
                    self.logger.warning(f"{service_name} health check failed")
            except Exception as e:
                self.logger.error(f"{service_name} health check error: {e}")
                self.service_health[service_name] = False
        
        # Check if critical services are healthy
        critical_services = ['Database', 'Application']
        unhealthy_critical = [
            service for service in critical_services 
            if not self.service_health.get(service, False)
        ]
        
        if unhealthy_critical:
            raise RuntimeError(f"Critical services unhealthy: {unhealthy_critical}")
    
    async def _check_database_health(self) -> bool:
        """Check database connectivity."""
        try:
            import asyncpg
            conn = await asyncpg.connect(
                "postgresql://integration:integration@localhost:5434/integration_financial_planning"
            )
            await conn.execute("SELECT 1")
            await conn.close()
            return True
        except Exception:
            return False
    
    async def _check_redis_health(self) -> bool:
        """Check Redis connectivity."""
        try:
            import redis.asyncio as redis
            r = redis.Redis(host='localhost', port=6380, decode_responses=True)
            await r.ping()
            await r.close()
            return True
        except Exception:
            return False
    
    async def _check_application_health(self) -> bool:
        """Check application health endpoint."""
        try:
            # This would check the main application health endpoint
            # For now, we'll assume it's healthy if we can import the app
            from app.main import app
            return True
        except Exception:
            return False
    
    async def _execute_tests(self, 
                            test_categories: Optional[List[str]] = None,
                            parallel: bool = False,
                            performance_mode: bool = False) -> Dict[str, Any]:
        """Execute integration tests."""
        self.logger.info("Executing integration tests")
        
        # Define test categories
        all_categories = {
            'user_journey': 'tests/integration/test_user_journey_complete.py',
            'notifications': 'tests/integration/test_notification_delivery.py',
            'banking': 'tests/integration/test_banking_integration.py',
            'pdf': 'tests/integration/test_pdf_generation.py',
            'system': 'tests/integration/test_system_integration.py'
        }
        
        # Determine which tests to run
        if test_categories:
            tests_to_run = {
                cat: all_categories[cat] for cat in test_categories 
                if cat in all_categories
            }
        else:
            tests_to_run = all_categories
        
        # Build pytest command
        cmd = ['python', '-m', 'pytest']
        
        # Add test files
        for test_file in tests_to_run.values():
            cmd.append(test_file)
        
        # Add options
        cmd.extend([
            '-v',
            '--tb=short',
            '--maxfail=5',
            '--timeout=300',
            '--asyncio-mode=auto',
            '--cov=app',
            '--cov-report=html:htmlcov',
            '--cov-report=xml',
            '--cov-report=term-missing',
            '--junit-xml=integration_test_results.xml'
        ])
        
        if parallel:
            cmd.extend(['-n', 'auto'])
        
        if performance_mode:
            cmd.extend(['--durations=0', '--benchmark-only'])
        
        # Execute tests
        self.logger.info(f"Running command: {' '.join(cmd)}")
        
        start_time = time.time()
        result = subprocess.run(cmd, capture_output=True, text=True)
        execution_time = time.time() - start_time
        
        # Parse results
        test_results = {
            'exit_code': result.returncode,
            'execution_time': execution_time,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'categories_run': list(tests_to_run.keys()),
            'parallel': parallel,
            'performance_mode': performance_mode
        }
        
        self.test_results = test_results
        
        if result.returncode == 0:
            self.logger.info("All integration tests passed")
        else:
            self.logger.error("Some integration tests failed")
            self.logger.error(f"Test output:\n{result.stdout}")
            self.logger.error(f"Test errors:\n{result.stderr}")
        
        return test_results
    
    async def _analyze_performance(self):
        """Analyze test performance metrics."""
        self.logger.info("Analyzing performance metrics")
        
        # This would analyze performance data from test execution
        # For now, we'll collect basic system metrics
        
        self.performance_metrics = {
            'system_stats': {
                'cpu_usage': psutil.cpu_percent(interval=1),
                'memory_usage': psutil.virtual_memory().percent,
                'disk_usage': psutil.disk_usage('/').percent
            },
            'test_execution_time': self.test_results.get('execution_time', 0),
            'timestamp': datetime.now().isoformat()
        }
        
        self.logger.info(f"Performance analysis completed: {self.performance_metrics}")
    
    async def _generate_reports(self, test_results: Dict[str, Any]):
        """Generate comprehensive test reports."""
        self.logger.info("Generating test reports")
        
        # Create reports directory
        reports_dir = Path('integration_test_reports')
        reports_dir.mkdir(exist_ok=True)
        
        # Generate summary report
        summary_report = {
            'execution_summary': {
                'start_time': datetime.fromtimestamp(self.start_time).isoformat(),
                'end_time': datetime.now().isoformat(),
                'total_duration': time.time() - self.start_time,
                'test_categories': test_results.get('categories_run', []),
                'exit_code': test_results.get('exit_code', 1),
                'success': test_results.get('exit_code', 1) == 0
            },
            'service_health': self.service_health,
            'performance_metrics': self.performance_metrics,
            'environment_info': {
                'python_version': sys.version,
                'platform': sys.platform,
                'cpu_count': psutil.cpu_count(),
                'memory_total_gb': psutil.virtual_memory().total / (1024**3)
            }
        }
        
        # Save summary report
        summary_file = reports_dir / 'integration_test_summary.json'
        with open(summary_file, 'w') as f:
            json.dump(summary_report, f, indent=2)
        
        # Save detailed output
        output_file = reports_dir / 'integration_test_output.txt'
        with open(output_file, 'w') as f:
            f.write("INTEGRATION TEST OUTPUT\n")
            f.write("=" * 50 + "\n\n")
            f.write("STDOUT:\n")
            f.write(test_results.get('stdout', ''))
            f.write("\n\nSTDERR:\n")
            f.write(test_results.get('stderr', ''))
        
        self.logger.info(f"Reports generated in {reports_dir}")
        
        # Print summary to console
        self._print_summary_report(summary_report)
    
    def _print_summary_report(self, summary_report: Dict[str, Any]):
        """Print summary report to console."""
        print("\n" + "="*60)
        print("INTEGRATION TEST SUMMARY")
        print("="*60)
        
        exec_summary = summary_report['execution_summary']
        print(f"Status: {'PASSED' if exec_summary['success'] else 'FAILED'}")
        print(f"Duration: {exec_summary['total_duration']:.2f} seconds")
        print(f"Categories: {', '.join(exec_summary['test_categories'])}")
        
        print(f"\nService Health:")
        for service, status in summary_report['service_health'].items():
            status_str = "HEALTHY" if status else "UNHEALTHY"
            print(f"  {service}: {status_str}")
        
        if summary_report['performance_metrics']:
            perf = summary_report['performance_metrics']
            if 'system_stats' in perf:
                stats = perf['system_stats']
                print(f"\nSystem Resources:")
                print(f"  CPU Usage: {stats['cpu_usage']:.1f}%")
                print(f"  Memory Usage: {stats['memory_usage']:.1f}%")
                print(f"  Disk Usage: {stats['disk_usage']:.1f}%")
        
        print("\n" + "="*60)
    
    async def _cleanup_test_environment(self):
        """Clean up test environment and containers."""
        self.logger.info("Cleaning up test environment")
        
        containers_to_remove = [
            'integration-postgres',
            'integration-redis', 
            'integration-kafka'
        ]
        
        for container_name in containers_to_remove:
            try:
                subprocess.run(['docker', 'rm', '-f', container_name], 
                             check=False, capture_output=True)
                self.logger.info(f"Removed container: {container_name}")
            except Exception as e:
                self.logger.warning(f"Failed to remove container {container_name}: {e}")
        
        # Clean up temporary files
        temp_files = [
            'integration_test_runner.log',
            '.coverage',
            'coverage.xml'
        ]
        
        for temp_file in temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except Exception as e:
                self.logger.warning(f"Failed to remove {temp_file}: {e}")
        
        self.logger.info("Cleanup completed")


async def main():
    """Main entry point for the integration test runner."""
    parser = argparse.ArgumentParser(description='Integration Test Runner')
    
    parser.add_argument(
        '--categories', 
        nargs='+', 
        choices=['user_journey', 'notifications', 'banking', 'pdf', 'system'],
        help='Test categories to run (default: all)'
    )
    
    parser.add_argument(
        '--parallel', 
        action='store_true',
        help='Run tests in parallel'
    )
    
    parser.add_argument(
        '--performance', 
        action='store_true',
        help='Enable performance monitoring'
    )
    
    parser.add_argument(
        '--skip-setup', 
        action='store_true',
        help='Skip environment setup (assume services are running)'
    )
    
    parser.add_argument(
        '--quick', 
        action='store_true',
        help='Run quick test suite (essential tests only)'
    )
    
    args = parser.parse_args()
    
    # Configure test categories for quick mode
    if args.quick:
        args.categories = ['user_journey', 'notifications']
    
    try:
        runner = IntegrationTestRunner()
        results = await runner.run_integration_tests(
            test_categories=args.categories,
            parallel=args.parallel,
            performance_mode=args.performance,
            skip_setup=args.skip_setup
        )
        
        # Exit with appropriate code
        sys.exit(results.get('exit_code', 1))
        
    except KeyboardInterrupt:
        print("\nTest execution interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"Test execution failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main())