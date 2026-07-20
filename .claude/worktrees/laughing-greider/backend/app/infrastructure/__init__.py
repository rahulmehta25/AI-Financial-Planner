"""
Financial Planning System - Infrastructure Module

This module provides comprehensive infrastructure management including:
- Disaster recovery and business continuity
- High availability and automatic failover
- Multi-region deployment coordination
- Comprehensive testing and validation

Usage:
    from backend.app.infrastructure import InfrastructureManager
    
    # Initialize with configuration
    config = {...}
    infrastructure = InfrastructureManager(config)
    
    # Start all services
    await infrastructure.start()
    
    # Get system status
    status = await infrastructure.get_overall_status()
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from .disaster_recovery import DisasterRecoveryManager, DisasterType, SeverityLevel
from .high_availability import HighAvailabilityManager, ServiceStatus
from .multi_region_manager import MultiRegionManager, RegionStatus
from .disaster_recovery_tests import DisasterRecoveryTestSuite


class InfrastructureManager:
    """
    Central infrastructure management system that coordinates all
    disaster recovery, high availability, and multi-region capabilities
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize infrastructure manager
        
        Args:
            config: Configuration dictionary containing settings for all components
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.disaster_recovery = DisasterRecoveryManager(
            config.get('disaster_recovery', {})
        )
        
        self.high_availability = HighAvailabilityManager(
            config.get('high_availability', {})
        )
        
        self.multi_region = MultiRegionManager(
            config.get('multi_region', {})
        )
        
        self.test_suite = DisasterRecoveryTestSuite(
            config.get('testing', {})
        )
        
        # Status tracking
        self.started = False
        self.start_time: Optional[datetime] = None
        
    async def start(self):
        """Start all infrastructure services"""
        if self.started:
            self.logger.warning("Infrastructure services already started")
            return
        
        self.logger.info("Starting infrastructure services...")
        
        try:
            # Start high availability manager
            await self.high_availability.start()
            self.logger.info("High availability manager started")
            
            # Initialize multi-region manager
            await self.multi_region.initialize()
            self.logger.info("Multi-region manager initialized")
            
            # Setup test environment (optional)
            if self.config.get('testing', {}).get('auto_setup', False):
                await self.test_suite.setup_test_environment()
                self.logger.info("Test environment setup complete")
            
            self.started = True
            self.start_time = datetime.utcnow()
            
            self.logger.info("All infrastructure services started successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to start infrastructure services: {e}")
            await self.stop()  # Cleanup on failure
            raise
    
    async def stop(self):
        """Stop all infrastructure services"""
        if not self.started:
            return
        
        self.logger.info("Stopping infrastructure services...")
        
        try:
            # Stop high availability manager
            await self.high_availability.stop()
            self.logger.info("High availability manager stopped")
            
            # Teardown test environment
            if hasattr(self.test_suite, 'teardown_test_environment'):
                await self.test_suite.teardown_test_environment()
                self.logger.info("Test environment cleaned up")
            
            self.started = False
            self.start_time = None
            
            self.logger.info("All infrastructure services stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping infrastructure services: {e}")
    
    async def get_overall_status(self) -> Dict[str, Any]:
        """Get comprehensive status of all infrastructure components"""
        try:
            # Get component statuses
            ha_status = await self.high_availability.get_system_status()
            mr_status = await self.multi_region.get_multi_region_status()
            
            # Get disaster recovery metrics
            dr_metrics = self.disaster_recovery.get_rto_rpo_metrics()
            
            # Determine overall health
            overall_health = "healthy"
            if ha_status.get('overall_health') != 'HEALTHY':
                overall_health = "degraded"
            
            if mr_status.get('healthy_regions', 0) < mr_status.get('total_regions', 1) / 2:
                overall_health = "critical"
            
            return {
                'overall_health': overall_health,
                'started': self.started,
                'uptime': (datetime.utcnow() - self.start_time).total_seconds() if self.start_time else 0,
                'components': {
                    'high_availability': ha_status,
                    'multi_region': mr_status,
                    'disaster_recovery': {
                        'rto_target': str(dr_metrics.get('rto_target', 'unknown')),
                        'rpo_target': str(dr_metrics.get('rpo_target', 'unknown')),
                        'active_recoveries': len(await self.disaster_recovery.list_active_recoveries())
                    }
                },
                'last_updated': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting overall status: {e}")
            return {
                'overall_health': 'unknown',
                'error': str(e),
                'last_updated': datetime.utcnow().isoformat()
            }
    
    async def trigger_disaster_recovery(self, incident_data: Dict[str, Any]) -> str:
        """
        Trigger disaster recovery process
        
        Args:
            incident_data: Information about the incident
            
        Returns:
            Recovery operation ID
        """
        self.logger.info(f"Triggering disaster recovery for incident: {incident_data.get('id', 'unknown')}")
        
        # Assess damage
        assessment = await self.disaster_recovery.assess_damage(incident_data)
        
        # Initiate recovery
        recovery_id = await self.disaster_recovery.initiate_failover(assessment)
        
        self.logger.info(f"Disaster recovery initiated: {recovery_id}")
        return recovery_id
    
    async def manual_failover(self, source_node: str, target_node: str) -> bool:
        """
        Trigger manual failover between nodes
        
        Args:
            source_node: Source node identifier
            target_node: Target node identifier
            
        Returns:
            True if failover successful
        """
        self.logger.info(f"Manual failover requested: {source_node} -> {target_node}")
        
        result = await self.high_availability.manual_failover(source_node, target_node)
        
        if result:
            self.logger.info(f"Manual failover completed successfully")
        else:
            self.logger.error(f"Manual failover failed")
        
        return result
    
    async def deploy_multi_region(self, deployment_config: Dict[str, Any]) -> str:
        """
        Deploy to multiple regions
        
        Args:
            deployment_config: Deployment configuration
            
        Returns:
            Deployment job ID
        """
        self.logger.info(f"Multi-region deployment requested for version {deployment_config.get('version')}")
        
        job_id = await self.multi_region.deploy_multi_region(deployment_config)
        
        self.logger.info(f"Multi-region deployment started: {job_id}")
        return job_id
    
    async def run_disaster_recovery_tests(self, suite_name: str = "smoke") -> Dict[str, Any]:
        """
        Run disaster recovery tests
        
        Args:
            suite_name: Test suite to run (smoke, full, etc.)
            
        Returns:
            Test results and report
        """
        self.logger.info(f"Running disaster recovery tests: {suite_name}")
        
        # Run test suite
        results = await self.test_suite.run_test_suite(suite_name)
        
        # Generate report
        report = self.test_suite.generate_test_report(results)
        
        self.logger.info(f"Test suite '{suite_name}' completed: {report['summary']['passed']}/{report['summary']['total_tests']} passed")
        
        return {
            'suite_name': suite_name,
            'results': results,
            'report': report
        }
    
    async def get_recovery_status(self, recovery_id: str) -> Optional[Dict[str, Any]]:
        """Get status of disaster recovery operation"""
        status = await self.disaster_recovery.get_recovery_status(recovery_id)
        
        if status:
            return {
                'recovery_id': status.recovery_id,
                'phase': status.phase.value,
                'progress': status.progress_percentage,
                'current_step': status.current_step,
                'total_steps': status.total_steps,
                'errors': status.errors,
                'warnings': status.warnings
            }
        
        return None
    
    async def get_deployment_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get status of multi-region deployment"""
        return await self.multi_region.get_deployment_status(job_id)


# Convenience functions for easy imports
def create_infrastructure_manager(config: Dict[str, Any]) -> InfrastructureManager:
    """Create and return an InfrastructureManager instance"""
    return InfrastructureManager(config)


# Default configuration template
DEFAULT_CONFIG = {
    'disaster_recovery': {
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
    },
    'high_availability': {
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
    },
    'multi_region': {
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
            'country_mappings': {
                'US': 'us-east-1',
                'CA': 'us-east-1',
                'GB': 'eu-west-1',
                'DE': 'eu-west-1',
                'FR': 'eu-west-1'
            }
        },
        'data_sync': {
            'redis': {
                'host': 'localhost',
                'port': 6379
            }
        }
    },
    'testing': {
        'auto_setup': False,
        'metrics': {
            'collection_interval': 1
        },
        'chaos': {
            'safety_enabled': True,
            'rollback_timeout': 300
        }
    }
}


# Export main classes and functions
__all__ = [
    'InfrastructureManager',
    'DisasterRecoveryManager',
    'HighAvailabilityManager', 
    'MultiRegionManager',
    'DisasterRecoveryTestSuite',
    'create_infrastructure_manager',
    'DEFAULT_CONFIG',
    'DisasterType',
    'SeverityLevel',
    'ServiceStatus',
    'RegionStatus'
]