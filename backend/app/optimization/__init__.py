"""
Performance Optimization Package for Financial Planning System

This package provides comprehensive performance optimization including:
- Multi-level caching (Memory, Redis, Memcached)
- Query optimization with eager loading
- Connection pooling with PgBouncer
- API response optimization
- Performance monitoring and auto-tuning

Target SLA:
- p50 < 100ms
- p95 < 300ms
- p99 < 500ms
"""

import asyncio
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from prometheus_client import make_asgi_app

from .cache_manager import (
    MultiLevelCacheManager,
    CacheConfig,
    cache_portfolio,
    cache_market_data,
    cache_user_profile,
    cache_computation
)
from .query_optimizer import (
    QueryOptimizer,
    ConnectionPoolConfig,
    QueryCacheConfig,
    optimized_query
)
from .connection_pool import (
    SmartConnectionPool,
    DatabaseNode,
    PoolType,
    PgBouncerConfig
)
from .response_optimizer import (
    ResponseOptimizer,
    OptimizationConfig,
    PerformanceTarget,
    optimize_api_response
)


class PerformanceOptimizationSystem:
    """
    Unified performance optimization system
    
    This class integrates all optimization components and provides
    a simple interface for the application.
    """
    
    def __init__(
        self,
        database_url: str,
        redis_url: str = "redis://localhost:6379",
        memcached_hosts: Optional[list] = None,
        enable_metrics: bool = True
    ):
        self.database_url = database_url
        self.redis_url = redis_url
        self.memcached_hosts = memcached_hosts or ["localhost:11211"]
        self.enable_metrics = enable_metrics
        
        # Initialize components
        self.cache_manager: Optional[MultiLevelCacheManager] = None
        self.query_optimizer: Optional[QueryOptimizer] = None
        self.connection_pool: Optional[SmartConnectionPool] = None
        self.response_optimizer: Optional[ResponseOptimizer] = None
        
        self._initialized = False
        
    async def initialize(self) -> None:
        """Initialize all optimization components"""
        if self._initialized:
            return
            
        # Setup cache manager
        cache_config = CacheConfig(
            redis_url=self.redis_url,
            memcached_hosts=self.memcached_hosts,
            enable_metrics=self.enable_metrics,
            enable_warming=True,
            memory_max_size=2000,
            memory_max_bytes=200 * 1024 * 1024  # 200MB
        )
        self.cache_manager = MultiLevelCacheManager(cache_config)
        await self.cache_manager.setup()
        
        # Setup query optimizer
        pool_config = ConnectionPoolConfig(
            min_size=20,
            max_size=100,
            max_overflow=50,
            pool_timeout=30.0,
            use_pgbouncer=True,
            max_queries_per_connection=1000
        )
        
        cache_config = QueryCacheConfig(
            enabled=True,
            max_size=10000,
            ttl=300,
            cache_select=True
        )
        
        self.query_optimizer = QueryOptimizer(
            self.database_url,
            pool_config,
            cache_config
        )
        await self.query_optimizer.setup()
        
        # Setup connection pool (if not using PgBouncer through query optimizer)
        # This provides additional read/write splitting capabilities
        nodes = [
            DatabaseNode(
                host="localhost",
                port=5432,
                database="financial_planning",
                pool_type=PoolType.PRIMARY,
                max_connections=50
            )
        ]
        
        pgbouncer_config = PgBouncerConfig(
            enabled=False,  # Already handled by query optimizer
            pool_mode="transaction"
        )
        
        self.connection_pool = SmartConnectionPool(nodes, pgbouncer_config)
        await self.connection_pool.setup()
        
        # Setup response optimizer
        optimization_config = OptimizationConfig(
            enable_compression=True,
            compression_threshold=512,  # Compress > 512 bytes
            preferred_compression=CompressionAlgorithm.BROTLI,
            enable_streaming=True,
            enable_etag=True,
            enable_partial_response=True,
            enable_response_caching=True
        )
        
        performance_targets = PerformanceTarget(
            p50_ms=100,
            p95_ms=300,
            p99_ms=500
        )
        
        self.response_optimizer = ResponseOptimizer(
            optimization_config,
            performance_targets
        )
        
        self._initialized = True
        
        # Start warming critical cache entries
        await self._warm_cache()
        
    async def shutdown(self) -> None:
        """Cleanup all resources"""
        if self.cache_manager:
            await self.cache_manager.close()
            
        if self.query_optimizer:
            await self.query_optimizer.close()
            
        if self.connection_pool:
            await self.connection_pool.close()
            
        self._initialized = False
        
    async def _warm_cache(self) -> None:
        """Pre-warm cache with frequently accessed data"""
        # Example cache warming - customize based on your application
        warm_keys = [
            # Market data
            ("market:sp500:latest", self._fetch_sp500_data),
            ("market:bonds:latest", self._fetch_bond_data),
            
            # Popular portfolios
            ("portfolio:recommended:conservative", self._fetch_conservative_portfolio),
            ("portfolio:recommended:moderate", self._fetch_moderate_portfolio),
            ("portfolio:recommended:aggressive", self._fetch_aggressive_portfolio),
        ]
        
        # Use actual data fetching functions in production
        async def dummy_fetch():
            return {"status": "warmed", "timestamp": datetime.utcnow().isoformat()}
            
        for key, _ in warm_keys:
            await self.cache_manager.set(key, await dummy_fetch(), ttl=3600)
            
    async def _fetch_sp500_data(self):
        """Fetch S&P 500 data"""
        # Implement actual data fetching
        return {"symbol": "SPY", "price": 450.0}
        
    async def _fetch_bond_data(self):
        """Fetch bond market data"""
        # Implement actual data fetching
        return {"symbol": "AGG", "yield": 3.5}
        
    async def _fetch_conservative_portfolio(self):
        """Fetch conservative portfolio allocation"""
        return {
            "stocks": 30,
            "bonds": 60,
            "cash": 10
        }
        
    async def _fetch_moderate_portfolio(self):
        """Fetch moderate portfolio allocation"""
        return {
            "stocks": 60,
            "bonds": 30,
            "cash": 10
        }
        
    async def _fetch_aggressive_portfolio(self):
        """Fetch aggressive portfolio allocation"""
        return {
            "stocks": 80,
            "bonds": 15,
            "cash": 5
        }
        
    def get_metrics(self) -> dict:
        """Get performance metrics from all components"""
        metrics = {
            "cache": self.cache_manager.get_stats() if self.cache_manager else {},
            "query": self.query_optimizer.get_performance_stats() if self.query_optimizer else {},
            "connection_pool": self.connection_pool.get_stats() if self.connection_pool else {},
            "response": self.response_optimizer.get_performance_metrics() if self.response_optimizer else {}
        }
        
        # Check if meeting SLA
        if self.response_optimizer:
            response_metrics = self.response_optimizer.get_performance_metrics()
            metrics["sla_compliance"] = {
                "meeting_targets": response_metrics.get("meeting_sla", False),
                "p50": response_metrics.get("p50", 0),
                "p95": response_metrics.get("p95", 0),
                "p99": response_metrics.get("p99", 0)
            }
            
        return metrics
        
    def auto_tune(self) -> dict:
        """Auto-tune all optimization components"""
        recommendations = {}
        
        if self.response_optimizer:
            recommendations["response"] = self.response_optimizer.auto_tune()
            
        # Add more auto-tuning logic here
        
        return recommendations


# Global instance
_optimization_system: Optional[PerformanceOptimizationSystem] = None


async def setup_optimization(
    app: FastAPI,
    database_url: str,
    redis_url: str = "redis://localhost:6379",
    memcached_hosts: Optional[list] = None
) -> PerformanceOptimizationSystem:
    """
    Setup performance optimization for FastAPI application
    
    Args:
        app: FastAPI application instance
        database_url: PostgreSQL connection URL
        redis_url: Redis connection URL
        memcached_hosts: List of Memcached hosts
        
    Returns:
        Initialized optimization system
    """
    global _optimization_system
    
    # Create optimization system
    _optimization_system = PerformanceOptimizationSystem(
        database_url=database_url,
        redis_url=redis_url,
        memcached_hosts=memcached_hosts
    )
    
    # Initialize on startup
    @app.on_event("startup")
    async def startup_optimization():
        await _optimization_system.initialize()
        
    # Cleanup on shutdown
    @app.on_event("shutdown")
    async def shutdown_optimization():
        await _optimization_system.shutdown()
        
    # Add middleware for response optimization
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    
    # Add Prometheus metrics endpoint
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)
    
    # Add performance monitoring endpoint
    @app.get("/api/v1/performance/metrics")
    async def get_performance_metrics():
        """Get current performance metrics"""
        return _optimization_system.get_metrics()
        
    @app.post("/api/v1/performance/tune")
    async def auto_tune_performance():
        """Run auto-tuning for performance optimization"""
        return _optimization_system.auto_tune()
        
    return _optimization_system


def get_optimization_system() -> PerformanceOptimizationSystem:
    """Get the global optimization system instance"""
    if _optimization_system is None:
        raise RuntimeError("Optimization system not initialized. Call setup_optimization() first.")
    return _optimization_system


# Dependency injection for FastAPI
async def get_cache_manager() -> MultiLevelCacheManager:
    """FastAPI dependency for cache manager"""
    system = get_optimization_system()
    return system.cache_manager


async def get_query_optimizer() -> QueryOptimizer:
    """FastAPI dependency for query optimizer"""
    system = get_optimization_system()
    return system.query_optimizer


async def get_connection_pool() -> SmartConnectionPool:
    """FastAPI dependency for connection pool"""
    system = get_optimization_system()
    return system.connection_pool


async def get_response_optimizer() -> ResponseOptimizer:
    """FastAPI dependency for response optimizer"""
    system = get_optimization_system()
    return system.response_optimizer


# Export main components and decorators
__all__ = [
    # Main system
    'PerformanceOptimizationSystem',
    'setup_optimization',
    'get_optimization_system',
    
    # Cache components
    'MultiLevelCacheManager',
    'CacheConfig',
    'cache_portfolio',
    'cache_market_data',
    'cache_user_profile',
    'cache_computation',
    
    # Query optimization
    'QueryOptimizer',
    'ConnectionPoolConfig',
    'QueryCacheConfig',
    'optimized_query',
    
    # Connection pooling
    'SmartConnectionPool',
    'DatabaseNode',
    'PoolType',
    'PgBouncerConfig',
    
    # Response optimization
    'ResponseOptimizer',
    'OptimizationConfig',
    'PerformanceTarget',
    'optimize_api_response',
    
    # FastAPI dependencies
    'get_cache_manager',
    'get_query_optimizer',
    'get_connection_pool',
    'get_response_optimizer'
]