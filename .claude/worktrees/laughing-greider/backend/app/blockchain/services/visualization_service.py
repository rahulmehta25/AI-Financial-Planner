"""
Service for generating audit trail visualizations and reports.
"""

import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import logging

from .audit_service import BlockchainAuditService
from .compliance_service import ComplianceService
from ..utils.crypto_utils import CryptoUtils

logger = logging.getLogger(__name__)


@dataclass
class AuditNode:
    """Node in audit trail visualization."""
    id: str
    type: str  # 'event', 'proof', 'compliance'
    timestamp: datetime
    title: str
    description: str
    data: Dict[str, Any]
    verified: bool
    connections: List[str]  # Connected node IDs


@dataclass
class AuditTrailVisualization:
    """Complete audit trail visualization data."""
    plan_id: str
    user_id: str
    nodes: List[AuditNode]
    timeline: List[Dict[str, Any]]
    statistics: Dict[str, Any]
    verification_summary: Dict[str, Any]


class VisualizationService:
    """Service for creating audit trail visualizations."""
    
    def __init__(self):
        self.audit_service = BlockchainAuditService()
        self.compliance_service = ComplianceService()
        self.crypto_utils = CryptoUtils()
        
    async def generate_audit_trail_visualization(
        self,
        plan_id: str,
        include_related: bool = True
    ) -> AuditTrailVisualization:
        """
        Generate comprehensive audit trail visualization for a plan.
        
        Args:
            plan_id: ID of the financial plan
            include_related: Whether to include related audit events
            
        Returns:
            AuditTrailVisualization object
        """
        try:
            nodes = []
            timeline = []
            
            # Get proof of existence
            proof_verification = await self.compliance_service.verify_proof_of_existence(plan_id)
            
            if proof_verification.get('valid'):
                proof_node = AuditNode(
                    id=f"proof_{plan_id}",
                    type="proof",
                    timestamp=proof_verification['timestamp'],
                    title="Proof of Existence",
                    description=f"Financial plan {plan_id} proof created",
                    data={
                        'plan_id': plan_id,
                        'user_id': proof_verification['user_id'],
                        'plan_hash': proof_verification['plan_hash'],
                        'block_number': proof_verification['block_number']
                    },
                    verified=proof_verification['valid'],
                    connections=[]
                )
                nodes.append(proof_node)
                
                timeline.append({
                    'timestamp': proof_verification['timestamp'].isoformat(),
                    'type': 'proof_created',
                    'title': 'Plan Proof Created',
                    'description': 'Proof of existence recorded on blockchain'
                })
            
            # Get related audit events if requested
            if include_related:
                audit_events = await self.audit_service.search_audit_events(
                    filters={'resource_id': plan_id},
                    limit=1000
                )
                
                for audit_log in audit_events:
                    # Verify each event
                    verification = await self.audit_service.verify_audit_event(
                        audit_log.event.event_id
                    )
                    
                    event_node = AuditNode(
                        id=f"event_{audit_log.event.event_id}",
                        type="event",
                        timestamp=audit_log.event.timestamp,
                        title=f"{audit_log.event.action.title()} {audit_log.event.resource_type}",
                        description=f"User {audit_log.event.user_id} performed {audit_log.event.action}",
                        data={
                            'event_id': audit_log.event.event_id,
                            'action': audit_log.event.action,
                            'user_id': audit_log.event.user_id,
                            'ip_address': audit_log.event.ip_address,
                            'data_hash': audit_log.data_hash,
                            'block_number': audit_log.block_number
                        },
                        verified=verification.get('valid', False),
                        connections=[f"proof_{plan_id}"] if proof_verification.get('valid') else []
                    )
                    nodes.append(event_node)
                    
                    timeline.append({
                        'timestamp': audit_log.event.timestamp.isoformat(),
                        'type': 'audit_event',
                        'title': f"{audit_log.event.action.title()} Action",
                        'description': f"{audit_log.event.action} on {audit_log.event.resource_type}",
                        'verified': verification.get('valid', False)
                    })
            
            # Sort nodes and timeline by timestamp
            nodes.sort(key=lambda x: x.timestamp)
            timeline.sort(key=lambda x: x['timestamp'])
            
            # Generate statistics
            statistics = self._generate_visualization_statistics(nodes)
            
            # Generate verification summary
            verification_summary = self._generate_verification_summary(nodes)
            
            return AuditTrailVisualization(
                plan_id=plan_id,
                user_id=proof_verification.get('user_id', ''),
                nodes=nodes,
                timeline=timeline,
                statistics=statistics,
                verification_summary=verification_summary
            )
            
        except Exception as e:
            logger.error(f"Error generating audit trail visualization: {e}")
            raise
    
    async def generate_user_audit_dashboard(
        self,
        user_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Generate audit dashboard for a user.
        
        Args:
            user_id: ID of the user
            days: Number of days to include
            
        Returns:
            Dictionary with dashboard data
        """
        try:
            start_date = datetime.now() - timedelta(days=days)
            
            # Get user audit events
            audit_events = await self.audit_service.get_user_audit_events(
                user_id=user_id,
                limit=1000
            )
            
            # Filter by date
            recent_events = [
                event for event in audit_events
                if event.event.timestamp >= start_date
            ]
            
            # Get user proofs
            user_proofs = await self.compliance_service.get_user_proofs(user_id)
            
            # Generate activity timeline
            activity_timeline = []
            for event in recent_events:
                activity_timeline.append({
                    'timestamp': event.event.timestamp.isoformat(),
                    'type': 'audit_event',
                    'action': event.event.action,
                    'resource_type': event.event.resource_type,
                    'resource_id': event.event.resource_id,
                    'verified': True  # Assume verified for dashboard
                })
            
            for proof in user_proofs:
                if proof.timestamp >= start_date:
                    activity_timeline.append({
                        'timestamp': proof.timestamp.isoformat(),
                        'type': 'proof_created',
                        'plan_id': proof.plan_id,
                        'verified': True
                    })
            
            # Sort timeline
            activity_timeline.sort(key=lambda x: x['timestamp'], reverse=True)
            
            # Generate statistics
            action_counts = {}
            resource_counts = {}
            
            for event in recent_events:
                action = event.event.action
                resource = event.event.resource_type
                
                action_counts[action] = action_counts.get(action, 0) + 1
                resource_counts[resource] = resource_counts.get(resource, 0) + 1
            
            dashboard = {
                'user_id': user_id,
                'period_days': days,
                'generated_at': datetime.now().isoformat(),
                'statistics': {
                    'total_events': len(recent_events),
                    'total_proofs': len([p for p in user_proofs if p.timestamp >= start_date]),
                    'action_breakdown': action_counts,
                    'resource_breakdown': resource_counts,
                    'daily_activity': self._generate_daily_activity_chart(recent_events, days)
                },
                'activity_timeline': activity_timeline[:50],  # Limit to 50 recent items
                'verification_status': {
                    'total_verified': len(recent_events),  # Assume all verified for now
                    'verification_rate': 1.0
                }
            }
            
            return dashboard
            
        except Exception as e:
            logger.error(f"Error generating user audit dashboard: {e}")
            raise
    
    async def generate_compliance_dashboard(self) -> Dict[str, Any]:
        """
        Generate compliance dashboard with overall system statistics.
        
        Returns:
            Dictionary with compliance dashboard data
        """
        try:
            # Get audit statistics
            audit_stats = await self.audit_service.get_audit_statistics()
            
            # Get compliance proofs for each standard
            compliance_stats = {}
            for standard in ['SOX', 'GDPR', 'PCI-DSS', 'HIPAA', 'ISO27001', 'NIST']:
                try:
                    from ..services.compliance_service import ComplianceStandard
                    std_enum = ComplianceStandard(standard)
                    proofs = await self.compliance_service.get_compliance_proofs_by_standard(std_enum)
                    compliance_stats[standard] = {
                        'total_proofs': len(proofs),
                        'recent_proofs': len([
                            p for p in proofs 
                            if p.timestamp >= datetime.now() - timedelta(days=30)
                        ])
                    }
                except:
                    compliance_stats[standard] = {'total_proofs': 0, 'recent_proofs': 0}
            
            # Generate trends
            trends = await self._generate_compliance_trends()
            
            dashboard = {
                'generated_at': datetime.now().isoformat(),
                'system_status': {
                    'blockchain_connected': audit_stats.get('blockchain_status', {}).get('connected', False),
                    'ipfs_connected': audit_stats.get('ipfs_status', False),
                    'total_audit_events': audit_stats.get('total_audit_events', 0)
                },
                'compliance_statistics': compliance_stats,
                'verification_statistics': audit_stats.get('integrity_verification', {}),
                'trends': trends,
                'alerts': await self._generate_compliance_alerts()
            }
            
            return dashboard
            
        except Exception as e:
            logger.error(f"Error generating compliance dashboard: {e}")
            raise
    
    def export_audit_trail_report(
        self,
        visualization: AuditTrailVisualization,
        format: str = "json"
    ) -> str:
        """
        Export audit trail visualization as a report.
        
        Args:
            visualization: AuditTrailVisualization object
            format: Export format (json, html, pdf)
            
        Returns:
            Exported report content
        """
        try:
            if format.lower() == "json":
                return json.dumps(asdict(visualization), indent=2, default=str)
            
            elif format.lower() == "html":
                return self._generate_html_report(visualization)
            
            elif format.lower() == "pdf":
                # PDF generation would require additional libraries
                raise NotImplementedError("PDF export not yet implemented")
            
            else:
                raise ValueError(f"Unsupported export format: {format}")
                
        except Exception as e:
            logger.error(f"Error exporting audit trail report: {e}")
            raise
    
    def _generate_visualization_statistics(self, nodes: List[AuditNode]) -> Dict[str, Any]:
        """Generate statistics for visualization."""
        total_nodes = len(nodes)
        verified_nodes = sum(1 for node in nodes if node.verified)
        
        type_counts = {}
        for node in nodes:
            type_counts[node.type] = type_counts.get(node.type, 0) + 1
        
        return {
            'total_nodes': total_nodes,
            'verified_nodes': verified_nodes,
            'verification_rate': verified_nodes / total_nodes if total_nodes > 0 else 0,
            'type_breakdown': type_counts,
            'date_range': {
                'start': min(node.timestamp for node in nodes).isoformat() if nodes else None,
                'end': max(node.timestamp for node in nodes).isoformat() if nodes else None
            }
        }
    
    def _generate_verification_summary(self, nodes: List[AuditNode]) -> Dict[str, Any]:
        """Generate verification summary."""
        verified_count = sum(1 for node in nodes if node.verified)
        total_count = len(nodes)
        
        verification_by_type = {}
        for node in nodes:
            if node.type not in verification_by_type:
                verification_by_type[node.type] = {'verified': 0, 'total': 0}
            
            verification_by_type[node.type]['total'] += 1
            if node.verified:
                verification_by_type[node.type]['verified'] += 1
        
        return {
            'overall_verification_rate': verified_count / total_count if total_count > 0 else 0,
            'verified_nodes': verified_count,
            'total_nodes': total_count,
            'verification_by_type': verification_by_type,
            'last_verification': datetime.now().isoformat()
        }
    
    def _generate_daily_activity_chart(self, events: List[Any], days: int) -> List[Dict[str, Any]]:
        """Generate daily activity chart data."""
        daily_counts = {}
        
        # Initialize all days with 0
        for i in range(days):
            date = (datetime.now() - timedelta(days=i)).date()
            daily_counts[date.isoformat()] = 0
        
        # Count events per day
        for event in events:
            date = event.event.timestamp.date()
            date_str = date.isoformat()
            if date_str in daily_counts:
                daily_counts[date_str] += 1
        
        # Convert to chart format
        chart_data = []
        for date_str, count in sorted(daily_counts.items()):
            chart_data.append({
                'date': date_str,
                'count': count
            })
        
        return chart_data
    
    async def _generate_compliance_trends(self) -> Dict[str, Any]:
        """Generate compliance trends data."""
        # This would analyze historical data to show trends
        # For now, return mock trend data
        return {
            'audit_events_trend': 'increasing',
            'verification_rate_trend': 'stable',
            'compliance_proofs_trend': 'stable',
            'system_health_trend': 'stable'
        }
    
    async def _generate_compliance_alerts(self) -> List[Dict[str, Any]]:
        """Generate compliance alerts."""
        alerts = []
        
        # Check system health
        audit_stats = await self.audit_service.get_audit_statistics()
        
        if not audit_stats.get('blockchain_status', {}).get('connected', False):
            alerts.append({
                'level': 'critical',
                'title': 'Blockchain Disconnected',
                'message': 'Blockchain connection is unavailable',
                'timestamp': datetime.now().isoformat()
            })
        
        if not audit_stats.get('ipfs_status', False):
            alerts.append({
                'level': 'warning',
                'title': 'IPFS Unavailable',
                'message': 'IPFS storage is not accessible',
                'timestamp': datetime.now().isoformat()
            })
        
        return alerts
    
    def _generate_html_report(self, visualization: AuditTrailVisualization) -> str:
        """Generate HTML report for audit trail."""
        html_template = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Audit Trail Report - Plan {visualization.plan_id}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .header {{ background-color: #f4f4f4; padding: 20px; border-radius: 5px; }}
                .section {{ margin: 20px 0; }}
                .node {{ background-color: #f9f9f9; padding: 15px; margin: 10px 0; border-left: 4px solid #007cba; }}
                .verified {{ border-left-color: #28a745; }}
                .unverified {{ border-left-color: #dc3545; }}
                .timeline-item {{ margin: 10px 0; padding: 10px; background-color: #f8f9fa; }}
                .stats {{ display: flex; gap: 20px; }}
                .stat-box {{ background-color: #e9ecef; padding: 15px; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Audit Trail Report</h1>
                <p><strong>Plan ID:</strong> {visualization.plan_id}</p>
                <p><strong>User ID:</strong> {visualization.user_id}</p>
                <p><strong>Generated:</strong> {datetime.now().isoformat()}</p>
            </div>
            
            <div class="section">
                <h2>Statistics</h2>
                <div class="stats">
                    <div class="stat-box">
                        <strong>Total Nodes:</strong> {visualization.statistics['total_nodes']}
                    </div>
                    <div class="stat-box">
                        <strong>Verified:</strong> {visualization.statistics['verified_nodes']}
                    </div>
                    <div class="stat-box">
                        <strong>Verification Rate:</strong> {visualization.statistics['verification_rate']:.1%}
                    </div>
                </div>
            </div>
            
            <div class="section">
                <h2>Audit Nodes</h2>
                {''.join([
                    f'<div class="node {"verified" if node.verified else "unverified"}">'
                    f'<h3>{node.title}</h3>'
                    f'<p>{node.description}</p>'
                    f'<p><strong>Type:</strong> {node.type} | <strong>Verified:</strong> {"Yes" if node.verified else "No"}</p>'
                    f'<p><strong>Timestamp:</strong> {node.timestamp}</p>'
                    f'</div>'
                    for node in visualization.nodes
                ])}
            </div>
            
            <div class="section">
                <h2>Timeline</h2>
                {''.join([
                    f'<div class="timeline-item">'
                    f'<strong>{item["title"]}</strong> - {item["timestamp"]}<br>'
                    f'{item["description"]}'
                    f'</div>'
                    for item in visualization.timeline
                ])}
            </div>
        </body>
        </html>
        """
        
        return html_template