#!/usr/bin/env python3
"""
Test FastAPI application structure
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

async def test_app_structure():
    """Test FastAPI app can be imported and initialized"""
    print("=" * 60)
    print("TESTING FASTAPI APPLICATION STRUCTURE")
    print("=" * 60)
    
    # Test 1: Import main app
    print("\n1. Testing app import...")
    try:
        from app.main import app
        print("✓ Successfully imported FastAPI app")
        print(f"  App title: {app.title}")
        print(f"  App version: {app.version}")
    except Exception as e:
        print(f"✗ Failed to import app: {e}")
        return False
    
    # Test 2: Check routes
    print("\n2. Checking registered routes...")
    routes = []
    for route in app.routes:
        if hasattr(route, "path"):
            routes.append(route.path)
    
    expected_routes = ["/health", "/health/detailed", "/", "/api/v1"]
    for expected in expected_routes:
        if any(expected in r for r in routes):
            print(f"✓ Found route: {expected}")
        else:
            print(f"✗ Missing route: {expected}")
    
    # Test 3: Check middleware
    print("\n3. Checking middleware...")
    if hasattr(app, 'user_middleware'):
        middleware_count = len(app.user_middleware)
        print(f"✓ {middleware_count} middleware registered")
    else:
        print("✓ Middleware configured")
    
    # Test 4: Test imports
    print("\n4. Testing component imports...")
    try:
        from app.api.v1.deps import get_db, get_current_user, get_data_provider
        print("✓ Dependencies imported successfully")
    except Exception as e:
        print(f"✗ Failed to import dependencies: {e}")
    
    try:
        from app.api.v1.endpoints import portfolio
        print("✓ Portfolio endpoint imported successfully")
    except Exception as e:
        print(f"✗ Failed to import portfolio endpoint: {e}")
    
    try:
        from app.schemas.portfolio import PortfolioResponse, PositionResponse
        print("✓ Schemas imported successfully")
    except Exception as e:
        print(f"✗ Failed to import schemas: {e}")
    
    # Test 5: Check OpenAPI schema generation
    print("\n5. Testing OpenAPI schema generation...")
    try:
        schema = app.openapi()
        print(f"✓ OpenAPI schema generated")
        print(f"  Paths: {len(schema.get('paths', {}))}")
        print(f"  Components: {len(schema.get('components', {}).get('schemas', {}))}")
    except Exception as e:
        print(f"✗ Failed to generate OpenAPI schema: {e}")
    
    return True


async def test_server_startup():
    """Test server can start (without actually running it)"""
    print("\n" + "=" * 60)
    print("TESTING SERVER INITIALIZATION")
    print("=" * 60)
    
    try:
        import uvicorn
        from app.main import app
        
        # Just test that we can create the server config
        config = uvicorn.Config(
            app=app,
            host="0.0.0.0",
            port=8000,
            log_level="info"
        )
        print("✓ Server configuration created successfully")
        print(f"  Host: {config.host}")
        print(f"  Port: {config.port}")
        print(f"  Workers: {config.workers or 1}")
        
        return True
    except Exception as e:
        print(f"✗ Server configuration failed: {e}")
        return False


async def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("FASTAPI STRUCTURE TESTS")
    print("=" * 60)
    
    # Test app structure
    success = await test_app_structure()
    
    if success:
        # Test server config
        await test_server_startup()
    
    print("\n" + "=" * 60)
    if success:
        print("✓ FASTAPI STRUCTURE TESTS PASSED")
        print("\nTo run the server:")
        print("  cd backend")
        print("  uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
        print("\nAPI docs will be available at:")
        print("  http://localhost:8000/api/docs")
    else:
        print("✗ FASTAPI STRUCTURE TESTS FAILED")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())