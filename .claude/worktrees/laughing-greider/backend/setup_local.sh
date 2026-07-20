#!/bin/bash

# Local Development Setup Script
echo "🚀 Setting up Financial Planner Backend..."

# Check Python version
python_version=$(python3 --version 2>&1 | grep -oE '[0-9]+\.[0-9]+')
required_version="3.11"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then 
    echo "❌ Python 3.11+ required. Current: $python_version"
    exit 1
fi

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install core dependencies first
echo "📚 Installing core dependencies..."
pip install --upgrade pip
pip install fastapi uvicorn sqlalchemy psycopg2-binary alembic python-dotenv

# Install financial libraries
echo "💹 Installing financial libraries..."
pip install yfinance pandas numpy scipy scikit-learn

# Install additional services
echo "🔧 Installing additional services..."
pip install redis celery pytest pytest-cov black pylint

# Create .env file if not exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cat > .env << EOL
# Database
DATABASE_URL=postgresql://localhost/financial_planner_dev

# Redis
REDIS_URL=redis://localhost:6379

# Market Data (get free API keys)
ALPHA_VANTAGE_API_KEY=your_key_here
FINNHUB_API_KEY=your_key_here

# AI (optional for now)
OPENAI_API_KEY=your_key_here

# Security
SECRET_KEY=$(openssl rand -hex 32)
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
EOL
fi

# Create database structure
echo "🗄️ Setting up database..."
cat > app/database/init_db.py << 'EOL'
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.base import Base
from app.models import User, Portfolio, Transaction, Holding
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost/financial_planner_dev")

engine = create_engine(DATABASE_URL)
Base.metadata.create_all(bind=engine)

print("✅ Database tables created successfully!")
EOL

python -c "from app.database.init_db import *"

echo "✅ Setup complete! Run with: uvicorn app.main:app --reload"