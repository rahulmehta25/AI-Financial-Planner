"""
API Versioning System for Financial Planning Backend

This package provides comprehensive API versioning capabilities including:
- URL path versioning (/api/v1, /api/v2)
- Header-based version negotiation
- Deprecation policy management
- Backward compatibility enforcement
- Version-specific routing and middleware
- A/B testing and gradual migration support
- Client SDK management with compatibility matrices
- Automatic documentation generation
- Gateway configuration generation
"""

from .models import (
    APIVersion,
    VersionStatus,
    DeprecationPolicy,
    VersionCompatibility,
    ClientSDKInfo,
    ABTestConfig
)

from .manager import VersionManager
from .middleware import VersioningMiddleware, VersionValidationMiddleware
from .router import VersionedAPIRouter
from .negotiation import VersionNegotiator
from .compatibility import CompatibilityAnalyzer
from .documentation import DocumentationGenerator
from .sdk_manager import SDKManager
from .ab_testing import ABTestManager
from .gateway import GatewayConfigGenerator
from .config import VersioningSystem, VersioningConfig, get_versioning_system
from .integration import setup_api_versioning, create_versioned_fastapi_app

__version__ = "1.0.0"

__all__ = [
    # Core models
    "APIVersion",
    "VersionStatus", 
    "DeprecationPolicy",
    "VersionCompatibility",
    "ClientSDKInfo",
    "ABTestConfig",
    
    # Core components
    "VersionManager",
    "VersioningMiddleware",
    "VersionValidationMiddleware",
    "VersionedAPIRouter",
    "VersionNegotiator",
    
    # Analysis and management
    "CompatibilityAnalyzer",
    "DocumentationGenerator",
    "SDKManager",
    "ABTestManager",
    "GatewayConfigGenerator",
    
    # Configuration and system
    "VersioningSystem",
    "VersioningConfig",
    "get_versioning_system",
    
    # Integration helpers
    "setup_api_versioning",
    "create_versioned_fastapi_app"
]