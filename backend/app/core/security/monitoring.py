"""
Security Monitoring Module

Implements real-time security monitoring, threat detection,
anomaly detection, and incident management.
"""

import time
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set
from enum import Enum
from dataclasses import dataclass, field
import asyncio
from collections import deque, defaultdict
import json
import re
import redis.asyncio as redis
from sklearn.ensemble import IsolationForest
import numpy as np

from app.core.config import settings


class ThreatLevel(Enum):
    """Threat severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IncidentStatus(Enum):
    """Incident status states"""
    OPEN = "open"
    INVESTIGATING = "investigating"
    CONTAINED = "contained"
    RESOLVED = "resolved"
    FALSE_POSITIVE = "false_positive"


class AlertType(Enum):
    """Types of security alerts"""
    BRUTE_FORCE = "brute_force"
    SQL_INJECTION = "sql_injection"
    XSS_ATTEMPT = "xss_attempt"
    PATH_TRAVERSAL = "path_traversal"
    DDOS_ATTACK = "ddos_attack"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    DATA_EXFILTRATION = "data_exfiltration"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    ANOMALOUS_BEHAVIOR = "anomalous_behavior"
    COMPLIANCE_VIOLATION = "compliance_violation"
    MALWARE_DETECTED = "malware_detected"
    SUSPICIOUS_API_USAGE = "suspicious_api_usage"


@dataclass
class SecurityEvent:
    """Represents a security event"""
    event_id: str
    timestamp: datetime
    event_type: str
    source_ip: Optional[str]
    user_id: Optional[str]
    target_resource: Optional[str]
    action: str
    result: str
    metadata: Dict[str, Any]
    threat_indicators: List[str] = field(default_factory=list)


@dataclass
class SecurityIncident:
    """Represents a security incident"""
    incident_id: str
    created_at: datetime
    alert_type: AlertType
    threat_level: ThreatLevel
    status: IncidentStatus
    affected_users: List[str]
    affected_resources: List[str]
    events: List[SecurityEvent]
    description: str
    response_actions: List[str] = field(default_factory=list)
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None


@dataclass
class ThreatIndicator:
    """Threat indicator for detection"""
    indicator_type: str  # ip, domain, hash, pattern
    value: str
    threat_level: ThreatLevel
    source: str  # Where indicator came from
    last_seen: datetime
    hit_count: int = 0


class ThreatDetector:
    """
    Real-time threat detection system
    """
    
    def __init__(self):
        self.threat_indicators = {}
        self.detection_rules = []
        self.redis_client = None
        self.load_detection_rules()
        self.load_threat_indicators()
    
    async def initialize(self):
        """Initialize threat detector"""
        
        self.redis_client = await redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )
    
    def load_detection_rules(self):
        """Load threat detection rules"""
        
        self.detection_rules = [
            # SQL Injection patterns
            {
                "name": "sql_injection",
                "patterns": [
                    r"(\bunion\b.*\bselect\b)",
                    r"(\bselect\b.*\bfrom\b.*\bwhere\b)",
                    r"(\bdrop\b.*\btable\b)",
                    r"(\binsert\b.*\binto\b)",
                    r"(\bdelete\b.*\bfrom\b)",
                    r"(\bupdate\b.*\bset\b)",
                    r"(\bexec\b|\bexecute\b)",
                    r"(xp_cmdshell)",
                    r"(/\*.*\*/)",
                    r"(--.*$)",
                    r"(;.*--)",
                    r"(\bor\b.*=.*)",
                    r"('.*\bor\b.*'=')"
                ],
                "alert_type": AlertType.SQL_INJECTION,
                "threat_level": ThreatLevel.HIGH
            },
            
            # XSS patterns
            {
                "name": "xss_attempt",
                "patterns": [
                    r"(<script[^>]*>.*</script>)",
                    r"(javascript:)",
                    r"(on\w+\s*=)",
                    r"(<iframe[^>]*>)",
                    r"(<object[^>]*>)",
                    r"(<embed[^>]*>)",
                    r"(document\.cookie)",
                    r"(document\.write)",
                    r"(\.innerHTML\s*=)",
                    r"(eval\s*\()"
                ],
                "alert_type": AlertType.XSS_ATTEMPT,
                "threat_level": ThreatLevel.HIGH
            },
            
            # Path Traversal patterns
            {
                "name": "path_traversal",
                "patterns": [
                    r"(\.\./)",
                    r"(\.\.\\)",
                    r"(%2e%2e/)",
                    r"(%252e%252e/)",
                    r"(\.\.%2f)",
                    r"(/etc/passwd)",
                    r"(/etc/shadow)",
                    r"(c:\\windows)",
                    r"(c:\\winnt)"
                ],
                "alert_type": AlertType.PATH_TRAVERSAL,
                "threat_level": ThreatLevel.HIGH
            },
            
            # Command Injection patterns
            {
                "name": "command_injection",
                "patterns": [
                    r"(;.*\|)",
                    r"(\|.*\|)",
                    r"(`.*`)",
                    r"(\$\(.*\))",
                    r"(&&.*&&)",
                    r"(\|\|.*\|\|)",
                    r"(>\s*/dev/null)",
                    r"(curl\s+http)",
                    r"(wget\s+http)",
                    r"(nc\s+-e)"
                ],
                "alert_type": AlertType.XSS_ATTEMPT,
                "threat_level": ThreatLevel.CRITICAL
            }
        ]
    
    def load_threat_indicators(self):
        """Load known threat indicators"""
        
        # Known malicious IPs (example)
        self.threat_indicators["malicious_ips"] = [
            ThreatIndicator(
                indicator_type="ip",
                value="192.168.1.100",  # Example
                threat_level=ThreatLevel.HIGH,
                source="threat_feed",
                last_seen=datetime.utcnow()
            )
        ]
        
        # Known attack patterns
        self.threat_indicators["attack_patterns"] = [
            ThreatIndicator(
                indicator_type="pattern",
                value="masscan",
                threat_level=ThreatLevel.MEDIUM,
                source="signature",
                last_seen=datetime.utcnow()
            )
        ]
    
    async def detect_threats(self, event: SecurityEvent) -> List[Tuple[AlertType, ThreatLevel]]:
        """Detect threats in a security event"""
        
        detected_threats = []
        
        # Check against detection rules
        for rule in self.detection_rules:
            if self.check_patterns(event, rule["patterns"]):
                detected_threats.append((rule["alert_type"], rule["threat_level"]))
                event.threat_indicators.append(rule["name"])
        
        # Check against threat indicators
        if event.source_ip:
            for indicator in self.threat_indicators.get("malicious_ips", []):
                if indicator.value == event.source_ip:
                    detected_threats.append((
                        AlertType.UNAUTHORIZED_ACCESS,
                        indicator.threat_level
                    ))
                    indicator.hit_count += 1
        
        # Check for brute force
        if await self.is_brute_force(event):
            detected_threats.append((AlertType.BRUTE_FORCE, ThreatLevel.HIGH))
        
        # Check for data exfiltration
        if await self.is_data_exfiltration(event):
            detected_threats.append((AlertType.DATA_EXFILTRATION, ThreatLevel.CRITICAL))
        
        return detected_threats
    
    def check_patterns(self, event: SecurityEvent, patterns: List[str]) -> bool:
        """Check if event matches threat patterns"""
        
        # Check in various event fields
        check_fields = [
            event.action,
            event.target_resource,
            json.dumps(event.metadata)
        ]
        
        for field in check_fields:
            if field:
                for pattern in patterns:
                    if re.search(pattern, field, re.IGNORECASE):
                        return True
        
        return False
    
    async def is_brute_force(self, event: SecurityEvent) -> bool:
        """Check if event is part of brute force attack"""
        
        if event.result != "failure":
            return False
        
        # Check failed login attempts
        if "login" in event.action.lower() or "auth" in event.action.lower():
            if self.redis_client:
                key = f"failed_auth:{event.source_ip or event.user_id}"
                count = await self.redis_client.incr(key)
                
                if count == 1:
                    await self.redis_client.expire(key, 300)  # 5 minute window
                
                return count > 5  # More than 5 failures in 5 minutes
        
        return False
    
    async def is_data_exfiltration(self, event: SecurityEvent) -> bool:
        """Check for potential data exfiltration"""
        
        # Check for large data transfers
        if "export" in event.action.lower() or "download" in event.action.lower():
            data_size = event.metadata.get("data_size", 0)
            
            if data_size > 100_000_000:  # 100MB
                return True
            
            # Check frequency
            if self.redis_client and event.user_id:
                key = f"data_transfer:{event.user_id}"
                count = await self.redis_client.incr(key)
                
                if count == 1:
                    await self.redis_client.expire(key, 3600)  # 1 hour window
                
                return count > 10  # More than 10 exports in an hour
        
        return False
    
    async def update_threat_intelligence(self):
        """Update threat intelligence from external sources"""
        
        # This would connect to threat intelligence feeds
        # For now, just a placeholder
        pass


class AnomalyDetector:
    """
    Machine learning-based anomaly detection
    """
    
    def __init__(self):
        self.models = {}
        self.feature_extractors = {}
        self.baseline_metrics = {}
        self.anomaly_threshold = 0.1
        self.initialize_models()
    
    def initialize_models(self):
        """Initialize ML models for anomaly detection"""
        
        # User behavior model
        self.models["user_behavior"] = IsolationForest(
            contamination=self.anomaly_threshold,
            random_state=42
        )
        
        # API usage model
        self.models["api_usage"] = IsolationForest(
            contamination=self.anomaly_threshold,
            random_state=42
        )
        
        # Network traffic model
        self.models["network_traffic"] = IsolationForest(
            contamination=self.anomaly_threshold,
            random_state=42
        )
    
    def extract_user_features(self, events: List[SecurityEvent]) -> np.ndarray:
        """Extract features from user behavior"""
        
        features = []
        
        # Time-based features
        hours = [e.timestamp.hour for e in events]
        features.append(statistics.mean(hours) if hours else 0)
        features.append(statistics.stdev(hours) if len(hours) > 1 else 0)
        
        # Action diversity
        unique_actions = len(set(e.action for e in events))
        features.append(unique_actions)
        
        # Resource access patterns
        unique_resources = len(set(e.target_resource for e in events if e.target_resource))
        features.append(unique_resources)
        
        # Success/failure ratio
        failures = sum(1 for e in events if e.result == "failure")
        features.append(failures / len(events) if events else 0)
        
        # Request frequency
        if len(events) > 1:
            time_diffs = [
                (events[i].timestamp - events[i-1].timestamp).seconds
                for i in range(1, len(events))
            ]
            features.append(statistics.mean(time_diffs))
        else:
            features.append(0)
        
        return np.array(features).reshape(1, -1)
    
    def extract_api_features(self, api_calls: List[Dict[str, Any]]) -> np.ndarray:
        """Extract features from API usage"""
        
        features = []
        
        # Call frequency
        features.append(len(api_calls))
        
        # Endpoint diversity
        unique_endpoints = len(set(c.get("endpoint") for c in api_calls))
        features.append(unique_endpoints)
        
        # Response time statistics
        response_times = [c.get("response_time", 0) for c in api_calls]
        features.append(statistics.mean(response_times) if response_times else 0)
        features.append(statistics.stdev(response_times) if len(response_times) > 1 else 0)
        
        # Error rate
        errors = sum(1 for c in api_calls if c.get("status_code", 200) >= 400)
        features.append(errors / len(api_calls) if api_calls else 0)
        
        # Data volume
        data_sizes = [c.get("response_size", 0) for c in api_calls]
        features.append(sum(data_sizes))
        
        return np.array(features).reshape(1, -1)
    
    async def detect_anomalies(
        self,
        user_id: str,
        recent_events: List[SecurityEvent]
    ) -> Tuple[bool, float]:
        """
        Detect anomalous behavior
        Returns (is_anomaly, anomaly_score)
        """
        
        if len(recent_events) < 5:
            return False, 0.0
        
        # Extract features
        features = self.extract_user_features(recent_events)
        
        # Check if model is trained
        if hasattr(self.models["user_behavior"], "offset_"):
            # Predict anomaly
            prediction = self.models["user_behavior"].predict(features)
            score = self.models["user_behavior"].score_samples(features)[0]
            
            is_anomaly = prediction[0] == -1
            anomaly_score = abs(score)
            
            return is_anomaly, anomaly_score
        else:
            # Model not trained yet, collect baseline data
            return False, 0.0
    
    async def train_models(self, training_data: Dict[str, List[Any]]):
        """Train anomaly detection models"""
        
        # Train user behavior model
        if "user_events" in training_data:
            user_features = []
            
            for user_events in training_data["user_events"]:
                features = self.extract_user_features(user_events)
                user_features.append(features[0])
            
            if len(user_features) > 10:
                X = np.array(user_features)
                self.models["user_behavior"].fit(X)
        
        # Train API usage model
        if "api_calls" in training_data:
            api_features = []
            
            for api_session in training_data["api_calls"]:
                features = self.extract_api_features(api_session)
                api_features.append(features[0])
            
            if len(api_features) > 10:
                X = np.array(api_features)
                self.models["api_usage"].fit(X)
    
    def calculate_baseline(self, metrics: List[float]) -> Dict[str, float]:
        """Calculate baseline statistics for metrics"""
        
        if not metrics:
            return {}
        
        return {
            "mean": statistics.mean(metrics),
            "stdev": statistics.stdev(metrics) if len(metrics) > 1 else 0,
            "min": min(metrics),
            "max": max(metrics),
            "p50": statistics.median(metrics),
            "p95": np.percentile(metrics, 95) if len(metrics) > 1 else metrics[0],
            "p99": np.percentile(metrics, 99) if len(metrics) > 1 else metrics[0]
        }


class IncidentManager:
    """
    Security incident management system
    """
    
    def __init__(self):
        self.incidents = {}
        self.incident_queue = deque()
        self.response_playbooks = {}
        self.redis_client = None
        self.load_playbooks()
    
    async def initialize(self):
        """Initialize incident manager"""
        
        self.redis_client = await redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )
    
    def load_playbooks(self):
        """Load incident response playbooks"""
        
        self.response_playbooks = {
            AlertType.BRUTE_FORCE: [
                "Block source IP",
                "Lock affected accounts",
                "Notify security team",
                "Force password reset",
                "Enable MFA"
            ],
            AlertType.SQL_INJECTION: [
                "Block request",
                "Log attack details",
                "Patch vulnerable endpoint",
                "Review application logs",
                "Conduct security audit"
            ],
            AlertType.DATA_EXFILTRATION: [
                "Suspend user account",
                "Revoke access tokens",
                "Audit data access logs",
                "Notify compliance team",
                "Initiate forensic investigation"
            ],
            AlertType.DDOS_ATTACK: [
                "Enable rate limiting",
                "Activate DDoS protection",
                "Scale infrastructure",
                "Block malicious IPs",
                "Contact ISP"
            ],
            AlertType.PRIVILEGE_ESCALATION: [
                "Revoke elevated privileges",
                "Audit permission changes",
                "Review access logs",
                "Reset all passwords",
                "Conduct security review"
            ]
        }
    
    async def create_incident(
        self,
        alert_type: AlertType,
        threat_level: ThreatLevel,
        events: List[SecurityEvent],
        description: str
    ) -> SecurityIncident:
        """Create a new security incident"""
        
        incident = SecurityIncident(
            incident_id=f"INC-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}",
            created_at=datetime.utcnow(),
            alert_type=alert_type,
            threat_level=threat_level,
            status=IncidentStatus.OPEN,
            affected_users=list(set(e.user_id for e in events if e.user_id)),
            affected_resources=list(set(e.target_resource for e in events if e.target_resource)),
            events=events,
            description=description
        )
        
        # Store incident
        self.incidents[incident.incident_id] = incident
        
        if self.redis_client:
            await self.redis_client.setex(
                f"incident:{incident.incident_id}",
                86400 * 30,  # 30 days retention
                json.dumps({
                    "incident_id": incident.incident_id,
                    "alert_type": alert_type.value,
                    "threat_level": threat_level.value,
                    "status": incident.status.value,
                    "created_at": incident.created_at.isoformat(),
                    "description": description
                })
            )
        
        # Queue for response
        self.incident_queue.append(incident.incident_id)
        
        # Trigger automatic response for critical incidents
        if threat_level == ThreatLevel.CRITICAL:
            await self.trigger_automatic_response(incident)
        
        return incident
    
    async def trigger_automatic_response(self, incident: SecurityIncident):
        """Trigger automatic incident response"""
        
        playbook = self.response_playbooks.get(incident.alert_type, [])
        
        for action in playbook[:2]:  # Execute first two actions automatically
            incident.response_actions.append(f"AUTO: {action}")
            await self.execute_response_action(incident, action)
        
        incident.status = IncidentStatus.INVESTIGATING
    
    async def execute_response_action(
        self,
        incident: SecurityIncident,
        action: str
    ):
        """Execute a response action"""
        
        # Implementation would trigger actual response actions
        # For now, just log the action
        
        if "Block" in action and incident.events:
            # Block IPs
            for event in incident.events:
                if event.source_ip:
                    # Would actually block the IP
                    pass
        
        elif "Lock" in action:
            # Lock accounts
            for user_id in incident.affected_users:
                # Would actually lock the account
                pass
        
        elif "Notify" in action:
            # Send notifications
            await self.send_incident_notification(incident)
    
    async def send_incident_notification(self, incident: SecurityIncident):
        """Send incident notification"""
        
        # Would send actual notifications (email, Slack, PagerDuty, etc.)
        pass
    
    async def update_incident(
        self,
        incident_id: str,
        status: Optional[IncidentStatus] = None,
        response_actions: Optional[List[str]] = None,
        resolution_notes: Optional[str] = None
    ):
        """Update incident status"""
        
        if incident_id not in self.incidents:
            return
        
        incident = self.incidents[incident_id]
        
        if status:
            incident.status = status
            
            if status == IncidentStatus.RESOLVED:
                incident.resolved_at = datetime.utcnow()
        
        if response_actions:
            incident.response_actions.extend(response_actions)
        
        if resolution_notes:
            incident.resolution_notes = resolution_notes
        
        # Update in Redis
        if self.redis_client:
            await self.redis_client.setex(
                f"incident:{incident_id}",
                86400 * 30,
                json.dumps({
                    "incident_id": incident.incident_id,
                    "status": incident.status.value,
                    "resolved_at": incident.resolved_at.isoformat() if incident.resolved_at else None,
                    "response_actions": incident.response_actions,
                    "resolution_notes": incident.resolution_notes
                })
            )
    
    async def get_incident_statistics(self) -> Dict[str, Any]:
        """Get incident statistics"""
        
        total_incidents = len(self.incidents)
        open_incidents = sum(1 for i in self.incidents.values() if i.status == IncidentStatus.OPEN)
        resolved_incidents = sum(1 for i in self.incidents.values() if i.status == IncidentStatus.RESOLVED)
        
        # Calculate mean time to resolution
        resolution_times = []
        for incident in self.incidents.values():
            if incident.resolved_at:
                resolution_time = (incident.resolved_at - incident.created_at).total_seconds() / 3600
                resolution_times.append(resolution_time)
        
        mttr = statistics.mean(resolution_times) if resolution_times else 0
        
        # Alert type distribution
        alert_distribution = defaultdict(int)
        for incident in self.incidents.values():
            alert_distribution[incident.alert_type.value] += 1
        
        return {
            "total_incidents": total_incidents,
            "open_incidents": open_incidents,
            "resolved_incidents": resolved_incidents,
            "false_positives": sum(1 for i in self.incidents.values() if i.status == IncidentStatus.FALSE_POSITIVE),
            "mean_time_to_resolution_hours": round(mttr, 2),
            "alert_distribution": dict(alert_distribution),
            "critical_incidents": sum(1 for i in self.incidents.values() if i.threat_level == ThreatLevel.CRITICAL)
        }


class SecurityMonitor:
    """
    Central security monitoring system
    """
    
    def __init__(self):
        self.threat_detector = ThreatDetector()
        self.anomaly_detector = AnomalyDetector()
        self.incident_manager = IncidentManager()
        self.event_buffer = deque(maxlen=10000)
        self.metrics = defaultdict(list)
    
    async def initialize(self):
        """Initialize security monitor"""
        
        await self.threat_detector.initialize()
        await self.incident_manager.initialize()
    
    async def process_event(self, event: SecurityEvent):
        """Process a security event"""
        
        # Add to buffer
        self.event_buffer.append(event)
        
        # Detect threats
        threats = await self.threat_detector.detect_threats(event)
        
        # Check for anomalies
        if event.user_id:
            user_events = [e for e in self.event_buffer if e.user_id == event.user_id]
            is_anomaly, anomaly_score = await self.anomaly_detector.detect_anomalies(
                event.user_id,
                user_events[-100:]  # Last 100 events
            )
            
            if is_anomaly:
                threats.append((AlertType.ANOMALOUS_BEHAVIOR, ThreatLevel.MEDIUM))
        
        # Create incident if threats detected
        if threats:
            # Get highest threat level
            max_threat = max(threats, key=lambda x: self.get_threat_priority(x[1]))
            
            await self.incident_manager.create_incident(
                alert_type=max_threat[0],
                threat_level=max_threat[1],
                events=[event],
                description=f"Security threat detected: {max_threat[0].value}"
            )
        
        # Update metrics
        self.update_metrics(event, threats)
    
    def get_threat_priority(self, threat_level: ThreatLevel) -> int:
        """Get numeric priority for threat level"""
        
        priorities = {
            ThreatLevel.LOW: 1,
            ThreatLevel.MEDIUM: 2,
            ThreatLevel.HIGH: 3,
            ThreatLevel.CRITICAL: 4
        }
        
        return priorities.get(threat_level, 0)
    
    def update_metrics(self, event: SecurityEvent, threats: List[Tuple[AlertType, ThreatLevel]]):
        """Update security metrics"""
        
        # Event metrics
        self.metrics["events_processed"].append(datetime.utcnow())
        
        if threats:
            self.metrics["threats_detected"].append(datetime.utcnow())
            
            for alert_type, threat_level in threats:
                self.metrics[f"threat_{alert_type.value}"].append(datetime.utcnow())
                self.metrics[f"level_{threat_level.value}"].append(datetime.utcnow())
    
    async def get_security_dashboard(self) -> Dict[str, Any]:
        """Get security dashboard data"""
        
        now = datetime.utcnow()
        hour_ago = now - timedelta(hours=1)
        day_ago = now - timedelta(days=1)
        
        # Calculate rates
        events_last_hour = sum(1 for t in self.metrics["events_processed"] if t > hour_ago)
        threats_last_hour = sum(1 for t in self.metrics["threats_detected"] if t > hour_ago)
        
        events_last_day = sum(1 for t in self.metrics["events_processed"] if t > day_ago)
        threats_last_day = sum(1 for t in self.metrics["threats_detected"] if t > day_ago)
        
        # Get incident stats
        incident_stats = await self.incident_manager.get_incident_statistics()
        
        return {
            "timestamp": now.isoformat(),
            "events": {
                "last_hour": events_last_hour,
                "last_24h": events_last_day,
                "total": len(self.event_buffer)
            },
            "threats": {
                "last_hour": threats_last_hour,
                "last_24h": threats_last_day,
                "detection_rate": (threats_last_hour / events_last_hour * 100) if events_last_hour > 0 else 0
            },
            "incidents": incident_stats,
            "top_threats": self.get_top_threats(),
            "system_health": self.get_system_health()
        }
    
    def get_top_threats(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get top detected threats"""
        
        threat_counts = defaultdict(int)
        
        for key in self.metrics:
            if key.startswith("threat_"):
                threat_type = key.replace("threat_", "")
                threat_counts[threat_type] = len(self.metrics[key])
        
        sorted_threats = sorted(threat_counts.items(), key=lambda x: x[1], reverse=True)
        
        return [
            {"type": threat_type, "count": count}
            for threat_type, count in sorted_threats[:limit]
        ]
    
    def get_system_health(self) -> str:
        """Get overall system health status"""
        
        # Simple health calculation based on threat rate
        recent_threats = sum(
            1 for t in self.metrics["threats_detected"]
            if t > datetime.utcnow() - timedelta(minutes=10)
        )
        
        if recent_threats > 50:
            return "CRITICAL"
        elif recent_threats > 20:
            return "WARNING"
        elif recent_threats > 5:
            return "ELEVATED"
        else:
            return "NORMAL"