"""
AI Financial Planning System - Main FastAPI Application

Robust startup handling with graceful fallbacks for missing dependencies.
"""

import asyncio
import logging
import os
import platform
import sys
import traceback
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from contextlib import asynccontextmanager
import uvicorn
import logging
from typing import Dict, Any

from app.core.config import settings
from app.services.financial_modeling.monte_carlo_engine import AdvancedMonteCarloEngine
from app.services.market_data.data_aggregator import MarketDataAggregator
from app.services.optimization.portfolio_optimizer import IntelligentPortfolioOptimizer
from app.services.ai.financial_advisor_ai import PersonalizedFinancialAdvisor

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Track import errors and available services
IMPORT_ERRORS = {}
AVAILABLE_SERVICES = {
    "fastapi": False,
    "database": False,
    "api_router": False,
    "settings": False,
    "exceptions": False,
    "social_router": False,
    "middleware": False,
    "pydantic": False,
    "sqlalchemy": False
}

# Application metadata
APP_METADATA = {
    "name": "AI Financial Planning System",
    "version": "1.0.0",
    "description": "AI-driven financial planning and simulation system",
    "startup_time": datetime.utcnow(),
    "python_version": sys.version,
    "platform": platform.platform()
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
    
    class MockRoute:
        def __init__(self, path, methods=None):
            self.path = path
            self.methods = methods or ["GET"]
    
    class FastAPI:
        def __init__(self, **kwargs):
            self.routes = []
            self.exception_handlers = {}
            self.middleware = []
            self.startup_handlers = []
            self.title = kwargs.get('title', 'FastAPI App')
            self.description = kwargs.get('description', '')
            self.version = kwargs.get('version', '1.0.0')
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
                route = MockRoute(path, ["GET"])
                self.routes.append(route)
                return func
            return decorator
        
        def post(self, path):
            def decorator(func):
                route = MockRoute(path, ["POST"])
                self.routes.append(route)
                return func
            return decorator
    
    class JSONResponse:
        def __init__(self, content, status_code=200):
            self.content = content
            self.status_code = status_code

# Try importing middleware
try:
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.middleware.trustedhost import TrustedHostMiddleware
    AVAILABLE_SERVICES["middleware"] = True
    logger.info("Middleware imported successfully")
except ImportError as e:
    IMPORT_ERRORS["middleware"] = str(e)
    logger.warning(f"Middleware import failed: {e}")
    
    # Create fallback middleware classes
    class CORSMiddleware:
        def __init__(self, app, **kwargs):
            pass
    
    class TrustedHostMiddleware:
        def __init__(self, app, **kwargs):
            pass

# Try importing settings with fallback
try:
    from app.core.config import settings
    AVAILABLE_SERVICES["settings"] = True
    logger.info("Settings loaded successfully")
except ImportError as e:
    IMPORT_ERRORS["settings"] = str(e)
    logger.warning(f"Settings import failed, using defaults: {e}")
    
    # Fallback settings class with environment variable support
    class FallbackSettings:
        PROJECT_NAME = os.getenv("PROJECT_NAME", "AI Financial Planning System")
        VERSION = os.getenv("VERSION", "1.0.0")
        API_V1_STR = os.getenv("API_V1_STR", "/api/v1")
        BACKEND_CORS_ORIGINS = [
            "http://localhost:3000", 
            "http://localhost:3001", 
            "http://127.0.0.1:3000",
            "http://127.0.0.1:3001",
            "http://localhost:5173",  # Vite dev server
            "http://127.0.0.1:5173",
            "http://localhost:4173",  # Vite preview
            "http://127.0.0.1:4173",
            "https://ai-financial-planner-zeta.vercel.app",  # Production frontend
            "https://ai-financial-planner-*.vercel.app",  # Preview deployments
            "*"
        ]
        ALLOWED_HOSTS = ["*"]
        DEBUG = os.getenv("DEBUG", "true").lower() == "true"
        HOST = os.getenv("HOST", "0.0.0.0")
        PORT = int(os.getenv("PORT", "8000"))
        ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
    
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

# Try importing API router with detailed fallback
api_router = None
try:
    from app.api.v1.api import api_router
    from app.routes.demo_metrics import router as demo_metrics_router
    AVAILABLE_SERVICES["api_router"] = True
    logger.info("API router imported successfully")
except ImportError as e:
    IMPORT_ERRORS["api_router"] = str(e)
    logger.warning(f"API router import failed: {e}")
    
    # Try importing individual components
    try:
        from fastapi import APIRouter
        api_router = APIRouter()
        logger.info("Created fallback API router")
    except ImportError:
        logger.error("Cannot create even basic API router - FastAPI not available")

# Try importing database initialization
init_db = None
DatabaseInitializer = None
try:
    from app.database.init_db import init_db, DatabaseInitializer
    AVAILABLE_SERVICES["database"] = True
    logger.info("Database initialization imported successfully")
except ImportError as e:
    IMPORT_ERRORS["database"] = str(e)
    logger.warning(f"Database init import failed: {e}")
    
    # Create mock database functions
    async def init_db():
        logger.warning("Mock database initialization - no actual database setup")
        return {"status": "mock", "message": "Database not available"}
    
    class DatabaseInitializer:
        async def health_check(self):
            return {"status": "unavailable", "message": "Database service not available"}

# Try importing additional dependencies
try:
    import pydantic
    AVAILABLE_SERVICES["pydantic"] = True
except ImportError as e:
    IMPORT_ERRORS["pydantic"] = str(e)
    logger.warning(f"Pydantic not available: {e}")

try:
    import sqlalchemy
    AVAILABLE_SERVICES["sqlalchemy"] = True
except ImportError as e:
    IMPORT_ERRORS["sqlalchemy"] = str(e)
    logger.warning(f"SQLAlchemy not available: {e}")

# Check for critical FastAPI availability
if not AVAILABLE_SERVICES["fastapi"]:
    logger.critical("FastAPI is not available. Cannot start application.")
    logger.critical("Please install FastAPI: pip install fastapi")
    
    # Create a minimal WSGI-compatible application
    def app(environ, start_response):
        status = '503 Service Unavailable'
        headers = [('Content-type', 'application/json')]
        start_response(status, headers)
        return [b'{"error": "FastAPI not available", "status": "service_unavailable"}']
    
    if __name__ == "__main__":
        print("Error: FastAPI is not installed. Cannot start server.")
        sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Security
security = HTTPBearer()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    # Startup
    logger.info("Starting AI Financial Planner API...")
    
    # Initialize services
    app.state.market_data = MarketDataAggregator()
    app.state.monte_carlo = AdvancedMonteCarloEngine(app.state.market_data)
    app.state.portfolio_optimizer = IntelligentPortfolioOptimizer()
    app.state.ai_advisor = PersonalizedFinancialAdvisor()
    
    logger.info("All services initialized successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down AI Financial Planner API...")

# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="AI-driven financial planning and simulation system with graceful degradation",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT
    }

# Market data endpoints
@app.get("/api/v1/market-data/historical")
async def get_historical_data(
    symbols: str,
    start_date: str,
    end_date: str,
    interval: str = "1d"
):
    """Get historical market data"""
    try:
        from datetime import datetime
        start = datetime.fromisoformat(start_date)
        end = datetime.fromisoformat(end_date)
        symbol_list = symbols.split(",")
        
        data = await app.state.market_data.get_historical_data(
            symbol_list, start, end, interval
        )
        
        return {"data": data.to_dict() if hasattr(data, 'to_dict') else str(data)}
    except Exception as e:
        logger.error(f"Error fetching historical data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch historical data: {str(e)}"
        )

@app.get("/api/v1/market-data/fundamental/{symbol}")
async def get_fundamental_data(symbol: str):
    """Get fundamental data for a symbol"""
    try:
        data = await app.state.market_data.get_fundamental_data([symbol])
        return {"data": data}
    except Exception as e:
        logger.error(f"Error fetching fundamental data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch fundamental data: {str(e)}"
        )

# Monte Carlo simulation endpoints
@app.post("/api/v1/simulations/monte-carlo")
async def run_monte_carlo_simulation(
    request: Dict[str, Any]
):
    """Run Monte Carlo simulation"""
    try:
        from app.services.financial_modeling.monte_carlo_engine import SimulationParams
        
        # Extract parameters from request
        params = SimulationParams(
            num_simulations=request.get("num_simulations", 10000),
            time_horizon=request.get("time_horizon", 30),
            batch_size=request.get("batch_size", 1000),
            confidence_level=request.get("confidence_level", 0.95)
        )
        
        # Create mock portfolio for simulation
        class MockPortfolio:
            def __init__(self):
                self.total_value = request.get("portfolio_value", 100000)
                self.holdings = []
                self.goals = []
        
        portfolio = MockPortfolio()
        
        # Run simulation
        results = await app.state.monte_carlo.simulate_portfolio(portfolio, params)
        
        return {
            "simulation_id": str(results.params),
            "results": {
                "statistics": results.analysis["statistics"],
                "risk_metrics": results.analysis["risk_metrics"],
                "confidence_intervals": results.analysis["confidence_intervals"],
                "computation_time": results.computation_time
            },
            "regime": results.regime
        }
        
    except Exception as e:
        logger.error(f"Error running Monte Carlo simulation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to run simulation: {str(e)}"
        )

# Portfolio optimization endpoints
@app.post("/api/v1/portfolio/optimize")
async def optimize_portfolio(
    request: Dict[str, Any]
):
    """Optimize portfolio"""
    try:
        from app.services.optimization.portfolio_optimizer import OptimizationConstraints
        
        # Create mock user profile
        class MockUserProfile:
            def __init__(self):
                self.risk_tolerance = request.get("risk_tolerance", 0.5)
                self.tax_bracket = request.get("tax_bracket", 0.22)
        
        user_profile = MockUserProfile()
        
        # Create mock current holdings
        current_holdings = request.get("current_holdings", [])
        
        # Create mock market data
        class MockMarketData:
            pass
        
        market_data = MockMarketData()
        
        # Create constraints
        constraints = OptimizationConstraints(
            max_position_size=request.get("max_position_size", 0.25),
            min_position_size=request.get("min_position_size", 0.01)
        )
        
        # Run optimization
        result = await app.state.portfolio_optimizer.optimize_portfolio(
            user_profile, current_holdings, market_data, constraints
        )
        
        return {
            "optimal_weights": result.optimal_weights,
            "expected_return": result.expected_return,
            "expected_risk": result.expected_risk,
            "sharpe_ratio": result.sharpe_ratio,
            "implementation_plan": result.implementation_plan,
            "confidence_scores": result.confidence_scores
        }
        
    except Exception as e:
        logger.error(f"Error optimizing portfolio: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to optimize portfolio: {str(e)}"
        )

# AI advice endpoints
@app.post("/api/v1/ai/advice")
async def get_ai_advice(
    request: Dict[str, Any]
):
    """Get AI-generated financial advice"""
    try:
        from app.services.ai.financial_advisor_ai import UserContext, MarketContext
        
        # Create user context
        user_context = UserContext(
            user_id=request.get("user_id", "demo_user"),
            profile=request.get("profile", {}),
            portfolio_analysis=request.get("portfolio_analysis", {}),
            goal_progress=request.get("goal_progress", [])
        )
        
        # Create market context
        market_context = MarketContext(
            current_market_conditions=request.get("market_conditions", "normal"),
            volatility_regime=request.get("volatility_regime", "medium"),
            economic_outlook=request.get("economic_outlook", "stable")
        )
        
        # Get user query
        user_query = request.get("query", "How should I allocate my portfolio?")
        
        # Generate advice
        advice = await app.state.ai_advisor.generate_personalized_advice(
            user_query, user_context, market_context
        )
        
        return {
            "advice": advice.narrative,
            "key_points": advice.key_points,
            "action_plan": {
                "items": [
                    {
                        "title": item.title,
                        "description": item.description,
                        "priority": item.priority,
                        "impact": item.impact,
                        "timeline": item.timeline
                    }
                    for item in advice.action_plan.items
                ],
                "total_estimated_impact": advice.action_plan.total_estimated_impact,
                "implementation_timeline": advice.action_plan.implementation_timeline
            },
            "confidence_score": advice.confidence_score,
            "disclaimers": advice.disclaimers
        }
        
    except Exception as e:
        logger.error(f"Error generating AI advice: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate advice: {str(e)}"
        )

# Portfolio analysis endpoints
@app.get("/api/v1/portfolio/{portfolio_id}/analysis")
async def get_portfolio_analysis(portfolio_id: str):
    """Get comprehensive portfolio analysis"""
    try:
        # Mock portfolio analysis
        analysis = {
            "portfolio_id": portfolio_id,
            "total_value": 150000,
            "allocation": {
                "equity": 0.60,
                "bonds": 0.25,
                "cash": 0.10,
                "alternatives": 0.05
            },
            "risk_metrics": {
                "volatility": 0.15,
                "sharpe_ratio": 0.85,
                "max_drawdown": 0.12,
                "var_95": 0.08
            },
            "performance": {
                "ytd": 0.08,
                "1_year": 0.12,
                "3_year": 0.09,
                "5_year": 0.11
            },
            "rebalancing_needed": True,
            "tax_efficiency_score": 0.75
        }
        
        return analysis
        
    except Exception as e:
        logger.error(f"Error analyzing portfolio: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze portfolio: {str(e)}"
        )

# Risk management endpoints
@app.post("/api/v1/risk/analysis")
async def analyze_portfolio_risk(
    request: Dict[str, Any]
):
    """Analyze portfolio risk"""
    try:
        # Mock risk analysis
        risk_analysis = {
            "overall_risk_score": 0.65,
            "risk_level": "moderate",
            "risk_decomposition": {
                "market_risk": 0.45,
                "credit_risk": 0.15,
                "liquidity_risk": 0.05
            },
            "stress_test_results": {
                "2008_crisis_scenario": -0.25,
                "covid_crash_scenario": -0.20,
                "inflation_spike_scenario": -0.15
            },
            "recommendations": [
                "Consider increasing bond allocation for stability",
                "Review international exposure for diversification",
                "Implement stop-loss orders for high-risk positions"
            ]
        }
        
        return risk_analysis
        
    except Exception as e:
        logger.error(f"Error analyzing risk: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze risk: {str(e)}"
        )

# Tax optimization endpoints
@app.post("/api/v1/tax/optimization")
async def optimize_tax_strategy(
    request: Dict[str, Any]
):
    """Optimize tax strategy"""
    try:
        # Mock tax optimization
        tax_optimization = {
            "estimated_tax_savings": 2500,
            "recommended_actions": [
                "Harvest tax losses on underperforming positions",
                "Increase 401(k) contributions to reduce taxable income",
                "Consider Roth conversion for tax-free growth"
            ],
            "account_allocation": {
                "taxable": ["growth_stocks", "index_funds"],
                "401k": ["bonds", "reits"],
                "roth_ira": ["high_growth_stocks", "international"]
            },
            "implementation_timeline": "3-6 months"
        }
        
        return tax_optimization
        
    except Exception as e:
        logger.error(f"Error optimizing tax strategy: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to optimize tax strategy: {str(e)}"
        )

# Goal planning endpoints
@app.post("/api/v1/goals/plan")
async def create_goal_plan(
    request: Dict[str, Any]
):
    """Create financial goal plan"""
    try:
        # Mock goal planning
        goal_plan = {
            "goal_id": "goal_123",
            "target_amount": request.get("target_amount", 1000000),
            "target_date": request.get("target_date", "2035-01-01"),
            "monthly_contribution": 2500,
            "expected_return": 0.08,
            "probability_of_success": 0.85,
            "milestones": [
                {"year": 2025, "target": 200000, "milestone": "25% of goal"},
                {"year": 2030, "target": 600000, "milestone": "60% of goal"},
                {"year": 2035, "target": 1000000, "milestone": "Goal achieved"}
            ],
            "recommendations": [
                "Increase monthly contributions by $500",
                "Consider higher-risk allocation for longer time horizon",
                "Review progress quarterly and adjust as needed"
            ]
        }
        
        return goal_plan
        
    except Exception as e:
        logger.error(f"Error creating goal plan: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create goal plan: {str(e)}"
        )

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

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize database and perform startup tasks with comprehensive error handling"""
    logger.info("=== Starting AI Financial Planning System ===")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Platform: {platform.platform()}")
    logger.info(f"Environment: {getattr(settings, 'ENVIRONMENT', 'unknown')}")
    
    startup_results = {
        "database_init": False,
        "services_loaded": list(k for k, v in AVAILABLE_SERVICES.items() if v),
        "services_failed": list(k for k, v in AVAILABLE_SERVICES.items() if not v),
        "errors": [],
        "warnings": [],
        "startup_time": datetime.utcnow()
    }
    
    # Database initialization
    if init_db and AVAILABLE_SERVICES["database"]:
        try:
            logger.info("Attempting database initialization...")
            db_result = await init_db()
            startup_results["database_init"] = True
            startup_results["database_result"] = db_result
            logger.info("Database initialization completed successfully")
        except Exception as e:
            error_msg = f"Database initialization failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            startup_results["errors"].append(error_msg)
    else:
        warning_msg = "Database initialization skipped - service not available"
        logger.warning(warning_msg)
        startup_results["warnings"].append(warning_msg)
    
    # Check critical services
    critical_services = ["fastapi", "settings"]
    missing_critical = [s for s in critical_services if not AVAILABLE_SERVICES[s]]
    if missing_critical:
        error_msg = f"Critical services missing: {missing_critical}"
        logger.error(error_msg)
        startup_results["errors"].append(error_msg)
    
    # Log startup summary
    logger.info("=== Startup Summary ===")
    logger.info(f"Services loaded: {startup_results['services_loaded']}")
    logger.info(f"Services failed: {startup_results['services_failed']}")
    logger.info(f"Errors: {len(startup_results['errors'])}")
    logger.info(f"Warnings: {len(startup_results['warnings'])}")
    logger.info("=== Application Ready ===")
    
    # Store startup results globally for health checks
    APP_METADATA["startup_results"] = startup_results

@app.get("/")
async def root():
    """Root endpoint with system information"""
    return {
        "message": "AI Financial Planning System API",
        "version": getattr(settings, 'VERSION', '1.0.0'),
        "status": "running",
        "description": "AI-driven financial planning and simulation system with graceful degradation",
        "services": AVAILABLE_SERVICES,
        "environment": getattr(settings, 'ENVIRONMENT', 'unknown'),
        "docs_url": "/docs",
        "health_url": "/health",
        "api_prefix": getattr(settings, 'API_V1_STR', '/api/v1'),
        "timestamp": datetime.utcnow().isoformat(),
        "uptime_seconds": (datetime.utcnow() - APP_METADATA['startup_time']).total_seconds()
    }

@app.get("/health")
async def comprehensive_health_check():
    """Comprehensive health check endpoint with detailed system information"""
    uptime = (datetime.utcnow() - APP_METADATA['startup_time']).total_seconds()
    critical_services = ["fastapi", "settings"]
    critical_healthy = all(AVAILABLE_SERVICES[key] for key in critical_services)
    
    health_status = {
        "status": "healthy" if critical_healthy else "degraded",
        "overall_health": "PASS" if critical_healthy else "DEGRADED",
        "version": getattr(settings, 'VERSION', '1.0.0'),
        "timestamp": datetime.utcnow().isoformat(),
        "uptime_seconds": uptime,
        "uptime_human": f"{int(uptime // 3600)}h {int((uptime % 3600) // 60)}m {int(uptime % 60)}s",
        "environment": getattr(settings, 'ENVIRONMENT', 'unknown'),
        "services": {},
        "system_info": {
            "python_version": sys.version,
            "platform": platform.platform(),
            "architecture": platform.architecture(),
            "processor": platform.processor(),
            "hostname": platform.node()
        },
        "import_errors": IMPORT_ERRORS,
        "available_endpoints": [],
        "startup_results": APP_METADATA.get("startup_results", {})
    }
    
    # Check each service with detailed information
    for service_name, available in AVAILABLE_SERVICES.items():
        service_info = {
            "available": available,
            "status": "healthy" if available else "unavailable",
            "critical": service_name in critical_services
        }
        
        if not available and service_name in IMPORT_ERRORS:
            service_info["error"] = IMPORT_ERRORS[service_name]
        
        health_status["services"][service_name] = service_info
    
    # Add database health check if available
    if AVAILABLE_SERVICES["database"] and DatabaseInitializer:
        try:
            initializer = DatabaseInitializer()
            db_health = await initializer.health_check()
            health_status["services"]["database"].update(db_health)
            health_status["database_detailed"] = db_health
        except Exception as e:
            health_status["services"]["database"]["error"] = str(e)
            health_status["services"]["database"]["status"] = "error"
            logger.error(f"Database health check failed: {e}")
    
    # List available endpoints with better organization
    endpoints_by_prefix = {}
    for route in app.routes:
        if hasattr(route, 'methods') and hasattr(route, 'path'):
            path = route.path
            methods = list(route.methods) if route.methods else ["GET"]
            
            # Organize by prefix
            prefix = "/" + path.split("/")[1] if len(path.split("/")) > 1 else "/"
            if prefix not in endpoints_by_prefix:
                endpoints_by_prefix[prefix] = []
            
            endpoints_by_prefix[prefix].append({
                "path": path,
                "methods": methods
            })
    
    health_status["available_endpoints"] = endpoints_by_prefix
    health_status["endpoint_count"] = len(app.routes)
    
    return health_status

@app.get("/status")
async def service_status():
    """Simple service status endpoint for monitoring"""
    uptime = (datetime.utcnow() - APP_METADATA['startup_time']).total_seconds()
    services_available = sum(AVAILABLE_SERVICES.values())
    total_services = len(AVAILABLE_SERVICES)
    
    return {
        "status": "running",
        "health": "healthy" if services_available >= 2 else "degraded",  # At least FastAPI + settings
        "services_available": services_available,
        "total_services": total_services,
        "service_availability_percent": round((services_available / total_services) * 100, 2),
        "uptime_seconds": uptime,
        "version": getattr(settings, 'VERSION', '1.0.0'),
        "environment": getattr(settings, 'ENVIRONMENT', 'unknown'),
        "timestamp": datetime.utcnow().isoformat()
    }

# Add mock endpoints for testing and demonstration
@app.get("/api/v1/mock/simulation")
async def mock_simulation():
    """Mock simulation endpoint for testing and demonstration"""
    return {
        "id": "mock-sim-001",
        "name": "Mock Retirement Simulation",
        "status": "completed",
        "type": "monte_carlo",
        "results": {
            "probability_of_success": 0.87,
            "projected_final_value": 2150000,
            "monthly_contribution_required": 2200,
            "years_to_goal": 30,
            "risk_level": 5,
            "expected_return": 0.075
        },
        "parameters": {
            "initial_investment": 50000,
            "monthly_contribution": 2000,
            "investment_horizon_years": 30,
            "target_amount": 2000000
        },
        "disclaimer": "This is mock data for testing and demonstration purposes only. Not for actual financial planning.",
        "mock": True,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/api/v1/mock/portfolio")
async def mock_portfolio():
    """Mock portfolio endpoint for testing"""
    return {
        "id": "mock-portfolio-001",
        "name": "Balanced Growth Portfolio",
        "risk_level": 5,
        "asset_allocation": {
            "stocks": 60,
            "bonds": 25,
            "real_estate": 10,
            "cash": 5
        },
        "expected_return": 0.075,
        "volatility": 0.12,
        "sharpe_ratio": 0.625,
        "mock": True,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/debug")
async def debug_info():
    """Debug information endpoint (only in development/debug mode)"""
    debug_enabled = getattr(settings, 'DEBUG', False)
    environment = getattr(settings, 'ENVIRONMENT', 'production')
    
    if not debug_enabled and environment == 'production':
        raise HTTPException(status_code=404, detail="Not found")
    
    # Get environment variables (sanitized)
    env_vars = {}
    for key, value in os.environ.items():
        if any(sensitive in key.lower() for sensitive in ['password', 'secret', 'key', 'token']):
            env_vars[key] = "[REDACTED]"
        else:
            env_vars[key] = value
    
    return {
        "application": {
            "name": APP_METADATA["name"],
            "version": getattr(settings, 'VERSION', '1.0.0'),
            "startup_time": APP_METADATA["startup_time"].isoformat(),
            "routes_count": len(app.routes)
        },
        "system": {
            "python_version": sys.version,
            "platform": platform.platform(),
            "architecture": platform.architecture(),
            "current_directory": os.getcwd(),
            "python_path": sys.path[:5]  # First 5 entries only
        },
        "services": {
            "available_services": AVAILABLE_SERVICES,
            "import_errors": IMPORT_ERRORS
        },
        "settings": {
            key: getattr(settings, key, None) 
            for key in ['PROJECT_NAME', 'VERSION', 'API_V1_STR', 'DEBUG', 'ENVIRONMENT', 'HOST', 'PORT']
        },
        "environment_variables": env_vars if debug_enabled else "[REDACTED - Debug mode required]",
        "debug_mode": debug_enabled,
        "timestamp": datetime.utcnow().isoformat()
    }

# Main execution
if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        workers=settings.WORKERS
    )