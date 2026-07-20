"""
Advanced Monitoring and Observability Infrastructure

Provides:
- Metrics collection with Prometheus integration
- Health checks for all system components
- Performance monitoring and alerting
- Distributed tracing support
- Custom business metrics
- System resource monitoring
"""

import asyncio
import logging
import os
import time
import uuid
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union
from functools import wraps
from collections import defaultdict, deque

import psutil
from prometheus_client import (
    Counter, Gauge, Histogram, Summary, CollectorRegistry,
    generate_latest, CONTENT_TYPE_LATEST, start_http_server
)

from app.core.config import settings

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health check status enumeration"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class MetricType(Enum):
    """Metric type enumeration"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


@dataclass
class HealthCheckResult:
    """Result of a health check"""
    status: HealthStatus
    component: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    response_time_ms: Optional[float] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'status': self.status.value,
            'component': self.component,
            'timestamp': self.timestamp.isoformat(),
            'response_time_ms': self.response_time_ms,
            'error': self.error,
            'metadata': self.metadata
        }


@dataclass
class MetricDefinition:
    """Definition of a metric"""
    name: str
    metric_type: MetricType
    description: str
    labels: List[str] = field(default_factory=list)
    buckets: Optional[List[float]] = None  # For histograms
    quantiles: Optional[List[float]] = None  # For summaries


class HealthChecker:
    """System health checker with component monitoring"""
    
    def __init__(self):
        self._checks: Dict[str, Callable] = {}
        self._check_cache: Dict[str, HealthCheckResult] = {}
        self._cache_ttl_seconds = 30
        self._check_timeout_seconds = 10
    
    def register_check(self, name: str, check_func: Callable, timeout: Optional[int] = None) -> None:
        """Register a health check function"""
        self._checks[name] = {
            'func': check_func,
            'timeout': timeout or self._check_timeout_seconds
        }
        logger.debug(f"Registered health check: {name}")
    
    async def check_component(self, name: str, force_refresh: bool = False) -> HealthCheckResult:
        """Check health of a specific component"""
        if name not in self._checks:
            return HealthCheckResult(
                status=HealthStatus.UNKNOWN,
                component=name,
                error=f"No health check registered for {name}"
            )
        
        # Return cached result if still valid
        if not force_refresh and name in self._check_cache:
            cached = self._check_cache[name]
            age_seconds = (datetime.now(timezone.utc) - cached.timestamp).total_seconds()
            if age_seconds < self._cache_ttl_seconds:
                return cached
        
        check_info = self._checks[name]
        start_time = time.time()
        
        try:
            # Execute health check with timeout
            result = await asyncio.wait_for(
                check_info['func'](),
                timeout=check_info['timeout']
            )
            
            response_time = (time.time() - start_time) * 1000
            
            if isinstance(result, HealthCheckResult):
                result.response_time_ms = response_time
                health_result = result
            elif isinstance(result, dict):
                health_result = HealthCheckResult(
                    status=HealthStatus(result.get('status', 'unknown')),
                    component=name,
                    response_time_ms=response_time,
                    error=result.get('error'),
                    metadata=result.get('metadata', {})
                )
            elif isinstance(result, bool):
                health_result = HealthCheckResult(
                    status=HealthStatus.HEALTHY if result else HealthStatus.UNHEALTHY,
                    component=name,
                    response_time_ms=response_time
                )
            else:
                health_result = HealthCheckResult(
                    status=HealthStatus.HEALTHY,
                    component=name,
                    response_time_ms=response_time,
                    metadata={'result': str(result)}
                )
            
        except asyncio.TimeoutError:
            health_result = HealthCheckResult(
                status=HealthStatus.UNHEALTHY,
                component=name,
                response_time_ms=(time.time() - start_time) * 1000,
                error=f"Health check timeout after {check_info['timeout']} seconds"
            )
            
        except Exception as e:
            health_result = HealthCheckResult(
                status=HealthStatus.UNHEALTHY,
                component=name,
                response_time_ms=(time.time() - start_time) * 1000,
                error=str(e)
            )
            
        # Cache the result
        self._check_cache[name] = health_result
        return health_result
    
    async def check_all(self, force_refresh: bool = False) -> Dict[str, HealthCheckResult]:
        """Check health of all registered components"""
        results = {}
        
        # Run all health checks concurrently
        tasks = [
            self.check_component(name, force_refresh)
            for name in self._checks.keys()
        ]
        
        if tasks:
            completed_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for i, result in enumerate(completed_results):
                component_name = list(self._checks.keys())[i]
                
                if isinstance(result, Exception):
                    results[component_name] = HealthCheckResult(
                        status=HealthStatus.UNHEALTHY,
                        component=component_name,
                        error=str(result)
                    )
                else:
                    results[component_name] = result
        
        return results
    
    async def get_overall_health(self) -> HealthCheckResult:
        """Get overall system health status"""
        all_results = await self.check_all()
        
        if not all_results:
            return HealthCheckResult(
                status=HealthStatus.UNKNOWN,
                component="system",
                error="No health checks registered"
            )
        
        # Determine overall status
        unhealthy_count = sum(1 for r in all_results.values() if r.status == HealthStatus.UNHEALTHY)
        degraded_count = sum(1 for r in all_results.values() if r.status == HealthStatus.DEGRADED)
        
        if unhealthy_count > 0:
            overall_status = HealthStatus.UNHEALTHY
        elif degraded_count > 0:
            overall_status = HealthStatus.DEGRADED
        else:
            overall_status = HealthStatus.HEALTHY
        
        # Calculate average response time
        response_times = [r.response_time_ms for r in all_results.values() if r.response_time_ms is not None]
        avg_response_time = sum(response_times) / len(response_times) if response_times else None
        
        return HealthCheckResult(
            status=overall_status,
            component="system",
            response_time_ms=avg_response_time,
            metadata={
                'components': {name: result.to_dict() for name, result in all_results.items()},
                'total_components': len(all_results),
                'healthy_components': len(all_results) - unhealthy_count - degraded_count,
                'degraded_components': degraded_count,
                'unhealthy_components': unhealthy_count
            }
        )


class MetricsCollector:
    """Prometheus metrics collector with business-specific metrics"""
    
    def __init__(self, registry: CollectorRegistry = None):
        self.registry = registry or CollectorRegistry()
        self.metrics: Dict[str, Any] = {}
        self._define_default_metrics()
    
    def _define_default_metrics(self) -> None:
        """Define default system and application metrics"""
        default_metrics = [
            MetricDefinition(
                name="http_requests_total",
                metric_type=MetricType.COUNTER,
                description="Total HTTP requests",
                labels=["method", "endpoint", "status_code"]
            ),
            MetricDefinition(
                name="http_request_duration_seconds",
                metric_type=MetricType.HISTOGRAM,
                description="HTTP request duration in seconds",
                labels=["method", "endpoint"],
                buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
            ),
            MetricDefinition(
                name="database_connections_active",
                metric_type=MetricType.GAUGE,
                description="Active database connections"
            ),
            MetricDefinition(
                name="database_query_duration_seconds",
                metric_type=MetricType.HISTOGRAM,
                description="Database query duration in seconds",
                labels=["query_type"],
                buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0]
            ),
            MetricDefinition(
                name="cache_operations_total",
                metric_type=MetricType.COUNTER,
                description="Total cache operations",
                labels=["operation", "status"]
            ),
            MetricDefinition(
                name="cache_hit_ratio",
                metric_type=MetricType.GAUGE,
                description="Cache hit ratio"
            ),
            MetricDefinition(
                name="simulation_runs_total",
                metric_type=MetricType.COUNTER,
                description="Total Monte Carlo simulation runs",
                labels=["plan_type", "status"]
            ),
            MetricDefinition(
                name="simulation_duration_seconds",
                metric_type=MetricType.HISTOGRAM,
                description="Simulation execution time in seconds",
                labels=["plan_type"],
                buckets=[1.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0, 600.0]
            ),
            MetricDefinition(
                name="active_users_current",
                metric_type=MetricType.GAUGE,
                description="Currently active users"
            ),
            MetricDefinition(
                name="system_memory_usage_bytes",
                metric_type=MetricType.GAUGE,
                description="System memory usage in bytes"
            ),
            MetricDefinition(
                name="system_cpu_usage_percent",
                metric_type=MetricType.GAUGE,
                description="System CPU usage percentage"
            )
        ]
        
        for metric_def in default_metrics:
            self.create_metric(metric_def)
    
    def create_metric(self, metric_def: MetricDefinition) -> None:
        """Create a metric based on definition"""
        if metric_def.name in self.metrics:
            logger.warning(f"Metric {metric_def.name} already exists")
            return
        
        if metric_def.metric_type == MetricType.COUNTER:
            metric = Counter(
                metric_def.name,
                metric_def.description,
                metric_def.labels,
                registry=self.registry
            )
        elif metric_def.metric_type == MetricType.GAUGE:
            metric = Gauge(
                metric_def.name,
                metric_def.description,
                metric_def.labels,
                registry=self.registry
            )
        elif metric_def.metric_type == MetricType.HISTOGRAM:
            metric = Histogram(
                metric_def.name,
                metric_def.description,
                metric_def.labels,
                buckets=metric_def.buckets,
                registry=self.registry
            )
        elif metric_def.metric_type == MetricType.SUMMARY:
            metric = Summary(
                metric_def.name,
                metric_def.description,
                metric_def.labels,
                registry=self.registry
            )
        else:
            raise ValueError(f"Unsupported metric type: {metric_def.metric_type}")
        
        self.metrics[metric_def.name] = metric
        logger.debug(f"Created metric: {metric_def.name}")
    
    def increment_counter(self, name: str, labels: Dict[str, str] = None, amount: float = 1) -> None:
        """Increment a counter metric"""
        if name not in self.metrics:
            logger.warning(f"Metric {name} not found")
            return
        
        metric = self.metrics[name]
        if hasattr(metric, 'inc'):
            if labels:
                metric.labels(**labels).inc(amount)
            else:
                metric.inc(amount)
    
    def set_gauge(self, name: str, value: float, labels: Dict[str, str] = None) -> None:
        """Set a gauge metric value"""
        if name not in self.metrics:
            logger.warning(f"Metric {name} not found")
            return
        
        metric = self.metrics[name]
        if hasattr(metric, 'set'):
            if labels:
                metric.labels(**labels).set(value)
            else:
                metric.set(value)
    
    def observe_histogram(self, name: str, value: float, labels: Dict[str, str] = None) -> None:
        """Observe a value in a histogram metric"""
        if name not in self.metrics:
            logger.warning(f"Metric {name} not found")
            return
        
        metric = self.metrics[name]
        if hasattr(metric, 'observe'):
            if labels:
                metric.labels(**labels).observe(value)
            else:
                metric.observe(value)
    
    def get_metric(self, name: str):
        """Get a metric by name"""
        return self.metrics.get(name)
    
    def export_metrics(self) -> str:
        """Export metrics in Prometheus format"""
        return generate_latest(self.registry)


class SystemResourceMonitor:
    """Monitor system resources (CPU, memory, disk, etc.)"""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics_collector = metrics_collector
        self._monitoring = False
        self._monitor_task = None
        self._interval_seconds = 30
    
    async def start_monitoring(self, interval_seconds: int = 30) -> None:
        """Start resource monitoring"""
        self._interval_seconds = interval_seconds
        self._monitoring = True
        
        if self._monitor_task is None or self._monitor_task.done():
            self._monitor_task = asyncio.create_task(self._monitor_loop())
        
        logger.info(f"Started system resource monitoring (interval: {interval_seconds}s)")
    
    async def stop_monitoring(self) -> None:
        """Stop resource monitoring"""
        self._monitoring = False
        
        if self._monitor_task and not self._monitor_task.done():
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Stopped system resource monitoring")
    
    async def _monitor_loop(self) -> None:
        """Main monitoring loop"""
        while self._monitoring:
            try:
                await self._collect_system_metrics()
                await asyncio.sleep(self._interval_seconds)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in resource monitoring loop: {e}")
                await asyncio.sleep(self._interval_seconds)
    
    async def _collect_system_metrics(self) -> None:
        """Collect system resource metrics"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            self.metrics_collector.set_gauge("system_cpu_usage_percent", cpu_percent)
            
            # Memory usage
            memory = psutil.virtual_memory()
            self.metrics_collector.set_gauge("system_memory_usage_bytes", memory.used)
            self.metrics_collector.set_gauge("system_memory_total_bytes", memory.total)
            self.metrics_collector.set_gauge("system_memory_usage_percent", memory.percent)
            
            # Disk usage
            disk = psutil.disk_usage('/')
            self.metrics_collector.set_gauge("system_disk_usage_bytes", disk.used)
            self.metrics_collector.set_gauge("system_disk_total_bytes", disk.total)
            self.metrics_collector.set_gauge("system_disk_usage_percent", disk.percent)
            
            # Network I/O
            network = psutil.net_io_counters()
            if network:
                self.metrics_collector.set_gauge("system_network_bytes_sent", network.bytes_sent)
                self.metrics_collector.set_gauge("system_network_bytes_recv", network.bytes_recv)
            
            # Process info
            process = psutil.Process(os.getpid())
            self.metrics_collector.set_gauge("process_memory_usage_bytes", process.memory_info().rss)
            self.metrics_collector.set_gauge("process_cpu_usage_percent", process.cpu_percent())
            self.metrics_collector.set_gauge("process_open_files", len(process.open_files()))
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")


class PerformanceTracker:
    """Track application performance metrics"""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics_collector = metrics_collector
        self._response_times: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self._error_rates: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
    
    def track_request(
        self,
        method: str,
        endpoint: str,
        status_code: int,
        duration_seconds: float
    ) -> None:
        """Track HTTP request metrics"""
        # Count requests
        self.metrics_collector.increment_counter(
            "http_requests_total",
            labels={"method": method, "endpoint": endpoint, "status_code": str(status_code)}
        )
        
        # Track duration
        self.metrics_collector.observe_histogram(
            "http_request_duration_seconds",
            duration_seconds,
            labels={"method": method, "endpoint": endpoint}
        )
        
        # Store response time for analysis
        key = f"{method}:{endpoint}"
        self._response_times[key].append(duration_seconds)
        
        # Track error rate
        is_error = status_code >= 400
        self._error_rates[key].append(1 if is_error else 0)
    
    def track_database_query(self, query_type: str, duration_seconds: float) -> None:
        """Track database query performance"""
        self.metrics_collector.observe_histogram(
            "database_query_duration_seconds",
            duration_seconds,
            labels={"query_type": query_type}
        )
    
    def track_cache_operation(self, operation: str, success: bool) -> None:
        """Track cache operation metrics"""
        status = "success" if success else "error"
        self.metrics_collector.increment_counter(
            "cache_operations_total",
            labels={"operation": operation, "status": status}
        )
    
    def track_simulation(
        self,
        plan_type: str,
        duration_seconds: float,
        success: bool
    ) -> None:
        """Track simulation performance"""
        status = "success" if success else "error"
        
        self.metrics_collector.increment_counter(
            "simulation_runs_total",
            labels={"plan_type": plan_type, "status": status}
        )
        
        if success:
            self.metrics_collector.observe_histogram(
                "simulation_duration_seconds",
                duration_seconds,
                labels={"plan_type": plan_type}
            )
    
    def get_performance_summary(self, endpoint: str = None) -> Dict[str, Any]:
        """Get performance summary for analysis"""
        if endpoint:
            response_times = self._response_times.get(endpoint, deque())
            error_rates = self._error_rates.get(endpoint, deque())
        else:
            # Aggregate all endpoints
            response_times = deque()
            error_rates = deque()
            
            for times in self._response_times.values():
                response_times.extend(times)
            
            for errors in self._error_rates.values():
                error_rates.extend(errors)
        
        if not response_times:
            return {"error": "No data available"}
        
        response_list = list(response_times)
        error_list = list(error_rates)
        
        return {
            "request_count": len(response_list),
            "avg_response_time_ms": sum(response_list) * 1000 / len(response_list),
            "min_response_time_ms": min(response_list) * 1000,
            "max_response_time_ms": max(response_list) * 1000,
            "error_rate_percent": sum(error_list) / len(error_list) * 100 if error_list else 0,
            "p95_response_time_ms": sorted(response_list)[int(len(response_list) * 0.95)] * 1000 if response_list else 0,
            "p99_response_time_ms": sorted(response_list)[int(len(response_list) * 0.99)] * 1000 if response_list else 0
        }


# Decorators for automatic monitoring
def monitor_performance(
    endpoint_name: str = None,
    track_args: bool = False
):
    """Decorator to automatically monitor function performance"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            endpoint = endpoint_name or func.__name__
            success = True
            
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                raise
            finally:
                duration = time.time() - start_time
                
                # Track performance
                if hasattr(wrapper, '_performance_tracker'):
                    if hasattr(wrapper, '_is_request'):
                        # HTTP request tracking
                        status_code = 200 if success else 500
                        wrapper._performance_tracker.track_request(
                            "GET", endpoint, status_code, duration
                        )
                    else:
                        # Generic performance tracking
                        pass
        
        return wrapper
    return decorator


# Global instances
health_checker = HealthChecker()
metrics_collector = MetricsCollector()
performance_tracker = PerformanceTracker(metrics_collector)
resource_monitor = SystemResourceMonitor(metrics_collector)


async def setup_monitoring() -> None:
    """Setup monitoring infrastructure"""
    if settings.METRICS_ENABLED:
        # Start Prometheus metrics server
        if settings.PROMETHEUS_ENABLED:
            try:
                start_http_server(settings.METRICS_PORT)
                logger.info(f"Prometheus metrics server started on port {settings.METRICS_PORT}")
            except Exception as e:
                logger.error(f"Failed to start Prometheus server: {e}")
        
        # Start resource monitoring
        await resource_monitor.start_monitoring(settings.HEALTH_CHECK_INTERVAL_SECONDS)


async def shutdown_monitoring() -> None:
    """Shutdown monitoring infrastructure"""
    await resource_monitor.stop_monitoring()
    logger.info("Monitoring infrastructure shutdown completed")


@asynccontextmanager
async def monitoring_context():
    """Context manager for monitoring setup and cleanup"""
    try:
        await setup_monitoring()
        yield {
            'health_checker': health_checker,
            'metrics_collector': metrics_collector,
            'performance_tracker': performance_tracker,
            'resource_monitor': resource_monitor
        }
    finally:
        await shutdown_monitoring()