#!/bin/bash

# Rollback Script for Financial Planning API
# This script provides comprehensive rollback capabilities for various deployment strategies

set -euo pipefail

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

# Default values
NAMESPACE="financial-planning-prod"
APP_NAME="financial-planning-api"
ROLLBACK_TYPE="helm"  # helm, blue-green, canary
REVISION=""
DRY_RUN=false
FORCE=false
SKIP_CONFIRMATION=false
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

Rollback Script for Financial Planning API

OPTIONS:
    -n, --namespace NAMESPACE    Kubernetes namespace (default: financial-planning-prod)
    -a, --app APP_NAME          Application name (default: financial-planning-api)
    -t, --type TYPE             Rollback type: helm, blue-green, canary (default: helm)
    -r, --revision REVISION     Helm revision to rollback to (for helm rollback)
    -d, --dry-run               Perform a dry run without actual rollback
    -f, --force                 Force rollback without confirmation
    -s, --skip-confirmation     Skip user confirmation prompts
    -w, --webhook-url URL       Slack webhook URL for notifications
    -h, --help                  Show this help message

Rollback Types:
    helm        - Rollback using Helm revision history
    blue-green  - Switch traffic back to previous blue/green slot
    canary      - Remove canary deployment and restore main deployment

Examples:
    $0                                    # Simple helm rollback to previous revision
    $0 --type helm --revision 5          # Rollback to specific helm revision
    $0 --type blue-green --force          # Force blue-green traffic switch
    $0 --type canary --dry-run            # Dry run canary rollback

EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -n|--namespace)
            NAMESPACE="$2"
            shift 2
            ;;
        -a|--app)
            APP_NAME="$2"
            shift 2
            ;;
        -t|--type)
            ROLLBACK_TYPE="$2"
            shift 2
            ;;
        -r|--revision)
            REVISION="$2"
            shift 2
            ;;
        -d|--dry-run)
            DRY_RUN=true
            shift
            ;;
        -f|--force)
            FORCE=true
            shift
            ;;
        -s|--skip-confirmation)
            SKIP_CONFIRMATION=true
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

# Check dependencies
check_dependencies() {
    local deps=("kubectl" "helm")
    
    for dep in "${deps[@]}"; do
        if ! command -v "$dep" &> /dev/null; then
            log_error "$dep is not installed or not in PATH"
            exit 1
        fi
    done
}

# Send Slack notification
send_slack_notification() {
    local message="$1"
    local color="${2:-#ff9900}"  # Default orange
    
    if [[ -n "$SLACK_WEBHOOK_URL" ]]; then
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"attachments\":[{\"color\":\"$color\",\"text\":\"$message\"}]}" \
            "$SLACK_WEBHOOK_URL" &> /dev/null || true
    fi
}

# Get user confirmation
get_confirmation() {
    local message="$1"
    
    if [[ "$FORCE" == "true" || "$SKIP_CONFIRMATION" == "true" ]]; then
        return 0
    fi
    
    echo
    log_warn "$message"
    read -p "Are you sure you want to continue? (yes/no): " -r
    echo
    
    if [[ "$REPLY" != "yes" ]]; then
        log_info "Operation cancelled by user"
        exit 0
    fi
}

# Show current deployment status
show_current_status() {
    log_info "Current deployment status:"
    
    # Show helm releases
    log_info "Helm releases:"
    helm list -n "$NAMESPACE" | grep -E "(NAME|$APP_NAME)" || true
    
    # Show deployments
    log_info "Deployments:"
    kubectl get deployments -n "$NAMESPACE" -l app.kubernetes.io/name="$APP_NAME" || true
    
    # Show services
    log_info "Services:"
    kubectl get services -n "$NAMESPACE" -l app.kubernetes.io/name="$APP_NAME" || true
}

# Helm rollback
helm_rollback() {
    log_info "Performing Helm rollback for $APP_NAME in namespace $NAMESPACE"
    
    # Show helm history
    log_info "Helm release history:"
    if ! helm history "$APP_NAME" -n "$NAMESPACE" --max 10; then
        log_error "Failed to get Helm history. Release may not exist."
        exit 1
    fi
    
    # Determine revision to rollback to
    local target_revision="$REVISION"
    if [[ -z "$target_revision" ]]; then
        # Get previous revision
        target_revision=$(helm history "$APP_NAME" -n "$NAMESPACE" --max 2 --output json | \
            jq -r '.[1].revision // empty' 2>/dev/null || echo "")
        
        if [[ -z "$target_revision" ]]; then
            log_error "No previous revision found for rollback"
            exit 1
        fi
    fi
    
    log_info "Rolling back to revision: $target_revision"
    
    get_confirmation "This will rollback $APP_NAME to revision $target_revision"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would rollback to revision $target_revision"
        return 0
    fi
    
    # Perform rollback
    if helm rollback "$APP_NAME" "$target_revision" -n "$NAMESPACE" --wait --timeout=300s; then
        log_success "Helm rollback completed successfully"
        
        # Show new status
        helm status "$APP_NAME" -n "$NAMESPACE"
    else
        log_error "Helm rollback failed"
        exit 1
    fi
}

# Blue-Green rollback
blue_green_rollback() {
    log_info "Performing Blue-Green rollback for $APP_NAME in namespace $NAMESPACE"
    
    # Get current active slot
    local current_selector
    current_selector=$(kubectl get service "$APP_NAME" -n "$NAMESPACE" \
        -o jsonpath='{.spec.selector.version}' 2>/dev/null || echo "")
    
    if [[ -z "$current_selector" ]]; then
        log_error "Could not determine current active slot"
        exit 1
    fi
    
    local previous_slot
    if [[ "$current_selector" == "blue" ]]; then
        previous_slot="green"
    else
        previous_slot="blue"
    fi
    
    log_info "Current active slot: $current_selector"
    log_info "Will switch back to: $previous_slot"
    
    # Check if previous slot deployment exists
    if ! kubectl get deployment "$APP_NAME-$previous_slot" -n "$NAMESPACE" &> /dev/null; then
        log_error "Previous deployment ($APP_NAME-$previous_slot) not found"
        log_info "Available deployments:"
        kubectl get deployments -n "$NAMESPACE" -l app.kubernetes.io/name="$APP_NAME" --no-headers | awk '{print $1}' || true
        exit 1
    fi
    
    # Check if previous deployment is healthy
    local ready_replicas
    ready_replicas=$(kubectl get deployment "$APP_NAME-$previous_slot" -n "$NAMESPACE" \
        -o jsonpath='{.status.readyReplicas}' 2>/dev/null || echo "0")
    
    if [[ "$ready_replicas" -eq 0 ]]; then
        log_warn "Previous deployment has no ready replicas. This rollback may cause downtime."
    fi
    
    get_confirmation "This will switch traffic from $current_selector to $previous_slot slot"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would switch traffic to $previous_slot slot"
        return 0
    fi
    
    # Switch traffic
    kubectl patch service "$APP_NAME" -n "$NAMESPACE" \
        -p "{\"spec\":{\"selector\":{\"version\":\"$previous_slot\"}}}"
    
    # Wait for traffic switch to take effect
    sleep 10
    
    # Verify health
    if kubectl wait --for=condition=ready pod \
        -l app.kubernetes.io/name="$APP_NAME",version="$previous_slot" \
        -n "$NAMESPACE" \
        --timeout=60s; then
        log_success "Blue-Green rollback completed successfully"
        log_info "Traffic switched to $previous_slot slot"
    else
        log_error "Health check failed after rollback"
        exit 1
    fi
}

# Canary rollback
canary_rollback() {
    log_info "Performing Canary rollback for $APP_NAME in namespace $NAMESPACE"
    
    # Check if canary deployment exists
    if ! helm status "$APP_NAME-canary" -n "$NAMESPACE" &> /dev/null; then
        log_warn "No canary deployment found"
        log_info "Current releases:"
        helm list -n "$NAMESPACE" | grep -E "(NAME|$APP_NAME)" || true
        exit 1
    fi
    
    # Show canary status
    log_info "Current canary deployment:"
    helm status "$APP_NAME-canary" -n "$NAMESPACE" --short
    
    get_confirmation "This will remove the canary deployment and restore normal traffic flow"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would remove canary deployment"
        return 0
    fi
    
    # Remove canary deployment
    if helm uninstall "$APP_NAME-canary" -n "$NAMESPACE"; then
        log_success "Canary deployment removed successfully"
    else
        log_error "Failed to remove canary deployment"
        exit 1
    fi
    
    # Verify main deployment is healthy
    if kubectl wait --for=condition=ready pod \
        -l app.kubernetes.io/name="$APP_NAME" \
        -n "$NAMESPACE" \
        --timeout=60s; then
        log_success "Main deployment is healthy after canary removal"
    else
        log_warn "Main deployment may not be fully healthy"
    fi
}

# Database rollback (if needed)
database_rollback() {
    log_warn "Database rollback is a destructive operation!"
    log_info "This would typically involve:"
    log_info "1. Stopping the application"
    log_info "2. Restoring database from backup"
    log_info "3. Running database migrations downward"
    log_info "4. Restarting application with previous version"
    
    get_confirmation "Database rollback is not automated. Please perform manually if needed."
}

# Health check after rollback
post_rollback_health_check() {
    log_info "Performing post-rollback health check..."
    
    # Check deployment status
    if kubectl get deployment "$APP_NAME" -n "$NAMESPACE" &> /dev/null; then
        kubectl rollout status deployment/"$APP_NAME" -n "$NAMESPACE" --timeout=60s || true
    fi
    
    # Port forward and test health endpoint
    local local_port=8080
    kubectl port-forward "service/$APP_NAME" "$local_port:80" -n "$NAMESPACE" &
    local port_forward_pid=$!
    
    # Cleanup function
    cleanup_port_forward() {
        if kill -0 "$port_forward_pid" 2>/dev/null; then
            kill "$port_forward_pid"
        fi
    }
    trap cleanup_port_forward EXIT
    
    # Wait for port-forward
    sleep 5
    
    # Test health endpoint
    if curl -f --max-time 10 "http://localhost:$local_port/health" &> /dev/null; then
        log_success "Health check passed after rollback"
    else
        log_warn "Health check failed - application may not be fully functional"
    fi
    
    cleanup_port_forward
    trap - EXIT
}

# Main rollback function
main() {
    log_info "Starting rollback process for $APP_NAME"
    log_info "Namespace: $NAMESPACE"
    log_info "Rollback type: $ROLLBACK_TYPE"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_warn "DRY RUN MODE - No actual changes will be made"
    fi
    
    # Check dependencies
    check_dependencies
    
    # Show current status
    show_current_status
    
    # Send start notification
    send_slack_notification "🔄 Starting rollback of $APP_NAME using $ROLLBACK_TYPE method"
    
    # Perform rollback based on type
    case "$ROLLBACK_TYPE" in
        "helm")
            helm_rollback
            ;;
        "blue-green")
            blue_green_rollback
            ;;
        "canary")
            canary_rollback
            ;;
        *)
            log_error "Unknown rollback type: $ROLLBACK_TYPE"
            log_info "Supported types: helm, blue-green, canary"
            exit 1
            ;;
    esac
    
    # Post-rollback health check
    if [[ "$DRY_RUN" == "false" ]]; then
        post_rollback_health_check
    fi
    
    # Final status
    log_info "Final deployment status:"
    show_current_status
    
    log_success "Rollback completed successfully!"
    
    # Send success notification
    send_slack_notification "✅ Rollback of $APP_NAME completed successfully using $ROLLBACK_TYPE method" "#36a64f"
}

# Error handling
handle_error() {
    local exit_code=$?
    local line_number=$1
    
    log_error "Rollback script failed on line $line_number with exit code $exit_code"
    send_slack_notification "💥 Rollback of $APP_NAME failed on line $line_number" "#ff0000"
    
    exit $exit_code
}

trap 'handle_error $LINENO' ERR

# Run main function
main "$@"