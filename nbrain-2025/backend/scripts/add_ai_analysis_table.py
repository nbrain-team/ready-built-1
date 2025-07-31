#!/usr/bin/env python3
"""
Add client_ai_analysis table for storing AI-generated insights
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

def add_ai_analysis_table():
    """Add client_ai_analysis table"""
    
    engine = create_engine(DATABASE_URL)
    
    try:
        with engine.connect() as conn:
            logger.info("Connected to database successfully")
            
            # Check if table already exists
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'client_ai_analysis'
                )
            """))
            
            if result.scalar():
                logger.info("Table client_ai_analysis already exists")
                return
            
            # Create the table
            logger.info("Creating client_ai_analysis table...")
            conn.execute(text("""
                CREATE TABLE client_ai_analysis (
                    id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid()::text,
                    client_id VARCHAR NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
                    analysis_type VARCHAR NOT NULL,
                    result_data JSONB NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    created_by VARCHAR NOT NULL REFERENCES users(id),
                    expires_at TIMESTAMP WITH TIME ZONE,
                    
                    -- Indexes for performance
                    CONSTRAINT unique_client_analysis_type UNIQUE (client_id, analysis_type)
                );
                
                CREATE INDEX idx_client_ai_analysis_client_id ON client_ai_analysis(client_id);
                CREATE INDEX idx_client_ai_analysis_type ON client_ai_analysis(analysis_type);
                CREATE INDEX idx_client_ai_analysis_created_at ON client_ai_analysis(created_at DESC);
            """))
            
            conn.commit()
            logger.info("✓ Successfully created client_ai_analysis table")
            
    except Exception as e:
        logger.error(f"Error creating table: {e}")
        sys.exit(1)
    finally:
        engine.dispose()

if __name__ == "__main__":
    add_ai_analysis_table() 