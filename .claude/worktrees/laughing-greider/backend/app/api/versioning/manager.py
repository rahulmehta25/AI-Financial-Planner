"""
Version Manager - Central management for API versions
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from pathlib import Path
from semantic_version import Version

from .models import (
    APIVersion, VersionStatus, DeprecationPolicy, 
    VersionCompatibility, VersionMetrics, ClientSDKInfo,
    VersionedEndpoint, ABTestConfig
)

logger = logging.getLogger(__name__)


class VersionManager:
    """Central manager for API versioning"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or "config/versions.json"
        self.deprecation_policy = DeprecationPolicy()
        self._versions: Dict[str, APIVersion] = {}
        self._compatibility_matrix: Dict[str, List[VersionCompatibility]] = {}
        self._endpoints: Dict[str, VersionedEndpoint] = {}
        self._ab_tests: Dict[str, ABTestConfig] = {}
        self._metrics: Dict[str, VersionMetrics] = {}
        self._client_sdks: List[ClientSDKInfo] = []
        
        self._load_configuration()
    
    def _load_configuration(self):
        """Load version configuration from file"""
        config_file = Path(self.config_path)
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    self._load_from_config(config)
                logger.info(f"Loaded version configuration from {self.config_path}")
            except Exception as e:
                logger.error(f"Failed to load version config: {e}")
                self._load_default_configuration()
        else:
            self._load_default_configuration()
    
    def _load_default_configuration(self):
        """Load default version configuration"""
        # Current stable version
        v1 = APIVersion(
            version="1.0.0",
            status=VersionStatus.STABLE,
            release_date=datetime(2024, 1, 1),
            description="Initial stable release with core financial planning features",
            new_features=[
                "User authentication and authorization",
                "Financial profile management", 
                "Goal setting and tracking",
                "Monte Carlo simulations",
                "PDF report generation"
            ],
            supported_until=datetime(2025, 12, 31)
        )
        
        # Development version
        v2 = APIVersion(
            version="2.0.0",
            status=VersionStatus.DEVELOPMENT,
            release_date=datetime(2024, 6, 1),
            description="Enhanced features with AI recommendations and social platform",
            new_features=[
                "AI-powered financial recommendations",
                "Social platform integration",
                "Advanced portfolio optimization",
                "Real-time market data integration",
                "Voice interface support"
            ],
            breaking_changes=[
                "Authentication header format changed",
                "Response format standardized",
                "Endpoint paths restructured"
            ]
        )
        
        self._versions = {
            "1.0.0": v1,
            "2.0.0": v2
        }
        
        # Default compatibility matrix
        self._compatibility_matrix = {
            "2.0.0": [
                VersionCompatibility(
                    from_version="1.0.0",
                    to_version="2.0.0",
                    compatibility_level="breaking",
                    migration_required=True,
                    breaking_changes=[
                        "Authentication headers must include 'Bearer' prefix",
                        "All response envelopes now include 'data' wrapper",
                        "Date formats changed to ISO 8601"
                    ],
                    migration_guide_url="/docs/migration/v1-to-v2"
                )
            ]
        }
        
        logger.info("Loaded default version configuration")
    
    def _load_from_config(self, config: dict):
        """Load configuration from dictionary"""
        # Load versions
        if 'versions' in config:
            for version_data in config['versions']:
                version = APIVersion(**version_data)
                self._versions[version.version] = version
        
        # Load compatibility matrix
        if 'compatibility' in config:
            for version, compatibilities in config['compatibility'].items():
                self._compatibility_matrix[version] = [
                    VersionCompatibility(**comp) for comp in compatibilities
                ]
        
        # Load endpoints
        if 'endpoints' in config:
            for endpoint_data in config['endpoints']:
                endpoint = VersionedEndpoint(**endpoint_data)
                self._endpoints[f"{endpoint.path}:{','.join(endpoint.methods)}"] = endpoint
        
        # Load A/B tests
        if 'ab_tests' in config:
            for test_data in config['ab_tests']:
                test = ABTestConfig(**test_data)
                self._ab_tests[test.test_name] = test
    
    def save_configuration(self):
        """Save current configuration to file"""
        config = {
            'versions': [v.dict() for v in self._versions.values()],
            'compatibility': {
                version: [comp.dict() for comp in comps]
                for version, comps in self._compatibility_matrix.items()
            },
            'endpoints': [ep.dict() for ep in self._endpoints.values()],
            'ab_tests': [test.dict() for test in self._ab_tests.values()]
        }
        
        config_file = Path(self.config_path)
        config_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2, default=str)
        
        logger.info(f"Saved version configuration to {self.config_path}")
    
    def get_version(self, version: str) -> Optional[APIVersion]:
        """Get version information"""
        return self._versions.get(version)
    
    def get_all_versions(self) -> List[APIVersion]:
        """Get all versions sorted by version number"""
        versions = list(self._versions.values())
        return sorted(versions, key=lambda v: Version(v.version), reverse=True)
    
    def get_supported_versions(self) -> List[APIVersion]:
        """Get all currently supported versions"""
        return [v for v in self._versions.values() if v.is_supported]
    
    def get_latest_version(self) -> Optional[APIVersion]:
        """Get the latest stable version"""
        stable_versions = [
            v for v in self._versions.values() 
            if v.status == VersionStatus.STABLE and v.is_supported
        ]
        
        if not stable_versions:
            return None
        
        return max(stable_versions, key=lambda v: Version(v.version))
    
    def add_version(self, version: APIVersion) -> bool:
        """Add a new version"""
        if version.version in self._versions:
            logger.warning(f"Version {version.version} already exists")
            return False
        
        self._versions[version.version] = version
        logger.info(f"Added version {version.version}")
        return True
    
    def deprecate_version(self, version: str, deprecation_date: Optional[datetime] = None) -> bool:
        """Deprecate a version"""
        if version not in self._versions:
            logger.error(f"Version {version} not found")
            return False
        
        api_version = self._versions[version]
        if api_version.status == VersionStatus.RETIRED:
            logger.error(f"Version {version} is already retired")
            return False
        
        deprecation_date = deprecation_date or datetime.utcnow()
        retirement_date = self.deprecation_policy.calculate_retirement_date(
            deprecation_date, api_version.status
        )
        
        api_version.status = VersionStatus.DEPRECATED
        api_version.deprecation_date = deprecation_date
        api_version.retirement_date = retirement_date
        
        logger.info(f"Deprecated version {version}, retirement scheduled for {retirement_date}")
        return True
    
    def retire_version(self, version: str) -> bool:
        """Retire a version"""
        if version not in self._versions:
            logger.error(f"Version {version} not found")
            return False
        
        api_version = self._versions[version]
        api_version.status = VersionStatus.RETIRED
        api_version.retirement_date = datetime.utcnow()
        
        logger.info(f"Retired version {version}")
        return True
    
    def is_version_supported(self, version: str) -> bool:
        """Check if version is supported"""
        api_version = self._versions.get(version)
        return api_version is not None and api_version.is_supported
    
    def get_compatibility(self, from_version: str, to_version: str) -> Optional[VersionCompatibility]:
        """Get compatibility information between versions"""
        compatibilities = self._compatibility_matrix.get(to_version, [])
        
        for compatibility in compatibilities:
            if compatibility.from_version == from_version:
                return compatibility
        
        return None
    
    def get_migration_path(self, from_version: str, to_version: str) -> List[VersionCompatibility]:
        """Get migration path between versions"""
        # For now, return direct migration if available
        compatibility = self.get_compatibility(from_version, to_version)
        return [compatibility] if compatibility else []
    
    def add_endpoint(self, endpoint: VersionedEndpoint):
        """Add a versioned endpoint"""
        key = f"{endpoint.path}:{','.join(endpoint.methods)}"
        self._endpoints[key] = endpoint
    
    def get_endpoints_for_version(self, version: str) -> List[VersionedEndpoint]:
        """Get all endpoints available in a version"""
        return [
            endpoint for endpoint in self._endpoints.values()
            if endpoint.is_available_in_version(version)
        ]
    
    def add_ab_test(self, test: ABTestConfig):
        """Add A/B test configuration"""
        self._ab_tests[test.test_name] = test
        logger.info(f"Added A/B test: {test.test_name}")
    
    def get_ab_test(self, test_name: str) -> Optional[ABTestConfig]:
        """Get A/B test configuration"""
        return self._ab_tests.get(test_name)
    
    def get_active_ab_tests(self) -> List[ABTestConfig]:
        """Get all active A/B tests"""
        return [test for test in self._ab_tests.values() if test.is_active]
    
    def should_use_version_for_test(self, test_name: str, user_id: str, current_version: str) -> str:
        """Determine version to use based on A/B test"""
        test = self.get_ab_test(test_name)
        
        if not test or not test.is_active:
            return current_version
        
        if test.from_version != current_version:
            return current_version
        
        if test.should_use_new_version(user_id):
            return test.to_version
        
        return current_version
    
    def record_metrics(self, version: str, request_count: int = 1, 
                      response_time_ms: float = 0, error: bool = False,
                      client_type: str = "unknown"):
        """Record usage metrics for a version"""
        if version not in self._metrics:
            self._metrics[version] = VersionMetrics(version=version)
        
        metrics = self._metrics[version]
        metrics.request_count += request_count
        metrics.last_request = datetime.utcnow()
        
        if response_time_ms > 0:
            # Update rolling average
            total_time = metrics.avg_response_time_ms * (metrics.request_count - request_count)
            metrics.avg_response_time_ms = (total_time + response_time_ms) / metrics.request_count
        
        if error:
            metrics.error_rate = ((metrics.error_rate * (metrics.request_count - 1)) + 1) / metrics.request_count
        
        # Update client breakdown
        if client_type not in metrics.client_breakdown:
            metrics.client_breakdown[client_type] = 0
        metrics.client_breakdown[client_type] += request_count
    
    def get_metrics(self, version: str) -> Optional[VersionMetrics]:
        """Get metrics for a version"""
        return self._metrics.get(version)
    
    def get_versions_needing_retirement_warning(self, days_ahead: int = 30) -> List[APIVersion]:
        """Get versions that need retirement warnings"""
        warning_date = datetime.utcnow() + timedelta(days=days_ahead)
        
        return [
            version for version in self._versions.values()
            if (version.retirement_date and 
                version.retirement_date <= warning_date and
                version.status == VersionStatus.DEPRECATED)
        ]
    
    def cleanup_retired_versions(self, keep_days: int = 30):
        """Clean up metrics and data for retired versions"""
        cleanup_date = datetime.utcnow() - timedelta(days=keep_days)
        
        retired_versions = [
            version.version for version in self._versions.values()
            if (version.status == VersionStatus.RETIRED and
                version.retirement_date and
                version.retirement_date <= cleanup_date)
        ]
        
        for version in retired_versions:
            if version in self._metrics:
                del self._metrics[version]
                logger.info(f"Cleaned up metrics for retired version {version}")
    
    def add_client_sdk(self, sdk: ClientSDKInfo):
        """Add client SDK information"""
        # Remove existing SDK with same name and version
        self._client_sdks = [
            s for s in self._client_sdks 
            if not (s.sdk_name == sdk.sdk_name and s.sdk_version == sdk.sdk_version)
        ]
        self._client_sdks.append(sdk)
        logger.info(f"Added SDK: {sdk.sdk_name} v{sdk.sdk_version}")
    
    def get_sdks_for_version(self, version: str) -> List[ClientSDKInfo]:
        """Get SDKs that support a specific API version"""
        return [sdk for sdk in self._client_sdks if sdk.supports_version(version)]
    
    def get_compatibility_matrix(self) -> Dict[str, List[VersionCompatibility]]:
        """Get the full compatibility matrix"""
        return self._compatibility_matrix.copy()
    
    def validate_version_sequence(self) -> List[str]:
        """Validate version sequence and return any issues"""
        issues = []
        versions = sorted(self._versions.values(), key=lambda v: Version(v.version))
        
        for i, version in enumerate(versions):
            # Check if deprecated versions have retirement dates
            if version.status == VersionStatus.DEPRECATED and not version.retirement_date:
                issues.append(f"Version {version.version} is deprecated but has no retirement date")
            
            # Check retirement dates are after deprecation dates
            if (version.deprecation_date and version.retirement_date and 
                version.retirement_date <= version.deprecation_date):
                issues.append(f"Version {version.version} retirement date must be after deprecation date")
        
        return issues