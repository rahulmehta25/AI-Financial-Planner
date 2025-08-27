"""
Main API router for v1 endpoints
"""

from fastapi import APIRouter
from app.api.v1.endpoints import auth, users, financial_profiles, goals, investments, simulations, market_data, monte_carlo, pdf_export, ml_recommendations, banking, voice, notifications, financial, ai, portfolio, websocket, advanced_strategies, retirement, irs_compliance
from app.social.router import router as social_router

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(financial_profiles.router, prefix="/financial-profiles", tags=["financial-profiles"])
api_router.include_router(goals.router, prefix="/goals", tags=["goals"])
api_router.include_router(investments.router, prefix="/investments", tags=["investments"])
api_router.include_router(monte_carlo.router, prefix="/simulations", tags=["monte-carlo"])
api_router.include_router(simulations.router, prefix="/simulations", tags=["simulations"])
api_router.include_router(market_data.router, prefix="/market-data", tags=["market-data"])
api_router.include_router(pdf_export.router, prefix="", tags=["pdf-export"])
api_router.include_router(ml_recommendations.router, prefix="/ml", tags=["ml-recommendations"])
api_router.include_router(voice.router, prefix="/voice", tags=["voice-interface"])
api_router.include_router(banking.router, prefix="/banking", tags=["banking"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])
api_router.include_router(financial.router, prefix="/financial", tags=["financial"])
api_router.include_router(ai.router, prefix="/ai", tags=["ai"])
api_router.include_router(portfolio.router, prefix="/portfolio", tags=["portfolio"])
api_router.include_router(retirement.router, prefix="/retirement", tags=["retirement"])
api_router.include_router(irs_compliance.router, prefix="/irs", tags=["irs-compliance"])
api_router.include_router(advanced_strategies.router, prefix="", tags=["advanced-strategies"])
api_router.include_router(websocket.router, prefix="", tags=["websocket"])