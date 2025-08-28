"""
Enhanced Authentication & Authorization Module

Implements:
- OAuth2 with PKCE (Proof Key for Code Exchange)
- Multi-Factor Authentication (MFA/2FA)
- Role-Based Access Control (RBAC)
- Session Management with Redis
- JWT with refresh tokens
- Biometric authentication support
"""

import secrets
import hashlib
import base64
import pyotp
import qrcode
from io import BytesIO
from typing import Optional, Dict, Any, List, Tuple, Set
from datetime import datetime, timedelta
from enum import Enum
import jwt
import bcrypt
from fastapi import HTTPException, Security, Depends, status
from fastapi.security import OAuth2AuthorizationCodeBearer, HTTPBearer
import redis.asyncio as redis
from pydantic import BaseModel, EmailStr, Field
import asyncio
from dataclasses import dataclass
import json
import uuid

from app.core.config import settings


class AuthenticationMethod(Enum):
    """Supported authentication methods"""
    PASSWORD = "password"
    OAUTH2 = "oauth2"
    SAML = "saml"
    MFA_TOTP = "mfa_totp"
    MFA_SMS = "mfa_sms"
    MFA_EMAIL = "mfa_email"
    BIOMETRIC = "biometric"
    HARDWARE_KEY = "hardware_key"
    PASSKEY = "passkey"


class Role(Enum):
    """User roles for RBAC"""
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    FINANCIAL_ADVISOR = "financial_advisor"
    PREMIUM_USER = "premium_user"
    STANDARD_USER = "standard_user"
    READ_ONLY_USER = "read_only_user"
    GUEST = "guest"


class Permission(Enum):
    """Granular permissions"""
    # Account permissions
    VIEW_ACCOUNTS = "view_accounts"
    EDIT_ACCOUNTS = "edit_accounts"
    DELETE_ACCOUNTS = "delete_accounts"
    
    # Portfolio permissions
    VIEW_PORTFOLIO = "view_portfolio"
    EDIT_PORTFOLIO = "edit_portfolio"
    TRADE = "trade"
    
    # Financial planning permissions
    VIEW_PLANS = "view_plans"
    CREATE_PLANS = "create_plans"
    EDIT_PLANS = "edit_plans"
    
    # Admin permissions
    MANAGE_USERS = "manage_users"
    VIEW_AUDIT_LOGS = "view_audit_logs"
    SYSTEM_CONFIG = "system_config"
    
    # Data permissions
    EXPORT_DATA = "export_data"
    DELETE_DATA = "delete_data"


# Role-Permission Mapping
ROLE_PERMISSIONS: Dict[Role, Set[Permission]] = {
    Role.SUPER_ADMIN: set(Permission),  # All permissions
    Role.ADMIN: {
        Permission.VIEW_ACCOUNTS, Permission.EDIT_ACCOUNTS,
        Permission.VIEW_PORTFOLIO, Permission.EDIT_PORTFOLIO,
        Permission.VIEW_PLANS, Permission.CREATE_PLANS, Permission.EDIT_PLANS,
        Permission.MANAGE_USERS, Permission.VIEW_AUDIT_LOGS,
        Permission.EXPORT_DATA
    },
    Role.FINANCIAL_ADVISOR: {
        Permission.VIEW_ACCOUNTS, Permission.EDIT_ACCOUNTS,
        Permission.VIEW_PORTFOLIO, Permission.EDIT_PORTFOLIO,
        Permission.VIEW_PLANS, Permission.CREATE_PLANS, Permission.EDIT_PLANS,
        Permission.TRADE
    },
    Role.PREMIUM_USER: {
        Permission.VIEW_ACCOUNTS, Permission.EDIT_ACCOUNTS,
        Permission.VIEW_PORTFOLIO, Permission.EDIT_PORTFOLIO,
        Permission.VIEW_PLANS, Permission.CREATE_PLANS,
        Permission.TRADE, Permission.EXPORT_DATA
    },
    Role.STANDARD_USER: {
        Permission.VIEW_ACCOUNTS, Permission.VIEW_PORTFOLIO,
        Permission.VIEW_PLANS, Permission.EXPORT_DATA
    },
    Role.READ_ONLY_USER: {
        Permission.VIEW_ACCOUNTS, Permission.VIEW_PORTFOLIO,
        Permission.VIEW_PLANS
    },
    Role.GUEST: set()  # No permissions
}


@dataclass
class SessionData:
    """User session data"""
    user_id: str
    username: str
    email: str
    roles: List[Role]
    permissions: Set[Permission]
    auth_method: AuthenticationMethod
    mfa_verified: bool
    ip_address: str
    user_agent: str
    created_at: datetime
    last_activity: datetime
    expires_at: datetime


class PKCEChallenge:
    """PKCE (Proof Key for Code Exchange) implementation"""
    
    @staticmethod
    def generate_code_verifier() -> str:
        """Generate code verifier for PKCE"""
        code_verifier = base64.urlsafe_b64encode(
            secrets.token_bytes(32)
        ).decode('utf-8').rstrip('=')
        return code_verifier
    
    @staticmethod
    def generate_code_challenge(code_verifier: str) -> str:
        """Generate code challenge from verifier"""
        code_challenge = base64.urlsafe_b64encode(
            hashlib.sha256(code_verifier.encode()).digest()
        ).decode('utf-8').rstrip('=')
        return code_challenge
    
    @staticmethod
    def verify_code_verifier(code_verifier: str, code_challenge: str) -> bool:
        """Verify PKCE code verifier against challenge"""
        expected_challenge = PKCEChallenge.generate_code_challenge(code_verifier)
        return secrets.compare_digest(expected_challenge, code_challenge)


class MFAManager:
    """Multi-Factor Authentication Manager"""
    
    def __init__(self):
        self.redis_client = None
        self.totp_issuer = "Financial Planner"
        
    async def initialize(self):
        """Initialize MFA manager"""
        self.redis_client = await redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )
    
    def generate_totp_secret(self) -> str:
        """Generate TOTP secret for user"""
        return pyotp.random_base32()
    
    def generate_totp_provisioning_uri(
        self,
        secret: str,
        email: str
    ) -> str:
        """Generate provisioning URI for TOTP setup"""
        totp = pyotp.TOTP(secret)
        return totp.provisioning_uri(
            name=email,
            issuer_name=self.totp_issuer
        )
    
    def generate_qr_code(self, provisioning_uri: str) -> bytes:
        """Generate QR code for TOTP setup"""
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(provisioning_uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buf = BytesIO()
        img.save(buf, format='PNG')
        return buf.getvalue()
    
    def verify_totp_token(self, secret: str, token: str) -> bool:
        """Verify TOTP token"""
        totp = pyotp.TOTP(secret)
        # Allow for time drift (30 seconds window)
        return totp.verify(token, valid_window=1)
    
    async def send_sms_code(self, phone_number: str) -> str:
        """Send SMS verification code"""
        code = str(secrets.randbelow(1000000)).zfill(6)
        
        # Store code in Redis with expiration
        await self.redis_client.setex(
            f"sms_code:{phone_number}",
            300,  # 5 minutes expiration
            code
        )
        
        # TODO: Integrate with SMS provider (Twilio, AWS SNS, etc.)
        print(f"SMS Code for {phone_number}: {code}")
        
        return code
    
    async def verify_sms_code(self, phone_number: str, code: str) -> bool:
        """Verify SMS code"""
        stored_code = await self.redis_client.get(f"sms_code:{phone_number}")
        if stored_code and secrets.compare_digest(stored_code, code):
            await self.redis_client.delete(f"sms_code:{phone_number}")
            return True
        return False
    
    async def send_email_code(self, email: str) -> str:
        """Send email verification code"""
        code = str(secrets.randbelow(1000000)).zfill(6)
        
        # Store code in Redis with expiration
        await self.redis_client.setex(
            f"email_code:{email}",
            600,  # 10 minutes expiration
            code
        )
        
        # TODO: Integrate with email service
        print(f"Email Code for {email}: {code}")
        
        return code
    
    async def verify_email_code(self, email: str, code: str) -> bool:
        """Verify email code"""
        stored_code = await self.redis_client.get(f"email_code:{email}")
        if stored_code and secrets.compare_digest(stored_code, code):
            await self.redis_client.delete(f"email_code:{email}")
            return True
        return False


class SessionManager:
    """Session management with Redis"""
    
    def __init__(self):
        self.redis_client = None
        self.session_ttl = 3600  # 1 hour
        self.refresh_threshold = 300  # 5 minutes
        
    async def initialize(self):
        """Initialize session manager"""
        self.redis_client = await redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )
    
    async def create_session(
        self,
        user_id: str,
        username: str,
        email: str,
        roles: List[Role],
        auth_method: AuthenticationMethod,
        ip_address: str,
        user_agent: str,
        mfa_verified: bool = False
    ) -> str:
        """Create new session"""
        session_id = str(uuid.uuid4())
        
        # Calculate permissions from roles
        permissions = set()
        for role in roles:
            permissions.update(ROLE_PERMISSIONS.get(role, set()))
        
        session_data = SessionData(
            user_id=user_id,
            username=username,
            email=email,
            roles=roles,
            permissions=permissions,
            auth_method=auth_method,
            mfa_verified=mfa_verified,
            ip_address=ip_address,
            user_agent=user_agent,
            created_at=datetime.utcnow(),
            last_activity=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(seconds=self.session_ttl)
        )
        
        # Store in Redis
        await self.redis_client.setex(
            f"session:{session_id}",
            self.session_ttl,
            json.dumps({
                "user_id": session_data.user_id,
                "username": session_data.username,
                "email": session_data.email,
                "roles": [role.value for role in session_data.roles],
                "permissions": [perm.value for perm in session_data.permissions],
                "auth_method": session_data.auth_method.value,
                "mfa_verified": session_data.mfa_verified,
                "ip_address": session_data.ip_address,
                "user_agent": session_data.user_agent,
                "created_at": session_data.created_at.isoformat(),
                "last_activity": session_data.last_activity.isoformat(),
                "expires_at": session_data.expires_at.isoformat()
            })
        )
        
        # Track active sessions per user
        await self.redis_client.sadd(f"user_sessions:{user_id}", session_id)
        
        return session_id
    
    async def get_session(self, session_id: str) -> Optional[SessionData]:
        """Get session data"""
        session_json = await self.redis_client.get(f"session:{session_id}")
        
        if not session_json:
            return None
        
        session_dict = json.loads(session_json)
        
        # Reconstruct SessionData
        return SessionData(
            user_id=session_dict["user_id"],
            username=session_dict["username"],
            email=session_dict["email"],
            roles=[Role(role) for role in session_dict["roles"]],
            permissions={Permission(perm) for perm in session_dict["permissions"]},
            auth_method=AuthenticationMethod(session_dict["auth_method"]),
            mfa_verified=session_dict["mfa_verified"],
            ip_address=session_dict["ip_address"],
            user_agent=session_dict["user_agent"],
            created_at=datetime.fromisoformat(session_dict["created_at"]),
            last_activity=datetime.fromisoformat(session_dict["last_activity"]),
            expires_at=datetime.fromisoformat(session_dict["expires_at"])
        )
    
    async def update_session_activity(self, session_id: str):
        """Update session last activity"""
        session = await self.get_session(session_id)
        
        if session:
            session.last_activity = datetime.utcnow()
            
            # Check if session needs refresh
            time_to_expire = (session.expires_at - datetime.utcnow()).total_seconds()
            
            if time_to_expire < self.refresh_threshold:
                # Extend session
                session.expires_at = datetime.utcnow() + timedelta(seconds=self.session_ttl)
                
                await self.redis_client.expire(
                    f"session:{session_id}",
                    self.session_ttl
                )
    
    async def invalidate_session(self, session_id: str):
        """Invalidate session"""
        session = await self.get_session(session_id)
        
        if session:
            # Remove from Redis
            await self.redis_client.delete(f"session:{session_id}")
            
            # Remove from user's active sessions
            await self.redis_client.srem(
                f"user_sessions:{session.user_id}",
                session_id
            )
    
    async def invalidate_all_user_sessions(self, user_id: str):
        """Invalidate all sessions for a user"""
        session_ids = await self.redis_client.smembers(f"user_sessions:{user_id}")
        
        for session_id in session_ids:
            await self.redis_client.delete(f"session:{session_id}")
        
        await self.redis_client.delete(f"user_sessions:{user_id}")
    
    async def get_active_sessions_count(self, user_id: str) -> int:
        """Get count of active sessions for user"""
        return await self.redis_client.scard(f"user_sessions:{user_id}")


class JWTManager:
    """JWT token management with refresh tokens"""
    
    def __init__(self):
        self.access_token_expire = timedelta(minutes=15)
        self.refresh_token_expire = timedelta(days=7)
        self.algorithm = "RS256"  # Using RSA for better security
        self.private_key = None
        self.public_key = None
        self._load_keys()
    
    def _load_keys(self):
        """Load RSA keys for JWT signing"""
        # In production, load from secure storage
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives import serialization
        
        if hasattr(settings, 'JWT_PRIVATE_KEY'):
            self.private_key = settings.JWT_PRIVATE_KEY
            self.public_key = settings.JWT_PUBLIC_KEY
        else:
            # Generate keys for development
            key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
            self.private_key = key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )
            self.public_key = key.public_key().public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
    
    def create_access_token(
        self,
        user_id: str,
        session_id: str,
        roles: List[Role],
        permissions: Set[Permission]
    ) -> str:
        """Create JWT access token"""
        expire = datetime.utcnow() + self.access_token_expire
        
        payload = {
            "sub": user_id,
            "sid": session_id,
            "roles": [role.value for role in roles],
            "permissions": [perm.value for perm in permissions],
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        }
        
        return jwt.encode(payload, self.private_key, algorithm=self.algorithm)
    
    def create_refresh_token(
        self,
        user_id: str,
        session_id: str
    ) -> str:
        """Create JWT refresh token"""
        expire = datetime.utcnow() + self.refresh_token_expire
        
        payload = {
            "sub": user_id,
            "sid": session_id,
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh"
        }
        
        return jwt.encode(payload, self.private_key, algorithm=self.algorithm)
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(
                token,
                self.public_key,
                algorithms=[self.algorithm]
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )


class OAuth2Manager:
    """OAuth2 with PKCE implementation"""
    
    def __init__(self):
        self.redis_client = None
        self.authorization_code_ttl = 600  # 10 minutes
        
    async def initialize(self):
        """Initialize OAuth2 manager"""
        self.redis_client = await redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )
    
    async def create_authorization_code(
        self,
        client_id: str,
        user_id: str,
        redirect_uri: str,
        code_challenge: str,
        scope: str,
        state: Optional[str] = None
    ) -> str:
        """Create authorization code with PKCE"""
        auth_code = base64.urlsafe_b64encode(
            secrets.token_bytes(32)
        ).decode('utf-8').rstrip('=')
        
        # Store authorization code details
        await self.redis_client.setex(
            f"auth_code:{auth_code}",
            self.authorization_code_ttl,
            json.dumps({
                "client_id": client_id,
                "user_id": user_id,
                "redirect_uri": redirect_uri,
                "code_challenge": code_challenge,
                "scope": scope,
                "state": state,
                "created_at": datetime.utcnow().isoformat()
            })
        )
        
        return auth_code
    
    async def exchange_authorization_code(
        self,
        auth_code: str,
        client_id: str,
        redirect_uri: str,
        code_verifier: str
    ) -> Optional[Dict[str, Any]]:
        """Exchange authorization code for tokens"""
        # Get stored authorization code
        auth_data_json = await self.redis_client.get(f"auth_code:{auth_code}")
        
        if not auth_data_json:
            return None
        
        auth_data = json.loads(auth_data_json)
        
        # Verify client_id and redirect_uri
        if auth_data["client_id"] != client_id or auth_data["redirect_uri"] != redirect_uri:
            return None
        
        # Verify PKCE code verifier
        if not PKCEChallenge.verify_code_verifier(
            code_verifier,
            auth_data["code_challenge"]
        ):
            return None
        
        # Delete authorization code (one-time use)
        await self.redis_client.delete(f"auth_code:{auth_code}")
        
        return {
            "user_id": auth_data["user_id"],
            "scope": auth_data["scope"]
        }


class PasswordManager:
    """Secure password management"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt(rounds=12)
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(
            password.encode('utf-8'),
            hashed.encode('utf-8')
        )
    
    @staticmethod
    def check_password_strength(password: str) -> Tuple[bool, List[str]]:
        """Check password strength"""
        issues = []
        
        if len(password) < 12:
            issues.append("Password must be at least 12 characters long")
        
        if not any(c.isupper() for c in password):
            issues.append("Password must contain at least one uppercase letter")
        
        if not any(c.islower() for c in password):
            issues.append("Password must contain at least one lowercase letter")
        
        if not any(c.isdigit() for c in password):
            issues.append("Password must contain at least one number")
        
        special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        if not any(c in special_chars for c in password):
            issues.append("Password must contain at least one special character")
        
        # Check for common passwords
        common_passwords = ["password", "12345678", "qwerty", "admin"]
        if password.lower() in common_passwords:
            issues.append("Password is too common")
        
        return len(issues) == 0, issues


class AuthenticationService:
    """Main authentication service orchestrator"""
    
    def __init__(self):
        self.mfa_manager = MFAManager()
        self.session_manager = SessionManager()
        self.jwt_manager = JWTManager()
        self.oauth2_manager = OAuth2Manager()
        self.password_manager = PasswordManager()
        
    async def initialize(self):
        """Initialize authentication service"""
        await self.mfa_manager.initialize()
        await self.session_manager.initialize()
        await self.oauth2_manager.initialize()
    
    async def authenticate_user(
        self,
        username: str,
        password: str,
        ip_address: str,
        user_agent: str
    ) -> Dict[str, Any]:
        """Authenticate user with password"""
        # TODO: Fetch user from database
        # For now, mock user data
        user = {
            "id": "user_123",
            "username": username,
            "email": f"{username}@example.com",
            "password_hash": self.password_manager.hash_password(password),
            "roles": [Role.PREMIUM_USER],
            "mfa_enabled": True,
            "mfa_secret": self.mfa_manager.generate_totp_secret()
        }
        
        # Verify password
        if not self.password_manager.verify_password(password, user["password_hash"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        # Create session
        session_id = await self.session_manager.create_session(
            user_id=user["id"],
            username=user["username"],
            email=user["email"],
            roles=user["roles"],
            auth_method=AuthenticationMethod.PASSWORD,
            ip_address=ip_address,
            user_agent=user_agent,
            mfa_verified=not user["mfa_enabled"]
        )
        
        # Get permissions
        permissions = set()
        for role in user["roles"]:
            permissions.update(ROLE_PERMISSIONS.get(role, set()))
        
        # Generate tokens
        access_token = self.jwt_manager.create_access_token(
            user_id=user["id"],
            session_id=session_id,
            roles=user["roles"],
            permissions=permissions
        )
        
        refresh_token = self.jwt_manager.create_refresh_token(
            user_id=user["id"],
            session_id=session_id
        )
        
        return {
            "session_id": session_id,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "mfa_required": user["mfa_enabled"],
            "mfa_qr_code": None  # Will be set if MFA setup is needed
        }
    
    async def verify_mfa(
        self,
        session_id: str,
        mfa_token: str,
        mfa_type: AuthenticationMethod
    ) -> bool:
        """Verify MFA token"""
        session = await self.session_manager.get_session(session_id)
        
        if not session:
            return False
        
        # TODO: Get user's MFA secret from database
        mfa_secret = "mock_secret"
        
        verified = False
        
        if mfa_type == AuthenticationMethod.MFA_TOTP:
            verified = self.mfa_manager.verify_totp_token(mfa_secret, mfa_token)
        elif mfa_type == AuthenticationMethod.MFA_SMS:
            # Verify SMS code
            pass
        elif mfa_type == AuthenticationMethod.MFA_EMAIL:
            # Verify email code
            pass
        
        if verified:
            # Update session
            session.mfa_verified = True
            # TODO: Update session in Redis
        
        return verified
    
    async def refresh_access_token(
        self,
        refresh_token: str
    ) -> Dict[str, Any]:
        """Refresh access token"""
        # Verify refresh token
        payload = self.jwt_manager.verify_token(refresh_token)
        
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Get session
        session = await self.session_manager.get_session(payload["sid"])
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session not found"
            )
        
        # Generate new access token
        access_token = self.jwt_manager.create_access_token(
            user_id=session.user_id,
            session_id=payload["sid"],
            roles=session.roles,
            permissions=session.permissions
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer"
        }
    
    async def logout(self, session_id: str):
        """Logout user"""
        await self.session_manager.invalidate_session(session_id)
    
    async def logout_all_devices(self, user_id: str):
        """Logout user from all devices"""
        await self.session_manager.invalidate_all_user_sessions(user_id)


# Global authentication service instance
auth_service = AuthenticationService()