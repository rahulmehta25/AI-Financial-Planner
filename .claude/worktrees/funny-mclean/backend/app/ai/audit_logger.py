"""Audit logging system for AI narrative generation."""

import json
import logging
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from enum import Enum
import asyncio
from collections import deque
import gzip


class AuditEventType(str, Enum):
    """Types of audit events."""
    PROMPT_SUBMITTED = "prompt_submitted"
    RESPONSE_GENERATED = "response_generated"
    SAFETY_VIOLATION = "safety_violation"
    API_CALL = "api_call"
    API_ERROR = "api_error"
    CACHE_HIT = "cache_hit"
    CACHE_MISS = "cache_miss"
    TEMPLATE_RENDERED = "template_rendered"
    AB_TEST = "ab_test"
    FALLBACK_USED = "fallback_used"


class AuditLogger:
    """Comprehensive audit logging for AI operations."""
    
    def __init__(self, 
                 log_dir: str = "/var/log/financial_ai",
                 max_buffer_size: int = 100,
                 rotation_size_mb: int = 100):
        """Initialize audit logger.
        
        Args:
            log_dir: Directory for audit logs
            max_buffer_size: Maximum buffered entries before flush
            rotation_size_mb: Max log file size before rotation
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self.max_buffer_size = max_buffer_size
        self.rotation_size_mb = rotation_size_mb
        
        # In-memory buffer for batch writing
        self.buffer = deque(maxlen=max_buffer_size)
        
        # Setup file logging
        self.current_log_file = self._get_current_log_file()
        
        # Setup structured logger
        self.logger = self._setup_logger()
        
        # Statistics tracking
        self.stats = {
            "total_prompts": 0,
            "total_responses": 0,
            "total_violations": 0,
            "total_api_calls": 0,
            "total_api_errors": 0,
            "cache_hits": 0,
            "cache_misses": 0
        }
        
        # Start background flush task
        self.flush_task = None
    
    def _setup_logger(self) -> logging.Logger:
        """Setup structured logger.
        
        Returns:
            Configured logger instance
        """
        logger = logging.getLogger("ai_audit")
        logger.setLevel(logging.INFO)
        
        # File handler with rotation
        handler = logging.handlers.RotatingFileHandler(
            self.current_log_file,
            maxBytes=self.rotation_size_mb * 1024 * 1024,
            backupCount=10
        )
        
        # JSON formatter for structured logs
        formatter = logging.Formatter('%(message)s')
        handler.setFormatter(formatter)
        
        logger.addHandler(handler)
        
        return logger
    
    def _get_current_log_file(self) -> Path:
        """Get current log file path.
        
        Returns:
            Path to current log file
        """
        date_str = datetime.utcnow().strftime("%Y%m%d")
        return self.log_dir / f"ai_audit_{date_str}.jsonl"
    
    async def log_event(self,
                       event_type: AuditEventType,
                       data: Dict[str, Any],
                       user_id: Optional[str] = None,
                       session_id: Optional[str] = None,
                       metadata: Optional[Dict[str, Any]] = None):
        """Log an audit event.
        
        Args:
            event_type: Type of event
            data: Event data
            user_id: User identifier
            session_id: Session identifier
            metadata: Additional metadata
        """
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type.value,
            "user_id": user_id,
            "session_id": session_id,
            "data": data,
            "metadata": metadata or {}
        }
        
        # Add to buffer
        self.buffer.append(event)
        
        # Update statistics
        self._update_stats(event_type)
        
        # Flush if buffer is full
        if len(self.buffer) >= self.max_buffer_size:
            await self.flush()
    
    async def log_prompt(self,
                        prompt: str,
                        template_type: Optional[str] = None,
                        user_id: Optional[str] = None,
                        session_id: Optional[str] = None):
        """Log a prompt submission.
        
        Args:
            prompt: The prompt text
            template_type: Template being used
            user_id: User identifier
            session_id: Session identifier
        """
        data = {
            "prompt_hash": hashlib.sha256(prompt.encode()).hexdigest(),
            "prompt_length": len(prompt),
            "template_type": template_type,
            "prompt_preview": prompt[:200] + "..." if len(prompt) > 200 else prompt
        }
        
        await self.log_event(
            AuditEventType.PROMPT_SUBMITTED,
            data,
            user_id,
            session_id
        )
    
    async def log_response(self,
                          response: str,
                          model: str,
                          provider: str,
                          tokens_used: int,
                          latency_ms: float,
                          user_id: Optional[str] = None,
                          session_id: Optional[str] = None):
        """Log an AI response.
        
        Args:
            response: Generated response text
            model: Model used
            provider: Provider (OpenAI/Anthropic)
            tokens_used: Number of tokens consumed
            latency_ms: Response latency in milliseconds
            user_id: User identifier
            session_id: Session identifier
        """
        data = {
            "response_hash": hashlib.sha256(response.encode()).hexdigest(),
            "response_length": len(response),
            "model": model,
            "provider": provider,
            "tokens_used": tokens_used,
            "latency_ms": latency_ms,
            "response_preview": response[:200] + "..." if len(response) > 200 else response
        }
        
        await self.log_event(
            AuditEventType.RESPONSE_GENERATED,
            data,
            user_id,
            session_id
        )
    
    async def log_api_call(self,
                          provider: str,
                          model: str,
                          endpoint: str,
                          status_code: int,
                          latency_ms: float,
                          error: Optional[str] = None):
        """Log an API call to LLM provider.
        
        Args:
            provider: API provider
            model: Model used
            endpoint: API endpoint
            status_code: HTTP status code
            latency_ms: Call latency
            error: Error message if failed
        """
        data = {
            "provider": provider,
            "model": model,
            "endpoint": endpoint,
            "status_code": status_code,
            "latency_ms": latency_ms,
            "success": status_code == 200,
            "error": error
        }
        
        event_type = AuditEventType.API_ERROR if error else AuditEventType.API_CALL
        await self.log_event(event_type, data)
    
    async def log_safety_violation(self,
                                   violation_type: str,
                                   content: str,
                                   user_id: Optional[str] = None):
        """Log a safety violation.
        
        Args:
            violation_type: Type of violation
            content: Content that triggered violation
            user_id: User identifier
        """
        data = {
            "violation_type": violation_type,
            "content_hash": hashlib.sha256(content.encode()).hexdigest(),
            "content_preview": content[:100] + "..." if len(content) > 100 else content,
            "severity": "high"  # Could be parameterized
        }
        
        await self.log_event(
            AuditEventType.SAFETY_VIOLATION,
            data,
            user_id
        )
    
    async def log_cache_event(self,
                             cache_hit: bool,
                             cache_key: str,
                             response_hash: Optional[str] = None):
        """Log cache hit or miss.
        
        Args:
            cache_hit: Whether cache was hit
            cache_key: Cache key used
            response_hash: Hash of cached response
        """
        data = {
            "cache_key": cache_key,
            "response_hash": response_hash
        }
        
        event_type = AuditEventType.CACHE_HIT if cache_hit else AuditEventType.CACHE_MISS
        await self.log_event(event_type, data)
    
    async def log_ab_test(self,
                         test_name: str,
                         variant: str,
                         user_id: str,
                         metrics: Dict[str, Any]):
        """Log A/B test participation.
        
        Args:
            test_name: Name of A/B test
            variant: Variant assigned (A or B)
            user_id: User identifier
            metrics: Test metrics
        """
        data = {
            "test_name": test_name,
            "variant": variant,
            "metrics": metrics
        }
        
        await self.log_event(
            AuditEventType.AB_TEST,
            data,
            user_id
        )
    
    async def flush(self):
        """Flush buffered events to disk."""
        if not self.buffer:
            return
        
        # Write all buffered events
        with open(self.current_log_file, 'a') as f:
            while self.buffer:
                event = self.buffer.popleft()
                f.write(json.dumps(event) + '\n')
    
    def _update_stats(self, event_type: AuditEventType):
        """Update statistics counters.
        
        Args:
            event_type: Type of event
        """
        if event_type == AuditEventType.PROMPT_SUBMITTED:
            self.stats["total_prompts"] += 1
        elif event_type == AuditEventType.RESPONSE_GENERATED:
            self.stats["total_responses"] += 1
        elif event_type == AuditEventType.SAFETY_VIOLATION:
            self.stats["total_violations"] += 1
        elif event_type == AuditEventType.API_CALL:
            self.stats["total_api_calls"] += 1
        elif event_type == AuditEventType.API_ERROR:
            self.stats["total_api_errors"] += 1
        elif event_type == AuditEventType.CACHE_HIT:
            self.stats["cache_hits"] += 1
        elif event_type == AuditEventType.CACHE_MISS:
            self.stats["cache_misses"] += 1
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get current statistics.
        
        Returns:
            Statistics dictionary
        """
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
            **self.stats,
            "cache_hit_rate": f"{cache_rate:.2f}%",
            "api_success_rate": f"{api_success_rate:.2f}%",
            "violation_rate": f"{self.stats['total_violations'] / max(self.stats['total_prompts'], 1) * 100:.2f}%"
        }
    
    async def search_logs(self,
                         start_date: datetime,
                         end_date: datetime,
                         event_type: Optional[AuditEventType] = None,
                         user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search audit logs.
        
        Args:
            start_date: Start of search period
            end_date: End of search period
            event_type: Filter by event type
            user_id: Filter by user
            
        Returns:
            List of matching events
        """
        results = []
        
        # Determine which log files to search
        current_date = start_date
        while current_date <= end_date:
            log_file = self.log_dir / f"ai_audit_{current_date.strftime('%Y%m%d')}.jsonl"
            
            if log_file.exists():
                with open(log_file, 'r') as f:
                    for line in f:
                        event = json.loads(line)
                        event_time = datetime.fromisoformat(event["timestamp"])
                        
                        # Apply filters
                        if event_time < start_date or event_time > end_date:
                            continue
                        
                        if event_type and event["event_type"] != event_type.value:
                            continue
                        
                        if user_id and event.get("user_id") != user_id:
                            continue
                        
                        results.append(event)
            
            # Move to next day
            current_date = current_date.replace(day=current_date.day + 1)
        
        return results
    
    async def export_logs(self,
                         start_date: datetime,
                         end_date: datetime,
                         output_file: str,
                         compress: bool = True):
        """Export logs for a date range.
        
        Args:
            start_date: Start of export period
            end_date: End of export period
            output_file: Output file path
            compress: Whether to compress output
        """
        logs = await self.search_logs(start_date, end_date)
        
        if compress:
            with gzip.open(output_file + '.gz', 'wt') as f:
                for log in logs:
                    f.write(json.dumps(log) + '\n')
        else:
            with open(output_file, 'w') as f:
                for log in logs:
                    f.write(json.dumps(log) + '\n')
    
    async def cleanup_old_logs(self, days_to_keep: int = 90):
        """Clean up old log files.
        
        Args:
            days_to_keep: Number of days of logs to retain
        """
        cutoff_date = datetime.utcnow().replace(
            day=datetime.utcnow().day - days_to_keep
        )
        
        for log_file in self.log_dir.glob("ai_audit_*.jsonl*"):
            # Extract date from filename
            try:
                date_str = log_file.stem.split('_')[-1]
                file_date = datetime.strptime(date_str, "%Y%m%d")
                
                if file_date < cutoff_date:
                    log_file.unlink()
                    self.logger.info(f"Deleted old log file: {log_file}")
            except (ValueError, IndexError):
                continue