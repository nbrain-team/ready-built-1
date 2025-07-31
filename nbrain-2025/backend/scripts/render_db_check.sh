#!/bin/bash
# Script to check for ADTV references in the database
# Run this in Render's shell

echo "=================================================="
echo "Checking nBrain Database for ADTV References"
echo "=================================================="
echo ""

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    echo "ERROR: DATABASE_URL environment variable is not set"
    exit 1
fi

echo "1. Checking chat_sessions table for ADTV references..."
echo "=================================================="

# Count total sessions
psql $DATABASE_URL -t -c "SELECT COUNT(*) FROM chat_sessions;" | while read count; do
    echo "Total chat sessions: $count"
done

# Check for ADTV references
echo ""
echo "Searching for ADTV or American Dream TV mentions..."
psql $DATABASE_URL -c "
SELECT 
    id,
    title,
    created_at,
    LENGTH(messages::text) as message_length
FROM chat_sessions 
WHERE messages::text ILIKE '%adtv%' 
   OR messages::text ILIKE '%american dream tv%'
   OR title ILIKE '%adtv%'
   OR title ILIKE '%american dream tv%'
ORDER BY created_at DESC
LIMIT 10;
"

# Count ADTV references
ADTV_COUNT=$(psql $DATABASE_URL -t -c "
SELECT COUNT(*) 
FROM chat_sessions 
WHERE messages::text ILIKE '%adtv%' 
   OR messages::text ILIKE '%american dream tv%'
   OR title ILIKE '%adtv%'
   OR title ILIKE '%american dream tv%';
")

echo ""
echo "Total sessions with ADTV references: $ADTV_COUNT"

echo ""
echo "2. Checking users table for ADTV-related emails..."
echo "=================================================="

psql $DATABASE_URL -c "
SELECT id, email 
FROM users 
WHERE email ILIKE '%adtv%' 
   OR email ILIKE '%american%dream%';
"

echo ""
echo "=================================================="
echo "QUICK ACTIONS (copy and paste in Render shell):"
echo "=================================================="
echo ""
echo "To DELETE ALL chat sessions:"
echo "psql \$DATABASE_URL -c \"DELETE FROM chat_sessions;\""
echo ""
echo "To DELETE only ADTV-related sessions:"
echo "psql \$DATABASE_URL -c \"DELETE FROM chat_sessions WHERE messages::text ILIKE '%adtv%' OR messages::text ILIKE '%american dream%' OR title ILIKE '%adtv%' OR title ILIKE '%american dream%';\""
echo ""
echo "To see first 5 session titles:"
echo "psql \$DATABASE_URL -c \"SELECT id, title, created_at FROM chat_sessions ORDER BY created_at DESC LIMIT 5;\""
echo "" 