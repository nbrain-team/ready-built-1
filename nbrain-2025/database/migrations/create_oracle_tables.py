"""
Create Oracle tables migration
This ensures all Oracle-related tables exist in the database
"""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def create_oracle_tables():
    """Create all Oracle-related tables if they don't exist"""
    
    with engine.connect() as conn:
        # Create oracle_data_sources table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS oracle_data_sources (
                id VARCHAR PRIMARY KEY,
                user_id VARCHAR REFERENCES users(id),
                source_type VARCHAR NOT NULL,
                status VARCHAR DEFAULT 'disconnected',
                credentials JSON,
                last_sync TIMESTAMP,
                item_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP
            );
        """))
        
        # Create oracle_action_items table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS oracle_action_items (
                id VARCHAR PRIMARY KEY,
                user_id VARCHAR REFERENCES users(id),
                title VARCHAR NOT NULL,
                source VARCHAR,
                source_type VARCHAR,
                source_id VARCHAR,
                due_date TIMESTAMP,
                priority VARCHAR DEFAULT 'medium',
                status VARCHAR DEFAULT 'pending',
                meta_data JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                is_deleted BOOLEAN DEFAULT FALSE,
                deleted_at TIMESTAMP,
                task_created BOOLEAN DEFAULT FALSE,
                task_id VARCHAR
            );
        """))
        
        # Create oracle_insights table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS oracle_insights (
                id VARCHAR PRIMARY KEY,
                user_id VARCHAR REFERENCES users(id),
                content TEXT,
                source VARCHAR,
                category VARCHAR,
                relevance_score FLOAT DEFAULT 0.5,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))
        
        # Create oracle_emails table for email storage
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS oracle_emails (
                id VARCHAR PRIMARY KEY,
                user_id VARCHAR REFERENCES users(id),
                message_id VARCHAR,
                thread_id VARCHAR,
                subject VARCHAR,
                from_email VARCHAR,
                to_emails JSON,
                content TEXT,
                date TIMESTAMP,
                is_sent BOOLEAN DEFAULT FALSE,
                is_received BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, message_id)
            );
        """))
        
        # Create indexes for better performance
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_oracle_action_items_user ON oracle_action_items(user_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_oracle_insights_user ON oracle_insights(user_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_oracle_emails_user ON oracle_emails(user_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_oracle_data_sources_user ON oracle_data_sources(user_id);"))
        
        conn.commit()
        print("Oracle tables created successfully!")

if __name__ == "__main__":
    create_oracle_tables() 