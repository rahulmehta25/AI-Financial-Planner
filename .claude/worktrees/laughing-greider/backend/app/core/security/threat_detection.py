"""
Threat Detection & Security Monitoring Module

Implements:
- Intrusion Detection System (IDS)
- Anomaly Detection using ML
- Real-time threat monitoring
- SIEM integration
- Security incident response
"""

import asyncio
import json
import hashlib
from typing import Dict, Any, Optional, List, Set, Tuple
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, asdict
import numpy as np
from collections import defaultdict, deque
import redis.asyncio as redis
import re
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import pickle

from app.core.config import settings
from app.core.security.audit import AuditLogger, AuditEventType, AuditSeverity


class ThreatLevel(Enum):
    """Threat severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ThreatType(Enum):
    """Types of security threats"""
    BRUTE_FORCE = "brute_force"
    SQL_INJECTION = "sql_injection"
    XSS_ATTACK = "xss_attack"
    CSRF_ATTACK = "csrf_attack"
    DDoS_ATTACK = "ddos_attack"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    DATA_EXFILTRATION = "data_exfiltration"
    MALWARE = "malware"
    INSIDER_THREAT = "insider_threat"
    ANOMALOUS_BEHAVIOR = "anomalous_behavior"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    SUSPICIOUS_PATTERN = "suspicious_pattern"


@dataclass
class SecurityEvent:
    """Security event for analysis"""
    timestamp: datetime
    event_type: str
    source_ip: str
    user_id: Optional[str]
    endpoint: str
    method: str
    status_code: int
    response_time: float
    payload_size: int
    user_agent: str
    headers: Dict[str, str]
    parameters: Dict[str, Any]
    response_size: int
    session_id: Optional[str]


@dataclass
class ThreatIndicator:
    """Indicator of a potential threat"""
    indicator_id: str
    threat_type: ThreatType
    threat_level: ThreatLevel
    confidence: float
    timestamp: datetime
    source_ip: str
    user_id: Optional[str]
    description: str
    evidence: Dict[str, Any]
    recommended_action: str


class PatternDetector:
    """Detect malicious patterns in requests"""
    
    # SQL Injection patterns
    SQL_INJECTION_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|CREATE|ALTER)\b)",
        r"(--|\#|\/\*|\*\/)",
        r"(\bOR\b\s*\d+\s*=\s*\d+)",
        r"(\bAND\b\s*\d+\s*=\s*\d+)",
        r"(;.*;)",
        r"(\'\s*OR\s*\')",
        r"(EXEC(\s|\+)+(SP_|XP_))",
        r"(WAITFOR\s+DELAY)",
    ]
    
    # XSS patterns
    XSS_PATTERNS = [
        r"(<script[^>]*>.*?</script>)",
        r"(javascript:)",
        r"(on\w+\s*=)",
        r"(<iframe[^>]*>.*?</iframe>)",
        r"(<img[^>]*onerror\s*=)",
        r"(<svg[^>]*onload\s*=)",
        r"(eval\s*\()",
        r"(alert\s*\()",
    ]
    
    # Path traversal patterns
    PATH_TRAVERSAL_PATTERNS = [
        r"(\.\.\/|\.\.\\)",
        r"(%2e%2e%2f|%2e%2e/)",
        r"(\/etc\/passwd)",
        r"(C:\\\\Windows\\\\)",
    ]
    
    # Command injection patterns
    COMMAND_INJECTION_PATTERNS = [
        r"(;.*\s*(ls|cat|wget|curl|nc|bash|sh)\s)",
        r"(\|.*\s*(ls|cat|wget|curl|nc|bash|sh)\s)",
        r"(`.*`)",
        r"(\$\(.*\))",
    ]
    
    @classmethod
    def detect_sql_injection(cls, text: str) -> bool:
        """Detect SQL injection attempts"""
        text_lower = text.lower()
        for pattern in cls.SQL_INJECTION_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return True
        return False
    
    @classmethod
    def detect_xss(cls, text: str) -> bool:
        """Detect XSS attempts"""
        for pattern in cls.XSS_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False
    
    @classmethod
    def detect_path_traversal(cls, text: str) -> bool:
        """Detect path traversal attempts"""
        for pattern in cls.PATH_TRAVERSAL_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False
    
    @classmethod
    def detect_command_injection(cls, text: str) -> bool:
        """Detect command injection attempts"""
        for pattern in cls.COMMAND_INJECTION_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False
    
    @classmethod
    def analyze_request(cls, event: SecurityEvent) -> List[ThreatType]:
        """Analyze request for threats"""
        threats = []
        
        # Check all parameters and headers
        all_text = json.dumps(event.parameters) + json.dumps(event.headers)
        
        if cls.detect_sql_injection(all_text):
            threats.append(ThreatType.SQL_INJECTION)
        
        if cls.detect_xss(all_text):
            threats.append(ThreatType.XSS_ATTACK)
        
        if cls.detect_path_traversal(event.endpoint):
            threats.append(ThreatType.UNAUTHORIZED_ACCESS)
        
        if cls.detect_command_injection(all_text):
            threats.append(ThreatType.SUSPICIOUS_PATTERN)
        
        return threats


class BehaviorAnalyzer:
    """Analyze user and system behavior for anomalies"""
    
    def __init__(self):
        self.user_profiles: Dict[str, Dict[str, Any]] = {}
        self.ip_profiles: Dict[str, Dict[str, Any]] = {}
        self.failed_login_attempts: Dict[str, List[datetime]] = defaultdict(list)
        self.request_rates: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        
        # Machine learning model for anomaly detection
        self.anomaly_model = IsolationForest(
            contamination=0.1,
            random_state=42
        )
        self.scaler = StandardScaler()
        self.model_trained = False
    
    def update_user_profile(self, user_id: str, event: SecurityEvent):
        """Update user behavior profile"""
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = {
                "typical_hours": set(),
                "typical_ips": set(),
                "typical_endpoints": set(),
                "typical_user_agents": set(),
                "avg_response_time": 0,
                "request_count": 0,
                "last_seen": None
            }
        
        profile = self.user_profiles[user_id]
        
        # Update profile
        profile["typical_hours"].add(event.timestamp.hour)
        profile["typical_ips"].add(event.source_ip)
        profile["typical_endpoints"].add(event.endpoint)
        profile["typical_user_agents"].add(event.user_agent)
        
        # Update average response time
        count = profile["request_count"]
        profile["avg_response_time"] = (
            (profile["avg_response_time"] * count + event.response_time) / 
            (count + 1)
        )
        profile["request_count"] = count + 1
        profile["last_seen"] = event.timestamp
    
    def detect_brute_force(self, source_ip: str, user_id: Optional[str]) -> bool:
        """Detect brute force attacks"""
        key = f"{source_ip}:{user_id}" if user_id else source_ip
        
        # Clean old attempts
        cutoff_time = datetime.utcnow() - timedelta(minutes=10)
        self.failed_login_attempts[key] = [
            attempt for attempt in self.failed_login_attempts[key]
            if attempt > cutoff_time
        ]
        
        # Check threshold
        if len(self.failed_login_attempts[key]) >= 5:
            return True
        
        return False
    
    def detect_rate_anomaly(self, source_ip: str) -> bool:
        """Detect abnormal request rates"""
        now = datetime.utcnow()
        self.request_rates[source_ip].append(now)
        
        # Count requests in last minute
        one_minute_ago = now - timedelta(minutes=1)
        recent_requests = sum(
            1 for req_time in self.request_rates[source_ip]
            if req_time > one_minute_ago
        )
        
        # Threshold: 100 requests per minute
        return recent_requests > 100
    
    def detect_user_anomaly(self, user_id: str, event: SecurityEvent) -> List[str]:
        """Detect anomalies in user behavior"""
        anomalies = []
        
        if user_id not in self.user_profiles:
            return []
        
        profile = self.user_profiles[user_id]
        
        # Check for unusual access time
        if event.timestamp.hour not in profile["typical_hours"]:
            if len(profile["typical_hours"]) > 10:  # Enough data
                anomalies.append("unusual_access_time")
        
        # Check for unusual IP
        if event.source_ip not in profile["typical_ips"]:
            if len(profile["typical_ips"]) > 5:  # Enough data
                anomalies.append("unusual_ip_address")
        
        # Check for unusual user agent
        if event.user_agent not in profile["typical_user_agents"]:
            if len(profile["typical_user_agents"]) > 3:
                anomalies.append("unusual_user_agent")
        
        # Check response time anomaly
        if profile["avg_response_time"] > 0:
            if event.response_time > profile["avg_response_time"] * 10:
                anomalies.append("abnormal_response_time")
        
        # Check for impossible travel
        if profile["last_seen"]:
            time_diff = (event.timestamp - profile["last_seen"]).total_seconds()
            if time_diff < 60:  # Less than 1 minute
                if event.source_ip not in profile["typical_ips"]:
                    anomalies.append("impossible_travel")
        
        return anomalies
    
    def train_anomaly_model(self, events: List[SecurityEvent]):
        """Train ML model for anomaly detection"""
        if len(events) < 100:
            return
        
        # Extract features
        features = []
        for event in events:
            feature_vector = self._extract_features(event)
            features.append(feature_vector)
        
        # Scale features
        features_scaled = self.scaler.fit_transform(features)
        
        # Train model
        self.anomaly_model.fit(features_scaled)
        self.model_trained = True
    
    def predict_anomaly(self, event: SecurityEvent) -> Tuple[bool, float]:
        """Predict if event is anomalous using ML"""
        if not self.model_trained:
            return False, 0.0
        
        # Extract features
        features = self._extract_features(event)
        features_scaled = self.scaler.transform([features])
        
        # Predict
        prediction = self.anomaly_model.predict(features_scaled)[0]
        score = self.anomaly_model.score_samples(features_scaled)[0]
        
        # -1 means anomaly in IsolationForest
        is_anomaly = prediction == -1
        confidence = abs(score)
        
        return is_anomaly, confidence
    
    def _extract_features(self, event: SecurityEvent) -> List[float]:
        """Extract numerical features from event"""
        return [
            event.timestamp.hour,
            event.timestamp.minute,
            event.timestamp.weekday(),
            event.status_code,
            event.response_time,
            event.payload_size,
            event.response_size,
            len(event.parameters),
            len(event.headers),
            1 if "bot" in event.user_agent.lower() else 0,
            1 if event.method == "POST" else 0,
            1 if event.method == "PUT" else 0,
            1 if event.method == "DELETE" else 0,
        ]


class ThreatIntelligence:
    """Threat intelligence feed integration"""
    
    def __init__(self):
        self.known_malicious_ips: Set[str] = set()
        self.known_malicious_domains: Set[str] = set()
        self.known_malicious_hashes: Set[str] = set()
        self.threat_indicators: Dict[str, ThreatIndicator] = {}
        
    async def update_threat_feeds(self):
        """Update threat intelligence feeds"""
        # TODO: Integrate with real threat intelligence APIs
        # - AlienVault OTX
        # - Abuse.ch
        # - Emerging Threats
        # - Commercial feeds
        
        # Mock threat data
        self.known_malicious_ips = {
            "192.168.1.100",
            "10.0.0.50",
        }
        
        self.known_malicious_domains = {
            "malicious.example.com",
            "phishing.site.com",
        }
    
    def check_ip_reputation(self, ip: str) -> Optional[ThreatLevel]:
        """Check IP reputation"""
        if ip in self.known_malicious_ips:
            return ThreatLevel.HIGH
        
        # Check IP patterns
        if ip.startswith("10.") or ip.startswith("192.168."):
            return None  # Internal IP
        
        # TODO: Check against threat feeds
        return None
    
    def check_domain_reputation(self, domain: str) -> Optional[ThreatLevel]:
        """Check domain reputation"""
        if domain in self.known_malicious_domains:
            return ThreatLevel.HIGH
        
        # Check for suspicious TLDs
        suspicious_tlds = [".tk", ".ml", ".ga", ".cf"]
        if any(domain.endswith(tld) for tld in suspicious_tlds):
            return ThreatLevel.MEDIUM
        
        return None
    
    def check_file_hash(self, file_hash: str) -> Optional[ThreatLevel]:
        """Check file hash against known malware"""
        if file_hash in self.known_malicious_hashes:
            return ThreatLevel.CRITICAL
        return None


class IncidentResponse:
    """Automated incident response"""
    
    def __init__(self):
        self.active_incidents: Dict[str, Dict[str, Any]] = {}
        self.blocked_ips: Set[str] = set()
        self.blocked_users: Set[str] = set()
        
    async def respond_to_threat(
        self,
        indicator: ThreatIndicator
    ) -> Dict[str, Any]:
        """Automated response to detected threat"""
        
        response = {
            "incident_id": indicator.indicator_id,
            "actions_taken": [],
            "notifications_sent": [],
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Determine response based on threat level and type
        if indicator.threat_level == ThreatLevel.CRITICAL:
            # Immediate blocking
            if indicator.source_ip:
                await self.block_ip(indicator.source_ip)
                response["actions_taken"].append(f"Blocked IP: {indicator.source_ip}")
            
            if indicator.user_id:
                await self.suspend_user(indicator.user_id)
                response["actions_taken"].append(f"Suspended user: {indicator.user_id}")
            
            # Alert security team
            await self.send_critical_alert(indicator)
            response["notifications_sent"].append("Critical alert sent to security team")
            
        elif indicator.threat_level == ThreatLevel.HIGH:
            # Rate limiting
            if indicator.source_ip:
                await self.rate_limit_ip(indicator.source_ip)
                response["actions_taken"].append(f"Rate limited IP: {indicator.source_ip}")
            
            # Increase monitoring
            await self.increase_monitoring(indicator)
            response["actions_taken"].append("Increased monitoring")
            
        elif indicator.threat_level == ThreatLevel.MEDIUM:
            # Log and monitor
            await self.log_threat(indicator)
            response["actions_taken"].append("Logged threat for analysis")
        
        # Store incident
        self.active_incidents[indicator.indicator_id] = response
        
        return response
    
    async def block_ip(self, ip: str):
        """Block IP address"""
        self.blocked_ips.add(ip)
        # TODO: Update firewall rules
        # TODO: Update WAF rules
    
    async def suspend_user(self, user_id: str):
        """Suspend user account"""
        self.blocked_users.add(user_id)
        # TODO: Invalidate user sessions
        # TODO: Disable user account
    
    async def rate_limit_ip(self, ip: str):
        """Apply rate limiting to IP"""
        # TODO: Update rate limiting rules
        pass
    
    async def increase_monitoring(self, indicator: ThreatIndicator):
        """Increase monitoring for specific threat"""
        # TODO: Adjust monitoring thresholds
        # TODO: Enable detailed logging
        pass
    
    async def send_critical_alert(self, indicator: ThreatIndicator):
        """Send critical security alert"""
        # TODO: Send to SIEM
        # TODO: Send email/SMS to security team
        # TODO: Create PagerDuty incident
        pass
    
    async def log_threat(self, indicator: ThreatIndicator):
        """Log threat for analysis"""
        # TODO: Log to SIEM
        # TODO: Store for threat hunting
        pass


class SecurityMonitor:
    """Main security monitoring and threat detection system"""
    
    def __init__(self):
        self.pattern_detector = PatternDetector()
        self.behavior_analyzer = BehaviorAnalyzer()
        self.threat_intelligence = ThreatIntelligence()
        self.incident_response = IncidentResponse()
        self.audit_logger = AuditLogger()
        self.redis_client = None
        
    async def initialize(self):
        """Initialize security monitor"""
        self.redis_client = await redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )
        await self.audit_logger.initialize()
        await self.threat_intelligence.update_threat_feeds()
    
    async def analyze_event(self, event: SecurityEvent) -> List[ThreatIndicator]:
        """Analyze security event for threats"""
        indicators = []
        
        # Pattern-based detection
        pattern_threats = self.pattern_detector.analyze_request(event)
        for threat_type in pattern_threats:
            indicator = ThreatIndicator(
                indicator_id=f"pattern_{event.timestamp.timestamp()}",
                threat_type=threat_type,
                threat_level=ThreatLevel.HIGH,
                confidence=0.9,
                timestamp=event.timestamp,
                source_ip=event.source_ip,
                user_id=event.user_id,
                description=f"Detected {threat_type.value} pattern",
                evidence={"endpoint": event.endpoint, "method": event.method},
                recommended_action="Block request and investigate"
            )
            indicators.append(indicator)
        
        # Behavior-based detection
        if event.user_id:
            anomalies = self.behavior_analyzer.detect_user_anomaly(event.user_id, event)
            if anomalies:
                indicator = ThreatIndicator(
                    indicator_id=f"behavior_{event.timestamp.timestamp()}",
                    threat_type=ThreatType.ANOMALOUS_BEHAVIOR,
                    threat_level=ThreatLevel.MEDIUM,
                    confidence=0.7,
                    timestamp=event.timestamp,
                    source_ip=event.source_ip,
                    user_id=event.user_id,
                    description=f"Anomalous behavior detected: {', '.join(anomalies)}",
                    evidence={"anomalies": anomalies},
                    recommended_action="Monitor closely"
                )
                indicators.append(indicator)
        
        # ML-based anomaly detection
        is_anomaly, confidence = self.behavior_analyzer.predict_anomaly(event)
        if is_anomaly:
            indicator = ThreatIndicator(
                indicator_id=f"ml_{event.timestamp.timestamp()}",
                threat_type=ThreatType.ANOMALOUS_BEHAVIOR,
                threat_level=ThreatLevel.MEDIUM if confidence < 0.8 else ThreatLevel.HIGH,
                confidence=confidence,
                timestamp=event.timestamp,
                source_ip=event.source_ip,
                user_id=event.user_id,
                description="ML model detected anomaly",
                evidence={"ml_score": confidence},
                recommended_action="Review and investigate"
            )
            indicators.append(indicator)
        
        # Rate limiting check
        if self.behavior_analyzer.detect_rate_anomaly(event.source_ip):
            indicator = ThreatIndicator(
                indicator_id=f"rate_{event.timestamp.timestamp()}",
                threat_type=ThreatType.DDoS_ATTACK,
                threat_level=ThreatLevel.HIGH,
                confidence=0.8,
                timestamp=event.timestamp,
                source_ip=event.source_ip,
                user_id=event.user_id,
                description="Abnormal request rate detected",
                evidence={"endpoint": event.endpoint},
                recommended_action="Apply rate limiting"
            )
            indicators.append(indicator)
        
        # Threat intelligence check
        ip_threat = self.threat_intelligence.check_ip_reputation(event.source_ip)
        if ip_threat:
            indicator = ThreatIndicator(
                indicator_id=f"threat_intel_{event.timestamp.timestamp()}",
                threat_type=ThreatType.SUSPICIOUS_PATTERN,
                threat_level=ip_threat,
                confidence=0.95,
                timestamp=event.timestamp,
                source_ip=event.source_ip,
                user_id=event.user_id,
                description="Known malicious IP",
                evidence={"source": "threat_intelligence"},
                recommended_action="Block immediately"
            )
            indicators.append(indicator)
        
        # Process indicators
        for indicator in indicators:
            await self.process_threat_indicator(indicator)
        
        return indicators
    
    async def process_threat_indicator(self, indicator: ThreatIndicator):
        """Process detected threat indicator"""
        
        # Log to audit trail
        await self.audit_logger.log(
            event_type=AuditEventType.SECURITY_ALERT,
            action="threat_detected",
            result=indicator.threat_type.value,
            user_id=indicator.user_id,
            details=asdict(indicator),
            severity=self._map_threat_to_audit_severity(indicator.threat_level)
        )
        
        # Automated response
        if indicator.threat_level in [ThreatLevel.HIGH, ThreatLevel.CRITICAL]:
            await self.incident_response.respond_to_threat(indicator)
        
        # Store in Redis for real-time dashboard
        await self.redis_client.setex(
            f"threat:{indicator.indicator_id}",
            3600,  # 1 hour TTL
            json.dumps(asdict(indicator), default=str)
        )
        
        # Update threat statistics
        await self.redis_client.hincrby(
            "threat_stats",
            indicator.threat_type.value,
            1
        )
    
    def _map_threat_to_audit_severity(self, threat_level: ThreatLevel) -> AuditSeverity:
        """Map threat level to audit severity"""
        mapping = {
            ThreatLevel.LOW: AuditSeverity.INFO,
            ThreatLevel.MEDIUM: AuditSeverity.WARNING,
            ThreatLevel.HIGH: AuditSeverity.ERROR,
            ThreatLevel.CRITICAL: AuditSeverity.CRITICAL
        }
        return mapping.get(threat_level, AuditSeverity.WARNING)
    
    async def get_security_status(self) -> Dict[str, Any]:
        """Get current security status"""
        
        # Get threat statistics
        threat_stats = await self.redis_client.hgetall("threat_stats")
        
        # Get active incidents
        active_incidents = len(self.incident_response.active_incidents)
        
        # Get blocked entities
        blocked_ips = len(self.incident_response.blocked_ips)
        blocked_users = len(self.incident_response.blocked_users)
        
        return {
            "status": "operational",
            "threat_level": self._calculate_overall_threat_level(threat_stats),
            "statistics": {
                "threats_detected": threat_stats,
                "active_incidents": active_incidents,
                "blocked_ips": blocked_ips,
                "blocked_users": blocked_users
            },
            "last_update": datetime.utcnow().isoformat()
        }
    
    def _calculate_overall_threat_level(self, threat_stats: Dict[str, str]) -> str:
        """Calculate overall threat level"""
        if not threat_stats:
            return "low"
        
        total_threats = sum(int(v) for v in threat_stats.values())
        
        if total_threats > 100:
            return "critical"
        elif total_threats > 50:
            return "high"
        elif total_threats > 10:
            return "medium"
        else:
            return "low"


# Global security monitor instance
security_monitor = SecurityMonitor()