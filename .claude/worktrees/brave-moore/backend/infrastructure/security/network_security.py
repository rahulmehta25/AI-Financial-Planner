"""
Network Security and Infrastructure Hardening

Network segmentation, bastion hosts, VPN configuration, and security architecture.
"""

import ipaddress
from typing import Dict, List, Any, Optional
from enum import Enum


class NetworkZone(Enum):
    """Network security zones"""
    PUBLIC = "public"
    DMZ = "dmz"
    INTERNAL = "internal"
    RESTRICTED = "restricted"
    MANAGEMENT = "management"


class NetworkSegmentation:
    """Network segmentation configuration"""
    
    @staticmethod
    def get_network_architecture() -> Dict[str, Any]:
        """Complete network architecture with security zones"""
        return {
            "vpc_configuration": {
                "production": {
                    "cidr": "10.0.0.0/16",
                    "region": "us-east-1",
                    "availability_zones": ["us-east-1a", "us-east-1b", "us-east-1c"],
                    "flow_logs": True,
                    "dns_firewall": True
                }
            },
            "subnets": {
                "public": {
                    "purpose": "Internet-facing services",
                    "cidrs": [
                        "10.0.1.0/24",  # AZ-1
                        "10.0.2.0/24",  # AZ-2
                        "10.0.3.0/24"   # AZ-3
                    ],
                    "services": ["ALB", "NAT Gateway", "Bastion Host"],
                    "internet_gateway": True,
                    "nat_gateway": False
                },
                "dmz": {
                    "purpose": "Web and API servers",
                    "cidrs": [
                        "10.0.10.0/24",  # AZ-1
                        "10.0.11.0/24",  # AZ-2
                        "10.0.12.0/24"   # AZ-3
                    ],
                    "services": ["Web Servers", "API Gateway", "WAF"],
                    "internet_gateway": False,
                    "nat_gateway": True
                },
                "application": {
                    "purpose": "Application servers",
                    "cidrs": [
                        "10.0.20.0/24",  # AZ-1
                        "10.0.21.0/24",  # AZ-2
                        "10.0.22.0/24"   # AZ-3
                    ],
                    "services": ["App Servers", "Container Cluster", "Lambda"],
                    "internet_gateway": False,
                    "nat_gateway": True
                },
                "database": {
                    "purpose": "Database servers",
                    "cidrs": [
                        "10.0.30.0/24",  # AZ-1
                        "10.0.31.0/24",  # AZ-2
                        "10.0.32.0/24"   # AZ-3
                    ],
                    "services": ["RDS", "ElastiCache", "DocumentDB"],
                    "internet_gateway": False,
                    "nat_gateway": False
                },
                "management": {
                    "purpose": "Management and monitoring",
                    "cidrs": [
                        "10.0.40.0/24"  # Single AZ
                    ],
                    "services": ["Bastion", "Monitoring", "Logging"],
                    "internet_gateway": False,
                    "nat_gateway": True
                },
                "restricted": {
                    "purpose": "Highly sensitive services",
                    "cidrs": [
                        "10.0.50.0/24"  # Single AZ
                    ],
                    "services": ["HSM", "Key Management", "Secrets"],
                    "internet_gateway": False,
                    "nat_gateway": False
                }
            },
            "security_groups": {
                "alb_sg": {
                    "description": "Application Load Balancer",
                    "ingress": [
                        {"protocol": "tcp", "port": 443, "source": "0.0.0.0/0"},
                        {"protocol": "tcp", "port": 80, "source": "0.0.0.0/0"}
                    ],
                    "egress": [
                        {"protocol": "tcp", "port": 443, "destination": "dmz_sg"},
                        {"protocol": "tcp", "port": 8080, "destination": "dmz_sg"}
                    ]
                },
                "web_sg": {
                    "description": "Web servers in DMZ",
                    "ingress": [
                        {"protocol": "tcp", "port": 443, "source": "alb_sg"},
                        {"protocol": "tcp", "port": 8080, "source": "alb_sg"}
                    ],
                    "egress": [
                        {"protocol": "tcp", "port": 8000, "destination": "app_sg"},
                        {"protocol": "tcp", "port": 443, "destination": "0.0.0.0/0"}
                    ]
                },
                "app_sg": {
                    "description": "Application servers",
                    "ingress": [
                        {"protocol": "tcp", "port": 8000, "source": "web_sg"}
                    ],
                    "egress": [
                        {"protocol": "tcp", "port": 5432, "destination": "db_sg"},
                        {"protocol": "tcp", "port": 6379, "destination": "cache_sg"},
                        {"protocol": "tcp", "port": 443, "destination": "0.0.0.0/0"}
                    ]
                },
                "db_sg": {
                    "description": "Database servers",
                    "ingress": [
                        {"protocol": "tcp", "port": 5432, "source": "app_sg"},
                        {"protocol": "tcp", "port": 5432, "source": "bastion_sg"}
                    ],
                    "egress": []  # No outbound connections
                },
                "bastion_sg": {
                    "description": "Bastion host for SSH access",
                    "ingress": [
                        {"protocol": "tcp", "port": 22, "source": "vpn_cidr"}
                    ],
                    "egress": [
                        {"protocol": "tcp", "port": 22, "destination": "all_internal"}
                    ]
                }
            },
            "network_acls": {
                "public_nacl": {
                    "subnet": "public",
                    "rules": [
                        {"rule": 100, "protocol": "tcp", "action": "allow", "port": 443, "source": "0.0.0.0/0"},
                        {"rule": 110, "protocol": "tcp", "action": "allow", "port": 80, "source": "0.0.0.0/0"},
                        {"rule": 200, "protocol": "tcp", "action": "allow", "port": "1024-65535", "source": "0.0.0.0/0"},
                        {"rule": 900, "protocol": "all", "action": "deny", "source": "0.0.0.0/0"}
                    ]
                },
                "database_nacl": {
                    "subnet": "database",
                    "rules": [
                        {"rule": 100, "protocol": "tcp", "action": "allow", "port": 5432, "source": "10.0.20.0/22"},
                        {"rule": 110, "protocol": "tcp", "action": "allow", "port": 5432, "source": "10.0.40.0/24"},
                        {"rule": 900, "protocol": "all", "action": "deny", "source": "0.0.0.0/0"}
                    ]
                }
            }
        }
    
    @staticmethod
    def get_firewall_rules() -> List[Dict[str, Any]]:
        """Comprehensive firewall rules"""
        return [
            # Inbound Rules
            {
                "priority": 100,
                "name": "AllowHTTPS",
                "direction": "inbound",
                "protocol": "tcp",
                "source": "0.0.0.0/0",
                "destination": "10.0.1.0/24",
                "port": 443,
                "action": "allow"
            },
            {
                "priority": 110,
                "name": "AllowHTTP",
                "direction": "inbound",
                "protocol": "tcp",
                "source": "0.0.0.0/0",
                "destination": "10.0.1.0/24",
                "port": 80,
                "action": "allow"
            },
            {
                "priority": 200,
                "name": "AllowSSHFromVPN",
                "direction": "inbound",
                "protocol": "tcp",
                "source": "192.168.100.0/24",  # VPN subnet
                "destination": "10.0.40.0/24",  # Management subnet
                "port": 22,
                "action": "allow"
            },
            {
                "priority": 300,
                "name": "AllowMonitoring",
                "direction": "inbound",
                "protocol": "tcp",
                "source": "10.0.40.0/24",
                "destination": "10.0.0.0/16",
                "port": "9090-9100",
                "action": "allow"
            },
            {
                "priority": 1000,
                "name": "DenyAllInbound",
                "direction": "inbound",
                "protocol": "all",
                "source": "0.0.0.0/0",
                "destination": "10.0.0.0/16",
                "action": "deny"
            },
            # Outbound Rules
            {
                "priority": 100,
                "name": "AllowHTTPSOutbound",
                "direction": "outbound",
                "protocol": "tcp",
                "source": "10.0.0.0/16",
                "destination": "0.0.0.0/0",
                "port": 443,
                "action": "allow"
            },
            {
                "priority": 200,
                "name": "AllowDNS",
                "direction": "outbound",
                "protocol": "udp",
                "source": "10.0.0.0/16",
                "destination": "0.0.0.0/0",
                "port": 53,
                "action": "allow"
            },
            {
                "priority": 300,
                "name": "AllowNTP",
                "direction": "outbound",
                "protocol": "udp",
                "source": "10.0.0.0/16",
                "destination": "0.0.0.0/0",
                "port": 123,
                "action": "allow"
            },
            {
                "priority": 1000,
                "name": "DenyAllOutbound",
                "direction": "outbound",
                "protocol": "all",
                "source": "10.0.30.0/24",  # Database subnet
                "destination": "0.0.0.0/0",
                "action": "deny"
            }
        ]


class BastionHostConfiguration:
    """Bastion host (jump server) configuration"""
    
    @staticmethod
    def get_bastion_config() -> Dict[str, Any]:
        """Bastion host security configuration"""
        return {
            "instance_configuration": {
                "instance_type": "t3.small",
                "ami": "hardened-amazon-linux-2",
                "subnet": "public",
                "auto_scaling": {
                    "min": 2,
                    "max": 4,
                    "desired": 2
                },
                "user_data": '''#!/bin/bash
                    # Update system
                    yum update -y
                    
                    # Install security tools
                    yum install -y fail2ban aide lynis
                    
                    # Configure SSH
                    sed -i 's/PermitRootLogin yes/PermitRootLogin no/g' /etc/ssh/sshd_config
                    sed -i 's/#MaxAuthTries 6/MaxAuthTries 3/g' /etc/ssh/sshd_config
                    sed -i 's/#ClientAliveInterval 0/ClientAliveInterval 300/g' /etc/ssh/sshd_config
                    sed -i 's/#ClientAliveCountMax 3/ClientAliveCountMax 2/g' /etc/ssh/sshd_config
                    echo "AllowUsers bastion-user" >> /etc/ssh/sshd_config
                    
                    # Configure fail2ban
                    systemctl enable fail2ban
                    systemctl start fail2ban
                    
                    # Configure auditd
                    auditctl -w /etc/passwd -p wa -k passwd_changes
                    auditctl -w /etc/shadow -p wa -k shadow_changes
                    auditctl -w /var/log/sudo.log -p wa -k sudo_log_changes
                    
                    # Install session recording
                    yum install -y ttyrec
                    echo 'ForceCommand /usr/bin/ttyrec -e $SHELL' >> /etc/ssh/sshd_config
                    
                    systemctl restart sshd
                '''
            },
            "ssh_configuration": {
                "port": 22,
                "protocol": 2,
                "permit_root_login": "no",
                "password_authentication": "no",
                "pubkey_authentication": "yes",
                "max_auth_tries": 3,
                "client_alive_interval": 300,
                "client_alive_count_max": 2,
                "allowed_users": ["bastion-user"],
                "login_grace_time": 60,
                "strict_modes": "yes",
                "permit_empty_passwords": "no",
                "challenge_response_authentication": "no",
                "use_pam": "yes",
                "x11_forwarding": "no",
                "print_motd": "yes",
                "tcp_keepalive": "yes",
                "compression": "no",
                "allow_agent_forwarding": "yes",
                "allow_tcp_forwarding": "yes"
            },
            "session_recording": {
                "enabled": True,
                "storage": "s3://security-logs/bastion-sessions/",
                "retention": "90_days",
                "encryption": "AES-256"
            },
            "monitoring": {
                "cloudwatch_logs": [
                    "/var/log/secure",
                    "/var/log/audit/audit.log",
                    "/var/log/messages"
                ],
                "metrics": [
                    "CPU Utilization",
                    "Network In/Out",
                    "Failed SSH Attempts",
                    "Successful Logins"
                ],
                "alarms": {
                    "high_cpu": {"threshold": 80, "period": 300},
                    "failed_ssh": {"threshold": 5, "period": 300},
                    "root_login_attempt": {"threshold": 1, "period": 60}
                }
            },
            "access_control": {
                "mfa_required": True,
                "ip_whitelist": [
                    "203.0.113.0/24",  # Corporate network
                    "198.51.100.0/24"  # VPN exit points
                ],
                "time_based_access": {
                    "enabled": True,
                    "business_hours": "08:00-20:00",
                    "timezone": "UTC",
                    "emergency_override": True
                },
                "session_timeout": 900,  # 15 minutes
                "concurrent_sessions": 2
            }
        }


class VPNConfiguration:
    """VPN configuration for secure remote access"""
    
    @staticmethod
    def get_site_to_site_vpn() -> Dict[str, Any]:
        """Site-to-site VPN configuration"""
        return {
            "vpn_gateway": {
                "type": "ipsec",
                "redundancy": "active-active",
                "bgp_asn": 65000
            },
            "customer_gateways": [
                {
                    "name": "HQ-Gateway",
                    "ip_address": "203.0.113.100",
                    "bgp_asn": 65001,
                    "device": "Cisco ASA"
                },
                {
                    "name": "DR-Gateway",
                    "ip_address": "198.51.100.200",
                    "bgp_asn": 65002,
                    "device": "pfSense"
                }
            ],
            "tunnels": {
                "tunnel_1": {
                    "encryption": ["AES-256-GCM", "AES-256-CBC"],
                    "integrity": ["SHA256", "SHA1"],
                    "dh_group": [14, 20, 21],
                    "ike_version": 2,
                    "phase1_lifetime": 28800,
                    "phase2_lifetime": 3600,
                    "dpd_timeout": 30,
                    "dpd_action": "restart",
                    "replay_window": 1024
                },
                "tunnel_2": {
                    "encryption": ["AES-256-GCM", "AES-256-CBC"],
                    "integrity": ["SHA256", "SHA1"],
                    "dh_group": [14, 20, 21],
                    "ike_version": 2,
                    "phase1_lifetime": 28800,
                    "phase2_lifetime": 3600,
                    "dpd_timeout": 30,
                    "dpd_action": "restart",
                    "replay_window": 1024
                }
            },
            "routing": {
                "type": "bgp",
                "static_routes": [
                    {"destination": "192.168.0.0/16", "target": "HQ-Gateway"},
                    {"destination": "172.16.0.0/12", "target": "DR-Gateway"}
                ]
            },
            "monitoring": {
                "tunnel_state": True,
                "bgp_state": True,
                "packet_loss": True,
                "latency": True,
                "bandwidth_utilization": True
            }
        }
    
    @staticmethod
    def get_client_vpn_config() -> Dict[str, Any]:
        """Client VPN configuration for remote users"""
        return {
            "vpn_type": "OpenVPN",
            "authentication": {
                "method": "certificate_and_mfa",
                "certificate_authority": "internal_ca",
                "mfa_provider": "duo",
                "saml_provider": "okta"
            },
            "network_configuration": {
                "client_cidr": "192.168.100.0/22",
                "dns_servers": ["10.0.0.2", "10.0.0.3"],
                "split_tunnel": True,
                "routes": [
                    "10.0.0.0/16",  # VPC CIDR
                    "192.168.0.0/16"  # Corporate network
                ]
            },
            "security_settings": {
                "protocol": "UDP",
                "port": 1194,
                "cipher": "AES-256-GCM",
                "auth": "SHA256",
                "tls_version": "1.2",
                "dh_param_bits": 2048,
                "renegotiation_interval": 3600,
                "max_clients": 500,
                "client_to_client": False,
                "compression": "disabled"
            },
            "access_control": {
                "authorization_rules": [
                    {
                        "group": "developers",
                        "access": ["10.0.20.0/24", "10.0.21.0/24"]
                    },
                    {
                        "group": "admins",
                        "access": ["10.0.0.0/16"]
                    },
                    {
                        "group": "support",
                        "access": ["10.0.40.0/24"]
                    }
                ],
                "revocation_list": True,
                "session_timeout": 43200,  # 12 hours
                "idle_timeout": 1800  # 30 minutes
            },
            "logging": {
                "connection_logs": True,
                "data_transfer_logs": True,
                "authentication_logs": True,
                "retention": "90_days"
            }
        }


class ZeroTrustArchitecture:
    """Zero Trust security architecture"""
    
    @staticmethod
    def get_zero_trust_config() -> Dict[str, Any]:
        """Zero Trust architecture configuration"""
        return {
            "principles": {
                "never_trust_always_verify": True,
                "least_privilege_access": True,
                "assume_breach": True,
                "verify_explicitly": True,
                "secure_by_design": True
            },
            "identity_verification": {
                "multi_factor_authentication": {
                    "required": True,
                    "methods": ["TOTP", "WebAuthn", "SMS", "Biometric"],
                    "adaptive": True,
                    "risk_based": True
                },
                "continuous_verification": {
                    "interval": 3600,
                    "factors": ["location", "device", "behavior", "time"]
                },
                "privileged_access_management": {
                    "just_in_time_access": True,
                    "approval_workflow": True,
                    "session_recording": True,
                    "credential_vaulting": True
                }
            },
            "device_trust": {
                "device_registration": True,
                "compliance_checking": {
                    "os_version": True,
                    "patch_level": True,
                    "antivirus": True,
                    "encryption": True,
                    "firewall": True
                },
                "device_health_attestation": True,
                "managed_devices_only": False,
                "byod_policy": {
                    "allowed": True,
                    "containerization": True,
                    "app_protection": True
                }
            },
            "microsegmentation": {
                "application_level": True,
                "workload_level": True,
                "data_level": True,
                "user_level": True,
                "enforcement_points": [
                    "Network firewall",
                    "Application firewall",
                    "Identity proxy",
                    "Service mesh"
                ]
            },
            "data_protection": {
                "classification": ["Public", "Internal", "Confidential", "Restricted"],
                "encryption": {
                    "at_rest": True,
                    "in_transit": True,
                    "in_use": True
                },
                "dlp_policies": True,
                "rights_management": True
            },
            "monitoring_and_analytics": {
                "user_behavior_analytics": True,
                "entity_behavior_analytics": True,
                "risk_scoring": True,
                "anomaly_detection": True,
                "threat_intelligence_integration": True
            }
        }