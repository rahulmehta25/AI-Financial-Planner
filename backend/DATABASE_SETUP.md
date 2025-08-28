# Financial Planning System - Database Setup Guide

This guide covers the complete database architecture setup for the Financial Planning System, including enhanced models, TimescaleDB configuration, and performance optimization.

## 🏗️ Database Architecture Overview

The system implements a comprehensive database schema with the following key components:

### Enhanced Models
- **Users**: KYC compliance, MFA support, risk profiling
- **Portfolios**: Version control, cached metrics, rebalancing logic
- **Accounts**: 401k, Roth IRA, 529, HSA, taxable accounts with tax tracking
- **Transactions**: Tax lot tracking, wash sale detection, comprehensive metadata
- **MarketData**: TimescaleDB optimized time-series data with technical indicators

### Key Features
- ✅ TimescaleDB integration for high-performance time-series data
- ✅ Comprehensive indexing strategy for financial queries
- ✅ Automated performance optimization
- ✅ Database relationship validation
- ✅ Tax optimization and wash sale detection
- ✅ Regulatory compliance and audit trails

## 🚀 Quick Start

### Prerequisites
```bash
# Ensure you have PostgreSQL with TimescaleDB extension (optional but recommended)
# For development, SQLite is also supported

# Install Python dependencies
pip install -r requirements.txt
```

### Complete Database Setup
```bash
# Run complete database setup (recommended for new installations)
python setup_database.py --all
```

This will:
1. ✅ Initialize database schema and migrations
2. ⏰ Configure TimescaleDB hypertables and continuous aggregates
3. ⚡ Create performance-optimized indexes
4. 🔍 Validate all relationships and constraints
5. 🏥 Perform final health check

## 🔧 Individual Operations

### Database Initialization Only
```bash
# Initialize schema, apply migrations, create indexes
python setup_database.py --init
```

### Performance Optimization
```bash
# Analyze and optimize database performance
python setup_database.py --optimize
```

### Database Validation
```bash
# Validate relationships, constraints, and data integrity
python setup_database.py --validate
```

### Health Check
```bash
# Check database connectivity and health
python setup_database.py --health
```

## 📊 Database Schema Components

### Core Tables

#### `enhanced_users`
```sql
-- User accounts with KYC compliance and MFA
- id (UUID, Primary Key)
- email (Unique, Indexed)
- mfa_secret, mfa_enabled, mfa_backup_codes
- risk_tolerance (0.0-1.0), investment_horizon
- kyc_status, kyc_data, kyc_verified_at
- accredited_investor status
- Comprehensive audit fields
```

#### `enhanced_portfolios`
```sql
-- Portfolio management with cached metrics
- id (UUID, Primary Key)
- user_id (FK to enhanced_users)
- total_value, cash_balance, invested_value
- performance metrics (YTD, 1yr, 3yr, inception)
- risk metrics (volatility, sharpe_ratio, beta)
- cached_metrics (JSONB for performance)
- rebalancing configuration and thresholds
```

#### `enhanced_accounts`
```sql
-- Account types: 401k, Roth IRA, 529, HSA, taxable
- id (UUID, Primary Key)
- portfolio_id (FK to enhanced_portfolios)
- account_type, institution, encrypted credentials
- current_balance, vested/unvested balances
- contribution limits and YTD contributions
- tax tracking fields (cost basis, gains/losses)
- Plaid integration for bank connectivity
```

#### `enhanced_transactions`
```sql
-- Comprehensive transaction tracking
- id (UUID, Primary Key)
- account_id (FK to enhanced_accounts)
- type, symbol, quantity, price, total_amount
- comprehensive fee tracking
- tax_lot_id for cost basis tracking
- wash_sale detection and adjustments
- corporate action handling
- data quality and confidence scoring
```

#### `enhanced_market_data` (TimescaleDB Hypertable)
```sql
-- High-performance time-series market data
- time, symbol (Composite Primary Key)
- OHLCV data with extended metrics
- Technical indicators (RSI, MACD, Bollinger Bands)
- Market microstructure (bid/ask, spreads)
- Alternative data (sentiment, analyst ratings)
- Optimized for TimescaleDB with compression
```

### Performance Features

#### Specialized Indexes
- **Transaction Analysis**: `(account_id, trade_date, symbol)` 
- **Tax Reporting**: `(tax_year, tax_category, account_id)`
- **Wash Sale Detection**: `(account_id, symbol, trade_date)`
- **Market Data**: `(symbol, time DESC)` with included columns
- **User Activity**: `(user_id, timestamp)` for audit trails

#### TimescaleDB Optimizations
- **Hypertables**: Automatic partitioning by time
- **Continuous Aggregates**: Pre-computed daily/weekly/monthly views
- **Compression**: Automatic compression for older data
- **Retention**: Automatic data lifecycle management

## 🔍 Monitoring and Maintenance

### Performance Monitoring
```bash
# Generate performance report with recommendations
python -c "
from app.database.performance_optimizer import performance_optimizer
import asyncio
asyncio.run(performance_optimizer.generate_performance_report())
"
```

### Validation Reports
```bash
# Generate validation report for data integrity
python -c "
from app.database.relationship_validator import relationship_validator  
import asyncio
asyncio.run(relationship_validator.generate_validation_report())
"
```

### Database Health
```bash
# Check database health and statistics
python -c "
from app.database.initialize_database import database_initializer
import asyncio
asyncio.run(database_initializer.get_database_health())
"
```

## 📈 Performance Characteristics

### Expected Performance
- **Market Data Ingestion**: 10,000+ records/second with TimescaleDB
- **Portfolio Queries**: Sub-100ms response for complex aggregations
- **Transaction Analysis**: Optimized for tax reporting and wash sale detection
- **User Activity**: Fast audit trail queries with proper indexing

### Scalability Features
- **TimescaleDB**: Automatic partitioning and compression
- **Connection Pooling**: Configurable pool sizes for high concurrency
- **Query Optimization**: Specialized indexes for financial workloads
- **Caching**: Materialized views for frequently accessed data

## 🛠️ Configuration

### Environment Variables
```bash
# Database Configuration
DATABASE_URL="postgresql+asyncpg://user:pass@localhost/financialdb"
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=30

# TimescaleDB Features
TIMESCALEDB_ENABLED=true
TIMESCALEDB_CHUNK_TIME_INTERVAL="1 day"
TIMESCALEDB_COMPRESSION_ENABLED=true
TIMESCALEDB_RETENTION_PERIOD="5 years"
```

### Migration Management
```bash
# Create new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Check migration status
alembic current
```

## 🐛 Troubleshooting

### Common Issues

#### TimescaleDB Not Available
```bash
# Check if TimescaleDB extension is installed
psql -c "SELECT * FROM pg_available_extensions WHERE name = 'timescaledb';"

# Install TimescaleDB extension
psql -c "CREATE EXTENSION IF NOT EXISTS timescaledb;"
```

#### Slow Query Performance
```bash
# Run performance analysis
python setup_database.py --optimize

# Check for missing indexes
python -c "
from app.database.performance_optimizer import performance_optimizer
# Review index recommendations
"
```

#### Relationship Violations
```bash
# Run validation check
python setup_database.py --validate

# Fix orphaned records
python -c "
from app.database.relationship_validator import relationship_validator
# Review and fix relationship issues
"
```

### Migration Issues
```bash
# Reset database (development only)
alembic downgrade base
alembic upgrade head

# Check for constraint violations
python setup_database.py --validate
```

## 📚 Additional Resources

- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [TimescaleDB Documentation](https://docs.timescale.com/)
- [PostgreSQL Performance Tuning](https://www.postgresql.org/docs/current/performance-tips.html)
- [Alembic Migration Guide](https://alembic.sqlalchemy.org/en/latest/)

## 🤝 Contributing

When adding new models or relationships:

1. Update the enhanced models in `app/models/enhanced_models.py`
2. Create new Alembic migration: `alembic revision --autogenerate`
3. Add validation rules to `relationship_validator.py`
4. Update performance indexes in `performance_optimizer.py`
5. Test with `python setup_database.py --all`

---

**Note**: This database architecture is designed for production use with comprehensive security, performance, and compliance features. For development, you can use SQLite, but PostgreSQL with TimescaleDB is recommended for production deployments.