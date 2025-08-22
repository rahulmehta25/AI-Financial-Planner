#!/bin/bash

# AWS Deployment Script for Financial Planning Demo
# This script deploys the application to AWS using Terraform and Docker

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
        print_error "AWS CLI is not installed. Please install it first."
        exit 1
    fi
    
    # Check for Terraform
    if ! command -v terraform &> /dev/null; then
        print_error "Terraform is not installed. Please install it first."
        exit 1
    fi
    
    # Check for Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install it first."
        exit 1
    fi
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        print_error "AWS credentials are not configured. Please configure them first."
        exit 1
    fi
    
    print_status "All prerequisites are met."
}

# Initialize Terraform
init_terraform() {
    print_status "Initializing Terraform..."
    cd ../terraform
    
    # Create backend bucket if it doesn't exist
    BUCKET_NAME="${PROJECT_NAME}-terraform-state-${AWS_ACCOUNT_ID}"
    if ! aws s3api head-bucket --bucket "$BUCKET_NAME" 2>/dev/null; then
        print_status "Creating S3 bucket for Terraform state..."
        aws s3api create-bucket \
            --bucket "$BUCKET_NAME" \
            --region "$AWS_REGION" \
            $(if [ "$AWS_REGION" != "us-east-1" ]; then echo "--create-bucket-configuration LocationConstraint=$AWS_REGION"; fi)
        
        # Enable versioning
        aws s3api put-bucket-versioning \
            --bucket "$BUCKET_NAME" \
            --versioning-configuration Status=Enabled
        
        # Enable encryption
        aws s3api put-bucket-encryption \
            --bucket "$BUCKET_NAME" \
            --server-side-encryption-configuration '{
                "Rules": [{
                    "ApplyServerSideEncryptionByDefault": {
                        "SSEAlgorithm": "AES256"
                    }
                }]
            }'
    fi
    
    # Create DynamoDB table for state locking if it doesn't exist
    TABLE_NAME="${PROJECT_NAME}-terraform-locks"
    if ! aws dynamodb describe-table --table-name "$TABLE_NAME" &> /dev/null; then
        print_status "Creating DynamoDB table for Terraform state locking..."
        aws dynamodb create-table \
            --table-name "$TABLE_NAME" \
            --attribute-definitions AttributeName=LockID,AttributeType=S \
            --key-schema AttributeName=LockID,KeyType=HASH \
            --billing-mode PAY_PER_REQUEST \
            --region "$AWS_REGION"
        
        # Wait for table to be active
        aws dynamodb wait table-exists --table-name "$TABLE_NAME"
    fi
    
    # Initialize Terraform with backend config
    terraform init \
        -backend-config="bucket=$BUCKET_NAME" \
        -backend-config="key=${ENVIRONMENT}/terraform.tfstate" \
        -backend-config="region=$AWS_REGION" \
        -backend-config="dynamodb_table=$TABLE_NAME" \
        -backend-config="encrypt=true"
    
    print_status "Terraform initialized successfully."
}

# Plan infrastructure
plan_infrastructure() {
    print_status "Planning infrastructure changes..."
    terraform plan -var="environment=$ENVIRONMENT" -out=tfplan
}

# Apply infrastructure
apply_infrastructure() {
    print_status "Applying infrastructure changes..."
    terraform apply tfplan
    
    # Save outputs
    terraform output -json > outputs.json
    print_status "Infrastructure deployed successfully."
}

# Build and push Docker images
build_and_push_images() {
    print_status "Building and pushing Docker images..."
    
    # Get ECR repository URLs from Terraform outputs
    BACKEND_REPO=$(terraform output -raw ecr_backend_repository)
    FRONTEND_REPO=$(terraform output -raw ecr_frontend_repository)
    
    # Login to ECR
    aws ecr get-login-password --region "$AWS_REGION" | \
        docker login --username AWS --password-stdin "$BACKEND_REPO"
    
    # Build and push backend
    print_status "Building backend image..."
    cd ../../../backend
    docker build -t "$BACKEND_REPO:latest" .
    docker push "$BACKEND_REPO:latest"
    
    # Build and push frontend
    print_status "Building frontend image..."
    cd ../frontend
    
    # Get API URL from Terraform outputs
    API_URL="https://$(cd ../cloud-deploy/aws/terraform && terraform output -raw alb_dns_name)"
    
    # Build with API URL
    docker build \
        --build-arg NEXT_PUBLIC_API_URL="$API_URL/api" \
        -t "$FRONTEND_REPO:latest" .
    docker push "$FRONTEND_REPO:latest"
    
    print_status "Docker images pushed successfully."
}

# Update ECS services
update_ecs_services() {
    print_status "Updating ECS services..."
    
    cd ../cloud-deploy/aws/terraform
    CLUSTER_NAME=$(terraform output -raw ecs_cluster_name)
    BACKEND_SERVICE=$(terraform output -raw backend_service_name)
    FRONTEND_SERVICE=$(terraform output -raw frontend_service_name)
    
    # Force new deployment for backend
    aws ecs update-service \
        --cluster "$CLUSTER_NAME" \
        --service "$BACKEND_SERVICE" \
        --force-new-deployment \
        --region "$AWS_REGION"
    
    # Force new deployment for frontend
    aws ecs update-service \
        --cluster "$CLUSTER_NAME" \
        --service "$FRONTEND_SERVICE" \
        --force-new-deployment \
        --region "$AWS_REGION"
    
    print_status "Waiting for services to stabilize..."
    
    # Wait for backend service to stabilize
    aws ecs wait services-stable \
        --cluster "$CLUSTER_NAME" \
        --services "$BACKEND_SERVICE" \
        --region "$AWS_REGION"
    
    # Wait for frontend service to stabilize
    aws ecs wait services-stable \
        --cluster "$CLUSTER_NAME" \
        --services "$FRONTEND_SERVICE" \
        --region "$AWS_REGION"
    
    print_status "ECS services updated successfully."
}

# Run database migrations
run_migrations() {
    print_status "Running database migrations..."
    
    # Get database URL from outputs
    cd ../cloud-deploy/aws/terraform
    DB_ENDPOINT=$(terraform output -raw rds_endpoint)
    
    # Run migrations using ECS task
    TASK_DEF="${PROJECT_NAME}-backend"
    CLUSTER_NAME=$(terraform output -raw ecs_cluster_name)
    SUBNETS=$(aws ec2 describe-subnets --query 'Subnets[?DefaultForAz==`true`].SubnetId' --output text | tr '\t' ',')
    
    # Run migration task
    aws ecs run-task \
        --cluster "$CLUSTER_NAME" \
        --task-definition "$TASK_DEF" \
        --launch-type FARGATE \
        --network-configuration "awsvpcConfiguration={subnets=[$SUBNETS],assignPublicIp=ENABLED}" \
        --overrides '{
            "containerOverrides": [{
                "name": "backend",
                "command": ["python", "-m", "alembic", "upgrade", "head"]
            }]
        }' \
        --region "$AWS_REGION"
    
    print_status "Database migrations completed."
}

# Display deployment information
display_info() {
    cd ../cloud-deploy/aws/terraform
    
    print_status "Deployment completed successfully!"
    echo ""
    echo "========================================="
    echo "       DEPLOYMENT INFORMATION"
    echo "========================================="
    echo ""
    echo "Application URL: http://$(terraform output -raw alb_dns_name)"
    echo "API Endpoint: http://$(terraform output -raw alb_dns_name)/api"
    echo ""
    echo "CloudFront CDN: https://$(terraform output -raw cloudfront_domain)"
    echo ""
    echo "Estimated Monthly Cost: ~$85"
    echo ""
    echo "To access the application, open:"
    echo "  http://$(terraform output -raw alb_dns_name)"
    echo ""
    echo "To tear down the infrastructure, run:"
    echo "  ./cleanup-aws.sh"
    echo ""
    echo "========================================="
}

# Main deployment flow
main() {
    print_status "Starting AWS deployment for $PROJECT_NAME ($ENVIRONMENT environment)..."
    
    # Get AWS account ID
    AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    
    check_prerequisites
    init_terraform
    plan_infrastructure
    
    # Confirm deployment
    echo ""
    print_warning "This will create AWS resources that will incur costs."
    read -p "Do you want to proceed with the deployment? (yes/no): " confirm
    
    if [ "$confirm" != "yes" ]; then
        print_status "Deployment cancelled."
        exit 0
    fi
    
    apply_infrastructure
    build_and_push_images
    update_ecs_services
    run_migrations
    display_info
}

# Run main function
main "$@"