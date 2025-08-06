#!/usr/bin/env python3
"""
Lightweight upload with 100 records per batch
Continues from Jan 4, 2025 (which has partial data)
"""

import os
import sys
import pandas as pd
from datetime import date, timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
import time
import gc

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

# Large batch size as requested
BATCH_SIZE = 100

# Continue from Jan 4 (partial) through Jan 9
START_DATE = date(2025, 1, 4)  # This date has partial data
END_DATE = date(2025, 1, 9)

def get_existing_sale_ids(session, target_date):
    """Get existing sale IDs for a date to avoid duplicates"""
    result = session.execute(
        text("""
        SELECT sale_id 
        FROM salon_transactions 
        WHERE sale_date = :target_date
        """),
        {"target_date": target_date}
    )
    return set(row[0] for row in result)

def process_transactions_for_date(target_date):
    """Process transaction data for a specific date"""
    print(f"\n📊 Processing Transactions for {target_date}...")
    
    file_path = 'blazer/Detailed Line Item 2025 071825.csv'
    session = Session()
    count = 0
    skipped = 0
    errors = 0
    
    try:
        # Get existing sale IDs to skip
        existing_ids = get_existing_sale_ids(session, target_date)
        if existing_ids:
            print(f"  Found {len(existing_ids)} existing transactions, will skip these")
        
        # Read only needed columns to save memory
        df = pd.read_csv(file_path, usecols=[
            'Sale id', 'Sale Date', 'Location Name', 'Staff Name',
            'Client Name', 'Service Name', 'Sale Type',
            'Net Service Sales', 'Net Sales'
        ])
        
        # Parse dates and filter for target date
        df['Sale Date'] = pd.to_datetime(df['Sale Date'], errors='coerce')
        df = df[df['Sale Date'].notna()]
        df = df[df['Sale Date'].dt.date == target_date]
        
        # Skip summary rows
        df = df[df['Sale id'] != 'All']
        df = df[df['Sale id'].notna()]
        
        print(f"  Found {len(df)} total transactions for {target_date}")
        
        if len(df) == 0:
            print("  No data found for this date!")
            return 0
        
        # Process each transaction
        for idx, row in df.iterrows():
            try:
                # Skip if already exists
                if row['Sale id'] in existing_ids:
                    skipped += 1
                    continue
                
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
                
                # Commit every BATCH_SIZE records
                if count % BATCH_SIZE == 0:
                    session.commit()
                    print(f"    Processed {count} new transactions...", end='\r')
                    time.sleep(0.1)  # Very short delay
                    
            except Exception as e:
                errors += 1
                if errors <= 3:
                    print(f"\n  ⚠️  Error with transaction {row.get('Sale id', 'unknown')}: {e}")
                session.rollback()
                session.close()
                session = Session()
                continue
        
        # Final commit
        session.commit()
        
        # Clear dataframe from memory
        del df
        gc.collect()
        
        print(f"\n  ✅ Uploaded {count} new transactions for {target_date}")
        if skipped > 0:
            print(f"  ℹ️  Skipped {skipped} existing transactions")
        if errors > 0:
            print(f"  ⚠️  {errors} errors occurred")
        
    except Exception as e:
        print(f"\n  ❌ Error processing transactions: {e}")
        session.rollback()
    finally:
        session.close()
    
    return count

def check_progress():
    """Check current upload progress"""
    session = Session()
    try:
        result = session.execute(text("""
            SELECT sale_date, COUNT(*) as count
            FROM salon_transactions
            WHERE sale_date >= '2025-01-01'
            GROUP BY sale_date
            ORDER BY sale_date
        """))
        
        print("\nCurrent progress:")
        total = 0
        for row in result:
            print(f"  {row.sale_date}: {row.count:,} transactions")
            total += row.count
        print(f"  Total: {total:,} transactions")
        
    except Exception as e:
        print(f"Error checking progress: {e}")
    finally:
        session.close()

def main():
    print("=" * 60)
    print("LIGHTWEIGHT BATCH UPLOAD")
    print(f"Target: {START_DATE} to {END_DATE}")
    print(f"Batch size: {BATCH_SIZE} records per commit")
    print("=" * 60)
    
    # Check current progress
    check_progress()
    
    start_time = time.time()
    total_count = 0
    
    # Process each day
    current_date = START_DATE
    while current_date <= END_DATE:
        day_count = process_transactions_for_date(current_date)
        total_count += day_count
        
        # Pause between days
        if current_date < END_DATE and day_count > 0:
            print(f"\n  Pausing before next day...")
            time.sleep(1)
        
        current_date += timedelta(days=1)
    
    # Final summary
    elapsed = time.time() - start_time
    
    print("\n" + "=" * 60)
    print("✅ UPLOAD COMPLETE")
    print("=" * 60)
    print(f"Time taken: {elapsed:.1f} seconds ({elapsed/60:.1f} minutes)")
    print(f"Total new records uploaded: {total_count:,}")
    
    # Final progress check
    check_progress()

if __name__ == "__main__":
    main() 