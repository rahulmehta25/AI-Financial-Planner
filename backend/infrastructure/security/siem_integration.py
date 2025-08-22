"""
SIEM Integration and Security Monitoring

Comprehensive security monitoring, threat detection, and automated response.
"""

import json
import hashlib
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from enum import Enum
import re


class ThreatLevel(Enum):
    """Threat severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class SIEMConnector:
    """SIEM platform connectors"""
    
    @staticmethod
    def get_splunk_config() -> Dict[str, Any]:
        """Splunk SIEM configuration"""
        return {
            "connection": {
                "host": "splunk.financialplanner.com",
                "port": 8089,
                "scheme": "https",
                "verify_ssl": True,
                "timeout": 30
            },
            "indexes": {
                "security": "security_events",
                "application": "app_logs",
                "audit": "audit_trail",
                "performance": "perf_metrics",
                "threat_intel": "threat_intelligence"
            },
            "saved_searches": [
                {
                    "name": "Failed Login Attempts",
                    "search": 'index=security_events event_type="authentication" status="failed" | stats count by src_ip user | where count > 5',
                    "schedule": "*/5 * * * *",
                    "alert_threshold": 5
                },
                {
                    "name": "SQL Injection Attempts",
                    "search": 'index=app_logs (SELECT OR INSERT OR UPDATE OR DELETE OR DROP) AND (FROM OR INTO OR TABLE)',
                    "schedule": "*/1 * * * *",
                    "alert_threshold": 1
                },
                {
                    "name": "Privilege Escalation",
                    "search": 'index=security_events event_type="privilege_change" | where new_role="admin"',
                    "schedule": "*/10 * * * *",
                    "alert_threshold": 1
                },
                {
                    "name": "Data Exfiltration",
                    "search": 'index=app_logs bytes_out > 100000000 | stats sum(bytes_out) as total_bytes by user | where total_bytes > 1000000000',
                    "schedule": "*/15 * * * *",
                    "alert_threshold": 1
                },
                {
                    "name": "Suspicious API Activity",
                    "search": 'index=app_logs api_endpoint="/api/*" | stats count by src_ip api_endpoint | where count > 1000',
                    "schedule": "*/5 * * * *",
                    "alert_threshold": 1000
                }
            ],
            "dashboards": [
                {
                    "name": "Security Overview",
                    "panels": [
                        "Authentication Events",
                        "Threat Detection",
                        "Vulnerability Scans",
                        "Incident Response"
                    ]
                },
                {
                    "name": "Compliance Monitoring",
                    "panels": [
                        "PCI DSS Compliance",
                        "GDPR Activities",
                        "Audit Trail",
                        "Data Access"
                    ]
                }
            ],
            "forwarder_config": {
                "type": "universal",
                "deployment_server": "splunk-deploy.financialplanner.com",
                "inputs": [
                    "/var/log/nginx/access.log",
                    "/var/log/nginx/error.log",
                    "/var/log/application/*.log",
                    "/var/log/audit/audit.log"
                ]
            }
        }
    
    @staticmethod
    def get_elastic_siem_config() -> Dict[str, Any]:
        """Elastic SIEM (ELK Stack) configuration"""
        return {
            "elasticsearch": {
                "hosts": ["https://elastic.financialplanner.com:9200"],
                "username": "elastic_siem",
                "api_key": "{{ELASTIC_API_KEY}}",
                "ssl_verify": True,
                "indices": {
                    "pattern": "security-*",
                    "lifecycle_policy": "security_ilm_policy"
                }
            },
            "kibana": {
                "host": "https://kibana.financialplanner.com:5601",
                "space": "security",
                "dashboards": [
                    "Security Overview",
                    "Threat Hunting",
                    "Incident Timeline",
                    "Compliance Tracking"
                ]
            },
            "detection_rules": [
                {
                    "name": "Brute Force Attack Detection",
                    "index": ["security-*"],
                    "query": {
                        "bool": {
                            "must": [
                                {"term": {"event.category": "authentication"}},
                                {"term": {"event.outcome": "failure"}}
                            ]
                        }
                    },
                    "threshold": {
                        "field": "source.ip",
                        "value": 5,
                        "timeframe": "5m"
                    },
                    "severity": "high"
                },
                {
                    "name": "Unusual Process Execution",
                    "index": ["endpoint-*"],
                    "query": {
                        "bool": {
                            "must": [
                                {"term": {"event.category": "process"}},
                                {"terms": {"process.name": ["powershell.exe", "cmd.exe", "wscript.exe"]}}
                            ]
                        }
                    },
                    "severity": "medium"
                },
                {
                    "name": "Lateral Movement Detection",
                    "index": ["network-*"],
                    "query": {
                        "bool": {
                            "must": [
                                {"range": {"network.packets": {"gte": 10000}}},
                                {"term": {"network.direction": "internal"}}
                            ]
                        }
                    },
                    "severity": "high"
                }
            ],
            "machine_learning_jobs": [
                {
                    "job_id": "suspicious_login_activity",
                    "description": "Detect unusual login patterns",
                    "analysis_config": {
                        "bucket_span": "15m",
                        "detectors": [
                            {
                                "function": "rare",
                                "by_field_name": "user.name",
                                "over_field_name": "source.geo.country_name"
                            }
                        ]
                    }
                },
                {
                    "job_id": "network_anomaly_detection",
                    "description": "Detect network traffic anomalies",
                    "analysis_config": {
                        "bucket_span": "5m",
                        "detectors": [
                            {
                                "function": "high_mean",
                                "field_name": "network.bytes",
                                "partition_field_name": "source.ip"
                            }
                        ]
                    }
                }
            ]
        }
    
    @staticmethod
    def get_sentinel_config() -> Dict[str, Any]:
        """Microsoft Sentinel configuration"""
        return {
            "workspace": {
                "workspace_id": "{{WORKSPACE_ID}}",
                "resource_group": "financial-planner-security",
                "subscription_id": "{{SUBSCRIPTION_ID}}"
            },
            "data_connectors": [
                {
                    "type": "AzureActiveDirectory",
                    "enabled": True,
                    "data_types": ["SignInLogs", "AuditLogs"]
                },
                {
                    "type": "AzureKeyVault",
                    "enabled": True,
                    "data_types": ["KeyVaultEvents"]
                },
                {
                    "type": "ThreatIntelligence",
                    "enabled": True,
                    "sources": ["MISP", "AlienVault", "ThreatConnect"]
                },
                {
                    "type": "Office365",
                    "enabled": True,
                    "data_types": ["Exchange", "SharePoint", "Teams"]
                }
            ],
            "analytics_rules": [
                {
                    "name": "Multiple Failed Login Attempts",
                    "query": '''
                        SigninLogs
                        | where ResultType != 0
                        | summarize FailedAttempts = count() by UserPrincipalName, IPAddress, bin(TimeGenerated, 5m)
                        | where FailedAttempts > 5
                    ''',
                    "frequency": "PT5M",
                    "severity": "High"
                },
                {
                    "name": "Suspicious Key Vault Access",
                    "query": '''
                        AzureDiagnostics
                        | where ResourceProvider == "MICROSOFT.KEYVAULT"
                        | where ResultSignature == "Forbidden"
                        | project TimeGenerated, OperationName, CallerIPAddress, requestUri_s
                    ''',
                    "frequency": "PT10M",
                    "severity": "Medium"
                },
                {
                    "name": "Mass Data Download",
                    "query": '''
                        OfficeActivity
                        | where Operation == "FileDownloaded"
                        | summarize DownloadCount = count(), TotalSize = sum(Size) by UserId, ClientIP, bin(TimeGenerated, 1h)
                        | where DownloadCount > 100 or TotalSize > 1000000000
                    ''',
                    "frequency": "PT1H",
                    "severity": "High"
                }
            ],
            "playbooks": [
                {
                    "name": "Block-IP-Address",
                    "trigger": "Alert",
                    "actions": ["Block IP in Firewall", "Send Email", "Create Incident"]
                },
                {
                    "name": "Isolate-Compromised-Account",
                    "trigger": "Alert",
                    "actions": ["Disable Account", "Reset Password", "Revoke Sessions"]
                }
            ]
        }


class ThreatIntelligence:
    """Threat intelligence integration"""
    
    @staticmethod
    def get_threat_feeds() -> List[Dict[str, Any]]:
        """Threat intelligence feed configuration"""
        return [
            {
                "name": "AlienVault OTX",
                "url": "https://otx.alienvault.com/api/v1/indicators",
                "api_key": "{{OTX_API_KEY}}",
                "update_frequency": "hourly",
                "types": ["IP", "Domain", "URL", "FileHash"]
            },
            {
                "name": "Abuse.ch Feodo Tracker",
                "url": "https://feodotracker.abuse.ch/downloads/ipblocklist.json",
                "update_frequency": "daily",
                "types": ["IP"]
            },
            {
                "name": "MISP Threat Sharing",
                "url": "https://misp.financialplanner.com",
                "api_key": "{{MISP_API_KEY}}",
                "update_frequency": "real-time",
                "types": ["IP", "Domain", "FileHash", "YARA"]
            },
            {
                "name": "CrowdStrike Threat Intel",
                "url": "https://api.crowdstrike.com/intel/v2",
                "api_key": "{{CROWDSTRIKE_API_KEY}}",
                "update_frequency": "hourly",
                "types": ["IP", "Domain", "Actor", "Malware"]
            }
        ]
    
    @staticmethod
    def get_ioc_patterns() -> Dict[str, List[str]]:
        """Indicators of Compromise patterns"""
        return {
            "malicious_ips": [
                r"^192\.168\.1\.\d{1,3}$",  # Example pattern
                r"^10\.0\.0\.\d{1,3}$"
            ],
            "suspicious_domains": [
                r".*\.tk$",
                r".*\.ml$",
                r".*\.ga$",
                r"^[a-z0-9]{32}\.",  # DGA domains
            ],
            "malware_hashes": {
                "md5": r"^[a-f0-9]{32}$",
                "sha1": r"^[a-f0-9]{40}$",
                "sha256": r"^[a-f0-9]{64}$"
            },
            "suspicious_user_agents": [
                r".*sqlmap.*",
                r".*nikto.*",
                r".*masscan.*",
                r".*nmap.*"
            ],
            "command_injection_patterns": [
                r";\s*cat\s+/etc/passwd",
                r";\s*wget\s+",
                r";\s*curl\s+",
                r"`.*`",
                r"\$\(.*\)"
            ]
        }


class SecurityOrchestration:
    """Security Orchestration, Automation and Response (SOAR)"""
    
    @staticmethod
    def get_incident_response_playbooks() -> Dict[str, Dict[str, Any]]:
        """Automated incident response playbooks"""
        return {
            "brute_force_attack": {
                "trigger": {
                    "condition": "failed_login_attempts > 10",
                    "timeframe": "5_minutes"
                },
                "actions": [
                    {
                        "step": 1,
                        "action": "block_ip",
                        "target": "firewall",
                        "duration": "1_hour"
                    },
                    {
                        "step": 2,
                        "action": "send_alert",
                        "target": "security_team",
                        "priority": "high"
                    },
                    {
                        "step": 3,
                        "action": "capture_packets",
                        "target": "network_tap",
                        "duration": "10_minutes"
                    },
                    {
                        "step": 4,
                        "action": "create_incident",
                        "target": "incident_management",
                        "severity": "high"
                    }
                ]
            },
            "data_exfiltration": {
                "trigger": {
                    "condition": "outbound_data > 1GB",
                    "timeframe": "1_hour"
                },
                "actions": [
                    {
                        "step": 1,
                        "action": "throttle_bandwidth",
                        "target": "network_qos",
                        "limit": "1Mbps"
                    },
                    {
                        "step": 2,
                        "action": "suspend_user",
                        "target": "identity_provider"
                    },
                    {
                        "step": 3,
                        "action": "snapshot_system",
                        "target": "affected_host"
                    },
                    {
                        "step": 4,
                        "action": "notify_dpo",
                        "target": "data_protection_officer",
                        "priority": "critical"
                    }
                ]
            },
            "malware_detection": {
                "trigger": {
                    "condition": "malware_signature_match",
                    "confidence": 0.9
                },
                "actions": [
                    {
                        "step": 1,
                        "action": "isolate_host",
                        "target": "endpoint",
                        "network_access": "blocked"
                    },
                    {
                        "step": 2,
                        "action": "kill_process",
                        "target": "malicious_process"
                    },
                    {
                        "step": 3,
                        "action": "quarantine_file",
                        "target": "malware_file"
                    },
                    {
                        "step": 4,
                        "action": "scan_network",
                        "target": "connected_hosts",
                        "scan_type": "deep"
                    },
                    {
                        "step": 5,
                        "action": "update_signatures",
                        "target": "all_endpoints"
                    }
                ]
            },
            "insider_threat": {
                "trigger": {
                    "condition": "anomalous_user_behavior",
                    "risk_score": 80
                },
                "actions": [
                    {
                        "step": 1,
                        "action": "enable_monitoring",
                        "target": "user_sessions",
                        "level": "detailed"
                    },
                    {
                        "step": 2,
                        "action": "backup_user_data",
                        "target": "user_workspace"
                    },
                    {
                        "step": 3,
                        "action": "restrict_access",
                        "target": "sensitive_data",
                        "level": "read_only"
                    },
                    {
                        "step": 4,
                        "action": "notify_manager",
                        "target": "user_manager",
                        "confidential": True
                    }
                ]
            },
            "ransomware_attack": {
                "trigger": {
                    "condition": "mass_file_encryption",
                    "threshold": 100
                },
                "actions": [
                    {
                        "step": 1,
                        "action": "network_isolation",
                        "target": "all_affected_systems",
                        "immediate": True
                    },
                    {
                        "step": 2,
                        "action": "stop_backup_jobs",
                        "target": "backup_systems"
                    },
                    {
                        "step": 3,
                        "action": "activate_dr_site",
                        "target": "disaster_recovery"
                    },
                    {
                        "step": 4,
                        "action": "notify_executives",
                        "target": "c_suite",
                        "priority": "critical"
                    },
                    {
                        "step": 5,
                        "action": "engage_incident_response",
                        "target": "external_ir_team"
                    }
                ]
            }
        }
    
    @staticmethod
    def get_automation_rules() -> List[Dict[str, Any]]:
        """Security automation rules"""
        return [
            {
                "name": "Auto-block Malicious IPs",
                "trigger": "threat_intel_match",
                "condition": "confidence > 0.8",
                "action": "add_to_blocklist",
                "target": ["firewall", "waf", "cdn"],
                "duration": "24_hours",
                "auto_execute": True
            },
            {
                "name": "Auto-patch Critical Vulnerabilities",
                "trigger": "vulnerability_scan",
                "condition": "cvss_score >= 9.0",
                "action": "apply_patch",
                "target": "affected_systems",
                "maintenance_window": "02:00-04:00",
                "auto_execute": False,
                "approval_required": True
            },
            {
                "name": "Auto-revoke Compromised Credentials",
                "trigger": "credential_leak_detection",
                "condition": "verified_leak == true",
                "action": "force_password_reset",
                "target": "affected_users",
                "notification": "immediate",
                "auto_execute": True
            },
            {
                "name": "Auto-quarantine Suspicious Files",
                "trigger": "file_upload",
                "condition": "sandbox_verdict == 'malicious'",
                "action": "quarantine_file",
                "target": "uploaded_file",
                "scan_connected_systems": True,
                "auto_execute": True
            }
        ]


class SecurityMetrics:
    """Security metrics and KPIs"""
    
    @staticmethod
    def get_security_kpis() -> Dict[str, Any]:
        """Key security performance indicators"""
        return {
            "mean_time_to_detect": {
                "target": "< 1 hour",
                "current": "45 minutes",
                "trend": "improving"
            },
            "mean_time_to_respond": {
                "target": "< 4 hours",
                "current": "3.5 hours",
                "trend": "stable"
            },
            "mean_time_to_remediate": {
                "target": "< 24 hours",
                "current": "18 hours",
                "trend": "improving"
            },
            "patch_compliance_rate": {
                "target": "> 95%",
                "current": "97%",
                "critical_patches": "100%",
                "high_patches": "98%"
            },
            "security_training_completion": {
                "target": "100%",
                "current": "94%",
                "phishing_simulation_pass_rate": "87%"
            },
            "vulnerability_remediation_sla": {
                "critical": {
                    "target": "24 hours",
                    "compliance": "98%"
                },
                "high": {
                    "target": "7 days",
                    "compliance": "95%"
                },
                "medium": {
                    "target": "30 days",
                    "compliance": "92%"
                },
                "low": {
                    "target": "90 days",
                    "compliance": "88%"
                }
            },
            "incident_metrics": {
                "total_incidents_ytd": 127,
                "critical_incidents": 3,
                "false_positive_rate": "12%",
                "incidents_prevented": 89
            }
        }