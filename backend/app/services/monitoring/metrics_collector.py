"""
Metrics Collector for Monitoring Dashboard
Collects and aggregates system metrics for Prometheus/Grafana
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from collections import defaultdict, deque
import psutil
from prometheus_client import Counter, Gauge, Histogram, Summary, CollectorRegistry, generate_latest

from app.core.config import Config
from app.services.base.logging_service import LoggingService
from app.models.portfolio import Portfolio
from app.services.market_data.aggregator import MarketDataAggregator

logger = LoggingService(__name__)


@dataclass
class MetricPoint:
    """Single metric data point"""
    name: str
    value: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    labels: Dict[str, str] = field(default_factory=dict)


@dataclass
class PerformanceMetrics:
    """System performance metrics"""
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_io: Dict[str, float]
    database_connections: int
    api_latency: float
    cache_hit_rate: float
    request_rate: float
    error_rate: float
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class PortfolioMetrics:
    """Portfolio-related metrics"""
    total_aum: float  # Assets Under Management
    active_users: int
    portfolios_monitored: int
    average_portfolio_value: float
    total_positions: int
    rebalancing_opportunities: int
    tax_harvest_opportunities: int
    risk_breaches: int
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class MarketMetrics:
    """Market data metrics"""
    data_points_processed: int
    websocket_connections: int
    market_data_latency: float
    quote_requests: int
    data_provider_health: Dict[str, str]
    cache_size: int
    timestamp: datetime = field(default_factory=datetime.utcnow)


class MetricsCollector:
    """Main metrics collector for monitoring dashboard"""
    
    def __init__(self):
        self.registry = CollectorRegistry()
        self._setup_prometheus_metrics()
        self.performance_history = deque(maxlen=1000)
        self.portfolio_history = deque(maxlen=1000)
        self.market_history = deque(maxlen=1000)
        self.alert_metrics = defaultdict(int)
        self.market_data = MarketDataAggregator()
        self.collection_interval = 10  # seconds
        self.running = False
        logger.info("Metrics Collector initialized")
    
    def _setup_prometheus_metrics(self):
        """Setup Prometheus metrics"""
        # System metrics
        self.cpu_gauge = Gauge('system_cpu_usage', 'CPU usage percentage', registry=self.registry)
        self.memory_gauge = Gauge('system_memory_usage', 'Memory usage percentage', registry=self.registry)
        self.disk_gauge = Gauge('system_disk_usage', 'Disk usage percentage', registry=self.registry)
        
        # API metrics
        self.api_requests_counter = Counter(
            'api_requests_total',
            'Total API requests',
            ['method', 'endpoint', 'status'],
            registry=self.registry
        )
        self.api_latency_histogram = Histogram(
            'api_request_duration_seconds',
            'API request latency',
            ['method', 'endpoint'],
            registry=self.registry
        )
        self.api_errors_counter = Counter(
            'api_errors_total',
            'Total API errors',
            ['method', 'endpoint', 'error_type'],
            registry=self.registry
        )
        
        # Portfolio metrics
        self.aum_gauge = Gauge('portfolio_aum_usd', 'Total assets under management', registry=self.registry)
        self.active_users_gauge = Gauge('active_users_total', 'Total active users', registry=self.registry)
        self.portfolios_gauge = Gauge('portfolios_total', 'Total portfolios', registry=self.registry)
        self.positions_gauge = Gauge('positions_total', 'Total positions across all portfolios', registry=self.registry)
        
        # Alert metrics
        self.alerts_counter = Counter(
            'alerts_generated_total',
            'Total alerts generated',
            ['type', 'priority'],
            registry=self.registry
        )
        self.alert_delivery_counter = Counter(
            'alert_deliveries_total',
            'Total alert deliveries',
            ['channel', 'status'],
            registry=self.registry
        )
        
        # Market data metrics
        self.market_data_points = Counter(
            'market_data_points_total',
            'Total market data points processed',
            ['source', 'data_type'],
            registry=self.registry
        )
        self.websocket_connections_gauge = Gauge(
            'websocket_connections_active',
            'Active WebSocket connections',
            registry=self.registry
        )
        self.market_data_latency = Summary(
            'market_data_latency_milliseconds',
            'Market data latency',
            ['source'],
            registry=self.registry
        )
        
        # Cache metrics
        self.cache_hits = Counter('cache_hits_total', 'Total cache hits', ['cache_type'], registry=self.registry)
        self.cache_misses = Counter('cache_misses_total', 'Total cache misses', ['cache_type'], registry=self.registry)
        self.cache_size_gauge = Gauge('cache_size_bytes', 'Cache size in bytes', ['cache_type'], registry=self.registry)
        
        # Database metrics
        self.db_connections_gauge = Gauge('database_connections_active', 'Active database connections', registry=self.registry)
        self.db_query_duration = Histogram(
            'database_query_duration_seconds',
            'Database query duration',
            ['query_type'],
            registry=self.registry
        )
    
    async def start_collection(self):
        """Start metrics collection"""
        self.running = True
        asyncio.create_task(self._collect_system_metrics())
        asyncio.create_task(self._collect_portfolio_metrics())
        asyncio.create_task(self._collect_market_metrics())
        asyncio.create_task(self._calculate_derived_metrics())
        logger.info("Metrics collection started")
    
    async def stop_collection(self):
        """Stop metrics collection"""
        self.running = False
        logger.info("Metrics collection stopped")
    
    async def _collect_system_metrics(self):
        """Collect system performance metrics"""
        while self.running:
            try:
                metrics = PerformanceMetrics(
                    cpu_usage=psutil.cpu_percent(interval=1),
                    memory_usage=psutil.virtual_memory().percent,
                    disk_usage=psutil.disk_usage('/').percent,
                    network_io=self._get_network_io(),
                    database_connections=await self._get_db_connections(),
                    api_latency=await self._get_api_latency(),
                    cache_hit_rate=await self._get_cache_hit_rate(),
                    request_rate=await self._get_request_rate(),
                    error_rate=await self._get_error_rate()
                )
                
                # Update Prometheus metrics
                self.cpu_gauge.set(metrics.cpu_usage)
                self.memory_gauge.set(metrics.memory_usage)
                self.disk_gauge.set(metrics.disk_usage)
                
                # Store in history
                self.performance_history.append(metrics)
                
                await asyncio.sleep(self.collection_interval)
                
            except Exception as e:
                logger.error(f"Error collecting system metrics: {e}")
                await asyncio.sleep(self.collection_interval)
    
    async def _collect_portfolio_metrics(self):
        """Collect portfolio-related metrics"""
        while self.running:
            try:
                metrics = await self._get_portfolio_metrics()
                
                # Update Prometheus metrics
                self.aum_gauge.set(metrics.total_aum)
                self.active_users_gauge.set(metrics.active_users)
                self.portfolios_gauge.set(metrics.portfolios_monitored)
                self.positions_gauge.set(metrics.total_positions)
                
                # Store in history
                self.portfolio_history.append(metrics)
                
                await asyncio.sleep(self.collection_interval * 6)  # Less frequent
                
            except Exception as e:
                logger.error(f"Error collecting portfolio metrics: {e}")
                await asyncio.sleep(self.collection_interval * 6)
    
    async def _collect_market_metrics(self):
        """Collect market data metrics"""
        while self.running:
            try:
                metrics = await self._get_market_metrics()
                
                # Update Prometheus metrics
                self.websocket_connections_gauge.set(metrics.websocket_connections)
                
                # Store in history
                self.market_history.append(metrics)
                
                await asyncio.sleep(self.collection_interval)
                
            except Exception as e:
                logger.error(f"Error collecting market metrics: {e}")
                await asyncio.sleep(self.collection_interval)
    
    async def _calculate_derived_metrics(self):
        """Calculate derived metrics and KPIs"""
        while self.running:
            try:
                await self._calculate_kpis()
                await asyncio.sleep(60)  # Every minute
            except Exception as e:
                logger.error(f"Error calculating derived metrics: {e}")
                await asyncio.sleep(60)
    
    def _get_network_io(self) -> Dict[str, float]:
        """Get network I/O stats"""
        net_io = psutil.net_io_counters()
        return {
            'bytes_sent': net_io.bytes_sent,
            'bytes_recv': net_io.bytes_recv,
            'packets_sent': net_io.packets_sent,
            'packets_recv': net_io.packets_recv
        }
    
    async def _get_db_connections(self) -> int:
        """Get active database connections"""
        # Implementation would query actual database
        return 10  # Placeholder
    
    async def _get_api_latency(self) -> float:
        """Get average API latency"""
        # Implementation would calculate from actual requests
        return 0.125  # Placeholder (125ms)
    
    async def _get_cache_hit_rate(self) -> float:
        """Get cache hit rate"""
        # Implementation would calculate from cache stats
        return 0.85  # Placeholder (85%)
    
    async def _get_request_rate(self) -> float:
        """Get request rate (requests/second)"""
        # Implementation would calculate from actual requests
        return 150.0  # Placeholder
    
    async def _get_error_rate(self) -> float:
        """Get error rate (errors/second)"""
        # Implementation would calculate from actual errors
        return 0.5  # Placeholder
    
    async def _get_portfolio_metrics(self) -> PortfolioMetrics:
        """Get portfolio-related metrics"""
        # Implementation would query actual data
        return PortfolioMetrics(
            total_aum=50000000,  # $50M
            active_users=1250,
            portfolios_monitored=1500,
            average_portfolio_value=33333,
            total_positions=7500,
            rebalancing_opportunities=125,
            tax_harvest_opportunities=45,
            risk_breaches=3
        )
    
    async def _get_market_metrics(self) -> MarketMetrics:
        """Get market data metrics"""
        # Implementation would query actual data
        return MarketMetrics(
            data_points_processed=1000000,
            websocket_connections=250,
            market_data_latency=15.5,  # ms
            quote_requests=5000,
            data_provider_health={
                'polygon': 'healthy',
                'alpaca': 'healthy',
                'yfinance': 'degraded'
            },
            cache_size=2048000  # 2MB
        )
    
    async def _calculate_kpis(self):
        """Calculate key performance indicators"""
        if len(self.performance_history) < 2:
            return
        
        # Calculate trends
        recent_metrics = list(self.performance_history)[-10:]
        
        # CPU trend
        cpu_trend = self._calculate_trend([m.cpu_usage for m in recent_metrics])
        
        # Memory trend
        memory_trend = self._calculate_trend([m.memory_usage for m in recent_metrics])
        
        # Request rate trend
        request_trend = self._calculate_trend([m.request_rate for m in recent_metrics])
        
        # Log significant changes
        if abs(cpu_trend) > 20:
            logger.warning(f"Significant CPU usage trend: {cpu_trend:+.1f}%")
        
        if abs(memory_trend) > 10:
            logger.warning(f"Significant memory usage trend: {memory_trend:+.1f}%")
    
    def _calculate_trend(self, values: List[float]) -> float:
        """Calculate trend percentage"""
        if len(values) < 2:
            return 0.0
        
        start_avg = sum(values[:len(values)//2]) / (len(values)//2)
        end_avg = sum(values[len(values)//2:]) / (len(values) - len(values)//2)
        
        if start_avg == 0:
            return 0.0
        
        return ((end_avg - start_avg) / start_avg) * 100
    
    def record_api_request(self, method: str, endpoint: str, status: int, duration: float):
        """Record API request metrics"""
        self.api_requests_counter.labels(method=method, endpoint=endpoint, status=str(status)).inc()
        self.api_latency_histogram.labels(method=method, endpoint=endpoint).observe(duration)
        
        if status >= 400:
            error_type = 'client_error' if status < 500 else 'server_error'
            self.api_errors_counter.labels(method=method, endpoint=endpoint, error_type=error_type).inc()
    
    def record_alert(self, alert_type: str, priority: str):
        """Record alert generation"""
        self.alerts_counter.labels(type=alert_type, priority=priority).inc()
        self.alert_metrics[f"{alert_type}_{priority}"] += 1
    
    def record_alert_delivery(self, channel: str, success: bool):
        """Record alert delivery"""
        status = 'success' if success else 'failed'
        self.alert_delivery_counter.labels(channel=channel, status=status).inc()
    
    def record_market_data(self, source: str, data_type: str, count: int = 1):
        """Record market data processing"""
        self.market_data_points.labels(source=source, data_type=data_type).inc(count)
    
    def record_cache_access(self, cache_type: str, hit: bool):
        """Record cache access"""
        if hit:
            self.cache_hits.labels(cache_type=cache_type).inc()
        else:
            self.cache_misses.labels(cache_type=cache_type).inc()
    
    def record_db_query(self, query_type: str, duration: float):
        """Record database query"""
        self.db_query_duration.labels(query_type=query_type).observe(duration)
    
    def get_prometheus_metrics(self) -> bytes:
        """Get metrics in Prometheus format"""
        return generate_latest(self.registry)
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get data for monitoring dashboard"""
        # Get latest metrics
        latest_performance = self.performance_history[-1] if self.performance_history else None
        latest_portfolio = self.portfolio_history[-1] if self.portfolio_history else None
        latest_market = self.market_history[-1] if self.market_history else None
        
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'system': {
                'cpu_usage': latest_performance.cpu_usage if latest_performance else 0,
                'memory_usage': latest_performance.memory_usage if latest_performance else 0,
                'disk_usage': latest_performance.disk_usage if latest_performance else 0,
                'api_latency': latest_performance.api_latency if latest_performance else 0,
                'request_rate': latest_performance.request_rate if latest_performance else 0,
                'error_rate': latest_performance.error_rate if latest_performance else 0,
                'cache_hit_rate': latest_performance.cache_hit_rate if latest_performance else 0
            },
            'portfolio': {
                'total_aum': latest_portfolio.total_aum if latest_portfolio else 0,
                'active_users': latest_portfolio.active_users if latest_portfolio else 0,
                'portfolios': latest_portfolio.portfolios_monitored if latest_portfolio else 0,
                'positions': latest_portfolio.total_positions if latest_portfolio else 0,
                'rebalancing_opportunities': latest_portfolio.rebalancing_opportunities if latest_portfolio else 0,
                'tax_harvest_opportunities': latest_portfolio.tax_harvest_opportunities if latest_portfolio else 0,
                'risk_breaches': latest_portfolio.risk_breaches if latest_portfolio else 0
            },
            'market': {
                'data_points': latest_market.data_points_processed if latest_market else 0,
                'websocket_connections': latest_market.websocket_connections if latest_market else 0,
                'latency': latest_market.market_data_latency if latest_market else 0,
                'quote_requests': latest_market.quote_requests if latest_market else 0,
                'provider_health': latest_market.data_provider_health if latest_market else {}
            },
            'alerts': dict(self.alert_metrics),
            'history': {
                'performance': [self._metric_to_dict(m) for m in list(self.performance_history)[-100:]],
                'portfolio': [self._metric_to_dict(m) for m in list(self.portfolio_history)[-100:]],
                'market': [self._metric_to_dict(m) for m in list(self.market_history)[-100:]]
            }
        }
    
    def _metric_to_dict(self, metric: Any) -> Dict[str, Any]:
        """Convert metric object to dictionary"""
        result = {}
        for key, value in metric.__dict__.items():
            if isinstance(value, datetime):
                result[key] = value.isoformat()
            else:
                result[key] = value
        return result
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get overall system health status"""
        latest_performance = self.performance_history[-1] if self.performance_history else None
        
        health_status = 'healthy'
        issues = []
        
        if latest_performance:
            if latest_performance.cpu_usage > 80:
                health_status = 'degraded'
                issues.append('High CPU usage')
            
            if latest_performance.memory_usage > 85:
                health_status = 'degraded'
                issues.append('High memory usage')
            
            if latest_performance.error_rate > 5:
                health_status = 'unhealthy'
                issues.append('High error rate')
            
            if latest_performance.api_latency > 1.0:
                health_status = 'degraded' if health_status == 'healthy' else health_status
                issues.append('High API latency')
        
        return {
            'status': health_status,
            'timestamp': datetime.utcnow().isoformat(),
            'issues': issues,
            'metrics': {
                'cpu': latest_performance.cpu_usage if latest_performance else 0,
                'memory': latest_performance.memory_usage if latest_performance else 0,
                'error_rate': latest_performance.error_rate if latest_performance else 0
            }
        }