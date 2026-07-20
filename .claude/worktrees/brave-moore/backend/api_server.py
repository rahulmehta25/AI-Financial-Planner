#!/usr/bin/env python3
"""
Financial Planning API Server with Frontend Integration
"""

import uvicorn
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import json
import random
import hashlib
import secrets

# Create FastAPI app
app = FastAPI(
    title="AI Financial Planning System API",
    description="Complete Financial Planning API with Authentication",
    version="2.0.0"
)

# Add CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Models
class UserRegister(BaseModel):
    email: str
    password: str
    full_name: str

class UserLogin(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: Dict[str, Any]

class FinancialGoal(BaseModel):
    id: Optional[str] = None
    name: str
    target_amount: float
    current_amount: float
    target_date: str
    priority: str = "medium"
    category: str

class Portfolio(BaseModel):
    total_value: float
    holdings: List[Dict[str, Any]]
    performance: Dict[str, float]

# In-memory storage
users_db = {}
sessions = {}
goals_db = {}
portfolios_db = {}

# Helper functions
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def create_token(email: str) -> str:
    token = secrets.token_urlsafe(32)
    sessions[token] = {
        "email": email,
        "created_at": datetime.now().isoformat()
    }
    return token

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    token = credentials.credentials
    if token not in sessions:
        raise HTTPException(status_code=401, detail="Invalid token")
    return sessions[token]["email"]

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "AI Financial Planning System API",
        "version": "2.0.0",
        "status": "running",
        "endpoints": {
            "auth": "/api/v1/auth/",
            "users": "/api/v1/users/",
            "financial": "/api/v1/financial/",
            "portfolio": "/api/v1/portfolio/",
            "simulations": "/api/v1/simulations/",
            "ai": "/api/v1/ai/",
            "docs": "/docs"
        }
    }

# Health check
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().timestamp(),
        "service": "AI Financial Planning API"
    }

# Authentication endpoints
@app.post("/api/v1/auth/register", response_model=Token)
async def register(user: UserRegister):
    if user.email in users_db:
        raise HTTPException(status_code=400, detail="User already exists")
    
    users_db[user.email] = {
        "email": user.email,
        "password": hash_password(user.password),
        "full_name": user.full_name,
        "created_at": datetime.now().isoformat()
    }
    
    token = create_token(user.email)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "email": user.email,
            "full_name": user.full_name
        }
    }

@app.post("/api/v1/auth/login", response_model=Token)
async def login(user: UserLogin):
    if user.email not in users_db:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if users_db[user.email]["password"] != hash_password(user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_token(user.email)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "email": user.email,
            "full_name": users_db[user.email]["full_name"]
        }
    }

@app.post("/api/v1/auth/logout")
async def logout(email: str = Depends(verify_token)):
    # Remove token from sessions
    tokens_to_remove = [t for t, s in sessions.items() if s["email"] == email]
    for token in tokens_to_remove:
        del sessions[token]
    return {"message": "Logged out successfully"}

# User endpoints
@app.get("/api/v1/users/profile")
async def get_profile(email: str = Depends(verify_token)):
    if email not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "email": email,
        "full_name": users_db[email]["full_name"],
        "risk_tolerance": "moderate",
        "created_at": users_db[email]["created_at"]
    }

@app.get("/api/v1/users/settings")
async def get_settings(email: str = Depends(verify_token)):
    return {
        "notifications": True,
        "theme": "light",
        "currency": "USD",
        "language": "en"
    }

# Financial endpoints
@app.get("/api/v1/financial/accounts")
async def get_accounts(email: str = Depends(verify_token)):
    return {
        "accounts": [
            {
                "id": "acc_1",
                "name": "Checking Account",
                "type": "checking",
                "balance": 15000.00,
                "currency": "USD"
            },
            {
                "id": "acc_2",
                "name": "Savings Account",
                "type": "savings",
                "balance": 50000.00,
                "currency": "USD"
            },
            {
                "id": "acc_3",
                "name": "Investment Account",
                "type": "investment",
                "balance": 125000.00,
                "currency": "USD"
            }
        ]
    }

@app.get("/api/v1/financial/transactions")
async def get_transactions(email: str = Depends(verify_token)):
    return {
        "transactions": [
            {
                "id": "tx_1",
                "date": "2024-01-15",
                "description": "Salary Deposit",
                "amount": 8500.00,
                "type": "credit",
                "category": "Income"
            },
            {
                "id": "tx_2",
                "date": "2024-01-14",
                "description": "Mortgage Payment",
                "amount": -2500.00,
                "type": "debit",
                "category": "Housing"
            }
        ]
    }

@app.get("/api/v1/financial/goals")
async def get_goals(email: str = Depends(verify_token)):
    if email not in goals_db:
        goals_db[email] = [
            {
                "id": "goal_1",
                "name": "Emergency Fund",
                "target_amount": 30000,
                "current_amount": 15000,
                "target_date": "2024-12-31",
                "priority": "high",
                "category": "savings"
            },
            {
                "id": "goal_2",
                "name": "House Down Payment",
                "target_amount": 100000,
                "current_amount": 45000,
                "target_date": "2025-12-31",
                "priority": "medium",
                "category": "real_estate"
            }
        ]
    return {"goals": goals_db[email]}

# Portfolio endpoints
@app.get("/api/v1/portfolio/overview")
async def get_portfolio_overview(email: str = Depends(verify_token)):
    return {
        "total_value": 125000.00,
        "total_gain": 15000.00,
        "total_gain_percent": 13.64,
        "day_change": 1250.00,
        "day_change_percent": 1.01
    }

@app.get("/api/v1/portfolio/holdings")
async def get_holdings(email: str = Depends(verify_token)):
    return {
        "holdings": [
            {
                "symbol": "AAPL",
                "name": "Apple Inc.",
                "shares": 100,
                "price": 185.50,
                "value": 18550.00,
                "gain": 2550.00
            },
            {
                "symbol": "MSFT",
                "name": "Microsoft Corp.",
                "shares": 50,
                "price": 420.00,
                "value": 21000.00,
                "gain": 3000.00
            }
        ]
    }

# AI endpoints
@app.post("/api/v1/ai/chat")
async def ai_chat(message: str, email: str = Depends(verify_token)):
    responses = [
        "Based on your financial profile, I recommend diversifying your portfolio with index funds.",
        "Your emergency fund is at 50% of target. Consider increasing monthly contributions.",
        "Market analysis suggests maintaining your current investment strategy.",
        "Your spending patterns show opportunity for saving an additional $500/month."
    ]
    return {
        "response": random.choice(responses),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/v1/ai/recommendations")
async def get_recommendations(email: str = Depends(verify_token)):
    return {
        "recommendations": [
            {
                "id": "rec_1",
                "title": "Increase Emergency Fund",
                "description": "Your emergency fund is below recommended levels",
                "priority": "high",
                "potential_impact": "$500/month savings"
            },
            {
                "id": "rec_2",
                "title": "Rebalance Portfolio",
                "description": "Your tech allocation exceeds 40% of portfolio",
                "priority": "medium",
                "potential_impact": "Reduce risk by 15%"
            }
        ]
    }

@app.get("/api/v1/ai/insights")
async def get_insights(email: str = Depends(verify_token)):
    return {
        "insights": [
            {
                "category": "spending",
                "insight": "You spent 20% less on dining this month",
                "trend": "positive"
            },
            {
                "category": "saving",
                "insight": "On track to meet yearly savings goal",
                "trend": "positive"
            }
        ]
    }

# Simulations endpoints
@app.post("/api/v1/simulations/monte-carlo")
async def run_monte_carlo(
    initial_amount: float = 100000,
    monthly_contribution: float = 1000,
    years: int = 10,
    email: str = Depends(verify_token)
):
    # Simple Monte Carlo simulation
    scenarios = []
    for _ in range(100):
        final_value = initial_amount
        for year in range(years):
            annual_return = random.gauss(0.07, 0.15)  # 7% mean, 15% std dev
            final_value = final_value * (1 + annual_return) + (monthly_contribution * 12)
        scenarios.append(final_value)
    
    scenarios.sort()
    return {
        "median_outcome": scenarios[50],
        "best_case": scenarios[90],
        "worst_case": scenarios[10],
        "success_probability": len([s for s in scenarios if s > initial_amount * 2]) / 100
    }

@app.post("/api/v1/simulations/portfolio-optimization")
async def optimize_portfolio(
    risk_tolerance: str = "moderate",
    email: str = Depends(verify_token)
):
    allocations = {
        "conservative": {"stocks": 30, "bonds": 60, "cash": 10},
        "moderate": {"stocks": 60, "bonds": 30, "cash": 10},
        "aggressive": {"stocks": 80, "bonds": 15, "cash": 5}
    }
    
    return {
        "recommended_allocation": allocations.get(risk_tolerance, allocations["moderate"]),
        "expected_return": random.uniform(5, 12),
        "risk_score": random.uniform(3, 8)
    }

# Demo data endpoint
@app.get("/demo")
async def get_demo_info():
    return {
        "message": "Demo API is running",
        "sample_credentials": {
            "email": "demo@example.com",
            "password": "demo123"
        },
        "endpoints": {
            "register": "POST /api/v1/auth/register",
            "login": "POST /api/v1/auth/login",
            "profile": "GET /api/v1/users/profile",
            "portfolio": "GET /api/v1/portfolio/overview",
            "goals": "GET /api/v1/financial/goals"
        }
    }

if __name__ == "__main__":
    print("🚀 Starting AI Financial Planning API Server...")
    print("📚 API Documentation: http://localhost:8000/docs")
    print("🔗 Frontend Connection: http://localhost:5173")
    print("=" * 60)
    
    # Create demo user
    demo_email = "demo@example.com"
    if demo_email not in users_db:
        users_db[demo_email] = {
            "email": demo_email,
            "password": hash_password("demo123"),
            "full_name": "Demo User",
            "created_at": datetime.now().isoformat()
        }
    
    uvicorn.run(app, host="0.0.0.0", port=8000)