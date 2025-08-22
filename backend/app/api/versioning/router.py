"""
Versioned API Router - Enhanced FastAPI router with versioning capabilities
"""

import logging
from typing import Any, Callable, Dict, List, Optional, Sequence, Type, Union
from fastapi import APIRouter, Request, Response, HTTPException, Depends
from fastapi.routing import APIRoute
from fastapi.responses import JSONResponse
from starlette.routing import Match

from .manager import VersionManager
from .models import VersionedEndpoint

logger = logging.getLogger(__name__)


class VersionedAPIRoute(APIRoute):
    """Custom API route with version support"""
    
    def __init__(
        self,
        path: str,
        endpoint: Callable[..., Any],
        *,
        min_version: Optional[str] = None,
        max_version: Optional[str] = None,
        deprecated_in: Optional[str] = None,
        removed_in: Optional[str] = None,
        version_changes: Optional[Dict[str, str]] = None,
        **kwargs
    ):
        super().__init__(path, endpoint, **kwargs)
        self.min_version = min_version
        self.max_version = max_version
        self.deprecated_in = deprecated_in
        self.removed_in = removed_in
        self.version_changes = version_changes or {}
    
    def matches(self, scope: Dict[str, Any]) -> tuple[Match, Dict[str, Any]]:
        """Override matches to include version checking"""
        match, path_info = super().matches(scope)
        
        if match != Match.FULL:
            return match, path_info
        
        # Check version compatibility
        request = Request(scope)
        if hasattr(request.state, 'api_version'):
            version = request.state.api_version
            
            if not self._is_version_compatible(version):
                return Match.NONE, {}
        
        return match, path_info
    
    def _is_version_compatible(self, version: str) -> bool:
        """Check if route is compatible with the version"""
        from semantic_version import Version
        
        try:
            version_obj = Version(version)
            
            if self.min_version:
                min_obj = Version(self.min_version)
                if version_obj < min_obj:
                    return False
            
            if self.max_version:
                max_obj = Version(self.max_version)
                if version_obj > max_obj:
                    return False
            
            if self.removed_in:
                removed_obj = Version(self.removed_in)
                if version_obj >= removed_obj:
                    return False
            
            return True
            
        except ValueError:
            logger.error(f"Invalid version format: {version}")
            return False


class VersionedAPIRouter(APIRouter):
    """Enhanced API router with versioning capabilities"""
    
    def __init__(
        self,
        version_manager: VersionManager,
        version: Optional[str] = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.version_manager = version_manager
        self.router_version = version
        self.versioned_endpoints: List[VersionedEndpoint] = []
        
        # Override route class
        kwargs.setdefault('route_class', VersionedAPIRoute)
    
    def add_api_route(
        self,
        path: str,
        endpoint: Callable[..., Any],
        *,
        min_version: Optional[str] = None,
        max_version: Optional[str] = None,
        deprecated_in: Optional[str] = None,
        removed_in: Optional[str] = None,
        version_changes: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> None:
        """Add versioned API route"""
        
        # Use router version as default
        if not min_version and self.router_version:
            min_version = self.router_version
        
        # Create versioned route
        route = VersionedAPIRoute(
            path=path,
            endpoint=endpoint,
            min_version=min_version,
            max_version=max_version,
            deprecated_in=deprecated_in,
            removed_in=removed_in,
            version_changes=version_changes,
            **kwargs
        )
        
        self.routes.append(route)
        
        # Register endpoint metadata
        versioned_endpoint = VersionedEndpoint(
            path=path,
            methods=kwargs.get('methods', ['GET']),
            introduced_in=min_version or '1.0.0',
            deprecated_in=deprecated_in,
            removed_in=removed_in,
            changes=version_changes or {}
        )
        
        self.versioned_endpoints.append(versioned_endpoint)
        self.version_manager.add_endpoint(versioned_endpoint)
    
    def get(
        self,
        path: str,
        *,
        min_version: Optional[str] = None,
        max_version: Optional[str] = None,
        deprecated_in: Optional[str] = None,
        removed_in: Optional[str] = None,
        version_changes: Optional[Dict[str, str]] = None,
        **kwargs
    ):
        """Add GET route with version support"""
        return super().get(
            path,
            min_version=min_version,
            max_version=max_version,
            deprecated_in=deprecated_in,
            removed_in=removed_in,
            version_changes=version_changes,
            **kwargs
        )
    
    def post(
        self,
        path: str,
        *,
        min_version: Optional[str] = None,
        max_version: Optional[str] = None,
        deprecated_in: Optional[str] = None,
        removed_in: Optional[str] = None,
        version_changes: Optional[Dict[str, str]] = None,
        **kwargs
    ):
        """Add POST route with version support"""
        return super().post(
            path,
            min_version=min_version,
            max_version=max_version,
            deprecated_in=deprecated_in,
            removed_in=removed_in,
            version_changes=version_changes,
            **kwargs
        )
    
    def put(
        self,
        path: str,
        *,
        min_version: Optional[str] = None,
        max_version: Optional[str] = None,
        deprecated_in: Optional[str] = None,
        removed_in: Optional[str] = None,
        version_changes: Optional[Dict[str, str]] = None,
        **kwargs
    ):
        """Add PUT route with version support"""
        return super().put(
            path,
            min_version=min_version,
            max_version=max_version,
            deprecated_in=deprecated_in,
            removed_in=removed_in,
            version_changes=version_changes,
            **kwargs
        )
    
    def delete(
        self,
        path: str,
        *,
        min_version: Optional[str] = None,
        max_version: Optional[str] = None,
        deprecated_in: Optional[str] = None,
        removed_in: Optional[str] = None,
        version_changes: Optional[Dict[str, str]] = None,
        **kwargs
    ):
        """Add DELETE route with version support"""
        return super().delete(
            path,
            min_version=min_version,
            max_version=max_version,
            deprecated_in=deprecated_in,
            removed_in=removed_in,
            version_changes=version_changes,
            **kwargs
        )
    
    def patch(
        self,
        path: str,
        *,
        min_version: Optional[str] = None,
        max_version: Optional[str] = None,
        deprecated_in: Optional[str] = None,
        removed_in: Optional[str] = None,
        version_changes: Optional[Dict[str, str]] = None,
        **kwargs
    ):
        """Add PATCH route with version support"""
        return super().patch(
            path,
            min_version=min_version,
            max_version=max_version,
            deprecated_in=deprecated_in,
            removed_in=removed_in,
            version_changes=version_changes,
            **kwargs
        )
    
    def include_router(
        self,
        router: "APIRouter",
        *,
        prefix: str = "",
        tags: Optional[List[str]] = None,
        dependencies: Optional[Sequence[Depends]] = None,
        responses: Optional[Dict[Union[int, str], Dict[str, Any]]] = None,
        min_version: Optional[str] = None,
        max_version: Optional[str] = None,
        **kwargs
    ) -> None:
        """Include router with version constraints"""
        
        # Apply version constraints to all routes in the included router
        if isinstance(router, VersionedAPIRouter):
            # Transfer version constraints
            for route in router.routes:
                if isinstance(route, VersionedAPIRoute):
                    if min_version and not route.min_version:
                        route.min_version = min_version
                    if max_version and not route.max_version:
                        route.max_version = max_version
        
        super().include_router(
            router,
            prefix=prefix,
            tags=tags,
            dependencies=dependencies,
            responses=responses,
            **kwargs
        )
    
    def get_endpoints_for_version(self, version: str) -> List[VersionedEndpoint]:
        """Get all endpoints available for a specific version"""
        return [
            endpoint for endpoint in self.versioned_endpoints
            if endpoint.is_available_in_version(version)
        ]
    
    def get_deprecated_endpoints(self, version: str) -> List[VersionedEndpoint]:
        """Get deprecated endpoints for a specific version"""
        return [
            endpoint for endpoint in self.versioned_endpoints
            if endpoint.is_deprecated_in_version(version)
        ]
    
    def validate_version_compatibility(self, version: str) -> Dict[str, Any]:
        """Validate version compatibility for all endpoints"""
        available_endpoints = self.get_endpoints_for_version(version)
        deprecated_endpoints = self.get_deprecated_endpoints(version)
        
        return {
            'version': version,
            'total_endpoints': len(self.versioned_endpoints),
            'available_endpoints': len(available_endpoints),
            'deprecated_endpoints': len(deprecated_endpoints),
            'compatibility_score': (
                len(available_endpoints) / len(self.versioned_endpoints)
                if self.versioned_endpoints else 1.0
            )
        }


def create_version_dependency(version_manager: VersionManager):
    """Create a dependency to inject version information"""
    
    async def get_version_info(request: Request) -> Dict[str, Any]:
        """Extract version information from request"""
        version = getattr(request.state, 'api_version', None)
        
        if not version:
            # Fallback to latest version
            latest = version_manager.get_latest_version()
            version = latest.version if latest else '1.0.0'
        
        version_obj = version_manager.get_version(version)
        
        return {
            'version': version,
            'version_object': version_obj,
            'is_deprecated': version_obj.is_deprecated if version_obj else False,
            'is_supported': version_obj.is_supported if version_obj else True,
            'source': getattr(request.state, 'version_source', 'default')
        }
    
    return get_version_info


def create_deprecation_warning_dependency(version_manager: VersionManager):
    """Create a dependency to add deprecation warnings to responses"""
    
    async def add_deprecation_warnings(
        request: Request,
        response: Response,
        version_info: Dict = Depends(create_version_dependency(version_manager))
    ):
        """Add deprecation warnings to response headers"""
        
        if version_info['is_deprecated']:
            version_obj = version_info['version_object']
            
            response.headers["X-API-Deprecated"] = "true"
            response.headers["X-API-Deprecation-Message"] = (
                f"API version {version_info['version']} is deprecated"
            )
            
            if version_obj and version_obj.retirement_date:
                response.headers["X-API-Retirement-Date"] = (
                    version_obj.retirement_date.isoformat()
                )
                
                days_until_retirement = version_obj.days_until_retirement()
                if days_until_retirement is not None:
                    response.headers["X-API-Days-Until-Retirement"] = (
                        str(days_until_retirement)
                    )
            
            # Add migration guide if available
            latest = version_manager.get_latest_version()
            if latest:
                compatibility = version_manager.get_compatibility(
                    version_info['version'], latest.version
                )
                if compatibility and compatibility.migration_guide_url:
                    response.headers["X-API-Migration-Guide"] = (
                        compatibility.migration_guide_url
                    )
    
    return add_deprecation_warnings


class VersionSpecificRouter:
    """Factory for creating version-specific routers"""
    
    def __init__(self, version_manager: VersionManager):
        self.version_manager = version_manager
    
    def create_router(
        self,
        version: str,
        prefix: str = "",
        tags: Optional[List[str]] = None,
        **kwargs
    ) -> VersionedAPIRouter:
        """Create a router for a specific version"""
        
        # Validate version exists
        if not self.version_manager.get_version(version):
            raise ValueError(f"Version {version} is not registered")
        
        router = VersionedAPIRouter(
            version_manager=self.version_manager,
            version=version,
            prefix=prefix,
            tags=tags or [f"v{version.split('.')[0]}"],
            **kwargs
        )
        
        return router
    
    def create_legacy_router(
        self,
        version: str,
        target_version: str,
        **kwargs
    ) -> VersionedAPIRouter:
        """Create a legacy router that redirects to newer version"""
        
        router = self.create_router(version, **kwargs)
        
        @router.middleware("http")
        async def legacy_redirect_middleware(request: Request, call_next):
            """Middleware to handle legacy version redirects"""
            
            # Add legacy headers
            response = await call_next(request)
            
            response.headers["X-API-Legacy"] = "true"
            response.headers["X-API-Recommended-Version"] = target_version
            response.headers["X-API-Legacy-Support"] = "limited"
            
            # Add migration warning
            compatibility = self.version_manager.get_compatibility(version, target_version)
            if compatibility and compatibility.migration_guide_url:
                response.headers["X-API-Migration-Guide"] = compatibility.migration_guide_url
            
            return response
        
        return router