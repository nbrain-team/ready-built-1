#!/usr/bin/env python3
"""
Upload just a single day of data (Jan 2, 2025) for testing
Clears existing data first to ensure clean upload
"""

import os
import sys
import pandas as pd
from datetime import date
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

# Target date: Jan 2, 2025 (since Jan 1 has no data)
TARGET_DATE = date(2025, 1, 2)

def clear_existing_data():
    """Clear existing data from the database"""
    print("\n" + "=" * 60)
    print("CLEARING EXISTING DATA")
    print("=" * 60)
    
    session = Session()
    
    try:
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
                
    except Exception as e:
        print(f"  ❌ Error clearing data: {e}")
        session.rollback()
    finally:
        session.close()

def upload_single_day_transactions():
    """Upload transactions for the target date"""
    print(f"\n📊 Processing Transactions for {TARGET_DATE}...")
    
    session = Session()
    count = 0
    errors = 0
    duplicates = 0
    
    try:
        # Read the CSV file
        df = pd.read_csv('blazer/Detailed Line Item 2025 071825.csv')
        
        # Parse dates and filter for target date
        df['Sale Date'] = pd.to_datetime(df['Sale Date'], errors='coerce')
        df = df[df['Sale Date'].notna()]
        df = df[df['Sale Date'].dt.date == TARGET_DATE]
        
        # Skip summary rows
        df = df[df['Sale id'] != 'All']
        df = df[df['Sale id'].notna()]
        
        print(f"  Found {len(df)} transactions for {TARGET_DATE}")
        
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
                
                # Insert transaction (without ON CONFLICT since we cleared the table)
                session.execute(
                    text("""INSERT INTO salon_transactions 
                    (sale_id, location_id, sale_date, client_name, 
                     staff_id, service_name, sale_type, 
                     net_service_sales, net_sales, created_at)
                    VALUES (:sale_id, :loc, :sale_date, :client, 
                            :staff, :service, :sale_type,
                            :net_service, :net_sales, NOW())"""),
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
                
                # Commit every 10 records
                if count % 10 == 0:
                    session.commit()
                    print(f"    Processed {count} transactions...", end='\r')
                    
            except Exception as e:
                if "duplicate key" in str(e):
                    duplicates += 1
                else:
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
        print(f"\n  ✅ Uploaded {count} transactions")
        
        if errors > 0:
            print(f"  ⚠️  {errors} errors occurred")
        if duplicates > 0:
            print(f"  ⚠️  {duplicates} duplicates skipped")
        
    except Exception as e:
        print(f"\n  ❌ Error processing transactions: {e}")
        session.rollback()
    finally:
        session.close()
    
    return count

def verify_upload():
    """Verify the upload was successful"""
    print("\n" + "=" * 60)
    print("VERIFICATION")
    print("=" * 60)
    
    session = Session()
    
    try:
        # Check transaction count for the date
        result = session.execute(text("""
            SELECT COUNT(*) as count,
                   MIN(net_sales) as min_sales,
                   MAX(net_sales) as max_sales,
                   AVG(net_sales) as avg_sales
            FROM salon_transactions 
            WHERE sale_date = :target_date
        """), {"target_date": TARGET_DATE})
        
        row = result.first()
        print(f"\nTransactions for {TARGET_DATE}:")
        print(f"  Count: {row.count}")
        print(f"  Min sales: ${row.min_sales:.2f}")
        print(f"  Max sales: ${row.max_sales:.2f}")
        print(f"  Avg sales: ${row.avg_sales:.2f}")
        
        # Show sample transactions
        result = session.execute(text("""
            SELECT sale_id, location_id, client_name, net_sales
            FROM salon_transactions 
            WHERE sale_date = :target_date
            ORDER BY net_sales DESC
            LIMIT 5
        """), {"target_date": TARGET_DATE})
        
        print("\nTop 5 transactions by sales:")
        for row in result:
            print(f"  {row.sale_id[:20]}... - ${row.net_sales:.2f} - {row.client_name[:30]}")
            
    except Exception as e:
        print(f"Error during verification: {e}")
    finally:
        session.close()

def main():
    print("=" * 60)
    print("SINGLE DAY UPLOAD TEST")
    print(f"Target Date: {TARGET_DATE}")
    print("=" * 60)
    
    # Ask for confirmation
    print("\n⚠️  WARNING: This will DELETE all existing transaction data!")
    print("Press Enter to continue or Ctrl+C to cancel...")
    try:
        input()
    except KeyboardInterrupt:
        print("\nCancelled.")
        return
    
    start_time = time.time()
    
    # Clear existing data
    clear_existing_data()
    
    # Upload single day
    count = upload_single_day_transactions()
    
    # Verify
    if count > 0:
        verify_upload()
    
    elapsed = time.time() - start_time
    
    print("\n" + "=" * 60)
    print("✅ SINGLE DAY UPLOAD COMPLETE")
    print("=" * 60)
    print(f"Time taken: {elapsed:.1f} seconds")
    print(f"Records uploaded: {count}")

if __name__ == "__main__":
    main() 