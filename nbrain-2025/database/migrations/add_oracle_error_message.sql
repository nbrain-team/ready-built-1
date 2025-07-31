-- Add error_message field to oracle_data_sources table
ALTER TABLE oracle_data_sources 
ADD COLUMN IF NOT EXISTS error_message VARCHAR(500); 