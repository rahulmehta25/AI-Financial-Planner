"""
Social platform integration patch for existing API router
Apply this integration to app/api/v1/api.py
"""

# Add this import to the existing imports:
# from app.social.router import router as social_router

# Add this line after the existing router includes:
# api_router.include_router(social_router, tags=["social-platform"])

# The complete integrated file should look like this:

api_integration_code = '''
"""
Main API router for v1 endpoints
"""

from fastapi import APIRouter
from app.api.v1.endpoints import auth, users, financial_profiles, goals, investments, simulations, market_data, monte_carlo, pdf_export, ml_recommendations, banking, voice
from app.social.router import router as social_router

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(financial_profiles.router, prefix="/financial-profiles", tags=["financial-profiles"])
api_router.include_router(goals.router, prefix="/goals", tags=["goals"])
api_router.include_router(investments.router, prefix="/investments", tags=["investments"])
api_router.include_router(simulations.router, prefix="/simulations", tags=["simulations"])
api_router.include_router(monte_carlo.router, prefix="/monte-carlo", tags=["monte-carlo"])
api_router.include_router(market_data.router, prefix="/market-data", tags=["market-data"])
api_router.include_router(pdf_export.router, prefix="", tags=["pdf-export"])
api_router.include_router(ml_recommendations.router, prefix="/ml", tags=["ml-recommendations"])
api_router.include_router(voice.router, prefix="/voice", tags=["voice-interface"])
api_router.include_router(banking.router, prefix="/banking", tags=["banking"])

# Include social platform router
api_router.include_router(social_router, tags=["social-platform"])
'''

# To manually integrate:
# 1. Add the social router import to the imports section
# 2. Add the include_router line after the existing routers

print("Integration patch created. Apply manually to app/api/v1/api.py")