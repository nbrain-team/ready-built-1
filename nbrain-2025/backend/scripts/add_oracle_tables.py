#!/usr/bin/env python3
"""
Add Oracle tables to the database
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables first
from dotenv import load_dotenv
load_dotenv()

from core.database import engine, SessionLocal, Base
from core.oracle_handler import OracleDataSource, OracleActionItem, OracleInsight
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_oracle_tables():
    """Create Oracle tables if they don't exist."""
    logger.info("Creating Oracle tables...")
    
    try:
        # Create all tables (this will only create tables that don't exist)
        Base.metadata.create_all(bind=engine)
        
        logger.info("✅ Oracle tables created successfully!")
        
        # Verify tables exist
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN ('oracle_data_sources', 'oracle_action_items', 'oracle_insights')
            """))
            
            tables = [row[0] for row in result]
            logger.info(f"Found Oracle tables: {tables}")
            
            if len(tables) == 3:
                logger.info("✅ All Oracle tables verified!")
            else:
                logger.warning("⚠️ Some Oracle tables may be missing")
        
        return True
        
    except Exception as e:
        logger.error(f"Error creating Oracle tables: {e}")
        return False

if __name__ == "__main__":
    logger.info("Starting Oracle database setup...")
    
    if add_oracle_tables():
        logger.info("✅ Oracle database setup complete!")
    else:
        logger.error("❌ Oracle database setup failed!")
        sys.exit(1) 