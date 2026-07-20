"""
Integration tests for authentication endpoints.

Tests user registration, login, token management, and security features.
"""
import pytest
from httpx import AsyncClient
from unittest.mock import patch
import json
from datetime import datetime, timedelta

from app.core.security import create_access_token, verify_password
from tests.factories import UserFactory


class TestAuthenticationEndpoints:
    """Test cases for authentication API endpoints."""
    
    @pytest.mark.asyncio
    async def test_user_registration(self, test_client: AsyncClient, db_session):
        """Test user registration endpoint."""
        # Arrange
        registration_data = {
            "email": "newuser@example.com",
            "password": "StrongPassword123!",
            "first_name": "John",
            "last_name": "Doe",
            "phone_number": "+1-555-123-4567"
        }
        
        # Act
        response = await test_client.post("/api/v1/auth/register", json=registration_data)
        
        # Assert
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["email"] == registration_data["email"]
        assert data["first_name"] == registration_data["first_name"]
        assert "password" not in data  # Password should not be returned
        assert "access_token" in data
        assert "token_type" in data
    
    @pytest.mark.asyncio
    async def test_user_registration_duplicate_email(self, test_client: AsyncClient, test_user):
        """Test registration with duplicate email."""
        # Arrange
        registration_data = {
            "email": test_user.email,  # Use existing user's email
            "password": "StrongPassword123!",
            "first_name": "Jane",
            "last_name": "Doe",
            "phone_number": "+1-555-987-6543"
        }
        
        # Act
        response = await test_client.post("/api/v1/auth/register", json=registration_data)
        
        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "email already registered" in data["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_user_registration_invalid_data(self, test_client: AsyncClient):
        """Test registration with invalid data."""
        invalid_data_cases = [
            # Missing required fields
            {"email": "test@example.com"},
            # Invalid email format
            {"email": "invalid-email", "password": "Strong123!"},
            # Weak password
            {"email": "test@example.com", "password": "weak"},
            # Invalid phone number format
            {
                "email": "test@example.com",
                "password": "Strong123!",
                "phone_number": "invalid-phone"
            }
        ]
        
        for invalid_data in invalid_data_cases:
            # Act
            response = await test_client.post("/api/v1/auth/register", json=invalid_data)
            
            # Assert
            assert response.status_code == 422  # Validation error
            data = response.json()
            assert "detail" in data
    
    @pytest.mark.asyncio
    async def test_user_login(self, test_client: AsyncClient, test_user):
        """Test user login endpoint."""
        # Arrange
        login_data = {
            "username": test_user.email,
            "password": "secret"  # From factory password
        }
        
        # Act
        response = await test_client.post("/api/v1/auth/login", data=login_data)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data
    
    @pytest.mark.asyncio
    async def test_user_login_invalid_credentials(self, test_client: AsyncClient, test_user):
        """Test login with invalid credentials."""
        # Test wrong password
        login_data = {
            "username": test_user.email,
            "password": "wrongpassword"
        }
        
        response = await test_client.post("/api/v1/auth/login", data=login_data)
        assert response.status_code == 401
        
        # Test non-existent user
        login_data = {
            "username": "nonexistent@example.com",
            "password": "password"
        }
        
        response = await test_client.post("/api/v1/auth/login", data=login_data)
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_get_current_user(self, authenticated_client: AsyncClient, test_user):
        """Test getting current user information."""
        # Act
        response = await authenticated_client.get("/api/v1/auth/me")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_user.id
        assert data["email"] == test_user.email
        assert data["first_name"] == test_user.first_name
        assert "password" not in data
    
    @pytest.mark.asyncio
    async def test_get_current_user_unauthorized(self, test_client: AsyncClient):
        """Test getting current user without authentication."""
        # Act
        response = await test_client.get("/api/v1/auth/me")
        
        # Assert
        assert response.status_code == 401
        data = response.json()
        assert "not authenticated" in data["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_token_refresh(self, test_client: AsyncClient, test_user):
        """Test token refresh endpoint."""
        # First, get a token
        login_data = {
            "username": test_user.email,
            "password": "secret"
        }
        login_response = await test_client.post("/api/v1/auth/login", data=login_data)
        token = login_response.json()["access_token"]
        
        # Act - refresh token
        headers = {"Authorization": f"Bearer {token}"}
        response = await test_client.post("/api/v1/auth/refresh", headers=headers)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["access_token"] != token  # Should be a new token
    
    @pytest.mark.asyncio
    async def test_password_reset_request(self, test_client: AsyncClient, test_user):
        """Test password reset request endpoint."""
        # Arrange
        reset_data = {"email": test_user.email}
        
        with patch('app.services.email_service.send_password_reset_email') as mock_send:
            # Act
            response = await test_client.post("/api/v1/auth/password-reset", json=reset_data)
            
            # Assert
            assert response.status_code == 200
            data = response.json()
            assert "message" in data
            mock_send.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_password_reset_confirm(self, test_client: AsyncClient, test_user):
        """Test password reset confirmation endpoint."""
        # Arrange - create a reset token
        reset_token = create_access_token(
            data={"sub": test_user.email, "type": "password_reset"},
            expires_delta=timedelta(hours=1)
        )
        
        reset_data = {
            "token": reset_token,
            "new_password": "NewStrongPassword123!"
        }
        
        # Act
        response = await test_client.post("/api/v1/auth/password-reset/confirm", json=reset_data)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        
        # Verify new password works
        login_data = {
            "username": test_user.email,
            "password": "NewStrongPassword123!"
        }
        login_response = await test_client.post("/api/v1/auth/login", data=login_data)
        assert login_response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_update_profile(self, authenticated_client: AsyncClient, test_user):
        """Test updating user profile."""
        # Arrange
        update_data = {
            "first_name": "Updated First",
            "last_name": "Updated Last",
            "phone_number": "+1-555-999-8888"
        }
        
        # Act
        response = await authenticated_client.put("/api/v1/auth/profile", json=update_data)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["first_name"] == update_data["first_name"]
        assert data["last_name"] == update_data["last_name"]
        assert data["phone_number"] == update_data["phone_number"]
    
    @pytest.mark.asyncio
    async def test_change_password(self, authenticated_client: AsyncClient, test_user):
        """Test changing password."""
        # Arrange
        password_data = {
            "current_password": "secret",
            "new_password": "NewSecretPassword123!"
        }
        
        # Act
        response = await authenticated_client.post("/api/v1/auth/change-password", json=password_data)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
    
    @pytest.mark.asyncio
    async def test_logout(self, authenticated_client: AsyncClient):
        """Test user logout."""
        # Act
        response = await authenticated_client.post("/api/v1/auth/logout")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
    
    @pytest.mark.asyncio
    async def test_account_verification(self, test_client: AsyncClient, db_session):
        """Test account verification process."""
        # Create unverified user
        user = await UserFactory.create(session=db_session, is_verified=False)
        
        # Create verification token
        verification_token = create_access_token(
            data={"sub": user.email, "type": "email_verification"},
            expires_delta=timedelta(days=1)
        )
        
        # Act
        response = await test_client.post(
            f"/api/v1/auth/verify-email?token={verification_token}"
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "verified" in data["message"].lower()
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self, test_client: AsyncClient):
        """Test rate limiting on authentication endpoints."""
        # Arrange - invalid login data
        login_data = {
            "username": "nonexistent@example.com",
            "password": "wrongpassword"
        }
        
        # Act - make multiple failed login attempts
        responses = []
        for _ in range(10):  # Exceed rate limit
            response = await test_client.post("/api/v1/auth/login", data=login_data)
            responses.append(response.status_code)
        
        # Assert - should eventually hit rate limit
        assert any(status == 429 for status in responses)  # Too Many Requests
    
    @pytest.mark.asyncio
    async def test_concurrent_logins(self, test_client: AsyncClient, test_user):
        """Test handling concurrent login attempts."""
        import asyncio
        
        # Arrange
        login_data = {
            "username": test_user.email,
            "password": "secret"
        }
        
        # Act - concurrent login attempts
        tasks = [
            test_client.post("/api/v1/auth/login", data=login_data)
            for _ in range(5)
        ]
        responses = await asyncio.gather(*tasks)
        
        # Assert - all should succeed
        for response in responses:
            assert response.status_code == 200
            data = response.json()
            assert "access_token" in data
    
    @pytest.mark.asyncio
    async def test_session_management(self, authenticated_client: AsyncClient, test_user):
        """Test session management features."""
        # Get active sessions
        response = await authenticated_client.get("/api/v1/auth/sessions")
        assert response.status_code == 200
        
        sessions = response.json()
        assert len(sessions) >= 1
        assert all("created_at" in session for session in sessions)
        assert all("last_activity" in session for session in sessions)
    
    @pytest.mark.asyncio
    async def test_security_headers(self, test_client: AsyncClient):
        """Test security headers in authentication responses."""
        # Arrange
        registration_data = {
            "email": "security@example.com",
            "password": "SecurePassword123!",
            "first_name": "Security",
            "last_name": "Test"
        }
        
        # Act
        response = await test_client.post("/api/v1/auth/register", json=registration_data)
        
        # Assert security headers
        headers = response.headers
        assert "X-Content-Type-Options" in headers
        assert "X-Frame-Options" in headers
        assert "X-XSS-Protection" in headers
    
    @pytest.mark.asyncio
    async def test_input_sanitization(self, test_client: AsyncClient):
        """Test input sanitization and validation."""
        # Test XSS attempt in registration
        malicious_data = {
            "email": "xss@example.com",
            "password": "Password123!",
            "first_name": "<script>alert('xss')</script>",
            "last_name": "Test"
        }
        
        response = await test_client.post("/api/v1/auth/register", json=malicious_data)
        
        if response.status_code == 201:  # If registration succeeds
            data = response.json()
            # Name should be sanitized
            assert "<script>" not in data["first_name"]
            assert "alert" not in data["first_name"]