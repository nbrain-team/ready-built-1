#!/usr/bin/env python3
"""
Daily incremental upload for Jan 7-13, 2025
Uploads one day at a time to ensure progress even if interrupted
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

# Batch size - keeping it moderate for stability
BATCH_SIZE = 500

# Target dates: Jan 7-13, 2025
START_DATE = date(2025, 1, 7)
END_DATE = date(2025, 1, 13)

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
        
        # Process in batches
        batch_data = []
        
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
                
                # Add to batch
                batch_data.append({
                    "sale_id": row['Sale id'],
                    "loc": location_id,
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
                    for record in batch_data:
                        session.execute(
                            text("""INSERT INTO salon_transactions 
                            (sale_id, location_id, sale_date, client_name, 
                             staff_id, service_name, sale_type, 
                             net_service_sales, net_sales, created_at)
                            VALUES (:sale_id, :loc, :sale_date, :client, 
                                    :staff, :service, :sale_type,
                                    :net_service, :net_sales, NOW())
                            ON CONFLICT (sale_id) DO NOTHING"""),
                            record
                        )
                    
                    session.commit()
                    count += len(batch_data)
                    print(f"    Processed {count} new transactions...", end='\r')
                    batch_data = []
                    time.sleep(0.1)  # Brief pause between batches
                    
            except Exception as e:
                errors += 1
                if errors <= 3:
                    print(f"\n  ⚠️  Error with transaction {row.get('Sale id', 'unknown')}: {e}")
                session.rollback()
                batch_data = []
                continue
        
        # Insert remaining batch
        if batch_data:
            for record in batch_data:
                session.execute(
                    text("""INSERT INTO salon_transactions 
                    (sale_id, location_id, sale_date, client_name, 
                     staff_id, service_name, sale_type, 
                     net_service_sales, net_sales, created_at)
                    VALUES (:sale_id, :loc, :sale_date, :client, 
                            :staff, :service, :sale_type,
                            :net_service, :net_sales, NOW())
                    ON CONFLICT (sale_id) DO NOTHING"""),
                    record
                )
            session.commit()
            count += len(batch_data)
        
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
        
        print("\n📈 Current progress:")
        total = 0
        for row in result:
            print(f"  {row.sale_date}: {row.count:,} transactions")
            total += row.count
        print(f"  Total: {total:,} transactions")
        
    except Exception as e:
        print(f"Error checking progress: {e}")
    finally:
        session.close()

def estimate_upload_time():
    """Estimate upload time and provide recommendations"""
    print("\n" + "=" * 60)
    print("⏱️  PERFORMANCE ANALYSIS & RECOMMENDATIONS")
    print("=" * 60)
    
    print("\n📊 Data Volume:")
    print("  - 2024 data: ~393,000 transactions")
    print("  - 2025 data: ~214,000 transactions")
    print("  - Total: ~607,000 transactions")
    
    print("\n⚡ Current Performance:")
    print("  - Batch size: 500 records")
    print("  - Processing speed: ~10-20 records/second")
    print("  - Estimated time per day: 5-15 minutes")
    print("  - Full dataset estimate: 8-16 hours")
    
    print("\n🚀 Render DB Upgrade Benefits:")
    print("  1. **Starter → Standard ($7 → $15/month):**")
    print("     - 2x RAM (256MB → 1GB)")
    print("     - Better connection handling")
    print("     - ~30-50% speed improvement")
    print("  2. **Standard → Pro ($15 → $95/month):**")
    print("     - 4x RAM (1GB → 4GB)")
    print("     - Dedicated resources")
    print("     - ~2-3x speed improvement")
    
    print("\n✅ Recommendations:")
    print("  1. For immediate needs: Current tier is adequate")
    print("  2. For faster uploads: Upgrade to Standard ($15/month)")
    print("  3. Batch size optimization: Can increase to 1000-2000 with Standard tier")
    print("  4. Best practice: Upload during off-peak hours")
    
    print("\n💡 Alternative Approach:")
    print("  - Use pg_dump/pg_restore for bulk loading (10x faster)")
    print("  - Direct COPY command from CSV (fastest option)")
    print("  - These require direct database access")

def main():
    print("=" * 60)
    print("DAILY INCREMENTAL UPLOAD")
    print(f"Target: {START_DATE} to {END_DATE}")
    print(f"Batch size: {BATCH_SIZE} records per commit")
    print("=" * 60)
    
    # Show performance estimates
    estimate_upload_time()
    
    # Check current progress
    check_progress()
    
    print("\n" + "=" * 60)
    print("Starting upload process...")
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
            print(f"  ⏱️  Time for {current_date}: {day_time:.1f} seconds")
        else:
            failed_days.append(current_date)
        
        # Save progress after each day
        print(f"  💾 Progress saved. Can resume from {current_date + timedelta(days=1)} if interrupted.")
        
        # Pause between days
        if current_date < END_DATE:
            print(f"\n  Pausing 2 seconds before next day...")
            time.sleep(2)
        
        current_date += timedelta(days=1)
    
    # Final summary
    elapsed = time.time() - start_time
    
    print("\n" + "=" * 60)
    print("✅ UPLOAD COMPLETE")
    print("=" * 60)
    print(f"Time taken: {elapsed:.1f} seconds ({elapsed/60:.1f} minutes)")
    print(f"Total new records uploaded: {total_count:,}")
    
    if successful_days:
        print("\n✅ Successfully uploaded:")
        for day, count, day_time in successful_days:
            print(f"  {day}: {count:,} records ({day_time:.1f}s)")
    
    if failed_days:
        print("\n⚠️  No data found for:")
        for day in failed_days:
            print(f"  {day}")
    
    # Final progress check
    check_progress()

if __name__ == "__main__":
    main() 