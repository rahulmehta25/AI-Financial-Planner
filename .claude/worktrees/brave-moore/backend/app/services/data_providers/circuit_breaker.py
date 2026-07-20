"""
Circuit breaker implementation for fault tolerance
"""
import asyncio
from typing import Callable, Optional, Any, TypeVar
from datetime import datetime, timedelta
from enum import Enum
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"      # Failing, rejecting calls
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreaker:
    """
    Circuit breaker pattern implementation
    
    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Service is failing, requests are rejected immediately
    - HALF_OPEN: Testing if service has recovered
    """
    
    def __init__(
        self,
        name: str,
        failure_threshold: int = 3,
        recovery_timeout: int = 60,
        expected_exception: Optional[type] = None
    ):
        """
        Initialize circuit breaker
        
        Args:
            name: Name for logging
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds to wait before attempting recovery
            expected_exception: Exception type to catch (None = all)
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception or Exception
        
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time: Optional[datetime] = None
        self._success_count = 0
        
    @property
    def state(self) -> CircuitState:
        """Get current circuit state"""
        return self._state
    
    @property
    def is_open(self) -> bool:
        """Check if circuit is open"""
        return self._state == CircuitState.OPEN
    
    @property
    def is_closed(self) -> bool:
        """Check if circuit is closed"""
        return self._state == CircuitState.CLOSED
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        if self._last_failure_time is None:
            return False
        
        time_since_failure = datetime.utcnow() - self._last_failure_time
        return time_since_failure > timedelta(seconds=self.recovery_timeout)
    
    def _record_success(self):
        """Record a successful call"""
        if self._state == CircuitState.HALF_OPEN:
            self._success_count += 1
            # After successful test in half-open, close the circuit
            if self._success_count >= 1:
                self._reset()
                logger.info(f"Circuit breaker '{self.name}' closed after successful recovery")
        else:
            self._failure_count = 0  # Reset failure count on success
    
    def _record_failure(self):
        """Record a failed call"""
        self._failure_count += 1
        self._last_failure_time = datetime.utcnow()
        
        if self._failure_count >= self.failure_threshold:
            self._trip()
    
    def _trip(self):
        """Trip the circuit breaker (open it)"""
        if self._state != CircuitState.OPEN:
            self._state = CircuitState.OPEN
            logger.warning(
                f"Circuit breaker '{self.name}' opened after "
                f"{self._failure_count} failures"
            )
    
    def _reset(self):
        """Reset the circuit breaker (close it)"""
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time = None
    
    def _attempt_reset(self):
        """Attempt to reset by moving to half-open state"""
        self._state = CircuitState.HALF_OPEN
        self._success_count = 0
        logger.info(f"Circuit breaker '{self.name}' attempting reset (half-open)")
    
    async def call(self, func: Callable[..., T], *args, **kwargs) -> T:
        """
        Call a function through the circuit breaker
        
        Args:
            func: Async function to call
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            CircuitOpenError: If circuit is open
            Original exception: If function fails
        """
        # Check if circuit should attempt reset
        if self._state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self._attempt_reset()
            else:
                raise CircuitOpenError(
                    f"Circuit breaker '{self.name}' is open. "
                    f"Retry after {self.recovery_timeout} seconds"
                )
        
        try:
            # Attempt the call
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            
            self._record_success()
            return result
            
        except self.expected_exception as e:
            self._record_failure()
            raise
        except CircuitOpenError:
            # Re-raise circuit open errors without recording as failure
            raise
        except Exception as e:
            # Unexpected exception - record and re-raise
            logger.error(f"Unexpected exception in circuit breaker '{self.name}': {e}")
            self._record_failure()
            raise
    
    def manual_reset(self):
        """Manually reset the circuit breaker"""
        self._reset()
        logger.info(f"Circuit breaker '{self.name}' manually reset")
    
    def manual_open(self):
        """Manually open the circuit breaker"""
        self._trip()
        logger.info(f"Circuit breaker '{self.name}' manually opened")
    
    def get_status(self) -> dict:
        """Get circuit breaker status"""
        return {
            "name": self.name,
            "state": self._state.value,
            "failure_count": self._failure_count,
            "success_count": self._success_count,
            "last_failure": self._last_failure_time.isoformat() if self._last_failure_time else None,
            "failure_threshold": self.failure_threshold,
            "recovery_timeout": self.recovery_timeout
        }


class CircuitOpenError(Exception):
    """Exception raised when circuit is open"""
    pass