"""
Advanced Cash Flow Modeling System

This module implements sophisticated cash flow modeling with:
- Income projections with inflation adjustments
- Comprehensive expense tracking and categorization
- Life event modeling (retirement, college, marriage, etc.)
- Tax-aware cash flow calculations
- Dynamic scenario analysis
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, date, timedelta
import asyncio
import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class LifeEvent(Enum):
    """Types of life events that affect cash flow"""
    RETIREMENT = "retirement"
    MARRIAGE = "marriage"
    DIVORCE = "divorce"
    CHILD_BIRTH = "child_birth"
    CHILD_COLLEGE = "child_college"
    HOME_PURCHASE = "home_purchase"
    HOME_SALE = "home_sale"
    JOB_CHANGE = "job_change"
    BUSINESS_START = "business_start"
    INHERITANCE = "inheritance"
    MAJOR_MEDICAL = "major_medical"
    DISABILITY = "disability"
    DEATH = "death"

class IncomeType(Enum):
    """Types of income streams"""
    SALARY = "salary"
    BONUS = "bonus"
    COMMISSION = "commission"
    BUSINESS = "business"
    RENTAL = "rental"
    DIVIDENDS = "dividends"
    INTEREST = "interest"
    PENSION = "pension"
    SOCIAL_SECURITY = "social_security"
    ANNUITY = "annuity"
    OTHER = "other"

class ExpenseCategory(Enum):
    """Expense categories for detailed tracking"""
    HOUSING = "housing"
    TRANSPORTATION = "transportation"
    FOOD = "food"
    UTILITIES = "utilities"
    HEALTHCARE = "healthcare"
    INSURANCE = "insurance"
    EDUCATION = "education"
    CHILDCARE = "childcare"
    ENTERTAINMENT = "entertainment"
    TRAVEL = "travel"
    CLOTHING = "clothing"
    PERSONAL_CARE = "personal_care"
    DEBT_PAYMENTS = "debt_payments"
    SAVINGS = "savings"
    TAXES = "taxes"
    OTHER = "other"

@dataclass
class InflationAssumptions:
    """Inflation assumptions for different categories"""
    general: float = 0.025  # 2.5% general inflation
    housing: float = 0.03   # 3% housing inflation
    healthcare: float = 0.05  # 5% healthcare inflation
    education: float = 0.06   # 6% education inflation
    utilities: float = 0.035  # 3.5% utilities inflation

@dataclass
class IncomeStream:
    """Individual income stream definition"""
    name: str
    income_type: IncomeType
    amount: float
    start_date: date
    end_date: Optional[date] = None
    growth_rate: float = 0.03  # Annual growth rate
    inflation_adjustment: bool = True
    tax_rate: float = 0.25  # Effective tax rate
    frequency: str = "monthly"  # monthly, quarterly, annually
    seasonal_pattern: Optional[Dict[int, float]] = None  # Month -> multiplier
    volatility: float = 0.0  # Income volatility (for business income, etc.)
    
@dataclass
class ExpenseItem:
    """Individual expense item definition"""
    name: str
    category: ExpenseCategory
    amount: float
    start_date: date
    end_date: Optional[date] = None
    frequency: str = "monthly"
    inflation_category: str = "general"  # Links to InflationAssumptions
    tax_deductible: bool = False
    seasonal_pattern: Optional[Dict[int, float]] = None
    life_stage_multipliers: Optional[Dict[str, float]] = None
    
@dataclass
class LifeEventDefinition:
    """Definition of a life event and its cash flow impact"""
    event_type: LifeEvent
    event_date: date
    name: str
    description: str
    immediate_cash_impact: float = 0.0  # One-time cash impact
    ongoing_income_changes: List[IncomeStream] = field(default_factory=list)
    ongoing_expense_changes: List[ExpenseItem] = field(default_factory=list)
    asset_changes: Dict[str, float] = field(default_factory=dict)  # Asset -> value change
    tax_implications: Dict[str, float] = field(default_factory=dict)
    duration_years: Optional[float] = None
    probability: float = 1.0  # Probability of event occurring
    
@dataclass
class CashFlowProjection:
    """Cash flow projection results"""
    dates: List[date]
    gross_income: np.ndarray
    after_tax_income: np.ndarray
    total_expenses: np.ndarray
    net_cash_flow: np.ndarray
    cumulative_cash_flow: np.ndarray
    income_breakdown: Dict[IncomeType, np.ndarray]
    expense_breakdown: Dict[ExpenseCategory, np.ndarray]
    tax_breakdown: Dict[str, np.ndarray]
    life_events_impact: Dict[str, np.ndarray]
    
@dataclass
class CashFlowScenario:
    """Scenario definition for cash flow analysis"""
    name: str
    description: str
    income_multiplier: float = 1.0
    expense_multiplier: float = 1.0
    inflation_adjustment: float = 1.0
    life_events: List[LifeEventDefinition] = field(default_factory=list)
    probability: float = 1.0

class TaxCalculator:
    """Tax calculation utilities"""
    
    def __init__(self):
        # 2024 Federal tax brackets (married filing jointly)
        self.federal_brackets = [
            (22550, 0.10),
            (89450, 0.12),
            (190750, 0.22),
            (364200, 0.24),
            (462500, 0.32),
            (693750, 0.35),
            (float('inf'), 0.37)
        ]
        
        # Standard deduction
        self.standard_deduction = 29200  # 2024 married filing jointly
        
        # State tax rates by state (simplified)
        self.state_tax_rates = {
            'CA': 0.093,
            'NY': 0.0882,
            'TX': 0.0,
            'FL': 0.0,
            'WA': 0.0,
            # Add more states as needed
        }
    
    def calculate_federal_income_tax(self, taxable_income: float) -> float:
        """Calculate federal income tax"""
        if taxable_income <= 0:
            return 0
        
        tax = 0
        prev_bracket = 0
        
        for bracket_limit, rate in self.federal_brackets:
            taxable_in_bracket = min(taxable_income, bracket_limit) - prev_bracket
            if taxable_in_bracket <= 0:
                break
            
            tax += taxable_in_bracket * rate
            prev_bracket = bracket_limit
            
            if taxable_income <= bracket_limit:
                break
        
        return tax
    
    def calculate_state_tax(self, taxable_income: float, state: str = 'CA') -> float:
        """Calculate state income tax (simplified)"""
        if state not in self.state_tax_rates or taxable_income <= 0:
            return 0
        
        return taxable_income * self.state_tax_rates[state]
    
    def calculate_payroll_taxes(self, earned_income: float) -> Dict[str, float]:
        """Calculate payroll taxes"""
        social_security_wage_base = 160200  # 2024 limit
        
        # Social Security tax (6.2% up to wage base)
        ss_tax = min(earned_income, social_security_wage_base) * 0.062
        
        # Medicare tax (1.45% on all income)
        medicare_tax = earned_income * 0.0145
        
        # Additional Medicare tax (0.9% on income over threshold)
        medicare_threshold = 250000  # For married filing jointly
        additional_medicare = max(0, earned_income - medicare_threshold) * 0.009
        
        return {
            'social_security': ss_tax,
            'medicare': medicare_tax + additional_medicare,
            'total_payroll': ss_tax + medicare_tax + additional_medicare
        }
    
    def calculate_total_tax(self, 
                          gross_income: float,
                          deductions: float = None,
                          state: str = 'CA') -> Dict[str, float]:
        """Calculate total tax liability"""
        
        if deductions is None:
            deductions = self.standard_deduction
        
        # Calculate taxable income
        taxable_income = max(0, gross_income - deductions)
        
        # Calculate taxes
        federal_tax = self.calculate_federal_income_tax(taxable_income)
        state_tax = self.calculate_state_tax(taxable_income, state)
        payroll_taxes = self.calculate_payroll_taxes(gross_income)
        
        total_tax = federal_tax + state_tax + payroll_taxes['total_payroll']
        effective_rate = total_tax / gross_income if gross_income > 0 else 0
        
        return {
            'federal_income_tax': federal_tax,
            'state_income_tax': state_tax,
            'payroll_taxes': payroll_taxes['total_payroll'],
            'total_tax': total_tax,
            'after_tax_income': gross_income - total_tax,
            'effective_tax_rate': effective_rate,
            'taxable_income': taxable_income
        }

class LifeEventModeler:
    """Models the financial impact of life events"""
    
    def __init__(self):
        self.event_templates = self._initialize_event_templates()
    
    def _initialize_event_templates(self) -> Dict[LifeEvent, Dict]:
        """Initialize default templates for common life events"""
        return {
            LifeEvent.RETIREMENT: {
                'income_replacement_ratio': 0.75,
                'healthcare_cost_increase': 1.5,
                'travel_expense_increase': 1.3,
                'housing_cost_decrease': 0.8
            },
            LifeEvent.CHILD_BIRTH: {
                'initial_cost': 15000,
                'annual_childcare_cost': 12000,
                'annual_basic_cost': 8000,
                'healthcare_increase': 1.25,
                'life_insurance_need': 250000
            },
            LifeEvent.CHILD_COLLEGE: {
                'annual_tuition_cost': 30000,
                'room_board_cost': 15000,
                'duration_years': 4,
                'inflation_rate': 0.06
            },
            LifeEvent.HOME_PURCHASE: {
                'down_payment_percent': 0.20,
                'closing_costs_percent': 0.03,
                'monthly_maintenance_percent': 0.01,
                'property_tax_percent': 0.012,
                'insurance_percent': 0.0035
            },
            LifeEvent.MARRIAGE: {
                'wedding_cost': 35000,
                'combined_living_expense_efficiency': 0.75,
                'insurance_changes': {'health': -0.20, 'life': 1.5}
            }
        }
    
    def model_retirement(self, 
                        current_income: float,
                        retirement_date: date,
                        life_expectancy_years: int = 30) -> LifeEventDefinition:
        """Model retirement cash flow impact"""
        
        template = self.event_templates[LifeEvent.RETIREMENT]
        
        # Reduced income from salary replacement
        pension_income = IncomeStream(
            name="Pension/401k Income",
            income_type=IncomeType.PENSION,
            amount=current_income * template['income_replacement_ratio'] / 12,
            start_date=retirement_date,
            end_date=retirement_date + timedelta(days=365 * life_expectancy_years),
            growth_rate=0.02,  # Conservative growth
            tax_rate=0.15  # Lower tax rate in retirement
        )
        
        # Social Security income (simplified calculation)
        ss_income = IncomeStream(
            name="Social Security",
            income_type=IncomeType.SOCIAL_SECURITY,
            amount=current_income * 0.4 / 12,  # Rough estimate
            start_date=retirement_date,
            end_date=retirement_date + timedelta(days=365 * life_expectancy_years),
            growth_rate=0.025,  # COLA adjustments
            tax_rate=0.10
        )
        
        # Healthcare cost increase
        healthcare_increase = ExpenseItem(
            name="Retirement Healthcare Premium",
            category=ExpenseCategory.HEALTHCARE,
            amount=1500,  # Monthly increase
            start_date=retirement_date,
            inflation_category="healthcare"
        )
        
        return LifeEventDefinition(
            event_type=LifeEvent.RETIREMENT,
            event_date=retirement_date,
            name="Retirement",
            description="Transition from working income to retirement income",
            ongoing_income_changes=[pension_income, ss_income],
            ongoing_expense_changes=[healthcare_increase]
        )
    
    def model_child_birth(self, 
                         birth_date: date,
                         child_count: int = 1) -> LifeEventDefinition:
        """Model child birth cash flow impact"""
        
        template = self.event_templates[LifeEvent.CHILD_BIRTH]
        
        # Initial costs
        immediate_cost = template['initial_cost'] * child_count
        
        # Ongoing childcare costs
        childcare_expense = ExpenseItem(
            name=f"Childcare for {child_count} child(ren)",
            category=ExpenseCategory.CHILDCARE,
            amount=template['annual_childcare_cost'] * child_count / 12,
            start_date=birth_date,
            end_date=birth_date + timedelta(days=365 * 5),  # Until school age
            inflation_category="general"
        )
        
        # Basic child-related expenses
        child_expenses = ExpenseItem(
            name=f"Child Expenses for {child_count} child(ren)",
            category=ExpenseCategory.OTHER,
            amount=template['annual_basic_cost'] * child_count / 12,
            start_date=birth_date,
            end_date=birth_date + timedelta(days=365 * 18),  # Until age 18
            inflation_category="general"
        )
        
        return LifeEventDefinition(
            event_type=LifeEvent.CHILD_BIRTH,
            event_date=birth_date,
            name=f"Birth of {child_count} Child(ren)",
            description=f"Financial impact of {child_count} new child(ren)",
            immediate_cash_impact=-immediate_cost,
            ongoing_expense_changes=[childcare_expense, child_expenses]
        )
    
    def model_college_expenses(self,
                              college_start_date: date,
                              college_type: str = "public",
                              children_count: int = 1) -> LifeEventDefinition:
        """Model college expense cash flow impact"""
        
        template = self.event_templates[LifeEvent.CHILD_COLLEGE]
        
        # Adjust costs based on college type
        cost_multipliers = {
            "public_in_state": 1.0,
            "public_out_state": 1.5,
            "private": 2.5
        }
        
        multiplier = cost_multipliers.get(college_type, 1.0)
        annual_tuition = template['annual_tuition_cost'] * multiplier
        annual_room_board = template['room_board_cost']
        
        # College expenses
        college_expense = ExpenseItem(
            name=f"College Expenses for {children_count} child(ren)",
            category=ExpenseCategory.EDUCATION,
            amount=(annual_tuition + annual_room_board) * children_count / 12,
            start_date=college_start_date,
            end_date=college_start_date + timedelta(days=365 * template['duration_years']),
            inflation_category="education"
        )
        
        return LifeEventDefinition(
            event_type=LifeEvent.CHILD_COLLEGE,
            event_date=college_start_date,
            name=f"College for {children_count} Child(ren)",
            description=f"College expenses for {children_count} children",
            ongoing_expense_changes=[college_expense]
        )

class CashFlowModelingEngine:
    """Main engine for cash flow modeling and projection"""
    
    def __init__(self):
        self.tax_calculator = TaxCalculator()
        self.life_event_modeler = LifeEventModeler()
        self.inflation_assumptions = InflationAssumptions()
    
    async def project_cash_flows(self,
                                income_streams: List[IncomeStream],
                                expenses: List[ExpenseItem],
                                life_events: List[LifeEventDefinition],
                                start_date: date,
                                end_date: date,
                                frequency: str = "monthly") -> CashFlowProjection:
        """Generate comprehensive cash flow projection"""
        
        logger.info(f"Projecting cash flows from {start_date} to {end_date}")
        
        # Generate date range
        dates = self._generate_date_range(start_date, end_date, frequency)
        n_periods = len(dates)
        
        # Initialize arrays
        gross_income = np.zeros(n_periods)
        total_expenses = np.zeros(n_periods)
        income_breakdown = {income_type: np.zeros(n_periods) for income_type in IncomeType}
        expense_breakdown = {expense_cat: np.zeros(n_periods) for expense_cat in ExpenseCategory}
        tax_breakdown = {'federal': np.zeros(n_periods), 'state': np.zeros(n_periods), 
                        'payroll': np.zeros(n_periods)}
        life_events_impact = {}
        
        # Process each period
        for i, current_date in enumerate(dates):
            # Calculate income for this period
            period_income = self._calculate_period_income(
                income_streams, current_date, start_date, life_events
            )
            gross_income[i] = sum(period_income.values())
            
            # Update income breakdown
            for income_type, amount in period_income.items():
                if income_type in income_breakdown:
                    income_breakdown[income_type][i] = amount
            
            # Calculate expenses for this period
            period_expenses = self._calculate_period_expenses(
                expenses, current_date, start_date, life_events
            )
            total_expenses[i] = sum(period_expenses.values())
            
            # Update expense breakdown
            for expense_cat, amount in period_expenses.items():
                if expense_cat in expense_breakdown:
                    expense_breakdown[expense_cat][i] = amount
            
            # Calculate taxes
            annual_income = gross_income[i] * (12 if frequency == "monthly" else 1)
            tax_result = self.tax_calculator.calculate_total_tax(annual_income)
            
            # Allocate taxes to period
            period_factor = 1/12 if frequency == "monthly" else 1
            tax_breakdown['federal'][i] = tax_result['federal_income_tax'] * period_factor
            tax_breakdown['state'][i] = tax_result['state_income_tax'] * period_factor
            tax_breakdown['payroll'][i] = tax_result['payroll_taxes'] * period_factor
            
            # Process life events impact for this period
            for event in life_events:
                if self._is_event_active(event, current_date):
                    event_impact = self._calculate_life_event_impact(event, current_date, start_date)
                    if event.name not in life_events_impact:
                        life_events_impact[event.name] = np.zeros(n_periods)
                    life_events_impact[event.name][i] = event_impact
        
        # Calculate net cash flow
        total_taxes = tax_breakdown['federal'] + tax_breakdown['state'] + tax_breakdown['payroll']
        after_tax_income = gross_income - total_taxes
        net_cash_flow = after_tax_income - total_expenses
        cumulative_cash_flow = np.cumsum(net_cash_flow)
        
        logger.info("Cash flow projection completed")
        
        return CashFlowProjection(
            dates=dates,
            gross_income=gross_income,
            after_tax_income=after_tax_income,
            total_expenses=total_expenses,
            net_cash_flow=net_cash_flow,
            cumulative_cash_flow=cumulative_cash_flow,
            income_breakdown=income_breakdown,
            expense_breakdown=expense_breakdown,
            tax_breakdown=tax_breakdown,
            life_events_impact=life_events_impact
        )
    
    async def analyze_scenarios(self,
                              base_scenario: CashFlowScenario,
                              alternative_scenarios: List[CashFlowScenario],
                              income_streams: List[IncomeStream],
                              expenses: List[ExpenseItem],
                              start_date: date,
                              end_date: date) -> Dict[str, CashFlowProjection]:
        """Analyze multiple cash flow scenarios"""
        
        logger.info(f"Analyzing {len(alternative_scenarios) + 1} cash flow scenarios")
        
        results = {}
        
        # Analyze base scenario
        results[base_scenario.name] = await self.project_cash_flows(
            income_streams, expenses, base_scenario.life_events, start_date, end_date
        )
        
        # Analyze alternative scenarios
        for scenario in alternative_scenarios:
            # Adjust income and expenses based on scenario
            adjusted_income = self._adjust_income_streams(income_streams, scenario)
            adjusted_expenses = self._adjust_expenses(expenses, scenario)
            
            results[scenario.name] = await self.project_cash_flows(
                adjusted_income, adjusted_expenses, scenario.life_events, start_date, end_date
            )
        
        return results
    
    def _generate_date_range(self, start_date: date, end_date: date, frequency: str) -> List[date]:
        """Generate date range based on frequency"""
        dates = []
        current_date = start_date
        
        if frequency == "monthly":
            while current_date <= end_date:
                dates.append(current_date)
                # Move to next month
                if current_date.month == 12:
                    current_date = current_date.replace(year=current_date.year + 1, month=1)
                else:
                    current_date = current_date.replace(month=current_date.month + 1)
        elif frequency == "quarterly":
            while current_date <= end_date:
                dates.append(current_date)
                # Move to next quarter
                new_month = current_date.month + 3
                if new_month > 12:
                    current_date = current_date.replace(year=current_date.year + 1, month=new_month - 12)
                else:
                    current_date = current_date.replace(month=new_month)
        elif frequency == "annually":
            while current_date <= end_date:
                dates.append(current_date)
                current_date = current_date.replace(year=current_date.year + 1)
        
        return dates
    
    def _calculate_period_income(self,
                               income_streams: List[IncomeStream],
                               current_date: date,
                               start_date: date,
                               life_events: List[LifeEventDefinition]) -> Dict[IncomeType, float]:
        """Calculate income for a specific period"""
        
        period_income = {income_type: 0.0 for income_type in IncomeType}
        
        # Calculate base income streams
        for stream in income_streams:
            if self._is_income_active(stream, current_date):
                amount = self._calculate_inflated_amount(
                    stream.amount,
                    stream.start_date,
                    current_date,
                    stream.growth_rate if stream.inflation_adjustment else 0
                )
                
                # Apply seasonal pattern if exists
                if stream.seasonal_pattern and current_date.month in stream.seasonal_pattern:
                    amount *= stream.seasonal_pattern[current_date.month]
                
                # Apply volatility if specified
                if stream.volatility > 0:
                    volatility_factor = np.random.normal(1.0, stream.volatility)
                    amount *= max(0, volatility_factor)
                
                period_income[stream.income_type] += amount
        
        # Add life event income changes
        for event in life_events:
            if self._is_event_active(event, current_date):
                for stream in event.ongoing_income_changes:
                    if self._is_income_active(stream, current_date):
                        amount = self._calculate_inflated_amount(
                            stream.amount,
                            max(stream.start_date, event.event_date),
                            current_date,
                            stream.growth_rate if stream.inflation_adjustment else 0
                        )
                        period_income[stream.income_type] += amount
        
        return period_income
    
    def _calculate_period_expenses(self,
                                 expenses: List[ExpenseItem],
                                 current_date: date,
                                 start_date: date,
                                 life_events: List[LifeEventDefinition]) -> Dict[ExpenseCategory, float]:
        """Calculate expenses for a specific period"""
        
        period_expenses = {expense_cat: 0.0 for expense_cat in ExpenseCategory}
        
        # Calculate base expenses
        for expense in expenses:
            if self._is_expense_active(expense, current_date):
                # Get inflation rate for this category
                inflation_rate = getattr(self.inflation_assumptions, expense.inflation_category, 0.025)
                
                amount = self._calculate_inflated_amount(
                    expense.amount,
                    expense.start_date,
                    current_date,
                    inflation_rate
                )
                
                # Apply seasonal pattern if exists
                if expense.seasonal_pattern and current_date.month in expense.seasonal_pattern:
                    amount *= expense.seasonal_pattern[current_date.month]
                
                period_expenses[expense.category] += amount
        
        # Add life event expense changes
        for event in life_events:
            if self._is_event_active(event, current_date):
                for expense in event.ongoing_expense_changes:
                    if self._is_expense_active(expense, current_date):
                        inflation_rate = getattr(self.inflation_assumptions, expense.inflation_category, 0.025)
                        amount = self._calculate_inflated_amount(
                            expense.amount,
                            max(expense.start_date, event.event_date),
                            current_date,
                            inflation_rate
                        )
                        period_expenses[expense.category] += amount
        
        return period_expenses
    
    def _is_income_active(self, stream: IncomeStream, current_date: date) -> bool:
        """Check if income stream is active on given date"""
        return (current_date >= stream.start_date and 
                (stream.end_date is None or current_date <= stream.end_date))
    
    def _is_expense_active(self, expense: ExpenseItem, current_date: date) -> bool:
        """Check if expense item is active on given date"""
        return (current_date >= expense.start_date and 
                (expense.end_date is None or current_date <= expense.end_date))
    
    def _is_event_active(self, event: LifeEventDefinition, current_date: date) -> bool:
        """Check if life event affects cash flow on given date"""
        if event.duration_years is None:
            return current_date >= event.event_date
        else:
            end_date = event.event_date + timedelta(days=365 * event.duration_years)
            return event.event_date <= current_date <= end_date
    
    def _calculate_inflated_amount(self,
                                 base_amount: float,
                                 start_date: date,
                                 current_date: date,
                                 annual_rate: float) -> float:
        """Calculate inflated amount based on time elapsed"""
        
        if annual_rate == 0:
            return base_amount
        
        years_elapsed = (current_date - start_date).days / 365.25
        return base_amount * (1 + annual_rate) ** years_elapsed
    
    def _calculate_life_event_impact(self,
                                   event: LifeEventDefinition,
                                   current_date: date,
                                   start_date: date) -> float:
        """Calculate immediate cash impact of life event"""
        
        if current_date == event.event_date:
            return event.immediate_cash_impact
        return 0.0
    
    def _adjust_income_streams(self,
                             base_streams: List[IncomeStream],
                             scenario: CashFlowScenario) -> List[IncomeStream]:
        """Adjust income streams for scenario analysis"""
        
        adjusted_streams = []
        for stream in base_streams:
            adjusted_stream = IncomeStream(
                name=stream.name,
                income_type=stream.income_type,
                amount=stream.amount * scenario.income_multiplier,
                start_date=stream.start_date,
                end_date=stream.end_date,
                growth_rate=stream.growth_rate * scenario.inflation_adjustment,
                inflation_adjustment=stream.inflation_adjustment,
                tax_rate=stream.tax_rate,
                frequency=stream.frequency,
                seasonal_pattern=stream.seasonal_pattern,
                volatility=stream.volatility
            )
            adjusted_streams.append(adjusted_stream)
        
        return adjusted_streams
    
    def _adjust_expenses(self,
                        base_expenses: List[ExpenseItem],
                        scenario: CashFlowScenario) -> List[ExpenseItem]:
        """Adjust expenses for scenario analysis"""
        
        adjusted_expenses = []
        for expense in base_expenses:
            adjusted_expense = ExpenseItem(
                name=expense.name,
                category=expense.category,
                amount=expense.amount * scenario.expense_multiplier,
                start_date=expense.start_date,
                end_date=expense.end_date,
                frequency=expense.frequency,
                inflation_category=expense.inflation_category,
                tax_deductible=expense.tax_deductible,
                seasonal_pattern=expense.seasonal_pattern,
                life_stage_multipliers=expense.life_stage_multipliers
            )
            adjusted_expenses.append(adjusted_expense)
        
        return adjusted_expenses

# Example usage and testing
async def run_cash_flow_example():
    """Example of cash flow modeling"""
    
    # Define income streams
    income_streams = [
        IncomeStream(
            name="Primary Salary",
            income_type=IncomeType.SALARY,
            amount=8333,  # $100k annually / 12
            start_date=date(2024, 1, 1),
            growth_rate=0.04,
            tax_rate=0.25
        ),
        IncomeStream(
            name="Spouse Salary",
            income_type=IncomeType.SALARY,
            amount=5000,  # $60k annually / 12
            start_date=date(2024, 1, 1),
            growth_rate=0.03,
            tax_rate=0.22
        )
    ]
    
    # Define expenses
    expenses = [
        ExpenseItem(
            name="Housing",
            category=ExpenseCategory.HOUSING,
            amount=3000,
            start_date=date(2024, 1, 1),
            inflation_category="housing"
        ),
        ExpenseItem(
            name="Transportation",
            category=ExpenseCategory.TRANSPORTATION,
            amount=800,
            start_date=date(2024, 1, 1)
        ),
        ExpenseItem(
            name="Food",
            category=ExpenseCategory.FOOD,
            amount=1200,
            start_date=date(2024, 1, 1)
        ),
        ExpenseItem(
            name="Healthcare",
            category=ExpenseCategory.HEALTHCARE,
            amount=600,
            start_date=date(2024, 1, 1),
            inflation_category="healthcare"
        )
    ]
    
    # Define life events
    engine = CashFlowModelingEngine()
    
    life_events = [
        engine.life_event_modeler.model_child_birth(date(2025, 6, 1)),
        engine.life_event_modeler.model_retirement(160000, date(2054, 1, 1))
    ]
    
    # Run projection
    projection = await engine.project_cash_flows(
        income_streams=income_streams,
        expenses=expenses,
        life_events=life_events,
        start_date=date(2024, 1, 1),
        end_date=date(2034, 1, 1)
    )
    
    return projection

if __name__ == "__main__":
    # Run example
    import asyncio
    projection = asyncio.run(run_cash_flow_example())
    
    print("\n=== Cash Flow Projection Results ===")
    print(f"Projection period: {len(projection.dates)} months")
    print(f"Average monthly gross income: ${np.mean(projection.gross_income):,.2f}")
    print(f"Average monthly after-tax income: ${np.mean(projection.after_tax_income):,.2f}")
    print(f"Average monthly expenses: ${np.mean(projection.total_expenses):,.2f}")
    print(f"Average monthly net cash flow: ${np.mean(projection.net_cash_flow):,.2f}")
    print(f"Final cumulative cash flow: ${projection.cumulative_cash_flow[-1]:,.2f}")