"""
Market Data Monitoring and Logging

Comprehensive monitoring and logging system for the market data streaming platform.
"""

import asyncio
import logging
import json
import time
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from collections import defaultdict, deque
from dataclasses import dataclass, asdict
from pathlib import Path
import structlog

from .config import config
from .models import DataProvider, MarketDataPoint


@dataclass
class PerformanceMetric:
    """Performance metric data structure"""
    name: str
    value: float
    timestamp: datetime
    tags: Dict[str, str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


@dataclass
class SystemHealth:
    """System health status"""
    component: str
    status: str  # healthy, degraded, unhealthy
    message: str
    timestamp: datetime
    details: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


class MetricsCollector:
    """Collects and aggregates performance metrics"""
    
    def __init__(self, max_points: int = 1000):
        self.max_points = max_points
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_points))
        self.counters: Dict[str, int] = defaultdict(int)
        self.gauges: Dict[str, float] = defaultdict(float)
        self.histograms: Dict[str, List[float]] = defaultdict(list)
        
        # Performance tracking
        self.start_time = datetime.utcnow()
        self.last_reset = datetime.utcnow()
    
    def record_metric(self, name: str, value: float, tags: Dict[str, str] = None):
        """Record a metric value"""
        metric = PerformanceMetric(
            name=name,
            value=value,
            timestamp=datetime.utcnow(),
            tags=tags or {}
        )
        
        self.metrics[name].append(metric)
    
    def increment_counter(self, name: str, value: int = 1, tags: Dict[str, str] = None):
        """Increment a counter"""
        key = f"{name}:{json.dumps(tags or {}, sort_keys=True)}"
        self.counters[key] += value
        
        # Also record as metric for trending
        self.record_metric(name, self.counters[key], tags)
    
    def set_gauge(self, name: str, value: float, tags: Dict[str, str] = None):
        """Set a gauge value"""
        key = f"{name}:{json.dumps(tags or {}, sort_keys=True)}"
        self.gauges[key] = value
        
        # Also record as metric for trending
        self.record_metric(name, value, tags)
    
    def record_histogram(self, name: str, value: float, tags: Dict[str, str] = None):
        """Record a histogram value"""
        key = f"{name}:{json.dumps(tags or {}, sort_keys=True)}"
        self.histograms[key].append(value)
        
        # Keep only recent values
        if len(self.histograms[key]) > 1000:
            self.histograms[key] = self.histograms[key][-500:]
        
        # Record percentiles as metrics
        values = self.histograms[key]
        if values:
            sorted_values = sorted(values)
            percentiles = [50, 90, 95, 99]
            
            for p in percentiles:
                idx = int(len(sorted_values) * p / 100)
                if idx < len(sorted_values):
                    self.record_metric(f"{name}_p{p}", sorted_values[idx], tags)
    
    def get_metric_summary(self, name: str, window_minutes: int = 5) -> Dict[str, Any]:
        """Get summary statistics for a metric"""
        if name not in self.metrics:
            return {}
        
        cutoff_time = datetime.utcnow() - timedelta(minutes=window_minutes)
        recent_metrics = [
            m for m in self.metrics[name] 
            if m.timestamp >= cutoff_time
        ]
        
        if not recent_metrics:
            return {}
        
        values = [m.value for m in recent_metrics]
        
        return {
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "avg": sum(values) / len(values),
            "sum": sum(values),
            "latest": values[-1] if values else None,
            "window_minutes": window_minutes
        }
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """Get all current metrics"""
        return {
            "counters": dict(self.counters),
            "gauges": dict(self.gauges),
            "uptime_seconds": (datetime.utcnow() - self.start_time).total_seconds(),
            "metrics_collected": sum(len(deque_obj) for deque_obj in self.metrics.values())
        }
    
    def reset_counters(self):
        """Reset all counters"""
        self.counters.clear()
        self.last_reset = datetime.utcnow()


class HealthChecker:
    """Monitors system health"""
    
    def __init__(self):
        self.health_checks: Dict[str, Callable] = {}
        self.health_status: Dict[str, SystemHealth] = {}
        self.check_intervals: Dict[str, int] = {}  # seconds
        self.last_checks: Dict[str, datetime] = {}
    
    def register_health_check(self, component: str, check_func: Callable, interval_seconds: int = 60):
        """Register a health check function"""
        self.health_checks[component] = check_func
        self.check_intervals[component] = interval_seconds
        self.last_checks[component] = datetime.min
    
    async def run_health_checks(self):
        """Run all health checks"""
        now = datetime.utcnow()
        
        for component, check_func in self.health_checks.items():
            last_check = self.last_checks[component]
            interval = self.check_intervals[component]
            
            if (now - last_check).total_seconds() >= interval:
                try:
                    is_healthy, message, details = await self._run_check(check_func)
                    
                    status = "healthy" if is_healthy else "unhealthy"
                    
                    self.health_status[component] = SystemHealth(
                        component=component,
                        status=status,
                        message=message,
                        timestamp=now,
                        details=details
                    )
                    
                    self.last_checks[component] = now
                    
                except Exception as e:
                    self.health_status[component] = SystemHealth(
                        component=component,
                        status="unhealthy",
                        message=f"Health check failed: {str(e)}",
                        timestamp=now,
                        details={"error": str(e)}
                    )
    
    async def _run_check(self, check_func: Callable) -> tuple:
        """Run a single health check"""
        if asyncio.iscoroutinefunction(check_func):
            return await check_func()
        else:
            return check_func()
    
    def get_overall_health(self) -> Dict[str, Any]:
        """Get overall system health"""
        if not self.health_status:
            return {
                "status": "unknown",
                "message": "No health checks configured",
                "components": {}
            }
        
        unhealthy_components = [
            comp for comp, health in self.health_status.items() 
            if health.status == "unhealthy"
        ]
        
        degraded_components = [
            comp for comp, health in self.health_status.items() 
            if health.status == "degraded"
        ]
        
        if unhealthy_components:
            overall_status = "unhealthy"
            message = f"Unhealthy components: {', '.join(unhealthy_components)}"
        elif degraded_components:
            overall_status = "degraded"
            message = f"Degraded components: {', '.join(degraded_components)}"
        else:
            overall_status = "healthy"
            message = "All components healthy"
        
        return {
            "status": overall_status,
            "message": message,
            "components": {
                comp: health.to_dict() 
                for comp, health in self.health_status.items()
            },
            "summary": {
                "total_components": len(self.health_status),
                "healthy": len([h for h in self.health_status.values() if h.status == "healthy"]),
                "degraded": len(degraded_components),
                "unhealthy": len(unhealthy_components)
            }
        }


class MarketDataMonitor:
    """Main monitoring system for market data platform"""
    
    def __init__(self):
        self.logger = self._setup_logging()
        self.metrics = MetricsCollector()
        self.health_checker = HealthChecker()
        
        # Monitoring state
        self._monitoring = False
        self._monitor_task: Optional[asyncio.Task] = None
        
        # Alert thresholds
        self.alert_thresholds = {
            "error_rate": 0.05,  # 5% error rate
            "response_time_p95": 5.0,  # 5 seconds
            "cache_hit_rate": 0.80,  # 80% cache hit rate
            "memory_usage": 0.90,  # 90% memory usage
        }
        
        # Alerts
        self.active_alerts: Dict[str, Dict] = {}
        self.alert_history: List[Dict] = []
    
    def _setup_logging(self) -> structlog.BoundLogger:
        """Setup structured logging"""
        # Configure structlog
        structlog.configure(
            processors=[
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.add_log_level,
                structlog.processors.JSONRenderer()
            ],
            wrapper_class=structlog.make_filtering_bound_logger(
                getattr(logging, config.log_level.upper(), logging.INFO)
            ),
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=True,
        )
        
        # Setup file logging if configured
        if config.log_file:
            log_file = Path(config.log_file)
            log_file.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(getattr(logging, config.log_level.upper(), logging.INFO))
            
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(formatter)
            
            # Add to root logger
            root_logger = logging.getLogger()
            root_logger.addHandler(file_handler)
        
        return structlog.get_logger("market_data.monitor")
    
    async def start_monitoring(self):
        """Start the monitoring system"""
        if self._monitoring:
            return
        
        self.logger.info("Starting market data monitoring")
        self._monitoring = True
        
        # Register health checks
        self._register_default_health_checks()
        
        # Start monitoring loop
        self._monitor_task = asyncio.create_task(self._monitoring_loop())
        
        self.logger.info("Market data monitoring started")
    
    async def stop_monitoring(self):
        """Stop the monitoring system"""
        if not self._monitoring:
            return
        
        self.logger.info("Stopping market data monitoring")
        self._monitoring = False
        
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("Market data monitoring stopped")
    
    def _register_default_health_checks(self):
        """Register default health checks"""
        
        async def check_memory_usage():
            """Check memory usage"""
            try:
                import psutil
                memory = psutil.virtual_memory()
                usage_percent = memory.percent / 100
                
                is_healthy = usage_percent < self.alert_thresholds["memory_usage"]
                message = f"Memory usage: {usage_percent:.1%}"
                details = {
                    "total": memory.total,
                    "available": memory.available,
                    "percent": memory.percent,
                    "used": memory.used
                }
                
                return is_healthy, message, details
            except ImportError:
                return True, "Memory monitoring not available (psutil not installed)", {}
        
        async def check_disk_space():
            """Check disk space"""
            try:
                import psutil
                disk = psutil.disk_usage('/')
                usage_percent = disk.percent / 100
                
                is_healthy = usage_percent < 0.90  # 90% threshold
                message = f"Disk usage: {usage_percent:.1%}"
                details = {
                    "total": disk.total,
                    "used": disk.used,
                    "free": disk.free,
                    "percent": disk.percent
                }
                
                return is_healthy, message, details
            except ImportError:
                return True, "Disk monitoring not available (psutil not installed)", {}
        
        self.health_checker.register_health_check("memory", check_memory_usage, 30)
        self.health_checker.register_health_check("disk", check_disk_space, 60)
    
    async def _monitoring_loop(self):
        """Main monitoring loop"""
        while self._monitoring:
            try:
                # Run health checks
                await self.health_checker.run_health_checks()
                
                # Check for alerts
                await self._check_alerts()
                
                # Log system status
                await self._log_system_status()
                
                # Wait before next iteration
                await asyncio.sleep(30)  # Monitor every 30 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error("Error in monitoring loop", error=str(e))
                await asyncio.sleep(60)  # Wait longer on error
    
    async def _check_alerts(self):
        """Check for alert conditions"""
        # Get current metrics
        error_rate = self._calculate_error_rate()
        if error_rate > self.alert_thresholds["error_rate"]:
            await self._trigger_alert("high_error_rate", {
                "current_rate": error_rate,
                "threshold": self.alert_thresholds["error_rate"],
                "message": f"Error rate {error_rate:.2%} exceeds threshold {self.alert_thresholds['error_rate']:.2%}"
            })
        
        # Check response times
        response_time_p95 = self._get_response_time_p95()
        if response_time_p95 and response_time_p95 > self.alert_thresholds["response_time_p95"]:
            await self._trigger_alert("high_response_time", {
                "current_p95": response_time_p95,
                "threshold": self.alert_thresholds["response_time_p95"],
                "message": f"95th percentile response time {response_time_p95:.2f}s exceeds threshold {self.alert_thresholds['response_time_p95']:.2f}s"
            })
    
    def _calculate_error_rate(self) -> float:
        """Calculate current error rate"""
        # This would calculate based on recent metrics
        # For now, return a placeholder
        return 0.0
    
    def _get_response_time_p95(self) -> Optional[float]:
        """Get 95th percentile response time"""
        # This would calculate based on recent metrics
        # For now, return a placeholder
        return None
    
    async def _trigger_alert(self, alert_type: str, details: Dict[str, Any]):
        """Trigger an alert"""
        alert_id = f"{alert_type}_{int(time.time())}"
        
        alert = {
            "id": alert_id,
            "type": alert_type,
            "timestamp": datetime.utcnow().isoformat(),
            "details": details,
            "status": "active"
        }
        
        self.active_alerts[alert_id] = alert
        self.alert_history.append(alert)
        
        # Keep only recent alerts in history
        if len(self.alert_history) > 1000:
            self.alert_history = self.alert_history[-500:]
        
        self.logger.warning("Alert triggered", alert=alert)
    
    async def _log_system_status(self):
        """Log periodic system status"""
        health = self.health_checker.get_overall_health()
        metrics = self.metrics.get_all_metrics()
        
        self.logger.info("System status", 
                        health_status=health["status"],
                        healthy_components=health["summary"]["healthy"],
                        total_components=health["summary"]["total_components"],
                        uptime_seconds=metrics.get("uptime_seconds", 0),
                        metrics_collected=metrics.get("metrics_collected", 0))
    
    # Market Data Specific Monitoring Methods
    
    def record_api_request(self, provider: DataProvider, symbol: str, success: bool, duration: float):
        """Record API request metrics"""
        tags = {
            "provider": provider.value,
            "symbol": symbol,
            "success": str(success)
        }
        
        self.metrics.increment_counter("api_requests_total", 1, tags)
        self.metrics.record_histogram("api_request_duration", duration, tags)
        
        if not success:
            self.metrics.increment_counter("api_errors_total", 1, tags)
    
    def record_cache_operation(self, operation: str, hit: bool, duration: float):
        """Record cache operation metrics"""
        tags = {
            "operation": operation,
            "hit": str(hit)
        }
        
        self.metrics.increment_counter("cache_operations_total", 1, tags)
        self.metrics.record_histogram("cache_operation_duration", duration, tags)
    
    def record_websocket_connection(self, action: str, client_count: int):
        """Record WebSocket connection metrics"""
        tags = {"action": action}
        
        self.metrics.increment_counter("websocket_connections", 1, tags)
        self.metrics.set_gauge("websocket_clients_connected", client_count)
    
    def record_alert_triggered(self, alert_type: str, symbol: str):
        """Record alert trigger metrics"""
        tags = {
            "alert_type": alert_type,
            "symbol": symbol
        }
        
        self.metrics.increment_counter("alerts_triggered_total", 1, tags)
    
    def record_data_validation(self, symbol: str, success: bool, anomalies: int):
        """Record data validation metrics"""
        tags = {
            "symbol": symbol,
            "success": str(success)
        }
        
        self.metrics.increment_counter("data_validations_total", 1, tags)
        self.metrics.set_gauge("data_anomalies_detected", anomalies, tags)
    
    def get_monitoring_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive monitoring dashboard data"""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "health": self.health_checker.get_overall_health(),
            "metrics": self.metrics.get_all_metrics(),
            "alerts": {
                "active": list(self.active_alerts.values()),
                "recent": self.alert_history[-10:],
                "total_triggered": len(self.alert_history)
            },
            "thresholds": self.alert_thresholds,
            "monitoring_status": "active" if self._monitoring else "inactive"
        }
    
    def get_performance_report(self, hours: int = 24) -> Dict[str, Any]:
        """Get performance report for the last N hours"""
        # This would analyze metrics over the specified time period
        # For now, return current status
        return {
            "period_hours": hours,
            "timestamp": datetime.utcnow().isoformat(),
            "summary": self.metrics.get_all_metrics(),
            "health_summary": self.health_checker.get_overall_health()["summary"]
        }