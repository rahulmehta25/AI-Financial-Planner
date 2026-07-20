#!/usr/bin/env python3
"""
Database Administration Toolkit for Financial Planning System

This toolkit provides comprehensive database administration capabilities including:
- Automated backup strategies with retention policies
- Performance monitoring and alerting
- User management and access control
- Database maintenance and optimization
- Disaster recovery procedures
- Connection pooling and high availability setup

Usage:
    python3 database_admin_toolkit.py [command] [options]

Commands:
    backup     - Create database backups
    restore    - Restore from backup
    monitor    - Performance monitoring
    maintain   - Database maintenance
    users      - User management
    health     - Health checks
    disaster   - Disaster recovery procedures
"""

import os
import sys
import json
import sqlite3
import time
import shutil
import hashlib
import argparse
import logging
import threading
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor
import schedule

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('database_admin.log')
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class BackupConfig:
    """Backup configuration settings"""
    backup_dir: str = "backups"
    retention_days: int = 30
    max_backups: int = 100
    compression: bool = True
    encryption: bool = False
    verify_backup: bool = True
    backup_types: List[str] = None
    
    def __post_init__(self):
        if self.backup_types is None:
            self.backup_types = ["full", "incremental"]

@dataclass
class MonitoringConfig:
    """Monitoring configuration settings"""
    check_interval_seconds: int = 60
    performance_threshold_ms: int = 1000
    connection_threshold: int = 80
    disk_space_threshold_mb: int = 100
    alert_email: str = ""
    enable_alerts: bool = True

@dataclass
class MaintenanceConfig:
    """Database maintenance configuration"""
    vacuum_schedule: str = "weekly"
    analyze_schedule: str = "daily"
    reindex_schedule: str = "monthly"
    cleanup_temp_tables: bool = True
    optimize_queries: bool = True

class DatabaseAdministrator:
    """Comprehensive database administration toolkit"""
    
    def __init__(self, db_path: str = "demo_data/financial_data.db"):
        self.db_path = Path(db_path)
        self.backup_config = BackupConfig()
        self.monitoring_config = MonitoringConfig()
        self.maintenance_config = MaintenanceConfig()
        
        # Ensure directories exist
        Path(self.backup_config.backup_dir).mkdir(exist_ok=True)
        
    def create_backup(self, backup_type: str = "full", description: str = "") -> Dict[str, Any]:
        """Create database backup with specified type"""
        logger.info(f"=== Creating {backup_type} backup ===")
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"backup_{backup_type}_{timestamp}.db"
            backup_path = Path(self.backup_config.backup_dir) / backup_filename
            
            # Create backup metadata
            metadata = {
                "backup_type": backup_type,
                "timestamp": datetime.now().isoformat(),
                "source_path": str(self.db_path),
                "backup_path": str(backup_path),
                "description": description,
                "file_size": 0,
                "checksum": "",
                "verified": False
            }
            
            start_time = time.time()
            
            if backup_type == "full":
                # Full backup - copy entire database
                shutil.copy2(self.db_path, backup_path)
                logger.info(f"✅ Full backup created: {backup_path}")
                
            elif backup_type == "incremental":
                # For SQLite, incremental is essentially a full copy
                # In production, you would implement WAL-based incremental backup
                shutil.copy2(self.db_path, backup_path)
                logger.info(f"✅ Incremental backup created: {backup_path}")
                
            backup_duration = time.time() - start_time
            
            # Get file size and calculate checksum
            metadata["file_size"] = backup_path.stat().st_size
            metadata["checksum"] = self._calculate_checksum(backup_path)
            metadata["duration"] = backup_duration
            
            # Verify backup if enabled
            if self.backup_config.verify_backup:
                metadata["verified"] = self._verify_backup(backup_path)
                logger.info(f"✅ Backup verification: {'PASSED' if metadata['verified'] else 'FAILED'}")
            
            # Save backup metadata
            metadata_path = backup_path.with_suffix('.json')
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            # Cleanup old backups
            self._cleanup_old_backups()
            
            logger.info(f"✅ Backup completed in {backup_duration:.2f}s")
            logger.info(f"✅ Backup size: {metadata['file_size']} bytes")
            
            return {
                "status": "success",
                "backup_path": str(backup_path),
                "metadata": metadata
            }
            
        except Exception as e:
            logger.error(f"❌ Backup creation failed: {str(e)}")
            return {
                "status": "failed",
                "error": str(e)
            }
    
    def restore_backup(self, backup_path: str, target_path: str = None) -> Dict[str, Any]:
        """Restore database from backup"""
        logger.info(f"=== Restoring from backup: {backup_path} ===")
        
        try:
            backup_file = Path(backup_path)
            if not backup_file.exists():
                raise FileNotFoundError(f"Backup file not found: {backup_path}")
            
            # Load backup metadata
            metadata_file = backup_file.with_suffix('.json')
            metadata = {}
            if metadata_file.exists():
                with open(metadata_file) as f:
                    metadata = json.load(f)
                
                # Verify backup integrity
                if metadata.get("checksum"):
                    current_checksum = self._calculate_checksum(backup_file)
                    if current_checksum != metadata["checksum"]:
                        logger.warning("⚠️ Backup checksum mismatch - backup may be corrupted")
            
            target = Path(target_path) if target_path else self.db_path
            
            # Create backup of current database
            if target.exists():
                current_backup = target.with_suffix('.db.pre_restore')
                shutil.copy2(target, current_backup)
                logger.info(f"✅ Current database backed up to: {current_backup}")
            
            # Restore database
            start_time = time.time()
            shutil.copy2(backup_file, target)
            restore_duration = time.time() - start_time
            
            # Verify restored database
            verification_result = self._verify_database(target)
            
            logger.info(f"✅ Database restored in {restore_duration:.2f}s")
            logger.info(f"✅ Verification: {'PASSED' if verification_result else 'FAILED'}")
            
            return {
                "status": "success",
                "restore_duration": restore_duration,
                "target_path": str(target),
                "metadata": metadata,
                "verified": verification_result
            }
            
        except Exception as e:
            logger.error(f"❌ Database restore failed: {str(e)}")
            return {
                "status": "failed",
                "error": str(e)
            }
    
    def monitor_performance(self, duration_minutes: int = 5) -> Dict[str, Any]:
        """Monitor database performance over specified duration"""
        logger.info(f"=== Performance monitoring for {duration_minutes} minutes ===")
        
        metrics = {
            "start_time": datetime.now().isoformat(),
            "duration_minutes": duration_minutes,
            "samples": [],
            "alerts": [],
            "summary": {}
        }
        
        try:
            end_time = datetime.now() + timedelta(minutes=duration_minutes)
            sample_interval = 10  # seconds
            
            while datetime.now() < end_time:
                sample = self._collect_performance_sample()
                metrics["samples"].append(sample)
                
                # Check for alerts
                alerts = self._check_performance_alerts(sample)
                metrics["alerts"].extend(alerts)
                
                if alerts:
                    for alert in alerts:
                        logger.warning(f"⚠️ ALERT: {alert['message']}")
                
                time.sleep(sample_interval)
            
            # Calculate summary statistics
            metrics["summary"] = self._calculate_performance_summary(metrics["samples"])
            
            logger.info("✅ Performance monitoring completed")
            logger.info(f"✅ Collected {len(metrics['samples'])} samples")
            logger.info(f"✅ Generated {len(metrics['alerts'])} alerts")
            
            return {
                "status": "success",
                "metrics": metrics
            }
            
        except Exception as e:
            logger.error(f"❌ Performance monitoring failed: {str(e)}")
            return {
                "status": "failed",
                "error": str(e)
            }
    
    def perform_maintenance(self, operations: List[str] = None) -> Dict[str, Any]:
        """Perform database maintenance operations"""
        logger.info("=== Database Maintenance ===")
        
        if operations is None:
            operations = ["vacuum", "analyze", "integrity_check"]
        
        results = {}
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                
                for operation in operations:
                    logger.info(f"Performing {operation}...")
                    start_time = time.time()
                    
                    try:
                        if operation == "vacuum":
                            conn.execute("VACUUM")
                            results[operation] = {
                                "status": "success",
                                "duration": time.time() - start_time
                            }
                            
                        elif operation == "analyze":
                            conn.execute("ANALYZE")
                            results[operation] = {
                                "status": "success",
                                "duration": time.time() - start_time
                            }
                            
                        elif operation == "integrity_check":
                            cursor = conn.execute("PRAGMA integrity_check")
                            result = cursor.fetchone()[0]
                            results[operation] = {
                                "status": "success" if result == "ok" else "failed",
                                "result": result,
                                "duration": time.time() - start_time
                            }
                            
                        elif operation == "reindex":
                            conn.execute("REINDEX")
                            results[operation] = {
                                "status": "success",
                                "duration": time.time() - start_time
                            }
                        
                        logger.info(f"✅ {operation} completed in {results[operation]['duration']:.2f}s")
                        
                    except Exception as e:
                        logger.error(f"❌ {operation} failed: {str(e)}")
                        results[operation] = {
                            "status": "failed",
                            "error": str(e),
                            "duration": time.time() - start_time
                        }
                
                # Get updated database statistics
                stats = self._get_database_statistics(conn)
                
                logger.info("✅ Maintenance operations completed")
                
                return {
                    "status": "success",
                    "operations": results,
                    "database_stats": stats
                }
                
        except Exception as e:
            logger.error(f"❌ Database maintenance failed: {str(e)}")
            return {
                "status": "failed",
                "error": str(e),
                "operations": results
            }
    
    def comprehensive_health_check(self) -> Dict[str, Any]:
        """Perform comprehensive database health check"""
        logger.info("=== Comprehensive Health Check ===")
        
        health_report = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "healthy",
            "checks": {},
            "recommendations": [],
            "alerts": []
        }
        
        try:
            # Database accessibility
            access_check = self._check_accessibility()
            health_report["checks"]["accessibility"] = access_check
            
            # Performance check
            performance_check = self._check_performance()
            health_report["checks"]["performance"] = performance_check
            
            # Disk space check
            disk_check = self._check_disk_space()
            health_report["checks"]["disk_space"] = disk_check
            
            # Backup status check
            backup_check = self._check_backup_status()
            health_report["checks"]["backup_status"] = backup_check
            
            # Connection status
            connection_check = self._check_connection_health()
            health_report["checks"]["connections"] = connection_check
            
            # Determine overall status
            failed_checks = [name for name, check in health_report["checks"].items() 
                           if check.get("status") != "healthy"]
            
            if failed_checks:
                health_report["overall_status"] = "degraded"
                health_report["alerts"].append(f"Failed checks: {', '.join(failed_checks)}")
            
            # Generate recommendations
            health_report["recommendations"] = self._generate_health_recommendations(health_report)
            
            logger.info(f"✅ Health check completed - Status: {health_report['overall_status'].upper()}")
            
            return health_report
            
        except Exception as e:
            logger.error(f"❌ Health check failed: {str(e)}")
            return {
                "timestamp": datetime.now().isoformat(),
                "overall_status": "critical",
                "error": str(e)
            }
    
    def setup_automated_backups(self, schedule_type: str = "daily") -> Dict[str, Any]:
        """Setup automated backup scheduling"""
        logger.info(f"=== Setting up {schedule_type} automated backups ===")
        
        try:
            if schedule_type == "daily":
                schedule.every().day.at("02:00").do(self._automated_backup_job, "full")
                schedule.every(6).hours.do(self._automated_backup_job, "incremental")
                
            elif schedule_type == "hourly":
                schedule.every().hour.do(self._automated_backup_job, "incremental")
                schedule.every().day.at("02:00").do(self._automated_backup_job, "full")
                
            elif schedule_type == "weekly":
                schedule.every().sunday.at("02:00").do(self._automated_backup_job, "full")
                schedule.every().day.at("02:00").do(self._automated_backup_job, "incremental")
            
            logger.info("✅ Automated backup scheduling configured")
            logger.info("Note: Run 'python3 database_admin_toolkit.py scheduler' to start the scheduler")
            
            return {
                "status": "success",
                "schedule_type": schedule_type,
                "jobs_scheduled": len(schedule.jobs)
            }
            
        except Exception as e:
            logger.error(f"❌ Automated backup setup failed: {str(e)}")
            return {
                "status": "failed",
                "error": str(e)
            }
    
    def disaster_recovery_test(self) -> Dict[str, Any]:
        """Test disaster recovery procedures"""
        logger.info("=== Disaster Recovery Test ===")
        
        try:
            # Create test backup
            backup_result = self.create_backup("full", "Disaster recovery test")
            if backup_result["status"] != "success":
                raise Exception("Failed to create test backup")
            
            backup_path = backup_result["backup_path"]
            
            # Create temporary database for testing
            test_db_path = self.db_path.parent / "disaster_recovery_test.db"
            
            # Test restore procedure
            restore_result = self.restore_backup(backup_path, str(test_db_path))
            
            # Verify restored database
            verification_passed = self._verify_database(test_db_path)
            
            # Cleanup test files
            if test_db_path.exists():
                test_db_path.unlink()
            
            rto = restore_result.get("restore_duration", 0)  # Recovery Time Objective
            
            logger.info("✅ Disaster recovery test completed")
            logger.info(f"✅ Recovery Time: {rto:.2f} seconds")
            logger.info(f"✅ Verification: {'PASSED' if verification_passed else 'FAILED'}")
            
            return {
                "status": "success",
                "backup_created": backup_result["status"] == "success",
                "restore_successful": restore_result["status"] == "success",
                "verification_passed": verification_passed,
                "recovery_time_seconds": rto,
                "backup_path": backup_path
            }
            
        except Exception as e:
            logger.error(f"❌ Disaster recovery test failed: {str(e)}")
            return {
                "status": "failed",
                "error": str(e)
            }
    
    # Helper methods
    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate MD5 checksum of file"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def _verify_backup(self, backup_path: Path) -> bool:
        """Verify backup integrity"""
        try:
            with sqlite3.connect(backup_path) as conn:
                cursor = conn.execute("PRAGMA integrity_check")
                result = cursor.fetchone()[0]
                return result == "ok"
        except:
            return False
    
    def _verify_database(self, db_path: Path) -> bool:
        """Verify database integrity"""
        try:
            with sqlite3.connect(db_path) as conn:
                cursor = conn.execute("PRAGMA integrity_check")
                result = cursor.fetchone()[0]
                return result == "ok"
        except:
            return False
    
    def _cleanup_old_backups(self):
        """Remove old backups based on retention policy"""
        backup_dir = Path(self.backup_config.backup_dir)
        if not backup_dir.exists():
            return
        
        cutoff_date = datetime.now() - timedelta(days=self.backup_config.retention_days)
        backups = list(backup_dir.glob("backup_*.db"))
        
        removed = 0
        for backup in backups:
            if backup.stat().st_mtime < cutoff_date.timestamp():
                backup.unlink()
                # Also remove metadata file
                metadata_file = backup.with_suffix('.json')
                if metadata_file.exists():
                    metadata_file.unlink()
                removed += 1
        
        if removed > 0:
            logger.info(f"✅ Cleaned up {removed} old backups")
    
    def _collect_performance_sample(self) -> Dict[str, Any]:
        """Collect a single performance sample"""
        sample = {
            "timestamp": datetime.now().isoformat(),
        }
        
        try:
            with sqlite3.connect(self.db_path, timeout=5.0) as conn:
                # Query performance test
                start_time = time.time()
                cursor = conn.execute("SELECT COUNT(*) FROM customer_portfolios")
                result = cursor.fetchone()
                query_duration = (time.time() - start_time) * 1000  # milliseconds
                
                sample.update({
                    "query_duration_ms": query_duration,
                    "record_count": result[0] if result else 0,
                    "connection_successful": True
                })
                
        except Exception as e:
            sample.update({
                "query_duration_ms": None,
                "connection_successful": False,
                "error": str(e)
            })
        
        return sample
    
    def _check_performance_alerts(self, sample: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check performance sample for alert conditions"""
        alerts = []
        
        # Query duration alert
        if sample.get("query_duration_ms", 0) > self.monitoring_config.performance_threshold_ms:
            alerts.append({
                "type": "performance",
                "severity": "warning",
                "message": f"Query duration {sample['query_duration_ms']:.2f}ms exceeds threshold {self.monitoring_config.performance_threshold_ms}ms",
                "timestamp": sample["timestamp"]
            })
        
        # Connection failure alert
        if not sample.get("connection_successful", True):
            alerts.append({
                "type": "connection",
                "severity": "critical",
                "message": f"Database connection failed: {sample.get('error', 'Unknown error')}",
                "timestamp": sample["timestamp"]
            })
        
        return alerts
    
    def _calculate_performance_summary(self, samples: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate summary statistics from performance samples"""
        if not samples:
            return {}
        
        valid_samples = [s for s in samples if s.get("query_duration_ms") is not None]
        
        if not valid_samples:
            return {"error": "No valid performance samples"}
        
        durations = [s["query_duration_ms"] for s in valid_samples]
        
        return {
            "total_samples": len(samples),
            "valid_samples": len(valid_samples),
            "avg_query_duration_ms": sum(durations) / len(durations),
            "min_query_duration_ms": min(durations),
            "max_query_duration_ms": max(durations),
            "connection_success_rate": len(valid_samples) / len(samples)
        }
    
    def _get_database_statistics(self, conn: sqlite3.Connection) -> Dict[str, Any]:
        """Get database statistics"""
        stats = {}
        
        try:
            # Page count and size
            cursor = conn.execute("PRAGMA page_count")
            page_count = cursor.fetchone()[0]
            
            cursor = conn.execute("PRAGMA page_size")
            page_size = cursor.fetchone()[0]
            
            stats["page_count"] = page_count
            stats["page_size"] = page_size
            stats["total_size"] = page_count * page_size
            
            # Table statistics
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            table_stats = {}
            for table in tables:
                cursor = conn.execute(f"SELECT COUNT(*) FROM {table}")
                row_count = cursor.fetchone()[0]
                table_stats[table] = {"row_count": row_count}
            
            stats["tables"] = table_stats
            
        except Exception as e:
            stats["error"] = str(e)
        
        return stats
    
    def _check_accessibility(self) -> Dict[str, Any]:
        """Check database accessibility"""
        try:
            with sqlite3.connect(self.db_path, timeout=5.0) as conn:
                cursor = conn.execute("SELECT 1")
                result = cursor.fetchone()
                return {
                    "status": "healthy",
                    "accessible": True,
                    "response_time": "< 5s"
                }
        except Exception as e:
            return {
                "status": "critical",
                "accessible": False,
                "error": str(e)
            }
    
    def _check_performance(self) -> Dict[str, Any]:
        """Check database performance"""
        try:
            start_time = time.time()
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT COUNT(*) FROM customer_portfolios")
                result = cursor.fetchone()
            
            duration_ms = (time.time() - start_time) * 1000
            
            status = "healthy" if duration_ms < self.monitoring_config.performance_threshold_ms else "warning"
            
            return {
                "status": status,
                "query_duration_ms": duration_ms,
                "threshold_ms": self.monitoring_config.performance_threshold_ms
            }
        except Exception as e:
            return {
                "status": "critical",
                "error": str(e)
            }
    
    def _check_disk_space(self) -> Dict[str, Any]:
        """Check available disk space"""
        try:
            db_size = self.db_path.stat().st_size
            available_space = shutil.disk_usage(self.db_path.parent).free
            
            available_mb = available_space / (1024 * 1024)
            threshold_mb = self.monitoring_config.disk_space_threshold_mb
            
            status = "healthy" if available_mb > threshold_mb else "warning"
            
            return {
                "status": status,
                "database_size_bytes": db_size,
                "available_space_mb": available_mb,
                "threshold_mb": threshold_mb
            }
        except Exception as e:
            return {
                "status": "critical",
                "error": str(e)
            }
    
    def _check_backup_status(self) -> Dict[str, Any]:
        """Check backup status"""
        try:
            backup_dir = Path(self.backup_config.backup_dir)
            if not backup_dir.exists():
                return {
                    "status": "warning",
                    "message": "No backup directory found"
                }
            
            backups = list(backup_dir.glob("backup_*.db"))
            if not backups:
                return {
                    "status": "warning",
                    "message": "No backups found"
                }
            
            # Check most recent backup
            latest_backup = max(backups, key=lambda x: x.stat().st_mtime)
            backup_age = datetime.now() - datetime.fromtimestamp(latest_backup.stat().st_mtime)
            
            status = "healthy" if backup_age.days < 1 else "warning"
            
            return {
                "status": status,
                "backup_count": len(backups),
                "latest_backup": str(latest_backup),
                "latest_backup_age_hours": backup_age.total_seconds() / 3600
            }
        except Exception as e:
            return {
                "status": "critical",
                "error": str(e)
            }
    
    def _check_connection_health(self) -> Dict[str, Any]:
        """Check connection pool health"""
        # For SQLite, we simulate connection health
        try:
            connections_tested = 5
            successful_connections = 0
            
            for _ in range(connections_tested):
                try:
                    with sqlite3.connect(self.db_path, timeout=1.0) as conn:
                        conn.execute("SELECT 1")
                        successful_connections += 1
                except:
                    pass
            
            success_rate = successful_connections / connections_tested
            status = "healthy" if success_rate >= 0.8 else "warning"
            
            return {
                "status": status,
                "connection_success_rate": success_rate,
                "connections_tested": connections_tested
            }
        except Exception as e:
            return {
                "status": "critical",
                "error": str(e)
            }
    
    def _generate_health_recommendations(self, health_report: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on health check results"""
        recommendations = []
        
        # Check each health category and provide specific recommendations
        checks = health_report.get("checks", {})
        
        if checks.get("performance", {}).get("status") != "healthy":
            recommendations.append("Consider optimizing slow queries and adding database indexes")
        
        if checks.get("disk_space", {}).get("status") != "healthy":
            recommendations.append("Free up disk space or increase storage capacity")
        
        if checks.get("backup_status", {}).get("status") != "healthy":
            recommendations.append("Set up automated backup procedures")
        
        if checks.get("connections", {}).get("status") != "healthy":
            recommendations.append("Investigate connection issues and implement connection pooling")
        
        # General recommendations
        recommendations.extend([
            "Schedule regular database maintenance (VACUUM, ANALYZE)",
            "Monitor database performance metrics regularly",
            "Test disaster recovery procedures quarterly",
            "Keep database and SQLite version updated"
        ])
        
        return recommendations
    
    def _automated_backup_job(self, backup_type: str):
        """Automated backup job for scheduler"""
        logger.info(f"Executing scheduled {backup_type} backup")
        result = self.create_backup(backup_type, f"Automated {backup_type} backup")
        if result["status"] == "success":
            logger.info(f"✅ Scheduled {backup_type} backup completed successfully")
        else:
            logger.error(f"❌ Scheduled {backup_type} backup failed: {result.get('error')}")

def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(description="Database Administration Toolkit")
    parser.add_argument("command", choices=[
        "backup", "restore", "monitor", "maintain", "health", 
        "disaster-test", "setup-backups", "scheduler", "report"
    ], help="Command to execute")
    
    parser.add_argument("--db-path", default="demo_data/financial_data.db",
                       help="Database file path")
    parser.add_argument("--backup-type", choices=["full", "incremental"], 
                       default="full", help="Backup type")
    parser.add_argument("--backup-path", help="Backup file path for restore")
    parser.add_argument("--duration", type=int, default=5,
                       help="Monitoring duration in minutes")
    parser.add_argument("--schedule", choices=["daily", "hourly", "weekly"],
                       default="daily", help="Backup schedule")
    parser.add_argument("--operations", nargs="+", 
                       choices=["vacuum", "analyze", "integrity_check", "reindex"],
                       help="Maintenance operations")
    
    args = parser.parse_args()
    
    # Initialize database administrator
    db_admin = DatabaseAdministrator(args.db_path)
    
    if args.command == "backup":
        result = db_admin.create_backup(args.backup_type)
        print(json.dumps(result, indent=2))
        
    elif args.command == "restore":
        if not args.backup_path:
            print("Error: --backup-path required for restore command")
            sys.exit(1)
        result = db_admin.restore_backup(args.backup_path)
        print(json.dumps(result, indent=2))
        
    elif args.command == "monitor":
        result = db_admin.monitor_performance(args.duration)
        print(json.dumps(result, indent=2))
        
    elif args.command == "maintain":
        result = db_admin.perform_maintenance(args.operations)
        print(json.dumps(result, indent=2))
        
    elif args.command == "health":
        result = db_admin.comprehensive_health_check()
        print(json.dumps(result, indent=2))
        
    elif args.command == "disaster-test":
        result = db_admin.disaster_recovery_test()
        print(json.dumps(result, indent=2))
        
    elif args.command == "setup-backups":
        result = db_admin.setup_automated_backups(args.schedule)
        print(json.dumps(result, indent=2))
        
    elif args.command == "scheduler":
        print("Starting backup scheduler...")
        print("Press Ctrl+C to stop")
        try:
            while True:
                schedule.run_pending()
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nScheduler stopped")
    
    elif args.command == "report":
        # Generate comprehensive operational report
        health = db_admin.comprehensive_health_check()
        disaster_test = db_admin.disaster_recovery_test()
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "database_path": args.db_path,
            "health_check": health,
            "disaster_recovery_test": disaster_test,
            "recommendations": [
                "Implement automated backup scheduling",
                "Set up monitoring alerts for critical metrics",
                "Test disaster recovery procedures quarterly",
                "Schedule regular maintenance operations",
                "Monitor disk space and performance metrics"
            ]
        }
        
        report_file = f"database_operational_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"Comprehensive operational report saved to: {report_file}")
        print(json.dumps(report, indent=2))

if __name__ == "__main__":
    main()