#!/usr/bin/env python3
"""
Initialize Railway PostgreSQL database with tables
"""
import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from app.core.database import Base
from app.models.user import User
from app.models.all_models import Account, Instrument, Transaction, Position, Price, Lot

# Get DATABASE_URL from environment
DATABASE_URL = os.getenv("DATABASE_URL", "")

# For local testing with public URL
# Uncomment and replace with your public URL:
# DATABASE_URL = "postgresql://postgres:oKlOSTYHPWxKGQYxlzrptJtNtXxZkoic@roundhouse.proxy.rlwy.net:PORT/railway"

if DATABASE_URL.startswith("postgresql://"):
    ASYNC_DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
else:
    ASYNC_DATABASE_URL = DATABASE_URL

async def init_db():
    """Create all tables in PostgreSQL"""
    if not DATABASE_URL:
        print("❌ No DATABASE_URL found")
        print("\nTo initialize Railway database:")
        print("1. Get PUBLIC DATABASE_URL from Railway")
        print("2. Run: export DATABASE_URL='your-public-url'")
        print("3. Run this script again")
        return
    
    print("Creating tables in Railway PostgreSQL...")
    print(f"Database: {ASYNC_DATABASE_URL[:50]}...")
    
    try:
        # Create engine
        engine = create_async_engine(ASYNC_DATABASE_URL, echo=True)
        
        # Create all tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        print("✅ All tables created successfully!")
        
        # List created tables
        async with engine.begin() as conn:
            from sqlalchemy import text
            result = await conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """))
            tables = result.fetchall()
            
            print("\nCreated tables:")
            for table in tables:
                print(f"  ✓ {table[0]}")
        
        await engine.dispose()
        
    except Exception as e:
        print(f"❌ Failed to create tables: {e}")

if __name__ == "__main__":
    asyncio.run(init_db())