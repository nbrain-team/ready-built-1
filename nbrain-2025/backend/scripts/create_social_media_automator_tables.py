#!/usr/bin/env python3
"""
Create Social Media Automator tables
"""

import os
import sys
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    logger.error("No DATABASE_URL found in environment")
    sys.exit(1)

def main():
    try:
        logger.info("Connecting to database...")
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        logger.info("Creating Social Media Automator tables...")
        
        # Read and execute the migration SQL
        migration_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "database", "migrations", "add_social_media_automator_tables.sql"
        )
        
        with open(migration_path, 'r') as f:
            sql = f.read()
            
        cur.execute(sql)
        conn.commit()
        
        logger.info("Social Media Automator tables created successfully!")
        
        # Verify tables exist
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN (
                'social_media_automator_clients',
                'campaigns',
                'video_clips',
                'social_posts'
            )
        """)
        
        tables = [row[0] for row in cur.fetchall()]
        logger.info(f"Verified tables: {tables}")
        
    except Exception as e:
        logger.error(f"Error creating tables: {e}")
        if conn:
            conn.rollback()
        sys.exit(1)
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    main() 