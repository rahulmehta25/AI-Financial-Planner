"""
Performance Profiler for Financial Planning System
Implements CPU, memory, I/O profiling with real-time monitoring
"""

import time
import asyncio
import psutil
import tracemalloc
import cProfile
import pstats
import io
import gc
import sys
import threading
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from contextlib import contextmanager, asynccontextmanager
from functools import wraps
import numpy as np

import logging
logger = logging.getLogger(__name__)


@dataclass
class ProfileMetrics:
    """Performance metrics for a profiled operation"""
    operation_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_ms: float = 0.0
    
    # CPU metrics
    cpu_percent: float = 0.0
    cpu_time_user: float = 0.0
    cpu_time_system: float = 0.0
    
    # Memory metrics
    memory_start_mb: float = 0.0
    memory_end_mb: float = 0.0
    memory_peak_mb: float = 0.0
    memory_allocated_mb: float = 0.0
    
    # I/O metrics
    io_read_count: int = 0
    io_write_count: int = 0
    io_read_bytes: int = 0
    io_write_bytes: int = 0
    
    # Database metrics
    db_query_count: int = 0
    db_query_time_ms: float = 0.0
    
    # Network metrics
    network_requests: int = 0
    network_bytes_sent: int = 0
    network_bytes_received: int = 0
    
    # Custom metrics
    custom_metrics: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """Convert metrics to dictionary for reporting"""
        return {
            'operation': self.operation_name,
            'duration_ms': round(self.duration_ms, 2),
            'cpu': {
                'percent': round(self.cpu_percent, 2),
                'time_user_ms': round(self.cpu_time_user * 1000, 2),
                'time_system_ms': round(self.cpu_time_system * 1000, 2)
            },
            'memory': {
                'start_mb': round(self.memory_start_mb, 2),
                'end_mb': round(self.memory_end_mb, 2),
                'peak_mb': round(self.memory_peak_mb, 2),
                'allocated_mb': round(self.memory_allocated_mb, 2)
            },
            'io': {
                'read_count': self.io_read_count,
                'write_count': self.io_write_count,
                'read_mb': round(self.io_read_bytes / (1024 * 1024), 2),
                'write_mb': round(self.io_write_bytes / (1024 * 1024), 2)
            },
            'database': {
                'query_count': self.db_query_count,
                'query_time_ms': round(self.db_query_time_ms, 2)
            },
            'network': {
                'requests': self.network_requests,
                'sent_kb': round(self.network_bytes_sent / 1024, 2),
                'received_kb': round(self.network_bytes_received / 1024, 2)
            },
            'custom': self.custom_metrics,
            'timestamp': self.start_time.isoformat()
        }


class CPUProfiler:
    """CPU profiling utilities"""
    
    def __init__(self):
        self.process = psutil.Process()
        self.profiler = cProfile.Profile()
        self.is_profiling = False
    
    def start(self):
        """Start CPU profiling"""
        if not self.is_profiling:
            self.profiler.enable()
            self.is_profiling = True
    
    def stop(self) -> str:
        """Stop CPU profiling and return stats"""
        if self.is_profiling:
            self.profiler.disable()
            self.is_profiling = False
            
            # Get profiling stats
            s = io.StringIO()
            ps = pstats.Stats(self.profiler, stream=s).sort_stats('cumulative')
            ps.print_stats(20)  # Top 20 functions
            
            return s.getvalue()
        return ""
    
    def get_cpu_stats(self) -> Dict:
        """Get current CPU statistics"""
        return {
            'cpu_percent': self.process.cpu_percent(interval=0.1),
            'cpu_times': self.process.cpu_times()._asdict(),
            'cpu_count': psutil.cpu_count(),
            'cpu_freq': psutil.cpu_freq()._asdict() if psutil.cpu_freq() else {},
            'per_cpu_percent': psutil.cpu_percent(interval=0.1, percpu=True)
        }


class MemoryProfiler:
    """Memory profiling and leak detection"""
    
    def __init__(self):
        self.process = psutil.Process()
        self.snapshots = []
        self.is_tracing = False
    
    def start_tracing(self):
        """Start memory allocation tracing"""
        if not self.is_tracing:
            tracemalloc.start()
            self.is_tracing = True
    
    def stop_tracing(self):
        """Stop memory allocation tracing"""
        if self.is_tracing:
            tracemalloc.stop()
            self.is_tracing = False
    
    def take_snapshot(self, label: str = ""):
        """Take memory snapshot for comparison"""
        if self.is_tracing:
            snapshot = tracemalloc.take_snapshot()
            self.snapshots.append((label, snapshot, datetime.now()))
            return snapshot
        return None
    
    def compare_snapshots(self, snapshot1, snapshot2) -> List[Dict]:
        """Compare two memory snapshots to find leaks"""
        if not snapshot1 or not snapshot2:
            return []
        
        top_stats = snapshot2.compare_to(snapshot1, 'lineno')
        
        results = []
        for stat in top_stats[:10]:  # Top 10 differences
            results.append({
                'file': stat.traceback.format()[0] if stat.traceback else 'unknown',
                'size_diff_mb': stat.size_diff / (1024 * 1024),
                'count_diff': stat.count_diff
            })
        
        return results
    
    def get_memory_stats(self) -> Dict:
        """Get current memory statistics"""
        mem_info = self.process.memory_info()
        mem_percent = self.process.memory_percent()
        
        return {
            'rss_mb': mem_info.rss / (1024 * 1024),
            'vms_mb': mem_info.vms / (1024 * 1024),
            'percent': mem_percent,
            'available_mb': psutil.virtual_memory().available / (1024 * 1024),
            'gc_stats': self._get_gc_stats()
        }
    
    def _get_gc_stats(self) -> Dict:
        """Get garbage collection statistics"""
        return {
            'collections': gc.get_count(),
            'collected': gc.collect(),
            'threshold': gc.get_threshold()
        }
    
    def detect_memory_leaks(self, threshold_mb: float = 10.0) -> List[str]:
        """Detect potential memory leaks"""
        warnings = []
        
        # Check for large objects
        for obj in gc.get_objects():
            try:
                size_mb = sys.getsizeof(obj) / (1024 * 1024)
                if size_mb > threshold_mb:
                    warnings.append(f"Large object detected: {type(obj).__name__} ({size_mb:.2f} MB)")
            except:
                pass
        
        # Check for uncollected garbage
        if gc.collect() > 100:
            warnings.append("Large amount of uncollected garbage detected")
        
        return warnings


class IOProfiler:
    """I/O and disk profiling"""
    
    def __init__(self):
        self.process = psutil.Process()
        self.start_io_counters = None
    
    def start(self):
        """Start I/O monitoring"""
        self.start_io_counters = self.process.io_counters()
    
    def get_io_stats(self) -> Dict:
        """Get I/O statistics since start"""
        if not self.start_io_counters:
            self.start()
        
        current = self.process.io_counters()
        
        return {
            'read_count': current.read_count - self.start_io_counters.read_count,
            'write_count': current.write_count - self.start_io_counters.write_count,
            'read_bytes': current.read_bytes - self.start_io_counters.read_bytes,
            'write_bytes': current.write_bytes - self.start_io_counters.write_bytes
        }
    
    def get_disk_stats(self) -> Dict:
        """Get disk usage statistics"""
        disk_usage = psutil.disk_usage('/')
        disk_io = psutil.disk_io_counters()
        
        return {
            'usage_percent': disk_usage.percent,
            'free_gb': disk_usage.free / (1024**3),
            'io_read_mb': disk_io.read_bytes / (1024**2) if disk_io else 0,
            'io_write_mb': disk_io.write_bytes / (1024**2) if disk_io else 0
        }


class NetworkProfiler:
    """Network I/O profiling"""
    
    def __init__(self):
        self.start_counters = None
    
    def start(self):
        """Start network monitoring"""
        self.start_counters = psutil.net_io_counters()
    
    def get_network_stats(self) -> Dict:
        """Get network statistics since start"""
        if not self.start_counters:
            self.start()
        
        current = psutil.net_io_counters()
        
        return {
            'bytes_sent': current.bytes_sent - self.start_counters.bytes_sent,
            'bytes_received': current.bytes_recv - self.start_counters.bytes_recv,
            'packets_sent': current.packets_sent - self.start_counters.packets_sent,
            'packets_received': current.packets_recv - self.start_counters.packets_recv,
            'errors': current.errin + current.errout - 
                     (self.start_counters.errin + self.start_counters.errout)
        }


class PerformanceProfiler:
    """
    Comprehensive performance profiler combining all metrics
    """
    
    def __init__(self):
        self.cpu_profiler = CPUProfiler()
        self.memory_profiler = MemoryProfiler()
        self.io_profiler = IOProfiler()
        self.network_profiler = NetworkProfiler()
        
        # Metrics storage
        self.active_profiles: Dict[str, ProfileMetrics] = {}
        self.completed_profiles: List[ProfileMetrics] = []
        
        # Performance thresholds
        self.thresholds = {
            'slow_operation_ms': 1000,
            'high_memory_mb': 100,
            'high_cpu_percent': 80
        }
        
        # Start memory tracing
        self.memory_profiler.start_tracing()
    
    @contextmanager
    def profile(self, operation_name: str, **kwargs):
        """
        Context manager for profiling a code block
        
        Usage:
            with profiler.profile('expensive_operation'):
                # code to profile
                pass
        """
        metrics = self._start_profile(operation_name)
        
        try:
            yield metrics
        finally:
            self._end_profile(operation_name)
    
    @asynccontextmanager
    async def aprofile(self, operation_name: str, **kwargs):
        """
        Async context manager for profiling async code
        
        Usage:
            async with profiler.aprofile('async_operation'):
                # async code to profile
                await some_async_function()
        """
        metrics = self._start_profile(operation_name)
        
        try:
            yield metrics
        finally:
            self._end_profile(operation_name)
    
    def _start_profile(self, operation_name: str) -> ProfileMetrics:
        """Start profiling an operation"""
        # Initialize metrics
        metrics = ProfileMetrics(
            operation_name=operation_name,
            start_time=datetime.now()
        )
        
        # Capture starting metrics
        memory_stats = self.memory_profiler.get_memory_stats()
        metrics.memory_start_mb = memory_stats['rss_mb']
        
        # Start I/O monitoring
        self.io_profiler.start()
        self.network_profiler.start()
        
        # Store active profile
        self.active_profiles[operation_name] = metrics
        
        return metrics
    
    def _end_profile(self, operation_name: str):
        """End profiling an operation"""
        if operation_name not in self.active_profiles:
            return
        
        metrics = self.active_profiles[operation_name]
        metrics.end_time = datetime.now()
        metrics.duration_ms = (metrics.end_time - metrics.start_time).total_seconds() * 1000
        
        # Capture ending metrics
        cpu_stats = self.cpu_profiler.get_cpu_stats()
        metrics.cpu_percent = cpu_stats['cpu_percent']
        
        memory_stats = self.memory_profiler.get_memory_stats()
        metrics.memory_end_mb = memory_stats['rss_mb']
        metrics.memory_allocated_mb = metrics.memory_end_mb - metrics.memory_start_mb
        
        io_stats = self.io_profiler.get_io_stats()
        metrics.io_read_count = io_stats['read_count']
        metrics.io_write_count = io_stats['write_count']
        metrics.io_read_bytes = io_stats['read_bytes']
        metrics.io_write_bytes = io_stats['write_bytes']
        
        network_stats = self.network_profiler.get_network_stats()
        metrics.network_bytes_sent = network_stats['bytes_sent']
        metrics.network_bytes_received = network_stats['bytes_received']
        
        # Check for performance issues
        self._check_performance_issues(metrics)
        
        # Move to completed
        del self.active_profiles[operation_name]
        self.completed_profiles.append(metrics)
        
        # Limit stored profiles
        if len(self.completed_profiles) > 1000:
            self.completed_profiles = self.completed_profiles[-1000:]
    
    def _check_performance_issues(self, metrics: ProfileMetrics):
        """Check for performance issues and log warnings"""
        warnings = []
        
        if metrics.duration_ms > self.thresholds['slow_operation_ms']:
            warnings.append(f"Slow operation: {metrics.duration_ms:.2f}ms")
        
        if metrics.memory_allocated_mb > self.thresholds['high_memory_mb']:
            warnings.append(f"High memory usage: {metrics.memory_allocated_mb:.2f}MB")
        
        if metrics.cpu_percent > self.thresholds['high_cpu_percent']:
            warnings.append(f"High CPU usage: {metrics.cpu_percent:.2f}%")
        
        if warnings:
            logger.warning(f"Performance issues in '{metrics.operation_name}': {', '.join(warnings)}")
    
    def profile_decorator(self, operation_name: Optional[str] = None):
        """
        Decorator for automatic profiling of functions
        
        Usage:
            @profiler.profile_decorator('my_function')
            def my_function():
                pass
        """
        def decorator(func):
            name = operation_name or func.__name__
            
            if asyncio.iscoroutinefunction(func):
                @wraps(func)
                async def async_wrapper(*args, **kwargs):
                    async with self.aprofile(name):
                        return await func(*args, **kwargs)
                return async_wrapper
            else:
                @wraps(func)
                def sync_wrapper(*args, **kwargs):
                    with self.profile(name):
                        return func(*args, **kwargs)
                return sync_wrapper
        
        return decorator
    
    def get_profile_report(self, operation_name: Optional[str] = None) -> Dict:
        """Get profiling report for operations"""
        if operation_name:
            # Get specific operation metrics
            for metrics in reversed(self.completed_profiles):
                if metrics.operation_name == operation_name:
                    return metrics.to_dict()
            return {}
        
        # Get summary of all operations
        return {
            'active_operations': [m.operation_name for m in self.active_profiles.values()],
            'recent_operations': [m.to_dict() for m in self.completed_profiles[-10:]],
            'statistics': self._calculate_statistics(),
            'system_metrics': self.get_system_metrics(),
            'recommendations': self._generate_recommendations()
        }
    
    def _calculate_statistics(self) -> Dict:
        """Calculate performance statistics"""
        if not self.completed_profiles:
            return {}
        
        durations = [m.duration_ms for m in self.completed_profiles]
        memory_usage = [m.memory_allocated_mb for m in self.completed_profiles]
        cpu_usage = [m.cpu_percent for m in self.completed_profiles]
        
        return {
            'operations_count': len(self.completed_profiles),
            'duration': {
                'mean_ms': np.mean(durations),
                'median_ms': np.median(durations),
                'p95_ms': np.percentile(durations, 95),
                'p99_ms': np.percentile(durations, 99),
                'max_ms': np.max(durations)
            },
            'memory': {
                'mean_mb': np.mean(memory_usage),
                'max_mb': np.max(memory_usage)
            },
            'cpu': {
                'mean_percent': np.mean(cpu_usage),
                'max_percent': np.max(cpu_usage)
            }
        }
    
    def get_system_metrics(self) -> Dict:
        """Get current system metrics"""
        return {
            'cpu': self.cpu_profiler.get_cpu_stats(),
            'memory': self.memory_profiler.get_memory_stats(),
            'disk': self.io_profiler.get_disk_stats(),
            'network': self.network_profiler.get_network_stats() 
                      if self.network_profiler.start_counters else {}
        }
    
    def _generate_recommendations(self) -> List[str]:
        """Generate performance recommendations"""
        recommendations = []
        stats = self._calculate_statistics()
        
        if stats:
            # Check for slow operations
            if stats['duration']['p95_ms'] > 1000:
                recommendations.append("95th percentile response time exceeds 1 second - consider optimization")
            
            # Check for memory issues
            if stats['memory']['max_mb'] > 500:
                recommendations.append("High memory usage detected - review memory allocation patterns")
            
            # Check for CPU bottlenecks
            if stats['cpu']['mean_percent'] > 70:
                recommendations.append("High CPU usage - consider async operations or caching")
        
        # Check for memory leaks
        leaks = self.memory_profiler.detect_memory_leaks()
        if leaks:
            recommendations.extend(leaks)
        
        return recommendations
    
    def benchmark(self, func: Callable, iterations: int = 100, **kwargs) -> Dict:
        """
        Benchmark a function with multiple iterations
        """
        results = []
        
        for _ in range(iterations):
            with self.profile(f"benchmark_{func.__name__}") as metrics:
                if asyncio.iscoroutinefunction(func):
                    asyncio.run(func(**kwargs))
                else:
                    func(**kwargs)
            
            results.append(metrics.duration_ms)
        
        return {
            'function': func.__name__,
            'iterations': iterations,
            'mean_ms': np.mean(results),
            'std_ms': np.std(results),
            'min_ms': np.min(results),
            'max_ms': np.max(results),
            'p50_ms': np.percentile(results, 50),
            'p95_ms': np.percentile(results, 95),
            'p99_ms': np.percentile(results, 99)
        }


# Singleton instance
performance_profiler = PerformanceProfiler()