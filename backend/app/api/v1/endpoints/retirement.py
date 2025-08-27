"""
Retirement account management API endpoints
Handles 401(k), IRA, Roth IRA, 529 Education Plans, and HSA operations
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from decimal import Decimal
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.api.deps import get_db, get_current_user
from app.models.retirement_accounts import (
    RetirementAccount, IRSContributionLimits, RetirementContribution,
    RetirementDistribution, EmployerPlan, Education529Plan, HSAAccount,
    RetirementProjection, AccountType, TaxTreatment, ContributionType
)
from app.services.retirement_planning import (
    RetirementPlanningService, PersonalInfo, AccountBalance, RetirementGoal,
    FilingStatus, WithdrawalStrategy
)
from app.database.models import User


router = APIRouter()


# Pydantic models for API requests/responses
class RetirementAccountCreate(BaseModel):
    account_type: AccountType
    account_name: str
    account_number: Optional[str] = None
    financial_institution: Optional[str] = None
    tax_treatment: TaxTreatment
    current_balance: Decimal = Field(..., ge=0)
    date_opened: Optional[datetime] = None
    employer_name: Optional[str] = None
    employer_ein: Optional[str] = None


class RetirementAccountUpdate(BaseModel):
    account_name: Optional[str] = None
    current_balance: Optional[Decimal] = Field(None, ge=0)
    financial_institution: Optional[str] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = None


class RetirementAccountResponse(BaseModel):
    id: str
    account_type: AccountType
    account_name: str
    account_number: Optional[str]
    financial_institution: Optional[str]
    tax_treatment: TaxTreatment
    current_balance: Decimal
    vested_balance: Optional[Decimal]
    is_active: bool
    date_opened: Optional[datetime]
    employer_name: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ContributionCreate(BaseModel):
    account_id: str
    contribution_type: ContributionType
    amount: Decimal = Field(..., gt=0)
    contribution_date: Optional[datetime] = None
    tax_year: Optional[int] = None
    payroll_period_start: Optional[datetime] = None
    payroll_period_end: Optional[datetime] = None
    compensation_amount: Optional[Decimal] = None


class ContributionResponse(BaseModel):
    id: str
    account_id: str
    contribution_type: ContributionType
    amount: Decimal
    contribution_date: datetime
    tax_year: int
    match_amount: Decimal
    tax_deductible: bool
    catch_up_contribution: Decimal
    created_at: datetime

    class Config:
        from_attributes = True


class EmployerPlanCreate(BaseModel):
    account_id: str
    plan_name: str
    plan_type: str
    has_employer_match: bool = False
    match_formula: Optional[str] = None
    match_percentage: Optional[Decimal] = None
    allows_roth_contributions: bool = False
    allows_loans: bool = False
    auto_enrollment_enabled: bool = False


class EmployerPlanResponse(BaseModel):
    id: str
    account_id: str
    plan_name: str
    plan_type: str
    has_employer_match: bool
    match_formula: Optional[str]
    match_percentage: Optional[Decimal]
    allows_roth_contributions: bool
    allows_loans: bool
    auto_enrollment_enabled: bool

    class Config:
        from_attributes = True


class Education529Create(BaseModel):
    account_id: str
    plan_name: str
    state_plan: str
    beneficiary_name: str
    beneficiary_relationship: str
    beneficiary_birth_date: Optional[datetime] = None
    target_enrollment_year: Optional[int] = None
    age_based_portfolio: bool = False


class HSAAccountCreate(BaseModel):
    account_id: str
    high_deductible_health_plan: str
    hdhp_deductible: Decimal
    hdhp_out_of_pocket_max: Decimal
    coverage_type: str = Field(..., regex="^(self_only|family)$")
    coverage_start_date: Optional[datetime] = None
    is_eligible: bool = True


class PersonalInfoRequest(BaseModel):
    current_age: int = Field(..., ge=18, le=100)
    retirement_age: int = Field(..., ge=50, le=75)
    life_expectancy: int = Field(default=95, ge=70, le=120)
    filing_status: FilingStatus
    state_of_residence: str = Field(default="CA", max_length=2)
    current_income: Decimal = Field(..., ge=0)
    spouse_age: Optional[int] = Field(None, ge=18, le=100)
    spouse_income: Optional[Decimal] = Field(None, ge=0)


class RetirementGoalRequest(BaseModel):
    target_retirement_income: Optional[Decimal] = None
    income_replacement_ratio: Decimal = Field(default=Decimal('0.80'), ge=0.3, le=1.5)
    inflation_rate: Decimal = Field(default=Decimal('0.025'), ge=0, le=0.1)
    years_in_retirement: int = Field(default=25, ge=10, le=50)


class ContributionLimitsResponse(BaseModel):
    tax_year: int
    account_type: AccountType
    regular_limit: Decimal
    catch_up_limit: Decimal
    catch_up_age: int
    income_phase_out_start_single: Optional[Decimal]
    income_phase_out_end_single: Optional[Decimal]
    income_phase_out_start_married: Optional[Decimal]
    income_phase_out_end_married: Optional[Decimal]


class ContributionRoomResponse(BaseModel):
    base_limit: Decimal
    catch_up_limit: Decimal
    total_limit: Decimal
    contributed_to_date: Decimal
    available_room: Decimal
    phase_out_applied: bool


class OptimizationRequest(BaseModel):
    personal_info: PersonalInfoRequest
    available_cash: Decimal = Field(..., ge=0)
    tax_year: int = Field(default=2025)


# API Endpoints
@router.get("/accounts", response_model=List[RetirementAccountResponse])
async def get_retirement_accounts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    account_type: Optional[AccountType] = None,
    is_active: bool = True
):
    """Get all retirement accounts for the current user"""
    
    query = db.query(RetirementAccount).filter(
        RetirementAccount.user_id == current_user.id,
        RetirementAccount.is_active == is_active
    )
    
    if account_type:
        query = query.filter(RetirementAccount.account_type == account_type)
    
    accounts = query.all()
    return accounts


@router.post("/accounts", response_model=RetirementAccountResponse)
async def create_retirement_account(
    account_data: RetirementAccountCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new retirement account"""
    
    account = RetirementAccount(
        id=uuid.uuid4(),
        user_id=current_user.id,
        **account_data.dict(),
        created_by=current_user.id
    )
    
    db.add(account)
    db.commit()
    db.refresh(account)
    
    return account


@router.get("/accounts/{account_id}", response_model=RetirementAccountResponse)
async def get_retirement_account(
    account_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific retirement account"""
    
    account = db.query(RetirementAccount).filter(
        RetirementAccount.id == account_id,
        RetirementAccount.user_id == current_user.id
    ).first()
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Retirement account not found"
        )
    
    return account


@router.put("/accounts/{account_id}", response_model=RetirementAccountResponse)
async def update_retirement_account(
    account_id: str,
    account_data: RetirementAccountUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a retirement account"""
    
    account = db.query(RetirementAccount).filter(
        RetirementAccount.id == account_id,
        RetirementAccount.user_id == current_user.id
    ).first()
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Retirement account not found"
        )
    
    update_data = account_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(account, field, value)
    
    account.updated_by = current_user.id
    db.commit()
    db.refresh(account)
    
    return account


@router.delete("/accounts/{account_id}")
async def delete_retirement_account(
    account_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete (deactivate) a retirement account"""
    
    account = db.query(RetirementAccount).filter(
        RetirementAccount.id == account_id,
        RetirementAccount.user_id == current_user.id
    ).first()
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Retirement account not found"
        )
    
    account.is_active = False
    account.updated_by = current_user.id
    db.commit()
    
    return {"message": "Retirement account deactivated"}


@router.post("/accounts/{account_id}/contributions", response_model=ContributionResponse)
async def add_contribution(
    account_id: str,
    contribution_data: ContributionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add a contribution to a retirement account"""
    
    # Verify account ownership
    account = db.query(RetirementAccount).filter(
        RetirementAccount.id == account_id,
        RetirementAccount.user_id == current_user.id
    ).first()
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Retirement account not found"
        )
    
    # Set defaults
    contribution_date = contribution_data.contribution_date or datetime.now()
    tax_year = contribution_data.tax_year or contribution_date.year
    
    contribution = RetirementContribution(
        id=uuid.uuid4(),
        account_id=account_id,
        contribution_type=contribution_data.contribution_type,
        amount=contribution_data.amount,
        contribution_date=contribution_date,
        tax_year=tax_year,
        payroll_period_start=contribution_data.payroll_period_start,
        payroll_period_end=contribution_data.payroll_period_end,
        compensation_amount=contribution_data.compensation_amount,
        created_by=current_user.id
    )
    
    # Set tax deductibility based on account type
    if account.account_type in [AccountType.TRADITIONAL_401K, AccountType.TRADITIONAL_IRA]:
        contribution.tax_deductible = True
    
    db.add(contribution)
    
    # Update account balance
    account.current_balance += contribution_data.amount
    account.updated_by = current_user.id
    
    db.commit()
    db.refresh(contribution)
    
    return contribution


@router.get("/accounts/{account_id}/contributions", response_model=List[ContributionResponse])
async def get_contributions(
    account_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    tax_year: Optional[int] = None,
    contribution_type: Optional[ContributionType] = None
):
    """Get contributions for a retirement account"""
    
    # Verify account ownership
    account = db.query(RetirementAccount).filter(
        RetirementAccount.id == account_id,
        RetirementAccount.user_id == current_user.id
    ).first()
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Retirement account not found"
        )
    
    query = db.query(RetirementContribution).filter(
        RetirementContribution.account_id == account_id
    )
    
    if tax_year:
        query = query.filter(RetirementContribution.tax_year == tax_year)
    
    if contribution_type:
        query = query.filter(RetirementContribution.contribution_type == contribution_type)
    
    contributions = query.order_by(RetirementContribution.contribution_date.desc()).all()
    return contributions


@router.post("/employer-plans", response_model=EmployerPlanResponse)
async def create_employer_plan(
    plan_data: EmployerPlanCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create employer plan details"""
    
    # Verify account ownership
    account = db.query(RetirementAccount).filter(
        RetirementAccount.id == plan_data.account_id,
        RetirementAccount.user_id == current_user.id
    ).first()
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Retirement account not found"
        )
    
    employer_plan = EmployerPlan(
        id=uuid.uuid4(),
        **plan_data.dict(),
        created_by=current_user.id
    )
    
    db.add(employer_plan)
    db.commit()
    db.refresh(employer_plan)
    
    return employer_plan


@router.post("/529-plans", response_model=Dict[str, Any])
async def create_529_plan(
    plan_data: Education529Create,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create 529 education savings plan details"""
    
    # Verify account ownership
    account = db.query(RetirementAccount).filter(
        RetirementAccount.id == plan_data.account_id,
        RetirementAccount.user_id == current_user.id
    ).first()
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Retirement account not found"
        )
    
    plan_529 = Education529Plan(
        id=uuid.uuid4(),
        **plan_data.dict(),
        created_by=current_user.id
    )
    
    db.add(plan_529)
    db.commit()
    db.refresh(plan_529)
    
    return {"message": "529 plan created successfully", "plan_id": str(plan_529.id)}


@router.post("/hsa-accounts", response_model=Dict[str, Any])
async def create_hsa_account(
    hsa_data: HSAAccountCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create HSA account details"""
    
    # Verify account ownership
    account = db.query(RetirementAccount).filter(
        RetirementAccount.id == hsa_data.account_id,
        RetirementAccount.user_id == current_user.id
    ).first()
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Retirement account not found"
        )
    
    hsa_account = HSAAccount(
        id=uuid.uuid4(),
        **hsa_data.dict(),
        created_by=current_user.id
    )
    
    db.add(hsa_account)
    db.commit()
    db.refresh(hsa_account)
    
    return {"message": "HSA account created successfully", "hsa_id": str(hsa_account.id)}


@router.get("/contribution-limits/{tax_year}/{account_type}", response_model=ContributionLimitsResponse)
async def get_contribution_limits(
    tax_year: int,
    account_type: AccountType,
    db: Session = Depends(get_db)
):
    """Get IRS contribution limits for specific year and account type"""
    
    limits = db.query(IRSContributionLimits).filter(
        IRSContributionLimits.tax_year == tax_year,
        IRSContributionLimits.account_type == account_type
    ).first()
    
    if not limits:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Contribution limits not found for {tax_year} {account_type}"
        )
    
    return ContributionLimitsResponse(
        tax_year=limits.tax_year,
        account_type=limits.account_type,
        regular_limit=limits.regular_limit,
        catch_up_limit=limits.catch_up_limit,
        catch_up_age=limits.catch_up_age,
        income_phase_out_start_single=limits.income_phase_out_start_single,
        income_phase_out_end_single=limits.income_phase_out_end_single,
        income_phase_out_start_married=limits.income_phase_out_start_married,
        income_phase_out_end_married=limits.income_phase_out_end_married
    )


@router.get("/contribution-room/{account_type}", response_model=ContributionRoomResponse)
async def get_contribution_room(
    account_type: AccountType,
    age: int = Query(..., ge=18, le=100),
    income: Decimal = Query(..., ge=0),
    filing_status: FilingStatus = Query(...),
    tax_year: int = Query(default=2025),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Calculate available contribution room for account type"""
    
    service = RetirementPlanningService(db)
    contribution_room = service.calculate_available_contribution_room(
        str(current_user.id), account_type, tax_year, age, income, filing_status
    )
    
    if 'error' in contribution_room:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=contribution_room['error']
        )
    
    return ContributionRoomResponse(**contribution_room)


@router.post("/optimize-contributions")
async def optimize_contributions(
    request: OptimizationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get optimal contribution strategy across all account types"""
    
    service = RetirementPlanningService(db)
    
    # Get user's retirement accounts
    accounts = db.query(RetirementAccount).filter(
        RetirementAccount.user_id == current_user.id,
        RetirementAccount.is_active == True
    ).all()
    
    # Convert to service format
    account_balances = []
    for account in accounts:
        account_balances.append(AccountBalance(
            account_id=str(account.id),
            account_type=account.account_type,
            current_balance=account.current_balance,
            tax_treatment=account.tax_treatment
        ))
    
    # Convert request to service format
    personal_info = PersonalInfo(
        current_age=request.personal_info.current_age,
        retirement_age=request.personal_info.retirement_age,
        life_expectancy=request.personal_info.life_expectancy,
        filing_status=request.personal_info.filing_status,
        state_of_residence=request.personal_info.state_of_residence,
        current_income=request.personal_info.current_income,
        spouse_age=request.personal_info.spouse_age,
        spouse_income=request.personal_info.spouse_income
    )
    
    strategy = service.optimize_contribution_strategy(
        personal_info, account_balances, request.available_cash, request.tax_year
    )
    
    return {
        "account_allocations": {k: float(v) for k, v in strategy.account_allocations.items()},
        "total_annual_contribution": float(strategy.total_annual_contribution),
        "tax_savings": float(strategy.tax_savings),
        "employer_match_captured": float(strategy.employer_match_captured),
        "strategy_explanation": strategy.strategy_explanation
    }


@router.post("/retirement-projection")
async def calculate_retirement_projection(
    personal_info: PersonalInfoRequest,
    retirement_goal: RetirementGoalRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Calculate retirement income needs and projections"""
    
    service = RetirementPlanningService(db)
    
    # Convert to service formats
    personal_info_obj = PersonalInfo(
        current_age=personal_info.current_age,
        retirement_age=personal_info.retirement_age,
        life_expectancy=personal_info.life_expectancy,
        filing_status=personal_info.filing_status,
        current_income=personal_info.current_income
    )
    
    retirement_goal_obj = RetirementGoal(
        target_retirement_income=retirement_goal.target_retirement_income or (
            personal_info.current_income * retirement_goal.income_replacement_ratio
        ),
        income_replacement_ratio=retirement_goal.income_replacement_ratio,
        inflation_rate=retirement_goal.inflation_rate,
        years_in_retirement=retirement_goal.years_in_retirement
    )
    
    projection = service.calculate_retirement_income_need(personal_info_obj, retirement_goal_obj)
    
    # Convert Decimal to float for JSON serialization
    return {k: float(v) if isinstance(v, Decimal) else v for k, v in projection.items()}


@router.post("/roth-conversion-analysis")
async def analyze_roth_conversion(
    traditional_balance: Decimal = Query(..., ge=0),
    current_age: int = Query(..., ge=18, le=75),
    current_tax_rate: Decimal = Query(..., ge=0, le=0.5),
    expected_retirement_tax_rate: Decimal = Query(..., ge=0, le=0.5),
    years_to_retirement: int = Query(..., ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Analyze Roth conversion opportunities"""
    
    service = RetirementPlanningService(db)
    analysis = service.analyze_roth_conversion(
        traditional_balance, current_age, current_tax_rate,
        expected_retirement_tax_rate, years_to_retirement
    )
    
    return {
        "optimal_conversion_amount": float(analysis.optimal_conversion_amount),
        "years_to_convert": analysis.years_to_convert,
        "tax_cost_of_conversion": float(analysis.tax_cost_of_conversion),
        "lifetime_tax_savings": float(analysis.lifetime_tax_savings),
        "breakeven_age": analysis.breakeven_age,
        "conversion_timeline": [
            {k: float(v) if isinstance(v, Decimal) else v for k, v in item.items()}
            for item in analysis.conversion_timeline
        ]
    }


@router.get("/backdoor-roth-strategy")
async def get_backdoor_roth_strategy(
    income: Decimal = Query(..., ge=0),
    filing_status: FilingStatus = Query(...),
    tax_year: int = Query(default=2025),
    db: Session = Depends(get_db)
):
    """Get backdoor Roth IRA strategy for high earners"""
    
    service = RetirementPlanningService(db)
    strategy = service.calculate_backdoor_roth_strategy(income, filing_status, tax_year)
    
    # Convert Decimal values to float
    if 'max_contribution' in strategy:
        strategy['max_contribution'] = float(strategy['max_contribution'])
    if 'max_backdoor_contribution' in strategy:
        strategy['max_backdoor_contribution'] = float(strategy['max_backdoor_contribution'])
    
    return strategy


@router.post("/account-projections/{account_id}")
async def project_account_growth(
    account_id: str,
    years: int = Query(..., ge=1, le=50),
    annual_contribution: Optional[Decimal] = Query(None, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Project account growth over time"""
    
    # Verify account ownership
    account = db.query(RetirementAccount).filter(
        RetirementAccount.id == account_id,
        RetirementAccount.user_id == current_user.id
    ).first()
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Retirement account not found"
        )
    
    service = RetirementPlanningService(db)
    
    account_balance = AccountBalance(
        account_id=str(account.id),
        account_type=account.account_type,
        current_balance=account.current_balance,
        tax_treatment=account.tax_treatment
    )
    
    projections = service.project_account_growth(account_balance, years, annual_contribution)
    
    # Convert Decimal values to float
    for projection in projections:
        for key, value in projection.items():
            if isinstance(value, Decimal):
                projection[key] = float(value)
    
    return {"projections": projections}


@router.get("/required-minimum-distribution")
async def calculate_rmd(
    account_balance: Decimal = Query(..., ge=0),
    age: int = Query(..., ge=70, le=120),
    db: Session = Depends(get_db)
):
    """Calculate Required Minimum Distribution"""
    
    service = RetirementPlanningService(db)
    rmd = service.calculate_rmd(account_balance, age)
    
    return {
        "account_balance": float(rmd.account_balance),
        "age": rmd.age,
        "life_expectancy_factor": float(rmd.life_expectancy_factor),
        "rmd_amount": float(rmd.rmd_amount),
        "tax_owed": float(rmd.tax_owed)
    }