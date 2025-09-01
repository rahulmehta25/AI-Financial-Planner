#!/usr/bin/env python3
"""
Test Railway PostgreSQL connection
"""
import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

# Get DATABASE_URL from environment or use a test URL
DATABASE_URL = os.getenv("DATABASE_URL", "")

# Railway provides postgresql:// but we need postgresql+asyncpg://
if DATABASE_URL.startswith("postgresql://"):
    ASYNC_DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
else:
    ASYNC_DATABASE_URL = DATABASE_URL

async def test_connection():
    """Test database connection"""
    if not DATABASE_URL:
        print("❌ No DATABASE_URL found in environment")
        print("\nTo test Railway database connection:")
        print("1. Go to Railway dashboard")
        print("2. Click on your PostgreSQL database")
        print("3. Copy the DATABASE_URL from Variables tab")
        print("4. Run: export DATABASE_URL='your-database-url'")
        print("5. Run this script again")
        return
    
    print(f"Testing connection to Railway PostgreSQL...")
    print(f"URL: {ASYNC_DATABASE_URL[:50]}...")  # Show partial URL for security
    
    try:
        # Create engine
        engine = create_async_engine(ASYNC_DATABASE_URL, echo=True)
        
        # Test connection
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT version()"))
            version = result.scalar()
            print(f"✅ Connected successfully!")
            print(f"PostgreSQL version: {version}")
            
            # Check if our tables exist
            result = await conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """))
            tables = result.fetchall()
            
            if tables:
                print(f"\nExisting tables:")
                for table in tables:
                    print(f"  - {table[0]}")
            else:
                print("\n⚠️ No tables found. Database is empty.")
                print("Run migrations to create tables.")
        
        await engine.dispose()
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("\nTroubleshooting:")
        print("1. Check if DATABASE_URL is correct")
        print("2. Check if database is running in Railway")
        print("3. Check network connectivity")

if __name__ == "__main__":
    asyncio.run(test_connection())