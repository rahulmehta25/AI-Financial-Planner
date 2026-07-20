"""
Regulatory Compliance Engine for Financial Services

This module implements comprehensive compliance checking for:
- SEC and FINRA regulations
- Pattern Day Trader (PDT) rules
- Wash sale rules
- Good faith violations
- Anti-Money Laundering (AML) checks
- Know Your Customer (KYC) validation
- Fiduciary standards
- Audit logging and reporting
"""

import asyncio
import hashlib
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from enum import Enum
import logging
import re
from decimal import Decimal

logger = logging.getLogger(__name__)


class ComplianceStatus(Enum):
    """Compliance check status"""
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    PENDING = "pending"
    REQUIRES_REVIEW = "requires_review"


class RegulationType(Enum):
    """Types of regulations"""
    SEC = "sec"
    FINRA = "finra"
    CFTC = "cftc"
    NFA = "nfa"
    STATE = "state"
    INTERNATIONAL = "international"


class ViolationType(Enum):
    """Types of compliance violations"""
    PDT = "pattern_day_trader"
    WASH_SALE = "wash_sale"
    GOOD_FAITH = "good_faith"
    FREE_RIDING = "free_riding"
    INSIDER_TRADING = "insider_trading"
    MARKET_MANIPULATION = "market_manipulation"
    AML = "anti_money_laundering"
    KYC = "know_your_customer"
    SUITABILITY = "suitability"
    BEST_EXECUTION = "best_execution"
    FIDUCIARY = "fiduciary_duty"


@dataclass
class ComplianceCheck:
    """Individual compliance check result"""
    rule_id: str
    rule_name: str
    status: ComplianceStatus
    message: str
    severity: str  # critical, high, medium, low
    regulation: RegulationType
    violation_type: Optional[ViolationType] = None
    remediation: Optional[str] = None
    documentation: Optional[Dict] = None
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ComplianceReport:
    """Comprehensive compliance report"""
    report_id: str
    user_id: str
    checks: List[ComplianceCheck]
    overall_status: ComplianceStatus
    risk_score: float
    violations: List[ViolationType]
    recommendations: List[str]
    audit_trail: List[Dict]
    generated_at: datetime
    next_review_date: Optional[datetime] = None
    regulatory_filings: List[Dict] = field(default_factory=list)


@dataclass
class Transaction:
    """Transaction for compliance checking"""
    transaction_id: str
    user_id: str
    security_id: str
    transaction_type: str  # buy, sell, short, cover
    quantity: float
    price: float
    amount: float
    timestamp: datetime
    settlement_date: Optional[datetime] = None
    account_type: str = "cash"  # cash, margin
    metadata: Dict = field(default_factory=dict)


@dataclass
class UserProfile:
    """User profile for compliance checking"""
    user_id: str
    account_value: float
    account_type: str  # individual, joint, ira, etc.
    is_pattern_day_trader: bool = False
    is_accredited_investor: bool = False
    risk_tolerance: str = "moderate"
    investment_objectives: List[str] = field(default_factory=list)
    kyc_status: str = "pending"
    aml_risk_score: float = 0.0
    transaction_history: List[Transaction] = field(default_factory=list)
    restrictions: List[str] = field(default_factory=list)
    last_review_date: Optional[datetime] = None


class ComplianceEngine:
    """
    Comprehensive regulatory compliance engine for financial services
    """
    
    def __init__(self):
        """Initialize compliance engine with rules and configurations"""
        self.rules = self._initialize_rules()
        self.violation_thresholds = self._initialize_thresholds()
        self.audit_logger = AuditLogger()
        self.reporting_engine = ComplianceReportingEngine()
        
    def _initialize_rules(self) -> Dict[str, Dict]:
        """Initialize compliance rules database"""
        return {
            # Pattern Day Trader Rules
            'pdt_minimum_equity': {
                'rule_id': 'FINRA-4210',
                'name': 'Pattern Day Trader Minimum Equity',
                'regulation': RegulationType.FINRA,
                'violation_type': ViolationType.PDT,
                'threshold': 25000,
                'severity': 'critical',
                'description': 'Pattern day traders must maintain minimum equity of $25,000'
            },
            'pdt_trade_limit': {
                'rule_id': 'FINRA-2520',
                'name': 'Day Trade Buying Power',
                'regulation': RegulationType.FINRA,
                'violation_type': ViolationType.PDT,
                'threshold': 4,  # 4x maintenance margin excess
                'severity': 'high',
                'description': 'Day trade buying power limited to 4x maintenance margin excess'
            },
            
            # Wash Sale Rules
            'wash_sale_period': {
                'rule_id': 'IRS-1091',
                'name': 'Wash Sale Rule',
                'regulation': RegulationType.SEC,
                'violation_type': ViolationType.WASH_SALE,
                'threshold': 30,  # days
                'severity': 'high',
                'description': 'No loss deduction if substantially identical security purchased within 30 days'
            },
            
            # Good Faith Violations
            'good_faith_settlement': {
                'rule_id': 'REG-T',
                'name': 'Good Faith Settlement',
                'regulation': RegulationType.SEC,
                'violation_type': ViolationType.GOOD_FAITH,
                'threshold': 2,  # T+2 settlement
                'severity': 'medium',
                'description': 'Securities must be paid for before being sold'
            },
            
            # Free Riding
            'free_riding': {
                'rule_id': 'REG-T-90',
                'name': 'Free Riding Prevention',
                'regulation': RegulationType.SEC,
                'violation_type': ViolationType.FREE_RIDING,
                'threshold': 90,  # day restriction
                'severity': 'high',
                'description': 'Account restricted for 90 days after free riding violation'
            },
            
            # AML Rules
            'aml_transaction_threshold': {
                'rule_id': 'BSA-CTR',
                'name': 'Currency Transaction Report',
                'regulation': RegulationType.SEC,
                'violation_type': ViolationType.AML,
                'threshold': 10000,  # USD
                'severity': 'critical',
                'description': 'Transactions over $10,000 require CTR filing'
            },
            'aml_suspicious_activity': {
                'rule_id': 'BSA-SAR',
                'name': 'Suspicious Activity Report',
                'regulation': RegulationType.SEC,
                'violation_type': ViolationType.AML,
                'threshold': 5000,  # USD
                'severity': 'critical',
                'description': 'Suspicious transactions over $5,000 require SAR filing'
            },
            
            # Suitability Rules
            'suitability_rule': {
                'rule_id': 'FINRA-2111',
                'name': 'Suitability Obligations',
                'regulation': RegulationType.FINRA,
                'violation_type': ViolationType.SUITABILITY,
                'severity': 'high',
                'description': 'Recommendations must be suitable for customer profile'
            },
            
            # Best Execution
            'best_execution': {
                'rule_id': 'FINRA-5310',
                'name': 'Best Execution Rule',
                'regulation': RegulationType.FINRA,
                'violation_type': ViolationType.BEST_EXECUTION,
                'severity': 'high',
                'description': 'Must use reasonable diligence to obtain best execution'
            },
            
            # Fiduciary Duty
            'fiduciary_standard': {
                'rule_id': 'SEC-IA-1940',
                'name': 'Fiduciary Standard',
                'regulation': RegulationType.SEC,
                'violation_type': ViolationType.FIDUCIARY,
                'severity': 'critical',
                'description': 'Must act in best interest of client'
            }
        }
    
    def _initialize_thresholds(self) -> Dict[str, Any]:
        """Initialize violation thresholds and limits"""
        return {
            'pdt_trades_per_week': 4,
            'wash_sale_days': 30,
            'settlement_days': 2,
            'free_ride_restriction_days': 90,
            'aml_daily_limit': 10000,
            'aml_suspicious_amount': 5000,
            'margin_call_deadline_hours': 24,
            'concentration_limit': 0.25,  # 25% in single position
            'leverage_limit': 2.0,  # 2:1 for retail
            'options_level_requirements': {
                0: {'experience': 0, 'net_worth': 0},
                1: {'experience': 1, 'net_worth': 25000},
                2: {'experience': 2, 'net_worth': 50000},
                3: {'experience': 3, 'net_worth': 100000},
                4: {'experience': 5, 'net_worth': 250000}
            }
        }
    
    async def validate_transaction(
        self,
        transaction: Transaction,
        user_profile: UserProfile
    ) -> ComplianceReport:
        """
        Validate a transaction for regulatory compliance
        
        Args:
            transaction: Transaction to validate
            user_profile: User profile for context
            
        Returns:
            Compliance report with validation results
        """
        checks = []
        violations = []
        
        # Start audit trail
        audit_trail = [{
            'timestamp': datetime.now().isoformat(),
            'action': 'transaction_validation_started',
            'transaction_id': transaction.transaction_id,
            'user_id': user_profile.user_id
        }]
        
        # Run compliance checks in parallel
        check_tasks = [
            self._check_pdt_rules(transaction, user_profile),
            self._check_wash_sale(transaction, user_profile),
            self._check_good_faith(transaction, user_profile),
            self._check_free_riding(transaction, user_profile),
            self._check_aml(transaction, user_profile),
            self._check_suitability(transaction, user_profile),
            self._check_concentration_limits(transaction, user_profile),
            self._check_margin_requirements(transaction, user_profile)
        ]
        
        check_results = await asyncio.gather(*check_tasks)
        
        # Process check results
        for check in check_results:
            if check:
                checks.append(check)
                if check.status == ComplianceStatus.FAILED:
                    violations.append(check.violation_type)
                
                # Add to audit trail
                audit_trail.append({
                    'timestamp': check.timestamp.isoformat(),
                    'rule': check.rule_name,
                    'status': check.status.value,
                    'message': check.message
                })
        
        # Determine overall status
        overall_status = self._determine_overall_status(checks)
        
        # Calculate risk score
        risk_score = self._calculate_compliance_risk_score(checks, violations)
        
        # Generate recommendations
        recommendations = self._generate_compliance_recommendations(
            checks, violations, user_profile
        )
        
        # Check if regulatory filings are needed
        regulatory_filings = await self._check_regulatory_filings(
            transaction, violations
        )
        
        # Create compliance report
        report = ComplianceReport(
            report_id=self._generate_report_id(),
            user_id=user_profile.user_id,
            checks=checks,
            overall_status=overall_status,
            risk_score=risk_score,
            violations=violations,
            recommendations=recommendations,
            audit_trail=audit_trail,
            generated_at=datetime.now(),
            next_review_date=datetime.now() + timedelta(days=30),
            regulatory_filings=regulatory_filings
        )
        
        # Log to audit system
        await self.audit_logger.log_compliance_check(report)
        
        return report
    
    async def _check_pdt_rules(
        self,
        transaction: Transaction,
        user_profile: UserProfile
    ) -> Optional[ComplianceCheck]:
        """Check Pattern Day Trader rules"""
        
        rule = self.rules['pdt_minimum_equity']
        
        # Check if user is flagged as PDT
        if user_profile.is_pattern_day_trader:
            if user_profile.account_value < rule['threshold']:
                return ComplianceCheck(
                    rule_id=rule['rule_id'],
                    rule_name=rule['name'],
                    status=ComplianceStatus.FAILED,
                    message=f"PDT account below minimum equity of ${rule['threshold']:,}",
                    severity=rule['severity'],
                    regulation=rule['regulation'],
                    violation_type=rule['violation_type'],
                    remediation="Deposit funds to meet minimum equity requirement or close positions"
                )
        
        # Check day trading frequency
        day_trades = self._count_day_trades(
            user_profile.transaction_history,
            lookback_days=5
        )
        
        if day_trades >= 4 and not user_profile.is_pattern_day_trader:
            return ComplianceCheck(
                rule_id=rule['rule_id'],
                rule_name="Pattern Day Trader Classification",
                status=ComplianceStatus.WARNING,
                message=f"Account will be flagged as PDT ({day_trades} day trades in 5 days)",
                severity="high",
                regulation=RegulationType.FINRA,
                violation_type=ViolationType.PDT,
                remediation="Reduce day trading activity or ensure $25,000 minimum equity"
            )
        
        return ComplianceCheck(
            rule_id=rule['rule_id'],
            rule_name=rule['name'],
            status=ComplianceStatus.PASSED,
            message="PDT rules compliance verified",
            severity="low",
            regulation=rule['regulation']
        )
    
    async def _check_wash_sale(
        self,
        transaction: Transaction,
        user_profile: UserProfile
    ) -> Optional[ComplianceCheck]:
        """Check for wash sale violations"""
        
        rule = self.rules['wash_sale_period']
        
        if transaction.transaction_type != 'sell':
            return None
        
        # Check for repurchase within wash sale period
        lookback_date = transaction.timestamp - timedelta(days=rule['threshold'])
        lookahead_date = transaction.timestamp + timedelta(days=rule['threshold'])
        
        for hist_trans in user_profile.transaction_history:
            if (hist_trans.security_id == transaction.security_id and
                hist_trans.transaction_type == 'buy' and
                lookback_date <= hist_trans.timestamp <= lookahead_date and
                hist_trans.transaction_id != transaction.transaction_id):
                
                return ComplianceCheck(
                    rule_id=rule['rule_id'],
                    rule_name=rule['name'],
                    status=ComplianceStatus.WARNING,
                    message=f"Potential wash sale detected for {transaction.security_id}",
                    severity=rule['severity'],
                    regulation=rule['regulation'],
                    violation_type=rule['violation_type'],
                    remediation="Loss deduction may be disallowed for tax purposes",
                    documentation={'related_transaction': hist_trans.transaction_id}
                )
        
        return ComplianceCheck(
            rule_id=rule['rule_id'],
            rule_name=rule['name'],
            status=ComplianceStatus.PASSED,
            message="No wash sale violation detected",
            severity="low",
            regulation=rule['regulation']
        )
    
    async def _check_good_faith(
        self,
        transaction: Transaction,
        user_profile: UserProfile
    ) -> Optional[ComplianceCheck]:
        """Check for good faith violations"""
        
        rule = self.rules['good_faith_settlement']
        
        if transaction.account_type != 'cash':
            return None  # Only applies to cash accounts
        
        # Check if selling securities bought with unsettled funds
        if transaction.transaction_type == 'sell':
            # Find corresponding buy transaction
            for hist_trans in user_profile.transaction_history:
                if (hist_trans.security_id == transaction.security_id and
                    hist_trans.transaction_type == 'buy' and
                    hist_trans.timestamp < transaction.timestamp):
                    
                    # Check if buy transaction has settled
                    if hist_trans.settlement_date and hist_trans.settlement_date > transaction.timestamp:
                        return ComplianceCheck(
                            rule_id=rule['rule_id'],
                            rule_name=rule['name'],
                            status=ComplianceStatus.FAILED,
                            message="Good faith violation: Selling securities bought with unsettled funds",
                            severity=rule['severity'],
                            regulation=rule['regulation'],
                            violation_type=rule['violation_type'],
                            remediation="Wait for funds to settle before selling",
                            documentation={'unsettled_transaction': hist_trans.transaction_id}
                        )
        
        return ComplianceCheck(
            rule_id=rule['rule_id'],
            rule_name=rule['name'],
            status=ComplianceStatus.PASSED,
            message="Good faith requirement satisfied",
            severity="low",
            regulation=rule['regulation']
        )
    
    async def _check_free_riding(
        self,
        transaction: Transaction,
        user_profile: UserProfile
    ) -> Optional[ComplianceCheck]:
        """Check for free riding violations"""
        
        rule = self.rules['free_riding']
        
        if transaction.account_type != 'cash':
            return None
        
        # Check if buying and selling before payment
        if transaction.transaction_type == 'sell':
            for hist_trans in user_profile.transaction_history:
                if (hist_trans.security_id == transaction.security_id and
                    hist_trans.transaction_type == 'buy'):
                    
                    # Check if sold before payment for purchase
                    days_between = (transaction.timestamp - hist_trans.timestamp).days
                    if days_between < 2 and not hist_trans.metadata.get('paid', False):
                        return ComplianceCheck(
                            rule_id=rule['rule_id'],
                            rule_name=rule['name'],
                            status=ComplianceStatus.FAILED,
                            message="Free riding violation detected",
                            severity=rule['severity'],
                            regulation=rule['regulation'],
                            violation_type=rule['violation_type'],
                            remediation=f"Account will be restricted for {rule['threshold']} days",
                            documentation={'violation_date': transaction.timestamp.isoformat()}
                        )
        
        return ComplianceCheck(
            rule_id=rule['rule_id'],
            rule_name=rule['name'],
            status=ComplianceStatus.PASSED,
            message="No free riding violation",
            severity="low",
            regulation=rule['regulation']
        )
    
    async def _check_aml(
        self,
        transaction: Transaction,
        user_profile: UserProfile
    ) -> ComplianceCheck:
        """Check Anti-Money Laundering compliance"""
        
        ctr_rule = self.rules['aml_transaction_threshold']
        sar_rule = self.rules['aml_suspicious_activity']
        
        # Check transaction amount thresholds
        if transaction.amount >= ctr_rule['threshold']:
            return ComplianceCheck(
                rule_id=ctr_rule['rule_id'],
                rule_name=ctr_rule['name'],
                status=ComplianceStatus.REQUIRES_REVIEW,
                message=f"Transaction exceeds CTR threshold of ${ctr_rule['threshold']:,}",
                severity=ctr_rule['severity'],
                regulation=ctr_rule['regulation'],
                violation_type=ctr_rule['violation_type'],
                remediation="File Currency Transaction Report (CTR)",
                documentation={'amount': transaction.amount, 'requires_ctr': True}
            )
        
        # Check for suspicious patterns
        suspicious_score = await self._calculate_suspicious_activity_score(
            transaction, user_profile
        )
        
        if suspicious_score > 0.7:
            return ComplianceCheck(
                rule_id=sar_rule['rule_id'],
                rule_name=sar_rule['name'],
                status=ComplianceStatus.REQUIRES_REVIEW,
                message="Suspicious activity detected",
                severity=sar_rule['severity'],
                regulation=sar_rule['regulation'],
                violation_type=sar_rule['violation_type'],
                remediation="Review transaction and consider filing SAR",
                documentation={'suspicious_score': suspicious_score, 'requires_sar': True}
            )
        
        return ComplianceCheck(
            rule_id=ctr_rule['rule_id'],
            rule_name="AML Compliance",
            status=ComplianceStatus.PASSED,
            message="AML checks passed",
            severity="low",
            regulation=RegulationType.SEC
        )
    
    async def _check_suitability(
        self,
        transaction: Transaction,
        user_profile: UserProfile
    ) -> ComplianceCheck:
        """Check investment suitability"""
        
        rule = self.rules['suitability_rule']
        
        # Analyze transaction suitability based on user profile
        suitability_score = self._calculate_suitability_score(
            transaction, user_profile
        )
        
        if suitability_score < 0.5:
            return ComplianceCheck(
                rule_id=rule['rule_id'],
                rule_name=rule['name'],
                status=ComplianceStatus.WARNING,
                message="Transaction may not be suitable for customer profile",
                severity=rule['severity'],
                regulation=rule['regulation'],
                violation_type=rule['violation_type'],
                remediation="Review customer objectives and risk tolerance",
                documentation={'suitability_score': suitability_score}
            )
        
        return ComplianceCheck(
            rule_id=rule['rule_id'],
            rule_name=rule['name'],
            status=ComplianceStatus.PASSED,
            message="Transaction suitable for customer profile",
            severity="low",
            regulation=rule['regulation']
        )
    
    async def _check_concentration_limits(
        self,
        transaction: Transaction,
        user_profile: UserProfile
    ) -> ComplianceCheck:
        """Check position concentration limits"""
        
        # Calculate position concentration after transaction
        position_value = transaction.quantity * transaction.price
        total_value = user_profile.account_value + position_value
        concentration = position_value / total_value if total_value > 0 else 0
        
        if concentration > self.violation_thresholds['concentration_limit']:
            return ComplianceCheck(
                rule_id="INTERNAL-001",
                rule_name="Position Concentration Limit",
                status=ComplianceStatus.WARNING,
                message=f"Position concentration ({concentration:.1%}) exceeds limit",
                severity="medium",
                regulation=RegulationType.SEC,
                violation_type=ViolationType.SUITABILITY,
                remediation="Consider diversifying portfolio",
                documentation={'concentration': concentration}
            )
        
        return ComplianceCheck(
            rule_id="INTERNAL-001",
            rule_name="Position Concentration",
            status=ComplianceStatus.PASSED,
            message="Position concentration within limits",
            severity="low",
            regulation=RegulationType.SEC
        )
    
    async def _check_margin_requirements(
        self,
        transaction: Transaction,
        user_profile: UserProfile
    ) -> Optional[ComplianceCheck]:
        """Check margin requirements for leveraged transactions"""
        
        if transaction.account_type != 'margin':
            return None
        
        # Calculate margin requirements (simplified)
        margin_required = transaction.amount * 0.5  # 50% initial margin
        available_margin = user_profile.account_value * 0.5
        
        if margin_required > available_margin:
            return ComplianceCheck(
                rule_id="REG-T-MARGIN",
                rule_name="Margin Requirements",
                status=ComplianceStatus.FAILED,
                message="Insufficient margin for transaction",
                severity="high",
                regulation=RegulationType.SEC,
                violation_type=ViolationType.GOOD_FAITH,
                remediation="Deposit additional funds or reduce position size",
                documentation={'margin_required': margin_required, 'available': available_margin}
            )
        
        return ComplianceCheck(
            rule_id="REG-T-MARGIN",
            rule_name="Margin Requirements",
            status=ComplianceStatus.PASSED,
            message="Margin requirements satisfied",
            severity="low",
            regulation=RegulationType.SEC
        )
    
    def _count_day_trades(
        self,
        transactions: List[Transaction],
        lookback_days: int
    ) -> int:
        """Count day trades in lookback period"""
        
        cutoff_date = datetime.now() - timedelta(days=lookback_days)
        day_trades = 0
        
        # Group transactions by security and date
        trades_by_security_date = {}
        for trans in transactions:
            if trans.timestamp >= cutoff_date:
                key = (trans.security_id, trans.timestamp.date())
                if key not in trades_by_security_date:
                    trades_by_security_date[key] = []
                trades_by_security_date[key].append(trans)
        
        # Count round trips (buy and sell same day)
        for trades in trades_by_security_date.values():
            buys = [t for t in trades if t.transaction_type == 'buy']
            sells = [t for t in trades if t.transaction_type == 'sell']
            if buys and sells:
                day_trades += min(len(buys), len(sells))
        
        return day_trades
    
    async def _calculate_suspicious_activity_score(
        self,
        transaction: Transaction,
        user_profile: UserProfile
    ) -> float:
        """Calculate suspicious activity score for AML"""
        
        score = 0.0
        factors = []
        
        # Large transaction relative to history
        avg_transaction = np.mean([t.amount for t in user_profile.transaction_history[-30:]]) if user_profile.transaction_history else 0
        if avg_transaction > 0 and transaction.amount > 5 * avg_transaction:
            score += 0.3
            factors.append("unusually_large_transaction")
        
        # Rapid in/out transactions
        recent_transactions = [
            t for t in user_profile.transaction_history
            if (transaction.timestamp - t.timestamp).days <= 3
        ]
        if len(recent_transactions) > 10:
            score += 0.2
            factors.append("rapid_trading")
        
        # Round amounts (potential structuring)
        if transaction.amount % 1000 == 0 and transaction.amount >= 5000:
            score += 0.1
            factors.append("round_amount")
        
        # High-risk jurisdictions (simplified)
        if transaction.metadata.get('jurisdiction') in ['offshore', 'high_risk']:
            score += 0.3
            factors.append("high_risk_jurisdiction")
        
        # User AML risk score
        score += user_profile.aml_risk_score * 0.1
        
        logger.info(f"Suspicious activity score: {score}, factors: {factors}")
        
        return min(score, 1.0)
    
    def _calculate_suitability_score(
        self,
        transaction: Transaction,
        user_profile: UserProfile
    ) -> float:
        """Calculate transaction suitability score"""
        
        score = 1.0
        
        # Check risk alignment
        transaction_risk = transaction.metadata.get('risk_level', 'medium')
        risk_alignment = {
            ('conservative', 'high'): 0.2,
            ('conservative', 'medium'): 0.5,
            ('conservative', 'low'): 1.0,
            ('moderate', 'high'): 0.5,
            ('moderate', 'medium'): 1.0,
            ('moderate', 'low'): 0.8,
            ('aggressive', 'high'): 1.0,
            ('aggressive', 'medium'): 0.8,
            ('aggressive', 'low'): 0.5
        }
        
        score *= risk_alignment.get(
            (user_profile.risk_tolerance, transaction_risk),
            0.5
        )
        
        # Check investment objectives alignment
        transaction_objective = transaction.metadata.get('objective', 'growth')
        if transaction_objective in user_profile.investment_objectives:
            score *= 1.0
        else:
            score *= 0.7
        
        # Check concentration
        position_pct = transaction.amount / user_profile.account_value if user_profile.account_value > 0 else 1.0
        if position_pct > 0.2:  # More than 20% in one position
            score *= 0.7
        
        return score
    
    def _determine_overall_status(
        self,
        checks: List[ComplianceCheck]
    ) -> ComplianceStatus:
        """Determine overall compliance status from individual checks"""
        
        if any(c.status == ComplianceStatus.FAILED for c in checks):
            return ComplianceStatus.FAILED
        elif any(c.status == ComplianceStatus.REQUIRES_REVIEW for c in checks):
            return ComplianceStatus.REQUIRES_REVIEW
        elif any(c.status == ComplianceStatus.WARNING for c in checks):
            return ComplianceStatus.WARNING
        else:
            return ComplianceStatus.PASSED
    
    def _calculate_compliance_risk_score(
        self,
        checks: List[ComplianceCheck],
        violations: List[ViolationType]
    ) -> float:
        """Calculate overall compliance risk score"""
        
        score = 0.0
        
        # Weight by severity
        severity_weights = {
            'critical': 1.0,
            'high': 0.7,
            'medium': 0.4,
            'low': 0.1
        }
        
        for check in checks:
            if check.status in [ComplianceStatus.FAILED, ComplianceStatus.WARNING]:
                score += severity_weights.get(check.severity, 0.5)
        
        # Add violation type weights
        violation_weights = {
            ViolationType.INSIDER_TRADING: 1.0,
            ViolationType.MARKET_MANIPULATION: 1.0,
            ViolationType.AML: 0.9,
            ViolationType.FIDUCIARY: 0.8,
            ViolationType.PDT: 0.6,
            ViolationType.WASH_SALE: 0.5,
            ViolationType.GOOD_FAITH: 0.4
        }
        
        for violation in violations:
            score += violation_weights.get(violation, 0.3)
        
        # Normalize to 0-100
        return min(score * 20, 100)
    
    def _generate_compliance_recommendations(
        self,
        checks: List[ComplianceCheck],
        violations: List[ViolationType],
        user_profile: UserProfile
    ) -> List[str]:
        """Generate compliance recommendations"""
        
        recommendations = []
        
        # Based on violations
        if ViolationType.PDT in violations:
            recommendations.append("Maintain minimum equity of $25,000 or reduce day trading frequency")
        
        if ViolationType.WASH_SALE in violations:
            recommendations.append("Wait 31 days before repurchasing securities sold at a loss")
        
        if ViolationType.GOOD_FAITH in violations:
            recommendations.append("Ensure funds are settled before selling securities in cash account")
        
        if ViolationType.AML in violations:
            recommendations.append("Complete enhanced due diligence and file required reports")
        
        # Based on warnings
        for check in checks:
            if check.status == ComplianceStatus.WARNING and check.remediation:
                recommendations.append(check.remediation)
        
        # General recommendations
        if user_profile.kyc_status != 'verified':
            recommendations.append("Complete KYC verification for full account access")
        
        if not user_profile.last_review_date or (datetime.now() - user_profile.last_review_date).days > 365:
            recommendations.append("Schedule annual compliance review")
        
        return recommendations
    
    async def _check_regulatory_filings(
        self,
        transaction: Transaction,
        violations: List[ViolationType]
    ) -> List[Dict]:
        """Check if regulatory filings are required"""
        
        filings = []
        
        # Check for CTR requirement
        if transaction.amount >= 10000:
            filings.append({
                'type': 'CTR',
                'form': 'FinCEN Form 112',
                'deadline': (transaction.timestamp + timedelta(days=15)).isoformat(),
                'status': 'required'
            })
        
        # Check for SAR requirement
        if ViolationType.AML in violations or transaction.amount >= 5000:
            filings.append({
                'type': 'SAR',
                'form': 'FinCEN Form 111',
                'deadline': (transaction.timestamp + timedelta(days=30)).isoformat(),
                'status': 'review_required'
            })
        
        # Check for Form 13F (large holdings)
        if transaction.amount >= 100000000:  # $100M
            filings.append({
                'type': '13F',
                'form': 'SEC Form 13F',
                'deadline': 'Quarterly',
                'status': 'required'
            })
        
        return filings
    
    def _generate_report_id(self) -> str:
        """Generate unique report ID"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        random_suffix = hashlib.md5(str(datetime.now().timestamp()).encode()).hexdigest()[:8]
        return f"COMP-{timestamp}-{random_suffix}"


class AuditLogger:
    """Audit logging for compliance activities"""
    
    async def log_compliance_check(self, report: ComplianceReport):
        """Log compliance check to audit system"""
        audit_entry = {
            'timestamp': report.generated_at.isoformat(),
            'report_id': report.report_id,
            'user_id': report.user_id,
            'overall_status': report.overall_status.value,
            'risk_score': report.risk_score,
            'violations': [v.value for v in report.violations],
            'checks_performed': len(report.checks),
            'regulatory_filings': report.regulatory_filings
        }
        
        # In production, write to secure audit log
        logger.info(f"Compliance audit: {json.dumps(audit_entry)}")


class ComplianceReportingEngine:
    """Generate regulatory compliance reports"""
    
    async def generate_regulatory_report(
        self,
        report_type: str,
        start_date: datetime,
        end_date: datetime,
        user_id: Optional[str] = None
    ) -> Dict:
        """Generate regulatory compliance report"""
        
        # Implementation would pull from audit logs and generate required reports
        return {
            'report_type': report_type,
            'period': f"{start_date.date()} to {end_date.date()}",
            'generated_at': datetime.now().isoformat(),
            'status': 'generated'
        }


# Import numpy for calculations
try:
    import numpy as np
except ImportError:
    # Fallback for basic statistics if numpy not available
    class np:
        @staticmethod
        def mean(values):
            return sum(values) / len(values) if values else 0


if __name__ == "__main__":
    # Example usage
    async def test_compliance():
        engine = ComplianceEngine()
        
        # Create test transaction
        transaction = Transaction(
            transaction_id="TXN-001",
            user_id="USER-001",
            security_id="AAPL",
            transaction_type="buy",
            quantity=100,
            price=150.0,
            amount=15000.0,
            timestamp=datetime.now()
        )
        
        # Create test user profile
        user_profile = UserProfile(
            user_id="USER-001",
            account_value=50000,
            account_type="individual",
            is_pattern_day_trader=False,
            risk_tolerance="moderate",
            investment_objectives=["growth", "income"]
        )
        
        # Run compliance check
        report = await engine.validate_transaction(transaction, user_profile)
        
        print(f"Compliance Status: {report.overall_status.value}")
        print(f"Risk Score: {report.risk_score:.2f}")
        print(f"Violations: {[v.value for v in report.violations]}")
        print("\nRecommendations:")
        for rec in report.recommendations:
            print(f"- {rec}")
    
    # Run test
    # asyncio.run(test_compliance())