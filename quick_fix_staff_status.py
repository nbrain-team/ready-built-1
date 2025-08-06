#!/usr/bin/env python3
"""
Quick fix to update staff status from 'A - Active' to 'A'
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

def fix_staff_status():
    """Update staff status to match what the code expects"""
    session = Session()
    
    print("=" * 60)
    print("QUICK FIX: STAFF STATUS")
    print("=" * 60)
    
    try:
        # Check current status
        print("\n1. Current staff status distribution:")
        result = session.execute(text("""
            SELECT position_status, COUNT(*) as count
            FROM salon_staff
            GROUP BY position_status
            ORDER BY position_status
        """))
        
        for row in result:
            status = row.position_status or 'NULL'
            print(f"   {status}: {row.count} staff")
        
        # Update 'A - Active' to 'A'
        print("\n2. Updating staff status...")
        result = session.execute(text("""
            UPDATE salon_staff 
            SET position_status = 'A' 
            WHERE position_status = 'A - Active'
        """))
        
        rows_updated = result.rowcount
        session.commit()
        print(f"   ✓ Updated {rows_updated} staff records")
        
        # Verify the fix
        print("\n3. New staff status distribution:")
        result = session.execute(text("""
            SELECT position_status, COUNT(*) as count
            FROM salon_staff
            GROUP BY position_status
            ORDER BY position_status
        """))
        
        active_count = 0
        for row in result:
            status = row.position_status or 'NULL'
            print(f"   {status}: {row.count} staff")
            if status == 'A':
                active_count = row.count
        
        print("\n" + "=" * 60)
        print("✅ FIX COMPLETE")
        print("=" * 60)
        print(f"Active staff will now show as: {active_count}")
        print("\nRefresh your dashboard to see the updated active staff count!")
        
    except Exception as e:
        print(f"\nError: {e}")
        session.rollback()
        import traceback
        traceback.print_exc()
    finally:
        session.close()

def main():
    fix_staff_status()

if __name__ == "__main__":
    main() 