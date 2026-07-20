#!/bin/bash

# Financial Planning System - Common Issues Auto-Fix Script
# ========================================================
# 
# This script automatically fixes common issues that prevent
# the demo from running properly.
#
# Usage:
#   ./fix_common_issues.sh                      # Fix all common issues
#   ./fix_common_issues.sh --kill-ports        # Kill processes on required ports
#   ./fix_common_issues.sh --install-deps      # Install missing dependencies
#   ./fix_common_issues.sh --reset-docker      # Reset Docker containers
#   ./fix_common_issues.sh --fix-permissions   # Fix file permissions
#   ./fix_common_issues.sh --check-only        # Check issues without fixing

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Configuration
REQUIRED_PORTS=(8000 3000 5432 6379 9090 5050 8081)
REQUIRED_DIRS=(logs exports tmp uploads)
PYTHON_CMD="python3"
PIP_CMD="pip3"

# Track fixes
FIXES_APPLIED=0
ISSUES_FOUND=0

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

print_header() {
    echo -e "${BOLD}${BLUE}"
    echo "================================================================"
    echo "  FINANCIAL PLANNING SYSTEM - AUTO-FIX SCRIPT"
    echo "================================================================"
    echo -e "${NC}"
}

print_summary() {
    echo ""
    echo -e "${BOLD}${CYAN}SUMMARY${NC}"
    echo "================================================================"
    echo -e "Issues found: ${RED}$ISSUES_FOUND${NC}"
    echo -e "Fixes applied: ${GREEN}$FIXES_APPLIED${NC}"
    
    if [ $ISSUES_FOUND -eq 0 ]; then
        echo -e "\n${GREEN}✓ No issues detected - system appears ready!${NC}"
        echo -e "${GREEN}  Run: python3 working_demo.py${NC}"
    elif [ $FIXES_APPLIED -gt 0 ]; then
        echo -e "\n${YELLOW}⚠ Issues were found and fixes were applied${NC}"
        echo -e "${YELLOW}  Please run the diagnostic again: python3 check_system.py${NC}"
    else
        echo -e "\n${RED}✗ Issues were found but no fixes were applied${NC}"
        echo -e "${RED}  Run with appropriate flags to apply fixes${NC}"
    fi
    echo "================================================================"
}

# Check system requirements
check_system_requirements() {
    log_info "Checking system requirements..."
    
    # Check operating system
    case "$(uname -s)" in
        Darwin*)
            OS="macOS"
            PACKAGE_MANAGER="brew"
            ;;
        Linux*)
            OS="Linux"
            if command -v apt-get &> /dev/null; then
                PACKAGE_MANAGER="apt"
            elif command -v yum &> /dev/null; then
                PACKAGE_MANAGER="yum"
            elif command -v dnf &> /dev/null; then
                PACKAGE_MANAGER="dnf"
            fi
            ;;
        CYGWIN*|MINGW32*|MSYS*|MINGW*)
            OS="Windows"
            PACKAGE_MANAGER="choco"
            ;;
        *)
            log_error "Unsupported operating system: $(uname -s)"
            exit 1
            ;;
    esac
    
    log_success "Operating System: $OS"
    
    # Check Python
    if ! command -v $PYTHON_CMD &> /dev/null; then
        log_error "Python 3 is required but not found"
        ISSUES_FOUND=$((ISSUES_FOUND + 1))
        
        if [ "$AUTO_INSTALL" = true ]; then
            log_info "Attempting to install Python 3..."
            case $PACKAGE_MANAGER in
                "brew")
                    brew install python3
                    ;;
                "apt")
                    sudo apt-get update && sudo apt-get install -y python3 python3-pip
                    ;;
                "yum"|"dnf")
                    sudo $PACKAGE_MANAGER install -y python3 python3-pip
                    ;;
                *)
                    log_error "Cannot auto-install Python on this system"
                    return 1
                    ;;
            esac
            FIXES_APPLIED=$((FIXES_APPLIED + 1))
        fi
    else
        python_version=$($PYTHON_CMD --version 2>&1 | cut -d' ' -f2)
        log_success "Python version: $python_version"
    fi
    
    # Check pip
    if ! command -v $PIP_CMD &> /dev/null; then
        log_warning "pip3 not found, trying pip"
        if command -v pip &> /dev/null; then
            PIP_CMD="pip"
        else
            log_error "pip is required but not found"
            ISSUES_FOUND=$((ISSUES_FOUND + 1))
        fi
    fi
}

# Kill processes on required ports
kill_port_conflicts() {
    log_info "Checking for port conflicts..."
    
    local ports_killed=0
    
    for port in "${REQUIRED_PORTS[@]}"; do
        # Check if port is in use
        if lsof -Pi :$port -sTCP:LISTEN -t &>/dev/null; then
            log_warning "Port $port is in use"
            ISSUES_FOUND=$((ISSUES_FOUND + 1))
            
            if [ "$KILL_PORTS" = true ]; then
                log_info "Killing processes on port $port..."
                
                # Get processes using the port
                local pids=$(lsof -ti:$port)
                
                if [ -n "$pids" ]; then
                    echo "$pids" | while read pid; do
                        if [ -n "$pid" ]; then
                            # Get process name for logging
                            local process_name=$(ps -p $pid -o comm= 2>/dev/null || echo "unknown")
                            log_debug "Killing process $process_name (PID: $pid)"
                            
                            # Try graceful termination first
                            kill $pid 2>/dev/null || true
                            sleep 2
                            
                            # Force kill if still running
                            if kill -0 $pid 2>/dev/null; then
                                kill -9 $pid 2>/dev/null || true
                                log_debug "Force killed process $pid"
                            fi
                        fi
                    done
                    
                    ports_killed=$((ports_killed + 1))
                    FIXES_APPLIED=$((FIXES_APPLIED + 1))
                    log_success "Killed processes on port $port"
                else
                    log_warning "Could not identify processes on port $port"
                fi
            fi
        else
            log_success "Port $port is available"
        fi
    done
    
    if [ $ports_killed -gt 0 ]; then
        log_info "Waiting 3 seconds for ports to be released..."
        sleep 3
    fi
}

# Install missing Python dependencies
install_python_dependencies() {
    log_info "Checking Python dependencies..."
    
    # Core requirements
    local core_packages=(
        "fastapi>=0.68.0"
        "uvicorn[standard]>=0.15.0"
        "numpy>=1.21.0"
        "pydantic>=1.8.0"
        "sqlalchemy>=1.4.0"
        "psycopg2-binary>=2.9.0"
        "python-jose[cryptography]>=3.3.0"
        "passlib[bcrypt]>=1.7.4"
        "python-multipart>=0.0.5"
        "psutil>=5.8.0"
    )
    
    # Optional packages for enhanced features
    local optional_packages=(
        "scipy>=1.7.0"
        "matplotlib>=3.4.0"
        "numba>=0.54.0"
        "reportlab>=3.6.0"
        "redis>=3.5.0"
        "celery>=5.2.0"
    )
    
    local missing_core=()
    local missing_optional=()
    
    # Check core packages
    for package in "${core_packages[@]}"; do
        local package_name=$(echo $package | cut -d'>' -f1 | cut -d'=' -f1)
        if ! $PYTHON_CMD -c "import $package_name" &>/dev/null; then
            missing_core+=("$package")
            log_warning "Missing core package: $package_name"
            ISSUES_FOUND=$((ISSUES_FOUND + 1))
        else
            log_success "Found core package: $package_name"
        fi
    done
    
    # Check optional packages
    for package in "${optional_packages[@]}"; do
        local package_name=$(echo $package | cut -d'>' -f1 | cut -d'=' -f1)
        if ! $PYTHON_CMD -c "import $package_name" &>/dev/null; then
            missing_optional+=("$package")
            log_debug "Missing optional package: $package_name"
        else
            log_success "Found optional package: $package_name"
        fi
    done
    
    # Install missing core packages
    if [ ${#missing_core[@]} -gt 0 ] && [ "$INSTALL_DEPS" = true ]; then
        log_info "Installing missing core packages..."
        
        # Update pip first
        $PIP_CMD install --upgrade pip
        
        for package in "${missing_core[@]}"; do
            log_info "Installing $package..."
            if $PIP_CMD install "$package"; then
                log_success "Successfully installed $package"
                FIXES_APPLIED=$((FIXES_APPLIED + 1))
            else
                log_error "Failed to install $package"
            fi
        done
    fi
    
    # Optionally install missing optional packages
    if [ ${#missing_optional[@]} -gt 0 ] && [ "$INSTALL_OPTIONAL" = true ]; then
        log_info "Installing optional packages for enhanced features..."
        
        for package in "${missing_optional[@]}"; do
            log_info "Installing optional package $package..."
            if $PIP_CMD install "$package"; then
                log_success "Successfully installed $package"
                FIXES_APPLIED=$((FIXES_APPLIED + 1))
            else
                log_warning "Could not install optional package $package"
            fi
        done
    fi
    
    # Install from requirements.txt if available
    if [ -f "requirements.txt" ] && [ "$INSTALL_DEPS" = true ]; then
        log_info "Installing from requirements.txt..."
        if $PIP_CMD install -r requirements.txt; then
            log_success "Successfully installed requirements.txt"
            FIXES_APPLIED=$((FIXES_APPLIED + 1))
        else
            log_error "Failed to install from requirements.txt"
        fi
    fi
}

# Create required directories
create_required_directories() {
    log_info "Checking required directories..."
    
    for dir in "${REQUIRED_DIRS[@]}"; do
        if [ ! -d "$dir" ]; then
            log_warning "Missing directory: $dir"
            ISSUES_FOUND=$((ISSUES_FOUND + 1))
            
            if [ "$FIX_PERMISSIONS" = true ]; then
                log_info "Creating directory: $dir"
                if mkdir -p "$dir"; then
                    log_success "Created directory: $dir"
                    FIXES_APPLIED=$((FIXES_APPLIED + 1))
                else
                    log_error "Failed to create directory: $dir"
                fi
            fi
        else
            log_success "Directory exists: $dir"
        fi
    done
    
    # Create subdirectories
    if [ "$FIX_PERMISSIONS" = true ]; then
        mkdir -p exports/{pdf,csv,excel} 2>/dev/null || true
        mkdir -p logs/{api,celery,nginx} 2>/dev/null || true
        mkdir -p tmp/uploads 2>/dev/null || true
    fi
}

# Fix file permissions
fix_file_permissions() {
    log_info "Checking file permissions..."
    
    local permission_fixes=0
    
    # Check and fix directory permissions
    for dir in . app scripts "${REQUIRED_DIRS[@]}"; do
        if [ -d "$dir" ]; then
            # Test write permissions
            local test_file="$dir/.permission_test_$$"
            if ! touch "$test_file" 2>/dev/null; then
                log_warning "No write permission for directory: $dir"
                ISSUES_FOUND=$((ISSUES_FOUND + 1))
                
                if [ "$FIX_PERMISSIONS" = true ]; then
                    log_info "Fixing permissions for directory: $dir"
                    if chmod 755 "$dir" 2>/dev/null; then
                        log_success "Fixed permissions for: $dir"
                        permission_fixes=$((permission_fixes + 1))
                        FIXES_APPLIED=$((FIXES_APPLIED + 1))
                    else
                        log_error "Could not fix permissions for: $dir"
                    fi
                fi
            else
                rm -f "$test_file" 2>/dev/null || true
                log_success "Write permission OK for: $dir"
            fi
        fi
    done
    
    # Make scripts executable
    if [ "$FIX_PERMISSIONS" = true ]; then
        for script in *.sh scripts/*.sh scripts/*/*.sh; do
            if [ -f "$script" ]; then
                chmod +x "$script" 2>/dev/null || true
                log_debug "Made executable: $script"
            fi
        done
        
        if [ $permission_fixes -gt 0 ]; then
            log_success "Fixed permissions for $permission_fixes items"
        fi
    fi
}

# Setup environment configuration
setup_environment_config() {
    log_info "Checking environment configuration..."
    
    # Check for .env file
    if [ ! -f ".env" ]; then
        log_warning "Missing .env configuration file"
        ISSUES_FOUND=$((ISSUES_FOUND + 1))
        
        if [ "$FIX_CONFIG" = true ]; then
            if [ -f "env.template" ]; then
                log_info "Creating .env from template..."
                cp env.template .env
                
                # Generate secure secret key if available
                if command -v openssl &> /dev/null; then
                    local secret_key=$(openssl rand -base64 32)
                    sed -i.bak "s/your-secret-key-here-change-in-production/$secret_key/" .env
                    rm -f .env.bak
                    log_success "Created .env with generated secret key"
                else
                    log_success "Created .env from template (please set SECRET_KEY)"
                fi
                
                FIXES_APPLIED=$((FIXES_APPLIED + 1))
            else
                log_error "No env.template file found to create .env"
            fi
        fi
    else
        log_success "Environment file .env exists"
        
        # Check for important environment variables
        local missing_vars=()
        local required_vars=("SECRET_KEY" "DATABASE_URL")
        
        for var in "${required_vars[@]}"; do
            if ! grep -q "^${var}=" .env; then
                missing_vars+=("$var")
            fi
        done
        
        if [ ${#missing_vars[@]} -gt 0 ]; then
            log_warning "Missing environment variables: ${missing_vars[*]}"
            ISSUES_FOUND=$((ISSUES_FOUND + 1))
        fi
    fi
}

# Reset Docker containers and volumes
reset_docker_containers() {
    log_info "Checking Docker setup..."
    
    # Check if Docker is available
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        ISSUES_FOUND=$((ISSUES_FOUND + 1))
        return 1
    fi
    
    # Check if Docker is running
    if ! docker info &> /dev/null; then
        log_error "Docker is not running"
        ISSUES_FOUND=$((ISSUES_FOUND + 1))
        return 1
    fi
    
    if [ "$RESET_DOCKER" = true ]; then
        log_info "Resetting Docker containers..."
        
        # Stop and remove containers
        if [ -f "docker-compose.yml" ]; then
            log_info "Stopping Docker Compose services..."
            docker-compose down -v --remove-orphans 2>/dev/null || true
            
            log_info "Pruning Docker system..."
            docker system prune -f
            
            log_success "Docker containers reset"
            FIXES_APPLIED=$((FIXES_APPLIED + 1))
        else
            log_warning "No docker-compose.yml found"
        fi
    fi
    
    # Check for Docker Compose
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose is not available"
        ISSUES_FOUND=$((ISSUES_FOUND + 1))
    else
        log_success "Docker Compose is available"
    fi
}

# Database connectivity check and fix
check_database_setup() {
    log_info "Checking database setup..."
    
    # Check for database files
    local db_files=("demo_data/financial_data.db")
    
    for db_file in "${db_files[@]}"; do
        if [ ! -f "$db_file" ]; then
            log_warning "Missing database file: $db_file"
            ISSUES_FOUND=$((ISSUES_FOUND + 1))
            
            if [ "$FIX_DATABASE" = true ]; then
                # Create database directory if it doesn't exist
                local db_dir=$(dirname "$db_file")
                mkdir -p "$db_dir"
                
                # Try to initialize database
                log_info "Attempting to initialize database..."
                if $PYTHON_CMD -c "from app.database.init_db import init_database; init_database()" 2>/dev/null; then
                    log_success "Database initialized successfully"
                    FIXES_APPLIED=$((FIXES_APPLIED + 1))
                else
                    log_warning "Could not initialize database automatically"
                fi
            fi
        else
            log_success "Database file exists: $db_file"
        fi
    done
}

# Verify system after fixes
verify_system() {
    log_info "Verifying system after fixes..."
    
    local verification_passed=true
    
    # Test Python imports
    if ! $PYTHON_CMD -c "import fastapi, uvicorn, numpy, pydantic" &>/dev/null; then
        log_error "Core Python packages still missing after fixes"
        verification_passed=false
    else
        log_success "Core Python packages are available"
    fi
    
    # Test port availability
    local ports_in_use=0
    for port in 8000 5432 6379; do  # Key ports only
        if lsof -Pi :$port -sTCP:LISTEN -t &>/dev/null; then
            ports_in_use=$((ports_in_use + 1))
        fi
    done
    
    if [ $ports_in_use -eq 0 ]; then
        log_success "Key ports are available"
    else
        log_warning "$ports_in_use key ports are still in use"
    fi
    
    # Test directory permissions
    if [ -w "." ] && [ -w "logs" ] && [ -w "exports" ]; then
        log_success "Directory permissions are correct"
    else
        log_warning "Some directory permission issues remain"
        verification_passed=false
    fi
    
    if [ "$verification_passed" = true ]; then
        log_success "System verification passed - ready to run demo"
        return 0
    else
        log_warning "System verification found remaining issues"
        return 1
    fi
}

# Main execution
main() {
    print_header
    
    # Parse command line arguments
    KILL_PORTS=false
    INSTALL_DEPS=false
    INSTALL_OPTIONAL=false
    RESET_DOCKER=false
    FIX_PERMISSIONS=false
    FIX_CONFIG=false
    FIX_DATABASE=false
    AUTO_INSTALL=false
    CHECK_ONLY=false
    VERBOSE=false
    
    # If no specific flags, enable all fixes
    if [ $# -eq 0 ]; then
        KILL_PORTS=true
        INSTALL_DEPS=true
        FIX_PERMISSIONS=true
        FIX_CONFIG=true
        FIX_DATABASE=true
    fi
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --kill-ports)
                KILL_PORTS=true
                shift
                ;;
            --install-deps)
                INSTALL_DEPS=true
                shift
                ;;
            --install-optional)
                INSTALL_OPTIONAL=true
                shift
                ;;
            --reset-docker)
                RESET_DOCKER=true
                shift
                ;;
            --fix-permissions)
                FIX_PERMISSIONS=true
                shift
                ;;
            --fix-config)
                FIX_CONFIG=true
                shift
                ;;
            --fix-database)
                FIX_DATABASE=true
                shift
                ;;
            --auto-install)
                AUTO_INSTALL=true
                shift
                ;;
            --check-only)
                CHECK_ONLY=true
                shift
                ;;
            --verbose|-v)
                VERBOSE=true
                shift
                ;;
            --all)
                KILL_PORTS=true
                INSTALL_DEPS=true
                INSTALL_OPTIONAL=true
                FIX_PERMISSIONS=true
                FIX_CONFIG=true
                FIX_DATABASE=true
                shift
                ;;
            --help|-h)
                echo "Usage: $0 [OPTIONS]"
                echo ""
                echo "Options:"
                echo "  --kill-ports        Kill processes using required ports"
                echo "  --install-deps      Install missing Python dependencies"
                echo "  --install-optional  Install optional Python packages"
                echo "  --reset-docker      Reset Docker containers and volumes"
                echo "  --fix-permissions   Fix file and directory permissions"
                echo "  --fix-config        Create/fix environment configuration"
                echo "  --fix-database      Initialize database if missing"
                echo "  --auto-install      Attempt to install system packages"
                echo "  --check-only        Check issues without applying fixes"
                echo "  --verbose, -v       Enable verbose output"
                echo "  --all               Enable all fix options"
                echo "  --help, -h          Show this help message"
                echo ""
                echo "If no options are specified, common fixes will be applied."
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                echo "Use --help for usage information"
                exit 1
                ;;
        esac
    done
    
    # If check-only mode, disable all fixes
    if [ "$CHECK_ONLY" = true ]; then
        KILL_PORTS=false
        INSTALL_DEPS=false
        INSTALL_OPTIONAL=false
        RESET_DOCKER=false
        FIX_PERMISSIONS=false
        FIX_CONFIG=false
        FIX_DATABASE=false
        AUTO_INSTALL=false
        log_info "Running in check-only mode - no fixes will be applied"
    fi
    
    # Run checks and fixes
    check_system_requirements
    echo ""
    
    kill_port_conflicts
    echo ""
    
    install_python_dependencies
    echo ""
    
    create_required_directories
    echo ""
    
    fix_file_permissions
    echo ""
    
    setup_environment_config
    echo ""
    
    check_database_setup
    echo ""
    
    reset_docker_containers
    echo ""
    
    # Verify system if fixes were applied
    if [ $FIXES_APPLIED -gt 0 ]; then
        echo ""
        verify_system
    fi
    
    print_summary
    
    # Return appropriate exit code
    if [ $ISSUES_FOUND -eq 0 ]; then
        exit 0
    elif [ $FIXES_APPLIED -gt 0 ]; then
        exit 2  # Issues found and fixes applied
    else
        exit 1  # Issues found but no fixes applied
    fi
}

# Make sure we're in the right directory
if [ ! -f "working_demo.py" ] && [ ! -f "minimal_working_demo.py" ]; then
    log_error "This script must be run from the backend directory"
    log_info "Current directory: $(pwd)"
    log_info "Expected files: working_demo.py, minimal_working_demo.py"
    exit 1
fi

# Run main function
main "$@"