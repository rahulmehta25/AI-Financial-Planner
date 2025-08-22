"""
FastAPI endpoints for compliance and proof-of-existence operations.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
import logging

from ..services.compliance_service import ComplianceService, ComplianceStandard
from ..models.audit_models import (
    ProofOfExistenceCreate,
    ProofOfExistence,
    ComplianceProofCreate,
    ComplianceProof,
    VerificationResult,
    ComplianceReport
)
from ...api.deps import get_current_user
from ...models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/blockchain/compliance", tags=["Blockchain Compliance"])

# Initialize service
compliance_service = ComplianceService()


@router.post("/proof-of-existence", response_model=ProofOfExistence)
async def create_proof_of_existence(
    proof_data: ProofOfExistenceCreate,
    current_user: User = Depends(get_current_user)
):
    """
    Create proof of existence for a financial plan.
    """
    try:
        # Verify user owns the plan or has admin access
        if proof_data.user_id != str(current_user.id) and not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Access denied")
        
        proof = await compliance_service.create_proof_of_existence(
            plan_id=proof_data.plan_id,
            user_id=proof_data.user_id,
            plan_data=proof_data.plan_data,
            metadata=proof_data.metadata
        )
        
        return ProofOfExistence(
            plan_id=proof.plan_id,
            user_id=proof.user_id,
            plan_hash=proof.plan_hash,
            timestamp=proof.timestamp,
            ipfs_hash=proof.ipfs_hash,
            blockchain_tx_hash=proof.blockchain_tx_hash,
            block_number=proof.block_number,
            metadata=proof.metadata
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating proof of existence: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/proof-of-existence/{plan_id}/verify", response_model=VerificationResult)
async def verify_proof_of_existence(
    plan_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Verify proof of existence for a financial plan.
    """
    try:
        verification_result = await compliance_service.verify_proof_of_existence(plan_id)
        
        return VerificationResult(
            valid=verification_result.get('valid', False),
            plan_id=verification_result.get('plan_id'),
            verification_time=verification_result.get('verification_time'),
            details=verification_result.get('details', {}),
            error=verification_result.get('error')
        )
        
    except Exception as e:
        logger.error(f"Error verifying proof of existence: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/users/{user_id}/proofs", response_model=List[ProofOfExistence])
async def get_user_proofs(
    user_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get all proofs of existence for a user.
    """
    try:
        # Check if user can access these proofs
        if str(current_user.id) != user_id and not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Access denied")
        
        proofs = await compliance_service.get_user_proofs(user_id)
        
        return [
            ProofOfExistence(
                plan_id=proof.plan_id,
                user_id=proof.user_id,
                plan_hash=proof.plan_hash,
                timestamp=proof.timestamp,
                ipfs_hash=proof.ipfs_hash,
                blockchain_tx_hash=proof.blockchain_tx_hash,
                block_number=proof.block_number,
                metadata=proof.metadata
            )
            for proof in proofs
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user proofs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/compliance-proof", response_model=ComplianceProof)
async def create_compliance_proof(
    proof_data: ComplianceProofCreate,
    current_user: User = Depends(get_current_user)
):
    """
    Record compliance proof for regulatory standards.
    """
    try:
        # Check if user has admin privileges for compliance recording
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        proof = await compliance_service.record_compliance_proof(
            standard=proof_data.standard,
            evidence_data=proof_data.evidence_data,
            description=proof_data.description,
            metadata=proof_data.metadata
        )
        
        return ComplianceProof(
            compliance_id=proof.compliance_id,
            standard=proof.standard,
            evidence_hash=proof.evidence_hash,
            timestamp=proof.timestamp,
            ipfs_evidence=proof.ipfs_evidence,
            blockchain_tx_hash=proof.blockchain_tx_hash,
            block_number=proof.block_number,
            description=proof.description,
            metadata=proof.metadata
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating compliance proof: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/compliance-proof/standard/{standard}", response_model=List[ComplianceProof])
async def get_compliance_proofs_by_standard(
    standard: ComplianceStandard,
    current_user: User = Depends(get_current_user)
):
    """
    Get all compliance proofs for a specific standard.
    """
    try:
        # Check if user has admin privileges
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        proofs = await compliance_service.get_compliance_proofs_by_standard(standard)
        
        return [
            ComplianceProof(
                compliance_id=proof.compliance_id,
                standard=proof.standard,
                evidence_hash=proof.evidence_hash,
                timestamp=proof.timestamp,
                ipfs_evidence=proof.ipfs_evidence,
                blockchain_tx_hash=proof.blockchain_tx_hash,
                block_number=proof.block_number,
                description=proof.description,
                metadata=proof.metadata
            )
            for proof in proofs
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting compliance proofs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/standards", response_model=List[str])
async def get_supported_standards():
    """
    Get list of supported compliance standards.
    """
    return [standard.value for standard in ComplianceStandard]


@router.post("/report", response_model=ComplianceReport)
async def generate_compliance_report(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    standard: Optional[ComplianceStandard] = Query(None, description="Filter by standard"),
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter"),
    current_user: User = Depends(get_current_user)
):
    """
    Generate compliance report.
    """
    try:
        # Check if user has admin privileges
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        report_data = await compliance_service.generate_compliance_report(
            user_id=user_id,
            standard=standard,
            start_date=start_date,
            end_date=end_date
        )
        
        if 'error' in report_data:
            raise HTTPException(status_code=500, detail=report_data['error'])
        
        # Convert proof objects to Pydantic models
        proofs_of_existence = []
        for proof_dict in report_data.get('proofs_of_existence', []):
            proofs_of_existence.append(ProofOfExistence(**proof_dict))
        
        compliance_proofs = []
        for proof_dict in report_data.get('compliance_proofs', []):
            # Convert standard string back to enum
            proof_dict['standard'] = ComplianceStandard(proof_dict['standard'])
            compliance_proofs.append(ComplianceProof(**proof_dict))
        
        return ComplianceReport(
            generated_at=datetime.fromisoformat(report_data['generated_at']),
            filters=report_data['filters'],
            proofs_of_existence=proofs_of_existence,
            compliance_proofs=compliance_proofs,
            summary=report_data['summary']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating compliance report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/report/export")
async def export_compliance_report(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    standard: Optional[ComplianceStandard] = Query(None, description="Filter by standard"),
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter"),
    format: str = Query(default="json", description="Export format (json, csv)"),
    current_user: User = Depends(get_current_user)
):
    """
    Export compliance report in various formats.
    """
    try:
        # Check if user has admin privileges
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        report_data = await compliance_service.generate_compliance_report(
            user_id=user_id,
            standard=standard,
            start_date=start_date,
            end_date=end_date
        )
        
        if 'error' in report_data:
            raise HTTPException(status_code=500, detail=report_data['error'])
        
        if format.lower() == "json":
            return JSONResponse(
                content=report_data,
                headers={
                    "Content-Disposition": f"attachment; filename=compliance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                }
            )
        elif format.lower() == "csv":
            # Implement CSV export logic here
            # For now, return JSON with appropriate headers
            return JSONResponse(
                content={"message": "CSV export not yet implemented"},
                status_code=501
            )
        else:
            raise HTTPException(status_code=400, detail="Unsupported export format")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting compliance report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/audit-trail/{plan_id}")
async def get_plan_audit_trail(
    plan_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get complete audit trail for a financial plan.
    """
    try:
        # Get proof of existence
        verification_result = await compliance_service.verify_proof_of_existence(plan_id)
        
        if not verification_result.get('valid'):
            raise HTTPException(status_code=404, detail="Plan proof not found or invalid")
        
        # This would typically include:
        # - Proof of existence
        # - All audit events related to the plan
        # - Compliance checks
        # - Verification history
        
        audit_trail = {
            "plan_id": plan_id,
            "proof_of_existence": verification_result,
            "last_verified": verification_result.get('verification_time'),
            "status": "verified" if verification_result.get('valid') else "invalid"
        }
        
        return audit_trail
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting audit trail: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def compliance_health_check():
    """
    Health check endpoint for compliance system.
    """
    try:
        # Check blockchain connection
        blockchain_connected = compliance_service.blockchain_utils.is_connected()
        
        # Check IPFS connection
        ipfs_connected = await compliance_service.ipfs_service.check_connection()
        
        status = "healthy" if blockchain_connected and ipfs_connected else "degraded"
        
        return {
            "status": status,
            "blockchain_connected": blockchain_connected,
            "ipfs_connected": ipfs_connected,
            "supported_standards": [standard.value for standard in ComplianceStandard],
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Compliance health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )