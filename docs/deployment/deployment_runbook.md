# Deployment Runbook
## Financial Planning Application

**Document Version:** 1.0  
**Last Updated:** 2025-08-22  
**Owner:** Platform Engineering  
**Classification:** Internal Use Only  

---

## Table of Contents
1. [Prerequisites](#1-prerequisites)
2. [Environment Configurations](#2-environment-configurations)
3. [Secret Management](#3-secret-management)
4. [Database Migration Strategy](#4-database-migration-strategy)
5. [Zero-Downtime Deployment](#5-zero-downtime-deployment)
6. [Health Check Validations](#6-health-check-validations)
7. [Smoke Test Procedures](#7-smoke-test-procedures)
8. [Rollback Procedures](#8-rollback-procedures)
9. [Post-Deployment Tasks](#9-post-deployment-tasks)
10. [Troubleshooting Guide](#10-troubleshooting-guide)

---

## 1. Prerequisites

### 1.1 Required Access and Permissions
```bash
# Verify access to required systems
kubectl auth can-i create deployments --namespace=financial-planning
aws sts get-caller-identity
docker login ghcr.io
helm version
```

### 1.2 Environment Variables
```bash
export DEPLOYMENT_ENV="production"
export CLUSTER_NAME="financial-planning-prod"
export AWS_REGION="us-east-1"
export GITHUB_TOKEN="$GITHUB_TOKEN"
export KUBE_CONFIG="$HOME/.kube/config-prod"
export VAULT_ADDR="https://vault.financial-planning.com"
```

### 1.3 Required Tools Verification
```bash
# Check tool versions
kubectl version --client --short
aws --version
helm version --short
docker version --format '{{.Client.Version}}'
jq --version
yq --version
```

### 1.4 Pre-Deployment Checklist
- [ ] All tests passing in CI/CD pipeline
- [ ] Security scans completed without critical issues
- [ ] Database migration scripts validated in staging
- [ ] Container images built and pushed to registry
- [ ] Configuration files updated and validated
- [ ] SSL certificates valid and not expiring within 30 days
- [ ] DNS records configured and propagated
- [ ] Backup verification completed within last 24 hours

---

## 2. Environment Configurations

### 2.1 Production Environment Setup
```yaml
# production-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: financial-planning-config
  namespace: financial-planning
data:
  # Application Configuration
  APP_ENV: "production"
  APP_DEBUG: "false"
  APP_LOG_LEVEL: "INFO"
  
  # Database Configuration
  DB_POOL_SIZE: "20"
  DB_MAX_OVERFLOW: "40"
  DB_POOL_TIMEOUT: "30"
  DB_POOL_RECYCLE: "3600"
  
  # Redis Configuration
  REDIS_MAX_CONNECTIONS: "100"
  REDIS_TIMEOUT: "5"
  
  # API Configuration
  API_RATE_LIMIT: "1000"
  API_TIMEOUT: "30"
  
  # ML Configuration
  ML_MODEL_PATH: "/app/models"
  ML_BATCH_SIZE: "1000"
  ML_GPU_MEMORY_FRACTION: "0.8"
  
  # Monitoring Configuration
  METRICS_ENABLED: "true"
  TRACING_ENABLED: "true"
  SENTRY_ENABLED: "true"
```

### 2.2 Staging Environment Setup
```yaml
# staging-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: financial-planning-config
  namespace: financial-planning-staging
data:
  APP_ENV: "staging"
  APP_DEBUG: "true"
  APP_LOG_LEVEL: "DEBUG"
  DB_POOL_SIZE: "5"
  DB_MAX_OVERFLOW: "10"
  API_RATE_LIMIT: "100"
  ML_BATCH_SIZE: "100"
```

### 2.3 Development Environment Setup
```yaml
# development-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: financial-planning-config
  namespace: financial-planning-dev
data:
  APP_ENV: "development"
  APP_DEBUG: "true"
  APP_LOG_LEVEL: "DEBUG"
  DB_POOL_SIZE: "2"
  API_RATE_LIMIT: "50"
  ML_BATCH_SIZE: "50"
```

---

## 3. Secret Management

### 3.1 Vault Integration
```bash
# Authenticate with Vault
vault auth -method=aws

# Retrieve database credentials
vault kv get -field=password secret/financial-planning/database/postgres

# Create Kubernetes secrets from Vault
kubectl create secret generic database-credentials \
  --from-literal=POSTGRES_USER="$(vault kv get -field=username secret/financial-planning/database/postgres)" \
  --from-literal=POSTGRES_PASSWORD="$(vault kv get -field=password secret/financial-planning/database/postgres)" \
  --from-literal=POSTGRES_HOST="$(vault kv get -field=host secret/financial-planning/database/postgres)" \
  --namespace=financial-planning
```

### 3.2 AWS Secrets Manager Integration
```bash
# Retrieve secrets from AWS Secrets Manager
aws secretsmanager get-secret-value \
  --secret-id "financial-planning/jwt-secret" \
  --query 'SecretString' --output text

# Create Kubernetes secret
kubectl create secret generic jwt-secret \
  --from-literal=JWT_SECRET="$(aws secretsmanager get-secret-value --secret-id 'financial-planning/jwt-secret' --query 'SecretString' --output text)" \
  --namespace=financial-planning
```

### 3.3 External Secrets Operator
```yaml
apiVersion: external-secrets.io/v1beta1
kind: SecretStore
metadata:
  name: vault-backend
  namespace: financial-planning
spec:
  provider:
    vault:
      server: "https://vault.financial-planning.com"
      path: "secret"
      auth:
        kubernetes:
          mountPath: "kubernetes"
          role: "financial-planning"

---
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: database-credentials
  namespace: financial-planning
spec:
  refreshInterval: 15s
  secretStoreRef:
    name: vault-backend
    kind: SecretStore
  target:
    name: database-credentials
    creationPolicy: Owner
  data:
  - secretKey: POSTGRES_USER
    remoteRef:
      key: financial-planning/database/postgres
      property: username
  - secretKey: POSTGRES_PASSWORD
    remoteRef:
      key: financial-planning/database/postgres
      property: password
```

---

## 4. Database Migration Strategy

### 4.1 Pre-Migration Validation
```bash
# Create database backup before migration
kubectl exec -it postgres-primary-0 -n financial-planning -- \
  pg_dump -U postgres -h localhost financial_planning > backup_pre_migration.sql

# Validate migration scripts
alembic check
alembic history --verbose
alembic show head
```

### 4.2 Migration Execution
```bash
# Create migration job
cat <<EOF | kubectl apply -f -
apiVersion: batch/v1
kind: Job
metadata:
  name: database-migration-$(date +%Y%m%d%H%M%S)
  namespace: financial-planning
spec:
  template:
    spec:
      containers:
      - name: migration
        image: ghcr.io/financial-planning/backend:latest
        command: ["alembic", "upgrade", "head"]
        envFrom:
        - secretRef:
            name: database-credentials
        - configMapRef:
            name: financial-planning-config
      restartPolicy: Never
  backoffLimit: 2
EOF

# Monitor migration progress
kubectl logs -f job/database-migration-$(date +%Y%m%d%H%M%S) -n financial-planning
```

### 4.3 Migration Rollback
```bash
# Rollback to previous migration
kubectl create job --from=cronjob/database-migration migration-rollback-$(date +%Y%m%d%H%M%S)
kubectl exec -it migration-rollback-$(date +%Y%m%d%H%M%S) -- alembic downgrade -1

# Restore from backup if needed
kubectl exec -it postgres-primary-0 -n financial-planning -- \
  psql -U postgres -h localhost financial_planning < backup_pre_migration.sql
```

---

## 5. Zero-Downtime Deployment

### 5.1 Blue-Green Deployment Process
```bash
# Step 1: Deploy green environment
helm upgrade financial-planning-green ./helm/financial-planning \
  --namespace=financial-planning \
  --set image.tag="$NEW_VERSION" \
  --set environment=production \
  --set deployment.color=green \
  --wait --timeout=600s

# Step 2: Verify green environment health
kubectl get pods -l app=financial-planning,version=green -n financial-planning
kubectl exec -it deployment/financial-planning-green -- curl -f http://localhost:8000/health

# Step 3: Update service selector to point to green
kubectl patch service financial-planning-api \
  --patch '{"spec":{"selector":{"version":"green"}}}' \
  -n financial-planning

# Step 4: Monitor for 5 minutes
sleep 300

# Step 5: Scale down blue environment
kubectl scale deployment financial-planning-blue --replicas=0 -n financial-planning
```

### 5.2 Canary Deployment Process
```bash
# Step 1: Deploy canary with 10% traffic
kubectl apply -f - <<EOF
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: financial-planning-api
  namespace: financial-planning
spec:
  replicas: 10
  strategy:
    canary:
      steps:
      - setWeight: 10
      - pause: {duration: 5m}
      - setWeight: 30
      - pause: {duration: 5m}
      - setWeight: 50
      - pause: {duration: 5m}
      - setWeight: 100
      canaryService: financial-planning-api-canary
      stableService: financial-planning-api-stable
      trafficRouting:
        istio:
          virtualService:
            name: financial-planning-api-vs
  selector:
    matchLabels:
      app: financial-planning-api
  template:
    metadata:
      labels:
        app: financial-planning-api
    spec:
      containers:
      - name: api
        image: ghcr.io/financial-planning/backend:$NEW_VERSION
EOF

# Step 2: Monitor canary metrics
kubectl argo rollouts get rollout financial-planning-api -n financial-planning --watch

# Step 3: Promote or rollback based on metrics
# Promote if metrics are good
kubectl argo rollouts promote financial-planning-api -n financial-planning

# Rollback if issues detected
kubectl argo rollouts abort financial-planning-api -n financial-planning
```

### 5.3 Rolling Deployment Process
```bash
# Step 1: Update deployment with rolling update strategy
kubectl patch deployment financial-planning-api \
  --patch='{"spec":{"template":{"spec":{"containers":[{"name":"api","image":"ghcr.io/financial-planning/backend:'$NEW_VERSION'"}]}}}}' \
  -n financial-planning

# Step 2: Monitor rollout progress
kubectl rollout status deployment/financial-planning-api -n financial-planning --timeout=600s

# Step 3: Verify deployment
kubectl get pods -l app=financial-planning-api -n financial-planning
kubectl logs -l app=financial-planning-api -n financial-planning --tail=100
```

---

## 6. Health Check Validations

### 6.1 Basic Health Checks
```bash
# Application health check
curl -f https://api.financial-planning.com/health

# Database connectivity
kubectl exec -it deployment/financial-planning-api -n financial-planning -- \
  python -c "
import psycopg2
import os
conn = psycopg2.connect(
    host=os.environ['POSTGRES_HOST'],
    user=os.environ['POSTGRES_USER'],
    password=os.environ['POSTGRES_PASSWORD'],
    database='financial_planning'
)
print('Database connection: OK')
conn.close()
"

# Redis connectivity
kubectl exec -it deployment/financial-planning-api -n financial-planning -- \
  redis-cli -h redis ping
```

### 6.2 Deep Health Checks
```bash
# API endpoint validation
curl -X POST https://api.financial-planning.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"testpass"}'

# ML service validation
curl -X POST https://api.financial-planning.com/api/v1/ml/health-check \
  -H "Authorization: Bearer $TEST_TOKEN"

# Banking service validation
curl -X GET https://api.financial-planning.com/api/v1/banking/health \
  -H "Authorization: Bearer $TEST_TOKEN"
```

### 6.3 Load Balancer Health Checks
```bash
# Check load balancer target health
aws elbv2 describe-target-health \
  --target-group-arn "arn:aws:elasticloadbalancing:us-east-1:123456789012:targetgroup/financial-planning-api/1234567890123456"

# Verify all targets are healthy
aws elbv2 describe-target-health \
  --target-group-arn "arn:aws:elasticloadbalancing:us-east-1:123456789012:targetgroup/financial-planning-api/1234567890123456" \
  --query 'TargetHealthDescriptions[?TargetHealth.State!=`healthy`]'
```

---

## 7. Smoke Test Procedures

### 7.1 Automated Smoke Tests
```bash
# Run comprehensive smoke test suite
kubectl create job --from=cronjob/smoke-tests smoke-test-$(date +%Y%m%d%H%M%S) -n financial-planning

# Monitor test execution
kubectl logs -f job/smoke-test-$(date +%Y%m%d%H%M%S) -n financial-planning

# Check test results
kubectl get job smoke-test-$(date +%Y%m%d%H%M%S) -n financial-planning -o jsonpath='{.status.conditions[0].type}'
```

### 7.2 Critical Path Testing
```bash
#!/bin/bash
# critical-path-test.sh

set -e

BASE_URL="https://api.financial-planning.com"
TEST_EMAIL="smoketest@example.com"
TEST_PASSWORD="SmokeTest123!"

echo "Starting critical path smoke tests..."

# Test 1: User Registration
echo "Testing user registration..."
REGISTER_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$TEST_EMAIL\",\"password\":\"$TEST_PASSWORD\",\"full_name\":\"Smoke Test User\"}")

if [[ $(echo $REGISTER_RESPONSE | jq -r '.status') != "success" ]]; then
  echo "FAIL: User registration failed"
  exit 1
fi
echo "PASS: User registration successful"

# Test 2: User Login
echo "Testing user login..."
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$TEST_EMAIL\",\"password\":\"$TEST_PASSWORD\"}")

TOKEN=$(echo $LOGIN_RESPONSE | jq -r '.access_token')
if [[ "$TOKEN" == "null" ]]; then
  echo "FAIL: User login failed"
  exit 1
fi
echo "PASS: User login successful"

# Test 3: Financial Profile Creation
echo "Testing financial profile creation..."
PROFILE_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/financial-profiles" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "age": 30,
    "annual_income": 75000,
    "current_savings": 25000,
    "risk_tolerance": "moderate"
  }')

PROFILE_ID=$(echo $PROFILE_RESPONSE | jq -r '.id')
if [[ "$PROFILE_ID" == "null" ]]; then
  echo "FAIL: Financial profile creation failed"
  exit 1
fi
echo "PASS: Financial profile creation successful"

# Test 4: Monte Carlo Simulation
echo "Testing Monte Carlo simulation..."
SIMULATION_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/simulations/monte-carlo" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "profile_id": "'$PROFILE_ID'",
    "goal_amount": 500000,
    "years_to_goal": 20,
    "monthly_contribution": 2000
  }')

SIMULATION_ID=$(echo $SIMULATION_RESPONSE | jq -r '.simulation_id')
if [[ "$SIMULATION_ID" == "null" ]]; then
  echo "FAIL: Monte Carlo simulation failed"
  exit 1
fi
echo "PASS: Monte Carlo simulation successful"

# Test 5: PDF Export
echo "Testing PDF export..."
PDF_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/export/pdf" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "simulation_id": "'$SIMULATION_ID'",
    "template": "detailed_plan"
  }')

EXPORT_URL=$(echo $PDF_RESPONSE | jq -r '.download_url')
if [[ "$EXPORT_URL" == "null" ]]; then
  echo "FAIL: PDF export failed"
  exit 1
fi
echo "PASS: PDF export successful"

echo "All critical path tests passed successfully!"
```

### 7.3 Performance Validation
```bash
# Load testing with hey
hey -n 1000 -c 10 -H "Authorization: Bearer $TEST_TOKEN" \
  https://api.financial-planning.com/api/v1/health

# Response time validation
RESPONSE_TIME=$(curl -o /dev/null -s -w '%{time_total}' \
  https://api.financial-planning.com/api/v1/health)

if (( $(echo "$RESPONSE_TIME > 0.5" | bc -l) )); then
  echo "WARNING: API response time is $RESPONSE_TIME seconds (>0.5s threshold)"
fi
```

---

## 8. Rollback Procedures

### 8.1 Application Rollback
```bash
# Immediate rollback using Helm
helm rollback financial-planning 0 --namespace=financial-planning

# Rollback using kubectl
kubectl rollout undo deployment/financial-planning-api -n financial-planning

# Verify rollback
kubectl rollout status deployment/financial-planning-api -n financial-planning
kubectl get pods -l app=financial-planning-api -n financial-planning
```

### 8.2 Database Rollback
```bash
# Schema rollback using Alembic
kubectl exec -it deployment/financial-planning-api -n financial-planning -- \
  alembic downgrade -1

# Data rollback from backup
kubectl exec -it postgres-primary-0 -n financial-planning -- \
  psql -U postgres financial_planning < backup_pre_deployment.sql
```

### 8.3 Configuration Rollback
```bash
# Rollback ConfigMap
kubectl rollout undo configmap/financial-planning-config -n financial-planning

# Rollback Secrets
kubectl delete secret database-credentials -n financial-planning
kubectl apply -f secrets-backup.yaml
```

### 8.4 Automated Rollback Triggers
```yaml
apiVersion: argoproj.io/v1alpha1
kind: AnalysisTemplate
metadata:
  name: success-rate
spec:
  metrics:
  - name: success-rate
    interval: 60s
    count: 5
    successCondition: result[0] >= 0.95
    failureLimit: 3
    provider:
      prometheus:
        address: http://prometheus.monitoring.svc.cluster.local:9090
        query: |
          sum(rate(http_requests_total{job="financial-planning-api",code!~"5.."}[5m])) /
          sum(rate(http_requests_total{job="financial-planning-api"}[5m]))
```

---

## 9. Post-Deployment Tasks

### 9.1 Monitoring Verification
```bash
# Verify metrics collection
curl -s http://prometheus.financial-planning.com/api/v1/targets | \
  jq '.data.activeTargets[] | select(.labels.job=="financial-planning-api") | .health'

# Check log aggregation
curl -X GET "http://elasticsearch.financial-planning.com:9200/logstash-*/_search" \
  -H 'Content-Type: application/json' \
  -d '{"query":{"term":{"service.name":"financial-planning-api"}},"size":10}'

# Verify alerting
curl -X GET "http://alertmanager.financial-planning.com/api/v1/alerts"
```

### 9.2 Performance Baseline Update
```bash
# Update performance baselines in monitoring
kubectl apply -f - <<EOF
apiVersion: v1
kind: ConfigMap
metadata:
  name: performance-baselines
  namespace: monitoring
data:
  api_response_time_p95: "500ms"
  api_error_rate_threshold: "0.1"
  database_connection_pool_usage: "80"
  memory_usage_threshold: "85"
EOF
```

### 9.3 Documentation Updates
```bash
# Update deployment history
echo "$(date): Deployed version $NEW_VERSION to production" >> deployment-history.log

# Update configuration documentation
kubectl get configmap financial-planning-config -n financial-planning -o yaml > docs/current-config.yaml

# Generate deployment report
cat > deployment-report.md <<EOF
# Deployment Report - $(date)

## Deployment Details
- **Version:** $NEW_VERSION
- **Deployment Method:** Blue-Green
- **Duration:** $(($DEPLOYMENT_END - $DEPLOYMENT_START)) seconds
- **Issues:** None

## Validation Results
- Health checks: PASS
- Smoke tests: PASS
- Performance tests: PASS
- Security validation: PASS

## Post-Deployment Metrics
- API Response Time: $(curl -o /dev/null -s -w '%{time_total}' https://api.financial-planning.com/health)s
- Error Rate: 0.0%
- Memory Usage: 45%
- CPU Usage: 35%
EOF
```

---

## 10. Troubleshooting Guide

### 10.1 Common Issues and Solutions

#### Issue: Pods stuck in CrashLoopBackOff
```bash
# Diagnose the issue
kubectl describe pod <pod-name> -n financial-planning
kubectl logs <pod-name> -n financial-planning --previous

# Common fixes
# 1. Check resource limits
kubectl get pods -n financial-planning -o yaml | grep -A 5 -B 5 "resources:"

# 2. Check secrets and configmaps
kubectl get secrets,configmaps -n financial-planning

# 3. Check node resources
kubectl top nodes
kubectl describe nodes
```

#### Issue: Database connection failures
```bash
# Check database pod status
kubectl get pods -l app=postgres -n financial-planning

# Test database connectivity
kubectl exec -it postgres-primary-0 -n financial-planning -- pg_isready

# Check database logs
kubectl logs postgres-primary-0 -n financial-planning --tail=100

# Verify secrets
kubectl get secret database-credentials -n financial-planning -o yaml | base64 -d
```

#### Issue: High memory usage
```bash
# Check memory metrics
kubectl top pods -n financial-planning --sort-by=memory

# Check for memory leaks
kubectl exec -it deployment/financial-planning-api -n financial-planning -- \
  python -c "
import psutil
import gc
gc.collect()
process = psutil.Process()
print(f'Memory usage: {process.memory_info().rss / 1024 / 1024:.2f} MB')
"

# Restart problematic pods
kubectl delete pod -l app=financial-planning-api -n financial-planning
```

### 10.2 Emergency Procedures

#### Complete System Outage
```bash
# 1. Switch to DR environment
kubectl config use-context disaster-recovery
kubectl get services -n financial-planning

# 2. Update DNS to point to DR
aws route53 change-resource-record-sets \
  --hosted-zone-id Z123456789 \
  --change-batch file://failover-dns-change.json

# 3. Notify stakeholders
curl -X POST https://hooks.slack.com/emergency \
  -d '{"text":"CRITICAL: Production system down, failover to DR initiated"}'
```

#### Security Incident
```bash
# 1. Isolate affected components
kubectl patch deployment financial-planning-api \
  --patch '{"spec":{"replicas":0}}' -n financial-planning

# 2. Block suspicious traffic
kubectl apply -f emergency-network-policy.yaml

# 3. Collect forensic data
kubectl get events --all-namespaces --sort-by=.metadata.creationTimestamp
kubectl logs -l app=financial-planning-api -n financial-planning --since=1h > security-incident-logs.txt
```

### 10.3 Contact Information

#### Escalation Matrix
| Severity | Contact | Response Time | Method |
|----------|---------|---------------|---------|
| P0 - Critical | On-call Engineer | 15 minutes | PagerDuty + Phone |
| P1 - High | Team Lead | 1 hour | Slack + Email |
| P2 - Medium | Team Member | 4 hours | Slack |
| P3 - Low | Team Member | Next business day | Email |

#### Emergency Contacts
- **On-call Engineer:** +1-555-ONCALL (24/7)
- **Platform Team Lead:** +1-555-PLATFORM (24/7)
- **Security Team:** +1-555-SECURITY (24/7)
- **Database Admin:** +1-555-DBA (Business hours)
- **Business Stakeholder:** +1-555-BUSINESS (Business hours)

---

## Appendices

### A. Command Reference
```bash
# Useful kubectl commands
kubectl get pods -n financial-planning -o wide
kubectl describe deployment financial-planning-api -n financial-planning
kubectl logs -f deployment/financial-planning-api -n financial-planning
kubectl exec -it deployment/financial-planning-api -n financial-planning -- /bin/bash
kubectl port-forward service/financial-planning-api 8080:8000 -n financial-planning

# Helm commands
helm list -n financial-planning
helm history financial-planning -n financial-planning
helm get values financial-planning -n financial-planning

# Docker commands
docker images | grep financial-planning
docker run --rm -it ghcr.io/financial-planning/backend:latest /bin/bash
```

### B. Configuration Templates
Located in: `/config-templates/`
- `production-values.yaml`
- `staging-values.yaml` 
- `development-values.yaml`
- `secrets-template.yaml`

### C. Monitoring Queries
Located in: `/monitoring-queries/`
- `prometheus-queries.txt`
- `grafana-dashboard-queries.txt`
- `alert-rules.yaml`

---

**Document Version History:**
- v1.0 - Initial release (2025-08-22)

**Next Review:** 2025-09-22