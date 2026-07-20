# VPC Outputs
output "vpc_id" {
  description = "ID of the VPC"
  value       = module.vpc.vpc_id
}

output "vpc_cidr_block" {
  description = "CIDR block of the VPC"
  value       = module.vpc.vpc_cidr_block
}

output "private_subnet_ids" {
  description = "List of IDs of private subnets"
  value       = module.vpc.private_subnets
}

output "public_subnet_ids" {
  description = "List of IDs of public subnets"
  value       = module.vpc.public_subnets
}

output "database_subnet_ids" {
  description = "List of IDs of database subnets"
  value       = module.vpc.database_subnets
}

output "nat_gateway_ips" {
  description = "List of public Elastic IPs created for AWS NAT Gateway"
  value       = module.vpc.nat_public_ips
}

# EKS Outputs
output "eks_cluster_id" {
  description = "EKS cluster ID"
  value       = module.eks.cluster_id
}

output "eks_cluster_arn" {
  description = "EKS cluster ARN"
  value       = module.eks.cluster_arn
}

output "eks_cluster_endpoint" {
  description = "Endpoint for EKS control plane"
  value       = module.eks.cluster_endpoint
}

output "eks_cluster_security_group_id" {
  description = "Security group ID attached to the EKS cluster"
  value       = module.eks.cluster_security_group_id
}

output "eks_cluster_iam_role_name" {
  description = "IAM role name associated with EKS cluster"
  value       = module.eks.cluster_iam_role_name
}

output "eks_cluster_iam_role_arn" {
  description = "IAM role ARN associated with EKS cluster"
  value       = module.eks.cluster_iam_role_arn
}

output "eks_cluster_certificate_authority_data" {
  description = "Base64 encoded certificate data required to communicate with the cluster"
  value       = module.eks.cluster_certificate_authority_data
}

output "eks_cluster_primary_security_group_id" {
  description = "Cluster security group that was created by Amazon EKS for the cluster"
  value       = module.eks.cluster_primary_security_group_id
}

output "eks_node_groups" {
  description = "EKS node groups"
  value       = module.eks.eks_managed_node_groups
  sensitive   = true
}

output "eks_oidc_issuer_url" {
  description = "The URL on the EKS cluster OIDC Issuer"
  value       = module.eks.cluster_oidc_issuer_url
}

# RDS Outputs
output "rds_endpoint" {
  description = "RDS instance endpoint"
  value       = module.rds.db_instance_endpoint
  sensitive   = true
}

output "rds_port" {
  description = "RDS instance port"
  value       = module.rds.db_instance_port
}

output "rds_database_name" {
  description = "RDS database name"
  value       = module.rds.db_instance_name
}

output "rds_username" {
  description = "RDS database username"
  value       = module.rds.db_instance_username
  sensitive   = true
}

output "rds_instance_id" {
  description = "RDS instance ID"
  value       = module.rds.db_instance_id
}

output "rds_instance_arn" {
  description = "RDS instance ARN"
  value       = module.rds.db_instance_arn
}

output "rds_security_group_id" {
  description = "RDS security group ID"
  value       = aws_security_group.rds.id
}

# ElastiCache Redis Outputs
output "redis_endpoint" {
  description = "Redis cluster endpoint"
  value       = module.redis.cluster_address
  sensitive   = true
}

output "redis_port" {
  description = "Redis cluster port"
  value       = module.redis.port
}

output "redis_cluster_id" {
  description = "Redis cluster ID"
  value       = module.redis.cluster_id
}

output "redis_security_group_id" {
  description = "Redis security group ID"
  value       = aws_security_group.redis.id
}

# S3 Bucket Outputs
output "s3_bucket_names" {
  description = "Names of S3 buckets"
  value       = module.s3_buckets.bucket_names
}

output "s3_bucket_arns" {
  description = "ARNs of S3 buckets"
  value       = module.s3_buckets.bucket_arns
}

output "s3_bucket_domain_names" {
  description = "Domain names of S3 buckets"
  value       = module.s3_buckets.bucket_domain_names
}

# Load Balancer Outputs
output "alb_arn" {
  description = "ARN of the load balancer"
  value       = module.alb.lb_arn
}

output "alb_dns_name" {
  description = "DNS name of the load balancer"
  value       = module.alb.lb_dns_name
}

output "alb_zone_id" {
  description = "Zone ID of the load balancer"
  value       = module.alb.lb_zone_id
}

output "alb_security_group_id" {
  description = "Security group ID of the load balancer"
  value       = aws_security_group.alb.id
}

output "target_group_arns" {
  description = "ARNs of the target groups"
  value       = module.alb.target_group_arns
}

# WAF Outputs
output "waf_web_acl_id" {
  description = "WAF WebACL ID"
  value       = aws_wafv2_web_acl.main.id
}

output "waf_web_acl_arn" {
  description = "WAF WebACL ARN"
  value       = aws_wafv2_web_acl.main.arn
}

# KMS Key Outputs
output "eks_kms_key_id" {
  description = "EKS KMS key ID"
  value       = aws_kms_key.eks.key_id
}

output "eks_kms_key_arn" {
  description = "EKS KMS key ARN"
  value       = aws_kms_key.eks.arn
}

output "rds_kms_key_id" {
  description = "RDS KMS key ID"
  value       = aws_kms_key.rds.key_id
}

output "rds_kms_key_arn" {
  description = "RDS KMS key ARN"
  value       = aws_kms_key.rds.arn
}

# DNS and Certificate Outputs
output "route53_zone_id" {
  description = "Route53 hosted zone ID"
  value       = var.ssl_certificate_arn != "" ? data.aws_route53_zone.main[0].zone_id : null
}

# Security Group Outputs
output "worker_security_group_id" {
  description = "Worker node security group ID"
  value       = aws_security_group.worker_group_mgmt.id
}

output "vpc_endpoint_security_group_id" {
  description = "VPC endpoint security group ID"
  value       = aws_security_group.vpc_endpoint.id
}

# Monitoring and Logging Outputs
output "cloudwatch_log_group_names" {
  description = "CloudWatch log group names"
  value = {
    vpc_flow_logs = module.vpc.vpc_flow_log_cloudwatch_log_group_name
    eks_cluster   = "/aws/eks/${module.eks.cluster_id}/cluster"
  }
}

# Application Configuration Outputs
output "database_connection_string" {
  description = "Database connection string (without password)"
  value       = "postgresql://${module.rds.db_instance_username}@${module.rds.db_instance_endpoint}:${module.rds.db_instance_port}/${module.rds.db_instance_name}"
  sensitive   = true
}

output "redis_connection_string" {
  description = "Redis connection string"
  value       = "redis://${module.redis.cluster_address}:${module.redis.port}/0"
  sensitive   = true
}

# Kubernetes Configuration
output "kubectl_config" {
  description = "kubectl config as generated by the module"
  value = templatefile("${path.module}/templates/kubeconfig.tpl", {
    cluster_name                      = module.eks.cluster_id
    cluster_endpoint                  = module.eks.cluster_endpoint
    cluster_certificate_authority_data = module.eks.cluster_certificate_authority_data
    aws_region                        = var.aws_region
  })
  sensitive = true
}

# Helm Values
output "helm_values" {
  description = "Helm values for application deployment"
  value = {
    image = {
      tag = "latest"
    }
    database = {
      host     = module.rds.db_instance_endpoint
      port     = module.rds.db_instance_port
      name     = module.rds.db_instance_name
      username = module.rds.db_instance_username
    }
    redis = {
      host = module.redis.cluster_address
      port = module.redis.port
    }
    ingress = {
      host        = "${var.api_subdomain}.${var.domain_name}"
      certificate_arn = var.ssl_certificate_arn
    }
    resources = {
      api = {
        min_replicas = var.api_min_replicas
        max_replicas = var.api_max_replicas
      }
      worker = {
        min_replicas = var.worker_min_replicas
        max_replicas = var.worker_max_replicas
      }
      ml = {
        min_replicas = var.ml_min_replicas
        max_replicas = var.ml_max_replicas
      }
    }
  }
  sensitive = true
}

# Cost Tracking
output "estimated_monthly_cost" {
  description = "Estimated monthly cost breakdown"
  value = {
    eks_cluster      = "240"  # Control plane
    eks_nodes        = "1200" # 8 nodes average
    rds_instance     = "800"  # db.r6g.2xlarge
    redis_cache      = "400"  # cache.r6g.xlarge x3
    load_balancer    = "25"   # ALB
    nat_gateways     = "135"  # 3 NAT gateways
    s3_storage       = "50"   # Estimated storage
    data_transfer    = "100"  # Estimated transfer
    cloudwatch_logs  = "50"   # Log storage
    total_usd        = "3000" # Approximate total
  }
}

# Environment Information
output "environment_info" {
  description = "Environment information"
  value = {
    project_name = var.project_name
    environment  = var.environment
    aws_region   = var.aws_region
    deployed_at  = timestamp()
    terraform_version = "~> 1.5"
  }
}

# Data sources for additional outputs
data "aws_route53_zone" "main" {
  count = var.ssl_certificate_arn != "" ? 1 : 0
  name  = var.domain_name
}

# Security and Compliance
output "security_configuration" {
  description = "Security configuration summary"
  value = {
    waf_enabled                = var.enable_waf
    encryption_at_rest_enabled = true
    encryption_in_transit_enabled = true
    vpc_flow_logs_enabled      = var.enable_vpc_flow_logs
    cloudtrail_enabled         = var.enable_cloudtrail
    guardduty_enabled          = var.enable_guardduty
  }
}

# Backup and Recovery
output "backup_configuration" {
  description = "Backup configuration summary"
  value = {
    rds_backup_retention_days    = var.db_backup_retention_period
    redis_snapshot_retention_days = 7
    cross_region_backup_enabled = var.enable_cross_region_backup
    backup_region               = var.backup_region
  }
}