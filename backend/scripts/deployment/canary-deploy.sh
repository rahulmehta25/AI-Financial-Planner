#!/bin/bash

# Canary Deployment Script for Financial Planning API
# This script performs a canary deployment with gradual traffic shifting and automatic rollback

set -euo pipefail

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

# Default values
NAMESPACE="financial-planning-prod"
APP_NAME="financial-planning-api"
IMAGE_TAG=""
INITIAL_WEIGHT=10
PROMOTION_STEPS="10,25,50,75,100"
STEP_DURATION=300  # 5 minutes between steps
TIMEOUT=300
DRY_RUN=false
AUTO_PROMOTE=false
ROLLBACK_ON_FAILURE=true
SLACK_WEBHOOK_URL=""
PROMETHEUS_URL="http://prometheus:9090"

# Canary metrics thresholds
ERROR_RATE_THRESHOLD=0.05  # 5%
LATENCY_THRESHOLD=1000     # 1000ms
MIN_REQUEST_COUNT=100      # Minimum requests for valid metrics

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

Canary Deployment Script for Financial Planning API

OPTIONS:
    -n, --namespace NAMESPACE    Kubernetes namespace (default: financial-planning-prod)
    -t, --tag TAG               Docker image tag to deploy (required)
    -a, --app APP_NAME          Application name (default: financial-planning-api)
    -w, --initial-weight WEIGHT Initial canary traffic weight % (default: 10)
    -s, --steps STEPS           Promotion steps as comma-separated percentages (default: 10,25,50,75,100)
    -d, --duration SECONDS      Duration between promotion steps (default: 300)
    -T, --timeout TIMEOUT       Deployment timeout in seconds (default: 300)
    -p, --auto-promote          Automatically promote based on metrics
    -r, --no-rollback           Don't rollback on failure
    -D, --dry-run               Perform a dry run without actual deployment
    -W, --webhook-url URL       Slack webhook URL for notifications
    -P, --prometheus-url URL    Prometheus URL for metrics (default: http://prometheus:9090)
    -e, --error-threshold PCT   Error rate threshold for auto-promotion (default: 0.05)
    -l, --latency-threshold MS  Latency threshold for auto-promotion (default: 1000)
    -h, --help                  Show this help message

Examples:
    $0 --tag v1.2.3
    $0 --tag v1.2.3 --auto-promote --steps "5,15,50,100"
    $0 --tag latest --initial-weight 5 --duration 600

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
        -w|--initial-weight)
            INITIAL_WEIGHT="$2"
            shift 2
            ;;
        -s|--steps)
            PROMOTION_STEPS="$2"
            shift 2
            ;;
        -d|--duration)
            STEP_DURATION="$2"
            shift 2
            ;;
        -T|--timeout)
            TIMEOUT="$2"
            shift 2
            ;;
        -p|--auto-promote)
            AUTO_PROMOTE=true
            shift
            ;;
        -r|--no-rollback)
            ROLLBACK_ON_FAILURE=false
            shift
            ;;
        -D|--dry-run)
            DRY_RUN=true
            shift
            ;;
        -W|--webhook-url)
            SLACK_WEBHOOK_URL="$2"
            shift 2
            ;;
        -P|--prometheus-url)
            PROMETHEUS_URL="$2"
            shift 2
            ;;
        -e|--error-threshold)
            ERROR_RATE_THRESHOLD="$2"
            shift 2
            ;;
        -l|--latency-threshold)
            LATENCY_THRESHOLD="$2"
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

# Check dependencies
check_dependencies() {
    local deps=("kubectl" "helm" "curl" "jq")
    
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
    local color="${2:-#36a64f}"  # Default green
    
    if [[ -n "$SLACK_WEBHOOK_URL" ]]; then
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"attachments\":[{\"color\":\"$color\",\"text\":\"$message\"}]}" \
            "$SLACK_WEBHOOK_URL" &> /dev/null || true
    fi
}

# Query Prometheus for metrics
query_prometheus() {
    local query="$1"
    local result
    
    result=$(curl -s --max-time 10 \
        "${PROMETHEUS_URL}/api/v1/query?query=${query}" | \
        jq -r '.data.result[0].value[1] // "0"' 2>/dev/null || echo "0")
    
    echo "$result"
}

# Check canary metrics
check_canary_metrics() {
    local canary_version="$1"
    local duration_minutes=5
    
    log_info "Checking canary metrics for version: $canary_version"
    
    # Error rate query
    local error_rate_query
    error_rate_query="rate(http_requests_total{version=\"$canary_version\",status=~\"5..\"}[${duration_minutes}m]) / rate(http_requests_total{version=\"$canary_version\"}[${duration_minutes}m])"
    
    # Latency query (95th percentile)
    local latency_query
    latency_query="histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{version=\"$canary_version\"}[${duration_minutes}m])) * 1000"
    
    # Request count query
    local request_count_query
    request_count_query="sum(rate(http_requests_total{version=\"$canary_version\"}[${duration_minutes}m])) * 60 * $duration_minutes"
    
    local error_rate
    local latency
    local request_count
    
    error_rate=$(query_prometheus "$error_rate_query")
    latency=$(query_prometheus "$latency_query")
    request_count=$(query_prometheus "$request_count_query")
    
    # Convert to proper numeric format for comparison
    error_rate=$(printf "%.4f" "$error_rate" 2>/dev/null || echo "0")
    latency=$(printf "%.0f" "$latency" 2>/dev/null || echo "0")
    request_count=$(printf "%.0f" "$request_count" 2>/dev/null || echo "0")
    
    log_info "Canary metrics:"
    log_info "  Error Rate: ${error_rate} (threshold: ${ERROR_RATE_THRESHOLD})"
    log_info "  95th Percentile Latency: ${latency}ms (threshold: ${LATENCY_THRESHOLD}ms)"
    log_info "  Request Count: ${request_count} (minimum: ${MIN_REQUEST_COUNT})"
    
    # Check if metrics are within acceptable thresholds
    if (( $(echo "$request_count < $MIN_REQUEST_COUNT" | bc -l) )); then
        log_warn "Insufficient request count for reliable metrics"
        return 2  # Insufficient data
    fi
    
    if (( $(echo "$error_rate > $ERROR_RATE_THRESHOLD" | bc -l) )); then
        log_error "Error rate ${error_rate} exceeds threshold ${ERROR_RATE_THRESHOLD}"
        return 1  # Metrics failed
    fi
    
    if (( $(echo "$latency > $LATENCY_THRESHOLD" | bc -l) )); then
        log_error "Latency ${latency}ms exceeds threshold ${LATENCY_THRESHOLD}ms"
        return 1  # Metrics failed
    fi
    
    log_success "Canary metrics are within acceptable thresholds"
    return 0  # Metrics passed
}

# Deploy canary version
deploy_canary() {
    local weight="$1"
    
    log_info "Deploying canary with ${weight}% traffic weight..."
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would deploy canary with ${weight}% traffic"
        return 0
    fi
    
    # Deploy canary using Helm
    if ! helm upgrade --install "$APP_NAME-canary" "./helm/financial-planning" \
        --namespace "$NAMESPACE" \
        --set image.tag="$IMAGE_TAG" \
        --set canary.enabled=true \
        --set canary.weight="$weight" \
        --set replicaCount=1 \
        --set service.type=ClusterIP \
        --wait \
        --timeout="${TIMEOUT}s"; then
        
        log_error "Canary deployment failed"
        return 1
    fi
    
    log_success "Canary deployed with ${weight}% traffic"
}

# Update canary traffic weight
update_canary_weight() {
    local weight="$1"
    
    log_info "Updating canary traffic weight to ${weight}%..."
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would update canary traffic to ${weight}%"
        return 0
    fi
    
    # Update ingress annotation for canary weight
    kubectl annotate ingress "$APP_NAME-canary" -n "$NAMESPACE" \
        nginx.ingress.kubernetes.io/canary-weight="$weight" --overwrite
    
    # If weight is 100%, promote to main deployment
    if [[ "$weight" == "100" ]]; then
        promote_canary
    fi
    
    log_success "Canary traffic weight updated to ${weight}%"
}

# Promote canary to main deployment
promote_canary() {
    log_info "Promoting canary to main deployment..."
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would promote canary to main deployment"
        return 0
    fi
    
    # Update main deployment with canary image
    helm upgrade "$APP_NAME" "./helm/financial-planning" \
        --namespace "$NAMESPACE" \
        --set image.tag="$IMAGE_TAG" \
        --reuse-values
    
    # Remove canary deployment
    helm uninstall "$APP_NAME-canary" --namespace "$NAMESPACE"
    
    log_success "Canary promoted to main deployment"
}

# Rollback canary deployment
rollback_canary() {
    log_warn "Rolling back canary deployment..."
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would rollback canary deployment"
        return 0
    fi
    
    # Remove canary deployment
    helm uninstall "$APP_NAME-canary" --namespace "$NAMESPACE" --ignore-not-found
    
    log_success "Canary deployment rolled back"
    
    # Send notification
    send_slack_notification "🚨 Canary deployment rolled back due to failed metrics" "#ff0000"
}

# Wait for user confirmation
wait_for_confirmation() {
    local weight="$1"
    
    if [[ "$AUTO_PROMOTE" == "true" ]]; then
        return 0
    fi
    
    echo
    log_info "Current canary traffic: ${weight}%"
    read -p "Continue to next step? (y/n/r for rollback): " -n 1 -r
    echo
    
    case $REPLY in
        [Yy])
            return 0
            ;;
        [Rr])
            return 2  # Rollback requested
            ;;
        *)
            return 1  # Stop deployment
            ;;
    esac
}

# Main canary deployment function
main() {
    log_info "Starting Canary deployment for $APP_NAME with image tag: $IMAGE_TAG"
    log_info "Namespace: $NAMESPACE"
    log_info "Initial weight: ${INITIAL_WEIGHT}%"
    log_info "Promotion steps: $PROMOTION_STEPS"
    log_info "Step duration: ${STEP_DURATION}s"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_warn "DRY RUN MODE - No actual changes will be made"
    fi
    
    if [[ "$AUTO_PROMOTE" == "true" ]]; then
        log_info "Auto-promotion enabled based on metrics"
    fi
    
    # Check dependencies
    check_dependencies
    
    # Send start notification
    send_slack_notification "🐤 Starting Canary deployment of $APP_NAME:$IMAGE_TAG"
    
    # Deploy initial canary
    if ! deploy_canary "$INITIAL_WEIGHT"; then
        log_error "Failed to deploy initial canary"
        send_slack_notification "❌ Canary deployment failed during initial deployment" "#ff0000"
        exit 1
    fi
    
    # Wait for canary to be ready
    sleep 30
    
    # Process promotion steps
    IFS=',' read -ra STEPS <<< "$PROMOTION_STEPS"
    
    for step in "${STEPS[@]}"; do
        step=$(echo "$step" | tr -d ' ')  # Remove whitespace
        
        log_info "Processing step: ${step}% traffic"
        
        # Update canary weight
        if ! update_canary_weight "$step"; then
            log_error "Failed to update canary weight to ${step}%"
            if [[ "$ROLLBACK_ON_FAILURE" == "true" ]]; then
                rollback_canary
            fi
            exit 1
        fi
        
        # If this is the final step (100%), we're done
        if [[ "$step" == "100" ]]; then
            log_success "Canary deployment completed successfully!"
            send_slack_notification "✅ Canary deployment of $APP_NAME:$IMAGE_TAG completed successfully"
            break
        fi
        
        # Wait for metrics to stabilize
        log_info "Waiting ${STEP_DURATION}s for metrics to stabilize..."
        sleep "$STEP_DURATION"
        
        # Check metrics if auto-promotion is enabled
        if [[ "$AUTO_PROMOTE" == "true" ]]; then
            local metrics_result=0
            check_canary_metrics "canary" || metrics_result=$?
            
            case $metrics_result in
                0)
                    log_success "Metrics check passed, continuing to next step"
                    ;;
                1)
                    log_error "Metrics check failed"
                    if [[ "$ROLLBACK_ON_FAILURE" == "true" ]]; then
                        rollback_canary
                        exit 1
                    fi
                    ;;
                2)
                    log_warn "Insufficient metrics data, continuing with caution"
                    ;;
            esac
        else
            # Manual confirmation
            local confirm_result=0
            wait_for_confirmation "$step" || confirm_result=$?
            
            case $confirm_result in
                0)
                    log_info "Continuing to next step"
                    ;;
                1)
                    log_info "Deployment stopped by user"
                    exit 0
                    ;;
                2)
                    log_warn "Rollback requested by user"
                    rollback_canary
                    exit 0
                    ;;
            esac
        fi
    done
    
    # Final success message
    log_success "Canary deployment completed successfully!"
    log_info "Application: $APP_NAME"
    log_info "Image Tag: $IMAGE_TAG"
    log_info "Namespace: $NAMESPACE"
    
    # Send final notification
    send_slack_notification "🎉 Canary deployment of $APP_NAME:$IMAGE_TAG completed and promoted successfully"
}

# Error handling
handle_error() {
    local exit_code=$?
    local line_number=$1
    
    log_error "Script failed on line $line_number with exit code $exit_code"
    
    if [[ "$ROLLBACK_ON_FAILURE" == "true" ]]; then
        log_warn "Attempting to rollback canary deployment..."
        rollback_canary || true
    fi
    
    send_slack_notification "💥 Canary deployment script failed on line $line_number" "#ff0000"
    
    exit $exit_code
}

trap 'handle_error $LINENO' ERR

# Install bc for arithmetic comparisons if not available
if ! command -v bc &> /dev/null; then
    log_warn "bc is not installed. Numeric comparisons may not work correctly."
    log_info "Please install bc: apt-get install bc (Ubuntu/Debian) or brew install bc (macOS)"
fi

# Run main function
main "$@"