"""
Database Performance Optimization for Financial Planning System

This module provides comprehensive database performance monitoring, analysis,
and optimization specifically tailored for financial data workloads including:
- Query performance analysis
- Index optimization recommendations
- Connection pool tuning
- Cache configuration
- Partition management for time-series data
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from statistics import mean, median
import json

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.pool import QueuePool

from app.core.infrastructure.database import db_manager, timescale_manager
from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass 
class QueryPerformanceMetric:
    """Performance metrics for a database query"""
    query_id: str
    query: str
    execution_count: int
    avg_execution_time: float
    total_execution_time: float
    avg_rows: float
    table_scans: int
    index_scans: int
    buffer_hits: int
    buffer_misses: int


@dataclass
class IndexRecommendation:
    """Recommendation for database index creation or modification"""
    table_name: str
    recommended_columns: List[str]
    index_type: str  # btree, gin, gist, hash
    reason: str
    estimated_benefit: str
    create_statement: str
    priority: int  # 1-5, where 1 is highest priority


@dataclass
class PerformanceOptimizationResult:
    """Results from performance optimization analysis"""
    slow_queries: List[QueryPerformanceMetric]
    missing_indexes: List[IndexRecommendation]
    table_stats: Dict[str, Any]
    connection_pool_stats: Dict[str, Any]
    cache_hit_ratios: Dict[str, float]
    recommendations: List[str]
    optimization_score: float  # 0-100


class DatabasePerformanceOptimizer:
    """
    Comprehensive database performance optimizer for financial planning system
    """
    
    def __init__(self):
        self.performance_thresholds = {
            "slow_query_threshold_ms": 1000,  # Queries slower than 1 second
            "low_cache_hit_ratio": 0.95,  # Cache hit ratio below 95%
            "high_sequential_scan_ratio": 0.1,  # More than 10% sequential scans
            "connection_pool_utilization_high": 0.8,  # 80% pool utilization
        }
    
    async def analyze_performance(self, session: AsyncSession) -> PerformanceOptimizationResult:
        """
        Comprehensive performance analysis of the database
        """
        logger.info("Starting comprehensive database performance analysis")
        
        result = PerformanceOptimizationResult(
            slow_queries=[],
            missing_indexes=[],
            table_stats={},
            connection_pool_stats={},
            cache_hit_ratios={},
            recommendations=[],
            optimization_score=0.0
        )
        
        try:
            # Analyze slow queries
            result.slow_queries = await self._analyze_slow_queries(session)
            
            # Get missing index recommendations
            result.missing_indexes = await self._get_index_recommendations(session)
            
            # Collect table statistics
            result.table_stats = await self._collect_table_statistics(session)
            
            # Get connection pool stats
            result.connection_pool_stats = await self._get_connection_pool_stats()
            
            # Calculate cache hit ratios
            result.cache_hit_ratios = await self._calculate_cache_hit_ratios(session)
            
            # Generate recommendations
            result.recommendations = await self._generate_recommendations(result)
            
            # Calculate optimization score
            result.optimization_score = self._calculate_optimization_score(result)
            
            logger.info(f"Performance analysis completed. Optimization score: {result.optimization_score:.1f}")
            
        except Exception as e:
            logger.error(f"Performance analysis failed: {e}")
            result.recommendations.append(f"Performance analysis error: {e}")
        
        return result
    
    async def _analyze_slow_queries(self, session: AsyncSession) -> List[QueryPerformanceMetric]:
        """
        Analyze slow queries using pg_stat_statements
        """
        slow_queries = []
        
        try:
            # Enable pg_stat_statements if not already enabled
            await session.execute(text("CREATE EXTENSION IF NOT EXISTS pg_stat_statements;"))
            
            # Query for slow queries
            slow_query_sql = """
                SELECT 
                    queryid,
                    query,
                    calls as execution_count,
                    mean_exec_time as avg_execution_time,
                    total_exec_time as total_execution_time,
                    rows as avg_rows,
                    shared_blks_hit as buffer_hits,
                    shared_blks_read as buffer_misses
                FROM pg_stat_statements 
                WHERE mean_exec_time > :threshold
                ORDER BY mean_exec_time DESC
                LIMIT 20;
            """
            
            result = await session.execute(
                text(slow_query_sql), 
                {"threshold": self.performance_thresholds["slow_query_threshold_ms"]}
            )
            
            for row in result:
                metric = QueryPerformanceMetric(
                    query_id=str(row.queryid),
                    query=row.query[:200] + "..." if len(row.query) > 200 else row.query,
                    execution_count=row.execution_count,
                    avg_execution_time=row.avg_execution_time,
                    total_execution_time=row.total_execution_time,
                    avg_rows=row.avg_rows,
                    table_scans=0,  # Will be calculated separately
                    index_scans=0,  # Will be calculated separately
                    buffer_hits=row.buffer_hits,
                    buffer_misses=row.buffer_misses
                )
                slow_queries.append(metric)
                
        except Exception as e:
            logger.warning(f"Failed to analyze slow queries: {e}")
        
        return slow_queries
    
    async def _get_index_recommendations(self, session: AsyncSession) -> List[IndexRecommendation]:
        """
        Generate index recommendations based on query patterns and table statistics
        """
        recommendations = []
        
        # Financial planning specific index recommendations
        financial_indexes = [
            # High-priority indexes for financial data
            {
                "table": "enhanced_transactions",
                "columns": ["account_id", "trade_date", "symbol"],
                "type": "btree",
                "reason": "Optimize portfolio analysis queries that filter by account, date range, and symbol",
                "priority": 1
            },
            {
                "table": "enhanced_transactions", 
                "columns": ["tax_year", "tax_category", "realized_gain_loss"],
                "type": "btree",
                "reason": "Optimize tax reporting queries for gains/losses by year and category",
                "priority": 1
            },
            {
                "table": "enhanced_market_data",
                "columns": ["symbol", "time", "close"],
                "type": "btree", 
                "reason": "Optimize time-series price lookups with included close price",
                "priority": 2
            },
            {
                "table": "enhanced_portfolios",
                "columns": ["user_id", "status"],
                "type": "btree",
                "reason": "Optimize user portfolio queries filtering by active status",
                "priority": 2
            },
            {
                "table": "enhanced_accounts",
                "columns": ["portfolio_id", "account_type", "current_balance"],
                "type": "btree",
                "reason": "Optimize account balance queries grouped by type",
                "priority": 2
            },
            {
                "table": "user_activity_log",
                "columns": ["user_id", "timestamp"],
                "type": "btree",
                "reason": "Optimize audit trail queries for user activity over time",
                "priority": 3
            },
            # JSONB indexes for flexible queries
            {
                "table": "enhanced_portfolios",
                "columns": ["cached_metrics"],
                "type": "gin",
                "reason": "Enable fast queries on portfolio metrics stored in JSONB",
                "priority": 3
            },
            {
                "table": "enhanced_users",
                "columns": ["profile"],
                "type": "gin", 
                "reason": "Enable flexible queries on user profile data",
                "priority": 4
            }
        ]
        
        try:
            for idx in financial_indexes:
                # Check if index already exists
                existing_index_query = """
                    SELECT indexname 
                    FROM pg_indexes 
                    WHERE tablename = :table_name 
                    AND indexdef LIKE :column_pattern
                """
                
                column_pattern = f"%{idx['columns'][0]}%"
                result = await session.execute(
                    text(existing_index_query),
                    {"table_name": idx["table"], "column_pattern": column_pattern}
                )
                
                if not result.fetchone():
                    # Create index recommendation
                    columns_str = ", ".join(idx["columns"])
                    index_name = f"idx_{idx['table']}_{'_'.join([c.replace('(', '').replace(')', '') for c in idx['columns'][:3]])}"
                    
                    if idx["type"] == "gin":
                        create_statement = f"CREATE INDEX CONCURRENTLY {index_name} ON {idx['table']} USING gin ({columns_str});"
                    else:
                        create_statement = f"CREATE INDEX CONCURRENTLY {index_name} ON {idx['table']} ({columns_str});"
                    
                    recommendation = IndexRecommendation(
                        table_name=idx["table"],
                        recommended_columns=idx["columns"],
                        index_type=idx["type"],
                        reason=idx["reason"],
                        estimated_benefit="Medium to High",
                        create_statement=create_statement,
                        priority=idx["priority"]
                    )
                    recommendations.append(recommendation)
                    
        except Exception as e:
            logger.warning(f"Failed to generate index recommendations: {e}")
        
        return sorted(recommendations, key=lambda x: x.priority)
    
    async def _collect_table_statistics(self, session: AsyncSession) -> Dict[str, Any]:
        """
        Collect comprehensive table statistics
        """
        stats = {}
        
        try:
            # Get table sizes and row counts
            table_stats_query = """
                SELECT 
                    schemaname,
                    tablename,
                    n_tup_ins as inserts,
                    n_tup_upd as updates,
                    n_tup_del as deletes,
                    n_live_tup as live_rows,
                    n_dead_tup as dead_rows,
                    last_vacuum,
                    last_autovacuum,
                    last_analyze,
                    last_autoanalyze
                FROM pg_stat_user_tables
                WHERE schemaname = 'public'
                ORDER BY n_live_tup DESC;
            """
            
            result = await session.execute(text(table_stats_query))
            
            for row in result:
                table_name = row.tablename
                stats[table_name] = {
                    "live_rows": row.live_rows,
                    "dead_rows": row.dead_rows,
                    "inserts": row.inserts,
                    "updates": row.updates,
                    "deletes": row.deletes,
                    "last_vacuum": row.last_vacuum,
                    "last_analyze": row.last_analyze,
                    "dead_row_ratio": row.dead_rows / max(row.live_rows, 1) if row.dead_rows else 0
                }
            
            # Get table sizes
            size_query = """
                SELECT 
                    tablename,
                    pg_size_pretty(pg_total_relation_size(tablename::regclass)) as total_size,
                    pg_total_relation_size(tablename::regclass) as total_size_bytes,
                    pg_size_pretty(pg_relation_size(tablename::regclass)) as table_size,
                    pg_relation_size(tablename::regclass) as table_size_bytes
                FROM pg_tables 
                WHERE schemaname = 'public'
                ORDER BY pg_total_relation_size(tablename::regclass) DESC;
            """
            
            size_result = await session.execute(text(size_query))
            
            for row in size_result:
                if row.tablename in stats:
                    stats[row.tablename].update({
                        "total_size": row.total_size,
                        "total_size_bytes": row.total_size_bytes,
                        "table_size": row.table_size,
                        "table_size_bytes": row.table_size_bytes
                    })
                    
        except Exception as e:
            logger.warning(f"Failed to collect table statistics: {e}")
        
        return stats
    
    async def _get_connection_pool_stats(self) -> Dict[str, Any]:
        """
        Get connection pool statistics
        """
        stats = {
            "pool_size": 0,
            "checked_in": 0,
            "checked_out": 0,
            "overflow": 0,
            "utilization_percent": 0
        }
        
        try:
            # Get stats from database manager
            if hasattr(db_manager._async_engine, 'pool'):
                pool = db_manager._async_engine.pool
                if isinstance(pool, QueuePool):
                    stats.update({
                        "pool_size": pool.size(),
                        "checked_in": pool.checkedin(),
                        "checked_out": pool.checkedout(),
                        "overflow": pool.overflow(),
                        "utilization_percent": (pool.checkedout() / pool.size()) * 100
                    })
                    
        except Exception as e:
            logger.warning(f"Failed to get connection pool stats: {e}")
        
        return stats
    
    async def _calculate_cache_hit_ratios(self, session: AsyncSession) -> Dict[str, float]:
        """
        Calculate database cache hit ratios
        """
        cache_ratios = {}
        
        try:
            # Overall buffer cache hit ratio
            buffer_cache_query = """
                SELECT 
                    sum(heap_blks_hit) as heap_hit,
                    sum(heap_blks_read) as heap_read,
                    sum(idx_blks_hit) as idx_hit,
                    sum(idx_blks_read) as idx_read
                FROM pg_statio_user_tables;
            """
            
            result = await session.execute(text(buffer_cache_query))
            row = result.fetchone()
            
            if row:
                total_hit = (row.heap_hit or 0) + (row.idx_hit or 0)
                total_read = (row.heap_read or 0) + (row.idx_read or 0)
                total_access = total_hit + total_read
                
                if total_access > 0:
                    cache_ratios["buffer_cache_hit_ratio"] = total_hit / total_access
                
                # Table-specific cache hit ratios
                table_cache_query = """
                    SELECT 
                        relname,
                        heap_blks_hit,
                        heap_blks_read,
                        idx_blks_hit,
                        idx_blks_read
                    FROM pg_statio_user_tables
                    WHERE heap_blks_read + heap_blks_hit > 0;
                """
                
                table_result = await session.execute(text(table_cache_query))
                
                for table_row in table_result:
                    table_hit = (table_row.heap_blks_hit or 0) + (table_row.idx_blks_hit or 0)
                    table_read = (table_row.heap_blks_read or 0) + (table_row.idx_blks_read or 0)
                    table_total = table_hit + table_read
                    
                    if table_total > 0:
                        cache_ratios[f"{table_row.relname}_cache_hit_ratio"] = table_hit / table_total
                        
        except Exception as e:
            logger.warning(f"Failed to calculate cache hit ratios: {e}")
        
        return cache_ratios
    
    async def _generate_recommendations(self, analysis: PerformanceOptimizationResult) -> List[str]:
        """
        Generate performance optimization recommendations based on analysis
        """
        recommendations = []
        
        # Slow query recommendations
        if analysis.slow_queries:
            recommendations.append(
                f"🐌 Found {len(analysis.slow_queries)} slow queries. "
                f"Consider optimizing queries with average execution time > "
                f"{self.performance_thresholds['slow_query_threshold_ms']}ms"
            )
        
        # Index recommendations
        high_priority_indexes = [idx for idx in analysis.missing_indexes if idx.priority <= 2]
        if high_priority_indexes:
            recommendations.append(
                f"📊 Create {len(high_priority_indexes)} high-priority indexes to improve query performance"
            )
        
        # Cache hit ratio recommendations
        low_cache_tables = [
            table for table, ratio in analysis.cache_hit_ratios.items() 
            if ratio < self.performance_thresholds["low_cache_hit_ratio"]
        ]
        if low_cache_tables:
            recommendations.append(
                f"💾 {len(low_cache_tables)} tables have low cache hit ratios. "
                "Consider increasing shared_buffers or work_mem"
            )
        
        # Connection pool recommendations
        if analysis.connection_pool_stats.get("utilization_percent", 0) > 80:
            recommendations.append(
                "🔌 Connection pool utilization is high (>80%). "
                "Consider increasing pool size or optimizing connection usage"
            )
        
        # Table maintenance recommendations
        tables_needing_vacuum = []
        for table, stats in analysis.table_stats.items():
            if stats.get("dead_row_ratio", 0) > 0.1:  # 10% dead rows
                tables_needing_vacuum.append(table)
        
        if tables_needing_vacuum:
            recommendations.append(
                f"🧹 {len(tables_needing_vacuum)} tables have high dead row ratios. "
                "Run VACUUM ANALYZE on these tables"
            )
        
        # TimescaleDB specific recommendations
        if settings.TIMESCALEDB_ENABLED:
            recommendations.append(
                "⏰ Consider enabling TimescaleDB compression policies for older time-series data"
            )
        
        return recommendations
    
    def _calculate_optimization_score(self, analysis: PerformanceOptimizationResult) -> float:
        """
        Calculate overall optimization score (0-100)
        """
        score = 100.0
        
        # Deduct points for slow queries
        slow_query_penalty = min(len(analysis.slow_queries) * 5, 30)
        score -= slow_query_penalty
        
        # Deduct points for missing high-priority indexes
        high_priority_missing = len([idx for idx in analysis.missing_indexes if idx.priority <= 2])
        index_penalty = min(high_priority_missing * 10, 25)
        score -= index_penalty
        
        # Deduct points for low cache hit ratios
        low_cache_count = len([
            ratio for ratio in analysis.cache_hit_ratios.values() 
            if ratio < self.performance_thresholds["low_cache_hit_ratio"]
        ])
        cache_penalty = min(low_cache_count * 5, 15)
        score -= cache_penalty
        
        # Deduct points for high connection pool utilization
        pool_util = analysis.connection_pool_stats.get("utilization_percent", 0)
        if pool_util > 80:
            score -= min((pool_util - 80) * 0.5, 10)
        
        # Deduct points for tables needing maintenance
        maintenance_needed = len([
            stats for stats in analysis.table_stats.values()
            if stats.get("dead_row_ratio", 0) > 0.1
        ])
        maintenance_penalty = min(maintenance_needed * 3, 10)
        score -= maintenance_penalty
        
        return max(score, 0.0)
    
    async def apply_automatic_optimizations(self, session: AsyncSession) -> Dict[str, Any]:
        """
        Apply safe automatic optimizations
        """
        results = {
            "applied_optimizations": [],
            "skipped_optimizations": [],
            "errors": []
        }
        
        try:
            # Update table statistics
            tables_to_analyze = [
                "enhanced_users", "enhanced_portfolios", "enhanced_accounts",
                "enhanced_transactions", "enhanced_market_data", "user_activity_log"
            ]
            
            for table in tables_to_analyze:
                try:
                    await session.execute(text(f"ANALYZE {table};"))
                    results["applied_optimizations"].append(f"ANALYZE {table}")
                except Exception as e:
                    results["errors"].append(f"Failed to analyze {table}: {e}")
            
            # Vacuum tables with high dead row ratios (non-blocking)
            analysis = await self.analyze_performance(session)
            
            for table, stats in analysis.table_stats.items():
                if stats.get("dead_row_ratio", 0) > 0.2:  # 20% dead rows
                    try:
                        # Use non-blocking vacuum
                        await session.execute(text(f"VACUUM (ANALYZE, VERBOSE) {table};"))
                        results["applied_optimizations"].append(f"VACUUM {table}")
                    except Exception as e:
                        results["errors"].append(f"Failed to vacuum {table}: {e}")
            
            # Apply database parameter optimizations
            optimization_params = {
                "work_mem": "'256MB'",
                "maintenance_work_mem": "'512MB'",
                "effective_cache_size": "'4GB'",
                "random_page_cost": "1.1"
            }
            
            for param, value in optimization_params.items():
                try:
                    await session.execute(text(f"SET {param} = {value};"))
                    results["applied_optimizations"].append(f"SET {param} = {value}")
                except Exception as e:
                    results["skipped_optimizations"].append(f"Could not set {param}: {e}")
            
            await session.commit()
            logger.info(f"Applied {len(results['applied_optimizations'])} automatic optimizations")
            
        except Exception as e:
            await session.rollback()
            results["errors"].append(f"Automatic optimization failed: {e}")
        
        return results
    
    async def generate_performance_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive performance report
        """
        logger.info("Generating comprehensive performance report")
        
        try:
            async with db_manager.get_async_session() as session:
                # Run performance analysis
                analysis = await self.analyze_performance(session)
                
                # Apply automatic optimizations
                optimization_results = await self.apply_automatic_optimizations(session)
                
                report = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "optimization_score": analysis.optimization_score,
                    "performance_grade": self._get_performance_grade(analysis.optimization_score),
                    "summary": {
                        "slow_queries": len(analysis.slow_queries),
                        "missing_indexes": len(analysis.missing_indexes),
                        "high_priority_indexes": len([idx for idx in analysis.missing_indexes if idx.priority <= 2]),
                        "tables_analyzed": len(analysis.table_stats),
                        "recommendations": len(analysis.recommendations)
                    },
                    "slow_queries": [
                        {
                            "query": q.query,
                            "avg_time_ms": q.avg_execution_time,
                            "execution_count": q.execution_count,
                            "total_time_ms": q.total_execution_time
                        }
                        for q in analysis.slow_queries[:10]  # Top 10 slow queries
                    ],
                    "index_recommendations": [
                        {
                            "table": idx.table_name,
                            "columns": idx.recommended_columns,
                            "reason": idx.reason,
                            "priority": idx.priority,
                            "create_statement": idx.create_statement
                        }
                        for idx in analysis.missing_indexes[:10]  # Top 10 recommendations
                    ],
                    "cache_performance": analysis.cache_hit_ratios,
                    "connection_pool": analysis.connection_pool_stats,
                    "recommendations": analysis.recommendations,
                    "automatic_optimizations": optimization_results,
                    "largest_tables": self._get_largest_tables(analysis.table_stats),
                    "maintenance_status": self._get_maintenance_status(analysis.table_stats)
                }
                
                logger.info(f"Performance report generated. Score: {analysis.optimization_score:.1f}")
                return report
                
        except Exception as e:
            logger.error(f"Failed to generate performance report: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def _get_performance_grade(self, score: float) -> str:
        """Convert optimization score to letter grade"""
        if score >= 90:
            return "A"
        elif score >= 80:
            return "B"
        elif score >= 70:
            return "C"
        elif score >= 60:
            return "D"
        else:
            return "F"
    
    def _get_largest_tables(self, table_stats: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get the largest tables by size"""
        tables_with_size = [
            {
                "table": table,
                "total_size": stats.get("total_size", "Unknown"),
                "live_rows": stats.get("live_rows", 0)
            }
            for table, stats in table_stats.items()
            if "total_size_bytes" in stats
        ]
        
        return sorted(
            tables_with_size,
            key=lambda x: table_stats[x["table"]].get("total_size_bytes", 0),
            reverse=True
        )[:10]
    
    def _get_maintenance_status(self, table_stats: Dict[str, Any]) -> Dict[str, List[str]]:
        """Get maintenance status for tables"""
        needs_vacuum = []
        needs_analyze = []
        
        for table, stats in table_stats.items():
            if stats.get("dead_row_ratio", 0) > 0.1:
                needs_vacuum.append(table)
            
            if not stats.get("last_analyze") or (
                datetime.utcnow() - stats.get("last_analyze", datetime.utcnow())
            ).days > 7:
                needs_analyze.append(table)
        
        return {
            "needs_vacuum": needs_vacuum,
            "needs_analyze": needs_analyze
        }


# Global optimizer instance
performance_optimizer = DatabasePerformanceOptimizer()


async def main():
    """
    Main function for running performance optimization
    """
    print("Financial Planning System - Database Performance Optimizer")
    print("=" * 60)
    
    # Initialize database connection
    await db_manager.initialize()
    
    try:
        # Generate comprehensive performance report
        report = await performance_optimizer.generate_performance_report()
        
        if "error" in report:
            print(f"❌ Performance analysis failed: {report['error']}")
            return
        
        # Display report summary
        print(f"\n📊 Performance Score: {report['optimization_score']:.1f}/100 (Grade: {report['performance_grade']})")
        print(f"📈 Analysis Summary:")
        print(f"   • Slow Queries: {report['summary']['slow_queries']}")
        print(f"   • Missing Indexes: {report['summary']['missing_indexes']} (High Priority: {report['summary']['high_priority_indexes']})")
        print(f"   • Tables Analyzed: {report['summary']['tables_analyzed']}")
        print(f"   • Recommendations: {report['summary']['recommendations']}")
        
        # Display top recommendations
        if report['recommendations']:
            print(f"\n🎯 Top Recommendations:")
            for i, rec in enumerate(report['recommendations'][:5], 1):
                print(f"   {i}. {rec}")
        
        # Display automatic optimizations applied
        auto_opts = report.get('automatic_optimizations', {})
        if auto_opts.get('applied_optimizations'):
            print(f"\n✅ Automatic Optimizations Applied: {len(auto_opts['applied_optimizations'])}")
            for opt in auto_opts['applied_optimizations'][:3]:
                print(f"   • {opt}")
        
        # Display cache performance
        cache_perf = report.get('cache_performance', {})
        if 'buffer_cache_hit_ratio' in cache_perf:
            hit_ratio = cache_perf['buffer_cache_hit_ratio'] * 100
            print(f"\n💾 Buffer Cache Hit Ratio: {hit_ratio:.1f}%")
        
        # Save detailed report to file
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        report_file = f"performance_report_{timestamp}.json"
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"\n📄 Detailed report saved to: {report_file}")
        
    finally:
        await db_manager.shutdown()


if __name__ == "__main__":
    asyncio.run(main())