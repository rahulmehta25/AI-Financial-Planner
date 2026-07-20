"""
Security Headers Configuration for Production

Implements comprehensive security headers following OWASP recommendations.
"""

from typing import Dict, List, Optional
from enum import Enum


class SecurityLevel(Enum):
    """Security level configurations"""
    STRICT = "strict"
    MODERATE = "moderate"
    DEVELOPMENT = "development"


class SecurityHeadersConfig:
    """Configuration for security headers"""
    
    def __init__(self, security_level: SecurityLevel = SecurityLevel.STRICT):
        self.security_level = security_level
        
    def get_headers(self) -> Dict[str, str]:
        """Get security headers based on security level"""
        headers = {}
        
        # Content Security Policy (CSP)
        headers["Content-Security-Policy"] = self._get_csp_policy()
        
        # HTTP Strict Transport Security (HSTS)
        if self.security_level != SecurityLevel.DEVELOPMENT:
            headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
        
        # X-Frame-Options - Prevent clickjacking
        headers["X-Frame-Options"] = "DENY"
        
        # X-Content-Type-Options - Prevent MIME type sniffing
        headers["X-Content-Type-Options"] = "nosniff"
        
        # X-XSS-Protection - Enable XSS filter (legacy browsers)
        headers["X-XSS-Protection"] = "1; mode=block"
        
        # Referrer-Policy - Control referrer information
        headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Permissions-Policy (formerly Feature-Policy)
        headers["Permissions-Policy"] = self._get_permissions_policy()
        
        # Additional security headers for strict mode
        if self.security_level == SecurityLevel.STRICT:
            headers["X-Permitted-Cross-Domain-Policies"] = "none"
            headers["Cross-Origin-Embedder-Policy"] = "require-corp"
            headers["Cross-Origin-Opener-Policy"] = "same-origin"
            headers["Cross-Origin-Resource-Policy"] = "same-origin"
        
        return headers
    
    def _get_csp_policy(self) -> str:
        """Build Content Security Policy based on security level"""
        if self.security_level == SecurityLevel.DEVELOPMENT:
            # More permissive for development
            return (
                "default-src 'self' http://localhost:* ws://localhost:*; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' http://localhost:*; "
                "style-src 'self' 'unsafe-inline' http://localhost:*; "
                "img-src 'self' data: blob: http://localhost:*; "
                "font-src 'self' data:; "
                "connect-src 'self' http://localhost:* ws://localhost:* wss://localhost:*; "
                "frame-ancestors 'none';"
            )
        elif self.security_level == SecurityLevel.MODERATE:
            # Balanced security for staging
            return (
                "default-src 'self'; "
                "script-src 'self' 'sha256-...' https://cdn.jsdelivr.net; "  # Add specific script hashes
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
                "img-src 'self' data: https:; "
                "font-src 'self' https://fonts.gstatic.com; "
                "connect-src 'self' https://api.financialplanner.com wss://ws.financialplanner.com; "
                "frame-ancestors 'none'; "
                "base-uri 'self'; "
                "form-action 'self';"
            )
        else:  # STRICT
            # Maximum security for production
            return (
                "default-src 'none'; "
                "script-src 'self'; "  # No inline scripts, only from same origin
                "style-src 'self'; "   # No inline styles
                "img-src 'self' data:; "
                "font-src 'self'; "
                "connect-src 'self' https://api.financialplanner.com wss://ws.financialplanner.com; "
                "frame-ancestors 'none'; "
                "base-uri 'self'; "
                "form-action 'self'; "
                "upgrade-insecure-requests; "
                "block-all-mixed-content; "
                "require-trusted-types-for 'script';"
            )
    
    def _get_permissions_policy(self) -> str:
        """Build Permissions Policy"""
        permissions = {
            "accelerometer": "()",
            "ambient-light-sensor": "()",
            "autoplay": "(self)",
            "battery": "()",
            "camera": "()",
            "cross-origin-isolated": "(self)",
            "display-capture": "()",
            "document-domain": "()",
            "encrypted-media": "(self)",
            "execution-while-not-rendered": "()",
            "execution-while-out-of-viewport": "()",
            "fullscreen": "(self)",
            "geolocation": "()",
            "gyroscope": "()",
            "keyboard-map": "()",
            "magnetometer": "()",
            "microphone": "()",
            "midi": "()",
            "navigation-override": "()",
            "payment": "(self)",  # Enable for payment processing
            "picture-in-picture": "()",
            "publickey-credentials-get": "(self)",
            "screen-wake-lock": "()",
            "sync-xhr": "()",
            "usb": "()",
            "web-share": "()",
            "xr-spatial-tracking": "()"
        }
        
        return ", ".join([f"{key}={value}" for key, value in permissions.items()])


class SecurityMiddleware:
    """FastAPI middleware for security headers"""
    
    def __init__(self, app, security_level: SecurityLevel = SecurityLevel.STRICT):
        self.app = app
        self.headers_config = SecurityHeadersConfig(security_level)
        
    async def __call__(self, request, call_next):
        response = await call_next(request)
        
        # Add security headers
        headers = self.headers_config.get_headers()
        for header_name, header_value in headers.items():
            response.headers[header_name] = header_value
        
        # Remove server header
        response.headers.pop("Server", None)
        response.headers.pop("X-Powered-By", None)
        
        return response


# CORS Configuration for production
CORS_CONFIG = {
    "allow_origins": [
        "https://app.financialplanner.com",
        "https://www.financialplanner.com"
    ],
    "allow_credentials": True,
    "allow_methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    "allow_headers": [
        "Authorization",
        "Content-Type",
        "X-Requested-With",
        "X-CSRF-Token"
    ],
    "expose_headers": ["X-Total-Count", "X-Page", "X-Per-Page"],
    "max_age": 86400  # 24 hours
}


# Security headers for nginx configuration
NGINX_SECURITY_HEADERS = """
# Security Headers
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
add_header X-Frame-Options "DENY" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
add_header Content-Security-Policy "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; font-src 'self'; connect-src 'self' https://api.financialplanner.com wss://ws.financialplanner.com; frame-ancestors 'none'; base-uri 'self'; form-action 'self';" always;
add_header Permissions-Policy "geolocation=(), camera=(), microphone=(), payment=(self)" always;

# Remove server version
server_tokens off;
more_clear_headers Server;
more_clear_headers X-Powered-By;

# SSL Configuration
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384;
ssl_prefer_server_ciphers off;
ssl_session_timeout 1d;
ssl_session_cache shared:SSL:10m;
ssl_session_tickets off;
ssl_stapling on;
ssl_stapling_verify on;

# OCSP Stapling
ssl_trusted_certificate /etc/nginx/ssl/chain.pem;
resolver 8.8.8.8 8.8.4.4 valid=300s;
resolver_timeout 5s;
"""