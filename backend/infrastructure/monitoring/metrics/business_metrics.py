"""
Custom Business Metrics for Financial Planning Application
This module defines and collects business-specific metrics that are critical
for monitoring the health and performance of the financial planning system.
"""

from prometheus_client import Counter, Histogram, Gauge, Enum, Info
from prometheus_client import CollectorRegistry, generate_latest
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from enum import Enum as PyEnum
import time
import json
import logging
from contextlib import contextmanager

class SimulationType(PyEnum):
    MONTE_CARLO = "monte_carlo"
    GOAL_PROJECTION = "goal_projection"
    RISK_ANALYSIS = "risk_analysis"
    SCENARIO_ANALYSIS = "scenario_analysis"

class RecommendationType(PyEnum):
    PORTFOLIO_REBALANCE = "portfolio_rebalance"
    ASSET_ALLOCATION = "asset_allocation"
    GOAL_ADJUSTMENT = "goal_adjustment"
    RISK_REDUCTION = "risk_reduction"
    TAX_OPTIMIZATION = "tax_optimization"

class UserActionType(PyEnum):
    GOAL_CREATED = "goal_created"
    PORTFOLIO_UPDATED = "portfolio_updated"
    SIMULATION_RUN = "simulation_run"
    REPORT_GENERATED = "report_generated"
    RECOMMENDATION_ACCEPTED = "recommendation_accepted"
    VOICE_INTERACTION = "voice_interaction"
    BANKING_CONNECTED = "banking_connected"

class FinancialPlanningMetrics:
    """Collection of all business metrics for the financial planning system"""
    
    def __init__(self, registry: Optional[CollectorRegistry] = None):
        self.registry = registry or CollectorRegistry()
        self.logger = logging.getLogger(__name__)
        
        # Initialize all metrics
        self._init_simulation_metrics()
        self._init_recommendation_metrics()
        self._init_user_engagement_metrics()
        self._init_market_data_metrics()
        self._init_portfolio_metrics()
        self._init_pdf_generation_metrics()
        self._init_voice_interface_metrics()
        self._init_banking_integration_metrics()
        self._init_performance_metrics()
        self._init_business_kpi_metrics()
    
    def _init_simulation_metrics(self):
        """Initialize Monte Carlo simulation metrics"""
        
        self.simulations_total = Counter(
            name='financial_simulations_total',
            documentation='Total number of financial simulations run',
            labelnames=['simulation_type', 'user_tier', 'result_status'],
            registry=self.registry
        )
        
        self.simulation_duration = Histogram(
            name='financial_simulation_duration_seconds',
            documentation='Time spent on financial simulations',
            labelnames=['simulation_type', 'complexity_level'],
            buckets=[1, 5, 10, 30, 60, 120, 300, 600],
            registry=self.registry
        )
        
        self.simulation_iterations = Histogram(
            name='financial_simulation_iterations',
            documentation='Number of iterations in Monte Carlo simulations',
            labelnames=['simulation_type'],
            buckets=[100, 500, 1000, 5000, 10000, 50000, 100000],
            registry=self.registry
        )
        
        self.simulation_portfolio_value = Histogram(
            name='financial_simulation_portfolio_value_dollars',
            documentation='Portfolio values processed in simulations',
            labelnames=['simulation_type'],
            buckets=[1000, 10000, 50000, 100000, 500000, 1000000, 5000000],
            registry=self.registry
        )
        
        self.simulation_accuracy = Gauge(
            name='financial_simulation_accuracy_score',
            documentation='Accuracy score of simulation predictions',
            labelnames=['simulation_type', 'time_period'],
            registry=self.registry
        )
    
    def _init_recommendation_metrics(self):
        """Initialize AI recommendation metrics"""
        
        self.recommendations_generated = Counter(
            name='ai_recommendations_generated_total',
            documentation='Total number of AI recommendations generated',
            labelnames=['recommendation_type', 'confidence_level', 'user_segment'],
            registry=self.registry
        )
        
        self.recommendation_acceptance_rate = Gauge(
            name='ai_recommendation_acceptance_rate',
            documentation='Rate of AI recommendation acceptance by users',
            labelnames=['recommendation_type', 'time_period'],
            registry=self.registry
        )
        
        self.recommendation_generation_time = Histogram(
            name='ai_recommendation_generation_seconds',
            documentation='Time to generate AI recommendations',
            labelnames=['recommendation_type', 'model_version'],
            buckets=[0.1, 0.5, 1, 2, 5, 10, 30],
            registry=self.registry
        )
        
        self.recommendation_confidence = Histogram(
            name='ai_recommendation_confidence_score',
            documentation='Confidence scores of AI recommendations',
            labelnames=['recommendation_type'],
            buckets=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
            registry=self.registry
        )
        
        self.model_accuracy = Gauge(
            name='ai_model_accuracy_score',
            documentation='Accuracy of AI/ML models',
            labelnames=['model_name', 'model_version'],
            registry=self.registry
        )
    
    def _init_user_engagement_metrics(self):
        """Initialize user engagement and behavior metrics"""
        
        self.user_actions = Counter(
            name='financial_user_actions_total',
            documentation='Total number of user actions',
            labelnames=['action_type', 'user_segment', 'platform'],
            registry=self.registry
        )
        
        self.active_users = Gauge(
            name='financial_active_users_total',
            documentation='Number of active users',
            labelnames=['time_period', 'user_tier'],
            registry=self.registry
        )
        
        self.session_duration = Histogram(
            name='financial_user_session_duration_seconds',
            documentation='User session duration',
            labelnames=['user_tier', 'feature_used'],
            buckets=[30, 60, 180, 300, 600, 1200, 1800, 3600],
            registry=self.registry
        )
        
        self.goal_completion_rate = Gauge(
            name='financial_goal_completion_rate',
            documentation='Rate of financial goal completion',
            labelnames=['goal_type', 'time_horizon', 'user_segment'],
            registry=self.registry
        )
        
        self.user_portfolio_value = Histogram(
            name='financial_user_portfolio_value_dollars',
            documentation='Distribution of user portfolio values',
            labelnames=['user_tier', 'account_age_months'],
            buckets=[1000, 10000, 50000, 100000, 500000, 1000000, 5000000],
            registry=self.registry
        )
    
    def _init_market_data_metrics(self):
        """Initialize market data and external API metrics"""
        
        self.market_data_requests = Counter(
            name='market_data_api_requests_total',
            documentation='Total market data API requests',
            labelnames=['provider', 'data_type', 'status'],
            registry=self.registry
        )
        
        self.market_data_latency = Histogram(
            name='market_data_fetch_duration_seconds',
            documentation='Market data fetch latency',
            labelnames=['provider', 'data_type'],
            buckets=[0.1, 0.5, 1, 2, 5, 10, 30],
            registry=self.registry
        )
        
        self.market_data_freshness = Gauge(
            name='market_data_freshness_minutes',
            documentation='Age of market data in minutes',
            labelnames=['provider', 'data_type'],
            registry=self.registry
        )
        
        self.api_rate_limit_remaining = Gauge(
            name='market_data_api_rate_limit_remaining',
            documentation='Remaining API rate limit calls',
            labelnames=['provider'],
            registry=self.registry
        )
        
        self.data_quality_score = Gauge(
            name='market_data_quality_score',
            documentation='Quality score of market data',
            labelnames=['provider', 'data_type'],
            registry=self.registry
        )
    
    def _init_portfolio_metrics(self):
        """Initialize portfolio management metrics"""
        
        self.portfolios_created = Counter(
            name='financial_portfolios_created_total',
            documentation='Total portfolios created',
            labelnames=['portfolio_type', 'risk_level', 'user_segment'],
            registry=self.registry
        )
        
        self.portfolio_updates = Counter(
            name='financial_portfolio_updates_total',
            documentation='Total portfolio updates',
            labelnames=['update_type', 'trigger_source'],
            registry=self.registry
        )
        
        self.portfolio_performance = Gauge(
            name='financial_portfolio_performance_percent',
            documentation='Portfolio performance percentage',
            labelnames=['portfolio_type', 'time_period'],
            registry=self.registry
        )
        
        self.asset_allocation_drift = Gauge(
            name='financial_asset_allocation_drift_percent',
            documentation='Asset allocation drift from target',
            labelnames=['portfolio_id', 'asset_class'],
            registry=self.registry
        )
        
        self.rebalancing_frequency = Counter(
            name='financial_portfolio_rebalancing_total',
            documentation='Portfolio rebalancing events',
            labelnames=['trigger_type', 'rebalancing_method'],
            registry=self.registry
        )
    
    def _init_pdf_generation_metrics(self):
        """Initialize PDF report generation metrics"""
        
        self.pdf_reports_generated = Counter(
            name='financial_pdf_reports_generated_total',
            documentation='Total PDF reports generated',
            labelnames=['report_type', 'template_version', 'user_tier'],
            registry=self.registry
        )
        
        self.pdf_generation_duration = Histogram(
            name='financial_pdf_generation_duration_seconds',
            documentation='PDF generation time',
            labelnames=['report_type', 'complexity'],
            buckets=[1, 5, 10, 20, 30, 60, 120],
            registry=self.registry
        )
        
        self.pdf_file_size = Histogram(
            name='financial_pdf_file_size_bytes',
            documentation='PDF file size in bytes',
            labelnames=['report_type'],
            buckets=[10000, 50000, 100000, 500000, 1000000, 5000000],
            registry=self.registry
        )
        
        self.pdf_download_rate = Gauge(
            name='financial_pdf_download_rate',
            documentation='Rate of PDF downloads after generation',
            labelnames=['report_type', 'time_period'],
            registry=self.registry
        )
    
    def _init_voice_interface_metrics(self):
        """Initialize voice interface metrics"""
        
        self.voice_sessions = Counter(
            name='voice_interface_sessions_total',
            documentation='Total voice interface sessions',
            labelnames=['session_type', 'language', 'device_type'],
            registry=self.registry
        )
        
        self.voice_response_time = Histogram(
            name='voice_response_time_seconds',
            documentation='Voice interface response time',
            labelnames=['interaction_type'],
            buckets=[0.5, 1, 2, 5, 10, 15, 30],
            registry=self.registry
        )
        
        self.speech_recognition_accuracy = Gauge(
            name='voice_speech_recognition_accuracy',
            documentation='Speech-to-text accuracy rate',
            labelnames=['language', 'audio_quality'],
            registry=self.registry
        )
        
        self.voice_commands_processed = Counter(
            name='voice_commands_processed_total',
            documentation='Voice commands processed',
            labelnames=['command_type', 'success_status'],
            registry=self.registry
        )
    
    def _init_banking_integration_metrics(self):
        """Initialize banking integration metrics"""
        
        self.banking_api_requests = Counter(
            name='banking_api_requests_total',
            documentation='Banking API requests',
            labelnames=['provider', 'request_type', 'status'],
            registry=self.registry
        )
        
        self.banking_connection_health = Gauge(
            name='banking_connection_health_score',
            documentation='Banking connection health score',
            labelnames=['provider', 'connection_type'],
            registry=self.registry
        )
        
        self.transaction_sync_latency = Histogram(
            name='banking_transaction_sync_duration_seconds',
            documentation='Transaction synchronization time',
            labelnames=['provider', 'account_type'],
            buckets=[1, 5, 10, 30, 60, 120, 300],
            registry=self.registry
        )
        
        self.accounts_connected = Gauge(
            name='banking_accounts_connected_total',
            documentation='Number of connected bank accounts',
            labelnames=['provider', 'account_type'],
            registry=self.registry
        )
    
    def _init_performance_metrics(self):
        """Initialize application performance metrics"""
        
        self.api_response_time = Histogram(
            name='financial_api_response_time_seconds',
            documentation='API endpoint response times',
            labelnames=['endpoint', 'method', 'status_code'],
            buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10],
            registry=self.registry
        )
        
        self.database_query_duration = Histogram(
            name='financial_database_query_duration_seconds',
            documentation='Database query execution time',
            labelnames=['query_type', 'table_name'],
            buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1, 5],
            registry=self.registry
        )
        
        self.cache_hit_rate = Gauge(
            name='financial_cache_hit_rate',
            documentation='Cache hit rate percentage',
            labelnames=['cache_type', 'data_type'],
            registry=self.registry
        )
        
        self.memory_usage = Gauge(
            name='financial_app_memory_usage_bytes',
            documentation='Application memory usage',
            labelnames=['component', 'process_type'],
            registry=self.registry
        )
    
    def _init_business_kpi_metrics(self):
        """Initialize key business performance indicators"""
        
        self.monthly_recurring_revenue = Gauge(
            name='financial_monthly_recurring_revenue_dollars',
            documentation='Monthly recurring revenue',
            labelnames=['subscription_tier', 'region'],
            registry=self.registry
        )
        
        self.customer_acquisition_cost = Gauge(
            name='financial_customer_acquisition_cost_dollars',
            documentation='Customer acquisition cost',
            labelnames=['acquisition_channel', 'user_tier'],
            registry=self.registry
        )
        
        self.customer_lifetime_value = Gauge(
            name='financial_customer_lifetime_value_dollars',
            documentation='Customer lifetime value',
            labelnames=['user_segment', 'cohort_month'],
            registry=self.registry
        )
        
        self.churn_rate = Gauge(
            name='financial_churn_rate_percent',
            documentation='Customer churn rate',
            labelnames=['user_tier', 'time_period'],
            registry=self.registry
        )
        
        self.net_promoter_score = Gauge(
            name='financial_net_promoter_score',
            documentation='Net Promoter Score',
            labelnames=['user_segment', 'survey_period'],
            registry=self.registry
        )
    
    # Convenience methods for recording metrics
    
    def record_simulation(self, simulation_type: SimulationType, duration: float, 
                         iterations: int, portfolio_value: float, status: str = "success",
                         user_tier: str = "free", complexity: str = "medium"):
        """Record a financial simulation event"""
        
        self.simulations_total.labels(
            simulation_type=simulation_type.value,
            user_tier=user_tier,
            result_status=status
        ).inc()
        
        self.simulation_duration.labels(
            simulation_type=simulation_type.value,
            complexity_level=complexity
        ).observe(duration)
        
        self.simulation_iterations.labels(
            simulation_type=simulation_type.value
        ).observe(iterations)
        
        self.simulation_portfolio_value.labels(
            simulation_type=simulation_type.value
        ).observe(portfolio_value)
    
    def record_recommendation(self, rec_type: RecommendationType, generation_time: float,
                            confidence: float, user_segment: str = "retail",
                            model_version: str = "v1.0"):
        """Record an AI recommendation event"""
        
        confidence_level = "high" if confidence > 0.8 else "medium" if confidence > 0.6 else "low"
        
        self.recommendations_generated.labels(
            recommendation_type=rec_type.value,
            confidence_level=confidence_level,
            user_segment=user_segment
        ).inc()
        
        self.recommendation_generation_time.labels(
            recommendation_type=rec_type.value,
            model_version=model_version
        ).observe(generation_time)
        
        self.recommendation_confidence.labels(
            recommendation_type=rec_type.value
        ).observe(confidence)
    
    def record_user_action(self, action: UserActionType, user_segment: str = "retail",
                          platform: str = "web", duration: float = None):
        """Record a user action event"""
        
        self.user_actions.labels(
            action_type=action.value,
            user_segment=user_segment,
            platform=platform
        ).inc()
        
        if duration is not None:
            feature_map = {
                UserActionType.SIMULATION_RUN: "simulation",
                UserActionType.REPORT_GENERATED: "reporting",
                UserActionType.VOICE_INTERACTION: "voice",
                UserActionType.PORTFOLIO_UPDATED: "portfolio"
            }
            
            feature = feature_map.get(action, "general")
            self.session_duration.labels(
                user_tier=user_segment,
                feature_used=feature
            ).observe(duration)
    
    def record_market_data_request(self, provider: str, data_type: str, 
                                 duration: float, status: str = "success"):
        """Record a market data API request"""
        
        self.market_data_requests.labels(
            provider=provider,
            data_type=data_type,
            status=status
        ).inc()
        
        self.market_data_latency.labels(
            provider=provider,
            data_type=data_type
        ).observe(duration)
    
    def record_pdf_generation(self, report_type: str, duration: float, 
                            file_size: int, user_tier: str = "free"):
        """Record PDF report generation"""
        
        complexity = "high" if file_size > 1000000 else "medium" if file_size > 100000 else "low"
        
        self.pdf_reports_generated.labels(
            report_type=report_type,
            template_version="v2.0",
            user_tier=user_tier
        ).inc()
        
        self.pdf_generation_duration.labels(
            report_type=report_type,
            complexity=complexity
        ).observe(duration)
        
        self.pdf_file_size.labels(
            report_type=report_type
        ).observe(file_size)
    
    def record_voice_session(self, session_type: str, response_time: float,
                           language: str = "en", device_type: str = "web"):
        """Record voice interface session"""
        
        self.voice_sessions.labels(
            session_type=session_type,
            language=language,
            device_type=device_type
        ).inc()
        
        self.voice_response_time.labels(
            interaction_type=session_type
        ).observe(response_time)
    
    def record_banking_request(self, provider: str, request_type: str,
                             duration: float, status: str = "success"):
        """Record banking integration request"""
        
        self.banking_api_requests.labels(
            provider=provider,
            request_type=request_type,
            status=status
        ).inc()
        
        if request_type == "transaction_sync":
            account_type = "checking"  # Could be parameterized
            self.transaction_sync_latency.labels(
                provider=provider,
                account_type=account_type
            ).observe(duration)
    
    @contextmanager
    def time_operation(self, operation_name: str, labels: Dict[str, str] = None):
        """Context manager to time operations"""
        
        start_time = time.time()
        try:
            yield
        finally:
            duration = time.time() - start_time
            
            # Record to appropriate metric based on operation name
            if "simulation" in operation_name:
                self.simulation_duration.labels(
                    simulation_type=labels.get("type", "unknown"),
                    complexity_level=labels.get("complexity", "medium")
                ).observe(duration)
            elif "recommendation" in operation_name:
                self.recommendation_generation_time.labels(
                    recommendation_type=labels.get("type", "unknown"),
                    model_version=labels.get("version", "v1.0")
                ).observe(duration)
            elif "api" in operation_name:
                self.api_response_time.labels(
                    endpoint=labels.get("endpoint", "unknown"),
                    method=labels.get("method", "GET"),
                    status_code=labels.get("status", "200")
                ).observe(duration)
    
    def update_business_kpis(self, mrr: float, cac: float, ltv: float, 
                           churn_rate: float, nps: float, period: str = "current"):
        """Update key business metrics"""
        
        self.monthly_recurring_revenue.labels(
            subscription_tier="all",
            region="global"
        ).set(mrr)
        
        self.customer_acquisition_cost.labels(
            acquisition_channel="all",
            user_tier="all"
        ).set(cac)
        
        self.customer_lifetime_value.labels(
            user_segment="all",
            cohort_month=period
        ).set(ltv)
        
        self.churn_rate.labels(
            user_tier="all",
            time_period=period
        ).set(churn_rate)
        
        self.net_promoter_score.labels(
            user_segment="all",
            survey_period=period
        ).set(nps)
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get a summary of key metrics for monitoring dashboards"""
        
        return {
            "simulations_per_minute": self._get_rate("financial_simulations_total", "1m"),
            "avg_simulation_duration": self._get_avg("financial_simulation_duration_seconds"),
            "recommendations_per_hour": self._get_rate("ai_recommendations_generated_total", "1h"),
            "active_users_count": self._get_current("financial_active_users_total"),
            "api_p95_response_time": self._get_percentile("financial_api_response_time_seconds", 0.95),
            "cache_hit_rate": self._get_current("financial_cache_hit_rate"),
            "pdf_generation_success_rate": self._get_success_rate("financial_pdf_reports_generated_total")
        }
    
    def _get_rate(self, metric_name: str, time_window: str) -> float:
        """Calculate rate for a counter metric (placeholder)"""
        # This would typically query your TSDB (Prometheus) for rate calculation
        return 0.0
    
    def _get_avg(self, metric_name: str) -> float:
        """Get average for a histogram metric (placeholder)"""
        return 0.0
    
    def _get_current(self, metric_name: str) -> float:
        """Get current value for a gauge metric (placeholder)"""
        return 0.0
    
    def _get_percentile(self, metric_name: str, percentile: float) -> float:
        """Get percentile for a histogram metric (placeholder)"""
        return 0.0
    
    def _get_success_rate(self, metric_name: str) -> float:
        """Calculate success rate for a counter metric (placeholder)"""
        return 0.0
    
    def export_metrics(self) -> str:
        """Export all metrics in Prometheus format"""
        return generate_latest(self.registry)

# Singleton instance for easy access
financial_metrics = FinancialPlanningMetrics()

# Decorator for automatic metric collection
def track_simulation_metrics(simulation_type: SimulationType):
    """Decorator to automatically track simulation metrics"""
    def decorator(func):
        import functools
        
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            status = "success"
            
            try:
                result = await func(*args, **kwargs)
                
                # Extract metrics from result
                iterations = kwargs.get('iterations', 1000)
                portfolio_value = kwargs.get('initial_investment', 10000)
                
                return result
            
            except Exception as e:
                status = "error"
                raise
            
            finally:
                duration = time.time() - start_time
                financial_metrics.record_simulation(
                    simulation_type=simulation_type,
                    duration=duration,
                    iterations=kwargs.get('iterations', 1000),
                    portfolio_value=kwargs.get('initial_investment', 10000),
                    status=status
                )
        
        return wrapper
    return decorator