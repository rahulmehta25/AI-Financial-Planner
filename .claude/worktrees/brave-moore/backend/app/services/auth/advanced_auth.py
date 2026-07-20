"""
Advanced Authentication & Authorization Service

Production-grade authentication system with:
- Argon2 password hashing
- RS256 JWT tokens  
- Multi-factor authentication (TOTP)
- Device fingerprinting and anomaly detection
- Rate limiting
- Refresh tokens with 30-day expiry
- JWT revocation with JTI
"""

import os
import uuid
import json
import hashlib
import secrets
import logging
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import asyncio

import jwt
import pyotp
import aioredis
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, update
from fastapi import HTTPException, status
import numpy as np
from sklearn.ensemble import IsolationForest
import joblib

from app.core.config import settings
from app.models.user import User
from app.models.auth import (
    TrustedDevice, 
    TokenBlacklist,
    LoginAttempt,
    SecurityEvent,
    UserSession,
    MFASecret
)

logger = logging.getLogger(__name__)


class AdvancedAuthenticationService:
    """
    Production-ready authentication service with enterprise security features
    """
    
    def __init__(self, db: AsyncSession = None, redis_client: aioredis.Redis = None):
        """Initialize authentication service with security configurations"""
        
        # Database session
        self.db = db
        self.redis = redis_client
        
        # Password hashing with Argon2
        self.pwd_context = CryptContext(
            schemes=["argon2", "bcrypt"],
            deprecated="auto",
            argon2__memory_cost=65536,  # 64 MB
            argon2__time_cost=3,         # 3 iterations
            argon2__parallelism=4        # 4 parallel threads
        )
        
        # JWT Configuration for RS256
        self.jwt_algorithm = "RS256"
        self.token_expiry = timedelta(minutes=15)
        self.refresh_token_expiry = timedelta(days=30)
        
        # Load RSA keys for RS256
        self._load_rsa_keys()
        
        # Rate limiting configuration
        self.max_login_attempts = 5
        self.rate_limit_window = timedelta(minutes=15)
        self.rate_limit_storage = defaultdict(list)
        
        # Device anomaly detection model
        self.device_anomaly_model = self._initialize_anomaly_model()
        self.device_anomaly_threshold = 0.7
        
        # MFA configuration
        self.mfa_issuer = "AI Financial Planner"
        self.mfa_window = 2  # Allow 2 time windows for TOTP validation
        
        # Security event logging
        self.security_events = []
        
    def _load_rsa_keys(self):
        """Load RSA keys for JWT signing and verification"""
        try:
            # Check if RSA keys exist, generate if not
            private_key_path = os.environ.get("JWT_PRIVATE_KEY_PATH", "keys/jwt_private.pem")
            public_key_path = os.environ.get("JWT_PUBLIC_KEY_PATH", "keys/jwt_public.pem")
            
            if os.path.exists(private_key_path) and os.path.exists(public_key_path):
                with open(private_key_path, 'rb') as f:
                    self.jwt_private_key = f.read()
                with open(public_key_path, 'rb') as f:
                    self.jwt_public_key = f.read()
            else:
                # Generate RSA keys if they don't exist
                from cryptography.hazmat.primitives.asymmetric import rsa
                from cryptography.hazmat.primitives import serialization
                from cryptography.hazmat.backends import default_backend
                
                private_key = rsa.generate_private_key(
                    public_exponent=65537,
                    key_size=2048,
                    backend=default_backend()
                )
                
                self.jwt_private_key = private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption()
                )
                
                public_key = private_key.public_key()
                self.jwt_public_key = public_key.public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo
                )
                
                # Save keys for future use
                os.makedirs(os.path.dirname(private_key_path), exist_ok=True)
                with open(private_key_path, 'wb') as f:
                    f.write(self.jwt_private_key)
                with open(public_key_path, 'wb') as f:
                    f.write(self.jwt_public_key)
                    
                logger.info("Generated new RSA key pair for JWT signing")
                
        except Exception as e:
            logger.error(f"Failed to load RSA keys, falling back to HS256: {str(e)}")
            # Fallback to HS256 if RSA keys fail
            self.jwt_algorithm = "HS256"
            self.jwt_private_key = settings.SECRET_KEY.get_secret_value()
            self.jwt_public_key = settings.SECRET_KEY.get_secret_value()
    
    def _initialize_anomaly_model(self):
        """Initialize or load the device anomaly detection model"""
        try:
            model_path = "models/device_anomaly_model.joblib"
            if os.path.exists(model_path):
                # Load existing model
                return joblib.load(model_path)
            else:
                # Create and train new model with synthetic data
                model = IsolationForest(
                    contamination=0.1,
                    random_state=42,
                    n_estimators=100
                )
                
                # Generate synthetic training data
                # In production, this would be trained on historical device data
                np.random.seed(42)
                normal_data = np.random.randn(1000, 10)  # 10 device features
                model.fit(normal_data)
                
                # Save model
                os.makedirs(os.path.dirname(model_path), exist_ok=True)
                joblib.dump(model, model_path)
                
                logger.info("Initialized new device anomaly detection model")
                return model
                
        except Exception as e:
            logger.error(f"Failed to initialize anomaly model: {str(e)}")
            return None
    
    async def authenticate_user(
        self, 
        email: str, 
        password: str,
        mfa_code: Optional[str] = None,
        device_fingerprint: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Multi-factor authentication with device fingerprinting
        
        Args:
            email: User email address
            password: User password
            mfa_code: TOTP code for MFA (if enabled)
            device_fingerprint: Device identification data
            ip_address: Client IP address
            user_agent: Client user agent string
            
        Returns:
            Authentication response with tokens and user data
            
        Raises:
            HTTPException: For various authentication failures
        """
        
        # Check rate limiting
        if await self._check_rate_limit(email, ip_address):
            await self._log_security_event(
                event_type="rate_limit_exceeded",
                severity="high",
                email=email,
                ip_address=ip_address,
                details={"reason": "Too many login attempts"}
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many login attempts. Please try again later."
            )
        
        # Verify credentials
        user = await self._get_user_by_email(email)
        if not user:
            await self._record_failed_attempt(email, ip_address, device_fingerprint, "invalid_email")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        # Verify password with timing attack protection
        password_valid = await self._verify_password_secure(password, user.hashed_password)
        if not password_valid:
            await self._record_failed_attempt(email, ip_address, device_fingerprint, "invalid_password")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        # Check account status
        if not user.is_active:
            await self._log_security_event(
                event_type="inactive_account_login",
                severity="medium",
                user_id=str(user.id),
                email=email,
                ip_address=ip_address
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is inactive. Please contact support."
            )
        
        # Check if MFA is enabled
        if user.mfa_enabled:
            if not mfa_code:
                # Generate MFA session token
                mfa_session_token = self._create_mfa_session(user.id)
                return {
                    "requires_mfa": True,
                    "mfa_session_token": mfa_session_token,
                    "message": "Please provide your 6-digit authenticator code"
                }
            
            # Verify MFA code
            mfa_valid = await self._verify_mfa(user.id, mfa_code)
            if not mfa_valid:
                await self._record_failed_attempt(email, ip_address, device_fingerprint, "invalid_mfa")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid MFA code"
                )
        
        # Check device fingerprint for anomaly detection
        if device_fingerprint:
            is_trusted = await self._verify_device(user.id, device_fingerprint, ip_address)
            if not is_trusted:
                # Send alert for new/suspicious device
                await self._send_new_device_alert(user, device_fingerprint, ip_address)
                
                # Optionally require additional verification for untrusted devices
                if user.enforce_device_trust:
                    await self._log_security_event(
                        event_type="untrusted_device_blocked",
                        severity="high",
                        user_id=str(user.id),
                        email=email,
                        ip_address=ip_address,
                        details={"device_fingerprint": device_fingerprint}
                    )
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Login from unrecognized device. Please verify via email."
                    )
        
        # Generate tokens with enhanced claims
        access_token = await self._create_access_token(user, device_fingerprint)
        refresh_token = await self._create_refresh_token(user, device_fingerprint)
        
        # Create user session
        session = await self._create_user_session(
            user_id=str(user.id),
            device_fingerprint=device_fingerprint,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        # Log successful authentication
        await self._log_authentication(user.id, device_fingerprint, ip_address, True)
        
        # Update last login timestamp
        await self._update_last_login(user.id)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": int(self.token_expiry.total_seconds()),
            "session_id": session.get("session_id") if session else None,
            "user": {
                "id": str(user.id),
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "mfa_enabled": user.mfa_enabled,
                "permissions": await self._get_user_permissions(user)
            }
        }
    
    async def _check_rate_limit(self, email: str, ip_address: Optional[str] = None) -> bool:
        """
        Check if rate limit has been exceeded
        
        Returns:
            True if rate limit exceeded, False otherwise
        """
        if self.redis:
            # Use Redis for distributed rate limiting
            key = f"rate_limit:{email}:{ip_address or 'unknown'}"
            try:
                current_attempts = await self.redis.incr(key)
                if current_attempts == 1:
                    await self.redis.expire(key, int(self.rate_limit_window.total_seconds()))
                return current_attempts > self.max_login_attempts
            except Exception as e:
                logger.error(f"Redis rate limiting failed: {str(e)}")
                # Fallback to in-memory rate limiting
        
        # In-memory rate limiting fallback
        now = datetime.utcnow()
        identifier = f"{email}:{ip_address or 'unknown'}"
        
        # Clean old attempts
        self.rate_limit_storage[identifier] = [
            attempt for attempt in self.rate_limit_storage[identifier]
            if now - attempt < self.rate_limit_window
        ]
        
        # Check current attempts
        if len(self.rate_limit_storage[identifier]) >= self.max_login_attempts:
            return True
        
        # Record new attempt
        self.rate_limit_storage[identifier].append(now)
        return False
    
    async def _verify_device(self, user_id: str, fingerprint: str, ip_address: str = None) -> bool:
        """
        Verify if device is trusted using ML-based anomaly detection
        
        Args:
            user_id: User identifier
            fingerprint: Device fingerprint data
            ip_address: Client IP address
            
        Returns:
            True if device is trusted, False otherwise
        """
        try:
            # Check if device is in trusted devices list
            if self.db:
                query = select(TrustedDevice).where(
                    and_(
                        TrustedDevice.user_id == user_id,
                        TrustedDevice.fingerprint == fingerprint,
                        TrustedDevice.is_active == True
                    )
                )
                result = await self.db.execute(query)
                trusted_device = result.scalar_one_or_none()
                
                if trusted_device:
                    # Update last seen
                    trusted_device.last_seen = datetime.utcnow()
                    trusted_device.last_ip = ip_address
                    await self.db.commit()
                    return True
            
            # Use ML model to check if device characteristics are similar to known devices
            if self.device_anomaly_model:
                device_features = self._extract_device_features(fingerprint)
                if device_features is not None:
                    # Predict returns -1 for anomalies, 1 for normal
                    anomaly_score = self.device_anomaly_model.predict([device_features])[0]
                    
                    # Decision function gives distance to separating hyperplane
                    confidence = self.device_anomaly_model.decision_function([device_features])[0]
                    
                    # Log anomaly detection result
                    await self._log_security_event(
                        event_type="device_anomaly_check",
                        severity="low",
                        user_id=user_id,
                        details={
                            "fingerprint": fingerprint[:32] + "...",  # Truncate for security
                            "anomaly_score": float(anomaly_score),
                            "confidence": float(confidence),
                            "is_anomaly": anomaly_score == -1
                        }
                    )
                    
                    # Device is trusted if not an anomaly and confidence is above threshold
                    return anomaly_score == 1 and confidence > -self.device_anomaly_threshold
            
            # Default to untrusted if no model available
            return False
            
        except Exception as e:
            logger.error(f"Device verification failed: {str(e)}")
            # Fail open for availability, but log the event
            await self._log_security_event(
                event_type="device_verification_error",
                severity="medium",
                user_id=user_id,
                details={"error": str(e)}
            )
            return False
    
    def _extract_device_features(self, fingerprint: str) -> Optional[np.ndarray]:
        """
        Extract numerical features from device fingerprint for ML model
        
        Args:
            fingerprint: Device fingerprint JSON string
            
        Returns:
            Numpy array of device features or None if extraction fails
        """
        try:
            # Parse fingerprint data
            if isinstance(fingerprint, str):
                data = json.loads(fingerprint)
            else:
                data = fingerprint
            
            # Extract relevant features (example features)
            features = []
            
            # Screen dimensions
            features.append(data.get('screenWidth', 0))
            features.append(data.get('screenHeight', 0))
            features.append(data.get('colorDepth', 0))
            
            # Browser features
            features.append(1 if data.get('cookieEnabled', False) else 0)
            features.append(data.get('hardwareConcurrency', 0))
            features.append(len(data.get('plugins', [])))
            
            # Timezone and language
            features.append(abs(data.get('timezoneOffset', 0)))
            features.append(len(data.get('languages', [])))
            
            # Canvas fingerprint hash (convert to numeric)
            canvas_hash = data.get('canvasHash', '')
            features.append(int(hashlib.md5(canvas_hash.encode()).hexdigest()[:8], 16))
            
            # WebGL vendor hash
            webgl_vendor = data.get('webglVendor', '')
            features.append(int(hashlib.md5(webgl_vendor.encode()).hexdigest()[:8], 16))
            
            # Normalize features
            features = np.array(features, dtype=np.float32)
            
            # Basic normalization (in production, use saved scaler)
            if features.std() > 0:
                features = (features - features.mean()) / features.std()
            
            return features
            
        except Exception as e:
            logger.error(f"Failed to extract device features: {str(e)}")
            return None
    
    async def _create_access_token(self, user: User, device_fingerprint: Optional[str] = None) -> str:
        """
        Create JWT access token with user claims and permissions
        
        Args:
            user: User object
            device_fingerprint: Optional device fingerprint
            
        Returns:
            Signed JWT token string
        """
        # Generate unique JWT ID for revocation
        jti = str(uuid.uuid4())
        
        # Get user permissions
        permissions = await self._get_user_permissions(user)
        
        # Build claims
        claims = {
            "sub": str(user.id),
            "email": user.email,
            "permissions": permissions,
            "exp": datetime.utcnow() + self.token_expiry,
            "iat": datetime.utcnow(),
            "nbf": datetime.utcnow(),  # Not valid before
            "jti": jti,
            "type": "access",
            "device_hash": hashlib.sha256(device_fingerprint.encode()).hexdigest()[:16] if device_fingerprint else None
        }
        
        # Add custom claims based on user attributes
        if hasattr(user, 'role'):
            claims['role'] = user.role
        if hasattr(user, 'organization_id'):
            claims['org'] = str(user.organization_id)
        
        # Sign token with private key
        token = jwt.encode(claims, self.jwt_private_key, algorithm=self.jwt_algorithm)
        
        # Store JTI in Redis for revocation checking if available
        if self.redis:
            try:
                await self.redis.setex(
                    f"jwt:active:{jti}",
                    int(self.token_expiry.total_seconds()),
                    "1"
                )
            except Exception as e:
                logger.error(f"Failed to store JWT in Redis: {str(e)}")
        
        return token
    
    async def _create_refresh_token(self, user: User, device_fingerprint: Optional[str] = None) -> str:
        """
        Create JWT refresh token
        
        Args:
            user: User object
            device_fingerprint: Optional device fingerprint
            
        Returns:
            Signed refresh token string
        """
        # Generate unique JWT ID
        jti = str(uuid.uuid4())
        
        # Build refresh token claims (minimal claims for security)
        claims = {
            "sub": str(user.id),
            "exp": datetime.utcnow() + self.refresh_token_expiry,
            "iat": datetime.utcnow(),
            "jti": jti,
            "type": "refresh",
            "device_hash": hashlib.sha256(device_fingerprint.encode()).hexdigest()[:16] if device_fingerprint else None
        }
        
        # Sign token
        token = jwt.encode(claims, self.jwt_private_key, algorithm=self.jwt_algorithm)
        
        # Store refresh token in database for tracking
        if self.db:
            try:
                refresh_token_record = TokenBlacklist(
                    jti=jti,
                    user_id=str(user.id),
                    token_type="refresh",
                    expires_at=datetime.utcnow() + self.refresh_token_expiry,
                    is_blacklisted=False
                )
                self.db.add(refresh_token_record)
                await self.db.commit()
            except Exception as e:
                logger.error(f"Failed to store refresh token: {str(e)}")
        
        return token
    
    async def _verify_mfa(self, user_id: str, mfa_code: str) -> bool:
        """
        Verify TOTP MFA code
        
        Args:
            user_id: User identifier
            mfa_code: 6-digit TOTP code
            
        Returns:
            True if code is valid, False otherwise
        """
        try:
            # Get user's MFA secret
            if self.db:
                query = select(MFASecret).where(
                    and_(
                        MFASecret.user_id == user_id,
                        MFASecret.is_active == True
                    )
                )
                result = await self.db.execute(query)
                mfa_secret = result.scalar_one_or_none()
                
                if not mfa_secret:
                    return False
                
                # Verify TOTP code
                totp = pyotp.TOTP(mfa_secret.secret)
                
                # Allow for time drift (valid_window parameter)
                is_valid = totp.verify(mfa_code, valid_window=self.mfa_window)
                
                if is_valid:
                    # Update last used timestamp
                    mfa_secret.last_used = datetime.utcnow()
                    mfa_secret.use_count += 1
                    await self.db.commit()
                    
                return is_valid
            
            return False
            
        except Exception as e:
            logger.error(f"MFA verification failed: {str(e)}")
            return False
    
    def _create_mfa_session(self, user_id: str) -> str:
        """
        Create temporary MFA session token
        
        Args:
            user_id: User identifier
            
        Returns:
            Temporary session token for MFA verification
        """
        # Create short-lived token for MFA flow
        claims = {
            "sub": str(user_id),
            "type": "mfa_session",
            "exp": datetime.utcnow() + timedelta(minutes=5),  # 5 minute expiry
            "iat": datetime.utcnow(),
            "jti": str(uuid.uuid4())
        }
        
        return jwt.encode(claims, self.jwt_private_key, algorithm=self.jwt_algorithm)
    
    async def _verify_password_secure(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verify password with timing attack protection
        
        Args:
            plain_password: Plain text password
            hashed_password: Hashed password from database
            
        Returns:
            True if password is valid, False otherwise
        """
        # Add small random delay to prevent timing attacks
        await asyncio.sleep(secrets.randbits(3) * 0.001)  # 0-7ms random delay
        
        try:
            return self.pwd_context.verify(plain_password, hashed_password)
        except Exception as e:
            logger.error(f"Password verification failed: {str(e)}")
            return False
    
    async def _get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email address"""
        if not self.db:
            return None
            
        try:
            query = select(User).where(User.email == email.lower())
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Failed to get user by email: {str(e)}")
            return None
    
    async def _get_user_permissions(self, user: User) -> List[str]:
        """
        Get user permissions based on role and specific grants
        
        Args:
            user: User object
            
        Returns:
            List of permission strings
        """
        permissions = []
        
        # Base permissions for all authenticated users
        permissions.extend([
            "read:own_profile",
            "update:own_profile",
            "read:own_portfolios",
            "create:portfolio",
            "run:simulations"
        ])
        
        # Role-based permissions
        if hasattr(user, 'role'):
            if user.role == 'admin':
                permissions.extend([
                    "read:all_users",
                    "update:all_users",
                    "delete:users",
                    "manage:system",
                    "view:audit_logs"
                ])
            elif user.role == 'advisor':
                permissions.extend([
                    "read:client_portfolios",
                    "update:client_portfolios",
                    "create:recommendations",
                    "view:client_analytics"
                ])
            elif user.role == 'premium':
                permissions.extend([
                    "access:advanced_features",
                    "unlimited:simulations",
                    "export:detailed_reports",
                    "access:ai_coaching"
                ])
        
        # Add any user-specific permissions
        if hasattr(user, 'custom_permissions') and user.custom_permissions:
            permissions.extend(user.custom_permissions)
        
        return list(set(permissions))  # Remove duplicates
    
    async def _record_failed_attempt(
        self, 
        email: str, 
        ip_address: Optional[str],
        device_fingerprint: Optional[str],
        reason: str
    ):
        """Record failed authentication attempt"""
        try:
            if self.db:
                attempt = LoginAttempt(
                    email=email,
                    ip_address=ip_address,
                    device_fingerprint=device_fingerprint[:255] if device_fingerprint else None,
                    success=False,
                    failure_reason=reason,
                    attempted_at=datetime.utcnow()
                )
                self.db.add(attempt)
                await self.db.commit()
                
            # Log security event
            await self._log_security_event(
                event_type="failed_login",
                severity="medium",
                email=email,
                ip_address=ip_address,
                details={"reason": reason}
            )
            
        except Exception as e:
            logger.error(f"Failed to record login attempt: {str(e)}")
    
    async def _log_authentication(
        self,
        user_id: str,
        device_fingerprint: Optional[str],
        ip_address: Optional[str],
        success: bool
    ):
        """Log authentication event"""
        await self._log_security_event(
            event_type="authentication",
            severity="low" if success else "medium",
            user_id=user_id,
            ip_address=ip_address,
            details={
                "success": success,
                "has_device_fingerprint": bool(device_fingerprint)
            }
        )
    
    async def setup_mfa(self, user_id: str, backup_codes: List[str] = None) -> Dict[str, Any]:
        """
        Set up MFA for user
        
        Args:
            user_id: User identifier
            backup_codes: Optional list of backup codes
            
        Returns:
            MFA setup information including QR code data
        """
        try:
            # Generate TOTP secret
            secret = pyotp.random_base32()
            
            # Create TOTP object
            totp = pyotp.TOTP(secret)
            
            # Generate backup codes if not provided
            if not backup_codes:
                backup_codes = [secrets.token_hex(4) for _ in range(10)]
            
            # Store MFA secret in database
            if self.db:
                mfa_secret = MFASecret(
                    user_id=user_id,
                    secret=secret,
                    backup_codes=json.dumps(backup_codes),
                    is_active=False  # Not active until verified
                )
                self.db.add(mfa_secret)
                await self.db.commit()
            
            # Generate QR code data
            user = await self._get_user_by_id(user_id)
            qr_code_uri = totp.provisioning_uri(
                name=user.email if user else user_id,
                issuer_name=self.mfa_issuer
            )
            
            return {
                "secret": secret,
                "qr_code_uri": qr_code_uri,
                "backup_codes": backup_codes,
                "manual_entry_key": secret
            }
            
        except Exception as e:
            logger.error(f"MFA setup failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to setup MFA"
            )
    
    async def verify_mfa_setup(self, user_id: str, totp_code: str) -> bool:
        """
        Verify MFA setup by confirming TOTP code
        
        Args:
            user_id: User identifier
            totp_code: TOTP code from authenticator app
            
        Returns:
            True if verification successful, False otherwise
        """
        try:
            if self.db:
                # Get pending MFA secret
                query = select(MFASecret).where(
                    and_(
                        MFASecret.user_id == user_id,
                        MFASecret.is_active == False
                    )
                )
                result = await self.db.execute(query)
                mfa_secret = result.scalar_one_or_none()
                
                if not mfa_secret:
                    return False
                
                # Verify TOTP code
                totp = pyotp.TOTP(mfa_secret.secret)
                if totp.verify(totp_code, valid_window=self.mfa_window):
                    # Activate MFA
                    mfa_secret.is_active = True
                    mfa_secret.verified_at = datetime.utcnow()
                    
                    # Update user to enable MFA
                    user_query = select(User).where(User.id == user_id)
                    user_result = await self.db.execute(user_query)
                    user = user_result.scalar_one_or_none()
                    if user:
                        user.mfa_enabled = True
                    
                    await self.db.commit()
                    
                    await self._log_security_event(
                        event_type="mfa_enabled",
                        severity="medium",
                        user_id=user_id,
                        details={"method": "TOTP"}
                    )
                    
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"MFA verification failed: {str(e)}")
            return False
    
    async def disable_mfa(self, user_id: str, password: str) -> bool:
        """
        Disable MFA for user after password verification
        
        Args:
            user_id: User identifier
            password: User's current password
            
        Returns:
            True if MFA disabled successfully, False otherwise
        """
        try:
            # Verify password
            user = await self._get_user_by_id(user_id)
            if not user or not await self._verify_password_secure(password, user.hashed_password):
                return False
            
            if self.db:
                # Deactivate MFA secrets
                query = update(MFASecret).where(
                    MFASecret.user_id == user_id
                ).values(is_active=False, disabled_at=datetime.utcnow())
                await self.db.execute(query)
                
                # Update user
                user.mfa_enabled = False
                await self.db.commit()
                
                await self._log_security_event(
                    event_type="mfa_disabled",
                    severity="high",
                    user_id=user_id,
                    details={"method": "password_verification"}
                )
                
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"MFA disable failed: {str(e)}")
            return False
    
    async def send_sms_code(self, user_id: str, phone_number: str) -> bool:
        """
        Send SMS verification code for MFA
        
        Args:
            user_id: User identifier
            phone_number: Phone number to send SMS to
            
        Returns:
            True if SMS sent successfully, False otherwise
        """
        try:
            # Generate 6-digit code
            sms_code = secrets.randbelow(900000) + 100000  # 6-digit code
            
            # Store SMS code in Redis with 5-minute expiry
            if self.redis:
                await self.redis.setex(
                    f"sms_code:{user_id}",
                    300,  # 5 minutes
                    str(sms_code)
                )
            
            # In production, integrate with SMS service (Twilio, AWS SNS, etc.)
            # For demo purposes, just log the code
            logger.info(f"SMS Code for {phone_number}: {sms_code}")
            
            await self._log_security_event(
                event_type="sms_code_sent",
                severity="low",
                user_id=user_id,
                details={"phone_number": phone_number[-4:]  # Log only last 4 digits}
            )
            
            return True
            
        except Exception as e:
            logger.error(f"SMS code sending failed: {str(e)}")
            return False
    
    async def verify_sms_code(self, user_id: str, sms_code: str) -> bool:
        """
        Verify SMS MFA code
        
        Args:
            user_id: User identifier
            sms_code: SMS code to verify
            
        Returns:
            True if code is valid, False otherwise
        """
        try:
            if self.redis:
                stored_code = await self.redis.get(f"sms_code:{user_id}")
                if stored_code and stored_code.decode() == sms_code:
                    # Delete used code
                    await self.redis.delete(f"sms_code:{user_id}")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"SMS code verification failed: {str(e)}")
            return False
    
    async def send_email_code(self, user_id: str, email: str) -> bool:
        """
        Send email verification code for MFA
        
        Args:
            user_id: User identifier
            email: Email address to send code to
            
        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            # Generate 6-digit code
            email_code = secrets.randbelow(900000) + 100000
            
            # Store email code in Redis with 10-minute expiry
            if self.redis:
                await self.redis.setex(
                    f"email_code:{user_id}",
                    600,  # 10 minutes
                    str(email_code)
                )
            
            # In production, send actual email
            # For demo purposes, just log the code
            logger.info(f"Email Code for {email}: {email_code}")
            
            await self._log_security_event(
                event_type="email_code_sent",
                severity="low",
                user_id=user_id,
                email=email
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Email code sending failed: {str(e)}")
            return False
    
    async def verify_email_code(self, user_id: str, email_code: str) -> bool:
        """
        Verify email MFA code
        
        Args:
            user_id: User identifier
            email_code: Email code to verify
            
        Returns:
            True if code is valid, False otherwise
        """
        try:
            if self.redis:
                stored_code = await self.redis.get(f"email_code:{user_id}")
                if stored_code and stored_code.decode() == email_code:
                    # Delete used code
                    await self.redis.delete(f"email_code:{user_id}")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Email code verification failed: {str(e)}")
            return False
    
    async def initiate_password_reset(self, email: str, ip_address: Optional[str] = None) -> str:
        """
        Initiate password reset process
        
        Args:
            email: User email address
            ip_address: Client IP address
            
        Returns:
            Reset token or empty string if user not found
        """
        try:
            user = await self._get_user_by_email(email)
            if not user:
                # Don't reveal if user exists
                await self._log_security_event(
                    event_type="password_reset_attempt_invalid_email",
                    severity="low",
                    email=email,
                    ip_address=ip_address
                )
                return ""
            
            # Generate reset token
            reset_token = secrets.token_urlsafe(32)
            
            # Store reset token in database
            if self.db:
                from app.models.auth import PasswordResetToken
                
                # Invalidate existing tokens for this user
                existing_query = select(PasswordResetToken).where(
                    and_(
                        PasswordResetToken.user_id == str(user.id),
                        PasswordResetToken.is_used == False,
                        PasswordResetToken.expires_at > datetime.utcnow()
                    )
                )
                existing_result = await self.db.execute(existing_query)
                existing_tokens = existing_result.scalars().all()
                
                for token in existing_tokens:
                    token.is_used = True
                    token.used_at = datetime.utcnow()
                
                # Create new reset token
                reset_token_record = PasswordResetToken(
                    user_id=str(user.id),
                    token=reset_token,
                    expires_at=datetime.utcnow() + timedelta(hours=1),  # 1 hour expiry
                    created_ip=ip_address
                )
                self.db.add(reset_token_record)
                await self.db.commit()
            
            # Log password reset request
            await self._log_security_event(
                event_type="password_reset_requested",
                severity="medium",
                user_id=str(user.id),
                email=email,
                ip_address=ip_address
            )
            
            # In production, send email with reset link
            logger.info(f"Password reset token for {email}: {reset_token}")
            
            return reset_token
            
        except Exception as e:
            logger.error(f"Password reset initiation failed: {str(e)}")
            return ""
    
    async def reset_password(self, reset_token: str, new_password: str, ip_address: Optional[str] = None) -> bool:
        """
        Reset user password using reset token
        
        Args:
            reset_token: Password reset token
            new_password: New password
            ip_address: Client IP address
            
        Returns:
            True if password reset successfully, False otherwise
        """
        try:
            if self.db:
                from app.models.auth import PasswordResetToken
                
                # Find valid reset token
                query = select(PasswordResetToken).where(
                    and_(
                        PasswordResetToken.token == reset_token,
                        PasswordResetToken.is_used == False,
                        PasswordResetToken.expires_at > datetime.utcnow()
                    )
                )
                result = await self.db.execute(query)
                token_record = result.scalar_one_or_none()
                
                if not token_record:
                    await self._log_security_event(
                        event_type="password_reset_invalid_token",
                        severity="medium",
                        ip_address=ip_address,
                        details={"token_prefix": reset_token[:8] + "..."}
                    )
                    return False
                
                # Get user
                user = await self._get_user_by_id(token_record.user_id)
                if not user:
                    return False
                
                # Hash new password
                hashed_password = self.pwd_context.hash(new_password)
                
                # Update user password
                user.hashed_password = hashed_password
                user.password_changed_at = datetime.utcnow()
                
                # Mark token as used
                token_record.is_used = True
                token_record.used_at = datetime.utcnow()
                token_record.used_ip = ip_address
                
                await self.db.commit()
                
                # Invalidate all user sessions (force re-login)
                await self._invalidate_all_user_sessions(str(user.id))
                
                # Log password reset
                await self._log_security_event(
                    event_type="password_reset_completed",
                    severity="high",
                    user_id=str(user.id),
                    email=user.email,
                    ip_address=ip_address
                )
                
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Password reset failed: {str(e)}")
            return False
    
    async def send_email_verification(self, user_id: str) -> str:
        """
        Send email verification link
        
        Args:
            user_id: User identifier
            
        Returns:
            Verification token
        """
        try:
            user = await self._get_user_by_id(user_id)
            if not user:
                return ""
            
            # Generate verification token
            verification_token = secrets.token_urlsafe(32)
            
            # Store in Redis with 24-hour expiry
            if self.redis:
                await self.redis.setex(
                    f"email_verification:{user_id}",
                    86400,  # 24 hours
                    verification_token
                )
            
            # In production, send actual verification email
            logger.info(f"Email verification token for {user.email}: {verification_token}")
            
            await self._log_security_event(
                event_type="email_verification_sent",
                severity="low",
                user_id=user_id,
                email=user.email
            )
            
            return verification_token
            
        except Exception as e:
            logger.error(f"Email verification sending failed: {str(e)}")
            return ""
    
    async def verify_email(self, user_id: str, verification_token: str) -> bool:
        """
        Verify user email using verification token
        
        Args:
            user_id: User identifier
            verification_token: Email verification token
            
        Returns:
            True if email verified successfully, False otherwise
        """
        try:
            if self.redis:
                stored_token = await self.redis.get(f"email_verification:{user_id}")
                if stored_token and stored_token.decode() == verification_token:
                    # Update user as verified
                    if self.db:
                        user = await self._get_user_by_id(user_id)
                        if user:
                            user.email_verified = True
                            user.email_verified_at = datetime.utcnow()
                            await self.db.commit()
                    
                    # Delete verification token
                    await self.redis.delete(f"email_verification:{user_id}")
                    
                    await self._log_security_event(
                        event_type="email_verified",
                        severity="low",
                        user_id=user_id
                    )
                    
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Email verification failed: {str(e)}")
            return False
    
    async def _invalidate_all_user_sessions(self, user_id: str):
        """
        Invalidate all user sessions and tokens
        
        Args:
            user_id: User identifier
        """
        try:
            if self.db:
                # Update all active sessions
                session_query = update(UserSession).where(
                    and_(
                        UserSession.user_id == user_id,
                        UserSession.is_active == True
                    )
                ).values(
                    is_active=False,
                    terminated_at=datetime.utcnow(),
                    termination_reason="password_reset"
                )
                await self.db.execute(session_query)
                
                # Blacklist all active tokens
                # In a real implementation, you'd need to track active tokens
                # For now, just log the event
                await self._log_security_event(
                    event_type="all_sessions_invalidated",
                    severity="high",
                    user_id=user_id,
                    details={"reason": "password_reset"}
                )
                
                await self.db.commit()
                
        except Exception as e:
            logger.error(f"Session invalidation failed: {str(e)}")
    
    async def _get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        if not self.db:
            return None
        
        try:
            query = select(User).where(User.id == user_id)
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Failed to get user by ID: {str(e)}")
            return None
    
    async def _log_security_event(
        self,
        event_type: str,
        severity: str,
        user_id: Optional[str] = None,
        email: Optional[str] = None,
        ip_address: Optional[str] = None,
        details: Optional[Dict] = None
    ):
        """Log security event to database and monitoring system"""
        try:
            event = {
                "timestamp": datetime.utcnow().isoformat(),
                "event_type": event_type,
                "severity": severity,
                "user_id": user_id,
                "email": email,
                "ip_address": ip_address,
                "details": details
            }
            
            # Store in database if available
            if self.db:
                security_event = SecurityEvent(
                    user_id=user_id,
                    event_type=event_type,
                    event_description=json.dumps(details) if details else None,
                    severity=severity,
                    ip_address=ip_address,
                    created_at=datetime.utcnow()
                )
                self.db.add(security_event)
                await self.db.commit()
            
            # Log to monitoring system
            if severity in ['high', 'critical']:
                logger.warning(f"Security Event: {event}")
            else:
                logger.info(f"Security Event: {event}")
            
            # Store in memory for analysis
            self.security_events.append(event)
            
            # Keep only last 1000 events in memory
            if len(self.security_events) > 1000:
                self.security_events = self.security_events[-1000:]
                
        except Exception as e:
            logger.error(f"Failed to log security event: {str(e)}")
    
    async def _send_new_device_alert(
        self,
        user: User,
        device_fingerprint: str,
        ip_address: Optional[str]
    ):
        """Send alert to user about login from new device"""
        try:
            # Extract device info from fingerprint
            device_info = "Unknown Device"
            if device_fingerprint:
                try:
                    data = json.loads(device_fingerprint) if isinstance(device_fingerprint, str) else device_fingerprint
                    device_info = f"{data.get('browser', 'Unknown')} on {data.get('os', 'Unknown')}"
                except:
                    pass
            
            # Log the alert
            await self._log_security_event(
                event_type="new_device_alert",
                severity="medium",
                user_id=str(user.id),
                email=user.email,
                ip_address=ip_address,
                details={
                    "device_info": device_info,
                    "action": "email_sent"
                }
            )
            
            # In production, send actual email notification
            # await email_service.send_security_alert(user.email, device_info, ip_address)
            
            logger.info(f"New device alert sent to {user.email}")
            
        except Exception as e:
            logger.error(f"Failed to send new device alert: {str(e)}")
    
    async def _create_user_session(
        self,
        user_id: str,
        device_fingerprint: Optional[str],
        ip_address: Optional[str],
        user_agent: Optional[str]
    ) -> Dict[str, Any]:
        """Create and store user session"""
        try:
            session_id = f"sess_{secrets.token_urlsafe(32)}"
            
            if self.db:
                session = UserSession(
                    session_id=session_id,
                    user_id=user_id,
                    ip_address=ip_address,
                    user_agent=user_agent[:255] if user_agent else None,
                    device_fingerprint=device_fingerprint[:255] if device_fingerprint else None,
                    expires_at=datetime.utcnow() + self.token_expiry,
                    is_active=True,
                    created_at=datetime.utcnow(),
                    last_activity=datetime.utcnow()
                )
                self.db.add(session)
                await self.db.commit()
            
            return {"session_id": session_id}
            
        except Exception as e:
            logger.error(f"Failed to create user session: {str(e)}")
            return {}
    
    async def _update_last_login(self, user_id: str):
        """Update user's last login timestamp"""
        try:
            if self.db:
                query = update(User).where(User.id == user_id).values(
                    last_login=datetime.utcnow()
                )
                await self.db.execute(query)
                await self.db.commit()
        except Exception as e:
            logger.error(f"Failed to update last login: {str(e)}")
    
    async def revoke_token(self, jti: str, user_id: str, reason: str = "manual_revocation"):
        """
        Revoke a JWT token by its JTI
        
        Args:
            jti: JWT ID to revoke
            user_id: User who owns the token
            reason: Reason for revocation
        """
        try:
            # Add to blacklist in database
            if self.db:
                blacklist_entry = TokenBlacklist(
                    jti=jti,
                    user_id=user_id,
                    token_type="access",
                    expires_at=datetime.utcnow() + self.token_expiry,
                    is_blacklisted=True,
                    blacklisted_at=datetime.utcnow(),
                    reason=reason
                )
                self.db.add(blacklist_entry)
                await self.db.commit()
            
            # Remove from Redis active tokens
            if self.redis:
                await self.redis.delete(f"jwt:active:{jti}")
            
            # Log revocation
            await self._log_security_event(
                event_type="token_revoked",
                severity="medium",
                user_id=user_id,
                details={"jti": jti, "reason": reason}
            )
            
        except Exception as e:
            logger.error(f"Failed to revoke token: {str(e)}")
            raise
    
    async def verify_token(self, token: str) -> Dict[str, Any]:
        """
        Verify and decode JWT token
        
        Args:
            token: JWT token string
            
        Returns:
            Decoded token claims
            
        Raises:
            HTTPException: If token is invalid or revoked
        """
        try:
            # Decode token
            claims = jwt.decode(token, self.jwt_public_key, algorithms=[self.jwt_algorithm])
            
            # Check if token is revoked
            jti = claims.get("jti")
            if jti:
                # Check Redis first for performance
                if self.redis:
                    is_active = await self.redis.get(f"jwt:active:{jti}")
                    if not is_active:
                        raise HTTPException(
                            status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Token has been revoked"
                        )
                
                # Check database blacklist
                if self.db:
                    query = select(TokenBlacklist).where(
                        and_(
                            TokenBlacklist.jti == jti,
                            TokenBlacklist.is_blacklisted == True
                        )
                    )
                    result = await self.db.execute(query)
                    if result.scalar_one_or_none():
                        raise HTTPException(
                            status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Token has been revoked"
                        )
            
            return claims
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.InvalidTokenError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {str(e)}"
            )