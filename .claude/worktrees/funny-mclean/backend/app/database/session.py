"""
Database session management.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool, QueuePool
from contextlib import contextmanager
from typing import Generator

from app.core.config import settings

# Create database engine with connection pooling
engine = create_engine(
    settings.DATABASE_URL,
    poolclass=QueuePool,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_pre_ping=True,  # Verify connections before using
    echo=settings.DEBUG,  # Log SQL statements in debug mode
)

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency to get database session.
    Usage: db: Session = Depends(get_db)
    """
    db = SessionLocal()
    try:
        # Set current user ID for RLS (will be set from JWT in production)
        # db.execute(f"SET app.current_user_id = '{user_id}'")
        yield db
    finally:
        db.close()


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    Context manager for database session.
    Usage: with get_db_session() as db: ...
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def init_db():
    """Initialize database with tables and default data."""
    from app.models.portfolio import Base, Benchmark
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Add default benchmarks
    with get_db_session() as db:
        # Check if benchmarks already exist
        existing = db.query(Benchmark).first()
        if not existing:
            benchmarks = [
                Benchmark(symbol="SPY", name="SPDR S&P 500 ETF", 
                         description="Tracks the S&P 500 index"),
                Benchmark(symbol="QQQ", name="Invesco QQQ Trust", 
                         description="Tracks the NASDAQ-100 index"),
                Benchmark(symbol="AGG", name="iShares Core US Aggregate Bond ETF", 
                         description="Tracks the US bond market"),
                Benchmark(symbol="VTI", name="Vanguard Total Stock Market ETF", 
                         description="Tracks the entire US stock market"),
            ]
            db.add_all(benchmarks)
            db.commit()
            print("Default benchmarks added")


def close_db():
    """Close database connections."""
    engine.dispose()