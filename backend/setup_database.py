#!/usr/bin/env python3
"""
Complete Database Setup Script for Financial Planning System

This script provides a comprehensive database setup and management tool that:
1. Initializes the complete database schema
2. Configures TimescaleDB for time-series data
3. Creates all required indexes and optimizations
4. Validates relationships and constraints
5. Provides health monitoring and maintenance

Usage:
    python setup_database.py --init          # Initialize complete database
    python setup_database.py --validate      # Validate database integrity  
    python setup_database.py --optimize      # Optimize database performance
    python setup_database.py --health        # Check database health
    python setup_database.py --all           # Run all operations
"""

import os
import sys
import argparse
import asyncio
import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.core.config import settings
from app.core.infrastructure.database import db_manager, timescale_manager
from app.database.initialize_database import database_initializer
from app.database.timescaledb_config import initialize_timescaledb
from app.database.performance_optimizer import performance_optimizer
from app.database.relationship_validator import relationship_validator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DatabaseSetupManager:
    """
    Comprehensive database setup and management system
    """
    
    def __init__(self):
        self.setup_results = {
            "initialization": {},
            "timescaledb": {},
            "optimization": {},
            "validation": {},
            "health": {},
            "errors": [],
            "warnings": []
        }
    
    async def run_complete_setup(self) -> Dict[str, Any]:
        """
        Run complete database setup process
        """
        print("🚀 Starting Complete Financial Planning Database Setup")
        print("=" * 60)
        
        try:
            # Initialize database connections
            print("\n📡 Initializing database connections...")
            await self._initialize_connections()
            
            # Step 1: Initialize database schema and structure
            print("\n🏗️  Step 1: Initializing database schema...")
            init_results = await self._run_database_initialization()
            self.setup_results["initialization"] = init_results
            self._print_step_results("Database Initialization", init_results)
            
            # Step 2: Configure TimescaleDB for time-series data
            print("\n⏰ Step 2: Configuring TimescaleDB...")
            timescale_results = await self._configure_timescaledb()
            self.setup_results["timescaledb"] = timescale_results
            self._print_step_results("TimescaleDB Configuration", timescale_results)
            
            # Step 3: Optimize database performance
            print("\n⚡ Step 3: Optimizing database performance...")
            optimization_results = await self._optimize_performance()
            self.setup_results["optimization"] = optimization_results
            self._print_step_results("Performance Optimization", optimization_results)
            
            # Step 4: Validate database integrity
            print("\n✅ Step 4: Validating database integrity...")
            validation_results = await self._validate_database()
            self.setup_results["validation"] = validation_results
            self._print_step_results("Database Validation", validation_results)
            
            # Step 5: Final health check
            print("\n🏥 Step 5: Final health check...")
            health_results = await self._check_database_health()
            self.setup_results["health"] = health_results
            self._print_step_results("Health Check", health_results)
            
            # Generate summary report
            await self._generate_setup_report()
            
            print("\n🎉 Database setup completed successfully!")
            
        except Exception as e:
            logger.error(f"Database setup failed: {e}")
            self.setup_results["errors"].append(str(e))
            print(f"\n❌ Setup failed: {e}")
            
        finally:
            await self._cleanup_connections()
        
        return self.setup_results
    
    async def _initialize_connections(self):
        """Initialize database connections"""
        try:
            await db_manager.initialize()
            await timescale_manager.initialize()
            logger.info("Database connections initialized")
        except Exception as e:
            raise Exception(f"Failed to initialize database connections: {e}")
    
    async def _run_database_initialization(self) -> Dict[str, Any]:
        """Run database initialization"""
        try:
            return await database_initializer.initialize_complete_database()
        except Exception as e:
            return {"error": str(e), "success": False}
    
    async def _configure_timescaledb(self) -> Dict[str, Any]:
        """Configure TimescaleDB"""
        try:
            if settings.TIMESCALEDB_ENABLED:
                return await initialize_timescaledb()
            else:
                return {"status": "disabled", "message": "TimescaleDB not enabled in settings"}
        except Exception as e:
            return {"error": str(e), "success": False}
    
    async def _optimize_performance(self) -> Dict[str, Any]:
        """Optimize database performance"""
        try:
            return await performance_optimizer.generate_performance_report()
        except Exception as e:
            return {"error": str(e), "success": False}
    
    async def _validate_database(self) -> Dict[str, Any]:
        """Validate database integrity"""
        try:
            return await relationship_validator.generate_validation_report()
        except Exception as e:
            return {"error": str(e), "success": False}
    
    async def _check_database_health(self) -> Dict[str, Any]:
        """Check database health"""
        try:
            return await database_initializer.get_database_health()
        except Exception as e:
            return {"error": str(e), "success": False}
    
    async def _cleanup_connections(self):
        """Cleanup database connections"""
        try:
            await db_manager.shutdown()
            await timescale_manager.shutdown()
            logger.info("Database connections closed")
        except Exception as e:
            logger.warning(f"Error during connection cleanup: {e}")
    
    def _print_step_results(self, step_name: str, results: Dict[str, Any]):
        """Print results for a setup step"""
        if "error" in results:
            print(f"   ❌ {step_name} failed: {results['error']}")
            return
        
        print(f"   ✅ {step_name} completed")
        
        # Print specific metrics based on step
        if step_name == "Database Initialization":
            if results.get("database_created"):
                print("      • Database created")
            if results.get("migrations_applied"):
                print("      • Migrations applied")
            if results.get("indexes_created"):
                print(f"      • {len(results['indexes_created'])} performance indexes created")
            if results.get("initial_data_seeded"):
                print("      • Initial data seeded")
        
        elif step_name == "TimescaleDB Configuration":
            if results.get("timescaledb_enabled"):
                print("      • TimescaleDB enabled")
                print(f"      • {len(results.get('hypertables_created', []))} hypertables created")
                print(f"      • {len(results.get('continuous_aggregates_created', []))} continuous aggregates created")
        
        elif step_name == "Performance Optimization":
            if "optimization_score" in results:
                print(f"      • Performance score: {results['optimization_score']:.1f}/100")
                print(f"      • Grade: {results.get('performance_grade', 'N/A')}")
        
        elif step_name == "Database Validation":
            if "validation_score" in results:
                print(f"      • Validation score: {results['validation_score']:.1f}/100")
                print(f"      • Grade: {results.get('validation_grade', 'N/A')}")
                print(f"      • Total issues: {results.get('summary', {}).get('total_issues', 0)}")
        
        elif step_name == "Health Check":
            status = results.get("status", "unknown")
            print(f"      • Status: {status.upper()}")
            if results.get("table_counts"):
                total_records = sum(results["table_counts"].values())
                print(f"      • Total records: {total_records:,}")
    
    async def _generate_setup_report(self):
        """Generate comprehensive setup report"""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        report_file = f"database_setup_report_{timestamp}.json"
        
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "database_url": settings.DATABASE_URL.split('@')[-1] if '@' in settings.DATABASE_URL else 'local',
            "setup_results": self.setup_results,
            "configuration": {
                "timescaledb_enabled": settings.TIMESCALEDB_ENABLED,
                "database_pool_size": settings.DATABASE_POOL_SIZE,
                "environment": settings.ENVIRONMENT
            },
            "recommendations": self._generate_recommendations()
        }
        
        try:
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            print(f"\n📄 Comprehensive setup report saved to: {report_file}")
        except Exception as e:
            logger.warning(f"Failed to save setup report: {e}")
    
    def _generate_recommendations(self) -> list:
        """Generate setup recommendations based on results"""
        recommendations = []
        
        # Check initialization results
        init_results = self.setup_results.get("initialization", {})
        if init_results.get("errors"):
            recommendations.append("❗ Review initialization errors and resolve before production use")
        
        # Check TimescaleDB results
        timescale_results = self.setup_results.get("timescaledb", {})
        if not timescale_results.get("timescaledb_enabled") and settings.DATABASE_URL.startswith("postgresql"):
            recommendations.append("💡 Consider enabling TimescaleDB for better time-series data performance")
        
        # Check performance results
        perf_results = self.setup_results.get("optimization", {})
        if perf_results.get("optimization_score", 100) < 80:
            recommendations.append("⚡ Performance score is below 80 - review and apply optimization recommendations")
        
        # Check validation results
        validation_results = self.setup_results.get("validation", {})
        if validation_results.get("summary", {}).get("error_issues", 0) > 0:
            recommendations.append("🔍 Database has validation errors that should be fixed before production")
        
        # Check health results
        health_results = self.setup_results.get("health", {})
        if health_results.get("status") != "healthy":
            recommendations.append("🏥 Database health check failed - investigate connectivity and configuration")
        
        if not recommendations:
            recommendations.append("🎉 Database setup is optimal and ready for production use!")
        
        return recommendations


async def run_initialization_only():
    """Run only database initialization"""
    print("🏗️  Running Database Initialization Only")
    print("=" * 45)
    
    try:
        await db_manager.initialize()
        result = await database_initializer.initialize_complete_database()
        
        if result.get("errors"):
            print(f"❌ Initialization failed with {len(result['errors'])} errors")
            for error in result["errors"][:3]:
                print(f"   • {error}")
        else:
            print("✅ Database initialization completed successfully")
            print(f"   • Database created: {result.get('database_created', False)}")
            print(f"   • Migrations applied: {result.get('migrations_applied', False)}")
            print(f"   • Indexes created: {len(result.get('indexes_created', []))}")
            
    finally:
        await db_manager.shutdown()


async def run_validation_only():
    """Run only database validation"""
    print("✅ Running Database Validation Only")
    print("=" * 40)
    
    try:
        await db_manager.initialize()
        report = await relationship_validator.generate_validation_report()
        
        if "error" in report:
            print(f"❌ Validation failed: {report['error']}")
        else:
            print(f"📊 Validation Score: {report['validation_score']:.1f}/100 (Grade: {report['validation_grade']})")
            print(f"   • Total Issues: {report['summary']['total_issues']}")
            print(f"   • Critical: {report['summary']['critical_issues']}")
            print(f"   • Errors: {report['summary']['error_issues']}")
            
    finally:
        await db_manager.shutdown()


async def run_optimization_only():
    """Run only database optimization"""
    print("⚡ Running Database Optimization Only")
    print("=" * 42)
    
    try:
        await db_manager.initialize()
        report = await performance_optimizer.generate_performance_report()
        
        if "error" in report:
            print(f"❌ Optimization failed: {report['error']}")
        else:
            print(f"📊 Performance Score: {report['optimization_score']:.1f}/100 (Grade: {report['performance_grade']})")
            print(f"   • Slow Queries: {report['summary']['slow_queries']}")
            print(f"   • Missing Indexes: {report['summary']['missing_indexes']}")
            
    finally:
        await db_manager.shutdown()


async def run_health_check():
    """Run only database health check"""
    print("🏥 Running Database Health Check Only")
    print("=" * 40)
    
    try:
        await db_manager.initialize()
        health = await database_initializer.get_database_health()
        
        print(f"Status: {health['status'].upper()}")
        print(f"Connection: {'✅' if health['connection_status'] else '❌'}")
        
        if health['table_counts']:
            total_records = sum(health['table_counts'].values())
            print(f"Total Records: {total_records:,}")
            
            print("\nTable Row Counts:")
            for table, count in sorted(health['table_counts'].items()):
                print(f"  {table}: {count:,} rows")
                
    finally:
        await db_manager.shutdown()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Financial Planning System Database Setup",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python setup_database.py --all          # Complete setup
  python setup_database.py --init         # Initialize only
  python setup_database.py --validate     # Validate only
  python setup_database.py --optimize     # Optimize only
  python setup_database.py --health       # Health check only
        """
    )
    
    parser.add_argument("--all", action="store_true", 
                       help="Run complete database setup")
    parser.add_argument("--init", action="store_true",
                       help="Initialize database schema and structure")
    parser.add_argument("--validate", action="store_true",
                       help="Validate database relationships and constraints")
    parser.add_argument("--optimize", action="store_true",
                       help="Optimize database performance")
    parser.add_argument("--health", action="store_true",
                       help="Check database health")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # If no specific action is specified, show help
    if not any([args.all, args.init, args.validate, args.optimize, args.health]):
        parser.print_help()
        return
    
    try:
        if args.all:
            setup_manager = DatabaseSetupManager()
            asyncio.run(setup_manager.run_complete_setup())
        elif args.init:
            asyncio.run(run_initialization_only())
        elif args.validate:
            asyncio.run(run_validation_only())
        elif args.optimize:
            asyncio.run(run_optimization_only())
        elif args.health:
            asyncio.run(run_health_check())
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Setup interrupted by user")
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        logger.exception("Setup failed with exception")


if __name__ == "__main__":
    main()