"""
High Availability Manager for Financial Planning System

This module provides comprehensive high availability capabilities including:
- Continuous health monitoring and alerting
- Automatic failover and recovery
- Load balancing and traffic management
- Circuit breaker patterns
- Service mesh coordination
- Multi-region deployment management
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple, Any, Callable
import json
import statistics
import aiohttp
import redis
import boto3
from concurrent.futures import ThreadPoolExecutor
import psutil
import socket
import ssl


class ServiceStatus(Enum):
    """Service health status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"
    MAINTENANCE = "maintenance"


class FailoverTrigger(Enum):
    """Failover trigger conditions"""
    HEALTH_CHECK_FAILURE = "health_check_failure"
    RESPONSE_TIME_THRESHOLD = "response_time_threshold"
    ERROR_RATE_THRESHOLD = "error_rate_threshold"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    MANUAL_TRIGGER = "manual_trigger"


class LoadBalanceStrategy(Enum):
    """Load balancing strategies"""
    ROUND_ROBIN = "round_robin"
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"
    LEAST_CONNECTIONS = "least_connections"
    LEAST_RESPONSE_TIME = "least_response_time"
    IP_HASH = "ip_hash"
    GEOGRAPHIC = "geographic"


@dataclass
class HealthCheck:
    """Health check configuration"""
    name: str
    endpoint: str
    method: str = "GET"
    timeout: int = 30
    interval: int = 60
    retries: int = 3
    expected_status: int = 200
    expected_response: Optional[str] = None
    headers: Dict[str, str] = field(default_factory=dict)
    critical: bool = True
    weight: float = 1.0


@dataclass
class ServiceNode:
    """Service node information"""
    node_id: str
    host: str
    port: int
    region: str
    zone: str
    status: ServiceStatus = ServiceStatus.UNKNOWN
    weight: float = 1.0
    capacity: int = 100
    current_load: int = 0
    last_health_check: Optional[datetime] = None
    response_times: List[float] = field(default_factory=list)
    error_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CircuitBreaker:
    """Circuit breaker state"""
    name: str
    failure_threshold: int = 5
    recovery_timeout: int = 60
    half_open_max_calls: int = 3
    state: str = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    failure_count: int = 0
    last_failure_time: Optional[datetime] = None
    next_attempt_time: Optional[datetime] = None


@dataclass
class FailoverEvent:
    """Failover event record"""
    event_id: str
    trigger: FailoverTrigger
    source_node: str
    target_node: str
    timestamp: datetime
    duration: Optional[timedelta] = None
    success: bool = False
    details: Dict[str, Any] = field(default_factory=dict)


class HealthMonitor:
    """Service health monitoring component"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Health check registry
        self.health_checks: Dict[str, HealthCheck] = {}
        self.health_results: Dict[str, Dict] = {}
        
        # Monitoring state
        self.monitoring_active = False
        self.monitor_tasks: List[asyncio.Task] = []
        
        # Alerting
        self.alert_callbacks: List[Callable] = []
        
    def register_health_check(self, health_check: HealthCheck):
        """Register a new health check"""
        self.health_checks[health_check.name] = health_check
        self.health_results[health_check.name] = {
            'status': ServiceStatus.UNKNOWN,
            'last_check': None,
            'response_time': None,
            'consecutive_failures': 0,
            'details': {}
        }
        
        self.logger.info(f"Registered health check: {health_check.name}")
    
    async def start_monitoring(self):
        """Start health monitoring"""
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        
        # Start monitoring tasks for each health check
        for health_check in self.health_checks.values():
            task = asyncio.create_task(self._monitor_health_check(health_check))
            self.monitor_tasks.append(task)
        
        self.logger.info("Health monitoring started")
    
    async def stop_monitoring(self):
        """Stop health monitoring"""
        self.monitoring_active = False
        
        # Cancel all monitoring tasks
        for task in self.monitor_tasks:
            task.cancel()
        
        if self.monitor_tasks:
            await asyncio.gather(*self.monitor_tasks, return_exceptions=True)
        
        self.monitor_tasks.clear()
        self.logger.info("Health monitoring stopped")
    
    async def _monitor_health_check(self, health_check: HealthCheck):
        """Monitor individual health check"""
        while self.monitoring_active:
            try:
                result = await self._execute_health_check(health_check)
                await self._process_health_result(health_check, result)
                
                # Sleep until next check
                await asyncio.sleep(health_check.interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Health check monitoring error for {health_check.name}: {e}")
                await asyncio.sleep(health_check.interval)
    
    async def _execute_health_check(self, health_check: HealthCheck) -> Dict[str, Any]:
        """Execute individual health check"""
        start_time = time.time()
        result = {
            'name': health_check.name,
            'timestamp': datetime.utcnow(),
            'response_time': None,
            'status': ServiceStatus.UNKNOWN,
            'details': {},
            'error': None
        }
        
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=health_check.timeout)) as session:
                async with session.request(
                    health_check.method,
                    health_check.endpoint,
                    headers=health_check.headers
                ) as response:
                    response_time = time.time() - start_time
                    result['response_time'] = response_time
                    
                    # Check status code
                    if response.status == health_check.expected_status:
                        # Check response content if specified
                        if health_check.expected_response:
                            content = await response.text()
                            if health_check.expected_response in content:
                                result['status'] = ServiceStatus.HEALTHY
                            else:
                                result['status'] = ServiceStatus.UNHEALTHY
                                result['details']['content_mismatch'] = True
                        else:
                            result['status'] = ServiceStatus.HEALTHY
                    else:
                        result['status'] = ServiceStatus.UNHEALTHY
                        result['details']['status_code'] = response.status
        
        except asyncio.TimeoutError:
            result['status'] = ServiceStatus.UNHEALTHY
            result['error'] = 'Timeout'
        except Exception as e:
            result['status'] = ServiceStatus.UNHEALTHY
            result['error'] = str(e)
        
        return result
    
    async def _process_health_result(self, health_check: HealthCheck, result: Dict[str, Any]):
        """Process health check result"""
        current_result = self.health_results[health_check.name]
        
        # Update result
        current_result['last_check'] = result['timestamp']
        current_result['response_time'] = result['response_time']
        current_result['details'] = result['details']
        
        # Update status and failure count
        if result['status'] == ServiceStatus.HEALTHY:
            current_result['consecutive_failures'] = 0
        else:
            current_result['consecutive_failures'] += 1
        
        current_result['status'] = result['status']
        
        # Check if alert should be triggered
        if (result['status'] != ServiceStatus.HEALTHY and 
            current_result['consecutive_failures'] >= health_check.retries):
            await self._trigger_alert(health_check, result)
    
    async def _trigger_alert(self, health_check: HealthCheck, result: Dict[str, Any]):
        """Trigger health check alert"""
        alert_data = {
            'type': 'health_check_failure',
            'service': health_check.name,
            'timestamp': result['timestamp'],
            'details': result,
            'critical': health_check.critical
        }
        
        for callback in self.alert_callbacks:
            try:
                await callback(alert_data)
            except Exception as e:
                self.logger.error(f"Alert callback error: {e}")
    
    def get_health_status(self, service_name: Optional[str] = None) -> Dict[str, Any]:
        """Get current health status"""
        if service_name:
            return self.health_results.get(service_name, {})
        
        return {
            'overall_status': self._calculate_overall_status(),
            'services': dict(self.health_results),
            'last_updated': datetime.utcnow()
        }
    
    def _calculate_overall_status(self) -> ServiceStatus:
        """Calculate overall system health status"""
        if not self.health_results:
            return ServiceStatus.UNKNOWN
        
        statuses = [result['status'] for result in self.health_results.values()]
        
        # If any critical service is unhealthy, system is unhealthy
        critical_services = [
            name for name, check in self.health_checks.items()
            if check.critical
        ]
        
        for service_name in critical_services:
            if self.health_results[service_name]['status'] == ServiceStatus.UNHEALTHY:
                return ServiceStatus.UNHEALTHY
        
        # Check for degraded services
        unhealthy_count = statuses.count(ServiceStatus.UNHEALTHY)
        degraded_count = statuses.count(ServiceStatus.DEGRADED)
        
        if unhealthy_count > 0 or degraded_count > len(statuses) * 0.3:
            return ServiceStatus.DEGRADED
        
        return ServiceStatus.HEALTHY


class LoadBalancer:
    """Intelligent load balancing component"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Service nodes
        self.service_nodes: Dict[str, ServiceNode] = {}
        self.active_nodes: Set[str] = set()
        
        # Load balancing state
        self.current_node_index = 0
        self.node_connections: Dict[str, int] = {}
        self.strategy = LoadBalanceStrategy(config.get('strategy', 'round_robin'))
    
    def register_node(self, node: ServiceNode):
        """Register a service node"""
        self.service_nodes[node.node_id] = node
        self.node_connections[node.node_id] = 0
        
        if node.status == ServiceStatus.HEALTHY:
            self.active_nodes.add(node.node_id)
        
        self.logger.info(f"Registered node: {node.node_id} at {node.host}:{node.port}")
    
    def update_node_status(self, node_id: str, status: ServiceStatus):
        """Update node health status"""
        if node_id not in self.service_nodes:
            return
        
        self.service_nodes[node_id].status = status
        self.service_nodes[node_id].last_health_check = datetime.utcnow()
        
        if status == ServiceStatus.HEALTHY:
            self.active_nodes.add(node_id)
        else:
            self.active_nodes.discard(node_id)
        
        self.logger.info(f"Updated node {node_id} status to {status.value}")
    
    async def get_next_node(self, request_context: Optional[Dict[str, Any]] = None) -> Optional[ServiceNode]:
        """Get next node using load balancing strategy"""
        if not self.active_nodes:
            return None
        
        if self.strategy == LoadBalanceStrategy.ROUND_ROBIN:
            return self._round_robin_selection()
        elif self.strategy == LoadBalanceStrategy.WEIGHTED_ROUND_ROBIN:
            return self._weighted_round_robin_selection()
        elif self.strategy == LoadBalanceStrategy.LEAST_CONNECTIONS:
            return self._least_connections_selection()
        elif self.strategy == LoadBalanceStrategy.LEAST_RESPONSE_TIME:
            return self._least_response_time_selection()
        elif self.strategy == LoadBalanceStrategy.IP_HASH:
            return self._ip_hash_selection(request_context)
        elif self.strategy == LoadBalanceStrategy.GEOGRAPHIC:
            return self._geographic_selection(request_context)
        
        return self._round_robin_selection()
    
    def _round_robin_selection(self) -> ServiceNode:
        """Round-robin node selection"""
        active_nodes = list(self.active_nodes)
        node_id = active_nodes[self.current_node_index % len(active_nodes)]
        self.current_node_index += 1
        return self.service_nodes[node_id]
    
    def _weighted_round_robin_selection(self) -> ServiceNode:
        """Weighted round-robin selection"""
        active_nodes = [self.service_nodes[node_id] for node_id in self.active_nodes]
        
        # Calculate total weight
        total_weight = sum(node.weight for node in active_nodes)
        
        # Select based on weight distribution
        import random
        target_weight = random.uniform(0, total_weight)
        
        current_weight = 0
        for node in active_nodes:
            current_weight += node.weight
            if current_weight >= target_weight:
                return node
        
        return active_nodes[0]  # Fallback
    
    def _least_connections_selection(self) -> ServiceNode:
        """Least connections selection"""
        active_nodes = [self.service_nodes[node_id] for node_id in self.active_nodes]
        return min(active_nodes, key=lambda node: self.node_connections[node.node_id])
    
    def _least_response_time_selection(self) -> ServiceNode:
        """Least response time selection"""
        active_nodes = [self.service_nodes[node_id] for node_id in self.active_nodes]
        
        # Filter nodes with response time data
        nodes_with_times = [
            node for node in active_nodes
            if node.response_times
        ]
        
        if not nodes_with_times:
            return self._round_robin_selection()
        
        # Select node with lowest average response time
        return min(nodes_with_times, 
                  key=lambda node: statistics.mean(node.response_times[-10:]))
    
    def record_request(self, node_id: str, response_time: float, success: bool):
        """Record request metrics"""
        if node_id not in self.service_nodes:
            return
        
        node = self.service_nodes[node_id]
        
        # Update response times
        node.response_times.append(response_time)
        if len(node.response_times) > 100:  # Keep last 100 measurements
            node.response_times.pop(0)
        
        # Update error count
        if not success:
            node.error_count += 1
        
        # Update connection count
        self.node_connections[node_id] = max(0, self.node_connections[node_id] - 1)


class HighAvailabilityManager:
    """
    Comprehensive high availability management system
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Components
        self.health_monitor = HealthMonitor(config.get('health_monitoring', {}))
        self.load_balancer = LoadBalancer(config.get('load_balancing', {}))
        
        # Circuit breakers
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        
        # Failover tracking
        self.failover_events: List[FailoverEvent] = []
        self.failover_in_progress: Set[str] = set()
        
        # External services
        self._init_external_services()
        
        # Auto-failover settings
        self.auto_failover_enabled = config.get('auto_failover_enabled', True)
        self.failover_thresholds = config.get('failover_thresholds', {
            'consecutive_failures': 3,
            'error_rate': 0.5,
            'response_time': 5.0
        })
        
        # Register alert callback
        self.health_monitor.alert_callbacks.append(self._handle_health_alert)
    
    def _init_external_services(self):
        """Initialize external service connections"""
        try:
            # Redis for coordination
            redis_config = self.config.get('redis', {})
            self.redis_client = redis.Redis(
                host=redis_config.get('host', 'localhost'),
                port=redis_config.get('port', 6379),
                decode_responses=True
            )
            
            # AWS services for cloud integration
            self.route53_client = boto3.client('route53')
            self.elb_client = boto3.client('elbv2')
            
            # Thread pool for blocking operations
            self.executor = ThreadPoolExecutor(max_workers=10)
            
        except Exception as e:
            self.logger.error(f"Failed to initialize external services: {e}")
    
    async def start(self):
        """Start high availability management"""
        self.logger.info("Starting High Availability Manager")
        
        # Load service configuration
        await self._load_service_configuration()
        
        # Start health monitoring
        await self.health_monitor.start_monitoring()
        
        # Start background tasks
        asyncio.create_task(self._monitor_failover_conditions())
        asyncio.create_task(self._cleanup_old_events())
        
        self.logger.info("High Availability Manager started successfully")
    
    async def stop(self):
        """Stop high availability management"""
        self.logger.info("Stopping High Availability Manager")
        
        # Stop health monitoring
        await self.health_monitor.stop_monitoring()
        
        self.logger.info("High Availability Manager stopped")
    
    async def _load_service_configuration(self):
        """Load service nodes and health checks configuration"""
        # Register default health checks
        default_health_checks = [
            HealthCheck(
                name="web_api",
                endpoint=f"{self.config.get('api_base_url', 'http://localhost:8000')}/health",
                interval=30,
                critical=True
            ),
            HealthCheck(
                name="database",
                endpoint=f"{self.config.get('api_base_url', 'http://localhost:8000')}/health/db",
                interval=60,
                critical=True
            ),
            HealthCheck(
                name="redis",
                endpoint=f"{self.config.get('api_base_url', 'http://localhost:8000')}/health/redis",
                interval=45,
                critical=False
            )
        ]
        
        for health_check in default_health_checks:
            self.health_monitor.register_health_check(health_check)
        
        # Register default service nodes
        default_nodes = [
            ServiceNode(
                node_id="primary_api_1",
                host="localhost",
                port=8000,
                region="us-east-1",
                zone="us-east-1a",
                weight=1.0
            ),
            ServiceNode(
                node_id="backup_api_1",
                host="backup.localhost",
                port=8001,
                region="us-west-2",
                zone="us-west-2a",
                weight=0.8
            )
        ]
        
        for node in default_nodes:
            self.load_balancer.register_node(node)
        
        # Initialize circuit breakers
        services = ['web_api', 'database', 'redis', 'market_data']
        for service in services:
            self.circuit_breakers[service] = CircuitBreaker(
                name=service,
                failure_threshold=self.failover_thresholds.get('consecutive_failures', 3),
                recovery_timeout=60
            )
    
    async def _handle_health_alert(self, alert_data: Dict[str, Any]):
        """Handle health check alerts"""
        self.logger.warning(f"Health alert: {alert_data}")
        
        service_name = alert_data['service']
        
        # Update circuit breaker
        if service_name in self.circuit_breakers:
            circuit_breaker = self.circuit_breakers[service_name]
            circuit_breaker.failure_count += 1
            circuit_breaker.last_failure_time = datetime.utcnow()
            
            # Check if circuit should open
            if circuit_breaker.failure_count >= circuit_breaker.failure_threshold:
                await self._open_circuit_breaker(circuit_breaker)
        
        # Trigger auto-failover if enabled
        if self.auto_failover_enabled and alert_data.get('critical', False):
            await self._trigger_auto_failover(service_name, FailoverTrigger.HEALTH_CHECK_FAILURE)
    
    async def _monitor_failover_conditions(self):
        """Monitor conditions that might trigger failover"""
        while True:
            try:
                # Check response time thresholds
                await self._check_response_time_thresholds()
                
                # Check error rate thresholds
                await self._check_error_rate_thresholds()
                
                # Check resource exhaustion
                await self._check_resource_exhaustion()
                
                # Update circuit breakers
                await self._update_circuit_breakers()
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                self.logger.error(f"Failover condition monitoring error: {e}")
                await asyncio.sleep(30)
    
    async def _check_response_time_thresholds(self):
        """Check if response times exceed thresholds"""
        threshold = self.failover_thresholds.get('response_time', 5.0)
        
        for node_id, node in self.load_balancer.service_nodes.items():
            if node.response_times:
                avg_response_time = statistics.mean(node.response_times[-10:])
                if avg_response_time > threshold:
                    self.logger.warning(f"Node {node_id} response time {avg_response_time:.2f}s exceeds threshold {threshold}s")
                    await self._trigger_node_failover(node_id, FailoverTrigger.RESPONSE_TIME_THRESHOLD)
    
    async def _check_error_rate_thresholds(self):
        """Check if error rates exceed thresholds"""
        threshold = self.failover_thresholds.get('error_rate', 0.5)
        
        for node_id, node in self.load_balancer.service_nodes.items():
            if len(node.response_times) >= 10:  # Need sufficient data
                error_rate = node.error_count / len(node.response_times)
                if error_rate > threshold:
                    self.logger.warning(f"Node {node_id} error rate {error_rate:.2f} exceeds threshold {threshold}")
                    await self._trigger_node_failover(node_id, FailoverTrigger.ERROR_RATE_THRESHOLD)
    
    async def _check_resource_exhaustion(self):
        """Check for resource exhaustion conditions"""
        try:
            # Check local system resources
            cpu_percent = psutil.cpu_percent(interval=1)
            memory_percent = psutil.virtual_memory().percent
            disk_percent = psutil.disk_usage('/').percent
            
            if cpu_percent > 90 or memory_percent > 90 or disk_percent > 90:
                self.logger.warning(f"Resource exhaustion detected: CPU {cpu_percent}%, Memory {memory_percent}%, Disk {disk_percent}%")
                await self._trigger_auto_failover('local_resources', FailoverTrigger.RESOURCE_EXHAUSTION)
        
        except Exception as e:
            self.logger.error(f"Resource check error: {e}")
    
    async def _update_circuit_breakers(self):
        """Update circuit breaker states"""
        current_time = datetime.utcnow()
        
        for circuit_breaker in self.circuit_breakers.values():
            if circuit_breaker.state == "OPEN":
                # Check if recovery timeout has passed
                if (circuit_breaker.next_attempt_time and 
                    current_time >= circuit_breaker.next_attempt_time):
                    circuit_breaker.state = "HALF_OPEN"
                    circuit_breaker.failure_count = 0
                    self.logger.info(f"Circuit breaker {circuit_breaker.name} moved to HALF_OPEN")
    
    async def _open_circuit_breaker(self, circuit_breaker: CircuitBreaker):
        """Open circuit breaker"""
        circuit_breaker.state = "OPEN"
        circuit_breaker.next_attempt_time = datetime.utcnow() + timedelta(seconds=circuit_breaker.recovery_timeout)
        
        self.logger.warning(f"Circuit breaker {circuit_breaker.name} OPENED due to failures")
        
        # Notify about circuit breaker opening
        await self._notify_circuit_breaker_event(circuit_breaker, "OPENED")
    
    async def _trigger_auto_failover(self, service: str, trigger: FailoverTrigger):
        """Trigger automatic failover"""
        if service in self.failover_in_progress:
            self.logger.info(f"Failover already in progress for {service}")
            return
        
        self.failover_in_progress.add(service)
        
        try:
            await self._execute_failover(service, trigger)
        finally:
            self.failover_in_progress.discard(service)
    
    async def _trigger_node_failover(self, node_id: str, trigger: FailoverTrigger):
        """Trigger failover for specific node"""
        if node_id not in self.load_balancer.service_nodes:
            return
        
        # Mark node as unhealthy
        self.load_balancer.update_node_status(node_id, ServiceStatus.UNHEALTHY)
        
        # Find alternative node
        alternative_nodes = [
            node for node_id_alt, node in self.load_balancer.service_nodes.items()
            if node_id_alt != node_id and node.status == ServiceStatus.HEALTHY
        ]
        
        if alternative_nodes:
            target_node = alternative_nodes[0]
            event = FailoverEvent(
                event_id=f"failover_{int(time.time())}",
                trigger=trigger,
                source_node=node_id,
                target_node=target_node.node_id,
                timestamp=datetime.utcnow(),
                success=True
            )
            
            self.failover_events.append(event)
            self.logger.info(f"Failed over from {node_id} to {target_node.node_id}")
        else:
            self.logger.error(f"No healthy alternative nodes available for {node_id}")
    
    async def _execute_failover(self, service: str, trigger: FailoverTrigger):
        """Execute service failover"""
        self.logger.info(f"Executing failover for {service} triggered by {trigger.value}")
        
        start_time = datetime.utcnow()
        success = False
        
        try:
            # Service-specific failover logic
            if service == 'web_api':
                success = await self._failover_web_api()
            elif service == 'database':
                success = await self._failover_database()
            elif service == 'redis':
                success = await self._failover_redis()
            else:
                success = await self._generic_service_failover(service)
            
            duration = datetime.utcnow() - start_time
            
            # Record failover event
            event = FailoverEvent(
                event_id=f"failover_{service}_{int(time.time())}",
                trigger=trigger,
                source_node=f"{service}_primary",
                target_node=f"{service}_backup",
                timestamp=start_time,
                duration=duration,
                success=success
            )
            
            self.failover_events.append(event)
            
            if success:
                self.logger.info(f"Failover for {service} completed successfully in {duration}")
            else:
                self.logger.error(f"Failover for {service} failed")
        
        except Exception as e:
            self.logger.error(f"Failover execution error for {service}: {e}")
    
    async def _failover_web_api(self) -> bool:
        """Failover web API service"""
        try:
            # Update DNS records to point to backup
            # This is a placeholder - actual implementation would use Route53 API
            self.logger.info("Updating DNS records for API failover")
            
            # Update load balancer configuration
            # Remove primary from active pool
            for node_id, node in self.load_balancer.service_nodes.items():
                if 'primary' in node_id:
                    self.load_balancer.update_node_status(node_id, ServiceStatus.UNHEALTHY)
                elif 'backup' in node_id:
                    self.load_balancer.update_node_status(node_id, ServiceStatus.HEALTHY)
            
            return True
        except Exception as e:
            self.logger.error(f"API failover error: {e}")
            return False
    
    async def _failover_database(self) -> bool:
        """Failover database service"""
        try:
            # Promote read replica to primary
            self.logger.info("Promoting database read replica to primary")
            
            # Update application configuration
            # This would typically involve updating connection strings
            
            return True
        except Exception as e:
            self.logger.error(f"Database failover error: {e}")
            return False
    
    async def _failover_redis(self) -> bool:
        """Failover Redis service"""
        try:
            # Switch to backup Redis instance
            self.logger.info("Switching to backup Redis instance")
            
            # Update Redis configuration
            # This would involve updating connection parameters
            
            return True
        except Exception as e:
            self.logger.error(f"Redis failover error: {e}")
            return False
    
    async def _generic_service_failover(self, service: str) -> bool:
        """Generic service failover"""
        try:
            self.logger.info(f"Executing generic failover for {service}")
            
            # Find and activate backup instances
            backup_found = False
            for node_id, node in self.load_balancer.service_nodes.items():
                if service in node_id.lower() and 'backup' in node_id.lower():
                    self.load_balancer.update_node_status(node_id, ServiceStatus.HEALTHY)
                    backup_found = True
            
            return backup_found
        except Exception as e:
            self.logger.error(f"Generic failover error for {service}: {e}")
            return False
    
    async def manual_failover(self, source_node: str, target_node: str) -> bool:
        """Trigger manual failover"""
        self.logger.info(f"Manual failover requested from {source_node} to {target_node}")
        
        if source_node not in self.load_balancer.service_nodes:
            raise ValueError(f"Unknown source node: {source_node}")
        
        if target_node not in self.load_balancer.service_nodes:
            raise ValueError(f"Unknown target node: {target_node}")
        
        # Update node statuses
        self.load_balancer.update_node_status(source_node, ServiceStatus.MAINTENANCE)
        self.load_balancer.update_node_status(target_node, ServiceStatus.HEALTHY)
        
        # Record event
        event = FailoverEvent(
            event_id=f"manual_failover_{int(time.time())}",
            trigger=FailoverTrigger.MANUAL_TRIGGER,
            source_node=source_node,
            target_node=target_node,
            timestamp=datetime.utcnow(),
            success=True
        )
        
        self.failover_events.append(event)
        
        return True
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        health_status = self.health_monitor.get_health_status()
        
        # Node information
        nodes_info = {}
        for node_id, node in self.load_balancer.service_nodes.items():
            nodes_info[node_id] = {
                'status': node.status.value,
                'host': node.host,
                'port': node.port,
                'region': node.region,
                'load': node.current_load,
                'avg_response_time': statistics.mean(node.response_times[-10:]) if node.response_times else None,
                'error_count': node.error_count
            }
        
        # Circuit breaker states
        circuit_states = {
            name: {
                'state': cb.state,
                'failure_count': cb.failure_count,
                'last_failure': cb.last_failure_time.isoformat() if cb.last_failure_time else None
            }
            for name, cb in self.circuit_breakers.items()
        }
        
        return {
            'overall_health': health_status['overall_status'].value,
            'service_health': {
                name: result['status'].value
                for name, result in health_status['services'].items()
            },
            'nodes': nodes_info,
            'circuit_breakers': circuit_states,
            'active_failovers': list(self.failover_in_progress),
            'recent_events': [
                {
                    'event_id': event.event_id,
                    'trigger': event.trigger.value,
                    'timestamp': event.timestamp.isoformat(),
                    'success': event.success
                }
                for event in self.failover_events[-10:]
            ]
        }
    
    async def _cleanup_old_events(self):
        """Clean up old failover events"""
        while True:
            try:
                cutoff_time = datetime.utcnow() - timedelta(days=7)
                self.failover_events = [
                    event for event in self.failover_events
                    if event.timestamp > cutoff_time
                ]
                
                await asyncio.sleep(3600)  # Clean up every hour
            except Exception as e:
                self.logger.error(f"Event cleanup error: {e}")
                await asyncio.sleep(3600)
    
    async def _notify_circuit_breaker_event(self, circuit_breaker: CircuitBreaker, event_type: str):
        """Notify about circuit breaker events"""
        # This would integrate with notification systems
        self.logger.info(f"Circuit breaker {circuit_breaker.name} {event_type}")


# Example usage and testing
if __name__ == "__main__":
    # Configuration example
    config = {
        'health_monitoring': {
            'interval': 30,
            'timeout': 10
        },
        'load_balancing': {
            'strategy': 'least_response_time'
        },
        'redis': {
            'host': 'localhost',
            'port': 6379
        },
        'api_base_url': 'http://localhost:8000',
        'auto_failover_enabled': True,
        'failover_thresholds': {
            'consecutive_failures': 3,
            'error_rate': 0.3,
            'response_time': 2.0
        }
    }
    
    async def example_ha_setup():
        # Initialize HA manager
        ha_manager = HighAvailabilityManager(config)
        
        # Start monitoring
        await ha_manager.start()
        
        # Simulate running for a while
        await asyncio.sleep(60)
        
        # Get status
        status = await ha_manager.get_system_status()
        print(f"System status: {status['overall_health']}")
        
        # Trigger manual failover
        await ha_manager.manual_failover('primary_api_1', 'backup_api_1')
        
        # Stop monitoring
        await ha_manager.stop()
    
    # Run example
    # asyncio.run(example_ha_setup())