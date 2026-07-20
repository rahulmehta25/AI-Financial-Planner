"""
Pydantic models for blockchain audit system.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, validator
from enum import Enum


class ComplianceStandard(str, Enum):
    """Supported compliance standards."""
    SOX = "SOX"
    GDPR = "GDPR"
    PCI_DSS = "PCI-DSS"
    HIPAA = "HIPAA"
    ISO27001 = "ISO27001"
    NIST = "NIST"


class AuditAction(str, Enum):
    """Common audit actions."""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"
    EXPORT = "export"
    IMPORT = "import"
    APPROVE = "approve"
    REJECT = "reject"


class ResourceType(str, Enum):
    """Resource types for audit logging."""
    USER = "user"
    FINANCIAL_PLAN = "financial_plan"
    INVESTMENT = "investment"
    GOAL = "goal"
    SIMULATION = "simulation"
    REPORT = "report"
    DOCUMENT = "document"


class AuditEventCreate(BaseModel):
    """Schema for creating audit events."""
    user_id: str = Field(..., description="ID of the user performing the action")
    action: AuditAction = Field(..., description="Action being performed")
    resource_type: ResourceType = Field(..., description="Type of resource")
    resource_id: str = Field(..., description="ID of the resource")
    data: Dict[str, Any] = Field(default_factory=dict, description="Additional event data")
    ip_address: Optional[str] = Field(None, description="IP address of the user")
    user_agent: Optional[str] = Field(None, description="User agent string")
    session_id: Optional[str] = Field(None, description="Session identifier")

    class Config:
        schema_extra = {
            "example": {
                "user_id": "user123",
                "action": "create",
                "resource_type": "financial_plan",
                "resource_id": "plan456",
                "data": {"plan_name": "Retirement Plan 2024"},
                "ip_address": "192.168.1.100",
                "user_agent": "Mozilla/5.0...",
                "session_id": "sess789"
            }
        }


class AuditEvent(BaseModel):
    """Complete audit event model."""
    event_id: str = Field(..., description="Unique event identifier")
    user_id: str = Field(..., description="ID of the user")
    action: str = Field(..., description="Action performed")
    resource_type: str = Field(..., description="Type of resource")
    resource_id: str = Field(..., description="ID of the resource")
    timestamp: datetime = Field(..., description="Event timestamp")
    data: Dict[str, Any] = Field(default_factory=dict, description="Event data")
    ip_address: Optional[str] = Field(None, description="IP address")
    user_agent: Optional[str] = Field(None, description="User agent")
    session_id: Optional[str] = Field(None, description="Session ID")
    data_hash: str = Field(..., description="Hash of event data")
    ipfs_hash: str = Field(..., description="IPFS hash for detailed data")
    blockchain_tx_hash: str = Field(..., description="Blockchain transaction hash")
    block_number: int = Field(..., description="Block number")
    verification_status: str = Field(default="pending", description="Verification status")

    class Config:
        schema_extra = {
            "example": {
                "event_id": "evt_123456789",
                "user_id": "user123",
                "action": "create",
                "resource_type": "financial_plan",
                "resource_id": "plan456",
                "timestamp": "2024-01-01T10:00:00Z",
                "data": {"plan_name": "Retirement Plan 2024"},
                "data_hash": "a1b2c3d4e5f6...",
                "ipfs_hash": "QmXyZ123...",
                "blockchain_tx_hash": "0x123abc...",
                "block_number": 12345,
                "verification_status": "confirmed"
            }
        }


class ProofOfExistenceCreate(BaseModel):
    """Schema for creating proof of existence."""
    plan_id: str = Field(..., description="Unique plan identifier")
    user_id: str = Field(..., description="ID of the plan owner")
    plan_data: Dict[str, Any] = Field(..., description="Financial plan data")
    metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Optional metadata"
    )

    class Config:
        schema_extra = {
            "example": {
                "plan_id": "plan123",
                "user_id": "user456",
                "plan_data": {
                    "name": "My Retirement Plan",
                    "goals": ["retirement", "education"],
                    "investments": ["stocks", "bonds"]
                },
                "metadata": {
                    "version": "1.0",
                    "created_by": "advisor789"
                }
            }
        }


class ProofOfExistence(BaseModel):
    """Proof of existence model."""
    plan_id: str = Field(..., description="Plan identifier")
    user_id: str = Field(..., description="User identifier")
    plan_hash: str = Field(..., description="Hash of plan data")
    timestamp: datetime = Field(..., description="Creation timestamp")
    ipfs_hash: str = Field(..., description="IPFS hash for plan storage")
    blockchain_tx_hash: str = Field(..., description="Blockchain transaction hash")
    block_number: int = Field(..., description="Block number")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Plan metadata")

    class Config:
        schema_extra = {
            "example": {
                "plan_id": "plan123",
                "user_id": "user456",
                "plan_hash": "a1b2c3d4e5f6...",
                "timestamp": "2024-01-01T10:00:00Z",
                "ipfs_hash": "QmXyZ123...",
                "blockchain_tx_hash": "0x123abc...",
                "block_number": 12345,
                "metadata": {"version": "1.0"}
            }
        }


class ComplianceProofCreate(BaseModel):
    """Schema for creating compliance proof."""
    standard: ComplianceStandard = Field(..., description="Compliance standard")
    evidence_data: Dict[str, Any] = Field(..., description="Evidence data")
    description: str = Field(..., description="Description of compliance proof")
    metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Optional metadata"
    )

    class Config:
        schema_extra = {
            "example": {
                "standard": "SOX",
                "evidence_data": {
                    "audit_report": "Annual SOX compliance audit",
                    "controls_tested": 25,
                    "deficiencies": 0
                },
                "description": "SOX compliance audit for Q4 2024",
                "metadata": {
                    "auditor": "Ernst & Young",
                    "period": "Q4 2024"
                }
            }
        }


class ComplianceProof(BaseModel):
    """Compliance proof model."""
    compliance_id: str = Field(..., description="Compliance identifier")
    standard: ComplianceStandard = Field(..., description="Compliance standard")
    evidence_hash: str = Field(..., description="Hash of evidence data")
    timestamp: datetime = Field(..., description="Creation timestamp")
    ipfs_evidence: str = Field(..., description="IPFS hash for evidence storage")
    blockchain_tx_hash: str = Field(..., description="Blockchain transaction hash")
    block_number: int = Field(..., description="Block number")
    description: str = Field(..., description="Description")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata")

    class Config:
        schema_extra = {
            "example": {
                "compliance_id": "comp_123456789",
                "standard": "SOX",
                "evidence_hash": "a1b2c3d4e5f6...",
                "timestamp": "2024-01-01T10:00:00Z",
                "ipfs_evidence": "QmXyZ123...",
                "blockchain_tx_hash": "0x123abc...",
                "block_number": 12345,
                "description": "SOX compliance audit",
                "metadata": {"auditor": "Ernst & Young"}
            }
        }


class VerificationResult(BaseModel):
    """Verification result model."""
    valid: bool = Field(..., description="Whether verification passed")
    event_id: Optional[str] = Field(None, description="Event ID (for audit events)")
    plan_id: Optional[str] = Field(None, description="Plan ID (for proofs)")
    verification_time: datetime = Field(..., description="Verification timestamp")
    details: Dict[str, Any] = Field(default_factory=dict, description="Verification details")
    error: Optional[str] = Field(None, description="Error message if verification failed")

    class Config:
        schema_extra = {
            "example": {
                "valid": True,
                "event_id": "evt_123456789",
                "verification_time": "2024-01-01T10:00:00Z",
                "details": {
                    "integrity_check": True,
                    "blockchain_check": True,
                    "ipfs_check": True
                }
            }
        }


class AuditSearchFilters(BaseModel):
    """Filters for searching audit events."""
    user_id: Optional[str] = Field(None, description="Filter by user ID")
    action: Optional[AuditAction] = Field(None, description="Filter by action")
    resource_type: Optional[ResourceType] = Field(None, description="Filter by resource type")
    resource_id: Optional[str] = Field(None, description="Filter by resource ID")
    start_date: Optional[datetime] = Field(None, description="Start date filter")
    end_date: Optional[datetime] = Field(None, description="End date filter")
    limit: int = Field(default=100, ge=1, le=1000, description="Maximum results")
    offset: int = Field(default=0, ge=0, description="Results offset")

    class Config:
        schema_extra = {
            "example": {
                "user_id": "user123",
                "action": "create",
                "resource_type": "financial_plan",
                "start_date": "2024-01-01T00:00:00Z",
                "end_date": "2024-12-31T23:59:59Z",
                "limit": 50,
                "offset": 0
            }
        }


class ComplianceReport(BaseModel):
    """Compliance report model."""
    generated_at: datetime = Field(..., description="Report generation timestamp")
    filters: Dict[str, Any] = Field(..., description="Applied filters")
    proofs_of_existence: List[ProofOfExistence] = Field(
        default_factory=list,
        description="Proofs of existence"
    )
    compliance_proofs: List[ComplianceProof] = Field(
        default_factory=list,
        description="Compliance proofs"
    )
    summary: Dict[str, Any] = Field(default_factory=dict, description="Report summary")

    class Config:
        schema_extra = {
            "example": {
                "generated_at": "2024-01-01T10:00:00Z",
                "filters": {
                    "user_id": "user123",
                    "standard": "SOX"
                },
                "proofs_of_existence": [],
                "compliance_proofs": [],
                "summary": {
                    "total_proofs_of_existence": 10,
                    "total_compliance_proofs": 5,
                    "standards_covered": ["SOX", "GDPR"]
                }
            }
        }


class AuditStatistics(BaseModel):
    """Audit system statistics."""
    total_audit_events: int = Field(..., description="Total number of audit events")
    blockchain_status: Dict[str, Any] = Field(..., description="Blockchain status")
    integrity_verification: Dict[str, Any] = Field(..., description="Integrity stats")
    ipfs_status: bool = Field(..., description="IPFS connection status")
    last_updated: datetime = Field(..., description="Last update timestamp")

    class Config:
        schema_extra = {
            "example": {
                "total_audit_events": 1000,
                "blockchain_status": {
                    "connected": True,
                    "block_number": 12345,
                    "chain_id": 1
                },
                "integrity_verification": {
                    "total_records": 1000,
                    "verified_records": 950,
                    "verification_rate": 0.95
                },
                "ipfs_status": True,
                "last_updated": "2024-01-01T10:00:00Z"
            }
        }