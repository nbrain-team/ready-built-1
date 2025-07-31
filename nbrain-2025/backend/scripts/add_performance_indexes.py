#!/usr/bin/env python3
"""
Add performance indexes to improve query speed and reduce database load.
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from core.database import engine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_index_exists(conn, index_name):
    """Check if an index already exists"""
    result = conn.execute(text("""
        SELECT 1 FROM pg_indexes 
        WHERE indexname = :index_name
    """), {"index_name": index_name})
    return result.fetchone() is not None

def get_table_size(conn, table_name):
    """Get the size of a table in rows"""
    try:
        result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
        return result.scalar()
    except:
        return 0

def add_indexes():
    """Add performance indexes to the database"""
    
    # During build, we'll create indexes without CONCURRENTLY to be faster
    # but only on smaller tables to avoid timeouts
    indexes = [
        # Client communications - most queried table
        ("idx_client_communications_client_id", "client_communications", "CREATE INDEX IF NOT EXISTS idx_client_communications_client_id ON client_communications(client_id);"),
        ("idx_client_communications_created_at", "client_communications", "CREATE INDEX IF NOT EXISTS idx_client_communications_created_at ON client_communications(created_at DESC);"),
        ("idx_client_communications_type", "client_communications", "CREATE INDEX IF NOT EXISTS idx_client_communications_type ON client_communications(type);"),
        ("idx_client_communications_composite", "client_communications", "CREATE INDEX IF NOT EXISTS idx_client_communications_composite ON client_communications(client_id, type, created_at DESC);"),
        
        # Client tasks
        ("idx_client_tasks_client_id", "client_tasks", "CREATE INDEX IF NOT EXISTS idx_client_tasks_client_id ON client_tasks(client_id);"),
        ("idx_client_tasks_status", "client_tasks", "CREATE INDEX IF NOT EXISTS idx_client_tasks_status ON client_tasks(status);"),
        ("idx_client_tasks_composite", "client_tasks", "CREATE INDEX IF NOT EXISTS idx_client_tasks_composite ON client_tasks(client_id, status);"),
        
        # Oracle data sources
        ("idx_oracle_sources_user_type", "oracle_data_sources", "CREATE INDEX IF NOT EXISTS idx_oracle_sources_user_type ON oracle_data_sources(user_id, source_type);"),
        
        # Oracle action items
        ("idx_oracle_actions_user_status", "oracle_action_items", "CREATE INDEX IF NOT EXISTS idx_oracle_actions_user_status ON oracle_action_items(user_id, status);"),
        
        # Chat sessions
        ("idx_chat_sessions_user_created", "chat_sessions", "CREATE INDEX IF NOT EXISTS idx_chat_sessions_user_created ON chat_sessions(user_id, created_at DESC);"),
        
        # CRM opportunities
        ("idx_crm_opportunities_user_status", "crm_opportunities", "CREATE INDEX IF NOT EXISTS idx_crm_opportunities_user_status ON crm_opportunities(user_id, status);"),
        
        # Client table indexes for faster loading
        ("idx_clients_created_at", "clients", "CREATE INDEX IF NOT EXISTS idx_clients_created_at ON clients(created_at DESC);"),
        ("idx_clients_status", "clients", "CREATE INDEX IF NOT EXISTS idx_clients_status ON clients(status);"),
    ]
    
    # Check table sizes first
    logger.info("Checking table sizes...")
    large_tables = set()
    
    with engine.connect() as conn:
        for _, table_name, _ in indexes:
            if table_name not in large_tables:
                size = get_table_size(conn, table_name)
                logger.info(f"Table {table_name} has {size} rows")
                if size > 100000:  # Skip tables with more than 100k rows during build
                    large_tables.add(table_name)
                    logger.warning(f"Table {table_name} is too large ({size} rows), skipping index creation during build")
    
    # Create indexes on smaller tables
    created_count = 0
    skipped_count = 0
    
    with engine.connect() as conn:
        # Set a shorter timeout for each index
        conn.execute(text("SET statement_timeout = '10s';"))
        
        for index_name, table_name, index_sql in indexes:
            try:
                # Skip large tables
                if table_name in large_tables:
                    logger.info(f"⏭️  Skipping index {index_name} on large table {table_name}")
                    skipped_count += 1
                    continue
                
                # Check if index already exists
                if check_index_exists(conn, index_name):
                    logger.info(f"✓ Index already exists: {index_name}")
                    continue
                
                # Create index
                conn.execute(text(index_sql))
                conn.commit()
                created_count += 1
                logger.info(f"✓ Created index: {index_name}")
                
            except Exception as e:
                if "already exists" in str(e):
                    logger.info(f"✓ Index already exists: {index_name}")
                elif "statement timeout" in str(e):
                    logger.warning(f"Timeout creating index {index_name}, skipping")
                    skipped_count += 1
                else:
                    logger.warning(f"Could not create index {index_name}: {e}")
                # Continue with other indexes even if one fails
                continue
        
    logger.info(f"\nIndex creation summary: {created_count} created, {skipped_count} skipped")
    
    if large_tables:
        logger.info("\nLarge tables detected. Indexes should be created manually after deployment:")
        logger.info("Run these commands in the database console when system is less busy:")
        for index_name, table_name, index_sql in indexes:
            if table_name in large_tables:
                # Replace IF NOT EXISTS with CONCURRENTLY for manual creation
                concurrent_sql = index_sql.replace("IF NOT EXISTS", "CONCURRENTLY IF NOT EXISTS")
                logger.info(f"  {concurrent_sql}")
    
    # Skip analyze on large tables too
    logger.info("\nAnalyzing smaller tables for query optimization...")
    tables_to_analyze = [
        'clients',
        'oracle_data_sources',
        'oracle_action_items',
        'chat_sessions',
        'crm_opportunities'
    ]
    
    # Only analyze if not in large_tables
    if 'client_communications' not in large_tables:
        tables_to_analyze.append('client_communications')
    if 'client_tasks' not in large_tables:
        tables_to_analyze.append('client_tasks')
    
    try:
        with engine.connect() as conn:
            # Set timeout for analyze operations
            conn.execute(text("SET statement_timeout = '5s';"))
            
            for table in tables_to_analyze:
                try:
                    conn.execute(text(f"ANALYZE {table};"))
                    logger.info(f"✓ Analyzed {table}")
                except Exception as e:
                    logger.warning(f"Could not analyze {table}: {e}")
            conn.commit()
    except Exception as e:
        logger.warning(f"Could not complete table analysis: {e}")

if __name__ == "__main__":
    try:
        add_indexes()
    except Exception as e:
        logger.error(f"Failed to add indexes: {e}")
        # Exit gracefully to not block deployment
        sys.exit(0) 