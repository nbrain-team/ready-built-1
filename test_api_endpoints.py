#!/usr/bin/env python3
"""
Test salon API endpoints to see what data is being returned
"""

import requests
import json
from datetime import datetime

# API base URL
API_BASE_URL = "https://ready-built-1.onrender.com"

# Test credentials
EMAIL = "danny@nbrain.ai"
PASSWORD = "Tm0bile#88"  # Updated password from user

def login():
    """Login and get access token"""
    print("Logging in...")
    # The login endpoint expects form data, not JSON
    response = requests.post(
        f"{API_BASE_URL}/login",
        data={
            "username": EMAIL,  # OAuth2 expects 'username' field
            "password": PASSWORD
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Login successful")
        return data.get("access_token")
    else:
        print(f"✗ Login failed: {response.status_code} - {response.text}")
        return None

def test_dashboard_endpoints(token):
    """Test all dashboard endpoints"""
    headers = {"Authorization": f"Bearer {token}"}
    
    endpoints = [
        "/api/salon/dashboard/overview",
        "/api/salon/dashboard/revenue",
        "/api/salon/dashboard/staff-performance",
        "/api/salon/dashboard/top-services",
        "/api/salon/dashboard/recent-appointments",
        "/api/salon/dashboard/alerts"
    ]
    
    for endpoint in endpoints:
        print(f"\n{'='*60}")
        print(f"Testing: {endpoint}")
        print('='*60)
        
        try:
            response = requests.get(
                f"{API_BASE_URL}{endpoint}",
                headers=headers
            )
            
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"Response: {json.dumps(data, indent=2)}")
            else:
                print(f"Error: {response.text}")
                
        except Exception as e:
            print(f"Exception: {e}")

def test_raw_query(token):
    """Test raw database query through debug endpoint"""
    print("\n" + "="*60)
    print("Testing raw database query")
    print("="*60)
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(
            f"{API_BASE_URL}/api/salon/debug/check-data",
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
        else:
            print(f"Error: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"Exception: {e}")

def main():
    print("SALON API ENDPOINT TEST")
    print("="*60)
    print(f"Target: {API_BASE_URL}")
    print(f"Time: {datetime.now()}")
    
    # Login
    token = login()
    if not token:
        print("Failed to login. Exiting.")
        return
    
    # Test endpoints
    test_dashboard_endpoints(token)
    
    # Test raw query if debug endpoint exists
    test_raw_query(token)
    
    print("\n" + "="*60)
    print("TEST COMPLETE")

if __name__ == "__main__":
    main() 