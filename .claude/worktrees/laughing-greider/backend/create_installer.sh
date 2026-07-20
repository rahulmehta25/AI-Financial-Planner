#!/bin/bash

# Financial Planning Demo - Advanced Installer Creator
# Creates a self-extracting installer with multiple distribution options
# Author: Financial Planning Team

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
VERSION=$(cat "$SCRIPT_DIR/VERSION" 2>/dev/null || echo "1.0.0")
BUILD_DATE=$(date +%Y%m%d)
DIST_DIR="$PROJECT_ROOT/dist"
INSTALLER_NAME="financial-planning-demo-installer-${VERSION}-${BUILD_DATE}"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() { echo -e "${BLUE}[$(date +'%H:%M:%S')] $1${NC}"; }
success() { echo -e "${GREEN}✓ $1${NC}"; }
warning() { echo -e "${YELLOW}⚠ $1${NC}"; }

# Create self-extracting installer
create_self_extracting_installer() {
    log "Creating self-extracting installer..."
    
    mkdir -p "$DIST_DIR"
    
    cat > "$DIST_DIR/${INSTALLER_NAME}.sh" << 'INSTALLER_EOF'
#!/bin/bash

# Financial Planning Demo - Self-Extracting Installer
# This installer contains the complete demo package

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m'

# Configuration
DEMO_NAME="Financial Planning Demo"
INSTALLER_VERSION="__INSTALLER_VERSION__"
PACKAGE_SIZE="__PACKAGE_SIZE__"
DEFAULT_INSTALL_DIR="$HOME/financial-planning-demo"

# Display functions
show_header() {
    clear
    echo -e "${BLUE}╭─────────────────────────────────────────╮${NC}"
    echo -e "${BLUE}│  ${BOLD}Financial Planning Demo Installer${NC}${BLUE}   │${NC}"
    echo -e "${BLUE}│  ${NC}Version: ${INSTALLER_VERSION}${BLUE}                     │${NC}"
    echo -e "${BLUE}╰─────────────────────────────────────────╯${NC}"
    echo ""
}

log() { echo -e "${BLUE}[$(date +'%H:%M:%S')] $1${NC}"; }
success() { echo -e "${GREEN}✓ $1${NC}"; }
warning() { echo -e "${YELLOW}⚠ $1${NC}"; }
error() { echo -e "${RED}✗ $1${NC}"; exit 1; }

# System requirements check
check_system_requirements() {
    log "Checking system requirements..."
    
    # Check OS
    case "$(uname -s)" in
        Linux*)   OS_NAME="Linux" ;;
        Darwin*)  OS_NAME="macOS" ;;
        CYGWIN*)  OS_NAME="Windows" ;;
        MINGW*)   OS_NAME="Windows" ;;
        *)        OS_NAME="Unknown" ;;
    esac
    
    if [[ "$OS_NAME" == "Unknown" ]]; then
        error "Unsupported operating system: $(uname -s)"
    fi
    success "Operating System: $OS_NAME"
    
    # Check Python
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
        if python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)" 2>/dev/null; then
            success "Python $PYTHON_VERSION found"
        else
            error "Python 3.8+ required. Found: $PYTHON_VERSION"
        fi
    else
        error "Python 3 not found. Please install Python 3.8 or later."
    fi
    
    # Check pip
    if command -v pip3 &> /dev/null; then
        success "pip3 found"
    else
        error "pip3 not found. Please install pip3."
    fi
    
    # Check available disk space
    AVAILABLE_SPACE=$(df -h . 2>/dev/null | awk 'NR==2 {print $4}' | sed 's/[^0-9]*//g')
    if [[ -n "$AVAILABLE_SPACE" ]] && [[ "$AVAILABLE_SPACE" -gt 1000 ]]; then
        success "Sufficient disk space available"
    else
        warning "May have insufficient disk space. At least 2GB recommended."
    fi
    
    # Check for optional components
    if command -v docker &> /dev/null; then
        success "Docker found (optional)"
        DOCKER_AVAILABLE=true
    else
        warning "Docker not found (optional for containerized deployment)"
        DOCKER_AVAILABLE=false
    fi
    
    if command -v git &> /dev/null; then
        success "Git found (optional)"
    else
        warning "Git not found (optional for version control)"
    fi
    
    echo ""
}

# Interactive installation prompts
get_installation_preferences() {
    echo -e "${BOLD}Installation Configuration${NC}"
    echo "────────────────────────────"
    
    # Installation directory
    echo -n "Installation directory [$DEFAULT_INSTALL_DIR]: "
    read -r INSTALL_DIR
    INSTALL_DIR=${INSTALL_DIR:-$DEFAULT_INSTALL_DIR}
    
    # Installation mode
    echo ""
    echo "Installation modes:"
    echo "1) Quick Install (Minimal setup, fastest)"
    echo "2) Standard Install (Recommended for most users)"
    echo "3) Full Install (Complete with all components)"
    echo -n "Select installation mode [2]: "
    read -r INSTALL_MODE
    INSTALL_MODE=${INSTALL_MODE:-2}
    
    case $INSTALL_MODE in
        1) INSTALL_TYPE="quick" ;;
        2) INSTALL_TYPE="standard" ;;
        3) INSTALL_TYPE="full" ;;
        *) INSTALL_TYPE="standard" ;;
    esac
    
    # Docker preference
    if $DOCKER_AVAILABLE; then
        echo ""
        echo -n "Use Docker for deployment? (y/N): "
        read -r USE_DOCKER
        USE_DOCKER=${USE_DOCKER:-n}
    else
        USE_DOCKER="n"
    fi
    
    # Auto-start preference
    echo -n "Auto-start demo after installation? (Y/n): "
    read -r AUTO_START
    AUTO_START=${AUTO_START:-y}
    
    echo ""
    echo -e "${BOLD}Installation Summary:${NC}"
    echo "─────────────────────"
    echo "Directory: $INSTALL_DIR"
    echo "Mode: $INSTALL_TYPE"
    echo "Docker: $([ "$USE_DOCKER" = "y" ] && echo "Yes" || echo "No")"
    echo "Auto-start: $([ "$AUTO_START" = "y" ] && echo "Yes" || echo "No")"
    echo ""
    echo -n "Proceed with installation? (Y/n): "
    read -r CONFIRM
    CONFIRM=${CONFIRM:-y}
    
    if [[ "$CONFIRM" != "y" && "$CONFIRM" != "Y" ]]; then
        echo "Installation cancelled."
        exit 0
    fi
    
    echo ""
}

# Extract embedded archive
extract_demo_package() {
    log "Extracting demo package..."
    
    # Create installation directory
    mkdir -p "$INSTALL_DIR"
    
    # Find the embedded archive marker
    ARCHIVE_MARKER="__ARCHIVE_BELOW__"
    ARCHIVE_LINE=$(awk "/$ARCHIVE_MARKER/{print NR + 1; exit}" "$0")
    
    if [[ -z "$ARCHIVE_LINE" ]]; then
        error "Archive not found in installer"
    fi
    
    # Extract the archive
    tail -n +$ARCHIVE_LINE "$0" | tar -xzf - -C "$INSTALL_DIR" --strip-components=1
    
    if [[ $? -eq 0 ]]; then
        success "Demo package extracted to: $INSTALL_DIR"
    else
        error "Failed to extract demo package"
    fi
}

# Install dependencies
install_dependencies() {
    log "Installing dependencies..."
    
    cd "$INSTALL_DIR"
    
    case $INSTALL_TYPE in
        "quick")
            pip3 install -r backend/requirements_minimal.txt 2>/dev/null || \
            pip3 install -r backend/requirements_demo.txt
            ;;
        "standard")
            pip3 install -r backend/requirements_demo.txt
            ;;
        "full")
            pip3 install -r backend/requirements.txt 2>/dev/null || \
            pip3 install -r backend/requirements_demo.txt
            ;;
    esac
    
    if [[ $? -eq 0 ]]; then
        success "Dependencies installed successfully"
    else
        warning "Some dependencies may have failed to install"
    fi
}

# Setup demo environment
setup_demo_environment() {
    log "Setting up demo environment..."
    
    cd "$INSTALL_DIR"
    
    # Make scripts executable
    find . -name "*.sh" -exec chmod +x {} \; 2>/dev/null
    
    # Setup environment file
    if [[ -f "backend/.env.example" ]]; then
        cp "backend/.env.example" "backend/.env"
        success "Environment configuration created"
    fi
    
    # Initialize database (if needed)
    if [[ -f "backend/reset_demo.sh" ]]; then
        cd backend
        ./reset_demo.sh >/dev/null 2>&1 || true
        cd ..
        success "Demo database initialized"
    fi
    
    # Set permissions
    chmod +x start_demo.sh stop_demo.sh 2>/dev/null || true
    
    success "Demo environment configured"
}

# Create desktop shortcuts (optional)
create_shortcuts() {
    if [[ "$OS_NAME" == "Linux" ]]; then
        DESKTOP_DIR="$HOME/Desktop"
        if [[ -d "$DESKTOP_DIR" ]]; then
            log "Creating desktop shortcut..."
            
            cat > "$DESKTOP_DIR/Financial Planning Demo.desktop" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Financial Planning Demo
Comment=Launch the Financial Planning Demo
Exec=$INSTALL_DIR/start_demo.sh
Icon=applications-office
Terminal=true
Categories=Office;Finance;
EOF
            
            chmod +x "$DESKTOP_DIR/Financial Planning Demo.desktop"
            success "Desktop shortcut created"
        fi
    fi
}

# Post-installation setup
post_installation_setup() {
    log "Running post-installation setup..."
    
    # Create startup script in user's bin (if exists)
    if [[ -d "$HOME/.local/bin" ]]; then
        cat > "$HOME/.local/bin/financial-planning-demo" << EOF
#!/bin/bash
cd "$INSTALL_DIR"
./start_demo.sh "\$@"
EOF
        chmod +x "$HOME/.local/bin/financial-planning-demo"
        success "Command-line launcher created: financial-planning-demo"
    fi
    
    # Add to shell profile (bash)
    if [[ -f "$HOME/.bashrc" ]] && ! grep -q "financial-planning-demo" "$HOME/.bashrc"; then
        echo "" >> "$HOME/.bashrc"
        echo "# Financial Planning Demo" >> "$HOME/.bashrc"
        echo "alias fpd='cd $INSTALL_DIR && ./start_demo.sh'" >> "$HOME/.bashrc"
        success "Shell alias 'fpd' added to .bashrc"
    fi
}

# Start demo if requested
start_demo() {
    if [[ "$AUTO_START" = "y" || "$AUTO_START" = "Y" ]]; then
        log "Starting demo..."
        
        cd "$INSTALL_DIR"
        
        if [[ "$USE_DOCKER" = "y" && -f "docker-compose.yml" ]]; then
            if command -v docker-compose &> /dev/null; then
                docker-compose up -d
                success "Demo started with Docker"
            else
                ./start_demo.sh &
                success "Demo started"
            fi
        else
            ./start_demo.sh &
            success "Demo started"
        fi
        
        echo ""
        echo -e "${BOLD}Demo Access Information:${NC}"
        echo "──────────────────────────"
        echo "Web Interface: http://localhost:8000"
        echo "API Documentation: http://localhost:8000/docs"
        echo "Health Check: http://localhost:8000/health"
        echo ""
        echo "To stop the demo: cd $INSTALL_DIR && ./stop_demo.sh"
        
        # Wait a moment and check if demo started
        sleep 3
        if curl -s http://localhost:8000/health >/dev/null 2>&1; then
            success "Demo is running and accessible!"
        else
            warning "Demo may still be starting up. Please wait a moment and try accessing the URLs above."
        fi
    fi
}

# Installation complete message
show_completion_message() {
    echo ""
    echo -e "${GREEN}╭─────────────────────────────────────────╮${NC}"
    echo -e "${GREEN}│  ${BOLD}Installation Completed Successfully!${NC}${GREEN}    │${NC}"
    echo -e "${GREEN}╰─────────────────────────────────────────╯${NC}"
    echo ""
    echo -e "${BOLD}Installation Details:${NC}"
    echo "───────────────────"
    echo "Location: $INSTALL_DIR"
    echo "Type: $INSTALL_TYPE installation"
    echo "Package size: $PACKAGE_SIZE"
    echo ""
    echo -e "${BOLD}Quick Start Commands:${NC}"
    echo "────────────────────"
    echo "Start demo:  cd $INSTALL_DIR && ./start_demo.sh"
    echo "Stop demo:   cd $INSTALL_DIR && ./stop_demo.sh"
    echo "Reset demo:  cd $INSTALL_DIR/backend && ./reset_demo.sh"
    echo ""
    if [[ -f "$HOME/.local/bin/financial-planning-demo" ]]; then
        echo "Global command: financial-planning-demo"
    fi
    if grep -q "alias fpd=" "$HOME/.bashrc" 2>/dev/null; then
        echo "Shell alias: fpd (restart shell to use)"
    fi
    echo ""
    echo -e "${BOLD}Documentation:${NC}"
    echo "─────────────"
    echo "Complete guide: $INSTALL_DIR/DEMO_PACKAGE_README.md"
    echo "Quick start: $INSTALL_DIR/docs/QUICKSTART.md"
    echo "API docs: http://localhost:8000/docs (when running)"
    echo ""
    echo -e "${BOLD}Support:${NC}"
    echo "───────"
    echo "Troubleshooting: See DEMO_PACKAGE_README.md"
    echo "Health check: http://localhost:8000/health"
    echo "Log files: $INSTALL_DIR/backend/logs/"
    echo ""
}

# Cleanup function
cleanup() {
    # Clean up any temporary files
    rm -f /tmp/fp_demo_* 2>/dev/null || true
}

# Main installation flow
main() {
    trap cleanup EXIT
    
    show_header
    check_system_requirements
    get_installation_preferences
    
    echo -e "${BOLD}Starting Installation...${NC}"
    echo "════════════════════════════"
    
    extract_demo_package
    install_dependencies
    setup_demo_environment
    create_shortcuts
    post_installation_setup
    start_demo
    show_completion_message
    
    echo -e "${GREEN}Thank you for installing Financial Planning Demo!${NC}"
}

# Run main installation if not sourced
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi

# Exit before the embedded archive
exit 0

__ARCHIVE_BELOW__
INSTALLER_EOF

    # Replace placeholders
    sed -i.bak "s/__INSTALLER_VERSION__/$VERSION-$BUILD_DATE/g" "$DIST_DIR/${INSTALLER_NAME}.sh"
    
    # Calculate package size (will be updated after embedding)
    echo "TBD" > /tmp/package_size_placeholder
    sed -i.bak "s/__PACKAGE_SIZE__/TBD/g" "$DIST_DIR/${INSTALLER_NAME}.sh"
    
    rm "$DIST_DIR/${INSTALLER_NAME}.sh.bak"
    
    success "Self-extracting installer shell created"
}

# Embed the package archive
embed_package_archive() {
    log "Embedding package archive in installer..."
    
    # Check if we have a package to embed
    PACKAGE_ARCHIVE=""
    for archive in "$DIST_DIR"/*.tar.gz; do
        if [[ -f "$archive" && "$archive" != *"docker"* && "$archive" != *"installer"* ]]; then
            PACKAGE_ARCHIVE="$archive"
            break
        fi
    done
    
    if [[ -z "$PACKAGE_ARCHIVE" ]]; then
        error "No package archive found. Run package_demo.sh first."
    fi
    
    # Get package size
    PACKAGE_SIZE=$(du -h "$PACKAGE_ARCHIVE" | cut -f1)
    
    # Update size in installer
    sed -i.bak "s/TBD/$PACKAGE_SIZE/g" "$DIST_DIR/${INSTALLER_NAME}.sh"
    rm "$DIST_DIR/${INSTALLER_NAME}.sh.bak"
    
    # Append the archive to the installer
    cat "$PACKAGE_ARCHIVE" >> "$DIST_DIR/${INSTALLER_NAME}.sh"
    
    # Make installer executable
    chmod +x "$DIST_DIR/${INSTALLER_NAME}.sh"
    
    # Get final installer size
    INSTALLER_SIZE=$(du -h "$DIST_DIR/${INSTALLER_NAME}.sh" | cut -f1)
    
    success "Package embedded. Installer size: $INSTALLER_SIZE"
}

# Create Windows installer
create_windows_installer() {
    log "Creating Windows installer stub..."
    
    cat > "$DIST_DIR/${INSTALLER_NAME}.bat" << 'BATCH_EOF'
@echo off
REM Financial Planning Demo - Windows Installer
REM This requires Windows Subsystem for Linux (WSL2)

echo Financial Planning Demo - Windows Installation
echo ===============================================
echo.

REM Check for WSL
wsl --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Windows Subsystem for Linux (WSL2) is required
    echo Please install WSL2 from Microsoft Store and try again
    echo.
    echo Installation instructions:
    echo https://docs.microsoft.com/en-us/windows/wsl/install
    pause
    exit /b 1
)

echo WSL2 detected. Launching installer in WSL environment...
echo.

REM Find the Linux installer
set "LINUX_INSTALLER=%~dp0financial-planning-demo-installer-__VERSION__.sh"

if not exist "%LINUX_INSTALLER%" (
    echo ERROR: Linux installer not found
    echo Please ensure both .bat and .sh files are in the same directory
    pause
    exit /b 1
)

REM Launch in WSL
wsl bash -c "chmod +x '%LINUX_INSTALLER%' && '%LINUX_INSTALLER%'"

if errorlevel 1 (
    echo.
    echo Installation may have encountered issues.
    echo Check the output above for details.
) else (
    echo.
    echo Installation completed successfully!
    echo.
    echo To start the demo:
    echo wsl bash -c "cd ~/financial-planning-demo && ./start_demo.sh"
)

echo.
pause
BATCH_EOF

    # Replace version placeholder
    sed -i.bak "s/__VERSION__/$VERSION-$BUILD_DATE/g" "$DIST_DIR/${INSTALLER_NAME}.bat"
    rm "$DIST_DIR/${INSTALLER_NAME}.bat.bak"
    
    success "Windows installer created"
}

# Create macOS installer
create_macos_installer() {
    log "Creating macOS installer application..."
    
    local APP_NAME="Financial Planning Demo Installer"
    local APP_DIR="$DIST_DIR/$APP_NAME.app"
    
    mkdir -p "$APP_DIR/Contents/MacOS"
    mkdir -p "$APP_DIR/Contents/Resources"
    
    # Create Info.plist
    cat > "$APP_DIR/Contents/Info.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>installer</string>
    <key>CFBundleIdentifier</key>
    <string>com.financialplanning.demo.installer</string>
    <key>CFBundleName</key>
    <string>Financial Planning Demo Installer</string>
    <key>CFBundleVersion</key>
    <string>$VERSION</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>$VERSION</string>
</dict>
</plist>
EOF

    # Create launcher script
    cat > "$APP_DIR/Contents/MacOS/installer" << 'MACOS_EOF'
#!/bin/bash

# Financial Planning Demo - macOS Installer Launcher
cd "$(dirname "$0")/../.."

# Find the installer
INSTALLER_SCRIPT=""
for file in *.sh; do
    if [[ "$file" == *"installer"* ]]; then
        INSTALLER_SCRIPT="$file"
        break
    fi
done

if [[ -z "$INSTALLER_SCRIPT" ]]; then
    osascript -e 'display alert "Error" message "Installer script not found. Please ensure all files are present." buttons {"OK"} default button "OK"'
    exit 1
fi

# Launch Terminal with installer
osascript -e "tell application \"Terminal\" to do script \"cd '$PWD' && chmod +x '$INSTALLER_SCRIPT' && ./'$INSTALLER_SCRIPT'\""
MACOS_EOF

    chmod +x "$APP_DIR/Contents/MacOS/installer"
    
    success "macOS installer application created"
}

# Generate installer documentation
create_installer_documentation() {
    log "Creating installer documentation..."
    
    cat > "$DIST_DIR/INSTALLER_README.md" << 'DOC_EOF'
# Financial Planning Demo - Installation Guide

## Available Installers

### Cross-Platform (Recommended)
- **`financial-planning-demo-installer-*.sh`** - Self-extracting installer for Linux and macOS
- Works on any Unix-like system with bash support
- Includes interactive installation wizard

### Platform-Specific
- **`financial-planning-demo-installer-*.bat`** - Windows installer (requires WSL2)
- **`Financial Planning Demo Installer.app`** - macOS application bundle

## Quick Installation

### Linux/macOS
```bash
chmod +x financial-planning-demo-installer-*.sh
./financial-planning-demo-installer-*.sh
```

### Windows
1. Ensure WSL2 is installed
2. Double-click `financial-planning-demo-installer-*.bat`
3. Follow the prompts

### macOS (Application)
1. Double-click `Financial Planning Demo Installer.app`
2. Allow Terminal access if prompted
3. Follow the installation wizard

## Installation Options

### Installation Modes
1. **Quick Install**: Minimal setup, fastest installation
2. **Standard Install**: Recommended for most users
3. **Full Install**: Complete with all development components

### Deployment Options
- **Native Python**: Direct installation with pip
- **Docker**: Containerized deployment (requires Docker)

## Post-Installation

### Starting the Demo
```bash
cd ~/financial-planning-demo
./start_demo.sh
```

### Accessing the Demo
- **Web Interface**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

### Stopping the Demo
```bash
cd ~/financial-planning-demo
./stop_demo.sh
```

## Troubleshooting

### Common Issues
1. **Permission Denied**: Run `chmod +x installer-script.sh`
2. **Python Not Found**: Install Python 3.8+ first
3. **Port 8000 Busy**: Kill existing processes or use different port

### Getting Help
- Check the complete documentation in `DEMO_PACKAGE_README.md` after installation
- Review installation logs for specific error messages
- Verify system requirements are met

## System Requirements

### Minimum
- Linux, macOS, or Windows 10+ with WSL2
- Python 3.8+
- 4GB RAM
- 2GB disk space

### Recommended
- Python 3.11+
- 8GB+ RAM
- 4+ CPU cores
- Docker (optional)

## Support

This installer provides:
- Interactive installation wizard
- Automatic dependency management
- Environment setup and configuration
- Desktop shortcuts and command aliases
- Post-installation health checks

For issues specific to the installer, check the installation logs and system compatibility.
DOC_EOF

    success "Installer documentation created"
}

# Main execution
main() {
    echo -e "${BLUE}"
    echo "Financial Planning Demo - Installer Creator"
    echo "==========================================="
    echo "Version: $VERSION"
    echo "Build Date: $BUILD_DATE"
    echo -e "${NC}"
    
    # Check if package exists
    if [[ ! -d "$DIST_DIR" ]] || [[ -z "$(ls "$DIST_DIR"/*.tar.gz 2>/dev/null)" ]]; then
        warning "No package found. Running package_demo.sh first..."
        bash "$SCRIPT_DIR/package_demo.sh"
    fi
    
    create_self_extracting_installer
    embed_package_archive
    create_windows_installer
    create_macos_installer
    create_installer_documentation
    
    # Generate final summary
    echo ""
    success "Installer creation completed!"
    echo ""
    echo -e "${GREEN}Available installers:${NC}"
    ls -la "$DIST_DIR"/*installer* "$DIST_DIR"/*.app 2>/dev/null || true
    echo ""
    echo -e "${GREEN}Installation Instructions:${NC}"
    echo "Linux/macOS: chmod +x ${INSTALLER_NAME}.sh && ./${INSTALLER_NAME}.sh"
    echo "Windows:     Double-click ${INSTALLER_NAME}.bat"
    echo "macOS App:   Double-click 'Financial Planning Demo Installer.app'"
    echo ""
    echo -e "${BLUE}Installers are ready for distribution!${NC}"
}

# Run main function
main "$@"