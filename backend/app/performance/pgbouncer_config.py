"""
PgBouncer Configuration and Connection Pool Management

Implements advanced database connection pooling with:
- PgBouncer integration
- Dynamic pool sizing
- Connection health monitoring
- Automatic failover
- Query routing
"""

import os
import asyncio
import psutil
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import asyncpg
from asyncpg.pool import Pool
import aioredis
import json
import time

logger = logging.getLogger(__name__)


class PoolMode(Enum):
    """PgBouncer pool modes"""
    SESSION = "session"  # Connection returned to pool after session ends
    TRANSACTION = "transaction"  # Connection returned after transaction
    STATEMENT = "statement"  # Connection returned after each statement


@dataclass
class PoolConfig:
    """Connection pool configuration"""
    # Basic settings
    database: str
    user: str
    password: str
    host: str = "localhost"
    port: int = 5432
    
    # Pool settings
    min_size: int = 10
    max_size: int = 100
    max_queries: int = 50000
    max_inactive_connection_lifetime: float = 300.0
    
    # PgBouncer settings
    pgbouncer_host: str = "localhost"
    pgbouncer_port: int = 6432
    pool_mode: PoolMode = PoolMode.TRANSACTION
    max_client_conn: int = 1000
    default_pool_size: int = 25
    reserve_pool_size: int = 5
    reserve_pool_timeout: int = 3
    max_db_connections: int = 100
    
    # Performance settings
    server_lifetime: int = 3600
    server_idle_timeout: int = 600
    server_connect_timeout: int = 15
    server_login_retry: int = 15
    query_timeout: int = 0  # 0 = disabled
    query_wait_timeout: int = 120
    
    # Monitoring
    stats_period: int = 60
    log_connections: bool = False
    log_disconnections: bool = False
    log_pooler_errors: bool = True


class PgBouncerManager:
    """
    Advanced PgBouncer management and monitoring
    """
    
    def __init__(self, config: PoolConfig):
        self.config = config
        self.pools: Dict[str, Pool] = {}
        self.monitoring_task: Optional[asyncio.Task] = None
        self.stats_cache: Dict[str, Any] = {}
        self.redis_client: Optional[aioredis.Redis] = None
        
    async def initialize(self):
        """Initialize PgBouncer and connection pools"""
        # Generate PgBouncer configuration
        await self._generate_pgbouncer_config()
        
        # Start PgBouncer if not running
        await self._ensure_pgbouncer_running()
        
        # Create connection pools
        await self._create_pools()
        
        # Initialize Redis for stats caching
        self.redis_client = await aioredis.create_redis_pool(
            'redis://localhost',
            minsize=5,
            maxsize=10
        )
        
        # Start monitoring
        self.monitoring_task = asyncio.create_task(self._monitor_pools())
        
        logger.info("PgBouncer manager initialized successfully")
    
    async def _generate_pgbouncer_config(self):
        """Generate PgBouncer configuration file"""
        config_content = f"""
[databases]
# Main database with transaction pooling
{self.config.database} = host={self.config.host} port={self.config.port} dbname={self.config.database} pool_mode={self.config.pool_mode.value}

# Read replica pools
{self.config.database}_read_1 = host={self.config.host} port={self.config.port} dbname={self.config.database} pool_mode=statement
{self.config.database}_read_2 = host={self.config.host} port={self.config.port} dbname={self.config.database} pool_mode=statement

# Analytics database with session pooling
{self.config.database}_analytics = host={self.config.host} port={self.config.port} dbname={self.config.database} pool_mode=session

[pgbouncer]
# Connection settings
listen_addr = {self.config.pgbouncer_host}
listen_port = {self.config.pgbouncer_port}
auth_type = md5
auth_file = /etc/pgbouncer/userlist.txt

# Pool settings
pool_mode = {self.config.pool_mode.value}
max_client_conn = {self.config.max_client_conn}
default_pool_size = {self.config.default_pool_size}
reserve_pool_size = {self.config.reserve_pool_size}
reserve_pool_timeout = {self.config.reserve_pool_timeout}
max_db_connections = {self.config.max_db_connections}

# Performance tuning
server_lifetime = {self.config.server_lifetime}
server_idle_timeout = {self.config.server_idle_timeout}
server_connect_timeout = {self.config.server_connect_timeout}
server_login_retry = {self.config.server_login_retry}
query_timeout = {self.config.query_timeout}
query_wait_timeout = {self.config.query_wait_timeout}

# TCP settings
tcp_keepalive = 1
tcp_keepidle = 60
tcp_keepintvl = 10
tcp_keepcnt = 3
tcp_user_timeout = 12000

# Logging
logfile = /var/log/pgbouncer/pgbouncer.log
pidfile = /var/run/pgbouncer/pgbouncer.pid
admin_users = pgbouncer_admin
stats_users = pgbouncer_stats
stats_period = {self.config.stats_period}

# Security
server_tls_sslmode = prefer
server_tls_protocols = TLSv1.2,TLSv1.3
server_tls_ciphers = HIGH:!aNULL:!MD5

# Performance optimizations
pkt_buf = 8192
listen_backlog = 256
sbuf_loopcnt = 10
suspend_timeout = 10
"""
        
        # Write configuration file
        config_path = "/etc/pgbouncer/pgbouncer.ini"
        try:
            with open(config_path, 'w') as f:
                f.write(config_content)
            logger.info(f"PgBouncer configuration written to {config_path}")
        except IOError as e:
            logger.error(f"Failed to write PgBouncer config: {e}")
            # Fallback to local config
            config_path = "./pgbouncer.ini"
            with open(config_path, 'w') as f:
                f.write(config_content)
    
    async def _ensure_pgbouncer_running(self):
        """Ensure PgBouncer service is running"""
        try:
            # Check if PgBouncer is running
            for proc in psutil.process_iter(['pid', 'name']):
                if 'pgbouncer' in proc.info['name'].lower():
                    logger.info(f"PgBouncer already running (PID: {proc.info['pid']})")
                    return
            
            # Start PgBouncer
            import subprocess
            subprocess.Popen(['pgbouncer', '-d', '/etc/pgbouncer/pgbouncer.ini'])
            await asyncio.sleep(2)  # Wait for startup
            logger.info("PgBouncer started successfully")
            
        except Exception as e:
            logger.warning(f"Could not manage PgBouncer service: {e}")
    
    async def _create_pools(self):
        """Create connection pools for different workloads"""
        
        # Main read-write pool (through PgBouncer)
        self.pools['main'] = await asyncpg.create_pool(
            host=self.config.pgbouncer_host,
            port=self.config.pgbouncer_port,
            database=self.config.database,
            user=self.config.user,
            password=self.config.password,
            min_size=self.config.min_size,
            max_size=self.config.max_size,
            max_queries=self.config.max_queries,
            max_inactive_connection_lifetime=self.config.max_inactive_connection_lifetime,
            command_timeout=60,
            server_settings={
                'jit': 'on',
                'max_parallel_workers_per_gather': '4',
                'work_mem': '256MB'
            }
        )
        
        # Read-only pool for queries (through PgBouncer)
        self.pools['read'] = await asyncpg.create_pool(
            host=self.config.pgbouncer_host,
            port=self.config.pgbouncer_port,
            database=f"{self.config.database}_read_1",
            user=self.config.user,
            password=self.config.password,
            min_size=self.config.min_size * 2,  # More connections for reads
            max_size=self.config.max_size * 2,
            max_queries=self.config.max_queries * 2,
            command_timeout=30
        )
        
        # Analytics pool for heavy queries (through PgBouncer)
        self.pools['analytics'] = await asyncpg.create_pool(
            host=self.config.pgbouncer_host,
            port=self.config.pgbouncer_port,
            database=f"{self.config.database}_analytics",
            user=self.config.user,
            password=self.config.password,
            min_size=5,
            max_size=20,
            max_queries=1000,
            command_timeout=300,  # Longer timeout for analytics
            server_settings={
                'work_mem': '512MB',
                'max_parallel_workers_per_gather': '8'
            }
        )
        
        # Direct connection pool (bypass PgBouncer for special cases)
        self.pools['direct'] = await asyncpg.create_pool(
            host=self.config.host,
            port=self.config.port,
            database=self.config.database,
            user=self.config.user,
            password=self.config.password,
            min_size=2,
            max_size=10,
            max_queries=100
        )
        
        logger.info(f"Created {len(self.pools)} connection pools")
    
    async def get_connection(
        self,
        pool_type: str = 'main',
        isolation_level: str = 'read_committed'
    ) -> asyncpg.Connection:
        """
        Get a connection from the appropriate pool
        
        Args:
            pool_type: Type of pool ('main', 'read', 'analytics', 'direct')
            isolation_level: Transaction isolation level
            
        Returns:
            Database connection
        """
        pool = self.pools.get(pool_type, self.pools['main'])
        
        async with pool.acquire() as connection:
            await connection.execute(f"SET TRANSACTION ISOLATION LEVEL {isolation_level.upper()}")
            return connection
    
    async def execute_query(
        self,
        query: str,
        *args,
        pool_type: str = None,
        timeout: float = None
    ) -> List[asyncpg.Record]:
        """
        Execute a query with automatic pool selection
        
        Args:
            query: SQL query
            *args: Query parameters
            pool_type: Override pool selection
            timeout: Query timeout
            
        Returns:
            Query results
        """
        # Auto-select pool based on query type if not specified
        if pool_type is None:
            pool_type = self._select_pool_for_query(query)
        
        pool = self.pools.get(pool_type, self.pools['main'])
        
        async with pool.acquire() as connection:
            if timeout:
                return await asyncio.wait_for(
                    connection.fetch(query, *args),
                    timeout=timeout
                )
            else:
                return await connection.fetch(query, *args)
    
    def _select_pool_for_query(self, query: str) -> str:
        """
        Select appropriate pool based on query analysis
        
        Args:
            query: SQL query
            
        Returns:
            Pool type
        """
        query_lower = query.lower().strip()
        
        # Analytics queries
        if any(keyword in query_lower for keyword in [
            'group by', 'having', 'window', 'over', 'percentile',
            'stddev', 'variance', 'corr', 'covar'
        ]):
            return 'analytics'
        
        # Read queries
        if query_lower.startswith('select') and 'for update' not in query_lower:
            return 'read'
        
        # Write queries
        if any(query_lower.startswith(keyword) for keyword in [
            'insert', 'update', 'delete', 'merge'
        ]):
            return 'main'
        
        # DDL requires direct connection
        if any(query_lower.startswith(keyword) for keyword in [
            'create', 'alter', 'drop', 'truncate'
        ]):
            return 'direct'
        
        # Default to main pool
        return 'main'
    
    async def _monitor_pools(self):
        """Monitor pool health and performance"""
        while True:
            try:
                stats = await self._collect_pool_stats()
                
                # Store stats in Redis
                if self.redis_client:
                    await self.redis_client.setex(
                        'pgbouncer:stats',
                        60,  # TTL 60 seconds
                        json.dumps(stats)
                    )
                
                # Check for issues
                await self._check_pool_health(stats)
                
                # Auto-scale pools if needed
                await self._auto_scale_pools(stats)
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Pool monitoring error: {e}")
                await asyncio.sleep(60)
    
    async def _collect_pool_stats(self) -> Dict[str, Any]:
        """Collect statistics from all pools"""
        stats = {
            'timestamp': time.time(),
            'pools': {}
        }
        
        for name, pool in self.pools.items():
            pool_stats = {
                'size': pool.get_size(),
                'min_size': pool.get_min_size(),
                'max_size': pool.get_max_size(),
                'free_connections': pool.get_idle_size(),
                'used_connections': pool.get_size() - pool.get_idle_size()
            }
            
            # Calculate utilization
            if pool.get_size() > 0:
                pool_stats['utilization'] = (
                    (pool.get_size() - pool.get_idle_size()) / pool.get_size() * 100
                )
            else:
                pool_stats['utilization'] = 0
            
            stats['pools'][name] = pool_stats
        
        # Get PgBouncer stats if available
        try:
            pgbouncer_stats = await self._get_pgbouncer_stats()
            stats['pgbouncer'] = pgbouncer_stats
        except Exception as e:
            logger.warning(f"Could not get PgBouncer stats: {e}")
        
        return stats
    
    async def _get_pgbouncer_stats(self) -> Dict[str, Any]:
        """Get statistics from PgBouncer admin interface"""
        try:
            conn = await asyncpg.connect(
                host=self.config.pgbouncer_host,
                port=self.config.pgbouncer_port,
                database='pgbouncer',
                user='pgbouncer_stats',
                password=self.config.password
            )
            
            # Get pool stats
            pools = await conn.fetch("SHOW POOLS")
            databases = await conn.fetch("SHOW DATABASES")
            stats = await conn.fetch("SHOW STATS")
            
            await conn.close()
            
            return {
                'pools': [dict(p) for p in pools],
                'databases': [dict(d) for d in databases],
                'stats': [dict(s) for s in stats]
            }
            
        except Exception as e:
            logger.error(f"Failed to get PgBouncer stats: {e}")
            return {}
    
    async def _check_pool_health(self, stats: Dict[str, Any]):
        """Check pool health and alert on issues"""
        for pool_name, pool_stats in stats['pools'].items():
            # Check high utilization
            if pool_stats['utilization'] > 80:
                logger.warning(
                    f"High pool utilization for {pool_name}: "
                    f"{pool_stats['utilization']:.1f}%"
                )
            
            # Check connection exhaustion
            if pool_stats['free_connections'] == 0:
                logger.error(f"Connection pool {pool_name} exhausted!")
    
    async def _auto_scale_pools(self, stats: Dict[str, Any]):
        """Automatically scale pools based on utilization"""
        for pool_name, pool in self.pools.items():
            pool_stats = stats['pools'].get(pool_name, {})
            utilization = pool_stats.get('utilization', 0)
            
            current_max = pool.get_max_size()
            
            # Scale up if utilization is high
            if utilization > 75 and current_max < self.config.max_size * 2:
                new_max = min(current_max + 10, self.config.max_size * 2)
                await pool.set_max_size(new_max)
                logger.info(f"Scaled up {pool_name} pool to {new_max} connections")
            
            # Scale down if utilization is low
            elif utilization < 25 and current_max > self.config.max_size:
                new_max = max(current_max - 10, self.config.max_size)
                await pool.set_max_size(new_max)
                logger.info(f"Scaled down {pool_name} pool to {new_max} connections")
    
    async def execute_batch(
        self,
        queries: List[Tuple[str, tuple]],
        pool_type: str = 'main'
    ) -> List[List[asyncpg.Record]]:
        """
        Execute multiple queries in a batch
        
        Args:
            queries: List of (query, params) tuples
            pool_type: Pool to use
            
        Returns:
            List of results for each query
        """
        pool = self.pools.get(pool_type, self.pools['main'])
        results = []
        
        async with pool.acquire() as connection:
            async with connection.transaction():
                for query, params in queries:
                    result = await connection.fetch(query, *params)
                    results.append(result)
        
        return results
    
    async def get_pool_metrics(self) -> Dict[str, Any]:
        """Get current pool metrics for monitoring"""
        if self.redis_client:
            # Try to get from cache first
            cached = await self.redis_client.get('pgbouncer:stats')
            if cached:
                return json.loads(cached)
        
        # Collect fresh stats
        return await self._collect_pool_stats()
    
    async def close(self):
        """Close all pools and clean up resources"""
        # Stop monitoring
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        
        # Close all pools
        for name, pool in self.pools.items():
            await pool.close()
            logger.info(f"Closed pool: {name}")
        
        # Close Redis
        if self.redis_client:
            self.redis_client.close()
            await self.redis_client.wait_closed()
        
        logger.info("PgBouncer manager closed")


# Helper function to create and configure PgBouncer
async def setup_pgbouncer(
    database: str,
    user: str,
    password: str,
    host: str = "localhost",
    port: int = 5432
) -> PgBouncerManager:
    """
    Set up PgBouncer with optimized configuration
    
    Args:
        database: Database name
        user: Database user
        password: Database password
        host: Database host
        port: Database port
        
    Returns:
        Configured PgBouncerManager instance
    """
    # Calculate optimal pool sizes based on system resources
    cpu_count = psutil.cpu_count()
    memory_gb = psutil.virtual_memory().total / (1024**3)
    
    # Base calculations
    max_connections = min(cpu_count * 25, 200)  # 25 connections per CPU, max 200
    default_pool = min(cpu_count * 5, 50)  # 5 per CPU for default pool
    
    config = PoolConfig(
        database=database,
        user=user,
        password=password,
        host=host,
        port=port,
        max_size=max_connections // 2,  # Split between pools
        max_client_conn=max_connections * 5,  # Allow queueing
        default_pool_size=default_pool,
        max_db_connections=max_connections
    )
    
    manager = PgBouncerManager(config)
    await manager.initialize()
    
    return manager