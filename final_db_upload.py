#!/usr/bin/env python3
"""
Final direct database upload script
This bypasses the API and uploads directly to the database
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import time

# Database URL
DATABASE_URL = os.getenv('DATABASE_URL', '')

if not DATABASE_URL:
    print("Please set your DATABASE_URL environment variable")
    sys.exit(1)

# Create engine
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
Session = sessionmaker(bind=engine)

# File mappings
FILES = {
    'staff': 'blazer/Staff Performance Report.csv',
    'performance': 'blazer/Staff Performance Tracker.csv',
    'transactions_2024': 'blazer/Detailed Line Item 2024.csv',
    'transactions_2025': 'blazer/Detailed Line Item 2025 071825.csv',
    'timeclock_2024': 'blazer/Time Clock Data 2024.csv',
    'timeclock_2025': 'blazer/Time Clock Data 2025 071825.csv',
    'schedules': 'blazer/Schedule Records.csv'
}

def upload_staff_data(session, file_path):
    """Upload staff data"""
    print("\nUploading staff data...")
    
    df = pd.read_csv(file_path)
    staff_count = 0
    
    for _, row in df.iterrows():
        try:
            # Check if location exists
            location_name = row.get('Location', '')
            location = session.execute(
                text("SELECT id FROM salon_locations WHERE name = :name"),
                {"name": location_name}
            ).first()
            
            if not location:
                # Create location
                result = session.execute(
                    text("INSERT INTO salon_locations (name, is_active, created_at) VALUES (:name, true, NOW()) RETURNING id"),
                    {"name": location_name}
                )
                location_id = result.first()[0]
            else:
                location_id = location[0]
            
            # Insert staff
            session.execute(
                text("""INSERT INTO salon_staff 
                (full_name, email, phone, location_id, role, is_active, created_at)
                VALUES (:name, :email, :phone, :loc, :role, true, NOW())
                ON CONFLICT (email) DO UPDATE SET
                    full_name = EXCLUDED.full_name,
                    phone = EXCLUDED.phone,
                    location_id = EXCLUDED.location_id,
                    role = EXCLUDED.role"""),
                {
                    "name": row.get('Staff Name', ''),
                    "email": row.get('Email', f"{row.get('Staff Name', '').replace(' ', '.').lower()}@salon.com"),
                    "phone": row.get('Phone', ''),
                    "loc": location_id,
                    "role": row.get('Role', 'Stylist')
                }
            )
            staff_count += 1
            
        except Exception as e:
            print(f"  Error with staff {row.get('Staff Name', '')}: {e}")
            continue
    
    session.commit()
    print(f"✓ Uploaded {staff_count} staff members")

def upload_performance_data(session, file_path):
    """Upload performance data"""
    print("\nUploading performance data...")
    
    df = pd.read_csv(file_path)
    perf_count = 0
    
    for _, row in df.iterrows():
        try:
            # Get staff
            staff_name = row.get('Staff Name', '')
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
                continue
            
            # Parse date
            period_date = pd.to_datetime(row.get('Period', ''), errors='coerce')
            if pd.isna(period_date):
                period_date = None
            else:
                period_date = period_date.date()
            
            # Convert percentages
            utilization = float(row.get('Utilization %', 0) or 0) / 100
            prebooked = float(row.get('Prebooked %', 0) or 0) / 100
            
            session.execute(
                text("""INSERT INTO staff_performance 
                (staff_id, location_id, period, total_sales, service_count, 
                 retail_sales, client_count, new_clients, utilization_percent, 
                 prebooked_percent, created_at)
                VALUES (:staff, :loc, :period, :sales, :services, 
                        :retail, :clients, :new_clients, :util, 
                        :prebook, NOW())
                ON CONFLICT (staff_id, period) DO UPDATE SET
                    total_sales = EXCLUDED.total_sales,
                    service_count = EXCLUDED.service_count,
                    retail_sales = EXCLUDED.retail_sales,
                    client_count = EXCLUDED.client_count,
                    new_clients = EXCLUDED.new_clients,
                    utilization_percent = EXCLUDED.utilization_percent,
                    prebooked_percent = EXCLUDED.prebooked_percent"""),
                {
                    "staff": staff[0],
                    "loc": location[0],
                    "period": period_date,
                    "sales": float(row.get('Total Sales', 0) or 0),
                    "services": int(row.get('Service Count', 0) or 0),
                    "retail": float(row.get('Retail Sales', 0) or 0),
                    "clients": int(row.get('Client Count', 0) or 0),
                    "new_clients": int(row.get('New Clients', 0) or 0),
                    "util": utilization,
                    "prebook": prebooked
                }
            )
            perf_count += 1
            
        except Exception as e:
            print(f"  Error with performance record: {e}")
            continue
    
    session.commit()
    print(f"✓ Uploaded {perf_count} performance records")

def upload_transaction_data(session, file_path, year):
    """Upload transaction data in chunks"""
    print(f"\nUploading {year} transaction data...")
    
    chunk_size = 5000
    total_count = 0
    
    for chunk_num, chunk in enumerate(pd.read_csv(file_path, chunksize=chunk_size), 1):
        chunk_count = 0
        
        for _, row in chunk.iterrows():
            try:
                # Skip summary rows
                sale_id = row.get('Sale id')
                if sale_id == 'All' or pd.isna(sale_id):
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
                
                # Parse date
                sale_date = pd.to_datetime(row.get('Sale Date'), errors='coerce')
                if pd.isna(sale_date):
                    continue
                
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
                continue
        
        session.commit()
        total_count += chunk_count
        print(f"  Chunk {chunk_num}: {chunk_count} records inserted (Total: {total_count})")
        time.sleep(0.1)  # Small delay between chunks
    
    print(f"✓ Uploaded {total_count} transactions for {year}")

def upload_timeclock_data(session, file_path, year):
    """Upload time clock data"""
    print(f"\nUploading {year} time clock data...")
    
    df = pd.read_csv(file_path)
    tc_count = 0
    
    for idx, row in df.iterrows():
        try:
            staff_name = row.get('Employee Name', '')
            if not staff_name:
                continue
            
            staff = session.execute(
                text("SELECT id FROM salon_staff WHERE full_name = :name"),
                {"name": staff_name}
            ).first()
            
            if not staff:
                continue
            
            # Parse dates
            clock_date = pd.to_datetime(row.get('Date'), errors='coerce')
            clock_in = pd.to_datetime(row.get('Clock In'), errors='coerce')
            clock_out = pd.to_datetime(row.get('Clock Out'), errors='coerce')
            
            if pd.isna(clock_date):
                continue
            
            # Calculate hours
            hours_worked = 0
            minutes_worked = 0
            if pd.notna(clock_in) and pd.notna(clock_out):
                delta = clock_out - clock_in
                hours_worked = delta.total_seconds() / 3600
                minutes_worked = delta.total_seconds() / 60
            
            # Generate unique timecard_id
            timecard_id = f"{year}_tc_{idx}"
            
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
                    "date": clock_date.date(),
                    "in_time": clock_in if pd.notna(clock_in) else None,
                    "out_time": clock_out if pd.notna(clock_out) else None,
                    "hours": float(hours_worked),
                    "minutes": float(minutes_worked)
                }
            )
            tc_count += 1
            
        except Exception as e:
            continue
    
    session.commit()
    print(f"✓ Uploaded {tc_count} time clock entries")

def upload_schedule_data(session, file_path):
    """Upload schedule data"""
    print("\nUploading schedule data...")
    
    df = pd.read_csv(file_path)
    sched_count = 0
    
    for idx, row in df.iterrows():
        try:
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
            
            # Parse dates
            schedule_date = pd.to_datetime(row.get('Schedule Date'), errors='coerce')
            start_time = pd.to_datetime(row.get('Start Time'), errors='coerce')
            end_time = pd.to_datetime(row.get('End Time'), errors='coerce')
            
            if pd.isna(schedule_date):
                continue
            
            # Generate unique schedule_record_id
            schedule_record_id = f"sched_{idx}"
            
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
                    "date": schedule_date.date(),
                    "start": start_time if pd.notna(start_time) else None,
                    "end": end_time if pd.notna(end_time) else None
                }
            )
            sched_count += 1
            
        except Exception as e:
            continue
    
    session.commit()
    print(f"✓ Uploaded {sched_count} schedule records")

def main():
    print("=" * 60)
    print("FINAL DATABASE UPLOAD")
    print("=" * 60)
    print(f"Database: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'configured'}")
    print()
    
    session = Session()
    
    try:
        # Test connection
        result = session.execute(text("SELECT 1"))
        print("✓ Database connection successful")
        
        # Check current state
        print("\nCurrent database state:")
        tables = [
            ('salon_locations', 'Locations'),
            ('salon_staff', 'Staff'),
            ('staff_performance', 'Performance'),
            ('salon_transactions', 'Transactions'),
            ('salon_time_clock', 'Time Clock'),
            ('salon_schedules', 'Schedules')
        ]
        
        for table, name in tables:
            result = session.execute(text(f"SELECT COUNT(*) FROM {table}"))
            count = result.scalar()
            print(f"  {name}: {count:,} records")
        
        # Upload each file type
        if os.path.exists(FILES['staff']):
            upload_staff_data(session, FILES['staff'])
        
        if os.path.exists(FILES['performance']):
            upload_performance_data(session, FILES['performance'])
        
        if os.path.exists(FILES['transactions_2024']):
            upload_transaction_data(session, FILES['transactions_2024'], 2024)
        
        if os.path.exists(FILES['transactions_2025']):
            upload_transaction_data(session, FILES['transactions_2025'], 2025)
        
        if os.path.exists(FILES['timeclock_2024']):
            upload_timeclock_data(session, FILES['timeclock_2024'], 2024)
        
        if os.path.exists(FILES['timeclock_2025']):
            upload_timeclock_data(session, FILES['timeclock_2025'], 2025)
        
        if os.path.exists(FILES['schedules']):
            upload_schedule_data(session, FILES['schedules'])
        
        # Show final state
        print("\n" + "=" * 60)
        print("✓ UPLOAD COMPLETE!")
        print("=" * 60)
        
        print("\nFinal database state:")
        for table, name in tables:
            result = session.execute(text(f"SELECT COUNT(*) FROM {table}"))
            count = result.scalar()
            print(f"  {name}: {count:,} records")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        session.rollback()
        import traceback
        traceback.print_exc()
        
    finally:
        session.close()

if __name__ == "__main__":
    main() 