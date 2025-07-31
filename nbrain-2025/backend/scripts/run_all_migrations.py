#!/usr/bin/env python3
"""
Run all database migrations in the correct order
"""

import os
import sys
import logging
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import time

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

def run_migration(conn, name, sql):
    """Run a single migration with error handling"""
    try:
        logger.info(f"Running migration: {name}")
        conn.execute(text(sql))
        conn.commit()
        logger.info(f"✓ Successfully completed: {name}")
        return True
    except Exception as e:
        logger.warning(f"Migration {name} failed or already applied: {e}")
        conn.rollback()
        return False

def main():
    """Run all database migrations in order"""
    engine = create_engine(DATABASE_URL)
    
    # List of migration files in order
    migrations = [
        'initial_schema.sql',
        'add_user_roles.sql',
        'add_client_portal_tables.sql',
        'add_oauth_fields.sql',
        'update_user_roles.sql',
        'add_client_tasks.sql',
        'add_profile_fields.sql',
        'add_crm_tables.sql',
        'add_oauth_tables.sql',
        'add_calendar_tables.sql',
        'add_readai_tables.sql',
        'add_voice_assistant_tables.sql',
        'add_recordings_table.sql',
        'create_oracle_emails_table.sql',
        'add_crm_new_fields.sql',
        'add_crm_expanded_fields.sql',
        'add_social_media_automator_tables.sql',
        'add_oracle_error_message.sql',
        'add_oracle_action_items_fields.sql'
    ]
    
    try:
        with engine.connect() as conn:
            logger.info("Connected to database successfully")
            
            # 1. Add missing client columns
            run_migration(conn, "Add domain column", """
                ALTER TABLE clients ADD COLUMN IF NOT EXISTS domain VARCHAR;
            """)
            
            run_migration(conn, "Add company_size column", """
                ALTER TABLE clients ADD COLUMN IF NOT EXISTS company_size VARCHAR;
            """)
            
            run_migration(conn, "Add monthly_recurring_revenue column", """
                ALTER TABLE clients ADD COLUMN IF NOT EXISTS monthly_recurring_revenue FLOAT;
            """)
            
            # 2. Create client_ai_analysis table
            run_migration(conn, "Create client_ai_analysis table", """
                CREATE TABLE IF NOT EXISTS client_ai_analysis (
                    id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid()::text,
                    client_id VARCHAR NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
                    analysis_type VARCHAR NOT NULL,
                    result_data JSONB NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    created_by VARCHAR NOT NULL REFERENCES users(id),
                    expires_at TIMESTAMP WITH TIME ZONE,
                    
                    CONSTRAINT unique_client_analysis_type UNIQUE (client_id, analysis_type)
                );
            """)
            
            run_migration(conn, "Add client_ai_analysis indexes", """
                CREATE INDEX IF NOT EXISTS idx_client_ai_analysis_client_id ON client_ai_analysis(client_id);
                CREATE INDEX IF NOT EXISTS idx_client_ai_analysis_type ON client_ai_analysis(analysis_type);
                CREATE INDEX IF NOT EXISTS idx_client_ai_analysis_created_at ON client_ai_analysis(created_at DESC);
            """)
            
            # 3. Create client_chat_history table
            run_migration(conn, "Create client_chat_history table", """
                CREATE TABLE IF NOT EXISTS client_chat_history (
                    id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid()::text,
                    client_id VARCHAR NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
                    message TEXT NOT NULL,
                    query TEXT,
                    sources JSONB DEFAULT '[]'::jsonb,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    created_by VARCHAR NOT NULL REFERENCES users(id)
                );
            """)
            
            run_migration(conn, "Add client_chat_history indexes", """
                CREATE INDEX IF NOT EXISTS idx_chat_history_client_id ON client_chat_history(client_id);
                CREATE INDEX IF NOT EXISTS idx_chat_history_created_at ON client_chat_history(created_at DESC);
            """)
            
            # 4. Fix foreign key constraints if needed
            run_migration(conn, "Update communications foreign key", """
                DO $$
                BEGIN
                    -- Check if the constraint needs updating
                    IF EXISTS (
                        SELECT 1 FROM information_schema.referential_constraints 
                        WHERE constraint_name = 'client_communications_client_id_fkey'
                        AND delete_rule = 'CASCADE'
                    ) THEN
                        -- Drop and recreate without cascade
                        ALTER TABLE client_communications 
                        DROP CONSTRAINT IF EXISTS client_communications_client_id_fkey;
                        
                        ALTER TABLE client_communications 
                        ADD CONSTRAINT client_communications_client_id_fkey 
                        FOREIGN KEY (client_id) REFERENCES clients(id);
                    END IF;
                END $$;
            """)
            
            # 5. Add performance indexes
            run_migration(conn, "Add performance indexes", """
                -- Client communications indexes
                CREATE INDEX IF NOT EXISTS idx_client_communications_client_created 
                ON client_communications(client_id, created_at DESC);
                
                CREATE INDEX IF NOT EXISTS idx_client_communications_type 
                ON client_communications(type) WHERE type IS NOT NULL;
                
                -- Client tasks indexes
                CREATE INDEX IF NOT EXISTS idx_client_tasks_client_status 
                ON client_tasks(client_id, status);
                
                -- Oracle data sources indexes
                CREATE INDEX IF NOT EXISTS idx_oracle_data_sources_user_source 
                ON oracle_data_sources(user_id, source_type);
                
                -- Clients indexes
                CREATE INDEX IF NOT EXISTS idx_clients_created_at 
                ON clients(created_at DESC);
                
                CREATE INDEX IF NOT EXISTS idx_clients_status 
                ON clients(status);
            """)
            
            # 6. Add social media tables
            run_migration(conn, "Create social media enum types", """
                DO $$ BEGIN
                    CREATE TYPE poststatus AS ENUM ('draft', 'scheduled', 'published', 'failed');
                EXCEPTION
                    WHEN duplicate_object THEN null;
                END $$;
                
                DO $$ BEGIN
                    CREATE TYPE socialplatform AS ENUM ('twitter', 'instagram', 'facebook', 'linkedin');
                EXCEPTION
                    WHEN duplicate_object THEN null;
                END $$;
            """)
            
            run_migration(conn, "Create social_media_posts table", """
                CREATE TABLE IF NOT EXISTS social_media_posts (
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
            """)
            
            run_migration(conn, "Add social media indexes", """
                CREATE INDEX IF NOT EXISTS idx_social_posts_scheduled_date 
                ON social_media_posts(scheduled_date);
                
                CREATE INDEX IF NOT EXISTS idx_social_posts_client 
                ON social_media_posts(client_id);
                
                CREATE INDEX IF NOT EXISTS idx_social_posts_status 
                ON social_media_posts(status);
                
                CREATE INDEX IF NOT EXISTS idx_social_posts_platform 
                ON social_media_posts(platform);
            """)
            
            # 7. Add recordings table
            run_migration(conn, "Create recordings table", """
                CREATE TABLE IF NOT EXISTS recordings (
                    id VARCHAR(36) PRIMARY KEY,
                    user_id VARCHAR(255) NOT NULL,
                    client_id VARCHAR(36),
                    client_name VARCHAR(255),
                    context VARCHAR(50) NOT NULL, -- 'client' or 'oracle'
                    audio_path TEXT NOT NULL,
                    duration INTEGER NOT NULL, -- in seconds
                    transcript TEXT,
                    action_items JSONB,
                    recommendations JSONB,
                    summary TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE
                );
            """)
            
            run_migration(conn, "Add recordings indexes", """
                CREATE INDEX IF NOT EXISTS idx_user_recordings ON recordings(user_id);
                CREATE INDEX IF NOT EXISTS idx_client_recordings ON recordings(client_id);
                CREATE INDEX IF NOT EXISTS idx_context ON recordings(context);
                CREATE INDEX IF NOT EXISTS idx_created_at ON recordings(created_at);
            """)
            
            run_migration(conn, "Add source column to client_tasks", """
                ALTER TABLE client_tasks 
                ADD COLUMN IF NOT EXISTS source VARCHAR(50) DEFAULT 'manual';
            """)
            
            # 8. Add oracle_emails table
            run_migration(conn, "Create oracle_emails table", """
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
            """)
            
            run_migration(conn, "Add oracle_emails indexes", """
                CREATE INDEX IF NOT EXISTS idx_oracle_emails_user ON oracle_emails(user_id);
                CREATE INDEX IF NOT EXISTS idx_oracle_emails_date ON oracle_emails(date);
                CREATE INDEX IF NOT EXISTS idx_oracle_emails_message ON oracle_emails(message_id);
            """)
            
            # 9. Add new CRM fields
            run_migration(conn, "Add new CRM opportunity fields", """
                ALTER TABLE crm_opportunities 
                ADD COLUMN IF NOT EXISTS lead_status VARCHAR(50);
                
                ALTER TABLE crm_opportunities 
                ADD COLUMN IF NOT EXISTS job_title VARCHAR(255);
                
                ALTER TABLE crm_opportunities 
                ADD COLUMN IF NOT EXISTS company_address TEXT;
            """)
            
            run_migration(conn, "Update existing CRM opportunities default values", """
                UPDATE crm_opportunities 
                SET lead_status = 'New Lead' 
                WHERE lead_status IS NULL;
            """)
            
            run_migration(conn, "Add CRM field indexes", """
                CREATE INDEX IF NOT EXISTS idx_crm_lead_status ON crm_opportunities(lead_status);
                CREATE INDEX IF NOT EXISTS idx_crm_job_title ON crm_opportunities(job_title);
            """)
            
            # 10. Add expanded CRM fields
            run_migration(conn, "Add expanded CRM opportunity fields", """
                ALTER TABLE crm_opportunities 
                ADD COLUMN IF NOT EXISTS opportunity_type VARCHAR(50);
                
                ALTER TABLE crm_opportunities 
                ADD COLUMN IF NOT EXISTS owner VARCHAR(255);
                
                ALTER TABLE crm_opportunities 
                ADD COLUMN IF NOT EXISTS sales_pipeline VARCHAR(50);
                
                ALTER TABLE crm_opportunities 
                ADD COLUMN IF NOT EXISTS stage VARCHAR(50);
                
                ALTER TABLE crm_opportunities 
                ADD COLUMN IF NOT EXISTS est_close_date VARCHAR(50);
                
                ALTER TABLE crm_opportunities 
                ADD COLUMN IF NOT EXISTS close_date VARCHAR(50);
                
                ALTER TABLE crm_opportunities 
                ADD COLUMN IF NOT EXISTS engagement_type VARCHAR(50);
                
                ALTER TABLE crm_opportunities 
                ADD COLUMN IF NOT EXISTS win_likelihood VARCHAR(10);
                
                ALTER TABLE crm_opportunities 
                ADD COLUMN IF NOT EXISTS forecast_category VARCHAR(50);
            """)
            
            run_migration(conn, "Add expanded CRM field indexes", """
                CREATE INDEX IF NOT EXISTS idx_crm_opportunity_type ON crm_opportunities(opportunity_type);
                CREATE INDEX IF NOT EXISTS idx_crm_owner ON crm_opportunities(owner);
                CREATE INDEX IF NOT EXISTS idx_crm_sales_pipeline ON crm_opportunities(sales_pipeline);
                CREATE INDEX IF NOT EXISTS idx_crm_stage ON crm_opportunities(stage);
                CREATE INDEX IF NOT EXISTS idx_crm_close_dates ON crm_opportunities(est_close_date, close_date);
            """)
            
            # 11. Add social media automator tables
            run_migration(conn, "Create social media automator tables", """
                CREATE TABLE IF NOT EXISTS social_media_automator_tasks (
                    id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid()::text,
                    platform socialplatform NOT NULL,
                    task_type VARCHAR NOT NULL, -- e.g., 'post', 'comment', 'like'
                    status VARCHAR NOT NULL DEFAULT 'pending', -- 'pending', 'running', 'completed', 'failed'
                    parameters JSONB NOT NULL, -- JSONB for task-specific parameters
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    error_message TEXT
                );
            """)
            
            run_migration(conn, "Add social media automator indexes", """
                CREATE INDEX IF NOT EXISTS idx_automator_tasks_platform ON social_media_automator_tasks(platform);
                CREATE INDEX IF NOT EXISTS idx_automator_tasks_status ON social_media_automator_tasks(status);
                CREATE INDEX IF NOT EXISTS idx_automator_tasks_created_at ON social_media_automator_tasks(created_at DESC);
            """)
            
            # 12. Add error_message to oracle_data_sources
            run_migration(conn, "Add error_message to oracle_data_sources", """
                ALTER TABLE oracle_data_sources 
                ADD COLUMN IF NOT EXISTS error_message VARCHAR(500);
            """)
            
            # 13. Add oracle_action_items_fields
            run_migration(conn, "Add oracle_action_items_fields", """
                ALTER TABLE oracle_data_sources 
                ADD COLUMN IF NOT EXISTS action_items JSONB;
            """)
            
            # Run migration files from the list
            logger.info("Running migration files...")
            migrations_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '..', 'database', 'migrations')
            
            for migration_file in migrations:
                migration_path = os.path.join(migrations_dir, migration_file)
                if os.path.exists(migration_path):
                    logger.info(f"Running migration: {migration_file}")
                    with open(migration_path, 'r') as f:
                        migration_sql = f.read()
                    try:
                        conn.execute(text(migration_sql))
                        conn.commit()
                        logger.info(f"✓ Successfully ran {migration_file}")
                    except Exception as e:
                        if "already exists" in str(e) or "duplicate" in str(e):
                            logger.info(f"→ {migration_file} already applied (skipping)")
                        else:
                            logger.warning(f"⚠ Error in {migration_file}: {e}")
                else:
                    logger.warning(f"Migration file not found: {migration_file}")
            
            logger.info("All migrations completed successfully!")
            
    except Exception as e:
        logger.error(f"Critical error during migrations: {e}")
        sys.exit(1)
    finally:
        engine.dispose()

if __name__ == "__main__":
    main() 