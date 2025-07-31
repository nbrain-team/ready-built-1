#!/usr/bin/env python3
"""
Fix database connection issues and add performance indexes
"""

import os
import sys
import logging
from sqlalchemy import create_engine, text, pool
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

def fix_database_connections():
    """Fix database connection issues and add performance indexes"""
    
    # Create engine with optimized settings
    engine = create_engine(
        DATABASE_URL,
        pool_size=10,
        max_overflow=20,
        pool_timeout=30,
        pool_recycle=300,
        pool_pre_ping=True,
        poolclass=pool.QueuePool
    )
    
    try:
        with engine.connect() as conn:
            logger.info("Connected to database successfully")
            
            # Set statement timeout for this session
            conn.execute(text("SET statement_timeout = '30s'"))
            
            # Add indexes for better performance
            indexes = [
                # Client communications indexes
                ("idx_client_communications_client_id", 
                 "CREATE INDEX IF NOT EXISTS idx_client_communications_client_id ON client_communications(client_id)"),
                ("idx_client_communications_created_at", 
                 "CREATE INDEX IF NOT EXISTS idx_client_communications_created_at ON client_communications(created_at DESC)"),
                ("idx_client_communications_type", 
                 "CREATE INDEX IF NOT EXISTS idx_client_communications_type ON client_communications(type)"),
                
                # Client tasks indexes
                ("idx_client_tasks_client_id", 
                 "CREATE INDEX IF NOT EXISTS idx_client_tasks_client_id ON client_tasks(client_id)"),
                ("idx_client_tasks_status", 
                 "CREATE INDEX IF NOT EXISTS idx_client_tasks_status ON client_tasks(status)"),
                
                # Oracle data sources indexes
                ("idx_oracle_data_sources_user_id", 
                 "CREATE INDEX IF NOT EXISTS idx_oracle_data_sources_user_id ON oracle_data_sources(user_id)"),
                ("idx_oracle_data_sources_source_type", 
                 "CREATE INDEX IF NOT EXISTS idx_oracle_data_sources_source_type ON oracle_data_sources(source_type)"),
                
                # Clients indexes
                ("idx_clients_created_at", 
                 "CREATE INDEX IF NOT EXISTS idx_clients_created_at ON clients(created_at DESC)"),
                ("idx_clients_status", 
                 "CREATE INDEX IF NOT EXISTS idx_clients_status ON clients(status)"),
                
                # Users indexes
                ("idx_users_email", 
                 "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)"),
            ]
            
            for index_name, index_sql in indexes:
                try:
                    logger.info(f"Creating index: {index_name}")
                    conn.execute(text(index_sql))
                    conn.commit()
                    logger.info(f"✓ Created index: {index_name}")
                except Exception as e:
                    logger.warning(f"Could not create index {index_name}: {e}")
                    conn.rollback()
            
            # Analyze tables for better query planning
            tables = [
                'clients', 
                'client_communications', 
                'client_tasks', 
                'oracle_data_sources',
                'users',
                'chat_sessions'
            ]
            
            for table in tables:
                try:
                    logger.info(f"Analyzing table: {table}")
                    conn.execute(text(f"ANALYZE {table}"))
                    conn.commit()
                    logger.info(f"✓ Analyzed table: {table}")
                except Exception as e:
                    logger.warning(f"Could not analyze table {table}: {e}")
                    conn.rollback()
            
            # Show current connection stats
            result = conn.execute(text("""
                SELECT 
                    count(*) as total_connections,
                    count(*) FILTER (WHERE state = 'active') as active_connections,
                    count(*) FILTER (WHERE state = 'idle') as idle_connections
                FROM pg_stat_activity
                WHERE datname = current_database()
            """))
            
            stats = result.fetchone()
            logger.info(f"Database connection stats:")
            logger.info(f"  Total connections: {stats[0]}")
            logger.info(f"  Active connections: {stats[1]}")
            logger.info(f"  Idle connections: {stats[2]}")
            
            logger.info("✓ Database optimization completed successfully")
            
    except Exception as e:
        logger.error(f"Error during database optimization: {e}")
        sys.exit(1)
    finally:
        engine.dispose()

if __name__ == "__main__":
    fix_database_connections() 