#!/usr/bin/env python3
"""
Emergency fix for Oracle emails - apply constraint and clean duplicates
Run on Render: python scripts/emergency_fix_oracle.py
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
print("Emergency Oracle Fix")
print("="*60)

try:
    with engine.connect() as conn:
        # First, remove any duplicate emails (keep the most recent)
        print("\n1. Removing duplicate emails...")
        result = conn.execute(text("""
            DELETE FROM oracle_emails a
            USING oracle_emails b
            WHERE a.user_id = b.user_id 
            AND a.message_id = b.message_id
            AND a.created_at < b.created_at
        """))
        print(f"✓ Removed {result.rowcount} duplicate emails")
        
        # Check if constraint exists
        print("\n2. Checking for existing constraint...")
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
            print("\n3. Adding unique constraint...")
            conn.execute(text("""
                ALTER TABLE oracle_emails 
                ADD CONSTRAINT oracle_emails_user_message_unique 
                UNIQUE (user_id, message_id)
            """))
            print("✓ Added unique constraint on (user_id, message_id)")
        
        # Verify the constraint
        print("\n4. Verifying constraint...")
        result = conn.execute(text("""
            SELECT constraint_name, constraint_type
            FROM information_schema.table_constraints 
            WHERE table_name = 'oracle_emails' 
            AND constraint_type = 'UNIQUE'
        """))
        
        constraints = result.fetchall()
        print(f"✓ Found {len(constraints)} unique constraints:")
        for c in constraints:
            print(f"  - {c[0]}")
        
        # Count emails
        result = conn.execute(text("SELECT COUNT(*) FROM oracle_emails"))
        count = result.scalar()
        print(f"\n✓ Total emails in database: {count}")
        
        conn.commit()
        print("\n✅ Emergency fix completed successfully!")
        
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc() 