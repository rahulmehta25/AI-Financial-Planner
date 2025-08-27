#!/usr/bin/env python3
"""
Production startup script for AI Financial Planning Backend
"""

import os
import sys
import logging
import asyncio
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def setup_environment():
    """Setup environment for production"""
    # Set production environment
    os.environ.setdefault("ENVIRONMENT", "production")
    os.environ.setdefault("DEBUG", "false")
    
    # Load production environment file if it exists
    env_file = Path(".env.production")
    if env_file.exists():
        from dotenv import load_dotenv
        load_dotenv(env_file)
        logger.info("Loaded production environment variables")
    
    # Set default values if not provided
    os.environ.setdefault("HOST", "0.0.0.0")
    os.environ.setdefault("PORT", "8000")
    os.environ.setdefault("SECRET_KEY", "ai-financial-planner-change-this-in-production")
    os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./financial_planning.db")

async def initialize_database():
    """Initialize database on startup"""
    try:
        from app.database.init_db import init_db
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.warning(f"Database initialization failed: {e}")

def main():
    """Main entry point"""
    setup_environment()
    
    # Initialize database
    try:
        asyncio.run(initialize_database())
    except Exception as e:
        logger.warning(f"Database setup failed: {e}")
    
    # Import and start the app
    try:
        import uvicorn
        from app.main import app
        
        host = os.getenv("HOST", "0.0.0.0")
        port = int(os.getenv("PORT", "8000"))
        
        logger.info(f"Starting AI Financial Planning Backend on {host}:{port}")
        logger.info("Production mode: ON")
        
        uvicorn.run(
            app,
            host=host,
            port=port,
            log_level="info",
            access_log=True,
            use_colors=False,
            loop="asyncio"
        )
        
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()