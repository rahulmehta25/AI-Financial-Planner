"""
Database Initialization Script for Financial Planning System

This script handles complete database setup including:
- Table creation and migration
- Index optimization for all models
- Constraint validation
- Performance tuning
- TimescaleDB configuration
- Initial data seeding
"""

import logging
import asyncio
import sys
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
from pathlib import Path

import asyncpg
from sqlalchemy import create_engine, text, inspect, MetaData
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from alembic.config import Config
from alembic import command

from app.core.config import settings
from app.core.infrastructure.database import timescale_manager, db_manager, Base
from app.database.timescaledb_config import initialize_timescaledb
from app.models.enhanced_models import (
    User, Portfolio, Account, Transaction, EnhancedMarketData,
    UserActivityLog, RegulatoryReport
)

logger = logging.getLogger(__name__)


class DatabaseInitializer:
    """
    Comprehensive database initialization and setup manager
    """
    
    def __init__(self):
        self.engine = None
        self.async_engine = None
        self.metadata = Base.metadata
        
    async def initialize_complete_database(self) -> Dict[str, Any]:
        """
        Complete database initialization process
        """
        initialization_results = {
            "database_created": False,
            "migrations_applied": False,
            "indexes_created": [],
            "constraints_validated": [],
            "timescaledb_configured": False,
            "performance_optimized": False,
            "initial_data_seeded": False,
            "errors": [],
            "warnings": []
        }
        
        logger.info("Starting complete database initialization")
        
        try:
            # Step 1: Ensure database exists
            database_result = await self._ensure_database_exists()
            initialization_results.update(database_result)
            
            # Step 2: Apply Alembic migrations
            migration_result = await self._apply_migrations()
            initialization_results.update(migration_result)
            
            # Step 3: Create performance indexes
            index_result = await self._create_performance_indexes()
            initialization_results["indexes_created"] = index_result.get("indexes_created", [])
            if index_result.get("errors"):
                initialization_results["errors"].extend(index_result["errors"])
            
            # Step 4: Validate constraints
            constraint_result = await self._validate_constraints()
            initialization_results["constraints_validated"] = constraint_result.get("validated", [])
            if constraint_result.get("errors"):
                initialization_results["errors"].extend(constraint_result["errors"])
            
            # Step 5: Configure TimescaleDB
            timescale_result = await initialize_timescaledb()
            initialization_results["timescaledb_configured"] = timescale_result.get("timescaledb_enabled", False)
            if timescale_result.get("errors"):
                initialization_results["errors"].extend(timescale_result["errors"])
            
            # Step 6: Apply performance optimizations
            perf_result = await self._apply_performance_optimizations()
            initialization_results["performance_optimized"] = perf_result.get("success", False)
            if perf_result.get("errors"):
                initialization_results["errors"].extend(perf_result["errors"])
            
            # Step 7: Seed initial data
            seed_result = await self._seed_initial_data()
            initialization_results["initial_data_seeded"] = seed_result.get("success", False)
            if seed_result.get("errors"):
                initialization_results["errors"].extend(seed_result["errors"])
            
            logger.info("Database initialization completed successfully")
            
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            initialization_results["errors"].append(str(e))
        
        return initialization_results
    
    async def _ensure_database_exists(self) -> Dict[str, Any]:
        """
        Ensure the target database exists, create if needed
        """
        result = {"database_created": False, "errors": []}
        
        try:
            # Parse database URL to get connection details
            if settings.DATABASE_URL.startswith("postgresql"):
                # Extract database name from URL
                url_parts = settings.DATABASE_URL.split('/')
                db_name = url_parts[-1].split('?')[0]  # Remove query params
                base_url = '/'.join(url_parts[:-1])
                
                # Connect to postgres database to create target database
                postgres_url = f"{base_url}/postgres"
                
                engine = create_async_engine(postgres_url, poolclass=NullPool)
                
                async with engine.begin() as conn:
                    # Check if database exists
                    check_db = await conn.execute(
                        text("SELECT 1 FROM pg_database WHERE datname = :db_name"),
                        {"db_name": db_name}
                    )
                    
                    if not check_db.fetchone():
                        # Create database
                        await conn.execute(text(f"CREATE DATABASE {db_name}"))
                        result["database_created"] = True
                        logger.info(f"Created database: {db_name}")
                    else:
                        logger.info(f"Database {db_name} already exists")
                
                await engine.dispose()
            else:
                # For SQLite, database is created automatically
                result["database_created"] = True
                logger.info("SQLite database will be created automatically")
                
        except Exception as e:
            error_msg = f"Failed to ensure database exists: {e}"
            logger.error(error_msg)
            result["errors"].append(error_msg)
        
        return result
    
    async def _apply_migrations(self) -> Dict[str, Any]:
        """
        Apply Alembic database migrations
        """
        result = {"migrations_applied": False, "errors": []}
        
        try:
            # Setup Alembic configuration
            backend_dir = Path(__file__).parent.parent
            alembic_cfg = Config(str(backend_dir / "alembic.ini"))
            alembic_cfg.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
            
            # Apply migrations
            command.upgrade(alembic_cfg, "head")
            result["migrations_applied"] = True
            logger.info("Database migrations applied successfully")
            
        except Exception as e:
            error_msg = f"Failed to apply migrations: {e}"
            logger.error(error_msg)
            result["errors"].append(error_msg)
        
        return result
    
    async def _create_performance_indexes(self) -> Dict[str, Any]:
        """
        Create additional performance indexes beyond those in models
        """
        result = {"indexes_created": [], "errors": []}
        
        # Define additional performance indexes
        performance_indexes = [
            # User table performance indexes
            {
                "table": "enhanced_users",
                "name": "idx_enhanced_users_email_lower",
                "definition": "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_enhanced_users_email_lower ON enhanced_users (LOWER(email))"
            },
            {
                "table": "enhanced_users",
                "name": "idx_enhanced_users_kyc_expires",
                "definition": "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_enhanced_users_kyc_expires ON enhanced_users (kyc_expires_at) WHERE kyc_expires_at IS NOT NULL"
            },
            
            # Portfolio performance indexes
            {
                "table": "enhanced_portfolios",
                "name": "idx_enhanced_portfolios_user_active",
                "definition": "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_enhanced_portfolios_user_active ON enhanced_portfolios (user_id) WHERE status = 'active'"
            },
            {
                "table": "enhanced_portfolios",
                "name": "idx_enhanced_portfolios_rebalance_needed",
                "definition": "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_enhanced_portfolios_rebalance_needed ON enhanced_portfolios (last_rebalanced_at, auto_rebalancing_enabled) WHERE auto_rebalancing_enabled = true"
            },
            {
                "table": "enhanced_portfolios",
                "name": "idx_enhanced_portfolios_performance_ytd",
                "definition": "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_enhanced_portfolios_performance_ytd ON enhanced_portfolios (performance_ytd DESC) WHERE performance_ytd IS NOT NULL"
            },
            
            # Account performance indexes
            {
                "table": "enhanced_accounts",
                "name": "idx_enhanced_accounts_type_balance",
                "definition": "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_enhanced_accounts_type_balance ON enhanced_accounts (account_type, current_balance DESC)"
            },
            {
                "table": "enhanced_accounts",
                "name": "idx_enhanced_accounts_plaid_sync",
                "definition": "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_enhanced_accounts_plaid_sync ON enhanced_accounts (last_plaid_sync, plaid_sync_status) WHERE plaid_item_id IS NOT NULL"
            },
            {
                "table": "enhanced_accounts",
                "name": "idx_enhanced_accounts_retirement_contrib",
                "definition": "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_enhanced_accounts_retirement_contrib ON enhanced_accounts (account_type, employee_contribution_ytd) WHERE account_type IN ('401k', 'roth_ira', 'traditional_ira')"
            },
            
            # Transaction performance indexes
            {
                "table": "enhanced_transactions",
                "name": "idx_enhanced_transactions_symbol_date_desc",
                "definition": "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_enhanced_transactions_symbol_date_desc ON enhanced_transactions (symbol, trade_date DESC) WHERE symbol IS NOT NULL"
            },
            {
                "table": "enhanced_transactions",
                "name": "idx_enhanced_transactions_amount_desc",
                "definition": "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_enhanced_transactions_amount_desc ON enhanced_transactions (total_amount DESC)"
            },
            {
                "table": "enhanced_transactions",
                "name": "idx_enhanced_transactions_tax_reporting",
                "definition": "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_enhanced_transactions_tax_reporting ON enhanced_transactions (tax_year, tax_category, account_id) WHERE tax_year IS NOT NULL"
            },
            {
                "table": "enhanced_transactions",
                "name": "idx_enhanced_transactions_wash_sale_detection",
                "definition": "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_enhanced_transactions_wash_sale_detection ON enhanced_transactions (account_id, symbol, trade_date) WHERE type IN ('buy', 'sell') AND symbol IS NOT NULL"
            },
            {
                "table": "enhanced_transactions",
                "name": "idx_enhanced_transactions_corporate_actions",
                "definition": "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_enhanced_transactions_corporate_actions ON enhanced_transactions (symbol, corporate_action_type, trade_date) WHERE corporate_action_type IS NOT NULL"
            },
            
            # Market data performance indexes (TimescaleDB optimized)
            {
                "table": "enhanced_market_data",
                "name": "idx_enhanced_market_data_ohlc_lookup",
                "definition": "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_enhanced_market_data_ohlc_lookup ON enhanced_market_data (symbol, time DESC) INCLUDE (open, high, low, close, volume)"
            },
            {
                "table": "enhanced_market_data",
                "name": "idx_enhanced_market_data_technical_indicators",
                "definition": "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_enhanced_market_data_technical_indicators ON enhanced_market_data (symbol, time) INCLUDE (rsi_14, macd, sma_20, sma_50) WHERE rsi_14 IS NOT NULL"
            },
            {
                "table": "enhanced_market_data",
                "name": "idx_enhanced_market_data_high_volume",
                "definition": "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_enhanced_market_data_high_volume ON enhanced_market_data (volume DESC, time DESC) WHERE volume > 1000000"
            },
            
            # User activity log indexes
            {
                "table": "user_activity_log",
                "name": "idx_user_activity_log_suspicious",
                "definition": "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_activity_log_suspicious ON user_activity_log (is_suspicious, timestamp DESC) WHERE is_suspicious = true"
            },
            {
                "table": "user_activity_log",
                "name": "idx_user_activity_log_compliance_review",
                "definition": "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_activity_log_compliance_review ON user_activity_log (requires_notification, compliance_reviewed, timestamp) WHERE requires_notification = true"
            },
            
            # Regulatory report indexes
            {
                "table": "regulatory_reports",
                "name": "idx_regulatory_reports_due_date",
                "definition": "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_regulatory_reports_due_date ON regulatory_reports (due_date ASC, status) WHERE due_date IS NOT NULL AND status != 'submitted'"
            },
            {
                "table": "regulatory_reports",
                "name": "idx_regulatory_reports_user_period",
                "definition": "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_regulatory_reports_user_period ON regulatory_reports (user_id, reporting_period_start, reporting_period_end)"
            },
        ]
        
        try:
            async with db_manager.get_async_session() as session:
                for index in performance_indexes:
                    try:
                        await session.execute(text(index["definition"]))
                        result["indexes_created"].append(index["name"])
                        logger.info(f"Created performance index: {index['name']}")
                    except Exception as e:
                        error_msg = f"Failed to create index {index['name']}: {e}"
                        logger.warning(error_msg)
                        result["errors"].append(error_msg)
                
                await session.commit()
                
        except Exception as e:
            error_msg = f"Failed to create performance indexes: {e}"
            logger.error(error_msg)
            result["errors"].append(error_msg)
        
        return result
    
    async def _validate_constraints(self) -> Dict[str, Any]:
        """
        Validate all database constraints are properly defined
        """
        result = {"validated": [], "errors": []}
        
        # Define critical constraints to validate
        constraints_to_check = [
            # User constraints
            {
                "table": "enhanced_users",
                "constraint": "unique_email",
                "query": "SELECT COUNT(*) FROM enhanced_users GROUP BY LOWER(email) HAVING COUNT(*) > 1"
            },
            
            # Portfolio constraints
            {
                "table": "enhanced_portfolios", 
                "constraint": "valid_percentages",
                "query": "SELECT COUNT(*) FROM enhanced_portfolios WHERE performance_ytd < -1.0 OR performance_ytd > 10.0"
            },
            
            # Account constraints
            {
                "table": "enhanced_accounts",
                "constraint": "balance_consistency",
                "query": "SELECT COUNT(*) FROM enhanced_accounts WHERE current_balance < 0 AND account_type NOT IN ('margin', 'credit')"
            },
            
            # Transaction constraints
            {
                "table": "enhanced_transactions",
                "constraint": "trade_settlement_dates",
                "query": "SELECT COUNT(*) FROM enhanced_transactions WHERE trade_date > settlement_date AND settlement_date IS NOT NULL"
            },
            {
                "table": "enhanced_transactions",
                "constraint": "wash_sale_consistency",
                "query": "SELECT COUNT(*) FROM enhanced_transactions WHERE wash_sale = true AND wash_sale_disallowed_loss IS NULL"
            },
            
            # Market data constraints
            {
                "table": "enhanced_market_data",
                "constraint": "ohlc_validity", 
                "query": "SELECT COUNT(*) FROM enhanced_market_data WHERE high < low OR close < 0 OR open < 0"
            },
        ]
        
        try:
            async with db_manager.get_async_session() as session:
                for constraint in constraints_to_check:
                    try:
                        # Check if constraint violation exists
                        violation_result = await session.execute(text(constraint["query"]))
                        violation_count = violation_result.scalar()
                        
                        if violation_count == 0:
                            result["validated"].append(f"{constraint['table']}.{constraint['constraint']}")
                            logger.info(f"Constraint validated: {constraint['table']}.{constraint['constraint']}")
                        else:
                            error_msg = f"Constraint violation in {constraint['table']}.{constraint['constraint']}: {violation_count} violations found"
                            logger.warning(error_msg)
                            result["errors"].append(error_msg)
                            
                    except Exception as e:
                        error_msg = f"Failed to validate constraint {constraint['constraint']}: {e}"
                        logger.error(error_msg)
                        result["errors"].append(error_msg)
                        
        except Exception as e:
            error_msg = f"Constraint validation failed: {e}"
            logger.error(error_msg)
            result["errors"].append(error_msg)
        
        return result
    
    async def _apply_performance_optimizations(self) -> Dict[str, Any]:
        """
        Apply database performance optimizations
        """
        result = {"success": False, "optimizations": [], "errors": []}
        
        optimization_queries = [
            # Enable parallel query execution
            "SET max_parallel_workers_per_gather = 4;",
            "SET max_parallel_workers = 8;",
            "SET parallel_tuple_cost = 0.1;",
            "SET parallel_setup_cost = 1000.0;",
            
            # Optimize work memory for complex queries
            "SET work_mem = '256MB';",
            "SET maintenance_work_mem = '512MB';",
            
            # Enable query plan caching
            "SET plan_cache_mode = 'auto';",
            
            # Optimize checkpoint behavior
            "SET checkpoint_completion_target = 0.9;",
            "SET wal_buffers = '16MB';",
            
            # Random page cost for SSD optimization
            "SET random_page_cost = 1.1;",
            "SET seq_page_cost = 1.0;",
            
            # Enable JIT compilation for complex queries
            "SET jit = on;",
            "SET jit_above_cost = 100000;",
        ]
        
        try:
            async with db_manager.get_async_session() as session:
                for query in optimization_queries:
                    try:
                        await session.execute(text(query))
                        result["optimizations"].append(query.split('=')[0].strip().replace('SET ', ''))
                    except Exception as e:
                        logger.warning(f"Failed to apply optimization '{query}': {e}")
                        result["errors"].append(f"Optimization failed: {query}")
                
                # Update table statistics
                stats_tables = [
                    "enhanced_users", "enhanced_portfolios", "enhanced_accounts", 
                    "enhanced_transactions", "enhanced_market_data", "user_activity_log"
                ]
                
                for table in stats_tables:
                    try:
                        await session.execute(text(f"ANALYZE {table};"))
                        result["optimizations"].append(f"ANALYZE {table}")
                    except Exception as e:
                        logger.warning(f"Failed to analyze table {table}: {e}")
                
                await session.commit()
                result["success"] = True
                logger.info("Performance optimizations applied successfully")
                
        except Exception as e:
            error_msg = f"Performance optimization failed: {e}"
            logger.error(error_msg)
            result["errors"].append(error_msg)
        
        return result
    
    async def _seed_initial_data(self) -> Dict[str, Any]:
        """
        Seed initial system data
        """
        result = {"success": False, "seeded": [], "errors": []}
        
        try:
            async with db_manager.get_async_session() as session:
                # Check if data already exists
                user_count_result = await session.execute(text("SELECT COUNT(*) FROM enhanced_users"))
                user_count = user_count_result.scalar()
                
                if user_count == 0:
                    # Create system admin user
                    admin_user_data = {
                        "email": "admin@financialplanner.com",
                        "first_name": "System",
                        "last_name": "Administrator", 
                        "password_hash": "$2b$12$dummy.hash.for.initial.setup",
                        "is_active": True,
                        "is_verified": True,
                        "kyc_status": "approved",
                        "risk_tolerance": 0.5,
                        "investment_horizon": 30,
                        "tax_bracket": 0.24
                    }
                    
                    insert_query = text("""
                        INSERT INTO enhanced_users (
                            email, first_name, last_name, password_hash, 
                            is_active, is_verified, kyc_status, 
                            risk_tolerance, investment_horizon, tax_bracket,
                            created_at, updated_at
                        ) VALUES (
                            :email, :first_name, :last_name, :password_hash,
                            :is_active, :is_verified, :kyc_status,
                            :risk_tolerance, :investment_horizon, :tax_bracket,
                            :created_at, :updated_at
                        )
                    """)
                    
                    await session.execute(insert_query, {
                        **admin_user_data,
                        "created_at": datetime.now(timezone.utc),
                        "updated_at": datetime.now(timezone.utc)
                    })
                    
                    result["seeded"].append("admin_user")
                    logger.info("Created system admin user")
                
                # Seed market data source configuration
                market_sources_query = text("SELECT COUNT(*) FROM enhanced_market_data")
                market_count = await session.execute(market_sources_query)
                
                if market_count.scalar() == 0:
                    # Insert sample market data configuration
                    sample_symbols = ["SPY", "QQQ", "VTI", "BND", "GLD"]
                    for symbol in sample_symbols:
                        sample_data = {
                            "time": datetime.now(timezone.utc),
                            "symbol": symbol,
                            "close": 100.00,
                            "data_source": "initial_setup",
                            "data_quality_score": 1.0
                        }
                        
                        market_insert = text("""
                            INSERT INTO enhanced_market_data (time, symbol, close, data_source, data_quality_score, created_at)
                            VALUES (:time, :symbol, :close, :data_source, :data_quality_score, :created_at)
                        """)
                        
                        await session.execute(market_insert, {
                            **sample_data,
                            "created_at": datetime.now(timezone.utc)
                        })
                    
                    result["seeded"].append("sample_market_data")
                    logger.info("Seeded sample market data")
                
                await session.commit()
                result["success"] = True
                logger.info("Initial data seeding completed")
                
        except Exception as e:
            error_msg = f"Initial data seeding failed: {e}"
            logger.error(error_msg)
            result["errors"].append(error_msg)
        
        return result
    
    async def get_database_health(self) -> Dict[str, Any]:
        """
        Get comprehensive database health information
        """
        health_info = {
            "status": "unknown",
            "connection_status": False,
            "table_counts": {},
            "index_usage": {},
            "performance_stats": {},
            "errors": []
        }
        
        try:
            async with db_manager.get_async_session() as session:
                # Test connection
                await session.execute(text("SELECT 1"))
                health_info["connection_status"] = True
                
                # Get table row counts
                tables_to_check = [
                    "enhanced_users", "enhanced_portfolios", "enhanced_accounts",
                    "enhanced_transactions", "enhanced_market_data", "user_activity_log"
                ]
                
                for table in tables_to_check:
                    try:
                        count_result = await session.execute(text(f"SELECT COUNT(*) FROM {table}"))
                        health_info["table_counts"][table] = count_result.scalar()
                    except Exception as e:
                        health_info["errors"].append(f"Failed to count {table}: {e}")
                
                # Get index usage stats (PostgreSQL specific)
                if settings.DATABASE_URL.startswith("postgresql"):
                    index_stats_query = """
                        SELECT 
                            indexrelname as index_name,
                            idx_tup_read,
                            idx_tup_fetch
                        FROM pg_stat_user_indexes 
                        WHERE schemaname = 'public'
                        ORDER BY idx_tup_read DESC
                        LIMIT 10;
                    """
                    
                    try:
                        index_result = await session.execute(text(index_stats_query))
                        health_info["index_usage"] = [dict(row._mapping) for row in index_result]
                    except Exception as e:
                        health_info["errors"].append(f"Failed to get index stats: {e}")
                
                health_info["status"] = "healthy" if not health_info["errors"] else "degraded"
                
        except Exception as e:
            health_info["status"] = "unhealthy"
            health_info["errors"].append(f"Database health check failed: {e}")
        
        return health_info


# Global initializer instance
database_initializer = DatabaseInitializer()


async def main():
    """
    Main function to run database initialization
    """
    print("Starting Financial Planning System Database Initialization")
    print("=" * 60)
    
    # Initialize database managers
    await db_manager.initialize()
    await timescale_manager.initialize()
    
    # Run complete initialization
    results = await database_initializer.initialize_complete_database()
    
    # Print results
    print("\nInitialization Results:")
    print("-" * 30)
    
    for key, value in results.items():
        if key == "errors" and value:
            print(f"❌ {key}: {len(value)} errors")
            for error in value[:3]:  # Show first 3 errors
                print(f"   • {error}")
            if len(value) > 3:
                print(f"   ... and {len(value) - 3} more errors")
        elif key == "errors":
            print(f"✅ {key}: No errors")
        elif isinstance(value, bool):
            status = "✅" if value else "❌"
            print(f"{status} {key}: {value}")
        elif isinstance(value, list):
            print(f"📊 {key}: {len(value)} items")
        else:
            print(f"📋 {key}: {value}")
    
    # Get health check
    print("\nDatabase Health Check:")
    print("-" * 30)
    
    health = await database_initializer.get_database_health()
    print(f"Status: {health['status'].upper()}")
    print(f"Connection: {'✅' if health['connection_status'] else '❌'}")
    
    if health['table_counts']:
        print("\nTable Row Counts:")
        for table, count in health['table_counts'].items():
            print(f"  {table}: {count:,} rows")
    
    # Cleanup
    await db_manager.shutdown()
    await timescale_manager.shutdown()
    
    print("\nDatabase initialization completed!")


if __name__ == "__main__":
    asyncio.run(main())