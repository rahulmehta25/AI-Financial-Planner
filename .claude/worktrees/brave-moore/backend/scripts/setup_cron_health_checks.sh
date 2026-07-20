#!/bin/bash

# Setup Cron Health Checks for Demo Validation
# ============================================
# 
# This script sets up automated daily health checks for the financial planning demos.
# It configures cron jobs, systemd timers (on Linux), or scheduled tasks to run
# comprehensive demo validation on a regular schedule.

set -e

# Colors and formatting
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && cd ../.. && pwd)"
HEALTH_CHECK_SCRIPT="$PROJECT_ROOT/backend/scripts/daily_demo_health_check.py"
SMOKE_TEST_SCRIPT="$PROJECT_ROOT/demo-smoke-tests.sh"
LOG_DIR="/tmp/demo-health-logs"
CRON_LOG_FILE="$LOG_DIR/cron-health-check.log"
EMAIL_RECIPIENT="${DEMO_HEALTH_EMAIL:-}"
SLACK_WEBHOOK="${DEMO_HEALTH_SLACK_WEBHOOK:-}"

# Logging functions
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

print_header() {
    echo "================================================================"
    echo "🕒 Demo Health Check - Cron Setup"
    echo "================================================================"
    echo "Project: $PROJECT_ROOT"
    echo "Health Check Script: $HEALTH_CHECK_SCRIPT"
    echo "Log Directory: $LOG_DIR"
    echo "================================================================"
    echo ""
}

detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "linux"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macos"
    elif [[ "$OSTYPE" == "cygwin" ]] || [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
        echo "windows"
    else
        echo "unknown"
    fi
}

create_directories() {
    log_info "Creating required directories..."
    
    mkdir -p "$LOG_DIR"
    mkdir -p "$PROJECT_ROOT/reports/health-checks"
    
    log_success "Directories created"
}

create_wrapper_script() {
    log_info "Creating cron wrapper script..."
    
    local wrapper_script="$PROJECT_ROOT/backend/scripts/cron_health_check_wrapper.sh"
    
    cat > "$wrapper_script" << 'EOF'
#!/bin/bash

# Cron Wrapper Script for Demo Health Checks
# ===========================================
# This script is designed to be run from cron and handles:
# - Environment setup
# - Logging
# - Error handling
# - Notifications

# Configuration from environment or defaults
PROJECT_ROOT="${DEMO_PROJECT_ROOT:-/Users/rahulmehta/Desktop/Financial Planning}"
HEALTH_CHECK_SCRIPT="$PROJECT_ROOT/backend/scripts/daily_demo_health_check.py"
LOG_DIR="${DEMO_LOG_DIR:-/tmp/demo-health-logs}"
EMAIL_RECIPIENT="${DEMO_HEALTH_EMAIL:-}"
SLACK_WEBHOOK="${DEMO_HEALTH_SLACK_WEBHOOK:-}"

# Ensure log directory exists
mkdir -p "$LOG_DIR"

# Set up logging
TIMESTAMP=$(date '+%Y-%m-%d_%H-%M-%S')
LOG_FILE="$LOG_DIR/health-check-$TIMESTAMP.log"
REPORT_DIR="$PROJECT_ROOT/reports/health-checks"
REPORT_FILE="$REPORT_DIR/health-report-$TIMESTAMP.json"

# Ensure report directory exists
mkdir -p "$REPORT_DIR"

# Function to send notifications
send_notification() {
    local status="$1"
    local message="$2"
    local report_file="$3"
    
    # Email notification
    if [[ -n "$EMAIL_RECIPIENT" ]] && command -v mail >/dev/null; then
        echo -e "Demo Health Check Report\n\nStatus: $status\n\n$message\n\nReport file: $report_file" | \
            mail -s "Demo Health Check - $status" "$EMAIL_RECIPIENT"
    fi
    
    # Slack notification
    if [[ -n "$SLACK_WEBHOOK" ]] && command -v curl >/dev/null; then
        local color="good"
        case "$status" in
            "FAILED"|"UNHEALTHY") color="danger" ;;
            "WARNING") color="warning" ;;
        esac
        
        curl -X POST -H 'Content-type: application/json' \
            --data "{
                \"attachments\": [{
                    \"color\": \"$color\",
                    \"title\": \"Demo Health Check - $status\",
                    \"text\": \"$message\",
                    \"fields\": [{
                        \"title\": \"Timestamp\",
                        \"value\": \"$TIMESTAMP\",
                        \"short\": true
                    }, {
                        \"title\": \"Report\",
                        \"value\": \"$report_file\",
                        \"short\": true
                    }]
                }]
            }" \
            "$SLACK_WEBHOOK" >/dev/null 2>&1
    fi
}

# Function to cleanup old logs and reports
cleanup_old_files() {
    # Keep only last 30 days of logs
    find "$LOG_DIR" -name "health-check-*.log" -mtime +30 -delete 2>/dev/null || true
    find "$REPORT_DIR" -name "health-report-*.json" -mtime +30 -delete 2>/dev/null || true
}

# Main execution
main() {
    echo "Starting demo health check at $(date)" >> "$LOG_FILE"
    
    # Change to project directory
    cd "$PROJECT_ROOT" || {
        echo "Failed to change to project directory: $PROJECT_ROOT" >> "$LOG_FILE"
        send_notification "FAILED" "Could not access project directory: $PROJECT_ROOT" "$LOG_FILE"
        exit 1
    }
    
    # Set up environment
    export PYTHONPATH="$PROJECT_ROOT/backend:$PYTHONPATH"
    export DEMO_ENV="health_check"
    export AUTO_OPEN_BROWSER="false"
    
    # Run health check
    if python3 "$HEALTH_CHECK_SCRIPT" --save-report "$REPORT_FILE" --quiet >> "$LOG_FILE" 2>&1; then
        echo "Health check completed successfully at $(date)" >> "$LOG_FILE"
        
        # Extract summary from report
        if [[ -f "$REPORT_FILE" ]]; then
            local overall_status=$(python3 -c "
import json
try:
    with open('$REPORT_FILE') as f:
        data = json.load(f)
    print(data.get('overall_status', 'unknown'))
except:
    print('unknown')
" 2>/dev/null)
            
            case "$overall_status" in
                "healthy")
                    send_notification "HEALTHY" "All demo health checks passed successfully." "$REPORT_FILE"
                    ;;
                "warning")
                    send_notification "WARNING" "Demo health checks completed with warnings. Review required." "$REPORT_FILE"
                    ;;
                *)
                    send_notification "UNHEALTHY" "Demo health checks detected issues. Immediate attention required." "$REPORT_FILE"
                    ;;
            esac
        fi
    else
        echo "Health check failed at $(date)" >> "$LOG_FILE"
        send_notification "FAILED" "Demo health check script failed to execute properly." "$LOG_FILE"
        exit 1
    fi
    
    # Cleanup old files
    cleanup_old_files
    
    echo "Health check process completed at $(date)" >> "$LOG_FILE"
}

# Run main function
main
EOF

    chmod +x "$wrapper_script"
    log_success "Wrapper script created: $wrapper_script"
}

setup_cron_linux() {
    log_info "Setting up cron job (Linux)..."
    
    local cron_entry="0 2 * * * $PROJECT_ROOT/backend/scripts/cron_health_check_wrapper.sh"
    
    # Check if cron entry already exists
    if crontab -l 2>/dev/null | grep -q "cron_health_check_wrapper.sh"; then
        log_warning "Cron job already exists. Updating..."
        # Remove existing entry and add new one
        (crontab -l 2>/dev/null | grep -v "cron_health_check_wrapper.sh"; echo "$cron_entry") | crontab -
    else
        # Add new entry
        (crontab -l 2>/dev/null; echo "$cron_entry") | crontab -
    fi
    
    log_success "Cron job configured to run daily at 2:00 AM"
    
    # Optionally set up systemd timer for more robust scheduling
    if systemctl --user status >/dev/null 2>&1; then
        setup_systemd_timer
    fi
}

setup_cron_macos() {
    log_info "Setting up cron job (macOS)..."
    
    local cron_entry="0 2 * * * $PROJECT_ROOT/backend/scripts/cron_health_check_wrapper.sh"
    
    # Check if cron entry already exists
    if crontab -l 2>/dev/null | grep -q "cron_health_check_wrapper.sh"; then
        log_warning "Cron job already exists. Updating..."
        (crontab -l 2>/dev/null | grep -v "cron_health_check_wrapper.sh"; echo "$cron_entry") | crontab -
    else
        (crontab -l 2>/dev/null; echo "$cron_entry") | crontab -
    fi
    
    log_success "Cron job configured to run daily at 2:00 AM"
    log_info "Note: On macOS, you may need to grant Terminal full disk access in System Preferences > Security & Privacy"
}

setup_systemd_timer() {
    log_info "Setting up systemd timer..."
    
    local service_dir="$HOME/.config/systemd/user"
    mkdir -p "$service_dir"
    
    # Create service file
    cat > "$service_dir/demo-health-check.service" << EOF
[Unit]
Description=Daily Demo Health Check
After=network.target

[Service]
Type=oneshot
Environment=DEMO_PROJECT_ROOT=$PROJECT_ROOT
Environment=DEMO_LOG_DIR=$LOG_DIR
Environment=DEMO_HEALTH_EMAIL=$EMAIL_RECIPIENT
Environment=DEMO_HEALTH_SLACK_WEBHOOK=$SLACK_WEBHOOK
ExecStart=$PROJECT_ROOT/backend/scripts/cron_health_check_wrapper.sh
WorkingDirectory=$PROJECT_ROOT
EOF

    # Create timer file
    cat > "$service_dir/demo-health-check.timer" << EOF
[Unit]
Description=Run demo health check daily
Requires=demo-health-check.service

[Timer]
OnCalendar=daily
Persistent=true
RandomizedDelaySec=300

[Install]
WantedBy=timers.target
EOF
    
    # Enable and start timer
    systemctl --user daemon-reload
    systemctl --user enable demo-health-check.timer
    systemctl --user start demo-health-check.timer
    
    log_success "Systemd timer configured"
    log_info "Check status with: systemctl --user status demo-health-check.timer"
}

setup_windows_task() {
    log_info "Windows detected. Creating scheduled task..."
    
    log_warning "Windows scheduled task setup requires PowerShell."
    log_warning "Please run the following PowerShell commands as Administrator:"
    echo ""
    echo "# Create scheduled task for demo health checks"
    echo "schtasks /create /tn \"DemoHealthCheck\" /tr \"bash $PROJECT_ROOT/backend/scripts/cron_health_check_wrapper.sh\" /sc daily /st 02:00"
    echo ""
    log_info "Alternatively, use Task Scheduler GUI to create a daily task."
}

test_setup() {
    log_info "Testing health check setup..."
    
    # Test that scripts are executable
    if [[ ! -x "$HEALTH_CHECK_SCRIPT" ]]; then
        log_warning "Making health check script executable..."
        chmod +x "$HEALTH_CHECK_SCRIPT"
    fi
    
    if [[ ! -x "$SMOKE_TEST_SCRIPT" ]]; then
        log_warning "Making smoke test script executable..."
        chmod +x "$SMOKE_TEST_SCRIPT"
    fi
    
    # Run a quick test
    log_info "Running quick test..."
    if python3 "$HEALTH_CHECK_SCRIPT" --quiet >/dev/null 2>&1; then
        log_success "Health check script test passed"
    else
        log_error "Health check script test failed"
        return 1
    fi
    
    log_success "Setup test completed successfully"
}

print_status() {
    echo ""
    echo "================================================================"
    echo "📋 Demo Health Check Status"
    echo "================================================================"
    
    local os_type=$(detect_os)
    
    case "$os_type" in
        "linux")
            echo "Operating System: Linux"
            if crontab -l 2>/dev/null | grep -q "cron_health_check_wrapper.sh"; then
                echo "Cron Job: ✅ Configured"
                echo "Schedule: Daily at 2:00 AM"
            else
                echo "Cron Job: ❌ Not configured"
            fi
            
            if systemctl --user status demo-health-check.timer >/dev/null 2>&1; then
                echo "Systemd Timer: ✅ Active"
            else
                echo "Systemd Timer: ❌ Not configured"
            fi
            ;;
        "macos")
            echo "Operating System: macOS"
            if crontab -l 2>/dev/null | grep -q "cron_health_check_wrapper.sh"; then
                echo "Cron Job: ✅ Configured"
                echo "Schedule: Daily at 2:00 AM"
            else
                echo "Cron Job: ❌ Not configured"
            fi
            ;;
        "windows")
            echo "Operating System: Windows"
            echo "Scheduled Task: Please check Task Scheduler"
            ;;
        *)
            echo "Operating System: Unknown"
            ;;
    esac
    
    echo ""
    echo "Configuration:"
    echo "  Project Root: $PROJECT_ROOT"
    echo "  Log Directory: $LOG_DIR"
    echo "  Email Notifications: ${EMAIL_RECIPIENT:-'Not configured'}"
    echo "  Slack Notifications: ${SLACK_WEBHOOK:+'Configured'}"
    echo ""
    echo "Manual Commands:"
    echo "  Test Health Check: python3 \"$HEALTH_CHECK_SCRIPT\""
    echo "  Run Smoke Tests: \"$SMOKE_TEST_SCRIPT\""
    echo "  View Logs: ls -la \"$LOG_DIR\""
    echo ""
    echo "================================================================"
}

main() {
    local action="${1:-setup}"
    
    case "$action" in
        "setup")
            print_header
            create_directories
            create_wrapper_script
            
            local os_type=$(detect_os)
            case "$os_type" in
                "linux")
                    setup_cron_linux
                    ;;
                "macos")
                    setup_cron_macos
                    ;;
                "windows")
                    setup_windows_task
                    ;;
                *)
                    log_error "Unsupported operating system: $os_type"
                    exit 1
                    ;;
            esac
            
            test_setup
            print_status
            ;;
        "status")
            print_status
            ;;
        "test")
            test_setup
            ;;
        "clean")
            log_info "Cleaning up old logs and reports..."
            find "$LOG_DIR" -name "health-check-*.log" -mtime +7 -delete 2>/dev/null || true
            find "$PROJECT_ROOT/reports/health-checks" -name "health-report-*.json" -mtime +7 -delete 2>/dev/null || true
            log_success "Cleanup completed"
            ;;
        *)
            echo "Usage: $0 {setup|status|test|clean}"
            echo ""
            echo "Commands:"
            echo "  setup  - Configure daily health checks"
            echo "  status - Show current configuration"
            echo "  test   - Test health check scripts"
            echo "  clean  - Clean old logs and reports"
            exit 1
            ;;
    esac
}

# Run main function if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi