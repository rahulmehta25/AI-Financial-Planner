"""
IRS compliance and contribution limits management API endpoints
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.api.deps import get_db, get_current_user
from app.models.retirement_accounts import AccountType
from app.services.irs_compliance import IRSComplianceService
from app.database.models import User


router = APIRouter()


class ContributionLimitUpdate(BaseModel):
    regular_limit: Optional[float] = None
    catch_up_limit: Optional[float] = None
    catch_up_age: Optional[int] = None
    income_phase_out_start_single: Optional[float] = None
    income_phase_out_end_single: Optional[float] = None
    income_phase_out_start_married: Optional[float] = None
    income_phase_out_end_married: Optional[float] = None
    employer_match_limit: Optional[float] = None
    total_plan_limit: Optional[float] = None
    hsa_family_limit: Optional[float] = None


class ContributionValidationRequest(BaseModel):
    account_type: AccountType
    contribution_amount: float
    user_age: int
    annual_income: float
    filing_status: str = "single"
    tax_year: int = 2025


@router.post("/initialize-contribution-limits")
async def initialize_contribution_limits(
    tax_year: int = Query(2025, description="Tax year to initialize limits for"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Initialize IRS contribution limits for a specific tax year"""
    
    # Only allow superusers to initialize limits
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can initialize contribution limits"
        )
    
    service = IRSComplianceService(db)
    result = service.initialize_contribution_limits(tax_year)
    
    return result


@router.get("/contribution-limits/{tax_year}")
async def get_contribution_limits(
    tax_year: int,
    account_type: Optional[AccountType] = None,
    db: Session = Depends(get_db)
):
    """Get IRS contribution limits for a specific tax year"""
    
    service = IRSComplianceService(db)
    limits = service.get_contribution_limits(tax_year, account_type)
    
    if not limits:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No contribution limits found for {tax_year}" + 
                   (f" and account type {account_type}" if account_type else "")
        )
    
    return {
        'tax_year': tax_year,
        'account_type': account_type,
        'limits': limits
    }


@router.put("/contribution-limits/{tax_year}/{account_type}")
async def update_contribution_limits(
    tax_year: int,
    account_type: AccountType,
    updates: ContributionLimitUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update contribution limits for a specific tax year and account type"""
    
    # Only allow superusers to update limits
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can update contribution limits"
        )
    
    service = IRSComplianceService(db)
    result = service.update_contribution_limits(
        tax_year, 
        account_type, 
        updates.dict(exclude_unset=True)
    )
    
    if not result.get('success'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get('error', 'Failed to update contribution limits')
        )
    
    return result


@router.get("/cola-adjustments")
async def calculate_cola_adjustments(
    base_year: int = Query(..., description="Base year for COLA calculation"),
    target_year: int = Query(..., description="Target year for adjusted limits"),
    inflation_rate: float = Query(0.025, description="Annual inflation rate"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Calculate Cost of Living Adjustments (COLA) for contribution limits"""
    
    # Only allow superusers to calculate COLA adjustments
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can calculate COLA adjustments"
        )
    
    service = IRSComplianceService(db)
    result = service.calculate_cola_adjustments(base_year, target_year, inflation_rate)
    
    if 'error' in result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result['error']
        )
    
    return result


@router.post("/validate-contribution")
async def validate_contribution(
    validation_request: ContributionValidationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Validate if a contribution complies with IRS limits and rules"""
    
    from decimal import Decimal
    
    service = IRSComplianceService(db)
    result = service.validate_contribution_compliance(
        user_id=str(current_user.id),
        account_type=validation_request.account_type,
        contribution_amount=Decimal(str(validation_request.contribution_amount)),
        tax_year=validation_request.tax_year,
        user_age=validation_request.user_age,
        income=Decimal(str(validation_request.annual_income)),
        filing_status=validation_request.filing_status
    )
    
    return result


@router.get("/compliance-report/{tax_year}")
async def get_compliance_report(
    tax_year: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate a comprehensive compliance report for user's retirement contributions"""
    
    service = IRSComplianceService(db)
    report = service.generate_compliance_report(str(current_user.id), tax_year)
    
    return report


@router.get("/account-type-limits")
async def get_all_account_type_limits(
    tax_year: int = Query(2025, description="Tax year for limits"),
    db: Session = Depends(get_db)
):
    """Get contribution limits for all account types for a given tax year"""
    
    service = IRSComplianceService(db)
    limits = service.get_contribution_limits(tax_year)
    
    if not limits:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No contribution limits found for {tax_year}"
        )
    
    # Group by account type for easier consumption
    grouped_limits = {}
    for limit in limits:
        account_type = limit['account_type']
        grouped_limits[account_type] = limit
    
    return {
        'tax_year': tax_year,
        'limits_by_account_type': grouped_limits,
        'total_account_types': len(grouped_limits)
    }


@router.get("/contribution-room-summary")
async def get_contribution_room_summary(
    tax_year: int = Query(2025, description="Tax year for calculation"),
    user_age: int = Query(..., description="User's current age"),
    annual_income: float = Query(..., description="User's annual income"),
    filing_status: str = Query("single", description="Tax filing status"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a summary of contribution room across all account types"""
    
    from decimal import Decimal
    from app.models.retirement_accounts import RetirementAccount, RetirementContribution
    from sqlalchemy import and_
    
    service = IRSComplianceService(db)
    
    # Get all contribution limits for the tax year
    all_limits = service.get_contribution_limits(tax_year)
    
    # Get user's current year contributions
    contributions_query = db.query(RetirementContribution).join(
        RetirementAccount
    ).filter(
        and_(
            RetirementAccount.user_id == current_user.id,
            RetirementContribution.tax_year == tax_year
        )
    )
    
    current_contributions = contributions_query.all()
    
    # Aggregate contributions by account type
    contributions_by_type = {}
    for contribution in current_contributions:
        account = db.query(RetirementAccount).filter(
            RetirementAccount.id == contribution.account_id
        ).first()
        
        if account:
            account_type = account.account_type
            if account_type not in contributions_by_type:
                contributions_by_type[account_type] = Decimal('0')
            contributions_by_type[account_type] += contribution.amount
    
    # Calculate room for each account type
    contribution_room = []
    total_room_available = 0
    total_contributed = 0
    
    for limit_data in all_limits:
        account_type = limit_data['account_type']
        
        # Calculate applicable limit
        base_limit = Decimal(str(limit_data['regular_limit']))
        catch_up_limit = Decimal(str(limit_data['catch_up_limit'] or 0))
        catch_up_age = limit_data['catch_up_age']
        
        applicable_limit = base_limit
        if user_age >= catch_up_age and catch_up_limit > 0:
            applicable_limit += catch_up_limit
        
        # Apply income phase-outs for Roth IRA
        if account_type == 'roth_ira':
            phase_out_start = (Decimal(str(limit_data['income_phase_out_start_single'] or 0)) 
                             if filing_status == 'single' 
                             else Decimal(str(limit_data['income_phase_out_start_married'] or 0)))
            phase_out_end = (Decimal(str(limit_data['income_phase_out_end_single'] or 0))
                           if filing_status == 'single'
                           else Decimal(str(limit_data['income_phase_out_end_married'] or 0)))
            
            if phase_out_start and annual_income > float(phase_out_start):
                if annual_income > float(phase_out_end):
                    applicable_limit = Decimal('0')
                else:
                    reduction_factor = (Decimal(str(annual_income)) - phase_out_start) / (phase_out_end - phase_out_start)
                    applicable_limit = applicable_limit * (Decimal('1') - reduction_factor)
        
        # Calculate room
        contributed = contributions_by_type.get(account_type, Decimal('0'))
        room_available = max(Decimal('0'), applicable_limit - contributed)
        
        contribution_room.append({
            'account_type': account_type,
            'base_limit': float(base_limit),
            'catch_up_limit': float(catch_up_limit),
            'applicable_limit': float(applicable_limit),
            'contributed_ytd': float(contributed),
            'room_available': float(room_available),
            'utilization_percentage': float((contributed / applicable_limit * 100)) if applicable_limit > 0 else 0,
            'catch_up_eligible': user_age >= catch_up_age
        })
        
        total_room_available += float(room_available)
        total_contributed += float(contributed)
    
    return {
        'tax_year': tax_year,
        'user_age': user_age,
        'annual_income': annual_income,
        'filing_status': filing_status,
        'summary': {
            'total_contributed_ytd': total_contributed,
            'total_room_available': total_room_available,
            'number_of_account_types': len(contribution_room)
        },
        'contribution_room_by_type': contribution_room
    }