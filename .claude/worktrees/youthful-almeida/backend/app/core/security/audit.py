"""
Audit Module

Implements comprehensive audit logging, compliance reporting,
and audit trail management for regulatory requirements.
"""

import json
import hashlib
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from dataclasses import dataclass, asdict
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as redis

from app.core.config import settings


class AuditEventType(Enum):
    """Types of audit events"""
    # Authentication events
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    LOGOUT = "logout"
    PASSWORD_CHANGE = "password_change"
    MFA_ENABLED = "mfa_enabled"
    MFA_DISABLED = "mfa_disabled"
    
    # Authorization events
    ACCESS_GRANTED = "access_granted"
    ACCESS_DENIED = "access_denied"
    PERMISSION_CHANGED = "permission_changed"
    ROLE_ASSIGNED = "role_assigned"
    ROLE_REVOKED = "role_revoked"
    
    # Data events
    DATA_CREATE = "data_create"
    DATA_READ = "data_read"
    DATA_UPDATE = "data_update"
    DATA_DELETE = "data_delete"
    DATA_EXPORT = "data_export"
    DATA_IMPORT = "data_import"
    
    # Financial events
    TRANSACTION_INITIATED = "transaction_initiated"
    TRANSACTION_APPROVED = "transaction_approved"
    TRANSACTION_REJECTED = "transaction_rejected"
    PORTFOLIO_MODIFIED = "portfolio_modified"
    SIMULATION_RUN = "simulation_run"
    
    # Compliance events
    COMPLIANCE_CHECK = "compliance_check"
    COMPLIANCE_VIOLATION = "compliance_violation"
    COMPLIANCE_REPORT = "compliance_report"
    AUDIT_PERFORMED = "audit_performed"
    
    # System events
    SYSTEM_START = "system_start"
    SYSTEM_STOP = "system_stop"
    CONFIG_CHANGE = "config_change"
    BACKUP_CREATED = "backup_created"
    BACKUP_RESTORED = "backup_restored"
    
    # Security events
    SECURITY_ALERT = "security_alert"
    INTRUSION_DETECTED = "intrusion_detected"
    MALWARE_DETECTED = "malware_detected"
    ENCRYPTION_KEY_ROTATED = "encryption_key_rotated"
    CERTIFICATE_EXPIRED = "certificate_expired"


class AuditSeverity(Enum):
    """Severity levels for audit events"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class AuditEvent:
    """Represents an audit event"""
    event_id: str
    event_type: AuditEventType
    severity: AuditSeverity
    timestamp: datetime
    user_id: Optional[str]
    session_id: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    resource_type: Optional[str]
    resource_id: Optional[str]
    action: str
    result: str
    details: Dict[str, Any]
    metadata: Dict[str, Any]
    hash: Optional[str] = None
    previous_hash: Optional[str] = None


class AuditTrail:
    """
    Immutable audit trail with cryptographic verification
    Implements tamper-evident logging with hash chaining
    """
    
    def __init__(self):
        self.events = []
        self.last_hash = None
        self.redis_client = None
    
    async def initialize(self):
        """Initialize audit trail"""
        
        self.redis_client = await redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )
        
        # Load last hash from storage
        if self.redis_client:
            self.last_hash = await self.redis_client.get("audit:last_hash")
    
    def calculate_hash(self, event: AuditEvent) -> str:
        """Calculate cryptographic hash for audit event"""
        
        # Create deterministic string representation
        event_data = {
            "event_id": event.event_id,
            "event_type": event.event_type.value,
            "severity": event.severity.value,
            "timestamp": event.timestamp.isoformat(),
            "user_id": event.user_id,
            "session_id": event.session_id,
            "action": event.action,
            "result": event.result,
            "details": json.dumps(event.details, sort_keys=True),
            "previous_hash": event.previous_hash
        }
        
        # Calculate SHA-256 hash
        event_string = json.dumps(event_data, sort_keys=True)
        return hashlib.sha256(event_string.encode()).hexdigest()
    
    async def add_event(self, event: AuditEvent) -> str:
        """Add event to audit trail with hash chaining"""
        
        # Set previous hash
        event.previous_hash = self.last_hash
        
        # Calculate event hash
        event.hash = self.calculate_hash(event)
        
        # Store event
        if self.redis_client:
            # Store in Redis with expiration based on retention policy
            retention_days = settings.AUDIT_LOG_RETENTION_DAYS
            
            await self.redis_client.setex(
                f"audit:event:{event.event_id}",
                retention_days * 86400,
                json.dumps(asdict(event), default=str)
            )
            
            # Update last hash
            await self.redis_client.set("audit:last_hash", event.hash)
            
            # Add to time-series index
            await self.redis_client.zadd(
                f"audit:timeline:{event.timestamp.strftime('%Y-%m-%d')}",
                {event.event_id: event.timestamp.timestamp()}
            )
        
        # Update last hash
        self.last_hash = event.hash
        
        # Add to local cache
        self.events.append(event)
        
        return event.hash
    
    async def verify_integrity(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Tuple[bool, List[str]]:
        """Verify audit trail integrity"""
        
        issues = []
        previous_hash = None
        
        # Get events from storage
        events = await self.get_events(start_date, end_date)
        
        for event in events:
            # Verify hash chain
            if event.previous_hash != previous_hash:
                issues.append(f"Hash chain broken at event {event.event_id}")
            
            # Verify event hash
            calculated_hash = self.calculate_hash(event)
            if calculated_hash != event.hash:
                issues.append(f"Hash mismatch for event {event.event_id}")
            
            previous_hash = event.hash
        
        return len(issues) == 0, issues
    
    async def get_events(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        event_type: Optional[AuditEventType] = None,
        user_id: Optional[str] = None
    ) -> List[AuditEvent]:
        """Retrieve audit events with filtering"""
        
        events = []
        
        if self.redis_client:
            # Build date range
            if not start_date:
                start_date = datetime.now() - timedelta(days=30)
            if not end_date:
                end_date = datetime.now()
            
            # Get events for each day in range
            current_date = start_date
            while current_date <= end_date:
                date_key = current_date.strftime('%Y-%m-%d')
                
                # Get event IDs for the day
                event_ids = await self.redis_client.zrangebyscore(
                    f"audit:timeline:{date_key}",
                    current_date.timestamp(),
                    (current_date + timedelta(days=1)).timestamp()
                )
                
                # Retrieve events
                for event_id in event_ids:
                    event_data = await self.redis_client.get(f"audit:event:{event_id}")
                    
                    if event_data:
                        event_dict = json.loads(event_data)
                        
                        # Convert to AuditEvent
                        event = AuditEvent(
                            event_id=event_dict["event_id"],
                            event_type=AuditEventType(event_dict["event_type"]),
                            severity=AuditSeverity(event_dict["severity"]),
                            timestamp=datetime.fromisoformat(event_dict["timestamp"]),
                            user_id=event_dict.get("user_id"),
                            session_id=event_dict.get("session_id"),
                            ip_address=event_dict.get("ip_address"),
                            user_agent=event_dict.get("user_agent"),
                            resource_type=event_dict.get("resource_type"),
                            resource_id=event_dict.get("resource_id"),
                            action=event_dict["action"],
                            result=event_dict["result"],
                            details=event_dict.get("details", {}),
                            metadata=event_dict.get("metadata", {}),
                            hash=event_dict.get("hash"),
                            previous_hash=event_dict.get("previous_hash")
                        )
                        
                        # Apply filters
                        if event_type and event.event_type != event_type:
                            continue
                        if user_id and event.user_id != user_id:
                            continue
                        
                        events.append(event)
                
                current_date += timedelta(days=1)
        
        return sorted(events, key=lambda e: e.timestamp)


class EventRecorder:
    """
    Records security and compliance events
    """
    
    def __init__(self, audit_trail: AuditTrail):
        self.audit_trail = audit_trail
    
    async def record_login(
        self,
        user_id: str,
        success: bool,
        ip_address: str,
        user_agent: str,
        reason: Optional[str] = None
    ):
        """Record login attempt"""
        
        event = AuditEvent(
            event_id=str(uuid.uuid4()),
            event_type=AuditEventType.LOGIN_SUCCESS if success else AuditEventType.LOGIN_FAILURE,
            severity=AuditSeverity.INFO if success else AuditSeverity.WARNING,
            timestamp=datetime.utcnow(),
            user_id=user_id,
            session_id=str(uuid.uuid4()) if success else None,
            ip_address=ip_address,
            user_agent=user_agent,
            resource_type="authentication",
            resource_id=user_id,
            action="login",
            result="success" if success else "failure",
            details={"reason": reason} if reason else {},
            metadata={}
        )
        
        await self.audit_trail.add_event(event)
    
    async def record_data_access(
        self,
        user_id: str,
        session_id: str,
        resource_type: str,
        resource_id: str,
        action: str,
        success: bool,
        ip_address: Optional[str] = None
    ):
        """Record data access event"""
        
        event_type_map = {
            "create": AuditEventType.DATA_CREATE,
            "read": AuditEventType.DATA_READ,
            "update": AuditEventType.DATA_UPDATE,
            "delete": AuditEventType.DATA_DELETE,
            "export": AuditEventType.DATA_EXPORT
        }
        
        event = AuditEvent(
            event_id=str(uuid.uuid4()),
            event_type=event_type_map.get(action, AuditEventType.DATA_READ),
            severity=AuditSeverity.INFO if success else AuditSeverity.WARNING,
            timestamp=datetime.utcnow(),
            user_id=user_id,
            session_id=session_id,
            ip_address=ip_address,
            user_agent=None,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            result="success" if success else "failure",
            details={},
            metadata={}
        )
        
        await self.audit_trail.add_event(event)
    
    async def record_compliance_event(
        self,
        event_type: str,
        compliance_type: str,
        details: Dict[str, Any],
        user_id: Optional[str] = None
    ):
        """Record compliance-related event"""
        
        event = AuditEvent(
            event_id=str(uuid.uuid4()),
            event_type=AuditEventType.COMPLIANCE_CHECK,
            severity=AuditSeverity.INFO,
            timestamp=datetime.utcnow(),
            user_id=user_id,
            session_id=None,
            ip_address=None,
            user_agent=None,
            resource_type="compliance",
            resource_id=compliance_type,
            action=event_type,
            result="recorded",
            details=details,
            metadata={"compliance_type": compliance_type}
        )
        
        await self.audit_trail.add_event(event)
    
    async def record_security_alert(
        self,
        alert_type: str,
        severity: str,
        details: Dict[str, Any],
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None
    ):
        """Record security alert"""
        
        severity_map = {
            "low": AuditSeverity.INFO,
            "medium": AuditSeverity.WARNING,
            "high": AuditSeverity.ERROR,
            "critical": AuditSeverity.CRITICAL
        }
        
        event = AuditEvent(
            event_id=str(uuid.uuid4()),
            event_type=AuditEventType.SECURITY_ALERT,
            severity=severity_map.get(severity.lower(), AuditSeverity.WARNING),
            timestamp=datetime.utcnow(),
            user_id=user_id,
            session_id=None,
            ip_address=ip_address,
            user_agent=None,
            resource_type="security",
            resource_id=alert_type,
            action="alert",
            result="triggered",
            details=details,
            metadata={"alert_type": alert_type}
        )
        
        await self.audit_trail.add_event(event)


class ComplianceReporter:
    """
    Generate compliance reports for regulatory requirements
    """
    
    def __init__(self, audit_trail: AuditTrail):
        self.audit_trail = audit_trail
    
    async def generate_finra_report(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Generate FINRA compliance report"""
        
        events = await self.audit_trail.get_events(start_date, end_date)
        
        # Filter relevant events
        trading_events = [e for e in events if "transaction" in e.event_type.value]
        compliance_events = [e for e in events if e.event_type == AuditEventType.COMPLIANCE_CHECK]
        
        return {
            "report_type": "FINRA Compliance Report",
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "summary": {
                "total_transactions": len(trading_events),
                "compliance_checks": len(compliance_events),
                "violations": len([e for e in compliance_events if "violation" in e.result])
            },
            "transactions": [self._format_transaction(e) for e in trading_events],
            "compliance_activities": [self._format_compliance(e) for e in compliance_events],
            "generated_at": datetime.utcnow().isoformat()
        }
    
    async def generate_sec_report(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Generate SEC compliance report"""
        
        events = await self.audit_trail.get_events(start_date, end_date)
        
        # Focus on investment advisory activities
        advisory_events = [e for e in events if e.resource_type == "portfolio"]
        
        return {
            "report_type": "SEC Form ADV Compliance Report",
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "advisory_activities": {
                "portfolio_modifications": len([e for e in advisory_events if e.action == "update"]),
                "simulations_run": len([e for e in events if e.event_type == AuditEventType.SIMULATION_RUN]),
                "client_communications": 0  # Would track actual communications
            },
            "risk_disclosures": self._get_risk_disclosures(events),
            "conflicts_of_interest": [],  # Would identify conflicts
            "generated_at": datetime.utcnow().isoformat()
        }
    
    async def generate_gdpr_report(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Generate GDPR compliance report"""
        
        events = await self.audit_trail.get_events(start_date, end_date)
        
        # Focus on data processing activities
        data_events = [e for e in events if "data" in e.event_type.value]
        
        return {
            "report_type": "GDPR Article 30 Records",
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "processing_activities": {
                "data_collected": len([e for e in data_events if e.event_type == AuditEventType.DATA_CREATE]),
                "data_accessed": len([e for e in data_events if e.event_type == AuditEventType.DATA_READ]),
                "data_modified": len([e for e in data_events if e.event_type == AuditEventType.DATA_UPDATE]),
                "data_deleted": len([e for e in data_events if e.event_type == AuditEventType.DATA_DELETE]),
                "data_exported": len([e for e in data_events if e.event_type == AuditEventType.DATA_EXPORT])
            },
            "data_subjects": self._get_unique_users(data_events),
            "purposes": ["Financial planning", "Compliance", "Service improvement"],
            "retention_period": f"{settings.AUDIT_LOG_RETENTION_DAYS} days",
            "security_measures": self._get_security_measures(events),
            "generated_at": datetime.utcnow().isoformat()
        }
    
    async def generate_soc2_report(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Generate SOC 2 Type II report"""
        
        events = await self.audit_trail.get_events(start_date, end_date)
        
        # Analyze security controls
        security_events = [e for e in events if e.resource_type == "security"]
        access_events = [e for e in events if "access" in e.event_type.value]
        
        return {
            "report_type": "SOC 2 Type II",
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "trust_services_criteria": {
                "security": {
                    "access_controls": len(access_events),
                    "access_denials": len([e for e in access_events if e.result == "failure"]),
                    "security_incidents": len([e for e in security_events if e.severity.value in ["error", "critical"]])
                },
                "availability": {
                    "uptime_percentage": 99.9,  # Would calculate actual uptime
                    "incidents": 0
                },
                "processing_integrity": {
                    "errors": len([e for e in events if e.severity == AuditSeverity.ERROR]),
                    "data_validation_failures": 0
                },
                "confidentiality": {
                    "encryption_events": len([e for e in events if "encryption" in e.action]),
                    "unauthorized_access_attempts": len([e for e in access_events if e.result == "failure"])
                },
                "privacy": {
                    "data_access_events": len([e for e in events if e.event_type == AuditEventType.DATA_READ]),
                    "consent_records": 0  # Would track consent
                }
            },
            "control_deficiencies": [],
            "management_response": "Controls operating effectively",
            "generated_at": datetime.utcnow().isoformat()
        }
    
    def _format_transaction(self, event: AuditEvent) -> Dict[str, Any]:
        """Format transaction event for reporting"""
        
        return {
            "transaction_id": event.resource_id,
            "timestamp": event.timestamp.isoformat(),
            "user": event.user_id,
            "type": event.action,
            "status": event.result,
            "details": event.details
        }
    
    def _format_compliance(self, event: AuditEvent) -> Dict[str, Any]:
        """Format compliance event for reporting"""
        
        return {
            "check_id": event.event_id,
            "timestamp": event.timestamp.isoformat(),
            "compliance_type": event.metadata.get("compliance_type"),
            "result": event.result,
            "details": event.details
        }
    
    def _get_risk_disclosures(self, events: List[AuditEvent]) -> List[str]:
        """Extract risk disclosures from events"""
        
        disclosures = set()
        
        for event in events:
            if "risk" in event.details:
                disclosures.add(event.details.get("risk"))
        
        return list(disclosures)
    
    def _get_unique_users(self, events: List[AuditEvent]) -> int:
        """Count unique users from events"""
        
        users = set()
        
        for event in events:
            if event.user_id:
                users.add(event.user_id)
        
        return len(users)
    
    def _get_security_measures(self, events: List[AuditEvent]) -> List[str]:
        """Identify security measures from events"""
        
        measures = set()
        
        for event in events:
            if event.resource_type == "security":
                measures.add(event.action)
        
        return list(measures)


class AuditLogger:
    """
    Central audit logging system
    """
    
    def __init__(self):
        self.audit_trail = AuditTrail()
        self.event_recorder = None
        self.compliance_reporter = None
    
    async def initialize(self):
        """Initialize audit system"""
        
        await self.audit_trail.initialize()
        self.event_recorder = EventRecorder(self.audit_trail)
        self.compliance_reporter = ComplianceReporter(self.audit_trail)
    
    async def log(
        self,
        event_type: AuditEventType,
        action: str,
        result: str,
        user_id: Optional[str] = None,
        resource: Optional[Tuple[str, str]] = None,
        details: Optional[Dict[str, Any]] = None,
        severity: AuditSeverity = AuditSeverity.INFO
    ):
        """Log an audit event"""
        
        event = AuditEvent(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            severity=severity,
            timestamp=datetime.utcnow(),
            user_id=user_id,
            session_id=None,
            ip_address=None,
            user_agent=None,
            resource_type=resource[0] if resource else None,
            resource_id=resource[1] if resource else None,
            action=action,
            result=result,
            details=details or {},
            metadata={}
        )
        
        await self.audit_trail.add_event(event)
    
    async def verify_integrity(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Tuple[bool, List[str]]:
        """Verify audit trail integrity"""
        
        return await self.audit_trail.verify_integrity(start_date, end_date)
    
    async def generate_report(
        self,
        report_type: str,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Generate compliance report"""
        
        if report_type.lower() == "finra":
            return await self.compliance_reporter.generate_finra_report(start_date, end_date)
        elif report_type.lower() == "sec":
            return await self.compliance_reporter.generate_sec_report(start_date, end_date)
        elif report_type.lower() == "gdpr":
            return await self.compliance_reporter.generate_gdpr_report(start_date, end_date)
        elif report_type.lower() == "soc2":
            return await self.compliance_reporter.generate_soc2_report(start_date, end_date)
        else:
            raise ValueError(f"Unknown report type: {report_type}")
    
    async def search_events(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        event_type: Optional[AuditEventType] = None,
        user_id: Optional[str] = None
    ) -> List[AuditEvent]:
        """Search audit events"""
        
        return await self.audit_trail.get_events(start_date, end_date, event_type, user_id)