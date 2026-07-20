"""
Versioning Middleware - Handle version negotiation and routing
"""

import logging
import time
from typing import Callable, Optional
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from .manager import VersionManager
from .negotiation import VersionNegotiator

logger = logging.getLogger(__name__)


class VersioningMiddleware(BaseHTTPMiddleware):
    """Middleware to handle API versioning"""
    
    def __init__(self, app, version_manager: VersionManager):
        super().__init__(app)
        self.version_manager = version_manager
        self.negotiator = VersionNegotiator(version_manager)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with version handling"""
        start_time = time.time()
        
        try:
            # Extract version information
            version_info = await self._extract_version_info(request)
            
            # Validate version
            if not self._validate_version(version_info['version']):
                return self._create_version_error_response(
                    version_info['version'],
                    "Unsupported API version"
                )
            
            # Check for deprecation warnings
            deprecation_info = self._check_deprecation(version_info['version'])
            
            # Store version info in request state
            request.state.api_version = version_info['version']
            request.state.version_source = version_info['source']
            request.state.client_info = version_info.get('client_info', {})
            
            # Process A/B testing if applicable
            if hasattr(request.state, 'user_id'):
                version_info['version'] = self._handle_ab_testing(
                    request.state.user_id,
                    version_info['version']
                )
                request.state.api_version = version_info['version']
            
            # Call the next middleware/endpoint
            response = await call_next(request)
            
            # Add version headers to response
            self._add_version_headers(response, version_info['version'], deprecation_info)
            
            # Record metrics
            self._record_metrics(
                version_info['version'],
                request,
                response,
                time.time() - start_time
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Version middleware error: {e}")
            # Record error metrics if version was determined
            if hasattr(request.state, 'api_version'):
                self.version_manager.record_metrics(
                    request.state.api_version,
                    error=True,
                    response_time_ms=(time.time() - start_time) * 1000
                )
            
            # Re-raise the exception
            raise
    
    async def _extract_version_info(self, request: Request) -> dict:
        """Extract version information from request"""
        version_info = {
            'version': None,
            'source': None,
            'client_info': {}
        }
        
        # 1. Check URL path first (/api/v1/...)
        path = request.url.path
        if path.startswith('/api/v'):
            path_parts = path.split('/')
            if len(path_parts) >= 3:
                version_part = path_parts[2]  # v1, v2, etc.
                if version_part.startswith('v'):
                    try:
                        major_version = version_part[1:]
                        # Map to full semantic version
                        version_info['version'] = await self._resolve_version_from_major(major_version)
                        version_info['source'] = 'url_path'
                    except ValueError:
                        pass
        
        # 2. Check Accept header version negotiation
        if not version_info['version']:
            accept_header = request.headers.get('accept', '')
            version = self.negotiator.negotiate_from_accept_header(accept_header)
            if version:
                version_info['version'] = version
                version_info['source'] = 'accept_header'
        
        # 3. Check custom version header
        if not version_info['version']:
            api_version_header = request.headers.get('api-version') or request.headers.get('x-api-version')
            if api_version_header:
                version_info['version'] = api_version_header
                version_info['source'] = 'custom_header'
        
        # 4. Check query parameter
        if not version_info['version']:
            version_param = request.query_params.get('version') or request.query_params.get('api_version')
            if version_param:
                version_info['version'] = version_param
                version_info['source'] = 'query_param'
        
        # 5. Default to latest stable version
        if not version_info['version']:
            latest = self.version_manager.get_latest_version()
            if latest:
                version_info['version'] = latest.version
                version_info['source'] = 'default'
        
        # Extract client information
        version_info['client_info'] = {
            'user_agent': request.headers.get('user-agent', ''),
            'client_id': request.headers.get('x-client-id', ''),
            'client_version': request.headers.get('x-client-version', ''),
            'platform': request.headers.get('x-platform', ''),
        }
        
        return version_info
    
    async def _resolve_version_from_major(self, major_version: str) -> str:
        """Resolve full semantic version from major version"""
        # Find the latest stable version for the major version
        all_versions = self.version_manager.get_supported_versions()
        
        matching_versions = [
            v for v in all_versions 
            if v.version.startswith(f"{major_version}.")
        ]
        
        if not matching_versions:
            raise ValueError(f"No supported versions found for major version {major_version}")
        
        # Return the latest stable version for this major version
        latest = max(matching_versions, key=lambda v: v.semantic_version)
        return latest.version
    
    def _validate_version(self, version: str) -> bool:
        """Validate if version is supported"""
        if not version:
            return False
        
        return self.version_manager.is_version_supported(version)
    
    def _check_deprecation(self, version: str) -> Optional[dict]:
        """Check if version is deprecated and return warning info"""
        api_version = self.version_manager.get_version(version)
        
        if not api_version or not api_version.is_deprecated:
            return None
        
        deprecation_info = {
            'deprecated': True,
            'deprecation_date': api_version.deprecation_date.isoformat() if api_version.deprecation_date else None,
            'retirement_date': api_version.retirement_date.isoformat() if api_version.retirement_date else None,
            'message': f"API version {version} is deprecated",
            'migration_guide': None
        }
        
        # Add migration guide if available
        latest = self.version_manager.get_latest_version()
        if latest:
            compatibility = self.version_manager.get_compatibility(version, latest.version)
            if compatibility and compatibility.migration_guide_url:
                deprecation_info['migration_guide'] = compatibility.migration_guide_url
        
        # Add days until retirement
        days_until_retirement = api_version.days_until_retirement()
        if days_until_retirement is not None:
            deprecation_info['days_until_retirement'] = days_until_retirement
        
        return deprecation_info
    
    def _handle_ab_testing(self, user_id: str, current_version: str) -> str:
        """Handle A/B testing for version migration"""
        active_tests = self.version_manager.get_active_ab_tests()
        
        for test in active_tests:
            if test.from_version == current_version:
                new_version = self.version_manager.should_use_version_for_test(
                    test.test_name, user_id, current_version
                )
                if new_version != current_version:
                    logger.info(f"A/B test {test.test_name}: routing user {user_id} to version {new_version}")
                    return new_version
        
        return current_version
    
    def _add_version_headers(self, response: Response, version: str, deprecation_info: Optional[dict]):
        """Add version-related headers to response"""
        response.headers["X-API-Version"] = version
        response.headers["X-API-Version-Requested"] = version
        
        # Add deprecation warnings
        if deprecation_info:
            response.headers["X-API-Deprecated"] = "true"
            response.headers["X-API-Deprecation-Date"] = deprecation_info.get('deprecation_date', '')
            
            if deprecation_info.get('retirement_date'):
                response.headers["X-API-Retirement-Date"] = deprecation_info['retirement_date']
            
            if deprecation_info.get('days_until_retirement'):
                response.headers["X-API-Days-Until-Retirement"] = str(deprecation_info['days_until_retirement'])
            
            if deprecation_info.get('migration_guide'):
                response.headers["X-API-Migration-Guide"] = deprecation_info['migration_guide']
            
            # Add deprecation warning to response body if it's JSON
            if hasattr(response, 'body') and response.media_type == 'application/json':
                # This would require modifying the response body, which is complex
                # Instead, we rely on headers and documentation
                pass
        
        # Add supported versions
        supported_versions = [v.version for v in self.version_manager.get_supported_versions()]
        response.headers["X-API-Supported-Versions"] = ",".join(supported_versions)
        
        # Add latest version
        latest = self.version_manager.get_latest_version()
        if latest:
            response.headers["X-API-Latest-Version"] = latest.version
    
    def _record_metrics(self, version: str, request: Request, response: Response, response_time: float):
        """Record metrics for the request"""
        client_info = getattr(request.state, 'client_info', {})
        client_type = self._determine_client_type(client_info)
        
        is_error = response.status_code >= 400
        
        self.version_manager.record_metrics(
            version=version,
            request_count=1,
            response_time_ms=response_time * 1000,
            error=is_error,
            client_type=client_type
        )
    
    def _determine_client_type(self, client_info: dict) -> str:
        """Determine client type from client info"""
        user_agent = client_info.get('user_agent', '').lower()
        client_id = client_info.get('client_id', '')
        
        if 'mobile' in user_agent or 'android' in user_agent or 'iphone' in user_agent:
            return 'mobile'
        elif 'postman' in user_agent:
            return 'postman'
        elif 'curl' in user_agent:
            return 'curl'
        elif 'python' in user_agent:
            return 'python-sdk'
        elif 'javascript' in user_agent or 'nodejs' in user_agent:
            return 'javascript-sdk'
        elif client_id:
            return f"client-{client_id}"
        else:
            return 'unknown'
    
    def _create_version_error_response(self, version: str, message: str) -> JSONResponse:
        """Create error response for version issues"""
        supported_versions = [v.version for v in self.version_manager.get_supported_versions()]
        
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": "unsupported_api_version",
                "message": message,
                "requested_version": version,
                "supported_versions": supported_versions,
                "latest_version": self.version_manager.get_latest_version().version if self.version_manager.get_latest_version() else None,
                "documentation": "/docs/api-versioning"
            },
            headers={
                "X-API-Error": "unsupported_version",
                "X-API-Supported-Versions": ",".join(supported_versions)
            }
        )


class VersionValidationMiddleware(BaseHTTPMiddleware):
    """Middleware specifically for version validation before routing"""
    
    def __init__(self, app, version_manager: VersionManager):
        super().__init__(app)
        self.version_manager = version_manager
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Validate version before processing"""
        # Skip validation for health checks and documentation
        if request.url.path in ['/health', '/docs', '/redoc', '/openapi.json']:
            return await call_next(request)
        
        # Extract version from URL path
        path = request.url.path
        if path.startswith('/api/v'):
            path_parts = path.split('/')
            if len(path_parts) >= 3:
                version_part = path_parts[2]
                if version_part.startswith('v'):
                    major_version = version_part[1:]
                    
                    # Check if any version exists for this major version
                    all_versions = self.version_manager.get_all_versions()
                    has_version = any(
                        v.version.startswith(f"{major_version}.")
                        for v in all_versions
                    )
                    
                    if not has_version:
                        return JSONResponse(
                            status_code=status.HTTP_404_NOT_FOUND,
                            content={
                                "error": "version_not_found",
                                "message": f"API version {version_part} does not exist",
                                "available_versions": [
                                    f"v{v.version.split('.')[0]}" 
                                    for v in all_versions
                                ]
                            }
                        )
        
        return await call_next(request)