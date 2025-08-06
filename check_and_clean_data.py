#!/usr/bin/env python3
"""
Check for any data outside of Jan 2-6, 2025 and clean it if found
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

def check_and_clean_data():
    """Check for data outside of Jan 2-6, 2025 and clean if necessary"""
    session = Session()
    
    print("=" * 60)
    print("DATA VERIFICATION AND CLEANUP")
    print("=" * 60)
    
    try:
        # First, check what data we have
        print("\n1. Checking all transaction dates:")
        result = session.execute(text("""
            SELECT sale_date, COUNT(*) as count
            FROM salon_transactions
            GROUP BY sale_date
            ORDER BY sale_date
        """))
        
        all_dates = list(result)
        valid_dates = ['2025-01-02', '2025-01-03', '2025-01-04', '2025-01-05', '2025-01-06']
        dates_to_remove = []
        
        print("\nCurrent data:")
        for row in all_dates:
            date_str = str(row.sale_date)
            status = "✓ Valid" if date_str in valid_dates else "✗ Should be removed"
            print(f"  {row.sale_date}: {row.count:,} transactions {status}")
            
            if date_str not in valid_dates:
                dates_to_remove.append(row.sale_date)
        
        # Check for any pre-2025 or post Jan 6 data
        print("\n2. Checking for out-of-range data:")
        
        # Pre-2025 data
        result = session.execute(text("""
            SELECT COUNT(*) as count, MIN(sale_date) as min_date, MAX(sale_date) as max_date
            FROM salon_transactions
            WHERE sale_date < '2025-01-01'
        """))
        row = result.first()
        if row.count > 0:
            print(f"  ⚠️  Found {row.count} pre-2025 transactions ({row.min_date} to {row.max_date})")
            dates_to_remove.extend(['pre-2025'])
        else:
            print("  ✓ No pre-2025 data found")
        
        # Post Jan 6 data
        result = session.execute(text("""
            SELECT COUNT(*) as count, MIN(sale_date) as min_date, MAX(sale_date) as max_date
            FROM salon_transactions
            WHERE sale_date > '2025-01-06'
        """))
        row = result.first()
        if row.count > 0:
            print(f"  ⚠️  Found {row.count} post-Jan 6 transactions ({row.min_date} to {row.max_date})")
            dates_to_remove.extend(['post-jan-6'])
        else:
            print("  ✓ No post-Jan 6 data found")
        
        # Clean up if needed
        if dates_to_remove:
            print(f"\n3. Cleaning up {len(dates_to_remove)} invalid date ranges...")
            
            # Remove pre-2025
            if 'pre-2025' in dates_to_remove:
                result = session.execute(text("""
                    DELETE FROM salon_transactions
                    WHERE sale_date < '2025-01-01'
                """))
                print(f"  ✓ Removed {result.rowcount} pre-2025 transactions")
            
            # Remove post Jan 6
            if 'post-jan-6' in dates_to_remove:
                result = session.execute(text("""
                    DELETE FROM salon_transactions
                    WHERE sale_date > '2025-01-06'
                """))
                print(f"  ✓ Removed {result.rowcount} post-Jan 6 transactions")
            
            # Remove specific invalid dates
            for date in dates_to_remove:
                if date not in ['pre-2025', 'post-jan-6']:
                    result = session.execute(text("""
                        DELETE FROM salon_transactions
                        WHERE sale_date = :date
                    """), {"date": date})
                    print(f"  ✓ Removed {result.rowcount} transactions for {date}")
            
            session.commit()
            print("\n✅ Cleanup complete!")
        else:
            print("\n✅ No cleanup needed - all data is within valid date range!")
        
        # Final verification
        print("\n4. Final data verification:")
        result = session.execute(text("""
            SELECT sale_date, COUNT(*) as count
            FROM salon_transactions
            WHERE sale_date BETWEEN '2025-01-02' AND '2025-01-06'
            GROUP BY sale_date
            ORDER BY sale_date
        """))
        
        total = 0
        for row in result:
            print(f"  {row.sale_date}: {row.count:,} transactions")
            total += row.count
        
        print(f"\n  Total valid transactions: {total:,}")
        
        # Check other tables too
        print("\n5. Checking other tables:")
        tables = [
            ('salon_time_clock', 'clock_date', 'Time Clock'),
            ('salon_schedules', 'schedule_date', 'Schedules')
        ]
        
        for table, date_col, name in tables:
            result = session.execute(text(f"SELECT COUNT(*) FROM {table}"))
            count = result.scalar()
            if count > 0:
                result = session.execute(text(f"""
                    SELECT MIN({date_col}) as min_date, MAX({date_col}) as max_date
                    FROM {table}
                """))
                row = result.first()
                print(f"  {name}: {count} records ({row.min_date} to {row.max_date})")
                
                # Clean if needed
                result = session.execute(text(f"""
                    DELETE FROM {table}
                    WHERE {date_col} < '2025-01-02' OR {date_col} > '2025-01-06'
                """))
                if result.rowcount > 0:
                    print(f"    ✓ Removed {result.rowcount} out-of-range records")
                    session.commit()
            else:
                print(f"  {name}: 0 records")
        
    except Exception as e:
        print(f"\nError: {e}")
        session.rollback()
        import traceback
        traceback.print_exc()
    finally:
        session.close()

def main():
    check_and_clean_data()

if __name__ == "__main__":
    main() 