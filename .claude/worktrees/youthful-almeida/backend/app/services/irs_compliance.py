"""
IRS compliance and contribution limits management service
Handles contribution limits, automatic annual adjustments, and regulatory compliance
"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.retirement_accounts import (
    IRSContributionLimits, AccountType, initialize_2025_contribution_limits
)


class IRSComplianceService:
    """Service for managing IRS contribution limits and compliance"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def initialize_contribution_limits(self, tax_year: int = 2025) -> Dict[str, Any]:
        """Initialize IRS contribution limits for a given tax year"""
        
        # Check if limits already exist for this year
        existing_limits = self.db.query(IRSContributionLimits).filter(
            IRSContributionLimits.tax_year == tax_year
        ).first()
        
        if existing_limits:
            return {
                'message': f'Contribution limits for {tax_year} already exist',
                'limits_count': self.db.query(IRSContributionLimits).filter(
                    IRSContributionLimits.tax_year == tax_year
                ).count()
            }
        
        # Get the initialization data based on tax year
        if tax_year == 2025:
            limits_data = initialize_2025_contribution_limits()
        else:
            # For other years, we would need to add their specific limits
            # For now, we'll create a basic structure
            limits_data = self._generate_basic_limits(tax_year)
        
        # Create contribution limit records
        created_count = 0
        for limit_data in limits_data:
            limit_record = IRSContributionLimits(
                tax_year=limit_data['tax_year'],
                account_type=limit_data['account_type'],
                regular_limit=limit_data['regular_limit'],
                catch_up_limit=limit_data.get('catch_up_limit', Decimal('0')),
                catch_up_age=limit_data.get('catch_up_age', 50),
                income_phase_out_start_single=limit_data.get('income_phase_out_start_single'),
                income_phase_out_end_single=limit_data.get('income_phase_out_end_single'),
                income_phase_out_start_married=limit_data.get('income_phase_out_start_married'),
                income_phase_out_end_married=limit_data.get('income_phase_out_end_married'),
                employer_match_limit=limit_data.get('employer_match_limit'),
                total_plan_limit=limit_data.get('total_plan_limit'),
                hsa_family_limit=limit_data.get('hsa_family_limit'),
                effective_date=limit_data['effective_date'],
                irs_announcement_date=limit_data.get('irs_announcement_date')
            )
            
            self.db.add(limit_record)
            created_count += 1
        
        self.db.commit()
        
        return {
            'message': f'Successfully initialized {created_count} contribution limits for {tax_year}',
            'tax_year': tax_year,
            'limits_created': created_count
        }
    
    def get_contribution_limits(self, tax_year: int, account_type: Optional[AccountType] = None) -> List[Dict]:
        """Get contribution limits for a tax year, optionally filtered by account type"""
        
        query = self.db.query(IRSContributionLimits).filter(
            IRSContributionLimits.tax_year == tax_year
        )
        
        if account_type:
            query = query.filter(IRSContributionLimits.account_type == account_type)
        
        limits = query.all()
        
        return [
            {
                'tax_year': limit.tax_year,
                'account_type': limit.account_type,
                'regular_limit': float(limit.regular_limit),
                'catch_up_limit': float(limit.catch_up_limit),
                'catch_up_age': limit.catch_up_age,
                'income_phase_out_start_single': float(limit.income_phase_out_start_single) if limit.income_phase_out_start_single else None,
                'income_phase_out_end_single': float(limit.income_phase_out_end_single) if limit.income_phase_out_end_single else None,
                'income_phase_out_start_married': float(limit.income_phase_out_start_married) if limit.income_phase_out_start_married else None,
                'income_phase_out_end_married': float(limit.income_phase_out_end_married) if limit.income_phase_out_end_married else None,
                'employer_match_limit': float(limit.employer_match_limit) if limit.employer_match_limit else None,
                'total_plan_limit': float(limit.total_plan_limit) if limit.total_plan_limit else None,
                'hsa_family_limit': float(limit.hsa_family_limit) if limit.hsa_family_limit else None,
                'effective_date': limit.effective_date.isoformat() if limit.effective_date else None,
            }
            for limit in limits
        ]
    
    def update_contribution_limits(self, tax_year: int, account_type: AccountType, updates: Dict) -> Dict[str, Any]:
        """Update contribution limits for a specific tax year and account type"""
        
        limit_record = self.db.query(IRSContributionLimits).filter(
            and_(
                IRSContributionLimits.tax_year == tax_year,
                IRSContributionLimits.account_type == account_type
            )
        ).first()
        
        if not limit_record:
            return {
                'error': f'No contribution limits found for {tax_year} {account_type}',
                'success': False
            }
        
        # Update allowed fields
        updatable_fields = [
            'regular_limit', 'catch_up_limit', 'catch_up_age',
            'income_phase_out_start_single', 'income_phase_out_end_single',
            'income_phase_out_start_married', 'income_phase_out_end_married',
            'employer_match_limit', 'total_plan_limit', 'hsa_family_limit',
            'cola_adjustment', 'irs_announcement_date'
        ]
        
        updated_fields = []
        for field, value in updates.items():
            if field in updatable_fields and hasattr(limit_record, field):
                if value is not None:
                    if field in ['regular_limit', 'catch_up_limit', 'income_phase_out_start_single',
                                'income_phase_out_end_single', 'income_phase_out_start_married',
                                'income_phase_out_end_married', 'employer_match_limit',
                                'total_plan_limit', 'hsa_family_limit', 'cola_adjustment']:
                        setattr(limit_record, field, Decimal(str(value)))
                    else:
                        setattr(limit_record, field, value)
                    updated_fields.append(field)
        
        if updated_fields:
            self.db.commit()
            return {
                'message': f'Updated {len(updated_fields)} fields for {tax_year} {account_type}',
                'updated_fields': updated_fields,
                'success': True
            }
        else:
            return {
                'message': 'No valid fields to update',
                'success': False
            }
    
    def calculate_cola_adjustments(self, base_year: int, target_year: int, inflation_rate: float = 0.025) -> Dict[str, Any]:
        """Calculate Cost of Living Adjustments (COLA) for contribution limits"""
        
        if target_year <= base_year:
            return {'error': 'Target year must be after base year'}
        
        years_elapsed = target_year - base_year
        cola_factor = (1 + inflation_rate) ** years_elapsed
        
        # Get base year limits
        base_limits = self.db.query(IRSContributionLimits).filter(
            IRSContributionLimits.tax_year == base_year
        ).all()
        
        if not base_limits:
            return {'error': f'No contribution limits found for base year {base_year}'}
        
        # Calculate adjusted limits
        adjusted_limits = []
        for base_limit in base_limits:
            # IRS typically rounds to nearest $500 or $1000
            regular_limit = self._round_to_irs_standard(float(base_limit.regular_limit) * cola_factor)
            catch_up_limit = self._round_to_irs_standard(float(base_limit.catch_up_limit) * cola_factor) if base_limit.catch_up_limit else 0
            
            adjusted_data = {
                'account_type': base_limit.account_type,
                'base_regular_limit': float(base_limit.regular_limit),
                'adjusted_regular_limit': regular_limit,
                'base_catch_up_limit': float(base_limit.catch_up_limit) if base_limit.catch_up_limit else 0,
                'adjusted_catch_up_limit': catch_up_limit,
                'cola_factor': cola_factor,
                'inflation_rate': inflation_rate
            }
            
            # Adjust income phase-outs if they exist
            if base_limit.income_phase_out_start_single:
                adjusted_data['adjusted_phase_out_start_single'] = self._round_to_irs_standard(
                    float(base_limit.income_phase_out_start_single) * cola_factor
                )
            if base_limit.income_phase_out_end_single:
                adjusted_data['adjusted_phase_out_end_single'] = self._round_to_irs_standard(
                    float(base_limit.income_phase_out_end_single) * cola_factor
                )
            
            adjusted_limits.append(adjusted_data)
        
        return {
            'base_year': base_year,
            'target_year': target_year,
            'cola_factor': cola_factor,
            'inflation_rate': inflation_rate,
            'adjusted_limits': adjusted_limits
        }
    
    def validate_contribution_compliance(self, user_id: str, account_type: AccountType, 
                                      contribution_amount: Decimal, tax_year: int,
                                      user_age: int, income: Decimal, filing_status: str) -> Dict[str, Any]:
        """Validate if a contribution complies with IRS limits and rules"""
        
        # Get contribution limits for the account type
        limits = self.db.query(IRSContributionLimits).filter(
            and_(
                IRSContributionLimits.tax_year == tax_year,
                IRSContributionLimits.account_type == account_type
            )
        ).first()
        
        if not limits:
            return {
                'compliant': False,
                'error': f'No contribution limits found for {tax_year} {account_type}',
                'violations': ['Missing contribution limits data']
            }
        
        violations = []
        warnings = []
        
        # Calculate applicable limits
        base_limit = limits.regular_limit
        if user_age >= limits.catch_up_age and limits.catch_up_limit:
            total_limit = base_limit + limits.catch_up_limit
            catch_up_eligible = True
        else:
            total_limit = base_limit
            catch_up_eligible = False
        
        # Check basic contribution limit
        if contribution_amount > total_limit:
            violations.append(f'Contribution ${contribution_amount} exceeds limit ${total_limit}')
        
        # Check income phase-outs for Roth IRA
        if account_type == AccountType.ROTH_IRA:
            phase_out_start = (limits.income_phase_out_start_single if filing_status == 'single' 
                             else limits.income_phase_out_start_married)
            phase_out_end = (limits.income_phase_out_end_single if filing_status == 'single'
                           else limits.income_phase_out_end_married)
            
            if phase_out_start and income > phase_out_start:
                if income > phase_out_end:
                    violations.append(f'Income ${income} exceeds Roth IRA eligibility limit ${phase_out_end}')
                else:
                    # Calculate reduced limit
                    reduction_factor = (income - phase_out_start) / (phase_out_end - phase_out_start)
                    reduced_limit = total_limit * (1 - reduction_factor)
                    if contribution_amount > reduced_limit:
                        violations.append(f'Contribution ${contribution_amount} exceeds reduced limit ${reduced_limit:.2f} due to income phase-out')
                    else:
                        warnings.append(f'Contribution limit reduced to ${reduced_limit:.2f} due to income phase-out')
        
        # Additional validation for 401(k) plans
        if account_type in [AccountType.TRADITIONAL_401K, AccountType.ROTH_401K]:
            if limits.total_plan_limit and contribution_amount > limits.total_plan_limit:
                violations.append(f'Total plan contributions cannot exceed ${limits.total_plan_limit}')
        
        # HSA eligibility checks
        if account_type == AccountType.HSA:
            warnings.append('Ensure you have qualifying High Deductible Health Plan coverage')
            warnings.append('Cannot be enrolled in Medicare or covered by other health insurance')
        
        return {
            'compliant': len(violations) == 0,
            'contribution_amount': float(contribution_amount),
            'applicable_limit': float(total_limit),
            'base_limit': float(base_limit),
            'catch_up_limit': float(limits.catch_up_limit) if limits.catch_up_limit else 0,
            'catch_up_eligible': catch_up_eligible,
            'violations': violations,
            'warnings': warnings,
            'tax_year': tax_year,
            'account_type': account_type
        }
    
    def generate_compliance_report(self, user_id: str, tax_year: int) -> Dict[str, Any]:
        """Generate a comprehensive compliance report for a user's retirement contributions"""
        
        # This would analyze all of a user's contributions for the tax year
        # and provide a comprehensive compliance report
        
        from app.models.retirement_accounts import RetirementAccount, RetirementContribution
        
        # Get user's accounts
        accounts = self.db.query(RetirementAccount).filter(
            RetirementAccount.user_id == user_id,
            RetirementAccount.is_active == True
        ).all()
        
        # Get contributions for the tax year
        contributions = self.db.query(RetirementContribution).join(
            RetirementAccount
        ).filter(
            RetirementAccount.user_id == user_id,
            RetirementContribution.tax_year == tax_year
        ).all()
        
        # Aggregate contributions by account type
        contribution_summary = {}
        for contribution in contributions:
            account = next((a for a in accounts if a.id == contribution.account_id), None)
            if account:
                account_type = account.account_type
                if account_type not in contribution_summary:
                    contribution_summary[account_type] = {
                        'total_contributions': Decimal('0'),
                        'employee_contributions': Decimal('0'),
                        'employer_contributions': Decimal('0'),
                        'contribution_count': 0
                    }
                
                contribution_summary[account_type]['total_contributions'] += contribution.amount
                contribution_summary[account_type]['contribution_count'] += 1
                
                if contribution.contribution_type.value.startswith('employee'):
                    contribution_summary[account_type]['employee_contributions'] += contribution.amount
                elif contribution.contribution_type.value.startswith('employer'):
                    contribution_summary[account_type]['employer_contributions'] += contribution.amount
        
        # Check compliance for each account type
        compliance_results = []
        for account_type, summary in contribution_summary.items():
            # This is a simplified check - would need user age and income for full validation
            limits = self.db.query(IRSContributionLimits).filter(
                and_(
                    IRSContributionLimits.tax_year == tax_year,
                    IRSContributionLimits.account_type == account_type
                )
            ).first()
            
            if limits:
                compliance_results.append({
                    'account_type': account_type,
                    'contributed': float(summary['total_contributions']),
                    'limit': float(limits.regular_limit),
                    'compliance_status': 'Compliant' if summary['total_contributions'] <= limits.regular_limit else 'Exceeds Limit',
                    'remaining_capacity': float(max(Decimal('0'), limits.regular_limit - summary['total_contributions']))
                })
        
        return {
            'tax_year': tax_year,
            'user_id': user_id,
            'report_date': datetime.now(timezone.utc).isoformat(),
            'contribution_summary': {
                account_type: {
                    'total_contributions': float(summary['total_contributions']),
                    'employee_contributions': float(summary['employee_contributions']),
                    'employer_contributions': float(summary['employer_contributions']),
                    'contribution_count': summary['contribution_count']
                }
                for account_type, summary in contribution_summary.items()
            },
            'compliance_results': compliance_results,
            'overall_status': 'Compliant' if all(r['compliance_status'] == 'Compliant' for r in compliance_results) else 'Has Violations'
        }
    
    def _round_to_irs_standard(self, amount: float) -> int:
        """Round amounts to IRS standard increments (typically $500 or $1000)"""
        if amount < 5000:
            # Round to nearest $100
            return int(round(amount / 100) * 100)
        elif amount < 20000:
            # Round to nearest $500
            return int(round(amount / 500) * 500)
        else:
            # Round to nearest $1000
            return int(round(amount / 1000) * 1000)
    
    def _generate_basic_limits(self, tax_year: int) -> List[Dict]:
        """Generate basic contribution limits for years where we don't have specific data"""
        
        # This is a fallback method - in production, we'd want actual IRS data
        base_limits = [
            {
                'tax_year': tax_year,
                'account_type': AccountType.TRADITIONAL_401K,
                'regular_limit': Decimal('23000'),  # Estimated
                'catch_up_limit': Decimal('7500'),
                'catch_up_age': 50,
                'total_plan_limit': Decimal('69000'),
                'effective_date': datetime(tax_year, 1, 1),
            },
            {
                'tax_year': tax_year,
                'account_type': AccountType.TRADITIONAL_IRA,
                'regular_limit': Decimal('6500'),  # Estimated
                'catch_up_limit': Decimal('1000'),
                'catch_up_age': 50,
                'effective_date': datetime(tax_year, 1, 1),
            },
            {
                'tax_year': tax_year,
                'account_type': AccountType.ROTH_IRA,
                'regular_limit': Decimal('6500'),  # Estimated
                'catch_up_limit': Decimal('1000'),
                'catch_up_age': 50,
                'income_phase_out_start_single': Decimal('130000'),
                'income_phase_out_end_single': Decimal('145000'),
                'income_phase_out_start_married': Decimal('204000'),
                'income_phase_out_end_married': Decimal('214000'),
                'effective_date': datetime(tax_year, 1, 1),
            },
            {
                'tax_year': tax_year,
                'account_type': AccountType.HSA,
                'regular_limit': Decimal('4000'),  # Estimated self-only
                'hsa_family_limit': Decimal('8000'),
                'catch_up_limit': Decimal('1000'),
                'catch_up_age': 55,
                'effective_date': datetime(tax_year, 1, 1),
            }
        ]
        
        return base_limits