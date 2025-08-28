"""
Comprehensive unit tests for Tax Optimization Engine

Tests cover:
- Tax-loss harvesting with wash sale rules
- Asset location optimization across account types
- Roth conversion analysis
- Required Minimum Distribution calculations
- Tax bracket optimization
- Multi-state tax considerations
- Property-based testing with Hypothesis
"""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from decimal import Decimal
from hypothesis import given, strategies as st, settings, assume
from unittest.mock import patch, MagicMock
from typing import Dict, List

from app.services.tax.tax_optimization import (
    TaxOptimizationEngine,
    TaxAccountType,
    FilingStatus,
    AssetClass,
    TaxLot,
    AssetAllocation,
    TaxOptimizationResult
)
from tests.factories import (
    create_tax_optimization_scenario,
    TaxOptimizationScenarioFactory
)


class TestTaxOptimizationEngine:
    """Comprehensive tests for tax optimization functionality"""
    
    @pytest.fixture
    def tax_engine(self):
        """Create tax optimization engine"""
        return TaxOptimizationEngine(
            current_year=2024,
            filing_status=FilingStatus.MARRIED_FILING_JOINTLY
        )
    
    @pytest.fixture
    def sample_tax_accounts(self):
        """Sample tax accounts for testing"""
        return {
            TaxAccountType.TAXABLE: Decimal('500000'),
            TaxAccountType.TRADITIONAL_401K: Decimal('400000'),
            TaxAccountType.ROTH_IRA: Decimal('100000'),
            TaxAccountType.HSA: Decimal('25000')
        }
    
    @pytest.fixture
    def sample_holdings(self):
        """Sample holdings with tax lots"""
        return [
            TaxLot(
                symbol='AAPL',
                quantity=100,
                purchase_price=Decimal('150.00'),
                current_price=Decimal('180.00'),
                purchase_date=datetime(2023, 1, 15),
                account_type=TaxAccountType.TAXABLE
            ),
            TaxLot(
                symbol='GOOGL',
                quantity=50,
                purchase_price=Decimal('2800.00'),
                current_price=Decimal('2600.00'),  # Loss position
                purchase_date=datetime(2023, 6, 1),
                account_type=TaxAccountType.TAXABLE
            ),
            TaxLot(
                symbol='SPY',
                quantity=200,
                purchase_price=Decimal('400.00'),
                current_price=Decimal('450.00'),
                purchase_date=datetime(2022, 3, 10),  # Long-term
                account_type=TaxAccountType.TRADITIONAL_401K
            )
        ]
    
    def test_tax_engine_initialization(self, tax_engine):
        """Test tax engine initialization"""
        assert tax_engine.current_year == 2024
        assert tax_engine.filing_status == FilingStatus.MARRIED_FILING_JOINTLY
        assert hasattr(tax_engine, 'tax_brackets')
        assert hasattr(tax_engine, 'standard_deduction')
    
    def test_tax_bracket_calculation(self, tax_engine):
        """Test tax bracket calculations"""
        # Test various income levels
        test_cases = [
            (50000, 'Should be in lower brackets'),
            (100000, 'Middle income'),
            (250000, 'Higher income'),
            (500000, 'High income with higher rates')
        ]
        
        for income, description in test_cases:
            tax_info = tax_engine.calculate_income_tax(
                taxable_income=Decimal(income)
            )
            
            assert tax_info['federal_tax'] >= 0, f"{description}: Federal tax should be non-negative"
            assert tax_info['effective_rate'] >= 0, f"{description}: Effective rate should be non-negative"
            assert tax_info['marginal_rate'] > 0, f"{description}: Marginal rate should be positive"
            
            # Progressive taxation: higher income should have higher effective rate
            if income > 50000:
                lower_tax_info = tax_engine.calculate_income_tax(Decimal(50000))
                assert (tax_info['effective_rate'] >= 
                       lower_tax_info['effective_rate'] - 0.001), \
                       "Progressive taxation property violated"
    
    def test_capital_gains_calculation(self, tax_engine):
        """Test capital gains tax calculations"""
        # Long-term capital gains
        long_term_gain = tax_engine.calculate_capital_gains_tax(
            gain_amount=Decimal('10000'),
            holding_period_days=400,  # Long-term
            income_level=Decimal('80000')
        )
        
        assert long_term_gain['tax_rate'] <= 0.20  # Max long-term rate
        assert long_term_gain['tax_owed'] >= 0
        
        # Short-term capital gains (ordinary income rates)
        short_term_gain = tax_engine.calculate_capital_gains_tax(
            gain_amount=Decimal('10000'),
            holding_period_days=200,  # Short-term
            income_level=Decimal('80000')
        )
        
        # Short-term should be taxed at higher rate
        assert (short_term_gain['tax_rate'] >= 
               long_term_gain['tax_rate'] - 0.001)
    
    def test_tax_loss_harvesting_identification(self, tax_engine, sample_holdings):
        """Test tax-loss harvesting opportunity identification"""
        opportunities = tax_engine.identify_tax_loss_harvesting_opportunities(
            holdings=sample_holdings,
            current_date=datetime(2024, 1, 15)
        )
        
        # Should identify GOOGL as loss opportunity
        loss_opportunities = [opp for opp in opportunities if opp.symbol == 'GOOGL']
        assert len(loss_opportunities) > 0
        
        loss_opp = loss_opportunities[0]
        assert loss_opp.unrealized_loss > 0
        assert loss_opp.tax_benefit > 0
        
        # Should respect wash sale rules
        assert not loss_opp.wash_sale_violation
    
    def test_wash_sale_detection(self, tax_engine):
        """Test wash sale rule detection"""
        # Create scenario with potential wash sale
        sale_date = datetime(2024, 2, 1)
        
        # Sell at loss
        sell_transaction = TaxLot(
            symbol='MSFT',
            quantity=-100,  # Sell
            purchase_price=Decimal('300.00'),
            current_price=Decimal('280.00'),
            purchase_date=datetime(2023, 12, 1),
            transaction_date=sale_date,
            account_type=TaxAccountType.TAXABLE
        )
        
        # Buy back within 30 days
        buy_back = TaxLot(
            symbol='MSFT',
            quantity=50,
            purchase_price=Decimal('275.00'),
            current_price=Decimal('275.00'),
            purchase_date=sale_date + timedelta(days=15),
            account_type=TaxAccountType.TAXABLE
        )
        
        is_wash_sale = tax_engine.check_wash_sale_violation(
            sell_transaction=sell_transaction,
            other_transactions=[buy_back],
            check_date=sale_date + timedelta(days=20)
        )
        
        assert is_wash_sale, "Should detect wash sale violation"
        
        # Test no wash sale if different security
        different_buy = TaxLot(
            symbol='AAPL',  # Different stock
            quantity=50,
            purchase_price=Decimal('175.00'),
            current_price=Decimal('175.00'),
            purchase_date=sale_date + timedelta(days=15),
            account_type=TaxAccountType.TAXABLE
        )
        
        is_not_wash_sale = tax_engine.check_wash_sale_violation(
            sell_transaction=sell_transaction,
            other_transactions=[different_buy],
            check_date=sale_date + timedelta(days=20)
        )
        
        assert not is_not_wash_sale, "Should not detect wash sale for different security"
    
    def test_asset_location_optimization(self, tax_engine, sample_tax_accounts):
        """Test asset location optimization across account types"""
        # Define asset allocations with different tax characteristics
        target_allocation = {
            AssetClass.BONDS: Decimal('0.30'),  # Tax-inefficient
            AssetClass.EQUITIES: Decimal('0.60'),  # Tax-efficient
            AssetClass.REITS: Decimal('0.10')  # Tax-inefficient
        }
        
        optimization_result = tax_engine.optimize_asset_location(
            target_allocation=target_allocation,
            account_balances=sample_tax_accounts,
            investor_tax_rate=Decimal('0.24')
        )
        
        # Bonds should be placed in tax-advantaged accounts
        bond_allocations = optimization_result.asset_locations[AssetClass.BONDS]
        taxable_bond_allocation = bond_allocations.get(TaxAccountType.TAXABLE, Decimal('0'))
        
        # Should minimize bonds in taxable accounts
        total_bonds = sum(bond_allocations.values())
        if total_bonds > 0:
            taxable_bond_ratio = taxable_bond_allocation / total_bonds
            assert taxable_bond_ratio < 0.5, "Bonds should be primarily in tax-advantaged accounts"
        
        # Verify total allocation sums correctly
        for asset_class, target_pct in target_allocation.items():
            actual_total = sum(optimization_result.asset_locations[asset_class].values())
            total_portfolio = sum(sample_tax_accounts.values())
            expected_amount = target_pct * total_portfolio
            
            # Allow small rounding errors
            assert abs(actual_total - expected_amount) < Decimal('1000')
    
    def test_roth_conversion_analysis(self, tax_engine):
        """Test Roth conversion analysis and optimization"""
        conversion_analysis = tax_engine.analyze_roth_conversion(
            traditional_ira_balance=Decimal('200000'),
            current_income=Decimal('80000'),
            current_age=45,
            retirement_age=65,
            conversion_amount=Decimal('50000')
        )
        
        assert conversion_analysis['conversion_tax'] > 0
        assert conversion_analysis['future_tax_savings'] >= 0
        assert 'break_even_years' in conversion_analysis
        assert 'net_present_value' in conversion_analysis
        
        # Should provide recommendation
        assert 'recommendation' in conversion_analysis
        assert conversion_analysis['recommendation'] in ['CONVERT', 'DONT_CONVERT', 'PARTIAL_CONVERT']
    
    def test_roth_ladder_strategy(self, tax_engine):
        """Test Roth ladder conversion strategy"""
        ladder_strategy = tax_engine.create_roth_ladder_strategy(
            traditional_balance=Decimal('500000'),
            current_age=35,
            target_retirement_age=60,  # Early retirement
            annual_expenses=Decimal('60000')
        )
        
        assert len(ladder_strategy.annual_conversions) > 0
        assert ladder_strategy.total_conversions > 0
        assert ladder_strategy.total_tax_cost > 0
        
        # Conversions should be spread over multiple years
        non_zero_conversions = sum(1 for conv in ladder_strategy.annual_conversions 
                                 if conv.amount > 0)
        assert non_zero_conversions >= 5  # Should spread over multiple years
    
    def test_rmd_calculations(self, tax_engine):
        """Test Required Minimum Distribution calculations"""
        # Test RMD for 75-year-old
        rmd_info = tax_engine.calculate_required_minimum_distribution(
            account_balance=Decimal('800000'),
            age=75,
            account_type=TaxAccountType.TRADITIONAL_401K
        )
        
        assert rmd_info['required_amount'] > 0
        assert rmd_info['distribution_factor'] > 0
        assert rmd_info['penalty_if_missed'] > 0
        
        # RMD should increase with age (smaller distribution factor)
        older_rmd = tax_engine.calculate_required_minimum_distribution(
            account_balance=Decimal('800000'),
            age=85,
            account_type=TaxAccountType.TRADITIONAL_401K
        )
        
        # Older age should require larger distribution
        assert (older_rmd['required_amount'] > 
               rmd_info['required_amount'] * Decimal('1.1'))
        
        # Roth IRA should not have RMD for owner
        roth_rmd = tax_engine.calculate_required_minimum_distribution(
            account_balance=Decimal('800000'),
            age=75,
            account_type=TaxAccountType.ROTH_IRA
        )
        
        assert roth_rmd['required_amount'] == 0
    
    def test_charitable_giving_strategies(self, tax_engine):
        """Test charitable giving tax optimization"""
        giving_strategies = tax_engine.optimize_charitable_giving(
            desired_giving_amount=Decimal('25000'),
            income=Decimal('150000'),
            appreciated_assets_available=Decimal('100000'),
            asset_appreciation=Decimal('0.3')  # 30% appreciation
        )
        
        # Should recommend donating appreciated assets
        assert 'donate_appreciated_assets' in giving_strategies['recommendations']
        
        # Calculate tax benefits
        assert giving_strategies['total_tax_benefit'] > 0
        assert giving_strategies['deduction_amount'] > 0
        
        # Should consider donor-advised fund if amount is large
        if giving_strategies['donor_advised_fund_recommended']:
            assert giving_strategies['daf_benefits']['tax_deduction_timing'] == 'IMMEDIATE'
    
    def test_multi_state_tax_optimization(self, tax_engine):
        """Test multi-state tax considerations"""
        state_comparison = tax_engine.compare_state_tax_impact(
            income=Decimal('200000'),
            states=['CA', 'TX', 'FL', 'NY'],
            has_state_tax_deduction=True
        )
        
        assert len(state_comparison) == 4
        
        # Texas and Florida should have lower state tax
        tx_impact = next(s for s in state_comparison if s['state'] == 'TX')
        ca_impact = next(s for s in state_comparison if s['state'] == 'CA')
        
        assert tx_impact['state_tax'] < ca_impact['state_tax']
        assert tx_impact['total_tax'] < ca_impact['total_tax']
    
    @pytest.mark.asyncio
    async def test_comprehensive_optimization_scenario(self, db_session, tax_engine):
        """Test comprehensive tax optimization scenario"""
        # Create complex scenario using factory
        scenario = await create_tax_optimization_scenario(
            session=db_session,
            scenario_type='high_earner'
        )
        
        # Run comprehensive optimization
        optimization_result = tax_engine.optimize_comprehensive_tax_strategy(
            user=scenario['user'],
            financial_profile=scenario['profile'],
            accounts=scenario['accounts'],
            holdings=scenario.get('tax_lots', []),
            goals=['retirement', 'tax_minimization']
        )
        
        # Should provide multiple optimization recommendations
        assert len(optimization_result.recommendations) > 0
        assert optimization_result.projected_annual_tax_savings > 0
        
        # Should include various strategies
        strategy_types = {rec.strategy_type for rec in optimization_result.recommendations}
        expected_strategies = {'TAX_LOSS_HARVESTING', 'ASSET_LOCATION', 'ROTH_CONVERSION'}
        
        # Should recommend at least 2 strategies for high earner
        assert len(strategy_types.intersection(expected_strategies)) >= 2
    
    @given(
        income=st.integers(min_value=50000, max_value=500000),
        conversion_amount=st.integers(min_value=10000, max_value=100000),
        age=st.integers(min_value=25, max_value=65)
    )
    @settings(max_examples=10, deadline=3000)
    def test_roth_conversion_property_based(self, income, conversion_amount, age):
        """Property-based testing for Roth conversions"""
        assume(conversion_amount <= income * 2)  # Reasonable conversion amount
        
        tax_engine = TaxOptimizationEngine(
            current_year=2024,
            filing_status=FilingStatus.SINGLE
        )
        
        analysis = tax_engine.analyze_roth_conversion(
            traditional_ira_balance=Decimal(conversion_amount * 2),
            current_income=Decimal(income),
            current_age=age,
            retirement_age=65,
            conversion_amount=Decimal(conversion_amount)
        )
        
        # Properties that should always hold
        assert analysis['conversion_tax'] >= 0
        assert analysis['future_tax_savings'] >= 0
        assert 'break_even_years' in analysis
        
        # Higher conversion amounts should result in higher taxes
        if conversion_amount > 20000:
            smaller_analysis = tax_engine.analyze_roth_conversion(
                traditional_ira_balance=Decimal(conversion_amount * 2),
                current_income=Decimal(income),
                current_age=age,
                retirement_age=65,
                conversion_amount=Decimal(10000)
            )
            
            assert (analysis['conversion_tax'] >= 
                   smaller_analysis['conversion_tax'] - Decimal('100'))
    
    def test_tax_optimization_edge_cases(self, tax_engine):
        """Test edge cases and error handling"""
        # Test with zero income
        zero_income_tax = tax_engine.calculate_income_tax(Decimal('0'))
        assert zero_income_tax['federal_tax'] == 0
        
        # Test with very high income
        high_income_tax = tax_engine.calculate_income_tax(Decimal('10000000'))
        assert high_income_tax['federal_tax'] > 0
        assert high_income_tax['marginal_rate'] > 0.3  # Should hit top bracket
        
        # Test RMD for very young age (should be 0)
        young_rmd = tax_engine.calculate_required_minimum_distribution(
            account_balance=Decimal('100000'),
            age=50,
            account_type=TaxAccountType.TRADITIONAL_401K
        )
        assert young_rmd['required_amount'] == 0
        
        # Test empty holdings for tax loss harvesting
        empty_opportunities = tax_engine.identify_tax_loss_harvesting_opportunities(
            holdings=[],
            current_date=datetime(2024, 1, 15)
        )
        assert len(empty_opportunities) == 0
    
    def test_tax_calculation_accuracy(self, tax_engine):
        """Test accuracy of tax calculations"""
        # Test known tax calculation (2024 married filing jointly)
        # Standard deduction: $29,200
        # First bracket: 10% on income up to $23,200
        
        test_income = Decimal('50000')
        tax_info = tax_engine.calculate_income_tax(test_income)
        
        # Taxable income should be income minus standard deduction
        expected_taxable = max(Decimal('0'), test_income - tax_engine.standard_deduction)
        
        # Manual calculation for verification
        if expected_taxable <= Decimal('23200'):
            expected_tax = expected_taxable * Decimal('0.10')
        else:
            # 10% on first $23,200, 12% on remainder
            expected_tax = (Decimal('23200') * Decimal('0.10') + 
                          (expected_taxable - Decimal('23200')) * Decimal('0.12'))
        
        # Allow small rounding differences
        assert abs(tax_info['federal_tax'] - expected_tax) < Decimal('10')
    
    def test_performance_requirements(self, tax_engine, sample_holdings):
        """Test performance requirements for tax optimization"""
        import time
        
        # Create larger dataset for performance testing
        large_holdings = []
        for i in range(500):  # 500 holdings
            holding = TaxLot(
                symbol=f'STOCK_{i:03d}',
                quantity=100 + i,
                purchase_price=Decimal('100.00') + Decimal(str(i)),
                current_price=Decimal('95.00') + Decimal(str(i)),  # Some gains, some losses
                purchase_date=datetime(2023, 1, 1) + timedelta(days=i % 365),
                account_type=TaxAccountType.TAXABLE
            )
            large_holdings.append(holding)
        
        start_time = time.time()
        opportunities = tax_engine.identify_tax_loss_harvesting_opportunities(
            holdings=large_holdings,
            current_date=datetime(2024, 1, 15)
        )
        execution_time = time.time() - start_time
        
        # Should complete in reasonable time (under 2 seconds for 500 holdings)
        assert execution_time < 2.0
        assert len(opportunities) > 0  # Should find some opportunities


class TestTaxOptimizationIntegration:
    """Integration tests for tax optimization with other financial modules"""
    
    @pytest.mark.asyncio
    async def test_integration_with_portfolio_optimization(self, db_session):
        """Test tax optimization integration with portfolio optimization"""
        from app.services.optimization.portfolio_optimizer import IntelligentPortfolioOptimizer
        from app.services.optimization.rebalancing import TaxRates
        
        # Create scenario
        scenario = await create_tax_optimization_scenario(
            session=db_session,
            scenario_type='basic'
        )
        
        # Initialize both engines
        tax_engine = TaxOptimizationEngine(
            current_year=2024,
            filing_status=FilingStatus.MARRIED_FILING_JOINTLY
        )
        
        portfolio_optimizer = IntelligentPortfolioOptimizer()
        
        # Create sample assets
        np.random.seed(42)
        assets = []
        for i, symbol in enumerate(['VTI', 'VXUS', 'BND', 'VTEB']):
            returns = pd.Series(np.random.normal(0.08/252, 0.15/np.sqrt(252), 252))
            asset = AssetData(
                symbol=symbol,
                returns=returns,
                expected_return=0.08 - i * 0.01,
                volatility=0.15 + i * 0.02
            )
            assets.append(asset)
        
        # Current holdings with tax implications
        current_holdings = {
            'VTI': 0.4,
            'VXUS': 0.3,
            'BND': 0.2,
            'VTEB': 0.1
        }
        
        tax_rates = TaxRates(
            short_term_capital_gains=0.32,
            long_term_capital_gains=0.15,
            dividend_tax_rate=0.15
        )
        
        # Run tax-aware portfolio optimization
        result = portfolio_optimizer.tax_aware_optimization(
            assets=assets,
            current_holdings=current_holdings,
            tax_rates=tax_rates
        )
        
        # Should produce valid result
        assert isinstance(result, OptimizationResult)
        assert 'estimated_tax_cost' in result.optimization_info
        assert 'turnover' in result.optimization_info
        
        # Tax cost should be reasonable
        assert result.optimization_info['estimated_tax_cost'] >= 0
        assert result.optimization_info['turnover'] <= 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
