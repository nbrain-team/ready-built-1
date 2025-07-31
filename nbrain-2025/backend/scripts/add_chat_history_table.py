#!/usr/bin/env python3
"""
Add client_chat_history table for storing saved chat messages
"""

import os
import sys
import logging
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    logger.error("No DATABASE_URL found in environment")
    sys.exit(1)

# Convert postgresql:// to postgresql+psycopg2://
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://")
    if "sslmode=" not in DATABASE_URL:
        DATABASE_URL += "?sslmode=require"

def add_chat_history_table():
    """Add client_chat_history table"""
    
    engine = create_engine(DATABASE_URL)
    
    try:
        with engine.connect() as conn:
            logger.info("Connected to database successfully")
            
            # Check if table already exists
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'client_chat_history'
                )
            """))
            
            if result.scalar():
                logger.info("Table client_chat_history already exists")
                return
            
            # Create the table
            logger.info("Creating client_chat_history table...")
            conn.execute(text("""
                CREATE TABLE client_chat_history (
                    id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid()::text,
                    client_id VARCHAR NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
                    message TEXT NOT NULL,
                    query TEXT,
                    sources JSONB DEFAULT '[]'::jsonb,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    created_by VARCHAR NOT NULL REFERENCES users(id),
                    
                    -- Index for performance
                    CONSTRAINT idx_client_chat_history_client_id 
                        FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE
                );
                
                CREATE INDEX idx_chat_history_client_id ON client_chat_history(client_id);
                CREATE INDEX idx_chat_history_created_at ON client_chat_history(created_at DESC);
            """))
            
            conn.commit()
            logger.info("✓ Successfully created client_chat_history table")
            
    except Exception as e:
        logger.error(f"Error creating table: {e}")
        sys.exit(1)
    finally:
        engine.dispose()

if __name__ == "__main__":
    add_chat_history_table() 