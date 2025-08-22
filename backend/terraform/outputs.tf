# Outputs for Financial Planning Infrastructure

# VPC Outputs
output "vpc_id" {
  description = "ID of the VPC"
  value       = module.networking.vpc_id
}

output "vpc_cidr_block" {
  description = "CIDR block of the VPC"
  value       = module.networking.vpc_cidr_block
}

output "public_subnet_ids" {
  description = "List of IDs of public subnets"
  value       = module.networking.public_subnet_ids
}

output "private_subnet_ids" {
  description = "List of IDs of private subnets"
  value       = module.networking.private_subnet_ids
}

output "database_subnet_ids" {
  description = "List of IDs of database subnets"
  value       = module.networking.database_subnet_ids
}

output "cache_subnet_ids" {
  description = "List of IDs of cache subnets"
  value       = module.networking.cache_subnet_ids
}

# EKS Outputs
output "cluster_name" {
  description = "EKS cluster name"
  value       = module.eks.cluster_name
}

output "cluster_endpoint" {
  description = "Endpoint for EKS control plane"
  value       = module.eks.cluster_endpoint
}

output "cluster_security_group_id" {
  description = "Security group ID attached to the EKS cluster"
  value       = module.eks.cluster_security_group_id
}

output "cluster_iam_role_name" {
  description = "IAM role name associated with EKS cluster"
  value       = module.eks.cluster_iam_role_name
}

output "cluster_iam_role_arn" {
  description = "IAM role ARN associated with EKS cluster"
  value       = module.eks.cluster_iam_role_arn
}

output "cluster_certificate_authority_data" {
  description = "Base64 encoded certificate data required to communicate with the cluster"
  value       = module.eks.cluster_certificate_authority_data
  sensitive   = true
}

output "cluster_version" {
  description = "The Kubernetes version for the EKS cluster"
  value       = module.eks.cluster_version
}

output "node_groups" {
  description = "EKS node groups"
  value       = module.eks.node_groups
}

# RDS Outputs
output "db_instance_endpoint" {
  description = "RDS instance endpoint"
  value       = module.rds.endpoint
  sensitive   = true
}

output "db_instance_hosted_zone_id" {
  description = "The hosted zone ID of the DB instance"
  value       = module.rds.hosted_zone_id
}

output "db_instance_id" {
  description = "RDS instance ID"
  value       = module.rds.id
}

output "db_instance_status" {
  description = "RDS instance status"
  value       = module.rds.status
}

output "db_subnet_group_name" {
  description = "The name of the DB subnet group"
  value       = module.rds.db_subnet_group_name
}

output "database_name" {
  description = "The name of the database"
  value       = var.database_name
}

output "database_username" {
  description = "The master username for the database"
  value       = var.database_username
  sensitive   = true
}

# Redis Outputs
output "redis_primary_endpoint" {
  description = "Address of the primary endpoint for the ElastiCache cluster"
  value       = module.redis.primary_endpoint
}

output "redis_configuration_endpoint" {
  description = "Address of the configuration endpoint for the ElastiCache cluster"
  value       = module.redis.configuration_endpoint
}

output "redis_port" {
  description = "The port number on which each of the cache nodes will accept connections"
  value       = module.redis.port
}

output "redis_security_group_id" {
  description = "The ID of the security group"
  value       = module.redis.security_group_id
}

# Security Outputs
output "eks_cluster_security_group_id" {
  description = "EKS cluster security group ID"
  value       = module.security.eks_cluster_security_group_id
}

output "eks_node_security_group_id" {
  description = "EKS node security group ID"
  value       = module.security.eks_node_security_group_id
}

output "rds_security_group_id" {
  description = "RDS security group ID"
  value       = module.security.rds_security_group_id
}

output "redis_security_group_id" {
  description = "Redis security group ID"
  value       = module.security.redis_security_group_id
}

# Application Outputs
output "kubernetes_namespace" {
  description = "Kubernetes namespace for the application"
  value       = kubernetes_namespace.financial_planning.metadata[0].name
}

# Connection Information
output "kubectl_config" {
  description = "kubectl config command to connect to the cluster"
  value       = "aws eks update-kubeconfig --region ${var.aws_region} --name ${module.eks.cluster_name}"
}

output "database_connection_string" {
  description = "Database connection string"
  value       = "postgresql://${var.database_username}:${random_password.db_password.result}@${module.rds.endpoint}:5432/${var.database_name}"
  sensitive   = true
}

output "redis_connection_string" {
  description = "Redis connection string"
  value       = "redis://:${random_password.redis_password.result}@${module.redis.primary_endpoint}:${var.redis_port}/0"
  sensitive   = true
}

# Environment Information
output "environment" {
  description = "Environment name"
  value       = var.environment
}

output "project_name" {
  description = "Project name"
  value       = var.project_name
}

output "aws_region" {
  description = "AWS region"
  value       = var.aws_region
}

# Monitoring and Observability
output "cloudwatch_log_group_name" {
  description = "CloudWatch log group name"
  value       = "/aws/eks/${module.eks.cluster_name}"
}

# Deployment Information
output "deployment_info" {
  description = "Information needed for deployment"
  value = {
    cluster_name               = module.eks.cluster_name
    cluster_endpoint          = module.eks.cluster_endpoint
    namespace                 = kubernetes_namespace.financial_planning.metadata[0].name
    database_endpoint         = module.rds.endpoint
    redis_endpoint           = module.redis.primary_endpoint
    vpc_id                   = module.networking.vpc_id
    private_subnet_ids       = module.networking.private_subnet_ids
    public_subnet_ids        = module.networking.public_subnet_ids
  }
  sensitive = true
}

# Cost Information
output "estimated_monthly_cost" {
  description = "Estimated monthly cost breakdown"
  value = {
    eks_cluster    = "~$73 (control plane)"
    node_groups    = "Varies based on instance types and count"
    rds           = "Starts at ~$13 for db.t3.micro"
    redis         = "Starts at ~$15 for cache.t3.micro"
    nat_gateway   = "~$45 per NAT Gateway"
    data_transfer = "Varies based on usage"
    note          = "Actual costs may vary based on usage patterns and AWS pricing changes"
  }
}

# Security Information
output "security_recommendations" {
  description = "Security recommendations for the deployment"
  value = [
    "Restrict allowed_cidr_blocks to specific IP ranges",
    "Enable VPC Flow Logs for network monitoring",
    "Implement AWS Config for compliance monitoring",
    "Set up AWS GuardDuty for threat detection",
    "Enable CloudTrail for API auditing",
    "Use AWS Secrets Manager for sensitive data",
    "Implement pod security policies/standards",
    "Enable network policies in Kubernetes"
  ]
}

# Backup Information
output "backup_configuration" {
  description = "Backup configuration information"
  value = {
    rds_automated_backups = "Enabled with ${var.rds_backup_retention_period} day retention"
    rds_backup_window    = var.rds_backup_window
    etcd_snapshots       = "Managed by AWS EKS"
    recommendations      = [
      "Set up cross-region backup replication for disaster recovery",
      "Implement application-level backup strategies",
      "Test restore procedures regularly"
    ]
  }
}