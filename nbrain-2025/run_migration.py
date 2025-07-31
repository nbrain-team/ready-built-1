#!/usr/bin/env python3
"""
Run the oracle_emails table migration
"""

import os
import psycopg2
from urllib.parse import urlparse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get database URL
DATABASE_URL = os.getenv('DATABASE_URL')

if not DATABASE_URL:
    print("ERROR: DATABASE_URL not found in environment variables")
    exit(1)

# Parse the database URL
result = urlparse(DATABASE_URL)

try:
    # Connect to the database
    conn = psycopg2.connect(
        database=result.path[1:],
        user=result.username,
        password=result.password,
        host=result.hostname,
        port=result.port
    )
    
    # Create a cursor
    cur = conn.cursor()
    
    print("Connected to database successfully")
    
    # Read and execute the migration
    with open('database/migrations/create_oracle_emails_table.sql', 'r') as f:
        migration_sql = f.read()
    
    print("Executing migration...")
    cur.execute(migration_sql)
    
    # Commit the changes
    conn.commit()
    
    print("Migration completed successfully!")
    
    # Verify the table was created
    cur.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name = 'oracle_emails'
    """)
    
    result = cur.fetchone()
    if result:
        print(f"✓ Table 'oracle_emails' exists")
        
        # Check indexes
        cur.execute("""
            SELECT indexname 
            FROM pg_indexes 
            WHERE tablename = 'oracle_emails'
        """)
        
        indexes = cur.fetchall()
        print(f"✓ Created {len(indexes)} indexes:")
        for idx in indexes:
            print(f"  - {idx[0]}")
    else:
        print("⚠️  Table 'oracle_emails' was not created")
    
    # Close the cursor and connection
    cur.close()
    conn.close()
    
except Exception as e:
    print(f"ERROR: {e}")
    exit(1) 