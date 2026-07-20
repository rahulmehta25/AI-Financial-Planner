from opentelemetry import trace, metrics
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.psycopg2 import Psycopg2Instrumentor
from opentelemetry.instrumentation.celery import CeleryInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION
from opentelemetry.semconv.resource import ResourceAttributes
from opentelemetry.propagate import set_global_textmap
from opentelemetry.propagators.b3 import B3MultiFormat
import os
import logging

# Custom instrumentor for financial planning specific operations
class FinancialPlanningInstrumentor:
    def __init__(self):
        self.tracer = trace.get_tracer("financial-planning")
        self.meter = metrics.get_meter("financial-planning")
        
        # Create custom metrics
        self.simulation_duration = self.meter.create_histogram(
            name="financial_simulation_duration_seconds",
            description="Time spent on Monte Carlo simulations",
            unit="s"
        )
        
        self.recommendation_counter = self.meter.create_counter(
            name="ai_recommendations_generated_total",
            description="Total number of AI recommendations generated"
        )
        
        self.portfolio_updates = self.meter.create_counter(
            name="portfolio_updates_total",
            description="Total number of portfolio updates"
        )
        
        self.market_data_latency = self.meter.create_histogram(
            name="market_data_fetch_duration_seconds",
            description="Time spent fetching market data",
            unit="s"
        )
        
        self.user_actions = self.meter.create_counter(
            name="financial_user_actions_total",
            description="Total number of user actions"
        )

def setup_tracing(service_name: str = "financial-planning-api"):
    """Setup OpenTelemetry tracing with Jaeger"""
    
    # Create resource with service information
    resource = Resource.create({
        SERVICE_NAME: service_name,
        SERVICE_VERSION: os.getenv("APP_VERSION", "unknown"),
        ResourceAttributes.SERVICE_NAMESPACE: "financial-planning",
        ResourceAttributes.SERVICE_INSTANCE_ID: os.getenv("HOSTNAME", "unknown"),
        ResourceAttributes.DEPLOYMENT_ENVIRONMENT: os.getenv("ENVIRONMENT", "production"),
    })
    
    # Setup tracer provider
    tracer_provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(tracer_provider)
    
    # Setup Jaeger exporter
    jaeger_exporter = JaegerExporter(
        agent_host_name=os.getenv("JAEGER_AGENT_HOST", "jaeger"),
        agent_port=int(os.getenv("JAEGER_AGENT_PORT", "6831")),
    )
    
    # Add span processor
    span_processor = BatchSpanProcessor(jaeger_exporter)
    tracer_provider.add_span_processor(span_processor)
    
    # Set B3 propagation for microservices compatibility
    set_global_textmap(B3MultiFormat())
    
    logging.info(f"OpenTelemetry tracing initialized for {service_name}")

def setup_metrics():
    """Setup OpenTelemetry metrics"""
    
    # Create Prometheus metric reader
    prometheus_reader = PrometheusMetricReader()
    
    # Create metric provider
    metric_provider = MeterProvider(
        resource=Resource.create({
            SERVICE_NAME: "financial-planning-api",
            SERVICE_VERSION: os.getenv("APP_VERSION", "unknown"),
        }),
        metric_readers=[prometheus_reader]
    )
    
    metrics.set_meter_provider(metric_provider)
    
    logging.info("OpenTelemetry metrics initialized")

def instrument_app(app):
    """Instrument FastAPI application with OpenTelemetry"""
    
    # Instrument FastAPI
    FastAPIInstrumentor.instrument_app(
        app,
        tracer_provider=trace.get_tracer_provider(),
        excluded_urls="health,metrics,ready"
    )
    
    # Instrument database connections
    SQLAlchemyInstrumentor().instrument()
    Psycopg2Instrumentor().instrument()
    
    # Instrument Redis
    RedisInstrumentor().instrument()
    
    # Instrument HTTP clients
    HTTPXClientInstrumentor().instrument()
    
    # Instrument Celery if used
    CeleryInstrumentor().instrument()
    
    logging.info("Application instrumented with OpenTelemetry")

def create_custom_span(operation_name: str, attributes: dict = None):
    """Create a custom span for financial planning operations"""
    
    tracer = trace.get_tracer("financial-planning")
    span = tracer.start_span(operation_name)
    
    if attributes:
        for key, value in attributes.items():
            span.set_attribute(key, value)
    
    return span

# Decorators for tracing specific operations
def trace_simulation(func):
    """Decorator to trace Monte Carlo simulations"""
    import functools
    import time
    
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        tracer = trace.get_tracer("financial-planning")
        
        with tracer.start_as_current_span(
            f"simulation.{func.__name__}",
            attributes={
                "simulation.type": "monte_carlo",
                "simulation.function": func.__name__
            }
        ) as span:
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                span.set_attribute("simulation.status", "success")
                
                # Record custom metrics
                instrumentor = FinancialPlanningInstrumentor()
                duration = time.time() - start_time
                instrumentor.simulation_duration.record(duration)
                
                return result
            except Exception as e:
                span.set_attribute("simulation.status", "error")
                span.set_attribute("error.message", str(e))
                span.record_exception(e)
                raise
    
    return wrapper

def trace_ai_recommendation(func):
    """Decorator to trace AI recommendation generation"""
    import functools
    
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        tracer = trace.get_tracer("financial-planning")
        
        with tracer.start_as_current_span(
            f"ai.recommendation.{func.__name__}",
            attributes={
                "ai.component": "recommendation_engine",
                "ai.function": func.__name__
            }
        ) as span:
            try:
                result = await func(*args, **kwargs)
                span.set_attribute("ai.status", "success")
                span.set_attribute("ai.recommendations_count", len(result) if isinstance(result, list) else 1)
                
                # Record metric
                instrumentor = FinancialPlanningInstrumentor()
                instrumentor.recommendation_counter.add(1)
                
                return result
            except Exception as e:
                span.set_attribute("ai.status", "error")
                span.record_exception(e)
                raise
    
    return wrapper

def trace_market_data(func):
    """Decorator to trace market data operations"""
    import functools
    import time
    
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        tracer = trace.get_tracer("financial-planning")
        
        with tracer.start_as_current_span(
            f"market_data.{func.__name__}",
            attributes={
                "market_data.provider": kwargs.get('provider', 'unknown'),
                "market_data.function": func.__name__
            }
        ) as span:
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                span.set_attribute("market_data.status", "success")
                
                # Record latency metric
                instrumentor = FinancialPlanningInstrumentor()
                duration = time.time() - start_time
                instrumentor.market_data_latency.record(duration)
                
                return result
            except Exception as e:
                span.set_attribute("market_data.status", "error")
                span.record_exception(e)
                raise
    
    return wrapper

def trace_portfolio_operation(func):
    """Decorator to trace portfolio management operations"""
    import functools
    
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        tracer = trace.get_tracer("financial-planning")
        
        with tracer.start_as_current_span(
            f"portfolio.{func.__name__}",
            attributes={
                "portfolio.operation": func.__name__,
                "portfolio.user_id": kwargs.get('user_id', 'unknown')
            }
        ) as span:
            try:
                result = await func(*args, **kwargs)
                span.set_attribute("portfolio.status", "success")
                
                # Record metric
                instrumentor = FinancialPlanningInstrumentor()
                instrumentor.portfolio_updates.add(1)
                
                return result
            except Exception as e:
                span.set_attribute("portfolio.status", "error")
                span.record_exception(e)
                raise
    
    return wrapper

# Context manager for custom tracing
class TracingContext:
    def __init__(self, operation_name: str, attributes: dict = None):
        self.operation_name = operation_name
        self.attributes = attributes or {}
        self.span = None
    
    def __enter__(self):
        tracer = trace.get_tracer("financial-planning")
        self.span = tracer.start_span(self.operation_name)
        
        for key, value in self.attributes.items():
            self.span.set_attribute(key, value)
        
        return self.span
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.span.set_attribute("error", True)
            self.span.record_exception(exc_val)
        
        self.span.end()

def initialize_tracing():
    """Initialize complete OpenTelemetry setup"""
    setup_tracing()
    setup_metrics()
    logging.info("OpenTelemetry initialization complete")