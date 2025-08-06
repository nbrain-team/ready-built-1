#!/usr/bin/env python3
"""
Clear existing data and upload fresh in weekly batches
"""

import os
import sys
import pandas as pd
from datetime import datetime, timedelta
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
    print("\n" + "=" * 60)
    print("CLEARING EXISTING DATA")
    print("=" * 60)
    
    tables = [
        ('salon_transactions', 'Transactions'),
        ('salon_time_clock', 'Time Clock'),
        ('salon_schedules', 'Schedules')
    ]
    
    for table, name in tables:
        result = session.execute(text(f"SELECT COUNT(*) FROM {table}"))
        count = result.scalar()
        if count > 0:
            print(f"  Clearing {count:,} records from {name}...")
            session.execute(text(f"DELETE FROM {table}"))
            session.commit()
            print(f"  ✓ Cleared {name}")
        else:
            print(f"  {name}: Already empty")

def upload_week_batch(session, file_path, week_start, week_end):
    """Upload one week of transaction data"""
    week_str = f"{week_start.strftime('%Y-%m-%d')} to {week_end.strftime('%Y-%m-%d')}"
    
    # Read file in chunks
    chunk_size = 1000
    total_count = 0
    
    for chunk_num, chunk in enumerate(pd.read_csv(file_path, chunksize=chunk_size), 1):
        chunk_count = 0
        
        # Filter for this week only
        chunk['Sale Date'] = pd.to_datetime(chunk['Sale Date'], errors='coerce')
        week_data = chunk[(chunk['Sale Date'] >= week_start) & (chunk['Sale Date'] <= week_end)]
        
        # Skip if no data for this week
        if len(week_data) == 0:
            continue
        
        for _, row in week_data.iterrows():
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
                        "sale_date": row['Sale Date'].date(),
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
    
    if total_count > 0:
        print(f"  Week {week_str}: {total_count:,} records")
    
    return total_count

def main():
    print("=" * 60)
    print("CLEAR AND UPLOAD - 2025 DATA")
    print("=" * 60)
    print(f"Database: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'configured'}")
    
    session = Session()
    
    try:
        # Test connection
        result = session.execute(text("SELECT 1"))
        print("✓ Database connection successful")
        
        # Clear existing data
        clear_tables(session)
        
        # Upload transactions by week
        print("\n" + "=" * 60)
        print("UPLOADING 2025 TRANSACTIONS BY WEEK")
        print("=" * 60)
        
        file_path = 'blazer/Detailed Line Item 2025 071825.csv'
        
        # Define weeks to upload (Jan 1 - July 31, 2025)
        start_date = datetime(2025, 1, 1)
        end_date = datetime(2025, 7, 31)
        
        total_uploaded = 0
        current_date = start_date
        
        while current_date <= end_date:
            # Get week start (Monday) and end (Sunday)
            week_start = current_date - timedelta(days=current_date.weekday())
            week_end = week_start + timedelta(days=6)
            
            # Upload this week
            count = upload_week_batch(session, file_path, week_start, week_end)
            total_uploaded += count
            
            # Move to next week
            current_date = week_end + timedelta(days=1)
            
            # Small delay between weeks
            if count > 0:
                time.sleep(0.1)
        
        # Final summary
        print("\n" + "=" * 60)
        print("✓ UPLOAD COMPLETE!")
        print("=" * 60)
        print(f"Total transactions uploaded: {total_uploaded:,}")
        
        # Verify in database
        result = session.execute(text("SELECT COUNT(*) FROM salon_transactions"))
        db_count = result.scalar()
        print(f"Total in database: {db_count:,}")
        
        # Show date range
        result = session.execute(text("""
            SELECT MIN(sale_date) as min_date, MAX(sale_date) as max_date
            FROM salon_transactions
        """))
        row = result.first()
        if row:
            print(f"Date range: {row.min_date} to {row.max_date}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        session.rollback()
        import traceback
        traceback.print_exc()
        
    finally:
        session.close()

if __name__ == "__main__":
    # Confirm with user
    print("\n⚠️  WARNING: This will DELETE all existing transaction data!")
    print("Press Ctrl+C to cancel, or Enter to continue...")
    try:
        input()
    except KeyboardInterrupt:
        print("\nCancelled.")
        sys.exit(0)
    
    main() 