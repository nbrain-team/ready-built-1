#!/usr/bin/env python3
"""
Add domain field to clients table
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

def add_domain_field():
    """Add domain field to clients table"""
    
    with engine.connect() as conn:
        # Check if column already exists
        result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='clients' AND column_name='domain'
        """))
        
        if result.fetchone():
            logger.info("Domain column already exists in clients table")
            return
        
        # Add the domain column
        logger.info("Adding domain column to clients table...")
        conn.execute(text("ALTER TABLE clients ADD COLUMN domain VARCHAR"))
        conn.commit()
        
        logger.info("Successfully added domain column to clients table")

if __name__ == "__main__":
    add_domain_field() 