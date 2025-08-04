#!/usr/bin/env python3
"""
Script to upload Blazer salon data files to nBrain platform
"""

import os
import sys
import requests
import json
from datetime import datetime

# Configuration
API_BASE_URL = os.getenv('API_URL', 'https://nbrain-backend.onrender.com')
API_TOKEN = os.getenv('API_TOKEN', '')  # You'll need to set this

# File mappings - ALL data files
FILES_TO_UPLOAD = {
    'staff': {
        'file': 'blazer/Emp List Active as of 1.1.24-7.31.25.csv',
        'endpoint': '/upload/staff',
        'description': 'Employee/Staff Data'
    },
    'performance_2024': {
        'file': 'blazer/Staff Performance_Utilization - All Salons 2024.csv',
        'endpoint': '/upload/performance',
        'description': '2024 Performance Data'
    },
    'performance_2025': {
        'file': 'blazer/Staff Performance_Utilization - All Salons 2025 072725.csv',
        'endpoint': '/upload/performance',
        'description': '2025 Performance Data'
    },
    'transactions_2024': {
        'file': 'blazer/Detailed Line Item 2024.csv',
        'endpoint': '/upload/transactions',
        'description': '2024 Transaction Details'
    },
    'transactions_2025': {
        'file': 'blazer/Detailed Line Item 2025 071825.csv',
        'endpoint': '/upload/transactions',
        'description': '2025 Transaction Details'
    },
    'timeclock_2024': {
        'file': 'blazer/Time Clock Data 2024.csv',
        'endpoint': '/upload/timeclock',
        'description': '2024 Time Clock Data'
    },
    'timeclock_2025': {
        'file': 'blazer/Time Clock Data 2025 071825.csv',
        'endpoint': '/upload/timeclock',
        'description': '2025 Time Clock Data'
    },
    'schedules': {
        'file': 'blazer/Schedule Records.csv',
        'endpoint': '/upload/schedules',
        'description': 'Schedule Records'
    }
}

def login_and_get_token():
    """Login to get authentication token"""
    # You'll need to provide credentials
    username = input("Enter your username/email: ")
    password = input("Enter your password: ")
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/auth/login",
            data={
                "username": username,
                "password": password
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            return data.get('access_token')
        else:
            print(f"Login failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Login error: {e}")
        return None

def upload_file(file_path, endpoint, token, description):
    """Upload a single file to the specified endpoint"""
    if not os.path.exists(file_path):
        print(f"⚠️  File not found: {file_path}")
        return False
    
    # Get file size
    file_size = os.path.getsize(file_path) / (1024 * 1024)  # Size in MB
    print(f"   File size: {file_size:.1f} MB")
    
    if file_size > 50:
        print(f"   ⚠️  Large file - upload may take a while...")
    
    try:
        with open(file_path, 'rb') as f:
            files = {'file': (os.path.basename(file_path), f, 'text/csv')}
            headers = {'Authorization': f'Bearer {token}'}
            
            print(f"   Uploading to {endpoint}...")
            response = requests.post(
                f"{API_BASE_URL}/api/salon{endpoint}",
                files=files,
                headers=headers,
                timeout=300  # 5 minute timeout for large files
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✓ Success!")
                if 'records_created' in result:
                    print(f"     - Records created: {result['records_created']}")
                if 'records_skipped' in result:
                    print(f"     - Records skipped: {result['records_skipped']}")
                if 'records_updated' in result:
                    print(f"     - Records updated: {result['records_updated']}")
                return True
            else:
                print(f"   ✗ Failed!")
                print(f"     - Status: {response.status_code}")
                print(f"     - Error: {response.text}")
                return False
                
    except requests.exceptions.Timeout:
        print(f"   ✗ Upload timed out (file too large)")
        return False
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False

def main():
    print("=== Salon Data Upload Script (ALL DATA) ===")
    print(f"API URL: {API_BASE_URL}")
    print()
    
    # Get authentication token
    token = API_TOKEN
    if not token:
        print("No API_TOKEN found. Please login:")
        token = login_and_get_token()
        if not token:
            print("Failed to authenticate. Exiting.")
            sys.exit(1)
    
    print("\nStarting data upload...")
    print("=" * 60)
    
    # Track results
    successful_uploads = []
    failed_uploads = []
    
    # Upload in order: staff first, then performance, then transactions, etc.
    upload_order = [
        'staff',
        'performance_2024',
        'performance_2025',
        'transactions_2024',
        'transactions_2025',
        'timeclock_2024',
        'timeclock_2025',
        'schedules'
    ]
    
    for idx, key in enumerate(upload_order, 1):
        upload_info = FILES_TO_UPLOAD[key]
        print(f"\n{idx}. {upload_info['description']}:")
        
        if upload_file(
            upload_info['file'],
            upload_info['endpoint'],
            token,
            upload_info['description']
        ):
            successful_uploads.append(upload_info['description'])
        else:
            failed_uploads.append(upload_info['description'])
    
    # Summary
    print("\n" + "=" * 60)
    print("UPLOAD SUMMARY:")
    print(f"✓ Successful: {len(successful_uploads)}")
    for item in successful_uploads:
        print(f"  - {item}")
    
    if failed_uploads:
        print(f"\n✗ Failed: {len(failed_uploads)}")
        for item in failed_uploads:
            print(f"  - {item}")
    
    print("\n" + "=" * 60)
    print("Upload process completed!")
    
    if len(successful_uploads) == len(FILES_TO_UPLOAD):
        print("\n🎉 All data uploaded successfully!")
        print("\nYou can now:")
        print("- View the complete dashboard at: https://nbrain-frontend.onrender.com")
        print("- Use the AI Assistant to analyze all your salon data")
        print("- Access advanced analytics including:")
        print("  • Revenue analysis by service type")
        print("  • Staff productivity vs actual hours worked")
        print("  • Schedule optimization recommendations")
        print("  • Client retention patterns")
    else:
        print("\n⚠️  Some uploads failed. Please check the errors above.")

if __name__ == "__main__":
    main() 