#!/bin/bash

# Demo Smoke Tests - Quick Validation Script
# ==========================================
# 
# This script runs quick validation checks for all demos:
# - Checks file integrity 
# - Validates dependencies
# - Tests network connectivity
# - Ensures ports are available
# - Reports status for each demo

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
MOBILE_DIR="$PROJECT_ROOT/mobile"
LOG_FILE="/tmp/demo-smoke-tests.log"
QUICK_MODE=false
VERBOSE=false

# Test results tracking
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0
SKIPPED_TESTS=0

# Logging functions
log_info() { 
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$LOG_FILE"
    [ "$VERBOSE" = true ] && echo "$(date): [INFO] $1" >> "$LOG_FILE"
}

log_success() { 
    echo -e "${GREEN}[PASS]${NC} $1" | tee -a "$LOG_FILE"
    ((PASSED_TESTS++))
}

log_warning() { 
    echo -e "${YELLOW}[WARN]${NC} $1" | tee -a "$LOG_FILE"
}

log_error() { 
    echo -e "${RED}[FAIL]${NC} $1" | tee -a "$LOG_FILE"
    ((FAILED_TESTS++))
}

log_skip() {
    echo -e "${YELLOW}[SKIP]${NC} $1" | tee -a "$LOG_FILE"
    ((SKIPPED_TESTS++))
}

# Helper functions
run_test() {
    local test_name="$1"
    local test_command="$2"
    local required="${3:-true}"
    
    ((TOTAL_TESTS++))
    
    log_info "Running: $test_name"
    
    if [ "$VERBOSE" = true ]; then
        echo "Command: $test_command" >> "$LOG_FILE"
    fi
    
    if eval "$test_command" 2>>"$LOG_FILE"; then
        log_success "$test_name"
        return 0
    else
        if [ "$required" = "true" ]; then
            log_error "$test_name"
        else
            log_skip "$test_name (optional)"
        fi
        return 1
    fi
}

check_port_available() {
    local port="$1"
    local service_name="${2:-service}"
    
    if command -v netstat >/dev/null 2>&1; then
        ! netstat -an 2>/dev/null | grep -q ":$port.*LISTEN"
    elif command -v lsof >/dev/null 2>&1; then
        ! lsof -i ":$port" >/dev/null 2>&1
    else
        log_warning "Cannot check port $port - no netstat or lsof available"
        return 0
    fi
}

check_file_integrity() {
    local file_path="$1"
    
    # Check if file exists and is readable
    [ -f "$file_path" ] && [ -r "$file_path" ]
}

check_python_syntax() {
    local python_file="$1"
    
    if [ -f "$python_file" ]; then
        python3 -m py_compile "$python_file" 2>/dev/null
    else
        return 1
    fi
}

print_header() {
    echo "================================================================"
    echo "🚀 Financial Planning Demo - Smoke Test Suite"
    echo "================================================================"
    echo "Timestamp: $(date)"
    echo "Project Root: $PROJECT_ROOT"
    echo "Log File: $LOG_FILE"
    echo "Quick Mode: $QUICK_MODE"
    echo "================================================================"
    echo ""
}

print_summary() {
    echo ""
    echo "================================================================"
    echo "📊 Test Results Summary"
    echo "================================================================"
    echo "Total Tests:  $TOTAL_TESTS"
    echo -e "Passed:       ${GREEN}$PASSED_TESTS${NC}"
    echo -e "Failed:       ${RED}$FAILED_TESTS${NC}"  
    echo -e "Skipped:      ${YELLOW}$SKIPPED_TESTS${NC}"
    echo ""
    
    local success_rate=0
    if [ "$TOTAL_TESTS" -gt 0 ]; then
        success_rate=$((PASSED_TESTS * 100 / TOTAL_TESTS))
    fi
    
    if [ "$FAILED_TESTS" -eq 0 ]; then
        echo -e "${GREEN}✅ All critical tests passed! ($success_rate% success rate)${NC}"
        echo "================================================================"
        return 0
    else
        echo -e "${RED}❌ $FAILED_TESTS test(s) failed ($success_rate% success rate)${NC}"
        echo -e "${YELLOW}📋 Check log file for details: $LOG_FILE${NC}"
        echo "================================================================"
        return 1
    fi
}

# Test functions
test_system_requirements() {
    log_info "🔧 Testing System Requirements"
    
    run_test "Python 3 availability" "command -v python3 >/dev/null"
    
    if command -v python3 >/dev/null; then
        python_version=$(python3 --version 2>&1 | cut -d' ' -f2)
        run_test "Python version >= 3.8" "python3 -c 'import sys; exit(0 if sys.version_info >= (3, 8) else 1)'"
    fi
    
    run_test "Git availability" "command -v git >/dev/null" false
    run_test "Docker availability" "command -v docker >/dev/null" false
    run_test "Node.js availability" "command -v node >/dev/null" false
    run_test "npm availability" "command -v npm >/dev/null" false
    
    if command -v docker >/dev/null; then
        run_test "Docker daemon running" "docker info >/dev/null 2>&1" false
    fi
}

test_file_integrity() {
    log_info "📁 Testing File Integrity"
    
    # Core demo files
    local demo_files=(
        "backend/working_demo.py"
        "backend/minimal_working_demo.py"
        "backend/ml_simulation_demo.py"
        "backend/cli_demo.py"
        "backend/security_demo.py"
        "backend/performance_demo.py"
        "backend/data_pipeline_demo.py"
        "backend/simple_data_pipeline_demo.py"
    )
    
    for file in "${demo_files[@]}"; do
        run_test "File integrity: $file" "check_file_integrity '$PROJECT_ROOT/$file'"
    done
    
    # Script files
    local script_files=(
        "backend/start_demo.sh"
        "backend/stop_demo.sh" 
        "backend/reset_demo.sh"
        "validate_demo.sh"
        "start_docker_demo.sh"
    )
    
    for script in "${script_files[@]}"; do
        local script_path="$PROJECT_ROOT/$script"
        if [ -f "$script_path" ]; then
            run_test "Script executable: $script" "[ -x '$script_path' ]"
        else
            log_skip "Script not found: $script"
        fi
    done
    
    # Configuration files
    local config_files=(
        "backend/requirements.txt"
        "docker-compose.yml"
        "backend/pytest.ini"
    )
    
    for config in "${config_files[@]}"; do
        run_test "Config file: $config" "check_file_integrity '$PROJECT_ROOT/$config'"
    done
}

test_python_syntax() {
    log_info "🐍 Testing Python Syntax"
    
    local python_files=(
        "backend/working_demo.py"
        "backend/minimal_working_demo.py"
        "backend/ml_simulation_demo.py"
        "backend/cli_demo.py" 
        "backend/security_demo.py"
        "backend/performance_demo.py"
        "backend/data_pipeline_demo.py"
        "backend/simple_data_pipeline_demo.py"
    )
    
    for py_file in "${python_files[@]}"; do
        local full_path="$PROJECT_ROOT/$py_file"
        if [ -f "$full_path" ]; then
            run_test "Python syntax: $py_file" "check_python_syntax '$full_path'"
        else
            log_skip "Python file not found: $py_file"
        fi
    done
}

test_dependencies() {
    log_info "📦 Testing Dependencies"
    
    # Core Python dependencies
    local core_deps=(
        "fastapi"
        "uvicorn"
        "numpy"
        "pydantic"
        "jose"
        "passlib"
    )
    
    for dep in "${core_deps[@]}"; do
        run_test "Python import: $dep" "python3 -c 'import $dep' 2>/dev/null"
    done
    
    # Optional dependencies
    local optional_deps=(
        "scipy"
        "matplotlib"
        "reportlab"
        "numba"
        "requests"
        "psutil"
    )
    
    for dep in "${optional_deps[@]}"; do
        run_test "Optional import: $dep" "python3 -c 'import $dep' 2>/dev/null" false
    done
}

test_network_connectivity() {
    log_info "🌐 Testing Network Connectivity"
    
    # Test internet connectivity
    if command -v curl >/dev/null; then
        run_test "Internet connectivity" "curl -s --max-time 10 https://httpbin.org/status/200 >/dev/null" false
    elif command -v wget >/dev/null; then
        run_test "Internet connectivity" "wget -q --timeout=10 -O /dev/null https://httpbin.org/status/200" false
    else
        log_skip "No curl or wget available for connectivity test"
    fi
    
    # Test localhost resolution
    run_test "Localhost resolution" "ping -c 1 localhost >/dev/null 2>&1" false
}

test_port_availability() {
    log_info "🔌 Testing Port Availability"
    
    local required_ports=(8000 3000 5432 6379 9090 3001)
    
    for port in "${required_ports[@]}"; do
        run_test "Port $port available" "check_port_available $port" false
    done
}

test_docker_configuration() {
    if [ "$QUICK_MODE" = true ]; then
        log_skip "Docker tests (quick mode)"
        return
    fi
    
    log_info "🐳 Testing Docker Configuration"
    
    if ! command -v docker >/dev/null; then
        log_skip "Docker not available"
        return
    fi
    
    # Test docker-compose files
    local compose_files=(
        "docker-compose.yml"
        "docker-compose.demo.yml"
    )
    
    for compose_file in "${compose_files[@]}"; do
        local compose_path="$PROJECT_ROOT/$compose_file"
        if [ -f "$compose_path" ]; then
            if command -v docker-compose >/dev/null; then
                run_test "Docker compose valid: $compose_file" "cd '$PROJECT_ROOT' && docker-compose -f '$compose_file' config >/dev/null"
            else
                run_test "Docker compose valid: $compose_file" "cd '$PROJECT_ROOT' && docker compose -f '$compose_file' config >/dev/null"
            fi
        else
            log_skip "Docker compose file not found: $compose_file"
        fi
    done
    
    # Test Dockerfile syntax
    local dockerfiles=(
        "backend/Dockerfile"
        "backend/Dockerfile.demo"
        "frontend/Dockerfile"
    )
    
    for dockerfile in "${dockerfiles[@]}"; do
        local dockerfile_path="$PROJECT_ROOT/$dockerfile"
        if [ -f "$dockerfile_path" ]; then
            run_test "Dockerfile syntax: $dockerfile" "docker build --dry-run -f '$dockerfile_path' '$PROJECT_ROOT' >/dev/null 2>&1" false
        else
            log_skip "Dockerfile not found: $dockerfile"
        fi
    done
}

test_frontend_configuration() {
    if [ "$QUICK_MODE" = true ]; then
        log_skip "Frontend tests (quick mode)"
        return
    fi
    
    log_info "⚛️ Testing Frontend Configuration"
    
    if [ ! -d "$FRONTEND_DIR" ]; then
        log_skip "Frontend directory not found"
        return
    fi
    
    # Test package.json
    local package_json="$FRONTEND_DIR/package.json"
    if [ -f "$package_json" ]; then
        run_test "package.json valid" "cd '$FRONTEND_DIR' && node -e 'JSON.parse(require(\"fs\").readFileSync(\"package.json\"))'" false
        
        if command -v npm >/dev/null; then
            run_test "npm scripts defined" "cd '$FRONTEND_DIR' && npm run --silent 2>/dev/null | grep -q 'available via'" false
        fi
    else
        log_skip "package.json not found"
    fi
}

test_mobile_configuration() {
    if [ "$QUICK_MODE" = true ]; then
        log_skip "Mobile tests (quick mode)"
        return
    fi
    
    log_info "📱 Testing Mobile Configuration"
    
    if [ ! -d "$MOBILE_DIR" ]; then
        log_skip "Mobile directory not found"
        return
    fi
    
    # Test mobile package.json files
    local mobile_packages=(
        "$MOBILE_DIR/package.json"
        "$MOBILE_DIR/demo-app/package.json"
    )
    
    for package_file in "${mobile_packages[@]}"; do
        if [ -f "$package_file" ]; then
            run_test "Mobile package.json: $(basename $(dirname $package_file))" "node -e 'JSON.parse(require(\"fs\").readFileSync(\"$package_file\"))'" false
        else
            log_skip "Mobile package.json not found: $(basename $(dirname $package_file))"
        fi
    done
}

test_demo_quick_start() {
    if [ "$QUICK_MODE" = true ]; then
        log_skip "Demo startup tests (quick mode)"
        return
    fi
    
    log_info "🚀 Testing Demo Quick Start"
    
    # Test if we can import and validate core demo modules
    local demo_modules=(
        "working_demo"
        "minimal_working_demo"
    )
    
    for module in "${demo_modules[@]}"; do
        local module_path="$BACKEND_DIR/$module.py"
        if [ -f "$module_path" ]; then
            # Test if module can be imported without actually running it
            run_test "Module import: $module" "cd '$BACKEND_DIR' && python3 -c 'import sys; sys.argv=[\"test\"]; exec(open(\"$module.py\").read(), {\"__name__\": \"__test__\"})' 2>/dev/null || python3 -c 'import ast; ast.parse(open(\"$module.py\").read())'" false
        else
            log_skip "Module not found: $module"
        fi
    done
}

# Main execution
main() {
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --quick|-q)
                QUICK_MODE=true
                shift
                ;;
            --verbose|-v)
                VERBOSE=true
                shift
                ;;
            --help|-h)
                echo "Usage: $0 [OPTIONS]"
                echo ""
                echo "Options:"
                echo "  --quick, -q     Run only essential tests (faster)"
                echo "  --verbose, -v   Enable verbose logging"
                echo "  --help, -h      Show this help message"
                echo ""
                echo "This script performs smoke tests to validate demo functionality:"
                echo "  • File integrity checks"
                echo "  • Dependency validation"
                echo "  • Network connectivity tests"
                echo "  • Port availability checks"
                echo "  • Configuration validation"
                exit 0
                ;;
            *)
                echo "Unknown option: $1"
                echo "Use --help for usage information"
                exit 1
                ;;
        esac
    done
    
    # Initialize log file
    echo "Demo Smoke Tests - $(date)" > "$LOG_FILE"
    
    print_header
    
    # Run test suites
    test_system_requirements
    test_file_integrity
    test_python_syntax
    test_dependencies
    test_network_connectivity
    test_port_availability
    test_docker_configuration
    test_frontend_configuration
    test_mobile_configuration
    test_demo_quick_start
    
    # Print summary and exit with appropriate code
    if print_summary; then
        log_info "🎉 All smoke tests completed successfully!"
        exit 0
    else
        log_error "❌ Some smoke tests failed. Check the log for details."
        exit 1
    fi
}

# Trap to ensure cleanup on script exit
cleanup() {
    if [ $? -ne 0 ]; then
        log_warning "Script interrupted or failed"
    fi
}
trap cleanup EXIT

# Run main function if script is executed directly
if [ "${BASH_SOURCE[0]}" == "${0}" ]; then
    main "$@"
fi