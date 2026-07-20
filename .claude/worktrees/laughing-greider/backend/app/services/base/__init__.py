"""
Base Service Classes for Dependency Injection and Service Architecture

This module provides base classes and patterns for service implementation including:
- Service base class with dependency injection
- Repository pattern implementation
- Transaction management
- Error handling and logging
"""

from .base_service import BaseService
from .base_repository import BaseRepository
from .dependency_injection import ServiceRegistry, inject
from .transaction_manager import TransactionManager

__all__ = [
    "BaseService",
    "BaseRepository", 
    "ServiceRegistry",
    "inject",
    "TransactionManager"
]