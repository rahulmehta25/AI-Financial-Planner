"""
Integrity verification service using hash-based validation.
"""

import json
import hashlib
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import logging

from ..utils.crypto_utils import CryptoUtils
from ..config import get_blockchain_config

logger = logging.getLogger(__name__)


@dataclass
class IntegrityRecord:
    """Record for tracking data integrity."""
    id: str
    data_hash: str
    merkle_root: str
    timestamp: datetime
    metadata: Dict[str, Any]
    verification_count: int = 0
    last_verified: Optional[datetime] = None
    

@dataclass
class VerificationResult:
    """Result of integrity verification."""
    valid: bool
    record_id: str
    verification_time: datetime
    details: Dict[str, Any]
    

class IntegrityVerificationService:
    """Service for hash-based integrity verification."""
    
    def __init__(self):
        self.config = get_blockchain_config()
        self.crypto_utils = CryptoUtils()
        self.records: Dict[str, IntegrityRecord] = {}
        
    def create_integrity_record(
        self,
        record_id: str,
        data: Any,
        metadata: Dict[str, Any] = None
    ) -> IntegrityRecord:
        """
        Create an integrity record for data.
        
        Args:
            record_id: Unique identifier for the record
            data: Data to create integrity record for
            metadata: Optional metadata
            
        Returns:
            IntegrityRecord object
        """
        try:
            # Serialize data
            if isinstance(data, (dict, list)):
                data_bytes = json.dumps(data, sort_keys=True, default=str).encode()
            elif isinstance(data, str):
                data_bytes = data.encode()
            elif isinstance(data, bytes):
                data_bytes = data
            else:
                data_bytes = str(data).encode()
            
            # Generate primary hash
            data_hash = self.crypto_utils.generate_hash(data_bytes)
            
            # Create Merkle tree components
            components = self._extract_data_components(data)
            component_hashes = [self.crypto_utils.generate_hash(comp.encode()) for comp in components]
            merkle_root = self.crypto_utils.generate_merkle_root(component_hashes)
            
            # Create record
            record = IntegrityRecord(
                id=record_id,
                data_hash=data_hash,
                merkle_root=merkle_root,
                timestamp=datetime.now(),
                metadata=metadata or {}
            )
            
            # Store record
            self.records[record_id] = record
            
            logger.info(f"Created integrity record: {record_id}")
            return record
            
        except Exception as e:
            logger.error(f"Error creating integrity record: {e}")
            raise
    
    def verify_data_integrity(
        self,
        record_id: str,
        current_data: Any
    ) -> VerificationResult:
        """
        Verify the integrity of data against stored record.
        
        Args:
            record_id: ID of the integrity record
            current_data: Current data to verify
            
        Returns:
            VerificationResult object
        """
        try:
            if record_id not in self.records:
                return VerificationResult(
                    valid=False,
                    record_id=record_id,
                    verification_time=datetime.now(),
                    details={'error': 'Record not found'}
                )
            
            record = self.records[record_id]
            
            # Serialize current data
            if isinstance(current_data, (dict, list)):
                data_bytes = json.dumps(current_data, sort_keys=True, default=str).encode()
            elif isinstance(current_data, str):
                data_bytes = current_data.encode()
            elif isinstance(current_data, bytes):
                data_bytes = current_data
            else:
                data_bytes = str(current_data).encode()
            
            # Generate current hash
            current_hash = self.crypto_utils.generate_hash(data_bytes)
            
            # Verify primary hash
            hash_valid = current_hash == record.data_hash
            
            # Verify Merkle root
            components = self._extract_data_components(current_data)
            component_hashes = [self.crypto_utils.generate_hash(comp.encode()) for comp in components]
            current_merkle_root = self.crypto_utils.generate_merkle_root(component_hashes)
            merkle_valid = current_merkle_root == record.merkle_root
            
            # Overall validity
            valid = hash_valid and merkle_valid
            
            # Update record
            record.verification_count += 1
            record.last_verified = datetime.now()
            
            result = VerificationResult(
                valid=valid,
                record_id=record_id,
                verification_time=datetime.now(),
                details={
                    'hash_valid': hash_valid,
                    'merkle_valid': merkle_valid,
                    'original_hash': record.data_hash,
                    'current_hash': current_hash,
                    'original_merkle_root': record.merkle_root,
                    'current_merkle_root': current_merkle_root
                }
            )
            
            logger.info(f"Verified integrity for record {record_id}: {'VALID' if valid else 'INVALID'}")
            return result
            
        except Exception as e:
            logger.error(f"Error verifying data integrity: {e}")
            return VerificationResult(
                valid=False,
                record_id=record_id,
                verification_time=datetime.now(),
                details={'error': str(e)}
            )
    
    def create_merkle_proof(
        self,
        record_id: str,
        component_index: int
    ) -> Optional[List[str]]:
        """
        Create Merkle proof for a specific data component.
        
        Args:
            record_id: ID of the integrity record
            component_index: Index of the component to prove
            
        Returns:
            Merkle proof as list of hashes
        """
        try:
            if record_id not in self.records:
                return None
            
            record = self.records[record_id]
            
            # This is a simplified implementation
            # In a real system, you'd store the Merkle tree structure
            return [record.merkle_root]
            
        except Exception as e:
            logger.error(f"Error creating Merkle proof: {e}")
            return None
    
    def verify_merkle_proof(
        self,
        record_id: str,
        component_data: str,
        proof: List[str]
    ) -> bool:
        """
        Verify Merkle proof for a component.
        
        Args:
            record_id: ID of the integrity record
            component_data: Data of the component to verify
            proof: Merkle proof
            
        Returns:
            True if proof is valid
        """
        try:
            if record_id not in self.records:
                return False
            
            record = self.records[record_id]
            leaf_hash = self.crypto_utils.generate_hash(component_data.encode())
            
            return self.crypto_utils.verify_merkle_proof(
                leaf_hash,
                proof,
                record.merkle_root
            )
            
        except Exception as e:
            logger.error(f"Error verifying Merkle proof: {e}")
            return False
    
    def get_integrity_record(self, record_id: str) -> Optional[IntegrityRecord]:
        """
        Get integrity record by ID.
        
        Args:
            record_id: ID of the record
            
        Returns:
            IntegrityRecord object or None
        """
        return self.records.get(record_id)
    
    def list_integrity_records(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> List[IntegrityRecord]:
        """
        List integrity records with pagination.
        
        Args:
            limit: Maximum number of records to return
            offset: Number of records to skip
            
        Returns:
            List of IntegrityRecord objects
        """
        records = list(self.records.values())
        records.sort(key=lambda x: x.timestamp, reverse=True)
        return records[offset:offset + limit]
    
    def delete_integrity_record(self, record_id: str) -> bool:
        """
        Delete an integrity record.
        
        Args:
            record_id: ID of the record to delete
            
        Returns:
            True if deleted successfully
        """
        if record_id in self.records:
            del self.records[record_id]
            logger.info(f"Deleted integrity record: {record_id}")
            return True
        return False
    
    def batch_verify_integrity(
        self,
        verifications: List[Tuple[str, Any]]
    ) -> List[VerificationResult]:
        """
        Verify integrity for multiple records in batch.
        
        Args:
            verifications: List of (record_id, data) tuples
            
        Returns:
            List of VerificationResult objects
        """
        results = []
        for record_id, data in verifications:
            result = self.verify_data_integrity(record_id, data)
            results.append(result)
        return results
    
    def get_verification_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about integrity verifications.
        
        Returns:
            Dictionary with verification statistics
        """
        total_records = len(self.records)
        verified_records = sum(1 for r in self.records.values() if r.verification_count > 0)
        total_verifications = sum(r.verification_count for r in self.records.values())
        
        recent_verifications = sum(
            1 for r in self.records.values() 
            if r.last_verified and r.last_verified > datetime.now() - timedelta(days=1)
        )
        
        return {
            'total_records': total_records,
            'verified_records': verified_records,
            'total_verifications': total_verifications,
            'recent_verifications': recent_verifications,
            'verification_rate': verified_records / total_records if total_records > 0 else 0
        }
    
    def export_integrity_records(self) -> Dict[str, Any]:
        """
        Export all integrity records for backup.
        
        Returns:
            Dictionary with all records
        """
        export_data = {
            'timestamp': datetime.now().isoformat(),
            'total_records': len(self.records),
            'records': {}
        }
        
        for record_id, record in self.records.items():
            export_data['records'][record_id] = {
                'id': record.id,
                'data_hash': record.data_hash,
                'merkle_root': record.merkle_root,
                'timestamp': record.timestamp.isoformat(),
                'metadata': record.metadata,
                'verification_count': record.verification_count,
                'last_verified': record.last_verified.isoformat() if record.last_verified else None
            }
        
        return export_data
    
    def import_integrity_records(self, import_data: Dict[str, Any]) -> int:
        """
        Import integrity records from backup.
        
        Args:
            import_data: Dictionary with records to import
            
        Returns:
            Number of records imported
        """
        imported_count = 0
        
        for record_id, record_data in import_data.get('records', {}).items():
            try:
                record = IntegrityRecord(
                    id=record_data['id'],
                    data_hash=record_data['data_hash'],
                    merkle_root=record_data['merkle_root'],
                    timestamp=datetime.fromisoformat(record_data['timestamp']),
                    metadata=record_data['metadata'],
                    verification_count=record_data['verification_count'],
                    last_verified=datetime.fromisoformat(record_data['last_verified']) if record_data.get('last_verified') else None
                )
                
                self.records[record_id] = record
                imported_count += 1
                
            except Exception as e:
                logger.error(f"Error importing record {record_id}: {e}")
        
        logger.info(f"Imported {imported_count} integrity records")
        return imported_count
    
    def _extract_data_components(self, data: Any) -> List[str]:
        """
        Extract components from data for Merkle tree creation.
        
        Args:
            data: Data to extract components from
            
        Returns:
            List of string components
        """
        components = []
        
        if isinstance(data, dict):
            for key, value in sorted(data.items()):
                components.append(f"{key}:{str(value)}")
        elif isinstance(data, list):
            for i, item in enumerate(data):
                components.append(f"{i}:{str(item)}")
        else:
            # For non-structured data, create artificial components
            data_str = str(data)
            chunk_size = max(1, len(data_str) // 4)  # Split into 4 chunks
            for i in range(0, len(data_str), chunk_size):
                components.append(data_str[i:i + chunk_size])
        
        return components if components else [str(data)]