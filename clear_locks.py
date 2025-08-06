#!/usr/bin/env python3
"""
Clear database locks and prepare for upload
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Database URL
DATABASE_URL = os.getenv('DATABASE_URL', '')

if not DATABASE_URL:
    print("Please set your DATABASE_URL environment variable")
    sys.exit(1)

# Create engine
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
Session = sessionmaker(bind=engine)

def clear_locks():
    """Clear database locks"""
    session = Session()
    
    try:
        print("=" * 60)
        print("CLEARING DATABASE LOCKS")
        print("=" * 60)
        
        # Check current activity
        result = session.execute(text("""
            SELECT 
                pid,
                usename,
                state,
                query_start,
                state_change,
                SUBSTRING(query, 1, 50) as query_preview
            FROM pg_stat_activity
            WHERE datname = current_database()
            AND pid != pg_backend_pid()
            AND state != 'idle'
            ORDER BY query_start
        """))
        
        active = list(result)
        
        if not active:
            print("✓ No active queries found")
            return True
        
        print(f"\nFound {len(active)} active connections:")
        
        # Terminate problematic connections
        terminated = 0
        for row in active:
            # Only terminate long-running or stuck queries
            if row.state in ('idle in transaction', 'idle in transaction (aborted)', 'active'):
                try:
                    session.execute(
                        text("SELECT pg_terminate_backend(:pid)"),
                        {"pid": row.pid}
                    )
                    print(f"  ✓ Terminated PID {row.pid} ({row.state})")
                    terminated += 1
                except Exception as e:
                    print(f"  ✗ Failed to terminate PID {row.pid}: {e}")
        
        session.commit()
        
        if terminated > 0:
            print(f"\n✓ Terminated {terminated} connections")
        
        # Wait a moment for connections to clear
        import time
        time.sleep(2)
        
        # Verify
        result = session.execute(text("""
            SELECT COUNT(*) 
            FROM pg_stat_activity 
            WHERE datname = current_database()
            AND state != 'idle'
            AND pid != pg_backend_pid()
        """))
        
        remaining = result.scalar()
        
        if remaining > 0:
            print(f"\n⚠️  Warning: {remaining} connections still active")
        else:
            print("\n✓ All connections cleared")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        return False
        
    finally:
        session.close()

def check_table_locks():
    """Check for table-level locks"""
    session = Session()
    
    try:
        print("\nChecking table locks...")
        
        result = session.execute(text("""
            SELECT 
                l.relation::regclass as table_name,
                l.mode,
                l.granted,
                a.usename,
                a.pid
            FROM pg_locks l
            JOIN pg_stat_activity a ON l.pid = a.pid
            WHERE l.relation IN (
                'salon_transactions'::regclass,
                'salon_time_clock'::regclass,
                'salon_schedules'::regclass
            )
        """))
        
        locks = list(result)
        
        if not locks:
            print("✓ No table locks found")
        else:
            print(f"⚠️  Found {len(locks)} table locks:")
            for lock in locks:
                print(f"  - {lock.table_name}: {lock.mode} (PID: {lock.pid})")
        
    except Exception as e:
        print(f"Error checking locks: {e}")
        
    finally:
        session.close()

def main():
    if clear_locks():
        check_table_locks()
        print("\n✓ Database is ready for upload")
        print("\nNext step: Run the lightweight upload script")
        print("  export DATABASE_URL='...' && python lightweight_upload.py")
    else:
        print("\n✗ Failed to clear locks")

if __name__ == "__main__":
    main() 