#!/usr/bin/env python3
"""
Initialize SQLite database with tables
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy.ext.asyncio import create_async_engine
from app.core.database import Base, engine
from app.models.user import User
from app.models.all_models import Account, Instrument, Transaction, Position, Price, Lot


async def init_db():
    """Create all tables in SQLite"""
    print("Creating SQLite database...")
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    print("✓ Database tables created successfully")
    print("  Database file: test_portfolio.db")
    

if __name__ == "__main__":
    asyncio.run(init_db())