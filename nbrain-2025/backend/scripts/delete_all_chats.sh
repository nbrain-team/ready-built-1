#!/bin/bash
# Script to delete all chat history

DATABASE_URL="postgresql://nbrain_database_clean_user:TD1j8kvF8AmTYsec1ygMtzzeytX6DWAS@dpg-d1g44qnfte5s7387lqt0-a.oregon-postgres.render.com/nbrain_database_clean"

echo "⚠️  WARNING: This will delete ALL chat history!"
echo "Press Ctrl+C to cancel, or Enter to continue..."
read

echo "Deleting all chat sessions..."
psql "$DATABASE_URL" -c "DELETE FROM chat_sessions;"

echo "Checking remaining sessions..."
psql "$DATABASE_URL" -c "SELECT COUNT(*) as remaining_sessions FROM chat_sessions;"

echo "✅ Done!"
