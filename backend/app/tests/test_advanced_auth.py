"""
Test suite for Advanced Authentication & Authorization Service

Tests cover:
- Argon2 password hashing
- RS256 JWT tokens
- Multi-factor authentication
- Device fingerprinting
- Rate limiting
- Token revocation
"""

import pytest
import json
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
import uuid

from app.services.auth.advanced_auth import AdvancedAuthenticationService
from app.models.user import User
from app.models.auth import TrustedDevice, MFASecret
from fastapi import HTTPException


@pytest.fixture
async def auth_service():
    """Create authentication service instance for testing"""
    service = AdvancedAuthenticationService()
    service.db = AsyncMock()
    service.redis = AsyncMock()
    return service


@pytest.fixture
def sample_user():
    """Create sample user for testing"""
    user = Mock(spec=User)
    user.id = uuid.uuid4()
    user.email = "test@example.com"
    user.first_name = "Test"
    user.last_name = "User"
    user.hashed_password = "$argon2id$v=19$m=65536,t=3,p=4$..."  # Mock hash
    user.is_active = True
    user.mfa_enabled = False
    user.enforce_device_trust = False
    user.role = "user"
    return user


@pytest.fixture
def device_fingerprint():
    """Create sample device fingerprint"""
    return json.dumps({
        "screenWidth": 1920,
        "screenHeight": 1080,
        "colorDepth": 24,
        "cookieEnabled": True,
        "hardwareConcurrency": 8,
        "plugins": ["Chrome PDF Plugin", "Chrome PDF Viewer"],
        "timezoneOffset": -480,
        "languages": ["en-US", "en"],
        "canvasHash": "abc123def456",
        "webglVendor": "Intel Inc.",
        "browser": "Chrome",
        "os": "Windows 10"
    })


class TestPasswordHashing:
    """Test Argon2 password hashing implementation"""
    
    @pytest.mark.asyncio
    async def test_argon2_configuration(self, auth_service):
        """Test that Argon2 is properly configured"""
        assert "argon2" in auth_service.pwd_context.schemes
        
        # Test password hashing
        password = "SecureP@ssw0rd123!"
        hashed = auth_service.pwd_context.hash(password)
        
        # Verify it's an Argon2 hash
        assert hashed.startswith("$argon2")
        
        # Verify password
        assert auth_service.pwd_context.verify(password, hashed)
        assert not auth_service.pwd_context.verify("wrong_password", hashed)
    
    @pytest.mark.asyncio
    async def test_timing_attack_protection(self, auth_service):
        """Test timing attack protection in password verification"""
        password = "TestPassword123!"
        hashed = auth_service.pwd_context.hash(password)
        
        # Measure verification times
        start = datetime.utcnow()
        result = await auth_service._verify_password_secure(password, hashed)
        duration1 = (datetime.utcnow() - start).total_seconds()
        
        start = datetime.utcnow()
        result = await auth_service._verify_password_secure("wrong", hashed)
        duration2 = (datetime.utcnow() - start).total_seconds()
        
        # Both should have added random delay
        assert duration1 > 0
        assert duration2 > 0


class TestJWTTokens:
    """Test RS256 JWT token implementation"""
    
    @pytest.mark.asyncio
    async def test_rsa_key_generation(self, auth_service):
        """Test RSA key generation for JWT signing"""
        # Keys should be loaded/generated
        assert auth_service.jwt_private_key is not None
        assert auth_service.jwt_public_key is not None
        
        # If RS256 is available
        if auth_service.jwt_algorithm == "RS256":
            assert b"BEGIN RSA PRIVATE KEY" in auth_service.jwt_private_key or \
                   b"BEGIN PRIVATE KEY" in auth_service.jwt_private_key
            assert b"BEGIN PUBLIC KEY" in auth_service.jwt_public_key
    
    @pytest.mark.asyncio
    async def test_access_token_creation(self, auth_service, sample_user, device_fingerprint):
        """Test access token creation with proper claims"""
        token = await auth_service._create_access_token(sample_user, device_fingerprint)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 50  # JWT tokens are typically long
        
        # Decode and verify claims (without signature verification for test)
        import jwt
        claims = jwt.decode(token, options={"verify_signature": False})
        
        assert claims["sub"] == str(sample_user.id)
        assert claims["email"] == sample_user.email
        assert claims["type"] == "access"
        assert "jti" in claims  # JWT ID for revocation
        assert "permissions" in claims
        assert "exp" in claims
        assert "iat" in claims
        assert "device_hash" in claims
    
    @pytest.mark.asyncio
    async def test_refresh_token_creation(self, auth_service, sample_user):
        """Test refresh token creation"""
        token = await auth_service._create_refresh_token(sample_user)
        
        assert token is not None
        assert isinstance(token, str)
        
        # Decode and verify minimal claims
        import jwt
        claims = jwt.decode(token, options={"verify_signature": False})
        
        assert claims["sub"] == str(sample_user.id)
        assert claims["type"] == "refresh"
        assert "jti" in claims
        # Refresh tokens should have minimal claims for security
        assert "permissions" not in claims
        assert "email" not in claims
    
    @pytest.mark.asyncio
    async def test_token_expiry(self, auth_service, sample_user):
        """Test token expiry settings"""
        access_token = await auth_service._create_access_token(sample_user)
        refresh_token = await auth_service._create_refresh_token(sample_user)
        
        import jwt
        access_claims = jwt.decode(access_token, options={"verify_signature": False})
        refresh_claims = jwt.decode(refresh_token, options={"verify_signature": False})
        
        # Check expiry times
        access_exp = datetime.fromtimestamp(access_claims["exp"])
        refresh_exp = datetime.fromtimestamp(refresh_claims["exp"])
        now = datetime.utcnow()
        
        # Access token should expire in ~15 minutes
        assert (access_exp - now).total_seconds() < 1000  # Less than ~16 minutes
        assert (access_exp - now).total_seconds() > 800   # More than ~13 minutes
        
        # Refresh token should expire in ~30 days
        assert (refresh_exp - now).days >= 29
        assert (refresh_exp - now).days <= 30


class TestMultiFactorAuthentication:
    """Test MFA/TOTP implementation"""
    
    @pytest.mark.asyncio
    async def test_mfa_required_flow(self, auth_service, sample_user):
        """Test authentication flow when MFA is required"""
        sample_user.mfa_enabled = True
        
        # Mock database queries
        auth_service._get_user_by_email = AsyncMock(return_value=sample_user)
        auth_service._verify_password_secure = AsyncMock(return_value=True)
        
        result = await auth_service.authenticate_user(
            email="test@example.com",
            password="correct_password"
        )
        
        assert result["requires_mfa"] is True
        assert "mfa_session_token" in result
        assert "access_token" not in result
    
    @pytest.mark.asyncio
    async def test_mfa_verification(self, auth_service):
        """Test TOTP verification"""
        import pyotp
        
        # Create a test TOTP secret
        secret = pyotp.random_base32()
        totp = pyotp.TOTP(secret)
        
        # Mock MFA secret retrieval
        mfa_secret = Mock(spec=MFASecret)
        mfa_secret.secret = secret
        mfa_secret.use_count = 0
        
        auth_service.db.execute = AsyncMock()
        auth_service.db.execute.return_value.scalar_one_or_none = Mock(return_value=mfa_secret)
        auth_service.db.commit = AsyncMock()
        
        # Test with valid code
        valid_code = totp.now()
        result = await auth_service._verify_mfa("user_id", valid_code)
        assert result is True
        
        # Test with invalid code
        result = await auth_service._verify_mfa("user_id", "000000")
        assert result is False
    
    @pytest.mark.asyncio
    async def test_mfa_session_token(self, auth_service):
        """Test MFA session token creation"""
        user_id = str(uuid.uuid4())
        token = auth_service._create_mfa_session(user_id)
        
        assert token is not None
        
        import jwt
        claims = jwt.decode(token, options={"verify_signature": False})
        
        assert claims["sub"] == user_id
        assert claims["type"] == "mfa_session"
        
        # Should have short expiry (5 minutes)
        exp = datetime.fromtimestamp(claims["exp"])
        now = datetime.utcnow()
        assert (exp - now).total_seconds() < 310  # Less than ~5 minutes


class TestDeviceFingerprinting:
    """Test device fingerprinting and anomaly detection"""
    
    @pytest.mark.asyncio
    async def test_device_feature_extraction(self, auth_service, device_fingerprint):
        """Test extraction of device features for ML model"""
        features = auth_service._extract_device_features(device_fingerprint)
        
        assert features is not None
        assert len(features) == 10  # Should extract 10 features
        assert features.dtype == 'float32'
        
        # Features should be normalized
        if features.std() > 0:
            assert abs(features.mean()) < 1  # Mean should be close to 0
    
    @pytest.mark.asyncio
    async def test_trusted_device_check(self, auth_service, device_fingerprint):
        """Test trusted device verification"""
        user_id = str(uuid.uuid4())
        
        # Mock trusted device in database
        trusted_device = Mock(spec=TrustedDevice)
        trusted_device.fingerprint = device_fingerprint
        trusted_device.last_seen = datetime.utcnow()
        
        auth_service.db.execute = AsyncMock()
        auth_service.db.execute.return_value.scalar_one_or_none = Mock(return_value=trusted_device)
        auth_service.db.commit = AsyncMock()
        
        result = await auth_service._verify_device(user_id, device_fingerprint, "192.168.1.1")
        assert result is True
    
    @pytest.mark.asyncio
    async def test_anomaly_detection(self, auth_service, device_fingerprint):
        """Test ML-based anomaly detection"""
        if auth_service.device_anomaly_model is None:
            pytest.skip("Anomaly model not available")
        
        user_id = str(uuid.uuid4())
        
        # Mock no trusted device found
        auth_service.db.execute = AsyncMock()
        auth_service.db.execute.return_value.scalar_one_or_none = Mock(return_value=None)
        
        # Test anomaly detection
        result = await auth_service._verify_device(user_id, device_fingerprint)
        
        # Result depends on model prediction
        assert isinstance(result, bool)
    
    @pytest.mark.asyncio
    async def test_new_device_alert(self, auth_service, sample_user, device_fingerprint):
        """Test alert sending for new device"""
        auth_service._log_security_event = AsyncMock()
        
        await auth_service._send_new_device_alert(sample_user, device_fingerprint, "192.168.1.1")
        
        # Verify security event was logged
        auth_service._log_security_event.assert_called_once()
        call_args = auth_service._log_security_event.call_args
        assert call_args[1]["event_type"] == "new_device_alert"
        assert call_args[1]["severity"] == "medium"


class TestRateLimiting:
    """Test rate limiting implementation"""
    
    @pytest.mark.asyncio
    async def test_rate_limit_with_redis(self, auth_service):
        """Test rate limiting using Redis"""
        email = "test@example.com"
        ip = "192.168.1.1"
        
        # Mock Redis responses
        auth_service.redis.incr = AsyncMock(side_effect=[1, 2, 3, 4, 5, 6])
        auth_service.redis.expire = AsyncMock()
        
        # First 5 attempts should pass
        for i in range(5):
            result = await auth_service._check_rate_limit(email, ip)
            assert result is False
        
        # 6th attempt should be blocked
        result = await auth_service._check_rate_limit(email, ip)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_rate_limit_fallback(self, auth_service):
        """Test in-memory rate limiting fallback"""
        auth_service.redis = None  # No Redis available
        email = "test@example.com"
        ip = "192.168.1.1"
        
        # First 5 attempts should pass
        for i in range(5):
            result = await auth_service._check_rate_limit(email, ip)
            assert result is False
        
        # 6th attempt should be blocked
        result = await auth_service._check_rate_limit(email, ip)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_rate_limit_window_expiry(self, auth_service):
        """Test rate limit window expiration"""
        auth_service.redis = None
        email = "test@example.com"
        
        # Add attempts to storage with old timestamps
        old_time = datetime.utcnow() - timedelta(minutes=20)
        auth_service.rate_limit_storage[f"{email}:unknown"] = [old_time] * 10
        
        # Should not be rate limited (old attempts expired)
        result = await auth_service._check_rate_limit(email)
        assert result is False


class TestTokenRevocation:
    """Test JWT token revocation"""
    
    @pytest.mark.asyncio
    async def test_token_revocation(self, auth_service):
        """Test revoking a token by JTI"""
        jti = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        
        auth_service.db.add = Mock()
        auth_service.db.commit = AsyncMock()
        auth_service.redis.delete = AsyncMock()
        auth_service._log_security_event = AsyncMock()
        
        await auth_service.revoke_token(jti, user_id, "user_logout")
        
        # Verify token was added to blacklist
        auth_service.db.add.assert_called_once()
        auth_service.db.commit.assert_called_once()
        
        # Verify Redis key was deleted
        auth_service.redis.delete.assert_called_with(f"jwt:active:{jti}")
    
    @pytest.mark.asyncio
    async def test_verify_revoked_token(self, auth_service):
        """Test verification of revoked token"""
        # Create a mock token
        import jwt
        jti = str(uuid.uuid4())
        token = jwt.encode(
            {"sub": "user_id", "jti": jti, "exp": datetime.utcnow() + timedelta(minutes=5)},
            "secret",
            algorithm="HS256"
        )
        
        # Mock token as revoked in Redis
        auth_service.redis.get = AsyncMock(return_value=None)  # Not in active list
        auth_service.jwt_public_key = "secret"  # Use simple secret for test
        auth_service.jwt_algorithm = "HS256"
        
        with pytest.raises(HTTPException) as exc:
            await auth_service.verify_token(token)
        
        assert exc.value.status_code == 401
        assert "revoked" in str(exc.value.detail).lower()


class TestCompleteAuthenticationFlow:
    """Test complete authentication flow"""
    
    @pytest.mark.asyncio
    async def test_successful_authentication(self, auth_service, sample_user, device_fingerprint):
        """Test successful authentication flow"""
        # Setup mocks
        auth_service._get_user_by_email = AsyncMock(return_value=sample_user)
        auth_service._verify_password_secure = AsyncMock(return_value=True)
        auth_service._verify_device = AsyncMock(return_value=True)
        auth_service._create_access_token = AsyncMock(return_value="access_token_123")
        auth_service._create_refresh_token = AsyncMock(return_value="refresh_token_456")
        auth_service._create_user_session = AsyncMock(return_value={"session_id": "sess_789"})
        auth_service._log_authentication = AsyncMock()
        auth_service._update_last_login = AsyncMock()
        auth_service._get_user_permissions = AsyncMock(return_value=["read:own_profile"])
        
        result = await auth_service.authenticate_user(
            email="test@example.com",
            password="correct_password",
            device_fingerprint=device_fingerprint,
            ip_address="192.168.1.1"
        )
        
        assert result["access_token"] == "access_token_123"
        assert result["refresh_token"] == "refresh_token_456"
        assert result["token_type"] == "bearer"
        assert result["session_id"] == "sess_789"
        assert result["user"]["email"] == "test@example.com"
        assert "permissions" in result["user"]
    
    @pytest.mark.asyncio
    async def test_failed_authentication_invalid_password(self, auth_service, sample_user):
        """Test authentication failure with invalid password"""
        auth_service._get_user_by_email = AsyncMock(return_value=sample_user)
        auth_service._verify_password_secure = AsyncMock(return_value=False)
        auth_service._record_failed_attempt = AsyncMock()
        
        with pytest.raises(HTTPException) as exc:
            await auth_service.authenticate_user(
                email="test@example.com",
                password="wrong_password"
            )
        
        assert exc.value.status_code == 401
        assert "Invalid credentials" in str(exc.value.detail)
        auth_service._record_failed_attempt.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_authentication_with_untrusted_device(self, auth_service, sample_user, device_fingerprint):
        """Test authentication with untrusted device enforcement"""
        sample_user.enforce_device_trust = True
        
        auth_service._get_user_by_email = AsyncMock(return_value=sample_user)
        auth_service._verify_password_secure = AsyncMock(return_value=True)
        auth_service._verify_device = AsyncMock(return_value=False)  # Untrusted device
        auth_service._send_new_device_alert = AsyncMock()
        auth_service._log_security_event = AsyncMock()
        
        with pytest.raises(HTTPException) as exc:
            await auth_service.authenticate_user(
                email="test@example.com",
                password="correct_password",
                device_fingerprint=device_fingerprint
            )
        
        assert exc.value.status_code == 403
        assert "unrecognized device" in str(exc.value.detail).lower()
        auth_service._send_new_device_alert.assert_called_once()


class TestSecurityEventLogging:
    """Test security event logging"""
    
    @pytest.mark.asyncio
    async def test_security_event_logging(self, auth_service):
        """Test logging of security events"""
        auth_service.db.add = Mock()
        auth_service.db.commit = AsyncMock()
        
        await auth_service._log_security_event(
            event_type="test_event",
            severity="high",
            user_id="user_123",
            ip_address="192.168.1.1",
            details={"action": "test"}
        )
        
        # Verify event was added to database
        auth_service.db.add.assert_called_once()
        
        # Verify event was added to in-memory storage
        assert len(auth_service.security_events) > 0
        last_event = auth_service.security_events[-1]
        assert last_event["event_type"] == "test_event"
        assert last_event["severity"] == "high"
    
    @pytest.mark.asyncio
    async def test_security_event_memory_limit(self, auth_service):
        """Test that security events in memory are limited"""
        # Add more than 1000 events
        for i in range(1100):
            auth_service.security_events.append({
                "event_type": f"event_{i}",
                "timestamp": datetime.utcnow().isoformat()
            })
        
        auth_service.db = None  # No database for this test
        
        await auth_service._log_security_event(
            event_type="final_event",
            severity="low"
        )
        
        # Should keep only last 1000 events
        assert len(auth_service.security_events) == 1000
        assert auth_service.security_events[-1]["event_type"] == "final_event"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])