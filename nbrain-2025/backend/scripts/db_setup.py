#!/usr/bin/env python3
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import engine, create_tables, SessionLocal, Base
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_and_update_columns():
    """Check if columns exist and add them if they don't."""
    with engine.connect() as conn:
        # Check if implementation_estimate column exists
        result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='agent_ideas' AND column_name='implementation_estimate'
        """))
        
        if not result.fetchone():
            logger.info("Adding implementation_estimate column to agent_ideas table...")
            conn.execute(text("""
                ALTER TABLE agent_ideas 
                ADD COLUMN implementation_estimate JSON
            """))
            conn.commit()
            logger.info("implementation_estimate column added successfully!")
        else:
            logger.info("implementation_estimate column already exists.")
        
        # Check if security_considerations column exists
        result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='agent_ideas' AND column_name='security_considerations'
        """))
        
        if not result.fetchone():
            logger.info("Adding security_considerations column to agent_ideas table...")
            conn.execute(text("""
                ALTER TABLE agent_ideas 
                ADD COLUMN security_considerations JSON
            """))
            conn.commit()
            logger.info("security_considerations column added successfully!")
        else:
            logger.info("security_considerations column already exists.")
        
        # Check if future_enhancements column exists
        result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='agent_ideas' AND column_name='future_enhancements'
        """))
        
        if not result.fetchone():
            logger.info("Adding future_enhancements column to agent_ideas table...")
            conn.execute(text("""
                ALTER TABLE agent_ideas 
                ADD COLUMN future_enhancements JSON
            """))
            conn.commit()
            logger.info("future_enhancements column added successfully!")
        else:
            logger.info("future_enhancements column already exists.")
        
        # Check and add contact fields to crm_opportunities table
        contact_fields = [
            'contact_name',
            'contact_email', 
            'contact_phone',
            'linkedin_profile',
            'website_url'
        ]
        
        for field in contact_fields:
            result = conn.execute(text(f"""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='crm_opportunities' AND column_name='{field}'
            """))
            
            if not result.fetchone():
                logger.info(f"Adding {field} column to crm_opportunities table...")
                conn.execute(text(f"""
                    ALTER TABLE crm_opportunities 
                    ADD COLUMN {field} VARCHAR
                """))
                conn.commit()
                logger.info(f"{field} column added successfully!")
            else:
                logger.info(f"{field} column already exists.")

if __name__ == "__main__":
    logger.info("Setting up database...")
    
    # Create tables if they don't exist
    create_tables()
    logger.info("Tables created/verified.")
    
    # Check and update columns
    check_and_update_columns()
    
    logger.info("Database setup complete!") 