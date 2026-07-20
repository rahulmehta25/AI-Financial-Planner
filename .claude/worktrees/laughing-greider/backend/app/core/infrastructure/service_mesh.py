"""
Service Mesh and API Gateway Infrastructure

Provides:
- Service discovery and registration
- Load balancing
- Circuit breaker patterns
- Rate limiting
- API versioning
- Request routing
- Health checking
- Distributed tracing
"""

import asyncio
import hashlib
import json
import logging
import time
import uuid
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
from urllib.parse import urlparse

import aiohttp
from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import Counter, Histogram, Gauge
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings

logger = logging.getLogger(__name__)


# Metrics for monitoring
request_count = Counter('api_requests_total', 'Total API requests', ['method', 'endpoint', 'status'])
request_duration = Histogram('api_request_duration_seconds', 'API request duration', ['method', 'endpoint'])
active_requests = Gauge('api_active_requests', 'Active API requests')
circuit_breaker_state = Gauge('circuit_breaker_state', 'Circuit breaker state', ['service'])


class ServiceStatus(Enum):
    """Service health status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class LoadBalancerStrategy(Enum):
    """Load balancing strategies"""
    ROUND_ROBIN = "round_robin"
    LEAST_CONNECTIONS = "least_connections"
    WEIGHTED = "weighted"
    RANDOM = "random"
    IP_HASH = "ip_hash"


@dataclass
class ServiceInstance:
    """Service instance representation"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    host: str = ""
    port: int = 0
    weight: int = 1
    health_check_url: str = "/health"
    metadata: Dict[str, Any] = field(default_factory=dict)
    status: ServiceStatus = ServiceStatus.UNKNOWN
    last_health_check: Optional[datetime] = None
    active_connections: int = 0
    total_requests: int = 0
    error_count: int = 0
    response_times: List[float] = field(default_factory=list)
    
    @property
    def url(self) -> str:
        """Get service URL"""
        return f"http://{self.host}:{self.port}"
    
    @property
    def health_url(self) -> str:
        """Get health check URL"""
        return f"{self.url}{self.health_check_url}"
    
    @property
    def average_response_time(self) -> float:
        """Calculate average response time"""
        if not self.response_times:
            return 0.0
        return sum(self.response_times[-100:]) / len(self.response_times[-100:])
    
    @property
    def error_rate(self) -> float:
        """Calculate error rate"""
        if self.total_requests == 0:
            return 0.0
        return self.error_count / self.total_requests


class CircuitBreaker:
    """Circuit breaker implementation for fault tolerance"""
    
    class State(Enum):
        CLOSED = "closed"  # Normal operation
        OPEN = "open"      # Failures exceeded threshold
        HALF_OPEN = "half_open"  # Testing recovery
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: type = Exception
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.failure_count = 0
        self.last_failure_time = None
        self.state = self.State.CLOSED
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        if self.state == self.State.OPEN:
            if self._should_attempt_reset():
                self.state = self.State.HALF_OPEN
            else:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Service temporarily unavailable"
                )
        
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
            
        except self.expected_exception as e:
            self._on_failure()
            raise e
    
    def _should_attempt_reset(self) -> bool:
        """Check if circuit breaker should attempt reset"""
        if not self.last_failure_time:
            return True
        
        time_since_failure = time.time() - self.last_failure_time
        return time_since_failure >= self.recovery_timeout
    
    def _on_success(self):
        """Handle successful call"""
        self.failure_count = 0
        self.state = self.State.CLOSED
    
    def _on_failure(self):
        """Handle failed call"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = self.State.OPEN
            circuit_breaker_state.labels(service='unknown').set(1)  # Open state
        elif self.state == self.State.HALF_OPEN:
            self.state = self.State.OPEN


class RateLimiter:
    """Token bucket rate limiter"""
    
    def __init__(
        self,
        rate: int,  # Requests per period
        period: int = 60,  # Period in seconds
        burst: Optional[int] = None  # Max burst size
    ):
        self.rate = rate
        self.period = period
        self.burst = burst or rate
        self.tokens = self.burst
        self.last_refill = time.time()
        self._lock = asyncio.Lock()
    
    async def acquire(self, tokens: int = 1) -> bool:
        """Acquire tokens for request"""
        async with self._lock:
            self._refill()
            
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            
            return False
    
    def _refill(self):
        """Refill tokens based on elapsed time"""
        now = time.time()
        elapsed = now - self.last_refill
        
        tokens_to_add = (elapsed / self.period) * self.rate
        self.tokens = min(self.burst, self.tokens + tokens_to_add)
        self.last_refill = now


class ServiceRegistry:
    """Service discovery and registration"""
    
    def __init__(self):
        self.services: Dict[str, List[ServiceInstance]] = {}
        self._lock = asyncio.Lock()
    
    async def register(self, service: ServiceInstance) -> bool:
        """Register service instance"""
        async with self._lock:
            if service.name not in self.services:
                self.services[service.name] = []
            
            # Check for duplicate
            for existing in self.services[service.name]:
                if existing.host == service.host and existing.port == service.port:
                    return False
            
            self.services[service.name].append(service)
            logger.info(f"Registered service: {service.name} at {service.host}:{service.port}")
            return True
    
    async def deregister(self, service_name: str, host: str, port: int) -> bool:
        """Deregister service instance"""
        async with self._lock:
            if service_name not in self.services:
                return False
            
            initial_count = len(self.services[service_name])
            self.services[service_name] = [
                s for s in self.services[service_name]
                if not (s.host == host and s.port == port)
            ]
            
            if len(self.services[service_name]) < initial_count:
                logger.info(f"Deregistered service: {service_name} at {host}:{port}")
                return True
            
            return False
    
    async def get_service(self, service_name: str) -> Optional[List[ServiceInstance]]:
        """Get all instances of a service"""
        async with self._lock:
            return self.services.get(service_name, [])
    
    async def get_healthy_services(self, service_name: str) -> List[ServiceInstance]:
        """Get healthy service instances"""
        services = await self.get_service(service_name)
        if not services:
            return []
        
        return [s for s in services if s.status in [ServiceStatus.HEALTHY, ServiceStatus.DEGRADED]]
    
    async def update_service_status(
        self,
        service_name: str,
        host: str,
        port: int,
        status: ServiceStatus
    ) -> bool:
        """Update service instance status"""
        async with self._lock:
            if service_name not in self.services:
                return False
            
            for service in self.services[service_name]:
                if service.host == host and service.port == port:
                    service.status = status
                    service.last_health_check = datetime.now(timezone.utc)
                    return True
            
            return False


class LoadBalancer:
    """Load balancer for service instances"""
    
    def __init__(
        self,
        strategy: LoadBalancerStrategy = LoadBalancerStrategy.ROUND_ROBIN
    ):
        self.strategy = strategy
        self._round_robin_index = {}
    
    async def select_instance(
        self,
        instances: List[ServiceInstance],
        client_ip: Optional[str] = None
    ) -> Optional[ServiceInstance]:
        """Select service instance based on strategy"""
        if not instances:
            return None
        
        healthy_instances = [i for i in instances if i.status == ServiceStatus.HEALTHY]
        if not healthy_instances:
            # Fall back to degraded instances
            healthy_instances = [i for i in instances if i.status == ServiceStatus.DEGRADED]
        
        if not healthy_instances:
            return None
        
        if self.strategy == LoadBalancerStrategy.ROUND_ROBIN:
            return self._round_robin(healthy_instances)
        elif self.strategy == LoadBalancerStrategy.LEAST_CONNECTIONS:
            return self._least_connections(healthy_instances)
        elif self.strategy == LoadBalancerStrategy.WEIGHTED:
            return self._weighted(healthy_instances)
        elif self.strategy == LoadBalancerStrategy.RANDOM:
            return self._random(healthy_instances)
        elif self.strategy == LoadBalancerStrategy.IP_HASH:
            return self._ip_hash(healthy_instances, client_ip)
        
        return healthy_instances[0]
    
    def _round_robin(self, instances: List[ServiceInstance]) -> ServiceInstance:
        """Round-robin selection"""
        service_name = instances[0].name
        
        if service_name not in self._round_robin_index:
            self._round_robin_index[service_name] = 0
        
        index = self._round_robin_index[service_name]
        instance = instances[index % len(instances)]
        
        self._round_robin_index[service_name] = (index + 1) % len(instances)
        
        return instance
    
    def _least_connections(self, instances: List[ServiceInstance]) -> ServiceInstance:
        """Select instance with least active connections"""
        return min(instances, key=lambda x: x.active_connections)
    
    def _weighted(self, instances: List[ServiceInstance]) -> ServiceInstance:
        """Weighted selection based on instance weight"""
        import random
        
        total_weight = sum(i.weight for i in instances)
        if total_weight == 0:
            return instances[0]
        
        rand = random.uniform(0, total_weight)
        cumulative_weight = 0
        
        for instance in instances:
            cumulative_weight += instance.weight
            if rand <= cumulative_weight:
                return instance
        
        return instances[-1]
    
    def _random(self, instances: List[ServiceInstance]) -> ServiceInstance:
        """Random selection"""
        import random
        return random.choice(instances)
    
    def _ip_hash(
        self,
        instances: List[ServiceInstance],
        client_ip: Optional[str]
    ) -> ServiceInstance:
        """Consistent hashing based on client IP"""
        if not client_ip:
            return self._random(instances)
        
        hash_value = int(hashlib.md5(client_ip.encode()).hexdigest(), 16)
        index = hash_value % len(instances)
        
        return instances[index]


class ServiceProxy:
    """Service proxy with circuit breaker and retry logic"""
    
    def __init__(
        self,
        registry: ServiceRegistry,
        load_balancer: LoadBalancer,
        circuit_breaker: CircuitBreaker = None
    ):
        self.registry = registry
        self.load_balancer = load_balancer
        self.circuit_breaker = circuit_breaker or CircuitBreaker()
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def call(
        self,
        service_name: str,
        method: str,
        path: str,
        client_ip: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        timeout: int = 30,
        max_retries: int = 3
    ) -> Tuple[int, Dict[str, Any]]:
        """Call service with load balancing and circuit breaker"""
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        instances = await self.registry.get_healthy_services(service_name)
        if not instances:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"No healthy instances for service: {service_name}"
            )
        
        last_error = None
        
        for attempt in range(max_retries):
            instance = await self.load_balancer.select_instance(instances, client_ip)
            if not instance:
                continue
            
            try:
                # Update connection count
                instance.active_connections += 1
                
                # Make request with circuit breaker
                url = f"{instance.url}{path}"
                start_time = time.time()
                
                async def make_request():
                    async with self.session.request(
                        method=method,
                        url=url,
                        headers=headers,
                        json=json_data,
                        params=params,
                        timeout=aiohttp.ClientTimeout(total=timeout)
                    ) as response:
                        data = await response.json() if response.content_type == 'application/json' else {}
                        return response.status, data
                
                status_code, response_data = await self.circuit_breaker.call(make_request)
                
                # Update metrics
                response_time = time.time() - start_time
                instance.response_times.append(response_time)
                instance.total_requests += 1
                
                if status_code >= 500:
                    instance.error_count += 1
                    raise HTTPException(status_code=status_code, detail=response_data)
                
                return status_code, response_data
                
            except Exception as e:
                instance.error_count += 1
                last_error = e
                
                # Mark instance as unhealthy if error rate is high
                if instance.error_rate > 0.5:
                    await self.registry.update_service_status(
                        service_name,
                        instance.host,
                        instance.port,
                        ServiceStatus.UNHEALTHY
                    )
                
            finally:
                instance.active_connections -= 1
        
        if last_error:
            raise last_error
        
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to call service after {max_retries} attempts"
        )


class HealthChecker:
    """Service health checker"""
    
    def __init__(self, registry: ServiceRegistry):
        self.registry = registry
        self.check_interval = 30  # seconds
        self._running = False
        self._task = None
    
    async def start(self):
        """Start health checking"""
        self._running = True
        self._task = asyncio.create_task(self._health_check_loop())
        logger.info("Health checker started")
    
    async def stop(self):
        """Stop health checking"""
        self._running = False
        if self._task:
            await self._task
        logger.info("Health checker stopped")
    
    async def _health_check_loop(self):
        """Main health check loop"""
        while self._running:
            try:
                await self._check_all_services()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Health check error: {e}")
                await asyncio.sleep(self.check_interval)
    
    async def _check_all_services(self):
        """Check health of all registered services"""
        async with aiohttp.ClientSession() as session:
            tasks = []
            
            for service_name, instances in self.registry.services.items():
                for instance in instances:
                    tasks.append(self._check_instance_health(session, instance))
            
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _check_instance_health(
        self,
        session: aiohttp.ClientSession,
        instance: ServiceInstance
    ):
        """Check health of a service instance"""
        try:
            async with session.get(
                instance.health_url,
                timeout=aiohttp.ClientTimeout(total=5)
            ) as response:
                if response.status == 200:
                    status = ServiceStatus.HEALTHY
                elif response.status < 500:
                    status = ServiceStatus.DEGRADED
                else:
                    status = ServiceStatus.UNHEALTHY
                
        except Exception as e:
            logger.warning(f"Health check failed for {instance.name} at {instance.url}: {e}")
            status = ServiceStatus.UNHEALTHY
        
        await self.registry.update_service_status(
            instance.name,
            instance.host,
            instance.port,
            status
        )


class APIVersionMiddleware(BaseHTTPMiddleware):
    """API versioning middleware"""
    
    def __init__(self, app, default_version: str = "v1"):
        super().__init__(app)
        self.default_version = default_version
    
    async def dispatch(self, request: Request, call_next):
        """Process request with version handling"""
        # Extract version from URL path or header
        path_parts = request.url.path.split('/')
        
        if len(path_parts) > 1 and path_parts[1].startswith('v'):
            version = path_parts[1]
        else:
            version = request.headers.get('API-Version', self.default_version)
        
        # Add version to request state
        request.state.api_version = version
        
        # Process request
        response = await call_next(request)
        
        # Add version to response headers
        response.headers['API-Version'] = version
        
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware"""
    
    def __init__(
        self,
        app,
        rate: int = 100,
        period: int = 60,
        burst: Optional[int] = None
    ):
        super().__init__(app)
        self.limiters = {}  # Per-IP rate limiters
        self.rate = rate
        self.period = period
        self.burst = burst
    
    async def dispatch(self, request: Request, call_next):
        """Process request with rate limiting"""
        # Get client IP
        client_ip = request.client.host
        
        # Get or create rate limiter for IP
        if client_ip not in self.limiters:
            self.limiters[client_ip] = RateLimiter(
                self.rate,
                self.period,
                self.burst
            )
        
        limiter = self.limiters[client_ip]
        
        # Check rate limit
        if not await limiter.acquire():
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Rate limit exceeded"},
                headers={
                    "Retry-After": str(limiter.period),
                    "X-RateLimit-Limit": str(limiter.rate),
                    "X-RateLimit-Remaining": str(int(limiter.tokens)),
                    "X-RateLimit-Reset": str(int(time.time() + limiter.period))
                }
            )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(limiter.rate)
        response.headers["X-RateLimit-Remaining"] = str(int(limiter.tokens))
        response.headers["X-RateLimit-Reset"] = str(int(time.time() + limiter.period))
        
        return response


# Global instances
service_registry = ServiceRegistry()
load_balancer = LoadBalancer(LoadBalancerStrategy.LEAST_CONNECTIONS)
health_checker = HealthChecker(service_registry)


def configure_service_mesh(app: FastAPI):
    """Configure service mesh middleware and settings"""
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS if hasattr(settings, 'ALLOWED_ORIGINS') else ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Add API versioning
    app.add_middleware(APIVersionMiddleware, default_version="v1")
    
    # Add rate limiting
    app.add_middleware(
        RateLimitMiddleware,
        rate=getattr(settings, 'RATE_LIMIT_REQUESTS', 100),
        period=getattr(settings, 'RATE_LIMIT_PERIOD', 60)
    )
    
    # Start health checker on startup
    @app.on_event("startup")
    async def startup_event():
        await health_checker.start()
    
    # Stop health checker on shutdown
    @app.on_event("shutdown")
    async def shutdown_event():
        await health_checker.stop()
    
    logger.info("Service mesh configured")


# Service mesh health endpoint
async def service_mesh_health() -> Dict[str, Any]:
    """Get service mesh health status"""
    services_status = {}
    
    for service_name, instances in service_registry.services.items():
        healthy = sum(1 for i in instances if i.status == ServiceStatus.HEALTHY)
        degraded = sum(1 for i in instances if i.status == ServiceStatus.DEGRADED)
        unhealthy = sum(1 for i in instances if i.status == ServiceStatus.UNHEALTHY)
        
        services_status[service_name] = {
            'total_instances': len(instances),
            'healthy': healthy,
            'degraded': degraded,
            'unhealthy': unhealthy
        }
    
    return {
        'status': 'healthy' if services_status else 'no_services',
        'services': services_status,
        'load_balancer_strategy': load_balancer.strategy.value
    }