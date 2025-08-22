#!/usr/bin/env python3
"""
Financial Planning System - Demo Data Seeder
Comprehensive demo data generator for development and demonstration purposes

This script creates realistic demo data including:
- Demo users with different profiles
- Financial goals and scenarios
- Investment portfolios
- Transaction history
- Market data cache
- AI recommendations
"""

import asyncio
import os
import sys
import random
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Any, Optional
import json

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import text
    import bcrypt
    from faker import Faker
    import pandas as pd
    import numpy as np
except ImportError as e:
    print(f"❌ Missing required dependency: {e}")
    print("Please install requirements: pip install -r requirements.txt")
    sys.exit(1)

# Import application models
try:
    from app.database.models import User, FinancialProfile, Goal, Investment
    from app.database.models import SimulationResult, MarketDataCache
    from app.database.models import MLRecommendation, AuditLog
    from app.core.config import get_settings
except ImportError as e:
    print(f"❌ Cannot import application models: {e}")
    print("Make sure you're running from the project root directory")
    sys.exit(1)

# Configuration
fake = Faker()
settings = get_settings()

# Demo data configuration
DEMO_USERS_COUNT = 5
GOALS_PER_USER = 3
INVESTMENTS_PER_USER = 8
TRANSACTIONS_PER_USER = 50
SIMULATION_RESULTS_PER_USER = 2
RECOMMENDATIONS_PER_USER = 5

# Color codes for output
class Colors:
    BLUE = '\033[0;34m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[0;33m'
    RED = '\033[0;31m'
    NC = '\033[0m'  # No Color

def log_info(message: str):
    print(f"{Colors.BLUE}[INFO]{Colors.NC} {message}")

def log_success(message: str):
    print(f"{Colors.GREEN}[SUCCESS]{Colors.NC} {message}")

def log_warning(message: str):
    print(f"{Colors.YELLOW}[WARNING]{Colors.NC} {message}")

def log_error(message: str):
    print(f"{Colors.RED}[ERROR]{Colors.NC} {message}")

class DemoDataSeeder:
    """Comprehensive demo data seeder for financial planning system"""
    
    def __init__(self):
        self.engine = None
        self.session_factory = None
        self.created_users = []
        self.created_goals = []
        self.created_investments = []
        
        # Demo user templates
        self.user_templates = [
            {
                "email": "demo@financialplanning.com",
                "full_name": "Demo User",
                "age": 35,
                "income": 75000,
                "profile_type": "balanced"
            },
            {
                "email": "sarah.investor@example.com",
                "full_name": "Sarah Chen",
                "age": 28,
                "income": 95000,
                "profile_type": "aggressive"
            },
            {
                "email": "mike.conservative@example.com",
                "full_name": "Mike Johnson",
                "age": 45,
                "income": 120000,
                "profile_type": "conservative"
            },
            {
                "email": "emma.planner@example.com",
                "full_name": "Emma Rodriguez",
                "age": 32,
                "income": 85000,
                "profile_type": "growth"
            },
            {
                "email": "david.retiree@example.com",
                "full_name": "David Smith",
                "age": 58,
                "income": 110000,
                "profile_type": "income"
            }
        ]
        
        # Investment asset classes
        self.asset_classes = [
            {"symbol": "VTI", "name": "Vanguard Total Stock Market ETF", "type": "equity", "allocation": 0.4},
            {"symbol": "VXUS", "name": "Vanguard Total International Stock ETF", "type": "equity", "allocation": 0.2},
            {"symbol": "BND", "name": "Vanguard Total Bond Market ETF", "type": "bond", "allocation": 0.2},
            {"symbol": "VNQ", "name": "Vanguard Real Estate ETF", "type": "reit", "allocation": 0.1},
            {"symbol": "VTEB", "name": "Vanguard Tax-Exempt Bond ETF", "type": "bond", "allocation": 0.05},
            {"symbol": "VWO", "name": "Vanguard Emerging Markets ETF", "type": "equity", "allocation": 0.05},
        ]
        
        # Financial goals templates
        self.goal_templates = [
            {"name": "Emergency Fund", "target_amount": 30000, "priority": "high", "goal_type": "savings"},
            {"name": "House Down Payment", "target_amount": 100000, "priority": "high", "goal_type": "major_purchase"},
            {"name": "Retirement Savings", "target_amount": 1000000, "priority": "medium", "goal_type": "retirement"},
            {"name": "Vacation Fund", "target_amount": 15000, "priority": "low", "goal_type": "lifestyle"},
            {"name": "Children's Education", "target_amount": 200000, "priority": "high", "goal_type": "education"},
            {"name": "New Car", "target_amount": 35000, "priority": "medium", "goal_type": "major_purchase"},
        ]

    async def init_database(self):
        """Initialize database connection"""
        try:
            database_url = settings.DATABASE_URL
            if not database_url:
                raise ValueError("DATABASE_URL not configured")
            
            # Convert sync URL to async if needed
            if database_url.startswith("postgresql://"):
                database_url = database_url.replace("postgresql://", "postgresql+asyncpg://")
            elif not database_url.startswith("postgresql+asyncpg://"):
                database_url = f"postgresql+asyncpg://{database_url}"
            
            self.engine = create_async_engine(
                database_url,
                echo=False,
                pool_pre_ping=True,
                pool_size=5,
                max_overflow=10
            )
            
            self.session_factory = sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            log_success("Database connection initialized")
            
        except Exception as e:
            log_error(f"Failed to initialize database: {e}")
            raise

    async def clear_existing_demo_data(self):
        """Clear existing demo data"""
        log_info("Clearing existing demo data...")
        
        async with self.session_factory() as session:
            try:
                # Clear in reverse dependency order
                await session.execute(text("DELETE FROM audit_logs WHERE user_id IN (SELECT id FROM users WHERE email LIKE '%@example.com' OR email = 'demo@financialplanning.com')"))
                await session.execute(text("DELETE FROM ml_recommendations WHERE user_id IN (SELECT id FROM users WHERE email LIKE '%@example.com' OR email = 'demo@financialplanning.com')"))
                await session.execute(text("DELETE FROM simulation_results WHERE user_id IN (SELECT id FROM users WHERE email LIKE '%@example.com' OR email = 'demo@financialplanning.com')"))
                await session.execute(text("DELETE FROM investments WHERE user_id IN (SELECT id FROM users WHERE email LIKE '%@example.com' OR email = 'demo@financialplanning.com')"))
                await session.execute(text("DELETE FROM financial_goals WHERE user_id IN (SELECT id FROM users WHERE email LIKE '%@example.com' OR email = 'demo@financialplanning.com')"))
                await session.execute(text("DELETE FROM financial_profiles WHERE user_id IN (SELECT id FROM users WHERE email LIKE '%@example.com' OR email = 'demo@financialplanning.com')"))
                await session.execute(text("DELETE FROM users WHERE email LIKE '%@example.com' OR email = 'demo@financialplanning.com'"))
                
                await session.commit()
                log_success("Existing demo data cleared")
                
            except Exception as e:
                await session.rollback()
                log_warning(f"Failed to clear existing data: {e}")

    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    async def create_demo_users(self):
        """Create demo users with financial profiles"""
        log_info(f"Creating {len(self.user_templates)} demo users...")
        
        async with self.session_factory() as session:
            try:
                for template in self.user_templates:
                    # Create user
                    user_data = {
                        "id": str(uuid.uuid4()),
                        "email": template["email"],
                        "hashed_password": self.hash_password("demo123456"),  # Standard demo password
                        "full_name": template["full_name"],
                        "is_active": True,
                        "is_verified": True,
                        "created_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    }
                    
                    # Insert user
                    await session.execute(
                        text("""
                        INSERT INTO users (id, email, hashed_password, full_name, is_active, is_verified, created_at, updated_at)
                        VALUES (:id, :email, :hashed_password, :full_name, :is_active, :is_verified, :created_at, :updated_at)
                        """),
                        user_data
                    )
                    
                    # Create financial profile
                    profile_data = {
                        "id": str(uuid.uuid4()),
                        "user_id": user_data["id"],
                        "age": template["age"],
                        "annual_income": Decimal(str(template["income"])),
                        "risk_tolerance": template["profile_type"],
                        "investment_experience": random.choice(["beginner", "intermediate", "advanced"]),
                        "time_horizon": random.randint(5, 30),
                        "liquidity_needs": random.choice(["low", "medium", "high"]),
                        "financial_goals_summary": f"Building wealth through {template['profile_type']} investment strategy",
                        "created_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    }
                    
                    await session.execute(
                        text("""
                        INSERT INTO financial_profiles (id, user_id, age, annual_income, risk_tolerance, 
                                                      investment_experience, time_horizon, liquidity_needs, 
                                                      financial_goals_summary, created_at, updated_at)
                        VALUES (:id, :user_id, :age, :annual_income, :risk_tolerance, :investment_experience, 
                                :time_horizon, :liquidity_needs, :financial_goals_summary, :created_at, :updated_at)
                        """),
                        profile_data
                    )
                    
                    self.created_users.append({
                        "id": user_data["id"],
                        "email": user_data["email"],
                        "full_name": user_data["full_name"],
                        "profile_type": template["profile_type"]
                    })
                
                await session.commit()
                log_success(f"Created {len(self.user_templates)} demo users")
                
            except Exception as e:
                await session.rollback()
                log_error(f"Failed to create demo users: {e}")
                raise

    async def create_financial_goals(self):
        """Create financial goals for demo users"""
        log_info("Creating financial goals...")
        
        async with self.session_factory() as session:
            try:
                for user in self.created_users:
                    # Select goals based on user profile
                    selected_goals = random.sample(self.goal_templates, GOALS_PER_USER)
                    
                    for goal_template in selected_goals:
                        goal_data = {
                            "id": str(uuid.uuid4()),
                            "user_id": user["id"],
                            "name": goal_template["name"],
                            "description": f"{goal_template['name']} for {user['full_name']}",
                            "target_amount": Decimal(str(goal_template["target_amount"])),
                            "current_amount": Decimal(str(random.randint(0, goal_template["target_amount"] // 4))),
                            "target_date": datetime.utcnow() + timedelta(days=random.randint(365, 3650)),
                            "priority": goal_template["priority"],
                            "goal_type": goal_template["goal_type"],
                            "is_active": True,
                            "created_at": datetime.utcnow(),
                            "updated_at": datetime.utcnow()
                        }
                        
                        await session.execute(
                            text("""
                            INSERT INTO financial_goals (id, user_id, name, description, target_amount, 
                                                       current_amount, target_date, priority, goal_type, 
                                                       is_active, created_at, updated_at)
                            VALUES (:id, :user_id, :name, :description, :target_amount, :current_amount, 
                                    :target_date, :priority, :goal_type, :is_active, :created_at, :updated_at)
                            """),
                            goal_data
                        )
                        
                        self.created_goals.append(goal_data)
                
                await session.commit()
                log_success(f"Created {len(self.created_goals)} financial goals")
                
            except Exception as e:
                await session.rollback()
                log_error(f"Failed to create financial goals: {e}")
                raise

    async def create_investment_portfolios(self):
        """Create investment portfolios for demo users"""
        log_info("Creating investment portfolios...")
        
        async with self.session_factory() as session:
            try:
                for user in self.created_users:
                    # Create portfolio based on user risk profile
                    portfolio_value = random.randint(50000, 500000)
                    
                    for asset in self.asset_classes:
                        # Adjust allocation based on risk profile
                        base_allocation = asset["allocation"]
                        if user["profile_type"] == "conservative":
                            if asset["type"] == "bond":
                                allocation = base_allocation * 1.5
                            elif asset["type"] == "equity":
                                allocation = base_allocation * 0.8
                            else:
                                allocation = base_allocation
                        elif user["profile_type"] == "aggressive":
                            if asset["type"] == "equity":
                                allocation = base_allocation * 1.3
                            elif asset["type"] == "bond":
                                allocation = base_allocation * 0.6
                            else:
                                allocation = base_allocation
                        else:
                            allocation = base_allocation
                        
                        # Calculate investment details
                        market_value = Decimal(str(portfolio_value * allocation))
                        shares = random.randint(1, int(market_value / 100))
                        cost_basis = market_value * Decimal(str(random.uniform(0.8, 1.1)))
                        
                        investment_data = {
                            "id": str(uuid.uuid4()),
                            "user_id": user["id"],
                            "symbol": asset["symbol"],
                            "name": asset["name"],
                            "asset_type": asset["type"],
                            "shares": Decimal(str(shares)),
                            "cost_basis": cost_basis,
                            "current_price": market_value / Decimal(str(shares)) if shares > 0 else Decimal("100"),
                            "market_value": market_value,
                            "purchase_date": datetime.utcnow() - timedelta(days=random.randint(30, 1095)),
                            "is_active": True,
                            "created_at": datetime.utcnow(),
                            "updated_at": datetime.utcnow()
                        }
                        
                        await session.execute(
                            text("""
                            INSERT INTO investments (id, user_id, symbol, name, asset_type, shares, 
                                                   cost_basis, current_price, market_value, purchase_date, 
                                                   is_active, created_at, updated_at)
                            VALUES (:id, :user_id, :symbol, :name, :asset_type, :shares, :cost_basis, 
                                    :current_price, :market_value, :purchase_date, :is_active, :created_at, :updated_at)
                            """),
                            investment_data
                        )
                        
                        self.created_investments.append(investment_data)
                
                await session.commit()
                log_success(f"Created {len(self.created_investments)} investment holdings")
                
            except Exception as e:
                await session.rollback()
                log_error(f"Failed to create investment portfolios: {e}")
                raise

    async def create_simulation_results(self):
        """Create Monte Carlo simulation results"""
        log_info("Creating simulation results...")
        
        async with self.session_factory() as session:
            try:
                for user in self.created_users:
                    for i in range(SIMULATION_RESULTS_PER_USER):
                        # Generate realistic simulation data
                        scenarios = []
                        for percentile in [10, 25, 50, 75, 90]:
                            scenario_values = []
                            base_value = 100000
                            for year in range(1, 31):  # 30-year projection
                                if user["profile_type"] == "conservative":
                                    annual_return = random.gauss(0.06, 0.08)
                                elif user["profile_type"] == "aggressive":
                                    annual_return = random.gauss(0.10, 0.15)
                                else:
                                    annual_return = random.gauss(0.08, 0.12)
                                
                                base_value *= (1 + annual_return)
                                scenario_values.append(round(base_value, 2))
                            
                            scenarios.append({
                                "percentile": percentile,
                                "values": scenario_values
                            })
                        
                        simulation_data = {
                            "id": str(uuid.uuid4()),
                            "user_id": user["id"],
                            "simulation_type": "monte_carlo",
                            "parameters": json.dumps({
                                "initial_investment": 100000,
                                "monthly_contribution": 1000,
                                "time_horizon": 30,
                                "iterations": 10000,
                                "risk_profile": user["profile_type"]
                            }),
                            "results": json.dumps({
                                "scenarios": scenarios,
                                "statistics": {
                                    "mean_final_value": scenarios[2]["values"][-1],  # 50th percentile final value
                                    "probability_of_success": random.uniform(0.7, 0.95),
                                    "worst_case_value": scenarios[0]["values"][-1],  # 10th percentile
                                    "best_case_value": scenarios[4]["values"][-1]   # 90th percentile
                                }
                            }),
                            "confidence_level": Decimal(str(random.uniform(0.8, 0.95))),
                            "success_probability": Decimal(str(random.uniform(0.7, 0.9))),
                            "created_at": datetime.utcnow() - timedelta(days=random.randint(1, 30)),
                            "updated_at": datetime.utcnow()
                        }
                        
                        await session.execute(
                            text("""
                            INSERT INTO simulation_results (id, user_id, simulation_type, parameters, results, 
                                                          confidence_level, success_probability, created_at, updated_at)
                            VALUES (:id, :user_id, :simulation_type, :parameters, :results, :confidence_level, 
                                    :success_probability, :created_at, :updated_at)
                            """),
                            simulation_data
                        )
                
                await session.commit()
                log_success(f"Created {len(self.created_users) * SIMULATION_RESULTS_PER_USER} simulation results")
                
            except Exception as e:
                await session.rollback()
                log_error(f"Failed to create simulation results: {e}")
                raise

    async def create_ai_recommendations(self):
        """Create AI-powered recommendations"""
        log_info("Creating AI recommendations...")
        
        recommendation_templates = [
            {
                "type": "portfolio_rebalancing",
                "title": "Portfolio Rebalancing Opportunity",
                "description": "Your portfolio has drifted from target allocation. Consider rebalancing to maintain risk profile.",
                "priority": "medium"
            },
            {
                "type": "tax_optimization",
                "title": "Tax-Loss Harvesting Opportunity",
                "description": "You may benefit from tax-loss harvesting in your taxable accounts.",
                "priority": "high"
            },
            {
                "type": "goal_adjustment",
                "title": "Goal Timeline Adjustment",
                "description": "Based on current savings rate, consider adjusting your retirement goal timeline.",
                "priority": "medium"
            },
            {
                "type": "emergency_fund",
                "title": "Emergency Fund Review",
                "description": "Your emergency fund is below recommended levels. Consider increasing contributions.",
                "priority": "high"
            },
            {
                "type": "diversification",
                "title": "Diversification Enhancement",
                "description": "Adding international exposure could improve your portfolio's risk-adjusted returns.",
                "priority": "low"
            }
        ]
        
        async with self.session_factory() as session:
            try:
                for user in self.created_users:
                    selected_recs = random.sample(recommendation_templates, min(RECOMMENDATIONS_PER_USER, len(recommendation_templates)))
                    
                    for rec_template in selected_recs:
                        recommendation_data = {
                            "id": str(uuid.uuid4()),
                            "user_id": user["id"],
                            "recommendation_type": rec_template["type"],
                            "title": rec_template["title"],
                            "description": rec_template["description"],
                            "priority": rec_template["priority"],
                            "confidence_score": Decimal(str(random.uniform(0.7, 0.95))),
                            "is_active": True,
                            "is_applied": random.choice([True, False]),
                            "metadata": json.dumps({
                                "model_version": "1.0",
                                "generated_by": "ai_recommendation_engine",
                                "factors": ["portfolio_analysis", "goal_tracking", "market_conditions"]
                            }),
                            "created_at": datetime.utcnow() - timedelta(days=random.randint(1, 14)),
                            "updated_at": datetime.utcnow()
                        }
                        
                        await session.execute(
                            text("""
                            INSERT INTO ml_recommendations (id, user_id, recommendation_type, title, description, 
                                                          priority, confidence_score, is_active, is_applied, 
                                                          metadata, created_at, updated_at)
                            VALUES (:id, :user_id, :recommendation_type, :title, :description, :priority, 
                                    :confidence_score, :is_active, :is_applied, :metadata, :created_at, :updated_at)
                            """),
                            recommendation_data
                        )
                
                await session.commit()
                log_success(f"Created {len(self.created_users) * len(selected_recs)} AI recommendations")
                
            except Exception as e:
                await session.rollback()
                log_error(f"Failed to create AI recommendations: {e}")
                raise

    async def create_market_data_cache(self):
        """Create market data cache entries"""
        log_info("Creating market data cache...")
        
        async with self.session_factory() as session:
            try:
                for asset in self.asset_classes:
                    # Generate realistic price history
                    base_price = random.uniform(50, 300)
                    price_data = []
                    
                    for days_ago in range(30, 0, -1):
                        date = datetime.utcnow() - timedelta(days=days_ago)
                        # Simulate price movement
                        daily_change = random.gauss(0, 0.02)  # 2% daily volatility
                        base_price *= (1 + daily_change)
                        price_data.append({
                            "date": date.isoformat(),
                            "price": round(base_price, 2),
                            "volume": random.randint(1000000, 50000000)
                        })
                    
                    cache_data = {
                        "id": str(uuid.uuid4()),
                        "symbol": asset["symbol"],
                        "data_type": "daily_prices",
                        "data": json.dumps({
                            "prices": price_data,
                            "current_price": price_data[-1]["price"],
                            "change_24h": price_data[-1]["price"] - price_data[-2]["price"],
                            "change_percent_24h": ((price_data[-1]["price"] / price_data[-2]["price"]) - 1) * 100
                        }),
                        "source": "demo_data_generator",
                        "expires_at": datetime.utcnow() + timedelta(hours=24),
                        "created_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    }
                    
                    await session.execute(
                        text("""
                        INSERT INTO market_data_cache (id, symbol, data_type, data, source, expires_at, created_at, updated_at)
                        VALUES (:id, :symbol, :data_type, :data, :source, :expires_at, :created_at, :updated_at)
                        """),
                        cache_data
                    )
                
                await session.commit()
                log_success(f"Created market data cache for {len(self.asset_classes)} assets")
                
            except Exception as e:
                await session.rollback()
                log_error(f"Failed to create market data cache: {e}")
                raise

    async def create_audit_logs(self):
        """Create audit logs for demo activities"""
        log_info("Creating audit logs...")
        
        actions = [
            "user_login", "portfolio_view", "goal_created", "simulation_run",
            "recommendation_viewed", "investment_added", "profile_updated"
        ]
        
        async with self.session_factory() as session:
            try:
                for user in self.created_users:
                    for _ in range(random.randint(10, 25)):
                        action = random.choice(actions)
                        
                        audit_data = {
                            "id": str(uuid.uuid4()),
                            "user_id": user["id"],
                            "action": action,
                            "resource_type": action.split("_")[0],
                            "resource_id": str(uuid.uuid4()),
                            "ip_address": fake.ipv4(),
                            "user_agent": fake.user_agent(),
                            "metadata": json.dumps({
                                "success": True,
                                "duration_ms": random.randint(100, 2000),
                                "source": "web_app"
                            }),
                            "created_at": datetime.utcnow() - timedelta(days=random.randint(1, 30))
                        }
                        
                        await session.execute(
                            text("""
                            INSERT INTO audit_logs (id, user_id, action, resource_type, resource_id, 
                                                  ip_address, user_agent, metadata, created_at)
                            VALUES (:id, :user_id, :action, :resource_type, :resource_id, :ip_address, 
                                    :user_agent, :metadata, :created_at)
                            """),
                            audit_data
                        )
                
                await session.commit()
                log_success(f"Created audit logs for demo activities")
                
            except Exception as e:
                await session.rollback()
                log_error(f"Failed to create audit logs: {e}")
                raise

    async def verify_demo_data(self):
        """Verify that demo data was created successfully"""
        log_info("Verifying demo data creation...")
        
        async with self.session_factory() as session:
            try:
                # Count created records
                counts = {}
                
                result = await session.execute(text("SELECT COUNT(*) FROM users WHERE email LIKE '%@example.com' OR email = 'demo@financialplanning.com'"))
                counts['users'] = result.scalar()
                
                result = await session.execute(text("SELECT COUNT(*) FROM financial_goals WHERE user_id IN (SELECT id FROM users WHERE email LIKE '%@example.com' OR email = 'demo@financialplanning.com')"))
                counts['goals'] = result.scalar()
                
                result = await session.execute(text("SELECT COUNT(*) FROM investments WHERE user_id IN (SELECT id FROM users WHERE email LIKE '%@example.com' OR email = 'demo@financialplanning.com')"))
                counts['investments'] = result.scalar()
                
                result = await session.execute(text("SELECT COUNT(*) FROM simulation_results WHERE user_id IN (SELECT id FROM users WHERE email LIKE '%@example.com' OR email = 'demo@financialplanning.com')"))
                counts['simulations'] = result.scalar()
                
                result = await session.execute(text("SELECT COUNT(*) FROM ml_recommendations WHERE user_id IN (SELECT id FROM users WHERE email LIKE '%@example.com' OR email = 'demo@financialplanning.com')"))
                counts['recommendations'] = result.scalar()
                
                result = await session.execute(text("SELECT COUNT(*) FROM market_data_cache"))
                counts['market_data'] = result.scalar()
                
                log_success("Demo data verification complete:")
                for entity, count in counts.items():
                    print(f"  • {entity.title()}: {count}")
                
                return all(count > 0 for count in counts.values())
                
            except Exception as e:
                log_error(f"Failed to verify demo data: {e}")
                return False

    async def close_database(self):
        """Close database connections"""
        if self.engine:
            await self.engine.dispose()
            log_info("Database connections closed")

    async def run_seeding(self):
        """Run the complete demo data seeding process"""
        try:
            print("=" * 70)
            print("🌱 Financial Planning System - Demo Data Seeder")
            print("=" * 70)
            
            await self.init_database()
            await self.clear_existing_demo_data()
            await self.create_demo_users()
            await self.create_financial_goals()
            await self.create_investment_portfolios()
            await self.create_simulation_results()
            await self.create_ai_recommendations()
            await self.create_market_data_cache()
            await self.create_audit_logs()
            
            if await self.verify_demo_data():
                print("\n" + "=" * 70)
                print("🎉 Demo Data Seeding Completed Successfully!")
                print("=" * 70)
                print("\n📋 Demo Accounts Created:")
                for user in self.created_users:
                    print(f"  • {user['full_name']} ({user['email']}) - {user['profile_type']}")
                
                print("\n🔐 Demo Credentials:")
                print("  • Password for all accounts: demo123456")
                
                print("\n🚀 You can now:")
                print("  • Login to any demo account")
                print("  • Explore financial goals and portfolios")
                print("  • Run Monte Carlo simulations")
                print("  • View AI recommendations")
                print("  • Test all system features")
                print("\n" + "=" * 70)
                
                return True
            else:
                log_error("Demo data verification failed")
                return False
                
        except Exception as e:
            log_error(f"Demo data seeding failed: {e}")
            return False
        finally:
            await self.close_database()

async def main():
    """Main entry point"""
    seeder = DemoDataSeeder()
    success = await seeder.run_seeding()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log_warning("Demo data seeding interrupted by user")
        sys.exit(1)
    except Exception as e:
        log_error(f"Unexpected error: {e}")
        sys.exit(1)