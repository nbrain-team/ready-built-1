#!/usr/bin/env python3
"""
Manual script to create missing tables - can be run from Render shell
"""

import os
import sys
from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("ERROR: No DATABASE_URL found")
    sys.exit(1)

# Convert postgresql:// to postgresql+psycopg2://
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://")
    if "sslmode=" not in DATABASE_URL:
        DATABASE_URL += "?sslmode=require"

print(f"Connecting to database...")
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    # Create client_ai_analysis table
    print("Creating client_ai_analysis table...")
    try:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS client_ai_analysis (
                id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid()::text,
                client_id VARCHAR NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
                analysis_type VARCHAR NOT NULL,
                result_data JSONB NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                created_by VARCHAR NOT NULL REFERENCES users(id),
                expires_at TIMESTAMP WITH TIME ZONE
            );
        """))
        conn.commit()
        print("✓ Created client_ai_analysis table")
    except Exception as e:
        print(f"Error creating client_ai_analysis: {e}")
        conn.rollback()
    
    # Create unique constraint
    try:
        conn.execute(text("""
            ALTER TABLE client_ai_analysis 
            ADD CONSTRAINT unique_client_analysis_type UNIQUE (client_id, analysis_type);
        """))
        conn.commit()
        print("✓ Added unique constraint")
    except Exception as e:
        print(f"Constraint may already exist: {e}")
        conn.rollback()
    
    # Create indexes
    try:
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_client_ai_analysis_client_id ON client_ai_analysis(client_id);
            CREATE INDEX IF NOT EXISTS idx_client_ai_analysis_type ON client_ai_analysis(analysis_type);
            CREATE INDEX IF NOT EXISTS idx_client_ai_analysis_created_at ON client_ai_analysis(created_at DESC);
        """))
        conn.commit()
        print("✓ Created indexes")
    except Exception as e:
        print(f"Error creating indexes: {e}")
        conn.rollback()
    
    # Create client_chat_history table
    print("\nCreating client_chat_history table...")
    try:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS client_chat_history (
                id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid()::text,
                client_id VARCHAR NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
                message TEXT NOT NULL,
                query TEXT,
                sources JSONB DEFAULT '[]'::jsonb,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                created_by VARCHAR NOT NULL REFERENCES users(id)
            );
        """))
        conn.commit()
        print("✓ Created client_chat_history table")
    except Exception as e:
        print(f"Error creating client_chat_history: {e}")
        conn.rollback()
    
    # Create indexes for chat history
    try:
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_chat_history_client_id ON client_chat_history(client_id);
            CREATE INDEX IF NOT EXISTS idx_chat_history_created_at ON client_chat_history(created_at DESC);
        """))
        conn.commit()
        print("✓ Created chat history indexes")
    except Exception as e:
        print(f"Error creating chat history indexes: {e}")
        conn.rollback()

print("\nDone! Tables should now be created.")
engine.dispose() 