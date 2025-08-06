#!/usr/bin/env python3
"""
Monitor API upload progress
"""

import json
import os
import time
from datetime import datetime

PROGRESS_FILE = 'api_upload_progress.json'

def monitor_progress():
    """Monitor upload progress in real-time"""
    last_update = {}
    
    print("Monitoring API upload progress...")
    print("Press Ctrl+C to stop monitoring\n")
    
    while True:
        try:
            if not os.path.exists(PROGRESS_FILE):
                print("Waiting for upload to start...")
                time.sleep(2)
                continue
            
            with open(PROGRESS_FILE, 'r') as f:
                progress = json.load(f)
            
            # Clear screen for clean display
            print("\033[2J\033[H")  # Clear screen and move to top
            
            print("=" * 60)
            print(f"API UPLOAD PROGRESS - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("=" * 60)
            
            total_rows = 0
            processed_rows = 0
            
            for file_key, info in progress.items():
                status = "✅" if info['status'] == 'completed' else "🔄"
                percent = (info['processed_rows'] / info['total_rows']) * 100 if info['total_rows'] > 0 else 0
                
                total_rows += info['total_rows']
                processed_rows += info['processed_rows']
                
                # Display file progress
                print(f"\n{status} {file_key}:")
                print(f"   {info['processed_rows']:,} / {info['total_rows']:,} rows ({percent:.1f}%)")
                
                if info['status'] != 'completed':
                    remaining = info['total_rows'] - info['processed_rows']
                    print(f"   Remaining: {remaining:,} rows")
                    
                    # Progress bar
                    bar_length = 40
                    filled = int(bar_length * percent / 100)
                    bar = "█" * filled + "░" * (bar_length - filled)
                    print(f"   [{bar}]")
            
            # Overall progress
            overall_percent = (processed_rows / total_rows) * 100 if total_rows > 0 else 0
            print(f"\n{'=' * 60}")
            print(f"Overall Progress: {processed_rows:,} / {total_rows:,} ({overall_percent:.1f}%)")
            
            # Check if all completed
            if all(info['status'] == 'completed' for info in progress.values()):
                print("\n✅ ALL UPLOADS COMPLETED!")
                print("\nRunning final verification...")
                break
            
            time.sleep(2)  # Update every 2 seconds
            
        except KeyboardInterrupt:
            print("\n\nMonitoring stopped by user.")
            break
        except Exception as e:
            print(f"Error reading progress: {e}")
            time.sleep(2)

if __name__ == "__main__":
    monitor_progress() 