"""
Database utilities for connection pooling, backup, and operational excellence
"""

import asyncio
import logging
import os
import subprocess
import asyncpg
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List, AsyncGenerator
from pathlib import Path
import json
import gzip
import shutil

from sqlalchemy import text, create_engine, event
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import QueuePool, NullPool
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

logger = logging.getLogger(__name__)


class DatabaseConnectionManager:
    """Advanced database connection management with pooling and monitoring"""
    
    def __init__(self):
        self.engine = None
        self.async_engine = None
        self.session_factory = None
        self.pool_stats = {
            'total_connections': 0,
            'active_connections': 0,
            'idle_connections': 0,
            'connection_errors': 0,
            'last_error': None
        }
    
    async def initialize(self) -> None:
        """Initialize database connections with optimized pooling"""
        
        # Async engine with connection pooling
        self.async_engine = create_async_engine(
            settings.SQLALCHEMY_DATABASE_URI,
            
            # Connection pool settings
            pool_size=20,  # Base pool size
            max_overflow=30,  # Additional connections when needed
            pool_timeout=30,  # Timeout for getting connection
            pool_recycle=3600,  # Recycle connections every hour
            pool_pre_ping=True,  # Validate connections before use
            
            # Performance settings
            echo=settings.DEBUG,
            echo_pool=settings.DEBUG,
            future=True,
            
            # Connection options
            connect_args={
                "server_settings": {
                    "application_name": "financial_planning_app",
                    "jit": "off"  # Disable JIT for consistent performance
                }
            }
        )
        
        # Session factory
        self.session_factory = sessionmaker(
            bind=self.async_engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=True,
            autocommit=False
        )
        
        # Setup connection monitoring
        self._setup_connection_monitoring()
        
        logger.info("Database connection manager initialized")
    
    def _setup_connection_monitoring(self) -> None:
        """Setup connection pool monitoring and metrics"""
        
        @event.listens_for(self.async_engine.sync_engine, "connect")
        def on_connect(dbapi_connection, connection_record):
            self.pool_stats['total_connections'] += 1
            logger.debug(f"New database connection established. Total: {self.pool_stats['total_connections']}")
        
        @event.listens_for(self.async_engine.sync_engine, "checkout")
        def on_checkout(dbapi_connection, connection_record, connection_proxy):
            self.pool_stats['active_connections'] += 1
        
        @event.listens_for(self.async_engine.sync_engine, "checkin")
        def on_checkin(dbapi_connection, connection_record):
            if self.pool_stats['active_connections'] > 0:
                self.pool_stats['active_connections'] -= 1
        
        @event.listens_for(self.async_engine.sync_engine, "close")
        def on_close(dbapi_connection, connection_record):
            if self.pool_stats['total_connections'] > 0:
                self.pool_stats['total_connections'] -= 1
    
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get database session with proper error handling"""
        session = self.session_factory()
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            self.pool_stats['connection_errors'] += 1
            self.pool_stats['last_error'] = str(e)
            logger.error(f"Database session error: {e}")
            raise
        finally:
            await session.close()
    
    async def execute_raw_sql(self, query: str, params: Optional[Dict] = None) -> Any:
        """Execute raw SQL with proper connection handling"""
        async with self.async_engine.begin() as conn:
            result = await conn.execute(text(query), params or {})
            return result
    
    async def health_check(self) -> Dict[str, Any]:
        """Comprehensive database health check"""
        try:
            start_time = datetime.now()
            
            # Basic connectivity test
            async with self.async_engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
            
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            
            # Pool statistics
            pool = self.async_engine.pool
            pool_info = {
                'size': pool.size(),
                'checked_in': pool.checkedin(),
                'checked_out': pool.checkedout(),
                'overflow': pool.overflow(),
                'response_time_ms': response_time
            }
            
            # Database statistics
            db_stats = await self._get_database_stats()
            
            return {
                'status': 'healthy',
                'response_time_ms': response_time,
                'pool_stats': pool_info,
                'connection_stats': self.pool_stats,
                'database_stats': db_stats,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
    
    async def _get_database_stats(self) -> Dict[str, Any]:
        """Get detailed database statistics"""
        queries = {
            'total_connections': """
                SELECT count(*) as total,
                       count(*) FILTER (WHERE state = 'active') as active,
                       count(*) FILTER (WHERE state = 'idle') as idle
                FROM pg_stat_activity 
                WHERE datname = current_database()
            """,
            'database_size': """
                SELECT pg_size_pretty(pg_database_size(current_database())) as size
            """,
            'table_stats': """
                SELECT schemaname, tablename, 
                       n_tup_ins as inserts, 
                       n_tup_upd as updates, 
                       n_tup_del as deletes,
                       n_live_tup as live_tuples,
                       n_dead_tup as dead_tuples
                FROM pg_stat_user_tables
                ORDER BY n_live_tup DESC
                LIMIT 10
            """
        }
        
        stats = {}
        async with self.async_engine.begin() as conn:
            for stat_name, query in queries.items():
                try:
                    result = await conn.execute(text(query))
                    if stat_name == 'table_stats':
                        stats[stat_name] = [dict(row._mapping) for row in result]
                    else:
                        stats[stat_name] = dict(result.first()._mapping) if result.first() else {}
                except Exception as e:
                    logger.warning(f"Failed to collect {stat_name}: {e}")
                    stats[stat_name] = {'error': str(e)}
        
        return stats
    
    async def close(self) -> None:
        """Close all database connections"""
        if self.async_engine:
            await self.async_engine.dispose()
        logger.info("Database connections closed")


class DatabaseBackupManager:
    """Comprehensive backup and disaster recovery management"""
    
    def __init__(self, backup_dir: str = "/var/backups/financial_planning"):
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
    async def create_full_backup(self, 
                               compress: bool = True,
                               include_schema: bool = True,
                               include_data: bool = True) -> Dict[str, Any]:
        """Create full database backup with metadata"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"financial_planning_full_{timestamp}"
        backup_file = self.backup_dir / f"{backup_name}.sql"
        
        try:
            # Build pg_dump command
            cmd = [
                "pg_dump",
                "-h", settings.POSTGRES_SERVER,
                "-p", settings.POSTGRES_PORT,
                "-U", settings.POSTGRES_USER,
                "-d", settings.POSTGRES_DB,
                "--verbose",
                "--format=custom",
                "--no-password"
            ]
            
            if not include_schema:
                cmd.append("--data-only")
            elif not include_data:
                cmd.append("--schema-only")
            
            # Set environment variable for password
            env = os.environ.copy()
            env["PGPASSWORD"] = settings.POSTGRES_PASSWORD
            
            # Execute backup
            start_time = datetime.now()
            
            with open(backup_file, 'wb') as f:
                process = subprocess.run(
                    cmd,
                    stdout=f,
                    stderr=subprocess.PIPE,
                    env=env,
                    timeout=3600  # 1 hour timeout
                )
            
            if process.returncode != 0:
                raise Exception(f"pg_dump failed: {process.stderr.decode()}")
            
            backup_duration = (datetime.now() - start_time).total_seconds()
            backup_size = backup_file.stat().st_size
            
            # Compress if requested
            if compress:
                compressed_file = backup_file.with_suffix('.sql.gz')
                with open(backup_file, 'rb') as f_in:
                    with gzip.open(compressed_file, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                backup_file.unlink()  # Remove uncompressed file
                backup_file = compressed_file
                backup_size = backup_file.stat().st_size
            
            # Create backup metadata
            metadata = {
                'backup_id': backup_name,
                'timestamp': start_time.isoformat(),
                'duration_seconds': backup_duration,
                'file_path': str(backup_file),
                'file_size_bytes': backup_size,
                'file_size_human': self._format_bytes(backup_size),
                'compressed': compress,
                'include_schema': include_schema,
                'include_data': include_data,
                'database_version': await self._get_database_version(),
                'table_count': await self._get_table_count(),
                'checksum': self._calculate_checksum(backup_file)
            }
            
            # Save metadata
            metadata_file = backup_file.with_suffix('.json')
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            logger.info(f"Full backup completed: {backup_name} ({self._format_bytes(backup_size)})")
            return metadata
        
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            # Cleanup failed backup files
            if backup_file.exists():
                backup_file.unlink()
            raise
    
    async def create_incremental_backup(self, base_backup_id: str) -> Dict[str, Any]:
        """Create incremental backup using WAL files"""
        # This is a simplified implementation
        # In production, you would use pg_basebackup and WAL archiving
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"financial_planning_incremental_{timestamp}"
        
        try:
            # Get WAL files since last backup
            wal_files = await self._get_wal_files_since(base_backup_id)
            
            # Archive WAL files
            backup_dir = self.backup_dir / backup_name
            backup_dir.mkdir(exist_ok=True)
            
            for wal_file in wal_files:
                shutil.copy2(wal_file, backup_dir)
            
            metadata = {
                'backup_id': backup_name,
                'type': 'incremental',
                'base_backup_id': base_backup_id,
                'timestamp': datetime.now().isoformat(),
                'wal_files_count': len(wal_files),
                'backup_dir': str(backup_dir)
            }
            
            # Save metadata
            metadata_file = backup_dir / 'metadata.json'
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            logger.info(f"Incremental backup completed: {backup_name}")
            return metadata
        
        except Exception as e:
            logger.error(f"Incremental backup failed: {e}")
            raise
    
    async def restore_backup(self, backup_file: str, target_db: Optional[str] = None) -> Dict[str, Any]:
        """Restore database from backup file"""
        
        if not Path(backup_file).exists():
            raise FileNotFoundError(f"Backup file not found: {backup_file}")
        
        target_db = target_db or settings.POSTGRES_DB
        
        try:
            start_time = datetime.now()
            
            # Build pg_restore command
            cmd = [
                "pg_restore",
                "-h", settings.POSTGRES_SERVER,
                "-p", settings.POSTGRES_PORT,
                "-U", settings.POSTGRES_USER,
                "-d", target_db,
                "--clean",
                "--if-exists",
                "--verbose",
                "--no-password",
                backup_file
            ]
            
            # Set environment variable for password
            env = os.environ.copy()
            env["PGPASSWORD"] = settings.POSTGRES_PASSWORD
            
            # Execute restore
            process = subprocess.run(
                cmd,
                capture_output=True,
                env=env,
                timeout=7200  # 2 hour timeout
            )
            
            if process.returncode != 0:
                raise Exception(f"pg_restore failed: {process.stderr.decode()}")
            
            restore_duration = (datetime.now() - start_time).total_seconds()
            
            metadata = {
                'restore_timestamp': start_time.isoformat(),
                'duration_seconds': restore_duration,
                'backup_file': backup_file,
                'target_database': target_db,
                'success': True
            }
            
            logger.info(f"Database restore completed in {restore_duration:.2f} seconds")
            return metadata
        
        except Exception as e:
            logger.error(f"Restore failed: {e}")
            raise
    
    async def list_backups(self) -> List[Dict[str, Any]]:
        """List all available backups with metadata"""
        backups = []
        
        for backup_file in self.backup_dir.glob("*.sql*"):
            if backup_file.suffix == '.json':
                continue
            
            metadata_file = backup_file.with_suffix('.json')
            if metadata_file.exists():
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                backups.append(metadata)
            else:
                # Create basic metadata for files without it
                stat = backup_file.stat()
                backups.append({
                    'backup_id': backup_file.stem,
                    'file_path': str(backup_file),
                    'file_size_bytes': stat.st_size,
                    'timestamp': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    'has_metadata': False
                })
        
        return sorted(backups, key=lambda x: x['timestamp'], reverse=True)
    
    async def cleanup_old_backups(self, retention_days: int = 30) -> Dict[str, Any]:
        """Clean up old backup files based on retention policy"""
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        deleted_files = []
        total_space_freed = 0
        
        for backup_file in self.backup_dir.glob("*.sql*"):
            if backup_file.suffix == '.json':
                continue
            
            file_stat = backup_file.stat()
            file_date = datetime.fromtimestamp(file_stat.st_mtime)
            
            if file_date < cutoff_date:
                # Delete backup file and its metadata
                total_space_freed += file_stat.st_size
                deleted_files.append(str(backup_file))
                
                backup_file.unlink()
                
                metadata_file = backup_file.with_suffix('.json')
                if metadata_file.exists():
                    metadata_file.unlink()
        
        result = {
            'deleted_files': deleted_files,
            'files_deleted_count': len(deleted_files),
            'space_freed_bytes': total_space_freed,
            'space_freed_human': self._format_bytes(total_space_freed),
            'retention_days': retention_days
        }
        
        logger.info(f"Backup cleanup completed: {len(deleted_files)} files deleted, "
                   f"{self._format_bytes(total_space_freed)} freed")
        
        return result
    
    async def verify_backup(self, backup_file: str) -> Dict[str, Any]:
        """Verify backup file integrity"""
        if not Path(backup_file).exists():
            raise FileNotFoundError(f"Backup file not found: {backup_file}")
        
        try:
            # Test backup file by listing contents
            cmd = [
                "pg_restore",
                "--list",
                backup_file
            ]
            
            process = subprocess.run(
                cmd,
                capture_output=True,
                timeout=300  # 5 minute timeout
            )
            
            if process.returncode == 0:
                output_lines = process.stdout.decode().split('\n')
                table_count = len([line for line in output_lines if 'TABLE DATA' in line])
                
                return {
                    'valid': True,
                    'backup_file': backup_file,
                    'table_count': table_count,
                    'verification_timestamp': datetime.now().isoformat()
                }
            else:
                return {
                    'valid': False,
                    'backup_file': backup_file,
                    'error': process.stderr.decode(),
                    'verification_timestamp': datetime.now().isoformat()
                }
        
        except Exception as e:
            return {
                'valid': False,
                'backup_file': backup_file,
                'error': str(e),
                'verification_timestamp': datetime.now().isoformat()
            }
    
    def _format_bytes(self, bytes_count: int) -> str:
        """Format bytes in human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_count < 1024.0:
                return f"{bytes_count:.1f} {unit}"
            bytes_count /= 1024.0
        return f"{bytes_count:.1f} PB"
    
    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA256 checksum of file"""
        import hashlib
        
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        
        return sha256_hash.hexdigest()
    
    async def _get_database_version(self) -> str:
        """Get PostgreSQL version"""
        try:
            conn = await asyncpg.connect(
                host=settings.POSTGRES_SERVER,
                port=settings.POSTGRES_PORT,
                user=settings.POSTGRES_USER,
                password=settings.POSTGRES_PASSWORD,
                database=settings.POSTGRES_DB
            )
            
            version = await conn.fetchval("SELECT version()")
            await conn.close()
            return version
        except Exception:
            return "unknown"
    
    async def _get_table_count(self) -> int:
        """Get number of tables in database"""
        try:
            conn = await asyncpg.connect(
                host=settings.POSTGRES_SERVER,
                port=settings.POSTGRES_PORT,
                user=settings.POSTGRES_USER,
                password=settings.POSTGRES_PASSWORD,
                database=settings.POSTGRES_DB
            )
            
            count = await conn.fetchval(
                "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public'"
            )
            await conn.close()
            return count
        except Exception:
            return 0
    
    async def _get_wal_files_since(self, base_backup_id: str) -> List[str]:
        """Get WAL files since base backup (placeholder implementation)"""
        # This is a simplified implementation
        # In production, you would track WAL files and LSN positions
        return []


# Global instances
db_manager = DatabaseConnectionManager()
backup_manager = DatabaseBackupManager()


async def init_database():
    """Initialize database connection manager"""
    await db_manager.initialize()


async def close_database():
    """Close database connections"""
    await db_manager.close()


async def get_database_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session for dependency injection"""
    async for session in db_manager.get_session():
        yield session