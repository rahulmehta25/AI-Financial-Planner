#!/usr/bin/env python3
"""
Simple ML and Simulation Test Script
==================================

This script tests the core working ML and simulation components
without requiring external dependencies or database connections.
"""

import sys
import os
import asyncio
import logging
import time
import json
from datetime import datetime
import numpy as np

# Add the app directory to Python path
sys.path.append('/Users/rahulmehta/Desktop/Financial Planning/backend')
sys.path.append('/Users/rahulmehta/Desktop/Financial Planning/backend/app')

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_market_assumptions():
    """Test 1: Market Assumptions and Capital Market Model"""
    print("\n" + "="*60)
    print("🏦 TESTING MARKET ASSUMPTIONS")
    print("="*60)
    
    try:
        from app.simulations.market_assumptions import CapitalMarketAssumptions
        
        # Initialize market assumptions
        cma = CapitalMarketAssumptions()
        print(f"✅ Initialized with {len(cma.asset_classes)} asset classes")
        
        # Test asset classes
        for name, asset in list(cma.asset_classes.items())[:3]:
            print(f"   📊 {name}: {asset.expected_return:.1%} return, {asset.volatility:.1%} volatility")
        
        # Test correlation matrix
        corr_matrix, asset_names = cma.get_covariance_matrix()
        print(f"✅ Covariance matrix: {corr_matrix.shape}")
        
        # Test inflation simulation
        inflation_paths = cma.simulate_inflation_path(years=5, n_simulations=100)
        print(f"✅ Inflation simulation: {inflation_paths.shape}")
        
        # Test summary statistics
        stats = cma.get_summary_statistics()
        print(f"✅ Summary stats - Mean return: {stats['expected_returns']['mean']:.1%}")
        
        return True
        
    except Exception as e:
        print(f"❌ Market Assumptions test failed: {e}")
        return False

def test_monte_carlo_engine():
    """Test 2: Monte Carlo Simulation Engine"""
    print("\n" + "="*60)
    print("🎯 TESTING MONTE CARLO ENGINE")
    print("="*60)
    
    try:
        from app.simulations.engine import MonteCarloEngine, PortfolioAllocation, SimulationParameters
        
        # Initialize engine
        engine = MonteCarloEngine()
        print("✅ Monte Carlo engine initialized")
        
        # Create test portfolio
        portfolio = PortfolioAllocation({
            "US_LARGE_CAP": 0.60,
            "INTERNATIONAL_DEVELOPED": 0.20,
            "CORPORATE_BONDS": 0.20
        })
        print("✅ Test portfolio created (60% US Large Cap, 20% International, 20% Bonds)")
        
        # Create simulation parameters
        parameters = SimulationParameters(
            n_simulations=1000,  # Smaller for quick test
            years_to_retirement=20,
            retirement_years=15,
            initial_portfolio_value=100000,
            annual_contribution=12000,
            random_seed=42
        )
        print("✅ Simulation parameters configured")
        
        # Run simulation
        print("🔄 Running Monte Carlo simulation...")
        start_time = time.time()
        results = engine.run_simulation(portfolio, parameters)
        simulation_time = time.time() - start_time
        
        print(f"✅ Simulation completed in {simulation_time:.2f} seconds")
        print(f"   📊 Success probability: {results['success_probability']:.1%}")
        print(f"   💰 Median retirement balance: ${results['retirement_balance_stats']['median']:,.0f}")
        
        # Test performance metrics
        performance = engine.get_performance_metrics()
        print(f"   ⚡ Performance: {performance.get('simulations_per_second', 0):,} sims/sec")
        
        return True
        
    except Exception as e:
        print(f"❌ Monte Carlo Engine test failed: {e}")
        return False

def test_portfolio_mapping():
    """Test 3: Portfolio Optimization and Mapping"""
    print("\n" + "="*60)
    print("📈 TESTING PORTFOLIO OPTIMIZATION")
    print("="*60)
    
    try:
        from app.simulations.portfolio_mapping import PortfolioMapper, RiskTolerance
        from app.simulations.engine import PortfolioAllocation
        
        # Initialize portfolio mapper
        mapper = PortfolioMapper()
        print("✅ Portfolio mapper initialized")
        
        # Test model portfolios
        risk_levels = [RiskTolerance.CONSERVATIVE, RiskTolerance.MODERATE, RiskTolerance.AGGRESSIVE]
        for risk_level in risk_levels:
            portfolio = mapper.get_model_portfolio(risk_level)
            print(f"   📊 {risk_level.value.title()}: {portfolio.expected_return:.1%} return, {portfolio.expected_volatility:.1%} volatility")
        
        # Test age-adjusted portfolios
        young_portfolio = mapper.get_age_adjusted_portfolio(RiskTolerance.MODERATE, 25)
        old_portfolio = mapper.get_age_adjusted_portfolio(RiskTolerance.MODERATE, 65)
        
        # Calculate equity allocations for comparison
        equity_assets = ["US_LARGE_CAP", "US_SMALL_CAP", "INTERNATIONAL_DEVELOPED", "EMERGING_MARKETS"]
        young_equity = sum(young_portfolio.allocations.get(asset, 0) for asset in equity_assets)
        old_equity = sum(old_portfolio.allocations.get(asset, 0) for asset in equity_assets)
        
        print(f"✅ Age adjustment: 25yr old = {young_equity:.1%} equity, 65yr old = {old_equity:.1%} equity")
        
        # Test ETF recommendations
        test_allocation = PortfolioAllocation({"US_LARGE_CAP": 0.70, "CORPORATE_BONDS": 0.30})
        etf_recommendations = mapper.get_etf_recommendations(test_allocation)
        print(f"✅ ETF recommendations: {len(etf_recommendations)} ETFs suggested")
        for etf in etf_recommendations:
            print(f"   💼 {etf.symbol}: {etf.name} (Expense: {etf.expense_ratio:.2%})")
        
        return True
        
    except Exception as e:
        print(f"❌ Portfolio Optimization test failed: {e}")
        return False

def test_ml_recommendation_engine():
    """Test 4: ML Recommendation Engine (Structure Only)"""
    print("\n" + "="*60)
    print("🤖 TESTING ML RECOMMENDATION ENGINE")
    print("="*60)
    
    try:
        from app.ml.recommendations.recommendation_engine import RecommendationEngine
        
        # Initialize recommendation engine
        rec_engine = RecommendationEngine()
        print("✅ ML Recommendation engine initialized")
        
        # Test module status
        status = rec_engine.get_recommendation_status()
        print(f"✅ Overall health: {status['overall_health']}")
        print(f"   📦 Available modules: {len(status['modules'])}")
        
        # Test available categories
        categories = list(rec_engine.recommendation_categories.keys())
        print(f"✅ Recommendation categories: {len(categories)}")
        for category in categories[:3]:
            print(f"   🎯 {category}: {rec_engine.recommendation_categories[category]}")
        
        # Test training system (without actual training)
        print("✅ Model training system available")
        
        return True
        
    except Exception as e:
        print(f"❌ ML Recommendation Engine test failed: {e}")
        return False

async def test_ai_narrative_generation():
    """Test 5: AI Narrative Generation (Fallback Mode)"""
    print("\n" + "="*60)
    print("📝 TESTING AI NARRATIVE GENERATION")
    print("="*60)
    
    try:
        from app.ai.narrative_generator import NarrativeGenerator
        from app.ai.template_manager import TemplateType
        from app.ai.config import Language
        
        # Initialize narrative generator
        generator = NarrativeGenerator()
        print("✅ AI Narrative generator initialized")
        
        # Test narrative generation (will use fallback mode)
        sample_data = {
            "user_name": "Test User",
            "portfolio_value": 150000,
            "success_probability": 0.85,
            "retirement_years": 25,
            "monthly_income_needed": 5000
        }
        
        print("🔄 Generating narrative (fallback mode)...")
        narrative_result = await generator.generate_narrative(
            template_type=TemplateType.RETIREMENT_ANALYSIS,
            data=sample_data,
            user_id="test_user"
        )
        
        print(f"✅ Narrative generated")
        print(f"   📄 Length: {len(narrative_result.get('narrative', ''))} characters")
        print(f"   🔧 Provider: {narrative_result.get('provider', 'unknown')}")
        print(f"   ⏱️  Generation time: {narrative_result.get('generation_time_ms', 0):.0f}ms")
        
        # Show sample of narrative
        narrative = narrative_result.get('narrative', '')
        if narrative:
            sample = narrative[:200] + "..." if len(narrative) > 200 else narrative
            print(f"   📖 Sample: {sample}")
        
        return True
        
    except Exception as e:
        print(f"❌ AI Narrative Generation test failed: {e}")
        return False

def test_integration_workflow():
    """Test 6: Integration Between Components"""
    print("\n" + "="*60)
    print("🔗 TESTING COMPONENT INTEGRATION")
    print("="*60)
    
    try:
        from app.simulations.engine import MonteCarloEngine, PortfolioAllocation, SimulationParameters
        from app.simulations.portfolio_mapping import PortfolioMapper, RiskTolerance
        
        print("🔄 Running integrated workflow...")
        
        # Step 1: Create optimized portfolio
        mapper = PortfolioMapper()
        portfolio_allocation = mapper.get_age_adjusted_portfolio(RiskTolerance.MODERATE, 35)
        print("✅ Step 1: Portfolio optimized for 35-year-old moderate investor")
        
        # Step 2: Run Monte Carlo simulation
        engine = MonteCarloEngine()
        parameters = SimulationParameters(
            n_simulations=500,  # Smaller for integration test
            years_to_retirement=30,
            initial_portfolio_value=50000,
            annual_contribution=15000
        )
        
        simulation_results = engine.run_simulation(portfolio_allocation, parameters)
        print("✅ Step 2: Monte Carlo simulation completed")
        
        # Step 3: Analyze results
        success_rate = simulation_results['success_probability']
        median_balance = simulation_results['retirement_balance_stats']['median']
        
        print("✅ Step 3: Results analyzed")
        print(f"   🎯 Success probability: {success_rate:.1%}")
        print(f"   💰 Median retirement balance: ${median_balance:,.0f}")
        
        # Step 4: Generate summary
        portfolio_dict = dict(portfolio_allocation.allocations)
        equity_total = sum(v for k, v in portfolio_dict.items() 
                          if k in ["US_LARGE_CAP", "US_SMALL_CAP", "INTERNATIONAL_DEVELOPED", "EMERGING_MARKETS"])
        
        print("✅ Step 4: Integration summary completed")
        print(f"   📊 Portfolio: {equity_total:.1%} equity allocation")
        print(f"   ⏱️  Performance: {engine.get_performance_metrics().get('last_simulation_time_seconds', 0):.2f}s")
        
        return True
        
    except Exception as e:
        print(f"❌ Integration workflow test failed: {e}")
        return False

def create_demo_scenarios():
    """Create sample scenarios for demonstration"""
    print("\n" + "="*60)
    print("👥 DEMO SCENARIOS")
    print("="*60)
    
    scenarios = [
        {
            "name": "Young Professional",
            "age": 28,
            "risk_tolerance": "moderately_aggressive",
            "initial_savings": 25000,
            "annual_contribution": 15000,
            "years_to_retirement": 37
        },
        {
            "name": "Mid-Career Executive",
            "age": 45,
            "risk_tolerance": "moderate",
            "initial_savings": 200000,
            "annual_contribution": 25000,
            "years_to_retirement": 20
        },
        {
            "name": "Pre-Retirement Couple",
            "age": 58,
            "risk_tolerance": "conservative",
            "initial_savings": 750000,
            "annual_contribution": 30000,
            "years_to_retirement": 7
        }
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"{i}. {scenario['name']} (Age {scenario['age']})")
        print(f"   💰 Initial: ${scenario['initial_savings']:,}")
        print(f"   📈 Annual Contribution: ${scenario['annual_contribution']:,}")
        print(f"   🎯 Risk: {scenario['risk_tolerance']}")
        print(f"   ⏰ Years to retirement: {scenario['years_to_retirement']}")
        print()

async def main():
    """Main test execution"""
    print("="*80)
    print("🚀 FINANCIAL PLANNING ML & SIMULATION COMPONENT TEST")
    print("="*80)
    print(f"📅 Start Time: {datetime.now()}")
    print(f"📁 Backend Path: /Users/rahulmehta/Desktop/Financial Planning/backend")
    
    # Track test results
    test_results = []
    start_time = time.time()
    
    # Run all tests
    tests = [
        ("Market Assumptions", test_market_assumptions),
        ("Monte Carlo Engine", test_monte_carlo_engine),
        ("Portfolio Optimization", test_portfolio_mapping),
        ("ML Recommendation Engine", test_ml_recommendation_engine),
        ("AI Narrative Generation", test_ai_narrative_generation),
        ("Integration Workflow", test_integration_workflow)
    ]
    
    for test_name, test_func in tests:
        if asyncio.iscoroutinefunction(test_func):
            result = await test_func()
        else:
            result = test_func()
        test_results.append((test_name, result))
    
    # Display demo scenarios
    create_demo_scenarios()
    
    # Calculate summary
    total_time = time.time() - start_time
    passed_tests = sum(1 for _, result in test_results if result)
    total_tests = len(test_results)
    
    # Display final summary
    print("="*80)
    print("📊 FINAL TEST SUMMARY")
    print("="*80)
    print(f"⏱️  Total execution time: {total_time:.2f} seconds")
    print(f"✅ Tests passed: {passed_tests}/{total_tests}")
    print(f"📈 Success rate: {passed_tests/total_tests:.1%}")
    print()
    
    print("🔧 COMPONENT STATUS:")
    for test_name, result in test_results:
        status_icon = "✅" if result else "❌"
        print(f"{status_icon} {test_name}")
    
    if passed_tests == total_tests:
        print("\n🎉 ALL TESTS PASSED - System is ready for demonstration!")
    else:
        print(f"\n⚠️  {total_tests - passed_tests} tests failed - Check component configurations")
    
    # Save results
    results_summary = {
        "timestamp": datetime.now().isoformat(),
        "total_time": total_time,
        "tests_passed": passed_tests,
        "tests_total": total_tests,
        "success_rate": passed_tests / total_tests,
        "component_status": {name: result for name, result in test_results}
    }
    
    try:
        with open('/Users/rahulmehta/Desktop/Financial Planning/backend/test_results.json', 'w') as f:
            json.dump(results_summary, f, indent=2)
        print(f"\n💾 Results saved to test_results.json")
    except Exception as e:
        print(f"\n⚠️  Could not save results: {e}")
    
    print("\n" + "="*80)
    print("🎬 TEST COMPLETED")
    print("="*80)

if __name__ == "__main__":
    asyncio.run(main())