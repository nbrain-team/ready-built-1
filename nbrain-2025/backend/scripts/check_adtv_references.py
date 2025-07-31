#!/usr/bin/env python3
"""
Script to check for ADTV references in the nBrain database.
This will search through chat sessions and other relevant tables.
"""

import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

# Get database URL from environment or command line
DATABASE_URL = os.getenv('DATABASE_URL')
if len(sys.argv) > 1:
    DATABASE_URL = sys.argv[1]

if not DATABASE_URL:
    print("Please provide DATABASE_URL as environment variable or command line argument")
    sys.exit(1)

# Create database connection
engine = create_engine(DATABASE_URL)

print("Checking for ADTV references in the database...\n")

# Check chat_sessions table
print("1. Checking chat_sessions table...")
try:
    with engine.connect() as conn:
        # Search in messages JSON column
        query = text("""
            SELECT id, title, created_at, 
                   messages::text as messages_text
            FROM chat_sessions 
            WHERE messages::text ILIKE '%adtv%' 
               OR messages::text ILIKE '%american dream tv%'
               OR title ILIKE '%adtv%'
               OR title ILIKE '%american dream tv%'
            ORDER BY created_at DESC
        """)
        
        results = conn.execute(query).fetchall()
        
        if results:
            print(f"Found {len(results)} chat sessions with ADTV references:")
            for row in results:
                print(f"\n  - Session ID: {row.id}")
                print(f"    Title: {row.title}")
                print(f"    Created: {row.created_at}")
                
                # Count occurrences in messages
                messages_text = row.messages_text.lower()
                adtv_count = messages_text.count('adtv')
                american_dream_count = messages_text.count('american dream')
                
                print(f"    ADTV mentions: {adtv_count}")
                print(f"    American Dream mentions: {american_dream_count}")
        else:
            print("  ✓ No ADTV references found in chat_sessions")
            
except Exception as e:
    print(f"  Error checking chat_sessions: {e}")

# Check users table
print("\n2. Checking users table...")
try:
    with engine.connect() as conn:
        query = text("""
            SELECT id, email
            FROM users 
            WHERE email ILIKE '%adtv%' 
               OR email ILIKE '%american%dream%'
        """)
        
        results = conn.execute(query).fetchall()
        
        if results:
            print(f"Found {len(results)} users with ADTV-related emails:")
            for row in results:
                print(f"  - User ID: {row.id}")
                print(f"    Email: {row.email}")
        else:
            print("  ✓ No ADTV references found in users table")
            
except Exception as e:
    print(f"  Error checking users: {e}")

# Summary and recommendations
print("\n" + "="*50)
print("SUMMARY AND RECOMMENDATIONS:")
print("="*50)

print("""
If ADTV references were found in chat_sessions:
1. These are historical conversations that contain ADTV mentions
2. You can delete specific sessions with:
   DELETE FROM chat_sessions WHERE id = 'session_id_here';
   
3. Or update the messages to remove ADTV references:
   UPDATE chat_sessions 
   SET messages = REPLACE(messages::text, 'ADTV', 'nBrain')::json
   WHERE messages::text LIKE '%ADTV%';

4. To clear ALL chat history (careful!):
   DELETE FROM chat_sessions;

Remember to backup your database before making any changes!
""") 