#!/usr/bin/env python3
"""
Comprehensive Performance Profiling and Optimization Script
Profiles backend API response times, database queries, and generates optimization report
"""

import asyncio
import time
import json
import psutil
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import httpx
import asyncpg
import redis.asyncio as aioredis
from dataclasses import dataclass, asdict
import numpy as np
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich import print as rprint
import matplotlib.pyplot as plt
import seaborn as sns

console = Console()

@dataclass
class EndpointMetrics:
    """Metrics for API endpoint performance"""
    endpoint: str
    method: str
    avg_response_time: float
    p50: float
    p95: float
    p99: float
    min_time: float
    max_time: float
    request_count: int
    error_rate: float
    throughput: float

@dataclass
class DatabaseMetrics:
    """Database performance metrics"""
    total_queries: int
    slow_queries: List[Dict]
    avg_query_time: float
    connection_pool_usage: float
    cache_hit_ratio: float
    index_usage_ratio: float
    table_bloat: Dict[str, float]
    missing_indexes: List[str]

@dataclass
class CacheMetrics:
    """Cache performance metrics"""
    hit_ratio: float
    miss_ratio: float
    avg_get_time: float
    avg_set_time: float
    memory_usage_mb: float
    eviction_rate: float
    key_count: int

@dataclass
class SystemMetrics:
    """System resource metrics"""
    cpu_usage_percent: float
    memory_usage_percent: float
    disk_io_read_mb: float
    disk_io_write_mb: float
    network_in_mb: float
    network_out_mb: float
    open_file_descriptors: int

class PerformanceProfiler:
    """Main performance profiling class"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.db_url = "postgresql://user:password@localhost/financial_planning"
        self.redis_url = "redis://localhost:6379"
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "endpoints": [],
            "database": None,
            "cache": None,
            "system": None,
            "optimizations": []
        }
    
    async def profile_endpoints(self) -> List[EndpointMetrics]:
        """Profile all API endpoints"""
        console.print("[bold cyan]Profiling API Endpoints...[/bold cyan]")
        
        endpoints = [
            ("GET", "/api/v1/health"),
            ("GET", "/api/v1/users/me"),
            ("GET", "/api/v1/financial-profiles"),
            ("GET", "/api/v1/goals"),
            ("GET", "/api/v1/investments"),
            ("POST", "/api/v1/simulations/monte-carlo"),
            ("GET", "/api/v1/market-data/stocks/AAPL"),
            ("GET", "/api/v1/ml-recommendations"),
            ("POST", "/api/v1/pdf/export"),
        ]
        
        metrics = []
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            for method, endpoint in endpoints:
                response_times = []
                errors = 0
                
                # Warm up
                for _ in range(5):
                    try:
                        if method == "GET":
                            await client.get(f"{self.base_url}{endpoint}")
                        else:
                            await client.post(f"{self.base_url}{endpoint}", json={})
                    except:
                        pass
                
                # Actual measurements
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    console=console
                ) as progress:
                    task = progress.add_task(f"Testing {endpoint}...", total=100)
                    
                    start_batch = time.time()
                    for i in range(100):
                        start = time.perf_counter()
                        try:
                            if method == "GET":
                                response = await client.get(f"{self.base_url}{endpoint}")
                            else:
                                response = await client.post(f"{self.base_url}{endpoint}", json={
                                    "initial_amount": 10000,
                                    "monthly_contribution": 500,
                                    "years": 30,
                                    "risk_level": "moderate"
                                })
                            
                            elapsed = (time.perf_counter() - start) * 1000  # ms
                            response_times.append(elapsed)
                            
                            if response.status_code >= 400:
                                errors += 1
                        except Exception as e:
                            errors += 1
                            console.print(f"[red]Error testing {endpoint}: {e}[/red]")
                        
                        progress.update(task, advance=1)
                    
                    batch_time = time.time() - start_batch
                
                if response_times:
                    metric = EndpointMetrics(
                        endpoint=endpoint,
                        method=method,
                        avg_response_time=statistics.mean(response_times),
                        p50=np.percentile(response_times, 50),
                        p95=np.percentile(response_times, 95),
                        p99=np.percentile(response_times, 99),
                        min_time=min(response_times),
                        max_time=max(response_times),
                        request_count=len(response_times),
                        error_rate=errors / 100,
                        throughput=len(response_times) / batch_time
                    )
                    metrics.append(metric)
        
        return metrics
    
    async def profile_database(self) -> DatabaseMetrics:
        """Profile database performance"""
        console.print("[bold cyan]Profiling Database...[/bold cyan]")
        
        try:
            conn = await asyncpg.connect(self.db_url)
            
            # Get query statistics
            stats = await conn.fetch("""
                SELECT 
                    query,
                    calls,
                    mean_exec_time,
                    max_exec_time,
                    total_exec_time
                FROM pg_stat_statements
                WHERE query NOT LIKE '%pg_stat%'
                ORDER BY mean_exec_time DESC
                LIMIT 20
            """)
            
            slow_queries = [
                {
                    "query": row["query"][:100],
                    "avg_time": row["mean_exec_time"],
                    "calls": row["calls"]
                }
                for row in stats if row["mean_exec_time"] > 100  # > 100ms
            ]
            
            # Cache hit ratio
            cache_stats = await conn.fetchrow("""
                SELECT 
                    sum(heap_blks_hit)/(sum(heap_blks_hit) + sum(heap_blks_read)) as cache_hit_ratio
                FROM pg_statio_user_tables
            """)
            
            # Index usage
            index_stats = await conn.fetchrow("""
                SELECT 
                    sum(idx_scan)/(sum(idx_scan) + sum(seq_scan)) as index_usage_ratio
                FROM pg_stat_user_tables
                WHERE (idx_scan + seq_scan) > 0
            """)
            
            # Table bloat
            bloat_query = await conn.fetch("""
                SELECT 
                    schemaname || '.' || tablename as table_name,
                    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
                    n_dead_tup::float / NULLIF(n_live_tup + n_dead_tup, 0) as bloat_ratio
                FROM pg_stat_user_tables
                WHERE n_live_tup > 1000
                ORDER BY n_dead_tup DESC
                LIMIT 10
            """)
            
            table_bloat = {
                row["table_name"]: row["bloat_ratio"] or 0
                for row in bloat_query
            }
            
            # Missing indexes
            missing_idx = await conn.fetch("""
                SELECT 
                    schemaname || '.' || tablename as table_name,
                    seq_scan,
                    seq_tup_read,
                    idx_scan
                FROM pg_stat_user_tables
                WHERE seq_scan > idx_scan * 2
                    AND seq_tup_read > 100000
                    AND schemaname NOT IN ('pg_catalog', 'information_schema')
                ORDER BY seq_tup_read DESC
                LIMIT 10
            """)
            
            missing_indexes = [
                f"Consider index on {row['table_name']} (seq_scan: {row['seq_scan']})"
                for row in missing_idx
            ]
            
            # Connection pool usage
            pool_stats = await conn.fetchrow("""
                SELECT 
                    count(*) as active_connections,
                    (SELECT setting::int FROM pg_settings WHERE name = 'max_connections') as max_connections
                FROM pg_stat_activity
            """)
            
            await conn.close()
            
            return DatabaseMetrics(
                total_queries=len(stats),
                slow_queries=slow_queries[:10],
                avg_query_time=statistics.mean([row["mean_exec_time"] for row in stats]) if stats else 0,
                connection_pool_usage=(pool_stats["active_connections"] / pool_stats["max_connections"]) * 100,
                cache_hit_ratio=cache_stats["cache_hit_ratio"] or 0,
                index_usage_ratio=index_stats["index_usage_ratio"] or 0,
                table_bloat=table_bloat,
                missing_indexes=missing_indexes
            )
        except Exception as e:
            console.print(f"[yellow]Database profiling skipped: {e}[/yellow]")
            return DatabaseMetrics(
                total_queries=0,
                slow_queries=[],
                avg_query_time=0,
                connection_pool_usage=0,
                cache_hit_ratio=0,
                index_usage_ratio=0,
                table_bloat={},
                missing_indexes=[]
            )
    
    async def profile_cache(self) -> CacheMetrics:
        """Profile Redis cache performance"""
        console.print("[bold cyan]Profiling Cache...[/bold cyan]")
        
        try:
            redis = await aioredis.from_url(self.redis_url)
            
            # Get Redis info
            info = await redis.info()
            
            # Calculate metrics
            keyspace_hits = info.get("keyspace_hits", 0)
            keyspace_misses = info.get("keyspace_misses", 0)
            total_commands = keyspace_hits + keyspace_misses
            
            hit_ratio = keyspace_hits / total_commands if total_commands > 0 else 0
            miss_ratio = keyspace_misses / total_commands if total_commands > 0 else 0
            
            # Test cache operations
            get_times = []
            set_times = []
            
            for i in range(100):
                # SET operation
                key = f"perf_test_{i}"
                value = "x" * 1000  # 1KB value
                
                start = time.perf_counter()
                await redis.set(key, value, ex=60)
                set_times.append((time.perf_counter() - start) * 1000)
                
                # GET operation
                start = time.perf_counter()
                await redis.get(key)
                get_times.append((time.perf_counter() - start) * 1000)
            
            # Cleanup test keys
            for i in range(100):
                await redis.delete(f"perf_test_{i}")
            
            await redis.close()
            
            return CacheMetrics(
                hit_ratio=hit_ratio,
                miss_ratio=miss_ratio,
                avg_get_time=statistics.mean(get_times),
                avg_set_time=statistics.mean(set_times),
                memory_usage_mb=info.get("used_memory", 0) / (1024 * 1024),
                eviction_rate=info.get("evicted_keys", 0) / max(info.get("keyspace_hits", 1), 1),
                key_count=sum(info.get(f"db{i}", {}).get("keys", 0) for i in range(16))
            )
        except Exception as e:
            console.print(f"[yellow]Cache profiling skipped: {e}[/yellow]")
            return CacheMetrics(
                hit_ratio=0,
                miss_ratio=0,
                avg_get_time=0,
                avg_set_time=0,
                memory_usage_mb=0,
                eviction_rate=0,
                key_count=0
            )
    
    async def profile_system(self) -> SystemMetrics:
        """Profile system resource usage"""
        console.print("[bold cyan]Profiling System Resources...[/bold cyan]")
        
        # Initial IO counters
        disk_io_start = psutil.disk_io_counters()
        net_io_start = psutil.net_io_counters()
        
        # Wait for some activity
        await asyncio.sleep(5)
        
        # Final IO counters
        disk_io_end = psutil.disk_io_counters()
        net_io_end = psutil.net_io_counters()
        
        # Calculate rates
        disk_read_mb = (disk_io_end.read_bytes - disk_io_start.read_bytes) / (1024 * 1024)
        disk_write_mb = (disk_io_end.write_bytes - disk_io_start.write_bytes) / (1024 * 1024)
        net_in_mb = (net_io_end.bytes_recv - net_io_start.bytes_recv) / (1024 * 1024)
        net_out_mb = (net_io_end.bytes_sent - net_io_start.bytes_sent) / (1024 * 1024)
        
        process = psutil.Process()
        
        return SystemMetrics(
            cpu_usage_percent=psutil.cpu_percent(interval=1),
            memory_usage_percent=psutil.virtual_memory().percent,
            disk_io_read_mb=disk_read_mb / 5,  # Per second
            disk_io_write_mb=disk_write_mb / 5,
            network_in_mb=net_in_mb / 5,
            network_out_mb=net_out_mb / 5,
            open_file_descriptors=process.num_fds() if hasattr(process, 'num_fds') else 0
        )
    
    def generate_optimizations(self) -> List[Dict[str, Any]]:
        """Generate optimization recommendations"""
        optimizations = []
        
        # Endpoint optimizations
        if self.results["endpoints"]:
            slow_endpoints = [
                ep for ep in self.results["endpoints"]
                if ep["p95"] > 500  # > 500ms P95
            ]
            
            for ep in slow_endpoints:
                optimizations.append({
                    "category": "API Performance",
                    "issue": f"Slow endpoint: {ep['endpoint']}",
                    "impact": "High",
                    "current": f"P95: {ep['p95']:.0f}ms",
                    "recommendation": "Add caching, optimize database queries, or implement pagination",
                    "expected_improvement": "50-70% reduction in response time"
                })
        
        # Database optimizations
        if self.results["database"]:
            db = self.results["database"]
            
            if db["cache_hit_ratio"] < 0.9:
                optimizations.append({
                    "category": "Database",
                    "issue": "Low cache hit ratio",
                    "impact": "High",
                    "current": f"{db['cache_hit_ratio']*100:.1f}%",
                    "recommendation": "Increase shared_buffers, add more RAM, or optimize queries",
                    "expected_improvement": "20-40% query performance improvement"
                })
            
            if db["index_usage_ratio"] < 0.95:
                optimizations.append({
                    "category": "Database",
                    "issue": "Low index usage",
                    "impact": "Medium",
                    "current": f"{db['index_usage_ratio']*100:.1f}%",
                    "recommendation": "Review and add missing indexes",
                    "expected_improvement": "30-50% query performance improvement"
                })
            
            for query in db["slow_queries"][:3]:
                optimizations.append({
                    "category": "Database",
                    "issue": "Slow query detected",
                    "impact": "High",
                    "current": f"Avg time: {query['avg_time']:.0f}ms",
                    "recommendation": f"Optimize query: {query['query'][:50]}...",
                    "expected_improvement": "60-80% reduction in execution time"
                })
        
        # Cache optimizations
        if self.results["cache"]:
            cache = self.results["cache"]
            
            if cache["hit_ratio"] < 0.8:
                optimizations.append({
                    "category": "Caching",
                    "issue": "Low cache hit ratio",
                    "impact": "Medium",
                    "current": f"{cache['hit_ratio']*100:.1f}%",
                    "recommendation": "Review cache TTL, implement cache warming, add more cache layers",
                    "expected_improvement": "25-35% overall performance improvement"
                })
            
            if cache["eviction_rate"] > 0.1:
                optimizations.append({
                    "category": "Caching",
                    "issue": "High cache eviction rate",
                    "impact": "Medium",
                    "current": f"{cache['eviction_rate']*100:.1f}%",
                    "recommendation": "Increase Redis memory limit or optimize cache usage",
                    "expected_improvement": "15-25% cache performance improvement"
                })
        
        # System optimizations
        if self.results["system"]:
            sys = self.results["system"]
            
            if sys["cpu_usage_percent"] > 70:
                optimizations.append({
                    "category": "System",
                    "issue": "High CPU usage",
                    "impact": "High",
                    "current": f"{sys['cpu_usage_percent']:.1f}%",
                    "recommendation": "Profile CPU-intensive operations, add worker processes, or scale horizontally",
                    "expected_improvement": "30-40% reduction in CPU usage"
                })
            
            if sys["memory_usage_percent"] > 80:
                optimizations.append({
                    "category": "System",
                    "issue": "High memory usage",
                    "impact": "High",
                    "current": f"{sys['memory_usage_percent']:.1f}%",
                    "recommendation": "Optimize memory usage, fix memory leaks, or increase RAM",
                    "expected_improvement": "20-30% reduction in memory usage"
                })
        
        return optimizations
    
    def create_visualizations(self):
        """Create performance visualization charts"""
        if not self.results["endpoints"]:
            return
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('Performance Profiling Results', fontsize=16)
        
        # Response time distribution
        endpoints = self.results["endpoints"]
        labels = [ep["endpoint"].split("/")[-1] or "root" for ep in endpoints]
        p95_times = [ep["p95"] for ep in endpoints]
        
        axes[0, 0].barh(labels, p95_times)
        axes[0, 0].set_xlabel('P95 Response Time (ms)')
        axes[0, 0].set_title('API Endpoint Response Times')
        axes[0, 0].axvline(x=200, color='g', linestyle='--', label='Good (<200ms)')
        axes[0, 0].axvline(x=500, color='y', linestyle='--', label='Acceptable (<500ms)')
        axes[0, 0].axvline(x=1000, color='r', linestyle='--', label='Slow (>1000ms)')
        axes[0, 0].legend()
        
        # Throughput comparison
        throughputs = [ep["throughput"] for ep in endpoints]
        axes[0, 1].bar(labels, throughputs)
        axes[0, 1].set_ylabel('Requests/Second')
        axes[0, 1].set_title('Endpoint Throughput')
        axes[0, 1].tick_params(axis='x', rotation=45)
        
        # Database metrics
        if self.results["database"]:
            db = self.results["database"]
            metrics = ['Cache Hit', 'Index Usage', 'Connection Usage']
            values = [
                db["cache_hit_ratio"] * 100,
                db["index_usage_ratio"] * 100,
                db["connection_pool_usage"]
            ]
            
            axes[1, 0].bar(metrics, values)
            axes[1, 0].set_ylabel('Percentage (%)')
            axes[1, 0].set_title('Database Performance Metrics')
            axes[1, 0].axhline(y=90, color='g', linestyle='--', label='Target (>90%)')
            axes[1, 0].legend()
        
        # System resources
        if self.results["system"]:
            sys = self.results["system"]
            resources = ['CPU', 'Memory', 'Disk I/O', 'Network']
            usage = [
                sys["cpu_usage_percent"],
                sys["memory_usage_percent"],
                min((sys["disk_io_read_mb"] + sys["disk_io_write_mb"]) * 10, 100),  # Scale for visibility
                min((sys["network_in_mb"] + sys["network_out_mb"]) * 10, 100)
            ]
            
            axes[1, 1].bar(resources, usage)
            axes[1, 1].set_ylabel('Usage (%)')
            axes[1, 1].set_title('System Resource Utilization')
            axes[1, 1].axhline(y=70, color='y', linestyle='--', label='Warning (>70%)')
            axes[1, 1].axhline(y=90, color='r', linestyle='--', label='Critical (>90%)')
            axes[1, 1].legend()
        
        plt.tight_layout()
        plt.savefig('performance_analysis.png', dpi=150, bbox_inches='tight')
        console.print("[green]Performance visualization saved to performance_analysis.png[/green]")
    
    async def run_profiling(self):
        """Run complete profiling suite"""
        console.print(Panel.fit("[bold]Financial Planning System Performance Profiler[/bold]", style="cyan"))
        
        # Profile endpoints
        endpoint_metrics = await self.profile_endpoints()
        self.results["endpoints"] = [asdict(m) for m in endpoint_metrics]
        
        # Profile database
        db_metrics = await self.profile_database()
        self.results["database"] = asdict(db_metrics) if db_metrics else None
        
        # Profile cache
        cache_metrics = await self.profile_cache()
        self.results["cache"] = asdict(cache_metrics) if cache_metrics else None
        
        # Profile system
        sys_metrics = await self.profile_system()
        self.results["system"] = asdict(sys_metrics) if sys_metrics else None
        
        # Generate optimizations
        self.results["optimizations"] = self.generate_optimizations()
        
        # Display results
        self.display_results()
        
        # Create visualizations
        self.create_visualizations()
        
        # Save results
        with open('performance_profiling_results.json', 'w') as f:
            json.dump(self.results, f, indent=2)
        
        console.print("[green]Results saved to performance_profiling_results.json[/green]")
    
    def display_results(self):
        """Display profiling results in console"""
        
        # Endpoint results
        if self.results["endpoints"]:
            table = Table(title="API Endpoint Performance", show_header=True)
            table.add_column("Endpoint")
            table.add_column("Method")
            table.add_column("Avg (ms)", justify="right")
            table.add_column("P95 (ms)", justify="right")
            table.add_column("P99 (ms)", justify="right")
            table.add_column("Throughput (req/s)", justify="right")
            table.add_column("Error Rate", justify="right")
            
            for ep in self.results["endpoints"]:
                error_style = "red" if ep["error_rate"] > 0.05 else "green"
                time_style = "red" if ep["p95"] > 1000 else "yellow" if ep["p95"] > 500 else "green"
                
                table.add_row(
                    ep["endpoint"],
                    ep["method"],
                    f"[{time_style}]{ep['avg_response_time']:.0f}[/{time_style}]",
                    f"[{time_style}]{ep['p95']:.0f}[/{time_style}]",
                    f"[{time_style}]{ep['p99']:.0f}[/{time_style}]",
                    f"{ep['throughput']:.1f}",
                    f"[{error_style}]{ep['error_rate']*100:.1f}%[/{error_style}]"
                )
            
            console.print(table)
        
        # Database results
        if self.results["database"]:
            db = self.results["database"]
            table = Table(title="Database Performance", show_header=True)
            table.add_column("Metric")
            table.add_column("Value", justify="right")
            table.add_column("Status")
            
            cache_status = "🟢" if db["cache_hit_ratio"] > 0.9 else "🟡" if db["cache_hit_ratio"] > 0.7 else "🔴"
            index_status = "🟢" if db["index_usage_ratio"] > 0.95 else "🟡" if db["index_usage_ratio"] > 0.8 else "🔴"
            
            table.add_row("Cache Hit Ratio", f"{db['cache_hit_ratio']*100:.1f}%", cache_status)
            table.add_row("Index Usage Ratio", f"{db['index_usage_ratio']*100:.1f}%", index_status)
            table.add_row("Avg Query Time", f"{db['avg_query_time']:.1f}ms", "")
            table.add_row("Connection Pool Usage", f"{db['connection_pool_usage']:.1f}%", "")
            table.add_row("Slow Queries", str(len(db["slow_queries"])), "")
            
            console.print(table)
        
        # Optimization recommendations
        if self.results["optimizations"]:
            table = Table(title="Optimization Recommendations", show_header=True)
            table.add_column("Category")
            table.add_column("Issue")
            table.add_column("Impact")
            table.add_column("Recommendation")
            table.add_column("Expected Improvement")
            
            for opt in self.results["optimizations"][:10]:  # Top 10 recommendations
                impact_style = "red" if opt["impact"] == "High" else "yellow" if opt["impact"] == "Medium" else "white"
                table.add_row(
                    opt["category"],
                    opt["issue"],
                    f"[{impact_style}]{opt['impact']}[/{impact_style}]",
                    opt["recommendation"],
                    opt["expected_improvement"]
                )
            
            console.print(table)


async def main():
    """Main execution function"""
    profiler = PerformanceProfiler()
    await profiler.run_profiling()


if __name__ == "__main__":
    asyncio.run(main())