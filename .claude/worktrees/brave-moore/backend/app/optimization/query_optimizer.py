"""
Query Optimizer for High-Performance Database Operations

This module implements sophisticated query optimization techniques:
- Eager loading with intelligent prefetching
- Query result caching with dependency tracking
- Query plan analysis and optimization
- Automatic index recommendation
- Connection pooling with load balancing
- Query batching and pipelining

Target: sub-100ms p50, sub-500ms p99 response times
"""

import asyncio
import hashlib
import json
import time
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Type, Union

import asyncpg
from prometheus_client import Counter, Histogram, Gauge
from sqlalchemy import create_engine, event, pool, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import Session, selectinload, joinedload, subqueryload, contains_eager
from sqlalchemy.orm import Query
from sqlalchemy.pool import QueuePool, NullPool
from sqlalchemy.sql import Select
import numpy as np


# Metrics
query_duration = Histogram('query_duration_seconds', 'Query execution time', ['query_type', 'table'])
query_cache_hits = Counter('query_cache_hits_total', 'Query cache hits', ['query_type'])
query_cache_misses = Counter('query_cache_misses_total', 'Query cache misses', ['query_type'])
connection_pool_size = Gauge('connection_pool_size', 'Current connection pool size')
connection_wait_time = Histogram('connection_wait_time_seconds', 'Time waiting for connection')
query_batch_size = Histogram('query_batch_size', 'Number of queries in batch')


class LoadingStrategy(Enum):
    """ORM loading strategies"""
    LAZY = "lazy"  # Default lazy loading
    EAGER_JOINED = "joined"  # Single JOIN query
    EAGER_SUBQUERY = "subquery"  # Separate query per relationship
    EAGER_SELECT = "selectin"  # IN clause for collections
    IMMEDIATE = "immediate"  # Load immediately with parent


class QueryType(Enum):
    """Query classification for optimization"""
    POINT_LOOKUP = "point"  # Single row by primary key
    RANGE_SCAN = "range"  # Range of rows
    FULL_SCAN = "full"  # Full table scan
    JOIN = "join"  # Multi-table join
    AGGREGATION = "aggregation"  # GROUP BY queries
    BATCH = "batch"  # Batched operations


@dataclass
class QueryStats:
    """Query execution statistics"""
    query: str
    execution_time: float
    rows_returned: int
    plan: Optional[str] = None
    cache_hit: bool = False
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ConnectionPoolConfig:
    """Database connection pool configuration"""
    min_size: int = 10
    max_size: int = 50
    max_overflow: int = 20
    pool_timeout: float = 30.0
    pool_recycle: int = 3600  # Recycle connections after 1 hour
    pool_pre_ping: bool = True  # Test connections before use
    echo_pool: bool = False
    
    # Advanced settings
    use_lifo: bool = True  # LIFO for better connection reuse
    max_queries_per_connection: int = 1000
    connection_lifetime: int = 7200  # 2 hours
    
    # PgBouncer integration
    use_pgbouncer: bool = True
    pgbouncer_host: str = "localhost"
    pgbouncer_port: int = 6432
    pgbouncer_pool_mode: str = "transaction"  # transaction, session, statement


@dataclass
class QueryCacheConfig:
    """Query cache configuration"""
    enabled: bool = True
    max_size: int = 10000
    ttl: int = 300  # 5 minutes default
    invalidation_strategy: str = "time_based"  # time_based, dependency_based
    cache_select: bool = True
    cache_insert: bool = False
    cache_update: bool = False
    cache_delete: bool = False


class QueryPlanAnalyzer:
    """Analyze and optimize query execution plans"""
    
    def __init__(self, connection):
        self.connection = connection
        self.plan_cache: Dict[str, Dict] = {}
        self.index_recommendations: Dict[str, List[str]] = defaultdict(list)
        
    async def analyze_query(self, query: str, params: Optional[Dict] = None) -> Dict:
        """Analyze query execution plan"""
        # Get query hash
        query_hash = hashlib.md5(query.encode()).hexdigest()
        
        # Check cache
        if query_hash in self.plan_cache:
            return self.plan_cache[query_hash]
            
        # Get execution plan
        explain_query = f"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) {query}"
        
        try:
            if isinstance(self.connection, AsyncSession):
                result = await self.connection.execute(text(explain_query), params or {})
                plan = result.scalar()
            else:
                result = await self.connection.fetchval(explain_query, **(params or {}))
                plan = result
                
            analysis = self._parse_plan(plan)
            
            # Cache the analysis
            self.plan_cache[query_hash] = analysis
            
            # Generate index recommendations
            self._recommend_indexes(analysis)
            
            return analysis
            
        except Exception as e:
            return {'error': str(e), 'query': query}
            
    def _parse_plan(self, plan_json: str) -> Dict:
        """Parse execution plan JSON"""
        try:
            plan = json.loads(plan_json) if isinstance(plan_json, str) else plan_json
            
            # Extract key metrics
            if isinstance(plan, list) and len(plan) > 0:
                root_plan = plan[0].get('Plan', {})
            else:
                root_plan = plan.get('Plan', {})
                
            return {
                'total_cost': root_plan.get('Total Cost', 0),
                'execution_time': plan[0].get('Execution Time', 0) if isinstance(plan, list) else 0,
                'planning_time': plan[0].get('Planning Time', 0) if isinstance(plan, list) else 0,
                'rows': root_plan.get('Plan Rows', 0),
                'width': root_plan.get('Plan Width', 0),
                'node_type': root_plan.get('Node Type', ''),
                'index_used': self._extract_index_usage(root_plan),
                'join_type': root_plan.get('Join Type', ''),
                'scan_type': self._get_scan_type(root_plan)
            }
        except Exception as e:
            return {'error': f'Failed to parse plan: {e}'}
            
    def _extract_index_usage(self, plan: Dict) -> List[str]:
        """Extract indexes used in the plan"""
        indexes = []
        
        if 'Index Name' in plan:
            indexes.append(plan['Index Name'])
            
        # Recursively check child plans
        for child in plan.get('Plans', []):
            indexes.extend(self._extract_index_usage(child))
            
        return indexes
        
    def _get_scan_type(self, plan: Dict) -> str:
        """Determine scan type from plan"""
        node_type = plan.get('Node Type', '')
        
        if 'Index' in node_type:
            return 'index_scan'
        elif 'Seq Scan' in node_type:
            return 'sequential_scan'
        elif 'Bitmap' in node_type:
            return 'bitmap_scan'
        else:
            return 'unknown'
            
    def _recommend_indexes(self, analysis: Dict) -> None:
        """Generate index recommendations based on analysis"""
        if analysis.get('scan_type') == 'sequential_scan' and analysis.get('total_cost', 0) > 1000:
            # Recommend index for expensive sequential scans
            # This is simplified - real implementation would analyze WHERE clauses
            recommendation = "Consider adding an index on frequently filtered columns"
            self.index_recommendations['general'].append(recommendation)


class QueryCache:
    """LRU cache for query results with dependency tracking"""
    
    def __init__(self, config: QueryCacheConfig):
        self.config = config
        self.cache: Dict[str, Tuple[Any, datetime, Set[str]]] = {}
        self.access_order: deque = deque(maxlen=config.max_size)
        self.dependencies: Dict[str, Set[str]] = defaultdict(set)  # table -> query keys
        self.lock = asyncio.Lock()
        
    def _generate_key(self, query: str, params: Optional[Dict] = None) -> str:
        """Generate cache key from query and parameters"""
        key_parts = [query]
        if params:
            key_parts.append(json.dumps(params, sort_keys=True))
        return hashlib.sha256(''.join(key_parts).encode()).hexdigest()
        
    async def get(self, query: str, params: Optional[Dict] = None) -> Optional[Any]:
        """Get cached query result"""
        if not self.config.enabled:
            return None
            
        key = self._generate_key(query, params)
        
        async with self.lock:
            if key in self.cache:
                result, timestamp, tables = self.cache[key]
                
                # Check TTL
                if (datetime.utcnow() - timestamp).seconds > self.config.ttl:
                    del self.cache[key]
                    query_cache_misses.labels(query_type=self._get_query_type(query)).inc()
                    return None
                    
                # Update access order
                self.access_order.remove(key)
                self.access_order.append(key)
                
                query_cache_hits.labels(query_type=self._get_query_type(query)).inc()
                return result
                
        query_cache_misses.labels(query_type=self._get_query_type(query)).inc()
        return None
        
    async def set(
        self,
        query: str,
        result: Any,
        params: Optional[Dict] = None,
        tables: Optional[Set[str]] = None
    ) -> None:
        """Cache query result"""
        if not self.config.enabled:
            return
            
        # Check if query type should be cached
        query_type = self._get_query_type(query)
        if query_type == 'select' and not self.config.cache_select:
            return
        elif query_type == 'insert' and not self.config.cache_insert:
            return
        elif query_type == 'update' and not self.config.cache_update:
            return
        elif query_type == 'delete' and not self.config.cache_delete:
            return
            
        key = self._generate_key(query, params)
        
        async with self.lock:
            # Evict if at capacity
            if len(self.cache) >= self.config.max_size and key not in self.cache:
                oldest_key = self.access_order.popleft()
                old_result, _, old_tables = self.cache[oldest_key]
                del self.cache[oldest_key]
                
                # Remove from dependencies
                for table in old_tables:
                    self.dependencies[table].discard(oldest_key)
                    
            # Add to cache
            self.cache[key] = (result, datetime.utcnow(), tables or set())
            self.access_order.append(key)
            
            # Track dependencies
            if tables:
                for table in tables:
                    self.dependencies[table].add(key)
                    
    async def invalidate_table(self, table: str) -> None:
        """Invalidate all cached queries for a table"""
        async with self.lock:
            keys_to_invalidate = list(self.dependencies.get(table, set()))
            
            for key in keys_to_invalidate:
                if key in self.cache:
                    del self.cache[key]
                    try:
                        self.access_order.remove(key)
                    except ValueError:
                        pass
                        
            # Clear dependency tracking
            self.dependencies[table].clear()
            
    async def invalidate_all(self) -> None:
        """Clear entire cache"""
        async with self.lock:
            self.cache.clear()
            self.access_order.clear()
            self.dependencies.clear()
            
    def _get_query_type(self, query: str) -> str:
        """Determine query type from SQL"""
        query_lower = query.lower().strip()
        
        if query_lower.startswith('select'):
            return 'select'
        elif query_lower.startswith('insert'):
            return 'insert'
        elif query_lower.startswith('update'):
            return 'update'
        elif query_lower.startswith('delete'):
            return 'delete'
        else:
            return 'other'


class ConnectionPoolManager:
    """Advanced connection pool manager with PgBouncer support"""
    
    def __init__(self, database_url: str, config: Optional[ConnectionPoolConfig] = None):
        self.database_url = database_url
        self.config = config or ConnectionPoolConfig()
        self.engine: Optional[Engine] = None
        self.async_engine = None
        self.stats = {
            'connections_created': 0,
            'connections_recycled': 0,
            'connections_overflow': 0,
            'wait_time_total': 0.0
        }
        
    async def setup(self) -> None:
        """Initialize connection pools"""
        # Modify URL for PgBouncer if enabled
        if self.config.use_pgbouncer:
            # Parse and modify connection string for PgBouncer
            import urllib.parse
            parsed = urllib.parse.urlparse(self.database_url)
            pgbouncer_url = parsed._replace(
                netloc=f"{parsed.username}:{parsed.password}@{self.config.pgbouncer_host}:{self.config.pgbouncer_port}"
            ).geturl()
            url = pgbouncer_url
        else:
            url = self.database_url
            
        # Create async engine with optimized pool settings
        self.async_engine = create_async_engine(
            url,
            pool_size=self.config.min_size,
            max_overflow=self.config.max_overflow,
            pool_timeout=self.config.pool_timeout,
            pool_recycle=self.config.pool_recycle,
            pool_pre_ping=self.config.pool_pre_ping,
            echo_pool=self.config.echo_pool,
            pool_use_lifo=self.config.use_lifo,
            connect_args={
                "server_settings": {
                    "jit": "off",  # Disable JIT for consistent performance
                    "application_name": "financial_planner"
                },
                "command_timeout": 60,
                "prepared_statement_cache_size": 0,  # Disable for PgBouncer compatibility
                "prepared_statement_name_func": lambda: None  # For PgBouncer
            }
        )
        
        # Setup event listeners for monitoring
        @event.listens_for(self.async_engine.sync_engine, "connect")
        def receive_connect(dbapi_conn, connection_record):
            """Configure connection on creation"""
            self.stats['connections_created'] += 1
            connection_pool_size.inc()
            
            # Set connection parameters for optimization
            with dbapi_conn.cursor() as cursor:
                cursor.execute("SET work_mem = '256MB'")
                cursor.execute("SET effective_cache_size = '4GB'")
                cursor.execute("SET random_page_cost = 1.1")
                cursor.execute("SET enable_seqscan = off")  # Prefer indexes
                
        @event.listens_for(self.async_engine.sync_engine, "close")
        def receive_close(dbapi_conn, connection_record):
            """Handle connection close"""
            connection_pool_size.dec()
            
    async def get_connection(self) -> AsyncSession:
        """Get a database connection from the pool"""
        start_time = time.time()
        
        async_session = async_sessionmaker(
            self.async_engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        session = async_session()
        
        wait_time = time.time() - start_time
        self.stats['wait_time_total'] += wait_time
        connection_wait_time.observe(wait_time)
        
        return session
        
    @asynccontextmanager
    async def transaction(self):
        """Context manager for database transactions"""
        async with self.get_connection() as session:
            async with session.begin():
                yield session
                
    async def execute_batch(self, queries: List[Tuple[str, Dict]]) -> List[Any]:
        """Execute multiple queries in a single round trip"""
        query_batch_size.observe(len(queries))
        
        results = []
        async with self.get_connection() as session:
            async with session.begin():
                for query, params in queries:
                    result = await session.execute(text(query), params)
                    results.append(result.fetchall())
                    
        return results
        
    async def close(self) -> None:
        """Close all connections"""
        if self.async_engine:
            await self.async_engine.dispose()


class QueryOptimizer:
    """Main query optimizer with eager loading and intelligent prefetching"""
    
    def __init__(
        self,
        database_url: str,
        pool_config: Optional[ConnectionPoolConfig] = None,
        cache_config: Optional[QueryCacheConfig] = None
    ):
        self.database_url = database_url
        self.pool_manager = ConnectionPoolManager(database_url, pool_config)
        self.query_cache = QueryCache(cache_config or QueryCacheConfig())
        self.plan_analyzer = None  # Initialized after setup
        self.query_stats: List[QueryStats] = []
        self.prefetch_patterns: Dict[str, List[str]] = {}  # Model -> related models to prefetch
        
    async def setup(self) -> None:
        """Initialize the query optimizer"""
        await self.pool_manager.setup()
        
        # Initialize plan analyzer with a connection
        async with self.pool_manager.get_connection() as conn:
            self.plan_analyzer = QueryPlanAnalyzer(conn)
            
    async def close(self) -> None:
        """Clean up resources"""
        await self.pool_manager.close()
        
    def configure_eager_loading(self, model: Type, relationships: List[str], strategy: LoadingStrategy = LoadingStrategy.EAGER_SELECT) -> None:
        """
        Configure eager loading for a model's relationships
        
        Args:
            model: SQLAlchemy model class
            relationships: List of relationship names to eager load
            strategy: Loading strategy to use
        """
        model_name = model.__name__
        self.prefetch_patterns[model_name] = relationships
        
    async def optimize_query(self, query: Query, analyze: bool = True) -> Query:
        """
        Optimize a SQLAlchemy query
        
        Args:
            query: SQLAlchemy query object
            analyze: Whether to analyze the execution plan
            
        Returns:
            Optimized query
        """
        # Get model from query
        if hasattr(query, 'column_descriptions'):
            model = query.column_descriptions[0]['entity']
            model_name = model.__name__ if model else None
            
            # Apply eager loading if configured
            if model_name and model_name in self.prefetch_patterns:
                for relationship in self.prefetch_patterns[model_name]:
                    if hasattr(model, relationship):
                        # Use selectinload for collections (most efficient for most cases)
                        query = query.options(selectinload(getattr(model, relationship)))
                        
        # Analyze query plan if requested
        if analyze and self.plan_analyzer:
            try:
                query_str = str(query.statement.compile(compile_kwargs={"literal_binds": True}))
                analysis = await self.plan_analyzer.analyze_query(query_str)
                
                # Log slow queries
                if analysis.get('execution_time', 0) > 100:  # > 100ms
                    print(f"Slow query detected: {analysis}")
                    
            except Exception as e:
                print(f"Query analysis failed: {e}")
                
        return query
        
    async def execute_with_cache(
        self,
        query: Union[str, Query],
        params: Optional[Dict] = None,
        ttl: Optional[int] = None,
        invalidate_on: Optional[Set[str]] = None
    ) -> Any:
        """
        Execute query with caching
        
        Args:
            query: SQL query string or SQLAlchemy query
            params: Query parameters
            ttl: Cache TTL override
            invalidate_on: Set of table names that invalidate this cache
            
        Returns:
            Query result
        """
        # Convert SQLAlchemy query to string if needed
        if not isinstance(query, str):
            query_str = str(query.statement.compile(compile_kwargs={"literal_binds": True}))
        else:
            query_str = query
            
        # Check cache
        cached_result = await self.query_cache.get(query_str, params)
        if cached_result is not None:
            return cached_result
            
        # Execute query
        start_time = time.time()
        
        async with self.pool_manager.get_connection() as session:
            result = await session.execute(text(query_str), params or {})
            data = result.fetchall()
            
        execution_time = time.time() - start_time
        
        # Record stats
        self.query_stats.append(QueryStats(
            query=query_str,
            execution_time=execution_time,
            rows_returned=len(data),
            cache_hit=False
        ))
        
        # Update metrics
        query_duration.labels(
            query_type=self._classify_query(query_str).value,
            table=self._extract_main_table(query_str)
        ).observe(execution_time)
        
        # Cache result
        await self.query_cache.set(query_str, data, params, invalidate_on)
        
        return data
        
    async def bulk_insert(self, model: Type, records: List[Dict], batch_size: int = 1000) -> None:
        """
        Optimized bulk insert with batching
        
        Args:
            model: SQLAlchemy model class
            records: List of records to insert
            batch_size: Number of records per batch
        """
        async with self.pool_manager.get_connection() as session:
            # Process in batches
            for i in range(0, len(records), batch_size):
                batch = records[i:i + batch_size]
                
                # Use PostgreSQL's INSERT ... ON CONFLICT for upsert
                stmt = insert(model).values(batch)
                
                # Execute batch insert
                await session.execute(stmt)
                
            await session.commit()
            
    async def bulk_update(self, model: Type, updates: List[Dict], batch_size: int = 500) -> None:
        """
        Optimized bulk update
        
        Args:
            model: SQLAlchemy model class
            updates: List of update dictionaries with 'id' and fields to update
            batch_size: Number of records per batch
        """
        async with self.pool_manager.get_connection() as session:
            # Process in batches
            for i in range(0, len(updates), batch_size):
                batch = updates[i:i + batch_size]
                
                # Bulk update using bulk_update_mappings
                await session.bulk_update_mappings(model, batch)
                
            await session.commit()
            
    def _classify_query(self, query: str) -> QueryType:
        """Classify query type for optimization"""
        query_lower = query.lower().strip()
        
        if 'join' in query_lower:
            return QueryType.JOIN
        elif 'group by' in query_lower or 'sum(' in query_lower or 'count(' in query_lower:
            return QueryType.AGGREGATION
        elif 'where' in query_lower and '=' in query_lower and 'id' in query_lower:
            return QueryType.POINT_LOOKUP
        elif 'where' in query_lower and ('>' in query_lower or '<' in query_lower or 'between' in query_lower):
            return QueryType.RANGE_SCAN
        else:
            return QueryType.FULL_SCAN
            
    def _extract_main_table(self, query: str) -> str:
        """Extract main table name from query"""
        query_lower = query.lower()
        
        # Simple extraction - real implementation would use SQL parser
        if 'from' in query_lower:
            parts = query_lower.split('from')[1].split()
            if parts:
                return parts[0].strip()
                
        return 'unknown'
        
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        if not self.query_stats:
            return {}
            
        execution_times = [stat.execution_time for stat in self.query_stats]
        
        return {
            'query_count': len(self.query_stats),
            'avg_execution_time': np.mean(execution_times),
            'p50_execution_time': np.percentile(execution_times, 50),
            'p95_execution_time': np.percentile(execution_times, 95),
            'p99_execution_time': np.percentile(execution_times, 99),
            'cache_stats': {
                'size': len(self.query_cache.cache),
                'hit_rate': self._calculate_cache_hit_rate()
            },
            'pool_stats': self.pool_manager.stats,
            'index_recommendations': dict(self.plan_analyzer.index_recommendations) if self.plan_analyzer else {}
        }
        
    def _calculate_cache_hit_rate(self) -> float:
        """Calculate cache hit rate"""
        hits = sum(1 for stat in self.query_stats if stat.cache_hit)
        total = len(self.query_stats)
        
        return hits / total if total > 0 else 0.0


# Decorator for optimized queries
def optimized_query(
    cache_ttl: Optional[int] = 300,
    eager_load: Optional[List[str]] = None,
    analyze: bool = True
):
    """
    Decorator for optimizing database queries
    
    Args:
        cache_ttl: Cache TTL in seconds
        eager_load: Relationships to eager load
        analyze: Whether to analyze query plan
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get optimizer from context (assumes it's injected)
            optimizer = kwargs.get('optimizer') or getattr(wrapper, '_optimizer', None)
            
            if not optimizer:
                # Fallback to executing without optimization
                return await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
                
            # Execute function to get query
            query = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
            
            # Optimize query if it's a SQLAlchemy Query object
            if hasattr(query, 'statement'):
                query = await optimizer.optimize_query(query, analyze=analyze)
                
                # Apply eager loading if specified
                if eager_load:
                    for relationship in eager_load:
                        query = query.options(selectinload(relationship))
                        
            # Execute with caching
            return await optimizer.execute_with_cache(query, ttl=cache_ttl)
            
        return wrapper
    return decorator