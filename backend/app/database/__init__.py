"""
Database package initialization with comprehensive operational excellence
"""

from .base import Base, get_db
from .models import (
    User, Plan, PlanInput, PlanOutput, 
    CapitalMarketAssumptions, PortfolioModel,
    AuditLog, SystemEvent, DataRetentionPolicy
)
from .utils import (
    DatabaseConnectionManager, DatabaseBackupManager,
    db_manager, backup_manager, 
    init_database, close_database, get_database_session
)
from .audit import (
    AuditLogger, AuditAction, AuditSeverity, AuditContext,
    audit_logger, init_audit_system, shutdown_audit_system
)
from .performance import (
    DatabasePerformanceMonitor, QueryOptimizer,
    performance_monitor, query_optimizer,
    init_performance_monitoring, shutdown_performance_monitoring
)
from .retention import (
    DataRetentionManager, retention_manager,
    init_retention_system, shutdown_retention_system
)

__all__ = [
    # Base classes and dependencies
    'Base', 'get_db',
    
    # Database models
    'User', 'Plan', 'PlanInput', 'PlanOutput',
    'CapitalMarketAssumptions', 'PortfolioModel',
    'AuditLog', 'SystemEvent', 'DataRetentionPolicy',
    
    # Database utilities
    'DatabaseConnectionManager', 'DatabaseBackupManager',
    'db_manager', 'backup_manager',
    'init_database', 'close_database', 'get_database_session',
    
    # Audit system
    'AuditLogger', 'AuditAction', 'AuditSeverity', 'AuditContext',
    'audit_logger', 'init_audit_system', 'shutdown_audit_system',
    
    # Performance monitoring
    'DatabasePerformanceMonitor', 'QueryOptimizer',
    'performance_monitor', 'query_optimizer',
    'init_performance_monitoring', 'shutdown_performance_monitoring',
    
    # Data retention
    'DataRetentionManager', 'retention_manager',
    'init_retention_system', 'shutdown_retention_system',
]


async def initialize_database_system():
    """Initialize complete database system with all components"""
    # Initialize database connections
    await init_database()
    
    # Initialize audit system
    await init_audit_system()
    
    # Initialize performance monitoring
    await init_performance_monitoring()
    
    # Initialize retention system
    await init_retention_system()


async def shutdown_database_system():
    """Shutdown complete database system"""
    # Shutdown retention system
    await shutdown_retention_system()
    
    # Shutdown performance monitoring
    await shutdown_performance_monitoring()
    
    # Shutdown audit system
    await shutdown_audit_system()
    
    # Close database connections
    await close_database()