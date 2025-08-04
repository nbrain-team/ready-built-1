#!/usr/bin/env python3
"""
Direct upload script for Render deployment
Run this locally to upload all salon data to your deployed instance
"""

import os
import sys
import requests
import json
import time
from datetime import datetime
import getpass

# Configuration
API_BASE_URL = 'https://ready-built-1.onrender.com'

# File mappings - ALL data files
FILES_TO_UPLOAD = {
    'staff': {
        'file': 'blazer/Emp List Active as of 1.1.24-7.31.25.csv',
        'endpoint': '/upload/staff',
        'description': 'Employee/Staff Data',
        'order': 1
    },
    'performance_2024': {
        'file': 'blazer/Staff Performance_Utilization - All Salons 2024.csv',
        'endpoint': '/upload/performance',
        'description': '2024 Performance Data',
        'order': 2
    },
    'performance_2025': {
        'file': 'blazer/Staff Performance_Utilization - All Salons 2025 072725.csv',
        'endpoint': '/upload/performance',
        'description': '2025 Performance Data',
        'order': 3
    },
    'transactions_2024': {
        'file': 'blazer/Detailed Line Item 2024.csv',
        'endpoint': '/upload/transactions',
        'description': '2024 Transaction Details',
        'order': 4
    },
    'transactions_2025': {
        'file': 'blazer/Detailed Line Item 2025 071825.csv',
        'endpoint': '/upload/transactions',
        'description': '2025 Transaction Details',
        'order': 5
    },
    'timeclock_2024': {
        'file': 'blazer/Time Clock Data 2024.csv',
        'endpoint': '/upload/timeclock',
        'description': '2024 Time Clock Data',
        'order': 6
    },
    'timeclock_2025': {
        'file': 'blazer/Time Clock Data 2025 071825.csv',
        'endpoint': '/upload/timeclock',
        'description': '2025 Time Clock Data',
        'order': 7
    },
    'schedules': {
        'file': 'blazer/Schedule Records.csv',
        'endpoint': '/upload/schedules',
        'description': 'Schedule Records',
        'order': 8
    }
}

def get_credentials():
    """Get credentials from user"""
    print("Please enter your nBrain credentials:")
    username = input("Email: ")
    password = getpass.getpass("Password: ")
    return username, password

def login(username, password):
    """Login and get auth token"""
    print(f"\nLogging in as {username}...")
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/login",
            data={
                "username": username,
                "password": password
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            token = data.get('access_token')
            print("✓ Login successful!")
            return token
        else:
            print(f"✗ Login failed: {response.status_code}")
            print(f"  Response: {response.text}")
            return None
    except Exception as e:
        print(f"✗ Login error: {e}")
        return None

def upload_file_with_progress(file_path, endpoint, token, description):
    """Upload file with progress tracking"""
    if not os.path.exists(file_path):
        print(f"  ⚠️  File not found: {file_path}")
        return False
    
    file_size = os.path.getsize(file_path) / (1024 * 1024)  # MB
    print(f"  📁 File size: {file_size:.1f} MB")
    
    try:
        start_time = time.time()
        
        with open(file_path, 'rb') as f:
            files = {'file': (os.path.basename(file_path), f, 'text/csv')}
            headers = {'Authorization': f'Bearer {token}'}
            
            print(f"  ⬆️  Uploading to {endpoint}...")
            
            response = requests.post(
                f"{API_BASE_URL}/api/salon{endpoint}",
                files=files,
                headers=headers,
                timeout=600  # 10 minute timeout for large files
            )
            
            elapsed = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                print(f"  ✅ Success! (took {elapsed:.1f} seconds)")
                
                # Display results
                if 'records_created' in result:
                    print(f"     • Records created: {result['records_created']:,}")
                if 'records_skipped' in result:
                    print(f"     • Records skipped: {result['records_skipped']:,}")
                if 'records_updated' in result:
                    print(f"     • Records updated: {result['records_updated']:,}")
                
                return True
            else:
                print(f"  ❌ Failed! (after {elapsed:.1f} seconds)")
                print(f"     • Status: {response.status_code}")
                print(f"     • Error: {response.text[:200]}...")
                return False
                
    except requests.exceptions.Timeout:
        print(f"  ⏱️  Upload timed out (file too large)")
        return False
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def main():
    print("=" * 70)
    print("🎯 SALON DATA UPLOAD TO RENDER")
    print("=" * 70)
    print(f"Target: {API_BASE_URL}")
    print()
    
    # Get credentials
    username, password = get_credentials()
    
    # Login
    token = login(username, password)
    if not token:
        print("\n❌ Failed to authenticate. Exiting.")
        sys.exit(1)
    
    print("\n" + "=" * 70)
    print("📊 STARTING DATA UPLOAD")
    print("=" * 70)
    
    # Sort files by upload order
    sorted_files = sorted(FILES_TO_UPLOAD.items(), key=lambda x: x[1]['order'])
    
    # Track results
    results = {
        'successful': [],
        'failed': [],
        'start_time': time.time()
    }
    
    # Upload each file
    for key, info in sorted_files:
        print(f"\n{info['order']}. {info['description']}:")
        print("-" * 50)
        
        success = upload_file_with_progress(
            info['file'],
            info['endpoint'],
            token,
            info['description']
        )
        
        if success:
            results['successful'].append(info['description'])
        else:
            results['failed'].append(info['description'])
    
    # Final summary
    total_time = time.time() - results['start_time']
    
    print("\n" + "=" * 70)
    print("📈 UPLOAD SUMMARY")
    print("=" * 70)
    print(f"Total time: {total_time:.1f} seconds ({total_time/60:.1f} minutes)")
    print(f"\n✅ Successful uploads: {len(results['successful'])}")
    for item in results['successful']:
        print(f"   • {item}")
    
    if results['failed']:
        print(f"\n❌ Failed uploads: {len(results['failed'])}")
        for item in results['failed']:
            print(f"   • {item}")
    
    if len(results['successful']) == len(FILES_TO_UPLOAD):
        print("\n" + "🎉 " * 10)
        print("ALL DATA UPLOADED SUCCESSFULLY!")
        print("🎉 " * 10)
        print("\n✨ Your salon analytics platform is now fully populated!")
        print("\n📊 Next steps:")
        print("   1. Visit: https://nbrain-frontend.onrender.com")
        print("   2. Navigate to Salon Analytics")
        print("   3. Explore your complete data insights:")
        print("      • Revenue analytics by service type")
        print("      • Staff productivity metrics")
        print("      • Time clock vs scheduled hours analysis")
        print("      • Transaction patterns and trends")
        print("      • AI-powered predictions and recommendations")
    else:
        print("\n⚠️  Some uploads failed. Please check the errors above.")
        print("You may need to:")
        print("   1. Check if the tables are created (run migrations)")
        print("   2. Verify file formats match expected schemas")
        print("   3. Try uploading failed files individually")

if __name__ == "__main__":
    main() 