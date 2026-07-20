"""
Comprehensive security tests for authentication and encryption.

This test suite covers:
- Password security and hashing
- JWT token security
- Session management
- Rate limiting
- Brute force protection
- Encryption/decryption
- API key security
- OAuth security
- Two-factor authentication
- Account lockout mechanisms
"""
import pytest
import jwt
import hashlib
import time
from datetime import datetime, timedelta
from unittest.mock import patch, Mock, AsyncMock
from httpx import AsyncClient
from fastapi import status
import bcrypt
from cryptography.fernet import Fernet
import secrets
import string

from app.core.security import (
    create_access_token, 
    create_refresh_token,
    verify_password,
    get_password_hash,
    encrypt_sensitive_data,
    decrypt_sensitive_data
)
from app.core.config import get_settings
from app.models.user import User
from app.services.auth_service import AuthService
from app.core.exceptions import SecurityException


class TestPasswordSecurity:
    """Test password security mechanisms."""
    
    def test_password_hashing_strength(self):
        """Test that passwords are hashed with sufficient strength."""
        
        password = "TestPassword123!"
        hashed = get_password_hash(password)
        
        # Should not be the same as original password
        assert hashed != password
        
        # Should be bcrypt hash (starts with $2b$)
        assert hashed.startswith("$2b$")
        
        # Should have sufficient rounds (at least 12)
        rounds = int(hashed.split("$")[2])
        assert rounds >= 12, f"Hash rounds too low: {rounds}"
        
        # Should verify correctly
        assert verify_password(password, hashed)
        
        # Should not verify with wrong password
        assert not verify_password("WrongPassword", hashed)
    
    def test_password_complexity_requirements(self):
        """Test password complexity validation."""
        
        auth_service = AuthService()
        
        # Test weak passwords
        weak_passwords = [
            "password",          # Too simple
            "12345678",          # Only numbers
            "abcdefgh",          # Only lowercase
            "ABCDEFGH",          # Only uppercase
            "Pass1",             # Too short
            "password123",       # No uppercase or special chars
            "PASSWORD123",       # No lowercase or special chars
            "Password",          # No numbers or special chars
        ]
        
        for weak_password in weak_passwords:
            with pytest.raises((SecurityException, ValueError)):
                auth_service.validate_password_strength(weak_password)
        
        # Test strong passwords
        strong_passwords = [
            "MyStr0ng!Password",
            "C0mpl3x$Passw0rd",
            "Secure#Pass123",
            "MyP@ssw0rd!2024"
        ]
        
        for strong_password in strong_passwords:
            # Should not raise exception
            auth_service.validate_password_strength(strong_password)
    
    def test_password_hashing_consistency(self):
        """Test that password hashing is consistent but salted."""
        
        password = "TestPassword123!"
        
        # Hash the same password multiple times
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        hash3 = get_password_hash(password)
        
        # Hashes should be different due to salting
        assert hash1 != hash2
        assert hash2 != hash3
        assert hash1 != hash3
        
        # All should verify correctly
        assert verify_password(password, hash1)
        assert verify_password(password, hash2)
        assert verify_password(password, hash3)
    
    def test_password_timing_attack_resistance(self):
        """Test resistance to timing attacks on password verification."""
        
        password = "TestPassword123!"
        hashed = get_password_hash(password)
        
        # Measure time for correct password
        start_time = time.time()
        verify_password(password, hashed)
        correct_time = time.time() - start_time
        
        # Measure time for incorrect password
        start_time = time.time()
        verify_password("WrongPassword", hashed)
        incorrect_time = time.time() - start_time
        
        # Times should be similar (within 10ms difference)
        # This is a basic test - real timing attacks are more sophisticated
        time_difference = abs(correct_time - incorrect_time)
        assert time_difference < 0.01, f"Timing difference too large: {time_difference}"
    
    def test_password_rehashing_on_upgrade(self):
        """Test password rehashing when algorithm is upgraded."""
        
        password = "TestPassword123!"
        
        # Simulate old hash with lower rounds
        old_rounds = 10
        old_salt = bcrypt.gensalt(rounds=old_rounds)
        old_hash = bcrypt.hashpw(password.encode('utf-8'), old_salt).decode('utf-8')
        
        auth_service = AuthService()
        
        # Should detect that rehashing is needed
        needs_rehash = auth_service.needs_password_rehash(old_hash)
        assert needs_rehash
        
        # Should rehash with stronger algorithm
        new_hash = auth_service.rehash_password(password)
        new_rounds = int(new_hash.split("$")[2])
        assert new_rounds > old_rounds
        
        # Both old and new hashes should verify
        assert verify_password(password, old_hash)
        assert verify_password(password, new_hash)


class TestJWTSecurity:
    """Test JWT token security."""
    
    def test_jwt_token_structure(self):
        """Test JWT token structure and claims."""
        
        user_data = {"user_id": "123", "email": "test@example.com"}
        token = create_access_token(data=user_data)
        
        # Should have three parts (header.payload.signature)
        parts = token.split(".")
        assert len(parts) == 3
        
        # Decode without verification to check structure
        settings = get_settings()
        decoded = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        
        # Should have required claims
        assert "user_id" in decoded
        assert "email" in decoded
        assert "exp" in decoded  # Expiration
        assert "iat" in decoded  # Issued at
        assert "type" in decoded  # Token type
        
        assert decoded["user_id"] == "123"
        assert decoded["email"] == "test@example.com"
        assert decoded["type"] == "access"
    
    def test_jwt_token_expiration(self):
        """Test JWT token expiration."""
        
        user_data = {"user_id": "123"}
        
        # Create token with short expiration
        short_expiry = timedelta(seconds=1)
        token = create_access_token(data=user_data, expires_delta=short_expiry)
        
        settings = get_settings()
        
        # Should be valid immediately
        decoded = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        assert decoded["user_id"] == "123"
        
        # Wait for token to expire
        time.sleep(2)
        
        # Should raise ExpiredSignatureError
        with pytest.raises(jwt.ExpiredSignatureError):
            jwt.decode(token, settings.secret_key, algorithms=["HS256"])
    
    def test_jwt_token_signature_validation(self):
        """Test JWT signature validation."""
        
        user_data = {"user_id": "123"}
        token = create_access_token(data=user_data)
        
        settings = get_settings()
        
        # Should validate with correct secret
        decoded = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        assert decoded["user_id"] == "123"
        
        # Should fail with wrong secret
        with pytest.raises(jwt.InvalidSignatureError):
            jwt.decode(token, "wrong_secret", algorithms=["HS256"])
        
        # Should fail with modified token
        parts = token.split(".")
        modified_token = parts[0] + ".modified_payload." + parts[2]
        
        with pytest.raises(jwt.InvalidSignatureError):
            jwt.decode(modified_token, settings.secret_key, algorithms=["HS256"])
    
    def test_jwt_algorithm_security(self):
        """Test JWT algorithm security (prevent algorithm confusion)."""
        
        user_data = {"user_id": "123"}
        token = create_access_token(data=user_data)
        
        settings = get_settings()
        
        # Should fail if algorithm is not specified
        with pytest.raises(jwt.InvalidTokenError):
            jwt.decode(token, settings.secret_key)  # No algorithms specified
        
        # Should fail with different algorithm
        with pytest.raises(jwt.InvalidSignatureError):
            jwt.decode(token, settings.secret_key, algorithms=["HS512"])
        
        # Should succeed only with correct algorithm
        decoded = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        assert decoded["user_id"] == "123"
    
    def test_refresh_token_security(self):
        """Test refresh token security."""
        
        user_data = {"user_id": "123"}
        refresh_token = create_refresh_token(data=user_data)
        
        settings = get_settings()
        decoded = jwt.decode(refresh_token, settings.secret_key, algorithms=["HS256"])
        
        # Should have longer expiration than access token
        assert decoded["type"] == "refresh"
        
        # Should have different expiration time
        access_token = create_access_token(data=user_data)
        access_decoded = jwt.decode(access_token, settings.secret_key, algorithms=["HS256"])
        
        assert decoded["exp"] > access_decoded["exp"]
    
    def test_jwt_claim_validation(self):
        """Test JWT claim validation."""
        
        # Test with missing required claims
        incomplete_payload = {"user_id": "123"}  # Missing email
        
        # When creating tokens, all required claims should be included
        token = create_access_token(data=incomplete_payload)
        settings = get_settings()
        decoded = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        
        # Should have all required claims
        assert "user_id" in decoded
        assert "exp" in decoded
        assert "iat" in decoded
        assert "type" in decoded


class TestRateLimiting:
    """Test rate limiting mechanisms."""
    
    @pytest.mark.asyncio
    async def test_login_rate_limiting(self, test_client: AsyncClient):
        """Test rate limiting on login attempts."""
        
        login_data = {
            "email": "test@example.com",
            "password": "wrongpassword"
        }
        
        # Make multiple failed login attempts
        attempts = 0
        rate_limited = False
        
        for i in range(20):  # Try many times to trigger rate limit
            response = await test_client.post("/api/v1/auth/login", json=login_data)
            attempts += 1
            
            if response.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
                rate_limited = True
                break
            
            # Small delay between attempts
            await asyncio.sleep(0.1)
        
        assert rate_limited, f"Rate limiting not triggered after {attempts} attempts"
        assert attempts <= 10, "Rate limiting threshold too high"
    
    @pytest.mark.asyncio
    async def test_api_endpoint_rate_limiting(self, authenticated_client: AsyncClient):
        """Test general API rate limiting."""
        
        # Make many requests to a protected endpoint
        responses = []
        for i in range(100):
            response = await authenticated_client.get("/api/v1/users/me")
            responses.append(response)
            
            if response.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
                break
        
        # Should eventually hit rate limit
        rate_limited_responses = [r for r in responses 
                                if r.status_code == status.HTTP_429_TOO_MANY_REQUESTS]
        assert len(rate_limited_responses) > 0, "API rate limiting not working"
    
    @pytest.mark.asyncio
    async def test_rate_limit_reset(self, test_client: AsyncClient):
        """Test that rate limits reset after time period."""
        
        login_data = {
            "email": "test@example.com",
            "password": "wrongpassword"
        }
        
        # Trigger rate limit
        for i in range(15):
            response = await test_client.post("/api/v1/auth/login", json=login_data)
            if response.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
                break
        
        # Should be rate limited
        response = await test_client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        
        # Wait for rate limit to reset (simulate - in reality would be longer)
        with patch('app.core.rate_limiting.get_current_time') as mock_time:
            # Simulate time passing
            mock_time.return_value = time.time() + 3600  # 1 hour later
            
            # Should be able to try again
            response = await test_client.post("/api/v1/auth/login", json=login_data)
            assert response.status_code != status.HTTP_429_TOO_MANY_REQUESTS
    
    def test_rate_limiting_by_ip(self):
        """Test rate limiting by IP address."""
        
        from app.core.rate_limiting import RateLimiter
        
        rate_limiter = RateLimiter()
        
        ip1 = "192.168.1.1"
        ip2 = "192.168.1.2"
        
        # Each IP should have separate rate limits
        for i in range(10):
            assert rate_limiter.is_allowed(ip1, "login")
            assert rate_limiter.is_allowed(ip2, "login")
        
        # Exceed limit for IP1
        for i in range(20):
            rate_limiter.is_allowed(ip1, "login")
        
        # IP1 should be limited, IP2 should still work
        assert not rate_limiter.is_allowed(ip1, "login")
        assert rate_limiter.is_allowed(ip2, "login")
    
    def test_different_rate_limits_for_endpoints(self):
        """Test different rate limits for different endpoints."""
        
        from app.core.rate_limiting import RateLimiter
        
        rate_limiter = RateLimiter()
        ip = "192.168.1.1"
        
        # Login should have stricter limits than general API
        login_attempts = 0
        while rate_limiter.is_allowed(ip, "login"):
            login_attempts += 1
            if login_attempts > 20:  # Safety break
                break
        
        api_attempts = 0
        while rate_limiter.is_allowed(ip, "api"):
            api_attempts += 1
            if api_attempts > 100:  # Safety break
                break
        
        # API should allow more attempts than login
        assert api_attempts > login_attempts


class TestBruteForceProtection:
    """Test brute force attack protection."""
    
    @pytest.mark.asyncio
    async def test_account_lockout_after_failed_attempts(self, test_client: AsyncClient, test_user: User):
        """Test account lockout after multiple failed login attempts."""
        
        failed_login_data = {
            "email": test_user.email,
            "password": "wrongpassword"
        }
        
        # Make multiple failed attempts
        failed_attempts = 0
        for i in range(10):
            response = await test_client.post("/api/v1/auth/login", json=failed_login_data)
            if response.status_code == status.HTTP_401_UNAUTHORIZED:
                failed_attempts += 1
            elif response.status_code == status.HTTP_423_LOCKED:
                # Account locked
                break
        
        # Try with correct password - should still be locked
        correct_login_data = {
            "email": test_user.email,
            "password": "testpassword123"  # Assuming this is the correct password
        }
        
        response = await test_client.post("/api/v1/auth/login", json=correct_login_data)
        assert response.status_code == status.HTTP_423_LOCKED
        
        data = response.json()
        assert "locked" in data["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_progressive_delay_on_failed_attempts(self, test_client: AsyncClient):
        """Test progressive delays on failed login attempts."""
        
        login_data = {
            "email": "nonexistent@example.com",
            "password": "wrongpassword"
        }
        
        response_times = []
        
        for i in range(5):
            start_time = time.time()
            response = await test_client.post("/api/v1/auth/login", json=login_data)
            end_time = time.time()
            
            response_times.append(end_time - start_time)
        
        # Response times should generally increase (progressive delay)
        # Allow some variance for network/processing time
        for i in range(1, len(response_times)):
            # Each attempt should take at least as long as the previous (with tolerance)
            assert response_times[i] >= response_times[i-1] - 0.1
    
    def test_failed_attempt_tracking(self):
        """Test tracking of failed login attempts."""
        
        from app.services.security_service import SecurityService
        
        security_service = SecurityService()
        
        email = "test@example.com"
        ip = "192.168.1.1"
        
        # Record failed attempts
        for i in range(3):
            security_service.record_failed_login(email, ip)
        
        # Should track attempts
        failed_count = security_service.get_failed_login_count(email)
        assert failed_count == 3
        
        # Should reset on successful login
        security_service.record_successful_login(email, ip)
        failed_count = security_service.get_failed_login_count(email)
        assert failed_count == 0
    
    def test_suspicious_activity_detection(self):
        """Test detection of suspicious login activity."""
        
        from app.services.security_service import SecurityService
        
        security_service = SecurityService()
        
        email = "test@example.com"
        
        # Multiple IPs trying same account
        suspicious_ips = ["192.168.1.1", "10.0.0.1", "172.16.0.1", "203.0.113.1"]
        
        for ip in suspicious_ips:
            security_service.record_failed_login(email, ip)
        
        is_suspicious = security_service.is_suspicious_activity(email)
        assert is_suspicious, "Should detect suspicious activity from multiple IPs"
    
    def test_captcha_requirement_after_failures(self):
        """Test CAPTCHA requirement after failed attempts."""
        
        from app.services.security_service import SecurityService
        
        security_service = SecurityService()
        
        email = "test@example.com"
        ip = "192.168.1.1"
        
        # Initial attempts shouldn't require CAPTCHA
        assert not security_service.requires_captcha(email, ip)
        
        # After multiple failures, should require CAPTCHA
        for i in range(3):
            security_service.record_failed_login(email, ip)
        
        assert security_service.requires_captcha(email, ip)


class TestEncryptionSecurity:
    """Test data encryption and decryption security."""
    
    def test_sensitive_data_encryption(self):
        """Test encryption of sensitive data."""
        
        sensitive_data = "123-45-6789"  # SSN
        
        encrypted = encrypt_sensitive_data(sensitive_data)
        
        # Should not be same as original
        assert encrypted != sensitive_data
        
        # Should be base64 encoded
        import base64
        try:
            base64.b64decode(encrypted)
        except Exception:
            pytest.fail("Encrypted data is not valid base64")
        
        # Should decrypt correctly
        decrypted = decrypt_sensitive_data(encrypted)
        assert decrypted == sensitive_data
    
    def test_encryption_key_rotation(self):
        """Test encryption with key rotation."""
        
        data = "sensitive information"
        
        # Encrypt with current key
        encrypted1 = encrypt_sensitive_data(data)
        
        # Simulate key rotation
        with patch('app.core.security.get_encryption_key') as mock_get_key:
            new_key = Fernet.generate_key()
            mock_get_key.return_value = new_key
            
            # Encrypt with new key
            encrypted2 = encrypt_sensitive_data(data)
            
            # Should be different
            assert encrypted1 != encrypted2
            
            # Should decrypt with new key
            decrypted2 = decrypt_sensitive_data(encrypted2)
            assert decrypted2 == data
    
    def test_encryption_with_different_data_types(self):
        """Test encryption with different data types."""
        
        test_data = [
            "simple string",
            "complex string with special chars: !@#$%^&*()",
            json.dumps({"key": "value", "number": 123}),
            "unicode string with émojis: 🔒🔑",
            "very long string " * 100
        ]
        
        for data in test_data:
            encrypted = encrypt_sensitive_data(data)
            decrypted = decrypt_sensitive_data(encrypted)
            
            assert decrypted == data, f"Encryption/decryption failed for: {data[:50]}..."
    
    def test_encryption_failure_handling(self):
        """Test handling of encryption failures."""
        
        # Test decryption with invalid data
        with pytest.raises(Exception):
            decrypt_sensitive_data("invalid_encrypted_data")
        
        # Test decryption with corrupted data
        valid_encrypted = encrypt_sensitive_data("test data")
        corrupted = valid_encrypted[:-5] + "XXXXX"  # Corrupt the end
        
        with pytest.raises(Exception):
            decrypt_sensitive_data(corrupted)
    
    def test_field_level_encryption(self):
        """Test field-level encryption for database fields."""
        
        from app.models.user import User
        
        # Test that sensitive fields are encrypted before storage
        sensitive_data = {
            "ssn": "123-45-6789",
            "account_number": "1234567890",
            "routing_number": "987654321"
        }
        
        user = User(email="test@example.com")
        
        # Set sensitive fields
        for field, value in sensitive_data.items():
            if hasattr(user, f"encrypted_{field}"):
                setattr(user, field, value)
        
        # Check that encrypted versions are different
        for field, original_value in sensitive_data.items():
            if hasattr(user, f"encrypted_{field}"):
                encrypted_value = getattr(user, f"encrypted_{field}")
                if encrypted_value:
                    assert encrypted_value != original_value


class TestSessionSecurity:
    """Test session management security."""
    
    @pytest.mark.asyncio
    async def test_session_creation_and_validation(self, test_client: AsyncClient, test_user: User):
        """Test secure session creation and validation."""
        
        # Login to create session
        login_response = await test_client.post("/api/v1/auth/login", json={
            "email": test_user.email,
            "password": "testpassword123"
        })
        
        assert login_response.status_code == status.HTTP_200_OK
        session_data = login_response.json()
        
        # Should have secure session token
        assert "access_token" in session_data
        assert len(session_data["access_token"]) > 50  # Should be long enough
        
        # Should have expiration
        assert "expires_in" in session_data or "expires_at" in session_data
    
    @pytest.mark.asyncio
    async def test_session_invalidation_on_logout(self, authenticated_client: AsyncClient):
        """Test session invalidation on logout."""
        
        # Should be able to access protected endpoint
        response = await authenticated_client.get("/api/v1/users/me")
        assert response.status_code == status.HTTP_200_OK
        
        # Logout
        logout_response = await authenticated_client.post("/api/v1/auth/logout")
        assert logout_response.status_code == status.HTTP_200_OK
        
        # Should no longer be able to access protected endpoint
        response = await authenticated_client.get("/api/v1/users/me")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_session_timeout(self):
        """Test session timeout mechanisms."""
        
        from app.services.session_service import SessionService
        
        session_service = SessionService()
        
        user_id = "123"
        
        # Create session
        session_id = session_service.create_session(user_id)
        
        # Should be valid initially
        assert session_service.is_session_valid(session_id)
        
        # Simulate session timeout
        with patch('time.time') as mock_time:
            # Simulate 2 hours passing
            mock_time.return_value = time.time() + 7200
            
            # Session should be expired
            assert not session_service.is_session_valid(session_id)
    
    def test_concurrent_session_limits(self):
        """Test limits on concurrent sessions."""
        
        from app.services.session_service import SessionService
        
        session_service = SessionService()
        
        user_id = "123"
        
        # Create multiple sessions
        sessions = []
        for i in range(10):
            session_id = session_service.create_session(user_id)
            sessions.append(session_id)
        
        # Should enforce concurrent session limits
        active_sessions = session_service.get_active_sessions(user_id)
        assert len(active_sessions) <= 5  # Assuming limit of 5 concurrent sessions
        
        # Oldest sessions should be invalidated
        for session_id in sessions[:5]:
            assert not session_service.is_session_valid(session_id)


class TestAPIKeySecurity:
    """Test API key security mechanisms."""
    
    def test_api_key_generation(self):
        """Test secure API key generation."""
        
        from app.services.api_key_service import APIKeyService
        
        api_key_service = APIKeyService()
        
        api_key = api_key_service.generate_api_key()
        
        # Should be long enough
        assert len(api_key) >= 32
        
        # Should be cryptographically random
        api_key2 = api_key_service.generate_api_key()
        assert api_key != api_key2
        
        # Should only contain safe characters
        safe_chars = set(string.ascii_letters + string.digits + "-_")
        assert all(c in safe_chars for c in api_key)
    
    def test_api_key_hashing_and_verification(self):
        """Test API key hashing and verification."""
        
        from app.services.api_key_service import APIKeyService
        
        api_key_service = APIKeyService()
        
        api_key = "test_api_key_123456789"
        hashed_key = api_key_service.hash_api_key(api_key)
        
        # Should not be same as original
        assert hashed_key != api_key
        
        # Should verify correctly
        assert api_key_service.verify_api_key(api_key, hashed_key)
        
        # Should not verify wrong key
        assert not api_key_service.verify_api_key("wrong_key", hashed_key)
    
    @pytest.mark.asyncio
    async def test_api_key_authentication(self, test_client: AsyncClient, test_user: User):
        """Test API key authentication."""
        
        # Create API key for user
        from app.services.api_key_service import APIKeyService
        
        api_key_service = APIKeyService()
        api_key = await api_key_service.create_user_api_key(test_user.id, "test_key")
        
        # Should be able to authenticate with API key
        headers = {"X-API-Key": api_key}
        response = await test_client.get("/api/v1/users/me", headers=headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == str(test_user.id)
    
    def test_api_key_permissions_and_scopes(self):
        """Test API key permissions and scopes."""
        
        from app.services.api_key_service import APIKeyService
        
        api_key_service = APIKeyService()
        
        # Create API key with limited scope
        scopes = ["read:profile", "read:goals"]
        api_key_data = api_key_service.create_api_key_with_scopes("user_123", scopes)
        
        # Should have specified scopes
        assert set(api_key_data["scopes"]) == set(scopes)
        
        # Should validate scope requirements
        assert api_key_service.has_scope(api_key_data, "read:profile")
        assert not api_key_service.has_scope(api_key_data, "write:profile")
    
    def test_api_key_rate_limiting(self):
        """Test rate limiting for API keys."""
        
        from app.services.api_key_service import APIKeyService
        from app.core.rate_limiting import RateLimiter
        
        api_key_service = APIKeyService()
        rate_limiter = RateLimiter()
        
        api_key = "test_api_key_123"
        
        # Should have different rate limits for API keys
        for i in range(1000):  # Try many requests
            if not rate_limiter.is_allowed(api_key, "api_key"):
                break
        else:
            pytest.fail("API key rate limiting not enforced")
        
        # Should be able to make some requests
        assert i > 100, f"API key rate limit too restrictive: {i} requests allowed"


class TestTwoFactorAuthentication:
    """Test two-factor authentication security."""
    
    def test_totp_secret_generation(self):
        """Test TOTP secret generation."""
        
        from app.services.two_factor_service import TwoFactorService
        
        two_factor_service = TwoFactorService()
        
        secret = two_factor_service.generate_totp_secret()
        
        # Should be base32 encoded
        import base64
        try:
            base64.b32decode(secret)
        except Exception:
            pytest.fail("TOTP secret is not valid base32")
        
        # Should be long enough for security
        assert len(secret) >= 16
    
    def test_totp_code_generation_and_verification(self):
        """Test TOTP code generation and verification."""
        
        from app.services.two_factor_service import TwoFactorService
        
        two_factor_service = TwoFactorService()
        
        secret = "JBSWY3DPEHPK3PXP"  # Test secret
        
        # Generate current TOTP code
        current_code = two_factor_service.generate_totp_code(secret)
        
        # Should be 6 digits
        assert len(current_code) == 6
        assert current_code.isdigit()
        
        # Should verify correctly
        assert two_factor_service.verify_totp_code(secret, current_code)
        
        # Should not verify wrong code
        wrong_code = "000000"
        assert not two_factor_service.verify_totp_code(secret, wrong_code)
    
    def test_totp_time_window_tolerance(self):
        """Test TOTP time window tolerance."""
        
        from app.services.two_factor_service import TwoFactorService
        
        two_factor_service = TwoFactorService()
        
        secret = "JBSWY3DPEHPK3PXP"
        
        # Generate code for previous time window
        with patch('time.time') as mock_time:
            mock_time.return_value = time.time() - 30  # 30 seconds ago
            previous_code = two_factor_service.generate_totp_code(secret)
        
        # Should still be valid (allowing for clock skew)
        assert two_factor_service.verify_totp_code(secret, previous_code, window=1)
        
        # Should not be valid with zero window
        assert not two_factor_service.verify_totp_code(secret, previous_code, window=0)
    
    @pytest.mark.asyncio
    async def test_2fa_enforcement(self, test_client: AsyncClient, test_user: User):
        """Test 2FA enforcement for sensitive operations."""
        
        # Enable 2FA for user
        from app.services.two_factor_service import TwoFactorService
        
        two_factor_service = TwoFactorService()
        await two_factor_service.enable_2fa_for_user(test_user.id)
        
        # Login should require 2FA
        login_response = await test_client.post("/api/v1/auth/login", json={
            "email": test_user.email,
            "password": "testpassword123"
        })
        
        assert login_response.status_code == status.HTTP_200_OK
        data = login_response.json()
        
        # Should indicate 2FA is required
        assert "requires_2fa" in data
        assert data["requires_2fa"] is True
        assert "temp_token" in data  # Temporary token for 2FA completion
    
    def test_backup_codes_generation(self):
        """Test backup codes generation for 2FA."""
        
        from app.services.two_factor_service import TwoFactorService
        
        two_factor_service = TwoFactorService()
        
        backup_codes = two_factor_service.generate_backup_codes()
        
        # Should generate multiple codes
        assert len(backup_codes) >= 8
        
        # Each code should be unique
        assert len(set(backup_codes)) == len(backup_codes)
        
        # Codes should be reasonable length
        for code in backup_codes:
            assert len(code) >= 8
            assert code.replace("-", "").isalnum()  # Allow hyphens for readability


class TestOAuthSecurity:
    """Test OAuth security mechanisms."""
    
    def test_oauth_state_parameter_generation(self):
        """Test OAuth state parameter generation."""
        
        from app.services.oauth_service import OAuthService
        
        oauth_service = OAuthService()
        
        state1 = oauth_service.generate_state()
        state2 = oauth_service.generate_state()
        
        # Should be unique
        assert state1 != state2
        
        # Should be long enough
        assert len(state1) >= 32
        
        # Should be URL-safe
        import urllib.parse
        assert urllib.parse.quote(state1, safe='') == state1 or len(urllib.parse.quote(state1, safe='')) == len(state1)
    
    def test_oauth_state_validation(self):
        """Test OAuth state parameter validation."""
        
        from app.services.oauth_service import OAuthService
        
        oauth_service = OAuthService()
        
        # Store state
        state = oauth_service.generate_state()
        oauth_service.store_oauth_state("session_123", state)
        
        # Should validate correct state
        assert oauth_service.validate_oauth_state("session_123", state)
        
        # Should not validate wrong state
        assert not oauth_service.validate_oauth_state("session_123", "wrong_state")
        
        # Should not validate after expiration
        with patch('time.time') as mock_time:
            mock_time.return_value = time.time() + 3600  # 1 hour later
            assert not oauth_service.validate_oauth_state("session_123", state)
    
    def test_oauth_pkce_challenge_generation(self):
        """Test OAuth PKCE challenge generation."""
        
        from app.services.oauth_service import OAuthService
        
        oauth_service = OAuthService()
        
        # Generate PKCE challenge
        verifier, challenge = oauth_service.generate_pkce_challenge()
        
        # Verifier should be long enough
        assert len(verifier) >= 43
        
        # Challenge should be base64url encoded SHA256 of verifier
        import hashlib
        import base64
        
        expected_challenge = base64.urlsafe_b64encode(
            hashlib.sha256(verifier.encode()).digest()
        ).decode().rstrip('=')
        
        assert challenge == expected_challenge
    
    @pytest.mark.asyncio
    async def test_oauth_token_exchange_security(self, test_client: AsyncClient):
        """Test OAuth token exchange security."""
        
        # Mock OAuth provider response
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_post.return_value = Mock(
                status_code=200,
                json=Mock(return_value={
                    "access_token": "oauth_access_token",
                    "token_type": "Bearer",
                    "expires_in": 3600,
                    "refresh_token": "oauth_refresh_token"
                })
            )
            
            # Test token exchange
            response = await test_client.post("/api/v1/auth/oauth/callback", json={
                "code": "auth_code_123",
                "state": "valid_state_123"
            })
            
            # Should validate all parameters
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            
            # Should include PKCE verifier if used
            assert "code_verifier" in call_args[1]["data"] or "client_secret" in call_args[1]["data"]


@pytest.mark.security
class TestSecurityHeaders:
    """Test security headers in responses."""
    
    @pytest.mark.asyncio
    async def test_security_headers_present(self, test_client: AsyncClient):
        """Test that security headers are present in responses."""
        
        response = await test_client.get("/api/v1/health")
        
        # Test HSTS header
        assert "Strict-Transport-Security" in response.headers
        hsts_value = response.headers["Strict-Transport-Security"]
        assert "max-age" in hsts_value
        assert int(hsts_value.split("max-age=")[1].split(";")[0]) >= 31536000  # At least 1 year
        
        # Test content security policy
        assert "Content-Security-Policy" in response.headers
        csp_value = response.headers["Content-Security-Policy"]
        assert "default-src" in csp_value
        
        # Test X-Frame-Options
        assert "X-Frame-Options" in response.headers
        assert response.headers["X-Frame-Options"] in ["DENY", "SAMEORIGIN"]
        
        # Test X-Content-Type-Options
        assert "X-Content-Type-Options" in response.headers
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        
        # Test X-XSS-Protection
        assert "X-XSS-Protection" in response.headers
        assert "1" in response.headers["X-XSS-Protection"]
    
    @pytest.mark.asyncio
    async def test_cors_headers_security(self, test_client: AsyncClient):
        """Test CORS headers security."""
        
        # Test preflight request
        response = await test_client.options(
            "/api/v1/users/me",
            headers={
                "Origin": "https://malicious.com",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "Authorization"
            }
        )
        
        # Should not allow arbitrary origins
        if "Access-Control-Allow-Origin" in response.headers:
            allowed_origin = response.headers["Access-Control-Allow-Origin"]
            assert allowed_origin != "https://malicious.com"
            assert allowed_origin == "*" or allowed_origin.startswith("https://trusted-domain.com")
    
    @pytest.mark.asyncio
    async def test_sensitive_data_headers(self, authenticated_client: AsyncClient):
        """Test headers for sensitive data responses."""
        
        response = await authenticated_client.get("/api/v1/users/me")
        
        # Should have cache control for sensitive data
        assert "Cache-Control" in response.headers
        cache_control = response.headers["Cache-Control"]
        assert "no-store" in cache_control or "private" in cache_control
        
        # Should not cache sensitive responses
        assert "no-cache" in cache_control or "max-age=0" in cache_control