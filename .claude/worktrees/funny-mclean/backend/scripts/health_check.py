#!/usr/bin/env python3
"""
Financial Planning System - Comprehensive Health Check Script
Production-ready health monitoring with detailed diagnostics and alerting

This script provides:
- Service health monitoring
- Database connectivity checks
- Performance metrics collection
- Resource utilization monitoring
- External service validation
- Alert generation and notifications
"""

import asyncio
import os
import sys
import time
import json
import psutil
import socket
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import argparse

try:
    import httpx
    import redis
    import psycopg2
    from psycopg2.extras import RealDictCursor
    import docker
except ImportError as e:
    print(f"❌ Missing required dependency: {e}")
    print("Please install: pip install httpx redis psycopg2-binary docker psutil")
    sys.exit(1)

# Color codes for output
class Colors:
    BLUE = '\033[0;34m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[0;33m'
    RED = '\033[0;31m'
    PURPLE = '\033[0;35m'
    CYAN = '\033[0;36m'
    NC = '\033[0m'  # No Color

class HealthStatus(Enum):
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"

@dataclass
class HealthCheckResult:
    name: str
    status: HealthStatus
    message: str
    details: Dict[str, Any]
    duration_ms: float
    timestamp: datetime

@dataclass
class ServiceMetrics:
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_connections: int
    uptime_seconds: float

class HealthChecker:
    """Comprehensive health checker for financial planning system"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.results: List[HealthCheckResult] = []
        self.overall_status = HealthStatus.HEALTHY
        
        # Service endpoints
        self.api_url = config.get('api_url', 'http://localhost:8000')
        self.grafana_url = config.get('grafana_url', 'http://localhost:3000')
        self.prometheus_url = config.get('prometheus_url', 'http://localhost:9091')
        
        # Database configuration
        self.db_config = {
            'host': config.get('db_host', 'localhost'),
            'port': config.get('db_port', 5432),
            'database': config.get('db_name', 'financial_planning'),
            'user': config.get('db_user', 'financial_planning'),
            'password': config.get('db_password', 'financial_planning')
        }
        
        # Redis configuration
        self.redis_config = {
            'host': config.get('redis_host', 'localhost'),
            'port': config.get('redis_port', 6379),
            'db': config.get('redis_db', 0)
        }
        
        # Thresholds
        self.thresholds = {
            'cpu_warning': config.get('cpu_warning', 70),
            'cpu_critical': config.get('cpu_critical', 90),
            'memory_warning': config.get('memory_warning', 80),
            'memory_critical': config.get('memory_critical', 95),
            'disk_warning': config.get('disk_warning', 80),
            'disk_critical': config.get('disk_critical', 95),
            'response_time_warning': config.get('response_time_warning', 2000),
            'response_time_critical': config.get('response_time_critical', 5000)
        }

    def log_info(self, message: str):
        print(f"{Colors.BLUE}[INFO]{Colors.NC} {message}")

    def log_success(self, message: str):
        print(f"{Colors.GREEN}[SUCCESS]{Colors.NC} {message}")

    def log_warning(self, message: str):
        print(f"{Colors.YELLOW}[WARNING]{Colors.NC} {message}")

    def log_error(self, message: str):
        print(f"{Colors.RED}[ERROR]{Colors.NC} {message}")

    def log_critical(self, message: str):
        print(f"{Colors.RED}[CRITICAL]{Colors.NC} {message}")

    async def check_api_health(self) -> HealthCheckResult:
        """Check API service health"""
        start_time = time.time()
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Check basic health endpoint
                health_response = await client.get(f"{self.api_url}/health")
                health_duration = (time.time() - start_time) * 1000
                
                if health_response.status_code == 200:
                    health_data = health_response.json()
                    
                    # Check additional API endpoints
                    docs_response = await client.get(f"{self.api_url}/docs")
                    metrics_response = await client.get(f"{self.api_url}/metrics", 
                                                      headers={"Accept": "text/plain"})
                    
                    details = {
                        "health_status": health_data,
                        "response_time_ms": health_duration,
                        "docs_accessible": docs_response.status_code == 200,
                        "metrics_accessible": metrics_response.status_code == 200,
                        "api_version": health_data.get("version", "unknown")
                    }
                    
                    # Determine status based on response time
                    if health_duration > self.thresholds['response_time_critical']:
                        status = HealthStatus.CRITICAL
                        message = f"API responding but very slow ({health_duration:.1f}ms)"
                    elif health_duration > self.thresholds['response_time_warning']:
                        status = HealthStatus.WARNING
                        message = f"API responding but slow ({health_duration:.1f}ms)"
                    else:
                        status = HealthStatus.HEALTHY
                        message = f"API healthy ({health_duration:.1f}ms)"
                    
                    return HealthCheckResult(
                        name="API Service",
                        status=status,
                        message=message,
                        details=details,
                        duration_ms=health_duration,
                        timestamp=datetime.utcnow()
                    )
                else:
                    return HealthCheckResult(
                        name="API Service",
                        status=HealthStatus.CRITICAL,
                        message=f"API returned status {health_response.status_code}",
                        details={"status_code": health_response.status_code},
                        duration_ms=(time.time() - start_time) * 1000,
                        timestamp=datetime.utcnow()
                    )
                    
        except Exception as e:
            return HealthCheckResult(
                name="API Service",
                status=HealthStatus.CRITICAL,
                message=f"API unreachable: {str(e)}",
                details={"error": str(e)},
                duration_ms=(time.time() - start_time) * 1000,
                timestamp=datetime.utcnow()
            )

    async def check_database_health(self) -> HealthCheckResult:
        """Check database connectivity and performance"""
        start_time = time.time()
        
        try:
            # Test connection
            conn = psycopg2.connect(**self.db_config, connect_timeout=10)
            conn.autocommit = True
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Basic connectivity test
            cursor.execute("SELECT 1 as test")
            cursor.fetchone()
            
            # Check database size and activity
            cursor.execute("""
                SELECT 
                    pg_database_size(current_database()) as db_size_bytes,
                    (SELECT count(*) FROM pg_stat_activity WHERE state = 'active') as active_connections,
                    (SELECT count(*) FROM pg_stat_activity) as total_connections,
                    (SELECT setting::int FROM pg_settings WHERE name = 'max_connections') as max_connections
            """)
            db_stats = cursor.fetchone()
            
            # Check table counts
            cursor.execute("""
                SELECT 
                    (SELECT count(*) FROM users) as users_count,
                    (SELECT count(*) FROM financial_goals) as goals_count,
                    (SELECT count(*) FROM investments) as investments_count,
                    (SELECT count(*) FROM simulation_results) as simulations_count
            """)
            table_stats = cursor.fetchone()
            
            # Check recent activity
            cursor.execute("""
                SELECT count(*) as recent_logins 
                FROM audit_logs 
                WHERE action = 'user_login' 
                AND created_at > NOW() - INTERVAL '1 hour'
            """)
            recent_activity = cursor.fetchone()
            
            duration_ms = (time.time() - start_time) * 1000
            
            # Calculate connection utilization
            connection_utilization = (db_stats['active_connections'] / db_stats['max_connections']) * 100
            
            details = {
                "database_size_mb": round(db_stats['db_size_bytes'] / 1024 / 1024, 2),
                "active_connections": db_stats['active_connections'],
                "total_connections": db_stats['total_connections'],
                "max_connections": db_stats['max_connections'],
                "connection_utilization_percent": round(connection_utilization, 2),
                "table_counts": dict(table_stats),
                "recent_activity": dict(recent_activity),
                "response_time_ms": duration_ms
            }
            
            # Determine status
            if connection_utilization > 90:
                status = HealthStatus.CRITICAL
                message = f"Database connection pool near capacity ({connection_utilization:.1f}%)"
            elif connection_utilization > 70:
                status = HealthStatus.WARNING
                message = f"Database connection utilization high ({connection_utilization:.1f}%)"
            elif duration_ms > self.thresholds['response_time_critical']:
                status = HealthStatus.CRITICAL
                message = f"Database responding slowly ({duration_ms:.1f}ms)"
            elif duration_ms > self.thresholds['response_time_warning']:
                status = HealthStatus.WARNING
                message = f"Database response time elevated ({duration_ms:.1f}ms)"
            else:
                status = HealthStatus.HEALTHY
                message = f"Database healthy ({duration_ms:.1f}ms, {db_stats['active_connections']} connections)"
            
            cursor.close()
            conn.close()
            
            return HealthCheckResult(
                name="Database",
                status=status,
                message=message,
                details=details,
                duration_ms=duration_ms,
                timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            return HealthCheckResult(
                name="Database",
                status=HealthStatus.CRITICAL,
                message=f"Database connection failed: {str(e)}",
                details={"error": str(e)},
                duration_ms=(time.time() - start_time) * 1000,
                timestamp=datetime.utcnow()
            )

    async def check_redis_health(self) -> HealthCheckResult:
        """Check Redis cache health"""
        start_time = time.time()
        
        try:
            r = redis.Redis(**self.redis_config, socket_connect_timeout=10)
            
            # Test basic connectivity
            r.ping()
            
            # Get Redis info
            info = r.info()
            
            # Test read/write operations
            test_key = "health_check_test"
            r.set(test_key, "test_value", ex=60)
            value = r.get(test_key)
            r.delete(test_key)
            
            duration_ms = (time.time() - start_time) * 1000
            
            # Calculate memory utilization
            used_memory = info.get('used_memory', 0)
            max_memory = info.get('maxmemory', 0)
            memory_utilization = (used_memory / max_memory * 100) if max_memory > 0 else 0
            
            details = {
                "redis_version": info.get('redis_version'),
                "connected_clients": info.get('connected_clients'),
                "used_memory_mb": round(used_memory / 1024 / 1024, 2),
                "max_memory_mb": round(max_memory / 1024 / 1024, 2) if max_memory > 0 else "unlimited",
                "memory_utilization_percent": round(memory_utilization, 2),
                "keyspace_hits": info.get('keyspace_hits', 0),
                "keyspace_misses": info.get('keyspace_misses', 0),
                "operations_per_sec": info.get('instantaneous_ops_per_sec', 0),
                "response_time_ms": duration_ms
            }
            
            # Calculate hit ratio
            hits = info.get('keyspace_hits', 0)
            misses = info.get('keyspace_misses', 0)
            hit_ratio = (hits / (hits + misses) * 100) if (hits + misses) > 0 else 100
            details['cache_hit_ratio_percent'] = round(hit_ratio, 2)
            
            # Determine status
            if memory_utilization > 95:
                status = HealthStatus.CRITICAL
                message = f"Redis memory usage critical ({memory_utilization:.1f}%)"
            elif memory_utilization > 80:
                status = HealthStatus.WARNING
                message = f"Redis memory usage high ({memory_utilization:.1f}%)"
            elif hit_ratio < 70:
                status = HealthStatus.WARNING
                message = f"Redis cache hit ratio low ({hit_ratio:.1f}%)"
            else:
                status = HealthStatus.HEALTHY
                message = f"Redis healthy ({duration_ms:.1f}ms, {info.get('connected_clients')} clients)"
            
            return HealthCheckResult(
                name="Redis Cache",
                status=status,
                message=message,
                details=details,
                duration_ms=duration_ms,
                timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            return HealthCheckResult(
                name="Redis Cache",
                status=HealthStatus.CRITICAL,
                message=f"Redis connection failed: {str(e)}",
                details={"error": str(e)},
                duration_ms=(time.time() - start_time) * 1000,
                timestamp=datetime.utcnow()
            )

    def check_system_resources(self) -> HealthCheckResult:
        """Check system resource utilization"""
        start_time = time.time()
        
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            
            # Network statistics
            network = psutil.net_io_counters()
            
            # Process count
            process_count = len(psutil.pids())
            
            # Load average (Unix-like systems)
            try:
                load_avg = os.getloadavg()
            except (AttributeError, OSError):
                load_avg = (0, 0, 0)  # Windows doesn't have load average
            
            duration_ms = (time.time() - start_time) * 1000
            
            details = {
                "cpu_usage_percent": cpu_percent,
                "memory_usage_percent": memory_percent,
                "memory_available_gb": round(memory.available / 1024**3, 2),
                "memory_total_gb": round(memory.total / 1024**3, 2),
                "disk_usage_percent": disk_percent,
                "disk_free_gb": round(disk.free / 1024**3, 2),
                "disk_total_gb": round(disk.total / 1024**3, 2),
                "network_bytes_sent": network.bytes_sent,
                "network_bytes_recv": network.bytes_recv,
                "process_count": process_count,
                "load_average_1m": load_avg[0],
                "load_average_5m": load_avg[1],
                "load_average_15m": load_avg[2]
            }
            
            # Determine status based on thresholds
            critical_issues = []
            warning_issues = []
            
            if cpu_percent > self.thresholds['cpu_critical']:
                critical_issues.append(f"CPU usage critical ({cpu_percent:.1f}%)")
            elif cpu_percent > self.thresholds['cpu_warning']:
                warning_issues.append(f"CPU usage high ({cpu_percent:.1f}%)")
            
            if memory_percent > self.thresholds['memory_critical']:
                critical_issues.append(f"Memory usage critical ({memory_percent:.1f}%)")
            elif memory_percent > self.thresholds['memory_warning']:
                warning_issues.append(f"Memory usage high ({memory_percent:.1f}%)")
            
            if disk_percent > self.thresholds['disk_critical']:
                critical_issues.append(f"Disk usage critical ({disk_percent:.1f}%)")
            elif disk_percent > self.thresholds['disk_warning']:
                warning_issues.append(f"Disk usage high ({disk_percent:.1f}%)")
            
            if critical_issues:
                status = HealthStatus.CRITICAL
                message = "; ".join(critical_issues)
            elif warning_issues:
                status = HealthStatus.WARNING
                message = "; ".join(warning_issues)
            else:
                status = HealthStatus.HEALTHY
                message = f"System resources healthy (CPU: {cpu_percent:.1f}%, Memory: {memory_percent:.1f}%, Disk: {disk_percent:.1f}%)"
            
            return HealthCheckResult(
                name="System Resources",
                status=status,
                message=message,
                details=details,
                duration_ms=duration_ms,
                timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            return HealthCheckResult(
                name="System Resources",
                status=HealthStatus.CRITICAL,
                message=f"Failed to check system resources: {str(e)}",
                details={"error": str(e)},
                duration_ms=(time.time() - start_time) * 1000,
                timestamp=datetime.utcnow()
            )

    def check_docker_containers(self) -> HealthCheckResult:
        """Check Docker container health"""
        start_time = time.time()
        
        try:
            client = docker.from_env()
            
            # Get all containers related to the project
            containers = client.containers.list(all=True, 
                                              filters={"label": "com.docker.compose.project=financial-planning"})
            
            if not containers:
                # Fallback: check by name pattern
                all_containers = client.containers.list(all=True)
                containers = [c for c in all_containers if 'financial-planning' in c.name]
            
            container_status = {}
            running_count = 0
            total_count = len(containers)
            
            for container in containers:
                status = container.status
                container_status[container.name] = {
                    "status": status,
                    "image": container.image.tags[0] if container.image.tags else "unknown",
                    "created": container.attrs['Created'],
                    "ports": container.ports
                }
                
                if status == 'running':
                    running_count += 1
            
            duration_ms = (time.time() - start_time) * 1000
            
            details = {
                "total_containers": total_count,
                "running_containers": running_count,
                "stopped_containers": total_count - running_count,
                "containers": container_status
            }
            
            # Determine status
            if total_count == 0:
                status = HealthStatus.WARNING
                message = "No project containers found"
            elif running_count == total_count:
                status = HealthStatus.HEALTHY
                message = f"All {total_count} containers running"
            elif running_count == 0:
                status = HealthStatus.CRITICAL
                message = f"All {total_count} containers stopped"
            else:
                status = HealthStatus.WARNING
                message = f"{running_count}/{total_count} containers running"
            
            return HealthCheckResult(
                name="Docker Containers",
                status=status,
                message=message,
                details=details,
                duration_ms=duration_ms,
                timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            return HealthCheckResult(
                name="Docker Containers",
                status=HealthStatus.WARNING,
                message=f"Docker check failed: {str(e)}",
                details={"error": str(e)},
                duration_ms=(time.time() - start_time) * 1000,
                timestamp=datetime.utcnow()
            )

    async def check_external_services(self) -> HealthCheckResult:
        """Check external service dependencies"""
        start_time = time.time()
        
        external_services = [
            {"name": "OpenAI API", "url": "https://api.openai.com/v1/models", "timeout": 10},
            {"name": "Alpha Vantage", "url": "https://www.alphavantage.co", "timeout": 10},
            {"name": "IEX Cloud", "url": "https://cloud.iexapis.com", "timeout": 10}
        ]
        
        service_status = {}
        healthy_count = 0
        
        async with httpx.AsyncClient() as client:
            for service in external_services:
                try:
                    response = await client.get(service["url"], timeout=service["timeout"])
                    if response.status_code < 500:
                        service_status[service["name"]] = {
                            "status": "healthy",
                            "status_code": response.status_code,
                            "response_time_ms": response.elapsed.total_seconds() * 1000
                        }
                        healthy_count += 1
                    else:
                        service_status[service["name"]] = {
                            "status": "degraded",
                            "status_code": response.status_code,
                            "response_time_ms": response.elapsed.total_seconds() * 1000
                        }
                except Exception as e:
                    service_status[service["name"]] = {
                        "status": "unhealthy",
                        "error": str(e)
                    }
        
        duration_ms = (time.time() - start_time) * 1000
        
        details = {
            "services_checked": len(external_services),
            "healthy_services": healthy_count,
            "service_details": service_status
        }
        
        # Determine overall external service status
        if healthy_count == len(external_services):
            status = HealthStatus.HEALTHY
            message = f"All {len(external_services)} external services accessible"
        elif healthy_count > len(external_services) // 2:
            status = HealthStatus.WARNING
            message = f"{healthy_count}/{len(external_services)} external services accessible"
        else:
            status = HealthStatus.CRITICAL
            message = f"Only {healthy_count}/{len(external_services)} external services accessible"
        
        return HealthCheckResult(
            name="External Services",
            status=status,
            message=message,
            details=details,
            duration_ms=duration_ms,
            timestamp=datetime.utcnow()
        )

    async def run_all_checks(self) -> List[HealthCheckResult]:
        """Run all health checks"""
        self.log_info("Starting comprehensive health check...")
        
        # Run checks concurrently where possible
        check_tasks = [
            self.check_api_health(),
            self.check_database_health(),
            self.check_redis_health(),
            self.check_external_services()
        ]
        
        # Run async checks
        async_results = await asyncio.gather(*check_tasks, return_exceptions=True)
        
        # Run sync checks
        system_check = self.check_system_resources()
        docker_check = self.check_docker_containers()
        
        # Combine all results
        self.results = []
        
        for result in async_results:
            if isinstance(result, Exception):
                self.results.append(HealthCheckResult(
                    name="Unknown Check",
                    status=HealthStatus.CRITICAL,
                    message=f"Check failed: {str(result)}",
                    details={"error": str(result)},
                    duration_ms=0,
                    timestamp=datetime.utcnow()
                ))
            else:
                self.results.append(result)
        
        self.results.extend([system_check, docker_check])
        
        # Determine overall status
        self.overall_status = self._calculate_overall_status()
        
        return self.results

    def _calculate_overall_status(self) -> HealthStatus:
        """Calculate overall system health status"""
        critical_count = sum(1 for r in self.results if r.status == HealthStatus.CRITICAL)
        warning_count = sum(1 for r in self.results if r.status == HealthStatus.WARNING)
        
        if critical_count > 0:
            return HealthStatus.CRITICAL
        elif warning_count > 0:
            return HealthStatus.WARNING
        else:
            return HealthStatus.HEALTHY

    def print_results(self, verbose: bool = False):
        """Print health check results"""
        print("\n" + "=" * 80)
        print("🏥 Financial Planning System - Health Check Report")
        print("=" * 80)
        print(f"Timestamp: {datetime.utcnow().isoformat()}Z")
        print(f"Overall Status: {self._format_status(self.overall_status)}")
        print("=" * 80)
        
        for result in self.results:
            status_icon = self._get_status_icon(result.status)
            status_color = self._get_status_color(result.status)
            
            print(f"\n{status_icon} {result.name}")
            print(f"   Status: {status_color}{result.status.value.upper()}{Colors.NC}")
            print(f"   Message: {result.message}")
            print(f"   Duration: {result.duration_ms:.1f}ms")
            
            if verbose and result.details:
                print("   Details:")
                for key, value in result.details.items():
                    if isinstance(value, dict):
                        print(f"     {key}:")
                        for subkey, subvalue in value.items():
                            print(f"       {subkey}: {subvalue}")
                    else:
                        print(f"     {key}: {value}")
        
        print("\n" + "=" * 80)
        
        # Summary
        total_checks = len(self.results)
        healthy_checks = sum(1 for r in self.results if r.status == HealthStatus.HEALTHY)
        warning_checks = sum(1 for r in self.results if r.status == HealthStatus.WARNING)
        critical_checks = sum(1 for r in self.results if r.status == HealthStatus.CRITICAL)
        
        print("📊 Summary:")
        print(f"   Total Checks: {total_checks}")
        print(f"   {Colors.GREEN}Healthy: {healthy_checks}{Colors.NC}")
        print(f"   {Colors.YELLOW}Warnings: {warning_checks}{Colors.NC}")
        print(f"   {Colors.RED}Critical: {critical_checks}{Colors.NC}")
        print("=" * 80)

    def _format_status(self, status: HealthStatus) -> str:
        """Format status with color"""
        color = self._get_status_color(status)
        return f"{color}{status.value.upper()}{Colors.NC}"

    def _get_status_icon(self, status: HealthStatus) -> str:
        """Get icon for status"""
        icons = {
            HealthStatus.HEALTHY: "✅",
            HealthStatus.WARNING: "⚠️",
            HealthStatus.CRITICAL: "❌",
            HealthStatus.UNKNOWN: "❓"
        }
        return icons.get(status, "❓")

    def _get_status_color(self, status: HealthStatus) -> str:
        """Get color for status"""
        colors = {
            HealthStatus.HEALTHY: Colors.GREEN,
            HealthStatus.WARNING: Colors.YELLOW,
            HealthStatus.CRITICAL: Colors.RED,
            HealthStatus.UNKNOWN: Colors.PURPLE
        }
        return colors.get(status, Colors.NC)

    def export_json(self, filename: str = None):
        """Export results to JSON"""
        if not filename:
            filename = f"health_check_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        
        export_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "overall_status": self.overall_status.value,
            "checks": [
                {
                    "name": result.name,
                    "status": result.status.value,
                    "message": result.message,
                    "details": result.details,
                    "duration_ms": result.duration_ms,
                    "timestamp": result.timestamp.isoformat() + "Z"
                }
                for result in self.results
            ]
        }
        
        with open(filename, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
        
        self.log_success(f"Health check results exported to {filename}")

async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Financial Planning System Health Check")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--json", "-j", type=str, help="Export results to JSON file")
    parser.add_argument("--config", "-c", type=str, help="Configuration file path")
    parser.add_argument("--api-url", default="http://localhost:8000", help="API URL")
    parser.add_argument("--db-host", default="localhost", help="Database host")
    parser.add_argument("--redis-host", default="localhost", help="Redis host")
    parser.add_argument("--exit-code", action="store_true", help="Exit with non-zero code on failures")
    
    args = parser.parse_args()
    
    # Load configuration
    config = {
        "api_url": args.api_url,
        "db_host": args.db_host,
        "redis_host": args.redis_host
    }
    
    if args.config and os.path.exists(args.config):
        with open(args.config, 'r') as f:
            file_config = json.load(f)
            config.update(file_config)
    
    # Run health checks
    checker = HealthChecker(config)
    await checker.run_all_checks()
    
    # Output results
    checker.print_results(verbose=args.verbose)
    
    # Export to JSON if requested
    if args.json:
        checker.export_json(args.json)
    
    # Exit with appropriate code
    if args.exit_code:
        if checker.overall_status == HealthStatus.CRITICAL:
            sys.exit(2)
        elif checker.overall_status == HealthStatus.WARNING:
            sys.exit(1)
        else:
            sys.exit(0)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}[WARNING]{Colors.NC} Health check interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"{Colors.RED}[ERROR]{Colors.NC} Health check failed: {e}")
        sys.exit(1)