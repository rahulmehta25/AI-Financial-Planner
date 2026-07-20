#!/usr/bin/env python3
"""
Comprehensive Health Check Script for Financial Planning System

This script verifies that all components of the system are running correctly:
- Database connectivity
- Redis connectivity  
- API endpoints responsiveness
- External service integrations
- System resource usage

Usage:
python health_check.py [--detailed] [--json] [--config-file config.json]

Exit codes:
0 - All checks passed
1 - Critical failures detected
2 - Warning-level issues found
"""

import asyncio
import json
import sys
import time
import argparse
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import httpx
import asyncpg
import redis.asyncio as redis
import psutil

# Import application components
try:
    from app.core.config import settings
    from app.database.base import get_async_session
    from sqlalchemy import text
except ImportError as e:
    print(f"Warning: Could not import app components: {e}")
    settings = None


class CheckStatus(Enum):
    """Health check status levels"""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass
class HealthCheckResult:
    """Result of a health check"""
    name: str
    status: CheckStatus
    message: str
    details: Dict[str, Any]
    response_time_ms: float
    timestamp: str


class HealthChecker:
    """Comprehensive health checker for the financial planning system"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.results: List[HealthCheckResult] = []
        self.start_time = time.time()
        
        # Default endpoints and timeouts
        self.api_base_url = self.config.get('api_base_url', 'http://localhost:8000')
        self.frontend_url = self.config.get('frontend_url', 'http://localhost:3000')
        self.timeout = self.config.get('timeout', 10.0)
        
    async def run_all_checks(self, detailed: bool = False) -> Dict[str, Any]:
        """Run all health checks"""
        print("🏥 Starting comprehensive health check...")
        print("=" * 60)
        
        # Core system checks
        await self._check_system_resources()
        await self._check_database_connectivity()
        await self._check_redis_connectivity()
        
        # API checks
        await self._check_api_health()
        await self._check_api_endpoints()
        
        # External service checks
        if detailed:
            await self._check_external_services()
            await self._check_ml_services()
            await self._check_banking_integrations()
        
        # Frontend check
        await self._check_frontend_availability()
        
        # Generate summary
        return self._generate_summary()
    
    async def _check_system_resources(self):
        """Check system resource usage"""
        print("🖥️  Checking system resources...")
        
        start_time = time.time()
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            
            # Disk usage
            disk = psutil.disk_usage('/')
            
            # Network connections
            connections = len(psutil.net_connections())
            
            details = {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_available_gb": round(memory.available / (1024**3), 2),
                "disk_percent": disk.percent,
                "disk_free_gb": round(disk.free / (1024**3), 2),
                "network_connections": connections
            }
            
            # Determine status
            status = CheckStatus.HEALTHY
            message = "System resources are healthy"
            
            if cpu_percent > 80:
                status = CheckStatus.WARNING
                message = f"High CPU usage: {cpu_percent}%"
            elif memory.percent > 80:
                status = CheckStatus.WARNING
                message = f"High memory usage: {memory.percent}%"
            elif disk.percent > 90:
                status = CheckStatus.CRITICAL
                message = f"Low disk space: {disk.percent}% used"
            
            print(f"   📊 CPU: {cpu_percent}%, Memory: {memory.percent}%, Disk: {disk.percent}%")
            
        except Exception as e:
            status = CheckStatus.WARNING
            message = f"Could not check system resources: {str(e)}"
            details = {"error": str(e)}
            print(f"   ⚠️  {message}")
        
        response_time = (time.time() - start_time) * 1000
        self.results.append(HealthCheckResult(
            name="system_resources",
            status=status,
            message=message,
            details=details,
            response_time_ms=response_time,
            timestamp=datetime.now().isoformat()
        ))
    
    async def _check_database_connectivity(self):
        """Check database connectivity and performance"""
        print("🗄️  Checking database connectivity...")
        
        start_time = time.time()
        try:
            if settings:
                db_url = settings.DATABASE_URL
                # Parse connection string for asyncpg
                if db_url.startswith("postgresql+asyncpg://"):
                    db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
                
                conn = await asyncpg.connect(db_url)
                
                # Test basic query
                result = await conn.fetchval("SELECT version()")
                
                # Test performance with a simple query
                perf_start = time.time()
                await conn.fetchval("SELECT COUNT(*) FROM information_schema.tables")
                query_time = (time.time() - perf_start) * 1000
                
                await conn.close()
                
                details = {
                    "version": result,
                    "query_time_ms": round(query_time, 2),
                    "connection_successful": True
                }
                
                status = CheckStatus.HEALTHY
                message = "Database connection successful"
                
                if query_time > 1000:  # 1 second
                    status = CheckStatus.WARNING
                    message = f"Slow database response: {query_time:.0f}ms"
                
                print(f"   ✅ Database connected: {result.split()[0]} {result.split()[1]}")
                print(f"   ⏱️  Query time: {query_time:.2f}ms")
                
            else:
                # Fallback test without settings
                raise Exception("Settings not available")
                
        except Exception as e:
            status = CheckStatus.CRITICAL
            message = f"Database connection failed: {str(e)}"
            details = {"error": str(e)}
            print(f"   ❌ {message}")
        
        response_time = (time.time() - start_time) * 1000
        self.results.append(HealthCheckResult(
            name="database_connectivity",
            status=status,
            message=message,
            details=details,
            response_time_ms=response_time,
            timestamp=datetime.now().isoformat()
        ))
    
    async def _check_redis_connectivity(self):
        """Check Redis connectivity and performance"""
        print("🔴 Checking Redis connectivity...")
        
        start_time = time.time()
        try:
            if settings:
                redis_url = settings.REDIS_URL
            else:
                redis_url = "redis://localhost:6379"
            
            r = redis.from_url(redis_url)
            
            # Test basic operations
            await r.ping()
            
            # Test set/get performance
            test_key = "health_check_test"
            test_value = "test_value"
            
            perf_start = time.time()
            await r.set(test_key, test_value, ex=60)  # Expire in 60 seconds
            retrieved = await r.get(test_key)
            await r.delete(test_key)
            operation_time = (time.time() - perf_start) * 1000
            
            # Get Redis info
            info = await r.info()
            
            await r.close()
            
            details = {
                "ping_successful": True,
                "operation_time_ms": round(operation_time, 2),
                "redis_version": info.get("redis_version"),
                "connected_clients": info.get("connected_clients"),
                "used_memory_human": info.get("used_memory_human"),
                "uptime_in_seconds": info.get("uptime_in_seconds")
            }
            
            status = CheckStatus.HEALTHY
            message = "Redis connection successful"
            
            if operation_time > 100:  # 100ms
                status = CheckStatus.WARNING
                message = f"Slow Redis response: {operation_time:.0f}ms"
            
            print(f"   ✅ Redis connected: v{info.get('redis_version')}")
            print(f"   ⏱️  Operation time: {operation_time:.2f}ms")
            
        except Exception as e:
            status = CheckStatus.CRITICAL
            message = f"Redis connection failed: {str(e)}"
            details = {"error": str(e)}
            print(f"   ❌ {message}")
        
        response_time = (time.time() - start_time) * 1000
        self.results.append(HealthCheckResult(
            name="redis_connectivity",
            status=status,
            message=message,
            details=details,
            response_time_ms=response_time,
            timestamp=datetime.now().isoformat()
        ))
    
    async def _check_api_health(self):
        """Check main API health endpoint"""
        print("🌐 Checking API health...")
        
        start_time = time.time()
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.api_base_url}/health")
                
                if response.status_code == 200:
                    health_data = response.json()
                    
                    details = {
                        "status_code": response.status_code,
                        "response_data": health_data,
                        "headers": dict(response.headers)
                    }
                    
                    status = CheckStatus.HEALTHY
                    message = f"API health check passed: {health_data.get('status')}"
                    
                    print(f"   ✅ API health: {health_data.get('status')}")
                    print(f"   📋 Version: {health_data.get('version', 'Unknown')}")
                    
                else:
                    status = CheckStatus.WARNING
                    message = f"API health check returned {response.status_code}"
                    details = {"status_code": response.status_code}
                    print(f"   ⚠️  {message}")
                    
        except Exception as e:
            status = CheckStatus.CRITICAL
            message = f"API health check failed: {str(e)}"
            details = {"error": str(e)}
            print(f"   ❌ {message}")
        
        response_time = (time.time() - start_time) * 1000
        self.results.append(HealthCheckResult(
            name="api_health",
            status=status,
            message=message,
            details=details,
            response_time_ms=response_time,
            timestamp=datetime.now().isoformat()
        ))
    
    async def _check_api_endpoints(self):
        """Check key API endpoints"""
        print("🔗 Checking API endpoints...")
        
        endpoints = [
            ("/api/v1/auth/register", "POST", {"test": "data"}),
            ("/api/v1/financial-profiles/", "GET", None),
            ("/api/v1/goals/", "GET", None),
            ("/api/v1/monte-carlo/run", "POST", {"test": "data"}),
            ("/docs", "GET", None),
        ]
        
        endpoint_results = {}
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for endpoint, method, test_data in endpoints:
                start_time = time.time()
                try:
                    url = f"{self.api_base_url}{endpoint}"
                    
                    if method == "GET":
                        response = await client.get(url)
                    elif method == "POST":
                        response = await client.post(url, json=test_data)
                    
                    response_time = (time.time() - start_time) * 1000
                    
                    # 401/422 are acceptable for unauthenticated requests
                    if response.status_code in [200, 401, 422]:
                        endpoint_results[endpoint] = {
                            "status": "accessible",
                            "status_code": response.status_code,
                            "response_time_ms": round(response_time, 2)
                        }
                        print(f"   ✅ {endpoint}: {response.status_code} ({response_time:.0f}ms)")
                    else:
                        endpoint_results[endpoint] = {
                            "status": "error",
                            "status_code": response.status_code,
                            "response_time_ms": round(response_time, 2)
                        }
                        print(f"   ⚠️  {endpoint}: {response.status_code}")
                        
                except Exception as e:
                    endpoint_results[endpoint] = {
                        "status": "failed",
                        "error": str(e)
                    }
                    print(f"   ❌ {endpoint}: {str(e)}")
        
        # Determine overall status
        accessible_count = sum(1 for r in endpoint_results.values() if r.get("status") == "accessible")
        total_count = len(endpoints)
        
        if accessible_count == total_count:
            status = CheckStatus.HEALTHY
            message = "All API endpoints accessible"
        elif accessible_count > total_count * 0.7:
            status = CheckStatus.WARNING
            message = f"{accessible_count}/{total_count} endpoints accessible"
        else:
            status = CheckStatus.CRITICAL
            message = f"Only {accessible_count}/{total_count} endpoints accessible"
        
        response_time = sum(r.get("response_time_ms", 0) for r in endpoint_results.values()) / len(endpoint_results)
        
        self.results.append(HealthCheckResult(
            name="api_endpoints",
            status=status,
            message=message,
            details=endpoint_results,
            response_time_ms=response_time,
            timestamp=datetime.now().isoformat()
        ))
    
    async def _check_external_services(self):
        """Check external service integrations"""
        print("🌍 Checking external services...")
        
        external_services = {
            "openai": getattr(settings, 'OPENAI_API_KEY', None) if settings else None,
            "anthropic": getattr(settings, 'ANTHROPIC_API_KEY', None) if settings else None,
            "plaid": getattr(settings, 'PLAID_CLIENT_ID', None) if settings else None,
        }
        
        service_results = {}
        
        for service, api_key in external_services.items():
            if api_key:
                service_results[service] = {"configured": True, "status": "configured"}
                print(f"   ✅ {service.title()}: Configured")
            else:
                service_results[service] = {"configured": False, "status": "not_configured"}
                print(f"   ⚠️  {service.title()}: Not configured")
        
        configured_count = sum(1 for r in service_results.values() if r["configured"])
        total_count = len(external_services)
        
        if configured_count > 0:
            status = CheckStatus.HEALTHY if configured_count > total_count * 0.5 else CheckStatus.WARNING
            message = f"{configured_count}/{total_count} external services configured"
        else:
            status = CheckStatus.WARNING
            message = "No external services configured"
        
        self.results.append(HealthCheckResult(
            name="external_services",
            status=status,
            message=message,
            details=service_results,
            response_time_ms=0,
            timestamp=datetime.now().isoformat()
        ))
    
    async def _check_ml_services(self):
        """Check ML service availability"""
        print("🤖 Checking ML services...")
        
        start_time = time.time()
        try:
            # Try to access ML recommendation endpoint
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.api_base_url}/api/v1/ml/recommendations/1")
                
                # 404 or 500 is acceptable if no profile exists or ML not trained
                if response.status_code in [200, 404, 500, 503]:
                    status = CheckStatus.HEALTHY
                    message = "ML service endpoint accessible"
                    details = {"status_code": response.status_code}
                    print(f"   ✅ ML service: Accessible ({response.status_code})")
                else:
                    status = CheckStatus.WARNING
                    message = f"ML service returned {response.status_code}"
                    details = {"status_code": response.status_code}
                    print(f"   ⚠️  ML service: {message}")
                    
        except Exception as e:
            status = CheckStatus.WARNING
            message = f"ML service check failed: {str(e)}"
            details = {"error": str(e)}
            print(f"   ⚠️  {message}")
        
        response_time = (time.time() - start_time) * 1000
        self.results.append(HealthCheckResult(
            name="ml_services",
            status=status,
            message=message,
            details=details,
            response_time_ms=response_time,
            timestamp=datetime.now().isoformat()
        ))
    
    async def _check_banking_integrations(self):
        """Check banking integration services"""
        print("🏦 Checking banking integrations...")
        
        start_time = time.time()
        try:
            # Try to access banking endpoint
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.api_base_url}/api/v1/banking/accounts")
                
                # 401 is expected without authentication
                if response.status_code in [200, 401]:
                    status = CheckStatus.HEALTHY
                    message = "Banking service endpoint accessible"
                    details = {"status_code": response.status_code}
                    print(f"   ✅ Banking service: Accessible ({response.status_code})")
                else:
                    status = CheckStatus.WARNING
                    message = f"Banking service returned {response.status_code}"
                    details = {"status_code": response.status_code}
                    print(f"   ⚠️  Banking service: {message}")
                    
        except Exception as e:
            status = CheckStatus.WARNING
            message = f"Banking service check failed: {str(e)}"
            details = {"error": str(e)}
            print(f"   ⚠️  {message}")
        
        response_time = (time.time() - start_time) * 1000
        self.results.append(HealthCheckResult(
            name="banking_integrations",
            status=status,
            message=message,
            details=details,
            response_time_ms=response_time,
            timestamp=datetime.now().isoformat()
        ))
    
    async def _check_frontend_availability(self):
        """Check frontend application availability"""
        print("🖥️  Checking frontend availability...")
        
        start_time = time.time()
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(self.frontend_url)
                
                if response.status_code == 200:
                    status = CheckStatus.HEALTHY
                    message = "Frontend application accessible"
                    details = {
                        "status_code": response.status_code,
                        "content_length": len(response.content)
                    }
                    print(f"   ✅ Frontend: Accessible")
                else:
                    status = CheckStatus.WARNING
                    message = f"Frontend returned {response.status_code}"
                    details = {"status_code": response.status_code}
                    print(f"   ⚠️  Frontend: {message}")
                    
        except Exception as e:
            status = CheckStatus.WARNING
            message = f"Frontend not accessible: {str(e)}"
            details = {"error": str(e)}
            print(f"   ⚠️  {message}")
        
        response_time = (time.time() - start_time) * 1000
        self.results.append(HealthCheckResult(
            name="frontend_availability",
            status=status,
            message=message,
            details=details,
            response_time_ms=response_time,
            timestamp=datetime.now().isoformat()
        ))
    
    def _generate_summary(self) -> Dict[str, Any]:
        """Generate health check summary"""
        total_checks = len(self.results)
        healthy_checks = sum(1 for r in self.results if r.status == CheckStatus.HEALTHY)
        warning_checks = sum(1 for r in self.results if r.status == CheckStatus.WARNING)
        critical_checks = sum(1 for r in self.results if r.status == CheckStatus.CRITICAL)
        
        overall_status = CheckStatus.HEALTHY
        if critical_checks > 0:
            overall_status = CheckStatus.CRITICAL
        elif warning_checks > 0:
            overall_status = CheckStatus.WARNING
        
        total_time = time.time() - self.start_time
        
        summary = {
            "overall_status": overall_status.value,
            "timestamp": datetime.now().isoformat(),
            "total_checks": total_checks,
            "healthy_checks": healthy_checks,
            "warning_checks": warning_checks,
            "critical_checks": critical_checks,
            "total_time_seconds": round(total_time, 2),
            "results": [asdict(result) for result in self.results]
        }
        
        # Print summary
        print("\n" + "=" * 60)
        print("📋 HEALTH CHECK SUMMARY")
        print("=" * 60)
        print(f"Overall Status: {self._format_status(overall_status)}")
        print(f"Total Checks: {total_checks}")
        print(f"✅ Healthy: {healthy_checks}")
        print(f"⚠️  Warnings: {warning_checks}")
        print(f"❌ Critical: {critical_checks}")
        print(f"⏱️  Total Time: {total_time:.2f} seconds")
        
        if critical_checks > 0:
            print("\n🚨 CRITICAL ISSUES:")
            for result in self.results:
                if result.status == CheckStatus.CRITICAL:
                    print(f"   ❌ {result.name}: {result.message}")
        
        if warning_checks > 0:
            print("\n⚠️  WARNINGS:")
            for result in self.results:
                if result.status == CheckStatus.WARNING:
                    print(f"   ⚠️  {result.name}: {result.message}")
        
        return summary
    
    def _format_status(self, status: CheckStatus) -> str:
        """Format status with emoji"""
        emoji_map = {
            CheckStatus.HEALTHY: "✅ HEALTHY",
            CheckStatus.WARNING: "⚠️  WARNING",
            CheckStatus.CRITICAL: "❌ CRITICAL",
            CheckStatus.UNKNOWN: "❓ UNKNOWN"
        }
        return emoji_map.get(status, str(status.value))


async def main():
    """Main health check function"""
    parser = argparse.ArgumentParser(description="Financial Planning System Health Check")
    parser.add_argument("--detailed", action="store_true", help="Run detailed checks including external services")
    parser.add_argument("--json", action="store_true", help="Output results in JSON format")
    parser.add_argument("--config-file", help="Configuration file path")
    parser.add_argument("--save-report", help="Save detailed report to file")
    
    args = parser.parse_args()
    
    # Load configuration
    config = {}
    if args.config_file:
        try:
            with open(args.config_file, 'r') as f:
                config = json.load(f)
        except Exception as e:
            print(f"Warning: Could not load config file: {e}")
    
    # Run health checks
    checker = HealthChecker(config)
    summary = await checker.run_all_checks(detailed=args.detailed)
    
    # Output results
    if args.json:
        print(json.dumps(summary, indent=2))
    
    # Save report if requested
    if args.save_report:
        with open(args.save_report, 'w') as f:
            json.dump(summary, f, indent=2)
        print(f"\n📄 Report saved to: {args.save_report}")
    
    # Exit with appropriate code
    if summary["overall_status"] == "critical":
        sys.exit(1)
    elif summary["overall_status"] == "warning":
        sys.exit(2)
    else:
        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())