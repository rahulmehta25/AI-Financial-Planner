"""
Security and Compliance Framework

Comprehensive security modules for financial services compliance including:
- FINRA/SEC compliance monitoring
- SOC 2 audit trail requirements
- GDPR data handling procedures
- Field-level encryption for PII
- Rate limiting and DDoS protection
- Security event monitoring
- Automated vulnerability scanning
"""

from .authentication import (
    AuthenticationManager,
    JWTHandler,
    OAuth2Handler,
    SAMLHandler,
    MFAHandler
)
from .authorization import (
    AuthorizationManager,
    RBACPolicy,
    ABACPolicy,
    PermissionChecker
)
from .encryption import (
    EncryptionManager,
    FieldEncryption,
    DataClassifier,
    KeyManagement
)
from .compliance import (
    ComplianceEngine,
    FINRACompliance,
    SECCompliance,
    GDPRCompliance,
    SOC2Compliance
)
from .audit import (
    AuditLogger,
    ComplianceReporter,
    AuditTrail,
    EventRecorder
)
from .rate_limiting import (
    RateLimiter,
    DDoSProtection,
    APIThrottler,
    BruteForceProtection
)
from .monitoring import (
    SecurityMonitor,
    ThreatDetector,
    AnomalyDetector,
    IncidentManager
)
from .vulnerability import (
    VulnerabilityScanner,
    DependencyChecker,
    SecurityPatcher,
    CVEMonitor
)
from .data_protection import (
    PIIProtector,
    DataMasking,
    Tokenization,
    SecureStorage
)
from .headers import (
    SecurityHeadersMiddleware,
    CSPPolicy,
    HSTSPolicy,
    SecurityHeaders
)

__all__ = [
    # Authentication
    'AuthenticationManager',
    'JWTHandler',
    'OAuth2Handler',
    'SAMLHandler',
    'MFAHandler',
    
    # Authorization
    'AuthorizationManager',
    'RBACPolicy',
    'ABACPolicy',
    'PermissionChecker',
    
    # Encryption
    'EncryptionManager',
    'FieldEncryption',
    'DataClassifier',
    'KeyManagement',
    
    # Compliance
    'ComplianceEngine',
    'FINRACompliance',
    'SECCompliance',
    'GDPRCompliance',
    'SOC2Compliance',
    
    # Audit
    'AuditLogger',
    'ComplianceReporter',
    'AuditTrail',
    'EventRecorder',
    
    # Rate Limiting
    'RateLimiter',
    'DDoSProtection',
    'APIThrottler',
    'BruteForceProtection',
    
    # Monitoring
    'SecurityMonitor',
    'ThreatDetector',
    'AnomalyDetector',
    'IncidentManager',
    
    # Vulnerability
    'VulnerabilityScanner',
    'DependencyChecker',
    'SecurityPatcher',
    'CVEMonitor',
    
    # Data Protection
    'PIIProtector',
    'DataMasking',
    'Tokenization',
    'SecureStorage',
    
    # Headers
    'SecurityHeadersMiddleware',
    'CSPPolicy',
    'HSTSPolicy',
    'SecurityHeaders'
]