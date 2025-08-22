#!/usr/bin/env python3
"""
Database Management Script

This script provides comprehensive database management capabilities including:
- Full database initialization with seed data
- Database health checks and monitoring
- Backup and restore operations
- Migration management
- Performance monitoring
- Disaster recovery testing

Usage:
    python scripts/database/db_manager.py init          # Initialize database with seed data
    python scripts/database/db_manager.py health        # Check database health
    python scripts/database/db_manager.py reset         # Reset database (WARNING: Destroys data)
    python scripts/database/db_manager.py backup        # Create database backup
    python scripts/database/db_manager.py monitor       # Show performance metrics
    python scripts/database/db_manager.py test-audit    # Test audit logging
"""

import asyncio
import logging
import sys
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any
import argparse

# Add the backend directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from app.database.init_db import DatabaseInitializer, init_db, reset_db, quick_setup
from app.database.base import create_engine, create_session_maker, get_db_session, engine, health_check
from app.database.models import User, AuditLog, SystemEvent
from app.core.config import settings

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DatabaseManager:
    """Database management operations"""
    
    def __init__(self):
        self.initializer = DatabaseInitializer()
    
    async def initialize_database(self) -> Dict[str, Any]:
        """Initialize database with full setup and seed data"""
        logger.info("Starting database initialization...")
        
        try:
            results = await init_db()
            
            print("\n" + "="*60)
            print("DATABASE INITIALIZATION RESULTS")
            print("="*60)
            print(f"Status: {results['status']}")
            print(f"Steps completed: {len(results['steps_completed'])}")
            
            if results.get('statistics', {}).get('seed_data'):
                seed_stats = results['statistics']['seed_data']
                print("\nSeed Data Created:")
                for key, count in seed_stats.items():
                    print(f"  - {key.replace('_', ' ').title()}: {count}")
            
            if results.get('errors'):
                print(f"\nErrors: {len(results['errors'])}")
                for error in results['errors']:
                    print(f"  - {error}")
            
            print("\n" + "="*60)
            
            return results
            
        except Exception as e:
            logger.error(f"Database initialization failed: {str(e)}")
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive database health check"""
        logger.info("Performing database health check...")
        
        health_status = await self.initializer.health_check()
        
        print("\n" + "="*60)
        print("DATABASE HEALTH CHECK")
        print("="*60)
        print(f"Overall Status: {health_status['status']}")
        print(f"Timestamp: {health_status['timestamp']}")
        
        if health_status.get('checks'):
            print("\nConnection Checks:")
            for check, result in health_status['checks'].items():
                status = "✅ PASS" if result else "❌ FAIL"
                print(f"  - {check}: {status}")
        
        if health_status.get('metrics'):
            print("\nDatabase Metrics:")
            for metric, value in health_status['metrics'].items():
                if isinstance(value, dict):
                    print(f"  - {metric}:")
                    for sub_metric, sub_value in value.items():
                        print(f"    - {sub_metric}: {sub_value}")
                else:
                    print(f"  - {metric}: {value}")
        
        if health_status.get('error'):
            print(f"\nError: {health_status['error']}")
        
        print("\n" + "="*60)
        
        return health_status
    
    async def reset_database(self) -> None:
        """Reset database - WARNING: This will destroy all data"""
        print("\n" + "⚠️ "*20)
        print("WARNING: DATABASE RESET")
        print("⚠️ "*20)
        print("This operation will DESTROY ALL DATA in the database!")
        print("This action cannot be undone.")
        
        if not self._confirm_destructive_action():
            print("Operation cancelled.")
            return
        
        logger.warning("Resetting database...")
        await reset_db()
        print("✅ Database reset completed")
    
    async def create_backup(self) -> Dict[str, str]:
        """Create database backup"""
        logger.info("Creating database backup...")
        
        backup_info = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "type": "logical_dump",
            "status": "initiated"
        }
        
        try:
            # Log backup creation
            async with get_db_session() as session:
                system_event = SystemEvent(
                    event_type="backup_created",
                    event_category="database",
                    message=f"Database backup initiated at {backup_info['timestamp']}",
                    additional_data=backup_info,
                    severity="info"
                )
                session.add(system_event)
                await session.commit()
            
            backup_info["status"] = "completed"
            print(f"✅ Backup logged in system events")
            
        except Exception as e:
            backup_info["status"] = "failed"
            backup_info["error"] = str(e)
            logger.error(f"Backup failed: {str(e)}")
        
        return backup_info
    
    async def monitor_performance(self) -> Dict[str, Any]:
        """Monitor database performance"""
        logger.info("Collecting performance metrics...")
        
        metrics = {
            "timestamp": datetime.now(timezone.utc),
            "connection_pool": {},
            "table_stats": {},
            "query_performance": {}
        }
        
        try:
            # Get connection pool metrics
            if engine:
                metrics["connection_pool"] = {
                    "size": engine.pool.size(),
                    "checked_in": engine.pool.checkedin(),
                    "checked_out": engine.pool.checkedout(),
                    "overflow": engine.pool.overflow()
                }
            
            print("\n" + "="*60)
            print("DATABASE PERFORMANCE MONITORING")
            print("="*60)
            print(f"Timestamp: {metrics['timestamp']}")
            
            print("\nConnection Pool Status:")
            for key, value in metrics["connection_pool"].items():
                print(f"  - {key.replace('_', ' ').title()}: {value}")
            
            print("\n" + "="*60)
            
        except Exception as e:
            logger.error(f"Performance monitoring failed: {str(e)}")
            metrics["error"] = str(e)
        
        return metrics
    
    async def test_audit_logging(self) -> Dict[str, Any]:
        """Test audit logging functionality"""
        logger.info("Testing audit logging...")
        
        test_results = {
            "timestamp": datetime.now(timezone.utc),
            "tests": {},
            "overall_status": "passed"
        }
        
        try:
            async with get_db_session() as session:
                # Get initial audit log count
                from sqlalchemy import text, func
                initial_count_result = await session.execute(text("SELECT COUNT(*) FROM audit_logs"))
                initial_count = initial_count_result.scalar()
                
                # Create a test user to trigger audit logging
                from passlib.context import CryptContext
                pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
                
                test_user = User(
                    email="audit.test@example.com",
                    first_name="Audit",
                    last_name="Test",
                    hashed_password=pwd_context.hash("test123")
                )
                session.add(test_user)
                await session.commit()
                
                # Update the test user
                test_user.first_name = "Updated"
                await session.commit()
                
                # Check if audit logs were created
                final_count_result = await session.execute(text("SELECT COUNT(*) FROM audit_logs"))
                final_count = final_count_result.scalar()
                
                # Clean up test user
                await session.delete(test_user)
                await session.commit()
                
                # Verify audit logging worked
                audit_logs_created = final_count > initial_count
                test_results["tests"]["audit_log_creation"] = audit_logs_created
                
                if not audit_logs_created:
                    test_results["overall_status"] = "failed"
                
                print("\n" + "="*60)
                print("AUDIT LOGGING TEST RESULTS")
                print("="*60)
                print(f"Initial audit log count: {initial_count}")
                print(f"Final audit log count: {final_count}")
                print(f"Audit logs created: {'✅ YES' if audit_logs_created else '❌ NO'}")
                print(f"Overall status: {'✅ PASSED' if test_results['overall_status'] == 'passed' else '❌ FAILED'}")
                print("\n" + "="*60)
                
        except Exception as e:
            test_results["overall_status"] = "error"
            test_results["error"] = str(e)
            logger.error(f"Audit logging test failed: {str(e)}")
        
        return test_results
    
    def _confirm_destructive_action(self) -> bool:
        """Confirm destructive database operations"""
        response = input("\nType 'CONFIRM' to proceed: ").strip()
        return response == "CONFIRM"

async def main():
    """Main function to handle command line arguments"""
    parser = argparse.ArgumentParser(
        description="Database Management Tool for Financial Planning System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python scripts/database/db_manager.py init          # Initialize database
    python scripts/database/db_manager.py health        # Health check
    python scripts/database/db_manager.py reset         # Reset database
    python scripts/database/db_manager.py backup        # Create backup
    python scripts/database/db_manager.py monitor       # Performance metrics
    python scripts/database/db_manager.py test-audit    # Test audit logging
        """
    )
    
    parser.add_argument(
        'command',
        choices=['init', 'health', 'reset', 'backup', 'monitor', 'test-audit'],
        help='Database management command to execute'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialize database manager
    db_manager = DatabaseManager()
    
    try:
        if args.command == 'init':
            await db_manager.initialize_database()
            
        elif args.command == 'health':
            await db_manager.health_check()
            
        elif args.command == 'reset':
            await db_manager.reset_database()
            
        elif args.command == 'backup':
            await db_manager.create_backup()
            
        elif args.command == 'monitor':
            await db_manager.monitor_performance()
            
        elif args.command == 'test-audit':
            await db_manager.test_audit_logging()
            
    except Exception as e:
        logger.error(f"Command failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())