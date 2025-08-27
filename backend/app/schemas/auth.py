"""
Authentication Pydantic Schemas

Schemas for authentication tokens, sessions, and security-related operations.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, EmailStr, validator
from datetime import datetime
from enum import Enum


class TokenType(str, Enum):
    """Token types"""
    ACCESS = "access"
    REFRESH = "refresh"


class Token(BaseModel):
    """JWT token response"""
    
    access_token: str = Field(..., description="JWT access token")
    refresh_token: Optional[str] = Field(None, description="JWT refresh token")
    token_type: str = Field("bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")
    scope: Optional[str] = Field(None, description="Token scope")
    
    class Config:
        schema_extra = {
            "example": {
                "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                "token_type": "bearer",
                "expires_in": 1800,
                "scope": "read write"
            }
        }


class TokenPayload(BaseModel):
    """JWT token payload"""
    
    sub: str = Field(..., description="Subject (user ID)")
    exp: int = Field(..., description="Expiration timestamp")
    iat: int = Field(..., description="Issued at timestamp")
    type: TokenType = Field(..., description="Token type")
    jti: Optional[str] = Field(None, description="JWT ID for blacklisting")
    scope: Optional[str] = Field(None, description="Token scope")


class RefreshTokenRequest(BaseModel):
    """Refresh token request"""
    
    refresh_token: str = Field(..., description="Refresh token to use")
    
    class Config:
        schema_extra = {
            "example": {
                "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
            }
        }


class UserLogin(BaseModel):
    """User login request"""
    
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., min_length=1, description="User's password")
    remember_me: bool = Field(False, description="Whether to issue long-lived refresh token")
    
    class Config:
        schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "securepassword123",
                "remember_me": True
            }
        }


class UserRegister(BaseModel):
    """User registration request"""
    
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., min_length=8, description="Password (minimum 8 characters)")
    confirm_password: str = Field(..., description="Password confirmation")
    first_name: str = Field(..., min_length=1, max_length=100, description="First name")
    last_name: str = Field(..., min_length=1, max_length=100, description="Last name")
    phone_number: Optional[str] = Field(None, max_length=20, description="Phone number")
    
    @validator('confirm_password')
    def passwords_match(cls, v, values, **kwargs):
        if 'password' in values and v != values['password']:
            raise ValueError('Passwords do not match')
        return v
    
    @validator('password')
    def password_strength(cls, v):
        """Basic password strength validation"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "email": "newuser@example.com",
                "password": "SecurePass123",
                "confirm_password": "SecurePass123",
                "first_name": "John",
                "last_name": "Doe",
                "phone_number": "+1234567890"
            }
        }


class PasswordReset(BaseModel):
    """Password reset request"""
    
    email: EmailStr = Field(..., description="Email address for password reset")
    
    class Config:
        schema_extra = {
            "example": {
                "email": "user@example.com"
            }
        }


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation"""
    
    token: str = Field(..., description="Password reset token")
    new_password: str = Field(..., min_length=8, description="New password")
    confirm_password: str = Field(..., description="Password confirmation")
    
    @validator('confirm_password')
    def passwords_match(cls, v, values, **kwargs):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Passwords do not match')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "token": "reset-token-here",
                "new_password": "NewSecurePass123",
                "confirm_password": "NewSecurePass123"
            }
        }


class SessionInfo(BaseModel):
    """User session information"""
    
    session_id: str = Field(..., description="Session identifier")
    user_id: str = Field(..., description="User identifier")
    ip_address: str = Field(..., description="IP address")
    user_agent: str = Field(..., description="User agent string")
    created_at: datetime = Field(..., description="Session creation time")
    last_activity: datetime = Field(..., description="Last activity time")
    expires_at: datetime = Field(..., description="Session expiration time")
    is_active: bool = Field(..., description="Whether session is active")
    
    class Config:
        schema_extra = {
            "example": {
                "session_id": "sess_12345",
                "user_id": "user_67890",
                "ip_address": "192.168.1.1",
                "user_agent": "Mozilla/5.0...",
                "created_at": "2024-01-27T10:00:00Z",
                "last_activity": "2024-01-27T10:30:00Z",
                "expires_at": "2024-01-28T10:00:00Z",
                "is_active": True
            }
        }


class SessionList(BaseModel):
    """List of user sessions"""
    
    sessions: List[SessionInfo] = Field(..., description="List of active sessions")
    total: int = Field(..., description="Total number of sessions")
    
    class Config:
        schema_extra = {
            "example": {
                "sessions": [
                    {
                        "session_id": "sess_12345",
                        "ip_address": "192.168.1.1",
                        "user_agent": "Mozilla/5.0...",
                        "created_at": "2024-01-27T10:00:00Z",
                        "last_activity": "2024-01-27T10:30:00Z",
                        "is_active": True
                    }
                ],
                "total": 1
            }
        }


class AuthResponse(BaseModel):
    """Authentication response with user info and tokens"""
    
    user: Dict[str, Any] = Field(..., description="User information")
    tokens: Token = Field(..., description="Authentication tokens")
    session: SessionInfo = Field(..., description="Session information")
    
    class Config:
        schema_extra = {
            "example": {
                "user": {
                    "id": "user_12345",
                    "email": "user@example.com",
                    "first_name": "John",
                    "last_name": "Doe",
                    "is_active": True,
                    "email_verified": True
                },
                "tokens": {
                    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                    "token_type": "bearer",
                    "expires_in": 1800
                },
                "session": {
                    "session_id": "sess_12345",
                    "created_at": "2024-01-27T10:00:00Z",
                    "expires_at": "2024-01-28T10:00:00Z",
                    "is_active": True
                }
            }
        }


class LogoutRequest(BaseModel):
    """Logout request options"""
    
    all_sessions: bool = Field(False, description="Whether to logout from all sessions")
    
    class Config:
        schema_extra = {
            "example": {
                "all_sessions": False
            }
        }


class SecuritySettings(BaseModel):
    """User security settings"""
    
    two_factor_enabled: bool = Field(False, description="Whether 2FA is enabled")
    email_notifications: bool = Field(True, description="Email security notifications")
    login_alerts: bool = Field(True, description="Login alert notifications")
    password_changed_at: Optional[datetime] = Field(None, description="Last password change")
    
    class Config:
        schema_extra = {
            "example": {
                "two_factor_enabled": False,
                "email_notifications": True,
                "login_alerts": True,
                "password_changed_at": "2024-01-15T10:00:00Z"
            }
        }


class TwoFactorSetup(BaseModel):
    """Two-factor authentication setup"""
    
    secret_key: str = Field(..., description="TOTP secret key")
    qr_code_url: str = Field(..., description="QR code URL for setup")
    backup_codes: List[str] = Field(..., description="Backup recovery codes")
    
    class Config:
        schema_extra = {
            "example": {
                "secret_key": "JBSWY3DPEHPK3PXP",
                "qr_code_url": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA...",
                "backup_codes": ["12345678", "87654321", "11223344"]
            }
        }


class TwoFactorVerification(BaseModel):
    """Two-factor authentication verification"""
    
    code: str = Field(..., min_length=6, max_length=6, description="6-digit TOTP code")
    
    class Config:
        schema_extra = {
            "example": {
                "code": "123456"
            }
        }