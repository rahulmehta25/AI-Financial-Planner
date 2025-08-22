# Production Environment Configuration
# This file contains variable values specific to the production environment

# Basic Configuration
project_name = "financial-planning"
environment  = "production"
aws_region   = "us-west-2"
owner        = "platform-team"
cost_center  = "product"

# Cross-account deployment (if applicable)
assume_role_arn = "arn:aws:iam::PROD-ACCOUNT-ID:role/TerraformDeploymentRole"

# Networking Configuration
vpc_cidr = "10.2.0.0/16"
enable_nat_gateway = true
enable_vpn_gateway = true

# Security Configuration
allowed_cidr_blocks = [
  "10.2.0.0/16",     # Production VPC CIDR
  "10.100.0.0/16",   # Corporate network
]

# EKS Configuration
eks_cluster_version = "1.28"
eks_cluster_endpoint_private_access = true
eks_cluster_endpoint_public_access = false  # Private cluster for production

eks_node_groups = {
  general = {
    instance_types = ["m5.large", "m5.xlarge"]
    capacity_type  = "ON_DEMAND"
    
    scaling_config = {
      desired_size = 3
      max_size     = 10
      min_size     = 3
    }
    
    update_config = {
      max_unavailable_percentage = 25
    }
    
    disk_size = 100
    ami_type  = "AL2_x86_64"
    
    labels = {
      Environment = "production"
      NodeGroup   = "general"
    }
    
    taints = []
  }
  
  compute = {
    instance_types = ["c5.xlarge", "c5.2xlarge"]
    capacity_type  = "ON_DEMAND"
    
    scaling_config = {
      desired_size = 2
      max_size     = 8
      min_size     = 2
    }
    
    update_config = {
      max_unavailable_percentage = 25
    }
    
    disk_size = 200
    ami_type  = "AL2_x86_64"
    
    labels = {
      Environment = "production"
      NodeGroup   = "compute"
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
  
  memory = {
    instance_types = ["r5.large", "r5.xlarge"]
    capacity_type  = "ON_DEMAND"
    
    scaling_config = {
      desired_size = 2
      max_size     = 6
      min_size     = 2
    }
    
    update_config = {
      max_unavailable_percentage = 25
    }
    
    disk_size = 100
    ami_type  = "AL2_x86_64"
    
    labels = {
      Environment = "production"
      NodeGroup   = "memory"
      WorkloadType = "memory-intensive"
    }
    
    taints = [
      {
        key    = "workload-type"
        value  = "memory-intensive"
        effect = "NO_SCHEDULE"
      }
    ]
  }
}

# Database Configuration - Multi-AZ with Read Replicas
database_name     = "financial_planning_prod"
database_username = "fp_admin"

rds_instance_class        = "db.r5.large"
rds_engine_version       = "15.4"
rds_allocated_storage    = 500
rds_max_allocated_storage = 5000
rds_backup_retention_period = 30
rds_backup_window        = "03:00-04:00"
rds_maintenance_window   = "sun:04:00-sun:06:00"
rds_multi_az            = true
rds_performance_insights_enabled = true
rds_monitoring_interval = 15

# Read Replicas Configuration
enable_read_replicas = true
read_replica_config = {
  count           = 2
  instance_class  = "db.r5.large"
  multi_az        = true
  regions        = ["us-east-1", "us-west-1"]
}

# Redis Configuration - Cluster Mode
redis_node_type           = "cache.r5.large"
redis_num_cache_nodes     = 3
redis_parameter_group_name = "default.redis7.cluster.on"
redis_engine_version      = "7.0"
redis_port               = 6379
redis_cluster_mode       = true
redis_num_node_groups    = 3
redis_replicas_per_node_group = 2

# Monitoring and Logging
enable_cloudwatch_logs = true
log_retention_days     = 365  # 1 year retention for production
enable_xray_tracing   = true
enable_enhanced_monitoring = true

# Advanced Monitoring
enable_prometheus = true
enable_grafana = true
enable_jaeger = true
enable_elastic_apm = true

# Feature Flags
enable_backup_automation = true
enable_cost_optimization = false  # Disable aggressive cost optimization in prod
enable_security_scanning = true
enable_performance_monitoring = true

# Production-specific settings
auto_shutdown_enabled = false
auto_shutdown_schedule = null
auto_startup_schedule = null

# DNS and SSL
domain_name = "financial-planning.com"
enable_ssl  = true
certificate_arn = "arn:aws:acm:us-west-2:${data.aws_caller_identity.current.account_id}:certificate/prod-cert-id"

# Application Configuration - High Availability
app_replicas = 5
app_cpu_requests = "500m"
app_memory_requests = "1Gi"
app_cpu_limits = "2000m"
app_memory_limits = "4Gi"

# Horizontal Pod Autoscaling
enable_hpa = true
hpa_config = {
  min_replicas = 5
  max_replicas = 50
  cpu_utilization = 70
  memory_utilization = 80
  scale_up_stabilization = "0s"
  scale_down_stabilization = "300s"
}

# Vertical Pod Autoscaling
enable_vpa = true
vpa_config = {
  update_mode = "Auto"
  resource_policy = {
    cpu_min = "100m"
    cpu_max = "4000m"
    memory_min = "256Mi"
    memory_max = "8Gi"
  }
}

# External Integrations
enable_plaid_integration = true
enable_yodlee_integration = true
enable_ai_features = true
enable_voice_interface = true

# Compliance and Security
data_retention_days = 2555  # 7 years for financial data compliance
encryption_at_rest = true
encryption_in_transit = true
enable_audit_logging = true
enable_compliance_monitoring = true

# Backup and Disaster Recovery
enable_cross_region_backup = true
backup_regions = ["us-east-1"]
disaster_recovery_enabled = true
rpo_target_minutes = 15  # Recovery Point Objective
rto_target_minutes = 60  # Recovery Time Objective

# Blue-Green Deployment
enable_blue_green = true
blue_green_settings = {
  traffic_shift_percentage = 5
  evaluation_period = "10m"
  success_threshold = 99
  automatic_rollback = true
  rollback_threshold = 95
}

# Canary Deployment
enable_canary = true
canary_settings = {
  initial_weight = 5
  weight_increment = 5
  increment_interval = "2m"
  success_threshold = 99
  max_weight = 50
}

# Circuit Breaker
enable_circuit_breaker = true
circuit_breaker_config = {
  failure_threshold = 5
  timeout = "60s"
  max_requests = 10
}

# Rate Limiting
enable_rate_limiting = true
rate_limit_config = {
  requests_per_minute = 1000
  burst_size = 2000
  exempt_paths = ["/health", "/metrics"]
}

# CDN Configuration
enable_cdn = true
cdn_config = {
  price_class = "PriceClass_All"
  cache_behaviors = [
    {
      path_pattern = "/static/*"
      ttl = 86400  # 24 hours
    },
    {
      path_pattern = "/api/*"
      ttl = 0  # No caching for API
    }
  ]
}

# WAF Configuration
enable_waf = true
waf_rules = [
  "AWSManagedRulesCommonRuleSet",
  "AWSManagedRulesKnownBadInputsRuleSet",
  "AWSManagedRulesSQLiRuleSet",
  "AWSManagedRulesLinuxRuleSet",
  "AWSManagedRulesUnixRuleSet"
]

# Development Tools (disabled in production)
enable_debug_mode = false
enable_hot_reload = false
enable_profiling = false

# Cost Management
enable_cost_alerts = true
cost_budgets = [
  {
    name = "monthly-infrastructure"
    amount = 5000
    unit = "USD"
    time_period = "MONTHLY"
    threshold = 80
  },
  {
    name = "quarterly-total"
    amount = 45000
    unit = "USD"
    time_period = "QUARTERLY"
    threshold = 90
  }
]

# Compliance Tags
compliance_tags = {
  DataClassification = "Confidential"
  DataRetention = "7years"
  ComplianceFramework = "SOC2,PCI-DSS"
  BusinessCriticality = "High"
  SupportLevel = "24x7"
}