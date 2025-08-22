#!/bin/bash

# Azure Deployment Script for Financial Planning Demo
# This script deploys the application to Azure using ARM templates

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="finplan"
ENVIRONMENT="${ENVIRONMENT:-demo}"
LOCATION="${LOCATION:-eastus}"
RESOURCE_GROUP="${RESOURCE_GROUP:-${PROJECT_NAME}-${ENVIRONMENT}-rg}"

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
    
    # Check for Azure CLI
    if ! command -v az &> /dev/null; then
        print_error "Azure CLI is not installed. Please install it first."
        exit 1
    fi
    
    # Check for Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install it first."
        exit 1
    fi
    
    # Check Azure login
    if ! az account show &> /dev/null; then
        print_error "Not logged into Azure. Please run 'az login' first."
        exit 1
    fi
    
    print_status "All prerequisites are met."
}

# Create resource group
create_resource_group() {
    print_status "Creating resource group: $RESOURCE_GROUP"
    
    az group create \
        --name "$RESOURCE_GROUP" \
        --location "$LOCATION" \
        --tags "Project=$PROJECT_NAME" "Environment=$ENVIRONMENT"
}

# Deploy ARM template
deploy_template() {
    print_status "Deploying ARM template..."
    
    # Generate a secure password for PostgreSQL
    DB_PASSWORD=$(openssl rand -base64 32)
    
    az deployment group create \
        --resource-group "$RESOURCE_GROUP" \
        --template-file ../arm-templates/azuredeploy.json \
        --parameters \
            projectName="$PROJECT_NAME" \
            environment="$ENVIRONMENT" \
            administratorPassword="$DB_PASSWORD" \
        --name "${PROJECT_NAME}-deployment-$(date +%Y%m%d%H%M%S)"
    
    print_status "ARM template deployed successfully."
}

# Build and push Docker images
build_and_push_images() {
    print_status "Building and pushing Docker images to Azure Container Registry..."
    
    # Get ACR name from deployment
    ACR_NAME=$(az acr list --resource-group "$RESOURCE_GROUP" --query "[0].name" -o tsv)
    ACR_LOGIN_SERVER=$(az acr list --resource-group "$RESOURCE_GROUP" --query "[0].loginServer" -o tsv)
    
    # Login to ACR
    az acr login --name "$ACR_NAME"
    
    # Build and push backend
    print_status "Building backend image..."
    cd ../../../backend
    docker build -t "$ACR_LOGIN_SERVER/backend:latest" .
    docker push "$ACR_LOGIN_SERVER/backend:latest"
    
    # Build and push frontend
    print_status "Building frontend image..."
    cd ../frontend
    
    # Get backend URL
    BACKEND_URL=$(az webapp show \
        --resource-group "$RESOURCE_GROUP" \
        --name "${PROJECT_NAME}-backend-*" \
        --query "defaultHostName" -o tsv | head -1)
    
    docker build \
        --build-arg NEXT_PUBLIC_API_URL="https://${BACKEND_URL}/api" \
        -t "$ACR_LOGIN_SERVER/frontend:latest" .
    docker push "$ACR_LOGIN_SERVER/frontend:latest"
    
    print_status "Docker images pushed successfully."
}

# Update App Services with new images
update_app_services() {
    print_status "Updating App Services with new container images..."
    
    ACR_NAME=$(az acr list --resource-group "$RESOURCE_GROUP" --query "[0].name" -o tsv)
    ACR_LOGIN_SERVER=$(az acr list --resource-group "$RESOURCE_GROUP" --query "[0].loginServer" -o tsv)
    ACR_PASSWORD=$(az acr credential show --name "$ACR_NAME" --query "passwords[0].value" -o tsv)
    
    # Update backend
    BACKEND_APP=$(az webapp list --resource-group "$RESOURCE_GROUP" --query "[?contains(name, 'backend')].name" -o tsv)
    az webapp config container set \
        --resource-group "$RESOURCE_GROUP" \
        --name "$BACKEND_APP" \
        --docker-custom-image-name "$ACR_LOGIN_SERVER/backend:latest" \
        --docker-registry-server-url "https://$ACR_LOGIN_SERVER" \
        --docker-registry-server-user "$ACR_NAME" \
        --docker-registry-server-password "$ACR_PASSWORD"
    
    # Update frontend
    FRONTEND_APP=$(az webapp list --resource-group "$RESOURCE_GROUP" --query "[?contains(name, 'frontend')].name" -o tsv)
    az webapp config container set \
        --resource-group "$RESOURCE_GROUP" \
        --name "$FRONTEND_APP" \
        --docker-custom-image-name "$ACR_LOGIN_SERVER/frontend:latest" \
        --docker-registry-server-url "https://$ACR_LOGIN_SERVER" \
        --docker-registry-server-user "$ACR_NAME" \
        --docker-registry-server-password "$ACR_PASSWORD"
    
    # Restart apps
    az webapp restart --resource-group "$RESOURCE_GROUP" --name "$BACKEND_APP"
    az webapp restart --resource-group "$RESOURCE_GROUP" --name "$FRONTEND_APP"
    
    print_status "App Services updated successfully."
}

# Display deployment information
display_info() {
    print_status "Deployment completed successfully!"
    
    FRONTEND_URL=$(az webapp show \
        --resource-group "$RESOURCE_GROUP" \
        --name "${PROJECT_NAME}-frontend-*" \
        --query "defaultHostName" -o tsv | head -1)
    
    BACKEND_URL=$(az webapp show \
        --resource-group "$RESOURCE_GROUP" \
        --name "${PROJECT_NAME}-backend-*" \
        --query "defaultHostName" -o tsv | head -1)
    
    echo ""
    echo "========================================="
    echo "       DEPLOYMENT INFORMATION"
    echo "========================================="
    echo ""
    echo "Resource Group: $RESOURCE_GROUP"
    echo "Location: $LOCATION"
    echo ""
    echo "Frontend URL: https://$FRONTEND_URL"
    echo "Backend API: https://$BACKEND_URL/api"
    echo ""
    echo "Estimated Monthly Cost: ~$75 (Demo)"
    echo ""
    echo "To view resources in Azure Portal:"
    echo "  https://portal.azure.com/#@/resource/subscriptions/$(az account show --query id -o tsv)/resourceGroups/$RESOURCE_GROUP"
    echo ""
    echo "To delete all resources:"
    echo "  az group delete --name $RESOURCE_GROUP --yes"
    echo ""
    echo "========================================="
}

# Main deployment flow
main() {
    print_status "Starting Azure deployment for $PROJECT_NAME ($ENVIRONMENT environment)..."
    
    check_prerequisites
    
    # Confirm deployment
    echo ""
    print_warning "This will create Azure resources that will incur costs."
    read -p "Do you want to proceed with the deployment? (yes/no): " confirm
    
    if [ "$confirm" != "yes" ]; then
        print_status "Deployment cancelled."
        exit 0
    fi
    
    create_resource_group
    deploy_template
    build_and_push_images
    update_app_services
    display_info
}

# Run main function
main "$@"