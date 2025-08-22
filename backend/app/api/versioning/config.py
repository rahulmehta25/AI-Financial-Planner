"""
Configuration Management for API Versioning System
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from pathlib import Path
import json
import yaml
from datetime import datetime

from .models import DeprecationPolicy
from .manager import VersionManager
from .middleware import VersioningMiddleware
from .compatibility import CompatibilityAnalyzer
from .documentation import DocumentationGenerator
from .sdk_manager import SDKManager
from .ab_testing import ABTestManager
from .gateway import GatewayConfigGenerator

logger = logging.getLogger(__name__)


@dataclass
class VersioningConfig:
    """Main configuration for versioning system"""
    enabled: bool = True
    default_version: str = "1.0.0"
    deprecation_policy: DeprecationPolicy = field(default_factory=DeprecationPolicy)
    documentation_enabled: bool = True
    sdk_management_enabled: bool = True
    ab_testing_enabled: bool = True
    gateway_config_enabled: bool = True
    
    # Paths
    config_dir: str = "config/versioning"
    docs_output_dir: str = "docs/api"
    sdk_output_dir: str = "docs/sdk"
    ab_test_reports_dir: str = "reports/ab_tests"
    
    # Auto-generation settings
    auto_generate_docs: bool = True
    auto_export_gateway_configs: bool = False
    auto_advance_rollouts: bool = True
    
    # Monitoring settings
    metrics_enabled: bool = True
    metrics_retention_days: int = 90
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'enabled': self.enabled,
            'default_version': self.default_version,
            'deprecation_policy': self.deprecation_policy.__dict__,
            'documentation_enabled': self.documentation_enabled,
            'sdk_management_enabled': self.sdk_management_enabled,
            'ab_testing_enabled': self.ab_testing_enabled,
            'gateway_config_enabled': self.gateway_config_enabled,
            'config_dir': self.config_dir,
            'docs_output_dir': self.docs_output_dir,
            'sdk_output_dir': self.sdk_output_dir,
            'ab_test_reports_dir': self.ab_test_reports_dir,
            'auto_generate_docs': self.auto_generate_docs,
            'auto_export_gateway_configs': self.auto_export_gateway_configs,
            'auto_advance_rollouts': self.auto_advance_rollouts,
            'metrics_enabled': self.metrics_enabled,
            'metrics_retention_days': self.metrics_retention_days
        }


class VersioningSystem:
    """Main versioning system orchestrator"""
    
    def __init__(self, config: Optional[VersioningConfig] = None):
        self.config = config or VersioningConfig()
        
        # Ensure directories exist
        Path(self.config.config_dir).mkdir(parents=True, exist_ok=True)
        Path(self.config.docs_output_dir).mkdir(parents=True, exist_ok=True)
        Path(self.config.sdk_output_dir).mkdir(parents=True, exist_ok=True)
        Path(self.config.ab_test_reports_dir).mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self.version_manager = VersionManager(
            config_path=f"{self.config.config_dir}/versions.json"
        )
        
        self.compatibility_analyzer = CompatibilityAnalyzer(self.version_manager)
        
        self.documentation_generator = None
        self.sdk_manager = None
        self.ab_test_manager = None
        self.gateway_generator = None
        
        if self.config.documentation_enabled:
            self.documentation_generator = DocumentationGenerator(
                self.version_manager,
                self.compatibility_analyzer,
                template_dir=f"{self.config.config_dir}/templates"
            )
        
        if self.config.sdk_management_enabled:
            self.sdk_manager = SDKManager(
                self.version_manager,
                self.compatibility_analyzer,
                config_path=f"{self.config.config_dir}/sdk_config.json"
            )
        
        if self.config.ab_testing_enabled:
            self.ab_test_manager = ABTestManager(
                self.version_manager,
                config_path=f"{self.config.config_dir}/ab_tests.json"
            )
        
        if self.config.gateway_config_enabled:
            self.gateway_generator = GatewayConfigGenerator(self.version_manager)
        
        logger.info("Versioning system initialized")
    
    def get_middleware(self) -> VersioningMiddleware:
        """Get versioning middleware for FastAPI"""
        return VersioningMiddleware(None, self.version_manager)
    
    def get_version_for_request(
        self, 
        user_id: str = None, 
        user_context: Dict[str, Any] = None,
        default_version: str = None
    ) -> str:
        """Get appropriate version for a request"""
        
        default_version = default_version or self.config.default_version
        
        # Check A/B tests if enabled
        if self.config.ab_testing_enabled and self.ab_test_manager and user_id:
            user_context = user_context or {}
            return self.ab_test_manager.get_version_for_user(
                user_id, user_context, default_version
            )
        
        return default_version
    
    def generate_all_documentation(self) -> Dict[str, List[str]]:
        """Generate documentation for all versions"""
        if not self.documentation_generator:
            return {}
        
        return self.documentation_generator.export_all_documentation()
    
    def export_all_sdk_matrices(self) -> Dict[str, str]:
        """Export all SDK compatibility matrices"""
        if not self.sdk_manager:
            return {}
        
        return self.sdk_manager.export_compatibility_matrices(self.config.sdk_output_dir)
    
    def export_all_gateway_configs(self) -> Dict[str, str]:
        """Export all gateway configurations"""
        if not self.gateway_generator:
            return {}
        
        return self.gateway_generator.export_all_configs(
            f"{self.config.config_dir}/gateway"
        )
    
    def export_ab_test_results(self) -> Dict[str, str]:
        """Export A/B test results"""
        if not self.ab_test_manager:
            return {}
        
        return self.ab_test_manager.export_test_results(self.config.ab_test_reports_dir)
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status"""
        
        status = {
            'timestamp': datetime.utcnow().isoformat(),
            'system_enabled': self.config.enabled,
            'components': {
                'version_manager': True,
                'compatibility_analyzer': True,
                'documentation_generator': self.config.documentation_enabled,
                'sdk_manager': self.config.sdk_management_enabled,
                'ab_test_manager': self.config.ab_testing_enabled,
                'gateway_generator': self.config.gateway_config_enabled
            },
            'versions': {
                'total': len(self.version_manager.get_all_versions()),
                'supported': len(self.version_manager.get_supported_versions()),
                'deprecated': len([v for v in self.version_manager.get_all_versions() if v.is_deprecated]),
                'retired': len([v for v in self.version_manager.get_all_versions() if v.is_retired])
            }
        }
        
        # Add component-specific status
        if self.sdk_manager:
            compatibility_report = self.sdk_manager.generate_sdk_compatibility_report()
            status['sdk_management'] = {
                'total_sdks': compatibility_report['summary']['total_sdks'],
                'languages_supported': compatibility_report['summary']['languages_supported'],
                'compatibility_coverage': compatibility_report['summary']['compatibility_coverage']
            }
        
        if self.ab_test_manager:
            dashboard = self.ab_test_manager.get_test_dashboard()
            status['ab_testing'] = {
                'active_tests': dashboard['active_tests'],
                'total_tests': dashboard['total_tests'],
                'active_rollouts': dashboard['active_rollouts']
            }
        
        return status
    
    def validate_system_health(self) -> Dict[str, Any]:
        """Validate system health and configuration"""
        
        health = {
            'overall_status': 'healthy',
            'issues': [],
            'warnings': [],
            'recommendations': []
        }
        
        # Validate version manager
        version_issues = self.version_manager.validate_version_sequence()
        if version_issues:
            health['issues'].extend(version_issues)
            health['overall_status'] = 'issues'
        
        # Check for versions needing retirement warnings
        urgent_versions = self.version_manager.get_versions_needing_retirement_warning(30)
        if urgent_versions:
            health['warnings'].append(f"{len(urgent_versions)} versions need retirement warnings")
        
        # Validate SDK compatibility if enabled
        if self.sdk_manager:
            compatibility_report = self.sdk_manager.generate_sdk_compatibility_report()
            coverage = compatibility_report['summary']['compatibility_coverage']
            
            if coverage < 0.8:
                health['warnings'].append(f"Low SDK compatibility coverage: {coverage:.1%}")
                health['recommendations'].append("Update SDKs to improve API version coverage")
        
        # Check A/B test health if enabled
        if self.ab_test_manager:
            active_tests = self.ab_test_manager.get_active_tests()
            
            for test in active_tests:
                # Check if test has enough data
                if test.test_name in self.ab_test_manager.test_metrics:
                    control_metrics = self.ab_test_manager.test_metrics[test.test_name].get("control")
                    treatment_metrics = self.ab_test_manager.test_metrics[test.test_name].get("treatment")
                    
                    if control_metrics and control_metrics.total_requests < 100:
                        health['warnings'].append(f"A/B test {test.test_name} has insufficient data")
                    
                    if treatment_metrics and treatment_metrics.error_rate > 0.1:
                        health['issues'].append(f"A/B test {test.test_name} has high error rate")
                        health['overall_status'] = 'issues'
        
        return health
    
    def create_migration_plan(self, from_version: str, to_version: str) -> Dict[str, Any]:
        """Create comprehensive migration plan"""
        
        migration_plan = {
            'from_version': from_version,
            'to_version': to_version,
            'created_at': datetime.utcnow().isoformat(),
            'compatibility_analysis': None,
            'migration_guide': None,
            'sdk_recommendations': {},
            'testing_plan': None,
            'rollout_plan': None
        }
        
        # Get compatibility analysis
        migration_plan['compatibility_analysis'] = self.compatibility_analyzer.analyze_compatibility(
            from_version, to_version
        )
        
        # Generate migration guide
        migration_plan['migration_guide'] = self.compatibility_analyzer.generate_migration_guide(
            from_version, to_version
        )
        
        # Get SDK recommendations for each language
        if self.sdk_manager:
            for language in ['python', 'javascript', 'java']:
                recommendations = self.sdk_manager.generate_sdk_recommendations(
                    language, to_version
                )
                if recommendations['recommended_sdk']:
                    migration_plan['sdk_recommendations'][language] = recommendations
        
        # Create testing plan
        migration_plan['testing_plan'] = {
            'phases': [
                {
                    'phase': 'Unit Testing',
                    'description': 'Test individual components with new API version',
                    'duration': '1-2 days',
                    'checklist': [
                        'Update test configuration to use new API version',
                        'Run existing unit tests',
                        'Add tests for new features',
                        'Verify deprecated endpoint handling'
                    ]
                },
                {
                    'phase': 'Integration Testing',
                    'description': 'Test full application with new API version',
                    'duration': '2-3 days',
                    'checklist': [
                        'Configure staging environment',
                        'Run integration test suite',
                        'Test error handling and edge cases',
                        'Verify performance metrics'
                    ]
                },
                {
                    'phase': 'User Acceptance Testing',
                    'description': 'Validate functionality from user perspective',
                    'duration': '3-5 days',
                    'checklist': [
                        'Deploy to UAT environment',
                        'Execute user test scenarios',
                        'Validate UI/UX compatibility',
                        'Gather user feedback'
                    ]
                }
            ]
        }
        
        # Create rollout plan
        if migration_plan['compatibility_analysis']['is_breaking']:
            rollout_strategy = 'gradual'
        else:
            rollout_strategy = 'direct'
        
        migration_plan['rollout_plan'] = {
            'strategy': rollout_strategy,
            'phases': []
        }
        
        if rollout_strategy == 'gradual':
            migration_plan['rollout_plan']['phases'] = [
                {'percentage': 5, 'duration_hours': 24, 'description': 'Initial rollout to 5% of users'},
                {'percentage': 15, 'duration_hours': 48, 'description': 'Expand to 15% if metrics are good'},
                {'percentage': 50, 'duration_hours': 72, 'description': 'Roll out to half of users'},
                {'percentage': 100, 'duration_hours': 0, 'description': 'Complete rollout'}
            ]
        else:
            migration_plan['rollout_plan']['phases'] = [
                {'percentage': 100, 'duration_hours': 0, 'description': 'Direct deployment'}
            ]
        
        return migration_plan
    
    def save_configuration(self):
        """Save all component configurations"""
        
        # Save main config
        config_file = Path(self.config.config_dir) / "versioning_config.json"
        with open(config_file, 'w') as f:
            json.dump(self.config.to_dict(), f, indent=2)
        
        # Save component configs
        self.version_manager.save_configuration()
        
        if self.sdk_manager:
            # SDK manager would save its config
            pass
        
        if self.ab_test_manager:
            self.ab_test_manager.save_configuration()
        
        logger.info("Saved all versioning configurations")
    
    @classmethod
    def load_from_config(cls, config_path: str) -> 'VersioningSystem':
        """Load versioning system from configuration file"""
        
        config_file = Path(config_path)
        if not config_file.exists():
            logger.warning(f"Config file {config_path} not found, using defaults")
            return cls()
        
        try:
            with open(config_file, 'r') as f:
                config_data = json.load(f)
            
            # Create deprecation policy
            if 'deprecation_policy' in config_data:
                policy_data = config_data['deprecation_policy']
                deprecation_policy = DeprecationPolicy(**policy_data)
            else:
                deprecation_policy = DeprecationPolicy()
            
            # Create main config
            config = VersioningConfig(
                enabled=config_data.get('enabled', True),
                default_version=config_data.get('default_version', '1.0.0'),
                deprecation_policy=deprecation_policy,
                documentation_enabled=config_data.get('documentation_enabled', True),
                sdk_management_enabled=config_data.get('sdk_management_enabled', True),
                ab_testing_enabled=config_data.get('ab_testing_enabled', True),
                gateway_config_enabled=config_data.get('gateway_config_enabled', True),
                config_dir=config_data.get('config_dir', 'config/versioning'),
                docs_output_dir=config_data.get('docs_output_dir', 'docs/api'),
                sdk_output_dir=config_data.get('sdk_output_dir', 'docs/sdk'),
                ab_test_reports_dir=config_data.get('ab_test_reports_dir', 'reports/ab_tests'),
                auto_generate_docs=config_data.get('auto_generate_docs', True),
                auto_export_gateway_configs=config_data.get('auto_export_gateway_configs', False),
                auto_advance_rollouts=config_data.get('auto_advance_rollouts', True),
                metrics_enabled=config_data.get('metrics_enabled', True),
                metrics_retention_days=config_data.get('metrics_retention_days', 90)
            )
            
            return cls(config)
            
        except Exception as e:
            logger.error(f"Failed to load config from {config_path}: {e}")
            return cls()


# Global versioning system instance
versioning_system: Optional[VersioningSystem] = None


def get_versioning_system() -> VersioningSystem:
    """Get or create global versioning system instance"""
    global versioning_system
    
    if versioning_system is None:
        versioning_system = VersioningSystem()
    
    return versioning_system


def initialize_versioning_system(config_path: Optional[str] = None) -> VersioningSystem:
    """Initialize versioning system with optional config file"""
    global versioning_system
    
    if config_path:
        versioning_system = VersioningSystem.load_from_config(config_path)
    else:
        versioning_system = VersioningSystem()
    
    return versioning_system