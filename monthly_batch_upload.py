#!/usr/bin/env python3
"""
Monthly batch upload - processes data month by month for better performance
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import time
import json

# Database URL
DATABASE_URL = os.getenv('DATABASE_URL', '')

if not DATABASE_URL:
    print("Please set your DATABASE_URL environment variable")
    sys.exit(1)

# Create engine
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
Session = sessionmaker(bind=engine)

# Progress tracking
PROGRESS_FILE = 'monthly_upload_progress.json'

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

def clear_tables(session):
    """Clear existing data from tables"""
    print("\nClearing existing data...")
    tables = [
        ('salon_transactions', 'Transactions'),
        ('salon_time_clock', 'Time Clock'),
        ('salon_schedules', 'Schedules')
    ]
    
    for table, name in tables:
        result = session.execute(text(f"SELECT COUNT(*) FROM {table}"))
        count = result.scalar()
        if count > 0:
            session.execute(text(f"DELETE FROM {table}"))
            session.commit()
            print(f"  ✓ Cleared {count:,} records from {name}")

def get_months_in_file(file_path, date_column):
    """Get list of year-month combinations in a file"""
    print(f"  Scanning file for months...")
    months = set()
    
    # Read file in chunks to get all months
    for chunk in pd.read_csv(file_path, chunksize=10000):
        dates = pd.to_datetime(chunk[date_column], errors='coerce')
        valid_dates = dates.dropna()
        
        for date in valid_dates:
            if date.year >= 2025:  # Only 2025 and later
                months.add((date.year, date.month))
    
    return sorted(list(months))

def upload_transactions_by_month(session, file_path, year_month):
    """Upload transaction data for a specific month"""
    year, month = year_month
    month_name = datetime(year, month, 1).strftime('%B %Y')
    
    print(f"\n  Processing {month_name} transactions...")
    
    total_count = 0
    chunk_size = 2000  # Smaller chunks for monthly processing
    
    for chunk in pd.read_csv(file_path, chunksize=chunk_size):
        chunk_count = 0
        
        for _, row in chunk.iterrows():
            try:
                # Skip summary rows
                sale_id = row.get('Sale id')
                if sale_id == 'All' or pd.isna(sale_id):
                    continue
                
                # Parse date
                sale_date = pd.to_datetime(row.get('Sale Date'), errors='coerce')
                if pd.isna(sale_date):
                    continue
                
                # Only process this specific month
                if sale_date.year != year or sale_date.month != month:
                    continue
                
                # Get location
                location_name = row.get('Location Name', '')
                if not location_name:
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
                            :net_service, :net_sales, NOW())"""),
                    {
                        "sale_id": sale_id,
                        "loc": location_id,
                        "sale_date": sale_date.date(),
                        "client": row.get('Client Name', ''),
                        "staff": staff_id,
                        "service": row.get('Service Name', ''),
                        "sale_type": row.get('Sale Type', ''),
                        "net_service": float(row.get('Net Service Sales', 0) or 0),
                        "net_sales": float(row.get('Net Sales', 0) or 0)
                    }
                )
                chunk_count += 1
                
            except Exception as e:
                if "duplicate key" not in str(e):
                    print(f"    Error: {e}")
                continue
        
        if chunk_count > 0:
            session.commit()
            total_count += chunk_count
    
    print(f"    ✓ {month_name}: {total_count:,} records")
    return total_count

def upload_timeclock_by_month(session, file_path, year_month):
    """Upload time clock data for a specific month"""
    year, month = year_month
    month_name = datetime(year, month, 1).strftime('%B %Y')
    
    print(f"\n  Processing {month_name} time clock...")
    
    total_count = 0
    
    # Read entire file (time clock files are smaller)
    df = pd.read_csv(file_path)
    
    for idx, row in df.iterrows():
        try:
            # Parse date
            clock_date = pd.to_datetime(row.get('Date'), errors='coerce')
            if pd.isna(clock_date):
                continue
            
            # Only process this specific month
            if clock_date.year != year or clock_date.month != month:
                continue
            
            staff_name = row.get('Employee Name', '')
            if not staff_name:
                continue
            
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
            timecard_id = f"{year}_{month:02d}_tc_{idx}"
            
            session.execute(
                text("""INSERT INTO salon_time_clock 
                (timecard_id, staff_id, clock_date, clock_in, clock_out, 
                 hours_clocked, minutes_clocked, created_at)
                VALUES (:timecard_id, :staff, :date, :in_time, :out_time, 
                        :hours, :minutes, NOW())"""),
                {
                    "timecard_id": timecard_id,
                    "staff": staff[0],
                    "date": clock_date.date(),
                    "in_time": clock_in if pd.notna(clock_in) else None,
                    "out_time": clock_out if pd.notna(clock_out) else None,
                    "hours": float(hours_worked),
                    "minutes": float(minutes_worked)
                }
            )
            total_count += 1
            
        except Exception as e:
            if "duplicate key" not in str(e):
                print(f"    Error: {e}")
            continue
    
    if total_count > 0:
        session.commit()
    
    print(f"    ✓ {month_name}: {total_count:,} records")
    return total_count

def upload_schedules_by_month(session, file_path, year_month):
    """Upload schedule data for a specific month"""
    year, month = year_month
    month_name = datetime(year, month, 1).strftime('%B %Y')
    
    print(f"\n  Processing {month_name} schedules...")
    
    total_count = 0
    
    # Read entire file
    df = pd.read_csv(file_path)
    
    for idx, row in df.iterrows():
        try:
            # Parse date
            schedule_date = pd.to_datetime(row.get('Schedule Date'), errors='coerce')
            if pd.isna(schedule_date):
                continue
            
            # Only process this specific month
            if schedule_date.year != year or schedule_date.month != month:
                continue
            
            staff_name = row.get('Staff Name', '')
            if not staff_name:
                continue
            
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
            schedule_record_id = f"sched_{year}_{month:02d}_{idx}"
            
            session.execute(
                text("""INSERT INTO salon_schedules 
                (schedule_record_id, staff_id, location_id, schedule_date, 
                 start_time, end_time, created_at)
                VALUES (:schedule_record_id, :staff, :loc, :date, 
                        :start, :end, NOW())"""),
                {
                    "schedule_record_id": schedule_record_id,
                    "staff": staff[0],
                    "loc": location_id,
                    "date": schedule_date.date(),
                    "start": start_time if pd.notna(start_time) else None,
                    "end": end_time if pd.notna(end_time) else None
                }
            )
            total_count += 1
            
        except Exception as e:
            if "duplicate key" not in str(e):
                print(f"    Error: {e}")
            continue
    
    if total_count > 0:
        session.commit()
    
    print(f"    ✓ {month_name}: {total_count:,} records")
    return total_count

def main():
    print("=" * 60)
    print("MONTHLY BATCH UPLOAD (2025 DATA ONLY)")
    print("=" * 60)
    print(f"Database: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'configured'}")
    print("\n📅 Processing data month by month for better performance")
    print()
    
    session = Session()
    progress = load_progress()
    
    try:
        # Test connection
        result = session.execute(text("SELECT 1"))
        print("✓ Database connection successful")
        
        # Clear tables if starting fresh
        if not progress:
            clear_tables(session)
            progress = {'months_completed': [], 'totals': {}}
            save_progress(progress)
        
        # Process each data type
        data_types = [
            {
                'name': 'Transactions',
                'file': 'blazer/Detailed Line Item 2025 071825.csv',
                'date_column': 'Sale Date',
                'upload_func': upload_transactions_by_month
            },
            {
                'name': 'Time Clock',
                'file': 'blazer/Time Clock Data 2025 071825.csv',
                'date_column': 'Date',
                'upload_func': upload_timeclock_by_month
            },
            {
                'name': 'Schedules',
                'file': 'blazer/Schedule Records.csv',
                'date_column': 'Schedule Date',
                'upload_func': upload_schedules_by_month
            }
        ]
        
        for data_type in data_types:
            if not os.path.exists(data_type['file']):
                print(f"\n❌ File not found: {data_type['file']}")
                continue
            
            print(f"\n📊 Processing {data_type['name']}...")
            
            # Get months in file
            months = get_months_in_file(data_type['file'], data_type['date_column'])
            print(f"  Found {len(months)} months of data (2025+)")
            
            # Process each month
            type_total = 0
            for year_month in months:
                month_key = f"{data_type['name']}_{year_month[0]}_{year_month[1]:02d}"
                
                # Skip if already completed
                if month_key in progress['months_completed']:
                    month_name = datetime(year_month[0], year_month[1], 1).strftime('%B %Y')
                    print(f"    ✓ {month_name}: Already completed")
                    continue
                
                # Process this month
                count = data_type['upload_func'](session, data_type['file'], year_month)
                type_total += count
                
                # Update progress
                progress['months_completed'].append(month_key)
                save_progress(progress)
                
                # Small delay between months
                time.sleep(0.5)
            
            progress['totals'][data_type['name']] = type_total
            save_progress(progress)
        
        # Show final summary
        print("\n" + "=" * 60)
        print("✓ MONTHLY UPLOAD COMPLETE!")
        print("=" * 60)
        
        print("\nFinal counts:")
        for data_type, count in progress['totals'].items():
            print(f"  {data_type}: {count:,} records")
        
        # Verify in database
        print("\nVerifying database counts:")
        tables = [
            ('salon_transactions', 'Transactions'),
            ('salon_time_clock', 'Time Clock'),
            ('salon_schedules', 'Schedules')
        ]
        
        for table, name in tables:
            result = session.execute(text(f"SELECT COUNT(*) FROM {table}"))
            count = result.scalar()
            print(f"  {name}: {count:,} records")
        
        # Clean up progress file
        if os.path.exists(PROGRESS_FILE):
            os.remove(PROGRESS_FILE)
            print("\n✓ Progress file cleaned up")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Upload interrupted by user")
        print("Progress has been saved. Run the script again to resume.")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        session.rollback()
        import traceback
        traceback.print_exc()
        
    finally:
        session.close()

if __name__ == "__main__":
    main() 