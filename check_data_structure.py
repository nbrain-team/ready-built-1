#!/usr/bin/env python3
"""
Check database structure and data summary
"""

from sqlalchemy import create_engine, text
import os

DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    print("Please set DATABASE_URL")
    exit(1)

engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    # Get column information
    result = conn.execute(text('''
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'salon_transactions'
        ORDER BY ordinal_position
    '''))
    
    print('=== SALON TRANSACTIONS TABLE COLUMNS ===')
    for row in result:
        print(f'  {row.column_name}: {row.data_type}')
    
    # Get summary statistics
    result = conn.execute(text('''
        SELECT 
            COUNT(DISTINCT sale_id) as total_transactions,
            COUNT(DISTINCT client_name) as unique_clients,
            COUNT(DISTINCT service_name) as unique_services,
            COUNT(DISTINCT sale_type) as sale_types,
            SUM(net_sales) as total_revenue,
            SUM(net_service_sales) as total_service_revenue,
            MIN(sale_date) as first_date,
            MAX(sale_date) as last_date
        FROM salon_transactions
        WHERE sale_date >= '2025-01-01'
    '''))
    
    print('\n=== JANUARY 2025 DATA SUMMARY ===')
    row = result.first()
    print(f'  Total Transactions: {row.total_transactions:,}')
    print(f'  Unique Clients: {row.unique_clients:,}')
    print(f'  Unique Services: {row.unique_services:,}')
    print(f'  Sale Types: {row.sale_types}')
    print(f'  Total Revenue: ${row.total_revenue:,.2f}')
    print(f'  Service Revenue: ${row.total_service_revenue:,.2f}')
    print(f'  Date Range: {row.first_date} to {row.last_date}')
    
    # Get top services
    result = conn.execute(text('''
        SELECT service_name, COUNT(*) as count, SUM(net_sales) as revenue
        FROM salon_transactions
        WHERE sale_date >= '2025-01-01' AND service_name IS NOT NULL
        GROUP BY service_name
        ORDER BY revenue DESC
        LIMIT 5
    '''))
    
    print('\n=== TOP 5 SERVICES BY REVENUE ===')
    for row in result:
        print(f'  {row.service_name}: ${row.revenue:,.2f} ({row.count} transactions)')
    
    # Get daily averages
    result = conn.execute(text('''
        SELECT 
            AVG(daily_count) as avg_daily_transactions,
            AVG(daily_revenue) as avg_daily_revenue
        FROM (
            SELECT sale_date, 
                   COUNT(*) as daily_count,
                   SUM(net_sales) as daily_revenue
            FROM salon_transactions
            WHERE sale_date >= '2025-01-01'
            GROUP BY sale_date
        ) daily_stats
    '''))
    
    row = result.first()
    print('\n=== DAILY AVERAGES ===')
    print(f'  Avg Transactions/Day: {row.avg_daily_transactions:.0f}')
    print(f'  Avg Revenue/Day: ${row.avg_daily_revenue:,.2f}') 