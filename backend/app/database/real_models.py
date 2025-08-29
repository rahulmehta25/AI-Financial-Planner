"""
Real, working database models - not boilerplate!
Using SQLAlchemy with SQLite for easy local development
"""

from sqlalchemy import create_engine, Column, String, Float, Integer, DateTime, ForeignKey, JSON, Numeric
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime
import uuid

Base = declarative_base()

class User(Base):
    """Real user model"""
    __tablename__ = 'users'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    first_name = Column(String)
    last_name = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    portfolios = relationship("Portfolio", back_populates="user", cascade="all, delete-orphan")

class Portfolio(Base):
    """Real portfolio model"""
    __tablename__ = 'portfolios'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey('users.id'), nullable=False)
    name = Column(String, nullable=False)
    description = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Cached metrics (updated periodically)
    total_value = Column(Numeric(20, 2))
    total_cost = Column(Numeric(20, 2))
    total_gain_loss = Column(Numeric(20, 2))
    last_calculated = Column(DateTime)
    
    # Relationships
    user = relationship("User", back_populates="portfolios")
    holdings = relationship("Holding", back_populates="portfolio", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="portfolio", cascade="all, delete-orphan")

class Holding(Base):
    """Real holding model - what you currently own"""
    __tablename__ = 'holdings'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    portfolio_id = Column(String, ForeignKey('portfolios.id'), nullable=False)
    symbol = Column(String, nullable=False, index=True)
    quantity = Column(Numeric(20, 8), nullable=False)
    cost_basis = Column(Numeric(20, 2))  # Average cost per share
    
    # Current market data (cached)
    current_price = Column(Numeric(20, 2))
    market_value = Column(Numeric(20, 2))
    gain_loss = Column(Numeric(20, 2))
    gain_loss_percent = Column(Numeric(10, 2))
    last_updated = Column(DateTime)
    
    # Relationships
    portfolio = relationship("Portfolio", back_populates="holdings")

class Transaction(Base):
    """Real transaction model - buy/sell history"""
    __tablename__ = 'transactions'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    portfolio_id = Column(String, ForeignKey('portfolios.id'), nullable=False)
    symbol = Column(String, nullable=False, index=True)
    transaction_type = Column(String, nullable=False)  # 'buy' or 'sell'
    quantity = Column(Numeric(20, 8), nullable=False)
    price = Column(Numeric(20, 2), nullable=False)
    fees = Column(Numeric(10, 2), default=0)
    transaction_date = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    portfolio = relationship("Portfolio", back_populates="transactions")

class MarketData(Base):
    """Cache for market data"""
    __tablename__ = 'market_data'
    
    symbol = Column(String, primary_key=True)
    name = Column(String)
    current_price = Column(Numeric(20, 2))
    previous_close = Column(Numeric(20, 2))
    day_change = Column(Numeric(20, 2))
    day_change_percent = Column(Numeric(10, 2))
    volume = Column(Integer)
    market_cap = Column(Numeric(20, 0))
    pe_ratio = Column(Numeric(10, 2))
    dividend_yield = Column(Numeric(10, 4))
    fifty_two_week_high = Column(Numeric(20, 2))
    fifty_two_week_low = Column(Numeric(20, 2))
    last_updated = Column(DateTime, default=datetime.utcnow)
    
    # Additional data as JSON
    extra_data = Column(JSON)


# Database setup
def init_database(db_url="sqlite:///./financial_planner.db"):
    """Initialize the database - creates all tables"""
    engine = create_engine(db_url, echo=True)
    Base.metadata.create_all(bind=engine)
    return engine

def get_session(engine):
    """Get a database session"""
    Session = sessionmaker(bind=engine)
    return Session()


# Test the models
if __name__ == "__main__":
    # Create database
    engine = init_database()
    session = get_session(engine)
    
    # Create a test user
    test_user = User(
        email="test@example.com",
        password_hash="hashed_password_here",
        first_name="Test",
        last_name="User"
    )
    session.add(test_user)
    session.commit()
    
    # Create a test portfolio
    test_portfolio = Portfolio(
        user_id=test_user.id,
        name="My Investment Portfolio",
        description="Long-term growth portfolio"
    )
    session.add(test_portfolio)
    session.commit()
    
    # Add some holdings
    holdings = [
        Holding(portfolio_id=test_portfolio.id, symbol="AAPL", quantity=10, cost_basis=150),
        Holding(portfolio_id=test_portfolio.id, symbol="GOOGL", quantity=5, cost_basis=2500),
        Holding(portfolio_id=test_portfolio.id, symbol="MSFT", quantity=15, cost_basis=300)
    ]
    session.add_all(holdings)
    session.commit()
    
    print(f"Created test user: {test_user.email}")
    print(f"Created portfolio: {test_portfolio.name}")
    print(f"Added {len(holdings)} holdings")
    
    session.close()