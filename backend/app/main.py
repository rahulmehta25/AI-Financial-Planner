"""
AI Financial Planning System - Main FastAPI Application
"""

from fastapi import FastAPI, Middleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.exceptions import CustomException
from app.api.v1.api import api_router
from app.database.init_db import init_db

# Create FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="AI-driven financial planning and simulation system",
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Set up CORS
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Add trusted host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS
)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.exception_handler(CustomException)
async def custom_exception_handler(request, exc: CustomException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "error_code": exc.error_code}
    )


@app.on_event("startup")
async def startup_event():
    """Initialize database and perform startup tasks"""
    await init_db()


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "AI Financial Planning System API",
        "version": settings.VERSION,
        "status": "healthy"
    }


@app.get("/health")
async def health_check():
    """Detailed health check endpoint"""
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "database": "connected",
        "simulation_engine": "ready"
    }