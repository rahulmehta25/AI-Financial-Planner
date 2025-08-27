#!/usr/bin/env python3
"""
Comprehensive Database Operations Verification Script

This script performs comprehensive database verification including:
1. SQLite database accessibility and health
2. Basic CRUD operations testing
3. Data persistence verification
4. Schema validation and table inspection
5. Concurrent access simulation
6. Performance benchmarking
7. Backup and recovery validation

Usage:
    python3 database_verification.py
"""

import os
import sys
import json
import sqlite3
import time
import threading
import asyncio
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import tempfile
import shutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('database_verification.log')
    ]
)
logger = logging.getLogger(__name__)

class DatabaseVerification:
    """Comprehensive database verification and testing"""
    
    def __init__(self, db_path: str = "demo_data/financial_data.db"):
        self.db_path = Path(db_path)
        self.backup_path = Path("demo_data/backup_test.db")
        self.test_results = {}
        self.connection_pool = []
        
    def verify_database_accessibility(self) -> Dict[str, Any]:
        """Verify that the SQLite database exists and is accessible"""
        logger.info("=== Database Accessibility Test ===")
        
        try:
            # Check if database file exists
            if not self.db_path.exists():
                return {
                    "status": "failed",
                    "error": f"Database file not found at {self.db_path}",
                    "accessible": False
                }
            
            # Check file permissions
            if not os.access(self.db_path, os.R_OK | os.W_OK):
                return {
                    "status": "failed",
                    "error": "Database file is not readable/writable",
                    "accessible": False
                }
            
            # Test basic connection
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT sqlite_version()")
                version = cursor.fetchone()[0]
                
                # Get database file size
                file_size = self.db_path.stat().st_size
                
                logger.info(f"✅ Database accessible at {self.db_path}")
                logger.info(f"✅ SQLite version: {version}")
                logger.info(f"✅ File size: {file_size} bytes")
                
                return {
                    "status": "success",
                    "accessible": True,
                    "sqlite_version": version,
                    "file_size_bytes": file_size,
                    "file_path": str(self.db_path.absolute())
                }
                
        except Exception as e:
            logger.error(f"❌ Database accessibility test failed: {str(e)}")
            return {
                "status": "failed",
                "error": str(e),
                "accessible": False
            }
    
    def verify_schema_and_tables(self) -> Dict[str, Any]:
        """Check database schema and validate table structures"""
        logger.info("=== Schema and Tables Verification ===")
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get all tables
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                
                logger.info(f"✅ Found {len(tables)} tables: {tables}")
                
                # Get schema for each table
                table_schemas = {}
                table_row_counts = {}
                
                for table in tables:
                    # Get schema
                    cursor.execute(f"SELECT sql FROM sqlite_master WHERE name='{table}'")
                    schema = cursor.fetchone()
                    table_schemas[table] = schema[0] if schema else "No schema found"
                    
                    # Get row count
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    row_count = cursor.fetchone()[0]
                    table_row_counts[table] = row_count
                    
                    logger.info(f"✅ Table '{table}': {row_count} rows")
                
                # Verify data integrity with sample queries
                integrity_checks = {}
                for table in tables:
                    try:
                        cursor.execute(f"SELECT * FROM {table} LIMIT 1")
                        sample_row = cursor.fetchone()
                        integrity_checks[table] = {
                            "has_data": sample_row is not None,
                            "sample_row_columns": len(sample_row) if sample_row else 0
                        }
                    except Exception as e:
                        integrity_checks[table] = {
                            "has_data": False,
                            "error": str(e)
                        }
                
                return {
                    "status": "success",
                    "tables": tables,
                    "table_count": len(tables),
                    "table_schemas": table_schemas,
                    "table_row_counts": table_row_counts,
                    "integrity_checks": integrity_checks
                }
                
        except Exception as e:
            logger.error(f"❌ Schema verification failed: {str(e)}")
            return {
                "status": "failed",
                "error": str(e)
            }
    
    def test_crud_operations(self) -> Dict[str, Any]:
        """Test Create, Read, Update, Delete operations"""
        logger.info("=== CRUD Operations Test ===")
        
        test_table = "crud_test"
        crud_results = {
            "create": False,
            "read": False,
            "update": False,
            "delete": False,
            "errors": []
        }
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # CREATE: Create test table and insert data
                try:
                    cursor.execute(f"""
                        CREATE TABLE IF NOT EXISTS {test_table} (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            name TEXT NOT NULL,
                            value REAL,
                            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
                    
                    # Insert test data
                    test_data = [
                        ("Test Record 1", 100.50),
                        ("Test Record 2", 200.75),
                        ("Test Record 3", 300.25)
                    ]
                    
                    cursor.executemany(
                        f"INSERT INTO {test_table} (name, value) VALUES (?, ?)",
                        test_data
                    )
                    conn.commit()
                    
                    crud_results["create"] = True
                    logger.info("✅ CREATE operations successful")
                    
                except Exception as e:
                    crud_results["errors"].append(f"CREATE failed: {str(e)}")
                    logger.error(f"❌ CREATE failed: {str(e)}")
                
                # READ: Query test data
                try:
                    cursor.execute(f"SELECT * FROM {test_table}")
                    rows = cursor.fetchall()
                    
                    if len(rows) >= 3:
                        crud_results["read"] = True
                        logger.info(f"✅ READ operations successful - retrieved {len(rows)} rows")
                    else:
                        crud_results["errors"].append(f"READ: Expected 3+ rows, got {len(rows)}")
                        
                except Exception as e:
                    crud_results["errors"].append(f"READ failed: {str(e)}")
                    logger.error(f"❌ READ failed: {str(e)}")
                
                # UPDATE: Modify test data
                try:
                    cursor.execute(f"""
                        UPDATE {test_table} 
                        SET value = value * 1.1 
                        WHERE name LIKE 'Test Record%'
                    """)
                    
                    updated_rows = cursor.rowcount
                    if updated_rows > 0:
                        crud_results["update"] = True
                        logger.info(f"✅ UPDATE operations successful - updated {updated_rows} rows")
                    else:
                        crud_results["errors"].append("UPDATE: No rows were updated")
                        
                except Exception as e:
                    crud_results["errors"].append(f"UPDATE failed: {str(e)}")
                    logger.error(f"❌ UPDATE failed: {str(e)}")
                
                # DELETE: Remove test data
                try:
                    cursor.execute(f"DELETE FROM {test_table} WHERE name LIKE 'Test Record%'")
                    deleted_rows = cursor.rowcount
                    
                    if deleted_rows > 0:
                        crud_results["delete"] = True
                        logger.info(f"✅ DELETE operations successful - deleted {deleted_rows} rows")
                    else:
                        crud_results["errors"].append("DELETE: No rows were deleted")
                    
                    # Clean up test table
                    cursor.execute(f"DROP TABLE IF EXISTS {test_table}")
                    conn.commit()
                    
                except Exception as e:
                    crud_results["errors"].append(f"DELETE failed: {str(e)}")
                    logger.error(f"❌ DELETE failed: {str(e)}")
                
                # Calculate success rate
                operations = ["create", "read", "update", "delete"]
                successful_ops = sum(1 for op in operations if crud_results[op])
                crud_results["success_rate"] = successful_ops / len(operations)
                crud_results["status"] = "success" if successful_ops == len(operations) else "partial_success"
                
                return crud_results
                
        except Exception as e:
            logger.error(f"❌ CRUD operations test failed: {str(e)}")
            return {
                "status": "failed",
                "error": str(e),
                **crud_results
            }
    
    def test_data_persistence(self) -> Dict[str, Any]:
        """Test data persistence across connection sessions"""
        logger.info("=== Data Persistence Test ===")
        
        test_table = "persistence_test"
        test_data_id = None
        
        try:
            # Session 1: Create and insert data
            with sqlite3.connect(self.db_path) as conn1:
                cursor1 = conn1.cursor()
                
                cursor1.execute(f"""
                    CREATE TABLE IF NOT EXISTS {test_table} (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        test_value TEXT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                test_value = f"persistence_test_{datetime.now().isoformat()}"
                cursor1.execute(
                    f"INSERT INTO {test_table} (test_value) VALUES (?)",
                    (test_value,)
                )
                test_data_id = cursor1.lastrowid
                conn1.commit()
                
                logger.info(f"✅ Session 1: Inserted test data with ID {test_data_id}")
            
            # Small delay to simulate real-world scenario
            time.sleep(0.1)
            
            # Session 2: Verify data exists
            with sqlite3.connect(self.db_path) as conn2:
                cursor2 = conn2.cursor()
                
                cursor2.execute(
                    f"SELECT test_value FROM {test_table} WHERE id = ?",
                    (test_data_id,)
                )
                result = cursor2.fetchone()
                
                if result and result[0] == test_value:
                    logger.info("✅ Session 2: Data persistence verified")
                    
                    # Clean up
                    cursor2.execute(f"DROP TABLE IF EXISTS {test_table}")
                    conn2.commit()
                    
                    return {
                        "status": "success",
                        "persistent": True,
                        "test_value": test_value,
                        "test_id": test_data_id
                    }
                else:
                    return {
                        "status": "failed",
                        "persistent": False,
                        "error": "Data not found in second session"
                    }
                    
        except Exception as e:
            logger.error(f"❌ Data persistence test failed: {str(e)}")
            return {
                "status": "failed",
                "persistent": False,
                "error": str(e)
            }
    
    def test_concurrent_access(self) -> Dict[str, Any]:
        """Test concurrent database access capabilities"""
        logger.info("=== Concurrent Access Test ===")
        
        def worker_task(worker_id: int, num_operations: int) -> Dict[str, Any]:
            """Worker function for concurrent access testing"""
            worker_results = {
                "worker_id": worker_id,
                "operations_attempted": num_operations,
                "operations_successful": 0,
                "errors": [],
                "duration": 0
            }
            
            start_time = time.time()
            
            try:
                with sqlite3.connect(self.db_path, timeout=10.0) as conn:
                    cursor = conn.cursor()
                    
                    for i in range(num_operations):
                        try:
                            # Perform a mix of read and write operations
                            if i % 2 == 0:
                                # Read operation
                                cursor.execute("SELECT COUNT(*) FROM customer_portfolios")
                                result = cursor.fetchone()
                                if result:
                                    worker_results["operations_successful"] += 1
                            else:
                                # Write operation (insert and delete to avoid data pollution)
                                test_value = f"worker_{worker_id}_op_{i}"
                                cursor.execute("""
                                    INSERT INTO customer_portfolios 
                                    (customer_id, asset_type, allocation_percent, value, risk_score, created_at)
                                    VALUES (?, 'TEST', 0.0, 0.0, 0.0, datetime('now'))
                                """, (test_value,))
                                
                                # Immediately delete to avoid data pollution
                                cursor.execute(
                                    "DELETE FROM customer_portfolios WHERE customer_id = ?",
                                    (test_value,)
                                )
                                conn.commit()
                                worker_results["operations_successful"] += 1
                                
                        except Exception as e:
                            worker_results["errors"].append(f"Operation {i}: {str(e)}")
                            
            except Exception as e:
                worker_results["errors"].append(f"Connection error: {str(e)}")
            
            worker_results["duration"] = time.time() - start_time
            return worker_results
        
        try:
            # Test with multiple concurrent workers
            num_workers = 5
            operations_per_worker = 10
            
            start_time = time.time()
            
            with ThreadPoolExecutor(max_workers=num_workers) as executor:
                futures = [
                    executor.submit(worker_task, worker_id, operations_per_worker)
                    for worker_id in range(num_workers)
                ]
                
                worker_results = []
                for future in as_completed(futures):
                    try:
                        result = future.result(timeout=30)
                        worker_results.append(result)
                    except Exception as e:
                        logger.error(f"Worker failed: {str(e)}")
            
            total_duration = time.time() - start_time
            
            # Analyze results
            total_operations = sum(r["operations_attempted"] for r in worker_results)
            successful_operations = sum(r["operations_successful"] for r in worker_results)
            total_errors = sum(len(r["errors"]) for r in worker_results)
            
            success_rate = successful_operations / total_operations if total_operations > 0 else 0
            
            logger.info(f"✅ Concurrent access test completed")
            logger.info(f"✅ {successful_operations}/{total_operations} operations successful ({success_rate:.1%})")
            logger.info(f"✅ {total_errors} errors encountered")
            logger.info(f"✅ Total duration: {total_duration:.2f} seconds")
            
            return {
                "status": "success",
                "num_workers": num_workers,
                "operations_per_worker": operations_per_worker,
                "total_operations": total_operations,
                "successful_operations": successful_operations,
                "success_rate": success_rate,
                "total_errors": total_errors,
                "total_duration": total_duration,
                "worker_results": worker_results
            }
            
        except Exception as e:
            logger.error(f"❌ Concurrent access test failed: {str(e)}")
            return {
                "status": "failed",
                "error": str(e)
            }
    
    def test_backup_and_recovery(self) -> Dict[str, Any]:
        """Test backup creation and recovery capabilities"""
        logger.info("=== Backup and Recovery Test ===")
        
        try:
            # Create backup
            backup_start = time.time()
            shutil.copy2(self.db_path, self.backup_path)
            backup_duration = time.time() - backup_start
            
            backup_size = self.backup_path.stat().st_size
            original_size = self.db_path.stat().st_size
            
            logger.info(f"✅ Backup created in {backup_duration:.3f} seconds")
            logger.info(f"✅ Backup size: {backup_size} bytes (original: {original_size} bytes)")
            
            # Verify backup integrity
            integrity_verified = False
            with sqlite3.connect(self.backup_path) as backup_conn:
                cursor = backup_conn.cursor()
                
                # Test basic query on backup
                cursor.execute("SELECT COUNT(*) FROM customer_portfolios")
                backup_count = cursor.fetchone()[0]
                
                # Compare with original
                with sqlite3.connect(self.db_path) as original_conn:
                    orig_cursor = original_conn.cursor()
                    orig_cursor.execute("SELECT COUNT(*) FROM customer_portfolios")
                    original_count = orig_cursor.fetchone()[0]
                    
                    if backup_count == original_count:
                        integrity_verified = True
                        logger.info(f"✅ Backup integrity verified ({backup_count} records)")
                    else:
                        logger.error(f"❌ Backup integrity check failed: {backup_count} vs {original_count}")
            
            # Test recovery simulation (create temporary file)
            recovery_test_path = Path("demo_data/recovery_test.db")
            recovery_start = time.time()
            shutil.copy2(self.backup_path, recovery_test_path)
            recovery_duration = time.time() - recovery_start
            
            # Verify recovered database
            recovery_verified = False
            with sqlite3.connect(recovery_test_path) as recovery_conn:
                cursor = recovery_conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM customer_portfolios")
                recovered_count = cursor.fetchone()[0]
                
                if recovered_count == backup_count:
                    recovery_verified = True
                    logger.info(f"✅ Recovery test successful ({recovered_count} records)")
            
            # Cleanup
            if self.backup_path.exists():
                self.backup_path.unlink()
            if recovery_test_path.exists():
                recovery_test_path.unlink()
            
            return {
                "status": "success",
                "backup_created": True,
                "backup_duration": backup_duration,
                "backup_size_bytes": backup_size,
                "original_size_bytes": original_size,
                "integrity_verified": integrity_verified,
                "recovery_duration": recovery_duration,
                "recovery_verified": recovery_verified,
                "size_match": backup_size == original_size
            }
            
        except Exception as e:
            logger.error(f"❌ Backup and recovery test failed: {str(e)}")
            return {
                "status": "failed",
                "error": str(e)
            }
    
    def performance_benchmark(self) -> Dict[str, Any]:
        """Run performance benchmarks on the database"""
        logger.info("=== Performance Benchmark ===")
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                benchmarks = {}
                
                # Benchmark 1: Simple SELECT query
                start_time = time.time()
                cursor.execute("SELECT COUNT(*) FROM customer_portfolios")
                result = cursor.fetchone()
                benchmarks["simple_count"] = {
                    "duration": time.time() - start_time,
                    "result": result[0] if result else 0
                }
                
                # Benchmark 2: Complex aggregation query
                start_time = time.time()
                cursor.execute("""
                    SELECT asset_type, 
                           COUNT(*) as count,
                           AVG(value) as avg_value,
                           SUM(allocation_percent) as total_allocation
                    FROM customer_portfolios 
                    GROUP BY asset_type
                    ORDER BY count DESC
                """)
                results = cursor.fetchall()
                benchmarks["aggregation_query"] = {
                    "duration": time.time() - start_time,
                    "result_count": len(results)
                }
                
                # Benchmark 3: Index performance (if indexes exist)
                start_time = time.time()
                cursor.execute("""
                    SELECT * FROM customer_portfolios 
                    WHERE customer_id LIKE 'customer_%' 
                    LIMIT 100
                """)
                results = cursor.fetchall()
                benchmarks["filtered_query"] = {
                    "duration": time.time() - start_time,
                    "result_count": len(results)
                }
                
                # Database size and statistics
                cursor.execute("PRAGMA page_count")
                page_count = cursor.fetchone()[0]
                
                cursor.execute("PRAGMA page_size")
                page_size = cursor.fetchone()[0]
                
                total_size = page_count * page_size
                
                logger.info("✅ Performance benchmarks completed")
                for benchmark, result in benchmarks.items():
                    logger.info(f"  {benchmark}: {result['duration']:.4f}s")
                
                return {
                    "status": "success",
                    "benchmarks": benchmarks,
                    "database_stats": {
                        "page_count": page_count,
                        "page_size": page_size,
                        "total_size": total_size
                    }
                }
                
        except Exception as e:
            logger.error(f"❌ Performance benchmark failed: {str(e)}")
            return {
                "status": "failed",
                "error": str(e)
            }
    
    def generate_health_report(self) -> Dict[str, Any]:
        """Generate comprehensive database health report"""
        logger.info("\n" + "="*80)
        logger.info("COMPREHENSIVE DATABASE HEALTH REPORT")
        logger.info("="*80)
        
        # Run all verification tests
        tests = [
            ("Database Accessibility", self.verify_database_accessibility),
            ("Schema and Tables", self.verify_schema_and_tables),
            ("CRUD Operations", self.test_crud_operations),
            ("Data Persistence", self.test_data_persistence),
            ("Concurrent Access", self.test_concurrent_access),
            ("Backup and Recovery", self.test_backup_and_recovery),
            ("Performance Benchmark", self.performance_benchmark)
        ]
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "database_path": str(self.db_path.absolute()),
            "tests": {},
            "summary": {}
        }
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test_name, test_func in tests:
            logger.info(f"\n{test_name}:")
            logger.info("-" * 50)
            
            try:
                result = test_func()
                report["tests"][test_name] = result
                
                if result.get("status") == "success":
                    passed_tests += 1
                    logger.info(f"✅ {test_name}: PASSED")
                else:
                    logger.info(f"❌ {test_name}: FAILED")
                    if "error" in result:
                        logger.info(f"   Error: {result['error']}")
                        
            except Exception as e:
                logger.error(f"❌ {test_name}: EXCEPTION - {str(e)}")
                report["tests"][test_name] = {
                    "status": "failed",
                    "error": f"Exception: {str(e)}"
                }
        
        # Generate summary
        report["summary"] = {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": total_tests - passed_tests,
            "success_rate": passed_tests / total_tests,
            "overall_health": "healthy" if passed_tests == total_tests else "degraded"
        }
        
        logger.info("\n" + "="*80)
        logger.info("SUMMARY")
        logger.info("="*80)
        logger.info(f"Tests Passed: {passed_tests}/{total_tests} ({report['summary']['success_rate']:.1%})")
        logger.info(f"Overall Health: {report['summary']['overall_health'].upper()}")
        
        if passed_tests == total_tests:
            logger.info("\n🎉 Database is fully operational and healthy!")
            logger.info("\nRecommendations:")
            logger.info("- Database operations are working correctly")
            logger.info("- Consider setting up automated backups")
            logger.info("- Monitor performance metrics regularly")
            logger.info("- Implement connection pooling for production use")
        else:
            logger.info(f"\n⚠️  Database has issues that need attention!")
            logger.info("\nRecommendations:")
            logger.info("- Review failed tests and address issues")
            logger.info("- Check database file permissions and access")
            logger.info("- Verify SQLite installation and version")
            logger.info("- Consider database repair or recreation if needed")
        
        # Save report to file
        report_file = Path("database_health_report.json")
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"\n📊 Detailed report saved to: {report_file.absolute()}")
        
        return report

def main():
    """Main execution function"""
    print("Financial Planning Database Verification")
    print("=" * 50)
    
    # Initialize verification
    verifier = DatabaseVerification()
    
    # Generate comprehensive health report
    report = verifier.generate_health_report()
    
    # Return exit code based on results
    success_rate = report["summary"]["success_rate"]
    exit_code = 0 if success_rate == 1.0 else 1
    
    return exit_code

if __name__ == "__main__":
    sys.exit(main())