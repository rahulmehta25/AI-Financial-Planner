"""
API Dependencies

Dependencies for FastAPI endpoints including authentication, database access,
and other common requirements.
"""

import logging
from typing import Generator, Optional
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings
from app.core.exceptions import AuthenticationError, AuthorizationError
from app.database.base import get_db_session
from app.database.models import User

logger = logging.getLogger(__name__)

# Security setup
security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def get_db() -> Generator[AsyncSession, None, None]:
    """Dependency for database session"""
    async for session in get_db_session():
        yield session


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get current authenticated user from JWT token"""
    
    try:
        # Decode JWT token
        payload = jwt.decode(
            credentials.credentials,
            settings.SECRET_KEY.get_secret_value(),
            algorithms=[settings.ALGORITHM]
        )
        
        user_id: str = payload.get("sub")
        if user_id is None:
            raise AuthenticationError("Invalid token payload")
        
        # Get user from database
        # TODO: Implement actual database query when models are ready
        # For now, return a mock user
        user = User(
            id=user_id,
            email="user@example.com",
            first_name="Test",
            last_name="User",
            hashed_password="",
            is_active=True,
            is_verified=True
        )
        
        if not user.is_active:
            raise AuthenticationError("Inactive user account")
        
        if not user.is_verified:
            raise AuthenticationError("Unverified user account")
        
        return user
        
    except JWTError:
        raise AuthenticationError("Invalid authentication token")
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise AuthenticationError("Authentication failed")


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current active user"""
    
    if not current_user.is_active:
        raise AuthenticationError("Inactive user account")
    
    return current_user


async def get_current_verified_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """Get current verified user"""
    
    if not current_user.is_verified:
        raise AuthenticationError("Unverified user account")
    
    return current_user


async def get_current_superuser(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """Get current superuser"""
    
    if not current_user.is_superuser:
        raise AuthorizationError("Insufficient permissions")
    
    return current_user


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate password hash"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[int] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    
    if expires_delta:
        from datetime import datetime, timedelta
        expire = datetime.utcnow() + timedelta(minutes=expires_delta)
    else:
        from datetime import datetime, timedelta
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.SECRET_KEY.get_secret_value(), 
        algorithm=settings.ALGORITHM
    )
    
    return encoded_jwt


async def get_request_id(request: Request) -> str:
    """Get unique request ID for tracking"""
    return getattr(request.state, "request_id", "unknown")


async def get_user_agent(request: Request) -> str:
    """Get user agent string"""
    return request.headers.get("user-agent", "unknown")


async def get_client_ip(request: Request) -> str:
    """Get client IP address"""
    # Check for forwarded headers (e.g., from proxy)
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    
    # Check for real IP header
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip
    
    # Fall back to direct client IP
    return request.client.host if request.client else "unknown"


async def require_plan_ownership(
    plan_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> bool:
    """Require that the user owns the specified plan"""
    
    # TODO: Implement actual database lookup when models are ready
    # For now, allow access to any plan
    return True


async def require_simulation_ownership(
    simulation_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> bool:
    """Require that the user owns the specified simulation"""
    
    # TODO: Implement actual database lookup when models are ready
    # For now, allow access to any simulation
    return True


def rate_limit_exceeded(user_id: str, endpoint: str) -> bool:
    """Check if rate limit is exceeded for user/endpoint"""
    
    # TODO: Implement actual rate limiting logic
    # For now, always allow requests
    return False


async def audit_log_dependency(
    action: str,
    resource_type: str,
    resource_id: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    request: Request = Depends(),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Dependency for audit logging"""
    
    audit_data = {
        "user_id": current_user.id,
        "action": action,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "ip_address": await get_client_ip(request),
        "user_agent": await get_user_agent(request),
        "request_id": await get_request_id(request),
        "timestamp": None  # Will be set by the audit service
    }
    
    return audit_data