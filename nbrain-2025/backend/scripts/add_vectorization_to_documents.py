#!/usr/bin/env python3
"""
Add vectorization fields to client_documents table
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import text
from core.database import engine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_vectorization_fields():
    """Add vectorization fields to client_documents table"""
    
    with engine.connect() as conn:
        # Add google_drive_id column
        try:
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='client_documents' AND column_name='google_drive_id'
            """))
            
            if not result.fetchone():
                logger.info("Adding google_drive_id column...")
                conn.execute(text("ALTER TABLE client_documents ADD COLUMN google_drive_id VARCHAR UNIQUE"))
                conn.commit()
        except Exception as e:
            logger.error(f"Error adding google_drive_id: {e}")
        
        # Add google_drive_link column
        try:
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='client_documents' AND column_name='google_drive_link'
            """))
            
            if not result.fetchone():
                logger.info("Adding google_drive_link column...")
                conn.execute(text("ALTER TABLE client_documents ADD COLUMN google_drive_link VARCHAR"))
                conn.commit()
        except Exception as e:
            logger.error(f"Error adding google_drive_link: {e}")
        
        # Add vectorized column
        try:
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='client_documents' AND column_name='vectorized'
            """))
            
            if not result.fetchone():
                logger.info("Adding vectorized column...")
                conn.execute(text("ALTER TABLE client_documents ADD COLUMN vectorized BOOLEAN DEFAULT FALSE"))
                conn.commit()
        except Exception as e:
            logger.error(f"Error adding vectorized: {e}")
        
        # Add vectorized_at column
        try:
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='client_documents' AND column_name='vectorized_at'
            """))
            
            if not result.fetchone():
                logger.info("Adding vectorized_at column...")
                conn.execute(text("ALTER TABLE client_documents ADD COLUMN vectorized_at TIMESTAMP"))
                conn.commit()
        except Exception as e:
            logger.error(f"Error adding vectorized_at: {e}")
        
        logger.info("Successfully added vectorization fields to client_documents table")

if __name__ == "__main__":
    add_vectorization_fields() 