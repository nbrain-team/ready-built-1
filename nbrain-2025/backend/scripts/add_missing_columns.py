#!/usr/bin/env python3
"""
Migration script to add missing columns to agent_ideas table.
Run this on Render to fix the database schema.
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_missing_columns():
    """Add security_considerations and future_enhancements columns if they don't exist."""
    
    # Get database URL from environment
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        logger.error("DATABASE_URL not found in environment!")
        return False
    
    logger.info(f"Connecting to database...")
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        # Start a transaction
        trans = conn.begin()
        
        try:
            # Check if security_considerations column exists
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='agent_ideas' AND column_name='security_considerations'
            """))
            
            if not result.fetchone():
                logger.info("Adding security_considerations column...")
                conn.execute(text("""
                    ALTER TABLE agent_ideas 
                    ADD COLUMN IF NOT EXISTS security_considerations JSON
                """))
                logger.info("✓ Added security_considerations column")
            else:
                logger.info("✓ security_considerations column already exists")
            
            # Check if future_enhancements column exists
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='agent_ideas' AND column_name='future_enhancements'
            """))
            
            if not result.fetchone():
                logger.info("Adding future_enhancements column...")
                conn.execute(text("""
                    ALTER TABLE agent_ideas 
                    ADD COLUMN IF NOT EXISTS future_enhancements JSON
                """))
                logger.info("✓ Added future_enhancements column")
            else:
                logger.info("✓ future_enhancements column already exists")
            
            # Commit the transaction
            trans.commit()
            logger.info("✅ Migration completed successfully!")
            
            # Show current agent ideas count
            result = conn.execute(text("SELECT COUNT(*) FROM agent_ideas"))
            count = result.scalar()
            logger.info(f"📊 Current agent ideas in database: {count}")
            
            return True
            
        except Exception as e:
            trans.rollback()
            logger.error(f"❌ Migration failed: {e}")
            return False

if __name__ == "__main__":
    logger.info("Starting agent_ideas table migration...")
    success = add_missing_columns()
    if success:
        logger.info("✅ All done! The database schema has been updated.")
    else:
        logger.error("❌ Migration failed. Please check the logs above.")
        sys.exit(1) 