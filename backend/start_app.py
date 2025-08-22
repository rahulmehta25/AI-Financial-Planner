#!/usr/bin/env python3
"""
Application Startup Script

This script can start the FastAPI application in various modes based on
available dependencies.
"""

import sys
import os
import logging
import subprocess

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_dependencies():
    """Check which dependencies are available"""
    dependencies = {
        "fastapi": False,
        "uvicorn": False,
        "pydantic": False,
        "sqlalchemy": False
    }
    
    for dep in dependencies:
        try:
            __import__(dep)
            dependencies[dep] = True
            logger.info(f"✓ {dep} is available")
        except ImportError:
            logger.warning(f"✗ {dep} is not available")
    
    return dependencies

def start_with_uvicorn():
    """Start the application with uvicorn"""
    try:
        cmd = [
            sys.executable, "-m", "uvicorn", 
            "app.main:app", 
            "--reload", 
            "--host", "0.0.0.0", 
            "--port", "8000"
        ]
        logger.info("Starting FastAPI application with uvicorn...")
        logger.info(f"Command: {' '.join(cmd)}")
        subprocess.run(cmd)
    except FileNotFoundError:
        logger.error("uvicorn not found. Please install with: pip install uvicorn")
        return False
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
        return True
    except Exception as e:
        logger.error(f"Failed to start with uvicorn: {e}")
        return False

def start_minimal_mode():
    """Start in minimal mode without uvicorn"""
    logger.info("Starting in minimal diagnostic mode...")
    try:
        from app.main import app
        logger.info("Application imported successfully")
        
        # If we have a minimal app, show its status
        if hasattr(app, 'get_status'):
            status = app.get_status()
            print("\n" + "="*60)
            print("APPLICATION STATUS")
            print("="*60)
            print(f"Status: {status.get('status', 'unknown')}")
            print(f"Version: {status.get('version', 'unknown')}")
            print(f"Mode: {status.get('mode', 'unknown')}")
            print("="*60)
        
        return True
    except Exception as e:
        logger.error(f"Failed to start in minimal mode: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main startup logic"""
    print("AI Financial Planning System - Startup Script")
    print("=" * 50)
    
    # Check dependencies
    deps = check_dependencies()
    
    # Determine startup mode
    if deps["fastapi"] and deps["uvicorn"]:
        logger.info("Full FastAPI environment detected")
        success = start_with_uvicorn()
    elif deps["fastapi"]:
        logger.info("FastAPI available but uvicorn missing")
        logger.info("Install uvicorn with: pip install uvicorn")
        success = start_minimal_mode()
    else:
        logger.info("FastAPI not available, running minimal diagnostics")
        success = start_minimal_mode()
    
    if not success:
        print("\nTroubleshooting:")
        print("1. Install dependencies: pip install fastapi uvicorn pydantic sqlalchemy")
        print("2. Check Python path and working directory")
        print("3. Try: python3 app/minimal_main.py")
        sys.exit(1)

if __name__ == "__main__":
    main()