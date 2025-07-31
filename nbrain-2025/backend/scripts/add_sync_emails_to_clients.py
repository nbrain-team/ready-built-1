#!/usr/bin/env python3
"""
Add sync_email_addresses column to clients table
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

def add_sync_emails_column():
    """Add sync_email_addresses column to clients table"""
    
    with engine.connect() as conn:
        # Check if column exists
        result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'clients' AND column_name = 'sync_email_addresses'
        """))
        
        if not result.fetchone():
            print("Adding sync_email_addresses column...")
            conn.execute(text("""
                ALTER TABLE clients 
                ADD COLUMN sync_email_addresses JSON DEFAULT '[]'::json
            """))
            conn.commit()
            print("✓ Added sync_email_addresses column")
        else:
            print("sync_email_addresses column already exists")

if __name__ == "__main__":
    print("Adding sync_email_addresses to clients table...")
    add_sync_emails_column() 