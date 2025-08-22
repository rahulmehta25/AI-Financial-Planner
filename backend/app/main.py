"""
AI Financial Planning System - Main FastAPI Application

Robust startup handling with graceful fallbacks for missing dependencies.
"""

import logging
import sys
import traceback
from typing import Dict, Any, Optional
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Track import errors and available services
IMPORT_ERRORS = {}
AVAILABLE_SERVICES = {
    "fastapi": False,
    "database": False,
    "api_router": False,
    "settings": False,
    "exceptions": False,
    "social_router": False
}

# Try importing core dependencies
try:
    from fastapi import FastAPI, HTTPException
    from fastapi.responses import JSONResponse
    AVAILABLE_SERVICES["fastapi"] = True
    logger.info("FastAPI imported successfully")
except ImportError as e:
    IMPORT_ERRORS["fastapi"] = str(e)
    logger.error(f"Failed to import FastAPI: {e}")
    # Create minimal fallback classes
    class HTTPException(Exception):
        def __init__(self, status_code: int, detail: str = None, headers: dict = None):
            super().__init__(detail)
            self.status_code = status_code
            self.detail = detail
            self.headers = headers
    
    class FastAPI:
        def __init__(self, **kwargs):
            self.routes = []
            self.exception_handlers = {}
            self.middleware = []
            self.startup_handlers = []
            logger.warning("Using minimal FastAPI fallback")
        
        def exception_handler(self, exc_class):
            def decorator(func):
                self.exception_handlers[exc_class] = func
                return func
            return decorator
        
        def add_middleware(self, middleware_class, **kwargs):
            self.middleware.append((middleware_class, kwargs))
        
        def include_router(self, router, **kwargs):
            # Mock router inclusion
            pass
        
        def on_event(self, event_type):
            def decorator(func):
                if event_type == "startup":
                    self.startup_handlers.append(func)
                return func
            return decorator
        
        def get(self, path):
            def decorator(func):
                self.routes.append({"path": path, "method": "GET", "func": func})
                return func
            return decorator
        
        def post(self, path):
            def decorator(func):
                self.routes.append({"path": path, "method": "POST", "func": func})
                return func
            return decorator
    
    class JSONResponse:
        def __init__(self, content, status_code=200):
            self.content = content
            self.status_code = status_code

try:
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.middleware.trustedhost import TrustedHostMiddleware
    MIDDLEWARE_AVAILABLE = True
except ImportError as e:
    IMPORT_ERRORS["middleware"] = str(e)
    MIDDLEWARE_AVAILABLE = False
    logger.warning(f"Middleware import failed: {e}")

# Try importing settings with fallback
try:
    from app.core.config import settings
    AVAILABLE_SERVICES["settings"] = True
    logger.info("Settings loaded successfully")
except ImportError as e:
    IMPORT_ERRORS["settings"] = str(e)
    logger.warning(f"Settings import failed, using defaults: {e}")
    
    # Fallback settings class
    class FallbackSettings:
        PROJECT_NAME = "AI Financial Planning System"
        VERSION = "1.0.0"
        API_V1_STR = "/api/v1"
        BACKEND_CORS_ORIGINS = ["http://localhost:3000", "http://localhost:3001", "*"]
        ALLOWED_HOSTS = ["*"]
        DEBUG = True
    
    settings = FallbackSettings()

# Try importing exceptions with fallback
try:
    from app.core.exceptions import CustomException
    AVAILABLE_SERVICES["exceptions"] = True
except ImportError as e:
    IMPORT_ERRORS["exceptions"] = str(e)
    logger.warning(f"Custom exceptions import failed: {e}")
    
    # Fallback exception
    class CustomException(HTTPException):
        def __init__(self, detail: str, status_code: int = 500, error_code: str = None):
            super().__init__(status_code=status_code, detail=detail)
            self.error_code = error_code

# Try importing API router with fallback
api_router = None
try:
    from app.api.v1.api import api_router
    AVAILABLE_SERVICES["api_router"] = True
    logger.info("API router imported successfully")
except ImportError as e:
    IMPORT_ERRORS["api_router"] = str(e)
    logger.warning(f"API router import failed: {e}")

# Try importing database initialization
init_db = None
try:
    from app.database.init_db import init_db
    AVAILABLE_SERVICES["database"] = True
    logger.info("Database initialization imported successfully")
except ImportError as e:
    IMPORT_ERRORS["database"] = str(e)
    logger.warning(f"Database init import failed: {e}")

# Only proceed if FastAPI is available
if not AVAILABLE_SERVICES["fastapi"]:
    logger.critical("FastAPI is not available. Starting in minimal mode...")
    
    # Import and run minimal application
    try:
        from app.minimal_main import main as minimal_main
        minimal_app = minimal_main()
        # Expose the minimal app for WSGI servers
        app = minimal_app
    except Exception as e:
        logger.critical(f"Cannot start even minimal mode: {e}")
        sys.exit(1)
    
    # Stop execution here for minimal mode
    if __name__ == "__main__":
        sys.exit(0)

# Create FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="AI-driven financial planning and simulation system with graceful degradation",
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json" if hasattr(settings, 'API_V1_STR') else "/api/v1/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Set up CORS if middleware is available
if MIDDLEWARE_AVAILABLE and hasattr(settings, 'BACKEND_CORS_ORIGINS'):
    try:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        logger.info("CORS middleware added successfully")
    except Exception as e:
        logger.warning(f"Failed to add CORS middleware: {e}")

# Add trusted host middleware if available
if MIDDLEWARE_AVAILABLE and hasattr(settings, 'ALLOWED_HOSTS'):
    try:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=settings.ALLOWED_HOSTS
        )
        logger.info("TrustedHost middleware added successfully")
    except Exception as e:
        logger.warning(f"Failed to add TrustedHost middleware: {e}")

# Include API router if available
if api_router and AVAILABLE_SERVICES["api_router"]:
    try:
        app.include_router(api_router, prefix=getattr(settings, 'API_V1_STR', '/api/v1'))
        logger.info("API router included successfully")
    except Exception as e:
        logger.error(f"Failed to include API router: {e}")
        # Create fallback routes
        create_fallback_routes()

# Exception handler
@app.exception_handler(CustomException)
async def custom_exception_handler(request, exc: CustomException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "error_code": getattr(exc, 'error_code', None)}
    )

# Global exception handler for unexpected errors
@app.exception_handler(Exception)
async def global_exception_handler(request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error_code": "INTERNAL_ERROR",
            "debug_info": str(exc) if getattr(settings, 'DEBUG', False) else None
        }
    )

def create_fallback_routes():
    """Create fallback routes when main API router is not available"""
    
    @app.get("/api/v1/users/me")
    async def fallback_current_user():
        return JSONResponse(
            status_code=503,
            content={
                "detail": "User service is temporarily unavailable",
                "error_code": "SERVICE_UNAVAILABLE",
                "fallback": True
            }
        )
    
    @app.get("/api/v1/simulations")
    async def fallback_simulations():
        return {
            "simulations": [],
            "message": "Simulation service is not available",
            "fallback": True,
            "mock_data": {
                "sample_simulation": {
                    "id": "mock-simulation-001",
                    "name": "Sample Retirement Plan",
                    "status": "completed",
                    "probability_of_success": 0.85,
                    "projected_value": 1500000
                }
            }
        }
    
    @app.post("/api/v1/simulations")
    async def fallback_create_simulation():
        return JSONResponse(
            status_code=503,
            content={
                "detail": "Simulation creation service is temporarily unavailable",
                "error_code": "SERVICE_UNAVAILABLE",
                "fallback": True
            }
        )

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize database and perform startup tasks with error handling"""
    logger.info("Starting up application...")
    
    startup_results = {
        "database_init": False,
        "errors": [],
        "warnings": []
    }
    
    if init_db and AVAILABLE_SERVICES["database"]:
        try:
            logger.info("Attempting database initialization...")
            await init_db()
            startup_results["database_init"] = True
            logger.info("Database initialization completed successfully")
        except Exception as e:
            error_msg = f"Database initialization failed: {str(e)}"
            logger.error(error_msg)
            startup_results["errors"].append(error_msg)
    else:
        warning_msg = "Database initialization skipped - service not available"
        logger.warning(warning_msg)
        startup_results["warnings"].append(warning_msg)
    
    # Log startup summary
    logger.info(f"Startup completed with results: {startup_results}")

# Add fallback routes if main router failed
if not AVAILABLE_SERVICES["api_router"]:
    create_fallback_routes()

@app.get("/")
async def root():
    """Health check endpoint with service status"""
    return {
        "message": "AI Financial Planning System API",
        "version": getattr(settings, 'VERSION', '1.0.0'),
        "status": "running",
        "services": AVAILABLE_SERVICES,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/health")
async def comprehensive_health_check():
    """Comprehensive health check endpoint"""
    health_status = {
        "status": "healthy" if all(AVAILABLE_SERVICES[key] for key in ["fastapi", "settings"]) else "degraded",
        "version": getattr(settings, 'VERSION', '1.0.0'),
        "timestamp": datetime.utcnow().isoformat(),
        "services": {},
        "import_errors": IMPORT_ERRORS,
        "available_endpoints": []
    }
    
    # Check each service
    for service_name, available in AVAILABLE_SERVICES.items():
        health_status["services"][service_name] = {
            "available": available,
            "status": "healthy" if available else "unavailable"
        }
    
    # Add database health check if available
    if AVAILABLE_SERVICES["database"]:
        try:
            from app.database.init_db import DatabaseInitializer
            initializer = DatabaseInitializer()
            db_health = await initializer.health_check()
            health_status["services"]["database"].update(db_health)
        except Exception as e:
            health_status["services"]["database"]["error"] = str(e)
            health_status["services"]["database"]["status"] = "error"
    
    # List available endpoints
    for route in app.routes:
        if hasattr(route, 'methods') and hasattr(route, 'path'):
            health_status["available_endpoints"].append({
                "path": route.path,
                "methods": list(route.methods)
            })
    
    return health_status

@app.get("/status")
async def service_status():
    """Simple service status endpoint"""
    return {
        "status": "running",
        "services_available": sum(AVAILABLE_SERVICES.values()),
        "total_services": len(AVAILABLE_SERVICES),
        "uptime": "N/A",  # Would need to track actual uptime
        "version": getattr(settings, 'VERSION', '1.0.0')
    }

# Add some mock endpoints for critical functionality
@app.get("/api/v1/mock/simulation")
async def mock_simulation():
    """Mock simulation endpoint for testing"""
    return {
        "id": "mock-sim-001",
        "name": "Mock Retirement Simulation",
        "status": "completed",
        "results": {
            "probability_of_success": 0.87,
            "projected_final_value": 2150000,
            "monthly_contribution_required": 2200,
            "years_to_goal": 30
        },
        "disclaimer": "This is mock data for testing purposes only",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/debug")
async def debug_info():
    """Debug information endpoint (only in development)"""
    if not getattr(settings, 'DEBUG', False):
        raise HTTPException(status_code=404, detail="Not found")
    
    return {
        "python_version": sys.version,
        "available_services": AVAILABLE_SERVICES,
        "import_errors": IMPORT_ERRORS,
        "settings": {
            key: getattr(settings, key, None) 
            for key in ['PROJECT_NAME', 'VERSION', 'API_V1_STR', 'DEBUG']
        },
        "routes_count": len(app.routes)
    }