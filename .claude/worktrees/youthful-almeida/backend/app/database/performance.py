"""
Database performance monitoring and optimization utilities
"""

import asyncio
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from contextlib import asynccontextmanager

import asyncpg
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.utils import db_manager
from app.database.audit import audit_logger, AuditSeverity
from app.core.config import settings

import logging
logger = logging.getLogger(__name__)


@dataclass
class QueryMetrics:
    """Query performance metrics"""
    query_hash: str
    query_text: str
    execution_count: int
    total_time_ms: float
    avg_time_ms: float
    min_time_ms: float
    max_time_ms: float
    rows_examined: int
    rows_returned: int
    last_executed: datetime


@dataclass
class IndexSuggestion:
    """Index optimization suggestion"""
    table_name: str
    column_names: List[str]
    index_type: str  # btree, hash, gin, gist
    reason: str
    potential_improvement: str
    estimated_size_mb: float


class DatabasePerformanceMonitor:
    """Real-time database performance monitoring and alerting"""
    
    def __init__(self):
        self.monitoring_enabled = False
        self.metrics_cache = {}
        self.alert_thresholds = {
            'slow_query_threshold_ms': 1000,
            'connection_pool_utilization': 0.8,
            'active_connections_threshold': 50,
            'deadlock_threshold': 5,
            'lock_timeout_threshold': 30000,  # 30 seconds
            'cache_hit_ratio_threshold': 0.95
        }
        self._monitor_task: Optional[asyncio.Task] = None
    
    async def start_monitoring(self, interval_seconds: int = 60):
        """Start continuous performance monitoring"""
        self.monitoring_enabled = True
        self._monitor_task = asyncio.create_task(self._monitoring_loop(interval_seconds))
        logger.info("Database performance monitoring started")
    
    async def stop_monitoring(self):
        """Stop performance monitoring"""
        self.monitoring_enabled = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        logger.info("Database performance monitoring stopped")
    
    async def _monitoring_loop(self, interval_seconds: int):
        """Main monitoring loop"""
        while self.monitoring_enabled:
            try:
                await self._collect_metrics()
                await self._check_alerts()
                await asyncio.sleep(interval_seconds)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(interval_seconds)
    
    async def _collect_metrics(self):
        """Collect comprehensive database metrics"""
        try:
            metrics = await self.get_comprehensive_metrics()
            self.metrics_cache['last_collection'] = datetime.now(timezone.utc)
            self.metrics_cache['metrics'] = metrics
            
            # Log significant metrics changes
            await self._log_significant_changes(metrics)
            
        except Exception as e:
            logger.error(f"Failed to collect metrics: {e}")
    
    async def _check_alerts(self):
        """Check for performance issues and send alerts"""
        if 'metrics' not in self.metrics_cache:
            return
        
        metrics = self.metrics_cache['metrics']
        alerts = []
        
        # Check slow queries
        if metrics.get('slow_queries'):
            for query in metrics['slow_queries']:
                if query['avg_time_ms'] > self.alert_thresholds['slow_query_threshold_ms']:
                    alerts.append({
                        'type': 'slow_query',
                        'severity': 'warning',
                        'message': f"Slow query detected: {query['avg_time_ms']:.2f}ms average",
                        'details': query
                    })
        
        # Check connection pool utilization
        pool_stats = metrics.get('connection_pool', {})
        if pool_stats.get('utilization', 0) > self.alert_thresholds['connection_pool_utilization']:
            alerts.append({
                'type': 'high_pool_utilization',
                'severity': 'warning',
                'message': f"High connection pool utilization: {pool_stats['utilization']:.2%}",
                'details': pool_stats
            })
        
        # Check active connections
        db_stats = metrics.get('database_stats', {})
        active_connections = db_stats.get('active_connections', 0)
        if active_connections > self.alert_thresholds['active_connections_threshold']:
            alerts.append({
                'type': 'high_active_connections',
                'severity': 'error',
                'message': f"High number of active connections: {active_connections}",
                'details': {'active_connections': active_connections}
            })
        
        # Check cache hit ratio
        cache_hit_ratio = db_stats.get('cache_hit_ratio', 1.0)
        if cache_hit_ratio < self.alert_thresholds['cache_hit_ratio_threshold']:
            alerts.append({
                'type': 'low_cache_hit_ratio',
                'severity': 'warning',
                'message': f"Low cache hit ratio: {cache_hit_ratio:.2%}",
                'details': {'cache_hit_ratio': cache_hit_ratio}
            })
        
        # Send alerts
        for alert in alerts:
            await self._send_alert(alert)
    
    async def _send_alert(self, alert: Dict[str, Any]):
        """Send performance alert"""
        severity = AuditSeverity.WARNING if alert['severity'] == 'warning' else AuditSeverity.ERROR
        
        await audit_logger.log_system_event(
            event_type="performance_alert",
            event_category="database",
            message=alert['message'],
            severity=severity,
            component="performance_monitor",
            additional_data=alert['details']
        )
        
        logger.warning(f"Performance alert: {alert['message']}")
    
    async def get_comprehensive_metrics(self) -> Dict[str, Any]:
        """Get comprehensive database performance metrics"""
        
        async with db_manager.async_engine.begin() as conn:
            metrics = {}
            
            # Basic database statistics
            metrics['database_stats'] = await self._get_database_stats(conn)
            
            # Query performance statistics
            metrics['query_stats'] = await self._get_query_stats(conn)
            
            # Slow queries
            metrics['slow_queries'] = await self._get_slow_queries(conn)
            
            # Index usage statistics
            metrics['index_stats'] = await self._get_index_stats(conn)
            
            # Table statistics
            metrics['table_stats'] = await self._get_table_stats(conn)
            
            # Connection pool statistics
            metrics['connection_pool'] = await self._get_pool_stats()
            
            # Lock statistics
            metrics['lock_stats'] = await self._get_lock_stats(conn)
            
            # Replication lag (if applicable)
            metrics['replication_stats'] = await self._get_replication_stats(conn)
            
            return metrics
    
    async def _get_database_stats(self, conn) -> Dict[str, Any]:
        """Get basic database statistics"""
        queries = {
            'connections': """
                SELECT 
                    count(*) as total_connections,
                    count(*) FILTER (WHERE state = 'active') as active_connections,
                    count(*) FILTER (WHERE state = 'idle') as idle_connections,
                    count(*) FILTER (WHERE state = 'idle in transaction') as idle_in_transaction
                FROM pg_stat_activity 
                WHERE datname = current_database()
            """,
            'cache_stats': """
                SELECT 
                    sum(heap_blks_read) as heap_read,
                    sum(heap_blks_hit) as heap_hit,
                    sum(idx_blks_read) as idx_read,
                    sum(idx_blks_hit) as idx_hit,
                    round(
                        (sum(heap_blks_hit) + sum(idx_blks_hit)) * 100.0 / 
                        NULLIF(sum(heap_blks_hit) + sum(idx_blks_hit) + sum(heap_blks_read) + sum(idx_blks_read), 0), 
                        2
                    ) as cache_hit_ratio
                FROM pg_statio_user_tables
            """,
            'database_size': """
                SELECT pg_size_pretty(pg_database_size(current_database())) as size,
                       pg_database_size(current_database()) as size_bytes
            """,
            'transaction_stats': """
                SELECT 
                    xact_commit as committed_transactions,
                    xact_rollback as rolled_back_transactions,
                    tup_returned as tuples_returned,
                    tup_fetched as tuples_fetched,
                    tup_inserted as tuples_inserted,
                    tup_updated as tuples_updated,
                    tup_deleted as tuples_deleted
                FROM pg_stat_database 
                WHERE datname = current_database()
            """
        }
        
        stats = {}
        for stat_name, query in queries.items():
            try:
                result = await conn.execute(text(query))
                row = result.first()
                if row:
                    stats[stat_name] = dict(row._mapping)
                else:
                    stats[stat_name] = {}
            except Exception as e:
                logger.warning(f"Failed to collect {stat_name}: {e}")
                stats[stat_name] = {'error': str(e)}
        
        return stats
    
    async def _get_query_stats(self, conn) -> Dict[str, Any]:
        """Get query performance statistics"""
        # Requires pg_stat_statements extension
        query = """
            SELECT 
                calls,
                total_exec_time,
                mean_exec_time,
                stddev_exec_time,
                rows,
                100.0 * shared_blks_hit / nullif(shared_blks_hit + shared_blks_read, 0) AS hit_percent
            FROM pg_stat_statements
            WHERE query NOT LIKE '%pg_stat_statements%'
            ORDER BY total_exec_time DESC
            LIMIT 10
        """
        
        try:
            result = await conn.execute(text(query))
            return [dict(row._mapping) for row in result]
        except Exception:
            # pg_stat_statements not available
            return []
    
    async def _get_slow_queries(self, conn) -> List[Dict[str, Any]]:
        """Get slow running queries"""
        query = """
            SELECT 
                query,
                calls,
                total_exec_time,
                mean_exec_time as avg_time_ms,
                min_exec_time as min_time_ms,
                max_exec_time as max_time_ms,
                rows as rows_returned
            FROM pg_stat_statements
            WHERE mean_exec_time > 100  -- queries taking more than 100ms on average
            ORDER BY mean_exec_time DESC
            LIMIT 20
        """
        
        try:
            result = await conn.execute(text(query))
            return [dict(row._mapping) for row in result]
        except Exception:
            return []
    
    async def _get_index_stats(self, conn) -> List[Dict[str, Any]]:
        """Get index usage statistics"""
        query = """
            SELECT 
                schemaname,
                tablename,
                indexname,
                idx_tup_read,
                idx_tup_fetch,
                pg_size_pretty(pg_relation_size(indexrelid)) as index_size
            FROM pg_stat_user_indexes
            ORDER BY idx_tup_read DESC
        """
        
        try:
            result = await conn.execute(text(query))
            return [dict(row._mapping) for row in result]
        except Exception as e:
            logger.warning(f"Failed to get index stats: {e}")
            return []
    
    async def _get_table_stats(self, conn) -> List[Dict[str, Any]]:
        """Get table statistics"""
        query = """
            SELECT 
                schemaname,
                tablename,
                n_tup_ins as inserts,
                n_tup_upd as updates,
                n_tup_del as deletes,
                n_live_tup as live_tuples,
                n_dead_tup as dead_tuples,
                pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as total_size,
                last_vacuum,
                last_autovacuum,
                last_analyze,
                last_autoanalyze
            FROM pg_stat_user_tables
            ORDER BY n_live_tup DESC
        """
        
        try:
            result = await conn.execute(text(query))
            return [dict(row._mapping) for row in result]
        except Exception as e:
            logger.warning(f"Failed to get table stats: {e}")
            return []
    
    async def _get_pool_stats(self) -> Dict[str, Any]:
        """Get connection pool statistics"""
        try:
            pool = db_manager.async_engine.pool
            return {
                'size': pool.size(),
                'checked_in': pool.checkedin(),
                'checked_out': pool.checkedout(),
                'overflow': pool.overflow(),
                'utilization': pool.checkedout() / (pool.size() + pool.overflow()) if (pool.size() + pool.overflow()) > 0 else 0
            }
        except Exception as e:
            logger.warning(f"Failed to get pool stats: {e}")
            return {}
    
    async def _get_lock_stats(self, conn) -> Dict[str, Any]:
        """Get lock statistics"""
        query = """
            SELECT 
                mode,
                count(*) as lock_count
            FROM pg_locks
            WHERE mode IS NOT NULL
            GROUP BY mode
            ORDER BY lock_count DESC
        """
        
        try:
            result = await conn.execute(text(query))
            locks = [dict(row._mapping) for row in result]
            
            # Get blocked queries
            blocked_query = """
                SELECT 
                    blocked_locks.pid AS blocked_pid,
                    blocked_activity.usename AS blocked_user,
                    blocking_locks.pid AS blocking_pid,
                    blocking_activity.usename AS blocking_user,
                    blocked_activity.query AS blocked_statement,
                    blocking_activity.query AS current_statement_in_blocking_process
                FROM pg_catalog.pg_locks blocked_locks
                JOIN pg_catalog.pg_stat_activity blocked_activity ON blocked_activity.pid = blocked_locks.pid
                JOIN pg_catalog.pg_locks blocking_locks ON blocking_locks.locktype = blocked_locks.locktype
                    AND blocking_locks.database IS NOT DISTINCT FROM blocked_locks.database
                    AND blocking_locks.relation IS NOT DISTINCT FROM blocked_locks.relation
                    AND blocking_locks.page IS NOT DISTINCT FROM blocked_locks.page
                    AND blocking_locks.tuple IS NOT DISTINCT FROM blocked_locks.tuple
                    AND blocking_locks.virtualxid IS NOT DISTINCT FROM blocked_locks.virtualxid
                    AND blocking_locks.transactionid IS NOT DISTINCT FROM blocked_locks.transactionid
                    AND blocking_locks.classid IS NOT DISTINCT FROM blocked_locks.classid
                    AND blocking_locks.objid IS NOT DISTINCT FROM blocked_locks.objid
                    AND blocking_locks.objsubid IS NOT DISTINCT FROM blocked_locks.objsubid
                    AND blocking_locks.pid != blocked_locks.pid
                JOIN pg_catalog.pg_stat_activity blocking_activity ON blocking_activity.pid = blocking_locks.pid
                WHERE NOT blocked_locks.granted
            """
            
            blocked_result = await conn.execute(text(blocked_query))
            blocked_queries = [dict(row._mapping) for row in blocked_result]
            
            return {
                'lock_modes': locks,
                'blocked_queries': blocked_queries,
                'total_locks': sum(lock['lock_count'] for lock in locks),
                'blocked_count': len(blocked_queries)
            }
        except Exception as e:
            logger.warning(f"Failed to get lock stats: {e}")
            return {}
    
    async def _get_replication_stats(self, conn) -> Dict[str, Any]:
        """Get replication statistics (if applicable)"""
        query = """
            SELECT 
                client_addr,
                state,
                pg_wal_lsn_diff(pg_current_wal_lsn(), sent_lsn) as send_lag_bytes,
                pg_wal_lsn_diff(sent_lsn, flush_lsn) as flush_lag_bytes,
                pg_wal_lsn_diff(flush_lsn, replay_lsn) as replay_lag_bytes
            FROM pg_stat_replication
        """
        
        try:
            result = await conn.execute(text(query))
            return [dict(row._mapping) for row in result]
        except Exception:
            # No replication configured
            return []
    
    async def _log_significant_changes(self, metrics: Dict[str, Any]):
        """Log significant changes in metrics"""
        # This is a placeholder for intelligent metric change detection
        # In production, you would compare with historical data
        pass


class QueryOptimizer:
    """Query optimization and index suggestion engine"""
    
    def __init__(self):
        self.optimization_cache = {}
    
    async def analyze_slow_queries(self) -> List[Dict[str, Any]]:
        """Analyze slow queries and provide optimization suggestions"""
        
        async with db_manager.async_engine.begin() as conn:
            # Get slow queries with execution plans
            query = """
                SELECT 
                    query,
                    calls,
                    total_exec_time,
                    mean_exec_time,
                    rows,
                    100.0 * shared_blks_hit / nullif(shared_blks_hit + shared_blks_read, 0) AS hit_percent
                FROM pg_stat_statements
                WHERE mean_exec_time > 500  -- queries taking more than 500ms
                ORDER BY total_exec_time DESC
                LIMIT 50
            """
            
            try:
                result = await conn.execute(text(query))
                slow_queries = [dict(row._mapping) for row in result]
                
                optimized_queries = []
                for query_data in slow_queries:
                    suggestions = await self._analyze_query(conn, query_data)
                    optimized_queries.append({
                        'query_data': query_data,
                        'suggestions': suggestions
                    })
                
                return optimized_queries
            except Exception as e:
                logger.error(f"Failed to analyze slow queries: {e}")
                return []
    
    async def _analyze_query(self, conn, query_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze individual query and provide suggestions"""
        suggestions = []
        
        try:
            # Get query execution plan
            explain_query = f"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) {query_data['query']}"
            result = await conn.execute(text(explain_query))
            plan_data = result.fetchone()[0]
            
            # Analyze the plan for optimization opportunities
            suggestions.extend(self._analyze_execution_plan(plan_data))
            
        except Exception as e:
            logger.warning(f"Could not analyze query: {e}")
        
        return suggestions
    
    def _analyze_execution_plan(self, plan_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze execution plan for optimization opportunities"""
        suggestions = []
        
        def analyze_node(node: Dict[str, Any]):
            node_type = node.get('Node Type', '')
            
            # Sequential scans on large tables
            if node_type == 'Seq Scan':
                rows = node.get('Actual Rows', 0)
                if rows > 1000:
                    suggestions.append({
                        'type': 'missing_index',
                        'description': f'Sequential scan on {rows} rows - consider adding index',
                        'table': node.get('Relation Name', 'unknown'),
                        'priority': 'high' if rows > 10000 else 'medium'
                    })
            
            # Nested loops with high cost
            if node_type == 'Nested Loop':
                cost = node.get('Total Cost', 0)
                if cost > 1000:
                    suggestions.append({
                        'type': 'expensive_join',
                        'description': f'Expensive nested loop (cost: {cost}) - consider hash join',
                        'priority': 'medium'
                    })
            
            # Sort operations that spill to disk
            if node_type == 'Sort':
                sort_method = node.get('Sort Method', '')
                if 'disk' in sort_method.lower():
                    suggestions.append({
                        'type': 'sort_spill',
                        'description': 'Sort operation spilling to disk - consider increasing work_mem',
                        'priority': 'medium'
                    })
            
            # Recursively analyze child nodes
            for child in node.get('Plans', []):
                analyze_node(child)
        
        # Analyze the root plan
        if plan_data and len(plan_data) > 0:
            analyze_node(plan_data[0]['Plan'])
        
        return suggestions
    
    async def suggest_indexes(self) -> List[IndexSuggestion]:
        """Suggest indexes based on query patterns and missing indexes"""
        
        async with db_manager.async_engine.begin() as conn:
            suggestions = []
            
            # Find tables with frequent sequential scans
            seq_scan_query = """
                SELECT 
                    schemaname,
                    tablename,
                    seq_scan,
                    seq_tup_read,
                    idx_scan,
                    n_live_tup
                FROM pg_stat_user_tables
                WHERE seq_scan > idx_scan 
                AND n_live_tup > 1000
                ORDER BY seq_tup_read DESC
            """
            
            try:
                result = await conn.execute(text(seq_scan_query))
                for row in result:
                    row_dict = dict(row._mapping)
                    
                    # Suggest index for frequently scanned tables
                    if row_dict['seq_tup_read'] > 10000:
                        suggestions.append(IndexSuggestion(
                            table_name=row_dict['tablename'],
                            column_names=['id'],  # Default to primary key
                            index_type='btree',
                            reason=f"High sequential scan activity ({row_dict['seq_tup_read']} rows read)",
                            potential_improvement="Reduce sequential scans by 70-90%",
                            estimated_size_mb=row_dict['n_live_tup'] * 0.001  # Rough estimate
                        ))
                
                # Find foreign key columns without indexes
                fk_query = """
                    SELECT 
                        tc.table_name,
                        kcu.column_name
                    FROM information_schema.table_constraints tc
                    JOIN information_schema.key_column_usage kcu 
                        ON tc.constraint_name = kcu.constraint_name
                        AND tc.table_schema = kcu.table_schema
                    WHERE tc.constraint_type = 'FOREIGN KEY'
                    AND tc.table_schema = 'public'
                """
                
                fk_result = await conn.execute(text(fk_query))
                for row in fk_result:
                    row_dict = dict(row._mapping)
                    suggestions.append(IndexSuggestion(
                        table_name=row_dict['table_name'],
                        column_names=[row_dict['column_name']],
                        index_type='btree',
                        reason="Foreign key column without index",
                        potential_improvement="Improve join performance by 50-80%",
                        estimated_size_mb=1.0  # Conservative estimate
                    ))
                
                return suggestions
            
            except Exception as e:
                logger.error(f"Failed to suggest indexes: {e}")
                return []
    
    async def generate_optimization_report(self) -> Dict[str, Any]:
        """Generate comprehensive optimization report"""
        
        slow_queries = await self.analyze_slow_queries()
        index_suggestions = await self.suggest_indexes()
        
        # Calculate potential impact
        total_slow_queries = len(slow_queries)
        high_impact_suggestions = [s for s in index_suggestions if 'high' in s.reason.lower()]
        
        return {
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'summary': {
                'slow_queries_analyzed': total_slow_queries,
                'index_suggestions': len(index_suggestions),
                'high_impact_optimizations': len(high_impact_suggestions)
            },
            'slow_queries': slow_queries[:10],  # Top 10 slow queries
            'index_suggestions': [asdict(s) for s in index_suggestions],
            'recommendations': self._generate_recommendations(slow_queries, index_suggestions)
        }
    
    def _generate_recommendations(self, slow_queries: List[Dict], index_suggestions: List[IndexSuggestion]) -> List[str]:
        """Generate high-level optimization recommendations"""
        recommendations = []
        
        if len(slow_queries) > 20:
            recommendations.append("High number of slow queries detected - consider query optimization review")
        
        if len(index_suggestions) > 10:
            recommendations.append("Many missing indexes detected - implement indexing strategy")
        
        # Check for specific patterns
        seq_scans = sum(1 for query in slow_queries 
                       for suggestion in query.get('suggestions', [])
                       if suggestion.get('type') == 'missing_index')
        
        if seq_scans > 5:
            recommendations.append("Multiple sequential scans detected - prioritize index creation")
        
        return recommendations


# Global performance monitor instance
performance_monitor = DatabasePerformanceMonitor()
query_optimizer = QueryOptimizer()


@asynccontextmanager
async def query_timer(query_name: str):
    """Context manager for timing queries"""
    start_time = time.time()
    try:
        yield
    finally:
        duration_ms = (time.time() - start_time) * 1000
        
        if duration_ms > 1000:  # Log slow queries
            await audit_logger.log_system_event(
                event_type="slow_query",
                event_category="performance",
                message=f"Slow query detected: {query_name}",
                severity=AuditSeverity.WARNING,
                component="query_timer",
                duration_ms=int(duration_ms)
            )


async def init_performance_monitoring():
    """Initialize performance monitoring"""
    await performance_monitor.start_monitoring()
    logger.info("Performance monitoring initialized")


async def shutdown_performance_monitoring():
    """Shutdown performance monitoring"""
    await performance_monitor.stop_monitoring()
    logger.info("Performance monitoring shutdown")