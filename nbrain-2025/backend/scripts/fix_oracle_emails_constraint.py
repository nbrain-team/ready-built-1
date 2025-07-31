#!/usr/bin/env python3
"""
Fix oracle_emails unique constraint
Run on Render: python scripts/fix_oracle_emails_constraint.py
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
print("Fixing Oracle Emails Constraint")
print("="*60)

try:
    with engine.connect() as conn:
        # First check if constraint already exists
        result = conn.execute(text("""
            SELECT constraint_name 
            FROM information_schema.table_constraints 
            WHERE table_name = 'oracle_emails' 
            AND constraint_type = 'UNIQUE'
            AND constraint_name = 'oracle_emails_user_message_unique'
        """))
        
        if result.fetchone():
            print("✓ Constraint already exists")
        else:
            # Add the constraint
            conn.execute(text("""
                ALTER TABLE oracle_emails 
                ADD CONSTRAINT oracle_emails_user_message_unique 
                UNIQUE (user_id, message_id)
            """))
            conn.commit()
            print("✓ Added unique constraint on (user_id, message_id)")
            
        print("\nConstraint added successfully!")
        
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc() 