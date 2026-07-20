"""
Comprehensive audit logging system for compliance and security
"""

import asyncio
import uuid
import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List, Union
from contextlib import asynccontextmanager
from dataclasses import dataclass, asdict
from enum import Enum

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

from app.database.models import AuditLog, SystemEvent
from app.database.utils import db_manager
from app.core.config import settings

import logging
logger = logging.getLogger(__name__)


class AuditAction(Enum):
    """Standard audit actions"""
    CREATE = "CREATE"
    READ = "READ"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    EXECUTE = "EXECUTE"
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    ACCESS_GRANTED = "ACCESS_GRANTED"
    ACCESS_DENIED = "ACCESS_DENIED"
    EXPORT = "EXPORT"
    IMPORT = "IMPORT"


class AuditSeverity(Enum):
    """Audit severity levels"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class AuditContext:
    """Context information for audit logging"""
    user_id: Optional[uuid.UUID] = None
    session_id: Optional[str] = None
    request_id: Optional[uuid.UUID] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    endpoint: Optional[str] = None
    method: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON storage"""
        return {k: str(v) if isinstance(v, uuid.UUID) else v 
                for k, v in asdict(self).items() if v is not None}


class AuditLogger:
    """High-performance audit logging system with batching and async processing"""
    
    def __init__(self, batch_size: int = 100, flush_interval: float = 5.0):
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self._audit_queue: List[Dict[str, Any]] = []
        self._system_event_queue: List[Dict[str, Any]] = []
        self._lock = asyncio.Lock()
        self._flush_task: Optional[asyncio.Task] = None
        self._running = False
    
    async def start(self):
        """Start the audit logger background task"""
        self._running = True
        self._flush_task = asyncio.create_task(self._periodic_flush())
        logger.info("Audit logger started")
    
    async def stop(self):
        """Stop the audit logger and flush remaining entries"""
        self._running = False
        if self._flush_task:
            self._flush_task.cancel()
            try:
                await self._flush_task
            except asyncio.CancelledError:
                pass
        
        # Flush any remaining entries
        await self._flush_queues()
        logger.info("Audit logger stopped")
    
    async def log_audit(self,
                       action: Union[AuditAction, str],
                       resource_type: str,
                       resource_id: Optional[uuid.UUID] = None,
                       old_values: Optional[Dict[str, Any]] = None,
                       new_values: Optional[Dict[str, Any]] = None,
                       changed_fields: Optional[List[str]] = None,
                       context: Optional[AuditContext] = None,
                       severity: AuditSeverity = AuditSeverity.INFO,
                       metadata: Optional[Dict[str, Any]] = None,
                       compliance_category: Optional[str] = None,
                       execution_time_ms: Optional[int] = None) -> uuid.UUID:
        """Log an audit event with comprehensive details"""
        
        audit_id = uuid.uuid4()
        timestamp = datetime.now(timezone.utc)
        
        audit_entry = {
            'id': audit_id,
            'timestamp': timestamp,
            'action': action.value if isinstance(action, AuditAction) else action,
            'resource_type': resource_type,
            'resource_id': resource_id,
            'old_values': old_values,
            'new_values': new_values,
            'changed_fields': changed_fields,
            'severity': severity.value,
            'metadata': metadata or {},
            'compliance_category': compliance_category,
            'execution_time_ms': execution_time_ms,
            'user_id': context.user_id if context else None,
            'session_id': context.session_id if context else None,
            'request_id': context.request_id if context else None,
            'ip_address': context.ip_address if context else None,
            'user_agent': context.user_agent if context else None
        }
        
        # Add context metadata
        if context:
            audit_entry['metadata'].update(context.to_dict())
        
        async with self._lock:
            self._audit_queue.append(audit_entry)
            
            # Immediate flush for critical events
            if severity == AuditSeverity.CRITICAL or len(self._audit_queue) >= self.batch_size:
                await self._flush_audit_queue()
        
        return audit_id
    
    async def log_system_event(self,
                              event_type: str,
                              event_category: str,
                              message: str,
                              severity: AuditSeverity = AuditSeverity.INFO,
                              component: Optional[str] = None,
                              error_code: Optional[str] = None,
                              stack_trace: Optional[str] = None,
                              additional_data: Optional[Dict[str, Any]] = None,
                              duration_ms: Optional[int] = None,
                              memory_usage_mb: Optional[int] = None,
                              cpu_usage_percent: Optional[float] = None) -> uuid.UUID:
        """Log a system event"""
        
        event_id = uuid.uuid4()
        timestamp = datetime.now(timezone.utc)
        
        system_event = {
            'id': event_id,
            'timestamp': timestamp,
            'event_type': event_type,
            'event_category': event_category,
            'message': message,
            'severity': severity.value,
            'component': component,
            'environment': settings.ENVIRONMENT,
            'version': settings.VERSION,
            'error_code': error_code,
            'stack_trace': stack_trace,
            'additional_data': additional_data or {},
            'duration_ms': duration_ms,
            'memory_usage_mb': memory_usage_mb,
            'cpu_usage_percent': cpu_usage_percent,
            'resolved': False
        }
        
        async with self._lock:
            self._system_event_queue.append(system_event)
            
            # Immediate flush for critical events
            if severity == AuditSeverity.CRITICAL or len(self._system_event_queue) >= self.batch_size:
                await self._flush_system_event_queue()
        
        return event_id
    
    async def log_user_action(self,
                             user_id: uuid.UUID,
                             action: str,
                             resource_type: str,
                             resource_id: Optional[uuid.UUID] = None,
                             details: Optional[Dict[str, Any]] = None,
                             context: Optional[AuditContext] = None) -> uuid.UUID:
        """Convenience method for logging user actions"""
        
        return await self.log_audit(
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            context=context or AuditContext(user_id=user_id),
            metadata=details,
            compliance_category="user_action"
        )
    
    async def log_data_access(self,
                             user_id: uuid.UUID,
                             table_name: str,
                             record_id: Optional[uuid.UUID] = None,
                             access_type: str = "READ",
                             context: Optional[AuditContext] = None) -> uuid.UUID:
        """Log data access for compliance tracking"""
        
        return await self.log_audit(
            action=access_type,
            resource_type=f"data.{table_name}",
            resource_id=record_id,
            context=context or AuditContext(user_id=user_id),
            compliance_category="data_access"
        )
    
    async def log_security_event(self,
                                event_type: str,
                                user_id: Optional[uuid.UUID] = None,
                                details: Optional[Dict[str, Any]] = None,
                                severity: AuditSeverity = AuditSeverity.WARNING,
                                context: Optional[AuditContext] = None) -> uuid.UUID:
        """Log security-related events"""
        
        return await self.log_audit(
            action=event_type,
            resource_type="security",
            context=context or AuditContext(user_id=user_id),
            severity=severity,
            metadata=details,
            compliance_category="security"
        )
    
    async def _periodic_flush(self):
        """Periodically flush audit queues"""
        while self._running:
            try:
                await asyncio.sleep(self.flush_interval)
                async with self._lock:
                    if self._audit_queue or self._system_event_queue:
                        await self._flush_queues()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in periodic flush: {e}")
    
    async def _flush_queues(self):
        """Flush both audit and system event queues"""
        await self._flush_audit_queue()
        await self._flush_system_event_queue()
    
    async def _flush_audit_queue(self):
        """Flush audit queue to database"""
        if not self._audit_queue:
            return
        
        entries_to_flush = self._audit_queue[:]
        self._audit_queue.clear()
        
        try:
            async for session in db_manager.get_session():
                for entry in entries_to_flush:
                    audit_log = AuditLog(**entry)
                    session.add(audit_log)
                
                await session.commit()
                logger.debug(f"Flushed {len(entries_to_flush)} audit entries")
        
        except Exception as e:
            logger.error(f"Failed to flush audit queue: {e}")
            # Re-add entries to queue for retry
            self._audit_queue.extend(entries_to_flush)
    
    async def _flush_system_event_queue(self):
        """Flush system event queue to database"""
        if not self._system_event_queue:
            return
        
        events_to_flush = self._system_event_queue[:]
        self._system_event_queue.clear()
        
        try:
            async for session in db_manager.get_session():
                for event in events_to_flush:
                    system_event = SystemEvent(**event)
                    session.add(system_event)
                
                await session.commit()
                logger.debug(f"Flushed {len(events_to_flush)} system events")
        
        except Exception as e:
            logger.error(f"Failed to flush system event queue: {e}")
            # Re-add events to queue for retry
            self._system_event_queue.extend(events_to_flush)


class AuditQueryBuilder:
    """Builder for complex audit queries with filtering and aggregation"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self._filters = []
        self._order_by = []
        self._limit = None
        self._offset = None
    
    def filter_by_user(self, user_id: uuid.UUID) -> 'AuditQueryBuilder':
        """Filter by user ID"""
        self._filters.append(f"user_id = '{user_id}'")
        return self
    
    def filter_by_action(self, action: Union[AuditAction, str]) -> 'AuditQueryBuilder':
        """Filter by action type"""
        action_value = action.value if isinstance(action, AuditAction) else action
        self._filters.append(f"action = '{action_value}'")
        return self
    
    def filter_by_resource(self, resource_type: str, resource_id: Optional[uuid.UUID] = None) -> 'AuditQueryBuilder':
        """Filter by resource type and optionally resource ID"""
        self._filters.append(f"resource_type = '{resource_type}'")
        if resource_id:
            self._filters.append(f"resource_id = '{resource_id}'")
        return self
    
    def filter_by_date_range(self, start_date: datetime, end_date: datetime) -> 'AuditQueryBuilder':
        """Filter by date range"""
        self._filters.append(f"timestamp >= '{start_date.isoformat()}'")
        self._filters.append(f"timestamp <= '{end_date.isoformat()}'")
        return self
    
    def filter_by_severity(self, severity: AuditSeverity) -> 'AuditQueryBuilder':
        """Filter by severity level"""
        self._filters.append(f"severity = '{severity.value}'")
        return self
    
    def order_by_timestamp(self, descending: bool = True) -> 'AuditQueryBuilder':
        """Order by timestamp"""
        direction = "DESC" if descending else "ASC"
        self._order_by.append(f"timestamp {direction}")
        return self
    
    def limit(self, count: int) -> 'AuditQueryBuilder':
        """Limit number of results"""
        self._limit = count
        return self
    
    def offset(self, count: int) -> 'AuditQueryBuilder':
        """Set result offset"""
        self._offset = count
        return self
    
    async def execute(self) -> List[Dict[str, Any]]:
        """Execute the query and return results"""
        query_parts = ["SELECT * FROM audit_logs"]
        
        if self._filters:
            query_parts.append("WHERE " + " AND ".join(self._filters))
        
        if self._order_by:
            query_parts.append("ORDER BY " + ", ".join(self._order_by))
        
        if self._limit:
            query_parts.append(f"LIMIT {self._limit}")
        
        if self._offset:
            query_parts.append(f"OFFSET {self._offset}")
        
        query = " ".join(query_parts)
        
        result = await self.session.execute(text(query))
        return [dict(row._mapping) for row in result]
    
    async def count(self) -> int:
        """Get count of matching records"""
        query_parts = ["SELECT COUNT(*) as count FROM audit_logs"]
        
        if self._filters:
            query_parts.append("WHERE " + " AND ".join(self._filters))
        
        query = " ".join(query_parts)
        
        result = await self.session.execute(text(query))
        return result.scalar()


class ComplianceReporter:
    """Generate compliance reports from audit data"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def generate_user_activity_report(self,
                                          user_id: uuid.UUID,
                                          start_date: datetime,
                                          end_date: datetime) -> Dict[str, Any]:
        """Generate comprehensive user activity report"""
        
        query_builder = AuditQueryBuilder(self.session)
        activities = await (query_builder
                           .filter_by_user(user_id)
                           .filter_by_date_range(start_date, end_date)
                           .order_by_timestamp()
                           .execute())
        
        # Aggregate statistics
        action_counts = {}
        resource_counts = {}
        hourly_activity = {}
        
        for activity in activities:
            # Count by action
            action = activity['action']
            action_counts[action] = action_counts.get(action, 0) + 1
            
            # Count by resource type
            resource_type = activity['resource_type']
            resource_counts[resource_type] = resource_counts.get(resource_type, 0) + 1
            
            # Count by hour
            hour = activity['timestamp'].hour
            hourly_activity[hour] = hourly_activity.get(hour, 0) + 1
        
        return {
            'user_id': str(user_id),
            'report_period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            },
            'total_activities': len(activities),
            'action_breakdown': action_counts,
            'resource_breakdown': resource_counts,
            'hourly_activity': hourly_activity,
            'activities': activities[:100],  # Include first 100 detailed activities
            'generated_at': datetime.now(timezone.utc).isoformat()
        }
    
    async def generate_security_report(self,
                                     start_date: datetime,
                                     end_date: datetime) -> Dict[str, Any]:
        """Generate security events report"""
        
        query_builder = AuditQueryBuilder(self.session)
        security_events = await (query_builder
                                .filter_by_resource("security", None)
                                .filter_by_date_range(start_date, end_date)
                                .order_by_timestamp()
                                .execute())
        
        # Categorize security events
        login_attempts = []
        access_violations = []
        suspicious_activities = []
        
        for event in security_events:
            action = event['action']
            if action in ['LOGIN', 'LOGOUT']:
                login_attempts.append(event)
            elif action == 'ACCESS_DENIED':
                access_violations.append(event)
            else:
                suspicious_activities.append(event)
        
        return {
            'report_period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            },
            'summary': {
                'total_security_events': len(security_events),
                'login_attempts': len(login_attempts),
                'access_violations': len(access_violations),
                'suspicious_activities': len(suspicious_activities)
            },
            'login_attempts': login_attempts,
            'access_violations': access_violations,
            'suspicious_activities': suspicious_activities,
            'generated_at': datetime.now(timezone.utc).isoformat()
        }
    
    async def generate_data_access_report(self,
                                        table_name: str,
                                        start_date: datetime,
                                        end_date: datetime) -> Dict[str, Any]:
        """Generate data access compliance report"""
        
        query_builder = AuditQueryBuilder(self.session)
        data_access_events = await (query_builder
                                   .filter_by_resource(f"data.{table_name}", None)
                                   .filter_by_date_range(start_date, end_date)
                                   .order_by_timestamp()
                                   .execute())
        
        # Analyze access patterns
        user_access = {}
        access_types = {}
        
        for event in data_access_events:
            user_id = event['user_id']
            action = event['action']
            
            if user_id:
                if user_id not in user_access:
                    user_access[user_id] = {'reads': 0, 'writes': 0, 'deletes': 0}
                
                if action == 'READ':
                    user_access[user_id]['reads'] += 1
                elif action in ['CREATE', 'UPDATE']:
                    user_access[user_id]['writes'] += 1
                elif action == 'DELETE':
                    user_access[user_id]['deletes'] += 1
            
            access_types[action] = access_types.get(action, 0) + 1
        
        return {
            'table_name': table_name,
            'report_period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            },
            'summary': {
                'total_access_events': len(data_access_events),
                'unique_users': len(user_access),
                'access_type_breakdown': access_types
            },
            'user_access_summary': user_access,
            'detailed_events': data_access_events[:1000],  # Include first 1000 events
            'generated_at': datetime.now(timezone.utc).isoformat()
        }


# Global audit logger instance
audit_logger = AuditLogger()


@asynccontextmanager
async def audit_context(context: AuditContext):
    """Context manager for audit logging"""
    # Store context in thread-local or async context
    yield context


async def init_audit_system():
    """Initialize the audit system"""
    await audit_logger.start()
    logger.info("Audit system initialized")


async def shutdown_audit_system():
    """Shutdown the audit system"""
    await audit_logger.stop()
    logger.info("Audit system shutdown")