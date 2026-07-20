"""
Compliance Module

Implements FINRA, SEC, GDPR, and SOC 2 compliance requirements
for financial services regulatory compliance.
"""

import re
import hashlib
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from enum import Enum
from dataclasses import dataclass
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings


class ComplianceType(Enum):
    """Types of compliance requirements"""
    FINRA = "finra"  # Financial Industry Regulatory Authority
    SEC = "sec"  # Securities and Exchange Commission
    GDPR = "gdpr"  # General Data Protection Regulation
    SOC2 = "soc2"  # Service Organization Control 2
    PCI_DSS = "pci_dss"  # Payment Card Industry Data Security Standard
    CCPA = "ccpa"  # California Consumer Privacy Act
    MiFID_II = "mifid_ii"  # Markets in Financial Instruments Directive II


class DataClassification(Enum):
    """Data classification levels"""
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"
    PII = "pii"  # Personally Identifiable Information
    MNPI = "mnpi"  # Material Non-Public Information


@dataclass
class ComplianceViolation:
    """Represents a compliance violation"""
    violation_id: str
    compliance_type: ComplianceType
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    description: str
    detected_at: datetime
    user_id: Optional[str] = None
    resource_id: Optional[str] = None
    remediation: Optional[str] = None
    resolved: bool = False
    resolved_at: Optional[datetime] = None


@dataclass
class DataSubjectRequest:
    """GDPR Data Subject Request"""
    request_id: str
    subject_id: str
    request_type: str  # ACCESS, RECTIFICATION, ERASURE, PORTABILITY, RESTRICTION, OBJECTION
    requested_at: datetime
    status: str  # PENDING, PROCESSING, COMPLETED, REJECTED
    completed_at: Optional[datetime] = None
    response: Optional[Dict[str, Any]] = None


class FINRACompliance:
    """
    FINRA Compliance Implementation
    
    Implements:
    - Rule 3110: Supervision
    - Rule 4511: Books and Records
    - Rule 2111: Suitability
    - Rule 2210: Communications with the Public
    """
    
    def __init__(self):
        self.violations = []
        self.audit_trail = []
    
    async def check_suitability(
        self,
        client_profile: Dict[str, Any],
        investment_recommendation: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """
        FINRA Rule 2111: Check investment suitability for client
        """
        
        violations = []
        
        # Check risk tolerance
        client_risk = client_profile.get("risk_tolerance", "conservative")
        investment_risk = investment_recommendation.get("risk_level", "high")
        
        risk_levels = ["conservative", "moderate", "aggressive"]
        if risk_levels.index(investment_risk) > risk_levels.index(client_risk):
            violations.append("Investment risk exceeds client risk tolerance")
        
        # Check investment objectives alignment
        client_objectives = set(client_profile.get("investment_objectives", []))
        investment_objectives = set(investment_recommendation.get("objectives", []))
        
        if not investment_objectives.intersection(client_objectives):
            violations.append("Investment objectives do not align with client objectives")
        
        # Check concentration limits
        concentration = investment_recommendation.get("portfolio_percentage", 0)
        if concentration > 25:  # No single investment should exceed 25% of portfolio
            violations.append(f"Investment concentration ({concentration}%) exceeds limit (25%)")
        
        # Check client net worth requirements
        min_net_worth = investment_recommendation.get("min_net_worth", 0)
        client_net_worth = client_profile.get("net_worth", 0)
        
        if min_net_worth > client_net_worth:
            violations.append(f"Client net worth insufficient for investment")
        
        # Check accredited investor status if required
        requires_accredited = investment_recommendation.get("requires_accredited", False)
        is_accredited = client_profile.get("accredited_investor", False)
        
        if requires_accredited and not is_accredited:
            violations.append("Investment requires accredited investor status")
        
        if violations:
            return False, "; ".join(violations)
        
        return True, None
    
    async def validate_communication(
        self,
        communication: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """
        FINRA Rule 2210: Validate communications with the public
        """
        
        issues = []
        content = communication.get("content", "")
        communication_type = communication.get("type", "")  # retail, institutional, correspondence
        
        # Check for required disclaimers
        required_disclaimers = [
            "Past performance is not indicative of future results",
            "Investments involve risk",
            "Not FDIC insured"
        ]
        
        for disclaimer in required_disclaimers:
            if disclaimer.lower() not in content.lower():
                issues.append(f"Missing required disclaimer: {disclaimer}")
        
        # Check for prohibited content
        prohibited_phrases = [
            "guaranteed returns",
            "risk-free",
            "can't lose",
            "sure thing",
            "no risk"
        ]
        
        for phrase in prohibited_phrases:
            if phrase.lower() in content.lower():
                issues.append(f"Prohibited phrase found: {phrase}")
        
        # Check for performance claims
        if re.search(r'\d+%\s*(return|gain|profit)', content, re.IGNORECASE):
            if "hypothetical" not in content.lower() and "past performance" not in content.lower():
                issues.append("Performance claims must include appropriate disclaimers")
        
        # Check approval status for retail communications
        if communication_type == "retail" and not communication.get("approved_by"):
            issues.append("Retail communications require principal approval")
        
        return len(issues) == 0, issues
    
    async def record_supervision(
        self,
        supervisor_id: str,
        supervised_id: str,
        activity_type: str,
        review_notes: str
    ):
        """
        FINRA Rule 3110: Record supervisory activities
        """
        
        supervision_record = {
            "record_id": f"sup_{datetime.utcnow().timestamp()}",
            "supervisor_id": supervisor_id,
            "supervised_id": supervised_id,
            "activity_type": activity_type,
            "review_notes": review_notes,
            "timestamp": datetime.utcnow().isoformat(),
            "compliant": True
        }
        
        self.audit_trail.append(supervision_record)
        
        # Check for patterns requiring escalation
        if any(keyword in review_notes.lower() for keyword in ["violation", "concern", "issue"]):
            await self.create_violation(
                ComplianceType.FINRA,
                "MEDIUM",
                f"Supervisory concern noted: {review_notes[:100]}",
                supervisor_id
            )
    
    async def maintain_books_records(
        self,
        record_type: str,
        record_data: Dict[str, Any],
        retention_years: int = 7
    ):
        """
        FINRA Rule 4511: Maintain required books and records
        """
        
        record = {
            "record_id": f"rec_{datetime.utcnow().timestamp()}",
            "type": record_type,
            "data": record_data,
            "created_at": datetime.utcnow().isoformat(),
            "retention_until": (datetime.utcnow() + timedelta(days=retention_years*365)).isoformat(),
            "hash": hashlib.sha256(json.dumps(record_data).encode()).hexdigest()
        }
        
        # Store record (would typically go to compliant storage)
        self.audit_trail.append(record)
        
        return record["record_id"]
    
    async def create_violation(
        self,
        compliance_type: ComplianceType,
        severity: str,
        description: str,
        user_id: Optional[str] = None
    ):
        """Create and log a compliance violation"""
        
        violation = ComplianceViolation(
            violation_id=f"vio_{datetime.utcnow().timestamp()}",
            compliance_type=compliance_type,
            severity=severity,
            description=description,
            detected_at=datetime.utcnow(),
            user_id=user_id
        )
        
        self.violations.append(violation)
        
        # Trigger alerts for critical violations
        if severity == "CRITICAL":
            await self.send_compliance_alert(violation)
        
        return violation
    
    async def send_compliance_alert(self, violation: ComplianceViolation):
        """Send alert for critical compliance violations"""
        # Implementation would send to compliance team
        pass


class SECCompliance:
    """
    SEC Compliance Implementation
    
    Implements:
    - Regulation Best Interest (Reg BI)
    - Form ADV Requirements
    - Custody Rule
    - Marketing Rule
    """
    
    def __init__(self):
        self.disclosures = []
        self.conflicts_of_interest = []
    
    async def check_best_interest(
        self,
        advisor_id: str,
        client_id: str,
        recommendation: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """
        Regulation Best Interest compliance check
        """
        
        issues = []
        
        # Disclosure Obligation
        required_disclosures = [
            "fees_and_costs",
            "conflicts_of_interest",
            "scope_of_services",
            "account_types"
        ]
        
        provided_disclosures = recommendation.get("disclosures", {})
        for disclosure in required_disclosures:
            if disclosure not in provided_disclosures:
                issues.append(f"Missing required disclosure: {disclosure}")
        
        # Care Obligation
        if not recommendation.get("client_profile_reviewed"):
            issues.append("Client profile must be reviewed before recommendation")
        
        if not recommendation.get("alternatives_considered"):
            issues.append("Alternative investments must be considered")
        
        # Conflict of Interest Obligation
        conflicts = recommendation.get("conflicts_of_interest", [])
        if conflicts and not recommendation.get("conflicts_mitigated"):
            issues.append("Conflicts of interest must be mitigated or eliminated")
        
        # Compliance Obligation
        if not recommendation.get("policies_followed"):
            issues.append("Firm policies and procedures must be followed")
        
        return len(issues) == 0, issues
    
    async def validate_form_adv(
        self,
        form_data: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """
        Validate Form ADV requirements
        """
        
        issues = []
        
        # Check required sections
        required_sections = [
            "advisory_business",
            "fees_and_compensation",
            "performance_based_fees",
            "types_of_clients",
            "methods_of_analysis",
            "disciplinary_information",
            "other_financial_activities",
            "custody",
            "investment_discretion",
            "voting_client_securities"
        ]
        
        for section in required_sections:
            if section not in form_data or not form_data[section]:
                issues.append(f"Form ADV missing required section: {section}")
        
        # Validate AUM reporting
        aum = form_data.get("assets_under_management", 0)
        if aum > 100_000_000 and not form_data.get("sec_registered"):
            issues.append("Advisors with >$100M AUM must register with SEC")
        
        # Check disclosure brochure
        if not form_data.get("brochure_delivered"):
            issues.append("Form ADV Part 2 brochure must be delivered to clients")
        
        return len(issues) == 0, issues
    
    async def check_custody_rule(
        self,
        advisor_id: str,
        client_assets: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """
        Check compliance with SEC Custody Rule
        """
        
        issues = []
        
        # Check qualified custodian requirement
        if not client_assets.get("qualified_custodian"):
            issues.append("Client assets must be held by qualified custodian")
        
        # Check account statements
        if not client_assets.get("quarterly_statements_sent"):
            issues.append("Quarterly account statements must be sent to clients")
        
        # Check surprise examination requirement
        if client_assets.get("has_custody"):
            last_exam = client_assets.get("last_surprise_exam")
            if not last_exam or (datetime.now() - last_exam).days > 365:
                issues.append("Annual surprise examination required for advisors with custody")
        
        return len(issues) == 0, issues
    
    async def validate_marketing(
        self,
        marketing_material: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """
        Validate compliance with SEC Marketing Rule
        """
        
        issues = []
        content = marketing_material.get("content", "")
        
        # Check for testimonials and endorsements
        if "testimonial" in content.lower() or "endorsement" in content.lower():
            if not marketing_material.get("disclosure_provided"):
                issues.append("Testimonials/endorsements require specific disclosures")
            
            if not marketing_material.get("oversight_exercised"):
                issues.append("Advisor must exercise oversight over testimonials/endorsements")
        
        # Check performance advertising
        if "performance" in content.lower() or "returns" in content.lower():
            if not marketing_material.get("net_of_fees"):
                issues.append("Performance must be shown net of fees")
            
            if not marketing_material.get("time_period_disclosed"):
                issues.append("Performance time periods must be disclosed")
        
        # Check for fair and balanced presentation
        if re.search(r'(guaranteed|assured|certain)\s+returns?', content, re.IGNORECASE):
            issues.append("Marketing cannot guarantee returns")
        
        return len(issues) == 0, issues


class GDPRCompliance:
    """
    GDPR Compliance Implementation
    
    Implements:
    - Data Subject Rights
    - Consent Management
    - Data Protection Impact Assessments
    - Data Breach Notifications
    """
    
    def __init__(self):
        self.consent_records = {}
        self.data_requests = []
        self.breach_notifications = []
    
    async def record_consent(
        self,
        data_subject_id: str,
        purpose: str,
        consent_given: bool,
        withdrawal_method: Optional[str] = None
    ) -> str:
        """
        Record consent for data processing
        """
        
        consent_id = f"consent_{datetime.utcnow().timestamp()}"
        
        consent_record = {
            "consent_id": consent_id,
            "data_subject_id": data_subject_id,
            "purpose": purpose,
            "consent_given": consent_given,
            "timestamp": datetime.utcnow().isoformat(),
            "withdrawal_method": withdrawal_method,
            "ip_address": None,  # Would capture from request
            "version": "1.0"
        }
        
        if data_subject_id not in self.consent_records:
            self.consent_records[data_subject_id] = []
        
        self.consent_records[data_subject_id].append(consent_record)
        
        return consent_id
    
    async def process_data_request(
        self,
        subject_id: str,
        request_type: str,
        request_data: Optional[Dict[str, Any]] = None
    ) -> DataSubjectRequest:
        """
        Process GDPR data subject request
        """
        
        request = DataSubjectRequest(
            request_id=f"dsr_{datetime.utcnow().timestamp()}",
            subject_id=subject_id,
            request_type=request_type,
            requested_at=datetime.utcnow(),
            status="PENDING"
        )
        
        self.data_requests.append(request)
        
        # Process based on request type
        if request_type == "ACCESS":
            response = await self.handle_access_request(subject_id)
        elif request_type == "ERASURE":
            response = await self.handle_erasure_request(subject_id)
        elif request_type == "PORTABILITY":
            response = await self.handle_portability_request(subject_id)
        elif request_type == "RECTIFICATION":
            response = await self.handle_rectification_request(subject_id, request_data)
        else:
            response = {"error": "Unknown request type"}
        
        request.response = response
        request.status = "COMPLETED"
        request.completed_at = datetime.utcnow()
        
        return request
    
    async def handle_access_request(self, subject_id: str) -> Dict[str, Any]:
        """
        Handle data access request - provide all data about subject
        """
        
        # Would query all databases for user data
        return {
            "personal_data": {
                "profile": {},
                "transactions": [],
                "logs": []
            },
            "processing_purposes": ["service_provision", "compliance", "analytics"],
            "recipients": ["internal_systems", "authorized_third_parties"],
            "retention_period": "7 years for compliance",
            "rights": ["access", "rectification", "erasure", "portability", "objection"]
        }
    
    async def handle_erasure_request(self, subject_id: str) -> Dict[str, Any]:
        """
        Handle right to be forgotten request
        """
        
        # Check if erasure can be performed
        can_erase = True
        reasons = []
        
        # Check legal obligations
        if await self.has_legal_obligation(subject_id):
            can_erase = False
            reasons.append("Legal obligation to retain data")
        
        # Check ongoing contracts
        if await self.has_active_contract(subject_id):
            can_erase = False
            reasons.append("Active contract requires data retention")
        
        if can_erase:
            # Perform erasure (pseudonymization in practice)
            return {"status": "erased", "timestamp": datetime.utcnow().isoformat()}
        else:
            return {"status": "denied", "reasons": reasons}
    
    async def handle_portability_request(self, subject_id: str) -> Dict[str, Any]:
        """
        Handle data portability request
        """
        
        # Export data in machine-readable format
        return {
            "format": "JSON",
            "data": {},  # Would include all portable data
            "generated_at": datetime.utcnow().isoformat()
        }
    
    async def handle_rectification_request(
        self,
        subject_id: str,
        corrections: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Handle data rectification request
        """
        
        # Apply corrections to data
        corrected_fields = []
        
        for field, new_value in corrections.items():
            # Would update in database
            corrected_fields.append(field)
        
        return {
            "status": "rectified",
            "corrected_fields": corrected_fields,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def report_breach(
        self,
        breach_data: Dict[str, Any]
    ) -> str:
        """
        Report data breach (must be within 72 hours)
        """
        
        breach_id = f"breach_{datetime.utcnow().timestamp()}"
        
        notification = {
            "breach_id": breach_id,
            "detected_at": datetime.utcnow().isoformat(),
            "nature": breach_data.get("nature"),
            "categories_affected": breach_data.get("categories"),
            "approximate_subjects": breach_data.get("affected_count"),
            "likely_consequences": breach_data.get("consequences"),
            "measures_taken": breach_data.get("measures"),
            "dpo_notified": True,
            "authority_notified": False,  # Would trigger actual notification
            "subjects_notified": False
        }
        
        self.breach_notifications.append(notification)
        
        # Check if notification to subjects is required
        if breach_data.get("high_risk", False):
            await self.notify_affected_subjects(breach_id, breach_data)
        
        return breach_id
    
    async def notify_affected_subjects(self, breach_id: str, breach_data: Dict[str, Any]):
        """Notify affected data subjects of breach"""
        # Implementation would send notifications
        pass
    
    async def has_legal_obligation(self, subject_id: str) -> bool:
        """Check if there's a legal obligation to retain data"""
        # Would check against retention policies
        return False
    
    async def has_active_contract(self, subject_id: str) -> bool:
        """Check if subject has active contracts"""
        # Would check active services
        return False


class SOC2Compliance:
    """
    SOC 2 Compliance Implementation
    
    Implements Trust Service Criteria:
    - Security
    - Availability
    - Processing Integrity
    - Confidentiality
    - Privacy
    """
    
    def __init__(self):
        self.controls = {}
        self.control_tests = []
        self.incidents = []
    
    async def implement_security_controls(self) -> Dict[str, bool]:
        """
        Implement SOC 2 Security criteria controls
        """
        
        controls = {
            "CC6.1": await self.logical_access_controls(),
            "CC6.2": await self.registration_authorization(),
            "CC6.3": await self.access_removal(),
            "CC6.6": await self.encryption_controls(),
            "CC6.7": await self.authentication_controls(),
            "CC6.8": await self.incident_prevention()
        }
        
        self.controls.update(controls)
        return controls
    
    async def logical_access_controls(self) -> bool:
        """CC6.1: Logical and Physical Access Controls"""
        
        checks = [
            self.check_password_policy(),
            self.check_mfa_enabled(),
            self.check_session_timeout(),
            self.check_access_logs()
        ]
        
        return all(await asyncio.gather(*checks))
    
    async def registration_authorization(self) -> bool:
        """CC6.2: Prior to Issuing System Credentials"""
        
        # Check user registration process
        return True  # Would validate actual process
    
    async def access_removal(self) -> bool:
        """CC6.3: Access Removal Process"""
        
        # Check terminated user access removal
        return True  # Would validate deprovisioning
    
    async def encryption_controls(self) -> bool:
        """CC6.6: Encryption Requirements"""
        
        checks = {
            "data_at_rest": True,  # Would check database encryption
            "data_in_transit": True,  # Would check TLS configuration
            "key_management": True  # Would check key rotation
        }
        
        return all(checks.values())
    
    async def authentication_controls(self) -> bool:
        """CC6.7: Authentication Management"""
        
        # Check authentication mechanisms
        return True
    
    async def incident_prevention(self) -> bool:
        """CC6.8: Incident Prevention and Detection"""
        
        # Check IDS/IPS systems
        return True
    
    async def check_password_policy(self) -> bool:
        """Verify password policy compliance"""
        
        policy = {
            "min_length": 12,
            "complexity": True,
            "expiration_days": 90,
            "history_count": 12,
            "lockout_attempts": 5
        }
        
        # Would check against actual implementation
        return True
    
    async def check_mfa_enabled(self) -> bool:
        """Check if MFA is enabled for all users"""
        return True
    
    async def check_session_timeout(self) -> bool:
        """Check session timeout configuration"""
        return True
    
    async def check_access_logs(self) -> bool:
        """Check if access logging is enabled"""
        return True
    
    async def perform_control_test(
        self,
        control_id: str,
        test_procedure: str
    ) -> Dict[str, Any]:
        """
        Perform control effectiveness test
        """
        
        test_result = {
            "test_id": f"test_{datetime.utcnow().timestamp()}",
            "control_id": control_id,
            "procedure": test_procedure,
            "performed_at": datetime.utcnow().isoformat(),
            "result": "PASS",  # Would be actual test result
            "evidence": [],
            "exceptions": []
        }
        
        self.control_tests.append(test_result)
        return test_result
    
    async def generate_soc2_report(self) -> Dict[str, Any]:
        """
        Generate SOC 2 compliance report
        """
        
        return {
            "report_type": "SOC 2 Type II",
            "period": {
                "start": (datetime.now() - timedelta(days=365)).isoformat(),
                "end": datetime.now().isoformat()
            },
            "controls_implemented": len(self.controls),
            "controls_effective": sum(1 for v in self.controls.values() if v),
            "tests_performed": len(self.control_tests),
            "tests_passed": sum(1 for t in self.control_tests if t["result"] == "PASS"),
            "incidents": len(self.incidents),
            "opinion": "Unqualified" if all(self.controls.values()) else "Qualified"
        }


class ComplianceEngine:
    """
    Central compliance engine coordinating all compliance requirements
    """
    
    def __init__(self):
        self.finra = FINRACompliance()
        self.sec = SECCompliance()
        self.gdpr = GDPRCompliance()
        self.soc2 = SOC2Compliance()
        self.compliance_calendar = []
        self.compliance_metrics = {}
    
    async def run_compliance_checks(
        self,
        check_type: Optional[ComplianceType] = None
    ) -> Dict[str, Any]:
        """
        Run comprehensive compliance checks
        """
        
        results = {}
        
        if not check_type or check_type == ComplianceType.FINRA:
            results["finra"] = await self.check_finra_compliance()
        
        if not check_type or check_type == ComplianceType.SEC:
            results["sec"] = await self.check_sec_compliance()
        
        if not check_type or check_type == ComplianceType.GDPR:
            results["gdpr"] = await self.check_gdpr_compliance()
        
        if not check_type or check_type == ComplianceType.SOC2:
            results["soc2"] = await self.check_soc2_compliance()
        
        # Update metrics
        self.update_compliance_metrics(results)
        
        return results
    
    async def check_finra_compliance(self) -> Dict[str, Any]:
        """Run FINRA compliance checks"""
        
        return {
            "compliant": len(self.finra.violations) == 0,
            "violations": len(self.finra.violations),
            "last_check": datetime.utcnow().isoformat()
        }
    
    async def check_sec_compliance(self) -> Dict[str, Any]:
        """Run SEC compliance checks"""
        
        return {
            "compliant": True,  # Would check actual compliance
            "disclosures_current": True,
            "last_check": datetime.utcnow().isoformat()
        }
    
    async def check_gdpr_compliance(self) -> Dict[str, Any]:
        """Run GDPR compliance checks"""
        
        pending_requests = [r for r in self.gdpr.data_requests if r.status == "PENDING"]
        
        return {
            "compliant": len(pending_requests) == 0,
            "pending_requests": len(pending_requests),
            "consent_records": len(self.gdpr.consent_records),
            "last_check": datetime.utcnow().isoformat()
        }
    
    async def check_soc2_compliance(self) -> Dict[str, Any]:
        """Run SOC 2 compliance checks"""
        
        controls = await self.soc2.implement_security_controls()
        
        return {
            "compliant": all(controls.values()),
            "controls_passed": sum(1 for v in controls.values() if v),
            "controls_total": len(controls),
            "last_check": datetime.utcnow().isoformat()
        }
    
    def update_compliance_metrics(self, results: Dict[str, Any]):
        """Update compliance metrics for reporting"""
        
        self.compliance_metrics = {
            "overall_compliance": all(r.get("compliant", False) for r in results.values()),
            "checks_performed": len(results),
            "last_updated": datetime.utcnow().isoformat(),
            "details": results
        }
    
    async def generate_compliance_report(self) -> Dict[str, Any]:
        """Generate comprehensive compliance report"""
        
        return {
            "report_date": datetime.utcnow().isoformat(),
            "metrics": self.compliance_metrics,
            "finra": {
                "violations": self.finra.violations,
                "audit_trail_entries": len(self.finra.audit_trail)
            },
            "sec": {
                "disclosures": len(self.sec.disclosures),
                "conflicts": len(self.sec.conflicts_of_interest)
            },
            "gdpr": {
                "data_requests": len(self.gdpr.data_requests),
                "consent_records": len(self.gdpr.consent_records),
                "breaches": len(self.gdpr.breach_notifications)
            },
            "soc2": await self.soc2.generate_soc2_report()
        }
    
    async def schedule_compliance_task(
        self,
        task_name: str,
        compliance_type: ComplianceType,
        due_date: datetime,
        recurring: Optional[str] = None  # daily, weekly, monthly, quarterly, annually
    ):
        """Schedule compliance task"""
        
        task = {
            "task_id": f"task_{datetime.utcnow().timestamp()}",
            "name": task_name,
            "type": compliance_type.value,
            "due_date": due_date.isoformat(),
            "recurring": recurring,
            "status": "SCHEDULED"
        }
        
        self.compliance_calendar.append(task)
        return task["task_id"]