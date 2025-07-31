"""
Script to manually run Oracle migrations
Run this on Render shell to ensure migrations are applied
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)

def run_migration():
    """Run the is_deleted migration"""
    with engine.connect() as conn:
        try:
            # Check if column exists
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='oracle_emails' AND column_name='is_deleted'
            """))
            
            if result.rowcount == 0:
                print("Adding is_deleted column...")
                conn.execute(text("""
                    ALTER TABLE oracle_emails 
                    ADD COLUMN is_deleted BOOLEAN DEFAULT FALSE
                """))
                
                conn.execute(text("""
                    ALTER TABLE oracle_emails
                    ADD COLUMN deleted_at TIMESTAMP WITH TIME ZONE
                """))
                
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_oracle_emails_deleted 
                    ON oracle_emails(user_id, is_deleted)
                """))
                
                conn.commit()
                print("Migration completed successfully!")
            else:
                print("is_deleted column already exists")
                
        except Exception as e:
            print(f"Error: {e}")
            conn.rollback()

if __name__ == "__main__":
    run_migration() 