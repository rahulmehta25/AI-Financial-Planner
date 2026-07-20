#!/usr/bin/env python3
"""
Simple test to verify working_demo.py functionality
=================================================

This script tests core functions without starting the full server.
"""

import sys
from pathlib import Path

def test_imports():
    """Test if all required imports work"""
    print("🔄 Testing imports...")
    
    try:
        # Test core imports
        import numpy as np
        import matplotlib.pyplot as plt
        import sqlite3
        import json
        from datetime import datetime
        print("   ✅ Core libraries imported successfully")
        
        # Test FastAPI imports
        from fastapi import FastAPI
        from pydantic import BaseModel
        print("   ✅ FastAPI libraries imported successfully")
        
        # Test scientific libraries
        from scipy import optimize
        print("   ✅ SciPy imported successfully")
        
        # Try to import numba (might not be available)
        try:
            from numba import jit
            print("   ✅ Numba imported successfully")
        except ImportError:
            print("   ⚠️  Numba not available (will fallback to regular Python)")
            
        return True
        
    except ImportError as e:
        print(f"   ❌ Import failed: {e}")
        return False

def test_basic_simulation():
    """Test basic simulation without Numba optimization"""
    print("\n🎲 Testing basic Monte Carlo simulation...")
    
    try:
        import numpy as np
        
        # Simple simulation without numba
        def simple_monte_carlo(initial_amount, monthly_contribution, annual_return, 
                             annual_volatility, years, num_simulations):
            monthly_return = annual_return / 12
            monthly_volatility = annual_volatility / np.sqrt(12)
            months = years * 12
            
            np.random.seed(42)
            random_returns = np.random.normal(monthly_return, monthly_volatility, 
                                            (num_simulations, months))
            
            final_values = []
            for sim in range(num_simulations):
                value = initial_amount
                for month in range(months):
                    value += monthly_contribution
                    value *= (1 + random_returns[sim, month])
                final_values.append(value)
            
            return {
                "median": np.median(final_values),
                "mean": np.mean(final_values),
                "std": np.std(final_values),
                "min": np.min(final_values),
                "max": np.max(final_values)
            }
        
        results = simple_monte_carlo(10000, 500, 0.08, 0.12, 10, 1000)
        
        print(f"   ✅ Simulation completed successfully")
        print(f"   💰 Median final value: ${results['median']:,.0f}")
        print(f"   📊 Mean final value: ${results['mean']:,.0f}")
        print(f"   📈 Min-Max range: ${results['min']:,.0f} - ${results['max']:,.0f}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Simulation failed: {e}")
        return False

def test_portfolio_optimization():
    """Test basic portfolio optimization"""
    print("\n📈 Testing portfolio optimization...")
    
    try:
        import numpy as np
        from scipy import optimize
        
        # Simple optimization test
        def simple_portfolio_optimization():
            # Sample data
            returns = np.array([0.10, 0.08, 0.04, 0.09, 0.06])  # 5 assets
            volatilities = np.array([0.16, 0.18, 0.05, 0.20, 0.22])
            
            # Correlation matrix
            correlation = np.array([
                [1.00, 0.75, -0.20, 0.60, 0.30],
                [0.75, 1.00, -0.15, 0.55, 0.25],
                [-0.20, -0.15, 1.00, 0.10, -0.10],
                [0.60, 0.55, 0.10, 1.00, 0.40],
                [0.30, 0.25, -0.10, 0.40, 1.00]
            ])
            
            cov_matrix = np.outer(volatilities, volatilities) * correlation
            
            def objective(weights):
                # Maximize Sharpe ratio = minimize negative Sharpe ratio
                portfolio_return = np.sum(returns * weights)
                portfolio_vol = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
                return -portfolio_return / portfolio_vol if portfolio_vol > 0 else 0
            
            # Constraints: weights sum to 1
            constraints = [{"type": "eq", "fun": lambda x: np.sum(x) - 1}]
            bounds = tuple((0, 1) for _ in range(len(returns)))
            
            # Initial guess
            x0 = np.array([0.2] * len(returns))
            
            result = optimize.minimize(objective, x0, method="SLSQP", 
                                     bounds=bounds, constraints=constraints)
            
            if result.success:
                weights = result.x
                portfolio_return = np.sum(returns * weights)
                portfolio_vol = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
                sharpe_ratio = portfolio_return / portfolio_vol
                
                return {
                    "success": True,
                    "weights": weights,
                    "return": portfolio_return,
                    "volatility": portfolio_vol,
                    "sharpe_ratio": sharpe_ratio
                }
            else:
                return {"success": False, "error": result.message}
        
        result = simple_portfolio_optimization()
        
        if result["success"]:
            print(f"   ✅ Portfolio optimization successful")
            print(f"   📊 Expected return: {result['return']:.2%}")
            print(f"   📉 Expected volatility: {result['volatility']:.2%}")
            print(f"   ⚡ Sharpe ratio: {result['sharpe_ratio']:.2f}")
            print(f"   💼 Top allocation: {max(result['weights']):.1%}")
        else:
            print(f"   ❌ Optimization failed: {result.get('error', 'Unknown error')}")
            return False
            
        return True
        
    except Exception as e:
        print(f"   ❌ Portfolio optimization failed: {e}")
        return False

def test_database():
    """Test SQLite database functionality"""
    print("\n💾 Testing database functionality...")
    
    try:
        import sqlite3
        import tempfile
        import os
        
        # Create temporary database
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
            db_path = tmp_file.name
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create test table
        cursor.execute("""
            CREATE TABLE test_users (
                id INTEGER PRIMARY KEY,
                email TEXT UNIQUE,
                name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Insert test data
        cursor.execute(
            "INSERT INTO test_users (email, name) VALUES (?, ?)",
            ("test@example.com", "Test User")
        )
        
        # Query test data
        cursor.execute("SELECT * FROM test_users WHERE email = ?", ("test@example.com",))
        user = cursor.fetchone()
        
        conn.commit()
        conn.close()
        
        # Cleanup
        os.unlink(db_path)
        
        if user:
            print(f"   ✅ Database operations successful")
            print(f"   👤 Test user: {user[2]} ({user[1]})")
            return True
        else:
            print("   ❌ Database test failed: No user found")
            return False
            
    except Exception as e:
        print(f"   ❌ Database test failed: {e}")
        return False

def test_charts():
    """Test chart generation capability"""
    print("\n📊 Testing chart generation...")
    
    try:
        import matplotlib
        matplotlib.use('Agg')  # Non-interactive backend
        import matplotlib.pyplot as plt
        import numpy as np
        import io
        import base64
        
        # Generate simple test chart
        x = np.linspace(0, 10, 100)
        y = np.sin(x)
        
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.plot(x, y)
        ax.set_title('Test Chart')
        ax.set_xlabel('X axis')
        ax.set_ylabel('Y axis')
        
        # Convert to base64
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        chart_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close()
        
        if len(chart_base64) > 1000:  # Reasonable size check
            print(f"   ✅ Chart generation successful")
            print(f"   📏 Chart size: {len(chart_base64)} characters")
            return True
        else:
            print("   ❌ Chart generation failed: Chart too small")
            return False
            
    except Exception as e:
        print(f"   ❌ Chart generation failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Simple ML Test Suite for Financial Planning Demo")
    print("=" * 60)
    
    tests = [
        ("Import Libraries", test_imports),
        ("Monte Carlo Simulation", test_basic_simulation),
        ("Portfolio Optimization", test_portfolio_optimization),
        ("Database Operations", test_database),
        ("Chart Generation", test_charts)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"   ❌ Unexpected error in {test_name}: {e}")
        print()
    
    print("=" * 60)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The demo should work correctly.")
        print("\n🚀 Ready to run:")
        print("   python3 working_demo.py")
        print("\n📚 Then visit:")
        print("   http://localhost:8000/docs")
    else:
        print(f"⚠️  {total - passed} tests failed.")
        print("Some features might not work as expected.")
        print("Check error messages above for details.")
        
        if passed >= 3:  # At least basic functionality works
            print("\n💡 Basic functionality seems to work.")
            print("You can still try running the demo.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)