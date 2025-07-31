#!/usr/bin/env python3
"""
Fix Oracle-related database issues
Run on Render: python scripts/fix_oracle_issues.py
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
import json
import uuid

# Get database URL from environment
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    print("ERROR: DATABASE_URL not set")
    sys.exit(1)

# Create engine
engine = create_engine(DATABASE_URL)

print("="*60)
print("Fixing Oracle Database Issues")
print("="*60)

try:
    with engine.connect() as conn:
        # 1. Add missing columns to oracle_emails
        print("\n1. Checking oracle_emails columns...")
        
        # Check if is_deleted column exists
        result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'oracle_emails' 
            AND column_name = 'is_deleted'
        """))
        
        if not result.fetchone():
            print("   Adding is_deleted column...")
            conn.execute(text("""
                ALTER TABLE oracle_emails 
                ADD COLUMN is_deleted BOOLEAN DEFAULT FALSE
            """))
            conn.commit()
            print("   ✓ Added is_deleted column")
        else:
            print("   ✓ is_deleted column already exists")
            
        # Check for deleted_at column
        result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'oracle_emails' 
            AND column_name = 'deleted_at'
        """))
        
        if not result.fetchone():
            print("   Adding deleted_at column...")
            conn.execute(text("""
                ALTER TABLE oracle_emails 
                ADD COLUMN deleted_at TIMESTAMP
            """))
            conn.commit()
            print("   ✓ Added deleted_at column")
        else:
            print("   ✓ deleted_at column already exists")
        
        # 2. Fix action items without IDs
        print("\n2. Fixing action items without IDs...")
        
        # Get all users who might have action items stored
        users_result = conn.execute(text("""
            SELECT DISTINCT user_id 
            FROM oracle_emails
        """))
        
        users = [row[0] for row in users_result]
        
        for user_id in users:
            # Check if user has action items file
            file_path = f"oracle_data/items_{user_id}.json"
            if os.path.exists(file_path):
                print(f"   Processing items for user {user_id}...")
                
                try:
                    with open(file_path, 'r') as f:
                        items = json.load(f)
                    
                    modified = False
                    for item in items:
                        # Add ID if missing
                        if 'id' not in item:
                            item['id'] = str(uuid.uuid4())
                            modified = True
                        
                        # Ensure source field exists
                        if 'source' not in item and 'from_email' in item:
                            item['source'] = item['from_email']
                            modified = True
                        elif 'source' not in item and 'source_email_id' in item:
                            item['source'] = 'Email'
                            modified = True
                        elif 'source' not in item:
                            item['source'] = 'Unknown'
                            modified = True
                    
                    if modified:
                        # Write back the fixed items
                        with open(file_path, 'w') as f:
                            json.dump(items, f, default=str)
                        print(f"   ✓ Fixed {len(items)} items for user {user_id}")
                    else:
                        print(f"   ✓ All items already have IDs for user {user_id}")
                        
                except Exception as e:
                    print(f"   ⚠ Error processing items for user {user_id}: {e}")
        
        # 3. Clear any Redis cache that might have old data
        print("\n3. Attempting to clear Redis cache...")
        try:
            import redis
            redis_url = os.getenv("REDIS_URL")
            if redis_url:
                r = redis.from_url(redis_url)
                # Clear all oracle-related keys
                for key in r.scan_iter("oracle:*"):
                    r.delete(key)
                print("   ✓ Cleared Redis cache")
            else:
                print("   ⚠ Redis not configured, skipping cache clear")
        except Exception as e:
            print(f"   ⚠ Could not clear Redis cache: {e}")
        
        print("\n✅ All fixes completed successfully!")
        
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc() 