#!/usr/bin/env python3
"""
Direct database upload script for Salon data
This bypasses the API and uploads directly to the database
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import io

# You'll need to get this from your Render dashboard
# Go to your database service and copy the "External Database URL"
DATABASE_URL = os.getenv('DATABASE_URL', '')

if not DATABASE_URL:
    print("Please set your DATABASE_URL environment variable")
    print("You can find this in your Render dashboard under the database service")
    print("Example: export DATABASE_URL='postgresql://user:pass@host/dbname'")
    sys.exit(1)

# Create engine
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

# File mappings
FILES = {
    'staff': 'blazer/Emp List Active as of 1.1.24-7.31.25.csv',
    'performance_2024': 'blazer/Staff Performance_Utilization - All Salons 2024.csv',
    'performance_2025': 'blazer/Staff Performance_Utilization - All Salons 2025 072725.csv',
    'transactions_2024': 'blazer/Detailed Line Item 2024.csv',
    'transactions_2025': 'blazer/Detailed Line Item 2025 071825.csv',
    'timeclock_2024': 'blazer/Time Clock Data 2024.csv',
    'timeclock_2025': 'blazer/Time Clock Data 2025 071825.csv',
    'schedules': 'blazer/Schedule Records.csv'
}

def upload_staff_data(session, file_path):
    """Upload staff data"""
    print(f"Uploading staff data from {file_path}...")
    df = pd.read_csv(file_path)
    
    locations_created = 0
    staff_created = 0
    
    for _, row in df.iterrows():
        # Extract location
        dept = row.get('HOME DEPARTMENT', '')
        location_name = dept.split(' - ')[-1] if ' - ' in dept else dept
        
        # Check/create location
        location = session.execute(
            text("SELECT id FROM salon_locations WHERE name = :name"),
            {"name": location_name}
        ).first()
        
        if not location and location_name:
            result = session.execute(
                text("INSERT INTO salon_locations (name, code, is_active, created_at) "
                     "VALUES (:name, :code, true, NOW()) RETURNING id"),
                {
                    "name": location_name,
                    "code": dept.split(' - ')[0] if ' - ' in dept else None
                }
            )
            location_id = result.first()[0]
            locations_created += 1
        else:
            location_id = location[0] if location else None
        
        # Create staff
        first_name = row.get('PREFERRED FIRST NAME') or row.get('PAYROLL FIRST NAME', '')
        last_name = row.get('PAYROLL LAST NAME', '')
        full_name = f"{first_name} {last_name}".strip()
        
        # Check if staff exists
        existing = session.execute(
            text("SELECT id FROM salon_staff WHERE full_name = :name"),
            {"name": full_name}
        ).first()
        
        if not existing:
            # Handle NaT values
            hire_date = pd.to_datetime(row.get('HIRE DATE'), errors='coerce')
            rehire_date = pd.to_datetime(row.get('REHIRE DATE'), errors='coerce')
            term_date = pd.to_datetime(row.get('TERMINATION DATE'), errors='coerce')
            
            session.execute(
                text("""INSERT INTO salon_staff 
                (payroll_last_name, payroll_first_name, preferred_first_name, 
                 full_name, job_title, location_id, department, position_status,
                 hire_date, rehire_date, termination_date, created_at)
                VALUES (:last, :first, :preferred, :full, :job, :loc, :dept, :status,
                        :hire, :rehire, :term, NOW())"""),
                {
                    "last": last_name,
                    "first": row.get('PAYROLL FIRST NAME', ''),
                    "preferred": row.get('PREFERRED FIRST NAME', ''),
                    "full": full_name,
                    "job": row.get('JOB TITLE', ''),
                    "loc": location_id,
                    "dept": row.get('HOME DEPARTMENT', ''),
                    "status": row.get('POSITION STATUS', 'A'),
                    "hire": hire_date if pd.notna(hire_date) else None,
                    "rehire": rehire_date if pd.notna(rehire_date) else None,
                    "term": term_date if pd.notna(term_date) else None
                }
            )
            staff_created += 1
    
    session.commit()
    print(f"✓ Created {locations_created} locations and {staff_created} staff members")

def upload_performance_data(session, file_path, year):
    """Upload performance data"""
    print(f"Uploading {year} performance data...")
    df = pd.read_csv(file_path)
    
    # Skip summary rows
    df = df[(df['Location name'] != 'All') & (df['Staff Name'] != 'All') & (df['Staff Name'].notna())]
    
    records_created = 0
    
    for _, row in df.iterrows():
        # Get location
        location = session.execute(
            text("SELECT id FROM salon_locations WHERE name = :name"),
            {"name": row.get('Location name', '')}
        ).first()
        
        if not location:
            continue
            
        # Get staff
        staff = session.execute(
            text("SELECT id FROM salon_staff WHERE full_name = :name"),
            {"name": row.get('Staff Name', '')}
        ).first()
        
        if not staff:
            continue
        
        # Create performance record with proper date
        # Use the last day of the month for the period
        if year == 2024:
            period_date = datetime(2024, 12, 31).date()
        else:
            period_date = datetime(2025, 7, 31).date()
        
        session.execute(
            text("""INSERT INTO staff_performance 
            (location_id, staff_id, period_date, hours_booked, hours_scheduled,
             utilization_percent, prebooked_percent, appointment_count, 
             service_sales, net_sales, created_at)
            VALUES (:loc, :staff, :period, :booked, :scheduled, :util, :prebook,
                    :appts, :service, :net, NOW())
            ON CONFLICT (staff_id, period_date) DO UPDATE SET
                hours_booked = EXCLUDED.hours_booked,
                hours_scheduled = EXCLUDED.hours_scheduled,
                utilization_percent = EXCLUDED.utilization_percent,
                prebooked_percent = EXCLUDED.prebooked_percent,
                appointment_count = EXCLUDED.appointment_count,
                service_sales = EXCLUDED.service_sales,
                net_sales = EXCLUDED.net_sales"""),
            {
                "loc": location[0],
                "staff": staff[0],
                "period": period_date,
                "booked": float(row.get('Hours Booked', 0) or 0),
                "scheduled": float(row.get('Hours Scheduled', 0) or 0),
                "util": float(row.get('Utilization %', 0) or 0) / 100,  # Convert to decimal
                "prebook": float(row.get('Prebooked %', 0) or 0) / 100,  # Convert to decimal
                "appts": int(row.get('Appointment Count', 0) or 0),
                "service": float(row.get('Service Sales', 0) or 0),
                "net": float(row.get('Net Sales', 0) or 0)
            }
        )
        records_created += 1
    
    session.commit()
    print(f"✓ Created/Updated {records_created} performance records")

def upload_transaction_data(session, file_path, year):
    """Upload transaction data"""
    print(f"Uploading {year} transaction data...")
    
    # Read in chunks due to large file size
    chunk_size = 10000
    total_records = 0
    
    for chunk in pd.read_csv(file_path, chunksize=chunk_size):
        records_in_chunk = 0
        
        for _, row in chunk.iterrows():
            # Get location
            location_name = row.get('Location name', '')
            location = session.execute(
                text("SELECT id FROM salon_locations WHERE name = :name"),
                {"name": location_name}
            ).first()
            
            if not location:
                # Create location if it doesn't exist
                result = session.execute(
                    text("INSERT INTO salon_locations (name, is_active, created_at) "
                         "VALUES (:name, true, NOW()) RETURNING id"),
                    {"name": location_name}
                )
                location_id = result.first()[0]
            else:
                location_id = location[0]
            
            # Get staff
            staff_name = row.get('Staff name', '')
            if staff_name and staff_name != 'No Staff':
                staff = session.execute(
                    text("SELECT id FROM salon_staff WHERE full_name = :name"),
                    {"name": staff_name}
                ).first()
                staff_id = staff[0] if staff else None
            else:
                staff_id = None
            
            # Parse dates
            trans_date = pd.to_datetime(row.get('Transaction date'), errors='coerce')
            
            if pd.notna(trans_date):
                session.execute(
                    text("""INSERT INTO salon_transactions 
                    (location_id, staff_id, transaction_date, client_name, 
                     service_name, category, quantity, unit_price, 
                     discount_amount, net_amount, created_at)
                    VALUES (:loc, :staff, :trans_date, :client, :service,
                            :category, :qty, :price, :discount, :net, NOW())"""),
                    {
                        "loc": location_id,
                        "staff": staff_id,
                        "trans_date": trans_date,
                        "client": row.get('Client name', ''),
                        "service": row.get('Item name', ''),
                        "category": row.get('Category', ''),
                        "qty": int(row.get('Quantity', 1) or 1),
                        "price": float(row.get('Unit price', 0) or 0),
                        "discount": float(row.get('Discount amount', 0) or 0),
                        "net": float(row.get('Net amount', 0) or 0)
                    }
                )
                records_in_chunk += 1
        
        session.commit()
        total_records += records_in_chunk
        print(f"  Processed {total_records} records...")
    
    print(f"✓ Created {total_records} transaction records")

def upload_timeclock_data(session, file_path, year):
    """Upload time clock data"""
    print(f"Uploading {year} time clock data...")
    
    # Read in chunks due to large file size
    chunk_size = 10000
    total_records = 0
    
    for chunk in pd.read_csv(file_path, chunksize=chunk_size):
        records_in_chunk = 0
        for _, row in chunk.iterrows():
            # Get staff
            staff_name = row.get('Employee Name', '')
            if not staff_name:
                continue
                
            staff = session.execute(
                text("SELECT id FROM salon_staff WHERE full_name = :name"),
                {"name": staff_name}
            ).first()
            
            if not staff:
                continue  # Skip if staff not found
            
            # Parse dates and times
            clock_date = pd.to_datetime(row.get('Date'), errors='coerce')
            clock_in = pd.to_datetime(row.get('Clock In'), errors='coerce')
            clock_out = pd.to_datetime(row.get('Clock Out'), errors='coerce')
            
            if pd.notna(clock_date):
                # Calculate hours worked
                hours_worked = 0
                if pd.notna(clock_in) and pd.notna(clock_out):
                    hours_worked = (clock_out - clock_in).total_seconds() / 3600
                
                session.execute(
                    text("""INSERT INTO salon_time_clock 
                    (staff_id, clock_date, clock_in_time, clock_out_time, 
                     hours_worked, created_at)
                    VALUES (:staff, :date, :in_time, :out_time, :hours, NOW())
                    ON CONFLICT (staff_id, clock_date) DO UPDATE SET
                        clock_in_time = EXCLUDED.clock_in_time,
                        clock_out_time = EXCLUDED.clock_out_time,
                        hours_worked = EXCLUDED.hours_worked"""),
                    {
                        "staff": staff[0],
                        "date": clock_date.date(),
                        "in_time": clock_in if pd.notna(clock_in) else None,
                        "out_time": clock_out if pd.notna(clock_out) else None,
                        "hours": float(hours_worked)
                    }
                )
                records_in_chunk += 1
        
        session.commit()
        total_records += records_in_chunk
        print(f"  Processed {total_records} records...")
    
    print(f"✓ Created/Updated {total_records} time clock records")

def upload_schedule_data(session, file_path):
    """Upload schedule data"""
    print(f"Uploading schedule data...")
    
    # Read in chunks due to large file size
    chunk_size = 10000
    total_records = 0
    
    for chunk in pd.read_csv(file_path, chunksize=chunk_size):
        records_in_chunk = 0
        for _, row in chunk.iterrows():
            # Get staff
            staff_name = row.get('Staff Name', '')
            if not staff_name:
                continue
                
            staff = session.execute(
                text("SELECT id FROM salon_staff WHERE full_name = :name"),
                {"name": staff_name}
            ).first()
            
            if not staff:
                continue  # Skip if staff not found
            
            # Get location
            location_name = row.get('Location', '')
            location = session.execute(
                text("SELECT id FROM salon_locations WHERE name = :name"),
                {"name": location_name}
            ).first()
            
            if not location:
                # Create location if it doesn't exist
                result = session.execute(
                    text("INSERT INTO salon_locations (name, is_active, created_at) "
                         "VALUES (:name, true, NOW()) RETURNING id"),
                    {"name": location_name}
                )
                location_id = result.first()[0]
            else:
                location_id = location[0]
            
            # Parse dates
            schedule_date = pd.to_datetime(row.get('Schedule Date'), errors='coerce')
            start_time = pd.to_datetime(row.get('Start Time'), errors='coerce')
            end_time = pd.to_datetime(row.get('End Time'), errors='coerce')
            
            if pd.notna(schedule_date):
                # Calculate scheduled hours
                scheduled_hours = 0
                if pd.notna(start_time) and pd.notna(end_time):
                    scheduled_hours = (end_time - start_time).total_seconds() / 3600
                
                session.execute(
                    text("""INSERT INTO salon_schedules 
                    (staff_id, location_id, schedule_date, start_time, 
                     end_time, scheduled_hours, created_at)
                    VALUES (:staff, :loc, :date, :start, :end, :hours, NOW())
                    ON CONFLICT (staff_id, schedule_date) DO UPDATE SET
                        location_id = EXCLUDED.location_id,
                        start_time = EXCLUDED.start_time,
                        end_time = EXCLUDED.end_time,
                        scheduled_hours = EXCLUDED.scheduled_hours"""),
                    {
                        "staff": staff[0],
                        "loc": location_id,
                        "date": schedule_date.date(),
                        "start": start_time if pd.notna(start_time) else None,
                        "end": end_time if pd.notna(end_time) else None,
                        "hours": float(scheduled_hours)
                    }
                )
                records_in_chunk += 1
        
        session.commit()
        total_records += records_in_chunk
        print(f"  Processed {total_records} records...")
    
    print(f"✓ Created/Updated {total_records} schedule records")

def main():
    print("=" * 60)
    print("DIRECT DATABASE UPLOAD FOR SALON DATA")
    print("=" * 60)
    print(f"Database: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'configured'}")
    print()
    
    session = Session()
    
    try:
        # Test connection
        result = session.execute(text("SELECT 1"))
        print("✓ Database connection successful")
        print()
        
        # Upload staff data first
        if os.path.exists(FILES['staff']):
            upload_staff_data(session, FILES['staff'])
        
        # Upload performance data
        if os.path.exists(FILES['performance_2024']):
            upload_performance_data(session, FILES['performance_2024'], 2024)
        
        if os.path.exists(FILES['performance_2025']):
            upload_performance_data(session, FILES['performance_2025'], 2025)
        
        # Upload transaction data
        if os.path.exists(FILES['transactions_2024']):
            upload_transaction_data(session, FILES['transactions_2024'], 2024)
        
        if os.path.exists(FILES['transactions_2025']):
            upload_transaction_data(session, FILES['transactions_2025'], 2025)
        
        # Upload time clock data
        if os.path.exists(FILES['timeclock_2024']):
            upload_timeclock_data(session, FILES['timeclock_2024'], 2024)
        
        if os.path.exists(FILES['timeclock_2025']):
            upload_timeclock_data(session, FILES['timeclock_2025'], 2025)
        
        # Upload schedule data
        if os.path.exists(FILES['schedules']):
            upload_schedule_data(session, FILES['schedules'])
        
        print("\n✓ Data upload complete!")
        print("\nUploaded:")
        print("  • Staff data")
        print("  • Performance data (2024 & 2025)")
        print("  • Transaction data (2024 & 2025)")
        print("  • Time clock data (2024 & 2025)")
        print("  • Schedule records")
        print("\nYour salon analytics dashboard should now have complete data!")
        
    except Exception as e:
        print(f"Error: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    main() 