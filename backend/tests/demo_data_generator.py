"""
Demo Data Generator for Financial Planning System

Generates realistic test data for demonstrations and comprehensive testing.
Creates diverse user scenarios, market conditions, and simulation parameters.

Usage:
python tests/demo_data_generator.py --scenario retirement
python tests/demo_data_generator.py --scenario comprehensive --users 10
"""

import asyncio
import json
import random
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Any, Optional
import argparse
from pathlib import Path

import asyncpg
from faker import Faker

from tests.factories import (
    UserFactory, FinancialProfileFactory, GoalFactory,
    InvestmentFactory, MarketDataFactory, SimulationResultFactory,
    create_complete_user_scenario, create_retirement_scenario
)

fake = Faker()


class DemoDataGenerator:
    """Generate comprehensive demo data for testing and demonstrations"""
    
    def __init__(self, db_url: str = None):
        self.db_url = db_url or "postgresql://financial_planning:financial_planning@localhost:5432/financial_planning"
        self.generated_data = {}
        
    async def connect_db(self):
        """Connect to the database"""
        if self.db_url.startswith("postgresql+asyncpg://"):
            self.db_url = self.db_url.replace("postgresql+asyncpg://", "postgresql://")
        
        self.conn = await asyncpg.connect(self.db_url)
        
    async def close_db(self):
        """Close database connection"""
        if hasattr(self, 'conn'):
            await self.conn.close()
    
    async def generate_user_personas(self, count: int = 10) -> List[Dict]:
        """Generate diverse user personas for testing"""
        print(f"🎭 Generating {count} user personas...")
        
        personas = []
        
        # Define persona templates
        persona_templates = [
            {
                "name": "Young Professional",
                "age_range": (25, 35),
                "income_range": (50000, 120000),
                "risk_tolerance": "moderate",
                "goals": ["emergency_fund", "house_down_payment", "retirement"],
                "debt_likely": True
            },
            {
                "name": "Mid-Career Family",
                "age_range": (35, 50),
                "income_range": (80000, 200000),
                "risk_tolerance": "moderate",
                "goals": ["retirement", "education", "house_down_payment"],
                "dependents": (1, 3)
            },
            {
                "name": "High Earner",
                "age_range": (40, 55),
                "income_range": (150000, 500000),
                "risk_tolerance": "aggressive",
                "goals": ["retirement", "investment", "luxury_purchase"],
                "investments_likely": True
            },
            {
                "name": "Pre-Retiree",
                "age_range": (55, 65),
                "income_range": (60000, 150000),
                "risk_tolerance": "conservative",
                "goals": ["retirement", "healthcare"],
                "savings_high": True
            },
            {
                "name": "Conservative Saver",
                "age_range": (30, 60),
                "income_range": (40000, 80000),
                "risk_tolerance": "conservative",
                "goals": ["emergency_fund", "retirement", "major_purchase"],
                "debt_low": True
            },
            {
                "name": "Tech Worker",
                "age_range": (25, 40),
                "income_range": (100000, 300000),
                "risk_tolerance": "aggressive",
                "goals": ["retirement", "investment", "travel"],
                "tech_savvy": True
            }
        ]
        
        for i in range(count):
            template = random.choice(persona_templates)
            
            # Generate basic user data
            age = random.randint(*template["age_range"])
            annual_income = random.randint(*template["income_range"])
            
            persona = {
                "id": f"demo_user_{i+1}",
                "template": template["name"],
                "email": f"demo.user.{i+1}@example.com",
                "full_name": fake.name(),
                "age": age,
                "annual_income": annual_income,
                "risk_tolerance": template["risk_tolerance"],
                "goals": template["goals"],
                
                # Financial details
                "monthly_expenses": int(annual_income * random.uniform(0.6, 0.8) / 12),
                "current_savings": self._calculate_savings(annual_income, age, template),
                "debt_amount": self._calculate_debt(annual_income, template),
                "dependents": template.get("dependents", (0, 2))[1] if isinstance(template.get("dependents"), tuple) else random.randint(0, 2),
                
                # Investment details
                "investment_timeline": 65 - age if age < 65 else 5,
                "investment_experience": self._determine_experience(template),
                
                # Additional attributes
                "employment_status": "employed",
                "marital_status": random.choice(["single", "married", "divorced"]),
                "phone_number": fake.phone_number(),
                "date_of_birth": fake.date_of_birth(minimum_age=age, maximum_age=age),
            }
            
            personas.append(persona)
            print(f"   👤 {persona['template']}: {persona['full_name']} (Age: {age}, Income: ${annual_income:,})")
        
        self.generated_data["personas"] = personas
        return personas
    
    def _calculate_savings(self, annual_income: int, age: int, template: Dict) -> int:
        """Calculate realistic savings based on income, age, and persona"""
        base_savings_rate = 0.1  # 10% base
        
        # Adjust for age (older people tend to have more savings)
        age_multiplier = min(age / 30, 2.0)
        
        # Adjust for persona type
        if template.get("savings_high"):
            persona_multiplier = 1.5
        elif template.get("debt_likely"):
            persona_multiplier = 0.5
        else:
            persona_multiplier = 1.0
        
        # Add some randomness
        random_factor = random.uniform(0.5, 2.0)
        
        savings = int(annual_income * base_savings_rate * age_multiplier * persona_multiplier * random_factor)
        return max(1000, min(savings, annual_income * 3))  # Between $1k and 3x annual income
    
    def _calculate_debt(self, annual_income: int, template: Dict) -> int:
        """Calculate realistic debt based on income and persona"""
        if template.get("debt_low"):
            debt_ratio = random.uniform(0, 0.1)
        elif template.get("debt_likely"):
            debt_ratio = random.uniform(0.2, 0.8)
        else:
            debt_ratio = random.uniform(0, 0.4)
        
        return int(annual_income * debt_ratio)
    
    def _determine_experience(self, template: Dict) -> str:
        """Determine investment experience based on persona"""
        if template.get("tech_savvy") or template.get("investments_likely"):
            return random.choice(["intermediate", "advanced"])
        elif template["risk_tolerance"] == "conservative":
            return "beginner"
        else:
            return random.choice(["beginner", "intermediate"])
    
    async def generate_market_scenarios(self, count: int = 5) -> List[Dict]:
        """Generate different market condition scenarios"""
        print(f"📈 Generating {count} market scenarios...")
        
        scenarios = [
            {
                "name": "Bull Market",
                "description": "Strong economic growth, rising markets",
                "expected_return": 0.10,
                "volatility": 0.15,
                "inflation_rate": 0.025,
                "probability": 0.3
            },
            {
                "name": "Bear Market",
                "description": "Economic downturn, declining markets",
                "expected_return": -0.05,
                "volatility": 0.25,
                "inflation_rate": 0.01,
                "probability": 0.15
            },
            {
                "name": "Normal Market",
                "description": "Steady economic conditions",
                "expected_return": 0.07,
                "volatility": 0.18,
                "inflation_rate": 0.025,
                "probability": 0.4
            },
            {
                "name": "High Inflation",
                "description": "Rising prices, economic uncertainty",
                "expected_return": 0.05,
                "volatility": 0.22,
                "inflation_rate": 0.06,
                "probability": 0.1
            },
            {
                "name": "Low Interest Rate",
                "description": "Accommodative monetary policy",
                "expected_return": 0.08,
                "volatility": 0.12,
                "inflation_rate": 0.015,
                "probability": 0.05
            }
        ]
        
        # Add variations for the requested count
        market_scenarios = scenarios[:count]
        if count > len(scenarios):
            for i in range(count - len(scenarios)):
                base_scenario = random.choice(scenarios)
                variation = base_scenario.copy()
                variation["name"] = f"{base_scenario['name']} Variant {i+1}"
                variation["expected_return"] *= random.uniform(0.8, 1.2)
                variation["volatility"] *= random.uniform(0.9, 1.1)
                market_scenarios.append(variation)
        
        for scenario in market_scenarios:
            print(f"   📊 {scenario['name']}: {scenario['expected_return']:.1%} return, {scenario['volatility']:.1%} volatility")
        
        self.generated_data["market_scenarios"] = market_scenarios
        return market_scenarios
    
    async def generate_goal_templates(self) -> List[Dict]:
        """Generate comprehensive goal templates"""
        print("🎯 Generating goal templates...")
        
        goal_templates = [
            {
                "name": "Emergency Fund",
                "category": "emergency",
                "priority": "high",
                "target_amount_formula": "monthly_expenses * 6",
                "target_timeline_months": 24,
                "description": "3-6 months of expenses for financial emergencies"
            },
            {
                "name": "Retirement Savings",
                "category": "retirement",
                "priority": "high",
                "target_amount_formula": "annual_income * 10",
                "target_timeline_years": "65 - age",
                "description": "Build wealth for retirement lifestyle"
            },
            {
                "name": "House Down Payment",
                "category": "major_purchase",
                "priority": "medium",
                "target_amount_range": (50000, 200000),
                "target_timeline_years": (3, 8),
                "description": "Save for home purchase down payment"
            },
            {
                "name": "Children's Education",
                "category": "education",
                "priority": "high",
                "target_amount_range": (50000, 200000),
                "target_timeline_years": (10, 18),
                "description": "Fund children's college education"
            },
            {
                "name": "Vacation Fund",
                "category": "lifestyle",
                "priority": "low",
                "target_amount_range": (5000, 20000),
                "target_timeline_years": (1, 3),
                "description": "Save for travel and experiences"
            },
            {
                "name": "Car Purchase",
                "category": "major_purchase",
                "priority": "medium",
                "target_amount_range": (20000, 60000),
                "target_timeline_years": (2, 5),
                "description": "Purchase reliable transportation"
            },
            {
                "name": "Business Investment",
                "category": "investment",
                "priority": "medium",
                "target_amount_range": (25000, 100000),
                "target_timeline_years": (2, 7),
                "description": "Start or invest in business venture"
            },
            {
                "name": "Healthcare Fund",
                "category": "healthcare",
                "priority": "high",
                "target_amount_range": (10000, 50000),
                "target_timeline_years": (1, 5),
                "description": "Prepare for healthcare expenses"
            }
        ]
        
        for template in goal_templates:
            print(f"   🎯 {template['name']} ({template['category']}): {template['priority']} priority")
        
        self.generated_data["goal_templates"] = goal_templates
        return goal_templates
    
    async def generate_simulation_parameters(self, count: int = 20) -> List[Dict]:
        """Generate diverse simulation parameter sets"""
        print(f"🎲 Generating {count} simulation parameter sets...")
        
        parameters = []
        
        for i in range(count):
            # Vary simulation parameters
            iterations = random.choice([10000, 25000, 50000, 100000])
            years = random.randint(5, 40)
            
            # Market parameters
            expected_return = random.uniform(0.04, 0.12)
            volatility = random.uniform(0.10, 0.30)
            inflation_rate = random.uniform(0.015, 0.06)
            
            # Portfolio allocation (simplified)
            stock_allocation = random.uniform(0.3, 0.9)
            bond_allocation = 1 - stock_allocation
            
            param_set = {
                "id": f"sim_params_{i+1}",
                "iterations": iterations,
                "time_horizon_years": years,
                "expected_return": round(expected_return, 4),
                "volatility": round(volatility, 4),
                "inflation_rate": round(inflation_rate, 4),
                "stock_allocation": round(stock_allocation, 2),
                "bond_allocation": round(bond_allocation, 2),
                "rebalancing_frequency": random.choice(["monthly", "quarterly", "annually"]),
                "tax_rate": random.uniform(0.15, 0.35),
                "fees": random.uniform(0.005, 0.02),
                "description": f"Simulation {i+1}: {years}yr horizon, {expected_return:.1%} return"
            }
            
            parameters.append(param_set)
            print(f"   🎲 Sim {i+1}: {years}yr, {expected_return:.1%} return, {iterations:,} iterations")
        
        self.generated_data["simulation_parameters"] = parameters
        return parameters
    
    async def generate_investment_portfolios(self, count: int = 5) -> List[Dict]:
        """Generate sample investment portfolios"""
        print(f"📊 Generating {count} investment portfolios...")
        
        # Common investment symbols with realistic data
        investments = [
            {"symbol": "AAPL", "name": "Apple Inc.", "type": "stock", "sector": "technology"},
            {"symbol": "MSFT", "name": "Microsoft Corp.", "type": "stock", "sector": "technology"},
            {"symbol": "GOOGL", "name": "Alphabet Inc.", "type": "stock", "sector": "technology"},
            {"symbol": "AMZN", "name": "Amazon.com Inc.", "type": "stock", "sector": "consumer"},
            {"symbol": "TSLA", "name": "Tesla Inc.", "type": "stock", "sector": "automotive"},
            {"symbol": "SPY", "name": "SPDR S&P 500 ETF", "type": "etf", "sector": "diversified"},
            {"symbol": "QQQ", "name": "Invesco QQQ Trust", "type": "etf", "sector": "technology"},
            {"symbol": "VTI", "name": "Vanguard Total Stock Market", "type": "etf", "sector": "diversified"},
            {"symbol": "BND", "name": "Vanguard Total Bond Market", "type": "etf", "sector": "bonds"},
            {"symbol": "VNQ", "name": "Vanguard Real Estate ETF", "type": "etf", "sector": "real_estate"}
        ]
        
        portfolio_templates = [
            {"name": "Conservative", "risk_level": "low", "stock_ratio": 0.3},
            {"name": "Moderate", "risk_level": "medium", "stock_ratio": 0.6},
            {"name": "Aggressive", "risk_level": "high", "stock_ratio": 0.9},
            {"name": "Growth", "risk_level": "high", "stock_ratio": 0.8},
            {"name": "Income", "risk_level": "low", "stock_ratio": 0.4}
        ]
        
        portfolios = []
        
        for i, template in enumerate(portfolio_templates[:count]):
            portfolio_value = random.randint(10000, 500000)
            num_holdings = random.randint(5, 12)
            
            holdings = []
            remaining_value = portfolio_value
            
            for j in range(num_holdings):
                investment = random.choice(investments)
                
                # Allocate portion of portfolio
                if j == num_holdings - 1:
                    holding_value = remaining_value
                else:
                    max_allocation = remaining_value * 0.3  # Max 30% in single holding
                    holding_value = random.randint(int(remaining_value * 0.05), int(max_allocation))
                
                quantity = holding_value / random.uniform(50, 500)  # Assume price between $50-500
                
                holdings.append({
                    "symbol": investment["symbol"],
                    "name": investment["name"],
                    "type": investment["type"],
                    "sector": investment["sector"],
                    "quantity": round(quantity, 4),
                    "value": holding_value,
                    "allocation_percent": round((holding_value / portfolio_value) * 100, 2)
                })
                
                remaining_value -= holding_value
                if remaining_value <= 0:
                    break
            
            portfolio = {
                "id": f"portfolio_{i+1}",
                "name": f"{template['name']} Portfolio",
                "risk_level": template["risk_level"],
                "total_value": portfolio_value,
                "holdings": holdings,
                "target_stock_allocation": template["stock_ratio"],
                "actual_stock_allocation": sum(h["allocation_percent"] for h in holdings if h["type"] in ["stock", "etf"]) / 100,
                "diversification_score": min(len(set(h["sector"] for h in holdings)) / 5, 1.0),
                "annual_dividend_yield": random.uniform(0.01, 0.04)
            }
            
            portfolios.append(portfolio)
            print(f"   📊 {portfolio['name']}: ${portfolio_value:,} ({len(holdings)} holdings)")
        
        self.generated_data["portfolios"] = portfolios
        return portfolios
    
    async def save_demo_data(self, output_file: str = "demo_data.json"):
        """Save all generated data to a file"""
        print(f"💾 Saving demo data to {output_file}...")
        
        # Add metadata
        self.generated_data["metadata"] = {
            "generated_at": datetime.now().isoformat(),
            "version": "1.0",
            "description": "Comprehensive demo data for Financial Planning System",
            "counts": {
                "personas": len(self.generated_data.get("personas", [])),
                "market_scenarios": len(self.generated_data.get("market_scenarios", [])),
                "goal_templates": len(self.generated_data.get("goal_templates", [])),
                "simulation_parameters": len(self.generated_data.get("simulation_parameters", [])),
                "portfolios": len(self.generated_data.get("portfolios", []))
            }
        }
        
        # Ensure output directory exists
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(self.generated_data, f, indent=2, default=str)
        
        print(f"   ✅ Demo data saved successfully")
        print(f"   📋 Generated: {self.generated_data['metadata']['counts']}")
    
    async def load_demo_data(self, input_file: str = "demo_data.json") -> Dict:
        """Load demo data from a file"""
        print(f"📁 Loading demo data from {input_file}...")
        
        try:
            with open(input_file, 'r') as f:
                self.generated_data = json.load(f)
            
            print(f"   ✅ Demo data loaded successfully")
            if "metadata" in self.generated_data:
                print(f"   📋 Loaded: {self.generated_data['metadata']['counts']}")
            
            return self.generated_data
            
        except FileNotFoundError:
            print(f"   ❌ File not found: {input_file}")
            return {}
        except json.JSONDecodeError as e:
            print(f"   ❌ Invalid JSON in file: {e}")
            return {}
    
    async def generate_complete_demo_dataset(self, 
                                           users: int = 10,
                                           market_scenarios: int = 5,
                                           simulations: int = 20,
                                           portfolios: int = 5) -> Dict:
        """Generate a complete demo dataset"""
        print("🚀 Generating complete demo dataset...")
        print("=" * 60)
        
        # Generate all components
        await self.generate_user_personas(users)
        await self.generate_market_scenarios(market_scenarios)
        await self.generate_goal_templates()
        await self.generate_simulation_parameters(simulations)
        await self.generate_investment_portfolios(portfolios)
        
        print("\n" + "=" * 60)
        print("✅ Complete demo dataset generated!")
        
        return self.generated_data


# CLI interface
async def main():
    parser = argparse.ArgumentParser(description="Generate demo data for Financial Planning System")
    parser.add_argument("--scenario", choices=["retirement", "comprehensive", "testing"], default="comprehensive",
                       help="Type of demo scenario to generate")
    parser.add_argument("--users", type=int, default=10, help="Number of user personas to generate")
    parser.add_argument("--output", default="tests/demo_data.json", help="Output file for demo data")
    parser.add_argument("--db-url", help="Database URL for direct data insertion")
    
    args = parser.parse_args()
    
    generator = DemoDataGenerator(args.db_url)
    
    try:
        if args.scenario == "retirement":
            print("🏖️  Generating retirement-focused demo data...")
            await generator.generate_user_personas(5)  # Focus on retirement users
            await generator.generate_market_scenarios(3)
            
        elif args.scenario == "testing":
            print("🧪 Generating testing-focused demo data...")
            await generator.generate_complete_demo_dataset(
                users=args.users,
                market_scenarios=10,
                simulations=50,
                portfolios=10
            )
            
        else:  # comprehensive
            print("🎯 Generating comprehensive demo data...")
            await generator.generate_complete_demo_dataset(
                users=args.users,
                market_scenarios=5,
                simulations=20,
                portfolios=5
            )
        
        # Save the data
        await generator.save_demo_data(args.output)
        
        print(f"\n🎉 Demo data generation complete!")
        print(f"📄 Data saved to: {args.output}")
        
    except Exception as e:
        print(f"❌ Error generating demo data: {e}")
        raise
    
    finally:
        if hasattr(generator, 'conn'):
            await generator.close_db()


if __name__ == "__main__":
    asyncio.run(main())