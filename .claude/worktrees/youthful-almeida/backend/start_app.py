#!/usr/bin/env python3
"""
Startup script for the AI Financial Planning System

This script demonstrates how to start the application properly
with automatic dependency detection and graceful degradation.
"""

import sys
import os
import subprocess
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed"""
    dependencies = {
        'fastapi': 'FastAPI web framework',
        'uvicorn': 'ASGI server',
        'pydantic': 'Data validation library',
        'sqlalchemy': 'Database ORM'
    }
    
    missing = []
    available = []
    
    for dep, description in dependencies.items():
        try:
            __import__(dep)
            available.append(f"✅ {dep}: {description}")
        except ImportError:
            missing.append(f"❌ {dep}: {description}")
    
    return available, missing

def install_minimal_dependencies():
    """Install minimal dependencies for basic functionality"""
    print("Installing minimal dependencies...")
    
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install", 
            "fastapi", "uvicorn[standard]", "pydantic", "python-multipart"
        ], check=True)
        print("✅ Minimal dependencies installed successfully!")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install dependencies")
        return False

def start_with_uvicorn():
    """Start the application with uvicorn"""
    print("Starting application with uvicorn...")
    
    # Set environment variables for development
    os.environ.setdefault('DEBUG', 'true')
    os.environ.setdefault('ENVIRONMENT', 'development')
    os.environ.setdefault('HOST', '0.0.0.0')
    os.environ.setdefault('PORT', '8000')
    
    try:
        # Change to the backend directory
        os.chdir(Path(__file__).parent)
        
        cmd = [
            sys.executable, "-m", "uvicorn", 
            "app.main:app",
            "--host", os.getenv('HOST', '0.0.0.0'),
            "--port", os.getenv('PORT', '8000'),
            "--reload",
            "--log-level", "info"
        ]
        
        print(f"Running command: {' '.join(cmd)}")
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\n🛑 Application stopped by user")
    except Exception as e:
        print(f"❌ Failed to start application: {e}")
        return False
    
    return True

def start_fallback_mode():
    """Start in fallback mode without full dependencies"""
    print("Starting in fallback mode...")
    print("This mode provides basic functionality even without all dependencies.")
    
    try:
        # Import and test the application
        from app.main import app, AVAILABLE_SERVICES
        
        print("\n📊 Service Status:")
        for service, available in AVAILABLE_SERVICES.items():
            status = "✅" if available else "❌"
            print(f"  {status} {service}")
        
        print(f"\n🔗 Available routes: {len(app.routes)}")
        
        # Try to start a basic HTTP server
        print("\n🚀 Starting basic HTTP server on http://localhost:8080")
        print("Note: This is a demonstration mode with limited functionality")
        print("Press Ctrl+C to stop")
        
        # This is a basic demo - in reality you'd use a proper server
        import http.server
        import socketserver
        
        class Handler(http.server.SimpleHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                response = {
                    "message": "AI Financial Planning System (Fallback Mode)",
                    "status": "running",
                    "services": AVAILABLE_SERVICES,
                    "note": "Limited functionality - install FastAPI for full features"
                }
                import json
                self.wfile.write(json.dumps(response, indent=2).encode())
        
        with socketserver.TCPServer(("", 8080), Handler) as httpd:
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print("\n🛑 Fallback server stopped by user")
    except Exception as e:
        print(f"❌ Failed to start fallback mode: {e}")
        return False
    
    return True

def main():
    """Main startup routine"""
    print("🚀 AI Financial Planning System - Startup Script")
    print("=" * 60)
    
    # Check current dependencies
    available, missing = check_dependencies()
    
    print("\n📋 Dependency Status:")
    for dep in available:
        print(f"  {dep}")
    
    if missing:
        print("\n⚠️  Missing Dependencies:")
        for dep in missing:
            print(f"  {dep}")
        
        print("\nOptions:")
        print("1. Install minimal dependencies and start normally")
        print("2. Start in fallback mode (limited functionality)")
        print("3. Exit")
        
        try:
            choice = input("\nEnter your choice (1-3): ").strip()
        except KeyboardInterrupt:
            print("\n🛑 Cancelled by user")
            return 1
        
        if choice == "1":
            if install_minimal_dependencies():
                return start_with_uvicorn()
            else:
                print("❌ Installation failed. Try fallback mode.")
                return start_fallback_mode()
        elif choice == "2":
            return start_fallback_mode()
        else:
            print("👋 Goodbye!")
            return 0
    else:
        print("\n✅ All dependencies available!")
        return start_with_uvicorn()

if __name__ == "__main__":
    sys.exit(main() or 0)