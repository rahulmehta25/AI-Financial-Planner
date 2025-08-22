"""
Main router for blockchain audit system API endpoints.
"""

from fastapi import APIRouter

from .api.audit_endpoints import router as audit_router
from .api.compliance_endpoints import router as compliance_router
from .api.visualization_endpoints import router as visualization_router

# Create main blockchain router
blockchain_router = APIRouter()

# Include all blockchain-related routers
blockchain_router.include_router(audit_router)
blockchain_router.include_router(compliance_router)
blockchain_router.include_router(visualization_router)

# Add any blockchain-wide middleware or dependencies here if needed