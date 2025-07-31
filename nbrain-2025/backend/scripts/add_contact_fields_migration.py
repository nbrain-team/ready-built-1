#!/usr/bin/env python3
"""
Migration script to add contact fields to CRM opportunities table.
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from core.database import DATABASE_URL

def run_migration():
    """Add contact fields to the crm_opportunities table."""
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        try:
            # Add new columns to crm_opportunities table
            print("Adding contact fields to crm_opportunities table...")
            
            columns_to_add = [
                ("contact_name", "VARCHAR"),
                ("contact_email", "VARCHAR"),
                ("contact_phone", "VARCHAR"),
                ("linkedin_profile", "VARCHAR"),
                ("website_url", "VARCHAR")
            ]
            
            for column_name, column_type in columns_to_add:
                try:
                    conn.execute(text(f"""
                        ALTER TABLE crm_opportunities 
                        ADD COLUMN IF NOT EXISTS {column_name} {column_type}
                    """))
                    conn.commit()
                    print(f"✓ Added column: {column_name}")
                except Exception as e:
                    print(f"⚠ Column {column_name} might already exist or error: {e}")
            
            print("\n✅ Migration completed successfully!")
            
        except Exception as e:
            print(f"\n❌ Migration failed: {e}")
            raise

if __name__ == "__main__":
    run_migration() 