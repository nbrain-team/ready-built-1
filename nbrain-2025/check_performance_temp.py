import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from core.database import engine
import time

print("Checking database performance...")

# Test connection
with engine.connect() as conn:
    # Test simple query
    start = time.time()
    result = conn.execute(text("SELECT COUNT(*) FROM clients"))
    count = result.scalar()
    elapsed = time.time() - start
    print(f"Clients count: {count} (took {elapsed:.3f}s)")
    
    # Check active connections
    result = conn.execute(text("""
        SELECT count(*) 
        FROM pg_stat_activity 
        WHERE datname = current_database()
    """))
    active = result.scalar()
    print(f"Total database connections: {active}")
    
    # Check connection states
    result = conn.execute(text("""
        SELECT state, count(*) 
        FROM pg_stat_activity 
        WHERE datname = current_database()
        GROUP BY state
    """))
    print("\nConnection states:")
    for state, cnt in result:
        print(f"  {state}: {cnt}")
    
    # Check for locks
    result = conn.execute(text("""
        SELECT count(*) 
        FROM pg_locks 
        WHERE NOT granted
    """))
    locks = result.scalar()
    print(f"\nBlocked locks: {locks}")

print("\nChecking pool status...")
pool = engine.pool
print(f"Pool size: {pool.size()}")
print(f"Checked out: {pool.checkedout()}")
print(f"Overflow: {pool.overflow()}")
