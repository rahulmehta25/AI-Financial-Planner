"""
Authentication Service

Comprehensive service for user authentication, session management, and security operations.
"""

import logging
import uuid
import secrets
import hashlib
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, update, delete
from sqlalchemy.exc import IntegrityError
from passlib.context import CryptContext
from jose import jwt, JWTError

from app.core.config import settings
from app.models.user import User
from app.models.auth import (
    TokenBlacklist, UserSession, LoginAttempt, 
    PasswordResetToken, SecurityEvent
)
from app.schemas.auth import UserRegister, UserLogin, TokenType
from app.core.exceptions import AuthenticationError, ValidationError

logger = logging.getLogger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """Service for authentication and user management operations"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def register_user(
        self, 
        user_data: UserRegister,
        ip_address: str = None,
        user_agent: str = None
    ) -> User:
        """Register a new user account"""
        
        try:
            # Check if user already exists
            existing_user = await self.get_user_by_email(user_data.email)
            if existing_user:
                raise ValidationError("Email address is already registered")
            
            # Hash password
            hashed_password = self._hash_password(user_data.password)
            
            # Create user
            user = User(
                email=user_data.email,
                hashed_password=hashed_password,
                first_name=user_data.first_name,
                last_name=user_data.last_name,
                phone_number=user_data.phone_number,
                is_active=True,
                email_verified=False  # Requires email verification
            )
            
            self.db.add(user)
            await self.db.commit()
            await self.db.refresh(user)
            
            # Log security event
            await self._log_security_event(
                user_id=str(user.id),
                event_type="user_registration",
                event_description=f"New user registered: {user.email}",
                severity="low",
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            logger.info(f"New user registered: {user.email}")
            return user
            
        except IntegrityError:
            await self.db.rollback()
            raise ValidationError("Email address is already registered")
        except Exception as e:
            await self.db.rollback()
            logger.error(f"User registration failed: {str(e)}")
            raise ValidationError("Registration failed")
    
    async def authenticate_user(
        self, 
        email: str, 
        password: str,
        ip_address: str = None,
        user_agent: str = None
    ) -> Optional[User]:
        """Authenticate user with email and password"""
        
        # Log login attempt
        await self._log_login_attempt(
            email=email,
            ip_address=ip_address,
            user_agent=user_agent,
            success=False  # Will update if successful
        )
        
        try:
            # Get user by email
            user = await self.get_user_by_email(email)
            if not user:
                await self._log_security_event(
                    event_type="login_attempt_invalid_email",
                    event_description=f"Login attempt with invalid email: {email}",
                    severity="medium",
                    ip_address=ip_address,
                    user_agent=user_agent
                )
                return None
            
            # Check if account is active
            if not user.is_active:
                await self._log_security_event(
                    user_id=str(user.id),
                    event_type="login_attempt_inactive_account",
                    event_description=f"Login attempt on inactive account: {email}",
                    severity="medium",
                    ip_address=ip_address,
                    user_agent=user_agent
                )
                return None
            
            # Verify password
            if not self._verify_password(password, user.hashed_password):
                await self._log_security_event(
                    user_id=str(user.id),
                    event_type="login_attempt_wrong_password",
                    event_description=f"Login attempt with wrong password: {email}",
                    severity="medium",
                    ip_address=ip_address,
                    user_agent=user_agent
                )
                return None
            
            # Update last login
            user.last_login = datetime.utcnow()
            await self.db.commit()
            
            # Update login attempt as successful
            await self._update_login_attempt_success(
                email=email,
                user_id=str(user.id),
                ip_address=ip_address
            )
            
            # Log successful login
            await self._log_security_event(
                user_id=str(user.id),
                event_type="user_login",
                event_description=f"Successful login: {email}",
                severity="low",
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            logger.info(f"User authenticated successfully: {email}")
            return user
            
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            return None
    
    async def create_session(
        self,
        user: User,
        ip_address: str = None,
        user_agent: str = None,
        remember_me: bool = False
    ) -> UserSession:
        """Create a new user session"""
        
        try:
            # Generate session ID
            session_id = self._generate_session_id()
            
            # Calculate expiration
            if remember_me:
                expires_at = datetime.utcnow() + timedelta(days=30)
            else:
                expires_at = datetime.utcnow() + timedelta(hours=24)
            
            # Create session
            session = UserSession(
                session_id=session_id,
                user_id=user.id,
                ip_address=ip_address,
                user_agent=user_agent,
                expires_at=expires_at,
                is_active=True
            )
            
            self.db.add(session)
            await self.db.commit()
            await self.db.refresh(session)
            
            logger.info(f"Session created for user {user.email}: {session_id}")
            return session
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Session creation failed: {str(e)}")
            raise
    
    async def create_tokens(
        self, 
        user: User, 
        session: UserSession = None
    ) -> Dict[str, Any]:
        """Create access and refresh tokens for user"""
        
        try:
            # Generate JTI (JWT ID) for token blacklisting
            access_jti = str(uuid.uuid4())
            refresh_jti = str(uuid.uuid4())
            
            # Access token payload
            access_token_data = {
                "sub": str(user.id),
                "email": user.email,
                "type": TokenType.ACCESS,
                "jti": access_jti,
                "session_id": session.session_id if session else None
            }
            
            # Refresh token payload
            refresh_token_data = {
                "sub": str(user.id),
                "type": TokenType.REFRESH,
                "jti": refresh_jti,
                "session_id": session.session_id if session else None
            }
            
            # Create tokens
            access_token = self._create_token(
                access_token_data, 
                timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
            )
            
            refresh_token = self._create_token(
                refresh_token_data,
                timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
            )
            
            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                "access_jti": access_jti,
                "refresh_jti": refresh_jti
            }
            
        except Exception as e:
            logger.error(f"Token creation failed: {str(e)}")
            raise
    
    async def refresh_token(
        self, 
        refresh_token: str,
        ip_address: str = None,
        user_agent: str = None
    ) -> Dict[str, Any]:
        """Refresh access token using refresh token"""
        
        try:
            # Decode refresh token
            payload = jwt.decode(
                refresh_token,
                settings.SECRET_KEY.get_secret_value(),
                algorithms=[settings.ALGORITHM]
            )
            
            # Validate token type
            if payload.get("type") != TokenType.REFRESH:
                raise AuthenticationError("Invalid token type")
            
            user_id = payload.get("sub")
            jti = payload.get("jti")
            session_id = payload.get("session_id")
            
            # Check if token is blacklisted
            if await self._is_token_blacklisted(jti):
                raise AuthenticationError("Token has been revoked")
            
            # Get user
            user = await self.get_user_by_id(user_id)
            if not user or not user.is_active:
                raise AuthenticationError("User not found or inactive")
            
            # Validate session if present
            if session_id:
                session = await self._get_session_by_id(session_id, user_id)
                if not session or not session.is_active:
                    raise AuthenticationError("Invalid session")
            else:
                session = None
            
            # Create new tokens
            tokens = await self.create_tokens(user, session)
            
            # Blacklist old refresh token
            await self._blacklist_token(
                jti=jti,
                user_id=user_id,
                token_type=TokenType.REFRESH,
                reason="token_refresh"
            )
            
            # Log token refresh
            await self._log_security_event(
                user_id=user_id,
                event_type="token_refresh",
                event_description="Access token refreshed",
                severity="low",
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            return tokens
            
        except JWTError:
            raise AuthenticationError("Invalid refresh token")
        except Exception as e:
            logger.error(f"Token refresh failed: {str(e)}")
            raise AuthenticationError("Token refresh failed")
    
    async def logout_user(
        self,
        user: User,
        access_token: str = None,
        refresh_token: str = None,
        session_id: str = None,
        all_sessions: bool = False,
        ip_address: str = None,
        user_agent: str = None
    ) -> bool:
        """Logout user and invalidate tokens/sessions"""
        
        try:
            # Extract token information
            access_jti = None
            refresh_jti = None
            
            if access_token:
                try:
                    payload = jwt.decode(
                        access_token,
                        settings.SECRET_KEY.get_secret_value(),
                        algorithms=[settings.ALGORITHM],
                        options={"verify_exp": False}  # Don't verify expiration for logout
                    )
                    access_jti = payload.get("jti")
                    if not session_id:
                        session_id = payload.get("session_id")
                except JWTError:
                    pass
            
            if refresh_token:
                try:
                    payload = jwt.decode(
                        refresh_token,
                        settings.SECRET_KEY.get_secret_value(),
                        algorithms=[settings.ALGORITHM],
                        options={"verify_exp": False}
                    )
                    refresh_jti = payload.get("jti")
                except JWTError:
                    pass
            
            # Blacklist tokens
            if access_jti:
                await self._blacklist_token(
                    jti=access_jti,
                    user_id=str(user.id),
                    token_type=TokenType.ACCESS,
                    reason="user_logout"
                )
            
            if refresh_jti:
                await self._blacklist_token(
                    jti=refresh_jti,
                    user_id=str(user.id),
                    token_type=TokenType.REFRESH,
                    reason="user_logout"
                )
            
            # Terminate sessions
            if all_sessions:
                terminated = await self._terminate_all_user_sessions(
                    str(user.id),
                    reason="logout_all"
                )
                logger.info(f"Terminated {terminated} sessions for user {user.email}")
            elif session_id:
                await self._terminate_session(session_id, str(user.id), "user_logout")
            
            # Log logout event
            await self._log_security_event(
                user_id=str(user.id),
                event_type="user_logout",
                event_description=f"User logged out{'(all sessions)' if all_sessions else ''}",
                severity="low",
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            logger.info(f"User logged out: {user.email}")
            return True
            
        except Exception as e:
            logger.error(f"Logout failed: {str(e)}")
            return False
    
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        try:
            query = select(User).where(User.id == user_id)
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Failed to get user by ID: {str(e)}")
            return None
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email address"""
        try:
            query = select(User).where(User.email == email)
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Failed to get user by email: {str(e)}")
            return None
    
    async def get_user_sessions(self, user_id: str) -> List[UserSession]:
        """Get all active sessions for a user"""
        try:
            query = select(UserSession).where(
                and_(
                    UserSession.user_id == user_id,
                    UserSession.is_active == True,
                    UserSession.expires_at > datetime.utcnow()
                )
            ).order_by(UserSession.last_activity.desc())
            
            result = await self.db.execute(query)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Failed to get user sessions: {str(e)}")
            return []
    
    # Private helper methods
    def _hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        return pwd_context.hash(password)
    
    def _verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    def _create_token(self, data: dict, expires_delta: timedelta) -> str:
        """Create JWT token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + expires_delta
        to_encode.update({"exp": expire, "iat": datetime.utcnow()})
        
        encoded_jwt = jwt.encode(
            to_encode,
            settings.SECRET_KEY.get_secret_value(),
            algorithm=settings.ALGORITHM
        )
        
        return encoded_jwt
    
    def _generate_session_id(self) -> str:
        """Generate secure session ID"""
        return f"sess_{secrets.token_urlsafe(32)}"
    
    async def _is_token_blacklisted(self, jti: str) -> bool:
        """Check if token is blacklisted"""
        try:
            query = select(TokenBlacklist).where(
                and_(
                    TokenBlacklist.jti == jti,
                    TokenBlacklist.expires_at > datetime.utcnow()
                )
            )
            result = await self.db.execute(query)
            return result.scalar_one_or_none() is not None
        except Exception:
            return False
    
    async def _blacklist_token(
        self, 
        jti: str, 
        user_id: str, 
        token_type: str, 
        reason: str = None
    ) -> bool:
        """Add token to blacklist"""
        try:
            # Calculate expiration based on token type
            if token_type == TokenType.ACCESS:
                expires_at = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
            else:
                expires_at = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
            
            blacklist_entry = TokenBlacklist(
                jti=jti,
                user_id=user_id,
                token_type=token_type,
                expires_at=expires_at,
                reason=reason
            )
            
            self.db.add(blacklist_entry)
            await self.db.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to blacklist token: {str(e)}")
            return False
    
    async def _get_session_by_id(self, session_id: str, user_id: str) -> Optional[UserSession]:
        """Get session by ID and user ID"""
        try:
            query = select(UserSession).where(
                and_(
                    UserSession.session_id == session_id,
                    UserSession.user_id == user_id,
                    UserSession.is_active == True
                )
            )
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
        except Exception:
            return None
    
    async def _terminate_session(
        self, 
        session_id: str, 
        user_id: str, 
        reason: str = None
    ) -> bool:
        """Terminate a specific session"""
        try:
            query = select(UserSession).where(
                and_(
                    UserSession.session_id == session_id,
                    UserSession.user_id == user_id,
                    UserSession.is_active == True
                )
            )
            result = await self.db.execute(query)
            session = result.scalar_one_or_none()
            
            if session:
                session.terminate(reason)
                await self.db.commit()
                return True
            return False
        except Exception:
            return False
    
    async def _terminate_all_user_sessions(
        self, 
        user_id: str, 
        reason: str = "logout_all"
    ) -> int:
        """Terminate all active sessions for a user"""
        try:
            query = select(UserSession).where(
                and_(
                    UserSession.user_id == user_id,
                    UserSession.is_active == True
                )
            )
            result = await self.db.execute(query)
            sessions = result.scalars().all()
            
            terminated_count = 0
            for session in sessions:
                session.terminate(reason)
                terminated_count += 1
            
            if terminated_count > 0:
                await self.db.commit()
            
            return terminated_count
        except Exception:
            return 0
    
    async def _log_login_attempt(
        self,
        email: str,
        ip_address: str = None,
        user_agent: str = None,
        success: bool = False,
        failure_reason: str = None,
        user_id: str = None
    ) -> None:
        """Log login attempt"""
        try:
            attempt = LoginAttempt(
                email=email,
                ip_address=ip_address,
                user_agent=user_agent,
                success=success,
                failure_reason=failure_reason,
                user_id=user_id
            )
            self.db.add(attempt)
            await self.db.commit()
        except Exception as e:
            logger.error(f"Failed to log login attempt: {str(e)}")
    
    async def _update_login_attempt_success(
        self,
        email: str,
        user_id: str,
        ip_address: str = None
    ) -> None:
        """Update recent login attempt as successful"""
        try:
            # Find the most recent failed attempt for this email/IP
            conditions = [LoginAttempt.email == email, LoginAttempt.success == False]
            if ip_address:
                conditions.append(LoginAttempt.ip_address == ip_address)
            
            query = select(LoginAttempt).where(
                and_(*conditions)
            ).order_by(LoginAttempt.attempted_at.desc()).limit(1)
            
            result = await self.db.execute(query)
            attempt = result.scalar_one_or_none()
            
            if attempt:
                attempt.success = True
                attempt.user_id = user_id
                await self.db.commit()
        except Exception as e:
            logger.error(f"Failed to update login attempt: {str(e)}")
    
    async def _log_security_event(
        self,
        event_type: str,
        event_description: str,
        severity: str,
        user_id: str = None,
        session_id: str = None,
        ip_address: str = None,
        user_agent: str = None,
        metadata: dict = None
    ) -> None:
        """Log security event"""
        try:
            event = SecurityEvent(
                user_id=user_id,
                session_id=session_id,
                event_type=event_type,
                event_description=event_description,
                severity=severity,
                ip_address=ip_address,
                user_agent=user_agent,
                metadata=str(metadata) if metadata else None
            )
            self.db.add(event)
            await self.db.commit()
        except Exception as e:
            logger.error(f"Failed to log security event: {str(e)}")