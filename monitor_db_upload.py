#!/usr/bin/env python3
"""
Monitor database upload progress
"""

import os
import time
from datetime import datetime
from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv('DATABASE_URL', '')

if not DATABASE_URL:
    print("Please set your DATABASE_URL environment variable")
    exit(1)

engine = create_engine(DATABASE_URL)

def monitor_progress():
    """Monitor upload progress"""
    print("Monitoring database upload progress...")
    print("Press Ctrl+C to stop\n")
    
    tables = [
        ('salon_locations', 'Locations'),
        ('salon_staff', 'Staff'),
        ('staff_performance', 'Performance'),
        ('salon_transactions', 'Transactions'),
        ('salon_time_clock', 'Time Clock'),
        ('salon_schedules', 'Schedules')
    ]
    
    last_counts = {}
    
    while True:
        try:
            with engine.connect() as conn:
                # Clear screen
                print("\033[2J\033[H")
                
                print("=" * 60)
                print(f"DATABASE UPLOAD PROGRESS - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                print("=" * 60)
                
                total_records = 0
                
                for table, name in tables:
                    result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = result.scalar()
                    total_records += count
                    
                    # Check if count changed
                    status = "🔄" if table in last_counts and last_counts[table] != count else "  "
                    
                    print(f"{status} {name}: {count:,} records")
                    
                    last_counts[table] = count
                
                print("-" * 60)
                print(f"Total Records: {total_records:,}")
                
                # Expected totals
                print("\nExpected:")
                print("  Transactions: ~607,918")
                print("  Time Clock: ~66,884")
                print("  Schedules: ~132,731")
                
            time.sleep(2)
            
        except KeyboardInterrupt:
            print("\n\nMonitoring stopped.")
            break
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    monitor_progress() 