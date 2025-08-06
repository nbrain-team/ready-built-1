#!/usr/bin/env python3
"""
Test dashboard endpoints directly to verify data
"""

import requests
import json
from datetime import datetime

# Base URL for the API
BASE_URL = "https://ready-built-1.onrender.com/api/salon"

def test_endpoints():
    """Test all dashboard endpoints"""
    
    print("=" * 60)
    print("TESTING DASHBOARD ENDPOINTS")
    print("=" * 60)
    
    endpoints = [
        ("/dashboard/overview", "Dashboard Overview"),
        ("/dashboard/performance-trends", "Performance Trends"),
        ("/dashboard/top-performers?metric=sales", "Top Performers by Sales"),
        ("/analytics/service-breakdown", "Service Breakdown"),
        ("/analytics/client-insights", "Client Insights"),
        ("/transactions/search?limit=5", "Transaction Search"),
        ("/analytics/daily-summary", "Daily Summary")
    ]
    
    for endpoint, name in endpoints:
        print(f"\n📊 Testing: {name}")
        print(f"   Endpoint: {endpoint}")
        
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Success! Response:")
                
                # Pretty print the response (limited for readability)
                if isinstance(data, dict):
                    for key, value in list(data.items())[:5]:
                        if isinstance(value, (int, float)):
                            if key in ['total_revenue', 'avg_daily_revenue', 'net_sales']:
                                print(f"      {key}: ${value:,.2f}")
                            else:
                                print(f"      {key}: {value:,}" if isinstance(value, int) else f"      {key}: {value}")
                        elif isinstance(value, list) and len(value) > 0:
                            print(f"      {key}: {len(value)} items")
                        else:
                            print(f"      {key}: {value}")
                elif isinstance(data, list):
                    print(f"      Returned {len(data)} items")
                    if data:
                        print(f"      First item: {json.dumps(data[0], indent=2)[:200]}...")
            else:
                print(f"   ❌ Error: Status {response.status_code}")
                print(f"      Response: {response.text[:200]}")
                
        except requests.exceptions.Timeout:
            print(f"   ⏱️  Timeout - endpoint may be slow")
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print("✅ TESTING COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    test_endpoints() 