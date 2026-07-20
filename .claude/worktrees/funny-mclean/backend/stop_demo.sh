#!/bin/bash

# Financial Planning System - Demo Shutdown Script
# Graceful service shutdown with resource cleanup and data preservation
# Supports: macOS, Linux, Windows WSL

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="financial-planning"
SHUTDOWN_TIMEOUT=${SHUTDOWN_TIMEOUT:-30}
PRESERVE_DATA=${PRESERVE_DATA:-true}
FORCE_STOP=${FORCE_STOP:-false}

# Logging functions
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

print_header() {
    echo "================================================================"
    echo "🛑 Financial Planning System - Demo Environment Shutdown"
    echo "================================================================"
    echo "Preserve Data: $PRESERVE_DATA"
    echo "Force Stop: $FORCE_STOP"
    echo "Timeout: ${SHUTDOWN_TIMEOUT}s"
    echo "Timestamp: $(date)"
    echo "================================================================"
}

save_demo_data() {
    if [ "$PRESERVE_DATA" = "true" ]; then
        log_info "Saving demo data before shutdown..."
        
        # Create backup directory with timestamp
        local backup_dir="backups/demo-$(date +%Y%m%d-%H%M%S)"
        mkdir -p "$backup_dir"
        
        # Export database if running
        if docker-compose ps postgres | grep -q "Up"; then
            log_info "Exporting database..."
            if docker-compose exec -T postgres pg_dump -U financial_planning -d financial_planning > "$backup_dir/database.sql" 2>/dev/null; then
                log_success "Database exported to $backup_dir/database.sql"
            else
                log_warning "Database export failed or database not accessible"
            fi
        fi
        
        # Save application logs
        if [ -d "logs" ]; then
            log_info "Archiving application logs..."
            cp -r logs "$backup_dir/logs" 2>/dev/null || true
            log_success "Logs archived to $backup_dir/logs"
        fi
        
        # Save generated reports/exports
        if [ -d "exports" ]; then
            log_info "Archiving generated reports..."
            cp -r exports "$backup_dir/exports" 2>/dev/null || true
            log_success "Reports archived to $backup_dir/exports"
        fi
        
        # Save configuration
        if [ -f ".env" ]; then
            cp .env "$backup_dir/.env.backup" 2>/dev/null || true
            log_success "Configuration backed up"
        fi
        
        log_success "Demo data saved to $backup_dir"
    else
        log_info "Skipping data preservation (PRESERVE_DATA=false)"
    fi
}

stop_services_gracefully() {
    log_info "Stopping services gracefully..."
    
    # Get list of running services
    local running_services=$(docker-compose ps --services --filter "status=running" 2>/dev/null || true)
    
    if [ -z "$running_services" ]; then
        log_info "No running services found"
        return 0
    fi
    
    log_info "Running services: $(echo $running_services | tr '\n' ' ')"
    
    # Stop application services first (reverse order of startup)
    local app_services=("nginx" "celery-beat" "celery-worker" "api")
    for service in "${app_services[@]}"; do
        if echo "$running_services" | grep -q "^$service$"; then
            log_info "Stopping $service..."
            if timeout $SHUTDOWN_TIMEOUT docker-compose stop "$service" 2>/dev/null; then
                log_success "$service stopped gracefully"
            else
                log_warning "$service stop timed out, will force stop later"
            fi
        fi
    done
    
    # Stop infrastructure services
    local infra_services=("redis" "postgres")
    for service in "${infra_services[@]}"; do
        if echo "$running_services" | grep -q "^$service$"; then
            log_info "Stopping $service..."
            if timeout $SHUTDOWN_TIMEOUT docker-compose stop "$service" 2>/dev/null; then
                log_success "$service stopped gracefully"
            else
                log_warning "$service stop timed out, will force stop later"
            fi
        fi
    done
    
    # Stop any remaining services (monitoring, admin tools, etc.)
    log_info "Stopping any remaining services..."
    if timeout $SHUTDOWN_TIMEOUT docker-compose stop 2>/dev/null; then
        log_success "All services stopped gracefully"
    else
        log_warning "Some services failed to stop gracefully"
    fi
}

force_stop_services() {
    if [ "$FORCE_STOP" = "true" ]; then
        log_warning "Force stopping all services..."
        docker-compose kill 2>/dev/null || true
        log_success "Services force stopped"
    fi
}

cleanup_containers() {
    log_info "Removing containers..."
    
    # Remove containers
    if docker-compose down --remove-orphans 2>/dev/null; then
        log_success "Containers removed successfully"
    else
        log_warning "Some containers may not have been removed properly"
    fi
    
    # Clean up orphaned containers
    local orphaned=$(docker ps -a --filter "label=com.docker.compose.project=$PROJECT_NAME" --format "{{.Names}}" 2>/dev/null || true)
    if [ -n "$orphaned" ]; then
        log_info "Cleaning up orphaned containers..."
        echo "$orphaned" | xargs docker rm -f 2>/dev/null || true
        log_success "Orphaned containers cleaned up"
    fi
}

cleanup_networks() {
    log_info "Cleaning up networks..."
    
    # Remove project networks
    local networks=$(docker network ls --filter "name=${PROJECT_NAME}" --format "{{.Name}}" 2>/dev/null || true)
    if [ -n "$networks" ]; then
        echo "$networks" | xargs docker network rm 2>/dev/null || true
        log_success "Project networks removed"
    fi
    
    # Clean up unused networks
    docker network prune -f &>/dev/null || true
}

cleanup_volumes() {
    local preserve_volumes=${PRESERVE_VOLUMES:-$PRESERVE_DATA}
    
    if [ "$preserve_volumes" = "true" ]; then
        log_info "Preserving Docker volumes (PRESERVE_VOLUMES=true)"
        return 0
    fi
    
    log_warning "Removing Docker volumes (this will delete all data!)..."
    
    # Give user a chance to abort
    if [ "${INTERACTIVE:-true}" = "true" ] && [ -t 0 ]; then
        echo -n "Are you sure you want to delete all data volumes? [y/N]: "
        read -r response
        if [[ ! "$response" =~ ^[Yy]$ ]]; then
            log_info "Volume cleanup cancelled"
            return 0
        fi
    fi
    
    # Remove project volumes
    docker-compose down -v 2>/dev/null || true
    log_success "Project volumes removed"
    
    # Clean up orphaned volumes
    docker volume prune -f &>/dev/null || true
    log_success "Orphaned volumes cleaned up"
}

cleanup_images() {
    local cleanup_images=${CLEANUP_IMAGES:-false}
    
    if [ "$cleanup_images" = "true" ]; then
        log_info "Cleaning up Docker images..."
        
        # Remove project images
        local images=$(docker images --filter "reference=${PROJECT_NAME}*" --format "{{.Repository}}:{{.Tag}}" 2>/dev/null || true)
        if [ -n "$images" ]; then
            echo "$images" | xargs docker rmi -f 2>/dev/null || true
            log_success "Project images removed"
        fi
        
        # Clean up dangling images
        docker image prune -f &>/dev/null || true
        log_success "Dangling images cleaned up"
    fi
}

cleanup_temporary_files() {
    log_info "Cleaning up temporary files..."
    
    # Clean up temporary directories
    local temp_dirs=("tmp" "temp" ".pytest_cache" "__pycache__")
    for dir in "${temp_dirs[@]}"; do
        if [ -d "$dir" ]; then
            rm -rf "$dir" 2>/dev/null || true
        fi
    done
    
    # Clean up log files if not preserving data
    if [ "$PRESERVE_DATA" = "false" ]; then
        if [ -d "logs" ]; then
            rm -rf logs/* 2>/dev/null || true
            log_success "Log files cleaned up"
        fi
    fi
    
    # Clean up Python cache files
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete 2>/dev/null || true
    
    log_success "Temporary files cleaned up"
}

verify_shutdown() {
    log_info "Verifying shutdown..."
    
    # Check for running containers
    local running_containers=$(docker-compose ps -q 2>/dev/null || true)
    if [ -n "$running_containers" ]; then
        log_warning "Some containers are still running:"
        docker-compose ps
        return 1
    fi
    
    # Check for listening ports
    local listening_ports=$(netstat -an 2>/dev/null | grep -E ":(8000|5432|6379|3000|9091|5050|8081).*LISTEN" || true)
    if [ -n "$listening_ports" ]; then
        log_warning "Some ports are still in use:"
        echo "$listening_ports"
        return 1
    fi
    
    log_success "Shutdown verification completed"
    return 0
}

print_shutdown_summary() {
    echo ""
    echo "================================================================"
    echo "✅ Financial Planning Demo Environment Shutdown Complete"
    echo "================================================================"
    echo ""
    echo "📊 Shutdown Summary:"
    echo "  • Services stopped: ✓"
    echo "  • Containers removed: ✓"
    echo "  • Networks cleaned: ✓"
    
    if [ "$PRESERVE_DATA" = "true" ]; then
        echo "  • Data preserved: ✓"
        echo "  • Backup location: backups/demo-$(date +%Y%m%d)*"
    else
        echo "  • Data removed: ✓"
    fi
    
    echo ""
    echo "🔄 To restart the demo:"
    echo "  ./start_demo.sh"
    echo ""
    echo "🗂️ To restore from backup (if preserved):"
    echo "  ./reset_demo.sh --restore backups/demo-YYYYMMDD-HHMMSS"
    echo ""
    echo "🧹 To perform complete cleanup:"
    echo "  PRESERVE_DATA=false CLEANUP_IMAGES=true ./stop_demo.sh"
    echo ""
    echo "================================================================"
}

handle_signals() {
    log_info "Received signal, initiating graceful shutdown..."
    FORCE_STOP=true
    main
}

main() {
    print_header
    
    # Handle interruption signals
    trap 'handle_signals' INT TERM
    
    # Save data before shutdown
    save_demo_data
    
    # Stop services
    stop_services_gracefully
    force_stop_services
    
    # Cleanup resources
    cleanup_containers
    cleanup_networks
    cleanup_volumes
    cleanup_images
    cleanup_temporary_files
    
    # Verify and report
    if verify_shutdown; then
        print_shutdown_summary
        log_success "Demo environment shutdown completed successfully!"
    else
        log_warning "Shutdown completed with warnings. Some resources may still be active."
        log_info "Run with FORCE_STOP=true to force cleanup"
    fi
}

# Help function
show_help() {
    echo "Financial Planning Demo - Shutdown Script"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -h, --help              Show this help message"
    echo "  -f, --force             Force stop all services"
    echo "  -p, --preserve          Preserve data (default: true)"
    echo "  -n, --no-preserve       Don't preserve data"
    echo "  -c, --cleanup-images    Remove Docker images"
    echo "  -t, --timeout SECONDS   Set shutdown timeout (default: 30)"
    echo ""
    echo "Environment Variables:"
    echo "  PRESERVE_DATA=true|false    Preserve demo data (default: true)"
    echo "  FORCE_STOP=true|false       Force stop services (default: false)"
    echo "  CLEANUP_IMAGES=true|false   Remove Docker images (default: false)"
    echo "  PRESERVE_VOLUMES=true|false Preserve Docker volumes (default: same as PRESERVE_DATA)"
    echo "  SHUTDOWN_TIMEOUT=seconds    Timeout for graceful shutdown (default: 30)"
    echo "  INTERACTIVE=true|false      Enable interactive prompts (default: true)"
    echo ""
    echo "Examples:"
    echo "  $0                          # Standard shutdown with data preservation"
    echo "  $0 --force                  # Force stop all services"
    echo "  $0 --no-preserve            # Clean shutdown without data preservation"
    echo "  CLEANUP_IMAGES=true $0      # Shutdown and remove Docker images"
    echo ""
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -f|--force)
            FORCE_STOP=true
            shift
            ;;
        -p|--preserve)
            PRESERVE_DATA=true
            shift
            ;;
        -n|--no-preserve)
            PRESERVE_DATA=false
            shift
            ;;
        -c|--cleanup-images)
            CLEANUP_IMAGES=true
            shift
            ;;
        -t|--timeout)
            SHUTDOWN_TIMEOUT="$2"
            shift 2
            ;;
        *)
            log_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Script execution
if [ "${BASH_SOURCE[0]}" == "${0}" ]; then
    main "$@"
fi