#!/usr/bin/env python3
"""
Test JWT authentication system with real database
"""
import asyncio
import sys
import httpx
from pathlib import Path
from datetime import datetime
import uuid

sys.path.insert(0, str(Path(__file__).parent))


async def test_auth_endpoints():
    """Test authentication endpoints"""
    print("=" * 60)
    print("TESTING JWT AUTHENTICATION SYSTEM")
    print("=" * 60)
    
    base_url = "http://localhost:8000/api/v1"
    
    # Generate unique test user
    test_id = str(uuid.uuid4())[:8]
    test_user = {
        "email": f"test_{test_id}@example.com",
        "username": f"testuser_{test_id}",
        "password": "TestPass123!",
        "full_name": "Test User"
    }
    
    async with httpx.AsyncClient() as client:
        # Test 1: Register new user
        print("\n1. Testing user registration...")
        try:
            response = await client.post(
                f"{base_url}/auth/register",
                json=test_user
            )
            if response.status_code == 200:
                user_data = response.json()
                print(f"✓ User registered successfully")
                print(f"  ID: {user_data['id']}")
                print(f"  Email: {user_data['email']}")
                print(f"  Username: {user_data['username']}")
            else:
                print(f"✗ Registration failed: {response.status_code}")
                print(f"  Error: {response.text}")
                return False
        except Exception as e:
            print(f"✗ Registration error: {e}")
            return False
        
        # Test 2: Login with credentials
        print("\n2. Testing login...")
        try:
            # OAuth2 expects form data, not JSON
            login_data = {
                "username": test_user["email"],  # Can use email or username
                "password": test_user["password"]
            }
            response = await client.post(
                f"{base_url}/auth/login",
                data=login_data  # Use form data
            )
            if response.status_code == 200:
                tokens = response.json()
                access_token = tokens["access_token"]
                refresh_token = tokens["refresh_token"]
                print(f"✓ Login successful")
                print(f"  Token type: {tokens['token_type']}")
                print(f"  Access token: {access_token[:20]}...")
                print(f"  Refresh token: {refresh_token[:20]}...")
            else:
                print(f"✗ Login failed: {response.status_code}")
                print(f"  Error: {response.text}")
                return False
        except Exception as e:
            print(f"✗ Login error: {e}")
            return False
        
        # Test 3: Access protected endpoint
        print("\n3. Testing protected endpoint access...")
        try:
            headers = {"Authorization": f"Bearer {access_token}"}
            response = await client.get(
                f"{base_url}/portfolio/positions",
                headers=headers
            )
            if response.status_code == 200:
                print(f"✓ Successfully accessed protected endpoint")
                positions = response.json()
                print(f"  Positions returned: {len(positions)}")
            else:
                print(f"✗ Protected access failed: {response.status_code}")
                print(f"  Error: {response.text}")
        except Exception as e:
            print(f"✗ Protected access error: {e}")
        
        # Test 4: Refresh token
        print("\n4. Testing token refresh...")
        try:
            response = await client.post(
                f"{base_url}/auth/refresh",
                json={"refresh_token": refresh_token}
            )
            if response.status_code == 200:
                new_tokens = response.json()
                print(f"✓ Token refreshed successfully")
                print(f"  New access token: {new_tokens['access_token'][:20]}...")
            else:
                print(f"✗ Token refresh failed: {response.status_code}")
                print(f"  Error: {response.text}")
        except Exception as e:
            print(f"✗ Token refresh error: {e}")
        
        # Test 5: Duplicate registration (should fail)
        print("\n5. Testing duplicate registration prevention...")
        try:
            response = await client.post(
                f"{base_url}/auth/register",
                json=test_user
            )
            if response.status_code == 400:
                print(f"✓ Duplicate registration correctly prevented")
                error = response.json()
                print(f"  Error: {error['detail']}")
            else:
                print(f"✗ Duplicate registration not prevented!")
        except Exception as e:
            print(f"✗ Duplicate check error: {e}")
        
        # Test 6: Invalid login
        print("\n6. Testing invalid login...")
        try:
            bad_login = {
                "username": test_user["email"],
                "password": "WrongPassword123"
            }
            response = await client.post(
                f"{base_url}/auth/login",
                data=bad_login
            )
            if response.status_code == 401:
                print(f"✓ Invalid login correctly rejected")
            else:
                print(f"✗ Invalid login not rejected!")
        except Exception as e:
            print(f"✗ Invalid login test error: {e}")
        
        # Test 7: Logout
        print("\n7. Testing logout...")
        try:
            response = await client.post(f"{base_url}/auth/logout")
            if response.status_code == 200:
                print(f"✓ Logout successful")
            else:
                print(f"✗ Logout failed: {response.status_code}")
        except Exception as e:
            print(f"✗ Logout error: {e}")
    
    return True


async def test_jwt_handler():
    """Test JWT handler directly"""
    print("\n" + "=" * 60)
    print("TESTING JWT HANDLER")
    print("=" * 60)
    
    from app.services.auth.jwt_handler import jwt_handler
    
    # Test 1: Password hashing
    print("\n1. Testing password hashing...")
    password = "TestPassword123!"
    hashed = jwt_handler.get_password_hash(password)
    print(f"✓ Password hashed: {hashed[:20]}...")
    
    # Test 2: Password verification
    print("\n2. Testing password verification...")
    if jwt_handler.verify_password(password, hashed):
        print("✓ Correct password verified")
    else:
        print("✗ Password verification failed")
    
    if not jwt_handler.verify_password("WrongPassword", hashed):
        print("✓ Wrong password correctly rejected")
    else:
        print("✗ Wrong password not rejected")
    
    # Test 3: Token creation and decoding
    print("\n3. Testing token creation...")
    user_id = str(uuid.uuid4())
    email = "test@example.com"
    
    access_token = jwt_handler.create_access_token(user_id, email)
    print(f"✓ Access token created: {access_token[:20]}...")
    
    refresh_token = jwt_handler.create_refresh_token(user_id)
    print(f"✓ Refresh token created: {refresh_token[:20]}...")
    
    # Test 4: Token decoding
    print("\n4. Testing token decoding...")
    payload = jwt_handler.decode_token(access_token)
    if payload:
        print(f"✓ Access token decoded successfully")
        print(f"  User ID: {payload.get('sub')}")
        print(f"  Email: {payload.get('email')}")
        print(f"  Type: {payload.get('type')}")
    else:
        print("✗ Token decoding failed")
    
    # Test 5: Invalid token
    print("\n5. Testing invalid token handling...")
    invalid_payload = jwt_handler.decode_token("invalid.token.here")
    if invalid_payload is None:
        print("✓ Invalid token correctly rejected")
    else:
        print("✗ Invalid token not rejected")


async def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("JWT AUTHENTICATION TESTS")
    print("=" * 60)
    print("\n⚠️  Make sure the FastAPI server is running:")
    print("  cd backend && uvicorn app.main:app --reload")
    
    # Test JWT handler
    await test_jwt_handler()
    
    # Test auth endpoints (requires running server)
    print("\n" + "=" * 60)
    print("TESTING AUTH ENDPOINTS (requires server)")
    print("=" * 60)
    
    try:
        success = await test_auth_endpoints()
    except httpx.ConnectError:
        print("\n✗ Could not connect to server")
        print("  Please start the server first:")
        print("  cd backend && uvicorn app.main:app --reload")
        success = False
    
    print("\n" + "=" * 60)
    if success:
        print("✓ JWT AUTHENTICATION TESTS PASSED")
    else:
        print("✗ Some tests failed - see above for details")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())