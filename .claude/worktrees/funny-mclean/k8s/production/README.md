# Financial Planning API - Production Kubernetes Configuration

This directory contains production-ready Kubernetes manifests for deploying the Financial Planning API with enterprise-grade security, scalability, and observability.

## 🏗️ Architecture Overview

The production deployment includes:

- **5 initial replicas** with auto-scaling (5-20 pods)
- **Multi-layered security** with RBAC, NetworkPolicies, and Pod Security Standards
- **High availability** with pod anti-affinity and disruption budgets
- **Comprehensive monitoring** with Prometheus, Grafana, and Jaeger
- **Service mesh** integration with Istio for traffic management
- **Zero-downtime deployments** with rolling updates

## 📁 Directory Structure

```
production/
├── manifests/
│   ├── 00-namespace.yaml              # Namespace, ResourceQuota, LimitRange
│   ├── 01-rbac.yaml                   # ServiceAccount, Role, RoleBinding
│   ├── 02-configmaps-secrets.yaml     # Configuration and secrets
│   ├── 03-deployment.yaml             # Main application deployment
│   ├── 04-hpa.yaml                    # HorizontalPodAutoscaler, VPA, PDB
│   ├── 05-services.yaml               # Services, Ingress, LoadBalancer
│   ├── 06-network-policies.yaml       # NetworkPolicies for security
│   └── 07-monitoring-service-mesh.yaml # Istio, monitoring configs
├── deploy.sh                          # Automated deployment script
└── README.md                          # This file
```

## 🚀 Quick Start

### Prerequisites

1. **Kubernetes cluster** (1.24+) with adequate resources:
   - Minimum: 8 CPU cores, 16GB RAM
   - Recommended: 16+ CPU cores, 32GB+ RAM

2. **kubectl** configured with cluster access
3. **Helm** (optional, for monitoring stack)
4. **Istio** (optional, for service mesh features)

### Basic Deployment

1. **Update secrets** in `manifests/02-configmaps-secrets.yaml`:
   ```bash
   # Replace ALL placeholder values marked with "CHANGE_ME"
   vim manifests/02-configmaps-secrets.yaml
   ```

2. **Deploy the application**:
   ```bash
   ./deploy.sh deploy
   ```

3. **Verify deployment**:
   ```bash
   ./deploy.sh verify
   ```

## 🔧 Configuration

### Environment Variables

Key configuration options in ConfigMaps:

| Variable | Description | Default |
|----------|-------------|---------|
| `ENVIRONMENT` | Deployment environment | `production` |
| `DEBUG` | Enable debug mode | `false` |
| `WORKERS` | Number of worker processes | `4` |
| `DATABASE_POOL_SIZE` | DB connection pool size | `20` |
| `RATE_LIMIT_REQUESTS_PER_MINUTE` | Rate limiting | `100` |

### Secrets Management

**CRITICAL**: Update all secrets before deployment:

```yaml
# Database credentials
DATABASE_PASSWORD: "YOUR_SECURE_PASSWORD"
DATABASE_URL: "postgresql://user:password@host:5432/db"

# JWT signing keys
JWT_SECRET_KEY: "YOUR_256_BIT_SECRET"
JWT_PRIVATE_KEY: "YOUR_RSA_PRIVATE_KEY"
JWT_PUBLIC_KEY: "YOUR_RSA_PUBLIC_KEY"

# API keys
ALPHA_VANTAGE_API_KEY: "YOUR_API_KEY"
FINNHUB_API_KEY: "YOUR_API_KEY"
```

## 📊 Resource Requirements

### Pod Resources

| Component | CPU Request | CPU Limit | Memory Request | Memory Limit |
|-----------|-------------|-----------|----------------|--------------|
| API Container | 500m | 2000m | 1Gi | 4Gi |
| Log Shipper | 50m | 100m | 64Mi | 128Mi |
| Init Container | 100m | 500m | 256Mi | 512Mi |

### Cluster Resources

- **Minimum cluster**: 5 nodes × (2 CPU, 4GB RAM)
- **Recommended cluster**: 10 nodes × (4 CPU, 8GB RAM)
- **Storage**: 200Gi persistent storage for databases

## 🔒 Security Features

### Pod Security

- **Non-root containers** with user ID 1001
- **Read-only root filesystem** with writable volumes
- **Dropped capabilities** (ALL capabilities removed)
- **Security contexts** enforced at pod and container level

### Network Security

- **Default deny-all** NetworkPolicies
- **Explicit allow rules** for required communication
- **Namespace isolation** with strict egress controls
- **mTLS enforcement** via Istio service mesh

### RBAC Security

- **Minimal permissions** principle
- **Separate service accounts** for different components
- **Role-based access** to cluster resources
- **Network policy management** separation

## 📈 Auto-scaling Configuration

### Horizontal Pod Autoscaler (HPA)

```yaml
minReplicas: 5      # Minimum for high availability
maxReplicas: 20     # Maximum to prevent resource exhaustion
```

**Scaling Metrics**:
- CPU utilization > 70%
- Memory utilization > 80%
- HTTP requests > 100 RPS per pod
- Response time > 500ms
- Load balancer queue depth > 10

### Vertical Pod Autoscaler (VPA)

- **Recommendation mode only** (no automatic updates)
- **Resource recommendations** based on actual usage
- **Historical analysis** for optimal sizing

## 🏥 Health Checks

### Probe Configuration

| Probe Type | Path | Initial Delay | Period | Timeout | Threshold |
|------------|------|---------------|--------|---------|-----------|
| Startup | `/health` | 10s | 5s | 5s | 20 failures |
| Liveness | `/health` | 30s | 30s | 10s | 3 failures |
| Readiness | `/health` | 10s | 10s | 5s | 3 failures |

### Health Check Endpoints

- `GET /health` - Overall application health
- `GET /status` - Simple status check
- `GET /metrics` - Prometheus metrics

## 🔄 Deployment Strategies

### Rolling Updates

```yaml
strategy:
  type: RollingUpdate
  rollingUpdate:
    maxUnavailable: 1    # Keep most pods available
    maxSurge: 2          # Allow temporary over-scaling
```

### Blue-Green Deployment (Manual)

1. Deploy to new namespace:
   ```bash
   # Edit namespace in manifests
   ./deploy.sh deploy
   ```

2. Test new version:
   ```bash
   kubectl port-forward -n new-namespace svc/api 8080:80
   curl http://localhost:8080/health
   ```

3. Switch traffic:
   ```bash
   # Update ingress or load balancer configuration
   kubectl patch ingress api-ingress -p '...'
   ```

### Canary Deployment (Istio)

```yaml
# VirtualService with traffic splitting
http:
- match:
  - headers:
      canary:
        exact: "true"
  route:
  - destination:
      host: api-v2
- route:
  - destination:
      host: api-v1
    weight: 90
  - destination:
      host: api-v2
    weight: 10
```

## 📊 Monitoring & Observability

### Metrics Collection

- **Prometheus** scrapes metrics from `/metrics` endpoint
- **Custom metrics** for business KPIs
- **Istio metrics** for service mesh observability
- **Alert rules** for proactive monitoring

### Distributed Tracing

- **Jaeger** for distributed tracing
- **OpenTelemetry** instrumentation
- **7-day retention** for trace data
- **Cross-service correlation** tracking

### Logging

- **Structured JSON logging** with contextual information
- **Log aggregation** via Fluentd/Fluent Bit
- **Elasticsearch** storage with index rotation
- **Log retention** policies

### Dashboards

Pre-configured Grafana dashboards:
- Application performance metrics
- Infrastructure resource usage
- Business KPIs and SLAs
- Error rates and latency percentiles

## 🌐 Service Mesh (Istio)

### Traffic Management

- **Intelligent routing** based on headers/weights
- **Circuit breaker** for fault tolerance
- **Rate limiting** at ingress and service level
- **Retry policies** with exponential backoff

### Security Policies

- **Mutual TLS** (mTLS) for all service communication
- **Authorization policies** for fine-grained access control
- **JWT validation** at ingress gateway
- **Security headers** injection

### Observability

- **Automatic metrics** collection without code changes
- **Distributed tracing** with correlation IDs
- **Access logging** with detailed request information
- **Service topology** visualization

## 🚨 Troubleshooting

### Common Issues

1. **Pods stuck in Pending**:
   ```bash
   kubectl describe pod <pod-name> -n financial-planning-prod
   # Check resource constraints and node capacity
   ```

2. **Failed health checks**:
   ```bash
   kubectl logs <pod-name> -n financial-planning-prod
   kubectl exec <pod-name> -n financial-planning-prod -- curl localhost:8000/health
   ```

3. **Network connectivity issues**:
   ```bash
   kubectl get networkpolicies -n financial-planning-prod
   kubectl describe networkpolicy <policy-name> -n financial-planning-prod
   ```

4. **Database connection failures**:
   ```bash
   kubectl get secrets database-credentials -n financial-planning-prod -o yaml
   kubectl exec <pod-name> -n financial-planning-prod -- nc -zv database-host 5432
   ```

### Debug Commands

```bash
# View all resources
kubectl get all -n financial-planning-prod

# Check pod logs
kubectl logs -l app=financial-planning-api -n financial-planning-prod --tail=100

# Execute commands in pod
kubectl exec -it deployment/financial-planning-api -n financial-planning-prod -- bash

# Port forward for local testing
kubectl port-forward svc/financial-planning-api-svc 8080:80 -n financial-planning-prod

# Scale deployment
kubectl scale deployment financial-planning-api --replicas=10 -n financial-planning-prod

# View HPA status
kubectl get hpa -n financial-planning-prod -w

# Check ingress status
kubectl describe ingress -n financial-planning-prod
```

## 📋 Deployment Checklist

### Pre-deployment

- [ ] Kubernetes cluster provisioned and accessible
- [ ] Required namespaces created (`monitoring`, `logging`, `istio-system`)
- [ ] Persistent volumes available
- [ ] DNS configured for ingress hostnames
- [ ] TLS certificates obtained
- [ ] Database instance running and accessible
- [ ] Redis cache instance running
- [ ] All secrets updated with production values
- [ ] Docker images built and pushed to registry
- [ ] Monitoring stack deployed (Prometheus, Grafana, Jaeger)

### Post-deployment

- [ ] All pods in Running state
- [ ] Health checks passing
- [ ] Services accessible via ingress
- [ ] Database connectivity verified
- [ ] Cache functionality working
- [ ] Metrics being collected
- [ ] Logs being shipped
- [ ] Alerts configured and firing correctly
- [ ] Auto-scaling triggered under load
- [ ] Backup procedures tested

## 🔄 Maintenance

### Regular Tasks

1. **Update secrets** rotation (monthly):
   ```bash
   kubectl patch secret financial-planning-secrets -p '{"data":{"key":"new-value"}}'
   ```

2. **Scale for expected load**:
   ```bash
   kubectl patch hpa financial-planning-api-hpa -p '{"spec":{"minReplicas":10}}'
   ```

3. **Update configuration**:
   ```bash
   kubectl patch configmap financial-planning-config --patch-file config-update.yaml
   kubectl rollout restart deployment/financial-planning-api
   ```

### Backup Procedures

1. **Configuration backup**:
   ```bash
   kubectl get all,secrets,configmaps -n financial-planning-prod -o yaml > backup.yaml
   ```

2. **Database backup** (handled separately by database team)

3. **Persistent volume snapshots** (cloud provider specific)

## 🆘 Emergency Procedures

### Incident Response

1. **Scale down to minimum** (circuit breaker):
   ```bash
   kubectl scale deployment financial-planning-api --replicas=1 -n financial-planning-prod
   ```

2. **Emergency rollback**:
   ```bash
   ./deploy.sh rollback
   ```

3. **Enable maintenance mode**:
   ```bash
   kubectl patch ingress financial-planning-api-ingress --patch-file maintenance-mode.yaml
   ```

4. **Isolate network** (emergency only):
   ```bash
   kubectl apply -f emergency-network-policy.yaml
   ```

### Contact Information

- **Platform Team**: platform-team@company.com
- **On-call Engineer**: +1-XXX-XXX-XXXX
- **Incident Management**: incident-response@company.com
- **Security Team**: security@company.com

## 📚 Additional Resources

- [Kubernetes Production Best Practices](https://kubernetes.io/docs/setup/best-practices/)
- [Istio Security Best Practices](https://istio.io/latest/docs/ops/best-practices/security/)
- [Prometheus Monitoring Best Practices](https://prometheus.io/docs/practices/)
- [Application Architecture Documentation](../docs/architecture.md)
- [API Documentation](../docs/api.md)
- [Runbook](../docs/runbook.md)

---

**Last Updated**: 2025-08-28  
**Version**: 1.0.0  
**Maintainer**: Platform Team