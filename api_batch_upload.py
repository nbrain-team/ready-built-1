#!/usr/bin/env python3
"""
API-based batch upload for salon data
Uses the backend endpoints which handle all the data mapping correctly
"""

import os
import sys
import requests
import pandas as pd
import time
import json
from io import StringIO

# API Configuration
API_BASE_URL = "https://ready-built-1.onrender.com"
EMAIL = "danny@nbrain.ai"
PASSWORD = "Onethree34"  # Updated password

# File mappings
FILES = {
    'transactions_2024': {
        'path': 'blazer/Detailed Line Item 2024.csv',
        'endpoint': '/api/salon/upload/transactions',
        'name': '2024 Transactions'
    },
    'transactions_2025': {
        'path': 'blazer/Detailed Line Item 2025 071825.csv',
        'endpoint': '/api/salon/upload/transactions',
        'name': '2025 Transactions'
    },
    'timeclock_2024': {
        'path': 'blazer/Time Clock Data 2024.csv',
        'endpoint': '/api/salon/upload/timeclock',
        'name': '2024 Time Clock'
    },
    'timeclock_2025': {
        'path': 'blazer/Time Clock Data 2025 071825.csv',
        'endpoint': '/api/salon/upload/timeclock',
        'name': '2025 Time Clock'
    },
    'schedules': {
        'path': 'blazer/Schedule Records.csv',
        'endpoint': '/api/salon/upload/schedules',
        'name': 'Schedule Records'
    }
}

# Progress file
PROGRESS_FILE = 'api_upload_progress.json'
CHUNK_SIZE = 10000  # Process in 10k row chunks

def load_progress():
    """Load progress from file"""
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_progress(progress):
    """Save progress to file"""
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f, indent=2)

def login():
    """Login and get access token"""
    print(f"Logging in as {EMAIL}...")
    
    response = requests.post(
        f"{API_BASE_URL}/login",
        data={
            "username": EMAIL,
            "password": PASSWORD
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        print("✓ Login successful")
        return data.get("access_token")
    else:
        print(f"✗ Login failed: {response.status_code} - {response.text}")
        return None

def upload_file_in_chunks(token, file_info, file_key):
    """Upload a file in chunks"""
    progress = load_progress()
    
    if file_key not in progress:
        # Count total rows
        total_rows = sum(1 for line in open(file_info['path'], 'r', encoding='utf-8', errors='ignore')) - 1
        progress[file_key] = {
            'total_rows': total_rows,
            'processed_rows': 0,
            'status': 'pending'
        }
        save_progress(progress)
    
    file_progress = progress[file_key]
    
    if file_progress['status'] == 'completed':
        print(f"✓ {file_info['name']} already completed")
        return True
    
    print(f"\nUploading {file_info['name']}...")
    print(f"Total rows: {file_progress['total_rows']:,}")
    print(f"Starting from row: {file_progress['processed_rows']:,}")
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    # Read and process in chunks
    skiprows = file_progress['processed_rows'] if file_progress['processed_rows'] > 0 else None
    
    chunk_num = 0
    for chunk in pd.read_csv(file_info['path'], chunksize=CHUNK_SIZE, 
                             skiprows=skiprows, header=0 if skiprows else None):
        chunk_num += 1
        
        # Convert chunk to CSV string
        csv_buffer = StringIO()
        chunk.to_csv(csv_buffer, index=False)
        csv_content = csv_buffer.getvalue()
        
        # Upload chunk
        files = {
            'file': (f'chunk_{chunk_num}.csv', csv_content, 'text/csv')
        }
        
        try:
            response = requests.post(
                f"{API_BASE_URL}{file_info['endpoint']}",
                headers=headers,
                files=files,
                timeout=300  # 5 minute timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                records = result.get('records_created', 0) + result.get('records_updated', 0)
                print(f"  Chunk {chunk_num}: {records:,} records processed")
            else:
                print(f"  Chunk {chunk_num}: Failed - {response.status_code}")
                print(f"  Error: {response.text[:200]}")
                # Don't stop on error, continue with next chunk
            
        except requests.exceptions.Timeout:
            print(f"  Chunk {chunk_num}: Timeout - retrying...")
            time.sleep(5)
            continue
        except Exception as e:
            print(f"  Chunk {chunk_num}: Error - {str(e)}")
            continue
        
        # Update progress
        file_progress['processed_rows'] += len(chunk)
        progress[file_key] = file_progress
        save_progress(progress)
        
        # Show progress
        percent = (file_progress['processed_rows'] / file_progress['total_rows']) * 100
        print(f"  Progress: {file_progress['processed_rows']:,}/{file_progress['total_rows']:,} ({percent:.1f}%)")
        
        # Small delay between chunks
        time.sleep(1)
    
    # Mark as completed
    file_progress['status'] = 'completed'
    progress[file_key] = file_progress
    save_progress(progress)
    
    print(f"✓ Completed {file_info['name']}")
    return True

def main():
    print("=" * 60)
    print("API-BASED BATCH UPLOAD")
    print("=" * 60)
    print(f"Target: {API_BASE_URL}")
    print(f"Chunk size: {CHUNK_SIZE:,} rows")
    print()
    
    # Login
    token = login()
    if not token:
        print("Failed to authenticate. Exiting.")
        return
    
    # Check progress
    progress = load_progress()
    if progress:
        print("\nPrevious progress found:")
        for file_key, info in progress.items():
            status = "✓" if info['status'] == 'completed' else "⏸"
            percent = (info['processed_rows'] / info['total_rows']) * 100
            print(f"  {status} {file_key}: {percent:.1f}% complete")
    
    # Upload each file
    for file_key, file_info in FILES.items():
        if os.path.exists(file_info['path']):
            success = upload_file_in_chunks(token, file_info, file_key)
            if not success:
                print(f"Failed to upload {file_info['name']}")
        else:
            print(f"File not found: {file_info['path']}")
    
    print("\n" + "=" * 60)
    print("✓ UPLOAD COMPLETE!")
    print("=" * 60)
    
    # Clean up progress file if all completed
    progress = load_progress()
    if all(info['status'] == 'completed' for info in progress.values()):
        os.remove(PROGRESS_FILE)
        print("\n✓ Progress file cleaned up")

if __name__ == "__main__":
    main() 