"""
Crisis Management Coaching System

Provides emergency financial guidance, debt reduction strategies,
market downturn advice, and stress management techniques.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import json
from dataclasses import dataclass, field
import uuid

import numpy as np
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.database.base import SessionLocal
from app.models.user import User
from app.models.financial_profile import FinancialProfile
from app.ai.llm_client import LLMClientManager
from app.services.notifications.manager import NotificationManager

logger = logging.getLogger(__name__)


class CrisisType(str, Enum):
    """Types of financial crises."""
    JOB_LOSS = "job_loss"
    MEDICAL_EMERGENCY = "medical_emergency"
    INCOME_REDUCTION = "income_reduction"
    UNEXPECTED_EXPENSE = "unexpected_expense"
    DEBT_OVERWHELM = "debt_overwhelm"
    MARKET_CRASH = "market_crash"
    HOUSING_CRISIS = "housing_crisis"
    FAMILY_EMERGENCY = "family_emergency"
    NATURAL_DISASTER = "natural_disaster"
    RELATIONSHIP_CHANGE = "relationship_change"  # Divorce, separation
    BUSINESS_FAILURE = "business_failure"
    LEGAL_ISSUE = "legal_issue"


class CrisisSeverity(str, Enum):
    """Severity levels of crisis."""
    MILD = "mild"  # Can be managed with adjustments
    MODERATE = "moderate"  # Requires significant changes
    SEVERE = "severe"  # Requires immediate action
    CRITICAL = "critical"  # Emergency intervention needed


class ActionPriority(str, Enum):
    """Priority levels for crisis actions."""
    IMMEDIATE = "immediate"  # Do today
    URGENT = "urgent"  # Within 3 days
    HIGH = "high"  # Within 1 week
    MEDIUM = "medium"  # Within 2 weeks
    LOW = "low"  # Within 1 month


@dataclass
class CrisisAction:
    """Represents a crisis management action."""
    action_id: str
    title: str
    description: str
    priority: ActionPriority
    category: str  # income, expense, debt, asset, support
    estimated_impact: float  # Financial impact in dollars
    time_required: str  # Time to complete
    resources_needed: List[str]
    dependencies: List[str]  # Other actions that must be completed first
    deadline: Optional[datetime]
    completed: bool = False
    completion_date: Optional[datetime] = None
    notes: str = ""


@dataclass
class CrisisResponse:
    """Complete crisis response plan."""
    crisis_id: str
    user_id: str
    crisis_type: CrisisType
    severity: CrisisSeverity
    assessment: Dict[str, Any]
    immediate_actions: List[CrisisAction]
    short_term_plan: Dict[str, Any]  # 1-4 weeks
    medium_term_plan: Dict[str, Any]  # 1-3 months
    long_term_recovery: Dict[str, Any]  # 3-12 months
    resources: List[Dict[str, str]]
    support_contacts: List[Dict[str, str]]
    stress_management: List[str]
    monitoring_metrics: Dict[str, Any]
    created_at: datetime
    last_updated: datetime


class EmergencyFundCalculator(BaseModel):
    """Emergency fund requirement calculator."""
    essential_expenses: float
    months_coverage: int
    current_savings: float
    target_amount: float
    monthly_contribution_needed: float
    time_to_goal: int  # months
    priority_expenses: List[Dict[str, float]]


class DebtReductionStrategy(BaseModel):
    """Debt reduction strategy model."""
    total_debt: float
    minimum_payments: float
    available_for_debt: float
    strategy_type: str  # avalanche, snowball, hybrid
    debt_priority_order: List[Dict[str, Any]]
    projected_payoff_timeline: Dict[str, Any]
    interest_savings: float
    monthly_plan: List[Dict[str, Any]]


class CrisisManagementCoach:
    """AI-powered crisis management and emergency financial coaching."""
    
    def __init__(
        self,
        llm_manager: LLMClientManager,
        notification_manager: Optional[NotificationManager] = None
    ):
        self.llm_manager = llm_manager
        self.notification_manager = notification_manager
        
        # Crisis response templates
        self.response_templates = self._initialize_response_templates()
        
        # Resource directories
        self.resource_directory = self._initialize_resource_directory()
        
        # Stress management techniques
        self.stress_techniques = self._initialize_stress_techniques()
        
        # Active crisis tracking
        self.active_crises: Dict[str, CrisisResponse] = {}
    
    async def assess_crisis(
        self,
        user_id: str,
        crisis_description: str,
        financial_data: Dict[str, Any],
        user_context: Optional[Dict[str, Any]] = None
    ) -> CrisisResponse:
        """Assess crisis and generate comprehensive response plan."""
        
        try:
            # Classify crisis type and severity
            classification = await self._classify_crisis(
                crisis_description, financial_data
            )
            
            # Perform detailed assessment
            assessment = await self._perform_crisis_assessment(
                classification, financial_data, user_context
            )
            
            # Generate immediate action plan
            immediate_actions = await self._generate_immediate_actions(
                classification, assessment, financial_data
            )
            
            # Create short-term stabilization plan
            short_term = await self._create_short_term_plan(
                classification, assessment, financial_data
            )
            
            # Develop medium-term recovery plan
            medium_term = await self._create_medium_term_plan(
                classification, assessment, financial_data
            )
            
            # Design long-term resilience plan
            long_term = await self._create_long_term_plan(
                classification, assessment, financial_data
            )
            
            # Gather relevant resources
            resources = await self._gather_crisis_resources(classification)
            
            # Identify support contacts
            support = await self._identify_support_contacts(classification)
            
            # Generate stress management plan
            stress_mgmt = await self._create_stress_management_plan(
                classification['severity'], user_context
            )
            
            # Define monitoring metrics
            metrics = self._define_monitoring_metrics(classification)
            
            # Create comprehensive response
            response = CrisisResponse(
                crisis_id=str(uuid.uuid4()),
                user_id=user_id,
                crisis_type=classification['type'],
                severity=classification['severity'],
                assessment=assessment,
                immediate_actions=immediate_actions,
                short_term_plan=short_term,
                medium_term_plan=medium_term,
                long_term_recovery=long_term,
                resources=resources,
                support_contacts=support,
                stress_management=stress_mgmt,
                monitoring_metrics=metrics,
                created_at=datetime.utcnow(),
                last_updated=datetime.utcnow()
            )
            
            # Store active crisis
            self.active_crises[response.crisis_id] = response
            
            # Schedule follow-ups if notification manager available
            if self.notification_manager:
                await self._schedule_crisis_followups(response)
            
            return response
            
        except Exception as e:
            logger.error(f"Error assessing crisis: {str(e)}")
            return self._get_emergency_fallback_response(user_id, crisis_description)
    
    async def calculate_emergency_fund(
        self,
        user_id: str,
        monthly_expenses: Dict[str, float],
        current_savings: float,
        risk_factors: Optional[Dict[str, Any]] = None
    ) -> EmergencyFundCalculator:
        """Calculate emergency fund requirements."""
        
        try:
            # Identify essential expenses
            essential = await self._identify_essential_expenses(monthly_expenses)
            
            # Determine recommended months of coverage
            months_needed = await self._calculate_coverage_months(risk_factors)
            
            # Calculate target amount
            target = essential * months_needed
            
            # Determine contribution plan
            monthly_contribution = await self._calculate_contribution_plan(
                target, current_savings, risk_factors
            )
            
            # Calculate time to goal
            if monthly_contribution > 0:
                time_to_goal = int((target - current_savings) / monthly_contribution)
            else:
                time_to_goal = 999  # Placeholder for "undefined"
            
            return EmergencyFundCalculator(
                essential_expenses=essential,
                months_coverage=months_needed,
                current_savings=current_savings,
                target_amount=target,
                monthly_contribution_needed=monthly_contribution,
                time_to_goal=time_to_goal,
                priority_expenses=[
                    {'housing': essential * 0.35},
                    {'food': essential * 0.15},
                    {'utilities': essential * 0.10},
                    {'insurance': essential * 0.10},
                    {'transportation': essential * 0.15},
                    {'healthcare': essential * 0.10},
                    {'minimum_debt_payments': essential * 0.05}
                ]
            )
            
        except Exception as e:
            logger.error(f"Error calculating emergency fund: {str(e)}")
            # Return conservative estimate
            return EmergencyFundCalculator(
                essential_expenses=sum(monthly_expenses.values()) * 0.7,
                months_coverage=6,
                current_savings=current_savings,
                target_amount=sum(monthly_expenses.values()) * 0.7 * 6,
                monthly_contribution_needed=500,
                time_to_goal=12,
                priority_expenses=[]
            )
    
    async def create_debt_reduction_plan(
        self,
        user_id: str,
        debts: List[Dict[str, Any]],
        monthly_income: float,
        monthly_expenses: float,
        strategy_preference: Optional[str] = None
    ) -> DebtReductionStrategy:
        """Create comprehensive debt reduction strategy."""
        
        try:
            # Calculate total debt and minimum payments
            total_debt = sum(d['balance'] for d in debts)
            min_payments = sum(d['minimum_payment'] for d in debts)
            
            # Determine available funds for debt payment
            available = monthly_income - monthly_expenses
            extra_payment = max(0, available - min_payments)
            
            # Choose optimal strategy
            strategy = await self._choose_debt_strategy(
                debts, extra_payment, strategy_preference
            )
            
            # Order debts by strategy
            ordered_debts = await self._order_debts_by_strategy(debts, strategy)
            
            # Calculate payoff timeline
            timeline = await self._calculate_payoff_timeline(
                ordered_debts, min_payments + extra_payment
            )
            
            # Calculate interest savings
            interest_savings = await self._calculate_interest_savings(
                debts, timeline, strategy
            )
            
            # Create monthly action plan
            monthly_plan = await self._create_monthly_debt_plan(
                ordered_debts, available, timeline
            )
            
            return DebtReductionStrategy(
                total_debt=total_debt,
                minimum_payments=min_payments,
                available_for_debt=available,
                strategy_type=strategy,
                debt_priority_order=ordered_debts,
                projected_payoff_timeline=timeline,
                interest_savings=interest_savings,
                monthly_plan=monthly_plan
            )
            
        except Exception as e:
            logger.error(f"Error creating debt reduction plan: {str(e)}")
            return self._get_fallback_debt_strategy(debts, monthly_income, monthly_expenses)
    
    async def handle_market_downturn(
        self,
        user_id: str,
        portfolio: Dict[str, Any],
        risk_tolerance: str,
        time_horizon: int,  # years
        market_conditions: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Provide guidance during market downturns."""
        
        try:
            # Assess portfolio impact
            impact = await self._assess_portfolio_impact(
                portfolio, market_conditions
            )
            
            # Generate personalized advice
            advice = await self._generate_market_advice(
                impact, risk_tolerance, time_horizon, market_conditions
            )
            
            # Suggest rebalancing opportunities
            rebalancing = await self._suggest_rebalancing(
                portfolio, risk_tolerance, market_conditions
            )
            
            # Identify tax-loss harvesting opportunities
            tax_opportunities = await self._identify_tax_opportunities(
                portfolio, market_conditions
            )
            
            # Create action plan
            action_plan = await self._create_market_action_plan(
                advice, rebalancing, tax_opportunities, time_horizon
            )
            
            # Provide psychological support
            psychological = await self._provide_market_psychology_support(
                impact['percentage_decline'], time_horizon
            )
            
            return {
                'portfolio_impact': impact,
                'personalized_advice': advice,
                'rebalancing_opportunities': rebalancing,
                'tax_loss_harvesting': tax_opportunities,
                'action_plan': action_plan,
                'psychological_support': psychological,
                'historical_context': await self._provide_historical_context(),
                'monitoring_plan': self._create_monitoring_plan(market_conditions)
            }
            
        except Exception as e:
            logger.error(f"Error handling market downturn: {str(e)}")
            return self._get_fallback_market_guidance()
    
    async def provide_stress_management(
        self,
        user_id: str,
        stress_level: float,  # 0-1
        crisis_type: Optional[CrisisType] = None,
        preferences: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Provide financial stress management techniques."""
        
        try:
            # Select appropriate techniques based on stress level
            techniques = await self._select_stress_techniques(
                stress_level, crisis_type, preferences
            )
            
            # Generate daily stress management plan
            daily_plan = await self._create_daily_stress_plan(
                techniques, stress_level
            )
            
            # Provide coping strategies
            coping = await self._generate_coping_strategies(
                crisis_type, stress_level
            )
            
            # Create support network plan
            support = await self._create_support_network_plan(crisis_type)
            
            # Generate motivational content
            motivation = await self._generate_motivation(stress_level, crisis_type)
            
            return {
                'stress_level_assessment': self._assess_stress_level(stress_level),
                'recommended_techniques': techniques,
                'daily_plan': daily_plan,
                'coping_strategies': coping,
                'support_network': support,
                'motivational_message': motivation,
                'resources': self._get_stress_resources(),
                'progress_tracking': self._create_stress_tracking_plan()
            }
            
        except Exception as e:
            logger.error(f"Error providing stress management: {str(e)}")
            return self._get_fallback_stress_management()
    
    async def _classify_crisis(
        self,
        description: str,
        financial_data: Dict
    ) -> Dict[str, Any]:
        """Classify crisis type and severity using AI."""
        
        prompt = f"""
        Analyze this financial crisis:
        
        Description: {description}
        
        Financial Data:
        - Monthly Income: ${financial_data.get('income', 0):,.0f}
        - Monthly Expenses: ${financial_data.get('expenses', 0):,.0f}
        - Savings: ${financial_data.get('savings', 0):,.0f}
        - Debt: ${financial_data.get('debt', 0):,.0f}
        
        Classify:
        1. Crisis Type (job_loss, medical_emergency, debt_overwhelm, etc.)
        2. Severity (mild, moderate, severe, critical)
        3. Urgency Level (1-10)
        4. Primary Impact Areas
        5. Risk of escalation
        """
        
        try:
            response = await self.llm_manager.generate(
                prompt=prompt,
                temperature=0.3,
                max_tokens=500
            )
            
            # Parse response (simplified)
            return {
                'type': CrisisType.UNEXPECTED_EXPENSE,
                'severity': CrisisSeverity.MODERATE,
                'urgency': 7,
                'impact_areas': ['cash_flow', 'savings', 'stress'],
                'escalation_risk': 0.6
            }
        except:
            return {
                'type': CrisisType.UNEXPECTED_EXPENSE,
                'severity': CrisisSeverity.MODERATE,
                'urgency': 5,
                'impact_areas': ['general'],
                'escalation_risk': 0.5
            }
    
    async def _perform_crisis_assessment(
        self,
        classification: Dict,
        financial_data: Dict,
        user_context: Optional[Dict]
    ) -> Dict[str, Any]:
        """Perform detailed crisis assessment."""
        
        income = financial_data.get('income', 0)
        expenses = financial_data.get('expenses', 0)
        savings = financial_data.get('savings', 0)
        debt = financial_data.get('debt', 0)
        
        # Calculate key metrics
        runway = savings / expenses if expenses > 0 else 0
        debt_to_income = debt / (income * 12) if income > 0 else 999
        savings_rate = (income - expenses) / income if income > 0 else 0
        
        return {
            'financial_runway_months': runway,
            'debt_to_income_ratio': debt_to_income,
            'current_savings_rate': savings_rate,
            'emergency_fund_adequacy': savings / (expenses * 6),  # vs 6-month target
            'cash_flow_status': 'positive' if income > expenses else 'negative',
            'immediate_risks': self._identify_immediate_risks(classification, financial_data),
            'available_resources': self._identify_available_resources(financial_data),
            'time_sensitivity': classification['urgency'],
            'support_needed': self._determine_support_needs(classification, user_context)
        }
    
    async def _generate_immediate_actions(
        self,
        classification: Dict,
        assessment: Dict,
        financial_data: Dict
    ) -> List[CrisisAction]:
        """Generate immediate crisis actions."""
        
        actions = []
        
        # Universal immediate actions
        actions.append(CrisisAction(
            action_id=str(uuid.uuid4()),
            title="Document all expenses",
            description="Track every expense for the next 7 days to understand cash flow",
            priority=ActionPriority.IMMEDIATE,
            category="expense",
            estimated_impact=0,
            time_required="15 minutes daily",
            resources_needed=["Expense tracking app or spreadsheet"],
            dependencies=[],
            deadline=datetime.utcnow() + timedelta(days=1)
        ))
        
        # Crisis-specific actions
        if classification['type'] == CrisisType.JOB_LOSS:
            actions.extend([
                CrisisAction(
                    action_id=str(uuid.uuid4()),
                    title="File for unemployment benefits",
                    description="Apply for unemployment insurance immediately",
                    priority=ActionPriority.IMMEDIATE,
                    category="income",
                    estimated_impact=financial_data.get('income', 0) * 0.5,
                    time_required="2 hours",
                    resources_needed=["Previous pay stubs", "ID", "Work history"],
                    dependencies=[],
                    deadline=datetime.utcnow() + timedelta(days=1)
                ),
                CrisisAction(
                    action_id=str(uuid.uuid4()),
                    title="Review and reduce subscriptions",
                    description="Cancel all non-essential subscriptions and services",
                    priority=ActionPriority.URGENT,
                    category="expense",
                    estimated_impact=200,
                    time_required="1 hour",
                    resources_needed=["List of subscriptions", "Account logins"],
                    dependencies=[],
                    deadline=datetime.utcnow() + timedelta(days=3)
                )
            ])
        
        elif classification['type'] == CrisisType.MEDICAL_EMERGENCY:
            actions.extend([
                CrisisAction(
                    action_id=str(uuid.uuid4()),
                    title="Contact insurance provider",
                    description="Understand coverage and out-of-pocket maximums",
                    priority=ActionPriority.IMMEDIATE,
                    category="expense",
                    estimated_impact=0,
                    time_required="1 hour",
                    resources_needed=["Insurance card", "Medical records"],
                    dependencies=[],
                    deadline=datetime.utcnow() + timedelta(days=1)
                ),
                CrisisAction(
                    action_id=str(uuid.uuid4()),
                    title="Request payment plan",
                    description="Negotiate payment plans with medical providers",
                    priority=ActionPriority.URGENT,
                    category="debt",
                    estimated_impact=0,
                    time_required="30 minutes per provider",
                    resources_needed=["Medical bills", "Income documentation"],
                    dependencies=["Contact insurance provider"],
                    deadline=datetime.utcnow() + timedelta(days=7)
                )
            ])
        
        return actions[:5]  # Return top 5 immediate actions
    
    async def _create_short_term_plan(
        self,
        classification: Dict,
        assessment: Dict,
        financial_data: Dict
    ) -> Dict[str, Any]:
        """Create 1-4 week stabilization plan."""
        
        return {
            'week_1': {
                'focus': 'Immediate stabilization',
                'actions': [
                    'Complete expense audit',
                    'Secure emergency income sources',
                    'Negotiate payment deferrals'
                ],
                'target_savings': 500
            },
            'week_2': {
                'focus': 'Expense optimization',
                'actions': [
                    'Implement strict budget',
                    'Reduce discretionary spending by 50%',
                    'Explore side income opportunities'
                ],
                'target_savings': 750
            },
            'week_3_4': {
                'focus': 'Income replacement',
                'actions': [
                    'Apply for relevant positions',
                    'Start freelance/gig work',
                    'Liquidate non-essential assets'
                ],
                'target_income': 2000
            },
            'success_metrics': {
                'expense_reduction': 0.30,  # 30% reduction target
                'income_replacement': 0.50,  # 50% income replacement
                'stress_reduction': 'daily_practice'
            }
        }
    
    async def _create_medium_term_plan(
        self,
        classification: Dict,
        assessment: Dict,
        financial_data: Dict
    ) -> Dict[str, Any]:
        """Create 1-3 month recovery plan."""
        
        return {
            'month_1': {
                'goals': ['Stabilize cash flow', 'Build mini emergency fund'],
                'financial_targets': {
                    'emergency_savings': 1000,
                    'expense_reduction': 0.25,
                    'income_sources': 2
                },
                'key_actions': [
                    'Establish new income stream',
                    'Refinance high-interest debt',
                    'Apply for assistance programs'
                ]
            },
            'month_2': {
                'goals': ['Increase income', 'Optimize expenses further'],
                'financial_targets': {
                    'emergency_savings': 2000,
                    'debt_reduction': 0.10,
                    'income_increase': 0.30
                },
                'key_actions': [
                    'Expand income opportunities',
                    'Negotiate bills and contracts',
                    'Build support network'
                ]
            },
            'month_3': {
                'goals': ['Establish new normal', 'Begin recovery'],
                'financial_targets': {
                    'emergency_savings': 3000,
                    'stable_income': True,
                    'budget_adherence': 0.90
                },
                'key_actions': [
                    'Solidify income sources',
                    'Review and adjust budget',
                    'Plan for long-term recovery'
                ]
            }
        }
    
    async def _create_long_term_plan(
        self,
        classification: Dict,
        assessment: Dict,
        financial_data: Dict
    ) -> Dict[str, Any]:
        """Create 3-12 month resilience plan."""
        
        return {
            'quarter_1': {
                'focus': 'Rebuild foundation',
                'goals': [
                    'Restore income to pre-crisis level',
                    'Build 3-month emergency fund',
                    'Establish sustainable budget'
                ]
            },
            'quarter_2': {
                'focus': 'Strengthen position',
                'goals': [
                    'Increase emergency fund to 6 months',
                    'Resume retirement contributions',
                    'Address deferred maintenance'
                ]
            },
            'quarter_3_4': {
                'focus': 'Build resilience',
                'goals': [
                    'Diversify income sources',
                    'Increase insurance coverage',
                    'Create crisis prevention plan'
                ]
            },
            'resilience_building': {
                'financial_buffers': ['Emergency fund', 'Credit line', 'Liquid assets'],
                'skill_development': ['New certifications', 'Side business', 'Network building'],
                'risk_mitigation': ['Insurance review', 'Legal protections', 'Estate planning']
            }
        }
    
    async def _gather_crisis_resources(self, classification: Dict) -> List[Dict[str, str]]:
        """Gather relevant crisis resources."""
        
        resources = []
        
        # Universal resources
        resources.extend([
            {
                'name': '211 Helpline',
                'description': 'Connect to local assistance programs',
                'url': 'https://www.211.org',
                'phone': '211'
            },
            {
                'name': 'National Foundation for Credit Counseling',
                'description': 'Free credit counseling and debt management',
                'url': 'https://www.nfcc.org',
                'phone': '1-800-388-2227'
            }
        ])
        
        # Crisis-specific resources
        if classification['type'] == CrisisType.JOB_LOSS:
            resources.extend([
                {
                    'name': 'Unemployment Insurance',
                    'description': 'State unemployment benefits',
                    'url': 'https://www.usa.gov/unemployment',
                    'phone': 'Varies by state'
                },
                {
                    'name': 'SNAP Benefits',
                    'description': 'Food assistance program',
                    'url': 'https://www.fns.usda.gov/snap',
                    'phone': 'Local office'
                }
            ])
        
        return resources
    
    async def _identify_support_contacts(self, classification: Dict) -> List[Dict[str, str]]:
        """Identify relevant support contacts."""
        
        contacts = [
            {
                'type': 'Financial Counselor',
                'description': 'Professional financial guidance',
                'how_to_find': 'NFCC.org or local credit union'
            },
            {
                'type': 'Legal Aid',
                'description': 'Free legal assistance for qualifying individuals',
                'how_to_find': 'LegalAid.org or local bar association'
            }
        ]
        
        if classification['type'] == CrisisType.MEDICAL_EMERGENCY:
            contacts.append({
                'type': 'Patient Advocate',
                'description': 'Help navigating medical billing',
                'how_to_find': 'Hospital social services department'
            })
        
        return contacts
    
    async def _create_stress_management_plan(
        self,
        severity: CrisisSeverity,
        user_context: Optional[Dict]
    ) -> List[str]:
        """Create stress management techniques."""
        
        techniques = [
            "Practice 5-minute daily meditation using free apps",
            "Maintain regular sleep schedule (7-8 hours)",
            "Take 10-minute walks outdoors daily",
            "Connect with support network weekly",
            "Journal financial wins and progress daily"
        ]
        
        if severity in [CrisisSeverity.SEVERE, CrisisSeverity.CRITICAL]:
            techniques.extend([
                "Consider professional counseling (many offer sliding scale fees)",
                "Join online support groups for financial stress",
                "Practice box breathing when feeling overwhelmed"
            ])
        
        return techniques
    
    def _define_monitoring_metrics(self, classification: Dict) -> Dict[str, Any]:
        """Define metrics to monitor during crisis."""
        
        return {
            'daily': ['Cash balance', 'Expenses', 'Stress level (1-10)'],
            'weekly': ['Income sources', 'Bill payments', 'Progress on action items'],
            'monthly': ['Net worth', 'Debt levels', 'Emergency fund', 'Recovery progress'],
            'triggers': {
                'cash_below_500': 'Activate emergency measures',
                'missed_payment': 'Contact creditor immediately',
                'stress_above_8': 'Seek additional support'
            }
        }
    
    async def _schedule_crisis_followups(self, response: CrisisResponse) -> None:
        """Schedule follow-up notifications for crisis management."""
        
        if not self.notification_manager:
            return
        
        # Daily check-in for first week
        for day in range(1, 8):
            await self.notification_manager.schedule_notification(
                user_id=response.user_id,
                notification_type='crisis_checkin',
                content={
                    'crisis_id': response.crisis_id,
                    'day': day,
                    'message': f"Day {day} crisis check-in: Review your action items"
                },
                scheduled_time=datetime.utcnow() + timedelta(days=day, hours=9)
            )
        
        # Weekly check-in for first month
        for week in range(2, 5):
            await self.notification_manager.schedule_notification(
                user_id=response.user_id,
                notification_type='crisis_progress',
                content={
                    'crisis_id': response.crisis_id,
                    'week': week,
                    'message': f"Week {week} progress review"
                },
                scheduled_time=datetime.utcnow() + timedelta(weeks=week)
            )
    
    def _get_emergency_fallback_response(
        self,
        user_id: str,
        description: str
    ) -> CrisisResponse:
        """Get emergency fallback response when AI fails."""
        
        return CrisisResponse(
            crisis_id=str(uuid.uuid4()),
            user_id=user_id,
            crisis_type=CrisisType.UNEXPECTED_EXPENSE,
            severity=CrisisSeverity.MODERATE,
            assessment={'status': 'Manual assessment needed'},
            immediate_actions=[
                CrisisAction(
                    action_id=str(uuid.uuid4()),
                    title="Contact financial counselor",
                    description="Reach out to NFCC for free counseling",
                    priority=ActionPriority.IMMEDIATE,
                    category="support",
                    estimated_impact=0,
                    time_required="1 hour",
                    resources_needed=["Phone", "Financial documents"],
                    dependencies=[],
                    deadline=datetime.utcnow() + timedelta(days=1)
                )
            ],
            short_term_plan={'focus': 'Stabilize situation'},
            medium_term_plan={'focus': 'Build recovery'},
            long_term_recovery={'focus': 'Prevent future crises'},
            resources=[],
            support_contacts=[],
            stress_management=["Seek professional help", "Call 211 for resources"],
            monitoring_metrics={},
            created_at=datetime.utcnow(),
            last_updated=datetime.utcnow()
        )
    
    async def _identify_essential_expenses(
        self,
        monthly_expenses: Dict[str, float]
    ) -> float:
        """Identify essential expenses for emergency fund calculation."""
        
        essential_categories = [
            'housing', 'rent', 'mortgage',
            'utilities', 'electricity', 'water', 'gas',
            'food', 'groceries',
            'transportation', 'gas', 'public_transport',
            'insurance', 'health', 'medical',
            'minimum_payments', 'debt'
        ]
        
        essential_total = 0
        for category, amount in monthly_expenses.items():
            if any(essential in category.lower() for essential in essential_categories):
                essential_total += amount
        
        # If no categorization, assume 70% of expenses are essential
        if essential_total == 0:
            essential_total = sum(monthly_expenses.values()) * 0.7
        
        return essential_total
    
    async def _calculate_coverage_months(
        self,
        risk_factors: Optional[Dict]
    ) -> int:
        """Calculate recommended months of emergency fund coverage."""
        
        base_months = 3
        
        if risk_factors:
            # Adjust based on risk factors
            if risk_factors.get('job_stability', 'stable') == 'unstable':
                base_months += 3
            if risk_factors.get('health_issues', False):
                base_months += 2
            if risk_factors.get('dependents', 0) > 0:
                base_months += 1
            if risk_factors.get('single_income', False):
                base_months += 2
        
        return min(12, base_months)  # Cap at 12 months
    
    async def _calculate_contribution_plan(
        self,
        target: float,
        current: float,
        risk_factors: Optional[Dict]
    ) -> float:
        """Calculate monthly contribution needed for emergency fund."""
        
        gap = target - current
        
        if gap <= 0:
            return 0
        
        # Determine urgency based on risk
        if risk_factors and risk_factors.get('immediate_risk', False):
            months_to_save = 6
        else:
            months_to_save = 12
        
        return gap / months_to_save
    
    def _identify_immediate_risks(
        self,
        classification: Dict,
        financial_data: Dict
    ) -> List[str]:
        """Identify immediate financial risks."""
        
        risks = []
        
        if financial_data.get('savings', 0) < financial_data.get('expenses', 1) * 1:
            risks.append("Less than 1 month emergency fund")
        
        if financial_data.get('income', 0) < financial_data.get('expenses', 0):
            risks.append("Negative cash flow")
        
        if financial_data.get('debt', 0) > financial_data.get('income', 1) * 12 * 0.4:
            risks.append("High debt-to-income ratio")
        
        return risks
    
    def _identify_available_resources(self, financial_data: Dict) -> Dict[str, Any]:
        """Identify available financial resources."""
        
        return {
            'liquid_savings': financial_data.get('savings', 0),
            'available_credit': financial_data.get('available_credit', 0),
            'sellable_assets': financial_data.get('assets', []),
            'potential_income': financial_data.get('potential_income', [])
        }
    
    def _determine_support_needs(
        self,
        classification: Dict,
        user_context: Optional[Dict]
    ) -> List[str]:
        """Determine what support is needed."""
        
        needs = []
        
        if classification['severity'] in [CrisisSeverity.SEVERE, CrisisSeverity.CRITICAL]:
            needs.append("Professional financial counseling")
        
        if classification['type'] in [CrisisType.LEGAL_ISSUE, CrisisType.RELATIONSHIP_CHANGE]:
            needs.append("Legal consultation")
        
        if user_context and user_context.get('stress_level', 0) > 0.7:
            needs.append("Mental health support")
        
        return needs
    
    async def _choose_debt_strategy(
        self,
        debts: List[Dict],
        extra_payment: float,
        preference: Optional[str]
    ) -> str:
        """Choose optimal debt reduction strategy."""
        
        if preference:
            return preference
        
        # Analyze debts to recommend strategy
        high_interest_debt = sum(d['balance'] for d in debts if d.get('interest_rate', 0) > 0.20)
        small_debts = sum(1 for d in debts if d['balance'] < 1000)
        
        if high_interest_debt > sum(d['balance'] for d in debts) * 0.5:
            return 'avalanche'  # Focus on high interest first
        elif small_debts >= len(debts) * 0.5:
            return 'snowball'  # Quick wins for motivation
        else:
            return 'hybrid'  # Combination approach
    
    async def _order_debts_by_strategy(
        self,
        debts: List[Dict],
        strategy: str
    ) -> List[Dict]:
        """Order debts according to chosen strategy."""
        
        if strategy == 'avalanche':
            # Highest interest rate first
            return sorted(debts, key=lambda d: d.get('interest_rate', 0), reverse=True)
        elif strategy == 'snowball':
            # Smallest balance first
            return sorted(debts, key=lambda d: d['balance'])
        else:  # hybrid
            # Small debts first, then by interest rate
            small = [d for d in debts if d['balance'] < 1000]
            large = [d for d in debts if d['balance'] >= 1000]
            return sorted(small, key=lambda d: d['balance']) + \
                   sorted(large, key=lambda d: d.get('interest_rate', 0), reverse=True)
    
    async def _calculate_payoff_timeline(
        self,
        ordered_debts: List[Dict],
        total_payment: float
    ) -> Dict[str, Any]:
        """Calculate debt payoff timeline."""
        
        timeline = {}
        remaining_payment = total_payment
        months_elapsed = 0
        
        for debt in ordered_debts:
            balance = debt['balance']
            min_payment = debt['minimum_payment']
            interest_rate = debt.get('interest_rate', 0) / 12  # Monthly rate
            
            # Simple calculation (would be more complex in production)
            if remaining_payment > min_payment:
                extra = remaining_payment - min_payment
                months_to_pay = balance / (min_payment + extra) if (min_payment + extra) > 0 else 999
            else:
                months_to_pay = 999
            
            months_elapsed += int(months_to_pay)
            timeline[debt.get('name', 'Debt')] = {
                'payoff_month': months_elapsed,
                'total_interest': balance * interest_rate * months_to_pay
            }
        
        return timeline
    
    async def _calculate_interest_savings(
        self,
        debts: List[Dict],
        timeline: Dict,
        strategy: str
    ) -> float:
        """Calculate interest savings from debt strategy."""
        
        # Simplified calculation
        total_interest_with_strategy = sum(
            debt_info.get('total_interest', 0)
            for debt_info in timeline.values()
        )
        
        # Calculate baseline (minimum payments only)
        baseline_interest = sum(
            debt['balance'] * debt.get('interest_rate', 0) * 2  # Assume 2 years average
            for debt in debts
        )
        
        return max(0, baseline_interest - total_interest_with_strategy)
    
    async def _create_monthly_debt_plan(
        self,
        ordered_debts: List[Dict],
        available: float,
        timeline: Dict
    ) -> List[Dict]:
        """Create month-by-month debt payment plan."""
        
        plan = []
        
        for month in range(1, 13):  # First 12 months
            month_plan = {
                'month': month,
                'payments': [],
                'total_payment': 0,
                'progress': {}
            }
            
            for debt in ordered_debts:
                payment = debt['minimum_payment']
                if month <= 3 and debt == ordered_debts[0]:  # Focus debt
                    payment += available * 0.5  # Add extra to focus debt
                
                month_plan['payments'].append({
                    'debt': debt.get('name', 'Debt'),
                    'payment': payment
                })
                month_plan['total_payment'] += payment
            
            plan.append(month_plan)
        
        return plan
    
    def _get_fallback_debt_strategy(
        self,
        debts: List[Dict],
        income: float,
        expenses: float
    ) -> DebtReductionStrategy:
        """Fallback debt strategy when AI fails."""
        
        return DebtReductionStrategy(
            total_debt=sum(d['balance'] for d in debts),
            minimum_payments=sum(d['minimum_payment'] for d in debts),
            available_for_debt=max(0, income - expenses),
            strategy_type='avalanche',
            debt_priority_order=debts,
            projected_payoff_timeline={'estimated': '24-36 months'},
            interest_savings=0,
            monthly_plan=[]
        )
    
    async def _assess_portfolio_impact(
        self,
        portfolio: Dict,
        market_conditions: Dict
    ) -> Dict[str, Any]:
        """Assess impact of market downturn on portfolio."""
        
        total_value = portfolio.get('total_value', 0)
        previous_value = portfolio.get('previous_value', total_value * 1.2)
        
        return {
            'current_value': total_value,
            'loss_amount': previous_value - total_value,
            'percentage_decline': (previous_value - total_value) / previous_value if previous_value > 0 else 0,
            'affected_assets': ['stocks', 'bonds'],
            'recovery_timeframe': '6-18 months historically'
        }
    
    async def _generate_market_advice(
        self,
        impact: Dict,
        risk_tolerance: str,
        time_horizon: int,
        market_conditions: Dict
    ) -> List[str]:
        """Generate personalized market downturn advice."""
        
        advice = []
        
        if time_horizon > 10:
            advice.append("Stay the course - you have time to recover")
            advice.append("Consider this a buying opportunity if you have cash")
        elif time_horizon > 5:
            advice.append("Review asset allocation but avoid panic selling")
            advice.append("Consider gradual rebalancing over time")
        else:
            advice.append("Reassess risk tolerance and timeline")
            advice.append("Consider speaking with a financial advisor")
        
        if risk_tolerance == 'conservative':
            advice.append("Review if current allocation matches risk tolerance")
        
        return advice
    
    async def _suggest_rebalancing(
        self,
        portfolio: Dict,
        risk_tolerance: str,
        market_conditions: Dict
    ) -> Dict[str, Any]:
        """Suggest portfolio rebalancing opportunities."""
        
        return {
            'rebalancing_needed': True,
            'current_allocation': portfolio.get('allocation', {}),
            'target_allocation': {
                'stocks': 0.6 if risk_tolerance == 'aggressive' else 0.4,
                'bonds': 0.3 if risk_tolerance == 'aggressive' else 0.5,
                'cash': 0.1
            },
            'actions': [
                "Rebalance using new contributions",
                "Set rebalancing bands (5% deviation triggers)",
                "Use tax-advantaged accounts for rebalancing"
            ]
        }
    
    async def _identify_tax_opportunities(
        self,
        portfolio: Dict,
        market_conditions: Dict
    ) -> Dict[str, Any]:
        """Identify tax-loss harvesting opportunities."""
        
        return {
            'harvesting_available': True,
            'potential_losses': portfolio.get('unrealized_losses', 0),
            'tax_savings_estimate': portfolio.get('unrealized_losses', 0) * 0.25,
            'replacement_securities': ['Similar ETFs', 'Index funds'],
            'wash_sale_warning': 'Avoid repurchasing same security for 31 days'
        }
    
    async def _create_market_action_plan(
        self,
        advice: List[str],
        rebalancing: Dict,
        tax_opportunities: Dict,
        time_horizon: int
    ) -> List[Dict]:
        """Create action plan for market downturn."""
        
        actions = []
        
        if time_horizon > 5:
            actions.append({
                'action': 'Continue regular contributions',
                'timing': 'Ongoing',
                'benefit': 'Dollar-cost averaging'
            })
        
        if rebalancing['rebalancing_needed']:
            actions.append({
                'action': 'Rebalance portfolio',
                'timing': 'Within 30 days',
                'benefit': 'Maintain target allocation'
            })
        
        if tax_opportunities['harvesting_available']:
            actions.append({
                'action': 'Harvest tax losses',
                'timing': 'Before year-end',
                'benefit': f"Save ${tax_opportunities['tax_savings_estimate']:.0f} in taxes"
            })
        
        return actions
    
    async def _provide_market_psychology_support(
        self,
        decline_percentage: float,
        time_horizon: int
    ) -> Dict[str, Any]:
        """Provide psychological support during market downturns."""
        
        return {
            'key_reminders': [
                "Market downturns are normal and temporary",
                "Losses aren't real until you sell",
                f"You have {time_horizon} years to recover",
                "Focus on long-term goals, not daily fluctuations"
            ],
            'historical_perspective': "Markets have recovered from every downturn in history",
            'coping_strategies': [
                "Limit checking portfolio to once per month",
                "Focus on what you can control (savings rate, expenses)",
                "Remember why you invested originally"
            ],
            'positive_framing': "This is an opportunity to buy quality assets at lower prices"
        }
    
    async def _provide_historical_context(self) -> Dict[str, Any]:
        """Provide historical market context."""
        
        return {
            'past_recoveries': {
                '2008 Financial Crisis': 'Full recovery in 5.5 years',
                '2020 COVID Crash': 'Full recovery in 6 months',
                'Dot-com Bubble': 'Full recovery in 7 years'
            },
            'average_bear_market': {
                'duration': '14 months',
                'decline': '-33%',
                'recovery_time': '25 months'
            },
            'long_term_returns': 'S&P 500 averages 10% annually over 90+ years'
        }
    
    def _create_monitoring_plan(self, market_conditions: Dict) -> Dict[str, Any]:
        """Create plan for monitoring market conditions."""
        
        return {
            'review_frequency': 'Monthly',
            'key_indicators': [
                'Portfolio value vs target',
                'Asset allocation drift',
                'New contribution opportunities'
            ],
            'action_triggers': {
                'rebalance': 'When allocation drifts >5%',
                'increase_contributions': 'When market drops >10%',
                'review_strategy': 'Quarterly or major life change'
            }
        }
    
    def _get_fallback_market_guidance(self) -> Dict[str, Any]:
        """Fallback market guidance when AI fails."""
        
        return {
            'portfolio_impact': {'status': 'Review needed'},
            'personalized_advice': [
                "Don't panic sell",
                "Review your time horizon",
                "Consider professional advice"
            ],
            'action_plan': [
                {'action': 'Review portfolio', 'timing': 'This week'},
                {'action': 'Continue contributions', 'timing': 'Ongoing'}
            ],
            'psychological_support': {
                'key_reminders': ["This too shall pass", "Focus on long-term goals"]
            }
        }
    
    async def _select_stress_techniques(
        self,
        stress_level: float,
        crisis_type: Optional[CrisisType],
        preferences: Optional[Dict]
    ) -> List[Dict]:
        """Select appropriate stress management techniques."""
        
        techniques = []
        
        if stress_level > 0.7:
            techniques.append({
                'name': 'Emergency Breathing',
                'description': '4-7-8 breathing technique',
                'duration': '2 minutes',
                'frequency': 'As needed'
            })
        
        techniques.extend([
            {
                'name': 'Financial Journaling',
                'description': 'Write 3 financial wins daily',
                'duration': '5 minutes',
                'frequency': 'Daily'
            },
            {
                'name': 'Progress Visualization',
                'description': 'Visualize achieving financial stability',
                'duration': '10 minutes',
                'frequency': 'Daily'
            }
        ])
        
        return techniques
    
    async def _create_daily_stress_plan(
        self,
        techniques: List[Dict],
        stress_level: float
    ) -> Dict[str, List[str]]:
        """Create daily stress management plan."""
        
        return {
            'morning': [
                '5-minute meditation or breathing exercise',
                'Review one positive financial fact',
                'Set one small financial goal for the day'
            ],
            'midday': [
                'Take 10-minute walk if stressed',
                'Practice gratitude for what you have',
                'Connect with support person if needed'
            ],
            'evening': [
                'Journal the day\'s financial wins',
                'Practice progressive muscle relaxation',
                'Limit financial news consumption'
            ]
        }
    
    async def _generate_coping_strategies(
        self,
        crisis_type: Optional[CrisisType],
        stress_level: float
    ) -> List[str]:
        """Generate specific coping strategies."""
        
        strategies = [
            "Focus on what you can control, not what you can't",
            "Break large problems into small, manageable tasks",
            "Celebrate small wins and progress",
            "Maintain routine and structure",
            "Practice self-compassion - financial struggles are common"
        ]
        
        if stress_level > 0.8:
            strategies.append("Consider professional counseling support")
        
        return strategies
    
    async def _create_support_network_plan(
        self,
        crisis_type: Optional[CrisisType]
    ) -> Dict[str, Any]:
        """Create support network plan."""
        
        return {
            'immediate_circle': [
                'Trusted family member for emotional support',
                'Financial mentor or counselor',
                'Friend who has overcome similar challenge'
            ],
            'professional_support': [
                'Financial counselor (NFCC)',
                'Mental health counselor',
                'Legal aid if needed'
            ],
            'online_communities': [
                'Financial recovery forums',
                'Crisis-specific support groups',
                'Reddit personal finance community'
            ],
            'communication_plan': 'Weekly check-ins with at least one support person'
        }
    
    async def _generate_motivation(
        self,
        stress_level: float,
        crisis_type: Optional[CrisisType]
    ) -> str:
        """Generate motivational message."""
        
        messages = [
            "You've already taken the hardest step by seeking help.",
            "Every financial crisis has a solution, and you're finding yours.",
            "Your current situation is temporary, but your resilience is permanent.",
            "Small steps forward are still progress.",
            "You're stronger than you know and this challenge will prove it."
        ]
        
        return messages[min(int(stress_level * 5), 4)]
    
    def _assess_stress_level(self, stress_level: float) -> Dict[str, Any]:
        """Assess and categorize stress level."""
        
        if stress_level < 0.3:
            category = 'Low'
            description = 'Manageable stress, preventive measures recommended'
        elif stress_level < 0.6:
            category = 'Moderate'
            description = 'Elevated stress, active management needed'
        elif stress_level < 0.8:
            category = 'High'
            description = 'Significant stress, comprehensive support required'
        else:
            category = 'Critical'
            description = 'Severe stress, immediate intervention recommended'
        
        return {
            'level': stress_level,
            'category': category,
            'description': description,
            'recommended_action': 'Implement daily stress management routine'
        }
    
    def _get_stress_resources(self) -> List[Dict[str, str]]:
        """Get stress management resources."""
        
        return [
            {
                'name': 'National Suicide Prevention Lifeline',
                'phone': '988',
                'description': '24/7 crisis support'
            },
            {
                'name': 'Financial Stress Helpline',
                'phone': '1-888-388-2221',
                'description': 'Financial counseling and support'
            },
            {
                'name': 'Headspace App',
                'url': 'headspace.com',
                'description': 'Free meditation and stress relief'
            }
        ]
    
    def _create_stress_tracking_plan(self) -> Dict[str, Any]:
        """Create plan for tracking stress levels."""
        
        return {
            'daily_check': {
                'method': 'Rate stress 1-10',
                'time': 'Morning and evening',
                'trigger_action': 'If >7, use emergency techniques'
            },
            'weekly_review': {
                'assess': 'Overall stress trend',
                'adjust': 'Modify techniques as needed',
                'celebrate': 'Acknowledge improvements'
            },
            'warning_signs': [
                'Sleep disruption',
                'Appetite changes',
                'Avoiding financial tasks',
                'Isolation from support'
            ]
        }
    
    def _get_fallback_stress_management(self) -> Dict[str, Any]:
        """Fallback stress management when AI fails."""
        
        return {
            'stress_level_assessment': {'category': 'Moderate', 'action': 'Seek support'},
            'recommended_techniques': [
                {'name': 'Deep breathing', 'frequency': 'As needed'},
                {'name': 'Walk outside', 'frequency': 'Daily'}
            ],
            'resources': self._get_stress_resources(),
            'motivational_message': 'You can overcome this challenge, one step at a time.'
        }
    
    def _initialize_response_templates(self) -> Dict:
        """Initialize crisis response templates."""
        
        return {
            CrisisType.JOB_LOSS: {
                'immediate_priorities': ['File unemployment', 'Reduce expenses', 'Contact creditors'],
                'timeline': '3-6 months typical recovery',
                'key_resources': ['Unemployment office', 'Career center', 'SNAP benefits']
            },
            CrisisType.MEDICAL_EMERGENCY: {
                'immediate_priorities': ['Understand insurance coverage', 'Negotiate bills', 'Payment plans'],
                'timeline': 'Varies by condition',
                'key_resources': ['Patient advocate', 'Charity care', 'Payment assistance']
            }
        }
    
    def _initialize_resource_directory(self) -> Dict:
        """Initialize comprehensive resource directory."""
        
        return {
            'national': {
                '211': 'Local assistance programs',
                'NFCC': 'Credit counseling',
                'Legal Aid': 'Free legal help'
            },
            'financial': {
                'Credit unions': 'Emergency loans',
                'Hardship programs': 'Utility assistance',
                'Food banks': 'Food assistance'
            },
            'emotional': {
                '988': 'Crisis support',
                'NAMI': 'Mental health resources',
                'Support groups': 'Peer support'
            }
        }
    
    def _initialize_stress_techniques(self) -> Dict:
        """Initialize stress management technique library."""
        
        return {
            'breathing': {
                'box_breathing': '4-4-4-4 count technique',
                '478_breathing': '4 in, 7 hold, 8 out',
                'belly_breathing': 'Deep diaphragmatic breathing'
            },
            'mindfulness': {
                'body_scan': 'Progressive relaxation',
                'grounding': '5-4-3-2-1 sensory technique',
                'meditation': 'Guided or silent practice'
            },
            'physical': {
                'walking': 'Nature walks preferred',
                'stretching': 'Gentle yoga poses',
                'exercise': 'Releases stress hormones'
            }
        }