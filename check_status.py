#!/usr/bin/env python3
"""
Check status of database and uploads
"""

import os
import sys
import json
import psutil
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Database URL
DATABASE_URL = os.getenv('DATABASE_URL', '')

if not DATABASE_URL:
    print("Please set your DATABASE_URL environment variable")
    sys.exit(1)

# Create engine
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
Session = sessionmaker(bind=engine)

def check_running_processes():
    """Check if any upload scripts are running"""
    print("\n1. CHECKING RUNNING PROCESSES")
    print("=" * 60)
    
    upload_scripts = [
        'batch_upload.py',
        'fresh_upload.py',
        'weekly_batch_upload.py',
        'monthly_batch_upload.py',
        'api_batch_upload.py',
        'upload_2025_only.py'
    ]
    
    found_processes = []
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = proc.info.get('cmdline', [])
            if cmdline and any(script in ' '.join(cmdline) for script in upload_scripts):
                found_processes.append({
                    'pid': proc.info['pid'],
                    'script': next(s for s in upload_scripts if s in ' '.join(cmdline)),
                    'status': proc.status()
                })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    
    if found_processes:
        print("Found running upload processes:")
        for p in found_processes:
            print(f"  PID {p['pid']}: {p['script']} ({p['status']})")
    else:
        print("  No upload scripts currently running")

def check_progress_files():
    """Check for progress tracking files"""
    print("\n2. CHECKING PROGRESS FILES")
    print("=" * 60)
    
    progress_files = [
        'weekly_upload_progress.json',
        'monthly_upload_progress.json',
        'batch_upload_progress.json',
        'upload_progress.json'
    ]
    
    for file in progress_files:
        if os.path.exists(file):
            print(f"\nFound {file}:")
            try:
                with open(file, 'r') as f:
                    data = json.load(f)
                    print(f"  Content: {json.dumps(data, indent=2)}")
            except Exception as e:
                print(f"  Error reading file: {e}")

def check_database_status(session):
    """Check current database status"""
    print("\n3. DATABASE STATUS")
    print("=" * 60)
    
    # Check connection
    try:
        result = session.execute(text("SELECT version()"))
        version = result.scalar()
        print(f"✓ Connected to: PostgreSQL {version.split(',')[0]}")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return
    
    # Check table counts
    print("\nTable Record Counts:")
    tables = [
        ('salon_locations', 'Locations'),
        ('salon_staff', 'Staff'),
        ('staff_performance', 'Performance'),
        ('salon_transactions', 'Transactions'),
        ('salon_time_clock', 'Time Clock'),
        ('salon_schedules', 'Schedules')
    ]
    
    total_records = 0
    for table, name in tables:
        try:
            result = session.execute(text(f"SELECT COUNT(*) FROM {table}"))
            count = result.scalar()
            total_records += count
            print(f"  {name}: {count:,} records")
        except Exception as e:
            print(f"  {name}: Error - {e}")
    
    print(f"\nTotal Records: {total_records:,}")
    
    # Check date ranges for main data tables
    print("\nData Date Ranges:")
    
    # Transactions
    try:
        result = session.execute(text("""
            SELECT 
                COUNT(*) as count,
                MIN(sale_date) as min_date,
                MAX(sale_date) as max_date,
                COUNT(DISTINCT sale_date) as unique_dates
            FROM salon_transactions
        """))
        row = result.first()
        if row and row.count > 0:
            print(f"\n  Transactions:")
            print(f"    Total: {row.count:,} records")
            print(f"    Date range: {row.min_date} to {row.max_date}")
            print(f"    Unique dates: {row.unique_dates}")
            
            # Check by year
            result = session.execute(text("""
                SELECT 
                    EXTRACT(YEAR FROM sale_date) as year,
                    COUNT(*) as count
                FROM salon_transactions
                GROUP BY EXTRACT(YEAR FROM sale_date)
                ORDER BY year
            """))
            print("    By year:")
            for r in result:
                if r.year:
                    print(f"      {int(r.year)}: {r.count:,} records")
    except Exception as e:
        print(f"  Transactions: Error - {e}")
    
    # Time Clock
    try:
        result = session.execute(text("""
            SELECT 
                COUNT(*) as count,
                MIN(clock_date) as min_date,
                MAX(clock_date) as max_date
            FROM salon_time_clock
        """))
        row = result.first()
        if row and row.count > 0:
            print(f"\n  Time Clock:")
            print(f"    Total: {row.count:,} records")
            print(f"    Date range: {row.min_date} to {row.max_date}")
    except Exception as e:
        print(f"  Time Clock: Error - {e}")
    
    # Schedules
    try:
        result = session.execute(text("""
            SELECT 
                COUNT(*) as count,
                MIN(schedule_date) as min_date,
                MAX(schedule_date) as max_date
            FROM salon_schedules
        """))
        row = result.first()
        if row and row.count > 0:
            print(f"\n  Schedules:")
            print(f"    Total: {row.count:,} records")
            print(f"    Date range: {row.min_date} to {row.max_date}")
    except Exception as e:
        print(f"  Schedules: Error - {e}")

def check_database_activity(session):
    """Check database activity and locks"""
    print("\n4. DATABASE ACTIVITY")
    print("=" * 60)
    
    try:
        # Check active queries
        result = session.execute(text("""
            SELECT 
                pid,
                usename,
                application_name,
                state,
                query_start,
                SUBSTRING(query, 1, 100) as query_preview
            FROM pg_stat_activity
            WHERE datname = current_database()
            AND state != 'idle'
            AND pid != pg_backend_pid()
            ORDER BY query_start
        """))
        
        active = list(result)
        if active:
            print(f"Found {len(active)} active database connections:")
            for row in active:
                print(f"\n  PID {row.pid}:")
                print(f"    User: {row.usename}")
                print(f"    State: {row.state}")
                print(f"    Started: {row.query_start}")
                print(f"    Query: {row.query_preview}...")
        else:
            print("  No active queries found")
            
        # Check for locks
        result = session.execute(text("""
            SELECT 
                l.pid,
                l.mode,
                l.granted,
                a.usename,
                a.query_start,
                SUBSTRING(a.query, 1, 50) as query
            FROM pg_locks l
            JOIN pg_stat_activity a ON l.pid = a.pid
            WHERE l.granted = false
        """))
        
        locks = list(result)
        if locks:
            print(f"\n⚠️  Found {len(locks)} waiting locks:")
            for row in locks:
                print(f"  PID {row.pid}: {row.mode} lock waiting since {row.query_start}")
        
    except Exception as e:
        print(f"  Error checking activity: {e}")

def check_log_files():
    """Check recent log files"""
    print("\n5. LOG FILES")
    print("=" * 60)
    
    log_files = [
        'weekly_upload.log',
        'monthly_upload.log',
        'upload.log'
    ]
    
    for log_file in log_files:
        if os.path.exists(log_file):
            print(f"\nFound {log_file}:")
            try:
                # Get file info
                stat = os.stat(log_file)
                print(f"  Size: {stat.st_size:,} bytes")
                print(f"  Modified: {datetime.fromtimestamp(stat.st_mtime)}")
                
                # Show last 10 lines
                with open(log_file, 'r') as f:
                    lines = f.readlines()
                    if lines:
                        print(f"  Last {min(10, len(lines))} lines:")
                        for line in lines[-10:]:
                            print(f"    {line.rstrip()}")
            except Exception as e:
                print(f"  Error reading log: {e}")

def main():
    print("=" * 60)
    print("DATABASE UPLOAD STATUS CHECK")
    print("=" * 60)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check running processes
    check_running_processes()
    
    # Check progress files
    check_progress_files()
    
    # Check database
    session = Session()
    try:
        check_database_status(session)
        check_database_activity(session)
    finally:
        session.close()
    
    # Check log files
    check_log_files()
    
    print("\n" + "=" * 60)
    print("STATUS CHECK COMPLETE")
    print("=" * 60)
    
    # Summary
    print("\nSUMMARY:")
    print("- Check if any upload scripts are running")
    print("- Review database record counts")
    print("- Look for any blocking database connections")
    print("- Check progress files to see if uploads can be resumed")

if __name__ == "__main__":
    main() 