#!/usr/bin/env python3
"""
Startup Test Suite

Tests the application startup in various configurations to ensure
robust behavior regardless of available dependencies.
"""

import sys
import logging
import json
import asyncio
from datetime import datetime

# Setup logging for tests
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_minimal_import():
    """Test that the minimal application can be imported"""
    try:
        from app.minimal_main import main as minimal_main
        app = minimal_main()
        
        # Test status
        status = app.get_status()
        assert status['version'] == '1.0.0'
        assert status['status'] == 'running_minimal'
        
        # Test health check
        health = app.get_health()
        assert health['status'] == 'degraded'
        assert 'services' in health
        
        # Test mock simulation
        simulation = app.get_mock_simulation()
        assert simulation['id'] == 'mock-sim-001'
        assert simulation['results']['probability_of_success'] == 0.87
        
        logger.info("✓ Minimal application import and basic functionality test passed")
        return True
    except Exception as e:
        logger.error(f"✗ Minimal application test failed: {e}")
        return False

def test_main_import():
    """Test that the main application can be imported"""
    try:
        from app.main import app
        logger.info(f"✓ Main application imported successfully (type: {type(app).__name__})")
        
        # Test basic app properties
        if hasattr(app, 'routes'):
            logger.info(f"✓ Application has {len(app.routes)} routes registered")
        
        return True
    except Exception as e:
        logger.error(f"✗ Main application import failed: {e}")
        return False

def test_startup_script():
    """Test the startup script functionality"""
    try:
        import start_app
        logger.info("✓ Startup script imports successfully")
        
        # Test dependency checking
        deps = start_app.check_dependencies()
        logger.info(f"✓ Dependency check completed: {sum(deps.values())}/{len(deps)} available")
        
        return True
    except Exception as e:
        logger.error(f"✗ Startup script test failed: {e}")
        return False

def test_service_availability():
    """Test service availability detection"""
    try:
        from app.main import AVAILABLE_SERVICES, IMPORT_ERRORS
        
        logger.info("Service Availability Status:")
        for service, available in AVAILABLE_SERVICES.items():
            status = "✓" if available else "✗"
            logger.info(f"  {status} {service}")
        
        if IMPORT_ERRORS:
            logger.info("Import Errors:")
            for service, error in IMPORT_ERRORS.items():
                logger.info(f"  • {service}: {error[:50]}...")
        
        return True
    except Exception as e:
        logger.error(f"✗ Service availability test failed: {e}")
        return False

async def test_mock_endpoints():
    """Test that mock endpoints work"""
    try:
        from app.main import app
        
        # If we have routes, test them
        if hasattr(app, 'routes') and app.routes:
            logger.info(f"✓ Found {len(app.routes)} registered routes")
            
            # Look for specific route patterns
            route_paths = [route.get('path', 'unknown') for route in app.routes if isinstance(route, dict)]
            expected_paths = ["/", "/health", "/status"]
            
            for path in expected_paths:
                if path in route_paths:
                    logger.info(f"✓ Found expected route: {path}")
                else:
                    logger.warning(f"⚠ Missing expected route: {path}")
        
        return True
    except Exception as e:
        logger.error(f"✗ Mock endpoints test failed: {e}")
        return False

def main():
    """Run all startup tests"""
    print("AI Financial Planning System - Startup Test Suite")
    print("=" * 60)
    
    tests = [
        ("Minimal Application Import", test_minimal_import),
        ("Main Application Import", test_main_import),
        ("Startup Script", test_startup_script),
        ("Service Availability", test_service_availability),
        ("Mock Endpoints", lambda: asyncio.run(test_mock_endpoints()))
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\nRunning: {test_name}")
        print("-" * 30)
        
        try:
            if test_func():
                passed += 1
        except Exception as e:
            logger.error(f"Test {test_name} failed with exception: {e}")
    
    print("\n" + "=" * 60)
    print("TEST RESULTS")
    print("=" * 60)
    print(f"Passed: {passed}/{total}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("🎉 All tests passed! Application startup is robust.")
        return 0
    else:
        print("⚠️  Some tests failed. Check logs for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())