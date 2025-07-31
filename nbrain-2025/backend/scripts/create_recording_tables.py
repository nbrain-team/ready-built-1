#!/usr/bin/env python3
"""
Manually create recording-related tables
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
    """Create recording tables"""
    engine = create_engine(DATABASE_URL)
    
    try:
        with engine.connect() as conn:
            logger.info("Connected to database")
            
            # Create recordings table
            try:
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS recordings (
                        id VARCHAR(36) PRIMARY KEY,
                        user_id VARCHAR(255) NOT NULL,
                        client_id VARCHAR(36),
                        client_name VARCHAR(255),
                        context VARCHAR(50) NOT NULL,
                        audio_path TEXT NOT NULL,
                        duration INTEGER NOT NULL,
                        transcript TEXT,
                        action_items JSONB,
                        recommendations JSONB,
                        summary TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        
                        FOREIGN KEY (user_id) REFERENCES users(id),
                        FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE
                    );
                """))
                conn.commit()
                logger.info("✓ Created recordings table")
            except Exception as e:
                logger.error(f"Failed to create recordings table: {e}")
                conn.rollback()
            
            # Create indexes
            try:
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_user_recordings ON recordings(user_id);
                    CREATE INDEX IF NOT EXISTS idx_client_recordings ON recordings(client_id);
                    CREATE INDEX IF NOT EXISTS idx_context ON recordings(context);
                    CREATE INDEX IF NOT EXISTS idx_created_at ON recordings(created_at);
                """))
                conn.commit()
                logger.info("✓ Created recordings indexes")
            except Exception as e:
                logger.error(f"Failed to create recordings indexes: {e}")
                conn.rollback()
            
            # Add source column to client_tasks
            try:
                conn.execute(text("""
                    ALTER TABLE client_tasks 
                    ADD COLUMN IF NOT EXISTS source VARCHAR(50) DEFAULT 'manual';
                """))
                conn.commit()
                logger.info("✓ Added source column to client_tasks")
            except Exception as e:
                logger.error(f"Failed to add source column: {e}")
                conn.rollback()
            
            # Create oracle_emails table
            try:
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS oracle_emails (
                        id VARCHAR(36) PRIMARY KEY,
                        user_id VARCHAR(255) NOT NULL,
                        message_id VARCHAR(255),
                        thread_id VARCHAR(255),
                        subject TEXT,
                        from_email VARCHAR(255),
                        to_emails TEXT,
                        content TEXT,
                        date TIMESTAMP,
                        is_sent BOOLEAN DEFAULT FALSE,
                        is_received BOOLEAN DEFAULT TRUE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        
                        FOREIGN KEY (user_id) REFERENCES users(id)
                    );
                """))
                conn.commit()
                logger.info("✓ Created oracle_emails table")
            except Exception as e:
                logger.error(f"Failed to create oracle_emails table: {e}")
                conn.rollback()
            
            # Create oracle_emails indexes
            try:
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_oracle_emails_user ON oracle_emails(user_id);
                    CREATE INDEX IF NOT EXISTS idx_oracle_emails_date ON oracle_emails(date);
                    CREATE INDEX IF NOT EXISTS idx_oracle_emails_message ON oracle_emails(message_id);
                """))
                conn.commit()
                logger.info("✓ Created oracle_emails indexes")
            except Exception as e:
                logger.error(f"Failed to create oracle_emails indexes: {e}")
                conn.rollback()
            
            logger.info("Recording tables setup complete!")
            
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        sys.exit(1)
    finally:
        engine.dispose()

if __name__ == "__main__":
    main() 