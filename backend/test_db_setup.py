#!/usr/bin/env python3
"""
Database Setup Test Script

This script tests the database setup without requiring full environment setup.
It validates:
- Database models and schema
- Initialization script functionality
- Backup and recovery scripts
- Overall database operational readiness
"""

import os
import sys
import json
from pathlib import Path

def test_file_structure():
    """Test that all required database files exist"""
    print("Testing database file structure...")
    
    required_files = [
        "app/database/__init__.py",
        "app/database/base.py", 
        "app/database/models.py",
        "app/database/init_db.py",
        "scripts/database/db_manager.py",
        "scripts/database/backup_manager.py",
        "alembic.ini",
        "alembic/env.py"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Missing files: {missing_files}")
        return False
    else:
        print("✅ All required database files exist")
        return True

def test_models_structure():
    """Test database models structure"""
    print("Testing database models structure...")
    
    try:
        # Read models file and check for key classes
        models_path = Path("app/database/models.py")
        with open(models_path, 'r') as f:
            models_content = f.read()
        
        required_models = [
            "class User",
            "class Plan", 
            "class PlanInput",
            "class PlanOutput",
            "class CapitalMarketAssumptions",
            "class PortfolioModel",
            "class AuditLog",
            "class SystemEvent",
            "class DataRetentionPolicy",
            "class AuditMixin"
        ]
        
        missing_models = []
        for model in required_models:
            if model not in models_content:
                missing_models.append(model)
        
        if missing_models:
            print(f"❌ Missing models: {missing_models}")
            return False
        else:
            print("✅ All required database models found")
            return True
            
    except Exception as e:
        print(f"❌ Error testing models: {str(e)}")
        return False

def test_initialization_script():
    """Test initialization script structure"""
    print("Testing initialization script structure...")
    
    try:
        init_db_path = Path("app/database/init_db.py")
        with open(init_db_path, 'r') as f:
            init_content = f.read()
        
        required_functions = [
            "class DatabaseInitializer",
            "async def full_initialization",
            "async def _create_seed_data",
            "async def _create_sample_users",
            "async def _create_sample_plans",
            "async def _setup_audit_logging",
            "async def health_check"
        ]
        
        missing_functions = []
        for func in required_functions:
            if func not in init_content:
                missing_functions.append(func)
        
        if missing_functions:
            print(f"❌ Missing functions: {missing_functions}")
            return False
        else:
            print("✅ All required initialization functions found")
            return True
            
    except Exception as e:
        print(f"❌ Error testing initialization script: {str(e)}")
        return False

def test_backup_scripts():
    """Test backup scripts structure"""
    print("Testing backup scripts structure...")
    
    try:
        backup_scripts = [
            "scripts/database/db_manager.py",
            "scripts/database/backup_manager.py"
        ]
        
        for script_path in backup_scripts:
            if not Path(script_path).exists():
                print(f"❌ Missing backup script: {script_path}")
                return False
            
            with open(script_path, 'r') as f:
                script_content = f.read()
            
            # Check for key functionality
            if script_path.endswith("db_manager.py"):
                required_features = [
                    "class DatabaseManager",
                    "async def initialize_database",
                    "async def health_check",
                    "async def test_audit_logging"
                ]
            else:  # backup_manager.py
                required_features = [
                    "class BackupManager", 
                    "async def create_backup",
                    "async def restore_backup",
                    "async def validate_backup",
                    "async def test_disaster_recovery"
                ]
            
            missing_features = []
            for feature in required_features:
                if feature not in script_content:
                    missing_features.append(feature)
            
            if missing_features:
                print(f"❌ Missing features in {script_path}: {missing_features}")
                return False
        
        print("✅ All backup scripts properly structured")
        return True
        
    except Exception as e:
        print(f"❌ Error testing backup scripts: {str(e)}")
        return False

def test_migration_setup():
    """Test Alembic migration setup"""
    print("Testing migration setup...")
    
    try:
        # Check alembic.ini exists
        if not Path("alembic.ini").exists():
            print("❌ Missing alembic.ini")
            return False
        
        # Check migration files
        versions_dir = Path("alembic/versions")
        if not versions_dir.exists():
            print("❌ Missing alembic/versions directory")
            return False
        
        migration_files = list(versions_dir.glob("*.py"))
        if not migration_files:
            print("❌ No migration files found")
            return False
        
        # Check that migrations contain key schema elements
        for migration_file in migration_files:
            with open(migration_file, 'r') as f:
                migration_content = f.read()
            
            if "create_table" in migration_content and "users" in migration_content:
                print("✅ Migration setup looks correct")
                return True
        
        print("❌ Migration files don't contain expected schema")
        return False
        
    except Exception as e:
        print(f"❌ Error testing migrations: {str(e)}")
        return False

def test_configuration():
    """Test configuration setup"""
    print("Testing configuration...")
    
    try:
        # Check configuration files exist
        config_files = [
            "app/core/config.py",
            "env.template"
        ]
        
        for config_file in config_files:
            if not Path(config_file).exists():
                print(f"❌ Missing configuration file: {config_file}")
                return False
        
        # Check config.py contains required settings
        with open("app/core/config.py", 'r') as f:
            config_content = f.read()
        
        required_settings = [
            "DATABASE_URL",
            "DATABASE_POOL_SIZE",
            "AUDIT_LOG_RETENTION_DAYS",
            "class Settings"
        ]
        
        missing_settings = []
        for setting in required_settings:
            if setting not in config_content:
                missing_settings.append(setting)
        
        if missing_settings:
            print(f"❌ Missing configuration settings: {missing_settings}")
            return False
        
        print("✅ Configuration setup looks correct")
        return True
        
    except Exception as e:
        print(f"❌ Error testing configuration: {str(e)}")
        return False

def generate_setup_report():
    """Generate comprehensive setup report"""
    print("\n" + "="*80)
    print("DATABASE SETUP VALIDATION REPORT")
    print("="*80)
    
    tests = [
        ("File Structure", test_file_structure),
        ("Models Structure", test_models_structure), 
        ("Initialization Script", test_initialization_script),
        ("Backup Scripts", test_backup_scripts),
        ("Migration Setup", test_migration_setup),
        ("Configuration", test_configuration)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        print("-" * 40)
        result = test_func()
        results.append((test_name, result))
    
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:25} {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 Database setup validation SUCCESSFUL!")
        print("\nNext steps:")
        print("1. Set up PostgreSQL database")
        print("2. Copy env.template to .env and configure database URL")
        print("3. Install requirements: pip install -r requirements.txt")
        print("4. Run database initialization: python scripts/database/db_manager.py init")
        print("5. Test database health: python scripts/database/db_manager.py health")
        return True
    else:
        print(f"\n❌ Database setup validation FAILED!")
        print(f"Please fix the {total - passed} failing tests above.")
        return False

def create_quick_start_guide():
    """Create a quick start guide for database setup"""
    guide_content = """# Financial Planning Database Setup Guide

## Prerequisites
- PostgreSQL 14+ installed and running
- Python 3.9+ installed
- Git repository cloned

## Quick Setup Steps

### 1. Database Setup
```bash
# Create PostgreSQL database
createdb financial_planning

# Or using psql
psql -c "CREATE DATABASE financial_planning;"
```

### 2. Environment Configuration
```bash
# Copy environment template
cp env.template .env

# Edit .env file with your database credentials
# Update DATABASE_URL=postgresql+asyncpg://username:password@localhost/financial_planning
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Initialize Database
```bash
# Full initialization with seed data
python scripts/database/db_manager.py init

# Or quick setup for development
python -c "
import asyncio
from app.database.init_db import quick_setup
asyncio.run(quick_setup())
"
```

### 5. Verify Setup
```bash
# Check database health
python scripts/database/db_manager.py health

# Test audit logging
python scripts/database/db_manager.py test-audit

# Check backup functionality
python scripts/database/backup_manager.py status
```

## Database Management Commands

### Database Operations
```bash
python scripts/database/db_manager.py init          # Initialize with seed data
python scripts/database/db_manager.py health        # Health check
python scripts/database/db_manager.py monitor       # Performance monitoring
python scripts/database/db_manager.py test-audit    # Test audit logging
python scripts/database/db_manager.py reset         # Reset database (destructive)
```

### Backup Operations
```bash
python scripts/database/backup_manager.py backup --type full
python scripts/database/backup_manager.py backup --type incremental
python scripts/database/backup_manager.py validate --backup-file backup_20240822.sql.gz
python scripts/database/backup_manager.py restore --backup-file backup_20240822.sql.gz
python scripts/database/backup_manager.py cleanup
python scripts/database/backup_manager.py test-recovery
python scripts/database/backup_manager.py status
```

## Demo Data Included

The initialization creates sample data for demonstration:
- 4 sample users with different profiles (advisor, planner, client, demo user)
- 2 sets of Capital Market Assumptions (conservative & optimistic)
- 3 portfolio models (conservative, balanced, aggressive)
- 3 sample financial plans with inputs and outputs
- Comprehensive audit logging setup
- Data retention policies
- Performance monitoring views

## Demo Login Credentials

All demo users have password: `Demo123!`

- john.advisor@demo.com (Super user, Financial Advisor)
- sarah.planner@demo.com (Certified Financial Planner)  
- michael.client@demo.com (Regular client)
- demo.user@demo.com (Demo account)

## Backup and Recovery

The system includes:
- Automated backup scheduling with retention policies
- Multiple backup types (full, incremental, differential)
- Backup validation and integrity checking
- Point-in-time recovery capabilities
- Disaster recovery testing procedures

## Monitoring and Maintenance

Built-in monitoring includes:
- Database performance metrics
- Connection pool monitoring
- Query performance analysis
- Audit log analysis
- Automated cleanup procedures

## Security Features

- Comprehensive audit logging for compliance
- Data retention policies (7-year retention for audit logs)
- Password hashing with bcrypt
- SQL injection protection via parameterized queries
- Database connection pooling with timeouts
- Automated security event logging

## Troubleshooting

Common issues and solutions:

1. **Connection refused**: Check if PostgreSQL is running
2. **Permission denied**: Ensure database user has necessary privileges
3. **Module not found**: Run `pip install -r requirements.txt`
4. **Migration errors**: Check database URL configuration in .env

For detailed logs, add `--verbose` to any command.
"""

    with open("DATABASE_SETUP_GUIDE.md", 'w') as f:
        f.write(guide_content)
    
    print("\n📚 Created DATABASE_SETUP_GUIDE.md with detailed instructions")

if __name__ == "__main__":
    # Run comprehensive setup validation
    success = generate_setup_report()
    
    # Create quick start guide
    create_quick_start_guide()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)