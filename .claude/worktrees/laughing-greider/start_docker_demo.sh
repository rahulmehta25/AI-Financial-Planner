#!/bin/bash

# Financial Planning System - Docker Demo Startup Script
# One-command bulletproof demo deployment
# Usage: ./start_docker_demo.sh [options]

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_FILE="docker-compose.demo.yml"
ENV_FILE=".env.demo"
PROJECT_NAME="financial-planning-demo"
HEALTH_CHECK_TIMEOUT=180

# Default options
DETACH=false
REBUILD=false
CLEAN=false
MONITORING=false
VERBOSE=false
QUICK_START=false

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${PURPLE}$1${NC}"
}

# Function to show usage
show_usage() {
    cat << EOF
Financial Planning System - Docker Demo

Usage: $0 [options]

Options:
    -d, --detach        Run in detached mode (background)
    -r, --rebuild       Force rebuild of Docker images
    -c, --clean         Clean up existing containers and volumes
    -m, --monitoring    Enable monitoring services (Prometheus, Grafana)
    -v, --verbose       Verbose output
    -q, --quick         Quick start (skip health checks)
    -h, --help          Show this help message

Examples:
    $0                  Start demo in foreground
    $0 -d               Start demo in background
    $0 -r -d            Rebuild images and start in background
    $0 -c -r            Clean environment, rebuild, and start

URLs after startup:
    Main Application:    http://localhost
    Frontend Direct:     http://localhost:3000
    Backend API:         http://localhost:8000
    API Documentation:   http://localhost:8000/docs
    Redis (if exposed):  localhost:6379

Demo Credentials:
    Email:    demo@financialplanning.com
    Password: demo123
EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -d|--detach)
            DETACH=true
            shift
            ;;
        -r|--rebuild)
            REBUILD=true
            shift
            ;;
        -c|--clean)
            CLEAN=true
            shift
            ;;
        -m|--monitoring)
            MONITORING=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -q|--quick)
            QUICK_START=true
            shift
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Function to check prerequisites
check_prerequisites() {
    print_header "🔍 Checking Prerequisites"
    
    # Check if Docker is installed and running
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        print_error "Docker is not running. Please start Docker first."
        exit 1
    fi
    
    # Check if Docker Compose is available
    if ! docker compose version &> /dev/null; then
        print_error "Docker Compose is not available. Please install Docker Compose."
        exit 1
    fi
    
    # Check if compose file exists
    if [[ ! -f "$COMPOSE_FILE" ]]; then
        print_error "Docker Compose file ($COMPOSE_FILE) not found in current directory."
        exit 1
    fi
    
    # Check if environment file exists
    if [[ ! -f "$ENV_FILE" ]]; then
        print_warning "Environment file ($ENV_FILE) not found. Using defaults."
    fi
    
    # Check available disk space (minimum 2GB)
    available_space=$(df -BG . | awk 'NR==2 {print $4}' | sed 's/G//')
    if [[ $available_space -lt 2 ]]; then
        print_warning "Low disk space available: ${available_space}GB. Minimum 2GB recommended."
    fi
    
    # Check available memory (minimum 2GB)
    if command -v free &> /dev/null; then
        available_memory=$(free -g | awk 'NR==2{print $7}')
        if [[ $available_memory -lt 2 ]]; then
            print_warning "Low memory available: ${available_memory}GB. Minimum 2GB recommended."
        fi
    fi
    
    print_success "Prerequisites check completed"
}

# Function to clean up existing containers
cleanup_environment() {
    print_header "🧹 Cleaning Up Environment"
    
    # Stop and remove containers
    docker compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" down -v --remove-orphans 2>/dev/null || true
    
    # Remove unused networks
    docker network prune -f 2>/dev/null || true
    
    # Remove unused volumes if requested
    if [[ "$CLEAN" == true ]]; then
        print_status "Removing volumes..."
        docker volume ls -q | grep -E "${PROJECT_NAME}_" | xargs -r docker volume rm 2>/dev/null || true
    fi
    
    # Clean up dangling images
    if [[ "$REBUILD" == true ]]; then
        print_status "Removing old images..."
        docker image prune -f 2>/dev/null || true
    fi
    
    print_success "Environment cleaned up"
}

# Function to build and start services
start_services() {
    print_header "🚀 Starting Demo Services"
    
    # Prepare Docker Compose command
    compose_cmd="docker compose -f $COMPOSE_FILE -p $PROJECT_NAME"
    
    # Add environment file if it exists
    if [[ -f "$ENV_FILE" ]]; then
        compose_cmd="$compose_cmd --env-file $ENV_FILE"
    fi
    
    # Add monitoring profile if requested
    if [[ "$MONITORING" == true ]]; then
        compose_cmd="$compose_cmd --profile monitoring"
    fi
    
    # Build arguments
    build_args="up"
    
    if [[ "$REBUILD" == true ]]; then
        build_args="$build_args --build"
    fi
    
    if [[ "$DETACH" == true ]]; then
        build_args="$build_args -d"
    fi
    
    # Execute Docker Compose
    print_status "Building and starting services..."
    if [[ "$VERBOSE" == true ]]; then
        eval "$compose_cmd $build_args"
    else
        eval "$compose_cmd $build_args" > /dev/null 2>&1 &
        local compose_pid=$!
        
        # Show progress indicator
        local spinner='-\|/'
        local i=0
        while kill -0 $compose_pid 2>/dev/null; do
            printf "\r${CYAN}Building services... ${spinner:$((i%4)):1}${NC}"
            sleep 0.5
            ((i++))
        done
        printf "\r${GREEN}✓ Services built and started${NC}\n"
        
        wait $compose_pid
        if [[ $? -ne 0 ]]; then
            print_error "Failed to start services"
            exit 1
        fi
    fi
    
    print_success "Services started successfully"
}

# Function to wait for services to be healthy
wait_for_health() {
    if [[ "$QUICK_START" == true ]]; then
        print_status "Skipping health checks (quick start mode)"
        return 0
    fi
    
    print_header "🏥 Waiting for Services to be Healthy"
    
    local services=("redis" "backend" "frontend" "nginx")
    local timeout=$HEALTH_CHECK_TIMEOUT
    local interval=5
    local elapsed=0
    
    while [[ $elapsed -lt $timeout ]]; do
        local healthy_count=0
        
        for service in "${services[@]}"; do
            local status=$(docker compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" ps -q $service 2>/dev/null | xargs -r docker inspect --format='{{.State.Health.Status}}' 2>/dev/null || echo "unknown")
            
            if [[ "$status" == "healthy" ]] || [[ "$service" == "redis" && "$status" == "" ]]; then
                ((healthy_count++))
            else
                printf "\r${CYAN}Waiting for $service to be healthy... (${elapsed}s/${timeout}s)${NC}"
            fi
        done
        
        if [[ $healthy_count -eq ${#services[@]} ]]; then
            printf "\r${GREEN}✓ All services are healthy${NC}\n"
            return 0
        fi
        
        sleep $interval
        elapsed=$((elapsed + interval))
    done
    
    print_warning "Health check timeout reached. Services may still be starting..."
    return 1
}

# Function to verify services are accessible
verify_services() {
    print_header "🔗 Verifying Service Accessibility"
    
    local services_to_check=(
        "http://localhost:80|Main Application"
        "http://localhost:3000|Frontend"
        "http://localhost:8000/health|Backend Health"
        "http://localhost:8000/docs|API Documentation"
    )
    
    for service_info in "${services_to_check[@]}"; do
        IFS='|' read -r url name <<< "$service_info"
        
        if curl -s -f "$url" > /dev/null 2>&1; then
            print_success "$name is accessible at $url"
        else
            print_warning "$name is not accessible at $url (may still be starting)"
        fi
    done
}

# Function to show final status and information
show_final_status() {
    print_header "🎉 Demo Deployment Complete!"
    
    echo ""
    echo -e "${GREEN}Financial Planning System Demo is now running!${NC}"
    echo ""
    echo -e "${CYAN}📱 Access URLs:${NC}"
    echo -e "  Main Application:     ${YELLOW}http://localhost${NC}"
    echo -e "  Frontend (Direct):    ${YELLOW}http://localhost:3000${NC}"
    echo -e "  Backend API:          ${YELLOW}http://localhost:8000${NC}"
    echo -e "  API Documentation:    ${YELLOW}http://localhost:8000/docs${NC}"
    echo -e "  OpenAPI Spec:         ${YELLOW}http://localhost:8000/openapi.json${NC}"
    
    if [[ "$MONITORING" == true ]]; then
        echo -e "  Prometheus:           ${YELLOW}http://localhost:9091${NC}"
        echo -e "  Grafana:              ${YELLOW}http://localhost:3001${NC} (admin/admin)"
    fi
    
    echo ""
    echo -e "${CYAN}🔑 Demo Credentials:${NC}"
    echo -e "  Email:    ${YELLOW}demo@financialplanning.com${NC}"
    echo -e "  Password: ${YELLOW}demo123${NC}"
    echo ""
    
    echo -e "${CYAN}🛠️ Useful Commands:${NC}"
    echo -e "  View logs:            ${YELLOW}docker compose -f $COMPOSE_FILE -p $PROJECT_NAME logs -f${NC}"
    echo -e "  Stop demo:            ${YELLOW}docker compose -f $COMPOSE_FILE -p $PROJECT_NAME down${NC}"
    echo -e "  Stop and cleanup:     ${YELLOW}docker compose -f $COMPOSE_FILE -p $PROJECT_NAME down -v${NC}"
    echo -e "  Restart service:      ${YELLOW}docker compose -f $COMPOSE_FILE -p $PROJECT_NAME restart <service>${NC}"
    echo ""
    
    if [[ "$DETACH" != true ]]; then
        echo -e "${CYAN}Press Ctrl+C to stop the demo${NC}"
        echo ""
    fi
}

# Function to handle cleanup on exit
cleanup_on_exit() {
    if [[ "$DETACH" != true ]]; then
        print_header "🛑 Stopping Demo Services"
        docker compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" down
        print_success "Demo stopped"
    fi
}

# Main execution
main() {
    print_header "🏦 Financial Planning System - Docker Demo Startup"
    echo ""
    
    # Set up signal handlers
    trap cleanup_on_exit INT TERM
    
    # Execute main workflow
    check_prerequisites
    
    if [[ "$CLEAN" == true ]] || [[ "$REBUILD" == true ]]; then
        cleanup_environment
    fi
    
    start_services
    
    if [[ "$DETACH" == true ]]; then
        wait_for_health || true
        verify_services
    fi
    
    show_final_status
    
    # If not running in detach mode, wait for user interrupt
    if [[ "$DETACH" != true ]]; then
        wait
    fi
}

# Run main function
main