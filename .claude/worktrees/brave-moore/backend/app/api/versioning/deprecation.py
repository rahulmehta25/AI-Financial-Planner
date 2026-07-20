"""
Deprecation Management - Handle API deprecation policies and timelines
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from enum import Enum
from dataclasses import dataclass, field

from .models import APIVersion, VersionStatus, DeprecationPolicy
from .manager import VersionManager

logger = logging.getLogger(__name__)


class DeprecationSeverity(str, Enum):
    """Severity levels for deprecation warnings"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    BREAKING = "breaking"


@dataclass
class DeprecationNotice:
    """Deprecation notice for an API version or endpoint"""
    version: str
    component: str  # "version", "endpoint", "parameter", "response_field"
    message: str
    severity: DeprecationSeverity
    deprecation_date: datetime
    removal_date: Optional[datetime] = None
    replacement: Optional[str] = None
    migration_guide: Optional[str] = None
    alternatives: List[str] = field(default_factory=list)
    affected_endpoints: List[str] = field(default_factory=list)
    client_impact: str = "medium"  # low, medium, high
    
    @property
    def days_until_removal(self) -> Optional[int]:
        """Calculate days until removal"""
        if not self.removal_date:
            return None
        delta = self.removal_date - datetime.utcnow()
        return max(0, delta.days)
    
    @property
    def is_urgent(self) -> bool:
        """Check if deprecation requires urgent attention"""
        if self.severity == DeprecationSeverity.BREAKING:
            return True
        
        days_left = self.days_until_removal
        if days_left is not None and days_left <= 30:
            return True
        
        return False


class DeprecationManager:
    """Manage API deprecation policies and notifications"""
    
    def __init__(self, version_manager: VersionManager, policy: Optional[DeprecationPolicy] = None):
        self.version_manager = version_manager
        self.policy = policy or DeprecationPolicy()
        self.deprecation_notices: Dict[str, List[DeprecationNotice]] = {}
        self.notification_history: List[Dict] = []
    
    def deprecate_version(
        self,
        version: str,
        reason: str,
        deprecation_date: Optional[datetime] = None,
        advance_notice: bool = True
    ) -> bool:
        """Deprecate an API version"""
        
        version_obj = self.version_manager.get_version(version)
        if not version_obj:
            logger.error(f"Version {version} not found")
            return False
        
        if version_obj.status == VersionStatus.RETIRED:
            logger.error(f"Version {version} is already retired")
            return False
        
        deprecation_date = deprecation_date or datetime.utcnow()
        
        # Calculate retirement date based on policy
        retirement_date = self.policy.calculate_retirement_date(
            deprecation_date, version_obj.status
        )
        
        # Update version in manager
        success = self.version_manager.deprecate_version(version, deprecation_date)
        if not success:
            return False
        
        # Create deprecation notice
        notice = DeprecationNotice(
            version=version,
            component="version",
            message=f"API version {version} is deprecated. {reason}",
            severity=DeprecationSeverity.WARNING,
            deprecation_date=deprecation_date,
            removal_date=retirement_date,
            migration_guide=f"/docs/migration/v{version.split('.')[0]}-migration",
            client_impact="high"
        )
        
        self.add_deprecation_notice(notice)
        
        # Send advance notice if configured
        if advance_notice:
            self._schedule_advance_notices(notice)
        
        logger.info(f"Deprecated version {version}, retirement scheduled for {retirement_date}")
        return True
    
    def deprecate_endpoint(
        self,
        version: str,
        endpoint_path: str,
        reason: str,
        replacement: Optional[str] = None,
        removal_version: Optional[str] = None
    ):
        """Deprecate a specific endpoint"""
        
        notice = DeprecationNotice(
            version=version,
            component="endpoint",
            message=f"Endpoint {endpoint_path} is deprecated. {reason}",
            severity=DeprecationSeverity.WARNING,
            deprecation_date=datetime.utcnow(),
            replacement=replacement,
            affected_endpoints=[endpoint_path],
            migration_guide=f"/docs/endpoints/{endpoint_path.replace('/', '-')}-deprecation"
        )
        
        if removal_version:
            # Calculate removal date based on version timeline
            target_version = self.version_manager.get_version(removal_version)
            if target_version:
                notice.removal_date = target_version.release_date
        
        self.add_deprecation_notice(notice)
        logger.info(f"Deprecated endpoint {endpoint_path} in version {version}")
    
    def deprecate_parameter(
        self,
        version: str,
        endpoint_path: str,
        parameter_name: str,
        reason: str,
        replacement: Optional[str] = None
    ):
        """Deprecate a specific parameter"""
        
        notice = DeprecationNotice(
            version=version,
            component="parameter",
            message=f"Parameter '{parameter_name}' in {endpoint_path} is deprecated. {reason}",
            severity=DeprecationSeverity.INFO,
            deprecation_date=datetime.utcnow(),
            replacement=replacement,
            affected_endpoints=[endpoint_path],
            client_impact="low"
        )
        
        self.add_deprecation_notice(notice)
        logger.info(f"Deprecated parameter {parameter_name} in {endpoint_path}")
    
    def add_deprecation_notice(self, notice: DeprecationNotice):
        """Add a deprecation notice"""
        if notice.version not in self.deprecation_notices:
            self.deprecation_notices[notice.version] = []
        
        self.deprecation_notices[notice.version].append(notice)
    
    def get_deprecation_notices(
        self,
        version: Optional[str] = None,
        severity: Optional[DeprecationSeverity] = None,
        component: Optional[str] = None
    ) -> List[DeprecationNotice]:
        """Get deprecation notices with optional filtering"""
        
        notices = []
        
        if version:
            notices = self.deprecation_notices.get(version, [])
        else:
            for version_notices in self.deprecation_notices.values():
                notices.extend(version_notices)
        
        # Apply filters
        if severity:
            notices = [n for n in notices if n.severity == severity]
        
        if component:
            notices = [n for n in notices if n.component == component]
        
        return sorted(notices, key=lambda n: n.deprecation_date, reverse=True)
    
    def get_urgent_notices(self) -> List[DeprecationNotice]:
        """Get notices requiring urgent attention"""
        all_notices = self.get_deprecation_notices()
        return [notice for notice in all_notices if notice.is_urgent]
    
    def check_version_compliance(self, version: str) -> Dict:
        """Check deprecation compliance for a version"""
        version_obj = self.version_manager.get_version(version)
        if not version_obj:
            return {'valid': False, 'error': 'Version not found'}
        
        notices = self.get_deprecation_notices(version)
        
        compliance = {
            'version': version,
            'status': version_obj.status.value,
            'is_deprecated': version_obj.is_deprecated,
            'is_retired': version_obj.is_retired,
            'deprecation_notices': len(notices),
            'urgent_notices': len([n for n in notices if n.is_urgent]),
            'compliance_score': 100.0,
            'issues': [],
            'recommendations': []
        }
        
        # Check deprecation timeline compliance
        if version_obj.is_deprecated:
            if not version_obj.retirement_date:
                compliance['issues'].append('Deprecated version missing retirement date')
                compliance['compliance_score'] -= 20
            
            elif version_obj.deprecation_date and version_obj.retirement_date:
                deprecation_period = version_obj.retirement_date - version_obj.deprecation_date
                min_period = timedelta(days=self.policy.min_deprecation_period_days)
                
                if deprecation_period < min_period:
                    compliance['issues'].append(
                        f'Deprecation period too short: {deprecation_period.days} days '
                        f'(minimum: {self.policy.min_deprecation_period_days} days)'
                    )
                    compliance['compliance_score'] -= 30
        
        # Check advance notice
        if version_obj.is_deprecated and version_obj.deprecation_date:
            advance_period = version_obj.deprecation_date - version_obj.release_date
            min_advance = timedelta(days=self.policy.advance_notice_days)
            
            if advance_period < min_advance:
                compliance['issues'].append(
                    f'Insufficient advance notice: {advance_period.days} days '
                    f'(minimum: {self.policy.advance_notice_days} days)'
                )
                compliance['compliance_score'] -= 15
        
        # Add recommendations
        if version_obj.is_deprecated:
            compliance['recommendations'].append('Provide migration documentation')
            compliance['recommendations'].append('Notify all clients of deprecation')
            
            if version_obj.days_until_retirement() and version_obj.days_until_retirement() <= 90:
                compliance['recommendations'].append('Send urgent retirement warnings')
        
        return compliance
    
    def generate_deprecation_timeline(self, version: str) -> Dict:
        """Generate a deprecation timeline for planning"""
        version_obj = self.version_manager.get_version(version)
        if not version_obj:
            return {'error': 'Version not found'}
        
        timeline = {
            'version': version,
            'current_status': version_obj.status.value,
            'milestones': []
        }
        
        # Add past milestones
        if version_obj.release_date:
            timeline['milestones'].append({
                'date': version_obj.release_date,
                'milestone': 'Release',
                'status': 'completed',
                'description': f'Version {version} released'
            })
        
        if version_obj.deprecation_date:
            timeline['milestones'].append({
                'date': version_obj.deprecation_date,
                'milestone': 'Deprecation',
                'status': 'completed' if datetime.utcnow() >= version_obj.deprecation_date else 'upcoming',
                'description': f'Version {version} deprecated'
            })
        
        # Add future milestones
        if version_obj.retirement_date:
            # Warning milestones
            for days_before in self.policy.retirement_warning_thresholds:
                warning_date = version_obj.retirement_date - timedelta(days=days_before)
                if warning_date > datetime.utcnow():
                    timeline['milestones'].append({
                        'date': warning_date,
                        'milestone': f'Warning ({days_before} days)',
                        'status': 'upcoming',
                        'description': f'Send retirement warning ({days_before} days notice)'
                    })
            
            # Retirement milestone
            timeline['milestones'].append({
                'date': version_obj.retirement_date,
                'milestone': 'Retirement',
                'status': 'upcoming' if datetime.utcnow() < version_obj.retirement_date else 'completed',
                'description': f'Version {version} retired'
            })
        
        # Sort milestones by date
        timeline['milestones'].sort(key=lambda m: m['date'])
        
        return timeline
    
    def _schedule_advance_notices(self, notice: DeprecationNotice):
        """Schedule advance notices for deprecation"""
        if not notice.removal_date:
            return
        
        for days_before in self.policy.retirement_warning_thresholds:
            warning_date = notice.removal_date - timedelta(days=days_before)
            
            if warning_date > datetime.utcnow():
                self.notification_history.append({
                    'type': 'scheduled_warning',
                    'notice_id': f"{notice.version}-{notice.component}",
                    'warning_date': warning_date,
                    'days_before': days_before,
                    'scheduled_at': datetime.utcnow()
                })
        
        logger.info(f"Scheduled {len(self.policy.retirement_warning_thresholds)} advance notices for {notice.version}")
    
    def get_notices_requiring_warnings(self) -> List[DeprecationNotice]:
        """Get notices that need warnings sent today"""
        notices_to_warn = []
        
        for version_notices in self.deprecation_notices.values():
            for notice in version_notices:
                if not notice.removal_date:
                    continue
                
                days_until_removal = notice.days_until_removal
                if days_until_removal in self.policy.retirement_warning_thresholds:
                    notices_to_warn.append(notice)
        
        return notices_to_warn
    
    def create_deprecation_response_headers(self, version: str, endpoint: str = None) -> Dict[str, str]:
        """Create deprecation headers for HTTP responses"""
        headers = {}
        
        # Version-level deprecation
        version_obj = self.version_manager.get_version(version)
        if version_obj and version_obj.is_deprecated:
            headers['X-API-Deprecated'] = 'true'
            headers['X-API-Deprecation-Date'] = version_obj.deprecation_date.isoformat() if version_obj.deprecation_date else ''
            
            if version_obj.retirement_date:
                headers['X-API-Retirement-Date'] = version_obj.retirement_date.isoformat()
                
                days_left = version_obj.days_until_retirement()
                if days_left is not None:
                    headers['X-API-Days-Until-Retirement'] = str(days_left)
        
        # Endpoint-specific deprecation
        if endpoint:
            endpoint_notices = [
                n for n in self.get_deprecation_notices(version)
                if n.component == 'endpoint' and endpoint in n.affected_endpoints
            ]
            
            if endpoint_notices:
                notice = endpoint_notices[0]  # Most recent
                headers['X-Endpoint-Deprecated'] = 'true'
                headers['X-Endpoint-Deprecation-Message'] = notice.message
                
                if notice.replacement:
                    headers['X-Endpoint-Replacement'] = notice.replacement
                
                if notice.migration_guide:
                    headers['X-Migration-Guide'] = notice.migration_guide
        
        return headers
    
    def export_deprecation_report(self, format: str = "json") -> Dict:
        """Export comprehensive deprecation report"""
        
        all_versions = self.version_manager.get_all_versions()
        
        report = {
            'generated_at': datetime.utcnow().isoformat(),
            'policy': {
                'min_deprecation_period_days': self.policy.min_deprecation_period_days,
                'stable_support_period_days': self.policy.stable_support_period_days,
                'beta_support_period_days': self.policy.beta_support_period_days,
                'advance_notice_days': self.policy.advance_notice_days
            },
            'versions': [],
            'urgent_actions': [],
            'summary': {
                'total_versions': len(all_versions),
                'deprecated_versions': 0,
                'retired_versions': 0,
                'total_notices': 0,
                'urgent_notices': 0
            }
        }
        
        # Process each version
        for version_obj in all_versions:
            version_data = {
                'version': version_obj.version,
                'status': version_obj.status.value,
                'release_date': version_obj.release_date.isoformat() if version_obj.release_date else None,
                'deprecation_date': version_obj.deprecation_date.isoformat() if version_obj.deprecation_date else None,
                'retirement_date': version_obj.retirement_date.isoformat() if version_obj.retirement_date else None,
                'notices': []
            }
            
            # Add notices
            notices = self.get_deprecation_notices(version_obj.version)
            for notice in notices:
                notice_data = {
                    'component': notice.component,
                    'message': notice.message,
                    'severity': notice.severity.value,
                    'deprecation_date': notice.deprecation_date.isoformat(),
                    'removal_date': notice.removal_date.isoformat() if notice.removal_date else None,
                    'is_urgent': notice.is_urgent,
                    'days_until_removal': notice.days_until_removal
                }
                version_data['notices'].append(notice_data)
                
                if notice.is_urgent:
                    report['urgent_actions'].append({
                        'version': version_obj.version,
                        'action': 'Address urgent deprecation',
                        'notice': notice_data
                    })
            
            report['versions'].append(version_data)
            
            # Update summary
            if version_obj.is_deprecated:
                report['summary']['deprecated_versions'] += 1
            if version_obj.is_retired:
                report['summary']['retired_versions'] += 1
            
            report['summary']['total_notices'] += len(notices)
            report['summary']['urgent_notices'] += len([n for n in notices if n.is_urgent])
        
        return report