#!/usr/bin/env python3
"""
Upload just one week of data (Jan 1-7, 2025) for all categories
Optimized for Render's limited resources with proper error handling
"""

import os
import sys
import pandas as pd
from datetime import datetime, date
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
import time

# Database URL
DATABASE_URL = os.getenv('DATABASE_URL', '')

if not DATABASE_URL:
    print("Please set your DATABASE_URL environment variable")
    sys.exit(1)

# Create engine with NullPool to minimize connections
engine = create_engine(
    DATABASE_URL, 
    poolclass=NullPool,
    connect_args={
        'connect_timeout': 10,
        'options': '-c statement_timeout=30000'
    }
)
Session = sessionmaker(bind=engine)

# Target week: Jan 1-7, 2025
TARGET_START = date(2025, 1, 1)
TARGET_END = date(2025, 1, 7)

def process_transactions_for_week():
    """Process transaction data for the target week"""
    print(f"\n📊 Processing Transactions for {TARGET_START} to {TARGET_END}...")
    
    file_path = 'blazer/Detailed Line Item 2025 071825.csv'
    session = Session()
    count = 0
    
    try:
        # Read only the necessary columns to save memory
        df = pd.read_csv(file_path, usecols=[
            'Sale id', 'Sale Date', 'Location Name', 'Staff Name',
            'Client Name', 'Service Name', 'Sale Type',
            'Net Service Sales', 'Net Sales'
        ])
        
        # Parse dates and filter for target week
        df['Sale Date'] = pd.to_datetime(df['Sale Date'], errors='coerce')
        df = df[df['Sale Date'].notna()]
        df = df[(df['Sale Date'].dt.date >= TARGET_START) & 
                (df['Sale Date'].dt.date <= TARGET_END)]
        
        # Skip summary rows
        df = df[df['Sale id'] != 'All']
        df = df[df['Sale id'].notna()]
        
        print(f"  Found {len(df)} transactions for the week")
        
        # Process each transaction
        for idx, row in df.iterrows():
            try:
                # Get or create location
                location_name = row['Location Name']
                if pd.isna(location_name):
                    continue
                
                location = session.execute(
                    text("SELECT id FROM salon_locations WHERE name = :name"),
                    {"name": location_name}
                ).first()
                
                if not location:
                    result = session.execute(
                        text("INSERT INTO salon_locations (name, is_active, created_at) VALUES (:name, true, NOW()) RETURNING id"),
                        {"name": location_name}
                    )
                    location_id = result.first()[0]
                else:
                    location_id = location[0]
                
                # Get staff (optional)
                staff_name = row.get('Staff Name', '')
                staff_id = None
                
                if staff_name and staff_name != 'No Staff' and not pd.isna(staff_name):
                    staff = session.execute(
                        text("SELECT id FROM salon_staff WHERE full_name = :name"),
                        {"name": staff_name}
                    ).first()
                    staff_id = staff[0] if staff else None
                
                # Insert transaction
                session.execute(
                    text("""INSERT INTO salon_transactions 
                    (sale_id, location_id, sale_date, client_name, 
                     staff_id, service_name, sale_type, 
                     net_service_sales, net_sales, created_at)
                    VALUES (:sale_id, :loc, :sale_date, :client, 
                            :staff, :service, :sale_type,
                            :net_service, :net_sales, NOW())
                    ON CONFLICT (sale_id) DO NOTHING"""),
                    {
                        "sale_id": row['Sale id'],
                        "loc": location_id,
                        "sale_date": row['Sale Date'].date(),
                        "client": row.get('Client Name', ''),
                        "staff": staff_id,
                        "service": row.get('Service Name', ''),
                        "sale_type": row.get('Sale Type', ''),
                        "net_service": float(row.get('Net Service Sales', 0) or 0),
                        "net_sales": float(row.get('Net Sales', 0) or 0)
                    }
                )
                count += 1
                
                # Commit every 50 records
                if count % 50 == 0:
                    session.commit()
                    print(f"    Processed {count} transactions...", end='\r')
                    time.sleep(0.5)  # Small delay
                    
            except Exception as e:
                print(f"\n  ⚠️  Error with transaction {row.get('Sale id', 'unknown')}: {e}")
                session.rollback()
                # Start a new session after rollback
                session.close()
                session = Session()
                continue
        
        # Final commit
        session.commit()
        print(f"\n  ✅ Uploaded {count} transactions for the week")
        
    except Exception as e:
        print(f"\n  ❌ Error processing transactions: {e}")
        session.rollback()
    finally:
        session.close()
    
    return count

def process_timeclock_for_week():
    """Process time clock data for the target week"""
    print(f"\n⏰ Processing Time Clock for {TARGET_START} to {TARGET_END}...")
    
    file_path = 'blazer/Time Clock Data 2025 071825.csv'
    session = Session()
    count = 0
    
    try:
        # Read the file
        df = pd.read_csv(file_path)
        
        # Parse dates and filter for target week
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df = df[df['Date'].notna()]
        df = df[(df['Date'].dt.date >= TARGET_START) & 
                (df['Date'].dt.date <= TARGET_END)]
        
        print(f"  Found {len(df)} time clock entries for the week")
        
        # Process each entry
        for idx, row in df.iterrows():
            try:
                staff_name = row.get('Employee Name', '')
                if not staff_name:
                    continue
                
                # Get staff
                staff = session.execute(
                    text("SELECT id FROM salon_staff WHERE full_name = :name"),
                    {"name": staff_name}
                ).first()
                
                if not staff:
                    continue
                
                # Parse times
                clock_in = pd.to_datetime(row.get('Clock In'), errors='coerce')
                clock_out = pd.to_datetime(row.get('Clock Out'), errors='coerce')
                
                # Calculate hours
                hours_worked = 0
                minutes_worked = 0
                if pd.notna(clock_in) and pd.notna(clock_out):
                    delta = clock_out - clock_in
                    hours_worked = delta.total_seconds() / 3600
                    minutes_worked = delta.total_seconds() / 60
                
                # Generate unique timecard_id
                timecard_id = f"2025_w1_{idx}"
                
                session.execute(
                    text("""INSERT INTO salon_time_clock 
                    (timecard_id, staff_id, clock_date, clock_in, clock_out, 
                     hours_clocked, minutes_clocked, created_at)
                    VALUES (:timecard_id, :staff, :date, :in_time, :out_time, 
                            :hours, :minutes, NOW())
                    ON CONFLICT (timecard_id) DO NOTHING"""),
                    {
                        "timecard_id": timecard_id,
                        "staff": staff[0],
                        "date": row['Date'].date(),
                        "in_time": clock_in if pd.notna(clock_in) else None,
                        "out_time": clock_out if pd.notna(clock_out) else None,
                        "hours": float(hours_worked),
                        "minutes": float(minutes_worked)
                    }
                )
                count += 1
                
                # Commit every 50 records
                if count % 50 == 0:
                    session.commit()
                    print(f"    Processed {count} time clock entries...", end='\r')
                    time.sleep(0.5)
                    
            except Exception as e:
                print(f"\n  ⚠️  Error with time clock entry: {e}")
                session.rollback()
                session.close()
                session = Session()
                continue
        
        # Final commit
        session.commit()
        print(f"\n  ✅ Uploaded {count} time clock entries for the week")
        
    except Exception as e:
        print(f"\n  ❌ Error processing time clock: {e}")
        session.rollback()
    finally:
        session.close()
    
    return count

def process_schedules_for_week():
    """Process schedule data for the target week"""
    print(f"\n📅 Processing Schedules for {TARGET_START} to {TARGET_END}...")
    
    file_path = 'blazer/Schedule Records.csv'
    session = Session()
    count = 0
    
    try:
        # Read the file
        df = pd.read_csv(file_path)
        
        # Parse dates and filter for target week
        df['Schedule Date'] = pd.to_datetime(df['Schedule Date'], errors='coerce')
        df = df[df['Schedule Date'].notna()]
        df = df[(df['Schedule Date'].dt.date >= TARGET_START) & 
                (df['Schedule Date'].dt.date <= TARGET_END)]
        
        print(f"  Found {len(df)} schedule records for the week")
        
        # Process each entry
        for idx, row in df.iterrows():
            try:
                staff_name = row.get('Staff Name', '')
                if not staff_name:
                    continue
                
                # Get staff
                staff = session.execute(
                    text("SELECT id FROM salon_staff WHERE full_name = :name"),
                    {"name": staff_name}
                ).first()
                
                if not staff:
                    continue
                
                # Get location
                location_name = row.get('Location', '')
                location = session.execute(
                    text("SELECT id FROM salon_locations WHERE name = :name"),
                    {"name": location_name}
                ).first()
                
                if not location:
                    result = session.execute(
                        text("INSERT INTO salon_locations (name, is_active, created_at) VALUES (:name, true, NOW()) RETURNING id"),
                        {"name": location_name}
                    )
                    location_id = result.first()[0]
                else:
                    location_id = location[0]
                
                # Parse times
                start_time = pd.to_datetime(row.get('Start Time'), errors='coerce')
                end_time = pd.to_datetime(row.get('End Time'), errors='coerce')
                
                # Generate unique schedule_record_id
                schedule_record_id = f"sched_2025_w1_{idx}"
                
                session.execute(
                    text("""INSERT INTO salon_schedules 
                    (schedule_record_id, staff_id, location_id, schedule_date, 
                     start_time, end_time, created_at)
                    VALUES (:schedule_record_id, :staff, :loc, :date, 
                            :start, :end, NOW())
                    ON CONFLICT (schedule_record_id) DO NOTHING"""),
                    {
                        "schedule_record_id": schedule_record_id,
                        "staff": staff[0],
                        "loc": location_id,
                        "date": row['Schedule Date'].date(),
                        "start": start_time if pd.notna(start_time) else None,
                        "end": end_time if pd.notna(end_time) else None
                    }
                )
                count += 1
                
                # Commit every 50 records
                if count % 50 == 0:
                    session.commit()
                    print(f"    Processed {count} schedule records...", end='\r')
                    time.sleep(0.5)
                    
            except Exception as e:
                print(f"\n  ⚠️  Error with schedule record: {e}")
                session.rollback()
                session.close()
                session = Session()
                continue
        
        # Final commit
        session.commit()
        print(f"\n  ✅ Uploaded {count} schedule records for the week")
        
    except Exception as e:
        print(f"\n  ❌ Error processing schedules: {e}")
        session.rollback()
    finally:
        session.close()
    
    return count

def check_database_status():
    """Check current database status"""
    session = Session()
    try:
        print("\n📊 Current Database Status:")
        print("-" * 40)
        
        # Check each table
        tables = [
            ('salon_transactions', 'Transactions'),
            ('salon_time_clock', 'Time Clock'),
            ('salon_schedules', 'Schedules')
        ]
        
        for table, name in tables:
            result = session.execute(text(f"SELECT COUNT(*) FROM {table}"))
            count = result.scalar()
            print(f"  {name}: {count:,} records")
        
        # Check date range for transactions
        result = session.execute(text("""
            SELECT MIN(sale_date) as min_date, MAX(sale_date) as max_date
            FROM salon_transactions
            WHERE sale_date >= '2025-01-01'
        """))
        row = result.first()
        if row and row.min_date:
            print(f"\n  Transaction date range: {row.min_date} to {row.max_date}")
            
    except Exception as e:
        print(f"  Error checking status: {e}")
    finally:
        session.close()

def main():
    print("=" * 60)
    print("ONE WEEK DATA UPLOAD")
    print(f"Target: {TARGET_START} to {TARGET_END}")
    print("=" * 60)
    
    # Check initial status
    check_database_status()
    
    # Process each data type
    start_time = time.time()
    
    trans_count = process_transactions_for_week()
    time.sleep(2)  # Pause between categories
    
    tc_count = process_timeclock_for_week()
    time.sleep(2)
    
    sched_count = process_schedules_for_week()
    
    # Final summary
    elapsed = time.time() - start_time
    print("\n" + "=" * 60)
    print("✅ ONE WEEK UPLOAD COMPLETE")
    print("=" * 60)
    print(f"Time taken: {elapsed:.1f} seconds")
    print(f"\nRecords uploaded:")
    print(f"  Transactions: {trans_count}")
    print(f"  Time Clock: {tc_count}")
    print(f"  Schedules: {sched_count}")
    
    # Final status check
    check_database_status()

if __name__ == "__main__":
    main() 