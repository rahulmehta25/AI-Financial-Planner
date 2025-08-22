# Cloud Deployment Configurations

This directory contains infrastructure-as-code configurations for deploying the Financial Planning demo application across multiple cloud providers.

## 📊 Cost Comparison

| Provider | Monthly Cost (Demo) | Setup Complexity | Best For |
|----------|-------------------|------------------|----------|
| **AWS** | ~$85 | Medium | Production-ready, scalable |
| **GCP** | ~$70 | Medium | Cloud Run simplicity |
| **Azure** | ~$75 | Low | Enterprise integration |
| **Heroku** | ~$50 | Very Low | Quick demos, prototypes |

## 🚀 Quick Start

### AWS Deployment (Recommended)

```bash
cd aws/scripts
chmod +x deploy-aws.sh
./deploy-aws.sh
```

**Features:**
- ECS Fargate with Spot instances (70% cost savings)
- RDS PostgreSQL with automated backups
- ElastiCache Redis for caching
- CloudFront CDN for static assets
- Auto-scaling with cost optimization
- CloudWatch monitoring and alerts

**Estimated Time:** 15-20 minutes

### GCP Deployment

```bash
cd gcp/terraform
terraform init
terraform plan -var="project_id=your-project-id"
terraform apply
```

**Features:**
- Cloud Run with scale-to-zero
- Cloud SQL PostgreSQL
- Memorystore Redis
- Cloud CDN
- Container Registry
- Automatic HTTPS

**Estimated Time:** 10-15 minutes

### Azure Deployment

```bash
cd azure/scripts
./deploy-azure.sh
```

Or use Azure Portal:
1. Click "Deploy to Azure" button
2. Fill in parameters
3. Review and create

**Features:**
- App Service with containers
- Azure Database for PostgreSQL
- Azure Cache for Redis
- Application Insights monitoring
- Key Vault for secrets
- Virtual Network integration

**Estimated Time:** 20-25 minutes

### Heroku Deployment (Fastest)

```bash
cd heroku
heroku create your-app-name
git push heroku main
```

Or use the Heroku Button:

[![Deploy to Heroku](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy)

**Features:**
- One-click deployment
- Automatic SSL
- Managed PostgreSQL and Redis
- Zero configuration needed
- Review apps for PRs

**Estimated Time:** 5 minutes

## 💰 Cost Optimization Tips

### General Strategies
1. **Use Free Tiers**: All providers offer free tiers for the first year
2. **Schedule Shutdowns**: Turn off resources during non-business hours
3. **Right-size Resources**: Start small and scale based on actual usage
4. **Use Spot/Preemptible Instances**: 70-90% cost savings for non-critical workloads
5. **Monitor Daily**: Set up cost alerts and review regularly

### AWS Specific
- Use Fargate Spot for ECS tasks
- Stop RDS instances when not in use
- Use S3 lifecycle policies
- Consider Lambda for low-traffic scenarios

### GCP Specific
- Use Cloud Run's scale-to-zero feature
- Enable auto-pause for Cloud SQL
- Use committed use discounts
- Leverage free tier quotas

### Azure Specific
- Use B-series VMs for burstable workloads
- Leverage Azure Hybrid Benefit if eligible
- Use reserved instances for production
- Enable auto-shutdown for dev/test

## 🏗️ Architecture Overview

### Components
- **Frontend**: Next.js application served via CDN
- **Backend**: FastAPI application with auto-scaling
- **Database**: PostgreSQL with automated backups
- **Cache**: Redis for session and computation caching
- **Storage**: Object storage for static assets
- **Monitoring**: Application and infrastructure metrics

### Security Features
- HTTPS/TLS encryption everywhere
- Private VPC/VNet networking
- Secrets management (AWS Secrets Manager, GCP Secret Manager, Azure Key Vault)
- IAM roles with least privilege
- Network security groups/firewall rules

## 📈 Scaling Configurations

### Demo Environment
- Minimal resources for cost optimization
- Single instance deployments
- Basic monitoring
- 7-day log retention

### Staging Environment
- Moderate resources for testing
- Multi-instance deployments
- Enhanced monitoring
- 30-day log retention

### Production Environment
- High availability configuration
- Auto-scaling based on load
- Full monitoring and alerting
- 90-day log retention
- Disaster recovery setup

## 🔧 Customization

Each deployment can be customized via:
- **Terraform variables** (AWS, GCP)
- **ARM template parameters** (Azure)
- **Environment variables** (Heroku)

Common customizations:
```bash
# AWS
terraform apply -var="environment=production" -var="rds_instance_class=db.t3.medium"

# GCP
terraform apply -var="backend_min_instances=1" -var="db_tier=db-n1-standard-1"

# Azure
az deployment group create --parameters environment=production

# Heroku
heroku config:set ENVIRONMENT=production
```

## 📊 Monitoring & Alerts

### Metrics to Monitor
- Application response times
- Error rates
- Database connections
- Memory/CPU usage
- Monthly costs

### Alert Thresholds
- Cost: > $100/month
- Error rate: > 1%
- Response time: > 2 seconds
- CPU: > 80%
- Memory: > 90%

## 🔒 Security Best Practices

1. **Never commit secrets** - Use environment variables or secret managers
2. **Enable MFA** for cloud provider accounts
3. **Rotate credentials** regularly
4. **Use private endpoints** where possible
5. **Enable audit logging**
6. **Regular security updates**
7. **Implement backup strategies**

## 🛠️ Troubleshooting

### Common Issues

#### AWS
- **ECS tasks failing**: Check CloudWatch logs
- **RDS connection issues**: Verify security groups
- **High costs**: Review Cost Explorer

#### GCP
- **Cloud Run timeout**: Increase timeout settings
- **SQL connection refused**: Check VPC connector
- **Permission denied**: Review IAM roles

#### Azure
- **Deployment failed**: Check deployment logs in Portal
- **App Service down**: Review Application Insights
- **Database slow**: Check DTU usage

#### Heroku
- **Build failed**: Check build logs
- **App crashed**: Run `heroku logs --tail`
- **Database full**: Upgrade to larger plan

## 📚 Additional Resources

- [AWS Well-Architected Framework](https://aws.amazon.com/architecture/well-architected/)
- [GCP Architecture Framework](https://cloud.google.com/architecture/framework)
- [Azure Architecture Center](https://docs.microsoft.com/en-us/azure/architecture/)
- [Heroku Best Practices](https://devcenter.heroku.com/articles/architecting-apps)

## 💡 Next Steps

1. Choose your preferred cloud provider
2. Review the cost estimates
3. Customize the configuration
4. Deploy using provided scripts
5. Set up monitoring and alerts
6. Configure custom domain (optional)
7. Enable CI/CD pipeline (optional)

## 📞 Support

For deployment issues or questions:
- Create an issue in the repository
- Check provider-specific documentation
- Review CloudWatch/Stackdriver/Application Insights logs
- Contact cloud provider support