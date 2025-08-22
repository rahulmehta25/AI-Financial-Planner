"""
Web Application Firewall (WAF) Rules Configuration

Comprehensive WAF rules for AWS WAF, Cloudflare, or custom implementation.
"""

import json
from typing import Dict, List, Any
from enum import Enum


class WAFProvider(Enum):
    """Supported WAF providers"""
    AWS_WAF = "aws_waf"
    CLOUDFLARE = "cloudflare"
    CUSTOM = "custom"


class WAFRuleSet:
    """WAF ruleset configuration"""
    
    @staticmethod
    def get_aws_waf_rules() -> Dict[str, Any]:
        """AWS WAF rules configuration"""
        return {
            "Rules": [
                {
                    "Name": "RateLimitRule",
                    "Priority": 1,
                    "Statement": {
                        "RateBasedStatement": {
                            "Limit": 2000,
                            "AggregateKeyType": "IP"
                        }
                    },
                    "Action": {
                        "Block": {
                            "CustomResponse": {
                                "ResponseCode": 429,
                                "CustomResponseBodyKey": "rate_limit_exceeded"
                            }
                        }
                    },
                    "VisibilityConfig": {
                        "SampledRequestsEnabled": True,
                        "CloudWatchMetricsEnabled": True,
                        "MetricName": "RateLimitRule"
                    }
                },
                {
                    "Name": "SQLInjectionRule",
                    "Priority": 2,
                    "Statement": {
                        "SqliMatchStatement": {
                            "FieldToMatch": {
                                "AllQueryArguments": {}
                            },
                            "TextTransformations": [
                                {"Priority": 0, "Type": "URL_DECODE"},
                                {"Priority": 1, "Type": "HTML_ENTITY_DECODE"}
                            ]
                        }
                    },
                    "Action": {"Block": {}},
                    "VisibilityConfig": {
                        "SampledRequestsEnabled": True,
                        "CloudWatchMetricsEnabled": True,
                        "MetricName": "SQLInjectionRule"
                    }
                },
                {
                    "Name": "XSSProtectionRule",
                    "Priority": 3,
                    "Statement": {
                        "XssMatchStatement": {
                            "FieldToMatch": {
                                "AllQueryArguments": {}
                            },
                            "TextTransformations": [
                                {"Priority": 0, "Type": "URL_DECODE"},
                                {"Priority": 1, "Type": "HTML_ENTITY_DECODE"}
                            ]
                        }
                    },
                    "Action": {"Block": {}},
                    "VisibilityConfig": {
                        "SampledRequestsEnabled": True,
                        "CloudWatchMetricsEnabled": True,
                        "MetricName": "XSSProtectionRule"
                    }
                },
                {
                    "Name": "SizeConstraintRule",
                    "Priority": 4,
                    "Statement": {
                        "SizeConstraintStatement": {
                            "FieldToMatch": {"Body": {}},
                            "ComparisonOperator": "GT",
                            "Size": 10485760,  # 10MB
                            "TextTransformations": [
                                {"Priority": 0, "Type": "NONE"}
                            ]
                        }
                    },
                    "Action": {"Block": {}},
                    "VisibilityConfig": {
                        "SampledRequestsEnabled": True,
                        "CloudWatchMetricsEnabled": True,
                        "MetricName": "SizeConstraintRule"
                    }
                },
                {
                    "Name": "GeoBlockingRule",
                    "Priority": 5,
                    "Statement": {
                        "NotStatement": {
                            "Statement": {
                                "GeoMatchStatement": {
                                    "CountryCodes": [
                                        "US", "CA", "GB", "AU", "NZ", 
                                        "IE", "DE", "FR", "IT", "ES",
                                        "NL", "BE", "CH", "AT", "DK",
                                        "SE", "NO", "FI", "JP", "SG"
                                    ]
                                }
                            }
                        }
                    },
                    "Action": {"Block": {}},
                    "VisibilityConfig": {
                        "SampledRequestsEnabled": True,
                        "CloudWatchMetricsEnabled": True,
                        "MetricName": "GeoBlockingRule"
                    }
                },
                {
                    "Name": "IPReputationList",
                    "Priority": 6,
                    "Statement": {
                        "ManagedRuleGroupStatement": {
                            "VendorName": "AWS",
                            "Name": "AWSManagedRulesAmazonIpReputationList"
                        }
                    },
                    "OverrideAction": {"None": {}},
                    "VisibilityConfig": {
                        "SampledRequestsEnabled": True,
                        "CloudWatchMetricsEnabled": True,
                        "MetricName": "IPReputationList"
                    }
                },
                {
                    "Name": "KnownBadInputsRule",
                    "Priority": 7,
                    "Statement": {
                        "ManagedRuleGroupStatement": {
                            "VendorName": "AWS",
                            "Name": "AWSManagedRulesKnownBadInputsRuleSet"
                        }
                    },
                    "OverrideAction": {"None": {}},
                    "VisibilityConfig": {
                        "SampledRequestsEnabled": True,
                        "CloudWatchMetricsEnabled": True,
                        "MetricName": "KnownBadInputsRule"
                    }
                },
                {
                    "Name": "CoreRuleSet",
                    "Priority": 8,
                    "Statement": {
                        "ManagedRuleGroupStatement": {
                            "VendorName": "AWS",
                            "Name": "AWSManagedRulesCommonRuleSet",
                            "ExcludedRules": [
                                {"Name": "SizeRestrictions_BODY"},
                                {"Name": "GenericRFI_BODY"}
                            ]
                        }
                    },
                    "OverrideAction": {"None": {}},
                    "VisibilityConfig": {
                        "SampledRequestsEnabled": True,
                        "CloudWatchMetricsEnabled": True,
                        "MetricName": "CoreRuleSet"
                    }
                },
                {
                    "Name": "PathTraversalRule",
                    "Priority": 9,
                    "Statement": {
                        "ByteMatchStatement": {
                            "SearchString": "../",
                            "FieldToMatch": {
                                "UriPath": {}
                            },
                            "TextTransformations": [
                                {"Priority": 0, "Type": "URL_DECODE"},
                                {"Priority": 1, "Type": "NORMALIZE_PATH"}
                            ],
                            "PositionalConstraint": "CONTAINS"
                        }
                    },
                    "Action": {"Block": {}},
                    "VisibilityConfig": {
                        "SampledRequestsEnabled": True,
                        "CloudWatchMetricsEnabled": True,
                        "MetricName": "PathTraversalRule"
                    }
                },
                {
                    "Name": "AdminPathProtection",
                    "Priority": 10,
                    "Statement": {
                        "AndStatement": {
                            "Statements": [
                                {
                                    "ByteMatchStatement": {
                                        "SearchString": "/admin",
                                        "FieldToMatch": {"UriPath": {}},
                                        "TextTransformations": [
                                            {"Priority": 0, "Type": "LOWERCASE"}
                                        ],
                                        "PositionalConstraint": "STARTS_WITH"
                                    }
                                },
                                {
                                    "NotStatement": {
                                        "Statement": {
                                            "IPSetReferenceStatement": {
                                                "Arn": "arn:aws:wafv2:region:account:global/ipset/admin-whitelist/id"
                                            }
                                        }
                                    }
                                }
                            ]
                        }
                    },
                    "Action": {"Block": {}},
                    "VisibilityConfig": {
                        "SampledRequestsEnabled": True,
                        "CloudWatchMetricsEnabled": True,
                        "MetricName": "AdminPathProtection"
                    }
                }
            ],
            "CustomResponseBodies": {
                "rate_limit_exceeded": {
                    "ContentType": "APPLICATION_JSON",
                    "Content": json.dumps({
                        "error": "Rate limit exceeded",
                        "message": "Too many requests. Please try again later."
                    })
                }
            }
        }
    
    @staticmethod
    def get_cloudflare_rules() -> List[Dict[str, Any]]:
        """Cloudflare WAF rules configuration"""
        return [
            {
                "description": "Block SQL Injection",
                "expression": '(http.request.uri.query contains "SELECT" and http.request.uri.query contains "FROM") or (http.request.uri.query contains "INSERT" and http.request.uri.query contains "INTO") or (http.request.uri.query contains "UPDATE" and http.request.uri.query contains "SET") or (http.request.uri.query contains "DELETE" and http.request.uri.query contains "FROM") or (http.request.uri.query contains "DROP" and http.request.uri.query contains "TABLE") or (http.request.uri.query contains "1=1") or (http.request.uri.query contains "1 = 1") or (http.request.uri.query contains "OR 1=1") or (http.request.uri.query contains "' OR '1'='1")',
                "action": "block"
            },
            {
                "description": "Block XSS Attacks",
                "expression": '(http.request.uri.query contains "<script") or (http.request.uri.query contains "javascript:") or (http.request.uri.query contains "onerror=") or (http.request.uri.query contains "onload=") or (http.request.body.raw contains "<script") or (http.request.body.raw contains "javascript:")',
                "action": "block"
            },
            {
                "description": "Block Path Traversal",
                "expression": '(http.request.uri.path contains "../") or (http.request.uri.path contains "..\\") or (http.request.uri.path contains "%2e%2e") or (http.request.uri.path contains "/etc/passwd") or (http.request.uri.path contains "C:\\Windows")',
                "action": "block"
            },
            {
                "description": "Rate Limiting",
                "expression": "(http.request.uri.path contains \"/api/\")",
                "action": "challenge",
                "ratelimit": {
                    "threshold": 50,
                    "period": 60,
                    "action": "block"
                }
            },
            {
                "description": "Geo-blocking for high-risk countries",
                "expression": '(ip.geoip.country in {"CN" "RU" "KP" "IR"})',
                "action": "block"
            },
            {
                "description": "Block Known Bad User Agents",
                "expression": '(http.user_agent contains "sqlmap") or (http.user_agent contains "nikto") or (http.user_agent contains "acunetix") or (http.user_agent contains "nmap") or (http.user_agent contains "metasploit")',
                "action": "block"
            },
            {
                "description": "Protect Admin Paths",
                "expression": '(http.request.uri.path contains "/admin" and not ip.src in {192.168.1.0/24 10.0.0.0/8})',
                "action": "block"
            },
            {
                "description": "Block Large Payloads",
                "expression": "(http.request.body.size > 10485760)",
                "action": "block"
            },
            {
                "description": "OWASP Core Rule Set",
                "action": "execute",
                "action_parameters": {
                    "id": "efb7b8c949ac4650a09736fc376e9aee",
                    "overrides": {
                        "enabled": True,
                        "rules": [
                            {
                                "id": "6179ae15870a4bb7b2d480d4843b323c",
                                "enabled": False
                            }
                        ]
                    }
                }
            },
            {
                "description": "Challenge Suspicious Requests",
                "expression": '(cf.threat_score > 30)',
                "action": "managed_challenge"
            }
        ]
    
    @staticmethod
    def get_custom_modsecurity_rules() -> str:
        """ModSecurity rules for custom WAF implementation"""
        return """
# ModSecurity Core Rule Set (CRS) Configuration

SecRuleEngine On
SecRequestBodyAccess On
SecResponseBodyAccess On
SecRequestBodyLimit 10485760
SecRequestBodyNoFilesLimit 131072
SecRequestBodyLimitAction Reject
SecResponseBodyLimit 524288
SecResponseBodyLimitAction ProcessPartial

# Audit logging
SecAuditEngine RelevantOnly
SecAuditLogRelevantStatus "^(?:5|4(?!04))"
SecAuditLogParts ABIJDEFHZ
SecAuditLogType Serial
SecAuditLog /var/log/modsec_audit.log

# Default action
SecDefaultAction "phase:1,log,auditlog,pass"

# Rate limiting
SecAction "phase:1,id:1001,initcol:ip=%{REMOTE_ADDR},pass,nolog"
SecRule IP:REQUEST_COUNT "@gt 100" \
    "phase:2,id:1002,block,msg:'Rate limit exceeded',logdata:'Requests: %{IP.REQUEST_COUNT}'"
SecAction "phase:5,id:1003,deprecatevar:ip.request_count=1/60,pass,nolog"

# SQL Injection Protection
SecRule REQUEST_COOKIES|!REQUEST_COOKIES:/__utm/|REQUEST_COOKIES_NAMES|ARGS_NAMES|ARGS|XML:/* \
    "@detectSQLi" \
    "id:1100,\
    phase:2,\
    block,\
    msg:'SQL Injection Attack Detected',\
    logdata:'Matched Data: %{MATCHED_VAR} found within %{MATCHED_VAR_NAME}',\
    t:none,t:utf8toUnicode,t:urlDecodeUni,t:removeNulls,t:removeComments"

# XSS Protection
SecRule REQUEST_COOKIES|!REQUEST_COOKIES:/__utm/|REQUEST_COOKIES_NAMES|REQUEST_HEADERS:User-Agent|REQUEST_HEADERS:Referer|ARGS_NAMES|ARGS|XML:/* \
    "@detectXSS" \
    "id:1200,\
    phase:2,\
    block,\
    msg:'XSS Attack Detected',\
    logdata:'Matched Data: %{MATCHED_VAR} found within %{MATCHED_VAR_NAME}',\
    t:none,t:utf8toUnicode,t:urlDecodeUni,t:htmlEntityDecode,t:jsDecode,t:cssDecode,t:removeNulls"

# Path Traversal Protection
SecRule REQUEST_URI|ARGS|REQUEST_HEADERS:Cookie \
    "@contains ../" \
    "id:1300,\
    phase:2,\
    block,\
    msg:'Path Traversal Attack',\
    logdata:'Matched Data: %{MATCHED_VAR} found within %{MATCHED_VAR_NAME}'"

# Command Injection Protection
SecRule ARGS|REQUEST_HEADERS:User-Agent \
    "@contains |" \
    "chain,id:1400,\
    phase:2,\
    block,\
    msg:'OS Command Injection',\
    logdata:'Matched Data: %{MATCHED_VAR} found within %{MATCHED_VAR_NAME}'"
    SecRule MATCHED_VAR "@rx (?:;|\||`|>|<|\$\(|\)|\{|\})"

# File Upload Protection
SecRule FILES_TMPNAMES "@rx \.(php|phtml|php3|php4|php5|phps|phar|exe|bat|cmd|sh|cgi)$" \
    "id:1500,\
    phase:2,\
    block,\
    msg:'Malicious File Upload Attempt',\
    logdata:'File name: %{MATCHED_VAR}'"

# Protocol Anomaly Detection
SecRule REQUEST_METHOD "!@rx ^(?:GET|HEAD|POST|PUT|DELETE|OPTIONS)$" \
    "id:1600,\
    phase:1,\
    block,\
    msg:'Invalid HTTP Method',\
    logdata:'Method: %{REQUEST_METHOD}'"

# Scanner Detection
SecRule REQUEST_HEADERS:User-Agent "@pmFromFile scanners.data" \
    "id:1700,\
    phase:1,\
    block,\
    msg:'Security Scanner Detected',\
    logdata:'Scanner: %{MATCHED_VAR}'"

# CSRF Protection
SecRule REQUEST_METHOD "@streq POST" \
    "chain,id:1800,\
    phase:2,\
    block,\
    msg:'CSRF Attack Detected'"
    SecRule &REQUEST_HEADERS:X-CSRF-Token "@eq 0"

# Session Fixation Protection
SecRule RESPONSE_HEADERS:Set-Cookie "!@contains httponly" \
    "id:1900,\
    phase:3,\
    pass,\
    msg:'Cookie without HttpOnly flag'"

SecRule RESPONSE_HEADERS:Set-Cookie "!@contains secure" \
    "id:1901,\
    phase:3,\
    pass,\
    msg:'Cookie without Secure flag'"
"""


class DDoSProtection:
    """DDoS protection configuration"""
    
    @staticmethod
    def get_cloudflare_ddos_config() -> Dict[str, Any]:
        """Cloudflare DDoS protection settings"""
        return {
            "ddos_protection": {
                "sensitivity_level": "high",
                "action": "challenge",
                "threshold": {
                    "requests_per_second": 100,
                    "requests_per_minute": 2000
                }
            },
            "rate_limiting": {
                "rules": [
                    {
                        "threshold": 50,
                        "period": 60,
                        "action": "simulate",
                        "match": {
                            "request": {
                                "url": "/api/*",
                                "methods": ["POST", "PUT", "DELETE"]
                            }
                        }
                    },
                    {
                        "threshold": 10,
                        "period": 60,
                        "action": "block",
                        "match": {
                            "request": {
                                "url": "/api/auth/login",
                                "methods": ["POST"]
                            }
                        }
                    }
                ]
            },
            "bot_management": {
                "definitely_automated": "block",
                "likely_automated": "challenge",
                "verified_bots": "allow",
                "js_detection": True,
                "static_resource_protection": True
            }
        }
    
    @staticmethod
    def get_aws_shield_config() -> Dict[str, Any]:
        """AWS Shield Advanced configuration"""
        return {
            "protection": {
                "name": "FinancialPlannerProtection",
                "resource_arn": "arn:aws:elasticloadbalancing:region:account:loadbalancer/app/name/id",
                "protection_type": "APPLICATION_LOAD_BALANCER"
            },
            "emergency_contacts": [
                {
                    "email": "security@financialplanner.com",
                    "phone": "+1234567890",
                    "contact_notes": "Primary security contact"
                }
            ],
            "proactive_engagement": {
                "enabled": True,
                "status": "ENABLED"
            },
            "ddos_response_team_access": {
                "role_arn": "arn:aws:iam::account:role/AWSDDOSResponseTeamRole"
            },
            "associated_health_checks": [
                {
                    "health_check_arn": "arn:aws:route53:::healthcheck/id"
                }
            ]
        }