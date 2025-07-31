#!/usr/bin/env python3
"""
Emergency migration script to add implementation_estimate column to agent_ideas table.
This fixes the production database schema mismatch.
"""

import os
import sys
import logging
from sqlalchemy import create_engine, text, inspect
from dotenv import load_dotenv

# Add parent directory to path to import from core
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Add implementation_estimate column to agent_ideas table if it doesn't exist."""
    
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        logger.error("DATABASE_URL not found in environment variables")
        sys.exit(1)
    
    try:
        # Create engine and connection
        engine = create_engine(database_url)
        
        with engine.connect() as conn:
            inspector = inspect(conn)
            
            # Check if agent_ideas table exists
            if not inspector.has_table('agent_ideas'):
                logger.error("agent_ideas table does not exist!")
                sys.exit(1)
            
            # Get existing columns
            columns = [col['name'] for col in inspector.get_columns('agent_ideas')]
            logger.info(f"Existing columns in agent_ideas: {columns}")
            
            # Check if implementation_estimate column exists
            if 'implementation_estimate' not in columns:
                logger.info("Adding implementation_estimate column...")
                
                # Add the column
                conn.execute(text("""
                    ALTER TABLE agent_ideas 
                    ADD COLUMN implementation_estimate JSON
                """))
                conn.commit()
                
                logger.info("Successfully added implementation_estimate column!")
            else:
                logger.info("implementation_estimate column already exists.")
            
            # Verify the column was added
            columns_after = [col['name'] for col in inspector.get_columns('agent_ideas')]
            logger.info(f"Columns after migration: {columns_after}")
            
            if 'implementation_estimate' in columns_after:
                logger.info("Migration completed successfully!")
            else:
                logger.error("Migration failed - column not found after addition")
                sys.exit(1)
                
    except Exception as e:
        logger.error(f"Migration failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main() 