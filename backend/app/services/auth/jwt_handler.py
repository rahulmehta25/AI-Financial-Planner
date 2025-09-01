"""
JWT token handling for authentication
"""
from typing import Optional, Dict, Any
from datetime import datetime, timedelta, timezone
import jwt
from passlib.context import CryptContext

from app.core.config import settings

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class JWTHandler:
    """Handle JWT token creation and validation"""
    
    def __init__(self):
        self.secret_key = settings.jwt_secret_key
        self.algorithm = settings.jwt_algorithm
        self.access_token_expire_minutes = settings.jwt_expiration_hours * 60  # Convert hours to minutes
        self.refresh_token_expire_days = settings.refresh_token_expiration_days
    
    def create_access_token(self, user_id: str, email: str) -> str:
        """Create JWT access token"""
        expires_delta = timedelta(minutes=self.access_token_expire_minutes)
        expire = datetime.now(timezone.utc) + expires_delta
        
        payload = {
            "sub": user_id,  # subject (user id)
            "email": email,
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "type": "access"
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def create_refresh_token(self, user_id: str) -> str:
        """Create JWT refresh token"""
        expires_delta = timedelta(days=self.refresh_token_expire_days)
        expire = datetime.now(timezone.utc) + expires_delta
        
        payload = {
            "sub": user_id,
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "type": "refresh"
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def decode_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Decode and validate JWT token"""
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Hash a password"""
        return pwd_context.hash(password)


# Global instance
jwt_handler = JWTHandler()