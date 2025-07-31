#!/usr/bin/env python3
"""
Add is_deleted column to oracle_emails if missing
Run on Render: python scripts/add_is_deleted_column.py
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text

# Get database URL from environment
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    print("ERROR: DATABASE_URL not set")
    sys.exit(1)

# Create engine
engine = create_engine(DATABASE_URL)

print("="*60)
print("Adding is_deleted Column")
print("="*60)

try:
    with engine.connect() as conn:
        # Check if column exists
        result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'oracle_emails' 
            AND column_name = 'is_deleted'
        """))
        
        if result.fetchone():
            print("✓ is_deleted column already exists")
        else:
            # Add the column
            print("Adding is_deleted column...")
            conn.execute(text("""
                ALTER TABLE oracle_emails 
                ADD COLUMN is_deleted BOOLEAN DEFAULT FALSE
            """))
            conn.commit()
            print("✓ Added is_deleted column")
            
        # Also check for deleted_at column
        result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'oracle_emails' 
            AND column_name = 'deleted_at'
        """))
        
        if result.fetchone():
            print("✓ deleted_at column already exists")
        else:
            # Add the column
            print("Adding deleted_at column...")
            conn.execute(text("""
                ALTER TABLE oracle_emails 
                ADD COLUMN deleted_at TIMESTAMP
            """))
            conn.commit()
            print("✓ Added deleted_at column")
            
        print("\n✅ Columns added successfully!")
        
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc() 