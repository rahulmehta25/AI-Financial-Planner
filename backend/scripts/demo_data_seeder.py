#!/usr/bin/env python3
"""
Demo Data Seeder for Financial Planning System
Automatically populates the database with realistic demo data for demonstrations.
"""

import os
import sys
import asyncio
import sqlite3
import json
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Dict, List, Any
import random
from dataclasses import dataclass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class DemoUser:
    """Demo user data structure"""
    email: str
    name: str
    age: int
    income: int
    savings: int
    risk_tolerance: str
    goals: List[str]

@dataclass
class DemoGoal:
    """Demo goal data structure"""
    name: str
    target_amount: int
    target_date: str
    priority: str
    category: str

class DemoDataSeeder:
    """Handles seeding of demo data into the database"""
    
    def __init__(self, db_path: str = "/app/data/demo_database.db"):
        self.db_path = db_path
        self.demo_users = self._generate_demo_users()
        self.demo_goals = self._generate_demo_goals()
        self.demo_transactions = []
        
    def _generate_demo_users(self) -> List[DemoUser]:
        """Generate realistic demo users"""
        return [
            DemoUser(
                email="demo@financialplanning.com",
                name="Alex Demo",
                age=35,
                income=75000,
                savings=50000,
                risk_tolerance="moderate",
                goals=["retirement", "house", "emergency_fund"]
            ),
            DemoUser(
                email="sarah.investor@example.com",
                name="Sarah Investor",
                age=28,
                income=85000,
                savings=25000,
                risk_tolerance="aggressive",
                goals=["house", "vacation", "investment"]
            ),
            DemoUser(
                email="john.conservative@example.com",
                name="John Conservative",
                age=45,
                income=95000,
                savings=150000,
                risk_tolerance="conservative",
                goals=["retirement", "education", "emergency_fund"]
            ),
            DemoUser(
                email="maria.entrepreneur@example.com",
                name="Maria Entrepreneur",
                age=32,
                income=60000,
                savings=15000,
                risk_tolerance="moderate",
                goals=["business", "house", "emergency_fund"]
            ),
            DemoUser(
                email="robert.retiree@example.com",
                name="Robert Retiree",
                age=55,
                income=120000,
                savings=300000,
                risk_tolerance="conservative",
                goals=["retirement", "healthcare", "legacy"]
            )
        ]
    
    def _generate_demo_goals(self) -> List[DemoGoal]:
        """Generate realistic demo goals"""
        return [
            DemoGoal(
                name="Emergency Fund",
                target_amount=25000,
                target_date="2025-12-31",
                priority="high",
                category="safety"
            ),
            DemoGoal(
                name="House Down Payment",
                target_amount=100000,
                target_date="2027-06-30",
                priority="high",
                category="housing"
            ),
            DemoGoal(
                name="Retirement Fund",
                target_amount=1000000,
                target_date="2055-12-31",
                priority="medium",
                category="retirement"
            ),
            DemoGoal(
                name="Vacation to Europe",
                target_amount=8000,
                target_date="2025-08-15",
                priority="low",
                category="lifestyle"
            ),
            DemoGoal(
                name="Children's Education",
                target_amount=200000,
                target_date="2040-09-01",
                priority="high",
                category="education"
            ),
            DemoGoal(
                name="New Car",
                target_amount=35000,
                target_date="2026-03-31",
                priority="medium",
                category="transportation"
            ),
            DemoGoal(
                name="Start a Business",
                target_amount=50000,
                target_date="2026-12-31",
                priority="medium",
                category="business"
            ),
            DemoGoal(
                name="Health Insurance Buffer",
                target_amount=15000,
                target_date="2025-06-30",
                priority="high",
                category="healthcare"
            )
        ]
    
    def _ensure_database_directory(self):
        """Ensure the database directory exists"""
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Database directory ensured: {db_dir}")
    
    def _create_demo_tables(self, conn: sqlite3.Connection):
        """Create demo tables if they don't exist"""
        
        # Users table
        conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            hashed_password TEXT NOT NULL,
            age INTEGER,
            income INTEGER,
            savings INTEGER,
            risk_tolerance TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Financial profiles table
        conn.execute("""
        CREATE TABLE IF NOT EXISTS financial_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            monthly_income DECIMAL(12,2),
            monthly_expenses DECIMAL(12,2),
            current_savings DECIMAL(12,2),
            debt_amount DECIMAL(12,2),
            risk_tolerance TEXT,
            investment_experience TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        """)
        
        # Goals table
        conn.execute("""
        CREATE TABLE IF NOT EXISTS goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            target_amount DECIMAL(12,2) NOT NULL,
            current_amount DECIMAL(12,2) DEFAULT 0,
            target_date DATE,
            priority TEXT,
            category TEXT,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        """)
        
        # Transactions table
        conn.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            goal_id INTEGER,
            amount DECIMAL(12,2) NOT NULL,
            transaction_type TEXT NOT NULL,
            description TEXT,
            category TEXT,
            date DATE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (goal_id) REFERENCES goals (id)
        )
        """)
        
        # Simulation results table
        conn.execute("""
        CREATE TABLE IF NOT EXISTS simulation_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            goal_id INTEGER,
            simulation_type TEXT NOT NULL,
            parameters TEXT,
            results TEXT,
            success_probability DECIMAL(5,2),
            expected_value DECIMAL(12,2),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (goal_id) REFERENCES goals (id)
        )
        """)
        
        # Demo status table
        conn.execute("""
        CREATE TABLE IF NOT EXISTS demo_status (
            id INTEGER PRIMARY KEY,
            initialized BOOLEAN DEFAULT FALSE,
            data_version TEXT DEFAULT '1.0.0',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        logger.info("Demo tables created successfully")
    
    def _hash_password(self, password: str) -> str:
        """Simple password hashing for demo purposes"""
        import hashlib
        return hashlib.sha256(password.encode()).hexdigest()
    
    def _insert_demo_users(self, conn: sqlite3.Connection):
        """Insert demo users into the database"""
        
        for user in self.demo_users:
            # Check if user already exists
            cursor = conn.execute("SELECT id FROM users WHERE email = ?", (user.email,))
            if cursor.fetchone():
                logger.info(f"User {user.email} already exists, skipping")
                continue
            
            # Insert user
            hashed_password = self._hash_password("demo123")
            cursor = conn.execute("""
            INSERT INTO users (email, name, hashed_password, age, income, savings, risk_tolerance)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (user.email, user.name, hashed_password, user.age, user.income, user.savings, user.risk_tolerance))
            
            user_id = cursor.lastrowid
            
            # Insert financial profile
            monthly_income = user.income / 12
            monthly_expenses = monthly_income * 0.7  # Assume 70% of income for expenses
            
            conn.execute("""
            INSERT INTO financial_profiles (
                user_id, monthly_income, monthly_expenses, current_savings, 
                debt_amount, risk_tolerance, investment_experience
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id, monthly_income, monthly_expenses, user.savings,
                random.randint(0, 50000), user.risk_tolerance, 
                random.choice(['beginner', 'intermediate', 'advanced'])
            ))
            
            logger.info(f"Inserted user: {user.name} ({user.email})")
    
    def _insert_demo_goals(self, conn: sqlite3.Connection):
        """Insert demo goals for users"""
        
        # Get all users
        cursor = conn.execute("SELECT id, email FROM users")
        users = cursor.fetchall()
        
        for user_id, email in users:
            # Assign random goals to each user
            user_goals = random.sample(self.demo_goals, k=random.randint(2, 4))
            
            for goal in user_goals:
                # Check if goal already exists for this user
                cursor = conn.execute(
                    "SELECT id FROM goals WHERE user_id = ? AND name = ?", 
                    (user_id, goal.name)
                )
                if cursor.fetchone():
                    continue
                
                # Adjust goal amounts based on user profile
                adjusted_amount = self._adjust_goal_amount(goal.target_amount, email)
                current_amount = random.randint(0, int(adjusted_amount * 0.3))
                
                conn.execute("""
                INSERT INTO goals (
                    user_id, name, target_amount, current_amount, 
                    target_date, priority, category
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    user_id, goal.name, adjusted_amount, current_amount,
                    goal.target_date, goal.priority, goal.category
                ))
                
            logger.info(f"Inserted {len(user_goals)} goals for user: {email}")
    
    def _adjust_goal_amount(self, base_amount: int, user_email: str) -> int:
        """Adjust goal amounts based on user profile"""
        if "conservative" in user_email:
            return int(base_amount * 1.2)  # Conservative users aim higher
        elif "entrepreneur" in user_email:
            return int(base_amount * 0.8)  # Entrepreneurs start smaller
        elif "retiree" in user_email:
            return int(base_amount * 1.5)  # Retirees have larger goals
        return base_amount
    
    def _generate_demo_transactions(self, conn: sqlite3.Connection):
        """Generate realistic demo transactions"""
        
        # Get all users and their goals
        cursor = conn.execute("""
        SELECT u.id, u.email, g.id as goal_id, g.name as goal_name, g.target_amount
        FROM users u
        LEFT JOIN goals g ON u.id = g.user_id
        """)
        user_goals = cursor.fetchall()
        
        # Generate transactions for the past 6 months
        start_date = datetime.now() - timedelta(days=180)
        
        for user_id, email, goal_id, goal_name, target_amount in user_goals:
            if not goal_id:  # Skip users without goals
                continue
                
            # Generate 10-30 transactions per user
            num_transactions = random.randint(10, 30)
            
            for _ in range(num_transactions):
                # Random transaction date
                days_ago = random.randint(1, 180)
                transaction_date = (datetime.now() - timedelta(days=days_ago)).date()
                
                # Random transaction amount (contribution to goal)
                amount = random.randint(100, 2000)
                
                # Transaction types and descriptions
                transaction_types = [
                    ("deposit", f"Monthly contribution to {goal_name}"),
                    ("transfer", f"Transfer to {goal_name}"),
                    ("investment", f"Investment towards {goal_name}"),
                    ("bonus", f"Bonus allocation to {goal_name}")
                ]
                
                transaction_type, description = random.choice(transaction_types)
                
                conn.execute("""
                INSERT INTO transactions (
                    user_id, goal_id, amount, transaction_type, 
                    description, category, date
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    user_id, goal_id, amount, transaction_type,
                    description, "savings", transaction_date
                ))
        
        logger.info("Generated demo transactions for all users")
    
    def _generate_simulation_results(self, conn: sqlite3.Connection):
        """Generate demo simulation results"""
        
        # Get all user-goal combinations
        cursor = conn.execute("""
        SELECT u.id as user_id, g.id as goal_id, g.name, g.target_amount
        FROM users u
        JOIN goals g ON u.id = g.user_id
        """)
        user_goals = cursor.fetchall()
        
        simulation_types = ["monte_carlo", "goal_projection", "risk_analysis"]
        
        for user_id, goal_id, goal_name, target_amount in user_goals:
            for sim_type in simulation_types:
                # Generate realistic simulation results
                success_probability = random.uniform(0.6, 0.95)
                expected_value = target_amount * random.uniform(0.8, 1.2)
                
                parameters = {
                    "simulation_type": sim_type,
                    "time_horizon": random.randint(5, 30),
                    "annual_return": random.uniform(0.05, 0.12),
                    "volatility": random.uniform(0.10, 0.25),
                    "goal_amount": target_amount
                }
                
                results = {
                    "success_probability": success_probability,
                    "expected_final_value": expected_value,
                    "percentiles": {
                        "10th": expected_value * 0.7,
                        "50th": expected_value,
                        "90th": expected_value * 1.3
                    },
                    "recommended_monthly_contribution": random.randint(200, 1500)
                }
                
                conn.execute("""
                INSERT INTO simulation_results (
                    user_id, goal_id, simulation_type, parameters, 
                    results, success_probability, expected_value
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    user_id, goal_id, sim_type, 
                    json.dumps(parameters), json.dumps(results),
                    success_probability, expected_value
                ))
        
        logger.info("Generated simulation results for all user-goal combinations")
    
    def _mark_demo_initialized(self, conn: sqlite3.Connection):
        """Mark the demo as initialized"""
        conn.execute("""
        INSERT OR REPLACE INTO demo_status (id, initialized, data_version, updated_at)
        VALUES (1, TRUE, '1.0.0', CURRENT_TIMESTAMP)
        """)
        logger.info("Demo marked as initialized")
    
    async def seed_demo_data(self) -> bool:
        """Main method to seed all demo data"""
        try:
            logger.info("Starting demo data seeding process...")
            
            # Ensure database directory exists
            self._ensure_database_directory()
            
            # Connect to SQLite database
            conn = sqlite3.connect(self.db_path)
            conn.execute("PRAGMA foreign_keys = ON")  # Enable foreign key constraints
            
            try:
                # Check if demo is already initialized
                cursor = conn.execute("SELECT initialized FROM demo_status WHERE id = 1")
                result = cursor.fetchone()
                if result and result[0]:
                    logger.info("Demo data already initialized, skipping...")
                    return True
                
                # Create tables
                self._create_demo_tables(conn)
                
                # Seed data
                self._insert_demo_users(conn)
                conn.commit()
                
                self._insert_demo_goals(conn)
                conn.commit()
                
                self._generate_demo_transactions(conn)
                conn.commit()
                
                self._generate_simulation_results(conn)
                conn.commit()
                
                # Mark as initialized
                self._mark_demo_initialized(conn)
                conn.commit()
                
                logger.info("Demo data seeding completed successfully!")
                return True
                
            except Exception as e:
                logger.error(f"Error during data seeding: {e}")
                conn.rollback()
                return False
                
            finally:
                conn.close()
                
        except Exception as e:
            logger.error(f"Failed to seed demo data: {e}")
            return False
    
    def get_demo_info(self) -> Dict[str, Any]:
        """Get information about the demo data"""
        return {
            "users_count": len(self.demo_users),
            "goals_count": len(self.demo_goals),
            "demo_credentials": {
                "email": "demo@financialplanning.com",
                "password": "demo123"
            },
            "database_path": self.db_path,
            "data_version": "1.0.0"
        }

async def main():
    """Main entry point for the demo data seeder"""
    logger.info("Financial Planning System - Demo Data Seeder")
    logger.info("=" * 50)
    
    # Get database path from environment or use default
    db_path = os.environ.get("DATABASE_URL", "sqlite:///./demo_database.db")
    if db_path.startswith("sqlite:///"):
        db_path = db_path.replace("sqlite:///", "")
    
    # Ensure absolute path
    if not os.path.isabs(db_path):
        db_path = os.path.join("/app/data", db_path)
    
    # Create seeder and run
    seeder = DemoDataSeeder(db_path)
    
    # Display demo info
    demo_info = seeder.get_demo_info()
    logger.info(f"Demo configuration:")
    logger.info(f"  Users: {demo_info['users_count']}")
    logger.info(f"  Goals: {demo_info['goals_count']}")
    logger.info(f"  Database: {demo_info['database_path']}")
    logger.info(f"  Demo login: {demo_info['demo_credentials']['email']}")
    
    # Seed data
    success = await seeder.seed_demo_data()
    
    if success:
        logger.info("✅ Demo data seeding completed successfully!")
        logger.info("The demo environment is ready for use.")
        sys.exit(0)
    else:
        logger.error("❌ Demo data seeding failed!")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())