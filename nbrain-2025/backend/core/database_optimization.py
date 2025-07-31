"""
Database optimization utilities for handling read replicas and connection pooling
"""

import os
import logging
from sqlalchemy import create_engine, pool
from sqlalchemy.orm import sessionmaker, scoped_session
from contextlib import contextmanager

logger = logging.getLogger(__name__)

# Primary database URL (for writes)
PRIMARY_DATABASE_URL = os.getenv("DATABASE_URL")

# Read replica URLs (comma-separated if multiple)
READ_REPLICA_URLS = os.getenv("READ_REPLICA_URLS", "").split(",") if os.getenv("READ_REPLICA_URLS") else []

# If no read replicas, use primary for reads
if not READ_REPLICA_URLS:
    READ_REPLICA_URLS = [PRIMARY_DATABASE_URL]

# Convert postgresql:// to postgresql+psycopg2://
def fix_database_url(url):
    if url and url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg2://")
        if "sslmode=" not in url:
            url += "?sslmode=require"
    return url

PRIMARY_DATABASE_URL = fix_database_url(PRIMARY_DATABASE_URL)
READ_REPLICA_URLS = [fix_database_url(url) for url in READ_REPLICA_URLS if url]

# Create engines with optimized settings
write_engine = create_engine(
    PRIMARY_DATABASE_URL,
    pool_size=5,  # Smaller pool for write operations
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=300,
    pool_pre_ping=True,
    poolclass=pool.QueuePool,
    echo=False
)

# Create read engines (round-robin between replicas)
read_engines = []
for replica_url in READ_REPLICA_URLS:
    engine = create_engine(
        replica_url,
        pool_size=10,  # Larger pool for read operations
        max_overflow=20,
        pool_timeout=30,
        pool_recycle=300,
        pool_pre_ping=True,
        poolclass=pool.QueuePool,
        echo=False
    )
    read_engines.append(engine)

# Session factories
WriteSessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=write_engine))
ReadSessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=read_engines[0]))

# Round-robin counter for read replicas
_read_replica_counter = 0

def get_read_engine():
    """Get the next read engine in round-robin fashion"""
    global _read_replica_counter
    if len(read_engines) == 1:
        return read_engines[0]
    
    engine = read_engines[_read_replica_counter % len(read_engines)]
    _read_replica_counter += 1
    return engine

@contextmanager
def get_read_db():
    """Get a read-only database session"""
    # Create a new session with the next read engine
    engine = get_read_engine()
    SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        SessionLocal.remove()

@contextmanager
def get_write_db():
    """Get a write database session"""
    db = WriteSessionLocal()
    try:
        yield db
    finally:
        db.close()
        WriteSessionLocal.remove()

def optimize_query_for_read(query):
    """Apply read optimizations to a query"""
    # Disable autoflush for read queries
    query = query.autoflush(False)
    
    # Enable query caching if available
    query = query.execution_options(
        synchronize_session=False,
        compiled_cache={}
    )
    
    return query

# Connection pool monitoring
def get_pool_status():
    """Get the current status of all connection pools"""
    status = {
        "write_pool": {
            "size": write_engine.pool.size(),
            "checked_in": write_engine.pool.checkedin(),
            "overflow": write_engine.pool.overflow(),
            "total": write_engine.pool.checkedin() + write_engine.pool.checkedout()
        },
        "read_pools": []
    }
    
    for i, engine in enumerate(read_engines):
        status["read_pools"].append({
            "replica": i,
            "size": engine.pool.size(),
            "checked_in": engine.pool.checkedin(),
            "overflow": engine.pool.overflow(),
            "total": engine.pool.checkedin() + engine.pool.checkedout()
        })
    
    return status

# Cleanup function
def cleanup_connections():
    """Dispose all database connections"""
    logger.info("Disposing database connections...")
    write_engine.dispose()
    for engine in read_engines:
        engine.dispose()
    logger.info("Database connections disposed") 