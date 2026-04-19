"""Database engine and session factory for the AIFP backend.

Connects to the shared portfolio Cloud SQL Postgres instance (osmoti-auth:us-east1:portfolio-pg),
database `aifp`. Uses asyncpg via SQLAlchemy 2.0 async APIs.

Connection options:
- Production: connect via Cloud SQL Auth Proxy on localhost:5432
- Development: connect via Cloud SQL public IP with sslmode=require (after running scripts/db-proxy.sh
  or adding your IP to authorized_networks)

Required env: DATABASE_URL. See .env.example.
"""
from __future__ import annotations

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from .config import get_settings

_settings = get_settings()

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def _build_engine() -> AsyncEngine:
    if not _settings.database_url:
        raise RuntimeError(
            "DATABASE_URL is not set. Either run scripts/db-proxy.sh and use "
            "postgresql+asyncpg://postgres:<pwd>@127.0.0.1:5432/aifp, or set the public "
            "IP form. See api/README.md for setup."
        )
    return create_async_engine(
        _settings.database_url,
        pool_size=5,
        max_overflow=5,
        pool_pre_ping=True,
        echo=False,
    )


def get_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        _engine = _build_engine()
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            bind=get_engine(),
            expire_on_commit=False,
            autoflush=False,
        )
    return _session_factory


async def get_db() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency. Use as: db: AsyncSession = Depends(get_db)."""
    factory = get_session_factory()
    async with factory() as session:
        yield session
