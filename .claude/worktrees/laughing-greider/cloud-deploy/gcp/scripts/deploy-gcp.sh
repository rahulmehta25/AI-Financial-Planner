#!/bin/bash

# GCP Deployment Script for Financial Planning Demo
# This script deploys the application to Google Cloud Platform

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="finplan"
ENVIRONMENT="${ENVIRONMENT:-demo}"
REGION="${REGION:-us-central1}"
ZONE="${ZONE:-us-central1-a}"
PROJECT_ID="${GCP_PROJECT_ID}"

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
    
    # Check for gcloud CLI
    if ! command -v gcloud &> /dev/null; then
        print_error "Google Cloud SDK is not installed. Please install it first."
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
    
    # Check GCP authentication
    if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" &> /dev/null; then
        print_error "Not authenticated with GCP. Please run 'gcloud auth login' first."
        exit 1
    fi
    
    # Check project ID
    if [ -z "$PROJECT_ID" ]; then
        PROJECT_ID=$(gcloud config get-value project)
        if [ -z "$PROJECT_ID" ]; then
            print_error "No GCP project selected. Set GCP_PROJECT_ID or run 'gcloud config set project PROJECT_ID'"
            exit 1
        fi
    fi
    
    print_status "Using GCP Project: $PROJECT_ID"
    print_status "All prerequisites are met."
}

# Enable required APIs
enable_apis() {
    print_status "Enabling required GCP APIs..."
    
    gcloud services enable \
        compute.googleapis.com \
        container.googleapis.com \
        cloudrun.googleapis.com \
        sqladmin.googleapis.com \
        redis.googleapis.com \
        artifactregistry.googleapis.com \
        cloudbuild.googleapis.com \
        secretmanager.googleapis.com \
        cloudresourcemanager.googleapis.com \
        servicenetworking.googleapis.com \
        vpcaccess.googleapis.com \
        --project="$PROJECT_ID"
    
    print_status "APIs enabled successfully."
}

# Initialize Terraform
init_terraform() {
    print_status "Initializing Terraform..."
    cd ../terraform
    
    # Create GCS bucket for Terraform state if it doesn't exist
    BUCKET_NAME="${PROJECT_NAME}-terraform-state-${PROJECT_ID}"
    if ! gsutil ls -b "gs://$BUCKET_NAME" &> /dev/null; then
        print_status "Creating GCS bucket for Terraform state..."
        gsutil mb -p "$PROJECT_ID" -l "$REGION" "gs://$BUCKET_NAME"
        gsutil versioning set on "gs://$BUCKET_NAME"
    fi
    
    # Initialize Terraform with backend config
    terraform init \
        -backend-config="bucket=$BUCKET_NAME" \
        -backend-config="prefix=terraform/state/${ENVIRONMENT}"
    
    print_status "Terraform initialized successfully."
}

# Plan infrastructure
plan_infrastructure() {
    print_status "Planning infrastructure changes..."
    terraform plan \
        -var="project_id=$PROJECT_ID" \
        -var="region=$REGION" \
        -var="zone=$ZONE" \
        -var="environment=$ENVIRONMENT" \
        -out=tfplan
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
    print_status "Building and pushing Docker images to Artifact Registry..."
    
    # Configure Docker for Artifact Registry
    gcloud auth configure-docker "${REGION}-docker.pkg.dev"
    
    REGISTRY="${REGION}-docker.pkg.dev/${PROJECT_ID}/${PROJECT_NAME}-docker"
    
    # Build and push backend
    print_status "Building backend image..."
    cd ../../../backend
    docker build -t "$REGISTRY/backend:latest" .
    docker push "$REGISTRY/backend:latest"
    
    # Build and push frontend
    print_status "Building frontend image..."
    cd ../frontend
    
    # Get backend Cloud Run URL
    BACKEND_URL=$(gcloud run services describe "${PROJECT_NAME}-backend" \
        --region="$REGION" \
        --format="value(status.url)" \
        --project="$PROJECT_ID")
    
    docker build \
        --build-arg NEXT_PUBLIC_API_URL="${BACKEND_URL}/api" \
        -t "$REGISTRY/frontend:latest" .
    docker push "$REGISTRY/frontend:latest"
    
    print_status "Docker images pushed successfully."
}

# Deploy to Cloud Run
deploy_cloud_run() {
    print_status "Deploying services to Cloud Run..."
    
    cd ../cloud-deploy/gcp/terraform
    REGISTRY="${REGION}-docker.pkg.dev/${PROJECT_ID}/${PROJECT_NAME}-docker"
    
    # Get database connection info from Terraform outputs
    DB_CONNECTION=$(terraform output -raw -json | jq -r '.database_connection_name.value')
    REDIS_HOST=$(terraform output -raw -json | jq -r '.redis_host.value')
    
    # Deploy backend
    gcloud run deploy "${PROJECT_NAME}-backend" \
        --image="$REGISTRY/backend:latest" \
        --platform=managed \
        --region="$REGION" \
        --allow-unauthenticated \
        --add-cloudsql-instances="$DB_CONNECTION" \
        --set-env-vars="ENVIRONMENT=$ENVIRONMENT" \
        --set-env-vars="REDIS_HOST=$REDIS_HOST" \
        --min-instances=0 \
        --max-instances=10 \
        --memory=512Mi \
        --cpu=1 \
        --timeout=300 \
        --project="$PROJECT_ID"
    
    # Get backend URL
    BACKEND_URL=$(gcloud run services describe "${PROJECT_NAME}-backend" \
        --region="$REGION" \
        --format="value(status.url)" \
        --project="$PROJECT_ID")
    
    # Deploy frontend
    gcloud run deploy "${PROJECT_NAME}-frontend" \
        --image="$REGISTRY/frontend:latest" \
        --platform=managed \
        --region="$REGION" \
        --allow-unauthenticated \
        --set-env-vars="NEXT_PUBLIC_API_URL=${BACKEND_URL}/api" \
        --min-instances=0 \
        --max-instances=10 \
        --memory=512Mi \
        --cpu=1 \
        --timeout=300 \
        --project="$PROJECT_ID"
    
    print_status "Cloud Run services deployed successfully."
}

# Run database migrations
run_migrations() {
    print_status "Running database migrations..."
    
    # Use Cloud Build to run migrations
    cat > cloudbuild-migrate.yaml << EOF
steps:
  - name: '${REGION}-docker.pkg.dev/${PROJECT_ID}/${PROJECT_NAME}-docker/backend:latest'
    entrypoint: 'python'
    args: ['-m', 'alembic', 'upgrade', 'head']
    env:
      - 'DATABASE_URL=\${_DATABASE_URL}'
substitutions:
  _DATABASE_URL: '$(terraform output -raw database_url)'
EOF
    
    gcloud builds submit \
        --config=cloudbuild-migrate.yaml \
        --project="$PROJECT_ID" \
        --region="$REGION"
    
    rm cloudbuild-migrate.yaml
    print_status "Database migrations completed."
}

# Display deployment information
display_info() {
    cd ../cloud-deploy/gcp/terraform
    
    FRONTEND_URL=$(gcloud run services describe "${PROJECT_NAME}-frontend" \
        --region="$REGION" \
        --format="value(status.url)" \
        --project="$PROJECT_ID")
    
    BACKEND_URL=$(gcloud run services describe "${PROJECT_NAME}-backend" \
        --region="$REGION" \
        --format="value(status.url)" \
        --project="$PROJECT_ID")
    
    print_status "Deployment completed successfully!"
    echo ""
    echo "========================================="
    echo "       DEPLOYMENT INFORMATION"
    echo "========================================="
    echo ""
    echo "Project ID: $PROJECT_ID"
    echo "Region: $REGION"
    echo ""
    echo "Frontend URL: $FRONTEND_URL"
    echo "Backend API: ${BACKEND_URL}/api"
    echo ""
    echo "Estimated Monthly Cost: ~$70 (Demo)"
    echo ""
    echo "To view resources in GCP Console:"
    echo "  https://console.cloud.google.com/home/dashboard?project=$PROJECT_ID"
    echo ""
    echo "To view Cloud Run services:"
    echo "  https://console.cloud.google.com/run?project=$PROJECT_ID"
    echo ""
    echo "To tear down the infrastructure:"
    echo "  cd ../terraform && terraform destroy"
    echo ""
    echo "========================================="
}

# Main deployment flow
main() {
    print_status "Starting GCP deployment for $PROJECT_NAME ($ENVIRONMENT environment)..."
    
    check_prerequisites
    
    # Confirm deployment
    echo ""
    print_warning "This will create GCP resources that will incur costs."
    print_warning "Project: $PROJECT_ID"
    read -p "Do you want to proceed with the deployment? (yes/no): " confirm
    
    if [ "$confirm" != "yes" ]; then
        print_status "Deployment cancelled."
        exit 0
    fi
    
    enable_apis
    init_terraform
    plan_infrastructure
    apply_infrastructure
    build_and_push_images
    deploy_cloud_run
    run_migrations
    display_info
}

# Run main function
main "$@"