# Financial Planning Database Setup Guide

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
