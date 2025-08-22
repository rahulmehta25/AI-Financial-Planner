"""
Database Base Configuration

Database engine, session management, and base configuration for the
AI Financial Planning System.
"""

import logging
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession, 
    create_async_engine, 
    async_sessionmaker,
    AsyncEngine
)
from sqlalchemy.pool import NullPool
from sqlalchemy.orm import declarative_base

from app.core.config import settings

logger = logging.getLogger(__name__)

# Create declarative base
Base = declarative_base()

# Database engine
engine: AsyncEngine = None
async_session_maker: async_sessionmaker = None


def create_engine() -> AsyncEngine:
    """Create async database engine"""
    global engine
    
    if engine is None:
        logger.info("Creating database engine...")
        
        # Engine configuration
        engine_config = {
            "echo": settings.DEBUG,
            "pool_size": settings.DATABASE_POOL_SIZE,
            "max_overflow": settings.DATABASE_MAX_OVERFLOW,
            "pool_timeout": settings.DATABASE_POOL_TIMEOUT,
            "pool_pre_ping": True,
            "pool_recycle": 3600,  # Recycle connections every hour
        }
        
        # Use NullPool for testing
        if settings.TESTING:
            engine_config["poolclass"] = NullPool
        
        try:
            engine = create_async_engine(
                settings.DATABASE_URL,
                **engine_config
            )
            logger.info("Database engine created successfully")
        except Exception as e:
            logger.error(f"Failed to create database engine: {str(e)}")
            raise
    
    return engine


def create_session_maker() -> async_sessionmaker:
    """Create async session maker"""
    global async_session_maker
    
    if async_session_maker is None:
        logger.info("Creating session maker...")
        
        if engine is None:
            create_engine()
        
        async_session_maker = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False
        )
        
        logger.info("Session maker created successfully")
    
    return async_session_maker


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session"""
    
    if async_session_maker is None:
        create_session_maker()
    
    async with async_session_maker() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Database session error: {str(e)}")
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize database"""
    
    try:
        logger.info("Initializing database...")
        
        # Create engine and session maker
        create_engine()
        create_session_maker()
        
        # Test database connection
        async with engine.begin() as conn:
            await conn.run_sync(lambda sync_conn: sync_conn.execute("SELECT 1"))
        
        logger.info("Database initialized successfully")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        raise


async def close_db() -> None:
    """Close database connections"""
    
    global engine, async_session_maker
    
    try:
        if engine:
            await engine.dispose()
            engine = None
            logger.info("Database engine closed")
        
        async_session_maker = None
        
    except Exception as e:
        logger.error(f"Error closing database: {str(e)}")


async def get_db_info() -> dict:
    """Get database information"""
    
    try:
        if engine is None:
            return {"status": "not_initialized"}
        
        # Test connection
        async with engine.begin() as conn:
            result = await conn.run_sync(lambda sync_conn: sync_conn.execute("SELECT version()"))
            version = result.scalar()
        
        return {
            "status": "connected",
            "version": version,
            "pool_size": engine.pool.size(),
            "checked_in": engine.pool.checkedin(),
            "checked_out": engine.pool.checkedout(),
            "overflow": engine.pool.overflow()
        }
        
    except Exception as e:
        logger.error(f"Failed to get database info: {str(e)}")
        return {
            "status": "error",
            "error": str(e)
        }


async def health_check() -> dict:
    """Database health check"""
    
    try:
        db_info = await get_db_info()
        
        if db_info["status"] == "connected":
            return {
                "status": "healthy",
                "database": "connected",
                "details": db_info
            }
        else:
            return {
                "status": "unhealthy",
                "database": db_info["status"],
                "details": db_info
            }
            
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "database": "error",
            "error": str(e)
        }