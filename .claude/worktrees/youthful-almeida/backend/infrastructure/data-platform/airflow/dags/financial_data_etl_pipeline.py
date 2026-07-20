"""
Financial Data ETL Pipeline - Main orchestration DAG
Handles the complete ETL process for financial planning data
"""

from datetime import datetime, timedelta
from typing import Dict, Any

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.providers.http.sensors.http import HttpSensor
from airflow.providers.email.operators.email import EmailOperator
from airflow.models import Variable
from airflow.utils.dates import days_ago
from airflow.utils.task_group import TaskGroup
from airflow.utils.trigger_rule import TriggerRule

import pandas as pd
import numpy as np
import logging
from sqlalchemy import create_engine
import requests
import json


# Configuration
default_args = {
    'owner': 'data-engineering',
    'depends_on_past': False,
    'start_date': days_ago(1),
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
    'catchup': False,
    'max_active_runs': 1,
    'email': ['data-alerts@financialplanning.com']
}

# DAG Definition
dag = DAG(
    'financial_data_etl_pipeline',
    default_args=default_args,
    description='Comprehensive financial data ETL pipeline with quality checks',
    schedule_interval='@daily',
    catchup=False,
    tags=['etl', 'financial', 'daily'],
    doc_md=__doc__
)


def extract_market_data(**context):
    """
    Extract market data from multiple sources with error handling
    """
    try:
        # Market data sources configuration
        sources = [
            {
                'name': 'alpha_vantage',
                'url': Variable.get('ALPHA_VANTAGE_URL'),
                'api_key': Variable.get('ALPHA_VANTAGE_API_KEY')
            },
            {
                'name': 'yahoo_finance',
                'url': Variable.get('YAHOO_FINANCE_URL'),
                'api_key': Variable.get('YAHOO_FINANCE_API_KEY', None)
            }
        ]
        
        extracted_data = {}
        
        for source in sources:
            logging.info(f"Extracting data from {source['name']}")
            
            # API request with retry logic
            for attempt in range(3):
                try:
                    headers = {'Authorization': f"Bearer {source['api_key']}"} if source.get('api_key') else {}
                    response = requests.get(source['url'], headers=headers, timeout=30)
                    response.raise_for_status()
                    
                    extracted_data[source['name']] = response.json()
                    logging.info(f"Successfully extracted data from {source['name']}")
                    break
                    
                except requests.exceptions.RequestException as e:
                    logging.warning(f"Attempt {attempt + 1} failed for {source['name']}: {str(e)}")
                    if attempt == 2:  # Last attempt
                        logging.error(f"Failed to extract data from {source['name']} after 3 attempts")
                        extracted_data[source['name']] = None
        
        # Store extracted data in XCom
        context['task_instance'].xcom_push(key='extracted_market_data', value=extracted_data)
        
        return extracted_data
        
    except Exception as e:
        logging.error(f"Market data extraction failed: {str(e)}")
        raise


def extract_banking_data(**context):
    """
    Extract banking and transaction data from Plaid/Yodlee
    """
    try:
        # Banking data extraction
        plaid_config = {
            'client_id': Variable.get('PLAID_CLIENT_ID'),
            'secret': Variable.get('PLAID_SECRET'),
            'environment': Variable.get('PLAID_ENVIRONMENT', 'sandbox')
        }
        
        # Simulate banking data extraction
        banking_data = {
            'transactions': [],
            'accounts': [],
            'balances': []
        }
        
        # In real implementation, this would connect to Plaid/Yodlee APIs
        logging.info("Banking data extraction completed")
        
        context['task_instance'].xcom_push(key='extracted_banking_data', value=banking_data)
        return banking_data
        
    except Exception as e:
        logging.error(f"Banking data extraction failed: {str(e)}")
        raise


def data_quality_check(**context):
    """
    Comprehensive data quality checks with configurable rules
    """
    try:
        # Retrieve extracted data
        market_data = context['task_instance'].xcom_pull(
            task_ids='extract_market_data', 
            key='extracted_market_data'
        )
        banking_data = context['task_instance'].xcom_pull(
            task_ids='extract_banking_data', 
            key='extracted_banking_data'
        )
        
        quality_results = {
            'passed': True,
            'errors': [],
            'warnings': [],
            'metrics': {}
        }
        
        # Data completeness checks
        if not market_data or all(v is None for v in market_data.values()):
            quality_results['errors'].append('No market data available')
            quality_results['passed'] = False
        
        # Data freshness checks
        # Add timestamp validation logic here
        
        # Data consistency checks
        # Add cross-source validation logic here
        
        # Schema validation
        # Add schema validation logic here
        
        logging.info(f"Data quality check completed: {quality_results}")
        
        context['task_instance'].xcom_push(key='quality_results', value=quality_results)
        
        if not quality_results['passed']:
            raise ValueError(f"Data quality check failed: {quality_results['errors']}")
        
        return quality_results
        
    except Exception as e:
        logging.error(f"Data quality check failed: {str(e)}")
        raise


def transform_market_data(**context):
    """
    Transform and clean market data with advanced processing
    """
    try:
        # Retrieve market data
        market_data = context['task_instance'].xcom_pull(
            task_ids='extract_market_data',
            key='extracted_market_data'
        )
        
        transformed_data = {}
        
        for source, data in market_data.items():
            if data is None:
                continue
                
            # Convert to DataFrame for processing
            df = pd.DataFrame(data)
            
            # Data cleaning and transformation
            # Remove duplicates
            df = df.drop_duplicates()
            
            # Handle missing values
            df = df.fillna(method='forward').fillna(method='backward')
            
            # Normalize data types
            # Add specific transformation logic here
            
            # Calculate technical indicators
            # Add financial calculations here
            
            transformed_data[source] = df.to_dict('records')
        
        logging.info("Market data transformation completed")
        
        context['task_instance'].xcom_push(key='transformed_market_data', value=transformed_data)
        return transformed_data
        
    except Exception as e:
        logging.error(f"Market data transformation failed: {str(e)}")
        raise


def transform_banking_data(**context):
    """
    Transform banking and transaction data
    """
    try:
        # Retrieve banking data
        banking_data = context['task_instance'].xcom_pull(
            task_ids='extract_banking_data',
            key='extracted_banking_data'
        )
        
        # Transform transactions
        transformed_transactions = []
        for transaction in banking_data.get('transactions', []):
            # Categorize transactions
            # Detect spending patterns
            # Calculate metrics
            transformed_transactions.append(transaction)
        
        # Transform accounts
        transformed_accounts = []
        for account in banking_data.get('accounts', []):
            # Standardize account data
            # Calculate account metrics
            transformed_accounts.append(account)
        
        transformed_data = {
            'transactions': transformed_transactions,
            'accounts': transformed_accounts,
            'balances': banking_data.get('balances', [])
        }
        
        logging.info("Banking data transformation completed")
        
        context['task_instance'].xcom_push(key='transformed_banking_data', value=transformed_data)
        return transformed_data
        
    except Exception as e:
        logging.error(f"Banking data transformation failed: {str(e)}")
        raise


def load_to_warehouse(**context):
    """
    Load transformed data to data warehouse with upsert logic
    """
    try:
        # Get transformed data
        market_data = context['task_instance'].xcom_pull(
            task_ids='transform_market_data',
            key='transformed_market_data'
        )
        banking_data = context['task_instance'].xcom_pull(
            task_ids='transform_banking_data',
            key='transformed_banking_data'
        )
        
        # Database connection
        postgres_hook = PostgresHook(postgres_conn_id='warehouse_postgres')
        engine = postgres_hook.get_sqlalchemy_engine()
        
        # Load market data
        for source, data in market_data.items():
            if data:
                df = pd.DataFrame(data)
                table_name = f'market_data_{source}'
                
                # Upsert operation
                df.to_sql(
                    table_name,
                    engine,
                    if_exists='replace',  # In production, use proper upsert logic
                    index=False,
                    method='multi'
                )
                logging.info(f"Loaded {len(df)} records to {table_name}")
        
        # Load banking data
        for data_type, data in banking_data.items():
            if data:
                df = pd.DataFrame(data)
                table_name = f'banking_{data_type}'
                
                df.to_sql(
                    table_name,
                    engine,
                    if_exists='replace',
                    index=False,
                    method='multi'
                )
                logging.info(f"Loaded {len(df)} records to {table_name}")
        
        logging.info("Data warehouse loading completed successfully")
        
        return True
        
    except Exception as e:
        logging.error(f"Data warehouse loading failed: {str(e)}")
        raise


def generate_data_lineage(**context):
    """
    Generate data lineage information for governance
    """
    try:
        lineage_info = {
            'pipeline_id': context['dag_run'].dag_id,
            'execution_date': context['execution_date'].isoformat(),
            'sources': ['alpha_vantage', 'yahoo_finance', 'plaid'],
            'transformations': ['data_cleaning', 'technical_indicators', 'categorization'],
            'destinations': ['warehouse.market_data', 'warehouse.banking_data']
        }
        
        # Store lineage in governance system
        # In production, this would integrate with data catalog
        
        logging.info(f"Data lineage generated: {lineage_info}")
        return lineage_info
        
    except Exception as e:
        logging.error(f"Data lineage generation failed: {str(e)}")
        raise


def send_success_notification(**context):
    """
    Send success notification with pipeline metrics
    """
    try:
        # Gather pipeline metrics
        metrics = {
            'execution_time': str(datetime.now() - context['dag_run'].start_date),
            'records_processed': 'TBD',  # Would calculate from XCom data
            'quality_score': 'PASS'
        }
        
        logging.info(f"Pipeline completed successfully: {metrics}")
        return metrics
        
    except Exception as e:
        logging.error(f"Success notification failed: {str(e)}")
        raise


# Task Groups for better organization
with TaskGroup("data_extraction", dag=dag) as extraction_group:
    extract_market_task = PythonOperator(
        task_id='extract_market_data',
        python_callable=extract_market_data,
        doc_md="Extract market data from external APIs"
    )
    
    extract_banking_task = PythonOperator(
        task_id='extract_banking_data',
        python_callable=extract_banking_data,
        doc_md="Extract banking data from Plaid/Yodlee"
    )

with TaskGroup("data_transformation", dag=dag) as transformation_group:
    transform_market_task = PythonOperator(
        task_id='transform_market_data',
        python_callable=transform_market_data,
        doc_md="Transform and clean market data"
    )
    
    transform_banking_task = PythonOperator(
        task_id='transform_banking_data',
        python_callable=transform_banking_data,
        doc_md="Transform banking and transaction data"
    )

# Individual tasks
data_quality_task = PythonOperator(
    task_id='data_quality_check',
    python_callable=data_quality_check,
    doc_md="Comprehensive data quality validation"
)

load_warehouse_task = PythonOperator(
    task_id='load_to_warehouse',
    python_callable=load_to_warehouse,
    doc_md="Load data to data warehouse"
)

lineage_task = PythonOperator(
    task_id='generate_data_lineage',
    python_callable=generate_data_lineage,
    doc_md="Generate data lineage for governance"
)

success_notification_task = PythonOperator(
    task_id='send_success_notification',
    python_callable=send_success_notification,
    trigger_rule=TriggerRule.ALL_SUCCESS,
    doc_md="Send pipeline success notification"
)

failure_notification_task = EmailOperator(
    task_id='send_failure_notification',
    to=['data-alerts@financialplanning.com'],
    subject='Financial Data ETL Pipeline Failed',
    html_content="""
    <h3>Pipeline Failure Alert</h3>
    <p>The financial data ETL pipeline has failed.</p>
    <p>Execution Date: {{ ds }}</p>
    <p>DAG: {{ dag.dag_id }}</p>
    <p>Please check the Airflow logs for more details.</p>
    """,
    trigger_rule=TriggerRule.ONE_FAILED
)

# Task Dependencies
extraction_group >> data_quality_task
data_quality_task >> transformation_group
transformation_group >> load_warehouse_task
load_warehouse_task >> lineage_task
lineage_task >> success_notification_task

# Failure notification runs on any task failure
[extraction_group, data_quality_task, transformation_group, 
 load_warehouse_task, lineage_task] >> failure_notification_task