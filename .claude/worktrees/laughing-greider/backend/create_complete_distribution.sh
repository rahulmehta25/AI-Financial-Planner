#!/bin/bash

# Financial Planning Demo - Complete Distribution Creator
# Master script that creates all distribution formats and packages
# Author: Financial Planning Team

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
VERSION=$(cat "$SCRIPT_DIR/VERSION" 2>/dev/null || echo "1.0.0")
BUILD_DATE=$(date +%Y%m%d)
DIST_DIR="$PROJECT_ROOT/dist"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# Logging functions
log() { echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"; }
success() { echo -e "${GREEN}✓ $1${NC}"; }
warning() { echo -e "${YELLOW}⚠ $1${NC}"; }
error() { echo -e "${RED}✗ $1${NC}"; exit 1; }
info() { echo -e "${CYAN}ℹ $1${NC}"; }
header() { echo -e "${PURPLE}${BOLD}$1${NC}"; }

# Configuration
ENABLE_DOCKER=${ENABLE_DOCKER:-true}
ENABLE_INSTALLER=${ENABLE_INSTALLER:-true}
ENABLE_PACKAGE=${ENABLE_PACKAGE:-true}
ENABLE_VERIFICATION=${ENABLE_VERIFICATION:-true}
CLEANUP_AFTER=${CLEANUP_AFTER:-false}

show_banner() {
    clear
    echo -e "${CYAN}"
    echo "╔═══════════════════════════════════════════════════════════╗"
    echo "║                                                           ║"
    echo "║    ${BOLD}Financial Planning Demo - Distribution Creator${NC}${CYAN}     ║"
    echo "║                                                           ║"
    echo "║    Version: $VERSION                                     ║"
    echo "║    Build Date: $BUILD_DATE                              ║"
    echo "║    Platform: $(uname -s) $(uname -m)                     ║"
    echo "║                                                           ║"
    echo "╚═══════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    echo ""
}

# Pre-flight checks
preflight_checks() {
    header "Running Pre-flight Checks"
    echo "──────────────────────────────────────"
    
    # Check required tools
    local required_tools=("tar" "zip" "sha256sum" "find" "python3")
    local optional_tools=("docker" "docker-compose" "kubectl")
    
    log "Checking required tools..."
    for tool in "${required_tools[@]}"; do
        if command -v "$tool" &> /dev/null; then
            success "$tool found"
        else
            error "$tool is required but not found"
        fi
    done
    
    log "Checking optional tools..."
    for tool in "${optional_tools[@]}"; do
        if command -v "$tool" &> /dev/null; then
            success "$tool found"
        else
            warning "$tool not found (optional)"
        fi
    done
    
    # Check disk space
    log "Checking available disk space..."
    AVAILABLE_KB=$(df "$PROJECT_ROOT" | awk 'NR==2 {print $4}')
    AVAILABLE_GB=$((AVAILABLE_KB / 1024 / 1024))
    
    if [ "$AVAILABLE_GB" -lt 5 ]; then
        warning "Low disk space: ${AVAILABLE_GB}GB available (5GB+ recommended)"
    else
        success "Disk space: ${AVAILABLE_GB}GB available"
    fi
    
    # Check Python environment
    log "Checking Python environment..."
    if python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)" 2>/dev/null; then
        PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
        success "Python $PYTHON_VERSION found"
    else
        warning "Python 3.8+ recommended for full functionality"
    fi
    
    # Check Docker availability
    if command -v docker &> /dev/null && docker info &> /dev/null; then
        DOCKER_VERSION=$(docker --version | cut -d' ' -f3 | sed 's/,//')
        success "Docker $DOCKER_VERSION available"
        DOCKER_AVAILABLE=true
    else
        warning "Docker not available - Docker distributions will be skipped"
        DOCKER_AVAILABLE=false
        ENABLE_DOCKER=false
    fi
    
    echo ""
    success "Pre-flight checks completed"
    echo ""
}

# Show configuration
show_configuration() {
    header "Distribution Configuration"
    echo "──────────────────────────────────"
    
    echo -e "${BOLD}Build Information:${NC}"
    echo "  Version: $VERSION"
    echo "  Build Date: $BUILD_DATE"
    echo "  Project Root: $PROJECT_ROOT"
    echo "  Distribution Dir: $DIST_DIR"
    echo ""
    
    echo -e "${BOLD}Enabled Components:${NC}"
    echo "  📦 Core Package: $([ "$ENABLE_PACKAGE" = true ] && echo "✓ Yes" || echo "✗ No")"
    echo "  🐳 Docker Distributions: $([ "$ENABLE_DOCKER" = true ] && echo "✓ Yes" || echo "✗ No")"
    echo "  💽 Installers: $([ "$ENABLE_INSTALLER" = true ] && echo "✓ Yes" || echo "✗ No")"
    echo "  🔍 Verification: $([ "$ENABLE_VERIFICATION" = true ] && echo "✓ Yes" || echo "✗ No")"
    echo "  🧹 Cleanup After: $([ "$CLEANUP_AFTER" = true ] && echo "✓ Yes" || echo "✗ No")"
    echo ""
    
    echo -e "${BOLD}Distribution Formats:${NC}"
    echo "  • ZIP archive (.zip)"
    echo "  • TAR.GZ archive (.tar.gz)"
    if [ "$ENABLE_DOCKER" = true ]; then
        echo "  • Docker image (docker.tar.gz)"
        echo "  • Docker Compose configurations"
        echo "  • Kubernetes manifests"
    fi
    if [ "$ENABLE_INSTALLER" = true ]; then
        echo "  • Self-extracting installer (.sh)"
        echo "  • Windows installer (.bat)"
        echo "  • macOS installer (.app)"
    fi
    echo ""
    
    info "Press Enter to continue or Ctrl+C to cancel..."
    read -r
    echo ""
}

# Create core package
create_core_package() {
    if [ "$ENABLE_PACKAGE" != true ]; then
        return 0
    fi
    
    header "Creating Core Package"
    echo "─────────────────────────"
    
    log "Running core package creation..."
    if ! bash "$SCRIPT_DIR/package_demo.sh"; then
        error "Core package creation failed"
    fi
    
    success "Core package created successfully"
    echo ""
}

# Create Docker distributions
create_docker_distributions() {
    if [ "$ENABLE_DOCKER" != true ]; then
        return 0
    fi
    
    header "Creating Docker Distributions"
    echo "────────────────────────────────"
    
    log "Running Docker distribution creation..."
    if ! bash "$SCRIPT_DIR/create_docker_distribution.sh"; then
        error "Docker distribution creation failed"
    fi
    
    success "Docker distributions created successfully"
    echo ""
}

# Create installers
create_installers() {
    if [ "$ENABLE_INSTALLER" != true ]; then
        return 0
    fi
    
    header "Creating Installers"
    echo "───────────────────"
    
    log "Running installer creation..."
    if ! bash "$SCRIPT_DIR/create_installer.sh"; then
        error "Installer creation failed"
    fi
    
    success "Installers created successfully"
    echo ""
}

# Verify distributions
verify_distributions() {
    if [ "$ENABLE_VERIFICATION" != true ]; then
        return 0
    fi
    
    header "Verifying Distributions"
    echo "──────────────────────"
    
    log "Verifying package integrity..."
    
    cd "$DIST_DIR"
    
    # Check checksums
    if [ -f "*-checksums.sha256" ]; then
        log "Verifying checksums..."
        if sha256sum -c *-checksums.sha256; then
            success "All checksums verified"
        else
            warning "Some checksum verifications failed"
        fi
    fi
    
    # Test archive extraction
    log "Testing archive extraction..."
    for archive in *.tar.gz *.zip; do
        if [ -f "$archive" ] && [[ "$archive" != *"docker"* ]]; then
            log "Testing $archive..."
            
            # Create temporary test directory
            TEST_DIR="/tmp/fp_test_$$"
            mkdir -p "$TEST_DIR"
            
            # Extract and verify
            if [[ "$archive" == *.tar.gz ]]; then
                if tar -tf "$archive" > /dev/null 2>&1; then
                    success "$archive: Valid tar.gz structure"
                    # Quick extraction test
                    tar -xzf "$archive" -C "$TEST_DIR" > /dev/null 2>&1
                    if [ -d "$TEST_DIR"/*/ ]; then
                        success "$archive: Extraction test passed"
                    else
                        warning "$archive: Extraction test inconclusive"
                    fi
                else
                    warning "$archive: Invalid tar.gz structure"
                fi
            elif [[ "$archive" == *.zip ]]; then
                if zip -T "$archive" > /dev/null 2>&1; then
                    success "$archive: Valid zip structure"
                else
                    warning "$archive: Invalid zip structure"
                fi
            fi
            
            # Cleanup
            rm -rf "$TEST_DIR"
        fi
    done
    
    # Test Docker images if available
    if [ "$DOCKER_AVAILABLE" = true ] && ls *-docker.tar.gz > /dev/null 2>&1; then
        log "Testing Docker images..."
        for docker_image in *-docker.tar.gz; do
            log "Testing $docker_image..."
            
            # Load image temporarily
            IMAGE_ID=$(docker load -i "$docker_image" | grep "Loaded image" | cut -d' ' -f3)
            if [ -n "$IMAGE_ID" ]; then
                success "$docker_image: Docker image loaded successfully"
                
                # Quick container test (without starting)
                if docker create "$IMAGE_ID" > /dev/null 2>&1; then
                    success "$docker_image: Container creation test passed"
                    # Cleanup created container
                    docker rm $(docker ps -aq --filter ancestor="$IMAGE_ID") > /dev/null 2>&1 || true
                else
                    warning "$docker_image: Container creation test failed"
                fi
                
                # Remove test image
                docker rmi "$IMAGE_ID" > /dev/null 2>&1 || true
            else
                warning "$docker_image: Failed to load Docker image"
            fi
        done
    fi
    
    success "Distribution verification completed"
    echo ""
}

# Generate final report
generate_final_report() {
    header "Distribution Summary Report"
    echo "─────────────────────────────"
    
    cd "$DIST_DIR"
    
    # Count distributions
    local archives=$(ls *.zip *.tar.gz 2>/dev/null | wc -l)
    local installers=$(ls *installer* *.app 2>/dev/null | wc -l)
    local docker_files=$(ls *docker* docker/ -d 2>/dev/null | wc -l)
    
    echo -e "${BOLD}Build Summary:${NC}"
    echo "  Version: $VERSION"
    echo "  Build ID: $VERSION-$BUILD_DATE"
    echo "  Build Time: $(date)"
    echo "  Total Files Created: $(find . -type f | wc -l)"
    echo "  Total Size: $(du -sh . | cut -f1)"
    echo ""
    
    echo -e "${BOLD}Distribution Breakdown:${NC}"
    echo "  📦 Archives: $archives"
    echo "  💽 Installers: $installers"
    echo "  🐳 Docker Components: $docker_files"
    echo ""
    
    if [ "$archives" -gt 0 ]; then
        echo -e "${BOLD}Archive Details:${NC}"
        for archive in *.zip *.tar.gz; do
            if [ -f "$archive" ]; then
                SIZE=$(du -h "$archive" | cut -f1)
                echo "  • $archive ($SIZE)"
            fi
        done
        echo ""
    fi
    
    if [ "$installers" -gt 0 ]; then
        echo -e "${BOLD}Installer Details:${NC}"
        for installer in *installer* *.app; do
            if [ -f "$installer" ] || [ -d "$installer" ]; then
                SIZE=$(du -sh "$installer" | cut -f1)
                echo "  • $installer ($SIZE)"
            fi
        done
        echo ""
    fi
    
    if [ -d "docker" ]; then
        echo -e "${BOLD}Docker Components:${NC}"
        echo "  • Multi-stage Dockerfiles (Demo, Dev, Full-stack)"
        echo "  • Docker Compose configurations (Demo, Dev, Prod)"
        echo "  • Kubernetes manifests with overlays"
        echo "  • Helper scripts for build and deployment"
        echo ""
    fi
    
    echo -e "${BOLD}Quick Start Options:${NC}"
    echo ""
    
    # Show installer options
    if ls *installer*.sh > /dev/null 2>&1; then
        echo -e "${GREEN}Option 1: Self-Extracting Installer (Recommended)${NC}"
        INSTALLER_FILE=$(ls *installer*.sh | head -1)
        echo "  chmod +x $INSTALLER_FILE"
        echo "  ./$INSTALLER_FILE"
        echo ""
    fi
    
    # Show archive options
    if ls *.tar.gz > /dev/null 2>&1; then
        ARCHIVE_FILE=$(ls *.tar.gz | grep -v docker | head -1)
        if [ -n "$ARCHIVE_FILE" ]; then
            echo -e "${GREEN}Option 2: Manual Archive Extraction${NC}"
            echo "  tar -xzf $ARCHIVE_FILE"
            echo "  cd financial-planning-demo-*/"
            echo "  ./start_demo.sh"
            echo ""
        fi
    fi
    
    # Show Docker options
    if [ -d "docker" ]; then
        echo -e "${GREEN}Option 3: Docker Deployment${NC}"
        echo "  cd docker/"
        echo "  ./scripts/build.sh $VERSION demo"
        echo "  ./scripts/run.sh demo"
        echo ""
    fi
    
    echo -e "${BOLD}Access Information:${NC}"
    echo "  🌐 Web Interface: http://localhost:8000"
    echo "  📖 API Documentation: http://localhost:8000/docs"
    echo "  ❤️ Health Check: http://localhost:8000/health"
    echo ""
    
    echo -e "${BOLD}Support Resources:${NC}"
    echo "  📚 Complete Guide: DEMO_PACKAGE_README.md (in package)"
    echo "  🚀 Quick Start: docs/QUICKSTART.md (in package)"
    echo "  🐛 Troubleshooting: See documentation for common issues"
    echo "  📊 Health Monitoring: Built-in health check endpoints"
    echo ""
    
    # Create distribution manifest
    cat > "DISTRIBUTION_MANIFEST.txt" << EOF
Financial Planning Demo - Distribution Manifest
==============================================

Build Information:
- Version: $VERSION
- Build ID: $VERSION-$BUILD_DATE
- Build Date: $(date)
- Build Host: $(hostname)
- Platform: $(uname -s) $(uname -m)

Distribution Contents:
$(find . -type f -not -name "DISTRIBUTION_MANIFEST.txt" | sort)

File Sizes:
$(find . -type f -not -name "DISTRIBUTION_MANIFEST.txt" -exec du -h {} \; | sort -hr)

Package Checksums:
$(find . -name "*.sha256" -exec cat {} \; 2>/dev/null || echo "No checksums available")

Installation Options:
1. Self-extracting installer: Run any *installer*.sh file
2. Archive extraction: Extract *.tar.gz and run start_demo.sh
3. Docker deployment: Use docker/ directory components

Access URLs (when running):
- Demo Interface: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

Generated: $(date)
EOF

    success "Distribution summary report generated"
    echo ""
}

# Cleanup function
cleanup_build_artifacts() {
    if [ "$CLEANUP_AFTER" != true ]; then
        return 0
    fi
    
    header "Cleaning Up Build Artifacts"
    echo "────────────────────────────────"
    
    log "Removing temporary files..."
    
    # Remove temporary Python cache files
    find "$PROJECT_ROOT" -name "*.pyc" -delete 2>/dev/null || true
    find "$PROJECT_ROOT" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
    
    # Remove build logs
    rm -f "$PROJECT_ROOT"/*.log 2>/dev/null || true
    
    # Remove temporary directories
    rm -rf "/tmp/fp_"* 2>/dev/null || true
    
    success "Build artifacts cleaned up"
    echo ""
}

# Main execution function
main() {
    trap cleanup_build_artifacts EXIT
    
    show_banner
    preflight_checks
    show_configuration
    
    # Start timing
    START_TIME=$(date +%s)
    
    header "Starting Distribution Creation Process"
    echo "═══════════════════════════════════════════"
    echo ""
    
    # Create distributions
    create_core_package
    create_docker_distributions  
    create_installers
    verify_distributions
    generate_final_report
    
    # End timing
    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))
    
    echo ""
    header "Distribution Creation Completed!"
    echo "═══════════════════════════════════════"
    
    success "All distributions created successfully!"
    success "Build completed in ${DURATION} seconds"
    echo ""
    echo -e "${GREEN}Distribution Location: $DIST_DIR${NC}"
    echo ""
    echo -e "${BOLD}Ready for deployment and distribution! 🚀${NC}"
    echo ""
    
    # Final file listing
    echo -e "${CYAN}Final Distribution Contents:${NC}"
    ls -la "$DIST_DIR" | grep -E '\.(zip|gz|sh|bat|app|txt|md)$|^d.*docker' || \
    ls -la "$DIST_DIR"
    
    echo ""
    info "For detailed usage instructions, see DEMO_PACKAGE_README.md in any extracted package"
}

# Handle command line options
while [[ $# -gt 0 ]]; do
    case $1 in
        --no-docker)
            ENABLE_DOCKER=false
            shift
            ;;
        --no-installer)
            ENABLE_INSTALLER=false
            shift
            ;;
        --no-package)
            ENABLE_PACKAGE=false
            shift
            ;;
        --no-verification)
            ENABLE_VERIFICATION=false
            shift
            ;;
        --cleanup)
            CLEANUP_AFTER=true
            shift
            ;;
        --help|-h)
            echo "Financial Planning Demo - Distribution Creator"
            echo ""
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  --no-docker       Skip Docker distribution creation"
            echo "  --no-installer    Skip installer creation"
            echo "  --no-package      Skip core package creation"
            echo "  --no-verification Skip distribution verification"
            echo "  --cleanup         Clean up build artifacts after completion"
            echo "  --help, -h        Show this help message"
            echo ""
            echo "Example:"
            echo "  $0                           # Create all distributions"
            echo "  $0 --no-docker --cleanup     # Skip Docker, cleanup after"
            echo ""
            exit 0
            ;;
        *)
            error "Unknown option: $1. Use --help for usage information."
            ;;
    esac
done

# Execute main function
main "$@"