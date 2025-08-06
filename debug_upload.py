#!/usr/bin/env python3
"""
Debug script to understand why uploads are failing
"""

import os
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv('DATABASE_URL', '')

if not DATABASE_URL:
    print("Please set your DATABASE_URL environment variable")
    exit(1)

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

def test_upload():
    session = Session()
    
    print("=" * 60)
    print("DEBUG UPLOAD TEST")
    print("=" * 60)
    
    try:
        # Read first 5 transaction rows
        df = pd.read_csv('blazer/Detailed Line Item 2024.csv', nrows=10)
        data_rows = df[df['Sale id'] != 'All']
        
        print(f"\nTesting with {len(data_rows)} rows...")
        print("\nFirst row data:")
        first_row = data_rows.iloc[0]
        for col in first_row.index:
            print(f"  {col}: {first_row[col]}")
        
        success_count = 0
        
        for idx, row in data_rows.iterrows():
            try:
                sale_id = row.get('Sale id')
                if sale_id == 'All' or pd.isna(sale_id):
                    continue
                
                # Get or create location
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
                    session.commit()
                    print(f"\n✓ Created location: {location_name} (ID: {location_id})")
                else:
                    location_id = location[0]
                    print(f"\n✓ Found location: {location_name} (ID: {location_id})")
                
                # Parse date
                sale_date = pd.to_datetime(row.get('Sale Date'), errors='coerce')
                if pd.isna(sale_date):
                    print(f"  ✗ Invalid date: {row.get('Sale Date')}")
                    continue
                
                # Try insert WITHOUT ON CONFLICT to see actual error
                print(f"\nInserting sale_id: {sale_id}")
                session.execute(
                    text("""INSERT INTO salon_transactions 
                    (sale_id, location_id, sale_date, client_name, 
                     staff_id, service_name, sale_type, 
                     net_service_sales, net_sales, created_at)
                    VALUES (:sale_id, :loc, :sale_date, :client, 
                            NULL, :service, :sale_type,
                            :net_service, :net_sales, NOW())"""),
                    {
                        "sale_id": str(sale_id),  # Ensure it's a string
                        "loc": location_id,
                        "sale_date": sale_date.date(),
                        "client": row.get('Client Name', ''),
                        "service": row.get('Service Name', ''),
                        "sale_type": row.get('Sale Type', ''),
                        "net_service": float(row.get('Net Service Sales', 0) or 0),
                        "net_sales": float(row.get('Net Sales', 0) or 0)
                    }
                )
                session.commit()
                success_count += 1
                print(f"  ✓ Successfully inserted!")
                
            except Exception as e:
                session.rollback()
                print(f"  ✗ Error: {e}")
                
                # Check if record already exists
                existing = session.execute(
                    text("SELECT sale_id, sale_date FROM salon_transactions WHERE sale_id = :id"),
                    {"id": str(sale_id)}
                ).first()
                
                if existing:
                    print(f"  → Record already exists: {existing.sale_id} ({existing.sale_date})")
        
        print(f"\n✓ Successfully inserted {success_count} records")
        
        # Show current counts
        print("\nCurrent database state:")
        result = session.execute(text("SELECT COUNT(*) FROM salon_transactions"))
        count = result.scalar()
        print(f"  Total transactions: {count}")
        
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    test_upload() 