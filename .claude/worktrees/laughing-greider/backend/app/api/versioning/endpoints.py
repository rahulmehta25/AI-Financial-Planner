"""
API Versioning Management Endpoints
"""

import logging
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Depends, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from datetime import datetime

from .config import get_versioning_system, VersioningSystem
from .models import APIVersion, VersionStatus, ClientSDKInfo, ABTestConfig

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/versioning", tags=["versioning"])


# Request/Response Models
class VersionCreateRequest(BaseModel):
    """Request model for creating a new version"""
    version: str = Field(..., description="Semantic version string")
    description: str = Field(..., description="Version description")
    status: VersionStatus = Field(default=VersionStatus.DEVELOPMENT)
    breaking_changes: List[str] = Field(default_factory=list)
    new_features: List[str] = Field(default_factory=list)
    bug_fixes: List[str] = Field(default_factory=list)


class VersionResponse(BaseModel):
    """Response model for version information"""
    version: str
    status: str
    release_date: Optional[str]
    deprecation_date: Optional[str]
    retirement_date: Optional[str]
    description: str
    breaking_changes: List[str]
    new_features: List[str]
    bug_fixes: List[str]
    is_supported: bool
    is_deprecated: bool
    is_retired: bool


class CompatibilityCheckRequest(BaseModel):
    """Request model for compatibility check"""
    from_version: str
    to_version: str


class ABTestCreateRequest(BaseModel):
    """Request model for creating A/B test"""
    test_name: str
    from_version: str
    to_version: str
    traffic_percentage: float = Field(ge=0.0, le=100.0)
    user_segments: List[str] = Field(default_factory=list)
    duration_days: int = Field(default=30, ge=1, le=365)


class SDKRecommendationRequest(BaseModel):
    """Request model for SDK recommendations"""
    language: str
    api_version: str


# Helper function to get versioning system
def get_versioning_dep() -> VersioningSystem:
    """Dependency to get versioning system"""
    return get_versioning_system()


# Version Management Endpoints
@router.get("/versions", response_model=List[VersionResponse])
async def get_all_versions(
    supported_only: bool = False,
    versioning: VersioningSystem = Depends(get_versioning_dep)
):
    """Get all API versions"""
    
    if supported_only:
        versions = versioning.version_manager.get_supported_versions()
    else:
        versions = versioning.version_manager.get_all_versions()
    
    return [
        VersionResponse(
            version=v.version,
            status=v.status.value,
            release_date=v.release_date.isoformat() if v.release_date else None,
            deprecation_date=v.deprecation_date.isoformat() if v.deprecation_date else None,
            retirement_date=v.retirement_date.isoformat() if v.retirement_date else None,
            description=v.description,
            breaking_changes=v.breaking_changes,
            new_features=v.new_features,
            bug_fixes=v.bug_fixes,
            is_supported=v.is_supported,
            is_deprecated=v.is_deprecated,
            is_retired=v.is_retired
        )
        for v in versions
    ]


@router.get("/versions/{version}", response_model=VersionResponse)
async def get_version(
    version: str,
    versioning: VersioningSystem = Depends(get_versioning_dep)
):
    """Get specific version information"""
    
    v = versioning.version_manager.get_version(version)
    if not v:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Version {version} not found"
        )
    
    return VersionResponse(
        version=v.version,
        status=v.status.value,
        release_date=v.release_date.isoformat() if v.release_date else None,
        deprecation_date=v.deprecation_date.isoformat() if v.deprecation_date else None,
        retirement_date=v.retirement_date.isoformat() if v.retirement_date else None,
        description=v.description,
        breaking_changes=v.breaking_changes,
        new_features=v.new_features,
        bug_fixes=v.bug_fixes,
        is_supported=v.is_supported,
        is_deprecated=v.is_deprecated,
        is_retired=v.is_retired
    )


@router.post("/versions", response_model=VersionResponse)
async def create_version(
    request: VersionCreateRequest,
    versioning: VersioningSystem = Depends(get_versioning_dep)
):
    """Create a new API version"""
    
    # Check if version already exists
    existing = versioning.version_manager.get_version(request.version)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Version {request.version} already exists"
        )
    
    # Create new version
    new_version = APIVersion(
        version=request.version,
        status=request.status,
        release_date=datetime.utcnow(),
        description=request.description,
        breaking_changes=request.breaking_changes,
        new_features=request.new_features,
        bug_fixes=request.bug_fixes
    )
    
    success = versioning.version_manager.add_version(new_version)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create version"
        )
    
    return VersionResponse(
        version=new_version.version,
        status=new_version.status.value,
        release_date=new_version.release_date.isoformat(),
        deprecation_date=None,
        retirement_date=None,
        description=new_version.description,
        breaking_changes=new_version.breaking_changes,
        new_features=new_version.new_features,
        bug_fixes=new_version.bug_fixes,
        is_supported=new_version.is_supported,
        is_deprecated=new_version.is_deprecated,
        is_retired=new_version.is_retired
    )


@router.post("/versions/{version}/deprecate")
async def deprecate_version(
    version: str,
    versioning: VersioningSystem = Depends(get_versioning_dep)
):
    """Deprecate an API version"""
    
    success = versioning.version_manager.deprecate_version(version)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to deprecate version {version}"
        )
    
    return {"message": f"Version {version} deprecated successfully"}


@router.post("/versions/{version}/retire")
async def retire_version(
    version: str,
    versioning: VersioningSystem = Depends(get_versioning_dep)
):
    """Retire an API version"""
    
    success = versioning.version_manager.retire_version(version)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to retire version {version}"
        )
    
    return {"message": f"Version {version} retired successfully"}


# Compatibility Endpoints
@router.post("/compatibility/check")
async def check_compatibility(
    request: CompatibilityCheckRequest,
    versioning: VersioningSystem = Depends(get_versioning_dep)
):
    """Check compatibility between two versions"""
    
    if not versioning.compatibility_analyzer:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Compatibility analysis not available"
        )
    
    analysis = versioning.compatibility_analyzer.analyze_compatibility(
        request.from_version, request.to_version
    )
    
    if 'error' in analysis:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=analysis['error']
        )
    
    return analysis


@router.get("/compatibility/matrix")
async def get_compatibility_matrix(
    versioning: VersioningSystem = Depends(get_versioning_dep)
):
    """Get full compatibility matrix"""
    
    if not versioning.compatibility_analyzer:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Compatibility analysis not available"
        )
    
    return versioning.version_manager.get_compatibility_matrix()


@router.post("/migration/plan")
async def create_migration_plan(
    request: CompatibilityCheckRequest,
    versioning: VersioningSystem = Depends(get_versioning_dep)
):
    """Create a comprehensive migration plan"""
    
    plan = versioning.create_migration_plan(
        request.from_version, request.to_version
    )
    
    return plan


# SDK Management Endpoints
@router.get("/sdk/languages")
async def get_supported_languages(
    versioning: VersioningSystem = Depends(get_versioning_dep)
):
    """Get supported SDK languages"""
    
    if not versioning.sdk_manager:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="SDK management not available"
        )
    
    return {
        "languages": list(versioning.sdk_manager.compatibility_matrices.keys())
    }


@router.get("/sdk/compatibility/{language}")
async def get_sdk_compatibility(
    language: str,
    versioning: VersioningSystem = Depends(get_versioning_dep)
):
    """Get SDK compatibility matrix for a language"""
    
    if not versioning.sdk_manager:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="SDK management not available"
        )
    
    matrix = versioning.sdk_manager.get_compatibility_matrix(language)
    if not matrix:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No SDK compatibility data for language: {language}"
        )
    
    return {
        "language": matrix.language,
        "platform": matrix.platform,
        "last_updated": matrix.last_updated.isoformat(),
        "matrix": matrix.matrix
    }


@router.post("/sdk/recommendations")
async def get_sdk_recommendations(
    request: SDKRecommendationRequest,
    versioning: VersioningSystem = Depends(get_versioning_dep)
):
    """Get SDK recommendations for language and API version"""
    
    if not versioning.sdk_manager:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="SDK management not available"
        )
    
    recommendations = versioning.sdk_manager.generate_sdk_recommendations(
        request.language, request.api_version
    )
    
    return recommendations


@router.get("/sdk/report")
async def get_sdk_compatibility_report(
    versioning: VersioningSystem = Depends(get_versioning_dep)
):
    """Get comprehensive SDK compatibility report"""
    
    if not versioning.sdk_manager:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="SDK management not available"
        )
    
    return versioning.sdk_manager.generate_sdk_compatibility_report()


# A/B Testing Endpoints
@router.get("/ab-tests")
async def get_ab_tests(
    active_only: bool = False,
    versioning: VersioningSystem = Depends(get_versioning_dep)
):
    """Get A/B tests"""
    
    if not versioning.ab_test_manager:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="A/B testing not available"
        )
    
    if active_only:
        tests = versioning.ab_test_manager.get_active_tests()
    else:
        tests = list(versioning.ab_test_manager.tests.values())
    
    return [test.dict() for test in tests]


@router.post("/ab-tests")
async def create_ab_test(
    request: ABTestCreateRequest,
    versioning: VersioningSystem = Depends(get_versioning_dep)
):
    """Create a new A/B test"""
    
    if not versioning.ab_test_manager:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="A/B testing not available"
        )
    
    success = versioning.ab_test_manager.create_ab_test(
        test_name=request.test_name,
        from_version=request.from_version,
        to_version=request.to_version,
        traffic_percentage=request.traffic_percentage,
        user_segments=request.user_segments,
        duration_days=request.duration_days
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create A/B test"
        )
    
    return {"message": f"A/B test {request.test_name} created successfully"}


@router.get("/ab-tests/{test_name}/results")
async def get_ab_test_results(
    test_name: str,
    versioning: VersioningSystem = Depends(get_versioning_dep)
):
    """Get A/B test results"""
    
    if not versioning.ab_test_manager:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="A/B testing not available"
        )
    
    results = versioning.ab_test_manager.analyze_test_results(test_name)
    
    if 'error' in results:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=results['error']
        )
    
    return results


@router.get("/ab-tests/dashboard")
async def get_ab_test_dashboard(
    versioning: VersioningSystem = Depends(get_versioning_dep)
):
    """Get A/B testing dashboard"""
    
    if not versioning.ab_test_manager:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="A/B testing not available"
        )
    
    return versioning.ab_test_manager.get_test_dashboard()


# Documentation Endpoints
@router.post("/documentation/generate")
async def generate_documentation(
    version: Optional[str] = None,
    versioning: VersioningSystem = Depends(get_versioning_dep)
):
    """Generate documentation for versions"""
    
    if not versioning.documentation_generator:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Documentation generation not available"
        )
    
    if version:
        # Generate for specific version
        try:
            files = versioning.documentation_generator.export_documentation(version)
            return {
                "message": f"Documentation generated for version {version}",
                "files": files
            }
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
    else:
        # Generate for all versions
        files = versioning.generate_all_documentation()
        return {
            "message": "Documentation generated for all versions",
            "files": files
        }


# Gateway Configuration Endpoints
@router.post("/gateway/export")
async def export_gateway_configs(
    versioning: VersioningSystem = Depends(get_versioning_dep)
):
    """Export gateway configurations"""
    
    if not versioning.gateway_generator:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Gateway configuration not available"
        )
    
    files = versioning.export_all_gateway_configs()
    return {
        "message": "Gateway configurations exported",
        "files": files
    }


# System Status and Health Endpoints
@router.get("/status")
async def get_system_status(
    versioning: VersioningSystem = Depends(get_versioning_dep)
):
    """Get versioning system status"""
    return versioning.get_system_status()


@router.get("/health")
async def get_system_health(
    versioning: VersioningSystem = Depends(get_versioning_dep)
):
    """Get versioning system health check"""
    return versioning.validate_system_health()


# Version Negotiation Endpoint
@router.get("/negotiate")
async def negotiate_version(
    request: Request,
    user_id: Optional[str] = None,
    versioning: VersioningSystem = Depends(get_versioning_dep)
):
    """Negotiate API version for a request"""
    
    # Extract user context from request
    user_context = {
        'user_agent': request.headers.get('user-agent', ''),
        'device_type': request.headers.get('x-device-type', ''),
        'client_version': request.headers.get('x-client-version', ''),
        'country': request.headers.get('x-country', ''),
        'user_id': user_id
    }
    
    # Get version for request
    version = versioning.get_version_for_request(
        user_id=user_id,
        user_context=user_context
    )
    
    # Get version object
    version_obj = versioning.version_manager.get_version(version)
    
    response_data = {
        'negotiated_version': version,
        'version_source': 'system_default',
        'user_context': user_context
    }
    
    if version_obj:
        response_data['version_info'] = {
            'status': version_obj.status.value,
            'is_deprecated': version_obj.is_deprecated,
            'is_supported': version_obj.is_supported
        }
    
    # Create response with version headers
    response = JSONResponse(content=response_data)
    response.headers['X-API-Version'] = version
    response.headers['X-API-Version-Negotiated'] = 'true'
    
    if version_obj and version_obj.is_deprecated:
        response.headers['X-API-Deprecated'] = 'true'
        if version_obj.retirement_date:
            response.headers['X-API-Retirement-Date'] = version_obj.retirement_date.isoformat()
    
    return response


# Configuration Management
@router.post("/config/save")
async def save_configuration(
    versioning: VersioningSystem = Depends(get_versioning_dep)
):
    """Save all versioning configurations"""
    
    versioning.save_configuration()
    return {"message": "Configuration saved successfully"}


@router.get("/config/export")
async def export_all_data(
    versioning: VersioningSystem = Depends(get_versioning_dep)
):
    """Export all versioning data"""
    
    exported_files = {}
    
    # Export documentation
    if versioning.documentation_generator:
        doc_files = versioning.generate_all_documentation()
        exported_files['documentation'] = doc_files
    
    # Export SDK matrices
    if versioning.sdk_manager:
        sdk_files = versioning.export_all_sdk_matrices()
        exported_files['sdk_compatibility'] = sdk_files
    
    # Export gateway configs
    if versioning.gateway_generator:
        gateway_files = versioning.export_all_gateway_configs()
        exported_files['gateway_configs'] = gateway_files
    
    # Export A/B test results
    if versioning.ab_test_manager:
        ab_test_files = versioning.export_ab_test_results()
        exported_files['ab_test_results'] = ab_test_files
    
    return {
        "message": "All versioning data exported",
        "exported_files": exported_files
    }