"""
FastAPI endpoints for blockchain audit operations.
"""

from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Query, Request
from fastapi.responses import JSONResponse
import logging

from ..services.audit_service import BlockchainAuditService
from ..models.audit_models import (
    AuditEventCreate,
    AuditEvent,
    VerificationResult,
    AuditSearchFilters,
    AuditStatistics
)
from ...api.deps import get_current_user
from ...models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/blockchain/audit", tags=["Blockchain Audit"])

# Initialize service
audit_service = BlockchainAuditService()


@router.post("/events", response_model=AuditEvent)
async def create_audit_event(
    event_data: AuditEventCreate,
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """
    Create a new audit event and log it to blockchain and IPFS.
    """
    try:
        # Extract request metadata
        ip_address = request.client.host
        user_agent = request.headers.get("user-agent")
        
        # Override user_id with authenticated user if needed
        if not event_data.user_id:
            event_data.user_id = str(current_user.id)
        
        # Log audit event
        audit_log = await audit_service.log_audit_event(
            user_id=event_data.user_id,
            action=event_data.action.value,
            resource_type=event_data.resource_type.value,
            resource_id=event_data.resource_id,
            data=event_data.data,
            ip_address=ip_address or event_data.ip_address,
            user_agent=user_agent or event_data.user_agent,
            session_id=event_data.session_id
        )
        
        # Convert to response model
        return AuditEvent(
            event_id=audit_log.event.event_id,
            user_id=audit_log.event.user_id,
            action=audit_log.event.action,
            resource_type=audit_log.event.resource_type,
            resource_id=audit_log.event.resource_id,
            timestamp=audit_log.event.timestamp,
            data=audit_log.event.data,
            ip_address=audit_log.event.ip_address,
            user_agent=audit_log.event.user_agent,
            session_id=audit_log.event.session_id,
            data_hash=audit_log.data_hash,
            ipfs_hash=audit_log.ipfs_hash,
            blockchain_tx_hash=audit_log.blockchain_tx_hash,
            block_number=audit_log.block_number,
            verification_status=audit_log.verification_status
        )
        
    except Exception as e:
        logger.error(f"Error creating audit event: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/events/{event_id}", response_model=AuditEvent)
async def get_audit_event(
    event_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve an audit event by ID.
    """
    try:
        audit_log = await audit_service.get_audit_event(event_id)
        
        if not audit_log:
            raise HTTPException(status_code=404, detail="Audit event not found")
        
        return AuditEvent(
            event_id=audit_log.event.event_id,
            user_id=audit_log.event.user_id,
            action=audit_log.event.action,
            resource_type=audit_log.event.resource_type,
            resource_id=audit_log.event.resource_id,
            timestamp=audit_log.event.timestamp,
            data=audit_log.event.data,
            ip_address=audit_log.event.ip_address,
            user_agent=audit_log.event.user_agent,
            session_id=audit_log.event.session_id,
            data_hash=audit_log.data_hash,
            ipfs_hash=audit_log.ipfs_hash,
            blockchain_tx_hash=audit_log.blockchain_tx_hash,
            block_number=audit_log.block_number,
            verification_status=audit_log.verification_status
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving audit event: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/events/{event_id}/verify", response_model=VerificationResult)
async def verify_audit_event(
    event_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Verify the integrity of an audit event.
    """
    try:
        verification_result = await audit_service.verify_audit_event(event_id)
        
        return VerificationResult(
            valid=verification_result.get('valid', False),
            event_id=verification_result.get('event_id'),
            verification_time=verification_result.get('verification_time'),
            details=verification_result.get('details', {}),
            error=verification_result.get('error')
        )
        
    except Exception as e:
        logger.error(f"Error verifying audit event: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/users/{user_id}/events", response_model=List[AuditEvent])
async def get_user_audit_events(
    user_id: str,
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user)
):
    """
    Get audit events for a specific user.
    """
    try:
        # Check if user can access these events
        # (implement proper authorization logic here)
        if str(current_user.id) != user_id and not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Access denied")
        
        audit_logs = await audit_service.get_user_audit_events(
            user_id=user_id,
            limit=limit,
            offset=offset
        )
        
        return [
            AuditEvent(
                event_id=log.event.event_id,
                user_id=log.event.user_id,
                action=log.event.action,
                resource_type=log.event.resource_type,
                resource_id=log.event.resource_id,
                timestamp=log.event.timestamp,
                data=log.event.data,
                ip_address=log.event.ip_address,
                user_agent=log.event.user_agent,
                session_id=log.event.session_id,
                data_hash=log.data_hash,
                ipfs_hash=log.ipfs_hash,
                blockchain_tx_hash=log.blockchain_tx_hash,
                block_number=log.block_number,
                verification_status=log.verification_status
            )
            for log in audit_logs
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user audit events: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/events/search", response_model=List[AuditEvent])
async def search_audit_events(
    filters: AuditSearchFilters,
    current_user: User = Depends(get_current_user)
):
    """
    Search audit events based on filters.
    """
    try:
        # Convert filters to dict
        search_filters = {
            k: v for k, v in filters.dict().items() 
            if v is not None and k not in ['limit', 'offset']
        }
        
        # Convert enum values to strings
        if 'action' in search_filters:
            search_filters['action'] = search_filters['action'].value
        if 'resource_type' in search_filters:
            search_filters['resource_type'] = search_filters['resource_type'].value
        
        audit_logs = await audit_service.search_audit_events(
            filters=search_filters,
            limit=filters.limit,
            offset=filters.offset
        )
        
        return [
            AuditEvent(
                event_id=log.event.event_id,
                user_id=log.event.user_id,
                action=log.event.action,
                resource_type=log.event.resource_type,
                resource_id=log.event.resource_id,
                timestamp=log.event.timestamp,
                data=log.event.data,
                ip_address=log.event.ip_address,
                user_agent=log.event.user_agent,
                session_id=log.event.session_id,
                data_hash=log.data_hash,
                ipfs_hash=log.ipfs_hash,
                blockchain_tx_hash=log.blockchain_tx_hash,
                block_number=log.block_number,
                verification_status=log.verification_status
            )
            for log in audit_logs
        ]
        
    except Exception as e:
        logger.error(f"Error searching audit events: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics", response_model=AuditStatistics)
async def get_audit_statistics(
    current_user: User = Depends(get_current_user)
):
    """
    Get audit system statistics.
    """
    try:
        # Check if user has admin privileges
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        stats = await audit_service.get_audit_statistics()
        
        return AuditStatistics(
            total_audit_events=stats.get('total_audit_events', 0),
            blockchain_status=stats.get('blockchain_status', {}),
            integrity_verification=stats.get('integrity_verification', {}),
            ipfs_status=stats.get('ipfs_status', False),
            last_updated=stats.get('last_updated')
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting audit statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/events/batch", response_model=List[AuditEvent])
async def create_batch_audit_events(
    events: List[AuditEventCreate],
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """
    Create multiple audit events in batch.
    """
    try:
        if len(events) > 50:  # Limit batch size
            raise HTTPException(status_code=400, detail="Batch size too large (max 50)")
        
        # Extract request metadata
        ip_address = request.client.host
        user_agent = request.headers.get("user-agent")
        
        # Convert to batch format
        batch_events = []
        for event_data in events:
            batch_events.append({
                'user_id': event_data.user_id or str(current_user.id),
                'action': event_data.action.value,
                'resource_type': event_data.resource_type.value,
                'resource_id': event_data.resource_id,
                'data': event_data.data,
                'ip_address': ip_address or event_data.ip_address,
                'user_agent': user_agent or event_data.user_agent,
                'session_id': event_data.session_id
            })
        
        audit_logs = await audit_service.batch_log_events(batch_events)
        
        return [
            AuditEvent(
                event_id=log.event.event_id,
                user_id=log.event.user_id,
                action=log.event.action,
                resource_type=log.event.resource_type,
                resource_id=log.event.resource_id,
                timestamp=log.event.timestamp,
                data=log.event.data,
                ip_address=log.event.ip_address,
                user_agent=log.event.user_agent,
                session_id=log.event.session_id,
                data_hash=log.data_hash,
                ipfs_hash=log.ipfs_hash,
                blockchain_tx_hash=log.blockchain_tx_hash,
                block_number=log.block_number,
                verification_status=log.verification_status
            )
            for log in audit_logs
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating batch audit events: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """
    Health check endpoint for blockchain audit system.
    """
    try:
        # Check blockchain connection
        blockchain_connected = audit_service.blockchain_utils.is_connected()
        
        # Check IPFS connection
        ipfs_connected = await audit_service.ipfs_service.check_connection()
        
        status = "healthy" if blockchain_connected and ipfs_connected else "degraded"
        
        return {
            "status": status,
            "blockchain_connected": blockchain_connected,
            "ipfs_connected": ipfs_connected,
            "timestamp": "2024-01-01T10:00:00Z"  # Use actual timestamp
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": "2024-01-01T10:00:00Z"  # Use actual timestamp
            }
        )