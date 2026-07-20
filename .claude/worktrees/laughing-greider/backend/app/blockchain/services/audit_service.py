"""
Main blockchain audit service for immutable audit logging.
"""

import json
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
import logging

from .ipfs_service import IPFSService
from .integrity_service import IntegrityVerificationService
from ..utils.blockchain_utils import BlockchainUtils
from ..utils.crypto_utils import CryptoUtils
from ..config import get_blockchain_config

logger = logging.getLogger(__name__)


@dataclass
class AuditEvent:
    """Audit event data structure."""
    event_id: str
    user_id: str
    action: str
    resource_type: str
    resource_id: str
    timestamp: datetime
    data: Dict[str, Any]
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    session_id: Optional[str] = None
    

@dataclass
class AuditLog:
    """Complete audit log with blockchain and IPFS references."""
    event: AuditEvent
    data_hash: str
    ipfs_hash: str
    blockchain_tx_hash: str
    block_number: int
    verification_status: str = "pending"
    

class BlockchainAuditService:
    """Service for blockchain-based audit logging."""
    
    def __init__(self):
        self.config = get_blockchain_config()
        self.blockchain_utils = BlockchainUtils()
        self.ipfs_service = IPFSService()
        self.integrity_service = IntegrityVerificationService()
        self.crypto_utils = CryptoUtils()
        
    async def log_audit_event(
        self,
        user_id: str,
        action: str,
        resource_type: str,
        resource_id: str,
        data: Dict[str, Any],
        ip_address: str = None,
        user_agent: str = None,
        session_id: str = None
    ) -> AuditLog:
        """
        Log an audit event to blockchain and IPFS.
        
        Args:
            user_id: ID of the user performing the action
            action: Action being performed
            resource_type: Type of resource being accessed
            resource_id: ID of the resource
            data: Additional event data
            ip_address: IP address of the user
            user_agent: User agent string
            session_id: Session ID
            
        Returns:
            AuditLog object with blockchain and IPFS references
        """
        try:
            # Create audit event
            event = AuditEvent(
                event_id=str(uuid.uuid4()),
                user_id=user_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                timestamp=datetime.now(),
                data=data,
                ip_address=ip_address,
                user_agent=user_agent,
                session_id=session_id
            )
            
            # Serialize event data
            event_data = asdict(event)
            event_data['timestamp'] = event.timestamp.isoformat()
            
            # Generate data hash
            data_hash = self.crypto_utils.generate_hash(
                json.dumps(event_data, sort_keys=True).encode()
            )
            
            # Store detailed data in IPFS
            ipfs_result = await self.ipfs_service.add_json(
                event_data,
                encrypt=True
            )
            ipfs_hash = ipfs_result['ipfs_hash']
            
            # Pin the file in IPFS
            await self.ipfs_service.pin_file(ipfs_hash)
            
            # Create integrity record
            self.integrity_service.create_integrity_record(
                event.event_id,
                event_data,
                {'type': 'audit_event', 'resource_type': resource_type}
            )
            
            # Log to blockchain
            blockchain_tx_hash = await self._log_to_blockchain(
                event.event_id,
                user_id,
                action,
                int(event.timestamp.timestamp()),
                data_hash,
                ipfs_hash
            )
            
            # Wait for transaction confirmation
            receipt = self.blockchain_utils.wait_for_transaction_receipt(blockchain_tx_hash)
            
            # Create audit log
            audit_log = AuditLog(
                event=event,
                data_hash=data_hash,
                ipfs_hash=ipfs_hash,
                blockchain_tx_hash=blockchain_tx_hash,
                block_number=receipt['block_number'],
                verification_status="confirmed"
            )
            
            logger.info(f"Audit event logged: {event.event_id}")
            return audit_log
            
        except Exception as e:
            logger.error(f"Error logging audit event: {e}")
            raise
    
    async def get_audit_event(self, event_id: str) -> Optional[AuditLog]:
        """
        Retrieve an audit event by ID.
        
        Args:
            event_id: ID of the audit event
            
        Returns:
            AuditLog object or None if not found
        """
        try:
            # Get event from blockchain
            contract = self.blockchain_utils.get_audit_contract()
            
            result = self.blockchain_utils.call_contract_function(
                contract.functions.getAuditEvent(event_id)
            )
            
            if not result or not result[0]:  # Check if event exists
                return None
            
            user_id, action, timestamp, data_hash, ipfs_hash, block_number = result
            
            # Get detailed data from IPFS
            event_data = await self.ipfs_service.get_json(ipfs_hash)
            
            # Reconstruct audit event
            event = AuditEvent(
                event_id=event_id,
                user_id=event_data['user_id'],
                action=event_data['action'],
                resource_type=event_data['resource_type'],
                resource_id=event_data['resource_id'],
                timestamp=datetime.fromisoformat(event_data['timestamp']),
                data=event_data['data'],
                ip_address=event_data.get('ip_address'),
                user_agent=event_data.get('user_agent'),
                session_id=event_data.get('session_id')
            )
            
            audit_log = AuditLog(
                event=event,
                data_hash=data_hash.hex(),
                ipfs_hash=ipfs_hash,
                blockchain_tx_hash="",  # Would need to get from event logs
                block_number=block_number,
                verification_status="confirmed"
            )
            
            return audit_log
            
        except Exception as e:
            logger.error(f"Error retrieving audit event: {e}")
            return None
    
    async def get_user_audit_events(
        self,
        user_id: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[AuditLog]:
        """
        Get audit events for a specific user.
        
        Args:
            user_id: ID of the user
            limit: Maximum number of events to return
            offset: Number of events to skip
            
        Returns:
            List of AuditLog objects
        """
        try:
            contract = self.blockchain_utils.get_audit_contract()
            
            # Get user event IDs from blockchain
            event_ids = self.blockchain_utils.call_contract_function(
                contract.functions.getUserAuditEvents(user_id)
            )
            
            # Apply pagination
            paginated_ids = event_ids[offset:offset + limit]
            
            # Retrieve each event
            audit_logs = []
            for event_id in paginated_ids:
                audit_log = await self.get_audit_event(event_id)
                if audit_log:
                    audit_logs.append(audit_log)
            
            return audit_logs
            
        except Exception as e:
            logger.error(f"Error getting user audit events: {e}")
            return []
    
    async def verify_audit_event(self, event_id: str) -> Dict[str, Any]:
        """
        Verify the integrity of an audit event.
        
        Args:
            event_id: ID of the audit event
            
        Returns:
            Dictionary with verification results
        """
        try:
            # Get event from blockchain
            audit_log = await self.get_audit_event(event_id)
            if not audit_log:
                return {'valid': False, 'error': 'Event not found'}
            
            # Verify data integrity
            event_data = asdict(audit_log.event)
            event_data['timestamp'] = audit_log.event.timestamp.isoformat()
            
            verification_result = self.integrity_service.verify_data_integrity(
                event_id,
                event_data
            )
            
            # Verify blockchain data hash
            contract = self.blockchain_utils.get_audit_contract()
            blockchain_valid = self.blockchain_utils.call_contract_function(
                contract.functions.verifyEventIntegrity(
                    event_id,
                    bytes.fromhex(audit_log.data_hash)
                )
            )
            
            # Verify IPFS data integrity
            expected_hash = self.crypto_utils.generate_hash(
                json.dumps(event_data, sort_keys=True).encode()
            )
            ipfs_valid = await self.ipfs_service.verify_file_integrity(
                audit_log.ipfs_hash,
                expected_hash
            )
            
            return {
                'valid': verification_result.valid and blockchain_valid and ipfs_valid,
                'event_id': event_id,
                'integrity_check': verification_result.valid,
                'blockchain_check': blockchain_valid,
                'ipfs_check': ipfs_valid,
                'verification_time': datetime.now().isoformat(),
                'details': verification_result.details
            }
            
        except Exception as e:
            logger.error(f"Error verifying audit event: {e}")
            return {'valid': False, 'error': str(e)}
    
    async def search_audit_events(
        self,
        filters: Dict[str, Any],
        limit: int = 100,
        offset: int = 0
    ) -> List[AuditLog]:
        """
        Search audit events based on filters.
        
        Args:
            filters: Search filters (user_id, action, resource_type, etc.)
            limit: Maximum number of events to return
            offset: Number of events to skip
            
        Returns:
            List of matching AuditLog objects
        """
        try:
            # Get event logs from blockchain
            contract = self.blockchain_utils.get_audit_contract()
            
            # Build event filter
            event_filter = {}
            if filters.get('user_id'):
                event_filter['userId'] = filters['user_id']
            
            # Get audit event logs
            logs = self.blockchain_utils.get_event_logs(
                contract,
                'AuditEventLogged',
                argument_filters=event_filter
            )
            
            # Filter and retrieve events
            matching_events = []
            for log in logs[offset:offset + limit]:
                event_id = log['args']['eventId']
                audit_log = await self.get_audit_event(event_id)
                
                if audit_log and self._matches_filters(audit_log, filters):
                    matching_events.append(audit_log)
            
            return matching_events
            
        except Exception as e:
            logger.error(f"Error searching audit events: {e}")
            return []
    
    async def get_audit_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about audit events.
        
        Returns:
            Dictionary with audit statistics
        """
        try:
            contract = self.blockchain_utils.get_audit_contract()
            
            total_events = self.blockchain_utils.call_contract_function(
                contract.functions.getTotalEventCount()
            )
            
            # Get integrity statistics
            integrity_stats = self.integrity_service.get_verification_statistics()
            
            # Get blockchain network info
            network_info = self.blockchain_utils.get_network_info()
            
            return {
                'total_audit_events': total_events,
                'blockchain_status': {
                    'connected': network_info.get('is_connected', False),
                    'block_number': network_info.get('block_number', 0),
                    'chain_id': network_info.get('chain_id', 0)
                },
                'integrity_verification': integrity_stats,
                'ipfs_status': await self.ipfs_service.check_connection(),
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting audit statistics: {e}")
            return {}
    
    async def batch_log_events(self, events: List[Dict[str, Any]]) -> List[AuditLog]:
        """
        Log multiple audit events in batch.
        
        Args:
            events: List of event data dictionaries
            
        Returns:
            List of AuditLog objects
        """
        try:
            # Process events individually for now
            # In production, consider true batch processing for efficiency
            audit_logs = []
            
            for event_data in events:
                audit_log = await self.log_audit_event(**event_data)
                audit_logs.append(audit_log)
            
            return audit_logs
            
        except Exception as e:
            logger.error(f"Error batch logging events: {e}")
            raise
    
    async def _log_to_blockchain(
        self,
        event_id: str,
        user_id: str,
        action: str,
        timestamp: int,
        data_hash: str,
        ipfs_hash: str
    ) -> str:
        """
        Log audit event to blockchain.
        
        Args:
            event_id: Unique event identifier
            user_id: User performing the action
            action: Action description
            timestamp: Unix timestamp
            data_hash: Hash of event data
            ipfs_hash: IPFS hash for detailed data
            
        Returns:
            Transaction hash
        """
        try:
            contract = self.blockchain_utils.get_audit_contract()
            
            # Convert hash to bytes32
            data_hash_bytes = bytes.fromhex(data_hash)
            
            tx_hash = self.blockchain_utils.send_transaction(
                contract.functions.logAuditEvent(
                    event_id,
                    user_id,
                    action,
                    timestamp,
                    data_hash_bytes,
                    ipfs_hash
                )
            )
            
            return tx_hash
            
        except Exception as e:
            logger.error(f"Error logging to blockchain: {e}")
            raise
    
    def _matches_filters(self, audit_log: AuditLog, filters: Dict[str, Any]) -> bool:
        """
        Check if audit log matches search filters.
        
        Args:
            audit_log: AuditLog to check
            filters: Search filters
            
        Returns:
            True if matches all filters
        """
        for key, value in filters.items():
            if key == 'action' and audit_log.event.action != value:
                return False
            elif key == 'resource_type' and audit_log.event.resource_type != value:
                return False
            elif key == 'resource_id' and audit_log.event.resource_id != value:
                return False
            elif key == 'start_date':
                if audit_log.event.timestamp < datetime.fromisoformat(value):
                    return False
            elif key == 'end_date':
                if audit_log.event.timestamp > datetime.fromisoformat(value):
                    return False
        
        return True