"""
Comprehensive unit tests for tax optimization service.

Tests cover:
- Tax-loss harvesting strategies
- Asset location optimization
- Roth conversion analysis
- Tax-aware rebalancing
- Withdrawal sequencing
- Charitable giving strategies
- Estate planning optimization
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from decimal import Decimal
from datetime import datetime, date, timedelta
from typing import Dict, List

from app.services.tax_optimization import (
    TaxOptimizationService, TaxLossHarvestingEngine, AssetLocationOptimizer,
    WithdrawalSequencer, RothConversionAnalyzer
)
from app.models.tax_accounts import TaxLot, Account, AccountType, TaxStatus
from app.schemas.tax_optimization import (
    TaxOptimizationRequest, HarvestingOpportunity, ConversionRecommendation
)


class TestTaxOptimizationService:
    """Test core tax optimization service functionality."""
    
    @pytest.fixture
    def mock_db_session(self):
        """Mock database session."""
        return AsyncMock()
    
    @pytest.fixture
    def tax_service(self, mock_db_session):
        """Create tax optimization service instance."""
        return TaxOptimizationService(db=mock_db_session)
    
    @pytest.fixture
    def sample_taxable_account(self):
        """Sample taxable investment account."""
        return Account(
            id="taxable_001",
            account_type=AccountType.TAXABLE,
            tax_status=TaxStatus.TAXABLE,
            balance=Decimal("100000.00"),
            cost_basis=Decimal("80000.00")
        )
    
    @pytest.fixture
    def sample_tax_lots(self):
        """Sample tax lots for testing."""
        return [
            TaxLot(
                id="lot_001",
                symbol="AAPL",
                quantity=Decimal("100"),
                cost_basis=Decimal("150.00"),
                purchase_date=date(2023, 1, 15),
                current_price=Decimal("180.00"),
                account_id="taxable_001"
            ),
            TaxLot(
                id="lot_002",
                symbol="GOOGL",
                quantity=Decimal("50"),
                cost_basis=Decimal("2800.00"),
                purchase_date=date(2023, 6, 20),
                current_price=Decimal("2600.00"),
                account_id="taxable_001"
            ),
            TaxLot(
                id="lot_003",
                symbol="MSFT",
                quantity=Decimal("75"),
                cost_basis=Decimal("300.00"),
                purchase_date=date(2022, 12, 10),
                current_price=Decimal("420.00"),
                account_id="taxable_001"
            )
        ]
    
    async def test_tax_loss_harvesting_identification(self, tax_service, sample_tax_lots):
        """Test identification of tax-loss harvesting opportunities."""
        
        # Mock database query to return sample tax lots
        tax_service.db.query().filter().all.return_value = sample_tax_lots
        
        opportunities = await tax_service.identify_harvesting_opportunities(
            account_id="taxable_001",
            min_loss_threshold=Decimal("1000.00")
        )
        
        # Should identify GOOGL as a harvesting opportunity (loss > $1000)
        assert len(opportunities) >= 1
        
        googl_opportunity = next(
            (opp for opp in opportunities if opp.symbol == "GOOGL"), None
        )
        assert googl_opportunity is not None
        assert googl_opportunity.unrealized_loss > Decimal("1000.00")
        assert googl_opportunity.days_held > 30  # Avoid wash sale
    
    async def test_wash_sale_detection(self, tax_service):
        """Test wash sale rule detection."""
        
        # Create scenario with potential wash sale
        sell_date = date(2024, 1, 15)
        purchase_dates = [
            date(2024, 1, 1),   # 14 days before - wash sale
            date(2023, 12, 20), # 26 days before - wash sale
            date(2023, 11, 15), # 61 days before - safe
        ]
        
        for purchase_date in purchase_dates:
            is_wash_sale = tax_service._is_wash_sale(
                sell_date=sell_date,
                purchase_date=purchase_date,
                symbol="AAPL"
            )
            
            days_diff = (sell_date - purchase_date).days
            if days_diff <= 30:
                assert is_wash_sale == True, f"Should be wash sale for {days_diff} days"
            else:
                assert is_wash_sale == False, f"Should not be wash sale for {days_diff} days"
    
    async def test_asset_location_optimization(self, tax_service):
        """Test asset location optimization across account types."""
        
        accounts = {
            "taxable": {"balance": Decimal("100000"), "tax_rate": Decimal("0.20")},
            "traditional_401k": {"balance": Decimal("150000"), "tax_rate": Decimal("0.22")},
            "roth_ira": {"balance": Decimal("50000"), "tax_rate": Decimal("0.00")}
        }
        
        assets = [
            {"symbol": "VTI", "expected_return": Decimal("0.07"), "dividend_yield": Decimal("0.015")},
            {"symbol": "VXUS", "expected_return": Decimal("0.06"), "dividend_yield": Decimal("0.025")},
            {"symbol": "BND", "expected_return": Decimal("0.03"), "dividend_yield": Decimal("0.030")},
            {"symbol": "VNQ", "expected_return": Decimal("0.08"), "dividend_yield": Decimal("0.040")}
        ]
        
        optimization = await tax_service.optimize_asset_location(accounts, assets)
        
        # High-dividend/REIT assets should go in tax-advantaged accounts
        roth_allocation = optimization["roth_ira"]
        assert "VNQ" in [asset["symbol"] for asset in roth_allocation], "REITs should be in Roth IRA"
        
        # Tax-efficient funds should go in taxable accounts
        taxable_allocation = optimization["taxable"]
        assert "VTI" in [asset["symbol"] for asset in taxable_allocation], "Tax-efficient funds in taxable"
    
    async def test_roth_conversion_analysis(self, tax_service):
        """Test Roth conversion opportunity analysis."""
        
        analysis = await tax_service.analyze_roth_conversion(
            traditional_balance=Decimal("200000"),
            current_age=45,
            current_tax_rate=Decimal("0.22"),
            expected_retirement_tax_rate=Decimal("0.28"),
            years_to_retirement=20
        )
        
        assert analysis.recommended_conversion_amount > Decimal("0")
        assert analysis.tax_cost > Decimal("0")
        assert analysis.breakeven_years < 20
        assert analysis.net_benefit > Decimal("0")  # Should be beneficial
    
    async def test_withdrawal_sequencing_optimization(self, tax_service):
        """Test optimal withdrawal sequencing from multiple accounts."""
        
        accounts = {
            "taxable": Decimal("100000"),
            "traditional_ira": Decimal("300000"),
            "roth_ira": Decimal("150000")
        }
        
        annual_need = Decimal("50000")
        age = 68
        
        sequence = await tax_service.optimize_withdrawal_sequence(
            accounts=accounts,
            annual_need=annual_need,
            current_age=age,
            tax_rate=Decimal("0.18")
        )
        
        # Should prioritize taxable first, then traditional (for RMD), then Roth last
        assert sequence[0]["account_type"] == "taxable"
        assert sequence[-1]["account_type"] == "roth_ira"
        
        total_withdrawal = sum(step["amount"] for step in sequence)
        assert total_withdrawal == annual_need
    
    async def test_charitable_giving_optimization(self, tax_service):
        """Test charitable giving tax optimization strategies."""
        
        # Highly appreciated stock for donation
        appreciated_stock = TaxLot(
            id="charitable_lot",
            symbol="AAPL",
            quantity=Decimal("100"),
            cost_basis=Decimal("50.00"),
            current_price=Decimal("200.00"),
            purchase_date=date(2020, 1, 1),  # Long-term holding
            account_id="taxable_001"
        )
        
        donation_amount = Decimal("20000")
        tax_rate = Decimal("0.24")
        
        strategy = await tax_service.optimize_charitable_giving(
            donation_amount=donation_amount,
            available_assets=[appreciated_stock],
            tax_rate=tax_rate
        )
        
        # Should recommend donating appreciated stock to avoid capital gains
        assert strategy["method"] == "appreciated_securities"
        assert strategy["tax_savings"] > donation_amount * tax_rate  # Additional savings from avoiding capital gains
    
    async def test_tax_alpha_calculation(self, tax_service):
        """Test calculation of tax alpha from optimization strategies."""
        
        optimization_strategies = [
            {"strategy": "tax_loss_harvesting", "annual_benefit": Decimal("2000")},
            {"strategy": "asset_location", "annual_benefit": Decimal("1500")},
            {"strategy": "roth_conversion", "annual_benefit": Decimal("3000")},
            {"strategy": "withdrawal_sequencing", "annual_benefit": Decimal("1000")}
        ]
        
        portfolio_value = Decimal("1000000")
        
        tax_alpha = tax_service.calculate_tax_alpha(
            optimization_strategies, portfolio_value
        )
        
        expected_alpha = (Decimal("7500") / portfolio_value) * 100  # 0.75%
        assert abs(tax_alpha - expected_alpha) < Decimal("0.01")


class TestTaxLossHarvestingEngine:
    """Test tax-loss harvesting engine functionality."""
    
    @pytest.fixture
    def harvesting_engine(self):
        """Create tax-loss harvesting engine."""
        return TaxLossHarvestingEngine()
    
    @pytest.fixture
    def loss_positions(self):
        """Sample positions with losses."""
        return [
            {
                "symbol": "ARKK",
                "quantity": Decimal("200"),
                "cost_basis": Decimal("100.00"),
                "current_price": Decimal("60.00"),
                "purchase_date": date(2023, 3, 15),
                "unrealized_loss": Decimal("8000.00")
            },
            {
                "symbol": "PLTR",
                "quantity": Decimal("500"),
                "cost_basis": Decimal("25.00"),
                "current_price": Decimal("18.00"),
                "purchase_date": date(2023, 8, 20),
                "unrealized_loss": Decimal("3500.00")
            }
        ]
    
    async def test_harvest_opportunity_ranking(self, harvesting_engine, loss_positions):
        """Test ranking of harvesting opportunities by tax benefit."""
        
        tax_rate = Decimal("0.20")
        
        ranked_opportunities = harvesting_engine.rank_harvesting_opportunities(
            loss_positions, tax_rate
        )
        
        # Should be ranked by tax benefit (loss * tax_rate)
        assert ranked_opportunities[0]["symbol"] == "ARKK"  # Higher loss = higher benefit
        assert ranked_opportunities[0]["tax_benefit"] == Decimal("1600.00")  # $8000 * 0.20
    
    async def test_replacement_security_selection(self, harvesting_engine):
        """Test selection of replacement securities to maintain exposure."""
        
        sold_security = "VTI"  # Total Stock Market ETF
        
        replacements = harvesting_engine.find_replacement_securities(sold_security)
        
        # Should suggest similar but not substantially identical securities
        expected_replacements = ["ITOT", "SCHB", "VTI"]  # Similar total market ETFs
        
        assert len(replacements) > 0
        assert all(rep["correlation"] > 0.95 for rep in replacements)  # High correlation
        assert all(rep["symbol"] != sold_security for rep in replacements)  # Not identical
    
    async def test_wash_sale_timing_optimization(self, harvesting_engine):
        """Test optimal timing to avoid wash sales."""
        
        # Recent purchase that would trigger wash sale
        recent_purchase_date = date.today() - timedelta(days=20)
        sell_date = date.today()
        
        safe_repurchase_date = harvesting_engine.calculate_safe_repurchase_date(
            sell_date=sell_date,
            recent_purchase_date=recent_purchase_date
        )
        
        # Should be at least 31 days after sell date
        assert (safe_repurchase_date - sell_date).days >= 31
    
    async def test_year_end_harvesting_strategy(self, harvesting_engine, loss_positions):
        """Test year-end harvesting strategy optimization."""
        
        current_date = date(2024, 11, 15)  # Late in tax year
        realized_gains = Decimal("15000.00")  # Capital gains to offset
        
        strategy = harvesting_engine.optimize_year_end_harvesting(
            loss_positions=loss_positions,
            realized_gains=realized_gains,
            current_date=current_date
        )
        
        # Should prioritize harvesting enough losses to offset gains
        total_harvested_losses = sum(
            pos["unrealized_loss"] for pos in strategy["recommended_sales"]
        )
        
        # Should harvest at least enough to offset realized gains
        assert total_harvested_losses >= realized_gains


class TestAssetLocationOptimizer:
    """Test asset location optimization functionality."""
    
    @pytest.fixture
    def asset_optimizer(self):
        """Create asset location optimizer."""
        return AssetLocationOptimizer()
    
    @pytest.fixture
    def multi_account_scenario(self):
        """Multi-account scenario for testing."""
        return {
            "accounts": {
                "taxable": {
                    "balance": Decimal("500000"),
                    "tax_rate_ordinary": Decimal("0.24"),
                    "tax_rate_capital_gains": Decimal("0.15"),
                    "tax_rate_dividends": Decimal("0.15")
                },
                "traditional_401k": {
                    "balance": Decimal("300000"),
                    "tax_rate_ordinary": Decimal("0.24"),
                    "tax_rate_capital_gains": Decimal("0.24"),
                    "tax_rate_dividends": Decimal("0.24")
                },
                "roth_ira": {
                    "balance": Decimal("200000"),
                    "tax_rate_ordinary": Decimal("0.00"),
                    "tax_rate_capital_gains": Decimal("0.00"),
                    "tax_rate_dividends": Decimal("0.00")
                }
            },
            "assets": [
                {
                    "symbol": "VTI",
                    "name": "Total Stock Market ETF",
                    "expected_return": Decimal("0.10"),
                    "dividend_yield": Decimal("0.015"),
                    "tax_efficiency": 0.9,  # Very tax efficient
                    "allocation_target": Decimal("0.60")
                },
                {
                    "symbol": "VXUS",
                    "name": "International Stock ETF", 
                    "expected_return": Decimal("0.08"),
                    "dividend_yield": Decimal("0.025"),
                    "tax_efficiency": 0.7,  # Foreign tax credits
                    "allocation_target": Decimal("0.20")
                },
                {
                    "symbol": "BND",
                    "name": "Total Bond Market ETF",
                    "expected_return": Decimal("0.04"),
                    "dividend_yield": Decimal("0.035"),
                    "tax_efficiency": 0.3,  # Taxed as ordinary income
                    "allocation_target": Decimal("0.15")
                },
                {
                    "symbol": "VNQ",
                    "name": "Real Estate ETF",
                    "expected_return": Decimal("0.07"),
                    "dividend_yield": Decimal("0.040"),
                    "tax_efficiency": 0.4,  # Non-qualified dividends
                    "allocation_target": Decimal("0.05")
                }
            ]
        }
    
    async def test_optimal_asset_placement(self, asset_optimizer, multi_account_scenario):
        """Test optimal placement of assets across account types."""
        
        optimization = asset_optimizer.optimize_asset_location(
            accounts=multi_account_scenario["accounts"],
            assets=multi_account_scenario["assets"]
        )
        
        # Tax-inefficient assets should go in tax-advantaged accounts
        traditional_401k_assets = [asset["symbol"] for asset in optimization["traditional_401k"]]
        assert "BND" in traditional_401k_assets, "Bonds should be in 401(k) due to tax inefficiency"
        
        roth_ira_assets = [asset["symbol"] for asset in optimization["roth_ira"]]
        assert "VNQ" in roth_ira_assets, "REITs should be in Roth IRA for tax-free growth"
        
        # Tax-efficient assets should go in taxable accounts
        taxable_assets = [asset["symbol"] for asset in optimization["taxable"]]
        assert "VTI" in taxable_assets, "Tax-efficient stocks should be in taxable accounts"
    
    async def test_tax_alpha_from_asset_location(self, asset_optimizer, multi_account_scenario):
        """Test calculation of tax alpha from optimal asset location."""
        
        # Compare optimized vs. non-optimized allocation
        optimized = asset_optimizer.optimize_asset_location(
            accounts=multi_account_scenario["accounts"],
            assets=multi_account_scenario["assets"]
        )
        
        # Calculate tax alpha
        total_portfolio_value = sum(
            account["balance"] for account in multi_account_scenario["accounts"].values()
        )
        
        tax_alpha = asset_optimizer.calculate_location_alpha(
            optimized_allocation=optimized,
            total_portfolio_value=total_portfolio_value
        )
        
        # Should generate positive tax alpha
        assert tax_alpha > Decimal("0.001")  # At least 0.1% tax alpha
        assert tax_alpha < Decimal("0.02")   # Reasonable upper bound of 2%


class TestWithdrawalSequencer:
    """Test optimal withdrawal sequencing functionality."""
    
    @pytest.fixture
    def withdrawal_sequencer(self):
        """Create withdrawal sequencer."""
        return WithdrawalSequencer()
    
    @pytest.fixture
    def retirement_accounts(self):
        """Sample retirement account balances."""
        return {
            "taxable": Decimal("200000"),
            "traditional_401k": Decimal("400000"),
            "traditional_ira": Decimal("150000"),
            "roth_401k": Decimal("100000"),
            "roth_ira": Decimal("75000")
        }
    
    async def test_pre_59_half_withdrawal_strategy(self, withdrawal_sequencer, retirement_accounts):
        """Test withdrawal strategy for early retirement (before 59.5)."""
        
        annual_need = Decimal("60000")
        current_age = 55
        
        strategy = withdrawal_sequencer.optimize_early_retirement_withdrawals(
            accounts=retirement_accounts,
            annual_need=annual_need,
            current_age=current_age
        )
        
        # Should prioritize penalty-free sources first
        first_source = strategy[0]
        assert first_source["account_type"] == "taxable"  # No penalties
        
        # Should minimize early withdrawal penalties
        total_penalties = sum(
            source.get("penalty", Decimal("0")) for source in strategy
        )
        assert total_penalties < annual_need * Decimal("0.05")  # Keep penalties under 5%
    
    async def test_rmd_compliance_withdrawal(self, withdrawal_sequencer, retirement_accounts):
        """Test withdrawal strategy considering RMD requirements."""
        
        annual_need = Decimal("40000")
        current_age = 75  # Subject to RMDs
        
        # Mock RMD calculations
        required_rmd = {
            "traditional_401k": Decimal("16000"),  # 4% of balance
            "traditional_ira": Decimal("6000")    # 4% of balance
        }
        
        strategy = withdrawal_sequencer.optimize_rmd_withdrawals(
            accounts=retirement_accounts,
            annual_need=annual_need,
            current_age=current_age,
            required_rmds=required_rmd
        )
        
        # Should satisfy RMD requirements first
        traditional_withdrawals = sum(
            source["amount"] for source in strategy 
            if source["account_type"] in ["traditional_401k", "traditional_ira"]
        )
        
        total_required_rmd = sum(required_rmd.values())
        assert traditional_withdrawals >= total_required_rmd
    
    async def test_tax_efficient_withdrawal_sequence(self, withdrawal_sequencer, retirement_accounts):
        """Test tax-efficient withdrawal sequencing."""
        
        annual_need = Decimal("80000")
        current_age = 68
        marginal_tax_rate = Decimal("0.22")
        
        strategy = withdrawal_sequencer.optimize_tax_efficient_withdrawals(
            accounts=retirement_accounts,
            annual_need=annual_need,
            current_age=current_age,
            marginal_tax_rate=marginal_tax_rate
        )
        
        # Should leave Roth accounts for last (tax-free growth)
        roth_sources = [s for s in strategy if "roth" in s["account_type"]]
        if roth_sources:
            roth_position = strategy.index(roth_sources[0])
            assert roth_position > len(strategy) / 2, "Roth should be withdrawn later"
        
        # Calculate total tax impact
        total_taxes = sum(
            source["amount"] * source.get("tax_rate", Decimal("0"))
            for source in strategy
        )
        
        # Should be tax efficient
        effective_tax_rate = total_taxes / annual_need
        assert effective_tax_rate <= marginal_tax_rate


class TestRothConversionAnalyzer:
    """Test Roth conversion analysis functionality."""
    
    @pytest.fixture
    def conversion_analyzer(self):
        """Create Roth conversion analyzer."""
        return RothConversionAnalyzer()
    
    async def test_conversion_opportunity_analysis(self, conversion_analyzer):
        """Test analysis of Roth conversion opportunities."""
        
        scenario = {
            "traditional_balance": Decimal("300000"),
            "current_age": 50,
            "current_tax_rate": Decimal("0.12"),  # Lower bracket this year
            "expected_retirement_tax_rate": Decimal("0.22"),
            "years_to_retirement": 15,
            "expected_return": Decimal("0.07")
        }
        
        analysis = conversion_analyzer.analyze_conversion_opportunity(**scenario)
        
        # Should recommend conversion when current rate < future rate
        assert analysis["recommended_conversion"] > Decimal("0")
        assert analysis["net_benefit"] > Decimal("0")
        assert analysis["breakeven_years"] < 15
    
    async def test_ladder_conversion_strategy(self, conversion_analyzer):
        """Test Roth ladder conversion strategy."""
        
        total_traditional_balance = Decimal("500000")
        years_to_retirement = 10
        annual_tax_capacity = Decimal("50000")  # Can convert this much annually at lower rates
        
        ladder_strategy = conversion_analyzer.design_conversion_ladder(
            total_balance=total_traditional_balance,
            years_available=years_to_retirement,
            annual_capacity=annual_tax_capacity
        )
        
        # Should spread conversions over available years
        assert len(ladder_strategy) <= years_to_retirement
        
        total_conversions = sum(
            year["conversion_amount"] for year in ladder_strategy
        )
        assert total_conversions <= total_traditional_balance
        
        # Should not exceed annual capacity
        for year in ladder_strategy:
            assert year["conversion_amount"] <= annual_tax_capacity
    
    async def test_conversion_tax_impact_calculation(self, conversion_analyzer):
        """Test calculation of tax impact from conversions."""
        
        conversion_amount = Decimal("75000")
        current_income = Decimal("90000")
        filing_status = "married_filing_jointly"
        
        tax_impact = conversion_analyzer.calculate_conversion_tax_impact(
            conversion_amount=conversion_amount,
            current_income=current_income,
            filing_status=filing_status
        )
        
        # Should calculate marginal tax rate impact
        assert tax_impact["additional_tax"] > Decimal("0")
        assert tax_impact["effective_rate"] > Decimal("0")
        assert tax_impact["marginal_rate"] >= tax_impact["effective_rate"]
    
    async def test_conversion_five_year_rule_tracking(self, conversion_analyzer):
        """Test tracking of five-year rule for Roth conversions."""
        
        conversions = [
            {"amount": Decimal("25000"), "conversion_date": date(2020, 3, 15)},
            {"amount": Decimal("30000"), "conversion_date": date(2021, 6, 10)},
            {"amount": Decimal("35000"), "conversion_date": date(2022, 12, 20)}
        ]
        
        withdrawal_date = date(2025, 8, 1)
        age_at_withdrawal = 62
        
        withdrawal_analysis = conversion_analyzer.analyze_conversion_withdrawals(
            conversions=conversions,
            withdrawal_date=withdrawal_date,
            age_at_withdrawal=age_at_withdrawal
        )
        
        # Should identify which conversions are penalty-free
        for conversion in withdrawal_analysis:
            five_years_passed = (
                withdrawal_date - conversion["conversion_date"]
            ).days >= (5 * 365)
            
            if five_years_passed:
                assert conversion["penalty_free"] == True
            else:
                assert conversion["penalty_free"] == False


class TestTaxOptimizationIntegration:
    """Integration tests for tax optimization strategies."""
    
    async def test_comprehensive_tax_strategy(self, tax_service):
        """Test comprehensive tax optimization strategy."""
        
        client_scenario = {
            "age": 45,
            "income": Decimal("150000"),
            "tax_rate": Decimal("0.24"),
            "accounts": {
                "taxable": Decimal("300000"),
                "traditional_401k": Decimal("200000"),
                "roth_ira": Decimal("75000")
            },
            "goals": {
                "retirement_age": 62,
                "annual_retirement_need": Decimal("100000")
            }
        }
        
        # This would integrate multiple tax optimization strategies
        comprehensive_strategy = await tax_service.develop_comprehensive_tax_strategy(
            **client_scenario
        )
        
        # Should include multiple optimization components
        strategy_components = comprehensive_strategy.keys()
        expected_components = [
            "tax_loss_harvesting",
            "asset_location", 
            "roth_conversions",
            "withdrawal_sequencing"
        ]
        
        for component in expected_components:
            assert component in strategy_components
        
        # Should calculate total tax alpha
        assert "total_tax_alpha" in comprehensive_strategy
        assert comprehensive_strategy["total_tax_alpha"] > Decimal("0")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
