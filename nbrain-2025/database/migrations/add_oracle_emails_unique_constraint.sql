-- Add unique constraint to oracle_emails table
ALTER TABLE oracle_emails 
ADD CONSTRAINT oracle_emails_user_message_unique 
UNIQUE (user_id, message_id); 