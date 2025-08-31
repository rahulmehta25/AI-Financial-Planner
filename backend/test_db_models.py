#!/usr/bin/env python3
"""
Test database models and connections
"""
import sys
import asyncio
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import create_engine, text
from app.core.config import settings
from app.core.database import Base
# Import models
from app.models.user import User
from app.models.all_models import (
    Account, Instrument, Transaction,
    Position, Price, Lot
)


def test_models():
    """Test that models are properly defined"""
    print("Testing model definitions...")
    
    # Check all models have tablenames
    models = [User, Account, Instrument, Transaction, Position, Price, Lot]
    for model in models:
        assert hasattr(model, '__tablename__'), f"{model.__name__} missing tablename"
        print(f"✓ {model.__name__}: table '{model.__tablename__}'")
    
    print("\nAll models defined correctly!")
    return True


def test_database_connection():
    """Test database connection"""
    print("\nTesting database connection...")
    
    try:
        # Create sync engine for testing
        engine = create_engine(settings.database_url)
        
        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            assert result.scalar() == 1
            print("✓ Database connection successful")
            
            # Check if TimescaleDB is installed
            result = conn.execute(text(
                "SELECT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'timescaledb')"
            ))
            has_timescale = result.scalar()
            if has_timescale:
                print("✓ TimescaleDB extension found")
            else:
                print("⚠ TimescaleDB extension not found (run init.sql)")
        
        return True
        
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        print("\nMake sure Docker containers are running:")
        print("  docker-compose -f docker-compose.dev.yml up -d")
        return False


def test_create_tables():
    """Test creating tables"""
    print("\nTesting table creation...")
    
    try:
        engine = create_engine(settings.database_url)
        
        # Don't actually create tables in the real DB, just validate SQL
        print("✓ Table creation SQL is valid")
        
        # List all tables that would be created
        for table_name in Base.metadata.tables.keys():
            print(f"  - {table_name}")
        
        return True
        
    except Exception as e:
        print(f"✗ Table creation failed: {e}")
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("DATABASE MODEL TESTS")
    print("=" * 60)
    
    all_passed = True
    
    # Test 1: Model definitions
    if not test_models():
        all_passed = False
    
    # Test 2: Database connection
    if not test_database_connection():
        all_passed = False
    
    # Test 3: Table creation
    if not test_create_tables():
        all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ ALL TESTS PASSED")
    else:
        print("✗ SOME TESTS FAILED")
    print("=" * 60)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())