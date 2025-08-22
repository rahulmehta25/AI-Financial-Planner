"""
Advanced Data Quality Pipeline - Comprehensive data validation and monitoring
Includes schema validation, data profiling, anomaly detection, and quality scoring
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import json
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
import great_expectations as ge
from great_expectations.checkpoint.types.checkpoint_result import CheckpointResult
from great_expectations.core.batch import RuntimeBatchRequest
from great_expectations.data_context import DataContext

from airflow import DAG
from airflow.operators.python import PythonOperator, BranchPythonOperator
from airflow.operators.bash import BashOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.providers.slack.operators.slack_webhook import SlackWebhookOperator
from airflow.providers.email.operators.email import EmailOperator
from airflow.models import Variable
from airflow.utils.dates import days_ago
from airflow.utils.task_group import TaskGroup
from airflow.utils.trigger_rule import TriggerRule
from airflow.sensors.filesystem import FileSensor
from airflow.sensors.sql import SqlSensor

import logging

# Configuration
default_args = {
    'owner': 'data-quality-team',
    'depends_on_past': False,
    'start_date': days_ago(1),
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=3),
    'catchup': False,
    'max_active_runs': 1,
    'email': ['data-quality@financialplanning.com']
}

# DAG Definition
dag = DAG(
    'advanced_data_quality_pipeline',
    default_args=default_args,
    description='Advanced data quality validation and monitoring pipeline',
    schedule_interval='@hourly',  # More frequent quality checks
    catchup=False,
    tags=['data-quality', 'validation', 'monitoring'],
    doc_md=__doc__
)

# Data Quality Configuration
QUALITY_RULES = {
    'completeness': {
        'threshold': 0.95,
        'critical_columns': ['user_id', 'transaction_id', 'amount', 'date_key']
    },
    'accuracy': {
        'threshold': 0.98,
        'validation_rules': {
            'amount': {'min': -50000, 'max': 1000000},
            'balance': {'min': -10000, 'max': 10000000},
            'transaction_date': {'min_date': '2020-01-01', 'max_date': 'today+1'}
        }
    },
    'consistency': {
        'threshold': 0.99,
        'cross_table_rules': [
            {'table1': 'transactions', 'table2': 'accounts', 'key': 'account_id'},
            {'table1': 'portfolio', 'table2': 'securities', 'key': 'security_key'}
        ]
    },
    'timeliness': {
        'max_delay_hours': 2,
        'tables': ['market_data', 'transactions', 'portfolio_values']
    },
    'uniqueness': {
        'threshold': 1.0,
        'unique_columns': {
            'transactions': ['transaction_id'],
            'users': ['user_id', 'email'],
            'accounts': ['account_id']
        }
    }
}

class DataQualityValidator:
    """Advanced data quality validation using Great Expectations"""
    
    def __init__(self, postgres_conn_id: str = 'warehouse_postgres'):
        self.postgres_hook = PostgresHook(postgres_conn_id=postgres_conn_id)
        self.engine = self.postgres_hook.get_sqlalchemy_engine()
        self.logger = logging.getLogger(__name__)
        
        # Initialize Great Expectations context
        self.ge_context = DataContext()
    
    def validate_schema(self, table_name: str, expected_schema: Dict) -> Dict[str, Any]:
        """Validate table schema against expected structure"""
        try:
            # Get actual schema
            query = f"""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = '{table_name}'
                ORDER BY ordinal_position
            """
            
            actual_schema_df = pd.read_sql(query, self.engine)
            actual_schema = actual_schema_df.to_dict('records')
            
            # Compare schemas
            schema_issues = []
            expected_columns = set(expected_schema.keys())
            actual_columns = set(actual_schema_df['column_name'])
            
            # Missing columns
            missing_columns = expected_columns - actual_columns
            if missing_columns:
                schema_issues.append(f"Missing columns: {missing_columns}")
            
            # Extra columns
            extra_columns = actual_columns - expected_columns
            if extra_columns:
                schema_issues.append(f"Extra columns: {extra_columns}")
            
            # Data type mismatches
            for col in expected_columns.intersection(actual_columns):
                expected_type = expected_schema[col]['type']
                actual_type = actual_schema_df[actual_schema_df['column_name'] == col]['data_type'].iloc[0]
                if not self._compatible_types(expected_type, actual_type):
                    schema_issues.append(f"Column {col}: expected {expected_type}, got {actual_type}")
            
            return {
                'table': table_name,
                'schema_valid': len(schema_issues) == 0,
                'issues': schema_issues,
                'expected_columns': len(expected_columns),
                'actual_columns': len(actual_columns)
            }
            
        except Exception as e:
            self.logger.error(f"Schema validation failed for {table_name}: {str(e)}")
            return {
                'table': table_name,
                'schema_valid': False,
                'issues': [f"Validation error: {str(e)}"],
                'expected_columns': 0,
                'actual_columns': 0
            }
    
    def _compatible_types(self, expected: str, actual: str) -> bool:
        """Check if data types are compatible"""
        type_mappings = {
            'integer': ['integer', 'bigint', 'smallint'],
            'decimal': ['numeric', 'decimal', 'real', 'double precision'],
            'varchar': ['character varying', 'text', 'character'],
            'timestamp': ['timestamp without time zone', 'timestamp with time zone'],
            'date': ['date'],
            'boolean': ['boolean']
        }
        
        return actual.lower() in type_mappings.get(expected.lower(), [expected.lower()])
    
    def validate_completeness(self, table_name: str, columns: List[str]) -> Dict[str, Any]:
        """Check data completeness - null values, missing records"""
        try:
            results = {}
            
            for column in columns:
                query = f"""
                    SELECT 
                        COUNT(*) as total_records,
                        COUNT({column}) as non_null_records,
                        COUNT(*) - COUNT({column}) as null_records,
                        ROUND(
                            (COUNT({column})::decimal / COUNT(*)::decimal) * 100, 2
                        ) as completeness_pct
                    FROM {table_name}
                    WHERE created_at >= NOW() - INTERVAL '24 hours'
                """
                
                df = pd.read_sql(query, self.engine)
                result = df.iloc[0]
                
                results[column] = {
                    'total_records': int(result['total_records']),
                    'non_null_records': int(result['non_null_records']),
                    'null_records': int(result['null_records']),
                    'completeness_pct': float(result['completeness_pct']),
                    'meets_threshold': result['completeness_pct'] >= (QUALITY_RULES['completeness']['threshold'] * 100)
                }
            
            return {
                'table': table_name,
                'completeness_results': results,
                'overall_pass': all(r['meets_threshold'] for r in results.values())
            }
            
        except Exception as e:
            self.logger.error(f"Completeness validation failed for {table_name}: {str(e)}")
            return {
                'table': table_name,
                'completeness_results': {},
                'overall_pass': False,
                'error': str(e)
            }
    
    def validate_accuracy(self, table_name: str, column_rules: Dict) -> Dict[str, Any]:
        """Validate data accuracy using business rules"""
        try:
            results = {}
            
            for column, rules in column_rules.items():
                query = f"SELECT COUNT(*) as total_records FROM {table_name} WHERE created_at >= NOW() - INTERVAL '24 hours'"
                total_records = pd.read_sql(query, self.engine).iloc[0]['total_records']
                
                if total_records == 0:
                    results[column] = {
                        'total_records': 0,
                        'valid_records': 0,
                        'invalid_records': 0,
                        'accuracy_pct': 100.0,
                        'meets_threshold': True
                    }
                    continue
                
                # Build validation query based on rules
                conditions = []
                if 'min' in rules:
                    conditions.append(f"{column} >= {rules['min']}")
                if 'max' in rules:
                    conditions.append(f"{column} <= {rules['max']}")
                if 'pattern' in rules:
                    conditions.append(f"{column} ~ '{rules['pattern']}'")
                if 'values' in rules:
                    values_list = "','".join(rules['values'])
                    conditions.append(f"{column} IN ('{values_list}')")
                
                if conditions:
                    where_clause = " AND ".join(conditions)
                    query = f"""
                        SELECT 
                            COUNT(*) as total_records,
                            COUNT(CASE WHEN {where_clause} THEN 1 END) as valid_records,
                            COUNT(CASE WHEN NOT ({where_clause}) OR {column} IS NULL THEN 1 END) as invalid_records
                        FROM {table_name}
                        WHERE created_at >= NOW() - INTERVAL '24 hours'
                    """
                    
                    df = pd.read_sql(query, self.engine)
                    result = df.iloc[0]
                    
                    accuracy_pct = (result['valid_records'] / result['total_records']) * 100 if result['total_records'] > 0 else 100
                    
                    results[column] = {
                        'total_records': int(result['total_records']),
                        'valid_records': int(result['valid_records']),
                        'invalid_records': int(result['invalid_records']),
                        'accuracy_pct': round(accuracy_pct, 2),
                        'meets_threshold': accuracy_pct >= (QUALITY_RULES['accuracy']['threshold'] * 100)
                    }
            
            return {
                'table': table_name,
                'accuracy_results': results,
                'overall_pass': all(r['meets_threshold'] for r in results.values())
            }
            
        except Exception as e:
            self.logger.error(f"Accuracy validation failed for {table_name}: {str(e)}")
            return {
                'table': table_name,
                'accuracy_results': {},
                'overall_pass': False,
                'error': str(e)
            }
    
    def validate_uniqueness(self, table_name: str, unique_columns: List[str]) -> Dict[str, Any]:
        """Check for duplicate records"""
        try:
            results = {}
            
            for column in unique_columns:
                query = f"""
                    SELECT 
                        COUNT(*) as total_records,
                        COUNT(DISTINCT {column}) as unique_records,
                        COUNT(*) - COUNT(DISTINCT {column}) as duplicate_records
                    FROM {table_name}
                    WHERE created_at >= NOW() - INTERVAL '24 hours'
                    AND {column} IS NOT NULL
                """
                
                df = pd.read_sql(query, self.engine)
                result = df.iloc[0]
                
                uniqueness_pct = (result['unique_records'] / result['total_records']) * 100 if result['total_records'] > 0 else 100
                
                results[column] = {
                    'total_records': int(result['total_records']),
                    'unique_records': int(result['unique_records']),
                    'duplicate_records': int(result['duplicate_records']),
                    'uniqueness_pct': round(uniqueness_pct, 2),
                    'meets_threshold': uniqueness_pct >= (QUALITY_RULES['uniqueness']['threshold'] * 100)
                }
            
            return {
                'table': table_name,
                'uniqueness_results': results,
                'overall_pass': all(r['meets_threshold'] for r in results.values())
            }
            
        except Exception as e:
            self.logger.error(f"Uniqueness validation failed for {table_name}: {str(e)}")
            return {
                'table': table_name,
                'uniqueness_results': {},
                'overall_pass': False,
                'error': str(e)
            }
    
    def detect_anomalies(self, table_name: str, numeric_columns: List[str]) -> Dict[str, Any]:
        """Detect statistical anomalies using Z-score and IQR methods"""
        try:
            results = {}
            
            for column in numeric_columns:
                # Get statistical profile
                query = f"""
                    SELECT 
                        AVG({column}) as mean_val,
                        STDDEV({column}) as std_val,
                        PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY {column}) as q1,
                        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY {column}) as q3,
                        COUNT(*) as total_records
                    FROM {table_name}
                    WHERE created_at >= NOW() - INTERVAL '24 hours'
                    AND {column} IS NOT NULL
                """
                
                stats_df = pd.read_sql(query, self.engine)
                stats = stats_df.iloc[0]
                
                if stats['std_val'] is None or stats['std_val'] == 0:
                    results[column] = {
                        'method': 'N/A - No variation in data',
                        'anomalies_count': 0,
                        'anomaly_pct': 0.0,
                        'threshold_values': {}
                    }
                    continue
                
                # Z-score method (values > 3 standard deviations)
                z_score_threshold = 3
                z_lower = stats['mean_val'] - (z_score_threshold * stats['std_val'])
                z_upper = stats['mean_val'] + (z_score_threshold * stats['std_val'])
                
                # IQR method
                iqr = stats['q3'] - stats['q1']
                iqr_lower = stats['q1'] - (1.5 * iqr)
                iqr_upper = stats['q3'] + (1.5 * iqr)
                
                # Count anomalies using both methods
                anomaly_query = f"""
                    SELECT 
                        COUNT(CASE WHEN {column} < {z_lower} OR {column} > {z_upper} THEN 1 END) as z_score_anomalies,
                        COUNT(CASE WHEN {column} < {iqr_lower} OR {column} > {iqr_upper} THEN 1 END) as iqr_anomalies
                    FROM {table_name}
                    WHERE created_at >= NOW() - INTERVAL '24 hours'
                    AND {column} IS NOT NULL
                """
                
                anomaly_df = pd.read_sql(anomaly_query, self.engine)
                anomaly_result = anomaly_df.iloc[0]
                
                # Use the more conservative (lower) count
                anomalies_count = min(anomaly_result['z_score_anomalies'], anomaly_result['iqr_anomalies'])
                anomaly_pct = (anomalies_count / stats['total_records']) * 100 if stats['total_records'] > 0 else 0
                
                results[column] = {
                    'method': 'Z-Score & IQR',
                    'anomalies_count': int(anomalies_count),
                    'anomaly_pct': round(anomaly_pct, 2),
                    'threshold_values': {
                        'z_score_bounds': [float(z_lower), float(z_upper)],
                        'iqr_bounds': [float(iqr_lower), float(iqr_upper)]
                    },
                    'statistical_profile': {
                        'mean': float(stats['mean_val']),
                        'std': float(stats['std_val']),
                        'q1': float(stats['q1']),
                        'q3': float(stats['q3'])
                    }
                }
            
            return {
                'table': table_name,
                'anomaly_results': results,
                'overall_anomaly_score': sum(r['anomaly_pct'] for r in results.values()) / len(results) if results else 0
            }
            
        except Exception as e:
            self.logger.error(f"Anomaly detection failed for {table_name}: {str(e)}")
            return {
                'table': table_name,
                'anomaly_results': {},
                'overall_anomaly_score': 0,
                'error': str(e)
            }
    
    def validate_timeliness(self, table_name: str, timestamp_column: str = 'created_at') -> Dict[str, Any]:
        """Check data timeliness - how recent is the latest data"""
        try:
            query = f"""
                SELECT 
                    MAX({timestamp_column}) as latest_record,
                    COUNT(*) as total_records,
                    COUNT(CASE WHEN {timestamp_column} >= NOW() - INTERVAL '1 hour' THEN 1 END) as recent_1h,
                    COUNT(CASE WHEN {timestamp_column} >= NOW() - INTERVAL '24 hours' THEN 1 END) as recent_24h,
                    EXTRACT(EPOCH FROM (NOW() - MAX({timestamp_column})))/3600 as hours_since_latest
                FROM {table_name}
            """
            
            df = pd.read_sql(query, self.engine)
            result = df.iloc[0]
            
            max_delay_hours = QUALITY_RULES['timeliness']['max_delay_hours']
            is_timely = result['hours_since_latest'] <= max_delay_hours
            
            return {
                'table': table_name,
                'latest_record': str(result['latest_record']),
                'hours_since_latest': float(result['hours_since_latest']),
                'recent_1h_count': int(result['recent_1h']),
                'recent_24h_count': int(result['recent_24h']),
                'is_timely': is_timely,
                'meets_threshold': is_timely
            }
            
        except Exception as e:
            self.logger.error(f"Timeliness validation failed for {table_name}: {str(e)}")
            return {
                'table': table_name,
                'latest_record': None,
                'hours_since_latest': float('inf'),
                'is_timely': False,
                'meets_threshold': False,
                'error': str(e)
            }


def run_comprehensive_data_quality_check(**context):
    """
    Execute comprehensive data quality validation across all critical tables
    """
    try:
        validator = DataQualityValidator()
        
        # Define tables and their validation rules
        tables_to_validate = {
            'facts.fact_transaction': {
                'schema': {
                    'user_key': {'type': 'bigint', 'nullable': False},
                    'account_key': {'type': 'bigint', 'nullable': False},
                    'amount': {'type': 'decimal', 'nullable': False},
                    'transaction_date': {'type': 'date', 'nullable': False}
                },
                'completeness_columns': ['user_key', 'account_key', 'amount', 'transaction_id'],
                'accuracy_rules': {
                    'amount': {'min': -50000, 'max': 1000000}
                },
                'uniqueness_columns': ['transaction_id'],
                'numeric_columns': ['amount'],
                'timestamp_column': 'created_at'
            },
            'facts.fact_account_balance_daily': {
                'schema': {
                    'user_key': {'type': 'bigint', 'nullable': False},
                    'account_key': {'type': 'bigint', 'nullable': False},
                    'closing_balance': {'type': 'decimal', 'nullable': False}
                },
                'completeness_columns': ['user_key', 'account_key', 'closing_balance'],
                'accuracy_rules': {
                    'closing_balance': {'min': -10000, 'max': 10000000}
                },
                'uniqueness_columns': [],
                'numeric_columns': ['closing_balance', 'opening_balance'],
                'timestamp_column': 'created_at'
            },
            'facts.fact_market_data_intraday': {
                'schema': {
                    'security_key': {'type': 'bigint', 'nullable': False},
                    'close_price': {'type': 'decimal', 'nullable': False}
                },
                'completeness_columns': ['security_key', 'close_price'],
                'accuracy_rules': {
                    'close_price': {'min': 0.01, 'max': 100000}
                },
                'uniqueness_columns': [],
                'numeric_columns': ['close_price', 'volume'],
                'timestamp_column': 'created_at'
            }
        }
        
        overall_results = {
            'execution_time': datetime.now(),
            'tables_validated': len(tables_to_validate),
            'validation_results': {},
            'overall_quality_score': 0,
            'critical_issues': [],
            'warnings': []
        }
        
        quality_scores = []
        
        for table_name, config in tables_to_validate.items():
            logging.info(f"Validating table: {table_name}")
            
            table_results = {
                'table': table_name,
                'validations': {},
                'table_quality_score': 0,
                'critical_failures': []
            }
            
            # Schema validation
            schema_result = validator.validate_schema(table_name, config['schema'])
            table_results['validations']['schema'] = schema_result
            
            # Completeness validation
            completeness_result = validator.validate_completeness(table_name, config['completeness_columns'])
            table_results['validations']['completeness'] = completeness_result
            
            # Accuracy validation
            accuracy_result = validator.validate_accuracy(table_name, config['accuracy_rules'])
            table_results['validations']['accuracy'] = accuracy_result
            
            # Uniqueness validation (if applicable)
            if config['uniqueness_columns']:
                uniqueness_result = validator.validate_uniqueness(table_name, config['uniqueness_columns'])
                table_results['validations']['uniqueness'] = uniqueness_result
            
            # Anomaly detection
            anomaly_result = validator.detect_anomalies(table_name, config['numeric_columns'])
            table_results['validations']['anomalies'] = anomaly_result
            
            # Timeliness validation
            timeliness_result = validator.validate_timeliness(table_name, config['timestamp_column'])
            table_results['validations']['timeliness'] = timeliness_result
            
            # Calculate table quality score (0-100)
            validation_scores = []
            
            if schema_result.get('schema_valid', False):
                validation_scores.append(100)
            else:
                validation_scores.append(0)
                table_results['critical_failures'].append('Schema validation failed')
            
            if completeness_result.get('overall_pass', False):
                # Calculate weighted completeness score
                completeness_scores = [r['completeness_pct'] for r in completeness_result.get('completeness_results', {}).values()]
                validation_scores.append(sum(completeness_scores) / len(completeness_scores) if completeness_scores else 0)
            else:
                validation_scores.append(0)
                table_results['critical_failures'].append('Completeness validation failed')
            
            if accuracy_result.get('overall_pass', False):
                accuracy_scores = [r['accuracy_pct'] for r in accuracy_result.get('accuracy_results', {}).values()]
                validation_scores.append(sum(accuracy_scores) / len(accuracy_scores) if accuracy_scores else 0)
            else:
                validation_scores.append(75)  # Partial credit for accuracy issues
            
            # Anomaly score (inverse - lower anomaly % = higher score)
            anomaly_score = max(0, 100 - (anomaly_result.get('overall_anomaly_score', 0) * 10))
            validation_scores.append(anomaly_score)
            
            if timeliness_result.get('meets_threshold', False):
                validation_scores.append(100)
            else:
                validation_scores.append(50)  # Partial credit for timeliness issues
            
            table_quality_score = sum(validation_scores) / len(validation_scores) if validation_scores else 0
            table_results['table_quality_score'] = round(table_quality_score, 2)
            quality_scores.append(table_quality_score)
            
            # Identify critical issues
            if table_quality_score < 80:
                overall_results['critical_issues'].append(f"{table_name}: Quality score {table_quality_score}% (Critical: {table_results['critical_failures']})")
            elif table_quality_score < 90:
                overall_results['warnings'].append(f"{table_name}: Quality score {table_quality_score}% - needs attention")
            
            overall_results['validation_results'][table_name] = table_results
        
        # Calculate overall quality score
        overall_results['overall_quality_score'] = round(sum(quality_scores) / len(quality_scores) if quality_scores else 0, 2)
        
        # Store results in XCom for downstream tasks
        context['task_instance'].xcom_push(key='data_quality_results', value=overall_results)
        
        # Log summary
        logging.info(f"Data Quality Validation Completed:")
        logging.info(f"  - Overall Quality Score: {overall_results['overall_quality_score']}%")
        logging.info(f"  - Tables Validated: {overall_results['tables_validated']}")
        logging.info(f"  - Critical Issues: {len(overall_results['critical_issues'])}")
        logging.info(f"  - Warnings: {len(overall_results['warnings'])}")
        
        # Determine if quality check passed
        quality_threshold = 85  # Minimum acceptable quality score
        if overall_results['overall_quality_score'] >= quality_threshold and len(overall_results['critical_issues']) == 0:
            logging.info("✅ Data quality validation PASSED")
            return 'quality_passed'
        else:
            logging.warning("❌ Data quality validation FAILED")
            return 'quality_failed'
    
    except Exception as e:
        logging.error(f"Data quality validation error: {str(e)}")
        context['task_instance'].xcom_push(key='data_quality_error', value=str(e))
        raise


def store_quality_metrics(**context):
    """
    Store data quality metrics in the audit database
    """
    try:
        # Get quality results from XCom
        quality_results = context['task_instance'].xcom_pull(
            task_ids='run_comprehensive_data_quality_check',
            key='data_quality_results'
        )
        
        if not quality_results:
            logging.warning("No quality results found to store")
            return
        
        postgres_hook = PostgresHook(postgres_conn_id='warehouse_postgres')
        
        # Store overall quality metrics
        insert_query = """
            INSERT INTO audit.data_quality_metrics (
                table_name, column_name, metric_type, metric_value, 
                threshold_value, status, execution_date
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        
        records_to_insert = []
        
        for table_name, table_results in quality_results['validation_results'].items():
            # Overall table quality score
            records_to_insert.append((
                table_name, None, 'overall_quality_score', 
                table_results['table_quality_score'], 85.0,
                'pass' if table_results['table_quality_score'] >= 85 else 'fail',
                datetime.now().date()
            ))
            
            # Individual validation metrics
            validations = table_results['validations']
            
            # Completeness metrics
            if 'completeness' in validations:
                for column, result in validations['completeness'].get('completeness_results', {}).items():
                    records_to_insert.append((
                        table_name, column, 'completeness',
                        result['completeness_pct'], 95.0,
                        'pass' if result['meets_threshold'] else 'fail',
                        datetime.now().date()
                    ))
            
            # Accuracy metrics
            if 'accuracy' in validations:
                for column, result in validations['accuracy'].get('accuracy_results', {}).items():
                    records_to_insert.append((
                        table_name, column, 'accuracy',
                        result['accuracy_pct'], 98.0,
                        'pass' if result['meets_threshold'] else 'fail',
                        datetime.now().date()
                    ))
            
            # Anomaly metrics
            if 'anomalies' in validations:
                for column, result in validations['anomalies'].get('anomaly_results', {}).items():
                    records_to_insert.append((
                        table_name, column, 'anomaly_score',
                        result['anomaly_pct'], 5.0,  # 5% anomaly threshold
                        'pass' if result['anomaly_pct'] <= 5 else 'warning',
                        datetime.now().date()
                    ))
        
        # Batch insert
        postgres_hook.insert_rows(
            table='audit.data_quality_metrics',
            rows=records_to_insert,
            target_fields=['table_name', 'column_name', 'metric_type', 'metric_value', 
                          'threshold_value', 'status', 'execution_date']
        )
        
        logging.info(f"Stored {len(records_to_insert)} quality metrics in audit database")
    
    except Exception as e:
        logging.error(f"Failed to store quality metrics: {str(e)}")
        raise


def send_quality_alert(**context):
    """
    Send alert for data quality issues
    """
    try:
        quality_results = context['task_instance'].xcom_pull(
            task_ids='run_comprehensive_data_quality_check',
            key='data_quality_results'
        )
        
        if not quality_results:
            return
        
        critical_issues = quality_results.get('critical_issues', [])
        warnings = quality_results.get('warnings', [])
        overall_score = quality_results.get('overall_quality_score', 0)
        
        if critical_issues or overall_score < 85:
            # Create alert message
            alert_message = f"""
            🚨 **Data Quality Alert** 🚨
            
            **Overall Quality Score:** {overall_score}%
            **Execution Time:** {quality_results.get('execution_time', 'Unknown')}
            **Tables Validated:** {quality_results.get('tables_validated', 0)}
            
            **Critical Issues ({len(critical_issues)}):**
            {chr(10).join(f"• {issue}" for issue in critical_issues)}
            
            **Warnings ({len(warnings)}):**
            {chr(10).join(f"• {warning}" for warning in warnings)}
            
            **Action Required:** Please investigate data quality issues immediately.
            **Dashboard:** Check the data quality dashboard for detailed metrics.
            """
            
            context['task_instance'].xcom_push(key='alert_message', value=alert_message)
            logging.warning("Data quality alert triggered")
        else:
            logging.info("✅ No data quality alerts needed - all systems healthy")
    
    except Exception as e:
        logging.error(f"Failed to send quality alert: {str(e)}")
        raise


# Task definitions
data_quality_check_task = BranchPythonOperator(
    task_id='run_comprehensive_data_quality_check',
    python_callable=run_comprehensive_data_quality_check,
    dag=dag,
    doc_md="""Run comprehensive data quality validation across all critical tables"""
)

store_metrics_task = PythonOperator(
    task_id='store_quality_metrics',
    python_callable=store_quality_metrics,
    dag=dag,
    doc_md="""Store data quality metrics in audit database"""
)

# Quality passed path
quality_passed_task = PythonOperator(
    task_id='quality_passed',
    python_callable=lambda **context: logging.info("✅ Data quality validation passed - pipeline can proceed"),
    dag=dag
)

# Quality failed path
quality_failed_task = PythonOperator(
    task_id='quality_failed',
    python_callable=send_quality_alert,
    dag=dag,
    doc_md="""Handle data quality failure - send alerts and notifications"""
)

# Notification tasks
slack_alert_task = SlackWebhookOperator(
    task_id='send_slack_alert',
    http_conn_id='slack_webhook',
    message="{{ ti.xcom_pull(task_ids='quality_failed', key='alert_message') }}",
    channel='#data-quality-alerts',
    dag=dag,
    trigger_rule=TriggerRule.ALL_FAILED
)

email_alert_task = EmailOperator(
    task_id='send_email_alert',
    to=['data-quality@financialplanning.com', 'engineering@financialplanning.com'],
    subject='🚨 Data Quality Alert - Immediate Action Required',
    html_content="""{{ ti.xcom_pull(task_ids='quality_failed', key='alert_message') | replace('\n', '<br>') }}""",
    dag=dag,
    trigger_rule=TriggerRule.ALL_FAILED
)

# Cleanup task
cleanup_task = PostgresOperator(
    task_id='cleanup_old_metrics',
    postgres_conn_id='warehouse_postgres',
    sql="""
        DELETE FROM audit.data_quality_metrics 
        WHERE execution_date < CURRENT_DATE - INTERVAL '90 days';
        
        -- Update quality trend statistics
        INSERT INTO audit.data_quality_trends (date, overall_score, critical_issues_count, warnings_count)
        SELECT 
            CURRENT_DATE,
            AVG(metric_value) FILTER (WHERE metric_type = 'overall_quality_score'),
            COUNT(*) FILTER (WHERE status = 'fail'),
            COUNT(*) FILTER (WHERE status = 'warning')
        FROM audit.data_quality_metrics 
        WHERE execution_date = CURRENT_DATE
        ON CONFLICT (date) DO UPDATE SET
            overall_score = EXCLUDED.overall_score,
            critical_issues_count = EXCLUDED.critical_issues_count,
            warnings_count = EXCLUDED.warnings_count;
    """,
    dag=dag,
    trigger_rule=TriggerRule.NONE_FAILED_MIN_ONE_SUCCESS
)

# Task dependencies
data_quality_check_task >> [quality_passed_task, quality_failed_task]
quality_passed_task >> store_metrics_task >> cleanup_task
quality_failed_task >> [slack_alert_task, email_alert_task] >> store_metrics_task >> cleanup_task