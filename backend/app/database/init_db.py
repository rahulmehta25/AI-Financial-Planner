"""
Database initialization and setup
"""

from sqlalchemy import text
from app.database.base import engine, Base
from app.models import *  # Import all models


async def init_db() -> None:
    """Initialize database tables"""
    async with engine.begin() as conn:
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
        
        # Create database extensions if needed
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";"))


async def reset_db() -> None:
    """Reset database (drop and recreate all tables)"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)