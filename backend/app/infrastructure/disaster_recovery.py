"""
Disaster Recovery Manager for Financial Planning System

This module provides comprehensive disaster recovery capabilities including:
- Damage assessment and impact analysis
- Full and partial failover strategies
- Data restoration from backups
- Recovery validation and verification
- Multi-region deployment coordination
- Business continuity management
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple, Any
import json
import hashlib
import boto3
import redis
import psycopg2
from concurrent.futures import ThreadPoolExecutor, as_completed
import aiohttp
import yaml


class DisasterType(Enum):
    """Types of disaster scenarios"""
    SYSTEM_FAILURE = "system_failure"
    DATA_CORRUPTION = "data_corruption"
    SECURITY_BREACH = "security_breach"
    NATURAL_DISASTER = "natural_disaster"
    NETWORK_OUTAGE = "network_outage"
    HARDWARE_FAILURE = "hardware_failure"
    SOFTWARE_BUG = "software_bug"
    HUMAN_ERROR = "human_error"


class SeverityLevel(Enum):
    """Disaster severity levels"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4
    CATASTROPHIC = 5


class RecoveryPhase(Enum):
    """Recovery process phases"""
    ASSESSMENT = "assessment"
    ISOLATION = "isolation"
    RESTORATION = "restoration"
    VALIDATION = "validation"
    MONITORING = "monitoring"
    COMPLETE = "complete"


class FailoverStrategy(Enum):
    """Failover strategy types"""
    FULL_FAILOVER = "full_failover"
    PARTIAL_FAILOVER = "partial_failover"
    ROLLING_FAILOVER = "rolling_failover"
    BLUE_GREEN = "blue_green"
    CANARY = "canary"


@dataclass
class DamageAssessment:
    """Damage assessment results"""
    disaster_id: str
    disaster_type: DisasterType
    severity: SeverityLevel
    affected_systems: List[str]
    affected_data: List[str]
    estimated_downtime: timedelta
    business_impact: str
    recovery_complexity: int  # 1-10 scale
    recommended_strategy: FailoverStrategy
    assessment_time: datetime = field(default_factory=datetime.utcnow)


@dataclass
class RecoveryPlan:
    """Disaster recovery plan"""
    plan_id: str
    disaster_type: DisasterType
    severity: SeverityLevel
    strategy: FailoverStrategy
    steps: List[Dict[str, Any]]
    estimated_rto: timedelta  # Recovery Time Objective
    estimated_rpo: timedelta  # Recovery Point Objective
    required_resources: List[str]
    validation_criteria: List[str]
    rollback_plan: List[Dict[str, Any]]


@dataclass
class RecoveryStatus:
    """Recovery operation status"""
    recovery_id: str
    plan_id: str
    phase: RecoveryPhase
    start_time: datetime
    current_step: int
    total_steps: int
    progress_percentage: float
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    completed_validations: List[str] = field(default_factory=list)


class DisasterRecoveryManager:
    """
    Comprehensive disaster recovery management system
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Recovery tracking
        self.active_recoveries: Dict[str, RecoveryStatus] = {}
        self.recovery_plans: Dict[str, RecoveryPlan] = {}
        self.damage_assessments: Dict[str, DamageAssessment] = {}
        
        # System monitoring
        self.system_health: Dict[str, bool] = {}
        self.last_health_check: Dict[str, datetime] = {}
        
        # Initialize connections
        self._init_connections()
        
        # Load recovery plans
        self._load_recovery_plans()
        
        # Start monitoring
        asyncio.create_task(self._continuous_monitoring())
    
    def _init_connections(self):
        """Initialize external service connections"""
        try:
            # AWS clients for multi-region operations
            self.s3_client = boto3.client('s3', region_name=self.config.get('primary_region', 'us-east-1'))
            self.ec2_client = boto3.client('ec2', region_name=self.config.get('primary_region', 'us-east-1'))
            self.rds_client = boto3.client('rds', region_name=self.config.get('primary_region', 'us-east-1'))
            
            # Redis for coordination
            redis_config = self.config.get('redis', {})
            self.redis_client = redis.Redis(
                host=redis_config.get('host', 'localhost'),
                port=redis_config.get('port', 6379),
                db=redis_config.get('db', 0),
                decode_responses=True
            )
            
            # Thread pool for parallel operations
            self.executor = ThreadPoolExecutor(max_workers=self.config.get('max_workers', 10))
            
        except Exception as e:
            self.logger.error(f"Failed to initialize connections: {e}")
            raise
    
    def _load_recovery_plans(self):
        """Load predefined recovery plans"""
        default_plans = {
            'system_failure_critical': RecoveryPlan(
                plan_id='sys_fail_crit_001',
                disaster_type=DisasterType.SYSTEM_FAILURE,
                severity=SeverityLevel.CRITICAL,
                strategy=FailoverStrategy.FULL_FAILOVER,
                steps=[
                    {'action': 'assess_damage', 'timeout': 300},
                    {'action': 'isolate_affected_systems', 'timeout': 180},
                    {'action': 'initiate_full_failover', 'timeout': 600},
                    {'action': 'restore_data', 'timeout': 1800},
                    {'action': 'validate_recovery', 'timeout': 900},
                    {'action': 'monitor_stability', 'timeout': 300}
                ],
                estimated_rto=timedelta(hours=1),
                estimated_rpo=timedelta(minutes=15),
                required_resources=['backup_region', 'standby_database', 'load_balancer'],
                validation_criteria=['api_health', 'data_integrity', 'user_authentication'],
                rollback_plan=[
                    {'action': 'switch_back_primary', 'timeout': 300},
                    {'action': 'verify_rollback', 'timeout': 180}
                ]
            ),
            'data_corruption_high': RecoveryPlan(
                plan_id='data_corr_high_001',
                disaster_type=DisasterType.DATA_CORRUPTION,
                severity=SeverityLevel.HIGH,
                strategy=FailoverStrategy.PARTIAL_FAILOVER,
                steps=[
                    {'action': 'identify_corrupted_data', 'timeout': 600},
                    {'action': 'isolate_affected_tables', 'timeout': 300},
                    {'action': 'restore_from_backup', 'timeout': 2400},
                    {'action': 'validate_data_integrity', 'timeout': 1200},
                    {'action': 'merge_recent_changes', 'timeout': 900}
                ],
                estimated_rto=timedelta(hours=2),
                estimated_rpo=timedelta(hours=1),
                required_resources=['point_in_time_backup', 'data_validation_tools'],
                validation_criteria=['data_consistency', 'referential_integrity'],
                rollback_plan=[
                    {'action': 'restore_previous_backup', 'timeout': 1800}
                ]
            )
        }
        
        self.recovery_plans.update(default_plans)
    
    async def assess_damage(self, incident_data: Dict[str, Any]) -> DamageAssessment:
        """
        Comprehensive damage assessment
        
        Args:
            incident_data: Information about the incident
            
        Returns:
            DamageAssessment with detailed analysis
        """
        disaster_id = incident_data.get('id', f"disaster_{int(time.time())}")
        
        self.logger.info(f"Starting damage assessment for disaster {disaster_id}")
        
        # Determine disaster type
        disaster_type = DisasterType(incident_data.get('type', 'system_failure'))
        
        # Assess affected systems
        affected_systems = await self._assess_affected_systems(incident_data)
        
        # Assess data impact
        affected_data = await self._assess_data_impact(incident_data)
        
        # Calculate severity
        severity = await self._calculate_severity(affected_systems, affected_data, incident_data)
        
        # Estimate recovery metrics
        estimated_downtime = await self._estimate_downtime(severity, affected_systems)
        recovery_complexity = await self._calculate_recovery_complexity(affected_systems, affected_data)
        
        # Determine business impact
        business_impact = await self._assess_business_impact(affected_systems, severity)
        
        # Recommend strategy
        recommended_strategy = await self._recommend_failover_strategy(
            severity, affected_systems, recovery_complexity
        )
        
        assessment = DamageAssessment(
            disaster_id=disaster_id,
            disaster_type=disaster_type,
            severity=severity,
            affected_systems=affected_systems,
            affected_data=affected_data,
            estimated_downtime=estimated_downtime,
            business_impact=business_impact,
            recovery_complexity=recovery_complexity,
            recommended_strategy=recommended_strategy
        )
        
        self.damage_assessments[disaster_id] = assessment
        
        # Store assessment for audit
        await self._store_assessment(assessment)
        
        self.logger.info(f"Damage assessment complete for {disaster_id}: {severity.name} severity")
        
        return assessment
    
    async def _assess_affected_systems(self, incident_data: Dict[str, Any]) -> List[str]:
        """Identify affected systems"""
        affected_systems = []
        
        # Check primary systems
        systems_to_check = [
            'web_api',
            'database_primary',
            'authentication_service',
            'portfolio_engine',
            'market_data_feed',
            'notification_service',
            'backup_systems',
            'monitoring'
        ]
        
        # Parallel health checks
        tasks = []
        for system in systems_to_check:
            task = asyncio.create_task(self._check_system_health(system))
            tasks.append((system, task))
        
        for system, task in tasks:
            try:
                is_healthy = await asyncio.wait_for(task, timeout=30)
                if not is_healthy:
                    affected_systems.append(system)
            except asyncio.TimeoutError:
                affected_systems.append(system)
                self.logger.warning(f"Health check timeout for system: {system}")
            except Exception as e:
                affected_systems.append(system)
                self.logger.error(f"Health check failed for {system}: {e}")
        
        return affected_systems
    
    async def _assess_data_impact(self, incident_data: Dict[str, Any]) -> List[str]:
        """Assess data corruption or loss"""
        affected_data = []
        
        # Data integrity checks
        data_sources = [
            'user_accounts',
            'portfolio_data',
            'transaction_history',
            'market_data',
            'financial_models',
            'user_preferences',
            'audit_logs'
        ]
        
        for data_source in data_sources:
            try:
                integrity_check = await self._verify_data_integrity(data_source)
                if not integrity_check:
                    affected_data.append(data_source)
            except Exception as e:
                affected_data.append(data_source)
                self.logger.error(f"Data integrity check failed for {data_source}: {e}")
        
        return affected_data
    
    async def _calculate_severity(self, affected_systems: List[str], 
                                 affected_data: List[str], 
                                 incident_data: Dict[str, Any]) -> SeverityLevel:
        """Calculate disaster severity"""
        severity_score = 0
        
        # System impact scoring
        critical_systems = {'database_primary', 'web_api', 'authentication_service'}
        important_systems = {'portfolio_engine', 'market_data_feed'}
        
        for system in affected_systems:
            if system in critical_systems:
                severity_score += 3
            elif system in important_systems:
                severity_score += 2
            else:
                severity_score += 1
        
        # Data impact scoring
        critical_data = {'user_accounts', 'portfolio_data', 'transaction_history'}
        for data in affected_data:
            if data in critical_data:
                severity_score += 2
            else:
                severity_score += 1
        
        # External factors
        user_count = incident_data.get('affected_users', 0)
        if user_count > 1000:
            severity_score += 2
        elif user_count > 100:
            severity_score += 1
        
        # Map score to severity level
        if severity_score >= 15:
            return SeverityLevel.CATASTROPHIC
        elif severity_score >= 10:
            return SeverityLevel.CRITICAL
        elif severity_score >= 6:
            return SeverityLevel.HIGH
        elif severity_score >= 3:
            return SeverityLevel.MEDIUM
        else:
            return SeverityLevel.LOW
    
    async def _estimate_downtime(self, severity: SeverityLevel, affected_systems: List[str]) -> timedelta:
        """Estimate recovery time"""
        base_times = {
            SeverityLevel.LOW: timedelta(minutes=30),
            SeverityLevel.MEDIUM: timedelta(hours=1),
            SeverityLevel.HIGH: timedelta(hours=2),
            SeverityLevel.CRITICAL: timedelta(hours=4),
            SeverityLevel.CATASTROPHIC: timedelta(hours=8)
        }
        
        base_time = base_times[severity]
        
        # Adjust for system complexity
        complexity_multiplier = 1.0
        if 'database_primary' in affected_systems:
            complexity_multiplier += 0.5
        if len(affected_systems) > 5:
            complexity_multiplier += 0.3
        
        return timedelta(seconds=base_time.total_seconds() * complexity_multiplier)
    
    async def initiate_failover(self, assessment: DamageAssessment) -> str:
        """
        Initiate disaster recovery based on assessment
        
        Args:
            assessment: Damage assessment results
            
        Returns:
            Recovery operation ID
        """
        recovery_id = f"recovery_{assessment.disaster_id}_{int(time.time())}"
        
        # Select recovery plan
        plan = await self._select_recovery_plan(assessment)
        if not plan:
            raise ValueError(f"No recovery plan found for {assessment.disaster_type.value}")
        
        # Create recovery status
        status = RecoveryStatus(
            recovery_id=recovery_id,
            plan_id=plan.plan_id,
            phase=RecoveryPhase.ASSESSMENT,
            start_time=datetime.utcnow(),
            current_step=0,
            total_steps=len(plan.steps),
            progress_percentage=0.0
        )
        
        self.active_recoveries[recovery_id] = status
        
        # Start recovery process
        asyncio.create_task(self._execute_recovery_plan(recovery_id, plan, assessment))
        
        self.logger.info(f"Initiated {assessment.recommended_strategy.value} for disaster {assessment.disaster_id}")
        
        return recovery_id
    
    async def _select_recovery_plan(self, assessment: DamageAssessment) -> Optional[RecoveryPlan]:
        """Select appropriate recovery plan"""
        # Look for specific plan
        plan_key = f"{assessment.disaster_type.value}_{assessment.severity.name.lower()}"
        
        if plan_key in self.recovery_plans:
            return self.recovery_plans[plan_key]
        
        # Fallback to generic plans
        for plan in self.recovery_plans.values():
            if (plan.disaster_type == assessment.disaster_type and 
                plan.severity == assessment.severity):
                return plan
        
        # Create dynamic plan if none exists
        return await self._create_dynamic_plan(assessment)
    
    async def _execute_recovery_plan(self, recovery_id: str, plan: RecoveryPlan, assessment: DamageAssessment):
        """Execute recovery plan steps"""
        status = self.active_recoveries[recovery_id]
        
        try:
            for i, step in enumerate(plan.steps):
                status.current_step = i + 1
                status.progress_percentage = (i / len(plan.steps)) * 100
                
                self.logger.info(f"Executing step {i+1}/{len(plan.steps)}: {step['action']}")
                
                # Execute step with timeout
                try:
                    await asyncio.wait_for(
                        self._execute_recovery_step(step, assessment),
                        timeout=step.get('timeout', 600)
                    )
                except asyncio.TimeoutError:
                    error_msg = f"Step {step['action']} timed out"
                    status.errors.append(error_msg)
                    self.logger.error(error_msg)
                    
                    # Decide whether to continue or abort
                    if step.get('critical', True):
                        raise Exception(error_msg)
                
                # Update progress
                await self._update_recovery_status(recovery_id)
            
            # Final validation
            status.phase = RecoveryPhase.VALIDATION
            await self._validate_recovery(recovery_id, plan)
            
            status.phase = RecoveryPhase.COMPLETE
            status.progress_percentage = 100.0
            
            self.logger.info(f"Recovery {recovery_id} completed successfully")
            
        except Exception as e:
            status.errors.append(str(e))
            self.logger.error(f"Recovery {recovery_id} failed: {e}")
            
            # Attempt rollback if available
            if plan.rollback_plan:
                await self._execute_rollback(recovery_id, plan)
    
    async def _execute_recovery_step(self, step: Dict[str, Any], assessment: DamageAssessment):
        """Execute individual recovery step"""
        action = step['action']
        
        if action == 'assess_damage':
            # Already done, just log
            self.logger.info("Damage assessment completed")
            
        elif action == 'isolate_affected_systems':
            await self._isolate_systems(assessment.affected_systems)
            
        elif action == 'initiate_full_failover':
            await self._execute_full_failover(assessment)
            
        elif action == 'initiate_partial_failover':
            await self._execute_partial_failover(assessment)
            
        elif action == 'restore_data':
            await self._restore_data_from_backup(assessment.affected_data)
            
        elif action == 'validate_recovery':
            await self._validate_system_recovery(assessment)
            
        elif action == 'monitor_stability':
            await self._monitor_post_recovery_stability()
            
        else:
            self.logger.warning(f"Unknown recovery action: {action}")
    
    async def _execute_full_failover(self, assessment: DamageAssessment):
        """Execute full system failover"""
        self.logger.info("Starting full failover to backup region")
        
        # Step 1: Update DNS to point to backup region
        await self._update_dns_routing()
        
        # Step 2: Activate standby database
        await self._activate_standby_database()
        
        # Step 3: Start backup application servers
        await self._start_backup_servers()
        
        # Step 4: Restore load balancer configuration
        await self._configure_backup_load_balancer()
        
        # Step 5: Verify all services are operational
        await self._verify_backup_services()
        
        self.logger.info("Full failover completed")
    
    async def _execute_partial_failover(self, assessment: DamageAssessment):
        """Execute partial system failover"""
        self.logger.info("Starting partial failover for affected systems")
        
        for system in assessment.affected_systems:
            if system == 'database_primary':
                await self._failover_database()
            elif system == 'web_api':
                await self._failover_api_servers()
            elif system == 'market_data_feed':
                await self._failover_market_data()
            else:
                await self._failover_generic_service(system)
        
        self.logger.info("Partial failover completed")
    
    async def restore_from_backup(self, backup_id: str, target_timestamp: Optional[datetime] = None) -> bool:
        """
        Restore system from backup
        
        Args:
            backup_id: Backup identifier
            target_timestamp: Point-in-time recovery target
            
        Returns:
            True if restoration successful
        """
        self.logger.info(f"Starting restoration from backup {backup_id}")
        
        try:
            # Step 1: Validate backup integrity
            if not await self._validate_backup_integrity(backup_id):
                raise Exception(f"Backup {backup_id} failed integrity check")
            
            # Step 2: Prepare restoration environment
            await self._prepare_restoration_environment()
            
            # Step 3: Restore database
            await self._restore_database_backup(backup_id, target_timestamp)
            
            # Step 4: Restore application data
            await self._restore_application_data(backup_id)
            
            # Step 5: Restore configuration files
            await self._restore_configurations(backup_id)
            
            # Step 6: Validate restoration
            if await self._validate_restoration():
                self.logger.info(f"Restoration from backup {backup_id} completed successfully")
                return True
            else:
                raise Exception("Restoration validation failed")
                
        except Exception as e:
            self.logger.error(f"Restoration failed: {e}")
            return False
    
    async def validate_recovery(self, recovery_id: str) -> Dict[str, Any]:
        """
        Comprehensive recovery validation
        
        Args:
            recovery_id: Recovery operation ID
            
        Returns:
            Validation results
        """
        if recovery_id not in self.active_recoveries:
            raise ValueError(f"Unknown recovery ID: {recovery_id}")
        
        status = self.active_recoveries[recovery_id]
        results = {
            'recovery_id': recovery_id,
            'validation_time': datetime.utcnow(),
            'passed_checks': [],
            'failed_checks': [],
            'warnings': [],
            'overall_status': 'unknown'
        }
        
        # System health validation
        system_health = await self._validate_system_health()
        if system_health['all_healthy']:
            results['passed_checks'].append('system_health')
        else:
            results['failed_checks'].append('system_health')
            results['warnings'].extend(system_health['issues'])
        
        # Data integrity validation
        data_integrity = await self._validate_data_integrity_comprehensive()
        if data_integrity['all_valid']:
            results['passed_checks'].append('data_integrity')
        else:
            results['failed_checks'].append('data_integrity')
            results['warnings'].extend(data_integrity['issues'])
        
        # Performance validation
        performance = await self._validate_system_performance()
        if performance['acceptable']:
            results['passed_checks'].append('performance')
        else:
            results['failed_checks'].append('performance')
            results['warnings'].extend(performance['issues'])
        
        # Security validation
        security = await self._validate_security_posture()
        if security['secure']:
            results['passed_checks'].append('security')
        else:
            results['failed_checks'].append('security')
            results['warnings'].extend(security['issues'])
        
        # Determine overall status
        if not results['failed_checks']:
            results['overall_status'] = 'passed'
            status.phase = RecoveryPhase.COMPLETE
        elif len(results['failed_checks']) < len(results['passed_checks']):
            results['overall_status'] = 'passed_with_warnings'
            status.phase = RecoveryPhase.MONITORING
        else:
            results['overall_status'] = 'failed'
        
        # Update status
        status.completed_validations = results['passed_checks']
        
        self.logger.info(f"Recovery validation {results['overall_status']} for {recovery_id}")
        
        return results
    
    async def get_recovery_status(self, recovery_id: str) -> Optional[RecoveryStatus]:
        """Get current recovery status"""
        return self.active_recoveries.get(recovery_id)
    
    async def list_active_recoveries(self) -> List[RecoveryStatus]:
        """List all active recovery operations"""
        return list(self.active_recoveries.values())
    
    async def _continuous_monitoring(self):
        """Continuous system monitoring for early disaster detection"""
        while True:
            try:
                # Monitor system health
                await self._monitor_system_health()
                
                # Check for anomalies
                await self._detect_anomalies()
                
                # Update health status
                await self._update_health_status()
                
                # Sleep between checks
                await asyncio.sleep(self.config.get('monitoring_interval', 60))
                
            except Exception as e:
                self.logger.error(f"Monitoring error: {e}")
                await asyncio.sleep(60)
    
    async def _check_system_health(self, system: str) -> bool:
        """Check health of individual system"""
        try:
            if system == 'web_api':
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{self.config['api_url']}/health", timeout=10) as response:
                        return response.status == 200
            
            elif system == 'database_primary':
                # Database connection check
                conn = psycopg2.connect(self.config['database_url'])
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
                conn.close()
                return True
            
            elif system == 'redis':
                return self.redis_client.ping()
            
            # Add more system-specific health checks
            return True
            
        except Exception:
            return False
    
    async def _verify_data_integrity(self, data_source: str) -> bool:
        """Verify data integrity for a specific source"""
        try:
            # Implementation depends on data source type
            # This is a placeholder for actual integrity checks
            return True
        except Exception:
            return False
    
    async def _store_assessment(self, assessment: DamageAssessment):
        """Store damage assessment for audit purposes"""
        assessment_data = {
            'disaster_id': assessment.disaster_id,
            'disaster_type': assessment.disaster_type.value,
            'severity': assessment.severity.value,
            'affected_systems': assessment.affected_systems,
            'affected_data': assessment.affected_data,
            'estimated_downtime': assessment.estimated_downtime.total_seconds(),
            'business_impact': assessment.business_impact,
            'recovery_complexity': assessment.recovery_complexity,
            'recommended_strategy': assessment.recommended_strategy.value,
            'assessment_time': assessment.assessment_time.isoformat()
        }
        
        # Store in Redis for immediate access
        await self.redis_client.hset(
            f"disaster_assessment:{assessment.disaster_id}",
            mapping=assessment_data
        )
        
        # Store in S3 for long-term retention
        s3_key = f"disaster_recovery/assessments/{assessment.disaster_id}.json"
        self.s3_client.put_object(
            Bucket=self.config['backup_bucket'],
            Key=s3_key,
            Body=json.dumps(assessment_data, indent=2)
        )
    
    def get_rto_rpo_metrics(self) -> Dict[str, timedelta]:
        """Get current RTO/RPO metrics"""
        return {
            'rto_target': timedelta(hours=4),
            'rpo_target': timedelta(minutes=15),
            'last_backup': self._get_last_backup_time(),
            'estimated_recovery_time': self._estimate_current_recovery_time()
        }


# Example usage and configuration
if __name__ == "__main__":
    # Configuration example
    config = {
        'primary_region': 'us-east-1',
        'backup_region': 'us-west-2',
        'backup_bucket': 'financial-planning-disaster-recovery',
        'redis': {
            'host': 'localhost',
            'port': 6379,
            'db': 0
        },
        'database_url': 'postgresql://user:pass@localhost:5432/financialdb',
        'api_url': 'https://api.financial-planning.com',
        'monitoring_interval': 30,
        'max_workers': 20
    }
    
    # Initialize disaster recovery manager
    dr_manager = DisasterRecoveryManager(config)
    
    # Example disaster scenario
    async def example_disaster_response():
        # Simulate system failure incident
        incident = {
            'id': 'incident_001',
            'type': 'system_failure',
            'affected_users': 1500,
            'description': 'Primary database cluster failure',
            'detected_at': datetime.utcnow()
        }
        
        # Assess damage
        assessment = await dr_manager.assess_damage(incident)
        print(f"Damage assessment: {assessment.severity.name} severity")
        print(f"Recommended strategy: {assessment.recommended_strategy.value}")
        
        # Initiate recovery
        recovery_id = await dr_manager.initiate_failover(assessment)
        print(f"Recovery initiated: {recovery_id}")
        
        # Monitor progress
        while True:
            status = await dr_manager.get_recovery_status(recovery_id)
            if status.phase == RecoveryPhase.COMPLETE:
                break
            
            print(f"Recovery progress: {status.progress_percentage:.1f}%")
            await asyncio.sleep(30)
        
        # Validate recovery
        validation_results = await dr_manager.validate_recovery(recovery_id)
        print(f"Validation status: {validation_results['overall_status']}")
    
    # Run example
    # asyncio.run(example_disaster_response())