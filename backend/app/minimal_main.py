#!/usr/bin/env python3
"""
Minimal FastAPI Application for Development

This is a completely standalone version that can run with just Python standard library.
Use this for testing when dependencies are not available.
"""

import json
import sys
import logging
from datetime import datetime
from typing import Dict, Any
import traceback

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MinimalApp:
    """Minimal web application fallback"""
    
    def __init__(self):
        self.routes = []
        self.available_services = {
            "fastapi": False,
            "database": False,
            "api_router": False,
            "settings": False,
            "exceptions": False
        }
        self.import_errors = {}
        
    def get_status(self) -> Dict[str, Any]:
        return {
            "message": "AI Financial Planning System API (Minimal Mode)",
            "version": "1.0.0",
            "status": "running_minimal",
            "services": self.available_services,
            "timestamp": datetime.utcnow().isoformat(),
            "mode": "standalone"
        }
    
    def get_health(self) -> Dict[str, Any]:
        return {
            "status": "degraded",
            "version": "1.0.0",
            "timestamp": datetime.utcnow().isoformat(),
            "services": {
                service: {"available": available, "status": "healthy" if available else "unavailable"}
                for service, available in self.available_services.items()
            },
            "import_errors": self.import_errors,
            "available_endpoints": [
                {"path": "/", "methods": ["GET"]},
                {"path": "/health", "methods": ["GET"]},
                {"path": "/status", "methods": ["GET"]},
                {"path": "/api/v1/mock/simulation", "methods": ["GET"]}
            ],
            "mode": "minimal"
        }
    
    def get_mock_simulation(self) -> Dict[str, Any]:
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
            "timestamp": datetime.utcnow().isoformat(),
            "mode": "minimal"
        }

def main():
    """Main entry point for minimal application"""
    logger.info("Starting minimal AI Financial Planning System...")
    
    app = MinimalApp()
    
    # Test all import attempts
    try:
        import fastapi
        app.available_services["fastapi"] = True
        logger.info("FastAPI available")
    except ImportError as e:
        app.import_errors["fastapi"] = str(e)
        logger.warning(f"FastAPI not available: {e}")
    
    try:
        from app.core.config import settings
        app.available_services["settings"] = True
        logger.info("Settings available")
    except ImportError as e:
        app.import_errors["settings"] = str(e)
        logger.warning(f"Settings not available: {e}")
    
    try:
        from app.api.v1.api import api_router
        app.available_services["api_router"] = True
        logger.info("API router available")
    except ImportError as e:
        app.import_errors["api_router"] = str(e)
        logger.warning(f"API router not available: {e}")
    
    try:
        from app.database.init_db import init_db
        app.available_services["database"] = True
        logger.info("Database initialization available")
    except ImportError as e:
        app.import_errors["database"] = str(e)
        logger.warning(f"Database initialization not available: {e}")
    
    # Print status
    status = app.get_status()
    print("\n" + "="*60)
    print("AI FINANCIAL PLANNING SYSTEM - MINIMAL MODE")
    print("="*60)
    print(f"Status: {status['status']}")
    print(f"Version: {status['version']}")
    print(f"Timestamp: {status['timestamp']}")
    print("\nService Availability:")
    for service, available in status['services'].items():
        indicator = "✓" if available else "✗"
        print(f"  {indicator} {service}")
    
    if app.import_errors:
        print("\nImport Errors:")
        for service, error in app.import_errors.items():
            print(f"  • {service}: {error}")
    
    print("\nAvailable Mock Endpoints:")
    print("  • GET /health - Health check")
    print("  • GET /status - Service status")
    print("  • GET /api/v1/mock/simulation - Mock simulation data")
    
    print("\nTo start with FastAPI (if available):")
    print("  uvicorn app.main:app --reload")
    print("\nTo view mock data:")
    
    mock_sim = app.get_mock_simulation()
    print("\nMock Simulation Data:")
    print(json.dumps(mock_sim, indent=2))
    
    print("\n" + "="*60)
    
    return app

if __name__ == "__main__":
    app = main()