#!/bin/bash

# Financial Planning System - Demo Reset Script
# Resets database to initial state, clears caches, and reloads sample data
# Supports: macOS, Linux, Windows WSL

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="financial-planning"
RESET_TYPE=${RESET_TYPE:-"soft"}  # soft, hard, restore
BACKUP_DIR=${BACKUP_DIR:-""}
SEED_DEMO_DATA=${SEED_DEMO_DATA:-true}
PRESERVE_USER_DATA=${PRESERVE_USER_DATA:-false}

# Logging functions
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Error handling
error_exit() {
    log_error "$1"
    exit 1
}

print_header() {
    echo "================================================================"
    echo "🔄 Financial Planning System - Demo Environment Reset"
    echo "================================================================"
    echo "Reset Type: $RESET_TYPE"
    echo "Seed Demo Data: $SEED_DEMO_DATA"
    echo "Preserve User Data: $PRESERVE_USER_DATA"
    echo "Timestamp: $(date)"
    echo "================================================================"
}

check_services_running() {
    log_info "Checking if services are running..."
    
    local api_running=false
    local db_running=false
    local redis_running=false
    
    # Check if API is responding
    if curl -s "http://localhost:8000/health" &>/dev/null; then
        api_running=true
        log_success "API service is running"
    else
        log_warning "API service is not responding"
    fi
    
    # Check if database is accessible
    if docker-compose exec -T postgres pg_isready -U financial_planning -d financial_planning &>/dev/null; then
        db_running=true
        log_success "Database service is running"
    else
        log_warning "Database service is not accessible"
    fi
    
    # Check if Redis is accessible
    if docker-compose exec -T redis redis-cli ping &>/dev/null; then
        redis_running=true
        log_success "Redis service is running"
    else
        log_warning "Redis service is not accessible"
    fi
    
    if [ "$api_running" = false ] || [ "$db_running" = false ]; then
        log_warning "Some services are not running. Starting services first..."
        ./start_demo.sh --skip-browser
        sleep 5
    fi
}

create_backup() {
    log_info "Creating backup before reset..."
    
    local backup_timestamp=$(date +%Y%m%d-%H%M%S)
    local backup_path="backups/reset-backup-$backup_timestamp"
    
    mkdir -p "$backup_path"
    
    # Backup database
    if docker-compose exec -T postgres pg_isready -U financial_planning -d financial_planning &>/dev/null; then
        log_info "Backing up database..."
        if docker-compose exec -T postgres pg_dump -U financial_planning -d financial_planning > "$backup_path/database.sql"; then
            log_success "Database backed up to $backup_path/database.sql"
        else
            log_warning "Database backup failed"
        fi
    fi
    
    # Backup Redis data
    if docker-compose exec -T redis redis-cli ping &>/dev/null; then
        log_info "Backing up Redis data..."
        if docker-compose exec -T redis redis-cli save &>/dev/null; then
            docker cp "$(docker-compose ps -q redis):/data/dump.rdb" "$backup_path/redis-dump.rdb" 2>/dev/null || true
            log_success "Redis data backed up"
        else
            log_warning "Redis backup failed"
        fi
    fi
    
    # Backup uploads and exports
    [ -d "uploads" ] && cp -r uploads "$backup_path/" 2>/dev/null || true
    [ -d "exports" ] && cp -r exports "$backup_path/" 2>/dev/null || true
    
    log_success "Backup created at $backup_path"
    echo "BACKUP_PATH=$backup_path" > .last_backup
}

reset_database_soft() {
    log_info "Performing soft database reset (clearing user data, keeping schema)..."
    
    # Preserve user data if requested
    local user_backup=""
    if [ "$PRESERVE_USER_DATA" = "true" ]; then
        log_info "Preserving user data..."
        user_backup=$(mktemp)
        docker-compose exec -T postgres pg_dump -U financial_planning -d financial_planning -t users -t user_profiles --data-only > "$user_backup"
    fi
    
    # Clear transactional data
    log_info "Clearing transactional data..."
    docker-compose exec -T postgres psql -U financial_planning -d financial_planning << 'EOF'
-- Clear simulation and analysis data
TRUNCATE TABLE simulation_results, monte_carlo_results CASCADE;
TRUNCATE TABLE ml_recommendations, recommendation_feedback CASCADE;
TRUNCATE TABLE goal_progress, financial_goals CASCADE;
TRUNCATE TABLE transactions, account_balances CASCADE;
TRUNCATE TABLE market_data_cache, market_alerts CASCADE;
TRUNCATE TABLE audit_logs CASCADE;
TRUNCATE TABLE pdf_exports CASCADE;
TRUNCATE TABLE notifications CASCADE;

-- Reset sequences
SELECT setval(pg_get_serial_sequence('simulation_results', 'id'), 1, false);
SELECT setval(pg_get_serial_sequence('financial_goals', 'id'), 1, false);
SELECT setval(pg_get_serial_sequence('transactions', 'id'), 1, false);

-- Clear user data unless preserved
EOF
    
    if [ "$PRESERVE_USER_DATA" = "false" ]; then
        docker-compose exec -T postgres psql -U financial_planning -d financial_planning << 'EOF'
TRUNCATE TABLE user_profiles, users CASCADE;
SELECT setval(pg_get_serial_sequence('users', 'id'), 1, false);
EOF
    fi
    
    # Restore user data if it was preserved
    if [ "$PRESERVE_USER_DATA" = "true" ] && [ -f "$user_backup" ]; then
        log_info "Restoring preserved user data..."
        docker-compose exec -T postgres psql -U financial_planning -d financial_planning < "$user_backup"
        rm -f "$user_backup"
    fi
    
    log_success "Soft database reset completed"
}

reset_database_hard() {
    log_info "Performing hard database reset (dropping and recreating database)..."
    
    # Drop and recreate database
    docker-compose exec -T postgres psql -U financial_planning -d postgres << 'EOF'
DROP DATABASE IF EXISTS financial_planning;
CREATE DATABASE financial_planning OWNER financial_planning;
EOF
    
    # Run migrations
    log_info "Running database migrations..."
    if docker-compose exec -T api alembic upgrade head; then
        log_success "Database migrations completed"
    else
        error_exit "Database migrations failed"
    fi
    
    log_success "Hard database reset completed"
}

restore_from_backup() {
    if [ -z "$BACKUP_DIR" ]; then
        error_exit "BACKUP_DIR must be specified for restore operation"
    fi
    
    if [ ! -d "$BACKUP_DIR" ]; then
        error_exit "Backup directory $BACKUP_DIR does not exist"
    fi
    
    log_info "Restoring from backup: $BACKUP_DIR"
    
    # Restore database
    if [ -f "$BACKUP_DIR/database.sql" ]; then
        log_info "Restoring database from backup..."
        
        # Drop and recreate database
        docker-compose exec -T postgres psql -U financial_planning -d postgres << 'EOF'
DROP DATABASE IF EXISTS financial_planning;
CREATE DATABASE financial_planning OWNER financial_planning;
EOF
        
        # Restore data
        if docker-compose exec -T postgres psql -U financial_planning -d financial_planning < "$BACKUP_DIR/database.sql"; then
            log_success "Database restored from backup"
        else
            error_exit "Database restore failed"
        fi
    else
        log_warning "No database backup found in $BACKUP_DIR"
    fi
    
    # Restore Redis data
    if [ -f "$BACKUP_DIR/redis-dump.rdb" ]; then
        log_info "Restoring Redis data from backup..."
        docker cp "$BACKUP_DIR/redis-dump.rdb" "$(docker-compose ps -q redis):/data/dump.rdb"
        docker-compose restart redis
        log_success "Redis data restored from backup"
    else
        log_warning "No Redis backup found in $BACKUP_DIR"
    fi
    
    # Restore file uploads and exports
    [ -d "$BACKUP_DIR/uploads" ] && cp -r "$BACKUP_DIR/uploads" . 2>/dev/null || true
    [ -d "$BACKUP_DIR/exports" ] && cp -r "$BACKUP_DIR/exports" . 2>/dev/null || true
    
    log_success "Restore from backup completed"
}

clear_caches() {
    log_info "Clearing application caches..."
    
    # Clear Redis cache
    if docker-compose exec -T redis redis-cli ping &>/dev/null; then
        log_info "Clearing Redis cache..."
        docker-compose exec -T redis redis-cli flushall &>/dev/null
        log_success "Redis cache cleared"
    fi
    
    # Clear application cache directories
    local cache_dirs=("tmp" "cache" ".cache" "__pycache__")
    for dir in "${cache_dirs[@]}"; do
        if [ -d "$dir" ]; then
            rm -rf "$dir"
            log_success "Cleared $dir directory"
        fi
    done
    
    # Clear Python cache files
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete 2>/dev/null || true
    
    # Clear temporary files
    rm -rf logs/tmp/* 2>/dev/null || true
    rm -rf exports/tmp/* 2>/dev/null || true
    
    log_success "Caches cleared"
}

reset_file_storage() {
    log_info "Resetting file storage..."
    
    # Clear uploads (except preserved files)
    if [ -d "uploads" ]; then
        if [ "$PRESERVE_USER_DATA" = "true" ]; then
            # Only clear temporary uploads
            rm -rf uploads/temp/* 2>/dev/null || true
            log_success "Temporary uploads cleared"
        else
            # Clear all uploads
            rm -rf uploads/*
            mkdir -p uploads/{temp,avatars,documents}
            log_success "All uploads cleared"
        fi
    fi
    
    # Clear generated exports (PDFs, CSVs, etc.)
    if [ -d "exports" ]; then
        rm -rf exports/*
        mkdir -p exports/{pdf,csv,excel}
        log_success "Generated exports cleared"
    fi
    
    # Clear logs (except current session)
    if [ -d "logs" ]; then
        find logs -name "*.log" -mtime +0 -delete 2>/dev/null || true
        log_success "Old log files cleared"
    fi
}

seed_sample_data() {
    if [ "$SEED_DEMO_DATA" = "true" ]; then
        log_info "Seeding demo data..."
        
        # Check if demo data seeder exists
        if [ -f "scripts/seed_demo_data.py" ]; then
            if python3 scripts/seed_demo_data.py; then
                log_success "Demo data seeded successfully"
            else
                log_warning "Demo data seeding failed"
            fi
        elif [ -f "scripts/demo_data_seeder.py" ]; then
            if python3 scripts/demo_data_seeder.py; then
                log_success "Demo data seeded successfully"
            else
                log_warning "Demo data seeding failed"
            fi
        else
            # Create minimal demo data via API
            log_info "Creating minimal demo data via API..."
            create_demo_data_via_api
        fi
    else
        log_info "Skipping demo data seeding (SEED_DEMO_DATA=false)"
    fi
}

create_demo_data_via_api() {
    log_info "Creating demo user and basic data..."
    
    # Wait for API to be ready
    local max_attempts=30
    local attempt=1
    while [ $attempt -le $max_attempts ]; do
        if curl -s "http://localhost:8000/health" &>/dev/null; then
            break
        fi
        
        if [ $attempt -eq $max_attempts ]; then
            error_exit "API not ready after $max_attempts attempts"
        fi
        
        sleep 2
        ((attempt++))
    done
    
    # Create demo user
    cat << 'EOF' > /tmp/demo_user.json
{
    "email": "demo@financialplanning.com",
    "password": "demo123456",
    "full_name": "Demo User",
    "is_active": true
}
EOF
    
    log_info "Creating demo user..."
    curl -s -X POST "http://localhost:8000/api/v1/users/register" \
        -H "Content-Type: application/json" \
        -d @/tmp/demo_user.json > /dev/null || true
    
    # Login to get token
    cat << 'EOF' > /tmp/login.json
{
    "username": "demo@financialplanning.com",
    "password": "demo123456"
}
EOF
    
    log_info "Logging in demo user..."
    local token_response=$(curl -s -X POST "http://localhost:8000/api/v1/auth/login" \
        -H "Content-Type: application/x-www-form-urlencoded" \
        -d "username=demo@financialplanning.com&password=demo123456" || echo "{}")
    
    local access_token=$(echo "$token_response" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4 || echo "")
    
    if [ -n "$access_token" ]; then
        # Create demo financial goals
        cat << 'EOF' > /tmp/demo_goal.json
{
    "name": "Emergency Fund",
    "description": "Build emergency fund covering 6 months of expenses",
    "target_amount": 30000,
    "target_date": "2025-12-31",
    "priority": "high",
    "goal_type": "savings"
}
EOF
        
        log_info "Creating demo financial goal..."
        curl -s -X POST "http://localhost:8000/api/v1/goals/" \
            -H "Authorization: Bearer $access_token" \
            -H "Content-Type: application/json" \
            -d @/tmp/demo_goal.json > /dev/null || true
        
        log_success "Demo data created via API"
    else
        log_warning "Could not authenticate demo user"
    fi
    
    # Cleanup temporary files
    rm -f /tmp/demo_user.json /tmp/login.json /tmp/demo_goal.json
}

restart_services() {
    log_info "Restarting services to apply changes..."
    
    # Restart application services
    docker-compose restart api celery-worker celery-beat
    
    # Wait for API to be ready
    local max_attempts=30
    local attempt=1
    while [ $attempt -le $max_attempts ]; do
        if curl -s "http://localhost:8000/health" &>/dev/null; then
            break
        fi
        
        if [ $attempt -eq $max_attempts ]; then
            error_exit "API failed to restart after $max_attempts attempts"
        fi
        
        log_info "Waiting for API restart... (attempt $attempt/$max_attempts)"
        sleep 2
        ((attempt++))
    done
    
    log_success "Services restarted successfully"
}

run_health_checks() {
    log_info "Running post-reset health checks..."
    
    local failed_checks=0
    
    # API Health Check
    if curl -s "http://localhost:8000/health" | grep -q "healthy"; then
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
    
    # Database Content Check
    local user_count=$(docker-compose exec -T postgres psql -U financial_planning -d financial_planning -t -c "SELECT COUNT(*) FROM users;" 2>/dev/null | tr -d ' \n' || echo "0")
    if [ "$user_count" -gt 0 ]; then
        log_success "✓ Database contains $user_count user(s)"
    else
        log_warning "⚠ Database appears to be empty"
    fi
    
    if [ $failed_checks -gt 0 ]; then
        log_error "$failed_checks health check(s) failed"
        return 1
    fi
    
    log_success "All health checks passed"
    return 0
}

print_reset_summary() {
    echo ""
    echo "================================================================"
    echo "✅ Financial Planning Demo Environment Reset Complete"
    echo "================================================================"
    echo ""
    echo "📊 Reset Summary:"
    echo "  • Reset Type: $RESET_TYPE"
    echo "  • Database: Reset ✓"
    echo "  • Caches: Cleared ✓"
    echo "  • File Storage: Reset ✓"
    
    if [ "$SEED_DEMO_DATA" = "true" ]; then
        echo "  • Demo Data: Seeded ✓"
    else
        echo "  • Demo Data: Skipped"
    fi
    
    if [ "$PRESERVE_USER_DATA" = "true" ]; then
        echo "  • User Data: Preserved ✓"
    fi
    
    echo ""
    echo "🔐 Demo Credentials:"
    echo "  • Email: demo@financialplanning.com"
    echo "  • Password: demo123456"
    echo ""
    echo "🌐 Access Points:"
    echo "  • API Server: http://localhost:8000"
    echo "  • API Docs: http://localhost:8000/docs"
    echo "  • Health Check: http://localhost:8000/health"
    echo ""
    echo "📖 Next Steps:"
    echo "  • Test the API endpoints"
    echo "  • Create additional users/data as needed"
    echo "  • Run integration tests"
    echo ""
    echo "================================================================"
}

show_help() {
    echo "Financial Planning Demo - Reset Script"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Reset Types:"
    echo "  soft      Clear user data, keep schema (default)"
    echo "  hard      Drop and recreate database completely"
    echo "  restore   Restore from backup directory"
    echo ""
    echo "Options:"
    echo "  -h, --help                  Show this help message"
    echo "  -t, --type TYPE             Reset type: soft|hard|restore"
    echo "  -b, --backup-dir DIR        Backup directory for restore"
    echo "  -s, --seed                  Seed demo data (default: true)"
    echo "  -n, --no-seed               Don't seed demo data"
    echo "  -p, --preserve-users        Preserve user data during reset"
    echo "  -f, --fast                  Skip backup creation"
    echo ""
    echo "Environment Variables:"
    echo "  RESET_TYPE=soft|hard|restore    Type of reset to perform"
    echo "  BACKUP_DIR=path                 Backup directory for restore"
    echo "  SEED_DEMO_DATA=true|false       Whether to seed demo data"
    echo "  PRESERVE_USER_DATA=true|false   Preserve existing users"
    echo ""
    echo "Examples:"
    echo "  $0                              # Soft reset with demo data"
    echo "  $0 --type hard                  # Complete database reset"
    echo "  $0 --type restore -b backups/demo-20240101-120000"
    echo "  $0 --preserve-users             # Reset but keep existing users"
    echo "  $0 --no-seed                    # Reset without demo data"
    echo ""
}

main() {
    print_header
    
    case "$RESET_TYPE" in
        soft)
            check_services_running
            create_backup
            reset_database_soft
            clear_caches
            reset_file_storage
            seed_sample_data
            restart_services
            ;;
        hard)
            check_services_running
            create_backup
            reset_database_hard
            clear_caches
            reset_file_storage
            seed_sample_data
            restart_services
            ;;
        restore)
            check_services_running
            restore_from_backup
            clear_caches
            restart_services
            ;;
        *)
            error_exit "Invalid reset type: $RESET_TYPE. Use: soft, hard, or restore"
            ;;
    esac
    
    # Validate reset
    if run_health_checks; then
        print_reset_summary
        log_success "Demo environment reset completed successfully!"
    else
        error_exit "Reset completed but health checks failed"
    fi
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -t|--type)
            RESET_TYPE="$2"
            shift 2
            ;;
        -b|--backup-dir)
            BACKUP_DIR="$2"
            shift 2
            ;;
        -s|--seed)
            SEED_DEMO_DATA=true
            shift
            ;;
        -n|--no-seed)
            SEED_DEMO_DATA=false
            shift
            ;;
        -p|--preserve-users)
            PRESERVE_USER_DATA=true
            shift
            ;;
        -f|--fast)
            SKIP_BACKUP=true
            shift
            ;;
        *)
            log_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Script execution
if [ "${BASH_SOURCE[0]}" == "${0}" ]; then
    main "$@"
fi