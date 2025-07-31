#!/usr/bin/env python3
"""
Add synced_by field to client_communications table to track which user's account emails were synced from
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from core.database import engine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_sync_metadata():
    """Add synced_by field to client_communications table"""
    
    with engine.connect() as conn:
        try:
            # Check if column already exists
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'client_communications' 
                AND column_name = 'synced_by'
            """))
            
            if result.fetchone():
                logger.info("synced_by column already exists in client_communications table")
                return
            
            # Add synced_by column
            logger.info("Adding synced_by column to client_communications table...")
            conn.execute(text("""
                ALTER TABLE client_communications 
                ADD COLUMN synced_by VARCHAR(255)
            """))
            conn.commit()
            
            logger.info("Successfully added synced_by column")
            
        except Exception as e:
            logger.error(f"Error adding synced_by column: {e}")
            raise

if __name__ == "__main__":
    add_sync_metadata() 