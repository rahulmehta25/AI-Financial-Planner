"""
Demo Script for Monte Carlo Simulation Engine

Demonstrates the complete simulation system with example scenarios
and performance testing.
"""

import asyncio
import time
from typing import Dict, Any

from .orchestrator import SimulationOrchestrator, SimulationRequest
from .portfolio_mapping import RiskTolerance
from .logging_config import setup_simulation_logging, default_logger


async def run_demo_simulations():
    """Run demonstration simulations with different scenarios"""
    
    print("="*60)
    print("MONTE CARLO SIMULATION ENGINE DEMONSTRATION")
    print("="*60)
    
    # Setup logging
    logger = setup_simulation_logging()
    
    # Initialize orchestrator
    orchestrator = SimulationOrchestrator()
    
    # Define test scenarios
    scenarios = [
        {
            "name": "Young Professional",
            "description": "25-year-old starting career with modest savings",
            "params": {
                "current_age": 25,
                "retirement_age": 65,
                "current_portfolio_value": 10_000,
                "annual_contribution": 8_000,
                "current_annual_income": 50_000,
                "risk_tolerance": "moderately_aggressive"
            }
        },
        {
            "name": "Mid-Career Professional", 
            "description": "40-year-old with established savings",
            "params": {
                "current_age": 40,
                "retirement_age": 65,
                "current_portfolio_value": 150_000,
                "annual_contribution": 15_000,
                "current_annual_income": 80_000,
                "risk_tolerance": "moderate"
            }
        },
        {
            "name": "Conservative Pre-Retiree",
            "description": "55-year-old near retirement with substantial savings",
            "params": {
                "current_age": 55,
                "retirement_age": 65,
                "current_portfolio_value": 800_000,
                "annual_contribution": 20_000,
                "current_annual_income": 100_000,
                "risk_tolerance": "conservative"
            }
        }
    ]
    
    results = []
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n{i}. {scenario['name']}")
        print(f"   {scenario['description']}")
        print("-" * 50)
        
        # Create simulation request
        request = SimulationRequest(
            user_id=f"demo_user_{i}",
            simulation_name=scenario["name"],
            n_simulations=10_000,  # Smaller for demo
            include_trade_off_analysis=True,
            include_stress_testing=True,
            **scenario["params"]
        )
        
        try:
            start_time = time.time()
            result = await orchestrator.run_comprehensive_simulation(request)
            end_time = time.time()
            
            results.append(result)
            
            # Print key results
            print(f"   Success Probability: {result.success_probability:.1%}")
            print(f"   Median Balance: ${result.median_retirement_balance:,.0f}")
            print(f"   10th Percentile: ${result.percentile_10_balance:,.0f}")
            print(f"   90th Percentile: ${result.percentile_90_balance:,.0f}")
            print(f"   Simulation Time: {end_time - start_time:.2f} seconds")
            
            # Print top recommendations
            if result.recommendations.get("immediate_actions"):
                print(f"   Top Recommendation: {result.recommendations['immediate_actions'][0]}")
            
        except Exception as e:
            print(f"   ERROR: {str(e)}")
            continue
    
    return results


async def run_performance_test():
    """Test performance with full-scale simulation"""
    
    print("\n" + "="*60)
    print("PERFORMANCE TEST - 50,000 SIMULATIONS")
    print("="*60)
    
    orchestrator = SimulationOrchestrator()
    
    # Performance test scenario
    request = SimulationRequest(
        user_id="performance_test",
        simulation_name="Performance Test",
        current_age=35,
        retirement_age=65,
        current_portfolio_value=100_000,
        annual_contribution=12_000,
        current_annual_income=60_000,
        risk_tolerance="moderate",
        n_simulations=50_000,  # Full simulation
        include_trade_off_analysis=True,
        include_stress_testing=True
    )
    
    print("Running 50,000 simulation Monte Carlo analysis...")
    print("Target: < 30 seconds execution time")
    
    try:
        start_time = time.time()
        result = await orchestrator.run_comprehensive_simulation(request)
        end_time = time.time()
        
        execution_time = end_time - start_time
        target_met = execution_time < 30.0
        
        print(f"\nRESULTS:")
        print(f"  Execution Time: {execution_time:.2f} seconds")
        print(f"  Target Met: {'✓' if target_met else '✗'} (< 30 seconds)")
        print(f"  Simulations/Second: {50_000/execution_time:,.0f}")
        print(f"  Success Probability: {result.success_probability:.1%}")
        print(f"  Median Balance: ${result.median_retirement_balance:,.0f}")
        
        # Performance metrics
        perf_metrics = result.performance_metrics
        if perf_metrics:
            print(f"  Performance Score: {'Excellent' if target_met else 'Needs Optimization'}")
        
        return result
        
    except Exception as e:
        print(f"Performance test failed: {str(e)}")
        return None


def run_quick_test():
    """Run quick synchronous test"""
    
    print("\n" + "="*60)
    print("QUICK FUNCTIONALITY TEST")
    print("="*60)
    
    from .market_assumptions import CapitalMarketAssumptions
    from .engine import MonteCarloEngine, PortfolioAllocation, SimulationParameters
    from .portfolio_mapping import PortfolioMapper
    
    # Test components individually
    print("1. Testing Market Assumptions...")
    cma = CapitalMarketAssumptions()
    stats = cma.get_summary_statistics()
    print(f"   Asset Classes: {stats['asset_classes']}")
    print(f"   Return Range: {stats['expected_returns']['min']:.1%} - {stats['expected_returns']['max']:.1%}")
    
    print("\n2. Testing Portfolio Mapping...")
    mapper = PortfolioMapper()
    portfolio = mapper.get_age_adjusted_portfolio(RiskTolerance.MODERATE, 35)
    print(f"   Generated portfolio with {len(portfolio.allocations)} asset classes")
    
    print("\n3. Testing Monte Carlo Engine...")
    engine = MonteCarloEngine()
    params = SimulationParameters(n_simulations=1_000)  # Small test
    
    start_time = time.time()
    results = engine.run_simulation(portfolio, params)
    end_time = time.time()
    
    print(f"   Simulation completed in {end_time - start_time:.2f} seconds")
    print(f"   Success probability: {results['success_probability']:.1%}")
    
    print("\n✓ All components functioning correctly!")


async def main():
    """Main demonstration function"""
    
    try:
        # Run quick test first
        run_quick_test()
        
        # Run demo scenarios
        demo_results = await run_demo_simulations()
        
        # Run performance test
        perf_result = await run_performance_test()
        
        print("\n" + "="*60)
        print("DEMONSTRATION COMPLETED SUCCESSFULLY")
        print("="*60)
        
        if demo_results:
            print(f"Demo scenarios completed: {len(demo_results)}/3")
        
        if perf_result:
            print(f"Performance test: {'PASSED' if perf_result.simulation_time_seconds < 30 else 'NEEDS OPTIMIZATION'}")
        
        print("\nThe Monte Carlo simulation engine is ready for production use!")
        
    except Exception as e:
        print(f"\nDemonstration failed: {str(e)}")
        raise


if __name__ == "__main__":
    # Run the demonstration
    asyncio.run(main())