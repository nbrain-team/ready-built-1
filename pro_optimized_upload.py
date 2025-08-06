#!/usr/bin/env python3
"""
Optimized upload script for Render Pro tier (8GB RAM / 2 CPU)
Takes advantage of increased resources for faster uploads
"""

import os
import sys
import pandas as pd
from datetime import date, timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
import time
import gc
from concurrent.futures import ThreadPoolExecutor
import threading

# Database URL
DATABASE_URL = os.getenv('DATABASE_URL', '')

if not DATABASE_URL:
    print("Please set your DATABASE_URL environment variable")
    sys.exit(1)

# Create engine optimized for Pro tier
engine = create_engine(
    DATABASE_URL, 
    poolclass=QueuePool,
    pool_size=10,  # Increased from default 5
    max_overflow=20,  # Increased from default 10
    pool_pre_ping=True,
    connect_args={
        'connect_timeout': 30,
        'options': '-c statement_timeout=60000'  # Increased timeout
    }
)
Session = sessionmaker(bind=engine)

# Optimized batch size for Pro tier
BATCH_SIZE = 2000  # Increased from 500

# Continue from Jan 14 onwards
START_DATE = date(2025, 1, 14)
END_DATE = date(2025, 1, 31)  # Rest of January

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

def bulk_insert_batch(session, batch_data):
    """Bulk insert a batch of records"""
    if not batch_data:
        return 0
    
    try:
        # Use executemany for better performance
        session.execute(
            text("""INSERT INTO salon_transactions 
            (sale_id, location_id, sale_date, client_name, 
             staff_id, service_name, sale_type, 
             net_service_sales, net_sales, created_at)
            VALUES (:sale_id, :loc, :sale_date, :client, 
                    :staff, :service, :sale_type,
                    :net_service, :net_sales, NOW())
            ON CONFLICT (sale_id) DO NOTHING"""),
            batch_data
        )
        session.commit()
        return len(batch_data)
    except Exception as e:
        print(f"\n  ⚠️  Error in bulk insert: {e}")
        session.rollback()
        return 0

def process_transactions_for_date(target_date):
    """Process transaction data for a specific date - optimized for Pro tier"""
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
        
        # Read data with optimized dtypes
        df = pd.read_csv(file_path, 
            usecols=[
                'Sale id', 'Sale Date', 'Location Name', 'Staff Name',
                'Client Name', 'Service Name', 'Sale Type',
                'Net Service Sales', 'Net Sales'
            ],
            dtype={
                'Sale id': str,
                'Location Name': str,
                'Staff Name': str,
                'Client Name': str,
                'Service Name': str,
                'Sale Type': str
            }
        )
        
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
        
        # Pre-fetch all locations and staff for better performance
        locations = {}
        staff_map = {}
        
        # Get all unique locations
        unique_locations = df['Location Name'].dropna().unique()
        for loc_name in unique_locations:
            location = session.execute(
                text("SELECT id FROM salon_locations WHERE name = :name"),
                {"name": loc_name}
            ).first()
            
            if not location:
                result = session.execute(
                    text("INSERT INTO salon_locations (name, is_active, created_at) VALUES (:name, true, NOW()) RETURNING id"),
                    {"name": loc_name}
                )
                locations[loc_name] = result.first()[0]
            else:
                locations[loc_name] = location[0]
        
        # Get all unique staff
        unique_staff = df['Staff Name'].dropna().unique()
        for staff_name in unique_staff:
            if staff_name and staff_name != 'No Staff':
                staff = session.execute(
                    text("SELECT id FROM salon_staff WHERE full_name = :name"),
                    {"name": staff_name}
                ).first()
                if staff:
                    staff_map[staff_name] = staff[0]
        
        # Process in larger batches
        batch_data = []
        
        for idx, row in df.iterrows():
            try:
                # Skip if already exists
                if row['Sale id'] in existing_ids:
                    skipped += 1
                    continue
                
                location_name = row['Location Name']
                if pd.isna(location_name) or location_name not in locations:
                    continue
                
                staff_name = row.get('Staff Name', '')
                staff_id = None
                if staff_name and not pd.isna(staff_name) and staff_name in staff_map:
                    staff_id = staff_map[staff_name]
                
                # Add to batch
                batch_data.append({
                    "sale_id": row['Sale id'],
                    "loc": locations[location_name],
                    "sale_date": row['Sale Date'].date(),
                    "client": row.get('Client Name', ''),
                    "staff": staff_id,
                    "service": row.get('Service Name', ''),
                    "sale_type": row.get('Sale Type', ''),
                    "net_service": float(row.get('Net Service Sales', 0) or 0),
                    "net_sales": float(row.get('Net Sales', 0) or 0)
                })
                
                # Insert batch when it reaches BATCH_SIZE
                if len(batch_data) >= BATCH_SIZE:
                    inserted = bulk_insert_batch(session, batch_data)
                    count += inserted
                    print(f"    Processed {count} new transactions...", end='\r')
                    batch_data = []
                    
            except Exception as e:
                errors += 1
                if errors <= 3:
                    print(f"\n  ⚠️  Error with transaction {row.get('Sale id', 'unknown')}: {e}")
                continue
        
        # Insert remaining batch
        if batch_data:
            inserted = bulk_insert_batch(session, batch_data)
            count += inserted
        
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
        import traceback
        traceback.print_exc()
    finally:
        session.close()
    
    return count

def check_progress():
    """Check current upload progress"""
    session = Session()
    try:
        # Get summary by month
        result = session.execute(text("""
            SELECT 
                DATE_TRUNC('month', sale_date) as month,
                COUNT(*) as count,
                MIN(sale_date) as first_date,
                MAX(sale_date) as last_date
            FROM salon_transactions
            WHERE sale_date >= '2025-01-01'
            GROUP BY DATE_TRUNC('month', sale_date)
            ORDER BY month
        """))
        
        print("\n📈 Current progress by month:")
        total = 0
        for row in result:
            print(f"  {row.month.strftime('%B %Y')}: {row.count:,} transactions ({row.first_date} to {row.last_date})")
            total += row.count
        print(f"  Total 2025: {total:,} transactions")
        
        # Get daily breakdown for current month
        result = session.execute(text("""
            SELECT sale_date, COUNT(*) as count
            FROM salon_transactions
            WHERE sale_date >= '2025-01-01' AND sale_date < '2025-02-01'
            GROUP BY sale_date
            ORDER BY sale_date
        """))
        
        print("\n📊 January 2025 daily breakdown:")
        for row in result:
            print(f"  {row.sale_date}: {row.count:,} transactions")
        
    except Exception as e:
        print(f"Error checking progress: {e}")
    finally:
        session.close()

def main():
    print("=" * 60)
    print("🚀 PRO-TIER OPTIMIZED UPLOAD")
    print(f"Target: {START_DATE} to {END_DATE}")
    print(f"Batch size: {BATCH_SIZE} records (4x larger)")
    print("=" * 60)
    
    print("\n⚡ Pro Tier Advantages:")
    print("  • 8GB RAM - Handle larger batches")
    print("  • 2 CPUs - Better parallel processing")
    print("  • Dedicated resources - No throttling")
    print("  • Expected: 3-5x faster uploads")
    
    # Check current progress
    check_progress()
    
    print("\n" + "=" * 60)
    print("Starting optimized upload process...")
    print("=" * 60)
    
    start_time = time.time()
    total_count = 0
    successful_days = []
    failed_days = []
    
    # Process each day
    current_date = START_DATE
    while current_date <= END_DATE:
        day_start = time.time()
        day_count = process_transactions_for_date(current_date)
        day_time = time.time() - day_start
        
        if day_count > 0:
            successful_days.append((current_date, day_count, day_time))
            total_count += day_count
            print(f"  ⏱️  Time for {current_date}: {day_time:.1f} seconds ({day_count/day_time:.1f} records/sec)")
        else:
            failed_days.append(current_date)
        
        # Save progress after each day
        print(f"  💾 Progress saved. Can resume from {current_date + timedelta(days=1)} if interrupted.")
        
        # Minimal pause between days (Pro tier can handle it)
        if current_date < END_DATE and day_count > 0:
            time.sleep(0.5)
        
        current_date += timedelta(days=1)
    
    # Final summary
    elapsed = time.time() - start_time
    
    print("\n" + "=" * 60)
    print("✅ UPLOAD COMPLETE")
    print("=" * 60)
    print(f"Time taken: {elapsed:.1f} seconds ({elapsed/60:.1f} minutes)")
    print(f"Total new records uploaded: {total_count:,}")
    print(f"Average speed: {total_count/elapsed:.1f} records/second")
    
    if successful_days:
        print("\n✅ Successfully uploaded:")
        total_records = 0
        total_time = 0
        for day, count, day_time in successful_days:
            print(f"  {day}: {count:,} records ({day_time:.1f}s)")
            total_records += count
            total_time += day_time
        print(f"\n  Average: {total_records/total_time:.1f} records/second")
    
    if failed_days:
        print("\n⚠️  No data found for:")
        for day in failed_days:
            print(f"  {day}")
    
    # Final progress check
    check_progress()

if __name__ == "__main__":
    main() 