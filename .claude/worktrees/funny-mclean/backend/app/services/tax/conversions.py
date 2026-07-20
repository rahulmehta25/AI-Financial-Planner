"""
Roth Conversion Analysis and Strategy Engine

Implements sophisticated Roth conversion strategies including:
- Multi-year conversion planning
- Tax bracket management
- Market timing considerations
- State tax implications
- Five-year rule tracking
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from decimal import Decimal
from datetime import datetime, date, timedelta
import logging
from sqlalchemy.orm import Session

from ...models.tax_accounts import (
    TaxAccount, RothConversionRecord, TaxProjection, 
    AccountTypeEnum, TaxTreatmentEnum, IRSLimits2025
)
from ...models.user import User
from ...models.financial_profile import FinancialProfile

logger = logging.getLogger(__name__)


@dataclass
class TaxBracket:
    """Tax bracket definition"""
    min_income: Decimal
    max_income: Decimal
    rate: float
    bracket_space: Decimal = field(init=False)
    
    def __post_init__(self):
        self.bracket_space = self.max_income - self.min_income


@dataclass
class ConversionScenario:
    """Roth conversion scenario analysis"""
    conversion_amount: Decimal
    conversion_year: int
    current_tax_impact: Decimal
    future_tax_savings: Decimal
    net_present_value: Decimal
    break_even_years: int
    marginal_tax_rate_at_conversion: float
    assumed_retirement_tax_rate: float
    five_year_rule_date: date
    risk_factors: List[str] = field(default_factory=list)


@dataclass
class MultiYearConversionPlan:
    """Multi-year Roth conversion strategy"""
    total_amount_to_convert: Decimal
    conversion_schedule: List[ConversionScenario]
    total_tax_cost: Decimal
    total_future_benefit: Decimal
    net_benefit: Decimal
    optimal_years: List[int]
    contingency_plans: List[Dict] = field(default_factory=list)


class RothConversionAnalyzer:
    """
    Comprehensive Roth conversion analysis and optimization engine
    """
    
    def __init__(self, db_session: Session):
        self.db = db_session
        
        # 2025 Tax Brackets (simplified - single filer)
        self.tax_brackets_single = [
            TaxBracket(Decimal('0'), Decimal('11600'), 0.10),
            TaxBracket(Decimal('11600'), Decimal('47150'), 0.12),
            TaxBracket(Decimal('47150'), Decimal('100525'), 0.22),
            TaxBracket(Decimal('100525'), Decimal('191950'), 0.24),
            TaxBracket(Decimal('191950'), Decimal('243725'), 0.32),
            TaxBracket(Decimal('243725'), Decimal('609350'), 0.35),
            TaxBracket(Decimal('609350'), Decimal('999999999'), 0.37)
        ]
        
        # 2025 Tax Brackets (married filing jointly)
        self.tax_brackets_married = [
            TaxBracket(Decimal('0'), Decimal('23200'), 0.10),
            TaxBracket(Decimal('23200'), Decimal('94300'), 0.12),
            TaxBracket(Decimal('94300'), Decimal('201050'), 0.22),
            TaxBracket(Decimal('201050'), Decimal('383900'), 0.24),
            TaxBracket(Decimal('383900'), Decimal('487450'), 0.32),
            TaxBracket(Decimal('487450'), Decimal('731200'), 0.35),
            TaxBracket(Decimal('731200'), Decimal('999999999'), 0.37)
        ]
        
        # Standard assumptions
        self.standard_assumptions = {
            'market_growth_rate': 0.07,  # Annual market growth
            'inflation_rate': 0.03,      # Annual inflation
            'discount_rate': 0.05,       # NPV discount rate
            'tax_rate_in_retirement': 0.22,  # Default assumption
            'medicare_surcharge_threshold': 200000  # IRMAA thresholds
        }
        
    async def analyze_conversion_opportunity(
        self,
        user_id: str,
        conversion_amount: Optional[Decimal] = None,
        analysis_years: int = 5
    ) -> MultiYearConversionPlan:
        """
        Comprehensive analysis of Roth conversion opportunities
        """
        logger.info(f"Analyzing Roth conversion for user {user_id}")
        
        # Get user profile and accounts
        user_profile = self._get_user_profile(user_id)
        traditional_accounts = self._get_traditional_retirement_accounts(user_id)
        roth_accounts = self._get_roth_accounts(user_id)
        
        if not traditional_accounts:
            logger.warning(f"No traditional retirement accounts found for user {user_id}")
            return self._empty_conversion_plan()
        
        # Calculate available balance for conversion
        total_traditional_balance = sum(
            account.current_balance for account in traditional_accounts
        )
        
        # If no amount specified, analyze optimal amount
        if not conversion_amount:
            conversion_amount = await self._calculate_optimal_conversion_amount(
                user_profile, total_traditional_balance
            )
        
        # Analyze conversion scenarios for multiple years
        conversion_scenarios = []
        
        for year in range(analysis_years):
            scenario = await self._analyze_conversion_scenario(
                user_profile,
                conversion_amount,
                year,
                traditional_accounts,
                roth_accounts
            )
            
            if scenario:
                conversion_scenarios.append(scenario)
        
        # Optimize conversion schedule
        optimal_schedule = self._optimize_conversion_schedule(
            conversion_scenarios,
            total_traditional_balance,
            user_profile
        )
        
        # Calculate total metrics
        total_tax_cost = sum(
            scenario.current_tax_impact for scenario in optimal_schedule
        )
        
        total_future_benefit = sum(
            scenario.future_tax_savings for scenario in optimal_schedule
        )
        
        net_benefit = total_future_benefit - total_tax_cost
        
        # Generate contingency plans
        contingency_plans = self._generate_contingency_plans(
            optimal_schedule, user_profile
        )
        
        plan = MultiYearConversionPlan(
            total_amount_to_convert=sum(s.conversion_amount for s in optimal_schedule),
            conversion_schedule=optimal_schedule,
            total_tax_cost=total_tax_cost,
            total_future_benefit=total_future_benefit,
            net_benefit=net_benefit,
            optimal_years=[s.conversion_year for s in optimal_schedule],
            contingency_plans=contingency_plans
        )
        
        # Store analysis results
        await self._store_conversion_analysis(user_id, plan)
        
        logger.info(
            f"Conversion analysis complete. Net benefit: ${net_benefit}"
        )
        
        return plan
    
    def _get_user_profile(self, user_id: str) -> FinancialProfile:
        """Get user's financial profile"""
        return self.db.query(FinancialProfile).filter(
            FinancialProfile.user_id == user_id
        ).first()
    
    def _get_traditional_retirement_accounts(self, user_id: str) -> List[TaxAccount]:
        """Get traditional retirement accounts eligible for conversion"""
        return self.db.query(TaxAccount).filter(
            TaxAccount.user_id == user_id,
            TaxAccount.account_type.in_([
                AccountTypeEnum.TRADITIONAL_401K,
                AccountTypeEnum.TRADITIONAL_IRA,
                AccountTypeEnum.SEP_IRA,
                AccountTypeEnum.SIMPLE_IRA
            ]),
            TaxAccount.is_active == True
        ).all()
    
    def _get_roth_accounts(self, user_id: str) -> List[TaxAccount]:
        """Get Roth accounts for conversion destination"""
        return self.db.query(TaxAccount).filter(
            TaxAccount.user_id == user_id,
            TaxAccount.account_type.in_([
                AccountTypeEnum.ROTH_401K,
                AccountTypeEnum.ROTH_IRA
            ]),
            TaxAccount.is_active == True
        ).all()
    
    async def _calculate_optimal_conversion_amount(
        self,
        user_profile: FinancialProfile,
        available_balance: Decimal
    ) -> Decimal:
        """Calculate optimal conversion amount to stay within tax bracket"""
        
        current_income = user_profile.annual_income or Decimal('0')
        filing_status = user_profile.filing_status or 'single'
        
        # Get tax brackets
        if filing_status == 'married_jointly':
            brackets = self.tax_brackets_married
        else:
            brackets = self.tax_brackets_single
        
        # Find current tax bracket
        current_bracket = None
        for bracket in brackets:
            if bracket.min_income <= current_income <= bracket.max_income:
                current_bracket = bracket
                break
        
        if not current_bracket:
            return Decimal('0')
        
        # Calculate space remaining in current bracket
        remaining_bracket_space = current_bracket.max_income - current_income
        
        # Convert up to bracket limit, but not more than available
        optimal_amount = min(remaining_bracket_space, available_balance)
        
        # Don't convert less than $5,000 (not worth the complexity)
        if optimal_amount < Decimal('5000'):
            return Decimal('0')
        
        return optimal_amount
    
    async def _analyze_conversion_scenario(
        self,
        user_profile: FinancialProfile,
        conversion_amount: Decimal,
        conversion_year: int,
        traditional_accounts: List[TaxAccount],
        roth_accounts: List[TaxAccount]
    ) -> Optional[ConversionScenario]:
        """Analyze a specific conversion scenario"""
        
        # Project income for conversion year
        current_income = user_profile.annual_income or Decimal('0')
        projected_income = current_income * (
            Decimal('1.03') ** conversion_year  # Assume 3% income growth
        )
        
        # Calculate tax impact of conversion
        tax_impact = self._calculate_conversion_tax_impact(
            projected_income,
            conversion_amount,
            user_profile.filing_status
        )
        
        # Calculate future tax savings
        years_to_retirement = max(1, user_profile.retirement_age - user_profile.age - conversion_year)
        future_value = self._calculate_future_value(
            conversion_amount,
            years_to_retirement,
            self.standard_assumptions['market_growth_rate']
        )
        
        # Assume retirement tax rate (could be more sophisticated)
        retirement_tax_rate = self.standard_assumptions['tax_rate_in_retirement']
        
        future_tax_savings = future_value * Decimal(str(retirement_tax_rate))
        
        # Calculate net present value
        npv = self._calculate_npv(
            -tax_impact,  # Cost today
            future_tax_savings,  # Benefit in retirement
            years_to_retirement,
            self.standard_assumptions['discount_rate']
        )
        
        # Calculate break-even point
        break_even_years = self._calculate_break_even_years(
            tax_impact,
            conversion_amount,
            retirement_tax_rate
        )
        
        # Five-year rule date
        five_year_date = date.today() + timedelta(days=365 * 5)
        
        # Identify risk factors
        risk_factors = self._identify_conversion_risks(
            user_profile,
            conversion_amount,
            conversion_year,
            tax_impact
        )
        
        # Only recommend if NPV is positive and reasonable break-even
        if npv <= 0 or break_even_years > 15:
            return None
        
        return ConversionScenario(
            conversion_amount=conversion_amount,
            conversion_year=conversion_year,
            current_tax_impact=tax_impact,
            future_tax_savings=future_tax_savings,
            net_present_value=npv,
            break_even_years=break_even_years,
            marginal_tax_rate_at_conversion=float(
                self._get_marginal_tax_rate(projected_income, user_profile.filing_status)
            ),
            assumed_retirement_tax_rate=retirement_tax_rate,
            five_year_rule_date=five_year_date,
            risk_factors=risk_factors
        )
    
    def _calculate_conversion_tax_impact(
        self,
        income: Decimal,
        conversion_amount: Decimal,
        filing_status: str
    ) -> Decimal:
        """Calculate additional tax owed due to conversion"""
        
        # Tax without conversion
        tax_without = self._calculate_federal_tax(income, filing_status)
        
        # Tax with conversion
        tax_with = self._calculate_federal_tax(income + conversion_amount, filing_status)
        
        return tax_with - tax_without
    
    def _calculate_federal_tax(self, income: Decimal, filing_status: str) -> Decimal:
        """Calculate federal income tax"""
        
        if filing_status == 'married_jointly':
            brackets = self.tax_brackets_married
        else:
            brackets = self.tax_brackets_single
        
        tax_owed = Decimal('0')
        remaining_income = income
        
        for bracket in brackets:
            if remaining_income <= 0:
                break
            
            taxable_in_bracket = min(remaining_income, bracket.bracket_space)
            tax_owed += taxable_in_bracket * Decimal(str(bracket.rate))
            remaining_income -= taxable_in_bracket
        
        return tax_owed
    
    def _get_marginal_tax_rate(self, income: Decimal, filing_status: str) -> Decimal:
        """Get marginal tax rate for given income"""
        
        if filing_status == 'married_jointly':
            brackets = self.tax_brackets_married
        else:
            brackets = self.tax_brackets_single
        
        for bracket in brackets:
            if bracket.min_income <= income <= bracket.max_income:
                return Decimal(str(bracket.rate))
        
        return Decimal('0.37')  # Top rate
    
    def _calculate_future_value(
        self,
        present_value: Decimal,
        years: int,
        growth_rate: float
    ) -> Decimal:
        """Calculate future value with compound growth"""
        return present_value * (Decimal('1') + Decimal(str(growth_rate))) ** years
    
    def _calculate_npv(
        self,
        initial_cost: Decimal,
        future_benefit: Decimal,
        years: int,
        discount_rate: float
    ) -> Decimal:
        """Calculate net present value"""
        pv_future_benefit = future_benefit / (
            (Decimal('1') + Decimal(str(discount_rate))) ** years
        )
        return initial_cost + pv_future_benefit
    
    def _calculate_break_even_years(
        self,
        conversion_tax_cost: Decimal,
        conversion_amount: Decimal,
        retirement_tax_rate: float
    ) -> int:
        """Calculate years to break even on conversion"""
        
        # Annual tax savings in retirement
        annual_tax_savings = (
            conversion_amount * 
            Decimal(str(self.standard_assumptions['market_growth_rate'])) *
            Decimal(str(retirement_tax_rate))
        )
        
        if annual_tax_savings <= 0:
            return 999  # Never breaks even
        
        return int(conversion_tax_cost / annual_tax_savings)
    
    def _identify_conversion_risks(
        self,
        user_profile: FinancialProfile,
        conversion_amount: Decimal,
        conversion_year: int,
        tax_impact: Decimal
    ) -> List[str]:
        """Identify potential risks with conversion"""
        
        risks = []
        
        # Large tax impact
        income = user_profile.annual_income or Decimal('0')
        if tax_impact > income * Decimal('0.1'):  # More than 10% of income
            risks.append("High tax impact relative to income")
        
        # Medicare surcharge risk
        if income + conversion_amount > Decimal('200000'):
            risks.append("May trigger Medicare IRMAA surcharges")
        
        # Early in career (long time horizon)
        if user_profile.age < 40:
            risks.append("Very long time horizon increases uncertainty")
        
        # Close to retirement
        if user_profile.retirement_age - user_profile.age < 10:
            risks.append("Short time horizon may not justify conversion cost")
        
        # Large conversion relative to balance
        traditional_balance = sum(
            acc.current_balance for acc in self._get_traditional_retirement_accounts(user_profile.user_id)
        )
        
        if conversion_amount > traditional_balance * Decimal('0.5'):
            risks.append("Converting large portion of traditional balance")
        
        # Market timing risk
        risks.append("Market downturn could reduce conversion value")
        
        return risks
    
    def _optimize_conversion_schedule(
        self,
        scenarios: List[ConversionScenario],
        total_balance: Decimal,
        user_profile: FinancialProfile
    ) -> List[ConversionScenario]:
        """Optimize multi-year conversion schedule"""
        
        # Sort scenarios by net present value per dollar converted
        scenarios_by_efficiency = sorted(
            scenarios,
            key=lambda x: x.net_present_value / x.conversion_amount,
            reverse=True
        )
        
        optimal_schedule = []
        remaining_balance = total_balance
        
        # Select scenarios that maximize total NPV
        for scenario in scenarios_by_efficiency:
            if (remaining_balance >= scenario.conversion_amount and
                scenario.net_present_value > 0 and
                len(optimal_schedule) < 5):  # Limit to 5 years
                
                optimal_schedule.append(scenario)
                remaining_balance -= scenario.conversion_amount
        
        return optimal_schedule
    
    def _generate_contingency_plans(
        self,
        optimal_schedule: List[ConversionScenario],
        user_profile: FinancialProfile
    ) -> List[Dict]:
        """Generate contingency plans for different scenarios"""
        
        contingencies = []
        
        # Market crash scenario
        contingencies.append({
            'scenario': 'market_crash',
            'description': 'Market drops 30% before conversion',
            'recommendation': 'Increase conversion amounts - assets are cheaper',
            'adjustment': 'Increase conversion by 20-30%'
        })
        
        # Income spike scenario
        contingencies.append({
            'scenario': 'income_increase',
            'description': 'Income increases significantly',
            'recommendation': 'Reduce or delay conversions to avoid higher brackets',
            'adjustment': 'Reduce conversion amounts or skip high-income years'
        })
        
        # Tax law changes
        contingencies.append({
            'scenario': 'tax_law_changes',
            'description': 'Tax rates increase or Roth rules change',
            'recommendation': 'Accelerate conversions if rates are increasing',
            'adjustment': 'Front-load conversions in early years'
        })
        
        # Health issues
        contingencies.append({
            'scenario': 'health_issues',
            'description': 'Health issues require early retirement',
            'recommendation': 'Prioritize conversions in early years',
            'adjustment': 'Complete conversions within 3 years'
        })
        
        return contingencies
    
    async def _store_conversion_analysis(
        self,
        user_id: str,
        plan: MultiYearConversionPlan
    ) -> None:
        """Store conversion analysis results"""
        
        for scenario in plan.conversion_schedule:
            projection = TaxProjection(
                user_id=user_id,
                projection_year=datetime.now().year + scenario.conversion_year,
                projected_tax_liability=scenario.current_tax_impact,
                scenario_name='roth_conversion',
                scenario_assumptions={
                    'conversion_amount': float(scenario.conversion_amount),
                    'tax_impact': float(scenario.current_tax_impact),
                    'future_benefit': float(scenario.future_tax_savings),
                    'npv': float(scenario.net_present_value),
                    'break_even_years': scenario.break_even_years,
                    'risk_factors': scenario.risk_factors
                }
            )
            
            self.db.add(projection)
        
        await self.db.commit()
    
    def _empty_conversion_plan(self) -> MultiYearConversionPlan:
        """Return empty plan when no conversions recommended"""
        return MultiYearConversionPlan(
            total_amount_to_convert=Decimal('0'),
            conversion_schedule=[],
            total_tax_cost=Decimal('0'),
            total_future_benefit=Decimal('0'),
            net_benefit=Decimal('0'),
            optimal_years=[],
            contingency_plans=[]
        )
    
    async def execute_roth_conversion(
        self,
        user_id: str,
        from_account_id: str,
        to_account_id: str,
        conversion_amount: Decimal,
        execution_date: date
    ) -> Dict:
        """Execute a Roth conversion"""
        
        from_account = self.db.query(TaxAccount).filter(
            TaxAccount.id == from_account_id,
            TaxAccount.user_id == user_id
        ).first()
        
        to_account = self.db.query(TaxAccount).filter(
            TaxAccount.id == to_account_id,
            TaxAccount.user_id == user_id
        ).first()
        
        if not from_account or not to_account:
            raise ValueError("Invalid account IDs")
        
        if from_account.current_balance < conversion_amount:
            raise ValueError("Insufficient balance for conversion")
        
        # Calculate tax impact
        user_profile = self._get_user_profile(user_id)
        tax_impact = self._calculate_conversion_tax_impact(
            user_profile.annual_income or Decimal('0'),
            conversion_amount,
            user_profile.filing_status
        )
        
        # Create conversion record
        conversion_record = RothConversionRecord(
            user_id=user_id,
            from_account_id=from_account_id,
            to_account_id=to_account_id,
            conversion_amount=conversion_amount,
            taxable_amount=conversion_amount,  # Typically the full amount
            tax_rate_at_conversion=float(
                self._get_marginal_tax_rate(
                    user_profile.annual_income or Decimal('0'),
                    user_profile.filing_status
                )
            ),
            taxes_paid=tax_impact,
            conversion_reason="Planned conversion for tax optimization",
            five_year_rule_date=execution_date + timedelta(days=365 * 5),
            conversion_date=datetime.combine(execution_date, datetime.min.time()),
            tax_year=execution_date.year
        )
        
        # Update account balances
        from_account.current_balance -= conversion_amount
        to_account.current_balance += conversion_amount
        
        self.db.add(conversion_record)
        await self.db.commit()
        
        result = {
            'conversion_id': str(conversion_record.id),
            'from_account': from_account.account_name,
            'to_account': to_account.account_name,
            'conversion_amount': conversion_amount,
            'tax_impact': tax_impact,
            'execution_date': execution_date,
            'five_year_rule_date': conversion_record.five_year_rule_date.date(),
            'status': 'executed'
        }
        
        logger.info(
            f"Executed Roth conversion: ${conversion_amount} from {from_account.account_name} "
            f"to {to_account.account_name}"
        )
        
        return result
    
    async def get_conversion_ladder_strategy(
        self,
        user_id: str,
        target_retirement_age: int,
        desired_roth_balance: Decimal
    ) -> Dict:
        """Generate Roth conversion ladder strategy for early retirement"""
        
        user_profile = self._get_user_profile(user_id)
        traditional_accounts = self._get_traditional_retirement_accounts(user_id)
        
        current_age = user_profile.age
        years_to_retirement = target_retirement_age - current_age
        
        if years_to_retirement <= 0:
            return {'error': 'Already at or past target retirement age'}
        
        # Calculate annual conversion needed
        total_traditional_balance = sum(
            account.current_balance for account in traditional_accounts
        )
        
        # Account for growth of existing balance
        projected_balance = self._calculate_future_value(
            total_traditional_balance,
            years_to_retirement,
            self.standard_assumptions['market_growth_rate']
        )
        
        # Annual conversion amount
        annual_conversion = min(
            desired_roth_balance / years_to_retirement,
            projected_balance / years_to_retirement
        )
        
        # Create ladder schedule
        ladder_schedule = []
        
        for year in range(years_to_retirement):
            # Lower conversions in early retirement years (lower income)
            if year >= years_to_retirement - 5:  # Last 5 years before retirement
                conversion_multiplier = 0.5  # Reduce due to lower income
            else:
                conversion_multiplier = 1.0
            
            year_conversion = annual_conversion * Decimal(str(conversion_multiplier))
            
            ladder_schedule.append({
                'year': datetime.now().year + year,
                'age': current_age + year,
                'conversion_amount': year_conversion,
                'reason': 'Early retirement ladder strategy',
                'five_year_access_date': datetime.now().date() + timedelta(days=365 * (5 + year))
            })
        
        return {
            'strategy': 'roth_conversion_ladder',
            'target_retirement_age': target_retirement_age,
            'total_conversions_needed': desired_roth_balance,
            'annual_conversion_target': annual_conversion,
            'conversion_schedule': ladder_schedule,
            'notes': [
                'Conversion ladder allows penalty-free access to principal after 5 years',
                'Consider tax implications of conversions in early retirement years',
                'Monitor income levels to optimize tax brackets'
            ]
        }