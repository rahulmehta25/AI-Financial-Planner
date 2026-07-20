#!/bin/bash

# AWS Cleanup Script for Financial Planning Demo
# This script tears down all AWS resources created by the deployment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="finplan"
AWS_REGION="${AWS_REGION:-us-east-1}"
ENVIRONMENT="${ENVIRONMENT:-demo}"

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check for AWS CLI
    if ! command -v aws &> /dev/null; then
        print_error "AWS CLI is not installed."
        exit 1
    fi
    
    # Check for Terraform
    if ! command -v terraform &> /dev/null; then
        print_error "Terraform is not installed."
        exit 1
    fi
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        print_error "AWS credentials are not configured."
        exit 1
    fi
    
    print_status "Prerequisites check completed."
}

# Empty S3 buckets before deletion
empty_s3_buckets() {
    print_status "Emptying S3 buckets..."
    
    cd ../terraform
    
    # Get bucket name from Terraform state
    if terraform state show aws_s3_bucket.static &> /dev/null; then
        BUCKET_NAME=$(terraform state show aws_s3_bucket.static | grep -E '^\s*bucket\s*=' | cut -d'"' -f2)
        
        if [ ! -z "$BUCKET_NAME" ]; then
            print_status "Emptying bucket: $BUCKET_NAME"
            aws s3 rm s3://"$BUCKET_NAME" --recursive || true
            
            # Delete all versions if versioning is enabled
            aws s3api delete-objects \
                --bucket "$BUCKET_NAME" \
                --delete "$(aws s3api list-object-versions \
                    --bucket "$BUCKET_NAME" \
                    --output json \
                    --query '{Objects: Versions[].{Key: Key, VersionId: VersionId}}')" 2>/dev/null || true
        fi
    fi
}

# Delete ECR images
delete_ecr_images() {
    print_status "Deleting ECR images..."
    
    cd ../terraform
    
    # Get repository names
    BACKEND_REPO=$(terraform output -raw ecr_backend_repository 2>/dev/null | cut -d'/' -f2 | cut -d':' -f1) || true
    FRONTEND_REPO=$(terraform output -raw ecr_frontend_repository 2>/dev/null | cut -d'/' -f2 | cut -d':' -f1) || true
    
    # Delete all images from backend repository
    if [ ! -z "$BACKEND_REPO" ]; then
        print_status "Deleting images from backend repository..."
        aws ecr list-images --repository-name "$BACKEND_REPO" --query 'imageIds[*]' --output json 2>/dev/null | \
            jq '.[] | select(.imageTag != null)' | \
            jq -s '.' | \
            xargs -I {} aws ecr batch-delete-image --repository-name "$BACKEND_REPO" --image-ids '{}' 2>/dev/null || true
    fi
    
    # Delete all images from frontend repository
    if [ ! -z "$FRONTEND_REPO" ]; then
        print_status "Deleting images from frontend repository..."
        aws ecr list-images --repository-name "$FRONTEND_REPO" --query 'imageIds[*]' --output json 2>/dev/null | \
            jq '.[] | select(.imageTag != null)' | \
            jq -s '.' | \
            xargs -I {} aws ecr batch-delete-image --repository-name "$FRONTEND_REPO" --image-ids '{}' 2>/dev/null || true
    fi
}

# Destroy infrastructure
destroy_infrastructure() {
    print_status "Destroying infrastructure with Terraform..."
    
    cd ../terraform
    
    # Initialize Terraform if needed
    if [ ! -d ".terraform" ]; then
        AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
        BUCKET_NAME="${PROJECT_NAME}-terraform-state-${AWS_ACCOUNT_ID}"
        TABLE_NAME="${PROJECT_NAME}-terraform-locks"
        
        terraform init \
            -backend-config="bucket=$BUCKET_NAME" \
            -backend-config="key=${ENVIRONMENT}/terraform.tfstate" \
            -backend-config="region=$AWS_REGION" \
            -backend-config="dynamodb_table=$TABLE_NAME" \
            -backend-config="encrypt=true"
    fi
    
    # Destroy infrastructure
    terraform destroy -var="environment=$ENVIRONMENT" -auto-approve
    
    print_status "Infrastructure destroyed successfully."
}

# Clean up Terraform backend
cleanup_backend() {
    print_status "Cleaning up Terraform backend..."
    
    AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    BUCKET_NAME="${PROJECT_NAME}-terraform-state-${AWS_ACCOUNT_ID}"
    TABLE_NAME="${PROJECT_NAME}-terraform-locks"
    
    # Delete state bucket
    if aws s3api head-bucket --bucket "$BUCKET_NAME" 2>/dev/null; then
        print_status "Deleting Terraform state bucket..."
        
        # Empty the bucket first
        aws s3 rm s3://"$BUCKET_NAME" --recursive || true
        
        # Delete all versions
        aws s3api delete-objects \
            --bucket "$BUCKET_NAME" \
            --delete "$(aws s3api list-object-versions \
                --bucket "$BUCKET_NAME" \
                --output json \
                --query '{Objects: Versions[].{Key: Key, VersionId: VersionId}}')" 2>/dev/null || true
        
        # Delete the bucket
        aws s3api delete-bucket --bucket "$BUCKET_NAME" || true
    fi
    
    # Delete DynamoDB table
    if aws dynamodb describe-table --table-name "$TABLE_NAME" &> /dev/null; then
        print_status "Deleting Terraform locks table..."
        aws dynamodb delete-table --table-name "$TABLE_NAME" || true
    fi
}

# Display cleanup summary
display_summary() {
    print_status "Cleanup completed successfully!"
    echo ""
    echo "========================================="
    echo "        CLEANUP SUMMARY"
    echo "========================================="
    echo ""
    echo "The following resources have been deleted:"
    echo "  - ECS Cluster and Services"
    echo "  - RDS Database Instance"
    echo "  - ElastiCache Redis Cluster"
    echo "  - Application Load Balancer"
    echo "  - ECR Repositories and Images"
    echo "  - S3 Buckets"
    echo "  - CloudFront Distribution"
    echo "  - VPC and Networking Resources"
    echo "  - IAM Roles and Policies"
    echo "  - CloudWatch Log Groups"
    echo "  - Terraform State and Lock Table"
    echo ""
    echo "All AWS resources have been cleaned up."
    echo "========================================="
}

# Main cleanup flow
main() {
    print_warning "WARNING: This will destroy ALL AWS resources for $PROJECT_NAME ($ENVIRONMENT environment)!"
    echo ""
    read -p "Are you sure you want to proceed? Type 'destroy' to confirm: " confirm
    
    if [ "$confirm" != "destroy" ]; then
        print_status "Cleanup cancelled."
        exit 0
    fi
    
    print_status "Starting cleanup process..."
    
    check_prerequisites
    empty_s3_buckets
    delete_ecr_images
    destroy_infrastructure
    
    # Ask about backend cleanup
    echo ""
    print_warning "Do you want to delete the Terraform backend (state bucket and lock table)?"
    read -p "This will prevent you from managing these resources with Terraform later (yes/no): " cleanup_backend
    
    if [ "$cleanup_backend" == "yes" ]; then
        cleanup_backend
    fi
    
    display_summary
}

# Run main function
main "$@"