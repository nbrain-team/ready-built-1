#!/usr/bin/env python3
"""
Upload 6 more days of data (Jan 3-8, 2025) with double batch size
"""

import os
import sys
import pandas as pd
from datetime import date, timedelta
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

# Double the batch size from before (was 10, now 20)
BATCH_SIZE = 20

# Target dates: Jan 3-8, 2025
START_DATE = date(2025, 1, 3)
END_DATE = date(2025, 1, 8)

def process_transactions_for_date(target_date):
    """Process transaction data for a specific date"""
    print(f"\n📊 Processing Transactions for {target_date}...")
    
    file_path = 'blazer/Detailed Line Item 2025 071825.csv'
    session = Session()
    count = 0
    errors = 0
    
    try:
        # Read the CSV file
        df = pd.read_csv(file_path)
        
        # Parse dates and filter for target date
        df['Sale Date'] = pd.to_datetime(df['Sale Date'], errors='coerce')
        df = df[df['Sale Date'].notna()]
        df = df[df['Sale Date'].dt.date == target_date]
        
        # Skip summary rows
        df = df[df['Sale id'] != 'All']
        df = df[df['Sale id'].notna()]
        
        print(f"  Found {len(df)} transactions for {target_date}")
        
        if len(df) == 0:
            print("  No data found for this date!")
            return 0
        
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
                
                # Commit every BATCH_SIZE records (doubled from before)
                if count % BATCH_SIZE == 0:
                    session.commit()
                    print(f"    Processed {count} transactions...", end='\r')
                    time.sleep(0.3)  # Slightly shorter delay since batch is bigger
                    
            except Exception as e:
                errors += 1
                if errors <= 3:  # Show first 3 errors
                    print(f"\n  ⚠️  Error with transaction {row.get('Sale id', 'unknown')}: {e}")
                session.rollback()
                # Start a new session after rollback
                session.close()
                session = Session()
                continue
        
        # Final commit
        session.commit()
        print(f"\n  ✅ Uploaded {count} transactions for {target_date}")
        
        if errors > 0:
            print(f"  ⚠️  {errors} errors occurred")
        
    except Exception as e:
        print(f"\n  ❌ Error processing transactions: {e}")
        session.rollback()
    finally:
        session.close()
    
    return count

def check_final_state():
    """Check final database state after all uploads"""
    session = Session()
    try:
        print("\n" + "=" * 60)
        print("FINAL DATABASE STATE")
        print("=" * 60)
        
        # Transaction summary
        result = session.execute(text("""
            SELECT MIN(sale_date) as min_date, 
                   MAX(sale_date) as max_date,
                   COUNT(*) as total_count,
                   COUNT(DISTINCT sale_date) as unique_dates,
                   SUM(net_sales) as total_sales
            FROM salon_transactions
        """))
        row = result.first()
        if row and row.min_date:
            print(f"\nTransaction Summary:")
            print(f"  Date range: {row.min_date} to {row.max_date}")
            print(f"  Total transactions: {row.total_count:,}")
            print(f"  Unique dates: {row.unique_dates}")
            print(f"  Total sales: ${row.total_sales:,.2f}")
            
            # Daily breakdown
            print("\nDaily breakdown:")
            result = session.execute(text("""
                SELECT sale_date, COUNT(*) as count, SUM(net_sales) as daily_sales
                FROM salon_transactions
                GROUP BY sale_date
                ORDER BY sale_date
            """))
            for row in result:
                print(f"  {row.sale_date}: {row.count:,} transactions, ${row.daily_sales:,.2f}")
                
    except Exception as e:
        print(f"Error checking final state: {e}")
    finally:
        session.close()

def main():
    print("=" * 60)
    print("SIX DAY UPLOAD")
    print(f"Target: {START_DATE} to {END_DATE}")
    print(f"Batch size: {BATCH_SIZE} records per commit (doubled)")
    print("=" * 60)
    
    start_time = time.time()
    total_count = 0
    
    # Process each day
    current_date = START_DATE
    while current_date <= END_DATE:
        day_count = process_transactions_for_date(current_date)
        total_count += day_count
        
        # Pause between days
        if current_date < END_DATE:
            print(f"\n  Pausing before next day...")
            time.sleep(2)
        
        current_date += timedelta(days=1)
    
    # Final summary
    elapsed = time.time() - start_time
    
    print("\n" + "=" * 60)
    print("✅ SIX DAY UPLOAD COMPLETE")
    print("=" * 60)
    print(f"Time taken: {elapsed:.1f} seconds ({elapsed/60:.1f} minutes)")
    print(f"Total records uploaded: {total_count:,}")
    print(f"Average time per day: {elapsed/6:.1f} seconds")
    
    # Check final state
    check_final_state()

if __name__ == "__main__":
    main() 