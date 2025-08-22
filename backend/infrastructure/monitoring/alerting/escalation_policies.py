"""
PagerDuty Escalation Policies for Financial Planning Application
This defines the escalation matrix for different types of incidents
"""

import os
from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Optional
import requests
import json

class Severity(Enum):
    CRITICAL = "critical"
    HIGH = "high" 
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

class Component(Enum):
    API = "api"
    DATABASE = "database"
    CACHE = "cache"
    MONTE_CARLO = "monte_carlo"
    MARKET_DATA = "market_data"
    AI_RECOMMENDATIONS = "ai_recommendations"
    BANKING_INTEGRATION = "banking_integration"
    VOICE_INTERFACE = "voice_interface"
    PDF_GENERATION = "pdf_generation"
    INFRASTRUCTURE = "infrastructure"

@dataclass
class EscalationStep:
    level: int
    delay_minutes: int
    targets: List[str]  # PagerDuty user/schedule IDs
    notification_methods: List[str]  # email, sms, phone

@dataclass
class EscalationPolicy:
    name: str
    component: Component
    severity: Severity
    steps: List[EscalationStep]
    business_hours_only: bool = False
    
class FinancialPlanningEscalations:
    def __init__(self, pagerduty_api_token: str):
        self.api_token = pagerduty_api_token
        self.base_url = "https://api.pagerduty.com"
        
        # Define team members and their roles
        self.team_members = {
            "primary_engineer": "P1XXXXX",  # Replace with actual PagerDuty user IDs
            "backend_lead": "P2XXXXX",
            "devops_lead": "P3XXXXX",
            "ml_engineer": "P4XXXXX",
            "data_engineer": "P5XXXXX",
            "security_engineer": "P6XXXXX",
            "product_manager": "P7XXXXX",
            "engineering_manager": "P8XXXXX",
            "cto": "P9XXXXX"
        }
        
        # Define schedules
        self.schedules = {
            "primary_oncall": "PXXXXXXX",  # Replace with actual schedule IDs
            "backend_oncall": "PXXXXXXX", 
            "devops_oncall": "PXXXXXXX",
            "escalation_schedule": "PXXXXXXX"
        }
    
    def get_escalation_policies(self) -> List[EscalationPolicy]:
        """Define all escalation policies for the financial planning system"""
        
        return [
            # Critical System-Wide Issues
            EscalationPolicy(
                name="Critical System Failure",
                component=Component.API,
                severity=Severity.CRITICAL,
                steps=[
                    EscalationStep(1, 0, [self.schedules["primary_oncall"]], ["sms", "phone"]),
                    EscalationStep(2, 5, [self.team_members["backend_lead"]], ["sms", "phone"]),
                    EscalationStep(3, 10, [self.team_members["devops_lead"]], ["sms", "phone"]),
                    EscalationStep(4, 15, [self.team_members["engineering_manager"]], ["sms", "phone", "email"]),
                    EscalationStep(5, 30, [self.team_members["cto"]], ["phone", "email"])
                ]
            ),
            
            # Database Issues
            EscalationPolicy(
                name="Database Critical Issues",
                component=Component.DATABASE,
                severity=Severity.CRITICAL,
                steps=[
                    EscalationStep(1, 0, [self.schedules["primary_oncall"]], ["sms", "phone"]),
                    EscalationStep(2, 3, [self.team_members["backend_lead"]], ["sms", "phone"]),
                    EscalationStep(3, 8, [self.team_members["devops_lead"]], ["sms", "phone"]),
                    EscalationStep(4, 15, [self.team_members["engineering_manager"]], ["phone", "email"])
                ]
            ),
            
            # Monte Carlo Simulation Issues
            EscalationPolicy(
                name="Simulation Engine Failure",
                component=Component.MONTE_CARLO,
                severity=Severity.HIGH,
                steps=[
                    EscalationStep(1, 0, [self.schedules["primary_oncall"]], ["sms"]),
                    EscalationStep(2, 10, [self.team_members["ml_engineer"]], ["sms", "email"]),
                    EscalationStep(3, 20, [self.team_members["backend_lead"]], ["sms", "email"]),
                    EscalationStep(4, 45, [self.team_members["engineering_manager"]], ["email"])
                ]
            ),
            
            # Market Data Issues
            EscalationPolicy(
                name="Market Data Pipeline Issues",
                component=Component.MARKET_DATA,
                severity=Severity.HIGH,
                steps=[
                    EscalationStep(1, 0, [self.team_members["data_engineer"]], ["sms"]),
                    EscalationStep(2, 15, [self.team_members["backend_lead"]], ["sms", "email"]),
                    EscalationStep(3, 30, [self.team_members["product_manager"]], ["email"]),
                    EscalationStep(4, 60, [self.team_members["engineering_manager"]], ["email"])
                ],
                business_hours_only=True  # Market data issues less critical after hours
            ),
            
            # AI Recommendation Issues
            EscalationPolicy(
                name="AI Recommendation System Issues",
                component=Component.AI_RECOMMENDATIONS,
                severity=Severity.MEDIUM,
                steps=[
                    EscalationStep(1, 0, [self.team_members["ml_engineer"]], ["email"]),
                    EscalationStep(2, 30, [self.team_members["backend_lead"]], ["email"]),
                    EscalationStep(3, 120, [self.team_members["engineering_manager"]], ["email"])
                ],
                business_hours_only=True
            ),
            
            # Banking Integration Issues
            EscalationPolicy(
                name="Banking Integration Failure",
                component=Component.BANKING_INTEGRATION,
                severity=Severity.HIGH,
                steps=[
                    EscalationStep(1, 0, [self.schedules["primary_oncall"]], ["sms"]),
                    EscalationStep(2, 10, [self.team_members["security_engineer"]], ["sms"]),
                    EscalationStep(3, 15, [self.team_members["backend_lead"]], ["sms", "email"]),
                    EscalationStep(4, 30, [self.team_members["engineering_manager"]], ["phone", "email"])
                ]
            ),
            
            # Infrastructure Issues
            EscalationPolicy(
                name="Infrastructure Problems",
                component=Component.INFRASTRUCTURE,
                severity=Severity.HIGH,
                steps=[
                    EscalationStep(1, 0, [self.schedules["devops_oncall"]], ["sms"]),
                    EscalationStep(2, 5, [self.team_members["devops_lead"]], ["sms", "phone"]),
                    EscalationStep(3, 15, [self.team_members["engineering_manager"]], ["phone", "email"])
                ]
            ),
            
            # Security Issues
            EscalationPolicy(
                name="Security Incidents",
                component=Component.API,  # Security spans all components
                severity=Severity.CRITICAL,
                steps=[
                    EscalationStep(1, 0, [self.team_members["security_engineer"]], ["sms", "phone"]),
                    EscalationStep(2, 2, [self.team_members["devops_lead"]], ["sms", "phone"]),
                    EscalationStep(3, 5, [self.team_members["engineering_manager"]], ["phone", "email"]),
                    EscalationStep(4, 10, [self.team_members["cto"]], ["phone", "email"])
                ]
            )
        ]
    
    def create_pagerduty_policy(self, policy: EscalationPolicy) -> Dict:
        """Create a PagerDuty escalation policy via API"""
        
        escalation_rules = []
        for step in policy.steps:
            rule = {
                "escalation_delay_in_minutes": step.delay_minutes,
                "targets": [
                    {
                        "id": target_id,
                        "type": "user_reference" if target_id.startswith("P") else "schedule_reference"
                    }
                    for target_id in step.targets
                ]
            }
            escalation_rules.append(rule)
        
        policy_data = {
            "escalation_policy": {
                "type": "escalation_policy",
                "name": f"Financial Planning - {policy.name}",
                "description": f"Escalation policy for {policy.component.value} {policy.severity.value} issues",
                "escalation_rules": escalation_rules,
                "services": [],  # Will be populated when services are created
                "teams": []      # Will be populated with team assignments
            }
        }
        
        headers = {
            "Authorization": f"Token token={self.api_token}",
            "Content-Type": "application/json",
            "Accept": "application/vnd.pagerduty+json;version=2"
        }
        
        response = requests.post(
            f"{self.base_url}/escalation_policies",
            headers=headers,
            data=json.dumps(policy_data)
        )
        
        return response.json()
    
    def create_incident_workflow(self, component: Component, severity: Severity) -> Dict:
        """Create automated incident response workflow"""
        
        workflows = {
            Component.MONTE_CARLO: {
                "actions": [
                    "Check simulation queue health",
                    "Verify GPU/CPU resources",
                    "Review recent simulation parameters",
                    "Check for memory leaks",
                    "Restart simulation workers if needed"
                ],
                "runbook_url": "https://runbooks.your-domain.com/simulation-issues"
            },
            Component.MARKET_DATA: {
                "actions": [
                    "Check API provider status",
                    "Verify data freshness",
                    "Review rate limiting",
                    "Check cache hit rates",
                    "Failover to backup provider if needed"
                ],
                "runbook_url": "https://runbooks.your-domain.com/market-data-issues"
            },
            Component.DATABASE: {
                "actions": [
                    "Check connection pool status",
                    "Review slow queries",
                    "Check disk space",
                    "Review replication lag",
                    "Consider read replica failover"
                ],
                "runbook_url": "https://runbooks.your-domain.com/database-issues"
            }
        }
        
        return workflows.get(component, {
            "actions": ["Check system health", "Review logs", "Escalate to engineering"],
            "runbook_url": "https://runbooks.your-domain.com/general-troubleshooting"
        })
    
    def setup_business_hours_policies(self):
        """Setup different escalation behavior for business hours vs after hours"""
        
        business_hours_config = {
            "timezone": "America/New_York",
            "business_days": ["monday", "tuesday", "wednesday", "thursday", "friday"],
            "start_time": "09:00",
            "end_time": "17:00"
        }
        
        after_hours_overrides = {
            Component.MARKET_DATA: {
                "severity_adjustment": "downgrade",  # Lower severity after market close
                "delay_multiplier": 2  # Double the escalation delays
            },
            Component.AI_RECOMMENDATIONS: {
                "severity_adjustment": "downgrade",
                "delay_multiplier": 3
            }
        }
        
        return business_hours_config, after_hours_overrides

def setup_pagerduty_integration():
    """Main function to setup PagerDuty integration"""
    
    api_token = os.getenv("PAGERDUTY_API_TOKEN")
    if not api_token:
        raise ValueError("PAGERDUTY_API_TOKEN environment variable is required")
    
    escalations = FinancialPlanningEscalations(api_token)
    policies = escalations.get_escalation_policies()
    
    created_policies = []
    for policy in policies:
        try:
            result = escalations.create_pagerduty_policy(policy)
            created_policies.append(result)
            print(f"Created escalation policy: {policy.name}")
        except Exception as e:
            print(f"Failed to create policy {policy.name}: {e}")
    
    return created_policies

if __name__ == "__main__":
    setup_pagerduty_integration()