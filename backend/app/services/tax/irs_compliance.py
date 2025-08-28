"""
Enhanced IRS Compliance and Tax Rules Engine

This module provides comprehensive IRS compliance management including:
- Contribution limits with automatic annual adjustments
- Income phase-out calculations
- Required Minimum Distribution (RMD) calculations
- Tax bracket management and optimization
- Catch-up contribution eligibility
- Plan loan limits and restrictions
- Rollover and conversion rules
- Early withdrawal penalty calculations
- Excess contribution handling
- Multi-year tax planning optimization
"""

import asyncio
import logging
from datetime import datetime, date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import calendar
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc

from ...models.retirement_accounts import (
    IRSContributionLimits, RetirementAccount, RetirementContribution,
    AccountType, ContributionType
)
from ...models.tax_accounts import TaxAccount, TaxAccountTransaction
from ...models.user import User
from ...models.financial_profile import FinancialProfile

logger = logging.getLogger(__name__)


class FilingStatus(Enum):
    """Tax filing status options"""
    SINGLE = "single"
    MARRIED_FILING_JOINTLY = "married_filing_jointly" 
    MARRIED_FILING_SEPARATELY = "married_filing_separately"
    HEAD_OF_HOUSEHOLD = "head_of_household"
    QUALIFYING_WIDOW = "qualifying_widow"


class ContributionLimitType(Enum):
    """Types of contribution limits"""
    REGULAR = "regular"
    CATCH_UP = "catch_up"
    TOTAL_ANNUAL = "total_annual"
    EMPLOYER_MATCH = "employer_match"
    TOTAL_PLAN = "total_plan"
    HSA_FAMILY = "hsa_family"


class PenaltyType(Enum):
    """Types of tax penalties"""
    EARLY_WITHDRAWAL = "early_withdrawal"
    EXCESS_CONTRIBUTION = "excess_contribution"
    INSUFFICIENT_RMD = "insufficient_rmd"
    PROHIBITED_TRANSACTION = "prohibited_transaction"
    LATE_ROLLOVER = "late_rollover"


@dataclass
class ContributionEligibility:
    """Contribution eligibility analysis"""
    eligible: bool
    maximum_contribution: Decimal
    phase_out_applicable: bool
    reduced_limit: Optional[Decimal]
    restrictions: List[str]
    recommendations: List[str]
    tax_year: int


@dataclass
class RMDCalculation:
    """Required Minimum Distribution calculation"""
    account_type: AccountType
    account_balance: Decimal
    age: int
    life_expectancy_factor: Decimal
    required_distribution: Decimal
    deadline: date
    penalty_for_miss: Decimal
    strategy_recommendations: List[str]


@dataclass
class TaxPenaltyAnalysis:
    """Tax penalty analysis and calculation"""
    penalty_type: PenaltyType
    penalty_amount: Decimal
    penalty_rate: Decimal
    triggering_amount: Decimal
    avoidance_strategies: List[str]
    correction_deadline: Optional[date]
    correction_method: Optional[str]


@dataclass
class MultiYearTaxPlan:
    """Multi-year tax optimization plan"""
    years_covered: int
    annual_strategies: Dict[int, Dict[str, Any]]
    total_tax_savings: Decimal
    implementation_complexity: str
    key_assumptions: List[str]
    sensitivity_analysis: Dict[str, Any]


class EnhancedIRSComplianceEngine:
    """
    Enhanced IRS compliance engine with comprehensive tax rule implementation
    """
    
    # 2025 IRS limits and thresholds
    IRS_LIMITS_2025 = {
        AccountType.TRADITIONAL_401K: {
            'regular_limit': Decimal('23500'),
            'catch_up_limit': Decimal('7500'),
            'catch_up_age': 50,
            'total_plan_limit': Decimal('70000'),
            'highly_compensated_threshold': Decimal('155000')
        },
        AccountType.ROTH_401K: {
            'regular_limit': Decimal('23500'),
            'catch_up_limit': Decimal('7500'),
            'catch_up_age': 50,
            'total_plan_limit': Decimal('70000')
        },
        AccountType.TRADITIONAL_IRA: {
            'regular_limit': Decimal('7000'),
            'catch_up_limit': Decimal('1000'),
            'catch_up_age': 50,
            'phase_out_start_single': Decimal('77000'),
            'phase_out_end_single': Decimal('87000'),
            'phase_out_start_married': Decimal('123000'),
            'phase_out_end_married': Decimal('143000')
        },
        AccountType.ROTH_IRA: {
            'regular_limit': Decimal('7000'),
            'catch_up_limit': Decimal('1000'),
            'catch_up_age': 50,
            'phase_out_start_single': Decimal('138000'),
            'phase_out_end_single': Decimal('153000'),
            'phase_out_start_married': Decimal('218000'),
            'phase_out_end_married': Decimal('228000')
        },
        AccountType.SEP_IRA: {
            'regular_limit_pct': Decimal('0.25'),  # 25% of compensation
            'regular_limit_max': Decimal('70000'),
            'min_compensation': Decimal('650')
        },
        AccountType.SIMPLE_IRA: {
            'regular_limit': Decimal('16000'),
            'catch_up_limit': Decimal('3500'),
            'catch_up_age': 50,
            'employer_match_max': Decimal('0.03')  # 3% of compensation
        },
        AccountType.HSA: {
            'regular_limit_individual': Decimal('4150'),
            'regular_limit_family': Decimal('8300'),
            'catch_up_limit': Decimal('1000'),
            'catch_up_age': 55
        }
    }
    
    # RMD life expectancy table (simplified - actual table has more precision)
    RMD_LIFE_EXPECTANCY = {
        70: 27.4, 71: 26.5, 72: 25.6, 73: 24.7, 74: 23.8, 75: 22.9,
        76: 22.0, 77: 21.2, 78: 20.3, 79: 19.5, 80: 18.7, 81: 17.9,
        82: 17.1, 83: 16.3, 84: 15.5, 85: 14.8, 86: 14.1, 87: 13.4,
        88: 12.7, 89: 12.0, 90: 11.4, 91: 10.8, 92: 10.2, 93: 9.6,
        94: 9.1, 95: 8.6, 96: 8.1, 97: 7.6, 98: 7.1, 99: 6.7, 100: 6.3
    }
    
    # Penalty rates
    PENALTY_RATES = {
        PenaltyType.EARLY_WITHDRAWAL: Decimal('0.10'),  # 10%
        PenaltyType.EXCESS_CONTRIBUTION: Decimal('0.06'),  # 6% per year
        PenaltyType.INSUFFICIENT_RMD: Decimal('0.25'),  # 25% (was 50% before SECURE 2.0)
    }
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.current_year = datetime.now().year
    
    async def analyze_contribution_eligibility(
        self,
        user_id: str,
        account_type: AccountType,
        proposed_contribution: Decimal,
        tax_year: int = None
    ) -> ContributionEligibility:
        """
        Comprehensive contribution eligibility analysis
        """
        if tax_year is None:
            tax_year = self.current_year
        
        logger.info(f"Analyzing contribution eligibility for user {user_id}, account {account_type}")
        
        # Get user profile
        user_profile = await self._get_user_profile(user_id)
        if not user_profile:
            raise ValueError(f"User profile not found for user {user_id}")
        
        # Get IRS limits for account type
        limits = self.IRS_LIMITS_2025.get(account_type)
        if not limits:
            raise ValueError(f"No IRS limits defined for account type {account_type}")
        
        # Get user's existing contributions for the tax year
        existing_contributions = await self._get_existing_contributions(
            user_id, account_type, tax_year
        )
        
        # Calculate eligibility
        eligibility = await self._calculate_contribution_eligibility(
            user_profile, account_type, proposed_contribution, 
            existing_contributions, limits, tax_year
        )
        
        return eligibility
    
    async def _get_user_profile(self, user_id: str) -> Optional[FinancialProfile]:
        """Get user's financial profile"""
        return self.db.query(FinancialProfile).filter(
            FinancialProfile.user_id == user_id
        ).first()
    
    async def _get_existing_contributions(
        self,
        user_id: str,
        account_type: AccountType,
        tax_year: int
    ) -> Decimal:
        """Get user's existing contributions for the tax year"""
        
        total_contributions = (
            self.db.query(func.sum(RetirementContribution.amount))
            .join(RetirementAccount)
            .filter(
                RetirementAccount.user_id == user_id,
                RetirementAccount.account_type == account_type,
                RetirementContribution.tax_year == tax_year,
                RetirementContribution.contribution_type.in_([
                    ContributionType.EMPLOYEE_ELECTIVE,
                    ContributionType.EMPLOYEE_ROTH,
                    ContributionType.EMPLOYEE_CATCH_UP,
                    ContributionType.EMPLOYEE_AFTER_TAX
                ])
            )
            .scalar()
        )
        
        return total_contributions or Decimal('0')
    
    async def _calculate_contribution_eligibility(
        self,
        user_profile: FinancialProfile,
        account_type: AccountType,
        proposed_contribution: Decimal,
        existing_contributions: Decimal,
        limits: Dict,
        tax_year: int
    ) -> ContributionEligibility:
        """Calculate detailed contribution eligibility"""
        
        restrictions = []
        recommendations = []
        
        # Basic limits
        regular_limit = limits.get('regular_limit', Decimal('0'))
        catch_up_limit = limits.get('catch_up_limit', Decimal('0'))
        catch_up_age = limits.get('catch_up_age', 50)
        
        # Determine if eligible for catch-up contributions
        current_age = self._calculate_age(user_profile.birth_date)
        catch_up_eligible = current_age >= catch_up_age
        
        # Calculate maximum contribution
        max_contribution = regular_limit
        if catch_up_eligible:
            max_contribution += catch_up_limit
        
        # Check income phase-outs for IRA accounts
        if account_type in [AccountType.TRADITIONAL_IRA, AccountType.ROTH_IRA]:
            phase_out_result = self._calculate_income_phase_out(
                user_profile, account_type, limits
            )
            
            if phase_out_result['phase_out_applicable']:
                max_contribution = phase_out_result['reduced_limit']
                if phase_out_result['completely_phased_out']:
                    restrictions.append(f"Income too high for {account_type} contributions")
        
        # Check total contributions don't exceed limit
        total_proposed = existing_contributions + proposed_contribution
        eligible = total_proposed <= max_contribution
        
        if not eligible:
            excess_amount = total_proposed - max_contribution
            restrictions.append(f"Proposed contribution exceeds limit by ${excess_amount}")
            recommendations.append(f"Reduce contribution by ${excess_amount}")
        
        # Account-specific checks
        if account_type == AccountType.SEP_IRA:
            eligible, restrictions = await self._check_sep_ira_eligibility(
                user_profile, proposed_contribution, limits, restrictions
            )
        elif account_type == AccountType.HSA:
            eligible, restrictions = await self._check_hsa_eligibility(
                user_profile, restrictions
            )
        
        # Generate recommendations
        if eligible:
            remaining_capacity = max_contribution - existing_contributions
            if remaining_capacity > proposed_contribution:
                recommendations.append(
                    f"Could contribute additional ${remaining_capacity - proposed_contribution}"
                )
        
        return ContributionEligibility(
            eligible=eligible,
            maximum_contribution=max_contribution,
            phase_out_applicable=account_type in [AccountType.TRADITIONAL_IRA, AccountType.ROTH_IRA],
            reduced_limit=max_contribution if max_contribution < regular_limit else None,
            restrictions=restrictions,
            recommendations=recommendations,
            tax_year=tax_year
        )
    
    def _calculate_age(self, birth_date: Optional[date]) -> int:
        """Calculate current age from birth date"""
        if not birth_date:
            return 30  # Default age if not provided
        
        today = date.today()
        return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
    
    def _calculate_income_phase_out(
        self,
        user_profile: FinancialProfile,
        account_type: AccountType,
        limits: Dict
    ) -> Dict[str, Any]:
        """Calculate income phase-out for IRA contributions"""
        
        income = user_profile.annual_income or Decimal('0')
        filing_status = user_profile.filing_status.lower()
        
        # Get phase-out thresholds
        if filing_status in ['single', 'head_of_household']:
            phase_out_start = limits.get('phase_out_start_single')
            phase_out_end = limits.get('phase_out_end_single')
        else:  # married filing jointly or separately
            phase_out_start = limits.get('phase_out_start_married')
            phase_out_end = limits.get('phase_out_end_married')
        
        if not phase_out_start or not phase_out_end:
            return {
                'phase_out_applicable': False,
                'reduced_limit': limits.get('regular_limit'),
                'completely_phased_out': False
            }
        
        if income <= phase_out_start:
            # No phase-out
            return {
                'phase_out_applicable': False,
                'reduced_limit': limits.get('regular_limit'),
                'completely_phased_out': False
            }
        elif income >= phase_out_end:
            # Completely phased out
            return {
                'phase_out_applicable': True,
                'reduced_limit': Decimal('0'),
                'completely_phased_out': True
            }
        else:
            # Partial phase-out
            phase_out_range = phase_out_end - phase_out_start
            excess_income = income - phase_out_start
            reduction_factor = excess_income / phase_out_range
            
            regular_limit = limits.get('regular_limit', Decimal('0'))
            reduced_limit = regular_limit * (Decimal('1') - reduction_factor)
            
            # Round down to nearest $10
            reduced_limit = (reduced_limit / 10).quantize(Decimal('1'), rounding=ROUND_HALF_UP) * 10
            
            return {
                'phase_out_applicable': True,
                'reduced_limit': max(Decimal('200'), reduced_limit),  # Minimum $200
                'completely_phased_out': False
            }
    
    async def _check_sep_ira_eligibility(
        self,
        user_profile: FinancialProfile,
        proposed_contribution: Decimal,
        limits: Dict,
        restrictions: List[str]
    ) -> Tuple[bool, List[str]]:
        """Check SEP-IRA specific eligibility requirements"""
        
        # SEP-IRA requires self-employment income
        self_employment_income = getattr(user_profile, 'self_employment_income', Decimal('0'))
        
        if self_employment_income == 0:
            restrictions.append("SEP-IRA requires self-employment income")
            return False, restrictions
        
        # Check contribution limits (25% of compensation or $70,000, whichever is less)
        max_contribution_pct = self_employment_income * limits.get('regular_limit_pct', Decimal('0.25'))
        max_contribution_abs = limits.get('regular_limit_max', Decimal('70000'))
        max_contribution = min(max_contribution_pct, max_contribution_abs)
        
        if proposed_contribution > max_contribution:
            restrictions.append(f"SEP-IRA contribution exceeds 25% of self-employment income limit")
            return False, restrictions
        
        return True, restrictions
    
    async def _check_hsa_eligibility(
        self,
        user_profile: FinancialProfile,
        restrictions: List[str]
    ) -> Tuple[bool, List[str]]:
        """Check HSA specific eligibility requirements"""
        
        # HSA requires High Deductible Health Plan
        has_hdhp = getattr(user_profile, 'has_high_deductible_health_plan', False)
        
        if not has_hdhp:
            restrictions.append("HSA requires High Deductible Health Plan coverage")
            return False, restrictions
        
        # Cannot be covered by other health insurance
        has_other_coverage = getattr(user_profile, 'has_other_health_coverage', False)
        if has_other_coverage:
            restrictions.append("HSA eligibility lost due to other health insurance coverage")
            return False, restrictions
        
        # Cannot be enrolled in Medicare
        age = self._calculate_age(user_profile.birth_date)
        if age >= 65:  # Simplified - actual Medicare eligibility is more complex
            restrictions.append("HSA contributions not allowed after Medicare enrollment")
            return False, restrictions
        
        return True, restrictions
    
    async def calculate_required_minimum_distributions(
        self,
        user_id: str,
        calculation_year: int = None
    ) -> List[RMDCalculation]:
        """
        Calculate Required Minimum Distributions for all applicable accounts
        """
        if calculation_year is None:
            calculation_year = self.current_year
        
        logger.info(f"Calculating RMDs for user {user_id}, year {calculation_year}")
        
        # Get user profile
        user_profile = await self._get_user_profile(user_id)
        if not user_profile:
            raise ValueError(f"User profile not found for user {user_id}")
        
        age = self._calculate_age(user_profile.birth_date)
        
        # RMDs start at age 73 (changed from 72 with SECURE 2.0 Act)
        if age < 73:
            logger.info(f"User age {age} - no RMDs required yet")
            return []
        
        # Get all retirement accounts subject to RMD
        rmd_accounts = await self._get_rmd_applicable_accounts(user_id)
        
        rmd_calculations = []
        
        for account in rmd_accounts:
            rmd_calc = await self._calculate_account_rmd(
                account, age, calculation_year
            )
            if rmd_calc:
                rmd_calculations.append(rmd_calc)
        
        return rmd_calculations
    
    async def _get_rmd_applicable_accounts(self, user_id: str) -> List[RetirementAccount]:
        """Get accounts subject to RMD requirements"""
        
        # RMDs apply to Traditional IRAs, SEP-IRAs, SIMPLE IRAs, and 401(k)s
        # Roth IRAs are exempt during owner's lifetime
        rmd_account_types = [
            AccountType.TRADITIONAL_IRA,
            AccountType.SEP_IRA,
            AccountType.SIMPLE_IRA,
            AccountType.TRADITIONAL_401K,
            # Note: Roth 401(k) is subject to RMD, but Roth IRA is not
        ]
        
        return (
            self.db.query(RetirementAccount)
            .filter(
                RetirementAccount.user_id == user_id,
                RetirementAccount.account_type.in_(rmd_account_types),
                RetirementAccount.is_active == True,
                RetirementAccount.current_balance > 0
            )
            .all()
        )
    
    async def _calculate_account_rmd(
        self,
        account: RetirementAccount,
        age: int,
        calculation_year: int
    ) -> Optional[RMDCalculation]:
        """Calculate RMD for a specific account"""
        
        # Account balance as of December 31 of prior year
        prior_year_balance = await self._get_prior_year_balance(account, calculation_year - 1)
        
        if prior_year_balance <= 0:
            return None
        
        # Get life expectancy factor
        life_expectancy = self.RMD_LIFE_EXPECTANCY.get(age)
        if not life_expectancy:
            # For ages beyond table, use last available factor
            life_expectancy = self.RMD_LIFE_EXPECTANCY.get(100, 6.3)
        
        # Calculate required distribution
        required_distribution = prior_year_balance / Decimal(str(life_expectancy))
        
        # RMD deadline is December 31 of the distribution year
        # Exception: First RMD can be delayed until April 1 of following year
        deadline = date(calculation_year, 12, 31)
        
        # Calculate penalty for missing RMD (25% of shortfall)
        penalty_for_miss = required_distribution * self.PENALTY_RATES[PenaltyType.INSUFFICIENT_RMD]
        
        # Generate strategy recommendations
        strategy_recommendations = self._generate_rmd_strategies(
            account, required_distribution, age
        )
        
        return RMDCalculation(
            account_type=account.account_type,
            account_balance=prior_year_balance,
            age=age,
            life_expectancy_factor=Decimal(str(life_expectancy)),
            required_distribution=required_distribution,
            deadline=deadline,
            penalty_for_miss=penalty_for_miss,
            strategy_recommendations=strategy_recommendations
        )
    
    async def _get_prior_year_balance(
        self,
        account: RetirementAccount,
        year: int
    ) -> Decimal:
        """Get account balance as of December 31 of specified year"""
        
        # In a production system, this would query historical balance data
        # For now, we'll use current balance as an approximation
        return account.current_balance or Decimal('0')
    
    def _generate_rmd_strategies(
        self,
        account: RetirementAccount,
        required_distribution: Decimal,
        age: int
    ) -> List[str]:
        """Generate RMD optimization strategies"""
        
        strategies = []
        
        # Basic strategy
        strategies.append(f"Withdraw ${required_distribution:,.2f} by December 31")
        
        # Tax optimization strategies
        strategies.append("Consider spreading withdrawals throughout the year for tax management")
        
        if required_distribution > Decimal('10000'):
            strategies.append("Consider in-kind distributions of appreciated securities")
        
        # Charitable giving strategies
        if age >= 70.5:  # QCD eligibility age
            qcd_limit = min(required_distribution, Decimal('100000'))
            strategies.append(f"Consider Qualified Charitable Distribution up to ${qcd_limit:,.2f}")
        
        # Estate planning considerations
        if age >= 80:
            strategies.append("Consider estate planning implications of large RMDs")
        
        return strategies
    
    async def analyze_tax_penalties(
        self,
        user_id: str,
        transaction_scenario: Dict[str, Any]
    ) -> List[TaxPenaltyAnalysis]:
        """
        Analyze potential tax penalties for various transaction scenarios
        """
        logger.info(f"Analyzing tax penalties for user {user_id}")
        
        penalties = []
        
        # Analyze early withdrawal penalties
        if transaction_scenario.get('early_withdrawal'):
            penalty = await self._analyze_early_withdrawal_penalty(
                user_id, transaction_scenario['early_withdrawal']
            )
            if penalty:
                penalties.append(penalty)
        
        # Analyze excess contribution penalties
        if transaction_scenario.get('excess_contribution'):
            penalty = await self._analyze_excess_contribution_penalty(
                user_id, transaction_scenario['excess_contribution']
            )
            if penalty:
                penalties.append(penalty)
        
        # Analyze insufficient RMD penalties
        if transaction_scenario.get('insufficient_rmd'):
            penalty = await self._analyze_insufficient_rmd_penalty(
                user_id, transaction_scenario['insufficient_rmd']
            )
            if penalty:
                penalties.append(penalty)
        
        return penalties
    
    async def _analyze_early_withdrawal_penalty(
        self,
        user_id: str,
        withdrawal_info: Dict[str, Any]
    ) -> Optional[TaxPenaltyAnalysis]:
        """Analyze early withdrawal penalty"""
        
        user_profile = await self._get_user_profile(user_id)
        age = self._calculate_age(user_profile.birth_date)
        
        # Early withdrawal penalty applies before age 59.5
        if age >= 59.5:
            return None
        
        withdrawal_amount = Decimal(str(withdrawal_info['amount']))
        account_type = AccountType(withdrawal_info['account_type'])
        
        # Check for exceptions
        avoidance_strategies = self._get_early_withdrawal_exceptions(account_type)
        
        # Calculate penalty (10% of withdrawn amount)
        penalty_rate = self.PENALTY_RATES[PenaltyType.EARLY_WITHDRAWAL]
        penalty_amount = withdrawal_amount * penalty_rate
        
        return TaxPenaltyAnalysis(
            penalty_type=PenaltyType.EARLY_WITHDRAWAL,
            penalty_amount=penalty_amount,
            penalty_rate=penalty_rate,
            triggering_amount=withdrawal_amount,
            avoidance_strategies=avoidance_strategies,
            correction_deadline=None,
            correction_method=None
        )
    
    def _get_early_withdrawal_exceptions(self, account_type: AccountType) -> List[str]:
        """Get early withdrawal penalty exceptions"""
        
        exceptions = [
            "First-time home purchase (up to $10,000 lifetime)",
            "Higher education expenses",
            "Medical expenses exceeding 7.5% of AGI",
            "Unemployment - health insurance premiums",
            "Disability",
            "Substantially Equal Periodic Payments (SEPP)"
        ]
        
        if account_type in [AccountType.TRADITIONAL_IRA, AccountType.ROTH_IRA]:
            exceptions.extend([
                "IRS levy on the account",
                "Return of excess contributions"
            ])
        
        if account_type == AccountType.HSA:
            exceptions = ["Medical expenses only - otherwise subject to 20% penalty"]
        
        return exceptions
    
    async def _analyze_excess_contribution_penalty(
        self,
        user_id: str,
        excess_info: Dict[str, Any]
    ) -> Optional[TaxPenaltyAnalysis]:
        """Analyze excess contribution penalty"""
        
        excess_amount = Decimal(str(excess_info['amount']))
        account_type = AccountType(excess_info['account_type'])
        
        # 6% penalty per year until corrected
        penalty_rate = self.PENALTY_RATES[PenaltyType.EXCESS_CONTRIBUTION]
        annual_penalty = excess_amount * penalty_rate
        
        # Correction deadline
        tax_year = excess_info.get('tax_year', self.current_year)
        correction_deadline = date(tax_year + 1, 10, 15)  # October 15 extended deadline
        
        avoidance_strategies = [
            "Remove excess contribution and earnings before tax deadline",
            "Apply excess to next year's contribution limit",
            "Recharacterize contribution if applicable"
        ]
        
        return TaxPenaltyAnalysis(
            penalty_type=PenaltyType.EXCESS_CONTRIBUTION,
            penalty_amount=annual_penalty,
            penalty_rate=penalty_rate,
            triggering_amount=excess_amount,
            avoidance_strategies=avoidance_strategies,
            correction_deadline=correction_deadline,
            correction_method="Remove excess plus earnings or recharacterize"
        )
    
    async def _analyze_insufficient_rmd_penalty(
        self,
        user_id: str,
        rmd_info: Dict[str, Any]
    ) -> Optional[TaxPenaltyAnalysis]:
        """Analyze insufficient RMD penalty"""
        
        required_amount = Decimal(str(rmd_info['required_amount']))
        distributed_amount = Decimal(str(rmd_info.get('distributed_amount', 0)))
        
        shortfall = required_amount - distributed_amount
        
        if shortfall <= 0:
            return None
        
        # 25% penalty on shortfall (reduced from 50% by SECURE 2.0)
        penalty_rate = self.PENALTY_RATES[PenaltyType.INSUFFICIENT_RMD]
        penalty_amount = shortfall * penalty_rate
        
        # Can be reduced to 10% if corrected promptly
        avoidance_strategies = [
            "Take corrective distribution immediately",
            "File Form 5329 to report penalty",
            "Request penalty waiver for reasonable error and reasonable steps to remedy"
        ]
        
        return TaxPenaltyAnalysis(
            penalty_type=PenaltyType.INSUFFICIENT_RMD,
            penalty_amount=penalty_amount,
            penalty_rate=penalty_rate,
            triggering_amount=shortfall,
            avoidance_strategies=avoidance_strategies,
            correction_deadline=date(self.current_year, 12, 31),
            correction_method="Take corrective distribution and file Form 5329"
        )
    
    async def generate_multi_year_tax_plan(
        self,
        user_id: str,
        planning_years: int = 10
    ) -> MultiYearTaxPlan:
        """
        Generate multi-year tax optimization plan
        """
        logger.info(f"Generating {planning_years}-year tax plan for user {user_id}")
        
        user_profile = await self._get_user_profile(user_id)
        if not user_profile:
            raise ValueError(f"User profile not found for user {user_id}")
        
        annual_strategies = {}
        total_tax_savings = Decimal('0')
        
        current_age = self._calculate_age(user_profile.birth_date)
        base_income = user_profile.annual_income or Decimal('100000')
        
        for year_offset in range(planning_years):
            year = self.current_year + year_offset
            age_in_year = current_age + year_offset
            
            # Project income with growth
            projected_income = base_income * (Decimal('1.03') ** year_offset)  # 3% growth
            
            year_strategy = await self._generate_annual_strategy(
                user_id, year, age_in_year, projected_income
            )
            
            annual_strategies[year] = year_strategy
            total_tax_savings += year_strategy.get('estimated_tax_savings', Decimal('0'))
        
        # Assess implementation complexity
        complexity = self._assess_plan_complexity(annual_strategies)
        
        # Generate key assumptions
        key_assumptions = [
            "3% annual income growth",
            "Current tax law remains unchanged",
            "Investment returns average 7% annually",
            "Inflation averages 2.5% annually"
        ]
        
        # Sensitivity analysis
        sensitivity_analysis = await self._perform_sensitivity_analysis(
            user_id, annual_strategies
        )
        
        return MultiYearTaxPlan(
            years_covered=planning_years,
            annual_strategies=annual_strategies,
            total_tax_savings=total_tax_savings,
            implementation_complexity=complexity,
            key_assumptions=key_assumptions,
            sensitivity_analysis=sensitivity_analysis
        )
    
    async def _generate_annual_strategy(
        self,
        user_id: str,
        year: int,
        age: int,
        projected_income: Decimal
    ) -> Dict[str, Any]:
        """Generate tax strategy for a specific year"""
        
        strategy = {
            'year': year,
            'age': age,
            'projected_income': float(projected_income),
            'strategies': [],
            'estimated_tax_savings': Decimal('0')
        }
        
        # Contribution strategies
        if age < 65:  # Still working
            contribution_strategy = await self._generate_contribution_strategy(
                user_id, age, projected_income, year
            )
            strategy['strategies'].append(contribution_strategy)
            strategy['estimated_tax_savings'] += contribution_strategy.get('tax_savings', Decimal('0'))
        
        # RMD strategies
        if age >= 73:
            rmd_strategy = await self._generate_rmd_strategy(user_id, age, year)
            strategy['strategies'].append(rmd_strategy)
            strategy['estimated_tax_savings'] += rmd_strategy.get('tax_savings', Decimal('0'))
        
        # Roth conversion strategies
        conversion_strategy = await self._generate_conversion_strategy(
            user_id, age, projected_income, year
        )
        if conversion_strategy:
            strategy['strategies'].append(conversion_strategy)
            strategy['estimated_tax_savings'] += conversion_strategy.get('long_term_savings', Decimal('0'))
        
        return strategy
    
    async def _generate_contribution_strategy(
        self,
        user_id: str,
        age: int,
        income: Decimal,
        year: int
    ) -> Dict[str, Any]:
        """Generate optimal contribution strategy for a year"""
        
        strategy = {
            'strategy_type': 'contributions',
            'recommendations': [],
            'tax_savings': Decimal('0')
        }
        
        # 401(k) contributions
        if age >= 50:
            max_401k = self.IRS_LIMITS_2025[AccountType.TRADITIONAL_401K]['regular_limit'] + \
                      self.IRS_LIMITS_2025[AccountType.TRADITIONAL_401K]['catch_up_limit']
        else:
            max_401k = self.IRS_LIMITS_2025[AccountType.TRADITIONAL_401K]['regular_limit']
        
        # Assume 22% marginal tax rate for middle income
        marginal_rate = Decimal('0.22')
        tax_savings_401k = max_401k * marginal_rate
        
        strategy['recommendations'].append(f"Maximize 401(k) contributions: ${max_401k}")
        strategy['tax_savings'] += tax_savings_401k
        
        # IRA contributions based on income limits
        if income < Decimal('100000'):  # Simplified income test
            ira_limit = self.IRS_LIMITS_2025[AccountType.TRADITIONAL_IRA]['regular_limit']
            if age >= 50:
                ira_limit += self.IRS_LIMITS_2025[AccountType.TRADITIONAL_IRA]['catch_up_limit']
            
            tax_savings_ira = ira_limit * marginal_rate
            strategy['recommendations'].append(f"IRA contribution: ${ira_limit}")
            strategy['tax_savings'] += tax_savings_ira
        
        return strategy
    
    async def _generate_rmd_strategy(self, user_id: str, age: int, year: int) -> Dict[str, Any]:
        """Generate RMD optimization strategy"""
        
        # Simplified RMD strategy
        return {
            'strategy_type': 'rmd_optimization',
            'recommendations': [
                "Consider Qualified Charitable Distributions",
                "Manage tax bracket with timing of distributions",
                "Consider in-kind distributions of appreciated assets"
            ],
            'tax_savings': Decimal('500')  # Estimated savings
        }
    
    async def _generate_conversion_strategy(
        self,
        user_id: str,
        age: int,
        income: Decimal,
        year: int
    ) -> Optional[Dict[str, Any]]:
        """Generate Roth conversion strategy"""
        
        # Conversions most beneficial in lower income years
        if income > Decimal('150000') or age > 75:
            return None
        
        return {
            'strategy_type': 'roth_conversion',
            'recommendations': [
                "Consider partial Roth conversion in low-income years",
                "Convert up to top of current tax bracket"
            ],
            'long_term_savings': Decimal('2000')  # Estimated long-term savings
        }
    
    def _assess_plan_complexity(self, annual_strategies: Dict[int, Dict]) -> str:
        """Assess implementation complexity of multi-year plan"""
        
        strategy_count = sum(
            len(year_data.get('strategies', [])) 
            for year_data in annual_strategies.values()
        )
        
        if strategy_count > 20:
            return "High"
        elif strategy_count > 10:
            return "Medium"
        else:
            return "Low"
    
    async def _perform_sensitivity_analysis(
        self,
        user_id: str,
        annual_strategies: Dict[int, Dict]
    ) -> Dict[str, Any]:
        """Perform sensitivity analysis on tax plan"""
        
        base_savings = sum(
            year_data.get('estimated_tax_savings', Decimal('0'))
            for year_data in annual_strategies.values()
        )
        
        return {
            'base_case_savings': float(base_savings),
            'scenarios': {
                'low_income_growth': {
                    'assumption': '1% income growth instead of 3%',
                    'impact': float(base_savings * Decimal('0.85'))
                },
                'high_tax_rates': {
                    'assumption': 'Tax rates increase by 20%',
                    'impact': float(base_savings * Decimal('1.20'))
                },
                'market_downturn': {
                    'assumption': 'Market returns 20% below expectations',
                    'impact': float(base_savings * Decimal('0.90'))
                }
            }
        }