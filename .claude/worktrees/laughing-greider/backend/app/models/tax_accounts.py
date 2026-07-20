"""
Tax-Aware Account Models for Financial Planning System
Implements comprehensive tax account management with 2025 IRS limits
"""

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, JSONB, Enum, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from decimal import Decimal
from datetime import datetime, date
from typing import Dict, List, Optional, Union
import enum
import uuid

Base = declarative_base()

# 2025 IRS Contribution Limits and Rules
class IRSLimits2025:
    """2025 IRS contribution limits and tax rules"""
    
    # 401(k) Limits
    EMPLOYEE_401K_LIMIT = 23500
    CATCH_UP_401K_LIMIT = 7500  # Age 50+
    MAX_401K_WITH_CATCHUP = EMPLOYEE_401K_LIMIT + CATCH_UP_401K_LIMIT
    TOTAL_401K_LIMIT = 70000  # Employee + employer combined
    TOTAL_401K_WITH_CATCHUP = 77500
    
    # IRA Limits
    TRADITIONAL_IRA_LIMIT = 7000
    ROTH_IRA_LIMIT = 7000
    IRA_CATCH_UP = 1000  # Age 50+
    MAX_IRA_WITH_CATCHUP = 8000
    
    # IRA Phase-out ranges (AGI)
    ROTH_PHASEOUT_SINGLE = (139000, 154000)
    ROTH_PHASEOUT_MARRIED = (218000, 228000)
    TRADITIONAL_PHASEOUT_SINGLE = (77000, 87000)  # With workplace plan
    TRADITIONAL_PHASEOUT_MARRIED = (123000, 143000)  # With workplace plan
    
    # HSA Limits
    HSA_INDIVIDUAL_LIMIT = 4150
    HSA_FAMILY_LIMIT = 8300
    HSA_CATCH_UP = 1000  # Age 55+
    
    # 529 Plan Limits
    ANNUAL_GIFT_TAX_EXCLUSION = 18000
    FIVE_YEAR_529_ELECTION = 90000  # 5x annual exclusion
    
    # Social Security
    SS_WAGE_BASE = 176100  # Maximum taxable earnings
    
    # Required Minimum Distribution
    RMD_AGE = 73  # Starting age for RMDs
    
    # Tax Brackets (simplified - would be more detailed in production)
    STANDARD_DEDUCTION_SINGLE = 14600
    STANDARD_DEDUCTION_MARRIED = 29200


class AccountTypeEnum(enum.Enum):
    """Types of tax-advantaged accounts"""
    TRADITIONAL_401K = "traditional_401k"
    ROTH_401K = "roth_401k"
    TRADITIONAL_403B = "traditional_403b"
    ROTH_403B = "roth_403b"
    TRADITIONAL_IRA = "traditional_ira"
    ROTH_IRA = "roth_ira"
    SEP_IRA = "sep_ira"
    SIMPLE_IRA = "simple_ira"
    HSA = "hsa"
    PLAN_529 = "529_plan"
    COVERDELL_ESA = "coverdell_esa"
    TAXABLE = "taxable"
    BROKERAGE = "brokerage"


class TaxTreatmentEnum(enum.Enum):
    """Tax treatment categories"""
    TAX_DEFERRED = "tax_deferred"  # Traditional 401k, IRA
    TAX_FREE = "tax_free"  # Roth accounts, HSA (qualified)
    TAXABLE = "taxable"  # Regular brokerage
    TAX_EXEMPT = "tax_exempt"  # Municipal bonds


class AssetLocationPriorityEnum(enum.Enum):
    """Priority for asset location optimization"""
    HIGH = "high"  # Tax-inefficient assets
    MEDIUM = "medium"
    LOW = "low"  # Tax-efficient assets


class TaxAccount(Base):
    """Base model for tax-advantaged accounts"""
    __tablename__ = "tax_accounts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    account_type = Column(Enum(AccountTypeEnum), nullable=False)
    account_name = Column(String(255), nullable=False)
    institution_name = Column(String(255))
    account_number = Column(String(100))
    
    # Balance and contribution tracking
    current_balance = Column(Numeric(15, 2), nullable=False, default=0)
    annual_contribution = Column(Numeric(15, 2), default=0)
    employer_contribution = Column(Numeric(15, 2), default=0)
    total_contributions = Column(Numeric(15, 2), default=0)
    
    # Tax treatment
    tax_treatment = Column(Enum(TaxTreatmentEnum), nullable=False)
    marginal_tax_rate = Column(Float, default=0.22)
    
    # Account limits and rules
    contribution_limit = Column(Numeric(15, 2))
    catch_up_eligible = Column(Boolean, default=False)
    employer_match_rate = Column(Float, default=0)
    employer_match_limit = Column(Numeric(15, 2))
    vesting_schedule = Column(JSONB)  # Vesting percentages by year
    
    # Asset location optimization
    asset_location_priority = Column(Enum(AssetLocationPriorityEnum))
    tax_efficiency_score = Column(Float)  # 0-1 scale
    
    # RMD tracking
    rmd_required = Column(Boolean, default=False)
    rmd_start_age = Column(Integer, default=IRSLimits2025.RMD_AGE)
    current_year_rmd = Column(Numeric(15, 2))
    
    # Account metadata
    opened_date = Column(DateTime)
    is_active = Column(Boolean, default=True)
    state_tax_benefits = Column(JSONB)  # State-specific benefits
    beneficiaries = Column(JSONB)  # Beneficiary information
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    holdings = relationship("TaxAccountHolding", back_populates="account")
    transactions = relationship("TaxAccountTransaction", back_populates="account")
    user = relationship("User", back_populates="tax_accounts")


class TaxAccountHolding(Base):
    """Holdings within tax accounts for asset location optimization"""
    __tablename__ = "tax_account_holdings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(UUID(as_uuid=True), ForeignKey("tax_accounts.id"), nullable=False)
    symbol = Column(String(20), nullable=False)
    asset_class = Column(String(50))  # equity, fixed_income, reit, commodity
    asset_type = Column(String(50))  # stock, bond, mutual_fund, etf
    
    # Position details
    shares = Column(Numeric(15, 6), nullable=False)
    cost_basis_per_share = Column(Numeric(15, 4))
    current_price = Column(Numeric(15, 4))
    market_value = Column(Numeric(15, 2))
    
    # Tax characteristics
    dividend_yield = Column(Float, default=0)
    turnover_ratio = Column(Float)  # For funds
    tax_efficiency_rating = Column(String(10))  # A, B, C, D
    generates_k1 = Column(Boolean, default=False)  # Tax complexity
    
    # Asset location metrics
    optimal_location_score = Column(Float)  # How well placed this asset is
    location_priority = Column(Enum(AssetLocationPriorityEnum))
    
    # Performance tracking
    unrealized_gain_loss = Column(Numeric(15, 2))
    realized_gain_loss_ytd = Column(Numeric(15, 2), default=0)
    
    # Wash sale tracking
    last_sale_date = Column(DateTime)
    wash_sale_period_active = Column(Boolean, default=False)
    
    acquired_date = Column(DateTime, nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    account = relationship("TaxAccount", back_populates="holdings")
    transactions = relationship("TaxAccountTransaction", 
                              foreign_keys="TaxAccountTransaction.holding_id")


class TaxAccountTransaction(Base):
    """Transactions within tax accounts"""
    __tablename__ = "tax_account_transactions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(UUID(as_uuid=True), ForeignKey("tax_accounts.id"), nullable=False)
    holding_id = Column(UUID(as_uuid=True), ForeignKey("tax_account_holdings.id"))
    
    # Transaction details
    transaction_type = Column(String(20), nullable=False)  # buy, sell, dividend, contribution
    symbol = Column(String(20))
    shares = Column(Numeric(15, 6))
    price_per_share = Column(Numeric(15, 4))
    total_amount = Column(Numeric(15, 2), nullable=False)
    
    # Tax implications
    wash_sale = Column(Boolean, default=False)
    disallowed_loss = Column(Numeric(15, 2))
    tax_lot_method = Column(String(20))  # FIFO, LIFO, specific_id
    
    # For contributions
    contribution_type = Column(String(20))  # employee, employer, rollover
    tax_year = Column(Integer)
    
    transaction_date = Column(DateTime, nullable=False)
    settlement_date = Column(DateTime)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    account = relationship("TaxAccount", back_populates="transactions")
    holding = relationship("TaxAccountHolding", 
                         foreign_keys=[holding_id])


class RothConversionRecord(Base):
    """Track Roth conversions for tax planning"""
    __tablename__ = "roth_conversion_records"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Conversion details
    from_account_id = Column(UUID(as_uuid=True), ForeignKey("tax_accounts.id"))
    to_account_id = Column(UUID(as_uuid=True), ForeignKey("tax_accounts.id"))
    conversion_amount = Column(Numeric(15, 2), nullable=False)
    
    # Tax implications
    taxable_amount = Column(Numeric(15, 2), nullable=False)
    tax_rate_at_conversion = Column(Float)
    taxes_paid = Column(Numeric(15, 2))
    
    # Conversion strategy
    conversion_reason = Column(String(255))  # market_dip, low_income_year, etc.
    five_year_rule_date = Column(DateTime)  # When penalty-free withdrawals start
    
    conversion_date = Column(DateTime, nullable=False)
    tax_year = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    from_account = relationship("TaxAccount", foreign_keys=[from_account_id])
    to_account = relationship("TaxAccount", foreign_keys=[to_account_id])


class RequiredMinimumDistribution(Base):
    """RMD calculations and tracking"""
    __tablename__ = "required_minimum_distributions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    account_id = Column(UUID(as_uuid=True), ForeignKey("tax_accounts.id"), nullable=False)
    
    # RMD calculation
    calculation_year = Column(Integer, nullable=False)
    account_balance_previous_year = Column(Numeric(15, 2), nullable=False)
    life_expectancy_factor = Column(Float, nullable=False)
    required_distribution = Column(Numeric(15, 2), nullable=False)
    
    # Distribution tracking
    distributed_amount = Column(Numeric(15, 2), default=0)
    remaining_amount = Column(Numeric(15, 2))
    due_date = Column(DateTime, nullable=False)  # December 31st
    
    # Status
    status = Column(String(20), default='pending')  # pending, partial, complete, overdue
    penalty_applied = Column(Boolean, default=False)
    penalty_amount = Column(Numeric(15, 2))
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    account = relationship("TaxAccount")


class TaxLossHarvestingOpportunity(Base):
    """Track tax loss harvesting opportunities"""
    __tablename__ = "tax_loss_harvesting_opportunities"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    holding_id = Column(UUID(as_uuid=True), ForeignKey("tax_account_holdings.id"))
    
    # Opportunity details
    symbol = Column(String(20), nullable=False)
    current_price = Column(Numeric(15, 4), nullable=False)
    cost_basis = Column(Numeric(15, 4), nullable=False)
    unrealized_loss = Column(Numeric(15, 2), nullable=False)
    tax_benefit = Column(Numeric(15, 2), nullable=False)
    
    # Replacement security
    replacement_symbol = Column(String(20))
    replacement_name = Column(String(255))
    correlation_score = Column(Float)  # How similar to original
    
    # Wash sale compliance
    wash_sale_safe = Column(Boolean, default=False)
    safe_date = Column(DateTime)  # When wash sale period expires
    
    # Opportunity scoring
    priority_score = Column(Float)  # 0-100 based on tax benefit and ease
    implementation_complexity = Column(String(20))  # simple, moderate, complex
    
    # Status tracking
    status = Column(String(20), default='identified')  # identified, planned, executed, expired
    identified_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    expiration_date = Column(DateTime)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    holding = relationship("TaxAccountHolding")


class AssetLocationAnalysis(Base):
    """Asset location optimization analysis"""
    __tablename__ = "asset_location_analysis"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Analysis metadata
    analysis_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    total_portfolio_value = Column(Numeric(15, 2), nullable=False)
    
    # Current allocation efficiency
    current_tax_drag = Column(Numeric(15, 2))  # Annual tax cost
    optimal_tax_drag = Column(Numeric(15, 2))  # After optimization
    potential_savings = Column(Numeric(15, 2))
    
    # Account utilization
    account_utilization = Column(JSONB)  # How well each account is used
    rebalancing_needs = Column(JSONB)  # Recommended moves
    
    # Optimization recommendations
    recommendations = Column(JSONB)  # List of specific actions
    implementation_steps = Column(JSONB)  # Step-by-step guide
    estimated_implementation_cost = Column(Numeric(15, 2))
    
    # Analysis quality
    confidence_score = Column(Float)  # 0-1 confidence in analysis
    data_completeness = Column(Float)  # 0-1 how complete the data is
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class TaxProjection(Base):
    """Long-term tax projections for planning"""
    __tablename__ = "tax_projections"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Projection parameters
    projection_year = Column(Integer, nullable=False)
    age_at_projection = Column(Integer)
    income_projection = Column(Numeric(15, 2))
    tax_rate_assumption = Column(Float)
    
    # Account projections
    account_balances = Column(JSONB)  # Projected balances by account
    contribution_projections = Column(JSONB)  # Planned contributions
    withdrawal_projections = Column(JSONB)  # Planned withdrawals
    
    # Tax implications
    projected_tax_liability = Column(Numeric(15, 2))
    rmd_obligations = Column(JSONB)  # Required minimum distributions
    conversion_opportunities = Column(JSONB)  # Roth conversion windows
    
    # Scenario analysis
    scenario_name = Column(String(100))  # base_case, optimistic, pessimistic
    scenario_assumptions = Column(JSONB)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


# Tax calculation utilities
class TaxCalculationUtils:
    """Utility functions for tax calculations"""
    
    @staticmethod
    def get_contribution_limit(account_type: AccountTypeEnum, age: int, 
                             filing_status: str = 'single', income: float = 0) -> float:
        """Get contribution limit for account type considering age and income"""
        
        if account_type in [AccountTypeEnum.TRADITIONAL_401K, AccountTypeEnum.ROTH_401K]:
            base_limit = IRSLimits2025.EMPLOYEE_401K_LIMIT
            if age >= 50:
                base_limit += IRSLimits2025.CATCH_UP_401K_LIMIT
            return base_limit
            
        elif account_type in [AccountTypeEnum.TRADITIONAL_IRA, AccountTypeEnum.ROTH_IRA]:
            base_limit = IRSLimits2025.TRADITIONAL_IRA_LIMIT
            if age >= 50:
                base_limit += IRSLimits2025.IRA_CATCH_UP
                
            # Apply phase-out rules for Roth IRA
            if account_type == AccountTypeEnum.ROTH_IRA:
                if filing_status == 'single':
                    phase_out = IRSLimits2025.ROTH_PHASEOUT_SINGLE
                else:
                    phase_out = IRSLimits2025.ROTH_PHASEOUT_MARRIED
                
                if income <= phase_out[0]:
                    return base_limit
                elif income >= phase_out[1]:
                    return 0
                else:
                    # Linear phase-out
                    reduction_ratio = (income - phase_out[0]) / (phase_out[1] - phase_out[0])
                    return base_limit * (1 - reduction_ratio)
            
            return base_limit
            
        elif account_type == AccountTypeEnum.HSA:
            # HSA limits depend on coverage type - simplified here
            base_limit = IRSLimits2025.HSA_INDIVIDUAL_LIMIT
            if age >= 55:
                base_limit += IRSLimits2025.HSA_CATCH_UP
            return base_limit
            
        return 0
    
    @staticmethod
    def calculate_rmd(balance: float, age: int) -> float:
        """Calculate required minimum distribution"""
        # IRS Uniform Lifetime Table - simplified
        life_expectancy_factors = {
            73: 26.5, 74: 25.5, 75: 24.6, 76: 23.7, 77: 22.9,
            78: 22.0, 79: 21.1, 80: 20.2, 81: 19.4, 82: 18.5,
            83: 17.7, 84: 16.8, 85: 16.0, 86: 15.2, 87: 14.4,
            88: 13.7, 89: 12.9, 90: 12.2, 91: 11.5, 92: 10.8,
            93: 10.1, 94: 9.5, 95: 8.9
        }
        
        if age < IRSLimits2025.RMD_AGE:
            return 0
        
        factor = life_expectancy_factors.get(age, 8.9)  # Default to age 95+ factor
        return balance / factor
    
    @staticmethod
    def assess_tax_efficiency(asset_class: str, dividend_yield: float, 
                            turnover_ratio: float = 0) -> str:
        """Assess tax efficiency of an asset"""
        score = 0
        
        # Dividend yield impact
        if dividend_yield <= 0.01:
            score += 3
        elif dividend_yield <= 0.03:
            score += 2
        elif dividend_yield <= 0.05:
            score += 1
        # High dividend = 0 points
        
        # Turnover ratio impact (for funds)
        if turnover_ratio <= 0.1:
            score += 2
        elif turnover_ratio <= 0.3:
            score += 1
        # High turnover = 0 points
        
        # Asset class considerations
        if asset_class in ['growth_stock', 'index_fund']:
            score += 1
        elif asset_class in ['bond', 'reit']:
            score -= 1
        
        # Convert to letter grade
        if score >= 5:
            return 'A'  # Very tax efficient
        elif score >= 3:
            return 'B'  # Tax efficient
        elif score >= 1:
            return 'C'  # Moderately tax efficient
        else:
            return 'D'  # Tax inefficient