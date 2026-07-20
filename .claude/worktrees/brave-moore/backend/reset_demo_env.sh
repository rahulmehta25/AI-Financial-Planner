#!/bin/bash

# Financial Planning System - Demo Environment Reset Script
# ========================================================
#
# This script completely resets the demo environment to a clean state.
# Use this when you need to start fresh or when the demo is in a broken state.
#
# Usage:
#   ./reset_demo_env.sh                     # Interactive reset with confirmations
#   ./reset_demo_env.sh --force             # Force reset without confirmations
#   ./reset_demo_env.sh --keep-data         # Reset but preserve user data
#   ./reset_demo_env.sh --docker-only       # Only reset Docker components
#   ./reset_demo_env.sh --files-only        # Only reset files and directories

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# Configuration
BACKUP_DIR="backups/reset_$(date +%Y%m%d_%H%M%S)"
TEMP_DIRS=(logs exports tmp uploads __pycache__ .pytest_cache)
LOG_FILES=(*.log data_pipeline.log simulation_engine.log)
DATA_FILES=(demo_data/financial_data.db working_demo_results.json test_results.json)
DOCKER_SERVICES=(postgres redis api celery nginx grafana prometheus)

# Options
FORCE_RESET=false
KEEP_DATA=false
DOCKER_ONLY=false
FILES_ONLY=false
CREATE_BACKUP=true
VERBOSE=false

# Track operations
OPERATIONS_COMPLETED=0
OPERATIONS_TOTAL=0

# Helper functions
log_info() {
    echo -e "${CYAN}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_debug() {
    if [ "$VERBOSE" = true ]; then
        echo -e "${PURPLE}[DEBUG]${NC} $1"
    fi
}

log_step() {
    OPERATIONS_COMPLETED=$((OPERATIONS_COMPLETED + 1))
    echo -e "${BLUE}[STEP $OPERATIONS_COMPLETED/$OPERATIONS_TOTAL]${NC} $1"
}

confirm_action() {
    if [ "$FORCE_RESET" = true ]; then
        return 0
    fi
    
    local message="$1"
    local default="${2:-n}"
    
    while true; do
        if [ "$default" = "y" ]; then
            read -p "$(echo -e "${YELLOW}$message [Y/n]: ${NC}")" -r response
            response=${response:-y}
        else
            read -p "$(echo -e "${YELLOW}$message [y/N]: ${NC}")" -r response
            response=${response:-n}
        fi
        
        case $response in
            [Yy]|[Yy][Ee][Ss])
                return 0
                ;;
            [Nn]|[Nn][Oo])
                return 1
                ;;
            *)
                echo -e "${RED}Please answer yes or no.${NC}"
                ;;
        esac
    done
}

print_header() {
    echo -e "${BOLD}${RED}"
    echo "================================================================"
    echo "  FINANCIAL PLANNING SYSTEM - DEMO ENVIRONMENT RESET"
    echo "================================================================"
    echo -e "${NC}"
    echo -e "${YELLOW}This script will reset the demo environment to a clean state.${NC}"
    echo -e "${YELLOW}This action will remove containers, volumes, logs, and data.${NC}"
    echo ""
}

print_summary() {
    echo ""
    echo -e "${BOLD}${CYAN}RESET SUMMARY${NC}"
    echo "================================================================"
    echo -e "Operations completed: ${GREEN}$OPERATIONS_COMPLETED/$OPERATIONS_TOTAL${NC}"
    
    if [ $OPERATIONS_COMPLETED -eq $OPERATIONS_TOTAL ]; then
        echo -e "\n${GREEN}✓ Demo environment has been successfully reset!${NC}"
        echo -e "${GREEN}  You can now run: ./start_demo.sh${NC}"
    else
        echo -e "\n${YELLOW}⚠ Reset completed with some operations skipped${NC}"
    fi
    
    if [ "$CREATE_BACKUP" = true ] && [ -d "$BACKUP_DIR" ]; then
        echo -e "\n${CYAN}Backup created at: $BACKUP_DIR${NC}"
        echo -e "${CYAN}You can restore data from this backup if needed${NC}"
    fi
    
    echo "================================================================"
}

create_backup() {
    if [ "$CREATE_BACKUP" = false ]; then
        return 0
    fi
    
    log_step "Creating backup before reset..."
    
    # Create backup directory
    mkdir -p "$BACKUP_DIR"
    
    # Backup important files
    local backup_items=(
        ".env"
        "demo_data/"
        "exports/"
        "logs/"
        "working_demo_results.json"
        "test_results.json"
    )
    
    local backed_up=0
    for item in "${backup_items[@]}"; do
        if [ -e "$item" ]; then
            cp -r "$item" "$BACKUP_DIR/" 2>/dev/null && backed_up=$((backed_up + 1))
            log_debug "Backed up: $item"
        fi
    done
    
    # Backup Docker volumes if possible
    if command -v docker &> /dev/null && docker info &> /dev/null; then
        log_debug "Backing up Docker volumes..."
        docker volume ls -q | grep financial-planning 2>/dev/null | while read volume; do
            if [ -n "$volume" ]; then
                docker run --rm -v "$volume":/data -v "$(pwd)/$BACKUP_DIR":/backup alpine tar czf "/backup/${volume}.tar.gz" -C /data . 2>/dev/null || true
                log_debug "Backed up volume: $volume"
            fi
        done
    fi
    
    log_success "Backup created with $backed_up items at: $BACKUP_DIR"
}

stop_all_processes() {
    log_step "Stopping all running processes..."
    
    # Stop Python processes
    local python_processes=$(pgrep -f "python.*demo" 2>/dev/null || true)
    if [ -n "$python_processes" ]; then
        log_info "Stopping Python demo processes..."
        echo "$python_processes" | xargs kill -TERM 2>/dev/null || true
        sleep 3
        echo "$python_processes" | xargs kill -KILL 2>/dev/null || true
        log_success "Python processes stopped"
    else
        log_debug "No Python demo processes running"
    fi
    
    # Stop processes on required ports
    local required_ports=(8000 3000 5432 6379 9090 5050)
    for port in "${required_ports[@]}"; do
        local pids=$(lsof -ti:$port 2>/dev/null || true)
        if [ -n "$pids" ]; then
            log_info "Stopping processes on port $port..."
            echo "$pids" | xargs kill -TERM 2>/dev/null || true
            sleep 2
            echo "$pids" | xargs kill -KILL 2>/dev/null || true
            log_debug "Stopped processes on port $port"
        fi
    done
    
    log_success "All processes stopped"
}

reset_docker_environment() {
    if [ "$FILES_ONLY" = true ]; then
        log_debug "Skipping Docker reset (files-only mode)"
        return 0
    fi
    
    log_step "Resetting Docker environment..."
    
    # Check if Docker is available
    if ! command -v docker &> /dev/null; then
        log_warning "Docker not found, skipping Docker reset"
        return 0
    fi
    
    if ! docker info &> /dev/null; then
        log_warning "Docker not running, skipping Docker reset"
        return 0
    fi
    
    # Stop and remove all containers
    if [ -f "docker-compose.yml" ]; then
        log_info "Stopping Docker Compose services..."
        
        # First try graceful shutdown
        if docker-compose ps -q | grep -q .; then
            docker-compose stop --timeout 30 2>/dev/null || true
            log_debug "Graceful shutdown completed"
        fi
        
        # Remove containers and volumes
        docker-compose down -v --remove-orphans 2>/dev/null || true
        log_success "Docker Compose services stopped and removed"
    else
        log_warning "No docker-compose.yml found"
    fi
    
    # Remove any remaining containers from this project
    local project_containers=$(docker ps -aq --filter "label=com.docker.compose.project=financial-planning" 2>/dev/null || true)
    if [ -n "$project_containers" ]; then
        log_info "Removing remaining project containers..."
        echo "$project_containers" | xargs docker rm -f 2>/dev/null || true
        log_debug "Project containers removed"
    fi
    
    # Remove project-specific volumes
    local project_volumes=$(docker volume ls -q --filter "name=financial-planning" 2>/dev/null || true)
    if [ -n "$project_volumes" ]; then
        log_info "Removing project volumes..."
        echo "$project_volumes" | xargs docker volume rm -f 2>/dev/null || true
        log_debug "Project volumes removed"
    fi
    
    # Remove project-specific networks
    local project_networks=$(docker network ls -q --filter "name=financial-planning" 2>/dev/null || true)
    if [ -n "$project_networks" ]; then
        log_info "Removing project networks..."
        echo "$project_networks" | xargs docker network rm 2>/dev/null || true
        log_debug "Project networks removed"
    fi
    
    # Clean up Docker system
    log_info "Cleaning up Docker system..."
    docker system prune -f --volumes 2>/dev/null || true
    
    # Remove any dangling images
    local dangling_images=$(docker images -q -f "dangling=true" 2>/dev/null || true)
    if [ -n "$dangling_images" ]; then
        echo "$dangling_images" | xargs docker rmi -f 2>/dev/null || true
        log_debug "Dangling images removed"
    fi
    
    log_success "Docker environment reset completed"
}

clean_temporary_files() {
    if [ "$DOCKER_ONLY" = true ]; then
        log_debug "Skipping file cleanup (docker-only mode)"
        return 0
    fi
    
    log_step "Cleaning temporary files and directories..."
    
    # Clean temporary directories
    for dir in "${TEMP_DIRS[@]}"; do
        if [ -d "$dir" ]; then
            log_info "Removing directory: $dir"
            rm -rf "$dir"
            log_debug "Removed: $dir"
        fi
    done
    
    # Clean log files
    for pattern in "${LOG_FILES[@]}"; do
        for file in $pattern; do
            if [ -f "$file" ] && [ "$file" != "$pattern" ]; then
                log_info "Removing log file: $file"
                rm -f "$file"
                log_debug "Removed: $file"
            fi
        done
    done
    
    # Clean Python cache files
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete 2>/dev/null || true
    find . -type f -name "*.pyo" -delete 2>/dev/null || true
    find . -type f -name "*.pyd" -delete 2>/dev/null || true
    find . -type f -name ".coverage" -delete 2>/dev/null || true
    
    # Clean test and build artifacts
    rm -rf .pytest_cache/ htmlcov/ .coverage dist/ build/ *.egg-info/ 2>/dev/null || true
    
    log_success "Temporary files cleaned"
}

reset_data_files() {
    if [ "$DOCKER_ONLY" = true ] || [ "$KEEP_DATA" = true ]; then
        log_debug "Skipping data file reset"
        return 0
    fi
    
    log_step "Resetting data files..."
    
    # Remove data files
    for file in "${DATA_FILES[@]}"; do
        if [ -f "$file" ]; then
            log_info "Removing data file: $file"
            rm -f "$file"
            log_debug "Removed: $file"
        fi
    done
    
    # Clean exports directory but keep structure
    if [ -d "exports" ]; then
        log_info "Cleaning exports directory..."
        rm -rf exports/*
        mkdir -p exports/{pdf,csv,excel}
        log_debug "Exports directory cleaned and restructured"
    fi
    
    # Reset database data directory
    if [ -d "demo_data" ]; then
        log_info "Resetting demo_data directory..."
        rm -rf demo_data/*
        log_debug "Demo data directory cleaned"
    fi
    
    log_success "Data files reset completed"
}

recreate_directory_structure() {
    if [ "$DOCKER_ONLY" = true ]; then
        log_debug "Skipping directory recreation (docker-only mode)"
        return 0
    fi
    
    log_step "Recreating directory structure..."
    
    # Create required directories
    local required_dirs=(
        "logs"
        "logs/api"
        "logs/celery"
        "logs/nginx"
        "exports"
        "exports/pdf"
        "exports/csv"
        "exports/excel"
        "tmp"
        "tmp/uploads"
        "demo_data"
        "uploads"
    )
    
    for dir in "${required_dirs[@]}"; do
        mkdir -p "$dir"
        log_debug "Created directory: $dir"
    done
    
    # Create placeholder files to preserve directory structure in git
    for dir in "${required_dirs[@]}"; do
        if [ ! -f "$dir/.gitkeep" ]; then
            touch "$dir/.gitkeep"
        fi
    done
    
    log_success "Directory structure recreated"
}

reset_environment_config() {
    if [ "$DOCKER_ONLY" = true ]; then
        log_debug "Skipping environment config reset (docker-only mode)"
        return 0
    fi
    
    log_step "Resetting environment configuration..."
    
    # Handle .env file
    if [ -f ".env" ]; then
        if confirm_action "Reset .env file to defaults?"; then
            if [ -f "env.template" ]; then
                log_info "Resetting .env from template..."
                cp env.template .env
                
                # Generate new secret key
                if command -v openssl &> /dev/null; then
                    local secret_key=$(openssl rand -base64 32)
                    sed -i.bak "s/your-secret-key-here-change-in-production/$secret_key/" .env
                    rm -f .env.bak
                    log_success ".env reset with new secret key"
                else
                    log_success ".env reset from template"
                fi
            else
                log_warning "No env.template found, keeping existing .env"
            fi
        else
            log_info "Keeping existing .env file"
        fi
    elif [ -f "env.template" ]; then
        log_info "Creating .env from template..."
        cp env.template .env
        
        if command -v openssl &> /dev/null; then
            local secret_key=$(openssl rand -base64 32)
            sed -i.bak "s/your-secret-key-here-change-in-production/$secret_key/" .env
            rm -f .env.bak
        fi
        
        log_success ".env created from template"
    fi
    
    log_success "Environment configuration reset completed"
}

verify_reset() {
    log_step "Verifying reset completion..."
    
    local issues_found=0
    
    # Check that Docker containers are gone
    if command -v docker &> /dev/null && docker info &> /dev/null; then
        local remaining_containers=$(docker ps -aq --filter "label=com.docker.compose.project=financial-planning" 2>/dev/null | wc -l)
        if [ "$remaining_containers" -gt 0 ]; then
            log_warning "$remaining_containers containers still exist"
            issues_found=$((issues_found + 1))
        else
            log_success "No project containers remain"
        fi
        
        local remaining_volumes=$(docker volume ls -q --filter "name=financial-planning" 2>/dev/null | wc -l)
        if [ "$remaining_volumes" -gt 0 ]; then
            log_warning "$remaining_volumes volumes still exist"
            issues_found=$((issues_found + 1))
        else
            log_success "No project volumes remain"
        fi
    fi
    
    # Check that processes are stopped
    local running_processes=$(pgrep -f "python.*demo" 2>/dev/null | wc -l)
    if [ "$running_processes" -gt 0 ]; then
        log_warning "$running_processes demo processes still running"
        issues_found=$((issues_found + 1))
    else
        log_success "No demo processes running"
    fi
    
    # Check that required directories exist
    local missing_dirs=0
    for dir in logs exports tmp demo_data; do
        if [ ! -d "$dir" ]; then
            missing_dirs=$((missing_dirs + 1))
        fi
    done
    
    if [ $missing_dirs -gt 0 ]; then
        log_warning "$missing_dirs required directories are missing"
        issues_found=$((issues_found + 1))
    else
        log_success "All required directories exist"
    fi
    
    # Check ports are free
    local ports_in_use=0
    for port in 8000 5432 6379; do
        if lsof -Pi :$port -sTCP:LISTEN -t &>/dev/null; then
            ports_in_use=$((ports_in_use + 1))
        fi
    done
    
    if [ $ports_in_use -gt 0 ]; then
        log_warning "$ports_in_use required ports are still in use"
        issues_found=$((issues_found + 1))
    else
        log_success "All required ports are available"
    fi
    
    if [ $issues_found -eq 0 ]; then
        log_success "Reset verification passed - environment is clean"
        return 0
    else
        log_warning "Reset verification found $issues_found issues"
        return 1
    fi
}

show_next_steps() {
    echo ""
    echo -e "${BOLD}${CYAN}NEXT STEPS${NC}"
    echo "================================================================"
    echo -e "${GREEN}1. Start the demo:${NC}"
    echo "   ./start_demo.sh"
    echo ""
    echo -e "${GREEN}2. Or run system diagnostics:${NC}"
    echo "   python3 check_system.py"
    echo ""
    echo -e "${GREEN}3. Or run minimal demo:${NC}"
    echo "   python3 minimal_working_demo.py"
    echo ""
    
    if [ -d "$BACKUP_DIR" ]; then
        echo -e "${YELLOW}To restore from backup:${NC}"
        echo "   cp -r $BACKUP_DIR/* ."
        echo ""
    fi
    
    echo -e "${CYAN}For help and troubleshooting:${NC}"
    echo "   cat TROUBLESHOOTING.md"
    echo "   python3 check_system.py --help"
    echo "================================================================"
}

main() {
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --force|-f)
                FORCE_RESET=true
                shift
                ;;
            --keep-data)
                KEEP_DATA=true
                shift
                ;;
            --docker-only)
                DOCKER_ONLY=true
                shift
                ;;
            --files-only)
                FILES_ONLY=true
                shift
                ;;
            --no-backup)
                CREATE_BACKUP=false
                shift
                ;;
            --verbose|-v)
                VERBOSE=true
                shift
                ;;
            --help|-h)
                echo "Usage: $0 [OPTIONS]"
                echo ""
                echo "Reset the Financial Planning System demo environment to a clean state."
                echo ""
                echo "Options:"
                echo "  --force, -f         Force reset without confirmations"
                echo "  --keep-data         Reset but preserve user data files"
                echo "  --docker-only       Only reset Docker containers and volumes"
                echo "  --files-only        Only reset files and directories"
                echo "  --no-backup         Skip creating backup before reset"
                echo "  --verbose, -v       Enable verbose output"
                echo "  --help, -h          Show this help message"
                echo ""
                echo "Examples:"
                echo "  $0                  # Interactive reset with backup"
                echo "  $0 --force          # Force reset without prompts"
                echo "  $0 --keep-data      # Reset but keep data files"
                echo "  $0 --docker-only    # Only reset Docker components"
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                echo "Use --help for usage information"
                exit 1
                ;;
        esac
    done
    
    # Calculate total operations
    OPERATIONS_TOTAL=7
    if [ "$DOCKER_ONLY" = true ]; then
        OPERATIONS_TOTAL=3
    elif [ "$FILES_ONLY" = true ]; then
        OPERATIONS_TOTAL=5
    fi
    
    print_header
    
    # Final confirmation
    if [ "$FORCE_RESET" = false ]; then
        echo -e "${RED}WARNING: This will completely reset your demo environment!${NC}"
        echo ""
        echo "This will:"
        echo "  • Stop all running processes"
        echo "  • Remove Docker containers and volumes"
        echo "  • Delete log files and temporary data"
        if [ "$KEEP_DATA" = false ]; then
            echo "  • Remove database and user data"
        fi
        echo "  • Reset configuration files"
        echo ""
        
        if [ "$CREATE_BACKUP" = true ]; then
            echo -e "${CYAN}A backup will be created before reset.${NC}"
            echo ""
        fi
        
        if ! confirm_action "Are you sure you want to proceed with the reset?"; then
            log_info "Reset cancelled by user"
            exit 0
        fi
        
        echo ""
    fi
    
    # Execute reset operations
    if [ "$CREATE_BACKUP" = true ]; then
        create_backup
    fi
    
    stop_all_processes
    
    if [ "$FILES_ONLY" = false ]; then
        reset_docker_environment
    fi
    
    if [ "$DOCKER_ONLY" = false ]; then
        clean_temporary_files
        reset_data_files
        recreate_directory_structure
        reset_environment_config
    fi
    
    verify_reset
    
    print_summary
    show_next_steps
    
    log_success "Demo environment reset completed successfully!"
}

# Ensure we're in the right directory
if [ ! -f "working_demo.py" ] && [ ! -f "minimal_working_demo.py" ]; then
    log_error "This script must be run from the backend directory"
    log_info "Current directory: $(pwd)"
    log_info "Expected files: working_demo.py, minimal_working_demo.py"
    exit 1
fi

# Run main function
main "$@"