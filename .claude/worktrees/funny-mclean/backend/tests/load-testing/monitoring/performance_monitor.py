"""
Performance Monitoring and Metrics Collection

Integrates with Prometheus, Grafana, and other monitoring tools
"""

import time
import psutil
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import threading
import queue
from prometheus_client import (
    Counter, Histogram, Gauge, Summary,
    CollectorRegistry, generate_latest, push_to_gateway
)


@dataclass
class PerformanceMetrics:
    """Performance metrics snapshot"""
    timestamp: datetime
    
    # Response times
    response_time_p50: float
    response_time_p95: float
    response_time_p99: float
    response_time_max: float
    
    # Throughput
    requests_per_second: float
    successful_requests: int
    failed_requests: int
    error_rate: float
    
    # System resources
    cpu_usage: float
    memory_usage: float
    memory_available: float
    disk_io_read: float
    disk_io_write: float
    network_rx: float
    network_tx: float
    
    # Database metrics
    db_connections_active: int
    db_connections_idle: int
    db_query_time_avg: float
    db_slow_queries: int
    
    # Application metrics
    active_users: int
    websocket_connections: int
    cache_hit_rate: float
    queue_size: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data


class PrometheusMetricsCollector:
    """Collect and export metrics to Prometheus"""
    
    def __init__(self, push_gateway_url: str = "localhost:9091"):
        """
        Initialize Prometheus metrics collector
        
        Args:
            push_gateway_url: Prometheus push gateway URL
        """
        self.push_gateway_url = push_gateway_url
        self.registry = CollectorRegistry()
        
        # Define metrics
        self.request_counter = Counter(
            'load_test_requests_total',
            'Total number of requests',
            ['method', 'endpoint', 'status'],
            registry=self.registry
        )
        
        self.response_time_histogram = Histogram(
            'load_test_response_time_seconds',
            'Response time in seconds',
            ['method', 'endpoint'],
            buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10, 30, 60),
            registry=self.registry
        )
        
        self.error_counter = Counter(
            'load_test_errors_total',
            'Total number of errors',
            ['error_type', 'endpoint'],
            registry=self.registry
        )
        
        self.active_users_gauge = Gauge(
            'load_test_active_users',
            'Number of active users',
            registry=self.registry
        )
        
        self.throughput_gauge = Gauge(
            'load_test_throughput_rps',
            'Requests per second',
            registry=self.registry
        )
        
        self.cpu_usage_gauge = Gauge(
            'load_test_cpu_usage_percent',
            'CPU usage percentage',
            registry=self.registry
        )
        
        self.memory_usage_gauge = Gauge(
            'load_test_memory_usage_bytes',
            'Memory usage in bytes',
            registry=self.registry
        )
        
        self.db_connections_gauge = Gauge(
            'load_test_db_connections',
            'Database connections',
            ['state'],  # active, idle
            registry=self.registry
        )
        
        self.websocket_connections_gauge = Gauge(
            'load_test_websocket_connections',
            'WebSocket connections',
            registry=self.registry
        )
        
        self.simulation_time_summary = Summary(
            'load_test_simulation_time_seconds',
            'Monte Carlo simulation time',
            ['simulation_type'],
            registry=self.registry
        )
        
        self.report_generation_time_summary = Summary(
            'load_test_report_generation_seconds',
            'Report generation time',
            ['report_type'],
            registry=self.registry
        )
    
    def record_request(
        self,
        method: str,
        endpoint: str,
        status: int,
        response_time: float,
        error: Optional[str] = None
    ):
        """Record request metrics"""
        self.request_counter.labels(
            method=method,
            endpoint=endpoint,
            status=str(status)
        ).inc()
        
        self.response_time_histogram.labels(
            method=method,
            endpoint=endpoint
        ).observe(response_time)
        
        if error:
            self.error_counter.labels(
                error_type=error,
                endpoint=endpoint
            ).inc()
    
    def update_system_metrics(self, metrics: PerformanceMetrics):
        """Update system metrics"""
        self.active_users_gauge.set(metrics.active_users)
        self.throughput_gauge.set(metrics.requests_per_second)
        self.cpu_usage_gauge.set(metrics.cpu_usage)
        self.memory_usage_gauge.set(metrics.memory_usage)
        self.websocket_connections_gauge.set(metrics.websocket_connections)
        
        self.db_connections_gauge.labels(state='active').set(metrics.db_connections_active)
        self.db_connections_gauge.labels(state='idle').set(metrics.db_connections_idle)
    
    def push_metrics(self, job_name: str = "load_test"):
        """Push metrics to Prometheus push gateway"""
        try:
            push_to_gateway(
                self.push_gateway_url,
                job=job_name,
                registry=self.registry
            )
        except Exception as e:
            print(f"Failed to push metrics to Prometheus: {e}")


class SystemResourceMonitor:
    """Monitor system resources during load testing"""
    
    def __init__(self, interval: int = 5):
        """
        Initialize resource monitor
        
        Args:
            interval: Monitoring interval in seconds
        """
        self.interval = interval
        self.monitoring = False
        self.metrics_queue = queue.Queue()
        self.monitor_thread = None
        
        # Track network I/O
        self.last_net_io = psutil.net_io_counters()
        self.last_disk_io = psutil.disk_io_counters()
        self.last_time = time.time()
    
    def start_monitoring(self):
        """Start resource monitoring"""
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        """Stop resource monitoring"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.monitoring:
            metrics = self._collect_metrics()
            self.metrics_queue.put(metrics)
            time.sleep(self.interval)
    
    def _collect_metrics(self) -> Dict[str, float]:
        """Collect current system metrics"""
        current_time = time.time()
        time_delta = current_time - self.last_time
        
        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_freq = psutil.cpu_freq()
        
        # Memory metrics
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        # Disk I/O
        disk_io = psutil.disk_io_counters()
        disk_read_rate = (disk_io.read_bytes - self.last_disk_io.read_bytes) / time_delta
        disk_write_rate = (disk_io.write_bytes - self.last_disk_io.write_bytes) / time_delta
        
        # Network I/O
        net_io = psutil.net_io_counters()
        net_rx_rate = (net_io.bytes_recv - self.last_net_io.bytes_recv) / time_delta
        net_tx_rate = (net_io.bytes_sent - self.last_net_io.bytes_sent) / time_delta
        
        # Update last values
        self.last_net_io = net_io
        self.last_disk_io = disk_io
        self.last_time = current_time
        
        # Process metrics
        process = psutil.Process()
        process_memory = process.memory_info()
        process_connections = len(process.connections())
        
        return {
            "timestamp": datetime.now().isoformat(),
            "cpu_percent": cpu_percent,
            "cpu_freq_current": cpu_freq.current if cpu_freq else 0,
            "memory_percent": memory.percent,
            "memory_used": memory.used,
            "memory_available": memory.available,
            "swap_percent": swap.percent,
            "disk_read_rate": disk_read_rate,
            "disk_write_rate": disk_write_rate,
            "network_rx_rate": net_rx_rate,
            "network_tx_rate": net_tx_rate,
            "process_memory_rss": process_memory.rss,
            "process_memory_vms": process_memory.vms,
            "process_connections": process_connections
        }
    
    def get_metrics(self) -> List[Dict[str, float]]:
        """Get collected metrics"""
        metrics = []
        while not self.metrics_queue.empty():
            metrics.append(self.metrics_queue.get())
        return metrics


class DatabaseMetricsCollector:
    """Collect database performance metrics"""
    
    def __init__(self, db_url: str):
        """
        Initialize database metrics collector
        
        Args:
            db_url: Database connection URL
        """
        self.db_url = db_url
        self.metrics = []
    
    def collect_metrics(self) -> Dict[str, Any]:
        """Collect current database metrics"""
        # This would connect to the actual database
        # For now, returning simulated metrics
        return {
            "timestamp": datetime.now().isoformat(),
            "connections_active": 45,
            "connections_idle": 55,
            "connections_waiting": 5,
            "queries_per_second": 250,
            "slow_queries": 3,
            "avg_query_time_ms": 12.5,
            "cache_hit_ratio": 0.92,
            "deadlocks": 0,
            "replication_lag_seconds": 0.5
        }


class PerformanceRegressionDetector:
    """Detect performance regressions"""
    
    def __init__(self, baseline_metrics: Dict[str, float], threshold: float = 0.1):
        """
        Initialize regression detector
        
        Args:
            baseline_metrics: Baseline performance metrics
            threshold: Regression threshold (10% by default)
        """
        self.baseline_metrics = baseline_metrics
        self.threshold = threshold
        self.regressions = []
    
    def check_regression(self, current_metrics: Dict[str, float]) -> List[Dict[str, Any]]:
        """
        Check for performance regressions
        
        Args:
            current_metrics: Current performance metrics
            
        Returns:
            List of detected regressions
        """
        regressions = []
        
        metrics_to_check = [
            ("response_time_p95", "increase"),
            ("response_time_p99", "increase"),
            ("error_rate", "increase"),
            ("throughput", "decrease"),
            ("cpu_usage", "increase"),
            ("memory_usage", "increase")
        ]
        
        for metric_name, direction in metrics_to_check:
            if metric_name in self.baseline_metrics and metric_name in current_metrics:
                baseline_value = self.baseline_metrics[metric_name]
                current_value = current_metrics[metric_name]
                
                if baseline_value > 0:
                    change_percent = ((current_value - baseline_value) / baseline_value) * 100
                    
                    is_regression = False
                    if direction == "increase" and change_percent > self.threshold * 100:
                        is_regression = True
                    elif direction == "decrease" and change_percent < -self.threshold * 100:
                        is_regression = True
                    
                    if is_regression:
                        regressions.append({
                            "metric": metric_name,
                            "baseline": baseline_value,
                            "current": current_value,
                            "change_percent": change_percent,
                            "severity": self._calculate_severity(change_percent)
                        })
        
        self.regressions = regressions
        return regressions
    
    def _calculate_severity(self, change_percent: float) -> str:
        """Calculate regression severity"""
        abs_change = abs(change_percent)
        if abs_change < 20:
            return "low"
        elif abs_change < 50:
            return "medium"
        else:
            return "high"
    
    def generate_alert(self, regressions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate alert for regressions"""
        if not regressions:
            return None
        
        high_severity = [r for r in regressions if r["severity"] == "high"]
        medium_severity = [r for r in regressions if r["severity"] == "medium"]
        
        alert = {
            "timestamp": datetime.now().isoformat(),
            "type": "performance_regression",
            "severity": "high" if high_severity else "medium" if medium_severity else "low",
            "summary": f"Detected {len(regressions)} performance regressions",
            "regressions": regressions,
            "recommended_actions": self._get_recommendations(regressions)
        }
        
        return alert
    
    def _get_recommendations(self, regressions: List[Dict[str, Any]]) -> List[str]:
        """Get recommendations based on regressions"""
        recommendations = []
        
        for regression in regressions:
            metric = regression["metric"]
            
            if "response_time" in metric:
                recommendations.append(
                    f"Investigate slow queries and optimize database indexes for {metric}"
                )
            elif metric == "error_rate":
                recommendations.append(
                    "Check application logs for error patterns and fix identified issues"
                )
            elif metric == "throughput":
                recommendations.append(
                    "Scale horizontally or optimize resource-intensive operations"
                )
            elif metric == "cpu_usage":
                recommendations.append(
                    "Profile CPU-intensive operations and optimize algorithms"
                )
            elif metric == "memory_usage":
                recommendations.append(
                    "Check for memory leaks and optimize memory allocation"
                )
        
        return list(set(recommendations))  # Remove duplicates


class AlertingService:
    """Send alerts for performance issues"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize alerting service
        
        Args:
            config: Alerting configuration
        """
        self.config = config
        self.slack_webhook = config.get("slack_webhook_url")
        self.email_config = config.get("email")
        self.pagerduty_key = config.get("pagerduty_integration_key")
    
    def send_alert(self, alert: Dict[str, Any]):
        """Send alert through configured channels"""
        if self.slack_webhook:
            self._send_slack_alert(alert)
        
        if self.email_config:
            self._send_email_alert(alert)
        
        if self.pagerduty_key and alert.get("severity") == "high":
            self._send_pagerduty_alert(alert)
    
    def _send_slack_alert(self, alert: Dict[str, Any]):
        """Send alert to Slack"""
        try:
            message = {
                "text": f"🚨 Performance Alert: {alert['summary']}",
                "attachments": [
                    {
                        "color": "danger" if alert["severity"] == "high" else "warning",
                        "fields": [
                            {
                                "title": "Severity",
                                "value": alert["severity"].upper(),
                                "short": True
                            },
                            {
                                "title": "Time",
                                "value": alert["timestamp"],
                                "short": True
                            },
                            {
                                "title": "Regressions",
                                "value": "\n".join([
                                    f"• {r['metric']}: {r['change_percent']:.1f}% change"
                                    for r in alert.get("regressions", [])[:5]
                                ])
                            },
                            {
                                "title": "Recommendations",
                                "value": "\n".join([
                                    f"• {rec}"
                                    for rec in alert.get("recommended_actions", [])[:3]
                                ])
                            }
                        ]
                    }
                ]
            }
            
            response = requests.post(self.slack_webhook, json=message)
            response.raise_for_status()
        except Exception as e:
            print(f"Failed to send Slack alert: {e}")
    
    def _send_email_alert(self, alert: Dict[str, Any]):
        """Send email alert"""
        # Implementation would use email service
        pass
    
    def _send_pagerduty_alert(self, alert: Dict[str, Any]):
        """Send PagerDuty alert for high severity issues"""
        try:
            payload = {
                "routing_key": self.pagerduty_key,
                "event_action": "trigger",
                "payload": {
                    "summary": alert["summary"],
                    "severity": "error" if alert["severity"] == "high" else "warning",
                    "source": "load_testing",
                    "timestamp": alert["timestamp"],
                    "custom_details": alert
                }
            }
            
            response = requests.post(
                "https://events.pagerduty.com/v2/enqueue",
                json=payload
            )
            response.raise_for_status()
        except Exception as e:
            print(f"Failed to send PagerDuty alert: {e}")


class MonitoringDashboard:
    """Generate monitoring dashboard data"""
    
    def __init__(self):
        """Initialize dashboard"""
        self.metrics_history = []
        self.current_metrics = None
    
    def update_metrics(self, metrics: PerformanceMetrics):
        """Update dashboard metrics"""
        self.current_metrics = metrics
        self.metrics_history.append(metrics)
        
        # Keep only last hour of metrics
        cutoff_time = datetime.now() - timedelta(hours=1)
        self.metrics_history = [
            m for m in self.metrics_history
            if m.timestamp > cutoff_time
        ]
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get dashboard data for visualization"""
        if not self.current_metrics:
            return {}
        
        return {
            "current": {
                "timestamp": self.current_metrics.timestamp.isoformat(),
                "active_users": self.current_metrics.active_users,
                "rps": self.current_metrics.requests_per_second,
                "error_rate": self.current_metrics.error_rate * 100,
                "p95_response_time": self.current_metrics.response_time_p95,
                "cpu_usage": self.current_metrics.cpu_usage,
                "memory_usage": self.current_metrics.memory_usage / (1024 ** 3)  # GB
            },
            "history": {
                "timestamps": [m.timestamp.isoformat() for m in self.metrics_history[-20:]],
                "rps": [m.requests_per_second for m in self.metrics_history[-20:]],
                "response_times": [m.response_time_p95 for m in self.metrics_history[-20:]],
                "error_rates": [m.error_rate * 100 for m in self.metrics_history[-20:]],
                "cpu_usage": [m.cpu_usage for m in self.metrics_history[-20:]]
            },
            "summary": {
                "total_requests": sum(m.successful_requests + m.failed_requests 
                                     for m in self.metrics_history),
                "total_errors": sum(m.failed_requests for m in self.metrics_history),
                "avg_response_time": sum(m.response_time_p50 for m in self.metrics_history) / 
                                   len(self.metrics_history) if self.metrics_history else 0,
                "peak_rps": max(m.requests_per_second for m in self.metrics_history) 
                           if self.metrics_history else 0
            }
        }
    
    def export_grafana_dashboard(self) -> Dict[str, Any]:
        """Export Grafana dashboard configuration"""
        return {
            "dashboard": {
                "title": "Load Testing Performance Dashboard",
                "panels": [
                    {
                        "title": "Requests Per Second",
                        "type": "graph",
                        "targets": [
                            {"expr": "rate(load_test_requests_total[1m])"}
                        ]
                    },
                    {
                        "title": "Response Time (P95)",
                        "type": "graph",
                        "targets": [
                            {"expr": "histogram_quantile(0.95, load_test_response_time_seconds)"}
                        ]
                    },
                    {
                        "title": "Error Rate",
                        "type": "graph",
                        "targets": [
                            {"expr": "rate(load_test_errors_total[1m])"}
                        ]
                    },
                    {
                        "title": "Active Users",
                        "type": "stat",
                        "targets": [
                            {"expr": "load_test_active_users"}
                        ]
                    },
                    {
                        "title": "CPU Usage",
                        "type": "gauge",
                        "targets": [
                            {"expr": "load_test_cpu_usage_percent"}
                        ]
                    },
                    {
                        "title": "Memory Usage",
                        "type": "gauge",
                        "targets": [
                            {"expr": "load_test_memory_usage_bytes / 1024 / 1024 / 1024"}
                        ]
                    }
                ]
            }
        }