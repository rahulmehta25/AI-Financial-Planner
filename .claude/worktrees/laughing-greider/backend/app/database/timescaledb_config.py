"""
TimescaleDB Configuration and Optimization for Financial Planning System

This module provides comprehensive TimescaleDB setup, hypertable management,
and optimization for time-series financial data including market data,
portfolio performance, and transaction history.
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.infrastructure.database import timescale_manager
from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class HypertableConfig:
    """Configuration for TimescaleDB hypertables"""
    table_name: str
    time_column: str
    chunk_time_interval: str
    partition_column: Optional[str] = None
    number_partitions: Optional[int] = None
    compress_after: Optional[str] = None
    retention_period: Optional[str] = None


@dataclass
class ContinuousAggregateConfig:
    """Configuration for TimescaleDB continuous aggregates"""
    view_name: str
    base_table: str
    time_column: str
    bucket_width: str
    aggregation_columns: List[str]
    refresh_policy_start: str = "1 day"
    refresh_policy_end: str = "1 hour"
    refresh_interval: str = "1 hour"


class TimescaleDBConfigurator:
    """
    Comprehensive TimescaleDB configuration manager for financial planning system
    """
    
    def __init__(self):
        self.hypertable_configs = self._get_hypertable_configs()
        self.continuous_aggregate_configs = self._get_continuous_aggregate_configs()
        
    def _get_hypertable_configs(self) -> List[HypertableConfig]:
        """Define all hypertable configurations for the financial planning system"""
        return [
            # Market data - highest volume, most frequent writes
            HypertableConfig(
                table_name="enhanced_market_data",
                time_column="time",
                chunk_time_interval="1 day",  # 1-day chunks for high volume
                compress_after="7 days",  # Compress week-old data
                retention_period="5 years"  # Keep 5 years of market data
            ),
            
            # Transaction data - moderate volume, historical importance
            HypertableConfig(
                table_name="enhanced_transactions", 
                time_column="trade_date",
                chunk_time_interval="1 week",  # Weekly chunks for moderate volume
                compress_after="30 days",  # Compress month-old transactions
                retention_period="10 years"  # Legal requirement for transaction records
            ),
            
            # User activity log - high volume, compliance importance
            HypertableConfig(
                table_name="user_activity_log",
                time_column="timestamp", 
                chunk_time_interval="1 day",  # Daily chunks for audit logs
                compress_after="90 days",  # Compress quarterly
                retention_period="7 years"  # Compliance requirement
            ),
            
            # Portfolio performance snapshots - daily/weekly snapshots
            HypertableConfig(
                table_name="portfolio_performance_snapshots",
                time_column="snapshot_time",
                chunk_time_interval="1 month",  # Monthly chunks for performance data
                compress_after="1 year",  # Compress yearly data
                retention_period="20 years"  # Long-term performance tracking
            ),
            
            # System events - operational monitoring
            HypertableConfig(
                table_name="system_events",
                time_column="timestamp",
                chunk_time_interval="1 day",  # Daily chunks for system events
                compress_after="30 days",  # Compress monthly
                retention_period="2 years"  # 2 years of system history
            ),
            
            # Monte Carlo simulation results - large datasets
            HypertableConfig(
                table_name="monte_carlo_results",
                time_column="created_at",
                chunk_time_interval="1 week",  # Weekly chunks for simulation data
                compress_after="6 months",  # Compress semi-annually 
                retention_period="5 years"  # Keep simulation history
            )
        ]
    
    def _get_continuous_aggregate_configs(self) -> List[ContinuousAggregateConfig]:
        """Define continuous aggregates for common query patterns"""
        return [
            # Daily market data aggregates
            ContinuousAggregateConfig(
                view_name="market_data_daily",
                base_table="enhanced_market_data",
                time_column="time",
                bucket_width="1 day",
                aggregation_columns=[
                    "symbol",
                    "first(open, time) as open",
                    "max(high) as high", 
                    "min(low) as low",
                    "last(close, time) as close",
                    "sum(volume) as volume",
                    "avg(vwap) as avg_vwap"
                ]
            ),
            
            # Weekly market data aggregates
            ContinuousAggregateConfig(
                view_name="market_data_weekly",
                base_table="enhanced_market_data", 
                time_column="time",
                bucket_width="1 week",
                aggregation_columns=[
                    "symbol",
                    "first(open, time) as open",
                    "max(high) as high",
                    "min(low) as low", 
                    "last(close, time) as close",
                    "sum(volume) as volume",
                    "avg(vwap) as avg_vwap",
                    "stddev(close) as volatility"
                ]
            ),
            
            # Monthly market data aggregates
            ContinuousAggregateConfig(
                view_name="market_data_monthly",
                base_table="enhanced_market_data",
                time_column="time", 
                bucket_width="1 month",
                aggregation_columns=[
                    "symbol",
                    "first(open, time) as open",
                    "max(high) as high",
                    "min(low) as low",
                    "last(close, time) as close", 
                    "sum(volume) as volume",
                    "avg(close) as avg_close",
                    "stddev(close) as volatility",
                    "avg(rsi_14) as avg_rsi"
                ]
            ),
            
            # Portfolio performance aggregates
            ContinuousAggregateConfig(
                view_name="portfolio_performance_daily",
                base_table="portfolio_performance_snapshots",
                time_column="snapshot_time",
                bucket_width="1 day",
                aggregation_columns=[
                    "portfolio_id",
                    "last(total_value, snapshot_time) as end_value",
                    "first(total_value, snapshot_time) as start_value",
                    "max(total_value) - min(total_value) as daily_range"
                ]
            ),
            
            # Transaction volume aggregates
            ContinuousAggregateConfig(
                view_name="transaction_volume_daily",
                base_table="enhanced_transactions",
                time_column="trade_date",
                bucket_width="1 day",
                aggregation_columns=[
                    "account_id",
                    "count(*) as transaction_count",
                    "sum(total_amount) as total_volume", 
                    "sum(total_fees) as total_fees",
                    "count(*) filter (where type = 'buy') as buy_count",
                    "count(*) filter (where type = 'sell') as sell_count"
                ]
            ),
            
            # User activity aggregates
            ContinuousAggregateConfig(
                view_name="user_activity_hourly", 
                base_table="user_activity_log",
                time_column="timestamp",
                bucket_width="1 hour",
                aggregation_columns=[
                    "user_id",
                    "count(*) as activity_count",
                    "count(distinct activity_type) as unique_activities",
                    "avg(duration_ms) as avg_duration",
                    "count(*) filter (where status = 'failure') as failure_count"
                ]
            )
        ]
    
    async def setup_timescaledb(self, session: AsyncSession) -> Dict[str, Any]:
        """
        Complete TimescaleDB setup including extensions, hypertables, and optimizations
        """
        setup_results = {
            "timescaledb_enabled": False,
            "hypertables_created": [],
            "continuous_aggregates_created": [],
            "policies_applied": [],
            "errors": []
        }
        
        try:
            # Check if TimescaleDB extension is available
            result = await session.execute(
                text("SELECT EXISTS(SELECT 1 FROM pg_available_extensions WHERE name = 'timescaledb')")
            )
            extension_available = result.scalar()
            
            if not extension_available:
                setup_results["errors"].append("TimescaleDB extension not available")
                return setup_results
            
            # Create TimescaleDB extension
            await session.execute(text("CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;"))
            setup_results["timescaledb_enabled"] = True
            logger.info("TimescaleDB extension enabled")
            
            # Create hypertables
            for config in self.hypertable_configs:
                try:
                    await self._create_hypertable(session, config)
                    setup_results["hypertables_created"].append(config.table_name)
                    logger.info(f"Created hypertable: {config.table_name}")
                except Exception as e:
                    setup_results["errors"].append(f"Failed to create hypertable {config.table_name}: {e}")
                    logger.error(f"Failed to create hypertable {config.table_name}: {e}")
            
            # Create continuous aggregates
            for config in self.continuous_aggregate_configs:
                try:
                    await self._create_continuous_aggregate(session, config)
                    setup_results["continuous_aggregates_created"].append(config.view_name)
                    logger.info(f"Created continuous aggregate: {config.view_name}")
                except Exception as e:
                    setup_results["errors"].append(f"Failed to create continuous aggregate {config.view_name}: {e}")
                    logger.error(f"Failed to create continuous aggregate {config.view_name}: {e}")
            
            # Apply compression and retention policies
            for config in self.hypertable_configs:
                try:
                    policies_applied = await self._apply_policies(session, config)
                    setup_results["policies_applied"].extend(policies_applied)
                except Exception as e:
                    setup_results["errors"].append(f"Failed to apply policies for {config.table_name}: {e}")
                    logger.error(f"Failed to apply policies for {config.table_name}: {e}")
            
            # Commit all changes
            await session.commit()
            logger.info("TimescaleDB setup completed successfully")
            
        except Exception as e:
            await session.rollback()
            setup_results["errors"].append(f"TimescaleDB setup failed: {e}")
            logger.error(f"TimescaleDB setup failed: {e}")
        
        return setup_results
    
    async def _create_hypertable(self, session: AsyncSession, config: HypertableConfig) -> None:
        """Create a hypertable with the specified configuration"""
        
        # Check if table exists
        check_table = await session.execute(
            text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = :table_name
                )
            """),
            {"table_name": config.table_name}
        )
        
        if not check_table.scalar():
            logger.warning(f"Table {config.table_name} does not exist, skipping hypertable creation")
            return
        
        # Check if already a hypertable
        check_hypertable = await session.execute(
            text("""
                SELECT EXISTS (
                    SELECT FROM timescaledb_information.hypertables 
                    WHERE hypertable_name = :table_name
                )
            """),
            {"table_name": config.table_name}
        )
        
        if check_hypertable.scalar():
            logger.info(f"Table {config.table_name} is already a hypertable")
            return
        
        # Create hypertable
        create_query = f"""
            SELECT create_hypertable(
                '{config.table_name}',
                '{config.time_column}',
                chunk_time_interval => INTERVAL '{config.chunk_time_interval}',
                if_not_exists => TRUE
            );
        """
        
        # Add partitioning if specified
        if config.partition_column and config.number_partitions:
            create_query = f"""
                SELECT create_hypertable(
                    '{config.table_name}',
                    '{config.time_column}',
                    '{config.partition_column}',
                    {config.number_partitions},
                    chunk_time_interval => INTERVAL '{config.chunk_time_interval}',
                    if_not_exists => TRUE
                );
            """
        
        await session.execute(text(create_query))
        logger.info(f"Created hypertable for {config.table_name}")
    
    async def _create_continuous_aggregate(self, session: AsyncSession, config: ContinuousAggregateConfig) -> None:
        """Create a continuous aggregate view"""
        
        # Check if view already exists
        check_view = await session.execute(
            text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.views 
                    WHERE table_name = :view_name
                )
            """),
            {"view_name": config.view_name}
        )
        
        if check_view.scalar():
            logger.info(f"Continuous aggregate {config.view_name} already exists")
            return
        
        # Build aggregation query
        columns_str = ",\n    ".join(config.aggregation_columns)
        
        # Create continuous aggregate
        create_query = f"""
            CREATE MATERIALIZED VIEW {config.view_name}
            WITH (timescaledb.continuous) AS
            SELECT 
                time_bucket('{config.bucket_width}', {config.time_column}) AS bucket,
                {columns_str}
            FROM {config.base_table}
            GROUP BY bucket, {config.aggregation_columns[0].split(',')[0]}
            ORDER BY bucket;
        """
        
        await session.execute(text(create_query))
        
        # Add refresh policy
        policy_query = f"""
            SELECT add_continuous_aggregate_policy(
                '{config.view_name}',
                start_offset => INTERVAL '{config.refresh_policy_start}',
                end_offset => INTERVAL '{config.refresh_policy_end}',
                schedule_interval => INTERVAL '{config.refresh_interval}'
            );
        """
        
        await session.execute(text(policy_query))
        logger.info(f"Created continuous aggregate {config.view_name} with refresh policy")
    
    async def _apply_policies(self, session: AsyncSession, config: HypertableConfig) -> List[str]:
        """Apply compression and retention policies to a hypertable"""
        policies_applied = []
        
        # Apply compression policy
        if config.compress_after:
            try:
                compress_query = f"""
                    SELECT add_compression_policy(
                        '{config.table_name}',
                        compress_after => INTERVAL '{config.compress_after}',
                        if_not_exists => TRUE
                    );
                """
                await session.execute(text(compress_query))
                policies_applied.append(f"compression:{config.table_name}")
                logger.info(f"Applied compression policy to {config.table_name}")
            except Exception as e:
                logger.warning(f"Failed to apply compression policy to {config.table_name}: {e}")
        
        # Apply retention policy
        if config.retention_period:
            try:
                retention_query = f"""
                    SELECT add_retention_policy(
                        '{config.table_name}',
                        drop_after => INTERVAL '{config.retention_period}',
                        if_not_exists => TRUE
                    );
                """
                await session.execute(text(retention_query))
                policies_applied.append(f"retention:{config.table_name}")
                logger.info(f"Applied retention policy to {config.table_name}")
            except Exception as e:
                logger.warning(f"Failed to apply retention policy to {config.table_name}: {e}")
        
        return policies_applied
    
    async def optimize_hypertables(self, session: AsyncSession) -> Dict[str, Any]:
        """Apply advanced optimizations to hypertables"""
        optimization_results = {
            "optimizations_applied": [],
            "statistics_updated": [],
            "errors": []
        }
        
        try:
            # Enable real-time aggregation
            for config in self.continuous_aggregate_configs:
                try:
                    realtime_query = f"""
                        ALTER MATERIALIZED VIEW {config.view_name} 
                        SET (timescaledb.materialized_only = false);
                    """
                    await session.execute(text(realtime_query))
                    optimization_results["optimizations_applied"].append(f"realtime:{config.view_name}")
                except Exception as e:
                    optimization_results["errors"].append(f"Failed to enable realtime for {config.view_name}: {e}")
            
            # Update table statistics for better query planning
            for config in self.hypertable_configs:
                try:
                    analyze_query = f"ANALYZE {config.table_name};"
                    await session.execute(text(analyze_query))
                    optimization_results["statistics_updated"].append(config.table_name)
                except Exception as e:
                    optimization_results["errors"].append(f"Failed to analyze {config.table_name}: {e}")
            
            # Create specialized indexes for common query patterns
            await self._create_specialized_indexes(session, optimization_results)
            
            await session.commit()
            logger.info("Hypertable optimizations completed")
            
        except Exception as e:
            await session.rollback()
            optimization_results["errors"].append(f"Optimization failed: {e}")
            logger.error(f"Hypertable optimization failed: {e}")
        
        return optimization_results
    
    async def _create_specialized_indexes(self, session: AsyncSession, results: Dict[str, Any]) -> None:
        """Create specialized indexes for time-series queries"""
        
        specialized_indexes = [
            # Market data indexes
            {
                "table": "enhanced_market_data",
                "index_name": "idx_market_data_symbol_time_desc",
                "definition": "CREATE INDEX IF NOT EXISTS idx_market_data_symbol_time_desc ON enhanced_market_data (symbol, time DESC);"
            },
            {
                "table": "enhanced_market_data",
                "index_name": "idx_market_data_volume_time",
                "definition": "CREATE INDEX IF NOT EXISTS idx_market_data_volume_time ON enhanced_market_data (volume, time) WHERE volume > 1000000;"
            },
            
            # Transaction indexes
            {
                "table": "enhanced_transactions",
                "index_name": "idx_transactions_account_symbol_date",
                "definition": "CREATE INDEX IF NOT EXISTS idx_transactions_account_symbol_date ON enhanced_transactions (account_id, symbol, trade_date DESC);"
            },
            {
                "table": "enhanced_transactions",
                "index_name": "idx_transactions_wash_sale_lookup",
                "definition": "CREATE INDEX IF NOT EXISTS idx_transactions_wash_sale_lookup ON enhanced_transactions (symbol, trade_date, wash_sale) WHERE wash_sale = true;"
            },
            
            # User activity indexes
            {
                "table": "user_activity_log",
                "index_name": "idx_activity_user_type_time",
                "definition": "CREATE INDEX IF NOT EXISTS idx_activity_user_type_time ON user_activity_log (user_id, activity_type, timestamp DESC);"
            }
        ]
        
        for index_config in specialized_indexes:
            try:
                await session.execute(text(index_config["definition"]))
                results["optimizations_applied"].append(f"index:{index_config['index_name']}")
                logger.info(f"Created specialized index: {index_config['index_name']}")
            except Exception as e:
                results["errors"].append(f"Failed to create index {index_config['index_name']}: {e}")
                logger.warning(f"Failed to create index {index_config['index_name']}: {e}")
    
    async def get_hypertable_stats(self, session: AsyncSession) -> Dict[str, Any]:
        """Get comprehensive statistics for all hypertables"""
        try:
            # Get hypertable information
            hypertables_query = """
                SELECT 
                    hypertable_name,
                    num_chunks,
                    table_bytes,
                    index_bytes,
                    toast_bytes,
                    total_bytes,
                    compression_enabled,
                    compressed_chunks,
                    uncompressed_chunks
                FROM timescaledb_information.hypertables h
                LEFT JOIN timescaledb_information.chunks c ON h.hypertable_name = c.hypertable_name
                LEFT JOIN timescaledb_information.compression_settings cs ON h.hypertable_name = cs.hypertable_name
                GROUP BY h.hypertable_name, h.num_chunks, h.table_bytes, h.index_bytes, h.toast_bytes, h.total_bytes, cs.compression_enabled;
            """
            
            result = await session.execute(text(hypertables_query))
            hypertable_stats = [dict(row._mapping) for row in result]
            
            # Get continuous aggregate information
            cagg_query = """
                SELECT 
                    view_name,
                    materialized_only,
                    compression_enabled
                FROM timescaledb_information.continuous_aggregates;
            """
            
            result = await session.execute(text(cagg_query))
            cagg_stats = [dict(row._mapping) for row in result]
            
            # Get policy information  
            policy_query = """
                SELECT 
                    hypertable,
                    job_type,
                    schedule_interval,
                    config
                FROM timescaledb_information.jobs 
                WHERE job_type IN ('compression', 'retention', 'continuous_aggregate');
            """
            
            result = await session.execute(text(policy_query))
            policy_stats = [dict(row._mapping) for row in result]
            
            return {
                "hypertables": hypertable_stats,
                "continuous_aggregates": cagg_stats,
                "policies": policy_stats,
                "total_hypertables": len(hypertable_stats),
                "total_continuous_aggregates": len(cagg_stats)
            }
            
        except Exception as e:
            logger.error(f"Failed to get hypertable stats: {e}")
            return {"error": str(e)}


# Global configurator instance
timescaledb_configurator = TimescaleDBConfigurator()


async def initialize_timescaledb() -> Dict[str, Any]:
    """
    Initialize TimescaleDB with all required configurations
    """
    logger.info("Starting TimescaleDB initialization")
    
    if not settings.TIMESCALEDB_ENABLED:
        logger.info("TimescaleDB is disabled in settings")
        return {"status": "disabled"}
    
    try:
        async with timescale_manager.get_async_session() as session:
            # Setup TimescaleDB
            setup_results = await timescaledb_configurator.setup_timescaledb(session)
            
            # Apply optimizations if setup was successful
            if setup_results["timescaledb_enabled"]:
                optimization_results = await timescaledb_configurator.optimize_hypertables(session)
                setup_results["optimizations"] = optimization_results
                
                # Get final statistics
                stats = await timescaledb_configurator.get_hypertable_stats(session)
                setup_results["statistics"] = stats
            
            logger.info("TimescaleDB initialization completed")
            return setup_results
            
    except Exception as e:
        logger.error(f"TimescaleDB initialization failed: {e}")
        return {"status": "failed", "error": str(e)}


async def refresh_continuous_aggregates() -> Dict[str, Any]:
    """
    Manually refresh all continuous aggregates
    """
    results = {
        "refreshed": [],
        "errors": []
    }
    
    try:
        async with timescale_manager.get_async_session() as session:
            for config in timescaledb_configurator.continuous_aggregate_configs:
                try:
                    refresh_query = f"""
                        CALL refresh_continuous_aggregate('{config.view_name}', NULL, NULL);
                    """
                    await session.execute(text(refresh_query))
                    results["refreshed"].append(config.view_name)
                    logger.info(f"Refreshed continuous aggregate: {config.view_name}")
                except Exception as e:
                    results["errors"].append(f"Failed to refresh {config.view_name}: {e}")
                    logger.error(f"Failed to refresh {config.view_name}: {e}")
            
            await session.commit()
            
    except Exception as e:
        logger.error(f"Failed to refresh continuous aggregates: {e}")
        results["errors"].append(str(e))
    
    return results


if __name__ == "__main__":
    # Run initialization if called directly
    asyncio.run(initialize_timescaledb())