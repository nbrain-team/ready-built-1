"""
Fix Oracle tables - add missing columns and constraints
"""

from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)

def fix_oracle_tables():
    """Add missing columns and constraints to Oracle tables"""
    
    with engine.connect() as conn:
        # Add missing columns to oracle_action_items if they don't exist
        conn.execute(text("""
            DO $$ 
            BEGIN
                -- Add is_deleted column if it doesn't exist
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name='oracle_action_items' AND column_name='is_deleted') THEN
                    ALTER TABLE oracle_action_items ADD COLUMN is_deleted BOOLEAN DEFAULT FALSE;
                END IF;
                
                -- Add deleted_at column if it doesn't exist
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name='oracle_action_items' AND column_name='deleted_at') THEN
                    ALTER TABLE oracle_action_items ADD COLUMN deleted_at TIMESTAMP;
                END IF;
                
                -- Add task_created column if it doesn't exist
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name='oracle_action_items' AND column_name='task_created') THEN
                    ALTER TABLE oracle_action_items ADD COLUMN task_created BOOLEAN DEFAULT FALSE;
                END IF;
                
                -- Add task_id column if it doesn't exist
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name='oracle_action_items' AND column_name='task_id') THEN
                    ALTER TABLE oracle_action_items ADD COLUMN task_id VARCHAR;
                END IF;
            END $$;
        """))
        
        # Add unique constraint to oracle_emails if it doesn't exist
        conn.execute(text("""
            DO $$
            BEGIN
                -- Check if the constraint exists
                IF NOT EXISTS (
                    SELECT 1 FROM pg_constraint 
                    WHERE conname = 'oracle_emails_user_message_unique'
                ) THEN
                    -- Add the unique constraint
                    ALTER TABLE oracle_emails 
                    ADD CONSTRAINT oracle_emails_user_message_unique 
                    UNIQUE (user_id, message_id);
                END IF;
            END $$;
        """))
        
        conn.commit()
        print("Oracle tables fixed successfully!")

if __name__ == "__main__":
    fix_oracle_tables() 