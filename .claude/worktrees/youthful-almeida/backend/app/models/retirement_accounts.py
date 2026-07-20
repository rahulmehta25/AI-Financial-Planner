"""
Comprehensive retirement account models for 401(k), IRA, Roth IRA, 529 Education Plans, and HSA accounts
with IRS compliance, contribution limits, and tax calculations
"""

import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from decimal import Decimal
from enum import Enum

from sqlalchemy import (
    Column, String, Integer, DateTime, Boolean, Text, JSON, 
    ForeignKey, Index, CheckConstraint, DECIMAL, BigInteger,
    text, event, UniqueConstraint, Float
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, NUMERIC, TIMESTAMP
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import relationship, validates
from sqlalchemy.ext.hybrid import hybrid_property

from app.database.base import Base
from app.database.models import AuditMixin


class AccountType(str, Enum):
    """Retirement account types"""
    TRADITIONAL_401K = "traditional_401k"
    ROTH_401K = "roth_401k"
    TRADITIONAL_IRA = "traditional_ira"
    ROTH_IRA = "roth_ira"
    SIMPLE_IRA = "simple_ira"
    SEP_IRA = "sep_ira"
    EDUCATION_529 = "education_529"
    HSA = "hsa"
    PENSION = "pension"


class ContributionType(str, Enum):
    """Types of contributions"""
    EMPLOYEE_PRETAX = "employee_pretax"
    EMPLOYEE_ROTH = "employee_roth"
    EMPLOYER_MATCH = "employer_match"
    EMPLOYER_NONELECTIVE = "employer_nonelective"
    PROFIT_SHARING = "profit_sharing"
    ROLLOVER = "rollover"
    CONVERSION = "conversion"


class TaxTreatment(str, Enum):
    """Tax treatment of accounts"""
    TAX_DEFERRED = "tax_deferred"  # Traditional accounts
    TAX_FREE = "tax_free"  # Roth accounts
    TRIPLE_TAX_ADVANTAGE = "triple_tax_advantage"  # HSA
    AFTER_TAX = "after_tax"  # 529 plans


class IRSContributionLimits(Base, AuditMixin):
    """IRS contribution limits by year and account type"""
    __tablename__ = "irs_contribution_limits"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tax_year = Column(Integer, nullable=False)
    account_type = Column(String(50), nullable=False)
    
    # Contribution limits
    regular_limit = Column(NUMERIC(12, 2), nullable=False)
    catch_up_limit = Column(NUMERIC(12, 2), default=0)  # Additional for 50+ years old
    catch_up_age = Column(Integer, default=50)
    
    # Income limits for eligibility (Roth IRA, etc.)
    income_phase_out_start_single = Column(NUMERIC(12, 2))
    income_phase_out_end_single = Column(NUMERIC(12, 2))
    income_phase_out_start_married = Column(NUMERIC(12, 2))
    income_phase_out_end_married = Column(NUMERIC(12, 2))
    
    # Special limits
    employer_match_limit = Column(NUMERIC(12, 2))  # For 401k matching
    total_plan_limit = Column(NUMERIC(12, 2))  # Total 401k contributions (employee + employer)
    
    # HSA specific limits
    hsa_family_limit = Column(NUMERIC(12, 2))  # Family coverage limit for HSA
    
    # Metadata
    cola_adjustment = Column(NUMERIC(5, 4))  # Cost of living adjustment
    irs_announcement_date = Column(DateTime(timezone=True))
    effective_date = Column(DateTime(timezone=True), nullable=False)
    
    __table_args__ = (
        UniqueConstraint('tax_year', 'account_type', name='unique_year_account_type'),
        Index('idx_contribution_limits_year', 'tax_year'),
        Index('idx_contribution_limits_type', 'account_type'),
    )


class RetirementAccount(Base, AuditMixin):
    """Base retirement account model"""
    __tablename__ = "retirement_accounts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    plan_id = Column(UUID(as_uuid=True), ForeignKey("plans.id"))
    
    # Account identification
    account_type = Column(String(50), nullable=False)
    account_name = Column(String(255), nullable=False)
    account_number = Column(String(100))
    financial_institution = Column(String(255))
    
    # Tax treatment
    tax_treatment = Column(String(50), nullable=False)
    
    # Account status
    is_active = Column(Boolean, default=True, nullable=False)
    date_opened = Column(DateTime(timezone=True))
    date_closed = Column(DateTime(timezone=True))
    
    # Current balance
    current_balance = Column(NUMERIC(15, 2), default=0, nullable=False)
    vested_balance = Column(NUMERIC(15, 2), default=0)
    
    # Employer information (for workplace plans)
    employer_name = Column(String(255))
    employer_ein = Column(String(20))  # Employer Identification Number
    plan_administrator = Column(String(255))
    
    # Investment options
    available_investments = Column(JSONB)
    current_allocation = Column(JSONB)
    
    # Beneficiary information
    primary_beneficiaries = Column(JSONB)
    contingent_beneficiaries = Column(JSONB)
    
    # Loan information (for 401k)
    loan_balance = Column(NUMERIC(15, 2), default=0)
    loan_details = Column(JSONB)
    
    # Required distributions
    rmd_age = Column(Integer, default=73)  # Required Minimum Distribution age
    first_rmd_year = Column(Integer)
    
    # Metadata
    notes = Column(Text)
    external_account_id = Column(String(255))  # For integration with external systems
    
    # Relationships
    user = relationship("User")
    plan = relationship("Plan")
    contributions = relationship("RetirementContribution", back_populates="account")
    distributions = relationship("RetirementDistribution", back_populates="account")
    
    __table_args__ = (
        Index('idx_retirement_account_user', 'user_id'),
        Index('idx_retirement_account_type', 'account_type'),
        Index('idx_retirement_account_active', 'is_active'),
    )
    
    @hybrid_property
    def account_age_years(self):
        """Calculate account age in years"""
        if not self.date_opened:
            return 0
        return (datetime.now(timezone.utc) - self.date_opened).days / 365.25
    
    def __repr__(self):
        return f"<RetirementAccount(id={self.id}, type={self.account_type}, name={self.account_name})>"


class EmployerPlan(Base, AuditMixin):
    """Employer-sponsored retirement plan details"""
    __tablename__ = "employer_plans"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(UUID(as_uuid=True), ForeignKey("retirement_accounts.id"), nullable=False)
    
    # Plan details
    plan_name = Column(String(255), nullable=False)
    plan_type = Column(String(50), nullable=False)  # 401k, 403b, 457, etc.
    plan_document_date = Column(DateTime(timezone=True))
    
    # Employer matching
    has_employer_match = Column(Boolean, default=False)
    match_formula = Column(String(500))  # "100% of first 3%, 50% of next 2%"
    match_percentage = Column(NUMERIC(5, 4))  # Maximum match as percentage of salary
    match_dollar_limit = Column(NUMERIC(12, 2))
    vesting_schedule = Column(JSONB)  # Vesting percentages by years of service
    
    # Contribution settings
    allows_roth_contributions = Column(Boolean, default=False)
    allows_after_tax_contributions = Column(Boolean, default=False)
    allows_in_service_withdrawals = Column(Boolean, default=False)
    allows_loans = Column(Boolean, default=False)
    
    # Loan provisions
    max_loan_percentage = Column(NUMERIC(5, 4), default=0.5)  # 50% of vested balance
    max_loan_amount = Column(NUMERIC(12, 2), default=50000)
    loan_interest_rate = Column(NUMERIC(5, 4))
    
    # Auto-enrollment features
    auto_enrollment_enabled = Column(Boolean, default=False)
    auto_enrollment_percentage = Column(NUMERIC(5, 4))
    auto_escalation_enabled = Column(Boolean, default=False)
    auto_escalation_rate = Column(NUMERIC(5, 4))
    
    # Safe harbor provisions
    is_safe_harbor_plan = Column(Boolean, default=False)
    safe_harbor_type = Column(String(50))  # basic_match, non_elective, qaca
    
    # Relationships
    account = relationship("RetirementAccount")
    
    __table_args__ = (
        Index('idx_employer_plan_account', 'account_id'),
    )


class RetirementContribution(Base, AuditMixin):
    """Track all retirement account contributions"""
    __tablename__ = "retirement_contributions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(UUID(as_uuid=True), ForeignKey("retirement_accounts.id"), nullable=False)
    
    # Contribution details
    contribution_date = Column(DateTime(timezone=True), nullable=False)
    contribution_type = Column(String(50), nullable=False)
    amount = Column(NUMERIC(12, 2), nullable=False)
    
    # Tax year attribution
    tax_year = Column(Integer, nullable=False)
    
    # Source information
    payroll_period_start = Column(DateTime(timezone=True))
    payroll_period_end = Column(DateTime(timezone=True))
    compensation_amount = Column(NUMERIC(12, 2))  # Compensation for the period
    
    # Employer match details
    match_amount = Column(NUMERIC(12, 2), default=0)
    match_vesting_percentage = Column(NUMERIC(5, 4), default=1.0)
    
    # Tax implications
    tax_deductible = Column(Boolean, default=False)
    tax_year_limit_used = Column(NUMERIC(12, 2))
    catch_up_contribution = Column(NUMERIC(12, 2), default=0)
    
    # Metadata
    external_transaction_id = Column(String(255))
    notes = Column(Text)
    
    # Relationships
    account = relationship("RetirementAccount", back_populates="contributions")
    
    __table_args__ = (
        Index('idx_contribution_account_date', 'account_id', 'contribution_date'),
        Index('idx_contribution_tax_year', 'tax_year'),
        Index('idx_contribution_type', 'contribution_type'),
    )


class RetirementDistribution(Base, AuditMixin):
    """Track retirement account distributions and withdrawals"""
    __tablename__ = "retirement_distributions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(UUID(as_uuid=True), ForeignKey("retirement_accounts.id"), nullable=False)
    
    # Distribution details
    distribution_date = Column(DateTime(timezone=True), nullable=False)
    gross_amount = Column(NUMERIC(12, 2), nullable=False)
    net_amount = Column(NUMERIC(12, 2), nullable=False)
    
    # Distribution type
    distribution_type = Column(String(50), nullable=False)  # rmd, withdrawal, loan, hardship, etc.
    distribution_reason = Column(String(100))
    
    # Tax implications
    taxable_amount = Column(NUMERIC(12, 2), nullable=False)
    tax_year = Column(Integer, nullable=False)
    
    # Withholding
    federal_withholding = Column(NUMERIC(12, 2), default=0)
    state_withholding = Column(NUMERIC(12, 2), default=0)
    withholding_rate = Column(NUMERIC(5, 4))
    
    # Penalties
    early_withdrawal_penalty = Column(NUMERIC(12, 2), default=0)
    excess_contribution_penalty = Column(NUMERIC(12, 2), default=0)
    
    # RMD tracking
    is_rmd = Column(Boolean, default=False)
    rmd_year = Column(Integer)
    rmd_required_amount = Column(NUMERIC(12, 2))
    
    # Rollover information
    is_rollover = Column(Boolean, default=False)
    rollover_destination = Column(String(255))
    rollover_completion_date = Column(DateTime(timezone=True))
    
    # Metadata
    form_1099r_issued = Column(Boolean, default=False)
    external_transaction_id = Column(String(255))
    notes = Column(Text)
    
    # Relationships
    account = relationship("RetirementAccount", back_populates="distributions")
    
    __table_args__ = (
        Index('idx_distribution_account_date', 'account_id', 'distribution_date'),
        Index('idx_distribution_tax_year', 'tax_year'),
        Index('idx_distribution_type', 'distribution_type'),
        Index('idx_distribution_rmd', 'is_rmd', 'rmd_year'),
    )


class Education529Plan(Base, AuditMixin):
    """529 Education Savings Plan specific details"""
    __tablename__ = "education_529_plans"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(UUID(as_uuid=True), ForeignKey("retirement_accounts.id"), nullable=False)
    
    # Plan details
    plan_name = Column(String(255), nullable=False)
    state_plan = Column(String(50), nullable=False)  # State offering the plan
    
    # Beneficiary information
    beneficiary_name = Column(String(255), nullable=False)
    beneficiary_ssn_last4 = Column(String(4))
    beneficiary_relationship = Column(String(50))
    beneficiary_birth_date = Column(DateTime(timezone=True))
    
    # State tax benefits
    state_tax_deduction_limit = Column(NUMERIC(12, 2))
    resident_state = Column(String(50))  # Account owner's state
    qualifies_for_state_deduction = Column(Boolean, default=False)
    
    # Investment options
    age_based_portfolio = Column(Boolean, default=False)
    target_enrollment_year = Column(Integer)
    risk_tolerance = Column(String(20))  # conservative, moderate, aggressive
    
    # Usage tracking
    total_qualified_withdrawals = Column(NUMERIC(12, 2), default=0)
    total_non_qualified_withdrawals = Column(NUMERIC(12, 2), default=0)
    
    # Family limits (aggregate across family members)
    family_contribution_limit = Column(NUMERIC(12, 2))
    
    # Relationships
    account = relationship("RetirementAccount")
    qualified_expenses = relationship("QualifiedEducationExpense", back_populates="plan")
    
    __table_args__ = (
        Index('idx_529_account', 'account_id'),
        Index('idx_529_state', 'state_plan'),
        Index('idx_529_beneficiary', 'beneficiary_name'),
    )


class QualifiedEducationExpense(Base, AuditMixin):
    """Track qualified education expenses for 529 plans"""
    __tablename__ = "qualified_education_expenses"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plan_id = Column(UUID(as_uuid=True), ForeignKey("education_529_plans.id"), nullable=False)
    
    # Expense details
    expense_date = Column(DateTime(timezone=True), nullable=False)
    expense_category = Column(String(50), nullable=False)  # tuition, room_board, books, etc.
    amount = Column(NUMERIC(12, 2), nullable=False)
    description = Column(String(500))
    
    # Institution information
    educational_institution = Column(String(255))
    institution_ein = Column(String(20))
    academic_year = Column(String(10))  # "2024-2025"
    
    # Tax forms
    form_1098t_amount = Column(NUMERIC(12, 2))
    qualified_for_aoc = Column(Boolean, default=False)  # American Opportunity Credit
    
    # Relationships
    plan = relationship("Education529Plan", back_populates="qualified_expenses")
    
    __table_args__ = (
        Index('idx_qualified_expense_plan', 'plan_id'),
        Index('idx_qualified_expense_date', 'expense_date'),
    )


class HSAAccount(Base, AuditMixin):
    """Health Savings Account specific details"""
    __tablename__ = "hsa_accounts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(UUID(as_uuid=True), ForeignKey("retirement_accounts.id"), nullable=False)
    
    # HSA specific details
    high_deductible_health_plan = Column(String(255))  # HDHP name
    hdhp_deductible = Column(NUMERIC(12, 2), nullable=False)
    hdhp_out_of_pocket_max = Column(NUMERIC(12, 2), nullable=False)
    
    # Coverage type
    coverage_type = Column(String(20), nullable=False)  # self_only, family
    coverage_start_date = Column(DateTime(timezone=True))
    coverage_end_date = Column(DateTime(timezone=True))
    
    # HSA eligibility
    is_eligible = Column(Boolean, default=True)
    eligibility_months = Column(Integer, default=12)  # Months eligible in tax year
    
    # Medicare enrollment (affects HSA eligibility)
    medicare_enrolled = Column(Boolean, default=False)
    medicare_enrollment_date = Column(DateTime(timezone=True))
    
    # Employer contributions
    employer_contribution_ytd = Column(NUMERIC(12, 2), default=0)
    
    # Usage for retirement (age 65+)
    used_for_non_medical_after_65 = Column(NUMERIC(12, 2), default=0)
    
    # Relationships
    account = relationship("RetirementAccount")
    medical_expenses = relationship("HSAMedicalExpense", back_populates="hsa")
    
    __table_args__ = (
        Index('idx_hsa_account', 'account_id'),
        Index('idx_hsa_eligibility', 'is_eligible'),
    )


class HSAMedicalExpense(Base, AuditMixin):
    """Track qualified medical expenses for HSA"""
    __tablename__ = "hsa_medical_expenses"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    hsa_id = Column(UUID(as_uuid=True), ForeignKey("hsa_accounts.id"), nullable=False)
    
    # Expense details
    expense_date = Column(DateTime(timezone=True), nullable=False)
    amount = Column(NUMERIC(12, 2), nullable=False)
    description = Column(String(500), nullable=False)
    
    # Medical provider
    provider_name = Column(String(255))
    provider_tax_id = Column(String(20))
    
    # Qualified expense validation
    is_qualified = Column(Boolean, default=True)
    qualifying_reason = Column(String(100))
    
    # Reimbursement tracking
    reimbursed_amount = Column(NUMERIC(12, 2), default=0)
    reimbursement_date = Column(DateTime(timezone=True))
    
    # Documentation
    receipt_stored = Column(Boolean, default=False)
    receipt_location = Column(String(500))
    
    # Relationships
    hsa = relationship("HSAAccount", back_populates="medical_expenses")
    
    __table_args__ = (
        Index('idx_hsa_expense_hsa', 'hsa_id'),
        Index('idx_hsa_expense_date', 'expense_date'),
    )


class RetirementProjection(Base, AuditMixin):
    """Store retirement projections and scenarios"""
    __tablename__ = "retirement_projections"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    plan_id = Column(UUID(as_uuid=True), ForeignKey("plans.id"))
    
    # Projection metadata
    projection_name = Column(String(255), nullable=False)
    projection_type = Column(String(50), nullable=False)  # retirement_income, contribution_strategy, etc.
    calculation_date = Column(DateTime(timezone=True), nullable=False)
    
    # Assumptions
    current_age = Column(Integer, nullable=False)
    retirement_age = Column(Integer, nullable=False)
    life_expectancy = Column(Integer, default=95)
    
    # Financial assumptions
    current_income = Column(NUMERIC(12, 2), nullable=False)
    income_growth_rate = Column(NUMERIC(5, 4), default=0.03)
    inflation_rate = Column(NUMERIC(5, 4), default=0.025)
    
    # Investment assumptions
    pre_retirement_return = Column(NUMERIC(5, 4), default=0.07)
    post_retirement_return = Column(NUMERIC(5, 4), default=0.05)
    
    # Results
    projection_results = Column(JSONB, nullable=False)
    
    # Monte Carlo results
    success_probability = Column(NUMERIC(5, 4))
    monte_carlo_results = Column(JSONB)
    
    # Recommendations
    recommended_actions = Column(JSONB)
    
    # Relationships
    user = relationship("User")
    plan = relationship("Plan")
    
    __table_args__ = (
        Index('idx_projection_user', 'user_id'),
        Index('idx_projection_type', 'projection_type'),
        Index('idx_projection_date', 'calculation_date'),
    )


# Initialize 2025 IRS contribution limits
def initialize_2025_contribution_limits():
    """Initialize IRS contribution limits for 2025"""
    return [
        {
            'tax_year': 2025,
            'account_type': AccountType.TRADITIONAL_401K,
            'regular_limit': Decimal('23500'),
            'catch_up_limit': Decimal('7500'),
            'catch_up_age': 50,
            'employer_match_limit': Decimal('70000'),  # Total contributions
            'total_plan_limit': Decimal('70000'),
            'effective_date': datetime(2025, 1, 1),
        },
        {
            'tax_year': 2025,
            'account_type': AccountType.TRADITIONAL_IRA,
            'regular_limit': Decimal('7000'),
            'catch_up_limit': Decimal('1000'),
            'catch_up_age': 50,
            'income_phase_out_start_single': Decimal('73000'),
            'income_phase_out_end_single': Decimal('83000'),
            'income_phase_out_start_married': Decimal('116000'),
            'income_phase_out_end_married': Decimal('136000'),
            'effective_date': datetime(2025, 1, 1),
        },
        {
            'tax_year': 2025,
            'account_type': AccountType.ROTH_IRA,
            'regular_limit': Decimal('7000'),
            'catch_up_limit': Decimal('1000'),
            'catch_up_age': 50,
            'income_phase_out_start_single': Decimal('138000'),
            'income_phase_out_end_single': Decimal('153000'),
            'income_phase_out_start_married': Decimal('218000'),
            'income_phase_out_end_married': Decimal('228000'),
            'effective_date': datetime(2025, 1, 1),
        },
        {
            'tax_year': 2025,
            'account_type': AccountType.HSA,
            'regular_limit': Decimal('4300'),  # Self-only coverage
            'hsa_family_limit': Decimal('8550'),  # Family coverage
            'catch_up_limit': Decimal('1000'),
            'catch_up_age': 55,
            'effective_date': datetime(2025, 1, 1),
        }
    ]