#!/usr/bin/env python3
"""
Simple script to start the FastAPI server with the correct database configuration.
"""
import os
import sys

# Set environment variables for database connection
os.environ['DATABASE_URL'] = 'postgresql://financial_user:secure_password_123@localhost:5432/financial_planner'
os.environ['REDIS_URL'] = 'redis://:redis_password_123@localhost:6379'
os.environ['ENVIRONMENT'] = 'development'
os.environ['LOG_LEVEL'] = 'INFO'
os.environ['CORS_ORIGINS'] = '["http://localhost:3000", "http://localhost:3002"]'
os.environ['WS_MAX_CONNECTIONS_PER_USER'] = '5'

# Import and run the FastAPI app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.app.main_portfolio:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )