"""
Data retention and cleanup procedures for compliance and storage optimization
"""

import asyncio
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, asdict
from croniter import croniter

from sqlalchemy import text, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import DataRetentionPolicy, AuditLog, SystemEvent, Plan, PlanInput, PlanOutput
from app.database.utils import db_manager, backup_manager
from app.database.audit import audit_logger, AuditSeverity, AuditAction
from app.core.config import settings

import logging
logger = logging.getLogger(__name__)


@dataclass
class RetentionExecutionResult:
    """Result of retention policy execution"""
    policy_id: uuid.UUID
    policy_name: str
    execution_start: datetime
    execution_end: datetime
    records_processed: int
    records_affected: int
    action_taken: str
    success: bool
    error_message: Optional[str] = None
    backup_created: Optional[str] = None


class DataRetentionManager:
    """Automated data retention and cleanup management"""
    
    def __init__(self):
        self.running = False
        self._scheduler_task: Optional[asyncio.Task] = None
        self.retention_policies: Dict[uuid.UUID, DataRetentionPolicy] = {}
        
        # Standard retention policies
        self.standard_policies = {
            'audit_logs_basic': {
                'name': 'Basic Audit Log Retention',
                'table_name': 'audit_logs',
                'retention_period_days': 2555,  # 7 years for compliance
                'action': 'archive',
                'conditions': {'severity': ['info', 'debug']},
                'schedule_cron': '0 2 * * 0'  # Sunday 2 AM
            },
            'audit_logs_security': {
                'name': 'Security Audit Log Retention',
                'table_name': 'audit_logs',
                'retention_period_days': 3650,  # 10 years for security events
                'action': 'archive',
                'conditions': {'compliance_category': 'security'},
                'schedule_cron': '0 3 * * 0'  # Sunday 3 AM
            },
            'system_events_resolved': {
                'name': 'Resolved System Events Cleanup',
                'table_name': 'system_events',
                'retention_period_days': 90,
                'action': 'delete',
                'conditions': {'resolved': True, 'severity': ['info', 'debug']},
                'schedule_cron': '0 1 * * *'  # Daily 1 AM
            },
            'temporary_plans': {
                'name': 'Temporary Plan Cleanup',
                'table_name': 'plans',
                'retention_period_days': 30,
                'action': 'delete',
                'conditions': {'status': 'draft', 'category': 'temporary'},
                'schedule_cron': '0 4 * * 0'  # Sunday 4 AM
            }
        }
    
    async def start_scheduler(self):
        """Start the retention policy scheduler"""
        self.running = True
        self._scheduler_task = asyncio.create_task(self._scheduler_loop())
        logger.info("Data retention scheduler started")
    
    async def stop_scheduler(self):
        """Stop the retention policy scheduler"""
        self.running = False
        if self._scheduler_task:
            self._scheduler_task.cancel()
            try:
                await self._scheduler_task
            except asyncio.CancelledError:
                pass
        logger.info("Data retention scheduler stopped")
    
    async def _scheduler_loop(self):
        """Main scheduler loop"""
        while self.running:
            try:
                await self._load_active_policies()
                await self._check_scheduled_policies()
                await asyncio.sleep(300)  # Check every 5 minutes
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in retention scheduler: {e}")
                await asyncio.sleep(300)
    
    async def _load_active_policies(self):
        """Load active retention policies from database"""
        async for session in db_manager.get_session():
            result = await session.execute(
                text("SELECT * FROM data_retention_policies WHERE is_active = true")
            )
            
            self.retention_policies.clear()
            for row in result:
                policy_data = dict(row._mapping)
                policy = DataRetentionPolicy(**policy_data)
                self.retention_policies[policy.id] = policy
    
    async def _check_scheduled_policies(self):
        """Check and execute scheduled retention policies"""
        now = datetime.now(timezone.utc)
        
        for policy in self.retention_policies.values():
            if policy.schedule_cron and self._should_execute_policy(policy, now):
                try:
                    await self.execute_retention_policy(policy.id)
                except Exception as e:
                    logger.error(f"Failed to execute retention policy {policy.name}: {e}")
    
    def _should_execute_policy(self, policy: DataRetentionPolicy, now: datetime) -> bool:
        """Check if policy should be executed now"""
        if not policy.schedule_cron:
            return False
        
        # Check if enough time has passed since last execution
        if policy.last_executed:
            cron = croniter(policy.schedule_cron, policy.last_executed)
            next_run = cron.get_next(datetime)
            return now >= next_run
        
        # First time execution
        return True
    
    async def create_retention_policy(self,
                                    name: str,
                                    table_name: str,
                                    retention_period_days: int,
                                    action: str = 'delete',
                                    conditions: Optional[Dict[str, Any]] = None,
                                    schedule_cron: Optional[str] = None,
                                    description: Optional[str] = None) -> uuid.UUID:
        """Create a new retention policy"""
        
        policy_id = uuid.uuid4()
        
        async for session in db_manager.get_session():
            policy = DataRetentionPolicy(
                id=policy_id,
                name=name,
                description=description,
                table_name=table_name,
                conditions=conditions or {},
                retention_period_days=retention_period_days,
                action=action,
                schedule_cron=schedule_cron,
                is_active=True
            )
            
            session.add(policy)
            await session.commit()
            
            await audit_logger.log_audit(
                action=AuditAction.CREATE,
                resource_type="data_retention_policy",
                resource_id=policy_id,
                new_values=asdict(policy),
                metadata={'table_name': table_name, 'retention_days': retention_period_days}
            )
            
            logger.info(f"Created retention policy: {name}")
            return policy_id
    
    async def execute_retention_policy(self, policy_id: uuid.UUID) -> RetentionExecutionResult:
        """Execute a specific retention policy"""
        
        start_time = datetime.now(timezone.utc)
        
        async for session in db_manager.get_session():
            # Load policy
            result = await session.execute(
                text("SELECT * FROM data_retention_policies WHERE id = :policy_id"),
                {'policy_id': policy_id}
            )
            policy_data = result.first()
            
            if not policy_data:
                raise ValueError(f"Retention policy {policy_id} not found")
            
            policy = DataRetentionPolicy(**dict(policy_data._mapping))
            
            try:
                # Execute based on action type
                if policy.action == 'delete':
                    result = await self._execute_delete_policy(session, policy)
                elif policy.action == 'archive':
                    result = await self._execute_archive_policy(session, policy)
                elif policy.action == 'anonymize':
                    result = await self._execute_anonymize_policy(session, policy)
                else:
                    raise ValueError(f"Unknown retention action: {policy.action}")
                
                # Update policy execution metadata
                await self._update_policy_execution(session, policy, result, start_time)
                
                # Log successful execution
                await audit_logger.log_audit(
                    action=AuditAction.EXECUTE,
                    resource_type="data_retention_policy",
                    resource_id=policy_id,
                    metadata={
                        'records_processed': result.records_processed,
                        'records_affected': result.records_affected,
                        'action': policy.action
                    }
                )
                
                logger.info(f"Executed retention policy {policy.name}: "
                           f"{result.records_affected} records {policy.action}d")
                
                return result
            
            except Exception as e:
                # Log failed execution
                await audit_logger.log_audit(
                    action=AuditAction.EXECUTE,
                    resource_type="data_retention_policy",
                    resource_id=policy_id,
                    metadata={'error': str(e), 'action': policy.action},
                    severity=AuditSeverity.ERROR
                )
                
                end_time = datetime.now(timezone.utc)
                return RetentionExecutionResult(
                    policy_id=policy_id,
                    policy_name=policy.name,
                    execution_start=start_time,
                    execution_end=end_time,
                    records_processed=0,
                    records_affected=0,
                    action_taken=policy.action,
                    success=False,
                    error_message=str(e)
                )
    
    async def _execute_delete_policy(self, session: AsyncSession, policy: DataRetentionPolicy) -> RetentionExecutionResult:
        """Execute delete retention policy"""
        
        start_time = datetime.now(timezone.utc)
        cutoff_date = start_time - timedelta(days=policy.retention_period_days)
        
        # Build WHERE clause
        where_conditions = [f"created_at < '{cutoff_date.isoformat()}'"]
        
        if policy.conditions:
            for key, value in policy.conditions.items():
                if isinstance(value, list):
                    value_list = "', '".join(str(v) for v in value)
                    where_conditions.append(f"{key} IN ('{value_list}')")
                else:
                    where_conditions.append(f"{key} = '{value}'")
        
        where_clause = " AND ".join(where_conditions)
        
        # Count records to be deleted
        count_query = f"SELECT COUNT(*) FROM {policy.table_name} WHERE {where_clause}"
        count_result = await session.execute(text(count_query))
        records_to_delete = count_result.scalar()
        
        # Execute deletion
        delete_query = f"DELETE FROM {policy.table_name} WHERE {where_clause}"
        await session.execute(text(delete_query))
        await session.commit()
        
        end_time = datetime.now(timezone.utc)
        
        return RetentionExecutionResult(
            policy_id=policy.id,
            policy_name=policy.name,
            execution_start=start_time,
            execution_end=end_time,
            records_processed=records_to_delete,
            records_affected=records_to_delete,
            action_taken='delete',
            success=True
        )
    
    async def _execute_archive_policy(self, session: AsyncSession, policy: DataRetentionPolicy) -> RetentionExecutionResult:
        """Execute archive retention policy"""
        
        start_time = datetime.now(timezone.utc)
        cutoff_date = start_time - timedelta(days=policy.retention_period_days)
        
        # Create backup before archiving
        backup_result = await backup_manager.create_full_backup(
            compress=True,
            include_schema=False,
            include_data=True
        )
        
        # Build WHERE clause
        where_conditions = [f"created_at < '{cutoff_date.isoformat()}'"]
        
        if policy.conditions:
            for key, value in policy.conditions.items():
                if isinstance(value, list):
                    value_list = "', '".join(str(v) for v in value)
                    where_conditions.append(f"{key} IN ('{value_list}')")
                else:
                    where_conditions.append(f"{key} = '{value}'")
        
        where_clause = " AND ".join(where_conditions)
        
        # Create archive table if not exists
        archive_table = f"{policy.table_name}_archive"
        await self._create_archive_table(session, policy.table_name, archive_table)
        
        # Move data to archive table
        insert_query = f"""
            INSERT INTO {archive_table} 
            SELECT * FROM {policy.table_name} 
            WHERE {where_clause}
        """
        
        insert_result = await session.execute(text(insert_query))
        records_archived = insert_result.rowcount
        
        # Delete from main table
        delete_query = f"DELETE FROM {policy.table_name} WHERE {where_clause}"
        await session.execute(text(delete_query))
        await session.commit()
        
        end_time = datetime.now(timezone.utc)
        
        return RetentionExecutionResult(
            policy_id=policy.id,
            policy_name=policy.name,
            execution_start=start_time,
            execution_end=end_time,
            records_processed=records_archived,
            records_affected=records_archived,
            action_taken='archive',
            success=True,
            backup_created=backup_result['backup_id']
        )
    
    async def _execute_anonymize_policy(self, session: AsyncSession, policy: DataRetentionPolicy) -> RetentionExecutionResult:
        """Execute anonymize retention policy"""
        
        start_time = datetime.now(timezone.utc)
        cutoff_date = start_time - timedelta(days=policy.retention_period_days)
        
        # Anonymization rules for sensitive fields
        anonymization_rules = {
            'users': {
                'email': "'anonymized_' || id || '@example.com'",
                'first_name': "'Anonymous'",
                'last_name': "'User'",
                'ip_address': "'0.0.0.0'",
                'user_agent': "'Anonymized'"
            },
            'audit_logs': {
                'ip_address': "'0.0.0.0'",
                'user_agent': "'Anonymized'",
                'old_values': "'{}'::jsonb",
                'new_values': "'{}'::jsonb"
            }
        }
        
        # Build WHERE clause
        where_conditions = [f"created_at < '{cutoff_date.isoformat()}'"]
        
        if policy.conditions:
            for key, value in policy.conditions.items():
                if isinstance(value, list):
                    value_list = "', '".join(str(v) for v in value)
                    where_conditions.append(f"{key} IN ('{value_list}')")
                else:
                    where_conditions.append(f"{key} = '{value}'")
        
        where_clause = " AND ".join(where_conditions)
        
        # Count records to be anonymized
        count_query = f"SELECT COUNT(*) FROM {policy.table_name} WHERE {where_clause}"
        count_result = await session.execute(text(count_query))
        records_to_anonymize = count_result.scalar()
        
        # Apply anonymization
        if policy.table_name in anonymization_rules:
            rules = anonymization_rules[policy.table_name]
            
            set_clauses = []
            for field, rule in rules.items():
                set_clauses.append(f"{field} = {rule}")
            
            update_query = f"""
                UPDATE {policy.table_name} 
                SET {', '.join(set_clauses)}
                WHERE {where_clause}
            """
            
            await session.execute(text(update_query))
            await session.commit()
        
        end_time = datetime.now(timezone.utc)
        
        return RetentionExecutionResult(
            policy_id=policy.id,
            policy_name=policy.name,
            execution_start=start_time,
            execution_end=end_time,
            records_processed=records_to_anonymize,
            records_affected=records_to_anonymize,
            action_taken='anonymize',
            success=True
        )
    
    async def _create_archive_table(self, session: AsyncSession, source_table: str, archive_table: str):
        """Create archive table with same structure as source table"""
        
        create_query = f"""
            CREATE TABLE IF NOT EXISTS {archive_table} (
                LIKE {source_table} INCLUDING ALL
            )
        """
        
        await session.execute(text(create_query))
        
        # Add archive-specific columns
        alter_queries = [
            f"ALTER TABLE {archive_table} ADD COLUMN IF NOT EXISTS archived_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP",
            f"ALTER TABLE {archive_table} ADD COLUMN IF NOT EXISTS archive_reason TEXT"
        ]
        
        for query in alter_queries:
            try:
                await session.execute(text(query))
            except Exception:
                # Column might already exist
                pass
    
    async def _update_policy_execution(self, session: AsyncSession, policy: DataRetentionPolicy, 
                                     result: RetentionExecutionResult, start_time: datetime):
        """Update policy execution metadata"""
        
        duration_ms = int((result.execution_end - start_time).total_seconds() * 1000)
        status = 'success' if result.success else 'failed'
        
        update_query = """
            UPDATE data_retention_policies 
            SET last_executed = :executed_at,
                records_processed = :records_processed,
                last_execution_duration_ms = :duration_ms,
                last_execution_status = :status,
                next_execution = :next_execution
            WHERE id = :policy_id
        """
        
        # Calculate next execution time
        next_execution = None
        if policy.schedule_cron:
            cron = croniter(policy.schedule_cron, start_time)
            next_execution = cron.get_next(datetime)
        
        await session.execute(text(update_query), {
            'executed_at': start_time,
            'records_processed': result.records_processed,
            'duration_ms': duration_ms,
            'status': status,
            'next_execution': next_execution,
            'policy_id': policy.id
        })
    
    async def initialize_standard_policies(self):
        """Initialize standard retention policies"""
        
        for policy_key, policy_config in self.standard_policies.items():
            try:
                await self.create_retention_policy(**policy_config)
                logger.info(f"Initialized standard retention policy: {policy_config['name']}")
            except Exception as e:
                logger.warning(f"Failed to create standard policy {policy_key}: {e}")
    
    async def get_retention_status(self) -> Dict[str, Any]:
        """Get current retention status and statistics"""
        
        async for session in db_manager.get_session():
            # Get policy statistics
            policies_query = """
                SELECT 
                    COUNT(*) as total_policies,
                    COUNT(*) FILTER (WHERE is_active = true) as active_policies,
                    COUNT(*) FILTER (WHERE last_executed IS NOT NULL) as executed_policies
                FROM data_retention_policies
            """
            
            policies_result = await session.execute(text(policies_query))
            policies_stats = dict(policies_result.first()._mapping)
            
            # Get table sizes
            table_sizes_query = """
                SELECT 
                    tablename,
                    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
                    pg_total_relation_size(schemaname||'.'||tablename) as size_bytes
                FROM pg_tables 
                WHERE schemaname = 'public'
                ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
            """
            
            table_sizes_result = await session.execute(text(table_sizes_query))
            table_sizes = [dict(row._mapping) for row in table_sizes_result]
            
            # Get recent executions
            recent_executions_query = """
                SELECT 
                    name,
                    table_name,
                    last_executed,
                    records_processed,
                    last_execution_status,
                    next_execution
                FROM data_retention_policies
                WHERE last_executed IS NOT NULL
                ORDER BY last_executed DESC
                LIMIT 10
            """
            
            recent_result = await session.execute(text(recent_executions_query))
            recent_executions = [dict(row._mapping) for row in recent_result]
            
            return {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'scheduler_running': self.running,
                'policies_statistics': policies_stats,
                'table_sizes': table_sizes,
                'recent_executions': recent_executions
            }
    
    async def cleanup_orphaned_data(self) -> Dict[str, Any]:
        """Clean up orphaned data across related tables"""
        
        cleanup_results = {}
        
        async for session in db_manager.get_session():
            # Clean up orphaned plan inputs (plans that no longer exist)
            orphaned_inputs_query = """
                DELETE FROM plan_inputs 
                WHERE plan_id NOT IN (SELECT id FROM plans)
            """
            
            inputs_result = await session.execute(text(orphaned_inputs_query))
            cleanup_results['orphaned_plan_inputs'] = inputs_result.rowcount
            
            # Clean up orphaned plan outputs
            orphaned_outputs_query = """
                DELETE FROM plan_outputs 
                WHERE plan_id NOT IN (SELECT id FROM plans)
            """
            
            outputs_result = await session.execute(text(orphaned_outputs_query))
            cleanup_results['orphaned_plan_outputs'] = outputs_result.rowcount
            
            # Clean up orphaned audit logs (users that no longer exist)
            orphaned_audit_query = """
                UPDATE audit_logs 
                SET user_id = NULL 
                WHERE user_id IS NOT NULL 
                AND user_id NOT IN (SELECT id FROM users)
            """
            
            audit_result = await session.execute(text(orphaned_audit_query))
            cleanup_results['orphaned_audit_logs'] = audit_result.rowcount
            
            await session.commit()
        
        # Log cleanup results
        await audit_logger.log_system_event(
            event_type="data_cleanup",
            event_category="maintenance",
            message="Orphaned data cleanup completed",
            severity=AuditSeverity.INFO,
            component="retention_manager",
            additional_data=cleanup_results
        )
        
        logger.info(f"Orphaned data cleanup completed: {cleanup_results}")
        return cleanup_results


# Global retention manager instance
retention_manager = DataRetentionManager()


async def init_retention_system():
    """Initialize the data retention system"""
    await retention_manager.initialize_standard_policies()
    await retention_manager.start_scheduler()
    logger.info("Data retention system initialized")


async def shutdown_retention_system():
    """Shutdown the data retention system"""
    await retention_manager.stop_scheduler()
    logger.info("Data retention system shutdown")