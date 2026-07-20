"""
Backward Compatibility Management System
"""

import logging
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
from semantic_version import Version
import json

from .models import VersionCompatibility, CompatibilityLevel, APIVersion
from .manager import VersionManager

logger = logging.getLogger(__name__)


class CompatibilityIssueType(str, Enum):
    """Types of compatibility issues"""
    BREAKING_CHANGE = "breaking_change"
    DEPRECATED_FEATURE = "deprecated_feature"
    REMOVED_FEATURE = "removed_feature"
    SCHEMA_CHANGE = "schema_change"
    BEHAVIOR_CHANGE = "behavior_change"
    SECURITY_CHANGE = "security_change"


class ImpactLevel(str, Enum):
    """Impact levels for compatibility issues"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class CompatibilityIssue:
    """Individual compatibility issue"""
    issue_type: CompatibilityIssueType
    component: str  # endpoint, parameter, response_field, etc.
    description: str
    impact_level: ImpactLevel
    introduced_in: str  # version where issue was introduced
    affects_versions: List[str] = field(default_factory=list)
    workaround: Optional[str] = None
    migration_steps: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'issue_type': self.issue_type.value,
            'component': self.component,
            'description': self.description,
            'impact_level': self.impact_level.value,
            'introduced_in': self.introduced_in,
            'affects_versions': self.affects_versions,
            'workaround': self.workaround,
            'migration_steps': self.migration_steps
        }


@dataclass 
class SchemaCompatibility:
    """Schema compatibility information"""
    field_name: str
    old_type: str
    new_type: str
    change_type: str  # added, removed, modified, deprecated
    required: bool = False
    default_value: Any = None
    migration_required: bool = False
    
    @property
    def is_breaking(self) -> bool:
        """Check if this schema change is breaking"""
        if self.change_type == "removed" and self.required:
            return True
        if self.change_type == "modified" and self.old_type != self.new_type:
            # Type changes are generally breaking
            return True
        return False


class CompatibilityAnalyzer:
    """Analyze compatibility between API versions"""
    
    def __init__(self, version_manager: VersionManager):
        self.version_manager = version_manager
        self.compatibility_rules: Dict[str, List[CompatibilityIssue]] = {}
        self.schema_changes: Dict[str, List[SchemaCompatibility]] = {}
        
    def analyze_compatibility(
        self, 
        from_version: str, 
        to_version: str
    ) -> Dict[str, Any]:
        """Analyze compatibility between two versions"""
        
        from_version_obj = self.version_manager.get_version(from_version)
        to_version_obj = self.version_manager.get_version(to_version)
        
        if not from_version_obj or not to_version_obj:
            return {'error': 'One or both versions not found'}
        
        # Determine compatibility level
        compatibility_level = self._determine_compatibility_level(from_version, to_version)
        
        # Find compatibility issues
        issues = self._find_compatibility_issues(from_version, to_version)
        
        # Analyze schema changes
        schema_changes = self._analyze_schema_changes(from_version, to_version)
        
        # Calculate compatibility score
        score = self._calculate_compatibility_score(issues, schema_changes)
        
        analysis = {
            'from_version': from_version,
            'to_version': to_version,
            'compatibility_level': compatibility_level.value,
            'compatibility_score': score,
            'is_breaking': compatibility_level == CompatibilityLevel.BREAKING,
            'migration_required': score < 80.0 or compatibility_level == CompatibilityLevel.BREAKING,
            'issues': [issue.to_dict() for issue in issues],
            'schema_changes': [
                {
                    'field': change.field_name,
                    'old_type': change.old_type,
                    'new_type': change.new_type,
                    'change_type': change.change_type,
                    'is_breaking': change.is_breaking,
                    'migration_required': change.migration_required
                }
                for change in schema_changes
            ],
            'migration_complexity': self._assess_migration_complexity(issues, schema_changes),
            'recommended_strategy': self._recommend_migration_strategy(compatibility_level, score, issues)
        }
        
        return analysis
    
    def _determine_compatibility_level(self, from_version: str, to_version: str) -> CompatibilityLevel:
        """Determine compatibility level between versions"""
        try:
            from_sem = Version(from_version)
            to_sem = Version(to_version)
            
            # Major version changes are generally breaking
            if to_sem.major > from_sem.major:
                return CompatibilityLevel.BREAKING
            
            # Minor version changes can add features but maintain compatibility
            if to_sem.minor > from_sem.minor:
                # Check for breaking changes in the version metadata
                to_version_obj = self.version_manager.get_version(to_version)
                if to_version_obj and to_version_obj.breaking_changes:
                    return CompatibilityLevel.BREAKING
                return CompatibilityLevel.FEATURE
            
            # Patch versions should be compatible
            if to_sem.patch > from_sem.patch:
                return CompatibilityLevel.PATCH
            
            # Same version
            if to_sem == from_sem:
                return CompatibilityLevel.COMPATIBLE
            
            # Downgrade (generally not recommended)
            return CompatibilityLevel.BREAKING
            
        except ValueError:
            # Invalid version format - assume breaking
            return CompatibilityLevel.BREAKING
    
    def _find_compatibility_issues(self, from_version: str, to_version: str) -> List[CompatibilityIssue]:
        """Find specific compatibility issues between versions"""
        issues = []
        
        # Get version objects
        from_version_obj = self.version_manager.get_version(from_version)
        to_version_obj = self.version_manager.get_version(to_version)
        
        if not from_version_obj or not to_version_obj:
            return issues
        
        # Check for breaking changes documented in the target version
        if to_version_obj.breaking_changes:
            for breaking_change in to_version_obj.breaking_changes:
                issues.append(CompatibilityIssue(
                    issue_type=CompatibilityIssueType.BREAKING_CHANGE,
                    component="api",
                    description=breaking_change,
                    impact_level=ImpactLevel.HIGH,
                    introduced_in=to_version,
                    affects_versions=[from_version]
                ))
        
        # Check endpoints availability
        from_endpoints = self.version_manager.get_endpoints_for_version(from_version)
        to_endpoints = self.version_manager.get_endpoints_for_version(to_version)
        
        from_paths = {f"{ep.path}:{','.join(ep.methods)}" for ep in from_endpoints}
        to_paths = {f"{ep.path}:{','.join(ep.methods)}" for ep in to_endpoints}
        
        # Find removed endpoints
        removed_endpoints = from_paths - to_paths
        for endpoint in removed_endpoints:
            issues.append(CompatibilityIssue(
                issue_type=CompatibilityIssueType.REMOVED_FEATURE,
                component="endpoint",
                description=f"Endpoint {endpoint} has been removed",
                impact_level=ImpactLevel.CRITICAL,
                introduced_in=to_version,
                affects_versions=[from_version],
                migration_steps=[
                    f"Update client code to use alternative endpoint",
                    f"Remove references to {endpoint}",
                    f"Test application without this endpoint"
                ]
            ))
        
        # Find deprecated endpoints
        for endpoint in to_endpoints:
            if endpoint.is_deprecated_in_version(to_version):
                issues.append(CompatibilityIssue(
                    issue_type=CompatibilityIssueType.DEPRECATED_FEATURE,
                    component="endpoint",
                    description=f"Endpoint {endpoint.path} is deprecated",
                    impact_level=ImpactLevel.MEDIUM,
                    introduced_in=to_version,
                    workaround="Use alternative endpoint if available",
                    migration_steps=[
                        f"Plan migration away from {endpoint.path}",
                        f"Update client code before endpoint removal"
                    ]
                ))
        
        # Add predefined compatibility rules
        version_issues = self.compatibility_rules.get(to_version, [])
        for issue in version_issues:
            if from_version in issue.affects_versions or not issue.affects_versions:
                issues.append(issue)
        
        return issues
    
    def _analyze_schema_changes(self, from_version: str, to_version: str) -> List[SchemaCompatibility]:
        """Analyze schema changes between versions"""
        # This would typically analyze API schemas (OpenAPI specs)
        # For now, return predefined schema changes
        return self.schema_changes.get(f"{from_version}:{to_version}", [])
    
    def _calculate_compatibility_score(
        self, 
        issues: List[CompatibilityIssue], 
        schema_changes: List[SchemaCompatibility]
    ) -> float:
        """Calculate compatibility score (0-100)"""
        
        if not issues and not schema_changes:
            return 100.0
        
        score = 100.0
        
        # Deduct points for issues
        for issue in issues:
            if issue.impact_level == ImpactLevel.CRITICAL:
                score -= 30.0
            elif issue.impact_level == ImpactLevel.HIGH:
                score -= 20.0
            elif issue.impact_level == ImpactLevel.MEDIUM:
                score -= 10.0
            else:  # LOW
                score -= 5.0
            
            # Additional deductions for breaking changes
            if issue.issue_type == CompatibilityIssueType.BREAKING_CHANGE:
                score -= 20.0
            elif issue.issue_type == CompatibilityIssueType.REMOVED_FEATURE:
                score -= 15.0
        
        # Deduct points for schema changes
        for change in schema_changes:
            if change.is_breaking:
                score -= 15.0
            elif change.migration_required:
                score -= 10.0
            else:
                score -= 5.0
        
        return max(0.0, score)
    
    def _assess_migration_complexity(
        self, 
        issues: List[CompatibilityIssue], 
        schema_changes: List[SchemaCompatibility]
    ) -> str:
        """Assess migration complexity"""
        
        breaking_issues = sum(1 for issue in issues if issue.issue_type == CompatibilityIssueType.BREAKING_CHANGE)
        critical_issues = sum(1 for issue in issues if issue.impact_level == ImpactLevel.CRITICAL)
        breaking_schema_changes = sum(1 for change in schema_changes if change.is_breaking)
        
        total_complexity_points = breaking_issues * 3 + critical_issues * 2 + breaking_schema_changes * 2
        
        if total_complexity_points >= 10:
            return "high"
        elif total_complexity_points >= 5:
            return "medium"
        elif total_complexity_points > 0:
            return "low"
        else:
            return "minimal"
    
    def _recommend_migration_strategy(
        self, 
        compatibility_level: CompatibilityLevel, 
        score: float, 
        issues: List[CompatibilityIssue]
    ) -> Dict[str, Any]:
        """Recommend migration strategy"""
        
        strategy = {
            'approach': 'direct',
            'recommended_steps': [],
            'timeline': 'immediate',
            'risk_level': 'low'
        }
        
        if compatibility_level == CompatibilityLevel.BREAKING or score < 50:
            strategy['approach'] = 'staged'
            strategy['timeline'] = 'extended'
            strategy['risk_level'] = 'high'
            strategy['recommended_steps'] = [
                'Create detailed migration plan',
                'Set up parallel testing environment',
                'Implement gradual rollout strategy',
                'Monitor for issues during migration',
                'Have rollback plan ready'
            ]
        elif score < 80:
            strategy['approach'] = 'careful'
            strategy['timeline'] = 'moderate'
            strategy['risk_level'] = 'medium'
            strategy['recommended_steps'] = [
                'Review all breaking changes',
                'Update client code incrementally',
                'Test thoroughly before deployment',
                'Monitor application performance'
            ]
        else:
            strategy['recommended_steps'] = [
                'Update version headers',
                'Test basic functionality',
                'Deploy with monitoring'
            ]
        
        # Add specific steps based on issues
        critical_issues = [issue for issue in issues if issue.impact_level == ImpactLevel.CRITICAL]
        if critical_issues:
            strategy['recommended_steps'].insert(0, 'Address critical compatibility issues first')
        
        return strategy
    
    def add_compatibility_rule(self, version: str, issue: CompatibilityIssue):
        """Add a compatibility rule for a specific version"""
        if version not in self.compatibility_rules:
            self.compatibility_rules[version] = []
        self.compatibility_rules[version].append(issue)
    
    def add_schema_change(self, version_pair: str, change: SchemaCompatibility):
        """Add a schema change for a version pair (from:to)"""
        if version_pair not in self.schema_changes:
            self.schema_changes[version_pair] = []
        self.schema_changes[version_pair].append(change)
    
    def generate_migration_guide(self, from_version: str, to_version: str) -> Dict[str, Any]:
        """Generate detailed migration guide"""
        
        analysis = self.analyze_compatibility(from_version, to_version)
        
        if 'error' in analysis:
            return analysis
        
        guide = {
            'title': f'Migration Guide: v{from_version} to v{to_version}',
            'overview': {
                'compatibility_level': analysis['compatibility_level'],
                'migration_required': analysis['migration_required'],
                'complexity': analysis['migration_complexity'],
                'estimated_effort': self._estimate_migration_effort(analysis)
            },
            'pre_migration': {
                'checklist': [
                    'Backup current implementation',
                    'Review all breaking changes',
                    'Set up testing environment',
                    'Identify affected components'
                ],
                'requirements': self._get_migration_requirements(analysis)
            },
            'step_by_step': self._generate_migration_steps(analysis),
            'testing': {
                'test_categories': [
                    'API endpoint compatibility',
                    'Request/response format validation',
                    'Authentication flow testing',
                    'Error handling verification',
                    'Performance benchmarking'
                ],
                'test_scripts': self._generate_test_scripts(from_version, to_version)
            },
            'rollback': {
                'strategy': 'Version pinning and traffic routing',
                'steps': [
                    'Revert version headers to previous version',
                    'Update gateway routing configuration',
                    'Monitor for stability',
                    'Document rollback reasons'
                ]
            },
            'support': {
                'documentation': f'/docs/migration/v{from_version}-to-v{to_version}',
                'examples': f'/examples/migration/v{from_version}-v{to_version}',
                'faq': f'/docs/faq/migration-v{to_version}'
            }
        }
        
        return guide
    
    def _estimate_migration_effort(self, analysis: Dict[str, Any]) -> str:
        """Estimate migration effort"""
        complexity = analysis['migration_complexity']
        num_issues = len(analysis['issues'])
        
        if complexity == 'high' or num_issues > 10:
            return 'high (2-4 weeks)'
        elif complexity == 'medium' or num_issues > 5:
            return 'medium (1-2 weeks)'
        elif complexity == 'low' or num_issues > 0:
            return 'low (2-5 days)'
        else:
            return 'minimal (1-2 days)'
    
    def _get_migration_requirements(self, analysis: Dict[str, Any]) -> List[str]:
        """Get migration requirements"""
        requirements = [
            'Access to development/staging environment',
            'API documentation for both versions',
            'Test suite for validation'
        ]
        
        if analysis['is_breaking']:
            requirements.extend([
                'Code modification capabilities',
                'Extended testing timeline',
                'Rollback plan and procedures'
            ])
        
        return requirements
    
    def _generate_migration_steps(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate step-by-step migration instructions"""
        steps = []
        
        # Step 1: Preparation
        steps.append({
            'step': 1,
            'title': 'Preparation',
            'description': 'Prepare for migration',
            'actions': [
                'Review compatibility analysis',
                'Set up testing environment',
                'Backup current configuration'
            ],
            'validation': 'Environment is ready for testing'
        })
        
        # Step 2: Address breaking changes
        if analysis['is_breaking']:
            breaking_issues = [
                issue for issue in analysis['issues'] 
                if issue['issue_type'] == 'breaking_change'
            ]
            
            if breaking_issues:
                steps.append({
                    'step': 2,
                    'title': 'Address Breaking Changes',
                    'description': 'Fix compatibility issues',
                    'actions': [
                        f"Fix: {issue['description']}" for issue in breaking_issues
                    ],
                    'validation': 'All breaking changes addressed'
                })
        
        # Step 3: Update version configuration
        steps.append({
            'step': len(steps) + 1,
            'title': 'Update Version Configuration',
            'description': 'Configure application to use new version',
            'actions': [
                'Update API version headers',
                'Modify version negotiation logic',
                'Update client configuration'
            ],
            'validation': 'Application uses new API version'
        })
        
        # Step 4: Testing
        steps.append({
            'step': len(steps) + 1,
            'title': 'Testing',
            'description': 'Validate migration',
            'actions': [
                'Run compatibility tests',
                'Validate all endpoints',
                'Check error handling',
                'Performance testing'
            ],
            'validation': 'All tests pass successfully'
        })
        
        # Step 5: Deployment
        steps.append({
            'step': len(steps) + 1,
            'title': 'Deployment',
            'description': 'Deploy to production',
            'actions': [
                'Deploy to staging first',
                'Gradual rollout to production',
                'Monitor metrics and logs',
                'Verify functionality'
            ],
            'validation': 'Production deployment successful'
        })
        
        return steps
    
    def _generate_test_scripts(self, from_version: str, to_version: str) -> List[Dict[str, str]]:
        """Generate test scripts for migration validation"""
        scripts = [
            {
                'name': 'version_negotiation_test.py',
                'description': 'Test version negotiation headers',
                'language': 'python',
                'content': f'''
import requests

def test_version_negotiation():
    # Test with explicit version header
    response = requests.get("http://api.example.com/api/v{to_version.split('.')[0]}/health", 
                          headers={{"X-API-Version": "{to_version}"}})
    assert response.headers.get("X-API-Version") == "{to_version}"
    
    # Test with Accept header
    response = requests.get("http://api.example.com/api/v{to_version.split('.')[0]}/health",
                          headers={{"Accept": "application/vnd.financial-planning.v{to_version.split('.')[0]}+json"}})
    assert response.status_code == 200

if __name__ == "__main__":
    test_version_negotiation()
    print("Version negotiation tests passed!")
'''
            },
            {
                'name': 'compatibility_test.sh',
                'description': 'Shell script for endpoint compatibility testing',
                'language': 'bash',
                'content': f'''#!/bin/bash

API_BASE="http://api.example.com/api/v{to_version.split('.')[0]}"
API_VERSION="{to_version}"

echo "Testing API compatibility for version $API_VERSION"

# Test authentication endpoint
curl -X POST "$API_BASE/auth/login" \\
     -H "X-API-Version: $API_VERSION" \\
     -H "Content-Type: application/json" \\
     -d '{{"username": "test", "password": "test"}}' \\
     --fail || echo "Auth endpoint failed"

# Test main endpoints
for endpoint in users financial-profiles goals; do
    echo "Testing $endpoint endpoint..."
    curl -X GET "$API_BASE/$endpoint" \\
         -H "X-API-Version: $API_VERSION" \\
         -H "Authorization: Bearer test-token" \\
         --fail || echo "$endpoint endpoint failed"
done

echo "Compatibility testing completed"
'''
            }
        ]
        
        return scripts
    
    def validate_backward_compatibility(self, version: str) -> Dict[str, Any]:
        """Validate backward compatibility for a version"""
        
        version_obj = self.version_manager.get_version(version)
        if not version_obj:
            return {'valid': False, 'error': 'Version not found'}
        
        # Get all older supported versions
        all_versions = self.version_manager.get_supported_versions()
        older_versions = [
            v for v in all_versions 
            if Version(v.version) < Version(version)
        ]
        
        compatibility_results = []
        overall_score = 100.0
        issues = []
        
        for old_version in older_versions:
            analysis = self.analyze_compatibility(old_version.version, version)
            compatibility_results.append(analysis)
            
            if analysis['is_breaking']:
                issues.append(f"Breaking changes from {old_version.version} to {version}")
                overall_score -= 20
            
            overall_score = min(overall_score, analysis['compatibility_score'])
        
        validation = {
            'version': version,
            'backward_compatible': overall_score >= 80.0 and not any(r['is_breaking'] for r in compatibility_results),
            'compatibility_score': overall_score,
            'tested_versions': [r['from_version'] for r in compatibility_results],
            'compatibility_results': compatibility_results,
            'issues': issues,
            'recommendations': self._get_compatibility_recommendations(compatibility_results)
        }
        
        return validation
    
    def _get_compatibility_recommendations(self, compatibility_results: List[Dict[str, Any]]) -> List[str]:
        """Get recommendations for improving compatibility"""
        recommendations = []
        
        breaking_changes = any(r['is_breaking'] for r in compatibility_results)
        low_scores = [r for r in compatibility_results if r['compatibility_score'] < 80]
        
        if breaking_changes:
            recommendations.append('Consider implementing compatibility layer for breaking changes')
            recommendations.append('Provide comprehensive migration guides')
            recommendations.append('Extend deprecation period for affected versions')
        
        if low_scores:
            recommendations.append('Address compatibility issues with lower-scored versions')
            recommendations.append('Consider adding backward compatibility shims')
        
        if not breaking_changes and not low_scores:
            recommendations.append('Excellent backward compatibility maintained')
            recommendations.append('Continue following semantic versioning principles')
        
        return recommendations