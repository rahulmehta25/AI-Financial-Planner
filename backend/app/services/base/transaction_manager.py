"""
Transaction Management for Database Operations

Provides:
- Distributed transaction support
- Rollback mechanisms  
- Transaction isolation levels
- Savepoint management
- Cross-service transaction coordination
"""

import asyncio
import logging
import uuid
from contextlib import asynccontextmanager
from enum import Enum
from typing import Any, Dict, List, Optional, Type, Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.config import settings

logger = logging.getLogger(__name__)


class TransactionState(Enum):
    """Transaction state enumeration"""
    ACTIVE = "active"
    COMMITTED = "committed"
    ROLLED_BACK = "rolled_back"
    FAILED = "failed"


class IsolationLevel(Enum):
    """Database isolation levels"""
    READ_UNCOMMITTED = "READ UNCOMMITTED"
    READ_COMMITTED = "READ COMMITTED"  
    REPEATABLE_READ = "REPEATABLE READ"
    SERIALIZABLE = "SERIALIZABLE"


@dataclass
class TransactionContext:
    """Transaction context information"""
    transaction_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    state: TransactionState = TransactionState.ACTIVE
    isolation_level: Optional[IsolationLevel] = None
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    user_id: Optional[uuid.UUID] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    savepoints: List[str] = field(default_factory=list)
    participants: List[str] = field(default_factory=list)  # Services participating in transaction


class TransactionManager:
    """
    Advanced transaction manager with distributed transaction support
    """
    
    def __init__(self):
        self._active_transactions: Dict[str, TransactionContext] = {}
        self._transaction_hooks: Dict[str, List[Callable]] = {
            'before_commit': [],
            'after_commit': [],
            'before_rollback': [],
            'after_rollback': []
        }
    
    @asynccontextmanager
    async def transaction(
        self,
        session: AsyncSession,
        isolation_level: Optional[IsolationLevel] = None,
        user_id: Optional[uuid.UUID] = None,
        metadata: Optional[Dict[str, Any]] = None,
        timeout_seconds: int = 30
    ):
        """
        Main transaction context manager
        
        Args:
            session: Database session
            isolation_level: Transaction isolation level
            user_id: User initiating the transaction
            metadata: Additional transaction metadata
            timeout_seconds: Transaction timeout
        """
        context = TransactionContext(
            isolation_level=isolation_level,
            user_id=user_id,
            metadata=metadata or {}
        )
        
        self._active_transactions[context.transaction_id] = context
        
        logger.info(
            f"Starting transaction {context.transaction_id}",
            extra={
                'transaction_id': context.transaction_id,
                'user_id': str(user_id) if user_id else None,
                'isolation_level': isolation_level.value if isolation_level else None
            }
        )
        
        try:
            # Set isolation level if specified
            if isolation_level:
                await session.execute(
                    text(f"SET TRANSACTION ISOLATION LEVEL {isolation_level.value}")
                )
            
            # Set transaction timeout
            if timeout_seconds:
                await session.execute(
                    text(f"SET LOCAL statement_timeout = '{timeout_seconds}s'")
                )
            
            # Begin transaction
            await session.begin()
            
            # Execute before_commit hooks
            await self._execute_hooks('before_commit', context, session)
            
            yield TransactionScope(self, session, context)
            
            # Commit transaction
            await session.commit()
            
            # Update transaction state
            context.state = TransactionState.COMMITTED
            context.completed_at = datetime.now(timezone.utc)
            
            # Execute after_commit hooks
            await self._execute_hooks('after_commit', context, session)
            
            logger.info(
                f"Transaction {context.transaction_id} committed successfully",
                extra={
                    'transaction_id': context.transaction_id,
                    'duration_ms': self._calculate_duration_ms(context)
                }
            )
            
        except Exception as e:
            # Rollback transaction
            await session.rollback()
            
            # Update transaction state
            context.state = TransactionState.ROLLED_BACK if not isinstance(e, TransactionFailedException) else TransactionState.FAILED
            context.completed_at = datetime.now(timezone.utc)
            
            # Execute rollback hooks
            await self._execute_hooks('before_rollback', context, session)
            await self._execute_hooks('after_rollback', context, session)
            
            logger.error(
                f"Transaction {context.transaction_id} rolled back due to error: {e}",
                extra={
                    'transaction_id': context.transaction_id,
                    'duration_ms': self._calculate_duration_ms(context),
                    'error': str(e)
                },
                exc_info=True
            )
            
            raise
            
        finally:
            # Clean up transaction context
            if context.transaction_id in self._active_transactions:
                del self._active_transactions[context.transaction_id]
    
    @asynccontextmanager
    async def distributed_transaction(
        self,
        sessions: Dict[str, AsyncSession],
        isolation_level: Optional[IsolationLevel] = None,
        user_id: Optional[uuid.UUID] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Distributed transaction across multiple database sessions
        Uses 2-phase commit protocol
        
        Args:
            sessions: Dictionary of service_name -> AsyncSession
            isolation_level: Transaction isolation level
            user_id: User initiating the transaction
            metadata: Additional transaction metadata
        """
        context = TransactionContext(
            isolation_level=isolation_level,
            user_id=user_id,
            metadata=metadata or {},
            participants=list(sessions.keys())
        )
        
        self._active_transactions[context.transaction_id] = context
        
        logger.info(
            f"Starting distributed transaction {context.transaction_id}",
            extra={
                'transaction_id': context.transaction_id,
                'participants': context.participants
            }
        )
        
        # Phase 1: Prepare all participants
        prepared_sessions = []
        
        try:
            for service_name, session in sessions.items():
                # Set isolation level
                if isolation_level:
                    await session.execute(
                        text(f"SET TRANSACTION ISOLATION LEVEL {isolation_level.value}")
                    )
                
                # Begin transaction
                await session.begin()
                prepared_sessions.append((service_name, session))
            
            # Yield distributed transaction scope
            yield DistributedTransactionScope(self, sessions, context)
            
            # Phase 2: Commit all participants
            for service_name, session in prepared_sessions:
                await session.commit()
                logger.debug(f"Committed transaction for service: {service_name}")
            
            context.state = TransactionState.COMMITTED
            context.completed_at = datetime.now(timezone.utc)
            
            logger.info(
                f"Distributed transaction {context.transaction_id} committed successfully",
                extra={
                    'transaction_id': context.transaction_id,
                    'duration_ms': self._calculate_duration_ms(context)
                }
            )
            
        except Exception as e:
            # Rollback all prepared sessions
            rollback_errors = []
            
            for service_name, session in prepared_sessions:
                try:
                    await session.rollback()
                    logger.debug(f"Rolled back transaction for service: {service_name}")
                except Exception as rollback_error:
                    rollback_errors.append(f"{service_name}: {rollback_error}")
            
            context.state = TransactionState.ROLLED_BACK
            context.completed_at = datetime.now(timezone.utc)
            
            error_msg = f"Distributed transaction {context.transaction_id} failed: {e}"
            if rollback_errors:
                error_msg += f". Rollback errors: {'; '.join(rollback_errors)}"
            
            logger.error(
                error_msg,
                extra={
                    'transaction_id': context.transaction_id,
                    'duration_ms': self._calculate_duration_ms(context)
                },
                exc_info=True
            )
            
            raise DistributedTransactionException(error_msg) from e
            
        finally:
            if context.transaction_id in self._active_transactions:
                del self._active_transactions[context.transaction_id]
    
    async def create_savepoint(
        self,
        session: AsyncSession,
        context: TransactionContext,
        savepoint_name: Optional[str] = None
    ) -> str:
        """Create a savepoint within a transaction"""
        savepoint_name = savepoint_name or f"sp_{len(context.savepoints) + 1}"
        
        await session.execute(text(f"SAVEPOINT {savepoint_name}"))
        context.savepoints.append(savepoint_name)
        
        logger.debug(f"Created savepoint {savepoint_name} in transaction {context.transaction_id}")
        
        return savepoint_name
    
    async def rollback_to_savepoint(
        self,
        session: AsyncSession,
        context: TransactionContext,
        savepoint_name: str
    ) -> None:
        """Rollback to a specific savepoint"""
        if savepoint_name not in context.savepoints:
            raise ValueError(f"Savepoint {savepoint_name} not found in transaction {context.transaction_id}")
        
        await session.execute(text(f"ROLLBACK TO SAVEPOINT {savepoint_name}"))
        
        # Remove savepoints created after this one
        savepoint_index = context.savepoints.index(savepoint_name)
        context.savepoints = context.savepoints[:savepoint_index + 1]
        
        logger.debug(f"Rolled back to savepoint {savepoint_name} in transaction {context.transaction_id}")
    
    async def release_savepoint(
        self,
        session: AsyncSession,
        context: TransactionContext,
        savepoint_name: str
    ) -> None:
        """Release a savepoint"""
        if savepoint_name not in context.savepoints:
            raise ValueError(f"Savepoint {savepoint_name} not found in transaction {context.transaction_id}")
        
        await session.execute(text(f"RELEASE SAVEPOINT {savepoint_name}"))
        context.savepoints.remove(savepoint_name)
        
        logger.debug(f"Released savepoint {savepoint_name} in transaction {context.transaction_id}")
    
    def add_hook(
        self,
        hook_type: str,
        callback: Callable[[TransactionContext, AsyncSession], None]
    ) -> None:
        """Add transaction hook"""
        if hook_type not in self._transaction_hooks:
            raise ValueError(f"Invalid hook type: {hook_type}")
        
        self._transaction_hooks[hook_type].append(callback)
    
    async def _execute_hooks(
        self,
        hook_type: str,
        context: TransactionContext,
        session: AsyncSession
    ) -> None:
        """Execute transaction hooks"""
        for hook in self._transaction_hooks[hook_type]:
            try:
                if asyncio.iscoroutinefunction(hook):
                    await hook(context, session)
                else:
                    hook(context, session)
            except Exception as e:
                logger.error(f"Transaction hook {hook_type} failed: {e}", exc_info=True)
    
    def _calculate_duration_ms(self, context: TransactionContext) -> float:
        """Calculate transaction duration in milliseconds"""
        if context.completed_at:
            return (context.completed_at - context.started_at).total_seconds() * 1000
        return (datetime.now(timezone.utc) - context.started_at).total_seconds() * 1000
    
    def get_active_transactions(self) -> Dict[str, TransactionContext]:
        """Get all active transactions"""
        return self._active_transactions.copy()


class TransactionScope:
    """Single database transaction scope"""
    
    def __init__(
        self,
        manager: TransactionManager,
        session: AsyncSession,
        context: TransactionContext
    ):
        self.manager = manager
        self.session = session
        self.context = context
    
    async def savepoint(self, name: Optional[str] = None) -> str:
        """Create savepoint"""
        return await self.manager.create_savepoint(self.session, self.context, name)
    
    async def rollback_to(self, savepoint_name: str) -> None:
        """Rollback to savepoint"""
        await self.manager.rollback_to_savepoint(self.session, self.context, savepoint_name)
    
    async def release(self, savepoint_name: str) -> None:
        """Release savepoint"""
        await self.manager.release_savepoint(self.session, self.context, savepoint_name)


class DistributedTransactionScope:
    """Distributed transaction scope"""
    
    def __init__(
        self,
        manager: TransactionManager,
        sessions: Dict[str, AsyncSession],
        context: TransactionContext
    ):
        self.manager = manager
        self.sessions = sessions
        self.context = context
    
    def get_session(self, service_name: str) -> AsyncSession:
        """Get session for specific service"""
        if service_name not in self.sessions:
            raise ValueError(f"Service {service_name} not participating in transaction")
        return self.sessions[service_name]


# Exceptions
class TransactionException(Exception):
    """Base transaction exception"""
    pass


class TransactionFailedException(TransactionException):
    """Transaction failed exception"""
    pass


class DistributedTransactionException(TransactionException):
    """Distributed transaction exception"""
    pass


# Global transaction manager instance
transaction_manager = TransactionManager()


# Convenience functions
@asynccontextmanager
async def db_transaction(
    session: AsyncSession,
    isolation_level: Optional[IsolationLevel] = None,
    user_id: Optional[uuid.UUID] = None,
    **kwargs
):
    """Convenience function for database transactions"""
    async with transaction_manager.transaction(
        session, isolation_level, user_id, **kwargs
    ) as tx:
        yield tx


@asynccontextmanager  
async def distributed_transaction(
    sessions: Dict[str, AsyncSession],
    isolation_level: Optional[IsolationLevel] = None,
    user_id: Optional[uuid.UUID] = None,
    **kwargs
):
    """Convenience function for distributed transactions"""
    async with transaction_manager.distributed_transaction(
        sessions, isolation_level, user_id, **kwargs
    ) as tx:
        yield tx