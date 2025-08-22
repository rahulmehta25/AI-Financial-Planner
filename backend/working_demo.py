#!/usr/bin/env python3
"""
Complete Working Demo - AI Financial Planning System
==================================================

A fully functional demo application that showcases:
✅ FastAPI backend with SQLite database
✅ User registration and JWT authentication
✅ Monte Carlo portfolio simulations
✅ Financial goal optimization
✅ Risk assessment and recommendations
✅ JSON API responses viewable in browser
✅ CORS enabled for frontend integration

Features:
- No PostgreSQL required - uses SQLite
- Simple setup and immediate functionality
- Sample data generation
- Health check endpoint
- Complete financial planning workflow

Run with: python working_demo.py
"""

import os
import sys
import json
import asyncio
import logging
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path

# Third-party imports
import uvicorn
import numpy as np
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from passlib.context import CryptContext
from jose import JWTError, jwt
import sqlite3

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
SECRET_KEY = "demo_secret_key_change_in_production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
DATABASE_FILE = "demo_financial_planning.db"

# Initialize FastAPI app
app = FastAPI(
    title="AI Financial Planning Demo",
    description="A complete working demo of the AI Financial Planning System",
    version="1.0.0"
)

# CORS configuration for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# Pydantic Models
class UserCreate(BaseModel):
    email: str
    password: str
    name: str
    age: int = Field(ge=18, le=100)

class UserLogin(BaseModel):
    email: str
    password: str

class FinancialProfile(BaseModel):
    user_id: int
    current_income: float = Field(gt=0)
    current_savings: float = Field(ge=0)
    monthly_expenses: float = Field(gt=0)
    risk_tolerance: str = Field(regex="^(conservative|moderate|aggressive)$")

class FinancialGoal(BaseModel):
    user_id: int
    goal_type: str
    target_amount: float = Field(gt=0)
    target_date: str
    priority: int = Field(ge=1, le=5)
    description: str

class SimulationRequest(BaseModel):
    user_id: int
    years_to_retirement: int = Field(ge=1, le=50)
    monthly_contribution: float = Field(gt=0)
    initial_amount: float = Field(ge=0)
    risk_level: str = Field(regex="^(conservative|moderate|aggressive)$")

# Database Setup
def init_database():
    """Initialize SQLite database with required tables"""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    # Users table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        name TEXT NOT NULL,
        age INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Financial profiles table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS financial_profiles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        current_income REAL NOT NULL,
        current_savings REAL NOT NULL,
        monthly_expenses REAL NOT NULL,
        risk_tolerance TEXT NOT NULL,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    """)
    
    # Financial goals table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS financial_goals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        goal_type TEXT NOT NULL,
        target_amount REAL NOT NULL,
        target_date DATE NOT NULL,
        priority INTEGER NOT NULL,
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    """)
    
    # Simulation results table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS simulation_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        simulation_type TEXT NOT NULL,
        parameters TEXT NOT NULL,
        results TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    """)
    
    conn.commit()
    conn.close()
    logger.info("Database initialized successfully")

# Authentication Functions
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash password"""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current user from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_email: str = payload.get("sub")
        if user_email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    # Get user from database
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (user_email,))
    user = cursor.fetchone()
    conn.close()
    
    if user is None:
        raise credentials_exception
    
    return {
        "id": user[0],
        "email": user[1],
        "name": user[3],
        "age": user[4]
    }

# Monte Carlo Simulation Functions
def simulate_portfolio_growth(
    initial_amount: float,
    monthly_contribution: float,
    annual_return: float,
    annual_volatility: float,
    years: int,
    num_simulations: int = 1000
) -> Dict[str, Any]:
    """
    Run Monte Carlo simulation for portfolio growth
    """
    monthly_return = annual_return / 12
    monthly_volatility = annual_volatility / np.sqrt(12)
    months = years * 12
    
    # Generate random returns for all simulations
    np.random.seed(42)  # For reproducible results in demo
    random_returns = np.random.normal(monthly_return, monthly_volatility, (num_simulations, months))
    
    # Initialize arrays
    portfolio_values = np.zeros((num_simulations, months + 1))
    portfolio_values[:, 0] = initial_amount
    
    # Simulate portfolio growth
    for month in range(months):
        # Add monthly contribution
        portfolio_values[:, month + 1] = portfolio_values[:, month] + monthly_contribution
        # Apply investment returns
        portfolio_values[:, month + 1] *= (1 + random_returns[:, month])
    
    final_values = portfolio_values[:, -1]
    
    return {
        "final_values": final_values.tolist(),
        "median_value": float(np.median(final_values)),
        "percentile_10": float(np.percentile(final_values, 10)),
        "percentile_25": float(np.percentile(final_values, 25)),
        "percentile_75": float(np.percentile(final_values, 75)),
        "percentile_90": float(np.percentile(final_values, 90)),
        "mean_value": float(np.mean(final_values)),
        "std_value": float(np.std(final_values)),
        "success_probability": float(np.mean(final_values > initial_amount * 2)),  # Doubling money
        "portfolio_paths": portfolio_values[:100].tolist()  # First 100 paths for visualization
    }

def get_risk_parameters(risk_level: str) -> Dict[str, float]:
    """Get expected return and volatility based on risk level"""
    risk_profiles = {
        "conservative": {"annual_return": 0.06, "annual_volatility": 0.08},
        "moderate": {"annual_return": 0.08, "annual_volatility": 0.12},
        "aggressive": {"annual_return": 0.10, "annual_volatility": 0.18}
    }
    return risk_profiles.get(risk_level, risk_profiles["moderate"])

# API Endpoints

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "AI Financial Planning Demo API",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": {
            "health": "/health",
            "register": "/register",
            "login": "/login", 
            "profile": "/profile",
            "goals": "/goals",
            "simulate": "/simulate",
            "recommendations": "/recommendations",
            "sample_data": "/sample-data"
        },
        "demo_users": {
            "email": "demo@example.com",
            "password": "demo123",
            "description": "Pre-created demo user account"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        conn = sqlite3.connect(DATABASE_FILE)
        conn.close()
        db_status = "healthy"
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "database": db_status,
        "version": "1.0.0"
    }

@app.post("/register")
async def register_user(user: UserCreate):
    """Register a new user"""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    # Check if user already exists
    cursor.execute("SELECT id FROM users WHERE email = ?", (user.email,))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new user
    password_hash = get_password_hash(user.password)
    cursor.execute(
        "INSERT INTO users (email, password_hash, name, age) VALUES (?, ?, ?, ?)",
        (user.email, password_hash, user.name, user.age)
    )
    user_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    return {
        "message": "User registered successfully",
        "user_id": user_id,
        "access_token": access_token,
        "token_type": "bearer"
    }

@app.post("/login")
async def login(user: UserLogin):
    """User login"""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (user.email,))
    db_user = cursor.fetchone()
    conn.close()
    
    if not db_user or not verify_password(user.password, db_user[2]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": db_user[0],
            "email": db_user[1],
            "name": db_user[3],
            "age": db_user[4]
        }
    }

@app.get("/profile")
async def get_profile(current_user: dict = Depends(get_current_user)):
    """Get user's financial profile"""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM financial_profiles WHERE user_id = ?", (current_user["id"],))
    profile = cursor.fetchone()
    conn.close()
    
    if not profile:
        # Return default profile structure if none exists
        return {
            "user_id": current_user["id"],
            "current_income": 0,
            "current_savings": 0,
            "monthly_expenses": 0,
            "risk_tolerance": "moderate",
            "has_profile": False
        }
    
    return {
        "id": profile[0],
        "user_id": profile[1],
        "current_income": profile[2],
        "current_savings": profile[3],
        "monthly_expenses": profile[4],
        "risk_tolerance": profile[5],
        "has_profile": True
    }

@app.post("/profile")
async def create_update_profile(
    profile: FinancialProfile,
    current_user: dict = Depends(get_current_user)
):
    """Create or update financial profile"""
    if profile.user_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    # Check if profile exists
    cursor.execute("SELECT id FROM financial_profiles WHERE user_id = ?", (profile.user_id,))
    existing = cursor.fetchone()
    
    if existing:
        # Update existing profile
        cursor.execute("""
            UPDATE financial_profiles 
            SET current_income = ?, current_savings = ?, monthly_expenses = ?, 
                risk_tolerance = ?, updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
        """, (
            profile.current_income, profile.current_savings, 
            profile.monthly_expenses, profile.risk_tolerance, profile.user_id
        ))
    else:
        # Create new profile
        cursor.execute("""
            INSERT INTO financial_profiles 
            (user_id, current_income, current_savings, monthly_expenses, risk_tolerance)
            VALUES (?, ?, ?, ?, ?)
        """, (
            profile.user_id, profile.current_income, profile.current_savings,
            profile.monthly_expenses, profile.risk_tolerance
        ))
    
    conn.commit()
    conn.close()
    
    return {"message": "Profile updated successfully"}

@app.get("/goals")
async def get_goals(current_user: dict = Depends(get_current_user)):
    """Get user's financial goals"""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM financial_goals WHERE user_id = ?", (current_user["id"],))
    goals = cursor.fetchall()
    conn.close()
    
    return [
        {
            "id": goal[0],
            "user_id": goal[1],
            "goal_type": goal[2],
            "target_amount": goal[3],
            "target_date": goal[4],
            "priority": goal[5],
            "description": goal[6]
        }
        for goal in goals
    ]

@app.post("/goals")
async def create_goal(
    goal: FinancialGoal,
    current_user: dict = Depends(get_current_user)
):
    """Create a new financial goal"""
    if goal.user_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO financial_goals 
        (user_id, goal_type, target_amount, target_date, priority, description)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        goal.user_id, goal.goal_type, goal.target_amount,
        goal.target_date, goal.priority, goal.description
    ))
    goal_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return {"message": "Goal created successfully", "goal_id": goal_id}

@app.post("/simulate")
async def run_simulation(
    request: SimulationRequest,
    current_user: dict = Depends(get_current_user)
):
    """Run Monte Carlo simulation for portfolio growth"""
    if request.user_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Get risk parameters
    risk_params = get_risk_parameters(request.risk_level)
    
    # Run simulation
    simulation_results = simulate_portfolio_growth(
        initial_amount=request.initial_amount,
        monthly_contribution=request.monthly_contribution,
        annual_return=risk_params["annual_return"],
        annual_volatility=risk_params["annual_volatility"],
        years=request.years_to_retirement,
        num_simulations=1000
    )
    
    # Store results in database
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO simulation_results (user_id, simulation_type, parameters, results)
        VALUES (?, ?, ?, ?)
    """, (
        request.user_id,
        "monte_carlo_portfolio",
        json.dumps(request.dict()),
        json.dumps(simulation_results)
    ))
    conn.commit()
    conn.close()
    
    # Add additional analysis
    monthly_total_invested = request.initial_amount + (request.monthly_contribution * request.years_to_retirement * 12)
    median_return = ((simulation_results["median_value"] - monthly_total_invested) / monthly_total_invested) * 100
    
    return {
        "simulation_id": cursor.lastrowid,
        "parameters": request.dict(),
        "risk_parameters": risk_params,
        "results": simulation_results,
        "analysis": {
            "total_invested": monthly_total_invested,
            "median_return_percentage": median_return,
            "inflation_adjusted_value": simulation_results["median_value"] * (0.97 ** request.years_to_retirement),  # Assuming 3% inflation
            "recommendation": get_simulation_recommendation(simulation_results, request.risk_level)
        }
    }

@app.get("/recommendations")
async def get_recommendations(current_user: dict = Depends(get_current_user)):
    """Get personalized financial recommendations"""
    # Get user profile
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM financial_profiles WHERE user_id = ?", (current_user["id"],))
    profile = cursor.fetchone()
    
    if not profile:
        conn.close()
        return {"message": "Please complete your financial profile first"}
    
    # Get recent simulation results
    cursor.execute("""
        SELECT results FROM simulation_results 
        WHERE user_id = ? ORDER BY created_at DESC LIMIT 1
    """, (current_user["id"],))
    recent_simulation = cursor.fetchone()
    conn.close()
    
    # Generate recommendations
    recommendations = generate_personalized_recommendations(
        profile=profile,
        user_age=current_user["age"],
        recent_simulation=recent_simulation
    )
    
    return recommendations

@app.get("/sample-data")
async def create_sample_data():
    """Create sample data for demonstration"""
    sample_users = [
        {
            "email": "demo@example.com",
            "password": "demo123",
            "name": "Demo User",
            "age": 35
        },
        {
            "email": "young.professional@example.com", 
            "password": "demo123",
            "name": "Young Professional",
            "age": 28
        },
        {
            "email": "experienced.investor@example.com",
            "password": "demo123", 
            "name": "Experienced Investor",
            "age": 45
        }
    ]
    
    created_users = []
    
    for user_data in sample_users:
        try:
            conn = sqlite3.connect(DATABASE_FILE)
            cursor = conn.cursor()
            
            # Check if user exists
            cursor.execute("SELECT id FROM users WHERE email = ?", (user_data["email"],))
            if cursor.fetchone():
                conn.close()
                continue
            
            # Create user
            password_hash = get_password_hash(user_data["password"])
            cursor.execute(
                "INSERT INTO users (email, password_hash, name, age) VALUES (?, ?, ?, ?)",
                (user_data["email"], password_hash, user_data["name"], user_data["age"])
            )
            user_id = cursor.lastrowid
            
            # Create sample profile
            if user_data["age"] <= 30:
                profile_data = {
                    "current_income": 65000,
                    "current_savings": 15000,
                    "monthly_expenses": 3500,
                    "risk_tolerance": "aggressive"
                }
            elif user_data["age"] <= 40:
                profile_data = {
                    "current_income": 85000,
                    "current_savings": 150000,
                    "monthly_expenses": 5500,
                    "risk_tolerance": "moderate"
                }
            else:
                profile_data = {
                    "current_income": 120000,
                    "current_savings": 400000,
                    "monthly_expenses": 7500,
                    "risk_tolerance": "conservative"
                }
            
            cursor.execute("""
                INSERT INTO financial_profiles 
                (user_id, current_income, current_savings, monthly_expenses, risk_tolerance)
                VALUES (?, ?, ?, ?, ?)
            """, (
                user_id, profile_data["current_income"], profile_data["current_savings"],
                profile_data["monthly_expenses"], profile_data["risk_tolerance"]
            ))
            
            # Create sample goals
            cursor.execute("""
                INSERT INTO financial_goals 
                (user_id, goal_type, target_amount, target_date, priority, description)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                user_id, "retirement", 1000000, "2050-12-31", 1, "Comfortable retirement"
            ))
            
            conn.commit()
            conn.close()
            
            created_users.append({
                "user_id": user_id,
                "email": user_data["email"],
                "name": user_data["name"]
            })
            
        except Exception as e:
            logger.error(f"Error creating sample user {user_data['email']}: {e}")
            continue
    
    return {
        "message": f"Created {len(created_users)} sample users",
        "users": created_users,
        "login_instructions": "Use any of these emails with password 'demo123' to test the API"
    }

# Helper Functions
def get_simulation_recommendation(results: Dict, risk_level: str) -> str:
    """Generate recommendation based on simulation results"""
    success_prob = results["success_probability"]
    
    if success_prob > 0.8:
        return f"Excellent! Your {risk_level} strategy has an {success_prob:.0%} chance of success. Consider maintaining your current approach."
    elif success_prob > 0.6:
        return f"Good progress! Your strategy has a {success_prob:.0%} success rate. Consider increasing contributions if possible."
    else:
        return f"Your current strategy has a {success_prob:.0%} success rate. Consider increasing contributions or adjusting risk tolerance."

def generate_personalized_recommendations(profile, user_age: int, recent_simulation) -> Dict:
    """Generate personalized recommendations based on user profile and age"""
    recommendations = []
    
    # Age-based recommendations
    if user_age < 30:
        recommendations.append({
            "category": "Investment Strategy",
            "title": "Aggressive Growth Focus",
            "description": "At your age, consider a higher equity allocation (80-90%) to maximize long-term growth potential.",
            "priority": "high"
        })
    elif user_age < 50:
        recommendations.append({
            "category": "Investment Strategy", 
            "title": "Balanced Growth Approach",
            "description": "Consider a moderate allocation (60-70% equity) to balance growth with stability.",
            "priority": "medium"
        })
    else:
        recommendations.append({
            "category": "Investment Strategy",
            "title": "Capital Preservation",
            "description": "Focus on capital preservation with a conservative allocation (40-50% equity).",
            "priority": "high"
        })
    
    # Savings rate recommendations
    current_income = profile[2]
    current_savings = profile[3]
    monthly_expenses = profile[4]
    monthly_surplus = (current_income / 12) - monthly_expenses
    
    if monthly_surplus > 0:
        savings_rate = (monthly_surplus * 12) / current_income
        if savings_rate < 0.1:
            recommendations.append({
                "category": "Savings",
                "title": "Increase Savings Rate", 
                "description": f"Your current savings rate is {savings_rate:.1%}. Consider targeting 15-20% of income.",
                "priority": "high"
            })
        else:
            recommendations.append({
                "category": "Savings",
                "title": "Excellent Savings Discipline",
                "description": f"Your savings rate of {savings_rate:.1%} is on track. Keep up the great work!",
                "priority": "low"
            })
    
    # Emergency fund recommendation
    monthly_expenses_coverage = current_savings / monthly_expenses if monthly_expenses > 0 else 0
    if monthly_expenses_coverage < 3:
        recommendations.append({
            "category": "Emergency Fund",
            "title": "Build Emergency Fund",
            "description": f"Build an emergency fund covering 3-6 months of expenses. You currently have {monthly_expenses_coverage:.1f} months covered.",
            "priority": "high"
        })
    
    return {
        "user_age": user_age,
        "risk_profile": profile[5],
        "recommendations": recommendations,
        "total_recommendations": len(recommendations),
        "generated_at": datetime.utcnow().isoformat()
    }

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    init_database()
    logger.info("Demo API started successfully")

@app.on_event("shutdown") 
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Demo API shutting down")

def main():
    """Main function to run the demo server"""
    print("🚀 Starting AI Financial Planning Demo Server")
    print("=" * 60)
    print(f"📊 Demo Features:")
    print(f"   ✅ FastAPI backend with auto-generated docs")
    print(f"   ✅ SQLite database (no PostgreSQL needed)")
    print(f"   ✅ User registration and JWT authentication")
    print(f"   ✅ Monte Carlo portfolio simulations")
    print(f"   ✅ Financial goal tracking")
    print(f"   ✅ Personalized recommendations")
    print(f"   ✅ CORS enabled for frontend integration")
    print()
    print(f"🌐 API Endpoints:")
    print(f"   📋 Interactive docs: http://localhost:8000/docs")
    print(f"   🏥 Health check: http://localhost:8000/health")
    print(f"   📊 Sample data: http://localhost:8000/sample-data")
    print(f"   🔐 Demo login: demo@example.com / demo123")
    print()
    print("🔥 Server starting on http://localhost:8000")
    print("=" * 60)
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

if __name__ == "__main__":
    main()