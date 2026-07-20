# Backend configuration template for multi-environment deployments
# This file provides backend configuration templates for different environments

# Development environment backend config
# Usage: terraform init -backend-config=environments/development/backend.hcl
resource "local_file" "backend_dev" {
  filename = "${path.module}/development/backend.hcl"
  content = <<-EOT
    bucket         = "financial-planning-terraform-state-dev"
    key            = "development/terraform.tfstate"
    region         = "us-west-2"
    encrypt        = true
    dynamodb_table = "financial-planning-terraform-locks"
    workspace_key_prefix = "workspaces"
  EOT
}

# Staging environment backend config
resource "local_file" "backend_staging" {
  filename = "${path.module}/staging/backend.hcl"
  content = <<-EOT
    bucket         = "financial-planning-terraform-state-staging"
    key            = "staging/terraform.tfstate"
    region         = "us-west-2"
    encrypt        = true
    dynamodb_table = "financial-planning-terraform-locks"
    workspace_key_prefix = "workspaces"
  EOT
}

# Production environment backend config
resource "local_file" "backend_prod" {
  filename = "${path.module}/production/backend.hcl"
  content = <<-EOT
    bucket         = "financial-planning-terraform-state-prod"
    key            = "production/terraform.tfstate"
    region         = "us-west-2"
    encrypt        = true
    dynamodb_table = "financial-planning-terraform-locks"
    workspace_key_prefix = "workspaces"
  EOT
}