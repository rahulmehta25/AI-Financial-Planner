"""
Data Source Failover Manager - Production-Grade Reliability System

Advanced failover management system featuring:
- Circuit breaker pattern implementation with multiple states
- Health monitoring and automatic recovery
- Intelligent failover routing with priority-based selection
- Performance metrics and alerting
- Graceful degradation and service level management
- Real-time status monitoring and reporting
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
import json
import statistics
from collections import defaultdict, deque
import time

from app.core.config import Config

logger = logging.getLogger(__name__)


class CircuitBreakerState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"           # Normal operation, calls allowed
    OPEN = "open"               # Failure state, calls rejected
    HALF_OPEN = "half_open"     # Recovery testing, limited calls allowed


class ServiceLevel(Enum):
    """Service level classifications"""
    CRITICAL = "critical"       # Must be available, immediate failover
    HIGH = "high"              # Important, fast failover
    MEDIUM = "medium"          # Standard, normal failover
    LOW = "low"                # Best effort, slow failover


class FailoverStrategy(Enum):
    """Failover strategies"""
    IMMEDIATE = "immediate"         # Instant failover on first failure
    PROGRESSIVE = "progressive"     # Gradual degradation, multiple attempts
    CONSENSUS = "consensus"         # Require multiple failures before failover
    ADAPTIVE = "adaptive"          # Adjust strategy based on historical performance


@dataclass
class HealthMetrics:
    """Health metrics for a service/provider"""
    success_rate: float = 0.0
    average_latency: float = 0.0
    error_count: int = 0
    total_requests: int = 0
    last_success: Optional[datetime] = None
    last_failure: Optional[datetime] = None
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    uptime_percentage: float = 100.0
    
    def calculate_success_rate(self) -> float:
        """Calculate current success rate"""
        if self.total_requests == 0:
            return 0.0
        return ((self.total_requests - self.error_count) / self.total_requests) * 100


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker"""
    failure_threshold: int = 5              # Number of failures to open circuit
    success_threshold: int = 3              # Number of successes to close circuit  
    timeout: int = 60                       # Timeout before trying half-open (seconds)
    slow_call_threshold: float = 5.0        # Slow call threshold (seconds)
    slow_call_rate_threshold: float = 50.0  # Percentage of slow calls to trigger
    minimum_number_of_calls: int = 10       # Minimum calls before evaluating
    sliding_window_size: int = 100          # Size of sliding window for evaluation
    
    # Advanced settings
    exponential_backoff: bool = True        # Use exponential backoff for timeouts
    max_timeout: int = 3600                # Maximum timeout (1 hour)
    jitter: bool = True                    # Add jitter to prevent thundering herd


class EnhancedCircuitBreaker:
    """
    Enhanced circuit breaker with sliding window, metrics, and adaptive behavior
    """
    
    def __init__(
        self,
        name: str,
        config: CircuitBreakerConfig = None,
        service_level: ServiceLevel = ServiceLevel.MEDIUM
    ):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.service_level = service_level
        self.state = CircuitBreakerState.CLOSED
        
        # Metrics and tracking
        self.metrics = HealthMetrics()
        self.call_history = deque(maxlen=self.config.sliding_window_size)
        self.state_history = []
        
        # Timing
        self.last_failure_time = None
        self.last_state_change = datetime.utcnow()
        self.next_attempt_time = None
        
        # Adaptive behavior
        self.failure_rate_window = deque(maxlen=50)  # Track failure rates
        self.latency_window = deque(maxlen=100)      # Track latencies
        
        # Event handlers
        self.on_state_change: Optional[Callable] = None
        self.on_failure: Optional[Callable] = None
        self.on_success: Optional[Callable] = None
    
    async def call(
        self,
        func: Callable,
        *args,
        timeout: Optional[float] = None,
        **kwargs
    ) -> Any:
        """
        Execute function call through circuit breaker protection
        
        Args:
            func: Function to execute
            *args: Function arguments
            timeout: Optional timeout for the call
            **kwargs: Function keyword arguments
            
        Returns:
            Function result if successful
            
        Raises:
            CircuitOpenException: If circuit is open
            Various exceptions: From the underlying function
        """
        
        # Check if circuit allows the call
        if not self._can_proceed():
            raise CircuitOpenException(
                f"Circuit breaker '{self.name}' is OPEN. "
                f"Next attempt allowed at {self.next_attempt_time}"
            )
        
        # Record call attempt
        call_start_time = time.time()
        
        try:
            # Execute the function with timeout
            if timeout:
                result = await asyncio.wait_for(func(*args, **kwargs), timeout=timeout)
            else:
                result = await func(*args, **kwargs)
            
            # Record successful call
            call_duration = time.time() - call_start_time
            await self._record_success(call_duration)
            
            return result
            
        except Exception as e:
            # Record failed call
            call_duration = time.time() - call_start_time
            await self._record_failure(call_duration, e)
            raise
    
    def _can_proceed(self) -> bool:
        """Check if the circuit breaker allows the call to proceed"""
        
        if self.state == CircuitBreakerState.CLOSED:
            return True
        
        if self.state == CircuitBreakerState.OPEN:
            if self._should_attempt_reset():
                self._transition_to_half_open()
                return True
            return False
        
        if self.state == CircuitBreakerState.HALF_OPEN:
            # Allow limited calls in half-open state
            return True
        
        return False
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        
        if not self.last_failure_time:
            return True
        
        timeout = self._calculate_timeout()
        time_since_failure = datetime.utcnow() - self.last_failure_time
        
        return time_since_failure.total_seconds() >= timeout
    
    def _calculate_timeout(self) -> float:
        """Calculate timeout with exponential backoff and jitter"""
        
        base_timeout = self.config.timeout
        
        if self.config.exponential_backoff:
            # Exponential backoff based on consecutive failures
            multiplier = min(2 ** (self.metrics.consecutive_failures - 1), 32)
            base_timeout = min(base_timeout * multiplier, self.config.max_timeout)
        
        if self.config.jitter:
            # Add jitter (±25%) to prevent thundering herd
            import random
            jitter = random.uniform(-0.25, 0.25)
            base_timeout *= (1 + jitter)
        
        return base_timeout
    
    async def _record_success(self, duration: float):
        """Record a successful call"""
        
        self.metrics.total_requests += 1
        self.metrics.consecutive_successes += 1
        self.metrics.consecutive_failures = 0
        self.metrics.last_success = datetime.utcnow()
        
        # Update latency tracking
        self.latency_window.append(duration)
        self.metrics.average_latency = statistics.mean(self.latency_window)
        
        # Record in call history
        self.call_history.append({
            'timestamp': datetime.utcnow(),
            'success': True,
            'duration': duration
        })
        
        # Update success rate
        self.metrics.success_rate = self.metrics.calculate_success_rate()
        
        # State transition logic
        if self.state == CircuitBreakerState.HALF_OPEN:
            if self.metrics.consecutive_successes >= self.config.success_threshold:
                await self._transition_to_closed()
        
        # Trigger success callback
        if self.on_success:
            await self.on_success(self, duration)
    
    async def _record_failure(self, duration: float, exception: Exception):
        """Record a failed call"""
        
        self.metrics.total_requests += 1
        self.metrics.error_count += 1
        self.metrics.consecutive_failures += 1
        self.metrics.consecutive_successes = 0
        self.metrics.last_failure = datetime.utcnow()
        self.last_failure_time = self.metrics.last_failure
        
        # Record in call history
        self.call_history.append({
            'timestamp': datetime.utcnow(),
            'success': False,
            'duration': duration,
            'error': str(exception)
        })
        
        # Update success rate
        self.metrics.success_rate = self.metrics.calculate_success_rate()
        
        # State transition logic
        if self.state == CircuitBreakerState.CLOSED:
            if self._should_open_circuit():
                await self._transition_to_open()
        elif self.state == CircuitBreakerState.HALF_OPEN:
            # Any failure in half-open immediately goes back to open
            await self._transition_to_open()
        
        # Trigger failure callback
        if self.on_failure:
            await self.on_failure(self, duration, exception)
    
    def _should_open_circuit(self) -> bool:
        """Determine if circuit should be opened based on failure patterns"""
        
        # Need minimum number of calls to evaluate
        if len(self.call_history) < self.config.minimum_number_of_calls:
            return False
        
        # Check failure threshold
        if self.metrics.consecutive_failures >= self.config.failure_threshold:
            return True
        
        # Check failure rate in sliding window
        recent_calls = list(self.call_history)[-self.config.minimum_number_of_calls:]
        failure_rate = (sum(1 for call in recent_calls if not call['success']) / len(recent_calls)) * 100
        
        if failure_rate > 50:  # 50% failure rate
            return True
        
        # Check slow call rate
        if self._is_slow_call_rate_exceeded():
            return True
        
        return False
    
    def _is_slow_call_rate_exceeded(self) -> bool:
        """Check if slow call rate threshold is exceeded"""
        
        if not self.call_history:
            return False
        
        recent_calls = list(self.call_history)[-self.config.minimum_number_of_calls:]
        slow_calls = sum(
            1 for call in recent_calls 
            if call['duration'] > self.config.slow_call_threshold
        )
        
        slow_call_rate = (slow_calls / len(recent_calls)) * 100
        return slow_call_rate > self.config.slow_call_rate_threshold
    
    async def _transition_to_open(self):
        """Transition circuit breaker to OPEN state"""
        
        previous_state = self.state
        self.state = CircuitBreakerState.OPEN
        self.last_state_change = datetime.utcnow()
        
        # Calculate next attempt time
        timeout = self._calculate_timeout()
        self.next_attempt_time = datetime.utcnow() + timedelta(seconds=timeout)
        
        # Record state change
        self.state_history.append({
            'timestamp': self.last_state_change,
            'from_state': previous_state.value,
            'to_state': self.state.value,
            'trigger': 'failure_threshold_exceeded'
        })
        
        logger.warning(
            f"Circuit breaker '{self.name}' opened. "
            f"Failures: {self.metrics.consecutive_failures}, "
            f"Success rate: {self.metrics.success_rate:.1f}%, "
            f"Next attempt at: {self.next_attempt_time}"
        )
        
        # Trigger state change callback
        if self.on_state_change:
            await self.on_state_change(self, previous_state, self.state)
    
    def _transition_to_half_open(self):
        """Transition circuit breaker to HALF_OPEN state"""
        
        previous_state = self.state
        self.state = CircuitBreakerState.HALF_OPEN
        self.last_state_change = datetime.utcnow()
        self.next_attempt_time = None
        
        # Record state change
        self.state_history.append({
            'timestamp': self.last_state_change,
            'from_state': previous_state.value,
            'to_state': self.state.value,
            'trigger': 'timeout_expired'
        })
        
        logger.info(f"Circuit breaker '{self.name}' transitioned to HALF_OPEN")
    
    async def _transition_to_closed(self):
        """Transition circuit breaker to CLOSED state"""
        
        previous_state = self.state
        self.state = CircuitBreakerState.CLOSED
        self.last_state_change = datetime.utcnow()
        
        # Record state change
        self.state_history.append({
            'timestamp': self.last_state_change,
            'from_state': previous_state.value,
            'to_state': self.state.value,
            'trigger': 'success_threshold_met'
        })
        
        logger.info(
            f"Circuit breaker '{self.name}' closed. "
            f"Successes: {self.metrics.consecutive_successes}"
        )
        
        # Trigger state change callback
        if self.on_state_change:
            await self.on_state_change(self, previous_state, self.state)
    
    def get_status(self) -> Dict[str, Any]:
        """Get current circuit breaker status and metrics"""
        
        return {
            'name': self.name,
            'state': self.state.value,
            'service_level': self.service_level.value,
            'metrics': {
                'success_rate': self.metrics.success_rate,
                'average_latency': self.metrics.average_latency,
                'total_requests': self.metrics.total_requests,
                'error_count': self.metrics.error_count,
                'consecutive_failures': self.metrics.consecutive_failures,
                'consecutive_successes': self.metrics.consecutive_successes,
                'last_success': self.metrics.last_success.isoformat() if self.metrics.last_success else None,
                'last_failure': self.metrics.last_failure.isoformat() if self.metrics.last_failure else None
            },
            'config': {
                'failure_threshold': self.config.failure_threshold,
                'success_threshold': self.config.success_threshold,
                'timeout': self.config.timeout,
                'slow_call_threshold': self.config.slow_call_threshold
            },
            'timing': {
                'last_state_change': self.last_state_change.isoformat(),
                'next_attempt_time': self.next_attempt_time.isoformat() if self.next_attempt_time else None
            }
        }
    
    def reset(self):
        """Manually reset the circuit breaker to CLOSED state"""
        
        self.state = CircuitBreakerState.CLOSED
        self.metrics.consecutive_failures = 0
        self.metrics.consecutive_successes = 0
        self.last_failure_time = None
        self.next_attempt_time = None
        self.last_state_change = datetime.utcnow()
        
        logger.info(f"Circuit breaker '{self.name}' manually reset")


class CircuitOpenException(Exception):
    """Exception raised when circuit breaker is open"""
    pass


@dataclass
class ProviderConfig:
    """Configuration for a data provider"""
    name: str
    priority: int                           # Lower number = higher priority
    service_level: ServiceLevel
    circuit_breaker_config: CircuitBreakerConfig
    timeout: float = 10.0                   # Default timeout for calls
    max_retries: int = 3                    # Maximum retry attempts
    retry_delay: float = 1.0                # Delay between retries
    health_check_interval: int = 300        # Health check interval (seconds)
    
    # Provider-specific settings
    cost_per_request: float = 0.0
    rate_limit: int = 1000                  # Requests per minute
    capabilities: List[str] = field(default_factory=list)


class DataSourceFailoverManager:
    """
    Production-grade data source failover manager
    
    Manages multiple data providers with intelligent failover,
    circuit breaker protection, and comprehensive monitoring.
    """
    
    def __init__(self):
        self.providers: Dict[str, ProviderConfig] = {}
        self.circuit_breakers: Dict[str, EnhancedCircuitBreaker] = {}
        self.health_monitors: Dict[str, Dict[str, Any]] = {}
        
        # Failover configuration
        self.failover_strategies = {
            ServiceLevel.CRITICAL: FailoverStrategy.IMMEDIATE,
            ServiceLevel.HIGH: FailoverStrategy.PROGRESSIVE,
            ServiceLevel.MEDIUM: FailoverStrategy.CONSENSUS,
            ServiceLevel.LOW: FailoverStrategy.ADAPTIVE
        }
        
        # Performance tracking
        self.request_metrics = defaultdict(lambda: {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'average_latency': 0.0,
            'cost_incurred': 0.0
        })
        
        # Event handlers
        self.event_handlers = defaultdict(list)
        
        # Background tasks
        self.monitoring_tasks = {}
        
        self._initialize_default_providers()
        
    def _initialize_default_providers(self):
        """Initialize default provider configurations"""
        
        # Tier 1: Critical providers
        self.add_provider(ProviderConfig(
            name='polygon',
            priority=1,
            service_level=ServiceLevel.CRITICAL,
            circuit_breaker_config=CircuitBreakerConfig(
                failure_threshold=3,
                success_threshold=2,
                timeout=60,
                minimum_number_of_calls=5
            ),
            timeout=5.0,
            cost_per_request=0.004,
            rate_limit=1000,
            capabilities=['real_time', 'historical', 'fundamental']
        ))
        
        self.add_provider(ProviderConfig(
            name='databento',
            priority=2,
            service_level=ServiceLevel.CRITICAL,
            circuit_breaker_config=CircuitBreakerConfig(
                failure_threshold=2,
                success_threshold=3,
                timeout=120,
                minimum_number_of_calls=10
            ),
            timeout=8.0,
            cost_per_request=0.008,
            rate_limit=500,
            capabilities=['real_time', 'tick_data', 'historical']
        ))
        
        # Tier 2: High priority providers
        self.add_provider(ProviderConfig(
            name='alpaca',
            priority=3,
            service_level=ServiceLevel.HIGH,
            circuit_breaker_config=CircuitBreakerConfig(
                failure_threshold=5,
                success_threshold=3,
                timeout=180,
                minimum_number_of_calls=10
            ),
            timeout=10.0,
            cost_per_request=0.002,
            rate_limit=200,
            capabilities=['real_time', 'historical']
        ))
        
        self.add_provider(ProviderConfig(
            name='iex_cloud',
            priority=4,
            service_level=ServiceLevel.HIGH,
            circuit_breaker_config=CircuitBreakerConfig(
                failure_threshold=5,
                success_threshold=4,
                timeout=240,
                minimum_number_of_calls=15
            ),
            timeout=12.0,
            cost_per_request=0.001,
            rate_limit=500,
            capabilities=['real_time', 'fundamental']
        ))
        
        # Tier 3: Backup providers
        self.add_provider(ProviderConfig(
            name='yahoo',
            priority=5,
            service_level=ServiceLevel.LOW,
            circuit_breaker_config=CircuitBreakerConfig(
                failure_threshold=10,
                success_threshold=5,
                timeout=300,
                minimum_number_of_calls=20
            ),
            timeout=15.0,
            cost_per_request=0.0,
            rate_limit=100,
            capabilities=['historical', 'basic_real_time']
        ))
        
        self.add_provider(ProviderConfig(
            name='alpha_vantage',
            priority=6,
            service_level=ServiceLevel.LOW,
            circuit_breaker_config=CircuitBreakerConfig(
                failure_threshold=15,
                success_threshold=8,
                timeout=600,
                minimum_number_of_calls=25
            ),
            timeout=20.0,
            cost_per_request=0.0,
            rate_limit=5,  # Very low rate limit for free tier
            capabilities=['historical', 'fundamental']
        ))
    
    def add_provider(self, config: ProviderConfig):
        """Add a new provider configuration"""
        
        self.providers[config.name] = config
        
        # Create circuit breaker
        circuit_breaker = EnhancedCircuitBreaker(
            name=f"cb_{config.name}",
            config=config.circuit_breaker_config,
            service_level=config.service_level
        )
        
        # Set up event handlers
        circuit_breaker.on_state_change = self._on_circuit_breaker_state_change
        circuit_breaker.on_failure = self._on_provider_failure
        circuit_breaker.on_success = self._on_provider_success
        
        self.circuit_breakers[config.name] = circuit_breaker
        
        # Initialize health monitoring
        self.health_monitors[config.name] = {
            'last_health_check': None,
            'health_status': True,
            'consecutive_health_failures': 0
        }
        
        # Start monitoring task
        if config.name not in self.monitoring_tasks:
            task = asyncio.create_task(self._monitor_provider_health(config.name))
            self.monitoring_tasks[config.name] = task
        
        logger.info(f"Added provider '{config.name}' with priority {config.priority}")
    
    def remove_provider(self, provider_name: str):
        """Remove a provider configuration"""
        
        if provider_name in self.providers:
            del self.providers[provider_name]
        
        if provider_name in self.circuit_breakers:
            del self.circuit_breakers[provider_name]
        
        if provider_name in self.health_monitors:
            del self.health_monitors[provider_name]
        
        if provider_name in self.monitoring_tasks:
            self.monitoring_tasks[provider_name].cancel()
            del self.monitoring_tasks[provider_name]
        
        logger.info(f"Removed provider '{provider_name}'")
    
    async def execute_with_failover(
        self,
        func: Callable,
        capability: str = None,
        service_level: ServiceLevel = ServiceLevel.MEDIUM,
        max_attempts: int = None,
        *args,
        **kwargs
    ) -> Any:
        """
        Execute function with automatic failover across providers
        
        Args:
            func: Function to execute (should accept provider_name as first arg)
            capability: Required capability (e.g., 'real_time', 'historical')
            service_level: Service level requirement
            max_attempts: Maximum number of provider attempts
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result from successful provider
            
        Raises:
            AllProvidersFailedException: If all providers fail
        """
        
        # Select providers based on criteria
        available_providers = self._select_providers(capability, service_level)
        
        if not available_providers:
            raise AllProvidersFailedException(
                f"No providers available for capability '{capability}' "
                f"and service level '{service_level.value}'"
            )
        
        # Limit attempts if specified
        if max_attempts:
            available_providers = available_providers[:max_attempts]
        
        last_exception = None
        
        for provider_name in available_providers:
            try:
                # Execute through circuit breaker
                circuit_breaker = self.circuit_breakers[provider_name]
                provider_config = self.providers[provider_name]
                
                logger.debug(f"Attempting request with provider '{provider_name}'")
                
                result = await circuit_breaker.call(
                    func,
                    provider_name,
                    *args,
                    timeout=provider_config.timeout,
                    **kwargs
                )
                
                # Update metrics
                await self._update_request_metrics(provider_name, True, 0.0)
                
                logger.info(f"Request successful with provider '{provider_name}'")
                return result
                
            except CircuitOpenException as e:
                logger.warning(f"Circuit breaker open for '{provider_name}': {e}")
                last_exception = e
                continue
                
            except Exception as e:
                logger.warning(f"Request failed with provider '{provider_name}': {e}")
                await self._update_request_metrics(provider_name, False, 0.0)
                last_exception = e
                continue
        
        # All providers failed
        await self._handle_all_providers_failed(capability, service_level, last_exception)
        
        raise AllProvidersFailedException(
            f"All {len(available_providers)} providers failed. Last error: {last_exception}"
        )
    
    def _select_providers(
        self,
        capability: str = None,
        service_level: ServiceLevel = ServiceLevel.MEDIUM
    ) -> List[str]:
        """
        Select available providers based on criteria
        
        Args:
            capability: Required capability
            service_level: Minimum service level
            
        Returns:
            List of provider names in priority order
        """
        
        candidates = []
        
        for name, config in self.providers.items():
            # Check service level
            service_levels = [ServiceLevel.LOW, ServiceLevel.MEDIUM, ServiceLevel.HIGH, ServiceLevel.CRITICAL]
            if service_levels.index(config.service_level) < service_levels.index(service_level):
                continue
            
            # Check capability
            if capability and capability not in config.capabilities:
                continue
            
            # Check circuit breaker state
            circuit_breaker = self.circuit_breakers[name]
            if circuit_breaker.state == CircuitBreakerState.OPEN:
                # Skip if circuit is open and can't proceed
                if not circuit_breaker._can_proceed():
                    continue
            
            # Check health status
            if not self.health_monitors[name]['health_status']:
                continue
            
            candidates.append((name, config.priority))
        
        # Sort by priority (lower number = higher priority)
        candidates.sort(key=lambda x: x[1])
        
        return [name for name, _ in candidates]
    
    async def _update_request_metrics(
        self,
        provider_name: str,
        success: bool,
        latency: float
    ):
        """Update request metrics for provider"""
        
        metrics = self.request_metrics[provider_name]
        metrics['total_requests'] += 1
        
        if success:
            metrics['successful_requests'] += 1
        else:
            metrics['failed_requests'] += 1
        
        # Update average latency
        if metrics['total_requests'] > 1:
            metrics['average_latency'] = (
                (metrics['average_latency'] * (metrics['total_requests'] - 1) + latency) 
                / metrics['total_requests']
            )
        else:
            metrics['average_latency'] = latency
        
        # Update cost
        if provider_name in self.providers:
            cost = self.providers[provider_name].cost_per_request
            metrics['cost_incurred'] += cost
    
    async def _monitor_provider_health(self, provider_name: str):
        """Monitor provider health in background"""
        
        if provider_name not in self.providers:
            return
        
        config = self.providers[provider_name]
        
        while True:
            try:
                await asyncio.sleep(config.health_check_interval)
                
                # Perform health check
                health_result = await self._perform_health_check(provider_name)
                
                self.health_monitors[provider_name]['last_health_check'] = datetime.utcnow()
                self.health_monitors[provider_name]['health_status'] = health_result
                
                if health_result:
                    self.health_monitors[provider_name]['consecutive_health_failures'] = 0
                    logger.debug(f"Health check passed for '{provider_name}'")
                else:
                    self.health_monitors[provider_name]['consecutive_health_failures'] += 1
                    logger.warning(
                        f"Health check failed for '{provider_name}' "
                        f"(consecutive failures: {self.health_monitors[provider_name]['consecutive_health_failures']})"
                    )
                
            except Exception as e:
                logger.error(f"Error monitoring health for '{provider_name}': {e}")
                await asyncio.sleep(60)  # Wait longer on error
    
    async def _perform_health_check(self, provider_name: str) -> bool:
        """Perform health check for provider"""
        
        try:
            # This would typically make a simple API call to test the provider
            # For now, we'll simulate based on circuit breaker state
            
            circuit_breaker = self.circuit_breakers[provider_name]
            
            # Consider healthy if circuit is not open or has recent successes
            if circuit_breaker.state == CircuitBreakerState.CLOSED:
                return True
            
            if circuit_breaker.state == CircuitBreakerState.HALF_OPEN:
                return True  # Might recover
            
            # Open circuit - unhealthy unless timeout has passed
            if circuit_breaker.state == CircuitBreakerState.OPEN:
                return circuit_breaker._should_attempt_reset()
            
            return False
            
        except Exception as e:
            logger.error(f"Health check error for '{provider_name}': {e}")
            return False
    
    async def _on_circuit_breaker_state_change(
        self,
        circuit_breaker: EnhancedCircuitBreaker,
        from_state: CircuitBreakerState,
        to_state: CircuitBreakerState
    ):
        """Handle circuit breaker state changes"""
        
        provider_name = circuit_breaker.name.replace('cb_', '')
        
        logger.info(
            f"Circuit breaker state change for '{provider_name}': "
            f"{from_state.value} -> {to_state.value}"
        )
        
        # Trigger event handlers
        await self._trigger_event('circuit_breaker_state_change', {
            'provider_name': provider_name,
            'from_state': from_state.value,
            'to_state': to_state.value,
            'timestamp': datetime.utcnow()
        })
        
        # If critical provider goes down, trigger immediate failover preparation
        if (to_state == CircuitBreakerState.OPEN and 
            self.providers[provider_name].service_level == ServiceLevel.CRITICAL):
            
            await self._prepare_critical_failover(provider_name)
    
    async def _on_provider_failure(
        self,
        circuit_breaker: EnhancedCircuitBreaker,
        duration: float,
        exception: Exception
    ):
        """Handle provider failure"""
        
        provider_name = circuit_breaker.name.replace('cb_', '')
        
        await self._trigger_event('provider_failure', {
            'provider_name': provider_name,
            'duration': duration,
            'error': str(exception),
            'consecutive_failures': circuit_breaker.metrics.consecutive_failures,
            'timestamp': datetime.utcnow()
        })
    
    async def _on_provider_success(
        self,
        circuit_breaker: EnhancedCircuitBreaker,
        duration: float
    ):
        """Handle provider success"""
        
        provider_name = circuit_breaker.name.replace('cb_', '')
        
        await self._trigger_event('provider_success', {
            'provider_name': provider_name,
            'duration': duration,
            'consecutive_successes': circuit_breaker.metrics.consecutive_successes,
            'timestamp': datetime.utcnow()
        })
    
    async def _prepare_critical_failover(self, failed_provider: str):
        """Prepare for critical provider failover"""
        
        logger.critical(f"Critical provider '{failed_provider}' failed - preparing failover")
        
        # Pre-warm backup connections, adjust timeouts, etc.
        # This would be customized based on specific requirements
        
        await self._trigger_event('critical_failover_preparation', {
            'failed_provider': failed_provider,
            'timestamp': datetime.utcnow()
        })
    
    async def _handle_all_providers_failed(
        self,
        capability: str,
        service_level: ServiceLevel,
        last_exception: Exception
    ):
        """Handle scenario where all providers have failed"""
        
        logger.critical(
            f"ALL PROVIDERS FAILED for capability '{capability}' "
            f"and service level '{service_level.value}'. Last error: {last_exception}"
        )
        
        await self._trigger_event('all_providers_failed', {
            'capability': capability,
            'service_level': service_level.value,
            'last_error': str(last_exception),
            'timestamp': datetime.utcnow()
        })
    
    async def _trigger_event(self, event_type: str, data: Dict[str, Any]):
        """Trigger event handlers"""
        
        handlers = self.event_handlers.get(event_type, [])
        
        for handler in handlers:
            try:
                await handler(data)
            except Exception as e:
                logger.error(f"Error in event handler for '{event_type}': {e}")
    
    def on(self, event_type: str, handler: Callable):
        """Register event handler"""
        self.event_handlers[event_type].append(handler)
    
    async def get_status(self) -> Dict[str, Any]:
        """Get comprehensive status of all providers and circuit breakers"""
        
        status = {
            'timestamp': datetime.utcnow().isoformat(),
            'providers': {},
            'overall_health': True,
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'total_cost': 0.0
        }
        
        for provider_name in self.providers:
            provider_config = self.providers[provider_name]
            circuit_breaker = self.circuit_breakers[provider_name]
            health_monitor = self.health_monitors[provider_name]
            metrics = self.request_metrics[provider_name]
            
            provider_status = {
                'name': provider_name,
                'priority': provider_config.priority,
                'service_level': provider_config.service_level.value,
                'capabilities': provider_config.capabilities,
                'circuit_breaker': circuit_breaker.get_status(),
                'health': {
                    'status': health_monitor['health_status'],
                    'last_check': health_monitor['last_health_check'].isoformat() if health_monitor['last_health_check'] else None,
                    'consecutive_failures': health_monitor['consecutive_health_failures']
                },
                'metrics': metrics.copy(),
                'config': {
                    'timeout': provider_config.timeout,
                    'cost_per_request': provider_config.cost_per_request,
                    'rate_limit': provider_config.rate_limit
                }
            }
            
            status['providers'][provider_name] = provider_status
            
            # Aggregate metrics
            status['total_requests'] += metrics['total_requests']
            status['successful_requests'] += metrics['successful_requests']
            status['failed_requests'] += metrics['failed_requests']
            status['total_cost'] += metrics['cost_incurred']
            
            # Overall health check
            if (circuit_breaker.state == CircuitBreakerState.OPEN or 
                not health_monitor['health_status']):
                if provider_config.service_level in [ServiceLevel.CRITICAL, ServiceLevel.HIGH]:
                    status['overall_health'] = False
        
        return status
    
    async def reset_provider(self, provider_name: str):
        """Manually reset a provider's circuit breaker"""
        
        if provider_name in self.circuit_breakers:
            self.circuit_breakers[provider_name].reset()
            
            # Reset health status
            self.health_monitors[provider_name]['health_status'] = True
            self.health_monitors[provider_name]['consecutive_health_failures'] = 0
            
            logger.info(f"Manually reset provider '{provider_name}'")
        else:
            raise ValueError(f"Provider '{provider_name}' not found")
    
    async def shutdown(self):
        """Shutdown the failover manager and cleanup resources"""
        
        # Cancel all monitoring tasks
        for task in self.monitoring_tasks.values():
            task.cancel()
        
        # Wait for tasks to complete
        if self.monitoring_tasks:
            await asyncio.gather(*self.monitoring_tasks.values(), return_exceptions=True)
        
        logger.info("DataSourceFailoverManager shutdown complete")


class AllProvidersFailedException(Exception):
    """Exception raised when all providers have failed"""
    pass


# Global instance for use throughout the application
failover_manager = DataSourceFailoverManager()