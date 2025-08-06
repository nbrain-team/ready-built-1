#!/usr/bin/env python3
"""
Test script - upload just 100 records with detailed debugging
"""

import os
import sys
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import traceback

# Database URL
DATABASE_URL = os.getenv('DATABASE_URL', '')

if not DATABASE_URL:
    print("Please set your DATABASE_URL environment variable")
    sys.exit(1)

# Create engine
engine = create_engine(DATABASE_URL, pool_pre_ping=True, echo=False)
Session = sessionmaker(bind=engine)

def check_database_state(session):
    """Check current database state"""
    print("\n" + "=" * 60)
    print("CURRENT DATABASE STATE")
    print("=" * 60)
    
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
    
    # Check if there are any 2025 transactions
    result = session.execute(text("""
        SELECT COUNT(*) as count, 
               MIN(sale_date) as min_date, 
               MAX(sale_date) as max_date
        FROM salon_transactions
        WHERE EXTRACT(YEAR FROM sale_date) = 2025
    """))
    row = result.first()
    if row and row.count > 0:
        print(f"\n  2025 Transactions: {row.count:,} records")
        print(f"  Date range: {row.min_date} to {row.max_date}")

def test_small_batch(session):
    """Test uploading just 100 records"""
    print("\n" + "=" * 60)
    print("TESTING SMALL BATCH UPLOAD")
    print("=" * 60)
    
    file_path = 'blazer/Detailed Line Item 2025 071825.csv'
    
    # Read just first 100 non-summary rows
    print(f"\nReading first 100 rows from {file_path}...")
    df = pd.read_csv(file_path, nrows=500)  # Read extra to account for summary rows
    
    # Filter out summary rows
    df = df[df['Sale id'] != 'All']
    df = df[df['Sale id'].notna()]
    df = df.head(100)
    
    print(f"Found {len(df)} valid rows to process")
    
    # Show sample data
    print("\nSample data (first 3 rows):")
    print(df[['Sale id', 'Sale Date', 'Location Name', 'Staff Name', 'Net Sales']].head(3))
    
    # Process each row
    success_count = 0
    error_count = 0
    duplicate_count = 0
    
    for idx, row in df.iterrows():
        try:
            sale_id = row.get('Sale id')
            
            # Check if this sale_id already exists
            existing = session.execute(
                text("SELECT 1 FROM salon_transactions WHERE sale_id = :sale_id"),
                {"sale_id": sale_id}
            ).first()
            
            if existing:
                duplicate_count += 1
                if duplicate_count <= 3:  # Show first 3 duplicates
                    print(f"\n  Duplicate: Sale ID {sale_id} already exists")
                continue
            
            # Parse date
            sale_date = pd.to_datetime(row.get('Sale Date'), errors='coerce')
            if pd.isna(sale_date):
                print(f"\n  Invalid date for Sale ID {sale_id}")
                error_count += 1
                continue
            
            # Get location
            location_name = row.get('Location Name', '')
            if not location_name:
                print(f"\n  Missing location for Sale ID {sale_id}")
                error_count += 1
                continue
            
            # Get or create location
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
                print(f"\n  Created new location: {location_name} (ID: {location_id})")
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
                
                if not staff_id and success_count < 3:  # Log first few missing staff
                    print(f"  Staff '{staff_name}' not found in database")
            
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
            
            success_count += 1
            
            # Show details for first successful insert
            if success_count == 1:
                print(f"\n✅ First successful insert:")
                print(f"   Sale ID: {sale_id}")
                print(f"   Date: {sale_date.date()}")
                print(f"   Location: {location_name}")
                print(f"   Staff: {staff_name or 'None'}")
                print(f"   Net Sales: ${float(row.get('Net Sales', 0)):,.2f}")
            
        except Exception as e:
            error_count += 1
            if error_count <= 3:  # Show first 3 errors
                print(f"\n❌ Error with row {idx}:")
                print(f"   Sale ID: {sale_id}")
                print(f"   Error: {str(e)}")
                if "duplicate key" not in str(e):
                    traceback.print_exc()
    
    # Commit if any successes
    if success_count > 0:
        session.commit()
        print(f"\n✅ Committed {success_count} new records")
    
    # Summary
    print(f"\n" + "-" * 40)
    print(f"Summary:")
    print(f"  Successful inserts: {success_count}")
    print(f"  Duplicates skipped: {duplicate_count}")
    print(f"  Errors: {error_count}")
    print(f"  Total processed: {success_count + duplicate_count + error_count}")

def main():
    print("=" * 60)
    print("DATABASE TEST - SMALL BATCH")
    print("=" * 60)
    print(f"Database: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'configured'}")
    
    session = Session()
    
    try:
        # Test connection
        result = session.execute(text("SELECT 1"))
        print("✓ Database connection successful")
        
        # Check current state
        check_database_state(session)
        
        # Test small batch
        test_small_batch(session)
        
        # Check final state
        print("\n" + "=" * 60)
        print("FINAL DATABASE STATE")
        print("=" * 60)
        
        result = session.execute(text("SELECT COUNT(*) FROM salon_transactions"))
        count = result.scalar()
        print(f"Total transactions: {count:,}")
        
        # Show last 5 inserted transactions
        result = session.execute(text("""
            SELECT sale_id, sale_date, location_id, net_sales 
            FROM salon_transactions 
            ORDER BY created_at DESC 
            LIMIT 5
        """))
        
        print("\nLast 5 transactions:")
        for row in result:
            print(f"  {row.sale_id}: {row.sale_date} - ${row.net_sales:,.2f}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        session.rollback()
        traceback.print_exc()
        
    finally:
        session.close()

if __name__ == "__main__":
    main() 