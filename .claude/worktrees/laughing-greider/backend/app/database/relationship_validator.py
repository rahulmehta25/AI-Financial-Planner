"""
Database Relationship and Constraint Validator for Financial Planning System

This module validates all database relationships, constraints, and data integrity
rules to ensure the database schema is properly implemented and maintained.
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional, Set, Tuple
from datetime import datetime, timezone
from dataclasses import dataclass, field
from enum import Enum

from sqlalchemy import text, inspect
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.infrastructure.database import db_manager
from app.models.enhanced_models import (
    User, Portfolio, Account, Transaction, EnhancedMarketData,
    UserActivityLog, RegulatoryReport
)

logger = logging.getLogger(__name__)


class ValidationSeverity(Enum):
    """Severity levels for validation issues"""
    INFO = "info"
    WARNING = "warning" 
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ValidationIssue:
    """Represents a database validation issue"""
    severity: ValidationSeverity
    category: str
    table_name: str
    column_name: Optional[str] = None
    constraint_name: Optional[str] = None
    description: str = ""
    affected_rows: int = 0
    recommendation: str = ""
    sql_query: Optional[str] = None


@dataclass 
class RelationshipDefinition:
    """Definition of a database relationship to validate"""
    parent_table: str
    parent_column: str
    child_table: str
    child_column: str
    relationship_type: str  # "one_to_many", "one_to_one", "many_to_many"
    is_nullable: bool = True
    cascade_delete: bool = False


@dataclass
class ValidationResult:
    """Results from database validation"""
    issues: List[ValidationIssue] = field(default_factory=list)
    relationship_violations: List[ValidationIssue] = field(default_factory=list)
    constraint_violations: List[ValidationIssue] = field(default_factory=list)
    data_integrity_issues: List[ValidationIssue] = field(default_factory=list)
    performance_issues: List[ValidationIssue] = field(default_factory=list)
    summary: Dict[str, int] = field(default_factory=dict)
    validation_score: float = 0.0


class DatabaseRelationshipValidator:
    """
    Comprehensive validator for database relationships and constraints
    """
    
    def __init__(self):
        self.relationships = self._define_relationships()
        self.business_rules = self._define_business_rules()
        
    def _define_relationships(self) -> List[RelationshipDefinition]:
        """Define all expected database relationships"""
        return [
            # User -> Portfolio (one-to-many)
            RelationshipDefinition(
                parent_table="enhanced_users",
                parent_column="id",
                child_table="enhanced_portfolios", 
                child_column="user_id",
                relationship_type="one_to_many",
                is_nullable=False,
                cascade_delete=True
            ),
            
            # Portfolio -> Account (one-to-many)
            RelationshipDefinition(
                parent_table="enhanced_portfolios",
                parent_column="id", 
                child_table="enhanced_accounts",
                child_column="portfolio_id",
                relationship_type="one_to_many",
                is_nullable=True,  # Accounts can exist without portfolio initially
                cascade_delete=True
            ),
            
            # Account -> Transaction (one-to-many)
            RelationshipDefinition(
                parent_table="enhanced_accounts",
                parent_column="id",
                child_table="enhanced_transactions",
                child_column="account_id", 
                relationship_type="one_to_many",
                is_nullable=False,
                cascade_delete=True
            ),
            
            # User -> UserActivityLog (one-to-many)
            RelationshipDefinition(
                parent_table="enhanced_users",
                parent_column="id",
                child_table="user_activity_log",
                child_column="user_id",
                relationship_type="one_to_many",
                is_nullable=True,  # System activities may not have user
                cascade_delete=True
            ),
            
            # User -> RegulatoryReport (one-to-many)
            RelationshipDefinition(
                parent_table="enhanced_users", 
                parent_column="id",
                child_table="regulatory_reports",
                child_column="user_id",
                relationship_type="one_to_many",
                is_nullable=True,  # Some reports may be system-wide
                cascade_delete=True
            ),
            
            # Account -> RegulatoryReport (one-to-many)
            RelationshipDefinition(
                parent_table="enhanced_accounts",
                parent_column="id",
                child_table="regulatory_reports",
                child_column="account_id", 
                relationship_type="one_to_many",
                is_nullable=True,
                cascade_delete=False
            ),
            
            # Portfolio -> RegulatoryReport (one-to-many)
            RelationshipDefinition(
                parent_table="enhanced_portfolios",
                parent_column="id",
                child_table="regulatory_reports", 
                child_column="portfolio_id",
                relationship_type="one_to_many",
                is_nullable=True,
                cascade_delete=False
            ),
            
            # Transaction -> Transaction (self-referential for corporate actions)
            RelationshipDefinition(
                parent_table="enhanced_transactions",
                parent_column="id",
                child_table="enhanced_transactions",
                child_column="original_transaction_id",
                relationship_type="one_to_many",
                is_nullable=True,
                cascade_delete=False
            )
        ]
    
    def _define_business_rules(self) -> List[Dict[str, Any]]:
        """Define business logic validation rules"""
        return [
            # User business rules
            {
                "name": "valid_email_format",
                "table": "enhanced_users",
                "query": "SELECT COUNT(*) FROM enhanced_users WHERE email !~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$'",
                "description": "Users must have valid email addresses",
                "severity": ValidationSeverity.ERROR
            },
            {
                "name": "risk_tolerance_range",
                "table": "enhanced_users", 
                "query": "SELECT COUNT(*) FROM enhanced_users WHERE risk_tolerance < 0 OR risk_tolerance > 1",
                "description": "Risk tolerance must be between 0 and 1",
                "severity": ValidationSeverity.ERROR
            },
            {
                "name": "investment_horizon_positive",
                "table": "enhanced_users",
                "query": "SELECT COUNT(*) FROM enhanced_users WHERE investment_horizon <= 0",
                "description": "Investment horizon must be positive",
                "severity": ValidationSeverity.ERROR
            },
            {
                "name": "kyc_expiration_future",
                "table": "enhanced_users",
                "query": "SELECT COUNT(*) FROM enhanced_users WHERE kyc_expires_at < NOW() AND kyc_status = 'approved'",
                "description": "Approved KYC records should not be expired",
                "severity": ValidationSeverity.WARNING
            },
            
            # Portfolio business rules
            {
                "name": "portfolio_total_value_non_negative",
                "table": "enhanced_portfolios",
                "query": "SELECT COUNT(*) FROM enhanced_portfolios WHERE total_value < 0",
                "description": "Portfolio total value cannot be negative",
                "severity": ValidationSeverity.ERROR
            },
            {
                "name": "performance_reasonable_range",
                "table": "enhanced_portfolios", 
                "query": "SELECT COUNT(*) FROM enhanced_portfolios WHERE performance_ytd < -0.99 OR performance_ytd > 10.0",
                "description": "Year-to-date performance should be within reasonable range",
                "severity": ValidationSeverity.WARNING
            },
            {
                "name": "rebalancing_threshold_valid",
                "table": "enhanced_portfolios",
                "query": "SELECT COUNT(*) FROM enhanced_portfolios WHERE rebalancing_threshold <= 0 OR rebalancing_threshold > 100",
                "description": "Rebalancing threshold should be between 0 and 100 percent",
                "severity": ValidationSeverity.ERROR
            },
            {
                "name": "cash_balance_consistency",
                "table": "enhanced_portfolios",
                "query": "SELECT COUNT(*) FROM enhanced_portfolios WHERE cash_balance > total_value",
                "description": "Cash balance cannot exceed total portfolio value", 
                "severity": ValidationSeverity.ERROR
            },
            
            # Account business rules
            {
                "name": "account_balance_non_negative_for_retirement",
                "table": "enhanced_accounts",
                "query": "SELECT COUNT(*) FROM enhanced_accounts WHERE current_balance < 0 AND account_type IN ('401k', 'roth_ira', 'traditional_ira', 'hsa', '529')",
                "description": "Retirement and tax-advantaged accounts cannot have negative balances",
                "severity": ValidationSeverity.ERROR
            },
            {
                "name": "contribution_limits_not_exceeded",
                "table": "enhanced_accounts", 
                "query": "SELECT COUNT(*) FROM enhanced_accounts WHERE employee_contribution_ytd > annual_contribution_limit AND annual_contribution_limit IS NOT NULL",
                "description": "Employee contributions should not exceed annual limits",
                "severity": ValidationSeverity.WARNING
            },
            {
                "name": "vested_balance_consistency",
                "table": "enhanced_accounts",
                "query": "SELECT COUNT(*) FROM enhanced_accounts WHERE vested_balance > current_balance AND vested_balance IS NOT NULL",
                "description": "Vested balance cannot exceed current balance",
                "severity": ValidationSeverity.ERROR
            },
            {
                "name": "employer_match_reasonable",
                "table": "enhanced_accounts",
                "query": "SELECT COUNT(*) FROM enhanced_accounts WHERE employer_match_percent > 100",
                "description": "Employer match percentage should not exceed 100%",
                "severity": ValidationSeverity.WARNING
            },
            
            # Transaction business rules  
            {
                "name": "transaction_amount_not_zero",
                "table": "enhanced_transactions",
                "query": "SELECT COUNT(*) FROM enhanced_transactions WHERE total_amount = 0 AND type NOT IN ('split', 'merger')",
                "description": "Transaction amounts should not be zero except for corporate actions",
                "severity": ValidationSeverity.WARNING
            },
            {
                "name": "trade_settlement_date_order",
                "table": "enhanced_transactions",
                "query": "SELECT COUNT(*) FROM enhanced_transactions WHERE trade_date > settlement_date AND settlement_date IS NOT NULL",
                "description": "Trade date should not be after settlement date",
                "severity": ValidationSeverity.ERROR
            },
            {
                "name": "wash_sale_consistency",
                "table": "enhanced_transactions",
                "query": "SELECT COUNT(*) FROM enhanced_transactions WHERE wash_sale = true AND wash_sale_disallowed_loss IS NULL",
                "description": "Wash sale transactions should have disallowed loss amount",
                "severity": ValidationSeverity.ERROR
            },
            {
                "name": "quantity_price_consistency", 
                "table": "enhanced_transactions",
                "query": "SELECT COUNT(*) FROM enhanced_transactions WHERE quantity IS NOT NULL AND price IS NOT NULL AND ABS(quantity * price - total_amount) > 0.01",
                "description": "Quantity * Price should approximately equal total amount",
                "severity": ValidationSeverity.WARNING
            },
            {
                "name": "dividend_per_share_consistency",
                "table": "enhanced_transactions",
                "query": "SELECT COUNT(*) FROM enhanced_transactions WHERE dividend_per_share IS NOT NULL AND quantity IS NOT NULL AND ABS(dividend_per_share * quantity - total_amount) > 0.01 AND type = 'dividend'",
                "description": "Dividend per share * quantity should equal total dividend amount",
                "severity": ValidationSeverity.WARNING
            },
            
            # Market data business rules
            {
                "name": "ohlc_logical_order",
                "table": "enhanced_market_data", 
                "query": "SELECT COUNT(*) FROM enhanced_market_data WHERE high < low OR high < open OR high < close OR low > open OR low > close",
                "description": "OHLC data must follow logical price relationships",
                "severity": ValidationSeverity.ERROR
            },
            {
                "name": "positive_prices",
                "table": "enhanced_market_data",
                "query": "SELECT COUNT(*) FROM enhanced_market_data WHERE open <= 0 OR high <= 0 OR low <= 0 OR close <= 0",
                "description": "All prices must be positive",
                "severity": ValidationSeverity.ERROR
            },
            {
                "name": "volume_non_negative",
                "table": "enhanced_market_data",
                "query": "SELECT COUNT(*) FROM enhanced_market_data WHERE volume < 0",
                "description": "Trading volume cannot be negative",
                "severity": ValidationSeverity.ERROR
            },
            {
                "name": "technical_indicators_range", 
                "table": "enhanced_market_data",
                "query": "SELECT COUNT(*) FROM enhanced_market_data WHERE rsi_14 < 0 OR rsi_14 > 100",
                "description": "RSI values must be between 0 and 100",
                "severity": ValidationSeverity.ERROR
            }
        ]
    
    async def validate_all(self, session: AsyncSession) -> ValidationResult:
        """
        Run comprehensive database validation
        """
        logger.info("Starting comprehensive database validation")
        
        result = ValidationResult()
        
        try:
            # Validate foreign key relationships
            relationship_issues = await self._validate_relationships(session)
            result.relationship_violations.extend(relationship_issues)
            result.issues.extend(relationship_issues)
            
            # Validate database constraints
            constraint_issues = await self._validate_constraints(session)
            result.constraint_violations.extend(constraint_issues) 
            result.issues.extend(constraint_issues)
            
            # Validate business rules
            business_rule_issues = await self._validate_business_rules(session)
            result.data_integrity_issues.extend(business_rule_issues)
            result.issues.extend(business_rule_issues)
            
            # Check for performance issues
            performance_issues = await self._check_performance_issues(session)
            result.performance_issues.extend(performance_issues)
            result.issues.extend(performance_issues)
            
            # Generate summary
            result.summary = self._generate_summary(result)
            result.validation_score = self._calculate_validation_score(result)
            
            logger.info(f"Database validation completed. Score: {result.validation_score:.1f}/100")
            
        except Exception as e:
            logger.error(f"Database validation failed: {e}")
            result.issues.append(ValidationIssue(
                severity=ValidationSeverity.CRITICAL,
                category="validation_error",
                table_name="system",
                description=f"Validation process failed: {e}"
            ))
        
        return result
    
    async def _validate_relationships(self, session: AsyncSession) -> List[ValidationIssue]:
        """Validate foreign key relationships"""
        issues = []
        
        for rel in self.relationships:
            try:
                # Check for orphaned records (child without parent)
                orphan_query = f"""
                    SELECT COUNT(*) 
                    FROM {rel.child_table} c
                    LEFT JOIN {rel.parent_table} p ON c.{rel.child_column} = p.{rel.parent_column}
                    WHERE p.{rel.parent_column} IS NULL 
                    AND c.{rel.child_column} IS NOT NULL
                """
                
                result = await session.execute(text(orphan_query))
                orphan_count = result.scalar()
                
                if orphan_count > 0:
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        category="orphaned_records",
                        table_name=rel.child_table,
                        column_name=rel.child_column,
                        description=f"Found {orphan_count} orphaned records in {rel.child_table}.{rel.child_column} referencing {rel.parent_table}.{rel.parent_column}",
                        affected_rows=orphan_count,
                        recommendation=f"Remove orphaned records or restore missing parent records in {rel.parent_table}",
                        sql_query=orphan_query
                    ))
                
                # Check for null violations if not nullable
                if not rel.is_nullable:
                    null_query = f"""
                        SELECT COUNT(*) 
                        FROM {rel.child_table}
                        WHERE {rel.child_column} IS NULL
                    """
                    
                    result = await session.execute(text(null_query))
                    null_count = result.scalar()
                    
                    if null_count > 0:
                        issues.append(ValidationIssue(
                            severity=ValidationSeverity.ERROR,
                            category="null_constraint_violation",
                            table_name=rel.child_table,
                            column_name=rel.child_column,
                            description=f"Found {null_count} null values in non-nullable foreign key {rel.child_table}.{rel.child_column}",
                            affected_rows=null_count,
                            recommendation=f"Set valid foreign key values for {rel.child_table}.{rel.child_column}",
                            sql_query=null_query
                        ))
                
                logger.debug(f"Validated relationship: {rel.parent_table} -> {rel.child_table}")
                
            except Exception as e:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    category="relationship_check_error", 
                    table_name=rel.child_table,
                    description=f"Failed to validate relationship {rel.parent_table} -> {rel.child_table}: {e}"
                ))
        
        return issues
    
    async def _validate_constraints(self, session: AsyncSession) -> List[ValidationIssue]:
        """Validate database constraints"""
        issues = []
        
        try:
            # Check constraint violations from PostgreSQL system tables
            constraint_query = """
                SELECT 
                    tc.table_name,
                    tc.constraint_name,
                    tc.constraint_type,
                    cc.check_clause
                FROM information_schema.table_constraints tc
                LEFT JOIN information_schema.check_constraints cc ON tc.constraint_name = cc.constraint_name
                WHERE tc.table_schema = 'public'
                AND tc.constraint_type IN ('CHECK', 'UNIQUE', 'PRIMARY KEY')
                ORDER BY tc.table_name, tc.constraint_name;
            """
            
            result = await session.execute(text(constraint_query))
            constraints = result.fetchall()
            
            for constraint in constraints:
                table_name = constraint.table_name
                constraint_name = constraint.constraint_name
                constraint_type = constraint.constraint_type
                
                # For check constraints, we can validate the condition
                if constraint_type == 'CHECK' and constraint.check_clause:
                    try:
                        # This is a simplified check - in practice, you'd need to parse the check clause
                        validation_query = f"""
                            SELECT COUNT(*) 
                            FROM {table_name} 
                            WHERE NOT ({constraint.check_clause})
                        """
                        
                        violation_result = await session.execute(text(validation_query))
                        violation_count = violation_result.scalar()
                        
                        if violation_count > 0:
                            issues.append(ValidationIssue(
                                severity=ValidationSeverity.ERROR,
                                category="check_constraint_violation",
                                table_name=table_name,
                                constraint_name=constraint_name,
                                description=f"Check constraint '{constraint_name}' violated in {violation_count} rows",
                                affected_rows=violation_count,
                                recommendation=f"Fix data that violates constraint: {constraint.check_clause}"
                            ))
                            
                    except Exception as e:
                        logger.debug(f"Could not validate check constraint {constraint_name}: {e}")
        
        except Exception as e:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category="constraint_validation_error",
                table_name="system",
                description=f"Failed to validate constraints: {e}"
            ))
        
        return issues
    
    async def _validate_business_rules(self, session: AsyncSession) -> List[ValidationIssue]:
        """Validate business logic rules"""
        issues = []
        
        for rule in self.business_rules:
            try:
                result = await session.execute(text(rule["query"]))
                violation_count = result.scalar()
                
                if violation_count > 0:
                    issues.append(ValidationIssue(
                        severity=rule["severity"],
                        category="business_rule_violation",
                        table_name=rule["table"],
                        description=f"{rule['description']} - Found {violation_count} violations",
                        affected_rows=violation_count,
                        recommendation=f"Review and fix data in {rule['table']} that violates: {rule['name']}",
                        sql_query=rule["query"]
                    ))
                
                logger.debug(f"Validated business rule: {rule['name']}")
                
            except Exception as e:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    category="business_rule_check_error",
                    table_name=rule["table"],
                    description=f"Failed to validate business rule '{rule['name']}': {e}"
                ))
        
        return issues
    
    async def _check_performance_issues(self, session: AsyncSession) -> List[ValidationIssue]:
        """Check for potential performance issues in relationships"""
        issues = []
        
        try:
            # Check for missing indexes on foreign keys
            missing_fk_indexes_query = """
                SELECT 
                    tc.table_name,
                    kcu.column_name,
                    tc.constraint_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu ON tc.constraint_name = kcu.constraint_name
                WHERE tc.constraint_type = 'FOREIGN KEY'
                AND tc.table_schema = 'public'
                AND NOT EXISTS (
                    SELECT 1 FROM pg_indexes i
                    WHERE i.tablename = tc.table_name 
                    AND i.indexdef LIKE '%' || kcu.column_name || '%'
                );
            """
            
            result = await session.execute(text(missing_fk_indexes_query))
            missing_indexes = result.fetchall()
            
            for missing_idx in missing_indexes:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    category="missing_foreign_key_index",
                    table_name=missing_idx.table_name,
                    column_name=missing_idx.column_name, 
                    description=f"Foreign key column {missing_idx.column_name} lacks index for optimal performance",
                    recommendation=f"CREATE INDEX ON {missing_idx.table_name} ({missing_idx.column_name})"
                ))
            
            # Check for large tables without appropriate partitioning
            large_table_query = """
                SELECT 
                    tablename,
                    n_live_tup as row_count,
                    pg_size_pretty(pg_total_relation_size(tablename::regclass)) as size
                FROM pg_stat_user_tables 
                WHERE n_live_tup > 1000000  -- Tables with more than 1M rows
                ORDER BY n_live_tup DESC;
            """
            
            result = await session.execute(text(large_table_query))
            large_tables = result.fetchall()
            
            for table in large_tables:
                # Check if it's a time-series table that should be partitioned
                if table.tablename in ['enhanced_market_data', 'enhanced_transactions', 'user_activity_log']:
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.INFO,
                        category="partitioning_recommendation",
                        table_name=table.tablename,
                        description=f"Large table {table.tablename} ({table.size}, {table.row_count:,} rows) could benefit from partitioning",
                        recommendation="Consider implementing table partitioning for better performance"
                    ))
        
        except Exception as e:
            logger.warning(f"Performance issue check failed: {e}")
        
        return issues
    
    def _generate_summary(self, result: ValidationResult) -> Dict[str, int]:
        """Generate validation summary statistics"""
        summary = {
            "total_issues": len(result.issues),
            "critical_issues": len([i for i in result.issues if i.severity == ValidationSeverity.CRITICAL]),
            "error_issues": len([i for i in result.issues if i.severity == ValidationSeverity.ERROR]),
            "warning_issues": len([i for i in result.issues if i.severity == ValidationSeverity.WARNING]),
            "info_issues": len([i for i in result.issues if i.severity == ValidationSeverity.INFO]),
            "relationship_violations": len(result.relationship_violations),
            "constraint_violations": len(result.constraint_violations),
            "business_rule_violations": len(result.data_integrity_issues),
            "performance_issues": len(result.performance_issues)
        }
        
        return summary
    
    def _calculate_validation_score(self, result: ValidationResult) -> float:
        """Calculate overall validation score (0-100)"""
        score = 100.0
        
        # Deduct points based on severity
        score -= result.summary["critical_issues"] * 25  # Critical issues: -25 points each
        score -= result.summary["error_issues"] * 10     # Error issues: -10 points each
        score -= result.summary["warning_issues"] * 5    # Warning issues: -5 points each
        score -= result.summary["info_issues"] * 1       # Info issues: -1 point each
        
        return max(score, 0.0)
    
    async def generate_validation_report(self) -> Dict[str, Any]:
        """Generate comprehensive validation report"""
        logger.info("Generating database validation report")
        
        try:
            async with db_manager.get_async_session() as session:
                result = await self.validate_all(session)
                
                report = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "validation_score": result.validation_score,
                    "validation_grade": self._get_validation_grade(result.validation_score),
                    "summary": result.summary,
                    "critical_issues": [
                        {
                            "severity": issue.severity.value,
                            "category": issue.category,
                            "table": issue.table_name,
                            "column": issue.column_name,
                            "description": issue.description,
                            "affected_rows": issue.affected_rows,
                            "recommendation": issue.recommendation
                        }
                        for issue in result.issues 
                        if issue.severity == ValidationSeverity.CRITICAL
                    ],
                    "error_issues": [
                        {
                            "severity": issue.severity.value,
                            "category": issue.category,
                            "table": issue.table_name,
                            "column": issue.column_name,
                            "description": issue.description,
                            "affected_rows": issue.affected_rows,
                            "recommendation": issue.recommendation
                        }
                        for issue in result.issues 
                        if issue.severity == ValidationSeverity.ERROR
                    ],
                    "relationship_issues": [
                        {
                            "category": issue.category,
                            "table": issue.table_name,
                            "column": issue.column_name,
                            "description": issue.description,
                            "affected_rows": issue.affected_rows
                        }
                        for issue in result.relationship_violations
                    ],
                    "business_rule_violations": [
                        {
                            "table": issue.table_name,
                            "description": issue.description,
                            "affected_rows": issue.affected_rows,
                            "recommendation": issue.recommendation
                        }
                        for issue in result.data_integrity_issues
                    ],
                    "performance_recommendations": [
                        {
                            "table": issue.table_name,
                            "column": issue.column_name,
                            "description": issue.description,
                            "recommendation": issue.recommendation
                        }
                        for issue in result.performance_issues
                    ]
                }
                
                logger.info(f"Validation report generated. Score: {result.validation_score:.1f}")
                return report
                
        except Exception as e:
            logger.error(f"Failed to generate validation report: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def _get_validation_grade(self, score: float) -> str:
        """Convert validation score to letter grade"""
        if score >= 95:
            return "A+"
        elif score >= 90:
            return "A"
        elif score >= 85:
            return "B+"
        elif score >= 80:
            return "B"
        elif score >= 75:
            return "C+"
        elif score >= 70:
            return "C"
        elif score >= 60:
            return "D"
        else:
            return "F"


# Global validator instance
relationship_validator = DatabaseRelationshipValidator()


async def main():
    """
    Main function for running database validation
    """
    print("Financial Planning System - Database Relationship Validator")
    print("=" * 60)
    
    # Initialize database connection
    await db_manager.initialize()
    
    try:
        # Generate comprehensive validation report
        report = await relationship_validator.generate_validation_report()
        
        if "error" in report:
            print(f"❌ Validation failed: {report['error']}")
            return
        
        # Display report summary
        print(f"\n📊 Validation Score: {report['validation_score']:.1f}/100 (Grade: {report['validation_grade']})")
        print(f"📈 Validation Summary:")
        print(f"   • Total Issues: {report['summary']['total_issues']}")
        print(f"   • Critical: {report['summary']['critical_issues']}")
        print(f"   • Errors: {report['summary']['error_issues']}")
        print(f"   • Warnings: {report['summary']['warning_issues']}")
        print(f"   • Info: {report['summary']['info_issues']}")
        
        # Display critical issues
        if report['critical_issues']:
            print(f"\n🚨 Critical Issues:")
            for issue in report['critical_issues']:
                print(f"   • {issue['table']}: {issue['description']}")
                if issue['recommendation']:
                    print(f"     → {issue['recommendation']}")
        
        # Display error issues
        if report['error_issues']:
            print(f"\n❌ Error Issues:")
            for issue in report['error_issues'][:5]:  # Show top 5
                print(f"   • {issue['table']}: {issue['description']}")
                if issue['affected_rows'] > 0:
                    print(f"     Affected rows: {issue['affected_rows']}")
        
        # Display relationship issues
        if report['relationship_issues']:
            print(f"\n🔗 Relationship Issues:")
            for issue in report['relationship_issues'][:5]:
                print(f"   • {issue['table']}.{issue['column']}: {issue['description']}")
        
        # Display performance recommendations
        if report['performance_recommendations']:
            print(f"\n⚡ Performance Recommendations:")
            for rec in report['performance_recommendations'][:3]:
                print(f"   • {rec['table']}: {rec['description']}")
        
        # Save detailed report to file
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        report_file = f"validation_report_{timestamp}.json"
        
        import json
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"\n📄 Detailed report saved to: {report_file}")
        
    finally:
        await db_manager.shutdown()


if __name__ == "__main__":
    asyncio.run(main())