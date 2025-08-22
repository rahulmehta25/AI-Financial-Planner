# Enhanced Variables for Multi-Environment Financial Planning Infrastructure
# This file extends the existing variables with advanced configuration options

# Git and Deployment Tracking
variable "git_commit" {
  description = "Git commit SHA for deployment tracking"
  type        = string
  default     = ""
}

variable "deployed_by" {
  description = "User or system that deployed this infrastructure"
  type        = string
  default     = "terraform"
}

variable "assume_role_arn" {
  description = "ARN of the role to assume for cross-account deployments"
  type        = string
  default     = null
}

# Advanced Networking
variable "enable_flow_logs" {
  description = "Enable VPC Flow Logs"
  type        = bool
  default     = true
}

variable "flow_logs_retention" {
  description = "CloudWatch Logs retention period for VPC Flow Logs"
  type        = number
  default     = 14
}

variable "enable_transit_gateway" {
  description = "Enable AWS Transit Gateway for multi-VPC connectivity"
  type        = bool
  default     = false
}

# Enhanced Security
variable "enable_guardduty" {
  description = "Enable AWS GuardDuty for threat detection"
  type        = bool
  default     = true
}

variable "enable_security_hub" {
  description = "Enable AWS Security Hub for security posture management"
  type        = bool
  default     = true
}

variable "enable_config" {
  description = "Enable AWS Config for compliance monitoring"
  type        = bool
  default     = true
}

variable "kms_key_rotation" {
  description = "Enable automatic KMS key rotation"
  type        = bool
  default     = true
}

# Enhanced EKS Configuration
variable "enable_irsa" {
  description = "Enable IAM Roles for Service Accounts (IRSA)"
  type        = bool
  default     = true
}

variable "enable_pod_security_policy" {
  description = "Enable Pod Security Policy"
  type        = bool
  default     = true
}

variable "enable_network_policy" {
  description = "Enable Kubernetes Network Policies"
  type        = bool
  default     = true
}

variable "enable_secrets_encryption" {
  description = "Enable etcd secrets encryption"
  type        = bool
  default     = true
}

variable "enable_cluster_autoscaler" {
  description = "Enable cluster autoscaler"
  type        = bool
  default     = true
}

variable "enable_aws_load_balancer_controller" {
  description = "Enable AWS Load Balancer Controller"
  type        = bool
  default     = true
}

variable "enable_external_dns" {
  description = "Enable External DNS controller"
  type        = bool
  default     = true
}

variable "enable_cert_manager" {
  description = "Enable cert-manager for SSL certificate automation"
  type        = bool
  default     = true
}

# Advanced RDS Configuration
variable "enable_read_replicas" {
  description = "Enable RDS read replicas"
  type        = bool
  default     = false
}

variable "read_replica_config" {
  description = "Configuration for RDS read replicas"
  type = object({
    count          = number
    instance_class = string
    multi_az       = bool
    regions        = list(string)
  })
  default = {
    count          = 0
    instance_class = "db.t3.micro"
    multi_az       = false
    regions        = []
  }
}

variable "enable_rds_proxy" {
  description = "Enable RDS Proxy for connection pooling"
  type        = bool
  default     = false
}

variable "enable_aurora" {
  description = "Use Aurora instead of standard RDS"
  type        = bool
  default     = false
}

variable "aurora_config" {
  description = "Aurora cluster configuration"
  type = object({
    engine_mode             = string
    min_capacity           = number
    max_capacity           = number
    auto_pause             = bool
    seconds_until_auto_pause = number
  })
  default = {
    engine_mode             = "serverless"
    min_capacity           = 2
    max_capacity           = 16
    auto_pause             = true
    seconds_until_auto_pause = 300
  }
}

# Advanced Redis Configuration
variable "redis_cluster_mode" {
  description = "Enable Redis cluster mode"
  type        = bool
  default     = false
}

variable "redis_num_node_groups" {
  description = "Number of node groups for Redis cluster"
  type        = number
  default     = 1
}

variable "redis_replicas_per_node_group" {
  description = "Number of replica nodes per node group"
  type        = number
  default     = 1
}

variable "enable_redis_auth" {
  description = "Enable Redis AUTH"
  type        = bool
  default     = true
}

# Application Scaling Configuration
variable "enable_hpa" {
  description = "Enable Horizontal Pod Autoscaler"
  type        = bool
  default     = true
}

variable "hpa_config" {
  description = "HPA configuration"
  type = object({
    min_replicas                = number
    max_replicas                = number
    cpu_utilization            = number
    memory_utilization         = number
    scale_up_stabilization     = string
    scale_down_stabilization   = string
  })
  default = {
    min_replicas                = 2
    max_replicas                = 10
    cpu_utilization            = 70
    memory_utilization         = 80
    scale_up_stabilization     = "0s"
    scale_down_stabilization   = "300s"
  }
}

variable "enable_vpa" {
  description = "Enable Vertical Pod Autoscaler"
  type        = bool
  default     = false
}

variable "vpa_config" {
  description = "VPA configuration"
  type = object({
    update_mode = string
    resource_policy = object({
      cpu_min    = string
      cpu_max    = string
      memory_min = string
      memory_max = string
    })
  })
  default = {
    update_mode = "Off"
    resource_policy = {
      cpu_min    = "100m"
      cpu_max    = "2000m"
      memory_min = "256Mi"
      memory_max = "2Gi"
    }
  }
}

# Resource Limits
variable "app_cpu_requests" {
  description = "CPU requests for application pods"
  type        = string
  default     = "100m"
}

variable "app_memory_requests" {
  description = "Memory requests for application pods"
  type        = string
  default     = "256Mi"
}

variable "app_cpu_limits" {
  description = "CPU limits for application pods"
  type        = string
  default     = "1000m"
}

variable "app_memory_limits" {
  description = "Memory limits for application pods"
  type        = string
  default     = "1Gi"
}

variable "app_replicas" {
  description = "Number of application replicas"
  type        = number
  default     = 3
}

# Monitoring and Observability
variable "enable_prometheus" {
  description = "Enable Prometheus monitoring"
  type        = bool
  default     = true
}

variable "enable_grafana" {
  description = "Enable Grafana dashboards"
  type        = bool
  default     = true
}

variable "enable_jaeger" {
  description = "Enable Jaeger distributed tracing"
  type        = bool
  default     = false
}

variable "enable_elastic_apm" {
  description = "Enable Elastic APM"
  type        = bool
  default     = false
}

variable "enable_cloudwatch_logs" {
  description = "Enable CloudWatch Logs"
  type        = bool
  default     = true
}

variable "log_retention_days" {
  description = "CloudWatch Logs retention period"
  type        = number
  default     = 30
}

variable "enable_xray_tracing" {
  description = "Enable AWS X-Ray tracing"
  type        = bool
  default     = false
}

variable "enable_enhanced_monitoring" {
  description = "Enable enhanced monitoring for all resources"
  type        = bool
  default     = false
}

# Backup and Disaster Recovery
variable "enable_backup_automation" {
  description = "Enable automated backup solutions"
  type        = bool
  default     = true
}

variable "enable_cross_region_backup" {
  description = "Enable cross-region backup replication"
  type        = bool
  default     = false
}

variable "backup_regions" {
  description = "List of regions for backup replication"
  type        = list(string)
  default     = []
}

variable "disaster_recovery_enabled" {
  description = "Enable disaster recovery setup"
  type        = bool
  default     = false
}

variable "rpo_target_minutes" {
  description = "Recovery Point Objective in minutes"
  type        = number
  default     = 60
}

variable "rto_target_minutes" {
  description = "Recovery Time Objective in minutes"
  type        = number
  default     = 240
}

# CI/CD Integration
variable "enable_blue_green" {
  description = "Enable blue-green deployment support"
  type        = bool
  default     = false
}

variable "blue_green_settings" {
  description = "Blue-green deployment configuration"
  type = object({
    traffic_shift_percentage = number
    evaluation_period       = string
    success_threshold       = number
    automatic_rollback      = optional(bool, false)
    rollback_threshold      = optional(number, 90)
  })
  default = {
    traffic_shift_percentage = 10
    evaluation_period       = "5m"
    success_threshold       = 95
  }
}

variable "enable_canary" {
  description = "Enable canary deployment support"
  type        = bool
  default     = false
}

variable "canary_settings" {
  description = "Canary deployment configuration"
  type = object({
    initial_weight      = number
    weight_increment    = number
    increment_interval  = string
    success_threshold   = number
    max_weight         = number
  })
  default = {
    initial_weight      = 5
    weight_increment    = 5
    increment_interval  = "2m"
    success_threshold   = 95
    max_weight         = 50
  }
}

# Feature Flags and Integrations
variable "enable_feature_flags" {
  description = "Enable feature flag service (LaunchDarkly integration)"
  type        = bool
  default     = false
}

variable "launchdarkly_config" {
  description = "LaunchDarkly configuration"
  type = object({
    sdk_key     = string
    project_key = string
    environment = string
  })
  default = {
    sdk_key     = ""
    project_key = ""
    environment = ""
  }
  sensitive = true
}

variable "enable_ab_testing" {
  description = "Enable A/B testing infrastructure"
  type        = bool
  default     = false
}

# External Service Integrations
variable "enable_plaid_integration" {
  description = "Enable Plaid banking integration"
  type        = bool
  default     = true
}

variable "enable_yodlee_integration" {
  description = "Enable Yodlee banking integration"
  type        = bool
  default     = false
}

variable "enable_ai_features" {
  description = "Enable AI/ML features"
  type        = bool
  default     = true
}

variable "enable_voice_interface" {
  description = "Enable voice interface features"
  type        = bool
  default     = false
}

# Performance and Cost Optimization
variable "enable_cost_optimization" {
  description = "Enable cost optimization features (Spot instances, etc.)"
  type        = bool
  default     = true
}

variable "enable_performance_monitoring" {
  description = "Enable detailed performance monitoring"
  type        = bool
  default     = false
}

variable "enable_auto_scaling" {
  description = "Enable auto-scaling for cost optimization"
  type        = bool
  default     = true
}

# Development Environment Features
variable "auto_shutdown_enabled" {
  description = "Enable automatic shutdown for non-production environments"
  type        = bool
  default     = false
}

variable "auto_shutdown_schedule" {
  description = "Cron schedule for automatic shutdown"
  type        = string
  default     = null
}

variable "auto_startup_schedule" {
  description = "Cron schedule for automatic startup"
  type        = string
  default     = null
}

variable "enable_debug_mode" {
  description = "Enable debug mode for development"
  type        = bool
  default     = false
}

variable "enable_hot_reload" {
  description = "Enable hot reload for development"
  type        = bool
  default     = false
}

variable "enable_profiling" {
  description = "Enable application profiling"
  type        = bool
  default     = false
}

# SSL and DNS Configuration
variable "enable_ssl" {
  description = "Enable SSL/TLS encryption"
  type        = bool
  default     = true
}

variable "certificate_arn" {
  description = "ARN of the SSL certificate"
  type        = string
  default     = null
}

# WAF Configuration
variable "waf_rules" {
  description = "List of WAF managed rule groups to enable"
  type        = list(string)
  default     = []
}

# CDN Configuration
variable "enable_cdn" {
  description = "Enable CloudFront CDN"
  type        = bool
  default     = false
}

variable "cdn_config" {
  description = "CloudFront CDN configuration"
  type = object({
    price_class = string
    cache_behaviors = list(object({
      path_pattern = string
      ttl         = number
    }))
  })
  default = {
    price_class = "PriceClass_100"
    cache_behaviors = []
  }
}

# Circuit Breaker Configuration
variable "enable_circuit_breaker" {
  description = "Enable circuit breaker pattern"
  type        = bool
  default     = false
}

variable "circuit_breaker_config" {
  description = "Circuit breaker configuration"
  type = object({
    failure_threshold = number
    timeout          = string
    max_requests     = number
  })
  default = {
    failure_threshold = 5
    timeout          = "60s"
    max_requests     = 10
  }
}

# Rate Limiting Configuration
variable "enable_rate_limiting" {
  description = "Enable rate limiting"
  type        = bool
  default     = true
}

variable "rate_limit_config" {
  description = "Rate limiting configuration"
  type = object({
    requests_per_minute = number
    burst_size         = number
    exempt_paths       = list(string)
  })
  default = {
    requests_per_minute = 1000
    burst_size         = 2000
    exempt_paths       = ["/health", "/metrics"]
  }
}

# Data Retention and Compliance
variable "data_retention_days" {
  description = "Data retention period in days"
  type        = number
  default     = 365
}

variable "enable_audit_logging" {
  description = "Enable comprehensive audit logging"
  type        = bool
  default     = true
}

variable "enable_compliance_monitoring" {
  description = "Enable compliance monitoring (SOC2, PCI-DSS)"
  type        = bool
  default     = false
}

variable "compliance_tags" {
  description = "Compliance-related tags"
  type        = map(string)
  default     = {}
}

# Cost Management
variable "enable_cost_alerts" {
  description = "Enable cost monitoring and alerts"
  type        = bool
  default     = false
}

variable "cost_budgets" {
  description = "Cost budget configurations"
  type = list(object({
    name        = string
    amount      = number
    unit        = string
    time_period = string
    threshold   = number
  }))
  default = []
}

# Load Testing Configuration
variable "enable_load_testing" {
  description = "Enable automated load testing"
  type        = bool
  default     = false
}

variable "load_test_schedules" {
  description = "Load testing schedule configurations"
  type = list(object({
    name     = string
    schedule = string
    duration = string
    users    = number
  }))
  default = []
}