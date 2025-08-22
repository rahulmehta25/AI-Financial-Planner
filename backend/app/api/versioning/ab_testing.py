"""
A/B Testing and Gradual Migration Support for API Versions
"""

import logging
import hashlib
import random
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
from pathlib import Path

from .models import ABTestConfig, APIVersion, VersionMetrics
from .manager import VersionManager

logger = logging.getLogger(__name__)


class TestStatus(str, Enum):
    """A/B test status"""
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class SegmentType(str, Enum):
    """User segment types"""
    PERCENTAGE = "percentage"
    USER_ID = "user_id"
    GEOGRAPHIC = "geographic"
    DEVICE_TYPE = "device_type"
    CLIENT_VERSION = "client_version"
    CUSTOM = "custom"


@dataclass
class TestMetrics:
    """Metrics for A/B test analysis"""
    test_name: str
    variant: str  # "control" or "treatment"
    total_requests: int = 0
    unique_users: int = 0
    success_rate: float = 0.0
    avg_response_time_ms: float = 0.0
    error_rate: float = 0.0
    conversion_rate: float = 0.0  # For business metrics
    last_updated: datetime = field(default_factory=datetime.utcnow)
    
    def update_metrics(self, requests: int, response_time: float, errors: int, conversions: int = 0):
        """Update metrics with new data"""
        self.total_requests += requests
        
        # Update average response time
        if self.total_requests > 0:
            total_time = self.avg_response_time_ms * (self.total_requests - requests)
            self.avg_response_time_ms = (total_time + response_time) / self.total_requests
        
        # Update error rate
        self.error_rate = errors / self.total_requests if self.total_requests > 0 else 0.0
        
        # Update success rate
        self.success_rate = 1.0 - self.error_rate
        
        # Update conversion rate
        if conversions > 0:
            self.conversion_rate = conversions / self.total_requests if self.total_requests > 0 else 0.0
        
        self.last_updated = datetime.utcnow()


@dataclass
class UserSegment:
    """User segment definition for A/B testing"""
    name: str
    segment_type: SegmentType
    criteria: Dict[str, Any]
    description: str = ""
    
    def matches_user(self, user_context: Dict[str, Any]) -> bool:
        """Check if user matches this segment"""
        
        if self.segment_type == SegmentType.PERCENTAGE:
            # Hash-based percentage routing
            user_id = user_context.get('user_id', '')
            if user_id:
                hash_value = int(hashlib.md5(f"{user_id}{self.name}".encode()).hexdigest()[:8], 16)
                percentage = (hash_value % 100) + 1
                return percentage <= self.criteria.get('percentage', 0)
        
        elif self.segment_type == SegmentType.USER_ID:
            # Specific user IDs
            user_id = user_context.get('user_id', '')
            return user_id in self.criteria.get('user_ids', [])
        
        elif self.segment_type == SegmentType.GEOGRAPHIC:
            # Geographic criteria
            user_country = user_context.get('country', '')
            user_region = user_context.get('region', '')
            
            allowed_countries = self.criteria.get('countries', [])
            allowed_regions = self.criteria.get('regions', [])
            
            return (not allowed_countries or user_country in allowed_countries) and \
                   (not allowed_regions or user_region in allowed_regions)
        
        elif self.segment_type == SegmentType.DEVICE_TYPE:
            # Device type criteria
            device_type = user_context.get('device_type', '')
            return device_type in self.criteria.get('device_types', [])
        
        elif self.segment_type == SegmentType.CLIENT_VERSION:
            # Client version criteria
            client_version = user_context.get('client_version', '')
            min_version = self.criteria.get('min_version')
            max_version = self.criteria.get('max_version')
            
            if min_version and client_version < min_version:
                return False
            if max_version and client_version > max_version:
                return False
            return True
        
        elif self.segment_type == SegmentType.CUSTOM:
            # Custom criteria evaluation
            for key, expected_value in self.criteria.items():
                user_value = user_context.get(key)
                if isinstance(expected_value, list):
                    if user_value not in expected_value:
                        return False
                else:
                    if user_value != expected_value:
                        return False
            return True
        
        return False


@dataclass
class GradualRollout:
    """Gradual rollout configuration"""
    test_name: str
    target_version: str
    rollout_schedule: List[Dict[str, Any]] = field(default_factory=list)
    current_percentage: float = 0.0
    max_percentage: float = 100.0
    success_criteria: Dict[str, float] = field(default_factory=dict)
    rollback_criteria: Dict[str, float] = field(default_factory=dict)
    auto_advance: bool = True
    
    def should_advance_rollout(self, metrics: TestMetrics) -> bool:
        """Check if rollout should advance to next stage"""
        if not self.auto_advance:
            return False
        
        # Check success criteria
        for metric_name, threshold in self.success_criteria.items():
            metric_value = getattr(metrics, metric_name, 0)
            if metric_value < threshold:
                return False
        
        return True
    
    def should_rollback(self, metrics: TestMetrics) -> bool:
        """Check if rollout should be rolled back"""
        
        # Check rollback criteria
        for metric_name, threshold in self.rollback_criteria.items():
            metric_value = getattr(metrics, metric_name, 0)
            if metric_value > threshold:  # Assuming higher is worse for rollback criteria
                return True
        
        return False


class ABTestManager:
    """Manage A/B tests and gradual rollouts"""
    
    def __init__(self, version_manager: VersionManager, config_path: str = "config/ab_tests.json"):
        self.version_manager = version_manager
        self.config_path = config_path
        
        # Test data
        self.tests: Dict[str, ABTestConfig] = {}
        self.test_metrics: Dict[str, Dict[str, TestMetrics]] = {}  # {test_name: {variant: metrics}}
        self.user_segments: Dict[str, UserSegment] = {}
        self.gradual_rollouts: Dict[str, GradualRollout] = {}
        self.user_assignments: Dict[str, Dict[str, str]] = {}  # {user_id: {test_name: variant}}
        
        self._load_configuration()
    
    def _load_configuration(self):
        """Load A/B test configuration"""
        config_file = Path(self.config_path)
        
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    self._load_from_config(config)
                logger.info(f"Loaded A/B test configuration from {self.config_path}")
            except Exception as e:
                logger.error(f"Failed to load A/B test config: {e}")
                self._load_default_configuration()
        else:
            self._load_default_configuration()
    
    def _load_default_configuration(self):
        """Load default A/B test configuration"""
        
        # Default user segments
        default_segments = [
            UserSegment(
                name="beta_users",
                segment_type=SegmentType.PERCENTAGE,
                criteria={"percentage": 10},
                description="10% of users for beta testing"
            ),
            UserSegment(
                name="mobile_users",
                segment_type=SegmentType.DEVICE_TYPE,
                criteria={"device_types": ["mobile", "tablet"]},
                description="Mobile and tablet users"
            ),
            UserSegment(
                name="us_users",
                segment_type=SegmentType.GEOGRAPHIC,
                criteria={"countries": ["US"]},
                description="Users from United States"
            )
        ]
        
        for segment in default_segments:
            self.user_segments[segment.name] = segment
        
        # Default A/B test
        default_test = ABTestConfig(
            test_name="api_v2_migration",
            from_version="1.0.0",
            to_version="2.0.0",
            traffic_percentage=10.0,
            user_segments=["beta_users"],
            metrics_to_track=["response_time", "error_rate", "success_rate"],
            success_criteria={
                "error_rate_threshold": 0.05,
                "response_time_threshold": 1000
            },
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow() + timedelta(days=30),
            is_active=True
        )
        
        self.tests[default_test.test_name] = default_test
        
        # Initialize metrics for default test
        self.test_metrics[default_test.test_name] = {
            "control": TestMetrics(test_name=default_test.test_name, variant="control"),
            "treatment": TestMetrics(test_name=default_test.test_name, variant="treatment")
        }
        
        logger.info("Loaded default A/B test configuration")
    
    def _load_from_config(self, config: dict):
        """Load configuration from dictionary"""
        
        # Load user segments
        if 'user_segments' in config:
            for segment_data in config['user_segments']:
                segment = UserSegment(**segment_data)
                self.user_segments[segment.name] = segment
        
        # Load A/B tests
        if 'ab_tests' in config:
            for test_data in config['ab_tests']:
                test = ABTestConfig(**test_data)
                self.tests[test.test_name] = test
                
                # Initialize metrics
                self.test_metrics[test.test_name] = {
                    "control": TestMetrics(test_name=test.test_name, variant="control"),
                    "treatment": TestMetrics(test_name=test.test_name, variant="treatment")
                }
        
        # Load gradual rollouts
        if 'gradual_rollouts' in config:
            for rollout_data in config['gradual_rollouts']:
                rollout = GradualRollout(**rollout_data)
                self.gradual_rollouts[rollout.test_name] = rollout
    
    def create_ab_test(
        self,
        test_name: str,
        from_version: str,
        to_version: str,
        traffic_percentage: float,
        user_segments: List[str] = None,
        duration_days: int = 30,
        success_criteria: Dict[str, Any] = None
    ) -> bool:
        """Create a new A/B test"""
        
        if test_name in self.tests:
            logger.error(f"A/B test {test_name} already exists")
            return False
        
        # Validate versions
        if not self.version_manager.get_version(from_version):
            logger.error(f"From version {from_version} not found")
            return False
        
        if not self.version_manager.get_version(to_version):
            logger.error(f"To version {to_version} not found")
            return False
        
        # Create test configuration
        test = ABTestConfig(
            test_name=test_name,
            from_version=from_version,
            to_version=to_version,
            traffic_percentage=traffic_percentage,
            user_segments=user_segments or [],
            metrics_to_track=["response_time", "error_rate", "success_rate"],
            success_criteria=success_criteria or {},
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow() + timedelta(days=duration_days),
            is_active=True
        )
        
        self.tests[test_name] = test
        
        # Initialize metrics
        self.test_metrics[test_name] = {
            "control": TestMetrics(test_name=test_name, variant="control"),
            "treatment": TestMetrics(test_name=test_name, variant="treatment")
        }
        
        # Add to version manager
        self.version_manager.add_ab_test(test)
        
        logger.info(f"Created A/B test: {test_name}")
        return True
    
    def assign_user_to_test(self, user_id: str, user_context: Dict[str, Any], test_name: str) -> str:
        """Assign user to A/B test variant"""
        
        # Check if user is already assigned
        if user_id in self.user_assignments and test_name in self.user_assignments[user_id]:
            return self.user_assignments[user_id][test_name]
        
        test = self.tests.get(test_name)
        if not test or not test.is_active:
            return "control"
        
        # Check if test is within date range
        now = datetime.utcnow()
        if now < test.start_date or now > test.end_date:
            return "control"
        
        # Check user segments
        if test.user_segments:
            matches_segment = False
            for segment_name in test.user_segments:
                segment = self.user_segments.get(segment_name)
                if segment and segment.matches_user(user_context):
                    matches_segment = True
                    break
            
            if not matches_segment:
                return "control"
        
        # Assign variant based on traffic percentage
        variant = "treatment" if test.should_use_new_version(user_id) else "control"
        
        # Store assignment
        if user_id not in self.user_assignments:
            self.user_assignments[user_id] = {}
        self.user_assignments[user_id][test_name] = variant
        
        return variant
    
    def get_version_for_user(
        self, 
        user_id: str, 
        user_context: Dict[str, Any], 
        default_version: str
    ) -> str:
        """Get the appropriate API version for a user considering A/B tests"""
        
        # Check all active tests
        for test_name, test in self.tests.items():
            if not test.is_active or test.from_version != default_version:
                continue
            
            variant = self.assign_user_to_test(user_id, user_context, test_name)
            
            if variant == "treatment":
                # Record assignment for metrics
                self._record_user_assignment(user_id, test_name, variant)
                return test.to_version
        
        # Check gradual rollouts
        for rollout_name, rollout in self.gradual_rollouts.items():
            if rollout.target_version == default_version:
                continue
            
            # Check if user should be included in rollout
            if self._should_include_in_rollout(user_id, user_context, rollout):
                return rollout.target_version
        
        return default_version
    
    def _record_user_assignment(self, user_id: str, test_name: str, variant: str):
        """Record user assignment for analytics"""
        # This would typically be sent to analytics system
        logger.debug(f"User {user_id} assigned to {test_name} variant: {variant}")
    
    def _should_include_in_rollout(
        self, 
        user_id: str, 
        user_context: Dict[str, Any], 
        rollout: GradualRollout
    ) -> bool:
        """Check if user should be included in gradual rollout"""
        
        # Use hash-based assignment for consistency
        hash_value = int(hashlib.md5(f"{user_id}{rollout.test_name}".encode()).hexdigest()[:8], 16)
        percentage = (hash_value % 100) + 1
        
        return percentage <= rollout.current_percentage
    
    def record_test_metrics(
        self,
        test_name: str,
        variant: str,
        user_id: str,
        response_time_ms: float,
        success: bool,
        conversion: bool = False
    ):
        """Record metrics for A/B test"""
        
        if test_name not in self.test_metrics:
            return
        
        if variant not in self.test_metrics[test_name]:
            return
        
        metrics = self.test_metrics[test_name][variant]
        
        # Update metrics
        errors = 0 if success else 1
        conversions = 1 if conversion else 0
        
        metrics.update_metrics(1, response_time_ms, errors, conversions)
        
        # Track unique users (simplified - in production, use proper user tracking)
        metrics.unique_users += 1
    
    def analyze_test_results(self, test_name: str) -> Dict[str, Any]:
        """Analyze A/B test results"""
        
        if test_name not in self.test_metrics:
            return {'error': 'Test not found'}
        
        control_metrics = self.test_metrics[test_name]["control"]
        treatment_metrics = self.test_metrics[test_name]["treatment"]
        
        # Calculate statistical significance (simplified)
        sample_size_control = control_metrics.total_requests
        sample_size_treatment = treatment_metrics.total_requests
        
        if sample_size_control < 100 or sample_size_treatment < 100:
            significance = "insufficient_data"
        else:
            # Simplified significance calculation
            control_rate = control_metrics.success_rate
            treatment_rate = treatment_metrics.success_rate
            
            difference = abs(treatment_rate - control_rate)
            
            if difference > 0.05:  # 5% difference threshold
                significance = "significant"
            elif difference > 0.02:  # 2% difference threshold
                significance = "marginal"
            else:
                significance = "not_significant"
        
        # Determine winner
        winner = "control"
        if treatment_metrics.success_rate > control_metrics.success_rate:
            if treatment_metrics.avg_response_time_ms <= control_metrics.avg_response_time_ms * 1.1:  # Allow 10% response time increase
                winner = "treatment"
        
        analysis = {
            'test_name': test_name,
            'analysis_date': datetime.utcnow().isoformat(),
            'significance': significance,
            'winner': winner,
            'control_metrics': {
                'total_requests': control_metrics.total_requests,
                'unique_users': control_metrics.unique_users,
                'success_rate': control_metrics.success_rate,
                'avg_response_time_ms': control_metrics.avg_response_time_ms,
                'error_rate': control_metrics.error_rate,
                'conversion_rate': control_metrics.conversion_rate
            },
            'treatment_metrics': {
                'total_requests': treatment_metrics.total_requests,
                'unique_users': treatment_metrics.unique_users,
                'success_rate': treatment_metrics.success_rate,
                'avg_response_time_ms': treatment_metrics.avg_response_time_ms,
                'error_rate': treatment_metrics.error_rate,
                'conversion_rate': treatment_metrics.conversion_rate
            },
            'improvements': {
                'success_rate_change': treatment_metrics.success_rate - control_metrics.success_rate,
                'response_time_change': treatment_metrics.avg_response_time_ms - control_metrics.avg_response_time_ms,
                'error_rate_change': treatment_metrics.error_rate - control_metrics.error_rate,
                'conversion_rate_change': treatment_metrics.conversion_rate - control_metrics.conversion_rate
            },
            'recommendations': self._generate_test_recommendations(
                control_metrics, treatment_metrics, significance, winner
            )
        }
        
        return analysis
    
    def _generate_test_recommendations(
        self,
        control_metrics: TestMetrics,
        treatment_metrics: TestMetrics,
        significance: str,
        winner: str
    ) -> List[str]:
        """Generate recommendations based on test results"""
        
        recommendations = []
        
        if significance == "insufficient_data":
            recommendations.append("Continue test to gather more data")
            recommendations.append("Consider increasing traffic allocation if feasible")
        
        elif significance == "not_significant":
            recommendations.append("No significant difference detected")
            recommendations.append("Consider longer test duration or different metrics")
        
        elif winner == "treatment":
            recommendations.append("Treatment version shows improvement")
            if significance == "significant":
                recommendations.append("Consider full rollout to treatment version")
            else:
                recommendations.append("Continue monitoring before full rollout")
        
        else:  # winner == "control"
            recommendations.append("Control version performs better")
            recommendations.append("Investigate issues with treatment version")
            recommendations.append("Consider reverting or fixing treatment version")
        
        # Specific metric recommendations
        if treatment_metrics.error_rate > control_metrics.error_rate * 1.5:
            recommendations.append("High error rate in treatment - investigate immediately")
        
        if treatment_metrics.avg_response_time_ms > control_metrics.avg_response_time_ms * 1.3:
            recommendations.append("Significant response time increase in treatment")
        
        return recommendations
    
    def create_gradual_rollout(
        self,
        test_name: str,
        target_version: str,
        initial_percentage: float = 5.0,
        max_percentage: float = 100.0,
        success_criteria: Dict[str, float] = None,
        rollback_criteria: Dict[str, float] = None
    ) -> bool:
        """Create a gradual rollout plan"""
        
        if test_name in self.gradual_rollouts:
            logger.error(f"Gradual rollout {test_name} already exists")
            return False
        
        # Default rollout schedule (5%, 10%, 25%, 50%, 100%)
        rollout_schedule = [
            {"percentage": 5.0, "duration_hours": 24},
            {"percentage": 10.0, "duration_hours": 48},
            {"percentage": 25.0, "duration_hours": 72},
            {"percentage": 50.0, "duration_hours": 96},
            {"percentage": 100.0, "duration_hours": 0}
        ]
        
        rollout = GradualRollout(
            test_name=test_name,
            target_version=target_version,
            rollout_schedule=rollout_schedule,
            current_percentage=initial_percentage,
            max_percentage=max_percentage,
            success_criteria=success_criteria or {
                "error_rate": 0.05,
                "success_rate": 0.95
            },
            rollback_criteria=rollback_criteria or {
                "error_rate": 0.10,
                "avg_response_time_ms": 5000
            },
            auto_advance=True
        )
        
        self.gradual_rollouts[test_name] = rollout
        
        # Initialize metrics
        if test_name not in self.test_metrics:
            self.test_metrics[test_name] = {
                "control": TestMetrics(test_name=test_name, variant="control"),
                "treatment": TestMetrics(test_name=test_name, variant="treatment")
            }
        
        logger.info(f"Created gradual rollout: {test_name}")
        return True
    
    def advance_rollout(self, test_name: str) -> bool:
        """Advance gradual rollout to next stage"""
        
        rollout = self.gradual_rollouts.get(test_name)
        if not rollout:
            return False
        
        # Find next stage
        next_stage = None
        for stage in rollout.rollout_schedule:
            if stage["percentage"] > rollout.current_percentage:
                next_stage = stage
                break
        
        if not next_stage:
            logger.info(f"Rollout {test_name} already at maximum percentage")
            return False
        
        # Check if we should advance based on metrics
        if test_name in self.test_metrics:
            treatment_metrics = self.test_metrics[test_name]["treatment"]
            
            if not rollout.should_advance_rollout(treatment_metrics):
                logger.warning(f"Rollout {test_name} does not meet advancement criteria")
                return False
            
            if rollout.should_rollback(treatment_metrics):
                logger.error(f"Rollout {test_name} meets rollback criteria - not advancing")
                return False
        
        # Advance to next stage
        rollout.current_percentage = next_stage["percentage"]
        
        logger.info(f"Advanced rollout {test_name} to {rollout.current_percentage}%")
        return True
    
    def rollback_rollout(self, test_name: str, target_percentage: float = 0.0) -> bool:
        """Rollback gradual rollout"""
        
        rollout = self.gradual_rollouts.get(test_name)
        if not rollout:
            return False
        
        if target_percentage >= rollout.current_percentage:
            logger.error(f"Target percentage must be less than current percentage")
            return False
        
        rollout.current_percentage = target_percentage
        
        logger.warning(f"Rolled back rollout {test_name} to {target_percentage}%")
        return True
    
    def get_active_tests(self) -> List[ABTestConfig]:
        """Get all active A/B tests"""
        now = datetime.utcnow()
        
        return [
            test for test in self.tests.values()
            if test.is_active and test.start_date <= now <= test.end_date
        ]
    
    def get_test_dashboard(self) -> Dict[str, Any]:
        """Get dashboard data for all tests"""
        
        dashboard = {
            'timestamp': datetime.utcnow().isoformat(),
            'active_tests': len(self.get_active_tests()),
            'total_tests': len(self.tests),
            'active_rollouts': len([r for r in self.gradual_rollouts.values() if r.current_percentage > 0]),
            'tests': [],
            'rollouts': []
        }
        
        # Add test data
        for test_name, test in self.tests.items():
            test_data = {
                'name': test_name,
                'status': 'active' if test.is_active else 'inactive',
                'from_version': test.from_version,
                'to_version': test.to_version,
                'traffic_percentage': test.traffic_percentage,
                'start_date': test.start_date.isoformat(),
                'end_date': test.end_date.isoformat(),
                'metrics': {}
            }
            
            # Add metrics if available
            if test_name in self.test_metrics:
                for variant, metrics in self.test_metrics[test_name].items():
                    test_data['metrics'][variant] = {
                        'total_requests': metrics.total_requests,
                        'success_rate': metrics.success_rate,
                        'avg_response_time_ms': metrics.avg_response_time_ms,
                        'error_rate': metrics.error_rate
                    }
            
            dashboard['tests'].append(test_data)
        
        # Add rollout data
        for rollout_name, rollout in self.gradual_rollouts.items():
            dashboard['rollouts'].append({
                'name': rollout_name,
                'target_version': rollout.target_version,
                'current_percentage': rollout.current_percentage,
                'max_percentage': rollout.max_percentage,
                'auto_advance': rollout.auto_advance
            })
        
        return dashboard
    
    def export_test_results(self, output_dir: str = "reports/ab_tests") -> Dict[str, str]:
        """Export A/B test results to files"""
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        exported_files = {}
        
        # Export individual test results
        for test_name in self.tests:
            analysis = self.analyze_test_results(test_name)
            
            if 'error' not in analysis:
                test_file = output_path / f"{test_name}_results.json"
                with open(test_file, 'w') as f:
                    json.dump(analysis, f, indent=2)
                
                exported_files[test_name] = str(test_file)
        
        # Export dashboard
        dashboard = self.get_test_dashboard()
        dashboard_file = output_path / "dashboard.json"
        with open(dashboard_file, 'w') as f:
            json.dump(dashboard, f, indent=2)
        
        exported_files["dashboard"] = str(dashboard_file)
        
        # Export configuration
        config = {
            'ab_tests': [test.dict() for test in self.tests.values()],
            'user_segments': [
                {
                    'name': segment.name,
                    'segment_type': segment.segment_type.value,
                    'criteria': segment.criteria,
                    'description': segment.description
                }
                for segment in self.user_segments.values()
            ],
            'gradual_rollouts': [
                {
                    'test_name': rollout.test_name,
                    'target_version': rollout.target_version,
                    'rollout_schedule': rollout.rollout_schedule,
                    'current_percentage': rollout.current_percentage,
                    'max_percentage': rollout.max_percentage,
                    'success_criteria': rollout.success_criteria,
                    'rollback_criteria': rollout.rollback_criteria,
                    'auto_advance': rollout.auto_advance
                }
                for rollout in self.gradual_rollouts.values()
            ]
        }
        
        config_file = output_path / "ab_test_config.json"
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        exported_files["config"] = str(config_file)
        
        logger.info(f"Exported A/B test results to {output_path}")
        return exported_files
    
    def save_configuration(self):
        """Save current configuration to file"""
        config = {
            'ab_tests': [test.dict() for test in self.tests.values()],
            'user_segments': [
                {
                    'name': segment.name,
                    'segment_type': segment.segment_type.value,
                    'criteria': segment.criteria,
                    'description': segment.description
                }
                for segment in self.user_segments.values()
            ],
            'gradual_rollouts': [
                {
                    'test_name': rollout.test_name,
                    'target_version': rollout.target_version,
                    'rollout_schedule': rollout.rollout_schedule,
                    'current_percentage': rollout.current_percentage,
                    'max_percentage': rollout.max_percentage,
                    'success_criteria': rollout.success_criteria,
                    'rollback_criteria': rollout.rollback_criteria,
                    'auto_advance': rollout.auto_advance
                }
                for rollout in self.gradual_rollouts.values()
            ]
        }
        
        config_file = Path(self.config_path)
        config_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        logger.info(f"Saved A/B test configuration to {self.config_path}")