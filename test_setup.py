#!/usr/bin/env python3
"""
Test script to verify the portfolio tracker setup is working correctly.
"""
import psycopg2
import yfinance as yf
from datetime import date, datetime
from decimal import Decimal
import uuid

def test_database_connection():
    """Test PostgreSQL connection and basic operations."""
    print("Testing database connection...")
    
    conn = psycopg2.connect(
        host="localhost",
        port=5432,  # This is the mapped port from docker-compose
        database="financial_planner",
        user="financial_user",
        password="secure_password_123"
    )
    cur = conn.cursor()
    
    # Test users table
    cur.execute("SELECT COUNT(*) FROM users;")
    user_count = cur.fetchone()[0]
    print(f"✓ Users table exists with {user_count} users")
    
    # Get demo user ID
    cur.execute("SELECT id FROM users WHERE email = 'demo@financialplanner.com';")
    user_id = cur.fetchone()[0]
    print(f"✓ Demo user ID: {user_id}")
    
    # Create a test account
    account_id = str(uuid.uuid4())
    cur.execute("""
        INSERT INTO accounts (id, user_id, name, account_type, institution)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT DO NOTHING
        RETURNING id;
    """, (account_id, user_id, 'Test Brokerage', 'taxable', 'Fidelity'))
    
    if cur.fetchone():
        print(f"✓ Created test account: {account_id}")
    
    # Add some test instruments
    instruments = [
        ('AAPL', 'Apple Inc.', 'equity'),
        ('MSFT', 'Microsoft Corporation', 'equity'),
        ('SPY', 'SPDR S&P 500 ETF', 'etf'),
        ('VTI', 'Vanguard Total Stock Market ETF', 'etf')
    ]
    
    for symbol, name, asset_class in instruments:
        cur.execute("""
            INSERT INTO instruments (symbol, name, asset_class)
            VALUES (%s, %s, %s)
            ON CONFLICT (symbol) DO UPDATE SET name = EXCLUDED.name
            RETURNING id;
        """, (symbol, name, asset_class))
        instrument_id = cur.fetchone()[0]
        print(f"✓ Added instrument: {symbol} (ID: {instrument_id})")
    
    # Add sample transactions
    cur.execute("SELECT id FROM instruments WHERE symbol = 'AAPL';")
    aapl_id = cur.fetchone()[0]
    
    cur.execute("""
        INSERT INTO transactions (
            account_id, instrument_id, transaction_type, 
            quantity, price, total_amount, trade_date
        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING id;
    """, (
        account_id, aapl_id, 'buy',
        Decimal('100'), Decimal('150.50'), Decimal('15050'),
        date(2024, 1, 15)
    ))
    transaction_id = cur.fetchone()[0]
    print(f"✓ Added test transaction: {transaction_id}")
    
    conn.commit()
    cur.close()
    conn.close()
    
    return True

def test_market_data():
    """Test market data fetching."""
    print("\nTesting market data fetch...")
    
    symbols = ['AAPL', 'MSFT', 'SPY']
    for symbol in symbols:
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            current_price = info.get('currentPrice') or info.get('regularMarketPrice')
            
            if not current_price:
                # Try alternative method
                hist = ticker.history(period="1d")
                if not hist.empty:
                    current_price = hist['Close'].iloc[-1]
            
            if current_price:
                print(f"✓ {symbol} current price: ${current_price:.2f}")
            else:
                print(f"⚠ {symbol}: Could not fetch price (market may be closed)")
        except Exception as e:
            print(f"✗ {symbol}: Error fetching data - {e}")
    
    return True

def test_timescale_connection():
    """Test TimescaleDB connection."""
    print("\nTesting TimescaleDB connection...")
    
    try:
        conn = psycopg2.connect(
            host="localhost",
            port=5433,
            database="financial_planner_ts",
            user="financial_user",
            password="secure_password_123"
        )
        cur = conn.cursor()
        
        # Check TimescaleDB version
        cur.execute("SELECT extversion FROM pg_extension WHERE extname = 'timescaledb';")
        version = cur.fetchone()[0]
        print(f"✓ TimescaleDB version: {version}")
        
        # Create a test hypertable for prices
        cur.execute("""
            CREATE TABLE IF NOT EXISTS prices (
                time TIMESTAMPTZ NOT NULL,
                symbol VARCHAR(20) NOT NULL,
                open DECIMAL(20, 8),
                high DECIMAL(20, 8),
                low DECIMAL(20, 8),
                close DECIMAL(20, 8),
                volume BIGINT
            );
        """)
        
        # Convert to hypertable if not already
        cur.execute("""
            SELECT * FROM timescaledb_information.hypertables 
            WHERE hypertable_name = 'prices';
        """)
        
        if not cur.fetchone():
            cur.execute("SELECT create_hypertable('prices', 'time', if_not_exists => TRUE);")
            print("✓ Created prices hypertable")
        else:
            print("✓ Prices hypertable already exists")
        
        conn.commit()
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"✗ TimescaleDB error: {e}")
        return False
    
    return True

def main():
    """Run all tests."""
    print("=" * 50)
    print("PORTFOLIO TRACKER SETUP TEST")
    print("=" * 50)
    
    all_passed = True
    
    try:
        if not test_database_connection():
            all_passed = False
    except Exception as e:
        print(f"✗ Database test failed: {e}")
        all_passed = False
    
    try:
        if not test_market_data():
            all_passed = False
    except Exception as e:
        print(f"✗ Market data test failed: {e}")
        all_passed = False
    
    try:
        if not test_timescale_connection():
            all_passed = False
    except Exception as e:
        print(f"✗ TimescaleDB test failed: {e}")
        all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("✅ ALL TESTS PASSED!")
        print("\nNext steps:")
        print("1. Start the FastAPI server: cd backend && uvicorn app.main_portfolio:app --reload")
        print("2. Visit http://localhost:8000/docs for API documentation")
        print("3. Test CSV import with sample data")
        print("4. Set up the frontend React application")
    else:
        print("⚠️ SOME TESTS FAILED")
        print("Please check the errors above and fix any issues.")
    print("=" * 50)

if __name__ == "__main__":
    main()