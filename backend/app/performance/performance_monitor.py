"""
Comprehensive Performance Monitoring and Dashboard

Implements real-time performance monitoring with:
- System metrics collection
- Application metrics
- Database performance tracking
- Cache hit ratios
- GPU utilization
- Custom dashboards
- Alert management
"""

import asyncio
import time
import psutil
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import prometheus_client
from prometheus_client import Counter, Histogram, Gauge, Summary
import aioredis
import asyncpg
from fastapi import FastAPI, WebSocket, BackgroundTasks
from fastapi.responses import HTMLResponse
import logging

# GPU monitoring
try:
    import pynvml
    pynvml.nvmlInit()
    GPU_AVAILABLE = True
except:
    GPU_AVAILABLE = False

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of metrics"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


@dataclass
class PerformanceMetric:
    """Performance metric data point"""
    timestamp: float
    name: str
    value: float
    unit: str
    labels: Dict[str, str] = None


@dataclass
class Alert:
    """Performance alert"""
    id: str
    timestamp: float
    severity: str  # info, warning, critical
    metric: str
    condition: str
    current_value: float
    threshold: float
    message: str
    resolved: bool = False


# Prometheus metrics
REQUEST_COUNT = Counter('app_requests_total', 'Total requests', ['method', 'endpoint', 'status'])
REQUEST_LATENCY = Histogram('app_request_latency_seconds', 'Request latency', ['method', 'endpoint'])
ACTIVE_USERS = Gauge('app_active_users', 'Currently active users')
DB_CONNECTIONS = Gauge('app_db_connections', 'Database connections', ['pool'])
CACHE_HITS = Counter('app_cache_hits_total', 'Cache hits', ['cache_level'])
CACHE_MISSES = Counter('app_cache_misses_total', 'Cache misses', ['cache_level'])
GPU_UTILIZATION = Gauge('app_gpu_utilization_percent', 'GPU utilization', ['gpu_id'])
GPU_MEMORY = Gauge('app_gpu_memory_mb', 'GPU memory usage', ['gpu_id', 'type'])
SIMULATION_TIME = Summary('app_simulation_time_seconds', 'Monte Carlo simulation time')
ERROR_RATE = Counter('app_errors_total', 'Application errors', ['error_type'])


class PerformanceMonitor:
    """
    Comprehensive performance monitoring system
    """
    
    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        db_url: str = None,
        enable_gpu_monitoring: bool = True,
        collection_interval: int = 5
    ):
        self.redis_url = redis_url
        self.db_url = db_url
        self.enable_gpu_monitoring = enable_gpu_monitoring and GPU_AVAILABLE
        self.collection_interval = collection_interval
        
        self.redis_client: Optional[aioredis.Redis] = None
        self.db_pool: Optional[asyncpg.Pool] = None
        
        self.monitoring_task: Optional[asyncio.Task] = None
        self.alerts: List[Alert] = []
        self.alert_thresholds = self._default_thresholds()
        
        # Metrics storage
        self.metrics_buffer: List[PerformanceMetric] = []
        self.max_buffer_size = 10000
    
    def _default_thresholds(self) -> Dict[str, Dict[str, Any]]:
        """Default alert thresholds"""
        return {
            'cpu_usage': {'warning': 70, 'critical': 90},
            'memory_usage': {'warning': 80, 'critical': 95},
            'disk_usage': {'warning': 80, 'critical': 90},
            'response_time_p95': {'warning': 1000, 'critical': 3000},  # ms
            'error_rate': {'warning': 0.01, 'critical': 0.05},  # 1%, 5%
            'db_connections': {'warning': 80, 'critical': 95},  # percentage
            'cache_hit_ratio': {'warning': 0.7, 'critical': 0.5},  # 70%, 50%
            'gpu_utilization': {'warning': 80, 'critical': 95},
            'gpu_memory': {'warning': 80, 'critical': 95}
        }
    
    async def initialize(self):
        """Initialize monitoring system"""
        # Connect to Redis
        self.redis_client = await aioredis.create_redis_pool(
            self.redis_url,
            minsize=5,
            maxsize=10
        )
        
        # Connect to database if URL provided
        if self.db_url:
            self.db_pool = await asyncpg.create_pool(
                self.db_url,
                min_size=2,
                max_size=5
            )
        
        # Start monitoring task
        self.monitoring_task = asyncio.create_task(self._collect_metrics())
        
        logger.info("Performance monitor initialized")
    
    async def _collect_metrics(self):
        """Main metrics collection loop"""
        while True:
            try:
                # Collect all metrics
                metrics = await self._gather_all_metrics()
                
                # Store metrics
                await self._store_metrics(metrics)
                
                # Check alerts
                await self._check_alerts(metrics)
                
                # Clean old metrics
                await self._cleanup_old_metrics()
                
                await asyncio.sleep(self.collection_interval)
                
            except Exception as e:
                logger.error(f"Error collecting metrics: {e}")
                await asyncio.sleep(self.collection_interval * 2)
    
    async def _gather_all_metrics(self) -> List[PerformanceMetric]:
        """Gather all system and application metrics"""
        metrics = []
        timestamp = time.time()
        
        # System metrics
        metrics.extend(self._collect_system_metrics(timestamp))
        
        # Application metrics
        metrics.extend(await self._collect_application_metrics(timestamp))
        
        # Database metrics
        if self.db_pool:
            metrics.extend(await self._collect_database_metrics(timestamp))
        
        # Cache metrics
        metrics.extend(await self._collect_cache_metrics(timestamp))
        
        # GPU metrics
        if self.enable_gpu_monitoring:
            metrics.extend(self._collect_gpu_metrics(timestamp))
        
        return metrics
    
    def _collect_system_metrics(self, timestamp: float) -> List[PerformanceMetric]:
        """Collect system-level metrics"""
        metrics = []
        
        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=0.1)
        metrics.append(PerformanceMetric(
            timestamp=timestamp,
            name="system_cpu_usage",
            value=cpu_percent,
            unit="percent"
        ))
        
        # Per-core CPU
        for i, core_percent in enumerate(psutil.cpu_percent(percpu=True, interval=0.1)):
            metrics.append(PerformanceMetric(
                timestamp=timestamp,
                name="system_cpu_core_usage",
                value=core_percent,
                unit="percent",
                labels={"core": str(i)}
            ))
        
        # Memory metrics
        memory = psutil.virtual_memory()
        metrics.append(PerformanceMetric(
            timestamp=timestamp,
            name="system_memory_usage",
            value=memory.percent,
            unit="percent"
        ))
        metrics.append(PerformanceMetric(
            timestamp=timestamp,
            name="system_memory_available",
            value=memory.available / (1024**3),  # GB
            unit="GB"
        ))
        
        # Swap metrics
        swap = psutil.swap_memory()
        metrics.append(PerformanceMetric(
            timestamp=timestamp,
            name="system_swap_usage",
            value=swap.percent,
            unit="percent"
        ))
        
        # Disk metrics
        for partition in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                metrics.append(PerformanceMetric(
                    timestamp=timestamp,
                    name="system_disk_usage",
                    value=usage.percent,
                    unit="percent",
                    labels={"mount": partition.mountpoint}
                ))
            except:
                pass
        
        # Disk I/O
        disk_io = psutil.disk_io_counters()
        if disk_io:
            metrics.append(PerformanceMetric(
                timestamp=timestamp,
                name="system_disk_read_bytes",
                value=disk_io.read_bytes,
                unit="bytes"
            ))
            metrics.append(PerformanceMetric(
                timestamp=timestamp,
                name="system_disk_write_bytes",
                value=disk_io.write_bytes,
                unit="bytes"
            ))
        
        # Network metrics
        net_io = psutil.net_io_counters()
        metrics.append(PerformanceMetric(
            timestamp=timestamp,
            name="system_network_bytes_sent",
            value=net_io.bytes_sent,
            unit="bytes"
        ))
        metrics.append(PerformanceMetric(
            timestamp=timestamp,
            name="system_network_bytes_recv",
            value=net_io.bytes_recv,
            unit="bytes"
        ))
        
        # Process metrics
        process = psutil.Process()
        metrics.append(PerformanceMetric(
            timestamp=timestamp,
            name="app_process_cpu_percent",
            value=process.cpu_percent(),
            unit="percent"
        ))
        metrics.append(PerformanceMetric(
            timestamp=timestamp,
            name="app_process_memory_mb",
            value=process.memory_info().rss / (1024**2),
            unit="MB"
        ))
        metrics.append(PerformanceMetric(
            timestamp=timestamp,
            name="app_process_threads",
            value=process.num_threads(),
            unit="count"
        ))
        
        return metrics
    
    async def _collect_application_metrics(self, timestamp: float) -> List[PerformanceMetric]:
        """Collect application-specific metrics"""
        metrics = []
        
        # Get metrics from Redis if available
        if self.redis_client:
            # Response times
            response_times = await self.redis_client.lrange('metrics:response_times', 0, -1)
            if response_times:
                times = [float(t) for t in response_times]
                
                # Calculate percentiles
                import numpy as np
                percentiles = np.percentile(times, [50, 75, 90, 95, 99])
                
                for i, p in enumerate([50, 75, 90, 95, 99]):
                    metrics.append(PerformanceMetric(
                        timestamp=timestamp,
                        name=f"app_response_time_p{p}",
                        value=percentiles[i],
                        unit="ms"
                    ))
            
            # Active users
            active_users = await self.redis_client.scard('active_users')
            metrics.append(PerformanceMetric(
                timestamp=timestamp,
                name="app_active_users",
                value=active_users or 0,
                unit="count"
            ))
            
            # Request rate
            request_count = await self.redis_client.get('metrics:request_count')
            if request_count:
                metrics.append(PerformanceMetric(
                    timestamp=timestamp,
                    name="app_request_rate",
                    value=float(request_count),
                    unit="requests/sec"
                ))
            
            # Error rate
            error_count = await self.redis_client.get('metrics:error_count')
            if error_count and request_count:
                error_rate = float(error_count) / float(request_count)
                metrics.append(PerformanceMetric(
                    timestamp=timestamp,
                    name="app_error_rate",
                    value=error_rate,
                    unit="ratio"
                ))
        
        # Update Prometheus metrics
        ACTIVE_USERS.set(active_users or 0)
        
        return metrics
    
    async def _collect_database_metrics(self, timestamp: float) -> List[PerformanceMetric]:
        """Collect database performance metrics"""
        metrics = []
        
        if not self.db_pool:
            return metrics
        
        try:
            async with self.db_pool.acquire() as conn:
                # Connection pool stats
                pool_size = self.db_pool.get_size()
                pool_free = self.db_pool.get_idle_size()
                pool_used = pool_size - pool_free
                
                metrics.append(PerformanceMetric(
                    timestamp=timestamp,
                    name="db_pool_connections_used",
                    value=pool_used,
                    unit="count"
                ))
                
                metrics.append(PerformanceMetric(
                    timestamp=timestamp,
                    name="db_pool_utilization",
                    value=(pool_used / pool_size * 100) if pool_size > 0 else 0,
                    unit="percent"
                ))
                
                # Database statistics
                stats = await conn.fetch("""
                    SELECT 
                        numbackends as connections,
                        xact_commit as commits,
                        xact_rollback as rollbacks,
                        blks_hit as cache_hits,
                        blks_read as disk_reads,
                        tup_returned as rows_returned,
                        tup_fetched as rows_fetched,
                        tup_inserted as rows_inserted,
                        tup_updated as rows_updated,
                        tup_deleted as rows_deleted
                    FROM pg_stat_database
                    WHERE datname = current_database()
                """)
                
                if stats:
                    stat = stats[0]
                    
                    metrics.append(PerformanceMetric(
                        timestamp=timestamp,
                        name="db_active_connections",
                        value=stat['connections'],
                        unit="count"
                    ))
                    
                    # Cache hit ratio
                    cache_hits = stat['cache_hits']
                    disk_reads = stat['disk_reads']
                    if cache_hits + disk_reads > 0:
                        cache_hit_ratio = cache_hits / (cache_hits + disk_reads)
                        metrics.append(PerformanceMetric(
                            timestamp=timestamp,
                            name="db_cache_hit_ratio",
                            value=cache_hit_ratio,
                            unit="ratio"
                        ))
                
                # Long running queries
                long_queries = await conn.fetch("""
                    SELECT COUNT(*) as count
                    FROM pg_stat_activity
                    WHERE state = 'active'
                        AND now() - query_start > interval '5 seconds'
                """)
                
                if long_queries:
                    metrics.append(PerformanceMetric(
                        timestamp=timestamp,
                        name="db_long_running_queries",
                        value=long_queries[0]['count'],
                        unit="count"
                    ))
                
                # Update Prometheus metrics
                DB_CONNECTIONS.labels(pool='main').set(pool_used)
                
        except Exception as e:
            logger.error(f"Error collecting database metrics: {e}")
        
        return metrics
    
    async def _collect_cache_metrics(self, timestamp: float) -> List[PerformanceMetric]:
        """Collect cache performance metrics"""
        metrics = []
        
        if not self.redis_client:
            return metrics
        
        try:
            # Redis INFO command
            info = await self.redis_client.info()
            
            # Memory usage
            used_memory = info.get('used_memory', 0) / (1024**2)  # MB
            metrics.append(PerformanceMetric(
                timestamp=timestamp,
                name="cache_memory_used",
                value=used_memory,
                unit="MB"
            ))
            
            # Hit/miss ratio
            keyspace_hits = info.get('keyspace_hits', 0)
            keyspace_misses = info.get('keyspace_misses', 0)
            
            if keyspace_hits + keyspace_misses > 0:
                hit_ratio = keyspace_hits / (keyspace_hits + keyspace_misses)
                metrics.append(PerformanceMetric(
                    timestamp=timestamp,
                    name="cache_hit_ratio",
                    value=hit_ratio,
                    unit="ratio"
                ))
            
            # Connected clients
            connected_clients = info.get('connected_clients', 0)
            metrics.append(PerformanceMetric(
                timestamp=timestamp,
                name="cache_connected_clients",
                value=connected_clients,
                unit="count"
            ))
            
            # Operations per second
            ops_per_sec = info.get('instantaneous_ops_per_sec', 0)
            metrics.append(PerformanceMetric(
                timestamp=timestamp,
                name="cache_ops_per_second",
                value=ops_per_sec,
                unit="ops/sec"
            ))
            
        except Exception as e:
            logger.error(f"Error collecting cache metrics: {e}")
        
        return metrics
    
    def _collect_gpu_metrics(self, timestamp: float) -> List[PerformanceMetric]:
        """Collect GPU metrics using pynvml"""
        metrics = []
        
        if not GPU_AVAILABLE:
            return metrics
        
        try:
            device_count = pynvml.nvmlDeviceGetCount()
            
            for i in range(device_count):
                handle = pynvml.nvmlDeviceGetHandleByIndex(i)
                
                # GPU utilization
                util = pynvml.nvmlDeviceGetUtilizationRates(handle)
                metrics.append(PerformanceMetric(
                    timestamp=timestamp,
                    name="gpu_utilization",
                    value=util.gpu,
                    unit="percent",
                    labels={"gpu_id": str(i)}
                ))
                
                # Memory utilization
                metrics.append(PerformanceMetric(
                    timestamp=timestamp,
                    name="gpu_memory_utilization",
                    value=util.memory,
                    unit="percent",
                    labels={"gpu_id": str(i)}
                ))
                
                # Memory info
                mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                metrics.append(PerformanceMetric(
                    timestamp=timestamp,
                    name="gpu_memory_used",
                    value=mem_info.used / (1024**2),  # MB
                    unit="MB",
                    labels={"gpu_id": str(i)}
                ))
                
                metrics.append(PerformanceMetric(
                    timestamp=timestamp,
                    name="gpu_memory_free",
                    value=mem_info.free / (1024**2),  # MB
                    unit="MB",
                    labels={"gpu_id": str(i)}
                ))
                
                # Temperature
                temp = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
                metrics.append(PerformanceMetric(
                    timestamp=timestamp,
                    name="gpu_temperature",
                    value=temp,
                    unit="celsius",
                    labels={"gpu_id": str(i)}
                ))
                
                # Power usage
                power = pynvml.nvmlDeviceGetPowerUsage(handle) / 1000  # Watts
                metrics.append(PerformanceMetric(
                    timestamp=timestamp,
                    name="gpu_power_usage",
                    value=power,
                    unit="watts",
                    labels={"gpu_id": str(i)}
                ))
                
                # Update Prometheus metrics
                GPU_UTILIZATION.labels(gpu_id=str(i)).set(util.gpu)
                GPU_MEMORY.labels(gpu_id=str(i), type='used').set(mem_info.used / (1024**2))
                
        except Exception as e:
            logger.error(f"Error collecting GPU metrics: {e}")
        
        return metrics
    
    async def _store_metrics(self, metrics: List[PerformanceMetric]):
        """Store metrics in Redis with time-series structure"""
        if not self.redis_client:
            return
        
        pipe = self.redis_client.pipeline()
        
        for metric in metrics:
            # Store in sorted set for time-series queries
            key = f"metrics:{metric.name}"
            if metric.labels:
                label_str = ",".join(f"{k}={v}" for k, v in metric.labels.items())
                key = f"{key}:{label_str}"
            
            # Store with timestamp as score
            pipe.zadd(key, metric.timestamp, json.dumps({
                'value': metric.value,
                'unit': metric.unit
            }))
            
            # Expire old data (keep 24 hours)
            pipe.zremrangebyscore(key, 0, time.time() - 86400)
            
            # Also store in buffer for batch processing
            self.metrics_buffer.append(metric)
        
        await pipe.execute()
        
        # Flush buffer if it's full
        if len(self.metrics_buffer) >= self.max_buffer_size:
            await self._flush_metrics_buffer()
    
    async def _flush_metrics_buffer(self):
        """Flush metrics buffer to persistent storage"""
        if not self.metrics_buffer:
            return
        
        # Store in database if available
        if self.db_pool:
            try:
                async with self.db_pool.acquire() as conn:
                    await conn.executemany("""
                        INSERT INTO performance_metrics 
                        (timestamp, name, value, unit, labels)
                        VALUES ($1, $2, $3, $4, $5)
                    """, [
                        (
                            datetime.fromtimestamp(m.timestamp),
                            m.name,
                            m.value,
                            m.unit,
                            json.dumps(m.labels) if m.labels else None
                        )
                        for m in self.metrics_buffer
                    ])
            except Exception as e:
                logger.error(f"Error flushing metrics to database: {e}")
        
        self.metrics_buffer.clear()
    
    async def _check_alerts(self, metrics: List[PerformanceMetric]):
        """Check metrics against alert thresholds"""
        current_alerts = {}
        
        for metric in metrics:
            # Check if this metric has thresholds
            threshold_config = None
            
            # Map metric names to threshold keys
            if 'cpu_usage' in metric.name:
                threshold_config = self.alert_thresholds.get('cpu_usage')
                threshold_key = 'cpu_usage'
            elif 'memory_usage' in metric.name:
                threshold_config = self.alert_thresholds.get('memory_usage')
                threshold_key = 'memory_usage'
            elif 'response_time_p95' in metric.name:
                threshold_config = self.alert_thresholds.get('response_time_p95')
                threshold_key = 'response_time_p95'
            elif 'error_rate' in metric.name:
                threshold_config = self.alert_thresholds.get('error_rate')
                threshold_key = 'error_rate'
            elif 'cache_hit_ratio' in metric.name:
                threshold_config = self.alert_thresholds.get('cache_hit_ratio')
                threshold_key = 'cache_hit_ratio'
            
            if threshold_config:
                # Check critical threshold
                if 'critical' in threshold_config:
                    critical = threshold_config['critical']
                    # For cache hit ratio, lower is worse
                    if 'cache_hit' in metric.name:
                        condition_met = metric.value < critical
                    else:
                        condition_met = metric.value > critical
                    
                    if condition_met:
                        alert_id = f"{metric.name}_critical"
                        current_alerts[alert_id] = Alert(
                            id=alert_id,
                            timestamp=metric.timestamp,
                            severity='critical',
                            metric=metric.name,
                            condition=f"{'<' if 'cache_hit' in metric.name else '>'} {critical}",
                            current_value=metric.value,
                            threshold=critical,
                            message=f"Critical: {metric.name} is {metric.value:.2f} (threshold: {critical})"
                        )
                        continue
                
                # Check warning threshold
                if 'warning' in threshold_config:
                    warning = threshold_config['warning']
                    if 'cache_hit' in metric.name:
                        condition_met = metric.value < warning
                    else:
                        condition_met = metric.value > warning
                    
                    if condition_met:
                        alert_id = f"{metric.name}_warning"
                        current_alerts[alert_id] = Alert(
                            id=alert_id,
                            timestamp=metric.timestamp,
                            severity='warning',
                            metric=metric.name,
                            condition=f"{'<' if 'cache_hit' in metric.name else '>'} {warning}",
                            current_value=metric.value,
                            threshold=warning,
                            message=f"Warning: {metric.name} is {metric.value:.2f} (threshold: {warning})"
                        )
        
        # Update alerts list
        for alert in current_alerts.values():
            # Check if alert already exists
            existing = next((a for a in self.alerts if a.id == alert.id), None)
            if not existing:
                self.alerts.append(alert)
                await self._send_alert(alert)
        
        # Mark resolved alerts
        for alert in self.alerts:
            if not alert.resolved and alert.id not in current_alerts:
                alert.resolved = True
                await self._send_alert_resolved(alert)
    
    async def _send_alert(self, alert: Alert):
        """Send alert notification"""
        logger.warning(f"ALERT: {alert.message}")
        
        # Store alert in Redis
        if self.redis_client:
            await self.redis_client.lpush(
                'alerts:active',
                json.dumps(asdict(alert))
            )
            await self.redis_client.ltrim('alerts:active', 0, 99)  # Keep last 100
    
    async def _send_alert_resolved(self, alert: Alert):
        """Send alert resolved notification"""
        logger.info(f"Alert resolved: {alert.id}")
        
        # Update in Redis
        if self.redis_client:
            await self.redis_client.lpush(
                'alerts:resolved',
                json.dumps(asdict(alert))
            )
    
    async def _cleanup_old_metrics(self):
        """Clean up old metrics data"""
        if self.redis_client:
            # Get all metric keys
            keys = await self.redis_client.keys('metrics:*')
            
            # Remove data older than 24 hours
            cutoff_time = time.time() - 86400
            
            pipe = self.redis_client.pipeline()
            for key in keys:
                pipe.zremrangebyscore(key, 0, cutoff_time)
            
            await pipe.execute()
    
    async def get_metrics_summary(self) -> Dict[str, Any]:
        """Get current metrics summary"""
        summary = {
            'timestamp': time.time(),
            'system': {},
            'application': {},
            'database': {},
            'cache': {},
            'gpu': {},
            'alerts': []
        }
        
        # Get latest metrics from Redis
        if self.redis_client:
            # System metrics
            for metric_name in ['system_cpu_usage', 'system_memory_usage', 'system_disk_usage']:
                key = f"metrics:{metric_name}"
                data = await self.redis_client.zrange(key, -1, -1, withscores=True)
                if data:
                    value = json.loads(data[0][0])['value']
                    summary['system'][metric_name] = value
            
            # Application metrics
            for metric_name in ['app_response_time_p95', 'app_active_users', 'app_error_rate']:
                key = f"metrics:{metric_name}"
                data = await self.redis_client.zrange(key, -1, -1, withscores=True)
                if data:
                    value = json.loads(data[0][0])['value']
                    summary['application'][metric_name] = value
        
        # Active alerts
        summary['alerts'] = [
            asdict(alert) for alert in self.alerts
            if not alert.resolved
        ]
        
        return summary
    
    async def get_metrics_history(
        self,
        metric_name: str,
        start_time: float = None,
        end_time: float = None,
        labels: Dict[str, str] = None
    ) -> List[Tuple[float, float]]:
        """
        Get historical metrics data
        
        Args:
            metric_name: Name of the metric
            start_time: Start timestamp (default: 1 hour ago)
            end_time: End timestamp (default: now)
            labels: Optional label filters
            
        Returns:
            List of (timestamp, value) tuples
        """
        if not self.redis_client:
            return []
        
        # Default time range
        if end_time is None:
            end_time = time.time()
        if start_time is None:
            start_time = end_time - 3600  # Last hour
        
        # Build key
        key = f"metrics:{metric_name}"
        if labels:
            label_str = ",".join(f"{k}={v}" for k, v in labels.items())
            key = f"{key}:{label_str}"
        
        # Get data from Redis
        data = await self.redis_client.zrangebyscore(
            key,
            start_time,
            end_time,
            withscores=True
        )
        
        result = []
        for value_json, timestamp in data:
            value = json.loads(value_json)['value']
            result.append((timestamp, value))
        
        return result
    
    async def close(self):
        """Clean up resources"""
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        
        # Flush remaining metrics
        await self._flush_metrics_buffer()
        
        if self.redis_client:
            self.redis_client.close()
            await self.redis_client.wait_closed()
        
        if self.db_pool:
            await self.db_pool.close()
        
        logger.info("Performance monitor closed")


def create_monitoring_dashboard() -> str:
    """Generate HTML dashboard for monitoring"""
    return """
<!DOCTYPE html>
<html>
<head>
    <title>Performance Monitoring Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
        }
        .dashboard {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 20px;
        }
        .metric-card {
            background: white;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .metric-title {
            font-size: 14px;
            color: #666;
            margin-bottom: 10px;
        }
        .metric-value {
            font-size: 32px;
            font-weight: bold;
            color: #333;
        }
        .metric-unit {
            font-size: 18px;
            color: #999;
            margin-left: 5px;
        }
        .chart-container {
            position: relative;
            height: 200px;
            margin-top: 20px;
        }
        .alert {
            padding: 10px;
            border-radius: 4px;
            margin-bottom: 10px;
        }
        .alert-warning {
            background: #fff3cd;
            border: 1px solid #ffc107;
        }
        .alert-critical {
            background: #f8d7da;
            border: 1px solid #dc3545;
        }
    </style>
</head>
<body>
    <h1>Performance Monitoring Dashboard</h1>
    
    <div class="dashboard">
        <div class="metric-card">
            <div class="metric-title">CPU Usage</div>
            <div class="metric-value" id="cpu-usage">--</div>
            <div class="metric-unit">%</div>
            <div class="chart-container">
                <canvas id="cpu-chart"></canvas>
            </div>
        </div>
        
        <div class="metric-card">
            <div class="metric-title">Memory Usage</div>
            <div class="metric-value" id="memory-usage">--</div>
            <div class="metric-unit">%</div>
            <div class="chart-container">
                <canvas id="memory-chart"></canvas>
            </div>
        </div>
        
        <div class="metric-card">
            <div class="metric-title">Response Time (P95)</div>
            <div class="metric-value" id="response-time">--</div>
            <div class="metric-unit">ms</div>
            <div class="chart-container">
                <canvas id="response-chart"></canvas>
            </div>
        </div>
        
        <div class="metric-card">
            <div class="metric-title">Active Users</div>
            <div class="metric-value" id="active-users">--</div>
            <div class="metric-unit">users</div>
            <div class="chart-container">
                <canvas id="users-chart"></canvas>
            </div>
        </div>
        
        <div class="metric-card">
            <div class="metric-title">Cache Hit Ratio</div>
            <div class="metric-value" id="cache-hit-ratio">--</div>
            <div class="metric-unit">%</div>
            <div class="chart-container">
                <canvas id="cache-chart"></canvas>
            </div>
        </div>
        
        <div class="metric-card">
            <div class="metric-title">Error Rate</div>
            <div class="metric-value" id="error-rate">--</div>
            <div class="metric-unit">%</div>
            <div class="chart-container">
                <canvas id="error-chart"></canvas>
            </div>
        </div>
        
        <div class="metric-card" style="grid-column: span 2;">
            <div class="metric-title">Active Alerts</div>
            <div id="alerts-container"></div>
        </div>
    </div>
    
    <script>
        // Initialize charts
        const charts = {};
        const chartData = {};
        
        function createChart(elementId, label, color) {
            const ctx = document.getElementById(elementId).getContext('2d');
            const data = {
                labels: [],
                datasets: [{
                    label: label,
                    data: [],
                    borderColor: color,
                    backgroundColor: color + '20',
                    tension: 0.4,
                    fill: true
                }]
            };
            
            chartData[elementId] = data;
            
            charts[elementId] = new Chart(ctx, {
                type: 'line',
                data: data,
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: false
                        }
                    },
                    scales: {
                        x: {
                            display: false
                        },
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
        }
        
        // Create all charts
        createChart('cpu-chart', 'CPU Usage', '#007bff');
        createChart('memory-chart', 'Memory Usage', '#28a745');
        createChart('response-chart', 'Response Time', '#ffc107');
        createChart('users-chart', 'Active Users', '#17a2b8');
        createChart('cache-chart', 'Cache Hit Ratio', '#6610f2');
        createChart('error-chart', 'Error Rate', '#dc3545');
        
        // WebSocket connection for real-time updates
        const ws = new WebSocket('ws://localhost:8000/ws/metrics');
        
        ws.onmessage = function(event) {
            const data = JSON.parse(event.data);
            
            // Update values
            document.getElementById('cpu-usage').textContent = 
                data.system.system_cpu_usage?.toFixed(1) || '--';
            document.getElementById('memory-usage').textContent = 
                data.system.system_memory_usage?.toFixed(1) || '--';
            document.getElementById('response-time').textContent = 
                data.application.app_response_time_p95?.toFixed(0) || '--';
            document.getElementById('active-users').textContent = 
                data.application.app_active_users || '--';
            document.getElementById('cache-hit-ratio').textContent = 
                ((data.cache.cache_hit_ratio || 0) * 100).toFixed(1);
            document.getElementById('error-rate').textContent = 
                ((data.application.app_error_rate || 0) * 100).toFixed(2);
            
            // Update charts
            const timestamp = new Date().toLocaleTimeString();
            
            function updateChart(chartId, value) {
                const data = chartData[chartId];
                data.labels.push(timestamp);
                data.datasets[0].data.push(value);
                
                // Keep only last 20 points
                if (data.labels.length > 20) {
                    data.labels.shift();
                    data.datasets[0].data.shift();
                }
                
                charts[chartId].update('none');
            }
            
            updateChart('cpu-chart', data.system.system_cpu_usage || 0);
            updateChart('memory-chart', data.system.system_memory_usage || 0);
            updateChart('response-chart', data.application.app_response_time_p95 || 0);
            updateChart('users-chart', data.application.app_active_users || 0);
            updateChart('cache-chart', (data.cache.cache_hit_ratio || 0) * 100);
            updateChart('error-chart', (data.application.app_error_rate || 0) * 100);
            
            // Update alerts
            const alertsContainer = document.getElementById('alerts-container');
            alertsContainer.innerHTML = '';
            
            if (data.alerts && data.alerts.length > 0) {
                data.alerts.forEach(alert => {
                    const alertDiv = document.createElement('div');
                    alertDiv.className = `alert alert-${alert.severity}`;
                    alertDiv.textContent = alert.message;
                    alertsContainer.appendChild(alertDiv);
                });
            } else {
                alertsContainer.innerHTML = '<div style="color: #28a745;">No active alerts</div>';
            }
        };
        
        ws.onerror = function(error) {
            console.error('WebSocket error:', error);
        };
        
        ws.onclose = function() {
            console.log('WebSocket connection closed');
            setTimeout(() => location.reload(), 5000);
        };
    </script>
</body>
</html>
"""