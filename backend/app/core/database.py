"""
Database connection and session management
"""
from typing import AsyncGenerator, Optional
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool
from sqlalchemy import MetaData, event
from contextlib import asynccontextmanager
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

# Database naming conventions for consistency
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

# Create metadata with naming convention
metadata = MetaData(naming_convention=NAMING_CONVENTION)

# Create declarative base
Base = declarative_base(metadata=metadata)

# Convert sync database URL to async
def get_async_database_url() -> str:
    """Convert postgresql:// to postgresql+asyncpg://"""
    db_url = settings.database_url
    if db_url.startswith("postgresql://"):
        return db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return db_url

# Create async engine
engine = create_async_engine(
    get_async_database_url(),
    echo=settings.db_echo,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    pool_timeout=settings.db_pool_timeout,
    pool_pre_ping=True,  # Verify connections before using
    poolclass=NullPool if settings.is_testing else None,  # Disable pooling in tests
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


class Database:
    """Database connection manager"""
    
    def __init__(self):
        self.engine = engine
        self.session_factory = AsyncSessionLocal
        self._connected = False
    
    async def connect(self):
        """Initialize database connection"""
        try:
            async with self.engine.begin() as conn:
                await conn.execute("SELECT 1")
            self._connected = True
            logger.info("Database connected successfully")
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise
    
    async def disconnect(self):
        """Close database connection"""
        await self.engine.dispose()
        self._connected = False
        logger.info("Database disconnected")
    
    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get database session context manager"""
        async with self.session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    async def execute(self, query: str):
        """Execute raw SQL query"""
        async with self.session() as session:
            return await session.execute(query)
    
    async def health_check(self) -> bool:
        """Check database health"""
        try:
            async with self.engine.begin() as conn:
                await conn.execute("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False

# Session dependency for FastAPI
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get database session.
    Usage in FastAPI:
        @app.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            # Set current user ID for RLS if available
            # This will be set from JWT token in actual requests
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Context manager for database session.
    Usage:
        async with get_db_session() as session:
            result = await session.execute(...)
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

async def set_current_user_id(session: AsyncSession, user_id: Optional[str]):
    """
    Set the current user ID for Row Level Security.
    This is called at the beginning of each request with a valid JWT.
    """
    if user_id:
        await session.execute(f"SET LOCAL app.current_user_id = '{user_id}'")
    else:
        await session.execute("RESET app.current_user_id")

async def init_db():
    """Initialize database (create tables if they don't exist)"""
    async with engine.begin() as conn:
        # In production, use Alembic migrations instead
        if settings.is_development:
            await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables created")

async def close_db():
    """Close database connections"""
    await engine.dispose()
    logger.info("Database connections closed")

# Health check query
async def check_database_health() -> bool:
    """Check if database is accessible"""
    try:
        async with AsyncSessionLocal() as session:
            await session.execute("SELECT 1")
            return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False