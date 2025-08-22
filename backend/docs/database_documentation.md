# Financial Planning System Database Documentation

## Overview
This document provides comprehensive documentation for the PostgreSQL database implementation of the Financial Planning System, designed for operational excellence, compliance, and 100% reproducibility.

## Architecture

### Core Design Principles
1. **100% Reproducibility**: Every simulation can be exactly reproduced using stored random seeds, CMA versions, and complete input snapshots
2. **Comprehensive Audit Logging**: Every action is logged for compliance and debugging
3. **Performance Optimization**: Advanced indexing, partitioning, and query optimization
4. **Operational Excellence**: Automated backups, monitoring, and maintenance procedures

### Database Schema Overview

```
Financial Planning Database Schema
├── Core Tables
│   ├── users                     # User accounts and authentication
│   ├── plans                     # Financial plan metadata  
│   ├── plan_inputs               # All user-provided inputs
│   ├── plan_outputs              # Simulation results and outcomes
│   ├── capital_market_assumptions # Versioned CMA data
│   └── portfolio_models          # Risk-based portfolio templates
├── Audit & Compliance
│   ├── audit_logs               # Comprehensive audit trail
│   ├── system_events            # System events and performance metrics
│   └── data_retention_policies  # Automated data cleanup policies
└── Partitioned Tables
    └── audit_logs_partitioned   # Monthly partitioned audit logs
```

## Table Specifications

### Core Business Tables

#### users
User accounts with security and professional information.

**Key Features:**
- UUID primary keys for security
- Comprehensive audit trail
- Security fields (failed login attempts, account locking)
- Professional information for compliance

**Columns:**
```sql
id                    UUID PRIMARY KEY
email                 VARCHAR(255) UNIQUE NOT NULL
first_name           VARCHAR(100) NOT NULL
last_name            VARCHAR(100) NOT NULL
hashed_password      VARCHAR(255) NOT NULL
is_active            BOOLEAN DEFAULT TRUE
is_superuser         BOOLEAN DEFAULT FALSE
is_verified          BOOLEAN DEFAULT FALSE
timezone             VARCHAR(50) DEFAULT 'UTC'
locale               VARCHAR(10) DEFAULT 'en_US'
preferences          JSONB DEFAULT '{}'
company              VARCHAR(255)
title                VARCHAR(255)
license_number       VARCHAR(100)
last_login           TIMESTAMP WITH TIME ZONE
failed_login_attempts INTEGER DEFAULT 0
locked_until         TIMESTAMP WITH TIME ZONE
password_changed_at  TIMESTAMP WITH TIME ZONE
created_at           TIMESTAMP WITH TIME ZONE NOT NULL
updated_at           TIMESTAMP WITH TIME ZONE NOT NULL
created_by           UUID
updated_by           UUID
```

#### plans
Financial plan metadata with versioning and reproducibility.

**Key Features:**
- Complete reproducibility through random seed storage
- Version tracking and plan hierarchies
- References to CMA and portfolio model versions
- Comprehensive metadata storage

**Columns:**
```sql
id                      UUID PRIMARY KEY
user_id                UUID NOT NULL REFERENCES users(id)
name                   VARCHAR(255) NOT NULL
description            TEXT
status                 VARCHAR(50) DEFAULT 'draft'
version                INTEGER DEFAULT 1
parent_plan_id         UUID REFERENCES plans(id)
cma_id                 UUID NOT NULL REFERENCES capital_market_assumptions(id)
portfolio_model_id     UUID NOT NULL REFERENCES portfolio_models(id)
monte_carlo_iterations INTEGER DEFAULT 10000
random_seed            BIGINT NOT NULL  -- Critical for reproducibility
planning_horizon_years INTEGER NOT NULL
confidence_level       NUMERIC(3,2) DEFAULT 0.95
last_run_at           TIMESTAMP WITH TIME ZONE
completed_at          TIMESTAMP WITH TIME ZONE
tags                  JSONB DEFAULT '[]'
category              VARCHAR(100)
created_at            TIMESTAMP WITH TIME ZONE NOT NULL
updated_at            TIMESTAMP WITH TIME ZONE NOT NULL
created_by            UUID
updated_by            UUID
```

#### plan_inputs
Complete storage of all user inputs for reproducibility.

**Key Features:**
- Flexible JSONB storage for any input type
- Validation rules and error tracking
- Data source and confidence scoring
- Complete version history

**Columns:**
```sql
id                 UUID PRIMARY KEY
plan_id           UUID NOT NULL REFERENCES plans(id)
input_type        VARCHAR(100) NOT NULL  -- demographics, goals, assets, etc.
input_name        VARCHAR(255) NOT NULL
input_value       JSONB NOT NULL
validation_rules  JSONB
is_valid          BOOLEAN DEFAULT TRUE
validation_errors JSONB
data_source       VARCHAR(100)  -- user_input, imported, calculated
confidence_score  NUMERIC(3,2)  -- 0.0 to 1.0
version           INTEGER DEFAULT 1
superseded_by     UUID REFERENCES plan_inputs(id)
created_at        TIMESTAMP WITH TIME ZONE NOT NULL
updated_at        TIMESTAMP WITH TIME ZONE NOT NULL
created_by        UUID
updated_by        UUID
```

#### plan_outputs
Simulation results with statistical metadata.

**Key Features:**
- Flexible result storage with dependency tracking
- Statistical confidence intervals
- Algorithm version tracking
- Performance metrics

**Columns:**
```sql
id                         UUID PRIMARY KEY
plan_id                   UUID NOT NULL REFERENCES plans(id)
output_type               VARCHAR(100) NOT NULL  -- simulation, analysis, recommendation
output_name               VARCHAR(255) NOT NULL
output_value              JSONB NOT NULL
computation_time_ms       INTEGER
algorithm_version         VARCHAR(50)
confidence_interval_lower NUMERIC(15,2)
confidence_interval_upper NUMERIC(15,2)
standard_deviation        NUMERIC(15,2)
version                   INTEGER DEFAULT 1
depends_on_inputs         JSONB  -- List of input IDs
depends_on_outputs        JSONB  -- List of output IDs
created_at                TIMESTAMP WITH TIME ZONE NOT NULL
updated_at                TIMESTAMP WITH TIME ZONE NOT NULL
created_by                UUID
updated_by                UUID
```

#### capital_market_assumptions
Versioned CMA data for reproducibility.

**Key Features:**
- Complete version control of market assumptions
- Approval workflow tracking
- Flexible JSONB storage for any CMA structure
- Effective date management

**Columns:**
```sql
id              UUID PRIMARY KEY
version         VARCHAR(50) UNIQUE NOT NULL
name           VARCHAR(255) NOT NULL
description    TEXT
is_active      BOOLEAN DEFAULT TRUE
effective_date DATETIME NOT NULL
assumptions    JSONB NOT NULL  -- Complete CMA data
source         VARCHAR(255)
methodology    TEXT
review_date    DATETIME
approved_by    UUID
created_at     TIMESTAMP WITH TIME ZONE NOT NULL
updated_at     TIMESTAMP WITH TIME ZONE NOT NULL
created_by     UUID
updated_by     UUID
```

#### portfolio_models
Risk-based portfolio templates.

**Key Features:**
- Risk level categorization (1-10 scale)
- Asset allocation stored as JSONB
- Expected returns and risk metrics
- Active/inactive status management

**Columns:**
```sql
id               UUID PRIMARY KEY
name            VARCHAR(255) NOT NULL
risk_level      INTEGER NOT NULL CHECK (risk_level >= 1 AND risk_level <= 10)
description     TEXT
is_active       BOOLEAN DEFAULT TRUE
asset_allocation JSONB NOT NULL
expected_return  NUMERIC(5,4)  -- Annual expected return
volatility       NUMERIC(5,4)  -- Annual volatility
sharpe_ratio     NUMERIC(5,4)
created_at       TIMESTAMP WITH TIME ZONE NOT NULL
updated_at       TIMESTAMP WITH TIME ZONE NOT NULL
created_by       UUID
updated_by       UUID
```

### Audit and Compliance Tables

#### audit_logs
Comprehensive audit trail for all system actions.

**Key Features:**
- Complete change tracking with before/after values
- Request context (IP address, user agent, session)
- Compliance categorization
- Retention management
- Monthly partitioning for performance

**Columns:**
```sql
id                   UUID PRIMARY KEY
timestamp           TIMESTAMP WITH TIME ZONE NOT NULL
user_id             UUID REFERENCES users(id)
session_id          VARCHAR(255)
action              VARCHAR(100) NOT NULL  -- CREATE, READ, UPDATE, DELETE, EXECUTE
resource_type       VARCHAR(100) NOT NULL  -- plan, user, simulation, etc.
resource_id         UUID
ip_address          VARCHAR(45)  -- IPv6 compatible
user_agent          TEXT
request_id          UUID
old_values          JSONB
new_values          JSONB
changed_fields      JSONB
metadata            JSONB
severity            VARCHAR(20) DEFAULT 'info'
compliance_category VARCHAR(100)  -- GDPR, SOX, etc.
retention_until     TIMESTAMP WITH TIME ZONE
execution_time_ms   INTEGER
```

#### system_events
System performance and operational events.

**Key Features:**
- Event categorization and severity levels
- Performance metrics tracking
- Error tracking with stack traces
- Resolution workflow

**Columns:**
```sql
id                  UUID PRIMARY KEY
timestamp          TIMESTAMP WITH TIME ZONE NOT NULL
event_type         VARCHAR(100) NOT NULL  -- startup, shutdown, error, performance
event_category     VARCHAR(100) NOT NULL  -- system, database, api, simulation
message            TEXT NOT NULL
severity           VARCHAR(20) DEFAULT 'info'
component          VARCHAR(100)
environment        VARCHAR(50)
version            VARCHAR(50)
error_code         VARCHAR(50)
stack_trace        TEXT
additional_data    JSONB
duration_ms        INTEGER
memory_usage_mb    INTEGER
cpu_usage_percent  NUMERIC(5,2)
resolved           BOOLEAN DEFAULT FALSE
resolved_at        TIMESTAMP WITH TIME ZONE
resolved_by        UUID
resolution_notes   TEXT
```

#### data_retention_policies
Automated data cleanup and retention management.

**Key Features:**
- Configurable retention periods
- Multiple action types (delete, archive, anonymize)
- Cron-based scheduling
- Execution tracking and metrics

**Columns:**
```sql
id                          UUID PRIMARY KEY
name                       VARCHAR(255) UNIQUE NOT NULL
description                TEXT
is_active                  BOOLEAN DEFAULT TRUE
table_name                 VARCHAR(100) NOT NULL
conditions                 JSONB
retention_period_days      INTEGER NOT NULL CHECK (retention_period_days > 0)
action                     VARCHAR(50) DEFAULT 'delete'  -- delete, archive, anonymize
schedule_cron              VARCHAR(100)
last_executed              TIMESTAMP WITH TIME ZONE
next_execution             TIMESTAMP WITH TIME ZONE
records_processed          BIGINT DEFAULT 0
last_execution_duration_ms INTEGER
last_execution_status      VARCHAR(50)  -- success, failed, partial
created_at                 TIMESTAMP WITH TIME ZONE NOT NULL
updated_at                 TIMESTAMP WITH TIME ZONE NOT NULL
created_by                 UUID
updated_by                 UUID
```

## Indexing Strategy

### Primary Indexes
All tables use UUID primary keys with automatic B-tree indexes.

### Performance Indexes
```sql
-- User lookup optimization
CREATE INDEX idx_users_email ON users(email);

-- Plan query optimization
CREATE INDEX idx_plan_user_status ON plans(user_id, status);
CREATE INDEX idx_plan_last_run ON plans(last_run_at);
CREATE INDEX idx_plan_random_seed ON plans(random_seed);

-- Input/Output optimization
CREATE INDEX idx_plan_input_type ON plan_inputs(plan_id, input_type);
CREATE INDEX idx_plan_output_type ON plan_outputs(plan_id, output_type);

-- Audit log optimization
CREATE INDEX idx_audit_timestamp ON audit_logs(timestamp);
CREATE INDEX idx_audit_user_action ON audit_logs(user_id, action);
CREATE INDEX idx_audit_resource ON audit_logs(resource_type, resource_id);

-- System events optimization
CREATE INDEX idx_system_event_timestamp ON system_events(timestamp);
CREATE INDEX idx_system_event_type ON system_events(event_type, severity);
```

### Composite Indexes
Strategic composite indexes for common query patterns:
```sql
-- Multi-column indexes for complex queries
CREATE INDEX idx_audit_session_time ON audit_logs(session_id, timestamp);
CREATE INDEX idx_plan_input_name ON plan_inputs(plan_id, input_name);
CREATE INDEX idx_cma_effective_date ON capital_market_assumptions(effective_date);
```

## Partitioning Strategy

### Monthly Partitioned Audit Logs
```sql
-- Partitioned table for better performance with large audit datasets
CREATE TABLE audit_logs_partitioned (
    LIKE audit_logs INCLUDING ALL
) PARTITION BY RANGE (timestamp);

-- Monthly partitions
CREATE TABLE audit_logs_2025_08 PARTITION OF audit_logs_partitioned
    FOR VALUES FROM ('2025-08-01') TO ('2025-09-01');
-- Additional partitions created automatically
```

## Reproducibility Features

### Random Seed Management
Every plan stores a `random_seed` that ensures exact reproduction of Monte Carlo simulations:
```sql
-- Example: Reproduce exact simulation results
SELECT random_seed FROM plans WHERE id = 'plan-uuid';
-- Use this seed to reproduce identical simulation results
```

### Version Tracking
- **Plan Versions**: Complete plan hierarchy with parent-child relationships
- **CMA Versions**: Timestamped capital market assumptions with approval workflow
- **Input Versions**: Complete change history with superseded_by relationships

### Complete Input/Output Snapshots
Every execution stores:
- Complete input snapshot in `plan_inputs`
- Full output dataset in `plan_outputs`
- Algorithm versions and computation metadata
- Dependency tracking between inputs and outputs

## Data Retention and Compliance

### Automated Retention Policies
```sql
-- Example policies automatically created
INSERT INTO data_retention_policies VALUES (
    uuid_generate_v4(),
    'Basic Audit Log Retention',
    'audit_logs',
    2555,  -- 7 years
    'archive',
    '0 2 * * 0'  -- Weekly execution
);
```

### Compliance Features
- **GDPR**: User data anonymization and deletion capabilities
- **SOX**: Complete audit trail with tamper-proof logging
- **Industry Standards**: 7-year retention for financial data

## Backup and Recovery

### Automated Backup Strategy
- **Full Backups**: Daily with compression and verification
- **Incremental Backups**: Every 6 hours using WAL archiving
- **Retention**: 30 days local, 1 year offsite
- **Verification**: Every backup automatically tested

### Recovery Procedures
```bash
# Full database restore
python3 scripts/backup.py restore --backup-file latest_backup.sql.gz

# Point-in-time recovery using WAL files
python3 scripts/backup.py restore --backup-file base_backup.sql.gz --wal-files wal_archive/

# Selective table restore
python3 scripts/backup.py restore --backup-file backup.sql.gz --tables plans,plan_inputs
```

## Performance Monitoring

### Real-time Metrics
- Connection pool utilization
- Query execution times
- Cache hit ratios
- Lock statistics
- Replication lag (if applicable)

### Automated Alerting
- Slow query detection (>1000ms)
- High connection usage (>80%)
- Failed backup alerts
- Disk space warnings (>90%)

### Query Optimization
```bash
# Analyze slow queries
python3 scripts/database_maintenance.py analyze

# Generate index suggestions
python3 -c "
from app.database.performance import query_optimizer
import asyncio
asyncio.run(query_optimizer.suggest_indexes())
"
```

## Operational Procedures

### Daily Operations
```bash
# Health check
python3 scripts/database_maintenance.py health

# Backup verification
python3 scripts/backup.py list

# Performance monitoring
python3 scripts/database_maintenance.py analyze
```

### Weekly Maintenance
```bash
# VACUUM ANALYZE all tables
python3 scripts/database_maintenance.py vacuum

# Update table statistics
python3 scripts/database_maintenance.py statistics

# Disaster recovery test
python3 scripts/backup.py test-dr
```

### Monthly Tasks
```bash
# REINDEX all indexes
python3 scripts/database_maintenance.py reindex

# Comprehensive maintenance report
python3 scripts/database_maintenance.py report

# Data cleanup
python3 scripts/database_maintenance.py cleanup
```

## Security Features

### Authentication and Authorization
- Bcrypt password hashing
- Session management with timeout
- Failed login attempt tracking
- Account locking mechanisms

### Audit Trail
- Every action logged with full context
- IP address and user agent tracking
- Request ID correlation
- Change tracking with before/after values

### Data Protection
- UUID primary keys (non-enumerable)
- Sensitive data encryption options
- Secure backup with encryption support
- Network security with SSL/TLS

## Integration Points

### Application Integration
```python
from app.database import initialize_database_system

# Initialize all database components
await initialize_database_system()
```

### FastAPI Integration
```python
from app.database import get_database_session

@app.get("/api/v1/plans")
async def get_plans(session: AsyncSession = Depends(get_database_session)):
    # Database operations with automatic audit logging
    pass
```

### Audit Logging Integration
```python
from app.database.audit import audit_logger, AuditAction

# Automatic audit logging
await audit_logger.log_audit(
    action=AuditAction.CREATE,
    resource_type="plan",
    resource_id=plan.id,
    new_values=plan_data
)
```

## Troubleshooting

### Common Issues

#### Connection Pool Exhaustion
```bash
# Check pool status
python3 -c "
import asyncio
from app.database.utils import db_manager
asyncio.run(db_manager.health_check())
"

# Solution: Increase pool size in configuration
```

#### Slow Queries
```bash
# Identify slow queries
python3 scripts/database_maintenance.py analyze

# Suggest optimizations
python3 -c "
from app.database.performance import query_optimizer
import asyncio
asyncio.run(query_optimizer.analyze_slow_queries())
"
```

#### Disk Space Issues
```bash
# Check table sizes
python3 -c "
import asyncio
from app.database.retention import retention_manager
asyncio.run(retention_manager.get_retention_status())
"

# Clean up old data
python3 scripts/database_maintenance.py cleanup
```

### Emergency Procedures
See the [Disaster Recovery Runbook](./disaster_recovery_runbook.md) for complete emergency procedures.

## Future Enhancements

### Planned Features
1. **Read Replicas**: For improved read performance
2. **Connection Pooling**: Advanced pooling with PgBouncer
3. **Automated Scaling**: Dynamic resource allocation
4. **Advanced Monitoring**: Integration with Prometheus/Grafana
5. **ML-based Optimization**: Intelligent query optimization

### Scalability Considerations
- Horizontal partitioning for large datasets
- Automated partition management
- Connection pooling optimization
- Query result caching

---

## Contact Information

**Database Administrator**: [Your DBA Contact]  
**Development Team**: [Your Dev Team Contact]  
**Operations Team**: [Your Ops Team Contact]

---

**Document Version**: 1.0  
**Last Updated**: 2025-08-21  
**Next Review**: 2025-11-21