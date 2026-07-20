"""
Integration module for API Versioning System with FastAPI application
"""

import logging
from typing import Optional
from fastapi import FastAPI, Request
from fastapi.middleware.base import BaseHTTPMiddleware

from .config import initialize_versioning_system, VersioningSystem
from .middleware import VersioningMiddleware, VersionValidationMiddleware
from .endpoints import router as versioning_router

logger = logging.getLogger(__name__)


def setup_api_versioning(
    app: FastAPI,
    config_path: Optional[str] = None,
    include_management_endpoints: bool = True
) -> VersioningSystem:
    """
    Setup comprehensive API versioning for FastAPI application
    
    Args:
        app: FastAPI application instance
        config_path: Optional path to versioning configuration file
        include_management_endpoints: Whether to include versioning management endpoints
    
    Returns:
        Configured VersioningSystem instance
    """
    
    # Initialize versioning system
    versioning_system = initialize_versioning_system(config_path)
    
    if not versioning_system.config.enabled:
        logger.info("API versioning is disabled")
        return versioning_system
    
    # Add version validation middleware (first)
    app.add_middleware(
        VersionValidationMiddleware,
        version_manager=versioning_system.version_manager
    )
    
    # Add main versioning middleware
    app.add_middleware(
        VersioningMiddleware,
        version_manager=versioning_system.version_manager
    )
    
    # Include management endpoints if requested
    if include_management_endpoints:
        app.include_router(versioning_router, prefix="/api/admin")
        logger.info("Added versioning management endpoints at /api/admin/versioning")
    
    # Store versioning system in app state for access in endpoints
    app.state.versioning_system = versioning_system
    
    logger.info("API versioning system setup completed")
    return versioning_system


def get_versioning_system_from_app(app: FastAPI) -> Optional[VersioningSystem]:
    """Get versioning system from FastAPI app state"""
    return getattr(app.state, 'versioning_system', None)


# Example integration with existing v1 and v2 routers
def integrate_versioned_routers(
    app: FastAPI, 
    versioning_system: VersioningSystem,
    v1_router,
    v2_router=None
):
    """
    Integrate existing v1 and v2 routers with versioning system
    
    Args:
        app: FastAPI application
        versioning_system: Configured versioning system
        v1_router: v1 API router
        v2_router: Optional v2 API router
    """
    
    # Include v1 router
    app.include_router(
        v1_router,
        prefix="/api/v1",
        tags=["v1"]
    )
    
    # Include v2 router if available
    if v2_router:
        app.include_router(
            v2_router,
            prefix="/api/v2", 
            tags=["v2"]
        )
    
    logger.info("Integrated versioned routers with application")


# Middleware for automatic version-based routing
class VersionRoutingMiddleware(BaseHTTPMiddleware):
    """Middleware to automatically route requests to correct version"""
    
    def __init__(self, app, versioning_system: VersioningSystem):
        super().__init__(app)
        self.versioning_system = versioning_system
    
    async def dispatch(self, request: Request, call_next):
        """Route request based on negotiated version"""
        
        # Get negotiated version from request state (set by VersioningMiddleware)
        api_version = getattr(request.state, 'api_version', None)
        
        if api_version:
            # Modify path to include correct version
            original_path = request.url.path
            
            # Only modify if path doesn't already include version
            if not original_path.startswith('/api/v'):
                version_major = api_version.split('.')[0]
                new_path = f"/api/v{version_major}{original_path}"
                
                # Update request URL
                request._url = request.url.replace(path=new_path)
        
        response = await call_next(request)
        return response


# Health check endpoints with versioning information
def add_versioning_health_checks(app: FastAPI, versioning_system: VersioningSystem):
    """Add health check endpoints that include versioning information"""
    
    @app.get("/health/versioning")
    async def versioning_health():
        """Health check specifically for versioning system"""
        health = versioning_system.validate_system_health()
        
        # Set appropriate status code based on health
        status_code = 200
        if health['overall_status'] == 'issues':
            status_code = 503
        elif health['warnings']:
            status_code = 200  # Warnings are OK, but noted
        
        return health
    
    @app.get("/versions")
    async def list_supported_versions():
        """Public endpoint to list supported API versions"""
        versions = versioning_system.version_manager.get_supported_versions()
        
        return {
            'supported_versions': [
                {
                    'version': v.version,
                    'status': v.status.value,
                    'description': v.description,
                    'is_deprecated': v.is_deprecated,
                    'deprecation_date': v.deprecation_date.isoformat() if v.deprecation_date else None,
                    'retirement_date': v.retirement_date.isoformat() if v.retirement_date else None
                }
                for v in versions
            ],
            'latest_version': versioning_system.version_manager.get_latest_version().version
            if versioning_system.version_manager.get_latest_version() else None
        }


# Example usage and configuration
def create_sample_versioning_config():
    """Create a sample versioning configuration file"""
    
    import json
    from pathlib import Path
    
    config = {
        "enabled": True,
        "default_version": "1.0.0",
        "deprecation_policy": {
            "min_deprecation_period_days": 180,
            "stable_support_period_days": 365,
            "beta_support_period_days": 90,
            "advance_notice_days": 60,
            "retirement_warning_thresholds": [90, 30, 7]
        },
        "documentation_enabled": True,
        "sdk_management_enabled": True,
        "ab_testing_enabled": True,
        "gateway_config_enabled": True,
        "config_dir": "config/versioning",
        "docs_output_dir": "docs/api",
        "sdk_output_dir": "docs/sdk",
        "ab_test_reports_dir": "reports/ab_tests",
        "auto_generate_docs": True,
        "auto_export_gateway_configs": False,
        "auto_advance_rollouts": True,
        "metrics_enabled": True,
        "metrics_retention_days": 90
    }
    
    # Ensure config directory exists
    config_dir = Path("config/versioning")
    config_dir.mkdir(parents=True, exist_ok=True)
    
    # Write config file
    config_file = config_dir / "versioning_config.json"
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    
    logger.info(f"Created sample versioning config at {config_file}")
    return str(config_file)


# Utility functions for version-aware endpoint creation
def version_aware_endpoint(versions: list, deprecated_in: str = None):
    """Decorator to mark endpoints as version-aware"""
    
    def decorator(func):
        func._api_versions = versions
        func._deprecated_in = deprecated_in
        return func
    
    return decorator


def create_versioned_fastapi_app(
    title: str = "Financial Planning API",
    version: str = "1.0.0",
    config_path: Optional[str] = None
) -> tuple[FastAPI, VersioningSystem]:
    """
    Create a FastAPI app with full versioning support
    
    Returns:
        Tuple of (FastAPI app, VersioningSystem)
    """
    
    # Create FastAPI app
    app = FastAPI(
        title=title,
        version=version,
        description="AI-driven financial planning API with comprehensive versioning support"
    )
    
    # Setup versioning
    versioning_system = setup_api_versioning(
        app=app,
        config_path=config_path,
        include_management_endpoints=True
    )
    
    # Add health checks
    add_versioning_health_checks(app, versioning_system)
    
    # Add startup event to generate initial documentation
    @app.on_event("startup")
    async def startup_event():
        """Generate documentation and configs on startup"""
        if versioning_system.config.auto_generate_docs:
            try:
                versioning_system.generate_all_documentation()
                logger.info("Generated API documentation on startup")
            except Exception as e:
                logger.error(f"Failed to generate documentation on startup: {e}")
        
        if versioning_system.config.auto_export_gateway_configs:
            try:
                versioning_system.export_all_gateway_configs()
                logger.info("Exported gateway configurations on startup")
            except Exception as e:
                logger.error(f"Failed to export gateway configs on startup: {e}")
    
    return app, versioning_system


# Example of how to integrate with existing financial planning app
def integrate_with_existing_app(existing_app: FastAPI) -> VersioningSystem:
    """
    Example integration with the existing financial planning FastAPI app
    """
    
    # Setup versioning system
    versioning_system = setup_api_versioning(
        app=existing_app,
        config_path="config/versioning/versioning_config.json",
        include_management_endpoints=True
    )
    
    # Add health checks
    add_versioning_health_checks(existing_app, versioning_system)
    
    # Modify existing routes to be version-aware
    # This would typically involve updating your existing route definitions
    
    logger.info("Integrated versioning system with existing financial planning app")
    return versioning_system


# CLI commands for versioning management
def create_cli_commands():
    """Create CLI commands for versioning management"""
    
    import click
    
    @click.group()
    def versioning():
        """API Versioning management commands"""
        pass
    
    @versioning.command()
    @click.option('--config', default=None, help='Configuration file path')
    def init(config):
        """Initialize versioning system"""
        versioning_system = initialize_versioning_system(config)
        click.echo(f"Versioning system initialized with {len(versioning_system.version_manager.get_all_versions())} versions")
    
    @versioning.command()
    @click.argument('version')
    @click.argument('description')
    def create_version(version, description):
        """Create a new API version"""
        versioning_system = initialize_versioning_system()
        
        from .models import APIVersion, VersionStatus
        from datetime import datetime
        
        new_version = APIVersion(
            version=version,
            status=VersionStatus.DEVELOPMENT,
            release_date=datetime.utcnow(),
            description=description
        )
        
        success = versioning_system.version_manager.add_version(new_version)
        if success:
            click.echo(f"Created version {version}")
        else:
            click.echo(f"Failed to create version {version}")
    
    @versioning.command()
    @click.argument('version')
    def deprecate(version):
        """Deprecate an API version"""
        versioning_system = initialize_versioning_system()
        success = versioning_system.version_manager.deprecate_version(version)
        
        if success:
            click.echo(f"Deprecated version {version}")
        else:
            click.echo(f"Failed to deprecate version {version}")
    
    @versioning.command()
    def generate_docs():
        """Generate documentation for all versions"""
        versioning_system = initialize_versioning_system()
        files = versioning_system.generate_all_documentation()
        
        click.echo("Generated documentation:")
        for version, file_list in files.items():
            click.echo(f"  {version}: {len(file_list)} files")
    
    @versioning.command()
    def health_check():
        """Check versioning system health"""
        versioning_system = initialize_versioning_system()
        health = versioning_system.validate_system_health()
        
        click.echo(f"Overall status: {health['overall_status']}")
        
        if health['issues']:
            click.echo("Issues:")
            for issue in health['issues']:
                click.echo(f"  - {issue}")
        
        if health['warnings']:
            click.echo("Warnings:")
            for warning in health['warnings']:
                click.echo(f"  - {warning}")
    
    return versioning