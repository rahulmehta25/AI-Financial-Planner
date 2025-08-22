# Variables for GCP Infrastructure

variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP region for deployment"
  type        = string
  default     = "us-central1"  # Cheapest region
}

variable "zone" {
  description = "GCP zone for deployment"
  type        = string
  default     = "us-central1-a"
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

# Cloud SQL Configuration
variable "db_tier" {
  description = "Cloud SQL instance tier"
  type        = string
  default     = "db-f1-micro"  # Cheapest option ~$8/month
}

# Cloud Run Configuration - Backend
variable "backend_cpu" {
  description = "CPU allocation for backend (e.g., '1', '2')"
  type        = string
  default     = "1"
}

variable "backend_memory" {
  description = "Memory allocation for backend (e.g., '512Mi', '1Gi')"
  type        = string
  default     = "512Mi"
}

variable "backend_min_instances" {
  description = "Minimum number of backend instances"
  type        = number
  default     = 0  # Scale to zero when not in use
}

variable "backend_max_instances" {
  description = "Maximum number of backend instances"
  type        = number
  default     = 3
}

# Cloud Run Configuration - Frontend
variable "frontend_cpu" {
  description = "CPU allocation for frontend"
  type        = string
  default     = "1"
}

variable "frontend_memory" {
  description = "Memory allocation for frontend"
  type        = string
  default     = "512Mi"
}

variable "frontend_min_instances" {
  description = "Minimum number of frontend instances"
  type        = number
  default     = 0  # Scale to zero when not in use
}

variable "frontend_max_instances" {
  description = "Maximum number of frontend instances"
  type        = number
  default     = 3
}

# Cost Monitoring
variable "cost_alert_threshold" {
  description = "Monthly cost threshold for alerts in USD"
  type        = number
  default     = 100
}

variable "notification_email" {
  description = "Email address for notifications"
  type        = string
  default     = ""
}