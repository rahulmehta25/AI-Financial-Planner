"""
Database package initialization with comprehensive operational excellence
"""

from .base import Base, get_db
try:
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
except Exception:
    # Avoid heavy side-effects during import at app startup
    DatabaseConnectionManager = None
    DatabaseBackupManager = None
    db_manager = None
    backup_manager = None
    init_database = None
    close_database = None
    get_database_session = None
    AuditLogger = None
    AuditAction = None
    AuditSeverity = None
    AuditContext = None
    audit_logger = None
    init_audit_system = None
    shutdown_audit_system = None
    DatabasePerformanceMonitor = None
    QueryOptimizer = None
    performance_monitor = None
    query_optimizer = None
    init_performance_monitoring = None
    shutdown_performance_monitoring = None
    DataRetentionManager = None
    retention_manager = None
    init_retention_system = None
    shutdown_retention_system = None

__all__ = [
    # Base classes and dependencies
    'Base', 'get_db',
    
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
    if init_database:
        await init_database()
    
    # Initialize audit system
    if init_audit_system:
        await init_audit_system()
    
    # Initialize performance monitoring
    if init_performance_monitoring:
        await init_performance_monitoring()
    
    # Initialize retention system
    if init_retention_system:
        await init_retention_system()


async def shutdown_database_system():
    """Shutdown complete database system"""
    # Shutdown retention system
    if shutdown_retention_system:
        await shutdown_retention_system()
    
    # Shutdown performance monitoring
    if shutdown_performance_monitoring:
        await shutdown_performance_monitoring()
    
    # Shutdown audit system
    if shutdown_audit_system:
        await shutdown_audit_system()
    
    # Close database connections
    if close_database:
        await close_database()