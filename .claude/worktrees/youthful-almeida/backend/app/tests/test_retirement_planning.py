"""
Comprehensive test suite for retirement planning calculations and IRS compliance
"""

import pytest
from decimal import Decimal
from datetime import datetime, timezone
from unittest.mock import Mock, patch

from app.services.retirement_planning import (
    RetirementPlanningService, PersonalInfo, AccountBalance, RetirementGoal,
    FilingStatus, WithdrawalStrategy, TaxTreatment, AccountType
)
from app.services.irs_compliance import IRSComplianceService
from app.models.retirement_accounts import (
    IRSContributionLimits, RetirementAccount, RetirementContribution,
    initialize_2025_contribution_limits
)


class TestRetirementPlanningService:
    """Test retirement planning service calculations"""
    
    @pytest.fixture
    def mock_db_session(self):
        """Mock database session"""
        return Mock()
    
    @pytest.fixture
    def retirement_service(self, mock_db_session):
        """Create retirement planning service instance"""
        return RetirementPlanningService(mock_db_session)
    
    @pytest.fixture
    def sample_personal_info(self):
        """Sample personal information"""
        return PersonalInfo(
            current_age=35,
            retirement_age=65,
            life_expectancy=90,
            filing_status=FilingStatus.SINGLE,
            current_income=Decimal('100000'),
            state_of_residence="CA"
        )
    
    @pytest.fixture
    def sample_account_balances(self):
        """Sample account balances"""
        return [
            AccountBalance(
                account_id="401k_account",
                account_type=AccountType.TRADITIONAL_401K,
                current_balance=Decimal('50000'),
                annual_contribution=Decimal('15000'),
                employer_match=Decimal('5000'),
                tax_treatment=TaxTreatment.TAX_DEFERRED
            ),
            AccountBalance(
                account_id="roth_ira_account",
                account_type=AccountType.ROTH_IRA,
                current_balance=Decimal('25000'),
                annual_contribution=Decimal('6000'),
                tax_treatment=TaxTreatment.TAX_FREE
            ),
            AccountBalance(
                account_id="hsa_account",
                account_type=AccountType.HSA,
                current_balance=Decimal('10000'),
                annual_contribution=Decimal('4300'),
                tax_treatment=TaxTreatment.TRIPLE_TAX_ADVANTAGE
            )
        ]
    
    def test_marginal_tax_rate_calculation(self, retirement_service, sample_personal_info):
        """Test marginal tax rate calculation for different income levels"""
        
        # Test different income brackets
        test_cases = [
            (Decimal('50000'), Decimal('0.12')),  # 12% bracket
            (Decimal('85000'), Decimal('0.22')),  # 22% bracket
            (Decimal('180000'), Decimal('0.24')), # 24% bracket
            (Decimal('400000'), Decimal('0.32'))  # 32% bracket
        ]
        
        for income, expected_rate in test_cases:
            sample_personal_info.current_income = income
            rate = retirement_service._get_marginal_tax_rate(sample_personal_info)
            assert abs(rate - expected_rate) < Decimal('0.01'), f"Income {income} should be in {expected_rate} bracket"
    
    def test_employer_match_calculation(self, retirement_service):
        """Test employer 401(k) match calculation"""
        
        salary = Decimal('100000')
        
        # Test standard match formula: "100% of first 3%, 50% of next 2%"
        test_cases = [
            (Decimal('0.02'), Decimal('2000')),    # 2% contribution -> 100% match
            (Decimal('0.03'), Decimal('3000')),    # 3% contribution -> 100% match
            (Decimal('0.04'), Decimal('3500')),    # 4% contribution -> 3% + 0.5%
            (Decimal('0.05'), Decimal('4000')),    # 5% contribution -> 3% + 1%
            (Decimal('0.06'), Decimal('4000')),    # 6% contribution -> capped at 4%
        ]
        
        match_formula = "100% of first 3%, 50% of next 2%"
        
        for contribution_rate, expected_match in test_cases:
            match = retirement_service.calculate_employer_match(
                salary, contribution_rate, match_formula
            )
            assert abs(match - expected_match) < Decimal('1'), \
                f"Contribution rate {contribution_rate} should generate {expected_match} match, got {match}"
    
    def test_contribution_optimization_priority(self, retirement_service, sample_personal_info, sample_account_balances):
        """Test that contribution optimization follows correct priority order"""
        
        available_cash = Decimal('25000')
        
        # Mock contribution limits
        with patch.object(retirement_service, 'get_contribution_limits') as mock_limits:
            mock_limits.return_value = {
                'regular_limit': Decimal('23500'),
                'catch_up_limit': Decimal('0'),
                'hsa_family_limit': Decimal('8550')
            }
            
            strategy = retirement_service.optimize_contribution_strategy(
                sample_personal_info, sample_account_balances, available_cash
            )
            
            # Should prioritize employer match, then HSA, then tax optimization
            assert strategy.employer_match_captured > 0, "Should capture employer match"
            assert 'hsa_account' in strategy.account_allocations, "Should contribute to HSA"
            assert strategy.total_annual_contribution <= available_cash, "Should not exceed available cash"
    
    def test_retirement_income_need_calculation(self, retirement_service, sample_personal_info):
        """Test retirement income need calculation with inflation"""
        
        goal = RetirementGoal(
            target_retirement_income=Decimal('80000'),
            income_replacement_ratio=Decimal('0.8'),
            inflation_rate=Decimal('0.025'),
            years_in_retirement=25
        )
        
        result = retirement_service.calculate_retirement_income_need(sample_personal_info, goal)
        
        assert result['current_income'] == sample_personal_info.current_income
        assert result['years_to_retirement'] == 30  # 65 - 35
        assert result['inflated_income_at_retirement'] > sample_personal_info.current_income
        assert result['total_retirement_need_pv'] > 0
    
    def test_account_growth_projection(self, retirement_service, sample_account_balances):
        """Test account balance projection over time"""
        
        account = sample_account_balances[0]  # 401k account
        years = 10
        
        projections = retirement_service.project_account_growth(account, years)
        
        assert len(projections) == years
        assert projections[0]['year'] == 1
        assert projections[-1]['year'] == years
        
        # Balance should grow over time
        for i in range(1, len(projections)):
            assert projections[i]['balance'] > projections[i-1]['balance']
    
    def test_rmd_calculation(self, retirement_service):
        """Test Required Minimum Distribution calculation"""
        
        test_cases = [
            (70, Decimal('100000')),   # Below RMD age
            (75, Decimal('500000')),   # Normal RMD
            (85, Decimal('200000')),   # Older age with smaller balance
        ]
        
        for age, balance in test_cases:
            rmd = retirement_service.calculate_rmd(balance, age)
            
            if age < 73:
                assert rmd.rmd_amount == Decimal('0'), "No RMD required before age 73"
            else:
                assert rmd.rmd_amount > Decimal('0'), "RMD should be required after age 73"
                assert rmd.life_expectancy_factor > Decimal('0'), "Life expectancy factor should be positive"
                assert rmd.rmd_amount == balance / rmd.life_expectancy_factor
    
    def test_roth_conversion_analysis(self, retirement_service):
        """Test Roth conversion analysis calculations"""
        
        analysis = retirement_service.analyze_roth_conversion(
            traditional_balance=Decimal('200000'),
            current_age=50,
            current_tax_rate=Decimal('0.22'),
            expected_retirement_tax_rate=Decimal('0.24'),
            years_to_retirement=15
        )
        
        assert analysis.optimal_conversion_amount > Decimal('0')
        assert analysis.tax_cost_of_conversion > Decimal('0')
        assert analysis.breakeven_age > 50
        assert len(analysis.conversion_timeline) > 0
        
        # Tax savings should be positive if retirement rate is higher
        assert analysis.lifetime_tax_savings >= Decimal('0')
    
    def test_backdoor_roth_strategy(self, retirement_service):
        """Test backdoor Roth IRA strategy calculation"""
        
        # Mock contribution limits
        with patch.object(retirement_service, 'get_contribution_limits') as mock_limits:
            mock_limits.return_value = {
                'regular_limit': Decimal('7000'),
                'income_phase_out_end_single': Decimal('153000'),
                'income_phase_out_end_married': Decimal('228000')
            }
            
            # High income - should recommend backdoor Roth
            high_income_result = retirement_service.calculate_backdoor_roth_strategy(
                income=Decimal('200000'),
                filing_status=FilingStatus.SINGLE
            )
            
            assert not high_income_result['eligible_for_direct_roth']
            assert high_income_result['backdoor_roth_needed']
            assert 'steps' in high_income_result
            
            # Low income - should allow direct Roth
            low_income_result = retirement_service.calculate_backdoor_roth_strategy(
                income=Decimal('80000'),
                filing_status=FilingStatus.SINGLE
            )
            
            assert low_income_result['eligible_for_direct_roth']
            assert not low_income_result['backdoor_roth_needed']
    
    def test_529_education_projection(self, retirement_service):
        """Test 529 education savings projection"""
        
        projection = retirement_service.calculate_529_education_projection(
            current_balance=Decimal('25000'),
            annual_contribution=Decimal('5000'),
            years_until_college=10,
            expected_return=Decimal('0.06'),
            education_inflation=Decimal('0.05')
        )
        
        assert projection['projected_529_balance'] > Decimal('25000')
        assert projection['estimated_total_college_cost'] > Decimal('0')
        assert projection['coverage_ratio'] >= Decimal('0')
        assert projection['years_until_college'] == 10


class TestIRSComplianceService:
    """Test IRS compliance and contribution limits"""
    
    @pytest.fixture
    def mock_db_session(self):
        """Mock database session"""
        mock_session = Mock()
        
        # Mock query results
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        mock_query.all.return_value = []
        
        return mock_session
    
    @pytest.fixture
    def compliance_service(self, mock_db_session):
        """Create IRS compliance service instance"""
        return IRSComplianceService(mock_db_session)
    
    def test_contribution_limits_initialization(self, compliance_service):
        """Test initialization of 2025 contribution limits"""
        
        limits_data = initialize_2025_contribution_limits()
        
        assert len(limits_data) >= 4  # Should have at least 401k, IRA, Roth IRA, HSA
        
        # Check 401k limits
        traditional_401k = next((l for l in limits_data if l['account_type'] == AccountType.TRADITIONAL_401K), None)
        assert traditional_401k is not None
        assert traditional_401k['regular_limit'] == Decimal('23500')
        assert traditional_401k['catch_up_limit'] == Decimal('7500')
        
        # Check IRA limits
        roth_ira = next((l for l in limits_data if l['account_type'] == AccountType.ROTH_IRA), None)
        assert roth_ira is not None
        assert roth_ira['regular_limit'] == Decimal('7000')
        assert roth_ira['income_phase_out_start_single'] == Decimal('138000')
        
        # Check HSA limits
        hsa = next((l for l in limits_data if l['account_type'] == AccountType.HSA), None)
        assert hsa is not None
        assert hsa['regular_limit'] == Decimal('4300')
        assert hsa['hsa_family_limit'] == Decimal('8550')
    
    def test_cola_adjustments_calculation(self, compliance_service):
        """Test COLA adjustments calculation"""
        
        # Mock existing limits for base year
        mock_limit = Mock()
        mock_limit.regular_limit = Decimal('23000')
        mock_limit.catch_up_limit = Decimal('7000')
        mock_limit.income_phase_out_start_single = Decimal('130000')
        mock_limit.income_phase_out_end_single = Decimal('145000')
        mock_limit.account_type = AccountType.TRADITIONAL_401K
        
        compliance_service.db.query().filter().all.return_value = [mock_limit]
        
        result = compliance_service.calculate_cola_adjustments(
            base_year=2024,
            target_year=2025,
            inflation_rate=0.025
        )
        
        assert result['base_year'] == 2024
        assert result['target_year'] == 2025
        assert result['cola_factor'] > 1.0  # Should be greater than 1 with positive inflation
        assert len(result['adjusted_limits']) > 0
        
        adjusted_limit = result['adjusted_limits'][0]
        assert adjusted_limit['adjusted_regular_limit'] > adjusted_limit['base_regular_limit']
    
    def test_contribution_compliance_validation(self, compliance_service):
        """Test contribution compliance validation"""
        
        # Mock contribution limits
        mock_limit = Mock()
        mock_limit.regular_limit = Decimal('7000')
        mock_limit.catch_up_limit = Decimal('1000')
        mock_limit.catch_up_age = 50
        mock_limit.income_phase_out_start_single = Decimal('138000')
        mock_limit.income_phase_out_end_single = Decimal('153000')
        
        compliance_service.db.query().filter().first.return_value = mock_limit
        
        # Test valid contribution
        valid_result = compliance_service.validate_contribution_compliance(
            user_id="test_user",
            account_type=AccountType.ROTH_IRA,
            contribution_amount=Decimal('6000'),
            tax_year=2025,
            user_age=30,
            income=Decimal('80000'),
            filing_status='single'
        )
        
        assert valid_result['compliant'] == True
        assert len(valid_result['violations']) == 0
        
        # Test over-contribution
        over_contribution_result = compliance_service.validate_contribution_compliance(
            user_id="test_user",
            account_type=AccountType.ROTH_IRA,
            contribution_amount=Decimal('8000'),
            tax_year=2025,
            user_age=30,
            income=Decimal('80000'),
            filing_status='single'
        )
        
        assert over_contribution_result['compliant'] == False
        assert len(over_contribution_result['violations']) > 0
        
        # Test income phase-out violation
        high_income_result = compliance_service.validate_contribution_compliance(
            user_id="test_user",
            account_type=AccountType.ROTH_IRA,
            contribution_amount=Decimal('6000'),
            tax_year=2025,
            user_age=30,
            income=Decimal('200000'),
            filing_status='single'
        )
        
        assert high_income_result['compliant'] == False
        assert any('income' in violation.lower() for violation in high_income_result['violations'])
    
    def test_irs_rounding_standards(self, compliance_service):
        """Test IRS standard rounding for contribution limits"""
        
        test_cases = [
            (4325.67, 4300),    # Round to nearest $100 for smaller amounts
            (12750.23, 12500),  # Round to nearest $500 for medium amounts
            (23750.89, 24000),  # Round to nearest $1000 for larger amounts
        ]
        
        for amount, expected in test_cases:
            rounded = compliance_service._round_to_irs_standard(amount)
            assert rounded == expected, f"Amount {amount} should round to {expected}, got {rounded}"


class TestRetirementAccountModels:
    """Test retirement account database models"""
    
    def test_account_type_enum_values(self):
        """Test that all required account types are defined"""
        
        required_types = [
            'traditional_401k', 'roth_401k', 'traditional_ira', 'roth_ira',
            'education_529', 'hsa', 'simple_ira', 'sep_ira', 'pension'
        ]
        
        for account_type in required_types:
            assert hasattr(AccountType, account_type.upper())
    
    def test_contribution_limits_model_constraints(self):
        """Test that contribution limits model has proper constraints"""
        
        # This would test database constraints in an actual database test
        # For now, we'll test the model structure
        
        limit = IRSContributionLimits(
            tax_year=2025,
            account_type=AccountType.TRADITIONAL_401K,
            regular_limit=Decimal('23500'),
            catch_up_limit=Decimal('7500'),
            effective_date=datetime(2025, 1, 1)
        )
        
        assert limit.tax_year == 2025
        assert limit.account_type == AccountType.TRADITIONAL_401K
        assert limit.regular_limit == Decimal('23500')
        assert limit.catch_up_limit == Decimal('7500')


class TestRetirementCalculationAccuracy:
    """Test accuracy of retirement calculations against known scenarios"""
    
    def test_compound_growth_accuracy(self):
        """Test compound growth calculation accuracy"""
        
        # Test the classic $1000 invested for 30 years at 7% = $7,612.26
        principal = Decimal('1000')
        rate = Decimal('0.07')
        years = 30
        
        expected = Decimal('7612.26')  # Known result
        calculated = principal * (Decimal('1') + rate) ** years
        
        # Allow small rounding differences
        assert abs(calculated - expected) < Decimal('1'), \
            f"Expected {expected}, got {calculated}"
    
    def test_present_value_annuity_accuracy(self):
        """Test present value of annuity calculation"""
        
        from app.services.retirement_planning import RetirementPlanningService
        
        service = RetirementPlanningService(Mock())
        
        # Test known scenario: $1000/year for 20 years at 5% = $12,462.21
        payment = Decimal('1000')
        periods = 20
        rate = Decimal('0.05')
        
        expected = Decimal('12462.21')
        calculated = service._present_value_annuity(payment, periods, rate)
        
        assert abs(calculated - expected) < Decimal('10'), \
            f"Expected {expected}, got {calculated}"
    
    def test_retirement_withdrawal_rates(self):
        """Test retirement withdrawal rate scenarios"""
        
        # Test 4% rule sustainability
        retirement_balance = Decimal('1000000')
        withdrawal_rate = Decimal('0.04')
        annual_withdrawal = retirement_balance * withdrawal_rate
        
        assert annual_withdrawal == Decimal('40000')
        
        # Test if balance can sustain withdrawals with growth
        years_tested = 30
        remaining_balance = retirement_balance
        annual_return = Decimal('0.05')  # Conservative estimate
        
        for year in range(years_tested):
            remaining_balance -= annual_withdrawal
            remaining_balance *= (Decimal('1') + annual_return)
        
        # Balance should still be positive after 30 years
        assert remaining_balance > Decimal('0'), "4% rule should sustain for 30 years with 5% returns"


# Integration tests would go here in a real application
# These would test the full API endpoints with a test database

@pytest.mark.integration
class TestRetirementAPIIntegration:
    """Integration tests for retirement planning APIs"""
    
    def test_retirement_account_creation_flow(self):
        """Test complete retirement account creation flow"""
        # This would test the full API flow in integration tests
        pass
    
    def test_contribution_optimization_api(self):
        """Test contribution optimization API endpoint"""
        # This would test the full optimization API
        pass
    
    def test_compliance_validation_api(self):
        """Test IRS compliance validation API"""
        # This would test the compliance API endpoints
        pass


if __name__ == "__main__":
    # Run tests with: python -m pytest app/tests/test_retirement_planning.py -v
    pytest.main([__file__, "-v"])