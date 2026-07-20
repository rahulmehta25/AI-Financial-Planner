#!/bin/bash

# Financial Planning Demo Simple Startup Script
# ============================================

echo "🚀 AI Financial Planning Demo Launcher"
echo "======================================"
echo ""

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not found."
    echo "Please install Python 3.8 or higher."
    exit 1
fi

echo "🐍 Python version:"
python3 --version
echo ""

# Check available dependencies
echo "📦 Checking dependencies..."

# Core requirements
python3 -c "import fastapi" 2>/dev/null && echo "   ✅ FastAPI available" || echo "   ⚠️  FastAPI not available - install with: pip3 install fastapi"
python3 -c "import uvicorn" 2>/dev/null && echo "   ✅ Uvicorn available" || echo "   ⚠️  Uvicorn not available - install with: pip3 install uvicorn"
python3 -c "import numpy" 2>/dev/null && echo "   ✅ NumPy available" || echo "   ⚠️  NumPy not available - install with: pip3 install numpy"
python3 -c "import pydantic" 2>/dev/null && echo "   ✅ Pydantic available" || echo "   ⚠️  Pydantic not available - install with: pip3 install pydantic"
python3 -c "import jose" 2>/dev/null && echo "   ✅ Python-JOSE available" || echo "   ⚠️  Python-JOSE not available - install with: pip3 install python-jose[cryptography]"
python3 -c "import passlib" 2>/dev/null && echo "   ✅ Passlib available" || echo "   ⚠️  Passlib not available - install with: pip3 install passlib[bcrypt]"

# Advanced dependencies
python3 -c "import scipy" 2>/dev/null && echo "   ✅ SciPy available (advanced optimization)" || echo "   ⚠️  SciPy not available (will use simplified optimization)"
python3 -c "import matplotlib" 2>/dev/null && echo "   ✅ Matplotlib available (charts)" || echo "   ⚠️  Matplotlib not available (no charts)"
python3 -c "import numba" 2>/dev/null && echo "   ✅ Numba available (JIT acceleration)" || echo "   ⚠️  Numba not available (will use NumPy)"
python3 -c "import reportlab" 2>/dev/null && echo "   ✅ ReportLab available (PDF reports)" || echo "   ⚠️  ReportLab not available (no PDF reports)"

echo ""

# Determine which demo to run
FULL_DEPS_AVAILABLE=true

# Check if full dependencies are available
python3 -c "import scipy, matplotlib, reportlab" 2>/dev/null || FULL_DEPS_AVAILABLE=false

if [ "$FULL_DEPS_AVAILABLE" = true ]; then
    echo "🌟 All dependencies available! Running full-featured demo..."
    DEMO_FILE="working_demo.py"
else
    echo "⚡ Running minimal dependency demo (still fully functional)..."
    DEMO_FILE="minimal_working_demo.py"
fi

echo ""

# Check if basic requirements are met
BASIC_DEPS_AVAILABLE=true
python3 -c "import fastapi, uvicorn, numpy, pydantic, jose, passlib" 2>/dev/null || BASIC_DEPS_AVAILABLE=false

if [ "$BASIC_DEPS_AVAILABLE" = false ]; then
    echo "❌ Missing basic dependencies. Installing them now..."
    echo ""
    echo "🔧 Installing required packages..."
    pip3 install fastapi uvicorn numpy pydantic "python-jose[cryptography]" "passlib[bcrypt]"
    echo ""
    echo "✅ Basic dependencies installed!"
    echo ""
fi

# Check if demo file exists
if [ ! -f "$DEMO_FILE" ]; then
    echo "❌ Demo file $DEMO_FILE not found!"
    exit 1
fi

echo "🚀 Starting demo server..."
echo "📚 Open http://localhost:8000/docs in your browser"
echo ""
echo "👤 Demo login credentials:"
echo "   📧 demo@example.com"
echo "   🔑 demo123"
echo ""
echo "🎯 Quick start:"
echo "   1. Visit http://localhost:8000/sample-data to create demo data"
echo "   2. Login with demo credentials"
echo "   3. Explore the interactive API documentation"
echo ""
echo "Press Ctrl+C to stop the server"
echo "================================="

# Start the appropriate demo
python3 "$DEMO_FILE"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="financial-planning"
BACKEND_PORT=8000
FRONTEND_PORT=3000
API_DOCS_PORT=8000
GRAFANA_PORT=3000
PROMETHEUS_PORT=9091

# Environment detection
DEMO_ENV=${DEMO_ENV:-development}
SKIP_CHECKS=${SKIP_CHECKS:-false}
AUTO_OPEN_BROWSER=${AUTO_OPEN_BROWSER:-true}
COMPOSE_PROFILES=${COMPOSE_PROFILES:-""}

# Logging functions
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Error handling
error_exit() {
    log_error "$1"
    log_error "Demo startup failed. Check the logs above for details."
    log_info "Run './stop_demo.sh' to clean up any partial deployment."
    exit 1
}

# Cleanup on exit
cleanup() {
    if [ $? -ne 0 ]; then
        log_warning "Script interrupted. Running cleanup..."
        ./stop_demo.sh 2>/dev/null || true
    fi
}
trap cleanup EXIT

print_header() {
    echo "================================================================"
    echo "🚀 Financial Planning System - Demo Environment Startup"
    echo "================================================================"
    echo "Environment: $DEMO_ENV"
    echo "Timestamp: $(date)"
    echo "================================================================"
}

check_system_requirements() {
    if [ "$SKIP_CHECKS" = "true" ]; then
        log_warning "Skipping system requirements check"
        return 0
    fi

    log_info "Checking system requirements..."

    # Check OS
    case "$(uname -s)" in
        Darwin)
            OS="macOS"
            PACKAGE_MANAGER="brew"
            ;;
        Linux)
            OS="Linux"
            if command -v apt-get &> /dev/null; then
                PACKAGE_MANAGER="apt"
            elif command -v yum &> /dev/null; then
                PACKAGE_MANAGER="yum"
            elif command -v dnf &> /dev/null; then
                PACKAGE_MANAGER="dnf"
            else
                PACKAGE_MANAGER="unknown"
            fi
            ;;
        CYGWIN*|MINGW32*|MSYS*|MINGW*)
            OS="Windows"
            PACKAGE_MANAGER="choco"
            ;;
        *)
            error_exit "Unsupported operating system: $(uname -s)"
            ;;
    esac

    log_success "Operating System: $OS"

    # Check Docker
    if ! command -v docker &> /dev/null; then
        error_exit "Docker is required but not installed. Please install Docker Desktop."
    fi

    if ! docker info &> /dev/null; then
        error_exit "Docker is not running. Please start Docker Desktop."
    fi

    local docker_version=$(docker --version | cut -d' ' -f3 | cut -d',' -f1)
    log_success "Docker $docker_version detected and running"

    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        error_exit "Docker Compose is required but not installed."
    fi

    # Check available ports
    local required_ports=($BACKEND_PORT $FRONTEND_PORT 5432 6379 $GRAFANA_PORT $PROMETHEUS_PORT 5050 8081)
    for port in "${required_ports[@]}"; do
        if netstat -an 2>/dev/null | grep -q ":$port.*LISTEN" || lsof -i :$port &>/dev/null; then
            log_warning "Port $port is already in use. This might cause conflicts."
        fi
    done

    # Check disk space (minimum 2GB)
    local available_space
    case "$OS" in
        macOS|Linux)
            available_space=$(df . | tail -1 | awk '{print $4}')
            available_space=$((available_space * 1024)) # Convert to bytes
            ;;
        *)
            available_space=0
            ;;
    esac

    if [ $available_space -lt 2147483648 ]; then # 2GB
        log_warning "Low disk space detected. At least 2GB recommended."
    fi

    # Check memory (minimum 4GB)
    case "$OS" in
        macOS)
            local total_memory=$(sysctl hw.memsize | awk '{print $2}')
            ;;
        Linux)
            local total_memory=$(grep MemTotal /proc/meminfo | awk '{print $2 * 1024}')
            ;;
        *)
            local total_memory=0
            ;;
    esac

    if [ $total_memory -lt 4294967296 ]; then # 4GB
        log_warning "Less than 4GB RAM detected. Performance may be affected."
    fi

    log_success "System requirements check completed"
}

setup_environment() {
    log_info "Setting up environment configuration..."

    # Create .env file from template if it doesn't exist
    if [ ! -f .env ]; then
        if [ -f env.template ]; then
            log_info "Creating .env file from template..."
            cp env.template .env
            
            # Generate secure secret key
            if command -v openssl &> /dev/null; then
                local secret_key=$(openssl rand -base64 32)
                sed -i.bak "s/your-secret-key-here-change-in-production/$secret_key/" .env
                rm -f .env.bak
            fi
            
            log_success ".env file created with generated secret key"
        else
            error_exit "env.template file not found"
        fi
    else
        log_success ".env file already exists"
    fi

    # Create required directories
    mkdir -p {logs,exports,tmp,uploads}
    mkdir -p exports/{pdf,csv,excel}
    mkdir -p logs/{api,celery,nginx}

    # Set environment-specific configurations
    if [ "$DEMO_ENV" = "development" ]; then
        export ENVIRONMENT=development
        export DEBUG=true
        export LOG_LEVEL=DEBUG
    elif [ "$DEMO_ENV" = "demo" ]; then
        export ENVIRONMENT=demo
        export DEBUG=false
        export LOG_LEVEL=INFO
    fi

    log_success "Environment setup completed"
}

install_dependencies() {
    log_info "Installing and checking dependencies..."

    # Python dependencies check
    if [ -f requirements.txt ]; then
        log_info "Checking Python dependencies..."
        if ! python3 -m pip check &> /dev/null; then
            log_info "Installing Python dependencies..."
            python3 -m pip install -r requirements.txt --quiet
            log_success "Python dependencies installed"
        else
            log_success "Python dependencies are up to date"
        fi
    fi

    # Build Docker images if they don't exist or if forced
    local force_build=${FORCE_BUILD:-false}
    if [ "$force_build" = "true" ] || ! docker images | grep -q "$PROJECT_NAME"; then
        log_info "Building Docker images..."
        docker-compose build --parallel
        log_success "Docker images built successfully"
    else
        log_success "Docker images already exist"
    fi
}

start_infrastructure() {
    log_info "Starting infrastructure services..."

    # Start core services first
    log_info "Starting database and cache services..."
    docker-compose up -d postgres redis

    # Wait for database to be ready
    log_info "Waiting for database to be ready..."
    local max_attempts=30
    local attempt=1
    while [ $attempt -le $max_attempts ]; do
        if docker-compose exec -T postgres pg_isready -U financial_planning -d financial_planning &>/dev/null; then
            break
        fi
        
        if [ $attempt -eq $max_attempts ]; then
            error_exit "Database failed to start after $max_attempts attempts"
        fi
        
        log_info "Waiting for database... (attempt $attempt/$max_attempts)"
        sleep 2
        ((attempt++))
    done
    
    log_success "Database is ready"

    # Wait for Redis to be ready
    log_info "Waiting for Redis to be ready..."
    attempt=1
    while [ $attempt -le $max_attempts ]; do
        if docker-compose exec -T redis redis-cli ping &>/dev/null; then
            break
        fi
        
        if [ $attempt -eq $max_attempts ]; then
            error_exit "Redis failed to start after $max_attempts attempts"
        fi
        
        log_info "Waiting for Redis... (attempt $attempt/$max_attempts)"
        sleep 1
        ((attempt++))
    done
    
    log_success "Redis is ready"
}

initialize_database() {
    log_info "Initializing database..."

    # Run database migrations
    log_info "Running database migrations..."
    if docker-compose exec -T api alembic upgrade head; then
        log_success "Database migrations completed"
    else
        error_exit "Database migrations failed"
    fi

    # Check if we should seed demo data
    if [ "$DEMO_ENV" = "demo" ] || [ "${SEED_DEMO_DATA:-true}" = "true" ]; then
        log_info "Seeding demo data..."
        if python3 scripts/seed_demo_data.py; then
            log_success "Demo data seeded successfully"
        else
            log_warning "Demo data seeding failed, continuing anyway"
        fi
    fi
}

start_application_services() {
    log_info "Starting application services..."

    # Determine which profiles to use
    local profiles=""
    if [ -n "$COMPOSE_PROFILES" ]; then
        profiles="--profile $COMPOSE_PROFILES"
    fi

    # Start all services
    docker-compose $profiles up -d

    # Wait for API to be ready
    log_info "Waiting for API to be ready..."
    local max_attempts=60
    local attempt=1
    while [ $attempt -le $max_attempts ]; do
        if curl -s "http://localhost:$BACKEND_PORT/health" &>/dev/null; then
            break
        fi
        
        if [ $attempt -eq $max_attempts ]; then
            error_exit "API failed to start after $max_attempts attempts"
        fi
        
        log_info "Waiting for API... (attempt $attempt/$max_attempts)"
        sleep 2
        ((attempt++))
    done
    
    log_success "API is ready"
}

run_health_checks() {
    log_info "Running health checks..."

    local failed_checks=0

    # API Health Check
    if curl -s "http://localhost:$BACKEND_PORT/health" | grep -q "healthy"; then
        log_success "✓ API health check passed"
    else
        log_error "✗ API health check failed"
        ((failed_checks++))
    fi

    # Database Health Check
    if docker-compose exec -T postgres pg_isready -U financial_planning -d financial_planning &>/dev/null; then
        log_success "✓ Database health check passed"
    else
        log_error "✗ Database health check failed"
        ((failed_checks++))
    fi

    # Redis Health Check
    if docker-compose exec -T redis redis-cli ping &>/dev/null; then
        log_success "✓ Redis health check passed"
    else
        log_error "✗ Redis health check failed"
        ((failed_checks++))
    fi

    # API Documentation Check
    if curl -s "http://localhost:$BACKEND_PORT/docs" &>/dev/null; then
        log_success "✓ API documentation accessible"
    else
        log_warning "⚠ API documentation check failed"
    fi

    if [ $failed_checks -gt 0 ]; then
        log_error "$failed_checks health check(s) failed"
        return 1
    fi

    log_success "All health checks passed"
}

open_browser() {
    if [ "$AUTO_OPEN_BROWSER" = "true" ]; then
        log_info "Opening browser to demo application..."
        
        # Wait a moment for services to stabilize
        sleep 3
        
        case "$OS" in
            macOS)
                open "http://localhost:$BACKEND_PORT/docs" &
                ;;
            Linux)
                if command -v xdg-open &> /dev/null; then
                    xdg-open "http://localhost:$BACKEND_PORT/docs" &
                fi
                ;;
            Windows)
                if command -v start &> /dev/null; then
                    start "http://localhost:$BACKEND_PORT/docs" &
                fi
                ;;
        esac
        
        log_success "Browser opened to API documentation"
    fi
}

print_demo_info() {
    echo ""
    echo "================================================================"
    echo "🎉 Financial Planning Demo Environment is Ready!"
    echo "================================================================"
    echo ""
    echo "📋 Service Information:"
    echo "  • API Server:          http://localhost:$BACKEND_PORT"
    echo "  • API Documentation:   http://localhost:$BACKEND_PORT/docs"
    echo "  • Health Check:        http://localhost:$BACKEND_PORT/health"
    echo "  • Database Admin:      http://localhost:5050 (admin@financialplanning.com / admin)"
    echo "  • Redis Admin:         http://localhost:8081"
    
    if docker-compose ps | grep -q grafana; then
        echo "  • Monitoring:          http://localhost:$GRAFANA_PORT (admin / admin)"
    fi
    
    echo ""
    echo "🔧 Useful Commands:"
    echo "  • View logs:           docker-compose logs -f [service]"
    echo "  • Stop demo:           ./stop_demo.sh"
    echo "  • Reset demo:          ./reset_demo.sh"
    echo "  • Run tests:           make test"
    echo "  • Check status:        docker-compose ps"
    echo ""
    echo "📖 Demo Features Available:"
    echo "  • Financial planning simulations"
    echo "  • Monte Carlo analysis"
    echo "  • AI-powered recommendations"
    echo "  • PDF report generation"
    echo "  • Voice interface (if configured)"
    echo "  • Real-time market data"
    echo ""
    echo "🚀 To test the API, try:"
    echo "  curl http://localhost:$BACKEND_PORT/health"
    echo ""
    echo "📱 Sample API endpoints:"
    echo "  • GET /api/v1/users/me"
    echo "  • POST /api/v1/simulations/monte-carlo"
    echo "  • GET /api/v1/market-data/quotes"
    echo ""
    echo "================================================================"
    echo "Demo startup completed successfully!"
    echo "================================================================"
}

main() {
    print_header
    
    # Main deployment flow
    check_system_requirements
    setup_environment
    install_dependencies
    start_infrastructure
    initialize_database
    start_application_services
    
    # Validation and finalization
    if run_health_checks; then
        open_browser
        print_demo_info
        
        log_success "Demo environment started successfully!"
        log_info "Use 'docker-compose logs -f' to monitor the services"
        log_info "Use './stop_demo.sh' when you're done"
    else
        error_exit "Health checks failed. Please check the logs for issues."
    fi
}

# Script execution with error handling
if [ "${BASH_SOURCE[0]}" == "${0}" ]; then
    main "$@"
fi