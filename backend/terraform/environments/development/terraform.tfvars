# Development Environment Configuration
# This file contains variable values specific to the development environment

# Basic Configuration
project_name = "financial-planning"
environment  = "development"
aws_region   = "us-west-2"
owner        = "development-team"
cost_center  = "engineering"

# Networking Configuration
vpc_cidr = "10.0.0.0/16"
enable_nat_gateway = true
enable_vpn_gateway = false

# Security Configuration
allowed_cidr_blocks = [
  "10.0.0.0/16",     # VPC CIDR
  "172.16.0.0/12",   # Private networks
  "192.168.0.0/16"   # Private networks
]

# EKS Configuration
eks_cluster_version = "1.28"
eks_cluster_endpoint_private_access = true
eks_cluster_endpoint_public_access = true

eks_node_groups = {
  general = {
    instance_types = ["t3.medium"]
    capacity_type  = "ON_DEMAND"
    
    scaling_config = {
      desired_size = 2
      max_size     = 4
      min_size     = 1
    }
    
    update_config = {
      max_unavailable_percentage = 25
    }
    
    disk_size = 20
    ami_type  = "AL2_x86_64"
    
    labels = {
      Environment = "development"
      NodeGroup   = "general"
    }
    
    taints = []
  }
}

# Database Configuration
database_name     = "financial_planning_dev"
database_username = "fp_admin"

rds_instance_class        = "db.t3.micro"
rds_engine_version       = "15.4"
rds_allocated_storage    = 20
rds_max_allocated_storage = 100
rds_backup_retention_period = 7
rds_backup_window        = "03:00-04:00"
rds_maintenance_window   = "sun:04:00-sun:05:00"
rds_multi_az            = false
rds_performance_insights_enabled = false
rds_monitoring_interval = 0

# Redis Configuration
redis_node_type           = "cache.t3.micro"
redis_num_cache_nodes     = 1
redis_parameter_group_name = "default.redis7"
redis_engine_version      = "7.0"
redis_port               = 6379

# Monitoring and Logging
enable_cloudwatch_logs = true
log_retention_days     = 14
enable_xray_tracing   = false

# Feature Flags
enable_backup_automation = false
enable_cost_optimization = true
enable_security_scanning = true
enable_performance_monitoring = false

# Development-specific settings
auto_shutdown_enabled = true
auto_shutdown_schedule = "0 22 * * 1-5"  # Shutdown at 10 PM on weekdays
auto_startup_schedule = "0 8 * * 1-5"    # Start at 8 AM on weekdays

# DNS and SSL
domain_name = "dev.financial-planning.internal"
enable_ssl  = false
certificate_arn = null

# Application Configuration
app_replicas = 1
app_cpu_requests = "100m"
app_memory_requests = "256Mi"
app_cpu_limits = "500m"
app_memory_limits = "512Mi"

# External Integrations
enable_plaid_integration = true
enable_yodlee_integration = false
enable_ai_features = true
enable_voice_interface = false

# Compliance and Security
data_retention_days = 90
encryption_at_rest = true
encryption_in_transit = true
enable_audit_logging = true

# Development Tools
enable_debug_mode = true
enable_hot_reload = true
enable_profiling = false