#!/usr/bin/env python3
"""
Automated Backup Scheduler for Financial Planning System
Implements intelligent backup scheduling with adaptive frequency
"""

import asyncio
import schedule
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Callable
import logging
import json
import psutil
import yaml
from pathlib import Path
from dataclasses import dataclass, asdict
from croniter import croniter
import aiofiles
import subprocess

# Import our backup orchestrator
import sys
sys.path.append(str(Path(__file__).parent.parent / "backup-strategy"))
from backup_orchestrator import AdvancedBackupOrchestrator, BackupConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ScheduleMetrics:
    """Metrics for backup scheduling decisions"""
    last_backup_time: datetime
    database_size_gb: float
    transaction_rate: float
    system_load: float
    available_disk_space_gb: float
    network_bandwidth_utilization: float
    backup_window_utilization: float


@dataclass
class SchedulePolicy:
    """Backup scheduling policy"""
    policy_name: str
    full_backup_cron: str
    incremental_backup_cron: str
    pitr_interval_minutes: int
    
    # Adaptive scheduling parameters
    min_interval_minutes: int = 60
    max_interval_minutes: int = 1440  # 24 hours
    load_threshold: float = 0.8
    transaction_rate_threshold: int = 1000
    
    # Business hours consideration
    business_hours_start: int = 8
    business_hours_end: int = 18
    business_days: List[int] = None  # 0=Monday, 6=Sunday
    
    def __post_init__(self):
        if self.business_days is None:
            self.business_days = [0, 1, 2, 3, 4]  # Monday to Friday


class IntelligentBackupScheduler:
    """Intelligent backup scheduler with adaptive frequency"""
    
    def __init__(self, config_path: str = None):
        self.config_path = config_path
        self.orchestrator = AdvancedBackupOrchestrator(config_path)
        self.schedule_policies = self._load_schedule_policies()
        self.current_policy = self.schedule_policies.get("production", self.schedule_policies["default"])
        
        # Metrics collection
        self.metrics_history: List[ScheduleMetrics] = []
        self.running = False
        
        # Schedule tracking
        self.scheduled_jobs = {}
        self.last_backup_check = datetime.now(timezone.utc)
        
    def _load_schedule_policies(self) -> Dict[str, SchedulePolicy]:
        """Load scheduling policies from configuration"""
        default_policies = {
            "default": SchedulePolicy(
                policy_name="default",
                full_backup_cron="0 2 * * 0",  # Sunday 2 AM
                incremental_backup_cron="0 */6 * * *",  # Every 6 hours
                pitr_interval_minutes=15
            ),
            "production": SchedulePolicy(
                policy_name="production",
                full_backup_cron="0 2 * * 0",  # Sunday 2 AM
                incremental_backup_cron="0 */4 * * *",  # Every 4 hours
                pitr_interval_minutes=10,
                min_interval_minutes=30,
                max_interval_minutes=480  # 8 hours
            ),
            "high_frequency": SchedulePolicy(
                policy_name="high_frequency",
                full_backup_cron="0 2 * * 0",  # Sunday 2 AM
                incremental_backup_cron="0 */2 * * *",  # Every 2 hours
                pitr_interval_minutes=5,
                min_interval_minutes=15,
                max_interval_minutes=240  # 4 hours
            ),
            "maintenance": SchedulePolicy(
                policy_name="maintenance",
                full_backup_cron="0 */12 * * *",  # Every 12 hours
                incremental_backup_cron="0 */1 * * *",  # Every hour
                pitr_interval_minutes=5,
                min_interval_minutes=10,
                max_interval_minutes=60
            )
        }
        
        # Try to load custom policies from config file
        if self.config_path and Path(self.config_path).exists():
            try:
                with open(self.config_path, 'r') as f:
                    config = yaml.safe_load(f)
                
                if 'schedule_policies' in config:
                    for name, policy_config in config['schedule_policies'].items():
                        default_policies[name] = SchedulePolicy(**policy_config)
                        
            except Exception as e:
                logger.error(f"Failed to load custom schedule policies: {e}")
        
        return default_policies
    
    async def collect_system_metrics(self) -> ScheduleMetrics:
        """Collect system metrics for scheduling decisions"""
        try:
            # Get database size
            db_size = await self._get_database_size()
            
            # Get transaction rate
            transaction_rate = await self._get_transaction_rate()
            
            # Get system metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory_percent = psutil.virtual_memory().percent
            disk_usage = psutil.disk_usage('/')
            
            # Network utilization (simplified)
            network_io = psutil.net_io_counters()
            network_utilization = (network_io.bytes_sent + network_io.bytes_recv) / 1024 / 1024  # MB
            
            # Get last backup time
            last_backup_time = await self._get_last_backup_time()
            
            metrics = ScheduleMetrics(
                last_backup_time=last_backup_time,
                database_size_gb=db_size,
                transaction_rate=transaction_rate,
                system_load=(cpu_percent + memory_percent) / 2,
                available_disk_space_gb=disk_usage.free / 1024 / 1024 / 1024,
                network_bandwidth_utilization=network_utilization,
                backup_window_utilization=0.0  # Will be calculated
            )
            
            # Store metrics for trend analysis
            self.metrics_history.append(metrics)
            
            # Keep only last 24 hours of metrics
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=24)
            self.metrics_history = [
                m for m in self.metrics_history 
                if m.last_backup_time > cutoff_time
            ]
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to collect system metrics: {e}")
            # Return default metrics
            return ScheduleMetrics(
                last_backup_time=datetime.now(timezone.utc) - timedelta(hours=6),
                database_size_gb=1.0,
                transaction_rate=100.0,
                system_load=0.5,
                available_disk_space_gb=100.0,
                network_bandwidth_utilization=10.0,
                backup_window_utilization=0.3
            )
    
    async def adaptive_scheduling_decision(self, metrics: ScheduleMetrics) -> Dict[str, Any]:
        """Make intelligent scheduling decisions based on metrics"""
        decision = {
            'should_trigger_backup': False,
            'backup_type': 'incremental',
            'priority': 'normal',
            'delay_minutes': 0,
            'reason': []
        }
        
        current_time = datetime.now(timezone.utc)
        time_since_last_backup = current_time - metrics.last_backup_time
        
        # Check if we're in business hours
        is_business_hours = self._is_business_hours(current_time)
        
        # High transaction rate - increase backup frequency
        if metrics.transaction_rate > self.current_policy.transaction_rate_threshold:
            if time_since_last_backup.total_seconds() > (self.current_policy.min_interval_minutes * 60):
                decision['should_trigger_backup'] = True
                decision['priority'] = 'high'
                decision['reason'].append('High transaction rate detected')
        
        # High system load - delay backup unless critical
        if metrics.system_load > self.current_policy.load_threshold:
            if is_business_hours:
                decision['delay_minutes'] = 30
                decision['reason'].append('High system load during business hours')
            else:
                # Outside business hours, proceed with backup
                if time_since_last_backup.total_seconds() > (self.current_policy.max_interval_minutes * 60):
                    decision['should_trigger_backup'] = True
                    decision['reason'].append('Critical backup window - high load but overdue')
        
        # Low disk space - trigger urgent backup and cleanup
        if metrics.available_disk_space_gb < 10:
            decision['should_trigger_backup'] = True
            decision['backup_type'] = 'incremental'
            decision['priority'] = 'urgent'
            decision['reason'].append('Low disk space - urgent backup needed')
        
        # Schedule full backup on Sunday
        if current_time.weekday() == 6 and current_time.hour == 2:  # Sunday 2 AM
            decision['should_trigger_backup'] = True
            decision['backup_type'] = 'full'
            decision['priority'] = 'high'
            decision['reason'].append('Scheduled full backup')
        
        # Regular incremental backup schedule
        regular_interval = self._calculate_adaptive_interval(metrics)
        if time_since_last_backup.total_seconds() > (regular_interval * 60):
            decision['should_trigger_backup'] = True
            decision['reason'].append(f'Regular backup interval ({regular_interval} minutes)')
        
        return decision
    
    def _calculate_adaptive_interval(self, metrics: ScheduleMetrics) -> int:
        """Calculate adaptive backup interval based on system metrics"""
        base_interval = 360  # 6 hours base
        
        # Adjust based on transaction rate
        if metrics.transaction_rate > 1000:
            base_interval = max(base_interval // 2, self.current_policy.min_interval_minutes)
        elif metrics.transaction_rate < 100:
            base_interval = min(base_interval * 2, self.current_policy.max_interval_minutes)
        
        # Adjust based on database size
        if metrics.database_size_gb > 100:
            base_interval = max(base_interval - 60, self.current_policy.min_interval_minutes)
        
        # Adjust based on system load
        if metrics.system_load > 0.8:
            base_interval = min(base_interval + 120, self.current_policy.max_interval_minutes)
        
        return max(
            min(base_interval, self.current_policy.max_interval_minutes),
            self.current_policy.min_interval_minutes
        )
    
    def _is_business_hours(self, dt: datetime) -> bool:
        """Check if given time is during business hours"""
        if dt.weekday() not in self.current_policy.business_days:
            return False
        
        hour = dt.hour
        return self.current_policy.business_hours_start <= hour < self.current_policy.business_hours_end
    
    async def schedule_backup(self, backup_type: str = "incremental", priority: str = "normal") -> bool:
        """Schedule and execute a backup"""
        try:
            logger.info(f"Starting {backup_type} backup (priority: {priority})")
            
            if backup_type == "full":
                result = await self.orchestrator.create_full_backup()
            elif backup_type == "incremental":
                # Find latest full backup as base
                latest_full = await self._find_latest_full_backup()
                if latest_full:
                    result = await self.orchestrator.create_incremental_backup(latest_full)
                else:
                    logger.warning("No full backup found, creating full backup instead")
                    result = await self.orchestrator.create_full_backup()
            else:
                raise ValueError(f"Unknown backup type: {backup_type}")
            
            logger.info(f"Backup completed successfully: {result.backup_id}")
            
            # Verify backup if high priority
            if priority in ["high", "urgent"]:
                verification_result = await self.orchestrator.verify_backup_integrity(result.backup_id)
                if not verification_result['overall_success']:
                    logger.error(f"Backup verification failed: {result.backup_id}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            return False
    
    async def run_scheduler(self):
        """Main scheduler loop"""
        logger.info("Starting intelligent backup scheduler")
        self.running = True
        
        while self.running:
            try:
                # Collect current system metrics
                metrics = await self.collect_system_metrics()
                
                # Make scheduling decision
                decision = await self.adaptive_scheduling_decision(metrics)
                
                # Execute backup if needed
                if decision['should_trigger_backup']:
                    if decision['delay_minutes'] > 0:
                        logger.info(f"Delaying backup by {decision['delay_minutes']} minutes: {', '.join(decision['reason'])}")
                        await asyncio.sleep(decision['delay_minutes'] * 60)
                    
                    success = await self.schedule_backup(
                        backup_type=decision['backup_type'],
                        priority=decision['priority']
                    )
                    
                    if not success and decision['priority'] == 'urgent':
                        logger.error("Urgent backup failed - sending alert")
                        await self._send_backup_alert("Urgent backup failed", metrics, decision)
                
                # Log scheduling decision
                await self._log_scheduling_decision(metrics, decision)
                
                # Wait before next check (default: 5 minutes)
                await asyncio.sleep(300)
                
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retry
    
    async def stop_scheduler(self):
        """Stop the scheduler"""
        logger.info("Stopping backup scheduler")
        self.running = False
    
    async def _get_database_size(self) -> float:
        """Get current database size in GB"""
        try:
            # Implementation to get database size
            # This would connect to the database and run appropriate queries
            return 5.0  # Placeholder
        except Exception:
            return 1.0
    
    async def _get_transaction_rate(self) -> float:
        """Get current transaction rate per minute"""
        try:
            # Implementation to get transaction rate
            # This would query database statistics
            return 500.0  # Placeholder
        except Exception:
            return 100.0
    
    async def _get_last_backup_time(self) -> datetime:
        """Get timestamp of last successful backup"""
        try:
            if self.orchestrator.metadata:
                latest_backup = max(
                    self.orchestrator.metadata.values(),
                    key=lambda x: x.timestamp
                )
                return latest_backup.timestamp
        except Exception:
            pass
        
        return datetime.now(timezone.utc) - timedelta(hours=6)
    
    async def _find_latest_full_backup(self) -> Optional[str]:
        """Find the latest full backup ID"""
        try:
            full_backups = [
                backup for backup in self.orchestrator.metadata.values()
                if backup.backup_type == "full"
            ]
            
            if full_backups:
                latest = max(full_backups, key=lambda x: x.timestamp)
                return latest.backup_id
        except Exception:
            pass
        
        return None
    
    async def _send_backup_alert(self, message: str, metrics: ScheduleMetrics, decision: Dict[str, Any]):
        """Send backup alert notification"""
        try:
            alert_data = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'message': message,
                'metrics': asdict(metrics),
                'decision': decision
            }
            
            # Log the alert
            logger.critical(f"BACKUP ALERT: {message}")
            logger.info(f"Alert data: {json.dumps(alert_data, default=str)}")
            
            # Here you would implement actual alerting (webhook, email, etc.)
            
        except Exception as e:
            logger.error(f"Failed to send backup alert: {e}")
    
    async def _log_scheduling_decision(self, metrics: ScheduleMetrics, decision: Dict[str, Any]):
        """Log scheduling decision for audit and analysis"""
        try:
            log_entry = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'metrics': asdict(metrics),
                'decision': decision
            }
            
            log_file = Path("/var/log/financial_planning/backup_scheduler.log")
            log_file.parent.mkdir(parents=True, exist_ok=True)
            
            async with aiofiles.open(log_file, 'a') as f:
                await f.write(json.dumps(log_entry, default=str) + '\n')
                
        except Exception as e:
            logger.error(f"Failed to log scheduling decision: {e}")


class BackupSchedulerService:
    """Service wrapper for backup scheduler"""
    
    def __init__(self, config_path: str = None):
        self.scheduler = IntelligentBackupScheduler(config_path)
        self.pid_file = Path("/var/run/backup_scheduler.pid")
    
    async def start_service(self):
        """Start scheduler as a service"""
        try:
            # Write PID file
            self.pid_file.parent.mkdir(parents=True, exist_ok=True)
            async with aiofiles.open(self.pid_file, 'w') as f:
                await f.write(str(os.getpid()))
            
            # Start scheduler
            await self.scheduler.run_scheduler()
            
        except Exception as e:
            logger.error(f"Service start failed: {e}")
        finally:
            # Clean up PID file
            if self.pid_file.exists():
                self.pid_file.unlink()
    
    async def stop_service(self):
        """Stop scheduler service"""
        await self.scheduler.stop_scheduler()
        
        if self.pid_file.exists():
            self.pid_file.unlink()


async def main():
    """Main function for CLI usage"""
    import argparse
    import os
    import signal
    
    parser = argparse.ArgumentParser(description='Intelligent Backup Scheduler')
    parser.add_argument('action', choices=['start', 'stop', 'status', 'test'])
    parser.add_argument('--config', help='Configuration file path')
    parser.add_argument('--daemon', action='store_true', help='Run as daemon')
    parser.add_argument('--policy', help='Schedule policy to use')
    
    args = parser.parse_args()
    
    if args.action == 'start':
        service = BackupSchedulerService(args.config)
        
        if args.daemon:
            # Fork to background
            if os.fork() > 0:
                return 0
        
        # Handle shutdown signals
        def signal_handler(signum, frame):
            asyncio.create_task(service.stop_service())
        
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)
        
        await service.start_service()
    
    elif args.action == 'stop':
        pid_file = Path("/var/run/backup_scheduler.pid")
        if pid_file.exists():
            with open(pid_file, 'r') as f:
                pid = int(f.read().strip())
            
            try:
                os.kill(pid, signal.SIGTERM)
                print(f"Stopped backup scheduler (PID: {pid})")
            except ProcessLookupError:
                print("Backup scheduler not running")
                pid_file.unlink()
        else:
            print("Backup scheduler not running")
    
    elif args.action == 'status':
        pid_file = Path("/var/run/backup_scheduler.pid")
        if pid_file.exists():
            with open(pid_file, 'r') as f:
                pid = int(f.read().strip())
            
            try:
                os.kill(pid, 0)  # Check if process exists
                print(f"Backup scheduler running (PID: {pid})")
            except ProcessLookupError:
                print("Backup scheduler not running (stale PID file)")
                pid_file.unlink()
        else:
            print("Backup scheduler not running")
    
    elif args.action == 'test':
        scheduler = IntelligentBackupScheduler(args.config)
        if args.policy:
            if args.policy in scheduler.schedule_policies:
                scheduler.current_policy = scheduler.schedule_policies[args.policy]
                print(f"Using policy: {args.policy}")
            else:
                print(f"Policy '{args.policy}' not found")
                return 1
        
        # Run one scheduling cycle
        metrics = await scheduler.collect_system_metrics()
        decision = await scheduler.adaptive_scheduling_decision(metrics)
        
        print(f"System Metrics:")
        print(f"  Database size: {metrics.database_size_gb:.2f} GB")
        print(f"  Transaction rate: {metrics.transaction_rate:.0f}/min")
        print(f"  System load: {metrics.system_load:.2f}")
        print(f"  Available disk: {metrics.available_disk_space_gb:.2f} GB")
        
        print(f"\nScheduling Decision:")
        print(f"  Trigger backup: {decision['should_trigger_backup']}")
        print(f"  Backup type: {decision['backup_type']}")
        print(f"  Priority: {decision['priority']}")
        print(f"  Delay: {decision['delay_minutes']} minutes")
        print(f"  Reasons: {', '.join(decision['reason'])}")


if __name__ == "__main__":
    import os
    exit_code = asyncio.run(main())
    exit(exit_code)