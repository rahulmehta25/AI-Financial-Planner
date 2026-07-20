"""
Authentication Middleware

Middleware for handling authentication, rate limiting, and security headers.
"""

import logging
import time
from typing import Callable, Optional, Dict, Any
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from fastapi import status

from app.core.config import settings
from app.core.security_enhanced import rate_limiter, IPValidator
from app.api.deps import get_current_user_from_token, get_db_session

logger = logging.getLogger(__name__)


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """
    Middleware for handling authentication and security
    """
    
    def __init__(self, app, exclude_paths: Optional[list] = None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or [
            "/docs",
            "/redoc",
            "/openapi.json",
            "/health",
            "/api/v1/auth/register",
            "/api/v1/auth/login",
            "/api/v1/auth/login/email",
            "/api/v1/auth/verify-token",
            "/",
        ]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request through authentication middleware"""
        
        start_time = time.time()
        
        # Add request ID for tracking
        import uuid
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Get client IP and user agent
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent", "unknown")
        
        # Skip authentication for excluded paths
        if self._should_skip_auth(request.url.path):
            response = await call_next(request)
            return self._add_security_headers(response, request_id)
        
        # Rate limiting
        if self._is_rate_limited(client_ip, request.url.path):
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Rate limit exceeded",
                    "message": "Too many requests. Please try again later.",
                    "request_id": request_id
                }
            )
        
        # IP validation
        if self._is_suspicious_ip(client_ip):
            logger.warning(f"Suspicious IP detected: {client_ip}")
            # You could block here or just log
        
        # Process request
        response = await call_next(request)
        
        # Add processing time header
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        
        return self._add_security_headers(response, request_id)
    
    def _should_skip_auth(self, path: str) -> bool:
        """Check if path should skip authentication"""
        return any(path.startswith(excluded) for excluded in self.exclude_paths)
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address from request"""
        # Check for forwarded headers (from proxy/load balancer)
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        # Check for real IP header
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        # Fall back to direct client IP
        return request.client.host if request.client else "unknown"
    
    def _is_rate_limited(self, client_ip: str, path: str) -> bool:
        """Check if request is rate limited"""
        # Different rate limits for different endpoints
        if path.startswith("/api/v1/auth/"):
            # Stricter limits for auth endpoints
            return rate_limiter.is_rate_limited(
                f"auth:{client_ip}", 
                max_attempts=10, 
                window_minutes=15
            )
        else:
            # General API rate limiting
            return rate_limiter.is_rate_limited(
                f"api:{client_ip}",
                max_attempts=settings.RATE_LIMIT_PER_MINUTE,
                window_minutes=1
            )
    
    def _is_suspicious_ip(self, client_ip: str) -> bool:
        """Check if IP appears suspicious"""
        return IPValidator.is_suspicious_ip(client_ip)
    
    def _add_security_headers(self, response: Response, request_id: str) -> Response:
        """Add security headers to response"""
        
        # Request tracking
        response.headers["X-Request-ID"] = request_id
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=(), "
            "payment=(), usb=(), magnetometer=(), gyroscope=(), "
            "accelerometer=(), ambient-light-sensor=(), autoplay=(), "
            "encrypted-media=(), picture-in-picture=()"
        )
        
        # HSTS (HTTP Strict Transport Security)
        if not settings.DEBUG:
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )
        
        # CSP (Content Security Policy) for API
        response.headers["Content-Security-Policy"] = (
            "default-src 'none'; "
            "script-src 'none'; "
            "style-src 'none'; "
            "img-src 'none'; "
            "font-src 'none'; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        )
        
        return response


class SessionValidationMiddleware(BaseHTTPMiddleware):
    """
    Middleware for validating user sessions
    """
    
    def __init__(self, app, exclude_paths: Optional[list] = None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or [
            "/docs",
            "/redoc", 
            "/openapi.json",
            "/health",
            "/api/v1/auth/register",
            "/api/v1/auth/login",
            "/api/v1/auth/login/email",
            "/api/v1/auth/verify-token",
            "/",
        ]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request through session validation middleware"""
        
        # Skip validation for excluded paths
        if self._should_skip_validation(request.url.path):
            return await call_next(request)
        
        # Extract token from Authorization header
        authorization = request.headers.get("authorization")
        if not authorization or not authorization.startswith("Bearer "):
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "error": "Authentication required",
                    "message": "Valid authentication token required"
                },
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        token = authorization.split(" ")[1]
        
        # Validate token and get user
        try:
            async for db in get_db_session():
                user = await get_current_user_from_token(token, db)
                if not user:
                    return JSONResponse(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        content={
                            "error": "Invalid token",
                            "message": "Authentication token is invalid or expired"
                        },
                        headers={"WWW-Authenticate": "Bearer"}
                    )
                
                # Store user in request state for use in endpoints
                request.state.current_user = user
                break
        except Exception as e:
            logger.error(f"Session validation error: {str(e)}")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": "Authentication error",
                    "message": "Failed to validate authentication"
                }
            )
        
        return await call_next(request)
    
    def _should_skip_validation(self, path: str) -> bool:
        """Check if path should skip session validation"""
        return any(path.startswith(excluded) for excluded in self.exclude_paths)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for logging requests and responses
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Log request and response information"""
        
        start_time = time.time()
        
        # Log request
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent", "unknown")
        
        logger.info(
            f"Request: {request.method} {request.url.path} "
            f"from {client_ip} ({user_agent})"
        )
        
        # Process request
        response = await call_next(request)
        
        # Log response
        process_time = time.time() - start_time
        logger.info(
            f"Response: {response.status_code} "
            f"({process_time:.3f}s) for {request.method} {request.url.path}"
        )
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address from request"""
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"


class CORSMiddleware(BaseHTTPMiddleware):
    """
    Custom CORS middleware with security enhancements
    """
    
    def __init__(
        self, 
        app, 
        allowed_origins: list = None,
        allowed_methods: list = None,
        allowed_headers: list = None,
        max_age: int = 86400
    ):
        super().__init__(app)
        self.allowed_origins = allowed_origins or settings.BACKEND_CORS_ORIGINS
        self.allowed_methods = allowed_methods or [
            "GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"
        ]
        self.allowed_headers = allowed_headers or [
            "Authorization", "Content-Type", "X-Requested-With"
        ]
        self.max_age = max_age
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Handle CORS"""
        
        origin = request.headers.get("origin")
        
        # Handle preflight requests
        if request.method == "OPTIONS":
            return self._handle_preflight(origin)
        
        # Process request
        response = await call_next(request)
        
        # Add CORS headers
        if origin and self._is_allowed_origin(origin):
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
        
        return response
    
    def _is_allowed_origin(self, origin: str) -> bool:
        """Check if origin is allowed"""
        return origin in self.allowed_origins
    
    def _handle_preflight(self, origin: str) -> Response:
        """Handle preflight OPTIONS requests"""
        
        headers = {}
        
        if origin and self._is_allowed_origin(origin):
            headers["Access-Control-Allow-Origin"] = origin
            headers["Access-Control-Allow-Methods"] = ", ".join(self.allowed_methods)
            headers["Access-Control-Allow-Headers"] = ", ".join(self.allowed_headers)
            headers["Access-Control-Allow-Credentials"] = "true"
            headers["Access-Control-Max-Age"] = str(self.max_age)
        
        return Response(status_code=204, headers=headers)


def create_middleware_stack():
    """Create and return the middleware stack"""
    
    middleware_stack = [
        # Order is important - they are applied in reverse order
        (RequestLoggingMiddleware, {}),
        (CORSMiddleware, {}),
        (AuthenticationMiddleware, {}),
        (SessionValidationMiddleware, {}),
    ]
    
    return middleware_stack