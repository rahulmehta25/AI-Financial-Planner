#!/usr/bin/env python3
"""
Test script to validate CLI demo structure without external dependencies
"""

import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_core_imports():
    """Test core application imports"""
    try:
        from app.schemas.financial_planning import PlanInputModel
        from app.simulations.engine import MonteCarloEngine, PortfolioAllocation, SimulationParameters
        from app.simulations.market_assumptions import CapitalMarketAssumptions
        print("✅ Core application imports successful")
        return True
    except ImportError as e:
        print(f"❌ Core import failed: {e}")
        return False

def test_cli_structure():
    """Test CLI structure without Rich imports"""
    try:
        # Test demo profile structure
        demo_profiles = {
            "Conservative Couple": {
                "age": 35,
                "target_retirement_age": 65,
                "marital_status": "married",
                "current_savings_balance": 125000.0,
                "annual_savings_rate_percentage": 15.0,
                "income_level": 85000.0,
                "debt_balance": 25000.0,
                "debt_interest_rate_percentage": 4.5,
                "account_buckets_taxable": 30.0,
                "account_buckets_401k_ira": 50.0,
                "account_buckets_roth": 20.0,
                "risk_preference": "conservative",
                "desired_retirement_spending_per_year": 60000.0,
                "plan_name": "Conservative Retirement Plan",
                "notes": "Focus on capital preservation with steady growth"
            }
        }
        
        # Validate profile structure
        profile = demo_profiles["Conservative Couple"]
        PlanInputModel(**profile)
        print("✅ Demo profile structure valid")
        
        # Test simulation parameters
        params = SimulationParameters(
            n_simulations=1000,  # Small test
            years_to_retirement=profile["target_retirement_age"] - profile["age"],
            retirement_years=25,
            initial_portfolio_value=profile["current_savings_balance"],
            annual_contribution=profile["income_level"] * (profile["annual_savings_rate_percentage"] / 100),
        )
        print("✅ Simulation parameters created successfully")
        
        # Test portfolio allocation
        allocation = PortfolioAllocation(allocations={"stocks": 0.30, "bonds": 0.60, "cash": 0.10})
        print("✅ Portfolio allocation created successfully")
        
        # Test Monte Carlo engine
        engine = MonteCarloEngine()
        print("✅ Monte Carlo engine initialized successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ CLI structure test failed: {e}")
        return False

def test_basic_simulation():
    """Test basic simulation functionality"""
    try:
        # Initialize engine
        engine = MonteCarloEngine()
        
        # Create simple parameters
        params = SimulationParameters(
            n_simulations=100,  # Very small for testing
            years_to_retirement=30,
            retirement_years=25,
            initial_portfolio_value=100000.0,
            annual_contribution=12000.0,
        )
        
        # Create allocation
        allocation = PortfolioAllocation(allocations={"stocks": 0.60, "bonds": 0.30, "cash": 0.10})
        
        # Run simulation
        results = engine.run_simulation(allocation, params)
        
        # Check results structure
        required_keys = ["success_probability", "retirement_balance_stats", "simulation_metadata"]
        for key in required_keys:
            if key not in results:
                raise ValueError(f"Missing required key: {key}")
        
        print(f"✅ Basic simulation completed successfully")
        print(f"   Success probability: {results['success_probability']:.1%}")
        print(f"   Median balance: ${results['retirement_balance_stats']['median']:,.0f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Basic simulation failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing CLI Demo Structure")
    print("=" * 40)
    
    tests = [
        ("Core Imports", test_core_imports),
        ("CLI Structure", test_cli_structure),
        ("Basic Simulation", test_basic_simulation),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 Testing {test_name}...")
        if test_func():
            passed += 1
        else:
            print(f"   Test failed, continuing...")
    
    print("\n" + "=" * 40)
    print(f"📊 Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All tests passed! CLI demo structure is valid.")
        return 0
    else:
        print("⚠️  Some tests failed. Check error messages above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())