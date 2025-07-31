#!/usr/bin/env python3
"""
Create social_media_posts table
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from core.database import engine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_social_media_table():
    """Create the social_media_posts table if it doesn't exist"""
    
    try:
        with engine.connect() as conn:
            # Check if table exists
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'social_media_posts'
                );
            """))
            table_exists = result.scalar()
            
            if table_exists:
                logger.info("Table social_media_posts already exists")
                return
            
            logger.info("Creating social_media_posts table...")
            
            # Create enum types first
            conn.execute(text("""
                DO $$ BEGIN
                    CREATE TYPE poststatus AS ENUM ('draft', 'scheduled', 'published', 'failed');
                EXCEPTION
                    WHEN duplicate_object THEN null;
                END $$;
            """))
            
            conn.execute(text("""
                DO $$ BEGIN
                    CREATE TYPE socialplatform AS ENUM ('twitter', 'instagram', 'facebook', 'linkedin');
                EXCEPTION
                    WHEN duplicate_object THEN null;
                END $$;
            """))
            
            # Create the table
            conn.execute(text("""
                CREATE TABLE social_media_posts (
                    id VARCHAR PRIMARY KEY,
                    platform socialplatform NOT NULL,
                    content TEXT NOT NULL,
                    scheduled_date TIMESTAMP NOT NULL,
                    published_date TIMESTAMP,
                    status poststatus DEFAULT 'draft',
                    client_id VARCHAR REFERENCES clients(id),
                    created_by VARCHAR NOT NULL REFERENCES users(id),
                    campaign_name VARCHAR,
                    media_urls JSON,
                    platform_data JSON,
                    analytics_data JSON,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    error_message TEXT
                );
            """))
            
            # Create indexes
            conn.execute(text("""
                CREATE INDEX idx_social_media_posts_scheduled_date ON social_media_posts(scheduled_date);
                CREATE INDEX idx_social_media_posts_status ON social_media_posts(status);
                CREATE INDEX idx_social_media_posts_client_id ON social_media_posts(client_id);
                CREATE INDEX idx_social_media_posts_created_by ON social_media_posts(created_by);
            """))
            
            conn.commit()
            logger.info("Successfully created social_media_posts table with indexes")
            
    except Exception as e:
        logger.error(f"Error creating social_media_posts table: {e}")
        raise

if __name__ == "__main__":
    create_social_media_table()