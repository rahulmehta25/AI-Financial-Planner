"""
Security utilities for authentication and authorization
"""

from datetime import datetime, timedelta
from typing import Any, Union, Optional
from jose import jwt
from passlib.context import CryptContext
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = "HS256"


def create_access_token(
    subject: Union[str, Any], expires_delta: timedelta = None
) -> str:
    """Create JWT access token"""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode = {"exp": expire, "sub": str(subject)}
    # Handle both SecretStr and regular string secret keys
    secret_key = settings.SECRET_KEY
    if hasattr(secret_key, 'get_secret_value'):
        secret_key = secret_key.get_secret_value()
    
    encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=ALGORITHM)
    return encoded_jwt


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate password hash"""
    return pwd_context.hash(password)


def verify_token(token: str) -> Optional[str]:
    """Verify JWT token and return subject"""
    try:
        # Handle both SecretStr and regular string secret keys
        secret_key = settings.SECRET_KEY
        if hasattr(secret_key, 'get_secret_value'):
            secret_key = secret_key.get_secret_value()
        
        payload = jwt.decode(
            token, secret_key, algorithms=[ALGORITHM]
        )
        return payload.get("sub")
    except jwt.JWTError:
        return None