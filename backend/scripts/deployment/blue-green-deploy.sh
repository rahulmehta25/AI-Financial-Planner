#!/bin/bash

# Blue-Green Deployment Script for Financial Planning API
# This script performs a blue-green deployment with automatic rollback on failure

set -euo pipefail

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

# Default values
NAMESPACE="financial-planning-prod"
APP_NAME="financial-planning-api"
IMAGE_TAG=""
TIMEOUT=300
DRY_RUN=false
SKIP_HEALTH_CHECK=false
ROLLBACK_ON_FAILURE=true
SLACK_WEBHOOK_URL=""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1" >&2
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1" >&2
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" >&2
}

# Usage function
usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Blue-Green Deployment Script for Financial Planning API

OPTIONS:
    -n, --namespace NAMESPACE    Kubernetes namespace (default: financial-planning-prod)
    -t, --tag TAG               Docker image tag to deploy (required)
    -a, --app APP_NAME          Application name (default: financial-planning-api)
    -T, --timeout TIMEOUT       Health check timeout in seconds (default: 300)
    -d, --dry-run               Perform a dry run without actual deployment
    -s, --skip-health-check     Skip health checks (not recommended)
    -r, --no-rollback           Don't rollback on failure
    -w, --webhook-url URL       Slack webhook URL for notifications
    -h, --help                  Show this help message

Examples:
    $0 --tag v1.2.3
    $0 --namespace staging --tag v1.2.3 --dry-run
    $0 --tag latest --timeout 600 --webhook-url https://hooks.slack.com/...

EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -n|--namespace)
            NAMESPACE="$2"
            shift 2
            ;;
        -t|--tag)
            IMAGE_TAG="$2"
            shift 2
            ;;
        -a|--app)
            APP_NAME="$2"
            shift 2
            ;;
        -T|--timeout)
            TIMEOUT="$2"
            shift 2
            ;;
        -d|--dry-run)
            DRY_RUN=true
            shift
            ;;
        -s|--skip-health-check)
            SKIP_HEALTH_CHECK=true
            shift
            ;;
        -r|--no-rollback)
            ROLLBACK_ON_FAILURE=false
            shift
            ;;
        -w|--webhook-url)
            SLACK_WEBHOOK_URL="$2"
            shift 2
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

# Validate required parameters
if [[ -z "$IMAGE_TAG" ]]; then
    log_error "Image tag is required. Use --tag to specify."
    usage
    exit 1
fi

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    log_error "kubectl is not installed or not in PATH"
    exit 1
fi

# Check if helm is available
if ! command -v helm &> /dev/null; then
    log_error "helm is not installed or not in PATH"
    exit 1
fi

# Send Slack notification
send_slack_notification() {
    local message="$1"
    local color="${2:-#36a64f}"  # Default green
    
    if [[ -n "$SLACK_WEBHOOK_URL" ]]; then
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"attachments\":[{\"color\":\"$color\",\"text\":\"$message\"}]}" \
            "$SLACK_WEBHOOK_URL" &> /dev/null || true
    fi
}

# Get current active slot (blue or green)
get_active_slot() {
    local current_selector
    current_selector=$(kubectl get service "$APP_NAME" -n "$NAMESPACE" \
        -o jsonpath='{.spec.selector.version}' 2>/dev/null || echo "")
    
    if [[ "$current_selector" == "blue" ]]; then
        echo "blue"
    elif [[ "$current_selector" == "green" ]]; then
        echo "green"
    else
        echo "blue"  # Default to blue if no current deployment
    fi
}

# Get inactive slot
get_inactive_slot() {
    local active_slot="$1"
    if [[ "$active_slot" == "blue" ]]; then
        echo "green"
    else
        echo "blue"
    fi
}

# Check if deployment exists
deployment_exists() {
    local deployment_name="$1"
    kubectl get deployment "$deployment_name" -n "$NAMESPACE" &> /dev/null
}

# Wait for deployment to be ready
wait_for_deployment() {
    local deployment_name="$1"
    local timeout="$2"
    
    log_info "Waiting for deployment $deployment_name to be ready (timeout: ${timeout}s)..."
    
    if kubectl wait --for=condition=available \
        --timeout="${timeout}s" \
        deployment/"$deployment_name" \
        -n "$NAMESPACE"; then
        log_success "Deployment $deployment_name is ready"
        return 0
    else
        log_error "Deployment $deployment_name failed to become ready within ${timeout}s"
        return 1
    fi
}

# Perform health check
health_check() {
    local service_name="$1"
    local timeout="$2"
    local endpoint_path="/health"
    
    if [[ "$SKIP_HEALTH_CHECK" == "true" ]]; then
        log_warn "Skipping health check as requested"
        return 0
    fi
    
    log_info "Performing health check on $service_name..."
    
    # Port forward to the service for health check
    local local_port=8080
    kubectl port-forward "service/$service_name" "$local_port:80" -n "$NAMESPACE" &
    local port_forward_pid=$!
    
    # Cleanup function for port-forward
    cleanup_port_forward() {
        if kill -0 "$port_forward_pid" 2>/dev/null; then
            kill "$port_forward_pid"
        fi
    }
    trap cleanup_port_forward EXIT
    
    # Wait for port-forward to be ready
    sleep 5
    
    local start_time
    start_time=$(date +%s)
    local end_time=$((start_time + timeout))
    
    while [[ $(date +%s) -lt $end_time ]]; do
        if curl -f --max-time 10 "http://localhost:$local_port$endpoint_path" &> /dev/null; then
            log_success "Health check passed for $service_name"
            cleanup_port_forward
            trap - EXIT
            return 0
        fi
        log_info "Health check failed, retrying in 10 seconds..."
        sleep 10
    done
    
    log_error "Health check failed for $service_name after ${timeout}s"
    cleanup_port_forward
    trap - EXIT
    return 1
}

# Switch traffic to new deployment
switch_traffic() {
    local target_slot="$1"
    
    log_info "Switching traffic to $target_slot slot..."
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would switch traffic to $target_slot"
        return 0
    fi
    
    kubectl patch service "$APP_NAME" -n "$NAMESPACE" \
        -p "{\"spec\":{\"selector\":{\"version\":\"$target_slot\"}}}"
    
    # Wait for traffic switch to take effect
    sleep 30
    
    log_success "Traffic switched to $target_slot slot"
}

# Rollback deployment
rollback_deployment() {
    local previous_slot="$1"
    
    log_warn "Initiating rollback to $previous_slot slot..."
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would rollback to $previous_slot"
        return 0
    fi
    
    # Switch traffic back
    kubectl patch service "$APP_NAME" -n "$NAMESPACE" \
        -p "{\"spec\":{\"selector\":{\"version\":\"$previous_slot\"}}}"
    
    log_success "Rollback completed. Traffic restored to $previous_slot slot"
    
    # Send notification
    send_slack_notification "🚨 Blue-Green deployment rolled back to $previous_slot slot due to health check failure" "#ff0000"
}

# Cleanup old deployment
cleanup_old_deployment() {
    local old_slot="$1"
    local deployment_name="$APP_NAME-$old_slot"
    
    log_info "Cleaning up old deployment: $deployment_name"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would cleanup deployment $deployment_name"
        return 0
    fi
    
    if deployment_exists "$deployment_name"; then
        kubectl delete deployment "$deployment_name" -n "$NAMESPACE" --ignore-not-found=true
        kubectl delete service "$APP_NAME-$old_slot" -n "$NAMESPACE" --ignore-not-found=true
        log_success "Cleaned up old deployment: $deployment_name"
    fi
}

# Main deployment function
main() {
    log_info "Starting Blue-Green deployment for $APP_NAME with image tag: $IMAGE_TAG"
    log_info "Namespace: $NAMESPACE, Timeout: ${TIMEOUT}s"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_warn "DRY RUN MODE - No actual changes will be made"
    fi
    
    # Get current active slot
    local active_slot
    active_slot=$(get_active_slot)
    local target_slot
    target_slot=$(get_inactive_slot "$active_slot")
    
    log_info "Current active slot: $active_slot"
    log_info "Target deployment slot: $target_slot"
    
    # Send start notification
    send_slack_notification "🚀 Starting Blue-Green deployment of $APP_NAME:$IMAGE_TAG to $target_slot slot"
    
    local deployment_name="$APP_NAME-$target_slot"
    local service_name="$APP_NAME-$target_slot"
    
    # Deploy to target slot using Helm
    log_info "Deploying to $target_slot slot..."
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would deploy with: helm upgrade --install $deployment_name ./helm/financial-planning"
    else
        if ! helm upgrade --install "$deployment_name" "./helm/financial-planning" \
            --namespace "$NAMESPACE" \
            --set image.tag="$IMAGE_TAG" \
            --set blueGreen.enabled=true \
            --set blueGreen.activeSlot="$target_slot" \
            --set service.type=ClusterIP \
            --wait \
            --timeout="${TIMEOUT}s"; then
            
            log_error "Helm deployment failed"
            send_slack_notification "❌ Blue-Green deployment failed during Helm install" "#ff0000"
            exit 1
        fi
    fi
    
    # Wait for deployment to be ready
    if ! wait_for_deployment "$deployment_name" "$TIMEOUT"; then
        log_error "Deployment failed to become ready"
        send_slack_notification "❌ Blue-Green deployment failed - pods not ready" "#ff0000"
        exit 1
    fi
    
    # Perform health check on new deployment
    if ! health_check "$service_name" 60; then
        log_error "Health check failed on new deployment"
        
        if [[ "$ROLLBACK_ON_FAILURE" == "true" ]]; then
            log_warn "Health check failed. Cleaning up failed deployment..."
            if [[ "$DRY_RUN" == "false" ]]; then
                kubectl delete deployment "$deployment_name" -n "$NAMESPACE" --ignore-not-found=true
                kubectl delete service "$service_name" -n "$NAMESPACE" --ignore-not-found=true
            fi
        fi
        
        send_slack_notification "❌ Blue-Green deployment failed health check" "#ff0000"
        exit 1
    fi
    
    # Switch traffic to new deployment
    switch_traffic "$target_slot"
    
    # Final health check after traffic switch
    if ! health_check "$APP_NAME" 30; then
        log_error "Final health check failed after traffic switch"
        
        if [[ "$ROLLBACK_ON_FAILURE" == "true" ]]; then
            rollback_deployment "$active_slot"
            exit 1
        fi
    fi
    
    log_success "Blue-Green deployment completed successfully!"
    log_info "New active slot: $target_slot"
    
    # Cleanup old deployment (keep for potential quick rollback)
    # Uncomment if you want immediate cleanup
    # cleanup_old_deployment "$active_slot"
    
    # Send success notification
    send_slack_notification "✅ Blue-Green deployment of $APP_NAME:$IMAGE_TAG completed successfully. Active slot: $target_slot"
    
    log_info "Deployment summary:"
    log_info "  - Application: $APP_NAME"
    log_info "  - Image Tag: $IMAGE_TAG"
    log_info "  - Namespace: $NAMESPACE"
    log_info "  - Active Slot: $target_slot"
    log_info "  - Previous Slot: $active_slot (available for quick rollback)"
}

# Error handling
handle_error() {
    local exit_code=$?
    local line_number=$1
    
    log_error "Script failed on line $line_number with exit code $exit_code"
    send_slack_notification "💥 Blue-Green deployment script failed on line $line_number" "#ff0000"
    
    exit $exit_code
}

trap 'handle_error $LINENO' ERR

# Run main function
main "$@"