#!/bin/bash

# Financial Planning System - Demo Monitoring Dashboard
# Real-time monitoring script for demo environment
# Provides continuous health monitoring and alerting

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
REFRESH_INTERVAL=${REFRESH_INTERVAL:-5}
ALERT_THRESHOLD_CPU=${ALERT_THRESHOLD_CPU:-80}
ALERT_THRESHOLD_MEMORY=${ALERT_THRESHOLD_MEMORY:-85}
ALERT_THRESHOLD_DISK=${ALERT_THRESHOLD_DISK:-90}
LOG_FILE="logs/monitoring.log"

# Create logs directory if it doesn't exist
mkdir -p "$(dirname "$LOG_FILE")"

# Logging functions
log_with_timestamp() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') $1" | tee -a "$LOG_FILE"
}

print_header() {
    clear
    echo "================================================================"
    echo "📊 Financial Planning System - Demo Monitoring Dashboard"
    echo "================================================================"
    echo "Refresh Interval: ${REFRESH_INTERVAL}s | Press Ctrl+C to exit"
    echo "================================================================"
    echo ""
}

check_service_status() {
    local service_name="$1"
    local check_command="$2"
    local port="$3"
    
    if eval "$check_command" &>/dev/null; then
        echo -e "${GREEN}✓${NC} $service_name (Port $port)"
        return 0
    else
        echo -e "${RED}✗${NC} $service_name (Port $port)"
        return 1
    fi
}

get_container_stats() {
    if command -v docker &>/dev/null; then
        # Get Docker container statistics
        echo -e "${CYAN}🐳 Docker Containers:${NC}"
        if docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null | grep -E "(financial-planning|api|postgres|redis)" || true; then
            echo ""
        else
            echo -e "${YELLOW}⚠️  No project containers found${NC}"
            echo ""
        fi
    fi
}

get_system_stats() {
    echo -e "${BLUE}💻 System Resources:${NC}"
    
    # CPU Usage
    if command -v top &>/dev/null; then
        cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | awk -F'%' '{print $1}' 2>/dev/null || echo "0")
    elif command -v iostat &>/dev/null; then
        cpu_usage=$(iostat -c 1 1 | tail -1 | awk '{print 100-$6}' 2>/dev/null || echo "0")
    else
        cpu_usage="N/A"
    fi
    
    # Memory Usage
    if command -v free &>/dev/null; then
        memory_stats=$(free -m | awk 'NR==2{printf "%.1f", $3*100/$2}')
        memory_usage="${memory_stats}%"
    else
        memory_usage="N/A"
    fi
    
    # Disk Usage
    disk_usage=$(df -h . | awk 'NR==2{print $5}' 2>/dev/null || echo "N/A")
    
    # Format and color code based on thresholds
    if [[ "$cpu_usage" != "N/A" ]] && (( $(echo "$cpu_usage > $ALERT_THRESHOLD_CPU" | bc -l 2>/dev/null || echo 0) )); then
        cpu_color="${RED}"
    elif [[ "$cpu_usage" != "N/A" ]] && (( $(echo "$cpu_usage > 60" | bc -l 2>/dev/null || echo 0) )); then
        cpu_color="${YELLOW}"
    else
        cpu_color="${GREEN}"
    fi
    
    echo -e "  CPU Usage: ${cpu_color}${cpu_usage}%${NC}"
    echo -e "  Memory Usage: ${GREEN}${memory_usage}${NC}"
    echo -e "  Disk Usage: ${GREEN}${disk_usage}${NC}"
    echo ""
}

check_api_endpoints() {
    echo -e "${PURPLE}🌐 API Endpoints:${NC}"
    
    local api_base="http://localhost:8000"
    local endpoints=(
        "health:Health Check"
        "docs:API Documentation"
        "metrics:Metrics"
    )
    
    for endpoint_info in "${endpoints[@]}"; do
        IFS=':' read -r endpoint name <<< "$endpoint_info"
        local url="$api_base/$endpoint"
        
        if curl -s -f "$url" >/dev/null 2>&1; then
            local response_time=$(curl -s -w "%{time_total}" -o /dev/null "$url" 2>/dev/null || echo "0")
            response_time_ms=$(echo "$response_time * 1000" | bc -l 2>/dev/null | cut -d'.' -f1)
            echo -e "  ${GREEN}✓${NC} $name (${response_time_ms}ms)"
        else
            echo -e "  ${RED}✗${NC} $name"
        fi
    done
    echo ""
}

check_database_status() {
    echo -e "${BLUE}🗄️  Database Status:${NC}"
    
    # Check PostgreSQL connection
    if docker-compose exec -T postgres pg_isready -U financial_planning -d financial_planning >/dev/null 2>&1; then
        # Get connection count
        local conn_count=$(docker-compose exec -T postgres psql -U financial_planning -d financial_planning -t -c "SELECT count(*) FROM pg_stat_activity;" 2>/dev/null | tr -d ' \n' || echo "0")
        echo -e "  ${GREEN}✓${NC} PostgreSQL (${conn_count} connections)"
        
        # Get database size
        local db_size=$(docker-compose exec -T postgres psql -U financial_planning -d financial_planning -t -c "SELECT pg_size_pretty(pg_database_size('financial_planning'));" 2>/dev/null | tr -d ' \n' || echo "Unknown")
        echo -e "  Database Size: ${db_size}"
    else
        echo -e "  ${RED}✗${NC} PostgreSQL"
    fi
    
    # Check Redis
    if docker-compose exec -T redis redis-cli ping >/dev/null 2>&1; then
        local redis_clients=$(docker-compose exec -T redis redis-cli info clients | grep connected_clients | cut -d: -f2 | tr -d '\r\n' || echo "0")
        echo -e "  ${GREEN}✓${NC} Redis (${redis_clients} clients)"
    else
        echo -e "  ${RED}✗${NC} Redis"
    fi
    echo ""
}

get_recent_activity() {
    echo -e "${CYAN}📊 Recent Activity:${NC}"
    
    # Check recent API requests (from logs if available)
    if [ -f "logs/api/access.log" ]; then
        local recent_requests=$(tail -100 logs/api/access.log 2>/dev/null | grep "$(date '+%Y-%m-%d %H:%M')" | wc -l || echo "0")
        echo -e "  Recent API Requests: ${recent_requests} (last minute)"
    fi
    
    # Check recent database activity
    if docker-compose exec -T postgres psql -U financial_planning -d financial_planning -t -c "SELECT 1" >/dev/null 2>&1; then
        local recent_queries=$(docker-compose exec -T postgres psql -U financial_planning -d financial_planning -t -c "SELECT count(*) FROM pg_stat_statements WHERE calls > 0;" 2>/dev/null | tr -d ' \n' || echo "N/A")
        echo -e "  Database Queries: ${recent_queries} query types"
    fi
    
    # Show demo users count
    if docker-compose exec -T postgres psql -U financial_planning -d financial_planning -t -c "SELECT 1" >/dev/null 2>&1; then
        local user_count=$(docker-compose exec -T postgres psql -U financial_planning -d financial_planning -t -c "SELECT count(*) FROM users;" 2>/dev/null | tr -d ' \n' || echo "0")
        echo -e "  Demo Users: ${user_count}"
    fi
    
    echo ""
}

show_service_urls() {
    echo -e "${GREEN}🔗 Service URLs:${NC}"
    echo "  API Server:       http://localhost:8000"
    echo "  API Docs:         http://localhost:8000/docs"
    echo "  Health Check:     http://localhost:8000/health"
    echo "  Grafana:          http://localhost:3000 (admin/admin)"
    echo "  Database Admin:   http://localhost:5050"
    echo "  Redis Admin:      http://localhost:8081"
    echo ""
}

show_useful_commands() {
    echo -e "${YELLOW}🛠️  Useful Commands:${NC}"
    echo "  View API logs:    docker-compose logs -f api"
    echo "  View DB logs:     docker-compose logs -f postgres"
    echo "  Health check:     python3 scripts/health_check.py"
    echo "  Reset demo:       ./reset_demo.sh"
    echo "  Stop demo:        ./stop_demo.sh"
    echo ""
}

check_alerts() {
    local alerts=()
    
    # Check CPU usage
    if command -v top &>/dev/null; then
        local cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | awk -F'%' '{print $1}' 2>/dev/null || echo "0")
        if (( $(echo "$cpu_usage > $ALERT_THRESHOLD_CPU" | bc -l 2>/dev/null || echo 0) )); then
            alerts+=("High CPU usage: ${cpu_usage}%")
        fi
    fi
    
    # Check memory usage
    if command -v free &>/dev/null; then
        local memory_usage=$(free | awk 'NR==2{printf "%.1f", $3*100/$2}')
        if (( $(echo "$memory_usage > $ALERT_THRESHOLD_MEMORY" | bc -l 2>/dev/null || echo 0) )); then
            alerts+=("High memory usage: ${memory_usage}%")
        fi
    fi
    
    # Check disk usage
    local disk_usage_num=$(df . | awk 'NR==2{print $5}' | sed 's/%//' 2>/dev/null || echo "0")
    if (( disk_usage_num > ALERT_THRESHOLD_DISK )); then
        alerts+=("High disk usage: ${disk_usage_num}%")
    fi
    
    # Check if API is responding
    if ! curl -s -f "http://localhost:8000/health" >/dev/null 2>&1; then
        alerts+=("API not responding")
    fi
    
    # Display alerts
    if [ ${#alerts[@]} -gt 0 ]; then
        echo -e "${RED}🚨 ALERTS:${NC}"
        for alert in "${alerts[@]}"; do
            echo -e "  ${RED}⚠️  ${alert}${NC}"
            log_with_timestamp "ALERT: $alert"
        done
        echo ""
    fi
}

main_monitoring_loop() {
    local iteration=0
    
    while true; do
        print_header
        
        echo -e "${BLUE}Iteration: $((++iteration)) | $(date)${NC}"
        echo ""
        
        # Check for alerts first
        check_alerts
        
        # System statistics
        get_system_stats
        
        # Container status
        get_container_stats
        
        # API endpoints
        check_api_endpoints
        
        # Database status
        check_database_status
        
        # Recent activity
        get_recent_activity
        
        # Service URLs
        show_service_urls
        
        # Useful commands
        show_useful_commands
        
        echo -e "${BLUE}Next refresh in ${REFRESH_INTERVAL} seconds... (Ctrl+C to exit)${NC}"
        
        # Wait for next iteration
        sleep "$REFRESH_INTERVAL"
    done
}

# Handle Ctrl+C gracefully
trap 'echo -e "\n${YELLOW}Monitoring stopped by user${NC}"; exit 0' INT

# Quick health check mode
if [ "${1:-}" = "--quick" ]; then
    print_header
    echo "Running quick health check..."
    echo ""
    
    get_system_stats
    check_api_endpoints
    check_database_status
    
    echo -e "${GREEN}Quick health check completed${NC}"
    exit 0
fi

# Help message
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
    echo "Financial Planning Demo - Monitoring Script"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --quick               Run quick health check and exit"
    echo "  --help, -h           Show this help message"
    echo ""
    echo "Environment Variables:"
    echo "  REFRESH_INTERVAL      Refresh interval in seconds (default: 5)"
    echo "  ALERT_THRESHOLD_CPU   CPU alert threshold (default: 80)"
    echo "  ALERT_THRESHOLD_MEMORY Memory alert threshold (default: 85)"
    echo "  ALERT_THRESHOLD_DISK  Disk alert threshold (default: 90)"
    echo ""
    echo "Examples:"
    echo "  $0                    # Start continuous monitoring"
    echo "  $0 --quick           # Quick health check"
    echo "  REFRESH_INTERVAL=10 $0  # Monitor with 10s intervals"
    echo ""
    exit 0
fi

# Start monitoring
log_with_timestamp "Demo monitoring started"
echo -e "${GREEN}Starting Financial Planning Demo Monitoring...${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop monitoring${NC}"
echo ""
sleep 2

main_monitoring_loop