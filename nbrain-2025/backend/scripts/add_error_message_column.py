#!/usr/bin/env python3
"""
Add error_message column to oracle_data_sources table
"""

import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import logging

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

def main():
    """Add error_message column"""
    engine = create_engine(DATABASE_URL)
    
    try:
        with engine.connect() as conn:
            logger.info("Connected to database")
            
            # Check if column already exists
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'oracle_data_sources' 
                AND column_name = 'error_message'
            """))
            
            if result.fetchone():
                logger.info("error_message column already exists")
            else:
                logger.info("Adding error_message column to oracle_data_sources table...")
                conn.execute(text("""
                    ALTER TABLE oracle_data_sources 
                    ADD COLUMN error_message VARCHAR(500)
                """))
                conn.commit()
                logger.info("✓ Successfully added error_message column")
            
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)
    finally:
        engine.dispose()

if __name__ == "__main__":
    main() 