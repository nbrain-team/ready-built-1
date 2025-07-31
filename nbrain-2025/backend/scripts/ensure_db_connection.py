#!/usr/bin/env python3
"""
Ensure database connection is working before starting the application.
This helps prevent SSL connection issues on startup.
"""

import os
import sys
import time
import logging
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from core.database import engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def ensure_db_connection(max_retries=5):
    """Ensure database connection is working with retries"""
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            # Test the connection
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                result.fetchone()
            
            logger.info("Database connection successful!")
            return True
            
        except Exception as e:
            retry_count += 1
            logger.warning(f"Database connection attempt {retry_count} failed: {e}")
            
            if retry_count < max_retries:
                wait_time = retry_count * 2  # Exponential backoff
                logger.info(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                logger.error("Failed to connect to database after all retries")
                return False
    
    return False

if __name__ == "__main__":
    if ensure_db_connection():
        sys.exit(0)
    else:
        sys.exit(1) 