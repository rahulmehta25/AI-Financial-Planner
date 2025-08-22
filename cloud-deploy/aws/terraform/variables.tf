# Variables for AWS Infrastructure

variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
  default     = "us-east-1"  # Cheapest region for most services
}

variable "environment" {
  description = "Environment name (demo, staging, production)"
  type        = string
  default     = "demo"
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "finplan"
}

variable "cost_center" {
  description = "Cost center for billing tags"
  type        = string
  default     = "demo"
}

# RDS Configuration
variable "rds_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.micro"  # Free tier eligible, ~$15/month after
}

# Redis Configuration
variable "redis_node_type" {
  description = "ElastiCache node type"
  type        = string
  default     = "cache.t3.micro"  # ~$13/month
}

# ECS Configuration - Backend
variable "backend_cpu" {
  description = "CPU units for backend task (256, 512, 1024, 2048, 4096)"
  type        = string
  default     = "256"  # Minimum for Fargate
}

variable "backend_memory" {
  description = "Memory for backend task in MB"
  type        = string
  default     = "512"  # Minimum for 256 CPU
}

variable "backend_desired_count" {
  description = "Desired number of backend tasks"
  type        = number
  default     = 1
}

variable "backend_min_capacity" {
  description = "Minimum number of backend tasks for auto-scaling"
  type        = number
  default     = 1
}

variable "backend_max_capacity" {
  description = "Maximum number of backend tasks for auto-scaling"
  type        = number
  default     = 3
}

# ECS Configuration - Frontend
variable "frontend_cpu" {
  description = "CPU units for frontend task"
  type        = string
  default     = "256"
}

variable "frontend_memory" {
  description = "Memory for frontend task in MB"
  type        = string
  default     = "512"
}

variable "frontend_desired_count" {
  description = "Desired number of frontend tasks"
  type        = number
  default     = 1
}

variable "frontend_min_capacity" {
  description = "Minimum number of frontend tasks for auto-scaling"
  type        = number
  default     = 1
}

variable "frontend_max_capacity" {
  description = "Maximum number of frontend tasks for auto-scaling"
  type        = number
  default     = 3
}

# Application Configuration
variable "cors_origins" {
  description = "CORS allowed origins"
  type        = string
  default     = "*"
}

variable "api_url" {
  description = "API URL for frontend"
  type        = string
  default     = ""  # Will be set to ALB URL
}

variable "certificate_arn" {
  description = "ACM certificate ARN for HTTPS (optional)"
  type        = string
  default     = ""
}

# Cost Monitoring
variable "cost_alarm_threshold" {
  description = "Monthly cost threshold for alarm in USD"
  type        = number
  default     = 100
}

variable "alarm_email" {
  description = "Email address for cost alarms"
  type        = string
  default     = ""
}