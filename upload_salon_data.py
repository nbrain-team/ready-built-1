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

# File mappings
FILES_TO_UPLOAD = {
    'staff': 'blazer/Emp List Active as of 1.1.24-7.31.25.csv',
    'performance_2024': 'blazer/Staff Performance_Utilization - All Salons 2024.csv',
    'performance_2025': 'blazer/Staff Performance_Utilization - All Salons 2025 072725.csv',
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

def upload_file(file_path, endpoint, token):
    """Upload a single file to the specified endpoint"""
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return False
    
    try:
        with open(file_path, 'rb') as f:
            files = {'file': (os.path.basename(file_path), f, 'text/csv')}
            headers = {'Authorization': f'Bearer {token}'}
            
            response = requests.post(
                f"{API_BASE_URL}/api/salon{endpoint}",
                files=files,
                headers=headers
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✓ Successfully uploaded {os.path.basename(file_path)}")
                print(f"  Result: {json.dumps(result, indent=2)}")
                return True
            else:
                print(f"✗ Failed to upload {os.path.basename(file_path)}")
                print(f"  Status: {response.status_code}")
                print(f"  Error: {response.text}")
                return False
                
    except Exception as e:
        print(f"✗ Error uploading {file_path}: {e}")
        return False

def main():
    print("=== Salon Data Upload Script ===")
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
    print("-" * 50)
    
    # Upload staff data first
    print("\n1. Uploading Staff Data:")
    if upload_file(FILES_TO_UPLOAD['staff'], '/upload/staff', token):
        print("   Staff data uploaded successfully!")
    
    # Upload performance data
    print("\n2. Uploading Performance Data 2024:")
    if upload_file(FILES_TO_UPLOAD['performance_2024'], '/upload/performance', token):
        print("   Performance 2024 data uploaded successfully!")
    
    print("\n3. Uploading Performance Data 2025:")
    if upload_file(FILES_TO_UPLOAD['performance_2025'], '/upload/performance', token):
        print("   Performance 2025 data uploaded successfully!")
    
    print("\n" + "=" * 50)
    print("Upload process completed!")
    print("\nYou can now:")
    print("- View the dashboard at: https://nbrain-frontend.onrender.com")
    print("- Use the AI Assistant to analyze the data")
    print("- Check capacity utilization and staff performance metrics")

if __name__ == "__main__":
    main() 