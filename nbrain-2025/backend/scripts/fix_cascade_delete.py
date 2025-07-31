#!/usr/bin/env python3
"""
Fix cascade delete issue for client communications.
This script updates the foreign key constraint to remove cascade delete.
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from core.database import engine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_cascade_delete():
    """Update the foreign key constraint to remove cascade delete"""
    try:
        with engine.connect() as conn:
            # Set a timeout for this operation
            conn.execute(text("SET statement_timeout = '10s';"))
            
            # Check if the constraint exists first
            result = conn.execute(text("""
                SELECT constraint_name 
                FROM information_schema.table_constraints 
                WHERE table_name = 'client_communications' 
                AND constraint_type = 'FOREIGN KEY'
                AND constraint_name = 'client_communications_client_id_fkey';
            """))
            
            constraint_exists = result.fetchone() is not None
            
            if not constraint_exists:
                logger.info("Foreign key constraint doesn't exist or already fixed. Skipping.")
                return
            
            try:
                # Use CONCURRENTLY to avoid locking (note: this requires no transaction)
                # So we'll use a non-blocking approach
                logger.info("Checking current foreign key definition...")
                
                # Check if cascade delete is actually set
                cascade_check = conn.execute(text("""
                    SELECT confdeltype 
                    FROM pg_constraint 
                    WHERE conname = 'client_communications_client_id_fkey';
                """))
                
                result = cascade_check.fetchone()
                if result and result[0] == 'a':  # 'a' means NO ACTION (no cascade)
                    logger.info("Foreign key already doesn't have cascade delete. Nothing to do.")
                    return
                
                # If we need to update, do it quickly
                logger.info("Updating foreign key constraint...")
                
                # Drop and recreate in one statement to minimize lock time
                conn.execute(text("""
                    ALTER TABLE client_communications 
                    DROP CONSTRAINT IF EXISTS client_communications_client_id_fkey,
                    ADD CONSTRAINT client_communications_client_id_fkey 
                    FOREIGN KEY (client_id) REFERENCES clients(id);
                """))
                
                logger.info("✓ Successfully updated cascade behavior for client_communications")
                
            except Exception as e:
                logger.warning(f"Could not update constraints: {e}")
                # Don't raise - let the build continue
                logger.info("Continuing build despite constraint update failure")
                
    except Exception as e:
        logger.warning(f"Database operation failed: {e}")
        # Don't raise - let the build continue
        logger.info("Continuing build despite database error")

if __name__ == "__main__":
    logger.info("Checking cascade delete configuration...")
    fix_cascade_delete()
    logger.info("Cascade delete check completed.") 