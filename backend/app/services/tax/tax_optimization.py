"""
Comprehensive Tax Optimization Engine for AI Financial Planner

This module implements a sophisticated tax optimization system that includes:
- Advanced tax-loss harvesting with wash sale compliance
- Asset location optimization across account types
- Tax bracket management and optimization
- Roth conversion analysis and laddering strategies
- Required Minimum Distribution (RMD) calculations
- Charitable giving tax strategies
- Estate tax planning considerations
- Capital gains optimization
- Tax-efficient withdrawal sequencing
- Multi-state tax optimization

The engine considers federal and state taxes across all account types:
401k, Traditional IRA, Roth IRA, HSA, 529, and taxable accounts.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import numpy as np
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from ...models.tax_accounts import (
    TaxAccount, TaxAccountHolding, TaxAccountTransaction,
    AccountTypeEnum, TaxTreatmentEnum
)
from ...models.retirement_accounts import (
    RetirementAccount, RetirementContribution, AccountType as RetirementAccountType
)
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


class TaxAccountType(Enum):
    """Comprehensive account types for tax optimization"""
    TAXABLE = "taxable"
    TRADITIONAL_401K = "traditional_401k"
    ROTH_401K = "roth_401k"
    TRADITIONAL_IRA = "traditional_ira"
    ROTH_IRA = "roth_ira"
    SEP_IRA = "sep_ira"
    SIMPLE_IRA = "simple_ira"
    HSA = "hsa"
    MSA = "msa"  # Medical Savings Account
    PLAN_529 = "529_plan"
    COVERDELL_ESA = "coverdell_esa"
    ANNUITY = "annuity"
    PENSION = "pension"
    CASH_BALANCE_PENSION = "cash_balance_pension"
    PROFIT_SHARING = "profit_sharing"


class AssetClass(Enum):
    """Asset classes for location optimization"""
    BONDS = "bonds"
    CORPORATE_BONDS = "corporate_bonds"
    MUNICIPAL_BONDS = "municipal_bonds"
    TREASURY_BONDS = "treasury_bonds"
    INTERNATIONAL_BONDS = "international_bonds"
    HIGH_YIELD_BONDS = "high_yield_bonds"
    TIPS = "tips"  # Treasury Inflation-Protected Securities
    
    EQUITIES = "equities"
    LARGE_CAP_GROWTH = "large_cap_growth"
    LARGE_CAP_VALUE = "large_cap_value"
    MID_CAP_GROWTH = "mid_cap_growth"
    MID_CAP_VALUE = "mid_cap_value"
    SMALL_CAP_GROWTH = "small_cap_growth"
    SMALL_CAP_VALUE = "small_cap_value"
    
    INTERNATIONAL_DEVELOPED = "international_developed"
    INTERNATIONAL_EMERGING = "international_emerging"
    
    REITS = "reits"
    COMMODITIES = "commodities"
    ALTERNATIVES = "alternatives"
    PRIVATE_EQUITY = "private_equity"
    HEDGE_FUNDS = "hedge_funds"


@dataclass
class TaxBracket:
    """Federal tax bracket information"""
    min_income: Decimal
    max_income: Optional[Decimal]
    rate: Decimal
    bracket_name: str


@dataclass
class StateTaxProfile:
    """State tax profile with comprehensive information"""
    state: str
    state_name: str
    income_tax_rate: Decimal
    capital_gains_rate: Optional[Decimal]
    retirement_income_exemption: bool
    pension_exemption_amount: Optional[Decimal]
    social_security_taxed: bool
    property_tax_deduction_limit: Optional[Decimal]
    state_tax_deduction_limit: Optional[Decimal]
    plan_529_deduction_limit: Optional[Decimal]
    plan_529_tax_credit_rate: Optional[Decimal]
    estate_tax_exemption: Optional[Decimal]
    inheritance_tax_rates: Optional[Dict[str, Decimal]]


@dataclass
class TaxLossOpportunity:
    """Advanced tax-loss harvesting opportunity"""
    holding_id: str
    symbol: str
    asset_class: AssetClass
    current_price: Decimal
    cost_basis_per_share: Decimal
    shares: Decimal
    purchase_date: datetime
    unrealized_loss: Decimal
    tax_benefit_short_term: Decimal
    tax_benefit_long_term: Decimal
    wash_sale_risk_score: float
    replacement_securities: List[str]
    optimal_replacement: Optional[str]
    implementation_priority: int
    execution_timeline: List[Dict]
    risk_factors: List[str]


@dataclass
class AssetLocationRecommendation:
    """Asset location optimization recommendation"""
    asset_class: AssetClass
    current_account_type: TaxAccountType
    recommended_account_type: TaxAccountType
    current_allocation: Decimal
    recommended_allocation: Decimal
    annual_tax_savings: Decimal
    implementation_steps: List[str]
    tax_efficiency_score: float
    priority_rank: int


@dataclass
class RothConversionOpportunity:
    """Roth conversion optimization opportunity"""
    traditional_ira_balance: Decimal
    conversion_amount: Decimal
    conversion_year: int
    current_tax_bracket: Decimal
    future_tax_bracket: Decimal
    tax_cost: Decimal
    future_tax_savings: Decimal
    break_even_years: int
    net_present_value: Decimal
    implementation_timeline: Dict
    risk_considerations: List[str]


@dataclass
class WithdrawalStrategy:
    """Tax-efficient withdrawal sequencing strategy"""
    total_withdrawal_needed: Decimal
    withdrawal_sequence: List[Dict]
    total_tax_impact: Decimal
    after_tax_amount: Decimal
    tax_efficiency_score: float
    alternative_strategies: List[Dict]


@dataclass
class CharitableGivingStrategy:
    """Charitable giving tax optimization strategy"""
    annual_giving_intent: Decimal
    strategy_type: str
    asset_donation_opportunities: List[Dict]
    tax_benefit: Decimal
    bunching_opportunity: Optional[Dict]
    donor_advised_fund_analysis: Optional[Dict]
    charitable_remainder_trust_analysis: Optional[Dict]


@dataclass
class EstateElanningRecommendation:
    """Estate tax planning recommendation"""
    current_estate_value: Decimal
    estate_tax_exposure: Decimal
    gift_tax_opportunities: List[Dict]
    trust_recommendations: List[Dict]
    generation_skipping_opportunities: List[Dict]
    step_up_basis_optimization: List[Dict]


class ComprehensiveTaxOptimizer:
    """
    Comprehensive tax optimization engine that analyzes and optimizes
    all aspects of tax-efficient financial planning
    """
    
    # 2025 Federal Tax Brackets (estimated with inflation adjustments)
    FEDERAL_TAX_BRACKETS_2025 = {
        FilingStatus.SINGLE: [
            TaxBracket(Decimal('0'), Decimal('11700'), Decimal('0.10'), '10%'),
            TaxBracket(Decimal('11700'), Decimal('47500'), Decimal('0.12'), '12%'),
            TaxBracket(Decimal('47500'), Decimal('100500'), Decimal('0.22'), '22%'),
            TaxBracket(Decimal('100500'), Decimal('191650'), Decimal('0.24'), '24%'),
            TaxBracket(Decimal('191650'), Decimal('243725'), Decimal('0.32'), '32%'),
            TaxBracket(Decimal('243725'), Decimal('609350'), Decimal('0.35'), '35%'),
            TaxBracket(Decimal('609350'), None, Decimal('0.37'), '37%'),
        ],
        FilingStatus.MARRIED_FILING_JOINTLY: [
            TaxBracket(Decimal('0'), Decimal('23400'), Decimal('0.10'), '10%'),
            TaxBracket(Decimal('23400'), Decimal('95000'), Decimal('0.12'), '12%'),
            TaxBracket(Decimal('95000'), Decimal('201000'), Decimal('0.22'), '22%'),
            TaxBracket(Decimal('201000'), Decimal('383300'), Decimal('0.24'), '24%'),
            TaxBracket(Decimal('383300'), Decimal('487450'), Decimal('0.32'), '32%'),
            TaxBracket(Decimal('487450'), Decimal('731200'), Decimal('0.35'), '35%'),
            TaxBracket(Decimal('731200'), None, Decimal('0.37'), '37%'),
        ],
        FilingStatus.MARRIED_FILING_SEPARATELY: [
            TaxBracket(Decimal('0'), Decimal('11700'), Decimal('0.10'), '10%'),
            TaxBracket(Decimal('11700'), Decimal('47500'), Decimal('0.12'), '12%'),
            TaxBracket(Decimal('47500'), Decimal('100500'), Decimal('0.22'), '22%'),
            TaxBracket(Decimal('100500'), Decimal('191650'), Decimal('0.24'), '24%'),
            TaxBracket(Decimal('191650'), Decimal('243725'), Decimal('0.32'), '32%'),
            TaxBracket(Decimal('243725'), Decimal('365600'), Decimal('0.35'), '35%'),
            TaxBracket(Decimal('365600'), None, Decimal('0.37'), '37%'),
        ],
        FilingStatus.HEAD_OF_HOUSEHOLD: [
            TaxBracket(Decimal('0'), Decimal('16750'), Decimal('0.10'), '10%'),
            TaxBracket(Decimal('16750'), Decimal('63700'), Decimal('0.12'), '12%'),
            TaxBracket(Decimal('63700'), Decimal('100500'), Decimal('0.22'), '22%'),
            TaxBracket(Decimal('100500'), Decimal('191650'), Decimal('0.24'), '24%'),
            TaxBracket(Decimal('191650'), Decimal('243700'), Decimal('0.32'), '32%'),
            TaxBracket(Decimal('243700'), Decimal('609350'), Decimal('0.35'), '35%'),
            TaxBracket(Decimal('609350'), None, Decimal('0.37'), '37%'),
        ],
    }
    
    # 2025 Capital Gains Tax Brackets
    CAPITAL_GAINS_BRACKETS_2025 = {
        FilingStatus.SINGLE: [
            TaxBracket(Decimal('0'), Decimal('47000'), Decimal('0.00'), '0%'),
            TaxBracket(Decimal('47000'), Decimal('518900'), Decimal('0.15'), '15%'),
            TaxBracket(Decimal('518900'), None, Decimal('0.20'), '20%'),
        ],
        FilingStatus.MARRIED_FILING_JOINTLY: [
            TaxBracket(Decimal('0'), Decimal('94000'), Decimal('0.00'), '0%'),
            TaxBracket(Decimal('94000'), Decimal('583750'), Decimal('0.15'), '15%'),
            TaxBracket(Decimal('583750'), None, Decimal('0.20'), '20%'),
        ],
        FilingStatus.MARRIED_FILING_SEPARATELY: [
            TaxBracket(Decimal('0'), Decimal('47000'), Decimal('0.00'), '0%'),
            TaxBracket(Decimal('47000'), Decimal('291875'), Decimal('0.15'), '15%'),
            TaxBracket(Decimal('291875'), None, Decimal('0.20'), '20%'),
        ],
        FilingStatus.HEAD_OF_HOUSEHOLD: [
            TaxBracket(Decimal('0'), Decimal('63000'), Decimal('0.00'), '0%'),
            TaxBracket(Decimal('63000'), Decimal('551350'), Decimal('0.15'), '15%'),
            TaxBracket(Decimal('551350'), None, Decimal('0.20'), '20%'),
        ],
    }
    
    # Standard deductions for 2025
    STANDARD_DEDUCTIONS_2025 = {
        FilingStatus.SINGLE: Decimal('14600'),
        FilingStatus.MARRIED_FILING_JOINTLY: Decimal('29200'),
        FilingStatus.MARRIED_FILING_SEPARATELY: Decimal('14600'),
        FilingStatus.HEAD_OF_HOUSEHOLD: Decimal('21900'),
    }
    
    # Estate tax exemption for 2025
    ESTATE_TAX_EXEMPTION_2025 = Decimal('13610000')
    GIFT_TAX_ANNUAL_EXCLUSION_2025 = Decimal('18000')
    
    def __init__(self, db_session: Session):
        self.db = db_session
        
        # Initialize state tax profiles
        self.state_tax_profiles = self._initialize_state_tax_profiles()
        
        # Asset location preferences (tax efficiency scoring)
        self.asset_location_preferences = {
            # Tax-inefficient assets prefer tax-deferred accounts
            AssetClass.BONDS: {
                TaxAccountType.TRADITIONAL_401K: 1.0,
                TaxAccountType.TRADITIONAL_IRA: 1.0,
                TaxAccountType.SEP_IRA: 1.0,
                TaxAccountType.ROTH_401K: 0.3,
                TaxAccountType.ROTH_IRA: 0.3,
                TaxAccountType.TAXABLE: 0.1,
            },
            AssetClass.CORPORATE_BONDS: {
                TaxAccountType.TRADITIONAL_401K: 1.0,
                TaxAccountType.TRADITIONAL_IRA: 1.0,
                TaxAccountType.SEP_IRA: 1.0,
                TaxAccountType.ROTH_401K: 0.3,
                TaxAccountType.ROTH_IRA: 0.3,
                TaxAccountType.TAXABLE: 0.1,
            },
            AssetClass.HIGH_YIELD_BONDS: {
                TaxAccountType.TRADITIONAL_401K: 1.0,
                TaxAccountType.TRADITIONAL_IRA: 1.0,
                TaxAccountType.ROTH_401K: 0.8,
                TaxAccountType.ROTH_IRA: 0.8,
                TaxAccountType.TAXABLE: 0.1,
            },
            AssetClass.REITS: {
                TaxAccountType.TRADITIONAL_401K: 1.0,
                TaxAccountType.TRADITIONAL_IRA: 1.0,
                TaxAccountType.ROTH_401K: 0.7,
                TaxAccountType.ROTH_IRA: 0.7,
                TaxAccountType.TAXABLE: 0.2,
            },
            
            # Municipal bonds prefer taxable accounts (tax-free interest)
            AssetClass.MUNICIPAL_BONDS: {
                TaxAccountType.TAXABLE: 1.0,
                TaxAccountType.TRADITIONAL_401K: 0.1,
                TaxAccountType.TRADITIONAL_IRA: 0.1,
                TaxAccountType.ROTH_401K: 0.2,
                TaxAccountType.ROTH_IRA: 0.2,
            },
            
            # Growth stocks prefer Roth or taxable accounts
            AssetClass.LARGE_CAP_GROWTH: {
                TaxAccountType.ROTH_IRA: 1.0,
                TaxAccountType.ROTH_401K: 1.0,
                TaxAccountType.TAXABLE: 0.8,
                TaxAccountType.TRADITIONAL_401K: 0.5,
                TaxAccountType.TRADITIONAL_IRA: 0.5,
            },
            AssetClass.SMALL_CAP_GROWTH: {
                TaxAccountType.ROTH_IRA: 1.0,
                TaxAccountType.ROTH_401K: 1.0,
                TaxAccountType.TAXABLE: 0.7,
                TaxAccountType.TRADITIONAL_401K: 0.4,
                TaxAccountType.TRADITIONAL_IRA: 0.4,
            },
            
            # International stocks prefer taxable (foreign tax credit)
            AssetClass.INTERNATIONAL_DEVELOPED: {
                TaxAccountType.TAXABLE: 1.0,
                TaxAccountType.ROTH_IRA: 0.8,
                TaxAccountType.ROTH_401K: 0.8,
                TaxAccountType.TRADITIONAL_401K: 0.6,
                TaxAccountType.TRADITIONAL_IRA: 0.6,
            },
            AssetClass.INTERNATIONAL_EMERGING: {
                TaxAccountType.TAXABLE: 1.0,
                TaxAccountType.ROTH_IRA: 0.9,
                TaxAccountType.ROTH_401K: 0.9,
                TaxAccountType.TRADITIONAL_401K: 0.7,
                TaxAccountType.TRADITIONAL_IRA: 0.7,
            },
        }
        
        # Wash sale substitute mapping
        self.wash_sale_substitutes = {
            # Broad market ETFs
            'SPY': ['VOO', 'VTI', 'ITOT', 'SPTM', 'SPLG'],
            'VOO': ['SPY', 'VTI', 'ITOT', 'SPTM', 'SPLG'],
            'VTI': ['ITOT', 'SPTM', 'SCHB', 'SPLG'],
            'ITOT': ['VTI', 'SPTM', 'SCHB', 'SPLG'],
            
            # International
            'VEA': ['IEFA', 'SCHF', 'VTEB', 'EFA'],
            'VWO': ['IEMG', 'SCHE', 'SPEM', 'EEM'],
            'VXUS': ['IXUS', 'FTIHX', 'SWISX'],
            
            # Bonds
            'BND': ['AGG', 'SCHZ', 'IUSB', 'FXNAX'],
            'AGG': ['BND', 'SCHZ', 'IUSB', 'FXNAX'],
            'TLT': ['EDV', 'VGLT', 'SPTL', 'FNBGX'],
            
            # Sector ETFs
            'XLK': ['VGT', 'FTEC', 'IYW', 'FSELX'],
            'XLF': ['VFH', 'IYF', 'FREL', 'FSKAX'],
            'XLE': ['VDE', 'IYE', 'FENY', 'FSENX'],
            'XLV': ['VHT', 'IYH', 'FHLC', 'FBIOX'],
            
            # Small cap
            'IWM': ['VB', 'VTWO', 'SCHA', 'SMLV'],
            'VB': ['IWM', 'VTWO', 'SCHA', 'SMLV'],
            
            # REITs
            'VNQ': ['SCHH', 'IYR', 'FREL', 'RWR'],
            'IYR': ['VNQ', 'SCHH', 'FREL', 'RWR'],
        }
    
    def _initialize_state_tax_profiles(self) -> Dict[str, StateTaxProfile]:
        """Initialize comprehensive state tax profiles"""
        return {
            'AL': StateTaxProfile(
                state='AL', state_name='Alabama', income_tax_rate=Decimal('0.05'),
                capital_gains_rate=None, retirement_income_exemption=True,
                pension_exemption_amount=Decimal('6000'), social_security_taxed=False,
                property_tax_deduction_limit=None, state_tax_deduction_limit=None,
                plan_529_deduction_limit=Decimal('5000'), plan_529_tax_credit_rate=None,
                estate_tax_exemption=None, inheritance_tax_rates=None
            ),
            'AK': StateTaxProfile(
                state='AK', state_name='Alaska', income_tax_rate=Decimal('0.00'),
                capital_gains_rate=Decimal('0.00'), retirement_income_exemption=True,
                pension_exemption_amount=None, social_security_taxed=False,
                property_tax_deduction_limit=None, state_tax_deduction_limit=None,
                plan_529_deduction_limit=None, plan_529_tax_credit_rate=None,
                estate_tax_exemption=None, inheritance_tax_rates=None
            ),
            'AZ': StateTaxProfile(
                state='AZ', state_name='Arizona', income_tax_rate=Decimal('0.045'),
                capital_gains_rate=None, retirement_income_exemption=True,
                pension_exemption_amount=Decimal('2500'), social_security_taxed=False,
                property_tax_deduction_limit=None, state_tax_deduction_limit=None,
                plan_529_deduction_limit=Decimal('2000'), plan_529_tax_credit_rate=None,
                estate_tax_exemption=None, inheritance_tax_rates=None
            ),
            'CA': StateTaxProfile(
                state='CA', state_name='California', income_tax_rate=Decimal('0.133'),
                capital_gains_rate=Decimal('0.133'), retirement_income_exemption=False,
                pension_exemption_amount=None, social_security_taxed=False,
                property_tax_deduction_limit=Decimal('10000'), state_tax_deduction_limit=Decimal('10000'),
                plan_529_deduction_limit=None, plan_529_tax_credit_rate=None,
                estate_tax_exemption=None, inheritance_tax_rates=None
            ),
            'CO': StateTaxProfile(
                state='CO', state_name='Colorado', income_tax_rate=Decimal('0.044'),
                capital_gains_rate=None, retirement_income_exemption=True,
                pension_exemption_amount=Decimal('24000'), social_security_taxed=False,
                property_tax_deduction_limit=None, state_tax_deduction_limit=None,
                plan_529_deduction_limit=None, plan_529_tax_credit_rate=None,
                estate_tax_exemption=None, inheritance_tax_rates=None
            ),
            'CT': StateTaxProfile(
                state='CT', state_name='Connecticut', income_tax_rate=Decimal('0.0699'),
                capital_gains_rate=None, retirement_income_exemption=True,
                pension_exemption_amount=Decimal('75000'), social_security_taxed=False,
                property_tax_deduction_limit=None, state_tax_deduction_limit=None,
                plan_529_deduction_limit=Decimal('5000'), plan_529_tax_credit_rate=None,
                estate_tax_exemption=Decimal('7100000'), inheritance_tax_rates=None
            ),
            'FL': StateTaxProfile(
                state='FL', state_name='Florida', income_tax_rate=Decimal('0.00'),
                capital_gains_rate=Decimal('0.00'), retirement_income_exemption=True,
                pension_exemption_amount=None, social_security_taxed=False,
                property_tax_deduction_limit=None, state_tax_deduction_limit=None,
                plan_529_deduction_limit=None, plan_529_tax_credit_rate=None,
                estate_tax_exemption=None, inheritance_tax_rates=None
            ),
            'NY': StateTaxProfile(
                state='NY', state_name='New York', income_tax_rate=Decimal('0.109'),
                capital_gains_rate=None, retirement_income_exemption=True,
                pension_exemption_amount=Decimal('20000'), social_security_taxed=False,
                property_tax_deduction_limit=Decimal('10000'), state_tax_deduction_limit=Decimal('10000'),
                plan_529_deduction_limit=Decimal('10000'), plan_529_tax_credit_rate=None,
                estate_tax_exemption=Decimal('6110000'), inheritance_tax_rates=None
            ),
            'TX': StateTaxProfile(
                state='TX', state_name='Texas', income_tax_rate=Decimal('0.00'),
                capital_gains_rate=Decimal('0.00'), retirement_income_exemption=True,
                pension_exemption_amount=None, social_security_taxed=False,
                property_tax_deduction_limit=None, state_tax_deduction_limit=None,
                plan_529_deduction_limit=None, plan_529_tax_credit_rate=None,
                estate_tax_exemption=None, inheritance_tax_rates=None
            ),
            'WA': StateTaxProfile(
                state='WA', state_name='Washington', income_tax_rate=Decimal('0.00'),
                capital_gains_rate=Decimal('0.07'),  # On capital gains over $250k
                retirement_income_exemption=True, pension_exemption_amount=None,
                social_security_taxed=False, property_tax_deduction_limit=None,
                state_tax_deduction_limit=None, plan_529_deduction_limit=None,
                plan_529_tax_credit_rate=None, estate_tax_exemption=Decimal('2193000'),
                inheritance_tax_rates=None
            ),
        }
    
    async def generate_comprehensive_tax_optimization(
        self,
        user_id: str,
        tax_year: int = 2025,
        projection_years: int = 30
    ) -> Dict[str, Any]:
        """
        Generate comprehensive tax optimization analysis and recommendations
        """
        logger.info(f"Generating comprehensive tax optimization for user {user_id}")
        
        try:
            # Get user profile and financial data
            user_profile = await self._get_user_profile(user_id)
            if not user_profile:
                raise ValueError(f"User profile not found for user {user_id}")
            
            # Get all accounts and holdings
            accounts = await self._get_user_accounts(user_id)
            holdings = await self._get_user_holdings(user_id)
            transactions = await self._get_recent_transactions(user_id)
            
            # Calculate current tax situation
            current_tax_situation = await self._calculate_current_tax_situation(user_profile, accounts)
            
            # Perform all optimization analyses
            optimization_results = {
                'user_id': user_id,
                'tax_year': tax_year,
                'analysis_date': datetime.utcnow().isoformat(),
                'current_tax_situation': current_tax_situation,
            }
            
            # 1. Tax-loss harvesting analysis
            logger.info("Analyzing tax-loss harvesting opportunities")
            tax_loss_analysis = await self._analyze_tax_loss_harvesting(
                user_id, holdings, transactions, user_profile, tax_year
            )
            optimization_results['tax_loss_harvesting'] = tax_loss_analysis
            
            # 2. Asset location optimization
            logger.info("Analyzing asset location optimization")
            asset_location_analysis = await self._analyze_asset_location(
                user_id, accounts, holdings, user_profile
            )
            optimization_results['asset_location'] = asset_location_analysis
            
            # 3. Roth conversion analysis
            logger.info("Analyzing Roth conversion opportunities")
            roth_conversion_analysis = await self._analyze_roth_conversions(
                user_id, user_profile, projection_years
            )
            optimization_results['roth_conversions'] = roth_conversion_analysis
            
            # 4. Tax-efficient withdrawal sequencing
            logger.info("Analyzing withdrawal sequencing strategies")
            withdrawal_analysis = await self._analyze_withdrawal_sequencing(
                user_id, accounts, user_profile
            )
            optimization_results['withdrawal_sequencing'] = withdrawal_analysis
            
            # 5. RMD optimization
            logger.info("Analyzing RMD strategies")
            rmd_analysis = await self._analyze_rmd_strategies(user_id, user_profile)
            optimization_results['rmd_strategies'] = rmd_analysis
            
            # 6. Charitable giving optimization
            logger.info("Analyzing charitable giving strategies")
            charitable_analysis = await self._analyze_charitable_giving(
                user_id, user_profile, holdings
            )
            optimization_results['charitable_giving'] = charitable_analysis
            
            # 7. Estate tax planning
            logger.info("Analyzing estate tax planning")
            estate_analysis = await self._analyze_estate_planning(user_id, user_profile)
            optimization_results['estate_planning'] = estate_analysis
            
            # 8. State tax optimization
            logger.info("Analyzing state tax optimization")
            state_tax_analysis = await self._analyze_state_tax_optimization(
                user_profile, accounts
            )
            optimization_results['state_tax_optimization'] = state_tax_analysis
            
            # 9. Generate integrated recommendations
            logger.info("Generating integrated recommendations")
            integrated_recommendations = await self._generate_integrated_recommendations(
                optimization_results, user_profile
            )
            optimization_results['integrated_recommendations'] = integrated_recommendations
            
            # 10. Implementation timeline
            implementation_timeline = await self._generate_implementation_timeline(
                optimization_results
            )
            optimization_results['implementation_timeline'] = implementation_timeline
            
            return optimization_results
            
        except Exception as e:
            logger.error(f"Error generating tax optimization for user {user_id}: {str(e)}")
            raise
    
    async def _get_user_profile(self, user_id: str) -> Optional[FinancialProfile]:
        """Get user's financial profile"""
        return self.db.query(FinancialProfile).filter(
            FinancialProfile.user_id == user_id
        ).first()
    
    async def _get_user_accounts(self, user_id: str) -> List[Dict]:
        """Get all user accounts across different account types"""
        accounts = []
        
        # Get tax accounts
        tax_accounts = self.db.query(TaxAccount).filter(
            TaxAccount.user_id == user_id,
            TaxAccount.is_active == True
        ).all()
        
        for account in tax_accounts:
            accounts.append({
                'account_id': account.id,
                'account_type': account.account_type,
                'tax_treatment': account.tax_treatment,
                'balance': account.current_balance,
                'account_category': 'tax_account'
            })
        
        # Get retirement accounts
        retirement_accounts = self.db.query(RetirementAccount).filter(
            RetirementAccount.user_id == user_id,
            RetirementAccount.is_active == True
        ).all()
        
        for account in retirement_accounts:
            accounts.append({
                'account_id': account.id,
                'account_type': account.account_type,
                'balance': account.current_balance,
                'account_category': 'retirement_account'
            })
        
        return accounts
    
    async def _get_user_holdings(self, user_id: str) -> List[Dict]:
        """Get all user holdings"""
        holdings = []
        
        # Get tax account holdings
        tax_holdings = (
            self.db.query(TaxAccountHolding)
            .join(TaxAccount)
            .filter(
                TaxAccount.user_id == user_id,
                TaxAccount.is_active == True
            )
            .all()
        )
        
        for holding in tax_holdings:
            holdings.append({
                'holding_id': holding.id,
                'account_id': holding.account_id,
                'symbol': holding.symbol,
                'shares': holding.shares,
                'cost_basis_per_share': holding.cost_basis_per_share,
                'current_price': holding.current_price,
                'asset_class': holding.asset_class,
                'purchase_date': holding.purchase_date,
                'holding_type': 'tax_account'
            })
        
        return holdings
    
    async def _get_recent_transactions(self, user_id: str) -> List[Dict]:
        """Get recent transactions for wash sale analysis"""
        transactions = []
        
        # Look back 60 days for wash sale analysis
        lookback_date = datetime.utcnow() - timedelta(days=60)
        
        tax_transactions = (
            self.db.query(TaxAccountTransaction)
            .join(TaxAccount)
            .filter(
                TaxAccount.user_id == user_id,
                TaxAccountTransaction.transaction_date >= lookback_date
            )
            .all()
        )
        
        for transaction in tax_transactions:
            transactions.append({
                'transaction_id': transaction.id,
                'account_id': transaction.account_id,
                'symbol': transaction.symbol,
                'transaction_type': transaction.transaction_type,
                'shares': transaction.shares,
                'price_per_share': transaction.price_per_share,
                'transaction_date': transaction.transaction_date,
            })
        
        return transactions
    
    async def _calculate_current_tax_situation(
        self,
        user_profile: FinancialProfile,
        accounts: List[Dict]
    ) -> Dict[str, Any]:
        """Calculate user's current tax situation"""
        
        # Get filing status
        filing_status = FilingStatus(user_profile.filing_status.lower())
        
        # Calculate income
        income = user_profile.annual_income or Decimal('0')
        
        # Calculate marginal and effective tax rates
        marginal_rate = self._calculate_marginal_tax_rate(income, filing_status)
        effective_rate = self._calculate_effective_tax_rate(income, filing_status)
        
        # Get state tax information
        state = user_profile.state or 'CA'
        state_profile = self.state_tax_profiles.get(state)
        
        # Calculate capital gains rates
        capital_gains_rates = self._get_capital_gains_rates(income, filing_status)
        
        # Calculate account balances by type
        account_balances = self._calculate_account_balances(accounts)
        
        return {
            'annual_income': float(income),
            'filing_status': filing_status.value,
            'federal_marginal_rate': float(marginal_rate),
            'federal_effective_rate': float(effective_rate),
            'state': state,
            'state_tax_rate': float(state_profile.income_tax_rate) if state_profile else 0.0,
            'combined_marginal_rate': float(marginal_rate + (state_profile.income_tax_rate if state_profile else Decimal('0'))),
            'capital_gains_rates': capital_gains_rates,
            'account_balances': account_balances,
            'tax_year': 2025,
        }
    
    def _calculate_marginal_tax_rate(
        self,
        income: Decimal,
        filing_status: FilingStatus
    ) -> Decimal:
        """Calculate federal marginal tax rate"""
        brackets = self.FEDERAL_TAX_BRACKETS_2025[filing_status]
        
        for bracket in reversed(brackets):
            if bracket.max_income is None or income > bracket.min_income:
                return bracket.rate
        
        return brackets[0].rate
    
    def _calculate_effective_tax_rate(
        self,
        income: Decimal,
        filing_status: FilingStatus
    ) -> Decimal:
        """Calculate federal effective tax rate"""
        brackets = self.FEDERAL_TAX_BRACKETS_2025[filing_status]
        
        total_tax = Decimal('0')
        remaining_income = income
        
        for bracket in brackets:
            if remaining_income <= 0:
                break
            
            bracket_width = (bracket.max_income or income) - bracket.min_income
            taxable_in_bracket = min(remaining_income, bracket_width)
            
            if taxable_in_bracket > 0:
                total_tax += taxable_in_bracket * bracket.rate
                remaining_income -= taxable_in_bracket
        
        return total_tax / income if income > 0 else Decimal('0')
    
    def _get_capital_gains_rates(
        self,
        income: Decimal,
        filing_status: FilingStatus
    ) -> Dict[str, float]:
        """Get capital gains tax rates"""
        brackets = self.CAPITAL_GAINS_BRACKETS_2025[filing_status]
        
        for bracket in reversed(brackets):
            if bracket.max_income is None or income > bracket.min_income:
                long_term_rate = bracket.rate
                break
        else:
            long_term_rate = brackets[0].rate
        
        # Short-term capital gains taxed as ordinary income
        short_term_rate = self._calculate_marginal_tax_rate(income, filing_status)
        
        return {
            'short_term': float(short_term_rate),
            'long_term': float(long_term_rate),
        }
    
    def _calculate_account_balances(self, accounts: List[Dict]) -> Dict[str, float]:
        """Calculate total balances by account type"""
        balances = {}
        
        for account in accounts:
            account_type = account['account_type']
            balance = account['balance'] or Decimal('0')
            
            if account_type not in balances:
                balances[account_type] = 0.0
            
            balances[account_type] += float(balance)
        
        return balances
    
    async def _analyze_tax_loss_harvesting(
        self,
        user_id: str,
        holdings: List[Dict],
        transactions: List[Dict],
        user_profile: FinancialProfile,
        tax_year: int
    ) -> Dict[str, Any]:
        """Comprehensive tax-loss harvesting analysis"""
        
        opportunities = []
        
        # Only analyze taxable account holdings
        taxable_holdings = [
            h for h in holdings 
            if h.get('holding_type') == 'tax_account'
        ]
        
        for holding in taxable_holdings:
            opportunity = await self._analyze_holding_for_tax_loss(
                holding, transactions, user_profile
            )
            if opportunity:
                opportunities.append(opportunity)
        
        # Sort by potential tax benefit
        opportunities.sort(key=lambda x: x.tax_benefit_short_term + x.tax_benefit_long_term, reverse=True)
        
        # Calculate total potential benefits
        total_short_term_benefit = sum(opp.tax_benefit_short_term for opp in opportunities)
        total_long_term_benefit = sum(opp.tax_benefit_long_term for opp in opportunities)
        total_losses = sum(opp.unrealized_loss for opp in opportunities)
        
        # Generate implementation strategy
        implementation_strategy = self._generate_harvesting_strategy(opportunities, user_profile)
        
        return {
            'opportunities_count': len(opportunities),
            'total_harvestable_losses': float(total_losses),
            'total_short_term_benefit': float(total_short_term_benefit),
            'total_long_term_benefit': float(total_long_term_benefit),
            'total_potential_benefit': float(total_short_term_benefit + total_long_term_benefit),
            'opportunities': [self._serialize_tax_loss_opportunity(opp) for opp in opportunities[:10]],  # Top 10
            'implementation_strategy': implementation_strategy,
            'annual_loss_limit': 3000.0,  # IRS limit for ordinary income offset
            'monitoring_recommendations': self._generate_harvesting_monitoring_plan()
        }
    
    async def _analyze_holding_for_tax_loss(
        self,
        holding: Dict,
        transactions: List[Dict],
        user_profile: FinancialProfile
    ) -> Optional[TaxLossOpportunity]:
        """Analyze individual holding for tax-loss harvesting potential"""
        
        # Calculate unrealized loss
        shares = holding['shares'] or Decimal('0')
        cost_basis = holding['cost_basis_per_share'] or Decimal('0')
        current_price = holding['current_price'] or Decimal('0')
        
        current_value = shares * current_price
        total_cost_basis = shares * cost_basis
        unrealized_loss = total_cost_basis - current_value
        
        # Skip if not a loss or loss is too small
        if unrealized_loss <= Decimal('100'):
            return None
        
        # Calculate tax benefits
        filing_status = FilingStatus(user_profile.filing_status.lower())
        income = user_profile.annual_income or Decimal('0')
        
        marginal_rate = self._calculate_marginal_tax_rate(income, filing_status)
        capital_gains_rates = self._get_capital_gains_rates(income, filing_status)
        
        # Determine holding period
        purchase_date = holding.get('purchase_date')
        if purchase_date:
            holding_period = (datetime.utcnow().date() - purchase_date.date()).days
            is_long_term = holding_period > 365
        else:
            is_long_term = False
        
        # Calculate tax benefits
        if is_long_term:
            tax_benefit_short_term = Decimal('0')
            tax_benefit_long_term = unrealized_loss * Decimal(str(capital_gains_rates['long_term']))
        else:
            tax_benefit_short_term = unrealized_loss * marginal_rate
            tax_benefit_long_term = Decimal('0')
        
        # Assess wash sale risk
        wash_sale_risk = self._assess_wash_sale_risk(
            holding['symbol'], transactions
        )
        
        # Find replacement securities
        replacements = self._find_replacement_securities(holding['symbol'])
        optimal_replacement = replacements[0] if replacements else None
        
        # Generate implementation steps
        implementation_steps = self._generate_harvesting_implementation_steps(
            holding, optimal_replacement, wash_sale_risk
        )
        
        # Identify risk factors
        risk_factors = self._identify_harvesting_risk_factors(
            holding, wash_sale_risk, replacements
        )
        
        # Determine implementation priority
        priority = self._calculate_implementation_priority(
            unrealized_loss, tax_benefit_short_term + tax_benefit_long_term, wash_sale_risk
        )
        
        return TaxLossOpportunity(
            holding_id=holding['holding_id'],
            symbol=holding['symbol'],
            asset_class=AssetClass(holding.get('asset_class', 'equities').lower()),
            current_price=current_price,
            cost_basis_per_share=cost_basis,
            shares=shares,
            purchase_date=purchase_date or datetime.utcnow(),
            unrealized_loss=unrealized_loss,
            tax_benefit_short_term=tax_benefit_short_term,
            tax_benefit_long_term=tax_benefit_long_term,
            wash_sale_risk_score=wash_sale_risk,
            replacement_securities=replacements,
            optimal_replacement=optimal_replacement,
            implementation_priority=priority,
            execution_timeline=implementation_steps,
            risk_factors=risk_factors
        )
    
    def _assess_wash_sale_risk(self, symbol: str, transactions: List[Dict]) -> float:
        """Assess wash sale rule violation risk (0.0 = no risk, 1.0 = high risk)"""
        current_date = datetime.utcnow().date()
        
        # Check for recent purchases of same or substantially identical security
        recent_purchases = [
            t for t in transactions
            if (t['symbol'] == symbol and 
                t['transaction_type'] == 'buy' and
                (current_date - t['transaction_date'].date()).days <= 30)
        ]
        
        if recent_purchases:
            # Calculate risk based on how recent the purchases were
            most_recent = max(
                (current_date - t['transaction_date'].date()).days 
                for t in recent_purchases
            )
            return max(0.0, 1.0 - (most_recent / 30.0))
        
        return 0.0
    
    def _find_replacement_securities(self, symbol: str) -> List[str]:
        """Find suitable replacement securities to avoid wash sale"""
        replacements = self.wash_sale_substitutes.get(symbol, [])
        
        # If no specific replacements found, suggest similar asset class funds
        if not replacements:
            # This would typically query a securities database
            # For now, return some generic alternatives
            if symbol.startswith(('SPY', 'VOO', 'VTI')):
                replacements = ['ITOT', 'SPTM', 'SCHB']
            elif symbol.startswith(('BND', 'AGG')):
                replacements = ['SCHZ', 'IUSB', 'VTEB']
        
        return replacements[:3]  # Return top 3 alternatives
    
    def _generate_harvesting_implementation_steps(
        self,
        holding: Dict,
        replacement: Optional[str],
        wash_sale_risk: float
    ) -> List[Dict]:
        """Generate step-by-step implementation plan for tax-loss harvesting"""
        steps = []
        
        if wash_sale_risk > 0.1:  # High wash sale risk
            days_to_wait = int(31 - (wash_sale_risk * 30))
            steps.append({
                'step': 1,
                'action': 'wait',
                'description': f"Wait {days_to_wait} days to clear wash sale period",
                'timing': f"{days_to_wait} days",
                'required': True
            })
        
        steps.append({
            'step': len(steps) + 1,
            'action': 'sell',
            'description': f"Sell {holding['shares']} shares of {holding['symbol']}",
            'timing': 'immediate' if wash_sale_risk <= 0.1 else 'after_wait_period',
            'required': True,
            'expected_proceeds': float(holding['shares'] * holding['current_price'])
        })
        
        if replacement:
            steps.append({
                'step': len(steps) + 1,
                'action': 'buy_replacement',
                'description': f"Purchase {replacement} as replacement security",
                'timing': 'immediate_after_sale',
                'required': False,
                'symbol': replacement,
                'rationale': 'Maintain similar market exposure while avoiding wash sale'
            })
        
        steps.append({
            'step': len(steps) + 1,
            'action': 'wait_repurchase',
            'description': f"Wait 31 days before repurchasing {holding['symbol']}",
            'timing': 'after_sale',
            'required': True,
            'note': 'Required to avoid wash sale rule violation'
        })
        
        return steps
    
    def _identify_harvesting_risk_factors(
        self,
        holding: Dict,
        wash_sale_risk: float,
        replacements: List[str]
    ) -> List[str]:
        """Identify potential risks with harvesting this position"""
        risks = []
        
        if wash_sale_risk > 0.1:
            risks.append(f"Wash sale risk: {wash_sale_risk:.1%}")
        
        if not replacements:
            risks.append("No suitable replacement securities identified")
        
        position_value = float(holding['shares'] * holding['current_price'])
        if position_value > 50000:
            risks.append("Large position size may impact market timing")
        
        if holding.get('dividend_yield', 0) > 0.03:
            risks.append("Position pays significant dividends - consider income impact")
        
        return risks
    
    def _calculate_implementation_priority(
        self,
        loss_amount: Decimal,
        tax_benefit: Decimal,
        wash_sale_risk: float
    ) -> int:
        """Calculate implementation priority (1 = highest, 10 = lowest)"""
        base_score = float(tax_benefit / 1000)  # Benefit per $1000
        
        # Adjust for wash sale risk
        if wash_sale_risk > 0.1:
            base_score *= (1 - wash_sale_risk)
        
        # Convert to priority ranking
        if base_score >= 5:
            return 1
        elif base_score >= 3:
            return 2
        elif base_score >= 1:
            return 3
        elif base_score >= 0.5:
            return 4
        else:
            return 5
    
    def _serialize_tax_loss_opportunity(self, opp: TaxLossOpportunity) -> Dict:
        """Serialize TaxLossOpportunity for JSON response"""
        return {
            'holding_id': opp.holding_id,
            'symbol': opp.symbol,
            'asset_class': opp.asset_class.value,
            'current_price': float(opp.current_price),
            'cost_basis_per_share': float(opp.cost_basis_per_share),
            'shares': float(opp.shares),
            'unrealized_loss': float(opp.unrealized_loss),
            'tax_benefit_short_term': float(opp.tax_benefit_short_term),
            'tax_benefit_long_term': float(opp.tax_benefit_long_term),
            'total_tax_benefit': float(opp.tax_benefit_short_term + opp.tax_benefit_long_term),
            'wash_sale_risk_score': opp.wash_sale_risk_score,
            'replacement_securities': opp.replacement_securities,
            'optimal_replacement': opp.optimal_replacement,
            'implementation_priority': opp.implementation_priority,
            'risk_factors': opp.risk_factors,
            'execution_timeline': opp.execution_timeline
        }
    
    def _generate_harvesting_strategy(
        self,
        opportunities: List[TaxLossOpportunity],
        user_profile: FinancialProfile
    ) -> Dict[str, Any]:
        """Generate comprehensive harvesting implementation strategy"""
        
        # Categorize opportunities
        immediate_opportunities = [opp for opp in opportunities if opp.wash_sale_risk_score <= 0.1]
        delayed_opportunities = [opp for opp in opportunities if opp.wash_sale_risk_score > 0.1]
        
        # Calculate annual loss utilization capacity
        annual_income = user_profile.annual_income or Decimal('0')
        
        # $3,000 annual ordinary income offset limit
        annual_loss_capacity = Decimal('3000')
        
        # Calculate optimal harvesting sequence
        current_year_harvest = []
        future_year_harvest = []
        
        running_total = Decimal('0')
        for opp in immediate_opportunities:
            if running_total + opp.unrealized_loss <= annual_loss_capacity * 3:  # 3 years of capacity
                current_year_harvest.append(opp)
                running_total += opp.unrealized_loss
            else:
                future_year_harvest.append(opp)
        
        return {
            'total_opportunities': len(opportunities),
            'immediate_opportunities': len(immediate_opportunities),
            'delayed_opportunities': len(delayed_opportunities),
            'current_year_recommendations': [
                {
                    'symbol': opp.symbol,
                    'loss_amount': float(opp.unrealized_loss),
                    'tax_benefit': float(opp.tax_benefit_short_term + opp.tax_benefit_long_term),
                    'priority': opp.implementation_priority
                }
                for opp in current_year_harvest[:5]  # Top 5 for current year
            ],
            'total_current_year_benefit': float(
                sum(opp.tax_benefit_short_term + opp.tax_benefit_long_term for opp in current_year_harvest)
            ),
            'future_opportunities': len(future_year_harvest),
            'strategy_notes': [
                f"Prioritize {len(immediate_opportunities)} immediate opportunities",
                f"Monitor {len(delayed_opportunities)} positions with wash sale concerns",
                f"Total harvestable losses: ${running_total:,.2f}",
                "Consider year-end timing for maximum tax benefit"
            ]
        }
    
    def _generate_harvesting_monitoring_plan(self) -> List[Dict]:
        """Generate ongoing monitoring plan for tax-loss harvesting"""
        return [
            {
                'frequency': 'weekly',
                'action': 'Monitor high-value loss positions',
                'description': 'Track positions with >$1,000 unrealized losses',
                'automation_available': True
            },
            {
                'frequency': 'monthly',
                'action': 'Review wash sale status',
                'description': 'Check all positions for wash sale rule compliance',
                'automation_available': True
            },
            {
                'frequency': 'quarterly',
                'action': 'Rebalance replacement securities',
                'description': 'Evaluate and rebalance temporary replacement positions',
                'automation_available': False
            },
            {
                'frequency': 'annually',
                'action': 'Year-end harvest review',
                'description': 'Final review before year-end to maximize tax benefits',
                'automation_available': False,
                'timing': 'November-December'
            }
        ]
    
    async def _analyze_asset_location(
        self,
        user_id: str,
        accounts: List[Dict],
        holdings: List[Dict],
        user_profile: FinancialProfile
    ) -> Dict[str, Any]:
        """Analyze asset location optimization opportunities"""
        
        recommendations = []
        
        # Group holdings by asset class and account type
        asset_allocation = {}
        for holding in holdings:
            asset_class = AssetClass(holding.get('asset_class', 'equities').lower())
            account_type = self._map_account_type(holding)
            
            if asset_class not in asset_allocation:
                asset_allocation[asset_class] = {}
            
            if account_type not in asset_allocation[asset_class]:
                asset_allocation[asset_class][account_type] = Decimal('0')
            
            market_value = holding['shares'] * holding['current_price']
            asset_allocation[asset_class][account_type] += market_value
        
        # Analyze each asset class for optimal location
        for asset_class, allocations in asset_allocation.items():
            recommendation = self._analyze_asset_class_location(
                asset_class, allocations, user_profile
            )
            if recommendation:
                recommendations.append(recommendation)
        
        # Sort by potential tax savings
        recommendations.sort(key=lambda x: x.annual_tax_savings, reverse=True)
        
        # Calculate total optimization potential
        total_annual_savings = sum(rec.annual_tax_savings for rec in recommendations)
        
        return {
            'total_recommendations': len(recommendations),
            'total_annual_tax_savings': float(total_annual_savings),
            'recommendations': [self._serialize_asset_location_recommendation(rec) for rec in recommendations[:10]],
            'asset_location_principles': self._get_asset_location_principles(),
            'implementation_complexity': self._assess_implementation_complexity(recommendations)
        }
    
    def _map_account_type(self, holding: Dict) -> TaxAccountType:
        """Map holding account type to standardized tax account type"""
        # This would map from the account information in the holding
        # For now, return a default mapping
        return TaxAccountType.TAXABLE  # Simplified for example
    
    def _analyze_asset_class_location(
        self,
        asset_class: AssetClass,
        current_allocations: Dict[TaxAccountType, Decimal],
        user_profile: FinancialProfile
    ) -> Optional[AssetLocationRecommendation]:
        """Analyze optimal location for specific asset class"""
        
        # Get location preferences for this asset class
        preferences = self.asset_location_preferences.get(asset_class, {})
        if not preferences:
            return None
        
        # Find current primary location
        total_allocation = sum(current_allocations.values())
        if total_allocation == 0:
            return None
        
        current_primary = max(current_allocations.items(), key=lambda x: x[1])
        current_account_type, current_amount = current_primary
        
        # Find optimal location
        optimal_account_type = max(preferences.items(), key=lambda x: x[1])[0]
        
        # Skip if already optimally located
        if current_account_type == optimal_account_type:
            return None
        
        # Calculate tax efficiency improvement
        current_efficiency = preferences.get(current_account_type, 0.0)
        optimal_efficiency = preferences.get(optimal_account_type, 0.0)
        
        if optimal_efficiency <= current_efficiency:
            return None
        
        # Estimate annual tax savings
        annual_tax_savings = self._estimate_asset_location_savings(
            asset_class, current_amount, current_efficiency, optimal_efficiency, user_profile
        )
        
        # Generate implementation steps
        implementation_steps = self._generate_asset_location_steps(
            asset_class, current_account_type, optimal_account_type, current_amount
        )
        
        return AssetLocationRecommendation(
            asset_class=asset_class,
            current_account_type=current_account_type,
            recommended_account_type=optimal_account_type,
            current_allocation=current_amount,
            recommended_allocation=current_amount,  # Same amount, different location
            annual_tax_savings=annual_tax_savings,
            implementation_steps=implementation_steps,
            tax_efficiency_score=optimal_efficiency - current_efficiency,
            priority_rank=1 if annual_tax_savings > Decimal('500') else 2
        )
    
    def _estimate_asset_location_savings(
        self,
        asset_class: AssetClass,
        amount: Decimal,
        current_efficiency: float,
        optimal_efficiency: float,
        user_profile: FinancialProfile
    ) -> Decimal:
        """Estimate annual tax savings from asset location optimization"""
        
        # Estimate annual income generated by asset class
        income_rates = {
            AssetClass.BONDS: Decimal('0.04'),
            AssetClass.CORPORATE_BONDS: Decimal('0.045'),
            AssetClass.HIGH_YIELD_BONDS: Decimal('0.06'),
            AssetClass.REITS: Decimal('0.05'),
            AssetClass.EQUITIES: Decimal('0.02'),  # Dividends
            AssetClass.LARGE_CAP_GROWTH: Decimal('0.01'),
            AssetClass.INTERNATIONAL_DEVELOPED: Decimal('0.025'),
        }
        
        annual_income = amount * income_rates.get(asset_class, Decimal('0.02'))
        
        # Calculate tax rate
        filing_status = FilingStatus(user_profile.filing_status.lower())
        income = user_profile.annual_income or Decimal('0')
        marginal_rate = self._calculate_marginal_tax_rate(income, filing_status)
        
        # Calculate efficiency improvement benefit
        efficiency_improvement = Decimal(str(optimal_efficiency - current_efficiency))
        annual_savings = annual_income * marginal_rate * efficiency_improvement
        
        return annual_savings
    
    def _generate_asset_location_steps(
        self,
        asset_class: AssetClass,
        current_account: TaxAccountType,
        target_account: TaxAccountType,
        amount: Decimal
    ) -> List[str]:
        """Generate implementation steps for asset location optimization"""
        steps = [
            f"Review current {asset_class.value} allocation in {current_account.value}",
            f"Assess available capacity in {target_account.value}",
            f"Plan tax-efficient transfer of ${amount:,.2f}",
        ]
        
        if current_account == TaxAccountType.TAXABLE:
            steps.append("Consider tax implications of selling current holdings")
            steps.append("Coordinate with tax-loss harvesting opportunities")
        
        steps.extend([
            f"Execute gradual transfer to {target_account.value}",
            "Monitor for rebalancing needs",
            "Document changes for tax reporting"
        ])
        
        return steps
    
    def _serialize_asset_location_recommendation(self, rec: AssetLocationRecommendation) -> Dict:
        """Serialize AssetLocationRecommendation for JSON response"""
        return {
            'asset_class': rec.asset_class.value,
            'current_account_type': rec.current_account_type.value,
            'recommended_account_type': rec.recommended_account_type.value,
            'current_allocation': float(rec.current_allocation),
            'annual_tax_savings': float(rec.annual_tax_savings),
            'tax_efficiency_score': rec.tax_efficiency_score,
            'priority_rank': rec.priority_rank,
            'implementation_steps': rec.implementation_steps
        }
    
    def _get_asset_location_principles(self) -> List[str]:
        """Get general asset location principles"""
        return [
            "Place tax-inefficient assets in tax-deferred accounts",
            "Place high-growth assets in Roth accounts for tax-free growth",
            "Keep international assets in taxable accounts for foreign tax credit",
            "Use municipal bonds in taxable accounts for tax-free income",
            "Consider state tax implications for location decisions",
            "Maintain overall portfolio balance across all accounts"
        ]
    
    def _assess_implementation_complexity(self, recommendations: List[AssetLocationRecommendation]) -> str:
        """Assess implementation complexity of asset location recommendations"""
        if not recommendations:
            return "Low"
        
        high_impact_count = sum(1 for rec in recommendations if rec.annual_tax_savings > Decimal('1000'))
        account_types_involved = len(set(rec.current_account_type for rec in recommendations))
        
        if high_impact_count >= 3 and account_types_involved >= 3:
            return "High"
        elif high_impact_count >= 2 or account_types_involved >= 2:
            return "Medium"
        else:
            return "Low"
    
    async def _analyze_roth_conversions(
        self,
        user_id: str,
        user_profile: FinancialProfile,
        projection_years: int
    ) -> Dict[str, Any]:
        """Comprehensive Roth conversion analysis and optimization"""
        
        # Get traditional retirement accounts
        traditional_accounts = [
            acc for acc in await self._get_user_accounts(user_id)
            if acc['account_type'] in ['traditional_401k', 'traditional_ira']
        ]
        
        if not traditional_accounts:
            return {
                'analysis_available': False,
                'reason': 'No traditional retirement accounts found',
                'recommendations': []
            }
        
        conversion_opportunities = []
        
        # Analyze conversion opportunities for each traditional account
        for account in traditional_accounts:
            opportunities = await self._analyze_account_roth_conversion(
                account, user_profile, projection_years
            )
            conversion_opportunities.extend(opportunities)
        
        # Sort by net present value
        conversion_opportunities.sort(key=lambda x: x.net_present_value, reverse=True)
        
        # Generate multi-year conversion ladder strategy
        conversion_ladder = self._generate_conversion_ladder_strategy(
            conversion_opportunities, user_profile, projection_years
        )
        
        # Calculate total optimization potential
        total_npv = sum(opp.net_present_value for opp in conversion_opportunities)
        
        return {
            'analysis_available': True,
            'total_conversion_opportunities': len(conversion_opportunities),
            'total_net_present_value': float(total_npv),
            'top_opportunities': [self._serialize_roth_opportunity(opp) for opp in conversion_opportunities[:5]],
            'conversion_ladder_strategy': conversion_ladder,
            'tax_considerations': self._get_roth_conversion_considerations(),
            'implementation_timeline': self._generate_roth_implementation_timeline(conversion_opportunities)
        }
    
    async def _analyze_account_roth_conversion(
        self,
        account: Dict,
        user_profile: FinancialProfile,
        projection_years: int
    ) -> List[RothConversionOpportunity]:
        """Analyze Roth conversion opportunities for a specific account"""
        opportunities = []
        
        balance = account['balance'] or Decimal('0')
        if balance < Decimal('5000'):  # Minimum threshold
            return opportunities
        
        # Analyze different conversion amounts
        conversion_percentages = [0.10, 0.25, 0.50, 1.00]  # 10%, 25%, 50%, 100%
        
        for percentage in conversion_percentages:
            conversion_amount = balance * Decimal(str(percentage))
            
            if conversion_amount < Decimal('1000'):
                continue
            
            opportunity = await self._evaluate_single_roth_conversion(
                conversion_amount, user_profile, projection_years
            )
            
            if opportunity and opportunity.net_present_value > Decimal('0'):
                opportunities.append(opportunity)
        
        return opportunities
    
    async def _evaluate_single_roth_conversion(
        self,
        conversion_amount: Decimal,
        user_profile: FinancialProfile,
        projection_years: int
    ) -> Optional[RothConversionOpportunity]:
        """Evaluate a single Roth conversion scenario"""
        
        # Calculate current tax cost
        filing_status = FilingStatus(user_profile.filing_status.lower())
        current_income = user_profile.annual_income or Decimal('0')
        current_marginal_rate = self._calculate_marginal_tax_rate(current_income, filing_status)
        
        # Calculate tax cost of conversion
        tax_cost = conversion_amount * current_marginal_rate
        
        # Project future tax savings
        retirement_age = user_profile.retirement_age or 65
        current_age = user_profile.age or 35
        years_to_retirement = max(1, retirement_age - current_age)
        
        # Assume modest growth rate for conservative estimates
        annual_growth_rate = Decimal('0.07')
        future_value = conversion_amount * (Decimal('1') + annual_growth_rate) ** years_to_retirement
        
        # Estimate future tax rates (assume similar to current)
        future_marginal_rate = current_marginal_rate
        future_tax_savings = future_value * future_marginal_rate
        
        # Calculate present value of future savings
        discount_rate = Decimal('0.04')  # Conservative discount rate
        present_value_savings = future_tax_savings / ((Decimal('1') + discount_rate) ** years_to_retirement)
        
        # Calculate net present value
        net_present_value = present_value_savings - tax_cost
        
        # Calculate break-even period
        if tax_cost > 0:
            break_even_years = int(
                years_to_retirement * (tax_cost / present_value_savings) if present_value_savings > 0 else 999
            )
        else:
            break_even_years = 0
        
        # Generate implementation timeline
        implementation_timeline = {
            'optimal_year': datetime.now().year + 1,  # Next tax year
            'quarterly_conversions': conversion_amount / 4,  # Spread over year
            'tax_planning_deadline': 'December 31st',
            'considerations': [
                'Monitor tax bracket thresholds',
                'Consider state tax implications',
                'Coordinate with other income sources'
            ]
        }
        
        # Risk considerations
        risk_considerations = []
        if conversion_amount > Decimal('50000'):
            risk_considerations.append("Large conversion may push into higher tax bracket")
        if years_to_retirement < 5:
            risk_considerations.append("Short time horizon limits tax-free growth benefit")
        if current_marginal_rate > Decimal('0.24'):
            risk_considerations.append("High current tax rate may reduce conversion benefit")
        
        return RothConversionOpportunity(
            traditional_ira_balance=conversion_amount * 4,  # Estimate total balance
            conversion_amount=conversion_amount,
            conversion_year=datetime.now().year + 1,
            current_tax_bracket=current_marginal_rate,
            future_tax_bracket=future_marginal_rate,
            tax_cost=tax_cost,
            future_tax_savings=present_value_savings,
            break_even_years=break_even_years,
            net_present_value=net_present_value,
            implementation_timeline=implementation_timeline,
            risk_considerations=risk_considerations
        )
    
    def _generate_conversion_ladder_strategy(
        self,
        opportunities: List[RothConversionOpportunity],
        user_profile: FinancialProfile,
        projection_years: int
    ) -> Dict[str, Any]:
        """Generate multi-year Roth conversion ladder strategy"""
        
        # Sort opportunities by conversion year and NPV
        sorted_opportunities = sorted(opportunities, key=lambda x: (x.conversion_year, -x.net_present_value))
        
        # Group by year and optimize annual conversions
        yearly_conversions = {}
        for opp in sorted_opportunities:
            year = opp.conversion_year
            if year not in yearly_conversions:
                yearly_conversions[year] = []
            yearly_conversions[year].append(opp)
        
        # Generate 5-year ladder strategy
        current_year = datetime.now().year
        ladder_strategy = {}
        
        for year_offset in range(5):
            year = current_year + year_offset + 1
            
            if year in yearly_conversions:
                year_opportunities = yearly_conversions[year]
                
                # Optimize conversions for this year
                optimal_conversion = self._optimize_yearly_conversion(
                    year_opportunities, user_profile
                )
                
                ladder_strategy[str(year)] = {
                    'recommended_conversion': float(optimal_conversion['total_amount']),
                    'tax_cost': float(optimal_conversion['tax_cost']),
                    'opportunities_count': len(year_opportunities),
                    'rationale': optimal_conversion['rationale']
                }
        
        total_ladder_value = sum(year_data['recommended_conversion'] for year_data in ladder_strategy.values())
        total_tax_cost = sum(year_data['tax_cost'] for year_data in ladder_strategy.values())
        
        return {
            'strategy_type': 'roth_conversion_ladder',
            'years_covered': len(ladder_strategy),
            'total_conversion_amount': total_ladder_value,
            'total_tax_cost': total_tax_cost,
            'annual_conversions': ladder_strategy,
            'key_benefits': [
                'Spreads tax cost over multiple years',
                'Manages tax bracket impact',
                'Provides flexibility for market timing',
                'Maximizes tax-free growth period'
            ]
        }
    
    def _optimize_yearly_conversion(
        self,
        year_opportunities: List[RothConversionOpportunity],
        user_profile: FinancialProfile
    ) -> Dict[str, Any]:
        """Optimize Roth conversions for a specific year"""
        
        # Calculate optimal amount to stay within current tax bracket
        annual_income = user_profile.annual_income or Decimal('0')
        filing_status = FilingStatus(user_profile.filing_status.lower())
        
        # Find current tax bracket ceiling
        brackets = self.FEDERAL_TAX_BRACKETS_2025[filing_status]
        current_bracket = None
        
        for bracket in brackets:
            if bracket.max_income and annual_income <= bracket.max_income:
                current_bracket = bracket
                break
        
        if current_bracket and current_bracket.max_income:
            # Calculate room in current bracket
            bracket_room = current_bracket.max_income - annual_income
            optimal_amount = min(
                bracket_room,
                sum(opp.conversion_amount for opp in year_opportunities)
            )
        else:
            # In highest bracket, use smaller conversion amount
            optimal_amount = Decimal('50000')  # Conservative amount
        
        # Calculate tax cost
        marginal_rate = self._calculate_marginal_tax_rate(annual_income, filing_status)
        tax_cost = optimal_amount * marginal_rate
        
        rationale = f"Optimized to stay within {current_bracket.bracket_name} tax bracket" if current_bracket else "Conservative conversion to manage tax impact"
        
        return {
            'total_amount': optimal_amount,
            'tax_cost': tax_cost,
            'rationale': rationale,
            'bracket_management': True
        }
    
    def _serialize_roth_opportunity(self, opp: RothConversionOpportunity) -> Dict:
        """Serialize RothConversionOpportunity for JSON response"""
        return {
            'conversion_amount': float(opp.conversion_amount),
            'conversion_year': opp.conversion_year,
            'tax_cost': float(opp.tax_cost),
            'future_tax_savings': float(opp.future_tax_savings),
            'net_present_value': float(opp.net_present_value),
            'break_even_years': opp.break_even_years,
            'current_tax_bracket': float(opp.current_tax_bracket),
            'implementation_timeline': opp.implementation_timeline,
            'risk_considerations': opp.risk_considerations
        }
    
    def _get_roth_conversion_considerations(self) -> List[str]:
        """Get key considerations for Roth conversions"""
        return [
            "Conversions are irreversible after the tax year ends",
            "Consider doing conversions early in the year for maximum growth",
            "Monitor required minimum distributions to optimize timing",
            "State tax implications may differ from federal treatment",
            "Consider impact on Medicare premiums and Social Security taxation",
            "Coordinate with charitable giving and other deduction strategies",
            "Market timing can significantly impact conversion value"
        ]
    
    def _generate_roth_implementation_timeline(
        self,
        opportunities: List[RothConversionOpportunity]
    ) -> List[Dict]:
        """Generate implementation timeline for Roth conversions"""
        timeline = []
        
        if opportunities:
            timeline.extend([
                {
                    'phase': 'Planning',
                    'timeframe': 'Q4 Current Year',
                    'actions': [
                        'Review current year tax situation',
                        'Project next year income and deductions',
                        'Confirm Roth IRA contribution eligibility',
                        'Set up Roth IRA if not already established'
                    ]
                },
                {
                    'phase': 'Execution',
                    'timeframe': 'Q1-Q3 Next Year',
                    'actions': [
                        'Execute conversion in quarterly installments',
                        'Monitor tax bracket thresholds',
                        'Track market performance impact',
                        'Adjust remaining conversions if needed'
                    ]
                },
                {
                    'phase': 'Management',
                    'timeframe': 'Ongoing',
                    'actions': [
                        'Monitor converted amounts for growth',
                        'Plan following year conversions',
                        'Consider recharacterization deadlines',
                        'Document for tax reporting'
                    ]
                }
            ])
        
        return timeline
    
    async def create_contribution_waterfall_strategy(
        self,
        user_id: str,
        available_contribution_amount: Decimal,
        user_profile: FinancialProfile
    ) -> Dict[str, Any]:
        """
        Create optimized contribution waterfall strategy with detailed prioritization.
        
        Prioritizes contributions based on:
        1. Employer match (immediate 100% return)
        2. HSA (triple tax advantage)
        3. High-deductible traditional accounts (if in high tax bracket)
        4. Roth accounts (for tax-free growth)
        5. Remaining traditional account space
        6. Taxable accounts
        """
        
        # Get all user accounts
        accounts = await self._get_user_accounts(user_id)
        
        contribution_plan = []
        remaining_contributions = available_contribution_amount
        
        # Step 1: Employer match (highest priority - 100% immediate return)
        employer_match_info = await self._get_employer_match_opportunities(user_id, user_profile)
        
        for match_opportunity in employer_match_info:
            if remaining_contributions <= 0:
                break
                
            contribution_amount = min(match_opportunity['match_amount'], remaining_contributions)
            
            if contribution_amount > 0:
                contribution_plan.append({
                    'priority': 1,
                    'account_type': match_opportunity['account_type'],
                    'account_id': match_opportunity['account_id'],
                    'contribution_amount': float(contribution_amount),
                    'immediate_benefit': float(contribution_amount),  # 100% match
                    'tax_savings': float(contribution_amount * self._get_deduction_value(user_profile)),
                    'rationale': f"Employer match provides immediate {match_opportunity['match_rate']:.0%} return",
                    'action_required': f"Contribute ${contribution_amount:,.2f} to capture full employer match"
                })
                remaining_contributions -= contribution_amount
        
        # Step 2: HSA contributions (triple tax advantage)
        hsa_opportunities = await self._get_hsa_opportunities(user_id, remaining_contributions)
        
        for hsa_opp in hsa_opportunities:
            if remaining_contributions <= 0:
                break
                
            contribution_plan.append({
                'priority': 2,
                'account_type': 'hsa',
                'account_id': hsa_opp['account_id'],
                'contribution_amount': float(hsa_opp['recommended_amount']),
                'tax_savings': float(hsa_opp['recommended_amount'] * self._get_deduction_value(user_profile)),
                'rationale': "Triple tax advantage: deductible contributions, tax-free growth, tax-free withdrawals for medical expenses",
                'action_required': f"Maximize HSA contribution of ${hsa_opp['recommended_amount']:,.2f}"
            })
            remaining_contributions -= hsa_opp['recommended_amount']
        
        # Step 3: Traditional retirement accounts (if high tax bracket)
        filing_status = FilingStatus(user_profile.filing_status.lower())
        income = user_profile.annual_income or Decimal('0')
        marginal_rate = self._calculate_marginal_tax_rate(income, filing_status)
        
        if marginal_rate >= Decimal('0.22'):  # 22% bracket or higher
            traditional_opportunities = await self._get_traditional_retirement_opportunities(
                user_id, remaining_contributions
            )
            
            for trad_opp in traditional_opportunities:
                if remaining_contributions <= 0:
                    break
                    
                contribution_plan.append({
                    'priority': 3,
                    'account_type': trad_opp['account_type'],
                    'account_id': trad_opp['account_id'],
                    'contribution_amount': float(trad_opp['recommended_amount']),
                    'tax_savings': float(trad_opp['recommended_amount'] * marginal_rate),
                    'rationale': f"High current tax rate ({marginal_rate:.1%}) makes traditional contributions attractive",
                    'action_required': f"Contribute ${trad_opp['recommended_amount']:,.2f} for immediate tax deduction"
                })
                remaining_contributions -= trad_opp['recommended_amount']
        
        # Step 4: Roth retirement accounts (tax-free growth)
        roth_opportunities = await self._get_roth_opportunities(user_id, remaining_contributions)
        
        for roth_opp in roth_opportunities:
            if remaining_contributions <= 0:
                break
                
            # Estimate long-term value of tax-free growth
            years_to_retirement = max(1, (user_profile.retirement_age or 65) - (user_profile.age or 35))
            long_term_value = roth_opp['recommended_amount'] * (Decimal('1.07') ** years_to_retirement)
            tax_free_benefit = long_term_value * marginal_rate
            
            contribution_plan.append({
                'priority': 4,
                'account_type': roth_opp['account_type'],
                'account_id': roth_opp['account_id'],
                'contribution_amount': float(roth_opp['recommended_amount']),
                'long_term_benefit': float(tax_free_benefit),
                'rationale': f"Tax-free growth over {years_to_retirement} years provides significant long-term value",
                'action_required': f"Contribute ${roth_opp['recommended_amount']:,.2f} for tax-free retirement income"
            })
            remaining_contributions -= roth_opp['recommended_amount']
        
        # Step 5: Fill remaining traditional account space (if not done in step 3)
        if marginal_rate < Decimal('0.22') and remaining_contributions > 0:
            remaining_traditional_opportunities = await self._get_traditional_retirement_opportunities(
                user_id, remaining_contributions
            )
            
            for trad_opp in remaining_traditional_opportunities:
                if remaining_contributions <= 0:
                    break
                    
                contribution_plan.append({
                    'priority': 5,
                    'account_type': trad_opp['account_type'],
                    'account_id': trad_opp['account_id'],
                    'contribution_amount': float(trad_opp['recommended_amount']),
                    'tax_savings': float(trad_opp['recommended_amount'] * marginal_rate),
                    'rationale': "Fill remaining tax-advantaged space for current tax deduction",
                    'action_required': f"Contribute ${trad_opp['recommended_amount']:,.2f} to traditional account"
                })
                remaining_contributions -= trad_opp['recommended_amount']
        
        # Step 6: Taxable investment accounts (after tax-advantaged space filled)
        if remaining_contributions > 0:
            contribution_plan.append({
                'priority': 6,
                'account_type': 'taxable',
                'account_id': 'taxable_investment',
                'contribution_amount': float(remaining_contributions),
                'tax_savings': 0.0,
                'rationale': "Tax-advantaged space maximized; additional savings in taxable account",
                'action_required': f"Invest ${remaining_contributions:,.2f} in tax-efficient funds in taxable account"
            })
        
        # Calculate total benefits
        total_immediate_benefits = sum(
            item.get('immediate_benefit', 0) + item.get('tax_savings', 0) 
            for item in contribution_plan
        )
        
        total_long_term_benefits = sum(
            item.get('long_term_benefit', 0) 
            for item in contribution_plan
        )
        
        return {
            'total_contribution_amount': float(available_contribution_amount),
            'contribution_recommendations': len(contribution_plan),
            'total_immediate_benefits': total_immediate_benefits,
            'total_long_term_benefits': total_long_term_benefits,
            'contribution_plan': contribution_plan,
            'implementation_notes': [
                "Execute contributions in priority order",
                "Consider spreading contributions throughout the year",
                "Monitor contribution limits and deadlines",
                "Coordinate with payroll deductions where possible"
            ],
            'tax_year_deadlines': {
                'employee_contributions': 'December 31st (through payroll)',
                'ira_contributions': 'April 15th (following tax year)',
                'hsa_contributions': 'April 15th (following tax year)'
            }
        }
    
    async def _get_employer_match_opportunities(
        self, 
        user_id: str, 
        user_profile: FinancialProfile
    ) -> List[Dict]:
        """Get employer match opportunities"""
        # This would query employer plan details
        # For now, return example data
        if user_profile.employer_401k_match_rate and user_profile.employer_401k_match_rate > 0:
            annual_income = user_profile.annual_income or Decimal('0')
            match_limit = min(
                annual_income * (user_profile.employer_401k_match_rate / 100),
                Decimal('15000')  # Reasonable match limit
            )
            
            return [{
                'account_type': 'traditional_401k',
                'account_id': 'employer_401k',
                'match_amount': match_limit,
                'match_rate': user_profile.employer_401k_match_rate / 100
            }]
        
        return []
    
    async def _get_hsa_opportunities(self, user_id: str, remaining_amount: Decimal) -> List[Dict]:
        """Get HSA contribution opportunities"""
        # HSA limits for 2025 (estimated)
        hsa_individual_limit = Decimal('4300')
        hsa_family_limit = Decimal('8550')
        hsa_catchup = Decimal('1000')  # Age 55+
        
        # This would check user's HSA eligibility and current contributions
        # For now, assume eligible and return opportunity
        return [{
            'account_id': 'primary_hsa',
            'account_type': 'hsa',
            'recommended_amount': min(remaining_amount, hsa_individual_limit)
        }]
    
    async def _get_traditional_retirement_opportunities(
        self, 
        user_id: str, 
        remaining_amount: Decimal
    ) -> List[Dict]:
        """Get traditional retirement account opportunities"""
        opportunities = []
        
        # 401k opportunity
        contribution_limit_401k = Decimal('23000')  # 2025 limit
        opportunities.append({
            'account_id': 'traditional_401k',
            'account_type': 'traditional_401k',
            'recommended_amount': min(remaining_amount, contribution_limit_401k)
        })
        
        # IRA opportunity if remaining amount after 401k
        if remaining_amount > contribution_limit_401k:
            ira_limit = Decimal('7000')  # 2025 limit
            opportunities.append({
                'account_id': 'traditional_ira',
                'account_type': 'traditional_ira',
                'recommended_amount': min(remaining_amount - contribution_limit_401k, ira_limit)
            })
        
        return opportunities
    
    async def _get_roth_opportunities(self, user_id: str, remaining_amount: Decimal) -> List[Dict]:
        """Get Roth retirement account opportunities"""
        opportunities = []
        
        # Roth 401k opportunity
        roth_401k_limit = Decimal('23000')  # 2025 limit
        opportunities.append({
            'account_id': 'roth_401k',
            'account_type': 'roth_401k',
            'recommended_amount': min(remaining_amount, roth_401k_limit)
        })
        
        # Roth IRA opportunity
        if remaining_amount > roth_401k_limit:
            roth_ira_limit = Decimal('7000')  # 2025 limit
            opportunities.append({
                'account_id': 'roth_ira',
                'account_type': 'roth_ira',
                'recommended_amount': min(remaining_amount - roth_401k_limit, roth_ira_limit)
            })
        
        return opportunities
    
    def _get_deduction_value(self, user_profile: FinancialProfile) -> Decimal:
        """Calculate the value of a tax deduction for this user"""
        filing_status = FilingStatus(user_profile.filing_status.lower())
        income = user_profile.annual_income or Decimal('0')
        return self._calculate_marginal_tax_rate(income, filing_status)
    
    async def calculate_required_minimum_distributions(
        self,
        user_id: str,
        user_profile: FinancialProfile,
        calculation_year: int
    ) -> Dict[str, Any]:
        """
        Calculate required minimum distributions with IRS compliance.
        
        Implements IRS Publication 590-B requirements for RMD calculations.
        """
        
        age = user_profile.age or 0
        
        # RMDs start at age 73 (SECURE Act 2.0 changes)
        rmd_start_age = 73
        
        if age < rmd_start_age:
            return {
                'rmd_required': False,
                'age': age,
                'years_until_rmd': rmd_start_age - age,
                'message': f"RMDs begin at age {rmd_start_age}. You have {rmd_start_age - age} years to optimize traditional account balances."
            }
        
        # Get accounts subject to RMD
        accounts = await self._get_user_accounts(user_id)
        rmd_accounts = [
            acc for acc in accounts
            if acc['account_type'] in ['traditional_401k', 'traditional_ira', 'sep_ira', 'simple_ira']
        ]
        
        if not rmd_accounts:
            return {
                'rmd_required': False,
                'reason': 'No accounts subject to RMD requirements',
                'recommendations': ['Consider Roth conversions to reduce future RMD burden']
            }
        
        # IRS Uniform Lifetime Table for RMD calculations
        uniform_lifetime_table = {
            73: 26.5, 74: 25.5, 75: 24.6, 76: 23.7, 77: 22.9,
            78: 22.0, 79: 21.1, 80: 20.2, 81: 19.4, 82: 18.5,
            83: 17.7, 84: 16.8, 85: 16.0, 86: 15.2, 87: 14.4,
            88: 13.7, 89: 12.9, 90: 12.2, 91: 11.5, 92: 10.8,
            93: 10.1, 94: 9.5, 95: 8.9, 96: 8.4, 97: 7.8,
            98: 7.3, 99: 6.8, 100: 6.4, 101: 6.0, 102: 5.7,
            103: 5.4, 104: 5.1, 105: 4.8, 106: 4.6, 107: 4.4,
            108: 4.1, 109: 3.9, 110: 3.7, 111: 3.4, 112: 3.1,
            113: 2.8, 114: 2.6, 115: 2.3
        }
        
        # Get life expectancy factor
        life_expectancy_factor = uniform_lifetime_table.get(age, 2.0)  # Default for 115+
        
        rmd_calculations = []
        total_rmd_amount = Decimal('0')
        
        for account in rmd_accounts:
            # Use December 31st balance of prior year for RMD calculation
            account_balance = account['balance'] or Decimal('0')
            
            # Calculate RMD for this account
            account_rmd = account_balance / Decimal(str(life_expectancy_factor))
            total_rmd_amount += account_rmd
            
            rmd_calculations.append({
                'account_id': account['account_id'],
                'account_type': account['account_type'],
                'balance': float(account_balance),
                'life_expectancy_factor': life_expectancy_factor,
                'required_distribution': float(account_rmd),
                'deadline': f"December 31, {calculation_year}",
                'penalty_rate': 0.25 if calculation_year >= 2023 else 0.50  # SECURE 2.0 reduced penalty
            })
        
        # Calculate tax implications
        filing_status = FilingStatus(user_profile.filing_status.lower())
        income = user_profile.annual_income or Decimal('0')
        marginal_rate = self._calculate_marginal_tax_rate(income + total_rmd_amount, filing_status)
        
        estimated_tax = total_rmd_amount * marginal_rate
        
        # Generate optimization strategies
        optimization_strategies = self._generate_rmd_optimization_strategies(
            rmd_calculations, user_profile, total_rmd_amount
        )
        
        # Generate distribution timeline
        distribution_timeline = self._generate_rmd_timeline(calculation_year, total_rmd_amount)
        
        return {
            'rmd_required': True,
            'calculation_year': calculation_year,
            'age': age,
            'life_expectancy_factor': life_expectancy_factor,
            'total_rmd_amount': float(total_rmd_amount),
            'estimated_tax_impact': float(estimated_tax),
            'marginal_tax_rate': float(marginal_rate),
            'account_calculations': rmd_calculations,
            'optimization_strategies': optimization_strategies,
            'distribution_timeline': distribution_timeline,
            'compliance_notes': self._get_rmd_compliance_notes(),
            'planning_opportunities': self._identify_rmd_planning_opportunities(user_profile, total_rmd_amount)
        }
    
    def _generate_rmd_optimization_strategies(
        self,
        rmd_calculations: List[Dict],
        user_profile: FinancialProfile,
        total_rmd: Decimal
    ) -> List[Dict]:
        """Generate strategies to optimize RMD tax impact"""
        strategies = []
        
        # Strategy 1: Timing optimization
        strategies.append({
            'strategy': 'Distribution Timing',
            'description': 'Optimize the timing of RMD distributions throughout the year',
            'benefits': ['Potential for market growth before distribution', 'Better cash flow management'],
            'implementation': [
                'Consider taking distributions late in the year',
                'Monitor market conditions for optimal timing',
                'Coordinate with other income sources'
            ],
            'estimated_benefit': 'Variable - depends on market performance'
        })
        
        # Strategy 2: QCD (Qualified Charitable Distribution)
        if user_profile.age and user_profile.age >= 70.5:
            max_qcd = min(total_rmd, Decimal('100000'))  # 2025 QCD limit
            
            strategies.append({
                'strategy': 'Qualified Charitable Distribution (QCD)',
                'description': 'Direct distribution from IRA to qualified charity',
                'benefits': ['Excludes distribution from taxable income', 'Satisfies RMD requirement'],
                'max_annual_amount': float(max_qcd),
                'tax_savings': float(max_qcd * self._get_deduction_value(user_profile)),
                'requirements': [
                    'Must be age 70½ or older',
                    'Distribution must go directly to qualified charity',
                    'Maximum $100,000 per year',
                    'Only available from traditional IRAs'
                ]
            })
        
        # Strategy 3: Tax-efficient withdrawal sequencing
        strategies.append({
            'strategy': 'Multi-Account Coordination',
            'description': 'Coordinate RMDs with other retirement account withdrawals',
            'benefits': ['Optimize overall tax bracket management', 'Preserve tax-free growth in Roth accounts'],
            'implementation': [
                'Take RMDs first to satisfy requirements',
                'Use remaining income needs from Roth accounts',
                'Consider converting traditional to Roth in low-income years'
            ]
        })
        
        # Strategy 4: Asset location within retirement accounts
        strategies.append({
            'strategy': 'In-Kind Distribution Strategy',
            'description': 'Distribute low-basis securities to minimize immediate tax impact',
            'benefits': ['Preserve high-basis securities in tax-deferred accounts', 'Step-up basis potential'],
            'considerations': [
                'Requires careful tracking of cost basis',
                'May affect overall asset allocation',
                'Consider market timing implications'
            ]
        })
        
        return strategies
    
    def _generate_rmd_timeline(self, calculation_year: int, total_rmd: Decimal) -> List[Dict]:
        """Generate RMD distribution timeline"""
        return [
            {
                'period': 'January - March',
                'action': 'Plan and calculate RMDs',
                'tasks': [
                    'Obtain December 31st account balances',
                    'Calculate RMD amounts for each account',
                    'Review beneficiary designations',
                    'Plan distribution strategy'
                ]
            },
            {
                'period': 'April - June',
                'action': 'Begin distributions if needed',
                'tasks': [
                    'Take early distributions if cash flow needed',
                    'Consider QCD opportunities',
                    'Monitor account performance'
                ]
            },
            {
                'period': 'July - September',
                'action': 'Mid-year review',
                'tasks': [
                    'Review year-to-date distributions',
                    'Assess tax impact and adjust strategy',
                    'Consider additional Roth conversions'
                ]
            },
            {
                'period': 'October - December',
                'action': 'Complete RMD requirements',
                'tasks': [
                    f'Ensure ${total_rmd:,.2f} total RMD is satisfied',
                    'Complete any remaining distributions',
                    'Plan for following year',
                    'Final deadline: December 31st'
                ]
            }
        ]
    
    def _get_rmd_compliance_notes(self) -> List[str]:
        """Get important RMD compliance notes"""
        return [
            "RMDs must begin by April 1st of the year after reaching age 73",
            "Subsequent RMDs must be taken by December 31st each year",
            "Penalty for missed or insufficient RMDs is 25% of the shortfall (reduced from 50% by SECURE 2.0)",
            "RMDs are calculated separately for each account but can be taken from any traditional IRA",
            "401(k) RMDs must be taken from each 401(k) account separately",
            "Roth IRAs are not subject to RMD requirements during owner's lifetime",
            "QCDs can satisfy RMD requirements up to $100,000 annually"
        ]
    
    def _identify_rmd_planning_opportunities(
        self,
        user_profile: FinancialProfile,
        total_rmd: Decimal
    ) -> List[str]:
        """Identify planning opportunities related to RMDs"""
        opportunities = []
        
        age = user_profile.age or 0
        
        if age < 73:
            years_remaining = 73 - age
            opportunities.extend([
                f"Consider Roth conversions over the next {years_remaining} years to reduce future RMDs",
                "Maximize current tax-deferred contributions while in lower tax brackets",
                "Plan for the tax impact of future RMDs in retirement income projections"
            ])
        else:
            opportunities.extend([
                "Consider QCDs if you have charitable giving goals",
                "Evaluate Roth conversion opportunities in years with lower income",
                "Coordinate RMDs with Social Security claiming strategy"
            ])
        
        if total_rmd > Decimal('50000'):
            opportunities.append("Large RMDs may benefit from professional tax planning and multi-year strategies")
        
        return opportunities