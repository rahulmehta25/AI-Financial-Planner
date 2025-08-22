#!/usr/bin/env python3
"""
Database Replication Manager for Financial Planning System
Implements master-slave replication with automatic failover
"""

import asyncio
import asyncpg
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Dict, List, Optional, Any
import logging
import json
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, asdict
import yaml
from pathlib import Path
import subprocess
import time
import boto3
from enum import Enum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ReplicationRole(Enum):
    MASTER = "master"
    SLAVE = "slave"
    STANDBY = "standby"


class ReplicationHealth(Enum):
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    FAILED = "failed"


@dataclass
class DatabaseNode:
    """Database node configuration"""
    node_id: str
    host: str
    port: int
    database: str
    username: str
    password: str
    role: ReplicationRole
    region: str
    availability_zone: str
    
    # Connection pool settings
    max_connections: int = 100
    min_connections: int = 10
    
    # Health check settings
    health_check_interval: int = 30
    timeout_seconds: int = 10
    
    # Replication settings
    replication_slot: Optional[str] = None
    replication_user: Optional[str] = None
    wal_level: str = "replica"


@dataclass
class ReplicationStatus:
    """Replication status information"""
    master_node: str
    slave_nodes: List[str]
    timestamp: datetime
    
    # Lag information
    replication_lag_bytes: int = 0
    replication_lag_seconds: float = 0.0
    
    # Health status
    master_health: ReplicationHealth = ReplicationHealth.HEALTHY
    slave_health: Dict[str, ReplicationHealth] = None
    
    # Performance metrics
    master_tps: float = 0.0
    slave_tps: Dict[str, float] = None
    
    def __post_init__(self):
        if self.slave_health is None:
            self.slave_health = {}
        if self.slave_tps is None:
            self.slave_tps = {}


class DatabaseReplicationManager:
    """Manages database replication with automatic failover"""
    
    def __init__(self, config_path: str = None):
        self.config = self._load_config(config_path)
        self.nodes: Dict[str, DatabaseNode] = {}
        self.current_master: Optional[str] = None
        self.connection_pools: Dict[str, Any] = {}
        
        # Monitoring
        self.replication_status: Optional[ReplicationStatus] = None
        self.monitoring_task: Optional[asyncio.Task] = None
        self.is_monitoring = False
        
        # Failover
        self.failover_in_progress = False
        self.failover_lock = asyncio.Lock()
        
        # Load nodes from configuration
        self._initialize_nodes()
    
    def _load_config(self, config_path: str = None) -> Dict[str, Any]:
        """Load replication configuration"""
        default_config = {
            'replication': {
                'monitoring_interval': 30,
                'failover_timeout': 300,
                'lag_threshold_seconds': 60,
                'health_check_retries': 3,
                'enable_automatic_failover': True
            },
            'nodes': {}
        }
        
        if config_path and Path(config_path).exists():
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                return {**default_config, **config}
        
        return default_config
    
    def _initialize_nodes(self):
        """Initialize database nodes from configuration"""
        for node_id, node_config in self.config.get('nodes', {}).items():
            self.nodes[node_id] = DatabaseNode(
                node_id=node_id,
                **node_config
            )
            
            # Set current master
            if self.nodes[node_id].role == ReplicationRole.MASTER:
                self.current_master = node_id
    
    async def initialize_connections(self):
        """Initialize connection pools for all nodes"""
        for node_id, node in self.nodes.items():
            try:
                # Create connection pool
                pool = await asyncpg.create_pool(
                    host=node.host,
                    port=node.port,
                    database=node.database,
                    user=node.username,
                    password=node.password,
                    min_size=node.min_connections,
                    max_size=node.max_connections,
                    command_timeout=node.timeout_seconds
                )
                
                self.connection_pools[node_id] = pool
                logger.info(f"Initialized connection pool for node {node_id}")
                
            except Exception as e:
                logger.error(f"Failed to initialize connection pool for {node_id}: {e}")
    
    async def setup_replication(self, master_node_id: str, slave_node_ids: List[str]):
        """Set up master-slave replication"""
        master_node = self.nodes[master_node_id]
        
        try:
            # Configure master for replication
            await self._configure_master(master_node)
            
            # Configure slaves
            for slave_id in slave_node_ids:
                slave_node = self.nodes[slave_id]
                await self._configure_slave(master_node, slave_node)
            
            # Update roles
            master_node.role = ReplicationRole.MASTER
            for slave_id in slave_node_ids:
                self.nodes[slave_id].role = ReplicationRole.SLAVE
            
            self.current_master = master_node_id
            
            logger.info(f"Replication setup completed: Master={master_node_id}, Slaves={slave_node_ids}")
            
        except Exception as e:
            logger.error(f"Failed to setup replication: {e}")
            raise
    
    async def _configure_master(self, master_node: DatabaseNode):
        """Configure master node for replication"""
        pool = self.connection_pools[master_node.node_id]
        
        async with pool.acquire() as conn:
            # Create replication user if not exists
            replication_user = master_node.replication_user or f"repl_{master_node.node_id}"
            
            await conn.execute(f"""
                DO $$
                BEGIN
                    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = '{replication_user}') THEN
                        CREATE USER {replication_user} WITH REPLICATION LOGIN PASSWORD '{master_node.password}';
                    END IF;
                END
                $$;
            """)
            
            # Create replication slot
            slot_name = master_node.replication_slot or f"slot_{master_node.node_id}"
            
            try:
                await conn.execute(f"SELECT pg_create_physical_replication_slot('{slot_name}')")
                logger.info(f"Created replication slot: {slot_name}")
            except Exception as e:
                if "already exists" not in str(e):
                    raise
            
            # Configure PostgreSQL settings for replication
            replication_settings = {
                'wal_level': 'replica',
                'max_wal_senders': '10',
                'wal_keep_segments': '32',
                'archive_mode': 'on',
                'archive_command': f"cp %p /var/lib/postgresql/archive/%f"
            }
            
            for setting, value in replication_settings.items():
                await conn.execute(f"ALTER SYSTEM SET {setting} = '{value}'")
            
            # Reload configuration
            await conn.execute("SELECT pg_reload_conf()")
    
    async def _configure_slave(self, master_node: DatabaseNode, slave_node: DatabaseNode):
        """Configure slave node for replication"""
        # Create recovery.conf file for the slave
        recovery_conf = f"""
standby_mode = 'on'
primary_conninfo = 'host={master_node.host} port={master_node.port} user={master_node.replication_user or master_node.username} password={master_node.password}'
primary_slot_name = '{master_node.replication_slot or f"slot_{master_node.node_id}"}'
restore_command = 'cp /var/lib/postgresql/archive/%f %p'
archive_cleanup_command = 'pg_archivecleanup /var/lib/postgresql/archive %r'
"""
        
        # This would normally involve setting up the slave's data directory
        # and configuring it to connect to the master
        logger.info(f"Configured slave {slave_node.node_id} to replicate from {master_node.node_id}")
    
    async def start_monitoring(self):
        """Start replication monitoring"""
        if self.is_monitoring:
            return
        
        self.is_monitoring = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        logger.info("Started replication monitoring")
    
    async def stop_monitoring(self):
        """Stop replication monitoring"""
        self.is_monitoring = False
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        logger.info("Stopped replication monitoring")
    
    async def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.is_monitoring:
            try:
                # Check replication status
                status = await self.check_replication_status()
                self.replication_status = status
                
                # Check for failover conditions
                if await self._should_trigger_failover(status):
                    if self.config['replication']['enable_automatic_failover']:
                        await self.trigger_failover()
                    else:
                        logger.warning("Failover conditions met but automatic failover is disabled")
                
                # Log status
                await self._log_replication_status(status)
                
                # Wait for next check
                interval = self.config['replication']['monitoring_interval']
                await asyncio.sleep(interval)
                
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                await asyncio.sleep(30)  # Wait before retry
    
    async def check_replication_status(self) -> ReplicationStatus:
        """Check current replication status"""
        if not self.current_master:
            raise ValueError("No master node configured")
        
        master_node = self.nodes[self.current_master]
        slave_nodes = [
            node_id for node_id, node in self.nodes.items()
            if node.role == ReplicationRole.SLAVE
        ]
        
        status = ReplicationStatus(
            master_node=self.current_master,
            slave_nodes=slave_nodes,
            timestamp=datetime.now(timezone.utc)
        )
        
        # Check master health
        status.master_health = await self._check_node_health(self.current_master)
        
        # Check slave health and lag
        for slave_id in slave_nodes:
            status.slave_health[slave_id] = await self._check_node_health(slave_id)
            
            # Get replication lag
            lag_info = await self._get_replication_lag(self.current_master, slave_id)
            if lag_info:
                status.replication_lag_bytes = max(status.replication_lag_bytes, lag_info['lag_bytes'])
                status.replication_lag_seconds = max(status.replication_lag_seconds, lag_info['lag_seconds'])
        
        # Get transaction rates
        status.master_tps = await self._get_transaction_rate(self.current_master)
        for slave_id in slave_nodes:
            status.slave_tps[slave_id] = await self._get_transaction_rate(slave_id)
        
        return status
    
    async def _check_node_health(self, node_id: str) -> ReplicationHealth:
        """Check health of a specific node"""
        if node_id not in self.connection_pools:
            return ReplicationHealth.FAILED
        
        pool = self.connection_pools[node_id]
        retries = self.config['replication']['health_check_retries']
        
        for attempt in range(retries):
            try:
                async with pool.acquire() as conn:
                    # Simple health check query
                    result = await conn.fetchval("SELECT 1")
                    if result == 1:
                        return ReplicationHealth.HEALTHY
            except Exception as e:
                logger.warning(f"Health check failed for {node_id} (attempt {attempt + 1}): {e}")
                if attempt < retries - 1:
                    await asyncio.sleep(1)
        
        return ReplicationHealth.FAILED
    
    async def _get_replication_lag(self, master_id: str, slave_id: str) -> Optional[Dict[str, Any]]:
        """Get replication lag between master and slave"""
        try:
            master_pool = self.connection_pools[master_id]
            
            async with master_pool.acquire() as conn:
                # Get current WAL position on master
                master_lsn = await conn.fetchval("SELECT pg_current_wal_lsn()")
                
                # Get replication status
                replication_info = await conn.fetch("""
                    SELECT 
                        client_addr,
                        sent_lsn,
                        write_lsn,
                        flush_lsn,
                        replay_lsn,
                        EXTRACT(EPOCH FROM (now() - backend_start)) as connection_time
                    FROM pg_stat_replication
                    WHERE application_name = $1
                """, slave_id)
                
                if replication_info:
                    info = replication_info[0]
                    
                    # Calculate lag in bytes
                    lag_bytes = await conn.fetchval("""
                        SELECT pg_wal_lsn_diff($1, $2)
                    """, master_lsn, info['replay_lsn'])
                    
                    return {
                        'lag_bytes': lag_bytes or 0,
                        'lag_seconds': info['connection_time'] or 0,
                        'master_lsn': master_lsn,
                        'slave_lsn': info['replay_lsn']
                    }
        
        except Exception as e:
            logger.error(f"Failed to get replication lag for {slave_id}: {e}")
        
        return None
    
    async def _get_transaction_rate(self, node_id: str) -> float:
        """Get transaction rate for a node"""
        try:
            pool = self.connection_pools[node_id]
            
            async with pool.acquire() as conn:
                result = await conn.fetchrow("""
                    SELECT 
                        xact_commit + xact_rollback as total_transactions
                    FROM pg_stat_database 
                    WHERE datname = current_database()
                """)
                
                if result:
                    return float(result['total_transactions'])
        
        except Exception as e:
            logger.error(f"Failed to get transaction rate for {node_id}: {e}")
        
        return 0.0
    
    async def _should_trigger_failover(self, status: ReplicationStatus) -> bool:
        """Determine if failover should be triggered"""
        # Master is unhealthy
        if status.master_health in [ReplicationHealth.CRITICAL, ReplicationHealth.FAILED]:
            logger.warning(f"Master node {status.master_node} is unhealthy: {status.master_health}")
            return True
        
        # Replication lag exceeds threshold
        lag_threshold = self.config['replication']['lag_threshold_seconds']
        if status.replication_lag_seconds > lag_threshold:
            logger.warning(f"Replication lag ({status.replication_lag_seconds}s) exceeds threshold ({lag_threshold}s)")
            return True
        
        # No healthy slaves available
        healthy_slaves = [
            slave_id for slave_id, health in status.slave_health.items()
            if health == ReplicationHealth.HEALTHY
        ]
        
        if not healthy_slaves:
            logger.warning("No healthy slave nodes available")
            return False  # Can't failover without healthy slaves
        
        return False
    
    async def trigger_failover(self, target_slave: str = None) -> bool:
        """Trigger failover to a slave node"""
        async with self.failover_lock:
            if self.failover_in_progress:
                logger.warning("Failover already in progress")
                return False
            
            self.failover_in_progress = True
        
        try:
            logger.info("Starting automatic failover process")
            
            # Select target slave if not specified
            if not target_slave:
                target_slave = await self._select_failover_target()
            
            if not target_slave:
                logger.error("No suitable failover target found")
                return False
            
            # Perform failover
            success = await self._perform_failover(target_slave)
            
            if success:
                logger.info(f"Failover completed successfully: New master is {target_slave}")
                
                # Send notification
                await self._send_failover_notification(self.current_master, target_slave)
            else:
                logger.error("Failover failed")
            
            return success
            
        finally:
            self.failover_in_progress = False
    
    async def _select_failover_target(self) -> Optional[str]:
        """Select the best slave for failover"""
        if not self.replication_status:
            return None
        
        # Find healthy slaves
        healthy_slaves = [
            slave_id for slave_id, health in self.replication_status.slave_health.items()
            if health == ReplicationHealth.HEALTHY
        ]
        
        if not healthy_slaves:
            return None
        
        # Select slave with lowest lag
        best_slave = None
        lowest_lag = float('inf')
        
        for slave_id in healthy_slaves:
            # Get individual lag for this slave
            lag_info = await self._get_replication_lag(self.current_master, slave_id)
            if lag_info and lag_info['lag_seconds'] < lowest_lag:
                lowest_lag = lag_info['lag_seconds']
                best_slave = slave_id
        
        return best_slave
    
    async def _perform_failover(self, target_slave: str) -> bool:
        """Perform the actual failover process"""
        try:
            old_master = self.current_master
            
            # Step 1: Stop writes to old master
            logger.info(f"Stopping writes to old master: {old_master}")
            await self._stop_writes_to_master(old_master)
            
            # Step 2: Wait for slave to catch up
            logger.info(f"Waiting for slave {target_slave} to catch up")
            await self._wait_for_slave_catchup(target_slave, timeout=60)
            
            # Step 3: Promote slave to master
            logger.info(f"Promoting slave {target_slave} to master")
            await self._promote_slave_to_master(target_slave)
            
            # Step 4: Update configuration
            self.current_master = target_slave
            self.nodes[target_slave].role = ReplicationRole.MASTER
            if old_master in self.nodes:
                self.nodes[old_master].role = ReplicationRole.STANDBY
            
            # Step 5: Reconfigure other slaves
            logger.info("Reconfiguring remaining slaves")
            await self._reconfigure_slaves_for_new_master(target_slave, old_master)
            
            return True
            
        except Exception as e:
            logger.error(f"Failover failed: {e}")
            return False
    
    async def _stop_writes_to_master(self, master_id: str):
        """Stop writes to the master node"""
        pool = self.connection_pools[master_id]
        
        async with pool.acquire() as conn:
            # Set database to read-only mode
            await conn.execute("ALTER SYSTEM SET default_transaction_read_only = on")
            await conn.execute("SELECT pg_reload_conf()")
    
    async def _wait_for_slave_catchup(self, slave_id: str, timeout: int = 60):
        """Wait for slave to catch up with master"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            lag_info = await self._get_replication_lag(self.current_master, slave_id)
            
            if lag_info and lag_info['lag_bytes'] == 0:
                logger.info(f"Slave {slave_id} has caught up")
                return
            
            await asyncio.sleep(1)
        
        logger.warning(f"Slave {slave_id} did not catch up within {timeout} seconds")
    
    async def _promote_slave_to_master(self, slave_id: str):
        """Promote slave to master"""
        pool = self.connection_pools[slave_id]
        
        async with pool.acquire() as conn:
            # Promote standby
            await conn.execute("SELECT pg_promote()")
            
            # Remove read-only restriction
            await conn.execute("ALTER SYSTEM SET default_transaction_read_only = off")
            await conn.execute("SELECT pg_reload_conf()")
    
    async def _reconfigure_slaves_for_new_master(self, new_master_id: str, old_master_id: str):
        """Reconfigure remaining slaves to follow new master"""
        new_master_node = self.nodes[new_master_id]
        
        for node_id, node in self.nodes.items():
            if (node.role == ReplicationRole.SLAVE and 
                node_id != new_master_id and 
                node_id != old_master_id):
                
                # Update slave's primary connection info
                # This would involve updating recovery.conf or recovery.signal
                logger.info(f"Reconfiguring slave {node_id} for new master {new_master_id}")
    
    async def _send_failover_notification(self, old_master: str, new_master: str):
        """Send notification about failover event"""
        notification = {
            'event': 'database_failover',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'old_master': old_master,
            'new_master': new_master,
            'replication_status': asdict(self.replication_status) if self.replication_status else None
        }
        
        logger.critical(f"DATABASE FAILOVER: {old_master} -> {new_master}")
        
        # Here you would implement actual notification sending
        # (email, webhook, PagerDuty, etc.)
    
    async def _log_replication_status(self, status: ReplicationStatus):
        """Log replication status for monitoring"""
        log_entry = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'replication_status': asdict(status)
        }
        
        # Log to file or monitoring system
        logger.info(f"Replication status: Master={status.master_node}, "
                   f"Lag={status.replication_lag_seconds:.2f}s, "
                   f"Health={status.master_health.value}")
    
    async def get_status_report(self) -> Dict[str, Any]:
        """Get comprehensive replication status report"""
        if not self.replication_status:
            await self.check_replication_status()
        
        return {
            'current_master': self.current_master,
            'failover_in_progress': self.failover_in_progress,
            'monitoring_active': self.is_monitoring,
            'replication_status': asdict(self.replication_status) if self.replication_status else None,
            'node_configurations': {
                node_id: {
                    'role': node.role.value,
                    'region': node.region,
                    'availability_zone': node.availability_zone
                }
                for node_id, node in self.nodes.items()
            }
        }


async def main():
    """Main function for CLI usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Database Replication Manager')
    parser.add_argument('action', choices=['setup', 'monitor', 'failover', 'status'])
    parser.add_argument('--config', help='Configuration file path')
    parser.add_argument('--master', help='Master node ID for setup')
    parser.add_argument('--slaves', nargs='+', help='Slave node IDs for setup')
    parser.add_argument('--target', help='Target slave for failover')
    
    args = parser.parse_args()
    
    replication_manager = DatabaseReplicationManager(args.config)
    await replication_manager.initialize_connections()
    
    try:
        if args.action == 'setup':
            if not args.master or not args.slaves:
                print("Error: --master and --slaves required for setup")
                return 1
            
            await replication_manager.setup_replication(args.master, args.slaves)
            print(f"Replication setup completed: Master={args.master}, Slaves={args.slaves}")
        
        elif args.action == 'monitor':
            await replication_manager.start_monitoring()
            print("Monitoring started. Press Ctrl+C to stop.")
            
            try:
                while True:
                    await asyncio.sleep(60)
                    status = await replication_manager.get_status_report()
                    print(f"Status: {json.dumps(status, indent=2, default=str)}")
            except KeyboardInterrupt:
                await replication_manager.stop_monitoring()
        
        elif args.action == 'failover':
            success = await replication_manager.trigger_failover(args.target)
            if success:
                print("Failover completed successfully")
            else:
                print("Failover failed")
                return 1
        
        elif args.action == 'status':
            status = await replication_manager.get_status_report()
            print(json.dumps(status, indent=2, default=str))
        
        return 0
        
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)