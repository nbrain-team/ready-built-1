#!/usr/bin/env python3
"""
Check what data is currently in the database
"""

import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Database URL
DATABASE_URL = os.getenv('DATABASE_URL', '')

if not DATABASE_URL:
    print("Please set your DATABASE_URL environment variable")
    exit(1)

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

def check_current_data():
    """Check current database state"""
    session = Session()
    
    print("=" * 60)
    print("CURRENT DATABASE STATE")
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
        
        # Check transaction date ranges
        print("\n2. Transaction date ranges:")
        result = session.execute(text("""
            SELECT MIN(sale_date) as min_date, 
                   MAX(sale_date) as max_date,
                   COUNT(DISTINCT sale_date) as unique_dates
            FROM salon_transactions
        """))
        row = result.first()
        if row and row.min_date:
            print(f"   Date range: {row.min_date} to {row.max_date}")
            print(f"   Unique dates: {row.unique_dates}")
            
            # Show daily breakdown
            print("\n3. Daily transaction breakdown:")
            result = session.execute(text("""
                SELECT sale_date, COUNT(*) as count
                FROM salon_transactions
                GROUP BY sale_date
                ORDER BY sale_date
                LIMIT 10
            """))
            for row in result:
                print(f"   {row.sale_date}: {row.count} transactions")
        else:
            print("   No transaction data found")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    check_current_data() 