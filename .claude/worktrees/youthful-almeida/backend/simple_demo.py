#!/usr/bin/env python3
"""
Simple Financial Planning Demo - FastAPI Server
This is a basic working demo that showcases the core functionality
"""

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import json
import random
import time

# Create FastAPI app
app = FastAPI(
    title="AI Financial Planning Demo",
    description="Simple Financial Planning API Demo",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple data models
class FinancialProfile(BaseModel):
    age: int
    income: float
    savings: float
    risk_tolerance: str

class SimulationResult(BaseModel):
    success_probability: float
    median_balance: float
    recommendation: str

# In-memory storage for demo
users = {}
simulations = {}

@app.get("/")
async def root():
    return {
        "message": "AI Financial Planning Demo API",
        "status": "running",
        "endpoints": [
            "/health",
            "/demo",
            "/simulate",
            "/docs"
        ]
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "service": "AI Financial Planning Demo"
    }

@app.get("/demo")
async def demo_info():
    return {
        "title": "AI Financial Planning System Demo",
        "features": [
            "Monte Carlo Simulations",
            "Portfolio Optimization", 
            "Risk Assessment",
            "Financial Planning",
            "PDF Report Generation"
        ],
        "demo_accounts": [
            {"email": "demo@example.com", "password": "demo123"},
            {"email": "user@example.com", "password": "user123"}
        ],
        "quick_start": [
            "1. Visit /docs for interactive API documentation",
            "2. Use POST /simulate to run financial simulations",
            "3. Explore the various endpoints"
        ]
    }

@app.post("/simulate")
async def run_simulation(profile: FinancialProfile):
    """Run a simple financial simulation"""
    
    # Simple simulation logic for demo
    base_probability = 0.7  # 70% base success rate
    
    # Adjust based on age
    if profile.age < 30:
        age_multiplier = 1.2
    elif profile.age < 50:
        age_multiplier = 1.0
    else:
        age_multiplier = 0.8
    
    # Adjust based on savings rate
    savings_rate = profile.savings / profile.income if profile.income > 0 else 0
    if savings_rate > 0.2:
        savings_multiplier = 1.3
    elif savings_rate > 0.1:
        savings_multiplier = 1.1
    else:
        savings_multiplier = 0.9
    
    # Adjust based on risk tolerance
    risk_multipliers = {
        "conservative": 0.9,
        "moderate": 1.0,
        "aggressive": 1.1
    }
    risk_multiplier = risk_multipliers.get(profile.risk_tolerance, 1.0)
    
    # Calculate final probability
    success_probability = min(0.95, base_probability * age_multiplier * savings_multiplier * risk_multiplier)
    
    # Generate median balance (simple calculation)
    years_to_retirement = 65 - profile.age
    annual_savings = profile.savings * 12
    expected_return = 0.07  # 7% annual return
    
    if years_to_retirement > 0:
        median_balance = profile.savings * (1 + expected_return) ** years_to_retirement + \
                        annual_savings * ((1 + expected_return) ** years_to_retirement - 1) / expected_return
    else:
        median_balance = profile.savings
    
    # Generate recommendation
    if success_probability > 0.8:
        recommendation = "Excellent! You're on track for a comfortable retirement."
    elif success_probability > 0.6:
        recommendation = "Good progress! Consider increasing your savings rate."
    else:
        recommendation = "Consider increasing your savings rate and starting earlier."
    
    result = SimulationResult(
        success_probability=round(success_probability * 100, 1),
        median_balance=round(median_balance, 2),
        recommendation=recommendation
    )
    
    # Store simulation result
    simulation_id = f"sim_{int(time.time())}"
    simulations[simulation_id] = {
        "profile": profile.dict(),
        "result": result.dict(),
        "timestamp": time.time()
    }
    
    return {
        "simulation_id": simulation_id,
        "result": result,
        "message": "Simulation completed successfully"
    }

@app.get("/simulations/{simulation_id}")
async def get_simulation(simulation_id: str):
    """Get a specific simulation result"""
    if simulation_id not in simulations:
        raise HTTPException(status_code=404, detail="Simulation not found")
    
    return simulations[simulation_id]

@app.get("/simulations")
async def list_simulations():
    """List all simulations"""
    return {
        "total_simulations": len(simulations),
        "simulations": list(simulations.keys())
    }

@app.get("/portfolio-optimization")
async def portfolio_optimization(risk_tolerance: str = "moderate"):
    """Get portfolio optimization recommendations"""
    
    portfolios = {
        "conservative": {
            "stocks": "30%",
            "bonds": "60%",
            "cash": "10%",
            "expected_return": "5.5%",
            "risk_level": "Low"
        },
        "moderate": {
            "stocks": "60%",
            "bonds": "35%",
            "cash": "5%",
            "expected_return": "7.5%",
            "risk_level": "Medium"
        },
        "aggressive": {
            "stocks": "80%",
            "bonds": "15%",
            "cash": "5%",
            "expected_return": "9.5%",
            "risk_level": "High"
        }
    }
    
    if risk_tolerance not in portfolios:
        raise HTTPException(status_code=400, detail="Invalid risk tolerance")
    
    return {
        "risk_tolerance": risk_tolerance,
        "recommended_allocation": portfolios[risk_tolerance],
        "disclaimer": "This is for demonstration purposes only. Consult a financial advisor for actual investment advice."
    }

@app.get("/market-data")
async def market_data():
    """Get sample market data"""
    return {
        "asset_classes": [
            {
                "name": "US Large Cap Stocks",
                "expected_return": "10.0%",
                "volatility": "16.0%",
                "sharpe_ratio": "0.44"
            },
            {
                "name": "International Stocks", 
                "expected_return": "8.5%",
                "volatility": "18.0%",
                "sharpe_ratio": "0.31"
            },
            {
                "name": "US Government Bonds",
                "expected_return": "4.5%",
                "volatility": "5.0%",
                "sharpe_ratio": "0.30"
            },
            {
                "name": "Real Estate (REITs)",
                "expected_return": "8.0%",
                "volatility": "19.0%",
                "sharpe_ratio": "0.26"
            }
        ],
        "last_updated": time.time()
    }

if __name__ == "__main__":
    print("🚀 Starting AI Financial Planning Demo Server...")
    print("📚 API Documentation: http://localhost:8000/docs")
    print("🔗 Health Check: http://localhost:8000/health")
    print("🎮 Demo Info: http://localhost:8000/demo")
    print("=" * 60)
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
