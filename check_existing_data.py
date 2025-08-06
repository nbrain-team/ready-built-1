#!/usr/bin/env python3
"""
Check if data was already uploaded
"""

import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv('DATABASE_URL', '')

if not DATABASE_URL:
    print("Please set your DATABASE_URL environment variable")
    exit(1)

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

def check_data():
    session = Session()
    
    print("=" * 60)
    print("CHECKING EXISTING DATA IN DATABASE")
    print("=" * 60)
    
    try:
        # Check transactions by year
        print("\n1. Transaction data by year:")
        result = session.execute(text("""
            SELECT 
                EXTRACT(YEAR FROM sale_date) as year,
                COUNT(*) as count,
                MIN(sale_date) as earliest,
                MAX(sale_date) as latest
            FROM salon_transactions
            GROUP BY EXTRACT(YEAR FROM sale_date)
            ORDER BY year
        """))
        
        total_trans = 0
        for row in result:
            print(f"   {int(row.year)}: {row.count:,} records ({row.earliest} to {row.latest})")
            total_trans += row.count
        print(f"   Total transactions: {total_trans:,}")
        
        # Check time clock by year
        print("\n2. Time clock data by year:")
        result = session.execute(text("""
            SELECT 
                EXTRACT(YEAR FROM clock_date) as year,
                COUNT(*) as count,
                MIN(clock_date) as earliest,
                MAX(clock_date) as latest
            FROM salon_time_clock
            GROUP BY EXTRACT(YEAR FROM clock_date)
            ORDER BY year
        """))
        
        total_tc = 0
        for row in result:
            if row.year:
                print(f"   {int(row.year)}: {row.count:,} records ({row.earliest} to {row.latest})")
                total_tc += row.count
        print(f"   Total time clock entries: {total_tc:,}")
        
        # Check schedules
        print("\n3. Schedule data:")
        result = session.execute(text("""
            SELECT 
                COUNT(*) as count,
                MIN(schedule_date) as earliest,
                MAX(schedule_date) as latest
            FROM salon_schedules
        """))
        
        row = result.first()
        print(f"   Total: {row.count:,} records")
        if row.count > 0:
            print(f"   Date range: {row.earliest} to {row.latest}")
        
        # Summary
        print("\n" + "=" * 60)
        print("SUMMARY:")
        print("=" * 60)
        
        expected = {
            'transactions': 607_918,  # 393,638 + 214,280
            'timeclock': 66_884,      # 41,320 + 25,564
            'schedules': 132_731
        }
        
        actual = {
            'transactions': total_trans,
            'timeclock': total_tc,
            'schedules': row.count
        }
        
        all_good = True
        for key, expected_count in expected.items():
            actual_count = actual[key]
            if actual_count >= expected_count:
                print(f"✅ {key}: {actual_count:,} records (expected {expected_count:,})")
            else:
                print(f"❌ {key}: {actual_count:,} records (expected {expected_count:,}, missing {expected_count - actual_count:,})")
                all_good = False
        
        if all_good:
            print("\n🎉 ALL DATA HAS BEEN SUCCESSFULLY UPLOADED!")
        else:
            print("\n⚠️  Some data is missing")
            
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    check_data() 