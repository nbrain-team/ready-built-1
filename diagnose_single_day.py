#!/usr/bin/env python3
"""
Diagnose issues with single day upload
"""

import os
import sys
import pandas as pd
from datetime import date
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

# Database URL
DATABASE_URL = os.getenv('DATABASE_URL', '')

if not DATABASE_URL:
    print("Please set your DATABASE_URL environment variable")
    sys.exit(1)

# Create engine with NullPool
engine = create_engine(DATABASE_URL, poolclass=NullPool)
Session = sessionmaker(bind=engine)

# Target date: Jan 1, 2025
TARGET_DATE = date(2025, 1, 1)

def check_database_state():
    """Check current database state"""
    session = Session()
    print("=" * 60)
    print("DATABASE STATE CHECK")
    print("=" * 60)
    
    try:
        # Check table counts
        print("\n1. Current record counts:")
        tables = [
            ('salon_locations', 'Locations'),
            ('salon_staff', 'Staff'),
            ('salon_transactions', 'Transactions'),
            ('salon_time_clock', 'Time Clock'),
            ('salon_schedules', 'Schedules')
        ]
        
        for table, name in tables:
            result = session.execute(text(f"SELECT COUNT(*) FROM {table}"))
            count = result.scalar()
            print(f"   {name}: {count:,} records")
        
        # Check for Jan 1, 2025 data specifically
        print(f"\n2. Checking for {TARGET_DATE} data:")
        
        # Transactions
        result = session.execute(text("""
            SELECT COUNT(*) as count, 
                   COUNT(DISTINCT sale_id) as unique_sales
            FROM salon_transactions 
            WHERE sale_date = :target_date
        """), {"target_date": TARGET_DATE})
        row = result.first()
        print(f"   Transactions: {row.count} records ({row.unique_sales} unique sale_ids)")
        
        # Time Clock
        result = session.execute(text("""
            SELECT COUNT(*) as count
            FROM salon_time_clock 
            WHERE clock_date = :target_date
        """), {"target_date": TARGET_DATE})
        count = result.scalar()
        print(f"   Time Clock: {count} records")
        
        # Schedules
        result = session.execute(text("""
            SELECT COUNT(*) as count
            FROM salon_schedules 
            WHERE schedule_date = :target_date
        """), {"target_date": TARGET_DATE})
        count = result.scalar()
        print(f"   Schedules: {count} records")
        
    except Exception as e:
        print(f"Error checking database: {e}")
    finally:
        session.close()

def analyze_csv_data():
    """Analyze what's in the CSV files for the target date"""
    print("\n" + "=" * 60)
    print("CSV FILE ANALYSIS")
    print("=" * 60)
    
    # Check transactions
    print(f"\n1. Analyzing transactions for {TARGET_DATE}:")
    try:
        df = pd.read_csv('blazer/Detailed Line Item 2025 071825.csv', nrows=10000)
        df['Sale Date'] = pd.to_datetime(df['Sale Date'], errors='coerce')
        
        # Filter for target date
        target_data = df[df['Sale Date'].dt.date == TARGET_DATE]
        
        # Skip summary rows
        target_data = target_data[target_data['Sale id'] != 'All']
        target_data = target_data[target_data['Sale id'].notna()]
        
        print(f"   Found {len(target_data)} transactions")
        
        if len(target_data) > 0:
            print("\n   Sample transactions:")
            for idx, row in target_data.head(3).iterrows():
                print(f"   - Sale ID: {row['Sale id']}")
                print(f"     Location: {row.get('Location Name', 'N/A')}")
                print(f"     Staff: {row.get('Staff Name', 'N/A')}")
                print(f"     Net Sales: ${row.get('Net Sales', 0)}")
                print()
    except Exception as e:
        print(f"   Error analyzing transactions: {e}")
    
    # Check time clock
    print(f"\n2. Analyzing time clock for {TARGET_DATE}:")
    try:
        df = pd.read_csv('blazer/Time Clock Data 2025 071825.csv', nrows=5000)
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        
        target_data = df[df['Date'].dt.date == TARGET_DATE]
        print(f"   Found {len(target_data)} time clock entries")
        
        if len(target_data) > 0:
            print("\n   Sample entries:")
            for idx, row in target_data.head(3).iterrows():
                print(f"   - Employee: {row.get('Employee Name', 'N/A')}")
                print(f"     Clock In: {row.get('Clock In', 'N/A')}")
                print(f"     Clock Out: {row.get('Clock Out', 'N/A')}")
    except Exception as e:
        print(f"   Error analyzing time clock: {e}")

def test_single_insert():
    """Test inserting a single record"""
    print("\n" + "=" * 60)
    print("SINGLE INSERT TEST")
    print("=" * 60)
    
    session = Session()
    
    try:
        # First, ensure we have a test location
        result = session.execute(
            text("SELECT id FROM salon_locations WHERE name = 'Test Location'")
        ).first()
        
        if not result:
            print("Creating test location...")
            result = session.execute(
                text("INSERT INTO salon_locations (name, is_active, created_at) VALUES ('Test Location', true, NOW()) RETURNING id")
            )
            location_id = result.first()[0]
            session.commit()
            print(f"✓ Created location with ID: {location_id}")
        else:
            location_id = result[0]
            print(f"✓ Using existing location ID: {location_id}")
        
        # Try to insert a test transaction
        test_sale_id = f"TEST_{TARGET_DATE.strftime('%Y%m%d')}_001"
        
        # Check if it already exists
        exists = session.execute(
            text("SELECT 1 FROM salon_transactions WHERE sale_id = :id"),
            {"id": test_sale_id}
        ).first()
        
        if exists:
            print(f"Test sale ID {test_sale_id} already exists")
        else:
            session.execute(
                text("""INSERT INTO salon_transactions 
                (sale_id, location_id, sale_date, client_name, 
                 staff_id, service_name, sale_type, 
                 net_service_sales, net_sales, created_at)
                VALUES (:sale_id, :loc, :sale_date, :client, 
                        NULL, :service, :sale_type,
                        :net_service, :net_sales, NOW())"""),
                {
                    "sale_id": test_sale_id,
                    "loc": location_id,
                    "sale_date": TARGET_DATE,
                    "client": "Test Client",
                    "service": "Test Service",
                    "sale_type": "Service",
                    "net_service": 100.0,
                    "net_sales": 100.0
                }
            )
            session.commit()
            print(f"✓ Successfully inserted test transaction: {test_sale_id}")
        
        # Verify it's there
        result = session.execute(
            text("SELECT sale_id, net_sales FROM salon_transactions WHERE sale_id = :id"),
            {"id": test_sale_id}
        ).first()
        
        if result:
            print(f"✓ Verified: {result.sale_id} with net sales ${result.net_sales}")
        
    except Exception as e:
        print(f"❌ Error during test insert: {e}")
        session.rollback()
        import traceback
        traceback.print_exc()
    finally:
        session.close()

def check_for_duplicates():
    """Check if we're hitting duplicate key constraints"""
    print("\n" + "=" * 60)
    print("DUPLICATE CHECK")
    print("=" * 60)
    
    session = Session()
    
    try:
        # Read first few sale IDs from CSV
        df = pd.read_csv('blazer/Detailed Line Item 2025 071825.csv', nrows=100)
        df = df[df['Sale id'] != 'All']
        df = df[df['Sale id'].notna()]
        
        sample_ids = df['Sale id'].head(5).tolist()
        
        print("Checking if these sale IDs already exist in database:")
        for sale_id in sample_ids:
            result = session.execute(
                text("SELECT sale_date, net_sales FROM salon_transactions WHERE sale_id = :id"),
                {"id": sale_id}
            ).first()
            
            if result:
                print(f"  ✓ {sale_id}: EXISTS (date: {result.sale_date}, sales: ${result.net_sales})")
            else:
                print(f"  ✗ {sale_id}: NOT FOUND")
                
    except Exception as e:
        print(f"Error checking duplicates: {e}")
    finally:
        session.close()

def main():
    print("SINGLE DAY UPLOAD DIAGNOSTIC")
    print(f"Target Date: {TARGET_DATE}")
    print("=" * 60)
    
    # Run all diagnostics
    check_database_state()
    analyze_csv_data()
    test_single_insert()
    check_for_duplicates()
    
    print("\n" + "=" * 60)
    print("DIAGNOSTIC COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    main() 