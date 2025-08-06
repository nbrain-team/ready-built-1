#!/usr/bin/env python3
"""Analyze data distribution to determine optimal batch size"""

import pandas as pd
from collections import defaultdict

def analyze_file(file_path, date_column, file_name):
    print(f"\n{file_name}:")
    print("-" * 50)
    
    # Read file
    df = pd.read_csv(file_path)
    print(f"Total rows: {len(df):,}")
    
    # Parse dates
    df[date_column] = pd.to_datetime(df[date_column], errors='coerce')
    
    # Filter for 2025 only
    df_2025 = df[df[date_column].dt.year >= 2025]
    print(f"2025+ rows: {len(df_2025):,}")
    
    if len(df_2025) == 0:
        print("No 2025 data found")
        return
    
    # Monthly breakdown
    print("\nMonthly breakdown:")
    monthly = df_2025.groupby(df_2025[date_column].dt.to_period('M')).size()
    for month, count in monthly.items():
        print(f"  {month}: {count:,} rows")
    
    # Weekly breakdown for largest month
    if len(monthly) > 0:
        largest_month = monthly.idxmax()
        largest_count = monthly.max()
        print(f"\nLargest month: {largest_month} with {largest_count:,} rows")
        
        # Get weekly breakdown for largest month
        month_data = df_2025[df_2025[date_column].dt.to_period('M') == largest_month]
        weekly = month_data.groupby(month_data[date_column].dt.to_period('W')).size()
        print(f"Weekly breakdown for {largest_month}:")
        for week, count in weekly.items():
            print(f"  {week}: {count:,} rows")

# Analyze each file
files = [
    ('blazer/Detailed Line Item 2025 071825.csv', 'Sale Date', '2025 Transactions'),
    ('blazer/Time Clock Data 2025 071825.csv', 'Date', '2025 Time Clock'),
    ('blazer/Schedule Records.csv', 'Schedule Date', 'Schedule Records')
]

print("DATA SIZE ANALYSIS")
print("=" * 50)

for file_path, date_col, name in files:
    try:
        analyze_file(file_path, date_col, name)
    except Exception as e:
        print(f"\nError analyzing {name}: {e}")

print("\n" + "=" * 50)
print("RECOMMENDATIONS:")
print("- Monthly batches: Good for Time Clock (3-4k rows/month)")
print("- Weekly batches: Better for Transactions (7-8k rows/week)")
print("- Weekly batches: Better for Schedules (4-5k rows/week)") 