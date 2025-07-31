-- Quick fix to add error_message column
ALTER TABLE oracle_data_sources 
ADD COLUMN IF NOT EXISTS error_message VARCHAR(500); 