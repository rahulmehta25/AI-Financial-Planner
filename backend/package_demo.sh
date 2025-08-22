#!/bin/bash

# Financial Planning Demo Packaging Script
# Creates a complete distributable package of the demo system
# Author: Financial Planning Team
# Version: 1.0.0

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
PACKAGE_NAME="financial-planning-demo"
VERSION=$(cat "$SCRIPT_DIR/VERSION" 2>/dev/null || echo "1.0.0")
BUILD_DATE=$(date +%Y%m%d)
BUILD_ID="${VERSION}-${BUILD_DATE}"
DIST_DIR="$PROJECT_ROOT/dist"
PACKAGE_DIR="$DIST_DIR/$PACKAGE_NAME-$BUILD_ID"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

success() {
    echo -e "${GREEN}[SUCCESS] $1${NC}"
}

warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
    exit 1
}

# Create distribution directory
create_dist_directory() {
    log "Creating distribution directory..."
    rm -rf "$DIST_DIR"
    mkdir -p "$PACKAGE_DIR"
    success "Distribution directory created: $PACKAGE_DIR"
}

# Copy core demo files
copy_core_files() {
    log "Copying core demo files..."
    
    # Backend core files
    mkdir -p "$PACKAGE_DIR/backend"
    
    # Essential backend files
    cp "$SCRIPT_DIR/start_demo.sh" "$PACKAGE_DIR/backend/"
    cp "$SCRIPT_DIR/stop_demo.sh" "$PACKAGE_DIR/backend/"
    cp "$SCRIPT_DIR/reset_demo.sh" "$PACKAGE_DIR/backend/"
    cp "$SCRIPT_DIR/requirements_demo.txt" "$PACKAGE_DIR/backend/"
    cp "$SCRIPT_DIR/Dockerfile.demo" "$PACKAGE_DIR/backend/"
    cp "$SCRIPT_DIR/docker-compose.yml" "$PACKAGE_DIR/backend/"
    cp "$SCRIPT_DIR/minimal_working_demo.py" "$PACKAGE_DIR/backend/"
    cp "$SCRIPT_DIR/ml_simulation_demo.py" "$PACKAGE_DIR/backend/"
    cp "$SCRIPT_DIR/working_demo.py" "$PACKAGE_DIR/backend/"
    
    # Demo data
    if [ -d "$SCRIPT_DIR/demo_data" ]; then
        cp -r "$SCRIPT_DIR/demo_data" "$PACKAGE_DIR/backend/"
    fi
    
    # Configuration files
    if [ -f "$SCRIPT_DIR/env.template" ]; then
        cp "$SCRIPT_DIR/env.template" "$PACKAGE_DIR/backend/.env.example"
    fi
    
    # Application code (selective)
    mkdir -p "$PACKAGE_DIR/backend/app"
    cp -r "$SCRIPT_DIR/app/main.py" "$PACKAGE_DIR/backend/app/" 2>/dev/null || true
    cp -r "$SCRIPT_DIR/app/minimal_main.py" "$PACKAGE_DIR/backend/app/" 2>/dev/null || true
    cp -r "$SCRIPT_DIR/app/core" "$PACKAGE_DIR/backend/app/" 2>/dev/null || true
    cp -r "$SCRIPT_DIR/app/database" "$PACKAGE_DIR/backend/app/" 2>/dev/null || true
    cp -r "$SCRIPT_DIR/app/models" "$PACKAGE_DIR/backend/app/" 2>/dev/null || true
    cp -r "$SCRIPT_DIR/app/schemas" "$PACKAGE_DIR/backend/app/" 2>/dev/null || true
    cp -r "$SCRIPT_DIR/app/simulations" "$PACKAGE_DIR/backend/app/" 2>/dev/null || true
    
    # Frontend demo files
    if [ -d "$PROJECT_ROOT/frontend" ]; then
        mkdir -p "$PACKAGE_DIR/frontend"
        cp -r "$PROJECT_ROOT/frontend/src/app/demo" "$PACKAGE_DIR/frontend/src/app/" 2>/dev/null || true
        cp -r "$PROJECT_ROOT/frontend/src/components/demo" "$PACKAGE_DIR/frontend/src/components/" 2>/dev/null || true
        cp "$PROJECT_ROOT/frontend/package.json" "$PACKAGE_DIR/frontend/" 2>/dev/null || true
        cp "$PROJECT_ROOT/frontend/Dockerfile.demo" "$PACKAGE_DIR/frontend/" 2>/dev/null || true
    fi
    
    # Scripts
    mkdir -p "$PACKAGE_DIR/scripts"
    cp -r "$SCRIPT_DIR/scripts/seed_demo_data.py" "$PACKAGE_DIR/scripts/" 2>/dev/null || true
    cp -r "$SCRIPT_DIR/scripts/health_check.py" "$PACKAGE_DIR/scripts/" 2>/dev/null || true
    
    success "Core files copied successfully"
}

# Copy documentation
copy_documentation() {
    log "Copying documentation..."
    
    mkdir -p "$PACKAGE_DIR/docs"
    
    # Demo-specific documentation
    cp "$SCRIPT_DIR/DEMO_DEPLOYMENT.md" "$PACKAGE_DIR/docs/" 2>/dev/null || true
    cp "$SCRIPT_DIR/CLI_DEMO_GUIDE.md" "$PACKAGE_DIR/docs/" 2>/dev/null || true
    cp "$SCRIPT_DIR/DATABASE_SETUP_GUIDE.md" "$PACKAGE_DIR/docs/" 2>/dev/null || true
    cp "$SCRIPT_DIR/DEMO_USAGE_GUIDE.md" "$PACKAGE_DIR/docs/" 2>/dev/null || true
    cp "$SCRIPT_DIR/README_DEMO.md" "$PACKAGE_DIR/docs/" 2>/dev/null || true
    cp "$SCRIPT_DIR/README_ML_DEMO.md" "$PACKAGE_DIR/docs/" 2>/dev/null || true
    
    # API documentation
    if [ -d "$SCRIPT_DIR/docs" ]; then
        cp "$SCRIPT_DIR/docs/QUICKSTART.md" "$PACKAGE_DIR/docs/" 2>/dev/null || true
        cp "$SCRIPT_DIR/docs/openapi_specification.json" "$PACKAGE_DIR/docs/" 2>/dev/null || true
    fi
    
    success "Documentation copied successfully"
}

# Create launcher scripts
create_launchers() {
    log "Creating launcher scripts..."
    
    # Main demo launcher
    cat > "$PACKAGE_DIR/start_demo.sh" << 'EOF'
#!/bin/bash

# Financial Planning Demo Launcher
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Starting Financial Planning Demo..."
echo "=================================="

# Check for Docker
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed. Please install Docker first."
    exit 1
fi

# Check for Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "Error: Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Start backend demo
cd "$SCRIPT_DIR/backend"
if [ -f "start_demo.sh" ]; then
    echo "Starting backend demo..."
    chmod +x start_demo.sh
    ./start_demo.sh
else
    echo "Starting demo with Docker Compose..."
    docker-compose up -d
fi

echo ""
echo "Demo started successfully!"
echo "Access the demo at: http://localhost:8000"
echo "API documentation: http://localhost:8000/docs"
echo ""
echo "To stop the demo, run: ./stop_demo.sh"
EOF

    # Stop script
    cat > "$PACKAGE_DIR/stop_demo.sh" << 'EOF'
#!/bin/bash

# Financial Planning Demo Stopper
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Stopping Financial Planning Demo..."
echo "=================================="

cd "$SCRIPT_DIR/backend"
if [ -f "stop_demo.sh" ]; then
    chmod +x stop_demo.sh
    ./stop_demo.sh
else
    docker-compose down
fi

echo "Demo stopped successfully!"
EOF

    chmod +x "$PACKAGE_DIR/start_demo.sh"
    chmod +x "$PACKAGE_DIR/stop_demo.sh"
    
    success "Launcher scripts created"
}

# Remove unnecessary files
cleanup_package() {
    log "Cleaning up unnecessary files..."
    
    # Remove development files
    find "$PACKAGE_DIR" -name "*.pyc" -delete 2>/dev/null || true
    find "$PACKAGE_DIR" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
    find "$PACKAGE_DIR" -name ".pytest_cache" -type d -exec rm -rf {} + 2>/dev/null || true
    find "$PACKAGE_DIR" -name "*.log" -delete 2>/dev/null || true
    find "$PACKAGE_DIR" -name ".DS_Store" -delete 2>/dev/null || true
    find "$PACKAGE_DIR" -name "Thumbs.db" -delete 2>/dev/null || true
    
    # Remove sensitive files
    find "$PACKAGE_DIR" -name "*.key" -delete 2>/dev/null || true
    find "$PACKAGE_DIR" -name "*.pem" -delete 2>/dev/null || true
    find "$PACKAGE_DIR" -name ".env" -delete 2>/dev/null || true
    
    success "Package cleaned up"
}

# Generate manifest
generate_manifest() {
    log "Generating package manifest..."
    
    cat > "$PACKAGE_DIR/MANIFEST.txt" << EOF
Financial Planning Demo Package
================================

Package: $PACKAGE_NAME
Version: $VERSION
Build ID: $BUILD_ID
Build Date: $(date)
Platform: $(uname -s) $(uname -m)

Contents:
---------
EOF

    # List all files in the package
    find "$PACKAGE_DIR" -type f -not -name "MANIFEST.txt" | \
        sed "s|$PACKAGE_DIR/||" | \
        sort >> "$PACKAGE_DIR/MANIFEST.txt"
    
    success "Manifest generated"
}

# Generate checksums
generate_checksums() {
    log "Generating checksums..."
    
    cd "$PACKAGE_DIR"
    
    # Generate SHA256 checksums for all files
    find . -type f -not -name "CHECKSUMS.sha256" -exec sha256sum {} \; | \
        sort > CHECKSUMS.sha256
    
    success "Checksums generated"
}

# Create version info
create_version_info() {
    log "Creating version information..."
    
    cat > "$PACKAGE_DIR/VERSION_INFO.json" << EOF
{
  "package": "$PACKAGE_NAME",
  "version": "$VERSION",
  "buildId": "$BUILD_ID",
  "buildDate": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "buildHost": "$(hostname)",
  "gitCommit": "$(cd "$PROJECT_ROOT" && git rev-parse HEAD 2>/dev/null || echo 'unknown')",
  "gitBranch": "$(cd "$PROJECT_ROOT" && git rev-parse --abbrev-ref HEAD 2>/dev/null || echo 'unknown')",
  "platform": {
    "os": "$(uname -s)",
    "arch": "$(uname -m)",
    "kernel": "$(uname -r)"
  },
  "dependencies": {
    "docker": "$(docker --version 2>/dev/null || echo 'not installed')",
    "python": "$(python3 --version 2>/dev/null || echo 'not installed')",
    "node": "$(node --version 2>/dev/null || echo 'not installed')"
  }
}
EOF

    success "Version information created"
}

# Create archives
create_archives() {
    log "Creating distribution archives..."
    
    cd "$DIST_DIR"
    
    # Create ZIP archive
    zip -r "${PACKAGE_NAME}-${BUILD_ID}.zip" "$(basename "$PACKAGE_DIR")" > /dev/null
    success "ZIP archive created: ${PACKAGE_NAME}-${BUILD_ID}.zip"
    
    # Create TAR.GZ archive
    tar -czf "${PACKAGE_NAME}-${BUILD_ID}.tar.gz" "$(basename "$PACKAGE_DIR")"
    success "TAR.GZ archive created: ${PACKAGE_NAME}-${BUILD_ID}.tar.gz"
    
    # Generate archive checksums
    sha256sum *.zip *.tar.gz > "${PACKAGE_NAME}-${BUILD_ID}-checksums.sha256"
    success "Archive checksums generated"
}

# Create Docker image
create_docker_image() {
    log "Creating Docker image..."
    
    if command -v docker &> /dev/null; then
        cd "$PACKAGE_DIR"
        
        # Create Dockerfile for the complete demo
        cat > Dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy backend files
COPY backend/ ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements_demo.txt

# Expose port
EXPOSE 8000

# Start the demo
CMD ["python", "minimal_working_demo.py"]
EOF

        # Build Docker image
        docker build -t "${PACKAGE_NAME}:${BUILD_ID}" . > /dev/null 2>&1 || {
            warning "Docker image build failed - continuing without Docker image"
            return 0
        }
        
        # Save Docker image
        docker save "${PACKAGE_NAME}:${BUILD_ID}" | gzip > "../${PACKAGE_NAME}-${BUILD_ID}-docker.tar.gz"
        success "Docker image created: ${PACKAGE_NAME}-${BUILD_ID}-docker.tar.gz"
        
        # Clean up
        rm Dockerfile
    else
        warning "Docker not available - skipping Docker image creation"
    fi
}

# Create installer script
create_installer() {
    log "Creating installer script..."
    
    cat > "$DIST_DIR/install_demo.sh" << 'EOF'
#!/bin/bash

# Financial Planning Demo Installer
set -euo pipefail

PACKAGE_NAME="financial-planning-demo"
INSTALL_DIR="$HOME/financial-planning-demo"

echo "Financial Planning Demo Installer"
echo "=================================="

# Check system requirements
check_requirements() {
    echo "Checking system requirements..."
    
    # Check for Python
    if ! command -v python3 &> /dev/null; then
        echo "Error: Python 3 is required but not installed."
        echo "Please install Python 3.8 or later."
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    if python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"; then
        echo "Python $PYTHON_VERSION found ✓"
    else
        echo "Error: Python 3.8 or later is required. Found: $PYTHON_VERSION"
        exit 1
    fi
    
    # Check for pip
    if ! command -v pip3 &> /dev/null; then
        echo "Error: pip3 is required but not installed."
        exit 1
    fi
    echo "pip3 found ✓"
    
    # Check for Docker (optional)
    if command -v docker &> /dev/null; then
        echo "Docker found ✓"
    else
        echo "Docker not found - will use Python installation"
    fi
}

# Extract package
extract_package() {
    echo "Extracting demo package..."
    
    # Find the package archive in the current directory
    ARCHIVE=""
    for ext in tar.gz zip; do
        if ls ${PACKAGE_NAME}-*.$ext 1> /dev/null 2>&1; then
            ARCHIVE=$(ls ${PACKAGE_NAME}-*.$ext | head -1)
            break
        fi
    done
    
    if [ -z "$ARCHIVE" ]; then
        echo "Error: No demo package archive found."
        echo "Please ensure the demo package is in the current directory."
        exit 1
    fi
    
    echo "Found package: $ARCHIVE"
    
    # Create installation directory
    mkdir -p "$INSTALL_DIR"
    
    # Extract archive
    if [[ "$ARCHIVE" == *.tar.gz ]]; then
        tar -xzf "$ARCHIVE" -C "$INSTALL_DIR" --strip-components=1
    elif [[ "$ARCHIVE" == *.zip ]]; then
        unzip -q "$ARCHIVE" -d /tmp/
        mv /tmp/${PACKAGE_NAME}-*/* "$INSTALL_DIR/"
        rm -rf /tmp/${PACKAGE_NAME}-*
    fi
    
    echo "Package extracted to: $INSTALL_DIR"
}

# Install dependencies
install_dependencies() {
    echo "Installing dependencies..."
    
    cd "$INSTALL_DIR"
    
    if [ -f "backend/requirements_demo.txt" ]; then
        pip3 install -r backend/requirements_demo.txt
        echo "Dependencies installed ✓"
    else
        echo "Warning: requirements file not found"
    fi
}

# Setup demo
setup_demo() {
    echo "Setting up demo..."
    
    cd "$INSTALL_DIR"
    
    # Make scripts executable
    chmod +x start_demo.sh stop_demo.sh 2>/dev/null || true
    chmod +x backend/start_demo.sh backend/stop_demo.sh 2>/dev/null || true
    
    # Create environment file if template exists
    if [ -f "backend/.env.example" ]; then
        cp "backend/.env.example" "backend/.env"
        echo "Environment file created ✓"
    fi
    
    echo "Demo setup complete ✓"
}

# Main installation flow
main() {
    check_requirements
    extract_package
    install_dependencies
    setup_demo
    
    echo ""
    echo "Installation completed successfully!"
    echo ""
    echo "Demo installed to: $INSTALL_DIR"
    echo ""
    echo "To start the demo:"
    echo "  cd $INSTALL_DIR"
    echo "  ./start_demo.sh"
    echo ""
    echo "To stop the demo:"
    echo "  ./stop_demo.sh"
    echo ""
    echo "For more information, see the docs/ directory."
}

main "$@"
EOF

    chmod +x "$DIST_DIR/install_demo.sh"
    success "Installer script created"
}

# Generate summary report
generate_summary() {
    log "Generating packaging summary..."
    
    PACKAGE_SIZE=$(du -sh "$PACKAGE_DIR" | cut -f1)
    ARCHIVE_COUNT=$(ls "$DIST_DIR"/*.zip "$DIST_DIR"/*.tar.gz 2>/dev/null | wc -l)
    FILE_COUNT=$(find "$PACKAGE_DIR" -type f | wc -l)
    
    cat > "$DIST_DIR/PACKAGE_SUMMARY.txt" << EOF
Financial Planning Demo Package Summary
========================================

Package Information:
-------------------
Name: $PACKAGE_NAME
Version: $VERSION
Build ID: $BUILD_ID
Build Date: $(date)
Package Size: $PACKAGE_SIZE
File Count: $FILE_COUNT
Archive Count: $ARCHIVE_COUNT

Distribution Contents:
---------------------
$(ls -la "$DIST_DIR" | grep -v "^total" | awk '{print $9, $5}' | column -t)

Package Structure:
-----------------
$(tree "$PACKAGE_DIR" 2>/dev/null | head -50 || find "$PACKAGE_DIR" -type d | head -20)

Installation:
------------
1. Run: ./install_demo.sh
2. Follow the installation prompts
3. Start demo: ./start_demo.sh

Support:
-------
For support and documentation, see the docs/ directory in the package.

Generated: $(date)
EOF

    success "Package summary generated"
}

# Main execution flow
main() {
    echo -e "${BLUE}"
    echo "Financial Planning Demo Packaging System"
    echo "======================================="
    echo "Version: $VERSION"
    echo "Build ID: $BUILD_ID"
    echo -e "${NC}"
    
    create_dist_directory
    copy_core_files
    copy_documentation
    create_launchers
    cleanup_package
    generate_manifest
    generate_checksums
    create_version_info
    create_archives
    create_docker_image
    create_installer
    generate_summary
    
    echo ""
    success "Demo packaging completed successfully!"
    echo ""
    echo -e "${GREEN}Distribution created in: $DIST_DIR${NC}"
    echo -e "${GREEN}Package directory: $PACKAGE_DIR${NC}"
    echo ""
    echo "Available distributions:"
    ls -la "$DIST_DIR"/*.zip "$DIST_DIR"/*.tar.gz 2>/dev/null || true
    echo ""
    echo "To install the demo:"
    echo "1. Extract any archive to your desired location"
    echo "2. Run: ./install_demo.sh"
    echo "3. Start demo: ./start_demo.sh"
}

# Execute main function
main "$@"