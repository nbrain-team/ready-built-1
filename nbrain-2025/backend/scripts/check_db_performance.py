#!/usr/bin/env python3
"""
Check database performance and connection pool status
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from core.database import engine, SessionLocal
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_db_performance():
    """Check database performance metrics"""
    
    logger.info("Checking database performance...")
    
    # Test connection pool
    logger.info("\n1. Connection Pool Status:")
    pool = engine.pool
    logger.info(f"   Pool size: {pool.size()}")
    logger.info(f"   Checked out connections: {pool.checkedout()}")
    logger.info(f"   Overflow: {pool.overflow()}")
    logger.info(f"   Total: {pool.size() + pool.overflow()}")
    
    # Test query performance
    logger.info("\n2. Testing Query Performance:")
    
    with engine.connect() as conn:
        # Test simple query
        start = time.time()
        result = conn.execute(text("SELECT COUNT(*) FROM clients"))
        count = result.scalar()
        elapsed = time.time() - start
        logger.info(f"   Clients count: {count} (took {elapsed:.3f}s)")
        
        # Test join query
        start = time.time()
        result = conn.execute(text("""
            SELECT c.id, COUNT(ct.id) as task_count
            FROM clients c
            LEFT JOIN client_tasks ct ON c.id = ct.client_id
            GROUP BY c.id
            LIMIT 10
        """))
        result.fetchall()
        elapsed = time.time() - start
        logger.info(f"   Join query test (took {elapsed:.3f}s)")
        
        # Check active connections
        result = conn.execute(text("""
            SELECT count(*) 
            FROM pg_stat_activity 
            WHERE datname = current_database()
            AND state = 'active'
        """))
        active = result.scalar()
        logger.info(f"   Active database connections: {active}")
        
        # Check for long-running queries
        result = conn.execute(text("""
            SELECT pid, now() - pg_stat_activity.query_start AS duration, query 
            FROM pg_stat_activity 
            WHERE (now() - pg_stat_activity.query_start) > interval '5 seconds'
            AND state = 'active'
            ORDER BY duration DESC
            LIMIT 5
        """))
        long_queries = result.fetchall()
        if long_queries:
            logger.warning("\n3. Long-running queries detected:")
            for pid, duration, query in long_queries:
                logger.warning(f"   PID {pid}: {duration} - {query[:100]}...")
        else:
            logger.info("\n3. No long-running queries detected")
    
    # Test session cleanup
    logger.info("\n4. Testing Session Management:")
    try:
        # Create and properly close a session
        session = SessionLocal()
        result = session.execute(text("SELECT 1"))
        result.scalar()
        SessionLocal.remove()  # Proper cleanup
        logger.info("   Session management: OK")
    except Exception as e:
        logger.error(f"   Session management error: {e}")
    
    logger.info("\n5. Recommendations:")
    if pool.checkedout() > pool.size() * 0.8:
        logger.warning("   - High connection usage detected. Consider increasing pool size.")
    else:
        logger.info("   - Connection pool usage is healthy")
    
    logger.info("\nPerformance check completed!")

if __name__ == "__main__":
    check_db_performance() 