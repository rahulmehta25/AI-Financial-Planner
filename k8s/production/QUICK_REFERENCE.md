# Financial Planning API - Production Quick Reference

## 🚀 One-Command Deployment

```bash
# Deploy everything
./deploy.sh deploy

# Verify deployment
./deploy.sh verify

# Rollback if needed
./deploy.sh rollback
```

## 🔧 Essential Commands

### Pod Management
```bash
# View pods
kubectl get pods -n financial-planning-prod

# View logs
kubectl logs -l app=financial-planning-api -n financial-planning-prod -f

# Exec into pod
kubectl exec -it deployment/financial-planning-api -n financial-planning-prod -- bash

# Restart deployment
kubectl rollout restart deployment/financial-planning-api -n financial-planning-prod
```

### Scaling
```bash
# Manual scale
kubectl scale deployment financial-planning-api --replicas=10 -n financial-planning-prod

# View HPA status
kubectl get hpa -n financial-planning-prod

# Update HPA min/max
kubectl patch hpa financial-planning-api-hpa -p '{"spec":{"minReplicas":8,"maxReplicas":25}}' -n financial-planning-prod
```

### Service Access
```bash
# Port forward
kubectl port-forward svc/financial-planning-api-svc 8080:80 -n financial-planning-prod

# Test health
curl http://localhost:8080/health

# Test API
curl http://localhost:8080/api/v1/mock/portfolio
```

### Monitoring
```bash
# View metrics
kubectl port-forward svc/financial-planning-api-metrics 9090:9090 -n financial-planning-prod
# Open http://localhost:9090/metrics

# Check alerts
kubectl get prometheusrule -n financial-planning-prod

# View service mesh
kubectl port-forward -n istio-system svc/kiali 20001:20001
# Open http://localhost:20001
```

## 🔒 Security Quick Checks

```bash
# Check network policies
kubectl get networkpolicies -n financial-planning-prod

# Verify RBAC
kubectl auth can-i --list --as=system:serviceaccount:financial-planning-prod:financial-planning-api -n financial-planning-prod

# Check pod security
kubectl get pods -n financial-planning-prod -o jsonpath='{.items[*].spec.securityContext}'

# Verify secrets
kubectl get secrets -n financial-planning-prod
```

## 📊 Performance Monitoring

```bash
# CPU/Memory usage
kubectl top pods -n financial-planning-prod

# Resource quotas
kubectl describe quota -n financial-planning-prod

# Network policies test
kubectl exec -it deployment/financial-planning-api -n financial-planning-prod -- nc -zv database-host 5432
```

## 🚨 Emergency Commands

```bash
# Emergency scale down
kubectl scale deployment financial-planning-api --replicas=1 -n financial-planning-prod

# Drain node for maintenance
kubectl drain <node-name> --ignore-daemonsets --delete-emptydir-data

# Emergency rollback
kubectl rollout undo deployment/financial-planning-api -n financial-planning-prod

# Patch for maintenance mode
kubectl patch ingress financial-planning-api-ingress -p '{"metadata":{"annotations":{"nginx.ingress.kubernetes.io/default-backend":"maintenance-page"}}}'
```

## 📋 Health Status Dashboard

```bash
# All-in-one status check
echo "=== PODS ==="
kubectl get pods -n financial-planning-prod
echo "=== SERVICES ==="
kubectl get svc -n financial-planning-prod
echo "=== HPA ==="
kubectl get hpa -n financial-planning-prod
echo "=== INGRESS ==="
kubectl get ingress -n financial-planning-prod
echo "=== NETWORK POLICIES ==="
kubectl get networkpolicies -n financial-planning-prod
```

## 🔄 Update Procedures

### Config Update (Zero Downtime)
```bash
# Edit configmap
kubectl edit configmap financial-planning-config -n financial-planning-prod

# Rolling restart
kubectl rollout restart deployment/financial-planning-api -n financial-planning-prod
```

### Secret Update (Secure)
```bash
# Update secret
kubectl patch secret financial-planning-secrets -n financial-planning-prod -p '{"data":{"DATABASE_PASSWORD":"<base64-new-password>"}}'

# Rolling restart
kubectl rollout restart deployment/financial-planning-api -n financial-planning-prod
```

### Image Update
```bash
# Update image
kubectl set image deployment/financial-planning-api financial-planning-api=financial-planning-api:v1.1.0 -n financial-planning-prod

# Check rollout status
kubectl rollout status deployment/financial-planning-api -n financial-planning-prod
```

## 🆘 Troubleshooting Checklist

### Pod Won't Start
1. `kubectl describe pod <pod-name> -n financial-planning-prod`
2. Check events for resource/scheduling issues
3. Verify secrets and configmaps exist
4. Check image pull secrets

### Network Issues
1. `kubectl get networkpolicies -n financial-planning-prod`
2. Test connectivity: `kubectl exec <pod> -- nc -zv <target> <port>`
3. Check DNS: `kubectl exec <pod> -- nslookup <service-name>`
4. Verify service endpoints: `kubectl get endpoints -n financial-planning-prod`

### Performance Issues
1. `kubectl top pods -n financial-planning-prod`
2. Check HPA metrics: `kubectl describe hpa -n financial-planning-prod`
3. Review Grafana dashboards
4. Check application logs for errors

## 🌐 External Access URLs

| Service | URL | Purpose |
|---------|-----|---------|
| API | https://api.financial-planning.yourdomain.com | Main API |
| Kiali | https://kiali.financial-planning.yourdomain.com | Service Mesh |
| Jaeger | https://jaeger.financial-planning.yourdomain.com | Tracing |
| Grafana | https://grafana.monitoring.yourdomain.com | Dashboards |

---
**🔗 Full Documentation**: [README.md](./README.md)  
**📞 Emergency Contact**: +1-XXX-XXX-XXXX