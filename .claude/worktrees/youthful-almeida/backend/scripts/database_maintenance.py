#!/usr/bin/env python3
"""
Database maintenance script for routine operations and monitoring
"""

import asyncio
import argparse
import sys
import json
from pathlib import Path
from datetime import datetime, timezone
import logging

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database.utils import db_manager
from app.database.performance import performance_monitor, query_optimizer
from app.database.retention import retention_manager
from app.database.audit import audit_logger, AuditSeverity
from app.core.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DatabaseMaintenanceOrchestrator:
    """Orchestrates routine database maintenance operations"""
    
    async def vacuum_analyze_all_tables(self, verbose: bool = False) -> dict:
        """Perform VACUUM ANALYZE on all tables"""
        
        logger.info("Starting VACUUM ANALYZE on all tables")
        start_time = datetime.now(timezone.utc)
        
        try:
            await db_manager.initialize()
            
            # Get list of all tables
            tables_query = """
                SELECT schemaname, tablename 
                FROM pg_tables 
                WHERE schemaname = 'public'
            """
            
            async with db_manager.async_engine.begin() as conn:
                from sqlalchemy import text
                result = await conn.execute(text(tables_query))
                tables = [dict(row._mapping) for row in result]
            
            vacuum_results = []
            
            for table in tables:
                table_name = f"{table['schemaname']}.{table['tablename']}"
                table_start = datetime.now(timezone.utc)
                
                try:
                    vacuum_cmd = f"VACUUM {'VERBOSE' if verbose else ''} ANALYZE {table_name}"
                    
                    async with db_manager.async_engine.begin() as conn:
                        await conn.execute(text(vacuum_cmd))
                    
                    table_duration = (datetime.now(timezone.utc) - table_start).total_seconds()
                    
                    vacuum_results.append({
                        'table': table_name,
                        'success': True,
                        'duration_seconds': table_duration
                    })
                    
                    logger.info(f"VACUUM ANALYZE completed for {table_name} ({table_duration:.2f}s)")
                
                except Exception as e:
                    vacuum_results.append({
                        'table': table_name,
                        'success': False,
                        'error': str(e)
                    })
                    logger.error(f"VACUUM ANALYZE failed for {table_name}: {e}")
            
            total_duration = (datetime.now(timezone.utc) - start_time).total_seconds()
            
            result = {
                'operation': 'vacuum_analyze',
                'start_time': start_time.isoformat(),
                'duration_seconds': total_duration,
                'tables_processed': len(tables),
                'successful_operations': len([r for r in vacuum_results if r['success']]),
                'failed_operations': len([r for r in vacuum_results if not r['success']]),
                'table_results': vacuum_results
            }
            
            logger.info(f"VACUUM ANALYZE completed: {result['successful_operations']}/{result['tables_processed']} tables")
            return result
        
        finally:
            await db_manager.close()
    
    async def reindex_all_tables(self, concurrently: bool = True) -> dict:
        """Rebuild all indexes"""
        
        logger.info("Starting REINDEX operation")
        start_time = datetime.now(timezone.utc)
        
        try:
            await db_manager.initialize()
            
            # Get list of all indexes
            indexes_query = """
                SELECT 
                    schemaname,
                    tablename,
                    indexname
                FROM pg_indexes 
                WHERE schemaname = 'public'
                AND indexname NOT LIKE '%_pkey'  -- Skip primary keys for REINDEX CONCURRENTLY
            """
            
            async with db_manager.async_engine.begin() as conn:
                from sqlalchemy import text
                result = await conn.execute(text(indexes_query))
                indexes = [dict(row._mapping) for row in result]
            
            reindex_results = []
            
            for index in indexes:
                index_name = index['indexname']
                index_start = datetime.now(timezone.utc)
                
                try:
                    reindex_cmd = f"REINDEX {'CONCURRENTLY' if concurrently else ''} INDEX {index_name}"
                    
                    async with db_manager.async_engine.begin() as conn:
                        await conn.execute(text(reindex_cmd))
                    
                    index_duration = (datetime.now(timezone.utc) - index_start).total_seconds()
                    
                    reindex_results.append({
                        'index': index_name,
                        'table': index['tablename'],
                        'success': True,
                        'duration_seconds': index_duration
                    })
                    
                    logger.info(f"REINDEX completed for {index_name} ({index_duration:.2f}s)")
                
                except Exception as e:
                    reindex_results.append({
                        'index': index_name,
                        'table': index['tablename'],
                        'success': False,
                        'error': str(e)
                    })
                    logger.error(f"REINDEX failed for {index_name}: {e}")
            
            total_duration = (datetime.now(timezone.utc) - start_time).total_seconds()
            
            result = {
                'operation': 'reindex',
                'start_time': start_time.isoformat(),
                'duration_seconds': total_duration,
                'indexes_processed': len(indexes),
                'successful_operations': len([r for r in reindex_results if r['success']]),
                'failed_operations': len([r for r in reindex_results if not r['success']]),
                'index_results': reindex_results
            }
            
            logger.info(f"REINDEX completed: {result['successful_operations']}/{result['indexes_processed']} indexes")
            return result
        
        finally:
            await db_manager.close()
    
    async def analyze_query_performance(self) -> dict:
        """Analyze query performance and generate optimization report"""
        
        logger.info("Analyzing query performance")
        
        try:
            await db_manager.initialize()
            
            optimization_report = await query_optimizer.generate_optimization_report()
            
            logger.info(f"Query performance analysis completed: "
                       f"{optimization_report['summary']['slow_queries_analyzed']} slow queries analyzed")
            
            return optimization_report
        
        finally:
            await db_manager.close()
    
    async def check_database_health(self) -> dict:
        """Comprehensive database health check"""
        
        logger.info("Performing database health check")
        
        try:
            await db_manager.initialize()
            
            health_check = await db_manager.health_check()
            
            # Additional health checks
            async with db_manager.async_engine.begin() as conn:
                from sqlalchemy import text
                
                # Check for blocking queries
                blocking_queries = await conn.execute(text("""
                    SELECT count(*) as blocked_queries
                    FROM pg_catalog.pg_locks blocked_locks
                    JOIN pg_catalog.pg_stat_activity blocked_activity ON blocked_activity.pid = blocked_locks.pid
                    WHERE NOT blocked_locks.granted
                """))
                
                # Check database size growth
                db_size = await conn.execute(text("""
                    SELECT pg_database_size(current_database()) as size_bytes,
                           pg_size_pretty(pg_database_size(current_database())) as size_human
                """))
                
                # Check for long-running transactions
                long_transactions = await conn.execute(text("""
                    SELECT count(*) as long_transactions
                    FROM pg_stat_activity 
                    WHERE state = 'active' 
                    AND now() - query_start > interval '1 hour'
                """))
                
                health_check['additional_checks'] = {
                    'blocked_queries': dict(blocking_queries.first()._mapping),
                    'database_size': dict(db_size.first()._mapping),
                    'long_running_transactions': dict(long_transactions.first()._mapping)
                }
            
            logger.info(f"Database health check completed: {health_check['status']}")
            return health_check
        
        finally:
            await db_manager.close()
    
    async def cleanup_expired_data(self) -> dict:
        """Execute data retention policies and cleanup"""
        
        logger.info("Starting data cleanup operations")
        
        try:
            await db_manager.initialize()
            await retention_manager.start_scheduler()
            
            # Execute immediate cleanup
            cleanup_results = await retention_manager.cleanup_orphaned_data()
            
            # Get retention status
            retention_status = await retention_manager.get_retention_status()
            
            result = {
                'operation': 'data_cleanup',
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cleanup_results': cleanup_results,
                'retention_status': retention_status
            }
            
            logger.info(f"Data cleanup completed: {sum(cleanup_results.values())} records cleaned")
            return result
        
        finally:
            await retention_manager.stop_scheduler()
            await db_manager.close()
    
    async def generate_maintenance_report(self) -> dict:
        """Generate comprehensive maintenance report"""
        
        logger.info("Generating comprehensive maintenance report")
        
        try:
            # Collect all maintenance information
            health_check = await self.check_database_health()
            performance_report = await self.analyze_query_performance()
            cleanup_status = await self.cleanup_expired_data()
            
            report = {
                'report_timestamp': datetime.now(timezone.utc).isoformat(),
                'database_health': health_check,
                'performance_analysis': performance_report,
                'data_cleanup_status': cleanup_status,
                'recommendations': []
            }
            
            # Generate recommendations based on findings
            if health_check['status'] != 'healthy':
                report['recommendations'].append("Database health issues detected - investigate immediately")
            
            if performance_report['summary']['slow_queries_analyzed'] > 10:
                report['recommendations'].append("High number of slow queries - consider optimization")
            
            if health_check.get('additional_checks', {}).get('blocked_queries', {}).get('blocked_queries', 0) > 0:
                report['recommendations'].append("Blocked queries detected - check for locking issues")
            
            logger.info("Comprehensive maintenance report generated")
            return report
        
        except Exception as e:
            logger.error(f"Failed to generate maintenance report: {e}")
            return {
                'report_timestamp': datetime.now(timezone.utc).isoformat(),
                'error': str(e),
                'status': 'failed'
            }
    
    async def update_table_statistics(self) -> dict:
        """Update table statistics for query optimization"""
        
        logger.info("Updating table statistics")
        start_time = datetime.now(timezone.utc)
        
        try:
            await db_manager.initialize()
            
            async with db_manager.async_engine.begin() as conn:
                from sqlalchemy import text
                
                # Update statistics for all tables
                await conn.execute(text("ANALYZE"))
            
            duration = (datetime.now(timezone.utc) - start_time).total_seconds()
            
            result = {
                'operation': 'update_statistics',
                'start_time': start_time.isoformat(),
                'duration_seconds': duration,
                'success': True
            }
            
            logger.info(f"Table statistics updated ({duration:.2f}s)")
            return result
        
        except Exception as e:
            result = {
                'operation': 'update_statistics',
                'start_time': start_time.isoformat(),
                'success': False,
                'error': str(e)
            }
            logger.error(f"Failed to update table statistics: {e}")
            return result
        
        finally:
            await db_manager.close()


async def main():
    """Main maintenance script entry point"""
    
    parser = argparse.ArgumentParser(description='Database Maintenance Tool')
    parser.add_argument('operation', 
                       choices=['vacuum', 'reindex', 'analyze', 'health', 'cleanup', 'report', 'statistics'],
                       help='Maintenance operation to perform')
    parser.add_argument('--verbose', action='store_true', help='Verbose output for VACUUM operations')
    parser.add_argument('--no-concurrent', action='store_true', help='Disable concurrent operations')
    parser.add_argument('--output-json', action='store_true', help='Output results in JSON format')
    
    args = parser.parse_args()
    
    orchestrator = DatabaseMaintenanceOrchestrator()
    result = None
    
    try:
        if args.operation == 'vacuum':
            result = await orchestrator.vacuum_analyze_all_tables(verbose=args.verbose)
        
        elif args.operation == 'reindex':
            result = await orchestrator.reindex_all_tables(concurrently=not args.no_concurrent)
        
        elif args.operation == 'analyze':
            result = await orchestrator.analyze_query_performance()
        
        elif args.operation == 'health':
            result = await orchestrator.check_database_health()
        
        elif args.operation == 'cleanup':
            result = await orchestrator.cleanup_expired_data()
        
        elif args.operation == 'report':
            result = await orchestrator.generate_maintenance_report()
        
        elif args.operation == 'statistics':
            result = await orchestrator.update_table_statistics()
        
        # Output results
        if args.output_json:
            print(json.dumps(result, indent=2, default=str))
        else:
            if args.operation == 'vacuum':
                success_count = result['successful_operations']
                total_count = result['tables_processed']
                print(f"✅ VACUUM ANALYZE completed: {success_count}/{total_count} tables")
                print(f"   Duration: {result['duration_seconds']:.2f}s")
            
            elif args.operation == 'reindex':
                success_count = result['successful_operations']
                total_count = result['indexes_processed']
                print(f"✅ REINDEX completed: {success_count}/{total_count} indexes")
                print(f"   Duration: {result['duration_seconds']:.2f}s")
            
            elif args.operation == 'analyze':
                summary = result['summary']
                print(f"✅ Query performance analysis completed:")
                print(f"   Slow queries: {summary['slow_queries_analyzed']}")
                print(f"   Index suggestions: {summary['index_suggestions']}")
            
            elif args.operation == 'health':
                status = result['status']
                print(f"✅ Database health check: {status}")
                if status != 'healthy':
                    print(f"   Issues detected - check detailed output")
            
            elif args.operation == 'cleanup':
                cleanup_results = result['cleanup_results']
                total_cleaned = sum(cleanup_results.values())
                print(f"✅ Data cleanup completed: {total_cleaned} records processed")
            
            elif args.operation == 'report':
                if result.get('status') == 'failed':
                    print(f"❌ Maintenance report failed: {result.get('error')}")
                else:
                    print("✅ Comprehensive maintenance report generated")
                    if result.get('recommendations'):
                        print("   Recommendations:")
                        for rec in result['recommendations']:
                            print(f"   - {rec}")
            
            elif args.operation == 'statistics':
                if result['success']:
                    print(f"✅ Table statistics updated ({result['duration_seconds']:.2f}s)")
                else:
                    print(f"❌ Failed to update statistics: {result.get('error')}")
        
        return 0
    
    except Exception as e:
        if args.output_json:
            print(json.dumps({'error': str(e)}, indent=2))
        else:
            print(f"❌ Error: {e}")
        return 1


if __name__ == '__main__':
    exit_code = asyncio.run(main())
    sys.exit(exit_code)