"""
Advanced Database Infrastructure with PostgreSQL and TimescaleDB Support

Provides enhanced database management, connection pooling, and time-series capabilities.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncContextManager, AsyncIterator, Dict, List, Optional, Type

import asyncpg
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import NullPool, QueuePool

from app.core.config import settings

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    """Enhanced base class for all database models"""
    pass


class DatabaseManager:
    """
    Advanced database manager with connection pooling, health checks, and transaction management
    """
    
    def __init__(self):
        self._engine = None
        self._async_engine = None
        self._session_factory = None
        self._async_session_factory = None
        self._is_connected = False
        
    async def initialize(self) -> None:
        """Initialize database connections and session factories"""
        try:
            # Create async engine with advanced configuration
            self._async_engine = create_async_engine(
                settings.DATABASE_URL,
                pool_size=settings.DATABASE_POOL_SIZE,
                max_overflow=settings.DATABASE_MAX_OVERFLOW,
                pool_timeout=settings.DATABASE_POOL_TIMEOUT,
                pool_pre_ping=True,
                pool_recycle=3600,  # 1 hour
                echo=settings.DEBUG,
                echo_pool=settings.DEBUG,
            )
            
            # Create synchronous engine for admin operations
            sync_database_url = settings.DATABASE_URL.replace("+aiosqlite", "")
            if settings.DATABASE_URL.startswith("postgresql"):
                sync_database_url = settings.DATABASE_URL.replace("+asyncpg", "+psycopg2")
            
            self._engine = create_engine(
                sync_database_url,
                pool_size=settings.DATABASE_POOL_SIZE,
                max_overflow=settings.DATABASE_MAX_OVERFLOW,
                pool_timeout=settings.DATABASE_POOL_TIMEOUT,
                pool_pre_ping=True,
                pool_recycle=3600,
                echo=settings.DEBUG,
            )
            
            # Create session factories
            self._async_session_factory = async_sessionmaker(
                bind=self._async_engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autoflush=True,
                autocommit=False
            )
            
            self._session_factory = sessionmaker(
                bind=self._engine,
                expire_on_commit=False,
                autoflush=True,
                autocommit=False
            )
            
            # Test connection
            await self._test_connection()
            self._is_connected = True
            logger.info("Database manager initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database manager: {e}")
            raise
    
    async def _test_connection(self) -> None:
        """Test database connectivity"""
        async with self._async_engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
    
    @asynccontextmanager
    async def get_async_session(self) -> AsyncIterator[AsyncSession]:
        """Get async database session with automatic cleanup"""
        if not self._is_connected:
            await self.initialize()
            
        session = self._async_session_factory()
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
    
    @asynccontextmanager
    def get_session(self) -> AsyncContextManager[Session]:
        """Get synchronous database session with automatic cleanup"""
        if not self._is_connected:
            raise RuntimeError("Database not initialized")
            
        session = self._session_factory()
        try:
            yield session
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    async def execute_raw_query(
        self, 
        query: str, 
        parameters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Execute raw SQL query and return results"""
        async with self._async_engine.begin() as conn:
            result = await conn.execute(text(query), parameters or {})
            if result.returns_rows:
                return [dict(row._mapping) for row in result]
            return []
    
    async def check_health(self) -> Dict[str, Any]:
        """Comprehensive health check for database connectivity"""
        try:
            start_time = asyncio.get_event_loop().time()
            
            async with self._async_engine.begin() as conn:
                # Test basic connectivity
                await conn.execute(text("SELECT 1"))
                
                # Test transaction capability
                async with conn.begin():
                    await conn.execute(text("SELECT 1"))
            
            response_time = (asyncio.get_event_loop().time() - start_time) * 1000
            
            # Get pool statistics if available
            pool_info = {}
            if hasattr(self._async_engine.pool, 'size'):
                pool_info = {
                    'pool_size': self._async_engine.pool.size(),
                    'checked_in': self._async_engine.pool.checkedin(),
                    'checked_out': self._async_engine.pool.checkedout(),
                    'overflow': getattr(self._async_engine.pool, 'overflow', 0),
                }
            
            return {
                'status': 'healthy',
                'response_time_ms': round(response_time, 2),
                'pool_info': pool_info,
                'database_url': settings.DATABASE_URL.split('@')[-1] if '@' in settings.DATABASE_URL else 'local'
            }
            
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'database_url': settings.DATABASE_URL.split('@')[-1] if '@' in settings.DATABASE_URL else 'local'
            }
    
    async def shutdown(self) -> None:
        """Gracefully shutdown database connections"""
        if self._async_engine:
            await self._async_engine.dispose()
        if self._engine:
            self._engine.dispose()
        self._is_connected = False
        logger.info("Database manager shutdown completed")


class TimescaleDBManager(DatabaseManager):
    """
    Enhanced database manager with TimescaleDB time-series capabilities
    """
    
    def __init__(self):
        super().__init__()
        self._hypertables_created = False
    
    async def initialize(self) -> None:
        """Initialize with TimescaleDB extensions and hypertables"""
        await super().initialize()
        await self._setup_timescaledb()
    
    async def _setup_timescaledb(self) -> None:
        """Setup TimescaleDB extensions and hypertables"""
        try:
            # Enable TimescaleDB extension
            await self.execute_raw_query("CREATE EXTENSION IF NOT EXISTS timescaledb;")
            
            # Create hypertables for time-series data
            await self._create_hypertables()
            
            logger.info("TimescaleDB setup completed successfully")
            
        except Exception as e:
            logger.warning(f"TimescaleDB setup failed (may not be available): {e}")
    
    async def _create_hypertables(self) -> None:
        """Create hypertables for time-series tables"""
        hypertable_configs = [
            {
                'table': 'market_data',
                'time_column': 'time',
                'chunk_time_interval': '1 day'
            },
            {
                'table': 'portfolio_performance',
                'time_column': 'timestamp',
                'chunk_time_interval': '1 day'
            },
            {
                'table': 'simulation_results',
                'time_column': 'created_at',
                'chunk_time_interval': '7 days'
            }
        ]
        
        for config in hypertable_configs:
            try:
                # Check if table exists and is not already a hypertable
                check_query = """
                    SELECT EXISTS (
                        SELECT 1 FROM information_schema.tables 
                        WHERE table_name = :table_name
                    ) AS table_exists,
                    EXISTS (
                        SELECT 1 FROM timescaledb_information.hypertables 
                        WHERE hypertable_name = :table_name
                    ) AS is_hypertable;
                """
                
                result = await self.execute_raw_query(
                    check_query, 
                    {'table_name': config['table']}
                )
                
                if result and result[0]['table_exists'] and not result[0]['is_hypertable']:
                    # Create hypertable
                    create_query = f"""
                        SELECT create_hypertable(
                            '{config['table']}',
                            '{config['time_column']}',
                            chunk_time_interval => INTERVAL '{config['chunk_time_interval']}'
                        );
                    """
                    await self.execute_raw_query(create_query)
                    logger.info(f"Created hypertable for {config['table']}")
                    
            except Exception as e:
                logger.warning(f"Failed to create hypertable for {config['table']}: {e}")
        
        self._hypertables_created = True
    
    async def create_continuous_aggregate(
        self, 
        view_name: str,
        base_table: str,
        time_column: str,
        bucket_width: str,
        aggregation_query: str
    ) -> None:
        """Create TimescaleDB continuous aggregate view"""
        try:
            query = f"""
                CREATE MATERIALIZED VIEW {view_name}
                WITH (timescaledb.continuous) AS
                SELECT 
                    time_bucket('{bucket_width}', {time_column}) AS bucket,
                    {aggregation_query}
                FROM {base_table}
                GROUP BY bucket
                ORDER BY bucket;
            """
            
            await self.execute_raw_query(query)
            
            # Add refresh policy
            policy_query = f"""
                SELECT add_continuous_aggregate_policy(
                    '{view_name}',
                    start_offset => INTERVAL '1 day',
                    end_offset => INTERVAL '1 hour',
                    schedule_interval => INTERVAL '1 hour'
                );
            """
            await self.execute_raw_query(policy_query)
            
            logger.info(f"Created continuous aggregate: {view_name}")
            
        except Exception as e:
            logger.error(f"Failed to create continuous aggregate {view_name}: {e}")
            raise
    
    async def optimize_hypertables(self) -> None:
        """Optimize hypertables with compression and retention policies"""
        try:
            # Enable compression on older chunks
            compression_configs = [
                {'table': 'market_data', 'compress_after': '7 days'},
                {'table': 'portfolio_performance', 'compress_after': '30 days'},
                {'table': 'simulation_results', 'compress_after': '90 days'}
            ]
            
            for config in compression_configs:
                # Add compression policy
                policy_query = f"""
                    SELECT add_compression_policy(
                        '{config['table']}',
                        compress_after => INTERVAL '{config['compress_after']}'
                    );
                """
                try:
                    await self.execute_raw_query(policy_query)
                    logger.info(f"Added compression policy for {config['table']}")
                except Exception as e:
                    logger.warning(f"Failed to add compression policy for {config['table']}: {e}")
            
            # Add retention policies
            retention_configs = [
                {'table': 'market_data', 'drop_after': '5 years'},
                {'table': 'portfolio_performance', 'drop_after': '10 years'},
                {'table': 'simulation_results', 'drop_after': '7 years'}
            ]
            
            for config in retention_configs:
                policy_query = f"""
                    SELECT add_retention_policy(
                        '{config['table']}',
                        drop_after => INTERVAL '{config['drop_after']}'
                    );
                """
                try:
                    await self.execute_raw_query(policy_query)
                    logger.info(f"Added retention policy for {config['table']}")
                except Exception as e:
                    logger.warning(f"Failed to add retention policy for {config['table']}: {e}")
                    
        except Exception as e:
            logger.error(f"Failed to optimize hypertables: {e}")


# Global database managers
db_manager = DatabaseManager()
timescale_manager = TimescaleDBManager()


async def get_db() -> AsyncIterator[AsyncSession]:
    """Dependency injection for async database sessions"""
    async with db_manager.get_async_session() as session:
        yield session


async def get_timescale_db() -> AsyncIterator[AsyncSession]:
    """Dependency injection for TimescaleDB sessions"""
    async with timescale_manager.get_async_session() as session:
        yield session