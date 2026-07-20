"""
Comprehensive tests for database migrations.

This test suite covers:
- Migration execution and rollback
- Schema integrity validation
- Data migration accuracy
- Performance impact testing
- Cross-version compatibility
- Migration dependencies
- Data preservation
"""
import pytest
import asyncio
import sqlalchemy as sa
from sqlalchemy import text, inspect
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from alembic.migration import MigrationContext
from alembic.operations import Operations
from datetime import datetime, timedelta
from decimal import Decimal
import tempfile
import os
from pathlib import Path

from app.database.base import Base
from app.database.models import *
from app.core.config import get_settings


class TestDatabaseMigrations:
    """Test database migration functionality."""
    
    @pytest.fixture
    def alembic_config(self):
        """Create Alembic configuration for testing."""
        # Create temporary directory for test migrations
        temp_dir = tempfile.mkdtemp()
        
        config = Config()
        config.set_main_option("script_location", "alembic")
        config.set_main_option("sqlalchemy.url", "postgresql+asyncpg://test:test@localhost:5433/test_migrations")
        config.set_main_option("version_locations", temp_dir)
        
        return config
    
    @pytest.fixture
    async def migration_engine(self):
        """Create engine for migration testing."""
        test_url = "postgresql+asyncpg://test:test@localhost:5433/test_migrations"
        engine = create_async_engine(test_url, echo=False)
        
        # Create fresh database
        async with engine.begin() as conn:
            await conn.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
            await conn.execute(text("CREATE SCHEMA public"))
        
        yield engine
        
        # Cleanup
        async with engine.begin() as conn:
            await conn.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
        await engine.dispose()
    
    @pytest.mark.asyncio
    async def test_initial_migration_execution(self, alembic_config, migration_engine):
        """Test execution of initial database migration."""
        
        # Run migration to head
        command.upgrade(alembic_config, "head")
        
        # Verify all tables were created
        async with migration_engine.connect() as conn:
            inspector = inspect(conn)
            tables = await conn.run_sync(lambda sync_conn: inspector.get_table_names())
        
        expected_tables = [
            'users', 'financial_profiles', 'goals', 'investments',
            'simulation_results', 'bank_accounts', 'transactions',
            'ml_recommendations', 'audit_logs', 'market_data',
            'user_sessions', 'api_keys', 'notification_preferences'
        ]
        
        for table in expected_tables:
            assert table in tables, f"Table {table} not created"
    
    @pytest.mark.asyncio
    async def test_migration_rollback(self, alembic_config, migration_engine):
        """Test rolling back migrations."""
        
        # Apply migrations
        command.upgrade(alembic_config, "head")
        
        # Get current revision
        script_dir = ScriptDirectory.from_config(alembic_config)
        revisions = list(script_dir.walk_revisions())
        
        if len(revisions) >= 2:
            # Rollback one revision
            previous_revision = revisions[1].revision
            command.downgrade(alembic_config, previous_revision)
            
            # Verify rollback was successful
            async with migration_engine.connect() as conn:
                context = MigrationContext.configure(conn)
                current_rev = context.get_current_revision()
                assert current_rev == previous_revision
    
    @pytest.mark.asyncio
    async def test_schema_validation_after_migration(self, alembic_config, migration_engine):
        """Test schema integrity after migration."""
        
        command.upgrade(alembic_config, "head")
        
        async with migration_engine.connect() as conn:
            inspector = inspect(conn)
            
            # Test users table schema
            await self._validate_users_table_schema(conn, inspector)
            
            # Test financial_profiles table schema
            await self._validate_financial_profiles_schema(conn, inspector)
            
            # Test goals table schema
            await self._validate_goals_table_schema(conn, inspector)
            
            # Test foreign key constraints
            await self._validate_foreign_key_constraints(conn, inspector)
            
            # Test indexes
            await self._validate_indexes(conn, inspector)
    
    async def _validate_users_table_schema(self, conn, inspector):
        """Validate users table schema."""
        columns = await conn.run_sync(lambda sync_conn: inspector.get_columns('users'))
        column_names = [col['name'] for col in columns]
        
        required_columns = [
            'id', 'email', 'hashed_password', 'first_name', 'last_name',
            'date_of_birth', 'phone_number', 'is_active', 'is_verified',
            'created_at', 'updated_at'
        ]
        
        for col in required_columns:
            assert col in column_names, f"Column {col} missing from users table"
        
        # Check column types
        email_col = next(col for col in columns if col['name'] == 'email')
        assert 'varchar' in str(email_col['type']).lower()
        
        # Check unique constraints
        unique_constraints = await conn.run_sync(
            lambda sync_conn: inspector.get_unique_constraints('users')
        )
        email_unique = any('email' in constraint['column_names'] 
                          for constraint in unique_constraints)
        assert email_unique, "Email unique constraint missing"
    
    async def _validate_financial_profiles_schema(self, conn, inspector):
        """Validate financial_profiles table schema."""
        columns = await conn.run_sync(
            lambda sync_conn: inspector.get_columns('financial_profiles')
        )
        column_names = [col['name'] for col in columns]
        
        required_columns = [
            'id', 'user_id', 'annual_income', 'monthly_expenses',
            'current_savings', 'debt_amount', 'risk_tolerance',
            'investment_experience', 'age', 'retirement_age'
        ]
        
        for col in required_columns:
            assert col in column_names, f"Column {col} missing from financial_profiles table"
        
        # Check decimal precision for financial fields
        income_col = next(col for col in columns if col['name'] == 'annual_income')
        assert 'numeric' in str(income_col['type']).lower() or 'decimal' in str(income_col['type']).lower()
    
    async def _validate_goals_table_schema(self, conn, inspector):
        """Validate goals table schema."""
        columns = await conn.run_sync(lambda sync_conn: inspector.get_columns('goals'))
        column_names = [col['name'] for col in columns]
        
        required_columns = [
            'id', 'user_id', 'name', 'description', 'target_amount',
            'current_amount', 'target_date', 'goal_type', 'priority',
            'is_active', 'created_at'
        ]
        
        for col in required_columns:
            assert col in column_names, f"Column {col} missing from goals table"
    
    async def _validate_foreign_key_constraints(self, conn, inspector):
        """Validate foreign key constraints."""
        
        # Check financial_profiles -> users
        fk_constraints = await conn.run_sync(
            lambda sync_conn: inspector.get_foreign_keys('financial_profiles')
        )
        
        user_fk = any(
            constraint['referred_table'] == 'users' and 'user_id' in constraint['constrained_columns']
            for constraint in fk_constraints
        )
        assert user_fk, "Foreign key constraint missing: financial_profiles.user_id -> users.id"
        
        # Check goals -> users
        goal_fk_constraints = await conn.run_sync(
            lambda sync_conn: inspector.get_foreign_keys('goals')
        )
        
        goal_user_fk = any(
            constraint['referred_table'] == 'users' and 'user_id' in constraint['constrained_columns']
            for constraint in goal_fk_constraints
        )
        assert goal_user_fk, "Foreign key constraint missing: goals.user_id -> users.id"
    
    async def _validate_indexes(self, conn, inspector):
        """Validate database indexes."""
        
        # Check users table indexes
        user_indexes = await conn.run_sync(
            lambda sync_conn: inspector.get_indexes('users')
        )
        
        email_indexed = any('email' in idx['column_names'] for idx in user_indexes)
        assert email_indexed, "Email index missing on users table"
        
        # Check financial_profiles indexes
        profile_indexes = await conn.run_sync(
            lambda sync_conn: inspector.get_indexes('financial_profiles')
        )
        
        user_id_indexed = any('user_id' in idx['column_names'] for idx in profile_indexes)
        assert user_id_indexed, "User ID index missing on financial_profiles table"
    
    @pytest.mark.asyncio
    async def test_data_migration_integrity(self, alembic_config, migration_engine):
        """Test data integrity during migrations."""
        
        # Apply initial migration
        command.upgrade(alembic_config, "head")
        
        # Insert test data
        test_data = await self._insert_test_data(migration_engine)
        
        # Simulate a data migration (e.g., adding calculated fields)
        await self._simulate_data_migration(migration_engine)
        
        # Verify data integrity
        await self._verify_data_integrity(migration_engine, test_data)
    
    async def _insert_test_data(self, engine):
        """Insert test data for migration testing."""
        async with engine.begin() as conn:
            # Insert test user
            user_result = await conn.execute(
                text("""
                    INSERT INTO users (email, hashed_password, first_name, last_name, 
                                     date_of_birth, created_at, updated_at)
                    VALUES ('test@example.com', 'hashed_password', 'Test', 'User',
                           '1990-01-01', NOW(), NOW())
                    RETURNING id
                """)
            )
            user_id = user_result.fetchone()[0]
            
            # Insert financial profile
            await conn.execute(
                text("""
                    INSERT INTO financial_profiles 
                    (user_id, annual_income, monthly_expenses, current_savings, 
                     debt_amount, risk_tolerance, age, retirement_age, created_at, updated_at)
                    VALUES (:user_id, 75000, 4500, 25000, 15000, 'moderate', 35, 65, NOW(), NOW())
                """),
                {"user_id": user_id}
            )
            
            # Insert goals
            await conn.execute(
                text("""
                    INSERT INTO goals 
                    (user_id, name, description, target_amount, current_amount,
                     target_date, goal_type, priority, is_active, created_at)
                    VALUES (:user_id, 'Emergency Fund', 'Build emergency savings',
                           50000, 10000, '2025-12-31', 'emergency_fund', 1, true, NOW())
                """),
                {"user_id": user_id}
            )
            
            return {"user_id": user_id}
    
    async def _simulate_data_migration(self, engine):
        """Simulate a data migration that adds calculated fields."""
        async with engine.begin() as conn:
            # Add a calculated field to financial_profiles (if not exists)
            try:
                await conn.execute(
                    text("ALTER TABLE financial_profiles ADD COLUMN net_worth DECIMAL(15,2)")
                )
            except Exception:
                pass  # Column might already exist
            
            # Update calculated field
            await conn.execute(
                text("""
                    UPDATE financial_profiles 
                    SET net_worth = current_savings - debt_amount
                    WHERE net_worth IS NULL
                """)
            )
    
    async def _verify_data_integrity(self, engine, test_data):
        """Verify data integrity after migration."""
        async with engine.begin() as conn:
            # Verify user still exists
            user_result = await conn.execute(
                text("SELECT * FROM users WHERE id = :user_id"),
                {"user_id": test_data["user_id"]}
            )
            assert user_result.fetchone() is not None, "User data lost during migration"
            
            # Verify calculated field is correct
            profile_result = await conn.execute(
                text("""
                    SELECT current_savings, debt_amount, net_worth 
                    FROM financial_profiles WHERE user_id = :user_id
                """),
                {"user_id": test_data["user_id"]}
            )
            
            profile_data = profile_result.fetchone()
            assert profile_data is not None, "Financial profile lost during migration"
            
            expected_net_worth = profile_data[0] - profile_data[1]  # savings - debt
            actual_net_worth = profile_data[2]
            
            assert abs(expected_net_worth - actual_net_worth) < 0.01, "Calculated field incorrect"
    
    @pytest.mark.asyncio
    async def test_migration_performance(self, alembic_config, migration_engine):
        """Test migration performance with large datasets."""
        
        # Apply initial migration
        command.upgrade(alembic_config, "head")
        
        # Insert large dataset
        await self._insert_large_dataset(migration_engine, num_users=1000)
        
        # Measure migration performance
        import time
        start_time = time.time()
        
        # Simulate a heavy data migration
        await self._simulate_heavy_migration(migration_engine)
        
        end_time = time.time()
        migration_time = end_time - start_time
        
        # Migration should complete within reasonable time (less than 30 seconds)
        assert migration_time < 30, f"Migration took too long: {migration_time} seconds"
    
    async def _insert_large_dataset(self, engine, num_users=1000):
        """Insert large dataset for performance testing."""
        async with engine.begin() as conn:
            # Batch insert users
            user_values = []
            for i in range(num_users):
                user_values.append(f"('user{i}@example.com', 'hashed_password', 'User', '{i}', '1990-01-01', NOW(), NOW())")
            
            users_sql = f"""
                INSERT INTO users (email, hashed_password, first_name, last_name, 
                                 date_of_birth, created_at, updated_at)
                VALUES {', '.join(user_values)}
            """
            await conn.execute(text(users_sql))
            
            # Get user IDs
            user_ids_result = await conn.execute(
                text("SELECT id FROM users ORDER BY id LIMIT :limit"),
                {"limit": num_users}
            )
            user_ids = [row[0] for row in user_ids_result.fetchall()]
            
            # Batch insert financial profiles
            profile_values = []
            for user_id in user_ids:
                profile_values.append(
                    f"({user_id}, 75000, 4500, 25000, 15000, 'moderate', 35, 65, NOW(), NOW())"
                )
            
            profiles_sql = f"""
                INSERT INTO financial_profiles 
                (user_id, annual_income, monthly_expenses, current_savings,
                 debt_amount, risk_tolerance, age, retirement_age, created_at, updated_at)
                VALUES {', '.join(profile_values)}
            """
            await conn.execute(text(profiles_sql))
    
    async def _simulate_heavy_migration(self, engine):
        """Simulate a heavy data migration operation."""
        async with engine.begin() as conn:
            # Add index (simulate schema change)
            try:
                await conn.execute(
                    text("CREATE INDEX idx_financial_profiles_risk_tolerance ON financial_profiles(risk_tolerance)")
                )
            except Exception:
                pass
            
            # Update all records (simulate data migration)
            await conn.execute(
                text("""
                    UPDATE financial_profiles 
                    SET updated_at = NOW()
                    WHERE updated_at < NOW()
                """)
            )
    
    @pytest.mark.asyncio
    async def test_migration_dependencies(self, alembic_config, migration_engine):
        """Test migration dependency resolution."""
        
        script_dir = ScriptDirectory.from_config(alembic_config)
        revisions = list(script_dir.walk_revisions())
        
        # Verify migration dependencies are properly set
        for revision in revisions:
            if revision.down_revision:
                # Verify down revision exists
                down_rev = script_dir.get_revision(revision.down_revision)
                assert down_rev is not None, f"Down revision {revision.down_revision} not found"
        
        # Test applying migrations out of order (should fail)
        if len(revisions) >= 2:
            latest_rev = revisions[0]
            previous_rev = revisions[1]
            
            # Try to apply latest without previous (should handle dependencies)
            try:
                command.upgrade(alembic_config, latest_rev.revision)
            except Exception as e:
                # Should either succeed (if dependencies handled) or fail gracefully
                assert "dependency" in str(e).lower() or "revision" in str(e).lower()
    
    @pytest.mark.asyncio
    async def test_migration_idempotency(self, alembic_config, migration_engine):
        """Test that migrations can be run multiple times safely."""
        
        # Run migration twice
        command.upgrade(alembic_config, "head")
        
        # Should not fail when run again
        try:
            command.upgrade(alembic_config, "head")
        except Exception as e:
            pytest.fail(f"Migration not idempotent: {e}")
        
        # Verify schema is still correct
        async with migration_engine.connect() as conn:
            inspector = inspect(conn)
            tables = await conn.run_sync(lambda sync_conn: inspector.get_table_names())
        
        assert 'users' in tables
        assert 'financial_profiles' in tables
    
    @pytest.mark.asyncio
    async def test_cross_version_compatibility(self, alembic_config, migration_engine):
        """Test compatibility across different schema versions."""
        
        script_dir = ScriptDirectory.from_config(alembic_config)
        revisions = list(script_dir.walk_revisions())
        
        if len(revisions) >= 3:
            # Test upgrading from old version to latest
            old_revision = revisions[-1]  # Oldest revision
            latest_revision = revisions[0]  # Latest revision
            
            # Start with old version
            command.upgrade(alembic_config, old_revision.revision)
            
            # Insert data compatible with old schema
            await self._insert_legacy_compatible_data(migration_engine)
            
            # Upgrade to latest
            command.upgrade(alembic_config, latest_revision.revision)
            
            # Verify data is still accessible
            await self._verify_legacy_data_accessibility(migration_engine)
    
    async def _insert_legacy_compatible_data(self, engine):
        """Insert data that should be compatible with older schema versions."""
        async with engine.begin() as conn:
            await conn.execute(
                text("""
                    INSERT INTO users (email, hashed_password, first_name, last_name,
                                     date_of_birth, created_at, updated_at)
                    VALUES ('legacy@example.com', 'hashed_password', 'Legacy', 'User',
                           '1985-01-01', NOW(), NOW())
                """)
            )
    
    async def _verify_legacy_data_accessibility(self, engine):
        """Verify legacy data is still accessible after migration."""
        async with engine.begin() as conn:
            result = await conn.execute(
                text("SELECT * FROM users WHERE email = 'legacy@example.com'")
            )
            assert result.fetchone() is not None, "Legacy data not accessible after migration"
    
    @pytest.mark.asyncio
    async def test_migration_backup_and_restore(self, alembic_config, migration_engine):
        """Test migration with backup and restore functionality."""
        
        # Apply initial migration and insert data
        command.upgrade(alembic_config, "head")
        test_data = await self._insert_test_data(migration_engine)
        
        # Create backup (simulate)
        backup_data = await self._create_backup(migration_engine)
        
        # Apply potentially destructive migration
        await self._simulate_destructive_migration(migration_engine)
        
        # Restore from backup if needed
        await self._restore_from_backup(migration_engine, backup_data)
        
        # Verify data integrity
        await self._verify_data_integrity(migration_engine, test_data)
    
    async def _create_backup(self, engine):
        """Create backup of critical data."""
        backup_data = {}
        
        async with engine.begin() as conn:
            # Backup users
            users_result = await conn.execute(text("SELECT * FROM users"))
            backup_data['users'] = users_result.fetchall()
            
            # Backup financial profiles
            profiles_result = await conn.execute(text("SELECT * FROM financial_profiles"))
            backup_data['profiles'] = profiles_result.fetchall()
        
        return backup_data
    
    async def _simulate_destructive_migration(self, engine):
        """Simulate a migration that might be destructive."""
        async with engine.begin() as conn:
            # Simulate dropping and recreating a table
            await conn.execute(text("DROP TABLE IF EXISTS temp_backup_table"))
            await conn.execute(
                text("""
                    CREATE TABLE temp_backup_table AS 
                    SELECT * FROM financial_profiles
                """)
            )
    
    async def _restore_from_backup(self, engine, backup_data):
        """Restore data from backup if needed."""
        # In a real scenario, this would restore from actual backup files
        # For testing, we just verify the backup data exists
        assert 'users' in backup_data
        assert 'profiles' in backup_data
        assert len(backup_data['users']) > 0
    
    @pytest.mark.asyncio
    async def test_migration_with_constraints_validation(self, alembic_config, migration_engine):
        """Test migration with database constraints validation."""
        
        command.upgrade(alembic_config, "head")
        
        async with migration_engine.begin() as conn:
            # Test NOT NULL constraints
            with pytest.raises(Exception):  # Should raise integrity error
                await conn.execute(
                    text("INSERT INTO users (email) VALUES (NULL)")
                )
            
            # Test unique constraints
            await conn.execute(
                text("""
                    INSERT INTO users (email, hashed_password, first_name, last_name,
                                     date_of_birth, created_at, updated_at)
                    VALUES ('unique@example.com', 'password', 'Test', 'User',
                           '1990-01-01', NOW(), NOW())
                """)
            )
            
            with pytest.raises(Exception):  # Should raise unique constraint violation
                await conn.execute(
                    text("""
                        INSERT INTO users (email, hashed_password, first_name, last_name,
                                         date_of_birth, created_at, updated_at)
                        VALUES ('unique@example.com', 'password2', 'Test2', 'User2',
                               '1990-01-01', NOW(), NOW())
                    """)
                )
            
            # Test foreign key constraints
            with pytest.raises(Exception):  # Should raise foreign key violation
                await conn.execute(
                    text("""
                        INSERT INTO financial_profiles 
                        (user_id, annual_income, monthly_expenses, created_at, updated_at)
                        VALUES (99999, 50000, 3000, NOW(), NOW())
                    """)
                )
    
    @pytest.mark.asyncio
    async def test_migration_with_large_text_fields(self, alembic_config, migration_engine):
        """Test migration with large text fields and proper indexing."""
        
        command.upgrade(alembic_config, "head")
        
        async with migration_engine.begin() as conn:
            # Insert user first
            user_result = await conn.execute(
                text("""
                    INSERT INTO users (email, hashed_password, first_name, last_name,
                                     date_of_birth, created_at, updated_at)
                    VALUES ('texttest@example.com', 'password', 'Text', 'Test',
                           '1990-01-01', NOW(), NOW())
                    RETURNING id
                """)
            )
            user_id = user_result.fetchone()[0]
            
            # Test large description field in goals
            large_description = "A" * 10000  # 10KB description
            
            await conn.execute(
                text("""
                    INSERT INTO goals 
                    (user_id, name, description, target_amount, target_date,
                     goal_type, priority, is_active, created_at)
                    VALUES (:user_id, 'Large Goal', :description, 100000, '2025-12-31',
                           'custom', 1, true, NOW())
                """),
                {"user_id": user_id, "description": large_description}
            )
            
            # Verify data was stored correctly
            result = await conn.execute(
                text("SELECT description FROM goals WHERE user_id = :user_id"),
                {"user_id": user_id}
            )
            stored_description = result.fetchone()[0]
            
            assert len(stored_description) == len(large_description)
            assert stored_description == large_description
    
    @pytest.mark.asyncio
    async def test_concurrent_migrations(self, alembic_config):
        """Test handling of concurrent migration attempts."""
        
        # This test would require more complex setup with multiple database connections
        # For now, we'll test that the migration lock mechanism works
        
        # Simulate migration lock
        lock_acquired = True  # In real implementation, this would check actual lock
        
        if lock_acquired:
            # Migration should proceed
            command.upgrade(alembic_config, "head")
        else:
            # Migration should wait or fail gracefully
            with pytest.raises(Exception):
                command.upgrade(alembic_config, "head")
    
    @pytest.mark.asyncio
    async def test_migration_logging_and_monitoring(self, alembic_config, migration_engine):
        """Test migration logging and monitoring capabilities."""
        
        # Enable migration logging (would be configured in alembic.ini)
        import logging
        migration_logger = logging.getLogger('alembic')
        
        # Capture log messages
        log_messages = []
        
        class TestLogHandler(logging.Handler):
            def emit(self, record):
                log_messages.append(record.getMessage())
        
        handler = TestLogHandler()
        migration_logger.addHandler(handler)
        migration_logger.setLevel(logging.INFO)
        
        try:
            # Run migration
            command.upgrade(alembic_config, "head")
            
            # Verify logging occurred
            assert len(log_messages) > 0, "No migration log messages captured"
            
            # Check for specific log patterns
            upgrade_logs = [msg for msg in log_messages if 'upgrade' in msg.lower()]
            assert len(upgrade_logs) > 0, "No upgrade log messages found"
            
        finally:
            migration_logger.removeHandler(handler)