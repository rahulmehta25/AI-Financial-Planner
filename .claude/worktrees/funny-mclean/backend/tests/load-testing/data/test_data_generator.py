"""
Test Data Generator for Load Testing

Generates realistic test data for various user profiles and scenarios
"""

import random
import string
import json
import csv
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import faker
import numpy as np
from pathlib import Path


fake = faker.Faker()


@dataclass
class TestUser:
    """Test user profile"""
    user_id: str
    email: str
    password: str
    first_name: str
    last_name: str
    age: int
    income: float
    net_worth: float
    risk_tolerance: str
    investment_experience: str
    employment_status: str
    marital_status: str
    dependents: int
    phone: str
    address: Dict[str, str]
    created_at: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


@dataclass
class FinancialGoal:
    """Financial goal for test users"""
    goal_id: str
    user_id: str
    name: str
    category: str
    target_amount: float
    current_amount: float
    target_date: str
    priority: str
    monthly_contribution: float
    auto_invest: bool
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


@dataclass
class Investment:
    """Investment holding for test users"""
    investment_id: str
    user_id: str
    symbol: str
    name: str
    asset_class: str
    quantity: float
    purchase_price: float
    current_price: float
    purchase_date: str
    account_type: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


@dataclass
class Transaction:
    """Financial transaction for test users"""
    transaction_id: str
    user_id: str
    date: str
    description: str
    category: str
    amount: float
    transaction_type: str  # income, expense, transfer
    account: str
    merchant: str
    tags: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


class TestDataGenerator:
    """Generate realistic test data for load testing"""
    
    def __init__(self, seed: int = 42):
        """
        Initialize test data generator
        
        Args:
            seed: Random seed for reproducibility
        """
        random.seed(seed)
        np.random.seed(seed)
        faker.Faker.seed(seed)
        
        self.fake = faker.Faker()
        
        # Stock symbols for investments
        self.stock_symbols = [
            "AAPL", "GOOGL", "MSFT", "AMZN", "META", "TSLA", "NVDA", "JPM",
            "V", "JNJ", "WMT", "PG", "MA", "UNH", "DIS", "HD", "BAC", "VZ",
            "ADBE", "NFLX", "CRM", "PFE", "TMO", "CMCSA", "KO", "PEP", "ABT",
            "NKE", "COST", "CVX", "WFC", "LLY", "AVGO", "MCD", "ABBV", "TXN"
        ]
        
        # ETF symbols
        self.etf_symbols = [
            "SPY", "VOO", "IVV", "QQQ", "VTI", "VEA", "EFA", "AGG", "BND",
            "VNQ", "GLD", "IWM", "VB", "VWO", "IEMG", "VIG", "VYM", "SCHD"
        ]
        
        # Transaction categories
        self.expense_categories = [
            "Housing", "Transportation", "Food", "Utilities", "Healthcare",
            "Insurance", "Shopping", "Entertainment", "Education", "Personal",
            "Travel", "Gifts", "Fees", "Taxes", "Other"
        ]
        
        self.income_categories = [
            "Salary", "Bonus", "Investment", "Rental", "Business", "Freelance",
            "Dividend", "Interest", "Capital Gains", "Other"
        ]
        
        # Goal categories
        self.goal_categories = [
            "retirement", "house", "education", "vacation", "emergency_fund",
            "car", "wedding", "debt_payoff", "investment", "business", "other"
        ]
        
        # Common merchants
        self.merchants = [
            "Amazon", "Walmart", "Target", "Costco", "Whole Foods", "Starbucks",
            "McDonald's", "Uber", "Lyft", "Shell", "Chevron", "AT&T", "Verizon",
            "Netflix", "Spotify", "Apple", "Google", "Microsoft", "Best Buy"
        ]
    
    def generate_user(self, profile_type: str = "moderate") -> TestUser:
        """
        Generate a test user with realistic profile
        
        Args:
            profile_type: Type of user profile
            
        Returns:
            Test user object
        """
        # Age based on profile
        age_ranges = {
            "young": (22, 35),
            "moderate": (35, 50),
            "mature": (50, 65),
            "senior": (65, 80)
        }
        
        age_range = age_ranges.get(profile_type, (25, 65))
        age = random.randint(*age_range)
        
        # Income correlates with age
        base_income = random.uniform(30000, 80000)
        age_factor = 1 + (age - 25) * 0.02  # 2% increase per year after 25
        income = base_income * age_factor * random.uniform(0.8, 1.5)
        
        # Net worth correlates with age and income
        net_worth = income * random.uniform(0.5, 5) * (age / 30)
        
        # Risk tolerance based on age
        if age < 35:
            risk_tolerance = random.choice(["moderate", "aggressive", "aggressive"])
        elif age < 50:
            risk_tolerance = random.choice(["conservative", "moderate", "aggressive"])
        else:
            risk_tolerance = random.choice(["conservative", "conservative", "moderate"])
        
        return TestUser(
            user_id=self.fake.uuid4(),
            email=self.fake.email(),
            password="Test@Password123",  # Standard test password
            first_name=self.fake.first_name(),
            last_name=self.fake.last_name(),
            age=age,
            income=round(income, 2),
            net_worth=round(net_worth, 2),
            risk_tolerance=risk_tolerance,
            investment_experience=random.choice(["beginner", "intermediate", "advanced"]),
            employment_status=random.choice(["employed", "self-employed", "retired"]),
            marital_status=random.choice(["single", "married", "divorced"]),
            dependents=random.randint(0, 3),
            phone=self.fake.phone_number(),
            address={
                "street": self.fake.street_address(),
                "city": self.fake.city(),
                "state": self.fake.state_abbr(),
                "zip": self.fake.zipcode()
            },
            created_at=self.fake.date_time_between(
                start_date="-2y", end_date="now"
            ).isoformat()
        )
    
    def generate_goals(self, user: TestUser, num_goals: int = 3) -> List[FinancialGoal]:
        """
        Generate financial goals for a user
        
        Args:
            user: Test user
            num_goals: Number of goals to generate
            
        Returns:
            List of financial goals
        """
        goals = []
        
        # Retirement goal (almost everyone has this)
        if user.age < 60:
            retirement_target = user.income * random.uniform(10, 25)
            retirement_date = datetime.now() + timedelta(days=(65 - user.age) * 365)
            
            goals.append(FinancialGoal(
                goal_id=self.fake.uuid4(),
                user_id=user.user_id,
                name="Retirement Fund",
                category="retirement",
                target_amount=round(retirement_target, 2),
                current_amount=round(retirement_target * random.uniform(0, 0.3), 2),
                target_date=retirement_date.isoformat(),
                priority="high",
                monthly_contribution=round(user.income * random.uniform(0.05, 0.15) / 12, 2),
                auto_invest=random.choice([True, False])
            ))
        
        # Additional goals based on age and profile
        if user.age < 40 and len(goals) < num_goals:
            # House down payment
            house_target = user.income * random.uniform(0.5, 2)
            goals.append(FinancialGoal(
                goal_id=self.fake.uuid4(),
                user_id=user.user_id,
                name="House Down Payment",
                category="house",
                target_amount=round(house_target, 2),
                current_amount=round(house_target * random.uniform(0, 0.5), 2),
                target_date=(datetime.now() + timedelta(days=random.randint(365, 1825))).isoformat(),
                priority=random.choice(["high", "medium"]),
                monthly_contribution=round(house_target / random.randint(24, 60), 2),
                auto_invest=True
            ))
        
        if user.dependents > 0 and len(goals) < num_goals:
            # Education fund
            education_target = random.uniform(50000, 200000)
            goals.append(FinancialGoal(
                goal_id=self.fake.uuid4(),
                user_id=user.user_id,
                name="College Education Fund",
                category="education",
                target_amount=round(education_target, 2),
                current_amount=round(education_target * random.uniform(0, 0.3), 2),
                target_date=(datetime.now() + timedelta(days=random.randint(1825, 6570))).isoformat(),
                priority="high",
                monthly_contribution=round(education_target / random.randint(60, 180), 2),
                auto_invest=True
            ))
        
        # Emergency fund (everyone should have this)
        if len(goals) < num_goals:
            emergency_target = user.income * random.uniform(0.25, 0.5)
            goals.append(FinancialGoal(
                goal_id=self.fake.uuid4(),
                user_id=user.user_id,
                name="Emergency Fund",
                category="emergency_fund",
                target_amount=round(emergency_target, 2),
                current_amount=round(emergency_target * random.uniform(0, 0.8), 2),
                target_date=(datetime.now() + timedelta(days=random.randint(180, 730))).isoformat(),
                priority="high",
                monthly_contribution=round(emergency_target / random.randint(6, 24), 2),
                auto_invest=False
            ))
        
        # Additional random goals
        while len(goals) < num_goals:
            category = random.choice(self.goal_categories)
            target = random.uniform(5000, 50000)
            
            goals.append(FinancialGoal(
                goal_id=self.fake.uuid4(),
                user_id=user.user_id,
                name=f"{category.replace('_', ' ').title()} Goal",
                category=category,
                target_amount=round(target, 2),
                current_amount=round(target * random.uniform(0, 0.5), 2),
                target_date=(datetime.now() + timedelta(days=random.randint(180, 3650))).isoformat(),
                priority=random.choice(["low", "medium", "high"]),
                monthly_contribution=round(target / random.randint(12, 120), 2),
                auto_invest=random.choice([True, False])
            ))
        
        return goals
    
    def generate_investments(self, user: TestUser, num_holdings: int = 10) -> List[Investment]:
        """
        Generate investment holdings for a user
        
        Args:
            user: Test user
            num_holdings: Number of holdings to generate
            
        Returns:
            List of investments
        """
        investments = []
        total_invested = user.net_worth * random.uniform(0.3, 0.8)
        
        # Allocate across different asset classes based on risk tolerance
        if user.risk_tolerance == "conservative":
            stock_ratio = 0.3
            bond_ratio = 0.6
            etf_ratio = 0.1
        elif user.risk_tolerance == "moderate":
            stock_ratio = 0.5
            bond_ratio = 0.3
            etf_ratio = 0.2
        else:  # aggressive
            stock_ratio = 0.7
            bond_ratio = 0.1
            etf_ratio = 0.2
        
        # Generate stock holdings
        num_stocks = int(num_holdings * stock_ratio)
        for _ in range(num_stocks):
            symbol = random.choice(self.stock_symbols)
            quantity = random.randint(10, 500)
            purchase_price = random.uniform(20, 500)
            # Simulate price movement
            price_change = random.uniform(-0.5, 1.5)
            current_price = purchase_price * (1 + price_change)
            
            investments.append(Investment(
                investment_id=self.fake.uuid4(),
                user_id=user.user_id,
                symbol=symbol,
                name=f"{symbol} Inc.",
                asset_class="stock",
                quantity=quantity,
                purchase_price=round(purchase_price, 2),
                current_price=round(current_price, 2),
                purchase_date=self.fake.date_between(start_date="-2y", end_date="today").isoformat(),
                account_type=random.choice(["taxable", "ira", "401k", "roth_ira"])
            ))
        
        # Generate ETF holdings
        num_etfs = int(num_holdings * etf_ratio)
        for _ in range(num_etfs):
            symbol = random.choice(self.etf_symbols)
            quantity = random.randint(50, 1000)
            purchase_price = random.uniform(50, 400)
            price_change = random.uniform(-0.2, 0.5)
            current_price = purchase_price * (1 + price_change)
            
            investments.append(Investment(
                investment_id=self.fake.uuid4(),
                user_id=user.user_id,
                symbol=symbol,
                name=f"{symbol} ETF",
                asset_class="etf",
                quantity=quantity,
                purchase_price=round(purchase_price, 2),
                current_price=round(current_price, 2),
                purchase_date=self.fake.date_between(start_date="-3y", end_date="today").isoformat(),
                account_type=random.choice(["taxable", "ira", "401k", "roth_ira"])
            ))
        
        # Generate bond holdings (simplified)
        num_bonds = num_holdings - num_stocks - num_etfs
        for _ in range(num_bonds):
            investments.append(Investment(
                investment_id=self.fake.uuid4(),
                user_id=user.user_id,
                symbol=f"BOND{random.randint(1000, 9999)}",
                name="Corporate Bond",
                asset_class="bond",
                quantity=random.randint(1, 50),
                purchase_price=1000,
                current_price=random.uniform(950, 1050),
                purchase_date=self.fake.date_between(start_date="-5y", end_date="today").isoformat(),
                account_type=random.choice(["taxable", "ira"])
            ))
        
        return investments
    
    def generate_transactions(
        self,
        user: TestUser,
        num_months: int = 6,
        transactions_per_month: int = 50
    ) -> List[Transaction]:
        """
        Generate transaction history for a user
        
        Args:
            user: Test user
            num_months: Number of months of history
            transactions_per_month: Average transactions per month
            
        Returns:
            List of transactions
        """
        transactions = []
        
        # Monthly income
        monthly_income = user.income / 12
        
        # Generate transactions for each month
        for month_offset in range(num_months):
            month_date = datetime.now() - timedelta(days=30 * month_offset)
            
            # Income transaction (salary)
            transactions.append(Transaction(
                transaction_id=self.fake.uuid4(),
                user_id=user.user_id,
                date=(month_date.replace(day=1)).isoformat(),
                description="Monthly Salary",
                category="Salary",
                amount=round(monthly_income, 2),
                transaction_type="income",
                account="checking",
                merchant="Employer",
                tags=["income", "salary", "regular"]
            ))
            
            # Generate expenses
            remaining_budget = monthly_income * random.uniform(0.7, 0.95)
            
            for _ in range(transactions_per_month - 1):
                # Random expense
                amount = random.uniform(5, min(500, remaining_budget / 10))
                category = random.choice(self.expense_categories)
                
                transaction_date = month_date - timedelta(
                    days=random.randint(0, 29),
                    hours=random.randint(0, 23),
                    minutes=random.randint(0, 59)
                )
                
                transactions.append(Transaction(
                    transaction_id=self.fake.uuid4(),
                    user_id=user.user_id,
                    date=transaction_date.isoformat(),
                    description=self.fake.sentence(nb_words=3),
                    category=category,
                    amount=round(amount, 2),
                    transaction_type="expense",
                    account=random.choice(["checking", "credit_card"]),
                    merchant=random.choice(self.merchants),
                    tags=self._generate_tags(category)
                ))
                
                remaining_budget -= amount
            
            # Investment contribution
            if random.random() > 0.3:
                transactions.append(Transaction(
                    transaction_id=self.fake.uuid4(),
                    user_id=user.user_id,
                    date=(month_date.replace(day=15)).isoformat(),
                    description="Investment Contribution",
                    category="Investment",
                    amount=round(monthly_income * random.uniform(0.05, 0.20), 2),
                    transaction_type="transfer",
                    account="investment",
                    merchant="Brokerage",
                    tags=["investment", "savings", "retirement"]
                ))
        
        return sorted(transactions, key=lambda x: x.date, reverse=True)
    
    def _generate_tags(self, category: str) -> List[str]:
        """Generate relevant tags for a transaction category"""
        tag_map = {
            "Housing": ["rent", "mortgage", "utilities", "home"],
            "Transportation": ["gas", "uber", "parking", "maintenance"],
            "Food": ["groceries", "dining", "restaurant", "coffee"],
            "Healthcare": ["medical", "pharmacy", "insurance", "health"],
            "Shopping": ["retail", "online", "clothing", "electronics"],
            "Entertainment": ["movies", "streaming", "games", "hobbies"]
        }
        
        base_tags = tag_map.get(category, [category.lower()])
        return random.sample(base_tags, min(2, len(base_tags)))
    
    def generate_market_data(self, num_days: int = 30) -> Dict[str, List[Dict]]:
        """
        Generate simulated market data
        
        Args:
            num_days: Number of days of market data
            
        Returns:
            Market data by symbol
        """
        market_data = {}
        
        for symbol in self.stock_symbols[:20]:  # Top 20 stocks
            data = []
            base_price = random.uniform(50, 500)
            
            for day_offset in range(num_days):
                date = datetime.now() - timedelta(days=day_offset)
                
                # Simulate daily price movement
                daily_return = np.random.normal(0.0002, 0.02)  # ~0.02% daily, 2% volatility
                base_price *= (1 + daily_return)
                
                # OHLCV data
                open_price = base_price * random.uniform(0.98, 1.02)
                high_price = base_price * random.uniform(1.00, 1.04)
                low_price = base_price * random.uniform(0.96, 1.00)
                close_price = base_price
                volume = random.randint(1000000, 50000000)
                
                data.append({
                    "date": date.isoformat(),
                    "open": round(open_price, 2),
                    "high": round(high_price, 2),
                    "low": round(low_price, 2),
                    "close": round(close_price, 2),
                    "volume": volume
                })
            
            market_data[symbol] = data
        
        return market_data
    
    def generate_complete_dataset(
        self,
        num_users: int = 100,
        output_dir: str = "./test_data"
    ) -> Dict[str, str]:
        """
        Generate complete test dataset
        
        Args:
            num_users: Number of test users to generate
            output_dir: Output directory for data files
            
        Returns:
            Paths to generated files
        """
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # Generate users
        users = []
        all_goals = []
        all_investments = []
        all_transactions = []
        
        for i in range(num_users):
            # Vary user profiles
            if i < num_users * 0.3:
                profile = "young"
            elif i < num_users * 0.6:
                profile = "moderate"
            elif i < num_users * 0.9:
                profile = "mature"
            else:
                profile = "senior"
            
            user = self.generate_user(profile)
            users.append(user)
            
            # Generate related data
            goals = self.generate_goals(user, num_goals=random.randint(2, 5))
            all_goals.extend(goals)
            
            investments = self.generate_investments(user, num_holdings=random.randint(5, 20))
            all_investments.extend(investments)
            
            transactions = self.generate_transactions(
                user,
                num_months=random.randint(3, 12),
                transactions_per_month=random.randint(30, 80)
            )
            all_transactions.extend(transactions)
        
        # Save users to JSON
        users_file = output_path / "test_users.json"
        with open(users_file, 'w') as f:
            json.dump([u.to_dict() for u in users], f, indent=2, default=str)
        
        # Save goals to JSON
        goals_file = output_path / "test_goals.json"
        with open(goals_file, 'w') as f:
            json.dump([g.to_dict() for g in all_goals], f, indent=2, default=str)
        
        # Save investments to JSON
        investments_file = output_path / "test_investments.json"
        with open(investments_file, 'w') as f:
            json.dump([i.to_dict() for i in all_investments], f, indent=2, default=str)
        
        # Save transactions to CSV (for bulk loading)
        transactions_file = output_path / "test_transactions.csv"
        with open(transactions_file, 'w', newline='') as f:
            if all_transactions:
                fieldnames = all_transactions[0].to_dict().keys()
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for t in all_transactions:
                    writer.writerow(t.to_dict())
        
        # Generate market data
        market_data = self.generate_market_data(num_days=90)
        market_file = output_path / "test_market_data.json"
        with open(market_file, 'w') as f:
            json.dump(market_data, f, indent=2, default=str)
        
        # Generate login credentials file for easy access
        credentials_file = output_path / "test_credentials.json"
        credentials = [
            {"email": u.email, "password": u.password, "user_id": u.user_id}
            for u in users[:20]  # First 20 users for quick access
        ]
        with open(credentials_file, 'w') as f:
            json.dump(credentials, f, indent=2)
        
        print(f"Generated test data for {num_users} users:")
        print(f"  - Users: {users_file}")
        print(f"  - Goals: {goals_file} ({len(all_goals)} total)")
        print(f"  - Investments: {investments_file} ({len(all_investments)} total)")
        print(f"  - Transactions: {transactions_file} ({len(all_transactions)} total)")
        print(f"  - Market Data: {market_file}")
        print(f"  - Credentials: {credentials_file}")
        
        return {
            "users": str(users_file),
            "goals": str(goals_file),
            "investments": str(investments_file),
            "transactions": str(transactions_file),
            "market_data": str(market_file),
            "credentials": str(credentials_file)
        }


if __name__ == "__main__":
    # Generate test dataset
    generator = TestDataGenerator(seed=42)
    files = generator.generate_complete_dataset(
        num_users=1000,
        output_dir="./test_data"
    )
    
    print("\nTest data generation complete!")
    print("Use these files for load testing scenarios")