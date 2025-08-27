"""
Test data factories for creating consistent test data.

Uses Factory Boy to create test instances of models with realistic data.
Provides factories for all major models with appropriate relationships.
"""
import factory
from factory import LazyAttribute, SubFactory, Sequence
from faker import Faker
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
from decimal import Decimal
import uuid
import asyncio

from app.models.user import User
from app.models.financial_profile import FinancialProfile
from app.models.goal import Goal
from app.models.investment import Investment
from app.models.market_data import MarketData
from app.models.simulation_result import SimulationResult

fake = Faker()


class AsyncSQLAlchemyModelFactory(factory.Factory):
    """Base factory for SQLAlchemy models with async session support."""
    
    class Meta:
        abstract = True
    
    @classmethod
    async def create(cls, session: AsyncSession, **kwargs):
        """Create and persist a model instance asynchronously."""
        instance = cls.build(**kwargs)
        session.add(instance)
        await session.commit()
        await session.refresh(instance)
        return instance
    
    @classmethod
    async def create_batch(cls, session: AsyncSession, size: int, **kwargs):
        """Create multiple instances asynchronously."""
        instances = []
        for _ in range(size):
            instance = await cls.create(session, **kwargs)
            instances.append(instance)
        return instances


class UserFactory(AsyncSQLAlchemyModelFactory):
    """Factory for creating test users."""
    
    class Meta:
        model = User
    
    id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    email = factory.Sequence(lambda n: f"user{n}@example.com")
    hashed_password = "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW"  # "secret"
    first_name = factory.LazyAttribute(lambda obj: fake.first_name())
    last_name = factory.LazyAttribute(lambda obj: fake.last_name())
    phone_number = factory.LazyAttribute(lambda obj: fake.phone_number())
    date_of_birth = factory.LazyAttribute(lambda obj: fake.date_of_birth(minimum_age=18, maximum_age=80))
    is_active = True
    is_verified = True
    created_at = factory.LazyFunction(datetime.utcnow)
    updated_at = factory.LazyFunction(datetime.utcnow)


class FinancialProfileFactory(AsyncSQLAlchemyModelFactory):
    """Factory for creating test financial profiles."""
    
    class Meta:
        model = FinancialProfile
    
    id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    user_id = factory.LazyAttribute(lambda obj: str(uuid.uuid4()))
    annual_income = factory.LazyAttribute(lambda obj: Decimal(fake.random_int(min=30000, max=200000)))
    monthly_expenses = factory.LazyAttribute(lambda obj: obj.annual_income / 12 * Decimal('0.7'))
    current_savings = factory.LazyAttribute(lambda obj: fake.random_int(min=1000, max=100000))
    current_debt = factory.LazyAttribute(lambda obj: fake.random_int(min=0, max=50000))
    investment_experience = factory.Iterator(['beginner', 'intermediate', 'advanced'])
    risk_tolerance = factory.Iterator(['conservative', 'moderate', 'aggressive'])
    investment_timeline = factory.LazyAttribute(lambda obj: fake.random_int(min=1, max=30))
    financial_goals = factory.List([
        'retirement',
        'house_down_payment',
        'emergency_fund',
        'education'
    ])
    employment_status = factory.Iterator(['employed', 'self_employed', 'unemployed', 'retired'])
    marital_status = factory.Iterator(['single', 'married', 'divorced', 'widowed'])
    dependents = factory.LazyAttribute(lambda obj: fake.random_int(min=0, max=5))
    created_at = factory.LazyFunction(datetime.utcnow)
    updated_at = factory.LazyFunction(datetime.utcnow)


class GoalFactory(AsyncSQLAlchemyModelFactory):
    """Factory for creating test financial goals."""
    
    class Meta:
        model = Goal
    
    id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    user_id = factory.LazyAttribute(lambda obj: str(uuid.uuid4()))
    name = factory.Iterator([
        'Retirement Fund',
        'House Down Payment',
        'Emergency Fund',
        'Vacation Fund',
        'Car Purchase',
        'Education Fund'
    ])
    description = factory.LazyAttribute(lambda obj: fake.text(max_nb_chars=200))
    goal_type = factory.Iterator(['retirement', 'major_purchase', 'emergency', 'education', 'other'])
    target_amount = factory.LazyAttribute(lambda obj: Decimal(fake.random_int(min=5000, max=1000000)))
    current_amount = factory.LazyAttribute(lambda obj: obj.target_amount * Decimal(fake.random.uniform(0, 0.5)))
    target_date = factory.LazyAttribute(lambda obj: fake.date_between(start_date='+1y', end_date='+30y'))
    priority = factory.Iterator(['low', 'medium', 'high'])
    status = factory.Iterator(['active', 'paused', 'completed', 'cancelled'])
    monthly_contribution = factory.LazyAttribute(lambda obj: Decimal(fake.random_int(min=50, max=2000)))
    created_at = factory.LazyFunction(datetime.utcnow)
    updated_at = factory.LazyFunction(datetime.utcnow)


class InvestmentFactory(AsyncSQLAlchemyModelFactory):
    """Factory for creating test investments."""
    
    class Meta:
        model = Investment
    
    id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    user_id = factory.LazyAttribute(lambda obj: str(uuid.uuid4()))
    symbol = factory.Iterator(['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA', 'SPY', 'QQQ', 'VTI'])
    name = factory.LazyAttribute(lambda obj: fake.company())
    investment_type = factory.Iterator(['stock', 'bond', 'etf', 'mutual_fund', 'cryptocurrency', 'real_estate'])
    quantity = factory.LazyAttribute(lambda obj: Decimal(fake.random.uniform(1, 1000)))
    purchase_price = factory.LazyAttribute(lambda obj: Decimal(fake.random.uniform(10, 1000)))
    current_price = factory.LazyAttribute(lambda obj: obj.purchase_price * Decimal(fake.random.uniform(0.5, 2.0)))
    purchase_date = factory.LazyAttribute(lambda obj: fake.date_between(start_date='-5y', end_date='today'))
    sector = factory.Iterator(['technology', 'healthcare', 'finance', 'energy', 'consumer', 'industrial'])
    risk_level = factory.Iterator(['low', 'medium', 'high'])
    created_at = factory.LazyFunction(datetime.utcnow)
    updated_at = factory.LazyFunction(datetime.utcnow)


class MarketDataFactory(AsyncSQLAlchemyModelFactory):
    """Factory for creating test market data."""
    
    class Meta:
        model = MarketData
    
    id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    symbol = factory.Iterator(['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA', 'SPY', 'QQQ'])
    date = factory.LazyAttribute(lambda obj: fake.date_between(start_date='-1y', end_date='today'))
    open_price = factory.LazyAttribute(lambda obj: Decimal(fake.random.uniform(100, 500)))
    high_price = factory.LazyAttribute(lambda obj: obj.open_price * Decimal(fake.random.uniform(1.0, 1.1)))
    low_price = factory.LazyAttribute(lambda obj: obj.open_price * Decimal(fake.random.uniform(0.9, 1.0)))
    close_price = factory.LazyAttribute(lambda obj: Decimal(fake.random.uniform(float(obj.low_price), float(obj.high_price))))
    volume = factory.LazyAttribute(lambda obj: fake.random_int(min=1000000, max=100000000))
    adjusted_close = factory.LazyAttribute(lambda obj: obj.close_price)
    created_at = factory.LazyFunction(datetime.utcnow)


class SimulationResultFactory(AsyncSQLAlchemyModelFactory):
    """Factory for creating test simulation results."""
    
    class Meta:
        model = SimulationResult
    
    id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    user_id = factory.LazyAttribute(lambda obj: str(uuid.uuid4()))
    simulation_type = factory.Iterator(['monte_carlo', 'goal_planning', 'retirement', 'portfolio_optimization'])
    parameters = factory.LazyAttribute(lambda obj: {
        'initial_investment': fake.random_int(min=1000, max=100000),
        'monthly_contribution': fake.random_int(min=100, max=5000),
        'time_horizon': fake.random_int(min=1, max=40),
        'risk_tolerance': fake.random.choice(['conservative', 'moderate', 'aggressive'])
    })
    results = factory.LazyAttribute(lambda obj: {
        'final_value': {
            'mean': fake.random_int(min=50000, max=2000000),
            'median': fake.random_int(min=40000, max=1800000),
            'percentile_10': fake.random_int(min=20000, max=1000000),
            'percentile_90': fake.random_int(min=80000, max=3000000)
        },
        'success_probability': fake.random.uniform(0.6, 0.95),
        'annual_return': fake.random.uniform(0.04, 0.12),
        'volatility': fake.random.uniform(0.08, 0.25)
    })
    success_probability = factory.LazyAttribute(lambda obj: obj.results['success_probability'])
    confidence_interval = factory.LazyAttribute(lambda obj: [
        obj.results['final_value']['percentile_10'],
        obj.results['final_value']['percentile_90']
    ])
    created_at = factory.LazyFunction(datetime.utcnow)


# Scenario-specific factories
class RetirementGoalFactory(GoalFactory):
    """Factory for retirement-specific goals."""
    name = "Retirement Fund"
    goal_type = "retirement"
    target_amount = factory.LazyAttribute(lambda obj: Decimal(fake.random_int(min=500000, max=2000000)))
    target_date = factory.LazyAttribute(lambda obj: fake.date_between(start_date='+10y', end_date='+40y'))
    priority = "high"


class EmergencyFundFactory(GoalFactory):
    """Factory for emergency fund goals."""
    name = "Emergency Fund"
    goal_type = "emergency"
    target_amount = factory.LazyAttribute(lambda obj: Decimal(fake.random_int(min=10000, max=50000)))
    target_date = factory.LazyAttribute(lambda obj: fake.date_between(start_date='+6m', end_date='+2y'))
    priority = "high"


class HouseDownPaymentFactory(GoalFactory):
    """Factory for house down payment goals."""
    name = "House Down Payment"
    goal_type = "major_purchase"
    target_amount = factory.LazyAttribute(lambda obj: Decimal(fake.random_int(min=50000, max=200000)))
    target_date = factory.LazyAttribute(lambda obj: fake.date_between(start_date='+2y', end_date='+10y'))
    priority = "medium"


class ConservativeProfileFactory(FinancialProfileFactory):
    """Factory for conservative financial profiles."""
    risk_tolerance = "conservative"
    investment_experience = "beginner"
    investment_timeline = factory.LazyAttribute(lambda obj: fake.random_int(min=1, max=10))


class AggressiveProfileFactory(FinancialProfileFactory):
    """Factory for aggressive financial profiles."""
    risk_tolerance = "aggressive"
    investment_experience = "advanced"
    investment_timeline = factory.LazyAttribute(lambda obj: fake.random_int(min=15, max=30))


# Advanced scenario factories for comprehensive testing

class TaxOptimizationScenarioFactory(AsyncSQLAlchemyModelFactory):
    """Factory for creating tax optimization test scenarios."""
    
    class Meta:
        abstract = True
    
    @classmethod
    async def create_tax_scenario(cls, session: AsyncSession, scenario_type: str = 'basic'):
        """Create comprehensive tax optimization scenario."""
        
        if scenario_type == 'high_earner':
            return await cls.create_high_earner_scenario(session)
        elif scenario_type == 'retiree':
            return await cls.create_retiree_scenario(session)
        elif scenario_type == 'young_professional':
            return await cls.create_young_professional_scenario(session)
        else:
            return await cls.create_basic_scenario(session)
    
    @classmethod
    async def create_high_earner_scenario(cls, session: AsyncSession):
        """High earner with complex tax situation."""
        user = await UserFactory.create(session=session)
        
        profile = await FinancialProfileFactory.create(
            session=session,
            user_id=user.id,
            annual_income=Decimal('250000'),
            current_savings=Decimal('500000'),
            current_debt=Decimal('75000'),
            risk_tolerance='aggressive'
        )
        
        # Multiple account types
        accounts = {
            'taxable': Decimal('300000'),
            'traditional_401k': Decimal('400000'),
            'roth_ira': Decimal('75000'),
            'hsa': Decimal('25000')
        }
        
        # Tax lots with gains and losses
        tax_lots = [
            {'symbol': 'AAPL', 'quantity': 500, 'cost_basis': 120.0, 'current_price': 180.0},
            {'symbol': 'GOOGL', 'quantity': 100, 'cost_basis': 2800.0, 'current_price': 2600.0},
            {'symbol': 'MSFT', 'quantity': 200, 'cost_basis': 250.0, 'current_price': 420.0},
            {'symbol': 'TSLA', 'quantity': 150, 'cost_basis': 900.0, 'current_price': 250.0}
        ]
        
        return {
            'user': user,
            'profile': profile,
            'accounts': accounts,
            'tax_lots': tax_lots,
            'scenario_type': 'high_earner'
        }
    
    @classmethod
    async def create_basic_scenario(cls, session: AsyncSession):
        """Basic tax scenario."""
        user = await UserFactory.create(session=session)
        
        profile = await FinancialProfileFactory.create(
            session=session,
            user_id=user.id,
            annual_income=Decimal('75000'),
            current_savings=Decimal('50000'),
            risk_tolerance='moderate'
        )
        
        accounts = {
            'taxable': Decimal('30000'),
            'traditional_401k': Decimal('50000')
        }
        
        return {
            'user': user,
            'profile': profile,
            'accounts': accounts,
            'scenario_type': 'basic'
        }


class EnhancedMarketDataFactory(MarketDataFactory):
    """Enhanced market data factory for advanced testing."""
    
    @classmethod
    async def create_time_series(cls, session: AsyncSession, symbol: str, days: int = 252):
        """Create time series data for backtesting."""
        import numpy as np
        
        start_date = fake.date_between(start_date='-2y', end_date='-1y')
        base_price = Decimal(fake.random.uniform(50, 500))
        
        data_points = []
        current_price = base_price
        
        for i in range(days):
            # Simulate realistic price movements
            daily_return = np.random.normal(0.0005, 0.02)  # ~12.5% annual return, 20% volatility
            current_price *= Decimal(1 + daily_return)
            
            # Generate OHLCV data
            high_price = current_price * Decimal(fake.random.uniform(1.0, 1.05))
            low_price = current_price * Decimal(fake.random.uniform(0.95, 1.0))
            volume = fake.random_int(min=100000, max=10000000)
            
            data_point = await cls.create(
                session=session,
                symbol=symbol,
                timestamp=datetime.combine(start_date + timedelta(days=i), datetime.min.time()),
                open_price=current_price,
                high_price=high_price,
                low_price=low_price,
                close_price=current_price,
                volume=volume,
                adjusted_close=current_price
            )
            data_points.append(data_point)
        
        return data_points


# Helper functions for creating test data scenarios
async def create_complete_user_scenario(session: AsyncSession, risk_tolerance: str = 'moderate'):
    """Create a complete user scenario with profile, goals, and investments."""
    user = await UserFactory.create(session=session)
    
    if risk_tolerance == 'conservative':
        profile = await ConservativeProfileFactory.create(session=session, user_id=user.id)
    elif risk_tolerance == 'aggressive':
        profile = await AggressiveProfileFactory.create(session=session, user_id=user.id)
    else:
        profile = await FinancialProfileFactory.create(session=session, user_id=user.id, risk_tolerance=risk_tolerance)
    
    # Create goals
    retirement_goal = await RetirementGoalFactory.create(session=session, user_id=user.id)
    emergency_goal = await EmergencyFundFactory.create(session=session, user_id=user.id)
    house_goal = await HouseDownPaymentFactory.create(session=session, user_id=user.id)
    
    # Create investments
    investments = await InvestmentFactory.create_batch(session=session, size=5, user_id=user.id)
    
    return {
        'user': user,
        'profile': profile,
        'goals': [retirement_goal, emergency_goal, house_goal],
        'investments': investments
    }


async def create_retirement_scenario(session: AsyncSession, age: int = 35):
    """Create a user scenario focused on retirement planning."""
    user = await UserFactory.create(session=session)
    user.date_of_birth = fake.date_of_birth(minimum_age=age, maximum_age=age)
    
    profile = await FinancialProfileFactory.create(
        session=session,
        user_id=user.id,
        annual_income=Decimal('75000'),
        current_savings=Decimal('50000'),
        risk_tolerance='moderate',
        investment_timeline=65 - age
    )
    
    retirement_goal = await RetirementGoalFactory.create(
        session=session,
        user_id=user.id,
        target_amount=Decimal('1000000'),
        target_date=fake.date_between(start_date=f'+{65-age}y', end_date=f'+{70-age}y')
    )
    
    return {
        'user': user,
        'profile': profile,
        'retirement_goal': retirement_goal
    }


async def create_tax_optimization_scenario(session: AsyncSession, scenario_type: str = 'basic'):
    """Create tax optimization scenario with multiple accounts and positions."""
    
    return await TaxOptimizationScenarioFactory.create_tax_scenario(
        session=session,
        scenario_type=scenario_type
    )


async def create_market_data_universe(session: AsyncSession, symbols: list, days: int = 252):
    """Create comprehensive market data for multiple symbols."""
    
    market_data = {}
    
    for symbol in symbols:
        data_points = await EnhancedMarketDataFactory.create_time_series(
            session=session,
            symbol=symbol,
            days=days
        )
        market_data[symbol] = data_points
    
    return market_data