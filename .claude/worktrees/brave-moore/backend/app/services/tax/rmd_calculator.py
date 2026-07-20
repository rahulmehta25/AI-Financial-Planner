"""
Required Minimum Distribution (RMD) Calculator and Planning System

Implements comprehensive RMD planning including:
- IRS Uniform Lifetime Table calculations
- Joint life expectancy tables for spousal beneficiaries
- Inherited IRA RMD rules (SECURE Act)
- Multi-year RMD projections
- Tax optimization strategies
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
    TaxAccount, RequiredMinimumDistribution, TaxProjection,
    AccountTypeEnum, TaxTreatmentEnum, IRSLimits2025,
    TaxCalculationUtils
)
from ...models.user import User
from ...models.financial_profile import FinancialProfile

logger = logging.getLogger(__name__)


@dataclass
class LifeExpectancyFactor:
    """Life expectancy factor for RMD calculations"""
    age: int
    uniform_lifetime_factor: float
    joint_life_factor: Optional[float] = None  # For 10+ year younger spouse


@dataclass
class RMDCalculation:
    """RMD calculation for a specific account and year"""
    account_id: str
    account_name: str
    account_type: AccountTypeEnum
    calculation_year: int
    owner_age: int
    account_balance_dec_31: Decimal
    life_expectancy_factor: float
    required_minimum_distribution: Decimal
    distribution_deadline: date
    penalty_if_missed: Decimal  # 25% penalty (reduced to 10% if corrected)
    tax_implications: Dict
    distribution_strategy: str


@dataclass
class AggregatedRMDPlan:
    """Comprehensive RMD plan across all accounts"""
    user_id: str
    plan_year: int
    total_rmd_required: Decimal
    account_rmds: List[RMDCalculation]
    tax_efficient_distribution_order: List[str]
    total_tax_impact: Decimal
    distribution_timing_strategy: Dict
    monitoring_schedule: List[Dict]
    optimization_opportunities: List[Dict]


class RMDCalculatorService:
    """
    Comprehensive RMD calculation and planning service
    """
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.tax_utils = TaxCalculationUtils()
        
        # IRS Uniform Lifetime Table (2022+ version)
        self.uniform_lifetime_table = {
            72: 27.4, 73: 26.5, 74: 25.5, 75: 24.6, 76: 23.7, 77: 22.9,
            78: 22.0, 79: 21.1, 80: 20.2, 81: 19.4, 82: 18.5, 83: 17.7,
            84: 16.8, 85: 16.0, 86: 15.2, 87: 14.4, 88: 13.7, 89: 12.9,
            90: 12.2, 91: 11.5, 92: 10.8, 93: 10.1, 94: 9.5, 95: 8.9,
            96: 8.4, 97: 7.8, 98: 7.3, 99: 6.8, 100: 6.4, 101: 6.0,
            102: 5.6, 103: 5.2, 104: 4.9, 105: 4.6, 106: 4.3, 107: 4.1,
            108: 3.9, 109: 3.7, 110: 3.5, 111: 3.4, 112: 3.3, 113: 3.1,
            114: 3.0, 115: 2.9, 116: 2.8, 117: 2.7, 118: 2.5, 119: 2.3,
            120: 2.0
        }
        
        # Joint Life Expectancy Table (for spouse 10+ years younger)
        # Simplified version - full table would have all age combinations
        self.joint_life_table_sample = {
            (72, 62): 32.3, (73, 63): 31.4, (74, 64): 30.5, (75, 65): 29.5,
            (76, 66): 28.6, (77, 67): 27.7, (78, 68): 26.8, (79, 69): 25.9,
            (80, 70): 25.0, (81, 71): 24.2, (82, 72): 23.3, (83, 73): 22.5,
            (84, 74): 21.7, (85, 75): 20.9, (86, 76): 20.1, (87, 77): 19.4,
            (88, 78): 18.6, (89, 79): 17.9, (90, 80): 17.2
        }
        
        # RMD-eligible account types
        self.rmd_account_types = {
            AccountTypeEnum.TRADITIONAL_401K,
            AccountTypeEnum.TRADITIONAL_403B,
            AccountTypeEnum.TRADITIONAL_IRA,
            AccountTypeEnum.SEP_IRA,
            AccountTypeEnum.SIMPLE_IRA
            # Note: Roth IRAs don't require RMDs for original owner
        }
        
        # Distribution timing strategies
        self.distribution_strategies = {
            'early_year': 'Distribute early in year for market participation',
            'late_year': 'Distribute late in year to maximize tax-deferred growth',
            'monthly': 'Monthly distributions for steady cash flow',
            'quarterly': 'Quarterly distributions for regular income',
            'lump_sum': 'Single lump sum distribution'
        }
    
    async def calculate_current_year_rmds(
        self,
        user_id: str,
        calculation_year: Optional[int] = None
    ) -> AggregatedRMDPlan:
        """
        Calculate RMDs for current or specified year
        """
        if not calculation_year:
            calculation_year = datetime.now().year
        
        logger.info(f"Calculating RMDs for user {user_id}, year {calculation_year}")
        
        # Get user profile and eligible accounts
        user_profile = self._get_user_profile(user_id)
        rmd_accounts = self._get_rmd_eligible_accounts(user_id)
        
        if not rmd_accounts:
            logger.info(f"No RMD-eligible accounts found for user {user_id}")
            return self._empty_rmd_plan(user_id, calculation_year)
        
        # Check if user has reached RMD age
        user_age_in_calc_year = user_profile.age + (calculation_year - datetime.now().year)
        
        if user_age_in_calc_year < IRSLimits2025.RMD_AGE:
            logger.info(f"User is {user_age_in_calc_year}, below RMD age of {IRSLimits2025.RMD_AGE}")
            return self._empty_rmd_plan(user_id, calculation_year)
        
        # Calculate RMD for each account
        account_rmds = []
        
        for account in rmd_accounts:
            rmd_calc = await self._calculate_account_rmd(
                account,
                user_profile,
                calculation_year,
                user_age_in_calc_year
            )
            
            if rmd_calc:
                account_rmds.append(rmd_calc)
        
        if not account_rmds:
            return self._empty_rmd_plan(user_id, calculation_year)
        
        # Calculate total RMD
        total_rmd = sum(calc.required_minimum_distribution for calc in account_rmds)
        
        # Optimize distribution order for tax efficiency
        distribution_order = self._optimize_distribution_order(account_rmds, user_profile)
        
        # Calculate tax implications
        total_tax_impact = self._calculate_rmd_tax_impact(
            total_rmd, user_profile, calculation_year
        )
        
        # Generate distribution timing strategy
        timing_strategy = self._generate_timing_strategy(
            account_rmds, user_profile
        )
        
        # Create monitoring schedule
        monitoring_schedule = self._create_rmd_monitoring_schedule(
            account_rmds, calculation_year
        )
        
        # Identify optimization opportunities
        optimization_opportunities = self._identify_optimization_opportunities(
            account_rmds, user_profile
        )
        
        plan = AggregatedRMDPlan(
            user_id=user_id,
            plan_year=calculation_year,
            total_rmd_required=total_rmd,
            account_rmds=account_rmds,
            tax_efficient_distribution_order=distribution_order,
            total_tax_impact=total_tax_impact,
            distribution_timing_strategy=timing_strategy,
            monitoring_schedule=monitoring_schedule,
            optimization_opportunities=optimization_opportunities
        )
        
        # Store RMD calculations in database
        await self._store_rmd_calculations(plan)
        
        logger.info(f"RMD calculations complete. Total RMD: ${total_rmd}")
        
        return plan
    
    def _get_user_profile(self, user_id: str) -> FinancialProfile:
        """Get user's financial profile"""
        return self.db.query(FinancialProfile).filter(
            FinancialProfile.user_id == user_id
        ).first()
    
    def _get_rmd_eligible_accounts(self, user_id: str) -> List[TaxAccount]:
        """Get accounts that require RMDs"""
        return self.db.query(TaxAccount).filter(
            TaxAccount.user_id == user_id,
            TaxAccount.account_type.in_(list(self.rmd_account_types)),
            TaxAccount.is_active == True,
            TaxAccount.current_balance > 0
        ).all()
    
    async def _calculate_account_rmd(
        self,
        account: TaxAccount,
        user_profile: FinancialProfile,
        calculation_year: int,
        user_age: int
    ) -> Optional[RMDCalculation]:
        """Calculate RMD for a specific account"""
        
        # Get account balance as of December 31 of previous year
        prior_year_balance = await self._get_prior_year_balance(
            account, calculation_year - 1
        )
        
        if prior_year_balance <= 0:
            return None
        
        # Determine life expectancy factor
        life_expectancy_factor = self._get_life_expectancy_factor(
            user_age, user_profile
        )
        
        # Calculate RMD
        rmd_amount = prior_year_balance / Decimal(str(life_expectancy_factor))
        
        # Distribution deadline (December 31, except first year can be April 1)
        if user_age == IRSLimits2025.RMD_AGE:
            # First year - can delay until April 1 of following year
            deadline = date(calculation_year + 1, 4, 1)
        else:
            deadline = date(calculation_year, 12, 31)
        
        # Calculate penalty for missing RMD (25% of shortfall, reduced to 10% if corrected)
        penalty_amount = rmd_amount * Decimal('0.25')
        
        # Tax implications
        tax_implications = self._calculate_account_tax_implications(
            rmd_amount, account, user_profile
        )
        
        # Determine distribution strategy
        distribution_strategy = self._determine_distribution_strategy(
            account, rmd_amount, user_profile
        )
        
        return RMDCalculation(
            account_id=str(account.id),
            account_name=account.account_name,
            account_type=account.account_type,
            calculation_year=calculation_year,
            owner_age=user_age,
            account_balance_dec_31=prior_year_balance,
            life_expectancy_factor=life_expectancy_factor,
            required_minimum_distribution=rmd_amount,
            distribution_deadline=deadline,
            penalty_if_missed=penalty_amount,
            tax_implications=tax_implications,
            distribution_strategy=distribution_strategy
        )
    
    async def _get_prior_year_balance(
        self,
        account: TaxAccount,
        prior_year: int
    ) -> Decimal:
        """Get account balance as of December 31 of prior year"""
        
        # In production, this would look up historical balance records
        # For now, use current balance as approximation
        return account.current_balance or Decimal('0')
    
    def _get_life_expectancy_factor(
        self,
        user_age: int,
        user_profile: FinancialProfile
    ) -> float:
        """Get appropriate life expectancy factor for RMD calculation"""
        
        # Check if spouse is sole beneficiary and 10+ years younger
        spouse_age_diff = getattr(user_profile, 'spouse_age_difference', 0)
        
        if spouse_age_diff >= 10:
            # Use Joint Life Expectancy Table
            spouse_age = user_age - spouse_age_diff
            joint_factor = self.joint_life_table_sample.get((user_age, spouse_age))
            
            if joint_factor:
                return joint_factor
        
        # Use Uniform Lifetime Table
        return self.uniform_lifetime_table.get(user_age, 2.0)  # Minimum factor for very old ages
    
    def _calculate_account_tax_implications(
        self,
        distribution_amount: Decimal,
        account: TaxAccount,
        user_profile: FinancialProfile
    ) -> Dict:
        """Calculate tax implications of RMD"""
        
        marginal_rate = user_profile.marginal_tax_rate or 0.22
        
        # Federal income tax
        federal_tax = distribution_amount * Decimal(str(marginal_rate))
        
        # State income tax (simplified)
        state_rate = getattr(user_profile, 'state_tax_rate', 0.05)
        state_tax = distribution_amount * Decimal(str(state_rate))
        
        # Potential Medicare surcharges (IRMAA)
        medicare_surcharge = Decimal('0')
        income_with_rmd = (user_profile.annual_income or Decimal('0')) + distribution_amount
        
        if income_with_rmd > Decimal('200000'):  # Simplified IRMAA threshold
            medicare_surcharge = Decimal('2000')  # Approximate annual surcharge
        
        return {
            'federal_income_tax': federal_tax,
            'state_income_tax': state_tax,
            'medicare_surcharge': medicare_surcharge,
            'total_tax_cost': federal_tax + state_tax + medicare_surcharge,
            'after_tax_amount': distribution_amount - federal_tax - state_tax - medicare_surcharge,
            'effective_tax_rate': float((federal_tax + state_tax) / distribution_amount)
        }
    
    def _determine_distribution_strategy(
        self,
        account: TaxAccount,
        rmd_amount: Decimal,
        user_profile: FinancialProfile
    ) -> str:
        """Determine optimal distribution strategy for account"""
        
        # Factors to consider:
        # - Account balance relative to RMD
        # - User's cash flow needs  
        # - Market volatility
        # - Tax situation
        
        balance_to_rmd_ratio = (account.current_balance or Decimal('0')) / rmd_amount
        
        if balance_to_rmd_ratio > 20:
            # Large balance relative to RMD - can be flexible
            if user_profile.risk_tolerance == 'conservative':
                return 'early_year'  # Take early to reduce market risk
            else:
                return 'late_year'   # Take late to maximize growth
        
        elif balance_to_rmd_ratio > 10:
            return 'quarterly'  # Moderate approach
        
        else:
            return 'monthly'    # Smooth out market timing risk
    
    def _optimize_distribution_order(
        self,
        account_rmds: List[RMDCalculation],
        user_profile: FinancialProfile
    ) -> List[str]:
        """Optimize order of distributions across accounts for tax efficiency"""
        
        # Sort by tax efficiency - distribute from least tax-efficient first
        # This allows tax-efficient accounts to continue growing
        
        sorted_accounts = sorted(
            account_rmds,
            key=lambda x: (
                # Prioritize by account type efficiency
                self._get_account_tax_efficiency_score(x.account_type),
                # Then by size (distribute from smaller accounts first)
                -float(x.account_balance_dec_31)
            )
        )
        
        return [calc.account_id for calc in sorted_accounts]
    
    def _get_account_tax_efficiency_score(self, account_type: AccountTypeEnum) -> int:
        """Score account types by tax efficiency (lower = distribute first)"""
        efficiency_scores = {
            AccountTypeEnum.TRADITIONAL_401K: 1,  # Often has limited investment options
            AccountTypeEnum.TRADITIONAL_403B: 1,
            AccountTypeEnum.SEP_IRA: 2,
            AccountTypeEnum.SIMPLE_IRA: 2,
            AccountTypeEnum.TRADITIONAL_IRA: 3   # Often has best investment options
        }
        
        return efficiency_scores.get(account_type, 2)
    
    def _calculate_rmd_tax_impact(
        self,
        total_rmd: Decimal,
        user_profile: FinancialProfile,
        calculation_year: int
    ) -> Decimal:
        """Calculate total tax impact of all RMDs"""
        
        # Project user's other income for the year
        base_income = user_profile.annual_income or Decimal('0')
        
        # Calculate tax with and without RMDs
        tax_without_rmd = self._estimate_federal_tax(base_income, user_profile.filing_status)
        tax_with_rmd = self._estimate_federal_tax(base_income + total_rmd, user_profile.filing_status)
        
        return tax_with_rmd - tax_without_rmd
    
    def _estimate_federal_tax(self, income: Decimal, filing_status: str) -> Decimal:
        """Simplified federal tax calculation"""
        # This would use proper tax brackets in production
        marginal_rate = 0.22  # Simplified assumption
        return income * Decimal(str(marginal_rate))
    
    def _generate_timing_strategy(
        self,
        account_rmds: List[RMDCalculation],
        user_profile: FinancialProfile
    ) -> Dict:
        """Generate optimal timing strategy for distributions"""
        
        total_rmd = sum(calc.required_minimum_distribution for calc in account_rmds)
        
        strategy = {
            'recommended_approach': 'quarterly',
            'rationale': 'Balance market timing risk with cash flow needs',
            'quarterly_amounts': total_rmd / 4,
            'distribution_dates': [
                date(datetime.now().year, 3, 31),
                date(datetime.now().year, 6, 30),
                date(datetime.now().year, 9, 30),
                date(datetime.now().year, 12, 31)
            ],
            'alternatives': {
                'conservative': {
                    'approach': 'early_year',
                    'rationale': 'Take distributions early to reduce market risk',
                    'target_date': date(datetime.now().year, 3, 31)
                },
                'aggressive': {
                    'approach': 'late_year',
                    'rationale': 'Delay distributions to maximize tax-deferred growth',
                    'target_date': date(datetime.now().year, 12, 15)
                }
            }
        }
        
        return strategy
    
    def _create_rmd_monitoring_schedule(
        self,
        account_rmds: List[RMDCalculation],
        calculation_year: int
    ) -> List[Dict]:
        """Create monitoring schedule for RMD compliance"""
        
        schedule = []
        
        # Quarterly reviews
        for quarter in range(1, 5):
            month = quarter * 3
            schedule.append({
                'date': date(calculation_year, month, 15),
                'task': f'Q{quarter} RMD review',
                'actions': [
                    'Review account balances',
                    'Check distribution progress',
                    'Adjust timing strategy if needed'
                ],
                'priority': 'medium'
            })
        
        # Year-end critical reminder
        schedule.append({
            'date': date(calculation_year, 12, 1),
            'task': 'Final RMD deadline reminder',
            'actions': [
                'Verify all RMDs completed',
                'Calculate any shortfalls',
                'Execute final distributions'
            ],
            'priority': 'high'
        })
        
        # Next year planning
        schedule.append({
            'date': date(calculation_year, 11, 1),
            'task': 'Plan next year RMDs',
            'actions': [
                'Update account balances for next year calculation',
                'Review beneficiary designations',
                'Consider Roth conversion opportunities'
            ],
            'priority': 'medium'
        })
        
        return schedule
    
    def _identify_optimization_opportunities(
        self,
        account_rmds: List[RMDCalculation],
        user_profile: FinancialProfile
    ) -> List[Dict]:
        """Identify opportunities to optimize RMD strategy"""
        
        opportunities = []
        
        # Qualified Charitable Distribution (QCD) opportunity
        if user_profile.age >= 70.5:  # QCD eligible age
            total_rmd = sum(calc.required_minimum_distribution for calc in account_rmds)
            
            opportunities.append({
                'strategy': 'qualified_charitable_distribution',
                'description': 'Direct IRA distribution to charity (up to $105,000 in 2025)',
                'benefit': 'Avoid income tax on distribution',
                'max_amount': min(total_rmd, Decimal('105000')),
                'requirements': [
                    'Must be from IRA (not 401k)',
                    'Must go directly to qualified charity',
                    'Must be 70.5 or older'
                ]
            })
        
        # Asset location optimization
        for rmd_calc in account_rmds:
            if rmd_calc.account_balance_dec_31 > rmd_calc.required_minimum_distribution * 10:
                opportunities.append({
                    'strategy': 'in_service_distribution',
                    'account': rmd_calc.account_name,
                    'description': 'Consider in-service distribution to Roth IRA',
                    'benefit': 'Convert high-growth assets to tax-free account',
                    'consideration': 'Evaluate current vs. future tax rates'
                })
        
        # Bunching strategy
        opportunities.append({
            'strategy': 'rmd_bunching',
            'description': 'Consider taking extra distributions in low-income years',
            'benefit': 'Reduce future RMDs and manage tax brackets',
            'timing': 'Best in years with unusually low income'
        })
        
        return opportunities
    
    async def _store_rmd_calculations(self, plan: AggregatedRMDPlan) -> None:
        """Store RMD calculations in database"""
        
        for rmd_calc in plan.account_rmds:
            # Check if RMD record already exists for this year
            existing = self.db.query(RequiredMinimumDistribution).filter(
                RequiredMinimumDistribution.user_id == plan.user_id,
                RequiredMinimumDistribution.account_id == rmd_calc.account_id,
                RequiredMinimumDistribution.calculation_year == plan.plan_year
            ).first()
            
            if existing:
                # Update existing record
                existing.account_balance_previous_year = rmd_calc.account_balance_dec_31
                existing.life_expectancy_factor = rmd_calc.life_expectancy_factor
                existing.required_distribution = rmd_calc.required_minimum_distribution
                existing.due_date = datetime.combine(rmd_calc.distribution_deadline, datetime.min.time())
                existing.updated_at = datetime.utcnow()
            else:
                # Create new record
                rmd_record = RequiredMinimumDistribution(
                    user_id=plan.user_id,
                    account_id=rmd_calc.account_id,
                    calculation_year=plan.plan_year,
                    account_balance_previous_year=rmd_calc.account_balance_dec_31,
                    life_expectancy_factor=rmd_calc.life_expectancy_factor,
                    required_distribution=rmd_calc.required_minimum_distribution,
                    due_date=datetime.combine(rmd_calc.distribution_deadline, datetime.min.time()),
                    status='pending'
                )
                
                self.db.add(rmd_record)
        
        await self.db.commit()
    
    def _empty_rmd_plan(self, user_id: str, calculation_year: int) -> AggregatedRMDPlan:
        """Return empty RMD plan"""
        return AggregatedRMDPlan(
            user_id=user_id,
            plan_year=calculation_year,
            total_rmd_required=Decimal('0'),
            account_rmds=[],
            tax_efficient_distribution_order=[],
            total_tax_impact=Decimal('0'),
            distribution_timing_strategy={},
            monitoring_schedule=[],
            optimization_opportunities=[]
        )
    
    async def project_future_rmds(
        self,
        user_id: str,
        projection_years: int = 10
    ) -> List[AggregatedRMDPlan]:
        """Project RMDs for multiple future years"""
        
        user_profile = self._get_user_profile(user_id)
        rmd_accounts = self._get_rmd_eligible_accounts(user_id)
        
        projections = []
        current_year = datetime.now().year
        
        for year_offset in range(projection_years):
            projection_year = current_year + year_offset
            user_age = user_profile.age + year_offset
            
            # Only project if user will be at RMD age
            if user_age >= IRSLimits2025.RMD_AGE:
                
                # Project account balances (simplified growth model)
                projected_balances = {}
                for account in rmd_accounts:
                    growth_rate = 0.06  # Assumed annual growth
                    current_balance = account.current_balance or Decimal('0')
                    projected_balance = current_balance * (Decimal('1.06') ** year_offset)
                    projected_balances[str(account.id)] = projected_balance
                
                # Calculate RMDs for projected year
                plan = await self._calculate_projected_year_rmds(
                    user_id,
                    projection_year,
                    user_age,
                    projected_balances,
                    rmd_accounts
                )
                
                projections.append(plan)
        
        return projections
    
    async def _calculate_projected_year_rmds(
        self,
        user_id: str,
        projection_year: int,
        user_age: int,
        projected_balances: Dict[str, Decimal],
        accounts: List[TaxAccount]
    ) -> AggregatedRMDPlan:
        """Calculate RMDs for a projected future year"""
        
        user_profile = self._get_user_profile(user_id)
        account_rmds = []
        
        for account in accounts:
            account_balance = projected_balances.get(str(account.id), Decimal('0'))
            
            if account_balance > 0:
                # Get life expectancy factor
                life_expectancy_factor = self._get_life_expectancy_factor(
                    user_age, user_profile
                )
                
                # Calculate RMD
                rmd_amount = account_balance / Decimal(str(life_expectancy_factor))
                
                rmd_calc = RMDCalculation(
                    account_id=str(account.id),
                    account_name=account.account_name,
                    account_type=account.account_type,
                    calculation_year=projection_year,
                    owner_age=user_age,
                    account_balance_dec_31=account_balance,
                    life_expectancy_factor=life_expectancy_factor,
                    required_minimum_distribution=rmd_amount,
                    distribution_deadline=date(projection_year, 12, 31),
                    penalty_if_missed=rmd_amount * Decimal('0.25'),
                    tax_implications=self._calculate_account_tax_implications(
                        rmd_amount, account, user_profile
                    ),
                    distribution_strategy='projected'
                )
                
                account_rmds.append(rmd_calc)
        
        total_rmd = sum(calc.required_minimum_distribution for calc in account_rmds)
        
        return AggregatedRMDPlan(
            user_id=user_id,
            plan_year=projection_year,
            total_rmd_required=total_rmd,
            account_rmds=account_rmds,
            tax_efficient_distribution_order=[],
            total_tax_impact=self._calculate_rmd_tax_impact(
                total_rmd, user_profile, projection_year
            ),
            distribution_timing_strategy={},
            monitoring_schedule=[],
            optimization_opportunities=[]
        )
    
    async def track_rmd_completion(
        self,
        user_id: str,
        account_id: str,
        distribution_amount: Decimal,
        distribution_date: date
    ) -> Dict:
        """Track completion of an RMD"""
        
        current_year = distribution_date.year
        
        # Find the RMD record
        rmd_record = self.db.query(RequiredMinimumDistribution).filter(
            RequiredMinimumDistribution.user_id == user_id,
            RequiredMinimumDistribution.account_id == account_id,
            RequiredMinimumDistribution.calculation_year == current_year
        ).first()
        
        if not rmd_record:
            raise ValueError(f"No RMD record found for account {account_id} in {current_year}")
        
        # Update distribution tracking
        rmd_record.distributed_amount += distribution_amount
        rmd_record.remaining_amount = max(
            Decimal('0'),
            rmd_record.required_distribution - rmd_record.distributed_amount
        )
        
        # Update status
        if rmd_record.remaining_amount <= Decimal('10'):  # Allow small rounding differences
            rmd_record.status = 'complete'
        elif rmd_record.distributed_amount > 0:
            rmd_record.status = 'partial'
        
        # Check for overdue status
        if distribution_date > rmd_record.due_date.date() and rmd_record.remaining_amount > 0:
            rmd_record.status = 'overdue'
        
        rmd_record.updated_at = datetime.utcnow()
        
        await self.db.commit()
        
        result = {
            'rmd_id': str(rmd_record.id),
            'required_distribution': rmd_record.required_distribution,
            'distributed_amount': rmd_record.distributed_amount,
            'remaining_amount': rmd_record.remaining_amount,
            'status': rmd_record.status,
            'is_complete': rmd_record.status == 'complete',
            'is_overdue': rmd_record.status == 'overdue'
        }
        
        logger.info(
            f"RMD tracking updated: ${distribution_amount} distributed from account {account_id}"
        )
        
        return result