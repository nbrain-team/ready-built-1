#!/usr/bin/env python3
"""
Comprehensive performance optimization for nBrain
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

def optimize_database_performance():
    """Apply comprehensive database optimizations"""
    
    engine = create_engine(
        DATABASE_URL,
        pool_size=5,
        max_overflow=10,
        pool_timeout=30,
        pool_recycle=300,
        pool_pre_ping=True,
        poolclass=pool.QueuePool
    )
    
    try:
        with engine.connect() as conn:
            logger.info("Connected to database successfully")
            
            # Set statement timeout
            conn.execute(text("SET statement_timeout = '60s'"))
            
            # 1. Create composite indexes for common queries
            composite_indexes = [
                # Client portal optimizations
                ("idx_clients_status_created", 
                 "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_clients_status_created ON clients(status, created_at DESC)"),
                
                ("idx_client_communications_composite", 
                 "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_client_communications_composite ON client_communications(client_id, created_at DESC) INCLUDE (type, subject, from_user)"),
                
                ("idx_client_tasks_composite", 
                 "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_client_tasks_composite ON client_tasks(client_id, status) INCLUDE (priority, due_date)"),
                
                ("idx_team_members_active", 
                 "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_team_members_active ON client_team_members(client_id, is_active) WHERE is_active = true"),
                
                # Oracle optimizations
                ("idx_oracle_sources_composite", 
                 "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_oracle_sources_composite ON oracle_data_sources(user_id, source_type, is_connected)"),
                
                # User session optimizations
                ("idx_users_email_active", 
                 "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_email_active ON users(email) WHERE is_active = true"),
                
                ("idx_chat_sessions_user", 
                 "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_chat_sessions_user ON chat_sessions(user_id, created_at DESC)"),
            ]
            
            for index_name, index_sql in composite_indexes:
                try:
                    logger.info(f"Creating composite index: {index_name}")
                    conn.execute(text(index_sql))
                    conn.commit()
                    logger.info(f"✓ Created index: {index_name}")
                except Exception as e:
                    logger.warning(f"Could not create index {index_name}: {e}")
                    conn.rollback()
            
            # 2. Update table statistics
            tables_to_analyze = [
                'clients', 
                'client_communications', 
                'client_tasks',
                'client_team_members',
                'client_activities',
                'oracle_data_sources',
                'users',
                'chat_sessions'
            ]
            
            for table in tables_to_analyze:
                try:
                    logger.info(f"Updating statistics for table: {table}")
                    conn.execute(text(f"ANALYZE {table}"))
                    conn.commit()
                    logger.info(f"✓ Updated statistics for: {table}")
                except Exception as e:
                    logger.warning(f"Could not analyze table {table}: {e}")
                    conn.rollback()
            
            # 3. Set optimal PostgreSQL configuration
            config_updates = [
                # Increase work memory for complex queries
                ("SET work_mem = '16MB'", "work_mem"),
                
                # Enable parallel queries
                ("SET max_parallel_workers_per_gather = 2", "parallel workers"),
                
                # Optimize for SSDs
                ("SET random_page_cost = 1.1", "random page cost"),
                
                # Increase statistics target for better query plans
                ("ALTER DATABASE adtvdb SET default_statistics_target = 100", "statistics target"),
            ]
            
            for config_sql, config_name in config_updates:
                try:
                    logger.info(f"Optimizing {config_name}")
                    conn.execute(text(config_sql))
                    conn.commit()
                    logger.info(f"✓ Optimized {config_name}")
                except Exception as e:
                    logger.warning(f"Could not optimize {config_name}: {e}")
                    conn.rollback()
            
            # 4. Create materialized view for client summaries
            try:
                logger.info("Creating materialized view for client summaries")
                conn.execute(text("""
                    CREATE MATERIALIZED VIEW IF NOT EXISTS client_summary_mv AS
                    SELECT 
                        c.id,
                        c.name,
                        c.status,
                        c.health_score,
                        c.total_tasks,
                        c.completed_tasks,
                        COUNT(DISTINCT tm.id) FILTER (WHERE tm.is_active = true) as active_team_members,
                        MAX(comm.created_at) as last_communication_date
                    FROM clients c
                    LEFT JOIN client_team_members tm ON c.id = tm.client_id
                    LEFT JOIN client_communications comm ON c.id = comm.client_id
                    GROUP BY c.id, c.name, c.status, c.health_score, c.total_tasks, c.completed_tasks
                """))
                
                # Create index on materialized view
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_client_summary_mv_id 
                    ON client_summary_mv(id)
                """))
                
                conn.commit()
                logger.info("✓ Created materialized view for client summaries")
            except Exception as e:
                logger.warning(f"Could not create materialized view: {e}")
                conn.rollback()
            
            # 5. Clean up and optimize
            logger.info("Running VACUUM ANALYZE on key tables...")
            for table in ['clients', 'client_communications', 'client_tasks']:
                try:
                    conn.execute(text(f"VACUUM ANALYZE {table}"))
                    conn.commit()
                    logger.info(f"✓ Vacuumed and analyzed {table}")
                except Exception as e:
                    logger.warning(f"Could not vacuum {table}: {e}")
                    conn.rollback()
            
            # 6. Show query performance stats
            result = conn.execute(text("""
                SELECT 
                    schemaname,
                    tablename,
                    n_tup_ins + n_tup_upd + n_tup_del as total_writes,
                    n_tup_hot_upd::numeric / NULLIF(n_tup_upd, 0) as hot_update_ratio,
                    n_live_tup,
                    n_dead_tup,
                    last_vacuum,
                    last_autovacuum
                FROM pg_stat_user_tables
                WHERE schemaname = 'public'
                ORDER BY total_writes DESC
                LIMIT 10
            """))
            
            logger.info("\nTable statistics:")
            for row in result:
                logger.info(f"  {row[1]}: {row[2]} writes, {row[4]} live tuples, {row[5]} dead tuples")
            
            logger.info("\n✓ Database optimization completed successfully")
            
    except Exception as e:
        logger.error(f"Error during database optimization: {e}")
        sys.exit(1)
    finally:
        engine.dispose()

if __name__ == "__main__":
    optimize_database_performance() 