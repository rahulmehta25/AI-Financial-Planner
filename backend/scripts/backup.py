#!/usr/bin/env python3
"""
Production backup script for Financial Planning System
Implements automated backup procedures with disaster recovery capabilities
"""

import asyncio
import argparse
import sys
import os
from pathlib import Path
from datetime import datetime, timezone
import json
import logging

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database.utils import backup_manager, db_manager
from app.database.audit import audit_logger, AuditSeverity
from app.core.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/financial_planning/backup.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class BackupOrchestrator:
    """Orchestrates comprehensive backup procedures"""
    
    def __init__(self):
        self.backup_config = {
            'full_backup_schedule': '0 2 * * 0',  # Sunday 2 AM
            'incremental_schedule': '0 */6 * * *',  # Every 6 hours
            'retention_days': 30,
            'offsite_enabled': False,
            'compression_enabled': True,
            'encryption_enabled': False
        }
    
    async def perform_full_backup(self, 
                                 compress: bool = True,
                                 verify: bool = True,
                                 cleanup_old: bool = True) -> dict:
        """Perform complete database backup with verification"""
        
        start_time = datetime.now(timezone.utc)
        logger.info("Starting full database backup")
        
        try:
            # Initialize database connection
            await db_manager.initialize()
            await audit_logger.start()
            
            # Perform backup
            backup_result = await backup_manager.create_full_backup(
                compress=compress,
                include_schema=True,
                include_data=True
            )
            
            # Verify backup integrity
            if verify:
                verification_result = await backup_manager.verify_backup(
                    backup_result['file_path']
                )
                backup_result['verification'] = verification_result
                
                if not verification_result['valid']:
                    raise Exception(f"Backup verification failed: {verification_result.get('error')}")
            
            # Cleanup old backups
            if cleanup_old:
                cleanup_result = await backup_manager.cleanup_old_backups(
                    retention_days=self.backup_config['retention_days']
                )
                backup_result['cleanup'] = cleanup_result
            
            # Log successful backup
            await audit_logger.log_system_event(
                event_type="backup_completed",
                event_category="maintenance",
                message="Full database backup completed successfully",
                severity=AuditSeverity.INFO,
                component="backup_orchestrator",
                additional_data={
                    'backup_id': backup_result['backup_id'],
                    'file_size': backup_result['file_size_human'],
                    'duration_seconds': backup_result['duration_seconds']
                }
            )
            
            execution_time = (datetime.now(timezone.utc) - start_time).total_seconds()
            backup_result['total_execution_time'] = execution_time
            
            logger.info(f"Full backup completed successfully: {backup_result['backup_id']}")
            return backup_result
        
        except Exception as e:
            logger.error(f"Full backup failed: {e}")
            
            # Log backup failure
            await audit_logger.log_system_event(
                event_type="backup_failed",
                event_category="maintenance", 
                message=f"Full database backup failed: {str(e)}",
                severity=AuditSeverity.ERROR,
                component="backup_orchestrator",
                stack_trace=str(e)
            )
            
            raise
        
        finally:
            await audit_logger.stop()
            await db_manager.close()
    
    async def perform_incremental_backup(self, base_backup_id: str) -> dict:
        """Perform incremental backup based on base backup"""
        
        start_time = datetime.now(timezone.utc)
        logger.info(f"Starting incremental backup based on {base_backup_id}")
        
        try:
            await db_manager.initialize()
            await audit_logger.start()
            
            backup_result = await backup_manager.create_incremental_backup(base_backup_id)
            
            await audit_logger.log_system_event(
                event_type="incremental_backup_completed",
                event_category="maintenance",
                message="Incremental backup completed successfully",
                severity=AuditSeverity.INFO,
                component="backup_orchestrator",
                additional_data={
                    'backup_id': backup_result['backup_id'],
                    'base_backup_id': base_backup_id
                }
            )
            
            execution_time = (datetime.now(timezone.utc) - start_time).total_seconds()
            backup_result['total_execution_time'] = execution_time
            
            logger.info(f"Incremental backup completed: {backup_result['backup_id']}")
            return backup_result
        
        except Exception as e:
            logger.error(f"Incremental backup failed: {e}")
            
            await audit_logger.log_system_event(
                event_type="incremental_backup_failed",
                event_category="maintenance",
                message=f"Incremental backup failed: {str(e)}",
                severity=AuditSeverity.ERROR,
                component="backup_orchestrator"
            )
            
            raise
        
        finally:
            await audit_logger.stop()
            await db_manager.close()
    
    async def list_available_backups(self) -> list:
        """List all available backups with metadata"""
        
        await db_manager.initialize()
        
        try:
            backups = await backup_manager.list_backups()
            return backups
        finally:
            await db_manager.close()
    
    async def restore_from_backup(self, 
                                backup_file: str, 
                                target_db: str = None,
                                dry_run: bool = False) -> dict:
        """Restore database from backup with safety checks"""
        
        start_time = datetime.now(timezone.utc)
        logger.info(f"Starting database restore from {backup_file}")
        
        try:
            await db_manager.initialize()
            await audit_logger.start()
            
            # Verify backup before restore
            verification = await backup_manager.verify_backup(backup_file)
            if not verification['valid']:
                raise Exception(f"Backup verification failed: {verification.get('error')}")
            
            if dry_run:
                logger.info("Dry run mode - restore would be performed with verified backup")
                return {
                    'dry_run': True,
                    'backup_file': backup_file,
                    'verification': verification,
                    'target_database': target_db or settings.POSTGRES_DB
                }
            
            # Create backup of current database before restore
            pre_restore_backup = await backup_manager.create_full_backup(
                compress=True,
                include_schema=True,
                include_data=True
            )
            
            # Perform restore
            restore_result = await backup_manager.restore_backup(backup_file, target_db)
            restore_result['pre_restore_backup'] = pre_restore_backup
            
            await audit_logger.log_system_event(
                event_type="database_restored",
                event_category="maintenance",
                message="Database restored from backup",
                severity=AuditSeverity.INFO,
                component="backup_orchestrator",
                additional_data={
                    'backup_file': backup_file,
                    'target_database': target_db or settings.POSTGRES_DB,
                    'pre_restore_backup': pre_restore_backup['backup_id']
                }
            )
            
            execution_time = (datetime.now(timezone.utc) - start_time).total_seconds()
            restore_result['total_execution_time'] = execution_time
            
            logger.info("Database restore completed successfully")
            return restore_result
        
        except Exception as e:
            logger.error(f"Database restore failed: {e}")
            
            await audit_logger.log_system_event(
                event_type="database_restore_failed",
                event_category="maintenance",
                message=f"Database restore failed: {str(e)}",
                severity=AuditSeverity.ERROR,
                component="backup_orchestrator"
            )
            
            raise
        
        finally:
            await audit_logger.stop()
            await db_manager.close()
    
    async def test_disaster_recovery(self) -> dict:
        """Test complete disaster recovery procedure"""
        
        logger.info("Starting disaster recovery test")
        
        try:
            await db_manager.initialize()
            
            # 1. Create test backup
            test_backup = await backup_manager.create_full_backup(compress=True)
            
            # 2. Verify backup
            verification = await backup_manager.verify_backup(test_backup['file_path'])
            
            # 3. Test restore (dry run)
            restore_test = await self.restore_from_backup(
                test_backup['file_path'],
                dry_run=True
            )
            
            # 4. Check database health
            health_check = await db_manager.health_check()
            
            test_results = {
                'test_timestamp': datetime.now(timezone.utc).isoformat(),
                'backup_test': {
                    'success': True,
                    'backup_id': test_backup['backup_id'],
                    'file_size': test_backup['file_size_human']
                },
                'verification_test': {
                    'success': verification['valid'],
                    'details': verification
                },
                'restore_test': {
                    'success': True,
                    'details': restore_test
                },
                'health_check': health_check,
                'overall_success': verification['valid'] and health_check['status'] == 'healthy'
            }
            
            logger.info(f"Disaster recovery test completed: {test_results['overall_success']}")
            return test_results
        
        except Exception as e:
            logger.error(f"Disaster recovery test failed: {e}")
            return {
                'test_timestamp': datetime.now(timezone.utc).isoformat(),
                'overall_success': False,
                'error': str(e)
            }
        
        finally:
            await db_manager.close()


async def main():
    """Main backup script entry point"""
    
    parser = argparse.ArgumentParser(description='Financial Planning System Backup Tool')
    parser.add_argument('action', choices=['full', 'incremental', 'list', 'restore', 'test-dr'],
                       help='Backup action to perform')
    parser.add_argument('--base-backup', help='Base backup ID for incremental backup')
    parser.add_argument('--backup-file', help='Backup file path for restore')
    parser.add_argument('--target-db', help='Target database for restore')
    parser.add_argument('--dry-run', action='store_true', help='Perform dry run without actual changes')
    parser.add_argument('--no-verify', action='store_true', help='Skip backup verification')
    parser.add_argument('--no-cleanup', action='store_true', help='Skip cleanup of old backups')
    parser.add_argument('--output-json', action='store_true', help='Output results in JSON format')
    
    args = parser.parse_args()
    
    orchestrator = BackupOrchestrator()
    result = None
    
    try:
        if args.action == 'full':
            result = await orchestrator.perform_full_backup(
                verify=not args.no_verify,
                cleanup_old=not args.no_cleanup
            )
        
        elif args.action == 'incremental':
            if not args.base_backup:
                print("Error: --base-backup required for incremental backup")
                return 1
            result = await orchestrator.perform_incremental_backup(args.base_backup)
        
        elif args.action == 'list':
            result = await orchestrator.list_available_backups()
        
        elif args.action == 'restore':
            if not args.backup_file:
                print("Error: --backup-file required for restore")
                return 1
            result = await orchestrator.restore_from_backup(
                args.backup_file,
                args.target_db,
                args.dry_run
            )
        
        elif args.action == 'test-dr':
            result = await orchestrator.test_disaster_recovery()
        
        # Output results
        if args.output_json:
            print(json.dumps(result, indent=2, default=str))
        else:
            if args.action == 'full':
                print(f"✅ Full backup completed: {result['backup_id']}")
                print(f"   File: {result['file_path']}")
                print(f"   Size: {result['file_size_human']}")
                print(f"   Duration: {result['duration_seconds']:.2f}s")
            
            elif args.action == 'incremental':
                print(f"✅ Incremental backup completed: {result['backup_id']}")
                print(f"   Base: {result['base_backup_id']}")
            
            elif args.action == 'list':
                print("Available backups:")
                for backup in result:
                    print(f"  {backup['backup_id']} - {backup['file_size_human']} - {backup['timestamp']}")
            
            elif args.action == 'restore':
                if args.dry_run:
                    print("✅ Dry run completed - restore would succeed")
                else:
                    print(f"✅ Database restored from {args.backup_file}")
            
            elif args.action == 'test-dr':
                if result['overall_success']:
                    print("✅ Disaster recovery test passed")
                else:
                    print("❌ Disaster recovery test failed")
                    if 'error' in result:
                        print(f"   Error: {result['error']}")
        
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