"""
Base Service Class with Dependency Injection and Standard Patterns

Provides foundation for all business logic services with common functionality including:
- Dependency injection
- Transaction management
- Error handling and logging
- Audit trail integration
- Performance monitoring
"""

import asyncio
import logging
import time
import uuid
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional, Type, TypeVar, Generic

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.infrastructure.database import db_manager, timescale_manager

# Generic type for service responses
T = TypeVar('T')

logger = logging.getLogger(__name__)


class ServiceResult(Generic[T]):
    """
    Standardized service result with success/failure indicators and metadata
    """
    
    def __init__(
        self,
        data: Optional[T] = None,
        success: bool = True,
        error: Optional[str] = None,
        error_code: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        execution_time_ms: Optional[float] = None
    ):
        self.data = data
        self.success = success
        self.error = error
        self.error_code = error_code
        self.metadata = metadata or {}
        self.execution_time_ms = execution_time_ms
        self.request_id = str(uuid.uuid4())
        
    @classmethod
    def success_result(
        cls, 
        data: T, 
        metadata: Optional[Dict[str, Any]] = None,
        execution_time_ms: Optional[float] = None
    ) -> 'ServiceResult[T]':
        """Create a successful service result"""
        return cls(
            data=data,
            success=True,
            metadata=metadata,
            execution_time_ms=execution_time_ms
        )
    
    @classmethod
    def error_result(
        cls,
        error: str,
        error_code: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        execution_time_ms: Optional[float] = None
    ) -> 'ServiceResult[None]':
        """Create an error service result"""
        return cls(
            success=False,
            error=error,
            error_code=error_code,
            metadata=metadata,
            execution_time_ms=execution_time_ms
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary for serialization"""
        return {
            'success': self.success,
            'data': self.data,
            'error': self.error,
            'error_code': self.error_code,
            'metadata': self.metadata,
            'request_id': self.request_id,
            'execution_time_ms': self.execution_time_ms
        }


class BaseService(ABC):
    """
    Abstract base service class providing common functionality for all business services
    """
    
    def __init__(
        self,
        db_session: Optional[AsyncSession] = None,
        timescale_session: Optional[AsyncSession] = None,
        user_id: Optional[uuid.UUID] = None,
        request_id: Optional[str] = None
    ):
        self.db_session = db_session
        self.timescale_session = timescale_session
        self.user_id = user_id
        self.request_id = request_id or str(uuid.uuid4())
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Performance tracking
        self._start_time: Optional[float] = None
        self._operation_metrics: Dict[str, Any] = {}
    
    @asynccontextmanager
    async def get_db_session(self) -> AsyncSession:
        """Get database session, using injected session or creating new one"""
        if self.db_session:
            yield self.db_session
        else:
            async with db_manager.get_async_session() as session:
                yield session
    
    @asynccontextmanager
    async def get_timescale_session(self) -> AsyncSession:
        """Get TimescaleDB session for time-series operations"""
        if self.timescale_session:
            yield self.timescale_session
        else:
            async with timescale_manager.get_async_session() as session:
                yield session
    
    def start_operation(self, operation_name: str) -> None:
        """Start tracking an operation for performance monitoring"""
        self._start_time = time.time()
        self._operation_metrics = {
            'operation': operation_name,
            'request_id': self.request_id,
            'user_id': str(self.user_id) if self.user_id else None,
            'service': self.__class__.__name__
        }
        
        self.logger.info(
            f"Starting operation: {operation_name}",
            extra=self._operation_metrics
        )
    
    def complete_operation(self, success: bool = True, error: Optional[str] = None) -> float:
        """Complete operation tracking and return execution time"""
        execution_time = (time.time() - self._start_time) * 1000 if self._start_time else 0
        
        self._operation_metrics.update({
            'execution_time_ms': execution_time,
            'success': success,
            'error': error
        })
        
        log_level = logging.INFO if success else logging.ERROR
        message = f"Operation completed: {self._operation_metrics['operation']}"
        
        self.logger.log(log_level, message, extra=self._operation_metrics)
        
        return execution_time
    
    async def execute_with_tracking(
        self,
        operation_name: str,
        operation_func,
        *args,
        **kwargs
    ) -> ServiceResult[Any]:
        """Execute an operation with automatic performance tracking and error handling"""
        self.start_operation(operation_name)
        
        try:
            result = await operation_func(*args, **kwargs)
            execution_time = self.complete_operation(success=True)
            
            if isinstance(result, ServiceResult):
                result.execution_time_ms = execution_time
                return result
            else:
                return ServiceResult.success_result(
                    data=result,
                    execution_time_ms=execution_time
                )
                
        except Exception as e:
            execution_time = self.complete_operation(success=False, error=str(e))
            
            self.logger.error(
                f"Operation failed: {operation_name}",
                exc_info=True,
                extra={
                    'request_id': self.request_id,
                    'user_id': str(self.user_id) if self.user_id else None,
                    'error': str(e)
                }
            )
            
            return ServiceResult.error_result(
                error=str(e),
                error_code=e.__class__.__name__,
                execution_time_ms=execution_time
            )
    
    async def audit_action(
        self,
        action: str,
        resource_type: str,
        resource_id: Optional[uuid.UUID] = None,
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Record audit trail for service actions"""
        try:
            from app.models.base import AuditLog
            
            audit_entry = AuditLog(
                user_id=self.user_id,
                request_id=uuid.UUID(self.request_id) if self.request_id else None,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                old_values=old_values,
                new_values=new_values,
                metadata=metadata or {},
                execution_time_ms=int(self._operation_metrics.get('execution_time_ms', 0))
            )
            
            async with self.get_db_session() as session:
                session.add(audit_entry)
                await session.commit()
                
        except Exception as e:
            self.logger.error(f"Failed to create audit log: {e}", exc_info=True)
    
    @abstractmethod
    async def validate_input(self, data: Dict[str, Any]) -> ServiceResult[Dict[str, Any]]:
        """Validate service input data - must be implemented by subclasses"""
        pass
    
    async def health_check(self) -> ServiceResult[Dict[str, Any]]:
        """Perform health check for this service"""
        health_data = {
            'service': self.__class__.__name__,
            'status': 'healthy',
            'dependencies': {}
        }
        
        try:
            # Check database connectivity
            async with self.get_db_session() as session:
                await session.execute('SELECT 1')
                health_data['dependencies']['database'] = 'healthy'
        except Exception as e:
            health_data['dependencies']['database'] = f'unhealthy: {str(e)}'
            health_data['status'] = 'unhealthy'
        
        try:
            # Check TimescaleDB connectivity if used by service
            if hasattr(self, 'uses_timescaledb') and self.uses_timescaledb:
                async with self.get_timescale_session() as session:
                    await session.execute('SELECT 1')
                    health_data['dependencies']['timescaledb'] = 'healthy'
        except Exception as e:
            health_data['dependencies']['timescaledb'] = f'unhealthy: {str(e)}'
            health_data['status'] = 'degraded'
        
        return ServiceResult.success_result(health_data)


class ReadOnlyService(BaseService):
    """
    Base class for read-only services that don't modify data
    Provides optimizations for read-only operations
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.read_only = True
    
    async def audit_action(self, *args, **kwargs) -> None:
        """Override audit action for read-only services to reduce logging overhead"""
        # Only audit if explicitly required for read operations
        if settings.AUDIT_READ_OPERATIONS:
            await super().audit_action(*args, **kwargs)


class CachedService(BaseService):
    """
    Base class for services that utilize caching
    Provides cache management utilities
    """
    
    def __init__(self, *args, cache_client=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.cache_client = cache_client
        self.cache_prefix = f"{self.__class__.__name__}:"
        self.default_ttl = 3600  # 1 hour
    
    def get_cache_key(self, *key_parts: str) -> str:
        """Generate standardized cache key"""
        return f"{self.cache_prefix}{':'.join(str(part) for part in key_parts)}"
    
    async def get_cached_result(
        self,
        cache_key: str,
        result_type: Type[T] = dict
    ) -> Optional[T]:
        """Get result from cache with type safety"""
        if not self.cache_client:
            return None
            
        try:
            cached_data = await self.cache_client.get(cache_key)
            if cached_data:
                self.logger.debug(f"Cache hit for key: {cache_key}")
                return cached_data
            else:
                self.logger.debug(f"Cache miss for key: {cache_key}")
                return None
        except Exception as e:
            self.logger.warning(f"Cache get failed for key {cache_key}: {e}")
            return None
    
    async def set_cached_result(
        self,
        cache_key: str,
        data: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """Set result in cache"""
        if not self.cache_client:
            return False
            
        try:
            await self.cache_client.set(
                cache_key,
                data,
                expire=ttl or self.default_ttl
            )
            self.logger.debug(f"Cache set for key: {cache_key}")
            return True
        except Exception as e:
            self.logger.warning(f"Cache set failed for key {cache_key}: {e}")
            return False
    
    async def invalidate_cache(self, pattern: str) -> int:
        """Invalidate cache entries matching pattern"""
        if not self.cache_client:
            return 0
            
        try:
            keys = await self.cache_client.keys(pattern)
            if keys:
                deleted = await self.cache_client.delete(*keys)
                self.logger.info(f"Invalidated {deleted} cache entries for pattern: {pattern}")
                return deleted
            return 0
        except Exception as e:
            self.logger.warning(f"Cache invalidation failed for pattern {pattern}: {e}")
            return 0


class BatchProcessingService(BaseService):
    """
    Base class for services that process data in batches
    Provides utilities for batch operations and progress tracking
    """
    
    def __init__(self, *args, batch_size: int = 100, **kwargs):
        super().__init__(*args, **kwargs)
        self.batch_size = batch_size
        self.processing_stats = {
            'total_items': 0,
            'processed_items': 0,
            'failed_items': 0,
            'start_time': None,
            'batches_processed': 0
        }
    
    async def process_in_batches(
        self,
        items: List[Any],
        processor_func,
        progress_callback: Optional[callable] = None
    ) -> ServiceResult[Dict[str, Any]]:
        """Process items in batches with progress tracking"""
        self.processing_stats['total_items'] = len(items)
        self.processing_stats['start_time'] = time.time()
        
        results = []
        failed_items = []
        
        for i in range(0, len(items), self.batch_size):
            batch = items[i:i + self.batch_size]
            batch_number = (i // self.batch_size) + 1
            
            try:
                batch_results = await processor_func(batch)
                results.extend(batch_results)
                self.processing_stats['processed_items'] += len(batch)
                self.processing_stats['batches_processed'] += 1
                
                if progress_callback:
                    await progress_callback(self.processing_stats, batch_number)
                    
            except Exception as e:
                failed_items.extend(batch)
                self.processing_stats['failed_items'] += len(batch)
                self.logger.error(f"Batch {batch_number} failed: {e}", exc_info=True)
        
        processing_time = time.time() - self.processing_stats['start_time']
        
        return ServiceResult.success_result(
            data={
                'results': results,
                'failed_items': failed_items,
                'stats': {
                    **self.processing_stats,
                    'processing_time_seconds': processing_time,
                    'items_per_second': self.processing_stats['processed_items'] / processing_time if processing_time > 0 else 0
                }
            },
            execution_time_ms=processing_time * 1000
        )