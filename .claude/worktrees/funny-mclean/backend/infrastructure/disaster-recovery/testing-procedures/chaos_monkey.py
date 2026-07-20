#!/usr/bin/env python3
"""
Chaos Monkey Implementation for Financial Planning System
Tests system resilience through controlled failure injection
"""

import asyncio
import random
import time
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import json
import yaml
from pathlib import Path
import subprocess
import psutil
import aiofiles
import boto3
import docker
import kubernetes
from kubernetes import client, config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ChaosType(Enum):
    NETWORK_LATENCY = "network_latency"
    NETWORK_PARTITION = "network_partition"
    INSTANCE_TERMINATION = "instance_termination"
    SERVICE_FAILURE = "service_failure"
    DATABASE_CONNECTION_EXHAUSTION = "database_connection_exhaustion"
    DISK_SPACE_EXHAUSTION = "disk_space_exhaustion"
    MEMORY_PRESSURE = "memory_pressure"
    CPU_STRESS = "cpu_stress"
    CONTAINER_RESTART = "container_restart"
    DEPENDENCY_FAILURE = "dependency_failure"


class ChaosSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ChaosExperiment:
    """Chaos experiment definition"""
    experiment_id: str
    name: str
    description: str
    chaos_type: ChaosType
    severity: ChaosSeverity
    
    # Target configuration
    target_service: str
    target_instances: List[str]
    target_percentage: float = 50.0
    
    # Timing configuration
    duration_minutes: int = 5
    delay_before_start: int = 0
    
    # Conditions
    business_hours_allowed: bool = False
    prerequisites: List[str] = None
    
    # Recovery
    auto_recovery: bool = True
    recovery_timeout_minutes: int = 10
    
    # Safety
    abort_conditions: List[str] = None
    max_impact_percentage: float = 25.0
    
    def __post_init__(self):
        if self.prerequisites is None:
            self.prerequisites = []
        if self.abort_conditions is None:
            self.abort_conditions = []


@dataclass
class ChaosExperimentResult:
    """Results of a chaos experiment"""
    experiment_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    success: bool = False
    aborted: bool = False
    
    # Metrics before chaos
    baseline_metrics: Dict[str, Any] = None
    
    # Metrics during chaos
    chaos_metrics: Dict[str, Any] = None
    
    # Recovery metrics
    recovery_metrics: Dict[str, Any] = None
    
    # Observations
    observations: List[str] = None
    
    # System response
    alerts_triggered: List[str] = None
    automated_responses: List[str] = None
    
    # Impact assessment
    service_impact: Dict[str, float] = None
    user_impact: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.baseline_metrics is None:
            self.baseline_metrics = {}
        if self.chaos_metrics is None:
            self.chaos_metrics = {}
        if self.recovery_metrics is None:
            self.recovery_metrics = {}
        if self.observations is None:
            self.observations = []
        if self.alerts_triggered is None:
            self.alerts_triggered = []
        if self.automated_responses is None:
            self.automated_responses = []
        if self.service_impact is None:
            self.service_impact = {}
        if self.user_impact is None:
            self.user_impact = {}


class SystemMetricsCollector:
    """Collects system metrics during chaos experiments"""
    
    def __init__(self):
        self.docker_client = None
        self.k8s_client = None
        
        try:
            self.docker_client = docker.from_env()
        except Exception:
            logger.warning("Docker client not available")
        
        try:
            config.load_incluster_config()
            self.k8s_client = client.CoreV1Api()
        except Exception:
            try:
                config.load_kube_config()
                self.k8s_client = client.CoreV1Api()
            except Exception:
                logger.warning("Kubernetes client not available")
    
    async def collect_system_metrics(self) -> Dict[str, Any]:
        """Collect comprehensive system metrics"""
        metrics = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'cpu': self._get_cpu_metrics(),
            'memory': self._get_memory_metrics(),
            'disk': self._get_disk_metrics(),
            'network': self._get_network_metrics(),
            'containers': await self._get_container_metrics(),
            'kubernetes': await self._get_kubernetes_metrics()
        }
        
        return metrics
    
    def _get_cpu_metrics(self) -> Dict[str, float]:
        """Get CPU utilization metrics"""
        return {
            'usage_percent': psutil.cpu_percent(interval=1),
            'load_1m': psutil.getloadavg()[0],
            'load_5m': psutil.getloadavg()[1],
            'load_15m': psutil.getloadavg()[2],
            'core_count': psutil.cpu_count()
        }
    
    def _get_memory_metrics(self) -> Dict[str, float]:
        """Get memory utilization metrics"""
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        return {
            'usage_percent': memory.percent,
            'available_gb': memory.available / 1024 / 1024 / 1024,
            'total_gb': memory.total / 1024 / 1024 / 1024,
            'swap_usage_percent': swap.percent,
            'swap_total_gb': swap.total / 1024 / 1024 / 1024
        }
    
    def _get_disk_metrics(self) -> Dict[str, Dict[str, float]]:
        """Get disk utilization metrics"""
        disk_metrics = {}
        
        for partition in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                disk_metrics[partition.mountpoint] = {
                    'usage_percent': (usage.used / usage.total) * 100,
                    'free_gb': usage.free / 1024 / 1024 / 1024,
                    'total_gb': usage.total / 1024 / 1024 / 1024
                }
            except PermissionError:
                continue
        
        return disk_metrics
    
    def _get_network_metrics(self) -> Dict[str, Any]:
        """Get network metrics"""
        net_io = psutil.net_io_counters()
        connections = len(psutil.net_connections())
        
        return {
            'bytes_sent': net_io.bytes_sent,
            'bytes_recv': net_io.bytes_recv,
            'packets_sent': net_io.packets_sent,
            'packets_recv': net_io.packets_recv,
            'connections_count': connections
        }
    
    async def _get_container_metrics(self) -> Dict[str, Any]:
        """Get Docker container metrics"""
        if not self.docker_client:
            return {}
        
        try:
            containers = self.docker_client.containers.list()
            metrics = {}
            
            for container in containers:
                stats = container.stats(stream=False)
                
                # Calculate CPU usage
                cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - \
                           stats['precpu_stats']['cpu_usage']['total_usage']
                system_cpu_delta = stats['cpu_stats']['system_cpu_usage'] - \
                                  stats['precpu_stats']['system_cpu_usage']
                
                cpu_usage = 0
                if system_cpu_delta > 0:
                    cpu_usage = (cpu_delta / system_cpu_delta) * 100
                
                # Calculate memory usage
                memory_usage = stats['memory_stats']['usage']
                memory_limit = stats['memory_stats']['limit']
                memory_percent = (memory_usage / memory_limit) * 100
                
                metrics[container.name] = {
                    'status': container.status,
                    'cpu_percent': cpu_usage,
                    'memory_percent': memory_percent,
                    'memory_usage_mb': memory_usage / 1024 / 1024,
                    'network_rx_bytes': stats['networks']['eth0']['rx_bytes'] if 'networks' in stats else 0,
                    'network_tx_bytes': stats['networks']['eth0']['tx_bytes'] if 'networks' in stats else 0
                }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to collect container metrics: {e}")
            return {}
    
    async def _get_kubernetes_metrics(self) -> Dict[str, Any]:
        """Get Kubernetes cluster metrics"""
        if not self.k8s_client:
            return {}
        
        try:
            # Get pod metrics
            pods = self.k8s_client.list_pod_for_all_namespaces()
            pod_metrics = {}
            
            for pod in pods.items:
                pod_metrics[f"{pod.metadata.namespace}/{pod.metadata.name}"] = {
                    'phase': pod.status.phase,
                    'ready': sum(1 for condition in (pod.status.conditions or []) 
                               if condition.type == 'Ready' and condition.status == 'True'),
                    'restarts': sum(container.restart_count for container in (pod.status.container_statuses or []))
                }
            
            # Get node metrics
            nodes = self.k8s_client.list_node()
            node_metrics = {}
            
            for node in nodes.items:
                node_metrics[node.metadata.name] = {
                    'ready': any(condition.type == 'Ready' and condition.status == 'True' 
                               for condition in node.status.conditions),
                    'capacity_cpu': node.status.capacity.get('cpu', '0'),
                    'capacity_memory': node.status.capacity.get('memory', '0')
                }
            
            return {
                'pods': pod_metrics,
                'nodes': node_metrics
            }
            
        except Exception as e:
            logger.error(f"Failed to collect Kubernetes metrics: {e}")
            return {}


class ChaosMonkey:
    """Main Chaos Monkey implementation"""
    
    def __init__(self, config_path: str = None):
        self.config = self._load_config(config_path)
        self.metrics_collector = SystemMetricsCollector()
        self.running_experiments: Dict[str, ChaosExperiment] = {}
        self.experiment_results: List[ChaosExperimentResult] = []
        
        # Safety mechanisms
        self.abort_all_experiments = False
        self.safety_checks_enabled = True
        self.max_concurrent_experiments = 3
        
        # Experiment registry
        self.experiment_registry: Dict[str, ChaosExperiment] = {}
        self._load_experiment_definitions()
    
    def _load_config(self, config_path: str = None) -> Dict[str, Any]:
        """Load chaos monkey configuration"""
        default_config = {
            'chaos_monkey': {
                'enabled': True,
                'business_hours_protection': True,
                'business_hours_start': 8,
                'business_hours_end': 18,
                'business_days': [0, 1, 2, 3, 4],  # Monday to Friday
                'safety_checks': True,
                'max_concurrent_experiments': 3,
                'experiment_cooldown_minutes': 30,
                'abort_on_high_error_rate': True,
                'error_rate_threshold': 10.0
            },
            'notifications': {
                'webhook_url': '',
                'email_recipients': [],
                'slack_channel': ''
            }
        }
        
        if config_path and Path(config_path).exists():
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                return {**default_config, **config}
        
        return default_config
    
    def _load_experiment_definitions(self):
        """Load predefined chaos experiments"""
        # Network latency experiment
        self.experiment_registry['network_latency'] = ChaosExperiment(
            experiment_id='network_latency',
            name='Network Latency Injection',
            description='Inject network latency to test application resilience',
            chaos_type=ChaosType.NETWORK_LATENCY,
            severity=ChaosSeverity.MEDIUM,
            target_service='web',
            target_instances=[],
            target_percentage=30.0,
            duration_minutes=10,
            business_hours_allowed=False,
            prerequisites=['healthy_system', 'backup_available'],
            abort_conditions=['error_rate_above_10_percent', 'response_time_above_5s']
        )
        
        # Database connection exhaustion
        self.experiment_registry['db_connection_exhaustion'] = ChaosExperiment(
            experiment_id='db_connection_exhaustion',
            name='Database Connection Pool Exhaustion',
            description='Exhaust database connection pool to test connection handling',
            chaos_type=ChaosType.DATABASE_CONNECTION_EXHAUSTION,
            severity=ChaosSeverity.HIGH,
            target_service='database',
            target_instances=[],
            duration_minutes=5,
            business_hours_allowed=False,
            abort_conditions=['database_unavailable', 'error_rate_above_25_percent']
        )
        
        # Container restart experiment
        self.experiment_registry['container_restart'] = ChaosExperiment(
            experiment_id='container_restart',
            name='Random Container Restart',
            description='Randomly restart containers to test recovery mechanisms',
            chaos_type=ChaosType.CONTAINER_RESTART,
            severity=ChaosSeverity.MEDIUM,
            target_service='app',
            target_instances=[],
            target_percentage=25.0,
            duration_minutes=1,
            business_hours_allowed=True,
            auto_recovery=False  # Container should restart automatically
        )
        
        # Memory pressure experiment
        self.experiment_registry['memory_pressure'] = ChaosExperiment(
            experiment_id='memory_pressure',
            name='Memory Pressure Test',
            description='Create memory pressure to test OOM handling',
            chaos_type=ChaosType.MEMORY_PRESSURE,
            severity=ChaosSeverity.HIGH,
            target_service='web',
            target_instances=[],
            duration_minutes=3,
            business_hours_allowed=False,
            abort_conditions=['system_memory_above_95_percent']
        )
    
    async def run_experiment(self, experiment_id: str, custom_config: Dict[str, Any] = None) -> ChaosExperimentResult:
        """Run a specific chaos experiment"""
        if experiment_id not in self.experiment_registry:
            raise ValueError(f"Unknown experiment: {experiment_id}")
        
        experiment = self.experiment_registry[experiment_id]
        
        # Apply custom configuration
        if custom_config:
            for key, value in custom_config.items():
                if hasattr(experiment, key):
                    setattr(experiment, key, value)
        
        # Safety checks
        if not await self._pre_experiment_safety_checks(experiment):
            logger.error(f"Pre-experiment safety checks failed for {experiment_id}")
            return ChaosExperimentResult(
                experiment_id=experiment_id,
                start_time=datetime.now(timezone.utc),
                aborted=True
            )
        
        # Check if we can run during current time
        if not self._is_experiment_allowed_now(experiment):
            logger.info(f"Experiment {experiment_id} not allowed at current time")
            return ChaosExperimentResult(
                experiment_id=experiment_id,
                start_time=datetime.now(timezone.utc),
                aborted=True
            )
        
        # Check concurrent experiment limit
        if len(self.running_experiments) >= self.max_concurrent_experiments:
            logger.warning(f"Maximum concurrent experiments ({self.max_concurrent_experiments}) reached")
            return ChaosExperimentResult(
                experiment_id=experiment_id,
                start_time=datetime.now(timezone.utc),
                aborted=True
            )
        
        # Start experiment
        result = ChaosExperimentResult(
            experiment_id=experiment_id,
            start_time=datetime.now(timezone.utc)
        )
        
        self.running_experiments[experiment_id] = experiment
        
        try:
            logger.info(f"Starting chaos experiment: {experiment.name}")
            
            # Collect baseline metrics
            result.baseline_metrics = await self.metrics_collector.collect_system_metrics()
            
            # Wait for delay if specified
            if experiment.delay_before_start > 0:
                await asyncio.sleep(experiment.delay_before_start)
            
            # Execute chaos
            await self._execute_chaos(experiment, result)
            
            # Monitor during chaos
            await self._monitor_during_chaos(experiment, result)
            
            # Recovery
            if experiment.auto_recovery:
                await self._execute_recovery(experiment, result)
            
            # Collect final metrics
            result.recovery_metrics = await self.metrics_collector.collect_system_metrics()
            
            result.success = True
            
        except Exception as e:
            logger.error(f"Experiment {experiment_id} failed: {e}")
            result.observations.append(f"Experiment failed with error: {str(e)}")
            
            # Attempt recovery
            if experiment.auto_recovery:
                try:
                    await self._execute_recovery(experiment, result)
                except Exception as recovery_error:
                    logger.error(f"Recovery failed for {experiment_id}: {recovery_error}")
        
        finally:
            result.end_time = datetime.now(timezone.utc)
            self.running_experiments.pop(experiment_id, None)
            self.experiment_results.append(result)
            
            # Send notification
            await self._send_experiment_notification(experiment, result)
            
            logger.info(f"Chaos experiment completed: {experiment.name} - Success: {result.success}")
        
        return result
    
    async def _pre_experiment_safety_checks(self, experiment: ChaosExperiment) -> bool:
        """Perform safety checks before running experiment"""
        if not self.safety_checks_enabled:
            return True
        
        # Check system health
        metrics = await self.metrics_collector.collect_system_metrics()
        
        # CPU check
        if metrics['cpu']['usage_percent'] > 80:
            logger.warning("High CPU usage detected, aborting experiment")
            return False
        
        # Memory check
        if metrics['memory']['usage_percent'] > 90:
            logger.warning("High memory usage detected, aborting experiment")
            return False
        
        # Disk space check
        for mount, disk_info in metrics['disk'].items():
            if disk_info['usage_percent'] > 90:
                logger.warning(f"High disk usage on {mount}, aborting experiment")
                return False
        
        # Check prerequisite conditions
        for prerequisite in experiment.prerequisites:
            if not await self._check_prerequisite(prerequisite):
                logger.warning(f"Prerequisite not met: {prerequisite}")
                return False
        
        return True
    
    async def _check_prerequisite(self, prerequisite: str) -> bool:
        """Check if a prerequisite condition is met"""
        if prerequisite == 'healthy_system':
            # Check if system is healthy
            return True  # Implement actual health check
        elif prerequisite == 'backup_available':
            # Check if recent backup is available
            return True  # Implement actual backup check
        else:
            logger.warning(f"Unknown prerequisite: {prerequisite}")
            return False
    
    def _is_experiment_allowed_now(self, experiment: ChaosExperiment) -> bool:
        """Check if experiment is allowed at current time"""
        if not experiment.business_hours_allowed:
            now = datetime.now()
            
            # Check if it's a business day
            if now.weekday() in self.config['chaos_monkey']['business_days']:
                # Check if it's business hours
                start_hour = self.config['chaos_monkey']['business_hours_start']
                end_hour = self.config['chaos_monkey']['business_hours_end']
                
                if start_hour <= now.hour < end_hour:
                    logger.info("Business hours protection active, experiment not allowed")
                    return False
        
        return True
    
    async def _execute_chaos(self, experiment: ChaosExperiment, result: ChaosExperimentResult):
        """Execute the chaos action based on experiment type"""
        chaos_type = experiment.chaos_type
        
        if chaos_type == ChaosType.NETWORK_LATENCY:
            await self._inject_network_latency(experiment, result)
        elif chaos_type == ChaosType.NETWORK_PARTITION:
            await self._create_network_partition(experiment, result)
        elif chaos_type == ChaosType.INSTANCE_TERMINATION:
            await self._terminate_instances(experiment, result)
        elif chaos_type == ChaosType.SERVICE_FAILURE:
            await self._fail_service(experiment, result)
        elif chaos_type == ChaosType.DATABASE_CONNECTION_EXHAUSTION:
            await self._exhaust_database_connections(experiment, result)
        elif chaos_type == ChaosType.DISK_SPACE_EXHAUSTION:
            await self._exhaust_disk_space(experiment, result)
        elif chaos_type == ChaosType.MEMORY_PRESSURE:
            await self._create_memory_pressure(experiment, result)
        elif chaos_type == ChaosType.CPU_STRESS:
            await self._create_cpu_stress(experiment, result)
        elif chaos_type == ChaosType.CONTAINER_RESTART:
            await self._restart_containers(experiment, result)
        elif chaos_type == ChaosType.DEPENDENCY_FAILURE:
            await self._fail_dependency(experiment, result)
        else:
            raise ValueError(f"Unknown chaos type: {chaos_type}")
    
    async def _inject_network_latency(self, experiment: ChaosExperiment, result: ChaosExperimentResult):
        """Inject network latency using tc (traffic control)"""
        latency_ms = 100 + random.randint(0, 200)  # 100-300ms latency
        
        # Use tc to add latency
        cmd = f"tc qdisc add dev eth0 root netem delay {latency_ms}ms"
        
        try:
            process = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                result.observations.append(f"Injected {latency_ms}ms network latency")
                logger.info(f"Network latency injected: {latency_ms}ms")
            else:
                result.observations.append(f"Failed to inject network latency: {stderr.decode()}")
                
        except Exception as e:
            result.observations.append(f"Network latency injection failed: {str(e)}")
    
    async def _create_network_partition(self, experiment: ChaosExperiment, result: ChaosExperimentResult):
        """Create network partition using iptables"""
        # Block traffic to specific services
        target_port = 5432  # PostgreSQL port
        
        cmd = f"iptables -A OUTPUT -p tcp --dport {target_port} -j DROP"
        
        try:
            process = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                result.observations.append(f"Created network partition for port {target_port}")
                logger.info(f"Network partition created for port {target_port}")
            else:
                result.observations.append(f"Failed to create network partition: {stderr.decode()}")
                
        except Exception as e:
            result.observations.append(f"Network partition creation failed: {str(e)}")
    
    async def _restart_containers(self, experiment: ChaosExperiment, result: ChaosExperimentResult):
        """Restart random containers"""
        if not self.metrics_collector.docker_client:
            result.observations.append("Docker client not available")
            return
        
        try:
            containers = self.metrics_collector.docker_client.containers.list()
            
            # Filter containers by target service
            target_containers = [
                c for c in containers 
                if experiment.target_service in c.name or 
                   experiment.target_service in (c.labels.get('service', ''))
            ]
            
            if not target_containers:
                result.observations.append(f"No containers found for service: {experiment.target_service}")
                return
            
            # Select random containers based on percentage
            num_to_restart = max(1, int(len(target_containers) * experiment.target_percentage / 100))
            containers_to_restart = random.sample(target_containers, num_to_restart)
            
            for container in containers_to_restart:
                container.restart()
                result.observations.append(f"Restarted container: {container.name}")
                logger.info(f"Restarted container: {container.name}")
                
        except Exception as e:
            result.observations.append(f"Container restart failed: {str(e)}")
    
    async def _exhaust_database_connections(self, experiment: ChaosExperiment, result: ChaosExperimentResult):
        """Exhaust database connection pool"""
        # This would create many connections to exhaust the pool
        # Implementation depends on specific database configuration
        result.observations.append("Database connection exhaustion simulation started")
        
        # Simulate by creating a burst of connections
        connections = []
        try:
            for i in range(100):  # Try to create 100 connections
                # This would normally connect to the actual database
                # conn = await asyncpg.connect(database_url)
                # connections.append(conn)
                pass
            
            result.observations.append(f"Created {len(connections)} database connections")
            
        except Exception as e:
            result.observations.append(f"Database connection exhaustion: {str(e)}")
        finally:
            # Clean up connections
            for conn in connections:
                try:
                    # await conn.close()
                    pass
                except Exception:
                    pass
    
    async def _create_memory_pressure(self, experiment: ChaosExperiment, result: ChaosExperimentResult):
        """Create memory pressure by allocating memory"""
        memory_to_allocate_mb = 1024  # 1GB
        
        try:
            # Use stress tool if available
            cmd = f"stress --vm 1 --vm-bytes {memory_to_allocate_mb}M --timeout {experiment.duration_minutes * 60}s"
            
            process = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            result.observations.append(f"Started memory stress test: {memory_to_allocate_mb}MB")
            logger.info(f"Memory pressure created: {memory_to_allocate_mb}MB")
            
        except Exception as e:
            result.observations.append(f"Memory pressure creation failed: {str(e)}")
    
    async def _create_cpu_stress(self, experiment: ChaosExperiment, result: ChaosExperimentResult):
        """Create CPU stress"""
        cpu_cores = psutil.cpu_count()
        
        try:
            # Use stress tool to stress CPU
            cmd = f"stress --cpu {cpu_cores} --timeout {experiment.duration_minutes * 60}s"
            
            process = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            result.observations.append(f"Started CPU stress test on {cpu_cores} cores")
            logger.info(f"CPU stress created on {cpu_cores} cores")
            
        except Exception as e:
            result.observations.append(f"CPU stress creation failed: {str(e)}")
    
    async def _monitor_during_chaos(self, experiment: ChaosExperiment, result: ChaosExperimentResult):
        """Monitor system during chaos experiment"""
        duration_seconds = experiment.duration_minutes * 60
        monitoring_interval = 10  # seconds
        
        start_time = time.time()
        
        while time.time() - start_time < duration_seconds:
            if self.abort_all_experiments:
                result.aborted = True
                result.observations.append("Experiment aborted by global abort signal")
                break
            
            # Collect metrics
            metrics = await self.metrics_collector.collect_system_metrics()
            result.chaos_metrics[f"t_{int(time.time() - start_time)}"] = metrics
            
            # Check abort conditions
            if await self._should_abort_experiment(experiment, metrics):
                result.aborted = True
                result.observations.append("Experiment aborted due to abort conditions")
                break
            
            await asyncio.sleep(monitoring_interval)
    
    async def _should_abort_experiment(self, experiment: ChaosExperiment, metrics: Dict[str, Any]) -> bool:
        """Check if experiment should be aborted based on current metrics"""
        for condition in experiment.abort_conditions:
            if condition == 'error_rate_above_10_percent':
                # This would check actual error rate from monitoring system
                # For simulation, randomly decide
                if random.random() < 0.05:  # 5% chance to trigger abort
                    logger.warning("Error rate threshold exceeded")
                    return True
            
            elif condition == 'response_time_above_5s':
                # This would check actual response times
                # For simulation, randomly decide
                if random.random() < 0.03:  # 3% chance to trigger abort
                    logger.warning("Response time threshold exceeded")
                    return True
            
            elif condition == 'system_memory_above_95_percent':
                if metrics['memory']['usage_percent'] > 95:
                    logger.warning("System memory usage too high")
                    return True
            
            elif condition == 'database_unavailable':
                # This would check actual database connectivity
                # For simulation, randomly decide
                if random.random() < 0.02:  # 2% chance to trigger abort
                    logger.warning("Database unavailable")
                    return True
        
        return False
    
    async def _execute_recovery(self, experiment: ChaosExperiment, result: ChaosExperimentResult):
        """Execute recovery actions to restore normal state"""
        chaos_type = experiment.chaos_type
        
        try:
            if chaos_type == ChaosType.NETWORK_LATENCY:
                # Remove network latency
                cmd = "tc qdisc del dev eth0 root"
                process = await asyncio.create_subprocess_shell(cmd)
                await process.communicate()
                result.observations.append("Removed network latency")
            
            elif chaos_type == ChaosType.NETWORK_PARTITION:
                # Remove iptables rule
                cmd = "iptables -F OUTPUT"
                process = await asyncio.create_subprocess_shell(cmd)
                await process.communicate()
                result.observations.append("Removed network partition")
            
            elif chaos_type in [ChaosType.MEMORY_PRESSURE, ChaosType.CPU_STRESS]:
                # Kill stress processes
                cmd = "pkill -f stress"
                process = await asyncio.create_subprocess_shell(cmd)
                await process.communicate()
                result.observations.append("Stopped stress processes")
            
            # Add more recovery actions as needed
            
            logger.info(f"Recovery completed for {experiment.name}")
            
        except Exception as e:
            logger.error(f"Recovery failed for {experiment.name}: {e}")
            result.observations.append(f"Recovery failed: {str(e)}")
    
    async def _send_experiment_notification(self, experiment: ChaosExperiment, result: ChaosExperimentResult):
        """Send notification about experiment completion"""
        notification = {
            'experiment': experiment.name,
            'experiment_id': experiment.experiment_id,
            'success': result.success,
            'aborted': result.aborted,
            'duration_minutes': (result.end_time - result.start_time).total_seconds() / 60 if result.end_time else None,
            'observations': result.observations,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        logger.info(f"Chaos experiment notification: {json.dumps(notification, indent=2)}")
        
        # Here you would implement actual notification sending
        # (webhook, email, Slack, etc.)
    
    async def run_chaos_schedule(self, schedule_config: Dict[str, Any]):
        """Run chaos experiments on a schedule"""
        logger.info("Starting chaos monkey scheduler")
        
        while not self.abort_all_experiments:
            try:
                # Select random experiment
                available_experiments = list(self.experiment_registry.keys())
                experiment_id = random.choice(available_experiments)
                
                # Check if we should run an experiment
                if self._should_run_experiment():
                    logger.info(f"Running scheduled chaos experiment: {experiment_id}")
                    result = await self.run_experiment(experiment_id)
                    
                    # Wait for cooldown
                    cooldown_minutes = self.config['chaos_monkey']['experiment_cooldown_minutes']
                    await asyncio.sleep(cooldown_minutes * 60)
                
                else:
                    # Wait before checking again
                    await asyncio.sleep(300)  # 5 minutes
                    
            except Exception as e:
                logger.error(f"Chaos scheduler error: {e}")
                await asyncio.sleep(60)  # Wait before retry
    
    def _should_run_experiment(self) -> bool:
        """Determine if we should run an experiment now"""
        # Random chance based on configuration
        if random.random() > 0.1:  # 10% chance per check
            return False
        
        # Don't run during business hours if protection is enabled
        if self.config['chaos_monkey']['business_hours_protection']:
            now = datetime.now()
            if (now.weekday() in self.config['chaos_monkey']['business_days'] and
                self.config['chaos_monkey']['business_hours_start'] <= now.hour < self.config['chaos_monkey']['business_hours_end']):
                return False
        
        return True
    
    async def abort_all_experiments(self):
        """Abort all running experiments"""
        logger.warning("Aborting all running chaos experiments")
        self.abort_all_experiments = True
        
        # Wait for experiments to finish aborting
        while self.running_experiments:
            await asyncio.sleep(1)
        
        self.abort_all_experiments = False
    
    def get_experiment_report(self) -> Dict[str, Any]:
        """Generate comprehensive experiment report"""
        total_experiments = len(self.experiment_results)
        successful_experiments = sum(1 for r in self.experiment_results if r.success)
        aborted_experiments = sum(1 for r in self.experiment_results if r.aborted)
        
        return {
            'summary': {
                'total_experiments': total_experiments,
                'successful_experiments': successful_experiments,
                'aborted_experiments': aborted_experiments,
                'success_rate': successful_experiments / total_experiments if total_experiments > 0 else 0
            },
            'recent_experiments': [
                {
                    'experiment_id': r.experiment_id,
                    'start_time': r.start_time.isoformat(),
                    'success': r.success,
                    'aborted': r.aborted,
                    'observations': r.observations
                }
                for r in self.experiment_results[-10:]  # Last 10 experiments
            ],
            'running_experiments': list(self.running_experiments.keys()),
            'available_experiments': list(self.experiment_registry.keys())
        }


async def main():
    """Main function for CLI usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Chaos Monkey for Financial Planning System')
    parser.add_argument('action', choices=['run', 'schedule', 'list', 'abort', 'report'])
    parser.add_argument('--experiment', help='Experiment ID to run')
    parser.add_argument('--config', help='Configuration file path')
    parser.add_argument('--duration', type=int, help='Override experiment duration (minutes)')
    parser.add_argument('--target-percentage', type=float, help='Override target percentage')
    
    args = parser.parse_args()
    
    chaos_monkey = ChaosMonkey(args.config)
    
    try:
        if args.action == 'run':
            if not args.experiment:
                print("Error: --experiment required for run action")
                return 1
            
            custom_config = {}
            if args.duration:
                custom_config['duration_minutes'] = args.duration
            if args.target_percentage:
                custom_config['target_percentage'] = args.target_percentage
            
            result = await chaos_monkey.run_experiment(args.experiment, custom_config)
            
            print(f"Experiment completed:")
            print(f"  Success: {result.success}")
            print(f"  Aborted: {result.aborted}")
            print(f"  Observations: {result.observations}")
        
        elif args.action == 'schedule':
            schedule_config = chaos_monkey.config.get('schedule', {})
            await chaos_monkey.run_chaos_schedule(schedule_config)
        
        elif args.action == 'list':
            experiments = chaos_monkey.experiment_registry
            print("Available experiments:")
            for exp_id, exp in experiments.items():
                print(f"  {exp_id}: {exp.name} ({exp.severity.value})")
        
        elif args.action == 'abort':
            await chaos_monkey.abort_all_experiments()
            print("All experiments aborted")
        
        elif args.action == 'report':
            report = chaos_monkey.get_experiment_report()
            print(json.dumps(report, indent=2, default=str))
        
        return 0
        
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)