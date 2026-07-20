"""
Base classes and utilities for comprehensive integration tests.

This module provides:
- Base test classes for different types of integration tests
- Common fixtures and utilities
- Test helpers for complex scenarios
- Resource management and cleanup
"""
import asyncio
import time
import logging
import json
import math
from typing import Dict, List, Any, Optional, Callable
from abc import ABC, abstractmethod
from dataclasses import dataclass
from contextlib import asynccontextmanager
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from testcontainers.compose import DockerCompose
from testcontainers.redis import RedisContainer
from testcontainers.kafka import KafkaContainer

from app.main import app
from app.core.config import settings
from app.database.base import Base
from tests.factories import UserFactory, create_complete_user_scenario


logger = logging.getLogger(__name__)


@dataclass
class TestMetrics:
    """Container for test performance metrics."""
    start_time: float
    end_time: float
    duration: float
    success: bool
    error_message: Optional[str] = None
    
    @property
    def duration_ms(self) -> float:
        return self.duration * 1000


@dataclass
class ResourceUsage:
    """Container for resource usage metrics."""
    cpu_usage: float
    memory_usage: float
    network_io: Dict[str, float]
    disk_io: Dict[str, float]
    timestamp: float


class BaseIntegrationTest(ABC):
    """Base class for all integration tests with common functionality."""
    
    def __init__(self):
        self.metrics: List[TestMetrics] = []
        self.resource_usage: List[ResourceUsage] = []
        self.test_id: Optional[str] = None
    
    @abstractmethod
    async def setup_test_environment(self) -> Dict[str, Any]:
        """Set up the test environment and return configuration."""
        pass
    
    @abstractmethod
    async def cleanup_test_environment(self, config: Dict[str, Any]) -> None:
        """Clean up test environment resources."""
        pass
    
    def record_metric(self, metric: TestMetrics) -> None:
        """Record a test metric."""
        self.metrics.append(metric)
        logger.info(f"Test metric recorded: {metric.duration_ms:.2f}ms, success: {metric.success}")
    
    def record_resource_usage(self, usage: ResourceUsage) -> None:
        """Record resource usage."""
        self.resource_usage.append(usage)
    
    async def measure_operation(self, operation: Callable, operation_name: str) -> Any:
        """Measure the performance of an operation."""
        start_time = time.time()
        success = True
        error_message = None
        result = None
        
        try:
            result = await operation()
        except Exception as e:
            success = False
            error_message = str(e)
            raise
        finally:
            end_time = time.time()
            duration = end_time - start_time
            
            metric = TestMetrics(
                start_time=start_time,
                end_time=end_time,
                duration=duration,
                success=success,
                error_message=error_message
            )
            self.record_metric(metric)
        
        return result


class FullStackIntegrationTest(BaseIntegrationTest):
    """Base class for full-stack integration tests with all services."""
    
    def __init__(self):
        super().__init__()
        self.compose: Optional[DockerCompose] = None
        self.redis_container: Optional[RedisContainer] = None
        self.kafka_container: Optional[KafkaContainer] = None
        self.client: Optional[AsyncClient] = None
        self.db_session: Optional[AsyncSession] = None
    
    async def setup_test_environment(self) -> Dict[str, Any]:
        """Set up full stack environment with all dependencies."""
        logger.info("Setting up full stack integration test environment")
        
        # Start external dependencies
        await self._start_external_services()
        
        # Start application services
        await self._start_application_services()
        
        # Initialize test client
        self.client = AsyncClient(app=app, base_url="http://test")
        
        config = {
            'redis_url': self.redis_container.get_connection_url() if self.redis_container else None,
            'kafka_url': self.kafka_container.get_bootstrap_server() if self.kafka_container else None,
            'app_url': 'http://test'
        }
        
        logger.info("Full stack environment setup complete")
        return config
    
    async def cleanup_test_environment(self, config: Dict[str, Any]) -> None:
        """Clean up full stack environment."""
        logger.info("Cleaning up full stack environment")
        
        if self.client:
            await self.client.aclose()
        
        if self.compose:
            self.compose.stop()
        
        if self.redis_container:
            self.redis_container.stop()
        
        if self.kafka_container:
            self.kafka_container.stop()
        
        logger.info("Full stack cleanup complete")
    
    async def _start_external_services(self) -> None:
        """Start external service containers."""
        # Redis for caching
        self.redis_container = RedisContainer("redis:7-alpine")
        self.redis_container.start()
        
        # Kafka for event streaming
        self.kafka_container = KafkaContainer("confluentinc/cp-kafka:latest")
        self.kafka_container.start()
        
        # Wait for services to be ready
        await asyncio.sleep(5)
    
    async def _start_application_services(self) -> None:
        """Start application microservices."""
        # Use docker-compose for microservices
        self.compose = DockerCompose(
            "/Users/rahulmehta/Desktop/Financial Planning/backend/infrastructure/deployment"
        )
        self.compose.start()
        
        # Wait for services to be ready
        await asyncio.sleep(10)


class UserJourneyTest(FullStackIntegrationTest):
    """Base class for end-to-end user journey tests."""
    
    def __init__(self):
        super().__init__()
        self.test_user = None
        self.auth_token = None
        self.journey_steps: List[Dict[str, Any]] = []
    
    async def create_test_user(self) -> Dict[str, Any]:
        """Create a test user and authenticate."""
        # Create user via API
        user_data = {
            "email": "test@example.com",
            "password": "test_password123",
            "first_name": "Test",
            "last_name": "User"
        }
        
        response = await self.client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 201
        
        # Authenticate user
        login_data = {
            "username": user_data["email"],
            "password": user_data["password"]
        }
        
        response = await self.client.post("/api/v1/auth/login", data=login_data)
        assert response.status_code == 200
        
        token_data = response.json()
        self.auth_token = token_data["access_token"]
        
        return user_data
    
    @property
    def auth_headers(self) -> Dict[str, str]:
        """Get authorization headers."""
        return {"Authorization": f"Bearer {self.auth_token}"}
    
    def record_journey_step(self, step_name: str, data: Dict[str, Any]) -> None:
        """Record a step in the user journey."""
        step = {
            "step_name": step_name,
            "timestamp": time.time(),
            "data": data
        }
        self.journey_steps.append(step)
        logger.info(f"Journey step recorded: {step_name}")


class PerformanceIntegrationTest(BaseIntegrationTest):
    """Base class for performance integration tests."""
    
    def __init__(self):
        super().__init__()
        self.concurrent_users = 10
        self.test_duration = 60  # seconds
        self.latency_thresholds = {
            'p50': 100,  # ms
            'p95': 500,  # ms
            'p99': 1000  # ms
        }
    
    async def setup_test_environment(self) -> Dict[str, Any]:
        """Set up performance test environment."""
        return {
            'concurrent_users': self.concurrent_users,
            'test_duration': self.test_duration
        }
    
    async def cleanup_test_environment(self, config: Dict[str, Any]) -> None:
        """Clean up performance test environment."""
        pass
    
    async def run_concurrent_users(self, user_simulation: Callable, num_users: int) -> List[TestMetrics]:
        """Run concurrent user simulations."""
        tasks = []
        for i in range(num_users):
            task = asyncio.create_task(
                self.measure_operation(
                    lambda: user_simulation(user_id=i),
                    f"user_simulation_{i}"
                )
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return self.metrics[-num_users:]  # Return last N metrics
    
    def calculate_latency_percentiles(self, metrics: List[TestMetrics]) -> Dict[str, float]:
        """Calculate latency percentiles from metrics."""
        durations = [m.duration_ms for m in metrics if m.success]
        durations.sort()
        
        if not durations:
            return {}
        
        n = len(durations)
        return {
            'p50': durations[int(n * 0.5)],
            'p95': durations[int(n * 0.95)],
            'p99': durations[int(n * 0.99)],
            'min': min(durations),
            'max': max(durations),
            'mean': sum(durations) / n
        }
    
    def assert_performance_requirements(self, metrics: List[TestMetrics]) -> None:
        """Assert that performance requirements are met."""
        percentiles = self.calculate_latency_percentiles(metrics)
        
        for threshold, expected in self.latency_thresholds.items():
            actual = percentiles.get(threshold, float('inf'))
            assert actual <= expected, f"{threshold} latency {actual:.2f}ms exceeds threshold {expected}ms"


class SecurityIntegrationTest(BaseIntegrationTest):
    """Base class for security integration tests."""
    
    def __init__(self):
        super().__init__()
        self.security_checks = []
        self.vulnerable_endpoints = []
    
    async def setup_test_environment(self) -> Dict[str, Any]:
        """Set up security test environment."""
        return {
            'security_mode': 'testing',
            'audit_enabled': True
        }
    
    async def cleanup_test_environment(self, config: Dict[str, Any]) -> None:
        """Clean up security test environment."""
        pass
    
    def record_security_check(self, check_name: str, passed: bool, details: str) -> None:
        """Record a security check result."""
        check = {
            'check_name': check_name,
            'passed': passed,
            'details': details,
            'timestamp': time.time()
        }
        self.security_checks.append(check)
        
        if not passed:
            self.vulnerable_endpoints.append(check_name)
        
        logger.info(f"Security check: {check_name} - {'PASSED' if passed else 'FAILED'}")
    
    async def test_endpoint_security(self, client: AsyncClient, endpoint: str, method: str = 'GET') -> bool:
        """Test security of a specific endpoint."""
        # Test without authentication
        try:
            response = await client.request(method, endpoint)
            if response.status_code == 401:
                self.record_security_check(f"{method} {endpoint} - auth required", True, "Properly requires authentication")
                return True
            else:
                self.record_security_check(f"{method} {endpoint} - auth bypass", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.record_security_check(f"{method} {endpoint} - error", False, str(e))
            return False


@asynccontextmanager
async def integration_test_context(test_class: BaseIntegrationTest):
    """Context manager for integration tests with setup/cleanup."""
    config = None
    try:
        config = await test_class.setup_test_environment()
        yield config
    finally:
        if config:
            await test_class.cleanup_test_environment(config)


# Utility functions for integration tests
async def wait_for_service(url: str, timeout: int = 30) -> bool:
    """Wait for a service to become available."""
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            async with AsyncClient() as client:
                response = await client.get(url)
                if response.status_code == 200:
                    return True
        except Exception:
            pass
        
        await asyncio.sleep(1)
    
    return False


async def assert_database_consistency(db_session: AsyncSession, checks: List[Callable]) -> None:
    """Assert database consistency using provided check functions."""
    for check in checks:
        result = await check(db_session)
        assert result, f"Database consistency check failed: {check.__name__}"


def generate_load_pattern(duration: int, peak_factor: float = 2.0) -> List[int]:
    """Generate a load pattern for performance testing."""
    pattern = []
    total_points = duration
    
    for i in range(total_points):
        # Create a sine wave pattern with peak factor
        base_load = 1
        wave = math.sin(2 * math.pi * i / total_points)
        load = int(base_load + (peak_factor - base_load) * (wave + 1) / 2)
        pattern.append(max(1, load))
    
    return pattern


class TestEnvironmentManager:
    """Manages test environments and resources."""
    
    def __init__(self):
        self.active_environments = {}
        self.resource_pools = {}
    
    async def create_environment(self, env_type: str, config: Dict[str, Any]) -> str:
        """Create a new test environment."""
        env_id = f"{env_type}_{int(time.time())}"
        
        if env_type == 'microservices':
            env = await self._create_microservices_environment(config)
        elif env_type == 'performance':
            env = await self._create_performance_environment(config)
        elif env_type == 'security':
            env = await self._create_security_environment(config)
        else:
            raise ValueError(f"Unknown environment type: {env_type}")
        
        self.active_environments[env_id] = env
        return env_id
    
    async def destroy_environment(self, env_id: str) -> None:
        """Destroy a test environment."""
        if env_id in self.active_environments:
            env = self.active_environments[env_id]
            await env.cleanup()
            del self.active_environments[env_id]
    
    async def _create_microservices_environment(self, config: Dict[str, Any]) -> Any:
        """Create microservices test environment."""
        # Implementation would set up docker containers, networking, etc.
        pass
    
    async def _create_performance_environment(self, config: Dict[str, Any]) -> Any:
        """Create performance test environment."""
        # Implementation would set up load generators, monitoring, etc.
        pass
    
    async def _create_security_environment(self, config: Dict[str, Any]) -> Any:
        """Create security test environment."""
        # Implementation would set up security scanning tools, etc.
        pass