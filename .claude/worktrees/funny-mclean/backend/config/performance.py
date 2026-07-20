"""
Performance Configuration for Financial Planning System
Centralized performance tuning parameters and optimization settings
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum


class OptimizationLevel(Enum):
    """Performance optimization levels"""
    DEVELOPMENT = "development"  # Minimal optimization, max debugging
    STAGING = "staging"  # Balanced optimization
    PRODUCTION = "production"  # Maximum optimization
    ULTRA = "ultra"  # Extreme optimization (may sacrifice features)


@dataclass
class CacheConfig:
    """Cache configuration settings"""
    # L1 Memory Cache
    l1_enabled: bool = True
    l1_max_size: int = 10000  # Maximum number of entries
    l1_max_memory_mb: int = 512  # Maximum memory usage in MB
    l1_ttl_seconds: int = 300  # Default TTL
    
    # L2 Redis Cache
    l2_enabled: bool = True
    l2_max_connections: int = 50
    l2_connection_timeout: int = 5
    l2_socket_keepalive: bool = True
    l2_compression_threshold: int = 1024  # Compress values larger than this (bytes)
    l2_ttl_seconds: int = 3600  # Default TTL
    
    # L3 CDN Cache
    l3_enabled: bool = False  # Disabled by default
    l3_endpoints: List[str] = field(default_factory=list)
    l3_ttl_seconds: int = 86400  # 24 hours
    
    # Cache key patterns and TTLs
    ttl_config: Dict[str, int] = field(default_factory=lambda: {
        'quote': 1,
        'market_data': 5,
        'portfolio_value': 10,
        'user_profile': 300,
        'portfolio_holdings': 60,
        'transactions': 120,
        'security_info': 3600,
        'historical_data': 1800,
        'analytics': 600,
        'monte_carlo': 1800,
        'optimization': 900,
        'recommendations': 600
    })
    
    # Cache warming
    warm_cache_on_startup: bool = True
    cache_preload_patterns: List[str] = field(default_factory=lambda: [
        'security_info:*',
        'user_profile:*',
        'portfolio_holdings:*'
    ])


@dataclass
class DatabaseConfig:
    """Database optimization configuration"""
    # Connection pooling
    pool_size: int = 20
    max_overflow: int = 40
    pool_timeout: int = 30
    pool_recycle: int = 3600  # Recycle connections after 1 hour
    pool_pre_ping: bool = True
    
    # Read replicas
    enable_read_replicas: bool = True
    read_replica_urls: List[str] = field(default_factory=list)
    read_replica_load_balancing: str = "round_robin"  # round_robin, random, least_connections
    
    # Query optimization
    slow_query_threshold_ms: int = 1000
    enable_query_cache: bool = True
    query_cache_ttl: int = 300
    auto_explain_threshold_ms: int = 500
    
    # Index management
    auto_create_indexes: bool = True
    auto_analyze_tables: bool = True
    analyze_interval_hours: int = 24
    vacuum_interval_hours: int = 168  # Weekly
    
    # Batch operations
    batch_size: int = 1000
    bulk_insert_threshold: int = 100
    
    # Connection settings
    statement_timeout_ms: int = 30000  # 30 seconds
    lock_timeout_ms: int = 10000  # 10 seconds
    idle_in_transaction_timeout_ms: int = 60000  # 1 minute


@dataclass
class AsyncConfig:
    """Asynchronous processing configuration"""
    # Thread pool
    thread_pool_size: int = 10
    max_thread_pool_size: int = 50
    
    # Process pool
    process_pool_size: int = 4
    max_process_pool_size: int = 8
    
    # Task queue
    task_queue_size: int = 10000
    task_timeout_seconds: int = 300
    max_retries: int = 3
    retry_backoff_seconds: int = 60
    
    # Celery settings
    celery_worker_concurrency: int = 4
    celery_worker_prefetch_multiplier: int = 4
    celery_task_acks_late: bool = True
    celery_task_reject_on_worker_lost: bool = True
    
    # WebSocket settings
    websocket_ping_interval: int = 30
    websocket_ping_timeout: int = 10
    websocket_max_connections: int = 1000
    websocket_message_queue_size: int = 100


@dataclass
class ComputeConfig:
    """Computational optimization configuration"""
    # Vectorization
    enable_vectorization: bool = True
    numpy_threads: int = 4
    use_mkl: bool = True  # Intel Math Kernel Library
    
    # GPU acceleration
    enable_gpu: bool = False  # Requires CUDA
    gpu_memory_fraction: float = 0.8
    gpu_allow_growth: bool = True
    
    # Monte Carlo
    monte_carlo_batch_size: int = 10000
    monte_carlo_parallel_runs: int = 4
    monte_carlo_cache_results: bool = True
    
    # Optimization algorithms
    optimizer_max_iterations: int = 1000
    optimizer_tolerance: float = 1e-6
    optimizer_parallel_evaluations: int = 4
    
    # Data processing
    dataframe_chunk_size: int = 10000
    enable_numba_jit: bool = True
    enable_cython: bool = False


@dataclass
class NetworkConfig:
    """Network optimization configuration"""
    # HTTP settings
    http_connection_pooling: bool = True
    http_max_connections: int = 100
    http_max_connections_per_host: int = 10
    http_timeout_seconds: int = 30
    http_retry_count: int = 3
    http_retry_backoff: float = 0.5
    
    # API rate limiting
    rate_limit_enabled: bool = True
    rate_limit_requests_per_minute: int = 60
    rate_limit_burst_size: int = 10
    
    # Response compression
    enable_gzip: bool = True
    gzip_compression_level: int = 6
    enable_brotli: bool = True
    brotli_compression_level: int = 4
    
    # Keep-alive
    tcp_keepalive: bool = True
    tcp_keepidle: int = 600  # 10 minutes
    tcp_keepintvl: int = 60  # 1 minute
    tcp_keepcnt: int = 9


@dataclass
class MonitoringConfig:
    """Performance monitoring configuration"""
    # Metrics collection
    enable_metrics: bool = True
    metrics_interval_seconds: int = 60
    
    # Profiling
    enable_profiling: bool = False  # Only in development
    profile_sample_rate: float = 0.01  # 1% of requests
    profile_slow_requests: bool = True
    slow_request_threshold_ms: int = 1000
    
    # Memory monitoring
    monitor_memory_leaks: bool = True
    memory_leak_threshold_mb: int = 100
    memory_snapshot_interval_minutes: int = 60
    
    # Alerts
    enable_performance_alerts: bool = True
    alert_cpu_threshold_percent: int = 80
    alert_memory_threshold_percent: int = 85
    alert_response_time_threshold_ms: int = 2000
    
    # Logging
    log_slow_queries: bool = True
    log_memory_usage: bool = True
    log_cache_stats: bool = True
    performance_log_level: str = "INFO"


@dataclass
class FrontendOptimizationConfig:
    """Frontend performance optimization settings"""
    # Code splitting
    enable_code_splitting: bool = True
    chunk_size_limit_kb: int = 244  # Recommended for optimal loading
    
    # Lazy loading
    enable_lazy_loading: bool = True
    lazy_load_threshold_px: int = 100
    
    # Image optimization
    optimize_images: bool = True
    image_quality: int = 85
    webp_conversion: bool = True
    responsive_images: bool = True
    lazy_load_images: bool = True
    
    # Bundle optimization
    tree_shake: bool = True
    minify_css: bool = True
    minify_js: bool = True
    remove_console_logs: bool = True
    
    # Caching
    service_worker_enabled: bool = True
    cache_static_assets: bool = True
    cache_api_responses: bool = True
    offline_mode: bool = True
    
    # Performance budgets
    bundle_size_budget_kb: int = 500
    initial_load_budget_ms: int = 3000
    interaction_budget_ms: int = 100


class PerformanceConfig:
    """
    Main performance configuration class
    """
    
    def __init__(self, optimization_level: OptimizationLevel = OptimizationLevel.PRODUCTION):
        self.optimization_level = optimization_level
        
        # Initialize sub-configurations based on optimization level
        if optimization_level == OptimizationLevel.DEVELOPMENT:
            self._init_development_config()
        elif optimization_level == OptimizationLevel.STAGING:
            self._init_staging_config()
        elif optimization_level == OptimizationLevel.PRODUCTION:
            self._init_production_config()
        elif optimization_level == OptimizationLevel.ULTRA:
            self._init_ultra_config()
    
    def _init_development_config(self):
        """Development configuration - minimal optimization"""
        self.cache = CacheConfig(
            l1_max_size=1000,
            l1_max_memory_mb=128,
            l2_enabled=False,
            l3_enabled=False,
            warm_cache_on_startup=False
        )
        
        self.database = DatabaseConfig(
            pool_size=5,
            max_overflow=10,
            enable_read_replicas=False,
            auto_create_indexes=False,
            auto_analyze_tables=False
        )
        
        self.async_config = AsyncConfig(
            thread_pool_size=2,
            process_pool_size=1,
            celery_worker_concurrency=1
        )
        
        self.compute = ComputeConfig(
            enable_vectorization=False,
            enable_gpu=False,
            monte_carlo_parallel_runs=1
        )
        
        self.network = NetworkConfig(
            rate_limit_enabled=False,
            enable_gzip=False,
            enable_brotli=False
        )
        
        self.monitoring = MonitoringConfig(
            enable_profiling=True,
            profile_sample_rate=1.0,
            enable_performance_alerts=False
        )
        
        self.frontend = FrontendOptimizationConfig(
            enable_code_splitting=False,
            enable_lazy_loading=False,
            optimize_images=False,
            service_worker_enabled=False
        )
    
    def _init_staging_config(self):
        """Staging configuration - balanced optimization"""
        self.cache = CacheConfig(
            l1_max_size=5000,
            l1_max_memory_mb=256,
            l2_enabled=True,
            l3_enabled=False
        )
        
        self.database = DatabaseConfig(
            pool_size=10,
            max_overflow=20,
            enable_read_replicas=False
        )
        
        self.async_config = AsyncConfig(
            thread_pool_size=5,
            process_pool_size=2,
            celery_worker_concurrency=2
        )
        
        self.compute = ComputeConfig(
            enable_vectorization=True,
            enable_gpu=False,
            monte_carlo_parallel_runs=2
        )
        
        self.network = NetworkConfig(
            rate_limit_enabled=True,
            enable_gzip=True,
            enable_brotli=False
        )
        
        self.monitoring = MonitoringConfig(
            enable_profiling=True,
            profile_sample_rate=0.1
        )
        
        self.frontend = FrontendOptimizationConfig(
            enable_code_splitting=True,
            enable_lazy_loading=True,
            optimize_images=True,
            service_worker_enabled=False
        )
    
    def _init_production_config(self):
        """Production configuration - high optimization"""
        self.cache = CacheConfig()  # Use defaults (all enabled)
        
        self.database = DatabaseConfig()  # Use defaults (fully optimized)
        
        self.async_config = AsyncConfig()  # Use defaults
        
        self.compute = ComputeConfig(
            enable_vectorization=True,
            enable_gpu=True,  # Enable if available
            monte_carlo_parallel_runs=4
        )
        
        self.network = NetworkConfig()  # Use defaults (all optimizations)
        
        self.monitoring = MonitoringConfig(
            enable_profiling=False,
            profile_sample_rate=0.01
        )
        
        self.frontend = FrontendOptimizationConfig()  # Use defaults (fully optimized)
    
    def _init_ultra_config(self):
        """Ultra configuration - extreme optimization"""
        self.cache = CacheConfig(
            l1_max_size=20000,
            l1_max_memory_mb=1024,
            l2_max_connections=100,
            l3_enabled=True,
            warm_cache_on_startup=True
        )
        
        self.database = DatabaseConfig(
            pool_size=50,
            max_overflow=100,
            enable_read_replicas=True,
            batch_size=5000
        )
        
        self.async_config = AsyncConfig(
            thread_pool_size=20,
            process_pool_size=8,
            celery_worker_concurrency=8,
            task_queue_size=50000
        )
        
        self.compute = ComputeConfig(
            enable_vectorization=True,
            enable_gpu=True,
            monte_carlo_parallel_runs=8,
            monte_carlo_batch_size=50000,
            enable_numba_jit=True,
            enable_cython=True
        )
        
        self.network = NetworkConfig(
            http_max_connections=200,
            enable_brotli=True,
            brotli_compression_level=11  # Maximum compression
        )
        
        self.monitoring = MonitoringConfig(
            enable_profiling=False,
            monitor_memory_leaks=True,
            enable_performance_alerts=True
        )
        
        self.frontend = FrontendOptimizationConfig(
            chunk_size_limit_kb=200,
            image_quality=80,
            webp_conversion=True,
            bundle_size_budget_kb=400,
            initial_load_budget_ms=2000
        )
    
    def get_config_dict(self) -> Dict:
        """Get configuration as dictionary"""
        return {
            'optimization_level': self.optimization_level.value,
            'cache': self.cache.__dict__,
            'database': self.database.__dict__,
            'async': self.async_config.__dict__,
            'compute': self.compute.__dict__,
            'network': self.network.__dict__,
            'monitoring': self.monitoring.__dict__,
            'frontend': self.frontend.__dict__
        }
    
    def apply_overrides(self, overrides: Dict):
        """Apply configuration overrides"""
        for section, settings in overrides.items():
            if hasattr(self, section):
                config_obj = getattr(self, section)
                for key, value in settings.items():
                    if hasattr(config_obj, key):
                        setattr(config_obj, key, value)


# Create default configuration based on environment
import os
env = os.getenv('ENVIRONMENT', 'production').lower()

if env == 'development':
    performance_config = PerformanceConfig(OptimizationLevel.DEVELOPMENT)
elif env == 'staging':
    performance_config = PerformanceConfig(OptimizationLevel.STAGING)
elif env == 'production':
    performance_config = PerformanceConfig(OptimizationLevel.PRODUCTION)
else:
    performance_config = PerformanceConfig(OptimizationLevel.PRODUCTION)

# Apply any environment-specific overrides
if os.getenv('ENABLE_GPU', 'false').lower() == 'true':
    performance_config.compute.enable_gpu = True

if os.getenv('ENABLE_CDN', 'false').lower() == 'true':
    performance_config.cache.l3_enabled = True

# Export configuration
__all__ = ['performance_config', 'PerformanceConfig', 'OptimizationLevel']