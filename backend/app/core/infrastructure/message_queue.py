"""
Advanced Message Queue Infrastructure with Celery Integration

Provides:
- Distributed task execution
- Task scheduling and orchestration
- Result backend management
- Task routing and priority queues
- Error handling and retries
- Task monitoring and tracking
"""

import asyncio
import logging
import uuid
from datetime import datetime, timedelta, timezone
from enum import Enum
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from celery import Celery, Task, group, chain, chord
from celery.result import AsyncResult, GroupResult
from celery.schedules import crontab
from kombu import Queue, Exchange
from kombu.serialization import register

from app.core.config import settings

logger = logging.getLogger(__name__)


class TaskPriority(Enum):
    """Task priority levels"""
    LOW = 0
    NORMAL = 5
    HIGH = 7
    CRITICAL = 10


class TaskStatus(Enum):
    """Task execution status"""
    PENDING = "PENDING"
    STARTED = "STARTED"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    RETRY = "RETRY"
    REVOKED = "REVOKED"


# Custom JSON serializer for better data type support
def custom_json_encoder(obj):
    """Custom JSON encoder for complex types"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif hasattr(obj, 'to_dict'):
        return obj.to_dict()
    return str(obj)


# Register custom serialization
register(
    'custom_json',
    lambda x: json.dumps(x, default=custom_json_encoder),
    lambda x: json.loads(x),
    content_type='application/json',
    content_encoding='utf-8'
)


class CeleryConfig:
    """Celery configuration"""
    
    # Broker settings
    broker_url = getattr(settings, 'CELERY_BROKER_URL', 'redis://localhost:6379/0')
    result_backend = getattr(settings, 'CELERY_RESULT_BACKEND', 'redis://localhost:6379/1')
    
    # Task settings
    task_serializer = 'json'
    result_serializer = 'json'
    accept_content = ['json']
    timezone = 'UTC'
    enable_utc = True
    
    # Task execution settings
    task_acks_late = True
    task_reject_on_worker_lost = True
    task_track_started = True
    task_time_limit = 3600  # 1 hour hard limit
    task_soft_time_limit = 3300  # 55 minutes soft limit
    
    # Result backend settings
    result_expires = 86400  # Results expire after 24 hours
    result_compression = 'gzip'
    result_extended = True  # Store task args and kwargs in result
    
    # Worker settings
    worker_prefetch_multiplier = 4
    worker_max_tasks_per_child = 1000
    worker_disable_rate_limits = False
    
    # Retry settings
    task_default_retry_delay = 60  # 1 minute
    task_max_retries = 3
    task_autoretry_for = (Exception,)
    
    # Routing
    task_routes = {
        'financial.analysis.*': {'queue': 'analysis', 'priority': TaskPriority.HIGH.value},
        'financial.optimization.*': {'queue': 'optimization', 'priority': TaskPriority.NORMAL.value},
        'financial.reports.*': {'queue': 'reports', 'priority': TaskPriority.LOW.value},
        'financial.realtime.*': {'queue': 'realtime', 'priority': TaskPriority.CRITICAL.value},
    }
    
    # Queue configuration
    task_queues = (
        Queue('default', Exchange('default'), routing_key='default'),
        Queue('analysis', Exchange('analysis'), routing_key='analysis', priority=TaskPriority.HIGH.value),
        Queue('optimization', Exchange('optimization'), routing_key='optimization', priority=TaskPriority.NORMAL.value),
        Queue('reports', Exchange('reports'), routing_key='reports', priority=TaskPriority.LOW.value),
        Queue('realtime', Exchange('realtime'), routing_key='realtime', priority=TaskPriority.CRITICAL.value),
    )
    
    # Beat schedule for periodic tasks
    beat_schedule = {
        'update-market-data': {
            'task': 'financial.realtime.update_market_data',
            'schedule': crontab(minute='*/5'),  # Every 5 minutes
            'options': {'priority': TaskPriority.HIGH.value}
        },
        'generate-daily-reports': {
            'task': 'financial.reports.generate_daily_reports',
            'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
            'options': {'priority': TaskPriority.LOW.value}
        },
        'portfolio-rebalancing-check': {
            'task': 'financial.optimization.check_rebalancing',
            'schedule': crontab(hour='*/6'),  # Every 6 hours
            'options': {'priority': TaskPriority.NORMAL.value}
        },
        'cleanup-old-tasks': {
            'task': 'financial.maintenance.cleanup_tasks',
            'schedule': crontab(hour=3, minute=0),  # Daily at 3 AM
            'options': {'priority': TaskPriority.LOW.value}
        }
    }


# Initialize Celery app
celery_app = Celery('financial_app')
celery_app.config_from_object(CeleryConfig)


class BaseTask(Task):
    """Base task class with enhanced features"""
    
    autoretry_for = (Exception,)
    retry_kwargs = {'max_retries': 3}
    retry_backoff = True
    retry_backoff_max = 600  # Max 10 minutes between retries
    retry_jitter = True
    
    def before_start(self, task_id, args, kwargs):
        """Called before task execution starts"""
        logger.info(f"Starting task {self.name} with ID {task_id}")
    
    def on_success(self, retval, task_id, args, kwargs):
        """Called on successful task completion"""
        logger.info(f"Task {self.name} with ID {task_id} completed successfully")
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Called on task failure"""
        logger.error(f"Task {self.name} with ID {task_id} failed: {exc}")
    
    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """Called when task is retried"""
        logger.warning(f"Retrying task {self.name} with ID {task_id}: {exc}")


class TaskManager:
    """High-level task management interface"""
    
    def __init__(self):
        self.celery = celery_app
        self._registered_tasks = {}
    
    def register_task(
        self,
        name: str,
        func: Callable,
        base: Task = BaseTask,
        **options
    ) -> Task:
        """Register a new task"""
        task = self.celery.task(
            name=name,
            base=base,
            **options
        )(func)
        
        self._registered_tasks[name] = task
        return task
    
    def submit_task(
        self,
        task_name: str,
        args: Tuple = (),
        kwargs: Dict = None,
        priority: TaskPriority = TaskPriority.NORMAL,
        countdown: Optional[int] = None,
        eta: Optional[datetime] = None,
        expires: Optional[Union[int, datetime]] = None,
        retry: bool = True,
        retry_policy: Dict = None
    ) -> AsyncResult:
        """Submit task for execution"""
        kwargs = kwargs or {}
        
        task = self._registered_tasks.get(task_name)
        if not task:
            raise ValueError(f"Task {task_name} not registered")
        
        options = {
            'priority': priority.value,
            'countdown': countdown,
            'eta': eta,
            'expires': expires,
            'retry': retry
        }
        
        if retry_policy:
            options['retry_policy'] = retry_policy
        
        # Remove None values
        options = {k: v for k, v in options.items() if v is not None}
        
        return task.apply_async(args=args, kwargs=kwargs, **options)
    
    def submit_group(
        self,
        tasks: List[Tuple[str, Tuple, Dict]],
        **options
    ) -> GroupResult:
        """Submit group of tasks for parallel execution"""
        task_signatures = []
        
        for task_name, args, kwargs in tasks:
            task = self._registered_tasks.get(task_name)
            if not task:
                raise ValueError(f"Task {task_name} not registered")
            
            task_signatures.append(task.s(*args, **kwargs))
        
        job = group(task_signatures)
        return job.apply_async(**options)
    
    def submit_chain(
        self,
        tasks: List[Tuple[str, Tuple, Dict]],
        **options
    ) -> AsyncResult:
        """Submit chain of tasks for sequential execution"""
        task_signatures = []
        
        for task_name, args, kwargs in tasks:
            task = self._registered_tasks.get(task_name)
            if not task:
                raise ValueError(f"Task {task_name} not registered")
            
            task_signatures.append(task.s(*args, **kwargs))
        
        workflow = chain(*task_signatures)
        return workflow.apply_async(**options)
    
    def submit_chord(
        self,
        header_tasks: List[Tuple[str, Tuple, Dict]],
        callback_task: Tuple[str, Tuple, Dict],
        **options
    ) -> AsyncResult:
        """Submit chord (group with callback) for map-reduce pattern"""
        header_signatures = []
        
        for task_name, args, kwargs in header_tasks:
            task = self._registered_tasks.get(task_name)
            if not task:
                raise ValueError(f"Task {task_name} not registered")
            
            header_signatures.append(task.s(*args, **kwargs))
        
        callback_name, callback_args, callback_kwargs = callback_task
        callback = self._registered_tasks.get(callback_name)
        if not callback:
            raise ValueError(f"Callback task {callback_name} not registered")
        
        workflow = chord(header_signatures)(callback.s(*callback_args, **callback_kwargs))
        return workflow.apply_async(**options)
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get task execution status"""
        result = AsyncResult(task_id, app=self.celery)
        
        return {
            'task_id': task_id,
            'status': result.status,
            'result': result.result if result.successful() else None,
            'error': str(result.info) if result.failed() else None,
            'traceback': result.traceback if result.failed() else None,
            'ready': result.ready(),
            'successful': result.successful(),
            'failed': result.failed()
        }
    
    def cancel_task(self, task_id: str, terminate: bool = False) -> bool:
        """Cancel a running task"""
        try:
            result = AsyncResult(task_id, app=self.celery)
            result.revoke(terminate=terminate)
            return True
        except Exception as e:
            logger.error(f"Failed to cancel task {task_id}: {e}")
            return False
    
    def get_active_tasks(self) -> List[Dict[str, Any]]:
        """Get list of active tasks"""
        inspect = self.celery.control.inspect()
        
        active = inspect.active()
        if not active:
            return []
        
        tasks = []
        for worker, task_list in active.items():
            for task in task_list:
                tasks.append({
                    'worker': worker,
                    'task_id': task['id'],
                    'name': task['name'],
                    'args': task.get('args', []),
                    'kwargs': task.get('kwargs', {}),
                    'time_start': task.get('time_start')
                })
        
        return tasks
    
    def get_scheduled_tasks(self) -> List[Dict[str, Any]]:
        """Get list of scheduled tasks"""
        inspect = self.celery.control.inspect()
        
        scheduled = inspect.scheduled()
        if not scheduled:
            return []
        
        tasks = []
        for worker, task_list in scheduled.items():
            for task in task_list:
                tasks.append({
                    'worker': worker,
                    'task_id': task['id'],
                    'name': task['name'],
                    'eta': task.get('eta'),
                    'priority': task.get('priority'),
                    'args': task.get('args', []),
                    'kwargs': task.get('kwargs', {})
                })
        
        return tasks
    
    def get_worker_stats(self) -> Dict[str, Any]:
        """Get worker statistics"""
        inspect = self.celery.control.inspect()
        
        stats = inspect.stats()
        if not stats:
            return {}
        
        worker_stats = {}
        for worker, stat in stats.items():
            worker_stats[worker] = {
                'total_tasks': stat.get('total', {}),
                'pool': stat.get('pool', {}),
                'prefetch_count': stat.get('prefetch_count'),
                'clock': stat.get('clock'),
                'uptime': stat.get('uptime')
            }
        
        return worker_stats


# Task decorator for async functions
def async_task(name: str = None, **options):
    """Decorator to convert async function to Celery task"""
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(func(*args, **kwargs))
            finally:
                loop.close()
        
        task_name = name or f"{func.__module__}.{func.__name__}"
        return celery_app.task(name=task_name, base=BaseTask, **options)(wrapper)
    
    return decorator


# Financial calculation tasks
@celery_app.task(name='financial.analysis.calculate_portfolio_metrics', base=BaseTask)
def calculate_portfolio_metrics(portfolio_id: str, date_range: Dict = None) -> Dict[str, Any]:
    """Calculate comprehensive portfolio metrics"""
    logger.info(f"Calculating metrics for portfolio {portfolio_id}")
    
    # Simulate complex calculation
    import time
    time.sleep(2)
    
    return {
        'portfolio_id': portfolio_id,
        'total_value': 1000000,
        'returns': {
            'daily': 0.02,
            'weekly': 0.05,
            'monthly': 0.08,
            'yearly': 0.15
        },
        'risk_metrics': {
            'volatility': 0.18,
            'sharpe_ratio': 1.2,
            'beta': 0.95,
            'alpha': 0.03
        },
        'calculated_at': datetime.now(timezone.utc).isoformat()
    }


@celery_app.task(name='financial.optimization.optimize_portfolio', base=BaseTask)
def optimize_portfolio(portfolio_id: str, constraints: Dict = None) -> Dict[str, Any]:
    """Run portfolio optimization"""
    logger.info(f"Optimizing portfolio {portfolio_id}")
    
    # Simulate optimization
    import time
    time.sleep(5)
    
    return {
        'portfolio_id': portfolio_id,
        'optimal_allocation': {
            'stocks': 0.60,
            'bonds': 0.30,
            'real_estate': 0.05,
            'commodities': 0.05
        },
        'expected_return': 0.12,
        'expected_risk': 0.15,
        'optimized_at': datetime.now(timezone.utc).isoformat()
    }


@celery_app.task(name='financial.reports.generate_report', base=BaseTask)
def generate_portfolio_report(portfolio_id: str, report_type: str = 'comprehensive') -> Dict[str, Any]:
    """Generate portfolio report"""
    logger.info(f"Generating {report_type} report for portfolio {portfolio_id}")
    
    # Simulate report generation
    import time
    time.sleep(3)
    
    return {
        'portfolio_id': portfolio_id,
        'report_type': report_type,
        'report_url': f"/reports/{portfolio_id}/{uuid.uuid4()}.pdf",
        'generated_at': datetime.now(timezone.utc).isoformat()
    }


# Global task manager instance
task_manager = TaskManager()

# Register default tasks
task_manager.register_task(
    'financial.analysis.calculate_portfolio_metrics',
    calculate_portfolio_metrics
)
task_manager.register_task(
    'financial.optimization.optimize_portfolio',
    optimize_portfolio
)
task_manager.register_task(
    'financial.reports.generate_report',
    generate_portfolio_report
)


# Health check for Celery
async def celery_health_check() -> Dict[str, Any]:
    """Check Celery and worker health"""
    try:
        inspect = celery_app.control.inspect()
        
        # Check for active workers
        active_workers = inspect.active_queues()
        if not active_workers:
            return {
                'status': 'unhealthy',
                'error': 'No active workers found'
            }
        
        # Get worker stats
        stats = inspect.stats()
        
        return {
            'status': 'healthy',
            'workers': list(active_workers.keys()),
            'worker_count': len(active_workers),
            'stats': stats
        }
        
    except Exception as e:
        return {
            'status': 'unhealthy',
            'error': str(e)
        }