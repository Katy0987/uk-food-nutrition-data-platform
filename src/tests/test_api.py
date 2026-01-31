#!/usr/bin/env python3
"""
Quick test script to verify API endpoints are working.
Run this after starting the API to test all major functionality.
"""

import requests
import json
import sys
from typing import Dict, Any

BASE_URL = "http://localhost:8000"
API_PREFIX = "/api/v1"


def test_endpoint(name: str, method: str, url: str, params: Dict = None) -> bool:
    """Test a single endpoint."""
    try:
        full_url = f"{BASE_URL}{url}"
        print(f"\n{'=' * 60}")
        print(f"Testing: {name}")
        print(f"URL: {method} {full_url}")
        if params:
            print(f"Params: {params}")
        
        if method == "GET":
            response = requests.get(full_url, params=params, timeout=10)
        elif method == "POST":
            response = requests.post(full_url, json=params, timeout=10)
        else:
            print(f"❌ Unsupported method: {method}")
            return False
        
        print(f"Status: {response.status_code}")
        
        if response.status_code < 400:
            data = response.json()
            print(f"Success: {data.get('success', 'N/A')}")
            
            # Show response time if available
            if 'meta' in data and 'response_time_ms' in data['meta']:
                print(f"Response Time: {data['meta']['response_time_ms']}ms")
            
            # Show data summary
            if 'data' in data:
                if isinstance(data['data'], list):
                    print(f"Results Count: {len(data['data'])}")
                elif isinstance(data['data'], dict):
                    print(f"Data Keys: {', '.join(list(data['data'].keys())[:5])}")
            
            print("✅ PASSED")
            return True
        else:
            print(f"❌ FAILED: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"❌ FAILED: Cannot connect to {BASE_URL}")
        print("   Make sure the API is running: uvicorn api.main:app --reload")
        return False
    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("EcoAPI Quick Test Suite")
    print("=" * 60)
    
    tests = [
        # Health endpoints
        ("Root Endpoint", "GET", "/"),
        ("Health Check", "GET", "/health"),
        ("System Status", "GET", f"{API_PREFIX}/status"),
        
        # Establishment endpoints
        ("Search Establishments", "GET", f"{API_PREFIX}/establishments/search", 
         {"limit": 5}),
        ("Search by Postcode", "GET", f"{API_PREFIX}/establishments/search", 
         {"postcode": "SW1A", "limit": 3}),
        ("Nearby Establishments", "GET", f"{API_PREFIX}/establishments/nearby", 
         {"lat": 51.5074, "lon": -0.1278, "radius": 1, "limit": 3}),
        
        # Product endpoints
        ("Search Products", "GET", f"{API_PREFIX}/products/search", 
         {"limit": 5}),
        ("Search Products by Category", "GET", f"{API_PREFIX}/products/search", 
         {"category": "beverages", "limit": 3}),
        ("Top Eco Products", "GET", f"{API_PREFIX}/products/categories/beverages/top-eco", 
         {"limit": 5}),
        
        # Intelligence endpoints
        ("District Intelligence", "GET", f"{API_PREFIX}/intelligence/district/SW1A1AA"),
        ("Category Insights", "GET", f"{API_PREFIX}/intelligence/category/beverages/insights"),
        
        # Admin endpoints
        ("System Metrics", "GET", f"{API_PREFIX}/metrics"),
        ("Detailed Health", "GET", f"{API_PREFIX}/health/detailed"),
        ("Summary Statistics", "GET", f"{API_PREFIX}/stats/summary"),
    ]
    
    results = []
    for test in tests:
        name, method, url = test[0], test[1], test[2]
        params = test[3] if len(test) > 3 else None
        passed = test_endpoint(name, method, url, params)
        results.append((name, passed))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status:10} | {name}")
    
    print("=" * 60)
    print(f"Results: {passed_count}/{total_count} tests passed")
    print("=" * 60)
    
    if passed_count == total_count:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total_count - passed_count} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())