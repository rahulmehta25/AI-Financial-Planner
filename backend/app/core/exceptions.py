"""
Core Exceptions for the AI Financial Planning System

Custom exception classes for handling various error scenarios
in a consistent and informative way.
"""

from typing import Any, Dict, Optional
from fastapi import HTTPException, status


class CustomException(HTTPException):
    """Base custom exception class"""
    
    def __init__(
        self,
        detail: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code: Optional[str] = None,
        headers: Optional[Dict[str, Any]] = None
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)
        self.error_code = error_code


class ValidationError(CustomException):
    """Raised when input validation fails"""
    
    def __init__(self, detail: str, error_code: str = "VALIDATION_ERROR"):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code=error_code
        )


class NotFoundError(CustomException):
    """Raised when a requested resource is not found"""
    
    def __init__(self, detail: str, error_code: str = "NOT_FOUND"):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_404_NOT_FOUND,
            error_code=error_code
        )


class AuthenticationError(CustomException):
    """Raised when authentication fails"""
    
    def __init__(self, detail: str = "Authentication failed", error_code: str = "AUTHENTICATION_ERROR"):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code=error_code
        )


class AuthorizationError(CustomException):
    """Raised when authorization fails"""
    
    def __init__(self, detail: str = "Insufficient permissions", error_code: str = "AUTHORIZATION_ERROR"):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_403_FORBIDDEN,
            error_code=error_code
        )


class SimulationError(CustomException):
    """Raised when simulation operations fail"""
    
    def __init__(self, detail: str, error_code: str = "SIMULATION_ERROR"):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code=error_code
        )


class DatabaseError(CustomException):
    """Raised when database operations fail"""
    
    def __init__(self, detail: str, error_code: str = "DATABASE_ERROR"):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code=error_code
        )


class ExternalServiceError(CustomException):
    """Raised when external service calls fail"""
    
    def __init__(self, detail: str, error_code: str = "EXTERNAL_SERVICE_ERROR"):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_502_BAD_GATEWAY,
            error_code=error_code
        )


class RateLimitError(CustomException):
    """Raised when rate limits are exceeded"""
    
    def __init__(self, detail: str = "Rate limit exceeded", error_code: str = "RATE_LIMIT_ERROR"):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            error_code=error_code
        )


class ConfigurationError(CustomException):
    """Raised when system configuration is invalid"""
    
    def __init__(self, detail: str, error_code: str = "CONFIGURATION_ERROR"):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code=error_code
        )


class AIProcessingError(CustomException):
    """Raised when AI/LLM processing fails"""
    
    def __init__(self, detail: str, error_code: str = "AI_PROCESSING_ERROR"):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code=error_code
        )


class ComplianceError(CustomException):
    """Raised when compliance requirements are not met"""
    
    def __init__(self, detail: str, error_code: str = "COMPLIANCE_ERROR"):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code=error_code
        )


class AuditError(CustomException):
    """Raised when audit logging fails"""
    
    def __init__(self, detail: str, error_code: str = "AUDIT_ERROR"):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code=error_code
        )


class PDFGenerationError(CustomException):
    """Raised when PDF generation fails"""
    
    def __init__(self, detail: str, error_code: str = "PDF_GENERATION_ERROR"):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code=error_code
        )


# Exception mapping for common HTTP status codes
EXCEPTION_MAPPING = {
    400: ValidationError,
    401: AuthenticationError,
    403: AuthorizationError,
    404: NotFoundError,
    429: RateLimitError,
    500: CustomException,
    502: ExternalServiceError
}


def create_exception(status_code: int, detail: str, error_code: Optional[str] = None) -> CustomException:
    """Create an appropriate exception based on status code"""
    
    exception_class = EXCEPTION_MAPPING.get(status_code, CustomException)
    return exception_class(detail=detail, error_code=error_code)