# S3 Buckets Module for Financial Planner
variable "name_prefix" {
  description = "Name prefix for resources"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "buckets" {
  description = "Map of bucket configurations"
  type = map(object({
    versioning_enabled = bool
    lifecycle_rules = optional(list(object({
      id     = string
      status = string
      transition = optional(list(object({
        days          = number
        storage_class = string
      })), [])
      expiration = optional(object({
        days = number
      }), null)
    })), [])
  }))
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}

# Create S3 buckets
resource "aws_s3_bucket" "buckets" {
  for_each = var.buckets
  
  bucket = "${var.name_prefix}-${each.key}"
  
  tags = merge(var.tags, {
    Name = "${var.name_prefix}-${each.key}"
    Type = each.key
  })
}

# Configure bucket versioning
resource "aws_s3_bucket_versioning" "versioning" {
  for_each = var.buckets
  
  bucket = aws_s3_bucket.buckets[each.key].id
  versioning_configuration {
    status = each.value.versioning_enabled ? "Enabled" : "Suspended"
  }
}

# Configure bucket encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "encryption" {
  for_each = var.buckets
  
  bucket = aws_s3_bucket.buckets[each.key].id
  
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
    bucket_key_enabled = true
  }
}

# Block public access
resource "aws_s3_bucket_public_access_block" "block_public" {
  for_each = var.buckets
  
  bucket = aws_s3_bucket.buckets[each.key].id
  
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Configure lifecycle rules
resource "aws_s3_bucket_lifecycle_configuration" "lifecycle" {
  for_each = {
    for k, v in var.buckets : k => v if length(v.lifecycle_rules) > 0
  }
  
  bucket = aws_s3_bucket.buckets[each.key].id
  
  dynamic "rule" {
    for_each = each.value.lifecycle_rules
    content {
      id     = rule.value.id
      status = rule.value.status
      
      dynamic "transition" {
        for_each = rule.value.transition != null ? rule.value.transition : []
        content {
          days          = transition.value.days
          storage_class = transition.value.storage_class
        }
      }
      
      dynamic "expiration" {
        for_each = rule.value.expiration != null ? [rule.value.expiration] : []
        content {
          days = expiration.value.days
        }
      }
    }
  }
}

# Outputs
output "bucket_names" {
  description = "Map of bucket names"
  value = {
    for k, v in aws_s3_bucket.buckets : k => v.id
  }
}

output "bucket_arns" {
  description = "Map of bucket ARNs"
  value = {
    for k, v in aws_s3_bucket.buckets : k => v.arn
  }
}

output "bucket_domain_names" {
  description = "Map of bucket domain names"
  value = {
    for k, v in aws_s3_bucket.buckets : k => v.bucket_domain_name
  }
}