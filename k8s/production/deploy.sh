#!/bin/bash

# Financial Planning API - Production Kubernetes Deployment Script
# This script deploys the complete production environment with security best practices

set -euo pipefail

# Configuration
NAMESPACE="financial-planning-prod"
DEPLOYMENT_NAME="financial-planning-api"
MANIFESTS_DIR="./manifests"
KUBECTL_TIMEOUT="300s"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check kubectl
    if ! command -v kubectl &> /dev/null; then
        error "kubectl is not installed or not in PATH"
        exit 1
    fi
    
    # Check cluster connection
    if ! kubectl cluster-info &> /dev/null; then
        error "Cannot connect to Kubernetes cluster"
        exit 1
    fi
    
    # Check if manifests directory exists
    if [[ ! -d "$MANIFESTS_DIR" ]]; then
        error "Manifests directory '$MANIFESTS_DIR' not found"
        exit 1
    fi
    
    success "Prerequisites check passed"
}

# Verify cluster context
verify_cluster_context() {
    local current_context
    current_context=$(kubectl config current-context)
    
    log "Current Kubernetes context: $current_context"
    
    if [[ "$current_context" != *"prod"* ]] && [[ "$current_context" != *"production"* ]]; then
        warning "You are not using a production context!"
        echo "Current context: $current_context"
        read -p "Are you sure you want to continue? (yes/no): " -r
        if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
            log "Deployment aborted by user"
            exit 0
        fi
    fi
}

# Create namespace if it doesn't exist
create_namespace() {
    log "Creating namespace if it doesn't exist..."
    
    if kubectl get namespace "$NAMESPACE" &> /dev/null; then
        log "Namespace '$NAMESPACE' already exists"
    else
        kubectl apply -f "$MANIFESTS_DIR/00-namespace.yaml" --timeout="$KUBECTL_TIMEOUT"
        success "Namespace '$NAMESPACE' created"
    fi
}

# Deploy RBAC resources
deploy_rbac() {
    log "Deploying RBAC resources..."
    kubectl apply -f "$MANIFESTS_DIR/01-rbac.yaml" --timeout="$KUBECTL_TIMEOUT"
    success "RBAC resources deployed"
}

# Deploy ConfigMaps and Secrets
deploy_config() {
    log "Deploying ConfigMaps and Secrets..."
    
    warning "IMPORTANT: Update secrets with actual production values before deploying!"
    warning "Current secrets contain placeholder values that MUST be changed!"
    
    read -p "Have you updated all secrets with production values? (yes/no): " -r
    if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        error "Please update secrets with production values first"
        exit 1
    fi
    
    kubectl apply -f "$MANIFESTS_DIR/02-configmaps-secrets.yaml" --timeout="$KUBECTL_TIMEOUT"
    success "ConfigMaps and Secrets deployed"
}

# Deploy main application
deploy_application() {
    log "Deploying main application..."
    kubectl apply -f "$MANIFESTS_DIR/03-deployment.yaml" --timeout="$KUBECTL_TIMEOUT"
    
    # Wait for deployment to be ready
    log "Waiting for deployment to be ready..."
    kubectl wait --for=condition=Available deployment/"$DEPLOYMENT_NAME" -n "$NAMESPACE" --timeout="$KUBECTL_TIMEOUT"
    success "Application deployment completed"
}

# Deploy autoscaling
deploy_autoscaling() {
    log "Deploying autoscaling resources..."
    kubectl apply -f "$MANIFESTS_DIR/04-hpa.yaml" --timeout="$KUBECTL_TIMEOUT"
    success "Autoscaling resources deployed"
}

# Deploy services
deploy_services() {
    log "Deploying services..."
    kubectl apply -f "$MANIFESTS_DIR/05-services.yaml" --timeout="$KUBECTL_TIMEOUT"
    success "Services deployed"
}

# Deploy network policies
deploy_network_policies() {
    log "Deploying network policies..."
    kubectl apply -f "$MANIFESTS_DIR/06-network-policies.yaml" --timeout="$KUBECTL_TIMEOUT"
    success "Network policies deployed"
}

# Deploy monitoring and service mesh
deploy_monitoring() {
    log "Deploying monitoring and service mesh resources..."
    
    # Check if Istio is installed
    if kubectl get namespace istio-system &> /dev/null; then
        kubectl apply -f "$MANIFESTS_DIR/07-monitoring-service-mesh.yaml" --timeout="$KUBECTL_TIMEOUT"
        success "Monitoring and service mesh resources deployed"
    else
        warning "Istio not found. Skipping service mesh configuration."
        log "Install Istio first: curl -L https://istio.io/downloadIstio | sh -"
    fi
}

# Verify deployment
verify_deployment() {
    log "Verifying deployment..."
    
    # Check pod status
    log "Checking pod status..."
    kubectl get pods -n "$NAMESPACE" -l app="$DEPLOYMENT_NAME"
    
    # Check service status
    log "Checking service status..."
    kubectl get services -n "$NAMESPACE"
    
    # Check HPA status
    log "Checking HPA status..."
    kubectl get hpa -n "$NAMESPACE"
    
    # Check if pods are ready
    local ready_pods
    ready_pods=$(kubectl get pods -n "$NAMESPACE" -l app="$DEPLOYMENT_NAME" --field-selector=status.phase=Running --no-headers | wc -l)
    
    if [[ "$ready_pods" -ge 5 ]]; then
        success "Deployment verification passed. $ready_pods pods are running."
    else
        warning "Only $ready_pods pods are running. Expected at least 5."
    fi
    
    # Test health endpoint
    log "Testing health endpoint..."
    if kubectl exec -n "$NAMESPACE" deployment/"$DEPLOYMENT_NAME" -- curl -f http://localhost:8000/health &> /dev/null; then
        success "Health check passed"
    else
        warning "Health check failed or pending"
    fi
}

# Get deployment info
get_deployment_info() {
    log "Getting deployment information..."
    
    echo "======================================"
    echo "DEPLOYMENT SUMMARY"
    echo "======================================"
    
    echo "Namespace: $NAMESPACE"
    echo "Deployment: $DEPLOYMENT_NAME"
    
    local external_ip
    external_ip=$(kubectl get service "${DEPLOYMENT_NAME}-lb" -n "$NAMESPACE" -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "Pending")
    echo "External IP: $external_ip"
    
    local ingress_hosts
    ingress_hosts=$(kubectl get ingress -n "$NAMESPACE" -o jsonpath='{.items[*].spec.rules[*].host}' 2>/dev/null || echo "N/A")
    echo "Ingress Hosts: $ingress_hosts"
    
    echo "======================================"
    echo "USEFUL COMMANDS"
    echo "======================================"
    echo "View pods:     kubectl get pods -n $NAMESPACE"
    echo "View logs:     kubectl logs -n $NAMESPACE deployment/$DEPLOYMENT_NAME -f"
    echo "Scale up:      kubectl scale deployment/$DEPLOYMENT_NAME --replicas=10 -n $NAMESPACE"
    echo "Port forward:  kubectl port-forward -n $NAMESPACE svc/${DEPLOYMENT_NAME}-svc 8080:80"
    echo "Health check:  curl http://localhost:8080/health"
    echo "======================================"
}

# Rollback function
rollback_deployment() {
    log "Rolling back deployment..."
    kubectl rollout undo deployment/"$DEPLOYMENT_NAME" -n "$NAMESPACE"
    kubectl rollout status deployment/"$DEPLOYMENT_NAME" -n "$NAMESPACE" --timeout="$KUBECTL_TIMEOUT"
    success "Rollback completed"
}

# Main deployment function
main() {
    log "Starting Financial Planning API production deployment..."
    
    # Handle command line arguments
    case "${1:-deploy}" in
        "deploy")
            check_prerequisites
            verify_cluster_context
            create_namespace
            deploy_rbac
            deploy_config
            deploy_application
            deploy_autoscaling
            deploy_services
            deploy_network_policies
            deploy_monitoring
            verify_deployment
            get_deployment_info
            success "Deployment completed successfully!"
            ;;
        "rollback")
            rollback_deployment
            ;;
        "verify")
            verify_deployment
            get_deployment_info
            ;;
        "destroy")
            warning "This will destroy the entire deployment!"
            read -p "Are you sure? Type 'yes' to confirm: " -r
            if [[ $REPLY == "yes" ]]; then
                log "Destroying deployment..."
                kubectl delete namespace "$NAMESPACE" --timeout="$KUBECTL_TIMEOUT"
                success "Deployment destroyed"
            else
                log "Destroy operation cancelled"
            fi
            ;;
        "help")
            echo "Usage: $0 [command]"
            echo "Commands:"
            echo "  deploy   - Deploy the application (default)"
            echo "  rollback - Rollback to previous version"
            echo "  verify   - Verify current deployment"
            echo "  destroy  - Destroy the entire deployment"
            echo "  help     - Show this help message"
            ;;
        *)
            error "Unknown command: $1"
            echo "Use '$0 help' for usage information"
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"