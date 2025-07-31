#!/usr/bin/env python3
"""
Clear emails that don't have the nBrain Priority label
Run on Render: python scripts/clear_unlabeled_emails.py
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from datetime import datetime

# Get database URL from environment
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    print("ERROR: DATABASE_URL not set")
    sys.exit(1)

# Create engine
engine = create_engine(DATABASE_URL)

USER_ID = '2908bb63-ebad-48d0-997d-5ed153aef0c2'

print("="*60)
print("Clearing Unlabeled Emails")
print("="*60)

try:
    with engine.connect() as conn:
        # First, count existing emails
        result = conn.execute(
            text("SELECT COUNT(*) FROM oracle_emails WHERE user_id = :user_id"),
            {"user_id": USER_ID}
        )
        total_count = result.scalar()
        print(f"Total emails in database: {total_count}")
        
        # Clear all emails for this user
        # (We'll re-sync only the labeled ones)
        result = conn.execute(
            text("DELETE FROM oracle_emails WHERE user_id = :user_id"),
            {"user_id": USER_ID}
        )
        conn.commit()
        
        print(f"✓ Cleared {result.rowcount} emails")
        print("\nNow please:")
        print("1. Go to the Oracle page")
        print("2. Click 'Sync Email & Calendar'")
        print("3. Only emails with 'nBrain Priority' label will be synced")
        
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc() 