# Disaster Recovery Runbook
## Financial Planning System Database

### Emergency Contacts
- **Database Administrator**: [Your DBA Contact]
- **System Administrator**: [Your SysAdmin Contact]  
- **Development Team Lead**: [Your Dev Lead Contact]
- **Business Continuity**: [Your BC Contact]

---

## Recovery Time Objectives (RTO) and Recovery Point Objectives (RPO)

| Scenario | RTO | RPO | Priority |
|----------|-----|-----|----------|
| Database Corruption | 4 hours | 1 hour | Critical |
| Hardware Failure | 2 hours | 30 minutes | Critical |
| Data Center Outage | 8 hours | 1 hour | High |
| Ransomware/Security Breach | 24 hours | 4 hours | Critical |
| User Error/Accidental Deletion | 1 hour | 15 minutes | Medium |

---

## Pre-Disaster Preparation Checklist

### Daily Tasks (Automated)
- [ ] Full database backup created and verified
- [ ] Incremental backups every 6 hours
- [ ] Backup integrity verification completed
- [ ] Offsite backup synchronization
- [ ] Monitoring alerts functioning

### Weekly Tasks
- [ ] Disaster recovery test performed
- [ ] Backup restoration test completed
- [ ] Update emergency contact information
- [ ] Review and update runbook procedures
- [ ] Check backup retention compliance

### Monthly Tasks
- [ ] Full disaster recovery drill
- [ ] Review RTO/RPO targets
- [ ] Update disaster recovery documentation
- [ ] Verify backup storage capacity
- [ ] Test failover procedures

---

## Emergency Response Procedures

### 1. Initial Assessment (0-15 minutes)

#### Immediate Actions
1. **STOP** - Do not make changes until assessment is complete
2. **Assess the situation**:
   ```bash
   # Check database connectivity
   python3 scripts/database_maintenance.py health --output-json
   
   # Check system resources
   df -h
   free -m
   ps aux | grep postgres
   ```

3. **Determine impact level**:
   - **Level 1 (Critical)**: Complete system unavailable
   - **Level 2 (High)**: Degraded performance, some features unavailable  
   - **Level 3 (Medium)**: Minor issues, system mostly functional

4. **Notify stakeholders** based on impact level

#### Decision Matrix
| Symptoms | Likely Cause | Response Level |
|----------|--------------|----------------|
| Database won't start | Corruption/Hardware | Level 1 |
| Slow queries, timeouts | Performance/Resource | Level 2 |
| Specific table issues | Data corruption | Level 2 |
| Connection refused | Network/Config | Level 2 |
| Disk space full | Storage exhaustion | Level 1 |

### 2. Database Corruption Recovery

#### Symptoms
- Database fails to start
- Corruption errors in logs
- Data integrity check failures

#### Recovery Steps
```bash
# 1. Stop the application
systemctl stop financial-planning-app

# 2. Stop PostgreSQL
systemctl stop postgresql

# 3. Check disk space and system resources
df -h
free -m

# 4. Attempt PostgreSQL repair
sudo -u postgres pg_resetwal /var/lib/postgresql/data

# 5. If repair fails, restore from backup
python3 scripts/backup.py restore --backup-file /var/backups/financial_planning/latest_backup.sql.gz

# 6. Verify restoration
python3 scripts/database_maintenance.py health

# 7. Start services
systemctl start postgresql
systemctl start financial-planning-app
```

### 3. Hardware Failure Recovery

#### Symptoms
- Server unresponsive
- Hardware error messages
- Disk failures

#### Recovery Steps
```bash
# 1. Provision new server/VM
# 2. Install PostgreSQL and dependencies
apt update && apt install postgresql-14 postgresql-contrib

# 3. Configure PostgreSQL
# Copy configuration from backup:
# - postgresql.conf
# - pg_hba.conf

# 4. Restore database from latest backup
python3 scripts/backup.py restore --backup-file /offsite/backups/latest_full_backup.sql.gz

# 5. Update DNS/Load balancer to point to new server

# 6. Verify application connectivity
python3 scripts/database_maintenance.py health
```

### 4. Data Center Outage Recovery

#### Prerequisites
- Offsite backup location accessible
- Secondary data center or cloud resources available
- Network connectivity to backup site

#### Recovery Steps
```bash
# 1. Activate secondary site
# 2. Provision database server at secondary location

# 3. Restore from offsite backup
scp backup-server:/offsite/backups/latest_backup.sql.gz ./
python3 scripts/backup.py restore --backup-file latest_backup.sql.gz

# 4. Update application configuration
# Edit config files to point to new database server

# 5. Update DNS records
# Point financial-planning.company.com to secondary site

# 6. Test application functionality
curl -f https://financial-planning.company.com/api/v1/health
```

### 5. Security Incident Recovery

#### Symptoms
- Ransomware detected
- Unauthorized access
- Data exfiltration suspected

#### Immediate Response
```bash
# 1. ISOLATE - Disconnect from network immediately
iptables -P INPUT DROP
iptables -P FORWARD DROP
iptables -P OUTPUT DROP

# 2. PRESERVE - Create forensic snapshot
dd if=/dev/sda of=/external/forensic_image.dd bs=4M

# 3. ASSESS - Check for data encryption/damage
python3 scripts/database_maintenance.py health --output-json

# 4. RESTORE - From clean backup (older than incident)
python3 scripts/backup.py list --output-json
python3 scripts/backup.py restore --backup-file /backups/pre_incident_backup.sql.gz
```

### 6. Accidental Data Deletion Recovery

#### For Recent Deletions (< 24 hours)
```bash
# 1. Check audit logs for deletion details
python3 -c "
from app.database.audit import AuditQueryBuilder, audit_logger
from datetime import datetime, timedelta
import asyncio

async def find_deletions():
    async for session in db_manager.get_session():
        query = AuditQueryBuilder(session)
        deletions = await query.filter_by_action('DELETE')
                                .filter_by_date_range(
                                    datetime.now() - timedelta(hours=24),
                                    datetime.now()
                                ).execute()
        for deletion in deletions:
            print(f'Deleted: {deletion}')

asyncio.run(find_deletions())
"

# 2. If data is still in recent backup, perform selective restore
# Create temporary database
createdb financial_planning_temp

# Restore backup to temp database
python3 scripts/backup.py restore --backup-file latest_backup.sql.gz --target-db financial_planning_temp

# Export specific data
pg_dump -t specific_table financial_planning_temp > recovered_data.sql

# Import to production
psql financial_planning < recovered_data.sql
```

---

## Backup and Restore Procedures

### Creating Backups
```bash
# Full backup (automated daily)
python3 scripts/backup.py full --output-json

# Incremental backup (automated every 6 hours)
python3 scripts/backup.py incremental --base-backup BACKUP_ID

# Manual backup before maintenance
python3 scripts/backup.py full --no-cleanup
```

### Restoring Backups
```bash
# List available backups
python3 scripts/backup.py list

# Test restore (dry run)
python3 scripts/backup.py restore --backup-file BACKUP_FILE --dry-run

# Full restore
python3 scripts/backup.py restore --backup-file BACKUP_FILE

# Restore to different database
python3 scripts/backup.py restore --backup-file BACKUP_FILE --target-db recovery_db
```

### Backup Verification
```bash
# Verify specific backup
python3 -c "
import asyncio
from app.database.utils import backup_manager

async def verify():
    result = await backup_manager.verify_backup('/path/to/backup.sql.gz')
    print(f'Backup valid: {result[\"valid\"]}')
    if not result['valid']:
        print(f'Error: {result[\"error\"]}')

asyncio.run(verify())
"
```

---

## Post-Recovery Procedures

### 1. System Verification Checklist
- [ ] Database connectivity restored
- [ ] Application health check passes
- [ ] All critical tables accessible
- [ ] Audit logging functioning
- [ ] Performance monitoring active
- [ ] Backup system operational

### 2. Data Integrity Verification
```bash
# Run comprehensive health check
python3 scripts/database_maintenance.py health --output-json

# Verify data consistency
python3 scripts/database_maintenance.py analyze --output-json

# Check for orphaned records
python3 -c "
import asyncio
from app.database.retention import retention_manager

async def check_integrity():
    result = await retention_manager.cleanup_orphaned_data()
    print(f'Orphaned records found: {sum(result.values())}')

asyncio.run(check_integrity())
"
```

### 3. Performance Validation
```bash
# Update table statistics
python3 scripts/database_maintenance.py statistics

# Run performance analysis
python3 scripts/database_maintenance.py analyze

# Monitor for 24 hours
python3 -c "
import asyncio
from app.database.performance import performance_monitor

async def monitor():
    await performance_monitor.start_monitoring(interval_seconds=300)
    # Let it run for monitoring

asyncio.run(monitor())
"
```

### 4. Communication and Documentation
- [ ] Notify stakeholders of recovery completion
- [ ] Update incident tracking system
- [ ] Document lessons learned
- [ ] Update runbook if needed
- [ ] Schedule post-incident review meeting

---

## Testing and Validation

### Monthly Disaster Recovery Test
```bash
#!/bin/bash
# monthly_dr_test.sh

echo "Starting monthly DR test..."

# 1. Test backup restoration
python3 scripts/backup.py test-dr --output-json > dr_test_results.json

# 2. Verify test results
if [ $? -eq 0 ]; then
    echo "✅ DR test passed"
else
    echo "❌ DR test failed"
    exit 1
fi

# 3. Test application connectivity
curl -f http://localhost:8000/api/v1/health

# 4. Run data integrity checks
python3 scripts/database_maintenance.py health --output-json

echo "Monthly DR test completed successfully"
```

### Automated Monitoring Alerts

#### Critical Alerts (Immediate Response)
- Database unavailable
- Backup failure
- Disk space > 90%
- Replication lag > 1 hour

#### Warning Alerts (Response within 4 hours)
- Slow query detected
- Connection pool utilization > 80%
- Failed login attempts > threshold

#### Information Alerts (Daily Review)
- Backup completed successfully
- Maintenance tasks completed
- Performance metrics summary

---

## Contact Information and Escalation

### Escalation Matrix
| Time | Contact Level | Response Type |
|------|---------------|---------------|
| 0-15 min | On-call DBA | Immediate response |
| 15-30 min | Senior DBA + Dev Lead | Conference call |
| 30-60 min | IT Director + Business Lead | Management briefing |
| 1+ hours | Executive team | Executive decision |

### Emergency Procedures
1. **Call**: Primary on-call DBA
2. **If no response**: Call secondary DBA
3. **Page**: Development team lead
4. **Escalate**: After 30 minutes, involve management

### Documentation Updates
- Update this runbook after each incident
- Quarterly review and validation
- Annual comprehensive review

---

## Quick Reference Commands

```bash
# Emergency stop
systemctl stop financial-planning-app
systemctl stop postgresql

# Emergency start
systemctl start postgresql
systemctl start financial-planning-app

# Check database status
systemctl status postgresql
python3 scripts/database_maintenance.py health

# Create emergency backup
python3 scripts/backup.py full --output-json

# Restore from backup
python3 scripts/backup.py restore --backup-file BACKUP_FILE

# Check disk space
df -h

# Check memory
free -m

# Check processes
ps aux | grep postgres

# View logs
tail -f /var/log/postgresql/postgresql.log
tail -f /var/log/financial_planning/app.log
```

---

**Document Version**: 1.0  
**Last Updated**: 2025-08-21  
**Next Review**: 2025-11-21  
**Owner**: Database Operations Team