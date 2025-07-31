#!/usr/bin/env python3
"""
Optimize database performance by running VACUUM and ANALYZE.
This should be run periodically to maintain good performance.
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from core.database import engine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def optimize_database():
    """Run database optimization commands"""
    
    logger.info("Starting database optimization...")
    
    # Use raw connection with autocommit for VACUUM
    raw_conn = engine.raw_connection()
    raw_conn.set_isolation_level(0)  # Set to autocommit mode
    
    try:
        cursor = raw_conn.cursor()
        
        # Set statement timeout to 10 seconds for these operations
        cursor.execute("SET statement_timeout = '10s';")
        
        # Run VACUUM ANALYZE on key tables
        tables = [
            'clients',
            'client_communications',
            'client_tasks',
            'client_activities',
            'client_team_members',
            'oracle_data_sources',
            'oracle_action_items',
            'chat_sessions',
            'crm_opportunities'
        ]
        
        for table in tables:
            try:
                logger.info(f"Optimizing table: {table}")
                # VACUUM reclaims storage and updates statistics
                cursor.execute(f"VACUUM ANALYZE {table};")
                logger.info(f"✓ Optimized {table}")
            except Exception as e:
                logger.warning(f"Could not optimize {table}: {e}")
        
        # Reset statement timeout
        cursor.execute("RESET statement_timeout;")
        
    finally:
        raw_conn.close()
    
    logger.info("\nDatabase optimization completed!")
    logger.info("This should improve query performance significantly.")

if __name__ == "__main__":
    optimize_database() 