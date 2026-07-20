"""
Demo Test Data Generator
========================

This module generates realistic test data for the API demo test suite.
Includes various financial scenarios and edge cases.
"""

import random
from datetime import datetime, timedelta
from typing import Dict, List, Any
from decimal import Decimal

class TestDataGenerator:
    """Generates realistic test data for financial planning scenarios"""
    
    def __init__(self, seed: int = 42):
        """Initialize with optional seed for reproducible results"""
        random.seed(seed)
        
        # Common data pools
        self.first_names = [
            "John", "Jane", "Michael", "Sarah", "David", "Emily", "Robert", "Jessica",
            "William", "Ashley", "James", "Amanda", "Christopher", "Stephanie", "Daniel",
            "Jennifer", "Matthew", "Lisa", "Anthony", "Michelle", "Mark", "Kimberly"
        ]
        
        self.last_names = [
            "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
            "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
            "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson"
        ]
        
        self.risk_preferences = ["conservative", "balanced", "aggressive"]
        self.marital_statuses = ["single", "married"]
        
    def generate_user_data(self) -> Dict[str, Any]:
        """Generate realistic user registration data"""
        first_name = random.choice(self.first_names)
        last_name = random.choice(self.last_names)
        
        return {
            "email": f"{first_name.lower()}.{last_name.lower()}@example.com",
            "password": "TestPassword123!",
            "full_name": f"{first_name} {last_name}",
            "first_name": first_name,
            "last_name": last_name
        }
    
    def generate_financial_profile(self, age: int = None) -> Dict[str, Any]:
        """Generate realistic financial profile data"""
        age = age or random.randint(25, 60)
        
        # Base income on age and add some variation
        base_income = 40000 + (age - 25) * 1500 + random.randint(-15000, 25000)
        base_income = max(30000, base_income)  # Minimum income
        
        # Savings rate typically increases with age/income
        savings_rate = min(25.0, 5.0 + (age - 25) * 0.5 + random.uniform(-3, 7))
        savings_rate = max(0.0, savings_rate)
        
        # Current savings based on age and income
        years_working = max(1, age - 22)
        annual_savings = base_income * (savings_rate / 100)
        current_savings = annual_savings * years_working * random.uniform(0.6, 1.4)
        current_savings = max(0, current_savings)
        
        # Debt decreases with age typically
        debt_probability = max(0.2, 0.8 - (age - 25) * 0.02)
        debt_balance = 0
        debt_interest_rate = 0
        
        if random.random() < debt_probability:
            debt_balance = random.uniform(5000, min(100000, base_income * 1.5))
            debt_interest_rate = random.uniform(3.5, 18.5)
        
        return {
            "age": age,
            "target_retirement_age": random.randint(62, 70),
            "marital_status": random.choice(self.marital_statuses),
            "current_savings_balance": round(current_savings, 2),
            "annual_savings_rate_percentage": round(savings_rate, 1),
            "income_level": round(base_income, 2),
            "debt_balance": round(debt_balance, 2),
            "debt_interest_rate_percentage": round(debt_interest_rate, 1),
            "account_buckets_taxable": round(random.uniform(20, 50), 1),
            "account_buckets_401k_ira": round(random.uniform(25, 45), 1),
            "account_buckets_roth": 0,  # Will be calculated to sum to 100
            "risk_preference": random.choice(self.risk_preferences),
            "desired_retirement_spending_per_year": round(base_income * random.uniform(0.6, 0.9), 2),
            "plan_name": f"Financial Plan {random.randint(1, 1000)}",
            "notes": "Generated test data for API demonstration"
        }
    
    def fix_account_buckets(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure account buckets sum to 100%"""
        taxable = profile["account_buckets_taxable"]
        k401_ira = profile["account_buckets_401k_ira"]
        roth = 100.0 - taxable - k401_ira
        
        # Ensure Roth is non-negative
        if roth < 0:
            # Adjust the other buckets proportionally
            total = taxable + k401_ira
            taxable = (taxable / total) * 90
            k401_ira = (k401_ira / total) * 90
            roth = 10.0
        
        profile["account_buckets_taxable"] = round(taxable, 1)
        profile["account_buckets_401k_ira"] = round(k401_ira, 1)
        profile["account_buckets_roth"] = round(roth, 1)
        
        return profile
    
    def generate_monte_carlo_request(self) -> Dict[str, Any]:
        """Generate Monte Carlo simulation request data"""
        return {
            "initial_investment": round(random.uniform(10000, 500000), 2),
            "monthly_contribution": round(random.uniform(500, 5000), 2),
            "years_to_retirement": random.randint(10, 40),
            "expected_return": round(random.uniform(0.04, 0.12), 4),
            "volatility": round(random.uniform(0.08, 0.20), 4),
            "simulations_count": random.choice([1000, 5000, 10000]),
            "retirement_spending": round(random.uniform(40000, 120000), 2)
        }
    
    def generate_simulation_request(self) -> Dict[str, Any]:
        """Generate general simulation request data"""
        profile = self.generate_financial_profile()
        profile = self.fix_account_buckets(profile)
        
        return {
            "name": f"Test Simulation {random.randint(1, 10000)}",
            "description": "Automated test simulation for API validation",
            "parameters": profile,
            "simulation_type": random.choice(["monte_carlo", "scenario_analysis", "basic"])
        }
    
    def generate_goal_data(self) -> Dict[str, Any]:
        """Generate financial goal data"""
        goal_types = ["retirement", "house_purchase", "education", "emergency_fund", "vacation"]
        goal_type = random.choice(goal_types)
        
        # Goal amounts vary by type
        amount_ranges = {
            "retirement": (500000, 2000000),
            "house_purchase": (200000, 800000),
            "education": (50000, 200000),
            "emergency_fund": (10000, 50000),
            "vacation": (5000, 25000)
        }
        
        min_amount, max_amount = amount_ranges[goal_type]
        target_amount = round(random.uniform(min_amount, max_amount), 2)
        
        # Time horizon varies by goal type
        time_ranges = {
            "retirement": (10, 40),
            "house_purchase": (2, 10),
            "education": (5, 18),
            "emergency_fund": (1, 3),
            "vacation": (1, 5)
        }
        
        min_years, max_years = time_ranges[goal_type]
        target_date = datetime.now() + timedelta(days=random.randint(min_years*365, max_years*365))
        
        return {
            "name": f"{goal_type.replace('_', ' ').title()} Goal",
            "description": f"Save for {goal_type.replace('_', ' ')}",
            "target_amount": target_amount,
            "current_amount": round(target_amount * random.uniform(0, 0.3), 2),
            "target_date": target_date.isoformat(),
            "priority": random.choice(["high", "medium", "low"]),
            "goal_type": goal_type
        }
    
    def generate_investment_data(self) -> Dict[str, Any]:
        """Generate investment portfolio data"""
        symbols = ["VTI", "VTIAX", "BND", "VBTLX", "VEA", "VWO", "VMOT", "VTEB"]
        
        return {
            "symbol": random.choice(symbols),
            "name": f"Investment {random.randint(1, 1000)}",
            "investment_type": random.choice(["stock", "bond", "etf", "mutual_fund"]),
            "amount": round(random.uniform(1000, 50000), 2),
            "shares": round(random.uniform(10, 1000), 2),
            "purchase_price": round(random.uniform(20, 500), 2),
            "purchase_date": (datetime.now() - timedelta(days=random.randint(1, 1825))).isoformat()
        }
    
    def generate_edge_case_scenarios(self) -> List[Dict[str, Any]]:
        """Generate edge case scenarios for testing"""
        scenarios = []
        
        # Very young person
        young_profile = self.generate_financial_profile(age=22)
        young_profile["target_retirement_age"] = 65
        young_profile["current_savings_balance"] = 1000
        young_profile["income_level"] = 35000
        scenarios.append(self.fix_account_buckets(young_profile))
        
        # Near retirement
        near_retirement = self.generate_financial_profile(age=62)
        near_retirement["target_retirement_age"] = 65
        near_retirement["current_savings_balance"] = 800000
        near_retirement["income_level"] = 95000
        scenarios.append(self.fix_account_buckets(near_retirement))
        
        # High earner
        high_earner = self.generate_financial_profile(age=45)
        high_earner["income_level"] = 250000
        high_earner["current_savings_balance"] = 1500000
        high_earner["annual_savings_rate_percentage"] = 20.0
        scenarios.append(self.fix_account_buckets(high_earner))
        
        # High debt scenario
        high_debt = self.generate_financial_profile(age=35)
        high_debt["debt_balance"] = high_debt["income_level"] * 2
        high_debt["debt_interest_rate_percentage"] = 15.5
        high_debt["current_savings_balance"] = 5000
        scenarios.append(self.fix_account_buckets(high_debt))
        
        # Conservative investor
        conservative = self.generate_financial_profile(age=55)
        conservative["risk_preference"] = "conservative"
        conservative["account_buckets_taxable"] = 60.0
        conservative["account_buckets_401k_ira"] = 30.0
        conservative["account_buckets_roth"] = 10.0
        scenarios.append(conservative)
        
        return scenarios
    
    def get_test_dataset(self, count: int = 10) -> Dict[str, List[Dict]]:
        """Generate a complete test dataset"""
        return {
            "users": [self.generate_user_data() for _ in range(count)],
            "financial_profiles": [self.fix_account_buckets(self.generate_financial_profile()) for _ in range(count)],
            "monte_carlo_requests": [self.generate_monte_carlo_request() for _ in range(count)],
            "simulation_requests": [self.generate_simulation_request() for _ in range(count)],
            "goals": [self.generate_goal_data() for _ in range(count)],
            "investments": [self.generate_investment_data() for _ in range(count)],
            "edge_cases": self.generate_edge_case_scenarios()
        }


def main():
    """Generate and display sample test data"""
    generator = TestDataGenerator()
    
    print("🎲 Demo Test Data Generator")
    print("=" * 50)
    
    # Generate sample data
    dataset = generator.get_test_dataset(count=3)
    
    print("\n👤 Sample User Data:")
    for i, user in enumerate(dataset["users"], 1):
        print(f"  {i}. {user['full_name']} <{user['email']}>")
    
    print("\n💰 Sample Financial Profiles:")
    for i, profile in enumerate(dataset["financial_profiles"], 1):
        print(f"  {i}. Age: {profile['age']}, Income: ${profile['income_level']:,.0f}, "
              f"Savings: ${profile['current_savings_balance']:,.0f}")
    
    print("\n🎯 Sample Goals:")
    for i, goal in enumerate(dataset["goals"], 1):
        print(f"  {i}. {goal['name']}: ${goal['target_amount']:,.0f}")
    
    print("\n🧪 Edge Case Scenarios:")
    for i, scenario in enumerate(dataset["edge_cases"], 1):
        print(f"  {i}. Age: {scenario['age']}, Income: ${scenario['income_level']:,.0f}, "
              f"Savings: ${scenario['current_savings_balance']:,.0f}, "
              f"Risk: {scenario['risk_preference']}")
    
    # Save to JSON file
    import json
    with open("demo_test_data.json", "w") as f:
        json.dump(dataset, f, indent=2, default=str)
    
    print(f"\n📁 Test data saved to: demo_test_data.json")


if __name__ == "__main__":
    main()