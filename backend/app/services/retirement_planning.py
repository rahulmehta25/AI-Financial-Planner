"""
Comprehensive retirement planning service with calculators, strategies, and optimization algorithms
for 401(k), IRA, Roth IRA, 529 Education Plans, and HSA accounts
"""

import math
import numpy as np
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Tuple, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum

from sqlalchemy.orm import Session
from app.models.retirement_accounts import (
    RetirementAccount, IRSContributionLimits, RetirementContribution,
    RetirementDistribution, AccountType, TaxTreatment, ContributionType
)


class FilingStatus(str, Enum):
    SINGLE = "single"
    MARRIED_FILING_JOINTLY = "married_filing_jointly"
    MARRIED_FILING_SEPARATELY = "married_filing_separately"
    HEAD_OF_HOUSEHOLD = "head_of_household"


class WithdrawalStrategy(str, Enum):
    PROPORTIONAL = "proportional"  # Withdraw proportionally from all accounts
    TAX_EFFICIENT = "tax_efficient"  # Tax-efficient sequence
    SPECIFIC_ORDER = "specific_order"  # User-defined order
    ROTH_CONVERSION_LADDER = "roth_conversion_ladder"


@dataclass
class TaxBracket:
    """Tax bracket definition"""
    min_income: Decimal
    max_income: Decimal
    rate: Decimal


@dataclass
class PersonalInfo:
    """Personal information for calculations"""
    current_age: int
    retirement_age: int
    life_expectancy: int = 95
    filing_status: FilingStatus = FilingStatus.SINGLE
    state_of_residence: str = "CA"
    current_income: Decimal = Decimal('0')
    spouse_age: Optional[int] = None
    spouse_income: Optional[Decimal] = None


@dataclass
class AccountBalance:
    """Account balance with growth projections"""
    account_id: str
    account_type: AccountType
    current_balance: Decimal
    annual_contribution: Decimal = Decimal('0')
    employer_match: Decimal = Decimal('0')
    expected_return: Decimal = Decimal('0.07')
    tax_treatment: TaxTreatment = TaxTreatment.TAX_DEFERRED


@dataclass
class RetirementGoal:
    """Retirement income goal"""
    target_retirement_income: Decimal
    income_replacement_ratio: Decimal = Decimal('0.80')
    inflation_rate: Decimal = Decimal('0.025')
    years_in_retirement: int = 25


@dataclass
class ContributionStrategy:
    """Optimal contribution strategy"""
    account_allocations: Dict[str, Decimal]
    total_annual_contribution: Decimal
    tax_savings: Decimal
    employer_match_captured: Decimal
    strategy_explanation: str


@dataclass
class WithdrawalPlan:
    """Optimal withdrawal sequence plan"""
    annual_withdrawals: List[Dict[str, Any]]
    total_taxes_paid: Decimal
    after_tax_income: Decimal
    account_balances_at_death: Dict[str, Decimal]
    strategy_explanation: str


@dataclass
class RothConversionAnalysis:
    """Roth conversion analysis results"""
    optimal_conversion_amount: Decimal
    years_to_convert: List[int]
    tax_cost_of_conversion: Decimal
    lifetime_tax_savings: Decimal
    breakeven_age: int
    conversion_timeline: List[Dict[str, Any]]


@dataclass
class RMDCalculation:
    """Required Minimum Distribution calculation"""
    account_id: str
    account_balance: Decimal
    age: int
    life_expectancy_factor: Decimal
    rmd_amount: Decimal
    tax_owed: Decimal


class RetirementPlanningService:
    """Comprehensive retirement planning service"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self._load_tax_brackets()
        self._load_rmd_tables()
    
    def _load_tax_brackets(self):
        """Load current tax brackets (2025 tax year)"""
        self.federal_tax_brackets = {
            FilingStatus.SINGLE: [
                TaxBracket(Decimal('0'), Decimal('11925'), Decimal('0.10')),
                TaxBracket(Decimal('11925'), Decimal('48475'), Decimal('0.12')),
                TaxBracket(Decimal('48475'), Decimal('103350'), Decimal('0.22')),
                TaxBracket(Decimal('103350'), Decimal('197300'), Decimal('0.24')),
                TaxBracket(Decimal('197300'), Decimal('250525'), Decimal('0.32')),
                TaxBracket(Decimal('250525'), Decimal('626350'), Decimal('0.35')),
                TaxBracket(Decimal('626350'), Decimal('999999999'), Decimal('0.37'))
            ],
            FilingStatus.MARRIED_FILING_JOINTLY: [
                TaxBracket(Decimal('0'), Decimal('23850'), Decimal('0.10')),
                TaxBracket(Decimal('23850'), Decimal('96950'), Decimal('0.12')),
                TaxBracket(Decimal('96950'), Decimal('206700'), Decimal('0.22')),
                TaxBracket(Decimal('206700'), Decimal('394600'), Decimal('0.24')),
                TaxBracket(Decimal('394600'), Decimal('501050'), Decimal('0.32')),
                TaxBracket(Decimal('501050'), Decimal('751600'), Decimal('0.35')),
                TaxBracket(Decimal('751600'), Decimal('999999999'), Decimal('0.37'))
            ]
        }
    
    def _load_rmd_tables(self):
        """Load IRS Required Minimum Distribution life expectancy tables"""
        # Uniform Lifetime Table (most common for RMDs)
        self.rmd_life_expectancy = {
            70: 29.1, 71: 28.2, 72: 27.4, 73: 26.5, 74: 25.5,
            75: 24.6, 76: 23.7, 77: 22.9, 78: 22.0, 79: 21.1,
            80: 20.2, 81: 19.4, 82: 18.5, 83: 17.7, 84: 16.8,
            85: 16.0, 86: 15.2, 87: 14.4, 88: 13.7, 89: 12.9,
            90: 12.2, 91: 11.5, 92: 10.8, 93: 10.1, 94: 9.5,
            95: 8.9, 96: 8.4, 97: 7.8, 98: 7.3, 99: 6.8,
            100: 6.4, 101: 6.0, 102: 5.6, 103: 5.2, 104: 4.9,
            105: 4.6, 106: 4.3, 107: 4.1, 108: 3.9, 109: 3.7,
            110: 3.5, 111: 3.4, 112: 3.3, 113: 3.1, 114: 3.0,
            115: 2.9
        }
    
    def get_contribution_limits(self, tax_year: int, account_type: AccountType) -> Optional[Dict]:
        """Get IRS contribution limits for specific year and account type"""
        limits = self.db.query(IRSContributionLimits).filter(
            IRSContributionLimits.tax_year == tax_year,
            IRSContributionLimits.account_type == account_type
        ).first()
        
        if limits:
            return {
                'regular_limit': limits.regular_limit,
                'catch_up_limit': limits.catch_up_limit,
                'catch_up_age': limits.catch_up_age,
                'income_phase_out_start_single': limits.income_phase_out_start_single,
                'income_phase_out_end_single': limits.income_phase_out_end_single,
                'income_phase_out_start_married': limits.income_phase_out_start_married,
                'income_phase_out_end_married': limits.income_phase_out_end_married,
                'employer_match_limit': limits.employer_match_limit,
                'total_plan_limit': limits.total_plan_limit,
                'hsa_family_limit': limits.hsa_family_limit
            }
        return None
    
    def calculate_available_contribution_room(self, 
                                            user_id: str, 
                                            account_type: AccountType,
                                            tax_year: int,
                                            age: int,
                                            income: Decimal,
                                            filing_status: FilingStatus) -> Dict:
        """Calculate available contribution room considering limits and phase-outs"""
        
        limits = self.get_contribution_limits(tax_year, account_type)
        if not limits:
            return {'error': f'No contribution limits found for {tax_year} {account_type}'}
        
        # Base contribution limit
        base_limit = limits['regular_limit']
        
        # Add catch-up contribution if eligible
        if age >= limits['catch_up_age']:
            base_limit += limits['catch_up_limit']
        
        # Apply income phase-outs for Roth IRA
        if account_type == AccountType.ROTH_IRA:
            if filing_status == FilingStatus.SINGLE:
                phase_out_start = limits['income_phase_out_start_single']
                phase_out_end = limits['income_phase_out_end_single']
            else:
                phase_out_start = limits['income_phase_out_start_married']
                phase_out_end = limits['income_phase_out_end_married']
            
            if income > phase_out_end:
                base_limit = Decimal('0')
            elif income > phase_out_start:
                reduction = (income - phase_out_start) / (phase_out_end - phase_out_start)
                base_limit = base_limit * (Decimal('1') - reduction)
        
        # Get current year contributions
        current_contributions = self.db.query(RetirementContribution).join(
            RetirementAccount
        ).filter(
            RetirementAccount.user_id == user_id,
            RetirementAccount.account_type == account_type,
            RetirementContribution.tax_year == tax_year
        ).all()
        
        total_contributed = sum(c.amount for c in current_contributions)
        available_room = max(Decimal('0'), base_limit - total_contributed)
        
        return {
            'base_limit': limits['regular_limit'],
            'catch_up_limit': limits['catch_up_limit'] if age >= limits['catch_up_age'] else Decimal('0'),
            'total_limit': base_limit,
            'contributed_to_date': total_contributed,
            'available_room': available_room,
            'phase_out_applied': account_type == AccountType.ROTH_IRA and income > phase_out_start
        }
    
    def calculate_employer_match(self, 
                               salary: Decimal,
                               employee_contribution_rate: Decimal,
                               match_formula: str) -> Decimal:
        """Calculate employer 401(k) match based on formula"""
        
        # Parse common match formulas
        # Example: "100% of first 3%, 50% of next 2%"
        total_match = Decimal('0')
        
        if "100% of first" in match_formula and "50% of next" in match_formula:
            # Parse the formula
            parts = match_formula.split(", ")
            
            # First part: "100% of first 3%"
            first_part = parts[0].replace("100% of first ", "").replace("%", "")
            first_threshold = Decimal(first_part) / 100
            
            # Second part: "50% of next 2%"
            second_part = parts[1].replace("50% of next ", "").replace("%", "")
            second_threshold = Decimal(second_part) / 100
            
            # Calculate match
            if employee_contribution_rate >= first_threshold:
                total_match += salary * first_threshold  # 100% match on first portion
                
                if employee_contribution_rate >= (first_threshold + second_threshold):
                    total_match += salary * second_threshold * Decimal('0.5')  # 50% match on second portion
                else:
                    remaining = employee_contribution_rate - first_threshold
                    total_match += salary * remaining * Decimal('0.5')
            else:
                total_match = salary * employee_contribution_rate  # 100% match up to contribution
        
        return total_match
    
    def optimize_contribution_strategy(self,
                                     personal_info: PersonalInfo,
                                     accounts: List[AccountBalance],
                                     available_cash: Decimal,
                                     tax_year: int = 2025) -> ContributionStrategy:
        """Determine optimal contribution strategy across all account types"""
        
        strategy = {}
        total_contribution = Decimal('0')
        total_tax_savings = Decimal('0')
        total_employer_match = Decimal('0')
        
        # Priority order: 1) Employer match, 2) HSA, 3) Traditional vs Roth optimization
        remaining_cash = available_cash
        
        # Step 1: Maximize employer match (free money)
        for account in accounts:
            if account.account_type in [AccountType.TRADITIONAL_401K, AccountType.ROTH_401K]:
                if account.employer_match > 0 and remaining_cash > 0:
                    match_contribution = min(remaining_cash, account.employer_match)
                    strategy[account.account_id] = match_contribution
                    total_contribution += match_contribution
                    total_employer_match += match_contribution  # 1:1 match assumed
                    remaining_cash -= match_contribution
        
        # Step 2: Maximize HSA (triple tax advantage)
        hsa_accounts = [a for a in accounts if a.account_type == AccountType.HSA]
        for account in hsa_accounts:
            if remaining_cash > 0:
                limits = self.get_contribution_limits(tax_year, AccountType.HSA)
                if limits:
                    hsa_limit = limits['regular_limit']
                    if personal_info.current_age >= 55:
                        hsa_limit += limits['catch_up_limit']
                    
                    hsa_contribution = min(remaining_cash, hsa_limit)
                    strategy[account.account_id] = strategy.get(account.account_id, Decimal('0')) + hsa_contribution
                    total_contribution += hsa_contribution
                    total_tax_savings += hsa_contribution * self._get_marginal_tax_rate(personal_info)
                    remaining_cash -= hsa_contribution
        
        # Step 3: Traditional vs Roth optimization based on tax situation
        marginal_rate = self._get_marginal_tax_rate(personal_info)
        expected_retirement_rate = self._estimate_retirement_tax_rate(personal_info, accounts)
        
        # If current tax rate > expected retirement rate, prefer traditional
        # If current tax rate < expected retirement rate, prefer Roth
        prefer_traditional = marginal_rate > expected_retirement_rate
        
        # Allocate remaining funds
        ira_accounts = [a for a in accounts if a.account_type in [AccountType.TRADITIONAL_IRA, AccountType.ROTH_IRA]]
        for account in ira_accounts:
            if remaining_cash > 0:
                limits = self.get_contribution_limits(tax_year, account.account_type)
                if limits:
                    ira_limit = limits['regular_limit']
                    if personal_info.current_age >= limits['catch_up_age']:
                        ira_limit += limits['catch_up_limit']
                    
                    # Apply income phase-outs
                    contribution_room = self.calculate_available_contribution_room(
                        "user_id", account.account_type, tax_year, 
                        personal_info.current_age, personal_info.current_income,
                        personal_info.filing_status
                    )
                    
                    available_limit = min(ira_limit, contribution_room['available_room'])
                    ira_contribution = min(remaining_cash, available_limit)
                    
                    # Prioritize based on tax optimization
                    if ((prefer_traditional and account.account_type == AccountType.TRADITIONAL_IRA) or
                        (not prefer_traditional and account.account_type == AccountType.ROTH_IRA)):
                        strategy[account.account_id] = strategy.get(account.account_id, Decimal('0')) + ira_contribution
                        total_contribution += ira_contribution
                        if account.account_type == AccountType.TRADITIONAL_IRA:
                            total_tax_savings += ira_contribution * marginal_rate
                        remaining_cash -= ira_contribution
        
        # Generate strategy explanation
        explanation = self._generate_contribution_strategy_explanation(
            strategy, total_employer_match, total_tax_savings, prefer_traditional
        )
        
        return ContributionStrategy(
            account_allocations=strategy,
            total_annual_contribution=total_contribution,
            tax_savings=total_tax_savings,
            employer_match_captured=total_employer_match,
            strategy_explanation=explanation
        )
    
    def calculate_retirement_income_need(self,
                                       personal_info: PersonalInfo,
                                       goal: RetirementGoal) -> Dict:
        """Calculate retirement income need with inflation adjustment"""
        
        years_to_retirement = personal_info.retirement_age - personal_info.current_age
        
        # Inflate current income to retirement
        inflated_income = personal_info.current_income * (
            (1 + goal.inflation_rate) ** years_to_retirement
        )
        
        # Apply replacement ratio
        target_income = inflated_income * goal.income_replacement_ratio
        
        # Calculate present value of retirement income stream
        pv_retirement_income = self._present_value_annuity(
            target_income, 
            goal.years_in_retirement,
            goal.inflation_rate  # Real return assumption
        )
        
        return {
            'current_income': personal_info.current_income,
            'inflated_income_at_retirement': inflated_income,
            'target_annual_retirement_income': target_income,
            'total_retirement_need_pv': pv_retirement_income,
            'years_to_retirement': years_to_retirement,
            'years_in_retirement': goal.years_in_retirement
        }
    
    def project_account_growth(self,
                             account: AccountBalance,
                             years: int,
                             annual_contribution: Optional[Decimal] = None) -> List[Dict]:
        """Project account balance growth over time"""
        
        contribution = annual_contribution or account.annual_contribution
        balance = account.current_balance
        projections = []
        
        for year in range(1, years + 1):
            # Add annual contribution at beginning of year
            balance += contribution
            
            # Add employer match if applicable
            if account.account_type in [AccountType.TRADITIONAL_401K, AccountType.ROTH_401K]:
                balance += account.employer_match
            
            # Apply investment growth
            balance *= (1 + account.expected_return)
            
            projections.append({
                'year': year,
                'age': year + 25,  # Assuming starting at 25
                'balance': balance,
                'annual_contribution': contribution,
                'employer_match': account.employer_match if account.account_type in [AccountType.TRADITIONAL_401K, AccountType.ROTH_401K] else Decimal('0')
            })
        
        return projections
    
    def calculate_rmd(self,
                     account_balance: Decimal,
                     age: int) -> RMDCalculation:
        """Calculate Required Minimum Distribution"""
        
        if age < 73:  # RMD age is 73 for those born after 1959
            return RMDCalculation(
                account_id="",
                account_balance=account_balance,
                age=age,
                life_expectancy_factor=Decimal('0'),
                rmd_amount=Decimal('0'),
                tax_owed=Decimal('0')
            )
        
        # Get life expectancy factor
        life_expectancy = Decimal(str(self.rmd_life_expectancy.get(age, 3.0)))
        
        # Calculate RMD
        rmd_amount = account_balance / life_expectancy
        
        # Estimate tax (assume ordinary income tax rate)
        marginal_rate = Decimal('0.22')  # Simplified assumption
        tax_owed = rmd_amount * marginal_rate
        
        return RMDCalculation(
            account_id="",
            account_balance=account_balance,
            age=age,
            life_expectancy_factor=life_expectancy,
            rmd_amount=rmd_amount,
            tax_owed=tax_owed
        )
    
    def analyze_roth_conversion(self,
                              traditional_balance: Decimal,
                              current_age: int,
                              current_tax_rate: Decimal,
                              expected_retirement_tax_rate: Decimal,
                              years_to_retirement: int) -> RothConversionAnalysis:
        """Analyze Roth conversion opportunities"""
        
        # Determine optimal conversion amount (typically fill up lower tax brackets)
        optimal_conversion = self._calculate_optimal_conversion_amount(
            current_tax_rate, expected_retirement_tax_rate
        )
        
        # Calculate tax cost
        tax_cost = optimal_conversion * current_tax_rate
        
        # Calculate lifetime tax savings
        years_in_retirement = 25
        future_value_savings = self._calculate_roth_conversion_savings(
            optimal_conversion, 
            current_tax_rate,
            expected_retirement_tax_rate,
            years_to_retirement,
            years_in_retirement
        )
        
        # Calculate breakeven age
        breakeven_age = current_age + self._calculate_conversion_breakeven_years(
            optimal_conversion, tax_cost, future_value_savings
        )
        
        # Generate conversion timeline
        conversion_timeline = self._generate_conversion_timeline(
            optimal_conversion, years_to_retirement
        )
        
        return RothConversionAnalysis(
            optimal_conversion_amount=optimal_conversion,
            years_to_convert=list(range(current_age, current_age + min(years_to_retirement, 10))),
            tax_cost_of_conversion=tax_cost,
            lifetime_tax_savings=future_value_savings,
            breakeven_age=breakeven_age,
            conversion_timeline=conversion_timeline
        )
    
    def calculate_backdoor_roth_strategy(self,
                                       income: Decimal,
                                       filing_status: FilingStatus,
                                       tax_year: int = 2025) -> Dict:
        """Calculate backdoor Roth IRA strategy for high earners"""
        
        roth_limits = self.get_contribution_limits(tax_year, AccountType.ROTH_IRA)
        if not roth_limits:
            return {'error': 'No Roth IRA limits found'}
        
        # Check if income exceeds Roth IRA limits
        if filing_status == FilingStatus.SINGLE:
            phase_out_end = roth_limits['income_phase_out_end_single']
        else:
            phase_out_end = roth_limits['income_phase_out_end_married']
        
        if income <= phase_out_end:
            return {
                'eligible_for_direct_roth': True,
                'backdoor_roth_needed': False,
                'max_contribution': roth_limits['regular_limit']
            }
        
        # Backdoor Roth strategy
        trad_ira_limits = self.get_contribution_limits(tax_year, AccountType.TRADITIONAL_IRA)
        max_backdoor_contribution = trad_ira_limits['regular_limit']
        
        return {
            'eligible_for_direct_roth': False,
            'backdoor_roth_needed': True,
            'max_backdoor_contribution': max_backdoor_contribution,
            'steps': [
                "1. Contribute to Traditional IRA (non-deductible)",
                "2. Immediately convert to Roth IRA",
                "3. Pay taxes on any earnings during conversion",
                "4. Ensure no other Traditional IRA balances to avoid pro-rata rule"
            ],
            'tax_implications': 'Minimal if converted immediately with no earnings'
        }
    
    def optimize_withdrawal_sequence(self,
                                   accounts: List[AccountBalance],
                                   annual_income_need: Decimal,
                                   years_in_retirement: int,
                                   strategy: WithdrawalStrategy = WithdrawalStrategy.TAX_EFFICIENT) -> WithdrawalPlan:
        """Optimize withdrawal sequence to minimize lifetime taxes"""
        
        if strategy == WithdrawalStrategy.TAX_EFFICIENT:
            return self._tax_efficient_withdrawal_sequence(accounts, annual_income_need, years_in_retirement)
        elif strategy == WithdrawalStrategy.PROPORTIONAL:
            return self._proportional_withdrawal_sequence(accounts, annual_income_need, years_in_retirement)
        else:
            return self._roth_conversion_ladder_strategy(accounts, annual_income_need, years_in_retirement)
    
    def calculate_529_education_projection(self,
                                         current_balance: Decimal,
                                         annual_contribution: Decimal,
                                         years_until_college: int,
                                         expected_return: Decimal = Decimal('0.06'),
                                         education_inflation: Decimal = Decimal('0.05')) -> Dict:
        """Project 529 plan growth and education cost coverage"""
        
        # Project 529 balance
        balance = current_balance
        for year in range(years_until_college):
            balance += annual_contribution
            balance *= (1 + expected_return)
        
        # Estimate future education costs
        current_college_cost = Decimal('50000')  # Average annual cost
        future_college_cost = current_college_cost * ((1 + education_inflation) ** years_until_college)
        total_college_cost = future_college_cost * 4  # 4 years
        
        coverage_ratio = balance / total_college_cost if total_college_cost > 0 else Decimal('0')
        
        return {
            'projected_529_balance': balance,
            'estimated_total_college_cost': total_college_cost,
            'annual_college_cost_future': future_college_cost,
            'coverage_ratio': coverage_ratio,
            'shortfall': max(Decimal('0'), total_college_cost - balance),
            'years_until_college': years_until_college
        }
    
    def _get_marginal_tax_rate(self, personal_info: PersonalInfo) -> Decimal:
        """Calculate marginal tax rate based on income and filing status"""
        
        brackets = self.federal_tax_brackets.get(personal_info.filing_status, self.federal_tax_brackets[FilingStatus.SINGLE])
        
        for bracket in brackets:
            if personal_info.current_income <= bracket.max_income:
                return bracket.rate
        
        return brackets[-1].rate  # Highest bracket
    
    def _estimate_retirement_tax_rate(self, 
                                    personal_info: PersonalInfo, 
                                    accounts: List[AccountBalance]) -> Decimal:
        """Estimate tax rate in retirement based on projected income"""
        
        # Simplified estimation based on account types and Social Security
        total_retirement_balance = sum(a.current_balance for a in accounts)
        estimated_annual_withdrawal = total_retirement_balance * Decimal('0.04')  # 4% rule
        
        # Add estimated Social Security (simplified)
        estimated_ss = personal_info.current_income * Decimal('0.40')  # 40% replacement
        
        total_retirement_income = estimated_annual_withdrawal + estimated_ss
        
        # Use tax brackets to estimate rate
        brackets = self.federal_tax_brackets.get(personal_info.filing_status, self.federal_tax_brackets[FilingStatus.SINGLE])
        
        for bracket in brackets:
            if total_retirement_income <= bracket.max_income:
                return bracket.rate
        
        return brackets[-1].rate
    
    def _present_value_annuity(self, payment: Decimal, periods: int, rate: Decimal) -> Decimal:
        """Calculate present value of annuity"""
        if rate == 0:
            return payment * periods
        return payment * (1 - (1 + rate) ** -periods) / rate
    
    def _calculate_optimal_conversion_amount(self,
                                           current_rate: Decimal,
                                           future_rate: Decimal) -> Decimal:
        """Calculate optimal Roth conversion amount"""
        
        # Simplified: convert enough to fill up current tax bracket
        # This would be more sophisticated in practice
        return Decimal('50000')  # Example amount
    
    def _calculate_roth_conversion_savings(self,
                                         conversion_amount: Decimal,
                                         current_rate: Decimal,
                                         future_rate: Decimal,
                                         years_to_retirement: int,
                                         years_in_retirement: int) -> Decimal:
        """Calculate lifetime tax savings from Roth conversion"""
        
        # Growth of converted amount
        future_value = conversion_amount * ((Decimal('1.07')) ** (years_to_retirement + years_in_retirement // 2))
        
        # Tax savings
        tax_savings = future_value * (future_rate - current_rate)
        
        return max(Decimal('0'), tax_savings)
    
    def _calculate_conversion_breakeven_years(self,
                                            conversion_amount: Decimal,
                                            tax_cost: Decimal,
                                            future_savings: Decimal) -> int:
        """Calculate years to breakeven on Roth conversion"""
        
        if future_savings <= tax_cost:
            return 50  # Never breaks even
        
        # Simplified calculation
        return int(tax_cost / ((future_savings - tax_cost) / 20))
    
    def _generate_conversion_timeline(self,
                                    optimal_amount: Decimal,
                                    years_available: int) -> List[Dict[str, Any]]:
        """Generate Roth conversion timeline"""
        
        annual_conversion = optimal_amount / min(years_available, 10)
        timeline = []
        
        for year in range(min(years_available, 10)):
            timeline.append({
                'year': year + 1,
                'conversion_amount': annual_conversion,
                'tax_cost': annual_conversion * Decimal('0.22'),
                'cumulative_converted': annual_conversion * (year + 1)
            })
        
        return timeline
    
    def _tax_efficient_withdrawal_sequence(self,
                                         accounts: List[AccountBalance],
                                         annual_need: Decimal,
                                         years: int) -> WithdrawalPlan:
        """Calculate tax-efficient withdrawal sequence"""
        
        # Standard tax-efficient order:
        # 1. Taxable accounts first
        # 2. Tax-deferred accounts (Traditional IRA/401k)
        # 3. Tax-free accounts last (Roth)
        
        withdrawals = []
        total_taxes = Decimal('0')
        account_balances = {a.account_id: a.current_balance for a in accounts}
        
        for year in range(years):
            annual_withdrawal = {
                'year': year + 1,
                'withdrawals': {},
                'total_withdrawn': Decimal('0'),
                'taxes_paid': Decimal('0')
            }
            
            remaining_need = annual_need
            
            # Withdraw from accounts in tax-efficient order
            for account in sorted(accounts, key=lambda x: self._get_withdrawal_priority(x.tax_treatment)):
                if remaining_need > 0 and account_balances[account.account_id] > 0:
                    withdrawal = min(remaining_need, account_balances[account.account_id])
                    annual_withdrawal['withdrawals'][account.account_id] = withdrawal
                    annual_withdrawal['total_withdrawn'] += withdrawal
                    
                    # Calculate taxes
                    if account.tax_treatment == TaxTreatment.TAX_DEFERRED:
                        tax = withdrawal * Decimal('0.22')  # Simplified rate
                        annual_withdrawal['taxes_paid'] += tax
                        total_taxes += tax
                    
                    account_balances[account.account_id] -= withdrawal
                    remaining_need -= withdrawal
            
            withdrawals.append(annual_withdrawal)
        
        return WithdrawalPlan(
            annual_withdrawals=withdrawals,
            total_taxes_paid=total_taxes,
            after_tax_income=annual_need * years - total_taxes,
            account_balances_at_death=account_balances,
            strategy_explanation="Tax-efficient withdrawal sequence: taxable first, then tax-deferred, then tax-free last"
        )
    
    def _proportional_withdrawal_sequence(self,
                                        accounts: List[AccountBalance],
                                        annual_need: Decimal,
                                        years: int) -> WithdrawalPlan:
        """Calculate proportional withdrawal sequence"""
        
        total_balance = sum(a.current_balance for a in accounts)
        withdrawals = []
        total_taxes = Decimal('0')
        
        for year in range(years):
            annual_withdrawal = {
                'year': year + 1,
                'withdrawals': {},
                'total_withdrawn': Decimal('0'),
                'taxes_paid': Decimal('0')
            }
            
            for account in accounts:
                proportion = account.current_balance / total_balance if total_balance > 0 else Decimal('0')
                withdrawal = annual_need * proportion
                annual_withdrawal['withdrawals'][account.account_id] = withdrawal
                annual_withdrawal['total_withdrawn'] += withdrawal
                
                # Calculate taxes
                if account.tax_treatment == TaxTreatment.TAX_DEFERRED:
                    tax = withdrawal * Decimal('0.22')
                    annual_withdrawal['taxes_paid'] += tax
                    total_taxes += tax
            
            withdrawals.append(annual_withdrawal)
        
        return WithdrawalPlan(
            annual_withdrawals=withdrawals,
            total_taxes_paid=total_taxes,
            after_tax_income=annual_need * years - total_taxes,
            account_balances_at_death={},
            strategy_explanation="Proportional withdrawal from all accounts based on current balances"
        )
    
    def _roth_conversion_ladder_strategy(self,
                                       accounts: List[AccountBalance],
                                       annual_need: Decimal,
                                       years: int) -> WithdrawalPlan:
        """Calculate Roth conversion ladder strategy"""
        
        # This is a simplified version of the conversion ladder strategy
        return WithdrawalPlan(
            annual_withdrawals=[],
            total_taxes_paid=Decimal('0'),
            after_tax_income=Decimal('0'),
            account_balances_at_death={},
            strategy_explanation="Roth conversion ladder strategy for early retirement"
        )
    
    def _get_withdrawal_priority(self, tax_treatment: TaxTreatment) -> int:
        """Get withdrawal priority order (lower number = withdraw first)"""
        priority_map = {
            TaxTreatment.AFTER_TAX: 1,  # Taxable accounts first
            TaxTreatment.TAX_DEFERRED: 2,  # Traditional accounts second
            TaxTreatment.TAX_FREE: 3,  # Roth accounts last
            TaxTreatment.TRIPLE_TAX_ADVANTAGE: 4  # HSA last (best for medical expenses)
        }
        return priority_map.get(tax_treatment, 5)
    
    def _generate_contribution_strategy_explanation(self,
                                                  strategy: Dict[str, Decimal],
                                                  employer_match: Decimal,
                                                  tax_savings: Decimal,
                                                  prefer_traditional: bool) -> str:
        """Generate explanation for contribution strategy"""
        
        explanation = "Optimal contribution strategy:\n"
        explanation += f"• Captured ${employer_match:,.2f} in employer matching\n"
        explanation += f"• Generated ${tax_savings:,.2f} in tax savings\n"
        
        if prefer_traditional:
            explanation += "• Prioritized traditional accounts due to current high tax rate\n"
        else:
            explanation += "• Prioritized Roth accounts for tax-free growth\n"
        
        explanation += f"• Total annual contributions: ${sum(strategy.values()):,.2f}"
        
        return explanation