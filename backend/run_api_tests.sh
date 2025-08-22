#!/bin/bash

# 🚀 Financial Planning API Test Suite Launcher
# ==============================================
# 
# This script provides easy ways to run the API test suite with different configurations.
# 
# Usage:
#   ./run_api_tests.sh                    # Basic test suite
#   ./run_api_tests.sh --load-test        # Include load testing
#   ./run_api_tests.sh --help            # Show help
#

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# Default configuration
BASE_URL="http://localhost:8000"
LOAD_TEST=false
VERBOSE=false

# Function to print colored output
print_color() {
    local color=$1
    shift
    echo -e "${color}$*${NC}"
}

print_header() {
    echo
    print_color $PURPLE "======================================================"
    print_color $CYAN "🚀 Financial Planning API Test Suite Launcher"
    print_color $PURPLE "======================================================"
    echo
}

print_help() {
    print_header
    cat << EOF
Usage: $0 [OPTIONS]

OPTIONS:
  --base-url URL     Set the base URL for API testing (default: http://localhost:8000)
  --load-test        Include load testing with 100 concurrent requests
  --verbose          Enable verbose output
  --install-deps     Install required test dependencies
  --help, -h         Show this help message

EXAMPLES:
  $0                                    # Run basic test suite
  $0 --load-test                       # Run with load testing
  $0 --base-url http://localhost:3000  # Test different URL
  $0 --verbose --load-test             # Verbose output with load testing
  $0 --install-deps                    # Install dependencies only

ENVIRONMENT:
  The test suite will generate:
  - Colorful console output with test results
  - HTML report (api_test_report.html)
  - Performance statistics
  - Error analysis

EOF
}

install_dependencies() {
    print_color $YELLOW "📦 Installing test dependencies..."
    
    if [ ! -f "requirements_test.txt" ]; then
        print_color $RED "❌ Error: requirements_test.txt not found"
        exit 1
    fi
    
    # Check if we're in a virtual environment
    if [ -z "$VIRTUAL_ENV" ]; then
        print_color $YELLOW "⚠️  Not in a virtual environment. Consider using one."
        echo "   Create venv with: python -m venv venv"
        echo "   Activate with: source venv/bin/activate (Linux/Mac) or venv\\Scripts\\activate (Windows)"
        echo
    fi
    
    pip install -r requirements_test.txt
    print_color $GREEN "✅ Dependencies installed successfully"
}

check_dependencies() {
    print_color $YELLOW "🔍 Checking dependencies..."
    
    # Check if Python is available
    if ! command -v python3 &> /dev/null; then
        print_color $RED "❌ Error: Python 3 is not installed or not in PATH"
        exit 1
    fi
    
    # Check if required packages are installed
    python3 -c "import httpx, rich, pydantic" 2>/dev/null || {
        print_color $RED "❌ Error: Required dependencies not installed"
        print_color $YELLOW "💡 Run with --install-deps to install them"
        exit 1
    }
    
    print_color $GREEN "✅ Dependencies check passed"
}

check_api_server() {
    print_color $YELLOW "🌐 Checking if API server is running at $BASE_URL..."
    
    # Use curl or python to check if server is responding
    if command -v curl &> /dev/null; then
        if curl -s --max-time 5 "$BASE_URL/health" > /dev/null 2>&1; then
            print_color $GREEN "✅ API server is responding"
        else
            print_color $YELLOW "⚠️  API server may not be running at $BASE_URL"
            print_color $CYAN "   Tests will continue but may fail if server is not available"
        fi
    else
        print_color $YELLOW "⚠️  Could not check server status (curl not available)"
        print_color $CYAN "   Make sure your API server is running at $BASE_URL"
    fi
}

run_tests() {
    print_color $BLUE "🧪 Starting API test suite..."
    echo
    
    # Build command
    local cmd="python3 test_api_demo.py --base-url $BASE_URL"
    
    if [ "$LOAD_TEST" = true ]; then
        cmd="$cmd --load-test"
    fi
    
    if [ "$VERBOSE" = true ]; then
        cmd="$cmd --verbose"
    fi
    
    print_color $CYAN "Executing: $cmd"
    echo
    
    # Run the tests
    if eval "$cmd"; then
        echo
        print_color $GREEN "🎉 Test suite completed successfully!"
        
        # Check if HTML report was generated
        if [ -f "api_test_report.html" ]; then
            print_color $BLUE "📄 HTML report generated: api_test_report.html"
            
            # Try to open the report in browser (optional)
            if command -v open &> /dev/null; then  # macOS
                print_color $CYAN "💡 Opening report in browser..."
                open api_test_report.html
            elif command -v xdg-open &> /dev/null; then  # Linux
                print_color $CYAN "💡 Opening report in browser..."
                xdg-open api_test_report.html
            elif command -v start &> /dev/null; then  # Windows
                print_color $CYAN "💡 Opening report in browser..."
                start api_test_report.html
            fi
        fi
    else
        print_color $RED "❌ Test suite failed"
        exit 1
    fi
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --base-url)
            BASE_URL="$2"
            shift 2
            ;;
        --load-test)
            LOAD_TEST=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --install-deps)
            install_dependencies
            exit 0
            ;;
        --help|-h)
            print_help
            exit 0
            ;;
        *)
            print_color $RED "❌ Unknown option: $1"
            print_help
            exit 1
            ;;
    esac
done

# Main execution
print_header

# Check if test file exists
if [ ! -f "test_api_demo.py" ]; then
    print_color $RED "❌ Error: test_api_demo.py not found"
    print_color $YELLOW "   Make sure you're in the correct directory"
    exit 1
fi

# Run pre-flight checks
check_dependencies
check_api_server

# Display configuration
print_color $WHITE "Configuration:"
print_color $CYAN "  Base URL: $BASE_URL"
print_color $CYAN "  Load Test: $([ "$LOAD_TEST" = true ] && echo "Yes" || echo "No")"
print_color $CYAN "  Verbose: $([ "$VERBOSE" = true ] && echo "Yes" || echo "No")"
echo

# Run the tests
run_tests

print_color $PURPLE "======================================================"
print_color $GREEN "🏁 API Test Suite Launcher Complete"
print_color $PURPLE "======================================================"