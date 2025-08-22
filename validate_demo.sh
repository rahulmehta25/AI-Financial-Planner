#!/bin/bash

# Demo Configuration Validator
# Validates that all demo files are properly configured

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Validation functions
print_status() {
    echo -e "${BLUE}[VALIDATE]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# Check file existence and permissions
check_file() {
    local file=$1
    local required=$2
    
    if [[ -f "$file" ]]; then
        print_success "Found: $file"
        
        # Check if file should be executable
        if [[ "$file" == *.sh ]]; then
            if [[ -x "$file" ]]; then
                print_success "Executable: $file"
            else
                print_warning "Not executable: $file (run: chmod +x $file)"
            fi
        fi
    else
        if [[ "$required" == "true" ]]; then
            print_error "Missing required file: $file"
            return 1
        else
            print_warning "Optional file missing: $file"
        fi
    fi
    return 0
}

# Validate Docker Compose file
validate_compose() {
    print_status "Validating Docker Compose configuration..."
    
    if command -v docker &> /dev/null && docker compose version &> /dev/null; then
        if docker compose -f docker-compose.demo.yml config > /dev/null 2>&1; then
            print_success "Docker Compose file is valid"
        else
            print_error "Docker Compose file has syntax errors"
            return 1
        fi
    else
        print_warning "Docker or Docker Compose not available - skipping validation"
    fi
    return 0
}

# Check environment file
validate_env_file() {
    print_status "Validating environment file..."
    
    if [[ -f ".env.demo" ]]; then
        # Check for required variables
        local required_vars=(
            "ENVIRONMENT"
            "DATABASE_URL" 
            "REDIS_URL"
            "SECRET_KEY"
            "ENABLE_DEMO_MODE"
        )
        
        local missing_vars=()
        
        for var in "${required_vars[@]}"; do
            if ! grep -q "^${var}=" .env.demo; then
                missing_vars+=("$var")
            fi
        done
        
        if [[ ${#missing_vars[@]} -eq 0 ]]; then
            print_success "All required environment variables present"
        else
            print_error "Missing environment variables: ${missing_vars[*]}"
            return 1
        fi
        
        # Check for demo-specific settings
        if grep -q "ENABLE_DEMO_MODE=true" .env.demo; then
            print_success "Demo mode enabled in environment"
        else
            print_warning "Demo mode not explicitly enabled"
        fi
        
    else
        print_error "Environment file .env.demo not found"
        return 1
    fi
    return 0
}

# Check Docker files
validate_dockerfiles() {
    print_status "Validating Dockerfiles..."
    
    local dockerfiles=(
        "backend/Dockerfile.demo"
        "frontend/Dockerfile.demo"
    )
    
    for dockerfile in "${dockerfiles[@]}"; do
        if [[ -f "$dockerfile" ]]; then
            # Basic syntax check
            if grep -q "FROM" "$dockerfile" && grep -q "WORKDIR" "$dockerfile"; then
                print_success "Dockerfile structure looks good: $dockerfile"
            else
                print_warning "Dockerfile may have issues: $dockerfile"
            fi
        else
            print_error "Missing Dockerfile: $dockerfile"
            return 1
        fi
    done
    return 0
}

# Check nginx configuration
validate_nginx_config() {
    print_status "Validating Nginx configuration..."
    
    if [[ -f "config/nginx.demo.conf" ]]; then
        # Check for basic nginx structure
        if grep -q "server {" config/nginx.demo.conf && \
           grep -q "upstream backend" config/nginx.demo.conf && \
           grep -q "upstream frontend" config/nginx.demo.conf; then
            print_success "Nginx configuration structure is valid"
        else
            print_warning "Nginx configuration may be incomplete"
        fi
        
        # Check for security headers
        if grep -q "X-Frame-Options" config/nginx.demo.conf; then
            print_success "Security headers configured in Nginx"
        else
            print_warning "Security headers not found in Nginx config"
        fi
    else
        print_error "Nginx configuration file not found"
        return 1
    fi
    return 0
}

# Check script files
validate_scripts() {
    print_status "Validating script files..."
    
    local scripts=(
        "start_docker_demo.sh"
        "backend/scripts/demo_data_seeder.py"
    )
    
    for script in "${scripts[@]}"; do
        if [[ -f "$script" ]]; then
            print_success "Found script: $script"
            
            # Check shebang
            if head -1 "$script" | grep -q "^#!"; then
                print_success "Shebang present: $script"
            else
                print_warning "No shebang in script: $script"
            fi
        else
            print_error "Missing script: $script"
            return 1
        fi
    done
    return 0
}

# Check ports availability
check_ports() {
    print_status "Checking port availability..."
    
    local ports=(80 3000 8000 6379)
    local occupied_ports=()
    
    for port in "${ports[@]}"; do
        if command -v lsof &> /dev/null; then
            if lsof -i ":$port" &> /dev/null; then
                occupied_ports+=("$port")
            fi
        elif command -v netstat &> /dev/null; then
            if netstat -ln | grep -q ":$port "; then
                occupied_ports+=("$port")
            fi
        fi
    done
    
    if [[ ${#occupied_ports[@]} -eq 0 ]]; then
        print_success "All required ports are available"
    else
        print_warning "Ports in use (may cause conflicts): ${occupied_ports[*]}"
    fi
}

# Main validation function
main() {
    echo -e "${BLUE}Financial Planning System - Demo Configuration Validator${NC}"
    echo "================================================================"
    echo ""
    
    local validation_failed=false
    
    # File structure validation
    print_status "Checking file structure..."
    
    local required_files=(
        "docker-compose.demo.yml:true"
        ".env.demo:true"
        "start_docker_demo.sh:true"
        "config/nginx.demo.conf:true"
        "backend/Dockerfile.demo:true"
        "frontend/Dockerfile.demo:true"
        "backend/scripts/demo_data_seeder.py:true"
    )
    
    for file_info in "${required_files[@]}"; do
        IFS=':' read -r file required <<< "$file_info"
        if ! check_file "$file" "$required"; then
            validation_failed=true
        fi
    done
    
    echo ""
    
    # Configuration validation
    if ! validate_compose; then
        validation_failed=true
    fi
    
    echo ""
    
    if ! validate_env_file; then
        validation_failed=true
    fi
    
    echo ""
    
    if ! validate_dockerfiles; then
        validation_failed=true
    fi
    
    echo ""
    
    if ! validate_nginx_config; then
        validation_failed=true
    fi
    
    echo ""
    
    if ! validate_scripts; then
        validation_failed=true
    fi
    
    echo ""
    
    check_ports
    
    echo ""
    echo "================================================================"
    
    if [[ "$validation_failed" == true ]]; then
        print_error "Demo configuration validation FAILED!"
        echo -e "${RED}Please fix the issues above before running the demo.${NC}"
        return 1
    else
        print_success "Demo configuration validation PASSED!"
        echo -e "${GREEN}Your demo setup is ready to go!${NC}"
        echo ""
        echo -e "${BLUE}To start the demo, run:${NC}"
        echo -e "${YELLOW}  ./start_docker_demo.sh${NC}"
        echo ""
        return 0
    fi
}

# Run main function
main