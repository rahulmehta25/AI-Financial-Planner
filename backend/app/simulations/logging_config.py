"""
Logging Configuration for Monte Carlo Simulation Engine

Provides comprehensive logging, error handling, and performance monitoring
for all simulation components.
"""

import logging
import sys
import traceback
import time
import functools
from typing import Any, Callable, Dict, Optional, Union
from datetime import datetime
from contextlib import contextmanager
import warnings

# Configure warnings to be logged
warnings.filterwarnings('default')
logging.captureWarnings(True)


class SimulationLogger:
    """
    Centralized logging configuration for simulation engine
    
    Features:
    - Performance monitoring
    - Error tracking and reporting
    - Structured logging with context
    - Memory and resource monitoring
    """
    
    def __init__(self, name: str = "monte_carlo_simulation", level: int = logging.INFO):
        """
        Initialize simulation logger
        
        Args:
            name: Logger name
            level: Logging level
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        
        # Prevent duplicate handlers
        if not self.logger.handlers:
            self._setup_handlers()
        
        self.performance_metrics = {}
        self.error_count = 0
        self.warning_count = 0
    
    def _setup_handlers(self):
        """Setup logging handlers with appropriate formatting"""
        
        # Console handler with detailed formatting
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        console_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
        console_handler.setFormatter(console_format)
        
        # File handler for detailed logs (if needed in production)
        try:
            file_handler = logging.FileHandler('simulation_engine.log')
            file_handler.setLevel(logging.DEBUG)
            
            file_format = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(module)s.%(funcName)s:%(lineno)d - %(message)s - [%(pathname)s]'
            )
            file_handler.setFormatter(file_format)
            self.logger.addHandler(file_handler)
            
        except (PermissionError, OSError):
            # Skip file logging if not possible (e.g., in containerized environments)
            pass
        
        self.logger.addHandler(console_handler)
    
    def log_simulation_start(self, parameters: Dict[str, Any]) -> None:
        """Log the start of a simulation with parameters"""
        self.logger.info("="*60)
        self.logger.info("MONTE CARLO SIMULATION STARTED")
        self.logger.info("="*60)
        
        for key, value in parameters.items():
            self.logger.info(f"Parameter {key}: {value}")
        
        self.performance_metrics['simulation_start_time'] = time.time()
    
    def log_simulation_end(self, success: bool, results_summary: Optional[Dict] = None) -> None:
        """Log the end of a simulation with results"""
        
        end_time = time.time()
        duration = end_time - self.performance_metrics.get('simulation_start_time', end_time)
        
        self.logger.info("="*60)
        self.logger.info(f"MONTE CARLO SIMULATION {'COMPLETED' if success else 'FAILED'}")
        self.logger.info(f"Duration: {duration:.2f} seconds")
        
        if results_summary:
            self.logger.info(f"Success Rate: {results_summary.get('success_probability', 'N/A'):.1%}")
            self.logger.info(f"Median Balance: ${results_summary.get('median_balance', 0):,.0f}")
        
        self.logger.info(f"Errors: {self.error_count}, Warnings: {self.warning_count}")
        self.logger.info("="*60)
        
        # Reset counters
        self.error_count = 0
        self.warning_count = 0
    
    def log_performance_metric(self, metric_name: str, value: Union[float, int], unit: str = "") -> None:
        """Log a performance metric"""
        self.performance_metrics[metric_name] = value
        self.logger.debug(f"Performance metric - {metric_name}: {value} {unit}")
    
    def log_error(self, error: Exception, context: Optional[str] = None, **kwargs) -> None:
        """Log an error with full context"""
        self.error_count += 1
        
        error_msg = f"ERROR: {type(error).__name__}: {str(error)}"
        if context:
            error_msg = f"{context} - {error_msg}"
        
        # Log additional context
        for key, value in kwargs.items():
            error_msg += f"\n  {key}: {value}"
        
        # Log stack trace for debugging
        self.logger.error(error_msg)
        self.logger.debug("Stack trace:", exc_info=True)
    
    def log_warning(self, message: str, **kwargs) -> None:
        """Log a warning with context"""
        self.warning_count += 1
        
        warning_msg = f"WARNING: {message}"
        for key, value in kwargs.items():
            warning_msg += f"\n  {key}: {value}"
        
        self.logger.warning(warning_msg)
    
    def log_validation_error(self, validation_errors: list, context: str = "Validation") -> None:
        """Log validation errors"""
        self.error_count += len(validation_errors)
        
        self.logger.error(f"{context} failed with {len(validation_errors)} error(s):")
        for i, error in enumerate(validation_errors, 1):
            self.logger.error(f"  {i}. {error}")
    
    @contextmanager
    def performance_timer(self, operation_name: str):
        """Context manager for timing operations"""
        start_time = time.time()
        self.logger.debug(f"Starting operation: {operation_name}")
        
        try:
            yield
        except Exception as e:
            self.logger.error(f"Operation '{operation_name}' failed: {str(e)}")
            raise
        finally:
            duration = time.time() - start_time
            self.log_performance_metric(f"{operation_name}_duration", duration, "seconds")
            self.logger.info(f"Operation '{operation_name}' completed in {duration:.2f} seconds")
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance metrics summary"""
        return {
            "metrics": self.performance_metrics.copy(),
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "timestamp": datetime.now().isoformat()
        }


def performance_monitor(logger: SimulationLogger):
    """Decorator for monitoring function performance"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            operation_name = f"{func.__module__}.{func.__name__}"
            
            with logger.performance_timer(operation_name):
                try:
                    result = func(*args, **kwargs)
                    logger.logger.debug(f"Function {func.__name__} executed successfully")
                    return result
                    
                except Exception as e:
                    logger.log_error(
                        e, 
                        context=f"Function {func.__name__}",
                        args=str(args)[:200],  # Truncate long args
                        kwargs=str(kwargs)[:200]
                    )
                    raise
        
        return wrapper
    return decorator


def error_handler(logger: SimulationLogger, default_return=None, raise_on_error: bool = True):
    """Decorator for handling errors gracefully"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
                
            except Exception as e:
                logger.log_error(
                    e,
                    context=f"Error in {func.__name__}",
                    function_args=str(args)[:200],
                    function_kwargs=str(kwargs)[:200]
                )
                
                if raise_on_error:
                    raise
                else:
                    logger.logger.warning(f"Returning default value due to error in {func.__name__}")
                    return default_return
        
        return wrapper
    return decorator


def validate_inputs(logger: SimulationLogger, validation_func: Callable):
    """Decorator for input validation"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                # Run validation
                validation_result = validation_func(*args, **kwargs)
                
                if validation_result is not True:
                    if isinstance(validation_result, list):
                        logger.log_validation_error(validation_result, f"Input validation for {func.__name__}")
                        raise ValueError(f"Input validation failed: {validation_result}")
                    elif isinstance(validation_result, str):
                        logger.log_validation_error([validation_result], f"Input validation for {func.__name__}")
                        raise ValueError(f"Input validation failed: {validation_result}")
                    else:
                        logger.log_validation_error(["Unknown validation error"], f"Input validation for {func.__name__}")
                        raise ValueError("Input validation failed")
                
                return func(*args, **kwargs)
                
            except Exception as e:
                logger.log_error(e, context=f"Validation error in {func.__name__}")
                raise
        
        return wrapper
    return decorator


class SimulationException(Exception):
    """Base exception for simulation-related errors"""
    pass


class ValidationError(SimulationException):
    """Exception raised for validation errors"""
    pass


class CalculationError(SimulationException):
    """Exception raised for calculation errors"""
    pass


class DataError(SimulationException):
    """Exception raised for data-related errors"""
    pass


class PerformanceError(SimulationException):
    """Exception raised for performance-related issues"""
    pass


def setup_simulation_logging(level: int = logging.INFO) -> SimulationLogger:
    """
    Setup simulation logging with appropriate configuration
    
    Args:
        level: Logging level
        
    Returns:
        Configured SimulationLogger instance
    """
    # Suppress some noisy third-party loggers
    logging.getLogger('matplotlib').setLevel(logging.WARNING)
    logging.getLogger('numba').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    
    return SimulationLogger("simulation_engine", level)


def log_memory_usage(logger: SimulationLogger, context: str = "Memory check"):
    """Log current memory usage (if psutil is available)"""
    try:
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        
        logger.logger.debug(
            f"{context} - Memory usage: "
            f"RSS={memory_info.rss / 1024 / 1024:.1f}MB, "
            f"VMS={memory_info.vms / 1024 / 1024:.1f}MB"
        )
        
        # Log system memory if available
        system_memory = psutil.virtual_memory()
        logger.logger.debug(
            f"{context} - System memory: "
            f"Available={system_memory.available / 1024 / 1024:.1f}MB, "
            f"Used={system_memory.percent:.1f}%"
        )
        
    except ImportError:
        logger.logger.debug("psutil not available - skipping memory logging")
    except Exception as e:
        logger.logger.debug(f"Error logging memory usage: {str(e)}")


# Create a default logger instance that can be imported and used
default_logger = setup_simulation_logging()


# Convenience functions for common logging patterns
def log_simulation_config(config: Dict[str, Any]) -> None:
    """Log simulation configuration"""
    default_logger.logger.info("Simulation Configuration:")
    for key, value in config.items():
        default_logger.logger.info(f"  {key}: {value}")


def log_market_assumptions(assumptions_summary: Dict[str, Any]) -> None:
    """Log market assumptions summary"""
    default_logger.logger.info("Market Assumptions:")
    default_logger.logger.info(f"  Asset classes: {assumptions_summary.get('asset_classes', 'N/A')}")
    default_logger.logger.info(f"  Expected return range: {assumptions_summary.get('expected_returns', {}).get('min', 0):.1%} - {assumptions_summary.get('expected_returns', {}).get('max', 0):.1%}")
    default_logger.logger.info(f"  Volatility range: {assumptions_summary.get('volatilities', {}).get('min', 0):.1%} - {assumptions_summary.get('volatilities', {}).get('max', 0):.1%}")


def log_portfolio_allocation(allocation: Dict[str, float]) -> None:
    """Log portfolio allocation"""
    default_logger.logger.info("Portfolio Allocation:")
    for asset_class, weight in allocation.items():
        if weight > 0.001:  # Only log meaningful allocations
            default_logger.logger.info(f"  {asset_class}: {weight:.1%}")


def log_results_summary(results: Dict[str, Any]) -> None:
    """Log simulation results summary"""
    default_logger.logger.info("Simulation Results Summary:")
    default_logger.logger.info(f"  Success probability: {results.get('success_probability', 0):.1%}")
    
    if 'outcome_metrics' in results:
        metrics = results['outcome_metrics']
        default_logger.logger.info(f"  Median balance: ${metrics.get('percentiles', {}).get('percentile_50', 0):,.0f}")
        default_logger.logger.info(f"  10th percentile: ${metrics.get('percentiles', {}).get('percentile_10', 0):,.0f}")
        default_logger.logger.info(f"  90th percentile: ${metrics.get('percentiles', {}).get('percentile_90', 0):,.0f}")


# Global exception handler for unhandled exceptions
def handle_unhandled_exception(exc_type, exc_value, exc_traceback):
    """Handle unhandled exceptions"""
    if issubclass(exc_type, KeyboardInterrupt):
        # Let keyboard interrupts through
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    
    default_logger.logger.critical(
        "Unhandled exception occurred",
        exc_info=(exc_type, exc_value, exc_traceback)
    )


# Install global exception handler
sys.excepthook = handle_unhandled_exception