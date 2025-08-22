"""
Comprehensive Data Governance Framework
Includes data catalog, privacy compliance, audit logging, and data lineage tracking
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
import hashlib
import re
from collections import defaultdict

import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text, MetaData, inspect
from sqlalchemy.exc import SQLAlchemyError
import requests
from cryptography.fernet import Fernet
import pydantic
from pydantic import BaseModel, Field, validator
from elasticsearch import Elasticsearch
from neo4j import GraphDatabase

# Privacy and compliance
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
from presidio_analyzer.nlp_engine import NlpEngineProvider

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataClassification(Enum):
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"
    PII = "personally_identifiable_information"
    PHI = "protected_health_information"
    PCI = "payment_card_information"

class DataQualityLevel(Enum):
    BRONZE = "bronze"  # Raw data
    SILVER = "silver"  # Cleaned and validated
    GOLD = "gold"     # Business-ready, aggregated
    PLATINUM = "platinum"  # Highly curated, certified

class ComplianceFramework(Enum):
    GDPR = "gdpr"     # General Data Protection Regulation
    CCPA = "ccpa"     # California Consumer Privacy Act
    SOX = "sox"       # Sarbanes-Oxley Act
    PCI_DSS = "pci_dss"  # Payment Card Industry Data Security Standard
    HIPAA = "hipaa"   # Health Insurance Portability and Accountability Act

@dataclass
class DataAsset:
    """Represents a data asset in the catalog"""
    id: str
    name: str
    description: str
    owner: str
    classification: DataClassification
    quality_level: DataQualityLevel
    compliance_frameworks: List[ComplianceFramework]
    schema: Dict[str, Any]
    lineage: List[str]  # List of upstream data asset IDs
    tags: List[str]
    created_at: datetime
    updated_at: datetime
    last_accessed: Optional[datetime] = None
    retention_policy_days: Optional[int] = None
    encryption_required: bool = False
    access_count: int = 0
    data_quality_score: float = 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        # Convert enums to strings
        result['classification'] = self.classification.value
        result['quality_level'] = self.quality_level.value
        result['compliance_frameworks'] = [f.value for f in self.compliance_frameworks]
        # Convert datetime to ISO string
        result['created_at'] = self.created_at.isoformat()
        result['updated_at'] = self.updated_at.isoformat()
        if self.last_accessed:
            result['last_accessed'] = self.last_accessed.isoformat()
        return result

@dataclass
class DataLineageNode:
    """Represents a node in the data lineage graph"""
    asset_id: str
    asset_name: str
    asset_type: str  # table, view, file, api, etc.
    transformation: Optional[str] = None  # SQL, Python code, etc.
    processing_time: Optional[datetime] = None
    data_quality_checks: List[Dict[str, Any]] = None

@dataclass
class AuditEvent:
    """Represents an audit event"""
    event_id: str
    timestamp: datetime
    event_type: str  # access, modification, deletion, etc.
    user_id: str
    resource_id: str
    resource_type: str
    action: str
    details: Dict[str, Any]
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    result: str = "success"  # success, failure, warning

class DataGovernanceFramework:
    """
    Comprehensive data governance framework with catalog, lineage, and compliance
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Database connections
        self.postgres_engine = create_engine(config['postgres_connection_string'])
        
        # Elasticsearch for search and catalog
        self.es_client = Elasticsearch(
            config.get('elasticsearch_url', 'http://localhost:9200')
        )
        
        # Neo4j for lineage graph
        self.neo4j_driver = GraphDatabase.driver(
            config.get('neo4j_uri', 'bolt://localhost:7687'),
            auth=(config.get('neo4j_user', 'neo4j'), config.get('neo4j_password', 'password'))
        )
        
        # Privacy engines
        self.analyzer_engine = AnalyzerEngine()
        self.anonymizer_engine = AnonymizerEngine()
        
        # Encryption for sensitive data
        encryption_key = config.get('encryption_key')
        if encryption_key:
            self.cipher_suite = Fernet(encryption_key.encode())
        else:
            # Generate a key for demo purposes
            self.cipher_suite = Fernet(Fernet.generate_key())
        
        # Data catalog storage
        self.catalog_index = 'financial_data_catalog'
        self.audit_index = 'financial_audit_log'
        
        # Initialize indices
        self.setup_elasticsearch_indices()
        self.setup_neo4j_constraints()
        
        self.logger.info("Data Governance Framework initialized")
    
    def setup_elasticsearch_indices(self):
        """Set up Elasticsearch indices for catalog and audit"""
        try:
            # Data catalog index
            catalog_mapping = {
                "mappings": {
                    "properties": {
                        "id": {"type": "keyword"},
                        "name": {"type": "text", "analyzer": "standard"},
                        "description": {"type": "text", "analyzer": "standard"},
                        "owner": {"type": "keyword"},
                        "classification": {"type": "keyword"},
                        "quality_level": {"type": "keyword"},
                        "compliance_frameworks": {"type": "keyword"},
                        "tags": {"type": "keyword"},
                        "created_at": {"type": "date"},
                        "updated_at": {"type": "date"},
                        "last_accessed": {"type": "date"},
                        "schema": {"type": "object", "enabled": False},
                        "lineage": {"type": "keyword"},
                        "data_quality_score": {"type": "float"}
                    }
                }
            }
            
            if not self.es_client.indices.exists(index=self.catalog_index):
                self.es_client.indices.create(index=self.catalog_index, body=catalog_mapping)
                self.logger.info(f"Created Elasticsearch index: {self.catalog_index}")
            
            # Audit log index
            audit_mapping = {
                "mappings": {
                    "properties": {
                        "event_id": {"type": "keyword"},
                        "timestamp": {"type": "date"},
                        "event_type": {"type": "keyword"},
                        "user_id": {"type": "keyword"},
                        "resource_id": {"type": "keyword"},
                        "resource_type": {"type": "keyword"},
                        "action": {"type": "keyword"},
                        "details": {"type": "object", "enabled": False},
                        "ip_address": {"type": "ip"},
                        "user_agent": {"type": "text"},
                        "result": {"type": "keyword"}
                    }
                }
            }
            
            if not self.es_client.indices.exists(index=self.audit_index):
                self.es_client.indices.create(index=self.audit_index, body=audit_mapping)
                self.logger.info(f"Created Elasticsearch index: {self.audit_index}")
                
        except Exception as e:
            self.logger.error(f"Error setting up Elasticsearch indices: {str(e)}")
    
    def setup_neo4j_constraints(self):
        """Set up Neo4j constraints and indices for lineage"""
        try:
            with self.neo4j_driver.session() as session:
                # Create constraints
                constraints = [
                    "CREATE CONSTRAINT asset_id_unique IF NOT EXISTS FOR (a:DataAsset) REQUIRE a.id IS UNIQUE",
                    "CREATE CONSTRAINT transformation_id_unique IF NOT EXISTS FOR (t:Transformation) REQUIRE t.id IS UNIQUE"
                ]
                
                for constraint in constraints:
                    try:
                        session.run(constraint)
                    except Exception as e:
                        # Constraint might already exist
                        if "already exists" not in str(e).lower():
                            self.logger.warning(f"Could not create constraint: {str(e)}")
                
                # Create indices
                indices = [
                    "CREATE INDEX asset_name_index IF NOT EXISTS FOR (a:DataAsset) ON (a.name)",
                    "CREATE INDEX asset_type_index IF NOT EXISTS FOR (a:DataAsset) ON (a.type)"
                ]
                
                for index in indices:
                    try:
                        session.run(index)
                    except Exception as e:
                        if "already exists" not in str(e).lower():
                            self.logger.warning(f"Could not create index: {str(e)}")
                
                self.logger.info("Neo4j constraints and indices set up")
                
        except Exception as e:
            self.logger.error(f"Error setting up Neo4j: {str(e)}")
    
    def discover_data_assets(self) -> List[DataAsset]:
        """
        Discover data assets from various sources
        """
        discovered_assets = []
        
        try:
            # Discover from PostgreSQL
            postgres_assets = self.discover_postgres_assets()
            discovered_assets.extend(postgres_assets)
            
            # Discover from file systems (future enhancement)
            # file_assets = self.discover_file_assets()
            # discovered_assets.extend(file_assets)
            
            # Discover from APIs (future enhancement)
            # api_assets = self.discover_api_assets()
            # discovered_assets.extend(api_assets)
            
            self.logger.info(f"Discovered {len(discovered_assets)} data assets")
            
        except Exception as e:
            self.logger.error(f"Error discovering data assets: {str(e)}")
        
        return discovered_assets
    
    def discover_postgres_assets(self) -> List[DataAsset]:
        """Discover data assets from PostgreSQL database"""
        assets = []
        
        try:
            inspector = inspect(self.postgres_engine)
            schemas = inspector.get_schema_names()
            
            for schema_name in schemas:
                if schema_name in ['information_schema', 'pg_catalog', 'pg_toast']:
                    continue
                
                tables = inspector.get_table_names(schema=schema_name)
                
                for table_name in tables:
                    try:
                        # Get table metadata
                        columns = inspector.get_columns(table_name, schema=schema_name)
                        
                        # Analyze data classification
                        classification = self.classify_table_data(schema_name, table_name, columns)
                        
                        # Determine compliance frameworks
                        compliance_frameworks = self.determine_compliance_frameworks(columns)
                        
                        # Build schema information
                        schema_info = {
                            'columns': [
                                {
                                    'name': col['name'],
                                    'type': str(col['type']),
                                    'nullable': col['nullable'],
                                    'default': str(col['default']) if col['default'] else None
                                } for col in columns
                            ],
                            'indexes': inspector.get_indexes(table_name, schema=schema_name),
                            'foreign_keys': inspector.get_foreign_keys(table_name, schema=schema_name)
                        }
                        
                        # Get row count and other stats
                        stats_query = f"SELECT COUNT(*) as row_count FROM {schema_name}.{table_name}"
                        with self.postgres_engine.connect() as conn:
                            result = conn.execute(text(stats_query)).fetchone()
                            row_count = result[0] if result else 0
                        
                        asset = DataAsset(
                            id=f"{schema_name}.{table_name}",
                            name=f"{schema_name}.{table_name}",
                            description=f"PostgreSQL table in {schema_name} schema",
                            owner="data_team",  # Default owner
                            classification=classification,
                            quality_level=self.determine_quality_level(schema_name),
                            compliance_frameworks=compliance_frameworks,
                            schema=schema_info,
                            lineage=[],  # Will be populated by lineage analysis
                            tags=self.generate_tags(schema_name, table_name, columns),
                            created_at=datetime.now(),
                            updated_at=datetime.now(),
                            retention_policy_days=self.determine_retention_policy(classification),
                            encryption_required=classification in [DataClassification.PII, DataClassification.PCI]
                        )
                        
                        assets.append(asset)
                        
                    except Exception as e:
                        self.logger.warning(f"Could not analyze table {schema_name}.{table_name}: {str(e)}")
                        continue
            
        except Exception as e:
            self.logger.error(f"Error discovering PostgreSQL assets: {str(e)}")
        
        return assets
    
    def classify_table_data(self, schema: str, table: str, columns: List[Dict]) -> DataClassification:
        """Classify data based on schema, table name, and column analysis"""
        # Check column names for PII indicators
        pii_indicators = [
            'email', 'phone', 'ssn', 'social_security', 'address', 'zip_code', 'postal_code',
            'first_name', 'last_name', 'full_name', 'date_of_birth', 'dob', 'birth_date'
        ]
        
        pci_indicators = [
            'credit_card', 'card_number', 'cvv', 'expiry_date', 'cardholder_name'
        ]
        
        column_names = [col['name'].lower() for col in columns]
        
        # Check for PCI data
        if any(indicator in ' '.join(column_names) for indicator in pci_indicators):
            return DataClassification.PCI
        
        # Check for PII data
        if any(indicator in ' '.join(column_names) for indicator in pii_indicators):
            return DataClassification.PII
        
        # Check by schema/table patterns
        if 'audit' in schema.lower() or 'log' in schema.lower():
            return DataClassification.INTERNAL
        
        if 'public' in schema.lower() or 'reference' in schema.lower():
            return DataClassification.PUBLIC
        
        if 'user' in table.lower() or 'customer' in table.lower():
            return DataClassification.CONFIDENTIAL
        
        # Default classification
        return DataClassification.INTERNAL
    
    def determine_compliance_frameworks(self, columns: List[Dict]) -> List[ComplianceFramework]:
        """Determine applicable compliance frameworks based on data"""
        frameworks = []
        
        column_names = [col['name'].lower() for col in columns]
        column_text = ' '.join(column_names)
        
        # GDPR - if processing personal data
        pii_indicators = ['email', 'name', 'address', 'phone', 'user_id']
        if any(indicator in column_text for indicator in pii_indicators):
            frameworks.append(ComplianceFramework.GDPR)
            frameworks.append(ComplianceFramework.CCPA)  # Often overlaps with GDPR
        
        # PCI DSS - if processing payment data
        pci_indicators = ['card', 'payment', 'credit', 'cvv']
        if any(indicator in column_text for indicator in pci_indicators):
            frameworks.append(ComplianceFramework.PCI_DSS)
        
        # SOX - financial data
        financial_indicators = ['transaction', 'balance', 'account', 'financial', 'investment']
        if any(indicator in column_text for indicator in financial_indicators):
            frameworks.append(ComplianceFramework.SOX)
        
        return frameworks
    
    def determine_quality_level(self, schema: str) -> DataQualityLevel:
        """Determine data quality level based on schema"""
        if schema == 'raw':
            return DataQualityLevel.BRONZE
        elif schema == 'staging':
            return DataQualityLevel.SILVER
        elif schema in ['marts', 'dimensions', 'facts']:
            return DataQualityLevel.GOLD
        elif schema == 'analytics':
            return DataQualityLevel.PLATINUM
        else:
            return DataQualityLevel.SILVER  # Default
    
    def determine_retention_policy(self, classification: DataClassification) -> int:
        """Determine retention policy based on data classification"""
        retention_policies = {
            DataClassification.PUBLIC: 2555,  # 7 years
            DataClassification.INTERNAL: 1095,  # 3 years
            DataClassification.CONFIDENTIAL: 2190,  # 6 years
            DataClassification.RESTRICTED: 2555,  # 7 years
            DataClassification.PII: 1095,  # 3 years (GDPR compliance)
            DataClassification.PCI: 1095,  # 3 years (PCI DSS requirement)
            DataClassification.PHI: 2555  # 7 years (HIPAA requirement)
        }
        
        return retention_policies.get(classification, 1095)
    
    def generate_tags(self, schema: str, table: str, columns: List[Dict]) -> List[str]:
        """Generate tags for a data asset"""
        tags = []
        
        # Schema-based tags
        tags.append(f"schema:{schema}")
        
        # Table name-based tags
        if 'user' in table.lower():
            tags.append('domain:user-management')
        elif 'transaction' in table.lower():
            tags.append('domain:transactions')
        elif 'portfolio' in table.lower():
            tags.append('domain:investments')
        elif 'goal' in table.lower():
            tags.append('domain:financial-planning')
        
        # Data type-based tags
        has_timestamps = any('timestamp' in str(col['type']).lower() or 'date' in str(col['type']).lower() 
                           for col in columns)
        if has_timestamps:
            tags.append('temporal-data')
        
        has_json = any('json' in str(col['type']).lower() for col in columns)
        if has_json:
            tags.append('semi-structured')
        
        # Size-based tags (would need actual row counts)
        tags.append('size:unknown')  # Placeholder
        
        return tags
    
    def register_data_asset(self, asset: DataAsset) -> bool:
        """Register a data asset in the catalog"""
        try:
            # Index in Elasticsearch
            self.es_client.index(
                index=self.catalog_index,
                id=asset.id,
                body=asset.to_dict()
            )
            
            # Add to Neo4j lineage graph
            with self.neo4j_driver.session() as session:
                session.run(
                    """
                    MERGE (a:DataAsset {id: $id})
                    SET a.name = $name,
                        a.type = $type,
                        a.classification = $classification,
                        a.owner = $owner,
                        a.created_at = $created_at
                    """,
                    id=asset.id,
                    name=asset.name,
                    type="table",  # Assume table for now
                    classification=asset.classification.value,
                    owner=asset.owner,
                    created_at=asset.created_at.isoformat()
                )
            
            self.logger.info(f"Registered data asset: {asset.id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error registering data asset {asset.id}: {str(e)}")
            return False
    
    def build_data_lineage(self, asset_id: str) -> Dict[str, Any]:
        """Build data lineage for a specific asset"""
        try:
            lineage_graph = {
                'asset_id': asset_id,
                'upstream': [],
                'downstream': [],
                'transformations': []
            }
            
            # Query database for lineage information
            # This would typically parse SQL queries, ETL logs, etc.
            lineage_info = self.extract_lineage_from_queries(asset_id)
            
            # Store lineage in Neo4j
            with self.neo4j_driver.session() as session:
                for upstream_asset in lineage_info.get('upstream', []):
                    session.run(
                        """
                        MATCH (source:DataAsset {id: $source_id})
                        MATCH (target:DataAsset {id: $target_id})
                        MERGE (source)-[r:FEEDS_INTO]->(target)
                        SET r.created_at = $timestamp
                        """,
                        source_id=upstream_asset,
                        target_id=asset_id,
                        timestamp=datetime.now().isoformat()
                    )
                    lineage_graph['upstream'].append(upstream_asset)
                
                for downstream_asset in lineage_info.get('downstream', []):
                    session.run(
                        """
                        MATCH (source:DataAsset {id: $source_id})
                        MATCH (target:DataAsset {id: $target_id})
                        MERGE (source)-[r:FEEDS_INTO]->(target)
                        SET r.created_at = $timestamp
                        """,
                        source_id=asset_id,
                        target_id=downstream_asset,
                        timestamp=datetime.now().isoformat()
                    )
                    lineage_graph['downstream'].append(downstream_asset)
            
            return lineage_graph
            
        except Exception as e:
            self.logger.error(f"Error building lineage for {asset_id}: {str(e)}")
            return {'asset_id': asset_id, 'error': str(e)}
    
    def extract_lineage_from_queries(self, asset_id: str) -> Dict[str, List[str]]:
        """Extract lineage information from SQL queries and ETL logs"""
        lineage = {'upstream': [], 'downstream': []}
        
        try:
            # Query audit logs for SQL statements involving this asset
            query = {
                "query": {
                    "bool": {
                        "must": [
                            {"match": {"resource_id": asset_id}},
                            {"match": {"event_type": "query_execution"}}
                        ]
                    }
                },
                "sort": [{"timestamp": {"order": "desc"}}],
                "size": 100
            }
            
            response = self.es_client.search(index=self.audit_index, body=query)
            
            for hit in response['hits']['hits']:
                event = hit['_source']
                sql_query = event.get('details', {}).get('query', '')
                
                if sql_query:
                    # Simple regex-based lineage extraction
                    # In production, use a proper SQL parser
                    upstream_tables = self.extract_tables_from_sql(sql_query, 'FROM')
                    lineage['upstream'].extend(upstream_tables)
                    
                    downstream_tables = self.extract_tables_from_sql(sql_query, 'INTO')
                    lineage['downstream'].extend(downstream_tables)
            
            # Remove duplicates
            lineage['upstream'] = list(set(lineage['upstream']))
            lineage['downstream'] = list(set(lineage['downstream']))
            
        except Exception as e:
            self.logger.warning(f"Could not extract lineage from queries: {str(e)}")
        
        return lineage
    
    def extract_tables_from_sql(self, sql_query: str, clause: str) -> List[str]:
        """Extract table names from SQL query (simplified)"""
        tables = []
        
        try:
            # Very basic regex - in production, use a proper SQL parser
            if clause.upper() == 'FROM':
                pattern = r'FROM\s+([a-zA-Z_][a-zA-Z0-9_.]*)'  
            elif clause.upper() == 'INTO':
                pattern = r'INTO\s+([a-zA-Z_][a-zA-Z0-9_.]*)'  
            else:
                return tables
            
            matches = re.findall(pattern, sql_query.upper(), re.IGNORECASE)
            tables.extend(matches)
            
        except Exception as e:
            self.logger.warning(f"Error extracting tables from SQL: {str(e)}")
        
        return tables
    
    def scan_for_sensitive_data(self, asset_id: str, sample_size: int = 1000) -> Dict[str, Any]:
        """Scan data asset for sensitive information using Presidio"""
        try:
            # Get sample data from the asset
            schema_table = asset_id.split('.')
            if len(schema_table) != 2:
                return {'error': 'Invalid asset ID format'}
            
            schema, table = schema_table
            
            # Sample data query
            query = f"""
                SELECT * FROM {schema}.{table} 
                TABLESAMPLE SYSTEM (1) 
                LIMIT {sample_size}
            """
            
            df = pd.read_sql(query, self.postgres_engine)
            
            sensitivity_results = {
                'asset_id': asset_id,
                'scan_timestamp': datetime.now().isoformat(),
                'rows_scanned': len(df),
                'columns_scanned': len(df.columns),
                'sensitive_columns': {},
                'overall_sensitivity_score': 0.0
            }
            
            total_sensitivity = 0
            
            for column in df.columns:
                column_data = df[column].astype(str).fillna('')
                sample_text = ' '.join(column_data.head(100).tolist())
                
                # Use Presidio to analyze text
                analysis_results = self.analyzer_engine.analyze(
                    text=sample_text,
                    entities=["PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER", "CREDIT_CARD", "US_SSN"],
                    language="en"
                )
                
                if analysis_results:
                    entity_types = [result.entity_type for result in analysis_results]
                    confidence_scores = [result.score for result in analysis_results]
                    
                    sensitivity_results['sensitive_columns'][column] = {
                        'entity_types': entity_types,
                        'confidence_scores': confidence_scores,
                        'max_confidence': max(confidence_scores) if confidence_scores else 0,
                        'entity_count': len(analysis_results)
                    }
                    
                    total_sensitivity += max(confidence_scores) if confidence_scores else 0
            
            # Calculate overall sensitivity score
            if df.columns.any():
                sensitivity_results['overall_sensitivity_score'] = total_sensitivity / len(df.columns)
            
            return sensitivity_results
            
        except Exception as e:
            self.logger.error(f"Error scanning for sensitive data in {asset_id}: {str(e)}")
            return {
                'asset_id': asset_id,
                'error': str(e),
                'scan_timestamp': datetime.now().isoformat()
            }
    
    def anonymize_sensitive_data(self, text: str, entity_types: List[str] = None) -> str:
        """Anonymize sensitive data in text using Presidio"""
        try:
            if entity_types is None:
                entity_types = ["PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER", "CREDIT_CARD", "US_SSN"]
            
            # Analyze text for entities
            analysis_results = self.analyzer_engine.analyze(
                text=text,
                entities=entity_types,
                language="en"
            )
            
            # Anonymize the text
            anonymized_text = self.anonymizer_engine.anonymize(
                text=text,
                analyzer_results=analysis_results
            )
            
            return anonymized_text.text
            
        except Exception as e:
            self.logger.error(f"Error anonymizing text: {str(e)}")
            return text  # Return original text if anonymization fails
    
    def log_audit_event(self, event: AuditEvent) -> bool:
        """Log an audit event"""
        try:
            event_dict = {
                'event_id': event.event_id,
                'timestamp': event.timestamp.isoformat(),
                'event_type': event.event_type,
                'user_id': event.user_id,
                'resource_id': event.resource_id,
                'resource_type': event.resource_type,
                'action': event.action,
                'details': event.details,
                'ip_address': event.ip_address,
                'user_agent': event.user_agent,
                'result': event.result
            }
            
            # Log to Elasticsearch
            self.es_client.index(
                index=self.audit_index,
                body=event_dict
            )
            
            # Also log to PostgreSQL for long-term retention
            with self.postgres_engine.connect() as conn:
                conn.execute(
                    text("""
                        INSERT INTO audit.governance_audit_log 
                        (event_id, timestamp, event_type, user_id, resource_id, 
                         resource_type, action, details, ip_address, user_agent, result)
                        VALUES 
                        (:event_id, :timestamp, :event_type, :user_id, :resource_id,
                         :resource_type, :action, :details, :ip_address, :user_agent, :result)
                    ""),
                    {
                        'event_id': event.event_id,
                        'timestamp': event.timestamp,
                        'event_type': event.event_type,
                        'user_id': event.user_id,
                        'resource_id': event.resource_id,
                        'resource_type': event.resource_type,
                        'action': event.action,
                        'details': json.dumps(event.details),
                        'ip_address': event.ip_address,
                        'user_agent': event.user_agent,
                        'result': event.result
                    }
                )
                conn.commit()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error logging audit event: {str(e)}")
            return False
    
    def search_catalog(self, query: str, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Search the data catalog"""
        try:
            # Build Elasticsearch query
            search_body = {
                "query": {
                    "bool": {
                        "must": [
                            {
                                "multi_match": {
                                    "query": query,
                                    "fields": ["name^2", "description", "tags", "owner"]
                                }
                            }
                        ]
                    }
                },
                "highlight": {
                    "fields": {
                        "name": {},
                        "description": {}
                    }
                },
                "size": 50
            }
            
            # Apply filters
            if filters:
                filter_clauses = []
                
                if filters.get('classification'):
                    filter_clauses.append({"term": {"classification": filters['classification']}})
                
                if filters.get('owner'):
                    filter_clauses.append({"term": {"owner": filters['owner']}})
                
                if filters.get('quality_level'):
                    filter_clauses.append({"term": {"quality_level": filters['quality_level']}})
                
                if filters.get('tags'):
                    for tag in filters['tags']:
                        filter_clauses.append({"term": {"tags": tag}})
                
                if filter_clauses:
                    search_body["query"]["bool"]["filter"] = filter_clauses
            
            # Execute search
            response = self.es_client.search(index=self.catalog_index, body=search_body)
            
            # Format results
            results = {
                'total_hits': response['hits']['total']['value'],
                'assets': [],
                'facets': self.get_search_facets()
            }
            
            for hit in response['hits']['hits']:
                asset = hit['_source']
                asset['score'] = hit['_score']
                if 'highlight' in hit:
                    asset['highlight'] = hit['highlight']
                results['assets'].append(asset)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error searching catalog: {str(e)}")
            return {
                'total_hits': 0,
                'assets': [],
                'error': str(e)
            }
    
    def get_search_facets(self) -> Dict[str, List[Dict]]:
        """Get facets for search refinement"""
        try:
            # Aggregation query for facets
            facet_body = {
                "size": 0,
                "aggs": {
                    "classifications": {
                        "terms": {"field": "classification"}
                    },
                    "owners": {
                        "terms": {"field": "owner"}
                    },
                    "quality_levels": {
                        "terms": {"field": "quality_level"}
                    },
                    "tags": {
                        "terms": {"field": "tags", "size": 20}
                    }
                }
            }
            
            response = self.es_client.search(index=self.catalog_index, body=facet_body)
            
            facets = {}
            for agg_name, agg_data in response['aggregations'].items():
                facets[agg_name] = [
                    {'value': bucket['key'], 'count': bucket['doc_count']}
                    for bucket in agg_data['buckets']
                ]
            
            return facets
            
        except Exception as e:
            self.logger.warning(f"Could not get search facets: {str(e)}")
            return {}
    
    def generate_compliance_report(self, framework: ComplianceFramework) -> Dict[str, Any]:
        """Generate compliance report for a specific framework"""
        try:
            report = {
                'framework': framework.value,
                'generated_at': datetime.now().isoformat(),
                'summary': {
                    'total_assets': 0,
                    'compliant_assets': 0,
                    'non_compliant_assets': 0,
                    'compliance_percentage': 0
                },
                'assets': [],
                'recommendations': []
            }
            
            # Query assets subject to this framework
            query = {
                "query": {
                    "term": {"compliance_frameworks": framework.value}
                },
                "size": 1000
            }
            
            response = self.es_client.search(index=self.catalog_index, body=query)
            
            report['summary']['total_assets'] = response['hits']['total']['value']
            
            for hit in response['hits']['hits']:
                asset = hit['_source']
                
                # Check compliance based on framework requirements
                compliance_status = self.check_asset_compliance(asset, framework)
                
                asset_report = {
                    'id': asset['id'],
                    'name': asset['name'],
                    'classification': asset['classification'],
                    'compliance_status': compliance_status['status'],
                    'issues': compliance_status['issues'],
                    'last_accessed': asset.get('last_accessed'),
                    'encryption_required': asset.get('encryption_required', False)
                }
                
                report['assets'].append(asset_report)
                
                if compliance_status['status'] == 'compliant':
                    report['summary']['compliant_assets'] += 1
                else:
                    report['summary']['non_compliant_assets'] += 1
            
            # Calculate compliance percentage
            if report['summary']['total_assets'] > 0:
                report['summary']['compliance_percentage'] = (
                    report['summary']['compliant_assets'] / report['summary']['total_assets']
                ) * 100
            
            # Generate recommendations
            report['recommendations'] = self.generate_compliance_recommendations(framework, report['assets'])
            
            return report
            
        except Exception as e:
            self.logger.error(f"Error generating compliance report: {str(e)}")
            return {
                'framework': framework.value,
                'error': str(e),
                'generated_at': datetime.now().isoformat()
            }
    
    def check_asset_compliance(self, asset: Dict[str, Any], framework: ComplianceFramework) -> Dict[str, Any]:
        """Check if an asset is compliant with a framework"""
        compliance_check = {
            'status': 'compliant',
            'issues': []
        }
        
        try:
            if framework == ComplianceFramework.GDPR:
                # GDPR compliance checks
                if asset['classification'] == DataClassification.PII.value:
                    if not asset.get('encryption_required', False):
                        compliance_check['issues'].append('PII data should be encrypted')
                    
                    if not asset.get('retention_policy_days'):
                        compliance_check['issues'].append('Retention policy not defined')
                    
                    if asset.get('retention_policy_days', 0) > 2555:  # 7 years
                        compliance_check['issues'].append('Retention period may be too long for GDPR')
            
            elif framework == ComplianceFramework.PCI_DSS:
                # PCI DSS compliance checks
                if asset['classification'] == DataClassification.PCI.value:
                    if not asset.get('encryption_required', False):
                        compliance_check['issues'].append('Payment data must be encrypted')
                    
                    if asset.get('retention_policy_days', 0) > 1095:  # 3 years
                        compliance_check['issues'].append('PCI data retention exceeds recommended period')
            
            elif framework == ComplianceFramework.SOX:
                # SOX compliance checks
                if 'financial' in asset.get('tags', []):
                    if not asset.get('last_accessed'):
                        compliance_check['issues'].append('Access tracking not implemented')
            
            if compliance_check['issues']:
                compliance_check['status'] = 'non_compliant'
            
        except Exception as e:
            compliance_check['status'] = 'error'
            compliance_check['issues'].append(f"Error checking compliance: {str(e)}")
        
        return compliance_check
    
    def generate_compliance_recommendations(self, framework: ComplianceFramework, 
                                         assets: List[Dict[str, Any]]) -> List[str]:
        """Generate compliance recommendations"""
        recommendations = []
        
        non_compliant_assets = [a for a in assets if a['compliance_status'] != 'compliant']
        
        if not non_compliant_assets:
            return ["All assets are compliant with the framework requirements."]
        
        # Common recommendations based on issues found
        encryption_issues = sum(1 for a in non_compliant_assets if any('encrypt' in issue.lower() for issue in a['issues']))
        retention_issues = sum(1 for a in non_compliant_assets if any('retention' in issue.lower() for issue in a['issues']))
        access_issues = sum(1 for a in non_compliant_assets if any('access' in issue.lower() for issue in a['issues']))
        
        if encryption_issues > 0:
            recommendations.append(f"Implement encryption for {encryption_issues} assets containing sensitive data")
        
        if retention_issues > 0:
            recommendations.append(f"Review and update retention policies for {retention_issues} assets")
        
        if access_issues > 0:
            recommendations.append(f"Implement access tracking and audit logging for {access_issues} assets")
        
        # Framework-specific recommendations
        if framework == ComplianceFramework.GDPR:
            recommendations.extend([
                "Implement data subject access request handling procedures",
                "Set up automated data deletion based on retention policies",
                "Conduct regular privacy impact assessments"
            ])
        
        elif framework == ComplianceFramework.PCI_DSS:
            recommendations.extend([
                "Implement network segmentation for payment processing systems",
                "Set up regular vulnerability scanning",
                "Establish access controls with least privilege principle"
            ])
        
        return recommendations
    
    def cleanup(self):
        """Clean up resources"""
        try:
            if hasattr(self, 'neo4j_driver'):
                self.neo4j_driver.close()
            self.logger.info("Data Governance Framework cleanup completed")
        except Exception as e:
            self.logger.error(f"Error during cleanup: {str(e)}")


# Example usage and setup functions
def setup_governance_database():
    """Set up governance-related database tables"""
    setup_sql = """
    -- Create governance audit log table
    CREATE TABLE IF NOT EXISTS audit.governance_audit_log (
        id BIGSERIAL PRIMARY KEY,
        event_id VARCHAR(100) NOT NULL UNIQUE,
        timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
        event_type VARCHAR(50) NOT NULL,
        user_id VARCHAR(100) NOT NULL,
        resource_id VARCHAR(200) NOT NULL,
        resource_type VARCHAR(50) NOT NULL,
        action VARCHAR(100) NOT NULL,
        details JSONB,
        ip_address INET,
        user_agent TEXT,
        result VARCHAR(20) NOT NULL DEFAULT 'success',
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
    
    -- Create indexes for performance
    CREATE INDEX IF NOT EXISTS idx_governance_audit_timestamp ON audit.governance_audit_log(timestamp);
    CREATE INDEX IF NOT EXISTS idx_governance_audit_user ON audit.governance_audit_log(user_id);
    CREATE INDEX IF NOT EXISTS idx_governance_audit_resource ON audit.governance_audit_log(resource_id);
    CREATE INDEX IF NOT EXISTS idx_governance_audit_event_type ON audit.governance_audit_log(event_type);
    
    -- Create data retention policies table
    CREATE TABLE IF NOT EXISTS governance.data_retention_policies (
        id BIGSERIAL PRIMARY KEY,
        asset_pattern VARCHAR(200) NOT NULL,
        classification VARCHAR(50) NOT NULL,
        retention_days INTEGER NOT NULL,
        compliance_framework VARCHAR(50),
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
    
    -- Create data lineage tracking table
    CREATE TABLE IF NOT EXISTS governance.data_lineage (
        id BIGSERIAL PRIMARY KEY,
        source_asset_id VARCHAR(200) NOT NULL,
        target_asset_id VARCHAR(200) NOT NULL,
        transformation_type VARCHAR(50),
        transformation_code TEXT,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    return setup_sql


if __name__ == "__main__":
    # Example configuration
    config = {
        'postgres_connection_string': 'postgresql://user:password@localhost/financial_planning',
        'elasticsearch_url': 'http://localhost:9200',
        'neo4j_uri': 'bolt://localhost:7687',
        'neo4j_user': 'neo4j',
        'neo4j_password': 'password',
        'encryption_key': Fernet.generate_key().decode()
    }
    
    # Initialize governance framework
    governance = DataGovernanceFramework(config)
    
    # Discover and register data assets
    print("Discovering data assets...")
    assets = governance.discover_data_assets()
    
    for asset in assets[:5]:  # Register first 5 assets
        governance.register_data_asset(asset)
        print(f"Registered: {asset.name}")
    
    # Scan for sensitive data
    if assets:
        print(f"\nScanning for sensitive data in {assets[0].id}...")
        sensitivity_scan = governance.scan_for_sensitive_data(assets[0].id)
        print(f"Sensitivity scan completed: {sensitivity_scan.get('overall_sensitivity_score', 0):.2f} score")
    
    # Generate compliance report
    print("\nGenerating GDPR compliance report...")
    compliance_report = governance.generate_compliance_report(ComplianceFramework.GDPR)
    print(f"Compliance report: {compliance_report['summary']['compliance_percentage']:.1f}% compliant")
    
    # Search catalog
    print("\nSearching catalog for 'user' assets...")
    search_results = governance.search_catalog("user")
    print(f"Found {search_results['total_hits']} assets matching 'user'")
    
    # Log sample audit event
    audit_event = AuditEvent(
        event_id="test_event_001",
        timestamp=datetime.now(),
        event_type="data_access",
        user_id="test_user",
        resource_id="dimensions.dim_user",
        resource_type="table",
        action="SELECT",
        details={"query": "SELECT * FROM dimensions.dim_user LIMIT 10"},
        result="success"
    )
    
    governance.log_audit_event(audit_event)
    print("\nAudit event logged successfully")
    
    # Cleanup
    governance.cleanup()
    print("\nData Governance Framework demonstration completed!")
