"""
Enhanced Security Utilities

JWT token creation, validation, and security-related utility functions.
"""

import logging
import hashlib
import secrets
import uuid
from typing import Optional, Dict, Any, Union
from datetime import datetime, timedelta

from jose import jwt, JWTError
from passlib.context import CryptContext
from cryptography.fernet import Fernet

from app.core.config import settings
from app.schemas.auth import TokenType, TokenPayload

logger = logging.getLogger(__name__)

# Password context for hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Encryption for sensitive data
def get_encryption_key() -> bytes:
    """Get or generate encryption key"""
    key = settings.SECRET_KEY.get_secret_value().encode()
    # Use first 32 bytes of secret key for Fernet
    return hashlib.sha256(key).digest()[:32]

# Initialize Fernet cipher
fernet = Fernet(Fernet.generate_key())


class SecurityUtils:
    """Security utility functions"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using bcrypt"""
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def generate_secure_token(length: int = 32) -> str:
        """Generate cryptographically secure random token"""
        return secrets.token_urlsafe(length)
    
    @staticmethod
    def generate_session_id() -> str:
        """Generate secure session ID"""
        return f"sess_{SecurityUtils.generate_secure_token(32)}"
    
    @staticmethod
    def generate_reset_token() -> str:
        """Generate password reset token"""
        return f"reset_{SecurityUtils.generate_secure_token(24)}"
    
    @staticmethod
    def hash_token(token: str) -> str:
        """Hash token for secure storage"""
        return hashlib.sha256(token.encode()).hexdigest()
    
    @staticmethod
    def encrypt_data(data: str) -> str:
        """Encrypt sensitive data"""
        try:
            return fernet.encrypt(data.encode()).decode()
        except Exception as e:
            logger.error(f"Encryption failed: {str(e)}")
            raise
    
    @staticmethod
    def decrypt_data(encrypted_data: str) -> str:
        """Decrypt sensitive data"""
        try:
            return fernet.decrypt(encrypted_data.encode()).decode()
        except Exception as e:
            logger.error(f"Decryption failed: {str(e)}")
            raise
    
    @staticmethod
    def is_strong_password(password: str) -> tuple[bool, list[str]]:
        """Check password strength and return validation messages"""
        issues = []
        
        if len(password) < settings.MIN_PASSWORD_LENGTH:
            issues.append(f"Password must be at least {settings.MIN_PASSWORD_LENGTH} characters long")
        
        if not any(c.isupper() for c in password):
            issues.append("Password must contain at least one uppercase letter")
        
        if not any(c.islower() for c in password):
            issues.append("Password must contain at least one lowercase letter")
        
        if not any(c.isdigit() for c in password):
            issues.append("Password must contain at least one digit")
        
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            issues.append("Password must contain at least one special character")
        
        # Check for common patterns
        common_patterns = ["123", "abc", "password", "admin", "user"]
        if any(pattern in password.lower() for pattern in common_patterns):
            issues.append("Password contains common patterns")
        
        return len(issues) == 0, issues


class JWTManager:
    """JWT token management utilities"""
    
    @staticmethod
    def create_access_token(
        user_id: str,
        email: str = None,
        session_id: str = None,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create JWT access token"""
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        # Generate unique JWT ID for blacklisting
        jti = str(uuid.uuid4())
        
        payload = {
            "sub": user_id,
            "email": email,
            "type": TokenType.ACCESS,
            "jti": jti,
            "session_id": session_id,
            "exp": expire,
            "iat": datetime.utcnow(),
            "iss": "financial-planner",
            "aud": "financial-planner-api"
        }
        
        try:
            # Handle both SecretStr and regular string secret keys
            secret_key = settings.SECRET_KEY
            if hasattr(secret_key, 'get_secret_value'):
                secret_key = secret_key.get_secret_value()
            
            encoded_jwt = jwt.encode(
                payload,
                secret_key,
                algorithm=settings.ALGORITHM
            )
            return encoded_jwt
        except Exception as e:
            logger.error(f"Failed to create access token: {str(e)}")
            raise
    
    @staticmethod
    def create_refresh_token(
        user_id: str,
        session_id: str = None,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create JWT refresh token"""
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        
        # Generate unique JWT ID for blacklisting
        jti = str(uuid.uuid4())
        
        payload = {
            "sub": user_id,
            "type": TokenType.REFRESH,
            "jti": jti,
            "session_id": session_id,
            "exp": expire,
            "iat": datetime.utcnow(),
            "iss": "financial-planner",
            "aud": "financial-planner-api"
        }
        
        try:
            # Handle both SecretStr and regular string secret keys
            secret_key = settings.SECRET_KEY
            if hasattr(secret_key, 'get_secret_value'):
                secret_key = secret_key.get_secret_value()
            
            encoded_jwt = jwt.encode(
                payload,
                secret_key,
                algorithm=settings.ALGORITHM
            )
            return encoded_jwt
        except Exception as e:
            logger.error(f"Failed to create refresh token: {str(e)}")
            raise
    
    @staticmethod
    def decode_token(token: str, verify_exp: bool = True) -> Optional[Dict[str, Any]]:
        """Decode and validate JWT token"""
        
        try:
            options = {}
            if not verify_exp:
                options["verify_exp"] = False
            
            # Handle both SecretStr and regular string secret keys
            secret_key = settings.SECRET_KEY
            if hasattr(secret_key, 'get_secret_value'):
                secret_key = secret_key.get_secret_value()
            
            payload = jwt.decode(
                token,
                secret_key,
                algorithms=[settings.ALGORITHM],
                options=options
            )
            
            return payload
            
        except JWTError as e:
            logger.warning(f"JWT decode error: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Token decode error: {str(e)}")
            return None
    
    @staticmethod
    def extract_jti(token: str) -> Optional[str]:
        """Extract JTI from token without full validation"""
        try:
            # Decode without verification for logout scenarios
            # Handle both SecretStr and regular string secret keys
            secret_key = settings.SECRET_KEY
            if hasattr(secret_key, 'get_secret_value'):
                secret_key = secret_key.get_secret_value()
            
            payload = jwt.decode(
                token,
                secret_key,
                algorithms=[settings.ALGORITHM],
                options={"verify_exp": False, "verify_aud": False, "verify_iss": False}
            )
            return payload.get("jti")
        except Exception:
            return None
    
    @staticmethod
    def get_token_expiry(token: str) -> Optional[datetime]:
        """Get token expiry time"""
        try:
            # Handle both SecretStr and regular string secret keys
            secret_key = settings.SECRET_KEY
            if hasattr(secret_key, 'get_secret_value'):
                secret_key = secret_key.get_secret_value()
            
            payload = jwt.decode(
                token,
                secret_key,
                algorithms=[settings.ALGORITHM],
                options={"verify_exp": False}
            )
            exp_timestamp = payload.get("exp")
            if exp_timestamp:
                return datetime.fromtimestamp(exp_timestamp)
            return None
        except Exception:
            return None


class RateLimiter:
    """Rate limiting utilities"""
    
    def __init__(self):
        self._attempts = {}
        self._blocked = {}
    
    def is_rate_limited(self, key: str, max_attempts: int = 5, window_minutes: int = 15) -> bool:
        """Check if key is rate limited"""
        now = datetime.utcnow()
        window_start = now - timedelta(minutes=window_minutes)
        
        # Clean old attempts
        if key in self._attempts:
            self._attempts[key] = [
                attempt for attempt in self._attempts[key] 
                if attempt > window_start
            ]
        
        # Check if blocked
        if key in self._blocked:
            if self._blocked[key] > now:
                return True
            else:
                del self._blocked[key]
        
        # Count attempts in window
        current_attempts = len(self._attempts.get(key, []))
        
        if current_attempts >= max_attempts:
            # Block for window duration
            self._blocked[key] = now + timedelta(minutes=window_minutes)
            return True
        
        return False
    
    def record_attempt(self, key: str) -> None:
        """Record an attempt for rate limiting"""
        now = datetime.utcnow()
        
        if key not in self._attempts:
            self._attempts[key] = []
        
        self._attempts[key].append(now)
    
    def reset_attempts(self, key: str) -> None:
        """Reset attempts for a key (e.g., after successful authentication)"""
        if key in self._attempts:
            del self._attempts[key]
        if key in self._blocked:
            del self._blocked[key]


class IPValidator:
    """IP address validation utilities"""
    
    @staticmethod
    def is_valid_ip(ip: str) -> bool:
        """Validate IP address format"""
        try:
            import ipaddress
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False
    
    @staticmethod
    def is_private_ip(ip: str) -> bool:
        """Check if IP is in private range"""
        try:
            import ipaddress
            ip_obj = ipaddress.ip_address(ip)
            return ip_obj.is_private
        except ValueError:
            return False
    
    @staticmethod
    def is_suspicious_ip(ip: str) -> bool:
        """Check if IP appears suspicious (basic checks)"""
        if not IPValidator.is_valid_ip(ip):
            return True
        
        # Add more sophisticated checks here
        # - Check against known malicious IP lists
        # - Check for TOR exit nodes
        # - Check for datacenter/VPN ranges
        
        return False


# Global rate limiter instance
rate_limiter = RateLimiter()