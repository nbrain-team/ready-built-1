#!/usr/bin/env python3
"""
Add missing columns to client_documents table
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
    """Add missing columns to client_documents table"""
    
    with engine.connect() as conn:
        # Check which columns exist
        result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'client_documents'
        """))
        existing_columns = {row[0] for row in result}
        
        # Add google_drive_id if missing
        if 'google_drive_id' not in existing_columns:
            print("Adding google_drive_id column...")
            conn.execute(text("""
                ALTER TABLE client_documents 
                ADD COLUMN google_drive_id VARCHAR UNIQUE
            """))
            conn.commit()
            print("✓ Added google_drive_id column")
        
        # Add google_drive_link if missing
        if 'google_drive_link' not in existing_columns:
            print("Adding google_drive_link column...")
            conn.execute(text("""
                ALTER TABLE client_documents 
                ADD COLUMN google_drive_link VARCHAR
            """))
            conn.commit()
            print("✓ Added google_drive_link column")
        
        # Add vectorized if missing
        if 'vectorized' not in existing_columns:
            print("Adding vectorized column...")
            conn.execute(text("""
                ALTER TABLE client_documents 
                ADD COLUMN vectorized BOOLEAN DEFAULT FALSE
            """))
            conn.commit()
            print("✓ Added vectorized column")
        
        # Add vectorized_at if missing
        if 'vectorized_at' not in existing_columns:
            print("Adding vectorized_at column...")
            conn.execute(text("""
                ALTER TABLE client_documents 
                ADD COLUMN vectorized_at TIMESTAMP
            """))
            conn.commit()
            print("✓ Added vectorized_at column")
        
        print("\nAll missing columns have been added successfully!")

if __name__ == "__main__":
    print("Adding missing columns to client_documents table...")
    add_missing_columns() 