"""
Advanced Database Connection Pooling with PgBouncer Integration

This module provides enterprise-grade connection pooling with:
- PgBouncer integration for connection multiplexing
- Read/write splitting for scalability
- Automatic failover and health checks
- Connection warming and recycling
- Circuit breaker pattern for resilience
"""

import asyncio
import random
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import asyncpg
from prometheus_client import Counter, Gauge, Histogram


# Metrics
pool_connections = Gauge('db_pool_connections', 'Active database connections', ['pool', 'state'])
pool_wait_time = Histogram('db_pool_wait_seconds', 'Time waiting for connection', ['pool'])
pool_errors = Counter('db_pool_errors_total', 'Database connection errors', ['pool', 'error_type'])
query_routing = Counter('db_query_routing_total', 'Query routing decisions', ['destination'])


class PoolType(Enum):
    """Connection pool types"""
    PRIMARY = "primary"  # Read/write
    REPLICA = "replica"  # Read-only
    ANALYTICS = "analytics"  # Heavy analytical queries


class ConnectionState(Enum):
    """Connection health states"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    RECOVERING = "recovering"


@dataclass
class DatabaseNode:
    """Database node configuration"""
    host: str
    port: int = 5432
    database: str = "financial_planning"
    user: str = "postgres"
    password: str = ""
    pool_type: PoolType = PoolType.PRIMARY
    weight: int = 1  # For load balancing
    max_connections: int = 50
    min_connections: int = 10
    
    # Health check settings
    health_check_interval: int = 30  # seconds
    health_check_timeout: int = 5
    max_failures: int = 3
    
    # State tracking
    state: ConnectionState = ConnectionState.HEALTHY
    last_health_check: Optional[datetime] = None
    consecutive_failures: int = 0
    
    @property
    def dsn(self) -> str:
        """Get PostgreSQL DSN"""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"


@dataclass 
class PgBouncerConfig:
    """PgBouncer configuration"""
    enabled: bool = True
    host: str = "localhost"
    port: int = 6432
    pool_mode: str = "transaction"  # transaction, session, statement
    max_client_conn: int = 1000
    default_pool_size: int = 25
    reserve_pool_size: int = 5
    reserve_pool_timeout: int = 3
    max_db_connections: int = 100
    max_user_connections: int = 100
    
    # Performance tuning
    query_timeout: int = 0  # 0 = disabled
    query_wait_timeout: int = 120
    client_idle_timeout: int = 0
    client_login_timeout: int = 60
    
    # Security
    auth_type: str = "md5"
    auth_file: str = "/etc/pgbouncer/userlist.txt"
    
    def generate_config(self) -> str:
        """Generate PgBouncer configuration file content"""
        return f"""
[databases]
financial_planning = host={self.host} port=5432 dbname=financial_planning

[pgbouncer]
listen_addr = {self.host}
listen_port = {self.port}
auth_type = {self.auth_type}
auth_file = {self.auth_file}
pool_mode = {self.pool_mode}
max_client_conn = {self.max_client_conn}
default_pool_size = {self.default_pool_size}
reserve_pool_size = {self.reserve_pool_size}
reserve_pool_timeout = {self.reserve_pool_timeout}
max_db_connections = {self.max_db_connections}
max_user_connections = {self.max_user_connections}
query_timeout = {self.query_timeout}
query_wait_timeout = {self.query_wait_timeout}
client_idle_timeout = {self.client_idle_timeout}
client_login_timeout = {self.client_login_timeout}

# Logging
logfile = /var/log/pgbouncer/pgbouncer.log
pidfile = /var/run/pgbouncer/pgbouncer.pid

# Performance
server_reset_query = DISCARD ALL
server_reset_query_always = 0
server_check_delay = 30
server_check_query = SELECT 1
server_lifetime = 3600
server_idle_timeout = 600
server_connect_timeout = 15
server_login_retry = 15

# TLS
server_tls_sslmode = prefer
client_tls_sslmode = prefer
"""


class CircuitBreaker:
    """Circuit breaker for connection resilience"""
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: type = Exception
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = "closed"  # closed, open, half-open
        
    def call(self, func):
        """Decorator for circuit breaker protection"""
        async def wrapper(*args, **kwargs):
            if self.state == "open":
                if self._should_attempt_reset():
                    self.state = "half-open"
                else:
                    raise Exception("Circuit breaker is open")
                    
            try:
                result = await func(*args, **kwargs)
                self._on_success()
                return result
            except self.expected_exception as e:
                self._on_failure()
                raise e
                
        return wrapper
        
    def _should_attempt_reset(self) -> bool:
        """Check if we should try to reset the circuit"""
        if self.last_failure_time is None:
            return True
        return (datetime.utcnow() - self.last_failure_time).seconds >= self.recovery_timeout
        
    def _on_success(self):
        """Handle successful call"""
        self.failure_count = 0
        self.state = "closed"
        
    def _on_failure(self):
        """Handle failed call"""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "open"


class SmartConnectionPool:
    """
    Intelligent connection pool with read/write splitting and health monitoring
    """
    
    def __init__(
        self,
        nodes: List[DatabaseNode],
        pgbouncer_config: Optional[PgBouncerConfig] = None
    ):
        self.nodes = nodes
        self.pgbouncer_config = pgbouncer_config or PgBouncerConfig()
        
        # Separate nodes by type
        self.primary_nodes = [n for n in nodes if n.pool_type == PoolType.PRIMARY]
        self.replica_nodes = [n for n in nodes if n.pool_type == PoolType.REPLICA]
        self.analytics_nodes = [n for n in nodes if n.pool_type == PoolType.ANALYTICS]
        
        # Connection pools
        self.pools: Dict[str, asyncpg.Pool] = {}
        
        # Circuit breakers
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        
        # Health check tasks
        self.health_check_tasks: List[asyncio.Task] = []
        
        # Statistics
        self.stats = {
            'connections_created': 0,
            'connections_recycled': 0,
            'queries_routed': {'primary': 0, 'replica': 0, 'analytics': 0},
            'failovers': 0
        }
        
    async def setup(self) -> None:
        """Initialize connection pools"""
        for node in self.nodes:
            pool_name = f"{node.host}:{node.port}"
            
            # Use PgBouncer if enabled
            if self.pgbouncer_config.enabled:
                dsn = f"postgresql://{node.user}:{node.password}@{self.pgbouncer_config.host}:{self.pgbouncer_config.port}/{node.database}"
            else:
                dsn = node.dsn
                
            # Create connection pool
            try:
                pool = await asyncpg.create_pool(
                    dsn,
                    min_size=node.min_connections,
                    max_size=node.max_connections,
                    max_queries=50000,
                    max_inactive_connection_lifetime=300,
                    timeout=10,
                    command_timeout=10,
                    setup=self._setup_connection,
                    init=self._init_connection
                )
                
                self.pools[pool_name] = pool
                
                # Create circuit breaker
                self.circuit_breakers[pool_name] = CircuitBreaker(
                    failure_threshold=node.max_failures,
                    recovery_timeout=60
                )
                
                # Start health check
                health_task = asyncio.create_task(
                    self._health_check_loop(node)
                )
                self.health_check_tasks.append(health_task)
                
                pool_connections.labels(pool=pool_name, state='active').set(pool.get_size())
                
            except Exception as e:
                print(f"Failed to create pool for {pool_name}: {e}")
                node.state = ConnectionState.UNHEALTHY
                pool_errors.labels(pool=pool_name, error_type='setup').inc()
                
    async def _setup_connection(self, connection):
        """Setup new connection"""
        # Set connection parameters for performance
        await connection.execute("SET work_mem = '256MB'")
        await connection.execute("SET maintenance_work_mem = '512MB'")
        await connection.execute("SET effective_cache_size = '4GB'")
        await connection.execute("SET random_page_cost = 1.1")
        await connection.execute("SET effective_io_concurrency = 200")
        await connection.execute("SET max_parallel_workers_per_gather = 4")
        
        # Set application name for monitoring
        await connection.execute("SET application_name = 'financial_planner_optimized'")
        
        self.stats['connections_created'] += 1
        
    async def _init_connection(self, connection):
        """Initialize connection from pool"""
        # Prepare commonly used statements
        await connection.execute("PREPARE get_user AS SELECT * FROM users WHERE id = $1")
        await connection.execute("PREPARE get_portfolio AS SELECT * FROM portfolios WHERE user_id = $1")
        
    async def _health_check_loop(self, node: DatabaseNode) -> None:
        """Background health check for a node"""
        pool_name = f"{node.host}:{node.port}"
        
        while True:
            try:
                await asyncio.sleep(node.health_check_interval)
                
                # Perform health check
                pool = self.pools.get(pool_name)
                if not pool:
                    node.state = ConnectionState.UNHEALTHY
                    continue
                    
                async with pool.acquire() as conn:
                    # Set timeout for health check
                    await asyncio.wait_for(
                        conn.fetchval("SELECT 1"),
                        timeout=node.health_check_timeout
                    )
                    
                # Health check passed
                if node.state != ConnectionState.HEALTHY:
                    print(f"Node {pool_name} recovered")
                    node.state = ConnectionState.HEALTHY
                    
                node.consecutive_failures = 0
                node.last_health_check = datetime.utcnow()
                
            except asyncio.TimeoutError:
                node.consecutive_failures += 1
                if node.consecutive_failures >= node.max_failures:
                    node.state = ConnectionState.UNHEALTHY
                    print(f"Node {pool_name} marked unhealthy (timeout)")
                    pool_errors.labels(pool=pool_name, error_type='health_check_timeout').inc()
                    
            except Exception as e:
                node.consecutive_failures += 1
                if node.consecutive_failures >= node.max_failures:
                    node.state = ConnectionState.UNHEALTHY
                    print(f"Node {pool_name} marked unhealthy: {e}")
                    pool_errors.labels(pool=pool_name, error_type='health_check_error').inc()
                    
    def _select_node(self, pool_type: PoolType, prefer_primary: bool = False) -> Optional[DatabaseNode]:
        """
        Select a healthy node for the query
        
        Args:
            pool_type: Type of pool to select from
            prefer_primary: Whether to prefer primary even for reads
            
        Returns:
            Selected node or None if no healthy nodes
        """
        # Get candidate nodes
        if pool_type == PoolType.PRIMARY or prefer_primary:
            candidates = self.primary_nodes
        elif pool_type == PoolType.REPLICA:
            candidates = self.replica_nodes or self.primary_nodes  # Fallback to primary
        else:
            candidates = self.analytics_nodes or self.replica_nodes or self.primary_nodes
            
        # Filter healthy nodes
        healthy_nodes = [n for n in candidates if n.state == ConnectionState.HEALTHY]
        
        if not healthy_nodes:
            # Try degraded nodes as last resort
            healthy_nodes = [n for n in candidates if n.state == ConnectionState.DEGRADED]
            
        if not healthy_nodes:
            return None
            
        # Weighted random selection
        total_weight = sum(n.weight for n in healthy_nodes)
        if total_weight == 0:
            return None
            
        rand = random.uniform(0, total_weight)
        cumulative_weight = 0
        
        for node in healthy_nodes:
            cumulative_weight += node.weight
            if rand <= cumulative_weight:
                return node
                
        return healthy_nodes[-1]  # Fallback
        
    @asynccontextmanager
    async def acquire(self, pool_type: PoolType = PoolType.PRIMARY, prefer_primary: bool = False):
        """
        Acquire a connection from the pool
        
        Args:
            pool_type: Type of pool to use
            prefer_primary: Force using primary for reads
            
        Yields:
            Database connection
        """
        start_time = time.time()
        
        # Select node
        node = self._select_node(pool_type, prefer_primary)
        if not node:
            raise Exception(f"No healthy nodes available for {pool_type.value}")
            
        pool_name = f"{node.host}:{node.port}"
        pool = self.pools.get(pool_name)
        
        if not pool:
            raise Exception(f"Pool not found for {pool_name}")
            
        # Record wait time
        wait_time = time.time() - start_time
        pool_wait_time.labels(pool=pool_name).observe(wait_time)
        
        # Update routing metrics
        query_routing.labels(destination=pool_type.value).inc()
        self.stats['queries_routed'][pool_type.value] += 1
        
        # Acquire connection with circuit breaker
        circuit_breaker = self.circuit_breakers.get(pool_name)
        
        @circuit_breaker.call
        async def get_connection():
            return await pool.acquire()
            
        try:
            conn = await get_connection()
            yield conn
        finally:
            if conn:
                await pool.release(conn)
                
    async def execute_read(self, query: str, *args, prefer_primary: bool = False) -> Any:
        """Execute a read query with automatic routing"""
        async with self.acquire(PoolType.REPLICA, prefer_primary) as conn:
            return await conn.fetch(query, *args)
            
    async def execute_write(self, query: str, *args) -> Any:
        """Execute a write query on primary"""
        async with self.acquire(PoolType.PRIMARY) as conn:
            return await conn.execute(query, *args)
            
    async def execute_analytics(self, query: str, *args) -> Any:
        """Execute heavy analytical query"""
        async with self.acquire(PoolType.ANALYTICS) as conn:
            # Set longer timeout for analytical queries
            await conn.execute("SET statement_timeout = '5min'")
            return await conn.fetch(query, *args)
            
    async def transaction(self):
        """Start a transaction (always on primary)"""
        async with self.acquire(PoolType.PRIMARY) as conn:
            async with conn.transaction():
                yield conn
                
    async def close(self) -> None:
        """Close all connection pools"""
        # Cancel health check tasks
        for task in self.health_check_tasks:
            task.cancel()
            
        # Close all pools
        for pool_name, pool in self.pools.items():
            await pool.close()
            
    def get_stats(self) -> Dict[str, Any]:
        """Get connection pool statistics"""
        pool_stats = {}
        
        for pool_name, pool in self.pools.items():
            pool_stats[pool_name] = {
                'size': pool.get_size(),
                'idle': pool.get_idle_size(),
                'max_size': pool.get_max_size(),
                'min_size': pool.get_min_size()
            }
            
        return {
            'pools': pool_stats,
            'routing': self.stats['queries_routed'],
            'connections_created': self.stats['connections_created'],
            'failovers': self.stats['failovers']
        }


# Example configuration
def create_production_pool() -> SmartConnectionPool:
    """Create production-ready connection pool"""
    
    nodes = [
        # Primary database
        DatabaseNode(
            host="primary.db.example.com",
            pool_type=PoolType.PRIMARY,
            max_connections=100,
            min_connections=20,
            weight=1
        ),
        
        # Read replicas
        DatabaseNode(
            host="replica1.db.example.com",
            pool_type=PoolType.REPLICA,
            max_connections=50,
            min_connections=10,
            weight=1
        ),
        DatabaseNode(
            host="replica2.db.example.com",
            pool_type=PoolType.REPLICA,
            max_connections=50,
            min_connections=10,
            weight=1
        ),
        
        # Analytics replica (for heavy queries)
        DatabaseNode(
            host="analytics.db.example.com",
            pool_type=PoolType.ANALYTICS,
            max_connections=20,
            min_connections=5,
            weight=1
        )
    ]
    
    pgbouncer_config = PgBouncerConfig(
        enabled=True,
        pool_mode="transaction",
        max_client_conn=2000,
        default_pool_size=50
    )
    
    return SmartConnectionPool(nodes, pgbouncer_config)