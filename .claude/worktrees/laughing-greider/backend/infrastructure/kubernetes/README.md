# Financial Planning - Production-Ready Kubernetes Deployment

This directory contains comprehensive production-ready Kubernetes deployment configurations for the Financial Planning application, including manifests, Helm charts, auto-scaling, security policies, monitoring, and service mesh integration.

## 📁 Directory Structure

```
infrastructure/kubernetes/
├── manifests/                 # Core Kubernetes resources
│   ├── 00-namespaces.yml     # Namespace definitions
│   ├── 01-configmaps.yml     # Application configuration
│   ├── 02-secrets.yml        # Secret templates
│   ├── 03-deployments.yml    # Microservice deployments
│   └── 04-services.yml       # Service definitions
├── persistence/               # Storage and persistence
│   └── persistent-volumes.yml # PVCs and storage classes
├── autoscaling/              # Auto-scaling configurations
│   ├── hpa.yml               # Horizontal Pod Autoscaler
│   ├── vpa.yml               # Vertical Pod Autoscaler
│   └── cluster-autoscaler.yml # Node auto-scaling
├── security/                 # Security policies
│   ├── rbac.yml              # Role-based access control
│   ├── network-policies.yml  # Network segmentation
│   └── pod-security-standards.yml # Pod security
├── monitoring/               # Observability stack
│   ├── prometheus.yml        # Metrics collection
│   └── grafana.yml           # Dashboards and visualization
├── ingress/                  # Traffic management
│   └── istio-gateway.yml     # Service mesh configuration
└── README.md                 # This file
```

## 🚀 Deployment Guide

### Prerequisites

1. **Kubernetes Cluster** (v1.24+)
   - EKS, GKE, or AKS recommended for production
   - Node groups: compute-optimized, memory-optimized, GPU nodes

2. **Required Tools**
   ```bash
   kubectl >= 1.24
   helm >= 3.10
   istioctl >= 1.20
   ```

3. **Dependencies**
   ```bash
   # Install Istio
   istioctl install --set values.defaultRevision=default
   
   # Install cert-manager
   helm repo add jetstack https://charts.jetstack.io
   helm install cert-manager jetstack/cert-manager --namespace cert-manager --create-namespace --set installCRDs=true
   
   # Install external-secrets
   helm repo add external-secrets https://charts.external-secrets.io
   helm install external-secrets external-secrets/external-secrets --namespace external-secrets-system --create-namespace
   ```

### Quick Start

1. **Deploy Core Infrastructure**
   ```bash
   # Create namespaces
   kubectl apply -f manifests/00-namespaces.yml
   
   # Deploy secrets (update with actual values)
   kubectl apply -f manifests/02-secrets.yml
   
   # Deploy configuration
   kubectl apply -f manifests/01-configmaps.yml
   
   # Create persistent volumes
   kubectl apply -f persistence/persistent-volumes.yml
   ```

2. **Deploy Services**
   ```bash
   # Deploy all microservices
   kubectl apply -f manifests/03-deployments.yml
   kubectl apply -f manifests/04-services.yml
   ```

3. **Configure Auto-scaling**
   ```bash
   kubectl apply -f autoscaling/
   ```

4. **Apply Security Policies**
   ```bash
   kubectl apply -f security/
   ```

5. **Setup Monitoring**
   ```bash
   kubectl apply -f monitoring/
   ```

6. **Configure Service Mesh**
   ```bash
   kubectl label namespace financial-planning istio-injection=enabled
   kubectl apply -f ingress/istio-gateway.yml
   ```

### Helm Deployment (Recommended)

```bash
# Production deployment
helm install financial-planning ./helm/financial-planning \
  --namespace financial-planning \
  --create-namespace \
  --values ./helm/financial-planning/values/production.yaml

# Staging deployment
helm install financial-planning-staging ./helm/financial-planning \
  --namespace financial-planning-staging \
  --create-namespace \
  --values ./helm/financial-planning/values/staging.yaml
```

## 🔧 Configuration

### Environment-Specific Values

- **Production** (`values/production.yaml`): High availability, full security, comprehensive monitoring
- **Staging** (`values/staging.yaml`): Scaled-down resources, reduced retention, testing-friendly
- **Development** (`values/development.yaml`): Minimal resources, disabled monitoring, local-friendly

### Secret Management

Update the following secrets before deployment:

```bash
# Database credentials
kubectl create secret generic database-credentials \
  --from-literal=password=<DATABASE_PASSWORD> \
  --from-literal=username=<DATABASE_USERNAME> \
  --namespace financial-planning

# API keys and external service credentials
kubectl create secret generic api-credentials \
  --from-literal=openai-api-key=<OPENAI_KEY> \
  --from-literal=plaid-client-id=<PLAID_CLIENT_ID> \
  --from-literal=plaid-secret=<PLAID_SECRET> \
  --namespace financial-planning
```

## 📊 Monitoring & Observability

### Access URLs (after deployment)

- **Grafana**: https://grafana.financialplanning.com
- **Prometheus**: https://prometheus.financialplanning.com
- **Jaeger**: https://jaeger.financialplanning.com

### Key Metrics

- **API Performance**: Request rate, response time, error rate
- **Business Metrics**: User registrations, transactions, goal completions
- **Infrastructure**: CPU, memory, disk usage, network traffic
- **Security**: Authentication failures, suspicious activity

### Alerts

- High error rate (>5%)
- High response time (>500ms for 95th percentile)
- Resource exhaustion (CPU >80%, Memory >90%)
- Security incidents

## 🔒 Security Features

### Network Security
- **Network Policies**: Micro-segmentation between services
- **Service Mesh**: mTLS encryption for all inter-service communication
- **Ingress Security**: WAF, rate limiting, DDoS protection

### Pod Security
- **Security Context**: Non-root containers, read-only filesystems
- **Pod Security Standards**: Restricted profile enforcement
- **RBAC**: Least privilege access control

### Data Security
- **Encryption at Rest**: All persistent volumes encrypted
- **Secrets Management**: External secrets with rotation
- **Audit Logging**: Comprehensive audit trail

## 🚦 Auto-scaling

### Horizontal Pod Autoscaler (HPA)
- **API Service**: 3-50 replicas based on CPU/memory/custom metrics
- **Banking Service**: 3-20 replicas (critical service)
- **ML Service**: Manual scaling (GPU workloads)

### Vertical Pod Autoscaler (VPA)
- Automatic resource right-sizing
- Recommendation-only mode for GPU workloads

### Cluster Autoscaler
- **General Compute**: 2-20 nodes (m5.large-2xlarge)
- **Compute Optimized**: 3-30 nodes (c5.large-4xlarge)
- **Memory Optimized**: 1-10 nodes (r5.large-4xlarge)
- **GPU Nodes**: 0-5 nodes (p3.2xlarge, g4dn.xlarge)

## 🔄 Traffic Management

### Service Mesh Features
- **Load Balancing**: Least connection, round-robin strategies
- **Circuit Breaking**: Automatic failure detection and isolation
- **Retries**: Configurable retry policies per service
- **Timeouts**: Service-specific timeout configurations
- **Rate Limiting**: User and IP-based rate limiting

### Traffic Policies
- **Banking Service**: Conservative settings, enhanced security
- **ML Service**: Extended timeouts, single retry attempts
- **API Service**: Balanced performance and reliability

## 📱 Service Architecture

### Microservices
1. **financial-planning-api**: Main API gateway (Port 8000)
2. **user-service**: User management and authentication (Port 8002)
3. **banking-service**: Financial data integration (Port 8003)
4. **ml-service**: Machine learning recommendations (Port 8004)
5. **notification-service**: Multi-channel notifications (Port 8005)
6. **document-service**: PDF generation and storage (Port 8006)
7. **simulation-service**: Financial simulations (Port 8001)
8. **graphql-gateway**: GraphQL API endpoint (Port 4000)

### Databases
- **PostgreSQL**: Primary database with read replicas
- **Redis**: Caching and session storage
- **Elasticsearch**: Log aggregation and search

## 🛠 Troubleshooting

### Common Issues

1. **Pod Startup Issues**
   ```bash
   kubectl describe pod <pod-name> -n financial-planning
   kubectl logs <pod-name> -n financial-planning --previous
   ```

2. **Service Connectivity**
   ```bash
   kubectl exec -it <pod-name> -n financial-planning -- wget -qO- http://service-name:port/health
   ```

3. **Certificate Issues**
   ```bash
   kubectl get certificaterequests -n financial-planning
   kubectl describe certificate <cert-name> -n financial-planning
   ```

4. **Istio Configuration**
   ```bash
   istioctl proxy-config cluster <pod-name> -n financial-planning
   istioctl analyze -n financial-planning
   ```

### Performance Debugging

```bash
# Check resource usage
kubectl top pods -n financial-planning
kubectl top nodes

# View HPA status
kubectl get hpa -n financial-planning

# Check service mesh metrics
kubectl exec -it <pod-name> -n financial-planning -c istio-proxy -- pilot-agent request GET stats/prometheus
```

## 📚 Additional Resources

- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Helm Charts](https://helm.sh/docs/)
- [Istio Service Mesh](https://istio.io/latest/docs/)
- [Prometheus Monitoring](https://prometheus.io/docs/)
- [Grafana Dashboards](https://grafana.com/docs/)

## 🤝 Contributing

When making changes to the Kubernetes configuration:

1. Test in development environment first
2. Validate YAML syntax: `kubectl apply --dry-run=client -f <file>`
3. Update documentation as needed
4. Follow semantic versioning for Helm charts

## 📄 License

This configuration is part of the Financial Planning application and follows the project's MIT license.