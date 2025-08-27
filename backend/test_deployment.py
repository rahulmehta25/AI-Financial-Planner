#!/usr/bin/env python3
"""
Deployment Test Script for AI Financial Planning Backend
=======================================================

This script tests your deployed backend to ensure all endpoints are working correctly.
"""

import requests
import json
import sys
from datetime import datetime

def test_backend_deployment(base_url):
    """
    Comprehensive test of the deployed backend
    """
    
    print("🧪 Testing AI Financial Planning Backend")
    print("=" * 50)
    print(f"Backend URL: {base_url}")
    print(f"Test Time: {datetime.now().isoformat()}")
    print()
    
    test_results = {
        "health_check": False,
        "root_endpoint": False,
        "simulation": False,
        "monte_carlo": False,
        "api_docs": False
    }
    
    # Test 1: Health Check
    print("1️⃣  Testing Health Check...")
    try:
        response = requests.get(f"{base_url}/health", timeout=30)
        if response.status_code == 200:
            health_data = response.json()
            print(f"   ✅ Status: {response.status_code}")
            print(f"   📊 Response: {health_data.get('status', 'N/A')}")
            print(f"   🕐 Timestamp: {health_data.get('timestamp', 'N/A')}")
            test_results["health_check"] = True
        else:
            print(f"   ❌ Failed with status: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
    
    print()
    
    # Test 2: Root Endpoint
    print("2️⃣  Testing Root Endpoint...")
    try:
        response = requests.get(f"{base_url}/", timeout=30)
        if response.status_code == 200:
            root_data = response.json()
            print(f"   ✅ Status: {response.status_code}")
            print(f"   📝 Message: {root_data.get('message', 'N/A')}")
            print(f"   🔢 Version: {root_data.get('version', 'N/A')}")
            test_results["root_endpoint"] = True
        else:
            print(f"   ❌ Failed with status: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
    
    print()
    
    # Test 3: Simulation Endpoint
    print("3️⃣  Testing Simulation Endpoint...")
    test_simulation_data = {
        "age": 30,
        "income": 75000,
        "savings": 1500,
        "risk_tolerance": "moderate"
    }
    
    try:
        response = requests.post(
            f"{base_url}/simulate",
            json=test_simulation_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            sim_result = response.json()
            print(f"   ✅ Status: {response.status_code}")
            print(f"   📈 Success Probability: {sim_result.get('success_probability', 'N/A')}%")
            print(f"   💰 Median Balance: ${sim_result.get('median_balance', 'N/A'):,.0f}" if sim_result.get('median_balance') else "   💰 Median Balance: N/A")
            print(f"   🎯 Risk Level: {sim_result.get('risk_level', 'N/A')}")
            test_results["simulation"] = True
        else:
            print(f"   ❌ Failed with status: {response.status_code}")
            if response.text:
                print(f"   📄 Response: {response.text[:200]}...")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
    
    print()
    
    # Test 4: Monte Carlo Endpoint (Frontend expects this)
    print("4️⃣  Testing Monte Carlo Endpoint...")
    try:
        response = requests.post(
            f"{base_url}/api/v1/simulations/monte-carlo",
            json=test_simulation_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            mc_result = response.json()
            print(f"   ✅ Status: {response.status_code}")
            print(f"   📈 Success Probability: {mc_result.get('success_probability', 'N/A')}%")
            print(f"   💡 Recommendation: {mc_result.get('recommendation', 'N/A')[:50]}...")
            test_results["monte_carlo"] = True
        else:
            print(f"   ❌ Failed with status: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
    
    print()
    
    # Test 5: API Documentation
    print("5️⃣  Testing API Documentation...")
    try:
        response = requests.get(f"{base_url}/docs", timeout=30)
        if response.status_code == 200:
            print(f"   ✅ Status: {response.status_code}")
            print(f"   📚 API Docs Available: {base_url}/docs")
            test_results["api_docs"] = True
        else:
            print(f"   ❌ Failed with status: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
    
    print()
    
    # Summary
    print("📊 Test Summary")
    print("=" * 20)
    
    total_tests = len(test_results)
    passed_tests = sum(test_results.values())
    
    for test_name, passed in test_results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name.replace('_', ' ').title()}: {status}")
    
    print()
    print(f"Overall: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All tests passed! Your backend is ready for production.")
        print()
        print("🔗 Important URLs:")
        print(f"   🏥 Health Check: {base_url}/health")
        print(f"   📚 API Docs: {base_url}/docs")
        print(f"   🔄 Simulation: {base_url}/simulate")
        print()
        print("✅ Next Steps:")
        print("1. Update your frontend's API configuration with this backend URL")
        print("2. Redeploy your frontend to Vercel")
        print("3. Test the end-to-end connection")
    else:
        print("⚠️  Some tests failed. Check your deployment configuration.")
        return False
    
    return True


def main():
    """
    Main function to run deployment tests
    """
    
    if len(sys.argv) < 2:
        print("Usage: python test_deployment.py <backend_url>")
        print("Example: python test_deployment.py https://your-app.onrender.com")
        sys.exit(1)
    
    backend_url = sys.argv[1].rstrip('/')
    
    # Validate URL format
    if not backend_url.startswith(('http://', 'https://')):
        print("❌ Error: Please provide a complete URL with http:// or https://")
        sys.exit(1)
    
    try:
        success = test_backend_deployment(backend_url)
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()