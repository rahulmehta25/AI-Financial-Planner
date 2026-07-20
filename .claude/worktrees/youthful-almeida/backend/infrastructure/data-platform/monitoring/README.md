# Financial Planning Data Platform - Monitoring System

## Overview

This comprehensive monitoring system provides enterprise-grade observability for the Financial Planning Data Platform. It monitors data quality, pipeline health, business KPIs, system performance, and provides real-time alerting across multiple channels.

## 🏗️ Architecture

### Core Components

1. **Data Quality Monitor** - Monitors data completeness, accuracy, freshness, and detects anomalies
2. **Pipeline Health Monitor** - Tracks Airflow DAG performance, task failures, and SLA violations
3. **Business KPI Monitor** - Monitors key business metrics like user activity, transaction volume, goal completion
4. **System Performance Monitor** - Tracks infrastructure metrics (CPU, memory, disk, network)
5. **Alert Manager** - Manages alerts and sends notifications via email, Slack, PagerDuty, webhooks

### Infrastructure Stack

- **Prometheus** - Metrics collection and storage
- **Grafana** - Visualization and dashboards
- **AlertManager** - Alert routing and management
- **Loki** - Log aggregation
- **Jaeger** - Distributed tracing
- **Multiple Exporters** - System, database, application metrics
- **Custom Exporters** - Business-specific metrics

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.9+
- Access to PostgreSQL database
- Redis instance
- Elasticsearch cluster

### 1. Setup Configuration

```bash
# Clone or navigate to the monitoring directory
cd infrastructure/data-platform/monitoring

# Copy and update configuration
cp monitoring_config.yaml.example monitoring_config.yaml
# Edit monitoring_config.yaml with your settings
```

### 2. Run Setup Script

```bash
# Make setup script executable
chmod +x setup_monitoring.py

# Run complete setup for development
python setup_monitoring.py --environment development

# Or setup without deployment
python setup_monitoring.py --no-deploy
```

### 3. Manual Deployment (if needed)

```bash
# Start monitoring stack
docker-compose -f docker-compose.monitoring.yml up -d

# Check service status
docker-compose -f docker-compose.monitoring.yml ps
```

### 4. Access Dashboards

- **Grafana**: http://localhost:3000 (admin/admin123)
- **Prometheus**: http://localhost:9090
- **AlertManager**: http://localhost:9093
- **Jaeger**: http://localhost:16686

## 📊 Monitoring Components

### Data Quality Monitoring

Monitors the following aspects:

- **Completeness**: Null value percentages
- **Uniqueness**: Duplicate record detection
- **Validity**: Data format and constraint validation
- **Freshness**: Data age and update frequency
- **Anomaly Detection**: Statistical outliers and pattern deviations

#### Key Metrics:
- `data_quality_score` - Overall quality score (0-1)
- `data_null_percentage` - Percentage of null values by column
- `data_duplicate_count` - Number of duplicate records
- `data_freshness_hours` - Data age in hours

### Pipeline Health Monitoring

Tracks Airflow pipeline performance:

- **Success Rates**: DAG and task success percentages
- **Duration Tracking**: Pipeline execution times
- **Failure Analysis**: Failed task details and patterns
- **SLA Monitoring**: Service level agreement violations

#### Key Metrics:
- `pipeline_success_rate` - Success rate by DAG
- `pipeline_duration_seconds` - Execution duration
- `pipeline_failed_tasks_total` - Failed task counter
- `pipeline_sla_violations_total` - SLA violation counter

### Business KPI Monitoring

Monitors critical business metrics:

- **User Metrics**: Active users, retention, registration
- **Financial Metrics**: Transaction volume, portfolio values
- **Goal Metrics**: Completion rates, progress tracking
- **Performance Metrics**: API response times, error rates

#### Key Metrics:
- `business_active_users_total` - Total active users
- `business_daily_transactions_total` - Daily transactions
- `business_portfolio_value_total` - Total portfolio value
- `business_goal_completion_rate` - Goal completion rate

### System Performance Monitoring

Tracks infrastructure health:

- **Resource Usage**: CPU, memory, disk utilization
- **Database Performance**: Connection pools, query performance
- **Cache Performance**: Redis metrics
- **Network Performance**: Throughput and latency

#### Key Metrics:
- `system_cpu_usage` - CPU usage percentage
- `system_memory_usage` - Memory usage percentage
- `system_disk_usage` - Disk usage percentage

## 🚨 Alerting

### Alert Severities

- **CRITICAL** - Immediate attention required
- **HIGH** - Important issues requiring prompt response
- **MEDIUM** - Moderate issues for investigation
- **LOW** - Minor issues for awareness
- **INFO** - Informational notifications

### Notification Channels

1. **Email** - All severity levels
2. **Slack** - Medium to Critical
3. **PagerDuty** - High to Critical
4. **Webhooks** - Configurable
5. **SMS** - Critical only (via Twilio)

### Alert Rules

Key alerting rules include:

#### Data Quality Alerts
- Low data quality score (< 80%)
- High null percentage (> 20%)
- Duplicate records detected
- Data freshness issues (> 24 hours)

#### Pipeline Health Alerts
- Pipeline failure (success rate < 90%)
- Long-running pipelines (> 1 hour)
- High task failure rate (> 5 per hour)
- SLA violations

#### Business KPI Alerts
- Low active users (< 100)
- Low transaction volume (< 50/day)
- Low goal completion rate (< 60%)
- Revenue drops (> 20% decrease)

#### System Performance Alerts
- High CPU usage (> 80%)
- High memory usage (> 85%)
- High disk usage (> 90%)
- Service downtime

## 📈 Dashboards

### Pre-built Dashboards

1. **Data Quality Overview**
   - Overall quality scores
   - Quality trends by schema
   - Tables with issues
   - Anomaly detection results

2. **Pipeline Health**
   - DAG success rates
   - Execution duration trends
   - Failed task analysis
   - SLA compliance

3. **Business KPIs**
   - User activity metrics
   - Financial performance
   - Goal progress tracking
   - Growth indicators

4. **System Performance**
   - Infrastructure metrics
   - Database performance
   - Application metrics
   - Resource utilization

### Custom Dashboards

Create custom dashboards in Grafana:
1. Access Grafana at http://localhost:3000
2. Click "+" → Dashboard
3. Add panels with Prometheus queries
4. Save and organize in folders

## ⚙️ Configuration

### Main Configuration File

Edit `monitoring_config.yaml`:

```yaml
monitoring_system:
  enabled: true
  
data_quality:
  enabled: true
  interval_seconds: 300
  tables:
    - schema: "financial_planning"
      table: "users"
      priority: "high"
      quality_threshold: 0.95

alerting:
  enabled: true
  email:
    smtp_server: "smtp.gmail.com"
    smtp_port: 587
    from_address: "alerts@company.com"
    to_addresses: ["admin@company.com"]
```

### Environment Variables

Set in `.env.{environment}` file:

```bash
GRAFANA_ADMIN_PASSWORD=secure_password
POSTGRES_USER=financial_user
POSTGRES_PASSWORD=secure_password
SLACK_BOT_TOKEN=xoxb-your-token
PAGERDUTY_API_KEY=your-api-key
```

### Database Setup

Create required database tables:

```sql
-- Run setup_governance_database() function
-- from data_governance_framework.py
```

## 🔧 Customization

### Adding Custom Metrics

1. **Create Custom Exporter**:
```python
from prometheus_client import Gauge, start_http_server

custom_metric = Gauge('custom_business_metric', 'Description')
custom_metric.set(value)
```

2. **Add to Prometheus Config**:
```yaml
scrape_configs:
  - job_name: 'custom-metrics'
    static_configs:
      - targets: ['custom-exporter:9200']
```

### Custom Alert Rules

Add to `prometheus/rules/custom_rules.yml`:

```yaml
groups:
  - name: custom_alerts
    rules:
      - alert: CustomMetricHigh
        expr: custom_business_metric > 100
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Custom metric is high"
```

### Custom Dashboards

1. Create dashboard JSON
2. Place in `grafana/dashboards/`
3. Restart Grafana or use API

## 🛠️ Troubleshooting

### Common Issues

1. **Services Not Starting**
```bash
# Check logs
docker-compose -f docker-compose.monitoring.yml logs [service_name]

# Check resource usage
docker stats
```

2. **Metrics Not Appearing**
```bash
# Test exporter endpoint
curl http://localhost:9100/metrics

# Check Prometheus targets
# Go to http://localhost:9090/targets
```

3. **Alerts Not Firing**
```bash
# Check AlertManager configuration
# Go to http://localhost:9093

# Validate alert rules
promtool check rules prometheus/rules/*.yml
```

4. **Database Connection Issues**
```bash
# Test database connectivity
docker exec -it postgres psql -U $POSTGRES_USER -d $POSTGRES_DB

# Check exporter logs
docker logs postgres-exporter
```

### Performance Tuning

1. **Prometheus Storage**:
   - Adjust retention time: `--storage.tsdb.retention.time=30d`
   - Increase memory: `--storage.tsdb.retention.size=10GB`

2. **Grafana Performance**:
   - Enable caching in configuration
   - Optimize dashboard queries
   - Use query result caching

3. **Alert Optimization**:
   - Tune alert thresholds
   - Adjust evaluation intervals
   - Use recording rules for complex queries

## 📚 Maintenance

### Regular Tasks

1. **Weekly**:
   - Review alert fatigue
   - Check dashboard performance
   - Update thresholds based on trends

2. **Monthly**:
   - Clean up old metrics data
   - Review and update alert rules
   - Performance optimization

3. **Quarterly**:
   - Capacity planning
   - Security updates
   - Configuration backup

### Backup and Recovery

1. **Prometheus Data**:
```bash
# Backup Prometheus data
docker exec prometheus tar -czf /prometheus-backup.tar.gz /prometheus

# Restore from backup
docker exec prometheus tar -xzf /prometheus-backup.tar.gz
```

2. **Grafana Dashboards**:
```bash
# Export dashboards
curl -H "Authorization: Bearer $GRAFANA_API_KEY" \
  http://localhost:3000/api/dashboards/db/dashboard-name
```

### Updates

1. **Update Images**:
```bash
docker-compose -f docker-compose.monitoring.yml pull
docker-compose -f docker-compose.monitoring.yml up -d
```

2. **Update Configuration**:
```bash
# Edit configuration files
# Reload services
docker-compose -f docker-compose.monitoring.yml restart
```

## 🔒 Security

### Authentication

- Grafana: Username/password authentication
- Prometheus: Basic authentication (production)
- AlertManager: OAuth integration available

### Network Security

- All services run in isolated Docker network
- Firewall rules for external access
- TLS encryption for external endpoints

### Data Protection

- Sensitive metrics are masked
- Access control by user roles
- Audit logging enabled

## 📞 Support

### Documentation

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [AlertManager Documentation](https://prometheus.io/docs/alerting/latest/alertmanager/)

### Contact

For issues or questions:
- Create GitHub issue
- Contact DevOps team
- Check internal documentation

## 🔄 Updates and Roadmap

### Recent Updates

- v1.0.0: Initial monitoring system implementation
- Enhanced data quality monitoring
- Business KPI tracking
- Multi-channel alerting

### Planned Features

- Machine learning-based anomaly detection
- Automated remediation workflows
- Enhanced business intelligence
- Mobile dashboard application
- Advanced forecasting and capacity planning

---

**Last Updated**: 2025-08-22
**Version**: 1.0.0
**Maintainer**: Data Engineering Team