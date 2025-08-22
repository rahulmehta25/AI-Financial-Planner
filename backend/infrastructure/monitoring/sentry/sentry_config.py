import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.asyncio import AsyncioIntegration
from sentry_sdk.integrations.httpx import HttpxIntegration
import logging
import os

def init_sentry(app_env: str = "production"):
    """Initialize Sentry error tracking with comprehensive integrations"""
    
    sentry_dsn = os.getenv("SENTRY_DSN")
    if not sentry_dsn:
        logging.warning("SENTRY_DSN not found in environment variables")
        return
    
    # Configure logging integration
    sentry_logging = LoggingIntegration(
        level=logging.INFO,        # Capture info and above as breadcrumbs
        event_level=logging.ERROR  # Send errors as events
    )
    
    sentry_sdk.init(
        dsn=sentry_dsn,
        environment=app_env,
        integrations=[
            FastApiIntegration(auto_enabling_integrations=True),
            SqlalchemyIntegration(),
            RedisIntegration(),
            CeleryIntegration(),
            AsyncioIntegration(),
            HttpxIntegration(),
            sentry_logging,
        ],
        
        # Performance Monitoring
        traces_sample_rate=0.1,  # 10% of transactions for performance monitoring
        profiles_sample_rate=0.1,  # Profile 10% of sampled transactions
        
        # Error Sampling
        sample_rate=1.0,  # Send 100% of error events
        
        # Release tracking
        release=os.getenv("GIT_COMMIT_HASH", "unknown"),
        
        # Additional configuration
        attach_stacktrace=True,
        send_default_pii=False,  # Don't send personally identifiable information
        max_breadcrumbs=50,
        
        # Custom tags
        before_send=before_send_filter,
        before_send_transaction=before_send_transaction_filter,
    )

def before_send_filter(event, hint):
    """Filter sensitive information before sending to Sentry"""
    
    # Remove sensitive financial data from error reports
    if 'extra' in event:
        sensitive_keys = [
            'password', 'token', 'key', 'secret', 'ssn', 
            'account_number', 'routing_number', 'credit_card',
            'bank_account', 'api_key', 'access_token'
        ]
        
        for key in list(event['extra'].keys()):
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                event['extra'][key] = '[Filtered]'
    
    # Filter out specific errors that are not actionable
    if 'exception' in event:
        for exception in event['exception']['values']:
            if exception['type'] in ['ConnectionError', 'TimeoutError'] and \
               'market_data' in str(exception.get('value', '')):
                # Don't send market data connection errors as they're external
                return None
    
    # Add custom tags based on error context
    if 'tags' not in event:
        event['tags'] = {}
    
    # Tag financial planning specific errors
    if 'simulation' in str(event.get('message', '')).lower():
        event['tags']['component'] = 'monte_carlo'
    elif 'recommendation' in str(event.get('message', '')).lower():
        event['tags']['component'] = 'ai_recommendations'
    elif 'portfolio' in str(event.get('message', '')).lower():
        event['tags']['component'] = 'portfolio_management'
    elif 'market_data' in str(event.get('message', '')).lower():
        event['tags']['component'] = 'market_data'
    
    return event

def before_send_transaction_filter(event, hint):
    """Filter transaction data before sending to Sentry"""
    
    # Don't track health check endpoints
    if event.get('transaction') in ['/health', '/metrics', '/ready']:
        return None
    
    # Sample financial simulation transactions differently
    if '/api/v1/simulations' in event.get('transaction', ''):
        # Only track 5% of simulation transactions due to high volume
        import random
        if random.random() > 0.05:
            return None
    
    return event

def configure_sentry_scope():
    """Configure Sentry scope with additional context"""
    
    with sentry_sdk.configure_scope() as scope:
        scope.set_tag("service", "financial-planning-api")
        scope.set_tag("version", os.getenv("APP_VERSION", "unknown"))
        scope.set_context("app", {
            "name": "Financial Planning Backend",
            "version": os.getenv("APP_VERSION", "unknown"),
            "build": os.getenv("BUILD_NUMBER", "unknown")
        })

def capture_financial_exception(
    error: Exception, 
    user_id: int = None, 
    simulation_id: str = None,
    additional_context: dict = None
):
    """Capture financial planning specific exceptions with context"""
    
    with sentry_sdk.configure_scope() as scope:
        if user_id:
            scope.set_user({"id": user_id})
        
        if simulation_id:
            scope.set_tag("simulation_id", simulation_id)
        
        if additional_context:
            for key, value in additional_context.items():
                scope.set_extra(key, value)
        
        scope.set_level("error")
        sentry_sdk.capture_exception(error)

def capture_business_metric(metric_name: str, value: float, tags: dict = None):
    """Capture business metrics as Sentry events for alerting"""
    
    with sentry_sdk.configure_scope() as scope:
        scope.set_level("info")
        
        if tags:
            for key, val in tags.items():
                scope.set_tag(key, val)
        
        scope.set_extra("metric_value", value)
        scope.set_extra("metric_name", metric_name)
        
        sentry_sdk.capture_message(
            f"Business Metric: {metric_name} = {value}",
            level="info"
        )

# Performance monitoring decorators
def monitor_simulation_performance(func):
    """Decorator to monitor Monte Carlo simulation performance"""
    import functools
    
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        with sentry_sdk.start_transaction(
            op="simulation",
            name=f"{func.__module__}.{func.__name__}"
        ) as transaction:
            try:
                result = await func(*args, **kwargs)
                transaction.set_tag("status", "success")
                return result
            except Exception as e:
                transaction.set_tag("status", "error")
                capture_financial_exception(e, additional_context={
                    "function": func.__name__,
                    "args": str(args)[:100],  # Truncate for privacy
                })
                raise
    
    return wrapper

def monitor_api_performance(func):
    """Decorator to monitor API endpoint performance"""
    import functools
    
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        with sentry_sdk.start_transaction(
            op="http",
            name=f"API: {func.__name__}"
        ) as transaction:
            try:
                result = await func(*args, **kwargs)
                transaction.set_tag("status", "success")
                return result
            except Exception as e:
                transaction.set_tag("status", "error")
                sentry_sdk.capture_exception(e)
                raise
    
    return wrapper