"""
Real-time Performance Monitoring Dashboard

Comprehensive monitoring with:
- Real-time metrics collection
- Performance anomaly detection
- Automated alerting
- Historical trend analysis
- Resource utilization tracking
"""

import asyncio
import time
import psutil
import statistics
from typing import Dict, List, Any, Optional, Deque, Callable
from datetime import datetime, timedelta
from collections import deque, defaultdict
from dataclasses import dataclass, field
from enum import Enum
import json

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import numpy as np

logger = None  # Will be initialized from main app


class MetricType(Enum):
    """Types of metrics to monitor"""
    CPU = "cpu"
    MEMORY = "memory"
    DISK = "disk"
    NETWORK = "network"
    DATABASE = "database"
    CACHE = "cache"
    API = "api"
    GPU = "gpu"
    CUSTOM = "custom"


class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class MetricPoint:
    """Single metric data point"""
    timestamp: datetime
    value: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Alert:
    """Performance alert"""
    id: str
    metric_type: MetricType
    severity: AlertSeverity
    message: str
    value: float
    threshold: float
    timestamp: datetime
    resolved: bool = False
    resolution_time: Optional[datetime] = None


@dataclass
class PerformanceMetrics:
    """Comprehensive performance metrics"""
    # System metrics
    cpu_percent: float
    memory_percent: float
    memory_used_gb: float
    memory_available_gb: float
    disk_io_read_mbps: float
    disk_io_write_mbps: float
    network_sent_mbps: float
    network_recv_mbps: float
    
    # Application metrics
    request_rate: float
    response_time_p50: float
    response_time_p95: float
    response_time_p99: float
    error_rate: float
    active_connections: int
    
    # Database metrics
    db_connections_active: int
    db_connections_idle: int
    db_query_time_avg: float
    db_slow_queries: int
    
    # Cache metrics
    cache_hit_rate: float
    cache_memory_used_mb: float
    cache_evictions: int
    
    # GPU metrics (if available)
    gpu_utilization: Optional[float] = None
    gpu_memory_used_gb: Optional[float] = None
    gpu_temperature: Optional[float] = None
    
    # Timestamp
    timestamp: datetime = field(default_factory=datetime.now)


class MetricsCollector:
    """
    Collect and aggregate performance metrics
    """
    
    def __init__(
        self,
        collection_interval: float = 1.0,
        history_size: int = 3600  # 1 hour at 1-second intervals
    ):
        """
        Initialize metrics collector
        
        Args:
            collection_interval: Interval between collections (seconds)
            history_size: Number of historical points to keep
        """
        self.collection_interval = collection_interval
        self.history_size = history_size
        
        # Metric histories
        self.histories: Dict[str, Deque[MetricPoint]] = defaultdict(
            lambda: deque(maxlen=history_size)
        )
        
        # System resource trackers
        self.process = psutil.Process()
        self.disk_io_prev = psutil.disk_io_counters()
        self.net_io_prev = psutil.net_io_counters()
        self.prev_time = time.time()
        
        # Application metrics
        self.request_times: Deque[float] = deque(maxlen=1000)
        self.request_count = 0
        self.error_count = 0
        self.active_connections = 0
        
        # Database metrics
        self.db_query_times: Deque[float] = deque(maxlen=1000)
        self.db_connections = {'active': 0, 'idle': 0}
        
        # Cache metrics
        self.cache_hits = 0
        self.cache_misses = 0
        
        # GPU metrics (if available)
        self.gpu_available = self._check_gpu_availability()
    
    def _check_gpu_availability(self) -> bool:
        """Check if GPU monitoring is available"""
        try:
            import pynvml
            pynvml.nvmlInit()
            return True
        except:
            return False
    
    async def collect_metrics(self) -> PerformanceMetrics:
        """
        Collect current performance metrics
        
        Returns:
            Current performance metrics
        """
        current_time = time.time()
        time_delta = current_time - self.prev_time
        
        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=0.1)
        self.histories['cpu'].append(
            MetricPoint(datetime.now(), cpu_percent)
        )
        
        # Memory metrics
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_used_gb = memory.used / (1024**3)
        memory_available_gb = memory.available / (1024**3)
        
        self.histories['memory'].append(
            MetricPoint(datetime.now(), memory_percent)
        )
        
        # Disk I/O metrics
        disk_io = psutil.disk_io_counters()
        disk_read_mbps = (disk_io.read_bytes - self.disk_io_prev.read_bytes) / time_delta / (1024**2)
        disk_write_mbps = (disk_io.write_bytes - self.disk_io_prev.write_bytes) / time_delta / (1024**2)
        self.disk_io_prev = disk_io
        
        # Network I/O metrics
        net_io = psutil.net_io_counters()
        network_sent_mbps = (net_io.bytes_sent - self.net_io_prev.bytes_sent) / time_delta / (1024**2)
        network_recv_mbps = (net_io.bytes_recv - self.net_io_prev.bytes_recv) / time_delta / (1024**2)
        self.net_io_prev = net_io
        
        # Application metrics
        request_rate = self.request_count / time_delta if time_delta > 0 else 0
        
        response_times = list(self.request_times) if self.request_times else [0]
        response_time_p50 = np.percentile(response_times, 50)
        response_time_p95 = np.percentile(response_times, 95)
        response_time_p99 = np.percentile(response_times, 99)
        
        error_rate = (self.error_count / self.request_count * 100) if self.request_count > 0 else 0
        
        # Database metrics
        db_query_times = list(self.db_query_times) if self.db_query_times else [0]
        db_query_time_avg = statistics.mean(db_query_times)
        db_slow_queries = sum(1 for t in db_query_times if t > 100)  # > 100ms
        
        # Cache metrics
        total_cache_ops = self.cache_hits + self.cache_misses
        cache_hit_rate = (self.cache_hits / total_cache_ops * 100) if total_cache_ops > 0 else 0
        
        # GPU metrics (if available)
        gpu_metrics = await self._collect_gpu_metrics() if self.gpu_available else {}
        
        # Reset counters
        self.request_count = 0
        self.error_count = 0
        self.prev_time = current_time
        
        return PerformanceMetrics(
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            memory_used_gb=memory_used_gb,
            memory_available_gb=memory_available_gb,
            disk_io_read_mbps=disk_read_mbps,
            disk_io_write_mbps=disk_write_mbps,
            network_sent_mbps=network_sent_mbps,
            network_recv_mbps=network_recv_mbps,
            request_rate=request_rate,
            response_time_p50=response_time_p50,
            response_time_p95=response_time_p95,
            response_time_p99=response_time_p99,
            error_rate=error_rate,
            active_connections=self.active_connections,
            db_connections_active=self.db_connections['active'],
            db_connections_idle=self.db_connections['idle'],
            db_query_time_avg=db_query_time_avg,
            db_slow_queries=db_slow_queries,
            cache_hit_rate=cache_hit_rate,
            cache_memory_used_mb=0,  # Would come from Redis INFO
            cache_evictions=0,  # Would come from Redis INFO
            **gpu_metrics
        )
    
    async def _collect_gpu_metrics(self) -> Dict[str, float]:
        """Collect GPU metrics if available"""
        try:
            import pynvml
            
            handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            
            # GPU utilization
            util = pynvml.nvmlDeviceGetUtilizationRates(handle)
            gpu_utilization = util.gpu
            
            # GPU memory
            mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
            gpu_memory_used_gb = mem_info.used / (1024**3)
            
            # GPU temperature
            gpu_temperature = pynvml.nvmlDeviceGetTemperature(
                handle,
                pynvml.NVML_TEMPERATURE_GPU
            )
            
            return {
                'gpu_utilization': gpu_utilization,
                'gpu_memory_used_gb': gpu_memory_used_gb,
                'gpu_temperature': gpu_temperature
            }
        except:
            return {}
    
    def record_request(self, response_time: float, is_error: bool = False):
        """Record API request metrics"""
        self.request_count += 1
        self.request_times.append(response_time)
        
        if is_error:
            self.error_count += 1
    
    def record_db_query(self, query_time: float):
        """Record database query metrics"""
        self.db_query_times.append(query_time)
    
    def record_cache_operation(self, is_hit: bool):
        """Record cache operation"""
        if is_hit:
            self.cache_hits += 1
        else:
            self.cache_misses += 1
    
    def update_connections(self, active: int = None, total: int = None):
        """Update connection counts"""
        if active is not None:
            self.active_connections = active
        
        if total is not None and active is not None:
            self.db_connections['active'] = active
            self.db_connections['idle'] = total - active


class AnomalyDetector:
    """
    Detect performance anomalies using statistical methods
    """
    
    def __init__(
        self,
        window_size: int = 60,
        z_score_threshold: float = 3.0
    ):
        """
        Initialize anomaly detector
        
        Args:
            window_size: Window size for moving statistics
            z_score_threshold: Z-score threshold for anomaly detection
        """
        self.window_size = window_size
        self.z_score_threshold = z_score_threshold
        
        # Moving statistics
        self.windows: Dict[str, Deque[float]] = defaultdict(
            lambda: deque(maxlen=window_size)
        )
    
    def detect_anomaly(
        self,
        metric_name: str,
        value: float
    ) -> Optional[float]:
        """
        Detect if value is anomalous
        
        Args:
            metric_name: Name of the metric
            value: Current value
            
        Returns:
            Z-score if anomalous, None otherwise
        """
        window = self.windows[metric_name]
        window.append(value)
        
        if len(window) < self.window_size:
            return None
        
        # Calculate statistics
        mean = statistics.mean(window)
        stdev = statistics.stdev(window)
        
        if stdev == 0:
            return None
        
        # Calculate Z-score
        z_score = abs((value - mean) / stdev)
        
        if z_score > self.z_score_threshold:
            return z_score
        
        return None


class AlertManager:
    """
    Manage performance alerts and notifications
    """
    
    def __init__(self):
        """Initialize alert manager"""
        self.alerts: Dict[str, Alert] = {}
        self.alert_history: Deque[Alert] = deque(maxlen=1000)
        
        # Alert thresholds
        self.thresholds = {
            MetricType.CPU: {'warning': 70, 'error': 85, 'critical': 95},
            MetricType.MEMORY: {'warning': 70, 'error': 85, 'critical': 95},
            MetricType.DISK: {'warning': 80, 'error': 90, 'critical': 95},
            MetricType.API: {
                'response_time': {'warning': 500, 'error': 1000, 'critical': 2000},
                'error_rate': {'warning': 1, 'error': 5, 'critical': 10}
            },
            MetricType.DATABASE: {
                'query_time': {'warning': 100, 'error': 500, 'critical': 1000},
                'connections': {'warning': 80, 'error': 90, 'critical': 95}
            },
            MetricType.CACHE: {
                'hit_rate': {'warning': 60, 'error': 40, 'critical': 20}
            }
        }
        
        # Alert callbacks
        self.alert_callbacks: List[Callable] = []
    
    def check_thresholds(self, metrics: PerformanceMetrics) -> List[Alert]:
        """
        Check metrics against thresholds
        
        Args:
            metrics: Current metrics
            
        Returns:
            List of new alerts
        """
        new_alerts = []
        
        # Check CPU
        cpu_alert = self._check_metric(
            MetricType.CPU,
            metrics.cpu_percent,
            self.thresholds[MetricType.CPU]
        )
        if cpu_alert:
            new_alerts.append(cpu_alert)
        
        # Check Memory
        memory_alert = self._check_metric(
            MetricType.MEMORY,
            metrics.memory_percent,
            self.thresholds[MetricType.MEMORY]
        )
        if memory_alert:
            new_alerts.append(memory_alert)
        
        # Check API response time
        if metrics.response_time_p95 > self.thresholds[MetricType.API]['response_time']['warning']:
            severity = self._get_severity(
                metrics.response_time_p95,
                self.thresholds[MetricType.API]['response_time']
            )
            alert = Alert(
                id=f"api_response_{int(time.time())}",
                metric_type=MetricType.API,
                severity=severity,
                message=f"High API response time: {metrics.response_time_p95:.0f}ms",
                value=metrics.response_time_p95,
                threshold=self.thresholds[MetricType.API]['response_time'][severity.value],
                timestamp=datetime.now()
            )
            new_alerts.append(alert)
        
        # Check error rate
        if metrics.error_rate > self.thresholds[MetricType.API]['error_rate']['warning']:
            severity = self._get_severity(
                metrics.error_rate,
                self.thresholds[MetricType.API]['error_rate']
            )
            alert = Alert(
                id=f"api_errors_{int(time.time())}",
                metric_type=MetricType.API,
                severity=severity,
                message=f"High error rate: {metrics.error_rate:.1f}%",
                value=metrics.error_rate,
                threshold=self.thresholds[MetricType.API]['error_rate'][severity.value],
                timestamp=datetime.now()
            )
            new_alerts.append(alert)
        
        # Process new alerts
        for alert in new_alerts:
            self.alerts[alert.id] = alert
            self.alert_history.append(alert)
            
            # Trigger callbacks
            for callback in self.alert_callbacks:
                asyncio.create_task(callback(alert))
        
        return new_alerts
    
    def _check_metric(
        self,
        metric_type: MetricType,
        value: float,
        thresholds: Dict[str, float]
    ) -> Optional[Alert]:
        """Check single metric against thresholds"""
        if value > thresholds['warning']:
            severity = self._get_severity(value, thresholds)
            
            return Alert(
                id=f"{metric_type.value}_{int(time.time())}",
                metric_type=metric_type,
                severity=severity,
                message=f"High {metric_type.value}: {value:.1f}%",
                value=value,
                threshold=thresholds[severity.value],
                timestamp=datetime.now()
            )
        
        return None
    
    def _get_severity(
        self,
        value: float,
        thresholds: Dict[str, float]
    ) -> AlertSeverity:
        """Determine alert severity based on value"""
        if value >= thresholds.get('critical', float('inf')):
            return AlertSeverity.CRITICAL
        elif value >= thresholds.get('error', float('inf')):
            return AlertSeverity.ERROR
        elif value >= thresholds.get('warning', float('inf')):
            return AlertSeverity.WARNING
        else:
            return AlertSeverity.INFO
    
    def resolve_alert(self, alert_id: str):
        """Mark alert as resolved"""
        if alert_id in self.alerts:
            alert = self.alerts[alert_id]
            alert.resolved = True
            alert.resolution_time = datetime.now()
    
    def add_callback(self, callback: Callable):
        """Add alert callback"""
        self.alert_callbacks.append(callback)


class MonitoringDashboard:
    """
    Real-time monitoring dashboard with WebSocket support
    """
    
    def __init__(
        self,
        app: FastAPI,
        collector: MetricsCollector,
        detector: AnomalyDetector,
        alert_manager: AlertManager
    ):
        """
        Initialize monitoring dashboard
        
        Args:
            app: FastAPI application
            collector: Metrics collector
            detector: Anomaly detector
            alert_manager: Alert manager
        """
        self.app = app
        self.collector = collector
        self.detector = detector
        self.alert_manager = alert_manager
        
        # WebSocket connections
        self.connections: List[WebSocket] = []
        
        # Setup routes
        self._setup_routes()
        
        # Start monitoring task
        asyncio.create_task(self._monitoring_loop())
    
    def _setup_routes(self):
        """Setup dashboard routes"""
        
        @self.app.get("/monitoring/dashboard")
        async def dashboard():
            """Serve monitoring dashboard HTML"""
            return HTMLResponse(self._generate_dashboard_html())
        
        @self.app.websocket("/monitoring/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket endpoint for real-time metrics"""
            await websocket.accept()
            self.connections.append(websocket)
            
            try:
                while True:
                    # Keep connection alive
                    await websocket.receive_text()
            except WebSocketDisconnect:
                self.connections.remove(websocket)
        
        @self.app.get("/monitoring/metrics")
        async def get_metrics():
            """Get current metrics snapshot"""
            metrics = await self.collector.collect_metrics()
            return metrics.__dict__
        
        @self.app.get("/monitoring/alerts")
        async def get_alerts():
            """Get active alerts"""
            return [
                alert.__dict__ for alert in self.alert_manager.alerts.values()
                if not alert.resolved
            ]
    
    async def _monitoring_loop(self):
        """Main monitoring loop"""
        while True:
            try:
                # Collect metrics
                metrics = await self.collector.collect_metrics()
                
                # Check for anomalies
                anomalies = self._check_anomalies(metrics)
                
                # Check thresholds
                alerts = self.alert_manager.check_thresholds(metrics)
                
                # Broadcast to WebSocket clients
                await self._broadcast_metrics(metrics, anomalies, alerts)
                
                # Sleep until next collection
                await asyncio.sleep(self.collector.collection_interval)
                
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                await asyncio.sleep(5)
    
    def _check_anomalies(self, metrics: PerformanceMetrics) -> Dict[str, float]:
        """Check for anomalies in metrics"""
        anomalies = {}
        
        # Check key metrics
        for metric_name, value in [
            ('cpu', metrics.cpu_percent),
            ('memory', metrics.memory_percent),
            ('response_time', metrics.response_time_p95),
            ('error_rate', metrics.error_rate)
        ]:
            z_score = self.detector.detect_anomaly(metric_name, value)
            if z_score:
                anomalies[metric_name] = z_score
        
        return anomalies
    
    async def _broadcast_metrics(
        self,
        metrics: PerformanceMetrics,
        anomalies: Dict[str, float],
        alerts: List[Alert]
    ):
        """Broadcast metrics to WebSocket clients"""
        message = {
            'timestamp': metrics.timestamp.isoformat(),
            'metrics': metrics.__dict__,
            'anomalies': anomalies,
            'alerts': [alert.__dict__ for alert in alerts]
        }
        
        # Send to all connected clients
        disconnected = []
        for websocket in self.connections:
            try:
                await websocket.send_json(message)
            except:
                disconnected.append(websocket)
        
        # Remove disconnected clients
        for websocket in disconnected:
            self.connections.remove(websocket)
    
    def _generate_dashboard_html(self) -> str:
        """Generate dashboard HTML with real-time charts"""
        return '''
<!DOCTYPE html>
<html>
<head>
    <title>Performance Monitoring Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .metrics-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
        .metric-card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .metric-value { font-size: 2em; font-weight: bold; color: #333; }
        .metric-label { color: #666; margin-bottom: 10px; }
        .alert { padding: 10px; margin: 10px 0; border-radius: 4px; }
        .alert-warning { background: #fff3cd; border-left: 4px solid #ffc107; }
        .alert-error { background: #f8d7da; border-left: 4px solid #dc3545; }
        .alert-critical { background: #d1ecf1; border-left: 4px solid #0dcaf0; }
        .chart-container { position: relative; height: 200px; margin-top: 20px; }
    </style>
</head>
<body>
    <h1>Performance Monitoring Dashboard</h1>
    
    <div id="alerts"></div>
    
    <div class="metrics-grid">
        <div class="metric-card">
            <div class="metric-label">CPU Usage</div>
            <div class="metric-value" id="cpu">--%</div>
            <div class="chart-container">
                <canvas id="cpuChart"></canvas>
            </div>
        </div>
        
        <div class="metric-card">
            <div class="metric-label">Memory Usage</div>
            <div class="metric-value" id="memory">--%</div>
            <div class="chart-container">
                <canvas id="memoryChart"></canvas>
            </div>
        </div>
        
        <div class="metric-card">
            <div class="metric-label">Response Time (P95)</div>
            <div class="metric-value" id="responseTime">--ms</div>
            <div class="chart-container">
                <canvas id="responseChart"></canvas>
            </div>
        </div>
        
        <div class="metric-card">
            <div class="metric-label">Request Rate</div>
            <div class="metric-value" id="requestRate">--/s</div>
            <div class="chart-container">
                <canvas id="requestChart"></canvas>
            </div>
        </div>
        
        <div class="metric-card">
            <div class="metric-label">Error Rate</div>
            <div class="metric-value" id="errorRate">--%</div>
        </div>
        
        <div class="metric-card">
            <div class="metric-label">Cache Hit Rate</div>
            <div class="metric-value" id="cacheHitRate">--%</div>
        </div>
    </div>
    
    <script>
        // WebSocket connection
        const ws = new WebSocket('ws://localhost:8000/monitoring/ws');
        
        // Chart configurations
        const chartOptions = {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: { beginAtZero: true }
            },
            plugins: {
                legend: { display: false }
            }
        };
        
        // Initialize charts
        const cpuChart = new Chart(document.getElementById('cpuChart'), {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    data: [],
                    borderColor: 'rgb(75, 192, 192)',
                    tension: 0.1
                }]
            },
            options: chartOptions
        });
        
        const memoryChart = new Chart(document.getElementById('memoryChart'), {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    data: [],
                    borderColor: 'rgb(255, 99, 132)',
                    tension: 0.1
                }]
            },
            options: chartOptions
        });
        
        const responseChart = new Chart(document.getElementById('responseChart'), {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    data: [],
                    borderColor: 'rgb(54, 162, 235)',
                    tension: 0.1
                }]
            },
            options: chartOptions
        });
        
        const requestChart = new Chart(document.getElementById('requestChart'), {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    data: [],
                    borderColor: 'rgb(153, 102, 255)',
                    tension: 0.1
                }]
            },
            options: chartOptions
        });
        
        // Update metrics
        ws.onmessage = function(event) {
            const data = JSON.parse(event.data);
            const metrics = data.metrics;
            
            // Update values
            document.getElementById('cpu').textContent = metrics.cpu_percent.toFixed(1) + '%';
            document.getElementById('memory').textContent = metrics.memory_percent.toFixed(1) + '%';
            document.getElementById('responseTime').textContent = metrics.response_time_p95.toFixed(0) + 'ms';
            document.getElementById('requestRate').textContent = metrics.request_rate.toFixed(1) + '/s';
            document.getElementById('errorRate').textContent = metrics.error_rate.toFixed(1) + '%';
            document.getElementById('cacheHitRate').textContent = metrics.cache_hit_rate.toFixed(1) + '%';
            
            // Update charts
            const time = new Date(data.timestamp).toLocaleTimeString();
            
            updateChart(cpuChart, time, metrics.cpu_percent);
            updateChart(memoryChart, time, metrics.memory_percent);
            updateChart(responseChart, time, metrics.response_time_p95);
            updateChart(requestChart, time, metrics.request_rate);
            
            // Update alerts
            updateAlerts(data.alerts);
        };
        
        function updateChart(chart, label, value) {
            if (chart.data.labels.length > 60) {
                chart.data.labels.shift();
                chart.data.datasets[0].data.shift();
            }
            chart.data.labels.push(label);
            chart.data.datasets[0].data.push(value);
            chart.update('none');
        }
        
        function updateAlerts(alerts) {
            const alertsDiv = document.getElementById('alerts');
            alertsDiv.innerHTML = '';
            
            alerts.forEach(alert => {
                const alertDiv = document.createElement('div');
                alertDiv.className = `alert alert-${alert.severity}`;
                alertDiv.textContent = alert.message;
                alertsDiv.appendChild(alertDiv);
            });
        }
    </script>
</body>
</html>
        '''
    
    def get_summary_report(self) -> Dict[str, Any]:
        """Get performance summary report"""
        # Calculate statistics from histories
        cpu_history = list(self.collector.histories['cpu'])
        memory_history = list(self.collector.histories['memory'])
        
        return {
            'uptime_seconds': time.time() - self.collector.process.create_time(),
            'cpu': {
                'current': cpu_history[-1].value if cpu_history else 0,
                'avg': statistics.mean([p.value for p in cpu_history]) if cpu_history else 0,
                'max': max([p.value for p in cpu_history]) if cpu_history else 0
            },
            'memory': {
                'current': memory_history[-1].value if memory_history else 0,
                'avg': statistics.mean([p.value for p in memory_history]) if memory_history else 0,
                'max': max([p.value for p in memory_history]) if memory_history else 0
            },
            'alerts': {
                'active': len([a for a in self.alert_manager.alerts.values() if not a.resolved]),
                'total': len(self.alert_manager.alert_history)
            }
        }