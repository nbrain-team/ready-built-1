#!/usr/bin/env python3
"""
Add missing columns to clients table
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("Error: DATABASE_URL not found in environment variables")
    sys.exit(1)

engine = create_engine(DATABASE_URL)

def add_missing_columns():
    """Add monthly_recurring_revenue and company_size columns to clients table"""
    
    with engine.connect() as conn:
        # Check and add monthly_recurring_revenue
        result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'clients' AND column_name = 'monthly_recurring_revenue'
        """))
        
        if not result.fetchone():
            print("Adding monthly_recurring_revenue column...")
            conn.execute(text("""
                ALTER TABLE clients 
                ADD COLUMN monthly_recurring_revenue FLOAT
            """))
            conn.commit()
            print("✓ Added monthly_recurring_revenue column")
        else:
            print("monthly_recurring_revenue column already exists")
        
        # Check and add company_size
        result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'clients' AND column_name = 'company_size'
        """))
        
        if not result.fetchone():
            print("Adding company_size column...")
            conn.execute(text("""
                ALTER TABLE clients 
                ADD COLUMN company_size VARCHAR(255)
            """))
            conn.commit()
            print("✓ Added company_size column")
        else:
            print("company_size column already exists")

if __name__ == "__main__":
    print("Adding missing columns to clients table...")
    add_missing_columns() 