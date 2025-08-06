#!/usr/bin/env python3
"""
Debug why dashboard shows no data
"""

import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from datetime import date

# Database URL
DATABASE_URL = os.getenv('DATABASE_URL', '')

if not DATABASE_URL:
    print("Please set your DATABASE_URL environment variable")
    exit(1)

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

def check_dashboard_data():
    """Check what data the dashboard endpoints are looking for"""
    session = Session()
    
    print("=" * 60)
    print("DASHBOARD DATA DEBUG")
    print("=" * 60)
    
    try:
        # 1. Check StaffPerformance table (what dashboard uses)
        print("\n1. StaffPerformance table:")
        result = session.execute(text("""
            SELECT COUNT(*) as count,
                   MIN(period_date) as min_date,
                   MAX(period_date) as max_date
            FROM staff_performance
        """))
        row = result.first()
        print(f"   Records: {row.count}")
        if row.count > 0:
            print(f"   Date range: {row.min_date} to {row.max_date}")
        
        # 2. Check latest performance date
        print("\n2. Latest performance date:")
        result = session.execute(text("SELECT MAX(period_date) FROM staff_performance"))
        latest_perf = result.scalar()
        print(f"   Latest date: {latest_perf}")
        
        # 3. Check if we have data for that date
        if latest_perf:
            result = session.execute(text("""
                SELECT COUNT(*) as count,
                       SUM(net_sales) as total_sales,
                       AVG(utilization_percent) as avg_util
                FROM staff_performance
                WHERE period_date = :date
            """), {"date": latest_perf})
            row = result.first()
            print(f"\n3. Data for latest date ({latest_perf}):")
            print(f"   Records: {row.count}")
            print(f"   Total sales: ${row.total_sales:,.2f}" if row.total_sales else "   Total sales: $0.00")
            print(f"   Avg utilization: {row.avg_util:.1f}%" if row.avg_util else "   Avg utilization: 0.0%")
        
        # 4. Check what's in transactions (what we uploaded)
        print("\n4. Transaction data (what we uploaded):")
        result = session.execute(text("""
            SELECT COUNT(*) as count,
                   MIN(sale_date) as min_date,
                   MAX(sale_date) as max_date,
                   SUM(net_sales) as total_sales
            FROM salon_transactions
        """))
        row = result.first()
        print(f"   Records: {row.count}")
        if row.count > 0:
            print(f"   Date range: {row.min_date} to {row.max_date}")
            print(f"   Total sales: ${row.total_sales:,.2f}" if row.total_sales else "   Total sales: $0.00")
        
        # 5. Check staff positions
        print("\n5. Staff position status:")
        result = session.execute(text("""
            SELECT position_status, COUNT(*) as count
            FROM salon_staff
            GROUP BY position_status
        """))
        for row in result:
            status = row.position_status or 'NULL'
            print(f"   Status '{status}': {row.count} staff")
        
        # 6. Check if we need to aggregate transaction data into performance
        print("\n6. Should we aggregate transaction data into performance?")
        result = session.execute(text("""
            SELECT 
                DATE_TRUNC('month', sale_date) as month,
                COUNT(DISTINCT staff_id) as staff_count,
                COUNT(*) as transaction_count,
                SUM(net_sales) as total_sales
            FROM salon_transactions
            WHERE staff_id IS NOT NULL
            GROUP BY DATE_TRUNC('month', sale_date)
            ORDER BY month
        """))
        
        print("   Monthly transaction summary:")
        for row in result:
            print(f"   {row.month.strftime('%Y-%m')}: {row.staff_count} staff, {row.transaction_count} transactions, ${row.total_sales:,.2f}")
            
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

def main():
    check_dashboard_data()
    
    print("\n" + "=" * 60)
    print("DIAGNOSIS:")
    print("=" * 60)
    print("The dashboard is looking for data in the 'staff_performance' table,")
    print("but we only uploaded transaction data. The dashboard needs:")
    print("1. Staff performance records with period_date")
    print("2. Staff with position_status = 'A' for active staff count")
    print("3. Aggregated metrics (utilization_percent, net_sales, etc.)")

if __name__ == "__main__":
    main() 