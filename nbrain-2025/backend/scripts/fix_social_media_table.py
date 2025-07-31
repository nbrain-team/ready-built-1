#!/usr/bin/env python3
"""
Manually create social_media_posts table if it doesn't exist
This script can be run directly to fix the missing table issue
"""

import os
import sys
import logging
from sqlalchemy import create_engine, text
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

# Convert postgresql:// to postgresql+psycopg2://
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://")
    if "sslmode=" not in DATABASE_URL:
        DATABASE_URL += "?sslmode=require"

def main():
    """Create the social media posts table"""
    engine = create_engine(DATABASE_URL)
    
    try:
        with engine.connect() as conn:
            logger.info("Connected to database successfully")
            
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
            
            # Create enum types first
            logger.info("Creating enum types...")
            try:
                conn.execute(text("""
                    CREATE TYPE poststatus AS ENUM ('draft', 'scheduled', 'published', 'failed');
                """))
                conn.commit()
                logger.info("Created poststatus enum")
            except Exception as e:
                if "already exists" in str(e):
                    logger.info("poststatus enum already exists")
                else:
                    raise
            
            try:
                conn.execute(text("""
                    CREATE TYPE socialplatform AS ENUM ('twitter', 'instagram', 'facebook', 'linkedin');
                """))
                conn.commit()
                logger.info("Created socialplatform enum")
            except Exception as e:
                if "already exists" in str(e):
                    logger.info("socialplatform enum already exists")
                else:
                    raise
            
            # Create the table
            logger.info("Creating social_media_posts table...")
            conn.execute(text("""
                CREATE TABLE social_media_posts (
                    id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid()::text,
                    platform socialplatform NOT NULL,
                    content TEXT NOT NULL,
                    scheduled_date TIMESTAMP NOT NULL,
                    published_date TIMESTAMP,
                    status poststatus DEFAULT 'draft',
                    client_id VARCHAR REFERENCES clients(id),
                    created_by VARCHAR NOT NULL REFERENCES users(id),
                    campaign_name VARCHAR,
                    media_urls JSONB,
                    platform_data JSONB,
                    analytics_data JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    error_message TEXT
                );
            """))
            
            # Create indexes
            logger.info("Creating indexes...")
            conn.execute(text("""
                CREATE INDEX idx_social_posts_scheduled_date ON social_media_posts(scheduled_date);
                CREATE INDEX idx_social_posts_client ON social_media_posts(client_id);
                CREATE INDEX idx_social_posts_status ON social_media_posts(status);
                CREATE INDEX idx_social_posts_platform ON social_media_posts(platform);
            """))
            
            conn.commit()
            logger.info("Successfully created social_media_posts table with indexes!")
            
    except Exception as e:
        logger.error(f"Error creating social_media_posts table: {e}")
        raise
    finally:
        engine.dispose()

if __name__ == "__main__":
    main() 