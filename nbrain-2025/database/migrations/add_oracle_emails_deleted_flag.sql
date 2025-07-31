-- Add is_deleted flag to oracle_emails table
-- This allows users to delete emails from the Oracle view without removing them from the database

ALTER TABLE oracle_emails 
ADD COLUMN IF NOT EXISTS is_deleted BOOLEAN DEFAULT FALSE;

ALTER TABLE oracle_emails
ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP WITH TIME ZONE;

-- Create index for efficient filtering of non-deleted emails
CREATE INDEX IF NOT EXISTS idx_oracle_emails_deleted ON oracle_emails(user_id, is_deleted); 