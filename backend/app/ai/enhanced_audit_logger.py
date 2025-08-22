"""Enhanced audit logging system with compliance tracking for AI narrative generation."""

import json
import logging
import logging.handlers
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List
from enum import Enum
import asyncio
from collections import deque
import gzip

from .config import AIConfig, LLMProvider


class AuditEventType(str, Enum):
    """Types of audit events."""
    # Request/Response Events
    REQUEST_RECEIVED = "request_received"
    PROMPT_SUBMITTED = "prompt_submitted"
    RESPONSE_GENERATED = "response_generated"
    NARRATIVE_DELIVERED = "narrative_delivered"
    
    # LLM Events
    LLM_GENERATION = "llm_generation"
    API_CALL = "api_call"
    API_ERROR = "api_error"
    PROVIDER_SWITCH = "provider_switch"
    
    # Template Events
    TEMPLATE_RENDERED = "template_rendered"
    TEMPLATE_VALIDATED = "template_validated"
    
    # Safety & Compliance Events
    SAFETY_VIOLATION = "safety_violation"
    COMPLIANCE_CHECK = "compliance_check"
    DISCLAIMER_ADDED = "disclaimer_added"
    NUMERICAL_VALIDATION = "numerical_validation"
    
    # Cache Events
    CACHE_HIT = "cache_hit"
    CACHE_MISS = "cache_miss"
    CACHE_WRITE = "cache_write"
    
    # A/B Testing Events
    AB_TEST = "ab_test"
    AB_VARIANT_ASSIGNED = "ab_variant_assigned"
    
    # Fallback Events
    FALLBACK_TRIGGERED = "fallback_triggered"
    
    # User Feedback
    USER_FEEDBACK = "user_feedback"
    SATISFACTION_SCORE = "satisfaction_score"
    
    # System Events
    SYSTEM_ERROR = "system_error"
    RATE_LIMIT = "rate_limit"


class ComplianceLevel(str, Enum):
    """Compliance levels for audit events."""
    CRITICAL = "critical"  # Must be logged for regulatory compliance
    HIGH = "high"         # Important for audit trail
    MEDIUM = "medium"     # Standard operational logging
    LOW = "low"          # Debug and informational


class EnhancedAuditLogger:
    """Enhanced audit logging with compliance tracking."""
    
    def __init__(self, config: Optional[AIConfig] = None):
        """Initialize enhanced audit logger."""
        self.config = config or AIConfig()
        
        # Setup logging directory
        self.log_dir = Path(self.config.audit_log_path).parent
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Compliance settings
        self.compliance_mode = self.config.enable_audit_logging
        self.retention_days = 365  # Keep logs for 1 year for compliance
        
        # In-memory buffer for batch writing
        self.buffer = deque(maxlen=100)
        self.critical_buffer = deque(maxlen=10)  # Separate buffer for critical events
        
        # Setup file logging
        self.logger = self._setup_logger()
        
        # Statistics tracking
        self.stats = {
            "total_requests": 0,
            "total_responses": 0,
            "total_violations": 0,
            "total_api_calls": 0,
            "total_api_errors": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "fallback_uses": 0,
            "compliance_checks": 0
        }
        
        # Compliance tracking
        self.compliance_stats = {
            "disclaimers_added": 0,
            "numerical_validations": 0,
            "safety_violations": 0,
            "pii_detections": 0
        }
        
        # Start background flush task
        self.flush_task = asyncio.create_task(self._periodic_flush())
    
    def _setup_logger(self) -> logging.Logger:
        """Setup structured logger with rotation."""
        logger = logging.getLogger("ai_audit_enhanced")
        logger.setLevel(logging.INFO)
        
        # Rotating file handler
        handler = logging.handlers.RotatingFileHandler(
            self.config.audit_log_path,
            maxBytes=100 * 1024 * 1024,  # 100MB
            backupCount=30  # Keep 30 backup files
        )
        
        # JSON formatter
        formatter = logging.Formatter('%(message)s')
        handler.setFormatter(formatter)
        
        logger.addHandler(handler)
        
        return logger
    
    async def _periodic_flush(self):
        """Periodically flush buffers to disk."""
        while True:
            await asyncio.sleep(30)  # Flush every 30 seconds
            await self.flush()
    
    async def log_event(
        self,
        event_type: AuditEventType,
        data: Dict[str, Any],
        compliance_level: ComplianceLevel = ComplianceLevel.MEDIUM,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        simulation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log an audit event with compliance tracking."""
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type.value,
            "compliance_level": compliance_level.value,
            "user_id": user_id,
            "session_id": session_id,
            "simulation_id": simulation_id,
            "data": data,
            "metadata": metadata or {},
            "environment": {
                "version": self.config.template_version,
                "strict_mode": self.config.strict_template_mode
            }
        }
        
        # Add to appropriate buffer based on compliance level
        if compliance_level == ComplianceLevel.CRITICAL:
            self.critical_buffer.append(event)
            # Immediately flush critical events
            await self._flush_critical()
        else:
            self.buffer.append(event)
        
        # Update statistics
        self._update_stats(event_type)
        
        # Flush if buffer is full
        if len(self.buffer) >= 100:
            await self.flush()
    
    async def log_request(
        self,
        user_id: str,
        simulation_id: str,
        narrative_type: str,
        language: str,
        data_hash: Optional[str] = None
    ):
        """Log incoming narrative request."""
        await self.log_event(
            AuditEventType.REQUEST_RECEIVED,
            {
                "narrative_type": narrative_type,
                "language": language,
                "data_hash": data_hash or hashlib.sha256(str(simulation_id).encode()).hexdigest()
            },
            ComplianceLevel.HIGH,
            user_id=user_id,
            simulation_id=simulation_id
        )
        self.stats["total_requests"] += 1
    
    async def log_generation(
        self,
        provider: LLMProvider,
        model: str,
        prompt_hash: str,
        tokens_used: int,
        success: bool,
        error: Optional[str] = None,
        latency_ms: Optional[float] = None
    ):
        """Log LLM generation event."""
        await self.log_event(
            AuditEventType.LLM_GENERATION,
            {
                "provider": provider.value,
                "model": model,
                "prompt_hash": prompt_hash,
                "tokens_used": tokens_used,
                "success": success,
                "error": error,
                "latency_ms": latency_ms
            },
            ComplianceLevel.HIGH
        )
    
    async def log_response(
        self,
        user_id: str,
        simulation_id: str,
        response: Any
    ):
        """Log narrative response delivery."""
        response_data = {
            "narrative_length": len(response.narrative) if hasattr(response, 'narrative') else 0,
            "provider": response.provider.value if hasattr(response, 'provider') else "unknown",
            "enhanced": response.enhanced if hasattr(response, 'enhanced') else False,
            "cached": response.cached if hasattr(response, 'cached') else False,
            "tokens_used": response.tokens_used if hasattr(response, 'tokens_used') else 0
        }
        
        await self.log_event(
            AuditEventType.NARRATIVE_DELIVERED,
            response_data,
            ComplianceLevel.HIGH,
            user_id=user_id,
            simulation_id=simulation_id
        )
        self.stats["total_responses"] += 1
    
    async def log_compliance_check(
        self,
        check_type: str,
        passed: bool,
        details: Dict[str, Any],
        user_id: Optional[str] = None,
        simulation_id: Optional[str] = None
    ):
        """Log compliance check event."""
        await self.log_event(
            AuditEventType.COMPLIANCE_CHECK,
            {
                "check_type": check_type,
                "passed": passed,
                "details": details
            },
            ComplianceLevel.CRITICAL,
            user_id=user_id,
            simulation_id=simulation_id
        )
        self.compliance_stats["compliance_checks"] += 1
    
    async def log_numerical_validation(
        self,
        template_id: str,
        variables: Dict[str, Any],
        validation_passed: bool,
        errors: List[str],
        simulation_id: Optional[str] = None
    ):
        """Log numerical validation for templates."""
        await self.log_event(
            AuditEventType.NUMERICAL_VALIDATION,
            {
                "template_id": template_id,
                "variable_count": len(variables),
                "validation_passed": validation_passed,
                "errors": errors
            },
            ComplianceLevel.HIGH,
            simulation_id=simulation_id
        )
        self.compliance_stats["numerical_validations"] += 1
    
    async def log_disclaimer(
        self,
        disclaimer_type: str,
        language: str,
        position: str,
        simulation_id: Optional[str] = None
    ):
        """Log disclaimer addition for compliance."""
        await self.log_event(
            AuditEventType.DISCLAIMER_ADDED,
            {
                "disclaimer_type": disclaimer_type,
                "language": language,
                "position": position
            },
            ComplianceLevel.CRITICAL,
            simulation_id=simulation_id
        )
        self.compliance_stats["disclaimers_added"] += 1
    
    async def log_safety_violation(
        self,
        violation_type: str,
        content_hash: str,
        severity: str,
        action_taken: str,
        user_id: Optional[str] = None
    ):
        """Log safety violation with compliance tracking."""
        await self.log_event(
            AuditEventType.SAFETY_VIOLATION,
            {
                "violation_type": violation_type,
                "content_hash": content_hash,
                "severity": severity,
                "action_taken": action_taken
            },
            ComplianceLevel.CRITICAL,
            user_id=user_id
        )
        self.stats["total_violations"] += 1
        self.compliance_stats["safety_violations"] += 1
    
    async def log_feedback(
        self,
        user_id: str,
        simulation_id: str,
        satisfaction_score: float,
        enhanced: bool,
        feedback_text: Optional[str] = None
    ):
        """Log user feedback for quality tracking."""
        await self.log_event(
            AuditEventType.USER_FEEDBACK,
            {
                "satisfaction_score": satisfaction_score,
                "enhanced": enhanced,
                "feedback_text": feedback_text
            },
            ComplianceLevel.MEDIUM,
            user_id=user_id,
            simulation_id=simulation_id
        )
    
    async def log_error(
        self,
        user_id: str,
        simulation_id: str,
        error: str,
        error_type: str = "system",
        stack_trace: Optional[str] = None
    ):
        """Log system error."""
        await self.log_event(
            AuditEventType.SYSTEM_ERROR,
            {
                "error": error,
                "error_type": error_type,
                "stack_trace": stack_trace
            },
            ComplianceLevel.HIGH,
            user_id=user_id,
            simulation_id=simulation_id
        )
    
    async def log_cache_event(
        self,
        cache_hit: bool,
        cache_key: str,
        response_size: Optional[int] = None
    ):
        """Log cache hit or miss."""
        event_type = AuditEventType.CACHE_HIT if cache_hit else AuditEventType.CACHE_MISS
        await self.log_event(
            event_type,
            {
                "cache_key": cache_key,
                "response_size": response_size
            },
            ComplianceLevel.LOW
        )
        
        if cache_hit:
            self.stats["cache_hits"] += 1
        else:
            self.stats["cache_misses"] += 1
    
    async def flush(self):
        """Flush buffered events to disk."""
        if not self.buffer:
            return
        
        # Write all buffered events
        while self.buffer:
            event = self.buffer.popleft()
            self.logger.info(json.dumps(event))
    
    async def _flush_critical(self):
        """Immediately flush critical events."""
        while self.critical_buffer:
            event = self.critical_buffer.popleft()
            self.logger.critical(json.dumps(event))
    
    def _update_stats(self, event_type: AuditEventType):
        """Update statistics counters."""
        if event_type == AuditEventType.FALLBACK_TRIGGERED:
            self.stats["fallback_uses"] += 1
        elif event_type == AuditEventType.API_CALL:
            self.stats["total_api_calls"] += 1
        elif event_type == AuditEventType.API_ERROR:
            self.stats["total_api_errors"] += 1
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get current statistics including compliance metrics."""
        cache_rate = 0
        if self.stats["cache_hits"] + self.stats["cache_misses"] > 0:
            cache_rate = self.stats["cache_hits"] / (
                self.stats["cache_hits"] + self.stats["cache_misses"]
            ) * 100
        
        api_success_rate = 0
        if self.stats["total_api_calls"] > 0:
            api_success_rate = (
                (self.stats["total_api_calls"] - self.stats["total_api_errors"]) /
                self.stats["total_api_calls"] * 100
            )
        
        return {
            "operational": {
                **self.stats,
                "cache_hit_rate": f"{cache_rate:.2f}%",
                "api_success_rate": f"{api_success_rate:.2f}%",
                "fallback_rate": f"{self.stats['fallback_uses'] / max(self.stats['total_requests'], 1) * 100:.2f}%"
            },
            "compliance": {
                **self.compliance_stats,
                "violation_rate": f"{self.compliance_stats['safety_violations'] / max(self.stats['total_requests'], 1) * 100:.2f}%",
                "disclaimer_compliance": f"{self.compliance_stats['disclaimers_added'] / max(self.stats['total_responses'], 1) * 100:.2f}%"
            }
        }
    
    async def generate_compliance_report(
        self,
        start_date: datetime,
        end_date: datetime,
        output_file: str
    ):
        """Generate compliance report for audit purposes."""
        # Search for critical and high level events
        critical_events = await self.search_logs(
            start_date,
            end_date,
            compliance_level=ComplianceLevel.CRITICAL
        )
        
        high_events = await self.search_logs(
            start_date,
            end_date,
            compliance_level=ComplianceLevel.HIGH
        )
        
        report = {
            "report_period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "generated_at": datetime.utcnow().isoformat(),
            "summary": {
                "total_critical_events": len(critical_events),
                "total_high_events": len(high_events),
                "safety_violations": sum(1 for e in critical_events if e.get("event_type") == AuditEventType.SAFETY_VIOLATION.value),
                "compliance_checks": sum(1 for e in critical_events if e.get("event_type") == AuditEventType.COMPLIANCE_CHECK.value),
                "disclaimers_added": sum(1 for e in critical_events if e.get("event_type") == AuditEventType.DISCLAIMER_ADDED.value)
            },
            "critical_events": critical_events,
            "statistics": self.get_statistics()
        }
        
        # Write report
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        return report
    
    async def search_logs(
        self,
        start_date: datetime,
        end_date: datetime,
        event_type: Optional[AuditEventType] = None,
        compliance_level: Optional[ComplianceLevel] = None,
        user_id: Optional[str] = None,
        simulation_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Search audit logs with compliance filtering."""
        results = []
        
        # Read log file (in production, this would query a database)
        log_file = Path(self.config.audit_log_path)
        if not log_file.exists():
            return results
        
        with open(log_file, 'r') as f:
            for line in f:
                try:
                    event = json.loads(line)
                    event_time = datetime.fromisoformat(event["timestamp"])
                    
                    # Apply time filter
                    if event_time < start_date or event_time > end_date:
                        continue
                    
                    # Apply other filters
                    if event_type and event.get("event_type") != event_type.value:
                        continue
                    
                    if compliance_level and event.get("compliance_level") != compliance_level.value:
                        continue
                    
                    if user_id and event.get("user_id") != user_id:
                        continue
                    
                    if simulation_id and event.get("simulation_id") != simulation_id:
                        continue
                    
                    results.append(event)
                    
                except (json.JSONDecodeError, KeyError):
                    continue
        
        return results
    
    async def cleanup_old_logs(self):
        """Clean up old logs while maintaining compliance retention."""
        cutoff_date = datetime.utcnow() - timedelta(days=self.retention_days)
        
        # Archive old logs before deletion
        archive_dir = self.log_dir / "archive"
        archive_dir.mkdir(exist_ok=True)
        
        for log_file in self.log_dir.glob("*.log*"):
            # Check file modification time
            file_time = datetime.fromtimestamp(log_file.stat().st_mtime)
            
            if file_time < cutoff_date:
                # Compress and archive
                archive_file = archive_dir / f"{log_file.name}.gz"
                with open(log_file, 'rb') as f_in:
                    with gzip.open(archive_file, 'wb') as f_out:
                        f_out.writelines(f_in)
                
                # Delete original
                log_file.unlink()
                self.logger.info(f"Archived old log file: {log_file} -> {archive_file}")