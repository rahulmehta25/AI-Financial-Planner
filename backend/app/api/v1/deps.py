"""
FastAPI dependency injection
"""
from typing import Generator, Optional
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import jwt
from jwt.exceptions import InvalidTokenError

from app.core.config import settings
from app.core.database import Database
from app.models.user import User
from app.services.data_providers.cached_provider import CachedDataProvider

# Security scheme
security = HTTPBearer()


async def get_db(request: Request) -> AsyncSession:
    """
    Dependency to get database session
    """
    if not hasattr(request.app.state, "db"):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not initialized"
        )
    
    db: Database = request.app.state.db
    async with db.session() as session:
        try:
            yield session
        finally:
            await session.close()


async def get_data_provider(request: Request) -> CachedDataProvider:
    """
    Dependency to get data provider instance
    """
    if not hasattr(request.app.state, "data_provider"):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Data provider not initialized"
        )
    
    return request.app.state.data_provider


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Dependency to get current authenticated user
    """
    token = credentials.credentials
    
    try:
        # Decode JWT token
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        user_id: str = payload.get("sub")
        
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user from database
    query = select(User).where(User.id == user_id)
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    
    return user


async def get_current_active_superuser(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency to get current superuser
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user


class RateLimiter:
    """
    Rate limiting dependency
    """
    def __init__(self, calls: int = 10, period: int = 60):
        self.calls = calls
        self.period = period
        self.cache = {}
    
    async def __call__(self, request: Request):
        # Simple in-memory rate limiting
        # In production, use Redis for distributed rate limiting
        client_id = request.client.host
        
        # TODO: Implement proper rate limiting with Redis
        return True