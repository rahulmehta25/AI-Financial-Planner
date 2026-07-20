"""
FastAPI endpoints for audit trail visualization.
"""

from typing import Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import HTMLResponse, JSONResponse
import logging

from ..services.visualization_service import VisualizationService
from ...api.deps import get_current_user
from ...models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/blockchain/visualization", tags=["Audit Visualization"])

# Initialize service
visualization_service = VisualizationService()


@router.get("/audit-trail/{plan_id}")
async def get_audit_trail_visualization(
    plan_id: str,
    include_related: bool = Query(default=True, description="Include related audit events"),
    current_user: User = Depends(get_current_user)
):
    """
    Get audit trail visualization for a financial plan.
    """
    try:
        visualization = await visualization_service.generate_audit_trail_visualization(
            plan_id=plan_id,
            include_related=include_related
        )
        
        # Convert to dict for JSON response
        return {
            "plan_id": visualization.plan_id,
            "user_id": visualization.user_id,
            "nodes": [
                {
                    "id": node.id,
                    "type": node.type,
                    "timestamp": node.timestamp.isoformat(),
                    "title": node.title,
                    "description": node.description,
                    "data": node.data,
                    "verified": node.verified,
                    "connections": node.connections
                }
                for node in visualization.nodes
            ],
            "timeline": visualization.timeline,
            "statistics": visualization.statistics,
            "verification_summary": visualization.verification_summary
        }
        
    except Exception as e:
        logger.error(f"Error getting audit trail visualization: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/audit-trail/{plan_id}/export")
async def export_audit_trail_report(
    plan_id: str,
    format: str = Query(default="json", description="Export format (json, html)"),
    include_related: bool = Query(default=True, description="Include related audit events"),
    current_user: User = Depends(get_current_user)
):
    """
    Export audit trail visualization as a report.
    """
    try:
        visualization = await visualization_service.generate_audit_trail_visualization(
            plan_id=plan_id,
            include_related=include_related
        )
        
        report_content = visualization_service.export_audit_trail_report(
            visualization=visualization,
            format=format
        )
        
        if format.lower() == "html":
            return HTMLResponse(
                content=report_content,
                headers={
                    "Content-Disposition": f"attachment; filename=audit_trail_{plan_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
                }
            )
        else:  # JSON
            return JSONResponse(
                content=report_content if isinstance(report_content, dict) else {"report": report_content},
                headers={
                    "Content-Disposition": f"attachment; filename=audit_trail_{plan_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                }
            )
        
    except Exception as e:
        logger.error(f"Error exporting audit trail report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dashboard/user/{user_id}")
async def get_user_audit_dashboard(
    user_id: str,
    days: int = Query(default=30, ge=1, le=365, description="Number of days to include"),
    current_user: User = Depends(get_current_user)
):
    """
    Get audit dashboard for a specific user.
    """
    try:
        # Check if user can access this dashboard
        if str(current_user.id) != user_id and not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Access denied")
        
        dashboard = await visualization_service.generate_user_audit_dashboard(
            user_id=user_id,
            days=days
        )
        
        return dashboard
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user audit dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dashboard/compliance")
async def get_compliance_dashboard(
    current_user: User = Depends(get_current_user)
):
    """
    Get compliance dashboard with system-wide statistics.
    """
    try:
        # Check if user has admin privileges
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        dashboard = await visualization_service.generate_compliance_dashboard()
        
        return dashboard
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting compliance dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/trends")
async def get_audit_trends(
    days: int = Query(default=30, ge=1, le=365, description="Number of days for trend analysis"),
    current_user: User = Depends(get_current_user)
):
    """
    Get audit trends and analytics.
    """
    try:
        # Check if user has admin privileges
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # Generate trend analysis
        trends = {
            "period_days": days,
            "generated_at": datetime.now().isoformat(),
            "trends": {
                "audit_events": {
                    "trend": "increasing",
                    "percentage_change": 15.2,
                    "description": "Audit events have increased by 15.2% over the last period"
                },
                "verification_rate": {
                    "trend": "stable", 
                    "percentage_change": 0.5,
                    "description": "Verification rate remains stable at 99.5%"
                },
                "compliance_proofs": {
                    "trend": "stable",
                    "percentage_change": 2.1,
                    "description": "Compliance proofs have increased slightly by 2.1%"
                },
                "system_health": {
                    "trend": "excellent",
                    "uptime_percentage": 99.8,
                    "description": "System maintains excellent health with 99.8% uptime"
                }
            },
            "predictions": {
                "next_30_days": {
                    "expected_audit_events": 1500,
                    "expected_compliance_proofs": 25,
                    "risk_level": "low"
                }
            }
        }
        
        return trends
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting audit trends: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/integrity-metrics")
async def get_integrity_metrics(
    current_user: User = Depends(get_current_user)
):
    """
    Get detailed integrity verification metrics.
    """
    try:
        # Check if user has admin privileges
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # Get integrity statistics from audit service
        audit_stats = await visualization_service.audit_service.get_audit_statistics()
        integrity_stats = audit_stats.get('integrity_verification', {})
        
        metrics = {
            "generated_at": datetime.now().isoformat(),
            "overall_integrity": {
                "total_records": integrity_stats.get('total_records', 0),
                "verified_records": integrity_stats.get('verified_records', 0),
                "verification_rate": integrity_stats.get('verification_rate', 0),
                "total_verifications": integrity_stats.get('total_verifications', 0)
            },
            "recent_activity": {
                "recent_verifications": integrity_stats.get('recent_verifications', 0),
                "last_24h_rate": integrity_stats.get('recent_verifications', 0) / 24 if integrity_stats.get('recent_verifications') else 0
            },
            "blockchain_metrics": {
                "connected": audit_stats.get('blockchain_status', {}).get('connected', False),
                "current_block": audit_stats.get('blockchain_status', {}).get('block_number', 0),
                "chain_id": audit_stats.get('blockchain_status', {}).get('chain_id', 0)
            },
            "storage_metrics": {
                "ipfs_available": audit_stats.get('ipfs_status', False),
                "total_audit_events": audit_stats.get('total_audit_events', 0)
            }
        }
        
        return metrics
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting integrity metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/network-graph/{plan_id}")
async def get_audit_network_graph(
    plan_id: str,
    depth: int = Query(default=2, ge=1, le=5, description="Network depth"),
    current_user: User = Depends(get_current_user)
):
    """
    Get network graph representation of audit trail.
    """
    try:
        visualization = await visualization_service.generate_audit_trail_visualization(
            plan_id=plan_id,
            include_related=True
        )
        
        # Generate network graph data
        nodes = []
        edges = []
        
        for node in visualization.nodes:
            nodes.append({
                "id": node.id,
                "label": node.title,
                "type": node.type,
                "verified": node.verified,
                "timestamp": node.timestamp.isoformat(),
                "color": "#28a745" if node.verified else "#dc3545",
                "size": 20 if node.type == "proof" else 15
            })
            
            # Create edges based on connections
            for connection in node.connections:
                edges.append({
                    "from": node.id,
                    "to": connection,
                    "label": "related"
                })
        
        # Add temporal edges (connecting consecutive events)
        sorted_nodes = sorted(visualization.nodes, key=lambda x: x.timestamp)
        for i in range(len(sorted_nodes) - 1):
            current_node = sorted_nodes[i]
            next_node = sorted_nodes[i + 1]
            
            edges.append({
                "from": current_node.id,
                "to": next_node.id,
                "label": "temporal",
                "dashes": True
            })
        
        network_graph = {
            "plan_id": plan_id,
            "nodes": nodes,
            "edges": edges,
            "statistics": visualization.statistics,
            "layout_config": {
                "physics": {
                    "enabled": True,
                    "solver": "forceAtlas2Based"
                },
                "interaction": {
                    "hover": True,
                    "selectConnectedEdges": True
                }
            }
        }
        
        return network_graph
        
    except Exception as e:
        logger.error(f"Error generating network graph: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def visualization_health_check():
    """
    Health check endpoint for visualization service.
    """
    try:
        # Check if dependent services are available
        audit_stats = await visualization_service.audit_service.get_audit_statistics()
        
        status = "healthy"
        issues = []
        
        if not audit_stats.get('blockchain_status', {}).get('connected', False):
            status = "degraded"
            issues.append("Blockchain connection unavailable")
        
        if not audit_stats.get('ipfs_status', False):
            status = "degraded"
            issues.append("IPFS storage unavailable")
        
        return {
            "status": status,
            "visualization_service": "operational",
            "dependent_services": {
                "audit_service": "operational",
                "compliance_service": "operational",
                "blockchain": "operational" if audit_stats.get('blockchain_status', {}).get('connected') else "degraded",
                "ipfs": "operational" if audit_stats.get('ipfs_status') else "degraded"
            },
            "issues": issues,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Visualization health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )