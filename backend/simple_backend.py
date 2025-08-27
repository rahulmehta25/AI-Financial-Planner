#!/usr/bin/env python3
"""
Simple FastAPI Backend for AI Financial Planning Demo
====================================================

A minimal backend that provides the essential endpoints for the HTML demo.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import numpy as np
from datetime import datetime
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AI Financial Planning System - Simple Backend",
    description="Minimal backend for financial planning demo",
    version="1.0.0"
)

# CORS configuration - Allow the Vercel frontend
FRONTEND_URL = os.getenv("FRONTEND_URL", "https://ai-financial-planner-zeta.vercel.app")
DEBUG_MODE = os.getenv("DEBUG", "false").lower() == "true"

# Set up allowed origins
allowed_origins = [
    FRONTEND_URL,
    "https://ai-financial-planner-zeta.vercel.app",
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173"
]

# In development, allow all origins
if DEBUG_MODE:
    allowed_origins.append("*")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Data models
class SimulationRequest(BaseModel):
    age: int
    income: float
    savings: float
    risk_tolerance: str

class SimulationResponse(BaseModel):
    success_probability: float
    median_balance: float
    recommendation: str
    risk_level: str
    timestamp: str

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "AI Financial Planning System API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": [
            "/health",
            "/simulate",
            "/api/v1/simulations/monte-carlo",
            "/docs"
        ]
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "AI Financial Planning API",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/simulate", response_model=SimulationResponse)
async def run_simulation(request: SimulationRequest):
    """Run financial planning simulation"""
    try:
        # Extract parameters
        age = request.age
        income = request.income
        monthly_savings = request.savings
        risk_tolerance = request.risk_tolerance
        
        # Validate inputs
        if age < 18 or age > 100:
            raise HTTPException(status_code=400, detail="Age must be between 18 and 100")
        if income <= 0:
            raise HTTPException(status_code=400, detail="Income must be positive")
        if monthly_savings < 0:
            raise HTTPException(status_code=400, detail="Savings cannot be negative")
        
        # Calculate years to retirement
        years_to_retirement = max(0, 65 - age)
        
        # Risk-adjusted return rates based on risk tolerance
        risk_returns = {
            "conservative": 0.05,  # 5% annual return
            "moderate": 0.07,      # 7% annual return
            "aggressive": 0.09     # 9% annual return
        }
        
        expected_return = risk_returns.get(risk_tolerance, 0.07)
        
        # Monte Carlo simulation parameters
        n_simulations = 10000
        monthly_return = (1 + expected_return) ** (1/12) - 1
        
        # Generate random returns for Monte Carlo simulation
        np.random.seed(42)  # For reproducible results
        monthly_returns = np.random.normal(monthly_return, monthly_return * 0.3, (n_simulations, years_to_retirement * 12))
        
        # Calculate portfolio values for each simulation
        portfolio_values = np.zeros(n_simulations)
        
        for i in range(n_simulations):
            portfolio_value = monthly_savings * 12  # Initial annual savings
            for month in range(years_to_retirement * 12):
                if month > 0:
                    portfolio_value = portfolio_value * (1 + monthly_returns[i, month])
                portfolio_value += monthly_savings
        
            portfolio_values[i] = portfolio_value
        
        # Calculate statistics
        median_balance = np.median(portfolio_values)
        success_threshold = income * 0.8 * 25  # 80% of income for 25 years
        
        # Calculate success probability
        success_count = np.sum(portfolio_values >= success_threshold)
        success_probability = (success_count / n_simulations) * 100
        
        # Generate recommendation
        if success_probability >= 80:
            recommendation = "Excellent! You're on track for a comfortable retirement."
        elif success_probability >= 60:
            recommendation = "Good progress! Consider increasing your savings rate."
        elif success_probability >= 40:
            recommendation = "You're making progress. Consider increasing savings and starting earlier."
        else:
            recommendation = "Consider increasing your savings rate significantly and starting earlier."
        
        return SimulationResponse(
            success_probability=round(success_probability, 1),
            median_balance=round(median_balance),
            recommendation=recommendation,
            risk_level=risk_tolerance,
            timestamp=datetime.utcnow().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Simulation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Simulation failed: {str(e)}")

# Add the endpoint the frontend expects
@app.post("/api/v1/simulations/monte-carlo")
async def monte_carlo_simulation(request: SimulationRequest):
    """Monte Carlo simulation endpoint that the frontend expects"""
    # This is the same as the /simulate endpoint but with the path the frontend expects
    return await run_simulation(request)

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

if __name__ == "__main__":
    import uvicorn
    import os
    
    # Get port from environment variable (required for Render.com)
    port = int(os.environ.get("PORT", 8000))
    
    print("🚀 Starting AI Financial Planning System - Simple Backend")
    print(f"📚 API Documentation: http://localhost:{port}/docs")
    print(f"❤️  Health Check: http://localhost:{port}/health")
    print(f"🎮 Simulation Endpoint: POST http://localhost:{port}/simulate")
    print(f"🎲 Frontend Simulation Endpoint: POST http://localhost:{port}/api/v1/simulations/monte-carlo")
    
    uvicorn.run(
        "simple_backend:app",
        host="0.0.0.0",
        port=port,
        reload=False,  # Disable reload in production
        log_level="info"
    )
