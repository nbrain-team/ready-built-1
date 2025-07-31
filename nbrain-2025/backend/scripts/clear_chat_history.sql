-- Script to clear chat history from nBrain database
-- Run this with: psql DATABASE_URL -f clear_chat_history.sql

-- First, let's see what we have
SELECT COUNT(*) as total_sessions FROM chat_sessions;

-- Delete all chat sessions (uncomment the line below to execute)
-- DELETE FROM chat_sessions;

-- Or delete only sessions with specific keywords (uncomment to use)
-- DELETE FROM chat_sessions 
-- WHERE messages::text ILIKE '%adtv%' 
--    OR messages::text ILIKE '%american dream%'
--    OR title ILIKE '%adtv%'
--    OR title ILIKE '%american dream%';

-- Verify deletion
SELECT COUNT(*) as remaining_sessions FROM chat_sessions; 