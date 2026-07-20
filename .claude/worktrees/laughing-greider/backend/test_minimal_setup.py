#!/usr/bin/env python3
"""
Minimal test to verify our setup actually works.
This is step 1: Can we connect to a database and do basic operations?
"""
import os
import sys
from decimal import Decimal
from datetime import datetime, date

# Test 1: Can we import our dependencies?
print("Step 1: Testing imports...")
try:
    import psycopg2
    print("✓ psycopg2 imported")
except ImportError:
    print("✗ psycopg2 not installed. Run: pip install psycopg2-binary")
    sys.exit(1)

try:
    import yfinance as yf
    print("✓ yfinance imported")
except ImportError:
    print("✗ yfinance not installed. Run: pip install yfinance")
    sys.exit(1)

try:
    import pandas as pd
    print("✓ pandas imported")
except ImportError:
    print("✗ pandas not installed. Run: pip install pandas")
    sys.exit(1)

# Test 2: Can we connect to PostgreSQL?
print("\nStep 2: Testing PostgreSQL connection...")
DB_URL = os.getenv('DATABASE_URL', 'postgresql://portfolio_user:portfolio_dev_password@localhost:5432/portfolio_db')

try:
    # Parse connection string
    import re
    match = re.match(r'postgresql://([^:]+):([^@]+)@([^/]+)/(.+)', DB_URL)
    if match:
        user, password, host_port, dbname = match.groups()
        host = host_port.split(':')[0]
        port = host_port.split(':')[1] if ':' in host_port else '5432'
    else:
        print("✗ Invalid DATABASE_URL format")
        sys.exit(1)
    
    conn = psycopg2.connect(
        host=host,
        port=port,
        database=dbname,
        user=user,
        password=password
    )
    cur = conn.cursor()
    cur.execute("SELECT version();")
    version = cur.fetchone()[0]
    print(f"✓ Connected to PostgreSQL: {version[:30]}...")
    
    # Test 3: Create a minimal table
    print("\nStep 3: Creating minimal transaction table...")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS test_transactions (
            id SERIAL PRIMARY KEY,
            symbol VARCHAR(10) NOT NULL,
            quantity DECIMAL(20, 8) NOT NULL,
            price DECIMAL(20, 8) NOT NULL,
            trade_date DATE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()
    print("✓ Table created/verified")
    
    # Test 4: Insert a test transaction
    print("\nStep 4: Inserting test transaction...")
    cur.execute("""
        INSERT INTO test_transactions (symbol, quantity, price, trade_date)
        VALUES (%s, %s, %s, %s)
        RETURNING id;
    """, ('AAPL', Decimal('100'), Decimal('150.50'), date(2024, 1, 15)))
    transaction_id = cur.fetchone()[0]
    conn.commit()
    print(f"✓ Transaction inserted with ID: {transaction_id}")
    
    # Test 5: Query it back
    print("\nStep 5: Querying transaction...")
    cur.execute("SELECT symbol, quantity, price, trade_date FROM test_transactions WHERE id = %s", (transaction_id,))
    result = cur.fetchone()
    print(f"✓ Retrieved: {result[0]} - {result[1]} shares @ ${result[2]} on {result[3]}")
    
    cur.close()
    conn.close()
    
except psycopg2.OperationalError as e:
    print(f"✗ Cannot connect to PostgreSQL: {e}")
    print("\nMake sure PostgreSQL is running:")
    print("  - If using Docker: docker-compose up postgres")
    print("  - If local: brew services start postgresql (Mac)")
    sys.exit(1)
except Exception as e:
    print(f"✗ Database error: {e}")
    sys.exit(1)

# Test 6: Can we fetch real market data?
print("\nStep 6: Testing market data fetch...")
try:
    ticker = yf.Ticker("AAPL")
    info = ticker.info
    current_price = info.get('currentPrice') or info.get('regularMarketPrice')
    if current_price:
        print(f"✓ AAPL current price: ${current_price}")
    else:
        # Try alternative method
        hist = ticker.history(period="1d")
        if not hist.empty:
            current_price = hist['Close'].iloc[-1]
            print(f"✓ AAPL last close: ${current_price:.2f}")
        else:
            print("✗ Could not fetch price (market may be closed)")
except Exception as e:
    print(f"✗ Market data error: {e}")

# Test 7: Parse a simple CSV
print("\nStep 7: Testing CSV parsing...")
csv_content = """Date,Symbol,Action,Quantity,Price
2024-01-15,AAPL,Buy,100,150.50
2024-01-20,GOOGL,Buy,50,140.25
2024-02-01,AAPL,Sell,50,155.00"""

try:
    import io
    df = pd.read_csv(io.StringIO(csv_content))
    print(f"✓ Parsed {len(df)} transactions from CSV")
    print(f"  Symbols: {df['Symbol'].unique().tolist()}")
    print(f"  Total shares bought: {df[df['Action']=='Buy']['Quantity'].sum()}")
    print(f"  Total shares sold: {df[df['Action']=='Sell']['Quantity'].sum()}")
except Exception as e:
    print(f"✗ CSV parsing error: {e}")

print("\n" + "="*50)
print("BASIC SETUP TEST COMPLETE")
print("="*50)
print("\nNext steps:")
print("1. Create a real transaction import function")
print("2. Build cost basis calculation")
print("3. Add a simple API endpoint")
print("4. Create a basic frontend to display data")