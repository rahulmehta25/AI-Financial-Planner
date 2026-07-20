"""
Compliance service for regulatory proof generation and management.
"""

import json
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import logging

from .ipfs_service import IPFSService
from .integrity_service import IntegrityVerificationService
from ..utils.blockchain_utils import BlockchainUtils
from ..utils.crypto_utils import CryptoUtils
from ..config import get_blockchain_config

logger = logging.getLogger(__name__)


class ComplianceStandard(Enum):
    """Supported compliance standards."""
    SOX = "SOX"
    GDPR = "GDPR"
    PCI_DSS = "PCI-DSS"
    HIPAA = "HIPAA"
    ISO27001 = "ISO27001"
    NIST = "NIST"


@dataclass
class ProofOfExistence:
    """Proof of existence for financial plans."""
    plan_id: str
    user_id: str
    plan_hash: str
    timestamp: datetime
    ipfs_hash: str
    blockchain_tx_hash: str
    block_number: int
    metadata: Dict[str, Any]
    

@dataclass
class ComplianceProof:
    """Compliance proof record."""
    compliance_id: str
    standard: ComplianceStandard
    evidence_hash: str
    timestamp: datetime
    ipfs_evidence: str
    blockchain_tx_hash: str
    block_number: int
    description: str
    metadata: Dict[str, Any]
    

class ComplianceService:
    """Service for regulatory compliance and proof-of-existence."""
    
    def __init__(self):
        self.config = get_blockchain_config()
        self.blockchain_utils = BlockchainUtils()
        self.ipfs_service = IPFSService()
        self.integrity_service = IntegrityVerificationService()
        self.crypto_utils = CryptoUtils()
        
    async def create_proof_of_existence(
        self,
        plan_id: str,
        user_id: str,
        plan_data: Dict[str, Any],
        metadata: Dict[str, Any] = None
    ) -> ProofOfExistence:
        """
        Create proof of existence for a financial plan.
        
        Args:
            plan_id: Unique identifier for the plan
            user_id: ID of the user who owns the plan
            plan_data: The financial plan data
            metadata: Optional metadata about the plan
            
        Returns:
            ProofOfExistence object
        """
        try:
            # Generate plan hash
            plan_json = json.dumps(plan_data, sort_keys=True, default=str)
            plan_hash = self.crypto_utils.generate_hash(plan_json.encode())
            
            # Store plan data in IPFS
            ipfs_result = await self.ipfs_service.add_json(
                {
                    'plan_id': plan_id,
                    'plan_data': plan_data,
                    'metadata': metadata or {},
                    'timestamp': datetime.now().isoformat()
                },
                encrypt=True
            )
            ipfs_hash = ipfs_result['ipfs_hash']
            
            # Pin the file in IPFS
            await self.ipfs_service.pin_file(ipfs_hash)
            
            # Create integrity record
            self.integrity_service.create_integrity_record(
                plan_id,
                plan_data,
                {'type': 'financial_plan', 'user_id': user_id}
            )
            
            # Record proof on blockchain
            blockchain_tx_hash = await self._record_proof_on_blockchain(
                plan_id,
                user_id,
                plan_hash,
                int(datetime.now().timestamp()),
                ipfs_hash
            )
            
            # Wait for transaction confirmation
            receipt = self.blockchain_utils.wait_for_transaction_receipt(blockchain_tx_hash)
            
            proof = ProofOfExistence(
                plan_id=plan_id,
                user_id=user_id,
                plan_hash=plan_hash,
                timestamp=datetime.now(),
                ipfs_hash=ipfs_hash,
                blockchain_tx_hash=blockchain_tx_hash,
                block_number=receipt['block_number'],
                metadata=metadata or {}
            )
            
            logger.info(f"Proof of existence created for plan: {plan_id}")
            return proof
            
        except Exception as e:
            logger.error(f"Error creating proof of existence: {e}")
            raise
    
    async def verify_proof_of_existence(self, plan_id: str) -> Dict[str, Any]:
        """
        Verify proof of existence for a financial plan.
        
        Args:
            plan_id: ID of the plan to verify
            
        Returns:
            Dictionary with verification results
        """
        try:
            # Get proof from blockchain
            contract = self.blockchain_utils.get_compliance_contract()
            
            result = self.blockchain_utils.call_contract_function(
                contract.functions.getProofOfExistence(plan_id)
            )
            
            if not result or not result[0]:  # Check if proof exists
                return {'valid': False, 'error': 'Proof not found'}
            
            user_id, plan_hash, timestamp, ipfs_hash, block_number = result
            
            # Get plan data from IPFS
            plan_data = await self.ipfs_service.get_json(ipfs_hash)
            
            # Verify data integrity
            expected_hash = self.crypto_utils.generate_hash(
                json.dumps(plan_data['plan_data'], sort_keys=True, default=str).encode()
            )
            
            # Verify blockchain integrity
            blockchain_valid = self.blockchain_utils.call_contract_function(
                contract.functions.verifyPlanIntegrity(
                    plan_id,
                    bytes.fromhex(expected_hash)
                )
            )
            
            # Verify IPFS integrity
            ipfs_valid = await self.ipfs_service.verify_file_integrity(
                ipfs_hash,
                expected_hash
            )
            
            return {
                'valid': blockchain_valid and ipfs_valid,
                'plan_id': plan_id,
                'user_id': user_id,
                'plan_hash': plan_hash.hex(),
                'timestamp': datetime.fromtimestamp(timestamp),
                'block_number': block_number,
                'blockchain_check': blockchain_valid,
                'ipfs_check': ipfs_valid,
                'verification_time': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error verifying proof of existence: {e}")
            return {'valid': False, 'error': str(e)}
    
    async def record_compliance_proof(
        self,
        standard: ComplianceStandard,
        evidence_data: Dict[str, Any],
        description: str,
        metadata: Dict[str, Any] = None
    ) -> ComplianceProof:
        """
        Record compliance proof for regulatory standards.
        
        Args:
            standard: Compliance standard
            evidence_data: Evidence data for compliance
            description: Description of the compliance proof
            metadata: Optional metadata
            
        Returns:
            ComplianceProof object
        """
        try:
            compliance_id = str(uuid.uuid4())
            
            # Generate evidence hash
            evidence_json = json.dumps(evidence_data, sort_keys=True, default=str)
            evidence_hash = self.crypto_utils.generate_hash(evidence_json.encode())
            
            # Store evidence in IPFS
            ipfs_result = await self.ipfs_service.add_json(
                {
                    'compliance_id': compliance_id,
                    'standard': standard.value,
                    'evidence_data': evidence_data,
                    'description': description,
                    'metadata': metadata or {},
                    'timestamp': datetime.now().isoformat()
                },
                encrypt=True
            )
            ipfs_evidence = ipfs_result['ipfs_hash']
            
            # Pin the file in IPFS
            await self.ipfs_service.pin_file(ipfs_evidence)
            
            # Record compliance on blockchain
            blockchain_tx_hash = await self._record_compliance_on_blockchain(
                compliance_id,
                standard.value,
                evidence_hash,
                int(datetime.now().timestamp()),
                ipfs_evidence
            )
            
            # Wait for transaction confirmation
            receipt = self.blockchain_utils.wait_for_transaction_receipt(blockchain_tx_hash)
            
            proof = ComplianceProof(
                compliance_id=compliance_id,
                standard=standard,
                evidence_hash=evidence_hash,
                timestamp=datetime.now(),
                ipfs_evidence=ipfs_evidence,
                blockchain_tx_hash=blockchain_tx_hash,
                block_number=receipt['block_number'],
                description=description,
                metadata=metadata or {}
            )
            
            logger.info(f"Compliance proof recorded: {compliance_id} for {standard.value}")
            return proof
            
        except Exception as e:
            logger.error(f"Error recording compliance proof: {e}")
            raise
    
    async def get_user_proofs(self, user_id: str) -> List[ProofOfExistence]:
        """
        Get all proofs of existence for a user.
        
        Args:
            user_id: ID of the user
            
        Returns:
            List of ProofOfExistence objects
        """
        try:
            contract = self.blockchain_utils.get_compliance_contract()
            
            # Get user plan IDs from blockchain
            plan_ids = self.blockchain_utils.call_contract_function(
                contract.functions.getUserPlans(user_id)
            )
            
            proofs = []
            for plan_id in plan_ids:
                verification_result = await self.verify_proof_of_existence(plan_id)
                if verification_result.get('valid'):
                    # Get plan data from IPFS
                    contract_result = self.blockchain_utils.call_contract_function(
                        contract.functions.getProofOfExistence(plan_id)
                    )
                    
                    user_id_bc, plan_hash, timestamp, ipfs_hash, block_number = contract_result
                    
                    proof = ProofOfExistence(
                        plan_id=plan_id,
                        user_id=user_id_bc,
                        plan_hash=plan_hash.hex(),
                        timestamp=datetime.fromtimestamp(timestamp),
                        ipfs_hash=ipfs_hash,
                        blockchain_tx_hash="",  # Would need to get from event logs
                        block_number=block_number,
                        metadata={}
                    )
                    proofs.append(proof)
            
            return proofs
            
        except Exception as e:
            logger.error(f"Error getting user proofs: {e}")
            return []
    
    async def get_compliance_proofs_by_standard(
        self,
        standard: ComplianceStandard
    ) -> List[ComplianceProof]:
        """
        Get all compliance proofs for a specific standard.
        
        Args:
            standard: Compliance standard to search for
            
        Returns:
            List of ComplianceProof objects
        """
        try:
            contract = self.blockchain_utils.get_compliance_contract()
            
            # Get compliance IDs for the standard
            compliance_ids = self.blockchain_utils.call_contract_function(
                contract.functions.getStandardCompliance(standard.value)
            )
            
            proofs = []
            for compliance_id in compliance_ids:
                try:
                    # Get compliance proof from blockchain
                    result = self.blockchain_utils.call_contract_function(
                        contract.functions.getComplianceProof(compliance_id)
                    )
                    
                    std, evidence_hash, timestamp, ipfs_evidence, block_number = result
                    
                    # Get evidence data from IPFS
                    evidence_data = await self.ipfs_service.get_json(ipfs_evidence)
                    
                    proof = ComplianceProof(
                        compliance_id=compliance_id,
                        standard=ComplianceStandard(std),
                        evidence_hash=evidence_hash.hex(),
                        timestamp=datetime.fromtimestamp(timestamp),
                        ipfs_evidence=ipfs_evidence,
                        blockchain_tx_hash="",  # Would need to get from event logs
                        block_number=block_number,
                        description=evidence_data.get('description', ''),
                        metadata=evidence_data.get('metadata', {})
                    )
                    proofs.append(proof)
                    
                except Exception as e:
                    logger.warning(f"Error processing compliance proof {compliance_id}: {e}")
                    continue
            
            return proofs
            
        except Exception as e:
            logger.error(f"Error getting compliance proofs: {e}")
            return []
    
    async def generate_compliance_report(
        self,
        user_id: str = None,
        standard: ComplianceStandard = None,
        start_date: datetime = None,
        end_date: datetime = None
    ) -> Dict[str, Any]:
        """
        Generate compliance report.
        
        Args:
            user_id: Optional user ID filter
            standard: Optional compliance standard filter
            start_date: Optional start date filter
            end_date: Optional end date filter
            
        Returns:
            Dictionary with compliance report data
        """
        try:
            report = {
                'generated_at': datetime.now().isoformat(),
                'filters': {
                    'user_id': user_id,
                    'standard': standard.value if standard else None,
                    'start_date': start_date.isoformat() if start_date else None,
                    'end_date': end_date.isoformat() if end_date else None
                },
                'proofs_of_existence': [],
                'compliance_proofs': [],
                'summary': {}
            }
            
            # Get proofs of existence
            if user_id:
                user_proofs = await self.get_user_proofs(user_id)
                report['proofs_of_existence'] = [asdict(proof) for proof in user_proofs]
            
            # Get compliance proofs
            if standard:
                compliance_proofs = await self.get_compliance_proofs_by_standard(standard)
                filtered_proofs = self._filter_proofs_by_date(
                    compliance_proofs, start_date, end_date
                )
                report['compliance_proofs'] = [asdict(proof) for proof in filtered_proofs]
            else:
                # Get all standards
                all_proofs = []
                for std in ComplianceStandard:
                    std_proofs = await self.get_compliance_proofs_by_standard(std)
                    all_proofs.extend(std_proofs)
                
                filtered_proofs = self._filter_proofs_by_date(
                    all_proofs, start_date, end_date
                )
                report['compliance_proofs'] = [asdict(proof) for proof in filtered_proofs]
            
            # Generate summary
            report['summary'] = {
                'total_proofs_of_existence': len(report['proofs_of_existence']),
                'total_compliance_proofs': len(report['compliance_proofs']),
                'standards_covered': list(set(
                    proof['standard'] for proof in report['compliance_proofs']
                ))
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating compliance report: {e}")
            return {'error': str(e)}
    
    async def _record_proof_on_blockchain(
        self,
        plan_id: str,
        user_id: str,
        plan_hash: str,
        timestamp: int,
        ipfs_hash: str
    ) -> str:
        """
        Record proof of existence on blockchain.
        
        Args:
            plan_id: Plan identifier
            user_id: User identifier
            plan_hash: Hash of plan data
            timestamp: Unix timestamp
            ipfs_hash: IPFS hash for data storage
            
        Returns:
            Transaction hash
        """
        try:
            contract = self.blockchain_utils.get_compliance_contract()
            
            # Convert hash to bytes32
            plan_hash_bytes = bytes.fromhex(plan_hash)
            
            tx_hash = self.blockchain_utils.send_transaction(
                contract.functions.createProofOfExistence(
                    plan_id,
                    user_id,
                    plan_hash_bytes,
                    timestamp,
                    ipfs_hash
                )
            )
            
            return tx_hash
            
        except Exception as e:
            logger.error(f"Error recording proof on blockchain: {e}")
            raise
    
    async def _record_compliance_on_blockchain(
        self,
        compliance_id: str,
        standard: str,
        evidence_hash: str,
        timestamp: int,
        ipfs_evidence: str
    ) -> str:
        """
        Record compliance proof on blockchain.
        
        Args:
            compliance_id: Compliance identifier
            standard: Compliance standard
            evidence_hash: Hash of evidence data
            timestamp: Unix timestamp
            ipfs_evidence: IPFS hash for evidence storage
            
        Returns:
            Transaction hash
        """
        try:
            contract = self.blockchain_utils.get_compliance_contract()
            
            # Convert hash to bytes32
            evidence_hash_bytes = bytes.fromhex(evidence_hash)
            
            tx_hash = self.blockchain_utils.send_transaction(
                contract.functions.recordComplianceProof(
                    compliance_id,
                    standard,
                    evidence_hash_bytes,
                    timestamp
                )
            )
            
            return tx_hash
            
        except Exception as e:
            logger.error(f"Error recording compliance on blockchain: {e}")
            raise
    
    def _filter_proofs_by_date(
        self,
        proofs: List[ComplianceProof],
        start_date: datetime = None,
        end_date: datetime = None
    ) -> List[ComplianceProof]:
        """
        Filter proofs by date range.
        
        Args:
            proofs: List of proofs to filter
            start_date: Optional start date
            end_date: Optional end date
            
        Returns:
            Filtered list of proofs
        """
        filtered = proofs
        
        if start_date:
            filtered = [p for p in filtered if p.timestamp >= start_date]
        
        if end_date:
            filtered = [p for p in filtered if p.timestamp <= end_date]
        
        return filtered