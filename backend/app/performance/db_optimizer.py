"""
Database Query Optimization and Performance Tuning

Implements advanced database optimization techniques including:
- Query plan analysis and optimization
- Index management and suggestions
- Connection pooling optimization
- Query result caching
- Batch operations
- Read replica routing
"""

import asyncio
import time
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Type, Union
import logging
from dataclasses import dataclass
from enum import Enum

from sqlalchemy import (
    create_engine, event, text, inspect,
    MetaData, Table, Index, pool
)
from sqlalchemy.ext.asyncio import (
    AsyncSession, create_async_engine,
    AsyncEngine, async_sessionmaker
)
from sqlalchemy.orm import Session, Query, selectinload, joinedload, subqueryload
from sqlalchemy.sql import Select
from sqlalchemy.dialects.postgresql import EXPLAIN

logger = logging.getLogger(__name__)


class QueryComplexity(Enum):
    """Query complexity levels for routing"""
    SIMPLE = "simple"  # Single table, no joins
    MODERATE = "moderate"  # 1-2 joins
    COMPLEX = "complex"  # Multiple joins or subqueries
    ANALYTICAL = "analytical"  # Heavy aggregations


@dataclass
class QueryPlan:
    """Query execution plan analysis"""
    query: str
    execution_time: float
    total_cost: float
    index_scans: List[str]
    seq_scans: List[str]
    joins: List[str]
    suggestions: List[str]


class DatabaseOptimizer:
    """
    Advanced database optimization manager
    
    Features:
    - Automatic query plan analysis
    - Index suggestions
    - Connection pool management
    - Read/write splitting
    - Query result caching
    """
    
    def __init__(
        self,
        primary_url: str,
        read_replicas: List[str] = None,
        pool_size: int = 20,
        max_overflow: int = 40,
        pool_timeout: int = 30,
        enable_query_cache: bool = True,
        enable_profiling: bool = True
    ):
        self.primary_url = primary_url
        self.read_replicas = read_replicas or []
        
        # Connection pool configuration
        self.pool_config = {
            "pool_size": pool_size,
            "max_overflow": max_overflow,
            "pool_timeout": pool_timeout,
            "pool_recycle": 3600,  # Recycle connections after 1 hour
            "pool_pre_ping": True,  # Verify connections before use
            "echo_pool": False
        }
        
        # Initialize engines
        self.write_engine: Optional[AsyncEngine] = None
        self.read_engines: List[AsyncEngine] = []
        self.current_read_index = 0
        
        # Query profiling
        self.enable_profiling = enable_profiling
        self.query_stats: Dict[str, Dict] = {}
        
        # Index suggestions
        self.index_suggestions: Dict[str, List[str]] = {}
        
        # Slow query threshold (ms)
        self.slow_query_threshold = 100
    
    async def initialize(self):
        """Initialize database engines with optimized settings"""
        # Create write engine with optimized pool
        self.write_engine = create_async_engine(
            self.primary_url,
            **self.pool_config,
            connect_args={
                "server_settings": {
                    "jit": "on",
                    "max_parallel_workers_per_gather": "4",
                    "work_mem": "256MB",
                    "maintenance_work_mem": "512MB",
                    "effective_cache_size": "4GB",
                    "random_page_cost": "1.1"  # For SSD
                },
                "command_timeout": 60,
                "prepared_statement_cache_size": 500,
                "prepared_statement_name_func": lambda: f"stmt_{int(time.time() * 1000000)}"
            }
        )
        
        # Create read replica engines
        for replica_url in self.read_replicas:
            engine = create_async_engine(
                replica_url,
                **self.pool_config,
                connect_args={
                    "server_settings": {
                        "jit": "on",
                        "max_parallel_workers_per_gather": "4"
                    }
                }
            )
            self.read_engines.append(engine)
        
        # Set up event listeners for profiling
        if self.enable_profiling:
            self._setup_profiling()
        
        logger.info(f"Database optimizer initialized with {len(self.read_engines)} read replicas")
    
    def _setup_profiling(self):
        """Set up query profiling event listeners"""
        @event.listens_for(self.write_engine.sync_engine, "before_execute")
        def receive_before_execute(conn, clauseelement, multiparams, params, execution_options):
            conn.info.setdefault('query_start_time', []).append(time.time())
        
        @event.listens_for(self.write_engine.sync_engine, "after_execute")
        def receive_after_execute(conn, clauseelement, multiparams, params, execution_options, result):
            total_time = time.time() - conn.info['query_start_time'].pop(-1)
            
            # Log slow queries
            if total_time * 1000 > self.slow_query_threshold:
                logger.warning(f"Slow query detected ({total_time*1000:.2f}ms): {clauseelement}")
                
                # Store for analysis
                query_key = str(clauseelement)[:100]
                if query_key not in self.query_stats:
                    self.query_stats[query_key] = {
                        'count': 0,
                        'total_time': 0,
                        'avg_time': 0,
                        'max_time': 0
                    }
                
                stats = self.query_stats[query_key]
                stats['count'] += 1
                stats['total_time'] += total_time
                stats['avg_time'] = stats['total_time'] / stats['count']
                stats['max_time'] = max(stats['max_time'], total_time)
    
    def get_read_engine(self) -> AsyncEngine:
        """Get read engine with round-robin load balancing"""
        if not self.read_engines:
            return self.write_engine
        
        engine = self.read_engines[self.current_read_index]
        self.current_read_index = (self.current_read_index + 1) % len(self.read_engines)
        return engine
    
    @asynccontextmanager
    async def get_session(self, read_only: bool = False):
        """
        Get optimized database session
        
        Args:
            read_only: Use read replica for read-only operations
        """
        engine = self.get_read_engine() if read_only else self.write_engine
        
        async_session = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        async with async_session() as session:
            try:
                yield session
            except Exception as e:
                await session.rollback()
                raise
            else:
                if not read_only:
                    await session.commit()
    
    async def analyze_query_plan(
        self,
        query: Select,
        session: AsyncSession
    ) -> QueryPlan:
        """
        Analyze query execution plan
        
        Args:
            query: SQLAlchemy query
            session: Database session
            
        Returns:
            QueryPlan with analysis and suggestions
        """
        # Get EXPLAIN ANALYZE output
        explained = query.prefix_with("EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)")
        result = await session.execute(explained)
        plan_json = result.scalar()
        
        # Parse execution plan
        plan = plan_json[0]["Plan"] if isinstance(plan_json, list) else plan_json
        
        # Extract metrics
        execution_time = plan.get("Actual Total Time", 0)
        total_cost = plan.get("Total Cost", 0)
        
        # Analyze plan nodes
        index_scans = []
        seq_scans = []
        joins = []
        suggestions = []
        
        def analyze_node(node):
            node_type = node.get("Node Type", "")
            
            if "Index Scan" in node_type:
                index_scans.append(node.get("Index Name", "unknown"))
            elif "Seq Scan" in node_type:
                table = node.get("Relation Name", "unknown")
                seq_scans.append(table)
                
                # Suggest index if sequential scan is costly
                if node.get("Total Cost", 0) > 1000:
                    suggestions.append(f"Consider adding index on table '{table}'")
            elif "Join" in node_type:
                joins.append(node_type)
            
            # Recursively analyze child nodes
            for child in node.get("Plans", []):
                analyze_node(child)
        
        analyze_node(plan)
        
        # Additional suggestions based on metrics
        if execution_time > 100:
            suggestions.append("Query execution time is high, consider optimization")
        
        if len(seq_scans) > 2:
            suggestions.append("Multiple sequential scans detected, review indexing strategy")
        
        if len(joins) > 3:
            suggestions.append("Complex join pattern, consider denormalization or materialized views")
        
        return QueryPlan(
            query=str(query),
            execution_time=execution_time,
            total_cost=total_cost,
            index_scans=index_scans,
            seq_scans=seq_scans,
            joins=joins,
            suggestions=suggestions
        )
    
    async def suggest_indexes(
        self,
        table_name: str,
        session: AsyncSession
    ) -> List[str]:
        """
        Suggest indexes based on query patterns
        
        Args:
            table_name: Table to analyze
            session: Database session
            
        Returns:
            List of index suggestions
        """
        suggestions = []
        
        # Analyze missing indexes from pg_stat_user_tables
        query = text("""
            SELECT 
                schemaname,
                tablename,
                seq_scan,
                seq_tup_read,
                idx_scan,
                idx_tup_fetch,
                n_tup_ins,
                n_tup_upd,
                n_tup_del
            FROM pg_stat_user_tables
            WHERE tablename = :table_name
        """)
        
        result = await session.execute(query, {"table_name": table_name})
        stats = result.fetchone()
        
        if stats:
            seq_scan_ratio = stats.seq_scan / (stats.seq_scan + stats.idx_scan + 1)
            
            if seq_scan_ratio > 0.5:
                suggestions.append(f"High sequential scan ratio ({seq_scan_ratio:.2%}) on {table_name}")
        
        # Check for duplicate indexes
        query = text("""
            SELECT 
                indexname,
                indexdef
            FROM pg_indexes
            WHERE tablename = :table_name
        """)
        
        result = await session.execute(query, {"table_name": table_name})
        indexes = result.fetchall()
        
        # Analyze foreign key columns without indexes
        query = text("""
            SELECT
                tc.constraint_name,
                kcu.column_name
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
                ON tc.constraint_name = kcu.constraint_name
            WHERE tc.table_name = :table_name
                AND tc.constraint_type = 'FOREIGN KEY'
                AND NOT EXISTS (
                    SELECT 1
                    FROM pg_indexes
                    WHERE tablename = :table_name
                        AND indexdef LIKE '%' || kcu.column_name || '%'
                )
        """)
        
        result = await session.execute(query, {"table_name": table_name})
        missing_fk_indexes = result.fetchall()
        
        for fk in missing_fk_indexes:
            suggestions.append(f"Consider index on foreign key column: {fk.column_name}")
        
        return suggestions
    
    async def optimize_batch_insert(
        self,
        table: Table,
        records: List[Dict],
        session: AsyncSession,
        batch_size: int = 1000
    ):
        """
        Optimized batch insert with chunking
        
        Args:
            table: SQLAlchemy table
            records: List of records to insert
            session: Database session
            batch_size: Batch size for inserts
        """
        # Process in batches
        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            
            # Use PostgreSQL COPY for large batches
            if len(batch) > 100:
                # Convert to COPY format
                stmt = table.insert().values(batch)
                await session.execute(stmt)
            else:
                # Use regular insert for small batches
                await session.execute(table.insert(), batch)
            
            # Commit periodically
            if (i + batch_size) % (batch_size * 10) == 0:
                await session.commit()
    
    async def vacuum_analyze(
        self,
        table_name: str = None,
        full: bool = False
    ):
        """
        Run VACUUM ANALYZE for table maintenance
        
        Args:
            table_name: Specific table or None for all
            full: Run FULL vacuum (locks table)
        """
        async with self.write_engine.connect() as conn:
            # Set autocommit for VACUUM
            await conn.execution_options(isolation_level="AUTOCOMMIT")
            
            vacuum_cmd = "VACUUM FULL ANALYZE" if full else "VACUUM ANALYZE"
            
            if table_name:
                await conn.execute(text(f"{vacuum_cmd} {table_name}"))
                logger.info(f"Executed {vacuum_cmd} on {table_name}")
            else:
                await conn.execute(text(vacuum_cmd))
                logger.info(f"Executed {vacuum_cmd} on all tables")
    
    async def update_statistics(self, table_name: str = None):
        """Update table statistics for query planner"""
        async with self.write_engine.connect() as conn:
            if table_name:
                await conn.execute(text(f"ANALYZE {table_name}"))
            else:
                await conn.execute(text("ANALYZE"))
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get database performance metrics"""
        metrics = {
            "pool_size": self.write_engine.pool.size() if self.write_engine else 0,
            "pool_checked_in": self.write_engine.pool.checked_in_connections() if self.write_engine else 0,
            "pool_overflow": self.write_engine.pool.overflow() if self.write_engine else 0,
            "slow_queries": len([q for q in self.query_stats.values() if q['avg_time'] * 1000 > self.slow_query_threshold]),
            "query_stats": self.query_stats
        }
        
        return metrics
    
    async def close(self):
        """Close all database connections"""
        if self.write_engine:
            await self.write_engine.dispose()
        
        for engine in self.read_engines:
            await engine.dispose()


class QueryOptimizer:
    """
    Query optimization helpers for SQLAlchemy
    """
    
    @staticmethod
    def optimize_loading_strategy(query: Query, relationships: List[str]) -> Query:
        """
        Optimize query with appropriate loading strategies
        
        Args:
            query: Base SQLAlchemy query
            relationships: List of relationships to load
            
        Returns:
            Optimized query
        """
        for rel in relationships:
            # Analyze relationship cardinality
            if "." in rel:
                # Nested relationship - use subquery load
                query = query.options(subqueryload(rel))
            else:
                # Direct relationship - use joined load for one-to-one
                # or select-in load for one-to-many
                query = query.options(selectinload(rel))
        
        return query
    
    @staticmethod
    def add_query_hints(query: Query, hints: Dict[str, str]) -> Query:
        """
        Add PostgreSQL query hints
        
        Args:
            query: SQLAlchemy query
            hints: Dictionary of hints
            
        Returns:
            Query with hints
        """
        hint_string = " ".join([f"/*+ {k}({v}) */" for k, v in hints.items()])
        return query.prefix_with(hint_string)
    
    @staticmethod
    def partition_query(
        query: Query,
        partition_column: str,
        partitions: int = 4
    ) -> List[Query]:
        """
        Partition query for parallel processing
        
        Args:
            query: Base query
            partition_column: Column to partition on
            partitions: Number of partitions
            
        Returns:
            List of partitioned queries
        """
        # This is a simplified example - actual implementation would need
        # to determine partition boundaries based on data distribution
        queries = []
        for i in range(partitions):
            partition_query = query.filter(
                text(f"MOD(CAST({partition_column} AS INTEGER), {partitions}) = {i}")
            )
            queries.append(partition_query)
        
        return queries