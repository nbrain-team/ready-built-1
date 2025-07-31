#!/usr/bin/env python3
"""
Add social media posts table to the database
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from core.database import engine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_social_media_tables():
    """Add social media posts table"""
    
    with engine.connect() as conn:
        try:
            # Create enum types
            logger.info("Creating enum types...")
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
            
            conn.commit()
            
            # Create social_media_posts table
            logger.info("Creating social_media_posts table...")
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS social_media_posts (
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
            logger.info("Creating indexes...")
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_social_posts_scheduled_date 
                ON social_media_posts(scheduled_date);
            """))
            
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_social_posts_client 
                ON social_media_posts(client_id);
            """))
            
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_social_posts_status 
                ON social_media_posts(status);
            """))
            
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_social_posts_platform 
                ON social_media_posts(platform);
            """))
            
            conn.commit()
            logger.info("Social media tables created successfully!")
            
        except Exception as e:
            logger.error(f"Error creating social media tables: {e}")
            conn.rollback()
            raise

if __name__ == "__main__":
    add_social_media_tables() 