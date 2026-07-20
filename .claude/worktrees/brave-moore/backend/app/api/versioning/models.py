"""
Core models for API versioning system
"""

from datetime import datetime, timedelta
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from semantic_version import Version


class VersionStatus(str, Enum):
    """API version lifecycle status"""
    DEVELOPMENT = "development"
    BETA = "beta"
    STABLE = "stable"
    DEPRECATED = "deprecated"
    RETIRED = "retired"


class CompatibilityLevel(str, Enum):
    """Backward compatibility levels"""
    BREAKING = "breaking"
    COMPATIBLE = "compatible"
    FEATURE = "feature"
    PATCH = "patch"


class APIVersion(BaseModel):
    """API Version metadata"""
    version: str = Field(..., description="Semantic version string (e.g., '1.2.3')")
    status: VersionStatus = Field(..., description="Current status of this version")
    release_date: datetime = Field(..., description="When this version was released")
    deprecation_date: Optional[datetime] = Field(None, description="When this version was deprecated")
    retirement_date: Optional[datetime] = Field(None, description="When this version will be retired")
    description: str = Field(..., description="Human-readable description of changes")
    breaking_changes: List[str] = Field(default_factory=list, description="List of breaking changes")
    new_features: List[str] = Field(default_factory=list, description="List of new features")
    bug_fixes: List[str] = Field(default_factory=list, description="List of bug fixes")
    supported_until: Optional[datetime] = Field(None, description="Support end date")
    
    @validator('version')
    def validate_version_format(cls, v):
        """Ensure version follows semantic versioning"""
        try:
            Version(v)
            return v
        except ValueError:
            raise ValueError("Version must follow semantic versioning format (e.g., '1.2.3')")
    
    @property
    def semantic_version(self) -> Version:
        """Get semantic version object"""
        return Version(self.version)
    
    @property
    def is_deprecated(self) -> bool:
        """Check if version is deprecated"""
        return self.status == VersionStatus.DEPRECATED
    
    @property
    def is_retired(self) -> bool:
        """Check if version is retired"""
        return self.status == VersionStatus.RETIRED
    
    @property
    def is_supported(self) -> bool:
        """Check if version is currently supported"""
        if self.is_retired:
            return False
        if self.supported_until and datetime.utcnow() > self.supported_until:
            return False
        return True
    
    def days_until_retirement(self) -> Optional[int]:
        """Calculate days until retirement"""
        if not self.retirement_date:
            return None
        delta = self.retirement_date - datetime.utcnow()
        return max(0, delta.days)


class DeprecationPolicy(BaseModel):
    """Deprecation policy configuration"""
    min_deprecation_period_days: int = Field(
        default=180, 
        description="Minimum days between deprecation and retirement"
    )
    stable_support_period_days: int = Field(
        default=365,
        description="Days to support stable versions after deprecation"
    )
    beta_support_period_days: int = Field(
        default=90,
        description="Days to support beta versions after deprecation"
    )
    advance_notice_days: int = Field(
        default=60,
        description="Days of advance notice before deprecation"
    )
    retirement_warning_thresholds: List[int] = Field(
        default=[90, 30, 7],
        description="Days before retirement to send warnings"
    )
    
    def calculate_retirement_date(
        self, 
        deprecation_date: datetime, 
        version_status: VersionStatus
    ) -> datetime:
        """Calculate retirement date based on policy"""
        if version_status == VersionStatus.STABLE:
            days = self.stable_support_period_days
        elif version_status == VersionStatus.BETA:
            days = self.beta_support_period_days
        else:
            days = self.min_deprecation_period_days
        
        return deprecation_date + timedelta(days=days)


class VersionCompatibility(BaseModel):
    """Version compatibility mapping"""
    from_version: str = Field(..., description="Source version")
    to_version: str = Field(..., description="Target version")
    compatibility_level: CompatibilityLevel = Field(..., description="Compatibility level")
    migration_required: bool = Field(default=False, description="Whether migration is required")
    migration_guide_url: Optional[str] = Field(None, description="URL to migration guide")
    breaking_changes: List[str] = Field(default_factory=list, description="Breaking changes")
    automated_migration: bool = Field(default=False, description="Whether migration can be automated")
    
    @property
    def is_breaking_change(self) -> bool:
        """Check if this represents a breaking change"""
        return self.compatibility_level == CompatibilityLevel.BREAKING


class VersionMetrics(BaseModel):
    """Version usage metrics"""
    version: str = Field(..., description="API version")
    request_count: int = Field(default=0, description="Total requests")
    unique_clients: int = Field(default=0, description="Unique client count")
    error_rate: float = Field(default=0.0, description="Error rate percentage")
    avg_response_time_ms: float = Field(default=0.0, description="Average response time")
    last_request: Optional[datetime] = Field(None, description="Last request timestamp")
    client_breakdown: Dict[str, int] = Field(
        default_factory=dict,
        description="Request count by client type"
    )


class ClientSDKInfo(BaseModel):
    """Client SDK information"""
    sdk_name: str = Field(..., description="SDK name")
    sdk_version: str = Field(..., description="SDK version")
    supported_api_versions: List[str] = Field(
        ..., 
        description="List of supported API versions"
    )
    min_api_version: str = Field(..., description="Minimum supported API version")
    max_api_version: str = Field(..., description="Maximum supported API version")
    language: str = Field(..., description="Programming language")
    release_date: datetime = Field(..., description="SDK release date")
    download_url: str = Field(..., description="Download URL")
    documentation_url: str = Field(..., description="Documentation URL")
    changelog_url: str = Field(..., description="Changelog URL")
    auto_update_available: bool = Field(
        default=False, 
        description="Whether auto-update is available"
    )
    
    def supports_version(self, version: str) -> bool:
        """Check if SDK supports given API version"""
        return version in self.supported_api_versions


class VersionedEndpoint(BaseModel):
    """Versioned endpoint configuration"""
    path: str = Field(..., description="Endpoint path")
    methods: List[str] = Field(..., description="HTTP methods")
    introduced_in: str = Field(..., description="Version where endpoint was introduced")
    deprecated_in: Optional[str] = Field(None, description="Version where endpoint was deprecated")
    removed_in: Optional[str] = Field(None, description="Version where endpoint was removed")
    changes: Dict[str, str] = Field(
        default_factory=dict,
        description="Changes by version"
    )
    
    def is_available_in_version(self, version: str) -> bool:
        """Check if endpoint is available in given version"""
        version_obj = Version(version)
        introduced_obj = Version(self.introduced_in)
        
        if version_obj < introduced_obj:
            return False
            
        if self.removed_in:
            removed_obj = Version(self.removed_in)
            if version_obj >= removed_obj:
                return False
                
        return True
    
    def is_deprecated_in_version(self, version: str) -> bool:
        """Check if endpoint is deprecated in given version"""
        if not self.deprecated_in:
            return False
            
        version_obj = Version(version)
        deprecated_obj = Version(self.deprecated_in)
        
        return version_obj >= deprecated_obj


class ABTestConfig(BaseModel):
    """A/B testing configuration for version migration"""
    test_name: str = Field(..., description="A/B test name")
    from_version: str = Field(..., description="Current version")
    to_version: str = Field(..., description="Target version")
    traffic_percentage: float = Field(
        default=10.0,
        ge=0.0,
        le=100.0,
        description="Percentage of traffic to route to new version"
    )
    user_segments: List[str] = Field(
        default_factory=list,
        description="User segments to include in test"
    )
    metrics_to_track: List[str] = Field(
        default_factory=list,
        description="Metrics to track during test"
    )
    success_criteria: Dict[str, Any] = Field(
        default_factory=dict,
        description="Success criteria for the test"
    )
    start_date: datetime = Field(..., description="Test start date")
    end_date: datetime = Field(..., description="Test end date")
    is_active: bool = Field(default=True, description="Whether test is active")
    
    @validator('traffic_percentage')
    def validate_traffic_percentage(cls, v):
        """Validate traffic percentage is within bounds"""
        if not 0 <= v <= 100:
            raise ValueError("Traffic percentage must be between 0 and 100")
        return v
    
    def should_use_new_version(self, user_id: str) -> bool:
        """Determine if user should use new version based on A/B test config"""
        if not self.is_active:
            return False
            
        # Simple hash-based assignment for consistent routing
        import hashlib
        hash_value = int(hashlib.md5(f"{user_id}{self.test_name}".encode()).hexdigest()[:8], 16)
        percentage = (hash_value % 100) + 1
        
        return percentage <= self.traffic_percentage