"""
Security Middleware - Request/Response Security Layer

Implements comprehensive security middleware for FastAPI:
- Authentication verification
- Authorization checks
- Rate limiting
- Security headers injection
- Request/response logging
- Threat detection
- Input sanitization
- CORS handling
"""

import json
import time
import uuid
from typing import Callable, Optional, Dict, Any, List
from datetime import datetime

from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette.types import ASGIApp

from app.security.security_manager import (
    SecurityManager,
    SecurityConfig,
    SecurityContext,
    SecurityLevel,
    InputValidator,
    get_security_manager
)
from app.core.config import settings

import logging
logger = logging.getLogger(__name__)


class SecurityMiddleware(BaseHTTPMiddleware):
    """
    Main security middleware implementing defense-in-depth
    """
    
    def __init__(
        self,
        app: ASGIApp,
        security_config: Optional[SecurityConfig] = None,
        excluded_paths: Optional[List[str]] = None
    ):
        super().__init__(app)
        self.security_config = security_config or SecurityConfig()
        self.excluded_paths = excluded_paths or [
            "/health",
            "/metrics",
            "/docs",
            "/openapi.json",
            "/favicon.ico"
        ]
        self.security_manager: Optional[SecurityManager] = None
        self.request_counter = 0
        self.start_time = time.time()
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request through security pipeline"""
        
        # Generate request ID for tracking
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Skip security for excluded paths
        if any(request.url.path.startswith(path) for path in self.excluded_paths):
            response = await call_next(request)
            return response
        
        # Initialize security manager if needed
        if not self.security_manager:
            self.security_manager = await get_security_manager()
        
        # Track request metrics
        self.request_counter += 1
        start_time = time.time()
        
        try:
            # ===== Pre-processing Security Checks =====
            
            # 1. Rate limiting check
            if self.security_config.enable_rate_limiting:
                await self._check_rate_limit(request)
            
            # 2. Threat detection
            if self.security_config.enable_threat_detection:
                await self._detect_threats(request)
            
            # 3. Input validation for POST/PUT/PATCH requests
            if request.method in ["POST", "PUT", "PATCH"]:
                await self._validate_request_body(request)
            
            # 4. Validate security context (auth, permissions)
            security_context = await self._build_security_context(request)
            request.state.security_context = security_context
            
            # 5. Check CSRF token for state-changing operations
            if self.security_config.csrf_protection:
                await self._validate_csrf(request, security_context)
            
            # ===== Process Request =====
            response = await call_next(request)
            
            # ===== Post-processing Security =====
            
            # 6. Add security headers
            self._add_security_headers(response)
            
            # 7. Log successful request
            processing_time = time.time() - start_time
            await self._log_request(
                request,
                response.status_code,
                processing_time,
                security_context
            )
            
            # 8. Add request tracking headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Processing-Time"] = f"{processing_time:.3f}s"
            
            return response
            
        except HTTPException as e:
            # Handle expected HTTP exceptions
            processing_time = time.time() - start_time
            await self._log_request(
                request,
                e.status_code,
                processing_time,
                None,
                error=str(e.detail)
            )
            
            return JSONResponse(
                status_code=e.status_code,
                content={
                    "error": e.detail,
                    "request_id": request_id,
                    "timestamp": datetime.utcnow().isoformat()
                },
                headers=self._get_security_headers()
            )
            
        except Exception as e:
            # Handle unexpected errors
            processing_time = time.time() - start_time
            logger.error(f"Security middleware error: {str(e)}", exc_info=True)
            
            await self._log_request(
                request,
                500,
                processing_time,
                None,
                error="Internal server error"
            )
            
            # Don't expose internal errors to client
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": "Internal server error",
                    "request_id": request_id,
                    "timestamp": datetime.utcnow().isoformat()
                },
                headers=self._get_security_headers()
            )
    
    async def _check_rate_limit(self, request: Request):
        """Check rate limiting for the request"""
        
        # Get client identifier (IP or user ID)
        client_id = request.client.host if request.client else "unknown"
        
        # Check if we have auth header to get user-specific limit
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            try:
                token = auth_header.split(" ")[1]
                # Quick token decode to get user ID (without full validation)
                import jwt
                payload = jwt.decode(token, options={"verify_signature": False})
                client_id = f"user:{payload.get('sub', client_id)}"
            except:
                pass
        
        # Apply rate limiting
        if self.security_manager and self.security_manager.rate_limiter:
            # Different limits for different endpoints
            if "/auth" in request.url.path:
                max_requests = 5
                window = 900  # 15 minutes for auth endpoints
            elif request.method == "GET":
                max_requests = 100
                window = 60  # 1 minute for GET requests
            else:
                max_requests = 30
                window = 60  # 1 minute for POST/PUT/DELETE
            
            is_allowed = await self.security_manager.rate_limiter.check_limit(
                client_id,
                max_requests=max_requests,
                window_seconds=window
            )
            
            if not is_allowed:
                logger.warning(f"Rate limit exceeded for {client_id} on {request.url.path}")
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded. Please try again later."
                )
    
    async def _detect_threats(self, request: Request):
        """Detect potential security threats in the request"""
        
        if not self.security_manager or not self.security_manager.threat_detector:
            return
        
        # Extract request information
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("User-Agent")
        path = str(request.url.path)
        
        # Check for threats
        threat_detected = await self.security_manager.threat_detector.check_request(
            ip_address=ip_address,
            user_agent=user_agent,
            path=path,
            headers=dict(request.headers)
        )
        
        if threat_detected:
            logger.warning(f"Threat detected from {ip_address}: {threat_detected}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Security threat detected. Request blocked."
            )
    
    async def _validate_request_body(self, request: Request):
        """Validate request body for injection attacks"""
        
        try:
            # Get request body
            body = await request.body()
            if not body:
                return
            
            # Parse JSON body
            try:
                data = json.loads(body)
            except json.JSONDecodeError:
                # Not JSON, validate as string
                data = body.decode('utf-8', errors='ignore')
            
            # Validate all string fields
            validator = InputValidator()
            
            def validate_data(obj: Any, path: str = ""):
                if isinstance(obj, str):
                    is_valid, error = validator.validate_input(obj)
                    if not is_valid:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Invalid input at {path}: {error}"
                        )
                elif isinstance(obj, dict):
                    for key, value in obj.items():
                        validate_data(value, f"{path}.{key}" if path else key)
                elif isinstance(obj, list):
                    for i, item in enumerate(obj):
                        validate_data(item, f"{path}[{i}]")
            
            validate_data(data)
            
            # Store validated body for later use
            request.state.validated_body = data
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Body validation error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid request body"
            )
    
    async def _build_security_context(self, request: Request) -> SecurityContext:
        """Build security context from request"""
        
        context = SecurityContext(
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("User-Agent"),
            security_level=SecurityLevel.LOW
        )
        
        # Check for authentication
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            
            # Validate token and get user context
            if self.security_manager:
                try:
                    context = await self.security_manager.authorize(token)
                    context.ip_address = request.client.host if request.client else None
                    context.user_agent = request.headers.get("User-Agent")
                    context.device_fingerprint = request.headers.get("X-Device-Fingerprint")
                except HTTPException as e:
                    # For protected endpoints, re-raise the auth error
                    if not self._is_public_endpoint(request.url.path):
                        raise
                    # For public endpoints, continue without auth
        
        # Check if endpoint requires authentication
        elif not self._is_public_endpoint(request.url.path):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        return context
    
    async def _validate_csrf(self, request: Request, context: SecurityContext):
        """Validate CSRF token for state-changing operations"""
        
        # Skip CSRF for GET, HEAD, OPTIONS
        if request.method in ["GET", "HEAD", "OPTIONS"]:
            return
        
        # Skip if user not authenticated
        if not context.user:
            return
        
        # Check CSRF token
        csrf_token = request.headers.get("X-CSRF-Token")
        if not csrf_token:
            # Check in form data or JSON body
            if hasattr(request.state, "validated_body"):
                body = request.state.validated_body
                if isinstance(body, dict):
                    csrf_token = body.get("csrf_token")
        
        if not csrf_token:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="CSRF token missing"
            )
        
        # Validate CSRF token (implementation depends on your CSRF strategy)
        # For now, just ensure it's not empty
        if len(csrf_token) < 32:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid CSRF token"
            )
    
    def _add_security_headers(self, response: Response):
        """Add security headers to response"""
        
        headers = self._get_security_headers()
        for header, value in headers.items():
            response.headers[header] = value
    
    def _get_security_headers(self) -> Dict[str, str]:
        """Get security headers"""
        
        if self.security_manager:
            return self.security_manager.get_security_headers()
        
        return self.security_config.security_headers.copy()
    
    def _is_public_endpoint(self, path: str) -> bool:
        """Check if endpoint is public (no auth required)"""
        
        public_paths = [
            "/api/v1/auth/login",
            "/api/v1/auth/register",
            "/api/v1/auth/forgot-password",
            "/api/v1/auth/reset-password",
            "/api/v1/public",
            "/health",
            "/metrics"
        ]
        
        return any(path.startswith(p) for p in public_paths)
    
    async def _log_request(
        self,
        request: Request,
        status_code: int,
        processing_time: float,
        context: Optional[SecurityContext],
        error: Optional[str] = None
    ):
        """Log request for audit trail"""
        
        try:
            if self.security_manager and self.security_manager.audit_logger:
                await self.security_manager.audit_logger.log_request(
                    method=request.method,
                    path=str(request.url.path),
                    status_code=status_code,
                    processing_time=processing_time,
                    user_id=str(context.user.id) if context and context.user else None,
                    ip_address=request.client.host if request.client else None,
                    user_agent=request.headers.get("User-Agent"),
                    error=error
                )
        except Exception as e:
            logger.error(f"Failed to log request: {str(e)}")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get middleware metrics"""
        
        uptime = time.time() - self.start_time
        
        return {
            "requests_total": self.request_counter,
            "requests_per_second": self.request_counter / uptime if uptime > 0 else 0,
            "uptime_seconds": uptime,
            "security_config": {
                "mfa_enabled": self.security_config.enable_mfa,
                "encryption_enabled": self.security_config.enable_encryption,
                "rate_limiting_enabled": self.security_config.enable_rate_limiting,
                "threat_detection_enabled": self.security_config.enable_threat_detection
            }
        }


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Specialized middleware for distributed rate limiting
    """
    
    def __init__(
        self,
        app: ASGIApp,
        default_limit: int = 60,
        default_window: int = 60,
        custom_limits: Optional[Dict[str, tuple]] = None
    ):
        super().__init__(app)
        self.default_limit = default_limit
        self.default_window = default_window
        self.custom_limits = custom_limits or {
            "/api/v1/auth/login": (5, 900),  # 5 requests per 15 minutes
            "/api/v1/auth/register": (3, 3600),  # 3 requests per hour
            "/api/v1/simulations": (10, 60),  # 10 requests per minute
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Apply rate limiting"""
        
        # Get rate limiter
        security_manager = await get_security_manager()
        if not security_manager or not security_manager.rate_limiter:
            return await call_next(request)
        
        # Determine client ID
        client_id = request.client.host if request.client else "unknown"
        
        # Get rate limit for endpoint
        path = str(request.url.path)
        limit, window = self.custom_limits.get(path, (self.default_limit, self.default_window))
        
        # Apply rate limit
        rate_limit_key = f"{client_id}:{path}"
        is_allowed = await security_manager.rate_limiter.check_limit(
            rate_limit_key,
            max_requests=limit,
            window_seconds=window
        )
        
        if not is_allowed:
            remaining_time = await security_manager.rate_limiter.get_reset_time(rate_limit_key)
            
            response = JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Rate limit exceeded",
                    "retry_after": remaining_time
                }
            )
            response.headers["Retry-After"] = str(remaining_time)
            response.headers["X-RateLimit-Limit"] = str(limit)
            response.headers["X-RateLimit-Remaining"] = "0"
            response.headers["X-RateLimit-Reset"] = str(int(time.time()) + remaining_time)
            
            return response
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        remaining = await security_manager.rate_limiter.get_remaining(rate_limit_key, limit)
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(time.time()) + window)
        
        return response


class JWTMiddleware(BaseHTTPMiddleware):
    """
    JWT authentication middleware with automatic token refresh
    """
    
    def __init__(
        self,
        app: ASGIApp,
        excluded_paths: Optional[List[str]] = None,
        auto_refresh: bool = True
    ):
        super().__init__(app)
        self.excluded_paths = excluded_paths or [
            "/api/v1/auth",
            "/health",
            "/docs"
        ]
        self.auto_refresh = auto_refresh
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process JWT authentication"""
        
        # Skip for excluded paths
        if any(str(request.url.path).startswith(path) for path in self.excluded_paths):
            return await call_next(request)
        
        # Get token from header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"error": "Missing or invalid authorization header"}
            )
        
        token = auth_header.split(" ")[1]
        
        # Validate token
        security_manager = await get_security_manager()
        if not security_manager:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"error": "Security system not initialized"}
            )
        
        try:
            # Verify token and get claims
            claims = await security_manager.auth_service.verify_token(token)
            
            # Check if token is about to expire (within 5 minutes)
            exp_timestamp = claims.get("exp", 0)
            time_until_expiry = exp_timestamp - time.time()
            
            # Store user info in request state
            request.state.user_id = claims.get("sub")
            request.state.user_permissions = claims.get("permissions", [])
            
            # Process request
            response = await call_next(request)
            
            # Auto-refresh token if needed
            if self.auto_refresh and time_until_expiry < 300:  # Less than 5 minutes
                # Generate new token
                user = await security_manager._get_user(claims.get("sub"))
                if user:
                    new_token = await security_manager.auth_service._create_access_token(user)
                    response.headers["X-New-Token"] = new_token
                    response.headers["X-Token-Refreshed"] = "true"
            
            return response
            
        except HTTPException as e:
            return JSONResponse(
                status_code=e.status_code,
                content={"error": e.detail}
            )
        except Exception as e:
            logger.error(f"JWT validation error: {str(e)}")
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"error": "Invalid token"}
            )


def setup_security_middleware(app: ASGIApp, config: Optional[SecurityConfig] = None) -> ASGIApp:
    """
    Setup all security middleware for the application
    
    Args:
        app: FastAPI application
        config: Security configuration
    
    Returns:
        Application with security middleware configured
    """
    
    config = config or SecurityConfig()
    
    # Add CORS middleware (should be first)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors_allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-New-Token", "X-RateLimit-Limit"]
    )
    
    # Add Rate Limiting middleware
    if config.enable_rate_limiting:
        app.add_middleware(RateLimitMiddleware)
    
    # Add JWT middleware for protected routes
    app.add_middleware(JWTMiddleware)
    
    # Add main security middleware (should be last to wrap everything)
    app.add_middleware(
        SecurityMiddleware,
        security_config=config
    )
    
    logger.info("Security middleware configured successfully")
    
    return app