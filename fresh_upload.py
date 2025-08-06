#!/usr/bin/env python3
"""
Fresh upload - clear and upload 2025 data only
"""

import os
import sys
import pandas as pd
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

def upload_transactions(session):
    """Upload 2025 transaction data"""
    print("\nUploading 2025 transaction data...")
    
    file_path = 'blazer/Detailed Line Item 2025 071825.csv'
    chunk_size = 1000
    total_count = 0
    
    for chunk_num, chunk in enumerate(pd.read_csv(file_path, chunksize=chunk_size), 1):
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
                
                # Skip if not 2025
                if sale_date.year < 2025:
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
                
                # Insert transaction (no ON CONFLICT - we cleared the table)
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
            
        # Progress update every 10 chunks
        if chunk_num % 10 == 0:
            print(f"  Progress: {total_count:,} records uploaded...")
    
    print(f"✓ Uploaded {total_count:,} transactions")
    return total_count

def upload_timeclock(session):
    """Upload 2025 time clock data"""
    print("\nUploading 2025 time clock data...")
    
    file_path = 'blazer/Time Clock Data 2025 071825.csv'
    total_count = 0
    
    df = pd.read_csv(file_path)
    
    for idx, row in df.iterrows():
        try:
            # Parse date
            clock_date = pd.to_datetime(row.get('Date'), errors='coerce')
            if pd.isna(clock_date) or clock_date.year < 2025:
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
            timecard_id = f"2025_tc_{idx}"
            
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
            
            # Commit every 1000 records
            if total_count % 1000 == 0:
                session.commit()
                print(f"  Progress: {total_count:,} records uploaded...")
                
        except Exception as e:
            if "duplicate key" not in str(e):
                print(f"    Error: {e}")
            continue
    
    session.commit()
    print(f"✓ Uploaded {total_count:,} time clock entries")
    return total_count

def upload_schedules(session):
    """Upload schedule data (filtering for 2025)"""
    print("\nUploading 2025 schedule data...")
    
    file_path = 'blazer/Schedule Records.csv'
    total_count = 0
    
    df = pd.read_csv(file_path)
    
    for idx, row in df.iterrows():
        try:
            # Parse date
            schedule_date = pd.to_datetime(row.get('Schedule Date'), errors='coerce')
            if pd.isna(schedule_date) or schedule_date.year < 2025:
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
            schedule_record_id = f"sched_2025_{idx}"
            
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
            
            # Commit every 1000 records
            if total_count % 1000 == 0:
                session.commit()
                print(f"  Progress: {total_count:,} records uploaded...")
                
        except Exception as e:
            if "duplicate key" not in str(e):
                print(f"    Error: {e}")
            continue
    
    session.commit()
    print(f"✓ Uploaded {total_count:,} schedule records")
    return total_count

def main():
    print("=" * 60)
    print("FRESH DATABASE UPLOAD (2025 DATA ONLY)")
    print("=" * 60)
    print(f"Database: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'configured'}")
    
    session = Session()
    
    try:
        # Test connection
        result = session.execute(text("SELECT 1"))
        print("✓ Database connection successful")
        
        # Clear existing data
        clear_tables(session)
        
        # Upload each data type
        start_time = time.time()
        
        trans_count = upload_transactions(session)
        tc_count = upload_timeclock(session)
        sched_count = upload_schedules(session)
        
        elapsed = time.time() - start_time
        
        # Final summary
        print("\n" + "=" * 60)
        print("✓ UPLOAD COMPLETE!")
        print("=" * 60)
        print(f"Total time: {elapsed:.1f} seconds")
        print(f"Total records uploaded:")
        print(f"  Transactions: {trans_count:,}")
        print(f"  Time Clock: {tc_count:,}")
        print(f"  Schedules: {sched_count:,}")
        
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
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        session.rollback()
        import traceback
        traceback.print_exc()
        
    finally:
        session.close()

if __name__ == "__main__":
    main() 