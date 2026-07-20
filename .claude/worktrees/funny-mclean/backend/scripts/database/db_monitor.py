#!/usr/bin/env python3
"""
Database Performance Monitoring and Alerting System

This script provides comprehensive database monitoring capabilities:
- Real-time performance metrics collection
- Connection pool monitoring
- Query performance analysis
- Disk usage and table size tracking
- Automated alerting for anomalies
- Performance trend analysis
- Slow query identification and reporting

Usage:
    python scripts/database/db_monitor.py status        # Current status overview
    python scripts/database/db_monitor.py metrics       # Detailed metrics
    python scripts/database/db_monitor.py slow-queries  # Identify slow queries
    python scripts/database/db_monitor.py connections   # Monitor connections
    python scripts/database/db_monitor.py alerts        # Check alerts
    python scripts/database/db_monitor.py report        # Generate report
"""

import asyncio
import logging
import sys
import json
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional
import argparse
from dataclasses import dataclass, asdict

# Add the backend directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from app.database.base import get_db_session, engine
from app.database.models import SystemEvent
from sqlalchemy import text

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class MetricThreshold:
    """Performance metric threshold configuration"""
    metric_name: str
    warning_threshold: float
    critical_threshold: float
    comparison: str  # 'greater', 'less', 'equal'
    unit: str

@dataclass
class PerformanceAlert:
    """Performance alert structure"""
    timestamp: str
    severity: str  # warning, critical
    metric_name: str
    current_value: float
    threshold_value: float
    message: str
    suggested_action: str

class DatabaseMonitor:
    """Database performance monitoring and alerting"""
    
    def __init__(self):
        self.thresholds = self._init_thresholds()
        self.alerts = []
        
        # Monitoring configuration
        self.config = {
            "collection_interval": 60,  # seconds
            "retention_days": 30,
            "slow_query_threshold": 1000,  # milliseconds
            "connection_pool_warning": 0.8,  # 80% utilization
            "disk_usage_warning": 0.85,  # 85% disk usage
            "memory_warning": 0.9  # 90% memory usage
        }
    
    def _init_thresholds(self) -> Dict[str, MetricThreshold]:
        """Initialize performance thresholds"""
        return {
            "connection_pool_utilization": MetricThreshold(
                "connection_pool_utilization", 0.8, 0.95, "greater", "percent"
            ),
            "slow_queries_per_minute": MetricThreshold(
                "slow_queries_per_minute", 5, 15, "greater", "count"
            ),
            "average_query_time": MetricThreshold(
                "average_query_time", 100, 500, "greater", "milliseconds"
            ),
            "database_size": MetricThreshold(
                "database_size", 10, 50, "greater", "GB"
            ),
            "active_connections": MetricThreshold(
                "active_connections", 50, 100, "greater", "count"
            ),
            "lock_waits": MetricThreshold(
                "lock_waits", 1, 5, "greater", "count"
            ),
            "deadlocks": MetricThreshold(
                "deadlocks", 0, 1, "greater", "count"
            )
        }
    
    async def collect_metrics(self) -> Dict[str, Any]:
        """Collect comprehensive performance metrics"""
        logger.info("Collecting database performance metrics...")
        
        metrics = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "connection_pool": {},
            "database_stats": {},
            "query_performance": {},
            "table_stats": {},
            "system_stats": {},
            "alerts": []
        }
        
        try:
            async with get_db_session() as session:
                # Connection pool metrics
                if engine:
                    pool = engine.pool
                    pool_size = pool.size()
                    checked_out = pool.checkedout()
                    
                    metrics["connection_pool"] = {
                        "size": pool_size,
                        "checked_in": pool.checkedin(),
                        "checked_out": checked_out,
                        "overflow": pool.overflow(),
                        "utilization": (checked_out / pool_size) if pool_size > 0 else 0
                    }
                
                # Database statistics
                db_stats = await self._collect_database_stats(session)
                metrics["database_stats"] = db_stats
                
                # Query performance metrics
                query_stats = await self._collect_query_stats(session)
                metrics["query_performance"] = query_stats
                
                # Table statistics
                table_stats = await self._collect_table_stats(session)
                metrics["table_stats"] = table_stats
                
                # System statistics
                system_stats = await self._collect_system_stats(session)
                metrics["system_stats"] = system_stats
                
                # Check for alerts
                alerts = self._check_alerts(metrics)
                metrics["alerts"] = alerts
                
                # Log metrics collection
                await self._log_metrics_event(session, metrics)
                
        except Exception as e:
            logger.error(f"Error collecting metrics: {str(e)}")
            metrics["error"] = str(e)
        
        return metrics
    
    async def _collect_database_stats(self, session) -> Dict[str, Any]:
        """Collect database-level statistics"""
        try:
            stats = {}
            
            # Database size
            result = await session.execute(text("""
                SELECT pg_size_pretty(pg_database_size(current_database())) as size,
                       pg_database_size(current_database()) as size_bytes
            """))
            row = result.fetchone()
            if row:
                stats["database_size"] = row.size
                stats["database_size_bytes"] = row.size_bytes
            
            # Connection statistics
            result = await session.execute(text("""
                SELECT 
                    count(*) as total_connections,
                    count(*) FILTER (WHERE state = 'active') as active_connections,
                    count(*) FILTER (WHERE state = 'idle') as idle_connections,
                    count(*) FILTER (WHERE state = 'idle in transaction') as idle_in_transaction
                FROM pg_stat_activity 
                WHERE datname = current_database()
            """))
            row = result.fetchone()
            if row:
                stats["connections"] = {
                    "total": row.total_connections,
                    "active": row.active_connections,
                    "idle": row.idle_connections,
                    "idle_in_transaction": row.idle_in_transaction
                }
            
            # Transaction statistics
            result = await session.execute(text("""
                SELECT 
                    xact_commit,
                    xact_rollback,
                    blks_read,
                    blks_hit,
                    tup_returned,
                    tup_fetched,
                    tup_inserted,
                    tup_updated,
                    tup_deleted
                FROM pg_stat_database 
                WHERE datname = current_database()
            """))
            row = result.fetchone()
            if row:
                stats["transactions"] = {
                    "commits": row.xact_commit,
                    "rollbacks": row.xact_rollback,
                    "blocks_read": row.blks_read,
                    "blocks_hit": row.blks_hit,
                    "cache_hit_ratio": (row.blks_hit / (row.blks_hit + row.blks_read)) if (row.blks_hit + row.blks_read) > 0 else 0
                }
                
                stats["tuples"] = {
                    "returned": row.tup_returned,
                    "fetched": row.tup_fetched,
                    "inserted": row.tup_inserted,
                    "updated": row.tup_updated,
                    "deleted": row.tup_deleted
                }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error collecting database stats: {str(e)}")
            return {"error": str(e)}
    
    async def _collect_query_stats(self, session) -> Dict[str, Any]:
        """Collect query performance statistics"""
        try:
            stats = {}
            
            # Check if pg_stat_statements is available
            result = await session.execute(text("""
                SELECT EXISTS (
                    SELECT 1 FROM pg_extension WHERE extname = 'pg_stat_statements'
                )
            """))
            
            has_pg_stat_statements = result.scalar()
            
            if has_pg_stat_statements:
                # Top slow queries
                result = await session.execute(text("""
                    SELECT 
                        query,
                        calls,
                        total_exec_time,
                        mean_exec_time,
                        rows,
                        100.0 * shared_blks_hit / nullif(shared_blks_hit + shared_blks_read, 0) AS hit_percent
                    FROM pg_stat_statements 
                    WHERE mean_exec_time > :threshold
                    ORDER BY mean_exec_time DESC 
                    LIMIT 10
                """), {"threshold": self.config["slow_query_threshold"]})
                
                slow_queries = []
                for row in result:
                    slow_queries.append({
                        "query": row.query[:100] + "..." if len(row.query) > 100 else row.query,
                        "calls": row.calls,
                        "total_time": round(row.total_exec_time, 2),
                        "mean_time": round(row.mean_exec_time, 2),
                        "rows": row.rows,
                        "hit_percent": round(row.hit_percent or 0, 2)
                    })
                
                stats["slow_queries"] = slow_queries
                stats["slow_query_count"] = len(slow_queries)
            else:
                stats["slow_queries"] = []
                stats["slow_query_count"] = 0
                stats["note"] = "pg_stat_statements extension not available"
            
            # Lock statistics
            result = await session.execute(text("""
                SELECT 
                    COUNT(*) as total_locks,
                    COUNT(*) FILTER (WHERE NOT granted) as waiting_locks
                FROM pg_locks
            """))
            row = result.fetchone()
            if row:
                stats["locks"] = {
                    "total": row.total_locks,
                    "waiting": row.waiting_locks
                }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error collecting query stats: {str(e)}")
            return {"error": str(e)}
    
    async def _collect_table_stats(self, session) -> Dict[str, Any]:
        """Collect table-level statistics"""
        try:
            stats = {}
            
            # Table sizes
            result = await session.execute(text("""
                SELECT 
                    schemaname,
                    tablename,
                    pg_total_relation_size(schemaname||'.'||tablename) as total_bytes,
                    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as total_size,
                    pg_relation_size(schemaname||'.'||tablename) as data_bytes,
                    pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) as data_size
                FROM pg_tables 
                WHERE schemaname = 'public'
                ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
                LIMIT 10
            """))
            
            table_sizes = []
            for row in result:
                table_sizes.append({
                    "schema": row.schemaname,
                    "table": row.tablename,
                    "total_size": row.total_size,
                    "total_bytes": row.total_bytes,
                    "data_size": row.data_size,
                    "data_bytes": row.data_bytes
                })
            
            stats["largest_tables"] = table_sizes
            
            # Table activity
            result = await session.execute(text("""
                SELECT 
                    schemaname,
                    tablename,
                    n_tup_ins as inserts,
                    n_tup_upd as updates,
                    n_tup_del as deletes,
                    n_live_tup as live_tuples,
                    n_dead_tup as dead_tuples,
                    last_vacuum,
                    last_autovacuum,
                    last_analyze,
                    last_autoanalyze
                FROM pg_stat_user_tables
                ORDER BY (n_tup_ins + n_tup_upd + n_tup_del) DESC
                LIMIT 10
            """))
            
            table_activity = []
            for row in result:
                table_activity.append({
                    "schema": row.schemaname,
                    "table": row.tablename,
                    "inserts": row.inserts,
                    "updates": row.updates,
                    "deletes": row.deletes,
                    "live_tuples": row.live_tuples,
                    "dead_tuples": row.dead_tuples,
                    "last_vacuum": row.last_vacuum.isoformat() if row.last_vacuum else None,
                    "last_analyze": row.last_analyze.isoformat() if row.last_analyze else None
                })
            
            stats["most_active_tables"] = table_activity
            
            return stats
            
        except Exception as e:
            logger.error(f"Error collecting table stats: {str(e)}")
            return {"error": str(e)}
    
    async def _collect_system_stats(self, session) -> Dict[str, Any]:
        """Collect system-level statistics"""
        try:
            stats = {}
            
            # Current timestamp and uptime info
            result = await session.execute(text("""
                SELECT 
                    current_timestamp as current_time,
                    pg_postmaster_start_time() as start_time,
                    EXTRACT(EPOCH FROM (current_timestamp - pg_postmaster_start_time())) as uptime_seconds
            """))
            row = result.fetchone()
            if row:
                stats["uptime"] = {
                    "current_time": row.current_time.isoformat(),
                    "start_time": row.start_time.isoformat(),
                    "uptime_seconds": int(row.uptime_seconds),
                    "uptime_formatted": str(timedelta(seconds=int(row.uptime_seconds)))
                }
            
            # Configuration settings
            result = await session.execute(text("""
                SELECT name, setting, unit, category, short_desc
                FROM pg_settings 
                WHERE name IN ('max_connections', 'shared_buffers', 'effective_cache_size', 
                              'maintenance_work_mem', 'checkpoint_completion_target', 'wal_buffers')
            """))
            
            settings = {}
            for row in result:
                settings[row.name] = {
                    "value": row.setting,
                    "unit": row.unit,
                    "description": row.short_desc
                }
            
            stats["key_settings"] = settings
            
            return stats
            
        except Exception as e:
            logger.error(f"Error collecting system stats: {str(e)}")
            return {"error": str(e)}
    
    def _check_alerts(self, metrics: Dict[str, Any]) -> List[PerformanceAlert]:
        """Check metrics against thresholds and generate alerts"""
        alerts = []
        
        try:
            # Check connection pool utilization
            if "connection_pool" in metrics:
                utilization = metrics["connection_pool"].get("utilization", 0)
                threshold = self.thresholds["connection_pool_utilization"]
                
                if utilization >= threshold.critical_threshold:
                    alerts.append(PerformanceAlert(
                        timestamp=datetime.now(timezone.utc).isoformat(),
                        severity="critical",
                        metric_name="Connection Pool Utilization",
                        current_value=utilization,
                        threshold_value=threshold.critical_threshold,
                        message=f"Connection pool utilization at {utilization:.1%}",
                        suggested_action="Increase connection pool size or investigate connection leaks"
                    ))
                elif utilization >= threshold.warning_threshold:
                    alerts.append(PerformanceAlert(
                        timestamp=datetime.now(timezone.utc).isoformat(),
                        severity="warning",
                        metric_name="Connection Pool Utilization",
                        current_value=utilization,
                        threshold_value=threshold.warning_threshold,
                        message=f"Connection pool utilization at {utilization:.1%}",
                        suggested_action="Monitor connection usage and consider pool size adjustment"
                    ))
            
            # Check slow queries
            if "query_performance" in metrics:
                slow_query_count = metrics["query_performance"].get("slow_query_count", 0)
                threshold = self.thresholds["slow_queries_per_minute"]
                
                if slow_query_count >= threshold.critical_threshold:
                    alerts.append(PerformanceAlert(
                        timestamp=datetime.now(timezone.utc).isoformat(),
                        severity="critical",
                        metric_name="Slow Queries",
                        current_value=slow_query_count,
                        threshold_value=threshold.critical_threshold,
                        message=f"{slow_query_count} slow queries detected",
                        suggested_action="Review and optimize slow queries, consider adding indexes"
                    ))
                elif slow_query_count >= threshold.warning_threshold:
                    alerts.append(PerformanceAlert(
                        timestamp=datetime.now(timezone.utc).isoformat(),
                        severity="warning",
                        metric_name="Slow Queries",
                        current_value=slow_query_count,
                        threshold_value=threshold.warning_threshold,
                        message=f"{slow_query_count} slow queries detected",
                        suggested_action="Monitor query performance and consider optimization"
                    ))
            
            # Check active connections
            if "database_stats" in metrics and "connections" in metrics["database_stats"]:
                active_connections = metrics["database_stats"]["connections"].get("active", 0)
                threshold = self.thresholds["active_connections"]
                
                if active_connections >= threshold.critical_threshold:
                    alerts.append(PerformanceAlert(
                        timestamp=datetime.now(timezone.utc).isoformat(),
                        severity="critical",
                        metric_name="Active Connections",
                        current_value=active_connections,
                        threshold_value=threshold.critical_threshold,
                        message=f"{active_connections} active database connections",
                        suggested_action="Investigate high connection usage, check for connection leaks"
                    ))
                elif active_connections >= threshold.warning_threshold:
                    alerts.append(PerformanceAlert(
                        timestamp=datetime.now(timezone.utc).isoformat(),
                        severity="warning",
                        metric_name="Active Connections",
                        current_value=active_connections,
                        threshold_value=threshold.warning_threshold,
                        message=f"{active_connections} active database connections",
                        suggested_action="Monitor connection usage patterns"
                    ))
            
        except Exception as e:
            logger.error(f"Error checking alerts: {str(e)}")
        
        return alerts
    
    async def _log_metrics_event(self, session, metrics: Dict[str, Any]) -> None:
        """Log metrics collection event"""
        try:
            # Create summary for logging
            summary = {
                "collection_timestamp": metrics["timestamp"],
                "connection_pool_utilization": metrics.get("connection_pool", {}).get("utilization", 0),
                "active_connections": metrics.get("database_stats", {}).get("connections", {}).get("active", 0),
                "slow_queries": metrics.get("query_performance", {}).get("slow_query_count", 0),
                "alerts_count": len(metrics.get("alerts", []))
            }
            
            system_event = SystemEvent(
                event_type="metrics_collected",
                event_category="monitoring",
                message="Database performance metrics collected",
                severity="info",
                additional_data=summary
            )
            session.add(system_event)
            await session.commit()
            
        except Exception as e:
            logger.error(f"Failed to log metrics event: {str(e)}")
    
    async def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive monitoring report"""
        logger.info("Generating database monitoring report...")
        
        report = {
            "report_timestamp": datetime.now(timezone.utc).isoformat(),
            "report_type": "database_monitoring",
            "current_metrics": {},
            "recommendations": [],
            "alert_summary": {},
            "health_score": 0
        }
        
        try:
            # Collect current metrics
            current_metrics = await self.collect_metrics()
            report["current_metrics"] = current_metrics
            
            # Generate recommendations
            recommendations = self._generate_recommendations(current_metrics)
            report["recommendations"] = recommendations
            
            # Alert summary
            alerts = current_metrics.get("alerts", [])
            report["alert_summary"] = {
                "total_alerts": len(alerts),
                "critical_alerts": len([a for a in alerts if a.severity == "critical"]),
                "warning_alerts": len([a for a in alerts if a.severity == "warning"]),
                "alerts": [asdict(alert) for alert in alerts]
            }
            
            # Calculate health score
            health_score = self._calculate_health_score(current_metrics)
            report["health_score"] = health_score
            
        except Exception as e:
            logger.error(f"Error generating report: {str(e)}")
            report["error"] = str(e)
        
        return report
    
    def _generate_recommendations(self, metrics: Dict[str, Any]) -> List[str]:
        """Generate performance recommendations based on metrics"""
        recommendations = []
        
        try:
            # Connection pool recommendations
            if "connection_pool" in metrics:
                utilization = metrics["connection_pool"].get("utilization", 0)
                if utilization > 0.8:
                    recommendations.append("Consider increasing connection pool size due to high utilization")
                elif utilization < 0.1:
                    recommendations.append("Connection pool may be oversized, consider reducing for better resource utilization")
            
            # Query performance recommendations
            if "query_performance" in metrics:
                slow_queries = metrics["query_performance"].get("slow_query_count", 0)
                if slow_queries > 0:
                    recommendations.append("Optimize slow queries by adding indexes or rewriting query logic")
            
            # Cache hit ratio recommendations
            if "database_stats" in metrics and "transactions" in metrics["database_stats"]:
                cache_hit_ratio = metrics["database_stats"]["transactions"].get("cache_hit_ratio", 0)
                if cache_hit_ratio < 0.95:
                    recommendations.append("Cache hit ratio is low, consider increasing shared_buffers")
            
            # Table maintenance recommendations
            if "table_stats" in metrics and "most_active_tables" in metrics["table_stats"]:
                for table in metrics["table_stats"]["most_active_tables"]:
                    if table.get("dead_tuples", 0) > table.get("live_tuples", 0) * 0.1:
                        recommendations.append(f"Table {table['table']} has high dead tuple ratio, consider manual VACUUM")
            
            # Generic recommendations if no issues found
            if not recommendations:
                recommendations.append("Database performance appears optimal")
                recommendations.append("Continue monitoring for proactive maintenance")
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {str(e)}")
            recommendations.append("Error generating recommendations - manual review recommended")
        
        return recommendations
    
    def _calculate_health_score(self, metrics: Dict[str, Any]) -> int:
        """Calculate overall database health score (0-100)"""
        try:
            score = 100
            
            # Deduct for alerts
            alerts = metrics.get("alerts", [])
            critical_alerts = len([a for a in alerts if a.severity == "critical"])
            warning_alerts = len([a for a in alerts if a.severity == "warning"])
            
            score -= critical_alerts * 20  # -20 per critical alert
            score -= warning_alerts * 5    # -5 per warning alert
            
            # Deduct for poor cache hit ratio
            if "database_stats" in metrics and "transactions" in metrics["database_stats"]:
                cache_hit_ratio = metrics["database_stats"]["transactions"].get("cache_hit_ratio", 1.0)
                if cache_hit_ratio < 0.95:
                    score -= (0.95 - cache_hit_ratio) * 100
            
            # Deduct for high connection pool utilization
            if "connection_pool" in metrics:
                utilization = metrics["connection_pool"].get("utilization", 0)
                if utilization > 0.9:
                    score -= (utilization - 0.9) * 100
            
            return max(0, min(100, int(score)))
            
        except Exception as e:
            logger.error(f"Error calculating health score: {str(e)}")
            return 50  # Neutral score if calculation fails

async def main():
    """Main function for command line interface"""
    parser = argparse.ArgumentParser(
        description="Database Performance Monitoring System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python db_monitor.py status        # Quick status overview
    python db_monitor.py metrics       # Detailed metrics collection
    python db_monitor.py slow-queries  # Show slow queries
    python db_monitor.py connections   # Monitor connections
    python db_monitor.py alerts        # Check current alerts
    python db_monitor.py report        # Generate comprehensive report
        """
    )
    
    parser.add_argument(
        'command',
        choices=['status', 'metrics', 'slow-queries', 'connections', 'alerts', 'report'],
        help='Monitoring command to execute'
    )
    
    parser.add_argument(
        '--output-format',
        choices=['text', 'json'],
        default='text',
        help='Output format for results'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    monitor = DatabaseMonitor()
    
    try:
        if args.command == 'status':
            metrics = await monitor.collect_metrics()
            
            if args.output_format == 'json':
                print(json.dumps(metrics, indent=2))
            else:
                print("\n" + "="*60)
                print("DATABASE STATUS OVERVIEW")
                print("="*60)
                print(f"Timestamp: {metrics['timestamp']}")
                
                if "connection_pool" in metrics:
                    pool = metrics["connection_pool"]
                    print(f"\nConnection Pool:")
                    print(f"  Utilization: {pool.get('utilization', 0):.1%}")
                    print(f"  Active: {pool.get('checked_out', 0)}/{pool.get('size', 0)}")
                
                if "database_stats" in metrics and "connections" in metrics["database_stats"]:
                    conn = metrics["database_stats"]["connections"]
                    print(f"\nDatabase Connections:")
                    print(f"  Active: {conn.get('active', 0)}")
                    print(f"  Total: {conn.get('total', 0)}")
                
                alerts = metrics.get("alerts", [])
                if alerts:
                    print(f"\nAlerts: {len(alerts)}")
                    for alert in alerts:
                        print(f"  {alert.severity.upper()}: {alert.message}")
                else:
                    print("\n✅ No alerts")
        
        elif args.command == 'metrics':
            metrics = await monitor.collect_metrics()
            
            if args.output_format == 'json':
                print(json.dumps(metrics, indent=2))
            else:
                print("\n" + "="*60)
                print("DETAILED METRICS")
                print("="*60)
                print(json.dumps(metrics, indent=2))
        
        elif args.command == 'slow-queries':
            metrics = await monitor.collect_metrics()
            slow_queries = metrics.get("query_performance", {}).get("slow_queries", [])
            
            if args.output_format == 'json':
                print(json.dumps(slow_queries, indent=2))
            else:
                print("\n" + "="*60)
                print("SLOW QUERIES")
                print("="*60)
                if slow_queries:
                    for i, query in enumerate(slow_queries, 1):
                        print(f"\n{i}. Query: {query['query']}")
                        print(f"   Mean time: {query['mean_time']}ms")
                        print(f"   Calls: {query['calls']}")
                        print(f"   Total time: {query['total_time']}ms")
                else:
                    print("✅ No slow queries detected")
        
        elif args.command == 'connections':
            metrics = await monitor.collect_metrics()
            
            pool_info = metrics.get("connection_pool", {})
            db_connections = metrics.get("database_stats", {}).get("connections", {})
            
            if args.output_format == 'json':
                print(json.dumps({"pool": pool_info, "database": db_connections}, indent=2))
            else:
                print("\n" + "="*60)
                print("CONNECTION MONITORING")
                print("="*60)
                
                print("\nConnection Pool:")
                for key, value in pool_info.items():
                    if key == "utilization":
                        print(f"  {key}: {value:.1%}")
                    else:
                        print(f"  {key}: {value}")
                
                print("\nDatabase Connections:")
                for key, value in db_connections.items():
                    print(f"  {key}: {value}")
        
        elif args.command == 'alerts':
            metrics = await monitor.collect_metrics()
            alerts = metrics.get("alerts", [])
            
            if args.output_format == 'json':
                print(json.dumps([asdict(alert) for alert in alerts], indent=2))
            else:
                print("\n" + "="*60)
                print("CURRENT ALERTS")
                print("="*60)
                
                if alerts:
                    for alert in alerts:
                        severity_icon = "🔴" if alert.severity == "critical" else "⚠️"
                        print(f"\n{severity_icon} {alert.severity.upper()}: {alert.metric_name}")
                        print(f"   Message: {alert.message}")
                        print(f"   Current: {alert.current_value}")
                        print(f"   Threshold: {alert.threshold_value}")
                        print(f"   Action: {alert.suggested_action}")
                else:
                    print("✅ No active alerts")
        
        elif args.command == 'report':
            report = await monitor.generate_report()
            
            if args.output_format == 'json':
                print(json.dumps(report, indent=2))
            else:
                print("\n" + "="*80)
                print("DATABASE MONITORING REPORT")
                print("="*80)
                
                print(f"Report Generated: {report['report_timestamp']}")
                print(f"Health Score: {report['health_score']}/100")
                
                alert_summary = report.get("alert_summary", {})
                total_alerts = alert_summary.get("total_alerts", 0)
                if total_alerts > 0:
                    print(f"\nAlerts: {total_alerts} total")
                    print(f"  Critical: {alert_summary.get('critical_alerts', 0)}")
                    print(f"  Warnings: {alert_summary.get('warning_alerts', 0)}")
                else:
                    print("\n✅ No active alerts")
                
                recommendations = report.get("recommendations", [])
                if recommendations:
                    print("\nRecommendations:")
                    for i, rec in enumerate(recommendations, 1):
                        print(f"  {i}. {rec}")
                
                print("\n" + "="*80)
    
    except Exception as e:
        logger.error(f"Command failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())