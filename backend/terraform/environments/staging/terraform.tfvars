# Staging Environment Configuration
# This file contains variable values specific to the staging environment

# Basic Configuration
project_name = "financial-planning"
environment  = "staging"
aws_region   = "us-west-2"
owner        = "qa-team"
cost_center  = "engineering"

# Networking Configuration
vpc_cidr = "10.1.0.0/16"
enable_nat_gateway = true
enable_vpn_gateway = false

# Security Configuration
allowed_cidr_blocks = [
  "10.1.0.0/16",     # VPC CIDR
  "10.0.0.0/16",     # Development VPC for testing
  "172.16.0.0/12",   # Private networks
  "192.168.0.0/16"   # Private networks
]

# EKS Configuration
eks_cluster_version = "1.28"
eks_cluster_endpoint_private_access = true
eks_cluster_endpoint_public_access = true

eks_node_groups = {
  general = {
    instance_types = ["t3.large"]
    capacity_type  = "ON_DEMAND"
    
    scaling_config = {
      desired_size = 2
      max_size     = 6
      min_size     = 2
    }
    
    update_config = {
      max_unavailable_percentage = 25
    }
    
    disk_size = 50
    ami_type  = "AL2_x86_64"
    
    labels = {
      Environment = "staging"
      NodeGroup   = "general"
    }
    
    taints = []
  }
  
  performance = {
    instance_types = ["c5.large"]
    capacity_type  = "SPOT"
    
    scaling_config = {
      desired_size = 1
      max_size     = 3
      min_size     = 0
    }
    
    update_config = {
      max_unavailable_percentage = 50
    }
    
    disk_size = 100
    ami_type  = "AL2_x86_64"
    
    labels = {
      Environment = "staging"
      NodeGroup   = "performance"
      WorkloadType = "compute-intensive"
    }
    
    taints = [
      {
        key    = "workload-type"
        value  = "compute-intensive"
        effect = "NO_SCHEDULE"
      }
    ]
  }
}

# Database Configuration
database_name     = "financial_planning_staging"
database_username = "fp_admin"

rds_instance_class        = "db.t3.small"
rds_engine_version       = "15.4"
rds_allocated_storage    = 50
rds_max_allocated_storage = 500
rds_backup_retention_period = 14
rds_backup_window        = "03:00-04:00"
rds_maintenance_window   = "sun:04:00-sun:05:00"
rds_multi_az            = true
rds_performance_insights_enabled = true
rds_monitoring_interval = 60

# Redis Configuration
redis_node_type           = "cache.t3.small"
redis_num_cache_nodes     = 2
redis_parameter_group_name = "default.redis7"
redis_engine_version      = "7.0"
redis_port               = 6379

# Monitoring and Logging
enable_cloudwatch_logs = true
log_retention_days     = 30
enable_xray_tracing   = true

# Feature Flags
enable_backup_automation = true
enable_cost_optimization = true
enable_security_scanning = true
enable_performance_monitoring = true

# Staging-specific settings
auto_shutdown_enabled = false
auto_shutdown_schedule = null
auto_startup_schedule = null

# DNS and SSL
domain_name = "staging.financial-planning.com"
enable_ssl  = true
certificate_arn = "arn:aws:acm:us-west-2:${data.aws_caller_identity.current.account_id}:certificate/staging-cert-id"

# Application Configuration
app_replicas = 2
app_cpu_requests = "200m"
app_memory_requests = "512Mi"
app_cpu_limits = "1000m"
app_memory_limits = "1Gi"

# External Integrations
enable_plaid_integration = true
enable_yodlee_integration = true
enable_ai_features = true
enable_voice_interface = true

# Compliance and Security
data_retention_days = 365
encryption_at_rest = true
encryption_in_transit = true
enable_audit_logging = true

# Load Testing Configuration
enable_load_testing = true
load_test_schedules = [
  {
    name = "daily-load-test"
    schedule = "0 2 * * *"  # Daily at 2 AM
    duration = "30m"
    users = 100
  },
  {
    name = "weekly-stress-test"
    schedule = "0 3 * * 0"  # Weekly on Sunday at 3 AM
    duration = "2h"
    users = 500
  }
]

# Blue-Green Deployment
enable_blue_green = true
blue_green_settings = {
  traffic_shift_percentage = 10
  evaluation_period = "5m"
  success_threshold = 95
}

# Development Tools
enable_debug_mode = false
enable_hot_reload = false
enable_profiling = true