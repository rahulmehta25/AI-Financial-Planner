"""
API Dependencies

Dependencies for FastAPI endpoints including authentication, database access,
and other common requirements.
"""

import logging
from typing import Generator, Optional, List
from datetime import datetime
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings
from app.core.exceptions import AuthenticationError, AuthorizationError
from app.database.base import get_db_session
from app.models.user import User
from app.models.auth import TokenBlacklist, UserSession

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
        token = credentials.credentials
        
        # Decode JWT token
        payload = jwt.decode(
            token,
            settings.SECRET_KEY.get_secret_value(),
            algorithms=[settings.ALGORITHM]
        )
        
        user_id: str = payload.get("sub")
        jti: str = payload.get("jti")
        
        if user_id is None:
            raise AuthenticationError("Invalid token payload")
        
        # Check if token is blacklisted
        if jti:
            blacklist_query = select(TokenBlacklist).where(
                and_(
                    TokenBlacklist.jti == jti,
                    TokenBlacklist.expires_at > datetime.utcnow()
                )
            )
            blacklisted_token = await db.execute(blacklist_query)
            if blacklisted_token.scalar_one_or_none():
                raise AuthenticationError("Token has been revoked")
        
        # Get user from database
        user_query = select(User).where(User.id == user_id)
        result = await db.execute(user_query)
        user = result.scalar_one_or_none()
        
        if not user:
            raise AuthenticationError("User not found")
        
        if not user.is_active:
            raise AuthenticationError("Inactive user account")
        
        if not user.email_verified:
            raise AuthenticationError("Unverified user account")
        
        return user
        
    except JWTError as e:
        logger.warning(f"JWT error during authentication: {str(e)}")
        raise AuthenticationError("Invalid authentication token")
    except AuthenticationError:
        raise
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
    
    if not current_user.email_verified:
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


async def validate_session(
    session_id: str,
    user_id: str,
    db: AsyncSession
) -> Optional[UserSession]:
    """Validate and return user session if active"""
    
    try:
        query = select(UserSession).where(
            and_(
                UserSession.session_id == session_id,
                UserSession.user_id == user_id,
                UserSession.is_active == True,
                UserSession.expires_at > datetime.utcnow()
            )
        )
        
        result = await db.execute(query)
        session = result.scalar_one_or_none()
        
        if session:
            # Update last activity
            session.refresh_activity()
            await db.commit()
        
        return session
        
    except Exception as e:
        logger.error(f"Session validation error: {str(e)}")
        return None


async def blacklist_token(
    jti: str,
    user_id: str,
    token_type: str,
    expires_at: datetime,
    reason: str = None,
    db: AsyncSession = None
) -> bool:
    """Add token to blacklist"""
    
    try:
        blacklist_entry = TokenBlacklist(
            jti=jti,
            user_id=user_id,
            token_type=token_type,
            expires_at=expires_at,
            reason=reason
        )
        
        db.add(blacklist_entry)
        await db.commit()
        
        logger.info(f"Token {jti} blacklisted for user {user_id}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to blacklist token: {str(e)}")
        await db.rollback()
        return False


async def terminate_user_session(
    session_id: str,
    user_id: str,
    reason: str = None,
    db: AsyncSession = None
) -> bool:
    """Terminate a specific user session"""
    
    try:
        query = select(UserSession).where(
            and_(
                UserSession.session_id == session_id,
                UserSession.user_id == user_id,
                UserSession.is_active == True
            )
        )
        
        result = await db.execute(query)
        session = result.scalar_one_or_none()
        
        if session:
            session.terminate(reason)
            await db.commit()
            logger.info(f"Session {session_id} terminated for user {user_id}")
            return True
        
        return False
        
    except Exception as e:
        logger.error(f"Failed to terminate session: {str(e)}")
        await db.rollback()
        return False


async def terminate_all_user_sessions(
    user_id: str,
    exclude_session_id: str = None,
    reason: str = "logout_all",
    db: AsyncSession = None
) -> int:
    """Terminate all active sessions for a user"""
    
    try:
        conditions = [
            UserSession.user_id == user_id,
            UserSession.is_active == True
        ]
        
        if exclude_session_id:
            conditions.append(UserSession.session_id != exclude_session_id)
        
        query = select(UserSession).where(and_(*conditions))
        result = await db.execute(query)
        sessions = result.scalars().all()
        
        terminated_count = 0
        for session in sessions:
            session.terminate(reason)
            terminated_count += 1
        
        if terminated_count > 0:
            await db.commit()
            logger.info(f"Terminated {terminated_count} sessions for user {user_id}")
        
        return terminated_count
        
    except Exception as e:
        logger.error(f"Failed to terminate user sessions: {str(e)}")
        await db.rollback()
        return 0


async def get_user_active_sessions(
    user_id: str,
    db: AsyncSession
) -> List[UserSession]:
    """Get all active sessions for a user"""
    
    try:
        query = select(UserSession).where(
            and_(
                UserSession.user_id == user_id,
                UserSession.is_active == True,
                UserSession.expires_at > datetime.utcnow()
            )
        ).order_by(UserSession.last_activity.desc())
        
        result = await db.execute(query)
        return result.scalars().all()
        
    except Exception as e:
        logger.error(f"Failed to get user sessions: {str(e)}")
        return []


async def get_current_user_from_token(token: str, db: AsyncSession) -> Optional[User]:
    """Get current user from token string (for WebSocket authentication)"""
    try:
        # Decode JWT token
        payload = jwt.decode(
            token,
            settings.SECRET_KEY.get_secret_value(),
            algorithms=[settings.ALGORITHM]
        )
        
        user_id: str = payload.get("sub")
        jti: str = payload.get("jti")
        
        if user_id is None:
            return None
        
        # Check if token is blacklisted
        if jti:
            blacklist_query = select(TokenBlacklist).where(
                and_(
                    TokenBlacklist.jti == jti,
                    TokenBlacklist.expires_at > datetime.utcnow()
                )
            )
            blacklisted_token = await db.execute(blacklist_query)
            if blacklisted_token.scalar_one_or_none():
                return None
        
        # Get user from database
        user_query = select(User).where(User.id == user_id)
        result = await db.execute(user_query)
        user = result.scalar_one_or_none()
        
        if not user or not user.is_active:
            return None
        
        return user
        
    except JWTError:
        return None
    except Exception as e:
        logger.error(f"Token authentication error: {str(e)}")
        return None