#!/usr/bin/env python3
"""
Diagnose upload issues
"""

import os
import sys
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Database URL
DATABASE_URL = os.getenv('DATABASE_URL', '')

if not DATABASE_URL:
    print("Please set your DATABASE_URL environment variable")
    sys.exit(1)

# Create engine with echo=True to see SQL
engine = create_engine(DATABASE_URL, pool_pre_ping=True, echo=False)
Session = sessionmaker(bind=engine)

def diagnose():
    session = Session()
    
    print("=" * 60)
    print("DIAGNOSING UPLOAD ISSUES")
    print("=" * 60)
    
    # 1. Check database connection
    try:
        result = session.execute(text("SELECT version()"))
        version = result.scalar()
        print(f"✓ Database connected: PostgreSQL {version.split(',')[0]}")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return
    
    # 2. Check table structure
    print("\n2. Checking table structure...")
    try:
        result = session.execute(text("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_name = 'salon_transactions'
            ORDER BY ordinal_position
        """))
        
        print("\nColumns in salon_transactions:")
        for row in result:
            print(f"  - {row.column_name}: {row.data_type} (nullable: {row.is_nullable})")
    except Exception as e:
        print(f"❌ Error checking table structure: {e}")
    
    # 3. Check constraints
    print("\n3. Checking constraints...")
    try:
        result = session.execute(text("""
            SELECT constraint_name, constraint_type
            FROM information_schema.table_constraints
            WHERE table_name = 'salon_transactions'
        """))
        
        print("\nConstraints on salon_transactions:")
        for row in result:
            print(f"  - {row.constraint_name}: {row.constraint_type}")
    except Exception as e:
        print(f"❌ Error checking constraints: {e}")
    
    # 4. Check existing data
    print("\n4. Checking existing data...")
    try:
        # Count by date
        result = session.execute(text("""
            SELECT sale_date, COUNT(*) as count
            FROM salon_transactions
            GROUP BY sale_date
            ORDER BY sale_date
            LIMIT 10
        """))
        
        print("\nFirst 10 dates with data:")
        for row in result:
            print(f"  {row.sale_date}: {row.count} records")
        
        # Check for specific sale_ids from our file
        print("\n5. Checking if specific records exist...")
        df = pd.read_csv('blazer/Detailed Line Item 2025 071825.csv', nrows=10)
        
        for idx, row in df.iterrows():
            if idx >= 5:  # Just check first 5
                break
            
            sale_id = row.get('Sale id')
            if sale_id and sale_id != 'All':
                result = session.execute(
                    text("SELECT 1 FROM salon_transactions WHERE sale_id = :id"),
                    {"id": sale_id}
                ).first()
                
                exists = "EXISTS" if result else "NOT EXISTS"
                print(f"  Sale ID {sale_id}: {exists}")
    except Exception as e:
        print(f"❌ Error checking data: {e}")
    
    # 6. Try a test insert
    print("\n6. Testing insert capability...")
    try:
        # First, get a location ID
        result = session.execute(text("SELECT id FROM salon_locations LIMIT 1"))
        location_id = result.scalar()
        
        if not location_id:
            print("  Creating test location...")
            result = session.execute(
                text("INSERT INTO salon_locations (name, is_active, created_at) VALUES ('Test Location', true, NOW()) RETURNING id")
            )
            location_id = result.scalar()
            session.commit()
        
        # Try to insert a test record
        test_sale_id = f"TEST_{pd.Timestamp.now().strftime('%Y%m%d%H%M%S')}"
        
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
                "sale_date": pd.Timestamp.now().date(),
                "client": "Test Client",
                "service": "Test Service",
                "sale_type": "Service",
                "net_service": 100.0,
                "net_sales": 100.0
            }
        )
        session.commit()
        print(f"  ✓ Test insert successful: {test_sale_id}")
        
        # Delete the test record
        session.execute(
            text("DELETE FROM salon_transactions WHERE sale_id = :id"),
            {"id": test_sale_id}
        )
        session.commit()
        print("  ✓ Test record deleted")
        
    except Exception as e:
        print(f"  ❌ Test insert failed: {e}")
        session.rollback()
    
    # 7. Check for any database errors/locks
    print("\n7. Checking for database locks...")
    try:
        result = session.execute(text("""
            SELECT pid, usename, application_name, state, query_start, state_change
            FROM pg_stat_activity
            WHERE datname = current_database()
            AND state != 'idle'
            AND pid != pg_backend_pid()
        """))
        
        active = list(result)
        if active:
            print(f"  Found {len(active)} active connections")
            for row in active:
                print(f"    PID {row.pid}: {row.state} - {row.application_name}")
        else:
            print("  No blocking connections found")
            
    except Exception as e:
        print(f"  Error checking locks: {e}")
    
    session.close()
    print("\n" + "=" * 60)
    print("Diagnosis complete!")

if __name__ == "__main__":
    diagnose() 