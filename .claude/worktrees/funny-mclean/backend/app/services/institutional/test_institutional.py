"""
Test suite for Institutional Portfolio Management System

Demonstrates comprehensive testing of institutional investment capabilities:
- Liability-driven investing (LDI)
- Asset-liability matching (ALM)
- Large order execution algorithms
- Pension fund management
"""

import asyncio
import unittest
from datetime import datetime, timedelta
from typing import Dict, List, Any
import numpy as np

from institutional_manager import (
    InstitutionalPortfolioManager,
    PensionFundManager,
    Liability,
    AssetClass,
    ExecutionOrder,
    LiabilityType,
    ExecutionAlgorithm,
    RiskBudgetType
)


class TestInstitutionalPortfolioManager(unittest.TestCase):
    """Test suite for institutional portfolio management"""
    
    def setUp(self):
        """Initialize test fixtures"""
        self.manager = InstitutionalPortfolioManager()
        self.pension_manager = PensionFundManager(self.manager)
        
        # Create sample liabilities
        self.liabilities = [
            Liability(
                liability_id="L001",
                type=LiabilityType.DEFINED_BENEFIT,
                nominal_value=100_000_000,
                present_value=95_000_000,
                duration=12.5,
                convexity=180,
                payment_schedule=[
                    {"2025-12-31": 5_000_000},
                    {"2026-12-31": 5_500_000},
                    {"2027-12-31": 6_000_000}
                ],
                inflation_linked=True,
                discount_rate=0.045
            ),
            Liability(
                liability_id="L002",
                type=LiabilityType.DEFINED_BENEFIT,
                nominal_value=50_000_000,
                present_value=48_000_000,
                duration=8.5,
                convexity=95,
                payment_schedule=[
                    {"2025-06-30": 2_000_000},
                    {"2025-12-31": 2_200_000},
                    {"2026-06-30": 2_400_000}
                ],
                inflation_linked=False,
                discount_rate=0.040
            )
        ]
        
        # Create sample asset classes
        self.assets = {
            "US_Equity": AssetClass(
                name="US_Equity",
                allocation=0.35,
                target_allocation=0.30,
                min_allocation=0.20,
                max_allocation=0.45,
                expected_return=0.08,
                volatility=0.16,
                duration=0,
                liquidity_score=0.95
            ),
            "International_Equity": AssetClass(
                name="International_Equity",
                allocation=0.15,
                target_allocation=0.15,
                min_allocation=0.10,
                max_allocation=0.25,
                expected_return=0.075,
                volatility=0.18,
                duration=0,
                liquidity_score=0.90
            ),
            "Investment_Grade_Bonds": AssetClass(
                name="Investment_Grade_Bonds",
                allocation=0.30,
                target_allocation=0.35,
                min_allocation=0.25,
                max_allocation=0.50,
                expected_return=0.045,
                volatility=0.05,
                duration=7.5,
                liquidity_score=0.98
            ),
            "High_Yield_Bonds": AssetClass(
                name="High_Yield_Bonds",
                allocation=0.10,
                target_allocation=0.10,
                min_allocation=0.05,
                max_allocation=0.15,
                expected_return=0.065,
                volatility=0.10,
                duration=4.5,
                liquidity_score=0.85
            ),
            "Private_Equity": AssetClass(
                name="Private_Equity",
                allocation=0.10,
                target_allocation=0.10,
                min_allocation=0.05,
                max_allocation=0.20,
                expected_return=0.12,
                volatility=0.25,
                duration=0,
                liquidity_score=0.20
            )
        }
        
        # Set up manager's asset classes
        self.manager.asset_classes = self.assets
    
    # ========================================================================
    # LIABILITY-DRIVEN INVESTING TESTS
    # ========================================================================
    
    def test_ldi_strategy_implementation(self):
        """Test LDI strategy for different funding levels"""
        asyncio.run(self._test_ldi_strategy())
    
    async def _test_ldi_strategy(self):
        """Async test for LDI strategy"""
        # Test with different funding scenarios
        scenarios = [
            {"assets": {"total": 75_000_000}, "name": "Severely Underfunded"},
            {"assets": {"total": 95_000_000}, "name": "Underfunded"},
            {"assets": {"total": 143_000_000}, "name": "Near Fully Funded"},
            {"assets": {"total": 160_000_000}, "name": "Overfunded"}
        ]
        
        for scenario in scenarios:
            print(f"\n{'='*60}")
            print(f"Testing LDI Strategy: {scenario['name']}")
            print(f"{'='*60}")
            
            result = await self.manager.implement_ldi_strategy(
                liabilities=self.liabilities,
                assets=scenario["assets"],
                target_funding_ratio=1.05
            )
            
            self.assertIn('strategy_type', result)
            self.assertIn('funding_metrics', result)
            self.assertIn('asset_allocation', result)
            self.assertIn('hedging_strategy', result)
            
            print(f"Strategy Type: {result['strategy_type']}")
            print(f"Current Funding Ratio: {result['funding_metrics']['current_ratio']:.2%}")
            print(f"Required Return: {result['funding_metrics']['required_return']:.2%}")
            print(f"Duration Gap: {result['hedging_strategy']['duration_gap']:.2f} years")
            print(f"\nRecommended Allocation:")
            for asset, weight in result['asset_allocation'].items():
                if isinstance(weight, (int, float)):
                    print(f"  {asset}: {weight:.1%}")
    
    # ========================================================================
    # ASSET-LIABILITY MATCHING TESTS
    # ========================================================================
    
    def test_alm_optimization(self):
        """Test asset-liability matching optimization"""
        asyncio.run(self._test_alm_optimization())
    
    async def _test_alm_optimization(self):
        """Async test for ALM optimization"""
        print(f"\n{'='*60}")
        print("Testing Asset-Liability Matching Optimization")
        print(f"{'='*60}")
        
        constraints = {
            'min_funding_return': 0.06,
            'max_tracking_error': 0.08
        }
        
        result = await self.manager.optimize_alm(
            assets=self.assets,
            liabilities=self.liabilities,
            constraints=constraints
        )
        
        self.assertIn('optimal_allocation', result)
        self.assertIn('portfolio_metrics', result)
        self.assertIn('alm_metrics', result)
        
        print("\nOptimal ALM Allocation:")
        for asset, weight in result['optimal_allocation'].items():
            print(f"  {asset}: {weight:.1%}")
        
        print(f"\nPortfolio Metrics:")
        print(f"  Expected Return: {result['portfolio_metrics']['expected_return']:.2%}")
        print(f"  Volatility: {result['portfolio_metrics']['volatility']:.2%}")
        print(f"  Duration: {result['portfolio_metrics']['duration']:.2f} years")
        print(f"  Sharpe Ratio: {result['portfolio_metrics']['sharpe_ratio']:.2f}")
        
        print(f"\nALM Metrics:")
        print(f"  Duration Match: {result['alm_metrics']['duration_match']:.2f} years")
        print(f"  Surplus at Risk (95%): ${result['alm_metrics']['surplus_at_risk']:,.0f}")
    
    # ========================================================================
    # GLIDE PATH OPTIMIZATION TESTS
    # ========================================================================
    
    def test_glide_path_optimization(self):
        """Test glide path optimization for different participants"""
        print(f"\n{'='*60}")
        print("Testing Glide Path Optimization")
        print(f"{'='*60}")
        
        test_cases = [
            {
                "current_age": 35,
                "retirement_age": 65,
                "life_expectancy": 85,
                "risk_tolerance": 0.7,
                "funding_status": 0.85,
                "description": "Young participant, underfunded"
            },
            {
                "current_age": 55,
                "retirement_age": 65,
                "life_expectancy": 85,
                "risk_tolerance": 0.4,
                "funding_status": 1.05,
                "description": "Near retirement, fully funded"
            },
            {
                "current_age": 45,
                "retirement_age": 65,
                "life_expectancy": 85,
                "risk_tolerance": 0.5,
                "funding_status": 0.95,
                "description": "Mid-career, slightly underfunded"
            }
        ]
        
        for case in test_cases:
            print(f"\n{case['description']}:")
            result = self.manager.optimize_glide_path(
                current_age=case['current_age'],
                retirement_age=case['retirement_age'],
                life_expectancy=case['life_expectancy'],
                risk_tolerance=case['risk_tolerance'],
                funding_status=case['funding_status']
            )
            
            self.assertIn('glide_path', result)
            self.assertIn('current_allocation', result)
            
            print(f"  Current Allocation:")
            for asset, weight in result['current_allocation'].items():
                print(f"    {asset}: {weight:.1%}")
            
            print(f"  Retirement Allocation:")
            for asset, weight in result['retirement_allocation'].items():
                print(f"    {asset}: {weight:.1%}")
    
    # ========================================================================
    # RISK BUDGETING TESTS
    # ========================================================================
    
    def test_risk_budgeting(self):
        """Test different risk budgeting approaches"""
        print(f"\n{'='*60}")
        print("Testing Risk Budgeting Strategies")
        print(f"{'='*60}")
        
        strategies = [
            RiskBudgetType.EQUAL_RISK,
            RiskBudgetType.RISK_PARITY,
            RiskBudgetType.MAXIMUM_DIVERSIFICATION,
            RiskBudgetType.VOLATILITY_TARGET
        ]
        
        for strategy in strategies:
            print(f"\n{strategy.value.replace('_', ' ').title()}:")
            
            result = self.manager.implement_risk_budgeting(
                assets=self.assets,
                risk_budget_type=strategy,
                total_risk_budget=0.12
            )
            
            self.assertIn('risk_budget_allocation', result)
            self.assertIn('portfolio_metrics', result)
            
            print(f"  Portfolio Volatility: {result['portfolio_metrics']['volatility']:.2%}")
            print(f"  Sharpe Ratio: {result['portfolio_metrics']['sharpe_ratio']:.2f}")
            print(f"  Diversification Ratio: {result['risk_metrics']['diversification_ratio']:.2f}")
            
            # Show top 3 allocations
            allocations = sorted(
                result['risk_budget_allocation'].items(),
                key=lambda x: x[1]['weight'],
                reverse=True
            )[:3]
            
            print("  Top Allocations:")
            for asset, details in allocations:
                print(f"    {asset}: {details['weight']:.1%} (Risk: {details['risk_budget']:.1%})")
    
    # ========================================================================
    # OVERLAY STRATEGY TESTS
    # ========================================================================
    
    def test_overlay_strategies(self):
        """Test overlay strategy design"""
        asyncio.run(self._test_overlay_strategies())
    
    async def _test_overlay_strategies(self):
        """Async test for overlay strategies"""
        print(f"\n{'='*60}")
        print("Testing Overlay Strategies")
        print(f"{'='*60}")
        
        base_portfolio = {
            "US_Equity": 50_000_000,
            "International_Equity": 20_000_000,
            "Investment_Grade_Bonds": 40_000_000,
            "High_Yield_Bonds": 15_000_000,
            "Private_Equity": 15_000_000
        }
        
        overlay_objectives = [
            "duration_matching",
            "currency_hedging",
            "tail_risk_hedging"
        ]
        
        constraints = {
            "max_cost_bps": 50,
            "max_margin_pct": 0.10,
            "min_hedge_effectiveness": 0.80
        }
        
        result = await self.manager.design_overlay_strategy(
            base_portfolio=base_portfolio,
            overlay_objectives=overlay_objectives,
            constraints=constraints
        )
        
        self.assertIn('overlay_strategies', result)
        self.assertIn('aggregate_metrics', result)
        
        print("\nOverlay Strategies Designed:")
        for strategy in result['overlay_strategies']:
            print(f"\n  {strategy['type'].replace('_', ' ').title()}:")
            print(f"    Notional: ${strategy['notional']:,.0f}")
            print(f"    Hedge Ratio: {strategy['hedge_ratio']:.1%}")
            print(f"    Cost: {strategy['cost_bps']:.1f} bps")
            print(f"    Effectiveness: {strategy['effectiveness']:.1%}")
            print(f"    Instruments: {', '.join(strategy['instruments'][:2])}")
        
        print(f"\nAggregate Costs:")
        print(f"  Total Cost: {result['aggregate_metrics']['total_cost_bps']:.1f} bps")
        print(f"  Margin Required: ${result['aggregate_metrics']['total_margin']:,.0f}")
    
    # ========================================================================
    # LARGE ORDER EXECUTION TESTS
    # ========================================================================
    
    def test_large_order_execution(self):
        """Test large order execution algorithms"""
        asyncio.run(self._test_large_order_execution())
    
    async def _test_large_order_execution(self):
        """Async test for order execution"""
        print(f"\n{'='*60}")
        print("Testing Large Order Execution Algorithms")
        print(f"{'='*60}")
        
        # Create test orders
        orders = [
            ExecutionOrder(
                symbol="AAPL",
                quantity=500_000,
                side="buy",
                algorithm=ExecutionAlgorithm.VWAP,
                urgency=0.3,
                risk_aversion=0.7,
                start_time=datetime.now(),
                end_time=datetime.now() + timedelta(hours=6),
                participation_rate=0.15
            ),
            ExecutionOrder(
                symbol="SPY",
                quantity=1_000_000,
                side="sell",
                algorithm=ExecutionAlgorithm.IS,
                urgency=0.8,
                risk_aversion=0.5,
                start_time=datetime.now(),
                end_time=datetime.now() + timedelta(hours=2),
                participation_rate=0.25
            )
        ]
        
        market_conditions = {
            'current_price': 100,
            'arrival_price': 100,
            'spread': 0.01,
            'volatility': 0.20,
            'daily_volume': 10_000_000,
            'drift': 0.08,
            'close_price': 101
        }
        
        for order in orders:
            print(f"\nExecuting {order.quantity:,} share {order.side} order of {order.symbol}")
            print(f"  Algorithm: {order.algorithm.value.upper()}")
            
            result = await self.manager.execute_large_order(order, market_conditions)
            
            self.assertIn('execution_summary', result)
            self.assertIn('transaction_cost_analysis', result)
            
            print(f"  Average Price: ${result['execution_summary']['avg_price']:.2f}")
            print(f"  Total Cost: ${result['execution_summary']['total_cost']:,.2f}")
            print(f"  Cost (bps): {result['execution_summary']['cost_bps']:.1f}")
            
            print(f"\n  Cost Breakdown:")
            tca = result['transaction_cost_analysis']
            print(f"    Spread Cost: ${tca['spread_cost']:,.2f}")
            print(f"    Market Impact: ${tca['market_impact']:,.2f}")
            print(f"    Delay Cost: ${tca['delay_cost']:,.2f}")
            print(f"    Implementation Shortfall: ${tca['implementation_shortfall']:,.2f}")
    
    # ========================================================================
    # TRANSACTION COST ANALYSIS TESTS
    # ========================================================================
    
    def test_transaction_cost_analysis(self):
        """Test comprehensive TCA"""
        print(f"\n{'='*60}")
        print("Testing Transaction Cost Analysis")
        print(f"{'='*60}")
        
        # Create sample trades
        trades = [
            {
                'symbol': 'MSFT',
                'quantity': 100_000,
                'execution_price': 250.50,
                'benchmark_price': 250.00,
                'spread': 0.02,
                'side': 'buy',
                'algorithm': 'VWAP',
                'venue': 'NYSE'
            },
            {
                'symbol': 'GOOGL',
                'quantity': 50_000,
                'execution_price': 2800.75,
                'benchmark_price': 2801.00,
                'spread': 0.05,
                'side': 'sell',
                'algorithm': 'IS',
                'venue': 'NASDAQ'
            },
            {
                'symbol': 'AMZN',
                'quantity': 75_000,
                'execution_price': 3300.25,
                'benchmark_price': 3298.00,
                'spread': 0.03,
                'side': 'buy',
                'algorithm': 'TWAP',
                'venue': 'NYSE'
            }
        ]
        
        result = self.manager.analyze_transaction_costs(trades, benchmark="arrival")
        
        self.assertIn('aggregate_costs', result)
        self.assertIn('statistical_summary', result)
        
        print("\nAggregate Transaction Costs:")
        print(f"  Total Cost: ${result['aggregate_costs']['total_cost']:,.2f}")
        
        print("\nCost Breakdown:")
        breakdown = result['cost_breakdown']
        print(f"  Spread: {breakdown['spread_percentage']:.1f}%")
        print(f"  Market Impact: {breakdown['impact_percentage']:.1f}%")
        print(f"  Delay: {breakdown['delay_percentage']:.1f}%")
        
        print("\nStatistical Summary:")
        stats = result['statistical_summary']
        print(f"  Mean Cost: {stats['mean_cost_bps']:.1f} bps")
        print(f"  Median Cost: {stats['median_cost_bps']:.1f} bps")
        print(f"  95th Percentile: {stats['percentile_95']:.1f} bps")
        
        print("\nTrade-Level Analysis:")
        for trade in result['trade_level_analytics'][:3]:
            print(f"  {trade['symbol']}: {trade['total_cost_bps']:.1f} bps")
    
    # ========================================================================
    # PENSION FUND MANAGEMENT TESTS
    # ========================================================================
    
    def test_pension_funding_projection(self):
        """Test pension funding ratio projections"""
        asyncio.run(self._test_pension_funding())
    
    async def _test_pension_funding(self):
        """Async test for pension funding projections"""
        print(f"\n{'='*60}")
        print("Testing Pension Fund Projections")
        print(f"{'='*60}")
        
        participant_data = {
            'active_count': 10_000,
            'retiree_count': 5_000,
            'avg_salary': 75_000,
            'avg_benefit': 30_000,
            'contribution_rate': 0.10,
            'cola': 0.02,
            'workforce_growth': 0.01
        }
        
        economic_assumptions = {
            'expected_return': 0.07,
            'volatility': 0.12,
            'discount_rate': 0.045,
            'salary_growth': 0.03
        }
        
        result = await self.pension_manager.project_funding_ratio(
            current_assets=900_000_000,
            current_liabilities=1_000_000_000,
            participant_data=participant_data,
            economic_assumptions=economic_assumptions,
            years=20
        )
        
        self.assertIn('funding_ratio_percentiles', result)
        self.assertIn('probability_underfunded', result)
        self.assertIn('regulatory_compliance', result)
        
        print("\nFunding Ratio Projections:")
        print("Year | Median | 25th % | 75th % | P(Underfunded)")
        print("-" * 50)
        
        years_to_show = [0, 5, 10, 15, 20]
        for year in years_to_show:
            median = result['funding_ratio_percentiles']['p50'][year]
            p25 = result['funding_ratio_percentiles']['p25'][year]
            p75 = result['funding_ratio_percentiles']['p75'][year]
            prob_under = result['probability_underfunded'][year]
            
            print(f"{year:4d} | {median:.1%} | {p25:.1%} | {p75:.1%} | {prob_under:.1%}")
        
        print(f"\nRegulatory Compliance:")
        compliance = result['regulatory_compliance']
        print(f"  Meets Minimum Requirements: {compliance['meets_minimum']}")
        print(f"  PBGC Variable Premium: ${compliance['pbgc_variable_premium']:,.0f}")
        print(f"  ERISA Notice Required: {compliance['erisa_funding_notice_required']}")
        
        print(f"\nRisk Metrics:")
        risk = result['risk_metrics']
        print(f"  Funding Volatility: {risk['funding_ratio_volatility']:.2%}")
        print(f"  Worst Case (1%): {risk['worst_case_scenario']:.1%}")
        
        print(f"\nRecommendations:")
        for i, rec in enumerate(result['recommendations'][:3], 1):
            print(f"  {i}. {rec}")
    
    # ========================================================================
    # STRESS TESTING
    # ========================================================================
    
    def test_portfolio_stress_testing(self):
        """Test portfolio stress testing"""
        asyncio.run(self._test_stress_testing())
    
    async def _test_stress_testing(self):
        """Async test for stress testing"""
        print(f"\n{'='*60}")
        print("Testing Portfolio Stress Testing")
        print(f"{'='*60}")
        
        portfolio = {
            "US_Equity": 50_000_000,
            "International_Equity": 20_000_000,
            "Investment_Grade_Bonds": 40_000_000,
            "High_Yield_Bonds": 15_000_000,
            "Private_Equity": 15_000_000
        }
        
        scenarios = [
            "equity_crash_2008",
            "covid_pandemic_2020",
            "inflation_surge_2022"
        ]
        
        result = await self.manager.stress_test_portfolio(portfolio, scenarios)
        
        self.assertIn('scenario_results', result)
        self.assertIn('risk_metrics', result)
        
        print("\nStress Test Results:")
        print("Scenario                | Portfolio Loss | Funding Impact")
        print("-" * 60)
        
        for scenario, impact in result['scenario_results'].items():
            print(f"{scenario:22s} | {impact['portfolio_loss']:13.1%} | {impact['funding_ratio_impact']:.1%}")
        
        print(f"\nRisk Summary:")
        print(f"  Worst Case Loss: {result['risk_metrics']['worst_case_loss']:.1%}")
        print(f"  Expected Shortfall (95%): {result['risk_metrics']['expected_shortfall_95']:.1%}")
        
        if 'hedging_recommendations' in result:
            print(f"\nHedging Recommendations:")
            for rec in result['hedging_recommendations'][:3]:
                print(f"  - {rec}")


def run_tests():
    """Run all institutional portfolio management tests"""
    suite = unittest.TestLoader().loadTestsFromTestCase(TestInstitutionalPortfolioManager)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)


if __name__ == "__main__":
    print("="*70)
    print("INSTITUTIONAL PORTFOLIO MANAGEMENT SYSTEM TEST SUITE")
    print("="*70)
    print("\nThis test suite demonstrates:")
    print("- Liability-Driven Investing (LDI) strategies")
    print("- Asset-Liability Matching (ALM) optimization")
    print("- Glide path optimization for different funding levels")
    print("- Risk budgeting frameworks")
    print("- Overlay strategy design")
    print("- Large order execution algorithms")
    print("- Transaction cost analysis")
    print("- Pension funding projections")
    print("- Comprehensive stress testing")
    print("="*70)
    
    run_tests()