# Deployment Runbook - Financial Planning System

## Overview

This runbook provides step-by-step procedures for deploying the Financial Planning System across different environments. It includes normal deployment procedures, emergency procedures, rollback instructions, and troubleshooting guides.

## Table of Contents

1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Normal Deployment Procedures](#normal-deployment-procedures)
3. [Emergency Deployment Procedures](#emergency-deployment-procedures)
4. [Rollback Procedures](#rollback-procedures)
5. [Health Checks and Verification](#health-checks-and-verification)
6. [Troubleshooting Guide](#troubleshooting-guide)
7. [Monitoring and Alerting](#monitoring-and-alerting)
8. [Contact Information](#contact-information)

---

## Pre-Deployment Checklist

### General Prerequisites

- [ ] All CI tests passing
- [ ] Security scans completed with no critical issues
- [ ] Database migrations tested and verified
- [ ] Backup verification completed
- [ ] Maintenance window scheduled (if required)
- [ ] Stakeholders notified
- [ ] Rollback plan prepared

### Environment-Specific Prerequisites

#### Development
- [ ] Feature branch merged to develop
- [ ] Integration tests passing
- [ ] Environment available and healthy

#### Staging
- [ ] Code reviewed and approved
- [ ] Load testing completed
- [ ] Performance benchmarks met
- [ ] User acceptance testing completed

#### Production
- [ ] Change approval obtained
- [ ] Production readiness review completed
- [ ] Disaster recovery procedures verified
- [ ] On-call team notified
- [ ] Customer communication sent (if needed)

---

## Normal Deployment Procedures

### Automated Deployment (Recommended)

#### Triggering Deployment

1. **Development Environment**
   ```bash
   # Triggered automatically on push to develop branch
   git push origin develop
   ```

2. **Staging Environment**
   ```bash
   # Manual trigger via GitHub Actions
   gh workflow run cd.yml -f environment=staging
   ```

3. **Production Environment**
   ```bash
   # Manual trigger with approval required
   gh workflow run cd.yml -f environment=production
   ```

#### Monitoring Deployment Progress

1. **Check GitHub Actions**
   - Navigate to Actions tab in GitHub repository
   - Monitor deployment workflow progress
   - Watch for any failed steps

2. **Monitor Application Health**
   ```bash
   # Check application health
   kubectl get pods -n financial-planning-production
   kubectl logs -f deployment/financial-planning -n financial-planning-production
   
   # Check service endpoints
   curl -f https://api.financial-planning.com/health
   ```

3. **Verify Database Migrations**
   ```bash
   # Connect to database and verify schema version
   kubectl exec -it deployment/financial-planning -n financial-planning-production -- \
     python -c "from alembic import command; from alembic.config import Config; \
     config = Config('alembic.ini'); command.current(config)"
   ```

### Manual Deployment (Emergency Use Only)

#### Prerequisites
- kubectl configured for target cluster
- Docker images built and pushed
- Database migrations ready

#### Steps

1. **Update Kubernetes Manifests**
   ```bash
   # Update image tags in deployment manifests
   sed -i 's/image: .*/image: ghcr.io\/financial-planning\/backend:NEW_TAG/' \
     k8s/overlays/production/deployment.yml
   ```

2. **Apply Database Migrations**
   ```bash
   # Create migration job
   kubectl apply -f k8s/jobs/migration-job.yml
   
   # Wait for completion
   kubectl wait --for=condition=complete job/migration-job --timeout=300s
   ```

3. **Deploy Application**
   ```bash
   # Apply new deployment
   kubectl apply -k k8s/overlays/production/
   
   # Wait for rollout to complete
   kubectl rollout status deployment/financial-planning -n financial-planning-production
   ```

4. **Verify Deployment**
   ```bash
   # Check pod status
   kubectl get pods -n financial-planning-production
   
   # Test health endpoints
   kubectl port-forward service/financial-planning 8080:80 -n financial-planning-production &
   curl -f http://localhost:8080/health
   ```

---

## Emergency Deployment Procedures

### Hotfix Deployment

For critical production issues requiring immediate deployment:

1. **Create Hotfix Branch**
   ```bash
   git checkout main
   git pull origin main
   git checkout -b hotfix/critical-fix-description
   ```

2. **Implement and Test Fix**
   ```bash
   # Make necessary changes
   # Run local tests
   npm test  # Frontend
   pytest   # Backend
   ```

3. **Emergency Deployment**
   ```bash
   # Push hotfix
   git push origin hotfix/critical-fix-description
   
   # Trigger emergency deployment
   gh workflow run cd.yml \
     -f environment=production \
     -f skip_tests=false \
     -ref hotfix/critical-fix-description
   ```

4. **Post-Deployment Actions**
   - Monitor application metrics closely
   - Verify fix resolves the issue
   - Create post-incident review
   - Merge hotfix to main and develop branches

### Zero-Downtime Emergency Update

For critical security patches or urgent bug fixes:

1. **Use Blue-Green Deployment**
   ```bash
   # Deploy to green environment
   kubectl patch service financial-planning-active \
     -n financial-planning-production \
     -p '{"spec":{"selector":{"color":"green"}}}'
   ```

2. **Rapid Rollback if Needed**
   ```bash
   # Switch back to blue immediately
   kubectl patch service financial-planning-active \
     -n financial-planning-production \
     -p '{"spec":{"selector":{"color":"blue"}}}'
   ```

---

## Rollback Procedures

### Automated Rollback

The system includes automated rollback triggers:

- **Health Check Failures**: Automatic rollback after 3 consecutive failures
- **Error Rate Threshold**: Rollback when error rate > 5% for 2 minutes
- **Response Time**: Rollback when P95 latency > 2 seconds for 5 minutes

### Manual Rollback

#### Quick Rollback (Last Known Good)

```bash
# Rollback to previous deployment
kubectl rollout undo deployment/financial-planning -n financial-planning-production

# Wait for rollback to complete
kubectl rollout status deployment/financial-planning -n financial-planning-production
```

#### Specific Version Rollback

```bash
# List deployment history
kubectl rollout history deployment/financial-planning -n financial-planning-production

# Rollback to specific revision
kubectl rollout undo deployment/financial-planning \
  --to-revision=REVISION_NUMBER \
  -n financial-planning-production
```

#### Database Rollback

```bash
# CAUTION: Only use if database changes are backward compatible
# Connect to database
kubectl exec -it postgresql-pod -n financial-planning-production -- psql

# Check current migration version
SELECT version_num FROM alembic_version;

# Rollback to specific version (if safe)
kubectl exec -it deployment/financial-planning -n financial-planning-production -- \
  alembic downgrade PREVIOUS_VERSION
```

### Blue-Green Rollback

```bash
# Determine current active color
CURRENT_COLOR=$(kubectl get service financial-planning-active \
  -n financial-planning-production \
  -o jsonpath='{.spec.selector.color}')

# Switch to other color
if [[ "$CURRENT_COLOR" == "blue" ]]; then
  NEW_COLOR="green"
else
  NEW_COLOR="blue"
fi

# Switch traffic
kubectl patch service financial-planning-active \
  -n financial-planning-production \
  -p '{"spec":{"selector":{"color":"'$NEW_COLOR'"}}}'
```

---

## Health Checks and Verification

### Application Health Checks

#### Basic Health Check
```bash
curl -f https://api.financial-planning.com/health
```

#### Detailed Health Check
```bash
curl -s https://api.financial-planning.com/api/v1/health | jq '.'
```

#### Database Connectivity
```bash
curl -s https://api.financial-planning.com/api/v1/health/db
```

#### External Service Connectivity
```bash
curl -s https://api.financial-planning.com/api/v1/health/external
```

### Infrastructure Health Checks

#### Kubernetes Cluster Health
```bash
# Check node status
kubectl get nodes

# Check system pods
kubectl get pods -n kube-system

# Check resource usage
kubectl top nodes
kubectl top pods -n financial-planning-production
```

#### Database Health
```bash
# Check PostgreSQL status
kubectl exec -it postgresql-pod -n financial-planning-production -- \
  pg_isready -h localhost -p 5432

# Check connection pool
kubectl exec -it deployment/financial-planning -n financial-planning-production -- \
  python -c "
from app.database.base import engine
with engine.connect() as conn:
    result = conn.execute('SELECT 1')
    print('Database connection: OK')
"
```

#### Redis Health
```bash
# Check Redis connectivity
kubectl exec -it redis-pod -n financial-planning-production -- \
  redis-cli ping
```

### Performance Verification

#### Load Testing
```bash
# Run basic load test
kubectl run load-test --rm -i --tty --image=loadimpact/k6 -- \
  run --vus 10 --duration 30s - <<EOF
import http from 'k6/http';
export default function () {
  http.get('https://api.financial-planning.com/health');
}
EOF
```

#### Response Time Check
```bash
# Check response times
curl -w "@curl-format.txt" -o /dev/null -s https://api.financial-planning.com/health
```

---

## Troubleshooting Guide

### Common Issues and Solutions

#### 1. Pod Startup Failures

**Symptoms:**
- Pods stuck in `Pending` or `CrashLoopBackOff` state
- Health checks failing

**Diagnosis:**
```bash
# Check pod status
kubectl describe pod POD_NAME -n financial-planning-production

# Check logs
kubectl logs POD_NAME -n financial-planning-production --previous
```

**Solutions:**
- Check resource limits and requests
- Verify environment variables and secrets
- Check node capacity and scheduling
- Review security contexts and policies

#### 2. Database Connection Issues

**Symptoms:**
- Database connection errors in logs
- Health check failures

**Diagnosis:**
```bash
# Check database pod status
kubectl get pods -l app=postgresql -n financial-planning-production

# Test database connectivity
kubectl exec -it deployment/financial-planning -n financial-planning-production -- \
  pg_isready -h postgresql -p 5432
```

**Solutions:**
- Verify database credentials in secrets
- Check network policies
- Review database resource limits
- Check connection pool configuration

#### 3. High Response Times

**Symptoms:**
- P95 latency above thresholds
- Timeout errors

**Diagnosis:**
```bash
# Check resource usage
kubectl top pods -n financial-planning-production

# Check HPA status
kubectl get hpa -n financial-planning-production

# Review application logs for slow queries
kubectl logs deployment/financial-planning -n financial-planning-production | grep -i slow
```

**Solutions:**
- Scale up pods if CPU/memory usage is high
- Review database query performance
- Check external service dependencies
- Optimize application code

#### 4. Certificate Issues

**Symptoms:**
- SSL/TLS errors
- Certificate warnings

**Diagnosis:**
```bash
# Check certificate status
kubectl get certificates -n financial-planning-production

# Check cert-manager logs
kubectl logs -n cert-manager deployment/cert-manager
```

**Solutions:**
- Verify DNS records
- Check Let's Encrypt rate limits
- Review certificate issuer configuration
- Manually renew certificates if needed

### Emergency Contacts

#### Escalation Matrix

| Severity | Initial Contact | Escalation 1 | Escalation 2 |
|----------|----------------|--------------|--------------|
| P0 (Critical) | On-call Engineer | Engineering Manager | CTO |
| P1 (High) | On-call Engineer | Team Lead | Engineering Manager |
| P2 (Medium) | Team Lead | Engineering Manager | - |
| P3 (Low) | Team Lead | - | - |

#### Contact Information

- **On-call Engineer**: Check PagerDuty rotation
- **Team Lead**: team-lead@financial-planning.com
- **Engineering Manager**: eng-manager@financial-planning.com
- **DevOps Team**: devops@financial-planning.com
- **Security Team**: security@financial-planning.com

---

## Monitoring and Alerting

### Key Metrics to Monitor

#### Application Metrics
- Response time (P50, P95, P99)
- Error rate
- Throughput (requests per second)
- Active user sessions

#### Infrastructure Metrics
- CPU utilization
- Memory usage
- Disk space
- Network I/O

#### Business Metrics
- User signups
- Financial calculations performed
- PDF exports generated
- API usage by feature

### Alert Thresholds

#### Critical Alerts (P0)
- Service completely down (all health checks failing)
- Database connection failures
- Error rate > 10% for 2 minutes
- P99 response time > 10 seconds

#### High Priority Alerts (P1)
- Error rate > 5% for 5 minutes
- P95 response time > 2 seconds for 5 minutes
- Memory usage > 90% for 10 minutes
- Disk space > 85%

#### Medium Priority Alerts (P2)
- Error rate > 2% for 10 minutes
- P95 response time > 1 second for 10 minutes
- CPU usage > 80% for 15 minutes

### Monitoring Tools

- **Application Monitoring**: Sentry, DataDog APM
- **Infrastructure Monitoring**: Prometheus + Grafana
- **Log Aggregation**: ELK Stack (Elasticsearch, Logstash, Kibana)
- **Uptime Monitoring**: Pingdom, StatusCake
- **Business Intelligence**: Custom dashboards

### Useful Monitoring Queries

#### Prometheus Queries
```promql
# Error rate
rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m])

# Response time P95
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Memory usage
container_memory_usage_bytes / container_spec_memory_limit_bytes * 100

# Pod restart count
increase(kube_pod_container_status_restarts_total[1h])
```

---

## Post-Deployment Checklist

### Immediate (0-15 minutes)
- [ ] Health checks passing
- [ ] Error rates within normal range
- [ ] Response times acceptable
- [ ] No critical alerts triggered

### Short-term (15-60 minutes)
- [ ] User acceptance testing (if applicable)
- [ ] Performance metrics stable
- [ ] Business metrics trending normally
- [ ] No customer complaints

### Long-term (1-24 hours)
- [ ] Resource utilization stable
- [ ] No memory leaks detected
- [ ] Database performance normal
- [ ] All integrations functioning

### Cleanup Tasks
- [ ] Remove old deployment artifacts
- [ ] Update deployment documentation
- [ ] Schedule post-deployment review
- [ ] Communicate success to stakeholders

---

## Disaster Recovery Procedures

### Data Center Failure

1. **Assess Impact**
   - Determine scope of failure
   - Check backup systems status
   - Evaluate recovery options

2. **Activate DR Site**
   ```bash
   # Switch DNS to DR region
   # Update load balancer configuration
   # Restore from latest backup
   ```

3. **Verify Recovery**
   - Test all critical functions
   - Verify data integrity
   - Monitor performance

### Database Disaster Recovery

1. **Point-in-Time Recovery**
   ```bash
   # Restore from automated backup
   aws rds restore-db-instance-to-point-in-time \
     --source-db-instance-identifier financial-planning-prod \
     --target-db-instance-identifier financial-planning-recovery \
     --restore-time 2024-01-01T12:00:00Z
   ```

2. **Cross-Region Failover**
   ```bash
   # Promote read replica to primary
   aws rds promote-read-replica \
     --db-instance-identifier financial-planning-replica-east
   ```

### Complete System Recovery

1. **Infrastructure Recovery**
   ```bash
   # Deploy infrastructure from Terraform
   cd terraform/environments/production
   terraform plan -out=recovery.tfplan
   terraform apply recovery.tfplan
   ```

2. **Application Recovery**
   ```bash
   # Deploy application stack
   kubectl apply -k k8s/overlays/production/
   
   # Restore data from backups
   kubectl apply -f k8s/jobs/data-restore-job.yml
   ```

---

*This runbook should be reviewed and updated quarterly or after any significant infrastructure changes. Last updated: [Current Date]*