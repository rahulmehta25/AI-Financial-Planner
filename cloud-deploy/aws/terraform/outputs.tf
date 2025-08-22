# Terraform Outputs

output "alb_dns_name" {
  description = "DNS name of the Application Load Balancer"
  value       = aws_lb.main.dns_name
}

output "alb_url" {
  description = "URL to access the application"
  value       = "http://${aws_lb.main.dns_name}"
}

output "cloudfront_domain" {
  description = "CloudFront distribution domain for static assets"
  value       = aws_cloudfront_distribution.static.domain_name
}

output "ecr_backend_repository" {
  description = "ECR repository URL for backend"
  value       = aws_ecr_repository.backend.repository_url
}

output "ecr_frontend_repository" {
  description = "ECR repository URL for frontend"
  value       = aws_ecr_repository.frontend.repository_url
}

output "rds_endpoint" {
  description = "RDS instance endpoint"
  value       = aws_db_instance.postgres.endpoint
  sensitive   = true
}

output "redis_endpoint" {
  description = "Redis cluster endpoint"
  value       = aws_elasticache_cluster.redis.cache_nodes[0].address
  sensitive   = true
}

output "s3_bucket" {
  description = "S3 bucket for static assets"
  value       = aws_s3_bucket.static.id
}

output "ecs_cluster_name" {
  description = "ECS cluster name"
  value       = aws_ecs_cluster.main.name
}

output "backend_service_name" {
  description = "Backend ECS service name"
  value       = aws_ecs_service.backend.name
}

output "frontend_service_name" {
  description = "Frontend ECS service name"
  value       = aws_ecs_service.frontend.name
}

output "estimated_monthly_cost" {
  description = "Estimated monthly cost breakdown"
  value = {
    alb             = "$18/month (Application Load Balancer)"
    rds             = "$15/month (db.t3.micro after free tier)"
    redis           = "$13/month (cache.t3.micro)"
    ecs_fargate     = "$20/month (2x 0.25 vCPU @ spot pricing)"
    cloudfront      = "$5/month (estimated for demo traffic)"
    s3              = "$2/month (estimated for static assets)"
    data_transfer   = "$10/month (estimated egress)"
    logs            = "$2/month (CloudWatch logs with 7-day retention)"
    total_estimated = "$85/month"
    notes           = "Costs can be reduced further by using Lambda instead of Fargate for low traffic"
  }
}

output "cost_optimization_tips" {
  description = "Tips to reduce costs further"
  value = [
    "1. Use AWS Free Tier for first 12 months (saves ~$30/month)",
    "2. Stop RDS instance when not in use (saves $15/month)",
    "3. Use Lambda@Edge instead of ECS for very low traffic (saves $15/month)",
    "4. Reduce log retention to 3 days (saves $1/month)",
    "5. Use S3 static hosting instead of CloudFront for demo (saves $5/month)",
    "6. Schedule auto-shutdown for non-business hours (saves 60% on compute)"
  ]
}

output "deployment_instructions" {
  description = "Next steps for deployment"
  value = <<-EOT
    1. Configure AWS credentials:
       export AWS_ACCESS_KEY_ID=your-key
       export AWS_SECRET_ACCESS_KEY=your-secret
    
    2. Initialize Terraform:
       terraform init
    
    3. Review the plan:
       terraform plan
    
    4. Apply infrastructure:
       terraform apply
    
    5. Build and push Docker images:
       ./scripts/deploy-aws.sh
    
    6. Access application:
       ${aws_lb.main.dns_name}
  EOT
}