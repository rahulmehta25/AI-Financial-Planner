# AWS Cost Estimates for Financial Planning Demo

## Monthly Cost Breakdown (Demo Environment)

### Core Infrastructure Costs

| Service | Configuration | Monthly Cost | Notes |
|---------|--------------|--------------|-------|
| **Application Load Balancer** | 1x ALB | $18.00 | Fixed cost + data processing |
| **ECS Fargate (Spot)** | 2x 0.25 vCPU, 0.5GB RAM | $20.00 | Using Fargate Spot for 70% discount |
| **RDS PostgreSQL** | db.t3.micro, 20GB storage | $15.00 | After free tier expires |
| **ElastiCache Redis** | cache.t3.micro, 1 node | $13.00 | Single node, no replication |
| **CloudFront CDN** | Basic distribution | $5.00 | Estimated for demo traffic |
| **S3 Storage** | 10GB static assets | $2.00 | Standard storage class |
| **Data Transfer** | 50GB egress | $10.00 | Outbound data transfer |
| **CloudWatch Logs** | 7-day retention | $2.00 | Minimal logging |

**Total Estimated: $85/month**

## Cost Optimization Strategies

### 1. Free Tier Savings (First 12 Months)
- **RDS**: 750 hours/month of db.t3.micro - **Saves $15/month**
- **EC2/Fargate**: 750 hours/month - **Saves $10/month**
- **S3**: 5GB storage free - **Saves $1/month**
- **CloudFront**: 50GB transfer free - **Saves $5/month**
- **Total Free Tier Savings: $31/month**

### 2. Scheduled Scaling (Non-Production)
```bash
# Auto-shutdown during non-business hours (8 PM - 8 AM)
# Saves 50% on compute costs
```
- **Potential Savings: $25/month**

### 3. Reserved Capacity (Production)
- **1-year RDS Reserved Instance**: 30% discount - **Saves $5/month**
- **Savings Plans for Fargate**: 20% discount - **Saves $4/month**

### 4. Spot Instances
- **Fargate Spot**: Already included (70% discount)
- **Additional Spot usage**: Can save up to 90% on compute

## Environment-Specific Configurations

### Demo Environment (~$85/month)
```hcl
# Minimal resources for demonstrations
backend_cpu          = "256"    # 0.25 vCPU
backend_memory       = "512"    # 0.5 GB
backend_desired_count = 1       # Single instance
rds_instance_class   = "db.t3.micro"
redis_node_type      = "cache.t3.micro"
```

### Staging Environment (~$150/month)
```hcl
# Moderate resources for testing
backend_cpu          = "512"    # 0.5 vCPU
backend_memory       = "1024"   # 1 GB
backend_desired_count = 2       # Redundancy
rds_instance_class   = "db.t3.small"
redis_node_type      = "cache.t3.small"
rds_multi_az        = false
```

### Production Environment (~$500/month)
```hcl
# Production-ready with high availability
backend_cpu          = "1024"   # 1 vCPU
backend_memory       = "2048"   # 2 GB
backend_desired_count = 3       # High availability
backend_max_capacity = 10       # Auto-scaling
rds_instance_class   = "db.t3.medium"
redis_node_type      = "cache.m5.large"
rds_multi_az        = true      # High availability
rds_backup_retention = 30       # 30-day backups
```

## Cost Monitoring and Alerts

### CloudWatch Billing Alerts
```bash
# Set up in terraform/main.tf
cost_alarm_threshold = 100  # Alert at $100/month
```

### AWS Cost Explorer Tags
All resources are tagged with:
- `Project`: finplan
- `Environment`: demo/staging/production
- `CostCenter`: For department billing
- `ManagedBy`: Terraform

### Monthly Cost Review Checklist
- [ ] Review Cost Explorer for anomalies
- [ ] Check for unused resources
- [ ] Verify auto-scaling is working
- [ ] Review data transfer costs
- [ ] Optimize log retention
- [ ] Clean up old ECR images
- [ ] Review snapshot retention

## Alternative Cost-Saving Architectures

### 1. Serverless Architecture (~$30/month)
Replace ECS with:
- **AWS Lambda**: Pay per request
- **API Gateway**: $3.50 per million requests
- **Aurora Serverless v2**: Auto-pause when idle

### 2. Single EC2 Instance (~$40/month)
Deploy everything on one EC2 instance:
- **t3.small instance**: $15/month (with Reserved Instance)
- **Application on Docker**: No ECS/Fargate costs
- **Local PostgreSQL**: No RDS costs
- **Local Redis**: No ElastiCache costs

### 3. Static Hosting Only (~$5/month)
For demos with mock data:
- **S3 Static Website**: $2/month
- **CloudFront CDN**: $3/month
- **No backend infrastructure**

## Cost Calculation Formula

```
Monthly Cost = 
  Fixed Costs (ALB, NAT Gateway if used) +
  Compute (ECS Tasks × Hours × Price) +
  Storage (RDS + S3 + EBS) +
  Data Transfer (CloudFront + ALB + Cross-AZ) +
  Management (CloudWatch + Systems Manager)
```

## AWS Pricing Calculator Links

- [Full Demo Environment Estimate](https://calculator.aws/#/estimate)
- [EC2 Pricing](https://aws.amazon.com/ec2/pricing/)
- [Fargate Pricing](https://aws.amazon.com/fargate/pricing/)
- [RDS Pricing](https://aws.amazon.com/rds/pricing/)
- [ElastiCache Pricing](https://aws.amazon.com/elasticache/pricing/)

## Budget Management Commands

```bash
# Create AWS Budget
aws budgets create-budget \
  --account-id $AWS_ACCOUNT_ID \
  --budget file://budget.json \
  --notifications-with-subscribers file://notifications.json

# Get current month costs
aws ce get-cost-and-usage \
  --time-period Start=$(date +%Y-%m-01),End=$(date +%Y-%m-%d) \
  --granularity MONTHLY \
  --metrics "UnblendedCost" \
  --group-by Type=DIMENSION,Key=SERVICE
```

## Tips for Staying Under $100/month

1. **Use Free Tier aggressively** in the first year
2. **Stop resources when not in use** (especially RDS)
3. **Use Spot instances** for all non-critical workloads
4. **Set up auto-shutdown** for non-business hours
5. **Monitor daily** with Cost Explorer
6. **Clean up unused resources** weekly
7. **Use S3 Lifecycle policies** to delete old data
8. **Optimize data transfer** by using CloudFront
9. **Right-size instances** based on actual usage
10. **Set billing alerts** at $50, $75, and $100