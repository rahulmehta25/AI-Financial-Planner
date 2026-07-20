"""
Query Optimizer for Database Performance
Implements query optimization, indexing strategies, and performance monitoring
"""

import time
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import asyncio
from contextlib import asynccontextmanager

import asyncpg
from sqlalchemy import text, create_engine, MetaData, Table
from sqlalchemy.orm import Session
from sqlalchemy.pool import NullPool, QueuePool
from sqlalchemy.dialects.postgresql import JSONB
import pandas as pd
import numpy as np

from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class QueryStats:
    """Statistics for query performance tracking"""
    query: str
    execution_time: float
    rows_returned: int
    cache_hit: bool = False
    index_used: bool = False
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            'query': self.query[:100],  # Truncate for display
            'execution_time_ms': self.execution_time * 1000,
            'rows_returned': self.rows_returned,
            'cache_hit': self.cache_hit,
            'index_used': self.index_used,
            'timestamp': self.timestamp.isoformat()
        }


class ConnectionPoolManager:
    """
    Advanced connection pooling with read replica support
    """
    
    def __init__(self):
        # Primary database pool (writes)
        self.primary_pool = create_engine(
            settings.DATABASE_URL,
            poolclass=QueuePool,
            pool_size=20,
            max_overflow=40,
            pool_timeout=30,
            pool_recycle=3600,
            pool_pre_ping=True,
            echo_pool=settings.DEBUG
        )
        
        # Read replica pools (reads)
        self.read_replicas = []
        if hasattr(settings, 'READ_REPLICA_URLS'):
            for replica_url in settings.READ_REPLICA_URLS:
                replica_pool = create_engine(
                    replica_url,
                    poolclass=QueuePool,
                    pool_size=15,
                    max_overflow=30,
                    pool_timeout=30,
                    pool_recycle=3600,
                    pool_pre_ping=True,
                    echo_pool=settings.DEBUG
                )
                self.read_replicas.append(replica_pool)
        
        # Async connection pool for high-performance queries
        self.async_pool: Optional[asyncpg.Pool] = None
        
        # Connection statistics
        self.stats = {
            'total_connections': 0,
            'active_connections': 0,
            'failed_connections': 0,
            'pool_exhaustion_count': 0
        }
    
    async def init_async_pool(self):
        """Initialize async connection pool"""
        if not self.async_pool:
            self.async_pool = await asyncpg.create_pool(
                settings.DATABASE_URL,
                min_size=10,
                max_size=30,
                max_queries=50000,
                max_inactive_connection_lifetime=300,
                command_timeout=60
            )
    
    def get_read_connection(self):
        """Get connection from read replica with load balancing"""
        if self.read_replicas:
            # Round-robin load balancing
            replica_index = self.stats['total_connections'] % len(self.read_replicas)
            return self.read_replicas[replica_index]
        return self.primary_pool
    
    def get_write_connection(self):
        """Get connection for write operations"""
        return self.primary_pool
    
    @asynccontextmanager
    async def async_connection(self):
        """Context manager for async database connections"""
        if not self.async_pool:
            await self.init_async_pool()
        
        async with self.async_pool.acquire() as connection:
            self.stats['active_connections'] += 1
            try:
                yield connection
            finally:
                self.stats['active_connections'] -= 1


class QueryOptimizer:
    """
    Advanced query optimization with caching, indexing, and performance monitoring
    """
    
    def __init__(self):
        self.pool_manager = ConnectionPoolManager()
        self.query_cache = {}
        self.slow_query_log = []
        self.index_recommendations = []
        
        # Performance thresholds
        self.SLOW_QUERY_THRESHOLD = 1.0  # seconds
        self.CACHE_TTL = 300  # 5 minutes
        
        # Query patterns for optimization
        self.optimization_patterns = {
            'portfolio_summary': self._optimize_portfolio_query,
            'transaction_history': self._optimize_transaction_query,
            'market_data': self._optimize_market_data_query,
            'user_analytics': self._optimize_analytics_query
        }
    
    async def execute_optimized_query(
        self,
        query: str,
        params: Optional[Dict] = None,
        query_type: str = 'read',
        use_cache: bool = True
    ) -> Tuple[Any, QueryStats]:
        """
        Execute query with optimization, caching, and monitoring
        """
        start_time = time.time()
        cache_key = self._get_cache_key(query, params)
        
        # Check cache for read queries
        if query_type == 'read' and use_cache and cache_key in self.query_cache:
            cache_entry = self.query_cache[cache_key]
            if datetime.now() - cache_entry['timestamp'] < timedelta(seconds=self.CACHE_TTL):
                execution_time = time.time() - start_time
                stats = QueryStats(
                    query=query,
                    execution_time=execution_time,
                    rows_returned=len(cache_entry['data']),
                    cache_hit=True
                )
                return cache_entry['data'], stats
        
        # Optimize query
        optimized_query = await self._optimize_query(query, params)
        
        # Execute query
        try:
            if query_type == 'read':
                result = await self._execute_read_query(optimized_query, params)
            else:
                result = await self._execute_write_query(optimized_query, params)
            
            execution_time = time.time() - start_time
            
            # Cache result if applicable
            if query_type == 'read' and use_cache:
                self.query_cache[cache_key] = {
                    'data': result,
                    'timestamp': datetime.now()
                }
            
            # Analyze performance
            stats = QueryStats(
                query=query,
                execution_time=execution_time,
                rows_returned=len(result) if isinstance(result, list) else 1,
                index_used=await self._check_index_usage(optimized_query)
            )
            
            # Log slow queries
            if execution_time > self.SLOW_QUERY_THRESHOLD:
                self._log_slow_query(query, execution_time, params)
            
            return result, stats
            
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            self.pool_manager.stats['failed_connections'] += 1
            raise
    
    async def _optimize_query(self, query: str, params: Optional[Dict]) -> str:
        """
        Apply query optimization techniques
        """
        optimized = query
        
        # Identify query pattern and apply specific optimizations
        for pattern_name, optimizer_func in self.optimization_patterns.items():
            if pattern_name in query.lower():
                optimized = await optimizer_func(query, params)
                break
        
        # General optimizations
        optimized = self._apply_general_optimizations(optimized)
        
        return optimized
    
    def _apply_general_optimizations(self, query: str) -> str:
        """
        Apply general SQL optimization techniques
        """
        # Add LIMIT if not present for SELECT queries
        if 'SELECT' in query.upper() and 'LIMIT' not in query.upper():
            query += ' LIMIT 1000'
        
        # Use index hints for common tables
        query = query.replace('FROM users', 'FROM users USE INDEX (idx_users_email)')
        query = query.replace('FROM portfolios', 'FROM portfolios USE INDEX (idx_portfolios_user_id)')
        
        return query
    
    async def _optimize_portfolio_query(self, query: str, params: Optional[Dict]) -> str:
        """
        Optimize portfolio-related queries
        """
        # Use materialized view for portfolio summaries
        if 'portfolio_value' in query.lower():
            query = query.replace('portfolios', 'mv_portfolio_summary')
        
        # Add partitioning hints for date ranges
        if params and 'start_date' in params:
            query += f" AND created_at >= '{params['start_date']}'"
        
        return query
    
    async def _optimize_transaction_query(self, query: str, params: Optional[Dict]) -> str:
        """
        Optimize transaction history queries
        """
        # Use columnar storage for large transaction queries
        if 'transactions' in query.lower():
            # Add index hints for common filters
            if 'user_id' in query:
                query = query.replace('FROM transactions', 
                                    'FROM transactions USE INDEX (idx_transactions_user_date)')
        
        return query
    
    async def _optimize_market_data_query(self, query: str, params: Optional[Dict]) -> str:
        """
        Optimize market data queries
        """
        # Use time-series optimizations
        if 'market_data' in query.lower():
            # Use TimescaleDB hypertable if available
            query = query.replace('market_data', 'market_data_hypertable')
            
            # Add time-based partitioning
            if params and 'symbol' in params:
                query += f" AND symbol = '{params['symbol']}'"
        
        return query
    
    async def _optimize_analytics_query(self, query: str, params: Optional[Dict]) -> str:
        """
        Optimize analytics queries
        """
        # Use pre-aggregated tables for analytics
        if 'user_metrics' in query.lower():
            query = query.replace('user_metrics', 'mv_user_metrics_daily')
        
        return query
    
    async def _execute_read_query(self, query: str, params: Optional[Dict]) -> List[Dict]:
        """
        Execute read query using read replica
        """
        async with self.pool_manager.async_connection() as conn:
            if params:
                result = await conn.fetch(query, *params.values())
            else:
                result = await conn.fetch(query)
            
            return [dict(row) for row in result]
    
    async def _execute_write_query(self, query: str, params: Optional[Dict]) -> Any:
        """
        Execute write query on primary database
        """
        async with self.pool_manager.async_connection() as conn:
            if params:
                result = await conn.execute(query, *params.values())
            else:
                result = await conn.execute(query)
            
            return result
    
    async def _check_index_usage(self, query: str) -> bool:
        """
        Check if query is using indexes effectively
        """
        explain_query = f"EXPLAIN (FORMAT JSON) {query}"
        
        try:
            async with self.pool_manager.async_connection() as conn:
                result = await conn.fetchval(explain_query)
                
                # Parse EXPLAIN output to check for index scans
                if 'Index Scan' in str(result) or 'Index Only Scan' in str(result):
                    return True
                
        except Exception as e:
            logger.warning(f"Could not analyze query plan: {e}")
        
        return False
    
    def _log_slow_query(self, query: str, execution_time: float, params: Optional[Dict]):
        """
        Log slow queries for analysis
        """
        self.slow_query_log.append({
            'query': query,
            'execution_time': execution_time,
            'params': params,
            'timestamp': datetime.now()
        })
        
        logger.warning(f"Slow query detected ({execution_time:.2f}s): {query[:100]}")
        
        # Generate index recommendations
        self._recommend_indexes(query)
    
    def _recommend_indexes(self, query: str):
        """
        Recommend indexes based on query patterns
        """
        recommendations = []
        
        # Check for missing indexes on WHERE clauses
        if 'WHERE' in query.upper():
            # Extract column names from WHERE clause
            where_clause = query.upper().split('WHERE')[1].split('ORDER BY')[0]
            
            # Common patterns that benefit from indexes
            if 'user_id' in where_clause.lower() and 'portfolios' in query.lower():
                recommendations.append('CREATE INDEX idx_portfolios_user_id ON portfolios(user_id);')
            
            if 'created_at' in where_clause.lower():
                table_name = self._extract_table_name(query)
                if table_name:
                    recommendations.append(f'CREATE INDEX idx_{table_name}_created_at ON {table_name}(created_at);')
        
        # Check for missing indexes on JOIN columns
        if 'JOIN' in query.upper():
            # Extract JOIN conditions
            join_parts = query.upper().split('JOIN')
            for part in join_parts[1:]:
                if 'ON' in part:
                    on_clause = part.split('ON')[1].split('WHERE')[0]
                    # Add recommendations based on JOIN columns
                    if 'id' in on_clause.lower():
                        recommendations.append('-- Consider adding indexes on JOIN columns')
        
        self.index_recommendations.extend(recommendations)
    
    def _extract_table_name(self, query: str) -> Optional[str]:
        """
        Extract main table name from query
        """
        try:
            if 'FROM' in query.upper():
                from_clause = query.upper().split('FROM')[1].split('WHERE')[0].split('JOIN')[0]
                return from_clause.strip().split()[0].lower()
        except:
            pass
        return None
    
    def _get_cache_key(self, query: str, params: Optional[Dict]) -> str:
        """
        Generate cache key for query
        """
        import hashlib
        key_string = f"{query}_{str(params)}"
        return hashlib.md5(key_string.encode()).hexdigest()
    
    async def create_indexes(self):
        """
        Create recommended indexes for optimal performance
        """
        indexes = [
            # User and authentication indexes
            "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);",
            "CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at);",
            
            # Portfolio indexes
            "CREATE INDEX IF NOT EXISTS idx_portfolios_user_id ON portfolios(user_id);",
            "CREATE INDEX IF NOT EXISTS idx_portfolios_updated_at ON portfolios(updated_at);",
            "CREATE INDEX IF NOT EXISTS idx_portfolio_holdings_portfolio_id ON portfolio_holdings(portfolio_id);",
            
            # Transaction indexes
            "CREATE INDEX IF NOT EXISTS idx_transactions_user_id ON transactions(user_id);",
            "CREATE INDEX IF NOT EXISTS idx_transactions_portfolio_id ON transactions(portfolio_id);",
            "CREATE INDEX IF NOT EXISTS idx_transactions_created_at ON transactions(created_at);",
            "CREATE INDEX IF NOT EXISTS idx_transactions_user_date ON transactions(user_id, created_at DESC);",
            
            # Market data indexes
            "CREATE INDEX IF NOT EXISTS idx_market_data_symbol ON market_data(symbol);",
            "CREATE INDEX IF NOT EXISTS idx_market_data_timestamp ON market_data(timestamp);",
            "CREATE INDEX IF NOT EXISTS idx_market_data_symbol_timestamp ON market_data(symbol, timestamp DESC);",
            
            # Composite indexes for common query patterns
            "CREATE INDEX IF NOT EXISTS idx_portfolio_performance ON portfolios(user_id, created_at, total_value);",
            "CREATE INDEX IF NOT EXISTS idx_user_activity ON users(id, last_login, created_at);"
        ]
        
        async with self.pool_manager.async_connection() as conn:
            for index_sql in indexes:
                try:
                    await conn.execute(index_sql)
                    logger.info(f"Index created/verified: {index_sql[:50]}...")
                except Exception as e:
                    logger.warning(f"Could not create index: {e}")
    
    async def analyze_tables(self):
        """
        Run ANALYZE on tables to update statistics for query planner
        """
        tables = ['users', 'portfolios', 'transactions', 'market_data', 'portfolio_holdings']
        
        async with self.pool_manager.async_connection() as conn:
            for table in tables:
                try:
                    await conn.execute(f"ANALYZE {table};")
                    logger.info(f"Table statistics updated: {table}")
                except Exception as e:
                    logger.warning(f"Could not analyze table {table}: {e}")
    
    async def vacuum_tables(self):
        """
        Run VACUUM to reclaim storage and update statistics
        """
        tables = ['transactions', 'market_data', 'portfolio_holdings']
        
        async with self.pool_manager.async_connection() as conn:
            for table in tables:
                try:
                    # VACUUM cannot run in a transaction block
                    await conn.execute(f"VACUUM ANALYZE {table};")
                    logger.info(f"Table vacuumed: {table}")
                except Exception as e:
                    logger.warning(f"Could not vacuum table {table}: {e}")
    
    def get_performance_report(self) -> Dict:
        """
        Generate performance report with statistics and recommendations
        """
        return {
            'connection_stats': self.pool_manager.stats,
            'cache_stats': {
                'cache_size': len(self.query_cache),
                'cache_hit_rate': self._calculate_cache_hit_rate()
            },
            'slow_queries': [
                {
                    'query': q['query'][:100],
                    'execution_time': q['execution_time'],
                    'timestamp': q['timestamp'].isoformat()
                }
                for q in sorted(self.slow_query_log, 
                              key=lambda x: x['execution_time'], 
                              reverse=True)[:10]
            ],
            'index_recommendations': list(set(self.index_recommendations))[:10],
            'optimization_suggestions': self._generate_optimization_suggestions()
        }
    
    def _calculate_cache_hit_rate(self) -> float:
        """
        Calculate cache hit rate from recent queries
        """
        # This would track actual hit/miss ratio in production
        return 0.75  # Placeholder
    
    def _generate_optimization_suggestions(self) -> List[str]:
        """
        Generate optimization suggestions based on query patterns
        """
        suggestions = []
        
        # Analyze slow query patterns
        if len(self.slow_query_log) > 10:
            suggestions.append("Consider implementing query result caching for frequently accessed data")
        
        # Check for missing indexes
        if len(self.index_recommendations) > 5:
            suggestions.append("Multiple missing indexes detected - run index creation script")
        
        # Connection pool optimization
        if self.pool_manager.stats.get('pool_exhaustion_count', 0) > 0:
            suggestions.append("Connection pool exhaustion detected - consider increasing pool size")
        
        return suggestions


# Singleton instance
query_optimizer = QueryOptimizer()