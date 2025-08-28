"""
Daily Operations Manager Usage Example

Demonstrates how to initialize and use the DailyOperationsManager
for automated daily financial operations.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from app.automation.daily_operations import DailyOperationsManager, OperationPhase

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def main():
    """Main example function"""
    
    # Initialize the Daily Operations Manager
    logger.info("Initializing Daily Operations Manager...")
    operations_manager = DailyOperationsManager()
    
    try:
        # Initialize all services
        await operations_manager.initialize()
        logger.info("Daily Operations Manager initialized successfully")
        
        # The scheduler will automatically run operations at scheduled times
        # For demonstration, let's manually trigger some operations
        
        logger.info("Running example operations...")
        
        # Example 1: Manually trigger pre-market operations
        logger.info("Triggering pre-market operations...")
        await operations_manager._execute_pre_market_operations()
        
        # Example 2: Check system health
        logger.info("Checking system health...")
        await operations_manager._health_check()
        
        # Example 3: Get operation summary
        if operations_manager.operation_summaries:
            latest_summary = operations_manager.operation_summaries[-1]
            logger.info(f"Latest operation summary:")
            logger.info(f"  Phase: {latest_summary.phase.value}")
            logger.info(f"  Total tasks: {latest_summary.total_tasks}")
            logger.info(f"  Successful: {latest_summary.successful_tasks}")
            logger.info(f"  Failed: {latest_summary.failed_tasks}")
            logger.info(f"  Duration: {latest_summary.total_duration:.2f}s")
        
        # Example 4: Monitor operations for a short period
        logger.info("Monitoring operations for 30 seconds...")
        await asyncio.sleep(30)
        
        # Example 5: Get task execution history
        logger.info("Task execution history:")
        for task_name, results in operations_manager.task_results.items():
            if results:
                latest_result = results[-1]
                logger.info(f"  {task_name}: {latest_result.status.value} "
                           f"({latest_result.duration:.2f}s)")
        
        logger.info("Example completed successfully")
        
    except Exception as e:
        logger.error(f"Example failed: {e}")
        
    finally:
        # Shutdown the manager
        logger.info("Shutting down operations manager...")
        await operations_manager.shutdown()
        logger.info("Shutdown completed")


async def run_continuous_example():
    """Example of running continuous operations"""
    
    logger.info("Starting continuous operations example...")
    operations_manager = DailyOperationsManager()
    
    try:
        await operations_manager.initialize()
        
        # Run for 24 hours (or until interrupted)
        logger.info("Operations manager running... Press Ctrl+C to stop")
        
        # Keep the program running
        while True:
            await asyncio.sleep(3600)  # Sleep for 1 hour
            
            # Log status every hour
            logger.info(f"Operations manager status at {datetime.now()}:")
            logger.info(f"  Current phase: {operations_manager.current_phase}")
            logger.info(f"  Running tasks: {len(operations_manager.running_tasks)}")
            logger.info(f"  Total summaries: {len(operations_manager.operation_summaries)}")
            
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    except Exception as e:
        logger.error(f"Continuous operation error: {e}")
    finally:
        await operations_manager.shutdown()


async def test_individual_operations():
    """Test individual operation phases"""
    
    logger.info("Testing individual operations...")
    operations_manager = DailyOperationsManager()
    
    try:
        await operations_manager.initialize()
        
        # Test each operation phase
        phases = [
            ("Pre-market", operations_manager._execute_pre_market_operations),
            ("Market Open", operations_manager._execute_market_open_operations),
            ("Mid-day", operations_manager._execute_mid_day_operations),
            ("Market Close", operations_manager._execute_market_close_operations),
            ("Post-market", operations_manager._execute_post_market_operations)
        ]
        
        for phase_name, phase_func in phases:
            logger.info(f"Testing {phase_name} operations...")
            start_time = datetime.now()
            
            try:
                await phase_func()
                duration = (datetime.now() - start_time).total_seconds()
                logger.info(f"{phase_name} completed in {duration:.2f}s")
                
            except Exception as e:
                logger.error(f"{phase_name} failed: {e}")
            
            # Wait between phases
            await asyncio.sleep(5)
        
        logger.info("Individual operations testing completed")
        
    except Exception as e:
        logger.error(f"Testing failed: {e}")
    finally:
        await operations_manager.shutdown()


async def monitor_system_health():
    """Example of system health monitoring"""
    
    logger.info("Starting system health monitoring...")
    operations_manager = DailyOperationsManager()
    
    try:
        await operations_manager.initialize()
        
        # Monitor health for 5 minutes
        end_time = datetime.now() + timedelta(minutes=5)
        
        while datetime.now() < end_time:
            # Perform health check
            await operations_manager._health_check()
            
            # Log system health
            health = operations_manager.system_health
            if health:
                logger.info(f"System health at {health.get('timestamp', 'unknown')}:")
                
                # Log service health
                services = health.get('services', {})
                for service, status in services.items():
                    logger.info(f"  {service}: {status.get('status', 'unknown')}")
                
                # Log system metrics
                system = health.get('system', {})
                if system:
                    logger.info(f"  System metrics: {system}")
            
            # Wait 30 seconds
            await asyncio.sleep(30)
        
        logger.info("Health monitoring completed")
        
    except Exception as e:
        logger.error(f"Health monitoring failed: {e}")
    finally:
        await operations_manager.shutdown()


if __name__ == "__main__":
    # Choose which example to run
    import sys
    
    if len(sys.argv) > 1:
        example_type = sys.argv[1]
        
        if example_type == "continuous":
            asyncio.run(run_continuous_example())
        elif example_type == "individual":
            asyncio.run(test_individual_operations())
        elif example_type == "health":
            asyncio.run(monitor_system_health())
        else:
            print("Available examples: continuous, individual, health")
    else:
        # Run the basic example
        asyncio.run(main())