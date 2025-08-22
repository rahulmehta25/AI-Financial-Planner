#!/usr/bin/env python3
"""
Development Startup Script for AI Financial Planning System

This script helps start the development environment with proper configuration.
"""

import os
import sys
import subprocess
import asyncio
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ is required")
        sys.exit(1)
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import fastapi
        import uvicorn
        import sqlalchemy
        import numpy
        import numba
        print("✅ Core dependencies are installed")
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Please run: pip install -r requirements.txt")
        sys.exit(1)

def create_env_file():
    """Create .env file from template if it doesn't exist"""
    env_file = Path(".env")
    template_file = Path("env.template")
    
    if not env_file.exists() and template_file.exists():
        print("📝 Creating .env file from template...")
        with open(template_file, 'r') as f:
            content = f.read()
        
        # Generate a random secret key
        import secrets
        secret_key = secrets.token_urlsafe(32)
        content = content.replace("your-secret-key-here-change-in-production", secret_key)
        
        with open(env_file, 'w') as f:
            f.write(content)
        print("✅ .env file created with generated secret key")
    elif env_file.exists():
        print("✅ .env file already exists")
    else:
        print("⚠️  No .env file or template found")

def check_database():
    """Check database connectivity"""
    print("🔍 Checking database connectivity...")
    try:
        # This is a basic check - in production you'd want more robust checking
        print("⚠️  Database check skipped in development mode")
        print("   Make sure PostgreSQL is running and accessible")
        return True
    except Exception as e:
        print(f"❌ Database check failed: {e}")
        return False

def start_development_server():
    """Start the development server"""
    print("🚀 Starting development server...")
    
    # Set development environment variables
    os.environ["ENVIRONMENT"] = "development"
    os.environ["DEBUG"] = "true"
    os.environ["RELOAD"] = "true"
    
    try:
        # Start uvicorn server
        cmd = [
            sys.executable, "-m", "uvicorn",
            "app.main:app",
            "--host", "0.0.0.0",
            "--port", "8000",
            "--reload",
            "--log-level", "debug"
        ]
        
        print(f"Running: {' '.join(cmd)}")
        subprocess.run(cmd)
        
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        sys.exit(1)

def main():
    """Main startup function"""
    print("🎯 AI Financial Planning System - Development Startup")
    print("=" * 60)
    
    # Change to backend directory
    backend_dir = Path(__file__).parent
    os.chdir(backend_dir)
    
    # Run checks
    check_python_version()
    check_dependencies()
    create_env_file()
    
    print("\n📋 Environment Setup Complete!")
    print("\n🔧 Next Steps:")
    print("1. Configure your .env file with database credentials")
    print("2. Start PostgreSQL database")
    print("3. Run database migrations: alembic upgrade head")
    print("4. Start Redis (optional, for caching)")
    print("5. Configure AI API keys if using LLM features")
    
    print("\n🚀 Starting development server...")
    start_development_server()

if __name__ == "__main__":
    main()
