"""
Multi-Region Deployment Manager for Financial Planning System

This module provides comprehensive multi-region deployment and coordination including:
- Cross-region deployment orchestration
- Regional failover coordination
- Data synchronization across regions
- Latency-based routing
- Compliance and data residency management
- Cross-region disaster recovery
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple, Any
import json
import boto3
import aiohttp
import redis.asyncio as aioredis
from concurrent.futures import ThreadPoolExecutor
import dns.resolver
import geoip2.database


class RegionStatus(Enum):
    """Regional deployment status"""
    ACTIVE = "active"
    STANDBY = "standby"
    MAINTENANCE = "maintenance"
    DEGRADED = "degraded"
    OFFLINE = "offline"


class DeploymentStrategy(Enum):
    """Multi-region deployment strategies"""
    ACTIVE_ACTIVE = "active_active"
    ACTIVE_PASSIVE = "active_passive"
    BLUE_GREEN = "blue_green"
    CANARY = "canary"
    ROLLING = "rolling"


class DataSyncStrategy(Enum):
    """Data synchronization strategies"""
    SYNCHRONOUS = "synchronous"
    ASYNCHRONOUS = "asynchronous"
    EVENTUAL_CONSISTENCY = "eventual_consistency"
    CONFLICT_RESOLUTION = "conflict_resolution"


@dataclass
class Region:
    """Regional deployment configuration"""
    region_id: str
    name: str
    aws_region: str
    status: RegionStatus
    priority: int  # Lower number = higher priority
    capacity: int
    current_load: int = 0
    latency_ms: float = 0.0
    compliance_zones: List[str] = field(default_factory=list)
    data_residency_rules: Dict[str, Any] = field(default_factory=dict)
    endpoints: Dict[str, str] = field(default_factory=dict)
    last_health_check: Optional[datetime] = None


@dataclass
class DeploymentJob:
    """Deployment job tracking"""
    job_id: str
    target_regions: List[str]
    strategy: DeploymentStrategy
    version: str
    start_time: datetime
    estimated_duration: timedelta
    current_phase: str = "preparing"
    completed_regions: List[str] = field(default_factory=list)
    failed_regions: List[str] = field(default_factory=list)
    rollback_triggered: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SyncOperation:
    """Data synchronization operation"""
    sync_id: str
    source_region: str
    target_regions: List[str]
    data_type: str
    strategy: DataSyncStrategy
    priority: int
    start_time: datetime
    progress: float = 0.0
    conflicts: List[Dict[str, Any]] = field(default_factory=list)
    status: str = "running"


class LatencyMonitor:
    """Monitor inter-region latency"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Latency measurements
        self.latency_matrix: Dict[Tuple[str, str], List[float]] = {}
        self.monitoring_active = False
        
    async def start_monitoring(self, regions: Dict[str, Region]):
        """Start latency monitoring between regions"""
        self.monitoring_active = True
        
        # Create monitoring tasks for all region pairs
        tasks = []
        for source_region in regions.values():
            for target_region in regions.values():
                if source_region.region_id != target_region.region_id:
                    task = asyncio.create_task(
                        self._monitor_latency_pair(source_region, target_region)
                    )
                    tasks.append(task)
        
        self.logger.info(f"Started latency monitoring for {len(tasks)} region pairs")
        
        return tasks
    
    async def _monitor_latency_pair(self, source: Region, target: Region):
        """Monitor latency between two regions"""
        pair_key = (source.region_id, target.region_id)
        
        while self.monitoring_active:
            try:
                latency = await self._measure_latency(source, target)
                
                if pair_key not in self.latency_matrix:
                    self.latency_matrix[pair_key] = []
                
                self.latency_matrix[pair_key].append(latency)
                
                # Keep only recent measurements (last 100)
                if len(self.latency_matrix[pair_key]) > 100:
                    self.latency_matrix[pair_key].pop(0)
                
                await asyncio.sleep(self.config.get('latency_check_interval', 60))
                
            except Exception as e:
                self.logger.error(f"Latency monitoring error {source.region_id} -> {target.region_id}: {e}")
                await asyncio.sleep(60)
    
    async def _measure_latency(self, source: Region, target: Region) -> float:
        """Measure latency between regions"""
        start_time = time.time()
        
        try:
            endpoint = target.endpoints.get('health', f"https://{target.aws_region}.amazonaws.com")
            
            async with aiohttp.ClientSession() as session:
                async with session.get(endpoint, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    await response.text()
                    
            return (time.time() - start_time) * 1000  # Convert to milliseconds
            
        except Exception:
            return float('inf')  # Indicate unreachable
    
    def get_latency_matrix(self) -> Dict[Tuple[str, str], float]:
        """Get current latency matrix"""
        result = {}
        for pair_key, measurements in self.latency_matrix.items():
            if measurements:
                result[pair_key] = sum(measurements[-10:]) / len(measurements[-10:])  # Average of last 10
            else:
                result[pair_key] = float('inf')
        
        return result
    
    def find_closest_region(self, source_region: str, available_regions: List[str]) -> Optional[str]:
        """Find the closest available region"""
        if source_region in available_regions:
            return source_region
        
        latencies = []
        for target_region in available_regions:
            pair_key = (source_region, target_region)
            if pair_key in self.latency_matrix and self.latency_matrix[pair_key]:
                avg_latency = sum(self.latency_matrix[pair_key][-10:]) / len(self.latency_matrix[pair_key][-10:])
                latencies.append((target_region, avg_latency))
        
        if not latencies:
            return available_regions[0] if available_regions else None
        
        # Return region with lowest latency
        return min(latencies, key=lambda x: x[1])[0]


class GeographicRouter:
    """Geographic-based request routing"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # GeoIP database for location detection
        try:
            self.geoip_reader = geoip2.database.Reader(config.get('geoip_db_path', '/usr/local/share/GeoIP/GeoLite2-City.mmdb'))
        except Exception as e:
            self.logger.warning(f"GeoIP database not available: {e}")
            self.geoip_reader = None
        
        # Region mappings
        self.country_to_region: Dict[str, str] = config.get('country_mappings', {
            'US': 'us-east-1',
            'CA': 'us-east-1',
            'GB': 'eu-west-1',
            'DE': 'eu-west-1',
            'FR': 'eu-west-1',
            'JP': 'ap-northeast-1',
            'AU': 'ap-southeast-2',
            'SG': 'ap-southeast-1'
        })
    
    def get_optimal_region(self, client_ip: str, available_regions: List[Region], 
                          latency_matrix: Dict[Tuple[str, str], float]) -> Optional[Region]:
        """Determine optimal region for client"""
        try:
            # Get client location
            client_country = self._get_client_country(client_ip)
            if not client_country:
                return self._get_default_region(available_regions)
            
            # Find preferred region based on geography
            preferred_region_id = self.country_to_region.get(client_country)
            if preferred_region_id:
                # Check if preferred region is available
                for region in available_regions:
                    if region.region_id == preferred_region_id and region.status == RegionStatus.ACTIVE:
                        return region
            
            # Fallback to latency-based selection
            return self._select_by_latency(client_country, available_regions, latency_matrix)
            
        except Exception as e:
            self.logger.error(f"Geographic routing error: {e}")
            return self._get_default_region(available_regions)
    
    def _get_client_country(self, client_ip: str) -> Optional[str]:
        """Get client country from IP address"""
        if not self.geoip_reader:
            return None
        
        try:
            response = self.geoip_reader.city(client_ip)
            return response.country.iso_code
        except Exception:
            return None
    
    def _get_default_region(self, available_regions: List[Region]) -> Optional[Region]:
        """Get default region (highest priority)"""
        if not available_regions:
            return None
        
        active_regions = [r for r in available_regions if r.status == RegionStatus.ACTIVE]
        if not active_regions:
            return available_regions[0]
        
        return min(active_regions, key=lambda r: r.priority)
    
    def _select_by_latency(self, client_country: str, available_regions: List[Region],
                          latency_matrix: Dict[Tuple[str, str], float]) -> Optional[Region]:
        """Select region based on latency measurements"""
        # This is a simplified implementation
        # In practice, you'd need latency from client to regions, not region-to-region
        return self._get_default_region(available_regions)


class DataSyncManager:
    """Manage data synchronization across regions"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Sync operations tracking
        self.active_syncs: Dict[str, SyncOperation] = {}
        self.sync_history: List[SyncOperation] = []
        
        # Redis for coordination
        self.redis_client = None
        
    async def initialize(self):
        """Initialize data sync manager"""
        # Initialize Redis connection for coordination
        redis_config = self.config.get('redis', {})
        self.redis_client = await aioredis.from_url(
            f"redis://{redis_config.get('host', 'localhost')}:{redis_config.get('port', 6379)}"
        )
        
        self.logger.info("DataSyncManager initialized")
    
    async def start_sync(self, operation: SyncOperation) -> str:
        """Start data synchronization operation"""
        self.active_syncs[operation.sync_id] = operation
        
        # Start sync task
        asyncio.create_task(self._execute_sync(operation))
        
        self.logger.info(f"Started sync operation {operation.sync_id}: {operation.data_type}")
        return operation.sync_id
    
    async def _execute_sync(self, operation: SyncOperation):
        """Execute data synchronization"""
        try:
            if operation.strategy == DataSyncStrategy.SYNCHRONOUS:
                await self._sync_synchronous(operation)
            elif operation.strategy == DataSyncStrategy.ASYNCHRONOUS:
                await self._sync_asynchronous(operation)
            elif operation.strategy == DataSyncStrategy.EVENTUAL_CONSISTENCY:
                await self._sync_eventual_consistency(operation)
            elif operation.strategy == DataSyncStrategy.CONFLICT_RESOLUTION:
                await self._sync_with_conflict_resolution(operation)
            
            operation.status = "completed"
            operation.progress = 100.0
            
        except Exception as e:
            operation.status = "failed"
            self.logger.error(f"Sync operation {operation.sync_id} failed: {e}")
        
        finally:
            # Move to history
            if operation.sync_id in self.active_syncs:
                del self.active_syncs[operation.sync_id]
            
            self.sync_history.append(operation)
            
            # Cleanup old history
            if len(self.sync_history) > 1000:
                self.sync_history = self.sync_history[-1000:]
    
    async def _sync_synchronous(self, operation: SyncOperation):
        """Synchronous data synchronization"""
        self.logger.info(f"Executing synchronous sync for {operation.data_type}")
        
        # Implement synchronous replication logic
        # This would involve real-time data replication
        for i, target_region in enumerate(operation.target_regions):
            # Simulate sync progress
            await asyncio.sleep(1)
            operation.progress = ((i + 1) / len(operation.target_regions)) * 100
    
    async def _sync_asynchronous(self, operation: SyncOperation):
        """Asynchronous data synchronization"""
        self.logger.info(f"Executing asynchronous sync for {operation.data_type}")
        
        # Implement async replication with queues
        tasks = []
        for target_region in operation.target_regions:
            task = asyncio.create_task(self._replicate_to_region(operation, target_region))
            tasks.append(task)
        
        # Wait for all replications to complete
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _replicate_to_region(self, operation: SyncOperation, target_region: str):
        """Replicate data to specific region"""
        # Implement actual data replication logic
        await asyncio.sleep(2)  # Simulate replication time
        self.logger.debug(f"Replicated {operation.data_type} to {target_region}")


class MultiRegionManager:
    """
    Comprehensive multi-region deployment and coordination manager
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Regional configuration
        self.regions: Dict[str, Region] = {}
        
        # Components
        self.latency_monitor = LatencyMonitor(config.get('latency_monitoring', {}))
        self.geo_router = GeographicRouter(config.get('geographic_routing', {}))
        self.data_sync_manager = DataSyncManager(config.get('data_sync', {}))
        
        # Deployment tracking
        self.active_deployments: Dict[str, DeploymentJob] = {}
        self.deployment_history: List[DeploymentJob] = []
        
        # AWS clients for multi-region operations
        self._init_aws_clients()
        
        # Monitoring and coordination
        self.monitoring_tasks: List[asyncio.Task] = []
        
    def _init_aws_clients(self):
        """Initialize AWS clients for different regions"""
        self.aws_clients = {}
        
        for region_id, region_config in self.config.get('regions', {}).items():
            aws_region = region_config.get('aws_region')
            if aws_region:
                self.aws_clients[region_id] = {
                    'ec2': boto3.client('ec2', region_name=aws_region),
                    'ecs': boto3.client('ecs', region_name=aws_region),
                    'rds': boto3.client('rds', region_name=aws_region),
                    's3': boto3.client('s3', region_name=aws_region),
                    'route53': boto3.client('route53', region_name=aws_region),
                    'cloudformation': boto3.client('cloudformation', region_name=aws_region)
                }
    
    async def initialize(self):
        """Initialize multi-region manager"""
        # Load region configurations
        await self._load_regions()
        
        # Initialize components
        await self.data_sync_manager.initialize()
        
        # Start monitoring
        await self._start_monitoring()
        
        self.logger.info(f"MultiRegionManager initialized with {len(self.regions)} regions")
    
    async def _load_regions(self):
        """Load region configurations"""
        region_configs = self.config.get('regions', {})
        
        for region_id, config in region_configs.items():
            region = Region(
                region_id=region_id,
                name=config.get('name', region_id),
                aws_region=config.get('aws_region'),
                status=RegionStatus(config.get('status', 'active')),
                priority=config.get('priority', 1),
                capacity=config.get('capacity', 1000),
                compliance_zones=config.get('compliance_zones', []),
                data_residency_rules=config.get('data_residency_rules', {}),
                endpoints=config.get('endpoints', {})
            )
            
            self.regions[region_id] = region
    
    async def _start_monitoring(self):
        """Start regional monitoring"""
        # Start latency monitoring
        latency_tasks = await self.latency_monitor.start_monitoring(self.regions)
        self.monitoring_tasks.extend(latency_tasks)
        
        # Start health monitoring
        health_task = asyncio.create_task(self._monitor_regional_health())
        self.monitoring_tasks.append(health_task)
        
        # Start load monitoring
        load_task = asyncio.create_task(self._monitor_regional_load())
        self.monitoring_tasks.append(load_task)
    
    async def _monitor_regional_health(self):
        """Monitor health of all regions"""
        while True:
            try:
                for region in self.regions.values():
                    health_status = await self._check_region_health(region)
                    
                    if health_status != region.status:
                        old_status = region.status
                        region.status = health_status
                        region.last_health_check = datetime.utcnow()
                        
                        self.logger.info(f"Region {region.region_id} status changed: {old_status.value} -> {health_status.value}")
                        
                        # Trigger regional failover if needed
                        if health_status == RegionStatus.OFFLINE:
                            await self._handle_region_failure(region)
                
                await asyncio.sleep(self.config.get('health_check_interval', 60))
                
            except Exception as e:
                self.logger.error(f"Regional health monitoring error: {e}")
                await asyncio.sleep(60)
    
    async def _check_region_health(self, region: Region) -> RegionStatus:
        """Check health of specific region"""
        try:
            # Check primary endpoint
            if 'health' in region.endpoints:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        region.endpoints['health'], 
                        timeout=aiohttp.ClientTimeout(total=30)
                    ) as response:
                        if response.status == 200:
                            return RegionStatus.ACTIVE
                        else:
                            return RegionStatus.DEGRADED
            
            # Check AWS services if no custom endpoint
            if region.aws_region and region.region_id in self.aws_clients:
                ec2_client = self.aws_clients[region.region_id]['ec2']
                # Simple service availability check
                ec2_client.describe_availability_zones()
                return RegionStatus.ACTIVE
            
            return RegionStatus.UNKNOWN
            
        except Exception as e:
            self.logger.error(f"Health check failed for region {region.region_id}: {e}")
            return RegionStatus.OFFLINE
    
    async def deploy_multi_region(self, deployment_config: Dict[str, Any]) -> str:
        """Deploy application to multiple regions"""
        job_id = f"deploy_{int(time.time())}"
        
        deployment_job = DeploymentJob(
            job_id=job_id,
            target_regions=deployment_config['target_regions'],
            strategy=DeploymentStrategy(deployment_config.get('strategy', 'rolling')),
            version=deployment_config['version'],
            start_time=datetime.utcnow(),
            estimated_duration=timedelta(minutes=deployment_config.get('estimated_minutes', 30)),
            metadata=deployment_config.get('metadata', {})
        )
        
        self.active_deployments[job_id] = deployment_job
        
        # Start deployment task
        asyncio.create_task(self._execute_deployment(deployment_job))
        
        self.logger.info(f"Started multi-region deployment {job_id} to {len(deployment_job.target_regions)} regions")
        
        return job_id
    
    async def _execute_deployment(self, job: DeploymentJob):
        """Execute multi-region deployment"""
        try:
            if job.strategy == DeploymentStrategy.ROLLING:
                await self._deploy_rolling(job)
            elif job.strategy == DeploymentStrategy.BLUE_GREEN:
                await self._deploy_blue_green(job)
            elif job.strategy == DeploymentStrategy.CANARY:
                await self._deploy_canary(job)
            elif job.strategy == DeploymentStrategy.ACTIVE_ACTIVE:
                await self._deploy_active_active(job)
            else:
                await self._deploy_sequential(job)
            
            self.logger.info(f"Deployment {job.job_id} completed successfully")
            
        except Exception as e:
            self.logger.error(f"Deployment {job.job_id} failed: {e}")
            job.rollback_triggered = True
            await self._rollback_deployment(job)
        
        finally:
            # Move to history
            if job.job_id in self.active_deployments:
                del self.active_deployments[job.job_id]
            
            self.deployment_history.append(job)
    
    async def _deploy_rolling(self, job: DeploymentJob):
        """Rolling deployment across regions"""
        job.current_phase = "rolling_deployment"
        
        for region_id in job.target_regions:
            if region_id not in self.regions:
                job.failed_regions.append(region_id)
                continue
            
            try:
                self.logger.info(f"Deploying to region {region_id}")
                await self._deploy_to_region(region_id, job.version, job.metadata)
                job.completed_regions.append(region_id)
                
                # Wait between deployments for validation
                await asyncio.sleep(30)
                
            except Exception as e:
                self.logger.error(f"Deployment to region {region_id} failed: {e}")
                job.failed_regions.append(region_id)
                
                # Stop rolling deployment on failure
                if len(job.failed_regions) > len(job.target_regions) * 0.2:  # >20% failure
                    raise Exception(f"Rolling deployment stopped due to high failure rate")
    
    async def _deploy_to_region(self, region_id: str, version: str, metadata: Dict[str, Any]):
        """Deploy to specific region"""
        region = self.regions[region_id]
        
        # Check region availability
        if region.status != RegionStatus.ACTIVE:
            raise Exception(f"Region {region_id} is not active (status: {region.status.value})")
        
        # Execute deployment based on infrastructure
        if region.aws_region and region_id in self.aws_clients:
            await self._deploy_aws_region(region_id, version, metadata)
        else:
            await self._deploy_custom_region(region_id, version, metadata)
        
        self.logger.info(f"Successfully deployed version {version} to region {region_id}")
    
    async def _deploy_aws_region(self, region_id: str, version: str, metadata: Dict[str, Any]):
        """Deploy to AWS region using CloudFormation/ECS"""
        aws_clients = self.aws_clients[region_id]
        
        # Update ECS service with new task definition
        ecs_client = aws_clients['ecs']
        
        # This is a simplified example - actual implementation would be more complex
        cluster_name = metadata.get('ecs_cluster', 'financial-planning-cluster')
        service_name = metadata.get('ecs_service', 'financial-planning-service')
        
        # Update service (simplified)
        # In practice, you'd create new task definition, then update service
        self.logger.info(f"Updating ECS service {service_name} in cluster {cluster_name}")
        
        # Simulate deployment time
        await asyncio.sleep(5)
    
    async def route_request(self, client_ip: str, request_context: Dict[str, Any]) -> Optional[Region]:
        """Route request to optimal region"""
        # Get available regions
        available_regions = [
            region for region in self.regions.values()
            if region.status == RegionStatus.ACTIVE
        ]
        
        if not available_regions:
            self.logger.error("No available regions for request routing")
            return None
        
        # Check compliance requirements
        compliance_zone = request_context.get('compliance_zone')
        if compliance_zone:
            compliant_regions = [
                region for region in available_regions
                if compliance_zone in region.compliance_zones
            ]
            if compliant_regions:
                available_regions = compliant_regions
        
        # Get latency matrix
        latency_matrix = self.latency_monitor.get_latency_matrix()
        
        # Use geographic router
        optimal_region = self.geo_router.get_optimal_region(
            client_ip, available_regions, latency_matrix
        )
        
        if optimal_region:
            self.logger.debug(f"Routed request from {client_ip} to region {optimal_region.region_id}")
        
        return optimal_region
    
    async def sync_data_across_regions(self, data_type: str, source_region: str, 
                                     target_regions: List[str], 
                                     strategy: DataSyncStrategy) -> str:
        """Synchronize data across regions"""
        sync_id = f"sync_{data_type}_{int(time.time())}"
        
        sync_operation = SyncOperation(
            sync_id=sync_id,
            source_region=source_region,
            target_regions=target_regions,
            data_type=data_type,
            strategy=strategy,
            priority=1,
            start_time=datetime.utcnow()
        )
        
        await self.data_sync_manager.start_sync(sync_operation)
        
        return sync_id
    
    async def _handle_region_failure(self, failed_region: Region):
        """Handle region failure"""
        self.logger.warning(f"Handling failure for region {failed_region.region_id}")
        
        # Update DNS to remove failed region
        await self._update_dns_for_region_failure(failed_region.region_id)
        
        # Trigger data sync from other regions if needed
        active_regions = [
            region.region_id for region in self.regions.values()
            if region.status == RegionStatus.ACTIVE and region.region_id != failed_region.region_id
        ]
        
        if active_regions:
            # Sync critical data from nearest active region
            await self.sync_data_across_regions(
                'critical_data',
                active_regions[0],
                [failed_region.region_id],
                DataSyncStrategy.ASYNCHRONOUS
            )
    
    async def get_deployment_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get deployment status"""
        job = self.active_deployments.get(job_id)
        if not job:
            # Check history
            for historical_job in self.deployment_history:
                if historical_job.job_id == job_id:
                    job = historical_job
                    break
        
        if not job:
            return None
        
        return {
            'job_id': job.job_id,
            'strategy': job.strategy.value,
            'current_phase': job.current_phase,
            'progress': len(job.completed_regions) / len(job.target_regions) * 100,
            'completed_regions': job.completed_regions,
            'failed_regions': job.failed_regions,
            'rollback_triggered': job.rollback_triggered,
            'start_time': job.start_time.isoformat(),
            'estimated_completion': (job.start_time + job.estimated_duration).isoformat()
        }
    
    async def get_multi_region_status(self) -> Dict[str, Any]:
        """Get comprehensive multi-region status"""
        # Regional status
        regional_status = {}
        for region_id, region in self.regions.items():
            regional_status[region_id] = {
                'status': region.status.value,
                'priority': region.priority,
                'load': f"{region.current_load}/{region.capacity}",
                'latency_ms': region.latency_ms,
                'last_health_check': region.last_health_check.isoformat() if region.last_health_check else None
            }
        
        # Active deployments
        active_deployments = {
            job_id: {
                'strategy': job.strategy.value,
                'progress': len(job.completed_regions) / len(job.target_regions) * 100,
                'current_phase': job.current_phase
            }
            for job_id, job in self.active_deployments.items()
        }
        
        # Sync operations
        active_syncs = {
            sync_id: {
                'data_type': sync.data_type,
                'strategy': sync.strategy.value,
                'progress': sync.progress,
                'status': sync.status
            }
            for sync_id, sync in self.data_sync_manager.active_syncs.items()
        }
        
        return {
            'regions': regional_status,
            'active_deployments': active_deployments,
            'active_syncs': active_syncs,
            'latency_matrix': self.latency_monitor.get_latency_matrix(),
            'total_regions': len(self.regions),
            'healthy_regions': len([r for r in self.regions.values() if r.status == RegionStatus.ACTIVE])
        }


# Example usage and configuration
if __name__ == "__main__":
    # Configuration example
    config = {
        'regions': {
            'us-east-1': {
                'name': 'US East (Virginia)',
                'aws_region': 'us-east-1',
                'status': 'active',
                'priority': 1,
                'capacity': 1000,
                'compliance_zones': ['US', 'GLOBAL'],
                'endpoints': {
                    'health': 'https://api-us-east-1.financial-planning.com/health',
                    'api': 'https://api-us-east-1.financial-planning.com'
                }
            },
            'eu-west-1': {
                'name': 'EU West (Ireland)',
                'aws_region': 'eu-west-1',
                'status': 'active',
                'priority': 2,
                'capacity': 800,
                'compliance_zones': ['EU', 'GDPR'],
                'data_residency_rules': {'user_data': 'must_stay_in_eu'},
                'endpoints': {
                    'health': 'https://api-eu-west-1.financial-planning.com/health',
                    'api': 'https://api-eu-west-1.financial-planning.com'
                }
            }
        },
        'latency_monitoring': {
            'latency_check_interval': 60
        },
        'geographic_routing': {
            'geoip_db_path': '/usr/local/share/GeoIP/GeoLite2-City.mmdb',
            'country_mappings': {
                'US': 'us-east-1',
                'CA': 'us-east-1',
                'GB': 'eu-west-1',
                'DE': 'eu-west-1'
            }
        },
        'data_sync': {
            'redis': {
                'host': 'localhost',
                'port': 6379
            }
        }
    }
    
    async def example_multi_region_deployment():
        # Initialize manager
        mr_manager = MultiRegionManager(config)
        await mr_manager.initialize()
        
        # Deploy to multiple regions
        deployment_config = {
            'target_regions': ['us-east-1', 'eu-west-1'],
            'strategy': 'rolling',
            'version': 'v1.2.3',
            'estimated_minutes': 15,
            'metadata': {
                'ecs_cluster': 'financial-planning',
                'ecs_service': 'api-service'
            }
        }
        
        job_id = await mr_manager.deploy_multi_region(deployment_config)
        print(f"Started deployment: {job_id}")
        
        # Monitor deployment
        while True:
            status = await mr_manager.get_deployment_status(job_id)
            if not status or status['progress'] >= 100:
                break
            
            print(f"Deployment progress: {status['progress']:.1f}%")
            await asyncio.sleep(10)
        
        # Get overall status
        overall_status = await mr_manager.get_multi_region_status()
        print(f"Healthy regions: {overall_status['healthy_regions']}/{overall_status['total_regions']}")
    
    # Run example
    # asyncio.run(example_multi_region_deployment())