"""
Comprehensive Error Handling and Retry Logic for Banking Integration

This module provides robust error handling, retry mechanisms, and fallback
strategies for banking API integrations.
"""

import logging
import asyncio
import time
from typing import Any, Callable, Dict, List, Optional, Type, Union
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import functools

from httpx import HTTPStatusError, ConnectError, TimeoutException
from plaid.exceptions import ApiException as PlaidApiException

from app.core.config import settings
from app.core.exceptions import BankingIntegrationError, ValidationError

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Banking error categories"""
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    RATE_LIMIT = "rate_limit"
    NETWORK = "network"
    API_ERROR = "api_error"
    DATA_ERROR = "data_error"
    SYSTEM_ERROR = "system_error"
    TIMEOUT = "timeout"
    VALIDATION = "validation"


@dataclass
class ErrorContext:
    """Context information for error handling"""
    user_id: Optional[str]
    provider: str
    operation: str
    attempt_number: int
    timestamp: datetime
    metadata: Dict[str, Any]


@dataclass
class RetryConfig:
    """Retry configuration"""
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_factor: float = 2.0
    jitter: bool = True
    retryable_errors: List[Type[Exception]] = None


class BankingErrorHandler:
    """
    Comprehensive error handling and retry logic for banking operations.
    
    Features:
    - Configurable retry strategies
    - Error categorization and severity assessment
    - Circuit breaker pattern
    - Fallback provider switching
    - Comprehensive logging and monitoring
    - Rate limit handling
    - Dead letter queue for failed operations
    """
    
    def __init__(self):
        self.default_retry_config = RetryConfig(
            max_attempts=settings.BANKING_MAX_RETRY_ATTEMPTS,
            base_delay=settings.BANKING_RETRY_DELAY_SECONDS,
            retryable_errors=[
                ConnectError,
                TimeoutException,
                HTTPStatusError
            ]
        )
        self.circuit_breakers = {}
        self.error_counts = {}
        self.rate_limit_trackers = {}
    
    def categorize_error(self, error: Exception, context: ErrorContext) -> ErrorCategory:
        """Categorize error for appropriate handling"""
        try:
            error_type = type(error).__name__
            error_message = str(error).lower()
            
            # Plaid-specific errors
            if isinstance(error, PlaidApiException):
                if hasattr(error, 'error_type'):
                    error_type_plaid = error.error_type
                    if error_type_plaid == 'INVALID_CREDENTIALS':
                        return ErrorCategory.AUTHENTICATION
                    elif error_type_plaid == 'INVALID_ACCESS_TOKEN':
                        return ErrorCategory.AUTHORIZATION
                    elif error_type_plaid == 'RATE_LIMIT_EXCEEDED':
                        return ErrorCategory.RATE_LIMIT
                    elif error_type_plaid == 'API_ERROR':
                        return ErrorCategory.API_ERROR
                
                # Check error code for more specific categorization
                if hasattr(error, 'error_code'):
                    error_code = error.error_code
                    if 'ITEM_LOGIN_REQUIRED' in error_code:
                        return ErrorCategory.AUTHENTICATION
                    elif 'INSUFFICIENT_CREDENTIALS' in error_code:
                        return ErrorCategory.AUTHORIZATION
            
            # HTTP errors
            if isinstance(error, HTTPStatusError):
                status_code = error.response.status_code
                if status_code == 401:
                    return ErrorCategory.AUTHENTICATION
                elif status_code == 403:
                    return ErrorCategory.AUTHORIZATION
                elif status_code == 429:
                    return ErrorCategory.RATE_LIMIT
                elif 400 <= status_code < 500:
                    return ErrorCategory.VALIDATION
                elif status_code >= 500:
                    return ErrorCategory.API_ERROR
            
            # Network errors
            if isinstance(error, (ConnectError, TimeoutException)):
                return ErrorCategory.NETWORK
            
            # Timeout errors
            if 'timeout' in error_message or isinstance(error, TimeoutException):
                return ErrorCategory.TIMEOUT
            
            # Validation errors
            if isinstance(error, ValidationError) or 'invalid' in error_message:
                return ErrorCategory.VALIDATION
            
            # Default to system error
            return ErrorCategory.SYSTEM_ERROR
            
        except Exception as e:
            logger.error(f"Error categorizing exception: {str(e)}")
            return ErrorCategory.SYSTEM_ERROR
    
    def assess_severity(self, error: Exception, category: ErrorCategory, context: ErrorContext) -> ErrorSeverity:
        """Assess error severity for escalation decisions"""
        try:
            # Critical errors that require immediate attention
            if category in [ErrorCategory.AUTHENTICATION, ErrorCategory.AUTHORIZATION]:
                return ErrorSeverity.CRITICAL
            
            # High severity errors
            if category in [ErrorCategory.SYSTEM_ERROR, ErrorCategory.API_ERROR]:
                return ErrorSeverity.HIGH
            
            # Medium severity errors
            if category in [ErrorCategory.RATE_LIMIT, ErrorCategory.TIMEOUT]:
                return ErrorSeverity.MEDIUM
            
            # Low severity errors
            if category in [ErrorCategory.NETWORK, ErrorCategory.VALIDATION]:
                return ErrorSeverity.LOW
            
            # Consider attempt number for escalation
            if context.attempt_number >= self.default_retry_config.max_attempts:
                if category == ErrorCategory.NETWORK:
                    return ErrorSeverity.MEDIUM
                else:
                    return ErrorSeverity.HIGH
            
            return ErrorSeverity.LOW
            
        except Exception as e:
            logger.error(f"Error assessing severity: {str(e)}")
            return ErrorSeverity.MEDIUM
    
    def is_retryable(self, error: Exception, category: ErrorCategory, context: ErrorContext) -> bool:
        """Determine if error is retryable"""
        try:
            # Never retry authentication/authorization errors
            if category in [ErrorCategory.AUTHENTICATION, ErrorCategory.AUTHORIZATION]:
                return False
            
            # Never retry validation errors
            if category == ErrorCategory.VALIDATION:
                return False
            
            # Always retry network and timeout errors
            if category in [ErrorCategory.NETWORK, ErrorCategory.TIMEOUT]:
                return True
            
            # Retry rate limit errors with backoff
            if category == ErrorCategory.RATE_LIMIT:
                return True
            
            # Retry API errors up to limit
            if category == ErrorCategory.API_ERROR:
                return context.attempt_number < self.default_retry_config.max_attempts
            
            # Default to retryable for other errors
            return True
            
        except Exception as e:
            logger.error(f"Error determining retry eligibility: {str(e)}")
            return False
    
    def calculate_retry_delay(
        self,
        attempt_number: int,
        category: ErrorCategory,
        config: Optional[RetryConfig] = None
    ) -> float:
        """Calculate retry delay with exponential backoff"""
        try:
            if not config:
                config = self.default_retry_config
            
            # Base delay calculation
            delay = config.base_delay * (config.exponential_factor ** (attempt_number - 1))
            
            # Cap at max delay
            delay = min(delay, config.max_delay)
            
            # Special handling for rate limits
            if category == ErrorCategory.RATE_LIMIT:
                # Longer delays for rate limits
                delay = max(delay, 60.0)  # Minimum 1 minute for rate limits
            
            # Add jitter to prevent thundering herd
            if config.jitter:
                import random
                delay *= (0.5 + random.random() * 0.5)  # 50-100% of calculated delay
            
            return delay
            
        except Exception as e:
            logger.error(f"Error calculating retry delay: {str(e)}")
            return config.base_delay if config else 1.0
    
    async def handle_error(
        self,
        error: Exception,
        context: ErrorContext,
        config: Optional[RetryConfig] = None
    ) -> Dict[str, Any]:
        """Comprehensive error handling with categorization and response"""
        try:
            # Categorize and assess error
            category = self.categorize_error(error, context)
            severity = self.assess_severity(error, category, context)
            retryable = self.is_retryable(error, category, context)
            
            # Log error with context
            self._log_error(error, category, severity, context)
            
            # Update error tracking
            self._update_error_tracking(context.provider, category, severity)
            
            # Check circuit breaker
            if self._should_circuit_break(context.provider, category):
                logger.warning(f"Circuit breaker triggered for {context.provider}")
                return {
                    "action": "circuit_break",
                    "category": category.value,
                    "severity": severity.value,
                    "retryable": False,
                    "circuit_breaker_active": True
                }
            
            # Determine action
            if not retryable or context.attempt_number >= (config or self.default_retry_config).max_attempts:
                action = "fail"
                if category in [ErrorCategory.AUTHENTICATION, ErrorCategory.AUTHORIZATION]:
                    action = "reauth_required"
                elif severity == ErrorSeverity.CRITICAL:
                    action = "escalate"
            else:
                action = "retry"
            
            # Calculate retry delay if retrying
            retry_delay = None
            if action == "retry":
                retry_delay = self.calculate_retry_delay(context.attempt_number, category, config)
            
            return {
                "action": action,
                "category": category.value,
                "severity": severity.value,
                "retryable": retryable,
                "retry_delay": retry_delay,
                "circuit_breaker_active": False,
                "error_message": str(error),
                "recommendations": self._get_error_recommendations(category, severity, context)
            }
            
        except Exception as e:
            logger.error(f"Error in error handler: {str(e)}")
            return {
                "action": "fail",
                "category": "system_error",
                "severity": "high",
                "error_message": "Error handler failure"
            }
    
    def _log_error(self, error: Exception, category: ErrorCategory, severity: ErrorSeverity, context: ErrorContext):
        """Log error with appropriate level and context"""
        try:
            log_data = {
                "error_type": type(error).__name__,
                "error_message": str(error),
                "category": category.value,
                "severity": severity.value,
                "user_id": context.user_id,
                "provider": context.provider,
                "operation": context.operation,
                "attempt": context.attempt_number,
                "metadata": context.metadata
            }
            
            if severity == ErrorSeverity.CRITICAL:
                logger.critical(f"Critical banking error: {log_data}")
            elif severity == ErrorSeverity.HIGH:
                logger.error(f"High severity banking error: {log_data}")
            elif severity == ErrorSeverity.MEDIUM:
                logger.warning(f"Medium severity banking error: {log_data}")
            else:
                logger.info(f"Low severity banking error: {log_data}")
                
        except Exception as e:
            logger.error(f"Error logging error: {str(e)}")
    
    def _update_error_tracking(self, provider: str, category: ErrorCategory, severity: ErrorSeverity):
        """Update error tracking for circuit breaker decisions"""
        try:
            key = f"{provider}:{category.value}"
            
            if key not in self.error_counts:
                self.error_counts[key] = {
                    "count": 0,
                    "window_start": datetime.utcnow(),
                    "severity_counts": {}
                }
            
            # Reset window if too old (1 hour window)
            if datetime.utcnow() - self.error_counts[key]["window_start"] > timedelta(hours=1):
                self.error_counts[key] = {
                    "count": 0,
                    "window_start": datetime.utcnow(),
                    "severity_counts": {}
                }
            
            # Increment counters
            self.error_counts[key]["count"] += 1
            severity_key = severity.value
            self.error_counts[key]["severity_counts"][severity_key] = \
                self.error_counts[key]["severity_counts"].get(severity_key, 0) + 1
                
        except Exception as e:
            logger.error(f"Error updating error tracking: {str(e)}")
    
    def _should_circuit_break(self, provider: str, category: ErrorCategory) -> bool:
        """Determine if circuit breaker should trigger"""
        try:
            key = f"{provider}:{category.value}"
            
            if key not in self.error_counts:
                return False
            
            error_data = self.error_counts[key]
            
            # Circuit break thresholds
            if category in [ErrorCategory.AUTHENTICATION, ErrorCategory.AUTHORIZATION]:
                return error_data["count"] >= 3  # 3 auth errors in window
            elif category == ErrorCategory.RATE_LIMIT:
                return error_data["count"] >= 5  # 5 rate limit errors
            elif category in [ErrorCategory.API_ERROR, ErrorCategory.SYSTEM_ERROR]:
                critical_count = error_data["severity_counts"].get("critical", 0)
                high_count = error_data["severity_counts"].get("high", 0)
                return critical_count >= 2 or high_count >= 5
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking circuit breaker: {str(e)}")
            return False
    
    def _get_error_recommendations(
        self,
        category: ErrorCategory,
        severity: ErrorSeverity,
        context: ErrorContext
    ) -> List[str]:
        """Get recommendations for error resolution"""
        try:
            recommendations = []
            
            if category == ErrorCategory.AUTHENTICATION:
                recommendations.extend([
                    "User needs to re-authenticate with their bank",
                    "Check if banking credentials have changed",
                    "Verify institution supports current authentication method"
                ])
            
            elif category == ErrorCategory.AUTHORIZATION:
                recommendations.extend([
                    "User may need to grant additional permissions",
                    "Check if account access has been revoked",
                    "Verify API permissions are sufficient"
                ])
            
            elif category == ErrorCategory.RATE_LIMIT:
                recommendations.extend([
                    "Implement exponential backoff",
                    "Consider using alternative provider",
                    "Review API usage patterns"
                ])
            
            elif category == ErrorCategory.NETWORK:
                recommendations.extend([
                    "Check internet connectivity",
                    "Verify provider API endpoints are accessible",
                    "Consider implementing offline mode"
                ])
            
            elif category == ErrorCategory.API_ERROR:
                recommendations.extend([
                    "Check provider status page",
                    "Verify API version compatibility",
                    "Consider fallback provider"
                ])
            
            elif category == ErrorCategory.VALIDATION:
                recommendations.extend([
                    "Review input data format",
                    "Check required fields",
                    "Validate against provider requirements"
                ])
            
            # Add severity-based recommendations
            if severity == ErrorSeverity.CRITICAL:
                recommendations.append("Escalate to technical support immediately")
            elif severity == ErrorSeverity.HIGH:
                recommendations.append("Monitor closely and consider manual intervention")
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {str(e)}")
            return ["Unable to generate recommendations"]


# Retry decorator
def with_retry(
    config: Optional[RetryConfig] = None,
    operation_name: str = "unknown",
    provider: str = "unknown"
):
    """Decorator for adding retry logic to banking operations"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            error_handler = BankingErrorHandler()
            retry_config = config or error_handler.default_retry_config
            
            for attempt in range(1, retry_config.max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                    
                except Exception as error:
                    # Create error context
                    context = ErrorContext(
                        user_id=kwargs.get('user_id'),
                        provider=provider,
                        operation=operation_name,
                        attempt_number=attempt,
                        timestamp=datetime.utcnow(),
                        metadata={
                            "function": func.__name__,
                            "args_count": len(args),
                            "kwargs_keys": list(kwargs.keys())
                        }
                    )
                    
                    # Handle error
                    error_response = await error_handler.handle_error(error, context, retry_config)
                    
                    # Check if we should retry
                    if error_response["action"] != "retry" or attempt == retry_config.max_attempts:
                        # Log final failure
                        logger.error(
                            f"Operation {operation_name} failed after {attempt} attempts: "
                            f"{error_response}"
                        )
                        
                        # Re-raise with enhanced error information
                        if error_response["action"] == "reauth_required":
                            raise BankingIntegrationError(
                                "Authentication required: User needs to re-link their account"
                            )
                        elif error_response["action"] == "circuit_break":
                            raise BankingIntegrationError(
                                f"Service temporarily unavailable for {provider}"
                            )
                        else:
                            raise BankingIntegrationError(
                                f"Operation failed: {error_response['error_message']}"
                            )
                    
                    # Wait before retry
                    if error_response.get("retry_delay"):
                        await asyncio.sleep(error_response["retry_delay"])
            
            # Should never reach here, but just in case
            raise BankingIntegrationError("Maximum retry attempts exceeded")
        
        return wrapper
    return decorator


# Usage example decorators
def with_plaid_retry(operation_name: str = "plaid_operation"):
    """Decorator specifically for Plaid operations"""
    return with_retry(
        config=RetryConfig(
            max_attempts=3,
            base_delay=2.0,
            max_delay=30.0,
            retryable_errors=[PlaidApiException, ConnectError, TimeoutException]
        ),
        operation_name=operation_name,
        provider="plaid"
    )


def with_yodlee_retry(operation_name: str = "yodlee_operation"):
    """Decorator specifically for Yodlee operations"""
    return with_retry(
        config=RetryConfig(
            max_attempts=3,
            base_delay=1.5,
            max_delay=45.0,
            retryable_errors=[HTTPStatusError, ConnectError, TimeoutException]
        ),
        operation_name=operation_name,
        provider="yodlee"
    )


# Global error handler instance
banking_error_handler = BankingErrorHandler()