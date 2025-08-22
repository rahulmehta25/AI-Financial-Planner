#!/usr/bin/env python3
"""
ML Demo Verification Script
===========================

Quick verification that all ML demo components work correctly.
"""

import sys
import time
import numpy as np
from ml_simulation_demo import (
    MarketAssumptions, PortfolioOptimizer, MonteCarloSimulator, 
    RiskProfiler, VisualizationEngine, create_example_scenarios,
    print_success, print_info, print_header
)

def verify_market_assumptions():
    """Test market assumptions"""
    market = MarketAssumptions()
    assert len(market.asset_classes) == 8
    assert market.correlations.shape == (8, 8)
    assert np.allclose(np.diag(market.correlations), 1.0)  # Diagonal should be 1
    print_success("✓ Market assumptions verified")

def verify_portfolio_optimizer():
    """Test portfolio optimization"""
    market = MarketAssumptions()
    optimizer = PortfolioOptimizer(market)
    
    # Test basic portfolio stats
    equal_weights = np.array([1/8] * 8)
    ret, vol, sharpe = optimizer.portfolio_stats(equal_weights)
    assert 0.05 < ret < 0.12  # Reasonable return range
    assert 0.05 < vol < 0.20  # Reasonable volatility range
    assert -1 < sharpe < 2    # Reasonable Sharpe ratio range
    
    # Test efficient frontier
    frontier_returns, frontier_vols, _ = optimizer.efficient_frontier(10)
    assert len(frontier_returns) > 5  # Should have some valid portfolios
    assert len(frontier_vols) == len(frontier_returns)
    
    print_success("✓ Portfolio optimizer verified")

def verify_monte_carlo():
    """Test Monte Carlo simulation"""
    market = MarketAssumptions()
    simulator = MonteCarloSimulator(market)
    
    # Small test simulation
    weights = np.array([0.6, 0.2, 0.1, 0.05, 0.03, 0.01, 0.005, 0.005])
    paths = simulator.simulate_portfolio_paths(
        weights=weights,
        initial_value=10000,
        years=5,
        annual_contribution=1000,
        n_simulations=100
    )
    
    assert paths.shape == (100, 5*12 + 1)  # 100 sims, 5 years monthly + initial
    assert np.all(paths[:, 0] == 10000)    # Initial value correct
    assert np.all(paths >= 0)              # No negative values
    
    print_success("✓ Monte Carlo simulator verified")

def verify_risk_profiler():
    """Test risk profiling"""
    profiler = RiskProfiler()
    
    # Generate test data
    investor_data = profiler.create_synthetic_investors(100)
    assert len(investor_data) == 100
    assert len(investor_data.columns) == 8  # 8 features
    
    # Test clustering
    clusters, features_pca = profiler.fit_risk_clusters(investor_data)
    assert len(clusters) == 100
    assert len(np.unique(clusters)) <= 3  # Should have 3 clusters max
    assert features_pca.shape == (100, 2)  # PCA to 2 dimensions
    
    # Test allocations
    allocations = profiler.get_risk_profile_allocations()
    assert len(allocations) == 3
    for profile, weights in allocations.items():
        assert len(weights) == 8
        assert np.isclose(np.sum(weights), 1.0, rtol=1e-3)
    
    print_success("✓ Risk profiler verified")

def verify_scenarios():
    """Test example scenarios"""
    scenarios = create_example_scenarios()
    assert len(scenarios) == 3
    
    required_keys = ['description', 'initial_investment', 'annual_contribution',
                    'years_to_retirement', 'retirement_years', 'target_allocation']
    
    for scenario_name, scenario in scenarios.items():
        for key in required_keys:
            assert key in scenario, f"Missing key {key} in scenario {scenario_name}"
        assert scenario['initial_investment'] > 0
        assert scenario['annual_contribution'] > 0
        assert scenario['years_to_retirement'] > 0
        assert scenario['retirement_years'] > 0
    
    print_success("✓ Example scenarios verified")

def verify_integration():
    """Test end-to-end integration"""
    print_info("Running mini end-to-end test...")
    
    # Initialize components
    market = MarketAssumptions()
    optimizer = PortfolioOptimizer(market)
    simulator = MonteCarloSimulator(market)
    profiler = RiskProfiler()
    
    # Get risk profile allocation
    allocations = profiler.get_risk_profile_allocations()
    balanced_weights = allocations['Balanced']
    
    # Run small simulation
    paths = simulator.simulate_portfolio_paths(
        weights=balanced_weights,
        initial_value=50000,
        years=10,
        annual_contribution=10000,
        n_simulations=500
    )
    
    # Run retirement simulation
    retirement_results = simulator.retirement_simulation(
        portfolio_paths=paths,
        retirement_years=20,
        withdrawal_rate=0.04
    )
    
    # Validate results
    assert 'success_rate' in retirement_results
    assert 'final_balances' in retirement_results
    assert len(retirement_results['final_balances']) == 500
    assert 0 <= retirement_results['success_rate'] <= 1
    
    print_success("✓ End-to-end integration verified")

def main():
    """Run all verification tests"""
    print_header("🔍 ML DEMO VERIFICATION 🔍")
    
    start_time = time.time()
    
    try:
        verify_market_assumptions()
        verify_portfolio_optimizer() 
        verify_monte_carlo()
        verify_risk_profiler()
        verify_scenarios()
        verify_integration()
        
        total_time = time.time() - start_time
        
        print_header("✅ ALL TESTS PASSED! ✅")
        print_success(f"Verification completed in {total_time:.2f} seconds")
        print_info("The ML demo is ready for production use!")
        
        return True
        
    except Exception as e:
        print_header("❌ VERIFICATION FAILED ❌")
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)