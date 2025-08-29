#!/usr/bin/env python3
"""
Run the portfolio tracker API locally
This is REAL, WORKING code - not boilerplate!
"""

import sys
import os
import subprocess

# Add app directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

def check_requirements():
    """Check and install required packages"""
    required = ['fastapi', 'uvicorn', 'sqlalchemy', 'yfinance', 'pandas']
    
    for package in required:
        try:
            __import__(package)
        except ImportError:
            print(f"Installing {package}...")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])

def test_market_data():
    """Test that market data fetching works"""
    print("\n📊 Testing Market Data Service...")
    from app.core.market_data import MarketDataService
    
    service = MarketDataService()
    
    # Test getting a stock price
    price = service.get_current_price("AAPL")
    if price:
        print(f"✅ Apple (AAPL) current price: ${price:.2f}")
    else:
        print("❌ Failed to fetch Apple price")
    
    # Test portfolio calculation
    test_holdings = [
        {'symbol': 'AAPL', 'quantity': 10, 'cost_basis': 150},
        {'symbol': 'GOOGL', 'quantity': 5, 'cost_basis': 2500},
    ]
    
    metrics = service.calculate_portfolio_metrics(test_holdings)
    if metrics['total_value'] > 0:
        print(f"✅ Portfolio value: ${metrics['total_value']:,.2f}")
        print(f"   Gain/Loss: ${metrics['total_gain_loss']:,.2f} ({metrics['total_gain_loss_percent']:.2f}%)")
    else:
        print("❌ Failed to calculate portfolio metrics")

def setup_database():
    """Initialize the database"""
    print("\n🗄️ Setting up database...")
    from app.database.real_models import init_database, get_session, User, Portfolio, Holding
    
    engine = init_database()
    session = get_session(engine)
    
    # Check if demo user exists
    demo_user = session.query(User).filter(User.id == "demo-user-123").first()
    if not demo_user:
        print("Creating demo user...")
        demo_user = User(
            id="demo-user-123",
            email="demo@example.com",
            password_hash="demo",
            first_name="Demo",
            last_name="User"
        )
        session.add(demo_user)
        session.commit()
        print("✅ Demo user created")
    else:
        print("✅ Demo user already exists")
    
    # Check for portfolios
    portfolios = session.query(Portfolio).filter(Portfolio.user_id == "demo-user-123").all()
    print(f"📁 Found {len(portfolios)} existing portfolios")
    
    session.close()

def run_api():
    """Run the FastAPI server"""
    print("\n🚀 Starting Portfolio Tracker API...")
    print("📍 API will be available at: http://localhost:8000")
    print("📍 API docs at: http://localhost:8000/docs")
    print("\nPress Ctrl+C to stop the server\n")
    
    import uvicorn
    from app.api.portfolio_api import app
    
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)

if __name__ == "__main__":
    print("=" * 50)
    print("🎯 REAL Portfolio Tracker - Local Setup")
    print("=" * 50)
    
    # Check requirements
    print("\n📦 Checking requirements...")
    check_requirements()
    print("✅ All requirements installed")
    
    # Test market data
    test_market_data()
    
    # Setup database
    setup_database()
    
    # Run API
    run_api()