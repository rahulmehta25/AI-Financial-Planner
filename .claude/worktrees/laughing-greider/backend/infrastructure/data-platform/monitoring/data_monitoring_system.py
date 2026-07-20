"""
Comprehensive Data Monitoring and Alerting System
Monitors data quality, pipeline health, KPIs, and system performance
"""

import os
import json
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
import threading
import time
from collections import defaultdict, deque
import statistics

import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text, MetaData
from sqlalchemy.exc import SQLAlchemyError
import requests
import psutil
from prometheus_client import Counter, Histogram, Gauge, start_http_server, CollectorRegistry
from prometheus_client.core import REGISTRY
import redis
from elasticsearch import Elasticsearch
from kafka import KafkaConsumer, KafkaProducer
import slack_sdk
from slack_sdk import WebClient as SlackWebClient
import pagerduty
from pagerduty import PagerDuty

# Airflow integration
from airflow.models import DagRun, TaskInstance
from airflow.utils.state import State

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AlertSeverity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

class MonitoringType(Enum):
    DATA_QUALITY = "data_quality"
    PIPELINE_HEALTH = "pipeline_health"
    BUSINESS_KPI = "business_kpi"
    SYSTEM_PERFORMANCE = "system_performance"
    SECURITY = "security"
    COMPLIANCE = "compliance"

class AlertChannel(Enum):
    EMAIL = "email"
    SLACK = "slack"
    PAGERDUTY = "pagerduty"
    WEBHOOK = "webhook"
    SMS = "sms"

@dataclass
class Alert:
    """Alert data structure"""
    id: str
    title: str
    description: str
    severity: AlertSeverity
    monitoring_type: MonitoringType
    timestamp: datetime
    source: str
    metric_value: Optional[float] = None
    threshold: Optional[float] = None
    tags: List[str] = None
    acknowledged: bool = False
    resolved: bool = False
    escalated: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['severity'] = self.severity.value
        result['monitoring_type'] = self.monitoring_type.value
        result['timestamp'] = self.timestamp.isoformat()
        return result

@dataclass
class Metric:
    """Metric data structure"""
    name: str
    value: float
    timestamp: datetime
    tags: Dict[str, str]
    unit: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['timestamp'] = self.timestamp.isoformat()
        return result

@dataclass
class ThresholdRule:
    """Threshold-based alerting rule"""
    metric_name: str
    operator: str  # >, <, >=, <=, ==, !=
    threshold: float
    severity: AlertSeverity
    window_minutes: int = 5
    min_samples: int = 1
    enabled: bool = True

class DataQualityMonitor:
    """Monitors data quality metrics and anomalies"""
    
    def __init__(self, postgres_engine, redis_client):
        self.postgres_engine = postgres_engine
        self.redis_client = redis_client
        self.logger = logging.getLogger(__name__)
        
        # Prometheus metrics
        self.data_quality_score = Gauge('data_quality_score', 'Data quality score by table', ['table', 'schema'])
        self.null_percentage = Gauge('data_null_percentage', 'Null percentage by column', ['table', 'column'])
        self.duplicate_count = Gauge('data_duplicate_count', 'Number of duplicate records', ['table'])
        self.freshness_hours = Gauge('data_freshness_hours', 'Data freshness in hours', ['table'])
        
    def check_data_quality(self, table_name: str, schema: str = 'public') -> Dict[str, Any]:
        """Comprehensive data quality check for a table"""
        try:
            quality_metrics = {
                'table': f"{schema}.{table_name}",
                'timestamp': datetime.now().isoformat(),
                'completeness': 0.0,
                'uniqueness': 0.0,
                'validity': 0.0,
                'freshness': 0.0,
                'overall_score': 0.0,
                'issues': []
            }
            
            # Get table metadata
            with self.postgres_engine.connect() as conn:
                # Count total records
                total_query = f"SELECT COUNT(*) as total FROM {schema}.{table_name}"
                total_result = conn.execute(text(total_query)).fetchone()
                total_records = total_result[0] if total_result else 0
                
                if total_records == 0:
                    quality_metrics['issues'].append("Table is empty")
                    return quality_metrics
                
                # Get column information
                columns_query = """
                    SELECT column_name, data_type, is_nullable 
                    FROM information_schema.columns 
                    WHERE table_schema = :schema AND table_name = :table
                """
                columns_result = conn.execute(text(columns_query), 
                                            {'schema': schema, 'table': table_name}).fetchall()
                
                columns = [{'name': col[0], 'type': col[1], 'nullable': col[2] == 'YES'} 
                          for col in columns_result]
                
                # Completeness check (null values)
                completeness_scores = []
                for column in columns:
                    null_query = f"""
                        SELECT COUNT(*) as null_count 
                        FROM {schema}.{table_name} 
                        WHERE {column['name']} IS NULL
                    """
                    null_result = conn.execute(text(null_query)).fetchone()
                    null_count = null_result[0] if null_result else 0
                    
                    null_percentage = (null_count / total_records) * 100
                    self.null_percentage.labels(table=table_name, column=column['name']).set(null_percentage)
                    
                    if not column['nullable'] and null_count > 0:
                        quality_metrics['issues'].append(f"Non-nullable column {column['name']} has {null_count} null values")
                    
                    column_completeness = 1.0 - (null_count / total_records)
                    completeness_scores.append(column_completeness)
                
                quality_metrics['completeness'] = statistics.mean(completeness_scores) if completeness_scores else 0.0
                
                # Uniqueness check (duplicates)
                # Check for completely duplicate rows
                duplicate_query = f"""
                    SELECT COUNT(*) - COUNT(DISTINCT *) as duplicate_count 
                    FROM {schema}.{table_name}
                """
                try:
                    duplicate_result = conn.execute(text(duplicate_query)).fetchone()
                    duplicate_count = duplicate_result[0] if duplicate_result else 0
                    quality_metrics['uniqueness'] = 1.0 - (duplicate_count / total_records)
                    self.duplicate_count.labels(table=table_name).set(duplicate_count)
                    
                    if duplicate_count > 0:
                        quality_metrics['issues'].append(f"Found {duplicate_count} duplicate records")
                except Exception as e:
                    # Some tables might not support DISTINCT *
                    quality_metrics['uniqueness'] = 1.0
                
                # Validity check (basic data type validation)
                validity_scores = []
                for column in columns:
                    if 'email' in column['name'].lower():
                        # Email validation
                        invalid_email_query = f"""
                            SELECT COUNT(*) as invalid_count 
                            FROM {schema}.{table_name} 
                            WHERE {column['name']} IS NOT NULL 
                            AND {column['name']} !~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{{2,}}$'
                        """
                        try:
                            invalid_result = conn.execute(text(invalid_email_query)).fetchone()
                            invalid_count = invalid_result[0] if invalid_result else 0
                            validity_score = 1.0 - (invalid_count / total_records)
                            validity_scores.append(validity_score)
                            
                            if invalid_count > 0:
                                quality_metrics['issues'].append(f"Column {column['name']} has {invalid_count} invalid email addresses")
                        except Exception:
                            validity_scores.append(1.0)  # Skip if regex not supported
                    else:
                        validity_scores.append(1.0)  # Assume valid for other columns
                
                quality_metrics['validity'] = statistics.mean(validity_scores) if validity_scores else 1.0
                
                # Freshness check (if there's a timestamp column)
                timestamp_columns = [col['name'] for col in columns 
                                   if any(term in col['name'].lower() 
                                         for term in ['created_at', 'updated_at', 'timestamp', 'date'])]
                
                if timestamp_columns:
                    freshness_query = f"""
                        SELECT EXTRACT(EPOCH FROM (NOW() - MAX({timestamp_columns[0]}))) / 3600 as hours_old
                        FROM {schema}.{table_name}
                    """
                    try:
                        freshness_result = conn.execute(text(freshness_query)).fetchone()
                        hours_old = freshness_result[0] if freshness_result else 0
                        self.freshness_hours.labels(table=table_name).set(hours_old)
                        
                        # Freshness score (100% if data is less than 1 hour old, decreasing linearly)
                        quality_metrics['freshness'] = max(0.0, 1.0 - (hours_old / 24))  # 24 hours = 0% freshness
                        
                        if hours_old > 24:
                            quality_metrics['issues'].append(f"Data is {hours_old:.1f} hours old")
                    except Exception:
                        quality_metrics['freshness'] = 1.0
                else:
                    quality_metrics['freshness'] = 1.0  # No timestamp column
                
                # Calculate overall score
                quality_metrics['overall_score'] = (
                    quality_metrics['completeness'] * 0.3 +
                    quality_metrics['uniqueness'] * 0.25 +
                    quality_metrics['validity'] * 0.25 +
                    quality_metrics['freshness'] * 0.2
                )
                
                # Update Prometheus metric
                self.data_quality_score.labels(table=table_name, schema=schema).set(quality_metrics['overall_score'])
                
                # Cache results in Redis
                cache_key = f"data_quality:{schema}.{table_name}"
                self.redis_client.setex(cache_key, 3600, json.dumps(quality_metrics))  # Cache for 1 hour
                
            return quality_metrics
            
        except Exception as e:
            self.logger.error(f"Error checking data quality for {schema}.{table_name}: {str(e)}")
            return {
                'table': f"{schema}.{table_name}",
                'timestamp': datetime.now().isoformat(),
                'error': str(e),
                'overall_score': 0.0
            }
    
    def detect_anomalies(self, table_name: str, schema: str = 'public') -> List[Dict[str, Any]]:
        """Detect data anomalies using statistical methods"""
        anomalies = []
        
        try:
            with self.postgres_engine.connect() as conn:
                # Get numeric columns for anomaly detection
                numeric_columns_query = """
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_schema = :schema AND table_name = :table 
                    AND data_type IN ('integer', 'bigint', 'numeric', 'real', 'double precision')
                """
                numeric_columns = conn.execute(text(numeric_columns_query), 
                                             {'schema': schema, 'table': table_name}).fetchall()
                
                for col in numeric_columns:
                    column_name = col[0]
                    
                    # Get basic statistics
                    stats_query = f"""
                        SELECT 
                            AVG({column_name}) as mean,
                            STDDEV({column_name}) as stddev,
                            MIN({column_name}) as min_val,
                            MAX({column_name}) as max_val,
                            COUNT(*) as total_count,
                            COUNT({column_name}) as non_null_count
                        FROM {schema}.{table_name}
                        WHERE {column_name} IS NOT NULL
                    """
                    
                    stats_result = conn.execute(text(stats_query)).fetchone()
                    if not stats_result:
                        continue
                    
                    mean, stddev, min_val, max_val, total_count, non_null_count = stats_result
                    
                    if stddev and mean:
                        # Z-score based outlier detection
                        outlier_query = f"""
                            SELECT COUNT(*) as outlier_count
                            FROM {schema}.{table_name}
                            WHERE {column_name} IS NOT NULL
                            AND ABS(({column_name} - {mean}) / {stddev}) > 3
                        """
                        
                        outlier_result = conn.execute(text(outlier_query)).fetchone()
                        outlier_count = outlier_result[0] if outlier_result else 0
                        
                        if outlier_count > 0:
                            outlier_percentage = (outlier_count / non_null_count) * 100
                            anomalies.append({
                                'type': 'statistical_outlier',
                                'column': column_name,
                                'outlier_count': outlier_count,
                                'outlier_percentage': outlier_percentage,
                                'severity': 'medium' if outlier_percentage > 5 else 'low'
                            })
            
        except Exception as e:
            self.logger.error(f"Error detecting anomalies in {schema}.{table_name}: {str(e)}")
        
        return anomalies

class PipelineHealthMonitor:
    """Monitors Airflow pipeline health and performance"""
    
    def __init__(self, airflow_db_engine):
        self.airflow_db_engine = airflow_db_engine
        self.logger = logging.getLogger(__name__)
        
        # Prometheus metrics
        self.pipeline_success_rate = Gauge('pipeline_success_rate', 'Pipeline success rate', ['dag_id'])
        self.pipeline_duration = Histogram('pipeline_duration_seconds', 'Pipeline duration', ['dag_id'])
        self.failed_tasks = Counter('pipeline_failed_tasks_total', 'Failed tasks count', ['dag_id', 'task_id'])
        self.pipeline_sla_violations = Counter('pipeline_sla_violations_total', 'SLA violations', ['dag_id'])
    
    def check_pipeline_health(self, dag_id: str = None, hours: int = 24) -> Dict[str, Any]:
        """Check health of Airflow pipelines"""
        try:
            health_report = {
                'timestamp': datetime.now().isoformat(),
                'overall_health': 'healthy',
                'pipelines': [],
                'summary': {
                    'total_pipelines': 0,
                    'healthy_pipelines': 0,
                    'degraded_pipelines': 0,
                    'failed_pipelines': 0,
                    'avg_success_rate': 0.0
                }
            }
            
            # Query DAG runs from the last N hours
            with self.airflow_db_engine.connect() as conn:
                since_time = datetime.now() - timedelta(hours=hours)
                
                # Base query for DAG runs
                dag_filter = f"AND dag_id = '{dag_id}'" if dag_id else ""
                
                dag_runs_query = f"""
                    SELECT 
                        dag_id,
                        state,
                        start_date,
                        end_date,
                        execution_date,
                        run_id
                    FROM dag_run 
                    WHERE start_date >= '{since_time.isoformat()}'
                    {dag_filter}
                    ORDER BY dag_id, start_date DESC
                """
                
                dag_runs = conn.execute(text(dag_runs_query)).fetchall()
                
                # Group by DAG ID
                dag_stats = defaultdict(lambda: {
                    'runs': [],
                    'success_count': 0,
                    'failed_count': 0,
                    'running_count': 0,
                    'total_duration': 0,
                    'avg_duration': 0,
                    'success_rate': 0
                })
                
                for run in dag_runs:
                    dag_id, state, start_date, end_date, execution_date, run_id = run
                    
                    dag_stats[dag_id]['runs'].append({
                        'state': state,
                        'start_date': start_date.isoformat() if start_date else None,
                        'end_date': end_date.isoformat() if end_date else None,
                        'execution_date': execution_date.isoformat() if execution_date else None,
                        'run_id': run_id
                    })
                    
                    if state == 'success':
                        dag_stats[dag_id]['success_count'] += 1
                        if start_date and end_date:
                            duration = (end_date - start_date).total_seconds()
                            dag_stats[dag_id]['total_duration'] += duration
                            self.pipeline_duration.labels(dag_id=dag_id).observe(duration)
                    elif state == 'failed':
                        dag_stats[dag_id]['failed_count'] += 1
                        self.failed_tasks.labels(dag_id=dag_id, task_id='unknown').inc()
                    elif state == 'running':
                        dag_stats[dag_id]['running_count'] += 1
                
                # Calculate pipeline health metrics
                total_success_rates = []
                
                for dag_id, stats in dag_stats.items():
                    total_runs = len(stats['runs'])
                    if total_runs > 0:
                        stats['success_rate'] = stats['success_count'] / total_runs
                        total_success_rates.append(stats['success_rate'])
                        
                        if stats['success_count'] > 0:
                            stats['avg_duration'] = stats['total_duration'] / stats['success_count']
                        
                        # Update Prometheus metrics
                        self.pipeline_success_rate.labels(dag_id=dag_id).set(stats['success_rate'])
                        
                        # Determine health status
                        if stats['success_rate'] >= 0.95:
                            health_status = 'healthy'
                            health_report['summary']['healthy_pipelines'] += 1
                        elif stats['success_rate'] >= 0.80:
                            health_status = 'degraded'
                            health_report['summary']['degraded_pipelines'] += 1
                        else:
                            health_status = 'failed'
                            health_report['summary']['failed_pipelines'] += 1
                        
                        pipeline_health = {
                            'dag_id': dag_id,
                            'health_status': health_status,
                            'total_runs': total_runs,
                            'success_rate': stats['success_rate'],
                            'avg_duration_seconds': stats['avg_duration'],
                            'recent_runs': stats['runs'][:5]  # Last 5 runs
                        }
                        
                        health_report['pipelines'].append(pipeline_health)
                
                # Calculate summary metrics
                health_report['summary']['total_pipelines'] = len(dag_stats)
                if total_success_rates:
                    health_report['summary']['avg_success_rate'] = statistics.mean(total_success_rates)
                
                # Determine overall health
                if health_report['summary']['failed_pipelines'] > 0:
                    health_report['overall_health'] = 'critical'
                elif health_report['summary']['degraded_pipelines'] > 0:
                    health_report['overall_health'] = 'degraded'
                else:
                    health_report['overall_health'] = 'healthy'
            
            return health_report
            
        except Exception as e:
            self.logger.error(f"Error checking pipeline health: {str(e)}")
            return {
                'timestamp': datetime.now().isoformat(),
                'error': str(e),
                'overall_health': 'unknown'
            }
    
    def get_failed_tasks(self, dag_id: str = None, hours: int = 24) -> List[Dict[str, Any]]:
        """Get details of failed tasks"""
        failed_tasks = []
        
        try:
            with self.airflow_db_engine.connect() as conn:
                since_time = datetime.now() - timedelta(hours=hours)
                dag_filter = f"AND ti.dag_id = '{dag_id}'" if dag_id else ""
                
                failed_tasks_query = f"""
                    SELECT 
                        ti.dag_id,
                        ti.task_id,
                        ti.execution_date,
                        ti.start_date,
                        ti.end_date,
                        ti.state,
                        ti.try_number,
                        ti.log_filepath
                    FROM task_instance ti
                    WHERE ti.state = 'failed'
                    AND ti.start_date >= '{since_time.isoformat()}'
                    {dag_filter}
                    ORDER BY ti.start_date DESC
                    LIMIT 100
                """
                
                results = conn.execute(text(failed_tasks_query)).fetchall()
                
                for result in results:
                    dag_id, task_id, execution_date, start_date, end_date, state, try_number, log_filepath = result
                    
                    failed_task = {
                        'dag_id': dag_id,
                        'task_id': task_id,
                        'execution_date': execution_date.isoformat() if execution_date else None,
                        'start_date': start_date.isoformat() if start_date else None,
                        'end_date': end_date.isoformat() if end_date else None,
                        'state': state,
                        'try_number': try_number,
                        'log_filepath': log_filepath
                    }
                    
                    failed_tasks.append(failed_task)
        
        except Exception as e:
            self.logger.error(f"Error getting failed tasks: {str(e)}")
        
        return failed_tasks

class BusinessKPIMonitor:
    """Monitors business KPIs and metrics"""
    
    def __init__(self, postgres_engine, redis_client):
        self.postgres_engine = postgres_engine
        self.redis_client = redis_client
        self.logger = logging.getLogger(__name__)
        
        # Prometheus metrics for business KPIs
        self.active_users = Gauge('business_active_users_total', 'Total active users')
        self.daily_transactions = Gauge('business_daily_transactions_total', 'Daily transactions count')
        self.revenue = Gauge('business_revenue_usd', 'Revenue in USD', ['period'])
        self.portfolio_value = Gauge('business_portfolio_value_total', 'Total portfolio value')
        self.goal_completion_rate = Gauge('business_goal_completion_rate', 'Goal completion rate')
    
    def calculate_business_metrics(self) -> Dict[str, Any]:
        """Calculate key business metrics"""
        try:
            metrics = {
                'timestamp': datetime.now().isoformat(),
                'user_metrics': {},
                'transaction_metrics': {},
                'portfolio_metrics': {},
                'goal_metrics': {},
                'financial_metrics': {}
            }
            
            with self.postgres_engine.connect() as conn:
                # User metrics
                user_metrics_query = """
                    SELECT 
                        COUNT(*) as total_users,
                        COUNT(CASE WHEN last_login >= NOW() - INTERVAL '7 days' THEN 1 END) as weekly_active_users,
                        COUNT(CASE WHEN last_login >= NOW() - INTERVAL '30 days' THEN 1 END) as monthly_active_users,
                        COUNT(CASE WHEN created_at >= NOW() - INTERVAL '7 days' THEN 1 END) as new_users_week
                    FROM financial_planning.users
                """
                
                user_result = conn.execute(text(user_metrics_query)).fetchone()
                if user_result:
                    metrics['user_metrics'] = {
                        'total_users': user_result[0],
                        'weekly_active_users': user_result[1],
                        'monthly_active_users': user_result[2],
                        'new_users_this_week': user_result[3]
                    }
                    
                    self.active_users.set(user_result[2])  # Monthly active users
                
                # Transaction metrics
                transaction_metrics_query = """
                    SELECT 
                        COUNT(*) as total_transactions,
                        COUNT(CASE WHEN date >= CURRENT_DATE THEN 1 END) as daily_transactions,
                        COUNT(CASE WHEN date >= CURRENT_DATE - INTERVAL '7 days' THEN 1 END) as weekly_transactions,
                        SUM(amount) as total_amount,
                        AVG(amount) as avg_transaction_amount
                    FROM financial_planning.transactions
                    WHERE date >= CURRENT_DATE - INTERVAL '30 days'
                """
                
                transaction_result = conn.execute(text(transaction_metrics_query)).fetchone()
                if transaction_result:
                    metrics['transaction_metrics'] = {
                        'total_transactions_30d': transaction_result[0],
                        'daily_transactions': transaction_result[1],
                        'weekly_transactions': transaction_result[2],
                        'total_amount_30d': float(transaction_result[3]) if transaction_result[3] else 0,
                        'avg_transaction_amount': float(transaction_result[4]) if transaction_result[4] else 0
                    }
                    
                    self.daily_transactions.set(transaction_result[1])
                
                # Portfolio metrics
                portfolio_metrics_query = """
                    SELECT 
                        COUNT(DISTINCT user_id) as users_with_portfolios,
                        SUM(current_value) as total_portfolio_value,
                        AVG(current_value) as avg_portfolio_value,
                        SUM(CASE WHEN performance_7d > 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as positive_performance_rate
                    FROM financial_planning.portfolios
                    WHERE is_active = true
                """
                
                portfolio_result = conn.execute(text(portfolio_metrics_query)).fetchone()
                if portfolio_result:
                    metrics['portfolio_metrics'] = {
                        'users_with_portfolios': portfolio_result[0],
                        'total_portfolio_value': float(portfolio_result[1]) if portfolio_result[1] else 0,
                        'avg_portfolio_value': float(portfolio_result[2]) if portfolio_result[2] else 0,
                        'positive_performance_rate': float(portfolio_result[3]) if portfolio_result[3] else 0
                    }
                    
                    self.portfolio_value.set(metrics['portfolio_metrics']['total_portfolio_value'])
                
                # Goal metrics
                goal_metrics_query = """
                    SELECT 
                        COUNT(*) as total_goals,
                        COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_goals,
                        COUNT(CASE WHEN status = 'active' THEN 1 END) as active_goals,
                        AVG(progress_percentage) as avg_progress,
                        COUNT(CASE WHEN target_date < CURRENT_DATE AND status != 'completed' THEN 1 END) as overdue_goals
                    FROM financial_planning.financial_goals
                """
                
                goal_result = conn.execute(text(goal_metrics_query)).fetchone()
                if goal_result:
                    total_goals = goal_result[0]
                    completed_goals = goal_result[1]
                    completion_rate = (completed_goals / total_goals * 100) if total_goals > 0 else 0
                    
                    metrics['goal_metrics'] = {
                        'total_goals': total_goals,
                        'completed_goals': completed_goals,
                        'active_goals': goal_result[2],
                        'avg_progress': float(goal_result[3]) if goal_result[3] else 0,
                        'overdue_goals': goal_result[4],
                        'completion_rate': completion_rate
                    }
                    
                    self.goal_completion_rate.set(completion_rate / 100)
                
                # Financial health metrics
                financial_health_query = """
                    SELECT 
                        AVG(savings_rate) as avg_savings_rate,
                        AVG(debt_to_income_ratio) as avg_debt_ratio,
                        COUNT(CASE WHEN emergency_fund_months >= 6 THEN 1 END) * 100.0 / COUNT(*) as emergency_fund_adequate_rate
                    FROM financial_planning.user_financial_health
                    WHERE updated_at >= NOW() - INTERVAL '30 days'
                """
                
                financial_result = conn.execute(text(financial_health_query)).fetchone()
                if financial_result:
                    metrics['financial_metrics'] = {
                        'avg_savings_rate': float(financial_result[0]) if financial_result[0] else 0,
                        'avg_debt_ratio': float(financial_result[1]) if financial_result[1] else 0,
                        'emergency_fund_adequate_rate': float(financial_result[2]) if financial_result[2] else 0
                    }
            
            # Cache metrics in Redis
            cache_key = "business_metrics:latest"
            self.redis_client.setex(cache_key, 300, json.dumps(metrics))  # Cache for 5 minutes
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error calculating business metrics: {str(e)}")
            return {
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            }

class AlertManager:
    """Manages alerts and notifications"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Alert storage
        self.active_alerts = {}
        self.alert_history = deque(maxlen=1000)
        
        # Notification clients
        self.setup_notification_clients()
        
        # Threshold rules
        self.threshold_rules = self.load_threshold_rules()
        
        # Prometheus metrics
        self.alerts_total = Counter('alerts_total', 'Total alerts generated', ['severity', 'type'])
        self.alerts_resolved = Counter('alerts_resolved_total', 'Total alerts resolved', ['severity', 'type'])
        
    def setup_notification_clients(self):
        """Setup notification service clients"""
        try:
            # Slack client
            if self.config.get('slack', {}).get('token'):
                self.slack_client = SlackWebClient(token=self.config['slack']['token'])
            else:
                self.slack_client = None
            
            # PagerDuty client
            if self.config.get('pagerduty', {}).get('api_key'):
                self.pagerduty_client = PagerDuty(api_key=self.config['pagerduty']['api_key'])
            else:
                self.pagerduty_client = None
            
            # Email settings
            self.email_config = self.config.get('email', {})
            
        except Exception as e:
            self.logger.error(f"Error setting up notification clients: {str(e)}")
    
    def load_threshold_rules(self) -> List[ThresholdRule]:
        """Load alerting threshold rules"""
        rules = []
        
        # Default rules
        default_rules = [
            # Data quality rules
            ThresholdRule('data_quality_score', '<', 0.8, AlertSeverity.HIGH),
            ThresholdRule('data_null_percentage', '>', 20.0, AlertSeverity.MEDIUM),
            ThresholdRule('data_freshness_hours', '>', 24.0, AlertSeverity.MEDIUM),
            
            # Pipeline health rules
            ThresholdRule('pipeline_success_rate', '<', 0.95, AlertSeverity.HIGH),
            ThresholdRule('pipeline_duration_seconds', '>', 3600, AlertSeverity.MEDIUM),
            
            # Business KPI rules
            ThresholdRule('business_goal_completion_rate', '<', 0.5, AlertSeverity.MEDIUM),
            ThresholdRule('business_active_users_total', '<', 100, AlertSeverity.LOW),
            
            # System performance rules
            ThresholdRule('system_cpu_usage', '>', 80.0, AlertSeverity.HIGH),
            ThresholdRule('system_memory_usage', '>', 85.0, AlertSeverity.HIGH),
            ThresholdRule('system_disk_usage', '>', 90.0, AlertSeverity.CRITICAL)
        ]
        
        rules.extend(default_rules)
        
        # Load custom rules from config
        custom_rules = self.config.get('threshold_rules', [])
        for rule_config in custom_rules:
            try:
                rule = ThresholdRule(
                    metric_name=rule_config['metric_name'],
                    operator=rule_config['operator'],
                    threshold=rule_config['threshold'],
                    severity=AlertSeverity(rule_config['severity']),
                    window_minutes=rule_config.get('window_minutes', 5),
                    min_samples=rule_config.get('min_samples', 1),
                    enabled=rule_config.get('enabled', True)
                )
                rules.append(rule)
            except Exception as e:
                self.logger.warning(f"Invalid threshold rule configuration: {str(e)}")
        
        return rules
    
    def create_alert(self, title: str, description: str, severity: AlertSeverity, 
                    monitoring_type: MonitoringType, source: str, 
                    metric_value: float = None, threshold: float = None,
                    tags: List[str] = None) -> Alert:
        """Create a new alert"""
        alert_id = f"{source}_{int(datetime.now().timestamp())}"
        
        alert = Alert(
            id=alert_id,
            title=title,
            description=description,
            severity=severity,
            monitoring_type=monitoring_type,
            timestamp=datetime.now(),
            source=source,
            metric_value=metric_value,
            threshold=threshold,
            tags=tags or []
        )
        
        # Store active alert
        self.active_alerts[alert_id] = alert
        self.alert_history.append(alert)
        
        # Update metrics
        self.alerts_total.labels(severity=severity.value, type=monitoring_type.value).inc()
        
        # Send notifications
        self.send_notifications(alert)
        
        self.logger.info(f"Created alert: {alert.title} (Severity: {alert.severity.value})")
        
        return alert
    
    def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an active alert"""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.resolved = True
            
            # Update metrics
            self.alerts_resolved.labels(severity=alert.severity.value, type=alert.monitoring_type.value).inc()
            
            # Remove from active alerts
            del self.active_alerts[alert_id]
            
            self.logger.info(f"Resolved alert: {alert.title}")
            return True
        
        return False
    
    def send_notifications(self, alert: Alert):
        """Send alert notifications through configured channels"""
        try:
            # Determine notification channels based on severity
            channels = self.get_notification_channels(alert.severity)
            
            for channel in channels:
                if channel == AlertChannel.EMAIL and self.email_config:
                    self.send_email_notification(alert)
                elif channel == AlertChannel.SLACK and self.slack_client:
                    self.send_slack_notification(alert)
                elif channel == AlertChannel.PAGERDUTY and self.pagerduty_client:
                    self.send_pagerduty_notification(alert)
                elif channel == AlertChannel.WEBHOOK:
                    self.send_webhook_notification(alert)
        
        except Exception as e:
            self.logger.error(f"Error sending notifications for alert {alert.id}: {str(e)}")
    
    def get_notification_channels(self, severity: AlertSeverity) -> List[AlertChannel]:
        """Get notification channels based on alert severity"""
        if severity == AlertSeverity.CRITICAL:
            return [AlertChannel.EMAIL, AlertChannel.SLACK, AlertChannel.PAGERDUTY]
        elif severity == AlertSeverity.HIGH:
            return [AlertChannel.EMAIL, AlertChannel.SLACK]
        elif severity == AlertSeverity.MEDIUM:
            return [AlertChannel.SLACK]
        else:
            return [AlertChannel.EMAIL]
    
    def send_email_notification(self, alert: Alert):
        """Send email notification"""
        try:
            if not self.email_config:
                return
            
            msg = MimeMultipart()
            msg['From'] = self.email_config['from_address']
            msg['To'] = ', '.join(self.email_config['to_addresses'])
            msg['Subject'] = f"[{alert.severity.value.upper()}] {alert.title}"
            
            body = f"""
            Alert Details:
            - Title: {alert.title}
            - Description: {alert.description}
            - Severity: {alert.severity.value}
            - Type: {alert.monitoring_type.value}
            - Source: {alert.source}
            - Timestamp: {alert.timestamp}
            """
            
            if alert.metric_value is not None:
                body += f"- Metric Value: {alert.metric_value}"
            if alert.threshold is not None:
                body += f"- Threshold: {alert.threshold}"
            
            msg.attach(MimeText(body, 'plain'))
            
            server = smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port'])
            if self.email_config.get('use_tls'):
                server.starttls()
            if self.email_config.get('username'):
                server.login(self.email_config['username'], self.email_config['password'])
            
            server.send_message(msg)
            server.quit()
            
            self.logger.info(f"Sent email notification for alert {alert.id}")
            
        except Exception as e:
            self.logger.error(f"Failed to send email notification: {str(e)}")
    
    def send_slack_notification(self, alert: Alert):
        """Send Slack notification"""
        try:
            if not self.slack_client:
                return
            
            color = {
                AlertSeverity.CRITICAL: "#FF0000",
                AlertSeverity.HIGH: "#FF6600",
                AlertSeverity.MEDIUM: "#FFCC00",
                AlertSeverity.LOW: "#00FF00",
                AlertSeverity.INFO: "#0066FF"
            }.get(alert.severity, "#808080")
            
            message = {
                "text": f"Alert: {alert.title}",
                "attachments": [
                    {
                        "color": color,
                        "fields": [
                            {
                                "title": "Severity",
                                "value": alert.severity.value.upper(),
                                "short": True
                            },
                            {
                                "title": "Type",
                                "value": alert.monitoring_type.value,
                                "short": True
                            },
                            {
                                "title": "Source",
                                "value": alert.source,
                                "short": True
                            },
                            {
                                "title": "Description",
                                "value": alert.description,
                                "short": False
                            }
                        ],
                        "ts": int(alert.timestamp.timestamp())
                    }
                ]
            }
            
            if alert.metric_value is not None and alert.threshold is not None:
                message["attachments"][0]["fields"].append({
                    "title": "Metric",
                    "value": f"{alert.metric_value} (threshold: {alert.threshold})",
                    "short": True
                })
            
            self.slack_client.chat_postMessage(
                channel=self.config['slack']['channel'],
                **message
            )
            
            self.logger.info(f"Sent Slack notification for alert {alert.id}")
            
        except Exception as e:
            self.logger.error(f"Failed to send Slack notification: {str(e)}")
    
    def send_pagerduty_notification(self, alert: Alert):
        """Send PagerDuty notification"""
        try:
            if not self.pagerduty_client or alert.severity not in [AlertSeverity.CRITICAL, AlertSeverity.HIGH]:
                return
            
            incident_data = {
                "incident": {
                    "type": "incident",
                    "title": alert.title,
                    "service": {
                        "id": self.config['pagerduty']['service_id'],
                        "type": "service_reference"
                    },
                    "priority": {
                        "id": self.config['pagerduty'].get('priority_id'),
                        "type": "priority_reference"
                    } if self.config['pagerduty'].get('priority_id') else None,
                    "body": {
                        "type": "incident_body",
                        "details": alert.description
                    }
                }
            }
            
            # Remove None values
            incident_data = {k: v for k, v in incident_data["incident"].items() if v is not None}
            
            response = self.pagerduty_client.incidents.create(data={"incident": incident_data})
            
            self.logger.info(f"Sent PagerDuty notification for alert {alert.id}")
            
        except Exception as e:
            self.logger.error(f"Failed to send PagerDuty notification: {str(e)}")
    
    def send_webhook_notification(self, alert: Alert):
        """Send webhook notification"""
        try:
            webhook_url = self.config.get('webhook', {}).get('url')
            if not webhook_url:
                return
            
            payload = alert.to_dict()
            
            response = requests.post(
                webhook_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            response.raise_for_status()
            
            self.logger.info(f"Sent webhook notification for alert {alert.id}")
            
        except Exception as e:
            self.logger.error(f"Failed to send webhook notification: {str(e)}")

class DataMonitoringSystem:
    """Main data monitoring system orchestrator"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Database connections
        self.postgres_engine = create_engine(config['postgres_connection_string'])
        self.airflow_db_engine = create_engine(config['airflow_db_connection_string'])
        
        # Redis for caching
        self.redis_client = redis.Redis(
            host=config.get('redis_host', 'localhost'),
            port=config.get('redis_port', 6379),
            db=config.get('redis_db', 0)
        )
        
        # Elasticsearch for logging
        self.es_client = Elasticsearch(config.get('elasticsearch_url', 'http://localhost:9200'))
        
        # Initialize monitoring components
        self.data_quality_monitor = DataQualityMonitor(self.postgres_engine, self.redis_client)
        self.pipeline_health_monitor = PipelineHealthMonitor(self.airflow_db_engine)
        self.business_kpi_monitor = BusinessKPIMonitor(self.postgres_engine, self.redis_client)
        self.alert_manager = AlertManager(config.get('alerting', {}))
        
        # Monitoring state
        self.running = False
        self.monitoring_threads = []
        
        # Start Prometheus metrics server
        if config.get('prometheus_port'):
            start_http_server(config['prometheus_port'])
            self.logger.info(f"Prometheus metrics server started on port {config['prometheus_port']}")
    
    def start_monitoring(self):
        """Start all monitoring threads"""
        self.running = True
        
        # Start monitoring threads
        threads = [
            threading.Thread(target=self.monitor_data_quality, daemon=True),
            threading.Thread(target=self.monitor_pipeline_health, daemon=True),
            threading.Thread(target=self.monitor_business_kpis, daemon=True),
            threading.Thread(target=self.monitor_system_performance, daemon=True),
            threading.Thread(target=self.process_alerts, daemon=True)
        ]
        
        for thread in threads:
            thread.start()
            self.monitoring_threads.append(thread)
        
        self.logger.info("Data monitoring system started")
    
    def stop_monitoring(self):
        """Stop all monitoring"""
        self.running = False
        
        for thread in self.monitoring_threads:
            thread.join(timeout=5)
        
        self.logger.info("Data monitoring system stopped")
    
    def monitor_data_quality(self):
        """Monitor data quality continuously"""
        while self.running:
            try:
                # Get list of tables to monitor
                tables_to_monitor = self.config.get('data_quality_monitoring', {}).get('tables', [])
                
                if not tables_to_monitor:
                    # Auto-discover tables if not configured
                    tables_to_monitor = self.discover_tables()
                
                for table_config in tables_to_monitor:
                    if isinstance(table_config, str):
                        schema, table = 'public', table_config
                    else:
                        schema = table_config.get('schema', 'public')
                        table = table_config['table']
                    
                    # Check data quality
                    quality_metrics = self.data_quality_monitor.check_data_quality(table, schema)
                    
                    # Check for alerts
                    if quality_metrics.get('overall_score', 1.0) < 0.8:
                        self.alert_manager.create_alert(
                            title=f"Poor Data Quality in {schema}.{table}",
                            description=f"Data quality score is {quality_metrics['overall_score']:.2f}. Issues: {', '.join(quality_metrics.get('issues', []))}",
                            severity=AlertSeverity.HIGH if quality_metrics['overall_score'] < 0.6 else AlertSeverity.MEDIUM,
                            monitoring_type=MonitoringType.DATA_QUALITY,
                            source=f"{schema}.{table}",
                            metric_value=quality_metrics['overall_score'],
                            threshold=0.8,
                            tags=['data_quality', schema, table]
                        )
                    
                    # Check for anomalies
                    anomalies = self.data_quality_monitor.detect_anomalies(table, schema)
                    for anomaly in anomalies:
                        if anomaly.get('severity') in ['high', 'medium']:
                            self.alert_manager.create_alert(
                                title=f"Data Anomaly Detected in {schema}.{table}",
                                description=f"Anomaly in column {anomaly['column']}: {anomaly['outlier_count']} outliers ({anomaly['outlier_percentage']:.1f}%)",
                                severity=AlertSeverity.MEDIUM,
                                monitoring_type=MonitoringType.DATA_QUALITY,
                                source=f"{schema}.{table}.{anomaly['column']}",
                                tags=['anomaly', 'data_quality', schema, table]
                            )
                
                # Sleep before next check
                time.sleep(self.config.get('data_quality_monitoring', {}).get('interval_seconds', 300))
                
            except Exception as e:
                self.logger.error(f"Error in data quality monitoring: {str(e)}")
                time.sleep(60)  # Wait before retrying
    
    def monitor_pipeline_health(self):
        """Monitor pipeline health continuously"""
        while self.running:
            try:
                # Check overall pipeline health
                health_report = self.pipeline_health_monitor.check_pipeline_health()
                
                # Check for unhealthy pipelines
                for pipeline in health_report.get('pipelines', []):
                    if pipeline['health_status'] == 'failed':
                        self.alert_manager.create_alert(
                            title=f"Pipeline Failed: {pipeline['dag_id']}",
                            description=f"Pipeline {pipeline['dag_id']} has a success rate of {pipeline['success_rate']:.1%}",
                            severity=AlertSeverity.CRITICAL,
                            monitoring_type=MonitoringType.PIPELINE_HEALTH,
                            source=pipeline['dag_id'],
                            metric_value=pipeline['success_rate'],
                            threshold=0.95,
                            tags=['pipeline', 'failed']
                        )
                    elif pipeline['health_status'] == 'degraded':
                        self.alert_manager.create_alert(
                            title=f"Pipeline Degraded: {pipeline['dag_id']}",
                            description=f"Pipeline {pipeline['dag_id']} has a success rate of {pipeline['success_rate']:.1%}",
                            severity=AlertSeverity.HIGH,
                            monitoring_type=MonitoringType.PIPELINE_HEALTH,
                            source=pipeline['dag_id'],
                            metric_value=pipeline['success_rate'],
                            threshold=0.95,
                            tags=['pipeline', 'degraded']
                        )
                
                # Check for failed tasks
                failed_tasks = self.pipeline_health_monitor.get_failed_tasks(hours=1)
                if len(failed_tasks) > 5:  # More than 5 failed tasks in the last hour
                    self.alert_manager.create_alert(
                        title="High Number of Task Failures",
                        description=f"{len(failed_tasks)} tasks failed in the last hour",
                        severity=AlertSeverity.HIGH,
                        monitoring_type=MonitoringType.PIPELINE_HEALTH,
                        source="task_failures",
                        metric_value=len(failed_tasks),
                        tags=['tasks', 'failures']
                    )
                
                time.sleep(self.config.get('pipeline_monitoring', {}).get('interval_seconds', 180))
                
            except Exception as e:
                self.logger.error(f"Error in pipeline health monitoring: {str(e)}")
                time.sleep(60)
    
    def monitor_business_kpis(self):
        """Monitor business KPIs continuously"""
        while self.running:
            try:
                # Calculate business metrics
                metrics = self.business_kpi_monitor.calculate_business_metrics()
                
                # Check KPI thresholds
                user_metrics = metrics.get('user_metrics', {})
                if user_metrics.get('monthly_active_users', 0) < 100:
                    self.alert_manager.create_alert(
                        title="Low Monthly Active Users",
                        description=f"Only {user_metrics['monthly_active_users']} monthly active users",
                        severity=AlertSeverity.MEDIUM,
                        monitoring_type=MonitoringType.BUSINESS_KPI,
                        source="user_metrics",
                        metric_value=user_metrics['monthly_active_users'],
                        threshold=100,
                        tags=['users', 'kpi']
                    )
                
                goal_metrics = metrics.get('goal_metrics', {})
                if goal_metrics.get('completion_rate', 0) < 50:
                    self.alert_manager.create_alert(
                        title="Low Goal Completion Rate",
                        description=f"Goal completion rate is {goal_metrics['completion_rate']:.1f}%",
                        severity=AlertSeverity.MEDIUM,
                        monitoring_type=MonitoringType.BUSINESS_KPI,
                        source="goal_metrics",
                        metric_value=goal_metrics['completion_rate'],
                        threshold=50,
                        tags=['goals', 'kpi']
                    )
                
                time.sleep(self.config.get('kpi_monitoring', {}).get('interval_seconds', 600))
                
            except Exception as e:
                self.logger.error(f"Error in business KPI monitoring: {str(e)}")
                time.sleep(60)
    
    def monitor_system_performance(self):
        """Monitor system performance continuously"""
        system_cpu_gauge = Gauge('system_cpu_usage', 'System CPU usage percentage')
        system_memory_gauge = Gauge('system_memory_usage', 'System memory usage percentage')
        system_disk_gauge = Gauge('system_disk_usage', 'System disk usage percentage')
        
        while self.running:
            try:
                # Get system metrics
                cpu_percent = psutil.cpu_percent(interval=1)
                memory_percent = psutil.virtual_memory().percent
                disk_percent = psutil.disk_usage('/').percent
                
                # Update Prometheus metrics
                system_cpu_gauge.set(cpu_percent)
                system_memory_gauge.set(memory_percent)
                system_disk_gauge.set(disk_percent)
                
                # Check thresholds
                if cpu_percent > 80:
                    self.alert_manager.create_alert(
                        title="High CPU Usage",
                        description=f"CPU usage is {cpu_percent:.1f}%",
                        severity=AlertSeverity.HIGH,
                        monitoring_type=MonitoringType.SYSTEM_PERFORMANCE,
                        source="system_cpu",
                        metric_value=cpu_percent,
                        threshold=80,
                        tags=['system', 'cpu']
                    )
                
                if memory_percent > 85:
                    self.alert_manager.create_alert(
                        title="High Memory Usage",
                        description=f"Memory usage is {memory_percent:.1f}%",
                        severity=AlertSeverity.HIGH,
                        monitoring_type=MonitoringType.SYSTEM_PERFORMANCE,
                        source="system_memory",
                        metric_value=memory_percent,
                        threshold=85,
                        tags=['system', 'memory']
                    )
                
                if disk_percent > 90:
                    self.alert_manager.create_alert(
                        title="High Disk Usage",
                        description=f"Disk usage is {disk_percent:.1f}%",
                        severity=AlertSeverity.CRITICAL,
                        monitoring_type=MonitoringType.SYSTEM_PERFORMANCE,
                        source="system_disk",
                        metric_value=disk_percent,
                        threshold=90,
                        tags=['system', 'disk']
                    )
                
                time.sleep(self.config.get('system_monitoring', {}).get('interval_seconds', 60))
                
            except Exception as e:
                self.logger.error(f"Error in system performance monitoring: {str(e)}")
                time.sleep(60)
    
    def process_alerts(self):
        """Process and manage alerts"""
        while self.running:
            try:
                # Auto-resolve alerts that are no longer applicable
                current_time = datetime.now()
                alerts_to_resolve = []
                
                for alert_id, alert in self.alert_manager.active_alerts.items():
                    # Auto-resolve alerts older than configured timeout
                    timeout_minutes = self.config.get('alerting', {}).get('auto_resolve_minutes', 60)
                    if (current_time - alert.timestamp).total_seconds() > timeout_minutes * 60:
                        alerts_to_resolve.append(alert_id)
                
                for alert_id in alerts_to_resolve:
                    self.alert_manager.resolve_alert(alert_id)
                
                time.sleep(60)  # Check every minute
                
            except Exception as e:
                self.logger.error(f"Error in alert processing: {str(e)}")
                time.sleep(60)
    
    def discover_tables(self) -> List[str]:
        """Discover tables to monitor"""
        tables = []
        
        try:
            with self.postgres_engine.connect() as conn:
                query = """
                    SELECT schemaname, tablename 
                    FROM pg_tables 
                    WHERE schemaname NOT IN ('information_schema', 'pg_catalog', 'pg_toast')
                """
                
                results = conn.execute(text(query)).fetchall()
                
                for schema, table in results:
                    tables.append(f"{schema}.{table}")
        
        except Exception as e:
            self.logger.error(f"Error discovering tables: {str(e)}")
        
        return tables
    
    def get_monitoring_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive monitoring dashboard data"""
        try:
            dashboard_data = {
                'timestamp': datetime.now().isoformat(),
                'system_health': {
                    'overall_status': 'healthy',
                    'components': {}
                },
                'active_alerts': [],
                'metrics_summary': {},
                'recent_events': []
            }
            
            # Get active alerts
            for alert in self.alert_manager.active_alerts.values():
                dashboard_data['active_alerts'].append(alert.to_dict())
            
            # Get latest business metrics
            business_metrics = self.business_kpi_monitor.calculate_business_metrics()
            dashboard_data['metrics_summary']['business'] = business_metrics
            
            # Get pipeline health
            pipeline_health = self.pipeline_health_monitor.check_pipeline_health()
            dashboard_data['metrics_summary']['pipelines'] = pipeline_health
            
            # Determine overall system health
            if len(dashboard_data['active_alerts']) > 0:
                critical_alerts = [a for a in dashboard_data['active_alerts'] if a['severity'] == 'critical']
                high_alerts = [a for a in dashboard_data['active_alerts'] if a['severity'] == 'high']
                
                if critical_alerts:
                    dashboard_data['system_health']['overall_status'] = 'critical'
                elif high_alerts:
                    dashboard_data['system_health']['overall_status'] = 'degraded'
                else:
                    dashboard_data['system_health']['overall_status'] = 'warning'
            
            return dashboard_data
            
        except Exception as e:
            self.logger.error(f"Error getting dashboard data: {str(e)}")
            return {
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            }

if __name__ == "__main__":
    # Example configuration
    config = {
        'postgres_connection_string': 'postgresql://user:password@localhost/financial_planning',
        'airflow_db_connection_string': 'postgresql://airflow:password@localhost/airflow',
        'redis_host': 'localhost',
        'redis_port': 6379,
        'elasticsearch_url': 'http://localhost:9200',
        'prometheus_port': 8080,
        'data_quality_monitoring': {
            'interval_seconds': 300,
            'tables': [
                {'schema': 'financial_planning', 'table': 'users'},
                {'schema': 'financial_planning', 'table': 'transactions'},
                {'schema': 'financial_planning', 'table': 'portfolios'}
            ]
        },
        'pipeline_monitoring': {
            'interval_seconds': 180
        },
        'kpi_monitoring': {
            'interval_seconds': 600
        },
        'system_monitoring': {
            'interval_seconds': 60
        },
        'alerting': {
            'auto_resolve_minutes': 60,
            'email': {
                'smtp_server': 'smtp.gmail.com',
                'smtp_port': 587,
                'use_tls': True,
                'username': 'alerts@company.com',
                'password': 'password',
                'from_address': 'alerts@company.com',
                'to_addresses': ['admin@company.com', 'devops@company.com']
            },
            'slack': {
                'token': 'xoxb-slack-token',
                'channel': '#alerts'
            },
            'pagerduty': {
                'api_key': 'pagerduty-api-key',
                'service_id': 'service-id'
            }
        }
    }
    
    # Initialize and start monitoring system
    monitoring_system = DataMonitoringSystem(config)
    
    try:
        print("Starting Data Monitoring System...")
        monitoring_system.start_monitoring()
        
        # Keep the main thread alive
        while True:
            # Get dashboard data every 30 seconds
            dashboard_data = monitoring_system.get_monitoring_dashboard_data()
            print(f"\nSystem Status: {dashboard_data['system_health']['overall_status']}")
            print(f"Active Alerts: {len(dashboard_data['active_alerts'])}")
            
            time.sleep(30)
            
    except KeyboardInterrupt:
        print("\nShutting down monitoring system...")
        monitoring_system.stop_monitoring()
        print("Monitoring system stopped.")