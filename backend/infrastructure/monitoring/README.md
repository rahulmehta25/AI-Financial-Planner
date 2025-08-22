# Financial Planning - Comprehensive Monitoring & Observability Stack

This directory contains a complete monitoring and observability solution for the Financial Planning backend application, designed for rapid incident response and comprehensive system visibility.

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Application   │    │   Monitoring    │    │   Alerting      │
│   Metrics       │───▶│   Collection    │───▶│   & Response    │
│   Logs          │    │   & Storage     │    │                 │
│   Traces        │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📊 Components

### 1. Application Monitoring (Prometheus + Grafana)
- **Prometheus**: Metrics collection and time-series storage
- **Grafana**: Visualization dashboards and alerting
- **Custom Business Metrics**: Financial planning specific KPIs

### 2. Infrastructure Monitoring
- **Node Exporter**: System-level metrics (CPU, memory, disk)
- **cAdvisor**: Container metrics
- **PostgreSQL Exporter**: Database performance metrics
- **Redis Exporter**: Cache performance metrics

### 3. Log Aggregation (ELK Stack)
- **Elasticsearch**: Log storage and search
- **Logstash**: Log processing and transformation
- **Kibana**: Log visualization and analysis
- **Filebeat**: Log shipping from containers

### 4. Error Tracking (Sentry)
- **Error Grouping**: Automatic error categorization
- **Release Tracking**: Error trends across deployments
- **Performance Monitoring**: Transaction and query performance
- **User Impact Analysis**: Error impact on user experience

### 5. Distributed Tracing (OpenTelemetry + Jaeger)
- **Request Tracing**: End-to-end request flow tracking
- **Service Dependencies**: Microservice interaction mapping
- **Performance Bottlenecks**: Slow service identification
- **Error Correlation**: Link errors to specific traces

### 6. Alerting (PagerDuty Integration)
- **Escalation Policies**: Team-specific alert routing
- **Business Hours**: Different escalation for off-hours
- **Alert Grouping**: Reduce noise with intelligent grouping
- **Runbook Integration**: Automatic troubleshooting guidance

### 7. Synthetic Monitoring
- **Uptime Checks**: Endpoint availability monitoring
- **User Journey Testing**: Complete workflow validation
- **Performance Monitoring**: Response time tracking
- **Geographic Distribution**: Multi-region monitoring

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Environment variables configured (see `.env.example`)

### 1. Start the Monitoring Stack

```bash
# Create monitoring network
docker network create financial-monitoring

# Start all monitoring services
docker-compose -f docker-compose.monitoring.yml up -d

# Check service health
docker-compose -f docker-compose.monitoring.yml ps
```

### 2. Access Monitoring Interfaces

| Service | URL | Default Credentials |
|---------|-----|-------------------|
| Grafana | http://localhost:3000 | admin / admin |
| Prometheus | http://localhost:9090 | - |
| Kibana | http://localhost:5601 | - |
| Jaeger | http://localhost:16686 | - |
| AlertManager | http://localhost:9093 | - |

### 3. Configure Application Integration

Add to your application's main.py:

```python
from infrastructure.monitoring.sentry.sentry_config import init_sentry
from infrastructure.monitoring.tracing.opentelemetry_config import initialize_tracing
from infrastructure.monitoring.metrics.business_metrics import financial_metrics

# Initialize monitoring
init_sentry("production")
initialize_tracing()

# Add metrics endpoint
@app.get("/metrics")
async def metrics():
    return Response(
        financial_metrics.export_metrics(),
        media_type="text/plain"
    )
```

## 📈 Dashboard Overview

### Application Overview Dashboard
- API health and response times
- Request rates and error rates
- Active user counts
- Database and cache performance

### Business Metrics Dashboard
- Monte Carlo simulations per day
- AI recommendation acceptance rates
- PDF report generation metrics
- User engagement metrics
- Revenue and growth KPIs

### Infrastructure Dashboard
- System resource usage
- Container performance
- Network I/O
- Disk usage and availability

## 🔍 Key Metrics & SLAs

### Service Level Objectives (SLOs)

| Metric | Target | Measurement |
|--------|---------|-------------|
| API Availability | 99.9% | Uptime over 30 days |
| API Response Time | <500ms p95 | 95th percentile response time |
| Simulation Success Rate | >99% | Successful simulations / total |
| Market Data Freshness | <5 minutes | Time since last update |
| PDF Generation Time | <30s p95 | 95th percentile generation time |

### Critical Business Metrics

- **Daily Simulations**: Monte Carlo simulations run per day
- **User Engagement**: Active users and session duration
- **Recommendation Accuracy**: ML model prediction accuracy
- **Revenue Metrics**: MRR, CAC, LTV, Churn Rate
- **System Performance**: Error rates, response times

## 🚨 Alerting Strategy

### Alert Severity Levels

1. **Critical**: Immediate response required (5-15 minutes)
   - API completely down
   - Database unavailable
   - Security incidents
   - Customer-facing errors >10%

2. **High**: Response within 1-4 hours
   - High error rates (5-10%)
   - Performance degradation
   - Banking integration failures
   - Simulation failures >5%

3. **Medium**: Response within 24 hours
   - Resource utilization warnings
   - Low cache hit rates
   - AI model accuracy decline

4. **Low**: Response within 48 hours
   - Info-level monitoring alerts
   - Capacity planning warnings

### Escalation Matrix

| Component | Team | Primary Contact | Escalation |
|-----------|------|----------------|------------|
| API/Backend | Backend Team | On-call Engineer | Engineering Manager |
| Database | Database Team | DBA | DevOps Lead |
| AI/ML | ML Team | ML Engineer | Data Science Manager |
| Market Data | Data Team | Data Engineer | Backend Lead |
| Infrastructure | DevOps | DevOps Engineer | CTO |

## 📋 Runbooks

### Common Incidents

1. **API Down**: [runbooks/api-down.md](runbooks/api-down.md)
2. **High Response Times**: [runbooks/performance-issues.md](runbooks/performance-issues.md)
3. **Database Issues**: [runbooks/database-issues.md](runbooks/database-issues.md)
4. **Market Data Failures**: [runbooks/market-data-issues.md](runbooks/market-data-issues.md)
5. **Simulation Failures**: [runbooks/simulation-issues.md](runbooks/simulation-issues.md)

## 🔧 Configuration

### Environment Variables

Create a `.env` file with the following variables:

```bash
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=financial_planning
DB_USER=your_user
DB_PASSWORD=your_password

# Monitoring Configuration
GRAFANA_ADMIN_PASSWORD=secure_password
KIBANA_PASSWORD=secure_password
KIBANA_ENCRYPTION_KEY=your-32-char-encryption-key

# External Services
SENTRY_DSN=your_sentry_dsn
PAGERDUTY_API_TOKEN=your_pagerduty_token
PAGERDUTY_CRITICAL_SERVICE_KEY=your_service_key
PAGERDUTY_WARNING_SERVICE_KEY=your_service_key

# Application
FINANCIAL_API_BASE_URL=http://localhost:8000
SYNTHETIC_API_TOKEN=your_api_token

# Email Configuration
SMTP_HOST=localhost:587
SMTP_USER=your_email
SMTP_PASSWORD=your_password
```

### Custom Metrics Integration

Use the business metrics collector in your application:

```python
from infrastructure.monitoring.metrics.business_metrics import financial_metrics
from infrastructure.monitoring.metrics.business_metrics import SimulationType, RecommendationType

# Record a Monte Carlo simulation
financial_metrics.record_simulation(
    simulation_type=SimulationType.MONTE_CARLO,
    duration=45.2,
    iterations=10000,
    portfolio_value=100000,
    status="success"
)

# Record an AI recommendation
financial_metrics.record_recommendation(
    rec_type=RecommendationType.PORTFOLIO_REBALANCE,
    generation_time=2.5,
    confidence=0.85,
    user_segment="premium"
)
```

## 🛠️ Maintenance

### Daily Tasks
- Review overnight alerts and incidents
- Check system resource usage trends
- Verify backup completion
- Review synthetic monitoring results

### Weekly Tasks
- Analyze error trends and patterns
- Review and update dashboard configurations
- Check log retention and cleanup
- Update monitoring documentation

### Monthly Tasks
- Review SLA/SLO performance
- Update escalation policies
- Analyze cost optimization opportunities
- Conduct monitoring system health checks

## 🔍 Troubleshooting

### Common Issues

1. **High Memory Usage**
   ```bash
   # Check container memory usage
   docker stats
   
   # Adjust memory limits in docker-compose.yml
   ```

2. **Elasticsearch Disk Space**
   ```bash
   # Check disk usage
   docker exec elasticsearch df -h
   
   # Clean old indices
   docker exec elasticsearch curator delete indices --older-than 30
   ```

3. **Missing Metrics**
   ```bash
   # Check Prometheus targets
   curl http://localhost:9090/api/v1/targets
   
   # Verify application metrics endpoint
   curl http://localhost:8000/metrics
   ```

## 📚 Additional Resources

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [Elasticsearch Guide](https://www.elastic.co/guide/)
- [Jaeger Documentation](https://www.jaegertracing.io/docs/)
- [PagerDuty API Reference](https://developer.pagerduty.com/docs/)
- [OpenTelemetry Documentation](https://opentelemetry.io/docs/)

## 🤝 Contributing

When adding new metrics or monitoring capabilities:

1. Update the business metrics collector
2. Create corresponding Grafana dashboard panels
3. Add appropriate alerting rules
4. Update runbook documentation
5. Test synthetic monitoring scenarios

## 📞 Support

For monitoring system issues:
- **Critical Issues**: Page the DevOps on-call engineer
- **General Questions**: Create a ticket in the monitoring project
- **Dashboard Requests**: Contact the platform team

---

**Remember**: This monitoring system is designed for rapid incident response. When alerts fire, they indicate real user impact that requires immediate attention.