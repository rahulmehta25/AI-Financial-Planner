"""
Main FastAPI application with production-ready structure
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import redis.asyncio as redis

from app.core.config import settings
from app.core.database import Database
from app.api.v1.router import api_router
from app.services.data_providers.yfinance_provider import YFinanceProvider
from app.services.data_providers.cached_provider import CachedDataProvider

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global instances
db: Database = None
redis_client: redis.Redis = None
data_provider: CachedDataProvider = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown with resource management"""
    global db, redis_client, data_provider
    
    # Startup
    logger.info("Starting Financial Planning API...")
    
    try:
        # Initialize database
        logger.info("Connecting to database...")
        db = Database()
        await db.connect()
        
        # Initialize Redis
        logger.info("Connecting to Redis...")
        redis_client = redis.from_url(
            settings.redis_url,
            decode_responses=False,
            max_connections=settings.redis_max_connections
        )
        await redis_client.ping()
        
        # Initialize data provider with caching
        logger.info("Initializing market data provider...")
        yfinance_provider = YFinanceProvider()
        data_provider = CachedDataProvider(yfinance_provider, redis_client)
        
        # Test health
        if await data_provider.health_check():
            logger.info("Data provider health check passed")
        else:
            logger.warning("Data provider health check failed - will retry on demand")
        
        # Store in app state
        app.state.db = db
        app.state.redis = redis_client
        app.state.data_provider = data_provider
        
        logger.info("Application startup complete")
        
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Financial Planning API...")
    
    try:
        if data_provider:
            await data_provider.close()
        if redis_client:
            await redis_client.close()
        if db:
            await db.disconnect()
        logger.info("Application shutdown complete")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


app = FastAPI(
    title="Financial Planning API",
    description="Production-ready portfolio management and financial planning system",
    version="1.0.0",
    docs_url="/api/docs" if settings.environment != "production" else None,
    redoc_url="/api/redoc" if settings.environment != "production" else None,
    lifespan=lifespan
)

# Security middleware
if settings.environment == "production":
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.allowed_hosts
    )

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Request ID middleware
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Add unique request ID for tracing"""
    import uuid
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response

# Exception handlers
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "status_code": exc.status_code,
            "request_id": getattr(request.state, "request_id", None)
        }
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors"""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": exc.errors(),
            "body": exc.body,
            "request_id": getattr(request.state, "request_id", None)
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "request_id": getattr(request.state, "request_id", None)
        }
    )

# Include API routers
app.include_router(api_router, prefix="/api/v1")

# Health check endpoints
@app.get("/health")
async def health_check():
    """Basic health check"""
    return {"status": "healthy"}

@app.get("/health/detailed")
async def detailed_health_check(request: Request):
    """Detailed health check with component status"""
    health_status = {
        "status": "healthy",
        "components": {}
    }
    
    # Check database
    try:
        if hasattr(request.app.state, "db"):
            await request.app.state.db.execute("SELECT 1")
            health_status["components"]["database"] = "healthy"
    except Exception as e:
        health_status["components"]["database"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    # Check Redis
    try:
        if hasattr(request.app.state, "redis"):
            await request.app.state.redis.ping()
            health_status["components"]["redis"] = "healthy"
    except Exception as e:
        health_status["components"]["redis"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    # Check data provider
    try:
        if hasattr(request.app.state, "data_provider"):
            provider_healthy = await request.app.state.data_provider.health_check()
            health_status["components"]["data_provider"] = "healthy" if provider_healthy else "unhealthy"
    except Exception as e:
        health_status["components"]["data_provider"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    return health_status

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "Financial Planning API",
        "version": "1.0.0",
        "docs": "/api/docs" if settings.environment != "production" else None
    }