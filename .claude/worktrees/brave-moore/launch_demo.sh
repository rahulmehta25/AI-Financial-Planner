#!/bin/bash

# ==============================================================================
# Financial Planning System - Unix Demo Launcher
# ==============================================================================
# 
# Professional shell script launcher for Unix systems (macOS, Linux)
# Provides easy access to all demos with dependency checking and error handling
#
# Usage:
#   ./launch_demo.sh                    # Interactive mode
#   ./launch_demo.sh backend-full       # Direct launch
#   ./launch_demo.sh --list             # List all demos
#   ./launch_demo.sh --help             # Show help
#
# Features:
#   - Automatic Python and dependency detection
#   - System requirements validation
#   - Professional progress indicators
#   - Error handling and cleanup
#   - Cross-platform compatibility
# ==============================================================================

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LAUNCHER_SCRIPT="demo_launcher.py"
MIN_PYTHON_VERSION="3.8"

# Colors for output
if [[ -t 1 ]] && command -v tput >/dev/null 2>&1; then
    RED=$(tput setaf 1)
    GREEN=$(tput setaf 2)
    YELLOW=$(tput setaf 3)
    BLUE=$(tput setaf 4)
    MAGENTA=$(tput setaf 5)
    CYAN=$(tput setaf 6)
    WHITE=$(tput setaf 7)
    BOLD=$(tput bold)
    RESET=$(tput sgr0)
else
    RED=""
    GREEN=""
    YELLOW=""
    BLUE=""
    MAGENTA=""
    CYAN=""
    WHITE=""
    BOLD=""
    RESET=""
fi

# ASCII Banner
print_banner() {
    echo "${CYAN}${BOLD}"
    echo "╔══════════════════════════════════════════════════════════════════════════════╗"
    echo "║                    🏦 FINANCIAL PLANNING SYSTEM 🏦                         ║"
    echo "║                         Unix Demo Launcher                                  ║"
    echo "║                                                                              ║"
    echo "║    💰 Advanced Monte Carlo Simulations                                      ║"
    echo "║    📊 Real-time Portfolio Analytics                                         ║"
    echo "║    🤖 AI-Powered Recommendations                                            ║"
    echo "║    📱 Multi-Platform Support                                                ║"
    echo "║    🔒 Enterprise Security                                                   ║"
    echo "╚══════════════════════════════════════════════════════════════════════════════╝"
    echo "${RESET}"
}

# Logging functions
log_info() {
    echo "${BLUE}[INFO]${RESET} $1"
}

log_success() {
    echo "${GREEN}[SUCCESS]${RESET} $1"
}

log_warning() {
    echo "${YELLOW}[WARNING]${RESET} $1"
}

log_error() {
    echo "${RED}[ERROR]${RESET} $1"
}

log_step() {
    echo "${CYAN}${BOLD}==> $1${RESET}"
}

# Progress spinner
show_spinner() {
    local pid=$1
    local message=$2
    local delay=0.1
    local spinner_chars="⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
    local temp_file=$(mktemp)
    
    echo -n "${message} "
    
    while kill -0 "$pid" 2>/dev/null; do
        for char in $(echo "$spinner_chars" | grep -o .); do
            printf "\r${message} ${CYAN}${char}${RESET}"
            sleep $delay
            if ! kill -0 "$pid" 2>/dev/null; then
                break 2
            fi
        done
    done
    
    wait "$pid"
    local exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        printf "\r${message} ${GREEN}✅${RESET}\n"
    else
        printf "\r${message} ${RED}❌${RESET}\n"
    fi
    
    return $exit_code
}

# Error handling
error_exit() {
    log_error "$1"
    log_error "Demo launcher failed. Please check the error message above."
    exit 1
}

# Cleanup function
cleanup() {
    if [ $? -ne 0 ]; then
        log_warning "Script interrupted. Performing cleanup..."
        # Kill any background processes if needed
        jobs -p | xargs -r kill 2>/dev/null || true
    fi
}
trap cleanup EXIT

# Check if script is run with sudo (not recommended)
check_sudo() {
    if [[ $EUID -eq 0 ]]; then
        log_warning "Running as root is not recommended for demos"
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

# Detect operating system
detect_os() {
    case "$(uname -s)" in
        Darwin)
            OS="macOS"
            DISTRO="macOS $(sw_vers -productVersion)"
            PACKAGE_MANAGER="brew"
            ;;
        Linux)
            OS="Linux"
            if [ -f /etc/os-release ]; then
                . /etc/os-release
                DISTRO="$NAME $VERSION"
            else
                DISTRO="Unknown Linux"
            fi
            
            if command -v apt-get >/dev/null 2>&1; then
                PACKAGE_MANAGER="apt"
            elif command -v yum >/dev/null 2>&1; then
                PACKAGE_MANAGER="yum"
            elif command -v dnf >/dev/null 2>&1; then
                PACKAGE_MANAGER="dnf"
            elif command -v pacman >/dev/null 2>&1; then
                PACKAGE_MANAGER="pacman"
            else
                PACKAGE_MANAGER="unknown"
            fi
            ;;
        CYGWIN*|MINGW*|MSYS*)
            OS="Windows"
            DISTRO="Windows (Cygwin/MSYS)"
            PACKAGE_MANAGER="unknown"
            ;;
        *)
            OS="Unknown"
            DISTRO="Unknown"
            PACKAGE_MANAGER="unknown"
            ;;
    esac
    
    log_success "Detected: $DISTRO"
}

# Check Python installation
check_python() {
    log_step "Checking Python Installation"
    
    # Try different Python commands
    local python_cmd=""
    for cmd in python3 python python3.11 python3.10 python3.9 python3.8; do
        if command -v "$cmd" >/dev/null 2>&1; then
            local version=$($cmd --version 2>&1 | grep -oE '[0-9]+\.[0-9]+' | head -1)
            if [ -n "$version" ]; then
                # Compare versions
                if printf '%s\n%s\n' "$MIN_PYTHON_VERSION" "$version" | sort -V | head -1 | grep -q "^$MIN_PYTHON_VERSION$"; then
                    python_cmd="$cmd"
                    log_success "Found Python $version at $(which $cmd)"
                    break
                else
                    log_warning "Found Python $version (minimum required: $MIN_PYTHON_VERSION)"
                fi
            fi
        fi
    done
    
    if [ -z "$python_cmd" ]; then
        log_error "Python $MIN_PYTHON_VERSION or higher is required but not found"
        
        case "$OS" in
            "macOS")
                echo "Install Python using:"
                echo "  brew install python"
                echo "  or download from https://python.org"
                ;;
            "Linux")
                case "$PACKAGE_MANAGER" in
                    "apt")
                        echo "Install Python using:"
                        echo "  sudo apt update && sudo apt install python3 python3-pip"
                        ;;
                    "yum")
                        echo "Install Python using:"
                        echo "  sudo yum install python3 python3-pip"
                        ;;
                    "dnf")
                        echo "Install Python using:"
                        echo "  sudo dnf install python3 python3-pip"
                        ;;
                    *)
                        echo "Please install Python 3.8+ using your system's package manager"
                        ;;
                esac
                ;;
        esac
        return 1
    fi
    
    export PYTHON_CMD="$python_cmd"
    return 0
}

# Check system dependencies
check_system_deps() {
    log_step "Checking System Dependencies"
    
    local missing_deps=()
    local optional_deps=()
    
    # Essential tools
    local essential=("git" "curl" "wget")
    for tool in "${essential[@]}"; do
        if ! command -v "$tool" >/dev/null 2>&1; then
            missing_deps+=("$tool")
        else
            log_success "$tool: $(which $tool)"
        fi
    done
    
    # Optional but recommended tools
    local optional=("docker" "node" "npm")
    for tool in "${optional[@]}"; do
        if ! command -v "$tool" >/dev/null 2>&1; then
            optional_deps+=("$tool")
        else
            local version=""
            case "$tool" in
                "docker")
                    version=$(docker --version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)
                    ;;
                "node")
                    version=$(node --version 2>/dev/null)
                    ;;
                "npm")
                    version=$(npm --version 2>/dev/null)
                    ;;
            esac
            log_success "$tool $version: $(which $tool)"
        fi
    done
    
    # Report missing dependencies
    if [ ${#missing_deps[@]} -gt 0 ]; then
        log_warning "Missing essential dependencies: ${missing_deps[*]}"
        
        case "$OS" in
            "macOS")
                if ! command -v brew >/dev/null 2>&1; then
                    echo "Install Homebrew first: https://brew.sh"
                fi
                echo "Install missing tools with: brew install ${missing_deps[*]}"
                ;;
            "Linux")
                case "$PACKAGE_MANAGER" in
                    "apt")
                        echo "Install with: sudo apt install ${missing_deps[*]}"
                        ;;
                    "yum")
                        echo "Install with: sudo yum install ${missing_deps[*]}"
                        ;;
                    "dnf")
                        echo "Install with: sudo dnf install ${missing_deps[*]}"
                        ;;
                    *)
                        echo "Please install these tools using your system's package manager"
                        ;;
                esac
                ;;
        esac
        
        read -p "Continue without these tools? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            return 1
        fi
    fi
    
    if [ ${#optional_deps[@]} -gt 0 ]; then
        log_warning "Optional tools not found: ${optional_deps[*]}"
        echo "Some demos may not be available without these tools."
    fi
    
    return 0
}

# Check if demo launcher exists
check_launcher() {
    log_step "Checking Demo Launcher"
    
    if [ ! -f "$SCRIPT_DIR/$LAUNCHER_SCRIPT" ]; then
        error_exit "Demo launcher script not found: $LAUNCHER_SCRIPT"
    fi
    
    log_success "Demo launcher found: $LAUNCHER_SCRIPT"
    return 0
}

# Install Python dependencies if needed
install_python_deps() {
    log_step "Checking Python Dependencies"
    
    # Check if pip is available
    if ! $PYTHON_CMD -m pip --version >/dev/null 2>&1; then
        log_warning "pip not found, attempting to install..."
        
        # Try to install pip
        case "$OS" in
            "macOS")
                if command -v brew >/dev/null 2>&1; then
                    brew install python3
                else
                    error_exit "Please install pip manually or use Homebrew"
                fi
                ;;
            "Linux")
                case "$PACKAGE_MANAGER" in
                    "apt")
                        sudo apt update && sudo apt install python3-pip
                        ;;
                    "yum")
                        sudo yum install python3-pip
                        ;;
                    "dnf")
                        sudo dnf install python3-pip
                        ;;
                    *)
                        error_exit "Please install pip manually"
                        ;;
                esac
                ;;
            *)
                error_exit "Please install pip manually"
                ;;
        esac
    fi
    
    # Check for essential Python packages
    local required_packages=("fastapi" "uvicorn" "numpy" "pydantic")
    local missing_packages=()
    
    for package in "${required_packages[@]}"; do
        if ! $PYTHON_CMD -c "import $package" >/dev/null 2>&1; then
            missing_packages+=("$package")
        fi
    done
    
    if [ ${#missing_packages[@]} -gt 0 ]; then
        log_warning "Missing Python packages: ${missing_packages[*]}"
        
        read -p "Install missing packages now? (Y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Nn]$ ]]; then
            log_info "Installing Python packages..."
            
            # Install in background with spinner
            (
                $PYTHON_CMD -m pip install --user --upgrade pip
                $PYTHON_CMD -m pip install --user "${missing_packages[@]}"
            ) &
            
            show_spinner $! "Installing Python packages"
            
            if [ $? -ne 0 ]; then
                error_exit "Failed to install Python packages"
            fi
        fi
    else
        log_success "All essential Python packages are available"
    fi
    
    return 0
}

# Check disk space
check_disk_space() {
    local required_space_mb=2048  # 2GB minimum
    
    case "$OS" in
        "macOS"|"Linux")
            local available_space=$(df "$SCRIPT_DIR" | tail -1 | awk '{print $4}')
            # Convert KB to MB
            available_space=$((available_space / 1024))
            
            if [ "$available_space" -lt "$required_space_mb" ]; then
                log_warning "Low disk space: ${available_space}MB available (${required_space_mb}MB recommended)"
                read -p "Continue anyway? (y/N): " -n 1 -r
                echo
                if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                    return 1
                fi
            else
                log_success "Disk space: ${available_space}MB available"
            fi
            ;;
    esac
    
    return 0
}

# Check memory
check_memory() {
    local required_memory_mb=4096  # 4GB minimum
    
    case "$OS" in
        "macOS")
            local total_memory_bytes=$(sysctl -n hw.memsize)
            local total_memory_mb=$((total_memory_bytes / 1024 / 1024))
            ;;
        "Linux")
            local total_memory_kb=$(grep MemTotal /proc/meminfo | awk '{print $2}')
            local total_memory_mb=$((total_memory_kb / 1024))
            ;;
        *)
            # Skip memory check for unknown systems
            return 0
            ;;
    esac
    
    if [ "$total_memory_mb" -lt "$required_memory_mb" ]; then
        log_warning "Low memory: ${total_memory_mb}MB total (${required_memory_mb}MB recommended)"
        echo "Some demos may run slowly or fail."
    else
        log_success "Memory: ${total_memory_mb}MB total"
    fi
    
    return 0
}

# Show help
show_help() {
    print_banner
    echo "${BOLD}Financial Planning System - Unix Demo Launcher${RESET}"
    echo
    echo "Usage:"
    echo "  $0 [DEMO_ID]               Launch specific demo"
    echo "  $0 --list                  List all available demos"
    echo "  $0 --check                 Run system requirements check only"
    echo "  $0 --help                  Show this help message"
    echo
    echo "Examples:"
    echo "  $0                         # Interactive mode"
    echo "  $0 backend-full            # Launch full backend demo"
    echo "  $0 frontend                # Launch frontend demo"
    echo "  $0 --list                  # List all demos"
    echo
    echo "Demo Categories:"
    echo "  • Backend Services         - FastAPI servers with ML simulations"
    echo "  • Frontend Applications    - React/Next.js web applications"
    echo "  • Mobile Applications      - React Native mobile apps"
    echo "  • Infrastructure & DevOps  - Docker, Kubernetes deployments"
    echo "  • Security Demonstrations - Authentication, encryption demos"
    echo "  • Data Pipeline & Analytics- ETL processes and data analysis"
    echo "  • Machine Learning & AI    - ML models and recommendations"
    echo "  • End-to-End Integration   - Complete system tests"
    echo
    echo "System Requirements:"
    echo "  • Python 3.8 or higher"
    echo "  • 4GB+ RAM recommended"
    echo "  • 2GB+ disk space"
    echo "  • Git, curl (essential)"
    echo "  • Docker, Node.js (optional, for some demos)"
    echo
    echo "For more information, visit the documentation or run in interactive mode."
}

# Main system check
run_system_check() {
    log_step "System Requirements Check"
    echo
    
    detect_os
    check_python || return 1
    check_system_deps || return 1
    check_disk_space || return 1
    check_memory
    check_launcher || return 1
    install_python_deps || return 1
    
    echo
    log_success "System check completed successfully!"
    return 0
}

# Launch Python demo launcher
launch_python_launcher() {
    local args=("$@")
    
    log_step "Launching Demo System"
    
    # Change to script directory
    cd "$SCRIPT_DIR" || error_exit "Could not change to script directory"
    
    # Launch the Python launcher with all arguments
    exec "$PYTHON_CMD" "$LAUNCHER_SCRIPT" "${args[@]}"
}

# Main function
main() {
    # Handle command line arguments
    case "${1:-}" in
        --help|-h)
            show_help
            exit 0
            ;;
        --check)
            print_banner
            run_system_check
            exit $?
            ;;
        *)
            print_banner
            
            # Don't run sudo check in interactive mode for better UX
            if [ $# -eq 0 ]; then
                check_sudo
            fi
            
            # Run system check
            if ! run_system_check; then
                error_exit "System requirements not met"
            fi
            
            echo
            log_step "Starting Demo Launcher"
            echo
            
            # Launch Python launcher with all arguments
            launch_python_launcher "$@"
            ;;
    esac
}

# Make sure we're not being sourced
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi