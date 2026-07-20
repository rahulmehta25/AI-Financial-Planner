"""
Authentication Module

Implements JWT, OAuth2, SAML, and Multi-Factor Authentication (MFA)
following OWASP best practices and financial services requirements.
"""

import secrets
import hashlib
import base64
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
from enum import Enum
import pyotp
import qrcode
from io import BytesIO
import jwt
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
from passlib.context import CryptContext
from fastapi import HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as redis
import json

from app.core.config import settings


class AuthType(Enum):
    """Authentication types"""
    JWT = "jwt"
    OAUTH2 = "oauth2"
    SAML = "saml"
    API_KEY = "api_key"
    MFA = "mfa"


class TokenType(Enum):
    """Token types for different purposes"""
    ACCESS = "access"
    REFRESH = "refresh"
    MFA = "mfa"
    PASSWORD_RESET = "password_reset"
    EMAIL_VERIFICATION = "email_verification"


class JWTHandler:
    """
    Enhanced JWT handler with refresh tokens, token rotation,
    and revocation support
    """
    
    def __init__(self):
        self.algorithm = "RS256"  # Use RS256 for better security
        self.access_token_expire = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        self.refresh_token_expire = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        self.redis_client = None
        
    async def init_redis(self):
        """Initialize Redis for token blacklisting"""
        self.redis_client = await redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )
    
    def create_token(
        self,
        subject: str,
        token_type: TokenType,
        expires_delta: Optional[timedelta] = None,
        additional_claims: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create a JWT token with specified type and claims"""
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            if token_type == TokenType.ACCESS:
                expire = datetime.utcnow() + self.access_token_expire
            elif token_type == TokenType.REFRESH:
                expire = datetime.utcnow() + self.refresh_token_expire
            elif token_type == TokenType.MFA:
                expire = datetime.utcnow() + timedelta(minutes=5)
            elif token_type == TokenType.PASSWORD_RESET:
                expire = datetime.utcnow() + timedelta(hours=1)
            else:
                expire = datetime.utcnow() + timedelta(hours=24)
        
        to_encode = {
            "sub": str(subject),
            "exp": expire,
            "iat": datetime.utcnow(),
            "jti": secrets.token_urlsafe(32),  # JWT ID for revocation
            "type": token_type.value
        }
        
        if additional_claims:
            to_encode.update(additional_claims)
        
        encoded_jwt = jwt.encode(
            to_encode,
            settings.SECRET_KEY.get_secret_value(),
            algorithm=self.algorithm
        )
        
        return encoded_jwt
    
    async def verify_token(
        self,
        token: str,
        token_type: TokenType,
        verify_blacklist: bool = True
    ) -> Optional[Dict[str, Any]]:
        """Verify and decode a JWT token"""
        
        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY.get_secret_value(),
                algorithms=[self.algorithm]
            )
            
            # Verify token type
            if payload.get("type") != token_type.value:
                return None
            
            # Check if token is blacklisted
            if verify_blacklist and self.redis_client:
                jti = payload.get("jti")
                if jti and await self.redis_client.exists(f"blacklist:{jti}"):
                    return None
            
            return payload
            
        except jwt.ExpiredSignatureError:
            return None
        except jwt.JWTError:
            return None
    
    async def revoke_token(self, token: str) -> bool:
        """Revoke a token by adding it to the blacklist"""
        
        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY.get_secret_value(),
                algorithms=[self.algorithm],
                options={"verify_exp": False}
            )
            
            jti = payload.get("jti")
            exp = payload.get("exp")
            
            if jti and exp and self.redis_client:
                # Calculate TTL for blacklist entry
                ttl = exp - datetime.utcnow().timestamp()
                if ttl > 0:
                    await self.redis_client.setex(
                        f"blacklist:{jti}",
                        int(ttl),
                        "revoked"
                    )
                    return True
            
            return False
            
        except Exception:
            return False
    
    def create_token_pair(
        self,
        subject: str,
        additional_claims: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, str]:
        """Create access and refresh token pair"""
        
        access_token = self.create_token(
            subject,
            TokenType.ACCESS,
            additional_claims=additional_claims
        )
        
        refresh_token = self.create_token(
            subject,
            TokenType.REFRESH,
            additional_claims=additional_claims
        )
        
        return access_token, refresh_token


class OAuth2Handler:
    """
    OAuth2 implementation for third-party authentication
    Supports Google, Microsoft, GitHub providers
    """
    
    PROVIDERS = {
        "google": {
            "auth_url": "https://accounts.google.com/o/oauth2/v2/auth",
            "token_url": "https://oauth2.googleapis.com/token",
            "user_info_url": "https://www.googleapis.com/oauth2/v1/userinfo",
            "scopes": ["openid", "email", "profile"]
        },
        "microsoft": {
            "auth_url": "https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
            "token_url": "https://login.microsoftonline.com/common/oauth2/v2.0/token",
            "user_info_url": "https://graph.microsoft.com/v1.0/me",
            "scopes": ["openid", "email", "profile"]
        },
        "github": {
            "auth_url": "https://github.com/login/oauth/authorize",
            "token_url": "https://github.com/login/oauth/access_token",
            "user_info_url": "https://api.github.com/user",
            "scopes": ["user:email"]
        }
    }
    
    def __init__(self):
        self.redis_client = None
    
    async def init_redis(self):
        """Initialize Redis for state management"""
        self.redis_client = await redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )
    
    def generate_authorization_url(
        self,
        provider: str,
        client_id: str,
        redirect_uri: str,
        state: Optional[str] = None
    ) -> str:
        """Generate OAuth2 authorization URL"""
        
        if provider not in self.PROVIDERS:
            raise ValueError(f"Unsupported provider: {provider}")
        
        config = self.PROVIDERS[provider]
        
        if not state:
            state = secrets.token_urlsafe(32)
        
        # Store state in Redis for verification
        if self.redis_client:
            self.redis_client.setex(
                f"oauth_state:{state}",
                300,  # 5 minutes
                json.dumps({
                    "provider": provider,
                    "redirect_uri": redirect_uri,
                    "timestamp": datetime.utcnow().isoformat()
                })
            )
        
        params = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": " ".join(config["scopes"]),
            "state": state,
            "access_type": "offline",
            "prompt": "consent"
        }
        
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{config['auth_url']}?{query_string}"
    
    async def verify_state(self, state: str) -> Optional[Dict[str, Any]]:
        """Verify OAuth2 state parameter"""
        
        if not self.redis_client:
            return None
        
        state_data = await self.redis_client.get(f"oauth_state:{state}")
        if state_data:
            await self.redis_client.delete(f"oauth_state:{state}")
            return json.loads(state_data)
        
        return None


class SAMLHandler:
    """
    SAML 2.0 implementation for enterprise SSO
    """
    
    def __init__(self):
        self.saml_settings = {}
        self.redis_client = None
    
    async def init_redis(self):
        """Initialize Redis for SAML session management"""
        self.redis_client = await redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )
    
    def create_saml_request(
        self,
        idp_url: str,
        sp_entity_id: str,
        acs_url: str
    ) -> str:
        """Create SAML authentication request"""
        
        request_id = f"id_{secrets.token_hex(16)}"
        issue_instant = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        
        saml_request = f'''
        <samlp:AuthnRequest 
            xmlns:samlp="urn:oasis:names:tc:SAML:2.0:protocol"
            xmlns:saml="urn:oasis:names:tc:SAML:2.0:assertion"
            ID="{request_id}"
            Version="2.0"
            IssueInstant="{issue_instant}"
            Destination="{idp_url}"
            AssertionConsumerServiceURL="{acs_url}"
            ProtocolBinding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST">
            <saml:Issuer>{sp_entity_id}</saml:Issuer>
        </samlp:AuthnRequest>
        '''
        
        # Base64 encode and URL encode
        encoded = base64.b64encode(saml_request.encode()).decode()
        return encoded
    
    def validate_saml_response(
        self,
        saml_response: str,
        expected_audience: str
    ) -> Optional[Dict[str, Any]]:
        """Validate SAML response and extract user attributes"""
        
        # This is a simplified implementation
        # In production, use python-saml or similar library
        
        try:
            decoded = base64.b64decode(saml_response)
            # Parse XML and validate signature
            # Extract user attributes
            
            return {
                "user_id": "extracted_user_id",
                "email": "user@example.com",
                "attributes": {}
            }
            
        except Exception:
            return None


class MFAHandler:
    """
    Multi-Factor Authentication handler
    Supports TOTP, SMS, Email, and Backup codes
    """
    
    def __init__(self):
        self.redis_client = None
    
    async def init_redis(self):
        """Initialize Redis for MFA session management"""
        self.redis_client = await redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )
    
    def generate_totp_secret(self) -> str:
        """Generate TOTP secret for user"""
        return pyotp.random_base32()
    
    def generate_qr_code(
        self,
        secret: str,
        user_email: str,
        issuer: str = "Financial Planning System"
    ) -> str:
        """Generate QR code for TOTP setup"""
        
        totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
            name=user_email,
            issuer_name=issuer
        )
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(totp_uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buf = BytesIO()
        img.save(buf, format='PNG')
        
        return base64.b64encode(buf.getvalue()).decode()
    
    def verify_totp(self, secret: str, token: str) -> bool:
        """Verify TOTP token"""
        
        totp = pyotp.TOTP(secret)
        # Allow for time drift (1 period before/after)
        return totp.verify(token, valid_window=1)
    
    def generate_backup_codes(self, count: int = 10) -> List[str]:
        """Generate backup codes for account recovery"""
        
        codes = []
        for _ in range(count):
            code = f"{secrets.randbelow(1000):03d}-{secrets.randbelow(1000):03d}"
            codes.append(code)
        
        return codes
    
    async def send_sms_code(self, phone_number: str) -> str:
        """Send SMS verification code"""
        
        code = f"{secrets.randbelow(1000000):06d}"
        
        # Store code in Redis with expiration
        if self.redis_client:
            await self.redis_client.setex(
                f"sms_code:{phone_number}",
                300,  # 5 minutes
                code
            )
        
        # TODO: Integrate with SMS provider (Twilio, AWS SNS, etc.)
        
        return code
    
    async def verify_sms_code(self, phone_number: str, code: str) -> bool:
        """Verify SMS code"""
        
        if not self.redis_client:
            return False
        
        stored_code = await self.redis_client.get(f"sms_code:{phone_number}")
        if stored_code and stored_code == code:
            await self.redis_client.delete(f"sms_code:{phone_number}")
            return True
        
        return False


class AuthenticationManager:
    """
    Central authentication manager coordinating all auth methods
    """
    
    def __init__(self):
        self.jwt_handler = JWTHandler()
        self.oauth2_handler = OAuth2Handler()
        self.saml_handler = SAMLHandler()
        self.mfa_handler = MFAHandler()
        self.pwd_context = CryptContext(
            schemes=["bcrypt", "argon2"],
            deprecated="auto",
            bcrypt__rounds=12,
            argon2__time_cost=2,
            argon2__memory_cost=65536,
            argon2__parallelism=1
        )
        self.failed_attempts = {}
    
    async def initialize(self):
        """Initialize all handlers"""
        await self.jwt_handler.init_redis()
        await self.oauth2_handler.init_redis()
        await self.saml_handler.init_redis()
        await self.mfa_handler.init_redis()
    
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt/argon2"""
        return self.pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def check_password_strength(self, password: str) -> Tuple[bool, List[str]]:
        """
        Check password strength according to NIST guidelines
        Returns (is_valid, list_of_issues)
        """
        
        issues = []
        
        # NIST SP 800-63B recommendations
        if len(password) < 8:
            issues.append("Password must be at least 8 characters long")
        
        if len(password) > 64:
            issues.append("Password must not exceed 64 characters")
        
        # Check against common passwords (simplified)
        common_passwords = ["password", "123456", "qwerty", "admin"]
        if password.lower() in common_passwords:
            issues.append("Password is too common")
        
        # Check for sequential/repeated characters
        if any(password[i:i+3] in "abcdefghijklmnopqrstuvwxyz0123456789" 
               for i in range(len(password)-2)):
            issues.append("Password contains sequential characters")
        
        return len(issues) == 0, issues
    
    async def track_failed_attempt(self, identifier: str) -> bool:
        """
        Track failed login attempts for brute force protection
        Returns True if account should be locked
        """
        
        current_time = datetime.utcnow()
        
        if identifier not in self.failed_attempts:
            self.failed_attempts[identifier] = []
        
        # Clean old attempts (older than 1 hour)
        self.failed_attempts[identifier] = [
            attempt for attempt in self.failed_attempts[identifier]
            if (current_time - attempt).seconds < 3600
        ]
        
        self.failed_attempts[identifier].append(current_time)
        
        # Lock after 5 failed attempts within an hour
        if len(self.failed_attempts[identifier]) >= 5:
            return True
        
        return False
    
    async def clear_failed_attempts(self, identifier: str):
        """Clear failed login attempts after successful login"""
        
        if identifier in self.failed_attempts:
            del self.failed_attempts[identifier]
    
    async def authenticate_user(
        self,
        username: str,
        password: str,
        require_mfa: bool = False,
        db: AsyncSession = None
    ) -> Optional[Dict[str, Any]]:
        """
        Authenticate user with username/password and optional MFA
        """
        
        # Check for account lockout
        if await self.track_failed_attempt(username):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Account temporarily locked due to multiple failed attempts"
            )
        
        # TODO: Fetch user from database
        # user = await db.query(User).filter(User.username == username).first()
        
        # For now, return mock user
        user = {
            "id": "user_123",
            "username": username,
            "email": f"{username}@example.com",
            "mfa_enabled": require_mfa
        }
        
        # Verify password
        # if not self.verify_password(password, user.password_hash):
        #     return None
        
        await self.clear_failed_attempts(username)
        
        if require_mfa:
            # Return temporary token for MFA verification
            mfa_token = self.jwt_handler.create_token(
                user["id"],
                TokenType.MFA,
                additional_claims={"requires_mfa": True}
            )
            return {"mfa_token": mfa_token, "mfa_required": True}
        
        # Create access and refresh tokens
        access_token, refresh_token = self.jwt_handler.create_token_pair(
            user["id"],
            additional_claims={
                "username": user["username"],
                "email": user["email"]
            }
        )
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": user
        }
    
    async def refresh_access_token(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        """Refresh access token using refresh token"""
        
        payload = await self.jwt_handler.verify_token(
            refresh_token,
            TokenType.REFRESH
        )
        
        if not payload:
            return None
        
        # Create new access token
        access_token = self.jwt_handler.create_token(
            payload["sub"],
            TokenType.ACCESS,
            additional_claims={
                "username": payload.get("username"),
                "email": payload.get("email")
            }
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer"
        }
    
    async def logout(self, access_token: str, refresh_token: Optional[str] = None):
        """Logout user by revoking tokens"""
        
        await self.jwt_handler.revoke_token(access_token)
        
        if refresh_token:
            await self.jwt_handler.revoke_token(refresh_token)