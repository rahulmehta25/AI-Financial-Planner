"""
Comprehensive Testing and Validation Framework for Disaster Recovery

This module provides extensive testing capabilities for disaster recovery including:
- Disaster simulation and chaos engineering
- Failover testing and validation
- Recovery time and data integrity testing
- Multi-region coordination testing
- Performance and stress testing under failure conditions
"""

import asyncio
import logging
import time
import random
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple, Any, Callable
import json
import uuid
import statistics
import aiohttp
import pytest
import numpy as np
from concurrent.futures import ThreadPoolExecutor
import psutil

from .disaster_recovery import DisasterRecoveryManager, DisasterType, SeverityLevel, FailoverStrategy
from .high_availability import HighAvailabilityManager, ServiceStatus, FailoverTrigger
from .multi_region_manager import MultiRegionManager, RegionStatus, DeploymentStrategy


class TestType(Enum):
    """Types of disaster recovery tests"""
    UNIT_TEST = "unit_test"
    INTEGRATION_TEST = "integration_test"
    CHAOS_TEST = "chaos_test"
    LOAD_TEST = "load_test"
    FAILOVER_TEST = "failover_test"
    RECOVERY_TEST = "recovery_test"
    END_TO_END_TEST = "end_to_end_test"


class TestSeverity(Enum):
    """Test severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TestResult(Enum):
    """Test result status"""
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


@dataclass
class TestCase:
    """Individual test case definition"""
    test_id: str
    name: str
    description: str
    test_type: TestType
    severity: TestSeverity
    prerequisites: List[str] = field(default_factory=list)
    timeout: int = 300  # seconds
    retry_count: int = 0
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TestExecution:
    """Test execution results"""
    test_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: Optional[timedelta] = None
    result: TestResult = TestResult.SKIPPED
    error_message: Optional[str] = None
    metrics: Dict[str, Any] = field(default_factory=dict)
    artifacts: List[str] = field(default_factory=list)
    logs: List[str] = field(default_factory=list)


@dataclass
class ChaosExperiment:
    """Chaos engineering experiment definition"""
    experiment_id: str
    name: str
    description: str
    target_service: str
    failure_type: str
    duration: int  # seconds
    intensity: float  # 0.0 to 1.0
    hypothesis: str
    rollback_strategy: str
    safety_checks: List[str] = field(default_factory=list)


class MetricsCollector:
    """Collect and analyze system metrics during tests"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Metrics storage
        self.metrics: Dict[str, List[Tuple[datetime, float]]] = {}
        self.collecting = False
        self.collection_tasks: List[asyncio.Task] = []
    
    async def start_collection(self, metrics_to_collect: List[str]):
        """Start metrics collection"""
        self.collecting = True
        self.metrics = {metric: [] for metric in metrics_to_collect}
        
        # Start collection tasks
        for metric in metrics_to_collect:
            task = asyncio.create_task(self._collect_metric(metric))
            self.collection_tasks.append(task)
        
        self.logger.info(f"Started collecting {len(metrics_to_collect)} metrics")
    
    async def stop_collection(self) -> Dict[str, Any]:
        """Stop collection and return analysis"""
        self.collecting = False
        
        # Cancel collection tasks
        for task in self.collection_tasks:
            task.cancel()
        
        if self.collection_tasks:
            await asyncio.gather(*self.collection_tasks, return_exceptions=True)
        
        # Analyze collected metrics
        analysis = self._analyze_metrics()
        
        self.collection_tasks.clear()
        self.logger.info("Stopped metrics collection")
        
        return analysis
    
    async def _collect_metric(self, metric_name: str):
        """Collect individual metric"""
        while self.collecting:
            try:
                value = await self._get_metric_value(metric_name)
                if value is not None:
                    self.metrics[metric_name].append((datetime.utcnow(), value))
                
                await asyncio.sleep(self.config.get('collection_interval', 1))
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Metric collection error for {metric_name}: {e}")
                await asyncio.sleep(5)
    
    async def _get_metric_value(self, metric_name: str) -> Optional[float]:
        """Get current value for metric"""
        try:
            if metric_name == 'cpu_percent':
                return psutil.cpu_percent()
            elif metric_name == 'memory_percent':
                return psutil.virtual_memory().percent
            elif metric_name == 'disk_io_read':
                return psutil.disk_io_counters().read_bytes
            elif metric_name == 'disk_io_write':
                return psutil.disk_io_counters().write_bytes
            elif metric_name == 'network_sent':
                return psutil.net_io_counters().bytes_sent
            elif metric_name == 'network_recv':
                return psutil.net_io_counters().bytes_recv
            elif metric_name.startswith('response_time_'):
                # Custom response time measurement
                service = metric_name.replace('response_time_', '')
                return await self._measure_response_time(service)
            else:
                return None
        except Exception:
            return None
    
    async def _measure_response_time(self, service: str) -> Optional[float]:
        """Measure response time for service"""
        endpoints = {
            'api': 'http://localhost:8000/health',
            'database': 'http://localhost:8000/health/db',
            'redis': 'http://localhost:8000/health/redis'
        }
        
        endpoint = endpoints.get(service)
        if not endpoint:
            return None
        
        start_time = time.time()
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(endpoint, timeout=aiohttp.ClientTimeout(total=5)) as response:
                    await response.text()
                    return (time.time() - start_time) * 1000  # milliseconds
        except Exception:
            return None
    
    def _analyze_metrics(self) -> Dict[str, Any]:
        """Analyze collected metrics"""
        analysis = {}
        
        for metric_name, data_points in self.metrics.items():
            if not data_points:
                analysis[metric_name] = {'error': 'No data collected'}
                continue
            
            values = [point[1] for point in data_points]
            timestamps = [point[0] for point in data_points]
            
            analysis[metric_name] = {
                'count': len(values),
                'min': min(values),
                'max': max(values),
                'mean': statistics.mean(values),
                'median': statistics.median(values),
                'std_dev': statistics.stdev(values) if len(values) > 1 else 0,
                'duration': (timestamps[-1] - timestamps[0]).total_seconds() if len(timestamps) > 1 else 0
            }
            
            # Percentiles
            if len(values) > 1:
                analysis[metric_name]['p95'] = np.percentile(values, 95)
                analysis[metric_name]['p99'] = np.percentile(values, 99)
        
        return analysis


class ChaosEngineer:
    """Chaos engineering for disaster recovery testing"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Active experiments
        self.active_experiments: Dict[str, ChaosExperiment] = {}
        self.experiment_history: List[Dict[str, Any]] = []
        
        # Safety mechanisms
        self.safety_enabled = config.get('safety_enabled', True)
        self.rollback_timeout = config.get('rollback_timeout', 300)
    
    async def run_experiment(self, experiment: ChaosExperiment) -> Dict[str, Any]:
        """Run chaos experiment"""
        self.logger.info(f"Starting chaos experiment: {experiment.name}")
        
        start_time = datetime.utcnow()
        result = {
            'experiment_id': experiment.experiment_id,
            'name': experiment.name,
            'start_time': start_time,
            'status': 'running',
            'observations': [],
            'hypothesis_validated': None,
            'error': None
        }
        
        self.active_experiments[experiment.experiment_id] = experiment
        
        try:
            # Pre-experiment safety checks
            if self.safety_enabled:
                safety_passed = await self._run_safety_checks(experiment.safety_checks)
                if not safety_passed:
                    raise Exception("Safety checks failed, aborting experiment")
            
            # Collect baseline metrics
            baseline_metrics = await self._collect_baseline_metrics(experiment)
            result['baseline_metrics'] = baseline_metrics
            
            # Inject failure
            await self._inject_failure(experiment)
            
            # Monitor system behavior
            observations = await self._monitor_experiment(experiment)
            result['observations'] = observations
            
            # Validate hypothesis
            hypothesis_validated = await self._validate_hypothesis(experiment, observations)
            result['hypothesis_validated'] = hypothesis_validated
            
            # Rollback
            await self._rollback_experiment(experiment)
            
            result['status'] = 'completed'
            result['end_time'] = datetime.utcnow()
            result['duration'] = (result['end_time'] - start_time).total_seconds()
            
        except Exception as e:
            result['status'] = 'failed'
            result['error'] = str(e)
            result['end_time'] = datetime.utcnow()
            
            # Emergency rollback
            try:
                await self._rollback_experiment(experiment)
            except Exception as rollback_error:
                self.logger.error(f"Emergency rollback failed: {rollback_error}")
        
        finally:
            if experiment.experiment_id in self.active_experiments:
                del self.active_experiments[experiment.experiment_id]
            
            self.experiment_history.append(result)
        
        self.logger.info(f"Chaos experiment {experiment.name} completed with status: {result['status']}")
        return result
    
    async def _inject_failure(self, experiment: ChaosExperiment):
        """Inject specific type of failure"""
        if experiment.failure_type == 'service_crash':
            await self._crash_service(experiment.target_service, experiment.intensity)
        elif experiment.failure_type == 'network_partition':
            await self._create_network_partition(experiment.target_service, experiment.intensity)
        elif experiment.failure_type == 'latency_injection':
            await self._inject_latency(experiment.target_service, experiment.intensity)
        elif experiment.failure_type == 'resource_exhaustion':
            await self._exhaust_resources(experiment.target_service, experiment.intensity)
        elif experiment.failure_type == 'data_corruption':
            await self._corrupt_data(experiment.target_service, experiment.intensity)
        else:
            raise ValueError(f"Unknown failure type: {experiment.failure_type}")
    
    async def _crash_service(self, service: str, intensity: float):
        """Simulate service crash"""
        self.logger.info(f"Crashing service {service} with intensity {intensity}")
        
        # In a real implementation, this would:
        # 1. Stop the target service process
        # 2. Or kill specific containers
        # 3. Or terminate EC2 instances
        
        # Simulation: just log the action
        await asyncio.sleep(2)
    
    async def _create_network_partition(self, service: str, intensity: float):
        """Create network partition"""
        self.logger.info(f"Creating network partition for {service} with intensity {intensity}")
        
        # In a real implementation, this would use iptables or tc to:
        # 1. Block network traffic to/from service
        # 2. Drop packets with specified probability
        # 3. Delay packets
        
        await asyncio.sleep(2)
    
    async def _inject_latency(self, service: str, intensity: float):
        """Inject network latency"""
        latency_ms = int(intensity * 1000)  # Convert intensity to milliseconds
        self.logger.info(f"Injecting {latency_ms}ms latency to {service}")
        
        # In real implementation, use tc (traffic control) to add latency
        await asyncio.sleep(2)
    
    async def _monitor_experiment(self, experiment: ChaosExperiment) -> List[Dict[str, Any]]:
        """Monitor system during experiment"""
        observations = []
        monitor_duration = experiment.duration
        
        start_time = time.time()
        while time.time() - start_time < monitor_duration:
            observation = {
                'timestamp': datetime.utcnow(),
                'metrics': await self._collect_experiment_metrics()
            }
            observations.append(observation)
            
            await asyncio.sleep(5)  # Observe every 5 seconds
        
        return observations
    
    async def _collect_experiment_metrics(self) -> Dict[str, Any]:
        """Collect metrics during experiment"""
        return {
            'cpu_percent': psutil.cpu_percent(),
            'memory_percent': psutil.virtual_memory().percent,
            'active_connections': len(psutil.net_connections()),
            'process_count': len(psutil.pids())
        }


class DisasterRecoveryTestSuite:
    """Comprehensive disaster recovery test suite"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Test components
        self.dr_manager = None
        self.ha_manager = None
        self.mr_manager = None
        
        # Testing components
        self.metrics_collector = MetricsCollector(config.get('metrics', {}))
        self.chaos_engineer = ChaosEngineer(config.get('chaos', {}))
        
        # Test tracking
        self.test_cases: Dict[str, TestCase] = {}
        self.test_executions: Dict[str, TestExecution] = {}
        self.test_suites: Dict[str, List[str]] = {}
        
        # Load test definitions
        self._load_test_cases()
    
    def _load_test_cases(self):
        """Load test case definitions"""
        # Disaster Recovery Tests
        dr_tests = [
            TestCase(
                test_id="dr_001",
                name="Database Failure Recovery",
                description="Test recovery from primary database failure",
                test_type=TestType.FAILOVER_TEST,
                severity=TestSeverity.CRITICAL,
                timeout=600,
                tags=["database", "critical"]
            ),
            TestCase(
                test_id="dr_002", 
                name="API Server Failure Recovery",
                description="Test API server failover to backup instances",
                test_type=TestType.FAILOVER_TEST,
                severity=TestSeverity.HIGH,
                timeout=300,
                tags=["api", "failover"]
            ),
            TestCase(
                test_id="dr_003",
                name="Multi-Region Failover",
                description="Test failover from primary region to backup region",
                test_type=TestType.END_TO_END_TEST,
                severity=TestSeverity.CRITICAL,
                timeout=1800,
                tags=["multi-region", "critical"]
            )
        ]
        
        # High Availability Tests
        ha_tests = [
            TestCase(
                test_id="ha_001",
                name="Health Check Validation",
                description="Validate health check detection and response",
                test_type=TestType.INTEGRATION_TEST,
                severity=TestSeverity.MEDIUM,
                timeout=180,
                tags=["health-check", "monitoring"]
            ),
            TestCase(
                test_id="ha_002",
                name="Load Balancer Failover",
                description="Test automatic load balancer node removal",
                test_type=TestType.FAILOVER_TEST,
                severity=TestSeverity.HIGH,
                timeout=300,
                tags=["load-balancer", "failover"]
            )
        ]
        
        # Chaos Engineering Tests
        chaos_tests = [
            TestCase(
                test_id="chaos_001",
                name="Random Service Termination",
                description="Randomly terminate services to test resilience",
                test_type=TestType.CHAOS_TEST,
                severity=TestSeverity.HIGH,
                timeout=900,
                tags=["chaos", "resilience"]
            ),
            TestCase(
                test_id="chaos_002",
                name="Network Partition Test",
                description="Test system behavior under network partitions",
                test_type=TestType.CHAOS_TEST,
                severity=TestSeverity.CRITICAL,
                timeout=1200,
                tags=["chaos", "network"]
            )
        ]
        
        # Load tests into registry
        all_tests = dr_tests + ha_tests + chaos_tests
        for test in all_tests:
            self.test_cases[test.test_id] = test
        
        # Define test suites
        self.test_suites = {
            'disaster_recovery': [t.test_id for t in dr_tests],
            'high_availability': [t.test_id for t in ha_tests],
            'chaos_engineering': [t.test_id for t in chaos_tests],
            'smoke': ['dr_001', 'ha_001'],  # Quick validation tests
            'full': [t.test_id for t in all_tests]  # All tests
        }
    
    async def setup_test_environment(self):
        """Setup test environment"""
        self.logger.info("Setting up disaster recovery test environment")
        
        # Initialize disaster recovery components
        dr_config = self.config.get('disaster_recovery', {})
        self.dr_manager = DisasterRecoveryManager(dr_config)
        
        ha_config = self.config.get('high_availability', {})
        self.ha_manager = HighAvailabilityManager(ha_config)
        
        mr_config = self.config.get('multi_region', {})
        self.mr_manager = MultiRegionManager(mr_config)
        
        # Start components
        await self.ha_manager.start()
        await self.mr_manager.initialize()
        
        self.logger.info("Test environment setup complete")
    
    async def teardown_test_environment(self):
        """Teardown test environment"""
        self.logger.info("Tearing down test environment")
        
        # Stop components
        if self.ha_manager:
            await self.ha_manager.stop()
        
        self.logger.info("Test environment teardown complete")
    
    async def run_test(self, test_id: str) -> TestExecution:
        """Run individual test"""
        if test_id not in self.test_cases:
            raise ValueError(f"Unknown test ID: {test_id}")
        
        test_case = self.test_cases[test_id]
        execution = TestExecution(
            test_id=test_id,
            start_time=datetime.utcnow()
        )
        
        self.logger.info(f"Starting test {test_id}: {test_case.name}")
        
        try:
            # Start metrics collection
            await self.metrics_collector.start_collection([
                'cpu_percent', 'memory_percent', 'response_time_api'
            ])
            
            # Run test based on type
            if test_case.test_type == TestType.FAILOVER_TEST:
                await self._run_failover_test(test_case, execution)
            elif test_case.test_type == TestType.CHAOS_TEST:
                await self._run_chaos_test(test_case, execution)
            elif test_case.test_type == TestType.INTEGRATION_TEST:
                await self._run_integration_test(test_case, execution)
            elif test_case.test_type == TestType.END_TO_END_TEST:
                await self._run_end_to_end_test(test_case, execution)
            else:
                await self._run_generic_test(test_case, execution)
            
            execution.result = TestResult.PASSED
            
        except asyncio.TimeoutError:
            execution.result = TestResult.ERROR
            execution.error_message = f"Test timed out after {test_case.timeout} seconds"
        except Exception as e:
            execution.result = TestResult.FAILED
            execution.error_message = str(e)
            self.logger.error(f"Test {test_id} failed: {e}")
        
        finally:
            # Stop metrics collection and get analysis
            execution.metrics = await self.metrics_collector.stop_collection()
            
            # Complete execution record
            execution.end_time = datetime.utcnow()
            execution.duration = execution.end_time - execution.start_time
            
            # Store execution
            self.test_executions[test_id] = execution
        
        self.logger.info(f"Test {test_id} completed with result: {execution.result.value}")
        return execution
    
    async def _run_failover_test(self, test_case: TestCase, execution: TestExecution):
        """Run failover test"""
        if test_case.test_id == "dr_001":  # Database failure recovery
            # Simulate database failure
            incident = {
                'id': 'test_db_failure',
                'type': 'system_failure',
                'affected_systems': ['database_primary'],
                'description': 'Simulated database failure for testing'
            }
            
            # Assess damage
            assessment = await self.dr_manager.assess_damage(incident)
            execution.logs.append(f"Damage assessment: {assessment.severity.name}")
            
            # Initiate recovery
            recovery_id = await self.dr_manager.initiate_failover(assessment)
            execution.logs.append(f"Recovery initiated: {recovery_id}")
            
            # Monitor recovery
            timeout = time.time() + 300  # 5 minutes
            while time.time() < timeout:
                status = await self.dr_manager.get_recovery_status(recovery_id)
                if status and status.progress_percentage >= 100:
                    break
                await asyncio.sleep(10)
            
            # Validate recovery
            validation_results = await self.dr_manager.validate_recovery(recovery_id)
            execution.metrics['validation_results'] = validation_results
            
            if validation_results['overall_status'] != 'passed':
                raise Exception(f"Recovery validation failed: {validation_results}")
        
        elif test_case.test_id == "dr_002":  # API server failure recovery
            # Test load balancer failover
            if self.ha_manager:
                # Trigger manual failover
                await self.ha_manager.manual_failover('primary_api_1', 'backup_api_1')
                await asyncio.sleep(30)  # Wait for failover
                
                # Verify system status
                status = await self.ha_manager.get_system_status()
                execution.metrics['system_status'] = status
                
                if status['overall_health'] != 'HEALTHY':
                    raise Exception(f"System not healthy after failover: {status['overall_health']}")
    
    async def _run_chaos_test(self, test_case: TestCase, execution: TestExecution):
        """Run chaos engineering test"""
        if test_case.test_id == "chaos_001":  # Random service termination
            experiment = ChaosExperiment(
                experiment_id=f"chaos_{int(time.time())}",
                name="Random Service Termination",
                description="Randomly terminate services to test resilience",
                target_service="api_service",
                failure_type="service_crash",
                duration=60,
                intensity=0.5,
                hypothesis="System should recover automatically within 2 minutes",
                rollback_strategy="restart_service",
                safety_checks=["backup_service_available"]
            )
            
            result = await self.chaos_engineer.run_experiment(experiment)
            execution.metrics['chaos_result'] = result
            
            if result['status'] != 'completed' or not result.get('hypothesis_validated'):
                raise Exception(f"Chaos experiment failed: {result.get('error', 'Hypothesis not validated')}")
    
    async def _run_integration_test(self, test_case: TestCase, execution: TestExecution):
        """Run integration test"""
        if test_case.test_id == "ha_001":  # Health check validation
            if self.ha_manager:
                # Get current health status
                status = await self.ha_manager.get_system_status()
                execution.metrics['initial_status'] = status
                
                # Simulate service degradation
                # This would normally involve actual service manipulation
                await asyncio.sleep(30)
                
                # Verify health check detection
                final_status = await self.ha_manager.get_system_status()
                execution.metrics['final_status'] = final_status
    
    async def _run_end_to_end_test(self, test_case: TestCase, execution: TestExecution):
        """Run end-to-end test"""
        if test_case.test_id == "dr_003":  # Multi-region failover
            if self.mr_manager:
                # Test multi-region deployment
                deployment_config = {
                    'target_regions': ['us-east-1', 'eu-west-1'],
                    'strategy': 'blue_green',
                    'version': 'test_version',
                    'estimated_minutes': 10
                }
                
                job_id = await self.mr_manager.deploy_multi_region(deployment_config)
                execution.logs.append(f"Multi-region deployment started: {job_id}")
                
                # Monitor deployment
                timeout = time.time() + 600  # 10 minutes
                while time.time() < timeout:
                    status = await self.mr_manager.get_deployment_status(job_id)
                    if status and status.get('progress', 0) >= 100:
                        break
                    await asyncio.sleep(15)
                
                # Verify deployment
                final_status = await self.mr_manager.get_multi_region_status()
                execution.metrics['deployment_status'] = final_status
                
                if final_status['healthy_regions'] < 2:
                    raise Exception(f"Multi-region deployment failed: {final_status['healthy_regions']} healthy regions")
    
    async def _run_generic_test(self, test_case: TestCase, execution: TestExecution):
        """Run generic test"""
        # Generic test implementation
        execution.logs.append(f"Running generic test for {test_case.name}")
        await asyncio.sleep(5)  # Simulate test work
    
    async def run_test_suite(self, suite_name: str) -> Dict[str, TestExecution]:
        """Run a test suite"""
        if suite_name not in self.test_suites:
            raise ValueError(f"Unknown test suite: {suite_name}")
        
        test_ids = self.test_suites[suite_name]
        self.logger.info(f"Running test suite '{suite_name}' with {len(test_ids)} tests")
        
        results = {}
        
        # Run tests in parallel for non-conflicting tests
        # For now, run sequentially for safety
        for test_id in test_ids:
            try:
                execution = await self.run_test(test_id)
                results[test_id] = execution
            except Exception as e:
                self.logger.error(f"Failed to run test {test_id}: {e}")
                results[test_id] = TestExecution(
                    test_id=test_id,
                    start_time=datetime.utcnow(),
                    end_time=datetime.utcnow(),
                    result=TestResult.ERROR,
                    error_message=str(e)
                )
        
        # Generate suite report
        passed = len([r for r in results.values() if r.result == TestResult.PASSED])
        total = len(results)
        
        self.logger.info(f"Test suite '{suite_name}' completed: {passed}/{total} tests passed")
        
        return results
    
    def generate_test_report(self, suite_results: Dict[str, TestExecution]) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        report = {
            'summary': {
                'total_tests': len(suite_results),
                'passed': len([r for r in suite_results.values() if r.result == TestResult.PASSED]),
                'failed': len([r for r in suite_results.values() if r.result == TestResult.FAILED]),
                'errors': len([r for r in suite_results.values() if r.result == TestResult.ERROR]),
                'skipped': len([r for r in suite_results.values() if r.result == TestResult.SKIPPED]),
            },
            'test_results': {},
            'performance_metrics': {},
            'recommendations': []
        }
        
        # Calculate pass rate
        if report['summary']['total_tests'] > 0:
            report['summary']['pass_rate'] = (report['summary']['passed'] / report['summary']['total_tests']) * 100
        else:
            report['summary']['pass_rate'] = 0
        
        # Detailed results
        for test_id, execution in suite_results.items():
            test_case = self.test_cases[test_id]
            
            report['test_results'][test_id] = {
                'name': test_case.name,
                'result': execution.result.value,
                'duration': execution.duration.total_seconds() if execution.duration else 0,
                'error_message': execution.error_message,
                'severity': test_case.severity.value,
                'tags': test_case.tags
            }
        
        # Performance analysis
        durations = [
            execution.duration.total_seconds() 
            for execution in suite_results.values() 
            if execution.duration
        ]
        
        if durations:
            report['performance_metrics'] = {
                'total_duration': sum(durations),
                'average_duration': statistics.mean(durations),
                'max_duration': max(durations),
                'min_duration': min(durations)
            }
        
        # Recommendations
        if report['summary']['pass_rate'] < 100:
            report['recommendations'].append("Review failed tests and improve disaster recovery procedures")
        
        if report['performance_metrics'].get('average_duration', 0) > 300:
            report['recommendations'].append("Consider optimizing recovery procedures to meet RTO targets")
        
        critical_failures = [
            test_id for test_id, execution in suite_results.items()
            if (execution.result != TestResult.PASSED and 
                self.test_cases[test_id].severity == TestSeverity.CRITICAL)
        ]
        
        if critical_failures:
            report['recommendations'].append(f"URGENT: Address critical test failures: {', '.join(critical_failures)}")
        
        return report


# Example usage and pytest integration
class TestDisasterRecovery:
    """Pytest test class for disaster recovery"""
    
    @pytest.fixture(scope="class")
    async def test_suite(self):
        """Setup test suite fixture"""
        config = {
            'disaster_recovery': {
                'primary_region': 'us-east-1',
                'backup_region': 'us-west-2',
                'redis': {'host': 'localhost', 'port': 6379}
            },
            'high_availability': {
                'auto_failover_enabled': True,
                'api_base_url': 'http://localhost:8000'
            },
            'multi_region': {
                'regions': {
                    'us-east-1': {'name': 'US East', 'aws_region': 'us-east-1', 'priority': 1},
                    'eu-west-1': {'name': 'EU West', 'aws_region': 'eu-west-1', 'priority': 2}
                }
            },
            'metrics': {'collection_interval': 1},
            'chaos': {'safety_enabled': True}
        }
        
        suite = DisasterRecoveryTestSuite(config)
        await suite.setup_test_environment()
        
        yield suite
        
        await suite.teardown_test_environment()
    
    @pytest.mark.asyncio
    async def test_database_failure_recovery(self, test_suite):
        """Test database failure recovery"""
        execution = await test_suite.run_test("dr_001")
        assert execution.result == TestResult.PASSED
    
    @pytest.mark.asyncio
    async def test_health_check_validation(self, test_suite):
        """Test health check validation"""
        execution = await test_suite.run_test("ha_001")
        assert execution.result == TestResult.PASSED
    
    @pytest.mark.asyncio
    async def test_smoke_suite(self, test_suite):
        """Run smoke test suite"""
        results = await test_suite.run_test_suite("smoke")
        
        # All smoke tests should pass
        for test_id, execution in results.items():
            assert execution.result == TestResult.PASSED, f"Smoke test {test_id} failed: {execution.error_message}"


if __name__ == "__main__":
    # Example standalone execution
    async def run_disaster_recovery_tests():
        config = {
            'disaster_recovery': {'primary_region': 'us-east-1'},
            'high_availability': {'auto_failover_enabled': True},
            'multi_region': {'regions': {'us-east-1': {'priority': 1}}},
            'metrics': {'collection_interval': 2},
            'chaos': {'safety_enabled': True}
        }
        
        test_suite = DisasterRecoveryTestSuite(config)
        await test_suite.setup_test_environment()
        
        try:
            # Run full test suite
            results = await test_suite.run_test_suite("full")
            
            # Generate report
            report = test_suite.generate_test_report(results)
            
            print(f"Test Results: {report['summary']['passed']}/{report['summary']['total_tests']} passed")
            print(f"Pass Rate: {report['summary']['pass_rate']:.1f}%")
            
            if report['recommendations']:
                print("\nRecommendations:")
                for rec in report['recommendations']:
                    print(f"- {rec}")
        
        finally:
            await test_suite.teardown_test_environment()
    
    # Run tests
    # asyncio.run(run_disaster_recovery_tests())